"""Abstract base class for embedding providers.

Defines the interface that all embedding providers must implement,
ensuring consistency across different embedding services.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Optional

from src.core.exceptions import EmbeddingError


@dataclass
class EmbeddingConfig:
    """Configuration for embedding providers.

    Attributes:
        model: Name of the embedding model
        dimensions: Vector dimensionality
        batch_size: Maximum batch size for requests
        max_retries: Maximum retry attempts
        timeout_seconds: Request timeout
        normalize: Whether to normalize embeddings
    """

    model: str = "text-embedding-3-small"
    dimensions: int = 1536
    batch_size: int = 100
    max_retries: int = 3
    timeout_seconds: float = 30.0
    normalize: bool = True


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers.

    All embedding providers must implement this interface to ensure
    consistent behavior across different embedding services (OpenAI,
    local models, etc.).

    Example:
        ```python
        provider = OpenAIEmbeddingProvider(config)
        embeddings = await provider.embed(["text1", "text2"])
        ```
    """

    def __init__(self, config: Optional[EmbeddingConfig] = None) -> None:
        """Initialize the embedding provider.

        Args:
            config: Provider configuration
        """
        self.config = config or EmbeddingConfig()
        self._initialized = False

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors, one per input text

        Raises:
            EmbeddingError: If embedding generation fails
        """
        pass

    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query.

        This is a convenience method that wraps embed() for single queries.
        Some providers may optimize this differently than batch embedding.

        Args:
            text: Query text to embed

        Returns:
            Single embedding vector

        Raises:
            EmbeddingError: If embedding generation fails
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the embedding service is healthy.

        Returns:
            True if the service is available and responsive
        """
        pass

    async def initialize(self) -> None:
        """Initialize the provider (optional override).

        This method can be overridden by providers that need
        async initialization (e.g., loading models, connecting
        to services).
        """
        self._initialized = True

    async def close(self) -> None:
        """Clean up resources (optional override).

        This method can be overridden by providers that need
        to release resources (e.g., close connections, unload models).
        """
        self._initialized = False

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the embedding model.

        Returns:
            Dictionary with model information
        """
        return {
            "model": self.config.model,
            "dimensions": self.config.dimensions,
            "batch_size": self.config.batch_size,
            "provider": self.__class__.__name__,
        }

    def _validate_input(self, texts: List[str]) -> None:
        """Validate input texts before embedding.

        Args:
            texts: List of texts to validate

        Raises:
            EmbeddingError: If input is invalid
        """
        if not texts:
            raise EmbeddingError(
                message="Empty text list provided",
                error_code="EMPTY_INPUT",
            )

        if len(texts) > self.config.batch_size:
            raise EmbeddingError(
                message=f"Batch size {len(texts)} exceeds maximum {self.config.batch_size}",
                error_code="BATCH_TOO_LARGE",
                details={"batch_size": len(texts), "max_batch_size": self.config.batch_size},
            )

        for i, text in enumerate(texts):
            if not text or not text.strip():
                raise EmbeddingError(
                    message=f"Empty text at index {i}",
                    error_code="EMPTY_TEXT",
                    details={"index": i},
                )

    def _normalize_embedding(self, embedding: List[float]) -> List[float]:
        """Normalize an embedding vector to unit length.

        Args:
            embedding: Raw embedding vector

        Returns:
            Normalized embedding vector
        """
        if not self.config.normalize:
            return embedding

        import math

        magnitude = math.sqrt(sum(x * x for x in embedding))
        if magnitude == 0:
            return embedding

        return [x / magnitude for x in embedding]

    def _normalize_embeddings(self, embeddings: List[List[float]]) -> List[List[float]]:
        """Normalize multiple embedding vectors.

        Args:
            embeddings: List of raw embedding vectors

        Returns:
            List of normalized embedding vectors
        """
        return [self._normalize_embedding(emb) for emb in embeddings]