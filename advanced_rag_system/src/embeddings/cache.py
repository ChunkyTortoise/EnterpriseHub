"""Embedding cache implementation for Advanced RAG System.

Provides multi-layer caching for embeddings to reduce API costs
and latency. Supports both in-memory (L1) and Redis (L2) caching.
"""

from __future__ import annotations

import hashlib
import json
import pickle
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Protocol

from src.core.config import get_settings
from src.core.exceptions import CacheError
from src.core.types import DocumentChunk


class CacheBackend(Protocol):
    """Protocol for cache backend implementations."""

    async def get(self, key: str) -> Optional[Any]: ...
    async def set(self, key: str, value: Any, ttl: int) -> None: ...
    async def delete(self, key: str) -> bool: ...
    async def clear(self) -> None: ...


@dataclass
class CacheEntry:
    """Cache entry with metadata.

    Attributes:
        key: Cache key
        value: Cached value (embedding vector)
        created_at: Creation timestamp
        expires_at: Expiration timestamp
        hit_count: Number of cache hits
        size_bytes: Size of cached data
    """

    key: str
    value: List[float]
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    size_bytes: int = 0


@dataclass
class CacheStats:
    """Cache performance statistics.

    Attributes:
        hits: Number of cache hits
        misses: Number of cache misses
        evictions: Number of evictions
        total_requests: Total cache requests
        hit_rate: Cache hit rate (0-1)
        memory_usage_bytes: Current memory usage
    """

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    hit_rate: float = 0.0
    memory_usage_bytes: int = 0


class MemoryCacheBackend:
    """In-memory LRU cache backend."""

    def __init__(self, max_size: int = 10000, max_memory_mb: int = 100) -> None:
        """Initialize memory cache.

        Args:
            max_size: Maximum number of entries
            max_memory_mb: Maximum memory usage in MB
        """
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []
        self._current_memory = 0

    async def get(self, key: str) -> Optional[List[float]]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        entry = self._cache.get(key)
        if entry is None:
            return None

        if datetime.utcnow() > entry.expires_at:
            await self.delete(key)
            return None

        # Update access order
        self._access_order.remove(key)
        self._access_order.append(key)
        entry.hit_count += 1

        return entry.value

    async def set(self, key: str, value: List[float], ttl: int) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        # Calculate size
        size = len(pickle.dumps(value))

        # Check if we need to evict
        while (
            len(self._cache) >= self.max_size
            or self._current_memory + size > self.max_memory_bytes
        ):
            if not self._access_order:
                break
            await self._evict_lru()

        # Create entry
        now = datetime.utcnow()
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=now,
            expires_at=now + timedelta(seconds=ttl),
            size_bytes=size,
        )

        # Remove old entry if exists
        if key in self._cache:
            old_entry = self._cache[key]
            self._current_memory -= old_entry.size_bytes
            self._access_order.remove(key)

        # Add new entry
        self._cache[key] = entry
        self._access_order.append(key)
        self._current_memory += size

    async def delete(self, key: str) -> bool:
        """Delete entry from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        if key not in self._cache:
            return False

        entry = self._cache.pop(key)
        self._current_memory -= entry.size_bytes
        self._access_order.remove(key)
        return True

    async def clear(self) -> None:
        """Clear all entries from cache."""
        self._cache.clear()
        self._access_order.clear()
        self._current_memory = 0

    async def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._access_order:
            return

        oldest_key = self._access_order.pop(0)
        entry = self._cache.pop(oldest_key)
        self._current_memory -= entry.size_bytes

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary of statistics
        """
        return {
            "size": len(self._cache),
            "memory_mb": self._current_memory / (1024 * 1024),
            "max_size": self.max_size,
            "max_memory_mb": self.max_memory_bytes / (1024 * 1024),
        }


class RedisCacheBackend:
    """Redis cache backend (placeholder for future implementation)."""

    def __init__(self, redis_url: str) -> None:
        """Initialize Redis cache.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self._client: Optional[Any] = None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis (placeholder)."""
        # Placeholder - would use aioredis in production
        return None

    async def set(self, key: str, value: Any, ttl: int) -> None:
        """Set value in Redis (placeholder)."""
        pass

    async def delete(self, key: str) -> bool:
        """Delete from Redis (placeholder)."""
        return False

    async def clear(self) -> None:
        """Clear Redis cache (placeholder)."""
        pass


class EmbeddingCache:
    """Multi-layer embedding cache.

    Provides caching for embeddings to reduce API costs and latency.
    Uses in-memory L1 cache by default, with optional Redis L2 cache.

    Example:
        ```python
        cache = EmbeddingCache()

        # Try to get cached embedding
        embedding = await cache.get("text to embed")
        if embedding is None:
            # Generate and cache
            embedding = await provider.embed(["text to embed"])
            await cache.set("text to embed", embedding[0])
        ```
    """

    def __init__(
        self,
        l1_cache: Optional[MemoryCacheBackend] = None,
        l2_cache: Optional[RedisCacheBackend] = None,
        default_ttl: int = 3600,
    ) -> None:
        """Initialize embedding cache.

        Args:
            l1_cache: L1 (memory) cache backend
            l2_cache: L2 (Redis) cache backend
            default_ttl: Default TTL in seconds
        """
        settings = get_settings()

        self.l1 = l1_cache or MemoryCacheBackend()
        self.l2 = l2_cache
        self.default_ttl = default_ttl
        self.enabled = settings.cache_enabled

        self._stats = CacheStats()

    def _generate_key(self, text: str) -> str:
        """Generate cache key for text.

        Uses SHA-256 hash of normalized text for consistent keys.

        Args:
            text: Text to hash

        Returns:
            Cache key string
        """
        # Normalize text
        normalized = text.strip().lower()
        # Generate hash
        return hashlib.sha256(normalized.encode()).hexdigest()

    async def get(self, text: str) -> Optional[List[float]]:
        """Get cached embedding for text.

        Args:
            text: Text to look up

        Returns:
            Cached embedding or None
        """
        if not self.enabled:
            return None

        self._stats.total_requests += 1
        key = self._generate_key(text)

        # Try L1 first
        value = await self.l1.get(key)
        if value is not None:
            self._stats.hits += 1
            self._update_hit_rate()
            return value

        # Try L2 if configured
        if self.l2 is not None:
            value = await self.l2.get(key)
            if value is not None:
                # Promote to L1
                await self.l1.set(key, value, self.default_ttl)
                self._stats.hits += 1
                self._update_hit_rate()
                return value

        self._stats.misses += 1
        self._update_hit_rate()
        return None

    async def get_batch(self, texts: List[str]) -> Dict[str, Optional[List[float]]]:
        """Get cached embeddings for multiple texts.

        Args:
            texts: List of texts to look up

        Returns:
            Dictionary mapping text to embedding (or None)
        """
        if not self.enabled:
            return {text: None for text in texts}

        results = {}
        for text in texts:
            results[text] = await self.get(text)
        return results

    async def set(
        self,
        text: str,
        embedding: List[float],
        ttl: Optional[int] = None,
    ) -> None:
        """Cache embedding for text.

        Args:
            text: Original text
            embedding: Embedding vector
            ttl: Optional custom TTL
        """
        if not self.enabled:
            return

        key = self._generate_key(text)
        cache_ttl = ttl or self.default_ttl

        # Always set in L1
        await self.l1.set(key, embedding, cache_ttl)

        # Also set in L2 if configured
        if self.l2 is not None:
            await self.l2.set(key, embedding, cache_ttl)

    async def set_batch(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        ttl: Optional[int] = None,
    ) -> None:
        """Cache multiple embeddings.

        Args:
            texts: List of texts
            embeddings: List of embedding vectors
            ttl: Optional custom TTL
        """
        if len(texts) != len(embeddings):
            raise CacheError(
                message="Texts and embeddings must have same length",
                error_code="LENGTH_MISMATCH",
            )

        for text, embedding in zip(texts, embeddings):
            await self.set(text, embedding, ttl)

    async def delete(self, text: str) -> bool:
        """Delete cached embedding.

        Args:
            text: Text to delete from cache

        Returns:
            True if deleted from any layer
        """
        key = self._generate_key(text)

        deleted = await self.l1.delete(key)
        if self.l2 is not None:
            deleted = await self.l2.delete(key) or deleted

        return deleted

    async def clear(self) -> None:
        """Clear all cached embeddings."""
        await self.l1.clear()
        if self.l2 is not None:
            await self.l2.clear()

        self._stats = CacheStats()

    def get_stats(self) -> CacheStats:
        """Get cache statistics.

        Returns:
            CacheStats object with current statistics
        """
        # Update memory usage from L1
        l1_stats = self.l1.get_stats()
        self._stats.memory_usage_bytes = int(l1_stats.get("memory_mb", 0) * 1024 * 1024)

        return self._stats

    def _update_hit_rate(self) -> None:
        """Update the cache hit rate statistic."""
        if self._stats.total_requests > 0:
            self._stats.hit_rate = self._stats.hits / self._stats.total_requests

    async def get_document_chunks(
        self,
        chunks: List[DocumentChunk],
    ) -> Dict[int, Optional[List[float]]]:
        """Get cached embeddings for document chunks.

        Args:
            chunks: List of document chunks

        Returns:
            Dictionary mapping chunk index to embedding
        """
        results = {}
        for i, chunk in enumerate(chunks):
            results[i] = await self.get(chunk.content)
        return results

    async def set_document_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
    ) -> None:
        """Cache embeddings for document chunks.

        Args:
            chunks: List of document chunks
            embeddings: List of embedding vectors
        """
        for chunk, embedding in zip(chunks, embeddings):
            await self.set(chunk.content, embedding)