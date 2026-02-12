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
    <div className="flex flex-col h-full bg-black text-white">
      {/* Header bar */}
      {(sessionData || isReanalyzing) && (
        <div className="flex-shrink-0 w-full px-6 py-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between border-b border-white/10">
          <h2 className="text-sm uppercase tracking-[0.4em] text-white/70">Topics</h2>
          <div className="flex flex-wrap items-center gap-4 md:justify-end">
            {sessionData && <SessionInfo sessionData={sessionData} />}
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
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="flex-1 flex flex-col items-center justify-center py-16">
          <div className="w-6 h-6 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" />
          <span className="text-white/40 uppercase tracking-[0.35em] text-xs mt-6">
            {isReanalyzing ? 'Re-analyzing Session' : 'Analyzing Session'}
          </span>
        </div>
      )}

      {/* Master-detail split */}
      {!isLoading && sessionData && clusters.length > 0 && (
        <div className="flex flex-1 min-h-0">
          {/* Master: topic list */}
          <div className="w-[420px] flex-shrink-0 border-r border-white/10 overflow-y-auto thin-scrollbar py-2">
            {clusters.map((cluster, index) => {
              const isSelected = index === selectedIndex;
              return (
                <button
                  key={`${cluster.theme}-${index}`}
                  onClick={() => setSelectedIndex(index)}
                  className={`w-full text-left px-4 py-3 flex flex-col gap-1 transition-colors ${
                    isSelected
                      ? 'bg-white/10 text-white'
                      : 'text-white/50 hover:bg-white/5 hover:text-white/70'
                  }`}
                >
                  <span className="text-xs uppercase tracking-[0.2em]">
                    {cluster.theme}
                  </span>
                  {cluster.summary && (
                    <span className="text-xs text-white/40 line-clamp-6 leading-relaxed">
                      {cluster.summary}
                    </span>
                  )}
                  <span className="text-[10px] text-white/35 mt-0.5">
                    {cluster.items.length} item{cluster.items.length !== 1 ? 's' : ''}
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
