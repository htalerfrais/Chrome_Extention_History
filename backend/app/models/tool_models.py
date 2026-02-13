from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ToolDefinition(BaseModel):
    """Provider-agnostic tool definition"""
    name: str
    description: str
    parameters: Dict[str, Any]  


class ToolCall(BaseModel):
    """A tool invocation requested by the LLM."""
    id: str            
    name: str          
    arguments: dict    


class ToolResult(BaseModel):
    """Result of executing a tool, sent back to the LLM."""
    call_id: str
    content: str


class ConversationMessage(BaseModel):
    """Structured message for multi-turn tool conversations.
    
    Roles:
      - "system": system instructions (content only)
      - "user": user message (content only)
      - "assistant": model response (content and/or tool_calls)
      - "tool": tool result (content + tool_call_id)
    """
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None   # Only for role= assistant
    tool_call_id: Optional[str] = None            # Only for role= tool


class ToolAugmentedRequest(BaseModel):
    """Request model for LLM generation with tool/function calling support.
    Containing all messages, tools available and their definitions, provider, params...
    """
    messages: List[ConversationMessage]
    tools: List[ToolDefinition]
    provider: str
    model: Optional[str] = None
    max_tokens: int = Field(default=1000)
    temperature: float = Field(default=0.7)


class ToolAugmentedResponse(BaseModel):
    """Response model for LLM generation with tool calling support.
    has usage metricks, tokens used ...
    """
    text: Optional[str] = None
    tool_calls: List[ToolCall] = Field(default_factory=list) #defaults to empty list
    provider: str
    model: str
    usage: Optional[Dict[str, Any]] = None # token usage and other metrics
