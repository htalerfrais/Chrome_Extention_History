import { useState } from 'react';

interface HistoryItem {
  url: string;
  title: string;
  visit_time: string;
}

interface ClusterItemProps {
  item: HistoryItem;
}

export default function ClusterItem({ item }: ClusterItemProps) {
  const [currentFaviconIndex, setCurrentFaviconIndex] = useState(0);
  const [showFallback, setShowFallback] = useState(false);

  const getDomain = (url: string): string => {
    try {
      // Handle special cases - files and local pages
      if (url === 'about:blank' || 
          url.startsWith('chrome-extension://') || 
          url.startsWith('moz-extension://') ||
          url.startsWith('file://') ||
          url.includes('.pdf') ||
          url.includes('.png') ||
          url.includes('.jpg') ||
          url.includes('.jpeg') ||
          url.includes('.doc') ||
          url.includes('.docx')) {
        return 'local-file';
      }
      
      const urlObj = new URL(url);
      return urlObj.hostname;
    } catch {
      // If URL parsing fails, try to extract domain manually
      if (url.includes('://')) {
        const parts = url.split('://')[1];
        return parts.split('/')[0];
      }
      return 'unknown';
    }
  };


  const getAlternativeFaviconUrls = (url: string): string[] => {
    const domain = getDomain(url);
    
    // Skip favicon URLs for special cases (local files, extensions, etc.)
    if (domain === 'local-file' || domain === 'unknown' || domain === '') {
      return [];
    }
    
    return [
      `https://www.google.com/s2/favicons?domain=${domain}&sz=32`,
      `https://favicon.io/favicon/${domain}`,
      `https://icons.duckduckgo.com/ip3/${domain}.ico`,
      `https://${domain}/favicon.ico`,
      `https://${domain}/apple-touch-icon.png`,
      `https://${domain}/apple-touch-icon-precomposed.png`
    ];
  };

  const formatVisitTime = (visitTime: string): string => {
    return new Date(visitTime).toLocaleDateString();
  };

  const handleOpenUrl = (event: React.MouseEvent) => {
    event.stopPropagation();
    if (item.url) {
      chrome.tabs.create({ url: item.url });
    }
  };

  const handleFaviconError = () => {
    console.log(`Favicon failed for ${item.title}, trying next source...`);
    const alternativeUrls = getAlternativeFaviconUrls(item.url);
    if (currentFaviconIndex < alternativeUrls.length - 1) {
      setCurrentFaviconIndex(currentFaviconIndex + 1);
    } else {
      console.log(`All favicon sources failed for ${item.title}, showing initials: ${getInitials(item.title)}`);
      setShowFallback(true);
    }
  };

  const getInitials = (title: string): string => {
    // Handle special cases for local files
    if (title === 'about:blank') return 'AB';
    if (title.includes('.pdf')) return 'PDF';
    if (title.includes('.png') || title.includes('.jpg') || title.includes('.jpeg')) return 'IMG';
    if (title.includes('.doc') || title.includes('.docx')) return 'DOC';
    if (title.includes('.xls') || title.includes('.xlsx')) return 'XLS';
    
    return title
      .split(' ')
      .slice(0, 2)
      .map(word => word.charAt(0).toUpperCase())
      .join('')
      .substring(0, 2);
  };

  const domain = getDomain(item.url);
  const alternativeUrls = getAlternativeFaviconUrls(item.url);
  const currentFaviconUrl = alternativeUrls[currentFaviconIndex];
  const visitTime = formatVisitTime(item.visit_time);

  // For special cases (local files, about:blank, etc.), show fallback immediately
  const shouldShowFallback = showFallback || alternativeUrls.length === 0;

  return (
    <div className="flex items-center gap-3 py-2">
      {!shouldShowFallback ? (
        <img
          src={currentFaviconUrl}
          alt=""
          className="w-5 h-5"
          onError={handleFaviconError}
        />
      ) : (
        <div className="w-5 h-5 text-[10px] font-semibold bg-white text-black flex items-center justify-center">
          {getInitials(item.title)}
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="text-sm text-white truncate" title={item.title}>
          {item.title}
        </div>
        <div className="text-xs text-white/50 truncate" title={domain}>
          {domain}
        </div>
      </div>
      <div className="text-xs text-white/50">
        {visitTime}
      </div>
      <button 
        className="text-white/60 hover:text-white"
        onClick={handleOpenUrl}
        title="Ouvrir dans un nouvel onglet"
      >
        ↗
      </button>
    </div>
  );
}
