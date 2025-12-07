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
from .search_service import SearchService, SearchFilters
from .user_service import UserService

logger = logging.getLogger(__name__)

class ChatService:
    """
    Service for managing chat conversations with tool calling support
    
    Tool calling: Single-pass detection with [SEARCH: query] tag
    - 1 LLM call for simple questions
    - 2 LLM calls when history search is needed
    """
    
    SEARCH_TAG_PATTERN = r'\[SEARCH:\s*(.+?)\]'
    
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
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M:%S")
        
        base_prompt = (
            f"You are a helpful assistant for browsing history analysis. "
            f"Current date and time: {current_date} {current_time}. "
            f"You help users understand their browsing patterns and find information from their history. "
            f"Be concise, friendly, and helpful in your responses."
        )
        
        if with_tool_instructions:
            return (
                f"{base_prompt}\n\n"
                "TOOL AVAILABLE - History Search:\n"
                "If the user's question would benefit from searching their browsing history, "
                "start your response ONLY with [SEARCH: your search query] on a single line.\n"
                "You can add optional filters using: [SEARCH: query | filter:value | filter:value]\n"
                "Available filters:\n"
                "- after:YYYY-MM-DD - only items visited after this date\n"
                "- before:YYYY-MM-DD - only items visited before this date\n"
                "- title:keyword - only items with keyword in title\n"
                "- domain:keyword - only items from domains containing keyword\n"
                "Examples:\n"
                "- 'What articles did I read about AI?' → [SEARCH: AI articles]\n"
                "- 'Show me my shopping history' → [SEARCH: shopping purchases]\n"
                f"- 'What did I read today?' → [SEARCH: * | after:{current_date}]\n"
                "- 'What did I read on Amazon last month?' → [SEARCH: shopping | domain:amazon | after:2024-10-01]\n"
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
                url = item.url or ""
                visit_date = item.visit_time.strftime('%Y-%m-%d') if item.visit_time else ""
                parts.append(f"• {title} ({domain}) - visited: {visit_date} - {url}")
        
        return "\n".join(parts)
    
    def _parse_search_request(self, response_text: str) -> Optional[SearchFilters]:
        """Extract search query and filters from LLM response if present"""
        match = re.search(self.SEARCH_TAG_PATTERN, response_text, re.IGNORECASE)
        if not match:
            return None
        
        content = match.group(1).strip()
        if not content:
            return None
        
        # Parse query and filters: "query | filter:value | filter:value"
        parts = [p.strip() for p in content.split('|')]
        query_text = parts[0] if parts else None
        
        # Initialize filters
        date_from = None
        date_to = None
        title_contains = None
        domain_contains = None
        
        # Parse filter parts
        for part in parts[1:]:
            if ':' not in part:
                continue
            
            key, value = part.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            if key == 'after':
                try:
                    date_from = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    logger.warning(f"Invalid date format in 'after' filter: {value}")
            elif key == 'before':
                try:
                    date_to = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    logger.warning(f"Invalid date format in 'before' filter: {value}")
            elif key == 'title':
                title_contains = value
            elif key == 'domain':
                domain_contains = value
        
        return SearchFilters(
            query_text=query_text,
            date_from=date_from,
            date_to=date_to,
            title_contains=title_contains,
            domain_contains=domain_contains
        )
    
    def _strip_search_tag(self, response_text: str) -> str:
        """Remove [SEARCH: query] tag from response text"""
        return re.sub(self.SEARCH_TAG_PATTERN, '', response_text, flags=re.IGNORECASE).strip()
    
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
            response_metadata = first_response  # Track which response we're using
            
            # Step 2: Check for search tool call
            search_filters = self._parse_search_request(response_text)
            
            if search_filters:
                if not request.user_token:
                    logger.warning("Search requested but user_token missing - stripping tag from response")
                    response_text = self._strip_search_tag(response_text)
                else:
                    logger.info(f"🔍 Tool call detected: searching with query='{search_filters.query_text}', filters={search_filters}")
                    
                    # Get user_id from token
                    user_dict = await self.user_service.get_user_from_token(request.user_token)
                    
                    if user_dict:
                        user_id = user_dict["id"]
                        
                        # Execute search
                        clusters, items = await self.search_service.search(
                            user_id=user_id,
                            filters=search_filters
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
                        response_metadata = final_response  # Use metadata from the actual response
                    else:
                        logger.warning("User not found for token - stripping tag from response")
                        response_text = self._strip_search_tag(response_text)
            
            response = ChatResponse(
                response=response_text,
                conversation_id=conversation_id,
                timestamp=datetime.now(),
                provider=response_metadata.provider,
                model=response_metadata.model
            )
            
            logger.info(f"💬 ChatResponse payload: {response.model_dump()}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            raise
