"""
Database Sharding Strategy for Phase 4 Enterprise Scaling

Provides horizontal partitioning aligned with GHL multi-tenant model:
- Sharding by location_id for data locality
- PostgreSQL declarative partitioning
- Cross-shard query optimization
- Linear performance scaling

Performance Targets:
- Linear scaling for 1000+ concurrent users
- Cross-shard queries: <100ms P95 latency
- Zero data loss during shard migrations
- Maintain <50ms P90 single-shard queries

Architecture:
- Location-based sharding (aligned with GHL location_id)
- Horizontal partitioning for large tables (leads, properties, conversations)
- Shard-aware connection pooling
- Query routing optimization
"""

import asyncio
import hashlib
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Callable, Set, Union
from collections import defaultdict, deque
from enum import Enum
from functools import wraps
import logging
import json

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    asyncpg = None

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class ShardingStrategy(str, Enum):
    """Sharding strategies supported."""
    HASH = "hash"           # Hash-based distribution
    RANGE = "range"         # Range-based distribution
    LOCATION = "location"   # GHL location_id based (primary)
    LIST = "list"           # List partitioning
    COMPOSITE = "composite" # Multiple criteria


class ShardState(str, Enum):
    """Shard operational state."""
    ACTIVE = "active"
    READONLY = "readonly"
    MIGRATING = "migrating"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class ShardHealth(str, Enum):
    """Shard health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ShardConfig:
    """Configuration for a single shard."""
    shard_id: str
    host: str
    port: int = 5432
    database: str = "enterprisehub"
    user: str = "postgres"
    password: str = ""

    # Shard boundaries
    location_ids: List[str] = field(default_factory=list)  # For location-based
    hash_range_start: int = 0  # For hash-based
    hash_range_end: int = 0

    # Connection settings
    min_connections: int = 5
    max_connections: int = 50
    command_timeout: int = 60

    # Shard metadata
    state: ShardState = ShardState.ACTIVE
    health: ShardHealth = ShardHealth.UNKNOWN
    weight: float = 1.0  # For load balancing
    is_primary: bool = True  # vs replica

    # Performance metrics
    avg_query_time_ms: float = 0.0
    queries_per_second: int = 0
    active_connections: int = 0

    @property
    def dsn(self) -> str:
        """Get PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def is_available(self) -> bool:
        """Check if shard is available for queries."""
        return self.state in [ShardState.ACTIVE, ShardState.READONLY]


@dataclass
class ShardMetrics:
    """Metrics for shard performance monitoring."""
    shard_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Query metrics
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    avg_query_time_ms: float = 0.0
    p95_query_time_ms: float = 0.0
    p99_query_time_ms: float = 0.0

    # Connection metrics
    pool_size: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    waiting_queries: int = 0

    # Data metrics
    row_count: int = 0
    data_size_mb: float = 0.0
    index_size_mb: float = 0.0

    # Cross-shard metrics
    cross_shard_queries: int = 0
    avg_cross_shard_time_ms: float = 0.0


@dataclass
class CrossShardQuery:
    """Configuration for cross-shard query execution."""
    query_id: str
    query: str
    parameters: Tuple = field(default_factory=tuple)
    target_shards: List[str] = field(default_factory=list)

    # Execution settings
    parallel: bool = True
    timeout: float = 30.0
    merge_results: bool = True

    # Results aggregation
    aggregation_type: Optional[str] = None  # sum, avg, count, concat, etc.
    order_by: Optional[str] = None
    limit: Optional[int] = None


class ShardRouter:
    """
    Intelligent shard routing for GHL multi-tenant model.

    Routes queries to appropriate shards based on:
    - Location ID (primary routing key)
    - Hash distribution for non-location queries
    - Load balancing for read replicas
    """

    def __init__(self, shards: Dict[str, ShardConfig]):
        """
        Initialize shard router.

        Args:
            shards: Dictionary of shard configurations
        """
        self.shards = shards

        # Location to shard mapping
        self.location_shard_map: Dict[str, str] = {}

        # Hash ring for non-location routing
        self.hash_ring: List[Tuple[int, str]] = []

        # Build routing tables
        self._build_routing_tables()

        # Routing statistics
        self.routing_stats: Dict[str, int] = defaultdict(int)
        self.total_routed: int = 0

    def _build_routing_tables(self) -> None:
        """Build routing tables from shard configuration."""
        for shard_id, config in self.shards.items():
            # Build location map
            for location_id in config.location_ids:
                self.location_shard_map[location_id] = shard_id

            # Build hash ring
            if config.hash_range_start < config.hash_range_end:
                self.hash_ring.append((config.hash_range_start, shard_id))

        # Sort hash ring
        self.hash_ring.sort(key=lambda x: x[0])

    def route_by_location(self, location_id: str) -> Optional[str]:
        """
        Route query to shard by GHL location ID.

        Args:
            location_id: GHL location identifier

        Returns:
            Shard ID or None if not found
        """
        shard_id = self.location_shard_map.get(location_id)

        if shard_id:
            self.routing_stats[shard_id] += 1
            self.total_routed += 1

        return shard_id

    def route_by_hash(self, key: str) -> str:
        """
        Route query by hash when location is not known.

        Args:
            key: Key to hash for routing

        Returns:
            Shard ID
        """
        if not self.hash_ring:
            # Return first available shard
            return next(iter(self.shards.keys()))

        # Hash the key
        hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16) % 1000000

        # Find appropriate shard in hash ring
        for boundary, shard_id in reversed(self.hash_ring):
            if hash_value >= boundary:
                self.routing_stats[shard_id] += 1
                self.total_routed += 1
                return shard_id

        # Default to first shard
        shard_id = self.hash_ring[0][1]
        self.routing_stats[shard_id] += 1
        self.total_routed += 1
        return shard_id

    def get_shards_for_query(
        self,
        location_id: Optional[str] = None,
        location_ids: Optional[List[str]] = None,
        all_shards: bool = False
    ) -> List[str]:
        """
        Get list of shards to query.

        Args:
            location_id: Single location ID
            location_ids: Multiple location IDs
            all_shards: Query all shards (for aggregations)

        Returns:
            List of shard IDs to query
        """
        if all_shards:
            return [
                shard_id for shard_id, config in self.shards.items()
                if config.is_available
            ]

        if location_id:
            shard_id = self.route_by_location(location_id)
            return [shard_id] if shard_id else []

        if location_ids:
            shard_ids = set()
            for loc_id in location_ids:
                shard_id = self.route_by_location(loc_id)
                if shard_id:
                    shard_ids.add(shard_id)
            return list(shard_ids)

        return []

    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        if self.total_routed == 0:
            return {"total_routed": 0, "distribution": {}}

        distribution = {}
        for shard_id, count in self.routing_stats.items():
            distribution[shard_id] = {
                "count": count,
                "percentage": (count / self.total_routed) * 100
            }

        return {
            "total_routed": self.total_routed,
            "distribution": distribution,
            "balance_score": self._calculate_balance_score()
        }

    def _calculate_balance_score(self) -> float:
        """Calculate routing balance score (0-100)."""
        if not self.routing_stats or self.total_routed == 0:
            return 100.0

        expected = self.total_routed / len(self.shards)

        if expected == 0:
            return 100.0

        variance = sum(
            ((count - expected) / expected) ** 2
            for count in self.routing_stats.values()
        ) / len(self.shards)

        return max(0.0, 100.0 - (variance * 100))

    def add_location_mapping(self, location_id: str, shard_id: str) -> None:
        """Add new location to shard mapping."""
        self.location_shard_map[location_id] = shard_id

        # Update shard config
        if shard_id in self.shards:
            self.shards[shard_id].location_ids.append(location_id)

    def remove_location_mapping(self, location_id: str) -> Optional[str]:
        """Remove location mapping and return old shard ID."""
        return self.location_shard_map.pop(location_id, None)


class ShardManager:
    """
    Enterprise shard manager with connection pooling and health monitoring.

    Features:
    - Shard-aware connection pooling
    - Cross-shard query execution
    - Automatic failover to replicas
    - Performance monitoring and optimization
    """

    def __init__(
        self,
        shards: Optional[List[ShardConfig]] = None,
        strategy: ShardingStrategy = ShardingStrategy.LOCATION
    ):
        """
        Initialize shard manager.

        Args:
            shards: List of shard configurations
            strategy: Primary sharding strategy
        """
        self.strategy = strategy

        # Shard configurations
        self.shard_configs: Dict[str, ShardConfig] = {}
        if shards:
            for config in shards:
                self.shard_configs[config.shard_id] = config

        # Connection pools per shard
        self.connection_pools: Dict[str, asyncpg.Pool] = {}

        # Shard router
        self.router = ShardRouter(self.shard_configs)

        # Metrics per shard
        self.shard_metrics: Dict[str, ShardMetrics] = {}

        # Query history for analysis
        self.query_history: deque = deque(maxlen=10000)

        # Cross-shard query tracking
        self.cross_shard_queries: deque = deque(maxlen=1000)

        # Background tasks
        self.background_tasks: List[asyncio.Task] = []

        # Initialization state
        self.initialized = False

        logger.info(f"Shard Manager initialized with {len(self.shard_configs)} shards")

    async def initialize(self) -> bool:
        """
        Initialize shard connections and monitoring.

        Returns:
            True if initialization successful
        """
        try:
            # Setup default shards if none configured
            if not self.shard_configs:
                await self._setup_default_shards()

            # Create connection pools for each shard
            for shard_id, config in self.shard_configs.items():
                await self._create_shard_pool(shard_id, config)

            # Initialize metrics
            for shard_id in self.shard_configs:
                self.shard_metrics[shard_id] = ShardMetrics(shard_id=shard_id)

            # Start background monitoring
            self.background_tasks = [
                asyncio.create_task(self._health_monitor_worker()),
                asyncio.create_task(self._metrics_collector_worker()),
                asyncio.create_task(self._rebalance_monitor_worker()),
                asyncio.create_task(self._query_analyzer_worker()),
            ]

            self.initialized = True
            logger.info("Shard Manager initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Shard Manager: {e}")
            return False

    async def _setup_default_shards(self) -> None:
        """Setup default shard configuration for development."""
        # Default 3-shard configuration
        default_shards = [
            ShardConfig(
                shard_id="shard-1",
                host="localhost",
                port=5432,
                database="enterprisehub_shard1",
                hash_range_start=0,
                hash_range_end=333333,
                location_ids=["loc_default_1"]
            ),
            ShardConfig(
                shard_id="shard-2",
                host="localhost",
                port=5433,
                database="enterprisehub_shard2",
                hash_range_start=333334,
                hash_range_end=666666,
                location_ids=["loc_default_2"]
            ),
            ShardConfig(
                shard_id="shard-3",
                host="localhost",
                port=5434,
                database="enterprisehub_shard3",
                hash_range_start=666667,
                hash_range_end=1000000,
                location_ids=["loc_default_3"]
            ),
        ]

        for config in default_shards:
            self.shard_configs[config.shard_id] = config

        # Rebuild router
        self.router = ShardRouter(self.shard_configs)

    async def _create_shard_pool(self, shard_id: str, config: ShardConfig) -> None:
        """Create connection pool for a shard."""
        try:
            pool = await asyncpg.create_pool(
                dsn=config.dsn,
                min_size=config.min_connections,
                max_size=config.max_connections,
                command_timeout=config.command_timeout,
                server_settings={
                    'application_name': f'EnterpriseHub_Shard_{shard_id}',
                    'jit': 'off'
                }
            )

            # Test connection
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            self.connection_pools[shard_id] = pool
            config.health = ShardHealth.HEALTHY
            logger.info(f"Created connection pool for shard {shard_id}")

        except Exception as e:
            logger.error(f"Failed to create pool for shard {shard_id}: {e}")
            config.health = ShardHealth.UNHEALTHY

    async def execute(
        self,
        query: str,
        params: Tuple = (),
        location_id: Optional[str] = None,
        shard_id: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> Any:
        """
        Execute query on appropriate shard.

        Args:
            query: SQL query
            params: Query parameters
            location_id: GHL location ID for routing
            shard_id: Direct shard ID (overrides routing)
            timeout: Query timeout

        Returns:
            Query result
        """
        if not self.initialized:
            raise RuntimeError("Shard Manager not initialized")

        start_time = time.time()

        # Determine target shard
        if shard_id:
            target_shard = shard_id
        elif location_id:
            target_shard = self.router.route_by_location(location_id)
        else:
            # Extract location from query or use hash routing
            target_shard = self._extract_shard_from_query(query, params)

        if not target_shard or target_shard not in self.connection_pools:
            raise ValueError(f"No valid shard found for query")

        # Execute on target shard
        try:
            pool = self.connection_pools[target_shard]
            config = self.shard_configs[target_shard]

            async with pool.acquire() as conn:
                if timeout:
                    result = await asyncio.wait_for(
                        conn.fetch(query, *params),
                        timeout=timeout
                    )
                else:
                    result = await conn.fetch(query, *params)

            # Record metrics
            execution_time = (time.time() - start_time) * 1000
            await self._record_query_metrics(target_shard, execution_time, True)

            return result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            await self._record_query_metrics(target_shard, execution_time, False)
            logger.error(f"Query execution failed on shard {target_shard}: {e}")
            raise

    async def execute_cross_shard(
        self,
        query: CrossShardQuery
    ) -> List[Any]:
        """
        Execute query across multiple shards.

        Args:
            query: Cross-shard query configuration

        Returns:
            Aggregated results from all shards
        """
        if not self.initialized:
            raise RuntimeError("Shard Manager not initialized")

        start_time = time.time()

        # Determine target shards
        if query.target_shards:
            shards = query.target_shards
        else:
            shards = list(self.connection_pools.keys())

        if query.parallel:
            # Execute in parallel
            tasks = []
            for shard_id in shards:
                tasks.append(self._execute_on_shard(
                    shard_id, query.query, query.parameters, query.timeout
                ))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions
            valid_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Cross-shard query failed on {shards[i]}: {result}")
                else:
                    valid_results.extend(result)

        else:
            # Execute sequentially
            valid_results = []
            for shard_id in shards:
                try:
                    result = await self._execute_on_shard(
                        shard_id, query.query, query.parameters, query.timeout
                    )
                    valid_results.extend(result)
                except Exception as e:
                    logger.error(f"Cross-shard query failed on {shard_id}: {e}")

        # Record cross-shard metrics
        execution_time = (time.time() - start_time) * 1000
        self.cross_shard_queries.append({
            "query_id": query.query_id,
            "shards": shards,
            "execution_time_ms": execution_time,
            "results_count": len(valid_results)
        })

        # Apply result processing
        if query.merge_results:
            valid_results = self._merge_results(
                valid_results,
                query.aggregation_type,
                query.order_by,
                query.limit
            )

        return valid_results

    async def _execute_on_shard(
        self,
        shard_id: str,
        query: str,
        params: Tuple,
        timeout: float
    ) -> List[Any]:
        """Execute query on a specific shard."""
        pool = self.connection_pools.get(shard_id)
        if not pool:
            raise ValueError(f"No connection pool for shard {shard_id}")

        async with pool.acquire() as conn:
            if timeout:
                result = await asyncio.wait_for(
                    conn.fetch(query, *params),
                    timeout=timeout
                )
            else:
                result = await conn.fetch(query, *params)

        return [dict(row) for row in result]

    def _extract_shard_from_query(self, query: str, params: Tuple) -> Optional[str]:
        """Extract shard from query when location_id not provided."""
        # Simple heuristic - look for location_id in params or query
        query_lower = query.lower()

        # Check if location_id is in WHERE clause
        if 'location_id' in query_lower:
            # Try to find location_id value in params
            # This is a simplified approach - production would parse the query
            for param in params:
                if isinstance(param, str) and param.startswith('loc_'):
                    return self.router.route_by_location(param)

        # Fall back to hash-based routing using first param
        if params:
            return self.router.route_by_hash(str(params[0]))

        # Default to first available shard
        for shard_id, config in self.shard_configs.items():
            if config.is_available:
                return shard_id

        return None

    def _merge_results(
        self,
        results: List[Any],
        aggregation_type: Optional[str],
        order_by: Optional[str],
        limit: Optional[int]
    ) -> List[Any]:
        """Merge and process cross-shard results."""
        if not results:
            return []

        # Apply ordering
        if order_by and results and isinstance(results[0], dict):
            # Parse order_by (e.g., "created_at DESC")
            parts = order_by.split()
            field = parts[0]
            descending = len(parts) > 1 and parts[1].upper() == 'DESC'

            results.sort(
                key=lambda x: x.get(field, ''),
                reverse=descending
            )

        # Apply limit
        if limit and len(results) > limit:
            results = results[:limit]

        # Apply aggregation
        if aggregation_type and results:
            return self._aggregate_results(results, aggregation_type)

        return results

    def _aggregate_results(
        self,
        results: List[Dict[str, Any]],
        aggregation_type: str
    ) -> List[Dict[str, Any]]:
        """Apply aggregation to merged results."""
        if not results:
            return []

        if aggregation_type == 'count':
            return [{"count": len(results)}]

        if aggregation_type == 'sum':
            # Sum all numeric values
            summed = {}
            for result in results:
                for key, value in result.items():
                    if isinstance(value, (int, float)):
                        summed[key] = summed.get(key, 0) + value
            return [summed]

        if aggregation_type == 'avg':
            # Average all numeric values
            sums = {}
            counts = {}
            for result in results:
                for key, value in result.items():
                    if isinstance(value, (int, float)):
                        sums[key] = sums.get(key, 0) + value
                        counts[key] = counts.get(key, 0) + 1
            return [{key: sums[key] / counts[key] for key in sums}]

        return results

    async def _record_query_metrics(
        self,
        shard_id: str,
        execution_time_ms: float,
        success: bool
    ) -> None:
        """Record query performance metrics."""
        if shard_id not in self.shard_metrics:
            self.shard_metrics[shard_id] = ShardMetrics(shard_id=shard_id)

        metrics = self.shard_metrics[shard_id]
        metrics.total_queries += 1

        if success:
            metrics.successful_queries += 1
        else:
            metrics.failed_queries += 1

        # Update average query time
        alpha = 0.1
        metrics.avg_query_time_ms = (
            (1 - alpha) * metrics.avg_query_time_ms + alpha * execution_time_ms
        )

        # Record in history
        self.query_history.append({
            "shard_id": shard_id,
            "execution_time_ms": execution_time_ms,
            "success": success,
            "timestamp": time.time()
        })

    # Background workers
    async def _health_monitor_worker(self) -> None:
        """Monitor shard health."""
        while True:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds

                for shard_id, config in self.shard_configs.items():
                    await self._check_shard_health(shard_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")

    async def _check_shard_health(self, shard_id: str) -> None:
        """Check health of a single shard."""
        config = self.shard_configs.get(shard_id)
        pool = self.connection_pools.get(shard_id)

        if not config or not pool:
            return

        try:
            start = time.time()
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            latency = (time.time() - start) * 1000

            # Update config
            config.avg_query_time_ms = latency
            config.active_connections = pool.get_size() - pool.get_idle_size()

            # Determine health
            if latency < 50:
                config.health = ShardHealth.HEALTHY
            elif latency < 200:
                config.health = ShardHealth.DEGRADED
            else:
                config.health = ShardHealth.UNHEALTHY

            # Update metrics
            if shard_id in self.shard_metrics:
                self.shard_metrics[shard_id].pool_size = pool.get_size()
                self.shard_metrics[shard_id].active_connections = config.active_connections
                self.shard_metrics[shard_id].idle_connections = pool.get_idle_size()

        except Exception as e:
            logger.error(f"Health check failed for shard {shard_id}: {e}")
            config.health = ShardHealth.UNHEALTHY

    async def _metrics_collector_worker(self) -> None:
        """Collect detailed shard metrics."""
        while True:
            try:
                await asyncio.sleep(60)  # Collect every minute

                for shard_id in self.connection_pools:
                    await self._collect_shard_metrics(shard_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collector error: {e}")

    async def _collect_shard_metrics(self, shard_id: str) -> None:
        """Collect detailed metrics for a shard."""
        pool = self.connection_pools.get(shard_id)
        if not pool:
            return

        try:
            async with pool.acquire() as conn:
                # Get database size
                size_result = await conn.fetchrow("""
                    SELECT
                        pg_database_size(current_database()) as db_size,
                        pg_indexes_size(current_database()::regclass) as index_size
                """)

                if size_result and shard_id in self.shard_metrics:
                    metrics = self.shard_metrics[shard_id]
                    metrics.data_size_mb = size_result['db_size'] / (1024 * 1024)
                    metrics.index_size_mb = size_result['index_size'] / (1024 * 1024) if size_result['index_size'] else 0

        except Exception as e:
            logger.debug(f"Metrics collection failed for {shard_id}: {e}")

    async def _rebalance_monitor_worker(self) -> None:
        """Monitor shard balance and suggest rebalancing."""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes

                stats = self.router.get_routing_stats()
                if stats['balance_score'] < 70:
                    logger.warning(
                        f"Shard imbalance detected. Balance score: {stats['balance_score']:.2f}"
                    )
                    # In production, this would trigger rebalancing logic

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Rebalance monitor error: {e}")

    async def _query_analyzer_worker(self) -> None:
        """Analyze query patterns for optimization."""
        while True:
            try:
                await asyncio.sleep(120)  # Analyze every 2 minutes

                await self._analyze_query_patterns()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Query analyzer error: {e}")

    async def _analyze_query_patterns(self) -> None:
        """Analyze query patterns across shards."""
        if len(self.query_history) < 100:
            return

        # Calculate per-shard statistics
        shard_stats = defaultdict(lambda: {"count": 0, "total_time": 0, "failures": 0})

        for query in self.query_history:
            shard_id = query['shard_id']
            shard_stats[shard_id]['count'] += 1
            shard_stats[shard_id]['total_time'] += query['execution_time_ms']
            if not query['success']:
                shard_stats[shard_id]['failures'] += 1

        # Update percentile metrics
        for shard_id in self.connection_pools:
            shard_queries = [
                q['execution_time_ms'] for q in self.query_history
                if q['shard_id'] == shard_id and q['success']
            ]

            if shard_queries and shard_id in self.shard_metrics:
                sorted_times = sorted(shard_queries)
                metrics = self.shard_metrics[shard_id]
                metrics.p95_query_time_ms = sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0
                metrics.p99_query_time_ms = sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0

    async def close(self) -> None:
        """Close all connections and stop workers."""
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()

        await asyncio.gather(*self.background_tasks, return_exceptions=True)

        # Close connection pools
        for pool in self.connection_pools.values():
            try:
                await pool.close()
            except Exception:
                pass

        self.initialized = False
        logger.info("Shard Manager closed")

    async def get_shard_health(self) -> Dict[str, Any]:
        """Get comprehensive shard health status."""
        health_status = {
            "total_shards": len(self.shard_configs),
            "healthy_shards": 0,
            "unhealthy_shards": 0,
            "shards": {}
        }

        for shard_id, config in self.shard_configs.items():
            metrics = self.shard_metrics.get(shard_id, ShardMetrics(shard_id=shard_id))

            health_status["shards"][shard_id] = {
                "state": config.state.value,
                "health": config.health.value,
                "avg_query_time_ms": metrics.avg_query_time_ms,
                "p95_query_time_ms": metrics.p95_query_time_ms,
                "total_queries": metrics.total_queries,
                "success_rate": (
                    metrics.successful_queries / metrics.total_queries
                    if metrics.total_queries > 0 else 1.0
                ),
                "pool_size": metrics.pool_size,
                "active_connections": metrics.active_connections,
                "data_size_mb": metrics.data_size_mb
            }

            if config.health == ShardHealth.HEALTHY:
                health_status["healthy_shards"] += 1
            else:
                health_status["unhealthy_shards"] += 1

        # Add routing statistics
        health_status["routing"] = self.router.get_routing_stats()

        # Add cross-shard query stats
        recent_cross_shard = list(self.cross_shard_queries)[-100:]
        if recent_cross_shard:
            cross_shard_times = [q['execution_time_ms'] for q in recent_cross_shard]
            health_status["cross_shard"] = {
                "total_queries": len(recent_cross_shard),
                "avg_time_ms": sum(cross_shard_times) / len(cross_shard_times),
                "max_time_ms": max(cross_shard_times),
                "target_met": sum(cross_shard_times) / len(cross_shard_times) < 100
            }

        return health_status

    async def add_shard(self, config: ShardConfig) -> bool:
        """Add a new shard to the cluster."""
        if config.shard_id in self.shard_configs:
            logger.warning(f"Shard {config.shard_id} already exists")
            return False

        try:
            # Add configuration
            self.shard_configs[config.shard_id] = config

            # Create connection pool
            await self._create_shard_pool(config.shard_id, config)

            # Update router
            self.router = ShardRouter(self.shard_configs)

            # Initialize metrics
            self.shard_metrics[config.shard_id] = ShardMetrics(shard_id=config.shard_id)

            logger.info(f"Added shard {config.shard_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add shard {config.shard_id}: {e}")
            return False

    async def remove_shard(self, shard_id: str, migrate_data: bool = True) -> bool:
        """Remove a shard from the cluster."""
        if shard_id not in self.shard_configs:
            return False

        try:
            # Mark shard as offline
            self.shard_configs[shard_id].state = ShardState.OFFLINE

            if migrate_data:
                # Migrate data to remaining shards
                await self._migrate_shard_data(shard_id)

            # Close connection pool
            if shard_id in self.connection_pools:
                await self.connection_pools[shard_id].close()
                del self.connection_pools[shard_id]

            # Remove from configuration
            del self.shard_configs[shard_id]

            # Update router
            self.router = ShardRouter(self.shard_configs)

            # Remove metrics
            if shard_id in self.shard_metrics:
                del self.shard_metrics[shard_id]

            logger.info(f"Removed shard {shard_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove shard {shard_id}: {e}")
            return False

    async def _migrate_shard_data(self, source_shard: str) -> None:
        """Migrate data from source shard to remaining shards."""
        # In production, this would implement actual data migration
        # For now, just log the intent
        logger.info(f"Data migration from {source_shard} would be triggered here")


# Global instance
_shard_manager: Optional[ShardManager] = None


async def get_shard_manager(
    shards: Optional[List[ShardConfig]] = None,
    strategy: ShardingStrategy = ShardingStrategy.LOCATION
) -> ShardManager:
    """Get or create global shard manager."""
    global _shard_manager

    if _shard_manager is None:
        _shard_manager = ShardManager(shards, strategy)
        await _shard_manager.initialize()

    return _shard_manager


# Decorator for location-sharded queries
def location_sharded(location_param: str = "location_id"):
    """
    Decorator for automatic location-based shard routing.

    Args:
        location_param: Name of the location_id parameter in the function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract location_id from kwargs
            location_id = kwargs.get(location_param)

            if not location_id:
                # Try to find in args based on function signature
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                if location_param in params:
                    idx = params.index(location_param)
                    if idx < len(args):
                        location_id = args[idx]

            # Get shard manager
            manager = await get_shard_manager()

            # Route to appropriate shard
            if location_id:
                shard_id = manager.router.route_by_location(location_id)
                if shard_id:
                    kwargs['_shard_id'] = shard_id

            return await func(*args, **kwargs)

        return wrapper
    return decorator


__all__ = [
    "ShardingStrategy",
    "ShardState",
    "ShardHealth",
    "ShardConfig",
    "ShardMetrics",
    "CrossShardQuery",
    "ShardRouter",
    "ShardManager",
    "get_shard_manager",
    "location_sharded",
]
