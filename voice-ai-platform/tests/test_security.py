"""Security middleware tests for Voice AI Platform."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from voice_ai.main import create_app


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
        # FastAPI CORS middleware omits the header for disallowed origins
        assert response.headers.get("access-control-allow-origin") != "http://evil.example.com"

    @pytest.mark.asyncio
    async def test_cors_respects_env_var(self):
        with patch.dict(
            os.environ, {"ALLOWED_ORIGINS": "https://app.example.com,https://admin.example.com"}
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
                    response.headers.get("access-control-allow-origin") == "https://app.example.com"
                )


class TestAPIKeyAuth:
    """API key middleware should enforce authentication when keys are configured."""

    @pytest.mark.asyncio
    async def test_health_excluded_from_auth(self, client):
        """Health endpoint should be accessible without API key."""
        with patch.dict(os.environ, {"API_KEYS": "test-key-123"}):
            app = create_app()
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/health")
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_docs_excluded_from_auth(self, client):
        """Docs endpoint should be accessible without API key."""
        with patch.dict(os.environ, {"API_KEYS": "test-key-123"}):
            app = create_app()
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/docs")
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rejects_missing_api_key(self):
        with patch.dict(os.environ, {"API_KEYS": "test-key-123"}):
            app = create_app()
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/calls")
                assert response.status_code == 401
                data = response.json()
                assert data["error"] == "unauthorized"
                assert data["code"] == "AUTH_001"
                assert "Invalid or missing API key" in data["message"]

    @pytest.mark.asyncio
    async def test_rejects_invalid_api_key(self):
        with patch.dict(os.environ, {"API_KEYS": "test-key-123"}):
            app = create_app()
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/calls",
                    headers={"X-API-Key": "wrong-key"},
                )
                assert response.status_code == 401
                data = response.json()
                assert data["error"] == "unauthorized"
                assert data["code"] == "AUTH_001"
                assert "Invalid or missing API key" in data["message"]

    @pytest.mark.asyncio
    async def test_accepts_valid_api_key(self):
        with patch.dict(os.environ, {"API_KEYS": "test-key-123,another-key"}):
            app = create_app()
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/calls",
                    headers={"X-API-Key": "test-key-123"},
                )
                # Should not be 401 — may be 200, 404, etc. depending on route logic
                assert response.status_code != 401

    @pytest.mark.asyncio
    async def test_no_keys_configured_allows_access(self, client):
        """When API_KEYS is empty, all requests pass through (dev mode)."""
        with patch.dict(os.environ, {"API_KEYS": ""}, clear=False):
            response = await client.get("/api/v1/calls")
            assert response.status_code != 401


class TestErrorStandardization:
    """Error responses should follow the unified schema."""

    @pytest.mark.asyncio
    async def test_404_returns_standard_error(self, client):
        response = await client.get("/api/v1/nonexistent-route")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "message" in data
        assert "code" in data
        assert "request_id" in data
        assert data["error"] == "not_found"
        assert data["code"] == 404

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
        assert data["code"] == 500

    @pytest.mark.asyncio
    async def test_validation_error_returns_422(self, client):
        # POST to calls/outbound without required body
        response = await client.post("/api/v1/calls/outbound", json={})
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "validation_error"
        assert data["code"] == 422
        assert "request_id" in data


class TestStripeWebhook:
    """Stripe webhook should verify signatures."""

    @pytest.mark.asyncio
    async def test_stripe_webhook_rejects_missing_secret(self, client):
        """Webhook should return 500 if STRIPE_WEBHOOK_SECRET is not set."""
        with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": ""}, clear=False):
            response = await client.post(
                "/api/v1/webhooks/stripe",
                content=b"{}",
                headers={"stripe-signature": "fake"},
            )
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_stripe_webhook_rejects_invalid_signature(self):
        with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": "whsec_test123"}):
            app = create_app()
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/webhooks/stripe",
                    content=b'{"type": "test"}',
                    headers={"stripe-signature": "t=123,v1=invalid"},
                )
                assert response.status_code == 400
