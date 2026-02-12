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
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <h3 className="text-base font-semibold text-text leading-snug">
          {cluster.theme}
        </h3>
        {cluster.summary && (
          <p className="text-sm text-text-secondary leading-relaxed">{cluster.summary}</p>
        )}
      </div>

      {/* Count badge */}
      <div className="flex items-center gap-2">
        <span className="text-xxs font-medium text-accent-hover bg-accent-subtle px-2.5 py-1 rounded">
          {cluster.items.length} page{cluster.items.length !== 1 ? 's' : ''} visited
        </span>
      </div>

      {/* Items list */}
      <div className="space-y-0.5">
        {cluster.items.map((item, index) => (
          <ClusterItem key={`${item.url}-${item.visit_time}-${index}`} item={item} />
        ))}
      </div>
    </div>
  );
}
