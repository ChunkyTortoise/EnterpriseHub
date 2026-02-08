"""
Query Cache Module
==================

Query result cache with deduplication, incremental cache warming, and result deduplication.

Features:
    - Query result deduplication using content hashing
    - Incremental cache warming strategies
    - Query fingerprinting for duplicate detection
    - Background warming tasks
    - Result compression for large payloads

Example:
    >>> from src.caching import QueryCache, DeduplicationStrategy
    >>>
    >>> cache = QueryCache(
    ...     redis_client=redis,
    ...     dedup_strategy=DeduplicationStrategy.CONTENT_HASH,
    ...     enable_warming=True
    ... )
    >>>
    >>> # Cache query result
    >>> await cache.set_query_result(
    ...     query="SELECT * FROM users",
    ...     result=user_data,
    ...     ttl=300
    ... )
    >>>
    >>> # Get with automatic deduplication
    >>> result = await cache.get_query_result("SELECT * FROM users")

Classes:
    QueryCache: Main query cache implementation
    QueryResult: Data class for cached query results
    DeduplicationStrategy: Enum for deduplication methods
    CacheWarmingStrategy: Enum for warming strategies
"""

import asyncio
import hashlib
import json
import logging
import time
import zlib
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Set, Tuple, Union

from src.caching.redis_client import BaseRedisClient, RedisClient

logger = logging.getLogger(__name__)


class DeduplicationStrategy(Enum):
    """Strategies for query result deduplication."""

    NONE = auto()  # No deduplication
    EXACT_MATCH = auto()  # Exact string match
    CONTENT_HASH = auto()  # Hash of normalized content
    SEMANTIC = auto()  # Semantic similarity (requires embeddings)
    PARAMETERIZED = auto()  # Match parameterized queries


class CacheWarmingStrategy(Enum):
    """Strategies for cache warming."""

    NONE = auto()  # No automatic warming
    PREEMPTIVE = auto()  # Warm based on access patterns
    SCHEDULED = auto()  # Warm on schedule
    PREDICTIVE = auto()  # ML-based prediction of needed data
    INCREMENTAL = auto()  # Gradual warming based on popularity


@dataclass
class QueryFingerprint:
    """
    Fingerprint for query deduplication.

    Attributes:
        query_hash: Hash of normalized query
        parameter_hash: Hash of parameters
        content_hash: Hash of result content
        timestamp: When fingerprint was created
    """

    query_hash: str
    parameter_hash: str
    content_hash: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_key(self) -> str:
        """Generate unique key from fingerprint."""
        combined = f"{self.query_hash}:{self.parameter_hash}:{self.content_hash}"
        return hashlib.sha256(combined.encode()).hexdigest()[:32]


@dataclass
class QueryResult:
    """
    Represents a cached query result.

    Attributes:
        query: Original query string
        result: Cached result data
        fingerprint: Query fingerprint for deduplication
        created_at: Timestamp when cached
        expires_at: Expiration timestamp
        access_count: Number of times accessed
        last_accessed: Last access timestamp
        execution_time_ms: Original query execution time
        size_bytes: Size of result in bytes
        tags: Optional tags for organization
        metadata: Additional metadata
    """

    query: str
    result: Any
    fingerprint: Optional[QueryFingerprint] = None
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    execution_time_ms: float = 0.0
    size_bytes: int = 0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if result has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def touch(self) -> None:
        """Update access metadata."""
        self.last_accessed = datetime.now()
        self.access_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "query": self.query,
            "result": self.result,
            "fingerprint": asdict(self.fingerprint) if self.fingerprint else None,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat(),
            "execution_time_ms": self.execution_time_ms,
            "size_bytes": self.size_bytes,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QueryResult":
        """Create from dictionary."""
        fingerprint = None
        if data.get("fingerprint"):
            fp_data = data["fingerprint"]
            fingerprint = QueryFingerprint(
                query_hash=fp_data["query_hash"],
                parameter_hash=fp_data["parameter_hash"],
                content_hash=fp_data["content_hash"],
                timestamp=datetime.fromisoformat(fp_data["timestamp"]),
            )

        return cls(
            query=data["query"],
            result=data["result"],
            fingerprint=fingerprint,
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            execution_time_ms=data.get("execution_time_ms", 0.0),
            size_bytes=data.get("size_bytes", 0),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )


class QueryNormalizer:
    """Normalizes queries for consistent hashing and deduplication."""

    @staticmethod
    def normalize(query: str) -> str:
        """
        Normalize query string for consistent comparison.

        - Remove extra whitespace
        - Convert to lowercase
        - Remove comments
        - Standardize parameter placeholders
        """
        # Remove SQL comments
        lines = []
        for line in query.split("\n"):
            # Remove single-line comments
            if "--" in line:
                line = line[: line.index("--")]
            lines.append(line)

        query = " ".join(lines)

        # Remove multi-line comments
        while "/*" in query and "*/" in query:
            start = query.index("/*")
            end = query.index("*/", start) + 2
            query = query[:start] + " " + query[end:]

        # Normalize whitespace
        query = " ".join(query.split())

        # Convert to lowercase
        query = query.lower().strip()

        # Standardize parameter placeholders
        import re

        # Replace various parameter styles with standard ?
        query = re.sub(r"%\([^)]+\)s", "?", query)  # Python style
        query = re.sub(r":\w+", "?", query)  # Named params
        query = re.sub(r"\$\d+", "?", query)  # PostgreSQL style

        return query

    @staticmethod
    def extract_parameters(query: str) -> List[str]:
        """Extract parameter names from query."""
        import re

        params = []

        # Python style
        params.extend(re.findall(r"%\(([^)]+)\)s", query))
        # Named params
        params.extend(re.findall(r":(\w+)", query))
        # PostgreSQL style
        params.extend(re.findall(r"\$(\d+)", query))

        return params


class ContentHasher:
    """Hashes content for deduplication."""

    @staticmethod
    def hash_query(query: str) -> str:
        """Generate hash for normalized query."""
        normalized = QueryNormalizer.normalize(query)
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    @staticmethod
    def hash_parameters(params: Dict[str, Any]) -> str:
        """Generate hash for parameters."""
        # Sort keys for consistent hashing
        param_str = json.dumps(params, sort_keys=True, default=str)
        return hashlib.sha256(param_str.encode()).hexdigest()[:16]

    @staticmethod
    def hash_content(content: Any) -> str:
        """Generate hash for result content."""
        content_str = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]

    @staticmethod
    def generate_fingerprint(
        query: str, parameters: Optional[Dict[str, Any]] = None, content: Any = None
    ) -> QueryFingerprint:
        """Generate complete fingerprint for query."""
        return QueryFingerprint(
            query_hash=ContentHasher.hash_query(query),
            parameter_hash=ContentHasher.hash_parameters(parameters or {}),
            content_hash=ContentHasher.hash_content(content) if content is not None else "",
        )


class CompressionHandler:
    """Handles compression for large results."""

    COMPRESSION_THRESHOLD = 1024  # Compress results > 1KB

    @staticmethod
    def compress(data: bytes) -> Tuple[bytes, bool]:
        """
        Compress data if beneficial.

        Returns:
            Tuple of (data, was_compressed)
        """
        if len(data) < CompressionHandler.COMPRESSION_THRESHOLD:
            return data, False

        compressed = zlib.compress(data, level=6)

        # Only use compression if it actually reduces size
        if len(compressed) < len(data):
            return compressed, True
        return data, False

    @staticmethod
    def decompress(data: bytes, was_compressed: bool) -> bytes:
        """Decompress data if needed."""
        if was_compressed:
            return zlib.decompress(data)
        return data


class WarmingTask:
    """Represents a cache warming task."""

    def __init__(
        self, query: str, compute_fn: Callable[[], Any], priority: int = 0, interval_seconds: Optional[int] = None
    ):
        self.query = query
        self.compute_fn = compute_fn
        self.priority = priority
        self.interval_seconds = interval_seconds
        self.last_run: Optional[datetime] = None
        self.run_count = 0
        self.error_count = 0

    async def execute(self) -> Optional[Any]:
        """Execute the warming task."""
        try:
            if asyncio.iscoroutinefunction(self.compute_fn):
                result = await self.compute_fn()
            else:
                result = self.compute_fn()

            self.last_run = datetime.now()
            self.run_count += 1
            return result
        except Exception as e:
            self.error_count += 1
            logger.error(f"Warming task failed for query '{self.query}': {e}")
            return None

    def should_run(self) -> bool:
        """Check if task should run based on interval."""
        if self.interval_seconds is None:
            return True
        if self.last_run is None:
            return True
        elapsed = (datetime.now() - self.last_run).total_seconds()
        return elapsed >= self.interval_seconds


class QueryCache:
    """
    Query result cache with deduplication and warming support.

    Features:
        - Multiple deduplication strategies
        - Incremental cache warming
        - Result compression
        - Query fingerprinting
        - Background warming tasks

    Args:
        redis_client: Redis client for persistence
        dedup_strategy: Deduplication strategy to use
        warming_strategy: Cache warming strategy
        enable_compression: Whether to compress large results
        default_ttl: Default time-to-live in seconds
        max_warming_tasks: Maximum concurrent warming tasks
        key_prefix: Prefix for cache keys
    """

    def __init__(
        self,
        redis_client: Optional[BaseRedisClient] = None,
        dedup_strategy: DeduplicationStrategy = DeduplicationStrategy.CONTENT_HASH,
        warming_strategy: CacheWarmingStrategy = CacheWarmingStrategy.INCREMENTAL,
        enable_compression: bool = True,
        default_ttl: int = 300,
        max_warming_tasks: int = 10,
        key_prefix: str = "query_cache",
    ):
        self.redis = redis_client
        self.dedup_strategy = dedup_strategy
        self.warming_strategy = warming_strategy
        self.enable_compression = enable_compression
        self.default_ttl = default_ttl
        self.max_warming_tasks = max_warming_tasks
        self.key_prefix = key_prefix

        # In-memory cache
        self._memory_cache: Dict[str, QueryResult] = {}

        # Fingerprint index for deduplication
        self._fingerprint_index: Dict[str, str] = {}  # fingerprint -> cache_key

        # Warming tasks
        self._warming_tasks: Dict[str, WarmingTask] = {}
        self._warming_queue: deque = deque()
        self._warming_active = False
        self._warming_task: Optional[asyncio.Task] = None

        # Statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "deduplicated": 0,
            "compressed": 0,
            "warming_executed": 0,
        }

        # Lock for thread safety
        self._lock = asyncio.Lock()

        # Start warming if enabled
        if warming_strategy != CacheWarmingStrategy.NONE:
            self._start_warming()

    async def get(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[Tuple[Any, Dict[str, Any]]]:
        """
        Get cached query result.

        Returns:
            Tuple of (result, metadata) or None if not found
        """
        cache_key = self._generate_cache_key(query, parameters)

        async with self._lock:
            # Check memory first
            if cache_key in self._memory_cache:
                result = self._memory_cache[cache_key]
                if not result.is_expired():
                    result.touch()
                    self._stats["hits"] += 1
                    return result.result, self._get_metadata(result)
                else:
                    del self._memory_cache[cache_key]

            # Check Redis
            if self.redis:
                try:
                    data = await self.redis.get(cache_key)
                    if data:
                        result = QueryResult.from_dict(data)
                        if not result.is_expired():
                            # Promote to memory
                            self._memory_cache[cache_key] = result
                            result.touch()
                            self._stats["hits"] += 1
                            return result.result, self._get_metadata(result)
                except Exception as e:
                    logger.error(f"Error retrieving from Redis: {e}")

            self._stats["misses"] += 1
            return None

    async def set(
        self,
        query: str,
        result: Any,
        parameters: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None,
        execution_time_ms: float = 0.0,
        skip_dedup: bool = False,
    ) -> str:
        """
        Cache query result.

        Returns:
            Cache key
        """
        # Check for duplicates if deduplication is enabled
        if not skip_dedup and self.dedup_strategy != DeduplicationStrategy.NONE:
            existing_key = await self._check_deduplication(query, parameters, result)
            if existing_key:
                self._stats["deduplicated"] += 1
                return existing_key

        # Generate fingerprint
        fingerprint = ContentHasher.generate_fingerprint(query, parameters, result)

        # Calculate size
        result_bytes = json.dumps(result, default=str).encode()
        size_bytes = len(result_bytes)

        # Compress if enabled and beneficial
        compressed = False
        if self.enable_compression and size_bytes > CompressionHandler.COMPRESSION_THRESHOLD:
            result_bytes, compressed = CompressionHandler.compress(result_bytes)
            if compressed:
                self._stats["compressed"] += 1
                result = {"_compressed": True, "_data": result_bytes.hex()}
                size_bytes = len(result_bytes)

        # Create cache entry
        cache_key = self._generate_cache_key(query, parameters)
        ttl_seconds = ttl or self.default_ttl

        query_result = QueryResult(
            query=query,
            result=result,
            fingerprint=fingerprint,
            expires_at=datetime.now() + timedelta(seconds=ttl_seconds),
            execution_time_ms=execution_time_ms,
            size_bytes=size_bytes,
            tags=tags or [],
            metadata={
                "compressed": compressed,
                "dedup_strategy": self.dedup_strategy.name,
            },
        )

        async with self._lock:
            # Store in memory
            self._memory_cache[cache_key] = query_result

            # Index fingerprint
            self._fingerprint_index[fingerprint.to_key()] = cache_key

            # Persist to Redis
            if self.redis:
                try:
                    await self.redis.set(cache_key, query_result.to_dict(), ttl=ttl_seconds)
                except Exception as e:
                    logger.error(f"Error persisting to Redis: {e}")

        return cache_key

    async def get_or_set(
        self,
        query: str,
        compute_fn: Callable[[], Any],
        parameters: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None,
    ) -> Tuple[Any, bool, Dict[str, Any]]:
        """
        Get cached result or compute and cache.

        Returns:
            Tuple of (result, was_cached, metadata)
        """
        # Try to get from cache
        cached = await self.get(query, parameters)
        if cached:
            result, metadata = cached
            return result, True, metadata

        # Compute result
        start_time = time.time()
        if asyncio.iscoroutinefunction(compute_fn):
            result = await compute_fn()
        else:
            result = compute_fn()
        execution_time_ms = (time.time() - start_time) * 1000

        # Cache result
        await self.set(
            query=query, result=result, parameters=parameters, ttl=ttl, tags=tags, execution_time_ms=execution_time_ms
        )

        metadata = {
            "execution_time_ms": execution_time_ms,
            "cached": False,
        }

        return result, False, metadata

    async def invalidate(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> bool:
        """Invalidate cached query result."""
        cache_key = self._generate_cache_key(query, parameters)

        async with self._lock:
            # Remove from memory
            if cache_key in self._memory_cache:
                result = self._memory_cache.pop(cache_key)
                if result.fingerprint:
                    self._fingerprint_index.pop(result.fingerprint.to_key(), None)

            # Remove from Redis
            if self.redis:
                try:
                    await self.redis.delete(cache_key)
                except Exception as e:
                    logger.error(f"Error deleting from Redis: {e}")
                    return False

        return True

    async def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate all results with given tag."""
        removed = 0

        async with self._lock:
            # Remove from memory
            keys_to_remove = [key for key, result in self._memory_cache.items() if tag in result.tags]
            for key in keys_to_remove:
                result = self._memory_cache.pop(key)
                if result.fingerprint:
                    self._fingerprint_index.pop(result.fingerprint.to_key(), None)
                removed += 1

            # Remove from Redis
            if self.redis:
                try:
                    cursor = 0
                    while True:
                        cursor, keys = await self.redis.scan_keys(f"{self.key_prefix}:*", count=100, cursor=cursor)
                        for key in keys:
                            data = await self.redis.get(key)
                            if data:
                                result = QueryResult.from_dict(data)
                                if tag in result.tags:
                                    await self.redis.delete(key)
                                    removed += 1
                        if cursor == 0:
                            break
                except Exception as e:
                    logger.error(f"Error invalidating by tag: {e}")

        return removed

    async def clear(self) -> None:
        """Clear all cached results."""
        async with self._lock:
            self._memory_cache.clear()
            self._fingerprint_index.clear()

            if self.redis:
                try:
                    await self.redis.delete_pattern(f"{self.key_prefix}:*")
                except Exception as e:
                    logger.error(f"Error clearing Redis: {e}")

    def register_warming_task(
        self, query: str, compute_fn: Callable[[], Any], priority: int = 0, interval_seconds: Optional[int] = None
    ) -> None:
        """
        Register a cache warming task.

        Args:
            query: Query to warm
            compute_fn: Function to compute result
            priority: Higher priority = warmed first
            interval_seconds: How often to re-warm (None = once)
        """
        task = WarmingTask(query, compute_fn, priority, interval_seconds)
        self._warming_tasks[query] = task

        # Add to queue sorted by priority
        self._warming_queue.append(task)
        self._warming_queue = deque(sorted(self._warming_queue, key=lambda t: t.priority, reverse=True))

    def unregister_warming_task(self, query: str) -> bool:
        """Unregister a warming task."""
        if query in self._warming_tasks:
            task = self._warming_tasks.pop(query)
            if task in self._warming_queue:
                self._warming_queue.remove(task)
            return True
        return False

    async def warm_cache(self, query: Optional[str] = None) -> int:
        """
        Execute cache warming.

        Args:
            query: Specific query to warm (None = warm all registered)

        Returns:
            Number of tasks executed
        """
        executed = 0

        if query:
            if query in self._warming_tasks:
                task = self._warming_tasks[query]
                result = await task.execute()
                if result is not None:
                    await self.set(query, result)
                    executed += 1
        else:
            # Warm all registered tasks
            tasks_to_run = list(self._warming_queue)
            for task in tasks_to_run:
                if task.should_run():
                    result = await task.execute()
                    if result is not None:
                        await self.set(task.query, result)
                        executed += 1
                        self._stats["warming_executed"] += 1

        return executed

    def _start_warming(self) -> None:
        """Start background warming task."""
        if self._warming_active:
            return

        self._warming_active = True
        self._warming_task = asyncio.create_task(self._warming_loop())

    def stop_warming(self) -> None:
        """Stop background warming."""
        self._warming_active = False
        if self._warming_task:
            self._warming_task.cancel()

    async def _warming_loop(self) -> None:
        """Background warming loop."""
        while self._warming_active:
            try:
                if self.warming_strategy == CacheWarmingStrategy.SCHEDULED:
                    # Run every minute
                    await self.warm_cache()
                    await asyncio.sleep(60)

                elif self.warming_strategy == CacheWarmingStrategy.INCREMENTAL:
                    # Run tasks gradually
                    for task in list(self._warming_queue):
                        if task.should_run():
                            result = await task.execute()
                            if result is not None:
                                await self.set(task.query, result)
                                self._stats["warming_executed"] += 1
                            await asyncio.sleep(1)  # Throttle
                    await asyncio.sleep(10)

                elif self.warming_strategy == CacheWarmingStrategy.PREEMPTIVE:
                    # Warm based on access patterns
                    await self._preemptive_warming()
                    await asyncio.sleep(30)

                else:
                    await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in warming loop: {e}")
                await asyncio.sleep(60)

    async def _preemptive_warming(self) -> None:
        """Preemptively warm frequently accessed queries."""
        # Find frequently accessed queries
        frequent_queries = [(key, result) for key, result in self._memory_cache.items() if result.access_count > 5]

        # Sort by access count
        frequent_queries.sort(key=lambda x: x[1].access_count, reverse=True)

        # Warm top queries
        for cache_key, result in frequent_queries[: self.max_warming_tasks]:
            if result.query in self._warming_tasks:
                task = self._warming_tasks[result.query]
                if task.should_run():
                    new_result = await task.execute()
                    if new_result is not None:
                        await self.set(result.query, new_result)

    async def _check_deduplication(
        self, query: str, parameters: Optional[Dict[str, Any]], result: Any
    ) -> Optional[str]:
        """Check if this query/result is a duplicate."""
        if self.dedup_strategy == DeduplicationStrategy.EXACT_MATCH:
            cache_key = self._generate_cache_key(query, parameters)
            if cache_key in self._memory_cache:
                return cache_key

        elif self.dedup_strategy == DeduplicationStrategy.CONTENT_HASH:
            fingerprint = ContentHasher.generate_fingerprint(query, parameters, result)
            fp_key = fingerprint.to_key()
            if fp_key in self._fingerprint_index:
                return self._fingerprint_index[fp_key]

        elif self.dedup_strategy == DeduplicationStrategy.PARAMETERIZED:
            # Match queries with same structure but different params
            query_hash = ContentHasher.hash_query(query)
            for key, cached_result in self._memory_cache.items():
                if cached_result.fingerprint and cached_result.fingerprint.query_hash == query_hash:
                    return key

        return None

    def _generate_cache_key(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Generate cache key for query."""
        query_hash = ContentHasher.hash_query(query)
        param_hash = ContentHasher.hash_parameters(parameters or {})
        return f"{self.key_prefix}:{query_hash}:{param_hash}"

    def _get_metadata(self, result: QueryResult) -> Dict[str, Any]:
        """Get metadata for a cached result."""
        return {
            "cached": True,
            "created_at": result.created_at.isoformat(),
            "access_count": result.access_count,
            "execution_time_ms": result.execution_time_ms,
            "size_bytes": result.size_bytes,
            "tags": result.tags,
            **result.metadata,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            **self._stats,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "memory_entries": len(self._memory_cache),
            "warming_tasks": len(self._warming_tasks),
            "dedup_strategy": self.dedup_strategy.name,
            "warming_strategy": self.warming_strategy.name,
        }

    async def get_popular_queries(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most frequently accessed queries."""
        sorted_queries = sorted(
            [(r.query, r.access_count) for r in self._memory_cache.values()], key=lambda x: x[1], reverse=True
        )
        return sorted_queries[:limit]


# Factory function
async def create_query_cache(redis_url: Optional[str] = None, **kwargs) -> QueryCache:
    """
    Factory function to create a QueryCache instance.

    Args:
        redis_url: Redis URL (if None, uses in-memory only)
        **kwargs: Additional configuration options

    Returns:
        Configured QueryCache instance
    """
    redis_client = None
    if redis_url:
        redis_client = RedisClient(redis_url)
        await redis_client.connect()

    return QueryCache(redis_client=redis_client, **kwargs)
