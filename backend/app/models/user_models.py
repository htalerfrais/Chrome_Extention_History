from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class AuthenticateRequest(BaseModel):
    token: str = Field(...)
    google_user_id: str = Field(...)

class AuthenticateResponse(BaseModel):
    # what does our frontend need to know about the user ?
    # we need to know what everything that is gonig to be needeed to call the other services

    id: int = Field(...)
    google_user_id: str = Field(...)
    token: str = Field(...)
    created_at: datetime = Field(default_factory=datetime.now)