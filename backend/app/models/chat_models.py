from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

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

# === Core Chat Models (Phase 1) ===

class ChatMessage(BaseModel):
    """Individual chat message"""
    role: MessageRole = Field(...)
    content: str = Field(...)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = Field(None)
    history: Optional[List[ChatMessage]] = Field(default=[])
    provider: ChatProvider = Field(default=ChatProvider.GOOGLE)
    
    class Config:
        use_enum_values = True

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str = Field(...)
    conversation_id: str = Field(...)
    timestamp: datetime = Field(default_factory=datetime.now)
    provider: str = Field(...)
    model: str = Field(...)
