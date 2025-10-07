import httpx
from typing import Optional
import logging

from ..config import settings
from .base_provider import LLMProviderInterface
from ...models.llm_models import LLMRequest, LLMResponse

logger = logging.getLogger(__name__)

class OllamaProvider(LLMProviderInterface):
    """Ollama local LLM provider implementation"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        # Ollama doesn't require API key, but we keep the interface consistent
        self.base_url = base_url or settings.ollama_base_url
    
    def get_default_model(self) -> str:
        return "llama2"
    
    def validate_request(self, request: LLMRequest) -> bool:
        return request.provider == "ollama"
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        model = request.model or self.get_default_model()
        
        payload = {
            "model": model,
            "prompt": request.prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens
            }
        }
        
        # Add any additional parameters
        if request.additional_params:
            payload["options"].update(request.additional_params)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=settings.ollama_timeout
                )
                response.raise_for_status()
                data = response.json()
                
                generated_text = data.get("response", "")
                
                return LLMResponse(
                    generated_text=generated_text,
                    provider="ollama",
                    model=model,
                    usage={"prompt_tokens": len(request.prompt.split()), "completion_tokens": len(generated_text.split())},
                    metadata={"done": data.get("done")}
                )
                
        except httpx.HTTPError as e:
            logger.error(f"Ollama API error: {e}")
            raise Exception(f"Ollama API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in Ollama provider: {e}")
            raise
