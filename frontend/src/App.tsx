import { useEffect } from 'react'
import AppLayout from './layouts/AppLayout'
import { useSessionStore } from './stores/useSessionStore'

function App() {
  const initializeSessions = useSessionStore((s) => s.initializeSessions)

  useEffect(() => {
    initializeSessions()
  }, [initializeSessions])

  return <AppLayout />
}

export default App
