from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

from app.models.llm_models import LLMRequest, LLMResponse
from app.models.tool_models import ToolAugmentedRequest, ToolAugmentedResponse

logger = logging.getLogger(__name__)

class LLMProviderInterface(ABC):
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
    
    @abstractmethod
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        pass
    
    @abstractmethod
    def validate_request(self, request: LLMRequest) -> bool:
        pass

    async def generate_with_tools(self, request: ToolAugmentedRequest) -> ToolAugmentedResponse:
        """Generate a response with function/tool calling support.
        
        Override in providers that support function calling.
        Providers that don't override will raise NotImplementedError.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support function calling"
        )
