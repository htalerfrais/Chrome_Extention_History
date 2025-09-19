// API Client for Chrome Extension History Backend
// Handles all communication with the clustering API

class ApiClient {
    constructor(config) {
        this.config = config;
    }
    
    // Generic API request method with retry logic
    async makeRequest(endpoint, options = {}) {
        const url = this.config.getEndpointUrl(endpoint);
        const headers = this.config.getRequestHeaders();
        
        const requestOptions = {
            method: options.method || 'GET',
            headers: { ...headers, ...options.headers },
            ...options
        };
        
        let lastError;
        
        for (let attempt = 1; attempt <= this.config.REQUEST_CONFIG.retries; attempt++) {
            try {
                console.log(`API Request (attempt ${attempt}): ${requestOptions.method} ${url}`);
                
                const response = await fetch(url, requestOptions);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                console.log(`API Response: Success`);
                return { success: true, data };
                
            } catch (error) {
                lastError = error;
                console.warn(`API Request failed (attempt ${attempt}):`, error.message);
                
                if (attempt < this.config.REQUEST_CONFIG.retries) {
                    await this.delay(this.config.REQUEST_CONFIG.retryDelay * attempt);
                }
            }
        }
        
        console.error('API Request failed after all retries:', lastError.message);
        return { success: false, error: lastError.message };
    }
    
    // Utility method for delays
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // Check API health
    async checkHealth() {
        return await this.makeRequest('health');
    }
    
    // Send sessions for clustering
    async clusterSessions(sessions) {
        if (!sessions || sessions.length === 0) {
            return { success: false, error: 'No sessions provided' };
        }
        
        console.log(`Sending ${sessions.length} sessions for clustering`);
        
        return await this.makeRequest('cluster', {
            method: 'POST',
            body: JSON.stringify(sessions)
        });
    }
    
    // Get clustering preview
    async previewSessions(sessions) {
        if (!sessions || sessions.length === 0) {
            return { success: false, error: 'No sessions provided' };
        }
        
        console.log(`Getting preview for ${sessions.length} sessions`);
        
        return await this.makeRequest('preview', {
            method: 'POST',
            body: JSON.stringify(sessions)
        });
    }
    
    // Convert Chrome history to API format
    formatHistoryForApi(chromeHistory) {
        try {
            // Group history items into sessions (simple time-based grouping)
            const sessions = this.groupIntoSessions(chromeHistory);
            
            // Format sessions for API
            return sessions.map(session => ({
                session_id: session.sessionId,
                start_time: new Date(session.startTime).toISOString(),
                end_time: new Date(session.endTime).toISOString(),
                items: session.items.map(item => ({
                    url: item.url,
                    title: item.title || 'Untitled',
                    visit_time: new Date(item.lastVisitTime || item.visitTime).toISOString(),
                    visit_count: item.visitCount || 1,
                    typed_count: item.typedCount || 0
                })),
                duration_minutes: Math.round((session.endTime - session.startTime) / (1000 * 60))
            }));
        } catch (error) {
            console.error('Error formatting history for API:', error);
            return [];
        }
    }
    
    // Simple session grouping by time gaps
    groupIntoSessions(historyItems, sessionGapMinutes = window.ExtensionConstants?.SESSION_GAP_MINUTES || 30) {
        if (!historyItems || historyItems.length === 0) {
            return [];
        }
        
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
                    sessionId: `session_${sessions.length + 1}_${Date.now()}`,
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
        
        // Filter out sessions with too few items
        return sessions.filter(session => session.items.length >= (window.ExtensionConstants?.MIN_SESSION_ITEMS || 2));
    }
}

// Create and export API client instance
const apiClient = new ApiClient(window.ExtensionConfig || require('./config.js'));

// Make available globally
if (typeof window !== 'undefined') {
    window.ApiClient = apiClient;
}

// For Node.js/module environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ApiClient;
}
