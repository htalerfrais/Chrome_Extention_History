import os
import httpx
from typing import Optional
import logging

from ..base_provider import LLMProviderInterface
from ...models.llm_models import LLMRequest, LLMResponse, LLMProvider

logger = logging.getLogger(__name__)

class AnthropicProvider(LLMProviderInterface):
    """Anthropic Claude provider implementation"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = base_url or "https://api.anthropic.com/v1"
        
        if not self.api_key:
            logger.warning("Anthropic API key not provided")
    
    def get_default_model(self) -> str:
        return "claude-3-sonnet-20240229"
    
    def validate_request(self, request: LLMRequest) -> bool:
        return request.provider == LLMProvider.ANTHROPIC
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        if not self.api_key:
            raise ValueError("Anthropic API key is required")
        
        model = request.model or self.get_default_model()
        
        payload = {
            "model": model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": [{"role": "user", "content": request.prompt}]
        }
        
        # Add any additional parameters
        if request.additional_params:
            payload.update(request.additional_params)
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                generated_text = data["content"][0]["text"]
                usage = data.get("usage")
                
                return LLMResponse(
                    generated_text=generated_text,
                    provider=LLMProvider.ANTHROPIC,
                    model=model,
                    usage=usage,
                    metadata={"response_id": data.get("id")}
                )
                
        except httpx.HTTPError as e:
            logger.error(f"Anthropic API error: {e}")
            raise Exception(f"Anthropic API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in Anthropic provider: {e}")
            raise
