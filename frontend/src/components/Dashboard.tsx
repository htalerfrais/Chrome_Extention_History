// Dashboard component - main content area
// Displays clusters for the current session

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
}

export default function Dashboard({ 
  currentSessionResults, 
  activeSessionId
}: DashboardProps) {
  // Get the current session data
  const currentSessionData = activeSessionId ? currentSessionResults[activeSessionId] : null;

  return (
    <div className="dashboard-content">
      <ClustersSection sessionData={currentSessionData} />
    </div>
  );
}
