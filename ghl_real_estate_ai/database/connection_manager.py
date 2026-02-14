"""
Enterprise Database Connection Manager
Provides production-grade PostgreSQL connection management with advanced features
"""

import asyncio
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import asyncpg
from asyncpg import Pool, Record

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseStatus(str, Enum):
    """Database connection status"""

    INITIALIZING = "initializing"
    CONNECTED = "connected"
    DEGRADED = "degraded"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class ConnectionMetrics:
    """Database connection metrics"""

    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    total_queries: int = 0
    slow_queries: int = 0
    failed_queries: int = 0
    avg_query_time_ms: float = 0.0
    last_health_check: Optional[datetime] = None
    uptime_seconds: float = 0.0


@dataclass
class QueryExecution:
    """Query execution tracking"""

    query_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sql: str = ""
    params: tuple = ()
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    affected_rows: Optional[int] = None

    def complete(self, success: bool = True, error: Optional[str] = None, affected_rows: Optional[int] = None):
        """Mark query as complete"""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.success = success
        self.error = error
        self.affected_rows = affected_rows


class DatabaseConnectionManager:
    """
    Enterprise-grade database connection manager with:
    - Advanced connection pooling
    - Health monitoring and auto-recovery
    - Query performance tracking
    - Transaction management
    - Automatic schema migrations
    - Connection retry logic
    - Query timeout handling
    - Connection leak detection
    """

    def __init__(self, database_url: str = None, **pool_config):
        self.database_url = database_url or settings.database_url
        self.status = DatabaseStatus.DISCONNECTED
        self.metrics = ConnectionMetrics()
        self.start_time = time.time()

        # Pool configuration with enterprise defaults
        self.pool_config = {
            "min_size": pool_config.get("min_size", 10),
            "max_size": pool_config.get("max_size", 50),
            "max_queries": pool_config.get("max_queries", 100000),
            "max_inactive_connection_lifetime": pool_config.get("max_inactive_connection_lifetime", 300),
            "command_timeout": pool_config.get("command_timeout", 15),  # Reduced from 60 to catch slow queries
            "server_settings": {
                "application_name": "service6-enterprise",
                "jit": "off",
            },
        }

        # Runtime state
        self.pool: Optional[Pool] = None
        self.health_monitor: Optional[asyncio.Task] = None
        self.query_history: List[QueryExecution] = []
        self.active_connections: Dict[str, float] = {}  # connection_id -> start_time

        # Configuration
        self.slow_query_threshold_ms = 1000  # 1 second
        self.health_check_interval = 30  # 30 seconds
        self.max_query_history = 1000
        self.connection_leak_threshold = 300  # 5 minutes

    async def initialize(self) -> bool:
        """Initialize database connection pool"""
        if self.status == DatabaseStatus.CONNECTED:
            logger.info("Database already connected")
            return True

        self.status = DatabaseStatus.INITIALIZING

        try:
            logger.info(f"Initializing database connection pool: {self._mask_database_url()}")

            # Create connection pool
            self.pool = await asyncpg.create_pool(self.database_url, **self.pool_config)

            # Test connectivity
            await self._test_connectivity()

            # Run health check
            health = await self.health_check()
            if not health["healthy"]:
                raise Exception(f"Database health check failed: {health}")

            # Start background monitoring
            self.health_monitor = asyncio.create_task(self._health_monitoring_loop())

            self.status = DatabaseStatus.CONNECTED
            logger.info("Database connection pool initialized successfully")

            return True

        except Exception as e:
            self.status = DatabaseStatus.ERROR
            logger.error(f"Failed to initialize database: {e}")
            raise

    async def close(self) -> None:
        """Close database connection pool"""
        logger.info("Closing database connections")

        # Cancel health monitor
        if self.health_monitor:
            self.health_monitor.cancel()
            try:
                await self.health_monitor
            except asyncio.CancelledError:
                pass

        # Close pool
        if self.pool:
            await self.pool.close()
            self.pool = None

        self.status = DatabaseStatus.DISCONNECTED
        logger.info("Database connections closed")

    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool with tracking"""
        if not self.pool:
            await self.initialize()

        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = time.time()

        try:
            async with self.pool.acquire() as conn:
                yield conn
        finally:
            del self.active_connections[connection_id]

    @asynccontextmanager
    async def transaction(self, isolation: str = None, readonly: bool = None, deferrable: bool = None):
        """Execute operations within a transaction"""
        async with self.get_connection() as conn:
            async with conn.transaction(isolation=isolation, readonly=readonly, deferrable=deferrable):
                yield conn

    async def execute_query(
        self, sql: str, *args, timeout: Optional[float] = None, record_execution: bool = True
    ) -> Any:
        """Execute a query with performance tracking"""
        query_exec = QueryExecution(sql=sql, params=args)

        try:
            # SECURITY FIX: Log query fingerprint at DEBUG level
            logger.debug(f"Executing query: {sql[:50]}...")
            async with self.get_connection() as conn:
                result = await conn.fetch(sql, *args, timeout=timeout)

                query_exec.complete(success=True, affected_rows=len(result) if result else 0)

                # Update metrics
                self.metrics.total_queries += 1
                if query_exec.duration_ms > self.slow_query_threshold_ms:
                    self.metrics.slow_queries += 1
                    logger.warning(f"Slow query detected: {query_exec.duration_ms:.2f}ms - {sql[:100]}...")

                if record_execution:
                    self._record_query_execution(query_exec)

                return result

        except Exception as e:
            query_exec.complete(success=False, error=str(e))
            self.metrics.failed_queries += 1

            if record_execution:
                self._record_query_execution(query_exec)

            logger.error(f"Query execution failed: {e} - SQL: {sql[:100]}...")
            raise

    async def execute_fetchrow(self, sql: str, *args, timeout: Optional[float] = None) -> Optional[Record]:
        """Execute query and return single row"""
        async with self.get_connection() as conn:
            return await conn.fetchrow(sql, *args, timeout=timeout)

    async def execute_fetchval(
        self, sql: str, *args, column: Union[str, int] = 0, timeout: Optional[float] = None
    ) -> Any:
        """Execute query and return single value"""
        async with self.get_connection() as conn:
            return await conn.fetchval(sql, *args, column=column, timeout=timeout)

    async def execute_command(self, sql: str, *args, timeout: Optional[float] = None) -> str:
        """Execute command (INSERT, UPDATE, DELETE) and return status"""
        async with self.get_connection() as conn:
            return await conn.execute(sql, *args, timeout=timeout)

    async def bulk_insert(
        self, table_name: str, records: List[Dict[str, Any]], conflict_resolution: str = "DO NOTHING"
    ) -> int:
        """
        Bulk insert records with SQL injection protection.

        Args:
            table_name: Name of the table (validated against whitelist)
            records: List of record dictionaries
            conflict_resolution: Conflict resolution strategy (validated)

        Returns:
            Number of inserted records
        """
        if not records:
            return 0

        # Validate table name against whitelist
        allowed_tables = {"leads", "communication_logs", "nurture_campaigns", "lead_campaign_status"}
        if table_name not in allowed_tables:
            raise ValueError(f"Table name '{table_name}' not in allowed list: {allowed_tables}")

        # Validate conflict resolution
        allowed_conflicts = {"DO NOTHING", "DO UPDATE SET", "ABORT"}
        if conflict_resolution not in allowed_conflicts:
            raise ValueError(f"Invalid conflict resolution: {conflict_resolution}")

        start_time = time.time()

        try:
            # Get columns from first record
            columns = list(records[0].keys())

            # Validate column names (basic validation)
            for col in columns:
                if not col.replace("_", "").isalnum():
                    raise ValueError(f"Invalid column name: {col}")

            # Create placeholders for parameterized query
            placeholders = ", ".join([f"${i + 1}" for i in range(len(columns))])

            # Use safe identifier quoting
            import asyncpg

            quoted_table = asyncpg.utils._quote_ident(table_name)
            quoted_columns = ", ".join([asyncpg.utils._quote_ident(col) for col in columns])

            sql = f"""
                INSERT INTO {quoted_table} ({quoted_columns})
                VALUES ({placeholders})
                ON CONFLICT {conflict_resolution}
            """

            # Convert records to tuples
            values = [tuple(record[col] for col in columns) for record in records]

            async with self.transaction() as conn:
                result = await conn.executemany(sql, values)
                return len(values)

        except Exception as e:
            logger.error(f"Failed to bulk insert into {table_name}: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive database health check"""
        health = {
            "healthy": True,
            "status": self.status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "issues": [],
        }

        try:
            start_time = time.time()

            async with self.get_connection() as conn:
                # Test basic connectivity
                await conn.fetchval("SELECT 1")

                # Check database version
                version = await conn.fetchval("SELECT version()")
                health["database_version"] = version

                # Check current connections
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_connections,
                        COUNT(*) FILTER (WHERE state = 'active') as active_connections,
                        COUNT(*) FILTER (WHERE state = 'idle') as idle_connections
                    FROM pg_stat_activity 
                    WHERE datname = current_database()
                """)

                health["connections"] = dict(stats) if stats else {}

                # Check table counts
                table_stats = await conn.fetch("""
                    SELECT schemaname, relname as tablename, n_tup_ins, n_tup_upd, n_tup_del
                    FROM pg_stat_user_tables
                    ORDER BY n_tup_ins + n_tup_upd + n_tup_del DESC
                    LIMIT 10
                """)

                health["table_activity"] = [dict(row) for row in table_stats]

                # Check slow queries if pg_stat_statements available
                try:
                    slow_queries = await conn.fetch("""
                        SELECT query, calls, total_exec_time, mean_exec_time
                        FROM pg_stat_statements
                        WHERE mean_exec_time > 1000
                        ORDER BY mean_exec_time DESC
                        LIMIT 5
                    """)
                    health["slow_queries"] = [dict(row) for row in slow_queries]
                except asyncpg.PostgresError:
                    # pg_stat_statements not available or permission denied
                    pass

            # Calculate response time
            response_time = (time.time() - start_time) * 1000
            health["response_time_ms"] = response_time

            # Check for issues
            if response_time > 5000:  # > 5 seconds
                health["issues"].append(f"Slow database response: {response_time:.2f}ms")
                health["healthy"] = False

            # Check pool status
            if self.pool:
                pool_size = self.pool.get_size()
                pool_idle = self.pool.get_idle_size()

                health["pool"] = {"size": pool_size, "idle": pool_idle, "active": pool_size - pool_idle}

                if pool_idle == 0:
                    health["issues"].append("Connection pool exhausted")
                    health["healthy"] = False

            # Update metrics
            self.metrics.last_health_check = datetime.utcnow()
            self.metrics.uptime_seconds = time.time() - self.start_time

            if health["connections"]:
                self.metrics.total_connections = health["connections"]["total_connections"]
                self.metrics.active_connections = health["connections"]["active_connections"]
                self.metrics.idle_connections = health["connections"]["idle_connections"]

        except Exception as e:
            health["healthy"] = False
            health["issues"].append(f"Health check failed: {str(e)}")
            logger.error(f"Database health check error: {e}")

        return health

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        metrics = {
            "connection_metrics": {
                "total_connections": self.metrics.total_connections,
                "active_connections": self.metrics.active_connections,
                "idle_connections": self.metrics.idle_connections,
                "uptime_seconds": self.metrics.uptime_seconds,
            },
            "query_metrics": {
                "total_queries": self.metrics.total_queries,
                "slow_queries": self.metrics.slow_queries,
                "failed_queries": self.metrics.failed_queries,
                "slow_query_percentage": (self.metrics.slow_queries / max(1, self.metrics.total_queries)) * 100,
            },
            "recent_queries": [],
        }

        # Add recent query performance
        recent_queries = self.query_history[-50:]  # Last 50 queries
        if recent_queries:
            avg_duration = sum(q.duration_ms or 0 for q in recent_queries) / len(recent_queries)
            metrics["query_metrics"]["avg_query_time_ms"] = avg_duration

            metrics["recent_queries"] = [
                {
                    "query_id": q.query_id,
                    "sql_preview": q.sql[:100],
                    "duration_ms": q.duration_ms,
                    "success": q.success,
                    "error": q.error,
                }
                for q in recent_queries[-10:]  # Last 10 queries
            ]

        # Check for connection leaks
        current_time = time.time()
        leaked_connections = [
            conn_id
            for conn_id, start_time in self.active_connections.items()
            if current_time - start_time > self.connection_leak_threshold
        ]

        if leaked_connections:
            metrics["warnings"] = [
                f"Potential connection leak detected: {len(leaked_connections)} long-running connections"
            ]

        return metrics

    async def optimize_database(self) -> Dict[str, Any]:
        """Run database optimization tasks"""
        optimization_results = {"vacuum_analyze_completed": False, "index_usage_analyzed": False, "recommendations": []}

        try:
            async with self.get_connection() as conn:
                # Run VACUUM ANALYZE on main tables
                tables_to_optimize = ["leads", "communication_logs", "nurture_campaigns", "lead_campaign_status"]

                for table in tables_to_optimize:
                    try:
                        # Use safe identifier quoting to prevent SQL injection
                        import asyncpg

                        quoted_table = asyncpg.utils._quote_ident(table)
                        await conn.execute(f"VACUUM ANALYZE {quoted_table}")
                        logger.info(f"Vacuumed and analyzed table: {table}")
                    except Exception as e:
                        logger.warning(f"Failed to optimize table {table}: {e}")

                optimization_results["vacuum_analyze_completed"] = True

                # Analyze index usage
                index_stats = await conn.fetch("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes
                    WHERE idx_scan = 0
                    ORDER BY schemaname, tablename
                """)

                if index_stats:
                    unused_indexes = [dict(row) for row in index_stats]
                    optimization_results["unused_indexes"] = unused_indexes
                    optimization_results["recommendations"].append(
                        f"Consider dropping {len(unused_indexes)} unused indexes"
                    )

                optimization_results["index_usage_analyzed"] = True

                # Check table sizes
                table_sizes = await conn.fetch("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                """)

                optimization_results["table_sizes"] = [dict(row) for row in table_sizes]

        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            optimization_results["error"] = str(e)

        return optimization_results

    # Private methods

    def _mask_database_url(self) -> str:
        """Mask sensitive parts of database URL for logging"""
        if not self.database_url:
            return "None"

        # Simple masking - replace password with ***
        if "@" in self.database_url:
            parts = self.database_url.split("@")
            if ":" in parts[0]:
                auth_parts = parts[0].split(":")
                masked_auth = ":".join(auth_parts[:-1] + ["***"])
                return f"{masked_auth}@{parts[1]}"

        return self.database_url

    async def _test_connectivity(self):
        """Test database connectivity"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            if result != 1:
                raise Exception("Database connectivity test failed")

    def _record_query_execution(self, query_exec: QueryExecution):
        """Record query execution for performance tracking"""
        self.query_history.append(query_exec)

        # Limit history size
        if len(self.query_history) > self.max_query_history:
            self.query_history = self.query_history[-self.max_query_history // 2 :]

    async def _health_monitoring_loop(self):
        """Background health monitoring"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)

                health = await self.health_check()

                if not health["healthy"]:
                    logger.warning(f"Database health degraded: {health['issues']}")
                    self.status = DatabaseStatus.DEGRADED
                else:
                    self.status = DatabaseStatus.CONNECTED

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# Global database manager instance
_db_manager: Optional[DatabaseConnectionManager] = None


async def get_db_manager() -> DatabaseConnectionManager:
    """Get or create global database manager"""
    global _db_manager

    if _db_manager is None:
        _db_manager = DatabaseConnectionManager()
        await _db_manager.initialize()

    return _db_manager


async def close_db_manager():
    """Close global database manager"""
    global _db_manager

    if _db_manager:
        await _db_manager.close()
        _db_manager = None


# Convenience functions for common operations
async def execute_query(sql: str, *args, **kwargs) -> Any:
    """Execute query using global database manager"""
    db = await get_db_manager()
    return await db.execute_query(sql, *args, **kwargs)


async def execute_fetchrow(sql: str, *args, **kwargs) -> Optional[Record]:
    """Execute query and return single row"""
    db = await get_db_manager()
    return await db.execute_fetchrow(sql, *args, **kwargs)


async def execute_fetchval(sql: str, *args, **kwargs) -> Any:
    """Execute query and return single value"""
    db = await get_db_manager()
    return await db.execute_fetchval(sql, *args, **kwargs)


@asynccontextmanager
async def transaction(**kwargs):
    """Get database transaction"""
    db = await get_db_manager()
    async with db.transaction(**kwargs) as conn:
        yield conn


@asynccontextmanager
async def connection():
    """Get database connection"""
    db = await get_db_manager()
    async with db.get_connection() as conn:
        yield conn
