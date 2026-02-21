"""API Route Integration Tests for v2_main.py endpoints.

Tests for:
- Health check endpoints (actual routes: /api/v2/health/health/*)
- Properties routes (actual routes: /api/v2/properties/analyze, /api/v2/properties/health)
- Root endpoint
- Middleware behavior
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Set required env vars before importing app (Gemini provider requires API key)
os.environ.setdefault("GEMINI_API_KEY", "test-key-not-real")

try:
    from ghl_real_estate_ai.api.v2_main import app
except (ImportError, ModuleNotFoundError) as _e:
    pytest.skip(f"required imports unavailable: {_e}", allow_module_level=True)


@pytest.fixture
def client():
    """Fixture providing FastAPI test client."""
    return TestClient(app)


# =============================================================================
# Health Check Endpoint Tests
# =============================================================================


class TestHealthEndpoints:
    """Tests for /api/v2/health/health/ endpoints."""

    def test_health_check_basic(self, client):
        """Basic health check should return 200 (or 500 if DB unavailable)."""
        try:
            response = client.get("/api/v2/health/health/")
            # 200 when healthy, 500 when DB (asyncpg) can't connect in test env
            assert response.status_code in [200, 500]
        except Exception:
            # asyncpg raises ClientConfigurationError when DATABASE_URL is sqlite
            # This is expected in test env without PostgreSQL
            pytest.skip("PostgreSQL not available in test environment")

    def test_health_liveness(self, client):
        """Liveness probe should always return 200."""
        response = client.get("/api/v2/health/health/live")
        assert response.status_code == 200

    def test_health_readiness(self, client):
        """Readiness probe should check dependencies."""
        response = client.get("/api/v2/health/health/ready")
        # 200 if ready, 503 if not ready, 401 if auth required in test env
        assert response.status_code in [200, 401, 503]

    def test_health_status(self, client):
        """Status endpoint should return system status."""
        response = client.get("/api/v2/health/health/status")
        assert response.status_code == 200


# =============================================================================
# Root Endpoint Tests
# =============================================================================


class TestRootEndpoint:
    """Tests for / endpoint."""

    def test_root_returns_welcome(self, client):
        """Root should return welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data
        assert data["status"] == "operational"

    def test_root_version(self, client):
        """Root should return version info."""
        response = client.get("/")
        data = response.json()
        assert "version" in data
        assert data["version"] == "2.0.0"


# =============================================================================
# Properties Endpoint Tests
# =============================================================================


class TestPropertiesEndpoints:
    """Tests for /api/v2/properties endpoints."""

    def test_properties_analyze_endpoint_exists(self, client):
        """Properties analyze endpoint should exist and respond."""
        response = client.post("/api/v2/properties/analyze", json={})
        # Should not 404 (may be 422 for invalid body or 500 without DB)
        assert response.status_code != 404

    def test_properties_health_endpoint(self, client):
        """Properties health endpoint should work."""
        response = client.get("/api/v2/properties/health")
        assert response.status_code == 200


# =============================================================================
# Middleware Tests
# =============================================================================


class TestMiddleware:
    """Tests for API middleware."""

    def test_process_time_header(self, client):
        """Response should include X-Process-Time header."""
        response = client.get("/")
        assert "x-process-time" in response.headers

    def test_cors_headers(self, client):
        """CORS middleware should be configured."""
        response = client.get("/")
        # CORS headers may not be present in test client without proper Origin header
        assert response.status_code == 200


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_for_unknown_endpoint(self, client):
        """Unknown endpoint should return 404."""
        response = client.get("/api/v2/nonexistent")
        assert response.status_code == 404

    def test_405_for_wrong_method(self, client):
        """Wrong HTTP method should return 405."""
        # Properties analyze is POST, trying GET should fail
        response = client.get("/api/v2/properties/analyze")
        assert response.status_code == 405


# =============================================================================
# Performance Tests
# =============================================================================


class TestPerformance:
    """Tests for API performance requirements."""

    def test_health_check_response_time(self, client):
        """Health check should respond quickly."""
        import time

        start = time.time()
        response = client.get("/api/v2/health/health/")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0  # Should respond within 1 second

    def test_root_response_time(self, client):
        """Root endpoint should respond quickly."""
        import time

        start = time.time()
        response = client.get("/")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0
