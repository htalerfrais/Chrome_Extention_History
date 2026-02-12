import { useNavigate, useLocation } from 'react-router-dom';
import { useSessionStore } from '../../../stores/useSessionStore';

export default function SessionList() {
  const navigate = useNavigate();
  const location = useLocation();

  const availableSessions = useSessionStore((s) => s.availableSessions);
  const activeSessionId = useSessionStore((s) => s.activeSessionId);
  const sessionResults = useSessionStore((s) => s.sessionResults);
  const sessionAnalysisStates = useSessionStore((s) => s.sessionAnalysisStates);
  const setActiveSession = useSessionStore((s) => s.setActiveSession);

  const sortedSessions = [...availableSessions]
    .map((session) => ({
      sessionId: session.session_id,
      sessionData: session,
      startTime: new Date(session.start_time),
    }))
    .sort((a, b) => b.startTime.getTime() - a.startTime.getTime());

  if (sortedSessions.length === 0) {
    return (
      <div className="px-3 py-4 text-xs text-white/30 text-center">
        No sessions yet
      </div>
    );
  }

  const handleSessionClick = (sessionId: string) => {
    setActiveSession(sessionId);
    if (location.pathname !== '/sessions') {
      navigate('/sessions');
    }
  };

  return (
    <div className="flex flex-col gap-1 px-2 py-2 overflow-y-auto thin-scrollbar">
      {sortedSessions.map((session, index) => {
        const sessionNumber = index + 1;
        const startTime = session.startTime;
        const endTime = new Date(session.sessionData.end_time);
        const duration = Math.max(1, Math.round((endTime.getTime() - startTime.getTime()) / (1000 * 60)));
        const itemCount = session.sessionData.items?.length || 0;

        const analysisState = sessionAnalysisStates[session.sessionId] || 'pending';
        const sessionResult = sessionResults[session.sessionId];
        const clusterCount = sessionResult?.clusters?.length || 0;

        let statusText = '';
        switch (analysisState) {
          case 'pending':
            statusText = `${itemCount} items`;
            break;
          case 'loading':
            statusText = 'Analyzing...';
            break;
          case 'completed':
            statusText = `${duration}min · ${clusterCount} topics`;
            break;
          case 'error':
            statusText = 'Failed';
            break;
        }

        const isActive = session.sessionId === activeSessionId;

        return (
          <button
            key={session.sessionId}
            onClick={() => handleSessionClick(session.sessionId)}
            className={`flex flex-col items-start gap-0.5 w-full px-3 py-2 text-left rounded transition-colors ${
              isActive
                ? 'bg-white/10 text-white'
                : 'text-white/50 hover:bg-white/5 hover:text-white/70'
            }`}
          >
            <span className="text-[11px] uppercase tracking-[0.2em]">
              Session {sessionNumber}
            </span>
            <span className="text-[10px] text-white/40">
              {startTime.toLocaleDateString()} · {statusText}
            </span>
          </button>
        );
      })}
    </div>
  );
}
