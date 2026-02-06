import ClusterItem from './ClusterItem';

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

interface ClusterCardProps {
  cluster: Cluster;
}

export default function ClusterCard({ cluster }: ClusterCardProps) {
  return (
    <div className="bg-[#111111] text-white p-6 space-y-4">
      <div className="text-xs uppercase tracking-[0.3em] text-white/60">
        {cluster.theme}
      </div>
      {cluster.summary && (
        <div className="text-sm text-white/60" title={cluster.summary}>
          {cluster.summary}
        </div>
      )}
      <div className="max-h-80 overflow-y-auto pr-2 space-y-2 thin-scrollbar">
        {cluster.items.map((item, index) => (
          <ClusterItem key={`${item.url}-${item.visit_time}-${index}`} item={item} />
        ))}
      </div>
    </div>
  );
}
