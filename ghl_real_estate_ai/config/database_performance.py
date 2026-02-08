"""
Database Performance Configuration

Optimized database configuration for achieving:
- <50ms P95 database query latency
- 100+ connection pool for 1000+ concurrent users
- Connection pooling with health checks
- Query timeout and retry configuration
- Performance monitoring integration

Author: EnterpriseHub AI Performance Engineering
Version: 1.0.0
Last Updated: 2026-01-18
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class DatabasePerformanceConfig:
    """
    Production-optimized database performance configuration

    Targets:
    - P95 Query Latency: <50ms
    - Connection Pool: 100 connections (supports 1000+ concurrent users)
    - Query Timeout: 10 seconds (prevent long-running queries)
    - Health Check Interval: 10 seconds
    """

    # Connection Pool Configuration
    pool_size: int = 20  # Minimum connections
    max_overflow: int = 80  # Additional connections when pool exhausted (total: 100)
    pool_timeout: int = 30  # Seconds to wait for a connection from pool
    pool_recycle: int = 1800  # Recycle connections every 30 minutes
    pool_pre_ping: bool = True  # Enable connection health checks

    # Query Performance
    query_timeout: int = 10  # Maximum query execution time (seconds)
    statement_timeout: int = 10000  # PostgreSQL statement timeout (ms)
    lock_timeout: int = 5000  # PostgreSQL lock timeout (ms)

    # Connection Configuration
    connect_timeout: int = 5  # Connection timeout (seconds)
    keepalive: bool = True  # Enable TCP keepalive
    keepalive_idle: int = 60  # TCP keepalive idle time
    keepalive_interval: int = 15  # TCP keepalive interval
    keepalive_count: int = 5  # TCP keepalive count

    # PostgreSQL-specific optimizations
    prepared_statement_cache_size: int = 100  # Cache prepared statements
    client_encoding: str = "UTF8"
    application_name: str = "enterprisehub-ghl-ai"

    # Read replica configuration (if available)
    use_read_replicas: bool = False
    read_replica_url: Optional[str] = None
    read_replica_pool_size: int = 10

    def get_sqlalchemy_engine_options(self) -> Dict[str, Any]:
        """Get SQLAlchemy engine configuration options"""
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": self.pool_pre_ping,
            "connect_args": self._get_connect_args(),
        }

    def _get_connect_args(self) -> Dict[str, Any]:
        """Get connection arguments for database driver"""
        return {
            "connect_timeout": self.connect_timeout,
            "options": f"-c statement_timeout={self.statement_timeout} -c lock_timeout={self.lock_timeout}",
            "application_name": self.application_name,
            "client_encoding": self.client_encoding,
            "keepalives": 1 if self.keepalive else 0,
            "keepalives_idle": self.keepalive_idle,
            "keepalives_interval": self.keepalive_interval,
            "keepalives_count": self.keepalive_count,
        }

    def get_asyncpg_pool_options(self) -> Dict[str, Any]:
        """Get asyncpg connection pool configuration"""
        return {
            "min_size": self.pool_size,
            "max_size": self.pool_size + self.max_overflow,
            "max_queries": 50000,
            "max_inactive_connection_lifetime": self.pool_recycle,
            "timeout": self.connect_timeout,
            "command_timeout": self.query_timeout,
        }


# ============================================================================
# QUERY OPTIMIZATION PATTERNS
# ============================================================================


class QueryOptimizer:
    """
    Query optimization utilities for performance

    Best practices:
    - Use SELECT only required columns (not SELECT *)
    - Add proper indexes for frequent queries
    - Use LIMIT for pagination
    - Avoid N+1 queries with proper JOINs or batch loading
    - Use prepared statements for repeated queries
    """

    # Optimized query templates for common operations
    OPTIMIZED_QUERIES = {
        # Lead queries (most frequent)
        "get_lead_by_id": """
            SELECT id, email, phone, name, status, score, created_at, updated_at
            FROM leads
            WHERE id = $1
            LIMIT 1
        """,
        "get_leads_by_status": """
            SELECT id, email, name, status, score
            FROM leads
            WHERE status = $1
            ORDER BY score DESC, created_at DESC
            LIMIT $2 OFFSET $3
        """,
        "get_high_risk_leads": """
            SELECT l.id, l.email, l.name, c.risk_score_14d, c.risk_tier
            FROM leads l
            INNER JOIN churn_predictions c ON l.id = c.lead_id
            WHERE c.risk_tier IN ('critical', 'high')
            AND c.prediction_timestamp > NOW() - INTERVAL '7 days'
            ORDER BY c.risk_score_14d DESC
            LIMIT $1
        """,
        "get_lead_with_interactions": """
            SELECT l.*,
                   COUNT(i.id) as interaction_count,
                   MAX(i.created_at) as last_interaction
            FROM leads l
            LEFT JOIN interactions i ON l.id = i.lead_id
            WHERE l.id = $1
            GROUP BY l.id
        """,
        # Churn prediction queries
        "get_latest_prediction": """
            SELECT *
            FROM churn_predictions
            WHERE lead_id = $1
            ORDER BY prediction_timestamp DESC
            LIMIT 1
        """,
        "get_predictions_by_tier": """
            SELECT lead_id, risk_score_14d, risk_tier, confidence, prediction_timestamp
            FROM churn_predictions cp
            INNER JOIN (
                SELECT lead_id, MAX(prediction_timestamp) as max_ts
                FROM churn_predictions
                GROUP BY lead_id
            ) latest ON cp.lead_id = latest.lead_id
                     AND cp.prediction_timestamp = latest.max_ts
            WHERE cp.risk_tier = $1
            ORDER BY cp.risk_score_14d DESC
            LIMIT $2
        """,
        # Recovery campaign queries
        "get_recovery_eligible_leads": """
            SELECT ce.lead_id, ce.event_type, ce.recovery_eligibility,
                   ce.recovery_attempts_allowed - ce.recovery_attempts_used as attempts_remaining
            FROM churn_events ce
            INNER JOIN (
                SELECT lead_id, MAX(event_timestamp) as max_ts
                FROM churn_events
                GROUP BY lead_id
            ) latest ON ce.lead_id = latest.lead_id
                     AND ce.event_timestamp = latest.max_ts
            WHERE ce.recovery_eligibility IN ('eligible', 'partial')
            AND ce.recovery_attempts_used < ce.recovery_attempts_allowed
            ORDER BY ce.event_timestamp DESC
            LIMIT $1
        """,
        # Analytics queries
        "get_churn_analytics_summary": """
            SELECT
                COUNT(*) as total_events,
                COUNT(CASE WHEN event_type IN ('detected', 'confirmed') THEN 1 END) as churn_events,
                COUNT(CASE WHEN event_type = 'recovered' THEN 1 END) as recovery_events,
                COUNT(DISTINCT lead_id) as unique_leads
            FROM churn_events
            WHERE event_timestamp > NOW() - INTERVAL '$1 days'
        """,
        "get_intervention_effectiveness": """
            SELECT
                intervention_type,
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful,
                AVG(EXTRACT(EPOCH FROM (executed_time - scheduled_time))) as avg_delay_seconds
            FROM intervention_executions
            WHERE scheduled_time > NOW() - INTERVAL '$1 days'
            GROUP BY intervention_type
            ORDER BY successful DESC
        """,
    }

    @classmethod
    def get_query(cls, query_name: str) -> str:
        """Get optimized query by name"""
        return cls.OPTIMIZED_QUERIES.get(query_name, "")


# ============================================================================
# CONNECTION POOL MANAGER
# ============================================================================


class ConnectionPoolManager:
    """
    Manages database connection pools with performance monitoring

    Features:
    - Health checks for connections
    - Pool utilization monitoring
    - Automatic connection recovery
    - Performance metrics collection
    """

    _instance = None
    _pools: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConnectionPoolManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.config = DatabasePerformanceConfig()
        self._initialized = True
        logger.info("ConnectionPoolManager initialized")

    async def create_pool(self, pool_name: str, database_url: str) -> bool:
        """Create a new connection pool"""
        try:
            import asyncpg

            pool = await asyncpg.create_pool(database_url, **self.config.get_asyncpg_pool_options())

            self._pools[pool_name] = pool
            logger.info(f"Connection pool '{pool_name}' created successfully")
            return True

        except ImportError:
            logger.error("asyncpg not installed. Install with: pip install asyncpg")
            return False
        except Exception as e:
            logger.error(f"Failed to create connection pool '{pool_name}': {e}")
            return False

    async def get_connection(self, pool_name: str = "default"):
        """Get a connection from the pool"""
        pool = self._pools.get(pool_name)
        if not pool:
            raise ValueError(f"Connection pool '{pool_name}' not found")

        return await pool.acquire()

    async def release_connection(self, pool_name: str, connection):
        """Release a connection back to the pool"""
        pool = self._pools.get(pool_name)
        if pool:
            await pool.release(connection)

    async def close_pool(self, pool_name: str):
        """Close a connection pool"""
        pool = self._pools.get(pool_name)
        if pool:
            await pool.close()
            del self._pools[pool_name]
            logger.info(f"Connection pool '{pool_name}' closed")

    async def close_all_pools(self):
        """Close all connection pools"""
        for pool_name in list(self._pools.keys()):
            await self.close_pool(pool_name)

    def get_pool_stats(self, pool_name: str = "default") -> Dict[str, Any]:
        """Get pool statistics for monitoring"""
        pool = self._pools.get(pool_name)
        if not pool:
            return {"error": f"Pool '{pool_name}' not found"}

        return {
            "pool_name": pool_name,
            "size": pool.get_size(),
            "free_size": pool.get_idle_size(),
            "min_size": pool.get_min_size(),
            "max_size": pool.get_max_size(),
            "utilization_percent": ((pool.get_size() - pool.get_idle_size()) / pool.get_size() * 100)
            if pool.get_size() > 0
            else 0,
        }


# ============================================================================
# RECOMMENDED DATABASE INDEXES
# ============================================================================

# Critical indexes for performance (apply via migration)
PERFORMANCE_INDEXES = """
-- Performance-critical indexes for churn prediction system
-- Apply these indexes to achieve <50ms P95 query latency

-- Leads table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_status_score
    ON leads(status, score DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_created_at
    ON leads(created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_email_lower
    ON leads(LOWER(email));

-- Churn predictions indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_churn_predictions_lead_timestamp
    ON churn_predictions(lead_id, prediction_timestamp DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_churn_predictions_risk_tier
    ON churn_predictions(risk_tier, risk_score_14d DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_churn_predictions_timestamp
    ON churn_predictions(prediction_timestamp DESC);

-- Churn events indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_churn_events_lead_timestamp
    ON churn_events(lead_id, event_timestamp DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_churn_events_recovery_eligibility
    ON churn_events(recovery_eligibility);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_churn_events_event_type
    ON churn_events(event_type, event_timestamp DESC);

-- Interventions indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_interventions_lead_status
    ON intervention_executions(lead_id, status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_interventions_scheduled
    ON intervention_executions(scheduled_time, status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_interventions_type
    ON intervention_executions(intervention_type);

-- Interactions indexes (for engagement tracking)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_interactions_lead_created
    ON interactions(lead_id, created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_interactions_type_created
    ON interactions(interaction_type, created_at DESC);

-- Composite indexes for complex queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_status_score_created
    ON leads(status, score DESC, created_at DESC);
"""


# ============================================================================
# DEFAULT CONFIGURATION
# ============================================================================


def get_database_config() -> DatabasePerformanceConfig:
    """Get database performance configuration from environment or defaults"""
    config = DatabasePerformanceConfig()

    # Override from environment if available
    if os.getenv("DB_POOL_SIZE"):
        config.pool_size = int(os.getenv("DB_POOL_SIZE"))
    if os.getenv("DB_MAX_OVERFLOW"):
        config.max_overflow = int(os.getenv("DB_MAX_OVERFLOW"))
    if os.getenv("DB_QUERY_TIMEOUT"):
        config.query_timeout = int(os.getenv("DB_QUERY_TIMEOUT"))
    if os.getenv("DB_READ_REPLICA_URL"):
        config.use_read_replicas = True
        config.read_replica_url = os.getenv("DB_READ_REPLICA_URL")

    return config


def get_connection_pool_manager() -> ConnectionPoolManager:
    """Get singleton connection pool manager"""
    return ConnectionPoolManager()
