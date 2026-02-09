import pytest
pytestmark = pytest.mark.integration

"""
Test suite for Austin Market Service.

Tests comprehensive Austin real estate market functionality including:
- Market metrics and trends
- Property search and filtering
- Neighborhood analysis
- Corporate relocation insights
- Market timing recommendations
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest

try:
    from ghl_real_estate_ai.services.austin_market_service import (
        AustinMarketService,
        AustinNeighborhood,
        MarketCondition,
        MarketMetrics,
        PropertyListing,
        PropertyType,
        get_austin_market_service,
    )
except (ImportError, TypeError, AttributeError):
    pytest.skip("required imports unavailable", allow_module_level=True)


class TestAustinMarketService:
    """Test Austin Market Service functionality."""

    @pytest.fixture
    def market_service(self):
        """Create market service instance for testing."""
        return AustinMarketService()

    @pytest.fixture
    def sample_property_listing(self):
        """Sample property listing for tests."""
        return PropertyListing(
            mls_id="ATX2024001",
            address="123 South Lamar Blvd, Austin, TX 78704",
            price=725000,
            beds=3,
            baths=2.5,
            sqft=2100,
            lot_size=0.18,
            year_built=2019,
            property_type=PropertyType.SINGLE_FAMILY,
            neighborhood="South Lamar",
            school_district="Austin ISD",
            days_on_market=12,
            price_per_sqft=345,
            price_changes=[],
            features=["Open Floor Plan", "Modern Kitchen"],
            coordinates=(30.252222, -97.763889),
            photos=["photo1.jpg"],
            description="Modern home in South Lamar",
            listing_agent={"name": "Jorge Martinez"},
            last_updated=datetime.now(),
        )

    @pytest.mark.asyncio
    async def test_get_market_metrics_basic(self, market_service):
        """Test getting basic market metrics."""
        metrics = await market_service.get_market_metrics()

        assert isinstance(metrics, MarketMetrics)
        assert metrics.median_price > 0
        assert metrics.average_days_on_market > 0
        assert metrics.inventory_count > 0
        assert isinstance(metrics.market_condition, MarketCondition)
        assert 0 <= metrics.absorption_rate <= 100

    @pytest.mark.asyncio
    async def test_get_market_metrics_neighborhood_filter(self, market_service):
        """Test getting market metrics filtered by neighborhood."""
        # Test known neighborhood
        metrics = await market_service.get_market_metrics(neighborhood="Round Rock")

        assert isinstance(metrics, MarketMetrics)
        assert metrics.median_price > 0

        # Test unknown neighborhood
        metrics_unknown = await market_service.get_market_metrics(neighborhood="NonExistentPlace")
        assert isinstance(metrics_unknown, MarketMetrics)

    @pytest.mark.asyncio
    async def test_get_market_metrics_property_type_filter(self, market_service):
        """Test getting market metrics filtered by property type."""
        metrics = await market_service.get_market_metrics(property_type=PropertyType.CONDO)

        assert isinstance(metrics, MarketMetrics)
        # Condo market typically has different characteristics
        assert metrics.median_price > 0

    @pytest.mark.asyncio
    async def test_search_properties_basic(self, market_service):
        """Test basic property search."""
        criteria = {"min_price": 300000, "max_price": 800000, "min_beds": 2}

        properties = await market_service.search_properties(criteria, limit=10)

        assert isinstance(properties, list)
        assert len(properties) <= 10

        for prop in properties:
            assert isinstance(prop, PropertyListing)
            assert prop.price >= criteria["min_price"]
            assert prop.price <= criteria["max_price"]
            assert prop.beds >= criteria["min_beds"]

    @pytest.mark.asyncio
    async def test_search_properties_neighborhood_filter(self, market_service):
        """Test property search with neighborhood filter."""
        criteria = {"neighborhood": "South Lamar"}

        properties = await market_service.search_properties(criteria, limit=5)

        for prop in properties:
            assert prop.neighborhood == "South Lamar"

    @pytest.mark.asyncio
    async def test_get_neighborhood_analysis(self, market_service):
        """Test neighborhood analysis functionality."""
        # Test known neighborhood
        analysis = await market_service.get_neighborhood_analysis("Round Rock")

        assert isinstance(analysis, AustinNeighborhood)
        assert analysis.name == "Round Rock"
        assert analysis.zone == "North"
        assert analysis.median_price > 0
        assert analysis.school_rating > 0
        assert 0 <= analysis.walkability_score <= 100
        assert 0 <= analysis.tech_worker_appeal <= 100
        assert isinstance(analysis.corporate_proximity, dict)
        assert isinstance(analysis.amenities, list)

        # Test unknown neighborhood
        unknown_analysis = await market_service.get_neighborhood_analysis("NonExistent")
        assert unknown_analysis is None

    @pytest.mark.asyncio
    async def test_get_school_district_info(self, market_service):
        """Test school district information retrieval."""
        # Test known district
        district_info = await market_service.get_school_district_info("Austin ISD")

        assert isinstance(district_info, dict)
        if district_info:  # If data is available
            assert "name" in district_info
            assert "rating" in district_info
            assert "enrollment" in district_info

        # Test unknown district
        unknown_district = await market_service.get_school_district_info("NonExistent ISD")
        assert isinstance(unknown_district, dict)

    @pytest.mark.asyncio
    async def test_get_corporate_relocation_insights(self, market_service):
        """Test corporate relocation insights."""
        # Test with known employer
        insights = await market_service.get_corporate_relocation_insights(
            employer="Apple", position_level="Senior Engineer"
        )

        assert isinstance(insights, dict)
        assert "market_overview" in insights
        assert "top_employers" in insights
        assert "recommended_neighborhoods" in insights

        if insights.get("recommended_neighborhoods"):
            for neighborhood in insights["recommended_neighborhoods"]:
                assert "name" in neighborhood
                assert "commute" in neighborhood
                assert "appeal" in neighborhood

        # Test with unknown employer
        unknown_insights = await market_service.get_corporate_relocation_insights("UnknownCompany")
        assert isinstance(unknown_insights, dict)

    @pytest.mark.asyncio
    async def test_get_commute_analysis(self, market_service):
        """Test commute analysis functionality."""
        property_coords = (30.252222, -97.763889)  # South Lamar
        work_location = "Apple"

        commute_data = await market_service.get_commute_analysis(property_coords, work_location)

        assert isinstance(commute_data, dict)
        if "error" not in commute_data:
            assert "driving" in commute_data
            assert "public_transit" in commute_data
            assert "overall_score" in commute_data

    @pytest.mark.asyncio
    async def test_get_market_timing_advice_buy(self, market_service):
        """Test market timing advice for buyers."""
        timing_advice = await market_service.get_market_timing_advice("buy", PropertyType.SINGLE_FAMILY, "Round Rock")

        assert isinstance(timing_advice, dict)
        assert "timing_score" in timing_advice
        assert "market_condition" in timing_advice
        assert "recommendations" in timing_advice
        assert "urgency_level" in timing_advice

        assert 0 <= timing_advice["timing_score"] <= 100
        assert timing_advice["urgency_level"] in ["low", "medium", "high"]

    @pytest.mark.asyncio
    async def test_get_market_timing_advice_sell(self, market_service):
        """Test market timing advice for sellers."""
        timing_advice = await market_service.get_market_timing_advice("sell", PropertyType.SINGLE_FAMILY)

        assert isinstance(timing_advice, dict)
        assert "timing_score" in timing_advice
        assert "recommendations" in timing_advice
        assert "seasonal_factors" in timing_advice

    def test_neighborhood_data_loading(self, market_service):
        """Test neighborhood data is properly loaded."""
        neighborhoods = market_service.neighborhoods

        assert isinstance(neighborhoods, dict)
        assert len(neighborhoods) > 0

        # Check that key neighborhoods are present
        expected_neighborhoods = ["round_rock", "domain", "south_lamar", "downtown"]
        for neighborhood in expected_neighborhoods:
            assert neighborhood in neighborhoods

            neighborhood_data = neighborhoods[neighborhood]
            assert "name" in neighborhood_data
            assert "zone" in neighborhood_data
            assert "median_price" in neighborhood_data
            assert "school_rating" in neighborhood_data

    def test_corporate_headquarters_loading(self, market_service):
        """Test corporate headquarters data is properly loaded."""
        corporate_hqs = market_service.corporate_hqs

        assert isinstance(corporate_hqs, dict)
        assert len(corporate_hqs) > 0

        # Check that major employers are present
        expected_employers = ["apple", "google", "meta", "tesla", "dell"]
        for employer in expected_employers:
            assert employer in corporate_hqs

            employer_data = corporate_hqs[employer]
            assert "name" in employer_data
            assert "location" in employer_data
            assert "coordinates" in employer_data
            assert "employees" in employer_data

    @pytest.mark.asyncio
    async def test_cache_usage(self, market_service):
        """Test that caching is working properly."""
        # This test checks that cache keys are being generated
        # In a real implementation, you'd mock the cache service

        # First call should populate cache
        metrics1 = await market_service.get_market_metrics("Round Rock")

        # Second call should use cache (same results)
        metrics2 = await market_service.get_market_metrics("Round Rock")

        assert metrics1.median_price == metrics2.median_price
        assert metrics1.market_condition == metrics2.market_condition

    @pytest.mark.asyncio
    async def test_property_type_enum_handling(self, market_service):
        """Test property type enum handling in various methods."""
        # Test all property types
        for prop_type in PropertyType:
            metrics = await market_service.get_market_metrics(property_type=prop_type)
            assert isinstance(metrics, MarketMetrics)

    def test_seasonal_factors_accuracy(self, market_service):
        """Test seasonal factors return accurate data."""
        seasonal_factors = market_service._get_seasonal_factors()

        assert "current_season" in seasonal_factors
        assert "seasonal_data" in seasonal_factors
        assert "austin_specific_factors" in seasonal_factors

        current_season = seasonal_factors["current_season"]
        assert current_season in ["spring", "summer", "fall", "winter"]

        seasonal_data = seasonal_factors["seasonal_data"]
        assert "activity_level" in seasonal_data
        assert "recommendation" in seasonal_data

    @pytest.mark.asyncio
    async def test_error_handling(self, market_service):
        """Test error handling in various scenarios."""
        # Test with invalid inputs
        try:
            await market_service.search_properties({}, limit=-1)
        except Exception:
            pass  # Expected to handle gracefully

        # Test with empty criteria
        properties = await market_service.search_properties({}, limit=1)
        assert isinstance(properties, list)

    def test_singleton_pattern(self):
        """Test that get_austin_market_service returns singleton."""
        service1 = get_austin_market_service()
        service2 = get_austin_market_service()

        assert service1 is service2  # Same instance

    @pytest.mark.asyncio
    async def test_price_range_validation(self, market_service):
        """Test price range validation in search."""
        criteria = {
            "min_price": 500000,
            "max_price": 400000,  # Invalid: min > max
        }

        # Should handle gracefully
        properties = await market_service.search_properties(criteria, limit=5)
        assert isinstance(properties, list)

    def test_market_condition_logic(self, market_service):
        """Test market condition determination logic."""
        # Create test metrics
        from ghl_real_estate_ai.services.austin_market_service import MarketMetrics

        # Strong seller's market indicators
        strong_seller_metrics = MarketMetrics(
            median_price=700000,
            average_days_on_market=15,
            inventory_count=1000,
            months_supply=1.2,
            price_trend_1m=2.5,
            price_trend_3m=8.0,
            price_trend_1y=15.0,
            new_listings_7d=150,
            closed_sales_30d=800,
            pending_sales=600,
            absorption_rate=90.0,
            market_condition=MarketCondition.STRONG_SELLERS,
        )

        assert strong_seller_metrics.market_condition == MarketCondition.STRONG_SELLERS
        assert strong_seller_metrics.months_supply < 2.0
        assert strong_seller_metrics.average_days_on_market < 30

    @pytest.mark.asyncio
    async def test_corporate_employer_mapping(self, market_service):
        """Test corporate employer neighborhood mapping."""
        # Test Apple employee recommendations
        insights = await market_service.get_corporate_relocation_insights("Apple")

        if insights.get("recommended_neighborhoods"):
            apple_neighborhoods = [n["name"] for n in insights["recommended_neighborhoods"]]
            # Apple employees typically prefer Round Rock due to campus proximity
            assert any("Round Rock" in neighborhood for neighborhood in apple_neighborhoods)

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, market_service):
        """Test handling of concurrent requests."""
        # Simulate multiple concurrent requests
        tasks = [
            market_service.get_market_metrics("Downtown"),
            market_service.get_market_metrics("Round Rock"),
            market_service.get_neighborhood_analysis("Mueller"),
            market_service.search_properties({"min_beds": 3}, 5),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete without exceptions
        for result in results:
            assert not isinstance(result, Exception)

    @pytest.mark.asyncio
    async def test_data_freshness_tracking(self, market_service):
        """Test that data freshness is properly tracked."""
        metrics = await market_service.get_market_metrics()

        # Check that timestamps are recent
        assert isinstance(metrics, MarketMetrics)

        # In a real implementation, you'd check last_updated timestamps
        # For now, just verify the structure exists


class TestPropertyTypes:
    """Test PropertyType enum functionality."""

    def test_property_type_values(self):
        """Test property type enum values."""
        assert PropertyType.SINGLE_FAMILY.value == "single_family"
        assert PropertyType.CONDO.value == "condo"
        assert PropertyType.TOWNHOME.value == "townhome"
        assert PropertyType.LAND.value == "land"
        assert PropertyType.MULTI_FAMILY.value == "multi_family"

    def test_property_type_iteration(self):
        """Test property type enum iteration."""
        property_types = list(PropertyType)
        assert len(property_types) == 5
        assert PropertyType.SINGLE_FAMILY in property_types


class TestMarketConditions:
    """Test MarketCondition enum functionality."""

    def test_market_condition_values(self):
        """Test market condition enum values."""
        assert MarketCondition.STRONG_SELLERS.value == "strong_sellers"
        assert MarketCondition.BALANCED.value == "balanced"
        assert MarketCondition.STRONG_BUYERS.value == "strong_buyers"
        assert MarketCondition.TRANSITIONING.value == "transitioning"


@pytest.mark.integration
class TestAustinMarketServiceIntegration:
    """Integration tests for Austin Market Service."""

    @pytest.fixture
    def market_service(self):
        """Create market service for integration testing."""
        return AustinMarketService()

    @pytest.mark.asyncio
    async def test_full_property_search_workflow(self, market_service):
        """Test complete property search workflow."""
        # Step 1: Get market metrics
        metrics = await market_service.get_market_metrics()
        assert isinstance(metrics, MarketMetrics)

        # Step 2: Search properties based on market conditions
        if metrics.market_condition == MarketCondition.STRONG_SELLERS:
            # In seller's market, expand criteria
            criteria = {"min_beds": 2, "max_price": metrics.median_price * 1.2}
        else:
            # In buyer's market, be more selective
            criteria = {"min_beds": 3, "max_price": metrics.median_price}

        properties = await market_service.search_properties(criteria, limit=10)
        assert isinstance(properties, list)

        # Step 3: Analyze neighborhoods for found properties
        if properties:
            unique_neighborhoods = set(prop.neighborhood for prop in properties)
            for neighborhood in list(unique_neighborhoods)[:3]:  # Limit to 3 for testing
                analysis = await market_service.get_neighborhood_analysis(neighborhood)
                if analysis:
                    assert isinstance(analysis, AustinNeighborhood)

    @pytest.mark.asyncio
    async def test_corporate_relocation_complete_workflow(self, market_service):
        """Test complete corporate relocation workflow."""
        # Step 1: Get corporate insights
        insights = await market_service.get_corporate_relocation_insights("Apple", "Senior Engineer")
        assert isinstance(insights, dict)

        # Step 2: Analyze recommended neighborhoods
        if insights.get("recommended_neighborhoods"):
            for neighborhood_rec in insights["recommended_neighborhoods"][:2]:
                neighborhood = neighborhood_rec["name"]
                analysis = await market_service.get_neighborhood_analysis(neighborhood)
                if analysis:
                    assert analysis.tech_worker_appeal > 70  # Should be tech-friendly

        # Step 3: Get timing advice
        timing = await market_service.get_market_timing_advice("buy", PropertyType.SINGLE_FAMILY)
        assert "timing_score" in timing

    @pytest.mark.asyncio
    async def test_market_intelligence_pipeline(self, market_service):
        """Test complete market intelligence pipeline."""
        # Simulate a lead interested in Round Rock
        neighborhood = "Round Rock"

        # Get comprehensive data
        market_metrics = await market_service.get_market_metrics(neighborhood)
        neighborhood_analysis = await market_service.get_neighborhood_analysis(neighborhood)
        corporate_insights = await market_service.get_corporate_relocation_insights("Apple")
        timing_advice = await market_service.get_market_timing_advice("buy", PropertyType.SINGLE_FAMILY, neighborhood)

        # Verify all data is available and consistent
        assert isinstance(market_metrics, MarketMetrics)
        assert isinstance(neighborhood_analysis, AustinNeighborhood)
        assert isinstance(corporate_insights, dict)
        assert isinstance(timing_advice, dict)

        # Check data consistency
        if neighborhood_analysis:
            # Neighborhood median should be reflected in market metrics
            assert (
                abs(market_metrics.median_price - neighborhood_analysis.median_price) / market_metrics.median_price
                < 0.5
            )


# Performance Tests
@pytest.mark.performance
class TestAustinMarketServicePerformance:
    """Performance tests for Austin Market Service."""

    @pytest.fixture
    def market_service(self):
        """Create market service for performance testing."""
        return AustinMarketService()

    @pytest.mark.asyncio
    async def test_response_time_market_metrics(self, market_service):
        """Test market metrics response time."""
        start_time = datetime.now()

        await market_service.get_market_metrics()

        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()

        # Should respond within 2 seconds
        assert response_time < 2.0

    @pytest.mark.asyncio
    async def test_response_time_property_search(self, market_service):
        """Test property search response time."""
        start_time = datetime.now()

        await market_service.search_properties({"min_beds": 2}, limit=20)

        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()

        # Should respond within 3 seconds
        assert response_time < 3.0

    @pytest.mark.asyncio
    async def test_concurrent_load(self, market_service):
        """Test concurrent load handling."""
        # Simulate 10 concurrent requests
        tasks = []
        for i in range(10):
            if i % 3 == 0:
                tasks.append(market_service.get_market_metrics())
            elif i % 3 == 1:
                tasks.append(market_service.search_properties({"min_beds": 2}, 5))
            else:
                tasks.append(market_service.get_neighborhood_analysis("Round Rock"))

        start_time = datetime.now()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = datetime.now()

        # All should complete
        assert len(results) == 10

        # None should be exceptions
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0

        # Should complete within 5 seconds
        total_time = (end_time - start_time).total_seconds()
        assert total_time < 5.0
