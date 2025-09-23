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
}

export default function SessionTabs({ currentSessionResults, activeSessionId, onSessionChange }: SessionTabsProps) {
  // Sort sessions chronologically by start time
  const sortedSessions = Object.keys(currentSessionResults)
    .map(sessionId => ({
      sessionId,
      sessionData: currentSessionResults[sessionId],
      startTime: new Date(currentSessionResults[sessionId].session_start_time)
    }))
    .sort((a, b) => a.startTime.getTime() - b.startTime.getTime());

  if (sortedSessions.length === 0) {
    return null;
  }

  return (
    <div className="sessions-tabs">
      {sortedSessions.map((session, index) => {
        const sessionNumber = index + 1;
        const startTime = new Date(session.sessionData.session_start_time);
        const endTime = new Date(session.sessionData.session_end_time);
        const duration = Math.round((endTime.getTime() - startTime.getTime()) / (1000 * 60)); // minutes
        const clusterCount = session.sessionData.clusters?.length || 0;

        return (
          <button
            key={session.sessionId}
            className={`session-tab ${session.sessionId === activeSessionId ? 'active' : ''}`}
            onClick={() => onSessionChange(session.sessionId)}
          >
            <div className="session-tab-content">
              <div className="session-tab-title">Session {sessionNumber}</div>
              <div className="session-tab-meta">
                {startTime.toLocaleDateString()} • {duration}min • {clusterCount} topics
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
