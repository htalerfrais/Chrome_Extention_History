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

interface ClusterDetailProps {
  cluster: Cluster;
}

export default function ClusterDetail({ cluster }: ClusterDetailProps) {
  return (
    <div className="p-6 space-y-4">
      <div>
        <h3 className="text-xs uppercase tracking-[0.3em] text-white/60">
          {cluster.theme}
        </h3>
        {cluster.summary && (
          <p className="text-sm text-white/50 mt-2">{cluster.summary}</p>
        )}
      </div>

      <div className="text-[10px] uppercase tracking-[0.2em] text-white/30">
        {cluster.items.length} page{cluster.items.length !== 1 ? 's' : ''} visited
      </div>

      <div className="space-y-1 divide-y divide-white/5">
        {cluster.items.map((item, index) => (
          <ClusterItem key={`${item.url}-${item.visit_time}-${index}`} item={item} />
        ))}
      </div>
    </div>
  );
}
