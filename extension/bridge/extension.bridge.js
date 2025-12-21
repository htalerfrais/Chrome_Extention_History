// Extension Bridge - Frontend API Interface
// Provides a clean interface for React frontend to access extension services

class ExtensionBridge {
    constructor() {
        this.isReady = false;
        this.readyPromise = null;
    }
    
    /**
     * Wait for services to be ready
     * @param {number} timeout - Timeout in milliseconds
     * @returns {Promise<void>}
     */
    async waitForReady(timeout = 5000) {
        if (this.isReady) {
            return;
        }
        
        if (this.readyPromise) {
            return this.readyPromise;
        }
        
        this.readyPromise = new Promise((resolve, reject) => {
            const startTime = Date.now();
            
            const checkReady = () => {
                // Check if services are available (in service worker context)
                if (typeof self !== 'undefined' && self.Services) {
                    const services = self.Services;
                    if (services.historyService && 
                        services.sessionService && 
                        services.apiService && 
                        services.authService) {
                        this.isReady = true;
                        resolve();
                        return;
                    }
                }
                
                // For window context, check if chrome.runtime is available
                // and try to ping the service worker
                if (typeof chrome !== 'undefined' && chrome.runtime) {
                    chrome.runtime.sendMessage({ action: 'ping' }, (response) => {
                        if (!chrome.runtime.lastError) {
                            this.isReady = true;
                            resolve();
                            return;
                        }
                    });
                }
                
                if (Date.now() - startTime > timeout) {
                    reject(new Error('Timeout waiting for extension services'));
                    return;
                }
                
                setTimeout(checkReady, 100);
            };
            
            checkReady();
        });
        
        return this.readyPromise;
    }
    
    /**
     * Get all sessions (completed + current)
     * @returns {Promise<Array>}
     */
    async getAllSessions() {
        await this.waitForReady();
        
        // Use message passing to communicate with service worker
        return new Promise((resolve, reject) => {
            chrome.runtime.sendMessage(
                { action: 'getAllSessions' },
                (response) => {
                    if (chrome.runtime.lastError) {
                        reject(new Error(chrome.runtime.lastError.message));
                    } else if (response.error) {
                        reject(new Error(response.error));
                    } else {
                        resolve(response.sessions || []);
                    }
                }
            );
        });
    }
    
    /**
     * Analyze a session
     * @param {Object} session - Session object
     * @param {Object} options - Options (force: boolean)
     * @returns {Promise<{success: boolean, data?: any, error?: string}>}
     */
    async analyzeSession(session, options = {}) {
        await this.waitForReady();
        
        // Use message passing to communicate with service worker
        return new Promise((resolve, reject) => {
            chrome.runtime.sendMessage(
                { action: 'analyzeSession', session, options },
                (response) => {
                    if (chrome.runtime.lastError) {
                        reject(new Error(chrome.runtime.lastError.message));
                    } else if (response.error) {
                        reject(new Error(response.error));
                    } else {
                        resolve(response);
                    }
                }
            );
        });
    }
    
    /**
     * Send chat message
     * @param {string} message - User message
     * @param {string|null} conversationId - Optional conversation ID
     * @param {Array} history - Optional conversation history
     * @returns {Promise<{success: boolean, data?: any, error?: string}>}
     */
    async sendChatMessage(message, conversationId = null, history = []) {
        await this.waitForReady();
        
        // Use message passing to communicate with service worker
        return new Promise((resolve, reject) => {
            chrome.runtime.sendMessage(
                { action: 'sendChatMessage', message, conversationId, history },
                (response) => {
                    if (chrome.runtime.lastError) {
                        reject(new Error(chrome.runtime.lastError.message));
                    } else if (response.error) {
                        reject(new Error(response.error));
                    } else {
                        resolve(response);
                    }
                }
            );
        });
    }
    
    /**
     * Check API health
     * @returns {Promise<{success: boolean, data?: any, error?: string}>}
     */
    async checkApiHealth() {
        await this.waitForReady();
        
        // Use message passing to communicate with service worker
        return new Promise((resolve, reject) => {
            chrome.runtime.sendMessage(
                { action: 'checkApiHealth' },
                (response) => {
                    if (chrome.runtime.lastError) {
                        reject(new Error(chrome.runtime.lastError.message));
                    } else if (response.error) {
                        reject(new Error(response.error));
                    } else {
                        resolve(response);
                    }
                }
            );
        });
    }
    
    /**
     * Get extension configuration
     * @returns {Object} Config object
     */
    getConfig() {
        const config = (typeof window !== 'undefined' ? window.ExtensionConfig : 
                       typeof self !== 'undefined' ? self.ExtensionConfig : null);
        
        if (!config) {
            console.warn('ExtensionConfig not available, using defaults');
            return {
                currentEnvironment: 'development',
                getApiBaseUrl: () => 'http://localhost:8000'
            };
        }
        
        return config;
    }
    
    /**
     * Get extension constants
     * @returns {Object} Constants object
     */
    getConstants() {
        const constants = (typeof window !== 'undefined' ? window.ExtensionConstants : 
                          typeof self !== 'undefined' ? self.ExtensionConstants : null);
        
        if (!constants) {
            console.warn('ExtensionConstants not available, using defaults');
            return {
                SESSION_GAP_MINUTES: 120,
                HISTORY_DAYS_BACK: 7,
                DAY_MS: 24 * 60 * 60 * 1000,
                MAX_CLUSTER_ITEMS_DISPLAY: 5,
                STATUS_CHECKING_API: 'Checking API connection...',
                STATUS_FETCHING_HISTORY: 'Fetching history...',
                STATUS_PROCESSING_SESSIONS: 'Processing sessions...',
                STATUS_ANALYZING_PATTERNS: 'Analyzing patterns...',
                STATUS_ANALYSIS_COMPLETE: 'Analysis complete',
                STATUS_ANALYSIS_FAILED: 'Analysis failed',
                ERROR_NO_HISTORY: 'No history found',
                ERROR_NO_SESSIONS: 'No sessions could be created',
                ERROR_CLUSTERING_FAILED: 'Clustering failed'
            };
        }
        
        return constants;
    }
    
    /**
     * Check if services are ready
     * @returns {boolean}
     */
    isServicesReady() {
        return this.isReady || (typeof self !== 'undefined' && self.Services);
    }
}

// Create and expose singleton instance
const extensionAPI = new ExtensionBridge();

// Expose globally
if (typeof window !== 'undefined') {
    window.ExtensionAPI = extensionAPI;
}

if (typeof self !== 'undefined') {
    self.ExtensionAPI = extensionAPI;
}
