import os
import httpx
from typing import Optional
import logging

from .base_provider import LLMProviderInterface
from ...models.llm_models import LLMRequest, LLMResponse

logger = logging.getLogger(__name__)

class GoogleProvider(LLMProviderInterface):
    """Google Gemini provider implementation"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.base_url = base_url or "https://generativelanguage.googleapis.com/v1beta"
        
        if not self.api_key:
            logger.warning("Google API key not provided")
    
    def get_default_model(self) -> str:
        return "gemini-2.5-pro"
    
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
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                # Debug: Log the full API response to see what Gemini returns
                logger.debug(f"Google API full response: {data}")
                
                # Log model and usage info if available
                if "model" in data:
                    logger.info(f"🤖 Using model: {data['model']}")
                if "usageMetadata" in data:
                    usage = data["usageMetadata"]
                    logger.info(f"📊 Token usage - Prompt: {usage.get('promptTokenCount', 'N/A')}, Response: {usage.get('candidatesTokenCount', 'N/A')}")
                
                # Extract generated text from Gemini response
                generated_text = ""  # Initialize default value
                
                if "candidates" in data and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    logger.debug(f"Google candidate structure: {candidate}")
                    
                    # Check if there's text in the candidate
                    if "content" in candidate:
                        content = candidate["content"]
                        logger.debug(f"Content structure: {content}")
                        
                        # Check for blocked content or other issues
                        finish_reason = candidate.get("finishReason", "UNKNOWN")
                        logger.info(f"Candidate finish reason: {finish_reason}")
                        
                        # Check if content was blocked or filtered
                        if finish_reason in ["SAFETY", "RECITATION", "OTHER"]:
                            logger.warning(f"Gemini blocked content. Reason: {finish_reason}")
                            generated_text = ""
                        elif finish_reason == "MAX_TOKENS":
                            logger.warning(f"Gemini response truncated due to token limit. Reason: {finish_reason}")
                            # Still try to extract text even if truncated
                        elif finish_reason != "STOP":
                            logger.warning(f"Gemini finished unexpectedly. Reason: {finish_reason}")
                            generated_text = ""
                        
                        # Look for parts array for all non-blocked cases
                        if "parts" in content and isinstance(content["parts"], list) and len(content["parts"]) > 0:
                            if "text" in content["parts"][0]:
                                extracted_text = content["parts"][0]["text"]
                                generated_text = extracted_text
                                logger.debug(f"Extracted text from Gemini: '{extracted_text}'")
                                if finish_reason == "MAX_TOKENS":
                                    logger.info(f"Using truncated response with {len(extracted_text)} characters")
                            else:
                                generated_text = ""
                                logger.warning(f"No text field in Gemini parts[0]: {content['parts'][0]}")
                        elif generated_text == "":
                            logger.warning(f"No valid parts array in Gemini content: {content}")
                    else:
                        generated_text = ""
                        logger.warning(f"No content field in Gemini candidate: {candidate}")
                else:
                    generated_text = ""
                    logger.warning(f"No candidates found in Gemini response: {data}")
                
                # Extract usage information if available
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
