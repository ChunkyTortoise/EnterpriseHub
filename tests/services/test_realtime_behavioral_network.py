#!/usr/bin/env python3
"""
Tests for Real-time Behavioral Network - Including 5 TODO methods implementation
=============================================================================

Comprehensive test suite covering:
- All 5 TODO methods: _send_immediate_alert, _notify_agent, _set_priority_flag, 
  _send_automated_response, _deliver_personalized_content
- Real-time behavioral signal processing
- Multi-channel notification systems
- Database integration and logging

Target Coverage: 85%+ on realtime_behavioral_network.py
"""

import pytest
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
            "context": "Viewed premium listing for 15+ minutes"
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

@pytest.fixture
async def mock_services():
    """Mock external services."""
    return {
        "database_service": AsyncMock(),
        "email_service": AsyncMock(),
        "sms_service": AsyncMock(),
        "claude_client": AsyncMock()
    }

@pytest.fixture
async def behavioral_network(mock_services):
    """Create behavioral network with mocked services."""
    network = RealTimeBehavioralNetwork()
    
    # Inject mocked services
    for service_name, mock_service in mock_services.items():
        setattr(network, service_name, mock_service)
    
    # Setup database service responses
    network.database_service.get_lead.return_value = {
        "id": "lead_456",
        "first_name": "John",
        "last_name": "Smith", 
        "email": "john@example.com",
        "phone": "+1234567890",
        "assigned_agent_id": "agent_123"
    }
    
    network.database_service.get_available_agents.return_value = [
        {
            "id": "agent_123",
            "name": "Sarah Wilson",
            "email": "sarah@realestate.com",
            "phone": "+1987654321",
            "is_available": True,
            "current_load": 5,
            "capacity": 20
        }
    ]
    
    network.database_service.get_assigned_or_available_agent.return_value = {
        "id": "agent_123",
        "name": "Sarah Wilson",
        "email": "sarah@realestate.com",
        "phone": "+1987654321",
        "is_available": True
    }
    
    network.database_service.log_communication.return_value = True
    network.database_service.update_lead.return_value = True
    network.database_service.update_agent.return_value = True
    
    # Setup email and SMS services
    network.email_service.send_templated_email.return_value = True
    network.sms_service.send_templated_sms.return_value = True
    
    # Setup Claude client
    network.claude_client.generate.return_value = AsyncMock(
        content="Personalized market insights for Austin luxury homes..."
    )
    
    return network

class TestSendImmediateAlert:
    """Test _send_immediate_alert TODO method implementation."""
    
    @pytest.mark.asyncio
    async def test_send_immediate_alert_success(self, behavioral_network, sample_trigger):
        """Test successful immediate alert sending."""
        # Execute method
        await behavioral_network._send_immediate_alert(sample_trigger)
        
        # Verify database queries
        behavioral_network.database_service.get_lead.assert_called_once_with("lead_456")
        
        # Verify communication logging
        behavioral_network.database_service.log_communication.assert_called_once()
        log_call = behavioral_network.database_service.log_communication.call_args[0][0]
        
        assert log_call["lead_id"] == "lead_456"
        assert log_call["channel"] == "system_alert"
        assert log_call["direction"] == "outbound"
        assert "trigger_id" in log_call["metadata"]
    
    @pytest.mark.asyncio
    async def test_send_immediate_alert_no_database(self, sample_trigger):
        """Test alert handling when database is unavailable."""
        network = RealTimeBehavioralNetwork()
        network.database_service = None
        
        # Should not crash, should log warning
        await network._send_immediate_alert(sample_trigger)
        # No assertions needed - just verify it doesn't crash
    
    @pytest.mark.asyncio
    async def test_send_immediate_alert_high_priority(self, behavioral_network, sample_trigger):
        """Test multi-channel alert sending for high priority."""
        # Set high priority to trigger multiple channels
        sample_trigger.priority = 5
        
        await behavioral_network._send_immediate_alert(sample_trigger)
        
        # Should trigger database operations
        behavioral_network.database_service.get_lead.assert_called_once()
        behavioral_network.database_service.log_communication.assert_called_once()

class TestNotifyAgent:
    """Test _notify_agent TODO method implementation."""
    
    @pytest.mark.asyncio
    async def test_notify_agent_assigned_agent(self, behavioral_network, sample_trigger):
        """Test notifying assigned agent."""
        await behavioral_network._notify_agent(sample_trigger)
        
        # Verify agent was queried
        behavioral_network.database_service.get_assigned_or_available_agent.assert_called_once_with("lead_456")
        
        # Verify agent notification was logged
        behavioral_network.database_service.log_communication.assert_called()
        log_call = behavioral_network.database_service.log_communication.call_args[0][0]
        assert log_call["lead_id"] == "lead_456"
        assert "agent_notification" in log_call["channel"]
    
    @pytest.mark.asyncio
    async def test_notify_agent_no_available_agent(self, behavioral_network, sample_trigger):
        """Test behavior when no agents are available."""
        behavioral_network.database_service.get_assigned_or_available_agent.return_value = None
        behavioral_network.database_service.get_next_available_agent.return_value = None
        
        # Should handle gracefully
        await behavioral_network._notify_agent(sample_trigger)
        
        # Should still log the attempt
        behavioral_network.database_service.log_communication.assert_called()
    
    @pytest.mark.asyncio
    async def test_notify_agent_multi_channel_notification(self, behavioral_network, sample_trigger):
        """Test multi-channel agent notification."""
        # High priority trigger should send multiple notifications
        sample_trigger.priority = 4
        
        await behavioral_network._notify_agent(sample_trigger)
        
        # Verify agent was queried
        behavioral_network.database_service.get_assigned_or_available_agent.assert_called_once()
        
        # Verify communication was logged
        behavioral_network.database_service.log_communication.assert_called()

class TestSetPriorityFlag:
    """Test _set_priority_flag TODO method implementation."""
    
    @pytest.mark.asyncio
    async def test_set_priority_flag_success(self, behavioral_network, sample_trigger):
        """Test successful priority flag setting."""
        # Mock current lead data
        behavioral_network.database_service.get_lead.return_value = {
            "id": "lead_456",
            "priority": "medium",
            "lead_score": 65,
            "temperature": "warm"
        }
        
        await behavioral_network._set_priority_flag(sample_trigger)
        
        # Verify lead was updated
        behavioral_network.database_service.update_lead.assert_called_once()
        update_call = behavioral_network.database_service.update_lead.call_args[0]
        
        assert update_call[0] == "lead_456"  # Lead ID
        update_data = update_call[1]
        assert "priority" in update_data
        assert "lead_score" in update_data or "temperature" in update_data
    
    @pytest.mark.asyncio
    async def test_priority_escalation_triggers_rerouting(self, behavioral_network, sample_trigger):
        """Test that priority escalation triggers agent re-routing."""
        # Mock current lead with low priority
        behavioral_network.database_service.get_lead.return_value = {
            "id": "lead_456",
            "priority": "low",
            "lead_score": 30,
            "assigned_agent_id": "agent_456"
        }
        
        # Mock best agent for high priority
        behavioral_network.database_service.get_best_agent_for_priority.return_value = {
            "id": "agent_789",
            "name": "Top Agent",
            "email": "top@realestate.com"
        }
        
        # High priority trigger
        sample_trigger.priority = 5
        sample_trigger.action_payload["behavioral_score"] = 90
        
        await behavioral_network._set_priority_flag(sample_trigger)
        
        # Should update the lead
        behavioral_network.database_service.update_lead.assert_called_once()
        
        # Should log the priority change
        behavioral_network.database_service.log_communication.assert_called()
    
    @pytest.mark.asyncio
    async def test_set_priority_flag_database_error(self, behavioral_network, sample_trigger):
        """Test handling of database errors during priority flag setting."""
        # Mock database error
        behavioral_network.database_service.get_lead.side_effect = Exception("Database error")
        
        # Should handle gracefully
        await behavioral_network._set_priority_flag(sample_trigger)
        
        # Should not crash - method should handle the exception internally

class TestSendAutomatedResponse:
    """Test _send_automated_response TODO method implementation."""
    
    @pytest.mark.asyncio
    async def test_send_automated_response_sms(self, behavioral_network, sample_trigger):
        """Test automated SMS response."""
        # Mock lead data preferring SMS
        behavioral_network.database_service.get_lead.return_value = {
            "id": "lead_456",
            "first_name": "John",
            "phone": "+1234567890",
            "email": "john@example.com",
            "preferred_communication": "sms"
        }
        
        # Mock successful SMS sending
        behavioral_network.sms_service.send_templated_sms.return_value = True
        
        await behavioral_network._send_automated_response(sample_trigger)
        
        # Verify SMS was sent
        behavioral_network.sms_service.send_templated_sms.assert_called_once()
        
        # Verify communication was logged
        behavioral_network.database_service.log_communication.assert_called()
        log_call = behavioral_network.database_service.log_communication.call_args[0][0]
        assert log_call["channel"] == "sms"
    
    @pytest.mark.asyncio 
    async def test_send_automated_response_email(self, behavioral_network, sample_trigger):
        """Test automated email response."""
        # Mock lead preferring email
        behavioral_network.database_service.get_lead.return_value = {
            "id": "lead_456",
            "first_name": "John",
            "email": "john@example.com",
            "preferred_communication": "email"
        }
        
        # Mock successful email sending
        behavioral_network.email_service.send_templated_email.return_value = True
        
        await behavioral_network._send_automated_response(sample_trigger)
        
        # Verify email was sent
        behavioral_network.email_service.send_templated_email.assert_called_once()
        
        # Verify communication was logged
        behavioral_network.database_service.log_communication.assert_called()
        log_call = behavioral_network.database_service.log_communication.call_args[0][0]
        assert log_call["channel"] == "email"
    
    @pytest.mark.asyncio
    async def test_template_selection_logic(self, behavioral_network, sample_trigger):
        """Test template selection based on trigger type."""
        behavioral_network.database_service.get_lead.return_value = {
            "id": "lead_456",
            "first_name": "John",
            "email": "john@example.com"
        }
        
        # Test property view trigger
        sample_trigger.trigger_condition = "property_view_extended"
        await behavioral_network._send_automated_response(sample_trigger)
        
        # Should select appropriate template and send message
        # Verify either email or SMS service was called
        assert (behavioral_network.email_service.send_templated_email.called or 
                behavioral_network.sms_service.send_templated_sms.called)
    
    @pytest.mark.asyncio
    async def test_send_automated_response_communication_failure(self, behavioral_network, sample_trigger):
        """Test handling when communication services fail."""
        behavioral_network.database_service.get_lead.return_value = {
            "id": "lead_456",
            "first_name": "John",
            "email": "john@example.com"
        }
        
        # Mock communication service failures
        behavioral_network.email_service.send_templated_email.return_value = False
        behavioral_network.sms_service.send_templated_sms.return_value = False
        
        await behavioral_network._send_automated_response(sample_trigger)
        
        # Should still log the attempt even if sending fails
        behavioral_network.database_service.log_communication.assert_called()

class TestDeliverPersonalizedContent:
    """Test _deliver_personalized_content TODO method implementation."""
    
    @pytest.mark.asyncio
    async def test_deliver_personalized_content_success(self, behavioral_network, sample_trigger):
        """Test successful personalized content delivery."""
        # Mock lead profile
        behavioral_network.database_service.get_lead_profile_data.return_value = {
            "id": "lead_456",
            "first_name": "John",
            "email": "john@example.com",
            "budget_range": "$400k-600k",
            "preferred_location": "Austin, TX"
        }
        
        # Mock behavioral data
        behavioral_network.database_service.get_lead_activity_data.return_value = {
            "property_searches": [{"criteria": {"price_max": 600000}}],
            "website_visits": [{"page": "/luxury-homes"}]
        }
        
        # Mock AI content generation
        behavioral_network.claude_client.generate.return_value = AsyncMock(
            content="Personalized market insights for Austin luxury homes..."
        )
        
        await behavioral_network._deliver_personalized_content(sample_trigger)
        
        # Verify AI content generation was called
        behavioral_network.claude_client.generate.assert_called_once()
        
        # Verify content delivery was logged
        behavioral_network.database_service.log_communication.assert_called()
        log_call = behavioral_network.database_service.log_communication.call_args[0][0]
        assert log_call["lead_id"] == "lead_456"
        assert "personalized_content" in log_call["channel"]
    
    @pytest.mark.asyncio
    async def test_content_generation_failure_handling(self, behavioral_network, sample_trigger):
        """Test handling of AI content generation failures."""
        behavioral_network.database_service.get_lead_profile_data.return_value = {
            "id": "lead_456",
            "first_name": "John",
            "email": "john@example.com"
        }
        
        # Mock AI failure
        behavioral_network.claude_client.generate.side_effect = Exception("AI API Error")
        
        # Should handle gracefully without crashing
        await behavioral_network._deliver_personalized_content(sample_trigger)
        
        # Should still log the attempt
        behavioral_network.database_service.log_communication.assert_called()
        log_call = behavioral_network.database_service.log_communication.call_args[0][0]
        assert "error" in log_call.get("metadata", {}).get("status", "") or log_call.get("status") == "failed"
    
    @pytest.mark.asyncio
    async def test_channel_optimization(self, behavioral_network, sample_trigger):
        """Test optimal channel selection for content delivery."""
        # Mock lead with preferences
        behavioral_network.database_service.get_lead_profile_data.return_value = {
            "id": "lead_456",
            "first_name": "John",
            "email": "john@example.com",
            "phone": "+1234567890",
            "preferred_communication": "email"
        }
        
        behavioral_network.database_service.get_lead_activity_data.return_value = {
            "email_interactions": [{"opened": True, "clicked": True}]  # High email engagement
        }
        
        behavioral_network.claude_client.generate.return_value = AsyncMock(
            content="Test personalized content"
        )
        
        await behavioral_network._deliver_personalized_content(sample_trigger)
        
        # Should optimize for email based on preferences and engagement
        behavioral_network.database_service.log_communication.assert_called()

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
                "context": "Viewed multiple luxury properties in target area"
            },
            priority=5,
            expiration_time=datetime.now() + timedelta(hours=1)
        )
        
        # Execute all 5 TODO methods in sequence
        await behavioral_network._send_immediate_alert(high_intent_trigger)
        await behavioral_network._notify_agent(high_intent_trigger)
        await behavioral_network._set_priority_flag(high_intent_trigger)
        await behavioral_network._send_automated_response(high_intent_trigger)
        await behavioral_network._deliver_personalized_content(high_intent_trigger)
        
        # Verify comprehensive workflow execution
        # All database operations should have been called
        assert behavioral_network.database_service.get_lead.call_count >= 1
        assert behavioral_network.database_service.log_communication.call_count >= 1
    
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
        behavioral_network.signal_detector.process_signals.side_effect = Exception("Agent Error")
        
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
        assert processing_time < 1.0, f"Processing took {processing_time:.3f}s"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=ghl_real_estate_ai.services.realtime_behavioral_network"])