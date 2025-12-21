import { useState, useEffect } from 'react'
import './App.css'
import Header from './components/Header'
import ErrorDisplay from './components/ErrorDisplay'
import Dashboard from './components/Dashboard'
import MainLayout from './components/MainLayout'
import ChatWindow from './components/ChatWindow'
import { extensionBridge } from './services/extensionBridge'
import type { SessionResults, SessionAnalysisStates } from './types/session'

function App() {
  // State management
  const [error, setError] = useState<string | null>(null)
  
  const [currentSessionResults, setCurrentSessionResults] = useState<SessionResults>({})
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const [availableSessions, setAvailableSessions] = useState<any[]>([])
  const [sessionAnalysisStates, setSessionAnalysisStates] = useState<SessionAnalysisStates>({})
  const [isReanalyzing, setIsReanalyzing] = useState(false)

  // Wait for extension services to be ready and auto-load sessions
  useEffect(() => {
    const initializeServices = async () => {
      try {
        await extensionBridge.waitForExtensionServices();
        
        console.log('Extension services are ready');
        
        // Automatically load sessions after services are ready
        await loadDashboard();
      } catch (error) {
        console.error('Failed to initialize extension services:', error);
        setError('Failed to load extension services');
        
      }
    };

    initializeServices();
  }, []);

  // Load Dashboard function - loads sessions and auto-analyzes most recent
  const loadDashboard = async () => {
    try {
      setError(null)
      
      const constants = extensionBridge.getConstants();
      
      
      // Check API health using extension service
      const healthCheck = await extensionBridge.checkApiHealth()
      if (!healthCheck.success) {
        throw new Error(`API not available: ${healthCheck.error}`)
      }
      
      // Get all sessions using ExtensionAPI (unified method)
      const sessions = await extensionBridge.getAllSessions()
      console.log('Sessions:', sessions)
      if (sessions.length === 0) {
        throw new Error(constants.ERROR_NO_SESSIONS)
      }
      
      // Sort sessions by newest first (reverse chronological order)
      const sortedSessions = sessions.sort((a: any, b: any) => 
        new Date(b.start_time).getTime() - new Date(a.start_time).getTime()
      )
      
      // Store available sessions and initialize analysis states
      // Add session_id field for internal use (use session_identifier as the key)
      const sessionsWithId = sortedSessions.map((session: any) => ({
        ...session,
        session_id: session.session_identifier
      }))
      setAvailableSessions(sessionsWithId)
      
      const initialStates: { [sessionId: string]: 'pending' } = {}
      sessionsWithId.forEach((session: any) => {
        initialStates[session.session_identifier] = 'pending'
      })
      setSessionAnalysisStates(initialStates)
      
      // Set first session (most recent) as active and auto-analyze it
      if (sessionsWithId.length > 0) {
        const firstSessionId = sessionsWithId[0].session_identifier
        setActiveSessionId(firstSessionId)
        
        // Auto-analyze the first session
        // Call with immediate session object to avoid pending state depending on setState order
        const firstSession = sessionsWithId[0]
        setSessionAnalysisStates(prev => ({
          ...prev,
          [firstSession.session_identifier]: 'loading'
        }))
        const clusterResult = await extensionBridge.clusterSession(firstSession)
        if (!clusterResult.success) {
          throw new Error(`Clustering failed: ${clusterResult.error}`)
        }
        setCurrentSessionResults((prev: any) => ({
          ...prev,
          [firstSession.session_identifier]: clusterResult.data
        }))
        setSessionAnalysisStates(prev => ({
          ...prev,
          [firstSession.session_identifier]: 'completed'
        }))
        
      }
      
      
    } catch (error) {
      console.error('Dashboard loading failed:', error)
      setError(error instanceof Error ? error.message : 'Unknown error')
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

      
      
    } catch (error) {
      console.error(`Session analysis failed for ${sessionId}:`, error)
      
      // Update session state to error
      setSessionAnalysisStates(prev => ({
        ...prev,
        [sessionId]: 'error'
      }))

      
    }
  }

  // Force re-analysis for the active session
  const reanalyzeActiveSession = async () => {
    if (!activeSessionId) return
    const session = availableSessions.find(s => s.session_id === activeSessionId)
    if (!session) return

    try {
      setIsReanalyzing(true)
      

      const result = await extensionBridge.clusterSession(session, { force: true })
      if (!result.success) {
        throw new Error(`Clustering failed: ${result.error}`)
      }

      setCurrentSessionResults((prev: any) => ({
        ...prev,
        [activeSessionId]: result.data
      }))
      setSessionAnalysisStates(prev => ({
        ...prev,
        [activeSessionId]: 'completed'
      }))
      
    } catch (error) {
      console.error('Re-analysis failed:', error)
      
    } finally {
      setIsReanalyzing(false)
    }
  }

  // Handle session change - analyze if needed
  const handleSessionChange = async (sessionId: string) => {
    setActiveSessionId(sessionId)
    
    // Update current session index
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

  // Determine if the active session is currently analyzing
  const activeIsLoading = activeSessionId ? sessionAnalysisStates[activeSessionId] === 'loading' : false

  return (
    <div className="min-h-screen bg-black text-white font-sans">
      <Header 
        onSettings={openSettings}
      />
      <MainLayout 
        children={
          <main className="w-full">
            {error && <ErrorDisplay message={error} onRetry={loadDashboard} />}
            <Dashboard 
              currentSessionResults={currentSessionResults}
              activeSessionId={activeSessionId}
              onReanalyze={reanalyzeActiveSession}
              isReanalyzing={isReanalyzing}
              activeIsLoading={activeIsLoading}
              availableSessions={availableSessions}
              sessionAnalysisStates={sessionAnalysisStates}
              onSessionChange={handleSessionChange}
            />
          </main>
        }
        chatComponent={<ChatWindow />}
      />
    </div>
  )
}

export default App
