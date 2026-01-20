"""
Test Cross-Track Coordination via Event Bridge

Comprehensive tests to validate the coordination between CRM Integration,
Advanced Analytics, and Real-Time Dashboard tracks through the Event Bridge.

Author: Claude
Date: January 2026
"""

import asyncio
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

# Import core event system
from competitive_intelligence_engine.src.core.event_bus import EventBus, EventType, EventPriority

# Import Event Bridge components
from competitive_intelligence_engine.src.integration.event_bridge import (
    EventBridge,
    CrossTrackEvent,
    IntegrationEventType,
    IntegrationMetrics
)

# Import track components
from competitive_intelligence_engine.src.analytics.executive_analytics_engine import ExecutiveSummary, StakeholderType
from competitive_intelligence_engine.src.crm.crm_coordinator import CRMCoordinator, IntelligenceAction, IntelligenceActionType
from competitive_intelligence_engine.src.crm.base_crm_connector import CRMPlatform
from competitive_intelligence_engine.src.dashboard.real_time.websocket_manager import WebSocketManager, WebSocketEvent, MessageType


@pytest.fixture
async def event_bus():
    """Create event bus for testing."""
    bus = EventBus()
    await bus.start()
    yield bus
    await bus.stop()


@pytest.fixture
async def mock_crm_coordinator():
    """Create mock CRM coordinator."""
    coordinator = AsyncMock(spec=CRMCoordinator)
    coordinator._queue_intelligence_action = AsyncMock()
    return coordinator


@pytest.fixture
async def mock_websocket_manager():
    """Create mock WebSocket manager."""
    manager = AsyncMock(spec=WebSocketManager)
    manager.broadcast_event = AsyncMock()
    return manager


@pytest.fixture
async def event_bridge(event_bus, mock_crm_coordinator, mock_websocket_manager):
    """Create Event Bridge with all dependencies."""
    bridge = EventBridge(
        event_bus=event_bus,
        crm_coordinator=mock_crm_coordinator,
        websocket_manager=mock_websocket_manager,
        enable_event_replay=True,
        max_event_history=1000
    )
    await bridge.start()
    yield bridge
    await bridge.stop()


class TestEventBridgeInitialization:
    """Test Event Bridge initialization and configuration."""

    async def test_event_bridge_initialization(self, event_bus):
        """Test basic Event Bridge initialization."""
        bridge = EventBridge(event_bus=event_bus)

        assert bridge.event_bus == event_bus
        assert bridge.enable_event_replay is True
        assert bridge.max_event_history == 10000
        assert len(bridge.cross_track_events) == 0
        assert isinstance(bridge.metrics, IntegrationMetrics)

    async def test_event_bridge_startup(self, event_bridge):
        """Test Event Bridge startup process."""
        assert event_bridge.is_running is True
        assert event_bridge.event_bus is not None
        assert event_bridge.crm_coordinator is not None
        assert event_bridge.websocket_manager is not None


class TestExecutiveSummaryCoordination:
    """Test coordination of executive summary events across tracks."""

    async def test_executive_summary_to_dashboard_coordination(self, event_bridge):
        """Test executive summary creates dashboard update event."""
        # Create executive summary event
        summary_data = {
            "summary_id": "exec_001",
            "stakeholder_type": StakeholderType.BOARD.value,
            "threat_level": "high",
            "opportunity_count": 5,
            "action_count": 3,
            "business_impact": {
                "quantitative_analysis": {
                    "roi_analyses": [
                        {"opportunity": "market_expansion", "projected_roi": 0.25}
                    ]
                }
            }
        }

        # Create and process event
        event = MagicMock()
        event.type = EventType.EXECUTIVE_SUMMARY_CREATED
        event.data = summary_data
        event.correlation_id = "test_correlation_001"

        # Handle the event
        result = await event_bridge.handle(event)

        assert result is True
        assert event_bridge.metrics.events_processed == 1
        assert len(event_bridge.cross_track_events) == 2  # Dashboard + CRM events

        # Allow time for cross-track processing
        await asyncio.sleep(0.2)

        # Verify dashboard WebSocket call
        event_bridge.websocket_manager.broadcast_event.assert_called()
        call_args = event_bridge.websocket_manager.broadcast_event.call_args_list

        dashboard_calls = [call for call in call_args if call[1].get('topic') in ['executive_summary']]
        assert len(dashboard_calls) > 0

    async def test_executive_summary_to_crm_coordination(self, event_bridge):
        """Test executive summary triggers CRM actions."""
        # Create executive summary event
        summary_data = {
            "summary_id": "exec_002",
            "stakeholder_type": StakeholderType.EXECUTIVES.value,
            "business_impact": {
                "quantitative_analysis": {
                    "roi_analyses": [
                        {"opportunity": "competitive_defense", "projected_roi": 0.15}
                    ]
                }
            }
        }

        event = MagicMock()
        event.type = EventType.EXECUTIVE_SUMMARY_CREATED
        event.data = summary_data
        event.correlation_id = "test_correlation_002"

        # Handle the event
        await event_bridge.handle(event)

        # Allow time for cross-track processing
        await asyncio.sleep(0.2)

        # Verify CRM action queuing
        event_bridge.crm_coordinator._queue_intelligence_action.assert_called()

        # Check that actions were created with proper platform enum
        call_args = event_bridge.crm_coordinator._queue_intelligence_action.call_args_list
        assert len(call_args) > 0

        # Verify action contains proper CRM platform reference
        action = call_args[0][0][0] if call_args else None
        if action:
            assert action.target_platform == CRMPlatform.GOHIGHLEVEL.value


class TestStrategicPatternCoordination:
    """Test coordination of strategic pattern events."""

    async def test_critical_strategic_pattern_coordination(self, event_bridge):
        """Test critical strategic pattern triggers immediate dashboard alerts."""
        pattern_data = {
            "pattern_id": "pattern_critical_001",
            "pattern_type": "market_disruption",
            "urgency_level": "critical",
            "confidence_score": 0.95,
            "business_implications": [
                "Immediate competitive threat",
                "Market share risk"
            ],
            "recommended_response": "Defensive positioning required"
        }

        event = MagicMock()
        event.type = EventType.STRATEGIC_PATTERN_IDENTIFIED
        event.data = pattern_data
        event.correlation_id = "pattern_critical_001"

        # Handle the event
        result = await event_bridge.handle(event)

        assert result is True

        # Allow time for cross-track processing
        await asyncio.sleep(0.2)

        # Verify high-priority dashboard update
        event_bridge.websocket_manager.broadcast_event.assert_called()

        # Verify CRM strategic pattern alert
        event_bridge.crm_coordinator._queue_intelligence_action.assert_called()

        # Check that dashboard events have critical priority
        call_args = event_bridge.websocket_manager.broadcast_event.call_args_list
        critical_calls = [
            call for call in call_args
            if call[0][0].priority == "high"  # EventPriority.CRITICAL maps to "high" in WebSocket
        ]
        assert len(critical_calls) > 0


class TestMLPredictionCoordination:
    """Test coordination of ML prediction events."""

    async def test_ml_prediction_to_dashboard(self, event_bridge):
        """Test ML predictions are sent to dashboard."""
        prediction_data = {
            "prediction_type": "competitor_behavior",
            "confidence_score": 0.87,
            "model_name": "CompetitorLSTM",
            "predictions": [
                {
                    "competitor_id": "comp_001",
                    "predicted_action": "price_adjustment",
                    "confidence": 0.87,
                    "timeframe": "7_days"
                }
            ]
        }

        event = MagicMock()
        event.type = EventType.DEEP_LEARNING_PREDICTION
        event.data = prediction_data
        event.correlation_id = "ml_prediction_001"

        # Handle the event
        result = await event_bridge.handle(event)

        assert result is True

        # Allow time for cross-track processing
        await asyncio.sleep(0.2)

        # Verify dashboard update for ML prediction
        event_bridge.websocket_manager.broadcast_event.assert_called()

        # Verify correct topic routing
        call_args = event_bridge.websocket_manager.broadcast_event.call_args_list
        ml_calls = [call for call in call_args if call[1].get('topic') == 'analytics_updates']
        assert len(ml_calls) > 0


class TestCRMDataCoordination:
    """Test coordination of CRM data events."""

    async def test_crm_contact_update_coordination(self, event_bridge):
        """Test CRM contact updates trigger dashboard notifications."""
        crm_data = {
            "object_type": "contact",
            "object_id": "contact_12345",
            "action": "updated",
            "platform": "gohighlevel"
        }

        event = MagicMock()
        event.type = EventType.CRM_CONTACT_UPDATED
        event.data = crm_data
        event.correlation_id = "crm_update_001"

        # Handle the event
        result = await event_bridge.handle(event)

        assert result is True

        # Allow time for cross-track processing
        await asyncio.sleep(0.2)

        # Verify dashboard update
        event_bridge.websocket_manager.broadcast_event.assert_called()

    async def test_crm_sync_completion_coordination(self, event_bridge):
        """Test CRM sync completion triggers dashboard status update."""
        sync_data = {
            "platform": "gohighlevel",
            "objects_processed": 150,
            "duration_seconds": 45
        }

        event = MagicMock()
        event.type = EventType.CRM_SYNC_COMPLETED
        event.data = sync_data
        event.correlation_id = "crm_sync_001"

        # Handle the event
        result = await event_bridge.handle(event)

        assert result is True

        # Allow time for cross-track processing
        await asyncio.sleep(0.2)

        # Verify dashboard sync status update
        event_bridge.websocket_manager.broadcast_event.assert_called()


class TestCrossTrackEventProcessing:
    """Test cross-track event processing and transformation."""

    async def test_event_transformation_for_dashboard(self, event_bridge):
        """Test event data transformation for dashboard consumption."""
        cross_track_event = CrossTrackEvent(
            event_id="test_event_001",
            integration_event_type=IntegrationEventType.ANALYTICS_TO_DASHBOARD,
            source_track="analytics",
            target_tracks=["dashboard"],
            original_event_type="executive_summary_created",
            event_data={
                "summary_id": "exec_001",
                "stakeholder_type": "executives",
                "dashboard_update_type": "executive_summary",
                "priority": "high"
            },
            correlation_id="test_001"
        )

        # Transform for dashboard
        transformed = event_bridge._transform_for_dashboard(cross_track_event)

        assert transformed["event_id"] == "test_event_001"
        assert transformed["source_track"] == "analytics"
        assert transformed["original_event_type"] == "executive_summary_created"
        assert transformed["correlation_id"] == "test_001"
        assert "analytics_data" in transformed
        assert transformed["visualization_type"] == "executive_summary"
        assert transformed["priority"] == "high"

    async def test_event_transformation_for_crm(self, event_bridge):
        """Test event data transformation for CRM actions."""
        cross_track_event = CrossTrackEvent(
            event_id="test_event_002",
            integration_event_type=IntegrationEventType.INTELLIGENCE_TO_CRM,
            source_track="analytics",
            target_tracks=["crm"],
            original_event_type="executive_summary_created",
            event_data={
                "crm_action_type": "executive_intelligence_update",
                "stakeholder_type": "board",
                "target_platform": CRMPlatform.GOHIGHLEVEL.value
            },
            correlation_id="test_002"
        )

        # Transform for CRM
        actions = event_bridge._transform_for_crm(cross_track_event)

        assert len(actions) == 1
        action = actions[0]
        assert isinstance(action, IntelligenceAction)
        assert action.action_type == IntelligenceActionType.ADD_COMPETITIVE_NOTE
        assert action.target_platform == CRMPlatform.GOHIGHLEVEL.value
        assert action.target_object_type == "contact"
        assert action.intelligence_correlation_id == "test_002"


class TestEventReplay:
    """Test event replay functionality."""

    async def test_event_replay_within_timeframe(self, event_bridge):
        """Test replaying events within specified timeframe."""
        # Create some historical events
        base_time = datetime.now(timezone.utc) - timedelta(hours=1)

        for i in range(3):
            historical_event = CrossTrackEvent(
                event_id=f"historical_{i}",
                integration_event_type=IntegrationEventType.ANALYTICS_TO_DASHBOARD,
                source_track="analytics",
                target_tracks=["dashboard"],
                original_event_type="test_event",
                event_data={"test": f"data_{i}"},
                created_at=base_time + timedelta(minutes=i*10)
            )
            event_bridge.event_history.append(historical_event)

        # Replay events from 30 minutes ago
        from_time = base_time + timedelta(minutes=15)
        to_time = datetime.now(timezone.utc)

        replayed_count = await event_bridge.replay_events(from_time, to_time)

        assert replayed_count == 2  # Should replay last 2 events
        assert len(event_bridge.cross_track_events) >= 2

    async def test_event_replay_filtered_by_type(self, event_bridge):
        """Test replaying events filtered by event type."""
        # Create historical events of different types
        base_time = datetime.now(timezone.utc) - timedelta(hours=1)

        analytics_event = CrossTrackEvent(
            event_id="analytics_event",
            integration_event_type=IntegrationEventType.ANALYTICS_TO_DASHBOARD,
            source_track="analytics",
            target_tracks=["dashboard"],
            original_event_type="test_analytics",
            event_data={"test": "analytics"},
            created_at=base_time
        )

        crm_event = CrossTrackEvent(
            event_id="crm_event",
            integration_event_type=IntegrationEventType.CRM_TO_DASHBOARD,
            source_track="crm",
            target_tracks=["dashboard"],
            original_event_type="test_crm",
            event_data={"test": "crm"},
            created_at=base_time
        )

        event_bridge.event_history.extend([analytics_event, crm_event])

        # Replay only analytics events
        replayed_count = await event_bridge.replay_events(
            base_time - timedelta(minutes=5),
            datetime.now(timezone.utc),
            event_types=[IntegrationEventType.ANALYTICS_TO_DASHBOARD]
        )

        assert replayed_count == 1


class TestIntegrationMetrics:
    """Test integration performance metrics."""

    async def test_metrics_collection(self, event_bridge):
        """Test that metrics are properly collected during event processing."""
        initial_metrics = event_bridge.metrics

        # Create and process an event
        event = MagicMock()
        event.type = EventType.EXECUTIVE_SUMMARY_CREATED
        event.data = {
            "summary_id": "metrics_test_001",
            "stakeholder_type": StakeholderType.BOARD.value
        }
        event.correlation_id = "metrics_test"

        await event_bridge.handle(event)

        # Allow processing
        await asyncio.sleep(0.2)

        # Verify metrics were updated
        assert event_bridge.metrics.events_processed > initial_metrics.events_processed
        assert event_bridge.metrics.cross_track_events > initial_metrics.cross_track_events
        assert event_bridge.metrics.successful_transformations >= initial_metrics.successful_transformations

    async def test_integration_status_report(self, event_bridge):
        """Test integration status reporting."""
        status = event_bridge.get_integration_status()

        assert status["is_running"] is True
        assert status["components_connected"]["event_bus"] is True
        assert status["components_connected"]["crm_coordinator"] is True
        assert status["components_connected"]["websocket_manager"] is True

        metrics = status["metrics"]
        assert "events_processed" in metrics
        assert "cross_track_events" in metrics
        assert "successful_transformations" in metrics
        assert "failed_transformations" in metrics
        assert "success_rate" in metrics
        assert "dashboard_updates_sent" in metrics
        assert "crm_actions_triggered" in metrics


class TestTopicRouting:
    """Test dashboard topic routing for different event types."""

    async def test_executive_summary_topic_routing(self, event_bridge):
        """Test executive summary events route to correct topic."""
        event = CrossTrackEvent(
            event_id="topic_test_001",
            integration_event_type=IntegrationEventType.ANALYTICS_TO_DASHBOARD,
            source_track="analytics",
            target_tracks=["dashboard"],
            original_event_type="executive_summary_created",
            event_data={}
        )

        topic = event_bridge._get_dashboard_topic(event)
        assert topic == "executive_summary"

    async def test_strategic_pattern_topic_routing(self, event_bridge):
        """Test strategic pattern events route to correct topic."""
        event = CrossTrackEvent(
            event_id="topic_test_002",
            integration_event_type=IntegrationEventType.ANALYTICS_TO_DASHBOARD,
            source_track="analytics",
            target_tracks=["dashboard"],
            original_event_type="strategic_pattern_identified",
            event_data={}
        )

        topic = event_bridge._get_dashboard_topic(event)
        assert topic == "strategic_patterns"

    async def test_ml_model_update_topic_routing(self, event_bridge):
        """Test ML model update events route to correct topic."""
        event = CrossTrackEvent(
            event_id="topic_test_003",
            integration_event_type=IntegrationEventType.ML_MODEL_UPDATE,
            source_track="analytics",
            target_tracks=["dashboard"],
            original_event_type="deep_learning_prediction",
            event_data={}
        )

        topic = event_bridge._get_dashboard_topic(event)
        assert topic == "analytics_updates"


@pytest.mark.integration
class TestEndToEndCoordination:
    """End-to-end tests for complete cross-track coordination."""

    async def test_complete_intelligence_workflow(self, event_bridge):
        """Test complete intelligence workflow across all tracks."""
        # Simulate executive summary creation
        summary_event = MagicMock()
        summary_event.type = EventType.EXECUTIVE_SUMMARY_CREATED
        summary_event.data = {
            "summary_id": "workflow_001",
            "stakeholder_type": StakeholderType.BOARD.value,
            "threat_level": "critical",
            "opportunity_count": 8,
            "action_count": 5,
            "business_impact": {
                "quantitative_analysis": {
                    "roi_analyses": [
                        {"opportunity": "market_expansion", "projected_roi": 0.35},
                        {"opportunity": "competitive_defense", "projected_roi": 0.22}
                    ]
                }
            }
        }
        summary_event.correlation_id = "workflow_001"

        # Process executive summary
        await event_bridge.handle(summary_event)

        # Simulate strategic pattern identification
        pattern_event = MagicMock()
        pattern_event.type = EventType.STRATEGIC_PATTERN_IDENTIFIED
        pattern_event.data = {
            "pattern_id": "pattern_workflow_001",
            "pattern_type": "competitive_threat",
            "urgency_level": "high",
            "confidence_score": 0.92,
            "business_implications": [
                "Revenue impact risk",
                "Customer retention threat"
            ],
            "recommended_response": "Immediate competitive response required"
        }
        pattern_event.correlation_id = "workflow_001"

        # Process strategic pattern
        await event_bridge.handle(pattern_event)

        # Simulate ML prediction
        prediction_event = MagicMock()
        prediction_event.type = EventType.DEEP_LEARNING_PREDICTION
        prediction_event.data = {
            "prediction_type": "competitor_behavior",
            "confidence_score": 0.89,
            "model_name": "CompetitorTransformer",
            "predictions": [
                {
                    "competitor_id": "comp_workflow_001",
                    "predicted_action": "aggressive_pricing",
                    "confidence": 0.89,
                    "timeframe": "14_days"
                }
            ]
        }
        prediction_event.correlation_id = "workflow_001"

        # Process ML prediction
        await event_bridge.handle(prediction_event)

        # Allow all cross-track processing to complete
        await asyncio.sleep(0.5)

        # Verify comprehensive coordination
        assert event_bridge.metrics.events_processed == 3
        assert event_bridge.metrics.cross_track_events >= 4  # Multiple events generated

        # Verify dashboard updates
        dashboard_calls = event_bridge.websocket_manager.broadcast_event.call_args_list
        assert len(dashboard_calls) >= 3  # At least one per original event

        # Verify CRM actions
        crm_calls = event_bridge.crm_coordinator._queue_intelligence_action.call_args_list
        assert len(crm_calls) >= 2  # Executive summary + strategic pattern

        # Verify event history
        assert len(event_bridge.event_history) >= 4

        # Verify correlation tracking
        correlated_events = [
            event for event in event_bridge.event_history
            if event.correlation_id == "workflow_001"
        ]
        assert len(correlated_events) >= 4


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])