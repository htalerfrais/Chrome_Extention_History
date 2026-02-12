import os
import json
import httpx
from typing import Optional, List, Dict, Any
import logging

from app.config import settings
from .base_provider import LLMProviderInterface
from app.models.llm_models import LLMRequest, LLMResponse
from app.models.tool_models import (
    ToolAugmentedRequest, ToolAugmentedResponse,
    ToolDefinition, ToolCall, ConversationMessage,
)

logger = logging.getLogger(__name__)

class OpenAIProvider(LLMProviderInterface):
    """OpenAI GPT provider implementation"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        self.api_key = api_key or settings.openai_api_key
        self.base_url = base_url or settings.openai_base_url
        
        if not self.api_key:
            logger.warning("OpenAI API key not provided")
    
    def get_default_model(self) -> str:
        return "gpt-4.1-mini"  # Updated to current recommended model
    
    def validate_request(self, request: LLMRequest) -> bool:
        return request.provider == "openai"
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        model = request.model or self.get_default_model()
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": request.prompt}],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        
        # Add any additional parameters
        if request.additional_params:
            payload.update(request.additional_params)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"Sending request to OpenAI with model: {model}")
            logger.debug(f"OpenAI payload: {payload}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=settings.api_timeout
                )
                response.raise_for_status()
                data = response.json()
                
                logger.debug(f"OpenAI response received: {data}")
                
                generated_text = data["choices"][0]["message"]["content"]
                usage = data.get("usage")
                
                return LLMResponse(
                    generated_text=generated_text,
                    provider="openai",
                    model=model,
                    usage=usage,
                    metadata={"response_id": data.get("id")}
                )
                
        except httpx.HTTPError as e:
            logger.error(f"OpenAI API HTTP error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    logger.error(f"OpenAI API error details: {error_data}")
                except:
                    logger.error(f"OpenAI API raw response: {e.response.text}")
            raise Exception(f"OpenAI API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI provider: {e}")
            raise

    # ── Function calling ──────────────────────────────────────────────

    async def generate_with_tools(self, request: ToolAugmentedRequest) -> ToolAugmentedResponse:
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        model = request.model or self.get_default_model()

        messages = self._build_openai_messages(request.messages)
        tools_payload = self._build_openai_tools(request.tools)

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        if tools_payload:
            payload["tools"] = tools_payload

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=settings.api_timeout,
                )
                response.raise_for_status()
                data = response.json()

            logger.debug(f"OpenAI tool response: {data}")

            usage = data.get("usage")
            return self._parse_openai_tool_response(data, model, usage)

        except httpx.HTTPError as e:
            logger.error(f"OpenAI API error (tools): {e}")
            raise Exception(f"OpenAI API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI provider (tools): {e}")
            raise

    # ── OpenAI-specific formatting helpers ─────────────────────────────

    def _build_openai_tools(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """Convert provider-agnostic ToolDefinitions to OpenAI tools format."""
        if not tools:
            return []
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in tools
        ]

    def _build_openai_messages(self, messages: List[ConversationMessage]) -> List[Dict[str, Any]]:
        """Convert ConversationMessages to OpenAI messages array."""
        result: List[Dict[str, Any]] = []

        for msg in messages:
            if msg.role in ("system", "user"):
                result.append({"role": msg.role, "content": msg.content or ""})

            elif msg.role == "assistant":
                entry: Dict[str, Any] = {"role": "assistant"}
                if msg.content:
                    entry["content"] = msg.content
                if msg.tool_calls:
                    entry["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments),
                            },
                        }
                        for tc in msg.tool_calls
                    ]
                result.append(entry)

            elif msg.role == "tool":
                result.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id or "",
                    "content": msg.content or "",
                })

        return result

    def _parse_openai_tool_response(
        self, data: dict, model: str, usage: Any
    ) -> ToolAugmentedResponse:
        """Parse OpenAI chat completion response into ToolAugmentedResponse."""
        message = data["choices"][0]["message"]
        text = message.get("content")
        tool_calls: List[ToolCall] = []

        raw_calls = message.get("tool_calls") or []
        for tc in raw_calls:
            func = tc.get("function", {})
            # Parse arguments JSON string
            try:
                args = json.loads(func.get("arguments", "{}"))
            except (json.JSONDecodeError, TypeError):
                args = {}

            tool_calls.append(ToolCall(
                id=tc.get("id", ""),
                name=func.get("name", ""),
                arguments=args,
            ))

        return ToolAugmentedResponse(
            text=text,
            tool_calls=tool_calls,
            provider="openai",
            model=model,
            usage=usage,
        )
