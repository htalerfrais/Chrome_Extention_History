// Background Service Worker - Main entry point
// Orchestrates all services and handles Chrome API events

// Import utilities and configs
importScripts('config/constants.js');
importScripts('config/api.config.js');
importScripts('utils/preprocess.js');
importScripts('utils/session.utils.js');

// Import services
importScripts('services/api.service.js');
importScripts('services/auth.service.js');
importScripts('services/history.service.js');
importScripts('services/session.service.js');

// Create service instances
// Note: Resolve circular dependency by creating ApiService with temporary authService,
// then updating authService reference after both are created
let authService;
let apiService;
let historyService;
let sessionService;

// Initialize all services
async function initialize() {
    try {
        console.log('Initializing extension services...');
        
        // Step 1: Create services (resolve circular dependency)
        // Create temporary authService for ApiService
        const tempAuthService = {
            getToken: async () => {
                const stored = await chrome.storage.local.get(['userToken']);
                return stored.userToken || null;
            }
        };
        
        apiService = new ApiService(config, tempAuthService);
        authService = new AuthService(apiService);
        
        // Update ApiService with real authService
        apiService.authService = authService;
        
        // Create other services
        historyService = new HistoryService();
        sessionService = new SessionService(historyService, apiService);
        
        // Step 2: Initialize services in order
        console.log('Initializing auth service...');
        await authService.initialize();
        
        console.log('Initializing history service...');
        await historyService.initialize();
        
        console.log('Initializing session service...');
        await sessionService.initialize();
        
        // Step 3: Start session tracking
        sessionService.startTracking();
        
        console.log('All services initialized successfully');
        
        // Expose services globally for bridge
        self.Services = {
            historyService,
            sessionService,
            apiService,
            authService
        };
        
    } catch (error) {
        console.error('Error initializing services:', error);
    }
}

// Handle new history item (real-time)
chrome.history.onVisited.addListener(async (rawItem) => {
    try {
        // Wait for services to be initialized
        if (!historyService || !sessionService) {
            console.log('Services not yet initialized, skipping history item');
            return;
        }
        
        // Add to history service (preprocesses and stores)
        const processedItem = await historyService.addItem(rawItem);
        
        if (processedItem) {
            // Add to session service (manages current session)
            await sessionService.addItem(processedItem);
        }
    } catch (error) {
        console.error('Error handling new history item:', error);
    }
});

// Handle messages from frontend (for window context)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    (async () => {
        try {
            // Wait for services to be initialized
            if (!self.Services) {
                // Wait a bit for initialization
                await new Promise(resolve => setTimeout(resolve, 500));
                if (!self.Services) {
                    sendResponse({ error: 'Services not initialized' });
                    return;
                }
            }
            
            const { historyService, sessionService, apiService } = self.Services;
            
            switch (request.action) {
                case 'ping':
                    sendResponse({ success: true });
                    break;
                    
                case 'getAllSessions':
                    const sessions = await sessionService.getAllSessions();
                    sendResponse({ sessions });
                    break;
                    
                case 'analyzeSession':
                    const result = await apiService.analyzeSession(request.session, request.options);
                    sendResponse(result);
                    break;
                    
                case 'sendChatMessage':
                    const chatResult = await apiService.sendChatMessage(
                        request.message,
                        request.conversationId,
                        request.history
                    );
                    sendResponse(chatResult);
                    break;
                    
                case 'checkApiHealth':
                    const healthResult = await apiService.checkHealth();
                    sendResponse(healthResult);
                    break;
                    
                default:
                    sendResponse({ error: 'Unknown action' });
            }
        } catch (error) {
            console.error('Error handling message:', error);
            sendResponse({ error: error.message });
        }
    })();
    
    return true; // Indicates we will send a response asynchronously
});

// Start initialization
initialize();
