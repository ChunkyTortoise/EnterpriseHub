"""
Integration Tests for Smart Appointment Scheduling System.

Tests the complete end-to-end flow of Jorge's smart appointment scheduling:
- Webhook receives qualified lead
- Seller engine offers 2-3 time slots
- Lead selects a slot in follow-up flow (tested elsewhere)
- Fallback to manual scheduling when needed

Validates the 40% faster lead→appointment conversion target.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
import json

import pytest
import pytz

from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook
from ghl_real_estate_ai.api.schemas.ghl import (
    GHLWebhookEvent,
    GHLMessage,
    GHLContact,
    MessageType,
    MessageDirection,
    ActionType
)
from ghl_real_estate_ai.services.calendar_scheduler import AppointmentType, AUSTIN_TZ
from ghl_real_estate_ai.core.conversation_manager import AIResponse


@pytest.fixture
def qualified_lead_webhook_event():
    """Mock webhook event for qualified lead ready for appointment."""
    return GHLWebhookEvent(
        type="InboundMessage",
        contactId="contact_qualified_123",
        locationId="location_jorge_456",
        message=GHLMessage(
            type=MessageType.SMS,
            body="Yes, I'm pre-approved and ready to see homes in Austin. My budget is $450k and I need to move by next month.",
            direction=MessageDirection.INBOUND
        ),
        contact=GHLContact(
            id="contact_qualified_123",
            firstName="Sarah",
            lastName="Thompson",
            phone="+15129876543",
            email="sarah.thompson@example.com",
            tags=["Hit List", "Needs Qualifying"],
            customFields={}
        )
    )


@pytest.fixture
def unqualified_lead_webhook_event():
    """Mock webhook event for unqualified lead (low score)."""
    return GHLWebhookEvent(
        type="InboundMessage",
        contactId="contact_unqualified_789",
        locationId="location_jorge_456",
        message=GHLMessage(
            type=MessageType.SMS,
            body="Hi, just looking around",
            direction=MessageDirection.INBOUND
        ),
        contact=GHLContact(
            id="contact_unqualified_789",
            firstName="John",
            lastName="Browser",
            phone="+15123334444",
            email="john.browser@example.com",
            tags=["Hit List"],
            customFields={}
        )
    )


@pytest.fixture
def mock_conversation_manager():
    """Mock conversation manager for testing."""
    manager = AsyncMock()

    # Mock context
    manager.get_context.return_value = {
        "extracted_preferences": {},
        "conversation_history": [],
        "created_at": datetime.utcnow()
    }

    # Mock AI response for qualified lead
    manager.generate_response.return_value = AIResponse(
        message="That's great! I can see you're ready to start looking. Let me help you find the perfect home in Austin within your budget.",
        extracted_data={
            "budget": 450000,
            "location": ["Austin"],
            "timeline": "next month",
            "bedrooms": 3,
            "bathrooms": 2,
            "financing": "pre-approved",
            "motivation": "need to move"
        },
        lead_score=6  # Qualified for auto-booking
    )

    return manager


@pytest.fixture
def mock_ghl_client():
    """Mock GHL client for testing."""
    client = AsyncMock()

    # Mock calendar availability
    austin_time = datetime(2024, 1, 18, 14, 0, 0, tzinfo=AUSTIN_TZ)
    client.get_available_slots.return_value = [
        {
            "start_time": austin_time.isoformat(),
            "end_time": (austin_time + timedelta(minutes=60)).isoformat(),
            "available": True
        },
        {
            "start_time": (austin_time + timedelta(hours=2)).isoformat(),
            "end_time": (austin_time + timedelta(hours=3)).isoformat(),
            "available": True
        }
    ]

    # Mock appointment creation
    client.create_appointment.return_value = {
        "id": "apt_sarah_123456",
        "status": "confirmed",
        "startTime": austin_time.isoformat(),
        "contactId": "contact_qualified_123",
        "calendarId": "cal_jorge_456",
        "title": "Buyer Consultation - Sarah Thompson"
    }

    # Mock message sending
    client.send_message.return_value = {"messageId": "msg_123", "status": "sent"}

    # Mock action application
    client.apply_actions.return_value = [
        {"status": "success", "action": "add_tag"},
        {"status": "success", "action": "send_message"},
        {"status": "success", "action": "update_custom_field"}
    ]

    return client


@pytest.fixture
def mock_background_tasks():
    """Mock FastAPI background tasks."""
    tasks = Mock()
    tasks.add_task = Mock()
    return tasks


@pytest.fixture
def mock_request():
    """Mock FastAPI request object."""
    request = Mock()
    request.headers = {"x-webhook-signature": "valid_signature"}
    return request


class TestSmartAppointmentSchedulingIntegration:
    """Integration tests for complete appointment scheduling flow."""

    @pytest.mark.asyncio
    async def test_qualified_lead_auto_booking_success(
        self,
        qualified_lead_webhook_event,
        mock_background_tasks,
        mock_request
    ):
        """Test slot offer flow for qualified lead."""

        with patch('ghl_real_estate_ai.services.jorge.jorge_seller_engine.JorgeSellerEngine') as MockEngine:
            instance = MockEngine.return_value
            instance.process_seller_response = AsyncMock(return_value={
                "message": "I can get you on Jorge's calendar. Reply with 1, 2, or 3.\n1) Thursday, January 18 at 2:00 PM PT",
                "temperature": "hot",
                "questions_answered": 4,
                "actions": []
            })

            with patch('ghl_real_estate_ai.api.routes.webhook.conversation_manager', new=AsyncMock()) as mock_cm,                  patch('ghl_real_estate_ai.api.routes.webhook.tenant_service', new=AsyncMock()) as mock_ts:
                mock_cm.get_context = AsyncMock(return_value={"seller_preferences": {}, "conversation_history": []})
                mock_cm.update_context = AsyncMock()
                mock_cm.memory_service = AsyncMock()
                mock_cm.memory_service.save_context = AsyncMock()
                mock_ts.get_tenant_config = AsyncMock(return_value=None)

                with patch('ghl_real_estate_ai.api.routes.webhook.jorge_settings') as mock_jorge_settings:
                    mock_jorge_settings.JORGE_SELLER_MODE = True
                    mock_jorge_settings.JORGE_BUYER_MODE = False
                    mock_jorge_settings.JORGE_LEAD_MODE = False
                    mock_jorge_settings.BUYER_ACTIVATION_TAG = "Buyer-Lead"
                    mock_jorge_settings.LEAD_ACTIVATION_TAG = "Lead-Qualified"

                    response = await handle_ghl_webhook.__wrapped__(
                        request=mock_request,
                        event=qualified_lead_webhook_event,
                        background_tasks=mock_background_tasks
                    )

        # Verify response
        assert response.success is True
        assert "Reply with 1, 2, or 3" in response.message
        assert response.actions == []

    @pytest.mark.asyncio
    async def test_qualified_lead_no_availability_fallback(
        self,
        qualified_lead_webhook_event,
        mock_background_tasks,
        mock_request
    ):
        """Test fallback message when manual scheduling is required."""

        with patch('ghl_real_estate_ai.services.jorge.jorge_seller_engine.JorgeSellerEngine') as MockEngine:
            instance = MockEngine.return_value
            instance.process_seller_response = AsyncMock(return_value={
                "message": "I'd love to get you connected with Jorge! Let me check his calendar and get back to you with the best available times for your schedule.",
                "temperature": "hot",
                "questions_answered": 4,
                "actions": [{"type": "add_tag", "tag": "Needs-Manual-Scheduling"}]
            })

            with patch('ghl_real_estate_ai.api.routes.webhook.conversation_manager', new=AsyncMock()) as mock_cm,                  patch('ghl_real_estate_ai.api.routes.webhook.tenant_service', new=AsyncMock()) as mock_ts:
                mock_cm.get_context = AsyncMock(return_value={"seller_preferences": {}, "conversation_history": []})
                mock_cm.update_context = AsyncMock()
                mock_cm.memory_service = AsyncMock()
                mock_cm.memory_service.save_context = AsyncMock()
                mock_ts.get_tenant_config = AsyncMock(return_value=None)

                with patch('ghl_real_estate_ai.api.routes.webhook.jorge_settings') as mock_jorge_settings:
                    mock_jorge_settings.JORGE_SELLER_MODE = True
                    mock_jorge_settings.JORGE_BUYER_MODE = False
                    mock_jorge_settings.JORGE_LEAD_MODE = False
                    mock_jorge_settings.BUYER_ACTIVATION_TAG = "Buyer-Lead"
                    mock_jorge_settings.LEAD_ACTIVATION_TAG = "Lead-Qualified"

                    response = await handle_ghl_webhook.__wrapped__(
                        request=mock_request,
                        event=qualified_lead_webhook_event,
                        background_tasks=mock_background_tasks
                    )

        # Verify fallback response
        assert response.success is True
        assert "check his calendar" in response.message.lower()
        assert "get back to you" in response.message.lower()

        tag_actions = [action for action in response.actions if action.type == ActionType.ADD_TAG]
        tag_names = [action.tag for action in tag_actions if hasattr(action, 'tag')]
        assert "Needs-Manual-Scheduling" in tag_names

    @pytest.mark.asyncio
    async def test_unqualified_lead_no_booking_attempt(
        self,
        unqualified_lead_webhook_event,
        mock_background_tasks,
        mock_request
    ):
        """Test that unqualified leads don't trigger slot offers."""

        with patch('ghl_real_estate_ai.services.jorge.jorge_seller_engine.JorgeSellerEngine') as MockEngine:
            instance = MockEngine.return_value
            instance.process_seller_response = AsyncMock(return_value={
                "message": "Tell me a bit about your timeline and condition.",
                "temperature": "cold",
                "questions_answered": 0,
                "actions": []
            })

            with patch('ghl_real_estate_ai.api.routes.webhook.conversation_manager', new=AsyncMock()) as mock_cm,                  patch('ghl_real_estate_ai.api.routes.webhook.tenant_service', new=AsyncMock()) as mock_ts:
                mock_cm.get_context = AsyncMock(return_value={"seller_preferences": {}, "conversation_history": []})
                mock_cm.update_context = AsyncMock()
                mock_cm.memory_service = AsyncMock()
                mock_cm.memory_service.save_context = AsyncMock()
                mock_ts.get_tenant_config = AsyncMock(return_value=None)

                with patch('ghl_real_estate_ai.api.routes.webhook.jorge_settings') as mock_jorge_settings:
                    mock_jorge_settings.JORGE_SELLER_MODE = True
                    mock_jorge_settings.JORGE_BUYER_MODE = False
                    mock_jorge_settings.JORGE_LEAD_MODE = False
                    mock_jorge_settings.BUYER_ACTIVATION_TAG = "Buyer-Lead"
                    mock_jorge_settings.LEAD_ACTIVATION_TAG = "Lead-Qualified"

                    response = await handle_ghl_webhook.__wrapped__(
                        request=mock_request,
                        event=unqualified_lead_webhook_event,
                        background_tasks=mock_background_tasks
                    )

        # Verify no appointment booking attempted
        assert response.success is True
        assert "scheduled" not in response.message.lower()

        # Should not have appointment-related actions
        action_types = [action.type for action in response.actions]
        appointment_tags = [
            action.tag for action in response.actions
            if action.type == ActionType.ADD_TAG and hasattr(action, 'tag') and "Appointment" in str(action.tag)
        ]
        assert len(appointment_tags) == 0

    @pytest.mark.asyncio
    async def test_appointment_booking_disabled(
        self,
        qualified_lead_webhook_event,
        mock_background_tasks,
        mock_request
    ):
        """Test behavior when seller engine does not offer slots."""

        with patch('ghl_real_estate_ai.services.jorge.jorge_seller_engine.JorgeSellerEngine') as MockEngine:
            instance = MockEngine.return_value
            instance.process_seller_response = AsyncMock(return_value={
                "message": "Thanks, I can help. What's your timeline?",
                "temperature": "warm",
                "questions_answered": 2,
                "actions": []
            })

            with patch('ghl_real_estate_ai.api.routes.webhook.conversation_manager', new=AsyncMock()) as mock_cm,                  patch('ghl_real_estate_ai.api.routes.webhook.tenant_service', new=AsyncMock()) as mock_ts:
                mock_cm.get_context = AsyncMock(return_value={"seller_preferences": {}, "conversation_history": []})
                mock_cm.update_context = AsyncMock()
                mock_cm.memory_service = AsyncMock()
                mock_cm.memory_service.save_context = AsyncMock()
                mock_ts.get_tenant_config = AsyncMock(return_value=None)

                with patch('ghl_real_estate_ai.api.routes.webhook.jorge_settings') as mock_jorge_settings:
                    mock_jorge_settings.JORGE_SELLER_MODE = True
                    mock_jorge_settings.JORGE_BUYER_MODE = False
                    mock_jorge_settings.JORGE_LEAD_MODE = False
                    mock_jorge_settings.BUYER_ACTIVATION_TAG = "Buyer-Lead"
                    mock_jorge_settings.LEAD_ACTIVATION_TAG = "Lead-Qualified"

                    response = await handle_ghl_webhook.__wrapped__(
                        request=mock_request,
                        event=qualified_lead_webhook_event,
                        background_tasks=mock_background_tasks
                    )

        assert response.success is True
        assert "Reply with 1, 2, or 3" not in response.message

    @pytest.mark.asyncio
    async def test_calendar_scheduling_error_graceful_handling(
        self,
        qualified_lead_webhook_event,
        mock_background_tasks,
        mock_request
    ):
        """Test graceful handling when seller engine raises an exception."""

        with patch('ghl_real_estate_ai.services.jorge.jorge_seller_engine.JorgeSellerEngine') as MockEngine:
            instance = MockEngine.return_value
            instance.process_seller_response = AsyncMock(side_effect=Exception("Calendar API unavailable"))

            with patch('ghl_real_estate_ai.api.routes.webhook.conversation_manager', new=AsyncMock()) as mock_cm,                  patch('ghl_real_estate_ai.api.routes.webhook.tenant_service', new=AsyncMock()) as mock_ts:
                mock_cm.get_context = AsyncMock(return_value={"seller_preferences": {}, "conversation_history": []})
                mock_cm.update_context = AsyncMock()
                mock_cm.memory_service = AsyncMock()
                mock_cm.memory_service.save_context = AsyncMock()
                mock_ts.get_tenant_config = AsyncMock(return_value=None)

                with patch('ghl_real_estate_ai.api.routes.webhook.jorge_settings') as mock_jorge_settings:
                    mock_jorge_settings.JORGE_SELLER_MODE = True
                    mock_jorge_settings.JORGE_BUYER_MODE = False
                    mock_jorge_settings.JORGE_LEAD_MODE = False
                    mock_jorge_settings.BUYER_ACTIVATION_TAG = "Buyer-Lead"
                    mock_jorge_settings.LEAD_ACTIVATION_TAG = "Lead-Qualified"

                    response = await handle_ghl_webhook.__wrapped__(
                        request=mock_request,
                        event=qualified_lead_webhook_event,
                        background_tasks=mock_background_tasks
                    )

        assert response.success is True
        assert len(response.message) > 0

    @pytest.mark.asyncio
    async def test_appointment_type_detection_listing(
        self,
        mock_background_tasks,
        mock_request
    ):
        """Test listing-related messaging for seller appointments."""

        # Create webhook event for seller
        seller_event = GHLWebhookEvent(
            type="InboundMessage",
            contactId="contact_seller_456",
            locationId="location_jorge_456",
            message=GHLMessage(
                type=MessageType.SMS,
                body="I need to sell my house quickly. It's in excellent condition and ready to list.",
                direction=MessageDirection.INBOUND
            ),
            contact=GHLContact(
                id="contact_seller_456",
                firstName="Lisa",
                lastName="Seller",
                phone="+15125551111",
                email="lisa.seller@example.com",
                tags=["Hit List", "Needs Qualifying"],
                customFields={}
            )
        )

        with patch('ghl_real_estate_ai.services.jorge.jorge_seller_engine.JorgeSellerEngine') as MockEngine:
            instance = MockEngine.return_value
            instance.process_seller_response = AsyncMock(return_value={
                "message": "I've got time to discuss your listing strategy. Reply with 1, 2, or 3.",
                "temperature": "hot",
                "questions_answered": 4,
                "actions": []
            })

            with patch('ghl_real_estate_ai.api.routes.webhook.conversation_manager', new=AsyncMock()) as mock_cm,                  patch('ghl_real_estate_ai.api.routes.webhook.tenant_service', new=AsyncMock()) as mock_ts:
                mock_cm.get_context = AsyncMock(return_value={"seller_preferences": {}, "conversation_history": []})
                mock_cm.update_context = AsyncMock()
                mock_cm.memory_service = AsyncMock()
                mock_cm.memory_service.save_context = AsyncMock()
                mock_ts.get_tenant_config = AsyncMock(return_value=None)

                with patch('ghl_real_estate_ai.api.routes.webhook.jorge_settings') as mock_jorge_settings:
                    mock_jorge_settings.JORGE_SELLER_MODE = True
                    mock_jorge_settings.JORGE_BUYER_MODE = False
                    mock_jorge_settings.JORGE_LEAD_MODE = False
                    mock_jorge_settings.BUYER_ACTIVATION_TAG = "Buyer-Lead"
                    mock_jorge_settings.LEAD_ACTIVATION_TAG = "Lead-Qualified"

                    response = await handle_ghl_webhook.__wrapped__(
                        request=mock_request,
                        event=seller_event,
                        background_tasks=mock_background_tasks
                    )

        # Verify seller slot offer messaging
        assert response.success is True
        assert "Reply with 1, 2, or 3" in response.message

    def test_business_hours_validation(self):
        """Test that appointments are only offered during business hours."""
        from ghl_real_estate_ai.services.calendar_scheduler import CalendarScheduler

        scheduler = CalendarScheduler()

        # Test Monday 10 AM (should be valid)
        monday_10am = datetime(2024, 1, 15, 10, 0, 0, tzinfo=AUSTIN_TZ)
        assert scheduler._is_during_business_hours(monday_10am) is True

        # Test Monday 8 AM (should be invalid - too early)
        monday_8am = datetime(2024, 1, 15, 8, 0, 0, tzinfo=AUSTIN_TZ)
        assert scheduler._is_during_business_hours(monday_8am) is False

        # Test Saturday 2 PM (should be valid)
        saturday_2pm = datetime(2024, 1, 20, 14, 0, 0, tzinfo=AUSTIN_TZ)
        assert scheduler._is_during_business_hours(saturday_2pm) is True

        # Test Sunday 2 PM (should be invalid - closed)
        sunday_2pm = datetime(2024, 1, 21, 14, 0, 0, tzinfo=AUSTIN_TZ)
        assert scheduler._is_during_business_hours(sunday_2pm) is False

    def test_appointment_duration_mapping(self):
        """Test appointment duration mapping for different types."""
        from ghl_real_estate_ai.services.calendar_scheduler import AppointmentDuration

        # Test duration mappings match Jorge's business needs
        assert AppointmentDuration.BUYER_CONSULTATION.value == 60  # 1 hour
        assert AppointmentDuration.LISTING_APPOINTMENT.value == 90  # 1.5 hours
        assert AppointmentDuration.INVESTOR_MEETING.value == 45    # 45 minutes
        assert AppointmentDuration.PROPERTY_SHOWING.value == 30    # 30 minutes
        assert AppointmentDuration.FOLLOW_UP_CALL.value == 15      # 15 minutes

    @pytest.mark.asyncio
    async def test_timezone_handling_austin(self):
        """Test proper timezone handling for Jorge's Austin market."""
        from ghl_real_estate_ai.services.calendar_scheduler import TimeSlot, AppointmentType

        # Create UTC time
        utc_time = datetime(2024, 1, 17, 20, 0, 0, tzinfo=pytz.UTC)  # 8 PM UTC

        slot = TimeSlot(
            start_time=utc_time,
            end_time=utc_time + timedelta(minutes=60),
            duration_minutes=60,
            appointment_type=AppointmentType.BUYER_CONSULTATION
        )

        # Convert to Austin time
        austin_time = slot.to_austin_time()

        # UTC 20:00 should be Rancho (PT) 12:00
        assert austin_time.hour == 12
        assert austin_time.tzinfo.zone == "America/Los_Angeles"

        # Format for lead display
        formatted = slot.format_for_lead()
        assert "12:00 PM PT" in formatted
        assert "Wednesday, January 17" in formatted


@pytest.mark.asyncio
async def test_performance_40_percent_faster_target():
    """
    Test that validates the 40% faster lead→appointment conversion target.

    This test ensures the system can book appointments faster than manual processes.
    """
    from ghl_real_estate_ai.services.calendar_scheduler import CalendarScheduler
    import time

    # Mock GHL client with fast responses
    mock_ghl_client = AsyncMock()
    mock_ghl_client.get_available_slots.return_value = [
        {"start_time": "2024-01-18T14:00:00Z", "available": True}
    ]
    mock_ghl_client.create_appointment.return_value = {"id": "apt_123", "status": "confirmed"}

    scheduler = CalendarScheduler(ghl_client=mock_ghl_client)

    # Simulate qualified lead data
    contact_info = {
        "contact_id": "contact_123",
        "first_name": "Speed",
        "last_name": "Test",
        "phone": "+15125551234",
        "email": "speed@test.com"
    }

    extracted_data = {
        "budget": 400000,
        "location": ["Austin"],
        "timeline": "urgent",
        "bedrooms": 3,
        "financing": "pre-approved"
    }

    # Measure booking time
    start_time = time.time()

    booking_attempted, response_message, actions = await scheduler.handle_appointment_request(
        contact_id="contact_123",
        contact_info=contact_info,
        lead_score=6,  # Qualified
        extracted_data=extracted_data,
        message_content="I'm ready to buy"
    )

    end_time = time.time()
    booking_duration = end_time - start_time

    # Verify booking was attempted and fast
    assert booking_attempted is True
    assert booking_duration < 2.0  # Should complete in under 2 seconds

    # Manual process typically takes 5-10 minutes
    # Automated process should be under 30 seconds (much more than 40% faster)
    manual_process_time = 300  # 5 minutes
    automation_speedup = manual_process_time / booking_duration

    # Should be significantly faster than 40% improvement
    assert automation_speedup > 150  # Over 150x faster (way beyond 40% target)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
