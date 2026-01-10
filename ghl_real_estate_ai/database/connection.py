"""
Database Connection Management for Multi-Tenant Continuous Memory System.

Provides PostgreSQL connection pooling with:
- Automatic connection management
- Health monitoring
- Graceful fallback handling
- Performance optimization
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import logging

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseConnectionError(Exception):
    """Database connection related errors."""
    pass


class DatabaseHealthStatus:
    """Database health monitoring."""

    def __init__(self):
        self.is_healthy = False
        self.last_check = None
        self.consecutive_failures = 0
        self.total_connections = 0
        self.active_connections = 0
        self.avg_query_time_ms = 0.0
        self.error_rate = 0.0
        self.last_error = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for monitoring."""
        return {
            "is_healthy": self.is_healthy,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "consecutive_failures": self.consecutive_failures,
            "total_connections": self.total_connections,
            "active_connections": self.active_connections,
            "avg_query_time_ms": self.avg_query_time_ms,
            "error_rate": self.error_rate,
            "last_error": str(self.last_error) if self.last_error else None
        }


class EnhancedDatabasePool:
    """
    Enhanced PostgreSQL connection pool with monitoring and health checks.
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        min_size: int = 5,
        max_size: int = 20,
        command_timeout: int = 60,
        health_check_interval: int = 30
    ):
        """
        Initialize database pool.

        Args:
            database_url: PostgreSQL connection URL
            min_size: Minimum pool size
            max_size: Maximum pool size
            command_timeout: Query timeout in seconds
            health_check_interval: Health check interval in seconds
        """
        self.database_url = database_url or getattr(settings, 'database_url', None)
        self.min_size = min_size
        self.max_size = max_size
        self.command_timeout = command_timeout
        self.health_check_interval = health_check_interval

        # Connection pool
        self.pool = None
        self.initialized = False

        # Health monitoring
        self.health = DatabaseHealthStatus()
        self._health_check_task = None
        self._query_metrics = []
        self._max_metrics = 1000  # Keep last 1000 queries for metrics

        # Performance metrics
        self.metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "avg_response_time_ms": 0.0,
            "peak_response_time_ms": 0.0,
            "pool_exhaustions": 0
        }

        logger.info(f"Database pool initialized - Min: {min_size}, Max: {max_size}")

    async def initialize(self) -> bool:
        """
        Initialize database connection pool.

        Returns:
            True if successful, False otherwise
        """
        if self.initialized:
            return True

        if not self.database_url:
            logger.warning("No database URL configured, database pool disabled")
            return False

        try:
            import asyncpg

            # Create connection pool
            self.pool = await asyncpg.create_pool(
                dsn=self.database_url,
                min_size=self.min_size,
                max_size=self.max_size,
                command_timeout=self.command_timeout,
                server_settings={
                    'application_name': 'enterprisehub_memory_system',
                    'jit': 'off'  # Disable JIT for faster startup
                }
            )

            # Verify connection with health check
            if await self._perform_health_check():
                self.initialized = True
                self.health.is_healthy = True
                logger.info("Database connection pool initialized successfully")

                # Start background health monitoring
                self._health_check_task = asyncio.create_task(self._background_health_monitor())
                return True
            else:
                logger.error("Database health check failed during initialization")
                await self.close()
                return False

        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            self.health.last_error = e
            self.health.consecutive_failures += 1
            return False

    async def close(self):
        """Close database connection pool."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        if self.pool:
            await self.pool.close()
            self.pool = None

        self.initialized = False
        logger.info("Database connection pool closed")

    @asynccontextmanager
    async def acquire(self):
        """
        Acquire database connection from pool.

        Usage:
            async with db_pool.acquire() as conn:
                result = await conn.fetch("SELECT * FROM table")
        """
        if not self.initialized:
            if not await self.initialize():
                raise DatabaseConnectionError("Database pool not initialized")

        connection = None
        start_time = time.time()

        try:
            connection = await asyncio.wait_for(
                self.pool.acquire(),
                timeout=30.0  # 30 second timeout to acquire connection
            )

            self.health.active_connections += 1
            yield connection

        except asyncio.TimeoutError:
            self.metrics["pool_exhaustions"] += 1
            logger.error("Database pool exhausted - unable to acquire connection")
            raise DatabaseConnectionError("Database pool exhausted")

        except Exception as e:
            logger.error(f"Database connection error: {e}")
            self.health.consecutive_failures += 1
            self.health.last_error = e
            raise DatabaseConnectionError(f"Database error: {e}")

        finally:
            if connection:
                try:
                    await self.pool.release(connection)
                    self.health.active_connections -= 1
                except Exception as e:
                    logger.error(f"Error releasing connection: {e}")

            # Record metrics
            query_time = (time.time() - start_time) * 1000
            self._record_query_metrics(query_time)

    async def execute(self, query: str, *args) -> str:
        """Execute a query and return status."""
        start_time = time.time()

        try:
            async with self.acquire() as conn:
                result = await conn.execute(query, *args)
                self._record_successful_query(time.time() - start_time)
                return result

        except Exception as e:
            self._record_failed_query(time.time() - start_time)
            raise

    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch multiple rows."""
        start_time = time.time()

        try:
            async with self.acquire() as conn:
                rows = await conn.fetch(query, *args)
                self._record_successful_query(time.time() - start_time)
                return [dict(row) for row in rows]

        except Exception as e:
            self._record_failed_query(time.time() - start_time)
            raise

    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch single row."""
        start_time = time.time()

        try:
            async with self.acquire() as conn:
                row = await conn.fetchrow(query, *args)
                self._record_successful_query(time.time() - start_time)
                return dict(row) if row else None

        except Exception as e:
            self._record_failed_query(time.time() - start_time)
            raise

    async def fetchval(self, query: str, *args) -> Any:
        """Fetch single value."""
        start_time = time.time()

        try:
            async with self.acquire() as conn:
                value = await conn.fetchval(query, *args)
                self._record_successful_query(time.time() - start_time)
                return value

        except Exception as e:
            self._record_failed_query(time.time() - start_time)
            raise

    async def transaction(self):
        """
        Create database transaction context.

        Usage:
            async with db_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute("INSERT ...")
                    await conn.execute("UPDATE ...")
        """
        async with self.acquire() as conn:
            async with conn.transaction():
                yield conn

    async def _perform_health_check(self) -> bool:
        """Perform database health check."""
        try:
            async with self.acquire() as conn:
                # Simple health check query
                result = await conn.fetchval("SELECT 1")
                if result == 1:
                    self.health.last_check = datetime.utcnow()
                    self.health.consecutive_failures = 0
                    return True
                else:
                    self.health.consecutive_failures += 1
                    return False

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            self.health.consecutive_failures += 1
            self.health.last_error = e
            return False

    async def _background_health_monitor(self):
        """Background task for continuous health monitoring."""
        while self.initialized:
            try:
                self.health.is_healthy = await self._perform_health_check()

                # Update pool statistics
                if self.pool:
                    self.health.total_connections = self.pool.get_size()

                # Log health status if unhealthy
                if not self.health.is_healthy:
                    logger.warning(f"Database health check failed. Consecutive failures: {self.health.consecutive_failures}")

                await asyncio.sleep(self.health_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(self.health_check_interval)

    def _record_query_metrics(self, query_time_ms: float):
        """Record query performance metrics."""
        self._query_metrics.append({
            "timestamp": time.time(),
            "query_time_ms": query_time_ms
        })

        # Trim metrics to keep memory usage bounded
        if len(self._query_metrics) > self._max_metrics:
            self._query_metrics = self._query_metrics[-self._max_metrics:]

        # Update averages
        if self._query_metrics:
            total_time = sum(m["query_time_ms"] for m in self._query_metrics)
            self.health.avg_query_time_ms = total_time / len(self._query_metrics)

    def _record_successful_query(self, query_time_seconds: float):
        """Record successful query metrics."""
        self.metrics["total_queries"] += 1
        self.metrics["successful_queries"] += 1

        query_time_ms = query_time_seconds * 1000
        self._record_query_metrics(query_time_ms)

        # Update peak response time
        if query_time_ms > self.metrics["peak_response_time_ms"]:
            self.metrics["peak_response_time_ms"] = query_time_ms

    def _record_failed_query(self, query_time_seconds: float):
        """Record failed query metrics."""
        self.metrics["total_queries"] += 1
        self.metrics["failed_queries"] += 1

        query_time_ms = query_time_seconds * 1000
        self._record_query_metrics(query_time_ms)

        # Calculate error rate
        if self.metrics["total_queries"] > 0:
            self.health.error_rate = self.metrics["failed_queries"] / self.metrics["total_queries"]

    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return self.health.to_dict()

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            **self.metrics,
            "pool_size": self.pool.get_size() if self.pool else 0,
            "pool_max_size": self.max_size,
            "pool_min_size": self.min_size,
            "health_status": self.get_health_status(),
            "recent_queries_count": len(self._query_metrics)
        }

    async def validate_schema(self) -> Dict[str, Any]:
        """Validate database schema integrity."""
        try:
            validation_results = await self.fetch(
                "SELECT * FROM validate_schema_integrity()"
            )

            return {
                "schema_valid": True,
                "validation_results": validation_results,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "schema_valid": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def get_table_stats(self) -> Dict[str, Any]:
        """Get database table statistics."""
        try:
            stats = await self.fetch("SELECT * FROM get_table_sizes()")
            return {
                "table_stats": stats,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting table stats: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global database pool instance
db_pool = EnhancedDatabasePool(
    min_size=getattr(settings, 'database_min_connections', 5),
    max_size=getattr(settings, 'database_max_connections', 20),
    command_timeout=getattr(settings, 'database_command_timeout', 60),
    health_check_interval=getattr(settings, 'database_health_check_interval', 30)
)


async def initialize_database():
    """Initialize global database pool."""
    return await db_pool.initialize()


async def close_database():
    """Close global database pool."""
    await db_pool.close()


async def get_database_health() -> Dict[str, Any]:
    """Get database health status."""
    return db_pool.get_health_status()


async def get_database_metrics() -> Dict[str, Any]:
    """Get database performance metrics."""
    return db_pool.get_performance_metrics()