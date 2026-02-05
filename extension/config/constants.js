// Application Constants for Chrome Extension History
// Static values that define application behavior

// Define constants as regular variables (not ES6 exports)
const SESSION_GAP_MINUTES = 30; // 
const MAX_SESSION_DURATION_MINUTES = 90; // Maximum session duration before auto-closure
const HISTORY_DAYS_BACK = 7;
const DAY_MS = 24 * 60 * 60 * 1000;
const HOUR_MS = 60 * 60 * 1000;
const MINUTE_MS = 60 * 1000;

// History and API constants
const MAX_HISTORY_RESULTS = 1000;
const MIN_SESSION_ITEMS = 2;
const API_TIMEOUT_MS = 5000; // For health checks
const API_REQUEST_TIMEOUT_MS = 30000; // For main requests

// UI constants
const POPUP_WIDTH = 500;
const MAX_CLUSTER_ITEMS_DISPLAY = 5;

// Clustering constants
const MAX_CLUSTERS_DEFAULT = 10;
const MIN_CLUSTER_SIZE_DEFAULT = 2;
const URL_SIMILARITY_THRESHOLD = 0.8; // Seuil de similarité pour la déduplication d'URLs (0.0-1.0, plus élevé = plus strict)

// Retry configuration
const API_RETRIES = 3;
const API_RETRY_DELAY_MS = 1000;

// Chrome extension specific
const CHROME_HISTORY_PERMISSION = 'history';
const CHROME_STORAGE_PERMISSION = 'storage';
const CHROME_TABS_PERMISSION = 'tabs';

// Default values
const DEFAULT_SEARCH_PLACEHOLDER = 'Recherche dans l\'historique';
const DEFAULT_SEARCH_BUTTON_TEXT = 'Chercher';
const DEFAULT_DASHBOARD_BUTTON_TEXT = '📊 Dashboard';

// Error messages
const ERROR_NO_HISTORY = 'No browsing history found';
const ERROR_NO_SESSIONS = 'No valid sessions found in history';
const ERROR_API_UNAVAILABLE = 'API not available';
const ERROR_CLUSTERING_FAILED = 'Clustering failed';

// Status messages
const STATUS_CHECKING_API = 'Checking API connection...';
const STATUS_FETCHING_HISTORY = 'Fetching browsing history...';
const STATUS_PROCESSING_SESSIONS = 'Processing sessions...';
const STATUS_ANALYZING_PATTERNS = 'Analyzing browsing patterns...';
const STATUS_ANALYSIS_COMPLETE = 'Analysis complete';
const STATUS_ANALYSIS_FAILED = 'Analysis failed';

// Create constants object
const ExtensionConstants = {
    SESSION_GAP_MINUTES,
    MAX_SESSION_DURATION_MINUTES,
    HISTORY_DAYS_BACK,
    DAY_MS,
    HOUR_MS,
    MINUTE_MS,
    MAX_HISTORY_RESULTS,
    MIN_SESSION_ITEMS,
    API_TIMEOUT_MS,
    API_REQUEST_TIMEOUT_MS,
    POPUP_WIDTH,
    MAX_CLUSTER_ITEMS_DISPLAY,
    MAX_CLUSTERS_DEFAULT,
    MIN_CLUSTER_SIZE_DEFAULT,
    URL_SIMILARITY_THRESHOLD,
    API_RETRIES,
    API_RETRY_DELAY_MS,
    CHROME_HISTORY_PERMISSION,
    CHROME_STORAGE_PERMISSION,
    CHROME_TABS_PERMISSION,
    DEFAULT_SEARCH_PLACEHOLDER,
    DEFAULT_SEARCH_BUTTON_TEXT,
    DEFAULT_DASHBOARD_BUTTON_TEXT,
    ERROR_NO_HISTORY,
    ERROR_NO_SESSIONS,
    ERROR_API_UNAVAILABLE,
    ERROR_CLUSTERING_FAILED,
    STATUS_CHECKING_API,
    STATUS_FETCHING_HISTORY,
    STATUS_PROCESSING_SESSIONS,
    STATUS_ANALYZING_PATTERNS,
    STATUS_ANALYSIS_COMPLETE,
    STATUS_ANALYSIS_FAILED
};

// Make available globally
if (typeof window !== 'undefined') {
    window.ExtensionConstants = ExtensionConstants;
}

// For service workers (background scripts)
if (typeof self !== 'undefined') {
    self.ExtensionConstants = ExtensionConstants;
}
