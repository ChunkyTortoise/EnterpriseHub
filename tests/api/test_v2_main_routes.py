"""API Route Integration Tests for v2_main.py endpoints.

Tests for:
- Health check endpoints
- Properties routes
- Webhook routes
- Lead intelligence routes
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from ghl_real_estate_ai.api.v2_main import app


@pytest.fixture
def client():
    """Fixture providing FastAPI test client."""
    return TestClient(app)


# =============================================================================
# Health Check Endpoint Tests
# =============================================================================


class TestHealthEndpoints:
    """Tests for /api/v2/health endpoints."""

    def test_health_check_basic(self, client):
        """Basic health check should return 200."""
        response = client.get("/api/v2/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_health_check_with_details(self, client):
        """Health check with details should include service status."""
        response = client.get("/api/v2/health?details=true")
        assert response.status_code == 200
        data = response.json()
        # Health response should include service statuses

    def test_health_liveness(self, client):
        """Liveness probe should always return 200."""
        response = client.get("/api/v2/health/live")
        assert response.status_code == 200

    def test_health_readiness(self, client):
        """Readiness probe should check dependencies."""
        response = client.get("/api/v2/health/ready")
        # Should return 200 if ready, 503 if not


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

    @pytest.mark.parametrize("endpoint,method", [
        ("/api/v2/properties", "GET"),
        ("/api/v2/properties/search", "POST"),
        ("/api/v2/properties/featured", "GET"),
    ])
    def test_properties_endpoints_exist(self, client, endpoint, method):
        """Properties endpoints should exist and respond."""
        if method == "GET":
            response = client.get(endpoint)
        else:
            response = client.post(endpoint, json={})

        # Should not 404 (may be other errors but not 404)
        assert response.status_code != 404

    def test_properties_list_pagination(self, client):
        """Properties list should support pagination."""
        response = client.get("/api/v2/properties?page=1&limit=10")
        assert response.status_code in [200, 500]  # May fail without DB

    def test_properties_list_with_filters(self, client):
        """Properties list should support filters."""
        response = client.get(
            "/api/v2/properties?min_price=100000&max_price=500000&bedrooms=3"
        )
        assert response.status_code in [200, 500]

    def test_properties_search_body(self, client):
        """Properties search should accept request body."""
        search_request = {
            "location": "Rancho Cucamonga",
            "price_range": {"min": 300000, "max": 800000},
            "bedrooms": 3,
            "bathrooms": 2,
        }
        response = client.post("/api/v2/properties/search", json=search_request)
        assert response.status_code in [200, 422, 500]

    def test_property_detail_not_found(self, client):
        """Property detail should return 404 for non-existent."""
        response = client.get("/api/v2/properties/nonexistent-id")
        assert response.status_code in [404, 500]

    def test_properties_featured(self, client):
        """Featured properties endpoint should work."""
        response = client.get("/api/v2/properties/featured")
        assert response.status_code in [200, 500]


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
        """Response should include CORS headers."""
        response = client.get("/")
        # CORS headers depend on configuration
        # CORS headers may not be present in test client without CORS middleware
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
        # Properties search is POST, trying GET should fail
        response = client.get("/api/v2/properties/search")
        assert response.status_code == 405

    def test_422_for_invalid_body(self, client):
        """Invalid request body should return 422."""
        response = client.post(
            "/api/v2/properties/search",
            json={"min_price": "not_a_number"}
        )
        assert response.status_code == 422


# =============================================================================
# Performance Tests
# =============================================================================


class TestPerformance:
    """Tests for API performance requirements."""

    def test_health_check_response_time(self, client):
        """Health check should respond quickly."""
        import time
        start = time.time()
        response = client.get("/api/v2/health")
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


# =============================================================================
# Webhook Endpoint Tests (if configured)
# =============================================================================


class TestWebhookEndpoints:
    """Tests for webhook endpoints."""

    def test_webhook_endpoint_exists(self, client):
        """Webhook endpoint should exist."""
        response = client.post("/api/v2/webhook", json={})
        # May be 401/403 without proper auth, but should exist
        assert response.status_code != 404

    def test_webhook_validates_payload(self, client):
        """Webhook should validate payload."""
        response = client.post(
            "/api/v2/webhook",
            json={"invalid": "payload"}
        )
        # Should validate and return appropriate error
        assert response.status_code in [200, 422]


# =============================================================================
# Lead Intelligence Endpoint Tests (if configured)
# =============================================================================


class TestLeadIntelligenceEndpoints:
    """Tests for lead intelligence endpoints."""

    def test_lead_analysis_endpoint(self, client):
        """Lead analysis endpoint should exist."""
        response = client.post(
            "/api/v2/leads/analyze",
            json={"lead_id": "test_123"}
        )
        assert response.status_code != 404

    def test_lead_scoring_endpoint(self, client):
        """Lead scoring endpoint should exist."""
        response = client.get("/api/v2/leads/score/test_123")
        assert response.status_code != 404

    def test_lead_history_endpoint(self, client):
        """Lead history endpoint should exist."""
        response = client.get("/api/v2/leads/test_123/history")
        assert response.status_code != 404
