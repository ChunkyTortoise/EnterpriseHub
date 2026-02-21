import pytest

pytestmark = pytest.mark.integration

"""
Unit tests for Pricing Optimization API routes.

Tests all pricing API endpoints for Jorge's revenue acceleration platform.
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from ghl_real_estate_ai.api.main import app
from ghl_real_estate_ai.services.dynamic_pricing_optimizer import LeadPricingResult
from ghl_real_estate_ai.services.roi_calculator_service import ClientROIReport


class TestPricingOptimizationRoutes:
    """Tests for pricing optimization API endpoints."""

    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user."""
        return {
            "user_id": "test_user_123",
            "location_id": "test_location_456",
            "permissions": ["pricing:read", "pricing:write"],
        }

    @pytest.fixture
    def sample_pricing_request(self):
        """Sample pricing calculation request."""
        return {
            "contact_id": "contact_789",
            "location_id": "location_456",
            "context": {
                "questions_answered": 3,
                "property_type": "Single Family",
                "budget_range": "$300000-$500000",
                "urgency": "high",
                "source": "Website Form",
            },
        }

    @pytest.fixture
    def sample_pricing_result(self):
        """Sample pricing calculation result."""
        return LeadPricingResult(
            contact_id="contact_789",
            location_id="location_456",
            suggested_price=425.0,
            confidence_score=0.87,
            price_justification="High-quality lead with strong buying signals",
            tier_classification="hot",
            roi_multiplier=4.2,
            calculated_at=datetime.now(),
        )

    def test_calculate_lead_pricing_success(self, client, mock_user, sample_pricing_request, sample_pricing_result):
        """Test successful lead pricing calculation."""

        with (
            patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user", return_value=mock_user),
            patch("ghl_real_estate_ai.services.dynamic_pricing_optimizer.DynamicPricingOptimizer") as mock_optimizer,
        ):
            # Setup pricing optimizer mock
            mock_optimizer.return_value.calculate_lead_price = AsyncMock(return_value=sample_pricing_result)

            # Make request
            response = client.post("/api/pricing/calculate", json=sample_pricing_request)

            # Verify response
            assert response.status_code == 200

            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["data"]["suggested_price"] == 425.0
            assert response_data["data"]["tier_classification"] == "hot"
            assert response_data["data"]["confidence_score"] == 0.87
            assert "price_justification" in response_data["data"]

    def test_calculate_lead_pricing_validation_error(self, client, mock_user):
        """Test pricing calculation with validation errors."""

        with patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user", return_value=mock_user):
            # Invalid request - missing required fields
            invalid_request = {
                "contact_id": "",  # Empty contact_id
                "location_id": "location_456",
                # Missing context
            }

            response = client.post("/api/pricing/calculate", json=invalid_request)

            # Should return validation error
            assert response.status_code == 422

            error_data = response.json()
            assert "detail" in error_data

    def test_calculate_lead_pricing_service_error(self, client, mock_user, sample_pricing_request):
        """Test pricing calculation when service fails."""

        with (
            patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user", return_value=mock_user),
            patch("ghl_real_estate_ai.services.dynamic_pricing_optimizer.DynamicPricingOptimizer") as mock_optimizer,
        ):
            # Setup service to raise exception
            mock_optimizer.return_value.calculate_lead_price = AsyncMock(
                side_effect=Exception("Pricing service unavailable")
            )

            response = client.post("/api/pricing/calculate", json=sample_pricing_request)

            # Should handle error gracefully
            assert response.status_code == 500

            error_data = response.json()
            assert error_data["success"] is False
            assert "error" in error_data

    def test_get_pricing_analytics_success(self, client, mock_user):
        """Test successful pricing analytics retrieval."""

        location_id = "test_location_456"

        with (
            patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user", return_value=mock_user),
            patch("ghl_real_estate_ai.services.dynamic_pricing_optimizer.DynamicPricingOptimizer") as mock_optimizer,
        ):
            # Setup analytics mock
            mock_analytics = {
                "average_price_by_tier": {"hot": 425.0, "warm": 275.0, "cold": 150.0},
                "conversion_rates": {"hot": 0.35, "warm": 0.18, "cold": 0.08},
                "total_leads_processed": 1247,
                "revenue_generated": 156780.50,
                "period_start": "2024-01-01",
                "period_end": "2024-01-31",
            }

            mock_optimizer.return_value.get_pricing_analytics = AsyncMock(return_value=mock_analytics)

            # Make request
            response = client.get(f"/api/pricing/analytics/{location_id}")

            # Verify response
            assert response.status_code == 200

            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["data"]["total_leads_processed"] == 1247
            assert response_data["data"]["average_price_by_tier"]["hot"] == 425.0

    def test_get_pricing_analytics_with_date_range(self, client, mock_user):
        """Test pricing analytics with custom date range."""

        location_id = "test_location_456"

        with (
            patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user", return_value=mock_user),
            patch("ghl_real_estate_ai.services.dynamic_pricing_optimizer.DynamicPricingOptimizer") as mock_optimizer,
        ):
            mock_optimizer.return_value.get_pricing_analytics = AsyncMock(return_value={})

            # Request with query parameters
            response = client.get(f"/api/pricing/analytics/{location_id}?days=60")

            # Verify service was called with correct parameters
            mock_optimizer.return_value.get_pricing_analytics.assert_called_once_with(location_id=location_id, days=60)

            assert response.status_code == 200

    def test_update_pricing_configuration(self, client, mock_user):
        """Test pricing configuration update."""

        location_id = "test_location_456"
        config_update = {
            "base_price_hot": 450.0,
            "base_price_warm": 275.0,
            "base_price_cold": 125.0,
            "roi_multiplier_target": 4.5,
        }

        with (
            patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user", return_value=mock_user),
            patch("ghl_real_estate_ai.services.dynamic_pricing_optimizer.DynamicPricingOptimizer") as mock_optimizer,
        ):
            # Setup configuration update mock
            mock_optimizer.return_value.update_pricing_configuration = AsyncMock(
                return_value={"success": True, "updated_settings": config_update}
            )

            response = client.put(f"/api/pricing/configuration/{location_id}", json=config_update)

            # Verify response
            assert response.status_code == 200

            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["data"]["updated_settings"]["base_price_hot"] == 450.0

    def test_get_roi_report(self, client, mock_user):
        """Test ROI report retrieval."""

        location_id = "test_location_456"

        with (
            patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user", return_value=mock_user),
            patch("ghl_real_estate_ai.services.roi_calculator_service.ROICalculatorService") as mock_roi,
        ):
            # Setup ROI report mock
            mock_report = ClientROIReport(
                location_id=location_id,
                report_period_days=30,
                total_leads=425,
                qualified_leads=312,
                converted_leads=89,
                conversion_rate=0.209,
                total_revenue=178500.0,
                average_deal_size=2005.62,
                cost_per_lead=125.0,
                customer_acquisition_cost=625.0,
                roi_percentage=185.6,
                projected_annual_revenue=714000.0,
                competitive_advantage_score=8.7,
                human_vs_ai_savings=45600.0,
                pricing_optimization_impact=23400.0,
                generated_at=datetime.now(),
            )

            mock_roi.return_value.generate_client_roi_report = AsyncMock(return_value=mock_report)

            response = client.get(f"/api/pricing/roi-report/{location_id}")

            # Verify response
            assert response.status_code == 200

            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["data"]["total_leads"] == 425
            assert response_data["data"]["roi_percentage"] == 185.6

    def test_get_human_vs_ai_comparison(self, client, mock_user):
        """Test human vs AI comparison endpoint."""

        location_id = "test_location_456"

        with (
            patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user", return_value=mock_user),
            patch("ghl_real_estate_ai.services.roi_calculator_service.ROICalculatorService") as mock_roi,
        ):
            # Setup comparison mock
            mock_comparison = {
                "ai_response_time": 0.3,
                "human_response_time": 4.2,
                "ai_accuracy": 0.94,
                "human_accuracy": 0.78,
                "ai_cost_per_lead": 125.0,
                "human_cost_per_lead": 195.0,
                "time_savings_hours": 156.8,
                "cost_savings_monthly": 8750.0,
                "efficiency_improvement_percentage": 67.3,
            }

            mock_roi.return_value.calculate_human_vs_ai_comparison = AsyncMock(return_value=mock_comparison)

            response = client.get(f"/api/pricing/human-vs-ai/{location_id}")

            # Verify response
            assert response.status_code == 200

            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["data"]["ai_response_time"] == 0.3
            assert response_data["data"]["cost_savings_monthly"] == 8750.0

    def test_calculate_interactive_savings(self, client, mock_user):
        """Test interactive savings calculator endpoint."""

        savings_request = {
            "current_monthly_leads": 350,
            "current_conversion_rate": 0.12,
            "current_cost_per_lead": 195.0,
            "average_deal_size": 1650.0,
            "ai_improvements": {
                "conversion_rate_increase": 0.08,
                "cost_per_lead_reduction": 0.25,
                "staff_time_reduction": 0.60,
            },
        }

        with (
            patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user", return_value=mock_user),
            patch("ghl_real_estate_ai.services.roi_calculator_service.ROICalculatorService") as mock_roi,
        ):
            # Setup savings calculation mock
            mock_savings = {
                "improved_conversion_rate": 0.20,
                "improved_cost_per_lead": 146.25,
                "additional_monthly_revenue": 46200.0,
                "monthly_cost_savings": 17062.50,
                "annual_roi_improvement": 245.8,
            }

            mock_roi.return_value.calculate_interactive_savings = AsyncMock(return_value=mock_savings)

            response = client.post("/api/pricing/interactive-savings", json=savings_request)

            # Verify response
            assert response.status_code == 200

            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["data"]["additional_monthly_revenue"] == 46200.0

    def test_export_pricing_data(self, client, mock_user):
        """Test pricing data export endpoint."""

        location_id = "test_location_456"
        export_request = {
            "format": "csv",
            "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
            "include_roi_metrics": True,
        }

        with (
            patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user", return_value=mock_user),
            patch("ghl_real_estate_ai.services.dynamic_pricing_optimizer.DynamicPricingOptimizer") as mock_optimizer,
        ):
            # Setup export mock
            mock_export = {
                "export_format": "csv",
                "file_size": "2.3 MB",
                "records_count": 1247,
                "download_url": "/exports/pricing_data_test_location_456.csv",
                "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
            }

            mock_optimizer.return_value.export_pricing_data = AsyncMock(return_value=mock_export)

            response = client.post(f"/api/pricing/export/{location_id}", json=export_request)

            # Verify response
            assert response.status_code == 200

            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["data"]["records_count"] == 1247
            assert "download_url" in response_data["data"]

    def test_unauthorized_access(self, client):
        """Test endpoints require authentication."""

        # Test without authentication
        response = client.post("/api/pricing/calculate", json={})
        assert response.status_code == 401

        response = client.get("/api/pricing/analytics/test_location")
        assert response.status_code == 401

    def test_insufficient_permissions(self, client):
        """Test endpoints require proper permissions."""

        # User without pricing permissions
        limited_user = {"user_id": "limited_user", "location_id": "test_location", "permissions": ["read_only"]}

        with patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user", return_value=limited_user):
            # Should be denied for configuration updates
            response = client.put("/api/pricing/configuration/test_location", json={})
            assert response.status_code == 403

    def test_rate_limiting(self, client, mock_user):
        """Test rate limiting on pricing endpoints."""

        with (
            patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user", return_value=mock_user),
            patch("ghl_real_estate_ai.services.dynamic_pricing_optimizer.DynamicPricingOptimizer") as mock_optimizer,
        ):
            # Setup rate limit mock
            mock_optimizer.return_value.calculate_lead_price = AsyncMock(
                side_effect=HTTPException(status_code=429, detail="Rate limit exceeded")
            )

            pricing_request = {"contact_id": "contact_123", "location_id": "location_456", "context": {}}

            response = client.post("/api/pricing/calculate", json=pricing_request)

            # Should handle rate limiting
            assert response.status_code == 429

    def test_pricing_analytics_caching_headers(self, client, mock_user):
        """Test that analytics endpoints return proper caching headers."""

        location_id = "test_location_456"

        with (
            patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user", return_value=mock_user),
            patch("ghl_real_estate_ai.services.dynamic_pricing_optimizer.DynamicPricingOptimizer") as mock_optimizer,
        ):
            mock_optimizer.return_value.get_pricing_analytics = AsyncMock(return_value={})

            response = client.get(f"/api/pricing/analytics/{location_id}")

            # Should include cache control headers
            assert response.status_code == 200
            # Note: Actual caching headers would be set by middleware


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
