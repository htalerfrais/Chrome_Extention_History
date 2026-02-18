from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from app.models.session_models import SessionClusteringResponse, ClusterResult, ClusterItem
from app.repositories.database_repository import DatabaseRepository
from app.monitoring import get_request_id

logger = logging.getLogger(__name__)


class MappingService:
    """Service for converting between Pydantic and database models"""
    
    def __init__(self, db_repository: DatabaseRepository):
        self.db_repository = db_repository
    
    def save_clustering_result(
        self,
        user_id: int,
        response: SessionClusteringResponse,
        replace_if_exists: bool = False
    ) -> int:
        total_items = sum(len(c.items) for c in response.clusters)
        
        logger.info(
            "mapping_save_start",
            extra={
                "request_id": get_request_id(),
                "session_id": response.session_identifier,
                "replace_existing": replace_if_exists,
                "clusters_to_save": len(response.clusters),
                "total_items": total_items
            }
        )
        
        if replace_if_exists:
            existing = self.db_repository.get_session_by_identifier(response.session_identifier)
            if existing:
                self.db_repository.delete_session_by_identifier(response.session_identifier)
                logger.info(
                    "mapping_deleted_existing",
                    extra={
                        "request_id": get_request_id(),
                        "session_id": response.session_identifier
                    }
                )

        # Create Session record
        session_dict = self.db_repository.create_session(
            user_id=user_id,
            session_identifier=response.session_identifier,
            start_time=response.session_start_time,
            end_time=response.session_end_time
        )
        
        if not session_dict:
            raise ValueError("Failed to create session record")
        
        session_id = session_dict["id"]
        
        for cluster in response.clusters:
            cluster_dict = self.db_repository.create_cluster(
                session_id=session_id,
                name=cluster.theme,
                description=cluster.summary,
                embedding=cluster.embedding or None
            )
            
            if not cluster_dict:
                logger.warning(f"Failed to create cluster: {cluster.theme}")
                continue
            
            cluster_id = cluster_dict["id"]
            
            # Create HistoryItem records for this cluster
            for item in cluster.items:
                self.db_repository.create_history_item(
                    cluster_id=cluster_id,
                    url=item.url,
                    title=item.title,
                    domain=item.url_hostname,
                    visit_time=item.visit_time,
                    raw_semantics={
                        "url_pathname_clean": item.url_pathname_clean,
                        "url_search_query": item.url_search_query
                    },
                    embedding=item.embedding or None
                )
        
        logger.info(
            "mapping_save_complete",
            extra={
                "request_id": get_request_id(),
                "session_id": response.session_identifier,
                "db_session_id": session_id,
                "clusters_saved": len(response.clusters),
                "items_saved": total_items
            }
        )
        return session_id
    
    def get_clustering_result(
        self, 
        session_identifier: str
    ) -> Optional[SessionClusteringResponse]:
        # Get session with all relations
        session_dict = self.db_repository.get_session_with_relations(session_identifier)
        
        if not session_dict:
            logger.info(
                "mapping_cache_lookup",
                extra={
                    "request_id": get_request_id(),
                    "session_id": session_identifier,
                    "found": False
                }
            )
            return None
        
        # Get clusters for this session
        clusters_dict = self.db_repository.get_clusters_by_session_id(session_dict["id"])
        
        if not clusters_dict:
            logger.info(f"❌ No clusters found for session {session_identifier}")
            return None
        
        cluster_results: List[ClusterResult] = []
        
        for cluster_dict in clusters_dict:
            cluster_id = cluster_dict["id"]
            
            # Get history items for this cluster
            items_dict = self.db_repository.get_history_items_by_cluster_id(cluster_id)
            
            if not items_dict:
                logger.warning(f"No items found for cluster {cluster_id}")
                continue
            
            cluster_items: List[ClusterItem] = []
            for item_dict in items_dict:
                raw_semantics = item_dict.get("raw_semantics") or {}
                
                cluster_item = ClusterItem(
                    url=item_dict["url"],
                    title=item_dict.get("title") or "Untitled",
                    visit_time=item_dict["visit_time"],
                    url_hostname=item_dict.get("domain"),
                    url_pathname_clean=raw_semantics.get("url_pathname_clean"),
                url_search_query=raw_semantics.get("url_search_query"),
                embedding=item_dict.get("embedding")
                )
                cluster_items.append(cluster_item)
            
            # Create ClusterResult
            cluster_result = ClusterResult(
                cluster_id=f"cluster_{cluster_id}",  # Generate simple cluster_id
                theme=cluster_dict["name"],
                summary=cluster_dict.get("description") or "",
            items=cluster_items,
            embedding=cluster_dict.get("embedding")
            )
            cluster_results.append(cluster_result)
        
        if not cluster_results:
            logger.info(
                "mapping_cache_lookup",
                extra={
                    "request_id": get_request_id(),
                    "session_id": session_identifier,
                    "found": False,
                    "reason": "no_valid_clusters"
                }
            )
            return None
        
        response = SessionClusteringResponse(
            session_identifier=session_dict["session_identifier"],
            session_start_time=session_dict["start_time"],
            session_end_time=session_dict["end_time"],
            clusters=cluster_results
        )
        
        logger.info(
            "mapping_cache_lookup",
            extra={
                "request_id": get_request_id(),
                "session_id": session_identifier,
                "found": True,
                "clusters_count": len(cluster_results),
                "total_items": sum(len(c.items) for c in cluster_results)
            }
        )
        return response

