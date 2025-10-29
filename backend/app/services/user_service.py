"""
User Service - Business logic for user operations

This service handles user-related business logic and orchestrates
database operations through the repository layer.
"""

from typing import Optional, Dict, List
import logging

from app.repositories.database_repository import DatabaseRepository
from app.models.user_models import AuthenticateRequest, AuthenticateResponse

logger = logging.getLogger(__name__)


class UserService:
    """Service for user business logic and orchestration"""
    
    def __init__(self, db_repository: DatabaseRepository):
        self.db_repository = db_repository
    
    # User CRUD operations
    

    def authenticate(self,  request: AuthenticateRequest) -> Optional[Dict]:
        """Authenticate user with Google using stable google_user_id"""
        return self.db_repository.get_or_create_user_by_google_id(request.google_user_id, token=request.token)


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