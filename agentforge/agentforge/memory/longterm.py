"""Long-term memory implementation for AgentForge.

This module provides long-term memory backed by a vector store for semantic
search capabilities. It integrates with the MemoryProvider interface and
supports pluggable embedding functions.

Long-term memory is designed for:
- Storing important facts and knowledge across sessions
- Semantic retrieval of relevant memories
- Building persistent agent knowledge bases
"""

from typing import Any, Awaitable, Callable, Optional, Union

from agentforge.memory.base import MemoryProvider
from agentforge.memory.vector_base import VectorEntry, VectorSearchResult, VectorStore


# Type alias for embedding functions
EmbeddingFunc = Callable[[str], Awaitable[list[float]]]


class LongTermMemory(MemoryProvider):
    """Long-term memory backed by a vector store for semantic search.

    Provides persistent storage with semantic retrieval capabilities.
    Entries are stored with their embeddings, enabling similarity-based
    search across stored memories.

    Features:
    - Semantic search over stored memories
    - Pluggable embedding functions
    - Metadata filtering
    - Works with any VectorStore implementation

    Example:
        ```python
        from agentforge.memory import InMemoryVectorStore, LongTermMemory

        # Create with an embedding function
        async def embed(text: str) -> list[float]:
            # Your embedding logic here (e.g., OpenAI, sentence-transformers)
            return [0.1, 0.2, 0.3, ...]

        store = InMemoryVectorStore(dimension=1536)
        memory = LongTermMemory(vector_store=store, embedder=embed)

        # Store a memory
        await memory.store(
            key="fact1",
            value="The user prefers dark mode",
            content="User preference: dark mode enabled",
            metadata={"category": "preferences"}
        )

        # Semantic search
        results = await memory.search("user interface preferences", top_k=5)
        ```
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedder: Optional[EmbeddingFunc] = None,
        default_dimension: int = 1536,
    ) -> None:
        """Initialize long-term memory.

        Args:
            vector_store: The vector store backend to use.
            embedder: Optional async function to convert text to embeddings.
                Required for semantic search functionality.
            default_dimension: Default vector dimension for entries without
                embeddings. Default is 1536 (OpenAI ada-002).
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.default_dimension = default_dimension

    async def store(
        self,
        key: str,
        value: Any,
        metadata: Optional[dict[str, Any]] = None,
        content: Optional[str] = None,
    ) -> None:
        """Store a value with optional embedding.

        If content is provided and an embedder is set, creates an embedding
        for semantic search. Otherwise, stores with a placeholder vector.

        Args:
            key: Unique identifier for the value.
            value: The value to store (can be any JSON-serializable type).
            metadata: Optional additional information.
            content: Optional text content to embed. If not provided and
                value is a string, uses value as content.
        """
        vector: Optional[list[float]] = None
        actual_content = content or (value if isinstance(value, str) else None)

        # Create embedding if we have content and an embedder
        if actual_content and self.embedder:
            try:
                vector = await self.embedder(actual_content)
            except Exception:
                # If embedding fails, continue with placeholder
                vector = None

        if vector:
            # Store with actual embedding
            entry = VectorEntry(
                id=key,
                vector=vector,
                metadata=metadata or {},
                content=actual_content,
            )
            await self.vector_store.insert(entry)
        else:
            # Store without embedding (placeholder vector)
            # Store the raw value in metadata since we can't embed it
            entry = VectorEntry(
                id=key,
                vector=[0.0] * self.default_dimension,
                metadata={
                    "raw_value": value,
                    "no_embedding": True,
                    **(metadata or {}),
                },
                content=actual_content,
            )
            await self.vector_store.insert(entry)

    async def retrieve(self, key: str) -> Any | None:
        """Retrieve a value by key.

        Args:
            key: The unique identifier for the value.

        Returns:
            The stored value, or None if not found.
        """
        entry = await self.vector_store.get(key)
        if entry is None:
            return None

        # If stored without embedding, return raw value from metadata
        if entry.metadata.get("no_embedding"):
            return entry.metadata.get("raw_value")

        # Return content if available, otherwise the raw value
        return entry.content

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Semantic search over stored memories.

        Requires an embedder to be set. Searches for memories similar to
        the query using vector similarity.

        Args:
            query: The search query string.
            top_k: Maximum number of results to return.
            filter_metadata: Optional metadata filters.

        Returns:
            List of search results with id, score, content, and metadata.

        Raises:
            ValueError: If no embedder is configured.
        """
        if not self.embedder:
            raise ValueError(
                "Embedder required for semantic search. "
                "Provide an embedder function when creating LongTermMemory."
            )

        # Create embedding for query
        query_vector = await self.embedder(query)

        # Search vector store
        results = await self.vector_store.search(query_vector, top_k, filter_metadata)

        # Format results
        return [
            {
                "id": r.id,
                "score": r.score,
                "content": r.content,
                "metadata": r.metadata,
            }
            for r in results
        ]

    async def search_by_vector(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filter_metadata: Optional[dict[str, Any]] = None,
    ) -> list[VectorSearchResult]:
        """Search directly with a vector (bypasses embedding).

        Useful when you already have an embedding and want to avoid
        recomputing it.

        Args:
            query_vector: The query embedding vector.
            top_k: Maximum number of results to return.
            filter_metadata: Optional metadata filters.

        Returns:
            List of VectorSearchResult objects.
        """
        return await self.vector_store.search(query_vector, top_k, filter_metadata)

    async def delete(self, key: str) -> bool:
        """Delete a memory by key.

        Args:
            key: The unique identifier to delete.

        Returns:
            True if deleted, False if not found.
        """
        return await self.vector_store.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if a key exists in memory.

        Args:
            key: The unique identifier to check.

        Returns:
            True if the key exists.
        """
        return await self.vector_store.exists(key)

    async def clear(self) -> None:
        """Clear all memories.

        Note: This relies on the underlying store having a clear method.
        For stores without clear, you may need to delete entries individually.
        """
        if hasattr(self.vector_store, "clear"):
            await self.vector_store.clear()
        else:
            # Fallback: delete all entries
            if hasattr(self.vector_store, "get_all_ids"):
                ids = await self.vector_store.get_all_ids()
                for id_ in ids:
                    await self.vector_store.delete(id_)

    async def keys(self) -> list[str]:
        """List all keys in memory.

        Returns:
            List of all stored keys.
        """
        if hasattr(self.vector_store, "get_all_ids"):
            return await self.vector_store.get_all_ids()

        # Fallback: use count and iterate (inefficient)
        # This is a limitation for stores without get_all_ids
        raise NotImplementedError(
            "Underlying vector store does not support listing all keys. "
            "Use a store with get_all_ids() method."
        )

    async def store_batch(
        self,
        entries: list[dict[str, Any]],
    ) -> list[str]:
        """Store multiple entries efficiently.

        Args:
            entries: List of dicts with keys 'key', 'value', optional
                'metadata', and optional 'content'.

        Returns:
            List of stored entry IDs.
        """
        vector_entries: list[VectorEntry] = []

        for entry in entries:
            key = entry["key"]
            value = entry["value"]
            metadata = entry.get("metadata", {})
            content = entry.get("content") or (value if isinstance(value, str) else None)

            vector: Optional[list[float]] = None
            if content and self.embedder:
                try:
                    vector = await self.embedder(content)
                except Exception:
                    vector = None

            if vector:
                vector_entries.append(
                    VectorEntry(
                        id=key,
                        vector=vector,
                        metadata=metadata,
                        content=content,
                    )
                )
            else:
                vector_entries.append(
                    VectorEntry(
                        id=key,
                        vector=[0.0] * self.default_dimension,
                        metadata={"raw_value": value, "no_embedding": True, **metadata},
                        content=content,
                    )
                )

        return await self.vector_store.insert_batch(vector_entries)

    async def count(self) -> int:
        """Count total stored memories.

        Returns:
            Number of stored entries.
        """
        return await self.vector_store.count()

    def __repr__(self) -> str:
        """String representation of long-term memory."""
        return f"LongTermMemory(store={type(self.vector_store).__name__})"


__all__ = ["LongTermMemory", "EmbeddingFunc"]
