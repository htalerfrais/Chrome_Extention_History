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

        url = f"{self.base_url}/models/{self.model}:embedText"
        params = {"key": self.api_key}
        payload = {"requests": [{"input": text} for text in texts]}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, params=params, json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            logger.error(f"EmbeddingService request failed: {exc}")
            return [[] for _ in texts]

        vectors: List[List[float]] = []
        for item in data.get("embeddings", []):
            values = None
            if isinstance(item, dict):
                values = item.get("values")
                if values is None and isinstance(item.get("embedding"), dict):
                    values = item["embedding"].get("values")
            if isinstance(values, list):
                vectors.append([float(x) for x in values])

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

