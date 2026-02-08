"""
Semantic Cache Module
=====================

Embedding-based cache with semantic similarity matching, TTL policies, and eviction strategies.

Features:
    - Semantic similarity matching using vector embeddings
    - Multiple embedding providers (OpenAI, SentenceTransformers, mock)
    - Configurable TTL and eviction policies
    - Cache key generation from embeddings
    - LRU, LFU, and custom eviction strategies

Example:
    >>> from src.caching import SemanticCache, EvictionPolicy
    >>>
    >>> cache = SemanticCache(
    ...     redis_client=redis,
    ...     similarity_threshold=0.85,
    ...     eviction_policy=EvictionPolicy.LRU,
    ...     max_entries=10000
    ... )
    >>>
    >>> # Store with semantic key
    >>> await cache.set("How do I reset my password?", response, ttl=3600)
    >>>
    >>> # Retrieve with similar query
    >>> result = await cache.get("How to change my password?")
    >>> # Returns cached response if similarity >= threshold

Classes:
    SemanticCache: Main cache implementation
    EmbeddingService: Base class for embedding providers
    CacheEntry: Data class for cache entries
    EvictionPolicy: Enum for eviction strategies
"""

import asyncio
import hashlib
import json
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np

# Optional dependencies
try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from sklearn.metrics.pairwise import cosine_similarity

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from src.caching.redis_client import BaseRedisClient, RedisClient


class EvictionPolicy(Enum):
    """Cache eviction policies."""

    LRU = auto()  # Least Recently Used
    LFU = auto()  # Least Frequently Used
    FIFO = auto()  # First In First Out
    TTL = auto()  # Time To Live based
    ADAPTIVE = auto()  # Adaptive based on hit rate


@dataclass
class CacheEntry:
    """
    Represents a cached entry with metadata.

    Attributes:
        key: Unique cache key
        value: Cached value
        embedding: Vector embedding of the query
        created_at: Timestamp when entry was created
        last_accessed: Timestamp of last access
        access_count: Number of times accessed
        ttl: Time to live in seconds
        tags: Optional tags for categorization
    """

    key: str
    value: Any
    embedding: Optional[np.ndarray] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    ttl: Optional[int] = None
    tags: List[str] = field(default_factory=list)

    def is_expired(self) -> bool:
        """Check if the entry has expired."""
        if self.ttl is None:
            return False
        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed > self.ttl

    def touch(self) -> None:
        """Update access metadata."""
        self.last_accessed = datetime.now()
        self.access_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "key": self.key,
            "value": self.value,
            "embedding": self.embedding.tolist() if self.embedding is not None else None,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "ttl": self.ttl,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        """Create from dictionary."""
        entry = cls(
            key=data["key"],
            value=data["value"],
            embedding=np.array(data["embedding"]) if data.get("embedding") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            access_count=data.get("access_count", 0),
            ttl=data.get("ttl"),
            tags=data.get("tags", []),
        )
        return entry


@dataclass
class CacheKeyComponents:
    """Components used to generate a cache key from embedding."""

    embedding_hash: str
    semantic_bucket: str
    timestamp_hash: str

    def to_key(self, prefix: str = "semantic") -> str:
        """Generate full cache key."""
        return f"{prefix}:{self.semantic_bucket}:{self.embedding_hash}"


class EmbeddingService(ABC):
    """Abstract base class for embedding services."""

    @abstractmethod
    async def embed(self, text: str) -> np.ndarray:
        """Generate embedding for text."""
        pass

    @abstractmethod
    def embed_sync(self, text: str) -> np.ndarray:
        """Generate embedding synchronously."""
        pass

    @abstractmethod
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate similarity between two embeddings (0-1)."""
        pass

    def calculate_similarity_batch(
        self, query_embedding: np.ndarray, candidate_embeddings: List[np.ndarray]
    ) -> List[float]:
        """Calculate similarity between query and multiple candidates."""
        return [self.calculate_similarity(query_embedding, cand) for cand in candidate_embeddings]


class OpenAIEmbeddingService(EmbeddingService):
    """OpenAI embedding service implementation."""

    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-ada-002", dimensions: int = 1536):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed")

        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
        self.dimensions = dimensions

    async def embed(self, text: str) -> np.ndarray:
        """Generate embedding using OpenAI API."""
        response = await self.client.embeddings.create(model=self.model, input=text)
        embedding = response.data[0].embedding
        return np.array(embedding, dtype=np.float32)

    def embed_sync(self, text: str) -> np.ndarray:
        """Not recommended for OpenAI - raises RuntimeError."""
        raise RuntimeError("Use embed() for OpenAI embeddings (async)")

    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity."""
        return self._cosine_similarity(embedding1, embedding2)

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))


class SentenceTransformerEmbeddingService(EmbeddingService):
    """Sentence-transformers embedding service (local)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: str = "cpu"):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers not installed")

        self.model = SentenceTransformer(model_name, device=device)
        self.dimensions = self.model.get_sentence_embedding_dimension()

    async def embed(self, text: str) -> np.ndarray:
        """Generate embedding asynchronously (runs in thread pool)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_sync, text)

    def embed_sync(self, text: str) -> np.ndarray:
        """Generate embedding synchronously."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.astype(np.float32)

    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity."""
        if SKLEARN_AVAILABLE:
            return float(cosine_similarity([embedding1], [embedding2])[0][0])
        return self._cosine_similarity(embedding1, embedding2)

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))


class MockEmbeddingService(EmbeddingService):
    """Mock embedding service for testing."""

    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions
        self._cache: Dict[str, np.ndarray] = {}

    async def embed(self, text: str) -> np.ndarray:
        """Generate deterministic mock embedding."""
        return self.embed_sync(text)

    def embed_sync(self, text: str) -> np.ndarray:
        """Generate deterministic mock embedding synchronously."""
        if text in self._cache:
            return self._cache[text]

        # Create deterministic embedding based on text hash
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()

        # Generate pseudo-random but deterministic embedding
        np.random.seed(int.from_bytes(hash_bytes[:4], "little"))
        embedding = np.random.randn(self.dimensions).astype(np.float32)
        embedding = embedding / np.linalg.norm(embedding)  # Normalize

        np.random.seed()  # Reset seed
        self._cache[text] = embedding
        return embedding

    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity."""
        return self._cosine_similarity(embedding1, embedding2)

    def calculate_similarity_batch(
        self, query_embedding: np.ndarray, candidate_embeddings: List[np.ndarray]
    ) -> List[float]:
        """Calculate similarity with batch processing."""
        return super().calculate_similarity_batch(query_embedding, candidate_embeddings)

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))


class CacheKeyGenerator:
    """Generates cache keys from embeddings."""

    def __init__(self, num_buckets: int = 100, prefix: str = "semantic"):
        self.num_buckets = num_buckets
        self.prefix = prefix

    def generate_key(self, embedding: np.ndarray, text: Optional[str] = None) -> str:
        """
        Generate a cache key from embedding vector.

        Creates both a semantic bucket key and a unique hash key.
        The semantic bucket allows for fast filtering of candidates.
        """
        # Create semantic bucket from first few dimensions
        bucket = self._get_semantic_bucket(embedding)

        # Create unique hash from full embedding
        embedding_hash = self._hash_embedding(embedding)

        # Add text hash for additional uniqueness if provided
        text_hash = hashlib.sha256((text or "").encode()).hexdigest()[:8]

        return f"{self.prefix}:{bucket}:{embedding_hash}:{text_hash}"

    def _get_semantic_bucket(self, embedding: np.ndarray) -> str:
        """Get semantic bucket from embedding."""
        # Use quantized first dimension to create bucket
        first_dim = float(embedding[0]) if len(embedding) > 0 else 0.0
        bucket = int((first_dim + 1) * self.num_buckets / 2)
        bucket = max(0, min(bucket, self.num_buckets - 1))
        return f"bucket_{bucket:03d}"

    def _hash_embedding(self, embedding: np.ndarray) -> str:
        """Create hash from embedding."""
        # Quantize embedding for stable hashing
        quantized = (embedding * 1000).astype(np.int16)
        embedding_bytes = quantized.tobytes()
        return hashlib.sha256(embedding_bytes).hexdigest()[:16]

    def get_bucket_pattern(self, bucket: str) -> str:
        """Get Redis key pattern for a bucket."""
        return f"{self.prefix}:{bucket}:*"


class SemanticCache:
    """
    Semantic cache with embedding-based similarity matching.

    Features:
        - Semantic similarity matching for cache hits
        - Multiple eviction policies (LRU, LFU, FIFO, TTL, Adaptive)
        - Hybrid in-memory + Redis storage
        - Configurable similarity thresholds
        - Tag-based cache management

    Args:
        redis_client: Redis client instance
        embedding_service: Service for generating embeddings
        similarity_threshold: Minimum similarity for cache hit (0-1)
        eviction_policy: Cache eviction policy
        max_entries: Maximum number of in-memory entries
        default_ttl: Default time-to-live in seconds
        enable_persistence: Whether to persist to Redis
    """

    def __init__(
        self,
        redis_client: Optional[BaseRedisClient] = None,
        embedding_service: Optional[EmbeddingService] = None,
        similarity_threshold: float = 0.85,
        eviction_policy: EvictionPolicy = EvictionPolicy.LRU,
        max_entries: int = 10000,
        default_ttl: Optional[int] = 3600,
        enable_persistence: bool = True,
        key_prefix: str = "semantic",
    ):
        self.redis = redis_client
        self.embedding_service = embedding_service or MockEmbeddingService()
        self.similarity_threshold = similarity_threshold
        self.eviction_policy = eviction_policy
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self.enable_persistence = enable_persistence and redis_client is not None
        self.key_prefix = key_prefix

        # Cache key generator
        self.key_generator = CacheKeyGenerator(num_buckets=100, prefix=key_prefix)

        # In-memory cache storage
        self._memory_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._access_stats: Dict[str, int] = {}

        # Statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "semantic_hits": 0,
            "exact_hits": 0,
            "evictions": 0,
            "insertions": 0,
        }

        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def get(self, query: str, embedding: Optional[np.ndarray] = None) -> Optional[Tuple[Any, float]]:
        """
        Get cached value for query.

        Returns:
            Tuple of (value, similarity_score) or None if not found
        """
        # Generate embedding if not provided
        if embedding is None:
            embedding = await self.embedding_service.embed(query)

        async with self._lock:
            # Try exact match first
            exact_result = await self._get_exact_match(query, embedding)
            if exact_result:
                self._stats["hits"] += 1
                self._stats["exact_hits"] += 1
                return exact_result

            # Try semantic match
            semantic_result = await self._get_semantic_match(query, embedding)
            if semantic_result:
                self._stats["hits"] += 1
                self._stats["semantic_hits"] += 1
                return semantic_result

            self._stats["misses"] += 1
            return None

    async def set(
        self,
        query: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None,
        embedding: Optional[np.ndarray] = None,
    ) -> str:
        """
        Store value in cache.

        Returns:
            Cache key
        """
        if embedding is None:
            embedding = await self.embedding_service.embed(query)

        # Generate cache key
        cache_key = self.key_generator.generate_key(embedding, query)

        # Create cache entry
        entry = CacheEntry(
            key=cache_key, value=value, embedding=embedding, ttl=ttl or self.default_ttl, tags=tags or []
        )

        async with self._lock:
            # Store in memory
            await self._store_in_memory(cache_key, entry)

            # Persist to Redis if enabled
            if self.enable_persistence:
                await self._persist_to_redis(cache_key, entry)

            self._stats["insertions"] += 1

        return cache_key

    async def get_or_set(
        self, query: str, compute_fn: Callable[[], Any], ttl: Optional[int] = None, tags: Optional[List[str]] = None
    ) -> Tuple[Any, bool, float]:
        """
        Get cached value or compute and store.

        Returns:
            Tuple of (value, was_cached, similarity_score)
        """
        # Try to get from cache
        result = await self.get(query)
        if result:
            value, similarity = result
            return value, True, similarity

        # Compute value
        if asyncio.iscoroutinefunction(compute_fn):
            value = await compute_fn()
        else:
            value = compute_fn()

        # Store in cache
        await self.set(query, value, ttl, tags)

        return value, False, 0.0

    async def invalidate(self, query: str) -> bool:
        """Invalidate cache entry for query."""
        embedding = await self.embedding_service.embed(query)
        cache_key = self.key_generator.generate_key(embedding, query)

        async with self._lock:
            # Remove from memory
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]

            # Remove from Redis
            if self.enable_persistence and self.redis:
                try:
                    await self.redis.delete(cache_key)
                except Exception:
                    pass

        return True

    async def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate all entries with given tag."""
        removed = 0

        async with self._lock:
            # Remove from memory
            keys_to_remove = [key for key, entry in self._memory_cache.items() if tag in entry.tags]
            for key in keys_to_remove:
                del self._memory_cache[key]
                removed += 1

            # Remove from Redis (scan and delete)
            if self.enable_persistence and self.redis:
                try:
                    cursor = 0
                    while True:
                        cursor, keys = await self.redis.scan_keys(f"{self.key_prefix}:*", count=100, cursor=cursor)
                        for key in keys:
                            data = await self.redis.get(key)
                            if data:
                                entry = CacheEntry.from_dict(data)
                                if tag in entry.tags:
                                    await self.redis.delete(key)
                                    removed += 1
                        if cursor == 0:
                            break
                except Exception:
                    pass

        return removed

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._memory_cache.clear()
            self._access_stats.clear()

            if self.enable_persistence and self.redis:
                try:
                    await self.redis.delete_pattern(f"{self.key_prefix}:*")
                except Exception:
                    pass

    async def _get_exact_match(self, query: str, embedding: np.ndarray) -> Optional[Tuple[Any, float]]:
        """Try to get exact match from cache."""
        cache_key = self.key_generator.generate_key(embedding, query)

        # Check memory first
        if cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]
            if not entry.is_expired():
                entry.touch()
                self._update_access_stats(cache_key)
                return entry.value, 1.0
            else:
                del self._memory_cache[cache_key]

        # Check Redis
        if self.enable_persistence and self.redis:
            try:
                data = await self.redis.get(cache_key)
                if data:
                    entry = CacheEntry.from_dict(data)
                    if not entry.is_expired():
                        # Promote to memory
                        self._memory_cache[cache_key] = entry
                        entry.touch()
                        return entry.value, 1.0
            except Exception:
                pass

        return None

    async def _get_semantic_match(self, query: str, embedding: np.ndarray) -> Optional[Tuple[Any, float]]:
        """Try to find semantically similar entry."""
        best_match: Optional[CacheEntry] = None
        best_similarity = 0.0

        # Search in-memory cache
        for key, entry in self._memory_cache.items():
            if entry.is_expired() or entry.embedding is None:
                continue

            similarity = self.embedding_service.calculate_similarity(embedding, entry.embedding)

            if similarity > best_similarity and similarity >= self.similarity_threshold:
                best_similarity = similarity
                best_match = entry

        # If not found in memory and Redis is available, search there
        if best_match is None and self.enable_persistence and self.redis:
            try:
                # Get bucket to narrow search
                bucket = self.key_generator._get_semantic_bucket(embedding)
                pattern = self.key_generator.get_bucket_pattern(bucket)

                cursor = 0
                while True:
                    cursor, keys = await self.redis.scan_keys(pattern, count=100, cursor=cursor)
                    for key in keys:
                        data = await self.redis.get(key)
                        if data:
                            entry = CacheEntry.from_dict(data)
                            if entry.is_expired() or entry.embedding is None:
                                continue

                            similarity = self.embedding_service.calculate_similarity(embedding, entry.embedding)

                            if similarity > best_similarity and similarity >= self.similarity_threshold:
                                best_similarity = similarity
                                best_match = entry

                    if cursor == 0:
                        break
            except Exception:
                pass

        if best_match:
            best_match.touch()
            self._update_access_stats(best_match.key)
            return best_match.value, best_similarity

        return None

    async def _store_in_memory(self, key: str, entry: CacheEntry) -> None:
        """Store entry in memory with eviction."""
        # Check if we need to evict
        while len(self._memory_cache) >= self.max_entries:
            await self._evict_entry()

        # Store entry
        self._memory_cache[key] = entry
        self._access_stats[key] = 0

    async def _persist_to_redis(self, key: str, entry: CacheEntry) -> None:
        """Persist entry to Redis."""
        if not self.redis:
            return

        try:
            data = entry.to_dict()
            ttl = entry.ttl or self.default_ttl
            await self.redis.set(key, data, ttl=ttl)
        except Exception as e:
            # Log but don't fail on persistence errors
            pass

    async def _evict_entry(self) -> None:
        """Evict an entry based on eviction policy."""
        if not self._memory_cache:
            return

        key_to_evict: Optional[str] = None

        if self.eviction_policy == EvictionPolicy.LRU:
            # Remove least recently used
            key_to_evict = next(iter(self._memory_cache))

        elif self.eviction_policy == EvictionPolicy.LFU:
            # Remove least frequently used
            min_accesses = float("inf")
            for key in self._memory_cache:
                accesses = self._access_stats.get(key, 0)
                if accesses < min_accesses:
                    min_accesses = accesses
                    key_to_evict = key

        elif self.eviction_policy == EvictionPolicy.FIFO:
            # Remove first inserted (oldest created_at)
            oldest_time = datetime.now()
            for key, entry in self._memory_cache.items():
                if entry.created_at < oldest_time:
                    oldest_time = entry.created_at
                    key_to_evict = key

        elif self.eviction_policy == EvictionPolicy.TTL:
            # Remove entry closest to expiration
            min_ttl_remaining = float("inf")
            for key, entry in self._memory_cache.items():
                if entry.ttl:
                    remaining = entry.ttl - (datetime.now() - entry.created_at).total_seconds()
                    if remaining < min_ttl_remaining:
                        min_ttl_remaining = remaining
                        key_to_evict = key

        elif self.eviction_policy == EvictionPolicy.ADAPTIVE:
            # Combine LRU and LFU with weighting
            min_score = float("inf")
            now = datetime.now()
            for key, entry in self._memory_cache.items():
                age_hours = (now - entry.last_accessed).total_seconds() / 3600
                accesses = self._access_stats.get(key, 0)
                # Lower score = more likely to evict
                score = age_hours / (accesses + 1)
                if score < min_score:
                    min_score = score
                    key_to_evict = key

        if key_to_evict:
            del self._memory_cache[key_to_evict]
            self._access_stats.pop(key_to_evict, None)
            self._stats["evictions"] += 1

    def _update_access_stats(self, key: str) -> None:
        """Update access statistics for key."""
        self._access_stats[key] = self._access_stats.get(key, 0) + 1

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            **self._stats,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "memory_entries": len(self._memory_cache),
            "similarity_threshold": self.similarity_threshold,
            "eviction_policy": self.eviction_policy.name,
            "max_entries": self.max_entries,
        }

    async def get_cache_keys(self, pattern: str = "*") -> List[str]:
        """Get all cache keys matching pattern."""
        keys = []

        # In-memory keys
        for key in self._memory_cache:
            if pattern == "*" or pattern in key:
                keys.append(key)

        # Redis keys
        if self.enable_persistence and self.redis:
            try:
                cursor = 0
                while True:
                    cursor, batch = await self.redis.scan_keys(f"{self.key_prefix}:{pattern}", count=100, cursor=cursor)
                    keys.extend(batch)
                    if cursor == 0:
                        break
            except Exception:
                pass

        return list(set(keys))  # Remove duplicates


# Factory function
def create_semantic_cache(
    redis_url: Optional[str] = None, embedding_provider: str = "mock", similarity_threshold: float = 0.85, **kwargs
) -> SemanticCache:
    """
    Factory function to create a SemanticCache instance.

    Args:
        redis_url: Redis URL (if None, uses in-memory only)
        embedding_provider: "openai", "sentence-transformers", or "mock"
        similarity_threshold: Minimum similarity for cache hits
        **kwargs: Additional configuration options

    Returns:
        Configured SemanticCache instance
    """
    # Create Redis client if URL provided
    redis_client = None
    if redis_url:
        redis_client = RedisClient(redis_url)

    # Create embedding service
    embedding_service: EmbeddingService
    if embedding_provider == "openai" and OPENAI_AVAILABLE:
        embedding_service = OpenAIEmbeddingService()
    elif embedding_provider == "sentence-transformers" and SENTENCE_TRANSFORMERS_AVAILABLE:
        embedding_service = SentenceTransformerEmbeddingService()
    else:
        embedding_service = MockEmbeddingService()

    return SemanticCache(
        redis_client=redis_client,
        embedding_service=embedding_service,
        similarity_threshold=similarity_threshold,
        **kwargs,
    )
