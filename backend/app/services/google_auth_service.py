import httpx
import logging
from typing import Optional

from app.config import settings
from app.models.user_models import TokenInfo

logger = logging.getLogger(__name__)

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


class GoogleAuthService:
    """Service for validating Google OAuth tokens"""
    
    async def validate_token(self, token: str) -> Optional[TokenInfo]:
        """
        Validate a Google OAuth token and extract user info.
        
        Returns TokenInfo if valid, None if invalid/expired.
        """
        if not token:
            logger.warning("Empty token provided")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=settings.api_timeout) as client:
                response = await client.get(
                    GOOGLE_TOKENINFO_URL,
                    params={"access_token": token}
                )
                
                if response.status_code != 200:
                    logger.warning(f"Token validation failed: HTTP {response.status_code}")
                    return None
                
                data = response.json()
                
                google_user_id = data.get("sub")
                if not google_user_id:
                    logger.warning("Token valid but missing 'sub' field")
                    return None
                
                token_info = TokenInfo(
                    google_user_id=google_user_id,
                    email=data.get("email"),
                    expires_in=int(data.get("expires_in", 0))
                )
                
                logger.info(f"✅ Token validated for google_user_id: {google_user_id}")
                return token_info
                
        except httpx.TimeoutException:
            logger.error("Timeout validating token with Google")
            return None
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return None

