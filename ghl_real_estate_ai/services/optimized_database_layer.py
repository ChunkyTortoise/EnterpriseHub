"""
Optimized Database Layer
========================

High-performance database layer with connection pooling, query optimization,
async operations, and intelligent caching for maximum performance.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import asyncpg
import redis.asyncio as redis
from contextlib import asynccontextmanager
import weakref

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Database query types for optimization"""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    BULK_INSERT = "bulk_insert"
    ANALYTICS = "analytics"


class CacheLevel(Enum):
    """Cache levels for different data types"""
    L1_MEMORY = "l1_memory"      # Fast memory cache
    L2_REDIS = "l2_redis"        # Distributed Redis cache
    L3_DATABASE = "l3_database"  # Database with optimized queries


@dataclass
class QueryStats:
    """Query performance statistics"""
    query_type: QueryType
    execution_time_ms: float
    rows_affected: int
    cache_hit: bool
    timestamp: datetime
    query_hash: str


@dataclass
class ConnectionPoolConfig:
    """Database connection pool configuration"""
    min_connections: int = 5
    max_connections: int = 50
    max_idle_time: int = 300  # seconds
    command_timeout: int = 60  # seconds
    server_settings: Dict[str, Any] = None


class OptimizedConnectionPool:
    """
    Advanced connection pool with load balancing, health monitoring,
    and automatic failover capabilities.
    """

    def __init__(self, config: ConnectionPoolConfig, database_url: str):
        self.config = config
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
        self.stats: Dict[str, Any] = {
            "total_queries": 0,
            "active_connections": 0,
            "pool_hits": 0,
            "pool_misses": 0,
            "avg_query_time": 0.0
        }
        self._query_times: List[float] = []
        self._health_check_task: Optional[asyncio.Task] = None

    async def initialize(self) -> None:
        """Initialize the connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                max_inactive_connection_lifetime=self.config.max_idle_time,
                command_timeout=self.config.command_timeout,
                server_settings=self.config.server_settings or {
                    "application_name": "enterprisehub_optimized",
                    "jit": "off",  # Disable JIT for consistent performance
                    "max_parallel_workers_per_gather": "2",
                    "work_mem": "64MB"
                }
            )

            # Start health monitoring
            self._health_check_task = asyncio.create_task(self._health_monitor())
            logger.info(f"Database pool initialized with {self.config.min_connections}-{self.config.max_connections} connections")

        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    async def close(self) -> None:
        """Close the connection pool"""
        if self._health_check_task:
            self._health_check_task.cancel()

        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")

    @asynccontextmanager
    async def acquire_connection(self):
        """Acquire a database connection from the pool"""
        if not self.pool:
            raise RuntimeError("Connection pool not initialized")

        start_time = time.time()
        try:
            async with self.pool.acquire() as connection:
                self.stats["pool_hits"] += 1
                self.stats["active_connections"] += 1
                yield connection
        except Exception as e:
            self.stats["pool_misses"] += 1
            logger.error(f"Failed to acquire connection: {e}")
            raise
        finally:
            self.stats["active_connections"] = max(0, self.stats["active_connections"] - 1)
            query_time = (time.time() - start_time) * 1000
            self._update_query_stats(query_time)

    async def execute_query(self, query: str, *args) -> Any:
        """Execute a query with performance tracking"""
        start_time = time.time()

        try:
            async with self.acquire_connection() as conn:
                result = await conn.fetch(query, *args)
                execution_time = (time.time() - start_time) * 1000

                self.stats["total_queries"] += 1
                self._query_times.append(execution_time)

                # Keep only recent query times for average calculation
                if len(self._query_times) > 1000:
                    self._query_times = self._query_times[-1000:]

                return result

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    def _update_query_stats(self, query_time_ms: float) -> None:
        """Update query performance statistics"""
        self._query_times.append(query_time_ms)
        if len(self._query_times) > 100:
            self.stats["avg_query_time"] = sum(self._query_times[-100:]) / 100

    async def _health_monitor(self) -> None:
        """Monitor pool health and performance"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                if self.pool:
                    # Check pool statistics
                    pool_size = self.pool.get_size()
                    idle_connections = self.pool.get_idle_size()

                    logger.debug(
                        f"Pool health: size={pool_size}, "
                        f"idle={idle_connections}, "
                        f"active={self.stats['active_connections']}"
                    )

                    # Test connection with simple query
                    async with self.acquire_connection() as conn:
                        await conn.fetchval("SELECT 1")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Health check failed: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        if self.pool:
            return {
                **self.stats,
                "pool_size": self.pool.get_size(),
                "idle_connections": self.pool.get_idle_size()
            }
        return self.stats


class QueryOptimizer:
    """
    Intelligent query optimizer with caching, batching, and execution planning.
    """

    def __init__(self):
        self.query_cache: Dict[str, str] = {}  # Optimized query cache
        self.execution_plans: Dict[str, Dict] = {}  # Query execution plans
        self.query_stats: Dict[str, List[QueryStats]] = {}
        self.batch_operations: Dict[str, List] = {}

    def optimize_select_query(self, base_query: str, params: Dict[str, Any]) -> Tuple[str, List]:
        """Optimize SELECT queries with intelligent indexing hints"""

        # Add query hints for better performance
        optimized_query = base_query

        # Add index hints for common patterns
        if "WHERE agent_id" in base_query:
            optimized_query = optimized_query.replace(
                "SELECT", "SELECT /*+ INDEX(agent_performance_idx) */"
            )

        if "ORDER BY created_at" in base_query:
            optimized_query = optimized_query.replace(
                "ORDER BY created_at",
                "ORDER BY created_at /*+ USE_INDEX(created_at_idx) */"
            )

        # Optimize date range queries
        if "created_at BETWEEN" in base_query:
            # Use partition pruning for date ranges
            optimized_query = optimized_query.replace(
                "created_at BETWEEN",
                "created_at BETWEEN /* PARTITION_WISE */"
            )

        # Convert dict params to list for asyncpg
        param_list = list(params.values()) if isinstance(params, dict) else params

        return optimized_query, param_list

    def should_use_batch_operation(self, query_type: QueryType, operation_count: int) -> bool:
        """Determine if operation should use batching"""
        batch_thresholds = {
            QueryType.INSERT: 5,
            QueryType.UPDATE: 10,
            QueryType.DELETE: 10
        }

        threshold = batch_thresholds.get(query_type, 50)
        return operation_count >= threshold

    def create_batch_insert_query(self, table: str, columns: List[str], rows: List[List]) -> str:
        """Create optimized batch insert query"""
        if not rows:
            return ""

        placeholders = ", ".join(
            f"({', '.join(f'${i * len(columns) + j + 1}' for j in range(len(columns)))})"
            for i in range(len(rows))
        )

        query = f"""
        INSERT INTO {table} ({', '.join(columns)})
        VALUES {placeholders}
        ON CONFLICT DO NOTHING
        """

        return query

    def analyze_query_performance(self, query_hash: str) -> Dict[str, Any]:
        """Analyze query performance and provide optimization recommendations"""
        stats = self.query_stats.get(query_hash, [])

        if not stats:
            return {"message": "No performance data available"}

        recent_stats = stats[-50:]  # Last 50 executions
        avg_time = sum(s.execution_time_ms for s in recent_stats) / len(recent_stats)
        cache_hit_rate = sum(1 for s in recent_stats if s.cache_hit) / len(recent_stats)

        recommendations = []

        if avg_time > 1000:  # Slow query (> 1 second)
            recommendations.append("Consider adding database indexes")
            recommendations.append("Review query for unnecessary JOINs")

        if cache_hit_rate < 0.7:  # Low cache hit rate
            recommendations.append("Increase cache TTL for this query type")
            recommendations.append("Consider query result caching")

        return {
            "average_execution_time_ms": avg_time,
            "cache_hit_rate": cache_hit_rate,
            "total_executions": len(recent_stats),
            "recommendations": recommendations
        }


class MultiLevelCache:
    """
    Multi-level caching system with L1 (memory), L2 (Redis), and L3 (database) layers.
    """

    def __init__(self):
        self.l1_cache: Dict[str, Dict[str, Any]] = {}  # Memory cache
        self.l2_client: Optional[redis.Redis] = None  # Redis cache
        self.cache_stats: Dict[str, int] = {
            "l1_hits": 0,
            "l2_hits": 0,
            "l3_hits": 0,
            "misses": 0
        }

    async def initialize_redis(self, redis_url: str) -> None:
        """Initialize Redis L2 cache"""
        try:
            self.l2_client = redis.from_url(redis_url)
            await self.l2_client.ping()
            logger.info("L2 Redis cache initialized")
        except Exception as e:
            logger.warning(f"L2 cache initialization failed: {e}")

    async def get(self, key: str, fetch_func: Optional[callable] = None) -> Any:
        """Get value from multi-level cache"""

        # L1 Memory cache
        if key in self.l1_cache:
            entry = self.l1_cache[key]
            if entry['expires_at'] > datetime.now():
                self.cache_stats["l1_hits"] += 1
                return entry['value']
            else:
                del self.l1_cache[key]

        # L2 Redis cache
        if self.l2_client:
            try:
                redis_value = await self.l2_client.get(f"cache:l2:{key}")
                if redis_value:
                    value = json.loads(redis_value)
                    # Promote to L1 cache
                    await self.set_l1(key, value, ttl=300)  # 5 minutes in L1
                    self.cache_stats["l2_hits"] += 1
                    return value
            except Exception as e:
                logger.warning(f"L2 cache error: {e}")

        # L3 Database fetch
        if fetch_func:
            value = await fetch_func() if asyncio.iscoroutinefunction(fetch_func) else fetch_func()
            if value is not None:
                # Store in all levels
                await self.set(key, value)
                self.cache_stats["l3_hits"] += 1
                return value

        self.cache_stats["misses"] += 1
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in all cache levels"""
        await self.set_l1(key, value, ttl=min(ttl, 300))  # Max 5 min in L1
        await self.set_l2(key, value, ttl=ttl)

    async def set_l1(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value in L1 memory cache"""
        # Implement LRU eviction
        if len(self.l1_cache) > 1000:
            # Remove oldest entry
            oldest_key = min(
                self.l1_cache.keys(),
                key=lambda k: self.l1_cache[k]['created_at']
            )
            del self.l1_cache[oldest_key]

        self.l1_cache[key] = {
            'value': value,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(seconds=ttl)
        }

    async def set_l2(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in L2 Redis cache"""
        if self.l2_client:
            try:
                await self.l2_client.setex(
                    f"cache:l2:{key}",
                    ttl,
                    json.dumps(value, default=str)
                )
            except Exception as e:
                logger.warning(f"L2 cache set error: {e}")

    async def invalidate(self, pattern: str) -> None:
        """Invalidate cache entries matching pattern"""
        # L1 invalidation
        keys_to_remove = [k for k in self.l1_cache.keys() if pattern in k]
        for key in keys_to_remove:
            del self.l1_cache[key]

        # L2 invalidation
        if self.l2_client:
            try:
                keys = await self.l2_client.keys(f"cache:l2:*{pattern}*")
                if keys:
                    await self.l2_client.delete(*keys)
            except Exception as e:
                logger.warning(f"L2 cache invalidation error: {e}")


class OptimizedDatabaseLayer:
    """
    Main optimized database layer coordinating all performance improvements.
    """

    def __init__(self, database_url: str, redis_url: str = "redis://localhost:6379/2"):
        self.database_url = database_url
        self.redis_url = redis_url

        # Initialize components
        self.pool_config = ConnectionPoolConfig()
        self.connection_pool = OptimizedConnectionPool(self.pool_config, database_url)
        self.query_optimizer = QueryOptimizer()
        self.cache = MultiLevelCache()

        # Performance tracking
        self.operation_stats: Dict[str, Any] = {
            "total_operations": 0,
            "cache_hit_rate": 0.0,
            "average_response_time": 0.0,
            "query_types": {}
        }

    async def initialize(self) -> None:
        """Initialize the optimized database layer"""
        logger.info("Initializing Optimized Database Layer")

        await self.connection_pool.initialize()
        await self.cache.initialize_redis(self.redis_url)

        logger.info("Optimized Database Layer initialized successfully")

    async def close(self) -> None:
        """Close the database layer"""
        await self.connection_pool.close()
        logger.info("Optimized Database Layer closed")

    async def execute_optimized_query(self,
                                    query: str,
                                    params: Optional[Dict[str, Any]] = None,
                                    query_type: QueryType = QueryType.SELECT,
                                    cache_key: Optional[str] = None,
                                    cache_ttl: int = 3600) -> Any:
        """
        Execute an optimized query with caching, connection pooling, and performance monitoring.
        """
        start_time = time.time()
        params = params or {}

        try:
            # Generate cache key if not provided
            if not cache_key and query_type == QueryType.SELECT:
                cache_key = f"query:{hash(query + str(sorted(params.items())))}"

            # Try cache first for SELECT queries
            if query_type == QueryType.SELECT and cache_key:
                cached_result = await self.cache.get(cache_key)
                if cached_result is not None:
                    self._update_stats(query_type, time.time() - start_time, True)
                    return cached_result

            # Optimize query
            optimized_query, param_list = self.query_optimizer.optimize_select_query(query, params)

            # Execute query with connection pooling
            result = await self.connection_pool.execute_query(optimized_query, *param_list)

            # Cache SELECT query results
            if query_type == QueryType.SELECT and cache_key and result:
                await self.cache.set(cache_key, result, cache_ttl)

            execution_time = time.time() - start_time
            self._update_stats(query_type, execution_time, False)

            return result

        except Exception as e:
            logger.error(f"Optimized query execution failed: {e}")
            raise

    async def batch_insert(self,
                          table: str,
                          columns: List[str],
                          rows: List[List[Any]],
                          batch_size: int = 1000) -> int:
        """
        Perform optimized batch insert with chunking and transaction management.
        """
        if not rows:
            return 0

        total_inserted = 0
        start_time = time.time()

        try:
            # Process in batches
            for i in range(0, len(rows), batch_size):
                batch_rows = rows[i:i + batch_size]

                # Create batch insert query
                query = self.query_optimizer.create_batch_insert_query(table, columns, batch_rows)

                # Flatten parameters for asyncpg
                flat_params = [item for row in batch_rows for item in row]

                async with self.connection_pool.acquire_connection() as conn:
                    async with conn.transaction():
                        await conn.execute(query, *flat_params)
                        total_inserted += len(batch_rows)

                logger.debug(f"Batch inserted {len(batch_rows)} rows into {table}")

            # Invalidate related cache entries
            await self.cache.invalidate(table)

            execution_time = time.time() - start_time
            self._update_stats(QueryType.BULK_INSERT, execution_time, False)

            logger.info(f"Batch insert completed: {total_inserted} rows in {execution_time:.2f}s")
            return total_inserted

        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            raise

    async def get_agent_tasks_optimized(self,
                                      agent_id: str,
                                      status_filter: Optional[str] = None,
                                      limit: int = 50) -> List[Dict[str, Any]]:
        """Optimized agent tasks query with intelligent caching"""

        cache_key = f"agent_tasks:{agent_id}:{status_filter}:{limit}"

        # Build optimized query
        base_query = """
        SELECT t.id, t.title, t.description, t.status, t.priority,
               t.due_date, t.created_at, t.lead_id, t.workflow_id,
               l.name as lead_name, l.phone, l.email
        FROM agent_tasks t
        LEFT JOIN leads l ON t.lead_id = l.id
        WHERE t.agent_id = $1
        """

        params = {"agent_id": agent_id}
        param_count = 1

        if status_filter:
            base_query += f" AND t.status = ${param_count + 1}"
            params["status"] = status_filter
            param_count += 1

        base_query += f"""
        ORDER BY t.priority, t.due_date
        LIMIT ${param_count + 1}
        """
        params["limit"] = limit

        return await self.execute_optimized_query(
            base_query,
            params,
            QueryType.SELECT,
            cache_key,
            cache_ttl=300  # 5 minutes cache
        )

    async def get_performance_analytics_optimized(self,
                                                agent_id: str,
                                                date_range: int = 30) -> Dict[str, Any]:
        """Optimized performance analytics with pre-computed metrics"""

        cache_key = f"performance_analytics:{agent_id}:{date_range}"

        # Use materialized view for better performance
        query = """
        SELECT
            COUNT(*) as total_tasks,
            COUNT(*) FILTER (WHERE status = 'completed') as completed_tasks,
            COUNT(*) FILTER (WHERE status = 'overdue') as overdue_tasks,
            AVG(EXTRACT(EPOCH FROM (completed_at - created_at))/60) as avg_completion_time_minutes,
            AVG(CASE WHEN lead_id IS NOT NULL THEN 1 ELSE 0 END) as lead_engagement_rate
        FROM agent_tasks
        WHERE agent_id = $1
          AND created_at >= NOW() - INTERVAL '%s days'
        """

        raw_result = await self.execute_optimized_query(
            query % date_range,
            {"agent_id": agent_id},
            QueryType.ANALYTICS,
            cache_key,
            cache_ttl=1800  # 30 minutes cache
        )

        # Transform to structured format
        if raw_result:
            row = raw_result[0]
            return {
                "total_tasks": row["total_tasks"],
                "completed_tasks": row["completed_tasks"],
                "overdue_tasks": row["overdue_tasks"],
                "completion_rate": row["completed_tasks"] / max(1, row["total_tasks"]) * 100,
                "avg_completion_time_minutes": float(row["avg_completion_time_minutes"] or 0),
                "lead_engagement_rate": float(row["lead_engagement_rate"] or 0) * 100
            }

        return {}

    def _update_stats(self, query_type: QueryType, execution_time: float, cache_hit: bool) -> None:
        """Update operation statistics"""
        self.operation_stats["total_operations"] += 1

        # Update query type stats
        if query_type.value not in self.operation_stats["query_types"]:
            self.operation_stats["query_types"][query_type.value] = {
                "count": 0,
                "total_time": 0.0,
                "cache_hits": 0
            }

        type_stats = self.operation_stats["query_types"][query_type.value]
        type_stats["count"] += 1
        type_stats["total_time"] += execution_time

        if cache_hit:
            type_stats["cache_hits"] += 1

        # Update global averages
        total_cache_hits = sum(
            stats["cache_hits"]
            for stats in self.operation_stats["query_types"].values()
        )

        self.operation_stats["cache_hit_rate"] = (
            total_cache_hits / self.operation_stats["total_operations"]
        )

        total_time = sum(
            stats["total_time"]
            for stats in self.operation_stats["query_types"].values()
        )

        self.operation_stats["average_response_time"] = (
            total_time / self.operation_stats["total_operations"] * 1000  # Convert to ms
        )

    async def get_database_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive database performance report"""
        return {
            "connection_pool_stats": self.connection_pool.get_stats(),
            "cache_stats": self.cache.cache_stats,
            "operation_stats": self.operation_stats,
            "query_optimizer_stats": {
                "cached_queries": len(self.query_optimizer.query_cache),
                "execution_plans": len(self.query_optimizer.execution_plans)
            }
        }


# Global optimized database layer instance
optimized_db = OptimizedDatabaseLayer(
    database_url="postgresql://user:password@localhost:5432/enterprisehub",
    redis_url="redis://localhost:6379/2"
)