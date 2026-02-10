"""
Tests for Analytics Coordinator

This module tests the AnalyticsCoordinator including component orchestration,
event handling, and comprehensive analytics generation.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.analytics.analytics_coordinator import (
    AnalyticsCoordinator, AnalyticsConfiguration, AnalyticsSession
)
from src.analytics.executive_analytics_engine import (
    ExecutiveSummary, StakeholderType, CompetitiveIntelligence, PredictionData
)
from src.analytics.landscape_mapper import (
    CompetitorProfile, MarketSegment, LandscapeAnalysis
)
from src.analytics.market_share_analytics import (
    MarketShareDataPoint, MarketShareAnalysis
)
from src.core.event_bus import EventType, EventPriority, Event

@pytest.mark.unit


class TestAnalyticsCoordinator:
    """Test suite for Analytics Coordinator."""
    
    @pytest.fixture
    def mock_event_bus(self):
        """Mock event bus for testing."""
        mock_bus = MagicMock()
        mock_bus.publish = AsyncMock()
        return mock_bus
    
    @pytest.fixture
    def analytics_config(self):
        """Analytics configuration for testing."""
        return AnalyticsConfiguration(
            executive_analytics_enabled=True,
            landscape_mapping_enabled=True,
            market_share_analytics_enabled=True,
            default_stakeholder=StakeholderType.CEO,
            summary_cache_minutes=5,
            analysis_cache_minutes=10,
            min_data_points=6
        )
    
    @pytest.fixture
    def analytics_coordinator(self, analytics_config, mock_event_bus):
        """Analytics coordinator with mocked dependencies."""
        return AnalyticsCoordinator(
            config=analytics_config,
            event_bus=mock_event_bus
        )
    
    @pytest.fixture
    def sample_intelligence_data(self):
        """Sample competitive intelligence data."""
        return [
            CompetitiveIntelligence(
                competitor_id="comp_001",
                competitor_name="Competitor A",
                activity_type="product_launch",
                activity_data={"product": "AI Platform"},
                timestamp=datetime.now(timezone.utc),
                confidence_score=0.9,
                source="monitor"
            )
        ]
    
    @pytest.fixture
    def sample_competitor_profiles(self):
        """Sample competitor profiles."""
        return [
            CompetitorProfile(
                competitor_id="comp_001",
                name="Tech Leader",
                revenue=1000000000.0,
                customer_count=50000,
                market_segments={"Enterprise"}
            )
        ]
    
    @pytest.fixture
    def sample_market_segments(self):
        """Sample market segments."""
        return [
            MarketSegment(
                segment_id="seg_001",
                name="Enterprise",
                size=5000000000.0,
                growth_rate=0.15,
                customer_count=10000,
                avg_deal_size=50000,
                competitive_intensity=0.8,
                key_features=["ai", "automation"],
                price_sensitivity=0.3,
                technology_adoption="mainstream"
            )
        ]
    
    @pytest.fixture
    def sample_market_share_data(self):
        """Sample market share data."""
        base_date = datetime.now(timezone.utc) - timedelta(days=180)
        return [
            MarketShareDataPoint(
                competitor_id="comp_001",
                market_segment="Enterprise",
                timestamp=base_date + timedelta(days=i * 30),
                market_share=0.4 + (i * 0.01),
                revenue=1000000.0 * (0.4 + (i * 0.01))
            )
            for i in range(6)
        ]
    
    @pytest.mark.asyncio
    async def test_initialize_coordinator(self, analytics_coordinator, analytics_config):
        """Test coordinator initialization."""
        assert analytics_coordinator is not None
        assert analytics_coordinator.config == analytics_config
        assert analytics_coordinator.sessions_completed == 0
        assert analytics_coordinator.analytics_triggered == 0
        assert len(analytics_coordinator.active_sessions) == 0
        
        # Verify event types are properly configured
        expected_event_types = [
            EventType.INTELLIGENCE_INSIGHT_CREATED,
            EventType.COMPETITOR_ACTIVITY_DETECTED,
            EventType.PREDICTION_GENERATED,
            EventType.DEEP_LEARNING_PREDICTION,
            EventType.EXECUTIVE_SUMMARY_CREATED,
            EventType.LANDSCAPE_MAPPED,
            EventType.MARKET_SHARE_CALCULATED,
            EventType.STRATEGIC_PATTERN_IDENTIFIED,
        ]
        
        for event_type in expected_event_types:
            assert event_type in analytics_coordinator.event_types
    
    @pytest.mark.asyncio
    async def test_start_coordinator(self, analytics_coordinator):
        """Test coordinator startup process."""
        # Mock the analytics components initialization
        with patch('src.analytics.analytics_coordinator.ExecutiveAnalyticsEngine') as mock_exec, \
             patch('src.analytics.analytics_coordinator.LandscapeMapper') as mock_landscape, \
             patch('src.analytics.analytics_coordinator.MarketShareAnalytics') as mock_market:
            
            await analytics_coordinator.start()
            
            # Verify components were initialized
            assert analytics_coordinator.executive_engine is not None
            assert analytics_coordinator.landscape_mapper is not None
            assert analytics_coordinator.market_share_analytics is not None
            
            # Verify component constructors were called
            mock_exec.assert_called_once()
            mock_landscape.assert_called_once()
            mock_market.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_coordinator(self, analytics_coordinator):
        """Test coordinator shutdown process."""
        # Create a mock active session
        session = AnalyticsSession(
            session_id="test_session",
            correlation_id="test_corr",
            started_at=datetime.now(),
            components_active={"executive_analytics"}
        )
        analytics_coordinator.active_sessions["test_session"] = session
        
        await analytics_coordinator.stop()
        
        # Verify cleanup
        assert len(analytics_coordinator.active_sessions) == 0
        assert analytics_coordinator.executive_engine is None
        assert analytics_coordinator.landscape_mapper is None
        assert analytics_coordinator.market_share_analytics is None
    
    @pytest.mark.asyncio
    async def test_generate_comprehensive_analytics(
        self, analytics_coordinator, sample_intelligence_data,
        sample_competitor_profiles, sample_market_segments, sample_market_share_data
    ):
        """Test comprehensive analytics generation."""
        # Mock analytics components
        mock_executive = MagicMock()
        mock_executive.generate_executive_summary = AsyncMock(return_value=MagicMock(
            summary_id="test_summary",
            stakeholder_type=StakeholderType.CEO,
            executive_bullets=["Test insight"]
        ))
        
        mock_landscape = MagicMock()
        mock_landscape.map_competitive_positions = AsyncMock(return_value=MagicMock(
            analysis_id="test_analysis",
            market_segments=sample_market_segments,
            competitor_positions=[],
            strategic_gaps=[]
        ))
        
        mock_market = MagicMock()
        mock_market.generate_comprehensive_analysis = AsyncMock(return_value=MagicMock(
            analysis_id="test_market_analysis",
            market_segments=["Enterprise"],
            forecasts=[],
            competitive_dynamics=[]
        ))
        
        analytics_coordinator.executive_engine = mock_executive
        analytics_coordinator.landscape_mapper = mock_landscape
        analytics_coordinator.market_share_analytics = mock_market
        
        # Generate comprehensive analytics
        results = await analytics_coordinator.generate_comprehensive_analytics(
            intelligence_data=sample_intelligence_data,
            competitor_profiles=sample_competitor_profiles,
            market_segments=sample_market_segments,
            market_share_data=sample_market_share_data,
            stakeholder_type=StakeholderType.CEO,
            correlation_id="test_correlation"
        )
        
        # Verify results structure
        assert "session_id" in results
        assert "correlation_id" in results
        assert results["correlation_id"] == "test_correlation"
        assert results["stakeholder_type"] == "ceo"
        assert "executive_summary" in results
        assert "landscape_analysis" in results
        assert "market_share_analysis" in results
        assert "session_performance" in results
        
        # Verify all components were called
        mock_executive.generate_executive_summary.assert_called_once()
        mock_landscape.map_competitive_positions.assert_called_once()
        mock_market.generate_comprehensive_analysis.assert_called_once()
        
        # Verify metrics updated
        assert analytics_coordinator.sessions_completed == 1
        
        # Verify event was published
        analytics_coordinator.event_bus.publish.assert_called()
    
    @pytest.mark.asyncio
    async def test_handle_intelligence_insight_event(self, analytics_coordinator):
        """Test handling of intelligence insight events."""
        # Mock executive engine
        mock_executive = MagicMock()
        mock_executive.generate_executive_summary = AsyncMock(return_value=MagicMock(
            summary_id="test_summary"
        ))
        analytics_coordinator.executive_engine = mock_executive
        
        # Create mock event
        event = Event(
            id="test_event",
            type=EventType.INTELLIGENCE_INSIGHT_CREATED,
            priority=EventPriority.HIGH,
            timestamp=datetime.now(timezone.utc),
            source_system="test",
            data={
                "competitor_id": "comp_001",
                "competitor_name": "Test Competitor",
                "activity_type": "product_launch",
                "activity_data": {"product": "New AI Tool"},
                "confidence_score": 0.9
            },
            correlation_id="test_correlation"
        )
        
        # Handle the event
        result = await analytics_coordinator.handle(event)
        
        # Verify handling
        assert result == True
        assert analytics_coordinator.analytics_triggered == 1
        
        # High confidence insight should trigger executive summary
        mock_executive.generate_executive_summary.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_competitor_activity_event(self, analytics_coordinator):
        """Test handling of competitor activity events."""
        # Mock landscape mapper
        mock_landscape = MagicMock()
        analytics_coordinator.landscape_mapper = mock_landscape
        
        # Create mock event with significant activity
        event = Event(
            id="test_event",
            type=EventType.COMPETITOR_ACTIVITY_DETECTED,
            priority=EventPriority.MEDIUM,
            timestamp=datetime.now(timezone.utc),
            source_system="test",
            data={
                "competitor_id": "comp_001",
                "activity_type": "major_acquisition",
                "significance_score": 0.8
            }
        )
        
        # Handle the event
        result = await analytics_coordinator.handle(event)
        
        # Verify handling
        assert result == True
        assert analytics_coordinator.analytics_triggered == 1
    
    @pytest.mark.asyncio
    async def test_handle_prediction_event(self, analytics_coordinator):
        """Test handling of prediction events."""
        # Mock market share analytics
        mock_market = MagicMock()
        analytics_coordinator.market_share_analytics = mock_market
        
        # Create mock prediction event
        event = Event(
            id="test_event",
            type=EventType.PREDICTION_GENERATED,
            priority=EventPriority.MEDIUM,
            timestamp=datetime.now(timezone.utc),
            source_system="test",
            data={
                "prediction_type": "market_share",
                "predicted_values": {"6_month": 0.35},
                "confidence_score": 0.85
            }
        )
        
        # Handle the event
        result = await analytics_coordinator.handle(event)
        
        # Verify handling
        assert result == True
        assert analytics_coordinator.analytics_triggered == 1
    
    @pytest.mark.asyncio
    async def test_session_management(self, analytics_coordinator):
        """Test analytics session management."""
        # Create test session
        session = AnalyticsSession(
            session_id="test_session",
            correlation_id="test_corr",
            started_at=datetime.now(),
            components_active={"executive_analytics", "landscape_mapping"}
        )
        
        analytics_coordinator.active_sessions["test_session"] = session
        
        # Test session completion check
        assert not analytics_coordinator._is_session_complete(session)
        
        # Mark components as completed
        session.executive_summary_completed = True
        session.landscape_analysis_completed = True
        
        assert analytics_coordinator._is_session_complete(session)
        
        # Test session cleanup
        await analytics_coordinator._cleanup_session("test_session")
        assert "test_session" not in analytics_coordinator.active_sessions
    
    @pytest.mark.asyncio
    async def test_analytics_status_monitoring(self, analytics_coordinator):
        """Test analytics status and monitoring."""
        # Mock components
        analytics_coordinator.executive_engine = MagicMock()
        analytics_coordinator.executive_engine.get_performance_metrics.return_value = {
            "summaries_generated": 5,
            "average_generation_time": 3.2
        }
        
        analytics_coordinator.landscape_mapper = MagicMock()
        analytics_coordinator.landscape_mapper.get_performance_metrics.return_value = {
            "analyses_generated": 3,
            "gaps_identified": 12
        }
        
        analytics_coordinator.market_share_analytics = MagicMock()
        analytics_coordinator.market_share_analytics.get_performance_metrics.return_value = {
            "forecasts_generated": 8,
            "average_model_accuracy": 0.82
        }
        
        # Set some test metrics
        analytics_coordinator.sessions_completed = 2
        analytics_coordinator.analytics_triggered = 15
        analytics_coordinator.error_count = 1
        
        status = await analytics_coordinator.get_analytics_status()
        
        # Verify status structure
        assert "coordinator_status" in status
        assert "active_sessions" in status
        assert "components_status" in status
        assert "performance_metrics" in status
        assert "executive_analytics_metrics" in status
        assert "landscape_mapping_metrics" in status
        assert "market_share_analytics_metrics" in status
        
        # Verify performance metrics
        perf_metrics = status["performance_metrics"]
        assert perf_metrics["sessions_completed"] == 2
        assert perf_metrics["analytics_triggered"] == 15
        assert perf_metrics["error_count"] == 1
        assert perf_metrics["error_rate"] == 1/15
        
        # Verify component status
        comp_status = status["components_status"]
        assert comp_status["executive_analytics"] == True
        assert comp_status["landscape_mapping"] == True
        assert comp_status["market_share_analytics"] == True
    
    @pytest.mark.asyncio
    async def test_error_handling_in_event_processing(self, analytics_coordinator):
        """Test error handling during event processing."""
        # Mock executive engine to raise exception
        mock_executive = MagicMock()
        mock_executive.generate_executive_summary = AsyncMock(side_effect=Exception("Test error"))
        analytics_coordinator.executive_engine = mock_executive
        
        # Create test event
        event = Event(
            id="test_event",
            type=EventType.INTELLIGENCE_INSIGHT_CREATED,
            priority=EventPriority.HIGH,
            timestamp=datetime.now(timezone.utc),
            source_system="test",
            data={
                "competitor_id": "comp_001",
                "confidence_score": 0.95
            }
        )
        
        # Handle event - should not raise exception
        result = await analytics_coordinator.handle(event)
        
        # Should return False on error and increment error count
        assert result == False
        assert analytics_coordinator.error_count == 1
    
    @pytest.mark.asyncio
    async def test_configuration_disabled_components(self, mock_event_bus):
        """Test coordinator with disabled components."""
        # Create config with some components disabled
        disabled_config = AnalyticsConfiguration(
            executive_analytics_enabled=True,
            landscape_mapping_enabled=False,  # Disabled
            market_share_analytics_enabled=False  # Disabled
        )
        
        coordinator = AnalyticsCoordinator(
            config=disabled_config,
            event_bus=mock_event_bus
        )
        
        # Mock only executive engine
        with patch('src.analytics.analytics_coordinator.ExecutiveAnalyticsEngine') as mock_exec:
            await coordinator.start()
            
            # Verify only executive engine was initialized
            assert coordinator.executive_engine is not None
            assert coordinator.landscape_mapper is None
            assert coordinator.market_share_analytics is None
            
            mock_exec.assert_called_once()
    
    def test_analytics_session_creation(self):
        """Test analytics session data structure."""
        session = AnalyticsSession(
            session_id="test_session",
            correlation_id="test_corr",
            started_at=datetime.now(),
            components_active={"executive_analytics"}
        )
        
        # Verify default values
        assert session.executive_summary_completed == False
        assert session.landscape_analysis_completed == False
        assert session.market_share_analysis_completed == False
        assert session.final_results is None
    
    def test_analytics_configuration_defaults(self):
        """Test analytics configuration default values."""
        config = AnalyticsConfiguration()
        
        assert config.executive_analytics_enabled == True
        assert config.landscape_mapping_enabled == True
        assert config.market_share_analytics_enabled == True
        assert config.default_stakeholder == StakeholderType.CEO
        assert config.claude_model == "claude-3-5-sonnet-20241022"
        assert config.min_data_points == 12
        assert config.forecast_confidence == 0.95
    
    def test_average_session_time_update(self, analytics_coordinator):
        """Test average session time calculation."""
        # Initial state
        assert analytics_coordinator.average_session_time == 0.0
        
        # Update with first session time
        analytics_coordinator._update_average_session_time(5.0)
        assert analytics_coordinator.average_session_time == 5.0
        
        # Update with second session time (should use exponential moving average)
        analytics_coordinator._update_average_session_time(3.0)
        expected = 0.1 * 3.0 + 0.9 * 5.0  # alpha=0.1
        assert abs(analytics_coordinator.average_session_time - expected) < 0.01
    
    @pytest.mark.asyncio 
    async def test_partial_component_execution(
        self, analytics_coordinator, sample_intelligence_data
    ):
        """Test analytics execution with only some components available."""
        # Mock only executive engine (others are None)
        mock_executive = MagicMock()
        mock_executive.generate_executive_summary = AsyncMock(return_value=MagicMock(
            summary_id="test_summary"
        ))
        analytics_coordinator.executive_engine = mock_executive
        analytics_coordinator.landscape_mapper = None
        analytics_coordinator.market_share_analytics = None
        
        # Generate analytics with partial components
        results = await analytics_coordinator.generate_comprehensive_analytics(
            intelligence_data=sample_intelligence_data,
            stakeholder_type=StakeholderType.CTO
        )
        
        # Verify partial execution
        assert "executive_summary" in results
        assert "landscape_analysis" in results
        assert "market_share_analysis" in results
        
        # Only executive summary should have data
        assert results["executive_summary"] is not None
        assert results["landscape_analysis"] is None
        assert results["market_share_analysis"] is None
        
        # Verify session performance reflects partial execution
        session_perf = results["session_performance"]
        assert session_perf["components_successful"] == 1
        assert session_perf["components_failed"] == 0  # None components aren't considered failed