"""Persistent memory implementations for AgentForge.

This module provides memory backends that persist data across executions,
including file-based storage and optional database backends.
"""

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from agentforge.memory.base import MemoryEntry, MemoryProvider, SearchResult


class FileMemoryConfig(BaseModel):
    """Configuration for file-based persistent memory.

    Attributes:
        path: Path to the JSON file for storage.
        autosave: Whether to automatically save after each modification.
        create_dirs: Whether to create parent directories if they don't exist.
    """

    path: str = "memory.json"
    autosave: bool = True
    create_dirs: bool = True


class FileMemory(MemoryProvider):
    """File-based persistent memory (JSON).

    Stores memory entries in a JSON file, providing persistence across
    application restarts. Supports automatic saving and directory creation.

    Features:
    - JSON-based storage for human readability
    - Automatic saving on each modification (configurable)
    - Atomic writes via temp file
    - Optional directory creation

    Example:
        ```python
        config = FileMemoryConfig(path="data/agent_memory.json")
        memory = FileMemory(config)

        await memory.store("user_preference", {"theme": "dark"})
        # Data is automatically saved to disk

        # Later, in a new session:
        memory = FileMemory(config)  # Loads from file
        pref = await memory.retrieve("user_preference")
        ```
    """

    def __init__(self, config: FileMemoryConfig | None = None) -> None:
        """Initialize file memory and load existing data.

        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or FileMemoryConfig()
        self._data: dict[str, MemoryEntry] = {}
        self._load()

    def _load(self) -> None:
        """Load data from the JSON file."""
        if os.path.exists(self.config.path):
            try:
                with open(self.config.path, encoding="utf-8") as f:
                    data = json.load(f)
                    self._data = {k: MemoryEntry(**v) for k, v in data.items()}
            except (json.JSONDecodeError, KeyError, TypeError):
                # If file is corrupted, start fresh
                self._data = {}

    def _save(self) -> None:
        """Save data to the JSON file."""
        if self.config.create_dirs:
            Path(self.config.path).parent.mkdir(parents=True, exist_ok=True)

        # Write to temp file first for atomicity
        temp_path = f"{self.config.path}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(
                    {k: v.model_dump() for k, v in self._data.items()},
                    f,
                    indent=2,
                    default=str,  # Handle datetime serialization
                )
            # Atomic rename
            os.replace(temp_path, self.config.path)
        except Exception:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

    async def store(self, key: str, value: Any, metadata: dict | None = None) -> None:
        """Store a value with optional metadata.

        Args:
            key: Unique identifier for the value.
            value: The value to store (should be JSON-serializable).
            metadata: Optional additional information.
        """
        self._data[key] = MemoryEntry(key=key, value=value, metadata=metadata)
        if self.config.autosave:
            self._save()

    async def retrieve(self, key: str) -> Any | None:
        """Retrieve a value by key.

        Args:
            key: The unique identifier.

        Returns:
            The stored value, or None if not found.
        """
        entry = self._data.get(key)
        return entry.value if entry else None

    async def delete(self, key: str) -> bool:
        """Delete a value by key.

        Args:
            key: The unique identifier to delete.

        Returns:
            True if deleted, False if not found.
        """
        if key in self._data:
            del self._data[key]
            if self.config.autosave:
                self._save()
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists.

        Args:
            key: The unique identifier to check.

        Returns:
            True if the key exists.
        """
        return key in self._data

    async def clear(self) -> None:
        """Clear all data and save."""
        self._data.clear()
        if self.config.autosave:
            self._save()

    async def keys(self) -> list[str]:
        """List all stored keys.

        Returns:
            List of all keys.
        """
        return list(self._data.keys())

    async def get_entry(self, key: str) -> MemoryEntry | None:
        """Get the full memory entry including metadata.

        Args:
            key: The unique identifier.

        Returns:
            The full MemoryEntry, or None if not found.
        """
        return self._data.get(key)

    def save(self) -> None:
        """Manually save data to file.

        Useful when autosave is disabled.
        """
        self._save()

    def reload(self) -> None:
        """Reload data from file.

        Discards any unsaved changes and reloads from disk.
        """
        self._load()

    def __len__(self) -> int:
        """Return the number of stored entries."""
        return len(self._data)

    def __repr__(self) -> str:
        """String representation of file memory."""
        return f"FileMemory(path={self.config.path}, entries={len(self._data)})"


class InMemoryVectorStore(MemoryProvider):
    """Simple in-memory vector store for semantic search.

    A basic implementation that stores embeddings in memory and supports
    similarity search. Requires the 'numpy' package for vector operations.

    Note: This is a simplified implementation. For production use,
    consider using dedicated vector databases like Pinecone, Weaviate,
    or ChromaDB.

    Example:
        ```python
        memory = InMemoryVectorStore()

        # Store with automatic embedding (requires embedding function)
        await memory.store_with_embedding(
            key="doc1",
            content="Hello world",
            embedding=[0.1, 0.2, 0.3, ...]
        )

        # Search for similar content
        results = await memory.search("hello", top_k=5)
        ```
    """

    def __init__(self) -> None:
        """Initialize the vector store."""
        self._data: dict[str, MemoryEntry] = {}
        self._embeddings: dict[str, list[float]] = {}

    async def store(self, key: str, value: Any, metadata: dict | None = None) -> None:
        """Store a value without embedding.

        Args:
            key: Unique identifier.
            value: The value to store.
            metadata: Optional metadata.
        """
        self._data[key] = MemoryEntry(key=key, value=value, metadata=metadata)

    async def store_with_embedding(
        self,
        key: str,
        content: str,
        embedding: list[float],
        metadata: dict | None = None,
    ) -> None:
        """Store content with its embedding vector.

        Args:
            key: Unique identifier.
            content: The text content.
            embedding: The embedding vector.
            metadata: Optional metadata.
        """
        self._data[key] = MemoryEntry(
            key=key,
            value=content,
            metadata=metadata,
        )
        self._embeddings[key] = embedding

    async def retrieve(self, key: str) -> Any | None:
        """Retrieve a value by key.

        Args:
            key: The unique identifier.

        Returns:
            The stored value, or None if not found.
        """
        entry = self._data.get(key)
        return entry.value if entry else None

    async def delete(self, key: str) -> bool:
        """Delete a value by key.

        Args:
            key: The unique identifier.

        Returns:
            True if deleted, False if not found.
        """
        if key in self._data:
            del self._data[key]
            self._embeddings.pop(key, None)
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        return key in self._data

    async def clear(self) -> None:
        """Clear all data."""
        self._data.clear()
        self._embeddings.clear()

    async def keys(self) -> list[str]:
        """List all keys."""
        return list(self._data.keys())

    async def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """Search is not implemented for basic InMemoryVectorStore.

        Override this method in a subclass that provides embedding generation.

        Args:
            query: The search query.
            top_k: Maximum results to return.

        Raises:
            NotImplementedError: Always, as this requires embedding generation.
        """
        raise NotImplementedError(
            "InMemoryVectorStore.search requires an embedding function. "
            "Use a subclass that implements embedding generation."
        )

    async def search_by_embedding(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[SearchResult]:
        """Search by embedding vector similarity.

        Uses cosine similarity to find the most similar stored embeddings.

        Args:
            query_embedding: The query embedding vector.
            top_k: Maximum results to return.

        Returns:
            List of search results with similarity scores.
        """
        try:
            import numpy as np
        except ImportError as e:
            raise ImportError(
                "numpy is required for vector search. Install with: pip install numpy"
            ) from e

        if not self._embeddings:
            return []

        query_vec = np.array(query_embedding)
        query_norm = np.linalg.norm(query_vec)

        if query_norm == 0:
            return []

        similarities: list[tuple[str, float]] = []

        for key, emb in self._embeddings.items():
            emb_vec = np.array(emb)
            emb_norm = np.linalg.norm(emb_vec)

            if emb_norm == 0:
                continue

            # Cosine similarity
            similarity = np.dot(query_vec, emb_vec) / (query_norm * emb_norm)
            similarities.append((key, float(similarity)))

        # Sort by similarity (descending) and take top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_results = similarities[:top_k]

        return [
            SearchResult(entry=self._data[key], score=score)
            for key, score in top_results
            if key in self._data
        ]

    def __len__(self) -> int:
        """Return the number of stored entries."""
        return len(self._data)

    def __repr__(self) -> str:
        """String representation."""
        return f"InMemoryVectorStore(entries={len(self._data)})"


__all__ = [
    "FileMemoryConfig",
    "FileMemory",
    "InMemoryVectorStore",
]
