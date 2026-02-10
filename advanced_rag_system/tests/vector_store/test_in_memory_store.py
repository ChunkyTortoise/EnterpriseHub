"""Tests for InMemoryVectorStore.

Validates the numpy-based in-memory vector store that serves as a
fallback when ChromaDB is unavailable (pydantic v2 on Python 3.14).
"""

from typing import List
from uuid import uuid4

import numpy as np
import pytest
from src.core.exceptions import NotFoundError, VectorStoreError
from src.core.types import DocumentChunk, Metadata
from src.vector_store.base import SearchOptions, VectorStoreConfig
from src.vector_store.in_memory_store import InMemoryVectorStore

@pytest.mark.integration


def _make_chunk(content: str, dim: int = 8) -> DocumentChunk:
    """Create a chunk with a deterministic embedding based on content."""
    doc_id = uuid4()
    c = DocumentChunk(document_id=doc_id, content=content, index=0, metadata=Metadata())
    rng = np.random.RandomState(hash(content) % (2**31))
    vec = rng.randn(dim).astype(np.float32)
    c.embedding = (vec / np.linalg.norm(vec)).tolist()
    return c


def _make_chunks(n: int, dim: int = 8) -> List[DocumentChunk]:
    return [_make_chunk(f"document number {i} about topic {i % 5}", dim) for i in range(n)]


class TestInMemoryVectorStoreLifecycle:
    """Test initialization, health, and cleanup."""

    @pytest.mark.asyncio
    async def test_initialize(self):
        store = InMemoryVectorStore()
        await store.initialize()
        assert await store.health_check() is True

    @pytest.mark.asyncio
    async def test_not_initialized_raises(self):
        store = InMemoryVectorStore()
        with pytest.raises(VectorStoreError, match="not initialized"):
            await store.add_chunks([])

    @pytest.mark.asyncio
    async def test_close_clears_state(self):
        store = InMemoryVectorStore(VectorStoreConfig(dimension=8))
        await store.initialize()
        await store.add_chunks(_make_chunks(3))
        assert await store.count() == 3

        await store.close()
        assert await store.health_check() is False

    @pytest.mark.asyncio
    async def test_clear(self):
        store = InMemoryVectorStore(VectorStoreConfig(dimension=8))
        await store.initialize()
        await store.add_chunks(_make_chunks(5))
        assert await store.count() == 5

        await store.clear()
        assert await store.count() == 0


class TestInMemoryVectorStoreAddDelete:
    """Test add and delete operations."""

    @pytest.mark.asyncio
    async def test_add_chunks(self):
        store = InMemoryVectorStore(VectorStoreConfig(dimension=8))
        await store.initialize()
        chunks = _make_chunks(10)
        await store.add_chunks(chunks)
        assert await store.count() == 10

    @pytest.mark.asyncio
    async def test_add_empty(self):
        store = InMemoryVectorStore(VectorStoreConfig(dimension=8))
        await store.initialize()
        await store.add_chunks([])
        assert await store.count() == 0

    @pytest.mark.asyncio
    async def test_add_missing_embedding_raises(self):
        store = InMemoryVectorStore(VectorStoreConfig(dimension=8))
        await store.initialize()
        chunk = DocumentChunk(document_id=uuid4(), content="no embedding", index=0, metadata=Metadata())
        with pytest.raises(VectorStoreError, match="no embedding"):
            await store.add_chunks([chunk])

    @pytest.mark.asyncio
    async def test_add_wrong_dimension_raises(self):
        store = InMemoryVectorStore(VectorStoreConfig(dimension=8))
        await store.initialize()
        chunk = _make_chunk("test", dim=16)  # Wrong dim
        with pytest.raises(VectorStoreError, match="mismatch"):
            await store.add_chunks([chunk])

    @pytest.mark.asyncio
    async def test_delete_chunks(self):
        store = InMemoryVectorStore(VectorStoreConfig(dimension=8))
        await store.initialize()
        chunks = _make_chunks(5)
        await store.add_chunks(chunks)

        await store.delete_chunks([chunks[0].id, chunks[1].id])
        assert await store.count() == 3

    @pytest.mark.asyncio
    async def test_delete_nonexistent_is_noop(self):
        store = InMemoryVectorStore(VectorStoreConfig(dimension=8))
        await store.initialize()
        await store.delete_chunks([uuid4()])
        assert await store.count() == 0


class TestInMemoryVectorStoreSearch:
    """Test search functionality."""

    @pytest.mark.asyncio
    async def test_search_self_match(self):
        store = InMemoryVectorStore(VectorStoreConfig(dimension=8))
        await store.initialize()
        chunk = _make_chunk("machine learning algorithms")
        await store.add_chunks([chunk])

        results = await store.search(chunk.embedding, SearchOptions(top_k=1))
        assert len(results) == 1
        assert results[0].score == pytest.approx(1.0, abs=0.001)
        assert results[0].chunk.id == chunk.id

    @pytest.mark.asyncio
    async def test_search_ranking(self):
        store = InMemoryVectorStore(VectorStoreConfig(dimension=8))
        await store.initialize()
        chunks = _make_chunks(20)
        await store.add_chunks(chunks)

        results = await store.search(chunks[0].embedding, SearchOptions(top_k=5))
        assert len(results) <= 5
        # First result should be self
        assert results[0].chunk.id == chunks[0].id
        # Scores should be descending
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score

    @pytest.mark.asyncio
    async def test_search_respects_top_k(self):
        store = InMemoryVectorStore(VectorStoreConfig(dimension=8))
        await store.initialize()
        chunks = _make_chunks(20)
        await store.add_chunks(chunks)

        results = await store.search(chunks[0].embedding, SearchOptions(top_k=3))
        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_search_respects_threshold(self):
        store = InMemoryVectorStore(VectorStoreConfig(dimension=8))
        await store.initialize()
        chunks = _make_chunks(10)
        await store.add_chunks(chunks)

        results = await store.search(
            chunks[0].embedding,
            SearchOptions(top_k=10, threshold=0.99),
        )
        # Only self-match should pass 0.99 threshold
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_empty_store(self):
        store = InMemoryVectorStore(VectorStoreConfig(dimension=8))
        await store.initialize()
        results = await store.search([0.0] * 8, SearchOptions(top_k=5))
        assert results == []

    @pytest.mark.asyncio
    async def test_search_wrong_dimension_raises(self):
        store = InMemoryVectorStore(VectorStoreConfig(dimension=8))
        await store.initialize()
        with pytest.raises(VectorStoreError, match="mismatch"):
            await store.search([0.0] * 16)


class TestInMemoryVectorStoreGetUpdate:
    """Test get and update operations."""

    @pytest.mark.asyncio
    async def test_get_chunk(self):
        store = InMemoryVectorStore(VectorStoreConfig(dimension=8))
        await store.initialize()
        chunk = _make_chunk("test content")
        await store.add_chunks([chunk])

        retrieved = await store.get_chunk(chunk.id)
        assert retrieved is not None
        assert retrieved.content == "test content"

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(self):
        store = InMemoryVectorStore(VectorStoreConfig(dimension=8))
        await store.initialize()
        assert await store.get_chunk(uuid4()) is None

    @pytest.mark.asyncio
    async def test_update_chunk(self):
        store = InMemoryVectorStore(VectorStoreConfig(dimension=8))
        await store.initialize()
        chunk = _make_chunk("original content")
        await store.add_chunks([chunk])

        chunk.content = "updated content"
        await store.update_chunk(chunk)

        retrieved = await store.get_chunk(chunk.id)
        assert retrieved.content == "updated content"

    @pytest.mark.asyncio
    async def test_update_nonexistent_raises(self):
        store = InMemoryVectorStore(VectorStoreConfig(dimension=8))
        await store.initialize()
        chunk = _make_chunk("test")
        with pytest.raises(NotFoundError):
            await store.update_chunk(chunk)


class TestInMemoryVectorStoreStats:
    """Test stats reporting."""

    @pytest.mark.asyncio
    async def test_get_stats(self):
        store = InMemoryVectorStore(VectorStoreConfig(dimension=8))
        await store.initialize()
        chunks = _make_chunks(10)
        await store.add_chunks(chunks)

        stats = await store.get_stats()
        assert stats["store_type"] == "in_memory"
        assert stats["chunk_count"] == 10
        assert stats["dimension"] == 8
        assert stats["memory_estimated_mb"] > 0