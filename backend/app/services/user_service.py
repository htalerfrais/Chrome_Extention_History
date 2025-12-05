"""
User Service - Business logic for user operations

This service handles user-related business logic and orchestrates
database operations through the repository layer.
"""

from typing import Optional, Dict
import logging

from app.repositories.database_repository import DatabaseRepository
from app.models.user_models import AuthenticateRequest
from app.services.google_auth_service import GoogleAuthService

logger = logging.getLogger(__name__)


class UserService:
    """Service for user business logic and orchestration"""
    
    def __init__(self, db_repository: DatabaseRepository, google_auth_service: GoogleAuthService):
        self.db_repository = db_repository
        self.google_auth_service = google_auth_service

    async def authenticate(self, request: AuthenticateRequest) -> Optional[Dict]:
        """
        Authenticate user by validating token with Google.
        
        The google_user_id is extracted from the validated token,
        NOT trusted from the client request.
        """
        # Validate token with Google and get the real google_user_id
        token_info = await self.google_auth_service.validate_token(request.token)
        
        if not token_info:
            logger.warning("Token validation failed")
            return None
        
        # Use the google_user_id from Google's response (trusted source)
        return self.db_repository.get_or_create_user_by_google_id(
            token_info.google_user_id, 
            token=request.token
        )
    
    async def get_user_from_token(self, token: str) -> Optional[Dict]:
        """
        Get user from a validated token.
        Used by endpoints that need user context.
        """
        token_info = await self.google_auth_service.validate_token(token)
        
        if not token_info:
            return None
        
        return self.db_repository.get_or_create_user_by_google_id(
            token_info.google_user_id,
            token=token
        )
