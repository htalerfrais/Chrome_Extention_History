class HistoryService {
    constructor() {
        this.MAX_ITEMS = 5000;
    }
    
    async initialize() {
        try {
            console.log('Initializing history collection...');
            
            // Check if we already have history in storage
            const stored = await chrome.storage.local.get(['historyItems']);
            if (stored.historyItems && stored.historyItems.length > 0) {
                console.log(`Found ${stored.historyItems.length} existing history items in storage`);
                return;
            }
            
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
                        const processed = this.preprocessItems(results);
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
        
        const dated = formatDates(rawItems);
        const withUrlFeatures = addUrlFeatures(dated);
        const filtered = filterHistoryURL(withUrlFeatures);
        
        return filtered;
    }
    
    async addItem(rawItem) {
        try {
            const titleMissing = !rawItem.title || 
                                 rawItem.title.trim() === '' || 
                                 rawItem.title === 'Untitled';
            
            if (titleMissing) {
                console.log(`[HISTORY] Title missing for ${rawItem.url}, waiting for page load...`);
                await new Promise(resolve => setTimeout(resolve, 2000));
                const updatedTitle = await this.fetchTitleFromHistory(rawItem.url);
                
                if (updatedTitle && updatedTitle.trim() !== '') {
                    rawItem.title = updatedTitle;
                    console.log(`[HISTORY] Title fetched: "${updatedTitle}"`);
                } else {
                    console.log(`[HISTORY] Title still unavailable for ${rawItem.url}`);
                }
            }
            
            const processed = this.preprocessItems([rawItem]);
            
            if (processed.length === 0) {
                console.log('Item filtered out (duplicate):', rawItem.url);
                return null;
            }
            
            const processedItem = processed[0];
            
            // Get existing items
            const stored = await chrome.storage.local.get({ historyItems: [] });
            let historyItems = stored.historyItems || [];
            
            // Deduplicate against the last item in storage
            if (historyItems.length > 0) {
                const lastItem = historyItems[historyItems.length - 1];
                const deduped = filterHistoryURL([lastItem, processedItem]);
                if (deduped.length === 1) {
                    console.log('Item filtered out (duplicate of last stored):', rawItem.url);
                    return null;
                }
            }

            historyItems.push(processedItem);
            
            if (historyItems.length > this.MAX_ITEMS) {
                historyItems = historyItems.slice(-this.MAX_ITEMS);
            }
            
            // Save back to storage
            await chrome.storage.local.set({ historyItems });
            
            console.log(`Added new history item: ${processedItem.title || 'Untitled'} - ${processedItem.url}`);
            return processedItem;
            
        } catch (error) {
            console.error('Error adding history item:', error);
            return null;
        }
    }
    
    async fetchTitleFromHistory(url) {
        return new Promise((resolve) => {
            chrome.history.search({ text: url, maxResults: 5 }, (results) => {
                if (chrome.runtime.lastError) {
                    console.error('Error fetching title from history:', chrome.runtime.lastError);
                    resolve(null);
                    return;
                }
                
                // Find exact URL match
                const match = results.find(r => r.url === url);
                resolve(match?.title || null);
            });
        });
    }
    
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
