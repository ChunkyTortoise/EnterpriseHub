"""
Tests for Health Check API endpoints.

Endpoints tested:
    GET  /api/health/        - Basic liveness probe
    GET  /api/health/live    - Kubernetes liveness probe
    GET  /api/health/ready   - Readiness probe (auth required)
    GET  /api/health/metrics - Performance metrics (auth required)
    GET  /api/health/dependencies - Dependency status (auth required)
    GET  /api/health/status  - Human-readable status page
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MOCK_USER = {"user": {"id": "test-user"}, "session": {"permissions": []}}


def _make_client():
    """Create TestClient with main app."""
    from ghl_real_estate_ai.api.main import app

    return TestClient(app, raise_server_exceptions=False)


def _make_authed_client():
    """Create TestClient with enterprise auth overridden."""
    from ghl_real_estate_ai.api.enterprise.auth import enterprise_auth_service
    from ghl_real_estate_ai.api.main import app

    async def _fake_user():
        return _MOCK_USER

    app.dependency_overrides[enterprise_auth_service.get_current_enterprise_user] = _fake_user
    client = TestClient(app, raise_server_exceptions=False)
    return client


@pytest.fixture(autouse=True)
def _cleanup_overrides():
    """Clear dependency overrides after each test."""
    yield
    from ghl_real_estate_ai.api.main import app

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /api/health/ — Basic liveness probe
# ---------------------------------------------------------------------------


class TestBasicHealth:
    """Tests for the basic health endpoint."""

    def test_basic_health_all_healthy(self):
        """Returns 200 with healthy status when DB and cache are OK."""
        mock_db = AsyncMock()
        mock_db.health_check = AsyncMock(return_value={"status": "healthy"})

        mock_cache = MagicMock()
        mock_cache.set = AsyncMock()
        mock_cache.get = AsyncMock(return_value="ok")

        with (
            patch(
                "ghl_real_estate_ai.api.routes.health.get_database",
                new=AsyncMock(return_value=mock_db),
            ),
            patch(
                "ghl_real_estate_ai.api.routes.health.get_cache_service",
                return_value=mock_cache,
            ),
        ):
            client = _make_client()
            resp = client.get("/api/health/")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["checks"]["database"] == "healthy"
        assert data["checks"]["cache"] == "healthy"

    def test_basic_health_degraded_when_cache_down(self):
        """Returns degraded when cache fails but DB is ok."""
        mock_db = AsyncMock()
        mock_db.health_check = AsyncMock(return_value={"status": "healthy"})

        mock_cache = MagicMock()
        mock_cache.set = AsyncMock(side_effect=ConnectionError("cache down"))

        with (
            patch(
                "ghl_real_estate_ai.api.routes.health.get_database",
                new=AsyncMock(return_value=mock_db),
            ),
            patch(
                "ghl_real_estate_ai.api.routes.health.get_cache_service",
                return_value=mock_cache,
            ),
        ):
            client = _make_client()
            resp = client.get("/api/health/")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "degraded"

    def test_basic_health_unhealthy_when_all_down(self):
        """Returns unhealthy when both DB and cache are down."""
        mock_db = AsyncMock()
        mock_db.health_check = AsyncMock(side_effect=ConnectionError("db down"))

        mock_cache = MagicMock()
        mock_cache.set = AsyncMock(side_effect=ConnectionError("cache down"))

        with (
            patch(
                "ghl_real_estate_ai.api.routes.health.get_database",
                new=AsyncMock(return_value=mock_db),
            ),
            patch(
                "ghl_real_estate_ai.api.routes.health.get_cache_service",
                return_value=mock_cache,
            ),
        ):
            client = _make_client()
            resp = client.get("/api/health/")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "unhealthy"

    def test_basic_health_includes_uptime(self):
        """Response includes uptime_seconds field."""
        mock_db = AsyncMock()
        mock_db.health_check = AsyncMock(return_value={"status": "healthy"})
        mock_cache = MagicMock()
        mock_cache.set = AsyncMock()
        mock_cache.get = AsyncMock(return_value="ok")

        with (
            patch(
                "ghl_real_estate_ai.api.routes.health.get_database",
                new=AsyncMock(return_value=mock_db),
            ),
            patch(
                "ghl_real_estate_ai.api.routes.health.get_cache_service",
                return_value=mock_cache,
            ),
        ):
            client = _make_client()
            resp = client.get("/api/health/")

        data = resp.json()
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))


# ---------------------------------------------------------------------------
# GET /api/health/live — Kubernetes liveness probe
# ---------------------------------------------------------------------------


class TestLivenessProbe:
    """Tests for the liveness probe endpoint."""

    def test_liveness_returns_healthy(self):
        """Always returns healthy if process is running."""
        client = _make_client()
        resp = client.get("/api/health/live")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["checks"]["process"] == "running"

    def test_liveness_includes_uptime(self):
        """Liveness response includes uptime_seconds."""
        client = _make_client()
        resp = client.get("/api/health/live")
        data = resp.json()
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0


# ---------------------------------------------------------------------------
# GET /api/health/ready — Readiness probe (auth required)
# ---------------------------------------------------------------------------


class TestReadinessProbe:
    """Tests for the readiness probe endpoint."""

    def test_readiness_requires_auth(self):
        """Returns 401/403 when no auth header is provided."""
        client = _make_client()
        resp = client.get("/api/health/ready")
        assert resp.status_code in (401, 403)

    def test_readiness_returns_services(self):
        """Returns service list when authed and deps are mocked."""
        mock_db = AsyncMock()
        mock_db.health_check = AsyncMock(
            return_value={
                "status": "healthy",
                "response_time_seconds": 0.01,
                "pool_stats": {"size": 5, "idle": 3},
            }
        )
        mock_cache = MagicMock()
        mock_cache.set = AsyncMock()
        mock_cache.get = AsyncMock(return_value="ok")

        with (
            patch(
                "ghl_real_estate_ai.api.routes.health.get_database",
                new=AsyncMock(return_value=mock_db),
            ),
            patch(
                "ghl_real_estate_ai.api.routes.health.get_cache_service",
                return_value=mock_cache,
            ),
        ):
            client = _make_authed_client()
            resp = client.get("/api/health/ready")

        assert resp.status_code == 200
        data = resp.json()
        assert "overall_status" in data
        assert "services" in data
        assert len(data["services"]) >= 2


# ---------------------------------------------------------------------------
# GET /api/health/status — Human-readable status
# ---------------------------------------------------------------------------


class TestServiceStatus:
    """Tests for the human-readable service status endpoint."""

    def test_status_returns_message(self):
        """Returns human-readable status message."""
        mock_db = AsyncMock()
        mock_db.health_check = AsyncMock(return_value={"status": "healthy"})
        mock_cache = MagicMock()
        mock_cache.set = AsyncMock()
        mock_cache.get = AsyncMock(return_value="ok")

        with (
            patch(
                "ghl_real_estate_ai.api.routes.health.get_database",
                new=AsyncMock(return_value=mock_db),
            ),
            patch(
                "ghl_real_estate_ai.api.routes.health.get_cache_service",
                return_value=mock_cache,
            ),
        ):
            client = _make_client()
            resp = client.get("/api/health/status")

        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert "running normally" in data["message"]

    def test_status_returns_503_when_unhealthy(self):
        """Returns 503 when service is unhealthy."""
        mock_db = AsyncMock()
        mock_db.health_check = AsyncMock(side_effect=ConnectionError("db down"))
        mock_cache = MagicMock()
        mock_cache.set = AsyncMock(side_effect=ConnectionError("cache down"))

        with (
            patch(
                "ghl_real_estate_ai.api.routes.health.get_database",
                new=AsyncMock(return_value=mock_db),
            ),
            patch(
                "ghl_real_estate_ai.api.routes.health.get_cache_service",
                return_value=mock_cache,
            ),
        ):
            client = _make_client()
            resp = client.get("/api/health/status")

        assert resp.status_code == 503
        data = resp.json()
        assert data["status"] == "unhealthy"


# ---------------------------------------------------------------------------
# GET /api/health/metrics — Performance metrics (auth required)
# ---------------------------------------------------------------------------


class TestPerformanceMetrics:
    """Tests for the performance metrics endpoint."""

    def test_metrics_requires_auth(self):
        """Returns 401/403 when no auth header is provided."""
        client = _make_client()
        resp = client.get("/api/health/metrics")
        assert resp.status_code in (401, 403)

    def test_metrics_returns_performance_data(self):
        """Returns performance data when authed."""
        mock_monitoring = MagicMock()
        mock_monitoring.get_performance_summary = MagicMock(return_value={"avg_latency_ms": 45.0})
        mock_monitoring.check_sla_compliance = AsyncMock(return_value={"sla_met": True})

        mock_db = AsyncMock()
        mock_db.get_performance_metrics = AsyncMock(return_value={"query_count": 100})

        with (
            patch(
                "ghl_real_estate_ai.api.routes.health.get_monitoring_service",
                return_value=mock_monitoring,
            ),
            patch(
                "ghl_real_estate_ai.api.routes.health.get_database",
                new=AsyncMock(return_value=mock_db),
            ),
        ):
            client = _make_authed_client()
            resp = client.get("/api/health/metrics")

        assert resp.status_code == 200
        data = resp.json()
        assert "performance" in data
        assert "uptime_seconds" in data


# ---------------------------------------------------------------------------
# GET /api/health/dependencies — Dependency status (auth required)
# ---------------------------------------------------------------------------


class TestDependencyStatus:
    """Tests for the dependency status endpoint."""

    def test_dependencies_requires_auth(self):
        """Returns 401/403 when no auth header is provided."""
        client = _make_client()
        resp = client.get("/api/health/dependencies")
        assert resp.status_code in (401, 403)

    def test_dependencies_passes_auth_gate(self):
        """With valid auth the endpoint does not return 401/403."""
        client = _make_authed_client()
        resp = client.get("/api/health/dependencies")
        # Auth passed — endpoint may return 200 or 500 depending on infra deps
        assert resp.status_code not in (401, 403)
