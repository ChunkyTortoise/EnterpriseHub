"""Unit tests for TenantMiddleware — tenant resolution, public paths, auth."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from starlette.middleware.base import BaseHTTPMiddleware

from rag_service.multi_tenant.isolation import TenantMiddleware, PUBLIC_PATHS
from rag_service.multi_tenant.tenant_router import TenantRouter


class TestPublicPaths:
    def test_health_is_public(self):
        assert "/health" in PUBLIC_PATHS

    def test_docs_is_public(self):
        assert "/docs" in PUBLIC_PATHS

    def test_openapi_is_public(self):
        assert "/openapi.json" in PUBLIC_PATHS

    def test_redoc_is_public(self):
        assert "/redoc" in PUBLIC_PATHS


class TestTenantMiddleware:
    @pytest.fixture
    def mock_router(self):
        return AsyncMock(spec=TenantRouter)

    @pytest.fixture
    def app(self, mock_router):
        app = FastAPI()

        # Add exception handler so HTTPException doesn't become 500
        @app.exception_handler(Exception)
        async def handle_exc(request: Request, exc):
            from fastapi import HTTPException
            if isinstance(exc, HTTPException):
                return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
            return JSONResponse(status_code=500, content={"detail": "Internal error"})

        app.add_middleware(TenantMiddleware, tenant_router=mock_router)

        @app.get("/health")
        async def health():
            return {"status": "ok"}

        @app.get("/api/v1/data")
        async def data(request: Request):
            return {
                "tenant_id": request.state.tenant_id,
                "tier": request.state.tenant_tier,
            }

        return app

    @pytest.mark.asyncio
    async def test_public_path_no_auth(self, app):
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/health")
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_missing_api_key_returns_401(self, app):
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/data")
            assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_api_key_returns_401(self, app, mock_router):
        mock_router.resolve_tenant.return_value = None
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/data", headers={"X-API-Key": "bad_key"})
            assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_api_key_passes_through(self, app, mock_router):
        mock_router.resolve_tenant.return_value = {
            "tenant_id": "t-123",
            "schema_name": "tenant_acme",
            "tier": "pro",
            "scopes": ["read", "write"],
        }
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/data", headers={"X-API-Key": "valid"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["tenant_id"] == "t-123"
            assert data["tier"] == "pro"

    @pytest.mark.asyncio
    async def test_auth_path_skips_tenant(self, app, mock_router):
        """Paths starting with /api/v1/auth should skip tenant resolution."""
        @app.get("/api/v1/auth/login")
        async def login():
            return {"ok": True}

        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/auth/login")
            assert resp.status_code == 200
