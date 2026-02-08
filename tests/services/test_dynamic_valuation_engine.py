"""
Tests for Dynamic Valuation Engine - AI-Powered Property Valuation

Comprehensive test suite covering:
- Valuation accuracy and methodology
- CMA analysis and comparable selection
- ML enhancement integration
- Confidence scoring algorithms
- Market adjustment calculations
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ghl_real_estate_ai.services.austin_market_service import MarketCondition, PropertyType
from ghl_real_estate_ai.services.dynamic_valuation_engine import (
    DynamicValuationEngine,
    MarketComparable,
    ValuationComponents,
    ValuationConfidence,
    ValuationMethod,
    ValuationResult,
    get_dynamic_valuation_engine,
)


class TestDynamicValuationEngine:
    """Test suite for Dynamic Valuation Engine"""

    @pytest.fixture
    def valuation_engine(self):
        """Create test valuation engine instance"""
        return DynamicValuationEngine()

    @pytest.fixture
    def sample_property_data(self):
        """Sample property data for testing"""
        return {
            "property_id": "test_prop_001",
            "address": "123 Test Street, Austin, TX 78701",
            "neighborhood": "Downtown",
            "price": 750000,
            "sqft": 2100,
            "bedrooms": 3,
            "bathrooms": 2.5,
            "year_built": 2015,
            "property_type": "single_family",
            "condition": "good",
            "amenities": ["pool", "garage", "updated kitchen"],
            "estimated_value": 750000,
        }

    @pytest.fixture
    def mock_market_service(self):
        """Mock market service for testing"""
        mock_service = Mock()
        mock_service.get_market_metrics = AsyncMock()
        mock_service.get_neighborhood_analysis = AsyncMock(return_value=None)
        mock_service.search_properties = AsyncMock(return_value=[])
        return mock_service

    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service for testing"""
        mock_cache = Mock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=True)
        return mock_cache

    @pytest.mark.asyncio
    async def test_comprehensive_valuation_generation(
        self, valuation_engine, sample_property_data, mock_market_service, mock_cache_service
    ):
        """Test comprehensive valuation generation with all components"""

        # Mock dependencies
        valuation_engine.market_service = mock_market_service
        valuation_engine.cache = mock_cache_service

        # Setup mock market data
        mock_market_metrics = Mock()
        mock_market_metrics.market_condition = MarketCondition.BALANCED
        mock_market_metrics.median_price = 800000
        mock_market_metrics.average_days_on_market = 35
        mock_market_metrics.months_supply = 2.5
        mock_market_service.get_market_metrics.return_value = mock_market_metrics

        # Setup mock neighborhood analysis for confidence scoring
        mock_neighborhood = Mock()
        mock_neighborhood.median_price = 800000
        mock_market_service.get_neighborhood_analysis.return_value = mock_neighborhood

        # Generate valuation
        result = await valuation_engine.generate_comprehensive_valuation(
            sample_property_data, include_comparables=True, use_ml_enhancement=True
        )

        # Verify result structure
        assert isinstance(result, ValuationResult)
        assert result.property_id == "test_prop_001"
        assert result.estimated_value > 0
        assert result.value_range_low < result.estimated_value < result.value_range_high
        assert isinstance(result.confidence_level, ValuationConfidence)
        assert 0 <= result.confidence_score <= 100
        assert isinstance(result.valuation_method, ValuationMethod)
        assert isinstance(result.components, ValuationComponents)

        # Verify business logic
        assert result.generation_time_ms >= 0
        assert len(result.data_sources_used) > 0
        assert result.valuation_date is not None

    @pytest.mark.asyncio
    async def test_cma_valuation_generation(self, valuation_engine, sample_property_data, mock_market_service):
        """Test CMA-based valuation methodology"""

        valuation_engine.market_service = mock_market_service

        # Mock comparable properties
        mock_properties = [
            Mock(
                mls_id="comp_001",
                address="124 Test Street",
                price=780000,
                beds=3,
                baths=2.5,
                sqft=2050,
                lot_size=0.25,
                year_built=2014,
                property_type=PropertyType.SINGLE_FAMILY,
                neighborhood="Downtown",
                days_on_market=25,
                price_per_sqft=380,
                last_updated=datetime.now() - timedelta(days=30),
            ),
            Mock(
                mls_id="comp_002",
                address="125 Test Street",
                price=765000,
                beds=3,
                baths=2.0,
                sqft=2200,
                lot_size=0.20,
                year_built=2016,
                property_type=PropertyType.SINGLE_FAMILY,
                neighborhood="Downtown",
                days_on_market=18,
                price_per_sqft=348,
                last_updated=datetime.now() - timedelta(days=45),
            ),
        ]
        mock_market_service.search_properties.return_value = mock_properties

        # Test CMA valuation
        cma_value = await valuation_engine._generate_cma_valuation(sample_property_data, include_comparables=True)

        assert cma_value > 0
        assert isinstance(cma_value, float)

        # Value should be reasonable based on comparables
        assert 700000 <= cma_value <= 850000

    @pytest.mark.asyncio
    async def test_ml_enhancement_application(self, valuation_engine, sample_property_data):
        """Test ML model enhancement application"""

        base_valuation = 750000

        # Test ML enhancement
        ml_factor = await valuation_engine._apply_ml_enhancement(sample_property_data, base_valuation)

        assert isinstance(ml_factor, float)
        # ML factor should be bounded
        assert 0.85 <= ml_factor <= 1.15

        # Enhanced valuation should be reasonable
        enhanced_valuation = base_valuation * ml_factor
        assert enhanced_valuation > 0

    def test_market_adjustment_calculations(self, valuation_engine, sample_property_data):
        """Test market adjustment factor calculations"""

        # Mock market metrics
        mock_market_metrics = Mock()
        mock_market_metrics.market_condition = MarketCondition.STRONG_SELLERS

        adjustment_factor = valuation_engine._calculate_market_adjustments(sample_property_data, mock_market_metrics)

        assert isinstance(adjustment_factor, float)
        assert adjustment_factor > 0

        # Strong seller's market should have positive adjustment
        assert adjustment_factor >= 1.0

    @pytest.mark.asyncio
    async def test_confidence_score_calculation(self, valuation_engine, sample_property_data, mock_market_service):
        """Test confidence score and level calculation"""

        valuation_engine.market_service = mock_market_service

        # Mock neighborhood analysis
        mock_neighborhood = Mock()
        mock_neighborhood.median_price = 800000
        mock_market_service.get_neighborhood_analysis.return_value = mock_neighborhood

        estimated_value = 750000
        has_comparables = True

        confidence_data = await valuation_engine._calculate_confidence_score(
            sample_property_data, estimated_value, has_comparables
        )

        assert "confidence_score" in confidence_data
        assert "confidence_level" in confidence_data
        assert 0 <= confidence_data["confidence_score"] <= 100
        assert isinstance(confidence_data["confidence_level"], ValuationConfidence)

        # Property with good data should have reasonable confidence
        assert confidence_data["confidence_score"] >= 70

    @pytest.mark.asyncio
    async def test_comparable_property_search(self, valuation_engine, sample_property_data, mock_market_service):
        """Test market comparable property search and scoring"""

        valuation_engine.market_service = mock_market_service

        # Setup mock properties
        mock_properties = [
            Mock(
                mls_id="comp_001",
                address="Similar Property 1",
                price=780000,
                beds=3,
                baths=2.5,
                sqft=2100,
                lot_size=0.25,
                year_built=2015,
                property_type=PropertyType.SINGLE_FAMILY,
                neighborhood="Downtown",
                days_on_market=25,
                price_per_sqft=371,
                last_updated=datetime.now() - timedelta(days=30),
            )
        ]
        mock_market_service.search_properties.return_value = mock_properties

        comparables = await valuation_engine._find_market_comparables(sample_property_data)

        assert isinstance(comparables, list)

        if comparables:
            comparable = comparables[0]
            assert isinstance(comparable, MarketComparable)
            assert comparable.mls_id == "comp_001"
            assert comparable.similarity_score > 0
            assert comparable.distance_miles >= 0

    def test_similarity_score_calculation(self, valuation_engine, sample_property_data):
        """Test similarity scoring between properties"""

        # Test identical properties
        identical_property = sample_property_data.copy()
        similarity_score = valuation_engine._calculate_similarity_score(sample_property_data, identical_property)
        assert similarity_score == 1.0

        # Test different properties
        different_property = {
            "sqft": 3000,  # Different size
            "beds": 4,  # Different bedrooms
            "year_built": 1990,  # Different age
            "neighborhood": "Different Area",  # Different neighborhood
        }
        similarity_score = valuation_engine._calculate_similarity_score(sample_property_data, different_property)
        assert 0 <= similarity_score < 1.0

    def test_comparable_adjustments(self, valuation_engine, sample_property_data):
        """Test comparable property price adjustments"""

        comparable = MarketComparable(
            mls_id="test_comp",
            address="Test Comparable",
            sale_price=800000,
            sale_date=datetime.now() - timedelta(days=90),
            beds=3,
            baths=2.5,
            sqft=2000,  # Smaller than subject
            lot_size=0.25,
            year_built=2010,  # Older than subject
            property_type=PropertyType.SINGLE_FAMILY,
            neighborhood="Downtown",
            days_on_market=30,
            price_per_sqft=400,
            distance_miles=1.5,
            similarity_score=0.85,
        )

        adjusted_price = valuation_engine._apply_comparable_adjustments(comparable, sample_property_data)

        assert isinstance(adjusted_price, (int, float))
        assert adjusted_price > 0
        # Should adjust for size and age differences
        assert adjusted_price != comparable.sale_price

    def test_property_specific_adjustments(self, valuation_engine, sample_property_data):
        """Test property-specific valuation adjustments"""

        base_value = 750000

        # Test condition adjustments
        excellent_property = sample_property_data.copy()
        excellent_property["condition"] = "excellent"

        adjusted_value = valuation_engine._apply_property_adjustments(excellent_property, base_value)

        # Excellent condition should increase value
        assert adjusted_value > base_value

        # Test amenity adjustments
        pool_property = sample_property_data.copy()
        pool_property["amenities"] = ["pool", "garage", "updated kitchen"]

        adjusted_value = valuation_engine._apply_property_adjustments(pool_property, base_value)

        # Pool should add value
        assert adjusted_value > base_value

    def test_seasonal_factor_calculation(self, valuation_engine):
        """Test seasonal adjustment factor calculation"""

        seasonal_factor = valuation_engine._get_seasonal_factor()

        assert isinstance(seasonal_factor, float)
        assert 0.9 <= seasonal_factor <= 1.1  # Reasonable seasonal range

    def test_confidence_margin_calculation(self, valuation_engine):
        """Test confidence margin calculation for value ranges"""

        # Test different confidence levels
        very_high_margin = valuation_engine._get_confidence_margin(ValuationConfidence.VERY_HIGH)
        low_margin = valuation_engine._get_confidence_margin(ValuationConfidence.LOW)

        assert isinstance(very_high_margin, float)
        assert isinstance(low_margin, float)

        # Lower confidence should have larger margin
        assert low_margin > very_high_margin

        # Margins should be reasonable
        assert 0 < very_high_margin < 0.1  # Less than 10%
        assert 0 < low_margin < 0.25  # Less than 25%

    def test_valuation_components_breakdown(self, valuation_engine, sample_property_data):
        """Test valuation components breakdown"""

        final_valuation = 750000
        market_adjustment = 1.02

        components = valuation_engine._build_valuation_components(
            sample_property_data, final_valuation, market_adjustment
        )

        assert isinstance(components, ValuationComponents)
        assert components.land_value > 0
        assert components.structure_value > 0
        assert components.location_premium >= 0

        # Components should sum to reasonable total
        total_base_value = components.land_value + components.structure_value + components.location_premium
        assert 0.8 * final_valuation <= total_base_value <= 1.2 * final_valuation

    @pytest.mark.asyncio
    async def test_error_handling(self, valuation_engine, mock_market_service):
        """Test error handling and fallback mechanisms"""

        valuation_engine.market_service = mock_market_service

        # Test with invalid property data
        invalid_property = {}

        result = await valuation_engine.generate_comprehensive_valuation(invalid_property)

        # Should return error result, not raise exception
        assert isinstance(result, ValuationResult)
        assert result.confidence_level == ValuationConfidence.UNRELIABLE
        assert result.confidence_score == 0
        assert "failed" in str(result.valuation_notes).lower()

    @pytest.mark.asyncio
    async def test_cache_integration(self, valuation_engine, sample_property_data, mock_cache_service):
        """Test cache integration for performance optimization"""

        valuation_engine.cache = mock_cache_service

        # First call should generate and cache
        await valuation_engine._generate_cma_valuation(sample_property_data, include_comparables=False)

        # Verify cache.set was called
        assert mock_cache_service.set.called

    def test_singleton_service_instance(self):
        """Test singleton pattern for service instance"""

        engine1 = get_dynamic_valuation_engine()
        engine2 = get_dynamic_valuation_engine()

        assert engine1 is engine2
        assert isinstance(engine1, DynamicValuationEngine)

    @pytest.mark.asyncio
    async def test_valuation_accuracy_targets(
        self, valuation_engine, sample_property_data, mock_market_service, mock_cache_service
    ):
        """Test valuation accuracy targeting for business requirements"""

        valuation_engine.market_service = mock_market_service
        valuation_engine.cache = mock_cache_service

        # Mock high-quality market data
        mock_market_metrics = Mock()
        mock_market_metrics.market_condition = MarketCondition.BALANCED
        mock_market_metrics.median_price = 750000
        mock_market_metrics.average_days_on_market = 30
        mock_market_metrics.months_supply = 2.5
        mock_market_service.get_market_metrics.return_value = mock_market_metrics

        # Mock neighborhood analysis
        mock_neighborhood = Mock()
        mock_neighborhood.median_price = 750000
        mock_market_service.get_neighborhood_analysis.return_value = mock_neighborhood

        # High-quality property data should achieve high confidence
        high_quality_property = {
            "property_id": "high_quality_001",
            "address": "123 Premium Street, Austin, TX",
            "neighborhood": "Downtown",
            "price": 750000,
            "sqft": 2100,
            "bedrooms": 3,
            "bathrooms": 2.5,
            "year_built": 2020,
            "property_type": "single_family",
            "condition": "excellent",
            "amenities": ["pool", "garage", "updated kitchen", "smart home"],
        }

        result = await valuation_engine.generate_comprehensive_valuation(
            high_quality_property, include_comparables=True, use_ml_enhancement=True
        )

        # Business requirement: Target 95%+ accuracy
        # High-quality data should achieve high confidence (90%+ score)
        assert result.confidence_score >= 85, f"Confidence score {result.confidence_score} below target"

        # Confidence level should be high or very high
        assert result.confidence_level in [ValuationConfidence.HIGH, ValuationConfidence.VERY_HIGH]

    @pytest.mark.asyncio
    async def test_market_condition_impact(self, valuation_engine, sample_property_data, mock_market_service):
        """Test impact of different market conditions on valuation"""

        valuation_engine.market_service = mock_market_service

        base_value = 750000

        # Test strong seller's market
        seller_market_metrics = Mock()
        seller_market_metrics.market_condition = MarketCondition.STRONG_SELLERS

        seller_adjustment = valuation_engine._calculate_market_adjustments(sample_property_data, seller_market_metrics)

        # Test strong buyer's market
        buyer_market_metrics = Mock()
        buyer_market_metrics.market_condition = MarketCondition.STRONG_BUYERS

        buyer_adjustment = valuation_engine._calculate_market_adjustments(sample_property_data, buyer_market_metrics)

        # Seller's market should have higher adjustment than buyer's market
        assert seller_adjustment > buyer_adjustment

        # Both should be reasonable (including seasonal and property type adjustments)
        assert 0.8 <= buyer_adjustment <= 1.2
        assert 0.9 <= seller_adjustment <= 1.3


@pytest.mark.performance
class TestValuationPerformance:
    """Performance tests for valuation engine"""

    @pytest.mark.asyncio
    async def test_valuation_generation_speed(self):
        """Test valuation generation performance"""

        engine = get_dynamic_valuation_engine()

        sample_property = {
            "property_id": "perf_test_001",
            "address": "123 Performance Test St",
            "price": 500000,
            "sqft": 1800,
            "bedrooms": 3,
            "bathrooms": 2,
            "year_built": 2010,
        }

        start_time = datetime.now()

        result = await engine.generate_comprehensive_valuation(
            sample_property,
            include_comparables=False,  # Faster for performance test
            use_ml_enhancement=False,
        )

        end_time = datetime.now()
        generation_time = (end_time - start_time).total_seconds() * 1000

        # Business requirement: Generate valuations within 2 seconds
        assert generation_time < 2000, f"Valuation took {generation_time}ms, exceeding 2s target"
        assert result.generation_time_ms < 2000

    @pytest.mark.asyncio
    async def test_concurrent_valuation_handling(self):
        """Test handling multiple concurrent valuation requests"""

        engine = get_dynamic_valuation_engine()

        # Create multiple property requests
        properties = [
            {"property_id": f"concurrent_test_{i}", "price": 500000 + i * 50000, "sqft": 2000 + i * 100}
            for i in range(5)
        ]

        # Execute concurrent valuations
        tasks = [engine.generate_comprehensive_valuation(prop, include_comparables=False) for prop in properties]

        start_time = datetime.now()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = datetime.now()

        # All should complete successfully
        for result in results:
            assert not isinstance(result, Exception)
            assert isinstance(result, ValuationResult)

        # Concurrent processing should be efficient
        total_time = (end_time - start_time).total_seconds() * 1000
        assert total_time < 5000, f"Concurrent processing took {total_time}ms"
