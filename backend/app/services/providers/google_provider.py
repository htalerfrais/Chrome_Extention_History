import os
import httpx
from typing import Optional
import logging

from app.config import settings
from .base_provider import LLMProviderInterface
from app.models.llm_models import LLMRequest, LLMResponse

logger = logging.getLogger(__name__)

class GoogleProvider(LLMProviderInterface):
    """Google Gemini provider implementation"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        self.api_key = api_key or settings.google_api_key
        self.base_url = base_url or settings.google_base_url
        
        if not self.api_key:
            logger.warning("Google API key not provided")
    
    def get_default_model(self) -> str:
        return settings.default_model
    
    def validate_request(self, request: LLMRequest) -> bool:
        return request.provider == "google"
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        if not self.api_key:
            raise ValueError("Google API key is required")
        
        model = request.model or self.get_default_model()
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": request.prompt
                }]
            }],
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            }
        }
        
        # Add any additional parameters
        if request.additional_params:
            payload["generationConfig"].update(request.additional_params)
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/models/{model}:generateContent?key={self.api_key}",
                    json=payload,
                    headers=headers,
                    timeout=settings.api_timeout
                )
                response.raise_for_status()
                data = response.json()
                
                # Log raw API response for debugging
                logger.info(f"🔍 Google API response: {data}")
                
                # Log token consumption if available
                if "usageMetadata" in data:
                    usage = data["usageMetadata"]
                    logger.info(f"📊 Token usage - Prompt: {usage.get('promptTokenCount', 'N/A')}, Response: {usage.get('candidatesTokenCount', 'N/A')}")
                
                # Extract generated text from Gemini response
                generated_text = ""
                
                if "candidates" in data and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    
                    if "content" in candidate:
                        content = candidate["content"]
                        finish_reason = candidate.get("finishReason", "UNKNOWN")
                        
                        # Check if content was blocked or filtered
                        if finish_reason in ["SAFETY", "RECITATION", "OTHER"]:
                            generated_text = ""
                        elif finish_reason == "MAX_TOKENS":
                            # Still try to extract text even if truncated
                            pass
                        elif finish_reason != "STOP":
                            generated_text = ""
                        
                        # Look for parts array for all non-blocked cases
                        if "parts" in content and isinstance(content["parts"], list) and len(content["parts"]) > 0:
                            if "text" in content["parts"][0]:
                                generated_text = content["parts"][0]["text"]
                
                # Extract usage information if available
                usage = None
                if "usageMetadata" in data:
                    usage = data["usageMetadata"]
                
                return LLMResponse(
                    generated_text=generated_text,
                    provider="google",
                    model=model,
                    usage=usage,
                    metadata={"response_id": data.get("model")}
                )
                
        except httpx.HTTPError as e:
            logger.error(f"Google API error: {e}")
            raise Exception(f"Google API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in Google provider: {e}")
            raise
