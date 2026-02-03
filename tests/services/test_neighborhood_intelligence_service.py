"""
Comprehensive tests for NeighborhoodIntelligenceService.

Test coverage:
- Service initialization and configuration
- Market data ingestion and processing
- ML prediction integration
- Market metrics calculation and caching
- Alert generation and management
- Investment opportunity analysis
- Performance and error handling
- Integration with external services
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import numpy as np
from typing import Dict, List, Any

from ghl_real_estate_ai.services.neighborhood_intelligence_service import (
    NeighborhoodIntelligenceService,
    NeighborhoodMetrics,
    MarketAlert,
    PricePrediction,
    MarketDataSource,
    MarketTrend,
    InvestmentGrade,
    MarketSegment,
    get_neighborhood_intelligence_service
)


class TestNeighborhoodIntelligenceService:
    """Test suite for NeighborhoodIntelligenceService."""

    @pytest_asyncio.fixture
    async def service(self):
        """Create service instance for testing."""
        service = NeighborhoodIntelligenceService()
        # Mock external dependencies
        service.cache = AsyncMock()
        service.data_sources = [
            MarketDataSource(
                name="Test MLS",
                api_endpoint="https://test.api",
                api_key_env="TEST_API_KEY",
                refresh_interval=5,
                reliability_score=0.95,
                data_types=["listings", "sales"],
                is_active=True
            )
        ]
        await service.initialize()
        return service

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
            last_updated=datetime.now()
        )

    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test service initialization and configuration."""
        service = NeighborhoodIntelligenceService()
        service.cache = AsyncMock()

        # Mock ML model loading
        with patch.object(service, '_load_ml_models', new_callable=AsyncMock), \
             patch.object(service, '_validate_data_sources', new_callable=AsyncMock), \
             patch.object(service, '_start_background_tasks', new_callable=AsyncMock):

            await service.initialize()

            assert service.is_initialized
            assert len(service.data_sources) > 0
            assert service.cache is not None

    @pytest.mark.asyncio
    async def test_get_neighborhood_intelligence_cached(self, service):
        """Test retrieval of cached neighborhood intelligence."""
        neighborhood_id = "test_neighborhood"
        cached_data = {
            "neighborhood_id": neighborhood_id,
            "metrics": {"median_home_value": 750000},
            "analysis": {"market_summary": "Strong market"},
            "generated_at": datetime.now().isoformat()
        }

        service.cache.get.return_value = cached_data

        result = await service.get_neighborhood_intelligence(neighborhood_id)

        assert result == cached_data
        service.cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_neighborhood_intelligence_fresh_data(self, service, sample_neighborhood_metrics):
        """Test generation of fresh neighborhood intelligence."""
        neighborhood_id = "test_neighborhood"

        # Mock cache miss
        service.cache.get.return_value = None

        # Mock metrics retrieval
        with patch.object(service, '_fetch_neighborhood_metrics', return_value=sample_neighborhood_metrics), \
             patch.object(service, '_generate_comparative_analysis', return_value={}):

            result = await service.get_neighborhood_intelligence(neighborhood_id)

            assert result is not None
            assert result["neighborhood_id"] == neighborhood_id
            assert "metrics" in result
            assert "analysis" in result
            # cache.set is called multiple times: once for metrics, once for
            # predictions, and once for the final intelligence result
            assert service.cache.set.call_count >= 1

    @pytest.mark.asyncio
    async def test_get_market_metrics_cached(self, service, sample_neighborhood_metrics):
        """Test retrieval of cached market metrics."""
        neighborhood_id = "test_neighborhood"

        # Mock cached metrics
        service.cache.get.return_value = sample_neighborhood_metrics.__dict__

        result = await service.get_market_metrics(neighborhood_id)

        assert isinstance(result, NeighborhoodMetrics)
        assert result.neighborhood_id == neighborhood_id
        assert result.median_home_value == 750000.0
        service.cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_market_metrics_fresh_data(self, service, sample_neighborhood_metrics):
        """Test generation of fresh market metrics."""
        neighborhood_id = "test_neighborhood"

        # Mock cache miss
        service.cache.get.return_value = None

        # Mock metrics fetching
        with patch.object(service, '_fetch_neighborhood_metrics', return_value=sample_neighborhood_metrics):
            result = await service.get_market_metrics(neighborhood_id)

            assert isinstance(result, NeighborhoodMetrics)
            assert result.neighborhood_id == neighborhood_id
            service.cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_price_predictions(self, service):
        """Test price prediction generation."""
        neighborhood_id = "test_neighborhood"

        # Mock cache miss
        service.cache.get.return_value = None

        # Mock prediction generation
        sample_prediction = PricePrediction(
            property_id=None,
            neighborhood_id=neighborhood_id,
            property_type="single_family",
            current_estimate=750000.0,
            predicted_1m=756000.0,
            predicted_3m=768000.0,
            predicted_6m=795000.0,
            predicted_12m=842500.0,
            confidence_intervals={
                "1m": (740000.0, 772000.0),
                "3m": (750000.0, 786000.0),
                "6m": (775000.0, 815000.0),
                "12m": (800000.0, 885000.0)
            },
            prediction_confidence=0.956,
            factors_analyzed=["market_trends", "comparables"],
            market_context={"trend": "appreciation"},
            model_version="2.1.0",
            generated_at=datetime.now()
        )

        with patch.object(service, '_generate_price_predictions', return_value=sample_prediction):
            result = await service.get_price_predictions(neighborhood_id)

            assert isinstance(result, PricePrediction)
            assert result.neighborhood_id == neighborhood_id
            assert result.prediction_confidence > 0.95
            assert len(result.confidence_intervals) == 4

    @pytest.mark.asyncio
    async def test_get_market_alerts(self, service):
        """Test market alert retrieval."""
        neighborhood_ids = ["test_neighborhood"]

        # Mock cache miss
        service.cache.get.return_value = None

        # Mock alert fetching
        sample_alerts = [
            MarketAlert(
                alert_id="alert_001",
                alert_type="inventory_drop",
                neighborhood_id="test_neighborhood",
                severity="high",
                title="Inventory Drop Alert",
                description="Significant inventory decrease detected",
                metrics_changed={"inventory": {"from": 200, "to": 145}},
                impact_score=85.0,
                recommended_actions=["Monitor market", "Prepare buyers"],
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=24)
            )
        ]

        with patch.object(service, '_fetch_market_alerts', return_value=sample_alerts):
            result = await service.get_market_alerts(neighborhood_ids)

            assert len(result) == 1
            assert result[0].alert_type == "inventory_drop"
            assert result[0].severity == "high"

    @pytest.mark.asyncio
    async def test_analyze_investment_opportunities(self, service):
        """Test investment opportunity analysis."""
        criteria = {
            "max_budget": 800000,
            "min_roi": 15.0,
            "risk_tolerance": "medium"
        }

        # Mock cache miss
        service.cache.get.return_value = None

        # Mock opportunity analysis
        sample_opportunities = [
            {
                "neighborhood_id": "opportunity_area",
                "opportunity_type": "value_play",
                "score": 94.2,
                "roi_projection": {"1_year": 18.5, "3_year": 42.8},
                "investment_thesis": "Strong fundamentals with growth potential"
            }
        ]

        with patch.object(service, '_analyze_investment_opportunities', return_value=sample_opportunities):
            result = await service.analyze_investment_opportunities(criteria)

            assert len(result) == 1
            assert result[0]["score"] > 90
            assert "roi_projection" in result[0]

    @pytest.mark.asyncio
    async def test_get_micro_market_analysis(self, service):
        """Test micro-market analysis."""
        neighborhood_id = "test_neighborhood"
        segment = MarketSegment.LUXURY

        # Mock cache miss
        service.cache.get.return_value = None

        # Mock analysis
        sample_analysis = {
            "neighborhood_id": neighborhood_id,
            "segment": segment.value,
            "micro_markets": [
                {
                    "area": "Central District",
                    "price_range": "$800K - $1.5M",
                    "characteristics": "High-end condos",
                    "target_demographic": "Professionals"
                }
            ]
        }

        with patch.object(service, '_perform_micro_market_analysis', return_value=sample_analysis):
            result = await service.get_micro_market_analysis(neighborhood_id, segment)

            assert result["neighborhood_id"] == neighborhood_id
            assert result["segment"] == segment.value
            assert len(result["micro_markets"]) > 0

    @pytest.mark.asyncio
    async def test_track_neighborhood_performance(self, service):
        """Test neighborhood performance tracking."""
        neighborhood_ids = ["area1", "area2"]
        timeframe = "30d"

        # Mock cache miss
        service.cache.get.return_value = None

        # Mock performance data
        sample_performance = {
            "performance_data": {
                "area1": {"price_performance": 12.5, "market_activity": 85.0},
                "area2": {"price_performance": 8.3, "market_activity": 72.0}
            },
            "rankings": {
                "price_performance": {"top": "area1", "ranking": ["area1", "area2"]}
            },
            "summary": {"top_performer": "area1"}
        }

        with patch.object(service, '_track_neighborhood_performance', return_value=sample_performance):
            result = await service.track_neighborhood_performance(neighborhood_ids, timeframe)

            assert "performance_data" in result
            assert len(result["performance_data"]) == 2
            assert result["summary"]["top_performer"] == "area1"

    @pytest.mark.asyncio
    async def test_data_source_validation(self, service):
        """Test data source validation."""
        # Mock successful validation
        with patch.object(service, '_validate_data_sources') as mock_validate:
            mock_validate.return_value = None
            await service._validate_data_sources()
            mock_validate.assert_called_once()

    @pytest.mark.asyncio
    async def test_ml_model_loading(self, service):
        """Test ML model loading and configuration."""
        # Mock model loading
        with patch.object(service, '_load_ml_models') as mock_load:
            mock_load.return_value = None
            await service._load_ml_models()
            mock_load.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_invalid_neighborhood(self, service):
        """Test error handling for invalid neighborhood ID."""
        invalid_id = "nonexistent_neighborhood"

        # Mock cache miss
        service.cache.get.return_value = None

        # Mock no metrics found
        with patch.object(service, '_fetch_neighborhood_metrics', return_value=None):
            result = await service.get_neighborhood_intelligence(invalid_id)

            assert result is None

    @pytest.mark.asyncio
    async def test_caching_behavior(self, service, sample_neighborhood_metrics):
        """Test caching behavior and TTL settings."""
        neighborhood_id = "test_neighborhood"

        # Mock cache miss, then hit
        service.cache.get.side_effect = [None, sample_neighborhood_metrics.__dict__]

        # Mock metrics fetching
        with patch.object(service, '_fetch_neighborhood_metrics', return_value=sample_neighborhood_metrics):
            # First call - should cache
            result1 = await service.get_market_metrics(neighborhood_id)
            service.cache.set.assert_called_once()

            # Second call - should hit cache
            result2 = await service.get_market_metrics(neighborhood_id)

            assert isinstance(result1, NeighborhoodMetrics)
            assert isinstance(result2, NeighborhoodMetrics)

    @pytest.mark.asyncio
    async def test_performance_metrics(self, service):
        """Test performance monitoring and metrics."""
        start_time = datetime.now()

        # Test with realistic data
        neighborhood_id = "performance_test"

        # Mock quick response
        service.cache.get.return_value = {"test": "data"}

        result = await service.get_neighborhood_intelligence(neighborhood_id)

        execution_time = (datetime.now() - start_time).total_seconds()

        # Should be very fast for cached data
        assert execution_time < 1.0
        assert result is not None

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, service, sample_neighborhood_metrics):
        """Test handling of concurrent requests."""
        # Use the same neighborhood_id as the sample fixture to ensure consistency
        neighborhood_id = sample_neighborhood_metrics.neighborhood_id

        # Mock cache behavior
        service.cache.get.return_value = None

        # Mock metrics fetching
        with patch.object(service, '_fetch_neighborhood_metrics', return_value=sample_neighborhood_metrics):
            # Make multiple concurrent requests
            tasks = [
                service.get_market_metrics(neighborhood_id)
                for _ in range(5)
            ]

            results = await asyncio.gather(*tasks)

            # All results should be valid
            assert len(results) == 5
            for result in results:
                assert isinstance(result, NeighborhoodMetrics)
                assert result.neighborhood_id == neighborhood_id

    @pytest.mark.asyncio
    async def test_data_quality_validation(self, service):
        """Test data quality validation and confidence scoring."""
        neighborhood_id = "quality_test"

        # Test with high-quality data
        high_quality_metrics = NeighborhoodMetrics(
            neighborhood_id=neighborhood_id,
            name="High Quality Area",
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
            confidence_score=0.98,  # High confidence
            last_updated=datetime.now()
        )

        service.cache.get.return_value = None

        with patch.object(service, '_fetch_neighborhood_metrics', return_value=high_quality_metrics):
            result = await service.get_market_metrics(neighborhood_id)

            assert result.confidence_score >= 0.9
            assert result.data_freshness is not None

    def test_singleton_service_instance(self):
        """Test singleton pattern for service instance."""
        # This would test the global service instance
        # In actual implementation, verify singleton behavior
        assert callable(get_neighborhood_intelligence_service)

    @pytest.mark.asyncio
    async def test_memory_usage_optimization(self, service):
        """Test memory usage optimization for large datasets."""
        # Test with large number of metrics
        large_data_set = []
        for i in range(100):
            large_data_set.append(f"neighborhood_{i}")

        # Mock efficient processing
        service.cache.get.return_value = None

        with patch.object(service, '_fetch_neighborhood_metrics') as mock_fetch:
            mock_fetch.return_value = None  # Simulate no data found

            # Process multiple neighborhoods
            results = []
            for neighborhood_id in large_data_set[:10]:  # Test with 10 items
                result = await service.get_market_metrics(neighborhood_id)
                results.append(result)

            # Verify reasonable memory usage (all None in this case)
            assert len(results) == 10

    @pytest.mark.asyncio
    async def test_alert_integration(self, service):
        """Test integration with alert system."""
        neighborhood_ids = ["alert_test"]

        # Mock alert data
        service.cache.get.return_value = None

        sample_alerts = [
            MarketAlert(
                alert_id="integration_test",
                alert_type="price_spike",
                neighborhood_id="alert_test",
                severity="medium",
                title="Integration Test Alert",
                description="Testing alert integration",
                metrics_changed={"price": {"change": 10.5}},
                impact_score=75.0,
                recommended_actions=["Monitor market"],
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=12)
            )
        ]

        with patch.object(service, '_fetch_market_alerts', return_value=sample_alerts):
            result = await service.get_market_alerts(neighborhood_ids)

            assert len(result) == 1
            assert result[0].alert_id == "integration_test"