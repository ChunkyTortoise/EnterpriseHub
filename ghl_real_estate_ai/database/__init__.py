"""
Database and Redis Infrastructure Initialization.

Provides unified initialization and management for:
- PostgreSQL connection pooling
- Redis caching
- Health monitoring
- Performance metrics
"""

import asyncio
from typing import Dict, Any, Optional
import atexit

from .connection import (
    db_pool, initialize_database, close_database,
    get_database_health, get_database_metrics
)
from .redis_client import (
    redis_client, initialize_redis, close_redis,
    get_redis_health, get_redis_metrics
)

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class InfrastructureManager:
    """
    Unified infrastructure manager for database and Redis.
    """

    def __init__(self):
        self.initialized = False
        self.database_available = False
        self.redis_available = False
        self._shutdown_registered = False

    async def initialize(self, enable_database: bool = True, enable_redis: bool = True) -> Dict[str, bool]:
        """
        Initialize database and Redis infrastructure.

        Args:
            enable_database: Whether to initialize database
            enable_redis: Whether to initialize Redis

        Returns:
            Dictionary with initialization results
        """
        if self.initialized:
            logger.info("Infrastructure already initialized")
            return {
                "database": self.database_available,
                "redis": self.redis_available,
                "overall": True
            }

        results = {}

        # Initialize database if requested
        if enable_database:
            try:
                self.database_available = await initialize_database()
                results["database"] = self.database_available
                if self.database_available:
                    logger.info("✅ Database connection pool initialized successfully")
                else:
                    logger.warning("⚠️ Database initialization failed, continuing without database")
            except Exception as e:
                logger.error(f"❌ Database initialization error: {e}")
                self.database_available = False
                results["database"] = False

        # Initialize Redis if requested
        if enable_redis:
            try:
                self.redis_available = await initialize_redis()
                results["redis"] = self.redis_available
                if self.redis_available:
                    logger.info("✅ Redis client initialized successfully")
                else:
                    logger.warning("⚠️ Redis initialization failed, continuing without cache")
            except Exception as e:
                logger.error(f"❌ Redis initialization error: {e}")
                self.redis_available = False
                results["redis"] = False

        # Register shutdown hook
        if not self._shutdown_registered:
            atexit.register(lambda: asyncio.create_task(self.shutdown()))
            self._shutdown_registered = True

        self.initialized = True
        overall_success = any(results.values()) if results else False
        results["overall"] = overall_success

        if overall_success:
            logger.info("🚀 Infrastructure initialization completed")
        else:
            logger.warning("⚠️ Infrastructure initialization completed with limited functionality")

        return results

    async def shutdown(self):
        """Gracefully shutdown infrastructure."""
        if not self.initialized:
            return

        logger.info("🛑 Shutting down infrastructure...")

        # Shutdown database
        if self.database_available:
            try:
                await close_database()
                logger.info("✅ Database connection pool closed")
            except Exception as e:
                logger.error(f"❌ Error closing database: {e}")

        # Shutdown Redis
        if self.redis_available:
            try:
                await close_redis()
                logger.info("✅ Redis client closed")
            except Exception as e:
                logger.error(f"❌ Error closing Redis: {e}")

        self.initialized = False
        self.database_available = False
        self.redis_available = False

        logger.info("✅ Infrastructure shutdown completed")

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for all infrastructure components."""
        health_status = {
            "timestamp": asyncio.get_event_loop().time(),
            "infrastructure_initialized": self.initialized,
            "components": {}
        }

        # Database health
        if self.database_available:
            try:
                db_health = await get_database_health()
                health_status["components"]["database"] = {
                    "available": True,
                    "healthy": db_health.get("is_healthy", False),
                    "details": db_health
                }
            except Exception as e:
                health_status["components"]["database"] = {
                    "available": False,
                    "healthy": False,
                    "error": str(e)
                }
        else:
            health_status["components"]["database"] = {
                "available": False,
                "healthy": False,
                "reason": "Not initialized"
            }

        # Redis health
        if self.redis_available:
            try:
                redis_health = await get_redis_health()
                health_status["components"]["redis"] = {
                    "available": True,
                    "healthy": redis_health.get("is_healthy", False),
                    "details": redis_health
                }
            except Exception as e:
                health_status["components"]["redis"] = {
                    "available": False,
                    "healthy": False,
                    "error": str(e)
                }
        else:
            health_status["components"]["redis"] = {
                "available": False,
                "healthy": False,
                "reason": "Not initialized"
            }

        # Overall health
        component_health = [
            comp.get("healthy", False)
            for comp in health_status["components"].values()
        ]
        health_status["overall_healthy"] = any(component_health)

        return health_status

    async def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        metrics = {
            "timestamp": asyncio.get_event_loop().time(),
            "infrastructure_status": {
                "initialized": self.initialized,
                "database_available": self.database_available,
                "redis_available": self.redis_available
            }
        }

        # Database metrics
        if self.database_available:
            try:
                db_metrics = await get_database_metrics()
                metrics["database"] = db_metrics
            except Exception as e:
                metrics["database"] = {"error": str(e)}

        # Redis metrics
        if self.redis_available:
            try:
                redis_metrics = await get_redis_metrics()
                metrics["redis"] = redis_metrics
            except Exception as e:
                metrics["redis"] = {"error": str(e)}

        return metrics

    async def validate_setup(self) -> Dict[str, Any]:
        """Validate infrastructure setup and configuration."""
        validation_results = {
            "timestamp": asyncio.get_event_loop().time(),
            "overall_valid": True,
            "components": {}
        }

        # Database validation
        if self.database_available:
            try:
                # Validate schema if database is available
                schema_validation = await db_pool.validate_schema()
                validation_results["components"]["database"] = {
                    "available": True,
                    "schema_valid": schema_validation.get("schema_valid", False),
                    "details": schema_validation
                }
            except Exception as e:
                validation_results["components"]["database"] = {
                    "available": False,
                    "schema_valid": False,
                    "error": str(e)
                }
                validation_results["overall_valid"] = False
        else:
            validation_results["components"]["database"] = {
                "available": False,
                "reason": "Database not initialized or unavailable"
            }

        # Redis validation
        if self.redis_available:
            try:
                # Test basic Redis operations
                test_key = "infrastructure:test"
                set_success = await redis_client.set(test_key, "test_value", ttl=10)
                get_value = await redis_client.get(test_key)
                delete_success = await redis_client.delete(test_key)

                validation_results["components"]["redis"] = {
                    "available": True,
                    "operations_working": set_success and get_value == "test_value" and delete_success,
                    "test_results": {
                        "set": set_success,
                        "get": get_value == "test_value",
                        "delete": delete_success > 0
                    }
                }
            except Exception as e:
                validation_results["components"]["redis"] = {
                    "available": False,
                    "operations_working": False,
                    "error": str(e)
                }
                validation_results["overall_valid"] = False
        else:
            validation_results["components"]["redis"] = {
                "available": False,
                "reason": "Redis not initialized or unavailable"
            }

        return validation_results


# Global infrastructure manager instance
infrastructure = InfrastructureManager()


# Convenience functions for backward compatibility and ease of use
async def initialize_infrastructure(enable_database: bool = True, enable_redis: bool = True) -> bool:
    """
    Initialize infrastructure components.

    Args:
        enable_database: Whether to initialize database
        enable_redis: Whether to initialize Redis

    Returns:
        True if any component initialized successfully
    """
    results = await infrastructure.initialize(enable_database, enable_redis)
    return results.get("overall", False)


async def shutdown_infrastructure():
    """Shutdown all infrastructure components."""
    await infrastructure.shutdown()


async def get_infrastructure_health() -> Dict[str, Any]:
    """Get infrastructure health status."""
    return await infrastructure.health_check()


async def get_infrastructure_metrics() -> Dict[str, Any]:
    """Get infrastructure performance metrics."""
    return await infrastructure.get_metrics()


async def validate_infrastructure() -> Dict[str, Any]:
    """Validate infrastructure setup."""
    return await infrastructure.validate_setup()


# Export main components for direct access
__all__ = [
    # Infrastructure manager
    'infrastructure',
    'initialize_infrastructure',
    'shutdown_infrastructure',
    'get_infrastructure_health',
    'get_infrastructure_metrics',
    'validate_infrastructure',

    # Database components
    'db_pool',
    'initialize_database',
    'close_database',
    'get_database_health',
    'get_database_metrics',

    # Redis components
    'redis_client',
    'initialize_redis',
    'close_redis',
    'get_redis_health',
    'get_redis_metrics'
]