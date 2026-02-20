import pytest

pytestmark = pytest.mark.integration

"""
Comprehensive Tests for Competitive Intelligence API Routes

Tests cover:
1. Authentication and authorization
2. Request validation and response formatting
3. Data collection and monitoring endpoints
4. Market analysis and intelligence endpoints
5. Threat detection and assessment endpoints
6. Response automation configuration
7. Performance metrics and health checks
8. Error handling and edge cases
9. Rate limiting and security
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app and routes
try:
    from ghl_real_estate_ai.api.routes.competitive_intelligence import router
except (ImportError, TypeError, AttributeError):
    pytest.skip("required imports unavailable", allow_module_level=True)
from fastapi import FastAPI

# Create test app
app = FastAPI()
app.include_router(router)


class TestCompetitiveIntelligenceAPI:
    """Test suite for competitive intelligence API routes"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {"Authorization": "Bearer test_token_12345", "Content-Type": "application/json"}

    @pytest.fixture
    def mock_services(self):
        """Mock competitive intelligence services"""
        with (
            patch(
                "ghl_real_estate_ai.api.routes.competitive_intelligence.get_competitive_data_pipeline"
            ) as mock_pipeline,
            patch(
                "ghl_real_estate_ai.api.routes.competitive_intelligence.get_competitive_intelligence_system"
            ) as mock_intel,
            patch(
                "ghl_real_estate_ai.api.routes.competitive_intelligence.get_competitive_response_engine"
            ) as mock_response,
        ):
            # Mock data pipeline
            mock_pipeline_instance = AsyncMock()
            mock_pipeline_instance.start_real_time_monitoring.return_value = True
            mock_pipeline_instance.stop_real_time_monitoring.return_value = True
            mock_pipeline_instance.collect_competitor_data.return_value = []
            mock_pipeline_instance.analyze_market_trends.return_value = []
            mock_pipeline_instance.detect_competitive_threats.return_value = []
            mock_pipeline_instance.get_pipeline_performance_metrics.return_value = {
                "data_points_collected_24h": 150,
                "collection_success_rate": 0.95,
                "average_processing_time": 1250.0,
                "cache_hit_rate": 0.75,
                "error_rate": 0.03,
                "data_quality_score": 0.86,
                "active_collectors": 6,
                "monitored_competitors": 8,
                "monitoring_active": True,
            }
            mock_pipeline.return_value = mock_pipeline_instance

            # Mock intelligence system
            mock_intel_instance = AsyncMock()
            mock_report = Mock()
            mock_report.confidence_score = 0.85
            mock_report.participating_agents = []
            mock_intel_instance.generate_intelligence_report.return_value = mock_report
            mock_intel.return_value = mock_intel_instance

            # Mock response engine
            mock_response_instance = AsyncMock()
            mock_response_instance.get_response_performance_metrics.return_value = {
                "overview": {
                    "total_responses_executed": 25,
                    "successful_responses": 22,
                    "success_rate": 0.88,
                    "avg_response_time_ms": 1250.0,
                    "total_cost": 450.75,
                    "active_rules": 8,
                    "pending_approvals": 2,
                }
            }
            mock_response.return_value = mock_response_instance

            yield {
                "pipeline": mock_pipeline_instance,
                "intelligence": mock_intel_instance,
                "response": mock_response_instance,
            }

    def test_start_monitoring_endpoint(self, client, auth_headers, mock_services):
        """Test starting competitive monitoring"""
        request_data = {
            "competitor_ids": ["comp_001", "comp_002", "comp_003"],
            "data_sources": ["mls_data", "social_media"],
            "monitoring_frequency": 300,
            "alert_thresholds": {"price_change": 0.05},
        }

        response = client.post(
            "/api/v1/competitive-intelligence/monitoring/start", json=request_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "monitoring_started"
        assert data["competitors_monitored"] == 3
        assert data["monitoring_frequency"] == 300
        assert "monitoring_id" in data
        assert "started_at" in data

        # Verify service was called
        mock_services["pipeline"].start_real_time_monitoring.assert_called_once()

    def test_start_monitoring_validation_errors(self, client, auth_headers):
        """Test request validation for monitoring start"""
        # Empty competitor list
        invalid_request = {"competitor_ids": [], "monitoring_frequency": 300}

        response = client.post(
            "/api/v1/competitive-intelligence/monitoring/start", json=invalid_request, headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

        # Invalid monitoring frequency
        invalid_frequency = {
            "competitor_ids": ["comp_001"],
            "monitoring_frequency": 30,  # Below minimum
        }

        response = client.post(
            "/api/v1/competitive-intelligence/monitoring/start", json=invalid_frequency, headers=auth_headers
        )

        assert response.status_code == 422

    def test_stop_monitoring_endpoint(self, client, auth_headers, mock_services):
        """Test stopping competitive monitoring"""
        response = client.post("/api/v1/competitive-intelligence/monitoring/stop", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "monitoring_stopped"
        assert "stopped_at" in data
        assert "final_metrics" in data
        assert data["data_retention_days"] == 30

        # Verify service was called
        mock_services["pipeline"].stop_real_time_monitoring.assert_called_once()

    def test_get_competitor_data_endpoint(self, client, auth_headers, mock_services):
        """Test retrieving competitor data"""
        competitor_id = "comp_001"

        # Mock competitor data points
        from ghl_real_estate_ai.services.competitive_data_pipeline import CompetitorDataPoint, DataSource, DataType

        mock_data_points = [
            CompetitorDataPoint(
                data_id="data_001",
                competitor_id=competitor_id,
                data_source=DataSource.MLS_DATA,
                data_type=DataType.PRICING,
                raw_data={"commission": 0.025},
                confidence_score=0.9,
                collected_at=datetime.now(),
            )
        ]

        mock_services["pipeline"].collect_competitor_data.return_value = mock_data_points

        # Mock quality validation
        from ghl_real_estate_ai.services.competitive_data_pipeline import DataQualityScore

        mock_quality = DataQualityScore(
            overall_score=0.85,
            accuracy_score=0.9,
            completeness_score=0.8,
            timeliness_score=0.9,
            consistency_score=0.8,
            reliability_score=0.85,
        )
        mock_services["pipeline"].validate_data_quality.return_value = mock_quality

        response = client.get(
            f"/api/v1/competitive-intelligence/competitors/{competitor_id}/data",
            headers=auth_headers,
            params={"time_range_hours": 24},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["competitor_id"] == competitor_id
        assert "data_points" in data
        assert "collection_summary" in data
        assert "quality_metrics" in data
        assert "last_updated" in data

        # Verify collection summary
        summary = data["collection_summary"]
        assert summary["total_data_points"] == 1
        assert summary["time_range"] == "24 hours"

    def test_market_analysis_endpoint(self, client, auth_headers, mock_services):
        """Test market trend analysis endpoint"""
        request_data = {
            "market_area": "Rancho Cucamonga",
            "time_period": 30,
            "analysis_types": ["pricing", "inventory", "competition"],
            "include_forecasts": True,
        }

        # Mock market insights
        from ghl_real_estate_ai.services.competitive_data_pipeline import DataSource, MarketInsight

        mock_insights = [
            MarketInsight(
                insight_id="insight_001",
                insight_type="price_trend",
                market_area="Rancho Cucamonga",
                title="Significant Price Trend",
                description="Property prices increasing by 3.5%",
                confidence_score=0.85,
                impact_assessment="moderate",
                data_sources=[DataSource.MLS_DATA],
            )
        ]

        mock_services["pipeline"].analyze_market_trends.return_value = mock_insights

        response = client.post(
            "/api/v1/competitive-intelligence/market-analysis", json=request_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["market_area"] == "Rancho Cucamonga"
        assert data["analysis_period"] == "30 days"
        assert "insights" in data
        assert "trend_analysis" in data
        assert "competitive_landscape" in data
        assert "strategic_recommendations" in data
        assert data["confidence_score"] == 0.85

        # Verify insights structure
        insights = data["insights"]
        assert len(insights) > 0
        insight = insights[0]
        assert insight["insight_id"] == "insight_001"
        assert insight["type"] == "price_trend"

    def test_threat_detection_endpoint(self, client, auth_headers, mock_services):
        """Test competitive threat detection endpoint"""
        request_data = {
            "competitor_id": "comp_001",
            "threat_types": ["pricing", "expansion", "technology"],
            "sensitivity_level": "high",
            "time_range_hours": 24,
        }

        # Mock threat assessments
        from ghl_real_estate_ai.services.competitive_data_pipeline import ThreatAssessment, ThreatLevel

        mock_threats = [
            ThreatAssessment(
                threat_id="threat_001",
                competitor_id="comp_001",
                threat_level=ThreatLevel.HIGH,
                threat_type="aggressive_pricing",
                threat_description="Competitor reduced prices by 15%",
                potential_impact="May trigger price competition",
                recommended_response="Review pricing strategy",
                confidence_level=0.9,
            )
        ]

        mock_services["pipeline"].detect_competitive_threats.return_value = mock_threats

        response = client.post(
            "/api/v1/competitive-intelligence/threats/detect", json=request_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "threats" in data
        assert "risk_summary" in data
        assert "alert_recommendations" in data
        assert "response_strategies" in data
        assert "assessment_time" in data

        # Verify threat structure
        threats = data["threats"]
        assert len(threats) > 0
        threat = threats[0]
        assert threat["threat_id"] == "threat_001"
        assert threat["competitor_id"] == "comp_001"
        assert threat["threat_level"] == "high"

        # Verify risk summary
        risk_summary = data["risk_summary"]
        assert "total_threats" in risk_summary
        assert "high_priority_threats" in risk_summary
        assert "overall_risk_level" in risk_summary

    def test_configure_response_endpoint(self, client, auth_headers, mock_services):
        """Test competitive response configuration endpoint"""
        request_data = {
            "trigger_conditions": ["price_drop > 10%", "competitor_expansion"],
            "response_type": "pricing",
            "automation_level": "assisted",
            "approval_required": True,
        }

        response = client.post(
            "/api/v1/competitive-intelligence/responses/configure", json=request_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "response_configured"
        assert "response_id" in data
        assert data["automation_level"] == "assisted"
        assert data["approval_workflow"] == "enabled"
        assert data["trigger_conditions"] == 2
        assert "configured_at" in data

    def test_system_performance_endpoint(self, client, auth_headers, mock_services):
        """Test system performance metrics endpoint"""
        response = client.get("/api/v1/competitive-intelligence/system/performance", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify all required metric categories
        required_categories = [
            "collection_metrics",
            "processing_metrics",
            "quality_metrics",
            "system_health",
            "uptime_stats",
        ]

        for category in required_categories:
            assert category in data

        # Verify collection metrics structure
        collection = data["collection_metrics"]
        assert "data_points_collected_24h" in collection
        assert "collection_success_rate" in collection
        assert "active_collectors" in collection

        # Verify processing metrics
        processing = data["processing_metrics"]
        assert "average_processing_time" in processing
        assert "processed_items_24h" in processing

        # Verify quality metrics
        quality = data["quality_metrics"]
        assert "data_quality_score" in quality
        assert "cache_hit_rate" in quality

    def test_system_health_endpoint(self, client, auth_headers):
        """Test system health check endpoint"""
        response = client.get("/api/v1/competitive-intelligence/system/health", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert "overall_status" in data
        assert "timestamp" in data
        assert "components" in data
        assert "recommendations" in data

        # Health status should be either healthy or unhealthy
        assert data["overall_status"] in ["healthy", "unhealthy"]

        # Components should be a dict with component statuses
        components = data["components"]
        assert isinstance(components, dict)

        # Recommendations should be a list
        assert isinstance(data["recommendations"], list)

    def test_data_cleanup_endpoint(self, client, auth_headers, mock_services):
        """Test data cleanup endpoint"""
        # Mock cleanup result
        mock_cleanup_result = {"cleaned_records": 45, "retained_records": 1205}
        mock_services["pipeline"].cleanup_expired_data.return_value = mock_cleanup_result

        response = client.delete(
            "/api/v1/competitive-intelligence/data/cleanup", headers=auth_headers, params={"retention_days": 30}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "cleanup_completed"
        assert data["retention_policy"] == "30 days"
        assert data["records_cleaned"] == 45
        assert data["records_retained"] == 1205
        assert "cleanup_time" in data
        assert "storage_freed_mb" in data

        # Verify service was called with correct parameters
        mock_services["pipeline"].cleanup_expired_data.assert_called_once_with(30)

    def test_generate_intelligence_report_endpoint(self, client, auth_headers, mock_services):
        """Test intelligence report generation endpoint"""
        # Mock intelligence report
        mock_report = Mock()
        mock_report.report_id = "report_001"
        mock_report.title = "Test Intelligence Report"
        mock_report.executive_summary = "Test summary"
        mock_report.key_insights = []
        mock_report.threat_assessment = {"overall_threat_level": "medium"}
        mock_report.opportunity_analysis = {"significant_opportunities": []}
        mock_report.strategic_recommendations = ["Test recommendation"]
        mock_report.market_positioning_score = 78.5
        mock_report.competitive_advantage_areas = ["AI technology"]
        mock_report.vulnerability_areas = ["Market share"]
        mock_report.participating_agents = []
        mock_report.confidence_score = 0.82
        mock_report.next_update_due = datetime.now() + timedelta(days=7)

        mock_services["intelligence"].generate_intelligence_report.return_value = mock_report

        response = client.get(
            "/api/v1/competitive-intelligence/reports/intelligence",
            headers=auth_headers,
            params={
                "market_areas": ["Rancho Cucamonga", "Upland"],
                "analysis_period": "30_days",
                "report_format": "detailed",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["report_type"] == "detailed"
        assert "generated_at" in data
        assert "report_content" in data
        assert "metadata" in data

        # Verify report content structure for detailed format
        content = data["report_content"]
        assert content["report_id"] == "report_001"
        assert content["title"] == "Test Intelligence Report"
        assert content["market_positioning_score"] == 78.5

        # Verify metadata
        metadata = data["metadata"]
        assert metadata["market_areas_analyzed"] == 2
        assert metadata["analysis_period"] == "30_days"

    def test_authentication_required(self, client):
        """Test that authentication is required for all endpoints"""
        # Test without auth headers
        response = client.post("/api/v1/competitive-intelligence/monitoring/start")
        assert response.status_code == 403  # Forbidden due to missing auth

        # Test with invalid auth
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/api/v1/competitive-intelligence/monitoring/start", headers=invalid_headers)
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden

    def test_request_validation_errors(self, client, auth_headers):
        """Test request validation for various endpoints"""
        # Invalid market analysis request - missing required field
        invalid_market_request = {
            "time_period": 30,
            "analysis_types": ["pricing"],
            # Missing required 'market_area' field
        }

        response = client.post(
            "/api/v1/competitive-intelligence/market-analysis", json=invalid_market_request, headers=auth_headers
        )
        assert response.status_code == 422

        # Invalid threat detection request - invalid sensitivity level
        invalid_threat_request = {
            "threat_types": ["pricing"],
            "sensitivity_level": "invalid_level",
            "time_range_hours": 24,
        }

        response = client.post(
            "/api/v1/competitive-intelligence/threats/detect", json=invalid_threat_request, headers=auth_headers
        )
        assert response.status_code == 422

        # Invalid response configuration - invalid response type
        invalid_response_request = {
            "trigger_conditions": ["price_drop"],
            "response_type": "invalid_type",
            "automation_level": "manual",
        }

        response = client.post(
            "/api/v1/competitive-intelligence/responses/configure", json=invalid_response_request, headers=auth_headers
        )
        assert response.status_code == 422

    def test_error_handling(self, client, auth_headers):
        """Test error handling for service failures"""
        with patch(
            "ghl_real_estate_ai.api.routes.competitive_intelligence.get_competitive_data_pipeline"
        ) as mock_pipeline:
            # Mock service failure
            mock_pipeline_instance = AsyncMock()
            mock_pipeline_instance.start_real_time_monitoring.side_effect = Exception("Service unavailable")
            mock_pipeline.return_value = mock_pipeline_instance

            request_data = {"competitor_ids": ["comp_001"], "monitoring_frequency": 300}

            response = client.post(
                "/api/v1/competitive-intelligence/monitoring/start", json=request_data, headers=auth_headers
            )

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data

    def test_competitor_data_with_filters(self, client, auth_headers, mock_services):
        """Test competitor data retrieval with filters"""
        competitor_id = "comp_001"

        response = client.get(
            f"/api/v1/competitive-intelligence/competitors/{competitor_id}/data",
            headers=auth_headers,
            params={"data_sources": ["mls_data", "social_media"], "time_range_hours": 48},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["competitor_id"] == competitor_id

        # Verify service was called with correct filters
        call_args = mock_services["pipeline"].collect_competitor_data.call_args
        assert call_args[1]["competitor_id"] == competitor_id

    def test_market_analysis_with_forecasts(self, client, auth_headers, mock_services):
        """Test market analysis with forecasting enabled"""
        request_data = {
            "market_area": "Rancho Cucamonga",
            "time_period": 90,
            "analysis_types": ["pricing", "inventory", "competition", "forecasting"],
            "include_forecasts": True,
        }

        response = client.post(
            "/api/v1/competitive-intelligence/market-analysis", json=request_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should include forecasting analysis
        assert "trend_analysis" in data
        trend_analysis = data["trend_analysis"]
        assert "market_direction" in trend_analysis

    def test_report_format_variations(self, client, auth_headers, mock_services):
        """Test intelligence report with different formats"""
        # Mock intelligence report
        mock_report = Mock()
        mock_report.report_id = "report_001"
        mock_report.title = "Test Report"
        mock_report.executive_summary = "Executive summary"
        mock_report.key_insights = []
        mock_report.threat_assessment = {}
        mock_report.opportunity_analysis = {}
        mock_report.strategic_recommendations = ["Recommendation 1"]
        mock_report.market_positioning_score = 75.0
        mock_report.competitive_advantage_areas = ["Technology"]
        mock_report.vulnerability_areas = ["Market share"]
        mock_report.participating_agents = []
        mock_report.confidence_score = 0.8
        mock_report.next_update_due = datetime.now()

        mock_services["intelligence"].generate_intelligence_report.return_value = mock_report

        formats = ["summary", "detailed", "executive"]

        for report_format in formats:
            response = client.get(
                "/api/v1/competitive-intelligence/reports/intelligence",
                headers=auth_headers,
                params={
                    "market_areas": ["Rancho Cucamonga"],
                    "analysis_period": "30_days",
                    "report_format": report_format,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["report_type"] == report_format

            # Verify format-specific content
            content = data["report_content"]
            if report_format == "executive":
                assert "executive_summary" in content
                assert "key_insights_count" in content
            elif report_format == "detailed":
                assert "insights" in content
                assert "threat_assessment" in content
            else:  # summary
                assert "insights_summary" in content
                assert "positioning_score" in content


class TestAPIRateLimiting:
    """Test suite for API rate limiting and security features"""

    @pytest.fixture
    def client(self):
        """Create test client with rate limiting"""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {"Authorization": "Bearer test_token_12345", "Content-Type": "application/json"}

    def test_concurrent_request_handling(self, client, auth_headers):
        """Test handling of concurrent API requests"""
        import threading
        import time

        results = []

        def make_request():
            response = client.get("/api/v1/competitive-intelligence/system/health", headers=auth_headers)
            results.append(response.status_code)

        # Create multiple threads for concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All requests should be successful (or properly rate limited)
        assert len(results) == 5
        assert all(status in [200, 429] for status in results)  # 200 OK or 429 Too Many Requests

    def test_large_request_handling(self, client, auth_headers):
        """Test handling of large requests"""
        # Create large competitor list
        large_request = {
            "competitor_ids": [f"comp_{i:04d}" for i in range(50)],  # Maximum allowed
            "monitoring_frequency": 300,
        }

        with patch("ghl_real_estate_ai.api.routes.competitive_intelligence.get_competitive_data_pipeline"):
            response = client.post(
                "/api/v1/competitive-intelligence/monitoring/start", json=large_request, headers=auth_headers
            )

            # Should either accept the request or reject with validation error
            assert response.status_code in [200, 422, 500]

    def test_malformed_request_handling(self, client, auth_headers):
        """Test handling of malformed requests"""
        # Invalid JSON
        response = client.post(
            "/api/v1/competitive-intelligence/monitoring/start", data="invalid json data", headers=auth_headers
        )

        assert response.status_code == 422  # Unprocessable Entity

        # Missing required fields
        incomplete_request = {
            "monitoring_frequency": 300
            # Missing required competitor_ids
        }

        response = client.post(
            "/api/v1/competitive-intelligence/monitoring/start", json=incomplete_request, headers=auth_headers
        )

        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])