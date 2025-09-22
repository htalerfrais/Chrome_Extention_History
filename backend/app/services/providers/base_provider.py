from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

from ...models.llm_models import LLMRequest, LLMResponse

logger = logging.getLogger(__name__)

class LLMProviderInterface(ABC):
    """Abstract interface for LLM providers"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
    
    @abstractmethod
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """Generate text based on the request"""
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        """Get the default model for this provider"""
        pass
    
    @abstractmethod
    def validate_request(self, request: LLMRequest) -> bool:
        """Validate if the request is compatible with this provider"""
        pass
