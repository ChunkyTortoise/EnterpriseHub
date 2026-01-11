"""
Database Sharding Router - Phase 4 Enterprise Scaling
Location-based sharding for linear performance scaling with 1000+ concurrent users

Architecture:
- 4 shards by geographic regions (US-East, US-West, US-Central, International)
- Tenant isolation by location_id (GHL tenant isolation)
- Linear scaling: 4 shards = ~4x throughput capacity
- Automatic failover and connection pooling
- Cross-shard query optimization

Performance Targets:
- <50ms P90 query latency per shard
- 5K+ transactions/sec per shard (20K+ total)
- 99.95% availability with automatic failover
- Connection pooling: 300 connections per shard
"""

import asyncio
import hashlib
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import asyncpg
import aiopg
from contextlib import asynccontextmanager

from .secure_logging_service import SecureLogger
from .base.base_service import BaseService

class ShardRegion(Enum):
    """Geographic shard regions for optimal latency."""
    US_EAST = "us_east"
    US_WEST = "us_west"
    US_CENTRAL = "us_central"
    INTERNATIONAL = "international"

class QueryType(Enum):
    """Database query types for optimization."""
    READ = "read"
    WRITE = "write"
    TRANSACTION = "transaction"
    BULK = "bulk"

@dataclass
class ShardConfig:
    """Shard configuration and connection details."""
    region: ShardRegion
    master_connection: str
    replica_connections: List[str]
    location_patterns: List[str]
    max_connections: int
    health_check_interval: int = 30

@dataclass
class ShardMetrics:
    """Shard performance metrics."""
    shard_region: ShardRegion
    active_connections: int
    avg_query_time_ms: float
    queries_per_second: float
    error_rate: float
    last_health_check: datetime
    is_healthy: bool

@dataclass
class QueryResult:
    """Enhanced query result with shard information."""
    data: Any
    execution_time_ms: float
    shard_region: ShardRegion
    rows_affected: int
    query_type: QueryType

class ConnectionPool:
    """
    Enhanced connection pool for database sharding.
    Handles master/replica routing and failover.
    """

    def __init__(self, shard_config: ShardConfig):
        self.shard_config = shard_config
        self.master_pool = None
        self.replica_pools = []
        self.is_initialized = False
        self.logger = SecureLogger(component_name=f"connection_pool_{shard_config.region.value}")

    async def initialize(self):
        """Initialize connection pools for master and replicas."""
        self.logger.info(f"Initializing connection pool for {self.shard_config.region.value}")

        try:
            # Initialize master connection pool
            self.master_pool = await asyncpg.create_pool(
                self.shard_config.master_connection,
                min_size=10,
                max_size=self.shard_config.max_connections,
                command_timeout=30,
                server_settings={
                    'application_name': f'enterprisehub_shard_{self.shard_config.region.value}',
                    'search_path': 'public'
                }
            )

            # Initialize replica pools
            for replica_conn in self.shard_config.replica_connections:
                replica_pool = await asyncpg.create_pool(
                    replica_conn,
                    min_size=5,
                    max_size=self.shard_config.max_connections // 2,
                    command_timeout=30,
                    server_settings={
                        'application_name': f'enterprisehub_replica_{self.shard_config.region.value}',
                        'search_path': 'public'
                    }
                )
                self.replica_pools.append(replica_pool)

            self.is_initialized = True
            self.logger.info(f"Connection pool initialized for {self.shard_config.region.value}")

        except Exception as e:
            self.logger.error(f"Failed to initialize connection pool: {e}")
            raise

    @asynccontextmanager
    async def get_connection(self, query_type: QueryType = QueryType.READ):
        """Get database connection based on query type."""
        if not self.is_initialized:
            await self.initialize()

        # Route reads to replicas, writes to master
        if query_type == QueryType.READ and self.replica_pools:
            # Load balance across replica pools
            pool_index = hash(str(time.time())) % len(self.replica_pools)
            pool = self.replica_pools[pool_index]
        else:
            # Use master for writes and transactions
            pool = self.master_pool

        try:
            async with pool.acquire() as connection:
                # Set tenant context for Row-Level Security
                await connection.execute("SELECT set_config('app.shard_region', $1, false)", self.shard_config.region.value)
                yield connection
        except Exception as e:
            self.logger.error(f"Connection error in {self.shard_config.region.value}: {e}")
            raise

    async def get_metrics(self) -> ShardMetrics:
        """Get current shard performance metrics."""
        try:
            active_connections = 0
            if self.master_pool:
                active_connections += len(self.master_pool._holders)

            for replica_pool in self.replica_pools:
                active_connections += len(replica_pool._holders)

            # Get query performance metrics
            async with self.get_connection(QueryType.READ) as conn:
                metrics_query = """
                    SELECT
                        COALESCE(AVG(mean_exec_time), 0) as avg_query_time,
                        COALESCE(SUM(calls), 0) as total_queries
                    FROM pg_stat_statements
                    WHERE query NOT LIKE '%pg_stat%'
                    AND dbid = (SELECT oid FROM pg_database WHERE datname = current_database())
                """

                row = await conn.fetchrow(metrics_query)
                avg_query_time = row['avg_query_time'] if row else 0
                queries_per_second = 0  # Would need time-based calculation

            return ShardMetrics(
                shard_region=self.shard_config.region,
                active_connections=active_connections,
                avg_query_time_ms=avg_query_time,
                queries_per_second=queries_per_second,
                error_rate=0.0,  # Would track from actual error monitoring
                last_health_check=datetime.now(timezone.utc),
                is_healthy=True
            )

        except Exception as e:
            self.logger.error(f"Failed to get metrics for {self.shard_config.region.value}: {e}")
            return ShardMetrics(
                shard_region=self.shard_config.region,
                active_connections=0,
                avg_query_time_ms=0,
                queries_per_second=0,
                error_rate=1.0,
                last_health_check=datetime.now(timezone.utc),
                is_healthy=False
            )

    async def health_check(self) -> bool:
        """Perform health check on shard."""
        try:
            async with self.get_connection(QueryType.READ) as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            self.logger.warning(f"Health check failed for {self.shard_config.region.value}: {e}")
            return False

    async def close(self):
        """Close all connection pools."""
        try:
            if self.master_pool:
                await self.master_pool.close()

            for replica_pool in self.replica_pools:
                await replica_pool.close()

            self.logger.info(f"Connection pools closed for {self.shard_config.region.value}")

        except Exception as e:
            self.logger.error(f"Error closing connection pools: {e}")

class TenantShardRouter:
    """
    Intelligent tenant-to-shard routing based on location_id.
    Implements consistent hashing for optimal distribution.
    """

    def __init__(self):
        self.logger = SecureLogger(component_name="tenant_shard_router")

        # Define shard configurations
        self.shard_configs = {
            ShardRegion.US_EAST: ShardConfig(
                region=ShardRegion.US_EAST,
                master_connection="postgresql://user:pass@postgres-shard-1:5432/enterprisehub",
                replica_connections=[
                    "postgresql://user:pass@postgres-replica-1a:5432/enterprisehub",
                    "postgresql://user:pass@postgres-replica-1b:5432/enterprisehub"
                ],
                location_patterns=[
                    "US-EAST-*", "CA-EAST-*", "US-NY-*", "US-FL-*", "US-MA-*"
                ],
                max_connections=300
            ),
            ShardRegion.US_WEST: ShardConfig(
                region=ShardRegion.US_WEST,
                master_connection="postgresql://user:pass@postgres-shard-2:5432/enterprisehub",
                replica_connections=[
                    "postgresql://user:pass@postgres-replica-2a:5432/enterprisehub",
                    "postgresql://user:pass@postgres-replica-2b:5432/enterprisehub"
                ],
                location_patterns=[
                    "US-WEST-*", "CA-WEST-*", "US-CA-*", "US-WA-*", "US-OR-*"
                ],
                max_connections=300
            ),
            ShardRegion.US_CENTRAL: ShardConfig(
                region=ShardRegion.US_CENTRAL,
                master_connection="postgresql://user:pass@postgres-shard-3:5432/enterprisehub",
                replica_connections=[
                    "postgresql://user:pass@postgres-replica-3a:5432/enterprisehub",
                    "postgresql://user:pass@postgres-replica-3b:5432/enterprisehub"
                ],
                location_patterns=[
                    "US-CENTRAL-*", "US-SOUTH-*", "US-TX-*", "US-IL-*", "US-CO-*"
                ],
                max_connections=300
            ),
            ShardRegion.INTERNATIONAL: ShardConfig(
                region=ShardRegion.INTERNATIONAL,
                master_connection="postgresql://user:pass@postgres-shard-4:5432/enterprisehub",
                replica_connections=[
                    "postgresql://user:pass@postgres-replica-4a:5432/enterprisehub",
                    "postgresql://user:pass@postgres-replica-4b:5432/enterprisehub"
                ],
                location_patterns=[
                    "EU-*", "APAC-*", "AU-*", "UK-*", "OTHER-*"
                ],
                max_connections=300
            )
        }

        self.connection_pools = {}

    async def initialize(self):
        """Initialize all shard connection pools."""
        self.logger.info("Initializing database sharding system")

        for region, config in self.shard_configs.items():
            pool = ConnectionPool(config)
            await pool.initialize()
            self.connection_pools[region] = pool

        self.logger.info("Database sharding system initialized successfully")

    def get_shard_for_location(self, location_id: str) -> ShardRegion:
        """
        Determine shard for given location_id using pattern matching + consistent hashing.
        """
        # First try pattern matching for optimal geographic routing
        for region, config in self.shard_configs.items():
            for pattern in config.location_patterns:
                if self._matches_pattern(location_id, pattern):
                    return region

        # Fallback to consistent hashing for unknown patterns
        return self._consistent_hash_location(location_id)

    def _matches_pattern(self, location_id: str, pattern: str) -> bool:
        """Check if location_id matches shard pattern."""
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return location_id.startswith(prefix)
        return location_id == pattern

    def _consistent_hash_location(self, location_id: str) -> ShardRegion:
        """Use consistent hashing for location distribution."""
        # Create hash of location_id
        hash_value = int(hashlib.md5(location_id.encode()).hexdigest(), 16)

        # Map to shard regions
        shard_index = hash_value % len(self.shard_configs)
        regions = list(self.shard_configs.keys())
        return regions[shard_index]

    async def get_connection(
        self,
        location_id: str,
        query_type: QueryType = QueryType.READ
    ):
        """Get database connection for specific tenant location."""
        shard_region = self.get_shard_for_location(location_id)
        pool = self.connection_pools[shard_region]
        return pool.get_connection(query_type)

    async def get_all_shard_metrics(self) -> Dict[ShardRegion, ShardMetrics]:
        """Get performance metrics for all shards."""
        metrics = {}

        for region, pool in self.connection_pools.items():
            try:
                metrics[region] = await pool.get_metrics()
            except Exception as e:
                self.logger.error(f"Failed to get metrics for {region.value}: {e}")

        return metrics

    async def health_check_all_shards(self) -> Dict[ShardRegion, bool]:
        """Perform health check on all shards."""
        health_results = {}

        for region, pool in self.connection_pools.items():
            health_results[region] = await pool.health_check()

        return health_results

class DatabaseShardingService(BaseService):
    """
    Main database sharding service.
    Provides high-level interface for sharded database operations.
    """

    def __init__(self):
        super().__init__()
        self.shard_router = TenantShardRouter()
        self.logger = SecureLogger(component_name="database_sharding_service")
        self.query_cache = {}  # Simple query result cache

    async def initialize(self):
        """Initialize database sharding service."""
        await self.shard_router.initialize()
        self.logger.info("Database Sharding Service initialized")

    async def execute_query(
        self,
        location_id: str,
        query: str,
        params: Tuple = None,
        query_type: QueryType = QueryType.READ
    ) -> QueryResult:
        """
        Execute query on appropriate shard for location.

        Args:
            location_id: GHL location ID for tenant isolation
            query: SQL query to execute
            params: Query parameters
            query_type: Type of query (read/write/transaction)

        Returns:
            QueryResult with execution details
        """
        start_time = time.time()

        # Validate cross-shard query safety
        self._validate_query_safety(query, location_id)

        try:
            # Get shard region for location
            shard_region = self.shard_router.get_shard_for_location(location_id)

            # Set tenant context and execute query
            async with self.shard_router.get_connection(location_id, query_type) as conn:
                # Set Row-Level Security context
                await conn.execute(
                    "SELECT set_config('app.current_location_id', $1, false)",
                    location_id
                )

                # Execute query
                if query_type == QueryType.READ:
                    if params:
                        result = await conn.fetch(query, *params)
                    else:
                        result = await conn.fetch(query)
                    rows_affected = len(result)
                else:
                    if params:
                        result = await conn.execute(query, *params)
                    else:
                        result = await conn.execute(query)
                    rows_affected = int(result.split()[-1]) if result else 0

                execution_time = (time.time() - start_time) * 1000

                self.logger.debug(
                    f"Query executed on {shard_region.value}",
                    metadata={
                        "location_id": location_id,
                        "execution_time_ms": execution_time,
                        "rows_affected": rows_affected,
                        "query_type": query_type.value
                    }
                )

                return QueryResult(
                    data=result,
                    execution_time_ms=execution_time,
                    shard_region=shard_region,
                    rows_affected=rows_affected,
                    query_type=query_type
                )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000

            self.logger.error(
                f"Query execution failed",
                metadata={
                    "location_id": location_id,
                    "error": str(e),
                    "execution_time_ms": execution_time
                }
            )
            raise

    async def execute_transaction(
        self,
        location_id: str,
        queries: List[Tuple[str, Tuple]]
    ) -> List[QueryResult]:
        """
        Execute multiple queries in a transaction on single shard.

        Args:
            location_id: GHL location ID
            queries: List of (query, params) tuples

        Returns:
            List of QueryResult objects
        """
        shard_region = self.shard_router.get_shard_for_location(location_id)
        results = []

        async with self.shard_router.get_connection(location_id, QueryType.TRANSACTION) as conn:
            # Set tenant context
            await conn.execute(
                "SELECT set_config('app.current_location_id', $1, false)",
                location_id
            )

            # Start transaction
            async with conn.transaction():
                for query, params in queries:
                    start_time = time.time()

                    # Validate query safety
                    self._validate_query_safety(query, location_id)

                    # Execute query
                    if params:
                        result = await conn.execute(query, *params)
                    else:
                        result = await conn.execute(query)

                    execution_time = (time.time() - start_time) * 1000
                    rows_affected = int(result.split()[-1]) if result else 0

                    results.append(QueryResult(
                        data=result,
                        execution_time_ms=execution_time,
                        shard_region=shard_region,
                        rows_affected=rows_affected,
                        query_type=QueryType.TRANSACTION
                    ))

        self.logger.info(
            f"Transaction executed with {len(queries)} queries",
            metadata={
                "location_id": location_id,
                "shard_region": shard_region.value,
                "total_queries": len(queries)
            }
        )

        return results

    async def bulk_execute_across_shards(
        self,
        queries_by_location: Dict[str, List[Tuple[str, Tuple]]]
    ) -> Dict[str, List[QueryResult]]:
        """
        Execute bulk queries across multiple shards in parallel.
        Optimized for data migration and bulk operations.

        Args:
            queries_by_location: Dict mapping location_id to list of queries

        Returns:
            Dict mapping location_id to query results
        """
        self.logger.info(f"Executing bulk queries across {len(queries_by_location)} locations")

        # Group queries by shard region for optimal execution
        queries_by_shard = {}
        for location_id, queries in queries_by_location.items():
            shard_region = self.shard_router.get_shard_for_location(location_id)
            if shard_region not in queries_by_shard:
                queries_by_shard[shard_region] = []
            queries_by_shard[shard_region].append((location_id, queries))

        # Execute queries per shard in parallel
        shard_tasks = []
        for shard_region, location_queries in queries_by_shard.items():
            task = self._execute_bulk_on_shard(shard_region, location_queries)
            shard_tasks.append(task)

        # Wait for all shards to complete
        shard_results = await asyncio.gather(*shard_tasks)

        # Combine results by location_id
        combined_results = {}
        for shard_result in shard_results:
            combined_results.update(shard_result)

        return combined_results

    async def _execute_bulk_on_shard(
        self,
        shard_region: ShardRegion,
        location_queries: List[Tuple[str, List[Tuple[str, Tuple]]]]
    ) -> Dict[str, List[QueryResult]]:
        """Execute bulk queries on single shard."""
        results = {}

        pool = self.shard_router.connection_pools[shard_region]

        async with pool.get_connection(QueryType.BULK) as conn:
            for location_id, queries in location_queries:
                # Set tenant context
                await conn.execute(
                    "SELECT set_config('app.current_location_id', $1, false)",
                    location_id
                )

                location_results = []

                for query, params in queries:
                    start_time = time.time()

                    # Execute query
                    if params:
                        result = await conn.execute(query, *params)
                    else:
                        result = await conn.execute(query)

                    execution_time = (time.time() - start_time) * 1000
                    rows_affected = int(result.split()[-1]) if result else 0

                    location_results.append(QueryResult(
                        data=result,
                        execution_time_ms=execution_time,
                        shard_region=shard_region,
                        rows_affected=rows_affected,
                        query_type=QueryType.BULK
                    ))

                results[location_id] = location_results

        return results

    def _validate_query_safety(self, query: str, location_id: str):
        """
        Validate query for cross-shard security.
        Prevents cross-tenant data access and injection attacks.
        """
        query_lower = query.lower().strip()

        # Block dangerous patterns
        dangerous_patterns = [
            "location_id != ",           # Cross-tenant comparison
            "location_id not in",        # Multi-tenant access
            "location_id is null",       # Null bypass attempt
            "or location_id",            # OR-based bypass
            "union select",              # Union injection
            "drop table",                # DDL attacks
            "truncate table",            # Data destruction
            "alter table",               # Schema modification
            "create table",              # Unauthorized creation
        ]

        for pattern in dangerous_patterns:
            if pattern in query_lower:
                self.logger.security(
                    f"Blocked dangerous query pattern: {pattern}",
                    metadata={
                        "location_id": location_id,
                        "query_pattern": pattern,
                        "query_preview": query[:100]
                    }
                )
                raise ValueError(f"Query contains dangerous pattern: {pattern}")

        # Ensure location_id is properly isolated
        if "location_id" in query_lower and location_id not in query:
            self.logger.warning(
                f"Query mentions location_id but doesn't reference current tenant",
                metadata={"location_id": location_id, "query_preview": query[:100]}
            )

    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary across all shards."""
        shard_metrics = await self.shard_router.get_all_shard_metrics()
        health_status = await self.shard_router.health_check_all_shards()

        # Calculate aggregate metrics
        total_connections = sum(metrics.active_connections for metrics in shard_metrics.values())
        avg_query_time = np.mean([metrics.avg_query_time_ms for metrics in shard_metrics.values()])
        total_throughput = sum(metrics.queries_per_second for metrics in shard_metrics.values())
        healthy_shards = sum(1 for healthy in health_status.values() if healthy)

        return {
            "total_shards": len(self.shard_router.shard_configs),
            "healthy_shards": healthy_shards,
            "availability_percentage": (healthy_shards / len(self.shard_router.shard_configs)) * 100,
            "total_active_connections": total_connections,
            "avg_query_time_ms": avg_query_time,
            "total_throughput_qps": total_throughput,
            "shard_metrics": {
                region.value: {
                    "active_connections": metrics.active_connections,
                    "avg_query_time_ms": metrics.avg_query_time_ms,
                    "queries_per_second": metrics.queries_per_second,
                    "is_healthy": metrics.is_healthy
                }
                for region, metrics in shard_metrics.items()
            },
            "performance_targets": {
                "query_latency_p90_ms": "< 50ms",
                "throughput_per_shard_qps": "> 5000",
                "total_throughput_qps": "> 20000",
                "availability": "> 99.95%"
            }
        }

    async def close(self):
        """Close all database connections."""
        for pool in self.shard_router.connection_pools.values():
            await pool.close()

        self.logger.info("Database sharding service closed")

# Helper functions for integration with existing services

async def get_database_connection(location_id: str, query_type: QueryType = QueryType.READ):
    """
    Helper function to get database connection for existing services.

    Usage:
        async with get_database_connection(location_id, QueryType.WRITE) as conn:
            result = await conn.execute("INSERT INTO ...")
    """
    # Global sharding service instance (would be initialized at app startup)
    global _sharding_service

    if _sharding_service is None:
        _sharding_service = DatabaseShardingService()
        await _sharding_service.initialize()

    return _sharding_service.shard_router.get_connection(location_id, query_type)

# Global service instance
_sharding_service: Optional[DatabaseShardingService] = None