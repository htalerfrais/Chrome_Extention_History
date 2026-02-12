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

class GoogleProvider(LLMProviderInterface):
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        self.api_key = api_key or settings.google_api_key
        self.base_url = base_url or settings.google_base_url
        
        if not self.api_key:
            logger.warning("Google API key not provided")
    
    def get_default_model(self) -> str:
        return settings.default_model
    
    def validate_request(self, request: LLMRequest) -> bool:
        return request.provider == "google"
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        if not self.api_key:
            raise ValueError("Google API key is required")
        
        model = request.model or self.get_default_model()
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": request.prompt
                }]
            }],
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            }
        }
        
        # Add any additional parameters
        if request.additional_params:
            payload["generationConfig"].update(request.additional_params)
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/models/{model}:generateContent?key={self.api_key}",
                    json=payload,
                    headers=headers,
                    timeout=settings.api_timeout
                )
                response.raise_for_status()
                data = response.json()
                
                logger.debug(f"🔍 Google API response: {data}")
                
                if "usageMetadata" in data:
                    usage = data["usageMetadata"]
                    logger.info(f"📊 Token usage - Prompt: {usage.get('promptTokenCount', 'N/A')}, Response: {usage.get('candidatesTokenCount', 'N/A')}")
                
                # Extract generated text from Gemini response
                generated_text = ""
                
                if "candidates" in data and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    
                    if "content" in candidate:
                        content = candidate["content"]
                        finish_reason = candidate.get("finishReason", "UNKNOWN")
                        
                        if finish_reason in ["SAFETY", "RECITATION", "OTHER"]:
                            generated_text = ""
                        elif finish_reason == "MAX_TOKENS":
                            # Still try to extract text even if truncated
                            pass
                        elif finish_reason != "STOP":
                            generated_text = ""
                        
                        if "parts" in content and isinstance(content["parts"], list) and len(content["parts"]) > 0:
                            if "text" in content["parts"][0]:
                                generated_text = content["parts"][0]["text"]
                
                usage = None
                if "usageMetadata" in data:
                    usage = data["usageMetadata"]
                
                return LLMResponse(
                    generated_text=generated_text,
                    provider="google",
                    model=model,
                    usage=usage,
                    metadata={"response_id": data.get("model")}
                )
                
        except httpx.HTTPError as e:
            logger.error(f"Google API error: {e}")
            raise Exception(f"Google API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in Google provider: {e}")
            raise

    # ── Function calling ──────────────────────────────────────────────

    async def generate_with_tools(self, request: ToolAugmentedRequest) -> ToolAugmentedResponse:
        if not self.api_key:
            raise ValueError("Google API key is required")

        model = request.model or self.get_default_model()

        # Build payload
        system_instruction, contents = self._build_google_contents(request.messages)
        tools_payload = self._build_google_tools(request.tools)

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            },
        }
        if system_instruction:
            payload["system_instruction"] = system_instruction
        if tools_payload:
            payload["tools"] = tools_payload

        headers = {"Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/models/{model}:generateContent?key={self.api_key}",
                    json=payload,
                    headers=headers,
                    timeout=settings.api_timeout,
                )
                response.raise_for_status()
                data = response.json()

            logger.debug(f"Google tool response: {data}")

            usage = data.get("usageMetadata")
            return self._parse_google_tool_response(data, model, usage)

        except httpx.HTTPError as e:
            logger.error(f"Google API error (tools): {e}")
            raise Exception(f"Google API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in Google provider (tools): {e}")
            raise

    # ── Google-specific formatting helpers ─────────────────────────────

    def _build_google_tools(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """Convert provider-agnostic ToolDefinitions to Google functionDeclarations."""
        if not tools:
            return []
        declarations = []
        for tool in tools:
            declarations.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            })
        return [{"functionDeclarations": declarations}]

    def _build_google_contents(
        self, messages: List[ConversationMessage]
    ) -> tuple:
        """Convert ConversationMessages to Google contents array + optional system_instruction.
        
        Returns:
            (system_instruction_dict | None, contents_list)
        """
        system_instruction = None
        contents: List[Dict[str, Any]] = []

        for msg in messages:
            if msg.role == "system":
                # Google uses a top-level system_instruction field
                system_instruction = {"parts": [{"text": msg.content or ""}]}

            elif msg.role == "user":
                contents.append({
                    "role": "user",
                    "parts": [{"text": msg.content or ""}],
                })

            elif msg.role == "assistant":
                parts: List[Dict[str, Any]] = []
                # Include text if present
                if msg.content:
                    parts.append({"text": msg.content})
                # Include function calls if present
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        parts.append({
                            "functionCall": {
                                "name": tc.name,
                                "args": tc.arguments,
                            }
                        })
                if parts:
                    contents.append({"role": "model", "parts": parts})

            elif msg.role == "tool":
                # Google expects functionResponse inside a user-role message
                # Parse the tool_call_id to recover the function name
                # We encode name in tool_call_id as "call_{index}_{name}"
                func_name = self._extract_func_name_from_call_id(msg.tool_call_id or "")
                response_data = msg.content or ""
                # Try to parse as JSON for structured response
                try:
                    response_obj = json.loads(response_data)
                except (json.JSONDecodeError, TypeError):
                    response_obj = {"result": response_data}

                contents.append({
                    "role": "user",
                    "parts": [{
                        "functionResponse": {
                            "name": func_name,
                            "response": response_obj,
                        }
                    }],
                })

        return system_instruction, contents

    def _extract_func_name_from_call_id(self, call_id: str) -> str:
        """Extract function name from synthetic call ID format 'call_{index}_{name}'."""
        parts = call_id.split("_", 2)
        if len(parts) >= 3:
            return parts[2]
        return call_id

    def _parse_google_tool_response(
        self, data: dict, model: str, usage: Any
    ) -> ToolAugmentedResponse:
        """Parse Google generateContent response into ToolAugmentedResponse."""
        tool_calls: List[ToolCall] = []
        text_parts: List[str] = []

        if "candidates" in data and len(data["candidates"]) > 0:
            candidate = data["candidates"][0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])

            for idx, part in enumerate(parts):
                if "functionCall" in part:
                    fc = part["functionCall"]
                    tool_calls.append(ToolCall(
                        id=f"call_{idx}_{fc.get('name', 'unknown')}",
                        name=fc.get("name", ""),
                        arguments=fc.get("args", {}),
                    ))
                elif "text" in part:
                    text_parts.append(part["text"])

        return ToolAugmentedResponse(
            text="\n".join(text_parts) if text_parts else None,
            tool_calls=tool_calls,
            provider="google",
            model=model,
            usage=usage,
        )
