from typing import Dict
import logging

from .providers.openai_provider import OpenAIProvider
from .providers.anthropic_provider import AnthropicProvider
from .providers.ollama_provider import OllamaProvider
from .providers.google_provider import GoogleProvider
from ..models.llm_models import LLMRequest, LLMResponse

logger = logging.getLogger(__name__)

class LLMService:
    """Main LLM service that manages different providers"""
    
    def __init__(self):
        self.providers: Dict[str, object] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available providers"""
        try:
            self.providers["openai"] = OpenAIProvider()
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI provider: {e}")
        
        try:
            self.providers["anthropic"] = AnthropicProvider()
        except Exception as e:
            logger.warning(f"Failed to initialize Anthropic provider: {e}")
        
        try:
            self.providers["ollama"] = OllamaProvider()
        except Exception as e:
            logger.warning(f"Failed to initialize Ollama provider: {e}")
        
        try:
            self.providers["google"] = GoogleProvider()
        except Exception as e:
            logger.warning(f"Failed to initialize Google provider: {e}")
        
        logger.info(f"Initialized {len(self.providers)} LLM providers: {list(self.providers.keys())}")
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """Generate text using the specified provider"""
        if request.provider not in self.providers:
            available = list(self.providers.keys())
            raise ValueError(f"Provider {request.provider} not available. Available providers: {available}")
        
        provider = self.providers[request.provider]
        
        try:
            logger.info(f"Generating text with {request.provider} provider")
            response = await provider.generate_text(request)
            logger.info(f"Successfully generated text with {request.provider}")
            return response
        except Exception as e:
            logger.error(f"Error generating text with {request.provider}: {e}")
            raise