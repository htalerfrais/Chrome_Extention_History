// API Service - Communication with backend
// Handles all HTTP requests to the FastAPI backend

class ApiService {
    constructor(config, authService) {
        this.config = config;
        this.authService = authService;
    }
    
    /**
     * Generic API request method with retry logic
     * @param {string} endpoint - Endpoint name (e.g., 'health', 'cluster-session')
     * @param {Object} options - Request options (method, body, query, headers)
     * @returns {Promise<{success: boolean, data?: any, error?: string}>}
     */
    async makeRequest(endpoint, options = {}) {
        const query = options.query || null;
        const urlBase = this.config.getEndpointUrl(endpoint);
        const url = query ? `${urlBase}?${new URLSearchParams(query).toString()}` : urlBase;
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
                    const delayMs = this.config.REQUEST_CONFIG.retryDelay * attempt;
                    await this.delay(delayMs);
                }
            }
        }
        
        console.error('API Request failed after all retries:', lastError.message);
        return { success: false, error: lastError.message };
    }
    
    /**
     * Utility method for delays
     * @param {number} ms - Milliseconds to delay
     * @returns {Promise<void>}
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * Check API health
     * @returns {Promise<{success: boolean, data?: any, error?: string}>}
     */
    async checkHealth() {
        return await this.makeRequest('health');
    }
    
    /**
     * Authenticate with backend using Google token
     * @param {string} token - Google OAuth token
     * @returns {Promise<{success: boolean, data?: any, error?: string}>}
     */
    async authenticate(token) {
        return await this.makeRequest('authenticate', {
            method: 'POST',
            body: JSON.stringify({ token })
        });
    }
    
    /**
     * Send single session for clustering
     * @param {Object} session - Session object (formatted for API)
     * @param {Object} opts - Options (force: boolean)
     * @returns {Promise<{success: boolean, data?: any, error?: string}>}
     */
    async analyzeSession(session, opts = {}) {
        if (!session || !session.items || session.items.length === 0) {
            return { success: false, error: 'No valid session provided' };
        }
        
        // Get user token from auth service
        const userToken = await this.authService.getToken();
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
            body: JSON.stringify(sessionWithUser),
            query: opts.force ? { force: 'true' } : undefined
        });
        
        if (result.success) {
            console.log(`Received clustering result for session ${session.session_identifier} with ${result.data.clusters?.length || 0} clusters`);
        }
        
        return result;
    }
    
    /**
     * Send chat message
     * @param {string} message - User message
     * @param {string|null} conversationId - Optional conversation ID
     * @param {Array} history - Optional conversation history
     * @returns {Promise<{success: boolean, data?: any, error?: string}>}
     */
    async sendChatMessage(message, conversationId = null, history = []) {
        if (!message || message.trim().length === 0) {
            return { success: false, error: 'Message cannot be empty' };
        }
        
        // Get user token from auth service
        const userToken = await this.authService.getToken();
        
        console.log(`Sending chat message${conversationId ? ` for conversation ${conversationId}` : ''}`);
        
        const payload = {
            message: message,
            conversation_id: conversationId,
            history: history,
            provider: "google",
            user_token: userToken || null
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
}
