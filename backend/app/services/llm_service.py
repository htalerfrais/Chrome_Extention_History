from typing import Dict, Optional
import logging

from .base_provider import LLMProviderInterface
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .ollama_provider import OllamaProvider
from ..models.llm_models import LLMRequest, LLMResponse, LLMProvider

logger = logging.getLogger(__name__)

class LLMService:
    """Main LLM service that manages different providers"""
    
    def __init__(self):
        self.providers: Dict[LLMProvider, LLMProviderInterface] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available providers"""
        try:
            self.providers[LLMProvider.OPENAI] = OpenAIProvider()
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI provider: {e}")
        
        try:
            self.providers[LLMProvider.ANTHROPIC] = AnthropicProvider()
        except Exception as e:
            logger.warning(f"Failed to initialize Anthropic provider: {e}")
        
        try:
            self.providers[LLMProvider.OLLAMA] = OllamaProvider()
        except Exception as e:
            logger.warning(f"Failed to initialize Ollama provider: {e}")
        
        logger.info(f"Initialized {len(self.providers)} LLM providers: {list(self.providers.keys())}")
    
    def get_available_providers(self) -> list[LLMProvider]:
        """Get list of available providers"""
        return list(self.providers.keys())
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """Generate text using the specified provider"""
        if request.provider not in self.providers:
            available = self.get_available_providers()
            raise ValueError(f"Provider {request.provider} not available. Available providers: {available}")
        
        provider = self.providers[request.provider]
        
        if not provider.validate_request(request):
            raise ValueError(f"Invalid request for provider {request.provider}")
        
        try:
            logger.info(f"Generating text with {request.provider} provider")
            response = await provider.generate_text(request)
            logger.info(f"Successfully generated text with {request.provider}")
            return response
        except Exception as e:
            logger.error(f"Error generating text with {request.provider}: {e}")
            raise
    
    def add_provider(self, provider_type: LLMProvider, provider: LLMProviderInterface):
        """Add a custom provider instance"""
        self.providers[provider_type] = provider
        logger.info(f"Added custom provider: {provider_type}")
    
    def remove_provider(self, provider_type: LLMProvider):
        """Remove a provider"""
        if provider_type in self.providers:
            del self.providers[provider_type]
            logger.info(f"Removed provider: {provider_type}")
