"""
Test for comprehensive health check endpoint.

Following TDD RED → GREEN → REFACTOR methodology.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app
from ghl_real_estate_ai.api.main import app

@pytest.mark.integration

client = TestClient(app)


class TestHealthEndpoint:
    """Test the enhanced health check endpoint."""

    def test_should_return_healthy_status_with_basic_info(self):
        """
        RED PHASE: Write failing test first.

        Health endpoint should return comprehensive health information including:
        - Service status
        - Database connectivity
        - External service status
        - System metrics
        """
        # Arrange - No setup needed for basic test

        # Act
        response = client.get("/health")

        # Assert - Test current basic functionality
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data

    def test_should_include_database_health_check(self):
        """
        RED PHASE: This test will fail initially.

        Enhanced health check should verify database connectivity.
        """
        # Act
        response = client.get("/health")

        # Assert - This will fail initially
        data = response.json()
        assert "database" in data
        assert data["database"]["status"] in ["healthy", "unhealthy"]
        assert "connection_time_ms" in data["database"]

    def test_should_include_external_services_health(self):
        """
        RED PHASE: This test will fail initially.

        Health check should verify external service connectivity.
        """
        # Act
        response = client.get("/health")

        # Assert - This will fail initially
        data = response.json()
        assert "external_services" in data
        assert "ghl_api" in data["external_services"]
        assert "anthropic_api" in data["external_services"]

    def test_should_include_system_metrics(self):
        """
        RED PHASE: This test will fail initially.

        Health check should include basic system metrics.
        """
        # Act
        response = client.get("/health")

        # Assert - This will fail initially
        data = response.json()
        assert "system" in data
        assert "memory_usage_mb" in data["system"]
        assert "uptime_seconds" in data["system"]

    def test_should_return_unhealthy_when_database_fails(self):
        """
        RED PHASE: This test will fail initially.

        Health endpoint should return unhealthy status when database is unreachable.
        """
        with patch("ghl_real_estate_ai.api.routes.health.check_database_health") as mock_db:
            # Arrange
            mock_db.return_value = {"status": "unhealthy", "error": "Connection failed"}

            # Act
            response = client.get("/health")

            # Assert
            assert response.status_code == 503  # Service Unavailable
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["database"]["status"] == "unhealthy"

    def test_should_return_degraded_when_external_service_fails(self):
        """
        RED PHASE: This test will fail initially.

        Health endpoint should return degraded status when external services fail.
        """
        with patch("ghl_real_estate_ai.api.routes.health.check_external_services") as mock_external:
            # Arrange
            mock_external.return_value = {
                "ghl_api": {"status": "unhealthy", "error": "API timeout"},
                "anthropic_api": {"status": "healthy", "response_time_ms": 150},
            }

            # Act
            response = client.get("/health")

            # Assert
            assert response.status_code == 200  # Still OK but degraded
            data = response.json()
            assert data["status"] == "degraded"
            assert data["external_services"]["ghl_api"]["status"] == "unhealthy"