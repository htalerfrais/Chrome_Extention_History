from typing import List
from datetime import datetime
import uuid
import logging

from ..models.chat_models import ChatRequest, ChatResponse, ChatMessage
from ..models.llm_models import LLMRequest
from .llm_service import LLMService

logger = logging.getLogger(__name__)

class ChatService:
    """
    Service for managing chat conversations
    
    Phase 1: Simple LLM chat with conversation context
    - Client-side conversation storage (stateless backend)
    - Basic prompt building with history
    - Integration with existing LLMService
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
    
    def _generate_conversation_id(self) -> str:
        """Generate a unique conversation ID"""
        return str(uuid.uuid4())
    
    def _build_conversation_prompt(self, user_message: str, history: List[ChatMessage]) -> str:
        """
        Build conversation prompt with context
        
        Phase 1: Simple system prompt + conversation history from client
        Phase 2: Will add history data context and tool instructions
        """
        # System prompt for browsing history assistant
        system_prompt = (
            "You are a helpful assistant for browsing history analysis. "
            "You help users understand their browsing patterns and find information from their history. "
            "Be concise, friendly, and helpful in your responses."
        )
        
        # Build conversation context from history
        context_lines = []
        
        # Add recent conversation history (last 10 messages to avoid token limits)
        recent_history = history[-10:] if history else []
        
        for msg in recent_history:
            role_prefix = "User" if msg.role == "user" else "Assistant"
            context_lines.append(f"{role_prefix}: {msg.content}")
        
        # Combine system prompt, context, and current message
        if context_lines:
            context = "\n".join(context_lines)
            prompt = f"{system_prompt}\n\nPrevious conversation:\n{context}\n\nUser: {user_message}\nAssistant:"
        else:
            prompt = f"{system_prompt}\n\nUser: {user_message}\nAssistant:"
        
        return prompt
    
    async def process_message(self, request: ChatRequest) -> ChatResponse:
        """
        Process user message and generate response
        
        Phase 1: Simple LLM chat with conversation context from client
        Phase 2: Will add tool calling and history data integration
        """
        try:
            # Log complete ChatRequest payload
            logger.info(f"💬 ChatRequest payload: {request.model_dump()}")
            
            # Generate or reuse conversation ID
            conversation_id = request.conversation_id or self._generate_conversation_id()
            
            # Use history provided by client (stateless approach)
            all_history = request.history or []
            
            # Build prompt with context
            prompt = self._build_conversation_prompt(request.message, all_history)
            
            # Create LLM request
            llm_request = LLMRequest(
                prompt=prompt,
                provider=request.provider,
                max_tokens=500,  # Reasonable limit for chat responses
                temperature=0.7  # Balanced creativity
            )
            
            # Call existing LLM service
            llm_response = await self.llm_service.generate_text(llm_request)
            
            # Create response
            response = ChatResponse(
                response=llm_response.generated_text,
                conversation_id=conversation_id,
                timestamp=datetime.now(),
                provider=llm_response.provider,
                model=llm_response.model
            )
            
            # Log complete ChatResponse payload
            logger.info(f"💬 ChatResponse payload: {response.model_dump()}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            raise
