"""In-memory vector store implementation for AgentForge.

This module provides a zero-dependency (optional numpy) in-memory vector store
for semantic search. It's suitable for development, testing, and small-scale
production use cases.

For production workloads, consider using dedicated vector databases like
Qdrant or ChromaDB (available as optional backends).
"""

from typing import Any

from agentforge.memory.vector_base import VectorEntry, VectorSearchResult, VectorStore


class InMemoryVectorStore(VectorStore):
    """In-memory vector store using numpy for similarity computation.

    A lightweight vector store that keeps all data in memory. Uses numpy
    for efficient cosine similarity calculations if available, with a
    pure Python fallback.

    Features:
    - Zero required dependencies (numpy optional but recommended)
    - Cosine similarity search
    - Metadata filtering
    - Batch operations

    Limitations:
    - Data is lost when the instance is destroyed
    - Not suitable for large-scale production use
    - No persistence

    Example:
        ```python
        # Create store with default dimension (1536 for OpenAI embeddings)
        store = InMemoryVectorStore(dimension=1536)

        # Insert entries
        entry = VectorEntry(
            id="doc1",
            vector=[0.1, 0.2, 0.3, ...],
            content="Hello world",
            metadata={"source": "greeting"}
        )
        await store.insert(entry)

        # Search for similar vectors
        results = await store.search(query_vector, top_k=5)

        # With metadata filtering
        results = await store.search(
            query_vector,
            top_k=5,
            filter_metadata={"source": "greeting"}
        )
        ```
    """

    def __init__(self, dimension: int = 1536) -> None:
        """Initialize the in-memory vector store.

        Args:
            dimension: Expected dimension of vectors. Default 1536 matches
                OpenAI text-embedding-ada-002 embeddings.
        """
        self.dimension = dimension
        self._vectors: dict[str, list[float]] = {}
        self._metadata: dict[str, dict[str, Any]] = {}
        self._content: dict[str, str | None] = {}
        self._created_at: dict[str, str | None] = {}

    async def insert(self, entry: VectorEntry) -> str:
        """Insert a vector entry into the store.

        Args:
            entry: The vector entry to insert.

        Returns:
            The ID of the inserted entry.

        Raises:
            ValueError: If the vector dimension doesn't match the store's dimension.
        """
        if len(entry.vector) != self.dimension:
            raise ValueError(
                f"Vector dimension mismatch: got {len(entry.vector)}, "
                f"expected {self.dimension}"
            )
        self._vectors[entry.id] = entry.vector
        self._metadata[entry.id] = entry.metadata.copy()
        self._content[entry.id] = entry.content
        self._created_at[entry.id] = entry.created_at
        return entry.id

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Search for similar vectors using cosine similarity.

        Args:
            query_vector: The query embedding vector.
            top_k: Maximum number of results to return.
            filter_metadata: Optional metadata filters. Only entries with
                matching key-value pairs will be returned.

        Returns:
            List of search results sorted by similarity (descending).
        """
        if not self._vectors:
            return []

        # Try to use numpy for efficient computation
        try:
            return await self._search_numpy(query_vector, top_k, filter_metadata)
        except ImportError:
            return await self._search_pure_python(query_vector, top_k, filter_metadata)

    async def _search_numpy(
        self,
        query_vector: list[float],
        top_k: int,
        filter_metadata: dict[str, Any] | None,
    ) -> list[VectorSearchResult]:
        """Search using numpy for efficient similarity computation."""
        import numpy as np

        query = np.array(query_vector, dtype=np.float32)
        query_norm = np.linalg.norm(query)

        if query_norm == 0:
            return []

        query_normalized = query / query_norm

        scores: list[tuple[str, float]] = []

        for id_, vec in self._vectors.items():
            # Apply metadata filter
            if filter_metadata:
                meta = self._metadata[id_]
                if not all(meta.get(k) == v for k, v in filter_metadata.items()):
                    continue

            vec_array = np.array(vec, dtype=np.float32)
            vec_norm = np.linalg.norm(vec_array)

            if vec_norm == 0:
                continue

            # Cosine similarity
            similarity = float(np.dot(query_normalized, vec_array / vec_norm))
            scores.append((id_, similarity))

        # Sort by similarity (descending) and take top_k
        scores.sort(key=lambda x: x[1], reverse=True)
        top_results = scores[:top_k]

        return [
            VectorSearchResult(
                id=id_,
                score=score,
                metadata=self._metadata[id_].copy(),
                content=self._content[id_],
            )
            for id_, score in top_results
        ]

    async def _search_pure_python(
        self,
        query_vector: list[float],
        top_k: int,
        filter_metadata: dict[str, Any] | None,
    ) -> list[VectorSearchResult]:
        """Search using pure Python (fallback when numpy unavailable)."""

        def dot_product(a: list[float], b: list[float]) -> float:
            return sum(x * y for x, y in zip(a, b))

        def norm(vec: list[float]) -> float:
            return sum(x * x for x in vec) ** 0.5

        query_norm = norm(query_vector)
        if query_norm == 0:
            return []

        scores: list[tuple[str, float]] = []

        for id_, vec in self._vectors.items():
            # Apply metadata filter
            if filter_metadata:
                meta = self._metadata[id_]
                if not all(meta.get(k) == v for k, v in filter_metadata.items()):
                    continue

            vec_norm = norm(vec)
            if vec_norm == 0:
                continue

            # Cosine similarity
            similarity = dot_product(query_vector, vec) / (query_norm * vec_norm)
            scores.append((id_, similarity))

        # Sort by similarity (descending) and take top_k
        scores.sort(key=lambda x: x[1], reverse=True)
        top_results = scores[:top_k]

        return [
            VectorSearchResult(
                id=id_,
                score=score,
                metadata=self._metadata[id_].copy(),
                content=self._content[id_],
            )
            for id_, score in top_results
        ]

    async def delete(self, id: str) -> bool:
        """Delete an entry by ID.

        Args:
            id: The unique identifier of the entry to delete.

        Returns:
            True if the entry was deleted, False if it didn't exist.
        """
        if id in self._vectors:
            del self._vectors[id]
            del self._metadata[id]
            del self._content[id]
            del self._created_at[id]
            return True
        return False

    async def get(self, id: str) -> VectorEntry | None:
        """Get an entry by ID.

        Args:
            id: The unique identifier of the entry.

        Returns:
            The vector entry, or None if not found.
        """
        if id not in self._vectors:
            return None
        return VectorEntry(
            id=id,
            vector=self._vectors[id].copy(),
            metadata=self._metadata[id].copy(),
            content=self._content[id],
            created_at=self._created_at[id],
        )

    async def count(self) -> int:
        """Count total entries in the store.

        Returns:
            The number of stored entries.
        """
        return len(self._vectors)

    async def clear(self) -> None:
        """Clear all entries from the store."""
        self._vectors.clear()
        self._metadata.clear()
        self._content.clear()
        self._created_at.clear()

    async def insert_batch(self, entries: list[VectorEntry]) -> list[str]:
        """Insert multiple entries efficiently.

        Args:
            entries: List of vector entries to insert.

        Returns:
            List of inserted entry IDs.

        Raises:
            ValueError: If any vector dimension doesn't match.
        """
        # Validate all dimensions first
        for entry in entries:
            if len(entry.vector) != self.dimension:
                raise ValueError(
                    f"Vector dimension mismatch for entry {entry.id}: "
                    f"got {len(entry.vector)}, expected {self.dimension}"
                )

        # Insert all entries
        ids = []
        for entry in entries:
            self._vectors[entry.id] = entry.vector
            self._metadata[entry.id] = entry.metadata.copy()
            self._content[entry.id] = entry.content
            self._created_at[entry.id] = entry.created_at
            ids.append(entry.id)

        return ids

    async def delete_batch(self, ids: list[str]) -> list[bool]:
        """Delete multiple entries by ID.

        Args:
            ids: List of entry IDs to delete.

        Returns:
            List of deletion success flags.
        """
        results = []
        for id_ in ids:
            results.append(await self.delete(id_))
        return results

    async def get_all_ids(self) -> list[str]:
        """Get all entry IDs in the store.

        Returns:
            List of all stored entry IDs.
        """
        return list(self._vectors.keys())

    def __len__(self) -> int:
        """Return the number of stored entries."""
        return len(self._vectors)

    def __repr__(self) -> str:
        """String representation of the vector store."""
        return f"InMemoryVectorStore(dimension={self.dimension}, entries={len(self._vectors)})"


__all__ = ["InMemoryVectorStore"]
