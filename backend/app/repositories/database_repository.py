"""
Database Repository - Simple CRUD operations

This repository handles basic database operations for all models.
Returns dictionaries to avoid SQLAlchemy session dependencies.
"""

from typing import Optional, Callable, Any, Dict, List
from datetime import datetime
import logging
from contextlib import contextmanager

from app.database import SessionLocal
from app.models.database_models import User, Session, Cluster, HistoryItem

logger = logging.getLogger(__name__)


class DatabaseRepository:
    """Repository for database CRUD operations"""
    
    @contextmanager
    def _get_session(self):
        """Context manager for database sessions"""
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
        Returns dictionary or list to avoid SQLAlchemy session dependencies
        """
        try:
            with self._get_session() as db:
                result = operation(db)
                if result is not None:
                    # Convert SQLAlchemy object(s) to dict(s)
                    if isinstance(result, list):
                        return [self._to_dict(obj) for obj in result]
                    return self._to_dict(result)
                return None
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
            # Convert datetime to ISO string for JSON serialization
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
        """Get existing user by google_user_id or create new one; update token if provided."""
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
    
    # Session operations
    
    def get_session_by_identifier(self, session_identifier: str) -> Optional[Dict]:
        """Get a session by its unique identifier"""
        def operation(db):
            session = db.query(Session).filter(Session.session_identifier == session_identifier).first()
            return session
        
        return self._execute(operation, "Failed to get session by identifier")
    
    def create_session(
        self,
        user_id: int,
        session_identifier: str,
        start_time: datetime,
        end_time: datetime,
        embedding: Optional[list] = None
    ) -> Optional[Dict]:
        """Create a new browsing session"""
        def operation(db):
            session = Session(
                user_id=user_id,
                session_identifier=session_identifier,
                start_time=start_time,
                end_time=end_time,
                embedding=embedding
            )
            db.add(session)
            db.flush()
            db.refresh(session)
            logger.info(f"✅ Created session ID: {session.id}, identifier: {session.session_identifier}")
            return session
        
        return self._execute(operation, "Failed to create session")
    
    # Cluster operations
    
    def create_cluster(
        self,
        session_id: int,
        name: str,
        description: Optional[str] = None,
        embedding: Optional[list] = None
    ) -> Optional[Dict]:
        """Create a new cluster within a session"""
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
            clusters = db.query(Cluster).filter(Cluster.session_id == session_id).all()
            return clusters
        
        result = self._execute(operation, "Failed to get clusters by session id")
        if result is None:
            return []
        return result if isinstance(result, list) else []
    
    def get_history_items_by_cluster_id(self, cluster_id: int) -> List[Dict]:
        """Get all history items for a cluster"""
        def operation(db):
            items = db.query(HistoryItem).filter(HistoryItem.cluster_id == cluster_id).all()
            return items
        
        result = self._execute(operation, "Failed to get history items by cluster id")
        if result is None:
            return []
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
        """Create a new history item within a cluster"""
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
