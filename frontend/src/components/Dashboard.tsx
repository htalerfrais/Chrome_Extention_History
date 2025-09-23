// Dashboard component - main content area
// Orchestrates session tabs and clusters section

import SessionTabs from './SessionTabs';
import ClustersSection from './ClustersSection';

interface HistoryItem {
  url: string;
  title: string;
  visit_time: string;
}

interface Cluster {
  theme: string;
  items: HistoryItem[];
}

interface SessionData {
  session_start_time: string;
  session_end_time: string;
  clusters: Cluster[];
}

interface DashboardProps {
  currentSessionResults: Record<string, SessionData>;
  activeSessionId: string | null;
  onSessionChange: (sessionId: string) => void;
}

export default function Dashboard({ currentSessionResults, activeSessionId, onSessionChange }: DashboardProps) {
  // Get the current session data
  const currentSessionData = activeSessionId ? currentSessionResults[activeSessionId] : null;

  return (
    <div className="dashboard-content">
      <SessionTabs
        currentSessionResults={currentSessionResults}
        activeSessionId={activeSessionId}
        onSessionChange={onSessionChange}
      />
      <ClustersSection sessionData={currentSessionData} />
    </div>
  );
}
