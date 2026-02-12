import asyncio
from typing import List, Optional, Tuple
from datetime import datetime
import uuid
import logging

from app.config import settings
from ..models.chat_models import ChatRequest, ChatResponse, ChatMessage, SourceItem, SearchFilters
from ..models.session_models import ClusterResult, ClusterItem
from ..models.tool_models import (
    ToolDefinition, ToolCall, ToolResult,
    ConversationMessage, ToolAugmentedRequest, ToolAugmentedResponse,
)
from .llm_service import LLMService
from .search_service import SearchService
from .user_service import UserService

logger = logging.getLogger(__name__)


class ChatService:

    SEARCH_HISTORY_TOOL = ToolDefinition(
        name="search_history",
        description=(
            "Search the user's browsing history. Use when the user asks about "
            "pages they visited, topics they explored, or browsing patterns. "
            "You can call this tool multiple times with different queries to "
            "compare topics or gather broader information."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Semantic search query describing what to look for",
                },
                "date_from": {
                    "type": "string",
                    "description": "ISO date (YYYY-MM-DD), only items visited after this date",
                },
                "date_to": {
                    "type": "string",
                    "description": "ISO date (YYYY-MM-DD), only items visited before this date",
                },
                "title_contains": {
                    "type": "string",
                    "description": "Filter: only items with this keyword in the title",
                },
                "domain_contains": {
                    "type": "string",
                    "description": "Filter: only items from domains containing this keyword",
                },
            },
            "required": ["query"],
        },
    )

    def __init__(
        self,
        llm_service: LLMService,
        search_service: SearchService,
        user_service: UserService,
    ):
        self.llm_service = llm_service
        self.search_service = search_service
        self.user_service = user_service

    # ── Public entry point ────────────────────────────────────────────

    async def process_message(self, request: ChatRequest) -> ChatResponse:
        try:
            logger.info(f"💬 ChatRequest payload: {request.model_dump()}")

            conversation_id = request.conversation_id or self._generate_conversation_id()
            messages = self._build_messages(request)
            all_sources: List[SourceItem] = []

            # Resolve user_id once (needed for search tool)
            user_id: Optional[int] = None
            if request.user_token:
                user_dict = await self.user_service.get_user_from_token(request.user_token)
                if user_dict:
                    user_id = user_dict["id"]

            # Only offer tools if we have a valid user (needed for search)
            tools = [self.SEARCH_HISTORY_TOOL] if user_id else []

            # Agentic loop: LLM can request tools, we execute and feed back
            response: Optional[ToolAugmentedResponse] = None

            for iteration in range(settings.chat_max_tool_iterations):
                response = await self.llm_service.generate_with_tools(
                    ToolAugmentedRequest(
                        messages=messages,
                        tools=tools,
                        provider=request.provider,
                        max_tokens=settings.chat_max_tokens,
                        temperature=settings.chat_temperature,
                    )
                )

                # No tool calls means the model produced a final answer
                if not response.tool_calls:
                    break

                logger.info(
                    f"🔧 Iteration {iteration + 1}: "
                    f"{len(response.tool_calls)} tool call(s) requested"
                )

                # Append assistant message containing the tool calls
                messages.append(ConversationMessage(
                    role="assistant",
                    content=response.text,
                    tool_calls=response.tool_calls,
                ))

                # Execute all tool calls in parallel
                tool_tasks = [
                    self._execute_tool_call(tc, user_id)
                    for tc in response.tool_calls
                ]
                results = await asyncio.gather(*tool_tasks)

                # Append each tool result as a separate message & collect sources
                for tool_result, sources in results:
                    messages.append(ConversationMessage(
                        role="tool",
                        content=tool_result.content,
                        tool_call_id=tool_result.call_id,
                    ))
                    all_sources.extend(sources)

            chat_response = ChatResponse(
                response=(response.text if response else "") or "",
                conversation_id=conversation_id,
                timestamp=datetime.now(),
                provider=response.provider if response else request.provider,
                model=response.model if response else "",
                sources=all_sources or None,
            )

            logger.info(f"💬 ChatResponse payload: {chat_response.model_dump()}")
            return chat_response

        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            raise

    # ── Message building ──────────────────────────────────────────────

    def _build_system_prompt(self) -> str:
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M:%S")

        return (
            f"You are a helpful assistant for browsing history analysis. "
            f"Current date and time: {current_date} {current_time}. "
            f"You help users understand their browsing patterns and find information from their history. "
            f"Be friendly, and helpful in your responses."
        )

    def _build_messages(self, request: ChatRequest) -> List[ConversationMessage]:
        """Convert a ChatRequest into the initial ConversationMessage list."""
        messages: List[ConversationMessage] = []

        # System message
        messages.append(ConversationMessage(
            role="system",
            content=self._build_system_prompt(),
        ))

        # Recent conversation history
        history = request.history or []
        recent_history = history[-settings.chat_history_limit:]
        for msg in recent_history:
            messages.append(ConversationMessage(
                role=msg.role,
                content=msg.content,
            ))

        # Current user message
        messages.append(ConversationMessage(
            role="user",
            content=request.message,
        ))

        return messages

    # ── Tool execution ────────────────────────────────────────────────

    async def _execute_tool_call(
        self, tool_call: ToolCall, user_id: Optional[int]
    ) -> Tuple[ToolResult, List[SourceItem]]:
        """Execute a single tool call and return (result, sources)."""
        if tool_call.name == "search_history":
            return await self._execute_search_history(tool_call, user_id)

        # Unknown tool: return an error message instead of crashing
        logger.warning(f"Unknown tool call: {tool_call.name}")
        return (
            ToolResult(call_id=tool_call.id, content=f"Unknown tool: {tool_call.name}"),
            [],
        )

    async def _execute_search_history(
        self, tool_call: ToolCall, user_id: Optional[int]
    ) -> Tuple[ToolResult, List[SourceItem]]:
        """Execute the search_history tool."""
        args = tool_call.arguments

        # Parse date filters
        date_from = None
        date_to = None
        if args.get("date_from"):
            try:
                date_from = datetime.fromisoformat(args["date_from"])
            except ValueError:
                logger.warning(f"Invalid date_from: {args['date_from']}")
        if args.get("date_to"):
            try:
                date_to = datetime.fromisoformat(args["date_to"])
            except ValueError:
                logger.warning(f"Invalid date_to: {args['date_to']}")

        filters = SearchFilters(
            query_text=args.get("query"),
            date_from=date_from,
            date_to=date_to,
            title_contains=args.get("title_contains"),
            domain_contains=args.get("domain_contains"),
        )

        logger.info(f"🔍 search_history: query='{filters.query_text}', filters={filters}")

        if not user_id:
            return (
                ToolResult(call_id=tool_call.id, content="User not authenticated, cannot search history."),
                [],
            )

        clusters, items = await self.search_service.search(
            user_id=user_id,
            filters=filters,
        )

        search_context = self._format_search_results(clusters, items)
        logger.info(f"🔍 search_history returned {len(clusters)} clusters, {len(items)} items")

        sources = [
            SourceItem(
                url=item.url,
                title=item.title,
                visit_time=item.visit_time,
                url_hostname=item.url_hostname,
            )
            for item in items
        ]

        return ToolResult(call_id=tool_call.id, content=search_context), sources

    # ── Formatting helpers ────────────────────────────────────────────

    def _format_search_results(
        self,
        clusters: List[ClusterResult],
        items: List[ClusterItem],
    ) -> str:
        """Format search results as text context for the LLM."""
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

    def _generate_conversation_id(self) -> str:
        return str(uuid.uuid4())
