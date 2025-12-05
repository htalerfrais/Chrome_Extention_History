from pydantic import BaseModel, Field
from datetime import datetime


class AuthenticateRequest(BaseModel):
    """Request containing only the OAuth token - google_user_id is extracted server-side"""
    token: str = Field(...)


class AuthenticateResponse(BaseModel):
    """Response with user info after successful authentication"""
    id: int = Field(...)
    google_user_id: str = Field(...)
    token: str = Field(...)
    created_at: datetime = Field(default_factory=datetime.now)
