"""Security middleware tests for RAG-as-a-Service."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from rag_service.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestCORSLockdown:
    """CORS should only allow configured origins."""

    @pytest.mark.asyncio
    async def test_cors_allows_configured_origin(self, client):
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

    @pytest.mark.asyncio
    async def test_cors_rejects_unknown_origin(self, client):
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://evil.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") != "http://evil.example.com"

    @pytest.mark.asyncio
    async def test_cors_respects_env_var(self):
        with patch.dict(
            os.environ,
            {"ALLOWED_ORIGINS": "https://app.example.com,https://admin.example.com"},
        ):
            app = create_app()
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.options(
                    "/health",
                    headers={
                        "Origin": "https://app.example.com",
                        "Access-Control-Request-Method": "GET",
                    },
                )
                assert (
                    response.headers.get("access-control-allow-origin")
                    == "https://app.example.com"
                )


class TestAPIKeyAuth:
    """API key middleware should enforce authentication when keys are configured."""

    @pytest.mark.asyncio
    async def test_health_excluded_from_auth(self):
        with patch.dict(os.environ, {"API_KEYS": "test-key-123"}):
            app = create_app()
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/health")
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_docs_excluded_from_auth(self):
        with patch.dict(os.environ, {"API_KEYS": "test-key-123"}):
            app = create_app()
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/docs")
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rejects_missing_api_key(self):
        """Request without API key should return 401."""
        with patch.dict(os.environ, {"API_KEYS": "test-key-123"}):
            app = create_app()
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/auth/keys")
                assert response.status_code == 401
                data = response.json()
                assert data["error"] == "unauthorized"
                assert data["code"] == "AUTH_001"
                assert "Invalid or missing API key" in data["message"]

    @pytest.mark.asyncio
    async def test_rejects_invalid_api_key(self):
        """Request with wrong API key should be rejected."""
        with patch.dict(os.environ, {"API_KEYS": "test-key-123"}):
            app = create_app()
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/auth/keys",
                    headers={"X-API-Key": "wrong-key"},
                )
                assert response.status_code == 401
                data = response.json()
                assert data["error"] == "unauthorized"
                assert data["code"] == "AUTH_001"

    @pytest.mark.asyncio
    async def test_no_keys_configured_allows_access(self, client):
        """When API_KEYS is empty, requests pass through to tenant middleware."""
        with patch.dict(os.environ, {"API_KEYS": ""}, clear=False):
            response = await client.get("/health")
            assert response.status_code == 200


class TestErrorStandardization:
    """Error responses should follow the unified schema."""

    @pytest.mark.asyncio
    async def test_health_returns_ok(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_500_returns_standard_error(self, app, client):
        @app.get("/api/v1/test/boom")
        async def boom():
            raise RuntimeError("test explosion")

        response = await client.get("/api/v1/test/boom")
        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "internal_server_error"
        assert "request_id" in data

    @pytest.mark.asyncio
    async def test_error_response_format_matches_schema(self, app, client):
        """All error responses must have error, message, code, and request_id."""

        @app.get("/api/v1/test/schema-check")
        async def schema_boom():
            raise RuntimeError("schema test")

        response = await client.get("/api/v1/test/schema-check")
        data = response.json()
        required_keys = {"error", "message", "code", "request_id"}
        assert required_keys.issubset(data.keys())


class TestStripeWebhook:
    """Stripe webhook should verify signatures."""

    @pytest.mark.asyncio
    async def test_stripe_webhook_rejects_missing_secret(self, client):
        with patch.dict(
            os.environ,
            {"STRIPE_WEBHOOK_SECRET": "", "RAG_STRIPE_WEBHOOK_SECRET": ""},
            clear=False,
        ):
            response = await client.post(
                "/api/v1/webhooks/stripe",
                content=b"{}",
                headers={"stripe-signature": "fake"},
            )
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_stripe_webhook_rejects_invalid_signature(self):
        """Webhook with bad signature should be rejected (400) when hitting endpoint directly."""
        with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": "whsec_test123"}):
            with patch(
                "rag_service.multi_tenant.tenant_router.TenantRouter.resolve_tenant",
                new_callable=AsyncMock,
                return_value={
                    "tenant_id": "test",
                    "schema_name": "test",
                    "tier": "starter",
                    "scopes": ["read"],
                },
            ):
                app = create_app()
                transport = ASGITransport(app=app, raise_app_exceptions=False)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/webhooks/stripe",
                        content=b'{"type": "test"}',
                        headers={
                            "stripe-signature": "t=123,v1=invalid",
                            "X-API-Key": "test-key",
                        },
                    )
                    assert response.status_code == 400
