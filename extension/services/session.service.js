// Session Service - Manage browsing sessions
// Handles session construction, tracking, and closure

class SessionService {
    constructor(historyService, apiService) {
        this.historyService = historyService;
        this.apiService = apiService;
        this.currentSession = null;
        this.completedSessions = [];
        this.gapTimer = null;
        
        // Get constants
        const constants = (typeof self !== 'undefined' ? self.ExtensionConstants : 
                          typeof window !== 'undefined' ? window.ExtensionConstants : {});
        this.SESSION_GAP_MS = (constants.SESSION_GAP_MINUTES || 60) * 60 * 1000;
        this.MAX_SESSION_DURATION_MS = (constants.MAX_SESSION_DURATION_MINUTES || 90) * 60 * 1000;
        this.MIN_SESSION_ITEMS = constants.MIN_SESSION_ITEMS || 2;
    }
    
    /**
     * Initialize session service
     * Loads completedSessions and currentSession from storage
     * If completedSessions is empty, builds it from historyItems
     * @returns {Promise<void>}
     */
    async initialize() {
        try {
            console.log('Initializing session service...');
            
            // Load from storage
            const stored = await chrome.storage.local.get(['completedSessions', 'currentSession']);
            this.completedSessions = stored.completedSessions || [];
            this.currentSession = stored.currentSession || null;
            
            // If no completed sessions, build them from history
            if (this.completedSessions.length === 0) {
                console.log('No completed sessions found, building from history...');
                await this.buildSessionsFromHistory();
            } else {
                console.log(`Found ${this.completedSessions.length} completed sessions in storage`);
            }
            
            // Check if currentSession is still valid (not too old)
            if (this.currentSession && !this.isSessionStillValid(this.currentSession)) {
                console.log('Current session is too old, closing it...');
                await this.closeCurrentSession();
            }
            
            console.log('Session service initialized');
            
        } catch (error) {
            console.error('Error initializing session service:', error);
        }
    }
    
    /**
     * Build all sessions from history items
     * @returns {Promise<void>}
     */
    async buildSessionsFromHistory() {
        try {
            const items = await this.historyService.getAllItems();
            if (items.length === 0) {
                console.log('No history items to build sessions from');
                return;
            }
            
            // Group items into sessions
            const constants = (typeof self !== 'undefined' ? self.ExtensionConstants : 
                              typeof window !== 'undefined' ? window.ExtensionConstants : {});
            const gapMinutes = constants.SESSION_GAP_MINUTES || 60;
            const minItems = constants.MIN_SESSION_ITEMS || 2;
            
            const sessions = groupItemsIntoSessions(items, gapMinutes, minItems);
            
            // Format sessions for API and store
            this.completedSessions = sessions.map(session => formatSessionForApi(session)).filter(Boolean);
            
            // Limit to 100 most recent
            if (this.completedSessions.length > 100) {
                this.completedSessions = this.completedSessions.slice(-100);
            }
            
            // Save to storage
            await chrome.storage.local.set({ completedSessions: this.completedSessions });
            
            console.log(`Built ${this.completedSessions.length} sessions from history`);
            
        } catch (error) {
            console.error('Error building sessions from history:', error);
        }
    }
    
    /**
     * Check if a session is still valid (not too old)
     * @param {Object} session - Session object
     * @returns {boolean}
     */
    isSessionStillValid(session) {
        if (!session || !session.endTime) return false;
        const now = Date.now();
        const sessionEnd = typeof session.endTime === 'number' ? session.endTime : new Date(session.endTime).getTime();
        return (now - sessionEnd) < this.SESSION_GAP_MS;
    }
    
    /**
     * Start tracking (called after initialization)
     * Sets up gap timer if currentSession exists
     */
    startTracking() {
        if (this.currentSession) {
            this.resetGapTimer();
        }
    }
    
    /**
     * Add item to current session or create new session
     * @param {Object} item - Preprocessed history item
     * @returns {Promise<void>}
     */
    async addItem(item) {
        try {
            const itemTime = item.lastVisitTime || item.visitTime || Date.now();
            
            // Check if we need to close current session (duration max)
            if (this.currentSession && this.shouldCloseSessionByDuration(itemTime)) {
                await this.closeCurrentSession();
                this.startNewSession(item);
            }
            // Check if we need to create new session (gap detected)
            else if (!this.currentSession || this.shouldStartNewSession(itemTime)) {
                if (this.currentSession) {
                    await this.closeCurrentSession();
                }
                this.startNewSession(item);
            } else {
                // Add to current session
                this.currentSession.items.push(item);
                this.currentSession.endTime = itemTime;
                this.resetGapTimer();
            }
            
            // Save current session
            await this.saveCurrentSession();
            
        } catch (error) {
            console.error('Error adding item to session:', error);
        }
    }
    
    /**
     * Check if session should be closed by duration
     * @param {number} currentTime - Current timestamp
     * @returns {boolean}
     */
    shouldCloseSessionByDuration(currentTime) {
        if (!this.currentSession) return false;
        const sessionDuration = currentTime - this.currentSession.startTime;
        return sessionDuration >= this.MAX_SESSION_DURATION_MS;
    }
    
    /**
     * Check if we should start a new session (gap detected)
     * @param {number} itemTime - Item timestamp
     * @returns {boolean}
     */
    shouldStartNewSession(itemTime) {
        if (!this.currentSession) return true;
        const gap = itemTime - this.currentSession.endTime;
        return gap > this.SESSION_GAP_MS;
    }
    
    /**
     * Start a new session
     * @param {Object} firstItem - First item in the session
     */
    startNewSession(firstItem) {
        const itemTime = firstItem.lastVisitTime || firstItem.visitTime || Date.now();
        
        this.currentSession = {
            sessionId: null, // Will be generated on close
            startTime: itemTime,
            endTime: itemTime,
            items: [firstItem]
        };
        
        this.resetGapTimer();
        console.log('Started new session');
    }
    
    /**
     * Reset gap timer
     * Cancels existing timer and schedules session closure
     */
    resetGapTimer() {
        if (this.gapTimer) {
            clearTimeout(this.gapTimer);
        }
        
        if (!this.currentSession) return;
        
        // Schedule closure after SESSION_GAP_MS
        this.gapTimer = setTimeout(() => {
            this.closeCurrentSessionByGap();
        }, this.SESSION_GAP_MS);
    }
    
    /**
     * Close current session by gap (called by timer)
     * @returns {Promise<void>}
     */
    async closeCurrentSessionByGap() {
        if (!this.currentSession) return;
        await this.closeCurrentSession();
    }
    
    /**
     * Close current session and add to completedSessions
     * Sends to backend for analysis (async, non-blocking)
     * @returns {Promise<void>}
     */
    async closeCurrentSession() {
        if (!this.currentSession || this.currentSession.items.length === 0) {
            this.currentSession = null;
            if (this.gapTimer) {
                clearTimeout(this.gapTimer);
                this.gapTimer = null;
            }
            return;
        }
        
        try {
            // Generate session ID
            this.currentSession.sessionId = generateSessionId(
                this.currentSession.startTime,
                this.currentSession.endTime,
                this.currentSession.items
            );
            
            // Format for API
            const formattedSession = formatSessionForApi(this.currentSession);
            if (!formattedSession) {
                console.error('Failed to format session for API');
                this.currentSession = null;
                return;
            }
            
            // Check for duplicates before adding
            const existingIds = new Set(this.completedSessions.map(s => s.session_identifier));
            if (existingIds.has(formattedSession.session_identifier)) {
                console.log(`Session ${formattedSession.session_identifier} already exists, skipping`);
                this.currentSession = null;
                if (this.gapTimer) {
                    clearTimeout(this.gapTimer);
                    this.gapTimer = null;
                }
                return;
            }
            
            // Add to completed sessions
            this.completedSessions.push(formattedSession);
            
            // Limit to 100 most recent
            if (this.completedSessions.length > 100) {
                this.completedSessions = this.completedSessions.slice(-100);
            }
            
            // Save to storage
            await chrome.storage.local.set({ completedSessions: this.completedSessions });
            
            console.log(`Session closed: ${formattedSession.session_identifier} with ${formattedSession.items.length} items`);
            
            // Send to backend for analysis (async, non-blocking)
            this.apiService.analyzeSession(formattedSession, { force: false })
                .then(result => {
                    if (result.success) {
                        console.log(`✅ Session ${formattedSession.session_identifier} analyzed successfully`);
                    } else {
                        console.error(`❌ Failed to analyze session ${formattedSession.session_identifier}:`, result.error);
                    }
                })
                .catch(error => {
                    console.error(`Error analyzing session ${formattedSession.session_identifier}:`, error);
                });
            
            // Reset current session
            this.currentSession = null;
            if (this.gapTimer) {
                clearTimeout(this.gapTimer);
                this.gapTimer = null;
            }
            
        } catch (error) {
            console.error('Error closing session:', error);
        }
    }
    
    /**
     * Save current session to storage
     * @returns {Promise<void>}
     */
    async saveCurrentSession() {
        if (this.currentSession) {
            await chrome.storage.local.set({ currentSession: this.currentSession });
        } else {
            await chrome.storage.local.remove(['currentSession']);
        }
    }
    
    /**
     * Get all sessions (completed + current)
     * @returns {Promise<Array>} Array of formatted sessions
     */
    async getAllSessions() {
        const allSessions = [...this.completedSessions];
        
        // Add current session if exists
        if (this.currentSession) {
            const formatted = formatSessionForApi(this.currentSession);
            if (formatted) {
                allSessions.push(formatted);
            }
        }
        
        return allSessions;
    }
    
    /**
     * Get current session
     * @returns {Object|null} Current session or null
     */
    getCurrentSession() {
        return this.currentSession;
    }
}
