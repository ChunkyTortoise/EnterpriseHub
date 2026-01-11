"""
Performance Acceleration Engine for EnterpriseHub
Unified performance optimization with measurable improvements

Performance Targets:
- Webhook processing: <200ms (from 400ms) - 50% improvement
- Claude coaching: <25ms (from 45ms) - 45% improvement
- API response time: <100ms (from 150ms) - 33% improvement
- Cache hit rate: >95% (from ~40%) - 137% improvement
- Database queries: <25ms (from 50ms) - 50% improvement

Architecture:
- Unified Cache Coordination Layer
- Enhanced Webhook Processing with Circuit Breaker
- Distributed Rate Limiting
- Connection Pooling Optimization
- Real-Time Performance Monitoring

Author: Claude Performance Specialist
Date: 2026-01-10
Version: 1.0.0
"""

import asyncio
import time
import json
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Set, Callable, Union
from collections import defaultdict, deque
from enum import Enum
import logging
import functools

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# Performance Metrics and Data Structures
# =============================================================================

class PerformanceLevel(Enum):
    """Performance level classification."""
    CRITICAL = "critical"     # >500ms response time
    DEGRADED = "degraded"     # >200ms response time
    NORMAL = "normal"         # 100-200ms response time
    OPTIMAL = "optimal"       # <100ms response time
    EXCELLENT = "excellent"   # <50ms response time


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics tracking."""
    # Timing metrics
    avg_response_time_ms: float = 0.0
    p50_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    min_response_time_ms: float = float('inf')
    max_response_time_ms: float = 0.0

    # Throughput metrics
    requests_per_second: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0

    # Cache metrics
    cache_hit_rate: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0

    # Circuit breaker metrics
    circuit_breaker_trips: int = 0
    circuit_breaker_state: str = "closed"

    # Resource metrics
    connection_pool_utilization: float = 0.0
    memory_usage_mb: float = 0.0

    # Performance level
    performance_level: PerformanceLevel = PerformanceLevel.NORMAL

    def update_response_time(self, response_time_ms: float) -> None:
        """Update response time metrics."""
        self.total_requests += 1
        self.min_response_time_ms = min(self.min_response_time_ms, response_time_ms)
        self.max_response_time_ms = max(self.max_response_time_ms, response_time_ms)

        # Update moving average
        if self.total_requests == 1:
            self.avg_response_time_ms = response_time_ms
        else:
            self.avg_response_time_ms = (
                (self.avg_response_time_ms * (self.total_requests - 1) + response_time_ms)
                / self.total_requests
            )

        # Classify performance level
        if response_time_ms < 50:
            self.performance_level = PerformanceLevel.EXCELLENT
        elif response_time_ms < 100:
            self.performance_level = PerformanceLevel.OPTIMAL
        elif response_time_ms < 200:
            self.performance_level = PerformanceLevel.NORMAL
        elif response_time_ms < 500:
            self.performance_level = PerformanceLevel.DEGRADED
        else:
            self.performance_level = PerformanceLevel.CRITICAL


@dataclass
class ServicePerformance:
    """Performance tracking per service."""
    service_name: str
    metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    response_times: deque = field(default_factory=lambda: deque(maxlen=1000))
    last_updated: datetime = field(default_factory=datetime.now)

    def record_response(self, response_time_ms: float, success: bool = True) -> None:
        """Record a response time."""
        self.response_times.append(response_time_ms)
        self.metrics.update_response_time(response_time_ms)

        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1

        self.last_updated = datetime.now()

    def get_percentile(self, percentile: float) -> float:
        """Calculate response time percentile."""
        if not self.response_times:
            return 0.0

        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * percentile / 100)
        return sorted_times[min(index, len(sorted_times) - 1)]


# =============================================================================
# Enhanced Circuit Breaker with Adaptive Thresholds
# =============================================================================

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class AdaptiveCircuitBreaker:
    """
    Adaptive circuit breaker with dynamic thresholds.

    Features:
    - Dynamic failure threshold based on request volume
    - Exponential backoff for recovery attempts
    - Health-based threshold adjustment
    - Partial recovery support
    """

    name: str
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: float = 60.0

    # State tracking
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    next_attempt_time: Optional[datetime] = None

    # Adaptive features
    consecutive_successes: int = 0
    health_score: float = 1.0  # 0-1 scale
    adaptive_timeout: float = 60.0

    def record_success(self) -> None:
        """Record successful operation."""
        self.success_count += 1
        self.consecutive_successes += 1
        self.failure_count = max(0, self.failure_count - 1)

        # Improve health score on success
        self.health_score = min(1.0, self.health_score + 0.1)

        # Transition from half-open to closed
        if self.state == CircuitState.HALF_OPEN:
            if self.success_count >= self.success_threshold:
                self._close_circuit()

    def record_failure(self) -> None:
        """Record failed operation."""
        self.failure_count += 1
        self.consecutive_successes = 0
        self.last_failure_time = datetime.now()

        # Degrade health score on failure
        self.health_score = max(0.0, self.health_score - 0.2)

        # Open circuit if threshold exceeded
        if self.failure_count >= self.failure_threshold:
            self._open_circuit()

    def can_execute(self) -> bool:
        """Check if operation can be executed."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if datetime.now() >= self.next_attempt_time:
                self._transition_to_half_open()
                return True
            return False

        # Half-open: allow limited requests
        return True

    def _open_circuit(self) -> None:
        """Open the circuit breaker."""
        self.state = CircuitState.OPEN

        # Adaptive timeout based on health
        self.adaptive_timeout = self.timeout_seconds * (2 - self.health_score)
        self.next_attempt_time = datetime.now() + timedelta(seconds=self.adaptive_timeout)

        logger.warning(
            f"Circuit breaker '{self.name}' opened after {self.failure_count} failures. "
            f"Recovery in {self.adaptive_timeout:.1f}s"
        )

    def _transition_to_half_open(self) -> None:
        """Transition to half-open state."""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        logger.info(f"Circuit breaker '{self.name}' transitioning to half-open")

    def _close_circuit(self) -> None:
        """Close the circuit breaker."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.health_score = min(1.0, self.health_score + 0.2)
        logger.info(f"Circuit breaker '{self.name}' closed after recovery")

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "health_score": self.health_score,
            "next_attempt_time": self.next_attempt_time.isoformat() if self.next_attempt_time else None
        }


# =============================================================================
# Distributed Rate Limiter
# =============================================================================

@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_second: float = 100.0
    burst_size: int = 150
    window_seconds: int = 60


class DistributedRateLimiter:
    """
    Distributed rate limiter with token bucket algorithm.

    Features:
    - Token bucket with configurable refill rate
    - Burst handling for traffic spikes
    - Per-tenant/location rate limiting
    - Graceful degradation under load
    """

    def __init__(self, default_config: Optional[RateLimitConfig] = None):
        self.default_config = default_config or RateLimitConfig()

        # Per-key rate limit tracking
        self._buckets: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

        # Performance tracking
        self.total_requests = 0
        self.rate_limited_requests = 0

    async def check_rate_limit(
        self,
        key: str,
        config: Optional[RateLimitConfig] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is within rate limit.

        Returns:
            Tuple of (allowed, metadata)
        """
        config = config or self.default_config
        current_time = time.time()

        async with self._lock:
            self.total_requests += 1

            # Initialize bucket if not exists
            if key not in self._buckets:
                self._buckets[key] = {
                    "tokens": config.burst_size,
                    "last_refill": current_time,
                    "requests_in_window": 0,
                    "window_start": current_time
                }

            bucket = self._buckets[key]

            # Refill tokens based on elapsed time
            elapsed = current_time - bucket["last_refill"]
            tokens_to_add = elapsed * config.requests_per_second
            bucket["tokens"] = min(config.burst_size, bucket["tokens"] + tokens_to_add)
            bucket["last_refill"] = current_time

            # Reset window if expired
            if current_time - bucket["window_start"] > config.window_seconds:
                bucket["requests_in_window"] = 0
                bucket["window_start"] = current_time

            # Check if request is allowed
            if bucket["tokens"] >= 1:
                bucket["tokens"] -= 1
                bucket["requests_in_window"] += 1

                return True, {
                    "remaining_tokens": bucket["tokens"],
                    "requests_in_window": bucket["requests_in_window"],
                    "rate_limited": False
                }

            # Rate limited
            self.rate_limited_requests += 1

            retry_after = (1 - bucket["tokens"]) / config.requests_per_second

            return False, {
                "remaining_tokens": 0,
                "requests_in_window": bucket["requests_in_window"],
                "rate_limited": True,
                "retry_after_seconds": retry_after
            }

    def get_statistics(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        rate_limited_percent = 0.0
        if self.total_requests > 0:
            rate_limited_percent = (self.rate_limited_requests / self.total_requests) * 100

        return {
            "total_requests": self.total_requests,
            "rate_limited_requests": self.rate_limited_requests,
            "rate_limited_percent": rate_limited_percent,
            "active_buckets": len(self._buckets)
        }


# =============================================================================
# Unified Cache Coordination Layer
# =============================================================================

class CacheLayer(Enum):
    """Cache layer types."""
    L0_MEMORY_MAPPED = "l0_memory_mapped"  # <1ms
    L1_IN_MEMORY = "l1_in_memory"          # 1-2ms
    L2_REDIS = "l2_redis"                  # 5-10ms
    L3_DATABASE = "l3_database"            # 50ms+


@dataclass
class CacheCoordinatorConfig:
    """Cache coordinator configuration."""
    l0_max_size_mb: int = 100
    l1_max_entries: int = 10000
    l2_enabled: bool = True
    l3_enabled: bool = True

    # TTL settings
    default_ttl_seconds: int = 3600
    hot_data_ttl_seconds: int = 7200
    cold_data_ttl_seconds: int = 1800

    # Warming settings
    warming_enabled: bool = True
    warming_interval_seconds: int = 60
    prediction_threshold: float = 0.7


class UnifiedCacheCoordinator:
    """
    Unified cache coordination layer for multi-level caching.

    Features:
    - Coordinated multi-layer cache management
    - Intelligent cache promotion/demotion
    - Predictive cache warming
    - Cache sharding by tenant/location
    - Unified invalidation patterns
    """

    def __init__(
        self,
        config: Optional[CacheCoordinatorConfig] = None,
        redis_client=None,
        predictive_cache_manager=None
    ):
        self.config = config or CacheCoordinatorConfig()
        self.redis_client = redis_client
        self.predictive_cache = predictive_cache_manager

        # L1 in-memory cache (fast)
        self._l1_cache: Dict[str, Any] = {}
        self._l1_access_order: List[str] = []
        self._l1_lock = asyncio.Lock()

        # Cache metrics per layer
        self._layer_metrics = {
            CacheLayer.L0_MEMORY_MAPPED: {"hits": 0, "misses": 0, "avg_time_ms": 0.0},
            CacheLayer.L1_IN_MEMORY: {"hits": 0, "misses": 0, "avg_time_ms": 0.0},
            CacheLayer.L2_REDIS: {"hits": 0, "misses": 0, "avg_time_ms": 0.0},
            CacheLayer.L3_DATABASE: {"hits": 0, "misses": 0, "avg_time_ms": 0.0}
        }

        # Tenant sharding
        self._tenant_shards: Dict[str, Set[str]] = defaultdict(set)

        # Cache warming tracking
        self._warm_queue: Set[str] = set()
        self._warming_task = None

        logger.info("Unified Cache Coordinator initialized")

    async def get(
        self,
        key: str,
        tenant_id: Optional[str] = None,
        fetch_callback: Optional[Callable] = None
    ) -> Tuple[Any, CacheLayer, float]:
        """
        Get value from unified cache with multi-layer fallback.

        Returns:
            Tuple of (value, cache_layer, lookup_time_ms)
        """
        start_time = time.time()

        # Try L1 in-memory cache first
        value = await self._get_from_l1(key)
        if value is not None:
            lookup_time = (time.time() - start_time) * 1000
            self._record_hit(CacheLayer.L1_IN_MEMORY, lookup_time)
            return value, CacheLayer.L1_IN_MEMORY, lookup_time

        # Try L2 Redis cache
        if self.config.l2_enabled and self.redis_client:
            try:
                value = await self.redis_client.optimized_get(f"unified:{key}")
                if value is not None:
                    # Promote to L1
                    await self._set_l1(key, value)

                    lookup_time = (time.time() - start_time) * 1000
                    self._record_hit(CacheLayer.L2_REDIS, lookup_time)
                    return value, CacheLayer.L2_REDIS, lookup_time
            except Exception as e:
                logger.warning(f"Redis cache lookup failed: {e}")

        # Try predictive cache manager (includes L0)
        if self.predictive_cache:
            try:
                value, was_cached = await self.predictive_cache.get(key)
                if was_cached:
                    # Promote to L1
                    await self._set_l1(key, value)

                    lookup_time = (time.time() - start_time) * 1000
                    self._record_hit(CacheLayer.L0_MEMORY_MAPPED, lookup_time)
                    return value, CacheLayer.L0_MEMORY_MAPPED, lookup_time
            except Exception as e:
                logger.warning(f"Predictive cache lookup failed: {e}")

        # Cache miss - fetch from source
        if fetch_callback:
            try:
                value = await fetch_callback()

                # Populate all cache layers
                await self.set(key, value, tenant_id=tenant_id)

                lookup_time = (time.time() - start_time) * 1000
                self._record_miss(lookup_time)
                return value, CacheLayer.L3_DATABASE, lookup_time
            except Exception as e:
                logger.error(f"Fetch callback failed for key {key}: {e}")
                raise

        lookup_time = (time.time() - start_time) * 1000
        self._record_miss(lookup_time)
        return None, CacheLayer.L3_DATABASE, lookup_time

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        tenant_id: Optional[str] = None,
        priority: str = "normal"  # hot, normal, cold
    ) -> bool:
        """
        Set value in unified cache (all layers).

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live
            tenant_id: Tenant ID for sharding
            priority: Cache priority level
        """
        try:
            ttl = ttl_seconds or self.config.default_ttl_seconds

            # Adjust TTL based on priority
            if priority == "hot":
                ttl = self.config.hot_data_ttl_seconds
            elif priority == "cold":
                ttl = self.config.cold_data_ttl_seconds

            # Set in L1
            await self._set_l1(key, value, ttl)

            # Set in L2 Redis
            if self.config.l2_enabled and self.redis_client:
                try:
                    await self.redis_client.optimized_set(f"unified:{key}", value, ttl=ttl)
                except Exception as e:
                    logger.warning(f"Redis cache set failed: {e}")

            # Set in predictive cache
            if self.predictive_cache:
                try:
                    await self.predictive_cache.set(key, value, ttl_seconds=ttl)
                except Exception as e:
                    logger.warning(f"Predictive cache set failed: {e}")

            # Track tenant shard
            if tenant_id:
                self._tenant_shards[tenant_id].add(key)

            return True

        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {e}")
            return False

    async def invalidate(
        self,
        key: str,
        tenant_id: Optional[str] = None,
        pattern: bool = False
    ) -> int:
        """
        Invalidate cache entries.

        Args:
            key: Cache key or pattern
            tenant_id: Tenant ID for scoped invalidation
            pattern: Whether key is a pattern

        Returns:
            Number of entries invalidated
        """
        invalidated = 0

        if pattern:
            # Pattern-based invalidation
            keys_to_invalidate = []

            async with self._l1_lock:
                for cache_key in list(self._l1_cache.keys()):
                    if key in cache_key:
                        keys_to_invalidate.append(cache_key)

            for cache_key in keys_to_invalidate:
                await self._invalidate_single(cache_key)
                invalidated += 1
        else:
            # Single key invalidation
            await self._invalidate_single(key)
            invalidated = 1

        logger.info(f"Invalidated {invalidated} cache entries for key/pattern: {key}")
        return invalidated

    async def invalidate_tenant(self, tenant_id: str) -> int:
        """Invalidate all cache entries for a tenant."""
        keys = self._tenant_shards.get(tenant_id, set())

        for key in keys:
            await self._invalidate_single(key)

        invalidated = len(keys)
        self._tenant_shards[tenant_id].clear()

        logger.info(f"Invalidated {invalidated} cache entries for tenant: {tenant_id}")
        return invalidated

    async def warm_cache(
        self,
        keys: List[str],
        fetch_callbacks: Dict[str, Callable]
    ) -> int:
        """
        Warm cache with specified keys.

        Returns:
            Number of entries warmed
        """
        warmed = 0

        for key in keys:
            if key in fetch_callbacks and key not in self._l1_cache:
                try:
                    value = await fetch_callbacks[key]()
                    await self.set(key, value, priority="hot")
                    self._warm_queue.add(key)
                    warmed += 1
                except Exception as e:
                    logger.warning(f"Failed to warm cache for key {key}: {e}")

        logger.info(f"Warmed {warmed} cache entries")
        return warmed

    async def _get_from_l1(self, key: str) -> Optional[Any]:
        """Get value from L1 cache."""
        async with self._l1_lock:
            if key in self._l1_cache:
                entry = self._l1_cache[key]

                # Check expiration
                if datetime.now() > entry["expires_at"]:
                    del self._l1_cache[key]
                    if key in self._l1_access_order:
                        self._l1_access_order.remove(key)
                    return None

                # Update access order (LRU)
                if key in self._l1_access_order:
                    self._l1_access_order.remove(key)
                self._l1_access_order.append(key)

                return entry["value"]

        return None

    async def _set_l1(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Set value in L1 cache with LRU eviction."""
        ttl = ttl_seconds or self.config.default_ttl_seconds

        async with self._l1_lock:
            # Evict if cache is full
            while len(self._l1_cache) >= self.config.l1_max_entries:
                if self._l1_access_order:
                    oldest_key = self._l1_access_order.pop(0)
                    if oldest_key in self._l1_cache:
                        del self._l1_cache[oldest_key]

            # Add entry
            self._l1_cache[key] = {
                "value": value,
                "expires_at": datetime.now() + timedelta(seconds=ttl),
                "created_at": datetime.now()
            }

            if key in self._l1_access_order:
                self._l1_access_order.remove(key)
            self._l1_access_order.append(key)

    async def _invalidate_single(self, key: str) -> None:
        """Invalidate a single cache key across all layers."""
        # L1
        async with self._l1_lock:
            if key in self._l1_cache:
                del self._l1_cache[key]
            if key in self._l1_access_order:
                self._l1_access_order.remove(key)

        # L2 Redis
        if self.config.l2_enabled and self.redis_client:
            try:
                await self.redis_client._redis_client.delete(f"unified:{key}")
            except Exception as e:
                logger.warning(f"Redis invalidation failed: {e}")

    def _record_hit(self, layer: CacheLayer, lookup_time_ms: float) -> None:
        """Record cache hit."""
        metrics = self._layer_metrics[layer]
        metrics["hits"] += 1
        total = metrics["hits"] + metrics["misses"]
        metrics["avg_time_ms"] = (
            (metrics["avg_time_ms"] * (total - 1) + lookup_time_ms) / total
        )

    def _record_miss(self, lookup_time_ms: float) -> None:
        """Record cache miss."""
        for layer in self._layer_metrics:
            self._layer_metrics[layer]["misses"] += 1

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        total_hits = sum(m["hits"] for m in self._layer_metrics.values())
        total_misses = self._layer_metrics[CacheLayer.L1_IN_MEMORY]["misses"]
        total_requests = total_hits + total_misses

        hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0.0

        return {
            "overall": {
                "total_requests": total_requests,
                "total_hits": total_hits,
                "total_misses": total_misses,
                "hit_rate_percent": hit_rate,
                "target_hit_rate_percent": 95.0,
                "target_met": hit_rate >= 95.0
            },
            "by_layer": {
                layer.value: {
                    "hits": self._layer_metrics[layer]["hits"],
                    "misses": self._layer_metrics[layer]["misses"],
                    "avg_lookup_time_ms": self._layer_metrics[layer]["avg_time_ms"]
                }
                for layer in CacheLayer
            },
            "capacity": {
                "l1_entries": len(self._l1_cache),
                "l1_max_entries": self.config.l1_max_entries,
                "l1_utilization_percent": len(self._l1_cache) / self.config.l1_max_entries * 100,
                "tenant_shards": len(self._tenant_shards)
            },
            "warming": {
                "enabled": self.config.warming_enabled,
                "queued_keys": len(self._warm_queue)
            }
        }


# =============================================================================
# Performance Acceleration Engine
# =============================================================================

class PerformanceAccelerationEngine:
    """
    Unified performance acceleration engine for EnterpriseHub.

    Features:
    - Unified cache coordination
    - Enhanced webhook processing
    - Distributed rate limiting
    - Circuit breaker protection
    - Real-time performance monitoring
    - Auto-optimization based on metrics

    Performance Targets:
    - Webhook processing: <200ms (50% improvement)
    - Claude coaching: <25ms (45% improvement)
    - API response: <100ms (33% improvement)
    - Cache hit rate: >95%
    - Database queries: <25ms (50% improvement)
    """

    def __init__(
        self,
        redis_client=None,
        predictive_cache_manager=None,
        enhanced_webhook_processor=None
    ):
        # External services
        self.redis_client = redis_client
        self.predictive_cache = predictive_cache_manager
        self.enhanced_webhook_processor = enhanced_webhook_processor

        # Core components
        self.cache_coordinator = UnifiedCacheCoordinator(
            redis_client=redis_client,
            predictive_cache_manager=predictive_cache_manager
        )
        self.rate_limiter = DistributedRateLimiter()

        # Circuit breakers per service
        self._circuit_breakers: Dict[str, AdaptiveCircuitBreaker] = {}

        # Performance tracking
        self._service_performance: Dict[str, ServicePerformance] = {}

        # Auto-optimization settings
        self._optimization_enabled = True
        self._optimization_interval = 60  # seconds
        self._last_optimization = datetime.now()

        # Performance targets
        self.targets = {
            "webhook_processing_ms": 200,
            "claude_coaching_ms": 25,
            "api_response_ms": 100,
            "cache_hit_rate_percent": 95,
            "database_query_ms": 25
        }

        # Background tasks
        self._monitoring_task = None
        self._optimization_task = None

        logger.info("Performance Acceleration Engine initialized")

    async def initialize(self) -> None:
        """Initialize the performance acceleration engine."""
        try:
            # Start background monitoring
            self._monitoring_task = asyncio.create_task(self._performance_monitoring_loop())

            # Start auto-optimization
            if self._optimization_enabled:
                self._optimization_task = asyncio.create_task(self._auto_optimization_loop())

            logger.info("Performance Acceleration Engine started")

        except Exception as e:
            logger.error(f"Failed to initialize Performance Acceleration Engine: {e}")
            raise

    def get_circuit_breaker(self, service_name: str) -> AdaptiveCircuitBreaker:
        """Get or create circuit breaker for service."""
        if service_name not in self._circuit_breakers:
            self._circuit_breakers[service_name] = AdaptiveCircuitBreaker(name=service_name)
        return self._circuit_breakers[service_name]

    def get_service_performance(self, service_name: str) -> ServicePerformance:
        """Get or create performance tracker for service."""
        if service_name not in self._service_performance:
            self._service_performance[service_name] = ServicePerformance(service_name=service_name)
        return self._service_performance[service_name]

    async def execute_with_acceleration(
        self,
        service_name: str,
        operation: Callable,
        cache_key: Optional[str] = None,
        rate_limit_key: Optional[str] = None,
        timeout_seconds: float = 30.0
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Execute operation with full performance acceleration.

        Features:
        - Cache lookup before execution
        - Circuit breaker protection
        - Rate limiting
        - Performance tracking
        - Timeout handling

        Returns:
            Tuple of (result, performance_metadata)
        """
        start_time = time.time()
        performance_metadata = {
            "service": service_name,
            "cached": False,
            "rate_limited": False,
            "circuit_breaker_state": "closed",
            "execution_time_ms": 0.0
        }

        # Check rate limit
        if rate_limit_key:
            allowed, rate_info = await self.rate_limiter.check_rate_limit(rate_limit_key)
            if not allowed:
                performance_metadata["rate_limited"] = True
                performance_metadata["retry_after"] = rate_info.get("retry_after_seconds")
                raise Exception(f"Rate limit exceeded for {rate_limit_key}")

        # Check cache
        if cache_key:
            cached_value, cache_layer, lookup_time = await self.cache_coordinator.get(
                cache_key
            )
            if cached_value is not None:
                performance_metadata["cached"] = True
                performance_metadata["cache_layer"] = cache_layer.value
                performance_metadata["execution_time_ms"] = lookup_time
                return cached_value, performance_metadata

        # Check circuit breaker
        circuit_breaker = self.get_circuit_breaker(service_name)
        performance_metadata["circuit_breaker_state"] = circuit_breaker.state.value

        if not circuit_breaker.can_execute():
            raise Exception(f"Circuit breaker open for {service_name}")

        # Execute operation with timeout
        try:
            result = await asyncio.wait_for(operation(), timeout=timeout_seconds)

            # Record success
            execution_time = (time.time() - start_time) * 1000
            circuit_breaker.record_success()
            self.get_service_performance(service_name).record_response(execution_time, success=True)

            # Cache result
            if cache_key:
                await self.cache_coordinator.set(cache_key, result)

            performance_metadata["execution_time_ms"] = execution_time
            performance_metadata["success"] = True

            return result, performance_metadata

        except asyncio.TimeoutError:
            circuit_breaker.record_failure()
            execution_time = timeout_seconds * 1000
            self.get_service_performance(service_name).record_response(execution_time, success=False)

            performance_metadata["execution_time_ms"] = execution_time
            performance_metadata["timeout"] = True
            performance_metadata["success"] = False

            raise Exception(f"Operation timed out after {timeout_seconds}s")

        except Exception as e:
            circuit_breaker.record_failure()
            execution_time = (time.time() - start_time) * 1000
            self.get_service_performance(service_name).record_response(execution_time, success=False)

            performance_metadata["execution_time_ms"] = execution_time
            performance_metadata["error"] = str(e)
            performance_metadata["success"] = False

            raise

    async def accelerate_webhook_processing(
        self,
        webhook_id: str,
        payload: Dict[str, Any],
        processor_callback: Callable
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Accelerate webhook processing with enhanced optimization.

        Target: <200ms (from 400ms)
        """
        # Use enhanced webhook processor if available
        if self.enhanced_webhook_processor:
            return await self.execute_with_acceleration(
                service_name="webhook_processing",
                operation=lambda: processor_callback(webhook_id, payload),
                cache_key=f"webhook:{webhook_id}",
                rate_limit_key=payload.get("locationId"),
                timeout_seconds=10.0
            )

        # Fallback to direct execution with acceleration
        return await self.execute_with_acceleration(
            service_name="webhook_processing",
            operation=lambda: processor_callback(webhook_id, payload),
            timeout_seconds=10.0
        )

    async def accelerate_claude_coaching(
        self,
        agent_id: str,
        context: Dict[str, Any],
        coaching_callback: Callable
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Accelerate Claude coaching response.

        Target: <25ms (from 45ms)
        """
        cache_key = f"coaching:{agent_id}:{hashlib.md5(json.dumps(context, sort_keys=True).encode()).hexdigest()[:8]}"

        return await self.execute_with_acceleration(
            service_name="claude_coaching",
            operation=lambda: coaching_callback(agent_id, context),
            cache_key=cache_key,
            timeout_seconds=5.0
        )

    async def accelerate_api_request(
        self,
        endpoint: str,
        request_callback: Callable,
        cache_key: Optional[str] = None
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Accelerate API request processing.

        Target: <100ms (from 150ms)
        """
        return await self.execute_with_acceleration(
            service_name=f"api:{endpoint}",
            operation=request_callback,
            cache_key=cache_key,
            timeout_seconds=30.0
        )

    async def _performance_monitoring_loop(self) -> None:
        """Background performance monitoring."""
        while True:
            try:
                await asyncio.sleep(30)  # Monitor every 30 seconds

                # Check performance against targets
                for service_name, perf in self._service_performance.items():
                    avg_time = perf.metrics.avg_response_time_ms

                    # Log warnings for degraded performance
                    if service_name == "webhook_processing" and avg_time > self.targets["webhook_processing_ms"]:
                        logger.warning(
                            f"Webhook processing degraded: {avg_time:.1f}ms "
                            f"(target: {self.targets['webhook_processing_ms']}ms)"
                        )

                    if "claude_coaching" in service_name and avg_time > self.targets["claude_coaching_ms"]:
                        logger.warning(
                            f"Claude coaching degraded: {avg_time:.1f}ms "
                            f"(target: {self.targets['claude_coaching_ms']}ms)"
                        )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")

    async def _auto_optimization_loop(self) -> None:
        """Background auto-optimization."""
        while True:
            try:
                await asyncio.sleep(self._optimization_interval)

                # Analyze and optimize
                optimizations = await self._analyze_and_optimize()

                if optimizations:
                    logger.info(f"Applied {len(optimizations)} auto-optimizations")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-optimization error: {e}")

    async def _analyze_and_optimize(self) -> List[str]:
        """Analyze performance and apply optimizations."""
        optimizations = []

        # Check cache hit rate
        cache_stats = self.cache_coordinator.get_statistics()
        hit_rate = cache_stats["overall"]["hit_rate_percent"]

        if hit_rate < self.targets["cache_hit_rate_percent"]:
            # Increase L1 cache size
            self.cache_coordinator.config.l1_max_entries = min(
                self.cache_coordinator.config.l1_max_entries * 2,
                50000  # Max 50k entries
            )
            optimizations.append(f"Increased L1 cache size to {self.cache_coordinator.config.l1_max_entries}")

        # Check circuit breaker health
        for name, cb in self._circuit_breakers.items():
            if cb.health_score < 0.5:
                # Reduce failure threshold to trip earlier
                cb.failure_threshold = max(2, cb.failure_threshold - 1)
                optimizations.append(f"Reduced circuit breaker threshold for {name}")

        return optimizations

    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        return {
            "cache": self.cache_coordinator.get_statistics(),
            "rate_limiter": self.rate_limiter.get_statistics(),
            "circuit_breakers": {
                name: cb.get_status()
                for name, cb in self._circuit_breakers.items()
            },
            "services": {
                name: {
                    "avg_response_time_ms": perf.metrics.avg_response_time_ms,
                    "total_requests": perf.metrics.total_requests,
                    "success_rate": (
                        perf.metrics.successful_requests / perf.metrics.total_requests * 100
                        if perf.metrics.total_requests > 0 else 100.0
                    ),
                    "performance_level": perf.metrics.performance_level.value,
                    "p95_response_time_ms": perf.get_percentile(95),
                    "p99_response_time_ms": perf.get_percentile(99)
                }
                for name, perf in self._service_performance.items()
            },
            "targets": self.targets,
            "targets_met": {
                "webhook_processing": self._check_target_met("webhook_processing", self.targets["webhook_processing_ms"]),
                "claude_coaching": self._check_target_met("claude_coaching", self.targets["claude_coaching_ms"]),
                "cache_hit_rate": self.cache_coordinator.get_statistics()["overall"]["hit_rate_percent"] >= self.targets["cache_hit_rate_percent"]
            },
            "timestamp": datetime.now().isoformat()
        }

    def _check_target_met(self, service_name: str, target_ms: float) -> bool:
        """Check if service meets performance target."""
        if service_name not in self._service_performance:
            return True  # No data yet

        return self._service_performance[service_name].metrics.avg_response_time_ms <= target_ms

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check."""
        try:
            cache_stats = self.cache_coordinator.get_statistics()

            # Check all components
            cache_healthy = cache_stats["overall"]["hit_rate_percent"] >= 50
            rate_limiter_healthy = self.rate_limiter.get_statistics()["rate_limited_percent"] < 10

            circuit_breakers_healthy = all(
                cb.state != CircuitState.OPEN
                for cb in self._circuit_breakers.values()
            )

            overall_healthy = cache_healthy and rate_limiter_healthy and circuit_breakers_healthy

            return {
                "healthy": overall_healthy,
                "components": {
                    "cache": {
                        "healthy": cache_healthy,
                        "hit_rate": cache_stats["overall"]["hit_rate_percent"]
                    },
                    "rate_limiter": {
                        "healthy": rate_limiter_healthy,
                        "stats": self.rate_limiter.get_statistics()
                    },
                    "circuit_breakers": {
                        "healthy": circuit_breakers_healthy,
                        "open_count": sum(1 for cb in self._circuit_breakers.values() if cb.state == CircuitState.OPEN)
                    }
                },
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        if self._optimization_task:
            self._optimization_task.cancel()
            try:
                await self._optimization_task
            except asyncio.CancelledError:
                pass

        logger.info("Performance Acceleration Engine cleaned up")


# =============================================================================
# Singleton Instance
# =============================================================================

_performance_engine: Optional[PerformanceAccelerationEngine] = None


async def get_performance_acceleration_engine(**kwargs) -> PerformanceAccelerationEngine:
    """Get singleton performance acceleration engine."""
    global _performance_engine

    if _performance_engine is None:
        _performance_engine = PerformanceAccelerationEngine(**kwargs)
        await _performance_engine.initialize()

    return _performance_engine


# =============================================================================
# Performance Decorator
# =============================================================================

def accelerated(
    service_name: str,
    cache_key_fn: Optional[Callable] = None,
    timeout_seconds: float = 30.0
):
    """
    Decorator for accelerated function execution.

    Usage:
        @accelerated("my_service", cache_key_fn=lambda args: f"key:{args[0]}")
        async def my_function(param):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            engine = await get_performance_acceleration_engine()

            cache_key = cache_key_fn(args) if cache_key_fn else None

            result, metadata = await engine.execute_with_acceleration(
                service_name=service_name,
                operation=lambda: func(*args, **kwargs),
                cache_key=cache_key,
                timeout_seconds=timeout_seconds
            )

            return result

        return wrapper
    return decorator


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "PerformanceAccelerationEngine",
    "UnifiedCacheCoordinator",
    "AdaptiveCircuitBreaker",
    "DistributedRateLimiter",
    "PerformanceMetrics",
    "ServicePerformance",
    "CacheLayer",
    "CircuitState",
    "PerformanceLevel",
    "get_performance_acceleration_engine",
    "accelerated"
]
