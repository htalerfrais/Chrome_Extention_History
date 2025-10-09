import os
import httpx
from typing import Optional
import logging

from app.config import settings
from .base_provider import LLMProviderInterface
from app.models.llm_models import LLMRequest, LLMResponse

logger = logging.getLogger(__name__)

class OpenAIProvider(LLMProviderInterface):
    """OpenAI GPT provider implementation"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        self.api_key = api_key or settings.openai_api_key
        self.base_url = base_url or settings.openai_base_url
        
        if not self.api_key:
            logger.warning("OpenAI API key not provided")
    
    def get_default_model(self) -> str:
        return "gpt-4.1-mini"  # Updated to current recommended model
    
    def validate_request(self, request: LLMRequest) -> bool:
        return request.provider == "openai"
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        model = request.model or self.get_default_model()
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": request.prompt}],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        
        # Add any additional parameters
        if request.additional_params:
            payload.update(request.additional_params)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"Sending request to OpenAI with model: {model}")
            logger.debug(f"OpenAI payload: {payload}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=settings.api_timeout
                )
                response.raise_for_status()
                data = response.json()
                
                logger.debug(f"OpenAI response received: {data}")
                
                generated_text = data["choices"][0]["message"]["content"]
                usage = data.get("usage")
                
                return LLMResponse(
                    generated_text=generated_text,
                    provider="openai",
                    model=model,
                    usage=usage,
                    metadata={"response_id": data.get("id")}
                )
                
        except httpx.HTTPError as e:
            logger.error(f"OpenAI API HTTP error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    logger.error(f"OpenAI API error details: {error_data}")
                except:
                    logger.error(f"OpenAI API raw response: {e.response.text}")
            raise Exception(f"OpenAI API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI provider: {e}")
            raise
