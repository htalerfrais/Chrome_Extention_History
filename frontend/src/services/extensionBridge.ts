// ExtensionBridge - Service layer to connect React with Chrome Extension services
// Communicates directly with the background service worker via chrome.runtime.sendMessage

/// <reference types="chrome"/>

declare global {
  interface Window {
    ExtensionConstants: any;
    ExtensionConfig: any;
  }
}

class ExtensionBridge {
  private isReady: boolean = false;
  private readyPromise: Promise<void> | null = null;

  /**
   * Wait for services to be ready
   * @param timeout - Timeout in milliseconds
   */
  async waitForReady(timeout: number = 5000): Promise<void> {
    if (this.isReady) {
      return;
    }

    if (this.readyPromise) {
      return this.readyPromise;
    }

    this.readyPromise = new Promise((resolve, reject) => {
      const startTime = Date.now();

      const checkReady = () => {
        // Try to ping the service worker
        if (typeof chrome !== 'undefined' && chrome.runtime) {
          chrome.runtime.sendMessage({ action: 'ping' }, (pingResponse) => {
            if (!chrome.runtime.lastError && pingResponse?.success) {
              this.isReady = true;
              resolve();
              return;
            }
            
            // If ping failed, retry after delay
            if (Date.now() - startTime > timeout) {
              reject(new Error('Timeout waiting for extension services'));
              return;
            }
            
            setTimeout(checkReady, 100);
          });
        } else {
          // Chrome runtime not available
          if (Date.now() - startTime > timeout) {
            reject(new Error('Chrome runtime not available'));
            return;
          }
          setTimeout(checkReady, 100);
        }
      };

      checkReady();
    });

    return this.readyPromise;
  }

  /**
   * Send message to service worker and wait for response
   */
  private sendMessage<T>(message: any): Promise<T> {
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(message, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else if (response.error) {
          reject(new Error(response.error));
        } else {
          resolve(response);
        }
      });
    });
  }

  /**
   * Get all sessions (completed + current)
   * Returns completedSessions[] + currentSession (if exists)
   */
  async getAllSessions(): Promise<any[]> {
    try {
      await this.waitForReady();
      const response = await this.sendMessage<{ sessions: any[] }>({ action: 'getAllSessions' });
      console.log(`Retrieved ${response.sessions.length} sessions from service worker`);
      return response.sessions || [];
    } catch (error) {
      console.error('Error getting all sessions:', error);
      throw error;
    }
  }

  /**
   * Get preprocessed history items from Chrome storage
   * Kept for backward compatibility (fallback)
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
   * Process history items into sessions
   * Kept for backward compatibility (fallback)
   */
  async processHistoryIntoSessions(_historyItems: any[]): Promise<any[]> {
    // Fallback: use getAllSessions instead
    return await this.getAllSessions();
  }

  /**
   * Send single session to backend for clustering
   */
  async clusterSession(session: any, options?: { force?: boolean }): Promise<any> {
    try {
      await this.waitForReady();
      const result = await this.sendMessage({ 
        action: 'analyzeSession', 
        session, 
        options 
      });
      console.log('Session clustering result:', result);
      return result;
    } catch (error) {
      console.error('Error clustering session:', error);
      throw error;
    }
  }

  /**
   * Check API health
   */
  async checkApiHealth(): Promise<any> {
    try {
      await this.waitForReady();
      const result = await this.sendMessage({ action: 'checkApiHealth' });
      console.log('API health check:', result);
      return result;
    } catch (error) {
      console.error('Error checking API health:', error);
      throw error;
    }
  }

  /**
   * Send chat message
   */
  async sendChatMessage(message: string, conversationId?: string, history?: any[]): Promise<any> {
    if (!message || message.trim().length === 0) {
      throw new Error('Message cannot be empty');
    }

    try {
      await this.waitForReady();
      const result = await this.sendMessage({
        action: 'sendChatMessage',
        message,
        conversationId: conversationId || null,
        history: history || []
      });
      console.log('Chat message result:', result);
      return result;
    } catch (error) {
      console.error('Error sending chat message:', error);
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
      chrome?.runtime &&
      window.ExtensionConstants && 
      window.ExtensionConfig &&
      chrome?.storage?.local
    );
  }

  /**
   * Wait for extension services to be ready
   */
  async waitForExtensionServices(timeoutMs: number = 5000): Promise<void> {
    return this.waitForReady(timeoutMs);
  }
}

// Create and export singleton instance
export const extensionBridge = new ExtensionBridge();

// For debugging
if (typeof window !== 'undefined') {
  (window as any).extensionBridge = extensionBridge;
}
