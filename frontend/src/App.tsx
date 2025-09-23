import { useState, useEffect } from 'react'
import './App.css'
import Header from './components/Header'
import StatusBar from './components/StatusBar'
import LoadingSpinner from './components/LoadingSpinner'
import ErrorDisplay from './components/ErrorDisplay'
import Dashboard from './components/Dashboard'
import { extensionBridge } from './services/extensionBridge'

function App() {
  // State management
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState('Waiting for extension services...')
  const [statusType, setStatusType] = useState<'loading' | 'success' | 'error'>('loading')
  const [currentSessionResults, setCurrentSessionResults] = useState<any>({})
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const [servicesReady, setServicesReady] = useState(false)

  // Wait for extension services to be ready
  useEffect(() => {
    const initializeServices = async () => {
      try {
        await extensionBridge.waitForExtensionServices();
        setServicesReady(true);
        setStatus('Extension services ready');
        setStatusType('success');
        console.log('Extension services are ready');
      } catch (error) {
        console.error('Failed to initialize extension services:', error);
        setError('Failed to load extension services');
        setStatus('Service initialization failed');
        setStatusType('error');
      }
    };

    initializeServices();
  }, []);

  // Load Dashboard function (using ExtensionBridge)
  const loadDashboard = async () => {
    if (!servicesReady) {
      setError('Extension services not ready');
      return;
    }

    try {
      setIsLoading(true)
      setError(null)
      
      const constants = extensionBridge.getConstants();
      
      setStatus(constants.STATUS_CHECKING_API)
      setStatusType('loading')
      
      // Check API health using extension service
      const healthCheck = await extensionBridge.checkApiHealth()
      if (!healthCheck.success) {
        throw new Error(`API not available: ${healthCheck.error}`)
      }
      
      setStatus(constants.STATUS_FETCHING_HISTORY)
      
      // Get preprocessed Chrome history from extension
      const history = await extensionBridge.getProcessedHistory()
      if (!history || history.length === 0) {
        throw new Error(constants.ERROR_NO_HISTORY)
      }
      
      setStatus(constants.STATUS_PROCESSING_SESSIONS)
      
      // Process history into sessions using extension service
      const sessions = await extensionBridge.processHistoryIntoSessions(history)
      console.log('Sessions:', sessions)
      if (sessions.length === 0) {
        throw new Error(constants.ERROR_NO_SESSIONS)
      }
      
      setStatus(constants.STATUS_ANALYZING_PATTERNS)
      
      // Get clustering results using extension service
      const clusterResult = await extensionBridge.clusterSessions(sessions)
      
      if (!clusterResult.success) {
        throw new Error(`${constants.ERROR_CLUSTERING_FAILED}: ${clusterResult.error}`)
      }
      
      // Store results and update UI
      setCurrentSessionResults(clusterResult.data)
      
      // Set first session as active
      const sessionIds = Object.keys(clusterResult.data)
      if (sessionIds.length > 0) {
        setActiveSessionId(sessionIds[0])
      }
      
      setStatus(constants.STATUS_ANALYSIS_COMPLETE)
      setStatusType('success')
      
    } catch (error) {
      console.error('Dashboard loading failed:', error)
      setError(error instanceof Error ? error.message : 'Unknown error')
      setStatus(extensionBridge.getConstants().STATUS_ANALYSIS_FAILED)
      setStatusType('error')
    } finally {
      setIsLoading(false)
    }
  }

  // Open Settings function (using ExtensionBridge)
  const openSettings = () => {
    const config = extensionBridge.getConfig()
    const constants = extensionBridge.getConstants()
    
    const currentEnv = config.currentEnvironment
    const apiUrl = config.getApiBaseUrl()
    const sessionGap = constants.SESSION_GAP_MINUTES
    
    alert(`Settings\n\nEnvironment: ${currentEnv}\nAPI URL: ${apiUrl}\nSession Gap: ${sessionGap} minutes\n\nTo switch environments, modify extension/api/config.js`)
  }

  return (
    <div className="dashboard-container">
      <Header onRefresh={loadDashboard} onSettings={openSettings} />
      <StatusBar status={status} statusType={statusType} />
      <main className="dashboard-main">
        {isLoading && <LoadingSpinner />}
        {error && <ErrorDisplay message={error} onRetry={loadDashboard} />}
        <Dashboard 
          currentSessionResults={currentSessionResults}
          activeSessionId={activeSessionId}
          onSessionChange={setActiveSessionId}
        />
      </main>
    </div>
  )
}

export default App
