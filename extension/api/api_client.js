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
    
    // Send preprocessed sessions for clustering
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
