"""
User Service - Business logic for user operations

This service handles user-related business logic and orchestrates
database operations through the repository layer.
"""

from typing import Optional, Dict, List
import logging

from app.repositories.database_repository import DatabaseRepository

logger = logging.getLogger(__name__)


class UserService:
    """Service for user business logic and orchestration"""
    
    def __init__(self, db_repository: DatabaseRepository):
        self.db_repository = db_repository
    
    # User CRUD operations
    

    def authenticate(self, token: str) -> Optional[Dict]:
        """Authenticate user with Google"""
        # returns user_id, token, timestamp
        return self.db_repository.get_or_create_user(token)


# ------------------- Next steps ------------------------------

    def create_user(self, email: str, username: Optional[str] = None) -> Optional[Dict]:
        """Create a new user"""
        pass
    
    def update_user(self, user_id: int, **kwargs) -> Optional[Dict]:
        """Update user fields"""
        pass
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user"""
        pass