// utils.js

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
function filterHistory(items, threshold) {
    if (!Array.isArray(items)) return [];
    const similarityThreshold = typeof threshold === 'number' ? threshold : 0.8;

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


