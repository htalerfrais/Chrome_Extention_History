// utils.js

// Convert lastVisitTime from WebKit epoch (1601-01-01) to Unix epoch (1970-01-01)
// and add convenient fields. If lastVisitTime is missing, item is returned as-is.
function datesFormating(items) {
    const WEBKIT_EPOCH_DIFF_MS = 11644473600000; // ms between 1601-01-01 and 1970-01-01
    if (!Array.isArray(items)) return [];
    return items.map((item) => {
        if (!item || typeof item.lastVisitTime !== 'number') return item;
        let unixMs = item.lastVisitTime - WEBKIT_EPOCH_DIFF_MS;
        if (unixMs < 0) {
            // Fallback: if already Unix epoch, keep as-is
            unixMs = item.lastVisitTime;
        }
        const iso = new Date(unixMs).toISOString();
        return Object.assign({}, item, {
            lastVisitUnixMs: unixMs,
            lastVisitISO: iso
        });
    });
}

// Placeholder for future filtering logic; currently returns items unchanged
function filterHistory(items) {
    if (!Array.isArray(items)) return [];
    return items;
}


