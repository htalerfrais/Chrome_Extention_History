// Dashboard JavaScript for Chrome Extension History
// Handles the dashboard UI and API communication

class Dashboard {
    constructor() {
        this.apiClient = window.ApiClient;
        this.config = window.ExtensionConfig;
        this.constants = window.ExtensionConstants || {};
        this.sessionManager = window.SessionManager;
        this.currentSessionResults = {};
        this.activeSessionId = null;
        
        this.initializeElements();
        this.attachEventListeners();
        this.loadDashboard();
    }
    
    initializeElements() {
        // Status elements
        this.statusText = document.getElementById('status-text');
        this.statusIndicator = document.getElementById('status-indicator');
        
        // Container elements
        this.loadingContainer = document.getElementById('loading-container');
        this.errorContainer = document.getElementById('error-container');
        this.dashboardContent = document.getElementById('dashboard-content');
        
        // Session tabs
        this.sessionsTabs = document.getElementById('sessions-tabs');
        
        // Content containers
        this.clustersContainer = document.getElementById('clusters-container');
        this.clustersTitle = document.getElementById('clusters-title');
        this.sessionInfo = document.getElementById('session-info');
        
        // Buttons
        this.refreshBtn = document.getElementById('refresh-btn');
        this.retryBtn = document.getElementById('retry-btn');
        this.settingsBtn = document.getElementById('settings-btn');
    }
    
    attachEventListeners() {
        this.refreshBtn.addEventListener('click', () => this.loadDashboard());
        this.retryBtn.addEventListener('click', () => this.loadDashboard());
        this.settingsBtn.addEventListener('click', () => this.openSettings());
    }
    
    async loadDashboard() {
        try {
            this.showLoading();
            this.updateStatus(this.constants.STATUS_CHECKING_API || 'Checking API connection...', 'loading');
            
            // Check API health
            const healthCheck = await this.apiClient.checkHealth();
            if (!healthCheck.success) {
                throw new Error(`API not available: ${healthCheck.error}`);
            }
            
            this.updateStatus(this.constants.STATUS_FETCHING_HISTORY, 'loading');
            
            // Get Chrome history
            const history = await this.getChromeHistory();
            if (!history || history.length === 0) {
                throw new Error(this.constants.ERROR_NO_HISTORY);
            }
            
            this.updateStatus(this.constants.STATUS_PROCESSING_SESSIONS, 'loading');
            
            // Preprocess history using SessionManager
            const sessions = this.sessionManager.processHistory(history);
            if (sessions.length === 0) {
                throw new Error(this.constants.ERROR_NO_SESSIONS);
            }
            
            this.updateStatus(this.constants.STATUS_ANALYZING_PATTERNS, 'loading');
            
            // Get clustering results
            const clusterResult = await this.apiClient.clusterSessions(sessions);
            
            if (!clusterResult.success) {
                throw new Error(`${this.constants.ERROR_CLUSTERING_FAILED}: ${clusterResult.error}`);
            }
            
            // Store results
            this.currentSessionResults = clusterResult.data;
            
            // Set first session as active
            const sessionIds = Object.keys(this.currentSessionResults);
            if (sessionIds.length > 0) {
                this.activeSessionId = sessionIds[0];
            }
            
            // Update UI
            this.updateStatus(this.constants.STATUS_ANALYSIS_COMPLETE, 'success');
            this.showDashboard();
            this.populateDashboard();
            
        } catch (error) {
            console.error('Dashboard loading failed:', error);
            this.showError(error.message);
            this.updateStatus(this.constants.STATUS_ANALYSIS_FAILED, 'error');
        }
    }
    
    async getChromeHistory() {
        return new Promise((resolve, reject) => {
            // Utilise les données déjà préprocessées par background.js
            chrome.storage.local.get({ historyItems: [] }, (data) => {
                if (chrome.runtime.lastError) {
                    reject(new Error(chrome.runtime.lastError.message));
                } else {
                    console.log(`Récupération de ${data.historyItems.length} items préprocessés depuis le storage`);
                    
                    // Filtrer par date si nécessaire (les données du storage peuvent être plus anciennes)
                    const oneWeekAgo = Date.now() - (this.constants.HISTORY_DAYS_BACK * this.constants.DAY_MS);
                    const recentItems = data.historyItems.filter(item => {
                        const itemTime = item.lastVisitTime || item.visitTime || 0;
                        return itemTime >= oneWeekAgo;
                    });
                    
                    console.log(`${recentItems.length} items dans la période des ${this.constants.HISTORY_DAYS_BACK} derniers jours`);
                    resolve(recentItems);
                }
            });
        });
    }
    
    populateDashboard() {
        this.populateSessionTabs();
        this.populateSessionClusters();
    }
    
    populateSessionTabs() {
        this.sessionsTabs.innerHTML = '';
        
        const sessionIds = Object.keys(this.currentSessionResults);
        if (sessionIds.length === 0) {
            return;
        }
        
        sessionIds.forEach(sessionId => {
            const sessionData = this.currentSessionResults[sessionId];
            const tab = this.createSessionTab(sessionId, sessionData);
            this.sessionsTabs.appendChild(tab);
        });
    }
    
    createSessionTab(sessionId, sessionData) {
        const tab = document.createElement('button');
        tab.className = `session-tab ${sessionId === this.activeSessionId ? 'active' : ''}`;
        tab.dataset.sessionId = sessionId;
        
        const startTime = new Date(sessionData.session_start_time);
        const endTime = new Date(sessionData.session_end_time);
        const duration = Math.round((endTime - startTime) / (1000 * 60)); // minutes
        
        tab.innerHTML = `
            <div class="session-tab-content">
                <div class="session-tab-title">Session ${sessionId.split('_').pop()}</div>
                <div class="session-tab-meta">
                    ${startTime.toLocaleDateString()} • ${duration}min • ${sessionData.clusters.length} topics
                </div>
            </div>
        `;
        
        tab.addEventListener('click', () => this.switchToSession(sessionId));
        
        return tab;
    }
    
    switchToSession(sessionId) {
        // Update active tab
        document.querySelectorAll('.session-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-session-id="${sessionId}"]`).classList.add('active');
        
        // Update active session
        this.activeSessionId = sessionId;
        
        // Update clusters display
        this.populateSessionClusters();
    }
    
    populateSessionClusters() {
        this.clustersContainer.innerHTML = '';
        
        if (!this.activeSessionId || !this.currentSessionResults[this.activeSessionId]) {
            this.clustersContainer.innerHTML = '<p>No session selected.</p>';
            return;
        }
        
        const sessionData = this.currentSessionResults[this.activeSessionId];
        const clusters = sessionData.clusters;
        
        if (!clusters || clusters.length === 0) {
            this.clustersContainer.innerHTML = '<p>No clusters found in this session.</p>';
            return;
        }
        
        // Update session info
        this.updateSessionInfo(sessionData);
        
        // Populate clusters
        clusters.forEach(cluster => {
            const clusterCard = this.createClusterCard(cluster);
            this.clustersContainer.appendChild(clusterCard);
        });
    }
    
    updateSessionInfo(sessionData) {
        const startTime = new Date(sessionData.session_start_time);
        const endTime = new Date(sessionData.session_end_time);
        const duration = Math.round((endTime - startTime) / (1000 * 60)); // minutes
        
        this.sessionInfo.innerHTML = `
            <div class="session-info-item">
                <strong>Duration:</strong> ${duration} minutes
            </div>
            <div class="session-info-item">
                <strong>Time:</strong> ${startTime.toLocaleString()} - ${endTime.toLocaleString()}
            </div>
            <div class="session-info-item">
                <strong>Topics:</strong> ${sessionData.clusters.length}
            </div>
        `;
    }
    
    createClusterCard(cluster) {
        const card = document.createElement('div');
        card.className = 'cluster-card';
        
        // Theme header
        const themeDiv = document.createElement('div');
        themeDiv.className = 'cluster-theme';
        themeDiv.textContent = cluster.theme;
        
        // Items list
        const itemsDiv = document.createElement('div');
        itemsDiv.className = 'cluster-items';
        
        cluster.items.slice(0, this.constants.MAX_CLUSTER_ITEMS_DISPLAY).forEach(item => {
            itemsDiv.appendChild(this.createClusterItem(item));
        });
        
        if (cluster.items.length > this.constants.MAX_CLUSTER_ITEMS_DISPLAY) {
            const moreDiv = document.createElement('div');
            moreDiv.className = 'item-more';
            moreDiv.textContent = `+${cluster.items.length - this.constants.MAX_CLUSTER_ITEMS_DISPLAY} more items`;
            itemsDiv.appendChild(moreDiv);
        }
        
        // Assemble card
        card.appendChild(themeDiv);
        card.appendChild(itemsDiv);
        
        return card;
    }
    
    createClusterItem(item) {
        const domain = new URL(item.url).hostname;
        const faviconUrl = `https://www.google.com/s2/favicons?domain=${domain}`;
        const visitTime = new Date(item.visit_time).toLocaleDateString();
        
        const itemElement = document.createElement('div');
        itemElement.className = 'cluster-item';
        
        const faviconImg = document.createElement('img');
        faviconImg.src = faviconUrl;
        faviconImg.alt = '';
        faviconImg.className = 'item-favicon';
        faviconImg.addEventListener('error', () => faviconImg.style.display = 'none');
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'item-content';
        
        const titleDiv = document.createElement('div');
        titleDiv.className = 'item-title';
        titleDiv.textContent = item.title;
        
        const urlDiv = document.createElement('div');
        urlDiv.className = 'item-url';
        urlDiv.textContent = domain;
        
        const timeDiv = document.createElement('div');
        timeDiv.className = 'item-time';
        timeDiv.textContent = visitTime;
        
        contentDiv.appendChild(titleDiv);
        contentDiv.appendChild(urlDiv);
        
        itemElement.appendChild(faviconImg);
        itemElement.appendChild(contentDiv);
        itemElement.appendChild(timeDiv);
        
        return itemElement;
    }
    
    
    showLoading() {
        this.loadingContainer.style.display = 'flex';
        this.errorContainer.style.display = 'none';
        this.dashboardContent.style.display = 'none';
    }
    
    showError(message) {
        document.getElementById('error-message').textContent = message;
        this.loadingContainer.style.display = 'none';
        this.errorContainer.style.display = 'flex';
        this.dashboardContent.style.display = 'none';
    }
    
    showDashboard() {
        this.loadingContainer.style.display = 'none';
        this.errorContainer.style.display = 'none';
        this.dashboardContent.style.display = 'block';
    }
    
    updateStatus(text, type = 'success') {
        this.statusText.textContent = text;
        this.statusIndicator.className = `status-indicator ${type}`;
    }
    
    openSettings() {
        // For now, just show environment info
        const currentEnv = this.config.currentEnvironment;
        const apiUrl = this.config.getApiBaseUrl();
        const sessionGap = this.constants.SESSION_GAP_MINUTES;
        
        alert(`Settings\n\nEnvironment: ${currentEnv}\nAPI URL: ${apiUrl}\nSession Gap: ${sessionGap} minutes\n\nTo switch environments, modify extension/utils/config.js`);
    }
    
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Wait for constants to be loaded
    if (window.ExtensionConstants) {
        new Dashboard();
    } else {
        console.error('ExtensionConstants not loaded. Check script loading order.');
        // Fallback: try again after a short delay
        setTimeout(() => {
            if (window.ExtensionConstants) {
                new Dashboard();
            } else {
                console.error('ExtensionConstants still not available');
            }
        }, 100);
    }
});
