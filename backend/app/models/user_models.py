from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TokenInfo(BaseModel):
    """Validated token information from Google"""
    google_user_id: str = Field(...)  # "sub" field - stable user identifier
    email: Optional[str] = None
    expires_in: int = 0


class AuthenticateRequest(BaseModel):
    """Request containing only the OAuth token - google_user_id is extracted server-side"""
    token: str = Field(...)


class AuthenticateResponse(BaseModel):
    """Response with user info after successful authentication"""
    id: int = Field(...)
    google_user_id: str = Field(...)
    token: str = Field(...)
    created_at: datetime = Field(default_factory=datetime.now)
