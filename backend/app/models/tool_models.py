from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ToolDefinition(BaseModel):
    """Provider-agnostic function/tool definition using JSON Schema for parameters."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema object


class ToolCall(BaseModel):
    """A tool invocation requested by the LLM."""
    id: str             # Provider-assigned call ID (synthetic for Google)
    name: str           # Function name
    arguments: dict     # Parsed arguments


class ToolResult(BaseModel):
    """Result of executing a tool, sent back to the LLM."""
    call_id: str        # Matches ToolCall.id
    content: str        # Stringified result


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
    tool_calls: Optional[List[ToolCall]] = None   # Only for role="assistant"
    tool_call_id: Optional[str] = None            # Only for role="tool"


class ToolAugmentedRequest(BaseModel):
    """Request model for LLM generation with tool/function calling support."""
    messages: List[ConversationMessage]
    tools: List[ToolDefinition]
    provider: str
    model: Optional[str] = None
    max_tokens: int = Field(default=1000)
    temperature: float = Field(default=0.7)


class ToolAugmentedResponse(BaseModel):
    """Response model for LLM generation with tool/function calling support."""
    text: Optional[str] = None              # Final text (when no tool calls)
    tool_calls: List[ToolCall] = Field(default_factory=list)
    provider: str
    model: str
    usage: Optional[Dict[str, Any]] = None
