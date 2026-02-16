"""FastAPI application entry point for RAG-as-a-Service."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rag_service.config import get_settings
from rag_service.multi_tenant.isolation import TenantMiddleware
from rag_service.multi_tenant.tenant_router import TenantRouter
from rag_service.api.documents import router as documents_router
from rag_service.api.queries import router as queries_router
from rag_service.api.collections import router as collections_router
from rag_service.api.tenants import router as tenants_router
from rag_service.api.auth import router as auth_router
from rag_service.api.billing import router as billing_router
from rag_service.api.teams import router as teams_router

logger = logging.getLogger(__name__)

settings = get_settings()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="RAG-as-a-Service",
        description="Multi-tenant hosted RAG platform with hybrid search, PII detection, and Stripe billing",
        version="0.1.0",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Tenant isolation middleware
    tenant_router = TenantRouter()
    app.add_middleware(TenantMiddleware, tenant_router=tenant_router)

    # Health check
    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "rag-as-a-service"}

    # API routes
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(documents_router, prefix="/api/v1/documents", tags=["documents"])
    app.include_router(queries_router, prefix="/api/v1/query", tags=["queries"])
    app.include_router(collections_router, prefix="/api/v1/collections", tags=["collections"])
    app.include_router(tenants_router, prefix="/api/v1/tenants", tags=["tenants"])
    app.include_router(billing_router, prefix="/api/v1/usage", tags=["billing"])
    app.include_router(teams_router, prefix="/api/v1/teams", tags=["teams"])

    return app


app = create_app()
