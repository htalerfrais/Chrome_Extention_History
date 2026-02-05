// Auth Service - Google OAuth authentication
// Handles token management and validation

class AuthService {
    constructor(apiService) {
        this.apiService = apiService;
    }
    
    /**
     * Initialize authentication
     * Obtains Google token and validates with backend
     * @returns {Promise<void>}
     */
    async initialize() {
        try {
            // Try to get existing token from storage first
            const stored = await chrome.storage.local.get(['userToken']);
            if (stored.userToken) {
                console.log('Found existing token in storage, validating...');
                // Validate token is still valid with backend
                const validationResult = await this.apiService.authenticate(stored.userToken);
                if (validationResult.success) {
                    console.log('Existing token is still valid');
                    return;
                } else {
                    console.log('Existing token is invalid, getting new token...');
                    // Token is invalid, remove it and get a new one
                    await chrome.storage.local.remove(['userToken']);
                }
            }
            
            // Get new token from Google
            const token = await this.getGoogleToken();
            if (!token) {
                console.error('Failed to obtain Google token');
                return;
            }
            
            // Validate token with backend
            const result = await this.apiService.authenticate(token);
            if (!result.success) {
                console.error('Backend authentication failed:', result.error);
                return;
            }
            
            // Store token
            await chrome.storage.local.set({ userToken: token });
            console.log('User token stored and validated');
            
        } catch (error) {
            console.error('Error initializing auth:', error);
        }
    }
    
    /**
     * Get Google OAuth token
     * @returns {Promise<string|null>}
     */
    async getGoogleToken() {
        return new Promise((resolve) => {
            chrome.identity.getAuthToken({ interactive: true }, (token) => {
                if (chrome.runtime.lastError || !token) {
                    console.error('Auth error:', chrome.runtime.lastError?.message || 'No token');
                    resolve(null);
                    return;
                }
                resolve(token);
            });
        });
    }
    
    /**
     * Get stored user token
     * @returns {Promise<string|null>}
     */
    async getToken() {
        try {
            const stored = await chrome.storage.local.get(['userToken']);
            return stored.userToken || null;
        } catch (error) {
            console.error('Error getting token:', error);
            return null;
        }
    }
    
    /**
     * Refresh token if necessary
     * @returns {Promise<void>}
     */
    async refreshToken() {
        try {
            // Remove old token
            await chrome.storage.local.remove(['userToken']);
            
            // Get new token
            const token = await this.getGoogleToken();
            if (!token) {
                console.error('Failed to refresh token');
                return;
            }
            
            // Validate with backend
            const result = await this.apiService.authenticate(token);
            if (!result.success) {
                console.error('Backend authentication failed after refresh:', result.error);
                return;
            }
            
            // Store new token
            await chrome.storage.local.set({ userToken: token });
            console.log('Token refreshed successfully');
            
        } catch (error) {
            console.error('Error refreshing token:', error);
        }
    }
}
