import logging
from typing import List, Dict, Any
from collections import defaultdict, Counter
from datetime import datetime
import re
from urllib.parse import urlparse
import asyncio

from ..models.session_models import HistorySession, ClusterResult, ClusterItem

logger = logging.getLogger(__name__)

class ClusteringService:
    """Service for clustering browsing history into thematic groups"""
    
    def __init__(self):
        self.domain_keywords = {
            'github.com': ['code', 'development', 'programming', 'repository'],
            'stackoverflow.com': ['programming', 'development', 'questions', 'coding'],
            'youtube.com': ['video', 'entertainment', 'learning', 'tutorial'],
            'reddit.com': ['discussion', 'community', 'social', 'forum'],
            'linkedin.com': ['professional', 'career', 'networking', 'business'],
            'twitter.com': ['social', 'news', 'updates', 'microblogging'],
            'medium.com': ['articles', 'blog', 'writing', 'learning'],
            'docs.google.com': ['documents', 'productivity', 'collaboration'],
            'gmail.com': ['email', 'communication', 'productivity'],
            'amazon.com': ['shopping', 'ecommerce', 'products'],
        }
        
        self.theme_patterns = {
            'Development': ['github', 'stackoverflow', 'code', 'programming', 'api', 'documentation', 'tutorial'],
            'Social Media': ['twitter', 'facebook', 'instagram', 'reddit', 'social'],
            'Shopping': ['amazon', 'shop', 'buy', 'store', 'product', 'cart'],
            'Learning': ['course', 'tutorial', 'learn', 'education', 'university', 'study'],
            'Entertainment': ['youtube', 'netflix', 'movie', 'video', 'game', 'music'],
            'News': ['news', 'article', 'breaking', 'politics', 'world'],
            'Productivity': ['docs', 'drive', 'calendar', 'email', 'office', 'work'],
            'Research': ['wiki', 'research', 'academic', 'paper', 'study'],
        }

    async def cluster_sessions(self, sessions: List[HistorySession]) -> List[ClusterResult]:
        """
        Main clustering method - groups sessions by themes
        """
        logger.info(f"Starting clustering for {len(sessions)} sessions")
        
        # Extract all items with metadata
        all_items = []
        for session in sessions:
            for item in session.items:
                cluster_item = ClusterItem(
                    url=item.url,
                    title=item.title,
                    visit_time=item.visit_time,
                    session_id=session.session_id
                )
                all_items.append((cluster_item, session))
        
        # Group items by detected themes
        theme_groups = self._group_by_themes(all_items)
        
        # Convert to cluster results
        clusters = []
        for theme, items_data in theme_groups.items():
            if len(items_data) < 2:  # Skip single-item clusters
                continue
                
            items = [item for item, _ in items_data]
            sessions_involved = list(set(session.session_id for _, session in items_data))
            
            cluster = ClusterResult(
                cluster_id=f"cluster_{theme.lower().replace(' ', '_')}_{len(clusters)}",
                theme=theme,
                items=items
            )
            clusters.append(cluster)
        
        # Sort by theme name for consistent ordering
        clusters.sort(key=lambda x: x.theme)
        
        logger.info(f"Generated {len(clusters)} clusters")
        return clusters

    def _group_by_themes(self, items_data: List[tuple]) -> Dict[str, List[tuple]]:
        """Group items by detected themes"""
        theme_groups = defaultdict(list)
        
        for item, session in items_data:
            detected_themes = self._detect_themes(item)
            
            # Assign to primary theme (highest scoring)
            if detected_themes:
                primary_theme = max(detected_themes.items(), key=lambda x: x[1])[0]
                theme_groups[primary_theme].append((item, session))
            # Skip items that can't be categorized into proper themes
        
        return dict(theme_groups)

    def _detect_themes(self, item: ClusterItem) -> Dict[str, float]:
        """Detect themes for a single item based on URL and title"""
        themes = {}
        
        # Analyze URL and title
        text = f"{item.url} {item.title}".lower()
        domain = urlparse(item.url).netloc
        
        # Check theme patterns
        for theme, keywords in self.theme_patterns.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    score += 1
            
            # Domain-specific boost
            if domain in self.domain_keywords:
                domain_kws = self.domain_keywords[domain]
                for kw in domain_kws:
                    if any(theme_kw in kw or kw in theme_kw for theme_kw in keywords):
                        score += 2
            
            if score > 0:
                themes[theme] = score / len(keywords)  # Normalize
        
        return themes


