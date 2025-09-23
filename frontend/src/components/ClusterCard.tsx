// ClusterCard component - displays individual clusters
// Shows cluster theme and its associated history items

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
    <div className="cluster-card">
      <div className="cluster-theme">
        {cluster.theme}
      </div>
      {cluster.summary && (
        <div className="cluster-summary" title={cluster.summary}>
          {cluster.summary}
        </div>
      )}
      <div className="cluster-items">
        {cluster.items.map((item, index) => (
          <ClusterItem key={`${item.url}-${item.visit_time}-${index}`} item={item} />
        ))}
      </div>
    </div>
  );
}
