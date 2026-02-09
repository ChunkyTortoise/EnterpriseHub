"""
Health Check Functions for Dependency Injection

Provides health check functions for various services to ensure
proper operation and dependency resolution.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


async def repository_health_check(repository: "IPropertyRepository") -> Dict[str, Any]:
    """
    Health check for property repository services.

    Verifies that the repository is connected and can perform basic operations.
    """
    health_status = {
        "healthy": False,
        "service_name": repository.name,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {},
    }

    try:
        # Check 1: Connection status
        health_status["checks"]["connection"] = {
            "status": "pass" if repository.is_connected else "fail",
            "message": "Repository connection status",
            "connected": repository.is_connected,
        }

        # Check 2: Repository health check
        if hasattr(repository, "health_check"):
            repo_health = await repository.health_check()
            health_status["checks"]["repository_health"] = {
                "status": "pass" if repo_health.get("healthy", True) else "fail",
                "message": "Repository internal health check",
                "details": repo_health,
            }

        # Check 3: Basic query test (if connected)
        if repository.is_connected:
            try:
                from ..repositories.interfaces import PropertyQuery

                test_query = PropertyQuery()
                test_query.pagination.limit = 1

                start_time = time.time()
                result = await repository.find_properties(test_query)
                query_time = (time.time() - start_time) * 1000  # ms

                health_status["checks"]["query_test"] = {
                    "status": "pass" if result.success else "fail",
                    "message": "Basic query test",
                    "query_time_ms": query_time,
                    "result_count": result.count,
                    "errors": result.errors,
                }
            except Exception as e:
                health_status["checks"]["query_test"] = {
                    "status": "fail",
                    "message": "Basic query test failed",
                    "error": str(e),
                }

        # Check 4: Performance metrics
        if hasattr(repository, "get_performance_metrics"):
            try:
                metrics = repository.get_performance_metrics()
                health_status["checks"]["performance"] = {
                    "status": "pass",
                    "message": "Performance metrics available",
                    "metrics": metrics,
                }
            except Exception as e:
                health_status["checks"]["performance"] = {
                    "status": "warn",
                    "message": "Performance metrics unavailable",
                    "error": str(e),
                }

        # Overall health assessment
        failed_checks = sum(1 for check in health_status["checks"].values() if check["status"] == "fail")

        health_status["healthy"] = failed_checks == 0
        health_status["critical_failures"] = failed_checks

        if health_status["healthy"]:
            health_status["message"] = "All health checks passed"
        else:
            health_status["message"] = f"{failed_checks} health check(s) failed"

    except Exception as e:
        health_status["healthy"] = False
        health_status["message"] = f"Health check error: {str(e)}"
        health_status["error"] = str(e)

    return health_status


async def data_service_health_check(data_service: "PropertyDataService") -> Dict[str, Any]:
    """Health check for property data service"""
    health_status = {
        "healthy": False,
        "service_name": "PropertyDataService",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {},
    }

    try:
        # Check 1: Service availability
        health_status["checks"]["service_availability"] = {"status": "pass", "message": "Service is available"}

        # Check 2: Repository connections
        if hasattr(data_service, "get_health_status"):
            try:
                service_health = await data_service.get_health_status()
                health_status["checks"]["repositories"] = {
                    "status": "pass" if service_health.get("healthy", True) else "fail",
                    "message": "Repository health status",
                    "details": service_health,
                }
            except Exception as e:
                health_status["checks"]["repositories"] = {
                    "status": "fail",
                    "message": "Failed to check repository health",
                    "error": str(e),
                }

        # Check 3: Data loading test
        try:
            test_preferences = {"budget": 500000, "location": "austin", "bedrooms": 3}

            start_time = time.time()
            properties = await data_service.load_properties_for_strategy_pattern(test_preferences)
            load_time = (time.time() - start_time) * 1000  # ms

            health_status["checks"]["data_loading"] = {
                "status": "pass",
                "message": "Data loading test successful",
                "load_time_ms": load_time,
                "properties_loaded": len(properties) if properties else 0,
            }
        except Exception as e:
            health_status["checks"]["data_loading"] = {
                "status": "fail",
                "message": "Data loading test failed",
                "error": str(e),
            }

        # Overall health assessment
        failed_checks = sum(1 for check in health_status["checks"].values() if check["status"] == "fail")

        health_status["healthy"] = failed_checks == 0
        health_status["message"] = (
            "All checks passed" if health_status["healthy"] else f"{failed_checks} check(s) failed"
        )

    except Exception as e:
        health_status["healthy"] = False
        health_status["message"] = f"Health check error: {str(e)}"

    return health_status


def cache_backend_health_check(cache_backend) -> Dict[str, Any]:
    """Health check for cache backend services"""
    health_status = {
        "healthy": False,
        "service_name": cache_backend.__class__.__name__,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {},
    }

    try:
        # Check 1: Basic connectivity
        if hasattr(cache_backend, "_redis") and cache_backend._redis:
            # Redis backend
            try:
                cache_backend._redis.ping()
                health_status["checks"]["connectivity"] = {"status": "pass", "message": "Redis connection successful"}
            except Exception as e:
                health_status["checks"]["connectivity"] = {
                    "status": "fail",
                    "message": "Redis connection failed",
                    "error": str(e),
                }
        else:
            # Memory backend
            health_status["checks"]["connectivity"] = {"status": "pass", "message": "Memory cache available"}

        # Check 2: Cache operations
        try:
            test_key = f"health_check_{int(time.time())}"
            test_value = {"test": True, "timestamp": time.time()}

            # Test set operation
            cache_backend.set(test_key, test_value, ttl=60)

            # Test get operation
            retrieved_value = cache_backend.get(test_key)

            if retrieved_value and retrieved_value.get("test") == True:
                health_status["checks"]["cache_operations"] = {
                    "status": "pass",
                    "message": "Cache set/get operations successful",
                }
            else:
                health_status["checks"]["cache_operations"] = {
                    "status": "fail",
                    "message": "Cache get operation failed",
                }

            # Cleanup test key
            cache_backend.delete(test_key)

        except Exception as e:
            health_status["checks"]["cache_operations"] = {
                "status": "fail",
                "message": "Cache operations failed",
                "error": str(e),
            }

        # Check 3: Cache statistics (if available)
        if hasattr(cache_backend, "get_stats"):
            try:
                stats = cache_backend.get_stats()
                health_status["checks"]["cache_stats"] = {
                    "status": "pass",
                    "message": "Cache statistics available",
                    "stats": stats,
                }
            except Exception as e:
                health_status["checks"]["cache_stats"] = {
                    "status": "warn",
                    "message": "Cache statistics unavailable",
                    "error": str(e),
                }

        # Overall health assessment
        failed_checks = sum(1 for check in health_status["checks"].values() if check["status"] == "fail")

        health_status["healthy"] = failed_checks == 0
        health_status["message"] = (
            "All checks passed" if health_status["healthy"] else f"{failed_checks} check(s) failed"
        )

    except Exception as e:
        health_status["healthy"] = False
        health_status["message"] = f"Health check error: {str(e)}"

    return health_status


async def scoring_service_health_check(scoring_factory) -> Dict[str, Any]:
    """Health check for scoring services"""
    health_status = {
        "healthy": False,
        "service_name": "ScoringFactory",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {},
    }

    try:
        # Check 1: Factory availability
        health_status["checks"]["factory_availability"] = {"status": "pass", "message": "Scoring factory available"}

        # Check 2: Available strategies
        if hasattr(scoring_factory, "get_available_strategies"):
            try:
                strategies = scoring_factory.get_available_strategies()
                health_status["checks"]["strategies"] = {
                    "status": "pass",
                    "message": f"Found {len(strategies)} scoring strategies",
                    "strategies": strategies,
                }
            except Exception as e:
                health_status["checks"]["strategies"] = {
                    "status": "fail",
                    "message": "Failed to get available strategies",
                    "error": str(e),
                }

        # Check 3: Strategy creation test
        try:
            if hasattr(scoring_factory, "create_scorer"):
                scorer = scoring_factory.create_scorer("basic")
                health_status["checks"]["strategy_creation"] = {
                    "status": "pass",
                    "message": "Basic strategy creation successful",
                }
            else:
                health_status["checks"]["strategy_creation"] = {
                    "status": "warn",
                    "message": "Strategy creation method not available",
                }
        except Exception as e:
            health_status["checks"]["strategy_creation"] = {
                "status": "fail",
                "message": "Strategy creation failed",
                "error": str(e),
            }

        # Overall health assessment
        failed_checks = sum(1 for check in health_status["checks"].values() if check["status"] == "fail")

        health_status["healthy"] = failed_checks == 0
        health_status["message"] = (
            "All checks passed" if health_status["healthy"] else f"{failed_checks} check(s) failed"
        )

    except Exception as e:
        health_status["healthy"] = False
        health_status["message"] = f"Health check error: {str(e)}"

    return health_status


def configuration_service_health_check(config_service) -> Dict[str, Any]:
    """Health check for configuration service"""
    health_status = {
        "healthy": False,
        "service_name": "ConfigurationService",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {},
    }

    try:
        # Check 1: Service availability
        health_status["checks"]["service_availability"] = {
            "status": "pass",
            "message": "Configuration service available",
        }

        # Check 2: Configuration access
        try:
            test_key = "health_check.test"
            test_value = "test_value"

            config_service.set(test_key, test_value)
            retrieved_value = config_service.get(test_key)

            if retrieved_value == test_value:
                health_status["checks"]["config_access"] = {
                    "status": "pass",
                    "message": "Configuration get/set operations successful",
                }
            else:
                health_status["checks"]["config_access"] = {
                    "status": "fail",
                    "message": "Configuration retrieval failed",
                }

        except Exception as e:
            health_status["checks"]["config_access"] = {
                "status": "fail",
                "message": "Configuration access failed",
                "error": str(e),
            }

        # Check 3: Configuration count
        try:
            all_config = config_service.get_all()
            health_status["checks"]["config_count"] = {
                "status": "pass",
                "message": f"Configuration contains {len(all_config)} keys",
                "count": len(all_config),
            }
        except Exception as e:
            health_status["checks"]["config_count"] = {
                "status": "warn",
                "message": "Could not retrieve configuration count",
                "error": str(e),
            }

        # Overall health assessment
        failed_checks = sum(1 for check in health_status["checks"].values() if check["status"] == "fail")

        health_status["healthy"] = failed_checks == 0
        health_status["message"] = (
            "All checks passed" if health_status["healthy"] else f"{failed_checks} check(s) failed"
        )

    except Exception as e:
        health_status["healthy"] = False
        health_status["message"] = f"Health check error: {str(e)}"

    return health_status


async def container_health_check(container: "DIContainer") -> Dict[str, Any]:
    """
    Comprehensive health check for the entire DI container and all registered services.
    """
    health_status = {
        "healthy": False,
        "container_name": container.name,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {},
        "summary": {},
    }

    try:
        # Get container health
        container_health = container.get_health_status()
        health_status["container_health"] = container_health

        # Check each service
        service_health_results = {}
        total_services = 0
        healthy_services = 0

        for service_name, metadata in container._services.items():
            total_services += 1

            try:
                # Get service instance for health check
                service_instance = await container.get_service_async(metadata.service_type, service_name)

                # Run appropriate health check
                if metadata.health_check:
                    if asyncio.iscoroutinefunction(metadata.health_check):
                        service_health = await metadata.health_check(service_instance)
                    else:
                        service_health = metadata.health_check(service_instance)
                else:
                    # Default health check
                    service_health = {
                        "healthy": True,
                        "message": "No specific health check defined",
                        "service_name": service_name,
                    }

                service_health_results[service_name] = service_health

                if service_health.get("healthy", False):
                    healthy_services += 1

            except Exception as e:
                service_health_results[service_name] = {
                    "healthy": False,
                    "message": f"Health check failed: {str(e)}",
                    "error": str(e),
                }

        health_status["services"] = service_health_results

        # Summary
        health_status["summary"] = {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "unhealthy_services": total_services - healthy_services,
            "health_percentage": (healthy_services / total_services * 100) if total_services > 0 else 0,
        }

        # Overall container health
        health_status["healthy"] = healthy_services == total_services and not container._disposed

        if health_status["healthy"]:
            health_status["message"] = f"All {total_services} services are healthy"
        else:
            unhealthy_count = total_services - healthy_services
            health_status["message"] = f"{unhealthy_count} of {total_services} services are unhealthy"

    except Exception as e:
        health_status["healthy"] = False
        health_status["message"] = f"Container health check failed: {str(e)}"
        health_status["error"] = str(e)

    return health_status


# Health check registry for dynamic health check resolution
HEALTH_CHECK_REGISTRY = {
    "repository": repository_health_check,
    "data_service": data_service_health_check,
    "cache_backend": cache_backend_health_check,
    "scoring_service": scoring_service_health_check,
    "configuration_service": configuration_service_health_check,
    "container": container_health_check,
}


def get_health_check(name: str):
    """Get health check function by name"""
    if name not in HEALTH_CHECK_REGISTRY:
        raise ValueError(f"Unknown health check: {name}")
    return HEALTH_CHECK_REGISTRY[name]
