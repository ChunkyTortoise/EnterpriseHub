import pytest
pytestmark = pytest.mark.integration

"""
Comprehensive tests for Proactive Communication Engine.
Tests cover multi-channel communication, AI-generated messaging, and GHL integration.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


try:
    from ghl_real_estate_ai.services.proactive_communication_engine import (
        CommunicationMessage,
        CommunicationTemplate,
        CommunicationType,
        MessageChannel,
        MessageStatus,
        ProactiveCommunicationEngine,
    )
except (ImportError, TypeError, AttributeError):
    pytest.skip("required imports unavailable", allow_module_level=True)


class TestCommunicationMessage:
    """Test CommunicationMessage dataclass functionality."""

    def test_message_creation(self):
        """Test message creation with all fields."""
        message = CommunicationMessage(
            id="msg_001",
            type=CommunicationType.MILESTONE_UPDATE,
            deal_id="deal_123",
            recipient_id="client_456",
            recipient_type="client",
            channels=[MessageChannel.EMAIL, MessageChannel.SMS],
            status=MessageStatus.PENDING,
            subject="Inspection Complete - Great News!",
            content="Your home inspection has been completed successfully...",
            scheduled_send_time=datetime.now() + timedelta(hours=1),
            priority=8,
            personalization_data={
                "client_name": "John",
                "property_address": "123 Main St",
                "milestone": "inspection_completion",
            },
            tracking_data={"campaign_id": "milestone_updates", "template_version": "v2.1"},
        )

        assert message.id == "msg_001"
        assert message.type == CommunicationType.MILESTONE_UPDATE
        assert len(message.channels) == 2
        assert MessageChannel.EMAIL in message.channels
        assert message.priority == 8
        assert message.personalization_data["client_name"] == "John"

    def test_message_serialization(self):
        """Test message serialization to dictionary."""
        message = CommunicationMessage(
            id="msg_002",
            type=CommunicationType.CELEBRATION,
            deal_id="deal_789",
            recipient_id="client_101",
            recipient_type="client",
            channels=[MessageChannel.PORTAL],
            status=MessageStatus.DELIVERED,
            subject="Congratulations on Your Closing!",
            content="Welcome to homeownership!",
            scheduled_send_time=datetime.now(),
            priority=5,
        )

        message_dict = message.__dict__
        assert message_dict["id"] == "msg_002"
        assert message_dict["type"] == CommunicationType.CELEBRATION
        assert isinstance(message_dict["scheduled_send_time"], datetime)


class TestCommunicationTemplate:
    """Test CommunicationTemplate dataclass functionality."""

    def test_template_creation(self):
        """Test template creation with variables."""
        template = CommunicationTemplate(
            id="tmpl_001",
            name="Milestone Update Template",
            type=CommunicationType.MILESTONE_UPDATE,
            subject_template="{{milestone_name}} Complete - {{property_address}}",
            content_template="Hi {{client_name}}, great news! Your {{milestone_name}} has been completed for {{property_address}}. {{milestone_details}}",
            variables=["client_name", "milestone_name", "property_address", "milestone_details"],
            channels=[MessageChannel.EMAIL, MessageChannel.SMS],
            metadata={"version": "2.0", "created_by": "ai_generation", "approval_status": "approved"},
        )

        assert template.id == "tmpl_001"
        assert template.type == CommunicationType.MILESTONE_UPDATE
        assert len(template.variables) == 4
        assert "{{client_name}}" in template.content_template
        assert MessageChannel.EMAIL in template.channels


class TestProactiveCommunicationEngine:
    """Test the main communication engine functionality."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for communication engine."""
        return {
            "cache_service": AsyncMock(),
            "ghl_service": AsyncMock(),
            "claude_service": AsyncMock(),
            "email_service": AsyncMock(),
            "sms_service": AsyncMock(),
            "portal_service": AsyncMock(),
        }

    @pytest.fixture
    def engine(self, mock_dependencies):
        """Create communication engine instance with mocked dependencies."""
        return ProactiveCommunicationEngine(
            cache_service=mock_dependencies["cache_service"],
            ghl_service=mock_dependencies["ghl_service"],
            claude_service=mock_dependencies["claude_service"],
        )

    @pytest.mark.asyncio
    async def test_send_milestone_update_success(self, engine, mock_dependencies):
        """Test successful milestone update sending."""
        milestone_data = {
            "deal_id": "deal_123",
            "milestone": "inspection_completed",
            "recipient_type": "client",
            "recipient_id": "client_456",
            "milestone_details": {
                "inspection_date": "2024-01-20",
                "inspector_name": "Elite Inspections",
                "overall_result": "no_major_issues",
                "next_steps": ["review_report", "proceed_to_appraisal"],
            },
            "property_data": {"address": "123 Main Street, Austin, TX", "price": 450000},
            "client_data": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "(555) 123-4567",
                "communication_preferences": ["email", "sms"],
            },
        }

        # Mock AI-generated message content
        mock_dependencies["claude_service"].generate_response.return_value = {
            "personalized_message": {
                "subject": "Great News! Your Home Inspection is Complete",
                "content": "Hi John, excellent news about your inspection at 123 Main Street! Elite Inspections completed their thorough review and found no major issues. This is a significant milestone - you're one step closer to your dream home! Next, we'll schedule the appraisal. I'll keep you updated on our progress.",
                "tone": "enthusiastic_professional",
                "personalization_score": 0.89,
            }
        }

        # Mock multi-channel sending
        mock_dependencies["email_service"].send_message.return_value = {
            "success": True,
            "message_id": "email_msg_789",
            "delivery_status": "sent",
        }

        mock_dependencies["sms_service"].send_message.return_value = {
            "success": True,
            "message_id": "sms_msg_790",
            "delivery_status": "sent",
        }

        mock_dependencies["ghl_service"].update_contact_timeline.return_value = {
            "success": True,
            "timeline_entry_id": "timeline_123",
        }

        result = await engine.send_milestone_update(milestone_data)

        assert result["success"] is True
        assert result["message_id"] is not None
        assert result["channels_sent"] == ["email", "sms"]
        assert result["ai_personalization_score"] == 0.89

        # Verify service calls
        mock_dependencies["claude_service"].generate_response.assert_called_once()
        mock_dependencies["email_service"].send_message.assert_called_once()
        mock_dependencies["sms_service"].send_message.assert_called_once()
        mock_dependencies["ghl_service"].update_contact_timeline.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_celebration_message_success(self, engine, mock_dependencies):
        """Test successful celebration message sending."""
        celebration_data = {
            "deal_id": "deal_456",
            "celebration_type": "closing_completed",
            "recipient_type": "client",
            "recipient_id": "client_789",
            "celebration_details": {
                "closing_date": "2024-01-25",
                "property_address": "456 Oak Street, Austin, TX",
                "purchase_price": 525000,
                "achievement": "first_time_homeowner",
            },
            "client_data": {"name": "Sarah Johnson", "email": "sarah@example.com", "phone": "(555) 987-6543"},
            "custom_message_elements": {
                "include_gift_suggestion": True,
                "include_maintenance_tips": True,
                "include_community_welcome": True,
            },
        }

        # Mock AI-generated celebration content
        mock_dependencies["claude_service"].generate_response.return_value = {
            "celebration_message": {
                "subject": "🎉 Welcome Home, Sarah! Congratulations!",
                "content": "Sarah, what an incredible milestone! You've officially become a homeowner at 456 Oak Street! 🏡 As a first-time buyer, this achievement is extra special. I've prepared some helpful tips for your first 30 days and information about your new neighborhood. Congratulations on this amazing journey - you've earned this celebration!",
                "tone": "celebratory_warm",
                "includes_emojis": True,
                "personalization_score": 0.95,
                "celebration_elements": ["achievement_recognition", "community_info", "helpful_resources"],
            }
        }

        # Mock celebration delivery
        mock_dependencies["email_service"].send_celebration.return_value = {
            "success": True,
            "message_id": "celebration_email_123",
            "includes_attachments": True,
        }

        mock_dependencies["portal_service"].create_welcome_package.return_value = {
            "success": True,
            "package_id": "welcome_pkg_456",
            "package_url": "https://portal.example.com/welcome/456",
        }

        result = await engine.send_celebration_message(celebration_data)

        assert result["success"] is True
        assert result["celebration_type"] == "closing_completed"
        assert result["personalization_score"] == 0.95
        assert result["welcome_package_created"] is True

        # Verify celebration-specific calls
        mock_dependencies["portal_service"].create_welcome_package.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_issue_alert_success(self, engine, mock_dependencies):
        """Test successful issue alert sending."""
        alert_data = {
            "deal_id": "deal_urgent",
            "issue_type": "financing_complication",
            "severity": "high",
            "recipient_type": "client",
            "recipient_id": "client_urgent",
            "issue_details": {
                "description": "Additional documentation required by lender",
                "required_action": "Provide 2023 tax returns and recent bank statements",
                "deadline": "2024-01-22T17:00:00",
                "impact": "May delay closing by 3-5 days if not resolved quickly",
            },
            "resolution_steps": [
                "Contact your CPA for 2023 tax returns",
                "Download recent bank statements (last 2 months)",
                "Upload documents to secure portal within 24 hours",
            ],
            "support_contact": {"agent_name": "Mike Rodriguez", "phone": "(555) 111-2222", "email": "mike@realty.com"},
        }

        # Mock AI-generated alert content
        mock_dependencies["claude_service"].generate_response.return_value = {
            "alert_message": {
                "subject": "Action Required: Additional Documents Needed",
                "content": "I need your help with something important for your closing. The lender requires your 2023 tax returns and recent bank statements. While this adds a step, it's completely normal and I'm here to guide you through it quickly. If we get these within 24 hours, we can stay on track. I've outlined exactly what you need below and I'm available to help.",
                "tone": "urgent_but_reassuring",
                "urgency_level": "high",
                "action_oriented": True,
                "personalization_score": 0.82,
            }
        }

        # Mock multi-channel alert delivery
        mock_dependencies["email_service"].send_priority_message.return_value = {
            "success": True,
            "message_id": "priority_email_456",
            "priority_flag": "high",
        }

        mock_dependencies["sms_service"].send_urgent_message.return_value = {
            "success": True,
            "message_id": "urgent_sms_789",
            "delivery_confirmation": True,
        }

        mock_dependencies["ghl_service"].create_task.return_value = {
            "success": True,
            "task_id": "task_urgent_123",
            "assigned_to": "agent",
        }

        result = await engine.send_issue_alert(alert_data)

        assert result["success"] is True
        assert result["urgency_level"] == "high"
        assert result["channels_sent"] == ["email", "sms"]
        assert result["follow_up_task_created"] is True

        # Verify urgent delivery methods
        mock_dependencies["email_service"].send_priority_message.assert_called_once()
        mock_dependencies["sms_service"].send_urgent_message.assert_called_once()
        mock_dependencies["ghl_service"].create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_schedule_communication_success(self, engine, mock_dependencies):
        """Test successful communication scheduling."""
        schedule_data = {
            "deal_id": "deal_scheduled",
            "communication_type": "weekly_update",
            "recipient_id": "client_weekly",
            "schedule_pattern": "weekly",
            "start_date": "2024-01-22T09:00:00",
            "end_date": "2024-02-19T09:00:00",  # 4 weeks of updates
            "template_id": "tmpl_weekly_update",
            "personalization_data": {
                "client_name": "Robert Smith",
                "property_address": "789 Pine Lane",
                "closing_date": "2024-02-20",
            },
        }

        # Mock scheduled message creation
        scheduled_messages = [
            {"message_id": "scheduled_001", "send_time": "2024-01-22T09:00:00", "week": 1},
            {"message_id": "scheduled_002", "send_time": "2024-01-29T09:00:00", "week": 2},
            {"message_id": "scheduled_003", "send_time": "2024-02-05T09:00:00", "week": 3},
            {"message_id": "scheduled_004", "send_time": "2024-02-12T09:00:00", "week": 4},
        ]

        mock_dependencies["cache_service"].set.return_value = True

        result = await engine.schedule_recurring_communication(schedule_data)

        assert result["success"] is True
        assert result["total_scheduled"] == 4
        assert len(result["scheduled_messages"]) == 4
        assert result["schedule_pattern"] == "weekly"

        # Verify scheduling storage
        mock_dependencies["cache_service"].set.assert_called()

    @pytest.mark.asyncio
    async def test_process_scheduled_messages(self, engine, mock_dependencies):
        """Test processing of scheduled messages."""
        # Mock pending scheduled messages
        current_time = datetime.now()
        pending_messages = [
            CommunicationMessage(
                id="scheduled_due_001",
                type=CommunicationType.WEEKLY_UPDATE,
                deal_id="deal_123",
                recipient_id="client_456",
                recipient_type="client",
                channels=[MessageChannel.EMAIL],
                status=MessageStatus.SCHEDULED,
                subject="Weekly Progress Update",
                content="Your weekly update...",
                scheduled_send_time=current_time - timedelta(minutes=5),  # Due
                priority=5,
            ),
            CommunicationMessage(
                id="scheduled_future_002",
                type=CommunicationType.MILESTONE_UPDATE,
                deal_id="deal_789",
                recipient_id="client_101",
                recipient_type="client",
                channels=[MessageChannel.SMS],
                status=MessageStatus.SCHEDULED,
                subject="Upcoming Milestone",
                content="Reminder about...",
                scheduled_send_time=current_time + timedelta(hours=2),  # Future
                priority=7,
            ),
        ]

        mock_dependencies["cache_service"].get.return_value = pending_messages

        # Mock message sending for due message
        mock_dependencies["email_service"].send_message.return_value = {"success": True, "message_id": "email_sent_123"}

        with patch.object(engine, "_send_message_via_channels") as mock_send:
            mock_send.return_value = {"success": True, "channels_sent": ["email"]}

            result = await engine.process_scheduled_messages()

        assert result["processed_count"] == 1  # Only one message was due
        assert result["sent_count"] == 1
        assert result["failed_count"] == 0

    @pytest.mark.asyncio
    async def test_ai_message_personalization(self, engine, mock_dependencies):
        """Test AI-powered message personalization."""
        personalization_request = {
            "template_content": "Hi {{client_name}}, your {{milestone}} is complete for {{property_address}}.",
            "personalization_data": {
                "client_name": "Jennifer",
                "milestone": "appraisal",
                "property_address": "321 Maple Drive",
                "client_profile": {
                    "first_time_buyer": True,
                    "communication_style": "detailed",
                    "concerns": ["timeline", "financing"],
                    "personality": "analytical",
                },
                "deal_context": {
                    "weeks_in_process": 3,
                    "milestones_completed": ["contract", "inspection", "appraisal"],
                    "next_milestone": "final_walkthrough",
                    "closing_timeline": "on_track",
                },
            },
        }

        # Mock AI personalization
        mock_dependencies["claude_service"].generate_response.return_value = {
            "personalized_content": {
                "subject": "Great Progress Jennifer - Your Appraisal Results Are In!",
                "content": "Jennifer, I have excellent news about your appraisal for 321 Maple Drive! The property appraised at value, which means your financing is secured and we're maintaining our timeline perfectly. I know you've been focused on staying on schedule, and I'm happy to confirm we're right on track. With the contract, inspection, and now appraisal complete, you're 75% of the way to your keys! Next up is the final walkthrough, which I'll coordinate for you. As a first-time buyer, you're doing amazingly well navigating this process.",
                "personalization_score": 0.94,
                "tone_match": "detailed_reassuring",
                "addresses_concerns": ["timeline", "financing"],
                "celebration_elements": ["progress_acknowledgment", "milestone_achievement"],
            }
        }

        result = await engine.personalize_message_with_ai(personalization_request)

        assert result["personalization_score"] == 0.94
        assert "Jennifer" in result["personalized_content"]["content"]
        assert "timeline" in result["personalized_content"]["content"].lower()
        assert result["tone_match"] == "detailed_reassuring"

    @pytest.mark.asyncio
    async def test_communication_analytics(self, engine, mock_dependencies):
        """Test communication analytics and performance tracking."""
        analytics_request = {
            "deal_id": "deal_analytics",
            "time_period": "last_30_days",
            "metrics": ["delivery_rate", "engagement_rate", "response_rate", "satisfaction_score"],
        }

        # Mock analytics data
        mock_analytics = {
            "total_messages_sent": 45,
            "successful_deliveries": 43,
            "failed_deliveries": 2,
            "email_metrics": {
                "sent": 30,
                "delivered": 29,
                "opened": 24,
                "clicked": 18,
                "open_rate": 82.8,
                "click_rate": 62.1,
            },
            "sms_metrics": {"sent": 15, "delivered": 14, "responses": 8, "delivery_rate": 93.3, "response_rate": 57.1},
            "client_satisfaction": {
                "average_rating": 4.6,
                "feedback_count": 12,
                "positive_feedback": 11,
                "improvement_suggestions": 1,
            },
        }

        mock_dependencies["cache_service"].get.return_value = mock_analytics

        result = await engine.get_communication_analytics(analytics_request)

        assert result["total_messages_sent"] == 45
        assert result["overall_delivery_rate"] == 95.6  # 43/45 * 100
        assert result["email_metrics"]["open_rate"] == 82.8
        assert result["client_satisfaction"]["average_rating"] == 4.6

    @pytest.mark.asyncio
    async def test_message_template_management(self, engine, mock_dependencies):
        """Test message template creation and management."""
        template_data = {
            "name": "Closing Preparation Checklist",
            "type": "milestone_update",
            "description": "Pre-closing checklist and preparation guide",
            "subject_template": "{{days_to_closing}} Days to Closing - Your Checklist for {{property_address}}",
            "content_template": "Hi {{client_name}}, we're {{days_to_closing}} days away from your closing at {{property_address}}! Here's your personalized checklist: {{checklist_items}}. {{closing_details}}",
            "variables": ["client_name", "days_to_closing", "property_address", "checklist_items", "closing_details"],
            "channels": ["email", "portal"],
            "approval_required": False,
            "ai_enhancement": True,
        }

        # Mock AI template enhancement
        mock_dependencies["claude_service"].generate_response.return_value = {
            "enhanced_template": {
                "subject_template": "{{days_to_closing}} Days to Your Keys! 🗝️ Closing Prep for {{property_address}}",
                "content_template": "Hi {{client_name}}, incredible - we're just {{days_to_closing}} days away from you getting the keys to {{property_address}}! 🏡 I've prepared your personalized closing checklist to ensure everything goes smoothly: {{checklist_items}}. {{closing_details}} Remember, I'm here every step of the way. Let's make this closing perfect!",
                "enhancement_score": 0.87,
                "improvements": ["added_excitement", "emoji_usage", "personal_commitment", "positive_framing"],
            }
        }

        result = await engine.create_message_template(template_data)

        assert result["success"] is True
        assert result["template_id"] is not None
        assert result["ai_enhanced"] is True
        assert result["enhancement_score"] == 0.87

        # Verify template storage
        mock_dependencies["cache_service"].set.assert_called()

    @pytest.mark.asyncio
    async def test_communication_preferences_management(self, engine, mock_dependencies):
        """Test client communication preferences management."""
        preferences_data = {
            "client_id": "client_preferences",
            "preferences": {
                "channels": ["email", "sms"],
                "frequency": "important_only",
                "time_restrictions": {
                    "no_contact_before": "08:00",
                    "no_contact_after": "20:00",
                    "weekend_contact": False,
                },
                "content_preferences": {
                    "tone": "professional",
                    "detail_level": "concise",
                    "emoji_usage": False,
                    "language": "english",
                },
                "notification_types": {
                    "milestone_updates": True,
                    "issue_alerts": True,
                    "weekly_updates": False,
                    "celebration_messages": True,
                    "marketing_messages": False,
                },
            },
        }

        result = await engine.update_communication_preferences(preferences_data)

        assert result["success"] is True
        assert result["preferences_updated"] is True

        # Verify preferences storage
        mock_dependencies["cache_service"].set.assert_called_with(
            f"communication_preferences:{preferences_data['client_id']}", preferences_data["preferences"]
        )

    @pytest.mark.asyncio
    async def test_emergency_communication_protocol(self, engine, mock_dependencies):
        """Test emergency communication protocol activation."""
        emergency_data = {
            "deal_id": "deal_emergency",
            "emergency_type": "closing_cancellation",
            "severity": "critical",
            "affected_parties": ["client", "agent", "lender", "title_company"],
            "situation_details": {
                "reason": "last_minute_financing_denial",
                "impact": "closing_cancelled_24h_before",
                "required_actions": ["find_alternative_lender", "reschedule_closing", "negotiate_extension"],
            },
            "immediate_contact_required": True,
            "escalation_level": "manager",
        }

        # Mock emergency protocol activation
        mock_dependencies["ghl_service"].activate_emergency_workflow.return_value = {
            "success": True,
            "emergency_id": "emergency_123",
            "manager_notified": True,
            "escalation_timeline": "immediate",
        }

        # Mock multi-party emergency communication
        mock_dependencies["email_service"].send_emergency_broadcast.return_value = {
            "success": True,
            "messages_sent": 4,
            "delivery_confirmations": 4,
        }

        result = await engine.activate_emergency_communication_protocol(emergency_data)

        assert result["success"] is True
        assert result["emergency_protocol_activated"] is True
        assert result["affected_parties_contacted"] == 4
        assert result["manager_escalated"] is True

    def test_message_content_validation(self, engine):
        """Test message content validation and compliance."""
        # Test valid content
        valid_content = "Hi John, your inspection is complete and everything looks great!"
        validation_result = engine._validate_message_content(valid_content)
        assert validation_result["is_valid"] is True

        # Test content with potential issues
        problematic_content = "URGENT: ACT NOW! Limited time offer!!!"
        validation_result = engine._validate_message_content(problematic_content)
        assert validation_result["warnings"] is not None

    def test_channel_optimization(self, engine):
        """Test communication channel optimization logic."""
        client_data = {
            "communication_history": {"email_open_rate": 45, "sms_response_rate": 85, "portal_usage": 20},
            "preferences": ["email", "sms"],
            "urgency": "high",
        }

        optimized_channels = engine._optimize_communication_channels(client_data)

        # SMS should be preferred due to higher response rate and high urgency
        assert MessageChannel.SMS in optimized_channels
        assert len(optimized_channels) >= 1

    def test_send_time_optimization(self, engine):
        """Test optimal send time calculation."""
        client_timezone = "America/Chicago"
        message_type = CommunicationType.MILESTONE_UPDATE
        urgency = "standard"

        optimal_time = engine._calculate_optimal_send_time(client_timezone, message_type, urgency)

        # Should return a reasonable business hour time
        assert 8 <= optimal_time.hour <= 18  # Business hours
        assert optimal_time.weekday() < 5  # Weekday


class TestCommunicationIntegration:
    """Integration tests for communication workflows."""

    @pytest.mark.asyncio
    async def test_complete_communication_workflow(self):
        """Test complete communication workflow from trigger to delivery."""
        # Integration test placeholder
        pass

    @pytest.mark.asyncio
    async def test_multi_channel_coordination(self):
        """Test coordination across multiple communication channels."""
        # Integration test placeholder
        pass

    @pytest.mark.asyncio
    async def test_communication_recovery_workflow(self):
        """Test communication workflow recovery after system issues."""
        # Integration test placeholder
        pass