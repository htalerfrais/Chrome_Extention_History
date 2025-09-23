// ClustersSection component - displays thematic clusters
// Main container for cluster display with header and session info

import SessionInfo from './SessionInfo';
import ClusterCard from './ClusterCard';

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

interface ClustersSectionProps {
  sessionData: SessionData | null;
}

export default function ClustersSection({ sessionData }: ClustersSectionProps) {
  // If there is no data yet (e.g., first session is still analyzing), render nothing
  if (!sessionData) {
    return null;
  }

  const clusters = sessionData.clusters || [];

  // While analyzing or if no clusters are available yet, render nothing
  if (clusters.length === 0) {
    return null;
  }

  return (
    <div className="clusters-section">
      <div className="clusters-header">
        <h2>Browsing Topics</h2>
        <SessionInfo sessionData={sessionData} />
      </div>
      <div className="clusters-container">
        {clusters.map((cluster, index) => (
          <ClusterCard key={`${cluster.theme}-${index}`} cluster={cluster} />
        ))}
      </div>
    </div>
  );
}
