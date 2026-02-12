import { useSessionStore } from '../../stores/useSessionStore';
import ClustersSection from './components/ClustersSection';
import ErrorDisplay from '../../components/ErrorDisplay';

export default function SessionView() {
  const activeSessionId = useSessionStore((s) => s.activeSessionId);
  const sessionResults = useSessionStore((s) => s.sessionResults);
  const sessionAnalysisStates = useSessionStore((s) => s.sessionAnalysisStates);
  const isReanalyzing = useSessionStore((s) => s.isReanalyzing);
  const error = useSessionStore((s) => s.error);
  const reanalyzeActiveSession = useSessionStore((s) => s.reanalyzeActiveSession);
  const initializeSessions = useSessionStore((s) => s.initializeSessions);

  const currentSessionData = activeSessionId ? sessionResults[activeSessionId] : null;
  const activeIsLoading = activeSessionId
    ? sessionAnalysisStates[activeSessionId] === 'loading'
    : false;
  const isAnalyzing = !currentSessionData || activeIsLoading;

  if (error) {
    return <ErrorDisplay message={error} onRetry={initializeSessions} />;
  }

  if (!activeSessionId) {
    return (
      <div className="flex items-center justify-center h-full text-text-tertiary text-sm">
        Select a session from the sidebar
      </div>
    );
  }

  return (
    <main className="w-full h-full">
      <ClustersSection
        sessionData={currentSessionData}
        isAnalyzing={isAnalyzing}
        onReanalyze={reanalyzeActiveSession}
        isReanalyzing={isReanalyzing}
      />
    </main>
  );
}
