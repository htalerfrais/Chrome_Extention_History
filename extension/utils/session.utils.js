// Session utility functions
// Pure functions for session management operations

/**
 * Generate a deterministic session identifier based on session content
 * @param {number} startTime - Session start timestamp
 * @param {number} endTime - Session end timestamp
 * @param {Array} items - Session items
 * @returns {string} Deterministic session identifier
 */
function generateSessionId(startTime, endTime, items) {
    // Create a stable string from session characteristics
    // Keep it stable for the current session by only using startTime and firstUrl
    const urls = items.map(item => item.url || '').filter(url => url.length > 0);
    const firstUrl = urls[0] || '';
    
    // Create a stable hash string combining key session attributes
    const hashInput = `${startTime}_${firstUrl}`;
    
    // Generate a deterministic hash using a simple string hashing algorithm
    let hash = 0;
    for (let i = 0; i < hashInput.length; i++) {
        const char = hashInput.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32-bit integer
    }
    
    // Convert to positive hex string
    const hashString = Math.abs(hash).toString(16).padStart(8, '0');
    
    return `session_${hashString}`;
}

/**
 * Groups history items into time-based sessions
 * @param {Array} historyItems - Preprocessed history items
 * @param {number} sessionGapMinutes - Gap between sessions in minutes
 * @param {number} minItems - Minimum items per session
 * @returns {Array} Array of session objects with sessionId
 */
function groupItemsIntoSessions(historyItems, sessionGapMinutes = 60, minItems = 2) {
    if (!historyItems || historyItems.length === 0) {
        return [];
    }
    
    console.log(`Grouping ${historyItems.length} history items into sessions with gap: ${sessionGapMinutes} minutes`);
    
    // Sort by visit time
    const sortedItems = [...historyItems].sort((a, b) => {
        const timeA = a.lastVisitTime || a.visitTime || 0;
        const timeB = b.lastVisitTime || b.visitTime || 0;
        return timeA - timeB;
    });
    
    const sessions = [];
    let currentSession = null;
    const sessionGapMs = sessionGapMinutes * 60 * 1000;
    
    for (const item of sortedItems) {
        const itemTime = item.lastVisitTime || item.visitTime || Date.now();
        
        if (!currentSession || (itemTime - currentSession.endTime) > sessionGapMs) {
            // Start new session
            if (currentSession) {
                sessions.push(currentSession);
            }
            
            currentSession = {
                sessionId: null, // Will be set after items are collected
                startTime: itemTime,
                endTime: itemTime,
                items: [item]
            };
        } else {
            // Add to current session
            currentSession.items.push(item);
            currentSession.endTime = itemTime;
        }
    }
    
    // Add the last session
    if (currentSession) {
        sessions.push(currentSession);
    }
    
    // Generate deterministic IDs for each session
    for (const session of sessions) {
        session.sessionId = generateSessionId(
            session.startTime,
            session.endTime,
            session.items
        );
    }
    
    // Filter out sessions with too few items
    const validSessions = sessions.filter(session => session.items.length >= minItems);
    
    console.log(`Created ${validSessions.length} valid sessions (filtered ${sessions.length - validSessions.length} small sessions)`);
    
    return validSessions;
}

/**
 * Format a session object for API consumption
 * @param {Object} session - Session object with sessionId, startTime, endTime, items
 * @returns {Object} Formatted session for API
 */
function formatSessionForApi(session) {
    if (!session || !session.items || session.items.length === 0) {
        return null;
    }
    
    return {
        session_identifier: session.sessionId,
        start_time: new Date(session.startTime).toISOString(),
        end_time: new Date(session.endTime).toISOString(),
        items: session.items.map(item => ({
            url: item.url,
            title: item.title || 'Untitled',
            visit_time: new Date(item.lastVisitTime || item.visitTime).toISOString(),
            url_hostname: item.urlHostname || safeGetHostname(item.url),
            url_pathname_clean: item.urlPathnameClean || '/',
            url_search_query: item.urlSearchQuery || ''
        })),
        duration_minutes: Math.round((session.endTime - session.startTime) / (1000 * 60))
    };
}

/**
 * Utility to safely extract hostname from URL
 * @param {string} rawUrl - Raw URL string
 * @returns {string} Hostname or empty string
 */
function safeGetHostname(rawUrl) {
    if (typeof rawUrl !== 'string' || rawUrl.length === 0) return '';
    try {
        return new URL(rawUrl).hostname;
    } catch (e) {
        try {
            return new URL('http://' + rawUrl).hostname;
        } catch (e2) {
            return '';
        }
    }
}
