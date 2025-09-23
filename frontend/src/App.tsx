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
  // Services readiness is handled internally; we auto-run loadDashboard when ready
  // Services readiness handled internally by extensionBridge
  const [availableSessions, setAvailableSessions] = useState<any[]>([])
  const [sessionAnalysisStates, setSessionAnalysisStates] = useState<{
    [sessionId: string]: 'pending' | 'loading' | 'completed' | 'error'
  }>({})
  const [currentSessionIndex, setCurrentSessionIndex] = useState(0)

  // Wait for extension services to be ready and auto-load sessions
  useEffect(() => {
    const initializeServices = async () => {
      try {
        await extensionBridge.waitForExtensionServices();
        setStatus('Analyzing most recent session...');
        setStatusType('loading');
        console.log('Extension services are ready');
        
        // Automatically load sessions after services are ready
        await loadDashboard();
      } catch (error) {
        console.error('Failed to initialize extension services:', error);
        setError('Failed to load extension services');
        setStatus('Service initialization failed');
        setStatusType('error');
      }
    };

    initializeServices();
  }, []);

  // Load Dashboard function - loads sessions and auto-analyzes most recent
  const loadDashboard = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      const constants = extensionBridge.getConstants();
      setStatus('Analyzing most recent session...')
      setStatusType('loading')
      
      // Check API health using extension service
      const healthCheck = await extensionBridge.checkApiHealth()
      if (!healthCheck.success) {
        throw new Error(`API not available: ${healthCheck.error}`)
      }
      
      // Get preprocessed Chrome history from extension
      const history = await extensionBridge.getProcessedHistory()
      if (!history || history.length === 0) {
        throw new Error(constants.ERROR_NO_HISTORY)
      }
      
      // Process history into sessions using extension service
      const sessions = await extensionBridge.processHistoryIntoSessions(history)
      console.log('Sessions:', sessions)
      if (sessions.length === 0) {
        throw new Error(constants.ERROR_NO_SESSIONS)
      }
      
      // Sort sessions by newest first (reverse chronological order)
      const sortedSessions = sessions.sort((a: any, b: any) => 
        new Date(b.start_time).getTime() - new Date(a.start_time).getTime()
      )
      
      // Store available sessions and initialize analysis states
      setAvailableSessions(sortedSessions)
      const initialStates: { [sessionId: string]: 'pending' } = {}
      sortedSessions.forEach((session: any) => {
        initialStates[session.session_id] = 'pending'
      })
      setSessionAnalysisStates(initialStates)
      
      // Set first session (most recent) as active and auto-analyze it
      if (sortedSessions.length > 0) {
        setCurrentSessionIndex(0)
        setActiveSessionId(sortedSessions[0].session_id)
        
        // Auto-analyze the first session
        setStatus('Analyzing most recent session...')
        await analyzeSession(sortedSessions[0].session_id)
      }
      
      setStatus('Most recent session analyzed. Use navigation to explore other sessions.')
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
    
    // Update current session index
    const newIndex = availableSessions.findIndex(s => s.session_id === sessionId)
    if (newIndex !== -1) {
      setCurrentSessionIndex(newIndex)
    }
    
    // Analyze session if not already completed
    if (sessionAnalysisStates[sessionId] === 'pending') {
      await analyzeSession(sessionId)
    }
  }

  // Navigation functions for Previous/Next buttons
  const goToPreviousSession = async () => {
    if (currentSessionIndex > 0) {
      const newIndex = currentSessionIndex - 1
      const newSessionId = availableSessions[newIndex].session_id
      await handleSessionChange(newSessionId)
    }
  }

  const goToNextSession = async () => {
    if (currentSessionIndex < availableSessions.length - 1) {
      const newIndex = currentSessionIndex + 1
      const newSessionId = availableSessions[newIndex].session_id
      await handleSessionChange(newSessionId)
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
      <Header 
        onSettings={openSettings}
        onPreviousSession={goToPreviousSession}
        onNextSession={goToNextSession}
        currentSessionIndex={currentSessionIndex}
        totalSessions={availableSessions.length}
        canGoPrevious={currentSessionIndex > 0}
        canGoNext={currentSessionIndex < availableSessions.length - 1}
      />
      <StatusBar status={status} statusType={statusType} />
      <main className="dashboard-main">
        {isLoading && <LoadingSpinner />}
        {error && <ErrorDisplay message={error} onRetry={loadDashboard} />}
        <Dashboard 
          currentSessionResults={currentSessionResults}
          activeSessionId={activeSessionId}
        />
      </main>
    </div>
  )
}

export default App
