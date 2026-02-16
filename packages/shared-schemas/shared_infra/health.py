"""Standard health check endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter


def create_health_router(
    db_check: Any | None = None,
    redis_check: Any | None = None,
) -> APIRouter:
    """Create a router with /health and /ready endpoints."""
    router = APIRouter(tags=["health"])

    @router.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/ready")
    async def ready() -> dict[str, Any]:
        checks: dict[str, str] = {}
        all_ok = True

        if db_check is not None:
            try:
                ok = await db_check()
                checks["database"] = "ok" if ok else "degraded"
                if not ok:
                    all_ok = False
            except Exception:
                checks["database"] = "degraded"
                all_ok = False

        if redis_check is not None:
            try:
                ok = await redis_check()
                checks["redis"] = "ok" if ok else "degraded"
                if not ok:
                    all_ok = False
            except Exception:
                checks["redis"] = "degraded"
                all_ok = False

        return {
            "status": "ready" if all_ok else "degraded",
            "checks": checks,
        }

    return router
