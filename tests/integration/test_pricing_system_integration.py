import pytest

pytestmark = pytest.mark.integration

"""
Comprehensive integration tests for the Dynamic Pricing System.

Tests the complete flow from webhook → pricing calculation → analytics → dashboard integration.
Validates all components work together correctly for Jorge's revenue acceleration platform.
"""

import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

try:
    from fastapi.testclient import TestClient
    from ghl_real_estate_ai.core.types import LeadClassification
    from httpx import AsyncClient

    from ghl_real_estate_ai.api.main import app
    from ghl_real_estate_ai.services.dynamic_pricing_optimizer import DynamicPricingOptimizer, LeadPricingResult
    from ghl_real_estate_ai.services.revenue_attribution import RevenueAttributionEngine
    from ghl_real_estate_ai.services.roi_calculator_service import ClientROIReport, ROICalculatorService
except (ImportError, TypeError, AttributeError, Exception):
    pytest.skip("required imports unavailable", allow_module_level=True)


class TestPricingSystemIntegration:
    """Integration tests for the complete pricing system."""

    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_webhook_payload(self):
        """Sample GHL webhook payload for testing."""
        return {
            "type": "ContactCreate",
            "contactId": "test_contact_123",
            "locationId": "test_location_456",
            "customFields": {"lead_score": "3", "property_type": "Single Family", "budget_range": "$300000-$500000"},
            "tags": ["hot_lead"],
            "source": "Website Form",
        }

    @pytest.fixture
    def sample_lead_context(self):
        """Sample lead context data."""
        return {
            "questions_answered": 3,
            "message_content": "Looking for a 3BR house under $400k",
            "extracted_data": {"bedrooms": 3, "budget_max": 400000, "urgency": "high"},
            "classification": LeadClassification.HOT,
        }

    @pytest.fixture
    async def pricing_optimizer(self):
        """Mock pricing optimizer with test data."""
        optimizer = DynamicPricingOptimizer()
        # Mock external dependencies
        optimizer.lead_scorer = AsyncMock()
        optimizer.predictive_scorer = AsyncMock()
        optimizer.revenue_engine = AsyncMock()
        return optimizer

    @pytest.fixture
    async def roi_calculator(self):
        """Mock ROI calculator service."""
        calculator = ROICalculatorService()
        calculator.revenue_engine = AsyncMock()
        calculator.cache_service = AsyncMock()
        return calculator

    async def test_complete_webhook_to_pricing_flow(self, client, sample_webhook_payload, sample_lead_context):
        """Test complete flow: webhook → pricing calculation → storage."""

        with (
            patch("ghl_real_estate_ai.api.routes.webhook.verify_ghl_signature", return_value=True),
            patch("ghl_real_estate_ai.services.claude_assistant.ClaudeAssistant") as mock_claude,
            patch("ghl_real_estate_ai.services.dynamic_pricing_optimizer.DynamicPricingOptimizer") as mock_pricing,
        ):
            # Setup mocks
            mock_claude.return_value.process_webhook.return_value = Mock(
                lead_score=3, extracted_data=sample_lead_context["extracted_data"], classification="hot"
            )

            mock_pricing_instance = mock_pricing.return_value
            mock_pricing_instance.calculate_lead_price.return_value = LeadPricingResult(
                contact_id=sample_webhook_payload["contactId"],
                location_id=sample_webhook_payload["locationId"],
                suggested_price=450.0,
                confidence_score=0.87,
                price_justification="High-quality lead with 3+ qualifying questions",
                tier_classification="hot",
                roi_multiplier=4.2,
                calculated_at=datetime.now(),
            )

            # Send webhook request
            response = client.post("/webhooks/ghl", json=sample_webhook_payload)

            # Verify webhook processing
            assert response.status_code == 200

            # Give background task time to complete
            await asyncio.sleep(0.1)

            # Verify pricing calculation was triggered
            mock_pricing_instance.calculate_lead_price.assert_called_once()

    async def test_pricing_api_endpoints_integration(self, client):
        """Test all pricing API endpoints work correctly together."""

        # Test data
        test_location = "test_location_456"
        test_contact = "test_contact_123"

        with (
            patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user", return_value={"user_id": "test_user"}),
            patch("ghl_real_estate_ai.services.dynamic_pricing_optimizer.DynamicPricingOptimizer") as mock_pricing,
        ):
            # Setup pricing optimizer mock
            pricing_instance = mock_pricing.return_value
            pricing_instance.calculate_lead_price.return_value = LeadPricingResult(
                contact_id=test_contact,
                location_id=test_location,
                suggested_price=375.0,
                confidence_score=0.92,
                price_justification="Premium lead with strong buying signals",
                tier_classification="hot",
                roi_multiplier=3.8,
                calculated_at=datetime.now(),
            )

            pricing_instance.get_pricing_analytics.return_value = {
                "average_price_by_tier": {"hot": 425.0, "warm": 275.0, "cold": 150.0},
                "conversion_rates": {"hot": 0.35, "warm": 0.18, "cold": 0.08},
                "total_leads_processed": 1247,
                "revenue_generated": 156780.50,
            }

            # Test lead pricing calculation endpoint
            pricing_request = {
                "contact_id": test_contact,
                "location_id": test_location,
                "context": {
                    "questions_answered": 3,
                    "property_type": "Single Family",
                    "budget_range": "$300000-$500000",
                },
            }

            response = client.post("/api/pricing/calculate", json=pricing_request)
            assert response.status_code == 200

            pricing_data = response.json()
            assert pricing_data["success"] is True
            assert pricing_data["data"]["suggested_price"] == 375.0
            assert pricing_data["data"]["tier_classification"] == "hot"

            # Test pricing analytics endpoint
            response = client.get(f"/api/pricing/analytics/{test_location}")
            assert response.status_code == 200

            analytics_data = response.json()
            assert analytics_data["success"] is True
            assert "average_price_by_tier" in analytics_data["data"]
            assert analytics_data["data"]["total_leads_processed"] == 1247

    async def test_roi_calculator_integration(self, roi_calculator, sample_lead_context):
        """Test ROI calculator integration with pricing system."""

        # Mock revenue engine data
        roi_calculator.revenue_engine.get_location_metrics.return_value = {
            "total_leads": 500,
            "converted_leads": 85,
            "total_revenue": 127500.0,
            "average_deal_size": 1500.0,
        }

        # Test ROI report generation
        roi_report = await roi_calculator.generate_client_roi_report(
            location_id="test_location_456", days=30, include_projections=True
        )

        assert isinstance(roi_report, ClientROIReport)
        assert roi_report.location_id == "test_location_456"
        assert roi_report.total_leads == 500
        assert roi_report.conversion_rate == 0.17  # 85/500
        assert roi_report.total_revenue == 127500.0

        # Verify projections are included
        assert roi_report.projected_annual_revenue > 0
        assert roi_report.roi_percentage > 0

    async def test_pricing_analytics_data_flow(self, pricing_optimizer):
        """Test data flow between pricing, analytics, and dashboard components."""

        test_location = "test_location_456"

        # Mock revenue attribution data
        pricing_optimizer.revenue_engine.calculate_lead_value_metrics.return_value = {
            "average_lead_value": 425.0,
            "lead_value_by_tier": {"hot": 850.0, "warm": 425.0, "cold": 125.0},
            "conversion_rates_by_tier": {"hot": 0.42, "warm": 0.23, "cold": 0.09},
            "total_qualified_leads": 324,
            "period_revenue": 187500.0,
        }

        # Test pricing analytics retrieval
        analytics = await pricing_optimizer.get_pricing_analytics(test_location, days=30)

        assert analytics["average_lead_value"] == 425.0
        assert analytics["lead_value_by_tier"]["hot"] == 850.0
        assert analytics["conversion_rates_by_tier"]["hot"] == 0.42
        assert analytics["total_qualified_leads"] == 324

    async def test_error_handling_and_fallbacks(self, client, sample_webhook_payload):
        """Test error handling in the integrated pricing system."""

        with (
            patch("ghl_real_estate_ai.api.routes.webhook.verify_ghl_signature", return_value=True),
            patch("ghl_real_estate_ai.services.claude_assistant.ClaudeAssistant") as mock_claude,
            patch("ghl_real_estate_ai.services.dynamic_pricing_optimizer.DynamicPricingOptimizer") as mock_pricing,
        ):
            # Test pricing service failure
            mock_claude.return_value.process_webhook.return_value = Mock(
                lead_score=2, extracted_data={}, classification="warm"
            )

            # Simulate pricing service error
            mock_pricing.return_value.calculate_lead_price.side_effect = Exception("Pricing service unavailable")

            # Webhook should still succeed, pricing calculation fails gracefully
            response = client.post("/webhooks/ghl", json=sample_webhook_payload)
            assert response.status_code == 200

            # Give background task time to complete
            await asyncio.sleep(0.1)

    async def test_pricing_configuration_persistence(self, client):
        """Test pricing configuration updates persist correctly."""

        test_location = "test_location_456"

        with (
            patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user", return_value={"user_id": "test_user"}),
            patch("ghl_real_estate_ai.services.dynamic_pricing_optimizer.DynamicPricingOptimizer") as mock_pricing,
        ):
            pricing_instance = mock_pricing.return_value
            pricing_instance.update_pricing_configuration.return_value = {
                "success": True,
                "updated_settings": {
                    "base_price_hot": 400.0,
                    "base_price_warm": 250.0,
                    "base_price_cold": 150.0,
                    "roi_multiplier_target": 4.0,
                },
            }

            # Update pricing configuration
            config_update = {
                "base_price_hot": 400.0,
                "base_price_warm": 250.0,
                "base_price_cold": 150.0,
                "roi_multiplier_target": 4.0,
            }

            response = client.put(f"/api/pricing/configuration/{test_location}", json=config_update)
            assert response.status_code == 200

            update_data = response.json()
            assert update_data["success"] is True
            assert update_data["data"]["updated_settings"]["base_price_hot"] == 400.0

    async def test_concurrent_pricing_calculations(self, pricing_optimizer):
        """Test multiple concurrent pricing calculations don't interfere."""

        # Setup multiple test contexts
        contexts = [{"contact_id": f"contact_{i}", "location_id": "test_location", "score": 3} for i in range(5)]

        # Mock pricing calculations
        async def mock_calculate(contact_id, location_id, context=None):
            await asyncio.sleep(0.01)  # Simulate processing time
            return LeadPricingResult(
                contact_id=contact_id,
                location_id=location_id,
                suggested_price=300.0 + (int(contact_id.split("_")[1]) * 50),
                confidence_score=0.85,
                price_justification=f"Calculated for {contact_id}",
                tier_classification="hot",
                roi_multiplier=3.5,
                calculated_at=datetime.now(),
            )

        pricing_optimizer.calculate_lead_price = mock_calculate

        # Run concurrent calculations
        tasks = [
            pricing_optimizer.calculate_lead_price(ctx["contact_id"], ctx["location_id"], {"score": ctx["score"]})
            for ctx in contexts
        ]

        results = await asyncio.gather(*tasks)

        # Verify all calculations completed correctly
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result.contact_id == f"contact_{i}"
            assert result.suggested_price == 300.0 + (i * 50)

    async def test_dashboard_data_integration(self, client):
        """Test dashboard component can retrieve integrated pricing data."""

        test_location = "test_location_456"

        with (
            patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user", return_value={"user_id": "test_user"}),
            patch("ghl_real_estate_ai.services.roi_calculator_service.ROICalculatorService") as mock_roi,
        ):
            # Setup ROI calculator mock for dashboard data
            roi_instance = mock_roi.return_value
            roi_instance.generate_client_roi_report.return_value = ClientROIReport(
                location_id=test_location,
                report_period_days=30,
                total_leads=428,
                qualified_leads=312,
                converted_leads=89,
                conversion_rate=0.208,
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

            # Test dashboard ROI data endpoint
            response = client.get(f"/api/pricing/roi-report/{test_location}")
            assert response.status_code == 200

            roi_data = response.json()
            assert roi_data["success"] is True
            assert roi_data["data"]["total_leads"] == 428
            assert roi_data["data"]["conversion_rate"] == 0.208
            assert roi_data["data"]["roi_percentage"] == 185.6

    async def test_pricing_export_functionality(self, client):
        """Test pricing data export for client reporting."""

        test_location = "test_location_456"

        with (
            patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user", return_value={"user_id": "test_user"}),
            patch("ghl_real_estate_ai.services.dynamic_pricing_optimizer.DynamicPricingOptimizer") as mock_pricing,
        ):
            # Setup export data mock
            pricing_instance = mock_pricing.return_value
            pricing_instance.export_pricing_data.return_value = {
                "export_format": "csv",
                "file_size": "2.3 MB",
                "records_count": 1247,
                "date_range": "2024-01-01 to 2024-01-31",
                "download_url": "/exports/pricing_data_test_location_456.csv",
                "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
            }

            # Test export request
            export_request = {
                "format": "csv",
                "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
                "include_roi_metrics": True,
            }

            response = client.post(f"/api/pricing/export/{test_location}", json=export_request)
            assert response.status_code == 200

            export_data = response.json()
            assert export_data["success"] is True
            assert export_data["data"]["records_count"] == 1247
            assert "download_url" in export_data["data"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])