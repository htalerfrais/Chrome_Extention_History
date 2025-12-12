from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from enum import Enum


class SearchFilters(BaseModel):
    """Filters for history search"""
    query_text: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    title_contains: Optional[str] = None
    domain_contains: Optional[str] = None


# === Enums for type safety ===

class MessageRole(str, Enum):
    """Roles for chat messages"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatProvider(str, Enum):
    """Available LLM providers for chat"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"

# === Core Chat Models ===

# Dans un ChatRequest on peut avoir plusieurs ChatMessage objects
class ChatMessage(BaseModel):
    """Individual chat message"""
    model_config = ConfigDict(use_enum_values=True)
    
    role: MessageRole = Field(...)
    content: str = Field(...)
    timestamp: datetime = Field(default_factory=datetime.now)


# frontend is sending the history to the backend as alist of ChatMessage objects
class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    model_config = ConfigDict(use_enum_values=True)
    
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = Field(None) # created if not existing yet
    history: Optional[List[ChatMessage]] = Field(default=[])
    provider: ChatProvider = Field(default=ChatProvider.GOOGLE)
    user_token: Optional[str] = Field(None)  # Google OAuth token for history search

class SourceItem(BaseModel):
    """
    Lightweight representation of a history item used as a source reference.
    Derived from ClusterItem but excludes embedding to reduce payload size.
    """
    url: str
    title: str
    visit_time: datetime
    url_hostname: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str = Field(...)
    conversation_id: str = Field(...)
    timestamp: datetime = Field(default_factory=datetime.now)
    provider: str = Field(...)
    model: str = Field(...)
    sources: Optional[List[SourceItem]] = None  # RAG search sources
