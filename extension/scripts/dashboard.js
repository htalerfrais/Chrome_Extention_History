// Dashboard JavaScript for Chrome Extension History
// Handles the dashboard UI and API communication

class Dashboard {
    constructor() {
        this.apiClient = window.ApiClient;
        this.config = window.ExtensionConfig;
        this.constants = window.ExtensionConstants || {};
        this.sessionManager = window.SessionManager;
        this.currentClusters = [];
        this.currentPreview = null;
        
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
        
        // Summary elements
        this.totalSessions = document.getElementById('total-sessions');
        this.totalItems = document.getElementById('total-items');
        this.totalClusters = document.getElementById('total-clusters');
        this.dateRange = document.getElementById('date-range');
        
        // Content containers
        this.clustersContainer = document.getElementById('clusters-container');
        this.domainsContainer = document.getElementById('domains-container');
        
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
            const [clusterResult, previewResult] = await Promise.all([
                this.apiClient.clusterSessions(sessions),
                this.apiClient.previewSessions(sessions)
            ]);
            
            if (!clusterResult.success) {
                throw new Error(`${this.constants.ERROR_CLUSTERING_FAILED}: ${clusterResult.error}`);
            }
            
            if (!previewResult.success) {
                throw new Error(`${this.constants.ERROR_PREVIEW_FAILED}: ${previewResult.error}`);
            }
            
            // Store results
            this.currentClusters = clusterResult.data;
            this.currentPreview = previewResult.data;
            
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
        this.populateSummary();
        this.populateClusters();
        this.populateDomains();
    }
    
    populateSummary() {
        if (!this.currentPreview) return;
        
        this.totalSessions.textContent = this.currentPreview.total_sessions;
        this.totalItems.textContent = this.currentPreview.total_items;
        this.totalClusters.textContent = this.currentClusters.length;
        
        if (this.currentPreview.date_range.start && this.currentPreview.date_range.end) {
            const startDate = new Date(this.currentPreview.date_range.start).toLocaleDateString();
            const endDate = new Date(this.currentPreview.date_range.end).toLocaleDateString();
            this.dateRange.textContent = `${startDate} - ${endDate}`;
        }
    }
    
    populateClusters() {
        this.clustersContainer.innerHTML = '';
        
        if (!this.currentClusters || this.currentClusters.length === 0) {
            this.clustersContainer.innerHTML = '<p>No clusters found in your browsing history.</p>';
            return;
        }
        
        this.currentClusters.forEach(cluster => {
            const clusterCard = this.createClusterCard(cluster);
            this.clustersContainer.appendChild(clusterCard);
        });
    }
    
    createClusterCard(cluster) {
        const card = document.createElement('div');
        card.className = 'cluster-card';
        
        const confidence = Math.round(cluster.confidence_score * 100);
        
        // Header
        const header = document.createElement('div');
        header.className = 'cluster-header';
        
        const themeDiv = document.createElement('div');
        themeDiv.className = 'cluster-theme';
        themeDiv.textContent = cluster.theme;
        
        const confidenceDiv = document.createElement('div');
        confidenceDiv.className = 'cluster-confidence';
        confidenceDiv.textContent = `${confidence}% confidence`;
        
        header.appendChild(themeDiv);
        header.appendChild(confidenceDiv);
        
        // Description
        const descriptionDiv = document.createElement('div');
        descriptionDiv.className = 'cluster-description';
        descriptionDiv.textContent = cluster.description;
        
        // Keywords
        const keywordsDiv = document.createElement('div');
        keywordsDiv.className = 'cluster-keywords';
        cluster.keywords.forEach(keyword => {
            const tag = document.createElement('span');
            tag.className = 'keyword-tag';
            tag.textContent = keyword;
            keywordsDiv.appendChild(tag);
        });
        
        // Stats
        const statsDiv = document.createElement('div');
        statsDiv.className = 'cluster-stats';
        
        const pagesSpan = document.createElement('span');
        pagesSpan.textContent = `${cluster.total_items} pages`;
        
        const sessionsSpan = document.createElement('span');
        sessionsSpan.textContent = `${cluster.session_ids.length} sessions`;
        
        statsDiv.appendChild(pagesSpan);
        statsDiv.appendChild(sessionsSpan);
        
        // Items
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
        card.appendChild(header);
        card.appendChild(descriptionDiv);
        card.appendChild(keywordsDiv);
        card.appendChild(statsDiv);
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
    
    populateDomains() {
        this.domainsContainer.innerHTML = '';
        
        if (!this.currentPreview || !this.currentPreview.top_domains) {
            return;
        }
        
        this.currentPreview.top_domains.forEach(domainData => {
            const domainCard = this.createDomainCard(domainData);
            this.domainsContainer.appendChild(domainCard);
        });
    }
    
    createDomainCard(domainData) {
        const card = document.createElement('div');
        card.className = 'domain-card';
        
        const faviconUrl = `https://www.google.com/s2/favicons?domain=${domainData.domain}`;
        
        const faviconImg = document.createElement('img');
        faviconImg.src = faviconUrl;
        faviconImg.alt = '';
        faviconImg.className = 'domain-favicon';
        faviconImg.addEventListener('error', () => faviconImg.style.display = 'none');
        
        const infoDiv = document.createElement('div');
        infoDiv.className = 'domain-info';
        
        const nameDiv = document.createElement('div');
        nameDiv.className = 'domain-name';
        nameDiv.textContent = domainData.domain;
        
        const countDiv = document.createElement('div');
        countDiv.className = 'domain-count';
        countDiv.textContent = `${domainData.count} visits`;
        
        infoDiv.appendChild(nameDiv);
        infoDiv.appendChild(countDiv);
        
        card.appendChild(faviconImg);
        card.appendChild(infoDiv);
        
        return card;
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
        
        alert(`Settings\n\nEnvironment: ${currentEnv}\nAPI URL: ${apiUrl}\n\nTo switch environments, modify extension/utils/config.js`);
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
