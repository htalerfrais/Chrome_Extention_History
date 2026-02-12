import { useState } from 'react';
import SessionInfo from './SessionInfo';
import ClusterDetail from './ClusterDetail';

interface HistoryItem {
  url: string;
  title: string;
  visit_time: string;
}

interface Cluster {
  theme: string;
  summary?: string;
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
  const [selectedIndex, setSelectedIndex] = useState(0);
  const clusters = sessionData?.clusters || [];
  const isLoading = isAnalyzing || isReanalyzing;

  if (!isLoading && (!sessionData || clusters.length === 0)) {
    return null;
  }

  const selectedCluster = clusters[selectedIndex] ?? null;

  return (
    <div className="flex flex-col h-full bg-bg text-text">
      {/* Header bar */}
      {(sessionData || isReanalyzing) && (
        <div className="flex-shrink-0 w-full px-6 py-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between border-b border-line">
          <h2 className="text-sm font-semibold tracking-wide text-text-secondary">Topics</h2>
          <div className="flex flex-wrap items-center gap-3 md:justify-end">
            {sessionData && <SessionInfo sessionData={sessionData} />}
            {onReanalyze && (
              <button
                onClick={onReanalyze}
                disabled={isReanalyzing}
                className="px-4 py-1.5 text-xxs font-medium uppercase tracking-wider rounded-lg bg-surface hover:bg-surface-hover text-text-secondary hover:text-text disabled:opacity-40 transition-colors duration-150"
              >
                {isReanalyzing ? 'Re-analyzing...' : 'Re-analyze'}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="flex-1 flex flex-col items-center justify-center py-16 gap-5">
          <div className="w-7 h-7 border-2 border-accent/20 border-t-accent rounded-full animate-spin" />
          <span className="text-text-tertiary text-xs tracking-wide">
            {isReanalyzing ? 'Re-analyzing session...' : 'Analyzing session...'}
          </span>
        </div>
      )}

      {/* Master-detail split */}
      {!isLoading && sessionData && clusters.length > 0 && (
        <div className="flex flex-1 min-h-0">
          {/* Master: topic list */}
          <div className="w-[420px] flex-shrink-0 border-r border-line bg-bg-deep overflow-y-auto thin-scrollbar py-1">
            {clusters.map((cluster, index) => {
              const isSelected = index === selectedIndex;
              return (
                <button
                  key={`${cluster.theme}-${index}`}
                  onClick={() => setSelectedIndex(index)}
                  className={`w-full text-left px-5 py-4 flex flex-col gap-1.5 transition-colors duration-150 border-l-2 ${
                    isSelected
                      ? 'bg-accent-subtle border-accent text-text'
                      : 'border-transparent text-text-secondary hover:bg-surface hover:text-text'
                  }`}
                >
                  <span className="text-sm font-medium leading-snug">
                    {cluster.theme}
                  </span>
                  {cluster.summary && (
                    <span className="text-xs text-text-tertiary line-clamp-6 leading-relaxed">
                      {cluster.summary}
                    </span>
                  )}
                  <span className="text-xxs text-text-ghost mt-0.5">
                    {cluster.items.length} page{cluster.items.length !== 1 ? 's' : ''}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Detail: selected cluster content */}
          <div className="flex-1 min-w-0 overflow-y-auto thin-scrollbar">
            {selectedCluster && <ClusterDetail cluster={selectedCluster} />}
          </div>
        </div>
      )}
    </div>
  );
}
