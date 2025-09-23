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
  isAnalyzing?: boolean;
}

export default function ClustersSection({ sessionData, isAnalyzing = false }: ClustersSectionProps) {
  // Compute clusters when available
  const clusters = sessionData?.clusters || [];

  // If not analyzing and nothing to show, render nothing
  if (!isAnalyzing && (!sessionData || clusters.length === 0)) {
    return null;
  }

  // Render container with optional content and overlay

  return (
    <div className="clusters-section">
      {sessionData && clusters.length > 0 && (
        <>
          <div className="clusters-header">
            <h2>Browsing Topics</h2>
            <SessionInfo sessionData={sessionData} />
          </div>
          <div className="clusters-container">
            {clusters.map((cluster, index) => (
              <ClusterCard key={`${cluster.theme}-${index}`} cluster={cluster} />
            ))}
          </div>
        </>
      )}
      {isAnalyzing && (
        <div className="clusters-overlay">
          <div className="loading-container">
            <div className="loading-spinner" />
            <p className="status-text">Analyzing session...</p>
          </div>
        </div>
      )}
    </div>
  );
}
