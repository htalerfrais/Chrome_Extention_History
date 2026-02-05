// Dashboard component - main content area
// Displays clusters for the current session

import ClustersSection from './ClustersSection';
import SessionTabs from './SessionTabs';
import type { SessionResults, SessionAnalysisStates } from '../types/session';

interface DashboardProps {
  currentSessionResults: SessionResults;
  activeSessionId: string | null;
  onReanalyze?: () => void;
  isReanalyzing?: boolean;
  activeIsLoading?: boolean;
  availableSessions: any[];
  sessionAnalysisStates: SessionAnalysisStates;
  onSessionChange: (sessionId: string) => void;
}

export default function Dashboard({ 
  currentSessionResults, 
  activeSessionId,
  onReanalyze,
  isReanalyzing,
  activeIsLoading = false,
  availableSessions,
  sessionAnalysisStates,
  onSessionChange
}: DashboardProps) {
  // Get the current session data
  const currentSessionData = activeSessionId ? currentSessionResults[activeSessionId] : null;
  const isAnalyzing = !currentSessionData || activeIsLoading;

  return (
    <div className="w-full space-y-6">
      <SessionTabs 
        currentSessionResults={currentSessionResults}
        activeSessionId={activeSessionId}
        onSessionChange={onSessionChange}
        availableSessions={availableSessions}
        sessionAnalysisStates={sessionAnalysisStates}
      />
      <ClustersSection sessionData={currentSessionData} isAnalyzing={isAnalyzing} onReanalyze={onReanalyze} isReanalyzing={isReanalyzing} />
    </div>
  );
}
