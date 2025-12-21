// History Service - Collect and preprocess browsing history
// Manages history items collection and preprocessing pipeline

class HistoryService {
    constructor() {
        this.MAX_ITEMS = 5000;
    }
    
    /**
     * Initialize history collection
     * Collects initial history and preprocesses it
     * @returns {Promise<void>}
     */
    async initialize() {
        try {
            console.log('Initializing history collection...');
            
            // Check if we already have history in storage
            const stored = await chrome.storage.local.get(['historyItems']);
            if (stored.historyItems && stored.historyItems.length > 0) {
                console.log(`Found ${stored.historyItems.length} existing history items in storage`);
                return;
            }
            
            // Collect initial history
            await this.collectInitialHistory();
            
        } catch (error) {
            console.error('Error initializing history service:', error);
        }
    }
    
    /**
     * Collect initial history from Chrome
     * @returns {Promise<void>}
     */
    async collectInitialHistory() {
        return new Promise((resolve, reject) => {
            chrome.history.search(
                { text: '', maxResults: this.MAX_ITEMS, startTime: 0 },
                async (results) => {
                    if (chrome.runtime.lastError) {
                        console.error('Error collecting history:', chrome.runtime.lastError);
                        reject(chrome.runtime.lastError);
                        return;
                    }
                    
                    try {
                        // Preprocess all items
                        const processed = this.preprocessItems(results);
                        
                        // Store in chrome.storage.local
                        await chrome.storage.local.set({ historyItems: processed });
                        
                        console.log(`Collected and preprocessed ${results.length} items (${processed.length} after filtering)`);
                        resolve();
                    } catch (error) {
                        console.error('Error preprocessing history:', error);
                        reject(error);
                    }
                }
            );
        });
    }
    
    /**
     * Preprocess items through the full pipeline
     * @param {Array} rawItems - Raw Chrome history items
     * @returns {Array} Preprocessed items
     */
    preprocessItems(rawItems) {
        if (!Array.isArray(rawItems) || rawItems.length === 0) {
            return [];
        }
        
        // Pipeline: formatDates → addUrlFeatures → filterHistoryURL
        const dated = formatDates(rawItems);
        const withUrlFeatures = addUrlFeatures(dated);
        const filtered = filterHistoryURL(withUrlFeatures);
        
        return filtered;
    }
    
    /**
     * Add a new item to history
     * Preprocesses and stores it
     * @param {Object} rawItem - Raw Chrome history item
     * @returns {Promise<Object|null>} Preprocessed item or null if filtered out
     */
    async addItem(rawItem) {
        try {
            // Preprocess the single item
            const processed = this.preprocessItems([rawItem]);
            
            if (processed.length === 0) {
                console.log('Item filtered out (duplicate):', rawItem.url);
                return null;
            }
            
            const processedItem = processed[0];
            
            // Get existing items
            const stored = await chrome.storage.local.get({ historyItems: [] });
            let historyItems = stored.historyItems || [];
            
            // Add new item
            historyItems.push(processedItem);
            
            // Limit size
            if (historyItems.length > this.MAX_ITEMS) {
                historyItems = historyItems.slice(-this.MAX_ITEMS);
            }
            
            // Save back to storage
            await chrome.storage.local.set({ historyItems });
            
            console.log(`Added new history item: ${processedItem.url}`);
            return processedItem;
            
        } catch (error) {
            console.error('Error adding history item:', error);
            return null;
        }
    }
    
    /**
     * Get all history items from storage
     * @returns {Promise<Array>} Array of preprocessed history items
     */
    async getAllItems() {
        try {
            const stored = await chrome.storage.local.get({ historyItems: [] });
            return stored.historyItems || [];
        } catch (error) {
            console.error('Error getting history items:', error);
            return [];
        }
    }
}
