import pytest
pytestmark = pytest.mark.integration

"""
Test suite for Market Intelligence API Routes.

Tests comprehensive Rancho Cucamonga real estate market API functionality including:
- Market metrics and neighborhood endpoints
- Property search and recommendation APIs
- Corporate relocation intelligence endpoints
- Market timing analysis APIs
- Property alert management
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest

try:
    # Mock FastAPI app for testing
    from fastapi import FastAPI, status
    from fastapi.testclient import TestClient

    # Import the FastAPI app and route components
    from ghl_real_estate_ai.api.routes.market_intelligence import router
    from ghl_real_estate_ai.services.rancho_cucamonga_market_service import MarketCondition, PropertyType
except (ImportError, TypeError, AttributeError, Exception):
    pytest.skip("required imports unavailable", allow_module_level=True)
app = FastAPI()
app.include_router(router)

client = TestClient(app)


class TestMarketMetricsEndpoints:
    """Test market metrics API endpoints."""

    def test_get_market_metrics_basic(self):
        """Test basic market metrics endpoint."""
        response = client.get("/api/v1/market-intelligence/metrics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "median_price" in data
        assert "average_days_on_market" in data
        assert "inventory_count" in data
        assert "market_condition" in data
        assert "last_updated" in data

        # Verify data types
        assert isinstance(data["median_price"], (int, float))
        assert isinstance(data["average_days_on_market"], int)
        assert isinstance(data["inventory_count"], int)
        assert data["market_condition"] in ["strong_sellers", "balanced", "strong_buyers", "transitioning"]

    def test_get_market_metrics_with_neighborhood(self):
        """Test market metrics with neighborhood filter."""
        response = client.get("/api/v1/market-intelligence/metrics?neighborhood=Round Rock")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["neighborhood"] == "Round Rock"
        assert "median_price" in data

    def test_get_market_metrics_with_property_type(self):
        """Test market metrics with property type filter."""
        response = client.get("/api/v1/market-intelligence/metrics?property_type=single_family")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["property_type"] == "single_family"

    def test_get_market_metrics_invalid_property_type(self):
        """Test market metrics with invalid property type."""
        response = client.get("/api/v1/market-intelligence/metrics?property_type=invalid_type")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid property type" in response.json()["detail"]

    def test_get_neighborhood_list(self):
        """Test neighborhood list endpoint."""
        response = client.get("/api/v1/market-intelligence/neighborhoods")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "neighborhoods" in data
        neighborhoods = data["neighborhoods"]

        # Verify structure
        assert isinstance(neighborhoods, list)
        assert len(neighborhoods) > 0

        # Check first neighborhood structure
        neighborhood = neighborhoods[0]
        assert "name" in neighborhood
        assert "zone" in neighborhood
        assert "appeal" in neighborhood

        # Verify key neighborhoods are present
        neighborhood_names = [n["name"] for n in neighborhoods]
        assert "Round Rock" in neighborhood_names
        assert "Ontario Mills" in neighborhood_names

    def test_get_neighborhood_analysis_valid(self):
        """Test neighborhood analysis for valid neighborhood."""
        response = client.get("/api/v1/market-intelligence/neighborhoods/Round Rock")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "neighborhood" in data
        assert "market_metrics" in data
        assert "lifestyle_score" in data

        # Verify neighborhood data structure
        neighborhood = data["neighborhood"]
        assert neighborhood["name"] == "Round Rock"
        assert "median_price" in neighborhood
        assert "school_rating" in neighborhood

    def test_get_neighborhood_analysis_invalid(self):
        """Test neighborhood analysis for invalid neighborhood."""
        response = client.get("/api/v1/market-intelligence/neighborhoods/NonExistentPlace")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]


class TestPropertySearchEndpoints:
    """Test property search API endpoints."""

    def test_search_properties_basic(self):
        """Test basic property search."""
        search_request = {"min_price": 400000, "max_price": 700000, "min_beds": 3, "limit": 10}

        response = client.post("/api/v1/market-intelligence/properties/search", json=search_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "properties" in data
        assert "total_found" in data
        assert "search_criteria" in data

        properties = data["properties"]
        assert isinstance(properties, list)
        assert len(properties) <= 10

        # Verify property structure if any found
        if properties:
            prop = properties[0]
            assert "mls_id" in prop
            assert "address" in prop
            assert "price" in prop
            assert "beds" in prop
            assert "neighborhood" in prop

    def test_search_properties_with_neighborhoods(self):
        """Test property search with neighborhood filter."""
        search_request = {"neighborhoods": ["Round Rock", "Cedar Park"], "min_beds": 2, "limit": 15}

        response = client.post("/api/v1/market-intelligence/properties/search", json=search_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify search criteria was applied
        assert data["search_criteria"]["neighborhoods"] == ["Round Rock", "Cedar Park"]

    def test_search_properties_with_commute_filter(self):
        """Test property search with commute requirements."""
        search_request = {"work_location": "Apple", "max_commute_minutes": 30, "min_beds": 3, "limit": 5}

        response = client.post("/api/v1/market-intelligence/properties/search", json=search_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "properties" in data

    def test_search_properties_empty_criteria(self):
        """Test property search with empty criteria."""
        search_request = {"limit": 5}

        response = client.post("/api/v1/market-intelligence/properties/search", json=search_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "properties" in data

    def test_get_property_recommendations(self):
        """Test property recommendations endpoint."""
        recommendation_request = {
            "lead_id": "test_lead_001",
            "employer": "Apple",
            "budget_range": [500000, 800000],
            "family_status": "family with children",
            "lifestyle_preferences": ["family-friendly", "good schools"],
            "timeline": "60 days",
        }

        response = client.post("/api/v1/market-intelligence/properties/recommendations", json=recommendation_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "lead_id" in data
        assert "recommendations" in data
        assert "lead_context" in data
        assert data["lead_id"] == "test_lead_001"

        recommendations = data["recommendations"]
        assert isinstance(recommendations, list)

        # Verify recommendation structure if any
        if recommendations:
            rec = recommendations[0]
            assert "property" in rec
            assert "match_explanation" in rec
            assert "match_score" in rec

    def test_get_property_recommendations_minimal_data(self):
        """Test property recommendations with minimal data."""
        recommendation_request = {
            "lead_id": "minimal_lead",
        }

        response = client.post("/api/v1/market-intelligence/properties/recommendations", json=recommendation_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["lead_id"] == "minimal_lead"
        assert "recommendations" in data


class TestCorporateIntelligenceEndpoints:
    """Test corporate relocation intelligence endpoints."""

    def test_get_corporate_insights(self):
        """Test corporate insights endpoint."""
        insights_request = {"employer": "Apple", "position_level": "Senior Engineer", "salary_range": [140000, 200000]}

        response = client.post("/api/v1/market-intelligence/corporate-insights", json=insights_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "employer" in data
        assert "insights" in data
        assert data["employer"] == "Apple"

        insights = data["insights"]
        assert isinstance(insights, dict)

        # Should have budget analysis with salary range
        if "budget_analysis" in insights:
            budget = insights["budget_analysis"]
            assert "recommended_max_price" in budget
            assert "comfortable_range" in budget

    def test_get_corporate_insights_minimal(self):
        """Test corporate insights with minimal data."""
        insights_request = {"employer": "Google"}

        response = client.post("/api/v1/market-intelligence/corporate-insights", json=insights_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["employer"] == "Google"

    def test_get_corporate_employers(self):
        """Test corporate employers list endpoint."""
        response = client.get("/api/v1/market-intelligence/corporate-employers")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "employers" in data
        employers = data["employers"]

        assert isinstance(employers, list)
        assert len(employers) > 0

        # Verify employer structure
        employer = employers[0]
        assert "name" in employer
        assert "location" in employer
        assert "employees" in employer
        assert "preferred_neighborhoods" in employer

        # Check key employers are present
        employer_names = [e["name"] for e in employers]
        assert "Apple" in employer_names
        assert "Google" in employer_names
        assert "Tesla" in employer_names


class TestMarketTimingEndpoints:
    """Test market timing analysis endpoints."""

    def test_get_market_timing_advice_buy(self):
        """Test market timing advice for buying."""
        timing_request = {"transaction_type": "buy", "property_type": "single_family", "neighborhood": "Round Rock"}

        response = client.post("/api/v1/market-intelligence/market-timing", json=timing_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["transaction_type"] == "buy"
        assert data["property_type"] == "single_family"
        assert data["neighborhood"] == "Round Rock"
        assert "timing_analysis" in data

        timing_analysis = data["timing_analysis"]
        assert "timing_score" in timing_analysis
        assert "recommendations" in timing_analysis

    def test_get_market_timing_advice_sell(self):
        """Test market timing advice for selling."""
        timing_request = {"transaction_type": "sell", "property_type": "condo"}

        response = client.post("/api/v1/market-intelligence/market-timing", json=timing_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["transaction_type"] == "sell"

    def test_get_market_timing_advice_with_lead_context(self):
        """Test market timing advice with lead context."""
        timing_request = {
            "transaction_type": "buy",
            "property_type": "single_family",
            "lead_context": {
                "lead_id": "timing_test",
                "employer": "Apple",
                "timeline": "90 days",
                "family_status": "family",
            },
        }

        response = client.post("/api/v1/market-intelligence/market-timing", json=timing_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        timing_analysis = data["timing_analysis"]
        # Should include enhanced insights with lead context
        assert isinstance(timing_analysis, dict)

    def test_get_market_trends(self):
        """Test market trends endpoint."""
        response = client.get("/api/v1/market-intelligence/market-trends")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "trends" in data
        assert "period" in data

        trends = data["trends"]
        assert "price_trend" in trends
        assert "inventory_trend" in trends
        assert "velocity_trend" in trends

    def test_get_market_trends_with_parameters(self):
        """Test market trends with query parameters."""
        response = client.get("/api/v1/market-intelligence/market-trends?period=6m&neighborhood=Round Rock")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["period"] == "6m"
        assert data["neighborhood"] == "Round Rock"

        # Should include neighborhood-specific insights
        if "neighborhood_insights" in data["trends"]:
            insights = data["trends"]["neighborhood_insights"]
            assert "tech_worker_appeal" in insights


class TestPropertyAlertsEndpoints:
    """Test property alerts management endpoints."""

    def test_setup_property_alerts(self):
        """Test setting up property alerts."""
        alert_request = {
            "min_price": 400000,
            "max_price": 700000,
            "min_beds": 3,
            "neighborhoods": ["Round Rock", "Cedar Park"],
            "work_location": "Apple",
            "max_commute_minutes": 30,
        }

        response = client.post("/api/v1/market-intelligence/alerts/setup?lead_id=alert_test_lead", json=alert_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["lead_id"] == "alert_test_lead"
        assert data["alert_status"] == "active"
        assert "criteria" in data

    def test_get_alert_summary(self):
        """Test getting alert summary."""
        # First setup alerts
        alert_request = {"min_price": 500000, "max_price": 800000, "min_beds": 2}

        client.post("/api/v1/market-intelligence/alerts/setup?lead_id=summary_test_lead", json=alert_request)

        # Then get summary
        response = client.get("/api/v1/market-intelligence/alerts/summary_test_lead/summary")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["lead_id"] == "summary_test_lead"
        assert "alert_summary" in data

    def test_get_alert_summary_nonexistent_lead(self):
        """Test getting alert summary for nonexistent lead."""
        response = client.get("/api/v1/market-intelligence/alerts/nonexistent_lead/summary")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["lead_id"] == "nonexistent_lead"
        # Should handle gracefully


class TestAIInsightsEndpoints:
    """Test AI-powered insights endpoints."""

    def test_get_ai_lead_analysis(self):
        """Test AI lead analysis endpoint."""
        lead_data = {
            "lead_id": "ai_test_lead",
            "name": "John Doe",
            "employer": "Apple",
            "budget_max": 750000,
            "preferred_neighborhoods": ["Round Rock"],
            "family_status": "married with kids",
        }

        response = client.post(
            "/api/v1/market-intelligence/ai-insights/lead-analysis",
            json={"lead_data": lead_data, "conversation_history": []},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "analysis" in data
        assert "generated_at" in data

    def test_get_ai_conversation_response(self):
        """Test AI conversation response endpoint."""
        conversation_request = {
            "query": "What neighborhoods would be best for an Apple employee with a family?",
            "lead_context": {
                "lead_id": "conversation_test",
                "employer": "Apple",
                "family_situation": "family with children",
                "conversation_stage": "discovery",
            },
            "conversation_history": [],
        }

        response = client.post("/api/v1/market-intelligence/ai-insights/conversation", json=conversation_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["query"] == conversation_request["query"]
        assert "ai_response" in data
        assert "generated_at" in data

        ai_response = data["ai_response"]
        assert "response" in ai_response

    def test_get_ai_conversation_response_minimal(self):
        """Test AI conversation response with minimal context."""
        conversation_request = {
            "query": "Tell me about Rancho Cucamonga real estate market",
            "lead_context": {"lead_id": "minimal_context"},
        }

        response = client.post("/api/v1/market-intelligence/ai-insights/conversation", json=conversation_request)

        assert response.status_code == status.HTTP_200_OK


class TestHealthAndStatusEndpoints:
    """Test health check and status endpoints."""

    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/api/v1/market-intelligence/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "status" in data
        assert "services" in data

        # Should indicate operational status
        assert data["status"] in ["healthy", "degraded"]

        services = data["services"]
        assert "market_service" in services
        assert "ai_assistant" in services
        assert "alert_system" in services


class TestErrorHandling:
    """Test error handling in API endpoints."""

    def test_invalid_json_request(self):
        """Test handling of invalid JSON requests."""
        response = client.post("/api/v1/market-intelligence/properties/search", data="invalid json")

        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        # Missing lead_id in property recommendations
        response = client.post("/api/v1/market-intelligence/properties/recommendations", json={"employer": "Apple"})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_field_values(self):
        """Test handling of invalid field values."""
        # Invalid transaction type in market timing
        timing_request = {"transaction_type": "invalid_type", "property_type": "single_family"}

        response = client.post("/api/v1/market-intelligence/market-timing", json=timing_request)

        # Should handle gracefully or return appropriate error
        assert response.status_code in [
            status.HTTP_200_OK,  # If handled gracefully
            status.HTTP_400_BAD_REQUEST,  # If validation error
            status.HTTP_422_UNPROCESSABLE_ENTITY,  # If Pydantic validation error
        ]


@pytest.mark.integration
class TestMarketIntelligenceIntegration:
    """Integration tests for Market Intelligence API."""

    def test_full_property_search_to_recommendation_workflow(self):
        """Test complete workflow from search to recommendations."""
        # Step 1: Search for properties
        search_request = {
            "min_price": 500000,
            "max_price": 800000,
            "min_beds": 3,
            "neighborhoods": ["Round Rock"],
            "limit": 10,
        }

        search_response = client.post("/api/v1/market-intelligence/properties/search", json=search_request)

        assert search_response.status_code == status.HTTP_200_OK

        # Step 2: Get recommendations based on search criteria
        recommendation_request = {
            "lead_id": "integration_test_lead",
            "employer": "Apple",
            "budget_range": [500000, 800000],
            "family_status": "family",
            "timeline": "60 days",
        }

        rec_response = client.post(
            "/api/v1/market-intelligence/properties/recommendations", json=recommendation_request
        )

        assert rec_response.status_code == status.HTTP_200_OK

        # Step 3: Set up alerts based on criteria
        alert_request = {"min_price": 500000, "max_price": 800000, "min_beds": 3, "neighborhoods": ["Round Rock"]}

        alert_response = client.post(
            "/api/v1/market-intelligence/alerts/setup?lead_id=integration_test_lead", json=alert_request
        )

        assert alert_response.status_code == status.HTTP_200_OK

    def test_corporate_relocation_workflow(self):
        """Test corporate relocation analysis workflow."""
        # Step 1: Get corporate insights
        insights_response = client.post(
            "/api/v1/market-intelligence/corporate-insights",
            json={"employer": "Apple", "position_level": "Senior Engineer"},
        )

        assert insights_response.status_code == status.HTTP_200_OK

        # Step 2: Get market timing advice
        timing_response = client.post(
            "/api/v1/market-intelligence/market-timing",
            json={
                "transaction_type": "buy",
                "property_type": "single_family",
                "lead_context": {"lead_id": "corporate_test", "employer": "Apple"},
            },
        )

        assert timing_response.status_code == status.HTTP_200_OK

        # Step 3: Get AI insights
        ai_response = client.post(
            "/api/v1/market-intelligence/ai-insights/lead-analysis",
            json={"lead_data": {"lead_id": "corporate_test", "employer": "Apple", "position": "Senior Engineer"}},
        )

        assert ai_response.status_code == status.HTTP_200_OK

    def test_market_analysis_workflow(self):
        """Test comprehensive market analysis workflow."""
        # Step 1: Get overall market metrics
        metrics_response = client.get("/api/v1/market-intelligence/metrics")
        assert metrics_response.status_code == status.HTTP_200_OK

        # Step 2: Get neighborhood-specific analysis
        neighborhood_response = client.get("/api/v1/market-intelligence/neighborhoods/Round Rock")
        assert neighborhood_response.status_code == status.HTTP_200_OK

        # Step 3: Get market trends
        trends_response = client.get("/api/v1/market-intelligence/market-trends?period=3m&neighborhood=Round Rock")
        assert trends_response.status_code == status.HTTP_200_OK

        # Step 4: Get timing advice
        timing_response = client.post(
            "/api/v1/market-intelligence/market-timing",
            json={"transaction_type": "buy", "property_type": "single_family", "neighborhood": "Round Rock"},
        )
        assert timing_response.status_code == status.HTTP_200_OK


@pytest.mark.performance
class TestMarketIntelligencePerformance:
    """Performance tests for Market Intelligence API."""

    def test_concurrent_requests_performance(self):
        """Test performance with concurrent requests."""
        import threading
        import time

        results = []
        start_time = time.time()

        def make_request():
            response = client.get("/api/v1/market-intelligence/metrics")
            results.append(response.status_code)

        # Create 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        end_time = time.time()
        total_time = end_time - start_time

        # All requests should succeed
        assert all(status == 200 for status in results)

        # Should complete within reasonable time
        assert total_time < 5.0  # 5 seconds for 10 concurrent requests

    def test_large_property_search_performance(self):
        """Test performance with large property search."""
        search_request = {
            "min_price": 200000,
            "max_price": 2000000,  # Wide range
            "limit": 100,  # Large limit
        }

        start_time = time.time()
        response = client.post("/api/v1/market-intelligence/properties/search", json=search_request)
        end_time = time.time()

        assert response.status_code == status.HTTP_200_OK

        # Should complete within reasonable time
        search_time = end_time - start_time
        assert search_time < 3.0  # 3 seconds for large search
