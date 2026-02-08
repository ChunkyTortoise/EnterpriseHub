"""
Tests for Multichannel Communication Engine
Comprehensive test suite for unified communication platform
"""

import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio

# Import the service under test
try:
    from ghl_real_estate_ai.services.multichannel_communication_engine import (
        AutomationRule,
        CommunicationContact,
        Conversation,
        Message,
        MultichannelCommunicationEngine,
    )
except ImportError as e:
    # Skip tests if dependencies not available
    pytest.skip(f"Skipping tests due to missing dependencies: {e}", allow_module_level=True)


class TestMultichannelCommunicationEngine:
    """Test suite for Multichannel Communication Engine"""

    @pytest_asyncio.fixture
    async def engine(self):
        """Create engine instance for testing"""
        with patch("ghl_real_estate_ai.services.multichannel_communication_engine.CacheService"):
            with patch("ghl_real_estate_ai.services.multichannel_communication_engine.ClaudeClient"):
                engine = MultichannelCommunicationEngine()
                yield engine

    @pytest.fixture
    def sample_contact(self):
        """Sample contact for testing"""
        return CommunicationContact(
            id="contact_123",
            name="John Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            preferred_channels=["email", "sms"],
            timezone="America/New_York",
            tags=["lead", "high_priority"],
            custom_fields={"lead_score": 85, "property_interest": "luxury"},
        )

    @pytest.fixture
    def sample_message(self):
        """Sample message for testing"""
        return Message(
            id="msg_123",
            conversation_id="conv_123",
            sender_id="agent_456",
            recipient_id="contact_123",
            channel="email",
            content="Thank you for your interest in our luxury properties.",
            message_type="text",
            status="sent",
            sent_at=datetime.now(),
            metadata={"campaign_id": "camp_789"},
        )

    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """Test engine initializes correctly"""
        assert engine is not None
        assert hasattr(engine, "cache_service")
        assert hasattr(engine, "claude_client")
        assert hasattr(engine, "providers")
        assert hasattr(engine, "performance_metrics")

    @pytest.mark.asyncio
    async def test_send_message(self, engine, sample_contact, sample_message):
        """Test sending message through multiple channels"""
        # Mock providers
        engine.providers = {"email": Mock(), "sms": Mock(), "whatsapp": Mock()}
        engine.providers["email"].send_message = AsyncMock(return_value={"status": "sent", "message_id": "email_123"})

        # Mock cache service
        engine.cache_service.get = AsyncMock(return_value=None)
        engine.cache_service.set = AsyncMock()

        result = await engine.send_message(
            contact=sample_contact, content="Test message", channel="email", message_type="promotional"
        )

        assert result["status"] == "sent"
        assert "message_id" in result

        # Verify provider was called
        engine.providers["email"].send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_conversation(self, engine, sample_contact):
        """Test conversation creation and management"""
        # Mock cache service
        engine.cache_service.get = AsyncMock(return_value=None)
        engine.cache_service.set = AsyncMock()

        conversation = await engine.create_conversation(
            participants=[sample_contact.id, "agent_456"], subject="Property Inquiry", channel="email"
        )

        assert isinstance(conversation, Conversation)
        assert conversation.subject == "Property Inquiry"
        assert conversation.channel == "email"
        assert sample_contact.id in conversation.participants
        assert "agent_456" in conversation.participants
        assert isinstance(conversation.created_at, datetime)

    @pytest.mark.asyncio
    async def test_personalize_message_content(self, engine, sample_contact):
        """Test AI-powered message personalization"""
        # Mock Claude client for personalization
        engine.claude_client.generate = AsyncMock(
            return_value=json.dumps(
                {
                    "personalized_content": "Dear John, based on your interest in luxury properties...",
                    "personalization_elements": ["name", "property_interest"],
                    "tone": "professional",
                    "optimization_score": 0.89,
                }
            )
        )

        template = "Dear {{name}}, based on your interest in {{property_interest}} properties..."

        personalized = await engine.personalize_message_content(
            template=template, contact=sample_contact, context={"recent_activity": "viewed luxury listings"}
        )

        assert "personalized_content" in personalized
        assert "John" in personalized["personalized_content"]
        assert "luxury" in personalized["personalized_content"]
        assert personalized["optimization_score"] > 0.8

    @pytest.mark.asyncio
    async def test_schedule_campaign(self, engine):
        """Test campaign scheduling and automation"""
        # Mock cache service
        engine.cache_service.set = AsyncMock()

        campaign_config = {
            "name": "Q1 Follow-up Campaign",
            "target_audience": {"tags": ["lead"], "lead_score_min": 70},
            "messages": [
                {"delay_hours": 0, "template": "welcome_message", "channel": "email"},
                {"delay_hours": 24, "template": "follow_up", "channel": "sms"},
            ],
            "schedule": {"start_date": "2024-03-01", "time_zone": "America/New_York"},
        }

        campaign_id = await engine.schedule_campaign(campaign_config)

        assert campaign_id is not None
        assert isinstance(campaign_id, str)

        # Verify campaign was cached
        engine.cache_service.set.assert_called()

    @pytest.mark.asyncio
    async def test_create_automation_rule(self, engine):
        """Test automation rule creation and processing"""
        automation_rule = AutomationRule(
            name="High Score Lead Follow-up",
            description="Automatically follow up with high-scoring leads",
            trigger_conditions={"event_type": "lead_scored", "score_threshold": 85},
            actions=[
                {"type": "send_message", "template": "high_priority_followup", "channel": "email", "delay_minutes": 5}
            ],
            is_active=True,
        )

        # Mock cache service
        engine.cache_service.set = AsyncMock()

        rule_id = await engine.create_automation_rule(automation_rule)

        assert rule_id is not None
        assert isinstance(rule_id, str)

    @pytest.mark.asyncio
    async def test_process_automation_rules(self, engine):
        """Test automation rule processing"""
        # Mock existing rules
        sample_rule = AutomationRule(
            name="Test Rule",
            trigger_conditions={"event_type": "lead_scored"},
            actions=[{"type": "send_message", "template": "test"}],
            is_active=True,
        )

        engine.cache_service.get = AsyncMock(return_value={"rule_123": sample_rule.__dict__})

        # Mock providers
        engine.providers = {"email": Mock()}
        engine.providers["email"].send_message = AsyncMock(return_value={"status": "sent"})

        event_data = {"event_type": "lead_scored", "contact_id": "contact_123", "score": 90}

        results = await engine.process_automation_rules(event_data)

        assert isinstance(results, list)
        # Results depend on rule matching and execution

    @pytest.mark.asyncio
    async def test_track_message_analytics(self, engine, sample_message):
        """Test message analytics tracking"""
        # Mock cache service
        engine.cache_service.get = AsyncMock(return_value={})
        engine.cache_service.set = AsyncMock()

        await engine.track_message_analytics(
            message=sample_message, event_type="delivered", metadata={"delivery_time": 2.5}
        )

        # Verify analytics were cached
        engine.cache_service.set.assert_called()

        # Test analytics retrieval
        analytics = await engine.get_communication_analytics(
            date_range={"start": "2024-01-01", "end": "2024-12-31"},
            channels=["email"],
            metrics=["delivery_rate", "open_rate", "click_rate"],
        )

        assert isinstance(analytics, dict)
        assert "summary" in analytics
        assert "metrics" in analytics

    @pytest.mark.asyncio
    async def test_optimize_channel_selection(self, engine, sample_contact):
        """Test AI-powered channel optimization"""
        # Mock Claude client for channel optimization
        engine.claude_client.generate = AsyncMock(
            return_value=json.dumps(
                {
                    "recommended_channel": "email",
                    "confidence_score": 0.92,
                    "reasoning": "High email engagement history and business hours timing",
                    "alternative_channels": ["sms"],
                    "optimal_timing": "10:00 AM EST",
                }
            )
        )

        # Mock historical data
        engine.cache_service.get = AsyncMock(
            return_value={
                "email": {"open_rate": 0.35, "click_rate": 0.08},
                "sms": {"delivery_rate": 0.98, "response_rate": 0.12},
            }
        )

        optimization = await engine.optimize_channel_selection(
            contact=sample_contact, message_type="promotional", urgency="normal"
        )

        assert "recommended_channel" in optimization
        assert "confidence_score" in optimization
        assert optimization["confidence_score"] > 0.8
        assert optimization["recommended_channel"] in ["email", "sms", "whatsapp"]

    @pytest.mark.asyncio
    async def test_sync_contact_data(self, engine, sample_contact):
        """Test contact data synchronization"""
        # Mock external CRM integration
        with patch("ghl_real_estate_ai.services.multichannel_communication_engine.httpx") as mock_httpx:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "contact": {"id": sample_contact.id, "updated_fields": ["phone", "tags"]}
            }
            mock_httpx.AsyncClient.return_value.__aenter__.return_value.post.return_value = mock_response

            # Mock cache service
            engine.cache_service.get = AsyncMock(return_value=sample_contact.__dict__)
            engine.cache_service.set = AsyncMock()

            sync_result = await engine.sync_contact_data(sample_contact.id)

            assert sync_result["status"] == "success"
            assert "updated_fields" in sync_result

    @pytest.mark.asyncio
    async def test_performance_metrics_tracking(self, engine):
        """Test performance metrics are tracked"""
        initial_messages = engine.performance_metrics.get("total_messages_sent", 0)

        # Mock provider and send message
        engine.providers = {"email": Mock()}
        engine.providers["email"].send_message = AsyncMock(return_value={"status": "sent"})
        engine.cache_service.get = AsyncMock(return_value=None)
        engine.cache_service.set = AsyncMock()

        sample_contact = CommunicationContact(id="test_contact", name="Test User", email="test@example.com")

        await engine.send_message(contact=sample_contact, content="Test message", channel="email")

        # Performance metrics should be updated
        assert engine.performance_metrics["total_messages_sent"] == initial_messages + 1
        assert "average_delivery_time" in engine.performance_metrics

    @pytest.mark.asyncio
    async def test_error_handling(self, engine):
        """Test error handling in communication operations"""
        # Mock provider to raise exception
        engine.providers = {"email": Mock()}
        engine.providers["email"].send_message = AsyncMock(side_effect=Exception("Provider error"))

        sample_contact = CommunicationContact(id="test_contact", email="test@example.com")

        # Should handle errors gracefully
        result = await engine.send_message(contact=sample_contact, content="Test message", channel="email")

        # Should return error result, not crash
        assert "error" in result or result.get("status") == "failed"

        # Error should be tracked
        assert "error_count" in engine.performance_metrics
        assert engine.performance_metrics["error_count"] > 0

    def test_communication_contact_model(self):
        """Test CommunicationContact data model"""
        contact = CommunicationContact(
            id="contact_123",
            name="John Doe",
            email="john@example.com",
            phone="+1234567890",
            preferred_channels=["email", "sms"],
            timezone="America/New_York",
            tags=["lead", "vip"],
            custom_fields={"score": 95},
        )

        assert contact.id == "contact_123"
        assert contact.name == "John Doe"
        assert contact.email == "john@example.com"
        assert contact.phone == "+1234567890"
        assert "email" in contact.preferred_channels
        assert contact.timezone == "America/New_York"
        assert "vip" in contact.tags
        assert contact.custom_fields["score"] == 95

    def test_message_model(self):
        """Test Message data model"""
        message = Message(
            id="msg_123",
            conversation_id="conv_123",
            sender_id="agent_456",
            recipient_id="contact_789",
            channel="email",
            content="Test message",
            message_type="promotional",
            status="sent",
            sent_at=datetime.now(),
            metadata={"campaign": "Q1_2024"},
        )

        assert message.id == "msg_123"
        assert message.conversation_id == "conv_123"
        assert message.sender_id == "agent_456"
        assert message.recipient_id == "contact_789"
        assert message.channel == "email"
        assert message.content == "Test message"
        assert message.message_type == "promotional"
        assert message.status == "sent"
        assert isinstance(message.sent_at, datetime)
        assert message.metadata["campaign"] == "Q1_2024"

    def test_automation_rule_model(self):
        """Test AutomationRule data model"""
        rule = AutomationRule(
            name="Follow-up Rule",
            description="Automatic follow-up for leads",
            trigger_conditions={"event": "lead_created"},
            actions=[{"type": "send_email", "template": "welcome"}],
            is_active=True,
            created_at=datetime.now(),
            priority=1,
        )

        assert rule.name == "Follow-up Rule"
        assert rule.description == "Automatic follow-up for leads"
        assert rule.trigger_conditions["event"] == "lead_created"
        assert len(rule.actions) == 1
        assert rule.actions[0]["type"] == "send_email"
        assert rule.is_active is True
        assert isinstance(rule.created_at, datetime)
        assert rule.priority == 1


# Integration test
@pytest.mark.asyncio
async def test_full_communication_pipeline():
    """Test complete communication pipeline integration"""
    try:
        with patch("ghl_real_estate_ai.services.multichannel_communication_engine.CacheService"):
            with patch("ghl_real_estate_ai.services.multichannel_communication_engine.ClaudeClient"):
                engine = MultichannelCommunicationEngine()

                # Mock dependencies
                engine.cache_service.get = AsyncMock(return_value=None)
                engine.cache_service.set = AsyncMock()
                engine.claude_client.generate = AsyncMock(
                    return_value=json.dumps(
                        {
                            "personalized_content": "Hello John, here is your personalized message",
                            "optimization_score": 0.9,
                        }
                    )
                )

                # Mock provider
                engine.providers = {"email": Mock()}
                engine.providers["email"].send_message = AsyncMock(
                    return_value={"status": "sent", "message_id": "email_123"}
                )

                # Create test contact
                contact = CommunicationContact(
                    id="test_contact", name="John Doe", email="john@example.com", preferred_channels=["email"]
                )

                # Send personalized message
                result = await engine.send_message(
                    contact=contact,
                    content="Hello {{name}}, welcome to our platform!",
                    channel="email",
                    personalize=True,
                )

                assert result["status"] == "sent"
                assert "message_id" in result

    except ImportError:
        pytest.skip("Dependencies not available for integration test")
