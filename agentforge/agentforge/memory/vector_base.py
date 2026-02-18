"""Vector store base classes for AgentForge.

This module provides abstract base classes for vector store implementations,
enabling semantic search and similarity-based retrieval for long-term memory.

The vector store architecture supports:
- Pluggable backends (in-memory, Qdrant, ChromaDB, etc.)
- Semantic search with metadata filtering
- Batch operations for efficiency
- Optional content storage alongside vectors
"""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


def _utc_now_iso() -> str:
    """Get current UTC time as ISO format string."""
    return datetime.now(UTC).isoformat()


class VectorEntry(BaseModel):
    """A single entry in the vector store.

    Represents a vector embedding with associated metadata and optional
    original content. Used for inserting new entries into the vector store.

    Attributes:
        id: Unique identifier for this entry.
        vector: The embedding vector (list of floats).
        metadata: Optional additional information (e.g., source, tags).
        content: Optional original text content that was embedded.
        created_at: ISO timestamp when the entry was created.
    """

    id: str
    vector: list[float]
    metadata: dict[str, Any] = Field(default_factory=dict)
    content: Optional[str] = None
    created_at: Optional[str] = Field(default_factory=_utc_now_iso)


class VectorSearchResult(BaseModel):
    """Result from a vector similarity search.

    Represents a single match from a vector search operation,
    including the entry ID, similarity score, and associated data.

    Attributes:
        id: Unique identifier of the matched entry.
        score: Similarity score (typically 0.0 to 1.0 for cosine similarity).
        metadata: Metadata associated with the matched entry.
        content: Original text content if available.
    """

    id: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)
    content: Optional[str] = None


class VectorStore(ABC):
    """Abstract base class for vector stores.

    Defines the interface that all vector store implementations must follow.
    Vector stores handle storage and similarity search of embedding vectors,
    enabling semantic retrieval for long-term memory.

    Subclasses must implement all abstract methods. The batch operations
    have default implementations that loop over single operations, but
    can be overridden for efficiency.

    Example:
        ```python
        class MyVectorStore(VectorStore):
            async def insert(self, entry: VectorEntry) -> str:
                # Store the vector entry
                ...

            async def search(self, query_vector, top_k=5, filter_metadata=None):
                # Find similar vectors
                ...

        # Usage
        store = MyVectorStore()
        entry = VectorEntry(
            id="doc1",
            vector=[0.1, 0.2, 0.3, ...],
            content="Hello world",
            metadata={"source": "greeting"}
        )
        await store.insert(entry)
        results = await store.search(query_vector, top_k=5)
        ```
    """

    @abstractmethod
    async def insert(self, entry: VectorEntry) -> str:
        """Insert a vector entry into the store.

        Args:
            entry: The vector entry to insert.

        Returns:
            The ID of the inserted entry.

        Raises:
            ValueError: If the vector dimension doesn't match the store's dimension.
        """
        ...

    @abstractmethod
    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filter_metadata: Optional[dict[str, Any]] = None,
    ) -> list[VectorSearchResult]:
        """Search for similar vectors.

        Args:
            query_vector: The query embedding vector.
            top_k: Maximum number of results to return.
            filter_metadata: Optional metadata filters (key-value pairs that
                must match exactly in the result's metadata).

        Returns:
            List of search results sorted by similarity (descending).
        """
        ...

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete an entry by ID.

        Args:
            id: The unique identifier of the entry to delete.

        Returns:
            True if the entry was deleted, False if it didn't exist.
        """
        ...

    @abstractmethod
    async def get(self, id: str) -> Optional[VectorEntry]:
        """Get an entry by ID.

        Args:
            id: The unique identifier of the entry.

        Returns:
            The vector entry, or None if not found.
        """
        ...

    @abstractmethod
    async def count(self) -> int:
        """Count total entries in the store.

        Returns:
            The number of stored entries.
        """
        ...

    async def insert_batch(self, entries: list[VectorEntry]) -> list[str]:
        """Insert multiple entries.

        Default implementation loops over single inserts. Override for
        efficient batch operations in specific backends.

        Args:
            entries: List of vector entries to insert.

        Returns:
            List of inserted entry IDs.
        """
        return [await self.insert(entry) for entry in entries]

    async def delete_batch(self, ids: list[str]) -> list[bool]:
        """Delete multiple entries by ID.

        Default implementation loops over single deletes. Override for
        efficient batch operations in specific backends.

        Args:
            ids: List of entry IDs to delete.

        Returns:
            List of deletion success flags.
        """
        return [await self.delete(id) for id in ids]

    async def exists(self, id: str) -> bool:
        """Check if an entry exists.

        Args:
            id: The unique identifier to check.

        Returns:
            True if the entry exists.
        """
        return await self.get(id) is not None

    async def update_metadata(self, id: str, metadata: dict[str, Any]) -> bool:
        """Update metadata for an existing entry.

        Default implementation retrieves, modifies, and re-inserts.
        Override for more efficient backend-specific implementations.

        Args:
            id: The unique identifier of the entry.
            metadata: New metadata (merged with existing).

        Returns:
            True if updated, False if entry not found.
        """
        entry = await self.get(id)
        if entry is None:
            return False
        entry.metadata.update(metadata)
        await self.insert(entry)  # Re-insert with updated metadata
        return True


__all__ = [
    "VectorEntry",
    "VectorSearchResult",
    "VectorStore",
]
