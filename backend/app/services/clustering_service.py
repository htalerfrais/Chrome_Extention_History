import logging
import os
import time
from typing import List, Dict, Any
from collections import defaultdict, Counter
from urllib.parse import urlparse
import asyncio
import re

from ..models.session_models import HistorySession, ClusterResult, ClusterItem, SessionClusteringResponse

logger = logging.getLogger(__name__)

class ClusteringService:
    """Service for clustering browsing history into thematic groups using BERTopic"""
    
    def __init__(self):
        # Lazy imports to avoid heavy startup costs if not used
        try:
            from bertopic import BERTopic  # type: ignore
            from sentence_transformers import SentenceTransformer  # type: ignore
            self._BERTopic = BERTopic
            self._SentenceTransformer = SentenceTransformer
        except Exception as e:
            logger.error(f"BERTopic dependencies not available: {e}")
            self._BERTopic = None
            self._SentenceTransformer = None
        
        # Configurable parameters via environment
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.min_topic_size = int(os.getenv("MIN_TOPIC_SIZE", "2"))
        self.nr_topics = os.getenv("NR_TOPICS", "auto")
        self.reduce_outliers = os.getenv("REDUCE_OUTLIERS", "true").lower() == "true"
        
        self.topic_model = None
        if self._BERTopic is not None and self._SentenceTransformer is not None:
            try:
                embeddings_model = self._SentenceTransformer(self.embedding_model_name)
                self.topic_model = self._BERTopic(
                    embedding_model=embeddings_model,
                    min_topic_size=self.min_topic_size,
                    nr_topics=self.nr_topics,
                    low_memory=True,
                    calculate_probabilities=True,
                    verbose=False,
                    hdbscan_model=None  # Use default clustering instead of HDBSCAN
                )
                logger.info(f"Initialized BERTopic with model {self.embedding_model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize BERTopic: {e}")
                self.topic_model = None

    async def cluster_sessions(self, sessions: List[HistorySession]) -> Dict[str, SessionClusteringResponse]:
        """
        Main clustering method - groups sessions by themes, processing each session independently
        
        Returns:
            Dict mapping session_id to SessionClusteringResponse
        """
        logger.info(f"Starting clustering for {len(sessions)} sessions")
        
        session_results = {}
        
        for session in sessions:
            logger.info(f"Processing session {session.session_id} with {len(session.items)} items")
            start_t = time.time()

            # Prepare documents and carry item references
            docs: List[str] = []
            item_refs: List[Any] = []
            for item in session.items:
                doc_text = self._build_doc_text(item)
                if not doc_text:
                    continue
                docs.append(doc_text)
                item_refs.append(item)

            clusters: List[ClusterResult] = []

            if self.topic_model is not None and len(docs) >= max(2, self.min_topic_size):
                try:
                    topics, probs = self.topic_model.fit_transform(docs)
                    # Collect items per topic (exclude -1 noise)
                    topic_to_indices: Dict[int, List[int]] = defaultdict(list)
                    for idx, t_id in enumerate(topics):
                        if t_id is not None and t_id >= 0:
                            topic_to_indices[t_id].append(idx)

                    # Build clusters from topics
                    for t_id, indices in topic_to_indices.items():
                        if len(indices) < 2:
                            continue
                        
                        cluster_items: List[ClusterItem] = []
                        for i in indices:
                            src = item_refs[i]
                            cluster_items.append(ClusterItem(
                                url=src.url,
                                title=src.title,
                                visit_time=src.visit_time,
                                session_id=session.session_id,
                                url_hostname=getattr(src, 'url_hostname', None),
                                url_pathname_clean=getattr(src, 'url_pathname_clean', None),
                                url_search_query=getattr(src, 'url_search_query', None)
                            ))
                        
                        # Generate label using actual page titles
                        label = self._get_topic_label_from_items(cluster_items)
                        
                        clusters.append(ClusterResult(
                            cluster_id=f"cluster_{session.session_id}_{t_id}",
                            theme=label,
                            items=cluster_items
                        ))
                except Exception as e:
                    logger.error(f"BERTopic failed for session {session.session_id}: {e}")

            # Fallback: simple grouping by hostname if no clusters
            if not clusters:
                logger.info(f"Falling back to hostname grouping for session {session.session_id}")
                clusters = self._fallback_group_by_hostname(session)

            # Sort clusters by theme name for consistent ordering
            clusters.sort(key=lambda x: x.theme)

            # Create session response
            session_response = SessionClusteringResponse(
                session_id=session.session_id,
                session_start_time=session.start_time,
                session_end_time=session.end_time,
                clusters=clusters
            )

            session_results[session.session_id] = session_response
            logger.info(f"Session {session.session_id}: generated {len(clusters)} clusters in {time.time()-start_t:.2f}s")
        
        logger.info(f"Generated clustering results for {len(session_results)} sessions")
        return session_results

    def _build_doc_text(self, item: Any) -> str:
        """Compose a robust document text from enriched fields for topic modeling."""
        parts: List[str] = []
        title = getattr(item, 'title', None) or ''
        search = getattr(item, 'url_search_query', None) or ''
        host = getattr(item, 'url_hostname', None) or ''
        path = getattr(item, 'url_pathname_clean', None) or ''
        
        # Prioritize meaningful content with context
        if title and len(title.strip()) > 3:
            parts.append(title)
        if search and len(search.strip()) > 2:
            parts.append(f"search: {search}")
        if host and host not in ['www.google.com', 'www.youtube.com']:  # Skip generic domains
            parts.append(f"site: {host}")
        if path and path != '/' and len(path.split('/')) > 2:  # Only meaningful paths
            path_clean = path.replace('/', ' ').replace('_', ' ').replace('-', ' ')
            parts.append(f"section: {path_clean}")
        
        doc = ' '.join(parts).strip().lower()
        return doc

    def _get_topic_label_from_items(self, items: List[ClusterItem]) -> str:
        """Generate label based on actual page titles and content in the cluster"""
        if not items:
            return "Unknown Topic"
        
        # Extract titles and search queries
        titles = [item.title for item in items if item.title and len(item.title.strip()) > 3]
        searches = [item.url_search_query for item in items if item.url_search_query and len(item.url_search_query.strip()) > 2]
        hosts = [item.url_hostname for item in items if item.url_hostname]
        
        # Strategy 1: Use search queries if available (most descriptive)
        if searches:
            # Find most common search terms
            all_search_words = []
            for search in searches:
                words = re.findall(r'\b\w+\b', search.lower())
                all_search_words.extend([w for w in words if len(w) > 2])
            
            if all_search_words:
                word_counts = Counter(all_search_words)
                common_words = [w for w, count in word_counts.most_common(3) if count > 1]
                if common_words:
                    return f"Recherche: {' '.join(common_words).title()}"
                else:
                    return f"Recherche: {searches[0].title()}"
        
        # Strategy 2: Use titles to find common themes
        if titles:
            # Extract meaningful words from titles
            all_title_words = []
            for title in titles:
                # Remove common suffixes and clean
                clean_title = re.sub(r'\s*-\s*(Recherche|Search|YouTube|Google).*$', '', title, flags=re.IGNORECASE)
                words = re.findall(r'\b\w+\b', clean_title.lower())
                all_title_words.extend([w for w in words if len(w) > 2 and w not in ['the', 'and', 'for', 'with', 'from', 'page']])
            
            if all_title_words:
                word_counts = Counter(all_title_words)
                common_words = [w for w, count in word_counts.most_common(3) if count > 1]
                if common_words:
                    return ' '.join(common_words).title()
                else:
                    # Use the first meaningful title
                    first_title = titles[0]
                    clean_title = re.sub(r'\s*-\s*(Recherche|Search|YouTube|Google).*$', '', first_title, flags=re.IGNORECASE)
                    return clean_title[:30] + "..." if len(clean_title) > 30 else clean_title
        
        # Strategy 3: Use hostname as fallback
        if hosts:
            host_counts = Counter(hosts)
            primary_host = host_counts.most_common(1)[0][0]
            clean_host = primary_host.replace('www.', '').replace('.com', '').replace('.fr', '').replace('.org', '')
            return f"{clean_host.title()}"
        
        # Strategy 4: Generic fallback
        return f"Cluster {len(items)} items"

    def _get_topic_label(self, topic_id: int) -> str:
        """Legacy method - kept for compatibility but not used"""
        if self.topic_model is None:
            return f"Topic {topic_id}"
        try:
            info = self.topic_model.get_topic(topic_id)
            # info is a list of (word, weight); build a simple label
            if not info:
                return f"Topic {topic_id}"
            top_words = [w for (w, _) in info[:3]]
            return ' / '.join(top_words)
        except Exception:
            return f"Topic {topic_id}"

    def _fallback_group_by_hostname(self, session: HistorySession) -> List[ClusterResult]:
        groups: Dict[str, List[ClusterItem]] = defaultdict(list)
        for src in session.items:
            host = getattr(src, 'url_hostname', None) or urlparse(src.url).netloc
            groups[host].append(ClusterItem(
                url=src.url,
                title=src.title,
                visit_time=src.visit_time,
                session_id=session.session_id,
                url_hostname=getattr(src, 'url_hostname', None),
                url_pathname_clean=getattr(src, 'url_pathname_clean', None),
                url_search_query=getattr(src, 'url_search_query', None)
            ))
        clusters: List[ClusterResult] = []
        for host, items in groups.items():
            if len(items) < 2:
                continue
            
            # Use the new label generation method for fallback too
            label = self._get_topic_label_from_items(items)
            
            clusters.append(ClusterResult(
                cluster_id=f"cluster_{session.session_id}_{host}",
                theme=label,
                items=items
            ))
        return clusters