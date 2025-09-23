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
  const [availableSessions, setAvailableSessions] = useState<any[]>([])
  const [sessionAnalysisStates, setSessionAnalysisStates] = useState<{
    [sessionId: string]: 'pending' | 'loading' | 'completed' | 'error'
  }>({})

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

  // Load Dashboard function - now only loads sessions, no clustering
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
      
      // Store available sessions and initialize analysis states
      setAvailableSessions(sessions)
      const initialStates: { [sessionId: string]: 'pending' } = {}
      sessions.forEach((session: any) => {
        initialStates[session.session_id] = 'pending'
      })
      setSessionAnalysisStates(initialStates)
      
      // Set first session as active (but don't analyze yet)
      if (sessions.length > 0) {
        setActiveSessionId(sessions[0].session_id)
      }
      
      setStatus('Sessions loaded. Click on a session tab to analyze it.')
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

  // Analyze single session when user clicks on a tab
  const analyzeSession = async (sessionId: string) => {
    const session = availableSessions.find(s => s.session_id === sessionId)
    if (!session) {
      console.error(`Session ${sessionId} not found`)
      return
    }

    // Skip if already completed
    if (sessionAnalysisStates[sessionId] === 'completed') {
      return
    }

    try {
      // Update session state to loading
      setSessionAnalysisStates(prev => ({
        ...prev,
        [sessionId]: 'loading'
      }))

      setStatus(`Analyzing session ${sessionId}...`)
      setStatusType('loading')

      // Cluster single session using extension service
      const clusterResult = await extensionBridge.clusterSession(session)
      
      if (!clusterResult.success) {
        throw new Error(`Clustering failed: ${clusterResult.error}`)
      }

      // Store result for this session
      setCurrentSessionResults((prev: any) => ({
        ...prev,
        [sessionId]: clusterResult.data
      }))

      // Update session state to completed
      setSessionAnalysisStates(prev => ({
        ...prev,
        [sessionId]: 'completed'
      }))

      setStatus(`Session ${sessionId} analyzed successfully`)
      setStatusType('success')
      
    } catch (error) {
      console.error(`Session analysis failed for ${sessionId}:`, error)
      
      // Update session state to error
      setSessionAnalysisStates(prev => ({
        ...prev,
        [sessionId]: 'error'
      }))

      setStatus(`Session ${sessionId} analysis failed`)
      setStatusType('error')
    }
  }

  // Handle session change - analyze if needed
  const handleSessionChange = async (sessionId: string) => {
    setActiveSessionId(sessionId)
    
    // Analyze session if not already completed
    if (sessionAnalysisStates[sessionId] === 'pending') {
      await analyzeSession(sessionId)
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
          onSessionChange={handleSessionChange}
          availableSessions={availableSessions}
          sessionAnalysisStates={sessionAnalysisStates}
        />
      </main>
    </div>
  )
}

export default App
