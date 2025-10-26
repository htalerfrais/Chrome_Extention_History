// Session Management for Chrome Extension History
// Handles grouping of history items into time-based sessions

class SessionManager {
    constructor() {
        this.constants = window.ExtensionConstants || {};
    }
    
    /**
     * Generate a deterministic session identifier based on session content
     * @param {number} startTime - Session start timestamp
     * @param {number} endTime - Session end timestamp
     * @param {Array} items - Session items
     * @returns {string} Deterministic session identifier
     */
    generateSessionIdentifier(startTime, endTime, items) {
        // Create a stable string from session characteristics
        // Use start/end times and first/last URLs to ensure uniqueness
        const urls = items.map(item => item.url || '').filter(url => url.length > 0);
        const firstUrl = urls[0] || '';
        const lastUrl = urls[urls.length - 1] || '';
        
        // Create a stable hash string combining key session attributes
        const hashInput = `${startTime}_${endTime}_${firstUrl}_${lastUrl}_${items.length}`;
        
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
     * @param {Array} historyItems - Raw Chrome history items
     * @param {number} sessionGapMinutes - Gap between sessions in minutes
     * @returns {Array} Array of session objects
     */
    groupIntoSessions(historyItems, sessionGapMinutes = this.constants.SESSION_GAP_MINUTES || 30) {
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
        
        // Now generate deterministic IDs for each session based on their actual content
        for (const session of sessions) {
            session.sessionId = this.generateSessionIdentifier(
                session.startTime,
                session.endTime,
                session.items
            );
        }
        
        // Filter out sessions with too few items
        const minItems = this.constants.MIN_SESSION_ITEMS || 2;
        const validSessions = sessions.filter(session => session.items.length >= minItems);
        
        console.log(`Created ${validSessions.length} valid sessions (filtered ${sessions.length - validSessions.length} small sessions)`);
        
        return validSessions;
    }
    
    /**
     * Formats sessions for API consumption
     * @param {Array} sessions - Session objects
     * @returns {Array} Formatted sessions for API
     */
    formatSessionsForApi(sessions) {
        if (!sessions || sessions.length === 0) {
            return [];
        }
        
        console.log(`Formatting ${sessions.length} sessions for API`);
        
        return sessions.map(session => ({
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
        }));
    }
    
    /**
     * Complete preprocessing pipeline: group into sessions and format for API
     * @param {Array} historyItems - Raw Chrome history items
     * @param {number} sessionGapMinutes - Gap between sessions in minutes
     * @returns {Array} Formatted sessions ready for API
     */
    processHistory(historyItems, sessionGapMinutes = this.constants.SESSION_GAP_MINUTES || 30) {
        try {
            console.log('Starting history preprocessing pipeline');
            
            // Step 1: Group into sessions
            const sessions = this.groupIntoSessions(historyItems, sessionGapMinutes);
            
            // Step 2: Format for API
            const formattedSessions = this.formatSessionsForApi(sessions);
            
            console.log(`Preprocessing complete: ${formattedSessions.length} sessions ready for API`);
            console.log('Formatted sessions:', formattedSessions);
            return formattedSessions;
            
        } catch (error) {
            console.error('Error in history preprocessing:', error);
            return [];
        }
    }
    
    /**
     * Get session statistics for debugging
     * @param {Array} sessions - Session objects
     * @returns {Object} Session statistics
     */
    getSessionStats(sessions) {
        if (!sessions || sessions.length === 0) {
            return {
                totalSessions: 0,
                totalItems: 0,
                averageItemsPerSession: 0,
                averageDurationMinutes: 0,
                dateRange: null
            };
        }
        
        const totalItems = sessions.reduce((sum, session) => sum + session.items.length, 0);
        const totalDuration = sessions.reduce((sum, session) => {
            return sum + (session.endTime - session.startTime);
        }, 0);
        
        const allTimes = sessions.flatMap(session => [session.startTime, session.endTime]);
        
        return {
            totalSessions: sessions.length,
            totalItems: totalItems,
            averageItemsPerSession: Math.round(totalItems / sessions.length),
            averageDurationMinutes: Math.round(totalDuration / (sessions.length * 60 * 1000)),
            dateRange: {
                start: new Date(Math.min(...allTimes)),
                end: new Date(Math.max(...allTimes))
            }
        };
    }
}

// Create and export session manager instance
const sessionManager = new SessionManager();

// Make available globally
if (typeof window !== 'undefined') {
    window.SessionManager = sessionManager;
}

// For Node.js/module environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SessionManager;
}

// Utility used in formatting when the enriched hostname is missing
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
