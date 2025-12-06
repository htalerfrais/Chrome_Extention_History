from typing import List, Optional
from datetime import datetime
import uuid
import logging
import re

from app.config import settings
from ..models.chat_models import ChatRequest, ChatResponse, ChatMessage
from ..models.llm_models import LLMRequest
from ..models.session_models import ClusterResult, ClusterItem
from .llm_service import LLMService
from .search_service import SearchService
from .user_service import UserService

logger = logging.getLogger(__name__)

class ChatService:
    """
    Service for managing chat conversations with tool calling support
    
    Tool calling: Single-pass detection with [SEARCH: query] tag
    - 1 LLM call for simple questions
    - 2 LLM calls when history search is needed
    """
    
    SEARCH_TAG_PATTERN = r'^\[SEARCH:\s*(.+?)\]'
    
    def __init__(
        self, 
        llm_service: LLMService,
        search_service: SearchService,
        user_service: UserService
    ):
        self.llm_service = llm_service
        self.search_service = search_service
        self.user_service = user_service
    
    def _generate_conversation_id(self) -> str:
        """Generate a unique conversation ID"""
        return str(uuid.uuid4())
    
    def _build_system_prompt(self, with_tool_instructions: bool = True) -> str:
        """Build system prompt with or without tool instructions"""
        base_prompt = (
            "You are a helpful assistant for browsing history analysis. "
            "You help users understand their browsing patterns and find information from their history. "
            "Be concise, friendly, and helpful in your responses."
        )
        
        if with_tool_instructions:
            return (
                f"{base_prompt}\n\n"
                "TOOL AVAILABLE - History Search:\n"
                "If the user's question would benefit from searching their browsing history, "
                "start your response ONLY with [SEARCH: your search query] on a single line.\n"
                "Examples of when to search:\n"
                "- 'What articles did I read about AI?' → [SEARCH: AI articles]\n"
                "- 'Show me my shopping history' → [SEARCH: shopping purchases]\n"
                "Do NOT search for greetings, general questions, or topics unrelated to their browsing."
            )
        return base_prompt
    
    def _build_conversation_prompt(
        self, 
        user_message: str, 
        history: List[ChatMessage],
        with_tool_instructions: bool = True,
        search_context: Optional[str] = None
    ) -> str:
        """Build conversation prompt with optional search context"""
        system_prompt = self._build_system_prompt(with_tool_instructions)
        
        context_lines = []
        
        # Add search context if provided
        if search_context:
            context_lines.append(f"[Browsing History Context]\n{search_context}\n")
        
        # Add recent conversation history
        recent_history = history[-settings.chat_history_limit:] if history else []
        for msg in recent_history:
            role_prefix = "User" if msg.role == "user" else "Assistant"
            context_lines.append(f"{role_prefix}: {msg.content}")
        
        if context_lines:
            context = "\n".join(context_lines)
            return f"{system_prompt}\n\n{context}\n\nUser: {user_message}\nAssistant:"
        else:
            return f"{system_prompt}\n\nUser: {user_message}\nAssistant:"
    
    def _format_search_results(
        self, 
        clusters: List[ClusterResult], 
        items: List[ClusterItem]
    ) -> str:
        """Format search results as context for the LLM"""
        if not clusters and not items:
            return "No relevant browsing history found."
        
        parts = []
        
        if clusters:
            parts.append("Relevant browsing themes:")
            for c in clusters[:5]:
                parts.append(f"• {c.theme}: {c.summary}")
        
        if items:
            parts.append("\nRelevant pages visited:")
            for item in items[:10]:
                title = item.title or "Untitled"
                domain = item.url_hostname or ""
                parts.append(f"• {title} ({domain})")
        
        return "\n".join(parts)
    
    def _parse_search_request(self, response_text: str) -> Optional[str]:
        """Extract search query from LLM response if present"""
        match = re.match(self.SEARCH_TAG_PATTERN, response_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    async def process_message(self, request: ChatRequest) -> ChatResponse:
        """
        Process user message with optional tool calling
        
        Flow:
        1. First LLM call with tool instructions
        2. If [SEARCH: query] detected → search history → second LLM call with context
        3. Return final response
        """
        try:
            logger.info(f"💬 ChatRequest payload: {request.model_dump()}")
            
            conversation_id = request.conversation_id or self._generate_conversation_id()
            history = request.history or []
            
            # Step 1: First LLM call with tool instructions
            prompt = self._build_conversation_prompt(
                request.message, 
                history, 
                with_tool_instructions=True
            )
            
            llm_request = LLMRequest(
                prompt=prompt,
                provider=request.provider,
                max_tokens=settings.chat_max_tokens,
                temperature=settings.chat_temperature
            )
            
            first_response = await self.llm_service.generate_text(llm_request)
            response_text = first_response.generated_text
            
            # Step 2: Check for search tool call
            search_query = self._parse_search_request(response_text)
            
            if search_query and request.user_token:
                logger.info(f"🔍 Tool call detected: searching for '{search_query}'")
                
                # Get user_id from token
                user_dict = await self.user_service.get_user_from_token(request.user_token)
                
                if user_dict:
                    user_id = user_dict["id"]
                    
                    # Execute search
                    clusters, items = await self.search_service.search(
                        user_id=user_id,
                        query_text=search_query
                    )
                    
                    search_context = self._format_search_results(clusters, items)
                    logger.info(f"🔍 Search returned {len(clusters)} clusters, {len(items)} items")
                    
                    # Step 3: Second LLM call with context (no tool instructions)
                    context_prompt = self._build_conversation_prompt(
                        request.message,
                        history,
                        with_tool_instructions=False,
                        search_context=search_context
                    )
                    
                    llm_request_with_context = LLMRequest(
                        prompt=context_prompt,
                        provider=request.provider,
                        max_tokens=settings.chat_max_tokens,
                        temperature=settings.chat_temperature
                    )
                    
                    final_response = await self.llm_service.generate_text(llm_request_with_context)
                    response_text = final_response.generated_text
                else:
                    logger.warning(f"User not found for token")
                    # Continue with first response without search
            
            response = ChatResponse(
                response=response_text,
                conversation_id=conversation_id,
                timestamp=datetime.now(),
                provider=first_response.provider,
                model=first_response.model
            )
            
            logger.info(f"💬 ChatResponse payload: {response.model_dump()}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            raise
