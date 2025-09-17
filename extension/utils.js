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

// Placeholder for future filtering logic; currently returns items unchanged
function filterHistory(items) {
    if (!Array.isArray(items)) return [];
    return items;
}


