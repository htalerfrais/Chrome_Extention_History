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
  onReanalyze?: () => void;
  isReanalyzing?: boolean;
}

export default function ClustersSection({ sessionData, isAnalyzing = false, onReanalyze, isReanalyzing = false }: ClustersSectionProps) {
  // Compute clusters when available
  const clusters = sessionData?.clusters || [];

  // If not analyzing and nothing to show, render nothing
  if (!isAnalyzing && (!sessionData || clusters.length === 0)) {
    return null;
  }

  // Render container with optional content and overlay

  return (
    <div className="bg-black text-white w-full">
      {sessionData && clusters.length > 0 && (
        <>
          <div className="w-full px-6 py-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <h2 className="text-sm uppercase tracking-[0.4em] text-white/70">Topics</h2>
            <div className="flex flex-wrap items-center gap-4 md:justify-end">
              <SessionInfo sessionData={sessionData} />
              {onReanalyze && (
                <button
                  onClick={onReanalyze}
                  disabled={isReanalyzing}
                  className="px-4 py-2 text-[10px] uppercase tracking-[0.3em] bg-white/10 text-white/80 hover:text-white disabled:opacity-40"
                >
                  {isReanalyzing ? 'Re-analyzing' : 'Re-analyze'}
                </button>
              )}
            </div>
          </div>
          <div className="px-6 pb-6 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
            {clusters.map((cluster, index) => (
              <ClusterCard key={`${cluster.theme}-${index}`} cluster={cluster} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
