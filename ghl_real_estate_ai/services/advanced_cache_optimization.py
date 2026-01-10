"""
Advanced Cache Optimization Layer

Comprehensive caching strategy for maximum performance across all services.
Implements intelligent cache warming, predictive preloading, and adaptive TTL management.

Performance Targets:
- Cache hit rate: >95%
- Cache lookup time: <1ms (L1), <3ms (L2), <8ms (L3)
- Memory efficiency: 70% reduction in redundant data
- Predictive accuracy: >80% for preloading

Key Features:
1. Multi-layer hierarchical caching (L1/L2/L3)
2. Intelligent cache warming and predictive preloading
3. Adaptive TTL based on access patterns
4. Cache compression and deduplication
5. Real-time performance monitoring and optimization
"""

import asyncio
import json
import time
import pickle
import zlib
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
from collections import OrderedDict, defaultdict, deque
from enum import Enum
import hashlib
import numpy as np
from functools import wraps
import weakref
import gc

from ghl_real_estate_ai.services.integration_cache_manager import IntegrationCacheManager
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class CacheLayer(Enum):
    """Cache layer hierarchy"""
    L1_MEMORY = "l1_memory"        # Ultra-fast in-memory cache
    L2_REDIS = "l2_redis"          # Fast shared cache
    L3_DATABASE = "l3_database"    # Persistent cache with compression
    PREDICTIVE = "predictive"      # Predictive preloading cache


class AccessPattern(Enum):
    """Access pattern types for optimization"""
    HOT = "hot"           # Frequently accessed, keep in L1
    WARM = "warm"         # Regularly accessed, L2 optimal
    COLD = "cold"         # Rarely accessed, L3 or evict
    TEMPORAL = "temporal" # Time-based access pattern
    SEQUENTIAL = "sequential" # Sequential access pattern


@dataclass
class CacheEntry:
    """Advanced cache entry with intelligence"""
    key: str
    data: Any
    created_at: datetime
    expires_at: datetime
    layer: CacheLayer

    # Access tracking
    access_count: int = 0
    last_accessed: datetime = None
    access_pattern: AccessPattern = AccessPattern.WARM

    # Performance metrics
    hit_count: int = 0
    miss_count: int = 0
    avg_access_interval: float = 0.0
    compression_ratio: float = 1.0

    # Optimization flags
    preloaded: bool = False
    compressed: bool = False
    deduplicated: bool = False
    predicted_next_access: Optional[datetime] = None

    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.created_at

    @property
    def age_seconds(self) -> float:
        return (datetime.now() - self.created_at).total_seconds()

    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at

    @property
    def access_frequency(self) -> float:
        """Calculate access frequency per hour"""
        age_hours = max(self.age_seconds / 3600, 0.01)  # Minimum 0.01 hour
        return self.access_count / age_hours

    def update_access_pattern(self) -> None:
        """Update access pattern based on usage"""
        frequency = self.access_frequency

        if frequency > 10:  # More than 10 accesses per hour
            self.access_pattern = AccessPattern.HOT
        elif frequency > 1:  # More than 1 access per hour
            self.access_pattern = AccessPattern.WARM
        else:
            self.access_pattern = AccessPattern.COLD

    def predict_next_access(self) -> Optional[datetime]:
        """Predict next access time based on patterns"""
        if self.access_count < 2:
            return None

        # Simple linear prediction based on average interval
        if self.avg_access_interval > 0:
            next_access = self.last_accessed + timedelta(seconds=self.avg_access_interval)
            return next_access

        return None


@dataclass
class CacheOptimizationMetrics:
    """Comprehensive cache optimization metrics"""
    # Hit rates by layer
    l1_hit_rate: float = 0.0
    l2_hit_rate: float = 0.0
    l3_hit_rate: float = 0.0
    overall_hit_rate: float = 0.0

    # Performance metrics
    avg_lookup_time_ms: float = 0.0
    avg_l1_lookup_ms: float = 0.0
    avg_l2_lookup_ms: float = 0.0
    avg_l3_lookup_ms: float = 0.0

    # Optimization effectiveness
    compression_effectiveness: float = 0.0
    deduplication_savings_mb: float = 0.0
    predictive_accuracy: float = 0.0
    preload_success_rate: float = 0.0

    # Resource utilization
    memory_usage_mb: float = 0.0
    memory_efficiency: float = 0.0
    cache_evictions: int = 0

    # Business impact
    response_time_improvement_percent: float = 0.0
    throughput_improvement_percent: float = 0.0


class AdvancedCacheOptimizer:
    """
    Advanced cache optimization system with intelligent management.

    Features:
    - Multi-layer hierarchical caching
    - Predictive preloading based on access patterns
    - Adaptive TTL management
    - Intelligent cache warming
    - Compression and deduplication
    """

    def __init__(
        self,
        l1_max_size: int = 5000,
        l2_redis_client=None,
        l3_database_client=None,
        enable_compression: bool = True,
        enable_prediction: bool = True
    ):
        """Initialize advanced cache optimizer"""

        # Cache layers
        self.l1_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.l1_max_size = l1_max_size

        self.l2_redis_client = l2_redis_client
        self.l3_database_client = l3_database_client

        # Optimization features
        self.enable_compression = enable_compression
        self.enable_prediction = enable_prediction

        # Access pattern tracking
        self.access_patterns: Dict[str, List[datetime]] = defaultdict(list)
        self.pattern_analysis_window = 3600  # 1 hour

        # Predictive caching
        self.prediction_queue = asyncio.Queue(maxsize=1000)
        self.preload_cache: Dict[str, CacheEntry] = {}

        # Deduplication
        self.data_hashes: Dict[str, Set[str]] = defaultdict(set)  # hash -> keys
        self.key_hashes: Dict[str, str] = {}  # key -> hash

        # Performance tracking
        self.metrics = CacheOptimizationMetrics()
        self.performance_history = deque(maxlen=10000)

        # Background tasks
        self.optimization_tasks = []

        # Cache warming strategies
        self.warm_up_patterns = {
            'lead_data': self._warm_up_lead_patterns,
            'property_data': self._warm_up_property_patterns,
            'ml_predictions': self._warm_up_ml_predictions
        }

        logger.info(
            f"Advanced Cache Optimizer initialized: "
            f"L1 size={l1_max_size}, compression={enable_compression}, prediction={enable_prediction}"
        )

    async def initialize(self):
        """Initialize advanced cache optimization"""
        try:
            # Start background optimization workers
            self.optimization_tasks = [
                asyncio.create_task(self._cache_optimization_worker()),
                asyncio.create_task(self._predictive_preloader_worker()),
                asyncio.create_task(self._access_pattern_analyzer_worker()),
                asyncio.create_task(self._cache_warming_worker()),
                asyncio.create_task(self._memory_management_worker())
            ]

            # Initialize cache warming
            await self._initial_cache_warming()

            logger.info("Advanced cache optimization initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize cache optimizer: {e}")
            raise

    async def get(
        self,
        key: str,
        namespace: str = "default",
        fallback_func: Optional[Callable] = None,
        ttl: Optional[int] = None,
        enable_preload: bool = True
    ) -> Any:
        """
        Advanced cache get with multi-layer lookup and optimization.

        Optimization features:
        - Intelligent layer selection based on access patterns
        - Automatic preloading of related data
        - Adaptive TTL based on usage patterns
        - Compression and deduplication
        """
        full_key = self._build_key(namespace, key)
        start_time = time.time()

        try:
            # Track access pattern
            self._record_access_pattern(full_key)

            # Try L1 cache first (fastest)
            l1_start = time.time()
            l1_result = await self._get_from_l1(full_key)

            if l1_result is not None:
                self.metrics.l1_hit_rate = self._update_hit_rate(self.metrics.l1_hit_rate, True)
                self._update_access_metrics(full_key, (time.time() - l1_start) * 1000, CacheLayer.L1_MEMORY)

                # Trigger predictive preloading
                if enable_preload:
                    asyncio.create_task(self._trigger_predictive_preload(full_key, namespace))

                return l1_result

            # Try L2 cache (Redis)
            if self.l2_redis_client:
                l2_start = time.time()
                l2_result = await self._get_from_l2(full_key)

                if l2_result is not None:
                    self.metrics.l2_hit_rate = self._update_hit_rate(self.metrics.l2_hit_rate, True)
                    self._update_access_metrics(full_key, (time.time() - l2_start) * 1000, CacheLayer.L2_REDIS)

                    # Promote to L1 if frequently accessed
                    if self._should_promote_to_l1(full_key):
                        await self._set_l1(full_key, l2_result, ttl)

                    return l2_result

            # Try L3 cache (Database)
            if self.l3_database_client:
                l3_start = time.time()
                l3_result = await self._get_from_l3(full_key)

                if l3_result is not None:
                    self.metrics.l3_hit_rate = self._update_hit_rate(self.metrics.l3_hit_rate, True)
                    self._update_access_metrics(full_key, (time.time() - l3_start) * 1000, CacheLayer.L3_DATABASE)

                    # Promote to higher layers based on access pattern
                    if self._should_promote_to_l2(full_key):
                        await self._set_l2(full_key, l3_result, ttl)
                    if self._should_promote_to_l1(full_key):
                        await self._set_l1(full_key, l3_result, ttl)

                    return l3_result

            # Cache miss - execute fallback
            if fallback_func:
                miss_start = time.time()
                result = await self._execute_fallback(fallback_func)
                miss_time = (time.time() - miss_start) * 1000

                # Store in optimal cache layer based on data characteristics
                await self._intelligent_cache_storage(full_key, result, ttl, namespace)

                self._update_access_metrics(full_key, miss_time, None)
                return result

            return None

        except Exception as e:
            logger.error(f"Advanced cache get failed for {full_key}: {e}")
            if fallback_func:
                return await self._execute_fallback(fallback_func)
            return None

    async def set(
        self,
        key: str,
        value: Any,
        namespace: str = "default",
        ttl: Optional[int] = None,
        force_layer: Optional[CacheLayer] = None
    ) -> None:
        """
        Advanced cache set with intelligent layer selection.

        Features:
        - Automatic compression for large objects
        - Deduplication to save memory
        - Intelligent layer selection based on data characteristics
        - Adaptive TTL based on access patterns
        """
        full_key = self._build_key(namespace, key)

        try:
            # Apply compression if beneficial
            compressed_value, compression_ratio = await self._apply_compression(value)

            # Check for deduplication opportunities
            deduplicated_key = await self._check_deduplication(full_key, compressed_value)

            # Determine optimal cache layer
            if force_layer:
                target_layer = force_layer
            else:
                target_layer = self._determine_optimal_layer(
                    full_key, compressed_value, compression_ratio
                )

            # Calculate adaptive TTL
            adaptive_ttl = self._calculate_adaptive_ttl(full_key, ttl)

            # Store in target layer
            await self._store_in_layer(
                full_key, compressed_value, adaptive_ttl, target_layer,
                compression_ratio, deduplicated_key
            )

        except Exception as e:
            logger.error(f"Advanced cache set failed for {full_key}: {e}")

    async def _get_from_l1(self, key: str) -> Any:
        """Get from L1 cache with access pattern tracking"""
        if key in self.l1_cache:
            entry = self.l1_cache[key]

            if entry.is_expired:
                del self.l1_cache[key]
                return None

            # Update access tracking
            entry.access_count += 1
            entry.last_accessed = datetime.now()
            entry.hit_count += 1
            entry.update_access_pattern()

            # Move to end (LRU)
            self.l1_cache.move_to_end(key)

            # Decompress if needed
            if entry.compressed:
                return self._decompress_data(entry.data)
            else:
                return entry.data

        return None

    async def _get_from_l2(self, key: str) -> Any:
        """Get from L2 cache (Redis) with optimization"""
        if not self.l2_redis_client:
            return None

        try:
            cached_data = await self.l2_redis_client.hget("cache_l2", key)
            if cached_data:
                # Deserialize and decompress
                entry_data = pickle.loads(cached_data)

                if entry_data.get('compressed', False):
                    return self._decompress_data(entry_data['data'])
                else:
                    return entry_data['data']

        except Exception as e:
            logger.error(f"L2 cache get error for {key}: {e}")

        return None

    async def _get_from_l3(self, key: str) -> Any:
        """Get from L3 cache (Database) with optimization"""
        if not self.l3_database_client:
            return None

        try:
            # Implementation would query database cache table
            # For now, return None as placeholder
            return None

        except Exception as e:
            logger.error(f"L3 cache get error for {key}: {e}")

        return None

    async def _apply_compression(self, value: Any) -> Tuple[Any, float]:
        """Apply compression if beneficial"""
        if not self.enable_compression:
            return value, 1.0

        try:
            # Serialize the value
            serialized = pickle.dumps(value)
            original_size = len(serialized)

            # Only compress if larger than 1KB
            if original_size > 1024:
                compressed = zlib.compress(serialized, level=6)  # Balanced compression
                compression_ratio = len(compressed) / original_size

                # Use compression if it saves at least 20%
                if compression_ratio < 0.8:
                    return compressed, compression_ratio

            return value, 1.0

        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return value, 1.0

    def _decompress_data(self, data: Any) -> Any:
        """Decompress data if compressed"""
        try:
            if isinstance(data, bytes):
                # Assume it's compressed
                decompressed = zlib.decompress(data)
                return pickle.loads(decompressed)
            else:
                return data
        except Exception as e:
            logger.error(f"Decompression failed: {e}")
            return data

    async def _check_deduplication(self, key: str, value: Any) -> Optional[str]:
        """Check for deduplication opportunities"""
        try:
            # Calculate hash of the value
            if isinstance(value, bytes):
                data_hash = hashlib.sha256(value).hexdigest()[:16]
            else:
                serialized = pickle.dumps(value)
                data_hash = hashlib.sha256(serialized).hexdigest()[:16]

            # Check if we already have this data
            if data_hash in self.data_hashes:
                existing_keys = self.data_hashes[data_hash]
                if existing_keys:
                    # Return reference to existing data
                    return list(existing_keys)[0]

            # Add to deduplication tracking
            self.data_hashes[data_hash].add(key)
            self.key_hashes[key] = data_hash

            return None

        except Exception as e:
            logger.error(f"Deduplication check failed: {e}")
            return None

    def _determine_optimal_layer(
        self,
        key: str,
        value: Any,
        compression_ratio: float
    ) -> CacheLayer:
        """Determine optimal cache layer for data"""

        # Check access pattern
        access_pattern = self._get_access_pattern(key)

        # Size-based decisions
        if isinstance(value, bytes):
            size_kb = len(value) / 1024
        else:
            size_kb = len(pickle.dumps(value)) / 1024

        # Layer selection logic
        if access_pattern == AccessPattern.HOT and size_kb < 100:  # Hot data, small size
            return CacheLayer.L1_MEMORY
        elif access_pattern in [AccessPattern.HOT, AccessPattern.WARM] and size_kb < 1000:
            return CacheLayer.L2_REDIS
        else:
            return CacheLayer.L3_DATABASE

    def _calculate_adaptive_ttl(self, key: str, default_ttl: Optional[int]) -> int:
        """Calculate adaptive TTL based on access patterns"""
        if default_ttl:
            base_ttl = default_ttl
        else:
            base_ttl = 300  # 5 minutes default

        # Get access pattern
        access_pattern = self._get_access_pattern(key)

        # Adjust TTL based on access pattern
        if access_pattern == AccessPattern.HOT:
            return base_ttl * 3  # Keep hot data longer
        elif access_pattern == AccessPattern.WARM:
            return base_ttl * 2  # Keep warm data moderately longer
        elif access_pattern == AccessPattern.COLD:
            return base_ttl // 2  # Shorter TTL for cold data
        else:
            return base_ttl

    async def _store_in_layer(
        self,
        key: str,
        value: Any,
        ttl: int,
        layer: CacheLayer,
        compression_ratio: float,
        deduplicated_key: Optional[str]
    ) -> None:
        """Store value in specified cache layer"""

        entry = CacheEntry(
            key=key,
            data=value,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=ttl),
            layer=layer,
            compression_ratio=compression_ratio,
            compressed=compression_ratio < 1.0,
            deduplicated=deduplicated_key is not None
        )

        if layer == CacheLayer.L1_MEMORY:
            await self._set_l1(key, value, ttl, entry)
        elif layer == CacheLayer.L2_REDIS:
            await self._set_l2(key, value, ttl, entry)
        elif layer == CacheLayer.L3_DATABASE:
            await self._set_l3(key, value, ttl, entry)

    async def _set_l1(self, key: str, value: Any, ttl: int, entry: Optional[CacheEntry] = None) -> None:
        """Set value in L1 cache with optimization"""
        try:
            # Check if we need to evict entries
            if len(self.l1_cache) >= self.l1_max_size and key not in self.l1_cache:
                await self._intelligent_eviction_l1()

            if entry is None:
                entry = CacheEntry(
                    key=key,
                    data=value,
                    created_at=datetime.now(),
                    expires_at=datetime.now() + timedelta(seconds=ttl),
                    layer=CacheLayer.L1_MEMORY
                )

            self.l1_cache[key] = entry

        except Exception as e:
            logger.error(f"L1 cache set error for {key}: {e}")

    async def _set_l2(self, key: str, value: Any, ttl: int, entry: Optional[CacheEntry] = None) -> None:
        """Set value in L2 cache (Redis) with optimization"""
        if not self.l2_redis_client:
            return

        try:
            # Serialize entry data
            entry_data = {
                'data': value,
                'compressed': entry.compressed if entry else False,
                'created_at': datetime.now().isoformat()
            }

            serialized_data = pickle.dumps(entry_data)

            # Store in Redis hash
            await self.l2_redis_client.hset("cache_l2", key, serialized_data)
            await self.l2_redis_client.expire("cache_l2", ttl)

        except Exception as e:
            logger.error(f"L2 cache set error for {key}: {e}")

    async def _set_l3(self, key: str, value: Any, ttl: int, entry: Optional[CacheEntry] = None) -> None:
        """Set value in L3 cache (Database) with optimization"""
        # Implementation would store in database cache table
        pass

    async def _intelligent_eviction_l1(self) -> None:
        """Intelligent eviction strategy for L1 cache"""
        # Remove expired entries first
        expired_keys = [
            k for k, entry in self.l1_cache.items() if entry.is_expired
        ]
        for key in expired_keys:
            del self.l1_cache[key]

        # If still over capacity, use sophisticated eviction
        if len(self.l1_cache) >= self.l1_max_size:
            # Calculate eviction scores (lower = more likely to evict)
            eviction_candidates = []

            for key, entry in self.l1_cache.items():
                # Score based on access pattern, frequency, and recency
                frequency_score = entry.access_frequency
                recency_score = 1.0 / max(1, entry.age_seconds)
                pattern_score = {
                    AccessPattern.HOT: 10,
                    AccessPattern.WARM: 5,
                    AccessPattern.TEMPORAL: 3,
                    AccessPattern.COLD: 1
                }.get(entry.access_pattern, 2)

                eviction_score = frequency_score + recency_score + pattern_score
                eviction_candidates.append((eviction_score, key))

            # Sort by score and remove lowest-scoring entries
            eviction_candidates.sort()
            evict_count = len(self.l1_cache) // 4  # Remove 25%

            for _, key in eviction_candidates[:evict_count]:
                # Try to promote to L2 before evicting
                if self.l2_redis_client and self.l1_cache[key].access_count > 1:
                    entry = self.l1_cache[key]
                    await self._set_l2(key, entry.data, 3600, entry)  # 1 hour in L2

                del self.l1_cache[key]

    async def _trigger_predictive_preload(self, key: str, namespace: str) -> None:
        """Trigger predictive preloading of related data"""
        if not self.enable_prediction:
            return

        try:
            # Add to prediction queue
            await self.prediction_queue.put({
                'key': key,
                'namespace': namespace,
                'timestamp': time.time()
            })

        except asyncio.QueueFull:
            logger.debug("Prediction queue full, skipping preload trigger")

    async def _cache_optimization_worker(self):
        """Background worker for cache optimization"""
        while True:
            try:
                await asyncio.sleep(30)  # Run every 30 seconds

                # Analyze cache performance
                await self._analyze_cache_performance()

                # Optimize cache distribution
                await self._optimize_cache_distribution()

                # Clean up expired entries
                await self._cleanup_expired_entries()

            except Exception as e:
                logger.error(f"Cache optimization worker error: {e}")

    async def _predictive_preloader_worker(self):
        """Background worker for predictive preloading"""
        while True:
            try:
                # Get prediction request
                prediction_request = await asyncio.wait_for(
                    self.prediction_queue.get(),
                    timeout=5.0
                )

                # Analyze access patterns and preload related data
                await self._execute_predictive_preload(prediction_request)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Predictive preloader error: {e}")

    async def _access_pattern_analyzer_worker(self):
        """Background worker for access pattern analysis"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute

                # Analyze access patterns
                await self._analyze_access_patterns()

                # Update cache promotion/demotion decisions
                await self._update_cache_distribution()

            except Exception as e:
                logger.error(f"Access pattern analyzer error: {e}")

    async def _cache_warming_worker(self):
        """Background worker for cache warming"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                # Execute cache warming strategies
                for pattern_name, warm_func in self.warm_up_patterns.items():
                    try:
                        await warm_func()
                    except Exception as e:
                        logger.error(f"Cache warming failed for {pattern_name}: {e}")

            except Exception as e:
                logger.error(f"Cache warming worker error: {e}")

    async def _memory_management_worker(self):
        """Background worker for memory management"""
        while True:
            try:
                await asyncio.sleep(120)  # Run every 2 minutes

                # Check memory usage
                await self._check_memory_usage()

                # Garbage collection if needed
                if len(self.l1_cache) > self.l1_max_size * 0.8:
                    gc.collect()

            except Exception as e:
                logger.error(f"Memory management worker error: {e}")

    # Utility methods for cache management
    def _record_access_pattern(self, key: str) -> None:
        """Record access pattern for key"""
        current_time = datetime.now()
        self.access_patterns[key].append(current_time)

        # Keep only recent access history
        cutoff_time = current_time - timedelta(seconds=self.pattern_analysis_window)
        self.access_patterns[key] = [
            access_time for access_time in self.access_patterns[key]
            if access_time > cutoff_time
        ]

    def _get_access_pattern(self, key: str) -> AccessPattern:
        """Get access pattern for key"""
        accesses = self.access_patterns.get(key, [])
        if not accesses:
            return AccessPattern.COLD

        # Calculate access frequency
        time_span = self.pattern_analysis_window
        frequency = len(accesses) / (time_span / 3600)  # accesses per hour

        if frequency > 10:
            return AccessPattern.HOT
        elif frequency > 1:
            return AccessPattern.WARM
        else:
            return AccessPattern.COLD

    def _should_promote_to_l1(self, key: str) -> bool:
        """Determine if key should be promoted to L1"""
        return self._get_access_pattern(key) in [AccessPattern.HOT, AccessPattern.WARM]

    def _should_promote_to_l2(self, key: str) -> bool:
        """Determine if key should be promoted to L2"""
        return self._get_access_pattern(key) != AccessPattern.COLD

    def _build_key(self, namespace: str, key: str) -> str:
        """Build cache key with namespace"""
        return f"{namespace}:{key}"

    async def _execute_fallback(self, fallback_func: Callable) -> Any:
        """Execute fallback function"""
        try:
            if asyncio.iscoroutinefunction(fallback_func):
                return await fallback_func()
            else:
                return fallback_func()
        except Exception as e:
            logger.error(f"Fallback function execution failed: {e}")
            raise

    def _update_hit_rate(self, current_rate: float, hit: bool) -> float:
        """Update rolling hit rate"""
        # Simple exponential moving average
        alpha = 0.1
        new_value = 1.0 if hit else 0.0
        return (1 - alpha) * current_rate + alpha * new_value

    def _update_access_metrics(self, key: str, lookup_time: float, layer: Optional[CacheLayer]) -> None:
        """Update access metrics for performance tracking"""
        # Update layer-specific metrics
        if layer == CacheLayer.L1_MEMORY:
            self.metrics.avg_l1_lookup_ms = self._update_rolling_average(
                self.metrics.avg_l1_lookup_ms, lookup_time
            )
        elif layer == CacheLayer.L2_REDIS:
            self.metrics.avg_l2_lookup_ms = self._update_rolling_average(
                self.metrics.avg_l2_lookup_ms, lookup_time
            )
        elif layer == CacheLayer.L3_DATABASE:
            self.metrics.avg_l3_lookup_ms = self._update_rolling_average(
                self.metrics.avg_l3_lookup_ms, lookup_time
            )

        # Update overall average
        self.metrics.avg_lookup_time_ms = self._update_rolling_average(
            self.metrics.avg_lookup_time_ms, lookup_time
        )

    def _update_rolling_average(self, current_avg: float, new_value: float) -> float:
        """Update rolling average with exponential decay"""
        alpha = 0.1
        return (1 - alpha) * current_avg + alpha * new_value

    async def get_optimization_metrics(self) -> Dict[str, Any]:
        """Get comprehensive cache optimization metrics"""
        return {
            **asdict(self.metrics),
            'cache_sizes': {
                'l1_size': len(self.l1_cache),
                'l1_max_size': self.l1_max_size,
                'deduplication_savings': len(self.data_hashes),
                'access_patterns_tracked': len(self.access_patterns)
            },
            'optimization_status': {
                'target_achievement': self.metrics.overall_hit_rate > 0.95,
                'performance_grade': self._calculate_performance_grade(),
                'memory_efficiency': f"{self.metrics.memory_efficiency:.1f}%"
            }
        }

    def _calculate_performance_grade(self) -> str:
        """Calculate overall performance grade"""
        hit_rate = self.metrics.overall_hit_rate
        lookup_time = self.metrics.avg_lookup_time_ms

        if hit_rate > 0.95 and lookup_time < 2:
            return "A+"
        elif hit_rate > 0.90 and lookup_time < 5:
            return "A"
        elif hit_rate > 0.85 and lookup_time < 10:
            return "B"
        elif hit_rate > 0.75 and lookup_time < 20:
            return "C"
        else:
            return "D"

    # Placeholder methods for additional functionality
    async def _initial_cache_warming(self) -> None:
        """Initial cache warming on startup"""
        pass

    async def _warm_up_lead_patterns(self) -> None:
        """Warm up common lead data patterns"""
        pass

    async def _warm_up_property_patterns(self) -> None:
        """Warm up common property data patterns"""
        pass

    async def _warm_up_ml_predictions(self) -> None:
        """Warm up common ML prediction patterns"""
        pass

    async def _analyze_cache_performance(self) -> None:
        """Analyze overall cache performance"""
        pass

    async def _optimize_cache_distribution(self) -> None:
        """Optimize data distribution across cache layers"""
        pass

    async def _cleanup_expired_entries(self) -> None:
        """Clean up expired entries across all layers"""
        pass

    async def _execute_predictive_preload(self, prediction_request: Dict[str, Any]) -> None:
        """Execute predictive preloading"""
        pass

    async def _analyze_access_patterns(self) -> None:
        """Analyze access patterns for optimization"""
        pass

    async def _update_cache_distribution(self) -> None:
        """Update cache distribution based on patterns"""
        pass

    async def _check_memory_usage(self) -> None:
        """Check and optimize memory usage"""
        pass


# Global instance
_advanced_cache_optimizer = None


def get_advanced_cache_optimizer(**kwargs) -> AdvancedCacheOptimizer:
    """Get singleton advanced cache optimizer"""
    global _advanced_cache_optimizer
    if _advanced_cache_optimizer is None:
        _advanced_cache_optimizer = AdvancedCacheOptimizer(**kwargs)
    return _advanced_cache_optimizer


# Decorator for automatic advanced caching
def advanced_cache(
    namespace: str = "default",
    ttl: int = 300,
    layer: Optional[CacheLayer] = None,
    enable_preload: bool = True
):
    """Advanced caching decorator with optimization features"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            optimizer = get_advanced_cache_optimizer()

            result = await optimizer.get(
                key=cache_key,
                namespace=namespace,
                fallback_func=lambda: func(*args, **kwargs),
                ttl=ttl,
                enable_preload=enable_preload
            )

            return result

        return wrapper
    return decorator


__all__ = [
    "AdvancedCacheOptimizer",
    "CacheLayer",
    "AccessPattern",
    "CacheEntry",
    "CacheOptimizationMetrics",
    "get_advanced_cache_optimizer",
    "advanced_cache"
]