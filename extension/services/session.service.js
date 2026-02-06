class SessionService {
    constructor(historyService, apiService) {
        this.historyService = historyService;
        this.apiService = apiService;
        
        this.completedSessionsCache = null;
        this.currentSessionCache = null;
        this.lastProcessedItemCount = 0;
        this.analyzedSessionIds = new Set();
        this.CHECK_ALARM_NAME = 'checkClosedSessions';
        
        const constants = (typeof self !== 'undefined' ? self.ExtensionConstants : 
                          typeof window !== 'undefined' ? window.ExtensionConstants : {});
        this.SESSION_GAP_MS = (constants.SESSION_GAP_MINUTES || 30) * 60 * 1000;
        this.MAX_SESSION_DURATION_MS = (constants.MAX_SESSION_DURATION_MINUTES || 90) * 60 * 1000;
        this.MIN_SESSION_ITEMS = constants.MIN_SESSION_ITEMS || 2;
    }
    
    async initialize() {
        try {
            console.log('[SESSION] Initializing session service...');
            
            const stored = await chrome.storage.local.get(['analyzedSessionIds']);
            this.analyzedSessionIds = new Set(stored.analyzedSessionIds || []);
            
            if (this.analyzedSessionIds.size > 200) {
                const arr = [...this.analyzedSessionIds];
                this.analyzedSessionIds = new Set(arr.slice(-200));
                await this.saveAnalyzedIds();
            }
            
            console.log(`[SESSION] Loaded ${this.analyzedSessionIds.size} analyzed session IDs`);
            
            chrome.alarms.onAlarm.addListener((alarm) => {
                if (alarm.name === this.CHECK_ALARM_NAME) {
                    console.log('[SESSION] Alarm triggered: checking closed sessions');
                    this.checkAndAnalyzeClosedSessions();
                }
            });
            
            console.log('[SESSION] Session service initialized');
            
            setTimeout(() => {
                console.log('[SESSION] Running deferred check for closed sessions...');
                this.checkAndAnalyzeClosedSessions();
            }, 2000);
            
        } catch (error) {
            console.error('[SESSION] Error initializing session service:', error);
        }
    }
    
    async onNewItem() {
        try {
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
    
    deriveAllSessions(items) {
        if (!items || items.length === 0) {
            return { completed: [], current: null };
        }
        
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
                session = {
                    startTime: itemTime,
                    endTime: itemTime,
                    items: [item]
                };
            } else {
                const gap = itemTime - session.endTime;
                const duration = itemTime - session.startTime;
                
                if (gap > this.SESSION_GAP_MS || duration > this.MAX_SESSION_DURATION_MS) {
                    session.sessionId = generateSessionId(
                        session.startTime,
                        session.endTime,
                        session.items
                    );
                    sessions.push(session);
                    
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
        
        if (session) {
            const now = Date.now();
            const timeSinceLastActivity = now - session.endTime;
            
            if (timeSinceLastActivity > this.SESSION_GAP_MS) {
                session.sessionId = generateSessionId(
                    session.startTime,
                    session.endTime,
                    session.items
                );
                sessions.push(session);
                return { completed: sessions, current: null };
            } else {
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
    
    deriveSessionsIncremental(newItems, existingCurrent) {
        const newCompleted = [];
        let session = existingCurrent;
        
        for (const item of newItems) {
            const itemTime = item.visitTime || item.lastVisitTime;
            
            if (!session) {
                session = {
                    startTime: itemTime,
                    endTime: itemTime,
                    items: [item]
                };
            } else {
                const gap = itemTime - session.endTime;
                const duration = itemTime - session.startTime;
                
                if (gap > this.SESSION_GAP_MS || duration > this.MAX_SESSION_DURATION_MS) {
                    session.sessionId = generateSessionId(
                        session.startTime,
                        session.endTime,
                        session.items
                    );
                    newCompleted.push(session);
                    
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
    
    async getAllSessions() {
        try {
            const items = await this.historyService.getAllItems();
            
            // Case 1: No items
            if (items.length === 0) {
                console.log('[SESSION] No items, returning empty sessions');
                return [];
            }
            
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
    
    getCurrentSession() {
        if (this.currentSessionCache) {
            return this.currentSessionCache;
        }
        return null;
    }
}
