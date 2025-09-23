// ClusterItem component - displays individual history items
// Shows favicon, title, URL, and visit time for each browsing history item

interface HistoryItem {
  url: string;
  title: string;
  visit_time: string;
}

interface ClusterItemProps {
  item: HistoryItem;
}

export default function ClusterItem({ item }: ClusterItemProps) {
  const getDomain = (url: string): string => {
    try {
      return new URL(url).hostname;
    } catch {
      return url;
    }
  };

  const getFaviconUrl = (url: string): string => {
    const domain = getDomain(url);
    return `https://www.google.com/s2/favicons?domain=${domain}`;
  };

  const formatVisitTime = (visitTime: string): string => {
    return new Date(visitTime).toLocaleDateString();
  };

  const domain = getDomain(item.url);
  const faviconUrl = getFaviconUrl(item.url);
  const visitTime = formatVisitTime(item.visit_time);

  return (
    <div className="cluster-item">
      <img
        src={faviconUrl}
        alt=""
        className="item-favicon"
        onError={(e) => {
          (e.target as HTMLImageElement).style.display = 'none';
        }}
      />
      <div className="item-content">
        <div className="item-title" title={item.title}>
          {item.title}
        </div>
        <div className="item-url" title={domain}>
          {domain}
        </div>
      </div>
      <div className="item-time">
        {visitTime}
      </div>
    </div>
  );
}
