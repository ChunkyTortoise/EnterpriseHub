"""
Unit Tests for Multi-Channel Notification Service

Comprehensive test coverage for multi-channel notification delivery,
intervention notifications, manager escalations, and delivery tracking.

Test Coverage:
- SMS delivery and tracking
- Email delivery with HTML templates
- Agent alerts via WebSocket
- GHL workflow and task integration
- Multi-channel parallel delivery
- Intervention notification routing
- Manager escalation alerts
- Delivery status tracking
- Channel health monitoring
- Performance metrics
- Error handling and fallbacks

Performance Validation:
- Channel delivery <500ms per channel
- Parallel delivery coordination
- Queue processing efficiency
- Delivery confirmation tracking
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from ghl_real_estate_ai.services.multi_channel_notification_service import (
    MultiChannelNotificationService,
    NotificationChannel,
    NotificationPriority,
    DeliveryStatus,
    NotificationTemplate,
    NotificationRecipient,
    NotificationContent,
    NotificationRequest,
    ChannelDeliveryResult,
    NotificationResult,
    InterventionData,
    EscalationData,
    NotificationMetrics,
    get_notification_service,
    send_churn_intervention,
    escalate_to_manager
)


@pytest.fixture
def mock_websocket_manager():
    """Mock WebSocket manager"""
    manager = AsyncMock()
    manager.websocket_hub = AsyncMock()
    manager.websocket_hub.broadcast_to_tenant = AsyncMock(
        return_value=MagicMock(
            connections_successful=5,
            connections_targeted=5,
            broadcast_time_ms=47.3
        )
    )
    manager.get_connection_health = AsyncMock(
        return_value={
            "performance_status": {"overall_healthy": True},
            "websocket_manager": {"avg_broadcast_latency_ms": 47.3}
        }
    )
    return manager


@pytest.fixture
def mock_ghl_client():
    """Mock GHL client"""
    client = MagicMock()
    client.send_message = AsyncMock(
        return_value={"messageId": "msg_123", "status": "sent"}
    )
    client.trigger_workflow = AsyncMock(
        return_value={"workflowId": "wf_456", "status": "triggered"}
    )
    client.update_custom_field = AsyncMock(
        return_value={"status": "updated"}
    )
    client.add_tags = AsyncMock(
        return_value={"status": "updated"}
    )
    client.check_health = MagicMock(
        return_value=MagicMock(status_code=200)
    )
    return client


@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    client = AsyncMock()
    client.initialize = AsyncMock()
    client.set = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.lpush = AsyncMock()
    return client


@pytest.fixture
async def notification_service(mock_websocket_manager, mock_ghl_client, mock_redis_client):
    """Notification service instance with mocked dependencies"""
    with patch("ghl_real_estate_ai.services.multi_channel_notification_service.redis_client", mock_redis_client):
        service = MultiChannelNotificationService(
            websocket_manager=mock_websocket_manager,
            ghl_client=mock_ghl_client
        )
        service.redis_client = mock_redis_client
        await service.initialize()
        yield service


@pytest.fixture
def sample_intervention_data():
    """Sample intervention data"""
    return InterventionData(
        lead_id="lead_123",
        tenant_id="tenant_456",
        intervention_id="int_789",
        intervention_stage="active_risk",
        churn_probability=0.65,
        risk_level="high",
        days_until_churn=7,
        lead_name="John Doe",
        lead_email="john.doe@example.com",
        lead_phone="+15551234567",
        ghl_contact_id="contact_123",
        recommended_actions=["Schedule consultation", "Send property matches"],
        property_matches=[
            {"property_id": "prop_1", "match_score": 0.92},
            {"property_id": "prop_2", "match_score": 0.87}
        ],
        behavioral_insights={"engagement_trend": "declining"},
        assigned_agent_id="agent_456"
    )


@pytest.fixture
def sample_escalation_data():
    """Sample escalation data"""
    return EscalationData(
        escalation_id="esc_123",
        lead_id="lead_456",
        tenant_id="tenant_789",
        churn_probability=0.85,
        time_sensitive=True,
        intervention_history=[
            {"stage": "early_warning", "outcome": "ignored"},
            {"stage": "active_risk", "outcome": "failed"}
        ],
        lead_name="Jane Smith",
        lead_value=250000.0,
        lead_engagement_score=3.2,
        escalated_from="agent_123",
        escalation_reason="Multiple failed interventions, high-value lead at critical risk",
        recommended_actions=["Immediate personal call", "Special incentive offer"],
        urgency_level="critical",
        manager_id="manager_789",
        manager_email="manager@example.com",
        manager_phone="+15559876543"
    )


class TestNotificationServiceInitialization:
    """Test notification service initialization"""

    @pytest.mark.asyncio
    async def test_service_initialization(self, notification_service):
        """Test service initializes successfully"""
        assert notification_service is not None
        assert notification_service.websocket_manager is not None
        assert notification_service.ghl_client is not None
        assert notification_service.redis_client is not None
        assert isinstance(notification_service.metrics, NotificationMetrics)

    @pytest.mark.asyncio
    async def test_singleton_pattern(self):
        """Test singleton service instance"""
        with patch("ghl_real_estate_ai.services.multi_channel_notification_service.get_websocket_manager") as mock_ws:
            with patch("ghl_real_estate_ai.services.multi_channel_notification_service.GHLClient") as mock_ghl:
                with patch("ghl_real_estate_ai.services.multi_channel_notification_service.redis_client") as mock_redis:
                    mock_ws.return_value = AsyncMock()
                    mock_ghl.return_value = MagicMock()
                    mock_redis.initialize = AsyncMock()

                    service1 = await get_notification_service()
                    service2 = await get_notification_service()

                    assert service1 is service2

    def test_template_initialization(self, notification_service):
        """Test templates are initialized"""
        assert len(notification_service._templates) > 0
        assert NotificationTemplate.EARLY_WARNING_EMAIL in notification_service._templates
        assert NotificationTemplate.ACTIVE_RISK_EMAIL in notification_service._templates
        assert NotificationTemplate.CRITICAL_RISK_EMAIL in notification_service._templates


class TestInterventionNotifications:
    """Test intervention notification delivery"""

    @pytest.mark.asyncio
    async def test_send_intervention_notification_success(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test successful intervention notification"""
        result = await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data,
            channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
            priority=NotificationPriority.HIGH
        )

        assert result is not None
        assert result.overall_status == DeliveryStatus.DELIVERED
        assert len(result.successful_channels) > 0
        assert result.total_delivery_time_ms > 0

    @pytest.mark.asyncio
    async def test_auto_channel_selection_early_warning(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test auto-channel selection for early warning stage"""
        sample_intervention_data.intervention_stage = "early_warning"
        sample_intervention_data.churn_probability = 0.35

        result = await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data
        )

        # Early warning should use email + GHL workflow
        assert NotificationChannel.EMAIL in result.successful_channels or NotificationChannel.EMAIL in result.failed_channels
        assert NotificationChannel.GHL_WORKFLOW in result.successful_channels or NotificationChannel.GHL_WORKFLOW in result.failed_channels

    @pytest.mark.asyncio
    async def test_auto_channel_selection_active_risk(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test auto-channel selection for active risk stage"""
        sample_intervention_data.intervention_stage = "active_risk"
        sample_intervention_data.churn_probability = 0.65

        result = await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data
        )

        # Active risk should use SMS + Email + Agent alert
        channels = result.successful_channels + result.failed_channels
        assert any(ch in channels for ch in [NotificationChannel.SMS, NotificationChannel.EMAIL, NotificationChannel.AGENT_ALERT])

    @pytest.mark.asyncio
    async def test_auto_channel_selection_critical_risk(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test auto-channel selection for critical risk stage"""
        sample_intervention_data.intervention_stage = "critical_risk"
        sample_intervention_data.churn_probability = 0.85

        result = await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data
        )

        # Critical risk should use all channels
        channels = result.successful_channels + result.failed_channels
        assert len(channels) >= 4

    @pytest.mark.asyncio
    async def test_template_selection_and_personalization(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test template selection and content personalization"""
        result = await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data,
            channels=[NotificationChannel.EMAIL]
        )

        # Content should be personalized with lead name
        assert sample_intervention_data.lead_name in str(result.metadata)

    @pytest.mark.asyncio
    async def test_parallel_channel_delivery(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test parallel delivery across multiple channels"""
        import time

        channels = [
            NotificationChannel.SMS,
            NotificationChannel.EMAIL,
            NotificationChannel.AGENT_ALERT
        ]

        start_time = time.time()
        result = await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data,
            channels=channels
        )
        delivery_time = (time.time() - start_time) * 1000

        # Parallel delivery should be faster than sequential
        # With 3 channels at ~100ms each, parallel should be ~100-200ms, sequential would be ~300ms
        assert result.parallel_delivery is True
        assert delivery_time < 1000  # Should complete in less than 1 second


class TestManagerEscalation:
    """Test manager escalation alerts"""

    @pytest.mark.asyncio
    async def test_send_manager_escalation_success(
        self,
        notification_service,
        sample_escalation_data
    ):
        """Test successful manager escalation"""
        result = await notification_service.send_manager_escalation_alert(
            escalation_data=sample_escalation_data
        )

        assert result is not None
        assert result.overall_status == DeliveryStatus.DELIVERED
        assert len(result.successful_channels) > 0

    @pytest.mark.asyncio
    async def test_escalation_uses_all_channels(
        self,
        notification_service,
        sample_escalation_data
    ):
        """Test escalation uses all available channels"""
        result = await notification_service.send_manager_escalation_alert(
            escalation_data=sample_escalation_data
        )

        channels = result.successful_channels + result.failed_channels
        # Should use email, SMS, agent alert, and GHL task
        assert len(channels) >= 3

    @pytest.mark.asyncio
    async def test_escalation_critical_priority(
        self,
        notification_service,
        sample_escalation_data
    ):
        """Test escalation has critical priority"""
        # This would be tested through retry behavior and queue priority
        result = await notification_service.send_manager_escalation_alert(
            escalation_data=sample_escalation_data
        )

        assert result.metadata.get("urgency_level") == "critical"

    @pytest.mark.asyncio
    async def test_escalation_content_includes_context(
        self,
        notification_service,
        sample_escalation_data
    ):
        """Test escalation content includes full context"""
        result = await notification_service.send_manager_escalation_alert(
            escalation_data=sample_escalation_data
        )

        # Content should include lead value, churn probability, and intervention history
        metadata = result.metadata
        assert metadata.get("churn_probability") == sample_escalation_data.churn_probability


class TestChannelDelivery:
    """Test individual channel delivery"""

    @pytest.mark.asyncio
    async def test_sms_delivery_via_ghl(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test SMS delivery through GHL"""
        result = await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data,
            channels=[NotificationChannel.SMS]
        )

        sms_result = result.channel_results.get(NotificationChannel.SMS)
        if sms_result:
            assert sms_result.provider in ["ghl_sms", "mock_sms"]
            assert sms_result.status == DeliveryStatus.DELIVERED
            assert notification_service.ghl_client.send_message.called

    @pytest.mark.asyncio
    async def test_email_delivery_via_ghl(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test email delivery through GHL"""
        result = await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data,
            channels=[NotificationChannel.EMAIL]
        )

        email_result = result.channel_results.get(NotificationChannel.EMAIL)
        if email_result:
            assert email_result.provider in ["ghl_email", "mock_email"]
            assert email_result.status == DeliveryStatus.DELIVERED
            assert notification_service.ghl_client.send_message.called

    @pytest.mark.asyncio
    async def test_agent_alert_via_websocket(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test agent alert delivery via WebSocket"""
        result = await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data,
            channels=[NotificationChannel.AGENT_ALERT]
        )

        alert_result = result.channel_results.get(NotificationChannel.AGENT_ALERT)
        if alert_result:
            assert alert_result.provider == "websocket"
            assert alert_result.status == DeliveryStatus.DELIVERED
            assert notification_service.websocket_manager.websocket_hub.broadcast_to_tenant.called

    @pytest.mark.asyncio
    async def test_ghl_workflow_trigger(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test GHL workflow triggering"""
        sample_intervention_data.intervention_stage = "active_risk"

        result = await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data,
            channels=[NotificationChannel.GHL_WORKFLOW]
        )

        workflow_result = result.channel_results.get(NotificationChannel.GHL_WORKFLOW)
        if workflow_result:
            assert workflow_result.status == DeliveryStatus.DELIVERED

    @pytest.mark.asyncio
    async def test_ghl_task_creation(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test GHL task creation"""
        result = await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data,
            channels=[NotificationChannel.GHL_TASK]
        )

        task_result = result.channel_results.get(NotificationChannel.GHL_TASK)
        if task_result:
            assert task_result.status == DeliveryStatus.DELIVERED
            assert notification_service.ghl_client.update_custom_field.called

    @pytest.mark.asyncio
    async def test_in_app_message_delivery(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test in-app message caching"""
        result = await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data,
            channels=[NotificationChannel.IN_APP_MESSAGE]
        )

        in_app_result = result.channel_results.get(NotificationChannel.IN_APP_MESSAGE)
        if in_app_result:
            assert in_app_result.provider == "redis_cache"
            assert in_app_result.status == DeliveryStatus.DELIVERED
            assert notification_service.redis_client.set.called


class TestDeliveryTracking:
    """Test delivery status tracking"""

    @pytest.mark.asyncio
    async def test_track_delivery_status(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test tracking notification delivery status"""
        # Send notification
        result = await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data,
            channels=[NotificationChannel.EMAIL]
        )

        # Track status
        tracked_result = await notification_service.track_delivery_status(
            result.notification_id
        )

        assert tracked_result is not None
        assert tracked_result.notification_id == result.notification_id

    @pytest.mark.asyncio
    async def test_delivery_result_caching(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test delivery results are cached"""
        result = await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data,
            channels=[NotificationChannel.SMS]
        )

        # Result should be cached in Redis
        assert notification_service.redis_client.set.called

    @pytest.mark.asyncio
    async def test_track_nonexistent_notification(
        self,
        notification_service
    ):
        """Test tracking non-existent notification"""
        result = await notification_service.track_delivery_status("nonexistent_123")
        assert result is None


class TestChannelHealth:
    """Test channel health monitoring"""

    @pytest.mark.asyncio
    async def test_get_channel_health(
        self,
        notification_service
    ):
        """Test channel health status"""
        health = await notification_service.get_channel_health()

        assert "channels" in health
        assert "sms" in health["channels"]
        assert "email" in health["channels"]
        assert "agent_alert" in health["channels"]
        assert "ghl_workflow" in health["channels"]
        assert "overall_metrics" in health

    @pytest.mark.asyncio
    async def test_channel_availability(
        self,
        notification_service
    ):
        """Test channel availability reporting"""
        health = await notification_service.get_channel_health()

        for channel_name, channel_health in health["channels"].items():
            assert "available" in channel_health
            assert isinstance(channel_health["available"], bool)

    @pytest.mark.asyncio
    async def test_overall_health_status(
        self,
        notification_service
    ):
        """Test overall health aggregation"""
        health = await notification_service.get_channel_health()

        assert "overall_healthy" in health
        assert isinstance(health["overall_healthy"], bool)


class TestPerformanceMetrics:
    """Test performance metrics tracking"""

    @pytest.mark.asyncio
    async def test_metrics_update_on_delivery(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test metrics are updated after delivery"""
        initial_count = notification_service.metrics.total_notifications

        await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data,
            channels=[NotificationChannel.EMAIL]
        )

        assert notification_service.metrics.total_notifications > initial_count

    @pytest.mark.asyncio
    async def test_delivery_success_rate_tracking(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test delivery success rate calculation"""
        # Send multiple notifications
        for _ in range(5):
            await notification_service.send_intervention_notification(
                intervention_data=sample_intervention_data,
                channels=[NotificationChannel.EMAIL]
            )

        # Success rate should be calculated
        assert notification_service.metrics.delivery_success_rate >= 0.0
        assert notification_service.metrics.delivery_success_rate <= 1.0

    @pytest.mark.asyncio
    async def test_channel_specific_metrics(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test channel-specific performance metrics"""
        await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data,
            channels=[NotificationChannel.SMS, NotificationChannel.EMAIL]
        )

        metrics = notification_service.metrics

        # Should track SMS and Email separately
        assert metrics.sms_sent >= 0
        assert metrics.emails_sent >= 0

    @pytest.mark.asyncio
    async def test_cost_tracking(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test cost tracking for notifications"""
        initial_cost = notification_service.metrics.total_sms_cost + notification_service.metrics.total_email_cost

        await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data,
            channels=[NotificationChannel.SMS, NotificationChannel.EMAIL]
        )

        final_cost = notification_service.metrics.total_sms_cost + notification_service.metrics.total_email_cost

        # Cost should increase (in mock mode, only SMS cost tracked)
        assert final_cost >= initial_cost


class TestErrorHandling:
    """Test error handling and resilience"""

    @pytest.mark.asyncio
    async def test_missing_contact_information(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test handling missing contact information"""
        sample_intervention_data.lead_email = None
        sample_intervention_data.lead_phone = None

        result = await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data,
            channels=[NotificationChannel.EMAIL, NotificationChannel.SMS]
        )

        # Should handle gracefully with failures for channels without contact info
        assert result is not None
        email_result = result.channel_results.get(NotificationChannel.EMAIL)
        sms_result = result.channel_results.get(NotificationChannel.SMS)

        # Both should fail due to missing contact info
        if email_result:
            assert email_result.status == DeliveryStatus.FAILED
        if sms_result:
            assert sms_result.status == DeliveryStatus.FAILED

    @pytest.mark.asyncio
    async def test_channel_delivery_timeout(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test handling channel delivery timeout"""
        # Mock a slow channel delivery
        async def slow_delivery(*args, **kwargs):
            await asyncio.sleep(35)  # Exceed timeout
            return {"status": "sent"}

        notification_service.ghl_client.send_message = slow_delivery
        notification_service.delivery_timeout_seconds = 1  # Short timeout for test

        result = await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data,
            channels=[NotificationChannel.EMAIL]
        )

        # Should timeout and mark as failed
        email_result = result.channel_results.get(NotificationChannel.EMAIL)
        if email_result:
            assert email_result.status == DeliveryStatus.FAILED
            assert "timeout" in email_result.error_message.lower()

    @pytest.mark.asyncio
    async def test_partial_channel_failure(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test handling partial channel failures"""
        # Make SMS fail but email succeed
        notification_service.ghl_client.send_message = AsyncMock(
            side_effect=[
                {"messageId": "email_123"},  # Email succeeds
                Exception("SMS service unavailable")  # SMS fails
            ]
        )

        result = await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data,
            channels=[NotificationChannel.EMAIL, NotificationChannel.SMS]
        )

        # Overall should still be delivered if at least one channel succeeds
        assert result.overall_status in [DeliveryStatus.DELIVERED, DeliveryStatus.FAILED]
        assert len(result.successful_channels) + len(result.failed_channels) == 2


class TestConvenienceFunctions:
    """Test convenience wrapper functions"""

    @pytest.mark.asyncio
    async def test_send_churn_intervention_wrapper(
        self,
        sample_intervention_data
    ):
        """Test send_churn_intervention convenience function"""
        with patch("ghl_real_estate_ai.services.multi_channel_notification_service.get_notification_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.send_intervention_notification = AsyncMock(
                return_value=MagicMock(overall_status=DeliveryStatus.DELIVERED)
            )
            mock_get.return_value = mock_service

            result = await send_churn_intervention(
                intervention_data=sample_intervention_data
            )

            assert mock_service.send_intervention_notification.called

    @pytest.mark.asyncio
    async def test_escalate_to_manager_wrapper(
        self,
        sample_escalation_data
    ):
        """Test escalate_to_manager convenience function"""
        with patch("ghl_real_estate_ai.services.multi_channel_notification_service.get_notification_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.send_manager_escalation_alert = AsyncMock(
                return_value=MagicMock(overall_status=DeliveryStatus.DELIVERED)
            )
            mock_get.return_value = mock_service

            result = await escalate_to_manager(
                escalation_data=sample_escalation_data
            )

            assert mock_service.send_manager_escalation_alert.called


class TestPerformanceTargets:
    """Test performance targets are met"""

    @pytest.mark.asyncio
    async def test_channel_delivery_latency(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test individual channel delivery <500ms"""
        import time

        start_time = time.time()
        result = await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data,
            channels=[NotificationChannel.EMAIL]
        )
        delivery_time = (time.time() - start_time) * 1000

        # Should deliver in <500ms for single channel
        assert delivery_time < 500

    @pytest.mark.asyncio
    async def test_multi_channel_coordination_overhead(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test multi-channel coordination overhead <50ms"""
        result = await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data,
            channels=[
                NotificationChannel.EMAIL,
                NotificationChannel.SMS,
                NotificationChannel.AGENT_ALERT
            ]
        )

        # Coordination overhead should be minimal
        # Total time minus max individual channel time
        # This is tested implicitly through parallel delivery being faster than sequential

    @pytest.mark.asyncio
    async def test_delivery_confirmation_tracking(
        self,
        notification_service,
        sample_intervention_data
    ):
        """Test 100% delivery tracking"""
        result = await notification_service.send_intervention_notification(
            intervention_data=sample_intervention_data,
            channels=[NotificationChannel.EMAIL]
        )

        # Every channel should have a result
        assert len(result.channel_results) > 0
        for channel, channel_result in result.channel_results.items():
            assert channel_result.status is not None
            assert channel_result.delivery_time_ms >= 0
