from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class LLMRequest(BaseModel):
    """Request model for LLM text generation"""
    prompt: str = Field(..., description="The input prompt for text generation")
    provider: str = Field(default="openai", description="LLM provider to use (openai, anthropic, ollama, google)")
    model: Optional[str] = Field(default=None, description="Specific model to use (provider-specific)")
    max_tokens: Optional[int] = Field(default=1000, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(default=0.7, description="Sampling temperature (0.0 to 2.0)")
    additional_params: Optional[Dict[str, Any]] = Field(default=None, description="Provider-specific parameters")

class LLMResponse(BaseModel):
    """Response model for LLM text generation"""
    generated_text: str = Field(..., description="The generated text")
    provider: str = Field(..., description="Provider used for generation")
    model: str = Field(..., description="Model used for generation")
    usage: Optional[Dict[str, Any]] = Field(default=None, description="Token usage information")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
