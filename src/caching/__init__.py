"""
Semantic Caching Layer
======================

Intelligent caching system to reduce latency and API costs through:
- Embedding-based semantic similarity matching
- Query result deduplication and caching
- Redis integration with distributed cache support
- Comprehensive analytics and monitoring

Modules:
    redis_client: Redis client wrapper with connection pooling
    semantic_cache: Embedding-based cache with similarity matching
    query_cache: Query result cache with deduplication
    analytics: Cache hit/miss analytics and monitoring

Example:
    >>> from src.caching import SemanticCache, QueryCache, RedisClient
    >>>
    >>> # Initialize Redis client
    >>> redis = RedisClient("redis://localhost:6379")
    >>>
    >>> # Create semantic cache
    >>> cache = SemanticCache(redis_client=redis, similarity_threshold=0.85)
    >>>
    >>> # Cache query results
    >>> result = await cache.get_or_set(
    ...     query="What is the market trend?",
    ...     compute_fn=expensive_api_call
    ... )
"""

from src.caching.analytics import (
    CacheAnalytics,
    CacheMetrics,
    HitMissRatio,
    PerformanceReport,
)
from src.caching.query_cache import (
    CacheWarmingStrategy,
    DeduplicationStrategy,
    QueryCache,
    QueryResult,
)
from src.caching.redis_client import RedisClient, RedisClusterClient
from src.caching.semantic_cache import (
    CacheEntry,
    EmbeddingService,
    EvictionPolicy,
    MockEmbeddingService,
    OpenAIEmbeddingService,
    SemanticCache,
    SentenceTransformerEmbeddingService,
)

__version__ = "1.0.0"
__all__ = [
    # Redis Client
    "RedisClient",
    "RedisClusterClient",
    # Semantic Cache
    "SemanticCache",
    "EmbeddingService",
    "OpenAIEmbeddingService",
    "SentenceTransformerEmbeddingService",
    "MockEmbeddingService",
    "CacheEntry",
    "EvictionPolicy",
    # Query Cache
    "QueryCache",
    "QueryResult",
    "DeduplicationStrategy",
    "CacheWarmingStrategy",
    # Analytics
    "CacheAnalytics",
    "CacheMetrics",
    "HitMissRatio",
    "PerformanceReport",
]
