"""Base memory provider definitions for AgentForge.

This module provides the abstract base class for all memory providers and
the fundamental data structures used throughout the memory system.
"""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(UTC)


class MemoryEntry(BaseModel):
    """A single memory entry.

    Represents a key-value pair stored in memory with optional metadata
    and timestamps for tracking creation and modification.

    Attributes:
        key: Unique identifier for this memory entry.
        value: The stored value (can be any JSON-serializable type).
        metadata: Optional additional information about the entry.
        created_at: Timestamp when the entry was created.
        updated_at: Timestamp when the entry was last modified.
    """

    key: str
    value: Any
    metadata: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)


class SearchResult(BaseModel):
    """Result from a memory search operation.

    Represents a single match from a semantic or keyword search,
    including the matched entry and a relevance score.

    Attributes:
        entry: The matched memory entry.
        score: Relevance score (0.0 to 1.0, where 1.0 is exact match).
    """

    entry: MemoryEntry
    score: float = 1.0


class MemoryProvider(ABC):
    """Abstract base class for memory providers.

    Defines the interface that all memory implementations must follow.
    Memory providers handle storage and retrieval of data across different
    backends (in-memory, file-based, database, vector stores, etc.).

    Subclasses must implement all abstract methods. The search method is
    optional and only applicable for vector-enabled backends.
    """

    @abstractmethod
    async def store(self, key: str, value: Any, metadata: dict | None = None) -> None:
        """Store a value with optional metadata.

        Args:
            key: Unique identifier for the value.
            value: The value to store (should be JSON-serializable).
            metadata: Optional additional information to attach.
        """
        ...

    @abstractmethod
    async def retrieve(self, key: str) -> Any | None:
        """Retrieve a value by key.

        Args:
            key: The unique identifier for the value.

        Returns:
            The stored value, or None if the key doesn't exist.
        """
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value by key.

        Args:
            key: The unique identifier for the value to delete.

        Returns:
            True if the value was deleted, False if the key didn't exist.
        """
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in memory.

        Args:
            key: The unique identifier to check.

        Returns:
            True if the key exists, False otherwise.
        """
        ...

    @abstractmethod
    async def clear(self) -> None:
        """Clear all memory entries.

        Removes all stored data from this memory provider.
        Use with caution as this operation is irreversible.
        """
        ...

    @abstractmethod
    async def keys(self) -> list[str]:
        """List all keys in memory.

        Returns:
            A list of all stored keys.
        """
        ...

    async def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """Search memory for relevant entries.

        This is an optional method for vector-enabled memory backends.
        Default implementation raises NotImplementedError.

        Args:
            query: The search query string.
            top_k: Maximum number of results to return.

        Returns:
            List of search results with relevance scores.

        Raises:
            NotImplementedError: If the backend doesn't support search.
        """
        raise NotImplementedError("Search not supported by this memory provider")

    async def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value with a default fallback.

        Convenience method that returns a default value if the key
        doesn't exist, similar to dict.get().

        Args:
            key: The unique identifier for the value.
            default: Value to return if key doesn't exist.

        Returns:
            The stored value or the default.
        """
        value = await self.retrieve(key)
        return value if value is not None else default

    async def update(self, key: str, value: Any, metadata: dict | None = None) -> bool:
        """Update an existing entry.

        Only updates if the key already exists. Use store() to create
        or update unconditionally.

        Args:
            key: The unique identifier for the value.
            value: The new value to store.
            metadata: Optional new metadata (replaces existing).

        Returns:
            True if updated, False if key didn't exist.
        """
        if await self.exists(key):
            await self.store(key, value, metadata)
            return True
        return False


__all__ = [
    "MemoryEntry",
    "SearchResult",
    "MemoryProvider",
]
