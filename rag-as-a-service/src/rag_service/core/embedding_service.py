"""Embedding service — generate embeddings via OpenAI, Cohere, or local models."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Result of an embedding operation."""
    embeddings: list[list[float]]
    model: str
    token_count: int = 0


class EmbeddingService:
    """Generate embeddings via configurable provider."""

    def __init__(
        self,
        provider: str = "openai",
        model: str = "text-embedding-3-small",
        api_key: str = "",
        dimension: int = 1536,
        batch_size: int = 100,
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.dimension = dimension
        self.batch_size = batch_size

    async def embed_texts(self, texts: list[str]) -> EmbeddingResult:
        """Generate embeddings for a list of texts, batched for efficiency."""
        all_embeddings: list[list[float]] = []
        total_tokens = 0

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            result = await self._embed_batch(batch)
            all_embeddings.extend(result.embeddings)
            total_tokens += result.token_count

        return EmbeddingResult(
            embeddings=all_embeddings,
            model=self.model,
            token_count=total_tokens,
        )

    async def embed_query(self, query: str) -> list[float]:
        """Embed a single query string."""
        result = await self.embed_texts([query])
        return result.embeddings[0]

    async def _embed_batch(self, texts: list[str]) -> EmbeddingResult:
        """Call the embedding API for a batch of texts."""
        if self.provider == "openai":
            return await self._embed_openai(texts)
        elif self.provider == "cohere":
            return await self._embed_cohere(texts)
        else:
            return self._embed_local(texts)

    async def _embed_openai(self, texts: list[str]) -> EmbeddingResult:
        """Call OpenAI embeddings API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"input": texts, "model": self.model},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            embeddings = [item["embedding"] for item in data["data"]]
            token_count = data.get("usage", {}).get("total_tokens", 0)
            return EmbeddingResult(embeddings=embeddings, model=self.model, token_count=token_count)

    async def _embed_cohere(self, texts: list[str]) -> EmbeddingResult:
        """Call Cohere embeddings API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.cohere.ai/v1/embed",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "texts": texts,
                    "model": self.model,
                    "input_type": "search_document",
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return EmbeddingResult(
                embeddings=data["embeddings"],
                model=self.model,
                token_count=len(texts),
            )

    def _embed_local(self, texts: list[str]) -> EmbeddingResult:
        """Generate simple local embeddings (for testing/development)."""
        import hashlib

        embeddings = []
        for text in texts:
            # Deterministic pseudo-embedding based on text hash
            h = hashlib.sha256(text.encode()).digest()
            embedding = [float(b) / 255.0 for b in h]
            # Pad or truncate to dimension
            if len(embedding) < self.dimension:
                embedding.extend([0.0] * (self.dimension - len(embedding)))
            else:
                embedding = embedding[: self.dimension]
            embeddings.append(embedding)

        return EmbeddingResult(embeddings=embeddings, model="local", token_count=len(texts))
