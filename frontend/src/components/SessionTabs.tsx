// SessionTabs component - displays session navigation tabs
// Shows different browsing sessions with metadata and allows switching between them

interface SessionData {
  session_start_time: string;
  session_end_time: string;
  clusters: any[];
}

interface SessionTabsProps {
  currentSessionResults: Record<string, SessionData>;
  activeSessionId: string | null;
  onSessionChange: (sessionId: string) => void;
  availableSessions: any[];
  sessionAnalysisStates: Record<string, 'pending' | 'loading' | 'completed' | 'error'>;
}

export default function SessionTabs({ 
  currentSessionResults, 
  activeSessionId, 
  onSessionChange, 
  availableSessions, 
  sessionAnalysisStates 
}: SessionTabsProps) {
  // Sort available sessions chronologically by start time
  const sortedSessions = availableSessions
    .map(session => ({
      sessionId: session.session_id,
      sessionData: session,
      startTime: new Date(session.start_time)
    }))
    .sort((a, b) => a.startTime.getTime() - b.startTime.getTime());

  if (sortedSessions.length === 0) {
    return null;
  }

  return (
    <div className="sessions-tabs">
      {sortedSessions.map((session, index) => {
        const sessionNumber = index + 1;
        const startTime = new Date(session.sessionData.start_time);
        const endTime = new Date(session.sessionData.end_time);
        const duration = Math.round((endTime.getTime() - startTime.getTime()) / (1000 * 60)); // minutes
        const itemCount = session.sessionData.items?.length || 0;
        
        // Get analysis state and result
        const analysisState = sessionAnalysisStates[session.sessionId] || 'pending';
        const sessionResult = currentSessionResults[session.sessionId];
        const clusterCount = sessionResult?.clusters?.length || 0;

        // Determine display text based on state
        let statusText = '';
        let statusClass = '';
        switch (analysisState) {
          case 'pending':
            statusText = `${itemCount} items • Click to analyze`;
            statusClass = 'pending';
            break;
          case 'loading':
            statusText = 'Analyzing...';
            statusClass = 'loading';
            break;
          case 'completed':
            statusText = `${duration}min • ${clusterCount} topics`;
            statusClass = 'completed';
            break;
          case 'error':
            statusText = 'Analysis failed • Click to retry';
            statusClass = 'error';
            break;
        }

        return (
          <button
            key={session.sessionId}
            className={`session-tab ${session.sessionId === activeSessionId ? 'active' : ''} ${statusClass}`}
            onClick={() => onSessionChange(session.sessionId)}
          >
            <div className="session-tab-content">
              <div className="session-tab-title">Session {sessionNumber}</div>
              <div className="session-tab-meta">
                {startTime.toLocaleDateString()} • {statusText}
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
