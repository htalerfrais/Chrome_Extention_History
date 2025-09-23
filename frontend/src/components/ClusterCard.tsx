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
  items: HistoryItem[];
}

interface ClusterCardProps {
  cluster: Cluster;
  maxItemsDisplay?: number;
}

export default function ClusterCard({ cluster, maxItemsDisplay = 5 }: ClusterCardProps) {
  const displayedItems = cluster.items.slice(0, maxItemsDisplay);
  const remainingCount = cluster.items.length - maxItemsDisplay;

  return (
    <div className="cluster-card">
      <div className="cluster-theme">
        {cluster.theme}
      </div>
      <div className="cluster-items">
        {displayedItems.map((item, index) => (
          <ClusterItem key={`${item.url}-${item.visit_time}-${index}`} item={item} />
        ))}
        {remainingCount > 0 && (
          <div className="item-more">
            +{remainingCount} more items
          </div>
        )}
      </div>
    </div>
  );
}
