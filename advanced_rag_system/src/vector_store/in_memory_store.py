"""In-memory vector store using numpy for similarity search.

A lightweight VectorStore implementation that does not depend on ChromaDB.
Useful when ChromaDB has dependency conflicts (e.g. pydantic v2 on Python 3.14).
Stores all vectors in memory using numpy arrays for fast cosine similarity search.

Limitations vs ChromaDB:
- No persistence (data lost on restart)
- No metadata-based filtering
- Less efficient for very large datasets (>100k vectors)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

import numpy as np

from src.core.exceptions import NotFoundError, VectorStoreError
from src.core.types import DocumentChunk, Metadata, SearchResult
from src.vector_store.base import SearchOptions, VectorStore, VectorStoreConfig


class InMemoryVectorStore(VectorStore):
    """In-memory vector store using numpy arrays.

    Provides vector similarity search without external dependencies.
    Suitable for development, testing, and moderate-scale production use.

    Example:
        ```python
        config = VectorStoreConfig(
            collection_name="documents",
            dimension=1536,
            distance_metric="cosine"
        )
        store = InMemoryVectorStore(config)
        await store.initialize()

        await store.add_chunks(chunks)
        results = await store.search(query_embedding, SearchOptions(top_k=5))
        ```
    """

    def __init__(self, config: Optional[VectorStoreConfig] = None) -> None:
        super().__init__(config)
        self._chunks: Dict[str, DocumentChunk] = {}
        self._embeddings: Dict[str, np.ndarray] = {}
        self._embedding_matrix: Optional[np.ndarray] = None
        self._id_index: List[str] = []
        self._dirty = False

    async def initialize(self) -> None:
        self._initialized = True

    async def close(self) -> None:
        self._chunks.clear()
        self._embeddings.clear()
        self._embedding_matrix = None
        self._id_index.clear()
        self._dirty = False
        self._initialized = False

    def _rebuild_matrix(self) -> None:
        """Rebuild the embedding matrix for batch similarity search."""
        if not self._embeddings:
            self._embedding_matrix = None
            self._id_index = []
            self._dirty = False
            return

        self._id_index = list(self._embeddings.keys())
        vectors = [self._embeddings[cid] for cid in self._id_index]
        self._embedding_matrix = np.vstack(vectors)

        # Normalize rows for cosine similarity (dot product on unit vectors)
        norms = np.linalg.norm(self._embedding_matrix, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        self._embedding_matrix = self._embedding_matrix / norms

        self._dirty = False

    async def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        self._ensure_initialized()

        if not chunks:
            return

        try:
            for chunk in chunks:
                if chunk.embedding is None:
                    raise VectorStoreError(
                        message=f"Chunk {chunk.id} has no embedding",
                        error_code="MISSING_EMBEDDING",
                        store_type="in_memory",
                    )
                self._validate_embedding(chunk.embedding)

                chunk_id = str(chunk.id)
                self._chunks[chunk_id] = chunk
                self._embeddings[chunk_id] = np.array(chunk.embedding, dtype=np.float32)

            self._dirty = True
        except VectorStoreError:
            raise
        except Exception as e:
            raise VectorStoreError(
                message=f"Failed to add chunks: {e}",
                error_code="ADD_ERROR",
                store_type="in_memory",
            )

    async def delete_chunks(self, chunk_ids: List[UUID]) -> None:
        self._ensure_initialized()

        for cid in chunk_ids:
            key = str(cid)
            self._chunks.pop(key, None)
            self._embeddings.pop(key, None)

        self._dirty = True

    async def search(
        self,
        query_embedding: List[float],
        options: Optional[SearchOptions] = None,
    ) -> List[SearchResult]:
        self._ensure_initialized()

        if options is None:
            options = SearchOptions()

        self._validate_embedding(query_embedding)

        if not self._embeddings:
            return []

        try:
            if self._dirty:
                self._rebuild_matrix()

            query_vec = np.array(query_embedding, dtype=np.float32)
            norm = np.linalg.norm(query_vec)
            if norm > 0:
                query_vec = query_vec / norm

            # Cosine similarity via dot product (vectors are pre-normalized)
            similarities = self._embedding_matrix @ query_vec

            # Get top_k indices
            n = len(similarities)
            top_k = min(options.top_k, n)

            if top_k >= n:
                # No partition needed — just sort everything
                top_indices = np.argsort(-similarities)[:top_k]
            else:
                top_indices = np.argpartition(-similarities, top_k)[:top_k]
                top_indices = top_indices[np.argsort(-similarities[top_indices])]

            results = []
            for rank, idx in enumerate(top_indices):
                # Clamp to [0, 1] to handle float32 precision drift
                score = float(np.clip(similarities[idx], 0.0, 1.0))
                if score < options.threshold:
                    continue

                chunk_id = self._id_index[idx]
                chunk = self._chunks[chunk_id]

                results.append(
                    SearchResult(
                        chunk=chunk,
                        score=score,
                        rank=rank + 1,
                        distance=max(0.0, 1.0 - score),
                    )
                )

            return results

        except VectorStoreError:
            raise
        except Exception as e:
            raise VectorStoreError(
                message=f"Search failed: {e}",
                error_code="SEARCH_ERROR",
                store_type="in_memory",
            )

    async def get_chunk(self, chunk_id: UUID) -> Optional[DocumentChunk]:
        self._ensure_initialized()
        return self._chunks.get(str(chunk_id))

    async def update_chunk(self, chunk: DocumentChunk) -> None:
        self._ensure_initialized()

        key = str(chunk.id)
        if key not in self._chunks:
            raise NotFoundError(
                message=f"Chunk {chunk.id} not found",
                resource_type="chunk",
                resource_id=key,
            )

        if chunk.embedding is None:
            raise VectorStoreError(
                message=f"Chunk {chunk.id} has no embedding",
                error_code="MISSING_EMBEDDING",
                store_type="in_memory",
            )

        self._validate_embedding(chunk.embedding)
        self._chunks[key] = chunk
        self._embeddings[key] = np.array(chunk.embedding, dtype=np.float32)
        self._dirty = True

    async def count(self) -> int:
        return len(self._chunks)

    async def clear(self) -> None:
        self._ensure_initialized()
        self._chunks.clear()
        self._embeddings.clear()
        self._embedding_matrix = None
        self._id_index.clear()
        self._dirty = False

    async def health_check(self) -> bool:
        return self._initialized

    async def get_stats(self) -> Dict[str, Any]:
        return {
            "store_type": "in_memory",
            "chunk_count": len(self._chunks),
            "dimension": self.config.dimension,
            "collection_name": self.config.collection_name,
            "memory_estimated_mb": (
                len(self._embeddings) * self.config.dimension * 4 / (1024 * 1024) if self._embeddings else 0.0
            ),
        }
