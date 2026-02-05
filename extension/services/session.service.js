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
                console.log('[SESSION] Current session is too old, closing it...');
                await this.closeCurrentSession('too_old');
            }
            
            // Generate sessionId for currentSession if it doesn't have one (legacy fix for old sessions)
            // New sessions will have sessionId generated immediately in startNewSession()
            if (this.currentSession && !this.currentSession.sessionId) {
                console.log('Generating sessionId for current session (legacy fix)...');
                this.currentSession.sessionId = generateSessionId(
                    this.currentSession.startTime,
                    this.currentSession.endTime,
                    this.currentSession.items
                );
                // Save updated session to storage
                await this.saveCurrentSession();
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
            const itemTimeStr = new Date(itemTime).toISOString();
            
            console.log(`[SESSION] Item arrived: ${item.url || 'unknown'} at ${itemTimeStr}`);
            
            if (!this.currentSession) {
                console.log(`[SESSION] No current session, starting new session`);
                this.startNewSession(item);
                await this.saveCurrentSession();
                return;
            }
            
            // Log current session state
            const sessionStartStr = new Date(this.currentSession.startTime).toISOString();
            const sessionEndStr = new Date(this.currentSession.endTime).toISOString();
            console.log(`[SESSION] Current session: ${this.currentSession.sessionId}`);
            console.log(`[SESSION]   Start: ${sessionStartStr}, End: ${sessionEndStr}, Items: ${this.currentSession.items.length}`);
            
            // Check if we need to close current session (duration max)
            if (this.shouldCloseSessionByDuration(itemTime)) {
                const duration = itemTime - this.currentSession.startTime;
                const durationMinutes = Math.round(duration / (60 * 1000));
                console.log(`[SESSION] ⚠️ CLOSING SESSION: Duration max reached (${durationMinutes} min >= ${this.MAX_SESSION_DURATION_MS / (60 * 1000)} min)`);
                await this.closeCurrentSession('duration_max');
                this.startNewSession(item);
            }
            // Check if we need to create new session (gap detected)
            else if (this.shouldStartNewSession(itemTime)) {
                const gap = itemTime - this.currentSession.endTime;
                const gapMinutes = Math.round(gap / (60 * 1000));
                console.log(`[SESSION] ⚠️ CLOSING SESSION: Gap detected (${gapMinutes} min > ${this.SESSION_GAP_MS / (60 * 1000)} min)`);
                await this.closeCurrentSession('gap_detected');
                this.startNewSession(item);
            } else {
                // Add to current session
                const gap = itemTime - this.currentSession.endTime;
                const gapMinutes = Math.round(gap / (60 * 1000));
                console.log(`[SESSION] ✓ Adding to current session (gap: ${gapMinutes} min, OK)`);
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
        const durationMinutes = Math.round(sessionDuration / (60 * 1000));
        const maxMinutes = Math.round(this.MAX_SESSION_DURATION_MS / (60 * 1000));
        const shouldClose = sessionDuration >= this.MAX_SESSION_DURATION_MS;
        
        if (shouldClose) {
            console.log(`[SESSION] Duration check: ${durationMinutes} min >= ${maxMinutes} min → CLOSE`);
        } else {
            console.log(`[SESSION] Duration check: ${durationMinutes} min < ${maxMinutes} min → CONTINUE`);
        }
        
        return shouldClose;
    }
    
    /**
     * Check if we should start a new session (gap detected)
     * @param {number} itemTime - Item timestamp
     * @returns {boolean}
     */
    shouldStartNewSession(itemTime) {
        if (!this.currentSession) {
            console.log(`[SESSION] Gap check: No current session → START NEW`);
            return true;
        }
        const gap = itemTime - this.currentSession.endTime;
        const gapMinutes = Math.round(gap / (60 * 1000));
        const gapThresholdMinutes = Math.round(this.SESSION_GAP_MS / (60 * 1000));
        const shouldStart = gap > this.SESSION_GAP_MS;
        
        const itemTimeStr = new Date(itemTime).toISOString();
        const endTimeStr = new Date(this.currentSession.endTime).toISOString();
        
        if (shouldStart) {
            console.log(`[SESSION] Gap check: ${gapMinutes} min > ${gapThresholdMinutes} min → START NEW`);
            console.log(`[SESSION]   Item time: ${itemTimeStr}, Session end: ${endTimeStr}`);
        } else {
            console.log(`[SESSION] Gap check: ${gapMinutes} min <= ${gapThresholdMinutes} min → CONTINUE`);
        }
        
        return shouldStart;
    }
    
    /**
     * Start a new session
     * @param {Object} firstItem - First item in the session
     */
    startNewSession(firstItem) {
        const itemTime = firstItem.lastVisitTime || firstItem.visitTime || Date.now();
        
        // Generate sessionId immediately (uses startTime + firstUrl, which are available now)
        // This ensures currentSession always has a sessionId, avoiding issues in getAllSessions()
        const sessionId = generateSessionId(
            itemTime,  // startTime
            itemTime,  // endTime (will be updated, but not used in hash)
            [firstItem] // items (only firstUrl is used)
        );
        
        this.currentSession = {
            sessionId: sessionId, // Generated immediately
            startTime: itemTime,
            endTime: itemTime,
            items: [firstItem]
        };
        
        this.resetGapTimer();
        const startTimeStr = new Date(itemTime).toISOString();
        console.log(`[SESSION] ✓ Started new session: ${sessionId} at ${startTimeStr}`);
    }
    
    /**
     * Reset gap timer
     * Cancels existing timer and schedules session closure
     */
    resetGapTimer() {
        if (this.gapTimer) {
            clearTimeout(this.gapTimer);
            console.log(`[SESSION] Timer: Cleared existing gap timer`);
        }
        
        if (!this.currentSession) return;
        
        // Schedule closure after SESSION_GAP_MS
        const gapMinutes = Math.round(this.SESSION_GAP_MS / (60 * 1000));
        const closureTime = Date.now() + this.SESSION_GAP_MS;
        const closureTimeStr = new Date(closureTime).toISOString();
        
        console.log(`[SESSION] Timer: Scheduling closure in ${gapMinutes} min (at ${closureTimeStr})`);
        
        this.gapTimer = setTimeout(() => {
            this.closeCurrentSessionByGap();
        }, this.SESSION_GAP_MS);
    }
    
    /**
     * Close current session by gap (called by timer)
     * @returns {Promise<void>}
     */
    async closeCurrentSessionByGap() {
        if (!this.currentSession) {
            console.log(`[SESSION] Timer triggered but no current session`);
            return;
        }
        
        const now = Date.now();
        const lastActivity = this.currentSession.endTime;
        const timeSinceLastActivity = now - lastActivity;
        const minutesSinceLastActivity = Math.round(timeSinceLastActivity / (60 * 1000));
        
        console.log(`[SESSION] ⚠️ TIMER TRIGGERED: Closing session due to inactivity`);
        console.log(`[SESSION]   Last activity: ${new Date(lastActivity).toISOString()}`);
        console.log(`[SESSION]   Time since last activity: ${minutesSinceLastActivity} min`);
        
        await this.closeCurrentSession('timer_gap');
    }
    
    /**
     * Close current session and add to completedSessions
     * Sends to backend for analysis (async, non-blocking)
     * @param {string} reason - Reason for closure ('duration_max', 'gap_detected', 'timer_gap', 'empty', 'format_failed', 'duplicate')
     * @returns {Promise<void>}
     */
    async closeCurrentSession(reason = 'unknown') {
        if (!this.currentSession || this.currentSession.items.length === 0) {
            console.log(`[SESSION] ⚠️ CLOSING SESSION: Empty session (reason: ${reason})`);
            this.currentSession = null;
            if (this.gapTimer) {
                clearTimeout(this.gapTimer);
                this.gapTimer = null;
            }
            // Save updated state (remove currentSession from storage)
            await this.saveCurrentSession();
            return;
        }
        
        // Log session details before closing
        const sessionDuration = this.currentSession.endTime - this.currentSession.startTime;
        const durationMinutes = Math.round(sessionDuration / (60 * 1000));
        const startTimeStr = new Date(this.currentSession.startTime).toISOString();
        const endTimeStr = new Date(this.currentSession.endTime).toISOString();
        
        console.log(`[SESSION] ⚠️ CLOSING SESSION: ${this.currentSession.sessionId} (reason: ${reason})`);
        console.log(`[SESSION]   Start: ${startTimeStr}`);
        console.log(`[SESSION]   End: ${endTimeStr}`);
        console.log(`[SESSION]   Duration: ${durationMinutes} min`);
        console.log(`[SESSION]   Items: ${this.currentSession.items.length}`);
        
        try {
            // Format for API
            const formattedSession = formatSessionForApi(this.currentSession);
            if (!formattedSession) {
                console.error('[SESSION] Failed to format session for API');
                this.currentSession = null;
                // Save updated state (remove currentSession from storage)
                await this.saveCurrentSession();
                return;
            }
            
            // Check for duplicates before adding
            const existingIds = new Set(this.completedSessions.map(s => s.session_identifier));
            if (existingIds.has(formattedSession.session_identifier)) {
                console.log(`[SESSION] Session ${formattedSession.session_identifier} already exists, skipping duplicate`);
                this.currentSession = null;
                if (this.gapTimer) {
                    clearTimeout(this.gapTimer);
                    this.gapTimer = null;
                }
                // Save updated state (remove currentSession from storage)
                await this.saveCurrentSession();
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
            
            console.log(`[SESSION] ✓ Session closed successfully: ${formattedSession.session_identifier}`);
            console.log(`[SESSION]   Added to completedSessions (total: ${this.completedSessions.length})`);
            
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
            
            // Save updated state (remove currentSession from storage)
            await this.saveCurrentSession();
            
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
