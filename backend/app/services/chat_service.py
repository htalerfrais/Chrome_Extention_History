from typing import Dict, List, Optional
from datetime import datetime
import uuid
import logging

from ..models.chat_models import ChatRequest, ChatResponse, ChatMessage, ChatError
from ..models.llm_models import LLMRequest
from .llm_service import LLMService

logger = logging.getLogger(__name__)

class ChatService:
    """
    Service for managing chat conversations
    
    Phase 1: Simple LLM chat with conversation context
    - In-memory conversation storage
    - Basic prompt building with history
    - Integration with existing LLMService
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        # Phase 1: In-memory storage (simple dict)
        # Phase 2: Will migrate to database
        self.conversations: Dict[str, List[Dict]] = {}
        
        logger.info("ChatService initialized with in-memory conversation storage")
    
    def _generate_conversation_id(self) -> str:
        """Generate a unique conversation ID"""
        return str(uuid.uuid4())
    
    def _build_conversation_prompt(self, user_message: str, history: List[ChatMessage]) -> str:
        """
        Build conversation prompt with context
        
        Phase 1: Simple system prompt + conversation history
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
        
        logger.debug(f"Built prompt with {len(recent_history)} history messages")
        return prompt
    
    def _store_conversation_message(self, conversation_id: str, role: str, content: str) -> None:
        """Store a message in the conversation history"""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        self.conversations[conversation_id].append(message)
        
        # Keep only last 50 messages per conversation to prevent memory bloat
        if len(self.conversations[conversation_id]) > 50:
            self.conversations[conversation_id] = self.conversations[conversation_id][-50:]
        
        logger.debug(f"Stored {role} message in conversation {conversation_id}")
    
    def _get_conversation_history(self, conversation_id: str) -> List[ChatMessage]:
        """Get conversation history as ChatMessage objects"""
        if conversation_id not in self.conversations:
            return []
        
        history = []
        for msg in self.conversations[conversation_id]:
            history.append(ChatMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=datetime.fromisoformat(msg["timestamp"])
            ))
        
        return history
    
    async def process_message(self, request: ChatRequest) -> ChatResponse:
        """
        Process user message and generate response
        
        Phase 1: Simple LLM chat with conversation context
        Phase 2: Will add tool calling and history data integration
        """
        try:
            # Generate or reuse conversation ID
            conversation_id = request.conversation_id or self._generate_conversation_id()
            
            # Get existing conversation history
            existing_history = self._get_conversation_history(conversation_id)
            
            # Merge with provided history (if any)
            all_history = existing_history + (request.history or [])
            
            # Build prompt with context
            prompt = self._build_conversation_prompt(request.message, all_history)
            
            # Create LLM request
            llm_request = LLMRequest(
                prompt=prompt,
                provider=request.provider,
                max_tokens=500,  # Reasonable limit for chat responses
                temperature=0.7  # Balanced creativity
            )
            
            logger.info(f"Processing chat message for conversation {conversation_id}")
            
            # Call existing LLM service
            llm_response = await self.llm_service.generate_text(llm_request)
            
            # Store both user message and assistant response
            self._store_conversation_message(conversation_id, "user", request.message)
            self._store_conversation_message(conversation_id, "assistant", llm_response.generated_text)
            
            # Create response
            response = ChatResponse(
                response=llm_response.generated_text,
                conversation_id=conversation_id,
                timestamp=datetime.now(),
                provider=llm_response.provider,
                model=llm_response.model
            )
            
            logger.info(f"Successfully processed chat message for conversation {conversation_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            raise ChatError(
                error=f"Failed to process chat message: {str(e)}",
                error_code="CHAT_PROCESSING_ERROR",
                conversation_id=conversation_id if 'conversation_id' in locals() else None
            )
