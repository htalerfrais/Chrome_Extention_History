// preprocess_history.js

// Enrich history items with convenient date fields derived from lastVisitTime (Unix ms)
function datesFormating(items) {
    if (!Array.isArray(items)) return [];
    return items.map((item) => {
        if (!item || typeof item.lastVisitTime !== 'number') return item;
        const iso = new Date(item.lastVisitTime).toISOString();
        return Object.assign({}, item, {
            lastVisitISO: iso
        });
    });
}

// --- URL similarity-based collapsing for consecutive near-duplicates (Option A) ---
// Only collapses when titles match; otherwise always keeps the item.
// threshold in [0,1] (e.g., 0.8)
function filterHistoryURL(items, threshold) {
    if (!Array.isArray(items)) return [];
    const similarityThreshold = typeof threshold === 'number' ? threshold : 0.6;

    const kept = [];
    const dropped = [];
    let lastKept = null;

    for (let i = 0; i < items.length; i++) {
        const current = items[i];
        if (!current) continue;

        if (!lastKept) {
            kept.push(current);
            lastKept = current;
            continue;
        }

        // If titles differ, keep unconditionally
        const titleA = (lastKept.title || '').trim().toLowerCase();
        const titleB = (current.title || '').trim().toLowerCase();
        if (!titleA || !titleB || titleA !== titleB) {
            kept.push(current);
            lastKept = current;
            continue;
        }

        // Titles match → compare normalized URLs
        const urlA = normalizeUrl(lastKept.url || '');
        const urlB = normalizeUrl(current.url || '');
        const sim = diceCoefficient(urlA, urlB);
        if (sim >= similarityThreshold) {
            // Drop current as too similar to previous kept & add dropped in dropped list
            dropped.push(current);
            continue;
        } else {
            kept.push(current);
            lastKept = current;
        }
    }
    console.log('Dropped items:', dropped);
    return kept;
}







// Normalize URLs for stable similarity: lowercase host, strip protocol/hash,
// remove tracking params, sort remaining query keys, trim trailing slashes
function normalizeUrl(raw) {
    if (typeof raw !== 'string' || raw.length === 0) return '';
    let u;
    try {
        // Ensure we have a protocol for URL parser
        u = new URL(raw);
    } catch (e) {
        try {
            u = new URL('http://' + raw);
        } catch (e2) {
            return raw.toLowerCase();
        }
    }

    u.hash = '';

    // Clean search params
    const toRemove = new Set([
        'gclid','fbclid','igshid','ref','ref_src','mc_cid','mc_eid'
    ]);
    const params = new URLSearchParams(u.search);
    // remove utm_* and known trackers
    for (const key of Array.from(params.keys())) {
        if (key.startsWith('utm_') || toRemove.has(key)) {
            params.delete(key);
        }
    }
    // Rebuild sorted query string
    const entries = Array.from(params.entries()).sort((a, b) => a[0].localeCompare(b[0]));
    const sorted = new URLSearchParams();
    for (const [k, v] of entries) sorted.append(k, v);

    const host = (u.hostname || '').toLowerCase();
    let pathname = u.pathname || '/';
    // collapse multiple slashes and remove trailing slash except root
    pathname = pathname.replace(/\/+/g, '/');
    if (pathname.length > 1 && pathname.endsWith('/')) pathname = pathname.slice(0, -1);

    const base = host + pathname;
    const query = sorted.toString();
    return query ? base + '?' + query : base;
}

// Dice coefficient over character bigrams; fast and effective for similarity
function diceCoefficient(a, b) {
    if (a === b) return 1;
    if (!a || !b) return 0;
    if (a.length < 2 || b.length < 2) return 0;

    const bigrams = new Map();
    for (let i = 0; i < a.length - 1; i++) {
        const bg = a.slice(i, i + 2);
        bigrams.set(bg, (bigrams.get(bg) || 0) + 1);
    }
    let overlap = 0;
    for (let i = 0; i < b.length - 1; i++) {
        const bg = b.slice(i, i + 2);
        const count = bigrams.get(bg) || 0;
        if (count > 0) {
            bigrams.set(bg, count - 1);
            overlap++;
        }
    }
    return (2 * overlap) / (a.length - 1 + b.length - 1);
}



// --- URL feature extraction for NLP-friendly fields ---
// Adds: urlHostname, urlPathnameClean, and optionally urlSearchQuery (for useful search params)
function addUrlFeatures(items) {
    if (!Array.isArray(items)) return [];
    return items.map((item) => {
        if (!item || typeof item.url !== 'string') return item;
        const features = extractUrlFeatures(item.url);
        return Object.assign({}, item, features);
    });
}

function extractUrlFeatures(raw) {
    const result = { urlHostname: '', urlPathnameClean: '/', urlSearchQuery: undefined };
    if (typeof raw !== 'string' || raw.length === 0) return result;

    let u;
    try {
        u = new URL(raw);
    } catch (e) {
        try {
            u = new URL('http://' + raw);
        } catch (e2) {
            return result;
        }
    }

    // Hostname in lowercase
    const hostname = (u.hostname || '').toLowerCase();
    result.urlHostname = hostname;

    // Extract useful search query if present
    const useful = extractUsefulSearchQuery(u.search, hostname, u.pathname || '/');
    if (useful) {
        result.urlSearchQuery = useful;
    }

    // Build cleaned pathname
    let pathname = u.pathname || '/';
    // Normalize slashes and trim trailing slash (except root)
    pathname = pathname.replace(/\/+/, '/');
    if (pathname.length > 1 && pathname.endsWith('/')) pathname = pathname.slice(0, -1);

    const segments = pathname.split('/').filter(Boolean).map(safeDecodeLower);
    const cleanedSegments = segments
        .map(stripCommonExtensions)
        .filter((seg) => !isNoiseSegment(seg))
        .filter((seg) => !isNumericId(seg))
        .filter((seg) => !isUuid(seg))
        .filter((seg) => !isHexLong(seg))
        .filter((seg) => !isLongSlug(seg));

    result.urlPathnameClean = '/' + cleanedSegments.join('/');
    if (result.urlPathnameClean === '/') {
        // Keep root if nothing meaningful remains
        result.urlPathnameClean = '/';
    }

    return result;
}

function extractUsefulSearchQuery(search, hostname, pathname) {
    if (!search) return '';
    const params = new URLSearchParams(search);
    const host = (hostname || '').toLowerCase();
    const path = (pathname || '/').toLowerCase();

    // Host/path-specific priority keys
    const hostKeyMap = [
        { match: /youtube\.com$/, keys: path.startsWith('/results') ? ['search_query', 'q', 'query'] : ['search_query', 'q', 'query'] },
        { match: /google\.[a-z.]+$/, keys: ['q'] },
        { match: /bing\.com$/, keys: ['q'] },
        { match: /duckduckgo\.com$/, keys: ['q'] },
        { match: /search\.yahoo\.com$/, keys: ['p', 'q'] },
        { match: /yahoo\.[a-z.]+$/, keys: ['p', 'q'] },
        { match: /leboncoin\.fr$/, keys: ['text', 'q'] },
        { match: /amazon\.[a-z.]+$/, keys: ['k', 'field-keywords', 'keyword'] },
        { match: /ebay\.[a-z.]+$/, keys: ['_nkw', 'kw', 'q'] },
        { match: /reddit\.com$/, keys: ['q'] },
        { match: /twitter\.com$/, keys: ['q'] },
        { match: /x\.com$/, keys: ['q'] },
        { match: /github\.com$/, keys: ['q'] },
        { match: /stackoverflow\.com$/, keys: ['q'] }
    ];

    let prioritizedKeys = [];
    for (const entry of hostKeyMap) {
        if (entry.match.test(host)) {
            prioritizedKeys = entry.keys;
            break;
        }
    }

    // Generic fallback keys (ordered by commonality)
    const genericKeys = ['q', 'query', 'text', 'search', 'keyword', 's'];
    const tryKeys = prioritizedKeys.length > 0 ? prioritizedKeys.concat(genericKeys) : genericKeys;

    for (const key of tryKeys) {
        if (params.has(key)) {
            let val = params.get(key) || '';
            // Normalize '+' to space for engines that use plus as space
            val = val.replace(/\+/g, ' ');
            val = val.trim();
            if (val) return val;
        }
    }

    return '';
}

function safeDecodeLower(s) {
    if (!s) return '';
    try {
        return decodeURIComponent(s).toLowerCase();
    } catch (e) {
        return s.toLowerCase();
    }
}

function stripCommonExtensions(seg) {
    return seg.replace(/\.(html?|php|asp|aspx|jsp|cfm|cgi)$/i, '');
}

function isNoiseSegment(seg) {
    if (!seg) return true;
    const noise = new Set([
        'index','home','default','page','pages','view','item','items','category','categories','tag','tags','archive','search'
    ]);
    return noise.has(seg);
}

function isNumericId(seg) {
    // Purely numeric with length >= 4
    return /^\d{4,}$/.test(seg);
}

function isUuid(seg) {
    return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(seg);
}

function isHexLong(seg) {
    // Long hex blobs (8+ chars) often noise/hash
    return /^[0-9a-f]{8,}$/i.test(seg);
}

function isLongSlug(seg) {
    // Very long slugs with only lowercase letters, digits, and hyphens
    return /^[a-z0-9-]{16,}$/.test(seg);
}