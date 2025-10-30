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
    .sort((a, b) => b.startTime.getTime() - a.startTime.getTime());

  if (sortedSessions.length === 0) {
    return null;
  }

  return (
    <div className="w-full overflow-x-auto border-b border-white/10 bg-black">
      <div className="flex gap-2 px-6 py-2">
        {sortedSessions.map((session, index) => {
          const sessionNumber = index + 1;
          const startTime = new Date(session.sessionData.start_time);
          const endTime = new Date(session.sessionData.end_time);
          const duration = Math.max(1, Math.round((endTime.getTime() - startTime.getTime()) / (1000 * 60))); // minutes
          const itemCount = session.sessionData.items?.length || 0;

          const analysisState = sessionAnalysisStates[session.sessionId] || 'pending';
          const sessionResult = currentSessionResults[session.sessionId];
          const clusterCount = sessionResult?.clusters?.length || 0;

          let statusText = '';
          switch (analysisState) {
            case 'pending':
              statusText = `${itemCount} items`;
              break;
            case 'loading':
              statusText = 'Analyzing';
              break;
            case 'completed':
              statusText = `${duration} min · ${clusterCount} topics`;
              break;
            case 'error':
              statusText = 'Analysis failed';
              break;
          }

          const isActive = session.sessionId === activeSessionId;

          return (
            <button
              key={session.sessionId}
              onClick={() => onSessionChange(session.sessionId)}
              className={`flex flex-col items-start gap-1 min-w-[160px] px-4 py-3 border border-white/10 ${isActive ? 'bg-white/10 text-white' : 'bg-transparent text-white/50 hover:text-white'} text-left`}
            >
              <span className="text-[11px] uppercase tracking-[0.3em]">
                Session {sessionNumber}
              </span>
              <span className="text-[10px] uppercase tracking-[0.2em] text-white/40">
                {startTime.toLocaleDateString()} · {statusText}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
