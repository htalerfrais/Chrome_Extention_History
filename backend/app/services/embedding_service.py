from typing import List, Optional
import logging
import time

import httpx

from app.config import settings
from app.monitoring import get_request_id, metrics, calculate_embedding_cost

logger = logging.getLogger(__name__)

# Google batch API limit
BATCH_SIZE = 100


class EmbeddingService:

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
        self.embedding_dim = settings.embedding_dim

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        if not self.api_key:
            logger.warning("EmbeddingService: missing API key, returning empty vectors.")
            return [[] for _ in texts]

        vectors: List[List[float]] = []
        
        # Process in batches of BATCH_SIZE (Google limit: 100)
        for batch_start in range(0, len(texts), BATCH_SIZE):
            batch_texts = texts[batch_start:batch_start + BATCH_SIZE]
            batch_vectors = await self._embed_batch(batch_texts)
            vectors.extend(batch_vectors)

        if len(vectors) != len(texts):
            logger.warning(
                "EmbeddingService: vector count mismatch (expected %s, got %s)",
                len(texts),
                len(vectors),
            )
            while len(vectors) < len(texts):
                vectors.append([])
            vectors = vectors[:len(texts)]

        return vectors

    async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Internal method: embed a batch of texts in a single API call.
        Uses Google's batchEmbedContents endpoint.
        """
        start = time.perf_counter()
        
        # Build batch request
        # Format: {"requests": [{"model": "...", "content": {"parts": [{"text": "..."}]}}]}
        url = f"{self.base_url}/models/{self.model}:batchEmbedContents"
        params = {"key": self.api_key}
        
        requests_payload = [
            {
                "model": f"models/{self.model}",
                "content": {"parts": [{"text": text}]},
                "outputDimensionality": self.embedding_dim
            }
            for text in texts
        ]
        payload = {"requests": requests_payload}
        
        total_chars = sum(len(t) for t in texts)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, params=params, json=payload)
                
                duration_ms = (time.perf_counter() - start) * 1000
                
                if response.status_code != 200:
                    error_body = response.text
                    logger.error(
                        "embedding_batch_failed",
                        extra={
                            "request_id": get_request_id(),
                            "status_code": response.status_code,
                            "error": error_body[:200]
                        }
                    )
                    return [[] for _ in texts]
                
                response.raise_for_status()
                data = response.json()
                
                embeddings = data.get("embeddings", [])
                
                vectors: List[List[float]] = []
                failures = 0
                for i, emb in enumerate(embeddings):
                    values = emb.get("values", [])
                    if isinstance(values, list) and len(values) > 0:
                        vectors.append([float(x) for x in values])
                    else:
                        failures += 1
                        vectors.append([])
                
                # Calculate embedding cost
                cost = calculate_embedding_cost(
                    provider=settings.embedding_provider,
                    model=self.model,
                    text_count=len(texts)
                )
                
                # Log batch completion
                logger.info(
                    "embedding_batch",
                    extra={
                        "request_id": get_request_id(),
                        "texts_count": len(texts),
                        "total_chars": total_chars,
                        "duration_ms": round(duration_ms, 2),
                        "vectors_returned": len(vectors),
                        "failures": failures,
                        "cost_estimate_usd": round(cost, 6)
                    }
                )
                
                # Record to metrics
                metrics.record_embedding(
                    batch_size=len(texts),
                    failures=failures,
                    duration_ms=duration_ms
                )
                
                return vectors
                
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "embedding_batch_exception",
                extra={
                    "request_id": get_request_id(),
                    "texts_count": len(texts),
                    "duration_ms": round(duration_ms, 2),
                    "error": str(exc)
                }
            )
            return [[] for _ in texts]
