"""Security middleware tests for AI DevOps Suite."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from devops_suite.main import create_app


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
                    response.headers.get("access-control-allow-origin") == "https://app.example.com"
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
        with patch.dict(os.environ, {"API_KEYS": "test-key-123"}):
            app = create_app()
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/events")
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
                    "/api/v1/events",
                    headers={"X-API-Key": "wrong-key"},
                )
                assert response.status_code == 401
                data = response.json()
                assert data["error"] == "unauthorized"
                assert data["code"] == "AUTH_001"

    @pytest.mark.asyncio
    async def test_accepts_valid_api_key(self):
        with patch.dict(os.environ, {"API_KEYS": "test-key-123"}):
            app = create_app()
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/events",
                    headers={"X-API-Key": "test-key-123"},
                )
                assert response.status_code != 401

    @pytest.mark.asyncio
    async def test_no_keys_configured_allows_access(self, client):
        with patch.dict(os.environ, {"API_KEYS": ""}, clear=False):
            response = await client.get("/api/v1/events")
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
    async def test_error_response_format_matches_schema(self, app, client):
        """All error responses must have error, message, code, and request_id."""

        @app.get("/api/v1/test/schema-check")
        async def schema_boom():
            raise RuntimeError("schema test")

        response = await client.get("/api/v1/test/schema-check")
        data = response.json()
        required_keys = {"error", "message", "code", "request_id"}
        assert required_keys.issubset(data.keys())
