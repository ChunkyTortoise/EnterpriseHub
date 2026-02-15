"""
Comprehensive Health Check Endpoints for Service 6 Lead Recovery & Nurture Engine.

Provides multiple levels of health checks:
- Basic liveness probe
- Detailed readiness checks
- Deep system health validation
- Performance metrics
- Service dependencies
"""

import time
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing_extensions import Annotated

from ghl_real_estate_ai.api.enterprise.auth import enterprise_auth_service
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import CacheService, get_cache_service
from ghl_real_estate_ai.services.circuit_breaker import get_circuit_manager
from ghl_real_estate_ai.services.database_service import DatabaseService, get_database
from ghl_real_estate_ai.services.monitoring_service import MonitoringService
from ghl_real_estate_ai.services.security_framework import SecurityFramework

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["Health Checks"])

# FastAPI dependency injection - using @lru_cache for singleton behavior


@lru_cache(maxsize=1)
def get_monitoring_service() -> MonitoringService:
    """Get MonitoringService singleton instance."""
    return MonitoringService()


@lru_cache(maxsize=1)
def get_security_framework() -> SecurityFramework:
    """Get SecurityFramework singleton instance."""
    return SecurityFramework()


# Annotated types for cleaner dependency injection
DatabaseDep = Annotated[DatabaseService, Depends(get_database)]
CacheDep = Annotated[CacheService, Depends(get_cache_service)]
MonitoringDep = Annotated[MonitoringService, Depends(get_monitoring_service)]
SecurityDep = Annotated[SecurityFramework, Depends(get_security_framework)]
UserDep = Annotated[dict, Depends(enterprise_auth_service.get_current_enterprise_user)]


class HealthResponse(BaseModel):
    """Standard health response model."""

    status: str  # healthy, degraded, unhealthy, critical
    timestamp: str
    version: str = "1.0.0"
    environment: str = settings.environment or "production"
    uptime_seconds: Optional[float] = None
    checks: Dict[str, Any] = {}


class ServiceHealth(BaseModel):
    """Individual service health model."""

    name: str
    status: str
    response_time_ms: Optional[float] = None
    last_check: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class DetailedHealthResponse(BaseModel):
    """Detailed health response with all services."""

    overall_status: str
    timestamp: str
    version: str = "1.0.0"
    environment: str = settings.environment or "production"
    uptime_seconds: Optional[float] = None
    services: List[ServiceHealth] = []
    metrics: Dict[str, Any] = {}
    alerts: List[Dict[str, Any]] = []


# Track service start time for uptime calculation
_service_start_time = time.time()


@router.get("/", response_model=HealthResponse)
async def basic_health(
    db: DatabaseDep,
    cache: CacheDep,
):
    """
    Basic liveness probe.

    Returns minimal health status for load balancer health checks.
    Fast response with minimal dependencies.
    """
    try:
        uptime = time.time() - _service_start_time

        # Basic database check
        try:
            db_health = await db.health_check()
            db_healthy = db_health.get("status") == "healthy"
        except Exception as e:
            logger.warning(f"Database health check failed in basic probe: {e}")
            db_healthy = False

        # Basic cache check
        try:
            await cache.set("health_check_basic", "ok", ttl=10)
            cache_result = await cache.get("health_check_basic")
            cache_healthy = cache_result == "ok"
        except Exception as e:
            logger.warning(f"Cache health check failed in basic probe: {e}")
            cache_healthy = False

        # Determine overall status
        if db_healthy and cache_healthy:
            status = "healthy"
        elif db_healthy or cache_healthy:
            status = "degraded"
        else:
            status = "unhealthy"

        return HealthResponse(
            status=status,
            timestamp=datetime.utcnow().isoformat(),
            uptime_seconds=uptime,
            checks={
                "database": "healthy" if db_healthy else "unhealthy",
                "cache": "healthy" if cache_healthy else "unhealthy",
            },
        )

    except Exception as e:
        logger.error(f"Basic health check failed: {e}")
        return HealthResponse(status="critical", timestamp=datetime.utcnow().isoformat(), checks={"error": str(e)})


@router.get("/live", response_model=HealthResponse)
async def liveness_probe():
    """
    Kubernetes-style liveness probe.

    Indicates if the application is running and should be restarted if failing.
    Very lightweight check - only verifies the process is responsive.
    """
    uptime = time.time() - _service_start_time

    return HealthResponse(
        status="healthy", timestamp=datetime.utcnow().isoformat(), uptime_seconds=uptime, checks={"process": "running"}
    )


@router.get("/ready", response_model=DetailedHealthResponse)
async def readiness_probe(
    current_user: UserDep,
    db: DatabaseDep,
    cache: CacheDep,
    security: SecurityDep,
):
    """
    Kubernetes-style readiness probe.

    Indicates if the application is ready to serve traffic.
    Checks all critical dependencies before marking as ready.
    """
    try:
        uptime = time.time() - _service_start_time
        services = []
        overall_status = "healthy"

        # Check database
        try:
            db_health = await db.health_check()

            services.append(
                ServiceHealth(
                    name="database",
                    status=db_health.get("status", "unknown"),
                    response_time_ms=db_health.get("response_time_seconds", 0) * 1000,
                    last_check=datetime.utcnow().isoformat(),
                    metadata={
                        "pool_size": db_health.get("pool_stats", {}).get("size", 0),
                        "idle_connections": db_health.get("pool_stats", {}).get("idle", 0),
                    },
                )
            )

            if db_health.get("status") != "healthy":
                overall_status = "unhealthy"

        except Exception as e:
            services.append(
                ServiceHealth(
                    name="database", status="critical", last_check=datetime.utcnow().isoformat(), error=str(e)
                )
            )
            overall_status = "critical"

        # Check cache/Redis
        try:
            cache_start = time.time()

            await cache.set("readiness_check", "ok", ttl=10)
            result = await cache.get("readiness_check")

            cache_response_time = (time.time() - cache_start) * 1000
            cache_healthy = result == "ok"

            services.append(
                ServiceHealth(
                    name="cache",
                    status="healthy" if cache_healthy else "unhealthy",
                    response_time_ms=cache_response_time,
                    last_check=datetime.utcnow().isoformat(),
                )
            )

            if not cache_healthy and overall_status == "healthy":
                overall_status = "degraded"

        except Exception as e:
            services.append(
                ServiceHealth(name="cache", status="critical", last_check=datetime.utcnow().isoformat(), error=str(e))
            )
            if overall_status == "healthy":
                overall_status = "degraded"

        # Check security framework
        try:
            # Test JWT functionality
            test_token = security.generate_jwt_token("readiness_test", "user")
            token_valid = bool(test_token and len(test_token) > 50)

            services.append(
                ServiceHealth(
                    name="security",
                    status="healthy" if token_valid else "unhealthy",
                    last_check=datetime.utcnow().isoformat(),
                    metadata={"jwt_functional": token_valid},
                )
            )

        except Exception as e:
            services.append(
                ServiceHealth(
                    name="security", status="unhealthy", last_check=datetime.utcnow().isoformat(), error=str(e)
                )
            )

        return DetailedHealthResponse(
            overall_status=overall_status,
            timestamp=datetime.utcnow().isoformat(),
            uptime_seconds=uptime,
            services=services,
            metrics={
                "total_services": len(services),
                "healthy_services": len([s for s in services if s.status == "healthy"]),
                "unhealthy_services": len([s for s in services if s.status in ["unhealthy", "critical"]]),
            },
        )

    except Exception as e:
        logger.error(f"Readiness probe failed: {e}")
        return DetailedHealthResponse(
            overall_status="critical", timestamp=datetime.utcnow().isoformat(), services=[], metrics={"error": str(e)}
        )


@router.get("/deep", response_model=DetailedHealthResponse)
async def deep_health_check(
    current_user: UserDep,
    monitoring: MonitoringDep,
):
    """
    Comprehensive deep health check.

    Includes all service dependencies, external APIs, and performance metrics.
    Should not be called frequently due to comprehensive nature.
    """
    try:
        uptime = time.time() - _service_start_time
        services = []
        alerts = []

        # Run comprehensive health checks
        try:
            # Initialize services for health checking if not already done
            from ghl_real_estate_ai.services.database_service import DatabaseService

            db = DatabaseService()
            await db.initialize()
            monitoring.register_database_health_check(db)

            # Register Graph DB health check
            monitoring.register_graph_health_check()

            # Add other services if credentials are available
            if settings.apollo_api_key and not settings.apollo_api_key.startswith("your_"):
                from ghl_real_estate_ai.services.apollo_client import ApolloClient

                apollo = ApolloClient()
                monitoring.register_apollo_health_check(apollo)

            if settings.twilio_account_sid and not settings.twilio_account_sid.startswith("your_"):
                from ghl_real_estate_ai.services.twilio_client import TwilioClient

                twilio = TwilioClient()
                monitoring.register_twilio_health_check(twilio)

            if settings.sendgrid_api_key and not settings.sendgrid_api_key.startswith("your_"):
                from ghl_real_estate_ai.services.sendgrid_client import SendGridClient

                sendgrid = SendGridClient()
                monitoring.register_sendgrid_health_check(sendgrid)

            if settings.ghl_api_key and not settings.ghl_api_key.startswith("your_"):
                from ghl_real_estate_ai.services.enhanced_ghl_client import EnhancedGHLClient

                ghl = EnhancedGHLClient()
                monitoring.register_ghl_health_check(ghl)

            # Run all health checks
            health_results = await monitoring.run_all_health_checks()

            # Convert to service health objects
            for service_name, result in health_results.get("services", {}).items():
                services.append(
                    ServiceHealth(
                        name=service_name,
                        status=result.get("status", "unknown"),
                        response_time_ms=result.get("response_time_ms"),
                        last_check=result.get("timestamp", datetime.utcnow().isoformat()),
                        error=result.get("error"),
                        metadata=result.get("details", {}),
                    )
                )

            # Get active alerts
            active_alerts = await monitoring.get_active_alerts()
            alerts = [alert.dict() for alert in active_alerts[-5:]]  # Last 5 alerts

            overall_status = health_results.get("overall_status", "unknown")

        except Exception as e:
            logger.error(f"Deep health check monitoring failed: {e}")
            overall_status = "degraded"
            services.append(
                ServiceHealth(
                    name="monitoring", status="failed", last_check=datetime.utcnow().isoformat(), error=str(e)
                )
            )

        # Calculate performance metrics
        metrics = {
            "total_services": len(services),
            "healthy_services": len([s for s in services if s.status == "healthy"]),
            "degraded_services": len([s for s in services if s.status == "degraded"]),
            "unhealthy_services": len([s for s in services if s.status in ["unhealthy", "critical"]]),
            "active_alerts": len(alerts),
            "avg_response_time_ms": sum(s.response_time_ms or 0 for s in services) / len(services) if services else 0,
        }

        # Add system metrics
        try:
            import psutil

            metrics.update(
                {
                    "cpu_percent": psutil.cpu_percent(interval=0.1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage("/").percent,
                }
            )
        except ImportError:
            # psutil not available
            pass

        return DetailedHealthResponse(
            overall_status=overall_status,
            timestamp=datetime.utcnow().isoformat(),
            uptime_seconds=uptime,
            services=services,
            metrics=metrics,
            alerts=alerts,
        )

    except Exception as e:
        logger.error(f"Deep health check failed: {e}")
        return DetailedHealthResponse(
            overall_status="critical",
            timestamp=datetime.utcnow().isoformat(),
            services=[],
            metrics={"error": str(e)},
            alerts=[],
        )


@router.get("/metrics")
async def performance_metrics(
    current_user: UserDep,
    monitoring: MonitoringDep,
    db: DatabaseDep,
):
    """
    Get performance and operational metrics.

    Provides detailed performance data for monitoring systems.
    """
    try:
        # Get performance summary
        performance = monitoring.get_performance_summary(duration_minutes=15)

        # Get SLA compliance
        sla_results = await monitoring.check_sla_compliance()

        # System uptime
        uptime_seconds = time.time() - _service_start_time

        # Database statistics
        db_stats = {}
        try:
            db_metrics = await db.get_performance_metrics()
            db_stats = db_metrics
        except Exception as e:
            logger.warning(f"Could not get database metrics: {e}")

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": uptime_seconds,
            "performance": performance,
            "sla_compliance": sla_results,
            "database": db_stats,
            "version": "1.0.0",
            "environment": settings.environment or "production",
        }

    except Exception:
        logger.exception("Metrics endpoint failed")
        raise HTTPException(status_code=500, detail="Metrics collection failed")


@router.get("/dependencies")
async def dependency_status(
    current_user: UserDep,
    db: DatabaseDep,
    cache: CacheDep,
):
    """
    Get status of all external dependencies.

    Useful for understanding which external services are affecting system health.
    """
    try:
        dependencies = {}

        # Database dependency
        try:
            db_health = await db.health_check()
            dependencies["database"] = {
                "status": db_health.get("status"),
                "type": "critical",
                "endpoint": "Internal PostgreSQL",
                "response_time_ms": db_health.get("response_time_seconds", 0) * 1000,
                "last_check": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            dependencies["database"] = {
                "status": "failed",
                "type": "critical",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat(),
            }

        # Redis dependency
        try:
            start_time = time.time()
            await cache.set("dependency_check", "ok", ttl=5)
            result = await cache.get("dependency_check")
            response_time = (time.time() - start_time) * 1000

            dependencies["redis"] = {
                "status": "healthy" if result == "ok" else "failed",
                "type": "critical",
                "endpoint": settings.redis_url.split("@")[-1] if "@" in settings.redis_url else settings.redis_url,
                "response_time_ms": response_time,
                "last_check": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            dependencies["redis"] = {
                "status": "failed",
                "type": "critical",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat(),
            }

        # External API dependencies
        external_apis = [
            ("apollo", "Apollo.io", settings.apollo_api_key),
            ("twilio", "Twilio", settings.twilio_account_sid),
            ("sendgrid", "SendGrid", settings.sendgrid_api_key),
            ("ghl", "GoHighLevel", settings.ghl_api_key),
        ]

        for api_name, api_label, api_key in external_apis:
            if api_key and not api_key.startswith("your_"):
                # Mark as configured but don't test (to avoid rate limits)
                dependencies[api_name] = {
                    "status": "configured",
                    "type": "optional",
                    "endpoint": api_label,
                    "note": "Credentials configured - use /health/deep for full test",
                    "last_check": datetime.utcnow().isoformat(),
                }
            else:
                dependencies[api_name] = {
                    "status": "not_configured",
                    "type": "optional",
                    "endpoint": api_label,
                    "last_check": datetime.utcnow().isoformat(),
                }

        # Calculate summary
        total_deps = len(dependencies)
        critical_deps = len([d for d in dependencies.values() if d.get("type") == "critical"])
        healthy_critical = len(
            [d for d in dependencies.values() if d.get("type") == "critical" and d.get("status") == "healthy"]
        )

        summary = {
            "total_dependencies": total_deps,
            "critical_dependencies": critical_deps,
            "healthy_critical_dependencies": healthy_critical,
            "critical_health_percentage": (healthy_critical / critical_deps * 100) if critical_deps > 0 else 100,
        }

        return {"timestamp": datetime.utcnow().isoformat(), "summary": summary, "dependencies": dependencies}

    except Exception:
        logger.exception("Dependency status check failed")
        raise HTTPException(status_code=500, detail="Dependency check failed")


@router.post("/alerts/test")
async def test_alerting(
    current_user: UserDep,
    monitoring: MonitoringDep,
):
    """
    Test the alerting system by creating a test alert.

    Useful for validating alert delivery mechanisms.
    """
    try:
        # Create test alert
        alert_id = await monitoring.create_alert(
            service_name="health_check",
            severity=monitoring.AlertSeverity.INFO,
            title="Health Check Test Alert",
            message="This is a test alert generated from the health check endpoint",
            metadata={"test": True, "generated_by": "health_endpoint"},
        )

        return {
            "message": "Test alert created successfully",
            "alert_id": alert_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception:
        logger.exception("Test alert creation failed")
        raise HTTPException(status_code=500, detail="Alert test failed")


@router.get("/status")
async def service_status(
    db: DatabaseDep,
    cache: CacheDep,
):
    """
    Human-readable service status page.

    Returns a simple text status suitable for monitoring dashboards.
    """
    try:
        # Determine health status (similar to basic_health)
        try:
            db_health = await db.health_check()
            db_healthy = db_health.get("status") == "healthy"
        except Exception:
            db_healthy = False

        try:
            await cache.set("health_check_status", "ok", ttl=10)
            cache_result = await cache.get("health_check_status")
            cache_healthy = cache_result == "ok"
        except Exception:
            cache_healthy = False

        if db_healthy and cache_healthy:
            status = "healthy"
        elif db_healthy or cache_healthy:
            status = "degraded"
        else:
            status = "unhealthy"

        status_map = {
            "healthy": ("Service 6 is running normally", 200),
            "degraded": ("Service 6 is running with some issues", 200),
            "unhealthy": ("Service 6 has significant issues", 503),
            "critical": ("Service 6 is not functioning properly", 503),
        }

        message, status_code = status_map.get(status, ("Unknown status", 500))

        response_data = {
            "message": message,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": time.time() - _service_start_time,
            "version": "1.0.0",
        }

        return JSONResponse(content=response_data, status_code=status_code)

    except Exception as e:
        logger.error(f"Status endpoint failed: {e}")
        return JSONResponse(content={"message": "Service status check failed", "error": str(e)}, status_code=500)


@router.get("/circuit-breakers")
async def circuit_breaker_status(current_user: UserDep):
    """
    Get status of all circuit breakers protecting external service calls.

    Returns detailed metrics on circuit breaker states, failure counts,
    and response times for GHL, Retell, SendGrid, and Lyrio services.

    Circuit breaker states:
    - CLOSED: Normal operation, requests flowing through
    - OPEN: Service failures exceeded threshold, blocking requests
    - HALF_OPEN: Testing recovery, allowing limited requests
    """
    try:
        circuit_manager = get_circuit_manager()
        health_summary = circuit_manager.get_health_summary()
        all_stats = circuit_manager.get_all_stats()

        # Calculate overall health
        total_breakers = health_summary["total_breakers"]
        open_breakers = health_summary["states"].get("OPEN", 0)
        half_open_breakers = health_summary["states"].get("HALF_OPEN", 0)

        if open_breakers == 0 and half_open_breakers == 0:
            overall_status = "healthy"
        elif open_breakers > 0:
            overall_status = "degraded" if open_breakers < total_breakers else "critical"
        else:
            overall_status = "recovering"

        return {
            "overall_status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_circuit_breakers": total_breakers,
                "states": health_summary["states"],
                "total_requests": health_summary["total_requests"],
                "total_failures": health_summary["total_failures"],
                "success_rate": (
                    (health_summary["total_requests"] - health_summary["total_failures"])
                    / health_summary["total_requests"]
                    * 100
                    if health_summary["total_requests"] > 0
                    else 100
                ),
            },
            "circuit_breakers": all_stats,
            "recommendations": _generate_circuit_breaker_recommendations(all_stats),
        }

    except Exception as e:
        logger.error(f"Circuit breaker status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Circuit breaker status check failed: {str(e)}")


def _generate_circuit_breaker_recommendations(stats: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate recommendations based on circuit breaker stats"""
    recommendations = []

    for service_name, service_stats in stats.items():
        state = service_stats.get("state")
        success_rate = service_stats.get("success_rate", 1.0)
        circuit_opens = service_stats.get("stats", {}).get("circuit_opens", 0)

        if state == "open":
            recommendations.append(
                {
                    "service": service_name,
                    "severity": "critical",
                    "message": f"{service_name} circuit is OPEN - service is experiencing failures",
                    "action": f"Check {service_name} service health and connectivity",
                }
            )
        elif state == "half_open":
            recommendations.append(
                {
                    "service": service_name,
                    "severity": "warning",
                    "message": f"{service_name} circuit is HALF_OPEN - testing recovery",
                    "action": "Monitor closely for full recovery or reopening",
                }
            )
        elif success_rate < 0.95 and circuit_opens > 0:
            recommendations.append(
                {
                    "service": service_name,
                    "severity": "warning",
                    "message": f"{service_name} success rate is {success_rate * 100:.1f}% (opened {circuit_opens} times)",
                    "action": "Investigate intermittent failures",
                }
            )

    if not recommendations:
        recommendations.append(
            {
                "service": "all",
                "severity": "info",
                "message": "All circuit breakers are healthy",
                "action": "No action required",
            }
        )

    return recommendations
