"""FastAPI application entry point for RAG-as-a-Service."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from rag_service.api.auth import router as auth_router
from rag_service.api.billing import router as billing_router
from rag_service.api.collections import router as collections_router
from rag_service.api.documents import router as documents_router
from rag_service.api.queries import router as queries_router
from rag_service.api.teams import router as teams_router
from rag_service.api.tenants import router as tenants_router
from rag_service.api.webhooks import router as webhooks_router
from rag_service.billing.quota_service import QuotaEnforcementMiddleware
from rag_service.billing.usage_tracker import UsageTracker
from rag_service.config import get_settings
from rag_service.logging_config import RequestLoggingMiddleware, get_logger, setup_logging
from rag_service.middleware.errors import register_error_handlers
from rag_service.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from rag_service.middleware.security import APIKeyMiddleware
from rag_service.middleware.security_headers import SecurityHeadersMiddleware
from rag_service.multi_tenant.isolation import TenantMiddleware
from rag_service.multi_tenant.tenant_router import TenantRouter

setup_logging()
logger = get_logger(__name__)

settings = get_settings()


def _parse_allowed_origins() -> list[str]:
    """Parse ALLOWED_ORIGINS from env var (comma-separated) or default to localhost."""
    raw = os.environ.get("ALLOWED_ORIGINS", "")
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    return ["http://localhost:3000"]


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="RAG-as-a-Service",
        description="Multi-tenant hosted RAG platform with hybrid search, PII detection, and Stripe billing",
        version="0.1.0",
    )

    # Rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # CORS — locked to ALLOWED_ORIGINS env var
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_parse_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API key authentication
    app.add_middleware(APIKeyMiddleware)

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Request logging (structured)
    app.add_middleware(RequestLoggingMiddleware)

    # Tenant isolation middleware
    tenant_router = TenantRouter()
    app.add_middleware(TenantMiddleware, tenant_router=tenant_router)

    # Usage tracker (in-memory fallback; Redis connected at startup in production)
    app.state.usage_tracker = UsageTracker()

    # Quota enforcement (checks tenant usage before resource-consuming requests)
    app.add_middleware(QuotaEnforcementMiddleware)

    # Standardized error handlers
    register_error_handlers(app)

    # Health check
    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/ready")
    async def readiness_check():
        checks: dict[str, str] = {}

        # Database check
        try:
            import asyncpg

            conn = await asyncpg.connect(
                settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
            )
            await conn.fetchval("SELECT 1")
            await conn.close()
            checks["database"] = "ok"
        except Exception:
            checks["database"] = "error"

        # Redis check
        try:
            import redis.asyncio as aioredis

            r = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
            await r.ping()
            await r.aclose()
            checks["redis"] = "ok"
        except Exception:
            checks["redis"] = "error"

        all_ok = all(v in ("ok", "not_configured") for v in checks.values())
        status_code = 200 if all_ok else 503
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=status_code,
            content={
                "status": "ready" if all_ok else "not_ready",
                "checks": checks,
            },
        )

    # API routes
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(documents_router, prefix="/api/v1/documents", tags=["documents"])
    app.include_router(queries_router, prefix="/api/v1/query", tags=["queries"])
    app.include_router(collections_router, prefix="/api/v1/collections", tags=["collections"])
    app.include_router(tenants_router, prefix="/api/v1/tenants", tags=["tenants"])
    app.include_router(billing_router, prefix="/api/v1/usage", tags=["billing"])
    app.include_router(teams_router, prefix="/api/v1/teams", tags=["teams"])
    app.include_router(webhooks_router, prefix="/api/v1/webhooks", tags=["webhooks"])

    return app


app = create_app()
