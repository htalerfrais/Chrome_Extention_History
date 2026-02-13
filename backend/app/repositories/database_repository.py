from typing import Optional, Callable, Any, Dict, List
from datetime import datetime
import logging
import time
from contextlib import contextmanager

from app.database import SessionLocal
from app.models.database_models import User, Session, Cluster, HistoryItem
from app.monitoring import get_request_id

logger = logging.getLogger(__name__)


class DatabaseRepository:
    
    @contextmanager
    def _get_session(self):
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def _execute(self, operation: Callable, error_msg: str = "Operation failed") -> Optional[Any]:
        """
        Generic database operation wrapper
        Handles session lifecycle, commits, rollbacks, and error logging
        Returns dictionary, list, or primitive types to avoid SQLAlchemy session dependencies
        """
        try:
            with self._get_session() as db:
                result = operation(db)
                if result is None:
                    return None
                
                if isinstance(result, (bool, int, str, float)):
                    return result
                
                # Handle lists of SQLAlchemy objects
                if isinstance(result, list):
                    return [self._to_dict(obj) if hasattr(obj, '__table__') else obj for obj in result]
                
                return self._to_dict(result) if hasattr(result, '__table__') else result
            
        except Exception as e:
            logger.error(f"❌ {error_msg}: {e}")
            return None
    
    def _to_dict(self, obj) -> Dict:
        """Convert SQLAlchemy object to dictionary"""
        if obj is None:
            return None
        
        result = {}
        for column in obj.__table__.columns:
            value = getattr(obj, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
    
    # User operations
    
    def get_user_by_google_id(self, google_user_id: str) -> Optional[Dict]:
        """Get existing user by stable Google user id"""
        def operation(db):
            user = db.query(User).filter(User.google_user_id == google_user_id).first()
            return user
        return self._execute(operation, "Get user by google_user_id failed")

    def get_or_create_user_by_google_id(self, google_user_id: str, token: Optional[str] = None) -> Optional[Dict]:
        def operation(db):
            user = db.query(User).filter(User.google_user_id == google_user_id).first()
            if user:
                # Update token if changed
                if token and user.token != token:
                    user.token = token
                    db.add(user)
                return user
            user = User(google_user_id=google_user_id, token=token)
            db.add(user)
            db.flush()
            db.refresh(user)
            logger.info(f"✅ Created user ID: {user.id} (google_user_id={google_user_id})")
            return user
        return self._execute(operation, "User operation failed")
    
    def get_session_by_identifier(self, session_identifier: str) -> Optional[Dict]:
        def operation(db):
            session = db.query(Session).filter(Session.session_identifier == session_identifier).first()
            return session
        
        return self._execute(operation, "Failed to get session by identifier")
    
    def create_session(
        self,
        user_id: int,
        session_identifier: str,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[Dict]:
        """Create a new browsing session"""
        def operation(db):
            session = Session(
                user_id=user_id,
                session_identifier=session_identifier,
                start_time=start_time,
                end_time=end_time
            )
            db.add(session)
            db.flush()
            db.refresh(session)
            logger.info(f"✅ Created session ID: {session.id}, identifier: {session.session_identifier}")
            return session
        
        return self._execute(operation, "Failed to create session")
    
    def create_cluster(
        self,
        session_id: int,
        name: str,
        description: Optional[str] = None,
        embedding: Optional[list] = None
    ) -> Optional[Dict]:
        def operation(db):
            cluster = Cluster(
                session_id=session_id,
                name=name,
                description=description,
                embedding=embedding
            )
            db.add(cluster)
            db.flush()
            db.refresh(cluster)
            logger.info(f"✅ Created cluster ID: {cluster.id}")
            return cluster
        
        return self._execute(operation, "Failed to create cluster")
    
    def get_clusters_by_session_id(self, session_id: int) -> List[Dict]:
        """Get all clusters for a session"""
        def operation(db):
            return db.query(Cluster).filter(Cluster.session_id == session_id).all()
        
        result = self._execute(operation, "Failed to get clusters by session id")
        return result if isinstance(result, list) else []
    
    def get_history_items_by_cluster_id(self, cluster_id: int) -> List[Dict]:
        def operation(db):
            return db.query(HistoryItem).filter(HistoryItem.cluster_id == cluster_id).all()
        
        result = self._execute(operation, "Failed to get history items by cluster id")
        return result if isinstance(result, list) else []
    
    def search_clusters_by_embedding(
        self,
        user_id: int,
        query_embedding: Optional[List[float]],
        limit: int = 5,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[Dict]:
        """Semantic search clusters for a user using cosine distance with optional date filters."""
        # Need at least embedding or date filters
        if not query_embedding and not date_from and not date_to:
            return []

        start = time.perf_counter()

        def operation(db):
            query = (
                db.query(Cluster)
                .join(Session)
                .filter(Session.user_id == user_id)
            )
            
            if date_from:
                query = query.filter(Session.end_time >= date_from)
            if date_to:
                query = query.filter(Session.start_time <= date_to)
            
            # Order by embedding similarity if provided, otherwise by session time desc
            if query_embedding:
                query = query.filter(Cluster.embedding.isnot(None))
                query = query.order_by(Cluster.embedding.cosine_distance(query_embedding))
            else:
                query = query.order_by(Session.start_time.desc())
            
            query = query.limit(limit)
            return query.all()

        result = self._execute(operation, "Failed to search clusters by embedding")
        duration_ms = (time.perf_counter() - start) * 1000
        
        results_count = len(result) if isinstance(result, list) else 0
        logger.info(
            "db_search_clusters",
            extra={
                "request_id": get_request_id(),
                "limit": limit,
                "has_embedding": query_embedding is not None,
                "has_date_filters": date_from is not None or date_to is not None,
                "results_count": results_count,
                "duration_ms": round(duration_ms, 2)
            }
        )
        
        return result if isinstance(result, list) else []

    def search_history_items_by_embedding(
        self,
        user_id: int,
        query_embedding: Optional[List[float]],
        cluster_ids: Optional[List[int]] = None,
        limit: int = 20,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        title_contains: Optional[str] = None,
        domain_contains: Optional[str] = None,
    ) -> List[Dict]:
        start = time.perf_counter()
        
        def operation(db):
            query = (
                db.query(HistoryItem)
                .join(Cluster)
                .join(Session)
                .filter(Session.user_id == user_id)
            )

            # Apply embedding filter only if provided
            if query_embedding:
                query = query.filter(HistoryItem.embedding.isnot(None))

            if cluster_ids:
                query = query.filter(HistoryItem.cluster_id.in_(cluster_ids))

            # Apply date filters
            if date_from:
                query = query.filter(HistoryItem.visit_time >= date_from)
            if date_to:
                query = query.filter(HistoryItem.visit_time <= date_to)

            if title_contains:
                query = query.filter(HistoryItem.title.ilike(f'%{title_contains}%'))

            # Apply domain filter
            if domain_contains:
                query = query.filter(HistoryItem.domain.ilike(f'%{domain_contains}%'))

            if query_embedding:
                query = query.order_by(HistoryItem.embedding.cosine_distance(query_embedding))
            else:
                query = query.order_by(HistoryItem.visit_time.desc())

            query = query.limit(limit)

            return query.all()

        result = self._execute(operation, "Failed to search history items by embedding")
        duration_ms = (time.perf_counter() - start) * 1000
        
        results_count = len(result) if isinstance(result, list) else 0
        logger.info(
            "db_search_items",
            extra={
                "request_id": get_request_id(),
                "limit": limit,
                "has_embedding": query_embedding is not None,
                "cluster_ids_count": len(cluster_ids) if cluster_ids else 0,
                "has_filters": any([date_from, date_to, title_contains, domain_contains]),
                "results_count": results_count,
                "duration_ms": round(duration_ms, 2)
            }
        )
        
        return result if isinstance(result, list) else []

    def get_session_with_relations(self, session_identifier: str) -> Optional[Dict]:
        """Get session with all related clusters and items"""
        def operation(db):
            from sqlalchemy.orm import joinedload
            
            session = db.query(Session)\
                .options(joinedload(Session.clusters))\
                .filter(Session.session_identifier == session_identifier)\
                .first()
            return session
        
        return self._execute(operation, "Failed to get session with relations")
    
    def delete_session_by_identifier(self, session_identifier: str) -> bool:
        def operation(db):
            session = db.query(Session).filter(Session.session_identifier == session_identifier).first()
            if not session:
                return False
            db.delete(session)
            return True
        
        result = self._execute(operation, "Failed to delete session by identifier")
        return result is True  # Convert None → False for consistency
    
    # History item operations
    
    def create_history_item(
        self,
        cluster_id: int,
        url: str,
        title: Optional[str] = None,
        domain: Optional[str] = None,
        visit_time: Optional[datetime] = None,
        raw_semantics: Optional[dict] = None,
        embedding: Optional[list] = None
    ) -> Optional[Dict]:
        def operation(db):
            item = HistoryItem(
                cluster_id=cluster_id,
                url=url,
                title=title,
                domain=domain,
                visit_time=visit_time or datetime.now(),
                raw_semantics=raw_semantics,
                embedding=embedding
            )
            db.add(item)
            db.flush()
            db.refresh(item)
            return item
        
        return self._execute(operation, "Failed to create history item")
