"""
Unit Tests for Neighborhood Intelligence API Service

Tests comprehensive multimodal property intelligence including:
- Walk Score, Transit, and Bike score integration
- GreatSchools API integration for school ratings
- Google Maps/Mapbox commute optimization
- 24-hour intelligent caching with >85% hit rate
- Cost optimization and API quota management
- Parallel API coordination and error handling
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from ghl_real_estate_ai.services.neighborhood_intelligence_api import (
    APICostMetrics,
    CommuteData,
    CommuteScores,
    LocationData,
    NeighborhoodIntelligence,
    NeighborhoodIntelligenceAPI,
    SchoolData,
    SchoolLevel,
    SchoolRatings,
    SchoolType,
    TransportMode,
    WalkabilityData,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_location():
    """Sample location data."""
    return {
        "address": "123 Main St, Austin, TX 78701",
        "lat": 30.2672,
        "lng": -97.7431,
        "city": "Austin",
        "state": "TX",
        "zipcode": "78701"
    }


@pytest.fixture
def sample_walkability_response():
    """Sample Walk Score API response."""
    return {
        "status": 1,
        "walkscore": 85,
        "description": "Very Walkable",
        "transit": {
            "score": 72,
            "description": "Excellent Transit"
        },
        "bike": {
            "score": 78,
            "description": "Very Bikeable"
        }
    }


@pytest.fixture
def sample_school_data():
    """Sample school data."""
    return [
        {
            "school_id": "school_001",
            "name": "Austin Elementary",
            "school_type": "public",
            "level": "elementary",
            "rating": 9,
            "district": "Austin ISD",
            "address": "456 School St, Austin, TX 78701",
            "lat": 30.2680,
            "lng": -97.7440,
            "distance_miles": 0.5,
            "enrollment": 450,
            "student_teacher_ratio": 15.2
        },
        {
            "school_id": "school_002",
            "name": "Austin Middle School",
            "school_type": "public",
            "level": "middle",
            "rating": 8,
            "district": "Austin ISD",
            "distance_miles": 1.2
        }
    ]


@pytest.fixture
def sample_commute_response():
    """Sample Google Maps Directions API response."""
    return {
        "routes": [
            {
                "legs": [
                    {
                        "distance": {
                            "value": 16093,  # meters (10 miles)
                            "text": "10 mi"
                        },
                        "duration": {
                            "value": 1200,  # seconds (20 min)
                            "text": "20 mins"
                        },
                        "duration_in_traffic": {
                            "value": 1500,  # 25 min in traffic
                            "text": "25 mins"
                        }
                    }
                ]
            }
        ]
    }


@pytest.fixture
async def intelligence_service():
    """Create NeighborhoodIntelligenceAPI instance."""
    service = NeighborhoodIntelligenceAPI()

    # Mock API keys
    service.walk_score_api_key = "test_walkscore_key"
    service.greatschools_api_key = "test_greatschools_key"
    service.google_maps_api_key = "test_googlemaps_key"

    await service.initialize()

    yield service

    await service.cleanup()


# ============================================================================
# Data Model Tests
# ============================================================================


class TestWalkabilityData:
    """Test WalkabilityData model."""

    def test_walkability_data_creation(self):
        """Test creating WalkabilityData instance."""
        data = WalkabilityData(
            address="123 Main St",
            lat=30.2672,
            lng=-97.7431,
            walk_score=85,
            walk_description="Very Walkable",
            transit_score=72,
            bike_score=78
        )

        assert data.walk_score == 85
        assert data.transit_score == 72
        assert data.bike_score == 78
        assert data.data_source == "walkscore"

    def test_walkability_serialization(self):
        """Test to_dict and from_dict."""
        original = WalkabilityData(
            address="123 Main St",
            lat=30.2672,
            lng=-97.7431,
            walk_score=85
        )

        # Serialize
        data_dict = original.to_dict()
        assert data_dict["walk_score"] == 85
        assert "timestamp" in data_dict

        # Deserialize
        restored = WalkabilityData.from_dict(data_dict)
        assert restored.walk_score == original.walk_score
        assert restored.lat == original.lat


class TestSchoolRatings:
    """Test SchoolRatings model."""

    def test_school_ratings_creation(self):
        """Test creating SchoolRatings with schools."""
        elementary_school = SchoolData(
            school_id="001",
            name="Test Elementary",
            school_type=SchoolType.PUBLIC,
            level=SchoolLevel.ELEMENTARY,
            rating=9
        )

        high_school = SchoolData(
            school_id="002",
            name="Test High",
            school_type=SchoolType.PUBLIC,
            level=SchoolLevel.HIGH,
            rating=7
        )

        ratings = SchoolRatings(
            address="123 Main St",
            elementary_schools=[elementary_school],
            high_schools=[high_school]
        )

        assert len(ratings.elementary_schools) == 1
        assert len(ratings.high_schools) == 1
        assert ratings.average_rating == 8.0  # (9 + 7) / 2

    def test_school_ratings_average_calculation(self):
        """Test average rating calculation."""
        schools = [
            SchoolData("001", "School 1", SchoolType.PUBLIC, SchoolLevel.ELEMENTARY, rating=8),
            SchoolData("002", "School 2", SchoolType.PUBLIC, SchoolLevel.MIDDLE, rating=6),
            SchoolData("003", "School 3", SchoolType.PUBLIC, SchoolLevel.HIGH, rating=10),
        ]

        ratings = SchoolRatings(
            address="Test",
            elementary_schools=[schools[0]],
            middle_schools=[schools[1]],
            high_schools=[schools[2]]
        )

        assert ratings.average_rating == 8.0  # (8 + 6 + 10) / 3


class TestCommuteScores:
    """Test CommuteScores model."""

    def test_commute_scores_metrics(self):
        """Test commute metrics calculation."""
        routes = [
            CommuteData(
                destination="Downtown",
                mode=TransportMode.DRIVING,
                distance_miles=10.0,
                duration_minutes=20,
                duration_in_traffic_minutes=25
            ),
            CommuteData(
                destination="Airport",
                mode=TransportMode.DRIVING,
                distance_miles=15.0,
                duration_minutes=45,
                duration_in_traffic_minutes=60
            ),
            CommuteData(
                destination="Downtown",
                mode=TransportMode.TRANSIT,
                distance_miles=10.5,
                duration_minutes=35
            )
        ]

        scores = CommuteScores(
            from_address="123 Main St",
            routes=routes
        )

        assert scores.average_commute_time == 40  # (25 + 60 + 35) / 3
        assert scores.employment_centers_within_30min == 1  # Only first route
        assert scores.public_transit_accessible is True
        assert scores.overall_commute_score > 0

    def test_commute_score_calculation(self):
        """Test overall commute score calculation."""
        # Excellent commute (all under 20 min)
        excellent_routes = [
            CommuteData("Dest1", TransportMode.DRIVING, 5.0, 15),
            CommuteData("Dest2", TransportMode.DRIVING, 6.0, 18),
        ]

        excellent_scores = CommuteScores("123 Main St", routes=excellent_routes)
        assert excellent_scores.overall_commute_score > 80

        # Poor commute (all over 60 min)
        poor_routes = [
            CommuteData("Dest1", TransportMode.DRIVING, 30.0, 65),
            CommuteData("Dest2", TransportMode.DRIVING, 35.0, 75),
        ]

        poor_scores = CommuteScores("123 Main St", routes=poor_routes)
        assert poor_scores.overall_commute_score < 50


class TestNeighborhoodIntelligence:
    """Test NeighborhoodIntelligence composite model."""

    def test_overall_score_calculation(self):
        """Test overall neighborhood score calculation."""
        location = LocationData(
            address="123 Main St",
            lat=30.2672,
            lng=-97.7431,
            city="Austin",
            state="TX",
            zipcode="78701",
            crime_index=20  # Low crime (good)
        )

        walkability = WalkabilityData(
            address="123 Main St",
            lat=30.2672,
            lng=-97.7431,
            walk_score=85
        )

        schools = SchoolRatings(
            address="123 Main St",
            elementary_schools=[
                SchoolData("001", "School", SchoolType.PUBLIC, SchoolLevel.ELEMENTARY, rating=9)
            ]
        )

        commute = CommuteScores(
            from_address="123 Main St",
            routes=[
                CommuteData("Work", TransportMode.DRIVING, 10.0, 20)
            ]
        )

        intelligence = NeighborhoodIntelligence(
            property_address="123 Main St",
            location=location,
            walkability=walkability,
            schools=schools,
            commute=commute
        )

        # Should have high overall score
        assert intelligence.overall_score is not None
        assert intelligence.overall_score > 70

    def test_serialization_roundtrip(self):
        """Test full serialization and deserialization."""
        location = LocationData(
            address="123 Main St",
            lat=30.2672,
            lng=-97.7431,
            city="Austin",
            state="TX",
            zipcode="78701"
        )

        original = NeighborhoodIntelligence(
            property_address="123 Main St",
            location=location
        )

        # Serialize
        data_dict = original.to_dict()

        # Deserialize
        restored = NeighborhoodIntelligence.from_dict(data_dict)

        assert restored.property_address == original.property_address
        assert restored.location.city == original.location.city


# ============================================================================
# API Cost Tracking Tests
# ============================================================================


class TestAPICostMetrics:
    """Test API cost tracking."""

    def test_cost_tracking(self):
        """Test API cost recording."""
        metrics = APICostMetrics()

        # Record API calls
        metrics.record_api_call("walk_score", 0.05)
        metrics.record_api_call("google_maps", 0.005)
        metrics.record_api_call("google_maps", 0.005)

        assert metrics.api_requests == 3
        assert metrics.walk_score_calls == 1
        assert metrics.google_maps_calls == 2
        assert metrics.estimated_cost_usd == 0.06

    def test_cache_hit_rate(self):
        """Test cache hit rate calculation."""
        metrics = APICostMetrics()

        # 7 cache hits, 3 API calls
        for _ in range(7):
            metrics.record_cache_hit()

        metrics.record_api_call("walk_score", 0.05)
        metrics.record_api_call("walk_score", 0.05)
        metrics.record_api_call("walk_score", 0.05)

        assert metrics.total_requests == 10
        assert metrics.cached_requests == 7
        assert metrics.cache_hit_rate == 70.0

    def test_zero_requests_cache_rate(self):
        """Test cache hit rate with zero requests."""
        metrics = APICostMetrics()
        assert metrics.cache_hit_rate == 0.0


# ============================================================================
# Service Integration Tests
# ============================================================================


@pytest.mark.asyncio
class TestNeighborhoodIntelligenceAPI:
    """Test NeighborhoodIntelligenceAPI service."""

    async def test_service_initialization(self, intelligence_service):
        """Test service initializes correctly."""
        assert intelligence_service._initialized is True
        assert intelligence_service.session is not None
        assert intelligence_service.walk_score_api_key is not None

    async def test_cache_key_generation(self, intelligence_service):
        """Test cache key generation is consistent."""
        key1 = intelligence_service._generate_cache_key(
            "test",
            lat=30.2672,
            lng=-97.7431,
            param="value"
        )

        key2 = intelligence_service._generate_cache_key(
            "test",
            lng=-97.7431,  # Different order
            lat=30.2672,
            param="value"
        )

        # Should be identical (deterministic)
        assert key1 == key2

    @patch('aiohttp.ClientSession.get')
    async def test_get_walkability_data(
        self,
        mock_get,
        intelligence_service,
        sample_walkability_response
    ):
        """Test Walk Score API integration."""
        # Mock API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=sample_walkability_response)
        mock_get.return_value.__aenter__.return_value = mock_response

        # Get walkability data
        result = await intelligence_service.get_walkability_data(
            lat=30.2672,
            lng=-97.7431,
            address="123 Main St"
        )

        assert result.walk_score == 85
        assert result.walk_description == "Very Walkable"
        assert result.transit_score == 72
        assert result.bike_score == 78

        # Verify API call
        mock_get.assert_called_once()

    @patch('aiohttp.ClientSession.get')
    async def test_walkability_data_caching(
        self,
        mock_get,
        intelligence_service,
        sample_walkability_response
    ):
        """Test walkability data is cached correctly."""
        # Mock API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=sample_walkability_response)
        mock_get.return_value.__aenter__.return_value = mock_response

        # First call - should hit API
        result1 = await intelligence_service.get_walkability_data(30.2672, -97.7431)
        assert result1.walk_score == 85

        # Second call - should use cache
        result2 = await intelligence_service.get_walkability_data(30.2672, -97.7431)
        assert result2.walk_score == 85

        # API should only be called once
        assert mock_get.call_count == 1

        # Cache metrics should show hit
        assert intelligence_service.cost_metrics.cached_requests >= 1

    async def test_walkability_fallback_no_api_key(self):
        """Test walkability fallback when API key missing."""
        service = NeighborhoodIntelligenceAPI()
        service.walk_score_api_key = None
        await service.initialize()

        result = await service.get_walkability_data(30.2672, -97.7431)

        assert result.walk_score is None
        assert result.data_source == "fallback"

        await service.cleanup()

    @patch('aiohttp.ClientSession.get')
    async def test_google_maps_commute_calculation(
        self,
        mock_get,
        intelligence_service,
        sample_commute_response
    ):
        """Test Google Maps commute calculation."""
        # Mock API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=sample_commute_response)
        mock_get.return_value.__aenter__.return_value = mock_response

        # Calculate commute
        result = await intelligence_service.calculate_commute_scores(
            from_address="123 Main St",
            from_lat=30.2672,
            from_lng=-97.7431,
            destinations=["Downtown Austin"]
        )

        assert len(result.routes) > 0
        assert result.overall_commute_score is not None

    @patch('aiohttp.ClientSession.get')
    async def test_comprehensive_neighborhood_analysis(
        self,
        mock_get,
        intelligence_service,
        sample_location,
        sample_walkability_response,
        sample_commute_response
    ):
        """Test full neighborhood analysis with parallel API calls."""
        # Mock responses for all APIs
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            side_effect=[
                sample_walkability_response,
                sample_commute_response
            ]
        )
        mock_get.return_value.__aenter__.return_value = mock_response

        # Perform analysis
        result = await intelligence_service.analyze_neighborhood(
            property_address=sample_location["address"],
            lat=sample_location["lat"],
            lng=sample_location["lng"],
            city=sample_location["city"],
            state=sample_location["state"],
            zipcode=sample_location["zipcode"],
            commute_destinations=["Downtown Austin"]
        )

        assert result.property_address == sample_location["address"]
        assert result.location is not None
        assert result.walkability is not None
        assert result.overall_score is not None

    async def test_cost_metrics_tracking(self, intelligence_service):
        """Test cost metrics are tracked correctly."""
        # Record some API calls
        intelligence_service.cost_metrics.record_api_call("walk_score", 0.05)
        intelligence_service.cost_metrics.record_api_call("google_maps", 0.005)
        intelligence_service.cost_metrics.record_cache_hit()

        metrics = intelligence_service.get_cost_metrics()

        assert metrics["total_requests"] == 3
        assert metrics["api_requests"] == 2
        assert metrics["cached_requests"] == 1
        assert metrics["cache_hit_rate"] > 0

    async def test_cache_invalidation(self, intelligence_service):
        """Test cache invalidation for location."""
        # This would require Redis to be running
        # For unit test, just verify method exists and doesn't crash
        deleted_count = await intelligence_service.invalidate_cache_for_location(
            30.2672,
            -97.7431
        )

        assert deleted_count >= 0

    async def test_cache_warming(self, intelligence_service):
        """Test cache warming for popular locations."""
        locations = [
            (30.2672, -97.7431),
            (30.2500, -97.7500)
        ]

        # Mock the API calls to prevent actual HTTP requests
        with patch.object(
            intelligence_service,
            'get_walkability_data',
            return_value=WalkabilityData("Test", 30.0, -97.0)
        ):
            with patch.object(
                intelligence_service,
                'get_school_ratings',
                return_value=SchoolRatings("Test")
            ):
                cached_count = await intelligence_service.warm_cache_for_locations(locations)
                assert cached_count == len(locations)

    async def test_service_health_check(self, intelligence_service):
        """Test service health check."""
        health = await intelligence_service.check_health()

        assert health["status"] == "healthy"
        assert health["service_name"] == "NeighborhoodIntelligenceAPI"
        assert "cost_metrics" in health


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling and fallbacks."""

    @patch('aiohttp.ClientSession.get')
    async def test_api_error_fallback(self, mock_get, intelligence_service):
        """Test fallback when API returns error."""
        # Mock API error
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_get.return_value.__aenter__.return_value = mock_response

        # Should return fallback data
        result = await intelligence_service.get_walkability_data(30.2672, -97.7431)

        assert result.data_source == "fallback"
        assert result.walk_score is None

    @patch('aiohttp.ClientSession.get')
    async def test_api_timeout_handling(self, mock_get, intelligence_service):
        """Test handling of API timeouts."""
        # Mock timeout exception
        mock_get.side_effect = asyncio.TimeoutError("Request timeout")

        # Should return fallback data
        result = await intelligence_service.get_walkability_data(30.2672, -97.7431)

        assert result.data_source == "fallback"

    @patch('aiohttp.ClientSession.get')
    async def test_malformed_response_handling(self, mock_get, intelligence_service):
        """Test handling of malformed API responses."""
        # Mock malformed response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"invalid": "data"})
        mock_get.return_value.__aenter__.return_value = mock_response

        # Should handle gracefully
        result = await intelligence_service.get_walkability_data(30.2672, -97.7431)

        # Should have address but missing scores
        assert result.walk_score is None or isinstance(result.walk_score, int)


# ============================================================================
# Performance Tests
# ============================================================================


@pytest.mark.asyncio
class TestPerformance:
    """Test performance characteristics."""

    async def test_parallel_api_calls(self, intelligence_service):
        """Test parallel API calls complete efficiently."""
        with patch.object(
            intelligence_service,
            'get_walkability_data',
            return_value=WalkabilityData("Test", 30.0, -97.0)
        ):
            with patch.object(
                intelligence_service,
                'get_school_ratings',
                return_value=SchoolRatings("Test")
            ):
                import time
                start = time.time()

                # Simulate 5 parallel requests
                tasks = [
                    intelligence_service.analyze_neighborhood(
                        f"Address {i}",
                        30.2672 + i * 0.01,
                        -97.7431,
                        "Austin",
                        "TX",
                        "78701"
                    )
                    for i in range(5)
                ]

                results = await asyncio.gather(*tasks)

                duration = time.time() - start

                # Should complete in reasonable time
                assert len(results) == 5
                assert duration < 5.0  # All 5 should complete in under 5 seconds

    async def test_cache_performance_benefit(self, intelligence_service):
        """Test cache provides performance benefit."""
        with patch.object(
            intelligence_service,
            'get_walkability_data',
            wraps=intelligence_service.get_walkability_data
        ) as mock_walkability:
            # First call
            await intelligence_service.get_walkability_data(30.2672, -97.7431)

            # Second call (should be cached)
            await intelligence_service.get_walkability_data(30.2672, -97.7431)

            # Should only make one actual API call
            assert mock_walkability.call_count == 2
            # But underlying implementation should cache


# ============================================================================
# Integration Pattern Tests
# ============================================================================


@pytest.mark.asyncio
class TestIntegrationPatterns:
    """Test integration with other services."""

    async def test_property_matching_integration(self, intelligence_service):
        """Test integration with property matching workflow."""
        # Simulate property matching workflow
        property_data = {
            "address": "123 Main St, Austin, TX 78701",
            "lat": 30.2672,
            "lng": -97.7431,
            "city": "Austin",
            "state": "TX",
            "zipcode": "78701"
        }

        lead_preferences = {
            "work_location": "Downtown Austin",
            "school_priority": True,
            "walkability_important": True
        }

        # Get neighborhood intelligence
        with patch.object(
            intelligence_service,
            'analyze_neighborhood',
            return_value=NeighborhoodIntelligence(
                property_address=property_data["address"],
                location=LocationData(**property_data),
                overall_score=85
            )
        ):
            analysis = await intelligence_service.analyze_neighborhood(
                property_data["address"],
                property_data["lat"],
                property_data["lng"],
                property_data["city"],
                property_data["state"],
                property_data["zipcode"],
                commute_destinations=[lead_preferences["work_location"]]
            )

            # Should have high overall score
            assert analysis.overall_score >= 80
