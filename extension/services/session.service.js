// Session Service - Event-Sourcing Architecture
// Derives sessions on-demand from history items with intelligent caching

class SessionService {
    constructor(historyService, apiService) {
        this.historyService = historyService;
        this.apiService = apiService;
        
        // Cache for performance optimization
        this.completedSessionsCache = null;  // Immutable completed sessions
        this.currentSessionCache = null;      // Volatile current session
        this.lastProcessedItemCount = 0;     // Detect item changes
        
        // Track analyzed sessions
        this.analyzedSessionIds = new Set(); // session_identifiers already sent to backend
        
        // Alarm for background session checking
        this.CHECK_ALARM_NAME = 'checkClosedSessions';
        
        // Get constants
        const constants = (typeof self !== 'undefined' ? self.ExtensionConstants : 
                          typeof window !== 'undefined' ? window.ExtensionConstants : {});
        this.SESSION_GAP_MS = (constants.SESSION_GAP_MINUTES || 30) * 60 * 1000;
        this.MAX_SESSION_DURATION_MS = (constants.MAX_SESSION_DURATION_MINUTES || 90) * 60 * 1000;
        this.MIN_SESSION_ITEMS = constants.MIN_SESSION_ITEMS || 2;
    }
    
    /**
     * Initialize session service
     * Loads analyzed session IDs and sets up alarm listener
     * @returns {Promise<void>}
     */
    async initialize() {
        try {
            console.log('[SESSION] Initializing session service (event-sourcing mode)...');
            
            // Load analyzed session IDs from storage
            const stored = await chrome.storage.local.get(['analyzedSessionIds']);
            this.analyzedSessionIds = new Set(stored.analyzedSessionIds || []);
            
            // Limit to 200 most recent IDs to prevent unbounded growth
            if (this.analyzedSessionIds.size > 200) {
                const arr = [...this.analyzedSessionIds];
                this.analyzedSessionIds = new Set(arr.slice(-200));
                await this.saveAnalyzedIds();
            }
            
            console.log(`[SESSION] Loaded ${this.analyzedSessionIds.size} analyzed session IDs`);
            
            // Register alarm listener
            chrome.alarms.onAlarm.addListener((alarm) => {
                if (alarm.name === this.CHECK_ALARM_NAME) {
                    console.log('[SESSION] Alarm triggered: checking closed sessions');
                    this.checkAndAnalyzeClosedSessions();
                }
            });
            
            console.log('[SESSION] Session service initialized');
            
            // Check for closed sessions after a short delay (non-blocking)
            // This handles sessions that closed while the service worker was idle
            setTimeout(() => {
                console.log('[SESSION] Running deferred check for closed sessions...');
                this.checkAndAnalyzeClosedSessions();
            }, 2000);
            
        } catch (error) {
            console.error('[SESSION] Error initializing session service:', error);
        }
    }
    
    /**
     * Called when a new history item is added
     * Reprograms the alarm to check for closed sessions
     * @returns {Promise<void>}
     */
    async onNewItem() {
        try {
            // Reprogram alarm: check after gap + 1 minute margin
            const delayMinutes = Math.ceil((this.SESSION_GAP_MS / 60000) + 1);
            
            await chrome.alarms.clear(this.CHECK_ALARM_NAME);
            await chrome.alarms.create(this.CHECK_ALARM_NAME, {
                delayInMinutes: delayMinutes
            });
            
            console.log(`[SESSION] Alarm reprogrammed: check in ${delayMinutes} min`);
            
        } catch (error) {
            console.error('[SESSION] Error reprogramming alarm:', error);
        }
    }
    
    /**
     * Derive all sessions from history items (event-sourcing projection)
     * @param {Array} items - History items
     * @returns {Object} { completed: Array, current: Object|null }
     */
    deriveAllSessions(items) {
        if (!items || items.length === 0) {
            return { completed: [], current: null };
        }
        
        // Sort by timestamp
        const sorted = [...items].sort((a, b) => {
            const timeA = a.visitTime || a.lastVisitTime || 0;
            const timeB = b.visitTime || b.lastVisitTime || 0;
            return timeA - timeB;
        });
        
        const sessions = [];
        let session = null;
        
        for (const item of sorted) {
            const itemTime = item.visitTime || item.lastVisitTime;
            
            if (!session) {
                // Start first session
                session = {
                    startTime: itemTime,
                    endTime: itemTime,
                    items: [item]
                };
            } else {
                const gap = itemTime - session.endTime;
                const duration = itemTime - session.startTime;
                
                // Check if we should close current session
                if (gap > this.SESSION_GAP_MS || duration > this.MAX_SESSION_DURATION_MS) {
                    // Generate sessionId and add to completed
                    session.sessionId = generateSessionId(
                        session.startTime,
                        session.endTime,
                        session.items
                    );
                    sessions.push(session);
                    
                    // Start new session
                    session = {
                        startTime: itemTime,
                        endTime: itemTime,
                        items: [item]
                    };
                } else {
                    // Add to current session
                    session.items.push(item);
                    session.endTime = itemTime;
                }
            }
        }
        
        // Handle last session
        if (session) {
            const now = Date.now();
            const timeSinceLastActivity = now - session.endTime;
            
            if (timeSinceLastActivity > this.SESSION_GAP_MS) {
                // Session is closed
                session.sessionId = generateSessionId(
                    session.startTime,
                    session.endTime,
                    session.items
                );
                sessions.push(session);
                return { completed: sessions, current: null };
            } else {
                // Session is still active
                session.sessionId = generateSessionId(
                    session.startTime,
                    session.endTime,
                    session.items
                );
                return { completed: sessions, current: session };
            }
        }
        
        return { completed: sessions, current: null };
    }
    
    /**
     * Incremental session derivation (optimization for new items)
     * @param {Array} newItems - Newly added items since last derivation
     * @param {Object|null} existingCurrent - Previous current session
     * @returns {Object} { newCompleted: Array, current: Object|null }
     */
    deriveSessionsIncremental(newItems, existingCurrent) {
        const newCompleted = [];
        let session = existingCurrent;
        
        for (const item of newItems) {
            const itemTime = item.visitTime || item.lastVisitTime;
            
            if (!session) {
                // No current session, start new one
                session = {
                    startTime: itemTime,
                    endTime: itemTime,
                    items: [item]
                };
            } else {
                const gap = itemTime - session.endTime;
                const duration = itemTime - session.startTime;
                
                if (gap > this.SESSION_GAP_MS || duration > this.MAX_SESSION_DURATION_MS) {
                    // Close current session
                    session.sessionId = generateSessionId(
                        session.startTime,
                        session.endTime,
                        session.items
                    );
                    newCompleted.push(session);
                    
                    // Start new session
                    session = {
                        startTime: itemTime,
                        endTime: itemTime,
                        items: [item]
                    };
                } else {
                    // Add to current session
                    session.items.push(item);
                    session.endTime = itemTime;
                }
            }
        }
        
        // Generate sessionId for current session if exists
        if (session) {
            session.sessionId = generateSessionId(
                session.startTime,
                session.endTime,
                session.items
            );
        }
        
        return { newCompleted, current: session };
    }
    
    /**
     * Get all sessions with intelligent caching
     * @returns {Promise<Array>} Array of formatted sessions for API
     */
    async getAllSessions() {
        try {
            const items = await this.historyService.getAllItems();
            
            // Case 1: No items
            if (items.length === 0) {
                console.log('[SESSION] No items, returning empty sessions');
                return [];
            }
            
            // Case 2: Same number of items - use cache, check if current session closed by timeout
            if (items.length === this.lastProcessedItemCount && this.completedSessionsCache !== null) {
                console.log('[SESSION] Item count unchanged, using cache');
                
                // Check if current session should now be closed
                if (this.currentSessionCache) {
                    const now = Date.now();
                    const gap = now - this.currentSessionCache.endTime;
                    
                    if (gap > this.SESSION_GAP_MS) {
                        console.log('[SESSION] Current session now closed by timeout');
                        const formatted = formatSessionForApi(this.currentSessionCache);
                        if (formatted) {
                            this.completedSessionsCache.push(formatted);
                        }
                        this.currentSessionCache = null;
                    }
                }
                
                // Return cached results
                const result = [...this.completedSessionsCache];
                if (this.currentSessionCache) {
                    const formatted = formatSessionForApi(this.currentSessionCache);
                    if (formatted) result.push(formatted);
                }
                
                console.log(`[SESSION] Returning ${result.length} sessions from cache`);
                return result;
            }
            
            // Case 3: New items added - incremental derivation
            if (items.length > this.lastProcessedItemCount && this.completedSessionsCache !== null) {
                console.log(`[SESSION] ${items.length - this.lastProcessedItemCount} new items, incremental derivation`);
                
                const newItems = items.slice(this.lastProcessedItemCount);
                const { newCompleted, current } = this.deriveSessionsIncremental(
                    newItems,
                    this.currentSessionCache
                );
                
                // Add newly completed sessions to cache
                for (const session of newCompleted) {
                    const formatted = formatSessionForApi(session);
                    if (formatted) {
                        this.completedSessionsCache.push(formatted);
                    }
                }
                
                this.currentSessionCache = current;
                this.lastProcessedItemCount = items.length;
                
                // Return all sessions
                const result = [...this.completedSessionsCache];
                if (this.currentSessionCache) {
                    const formatted = formatSessionForApi(this.currentSessionCache);
                    if (formatted) result.push(formatted);
                }
                
                console.log(`[SESSION] Returning ${result.length} sessions (${this.completedSessionsCache.length} completed, ${current ? 1 : 0} current)`);
                return result;
            }
            
            // Case 4: Full recalculation (first call or items decreased)
            console.log('[SESSION] Full derivation of sessions');
            
            const { completed, current } = this.deriveAllSessions(items);
            
            // Format and cache
            this.completedSessionsCache = [];
            for (const session of completed) {
                const formatted = formatSessionForApi(session);
                if (formatted) {
                    this.completedSessionsCache.push(formatted);
                }
            }
            
            this.currentSessionCache = current;
            this.lastProcessedItemCount = items.length;
            
            // Return all sessions
            const result = [...this.completedSessionsCache];
            if (this.currentSessionCache) {
                const formatted = formatSessionForApi(this.currentSessionCache);
                if (formatted) result.push(formatted);
            }
            
            console.log(`[SESSION] Returning ${result.length} sessions (${this.completedSessionsCache.length} completed, ${current ? 1 : 0} current)`);
            return result;
            
        } catch (error) {
            console.error('[SESSION] Error getting all sessions:', error);
            return [];
        }
    }
    
    /**
     * Check for closed sessions and analyze them
     * Called by alarm or on initialization
     * @returns {Promise<void>}
     */
    async checkAndAnalyzeClosedSessions() {
        try {
            console.log('[SESSION] Checking for closed sessions to analyze...');
            
            const allSessions = await this.getAllSessions();
            
            // All sessions except potentially the last one (which might be current)
            // We need to check if the last session is actually completed
            const now = Date.now();
            const completedSessions = allSessions.filter(session => {
                if (!session.end_time) return false;
                const endTime = new Date(session.end_time).getTime();
                return (now - endTime) > this.SESSION_GAP_MS;
            });
            
            console.log(`[SESSION] Found ${completedSessions.length} completed sessions, ${this.analyzedSessionIds.size} already analyzed`);
            
            let analyzedCount = 0;
            
            for (const session of completedSessions) {
                const sessionId = session.session_identifier;
                
                // Skip if already analyzed
                if (this.analyzedSessionIds.has(sessionId)) {
                    continue;
                }
                
                // Skip sessions with too few items
                if (!session.items || session.items.length < this.MIN_SESSION_ITEMS) {
                    console.log(`[SESSION] Skipping session ${sessionId} (too few items: ${session.items?.length || 0})`);
                    continue;
                }
                
                console.log(`[SESSION] Analyzing session: ${sessionId} (${session.items.length} items)`);
                
                try {
                    const result = await this.apiService.analyzeSession(session, { force: false });
                    
                    if (result.success) {
                        console.log(`[SESSION] ✅ Session ${sessionId} analyzed successfully`);
                        this.analyzedSessionIds.add(sessionId);
                        analyzedCount++;
                        
                        // Save after each successful analysis
                        await this.saveAnalyzedIds();
                    } else {
                        console.error(`[SESSION] ❌ Failed to analyze session ${sessionId}:`, result.error);
                    }
                } catch (error) {
                    console.error(`[SESSION] Error analyzing session ${sessionId}:`, error);
                }
            }
            
            if (analyzedCount > 0) {
                console.log(`[SESSION] Analyzed ${analyzedCount} new sessions`);
            } else {
                console.log('[SESSION] No new sessions to analyze');
            }
            
        } catch (error) {
            console.error('[SESSION] Error in checkAndAnalyzeClosedSessions:', error);
        }
    }
    
    /**
     * Save analyzed session IDs to storage
     * @returns {Promise<void>}
     */
    async saveAnalyzedIds() {
        try {
            // Limit to 200 most recent
            if (this.analyzedSessionIds.size > 200) {
                const arr = [...this.analyzedSessionIds];
                this.analyzedSessionIds = new Set(arr.slice(-200));
            }
            
            await chrome.storage.local.set({ 
                analyzedSessionIds: [...this.analyzedSessionIds] 
            });
        } catch (error) {
            console.error('[SESSION] Error saving analyzed IDs:', error);
        }
    }
    
    /**
     * Get current session (for compatibility)
     * @returns {Object|null} Current session or null
     */
    getCurrentSession() {
        // Derive from cache if available
        if (this.currentSessionCache) {
            return this.currentSessionCache;
        }
        return null;
    }
}
