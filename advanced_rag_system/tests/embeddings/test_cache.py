"""Tests for embedding cache."""

from uuid import uuid4

import pytest
from src.core.exceptions import CacheError
from src.core.types import DocumentChunk
from src.embeddings.cache import (
    CacheEntry,
    CacheStats,
    EmbeddingCache,
    MemoryCacheBackend,
)


class TestMemoryCacheBackend:
    """Test cases for MemoryCacheBackend."""

    @pytest.fixture
    async def backend(self):
        """Create cache backend fixture."""
        backend = MemoryCacheBackend(max_size=5, max_memory_mb=1)
        yield backend
        await backend.clear()

    @pytest.mark.asyncio
    async def test_get_missing_key(self, backend: MemoryCacheBackend) -> None:
        """Test getting non-existent key."""
        result = await backend.get("missing")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_and_get(self, backend: MemoryCacheBackend) -> None:
        """Test setting and getting value."""
        embedding = [0.1, 0.2, 0.3]
        await backend.set("key1", embedding, ttl=3600)
        result = await backend.get("key1")
        assert result == embedding

    @pytest.mark.asyncio
    async def test_expired_entry(self, backend: MemoryCacheBackend) -> None:
        """Test that expired entries are removed."""
        embedding = [0.1, 0.2, 0.3]
        await backend.set("key1", embedding, ttl=0)  # Already expired
        result = await backend.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, backend: MemoryCacheBackend) -> None:
        """Test deleting entry."""
        embedding = [0.1, 0.2, 0.3]
        await backend.set("key1", embedding, ttl=3600)
        deleted = await backend.delete("key1")
        assert deleted is True
        result = await backend.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_missing(self, backend: MemoryCacheBackend) -> None:
        """Test deleting non-existent key."""
        deleted = await backend.delete("missing")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_clear(self, backend: MemoryCacheBackend) -> None:
        """Test clearing cache."""
        await backend.set("key1", [0.1], ttl=3600)
        await backend.set("key2", [0.2], ttl=3600)
        await backend.clear()
        assert await backend.get("key1") is None
        assert await backend.get("key2") is None

    @pytest.mark.asyncio
    async def test_lru_eviction(self, backend: MemoryCacheBackend) -> None:
        """Test LRU eviction when max size reached."""
        # Add more items than max_size
        for i in range(7):
            await backend.set(f"key{i}", [float(i)], ttl=3600)

        # First items should be evicted
        assert await backend.get("key0") is None
        assert await backend.get("key1") is None
        # Recent items should still exist
        assert await backend.get("key5") is not None
        assert await backend.get("key6") is not None

    def test_get_stats(self, backend: MemoryCacheBackend) -> None:
        """Test getting statistics."""
        stats = backend.get_stats()
        assert "size" in stats
        assert "memory_mb" in stats
        assert "max_size" in stats


class TestEmbeddingCache:
    """Test cases for EmbeddingCache."""

    @pytest.fixture
    async def cache(self):
        """Create embedding cache fixture."""
        cache = EmbeddingCache()
        yield cache
        await cache.clear()

    @pytest.mark.asyncio
    async def test_get_missing(self, cache: EmbeddingCache) -> None:
        """Test getting non-cached embedding."""
        result = await cache.get("test text")
        assert result is None
        assert cache.get_stats().misses == 1

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache: EmbeddingCache) -> None:
        """Test caching and retrieving embedding."""
        embedding = [0.1, 0.2, 0.3]
        await cache.set("test text", embedding)
        result = await cache.get("test text")
        assert result == embedding
        assert cache.get_stats().hits == 1

    @pytest.mark.asyncio
    async def test_case_insensitive(self, cache: EmbeddingCache) -> None:
        """Test that cache keys are case insensitive."""
        embedding = [0.1, 0.2, 0.3]
        await cache.set("Test Text", embedding)
        result = await cache.get("test text")
        assert result == embedding

    @pytest.mark.asyncio
    async def test_whitespace_normalization(self, cache: EmbeddingCache) -> None:
        """Test that whitespace is normalized in keys."""
        embedding = [0.1, 0.2, 0.3]
        await cache.set("  test text  ", embedding)
        result = await cache.get("test text")
        assert result == embedding

    @pytest.mark.asyncio
    async def test_get_batch(self, cache: EmbeddingCache) -> None:
        """Test batch get operation."""
        embedding1 = [0.1, 0.2]
        embedding2 = [0.3, 0.4]
        await cache.set("text1", embedding1)
        await cache.set("text2", embedding2)

        results = await cache.get_batch(["text1", "text2", "text3"])
        assert results["text1"] == embedding1
        assert results["text2"] == embedding2
        assert results["text3"] is None

    @pytest.mark.asyncio
    async def test_set_batch(self, cache: EmbeddingCache) -> None:
        """Test batch set operation."""
        texts = ["text1", "text2"]
        embeddings = [[0.1, 0.2], [0.3, 0.4]]
        await cache.set_batch(texts, embeddings)

        assert await cache.get("text1") == [0.1, 0.2]
        assert await cache.get("text2") == [0.3, 0.4]

    @pytest.mark.asyncio
    async def test_set_batch_length_mismatch(self, cache: EmbeddingCache) -> None:
        """Test batch set with mismatched lengths raises error."""
        with pytest.raises(CacheError) as exc_info:
            await cache.set_batch(["text1"], [[0.1], [0.2]])
        assert exc_info.value.error_code == "CACHE_ERROR"

    @pytest.mark.asyncio
    async def test_delete(self, cache: EmbeddingCache) -> None:
        """Test deleting cached embedding."""
        await cache.set("text", [0.1, 0.2])
        deleted = await cache.delete("text")
        assert deleted is True
        assert await cache.get("text") is None

    @pytest.mark.asyncio
    async def test_document_chunks(self, cache: EmbeddingCache) -> None:
        """Test caching for document chunks."""
        chunks = [
            DocumentChunk(document_id=uuid4(), content="chunk1"),
            DocumentChunk(document_id=uuid4(), content="chunk2"),
        ]
        embeddings = [[0.1, 0.2], [0.3, 0.4]]

        await cache.set_document_chunks(chunks, embeddings)
        results = await cache.get_document_chunks(chunks)

        assert results[0] == [0.1, 0.2]
        assert results[1] == [0.3, 0.4]

    def test_get_stats(self, cache: EmbeddingCache) -> None:
        """Test getting cache statistics."""
        stats = cache.get_stats()
        assert isinstance(stats, CacheStats)
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.hit_rate == 0.0


class TestCacheStats:
    """Test cases for CacheStats."""

    def test_default_values(self) -> None:
        """Test default statistic values."""
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        assert stats.total_requests == 0
        assert stats.hit_rate == 0.0
        assert stats.memory_usage_bytes == 0

    def test_custom_values(self) -> None:
        """Test custom statistic values."""
        stats = CacheStats(
            hits=100,
            misses=50,
            evictions=10,
            total_requests=150,
            hit_rate=0.67,
            memory_usage_bytes=1024,
        )
        assert stats.hits == 100
        assert stats.misses == 50
        assert stats.hit_rate == 0.67
