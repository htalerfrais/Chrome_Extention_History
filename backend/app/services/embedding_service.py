from typing import List, Optional
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Google batch API limit
BATCH_SIZE = 100


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
        """
        Embed multiple texts using Google's batch API.
        
        Interface unchanged - ClusteringService doesn't need to know about batching.
        Internally uses batchEmbedContents for efficiency.
        """
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

        # Ensure result length matches input length
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
        # Build batch request
        # Format: {"requests": [{"model": "...", "content": {"parts": [{"text": "..."}]}}]}
        url = f"{self.base_url}/models/{self.model}:batchEmbedContents"
        params = {"key": self.api_key}
        
        requests_payload = [
            {
                "model": f"models/{self.model}",
                "content": {"parts": [{"text": text}]}
            }
            for text in texts
        ]
        payload = {"requests": requests_payload}
        
        logger.info(f"📤 Batch embedding {len(texts)} texts in single request")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, params=params, json=payload)
                
                if response.status_code != 200:
                    error_body = response.text
                    logger.error(f"EmbeddingService: API returned {response.status_code} - {error_body}")
                    return [[] for _ in texts]
                
                response.raise_for_status()
                data = response.json()
                
                # Response format: {"embeddings": [{"values": [...]}, ...]}
                embeddings = data.get("embeddings", [])
                
                vectors: List[List[float]] = []
                for i, emb in enumerate(embeddings):
                    values = emb.get("values", [])
                    if isinstance(values, list) and len(values) > 0:
                        vectors.append([float(x) for x in values])
                    else:
                        logger.warning(f"EmbeddingService: invalid embedding at index {i}")
                        vectors.append([])
                
                logger.info(f"✅ Received {len(vectors)} embeddings from batch request")
                return vectors
                
        except Exception as exc:
            logger.error(f"EmbeddingService batch request failed: {exc}")
            return [[] for _ in texts]
