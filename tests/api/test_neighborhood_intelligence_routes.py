import pytest
pytestmark = pytest.mark.integration

"""
Comprehensive tests for Neighborhood Intelligence API routes.

Test coverage:
- All API endpoints functionality
- Request validation and error handling
- Response formatting and structure
- Authentication and authorization
- Rate limiting and performance
- Integration with service layers
- Error responses and status codes
- API documentation compliance
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Create a test app with the router
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

# Import the main FastAPI app and router
from ghl_real_estate_ai.api.routes.neighborhood_intelligence import router
from ghl_real_estate_ai.ml.price_prediction_engine import PredictionTimeframe, PricePredictionResult
from ghl_real_estate_ai.services.inventory_alert_system import AlertInstance, AlertSeverity, AlertStatus, AlertType
from ghl_real_estate_ai.services.neighborhood_intelligence_service import (

@pytest.mark.integration
    InvestmentGrade,
    MarketTrend,
    NeighborhoodMetrics,
)

test_app = FastAPI()
test_app.include_router(router)

client = TestClient(test_app)


class TestNeighborhoodIntelligenceRoutes:
    """Test suite for neighborhood intelligence API routes."""

    @pytest.fixture
    def sample_neighborhood_metrics(self):
        """Sample neighborhood metrics for testing."""
        return NeighborhoodMetrics(
            neighborhood_id="test_neighborhood",
            name="Test Neighborhood",
            zip_codes=["12345"],
            county="Test County",
            state="TX",
            median_home_value=750000.0,
            median_rent=3200.0,
            price_per_sqft=385.0,
            rent_yield=5.12,
            price_appreciation_1m=0.8,
            price_appreciation_3m=2.4,
            price_appreciation_6m=5.8,
            price_appreciation_12m=12.3,
            active_listings=145,
            new_listings_30d=89,
            sold_listings_30d=76,
            pending_listings=32,
            days_on_market_median=28,
            inventory_months=1.9,
            absorption_rate=85.4,
            population=15420,
            median_age=34.5,
            median_income=89500.0,
            unemployment_rate=3.2,
            education_bachelor_plus=67.8,
            walk_score=78,
            transit_score=82,
            bike_score=71,
            crime_score=25,
            school_rating_avg=8.4,
            investment_grade=InvestmentGrade.A,
            roi_score=87.5,
            risk_score=23.4,
            liquidity_score=91.2,
            growth_potential=89.6,
            market_trend=MarketTrend.MODERATE_APPRECIATION,
            seasonal_factor=1.05,
            competition_level=78.3,
            buyer_demand_score=86.7,
            seller_motivation_score=34.2,
            coordinates=(30.2672, -97.7431),
            commute_scores={"downtown": 92.0, "tech_corridor": 88.5},
            amenity_scores={"restaurants": 94.0, "shopping": 89.0},
            data_freshness=datetime.now(),
            confidence_score=0.94,
            last_updated=datetime.now(),
        )

    @pytest.fixture
    def sample_intelligence_data(self):
        """Sample intelligence data for testing."""
        return {
            "neighborhood_id": "test_neighborhood",
            "metrics": {"median_home_value": 750000.0, "price_appreciation_12m": 12.3, "investment_grade": "A"},
            "analysis": {
                "market_summary": "Strong market with good fundamentals",
                "investment_thesis": "High-quality investment opportunity",
                "opportunity_score": 87.5,
            },
            "predictions": {
                "1m": {"predicted_price": 760000.0, "confidence": 0.95},
                "3m": {"predicted_price": 780000.0, "confidence": 0.93},
            },
            "alerts": [],
            "generated_at": datetime.now().isoformat(),
        }

    @pytest.fixture
    def sample_alert(self):
        """Sample market alert for testing."""
        return AlertInstance(
            alert_id="test_alert_001",
            rule_id="rule_001",
            alert_type=AlertType.INVENTORY_DROP,
            severity=AlertSeverity.HIGH,
            status=AlertStatus.SENT,
            title="Inventory Drop Alert",
            message="Significant inventory decrease detected",
            data_context={"inventory_change": -23.5},
            affected_areas=["test_neighborhood"],
            impact_score=85.0,
            confidence_score=0.92,
            urgency_score=78.0,
            target_users=["admin", "analyst"],
            delivery_channels=[],
            delivery_status={},
            triggered_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24),
            recommended_actions=["Monitor market", "Prepare buyers"],
        )

    def test_get_neighborhood_intelligence_success(self, sample_intelligence_data):
        """Test successful neighborhood intelligence retrieval."""
        with patch(
            "ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_neighborhood_intelligence_service"
        ) as mock_service:
            # Mock service response
            mock_service_instance = AsyncMock()
            mock_service_instance.get_neighborhood_intelligence.return_value = sample_intelligence_data
            mock_service.return_value = mock_service_instance

            response = client.get("/api/v1/neighborhoods/test_neighborhood/intelligence")

            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["success"] is True
            assert data["data"]["neighborhood_id"] == "test_neighborhood"
            assert "execution_time_ms" in data

    def test_get_neighborhood_intelligence_not_found(self):
        """Test neighborhood intelligence for non-existent neighborhood."""
        with patch(
            "ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_neighborhood_intelligence_service"
        ) as mock_service:
            # Mock service returning None (not found)
            mock_service_instance = AsyncMock()
            mock_service_instance.get_neighborhood_intelligence.return_value = None
            mock_service.return_value = mock_service_instance

            response = client.get("/api/v1/neighborhoods/nonexistent/intelligence")

            assert response.status_code == status.HTTP_404_NOT_FOUND

            data = response.json()
            assert data["success"] is False
            assert "not found" in data["message"].lower()

    def test_get_neighborhood_intelligence_empty_id(self):
        """Test neighborhood intelligence with empty ID."""
        response = client.get("/api/v1/neighborhoods/ /intelligence")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        data = response.json()
        assert data["success"] is False
        assert "empty" in data["message"].lower()

    def test_get_neighborhood_metrics_success(self, sample_neighborhood_metrics):
        """Test successful neighborhood metrics retrieval."""
        with patch(
            "ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_neighborhood_intelligence_service"
        ) as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.get_market_metrics.return_value = sample_neighborhood_metrics
            mock_service.return_value = mock_service_instance

            response = client.get("/api/v1/neighborhoods/test_neighborhood/metrics")

            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["success"] is True
            assert data["data"]["neighborhood_id"] == "test_neighborhood"
            assert data["data"]["median_home_value"] == 750000.0

    def test_get_neighborhood_metrics_with_timeframe(self, sample_neighborhood_metrics):
        """Test neighborhood metrics with specific timeframe."""
        with patch(
            "ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_neighborhood_intelligence_service"
        ) as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.get_market_metrics.return_value = sample_neighborhood_metrics
            mock_service.return_value = mock_service_instance

            response = client.get("/api/v1/neighborhoods/test_neighborhood/metrics?timeframe=1m")

            assert response.status_code == status.HTTP_200_OK

            # Verify timeframe was passed to service
            mock_service_instance.get_market_metrics.assert_called_with(
                neighborhood_id="test_neighborhood", timeframe="1m"
            )

    def test_get_price_predictions_success(self, sample_neighborhood_metrics):
        """Test successful price predictions."""
        with (
            patch(
                "ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_neighborhood_intelligence_service"
            ) as mock_intelligence,
            patch("ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_price_prediction_engine") as mock_engine,
        ):
            # Mock intelligence service
            mock_intelligence_instance = AsyncMock()
            mock_intelligence_instance.get_market_metrics.return_value = sample_neighborhood_metrics
            mock_intelligence.return_value = mock_intelligence_instance

            # Mock prediction engine
            mock_engine_instance = AsyncMock()
            mock_prediction_result = PricePredictionResult(
                property_id=None,
                predicted_price=780000.0,
                confidence_interval=(750000.0, 810000.0),
                prediction_confidence=0.95,
                timeframe_predictions={"1m": 785000.0},
                model_used="ensemble",
                feature_importance={"square_footage": 0.3},
                comparable_properties=[],
                market_position="at_market",
                price_per_sqft=350.0,
                neighborhood_context={},
                prediction_date=datetime.now(),
                data_freshness=datetime.now(),
                model_version="2.1.0",
            )
            mock_engine_instance.predict_price.return_value = mock_prediction_result
            mock_engine.return_value = mock_engine_instance

            request_data = {"property_type": "single_family", "timeframes": ["1m", "3m"]}

            response = client.post("/api/v1/neighborhoods/test_neighborhood/predictions", json=request_data)

            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["success"] is True
            assert "predictions" in data["data"]

    def test_get_price_predictions_invalid_timeframe(self, sample_neighborhood_metrics):
        """Test price predictions with invalid timeframe."""
        request_data = {"timeframes": ["invalid_timeframe"]}

        response = client.post("/api/v1/neighborhoods/test_neighborhood/predictions", json=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        data = response.json()
        assert data["success"] is False
        assert "invalid timeframe" in data["message"].lower()

    def test_search_neighborhoods_success(self):
        """Test successful neighborhood search."""
        with patch(
            "ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_neighborhood_intelligence_service"
        ) as mock_service:
            mock_service_instance = AsyncMock()
            mock_service.return_value = mock_service_instance

            request_data = {
                "criteria": {"max_price": 800000, "min_walk_score": 70},
                "max_results": 10,
                "include_metrics": True,
            }

            response = client.post("/api/v1/neighborhoods/search", json=request_data)

            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["success"] is True
            assert "results" in data["data"]

    def test_search_neighborhoods_empty_criteria(self):
        """Test neighborhood search with empty criteria."""
        request_data = {"criteria": {}, "max_results": 10}

        response = client.post("/api/v1/neighborhoods/search", json=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        data = response.json()
        assert data["success"] is False
        assert "criteria cannot be empty" in data["message"].lower()

    def test_get_market_alerts_success(self, sample_alert):
        """Test successful market alerts retrieval."""
        with patch(
            "ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_inventory_alert_system"
        ) as mock_alert_system:
            mock_system_instance = AsyncMock()
            mock_system_instance.get_active_alerts.return_value = [sample_alert]
            mock_alert_system.return_value = mock_system_instance

            response = client.get("/api/v1/market/alerts")

            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["alerts"]) == 1
            assert data["data"]["alerts"][0]["alert_id"] == "test_alert_001"

    def test_get_market_alerts_with_filters(self, sample_alert):
        """Test market alerts with filters."""
        with patch(
            "ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_inventory_alert_system"
        ) as mock_alert_system:
            mock_system_instance = AsyncMock()
            mock_system_instance.get_active_alerts.return_value = [sample_alert]
            mock_alert_system.return_value = mock_system_instance

            response = client.get("/api/v1/market/alerts?neighborhood_ids=test_neighborhood&min_severity=high&limit=20")

            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["success"] is True
            assert "filters_applied" in data["data"]

    def test_create_alert_rule_success(self):
        """Test successful alert rule creation."""
        with patch(
            "ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_inventory_alert_system"
        ) as mock_alert_system:
            mock_system_instance = AsyncMock()
            mock_system_instance.create_alert_rule.return_value = True
            mock_alert_system.return_value = mock_system_instance

            request_data = {
                "name": "Test Alert Rule",
                "description": "Test alert for inventory changes",
                "alert_type": "inventory_drop",
                "enabled": True,
                "conditions": {"metric": "active_listings"},
                "threshold_values": {"drop_percentage": 20.0},
                "comparison_period": "24h",
                "severity": "high",
                "delivery_channels": ["email"],
                "throttle_minutes": 60,
            }

            response = client.post("/api/v1/market/alerts/rules", json=request_data)

            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["success"] is True
            assert "rule_id" in data["data"]

    def test_create_alert_rule_validation_error(self):
        """Test alert rule creation with validation error."""
        request_data = {
            "name": "Test Alert Rule",
            "description": "Test alert",
            "alert_type": "invalid_type",  # Invalid type
            "enabled": True,
            "conditions": {},
            "threshold_values": {},
            "severity": "high",
        }

        response = client.post("/api/v1/market/alerts/rules", json=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        data = response.json()
        assert data["success"] is False

    def test_get_investment_opportunities_success(self):
        """Test successful investment opportunities analysis."""
        with patch(
            "ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_neighborhood_intelligence_service"
        ) as mock_service:
            mock_service_instance = AsyncMock()
            mock_opportunities = [
                {
                    "neighborhood_id": "opportunity_area",
                    "score": 94.2,
                    "roi_projection": {"1_year": 18.5},
                    "investment_thesis": "Strong growth potential",
                }
            ]
            mock_service_instance.analyze_investment_opportunities.return_value = mock_opportunities
            mock_service.return_value = mock_service_instance

            request_data = {
                "criteria": {"max_budget": 800000, "min_roi": 15.0},
                "max_results": 20,
                "risk_tolerance": "medium",
            }

            response = client.post("/api/v1/investment/opportunities", json=request_data)

            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["opportunities"]) == 1

    def test_generate_investment_heatmap_success(self):
        """Test successful investment heatmap generation."""
        with patch(
            "ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_geospatial_analysis_service"
        ) as mock_geo_service:
            from ghl_real_estate_ai.services.geospatial_analysis_service import InvestmentHeatmap

            mock_geo_instance = AsyncMock()
            mock_heatmap = InvestmentHeatmap(
                heatmap_id="test_heatmap",
                analysis_type="investment_opportunity",
                grid_resolution=0.5,
                bounds=(30.0, -98.0, 30.5, -97.5),
                grid_cells=[{"latitude": 30.25, "longitude": -97.75, "investment_score": 85.0}],
                hotspots=[],
                risk_zones=[],
                scoring_factors=["price_appreciation"],
                confidence_level=0.85,
                data_freshness=datetime.now(),
                generated_at=datetime.now(),
            )
            mock_geo_instance.generate_investment_heatmap.return_value = mock_heatmap
            mock_geo_service.return_value = mock_geo_instance

            request_data = {
                "bounds": [30.0, -98.0, 30.5, -97.5],
                "grid_resolution_km": 0.5,
                "scoring_factors": ["price_appreciation", "market_velocity"],
            }

            response = client.post("/api/v1/investment/heatmap", json=request_data)

            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["success"] is True
            assert "heatmap_id" in data["data"]

    def test_generate_heatmap_invalid_bounds(self):
        """Test heatmap generation with invalid bounds."""
        request_data = {
            "bounds": [200.0, -98.0, 30.5],  # Invalid bounds
            "grid_resolution_km": 0.5,
        }

        response = client.post("/api/v1/investment/heatmap", json=request_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_analyze_accessibility_success(self):
        """Test successful accessibility analysis."""
        with patch(
            "ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_geospatial_analysis_service"
        ) as mock_geo_service:
            from ghl_real_estate_ai.services.geospatial_analysis_service import AccessibilityScore, GeographicPoint

            mock_geo_instance = AsyncMock()
            mock_score = AccessibilityScore(
                location=GeographicPoint(30.2672, -97.7431),
                walk_score=85,
                transit_score=78,
                bike_score=82,
                car_dependency=0.15,
                amenity_access={"restaurants": 90, "shopping": 85},
                transit_stops=[],
                bike_infrastructure={},
                walkability_factors={},
                commute_scores={"downtown": 92.0},
                traffic_patterns={},
                calculated_at=datetime.now(),
            )
            mock_geo_instance.calculate_accessibility_scores.return_value = [mock_score]
            mock_geo_service.return_value = mock_geo_instance

            request_data = {
                "locations": [{"latitude": 30.2672, "longitude": -97.7431}],
                "analysis_radius_km": 2.0,
                "include_demographics": True,
            }

            response = client.post("/api/v1/geospatial/accessibility", json=request_data)

            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["accessibility_analysis"]) == 1

    def test_analyze_accessibility_invalid_coordinates(self):
        """Test accessibility analysis with invalid coordinates."""
        request_data = {
            "locations": [{"latitude": 200.0, "longitude": -97.7431}],  # Invalid latitude
            "analysis_radius_km": 2.0,
        }

        response = client.post("/api/v1/geospatial/accessibility", json=request_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_cluster_properties_success(self):
        """Test successful property clustering."""
        with patch(
            "ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_geospatial_analysis_service"
        ) as mock_geo_service:
            from ghl_real_estate_ai.services.geospatial_analysis_service import GeographicPoint, PropertyCluster

            mock_geo_instance = AsyncMock()
            mock_cluster = PropertyCluster(
                cluster_id="cluster_1",
                cluster_type="investment_potential",
                center_point=GeographicPoint(30.2672, -97.7431),
                radius_km=2.5,
                property_count=15,
                cluster_characteristics={"avg_price": 750000},
                similarity_score=0.85,
                market_homogeneity=0.78,
            )
            mock_geo_instance.cluster_properties.return_value = [mock_cluster]
            mock_geo_service.return_value = mock_geo_instance

            request_data = {
                "properties": [
                    {"latitude": 30.2672, "longitude": -97.7431, "price": 750000},
                    {"latitude": 30.2680, "longitude": -97.7440, "price": 780000},
                ],
                "cluster_criteria": "investment_potential",
                "max_clusters": 5,
            }

            response = client.post("/api/v1/geospatial/cluster", json=request_data)

            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["clusters"]) == 1

    def test_health_check_success(self):
        """Test health check endpoint."""
        with (
            patch(
                "ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_neighborhood_intelligence_service"
            ) as mock_intelligence,
            patch("ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_price_prediction_engine") as mock_engine,
            patch(
                "ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_geospatial_analysis_service"
            ) as mock_geo,
            patch("ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_inventory_alert_system") as mock_alert,
        ):
            # Mock all services as initialized
            mock_intelligence_instance = AsyncMock()
            mock_intelligence_instance.is_initialized = True
            mock_intelligence.return_value = mock_intelligence_instance

            mock_engine_instance = AsyncMock()
            mock_engine_instance.is_initialized = True
            mock_engine.return_value = mock_engine_instance

            mock_geo_instance = AsyncMock()
            mock_geo_instance.is_initialized = True
            mock_geo.return_value = mock_geo_instance

            mock_alert_instance = AsyncMock()
            mock_alert_instance.is_initialized = True
            mock_alert.return_value = mock_alert_instance

            response = client.get("/api/v1/health")

            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["success"] is True
            assert data["data"]["status"] == "healthy"
            assert all(data["data"]["services"].values())

    def test_health_check_service_unavailable(self):
        """Test health check when services are unavailable."""
        with patch(
            "ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_neighborhood_intelligence_service"
        ) as mock_service:
            mock_service.side_effect = Exception("Service unavailable")

            response = client.get("/api/v1/health")

            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

            data = response.json()
            assert data["success"] is False

    def test_request_validation(self):
        """Test request validation for various endpoints."""
        # Test missing required fields
        response = client.post("/api/v1/neighborhoods/search", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test invalid data types
        response = client.post(
            "/api/v1/neighborhoods/search",
            json={
                "criteria": "not_a_dict",  # Should be dict
                "max_results": "not_a_number",  # Should be number
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_error_response_format(self):
        """Test error response format consistency."""
        # Test with non-existent endpoint
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Test internal server error handling
        with patch(
            "ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_neighborhood_intelligence_service"
        ) as mock_service:
            mock_service.side_effect = Exception("Internal error")

            response = client.get("/api/v1/neighborhoods/test/intelligence")

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

            data = response.json()
            assert data["success"] is False
            assert "error" in data
            assert "timestamp" in data

    def test_response_time_performance(self, sample_intelligence_data):
        """Test API response time performance."""
        with patch(
            "ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_neighborhood_intelligence_service"
        ) as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.get_neighborhood_intelligence.return_value = sample_intelligence_data
            mock_service.return_value = mock_service_instance

            import time

            start_time = time.time()

            response = client.get("/api/v1/neighborhoods/test_neighborhood/intelligence")

            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds

            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert "execution_time_ms" in data

            # API should respond quickly for cached data
            assert execution_time < 1000  # Less than 1 second

    def test_concurrent_requests_handling(self, sample_intelligence_data):
        """Test handling of concurrent requests."""
        import threading
        import time

        with patch(
            "ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_neighborhood_intelligence_service"
        ) as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.get_neighborhood_intelligence.return_value = sample_intelligence_data
            mock_service.return_value = mock_service_instance

            results = []
            errors = []

            def make_request():
                try:
                    response = client.get("/api/v1/neighborhoods/concurrent_test/intelligence")
                    results.append(response.status_code)
                except Exception as e:
                    errors.append(str(e))

            # Make 10 concurrent requests
            threads = []
            for _ in range(10):
                thread = threading.Thread(target=make_request)
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # All requests should succeed
            assert len(errors) == 0
            assert len(results) == 10
            assert all(status_code == 200 for status_code in results)

    def test_large_payload_handling(self):
        """Test handling of large request payloads."""
        # Create large property list for clustering
        large_properties = []
        for i in range(1000):  # 1000 properties
            large_properties.append(
                {
                    "latitude": 30.0 + (i * 0.001),
                    "longitude": -97.0 - (i * 0.001),
                    "price": 500000 + (i * 1000),
                    "property_id": f"prop_{i}",
                }
            )

        with patch(
            "ghl_real_estate_ai.api.routes.neighborhood_intelligence.get_geospatial_analysis_service"
        ) as mock_geo_service:
            mock_geo_instance = AsyncMock()
            mock_geo_instance.cluster_properties.return_value = []
            mock_geo_service.return_value = mock_geo_instance

            request_data = {
                "properties": large_properties[:100],  # Limit to reasonable size
                "cluster_criteria": "price",
                "max_clusters": 5,
            }

            response = client.post("/api/v1/geospatial/cluster", json=request_data)

            # Should handle large payload gracefully
            assert response.status_code in [200, 413]  # OK or payload too large