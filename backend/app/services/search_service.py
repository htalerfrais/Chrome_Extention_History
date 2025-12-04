import logging
from typing import List, Tuple

from app.repositories.database_repository import DatabaseRepository
from app.services.embedding_service import EmbeddingService
from app.models.session_models import ClusterResult, ClusterItem


logger = logging.getLogger(__name__)


class SearchService:
    """Two-stage semantic search over clusters and history items."""

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
        query_text: str,
        limit_clusters: int = 5,
        limit_items: int = 20,
    ) -> Tuple[List[ClusterResult], List[ClusterItem]]:
        """Search clusters and items matching the query for a given user."""
        query = (query_text or "").strip()
        if not query:
            logger.info("SearchService: empty query, returning no results")
            return [], []

        embeddings = await self.embedding_service.embed_texts([query])
        if not embeddings or not embeddings[0]:
            logger.warning("SearchService: embedding generation failed, returning empty results")
            return [], []

        query_embedding = embeddings[0]

        cluster_dicts = self.db_repository.search_clusters_by_embedding(
            user_id=user_id,
            query_embedding=query_embedding,
            limit=limit_clusters,
        )
        clusters = [self._dict_to_cluster_result(cluster_dict) for cluster_dict in cluster_dicts]

        cluster_ids = [cluster_dict.get("id") for cluster_dict in cluster_dicts if cluster_dict.get("id") is not None]

        item_dicts = self.db_repository.search_history_items_by_embedding(
            user_id=user_id,
            query_embedding=query_embedding,
            cluster_ids=cluster_ids or None,
            limit=limit_items,
        )
        items = [self._dict_to_cluster_item(item_dict) for item_dict in item_dicts]

        logger.info(
            "SearchService: search completed (clusters=%s, items=%s)",
            len(clusters),
            len(items),
        )

        return clusters, items

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


