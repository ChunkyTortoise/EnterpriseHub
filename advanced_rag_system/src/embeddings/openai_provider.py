"""OpenAI embedding provider implementation.

Provides production-ready embedding generation using OpenAI's API
with batching, retries, and comprehensive error handling.
"""

from __future__ import annotations

import asyncio
from typing import List, Optional

import openai
from openai import AsyncOpenAI

from src.core.config import get_settings
from src.core.exceptions import EmbeddingError, RateLimitError
from src.embeddings.base import EmbeddingConfig, EmbeddingProvider


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider with batching and retry logic.

    This provider uses OpenAI's embedding API with the following features:
    - Automatic batching for optimal throughput
    - Exponential backoff retry logic
    - Rate limit handling
    - Connection pooling

    Example:
        ```python
        config = EmbeddingConfig(
            model="text-embedding-3-small",
            dimensions=1536,
            batch_size=100
        )
        provider = OpenAIEmbeddingProvider(config)
        await provider.initialize()

        embeddings = await provider.embed(["Hello world", "Test text"])
        await provider.close()
        ```
    """

    def __init__(
        self,
        config: Optional[EmbeddingConfig] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        """Initialize the OpenAI embedding provider.

        Args:
            config: Embedding configuration
            api_key: OpenAI API key (falls back to settings/env)
            base_url: Custom base URL for OpenAI API
        """
        super().__init__(config)
        settings = get_settings()

        self._api_key = api_key or settings.get_openai_api_key()
        self._base_url = base_url or settings.openai_base_url
        self._client: Optional[AsyncOpenAI] = None
        self._semaphore: Optional[asyncio.Semaphore] = None

    async def initialize(self) -> None:
        """Initialize the OpenAI client.

        Creates the async HTTP client with connection pooling.
        """
        if self._client is not None:
            return

        settings = get_settings()

        self._client = AsyncOpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
            timeout=self.config.timeout_seconds,
            max_retries=0,  # We handle retries manually for better control
        )

        # Limit concurrent requests to avoid rate limiting
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_requests)
        self._initialized = True

    async def close(self) -> None:
        """Close the OpenAI client and release resources."""
        if self._client is not None:
            await self._client.close()
            self._client = None
        self._semaphore = None
        self._initialized = False

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts.

        Automatically batches large inputs and handles retries.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingError: If embedding generation fails
            RateLimitError: If rate limit is exceeded
        """
        self._ensure_initialized()
        self._validate_input(texts)

        # Process in batches if needed
        if len(texts) <= self.config.batch_size:
            return await self._embed_batch(texts)

        # Split into batches and process
        batches = self._create_batches(texts, self.config.batch_size)
        all_embeddings: List[List[float]] = []

        for batch in batches:
            batch_embeddings = await self._embed_batch(batch)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    async def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query.

        Args:
            text: Query text to embed

        Returns:
            Single embedding vector
        """
        embeddings = await self.embed([text])
        return embeddings[0]

    async def health_check(self) -> bool:
        """Check if the OpenAI API is accessible.

        Returns:
            True if the service is healthy
        """
        try:
            self._ensure_initialized()
            # Try to embed a simple test string
            await self._embed_batch_with_retry(["health check"], attempt=1)
            return True
        except Exception:
            return False

    async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts with retry logic.

        Args:
            texts: Batch of texts to embed

        Returns:
            List of embeddings
        """
        return await self._embed_batch_with_retry(texts, attempt=1)

    async def _embed_batch_with_retry(
        self,
        texts: List[str],
        attempt: int,
    ) -> List[List[float]]:
        """Embed with exponential backoff retry.

        Args:
            texts: Texts to embed
            attempt: Current retry attempt

        Returns:
            List of embeddings

        Raises:
            EmbeddingError: If all retries fail
            RateLimitError: If rate limited and retries exhausted
        """

        if self._semaphore is None or self._client is None:
            raise EmbeddingError(
                message="Provider not initialized",
                error_code="NOT_INITIALIZED",
            )

        async with self._semaphore:
            try:
                response = await self._client.embeddings.create(
                    model=self.config.model,
                    input=texts,
                    dimensions=self.config.dimensions,
                )

                # Extract embeddings in order
                embeddings = [item.embedding for item in response.data]

                # Normalize if configured
                if self.config.normalize:
                    embeddings = self._normalize_embeddings(embeddings)

                return embeddings

            except openai.RateLimitError as e:
                if attempt >= self.config.max_retries:
                    retry_after = self._extract_retry_after(e)
                    raise RateLimitError(
                        message="OpenAI rate limit exceeded",
                        details={"error": str(e)},
                        retry_after=retry_after,
                    )

                # Exponential backoff
                wait_time = 2**attempt
                await asyncio.sleep(wait_time)
                return await self._embed_batch_with_retry(texts, attempt + 1)

            except openai.APIError as e:
                if attempt >= self.config.max_retries:
                    raise EmbeddingError(
                        message=f"OpenAI API error: {e.message}",
                        details={"error": str(e)},
                        provider="openai",
                    )

                wait_time = 2**attempt
                await asyncio.sleep(wait_time)
                return await self._embed_batch_with_retry(texts, attempt + 1)

            except openai.APIConnectionError as e:
                if attempt >= self.config.max_retries:
                    raise EmbeddingError(
                        message="Failed to connect to OpenAI API",
                        details={"error": str(e)},
                        provider="openai",
                    )

                wait_time = 2**attempt
                await asyncio.sleep(wait_time)
                return await self._embed_batch_with_retry(texts, attempt + 1)

            except Exception as e:
                raise EmbeddingError(
                    message=f"Unexpected error during embedding: {str(e)}",
                    details={"error": str(e)},
                    provider="openai",
                )

    def _create_batches(self, texts: List[str], batch_size: int) -> List[List[str]]:
        """Split texts into batches.

        Args:
            texts: All texts to batch
            batch_size: Maximum batch size

        Returns:
            List of batches
        """
        return [texts[i : i + batch_size] for i in range(0, len(texts), batch_size)]

    def _extract_retry_after(self, error: openai.RateLimitError) -> Optional[int]:
        """Extract retry-after header from rate limit error.

        Args:
            error: Rate limit error

        Returns:
            Seconds to wait, or None if not available
        """
        if hasattr(error, "response") and error.response is not None:
            headers = getattr(error.response, "headers", {})
            retry_after = headers.get("retry-after")
            if retry_after:
                try:
                    return int(retry_after)
                except (ValueError, TypeError):
                    pass
        return None

    def _ensure_initialized(self) -> None:
        """Ensure the provider is initialized.

        Raises:
            EmbeddingError: If not initialized
        """
        if not self._initialized or self._client is None:
            raise EmbeddingError(
                message="Provider not initialized. Call initialize() first.",
                error_code="NOT_INITIALIZED",
            )
