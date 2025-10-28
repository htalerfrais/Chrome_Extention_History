// Dashboard component - main content area
// Displays clusters for the current session

import ClustersSection from './ClustersSection';
import type { SessionResults } from '../types/session';

interface DashboardProps {
  currentSessionResults: SessionResults;
  activeSessionId: string | null;
  onReanalyze?: () => void;
  isReanalyzing?: boolean;
}

export default function Dashboard({ 
  currentSessionResults, 
  activeSessionId,
  onReanalyze,
  isReanalyzing
}: DashboardProps) {
  // Get the current session data
  const currentSessionData = activeSessionId ? currentSessionResults[activeSessionId] : null;
  const isAnalyzing = !currentSessionData;

  return (
    <div className="dashboard-content">
      <ClustersSection sessionData={currentSessionData} isAnalyzing={isAnalyzing} onReanalyze={onReanalyze} isReanalyzing={isReanalyzing} />
    </div>
  );
}
