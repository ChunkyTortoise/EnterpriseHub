"""Abstract base class for vector stores.

Defines the interface that all vector store implementations must follow,
ensuring consistent behavior across different backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID

from src.core.types import DocumentChunk, SearchResult


@dataclass
class VectorStoreConfig:
    """Configuration for vector stores.

    Attributes:
        collection_name: Default collection name
        dimension: Vector dimensionality
        distance_metric: Distance metric (cosine, euclidean, dot)
        metadata_schema: Optional schema for metadata validation
    """

    collection_name: str = "default"
    dimension: int = 1536
    distance_metric: str = "cosine"
    metadata_schema: Optional[Dict[str, Any]] = None


@dataclass
class SearchOptions:
    """Options for vector search operations.

    Attributes:
        top_k: Number of results to return
        threshold: Minimum similarity threshold
        filters: Metadata filters
        include_embeddings: Whether to include embeddings in results
        include_metadata: Whether to include metadata in results
    """

    top_k: int = 10
    threshold: float = 0.0
    filters: Optional[Dict[str, Any]] = None
    include_embeddings: bool = False
    include_metadata: bool = True


class VectorStore(ABC):
    """Abstract base class for vector stores.

    All vector store implementations must inherit from this class
    and implement the required methods for CRUD operations and search.

    Example:
        ```python
        store = ChromaVectorStore(config)
        await store.initialize()

        # Add chunks
        await store.add_chunks([chunk1, chunk2])

        # Search
        results = await store.search(embedding, SearchOptions(top_k=5))
        ```
    """

    def __init__(self, config: Optional[VectorStoreConfig] = None) -> None:
        """Initialize the vector store.

        Args:
            config: Vector store configuration
        """
        self.config = config or VectorStoreConfig()
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the vector store connection.

        This method should establish connections, create collections,
        and prepare the store for operations.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the vector store connection and release resources."""
        pass

    @abstractmethod
    async def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Add document chunks to the vector store.

        Args:
            chunks: List of document chunks to add

        Raises:
            VectorStoreError: If operation fails
        """
        pass

    @abstractmethod
    async def delete_chunks(self, chunk_ids: List[UUID]) -> None:
        """Delete chunks by their IDs.

        Args:
            chunk_ids: List of chunk IDs to delete

        Raises:
            VectorStoreError: If operation fails
        """
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        options: Optional[SearchOptions] = None,
    ) -> List[SearchResult]:
        """Search for similar vectors.

        Args:
            query_embedding: Query vector
            options: Search options

        Returns:
            List of search results

        Raises:
            VectorStoreError: If search fails
        """
        pass

    @abstractmethod
    async def get_chunk(self, chunk_id: UUID) -> Optional[DocumentChunk]:
        """Get a specific chunk by ID.

        Args:
            chunk_id: Chunk ID

        Returns:
            Document chunk or None if not found
        """
        pass

    @abstractmethod
    async def update_chunk(self, chunk: DocumentChunk) -> None:
        """Update an existing chunk.

        Args:
            chunk: Updated chunk data

        Raises:
            VectorStoreError: If chunk doesn't exist or update fails
        """
        pass

    @abstractmethod
    async def count(self) -> int:
        """Get the total number of chunks in the store.

        Returns:
            Total chunk count
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all chunks from the store."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the vector store is healthy.

        Returns:
            True if the store is accessible and operational
        """
        pass

    def _ensure_initialized(self) -> None:
        """Ensure the store is initialized.

        Raises:
            VectorStoreError: If not initialized
        """
        if not self._initialized:
            from src.core.exceptions import VectorStoreError

            raise VectorStoreError(
                message="Vector store not initialized. Call initialize() first.",
                error_code="NOT_INITIALIZED",
            )

    def _validate_embedding(self, embedding: List[float]) -> None:
        """Validate embedding vector dimensions.

        Args:
            embedding: Embedding vector to validate

        Raises:
            VectorStoreError: If dimensions don't match config
        """
        if len(embedding) != self.config.dimension:
            from src.core.exceptions import VectorStoreError

            raise VectorStoreError(
                message=f"Embedding dimension mismatch: expected {self.config.dimension}, got {len(embedding)}",
                error_code="DIMENSION_MISMATCH",
                details={
                    "expected": self.config.dimension,
                    "actual": len(embedding),
                },
            )

    def _chunk_to_dict(self, chunk: DocumentChunk) -> Dict[str, Any]:
        """Convert a DocumentChunk to a dictionary for storage.

        Args:
            chunk: Document chunk

        Returns:
            Dictionary representation
        """
        return {
            "id": str(chunk.id),
            "document_id": str(chunk.document_id),
            "content": chunk.content,
            "index": chunk.index,
            "token_count": chunk.token_count,
            "metadata": {
                "source": chunk.metadata.source,
                "title": chunk.metadata.title,
                "author": chunk.metadata.author,
                "language": chunk.metadata.language,
                "tags": chunk.metadata.tags,
                **chunk.metadata.custom,
            },
        }

    def _dict_to_chunk(
        self,
        data: Dict[str, Any],
        embedding: Optional[List[float]] = None,
    ) -> DocumentChunk:
        """Convert a dictionary back to a DocumentChunk.

        Args:
            data: Dictionary data
            embedding: Optional embedding vector

        Returns:
            DocumentChunk object
        """
        from src.core.types import Metadata

        metadata_data = data.get("metadata", {})
        metadata = Metadata(
            source=metadata_data.get("source"),
            title=metadata_data.get("title"),
            author=metadata_data.get("author"),
            language=metadata_data.get("language", "en"),
            tags=metadata_data.get("tags", []),
        )
        # Add custom fields
        known_fields = {"source", "title", "author", "language", "tags"}
        for key, value in metadata_data.items():
            if key not in known_fields:
                metadata.custom[key] = value

        return DocumentChunk(
            id=UUID(data.get("id")),
            document_id=UUID(data.get("document_id")),
            content=data.get("content", ""),
            embedding=embedding,
            metadata=metadata,
            index=data.get("index", 0),
            token_count=data.get("token_count", 0),
        )
