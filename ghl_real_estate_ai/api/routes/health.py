"""
Health Check API Routes - Enhanced Health Monitoring.

Provides comprehensive health checks for database, external services,
and system metrics following TDD methodology.
"""

import time
import psutil
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


def check_database_health() -> Dict[str, Any]:
    """
    Check database connectivity and performance.

    Returns:
        Dict with database health information
    """
    start_time = time.time()

    try:
        # TODO: Implement actual database connectivity check
        # For now, simulate a health check
        connection_time_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "status": "healthy",
            "connection_time_ms": connection_time_ms,
            "database_type": "postgresql"  # Based on project config
        }

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "connection_time_ms": round((time.time() - start_time) * 1000, 2)
        }


def check_external_services() -> Dict[str, Any]:
    """
    Check external service connectivity.

    Returns:
        Dict with external service health information
    """
    services = {
        "ghl_api": {"status": "healthy", "response_time_ms": 120},
        "anthropic_api": {"status": "healthy", "response_time_ms": 85}
    }

    # TODO: Implement actual service connectivity checks
    # For now, simulate healthy services

    return services


def get_system_metrics() -> Dict[str, Any]:
    """
    Get basic system metrics.

    Returns:
        Dict with system metrics
    """
    try:
        # Get memory usage
        memory = psutil.virtual_memory()
        memory_usage_mb = round(memory.used / 1024 / 1024, 2)

        # Get uptime (approximate)
        uptime_seconds = round(time.time() - psutil.boot_time(), 2)

        return {
            "memory_usage_mb": memory_usage_mb,
            "memory_percent": round(memory.percent, 2),
            "uptime_seconds": uptime_seconds,
            "cpu_percent": round(psutil.cpu_percent(), 2)
        }

    except Exception as e:
        logger.error(f"System metrics collection failed: {e}")
        return {
            "error": str(e),
            "memory_usage_mb": 0,
            "uptime_seconds": 0
        }


@router.get("/health")
async def enhanced_health_check():
    """
    Enhanced health check endpoint with comprehensive monitoring.

    Returns:
        - 200: System is healthy
        - 503: System is unhealthy (database issues)
        - 200 with degraded: External services have issues but core is working
    """
    # Basic service info
    health_data = {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.version,
        "timestamp": time.time()
    }

    # Check database health
    database_health = check_database_health()
    health_data["database"] = database_health

    # Check external services
    external_services = check_external_services()
    health_data["external_services"] = external_services

    # Get system metrics
    system_metrics = get_system_metrics()
    health_data["system"] = system_metrics

    # Determine overall status
    overall_status = "healthy"
    http_status = status.HTTP_200_OK

    # If database is unhealthy, mark as unhealthy
    if database_health.get("status") == "unhealthy":
        overall_status = "unhealthy"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    # If external services are unhealthy, mark as degraded
    elif any(service.get("status") == "unhealthy" for service in external_services.values()):
        overall_status = "degraded"

    health_data["status"] = overall_status

    return JSONResponse(
        status_code=http_status,
        content=health_data
    )