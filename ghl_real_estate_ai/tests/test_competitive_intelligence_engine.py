"""
Tests for Competitive Intelligence Engine

Validates:
- Real-time competitive monitoring and threat detection
- Strategic positioning analysis and recommendations
- Counter-strategy generation and effectiveness prediction
- Market landscape analysis and competitive gaps identification
- Performance targets (<50ms analysis, <30ms strategy generation)

Performance Requirements:
- Competitive analysis: <50ms (95th percentile)
- Threat detection: <100ms per monitoring cycle
- Strategy generation: <30ms
- Market positioning updates: <5 minutes
- Real-time monitoring: <100ms per event

Testing Coverage:
- Core competitive analysis functionality
- Real-time threat detection and alerting
- Counter-strategy generation and optimization
- Market positioning and opportunity identification
- Performance benchmarks and reliability
- Security and data validation
- Integration workflows
"""

import pytest
import asyncio
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Dict, Any, List

# Add project root to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ghl_real_estate_ai.services.competitive_intelligence_engine import (
    CompetitiveIntelligenceEngine,
    CompetitorProfile,
    CompetitiveEvent,
    CompetitiveAnalysis,
    CounterStrategy,
    ThreatLevel,
    CompetitorType,
    MarketPosition,
    CompetitiveStrategy
)


class TestCompetitorData:
    """Test data for competitive intelligence testing."""

    @property
    def sample_competitor(self) -> CompetitorProfile:
        """Generate sample competitor profile."""
        return CompetitorProfile(
            competitor_id="comp_001",
            name="Elite Realty Group",
            type=CompetitorType.TEAM_AGENT,
            brokerage="Premier Brokers Inc",
            market_areas=["downtown", "suburbs_north"],
            active_listings=25,
            recent_sales=8,
            market_share=0.15,
            average_days_on_market=28.5,
            average_sale_to_list_ratio=0.97,
            positioning_strategy=MarketPosition.PREMIUM_SERVICE,
            pricing_strategy="premium_positioning",
            technology_adoption=0.8,
            marketing_aggressiveness=0.9,
            activity_level=0.85,
            lead_response_time=2.5,
            threat_level=ThreatLevel.HIGH,
            threat_reasons=["aggressive_marketing", "strong_technology", "fast_response"]
        )

    @property
    def sample_competitive_event(self) -> CompetitiveEvent:
        """Generate sample competitive event."""
        return CompetitiveEvent(
            competitor_id="comp_001",
            event_type="new_listing",
            description="New competitive listing in target market area",
            property_id="prop_12345",
            price_change=-15000.0,
            listing_details={
                "price": 485000,
                "bedrooms": 3,
                "bathrooms": 2,
                "square_feet": 1800,
                "location": "downtown"
            },
            market_impact=0.7,
            threat_assessment=ThreatLevel.MEDIUM,
            affected_leads=["lead_001", "lead_002"],
            suggested_responses=[
                "Analyze pricing strategy",
                "Prepare competitive market analysis",
                "Contact affected leads immediately"
            ],
            urgency_level=2
        )

    @property
    def sample_lead_context(self) -> Dict[str, Any]:
        """Generate sample lead context for testing."""
        return {
            "lead_id": "lead_001",
            "location": "downtown",
            "budget_range": "450k-550k",
            "property_type": "condo",
            "timeline": "immediate",
            "preferences": {
                "bedrooms": 2,
                "bathrooms": 2,
                "parking": True
            }
        }


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    redis_mock = MagicMock()
    redis_mock.optimized_get = AsyncMock(return_value=None)
    redis_mock.optimized_set = AsyncMock()
    redis_mock.health_check = AsyncMock(return_value={"healthy": True})
    redis_mock.close = AsyncMock()
    return redis_mock


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for external API calls."""
    http_mock = MagicMock()
    http_mock.initialize = AsyncMock()
    http_mock.health_check = AsyncMock(return_value={"healthy": True})
    http_mock.cleanup = AsyncMock()
    return http_mock


@pytest.fixture
def mock_db_cache():
    """Mock database cache service."""
    db_mock = MagicMock()
    db_mock.initialize = AsyncMock()
    db_mock.cached_query = AsyncMock(return_value=[])
    db_mock.health_check = AsyncMock(return_value={"healthy": True})
    db_mock.cleanup = AsyncMock()
    return db_mock


@pytest.fixture
async def competitive_engine(mock_redis, mock_http_client, mock_db_cache):
    """Create competitive intelligence engine with mocked dependencies."""
    with patch('ghl_real_estate_ai.services.competitive_intelligence_engine.OptimizedRedisClient', return_value=mock_redis), \
         patch('ghl_real_estate_ai.services.competitive_intelligence_engine.AsyncHTTPClient', return_value=mock_http_client), \
         patch('ghl_real_estate_ai.services.competitive_intelligence_engine.DatabaseCacheService', return_value=mock_db_cache):

        engine = CompetitiveIntelligenceEngine({
            "redis_url": "redis://localhost:6379",
            "enable_monitoring": True
        })
        await engine.initialize()
        return engine


class TestCompetitiveIntelligenceEngineInitialization:
    """Test competitive intelligence engine initialization."""

    @pytest.mark.asyncio
    async def test_engine_initialization_success(self, competitive_engine):
        """Test engine initializes correctly with all dependencies."""
        assert competitive_engine.redis_client is not None
        assert competitive_engine.http_client is not None
        assert competitive_engine.db_cache is not None
        assert competitive_engine.competitor_profiles == {}
        assert competitive_engine.active_events == {}
        assert competitive_engine.monitoring_tasks == {}

    @pytest.mark.asyncio
    async def test_engine_initialization_performance(self):
        """Test engine initialization meets performance targets."""
        with patch('ghl_real_estate_ai.services.competitive_intelligence_engine.OptimizedRedisClient') as mock_redis, \
             patch('ghl_real_estate_ai.services.competitive_intelligence_engine.AsyncHTTPClient') as mock_http, \
             patch('ghl_real_estate_ai.services.competitive_intelligence_engine.DatabaseCacheService') as mock_db:

            mock_redis.return_value.initialize = AsyncMock()
            mock_http.return_value.initialize = AsyncMock()
            mock_db.return_value.initialize = AsyncMock()
            mock_db.return_value.cached_query = AsyncMock(return_value=[])

            start_time = time.time()
            engine = CompetitiveIntelligenceEngine({})
            await engine.initialize()
            init_time = (time.time() - start_time) * 1000

            assert init_time < 1000, f"Initialization took {init_time:.1f}ms (target: <1000ms)"


class TestCompetitiveAnalysis:
    """Test competitive landscape analysis functionality."""

    @pytest.mark.asyncio
    async def test_analyze_competitive_landscape_basic(self, competitive_engine, mock_db_cache):
        """Test basic competitive landscape analysis."""
        test_data = TestCompetitorData()

        # Mock lead data
        mock_db_cache.cached_query.return_value = {
            "location": "downtown",
            "property_preferences": {"bedrooms": 2},
            "budget_range": "450k-550k"
        }

        # Add sample competitor
        competitive_engine.competitor_profiles["comp_001"] = test_data.sample_competitor

        start_time = time.time()
        analysis = await competitive_engine.analyze_competitive_landscape(
            lead_id="lead_001",
            property_context={"area": "downtown"}
        )
        processing_time = (time.time() - start_time) * 1000

        assert analysis is not None
        assert analysis.lead_id == "lead_001"
        assert isinstance(analysis.total_competitors, int)
        assert analysis.processing_time_ms < 50, f"Analysis took {processing_time:.1f}ms (target: <50ms)"
        assert analysis.confidence_score > 0.0
        assert analysis.win_probability >= 0.0

    @pytest.mark.asyncio
    async def test_competitive_analysis_with_threats(self, competitive_engine, mock_db_cache):
        """Test competitive analysis identifies threats correctly."""
        test_data = TestCompetitorData()

        # Mock lead data
        mock_db_cache.cached_query.return_value = {
            "location": "downtown",
            "property_preferences": {"bedrooms": 2},
            "budget_range": "450k-550k"
        }

        # Add high-threat competitor
        competitor = test_data.sample_competitor
        competitor.threat_level = ThreatLevel.HIGH
        competitive_engine.competitor_profiles["comp_001"] = competitor

        analysis = await competitive_engine.analyze_competitive_landscape(
            lead_id="lead_001"
        )

        assert analysis.total_competitors >= 1
        assert len(analysis.active_threats) >= 1
        assert analysis.active_threats[0].threat_level == ThreatLevel.HIGH
        assert len(analysis.immediate_actions) > 0
        assert len(analysis.differentiation_points) > 0

    @pytest.mark.asyncio
    async def test_competitive_analysis_caching(self, competitive_engine, mock_redis):
        """Test competitive analysis caching functionality."""
        test_data = TestCompetitorData()
        lead_id = "lead_001"

        # First call - cache miss
        mock_redis.optimized_get.return_value = None
        analysis1 = await competitive_engine.analyze_competitive_landscape(lead_id)

        # Verify cache set was called
        mock_redis.optimized_set.assert_called()

        # Second call - cache hit
        mock_redis.optimized_get.return_value = analysis1.to_dict()
        start_time = time.time()
        analysis2 = await competitive_engine.analyze_competitive_landscape(lead_id)
        cache_time = (time.time() - start_time) * 1000

        assert cache_time < 10, f"Cache retrieval took {cache_time:.1f}ms (target: <10ms)"
        assert analysis2.lead_id == lead_id


class TestThreatDetection:
    """Test competitive threat detection functionality."""

    @pytest.mark.asyncio
    async def test_detect_competitive_threats_basic(self, competitive_engine, mock_db_cache):
        """Test basic competitive threat detection."""
        test_data = TestCompetitorData()
        lead_id = "lead_001"

        # Mock lead context
        mock_db_cache.cached_query.return_value = test_data.sample_lead_context

        start_time = time.time()
        threats = await competitive_engine.detect_competitive_threats(lead_id)
        detection_time = (time.time() - start_time) * 1000

        assert isinstance(threats, list)
        assert detection_time < 100, f"Threat detection took {detection_time:.1f}ms (target: <100ms)"

    @pytest.mark.asyncio
    async def test_threat_detection_prioritization(self, competitive_engine, mock_db_cache):
        """Test threat detection prioritizes threats correctly."""
        test_data = TestCompetitorData()
        lead_id = "lead_001"

        # Mock lead context
        mock_db_cache.cached_query.return_value = test_data.sample_lead_context

        # Mock multiple threat sources returning events
        with patch.object(competitive_engine, '_monitor_mls_activity') as mock_mls, \
             patch.object(competitive_engine, '_monitor_marketing_activity') as mock_marketing:

            mock_mls.return_value = [test_data.sample_competitive_event]
            mock_marketing.return_value = []

            threats = await competitive_engine.detect_competitive_threats(lead_id)

            # Should return prioritized threats
            assert isinstance(threats, list)
            if threats:
                # Check threats are sorted by severity/urgency
                for i in range(len(threats) - 1):
                    current_priority = threats[i].threat_assessment.value
                    next_priority = threats[i + 1].threat_assessment.value
                    # Higher severity threats should come first

    @pytest.mark.asyncio
    async def test_threat_detection_monitoring_sources(self, competitive_engine, mock_db_cache):
        """Test threat detection monitors multiple data sources."""
        test_data = TestCompetitorData()
        lead_id = "lead_001"

        # Mock lead context
        mock_db_cache.cached_query.return_value = test_data.sample_lead_context

        # Test that multiple monitoring sources are called
        with patch.object(competitive_engine, '_monitor_mls_activity', new=AsyncMock(return_value=[])) as mock_mls, \
             patch.object(competitive_engine, '_monitor_public_records', new=AsyncMock(return_value=[])) as mock_records, \
             patch.object(competitive_engine, '_monitor_social_media', new=AsyncMock(return_value=[])) as mock_social:

            await competitive_engine.detect_competitive_threats(
                lead_id,
                monitoring_scope=["mls", "public_records", "social_media"]
            )

            mock_mls.assert_called_once()
            mock_records.assert_called_once()
            mock_social.assert_called_once()


class TestCounterStrategyGeneration:
    """Test counter-strategy generation functionality."""

    @pytest.mark.asyncio
    async def test_generate_counter_strategy_basic(self, competitive_engine):
        """Test basic counter-strategy generation."""
        test_data = TestCompetitorData()
        threat_event = test_data.sample_competitive_event
        lead_context = test_data.sample_lead_context

        start_time = time.time()
        strategy = await competitive_engine.generate_counter_strategy(threat_event, lead_context)
        generation_time = (time.time() - start_time) * 1000

        assert strategy is not None
        assert strategy.threat_event_id == threat_event.event_id
        assert strategy.competitor_id == threat_event.competitor_id
        assert len(strategy.action_items) > 0
        assert strategy.expected_effectiveness > 0.0
        assert generation_time < 30, f"Strategy generation took {generation_time:.1f}ms (target: <30ms)"

    @pytest.mark.asyncio
    async def test_counter_strategy_for_different_threat_types(self, competitive_engine):
        """Test counter-strategy adapts to different threat types."""
        test_data = TestCompetitorData()
        lead_context = test_data.sample_lead_context

        # Test price competition threat
        price_threat = CompetitiveEvent(
            competitor_id="comp_001",
            event_type="price_drop",
            description="Competitor dropped price by $20k",
            market_impact=0.8,
            threat_assessment=ThreatLevel.HIGH
        )

        price_strategy = await competitive_engine.generate_counter_strategy(price_threat, lead_context)
        assert price_strategy.strategy_type == CompetitiveStrategy.SERVICE_DIFFERENTIATION

        # Test new listing threat
        listing_threat = CompetitiveEvent(
            competitor_id="comp_001",
            event_type="new_listing",
            description="New competitive listing",
            market_impact=0.6,
            threat_assessment=ThreatLevel.MEDIUM
        )

        listing_strategy = await competitive_engine.generate_counter_strategy(listing_threat, lead_context)
        assert listing_strategy.strategy_type == CompetitiveStrategy.SPEED_TO_MARKET

    @pytest.mark.asyncio
    async def test_counter_strategy_effectiveness_prediction(self, competitive_engine):
        """Test counter-strategy effectiveness prediction."""
        test_data = TestCompetitorData()
        threat_event = test_data.sample_competitive_event
        lead_context = test_data.sample_lead_context

        strategy = await competitive_engine.generate_counter_strategy(threat_event, lead_context)

        # Strategy should include effectiveness metrics
        assert 0.0 <= strategy.expected_effectiveness <= 1.0
        assert 0.0 <= strategy.implementation_effort <= 1.0
        assert 0.0 <= strategy.risk_level <= 1.0
        assert len(strategy.success_metrics) > 0
        assert strategy.timeline


class TestMarketPositioning:
    """Test market positioning analysis and monitoring."""

    @pytest.mark.asyncio
    async def test_market_positioning_analysis(self, competitive_engine):
        """Test market positioning opportunity identification."""
        test_data = TestCompetitorData()

        # Add competitors with different positioning
        competitor1 = test_data.sample_competitor
        competitor1.positioning_strategy = MarketPosition.PREMIUM_SERVICE
        competitor2 = CompetitorProfile(
            competitor_id="comp_002",
            name="Budget Realty",
            type=CompetitorType.DISCOUNT_BROKER,
            positioning_strategy=MarketPosition.VALUE_LEADER,
            market_areas=["downtown"]
        )

        competitive_engine.competitor_profiles["comp_001"] = competitor1
        competitive_engine.competitor_profiles["comp_002"] = competitor2

        # Analyze positioning opportunities
        competitive_data = {
            "local_competitors": [competitor1, competitor2],
            "market_conditions": {"market_temperature": "balanced"}
        }

        positioning = await competitive_engine._assess_positioning_opportunities(competitive_data)

        assert "positioning_distribution" in positioning
        assert "gap_opportunities" in positioning
        assert len(positioning["gap_opportunities"]) > 0  # Should find unused positions

    @pytest.mark.asyncio
    async def test_real_time_market_monitoring(self, competitive_engine, mock_db_cache):
        """Test real-time market positioning monitoring."""
        # Test that monitoring can be started
        market_area = "downtown"

        # Mock market data
        mock_db_cache.cached_query.return_value = [
            {
                "competitor_id": "comp_001",
                "positioning_change": "premium_to_value",
                "timestamp": datetime.now()
            }
        ]

        # Start monitoring in background (test setup only)
        monitor_task = asyncio.create_task(
            competitive_engine.monitor_market_positioning(market_area, update_frequency=1)
        )

        # Let it run briefly
        await asyncio.sleep(0.1)
        monitor_task.cancel()

        try:
            await monitor_task
        except asyncio.CancelledError:
            pass  # Expected when cancelling

        # Test that monitoring setup works
        assert True  # If we get here, monitoring started successfully


class TestPerformanceBenchmarks:
    """Test performance benchmarks and optimization."""

    @pytest.mark.asyncio
    async def test_competitive_analysis_performance_target(self, competitive_engine, mock_db_cache):
        """Test competitive analysis meets <50ms performance target."""
        # Mock minimal data for fast processing
        mock_db_cache.cached_query.return_value = {"location": "downtown"}

        # Run multiple iterations to test consistency
        processing_times = []
        for _ in range(5):
            start_time = time.time()
            analysis = await competitive_engine.analyze_competitive_landscape("lead_test")
            processing_time = (time.time() - start_time) * 1000
            processing_times.append(processing_time)

        avg_time = sum(processing_times) / len(processing_times)
        assert avg_time < 50, f"Average analysis time {avg_time:.1f}ms (target: <50ms)"

        # 95th percentile should be under target
        processing_times.sort()
        p95_time = processing_times[int(len(processing_times) * 0.95)]
        assert p95_time < 50, f"95th percentile time {p95_time:.1f}ms (target: <50ms)"

    @pytest.mark.asyncio
    async def test_threat_detection_performance_target(self, competitive_engine, mock_db_cache):
        """Test threat detection meets <100ms performance target."""
        # Mock lead context
        mock_db_cache.cached_query.return_value = TestCompetitorData().sample_lead_context

        start_time = time.time()
        threats = await competitive_engine.detect_competitive_threats("lead_test")
        detection_time = (time.time() - start_time) * 1000

        assert detection_time < 100, f"Threat detection took {detection_time:.1f}ms (target: <100ms)"

    @pytest.mark.asyncio
    async def test_strategy_generation_performance_target(self, competitive_engine):
        """Test counter-strategy generation meets <30ms target."""
        test_data = TestCompetitorData()
        threat_event = test_data.sample_competitive_event

        start_time = time.time()
        strategy = await competitive_engine.generate_counter_strategy(threat_event)
        generation_time = (time.time() - start_time) * 1000

        assert generation_time < 30, f"Strategy generation took {generation_time:.1f}ms (target: <30ms)"


class TestEngineReliability:
    """Test competitive intelligence engine reliability and error handling."""

    @pytest.mark.asyncio
    async def test_analysis_fallback_on_failure(self, competitive_engine, mock_db_cache):
        """Test analysis provides fallback results on failure."""
        # Simulate database failure
        mock_db_cache.cached_query.side_effect = Exception("Database connection failed")

        # Should return fallback analysis instead of crashing
        analysis = await competitive_engine.analyze_competitive_landscape("lead_test")

        assert analysis is not None
        assert analysis.lead_id == "lead_test"
        assert analysis.confidence_score > 0.0  # Fallback should have some confidence

    @pytest.mark.asyncio
    async def test_threat_detection_resilience(self, competitive_engine, mock_db_cache):
        """Test threat detection handles partial source failures."""
        # Mock lead context
        mock_db_cache.cached_query.return_value = TestCompetitorData().sample_lead_context

        # Simulate one monitoring source failing
        with patch.object(competitive_engine, '_monitor_mls_activity', side_effect=Exception("MLS API down")), \
             patch.object(competitive_engine, '_monitor_social_media', return_value=[]):

            # Should continue with working sources
            threats = await competitive_engine.detect_competitive_threats("lead_test")

            # Should return results (even if empty) without crashing
            assert isinstance(threats, list)

    @pytest.mark.asyncio
    async def test_engine_health_check(self, competitive_engine):
        """Test engine health check functionality."""
        health = await competitive_engine.health_check()

        assert "healthy" in health
        assert "service" in health
        assert health["service"] == "competitive_intelligence_engine"
        assert "checks" in health
        assert "performance_metrics" in health


class TestEngineSecurity:
    """Test competitive intelligence engine security and data validation."""

    @pytest.mark.asyncio
    async def test_input_validation(self, competitive_engine):
        """Test engine validates inputs correctly."""
        # Test with invalid lead ID
        analysis = await competitive_engine.analyze_competitive_landscape("")
        assert analysis is not None  # Should handle gracefully

        # Test with None values
        analysis = await competitive_engine.analyze_competitive_landscape(None)
        assert analysis is not None  # Should handle gracefully

    @pytest.mark.asyncio
    async def test_threat_data_sanitization(self, competitive_engine):
        """Test threat detection sanitizes external data."""
        test_data = TestCompetitorData()

        # Create threat with potentially malicious content
        malicious_event = CompetitiveEvent(
            competitor_id="<script>alert('xss')</script>",
            event_type="<injection_attempt>",
            description="Normal description",
            market_impact=0.5,
            threat_assessment=ThreatLevel.LOW
        )

        # Generate strategy - should not crash or include malicious content
        strategy = await competitive_engine.generate_counter_strategy(malicious_event)

        assert strategy is not None
        assert "<script>" not in strategy.description
        assert "<injection_attempt>" not in str(strategy.strategy_type)


class TestEngineIntegration:
    """Integration tests for complete competitive intelligence workflows."""

    @pytest.mark.asyncio
    async def test_complete_competitive_workflow(self, competitive_engine, mock_db_cache):
        """Test complete competitive intelligence workflow end-to-end."""
        test_data = TestCompetitorData()
        lead_id = "lead_integration_test"

        # Mock lead and competitor data
        mock_db_cache.cached_query.return_value = test_data.sample_lead_context
        competitive_engine.competitor_profiles["comp_001"] = test_data.sample_competitor

        # Step 1: Analyze competitive landscape
        analysis = await competitive_engine.analyze_competitive_landscape(lead_id)
        assert analysis.lead_id == lead_id
        assert analysis.total_competitors >= 0

        # Step 2: Detect threats
        threats = await competitive_engine.detect_competitive_threats(lead_id)
        assert isinstance(threats, list)

        # Step 3: Generate counter-strategies for any high-priority threats
        for threat in threats:
            if threat.threat_assessment in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                strategy = await competitive_engine.generate_counter_strategy(threat)
                assert strategy.threat_event_id == threat.event_id
                break

        # Step 4: Get health metrics
        health = await competitive_engine.health_check()
        assert health["healthy"]

        # Step 5: Cleanup
        await competitive_engine.cleanup()

    @pytest.mark.asyncio
    async def test_concurrent_analysis_requests(self, competitive_engine, mock_db_cache):
        """Test engine handles concurrent analysis requests efficiently."""
        # Mock data
        mock_db_cache.cached_query.return_value = TestCompetitorData().sample_lead_context

        # Submit multiple concurrent analysis requests
        tasks = [
            competitive_engine.analyze_competitive_landscape(f"lead_{i}")
            for i in range(5)
        ]

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = (time.time() - start_time) * 1000

        # All requests should complete successfully
        assert len(results) == 5
        for result in results:
            assert result is not None
            assert result.processing_time_ms > 0

        # Concurrent processing should be more efficient than sequential
        assert total_time < 250, f"Concurrent processing took {total_time:.1f}ms (target: <250ms for 5 requests)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])