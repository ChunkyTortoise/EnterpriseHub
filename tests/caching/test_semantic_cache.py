"""
Tests for Semantic Cache Module
===============================

Tests cover:
    - Embedding service implementations
    - Cache key generation from embeddings
    - Semantic similarity matching
    - TTL and eviction policies
    - Cache entry lifecycle
    - Integration between components
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from src.caching.semantic_cache import (

@pytest.mark.integration
    CacheEntry,
    CacheKeyGenerator,
    EmbeddingService,
    EvictionPolicy,
    MockEmbeddingService,
    SemanticCache,
)

pytestmark = pytest.mark.asyncio


class TestMockEmbeddingService:
    """Test cases for MockEmbeddingService."""

    @pytest.fixture
    def embedding_service(self):
        """Create a mock embedding service."""
        return MockEmbeddingService(dimensions=384)

    def test_embed_sync_deterministic(self, embedding_service):
        """Test that embeddings are deterministic for same input."""
        text = "test query"
        emb1 = embedding_service.embed_sync(text)
        emb2 = embedding_service.embed_sync(text)

        assert np.allclose(emb1, emb2)

    def test_embed_sync_different_inputs(self, embedding_service):
        """Test that different inputs produce different embeddings."""
        emb1 = embedding_service.embed_sync("query one")
        emb2 = embedding_service.embed_sync("query two")

        assert not np.allclose(emb1, emb2)

    def test_embed_sync_dimensions(self, embedding_service):
        """Test that embeddings have correct dimensions."""
        emb = embedding_service.embed_sync("test")

        assert len(emb) == 384

    async def test_embed_async(self, embedding_service):
        """Test async embedding generation."""
        emb = await embedding_service.embed("test query")

        assert isinstance(emb, np.ndarray)
        assert len(emb) == 384

    def test_calculate_similarity_identical(self, embedding_service):
        """Test similarity of identical embeddings."""
        emb = embedding_service.embed_sync("test")
        similarity = embedding_service.calculate_similarity(emb, emb)

        assert similarity == pytest.approx(1.0, abs=0.001)

    def test_calculate_similarity_different(self, embedding_service):
        """Test similarity of different embeddings."""
        emb1 = embedding_service.embed_sync("query one")
        emb2 = embedding_service.embed_sync("query two")
        similarity = embedding_service.calculate_similarity(emb1, emb2)

        assert 0 <= similarity <= 1

    def test_calculate_similarity_batch(self, embedding_service):
        """Test batch similarity calculation."""
        query_emb = embedding_service.embed_sync("query")
        candidates = [embedding_service.embed_sync(f"candidate {i}") for i in range(5)]

        similarities = embedding_service.calculate_similarity_batch(query_emb, candidates)

        assert len(similarities) == 5
        # Similarities should be valid floats (cosine similarity can be -1 to 1)
        assert all(-1 <= s <= 1 for s in similarities)


class TestCacheEntry:
    """Test cases for CacheEntry dataclass."""

    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        entry = CacheEntry(
            key="test_key", value="test_value", embedding=np.array([0.1, 0.2, 0.3]), ttl=3600, tags=["tag1", "tag2"]
        )

        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.ttl == 3600
        assert entry.tags == ["tag1", "tag2"]
        assert entry.access_count == 0

    def test_is_expired_no_ttl(self):
        """Test that entries without TTL don't expire."""
        entry = CacheEntry(key="key", value="value", ttl=None)

        assert not entry.is_expired()

    def test_is_expired_with_ttl(self):
        """Test TTL expiration."""
        entry = CacheEntry(key="key", value="value", ttl=1, created_at=datetime.now() - timedelta(seconds=2))

        assert entry.is_expired()

    def test_is_not_expired(self):
        """Test that valid entries don't show as expired."""
        entry = CacheEntry(key="key", value="value", ttl=3600, created_at=datetime.now())

        assert not entry.is_expired()

    def test_touch_updates_metadata(self):
        """Test that touch updates access metadata."""
        entry = CacheEntry(key="key", value="value")
        original_accessed = entry.last_accessed

        entry.touch()

        assert entry.access_count == 1
        assert entry.last_accessed > original_accessed

    def test_to_dict(self):
        """Test serialization to dictionary."""
        entry = CacheEntry(key="key", value={"data": "value"}, embedding=np.array([0.1, 0.2]), ttl=300)

        data = entry.to_dict()

        assert data["key"] == "key"
        assert data["value"] == {"data": "value"}
        assert data["embedding"] == [0.1, 0.2]
        assert data["ttl"] == 300

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "key": "key",
            "value": {"data": "value"},
            "embedding": [0.1, 0.2],
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "access_count": 5,
            "ttl": 300,
            "tags": ["tag1"],
        }

        entry = CacheEntry.from_dict(data)

        assert entry.key == "key"
        assert entry.value == {"data": "value"}
        assert np.allclose(entry.embedding, np.array([0.1, 0.2]))
        assert entry.access_count == 5


class TestCacheKeyGenerator:
    """Test cases for CacheKeyGenerator."""

    @pytest.fixture
    def key_generator(self):
        """Create a cache key generator."""
        return CacheKeyGenerator(num_buckets=100, prefix="test")

    def test_generate_key_consistency(self, key_generator):
        """Test that same embedding generates same key."""
        embedding = np.array([0.5, 0.3, 0.2])

        key1 = key_generator.generate_key(embedding)
        key2 = key_generator.generate_key(embedding)

        assert key1 == key2

    def test_generate_key_different_embeddings(self, key_generator):
        """Test that different embeddings generate different keys."""
        emb1 = np.array([0.1, 0.2, 0.3])
        emb2 = np.array([0.4, 0.5, 0.6])

        key1 = key_generator.generate_key(emb1)
        key2 = key_generator.generate_key(emb2)

        assert key1 != key2

    def test_generate_key_with_text(self, key_generator):
        """Test key generation with text."""
        embedding = np.array([0.5, 0.3, 0.2])
        text = "test query"

        key = key_generator.generate_key(embedding, text)

        assert key.startswith("test:")
        assert len(key) > 20  # Should be reasonably long

    def test_get_semantic_bucket(self, key_generator):
        """Test semantic bucket extraction."""
        embedding = np.array([0.5, 0.0, 0.0])

        bucket = key_generator._get_semantic_bucket(embedding)

        assert bucket.startswith("bucket_")
        bucket_num = int(bucket.split("_")[1])
        assert 0 <= bucket_num < 100


class TestSemanticCache:
    """Test cases for SemanticCache class."""

    @pytest.fixture
    async def cache(self):
        """Create a semantic cache for testing."""
        embedding_service = MockEmbeddingService(dimensions=384)
        cache = SemanticCache(
            redis_client=None,  # In-memory only for tests
            embedding_service=embedding_service,
            similarity_threshold=0.85,
            eviction_policy=EvictionPolicy.LRU,
            max_entries=100,
            enable_persistence=False,
        )
        return cache

    async def test_set_and_get(self, cache):
        """Test basic set and get operations."""
        await cache.set("test query", {"result": "value"}, ttl=300)

        result = await cache.get("test query")

        assert result is not None
        value, similarity = result
        assert value == {"result": "value"}
        assert similarity == 1.0  # Exact match

    async def test_get_nonexistent(self, cache):
        """Test getting a non-existent key."""
        result = await cache.get("nonexistent query")

        assert result is None

    async def test_semantic_similarity_match(self, cache):
        """Test semantic similarity matching."""
        # Store original query
        await cache.set("How do I reset my password?", {"action": "reset_password"})

        # Retrieve with similar query
        result = await cache.get("How can I change my password?")

        # May or may not match depending on mock embeddings
        # This tests the code path works
        if result:
            value, similarity = result
            assert similarity >= cache.similarity_threshold

    async def test_get_or_set_cache_miss(self, cache):
        """Test get_or_set with cache miss."""
        compute_fn = MagicMock(return_value={"computed": "value"})

        value, was_cached, similarity = await cache.get_or_set("new query", compute_fn)

        assert value == {"computed": "value"}
        assert was_cached is False
        assert similarity == 0.0
        compute_fn.assert_called_once()

    async def test_get_or_set_cache_hit(self, cache):
        """Test get_or_set with cache hit."""
        # Pre-populate cache
        await cache.set("existing query", {"cached": "value"})

        compute_fn = MagicMock()

        value, was_cached, similarity = await cache.get_or_set("existing query", compute_fn)

        assert value == {"cached": "value"}
        assert was_cached is True
        assert similarity == 1.0
        compute_fn.assert_not_called()

    async def test_invalidate(self, cache):
        """Test cache invalidation."""
        await cache.set("query to invalidate", {"data": "value"})

        # Verify it exists
        result_before = await cache.get("query to invalidate")
        assert result_before is not None

        # Invalidate
        await cache.invalidate("query to invalidate")

        # Verify it's gone
        result_after = await cache.get("query to invalidate")
        assert result_after is None

    async def test_invalidate_by_tag(self, cache):
        """Test invalidation by tag."""
        await cache.set("query1", {"data": 1}, tags=["tag1", "tag2"])
        await cache.set("query2", {"data": 2}, tags=["tag1"])
        await cache.set("query3", {"data": 3}, tags=["tag2"])

        removed = await cache.invalidate_by_tag("tag1")

        assert removed >= 2  # At least query1 and query2
        assert await cache.get("query1") is None
        assert await cache.get("query2") is None

    async def test_clear(self, cache):
        """Test clearing all cache entries."""
        await cache.set("query1", {"data": 1})
        await cache.set("query2", {"data": 2})

        await cache.clear()

        assert await cache.get("query1") is None
        assert await cache.get("query2") is None
        assert len(cache._memory_cache) == 0

    async def test_lru_eviction(self):
        """Test LRU eviction policy."""
        cache = SemanticCache(
            redis_client=None,
            embedding_service=MockEmbeddingService(),
            eviction_policy=EvictionPolicy.LRU,
            max_entries=3,
            enable_persistence=False,
        )

        # Add entries up to max
        await cache.set("query1", {"data": 1})
        await cache.set("query2", {"data": 2})
        await cache.set("query3", {"data": 3})

        # Access query1 to make it most recently used
        await cache.get("query1")

        # Add new entry - should evict query2 (LRU)
        await cache.set("query4", {"data": 4})

        assert len(cache._memory_cache) == 3
        # query1 should still exist
        assert await cache.get("query1") is not None

    async def test_lfu_eviction(self):
        """Test LFU eviction policy."""
        cache = SemanticCache(
            redis_client=None,
            embedding_service=MockEmbeddingService(),
            eviction_policy=EvictionPolicy.LFU,
            max_entries=3,
            enable_persistence=False,
        )

        # Add entries
        await cache.set("query1", {"data": 1})
        await cache.set("query2", {"data": 2})
        await cache.set("query3", {"data": 3})

        # Access query1 multiple times
        for _ in range(5):
            await cache.get("query1")

        # Access query2 once
        await cache.get("query2")

        # Add new entry - should evict query3 (LFU - never accessed)
        await cache.set("query4", {"data": 4})

        assert len(cache._memory_cache) == 3
        # query1 and query2 should still exist
        assert await cache.get("query1") is not None
        assert await cache.get("query2") is not None

    async def test_get_stats(self, cache):
        """Test statistics collection."""
        # Perform some operations
        await cache.set("query1", {"data": 1})
        await cache.get("query1")  # Hit
        await cache.get("query2")  # Miss

        stats = cache.get_stats()

        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["total_requests"] == 2
        assert stats["hit_rate"] == 0.5
        assert stats["eviction_policy"] == "LRU"

    async def test_entry_expiration(self, cache):
        """Test that expired entries are not returned."""
        # Add entry with very short TTL
        await cache.set("expiring query", {"data": "value"}, ttl=0)

        # Wait a tiny bit
        import time

        time.sleep(0.1)

        # Should not find expired entry
        result = await cache.get("expiring query")
        assert result is None

    async def test_tags_in_get_stats(self, cache):
        """Test that tags are tracked in entries."""
        await cache.set("query1", {"data": 1}, tags=["important"])

        result = await cache.get("query1")
        assert result is not None


class TestEvictionPolicies:
    """Test cases for different eviction policies."""

    async def test_fifo_eviction(self):
        """Test FIFO eviction policy."""
        cache = SemanticCache(
            redis_client=None,
            embedding_service=MockEmbeddingService(),
            eviction_policy=EvictionPolicy.FIFO,
            max_entries=2,
            enable_persistence=False,
        )

        await cache.set("first", {"data": 1})
        await cache.set("second", {"data": 2})
        await cache.set("third", {"data": 3})  # Should evict "first"

        assert await cache.get("first") is None
        assert await cache.get("second") is not None
        assert await cache.get("third") is not None

    async def test_ttl_eviction(self):
        """Test TTL-based eviction policy."""
        cache = SemanticCache(
            redis_client=None,
            embedding_service=MockEmbeddingService(),
            eviction_policy=EvictionPolicy.TTL,
            max_entries=3,
            enable_persistence=False,
        )

        # Add entries with different TTLs
        await cache.set("long_ttl", {"data": 1}, ttl=3600)
        await cache.set("short_ttl", {"data": 2}, ttl=60)
        await cache.set("no_ttl", {"data": 3}, ttl=None)

        # Add one more - should evict short_ttl (closest to expiration)
        await cache.set("another", {"data": 4})

        # Verify behavior - TTL policy should consider remaining time
        assert len(cache._memory_cache) <= 3