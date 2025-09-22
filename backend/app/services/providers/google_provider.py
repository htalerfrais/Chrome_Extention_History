import os
import httpx
from typing import Optional
import logging

from .base_provider import LLMProviderInterface
from ...models.llm_models import LLMRequest, LLMResponse

logger = logging.getLogger(__name__)

class GoogleProvider(LLMProviderInterface):
    """Google Gemini provider implementation"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.base_url = base_url or "https://generativelanguage.googleapis.com/v1beta"
        
        if not self.api_key:
            logger.warning("Google API key not provided")
    
    def get_default_model(self) -> str:
        return "gemini-1.5-flash"
    
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
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract generated text from Gemini response
                if "candidates" in data and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        generated_text = candidate["content"]["parts"][0]["text"]
                    else:
                        generated_text = ""
                else:
                    generated_text = ""
                
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
