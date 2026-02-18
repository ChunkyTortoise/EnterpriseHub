"""Qdrant vector store backend for AgentForge.

This module provides a Qdrant-based vector store implementation for
production-grade semantic search. Qdrant is a high-performance vector
database suitable for large-scale deployments.

Installation:
    pip install agentforge[qdrant]

Features:
- Persistent storage
- High-performance similarity search
- Metadata filtering
- Horizontal scaling support
"""

from typing import Any, Optional

from agentforge.memory.vector_base import VectorEntry, VectorSearchResult, VectorStore


class QdrantVectorStore(VectorStore):
    """Qdrant vector store backend.

    A production-grade vector store using Qdrant. Supports both local
    (in-memory) and remote (server/cluster) deployments.

    Features:
    - Persistent storage
    - High-performance similarity search
    - Rich metadata filtering
    - Horizontal scaling
    - Multiple distance metrics

    Example:
        ```python
        # Local in-memory mode
        store = QdrantVectorStore(location=":memory:")

        # Remote server mode
        store = QdrantVectorStore(
            url="http://localhost:6333",
            api_key="your-api-key"
        )

        # Insert and search
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

    def __init__(
        self,
        url: Optional[str] = None,
        location: Optional[str] = None,
        collection_name: str = "agentforge",
        api_key: Optional[str] = None,
        dimension: int = 1536,
        distance: str = "Cosine",
    ) -> None:
        """Initialize Qdrant vector store.

        Args:
            url: Qdrant server URL (e.g., "http://localhost:6333").
            location: Local storage path. Use ":memory:" for in-memory mode.
            collection_name: Name of the collection to use.
            api_key: API key for authentication (if required).
            dimension: Vector dimension. Default 1536 for OpenAI embeddings.
            distance: Distance metric. One of "Cosine", "Euclidean", "Dot".

        Raises:
            ImportError: If qdrant-client is not installed.
        """
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
        except ImportError as e:
            raise ImportError(
                "qdrant-client is required for QdrantVectorStore. "
                "Install with: pip install agentforge[qdrant]"
            ) from e

        self.collection_name = collection_name
        self.dimension = dimension
        self._distance_str = distance

        # Map distance string to enum
        distance_map = {
            "Cosine": Distance.COSINE,
            "Euclidean": Distance.EUCLID,
            "Dot": Distance.DOT,
        }
        self._distance = distance_map.get(distance, Distance.COSINE)

        # Initialize client
        if url:
            self._client = QdrantClient(url=url, api_key=api_key)
        elif location:
            self._client = QdrantClient(location=location)
        else:
            # Default to in-memory
            self._client = QdrantClient(location=":memory:")

        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Create collection if it doesn't exist."""
        from qdrant_client.models import VectorParams

        collections = self._client.get_collections().collections
        if self.collection_name not in [c.name for c in collections]:
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.dimension,
                    distance=self._distance,
                ),
            )

    async def insert(self, entry: VectorEntry) -> str:
        """Insert a vector entry into Qdrant.

        Args:
            entry: The vector entry to insert.

        Returns:
            The ID of the inserted entry.

        Raises:
            ValueError: If vector dimension doesn't match.
        """
        from qdrant_client.models import PointStruct

        if len(entry.vector) != self.dimension:
            raise ValueError(
                f"Vector dimension mismatch: got {len(entry.vector)}, "
                f"expected {self.dimension}"
            )

        # Build payload with metadata and content
        payload: dict[str, Any] = {
            "metadata": entry.metadata,
        }
        if entry.content:
            payload["content"] = entry.content
        if entry.created_at:
            payload["created_at"] = entry.created_at

        point = PointStruct(
            id=entry.id,
            vector=entry.vector,
            payload=payload,
        )

        self._client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )

        return entry.id

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filter_metadata: Optional[dict[str, Any]] = None,
    ) -> list[VectorSearchResult]:
        """Search for similar vectors in Qdrant.

        Args:
            query_vector: The query embedding vector.
            top_k: Maximum number of results to return.
            filter_metadata: Optional metadata filters.

        Returns:
            List of search results sorted by similarity.
        """
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        # Build filter if provided
        query_filter = None
        if filter_metadata:
            conditions = [
                FieldCondition(
                    key=f"metadata.{k}",
                    match=MatchValue(value=v),
                )
                for k, v in filter_metadata.items()
            ]
            query_filter = Filter(must=conditions)

        results = self._client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter,
        )

        return [
            VectorSearchResult(
                id=str(result.id),
                score=result.score,
                metadata=result.payload.get("metadata", {}),
                content=result.payload.get("content"),
            )
            for result in results
        ]

    async def delete(self, id: str) -> bool:
        """Delete an entry by ID.

        Args:
            id: The unique identifier to delete.

        Returns:
            True if deleted, False if not found.
        """
        try:
            from qdrant_client.models import PointIdsList

            # Check if exists first
            existing = self._client.retrieve(
                collection_name=self.collection_name,
                ids=[id],
            )
            if not existing:
                return False

            self._client.delete(
                collection_name=self.collection_name,
                points_selector=PointIdsList(points=[id]),
            )
            return True
        except Exception:
            return False

    async def get(self, id: str) -> Optional[VectorEntry]:
        """Get an entry by ID.

        Args:
            id: The unique identifier.

        Returns:
            The vector entry, or None if not found.
        """
        try:
            results = self._client.retrieve(
                collection_name=self.collection_name,
                ids=[id],
                with_vectors=True,
            )

            if not results:
                return None

            result = results[0]
            return VectorEntry(
                id=str(result.id),
                vector=result.vector,
                metadata=result.payload.get("metadata", {}),
                content=result.payload.get("content"),
                created_at=result.payload.get("created_at"),
            )
        except Exception:
            return None

    async def count(self) -> int:
        """Count total entries in the collection.

        Returns:
            Number of entries in the collection.
        """
        result = self._client.count(collection_name=self.collection_name)
        return result.count

    async def insert_batch(self, entries: list[VectorEntry]) -> list[str]:
        """Insert multiple entries efficiently.

        Args:
            entries: List of vector entries to insert.

        Returns:
            List of inserted entry IDs.
        """
        from qdrant_client.models import PointStruct

        # Validate dimensions
        for entry in entries:
            if len(entry.vector) != self.dimension:
                raise ValueError(
                    f"Vector dimension mismatch for entry {entry.id}: "
                    f"got {len(entry.vector)}, expected {self.dimension}"
                )

        points = []
        for entry in entries:
            payload: dict[str, Any] = {"metadata": entry.metadata}
            if entry.content:
                payload["content"] = entry.content
            if entry.created_at:
                payload["created_at"] = entry.created_at

            points.append(
                PointStruct(
                    id=entry.id,
                    vector=entry.vector,
                    payload=payload,
                )
            )

        self._client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

        return [e.id for e in entries]

    async def delete_batch(self, ids: list[str]) -> list[bool]:
        """Delete multiple entries by ID.

        Args:
            ids: List of entry IDs to delete.

        Returns:
            List of deletion success flags.
        """
        from qdrant_client.models import PointIdsList

        try:
            self._client.delete(
                collection_name=self.collection_name,
                points_selector=PointIdsList(points=ids),
            )
            # Qdrant doesn't return individual success, assume all succeeded
            return [True] * len(ids)
        except Exception:
            return [False] * len(ids)

    async def clear(self) -> None:
        """Clear all entries from the collection."""
        self._client.delete_collection(collection_name=self.collection_name)
        self._ensure_collection()

    async def get_all_ids(self) -> list[str]:
        """Get all entry IDs in the collection.

        Note: This can be slow for large collections.

        Returns:
            List of all entry IDs.
        """
        from qdrant_client.models import Filter

        # Scroll through all points
        all_ids = []
        offset = None

        while True:
            results, offset = self._client.scroll(
                collection_name=self.collection_name,
                limit=100,
                offset=offset,
                with_payload=False,
                with_vectors=False,
            )

            all_ids.extend(str(r.id) for r in results)

            if offset is None:
                break

        return all_ids

    def __repr__(self) -> str:
        """String representation of the Qdrant store."""
        return (
            f"QdrantVectorStore(collection={self.collection_name}, "
            f"dimension={self.dimension}, distance={self._distance_str})"
        )


__all__ = ["QdrantVectorStore"]
