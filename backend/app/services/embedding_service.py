from typing import List, Optional
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Minimal embedding client using Google Generative Language API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or settings.google_api_key
        self.base_url = (base_url or settings.google_base_url).rstrip("/")
        self.model = model or settings.embedding_model
        self.timeout = settings.api_timeout

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        if not self.api_key:
            logger.warning("EmbeddingService: missing API key, returning empty vectors.")
            return [[] for _ in texts]

        # Google Generative Language API: embedContent endpoint
        # Official format: POST /v1beta/models/{model}:embedContent
        # Request: {"content": {"parts": [{"text": "..."}]}}
        url = f"{self.base_url}/models/{self.model}:embedContent"
        params = {"key": self.api_key}
        
        vectors: List[List[float]] = []
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for text in texts:
                try:
                    payload = {"content": {"parts": [{"text": text}]}}
                    response = await client.post(url, params=params, json=payload)
                    
                    if response.status_code != 200:
                        error_body = response.text
                        logger.error(f"EmbeddingService: API returned {response.status_code} - {error_body}")
                        
                    response.raise_for_status()
                    data = response.json()
                    
                    # Google API returns: {"embedding": {"values": [...]}}
                    embedding_data = data.get("embedding", {})
                    values = embedding_data.get("values", [])
                    
                    if isinstance(values, list) and len(values) > 0:
                        vectors.append([float(x) for x in values])
                        logger.debug(f"EmbeddingService: generated embedding with {len(values)} dimensions")
                    else:
                        logger.warning(f"EmbeddingService: invalid embedding format for text: {text[:50]}...")
                        vectors.append([])
                        
                except Exception as exc:
                    logger.error(f"EmbeddingService request failed for text '{text[:50]}...': {exc}")
                    if hasattr(exc, 'response') and exc.response is not None:
                        try:
                            error_body = exc.response.text
                            logger.error(f"EmbeddingService: Error response body: {error_body}")
                        except:
                            pass
                    vectors.append([])

        # Ensure result length matches input length
        if len(vectors) != len(texts):
            logger.warning(
                "EmbeddingService: vector count mismatch (expected %s, got %s)",
                len(texts),
                len(vectors),
            )
            while len(vectors) < len(texts):
                vectors.append([])
            vectors = vectors[: len(texts)]

        return vectors

