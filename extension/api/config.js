// Configuration for Chrome Extension History
// Handles API endpoints and environment settings

class Config {
    constructor() {
        // API Configuration
        this.API_ENDPOINTS = {
            // Development (local Docker)
            development: {
                baseUrl: 'http://localhost:8000',
                cluster: '/cluster',
                health: '/health'
            },
            // Production (to be updated when deployed)
            production: {
                baseUrl: 'https://your-production-api.com',
                cluster: '/cluster',
                health: '/health'
            }
        };
        
        // Default to development
        this.currentEnvironment = 'development';
        
        // Request configuration
        this.REQUEST_CONFIG = {
            timeout: window.ExtensionConstants?.API_REQUEST_TIMEOUT_MS || 30000, // 30 seconds
            retries: window.ExtensionConstants?.API_RETRIES || 3,
            retryDelay: window.ExtensionConstants?.API_RETRY_DELAY_MS || 1000 // 1 second
        };
        
        // Clustering configuration
        this.CLUSTERING_CONFIG = {
            maxClusters: window.ExtensionConstants?.MAX_CLUSTERS_DEFAULT || 10,
            minClusterSize: window.ExtensionConstants?.MIN_CLUSTER_SIZE_DEFAULT || 2,
            confidenceThreshold: window.ExtensionConstants?.CONFIDENCE_THRESHOLD || 0.5
        };
    }
    
    // Get current API base URL
    getApiBaseUrl() {
        return this.API_ENDPOINTS[this.currentEnvironment].baseUrl;
    }
    
    // Get full endpoint URL
    getEndpointUrl(endpoint) {
        const baseUrl = this.getApiBaseUrl();
        const path = this.API_ENDPOINTS[this.currentEnvironment][endpoint];
        return `${baseUrl}${path}`;
    }
    
    // Switch environment
    setEnvironment(env) {
        if (this.API_ENDPOINTS[env]) {
            this.currentEnvironment = env;
            console.log(`Switched to ${env} environment`);
        } else {
            console.warn(`Unknown environment: ${env}`);
        }
    }
    
    // Check if API is available
    async checkApiHealth() {
        try {
            const response = await fetch(this.getEndpointUrl('health'), {
                method: 'GET',
                timeout: window.ExtensionConstants?.API_TIMEOUT_MS || 5000
            });
            
            if (response.ok) {
                const data = await response.json();
                return { available: true, data };
            } else {
                return { available: false, error: `HTTP ${response.status}` };
            }
        } catch (error) {
            return { available: false, error: error.message };
        }
    }
    
    // Get request headers
    getRequestHeaders() {
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
    }
}

// Export singleton instance
const config = new Config();

// Auto-detect environment based on Chrome extension context
// In development, you might want to manually set this
if (typeof chrome !== 'undefined' && chrome.runtime) {
    // Try to detect if we're in development by checking if localhost is accessible
    config.checkApiHealth().then(result => {
        if (!result.available) {
            console.warn('Development API not available, consider switching to production');
            // Uncomment the next line to auto-switch to production
            // config.setEnvironment('production');
        } else {
            console.log('Development API is available');
        }
    });
}

// Make available globally
if (typeof window !== 'undefined') {
    window.ExtensionConfig = config;
}

// For Node.js/module environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = config;
}
