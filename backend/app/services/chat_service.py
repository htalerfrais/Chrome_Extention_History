import asyncio
import time
from typing import List, Optional
from datetime import datetime
import uuid
import logging

from app.config import settings
from ..models.chat_models import ChatRequest, ChatResponse, SourceItem
from ..models.tool_models import ConversationMessage, ToolAugmentedRequest, ToolAugmentedResponse
from ..tools.registry import ToolRegistry
from .llm_service import LLMService
from .user_service import UserService
from ..monitoring import get_request_id, metrics, calculate_llm_cost

logger = logging.getLogger(__name__)


class ChatService:

    def __init__(
        self,
        llm_service: LLMService,
        tool_registry: ToolRegistry,
        user_service: UserService,
    ):
        self.llm_service = llm_service
        self.tool_registry = tool_registry
        self.user_service = user_service

    # ── Public entry point ────────────────────────────────────────────

    async def process_message(self, request: ChatRequest) -> ChatResponse:
        request_start = time.perf_counter()
        
        try:
            conversation_id = request.conversation_id or self._generate_conversation_id()
            messages = self._build_messages(request)
            all_sources: List[SourceItem] = []
            
            # Truncate message for logging if verbosity is disabled
            user_message_display = request.message
            if not settings.chat_log_full_prompts and len(request.message) > 100:
                user_message_display = request.message[:100] + "..."

            # Log request start
            logger.info(
                "chat_request_start",
                extra={
                    "request_id": get_request_id(),
                    "conversation_id": conversation_id,
                    "user_message": user_message_display,
                    "history_length": len(request.history or []),
                    "provider": request.provider
                }
            )

            # Resolve user_id once (needed for search tool)
            user_id: Optional[int] = None
            if request.user_token:
                user_dict = await self.user_service.get_user_from_token(request.user_token)
                if user_dict:
                    user_id = user_dict["id"]

            # Only offer tools if we have a valid user
            tools = self.tool_registry.get_definitions() if user_id else []

            # Track tokens across all iterations
            total_tokens_in = 0
            total_tokens_out = 0
            tool_calls_made: List[str] = []
            
            # Agentic loop: LLM can request tools, we execute and feed back
            response: Optional[ToolAugmentedResponse] = None
            final_iteration = 0

            for iteration in range(settings.chat_max_tool_iterations):
                iteration_start = time.perf_counter()
                final_iteration = iteration + 1
                
                response = await self.llm_service.generate_with_tools(
                    ToolAugmentedRequest(
                        messages=messages,
                        tools=tools,
                        provider=request.provider,
                        max_tokens=settings.chat_max_tokens,
                        temperature=settings.chat_temperature,
                    )
                )
                
                iteration_duration_ms = (time.perf_counter() - iteration_start) * 1000
                
                # Extract token usage
                usage = response.usage or {}
                if response.provider == "google":
                    iter_tokens_in = usage.get('promptTokenCount', 0)
                    iter_tokens_out = usage.get('candidatesTokenCount', 0)
                elif response.provider == "openai":
                    iter_tokens_in = usage.get('prompt_tokens', 0)
                    iter_tokens_out = usage.get('completion_tokens', 0)
                else:
                    iter_tokens_in = usage.get('total_tokens', 0)
                    iter_tokens_out = 0
                
                total_tokens_in += iter_tokens_in
                total_tokens_out += iter_tokens_out

                # Log iteration completion
                logger.info(
                    "chat_iteration_complete",
                    extra={
                        "request_id": get_request_id(),
                        "conversation_id": conversation_id,
                        "iteration": iteration + 1,
                        "duration_ms": round(iteration_duration_ms, 2),
                        "has_tool_calls": bool(response.tool_calls),
                        "tool_calls_count": len(response.tool_calls) if response.tool_calls else 0,
                        "tool_names": [tc.name for tc in response.tool_calls] if response.tool_calls else [],
                        "tokens_in": iter_tokens_in,
                        "tokens_out": iter_tokens_out
                    }
                )

                # No tool calls means the model produced a final answer
                if not response.tool_calls:
                    # Log final response
                    response_preview = response.text or ""
                    if not settings.chat_log_full_prompts and len(response_preview) > 200:
                        response_preview = response_preview[:200] + "..."
                    
                    logger.info(
                        "chat_final_response",
                        extra={
                            "request_id": get_request_id(),
                            "conversation_id": conversation_id,
                            "total_iterations": iteration + 1,
                            "response_preview": response_preview
                        }
                    )
                    break

                # Append assistant message containing the tool calls
                messages.append(ConversationMessage(
                    role="assistant",
                    content=response.text,
                    tool_calls=response.tool_calls,
                ))

                # Log each tool call
                for idx, tool_call in enumerate(response.tool_calls):
                    tool_calls_made.append(tool_call.name)
                    logger.info(
                        "chat_tool_call",
                        extra={
                            "request_id": get_request_id(),
                            "conversation_id": conversation_id,
                            "iteration": iteration + 1,
                            "tool_index": idx,
                            "tool_name": tool_call.name,
                            "tool_arguments": tool_call.arguments
                        }
                    )

                # Execute all tool calls in parallel via registry
                tool_tasks = [
                    self.tool_registry.execute(tc, user_id)
                    for tc in response.tool_calls
                ]
                results = await asyncio.gather(*tool_tasks)

                # Append each tool result as a separate message & collect sources
                for idx, (tool_result, source_dicts) in enumerate(results):
                    messages.append(ConversationMessage(
                        role="tool",
                        content=tool_result.content,
                        tool_call_id=tool_result.call_id,
                    ))
                    # Map generic source dicts to SourceItem
                    for sd in source_dicts:
                        all_sources.append(SourceItem(
                            url=sd.get("url", ""),
                            title=sd.get("title", "Untitled"),
                            visit_time=sd.get("visit_time", datetime.now()),
                            url_hostname=sd.get("url_hostname"),
                        ))
                    
                    # Log tool result
                    result_preview = tool_result.content
                    if not settings.chat_log_full_tool_responses and len(result_preview) > 300:
                        result_preview = result_preview[:300] + "..."
                    
                    logger.info(
                        "chat_tool_result",
                        extra={
                            "request_id": get_request_id(),
                            "conversation_id": conversation_id,
                            "iteration": iteration + 1,
                            "tool_index": idx,
                            "tool_call_id": tool_result.call_id,
                            "sources_count": len(source_dicts),
                            "result_preview": result_preview
                        }
                    )

            # Calculate total duration and cost
            total_duration_ms = (time.perf_counter() - request_start) * 1000
            estimated_cost = calculate_llm_cost(
                response.provider if response else request.provider,
                response.model if response else "",
                total_tokens_in,
                total_tokens_out
            )

            # Log chat request complete
            logger.info(
                "chat_request_complete",
                extra={
                    "request_id": get_request_id(),
                    "conversation_id": conversation_id,
                    "total_iterations": final_iteration,
                    "total_sources": len(all_sources),
                    "total_duration_ms": round(total_duration_ms, 2),
                    "tokens_in": total_tokens_in,
                    "tokens_out": total_tokens_out,
                    "tokens_total": total_tokens_in + total_tokens_out,
                    "cost_estimate_usd": round(estimated_cost, 6),
                    "provider": response.provider if response else request.provider,
                    "model": response.model if response else ""
                }
            )
            
            # Record to metrics
            metrics.record_chat_completion(
                turns=final_iteration,
                tool_calls=tool_calls_made,
                duration_ms=total_duration_ms
            )

            chat_response = ChatResponse(
                response=(response.text if response else "") or "",
                conversation_id=conversation_id,
                timestamp=datetime.now(),
                provider=response.provider if response else request.provider,
                model=response.model if response else "",
                sources=all_sources or None,
            )

            return chat_response

        except Exception as e:
            logger.error(
                "chat_request_failed",
                extra={
                    "request_id": get_request_id(),
                    "error": str(e)
                }
            )
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

    def _generate_conversation_id(self) -> str:
        return str(uuid.uuid4())
