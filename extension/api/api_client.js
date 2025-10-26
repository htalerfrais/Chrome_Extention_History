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
    
    // Send single session for clustering
    async clusterSession(session) {
        if (!session || !session.items || session.items.length === 0) {
            return { success: false, error: 'No valid session provided' };
        }
        
        // Get user token from chrome.storage
        let userToken;
        try {
            const stored = await chrome.storage.local.get('userToken');
            userToken = stored.userToken;
        } catch (e) {
            console.error('Failed to get user token from storage:', e);
        }
        
        if (!userToken) {
            return { success: false, error: 'User not authenticated' };
        }
        
        // Add user_token to session object
        const sessionWithUser = {
            ...session,
            user_token: userToken
        };
        
        console.log(`Sending session ${session.session_identifier} with ${session.items.length} items for clustering`);
        
        const result = await this.makeRequest('cluster-session', {
            method: 'POST',
            body: JSON.stringify(sessionWithUser)
        });
        
        if (result.success) {
            console.log(`Received clustering result for session ${session.session_identifier} with ${result.data.clusters?.length || 0} clusters`);
        }
        
        return result;
    }
    
    // Send chat message
    async sendChatMessage(message, conversationId = null, history = []) {
        if (!message || message.trim().length === 0) {
            return { success: false, error: 'Message cannot be empty' };
        }
        
        console.log(`Sending chat message${conversationId ? ` for conversation ${conversationId}` : ''}`);
        
        const payload = {
            message: message,
            conversation_id: conversationId,
            history: history,
            provider: "google"
        };
        
        const result = await this.makeRequest('chat', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        
        if (result.success) {
            console.log(`Received chat response for conversation ${result.data.conversation_id}`);
        }
        
        return result;
    }

    // Authenticate with Google
    async authenticateWithGoogle(token) {
        const result = await this.makeRequest('authenticate', {
            method: 'POST',
            body: JSON.stringify({ token })
        });
        return result;
    }
}

// Create and export API client instance
const apiClient = new ApiClient(
    (typeof window !== 'undefined' ? window.ExtensionConfig : 
     typeof self !== 'undefined' ? self.ExtensionConfig : 
     new Config())
);


// Make available globally
if (typeof window !== 'undefined') {
    window.ApiClient = apiClient;
}

// For service workers (background scripts)
if (typeof self !== 'undefined') {
    self.ApiClient = apiClient;
    // Expose authenticateWithGoogle function directly for convenience
    self.authenticateWithGoogle = apiClient.authenticateWithGoogle.bind(apiClient);
}

// For Node.js/module environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ApiClient;
}
