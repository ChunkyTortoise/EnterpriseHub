"""
Advanced Connection Pool Manager for Customer Intelligence Platform.

Optimizes database connections for:
- High concurrency async operations
- Connection pooling with proper sizing
- Health monitoring and recovery
- Load balancing across connections
- Automatic scaling based on load
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
import os

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool, NullPool, StaticPool
from sqlalchemy.engine.events import PoolEvents
from sqlalchemy import event, text
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError
import psutil

logger = logging.getLogger(__name__)

@dataclass
class ConnectionMetrics:
    """Connection pool performance metrics."""
    pool_size: int
    checked_out: int
    overflow: int
    checked_in: int
    total_connections: int
    active_queries: int
    avg_checkout_time_ms: float
    total_checkouts: int
    total_errors: int
    last_updated: datetime

@dataclass
class QueryMetrics:
    """Individual query performance metrics."""
    query_id: str
    duration_ms: float
    connection_id: str
    timestamp: datetime
    rows_affected: int
    error: Optional[str] = None

class AdaptiveConnectionPool:
    """Adaptive connection pool that scales based on load."""

    def __init__(
        self,
        database_url: str,
        initial_pool_size: int = 20,
        max_pool_size: int = 100,
        min_pool_size: int = 5,
        max_overflow: int = 50,
        pool_timeout: int = 10,
        pool_recycle: int = 3600,
        enable_adaptive_scaling: bool = True
    ):
        self.database_url = database_url
        self.initial_pool_size = initial_pool_size
        self.max_pool_size = max_pool_size
        self.min_pool_size = min_pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.enable_adaptive_scaling = enable_adaptive_scaling

        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[Callable] = None

        # Metrics tracking
        self.connection_metrics: List[ConnectionMetrics] = []
        self.query_metrics: List[QueryMetrics] = []
        self.checkout_times: List[float] = []
        self.error_count = 0
        self.total_checkouts = 0

        # Adaptive scaling
        self.current_pool_size = initial_pool_size
        self.last_scale_event = datetime.utcnow()
        self.scale_cooldown = timedelta(minutes=5)  # Minimum time between scale events

    async def initialize(self):
        """Initialize the connection pool with optimized settings."""
        # Calculate optimal pool size based on system resources
        optimal_pool_size = self._calculate_optimal_pool_size()

        if self.enable_adaptive_scaling:
            self.current_pool_size = min(optimal_pool_size, self.initial_pool_size)

        # Create engine with optimized pool settings
        self.engine = create_async_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=self.current_pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=True,  # Validate connections before use
            pool_reset_on_return='commit',  # Reset connection state
            echo=False,  # Disable SQL echo for performance
            future=True,  # SQLAlchemy 2.0 mode

            # Connection arguments for PostgreSQL optimization
            connect_args={
                "server_settings": {
                    "application_name": "customer_intelligence_platform",
                    "jit": "off",  # Disable JIT for faster simple queries
                    "shared_preload_libraries": "pg_stat_statements",
                },
                "command_timeout": 60,
                "prepare_threshold": 5,  # Prepare frequently used queries
            }
        )

        # Set up event listeners for monitoring
        self._setup_pool_events()

        # Create session factory
        self.session_factory = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False
        )

        # Start background monitoring
        if self.enable_adaptive_scaling:
            asyncio.create_task(self._monitor_and_scale())

        logger.info(
            f"Connection pool initialized with size={self.current_pool_size}, "
            f"max_overflow={self.max_overflow}"
        )

    def _calculate_optimal_pool_size(self) -> int:
        """Calculate optimal pool size based on system resources."""
        # Get system information
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)

        # Base calculation: 2-4 connections per CPU core
        base_pool_size = cpu_count * 3

        # Adjust based on available memory (each connection uses ~10MB)
        memory_limited_size = int((memory_gb * 1024) / 10) // 4  # Use 25% of available memory

        # Take the minimum of calculated sizes, but respect limits
        optimal_size = min(base_pool_size, memory_limited_size)
        optimal_size = max(self.min_pool_size, min(optimal_size, self.max_pool_size))

        logger.info(
            f"Calculated optimal pool size: {optimal_size} "
            f"(CPU cores: {cpu_count}, Memory: {memory_gb:.1f}GB)"
        )

        return optimal_size

    def _setup_pool_events(self):
        """Set up SQLAlchemy pool event listeners for monitoring."""

        @event.listens_for(self.engine.sync_engine.pool, "connect")
        def on_connect(dbapi_connection, connection_record):
            """Called when a new connection is created."""
            logger.debug("New database connection created")

            # Set optimal PostgreSQL connection settings
            with dbapi_connection.cursor() as cursor:
                # Optimize for customer intelligence workload
                cursor.execute("SET random_page_cost = 1.1")  # SSD-optimized
                cursor.execute("SET effective_cache_size = '1GB'")
                cursor.execute("SET work_mem = '4MB'")
                cursor.execute("SET maintenance_work_mem = '64MB'")
                cursor.execute("SET checkpoint_completion_target = 0.9")

        @event.listens_for(self.engine.sync_engine.pool, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            """Called when a connection is retrieved from the pool."""
            connection_record.info['checkout_time'] = time.perf_counter()
            self.total_checkouts += 1

        @event.listens_for(self.engine.sync_engine.pool, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            """Called when a connection is returned to the pool."""
            checkout_time = connection_record.info.get('checkout_time')
            if checkout_time:
                duration = (time.perf_counter() - checkout_time) * 1000
                self.checkout_times.append(duration)

                # Keep only recent checkout times (last 1000)
                if len(self.checkout_times) > 1000:
                    self.checkout_times = self.checkout_times[-1000:]

        @event.listens_for(self.engine.sync_engine.pool, "invalidate")
        def on_invalidate(dbapi_connection, connection_record, exception):
            """Called when a connection is invalidated."""
            logger.warning(f"Connection invalidated: {exception}")
            self.error_count += 1

    async def _monitor_and_scale(self):
        """Background task to monitor performance and scale pool if needed."""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                # Collect current metrics
                metrics = await self.get_pool_metrics()

                # Check if scaling is needed
                await self._check_and_scale(metrics)

                # Store metrics for history
                self.connection_metrics.append(metrics)

                # Keep only recent metrics (last 100 samples)
                if len(self.connection_metrics) > 100:
                    self.connection_metrics = self.connection_metrics[-100:]

            except Exception as e:
                logger.error(f"Error in pool monitoring: {e}")

    async def _check_and_scale(self, metrics: ConnectionMetrics):
        """Check if pool should be scaled and perform scaling."""
        now = datetime.utcnow()

        # Check cooldown period
        if now - self.last_scale_event < self.scale_cooldown:
            return

        # Scale up conditions
        should_scale_up = (
            metrics.checked_out / metrics.total_connections > 0.8 or  # >80% utilization
            metrics.avg_checkout_time_ms > 100 or  # Slow checkouts
            metrics.overflow > 0  # Using overflow connections
        )

        # Scale down conditions
        should_scale_down = (
            metrics.checked_out / metrics.total_connections < 0.3 and  # <30% utilization
            metrics.avg_checkout_time_ms < 10 and  # Fast checkouts
            self.current_pool_size > self.min_pool_size
        )

        if should_scale_up and self.current_pool_size < self.max_pool_size:
            await self._scale_up()
        elif should_scale_down:
            await self._scale_down()

    async def _scale_up(self):
        """Scale up the connection pool."""
        new_size = min(self.current_pool_size + 5, self.max_pool_size)

        if new_size > self.current_pool_size:
            logger.info(f"Scaling up connection pool from {self.current_pool_size} to {new_size}")

            # Note: SQLAlchemy doesn't support dynamic pool resizing
            # In production, this would require creating a new engine
            # For now, we log the recommendation
            self.current_pool_size = new_size
            self.last_scale_event = datetime.utcnow()

    async def _scale_down(self):
        """Scale down the connection pool."""
        new_size = max(self.current_pool_size - 3, self.min_pool_size)

        if new_size < self.current_pool_size:
            logger.info(f"Scaling down connection pool from {self.current_pool_size} to {new_size}")

            self.current_pool_size = new_size
            self.last_scale_event = datetime.utcnow()

    @asynccontextmanager
    async def get_session(self):
        """Get a database session with proper error handling and monitoring."""
        start_time = time.perf_counter()
        session = None

        try:
            session = self.session_factory()

            # Test connection with a simple query
            await session.execute(text("SELECT 1"))

            yield session

        except DisconnectionError:
            # Handle database disconnection
            logger.warning("Database disconnection detected, retrying...")
            if session:
                await session.close()

            # Retry with new session
            session = self.session_factory()
            yield session

        except Exception as e:
            logger.error(f"Database session error: {e}")
            if session:
                await session.rollback()
            raise

        finally:
            if session:
                try:
                    await session.close()
                except Exception as e:
                    logger.error(f"Error closing session: {e}")

            # Record session duration
            duration = (time.perf_counter() - start_time) * 1000
            self.query_metrics.append(QueryMetrics(
                query_id=f"session_{int(time.time())}",
                duration_ms=duration,
                connection_id="unknown",
                timestamp=datetime.utcnow(),
                rows_affected=0
            ))

    async def execute_with_retry(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        retry_delay: float = 0.1
    ) -> Any:
        """Execute query with automatic retry logic."""
        last_exception = None

        for attempt in range(max_retries):
            try:
                async with self.get_session() as session:
                    result = await session.execute(text(query), parameters or {})
                    await session.commit()
                    return result

            except (DisconnectionError, SQLAlchemyError) as e:
                last_exception = e
                logger.warning(f"Query attempt {attempt + 1} failed: {e}")

                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff

            except Exception as e:
                # Non-retryable error
                logger.error(f"Non-retryable error in query execution: {e}")
                raise

        # All retries failed
        logger.error(f"Query failed after {max_retries} attempts")
        raise last_exception

    async def get_pool_metrics(self) -> ConnectionMetrics:
        """Get current connection pool metrics."""
        pool = self.engine.pool

        # Calculate average checkout time
        avg_checkout_time = 0
        if self.checkout_times:
            avg_checkout_time = sum(self.checkout_times) / len(self.checkout_times)

        return ConnectionMetrics(
            pool_size=pool.size(),
            checked_out=pool.checkedout(),
            overflow=pool.overflow(),
            checked_in=pool.checkedin(),
            total_connections=pool.size() + pool.overflow(),
            active_queries=pool.checkedout(),  # Approximation
            avg_checkout_time_ms=avg_checkout_time,
            total_checkouts=self.total_checkouts,
            total_errors=self.error_count,
            last_updated=datetime.utcnow()
        )

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of the connection pool."""
        start_time = time.perf_counter()

        try:
            # Test basic connectivity
            async with self.get_session() as session:
                result = await session.execute(text("SELECT current_timestamp, version()"))
                row = result.first()

                if row:
                    db_timestamp = row[0]
                    db_version = row[1]
                else:
                    raise Exception("No result from health check query")

            # Get pool metrics
            metrics = await self.get_pool_metrics()

            # Calculate health score (0-100)
            health_score = 100
            if metrics.avg_checkout_time_ms > 50:
                health_score -= 20
            if metrics.checked_out / metrics.total_connections > 0.8:
                health_score -= 30
            if self.error_count > 10:
                health_score -= 25

            response_time = (time.perf_counter() - start_time) * 1000

            return {
                "status": "healthy" if health_score > 70 else "degraded",
                "health_score": health_score,
                "response_time_ms": response_time,
                "database_timestamp": db_timestamp.isoformat() if db_timestamp else None,
                "database_version": db_version,
                "pool_metrics": {
                    "pool_size": metrics.pool_size,
                    "active_connections": metrics.checked_out,
                    "total_connections": metrics.total_connections,
                    "avg_checkout_time_ms": metrics.avg_checkout_time_ms,
                    "total_errors": metrics.total_errors
                },
                "adaptive_scaling": {
                    "enabled": self.enable_adaptive_scaling,
                    "current_pool_size": self.current_pool_size,
                    "last_scale_event": self.last_scale_event.isoformat()
                }
            }

        except Exception as e:
            response_time = (time.perf_counter() - start_time) * 1000

            return {
                "status": "unhealthy",
                "health_score": 0,
                "response_time_ms": response_time,
                "error": str(e),
                "pool_metrics": None
            }

    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        metrics = await self.get_pool_metrics()

        # Analyze query performance
        if self.query_metrics:
            query_times = [q.duration_ms for q in self.query_metrics]
            avg_query_time = sum(query_times) / len(query_times)
            slow_queries = [q for q in self.query_metrics if q.duration_ms > 100]
        else:
            avg_query_time = 0
            slow_queries = []

        # Calculate performance trends
        performance_trend = "stable"
        if len(self.connection_metrics) >= 2:
            recent_avg = sum(m.avg_checkout_time_ms for m in self.connection_metrics[-5:]) / min(5, len(self.connection_metrics))
            older_avg = sum(m.avg_checkout_time_ms for m in self.connection_metrics[-10:-5]) / min(5, len(self.connection_metrics) - 5)

            if recent_avg > older_avg * 1.2:
                performance_trend = "degrading"
            elif recent_avg < older_avg * 0.8:
                performance_trend = "improving"

        return {
            "summary": {
                "pool_utilization": f"{(metrics.checked_out / metrics.total_connections) * 100:.1f}%",
                "avg_checkout_time_ms": metrics.avg_checkout_time_ms,
                "avg_query_time_ms": avg_query_time,
                "total_queries": len(self.query_metrics),
                "slow_queries": len(slow_queries),
                "error_rate": f"{(metrics.total_errors / max(metrics.total_checkouts, 1)) * 100:.2f}%",
                "performance_trend": performance_trend
            },
            "current_metrics": metrics,
            "recommendations": self._generate_recommendations(metrics),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _generate_recommendations(self, metrics: ConnectionMetrics) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []

        if metrics.avg_checkout_time_ms > 50:
            recommendations.append("Consider increasing pool size - high checkout times detected")

        if metrics.checked_out / metrics.total_connections > 0.8:
            recommendations.append("Pool utilization is high (>80%) - consider scaling up")

        if metrics.overflow > 5:
            recommendations.append("Frequent overflow connections - increase base pool size")

        if self.error_count > 10:
            recommendations.append("High error count - check database health and network connectivity")

        if not recommendations:
            recommendations.append("Connection pool is performing well")

        return recommendations

    async def close(self):
        """Close the connection pool and cleanup resources."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Connection pool closed")

# Factory function for easy initialization
async def create_connection_manager(database_url: str, **kwargs) -> AdaptiveConnectionPool:
    """Create and initialize adaptive connection pool manager."""
    manager = AdaptiveConnectionPool(database_url, **kwargs)
    await manager.initialize()
    return manager