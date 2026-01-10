"""
Comprehensive Test Suite for Advanced GHL Workflow Automation System

Tests all components of the workflow automation system including:
- Enhanced Advanced Workflow Engine
- Behavioral Trigger Service
- Enhanced Multichannel Orchestrator
- Integration with Enhanced Webhook Processor
- End-to-end workflow execution

Target: 80%+ test coverage with performance validation
"""

import asyncio
import json
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

# Import the services to test
from ghl_real_estate_ai.services.enhanced_advanced_workflow_engine import (
    EnhancedAdvancedWorkflowEngine,
    WorkflowExecution,
    WorkflowStatus,
    WorkflowMetrics,
    get_enhanced_advanced_workflow_engine
)
from ghl_real_estate_ai.services.behavioral_trigger_service import (
    BehavioralTriggerService,
    BehaviorEvent,
    BehaviorType,
    EngagementSpike,
    InactivityRisk,
    TriggerType,
    get_behavioral_trigger_service
)
from ghl_real_estate_ai.services.enhanced_multichannel_orchestrator import (
    EnhancedMultichannelOrchestrator,
    Channel,
    Message,
    MessageTemplate,
    MessageStatus,
    get_enhanced_multichannel_orchestrator
)
from ghl_real_estate_ai.services.enhanced_webhook_processor import (
    EnhancedWebhookProcessor,
    WebhookEvent,
    ProcessingResult,
    get_enhanced_webhook_processor
)


class TestBehavioralTriggerService:
    """Test suite for Behavioral Trigger Service."""

    @pytest.fixture
    async def behavioral_service(self):
        """Create test behavioral trigger service."""
        service = BehavioralTriggerService(
            cache_manager=AsyncMock(),
            workflow_engine=AsyncMock()
        )
        return service

    @pytest.fixture
    def sample_behavior_event(self):
        """Create sample behavior event."""
        return BehaviorEvent(
            event_id="test_event_1",
            contact_id="contact_123",
            behavior_type=BehaviorType.EMAIL_OPEN,
            timestamp=datetime.now(),
            metadata={"email_id": "email_123"},
            engagement_value=0.5,
            qualification_impact=0.02
        )

    @pytest.mark.asyncio
    async def test_track_behavior_performance(self, behavioral_service, sample_behavior_event):
        """Test behavior tracking performance (<25ms target)."""
        start_time = time.time()

        await behavioral_service.track_behavior("contact_123", sample_behavior_event)

        processing_time_ms = (time.time() - start_time) * 1000
        assert processing_time_ms < 25, f"Behavior tracking took {processing_time_ms}ms (target: <25ms)"

        # Verify event was tracked
        assert "contact_123" in behavioral_service._behavior_history
        assert len(behavioral_service._behavior_history["contact_123"]) == 1
        assert behavioral_service._behavior_history["contact_123"][0] == sample_behavior_event

    @pytest.mark.asyncio
    async def test_engagement_score_calculation(self, behavioral_service):
        """Test engagement score calculation performance (<50ms target)."""
        contact_id = "contact_123"

        # Add multiple behavior events
        events = [
            BehaviorEvent(
                event_id=f"event_{i}",
                contact_id=contact_id,
                behavior_type=BehaviorType.EMAIL_OPEN,
                timestamp=datetime.now() - timedelta(hours=i),
                engagement_value=0.3 + (i * 0.1)
            )
            for i in range(5)
        ]

        for event in events:
            await behavioral_service.track_behavior(contact_id, event)

        start_time = time.time()

        score = await behavioral_service.calculate_engagement_score(contact_id, 24)

        processing_time_ms = (time.time() - start_time) * 1000
        assert processing_time_ms < 50, f"Engagement score calculation took {processing_time_ms}ms (target: <50ms)"

        # Verify score is reasonable
        assert 0.0 <= score <= 1.0
        assert score > 0, "Score should be greater than 0 with engagement events"

    @pytest.mark.asyncio
    async def test_engagement_spike_detection(self, behavioral_service):
        """Test engagement spike detection."""
        contact_id = "contact_123"

        # Create property view spike (3+ views in 24h)
        property_events = [
            BehaviorEvent(
                event_id=f"prop_view_{i}",
                contact_id=contact_id,
                behavior_type=BehaviorType.PROPERTY_VIEW,
                timestamp=datetime.now() - timedelta(hours=i),
                engagement_value=0.7
            )
            for i in range(4)  # 4 property views
        ]

        for event in property_events:
            await behavioral_service.track_behavior(contact_id, event)

        start_time = time.time()

        spike = await behavioral_service.detect_engagement_spike(contact_id)

        processing_time_ms = (time.time() - start_time) * 1000
        assert processing_time_ms < 75, f"Pattern detection took {processing_time_ms}ms (target: <75ms)"

        # Verify spike detected
        assert spike is not None
        assert spike.contact_id == contact_id
        assert spike.spike_type == "property_view_spike"
        assert spike.events_count == 4
        assert spike.confidence > 0.5

    @pytest.mark.asyncio
    async def test_inactivity_risk_detection(self, behavioral_service):
        """Test inactivity risk detection."""
        contact_id = "contact_inactive"

        # Add old behavior event (8 days ago)
        old_event = BehaviorEvent(
            event_id="old_event",
            contact_id=contact_id,
            behavior_type=BehaviorType.EMAIL_OPEN,
            timestamp=datetime.now() - timedelta(days=8),
            engagement_value=0.5
        )

        await behavioral_service.track_behavior(contact_id, old_event)

        inactivity = await behavioral_service.detect_inactivity_risk(contact_id)

        # Verify inactivity detected
        assert inactivity is not None
        assert inactivity.contact_id == contact_id
        assert inactivity.days_inactive >= 7
        assert inactivity.risk_level in ["medium", "high", "critical"]

    @pytest.mark.asyncio
    async def test_trigger_evaluation_performance(self, behavioral_service):
        """Test trigger evaluation performance (<100ms target)."""
        contact_id = "contact_123"

        # Add various behavior events
        events = [
            BehaviorEvent(f"event_{i}", contact_id, BehaviorType.EMAIL_OPEN, datetime.now() - timedelta(hours=i))
            for i in range(3)
        ]

        for event in events:
            await behavioral_service.track_behavior(contact_id, event)

        start_time = time.time()

        triggers = await behavioral_service.evaluate_triggers(contact_id)

        processing_time_ms = (time.time() - start_time) * 1000
        assert processing_time_ms < 100, f"Trigger evaluation took {processing_time_ms}ms (target: <100ms)"

        # Verify triggers is a list
        assert isinstance(triggers, list)


class TestEnhancedMultichannelOrchestrator:
    """Test suite for Enhanced Multichannel Orchestrator."""

    @pytest.fixture
    async def orchestrator(self):
        """Create test multichannel orchestrator."""
        return EnhancedMultichannelOrchestrator(
            ghl_client=AsyncMock(),
            cache_manager=AsyncMock(),
            behavioral_service=AsyncMock(),
            webhook_processor=AsyncMock()
        )

    @pytest.fixture
    def sample_message_template(self):
        """Create sample message template."""
        return MessageTemplate(
            template_id="test_template",
            channel=Channel.EMAIL,
            subject="Test Subject {first_name}",
            content="Hi {first_name}, this is a test message.",
            variables={"agent_name": "John Smith"}
        )

    @pytest.fixture
    def sample_message(self, sample_message_template):
        """Create sample message."""
        return Message(
            message_id="msg_test_123",
            contact_id="contact_123",
            channel=Channel.EMAIL,
            template=sample_message_template,
            scheduled_at=datetime.now(),
            context={"first_name": "Jane", "agent_name": "John Smith"}
        )

    @pytest.mark.asyncio
    async def test_send_message_performance(self, orchestrator, sample_message):
        """Test message sending performance (<150ms target)."""
        # Mock channel availability and rate limiting
        orchestrator.check_channel_availability = AsyncMock(return_value=True)
        orchestrator._check_rate_limit = AsyncMock(return_value=True)
        orchestrator._get_contact_location = AsyncMock(return_value="loc_123")
        orchestrator._send_via_channel = AsyncMock(return_value={"success": True, "message_id": "sent_123"})

        start_time = time.time()

        result = await orchestrator.send_message(
            "contact_123", Channel.EMAIL, sample_message
        )

        processing_time_ms = (time.time() - start_time) * 1000
        assert processing_time_ms < 150, f"Message sending took {processing_time_ms}ms (target: <150ms)"

        # Verify result
        assert result.get("success") is True
        assert "processing_time_ms" in result

    @pytest.mark.asyncio
    async def test_channel_availability_check(self, orchestrator):
        """Test channel availability check performance (<25ms target)."""
        # Mock dependencies
        orchestrator._is_outside_quiet_hours = AsyncMock(return_value=True)
        orchestrator._get_channel_preferences = AsyncMock(return_value={})
        orchestrator._get_contact_data = AsyncMock(return_value={"email": "test@example.com", "phone": "+1234567890"})
        orchestrator._check_recent_message_frequency = AsyncMock(return_value=False)

        start_time = time.time()

        available = await orchestrator.check_channel_availability("contact_123", Channel.EMAIL)

        processing_time_ms = (time.time() - start_time) * 1000
        assert processing_time_ms < 25, f"Channel availability check took {processing_time_ms}ms (target: <25ms)"

        assert available is True

    @pytest.mark.asyncio
    async def test_optimal_channel_selection(self, orchestrator):
        """Test optimal channel selection algorithm."""
        contact_id = "contact_123"

        # Mock behavioral service
        orchestrator.behavioral_service.get_contact_behavioral_summary = AsyncMock(return_value={
            'engagement_score': 0.7,
            'behavior_distribution': {
                'email_open': 5,
                'sms_reply': 2,
                'property_view': 10
            }
        })

        # Mock engagement history
        orchestrator._engagement_history[contact_id] = [
            {"channel": "email", "action": "opened", "timestamp": datetime.now().isoformat()},
            {"channel": "sms", "action": "replied", "timestamp": datetime.now().isoformat()}
        ]

        # Mock channel availability
        orchestrator.check_channel_availability = AsyncMock(return_value=True)

        optimal_channel = await orchestrator.select_optimal_channel(
            contact_id, message_type="general", urgency="normal"
        )

        # Verify channel selection
        assert optimal_channel in [Channel.EMAIL, Channel.SMS, Channel.VOICE, Channel.WHATSAPP]

    @pytest.mark.asyncio
    async def test_engagement_tracking(self, orchestrator):
        """Test engagement tracking functionality."""
        contact_id = "contact_123"
        message_id = "msg_123"

        # Track engagement
        await orchestrator.track_engagement(
            contact_id=contact_id,
            channel=Channel.EMAIL,
            action="opened",
            message_id=message_id,
            metadata={"time_spent": 45}
        )

        # Verify tracking
        assert contact_id in orchestrator._engagement_history
        engagement_events = orchestrator._engagement_history[contact_id]
        assert len(engagement_events) == 1
        assert engagement_events[0]["action"] == "opened"
        assert engagement_events[0]["channel"] == "email"

    @pytest.mark.asyncio
    async def test_channel_failover(self, orchestrator, sample_message):
        """Test channel failover functionality."""
        # Mock primary channel unavailable
        orchestrator.check_channel_availability = AsyncMock(side_effect=[False, True])  # First fails, second succeeds
        orchestrator._send_via_channel = AsyncMock(return_value={"success": True})

        # Mock other methods
        orchestrator._get_contact_location = AsyncMock(return_value="loc_123")
        orchestrator._check_rate_limit = AsyncMock(return_value=True)

        result = await orchestrator.send_message("contact_123", Channel.EMAIL, sample_message)

        # Should have attempted failover
        assert orchestrator._performance_metrics['channel_failovers'] >= 1


class TestEnhancedAdvancedWorkflowEngine:
    """Test suite for Enhanced Advanced Workflow Engine."""

    @pytest.fixture
    async def workflow_engine(self, tmp_path):
        """Create test workflow engine."""
        # Create test workflow templates
        templates = {
            "workflows": {
                "test_workflow": {
                    "name": "Test Workflow",
                    "description": "Simple test workflow",
                    "triggers": [
                        {
                            "type": "event_based",
                            "event": "contact.created",
                            "conditions": []
                        }
                    ],
                    "steps": [
                        {
                            "id": "welcome_step",
                            "name": "Welcome Message",
                            "type": "send_message",
                            "config": {
                                "channel_selection": "email_preferred",
                                "template_id": "welcome_template",
                                "subject": "Welcome!",
                                "content": "Welcome {first_name}!"
                            },
                            "delay_config": {"type": "fixed", "seconds": 0},
                            "branches": [],
                            "default_next_step_id": "complete"
                        },
                        {
                            "id": "complete",
                            "name": "Complete",
                            "type": "workflow_transition",
                            "config": {"status": "completed"}
                        }
                    ]
                }
            },
            "behavioral_triggers": {},
            "ab_tests": {},
            "global_settings": {
                "performance_targets": {
                    "workflow_execution_start_ms": 100
                }
            }
        }

        # Write to temporary file
        templates_file = tmp_path / "test_templates.yaml"
        with open(templates_file, 'w') as f:
            import yaml
            yaml.dump(templates, f)

        # Create engine with test templates
        engine = EnhancedAdvancedWorkflowEngine(
            workflow_templates_path=str(templates_file),
            cache_manager=AsyncMock(),
            behavioral_service=AsyncMock(),
            multichannel_orchestrator=AsyncMock(),
            webhook_processor=AsyncMock(),
            analytics_service=AsyncMock()
        )

        # Wait for templates to load
        await asyncio.sleep(0.1)

        return engine

    @pytest.fixture
    def sample_contact_data(self):
        """Create sample contact data."""
        return {
            "id": "contact_123",
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
            "phone": "+1234567890",
            "tags": ["First-Time Buyer"],
            "qualification_score": 0.6
        }

    @pytest.mark.asyncio
    async def test_workflow_start_performance(self, workflow_engine, sample_contact_data):
        """Test workflow start performance (<100ms target)."""
        # Mock dependencies
        workflow_engine._get_contact_data = AsyncMock(return_value=sample_contact_data)
        workflow_engine._validate_workflow_triggers = AsyncMock(return_value=True)
        workflow_engine._assign_ab_test_variants = AsyncMock()

        start_time = time.time()

        execution_id = await workflow_engine.start_workflow(
            workflow_id="test_workflow",
            contact_id="contact_123",
            trigger_event={"type": "contact.created"},
            variables={"source": "website"}
        )

        processing_time_ms = (time.time() - start_time) * 1000
        assert processing_time_ms < 100, f"Workflow start took {processing_time_ms}ms (target: <100ms)"

        # Verify execution created
        assert execution_id is not None
        assert execution_id in workflow_engine._active_executions

        execution = workflow_engine._active_executions[execution_id]
        assert execution.workflow_id == "test_workflow"
        assert execution.contact_id == "contact_123"
        assert execution.status == WorkflowStatus.RUNNING

    @pytest.mark.asyncio
    async def test_condition_evaluation_performance(self, workflow_engine):
        """Test condition evaluation performance (<50ms target)."""
        execution = WorkflowExecution(
            execution_id="test_exec",
            workflow_id="test_workflow",
            contact_id="contact_123",
            started_at=datetime.now(),
            contact_data={"qualification_score": 0.75, "tags": ["First-Time Buyer"]},
            variables={"email_opened": True}
        )

        condition = {
            "field": "qualification_score",
            "operator": "greater_than",
            "value": 0.5
        }

        start_time = time.time()

        result = await workflow_engine._evaluate_condition(condition, execution)

        processing_time_ms = (time.time() - start_time) * 1000
        assert processing_time_ms < 50, f"Condition evaluation took {processing_time_ms}ms (target: <50ms)"

        assert result is True

    @pytest.mark.asyncio
    async def test_workflow_execution_with_steps(self, workflow_engine):
        """Test complete workflow execution."""
        # Mock step handlers
        workflow_engine._handle_send_message = AsyncMock(return_value=True)
        workflow_engine._handle_workflow_transition = AsyncMock(return_value=True)

        # Create execution
        execution = WorkflowExecution(
            execution_id="test_exec",
            workflow_id="test_workflow",
            contact_id="contact_123",
            started_at=datetime.now(),
            status=WorkflowStatus.RUNNING,
            contact_data={"first_name": "Jane"},
            variables={}
        )

        workflow_engine._active_executions["test_exec"] = execution

        # Execute workflow
        await workflow_engine._execute_workflow(execution)

        # Verify execution completed
        assert execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
        assert len(execution.completed_steps) > 0
        assert execution.steps_executed > 0

    @pytest.mark.asyncio
    async def test_error_handling_and_retry(self, workflow_engine):
        """Test error handling and retry logic."""
        # Mock failing step handler
        workflow_engine._handle_send_message = AsyncMock(side_effect=[False, False, True])  # Fail twice, then succeed

        # Create step with retry config
        step = {
            "id": "test_step",
            "type": "send_message",
            "config": {},
            "retry_config": {"max_retries": 3, "delay_seconds": 0.01}  # Fast retry for testing
        }

        execution = WorkflowExecution(
            execution_id="test_exec",
            workflow_id="test_workflow",
            contact_id="contact_123",
            started_at=datetime.now()
        )

        result = await workflow_engine._execute_step(step, execution)

        # Should eventually succeed after retries
        assert result is True
        assert execution.retry_count == 2  # Two failures before success


class TestWebhookProcessorIntegration:
    """Test suite for webhook processor integration."""

    @pytest.fixture
    async def webhook_processor(self):
        """Create test webhook processor."""
        return EnhancedWebhookProcessor(
            storage_dir="test_data",
            redis_client=AsyncMock(),
            ghl_client=AsyncMock(),
            webhook_secret="test_secret"
        )

    @pytest.mark.asyncio
    async def test_webhook_to_workflow_trigger(self, webhook_processor):
        """Test webhook processing triggers workflow."""
        # Mock workflow engine
        with patch('ghl_real_estate_ai.services.enhanced_advanced_workflow_engine.get_enhanced_advanced_workflow_engine') as mock_get_engine:
            mock_engine = AsyncMock()
            mock_engine.start_workflow = AsyncMock(return_value="exec_123")
            mock_get_engine.return_value = mock_engine

            # Create webhook payload
            payload = {
                "contactId": "contact_123",
                "locationId": "loc_456",
                "type": "contact.created",
                "tags": ["First-Time Buyer"],
                "customFields": {"budget_range": 400000}
            }

            # Process webhook
            result = await webhook_processor.process_webhook(
                webhook_id="webhook_123",
                payload=payload,
                signature="valid_signature"
            )

            # Verify workflow was triggered
            assert mock_engine.start_workflow.called
            call_args = mock_engine.start_workflow.call_args
            assert call_args[1]["workflow_id"] == "first_time_buyer_nurture"
            assert call_args[1]["contact_id"] == "contact_123"


class TestIntegrationPerformance:
    """Integration performance tests."""

    @pytest.mark.asyncio
    async def test_end_to_end_automation_performance(self):
        """Test complete end-to-end automation performance."""
        # Create all components
        behavioral_service = BehavioralTriggerService()
        orchestrator = EnhancedMultichannelOrchestrator(ghl_client=AsyncMock())

        # Create minimal workflow engine
        with patch('pathlib.Path.exists', return_value=False):  # No template file
            workflow_engine = EnhancedAdvancedWorkflowEngine()

        # Test behavioral event -> trigger evaluation -> message sending flow
        contact_id = "perf_test_contact"

        start_time = time.time()

        # 1. Track behavior events
        for i in range(5):
            event = BehaviorEvent(
                event_id=f"event_{i}",
                contact_id=contact_id,
                behavior_type=BehaviorType.PROPERTY_VIEW,
                timestamp=datetime.now() - timedelta(minutes=i),
                engagement_value=0.7
            )
            await behavioral_service.track_behavior(contact_id, event)

        # 2. Evaluate triggers
        triggers = await behavioral_service.evaluate_triggers(contact_id)

        # 3. Send message (mocked)
        if triggers:
            orchestrator.check_channel_availability = AsyncMock(return_value=True)
            orchestrator._send_via_channel = AsyncMock(return_value={"success": True})
            orchestrator._get_contact_location = AsyncMock(return_value="loc_123")
            orchestrator._check_rate_limit = AsyncMock(return_value=True)

            template = MessageTemplate("test", Channel.SMS, content="Test message")
            message = Message("msg_1", contact_id, Channel.SMS, template, datetime.now())

            result = await orchestrator.send_message(contact_id, Channel.SMS, message)

        total_time_ms = (time.time() - start_time) * 1000

        # Total end-to-end should be under 500ms
        assert total_time_ms < 500, f"End-to-end automation took {total_time_ms}ms (target: <500ms)"

    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self):
        """Test concurrent workflow execution performance."""
        with patch('pathlib.Path.exists', return_value=False):
            workflow_engine = EnhancedAdvancedWorkflowEngine()

        # Mock a simple workflow
        workflow_engine._workflows = {
            "concurrent_test": {
                "name": "Concurrent Test",
                "triggers": [{"type": "event_based", "event": "test", "conditions": []}],
                "steps": [
                    {
                        "id": "step1",
                        "type": "send_message",
                        "config": {"content": "Test"},
                        "branches": [],
                        "default_next_step_id": None
                    }
                ]
            }
        }

        # Mock dependencies
        workflow_engine._get_contact_data = AsyncMock(return_value={"id": "test"})
        workflow_engine._validate_workflow_triggers = AsyncMock(return_value=True)
        workflow_engine._assign_ab_test_variants = AsyncMock()
        workflow_engine._handle_send_message = AsyncMock(return_value=True)

        # Start multiple workflows concurrently
        start_time = time.time()

        tasks = []
        for i in range(10):  # 10 concurrent workflows
            task = workflow_engine.start_workflow(
                workflow_id="concurrent_test",
                contact_id=f"contact_{i}"
            )
            tasks.append(task)

        # Wait for all to complete
        execution_ids = await asyncio.gather(*tasks)

        total_time_ms = (time.time() - start_time) * 1000

        # Should handle 10 concurrent workflows under 1 second
        assert total_time_ms < 1000, f"Concurrent workflow execution took {total_time_ms}ms (target: <1000ms)"
        assert len(execution_ids) == 10
        assert all(eid is not None for eid in execution_ids)


@pytest.mark.asyncio
async def test_system_resource_usage():
    """Test system resource usage under load."""
    import psutil
    import gc

    # Get initial memory usage
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    # Create services
    behavioral_service = BehavioralTriggerService()
    orchestrator = EnhancedMultichannelOrchestrator()

    # Generate load
    for i in range(100):
        contact_id = f"load_test_contact_{i}"

        # Track multiple events per contact
        for j in range(10):
            event = BehaviorEvent(
                event_id=f"event_{i}_{j}",
                contact_id=contact_id,
                behavior_type=BehaviorType.EMAIL_OPEN,
                timestamp=datetime.now(),
                engagement_value=0.5
            )
            await behavioral_service.track_behavior(contact_id, event)

    # Force garbage collection
    gc.collect()

    # Check final memory usage
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory

    # Memory increase should be reasonable (< 100MB for 1000 events)
    assert memory_increase < 100, f"Memory usage increased by {memory_increase}MB (target: <100MB)"

    print(f"Memory usage: {initial_memory:.2f}MB -> {final_memory:.2f}MB (+{memory_increase:.2f}MB)")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])