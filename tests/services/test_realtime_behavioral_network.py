#!/usr/bin/env python3
"""
Tests for Real-time Behavioral Network - Including 5 TODO methods implementation
=============================================================================

Comprehensive test suite covering:
- All 5 TODO methods: _send_immediate_alert, _notify_agent, _set_priority_flag,
  _send_automated_response, _deliver_personalized_content
- Real-time behavioral signal processing
- Multi-channel notification systems
- Cache and internal helper integration

Target Coverage: 85%+ on realtime_behavioral_network.py
"""

import pytest
import pytest_asyncio
import asyncio
import time
import queue
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from ghl_real_estate_ai.services.realtime_behavioral_network import (
    RealTimeBehavioralNetwork,
    RealTimeTrigger,
    TriggerType,
    BehavioralSignal,
    BehavioralSignalType,
    BehavioralPattern,
    BehavioralInsight,
    BehavioralAnalysisAgentType,
    SignalDetectorAgent,
    PatternRecognizerAgent,
    IntentPredictorAgent
)

# Test fixtures and data
@pytest.fixture
def sample_trigger():
    """Sample real-time trigger for testing."""
    return RealTimeTrigger(
        trigger_id="trigger_123",
        lead_id="lead_456",
        trigger_type=TriggerType.IMMEDIATE_ALERT,
        trigger_condition="high_intent_property_view",
        action_payload={
            "property_id": "prop_789",
            "behavioral_score": 85,
            "lead_name": "John Smith",
            "context": "Viewed premium listing for 15+ minutes",
            "urgency": "high",
            "confidence": 0.9,
            "recommendations": ["call_immediately", "send_property_info", "schedule_showing"]
        },
        priority=4,
        expiration_time=datetime.now() + timedelta(hours=1)
    )

@pytest.fixture
def sample_behavioral_signal():
    """Sample behavioral signal for testing."""
    return BehavioralSignal(
        signal_id="signal_123",
        lead_id="lead_456",
        signal_type=BehavioralSignalType.PROPERTY_VIEW,
        timestamp=datetime.now(),
        page_url="https://example.com/property/123",
        property_id="prop_123",
        session_id="session_789",
        device_type="desktop",
        interaction_value=8.5,
        context_data={
            "time_spent_seconds": 300,
            "scroll_depth": 0.8,
            "clicked_elements": ["gallery", "details", "contact"]
        }
    )

@pytest_asyncio.fixture
async def behavioral_network():
    """Create behavioral network with mocked internal services."""
    network = RealTimeBehavioralNetwork()

    # Mock the cache service (used by _get_lead_details, _store_alert_audit, etc.)
    network.cache = AsyncMock()
    network.cache.get = AsyncMock(return_value=None)  # Cache miss by default
    network.cache.set = AsyncMock(return_value=True)

    # Mock sendgrid_client (used by _send_email_alert)
    network.sendgrid_client = AsyncMock()
    mock_email_result = MagicMock()
    mock_email_result.message_id = "msg_12345"
    network.sendgrid_client.send_email = AsyncMock(return_value=mock_email_result)

    # Mock twilio_client (used by _send_sms_alert)
    network.twilio_client = AsyncMock()
    mock_sms_result = MagicMock()
    mock_sms_result.sid = "sms_12345"
    network.twilio_client.send_sms = AsyncMock(return_value=mock_sms_result)

    return network


class TestSendImmediateAlert:
    """Test _send_immediate_alert TODO method implementation."""

    @pytest.mark.asyncio
    async def test_send_immediate_alert_success(self, behavioral_network, sample_trigger):
        """Test successful immediate alert sending."""
        # Mock _get_lead_details to return lead data
        behavioral_network._get_lead_details = AsyncMock(return_value={
            "name": "John Smith",
            "email": "john@example.com",
            "phone": "+1234567890"
        })

        # Mock internal alert methods
        behavioral_network._send_email_alert = AsyncMock(return_value={'success': True, 'message_id': 'email_123'})
        behavioral_network._send_slack_alert = AsyncMock(return_value={'success': True, 'message_id': 'slack_123'})
        behavioral_network._send_dashboard_notification = AsyncMock(return_value={'success': True, 'notification_id': 'dash_123'})
        behavioral_network._store_alert_audit = AsyncMock()

        # Execute method
        await behavioral_network._send_immediate_alert(sample_trigger)

        # Verify lead details were fetched
        behavioral_network._get_lead_details.assert_called_once_with("lead_456")

        # Verify email alert was sent (priority >= 4)
        behavioral_network._send_email_alert.assert_called_once()

        # Verify slack alert was sent (all priorities)
        behavioral_network._send_slack_alert.assert_called_once()

        # Verify dashboard notification was sent
        behavioral_network._send_dashboard_notification.assert_called_once()

        # Verify audit was stored
        behavioral_network._store_alert_audit.assert_called_once()

        # Verify trigger execution result
        assert sample_trigger.execution_result is not None
        assert sample_trigger.execution_result['success'] is True

    @pytest.mark.asyncio
    async def test_send_immediate_alert_no_lead_data(self, behavioral_network, sample_trigger):
        """Test alert handling when lead data is not in cache (fallback used)."""
        # _get_lead_details returns None -> service uses fallback data
        behavioral_network._get_lead_details = AsyncMock(return_value=None)
        behavioral_network._send_email_alert = AsyncMock(return_value={'success': True})
        behavioral_network._send_slack_alert = AsyncMock(return_value={'success': True})
        behavioral_network._send_dashboard_notification = AsyncMock(return_value={'success': True})
        behavioral_network._store_alert_audit = AsyncMock()

        # Should not crash, should use fallback data
        await behavioral_network._send_immediate_alert(sample_trigger)

        # Should still proceed with fallback lead data
        assert sample_trigger.execution_result is not None

    @pytest.mark.asyncio
    async def test_send_immediate_alert_high_priority(self, behavioral_network, sample_trigger):
        """Test multi-channel alert sending for high priority."""
        sample_trigger.priority = 5  # Critical priority

        behavioral_network._get_lead_details = AsyncMock(return_value={
            "name": "John Smith",
            "email": "john@example.com",
            "phone": "+1234567890"
        })
        behavioral_network._send_email_alert = AsyncMock(return_value={'success': True})
        behavioral_network._send_sms_alert = AsyncMock(return_value={'success': True})
        behavioral_network._send_slack_alert = AsyncMock(return_value={'success': True})
        behavioral_network._send_dashboard_notification = AsyncMock(return_value={'success': True})
        behavioral_network._store_alert_audit = AsyncMock()

        await behavioral_network._send_immediate_alert(sample_trigger)

        # Priority 5 should trigger email (>=4) AND SMS (>=5 with phone)
        behavioral_network._send_email_alert.assert_called_once()
        behavioral_network._send_sms_alert.assert_called_once()

        assert sample_trigger.execution_result['success'] is True


class TestNotifyAgent:
    """Test _notify_agent TODO method implementation."""

    @pytest.mark.asyncio
    async def test_notify_agent_assigned_agent(self, behavioral_network, sample_trigger):
        """Test notifying assigned agent."""
        behavioral_network._get_lead_details = AsyncMock(return_value={
            "name": "John Smith",
            "email": "john@example.com",
            "phone": "+1234567890"
        })
        behavioral_network._get_agent_assignment = AsyncMock(return_value={
            "agent_id": "agent_123",
            "agent_info": {
                "name": "Sarah Wilson",
                "email": "sarah@realestate.com",
                "phone": "+1987654321"
            },
            "workload_info": {
                "current_leads": 15,
                "priority_leads": 3,
                "availability_score": 0.8
            }
        })
        behavioral_network._send_agent_dashboard_notification = AsyncMock(return_value={'success': True})
        behavioral_network._send_agent_email_notification = AsyncMock(return_value={'success': True})
        behavioral_network._update_agent_workload = AsyncMock()
        behavioral_network._store_notification_audit = AsyncMock()
        behavioral_network._schedule_agent_followup_reminder = AsyncMock()

        await behavioral_network._notify_agent(sample_trigger)

        # Verify agent assignment was queried
        behavioral_network._get_agent_assignment.assert_called_once_with("lead_456", 4)

        # Verify dashboard notification was sent (always sent)
        behavioral_network._send_agent_dashboard_notification.assert_called_once()

        # Verify email notification was sent (priority >= 4)
        behavioral_network._send_agent_email_notification.assert_called_once()

        # Verify trigger result
        assert sample_trigger.execution_result is not None
        assert sample_trigger.execution_result['success'] is True
        assert sample_trigger.execution_result['agent_id'] == 'agent_123'

    @pytest.mark.asyncio
    async def test_notify_agent_no_available_agent(self, behavioral_network, sample_trigger):
        """Test behavior when no agents are available."""
        behavioral_network._get_lead_details = AsyncMock(return_value={
            "name": "John Smith",
            "email": "john@example.com"
        })
        behavioral_network._get_agent_assignment = AsyncMock(return_value=None)

        result = await behavioral_network._notify_agent(sample_trigger)

        # Should return failure when no agent available
        assert result is not None
        assert result['success'] is False
        assert result['reason'] == 'no_agent_available'

    @pytest.mark.asyncio
    async def test_notify_agent_multi_channel_notification(self, behavioral_network, sample_trigger):
        """Test multi-channel agent notification for critical priority."""
        sample_trigger.priority = 5
        sample_trigger.action_payload['urgency'] = 'critical'

        behavioral_network._get_lead_details = AsyncMock(return_value={
            "name": "John Smith",
            "email": "john@example.com",
            "phone": "+1234567890"
        })
        behavioral_network._get_agent_assignment = AsyncMock(return_value={
            "agent_id": "agent_123",
            "agent_info": {
                "name": "Sarah Wilson",
                "email": "sarah@realestate.com",
                "phone": "+1987654321"
            },
            "workload_info": {}
        })
        behavioral_network._send_agent_dashboard_notification = AsyncMock(return_value={'success': True})
        behavioral_network._send_agent_email_notification = AsyncMock(return_value={'success': True})
        behavioral_network._send_agent_push_notification = AsyncMock(return_value={'success': True})
        behavioral_network._send_agent_sms_notification = AsyncMock(return_value={'success': True})
        behavioral_network._update_agent_workload = AsyncMock()
        behavioral_network._store_notification_audit = AsyncMock()
        behavioral_network._schedule_agent_followup_reminder = AsyncMock()

        await behavioral_network._notify_agent(sample_trigger)

        # Priority 5 + critical urgency should trigger all channels
        behavioral_network._send_agent_dashboard_notification.assert_called_once()
        behavioral_network._send_agent_email_notification.assert_called_once()
        behavioral_network._send_agent_push_notification.assert_called_once()
        behavioral_network._send_agent_sms_notification.assert_called_once()


class TestSetPriorityFlag:
    """Test _set_priority_flag TODO method implementation."""

    @pytest.mark.asyncio
    async def test_set_priority_flag_success(self, behavioral_network, sample_trigger):
        """Test successful priority flag setting."""
        # Mock all internal priority flag methods
        behavioral_network._set_ghl_priority_flag = AsyncMock(return_value={'success': True})
        behavioral_network._set_internal_priority_flag = AsyncMock(return_value={'success': True})
        behavioral_network._cache_priority_status = AsyncMock(return_value={'success': True})
        behavioral_network._update_lead_priority_scoring = AsyncMock(return_value={'success': True})
        behavioral_network._trigger_priority_workflow = AsyncMock(return_value={'success': True})
        behavioral_network._schedule_priority_flag_review = AsyncMock(return_value={'success': True})
        behavioral_network._store_priority_flag_audit = AsyncMock()
        behavioral_network._send_priority_flag_notifications = AsyncMock()

        result = await behavioral_network._set_priority_flag(sample_trigger)

        # Verify priority flag was set in multiple systems
        behavioral_network._set_ghl_priority_flag.assert_called_once()
        behavioral_network._set_internal_priority_flag.assert_called_once()
        behavioral_network._cache_priority_status.assert_called_once()
        behavioral_network._update_lead_priority_scoring.assert_called_once()
        behavioral_network._trigger_priority_workflow.assert_called_once()
        behavioral_network._schedule_priority_flag_review.assert_called_once()

        # Verify result
        assert result['success'] is True
        assert result['successful_operations'] == 6

    @pytest.mark.asyncio
    async def test_priority_escalation_partial_failure(self, behavioral_network, sample_trigger):
        """Test that priority flag setting handles partial failures."""
        sample_trigger.priority = 5
        sample_trigger.action_payload["urgency"] = "critical"

        # Some succeed, some fail
        behavioral_network._set_ghl_priority_flag = AsyncMock(return_value={'success': True})
        behavioral_network._set_internal_priority_flag = AsyncMock(side_effect=Exception("DB error"))
        behavioral_network._cache_priority_status = AsyncMock(return_value={'success': True})
        behavioral_network._update_lead_priority_scoring = AsyncMock(return_value={'success': True})
        behavioral_network._trigger_priority_workflow = AsyncMock(side_effect=Exception("Workflow error"))
        behavioral_network._schedule_priority_flag_review = AsyncMock(return_value={'success': True})
        behavioral_network._store_priority_flag_audit = AsyncMock()
        behavioral_network._send_priority_flag_notifications = AsyncMock()

        result = await behavioral_network._set_priority_flag(sample_trigger)

        # Success if at least one operation succeeded
        assert result['success'] is True
        assert result['successful_operations'] == 4  # 4 of 6 succeeded

    @pytest.mark.asyncio
    async def test_set_priority_flag_complete_failure(self, behavioral_network, sample_trigger):
        """Test handling when all priority flag operations fail."""
        # All operations fail with exceptions
        behavioral_network._set_ghl_priority_flag = AsyncMock(side_effect=Exception("GHL error"))
        behavioral_network._set_internal_priority_flag = AsyncMock(side_effect=Exception("DB error"))
        behavioral_network._cache_priority_status = AsyncMock(side_effect=Exception("Cache error"))
        behavioral_network._update_lead_priority_scoring = AsyncMock(side_effect=Exception("Score error"))
        behavioral_network._trigger_priority_workflow = AsyncMock(side_effect=Exception("Workflow error"))
        behavioral_network._schedule_priority_flag_review = AsyncMock(side_effect=Exception("Review error"))
        behavioral_network._store_priority_flag_audit = AsyncMock()
        behavioral_network._send_priority_flag_notifications = AsyncMock()

        result = await behavioral_network._set_priority_flag(sample_trigger)

        # Should report failure (0 successful operations)
        assert result['success'] is False
        assert result['successful_operations'] == 0


class TestSendAutomatedResponse:
    """Test _send_automated_response TODO method implementation."""

    @pytest.mark.asyncio
    async def test_send_automated_response_email(self, behavioral_network, sample_trigger):
        """Test automated email response."""
        behavioral_network._get_lead_details = AsyncMock(return_value={
            "name": "John Smith",
            "email": "john@example.com",
            "phone": "+1234567890",
            "source": "website"
        })
        behavioral_network._get_behavioral_context = AsyncMock(return_value={
            "currently_active": False,
            "session_duration": 300,
            "page_views": 5
        })
        behavioral_network._determine_response_strategy = AsyncMock(return_value={
            "channel": "email",
            "template": "behavioral_engagement",
            "personalization": {"urgency": "high"},
            "ai_enhanced": True,
            "follow_up_sequence": "standard_nurture"
        })
        behavioral_network._send_automated_email_response = AsyncMock(return_value={'success': True})
        behavioral_network._send_automated_in_app_response = AsyncMock(return_value={'success': True})
        behavioral_network._schedule_automated_follow_up_sequence = AsyncMock(return_value={'success': True})
        behavioral_network._store_automated_response_audit = AsyncMock()
        behavioral_network._update_automated_response_tracking = AsyncMock()
        behavioral_network._setup_response_performance_monitoring = AsyncMock()

        result = await behavioral_network._send_automated_response(sample_trigger)

        # Verify email response was sent
        behavioral_network._send_automated_email_response.assert_called_once()

        # Verify result
        assert result['success'] is True
        assert result['response_channel'] == 'email'

    @pytest.mark.asyncio
    async def test_send_automated_response_sms(self, behavioral_network, sample_trigger):
        """Test automated SMS response."""
        behavioral_network._get_lead_details = AsyncMock(return_value={
            "name": "John Smith",
            "phone": "+1234567890",
            "source": "website"
        })
        behavioral_network._get_behavioral_context = AsyncMock(return_value={
            "currently_active": False
        })
        behavioral_network._determine_response_strategy = AsyncMock(return_value={
            "channel": "sms",
            "template": "quick_followup",
            "personalization": {"urgency": "medium"},
            "ai_enhanced": False
        })
        behavioral_network._send_automated_sms_response = AsyncMock(return_value={'success': True})
        behavioral_network._send_automated_in_app_response = AsyncMock(return_value={'success': True})
        behavioral_network._store_automated_response_audit = AsyncMock()
        behavioral_network._update_automated_response_tracking = AsyncMock()
        behavioral_network._setup_response_performance_monitoring = AsyncMock()

        result = await behavioral_network._send_automated_response(sample_trigger)

        # Verify SMS was sent
        behavioral_network._send_automated_sms_response.assert_called_once()
        assert result['success'] is True

    @pytest.mark.asyncio
    async def test_send_automated_response_no_lead_data(self, behavioral_network, sample_trigger):
        """Test automated response when lead data not found."""
        behavioral_network._get_lead_details = AsyncMock(return_value=None)
        behavioral_network._get_behavioral_context = AsyncMock(return_value={})

        result = await behavioral_network._send_automated_response(sample_trigger)

        assert result['success'] is False
        assert result['reason'] == 'no_lead_data'

    @pytest.mark.asyncio
    async def test_send_automated_response_communication_failure(self, behavioral_network, sample_trigger):
        """Test handling when communication services fail."""
        behavioral_network._get_lead_details = AsyncMock(return_value={
            "name": "John Smith",
            "email": "john@example.com"
        })
        behavioral_network._get_behavioral_context = AsyncMock(return_value={
            "currently_active": False
        })
        behavioral_network._determine_response_strategy = AsyncMock(return_value={
            "channel": "email",
            "template": "default",
            "personalization": {}
        })
        behavioral_network._send_automated_email_response = AsyncMock(side_effect=Exception("Email error"))
        behavioral_network._send_automated_in_app_response = AsyncMock(side_effect=Exception("App error"))
        behavioral_network._store_automated_response_audit = AsyncMock()
        behavioral_network._update_automated_response_tracking = AsyncMock()
        behavioral_network._setup_response_performance_monitoring = AsyncMock()

        result = await behavioral_network._send_automated_response(sample_trigger)

        # Should still complete without crashing, reporting failure
        assert result['success'] is False
        assert result['successful_responses'] == 0


class TestDeliverPersonalizedContent:
    """Test _deliver_personalized_content TODO method implementation."""

    @pytest.mark.asyncio
    async def test_deliver_personalized_content_success(self, behavioral_network, sample_trigger):
        """Test successful personalized content delivery."""
        behavioral_network._get_comprehensive_lead_profile = AsyncMock(return_value={
            "lead_id": "lead_456",
            "name": "John Smith",
            "email": "john@example.com",
            "preferences": {"budget": "400k-600k", "location": "Austin, TX"}
        })
        behavioral_network._get_behavioral_insights_history = AsyncMock(return_value={
            "total_visits": 15,
            "property_views": 8,
            "abandonment_risk": False,
            "high_intent_signals": True
        })
        behavioral_network._get_content_preferences = AsyncMock(return_value={
            "preferred_content_types": ["email", "interactive"]
        })
        behavioral_network._generate_content_strategy = AsyncMock(return_value={
            "personalization_level": "high",
            "content_types": ["email", "report", "interactive"],
            "delivery_channels": ["email", "website"],
            "theme": "property_recommendations",
            "target_intent": "buying_interest",
            "ai_generated": True,
            "version": "1.0"
        })
        behavioral_network._generate_personalized_email_content = AsyncMock(return_value={
            "subject": "Personalized Recommendations",
            "content": "AI-generated content"
        })
        behavioral_network._deliver_email_content = AsyncMock(return_value={'success': True})
        behavioral_network._generate_dynamic_website_content = AsyncMock(return_value={
            "widgets": ["recommendations"]
        })
        behavioral_network._deliver_website_content = AsyncMock(return_value={'success': True})
        behavioral_network._generate_personalized_property_report = AsyncMock(return_value={
            "report_type": "analysis"
        })
        behavioral_network._deliver_property_report = AsyncMock(return_value={'success': True})
        behavioral_network._generate_interactive_content = AsyncMock(return_value={
            "tools": ["calculator"]
        })
        behavioral_network._deliver_interactive_content = AsyncMock(return_value={'success': True})
        behavioral_network._update_content_preferences = AsyncMock()
        behavioral_network._store_content_delivery_audit = AsyncMock()
        behavioral_network._setup_content_engagement_tracking = AsyncMock()
        behavioral_network._schedule_content_performance_analysis = AsyncMock()

        result = await behavioral_network._deliver_personalized_content(sample_trigger)

        # Verify content generation and delivery
        behavioral_network._get_comprehensive_lead_profile.assert_called_once_with("lead_456")
        behavioral_network._generate_content_strategy.assert_called_once()
        assert result['success'] is True
        assert result['personalization_level'] == 'high'
        assert result['content_theme'] == 'property_recommendations'

    @pytest.mark.asyncio
    async def test_deliver_personalized_content_no_profile(self, behavioral_network, sample_trigger):
        """Test handling when lead profile not found."""
        behavioral_network._get_comprehensive_lead_profile = AsyncMock(return_value=None)
        behavioral_network._get_behavioral_insights_history = AsyncMock(return_value={})
        behavioral_network._get_content_preferences = AsyncMock(return_value={})

        result = await behavioral_network._deliver_personalized_content(sample_trigger)

        assert result['success'] is False
        assert result['reason'] == 'no_lead_profile'

    @pytest.mark.asyncio
    async def test_channel_optimization(self, behavioral_network, sample_trigger):
        """Test optimal channel selection for content delivery."""
        behavioral_network._get_comprehensive_lead_profile = AsyncMock(return_value={
            "lead_id": "lead_456",
            "name": "John Smith",
            "email": "john@example.com"
        })
        behavioral_network._get_behavioral_insights_history = AsyncMock(return_value={
            "abandonment_risk": False
        })
        behavioral_network._get_content_preferences = AsyncMock(return_value={})
        behavioral_network._generate_content_strategy = AsyncMock(return_value={
            "personalization_level": "medium",
            "content_types": ["email"],
            "delivery_channels": ["email"],
            "theme": "market_insights",
            "target_intent": "information_seeking",
            "ai_generated": False
        })
        behavioral_network._generate_personalized_email_content = AsyncMock(return_value={})
        behavioral_network._deliver_email_content = AsyncMock(return_value={'success': True})
        behavioral_network._update_content_preferences = AsyncMock()
        behavioral_network._store_content_delivery_audit = AsyncMock()
        behavioral_network._setup_content_engagement_tracking = AsyncMock()
        behavioral_network._schedule_content_performance_analysis = AsyncMock()

        result = await behavioral_network._deliver_personalized_content(sample_trigger)

        assert result['success'] is True
        behavioral_network._deliver_email_content.assert_called_once()


class TestBehavioralAnalysisAgents:
    """Test behavioral analysis agents."""

    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM client."""
        client = AsyncMock()
        client.generate.return_value = AsyncMock(
            content="Analysis: High intent lead based on behavioral patterns"
        )
        return client

    @pytest.mark.asyncio
    async def test_signal_detector_agent(self, mock_llm_client, sample_behavioral_signal):
        """Test signal detector agent processing."""
        agent = SignalDetectorAgent(mock_llm_client)
        signals = [sample_behavioral_signal]
        context = {"batch_size": 1}

        insights = await agent.process_signals(signals, context)

        assert isinstance(insights, list)
        # May be empty if signals don't meet thresholds, which is valid

    @pytest.mark.asyncio
    async def test_pattern_recognizer_agent(self, mock_llm_client, sample_behavioral_signal):
        """Test pattern recognizer agent processing."""
        agent = PatternRecognizerAgent(mock_llm_client)

        # Create multiple signals for pattern detection
        signals = []
        for i in range(5):
            signal = BehavioralSignal(
                signal_id=f"signal_{i}",
                lead_id="lead_456",
                signal_type=BehavioralSignalType.PROPERTY_VIEW,
                timestamp=datetime.now() - timedelta(minutes=i),
                interaction_value=8.0 + i
            )
            signals.append(signal)

        context = {"batch_size": len(signals)}
        insights = await agent.process_signals(signals, context)

        assert isinstance(insights, list)

    @pytest.mark.asyncio
    async def test_intent_predictor_agent(self, mock_llm_client, sample_behavioral_signal):
        """Test intent predictor agent processing."""
        agent = IntentPredictorAgent(mock_llm_client)

        # Create signals indicating buying intent
        signals = [
            BehavioralSignal(
                signal_id="calc_signal",
                lead_id="lead_456",
                signal_type=BehavioralSignalType.CALCULATOR_USAGE,
                timestamp=datetime.now(),
                interaction_value=10.0
            ),
            BehavioralSignal(
                signal_id="form_signal",
                lead_id="lead_456",
                signal_type=BehavioralSignalType.FORM_INTERACTION,
                timestamp=datetime.now(),
                interaction_value=9.0
            ),
            sample_behavioral_signal
        ]

        context = {"batch_size": len(signals)}
        insights = await agent.process_signals(signals, context)

        assert isinstance(insights, list)


class TestRealTimeBehavioralNetwork:
    """Test main RealTimeBehavioralNetwork class."""

    @pytest.mark.asyncio
    async def test_network_initialization(self):
        """Test behavioral network initialization."""
        network = RealTimeBehavioralNetwork()

        assert network.signal_detector is not None
        assert network.pattern_recognizer is not None
        assert network.intent_predictor is not None
        assert network.signal_queue is not None
        assert network.insight_queue is not None
        assert network.trigger_queue is not None

    @pytest.mark.asyncio
    async def test_signal_ingestion(self, behavioral_network, sample_behavioral_signal):
        """Test behavioral signal ingestion."""
        initial_count = behavioral_network.network_stats['total_signals_processed']

        behavioral_network.ingest_behavioral_signal(sample_behavioral_signal)

        assert behavioral_network.network_stats['total_signals_processed'] == initial_count + 1

    @pytest.mark.asyncio
    async def test_signal_queue_overflow_handling(self, behavioral_network):
        """Test handling of signal queue overflow."""
        # Fill up the queue to capacity
        for i in range(behavioral_network.signal_queue.maxsize + 10):
            signal = BehavioralSignal(
                signal_id=f"signal_{i}",
                lead_id=f"lead_{i}",
                signal_type=BehavioralSignalType.PAGE_VIEW,
                timestamp=datetime.now()
            )
            behavioral_network.ingest_behavioral_signal(signal)

        # Should handle gracefully without crashing
        # Additional signals should be dropped, not cause errors

    @pytest.mark.asyncio
    async def test_trigger_generation_and_execution(self, behavioral_network):
        """Test trigger generation and execution."""
        # Create a mock insight that should generate triggers
        insight = BehavioralInsight(
            agent_type=BehavioralAnalysisAgentType.INTENT_PREDICTOR,
            insight_id="insight_123",
            lead_id="lead_456",
            detected_patterns=[BehavioralPattern.HIGH_INTENT_BROWSING],
            confidence_score=0.9,
            urgency_level="high",
            predicted_intent="buying_intent",
            recommended_actions=["immediate_contact"],
            trigger_suggestions=[TriggerType.IMMEDIATE_ALERT, TriggerType.AGENT_NOTIFICATION],
            behavioral_score=85.0,
            processing_time_ms=100.0
        )

        # Test trigger generation
        triggers = await behavioral_network._generate_realtime_triggers([insight])

        assert len(triggers) >= 1
        for trigger in triggers:
            assert trigger.lead_id == "lead_456"
            assert trigger.priority >= 1

    @pytest.mark.asyncio
    async def test_urgent_trigger_execution(self, behavioral_network, sample_trigger):
        """Test urgent trigger execution."""
        sample_trigger.priority = 5  # High priority

        # Mock internal methods called during trigger execution
        behavioral_network._get_lead_details = AsyncMock(return_value={
            "name": "John Smith",
            "email": "john@example.com",
            "phone": "+1234567890"
        })
        behavioral_network._send_email_alert = AsyncMock(return_value={'success': True})
        behavioral_network._send_sms_alert = AsyncMock(return_value={'success': True})
        behavioral_network._send_slack_alert = AsyncMock(return_value={'success': True})
        behavioral_network._send_dashboard_notification = AsyncMock(return_value={'success': True})
        behavioral_network._store_alert_audit = AsyncMock()

        await behavioral_network._execute_trigger(sample_trigger)

        assert sample_trigger.executed is True
        assert sample_trigger.execution_result is not None
        assert sample_trigger.execution_result.get('success') is True


class TestIntegrationWorkflows:
    """Test complete behavioral network integration workflows."""

    @pytest.mark.asyncio
    async def test_high_intent_lead_complete_workflow(self, behavioral_network):
        """Test complete workflow for high-intent lead."""
        # Create high-intent trigger
        high_intent_trigger = RealTimeTrigger(
            trigger_id="trigger_high",
            lead_id="lead_urgent",
            trigger_type=TriggerType.IMMEDIATE_ALERT,
            trigger_condition="urgent_multiple_property_views",
            action_payload={
                "behavioral_score": 95,
                "properties_viewed": 5,
                "time_spent": "45_minutes",
                "context": "Viewed multiple luxury properties in target area",
                "urgency": "critical",
                "confidence": 0.95,
                "recommendations": ["call_now", "send_listings"]
            },
            priority=5,
            expiration_time=datetime.now() + timedelta(hours=1)
        )

        # Mock all internal helper methods used by the 5 TODO methods
        behavioral_network._get_lead_details = AsyncMock(return_value={
            "name": "Urgent Lead",
            "email": "urgent@example.com",
            "phone": "+1111111111"
        })
        behavioral_network._send_email_alert = AsyncMock(return_value={'success': True})
        behavioral_network._send_sms_alert = AsyncMock(return_value={'success': True})
        behavioral_network._send_slack_alert = AsyncMock(return_value={'success': True})
        behavioral_network._send_dashboard_notification = AsyncMock(return_value={'success': True})
        behavioral_network._store_alert_audit = AsyncMock()

        behavioral_network._get_agent_assignment = AsyncMock(return_value={
            "agent_id": "agent_1",
            "agent_info": {"name": "Agent", "email": "agent@test.com", "phone": "+12223334444"},
            "workload_info": {}
        })
        behavioral_network._send_agent_dashboard_notification = AsyncMock(return_value={'success': True})
        behavioral_network._send_agent_email_notification = AsyncMock(return_value={'success': True})
        behavioral_network._send_agent_push_notification = AsyncMock(return_value={'success': True})
        behavioral_network._send_agent_sms_notification = AsyncMock(return_value={'success': True})
        behavioral_network._update_agent_workload = AsyncMock()
        behavioral_network._store_notification_audit = AsyncMock()
        behavioral_network._schedule_agent_followup_reminder = AsyncMock()

        behavioral_network._set_ghl_priority_flag = AsyncMock(return_value={'success': True})
        behavioral_network._set_internal_priority_flag = AsyncMock(return_value={'success': True})
        behavioral_network._cache_priority_status = AsyncMock(return_value={'success': True})
        behavioral_network._update_lead_priority_scoring = AsyncMock(return_value={'success': True})
        behavioral_network._trigger_priority_workflow = AsyncMock(return_value={'success': True})
        behavioral_network._schedule_priority_flag_review = AsyncMock(return_value={'success': True})
        behavioral_network._store_priority_flag_audit = AsyncMock()
        behavioral_network._send_priority_flag_notifications = AsyncMock()

        behavioral_network._get_behavioral_context = AsyncMock(return_value={"currently_active": False})
        behavioral_network._determine_response_strategy = AsyncMock(return_value={
            "channel": "email", "template": "urgent", "personalization": {}
        })
        behavioral_network._send_automated_email_response = AsyncMock(return_value={'success': True})
        behavioral_network._send_automated_in_app_response = AsyncMock(return_value={'success': True})
        behavioral_network._store_automated_response_audit = AsyncMock()
        behavioral_network._update_automated_response_tracking = AsyncMock()
        behavioral_network._setup_response_performance_monitoring = AsyncMock()

        behavioral_network._get_comprehensive_lead_profile = AsyncMock(return_value={
            "lead_id": "lead_urgent",
            "email": "urgent@example.com"
        })
        behavioral_network._get_behavioral_insights_history = AsyncMock(return_value={
            "abandonment_risk": False
        })
        behavioral_network._get_content_preferences = AsyncMock(return_value={})
        behavioral_network._generate_content_strategy = AsyncMock(return_value={
            "personalization_level": "high",
            "content_types": ["email"],
            "delivery_channels": ["email"],
            "theme": "urgent_properties",
            "target_intent": "buying_intent",
            "ai_generated": True
        })
        behavioral_network._generate_personalized_email_content = AsyncMock(return_value={})
        behavioral_network._deliver_email_content = AsyncMock(return_value={'success': True})
        behavioral_network._update_content_preferences = AsyncMock()
        behavioral_network._store_content_delivery_audit = AsyncMock()
        behavioral_network._setup_content_engagement_tracking = AsyncMock()
        behavioral_network._schedule_content_performance_analysis = AsyncMock()

        # Execute all 5 TODO methods in sequence
        await behavioral_network._send_immediate_alert(high_intent_trigger)
        await behavioral_network._notify_agent(high_intent_trigger)
        await behavioral_network._set_priority_flag(high_intent_trigger)
        await behavioral_network._send_automated_response(high_intent_trigger)
        await behavioral_network._deliver_personalized_content(high_intent_trigger)

        # Verify comprehensive workflow execution
        behavioral_network._get_lead_details.assert_called()
        assert behavioral_network._get_lead_details.call_count >= 1

    @pytest.mark.asyncio
    async def test_signal_processing_pipeline(self, behavioral_network, sample_behavioral_signal):
        """Test complete signal processing pipeline."""
        # Create batch of signals
        signals = []
        for i in range(5):
            signal = BehavioralSignal(
                signal_id=f"signal_{i}",
                lead_id="lead_456",
                signal_type=BehavioralSignalType.PROPERTY_VIEW if i % 2 == 0 else BehavioralSignalType.CALCULATOR_USAGE,
                timestamp=datetime.now() - timedelta(minutes=i),
                interaction_value=7.0 + i
            )
            signals.append(signal)

        # Process signals through the pipeline
        await behavioral_network._process_signals_batch(signals)

        # Verify processing completed without errors
        assert behavioral_network.network_stats['total_insights_generated'] >= 0

    @pytest.mark.asyncio
    async def test_error_recovery_in_processing_pipeline(self, behavioral_network):
        """Test error recovery when components fail during processing."""
        # Mock agent failures
        behavioral_network.signal_detector.process_signals = AsyncMock(side_effect=Exception("Agent Error"))

        # Create test signals
        signals = [BehavioralSignal(
            signal_id="signal_error",
            lead_id="lead_456",
            signal_type=BehavioralSignalType.PAGE_VIEW,
            timestamp=datetime.now()
        )]

        # Should handle gracefully
        await behavioral_network._process_signals_batch(signals)

        # Processing should continue despite agent failure


class TestPerformanceMetrics:
    """Test performance and metrics tracking."""

    @pytest.mark.asyncio
    async def test_network_stats_tracking(self, behavioral_network, sample_behavioral_signal):
        """Test network statistics tracking."""
        initial_stats = behavioral_network.network_stats.copy()

        # Ingest signals
        for i in range(5):
            signal = BehavioralSignal(
                signal_id=f"perf_signal_{i}",
                lead_id=f"lead_{i}",
                signal_type=BehavioralSignalType.PAGE_VIEW,
                timestamp=datetime.now()
            )
            behavioral_network.ingest_behavioral_signal(signal)

        # Verify stats updated
        assert behavioral_network.network_stats['total_signals_processed'] > initial_stats['total_signals_processed']

    @pytest.mark.asyncio
    async def test_processing_latency_measurement(self, behavioral_network):
        """Test processing latency measurement."""
        signals = [BehavioralSignal(
            signal_id="latency_signal",
            lead_id="lead_456",
            signal_type=BehavioralSignalType.PROPERTY_VIEW,
            timestamp=datetime.now()
        )]

        start_time = time.time()
        await behavioral_network._process_signals_batch(signals)
        processing_time = time.time() - start_time

        # Should complete in reasonable time
        assert processing_time < 5.0, f"Processing took {processing_time:.3f}s"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=ghl_real_estate_ai.services.realtime_behavioral_network"])
