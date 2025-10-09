"""
Database Repository - Simple CRUD operations

This repository handles basic database operations for all models.
Returns dictionaries to avoid SQLAlchemy session dependencies.
"""

from typing import Optional, Callable, Any, Dict
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
    
    def _execute(self, operation: Callable, error_msg: str = "Operation failed") -> Optional[Dict]:
        """
        Generic database operation wrapper
        Handles session lifecycle, commits, rollbacks, and error logging
        Returns dictionary to avoid SQLAlchemy session dependencies
        """
        try:
            with self._get_session() as db:
                result = operation(db)
                if result is not None:
                    # Convert SQLAlchemy object to dict
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
    
    def get_or_create_user(self, email: str, username: Optional[str] = None) -> Optional[Dict]:
        """Get existing user or create new one"""
        def operation(db):
            user = db.query(User).filter(User.email == email).first()
            if user:
                return user
            
            user = User(email=email, username=username)
            db.add(user)
            db.flush()
            db.refresh(user)
            logger.info(f"✅ Created user ID: {user.id}")
            return user
        
        return self._execute(operation, "User operation failed")
    
    # Session operations
    
    def create_session(
        self,
        user_id: int,
        start_time: datetime,
        end_time: datetime,
        embedding: Optional[list] = None
    ) -> Optional[Dict]:
        """Create a new browsing session"""
        def operation(db):
            session = Session(
                user_id=user_id,
                start_time=start_time,
                end_time=end_time,
                embedding=embedding
            )
            db.add(session)
            db.flush()
            db.refresh(session)
            logger.info(f"✅ Created session ID: {session.id}")
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
