import logging
import os
import time
from typing import List, Dict, Any
from collections import defaultdict
from urllib.parse import urlparse
import asyncio

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
                    verbose=False
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
                        label = self._get_topic_label(t_id)
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
        if title:
            parts.append(title)
        if search:
            parts.append(search)
        if host:
            parts.append(host)
        if path and path != '/':
            parts.append(path.replace('/', ' '))
        doc = ' '.join(parts).strip().lower()
        return doc

    def _get_topic_label(self, topic_id: int) -> str:
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
            clusters.append(ClusterResult(
                cluster_id=f"cluster_{session.session_id}_{host}",
                theme=host,
                items=items
            ))
        return clusters


