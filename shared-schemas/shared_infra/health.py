"""Health check endpoint factory for FastAPI applications."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from redis import asyncio as aioredis

logger = logging.getLogger(__name__)


def create_health_router(
    redis: aioredis.Redis | None = None,
    db_check: Any | None = None,
    service_name: str = "service",
) -> APIRouter:
    """Create a health check router with /health and /ready endpoints.

    Args:
        redis: Optional Redis connection to check.
        db_check: Optional async callable that returns True if DB is healthy.
        service_name: Name of the service for identification.

    Returns:
        FastAPI APIRouter with health check endpoints.
    """
    router = APIRouter(tags=["health"])

    @router.get("/health")
    async def health() -> dict:
        """Basic health check — is the process alive?"""
        return {"status": "healthy", "service": service_name}

    @router.get("/ready")
    async def ready() -> dict:
        """Readiness check — are dependencies available?"""
        checks: dict[str, str] = {}
        all_healthy = True

        if redis is not None:
            try:
                await redis.ping()
                checks["redis"] = "ok"
            except Exception as e:
                checks["redis"] = f"error: {e}"
                all_healthy = False

        if db_check is not None:
            try:
                result = await db_check()
                checks["database"] = "ok" if result else "error: check returned False"
                if not result:
                    all_healthy = False
            except Exception as e:
                checks["database"] = f"error: {e}"
                all_healthy = False

        return {
            "status": "ready" if all_healthy else "not_ready",
            "service": service_name,
            "checks": checks,
        }

    return router
