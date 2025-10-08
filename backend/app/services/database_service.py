"""
Database Service - Simple CRUD operations

This service handles basic database operations for all models.
"""

from typing import Optional, Callable, Any
from datetime import datetime
import logging

from app.database import SessionLocal
from app.models.database_models import User, Session, Cluster, HistoryItem

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for database CRUD operations"""
    
    def _execute(self, operation: Callable, error_msg: str = "Operation failed") -> Any:
        """
        Generic database operation wrapper
        Handles session lifecycle, commits, rollbacks, and error logging
        """
        db = SessionLocal()
        try:
            result = operation(db)
            if result is not None:
                db.commit()
            return result
        except Exception as e:
            db.rollback()
            logger.error(f"❌ {error_msg}: {e}")
            return None
        finally:
            db.close()
    
    # User operations
    
    def get_or_create_user(self, email: str, username: Optional[str] = None) -> Optional[User]:
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
    ) -> Optional[Session]:
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
    ) -> Optional[Cluster]:
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
    ) -> Optional[HistoryItem]:
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
