// ExtensionBridge - Service layer to connect React with Chrome Extension services
// This provides a clean interface for React to use existing extension functionality

/// <reference types="chrome"/>

declare global {
  interface Window {
    SessionManager: any;
    ApiClient: any;
    ExtensionConstants: any;
    ExtensionConfig: any;
  }
}

class ExtensionBridge {
  /**
   * Get preprocessed history items from Chrome storage
   * Uses the data already processed by background.js
   */
  async getProcessedHistory(): Promise<any[]> {
    return new Promise((resolve, reject) => {
      if (!chrome?.storage?.local) {
        reject(new Error('Chrome storage not available'));
        return;
      }

      chrome.storage.local.get({ historyItems: [] }, (data: any) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          console.log(`Retrieved ${data.historyItems.length} preprocessed items from storage`);
          resolve(data.historyItems);
        }
      });
    });
  }

  /**
   * Process history items into sessions using extension's SessionManager
   * This uses the existing session_management.js logic
   */
  async processHistoryIntoSessions(historyItems: any[]): Promise<any[]> {
    if (!window.SessionManager) {
      throw new Error('SessionManager not available. Extension services not loaded.');
    }

    try {
      const sessions = window.SessionManager.processHistory(historyItems);
      console.log(`Processed ${historyItems.length} items into ${sessions.length} sessions`);
      return sessions;
    } catch (error) {
      console.error('Error processing history into sessions:', error);
      throw error;
    }
  }

  /**
   * Send single session to backend for clustering using extension's ApiClient
   * This uses the existing api_client.js logic
   */
  async clusterSession(session: any): Promise<any> {
    if (!window.ApiClient) {
      throw new Error('ApiClient not available. Extension services not loaded.');
    }

    try {
      const result = await window.ApiClient.clusterSession(session);
      console.log('Single session clustering result:', result);
      return result;
    } catch (error) {
      console.error('Error clustering single session:', error);
      throw error;
    }
  }

  /**
   * Check API health using extension's ApiClient
   */
  async checkApiHealth(): Promise<any> {
    if (!window.ApiClient) {
      throw new Error('ApiClient not available. Extension services not loaded.');
    }

    try {
      const result = await window.ApiClient.checkHealth();
      console.log('API health check:', result);
      return result;
    } catch (error) {
      console.error('Error checking API health:', error);
      throw error;
    }
  }

  /**
   * Get extension configuration
   */
  getConfig() {
    if (!window.ExtensionConfig) {
      console.warn('ExtensionConfig not available, using defaults');
      return {
        currentEnvironment: 'development',
        getApiBaseUrl: () => 'http://localhost:8000'
      };
    }
    return window.ExtensionConfig;
  }

  /**
   * Get extension constants
   */
  getConstants() {
    if (!window.ExtensionConstants) {
      console.warn('ExtensionConstants not available, using defaults');
      return {
        SESSION_GAP_MINUTES: 120,
        HISTORY_DAYS_BACK: 7,
        DAY_MS: 24 * 60 * 60 * 1000,
        MAX_CLUSTER_ITEMS_DISPLAY: 5,
        STATUS_CHECKING_API: 'Checking API connection...',
        STATUS_FETCHING_HISTORY: 'Fetching history...',
        STATUS_PROCESSING_SESSIONS: 'Processing sessions...',
        STATUS_ANALYZING_PATTERNS: 'Analyzing patterns...',
        STATUS_ANALYSIS_COMPLETE: 'Analysis complete',
        STATUS_ANALYSIS_FAILED: 'Analysis failed',
        ERROR_NO_HISTORY: 'No history found',
        ERROR_NO_SESSIONS: 'No sessions could be created',
        ERROR_CLUSTERING_FAILED: 'Clustering failed'
      };
    }
    return window.ExtensionConstants;
  }

  /**
   * Check if all extension services are loaded and ready
   */
  areExtensionServicesReady(): boolean {
    return !!(
      window.SessionManager && 
      window.ApiClient && 
      window.ExtensionConstants && 
      window.ExtensionConfig &&
      chrome?.storage?.local
    );
  }

  /**
   * Wait for extension services to be ready
   */
  async waitForExtensionServices(timeoutMs: number = 5000): Promise<void> {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      
      const checkServices = () => {
        if (this.areExtensionServicesReady()) {
          resolve();
          return;
        }
        
        if (Date.now() - startTime > timeoutMs) {
          reject(new Error('Timeout waiting for extension services to load'));
          return;
        }
        
        setTimeout(checkServices, 100);
      };
      
      checkServices();
    });
  }
}

// Create and export singleton instance
export const extensionBridge = new ExtensionBridge();

// For debugging
if (typeof window !== 'undefined') {
  (window as any).extensionBridge = extensionBridge;
}
