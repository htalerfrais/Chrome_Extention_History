import logging
from typing import List, Tuple, Optional, Dict

from app.config import settings
from app.repositories.database_repository import DatabaseRepository
from app.services.embedding_service import EmbeddingService
from app.models.session_models import ClusterResult, ClusterItem
from app.models.chat_models import SearchFilters


logger = logging.getLogger(__name__)


class SearchService:
    # Two-stage semantic search over clusters and history items."""

    def __init__(
        self,
        db_repository: DatabaseRepository,
        embedding_service: EmbeddingService,
    ) -> None:
        self.db_repository = db_repository
        self.embedding_service = embedding_service

    async def search(
        self,
        user_id: int,
        filters: SearchFilters,
        limit_clusters: int = settings.search_limit_clusters,
        limit_items_per_cluster: int = settings.search_limit_items_per_cluster,
    ) -> Tuple[List[ClusterResult], List[ClusterItem]]:
        """Search clusters and items matching the query and filters for a given user.
        
        Args:
            limit_items_per_cluster: Max items retrieved per cluster (ensures inter-cluster diversity)
        """
        query = (filters.query_text or "").strip()
        
        # Treat "*" as empty query (wildcard means "all", not a literal search)
        if query == "*":
            query = ""
        
        # Generate embedding only if meaningful query_text is provided
        query_embedding = None
        if query:
            embeddings = await self.embedding_service.embed_texts([query])
            if embeddings and embeddings[0]:
                query_embedding = embeddings[0]
            else:
                logger.warning("SearchService: embedding generation failed")
        
        # Check if we have at least query or filters
        has_query = bool(query_embedding)
        has_filters = any([
            filters.date_from,
            filters.date_to,
            filters.title_contains,
            filters.domain_contains
        ])
        
        if not has_query and not has_filters:
            logger.info("SearchService: no query and no filters, returning no results")
            return [], []
        
        # Search clusters (only if we have an embedding or date filters)
        cluster_dicts = []
        if query_embedding or filters.date_from or filters.date_to:
            cluster_dicts = self.db_repository.search_clusters_by_embedding(
                user_id=user_id,
                query_embedding=query_embedding,
                limit=limit_clusters,
                date_from=filters.date_from,
                date_to=filters.date_to,
            )
        clusters = [self._dict_to_cluster_result(cluster_dict) for cluster_dict in cluster_dicts]

        cluster_ids = [cluster_dict.get("id") for cluster_dict in cluster_dicts if cluster_dict.get("id") is not None]

        # Over-fetch to allow deduplication while still returning enough diverse items
        fetch_limit = limit_items_per_cluster * settings.search_overfetch_multiplier

        # Search items per cluster (over-fetch, then deduplicate for diversity)
        all_item_dicts = []
        if cluster_ids:
            for cluster_id in cluster_ids:
                cluster_item_dicts = self.db_repository.search_history_items_by_embedding(
                    user_id=user_id,
                    query_embedding=query_embedding,
                    cluster_ids=[cluster_id],
                    limit=fetch_limit,
                    date_from=filters.date_from,
                    date_to=filters.date_to,
                    title_contains=filters.title_contains,
                    domain_contains=filters.domain_contains,
                )
                # Deduplicate within this cluster's results
                cluster_item_dicts = self._deduplicate_item_dicts(
                    cluster_item_dicts, limit_items_per_cluster
                )
                all_item_dicts.extend(cluster_item_dicts)
        else:
            # No clusters found, search all items with fallback limit
            fallback_limit = limit_items_per_cluster * limit_clusters
            all_item_dicts = self.db_repository.search_history_items_by_embedding(
                user_id=user_id,
                query_embedding=query_embedding,
                cluster_ids=None,
                limit=fallback_limit * settings.search_overfetch_multiplier,
                date_from=filters.date_from,
                date_to=filters.date_to,
                title_contains=filters.title_contains,
                domain_contains=filters.domain_contains,
            )
            all_item_dicts = self._deduplicate_item_dicts(all_item_dicts, fallback_limit)
        
        items = [self._dict_to_cluster_item(item_dict) for item_dict in all_item_dicts]

        logger.info(
            "SearchService: search completed (clusters=%s, items=%s, limit_per_cluster=%s)",
            len(clusters),
            len(items),
            limit_items_per_cluster,
        )

        return clusters, items

    def _deduplicate_item_dicts(
        self, item_dicts: List[Dict], limit: int
    ) -> List[Dict]:
        """Keep at most one item per (title, domain) group, preserving DB order (relevance).
        
        Items from the same semantic group share the same title and domain,
        so this effectively picks one representative per group. The first
        occurrence wins (most relevant, since DB results are sorted by
        cosine distance or visit_time).
        """
        seen: set = set()
        result: List[Dict] = []

        for item in item_dicts:
            key = (
                (item.get("title") or "").strip().lower(),
                (item.get("domain") or "").strip().lower(),
            )
            if key in seen:
                continue
            seen.add(key)
            result.append(item)
            if len(result) >= limit:
                break

        return result

    def _dict_to_cluster_result(self, cluster_dict: dict) -> ClusterResult:
        cluster_id = cluster_dict.get("id")
        cluster_identifier = f"cluster_{cluster_id}" if cluster_id is not None else "cluster_unknown"

        return ClusterResult(
            cluster_id=cluster_identifier,
            theme=cluster_dict.get("name") or "Untitled",
            summary=cluster_dict.get("description") or "",
            items=[],
            embedding=cluster_dict.get("embedding"),
        )

    def _dict_to_cluster_item(self, item_dict: dict) -> ClusterItem:
        raw_semantics = item_dict.get("raw_semantics") or {}

        return ClusterItem(
            url=item_dict.get("url") or "",
            title=item_dict.get("title") or "Untitled",
            visit_time=item_dict.get("visit_time"),
            url_hostname=item_dict.get("domain"),
            url_pathname_clean=raw_semantics.get("url_pathname_clean"),
            url_search_query=raw_semantics.get("url_search_query"),
            embedding=item_dict.get("embedding"),
        )


