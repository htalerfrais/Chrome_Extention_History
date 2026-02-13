import httpx
import logging
import time
from typing import Optional

from app.config import settings
from app.models.user_models import TokenInfo
from app.monitoring import get_request_id

logger = logging.getLogger(__name__)

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


class GoogleAuthService:
    """Service for validating Google OAuth tokens"""
    
    async def validate_token(self, token: str) -> Optional[TokenInfo]:
        """
        Validate a Google OAuth token and extract user info.
        
        Returns TokenInfo if valid, None if invalid/expired.
        """
        start = time.perf_counter()
        
        if not token:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=settings.api_timeout) as client:
                response = await client.get(
                    GOOGLE_TOKENINFO_URL,
                    params={"access_token": token}
                )
                
                duration_ms = (time.perf_counter() - start) * 1000
                
                if response.status_code != 200:
                    logger.info(
                        "auth_validation",
                        extra={
                            "request_id": get_request_id(),
                            "validation_success": False,
                            "duration_ms": round(duration_ms, 2),
                            "status_code": response.status_code
                        }
                    )
                    return None
                
                data = response.json()
                
                google_user_id = data.get("sub")
                if not google_user_id:
                    logger.info(
                        "auth_validation",
                        extra={
                            "request_id": get_request_id(),
                            "validation_success": False,
                            "duration_ms": round(duration_ms, 2),
                            "reason": "missing_sub_field"
                        }
                    )
                    return None
                
                token_info = TokenInfo(
                    google_user_id=google_user_id,
                    email=data.get("email"),
                    expires_in=int(data.get("expires_in", 0))
                )
                
                logger.info(
                    "auth_validation",
                    extra={
                        "request_id": get_request_id(),
                        "validation_success": True,
                        "duration_ms": round(duration_ms, 2),
                        "google_user_id": google_user_id,
                        "expires_in": token_info.expires_in
                    }
                )
                return token_info
                
        except httpx.TimeoutException:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "auth_validation",
                extra={
                    "request_id": get_request_id(),
                    "validation_success": False,
                    "duration_ms": round(duration_ms, 2),
                    "error": "timeout"
                }
            )
            return None
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "auth_validation",
                extra={
                    "request_id": get_request_id(),
                    "validation_success": False,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(e)
                }
            )
            return None

