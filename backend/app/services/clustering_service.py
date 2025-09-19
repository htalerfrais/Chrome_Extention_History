import logging
from typing import List, Dict, Any
from collections import defaultdict, Counter
from datetime import datetime
import re
from urllib.parse import urlparse
import asyncio

from ..models.session_models import HistorySession, ClusterResult, ClusterItem, ClusteringPreview

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
                cluster_item = ClusterItem( # parsing a history session to an object with our model ClusterItem
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
                description=self._generate_description(theme, items),
                keywords=self._extract_keywords(theme, items),
                items=items,
                confidence_score=self._calculate_confidence(theme, items),
                session_ids=sessions_involved,
                total_items=len(items)
            )
            clusters.append(cluster)
        
        # Sort by confidence score
        clusters.sort(key=lambda x: x.confidence_score, reverse=True)
        
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
            else:
                # Fallback to domain-based grouping
                domain = urlparse(item.url).netloc
                theme_groups[f"Domain: {domain}"].append((item, session))
        
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

    def _generate_description(self, theme: str, items: List[ClusterItem]) -> str:
        """Generate a description for the cluster"""
        domains = Counter(urlparse(item.url).netloc for item in items)
        top_domain = domains.most_common(1)[0][0] if domains else "various sites"
        
        descriptions = {
            'Development': f"Programming and development activities on {top_domain} and related sites",
            'Social Media': f"Social media browsing and interaction on {top_domain}",
            'Shopping': f"Online shopping and product research on {top_domain}",
            'Learning': f"Educational content and learning resources from {top_domain}",
            'Entertainment': f"Entertainment and media consumption on {top_domain}",
            'News': f"News reading and current events from {top_domain}",
            'Productivity': f"Work and productivity tools usage on {top_domain}",
            'Research': f"Research and information gathering from {top_domain}",
        }
        
        return descriptions.get(theme, f"Browsing session focused on {theme.lower()} from {top_domain}")

    def _extract_keywords(self, theme: str, items: List[ClusterItem]) -> List[str]:
        """Extract relevant keywords for the cluster"""
        # Start with theme keywords
        keywords = set(self.theme_patterns.get(theme, []))
        
        # Add domain-specific keywords
        for item in items:
            domain = urlparse(item.url).netloc
            if domain in self.domain_keywords:
                keywords.update(self.domain_keywords[domain])
        
        # Extract from titles (simple approach)
        title_words = []
        for item in items:
            words = re.findall(r'\b\w{4,}\b', item.title.lower())
            title_words.extend(words)
        
        # Add most common title words
        common_title_words = [word for word, count in Counter(title_words).most_common(3)]
        keywords.update(common_title_words)
        
        return list(keywords)[:10]  # Limit to 10 keywords

    def _calculate_confidence(self, theme: str, items: List[ClusterItem]) -> float:
        """Calculate confidence score for the cluster"""
        if not items:
            return 0.0
        
        # Base confidence on theme detection strength
        total_score = 0
        for item in items:
            theme_scores = self._detect_themes(item)
            total_score += theme_scores.get(theme, 0)
        
        # Normalize by number of items
        avg_score = total_score / len(items)
        
        # Boost for larger clusters (more evidence)
        size_boost = min(len(items) / 10, 0.3)
        
        return min(avg_score + size_boost, 1.0)

    async def preview_sessions(self, sessions: List[HistorySession]) -> ClusteringPreview:
        """Generate a preview of sessions for debugging"""
        if not sessions:
            return ClusteringPreview(
                total_sessions=0,
                total_items=0,
                date_range={},
                top_domains=[],
                session_summary=[]
            )
        
        # Calculate totals
        total_items = sum(len(session.items) for session in sessions)
        
        # Date range
        all_times = []
        for session in sessions:
            all_times.append(session.start_time)
            all_times.append(session.end_time)
        
        date_range = {
            "start": min(all_times),
            "end": max(all_times)
        }
        
        # Top domains
        domain_counter = Counter()
        for session in sessions:
            for item in session.items:
                domain = urlparse(item.url).netloc
                domain_counter[domain] += 1
        
        top_domains = [
            {"domain": domain, "count": count}
            for domain, count in domain_counter.most_common(10)
        ]
        
        # Session summary
        session_summary = [
            {
                "session_id": session.session_id,
                "items_count": len(session.items),
                "duration_minutes": session.duration_minutes,
                "start_time": session.start_time,
                "top_domain": Counter(urlparse(item.url).netloc for item in session.items).most_common(1)[0][0] if session.items else "none"
            }
            for session in sessions[:5]  # Limit to first 5 sessions
        ]
        
        return ClusteringPreview(
            total_sessions=len(sessions),
            total_items=total_items,
            date_range=date_range,
            top_domains=top_domains,
            session_summary=session_summary
        )
