"""
Tests for CalendarBookingService integration with Jorge Seller Bot.

Tests the HOT seller calendar workflow:
- HOT sellers (PCS >= 70) get calendar slot offerings
- WARM/COLD sellers do NOT get calendar offers
- Fallback when no calendar ID configured
- Fallback when no slots available
- Slot selection and booking flow
- Slot selection detection patterns
"""

import re
from datetime import datetime, timezone
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from ghl_real_estate_ai.agents.seller.response_generator import ResponseGenerator
from ghl_real_estate_ai.agents.seller.strategy_selector import StrategySelector
from ghl_real_estate_ai.services.jorge.calendar_booking_service import (
    FALLBACK_MESSAGE,
    CalendarBookingService,
)


# ==============================
# Fixtures
# ==============================


@pytest.fixture
def mock_ghl_client():
    """Mock GHL client with calendar methods."""
    client = AsyncMock()
    client.get_free_slots = AsyncMock(
        return_value=[
            {"start": "2026-02-16T10:00:00Z", "end": "2026-02-16T10:30:00Z"},
            {"start": "2026-02-16T14:00:00Z", "end": "2026-02-16T14:30:00Z"},
            {"start": "2026-02-17T09:00:00Z", "end": "2026-02-17T09:30:00Z"},
        ]
    )
    client.create_appointment = AsyncMock(
        return_value={"id": "appt_123", "status": "confirmed"}
    )
    return client


@pytest.fixture
def calendar_service(mock_ghl_client):
    """CalendarBookingService with mocked GHL client and calendar ID set."""
    with patch.dict("os.environ", {"JORGE_CALENDAR_ID": "cal_test_123"}):
        service = CalendarBookingService(mock_ghl_client)
    return service


@pytest.fixture
def calendar_service_no_cal_id(mock_ghl_client):
    """CalendarBookingService without calendar ID configured."""
    with patch.dict("os.environ", {}, clear=True):
        # Ensure JORGE_CALENDAR_ID is not set
        import os
        orig = os.environ.pop("JORGE_CALENDAR_ID", None)
        service = CalendarBookingService(mock_ghl_client)
        if orig is not None:
            os.environ["JORGE_CALENDAR_ID"] = orig
    return service


@pytest.fixture
def mock_event_publisher():
    """Mock event publisher."""
    publisher = Mock()
    publisher.publish_bot_status_update = AsyncMock()
    publisher.publish_conversation_update = AsyncMock()
    publisher.publish_jorge_qualification_progress = AsyncMock()
    return publisher


@pytest.fixture
def mock_claude():
    """Mock Claude assistant."""
    claude = AsyncMock()
    claude.analyze_with_context = AsyncMock(
        return_value={"content": "That's great news! Let me help you get started."}
    )
    return claude


@pytest.fixture
def mock_sentiment_service():
    """Mock sentiment analysis service."""
    service = AsyncMock()
    result = MagicMock()
    result.sentiment = MagicMock()
    result.sentiment.value = "positive"
    result.confidence = 0.9
    result.escalation_required = MagicMock()
    result.escalation_required.value = "none"
    service.analyze_message = AsyncMock(return_value=result)
    service.get_response_tone_adjustment = Mock(return_value={"tone": "enthusiastic", "pace": "normal"})
    return service


@pytest.fixture
def mock_ab_testing():
    """Mock A/B testing service."""
    ab = AsyncMock()
    ab.get_variant = AsyncMock(return_value="empathetic")
    return ab


@pytest.fixture
def response_generator_with_calendar(mock_claude, mock_event_publisher, mock_sentiment_service, mock_ab_testing, calendar_service):
    """ResponseGenerator with CalendarBookingService injected."""
    return ResponseGenerator(
        claude=mock_claude,
        event_publisher=mock_event_publisher,
        sentiment_service=mock_sentiment_service,
        ab_testing=mock_ab_testing,
        calendar_service=calendar_service,
    )


@pytest.fixture
def response_generator_no_calendar(mock_claude, mock_event_publisher, mock_sentiment_service, mock_ab_testing):
    """ResponseGenerator without CalendarBookingService."""
    return ResponseGenerator(
        claude=mock_claude,
        event_publisher=mock_event_publisher,
        sentiment_service=mock_sentiment_service,
        ab_testing=mock_ab_testing,
        calendar_service=None,
    )


def _make_seller_state(pcs: float = 50.0, adaptive_mode: str = "standard_qualification", **overrides) -> Dict:
    """Create a minimal seller state dict for testing."""
    frs_mock = MagicMock()
    frs_mock.total_score = 75.0
    frs_mock.classification = "Warm Lead"

    pcs_mock = MagicMock()
    pcs_mock.total_score = pcs

    intent_profile = MagicMock()
    intent_profile.frs = frs_mock
    intent_profile.pcs = pcs_mock

    state = {
        "lead_id": "seller_test_001",
        "lead_name": "Test Seller",
        "property_address": "123 Main St",
        "conversation_history": [
            {"role": "user", "content": "I want to sell my house"},
            {"role": "assistant", "content": "Great, I can help with that!"},
        ],
        "intent_profile": intent_profile,
        "current_tone": "ENTHUSIASTIC",
        "stall_detected": False,
        "detected_stall_type": None,
        "next_action": "respond",
        "response_content": "",
        "psychological_commitment": pcs,
        "is_qualified": True,
        "current_journey_stage": "qualification",
        "follow_up_count": 0,
        "last_action_timestamp": None,
        "tone_variant": "empathetic",
        "adaptive_mode": adaptive_mode,
        "adaptive_question_used": None,
        "adaptation_applied": False,
        "memory_updated": False,
        "seller_persona": {"persona_type": "Traditional", "confidence": 0.8},
    }
    state.update(overrides)
    return state


# ==============================
# Strategy Selector Tests
# ==============================


class TestStrategyCalendarFocused:
    """Test that HOT sellers trigger calendar_focused mode."""

    @pytest.mark.asyncio
    async def test_hot_seller_gets_calendar_focused(self, mock_event_publisher):
        """PCS >= 70 should set adaptive_mode to calendar_focused."""
        selector = StrategySelector(event_publisher=mock_event_publisher)
        state = _make_seller_state(pcs=75)

        result = await selector.select_strategy(state)

        assert result["current_tone"] == "ENTHUSIASTIC"
        assert result.get("adaptive_mode") == "calendar_focused"

    @pytest.mark.asyncio
    async def test_warm_seller_no_calendar_focused(self, mock_event_publisher):
        """PCS between 30-69 should NOT get calendar_focused."""
        selector = StrategySelector(event_publisher=mock_event_publisher)
        state = _make_seller_state(pcs=50)

        result = await selector.select_strategy(state)

        assert result["current_tone"] == "CONSULTATIVE"
        assert result.get("adaptive_mode") is None

    @pytest.mark.asyncio
    async def test_cold_seller_no_calendar_focused(self, mock_event_publisher):
        """PCS < 30 should NOT get calendar_focused."""
        selector = StrategySelector(event_publisher=mock_event_publisher)
        state = _make_seller_state(pcs=20)

        result = await selector.select_strategy(state)

        assert result["current_tone"] == "EDUCATIONAL"
        assert result.get("adaptive_mode") is None

    @pytest.mark.asyncio
    async def test_exactly_70_pcs_gets_calendar(self, mock_event_publisher):
        """PCS == 70 (boundary) should get calendar_focused."""
        selector = StrategySelector(event_publisher=mock_event_publisher)
        state = _make_seller_state(pcs=70)

        result = await selector.select_strategy(state)

        assert result["current_tone"] == "ENTHUSIASTIC"
        assert result.get("adaptive_mode") == "calendar_focused"


# ==============================
# Response Generator Calendar Tests
# ==============================


class TestResponseGeneratorCalendar:
    """Test calendar slot injection into responses."""

    @pytest.mark.asyncio
    async def test_calendar_slots_injected_for_hot_seller(self, response_generator_with_calendar):
        """Calendar-focused mode should append slot options to response."""
        state = _make_seller_state(pcs=80, adaptive_mode="calendar_focused")

        result = await response_generator_with_calendar.generate_jorge_response(state)

        content = result["response_content"]
        assert "Great news!" in content
        assert "1." in content
        assert "reply with the number" in content.lower()

    @pytest.mark.asyncio
    async def test_no_calendar_for_warm_seller(self, response_generator_with_calendar):
        """Non-calendar-focused mode should NOT inject calendar slots."""
        state = _make_seller_state(pcs=50, adaptive_mode="standard_qualification")

        result = await response_generator_with_calendar.generate_jorge_response(state)

        content = result["response_content"]
        assert "reply with the number" not in content.lower()

    @pytest.mark.asyncio
    async def test_no_calendar_service_graceful(self, response_generator_no_calendar):
        """calendar_focused mode without calendar_service should still work."""
        state = _make_seller_state(pcs=80, adaptive_mode="calendar_focused")

        result = await response_generator_no_calendar.generate_jorge_response(state)

        # Should still have a response, just no calendar slots
        assert result["response_content"]

    @pytest.mark.asyncio
    async def test_fallback_when_no_calendar_id(self, mock_claude, mock_event_publisher, mock_sentiment_service, mock_ab_testing, calendar_service_no_cal_id):
        """Should use fallback message when no calendar ID configured."""
        gen = ResponseGenerator(
            claude=mock_claude,
            event_publisher=mock_event_publisher,
            sentiment_service=mock_sentiment_service,
            ab_testing=mock_ab_testing,
            calendar_service=calendar_service_no_cal_id,
        )
        state = _make_seller_state(pcs=80, adaptive_mode="calendar_focused")

        result = await gen.generate_jorge_response(state)

        content = result["response_content"]
        assert FALLBACK_MESSAGE in content

    @pytest.mark.asyncio
    async def test_fallback_when_no_slots_available(self, mock_claude, mock_event_publisher, mock_sentiment_service, mock_ab_testing, mock_ghl_client):
        """Should use fallback when GHL returns no free slots."""
        mock_ghl_client.get_free_slots = AsyncMock(return_value=[])
        with patch.dict("os.environ", {"JORGE_CALENDAR_ID": "cal_test_123"}):
            service = CalendarBookingService(mock_ghl_client)

        gen = ResponseGenerator(
            claude=mock_claude,
            event_publisher=mock_event_publisher,
            sentiment_service=mock_sentiment_service,
            ab_testing=mock_ab_testing,
            calendar_service=service,
        )
        state = _make_seller_state(pcs=80, adaptive_mode="calendar_focused")

        result = await gen.generate_jorge_response(state)

        content = result["response_content"]
        assert FALLBACK_MESSAGE in content


# ==============================
# Calendar Booking Service Tests
# ==============================


class TestCalendarBookingService:
    """Direct tests for CalendarBookingService."""

    @pytest.mark.asyncio
    async def test_offer_slots_returns_formatted_message(self, calendar_service):
        """Should return formatted slot options."""
        result = await calendar_service.offer_appointment_slots("contact_001")

        assert result["fallback"] is False
        assert len(result["slots"]) == 3
        assert "1." in result["message"]
        assert "2." in result["message"]
        assert "3." in result["message"]

    @pytest.mark.asyncio
    async def test_offer_slots_fallback_no_calendar_id(self, calendar_service_no_cal_id):
        """No calendar ID should return fallback."""
        result = await calendar_service_no_cal_id.offer_appointment_slots("contact_001")

        assert result["fallback"] is True
        assert result["slots"] == []
        assert result["message"] == FALLBACK_MESSAGE

    @pytest.mark.asyncio
    async def test_book_appointment_success(self, calendar_service):
        """Should book a valid slot and return confirmation."""
        # First offer slots to populate pending
        await calendar_service.offer_appointment_slots("contact_001")

        result = await calendar_service.book_appointment("contact_001", 0)

        assert result["success"] is True
        assert result["appointment"] is not None
        assert "booked" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_book_appointment_invalid_index(self, calendar_service):
        """Should reject out-of-range slot index."""
        await calendar_service.offer_appointment_slots("contact_001")

        result = await calendar_service.book_appointment("contact_001", 99)

        assert result["success"] is False
        assert "valid option" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_book_appointment_no_pending_slots(self, calendar_service):
        """Should fail gracefully when no pending slots exist."""
        result = await calendar_service.book_appointment("unknown_contact", 0)

        assert result["success"] is False
        assert "No pending slots" in result["message"]


# ==============================
# Slot Selection Detection Tests
# ==============================


class TestSlotSelectionDetection:
    """Test _detect_slot_selection patterns."""

    def _detect(self, message: str):
        """Import and call the static method."""
        from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot
        return JorgeSellerBot._detect_slot_selection(message)

    def test_plain_number(self):
        assert self._detect("1") == 0
        assert self._detect("2") == 1
        assert self._detect("3") == 2

    def test_slot_prefix(self):
        assert self._detect("slot 1") == 0
        assert self._detect("Slot 2") == 1

    def test_option_prefix(self):
        assert self._detect("option 3") == 2
        assert self._detect("Option 1") == 0

    def test_hash_prefix(self):
        assert self._detect("#1") == 0
        assert self._detect("#3") == 2

    def test_number_prefix(self):
        assert self._detect("number 2") == 1

    def test_no_match(self):
        assert self._detect("I want to sell my house") is None
        assert self._detect("morning works for me") is None
        assert self._detect("") is None

    def test_out_of_range(self):
        assert self._detect("0") is None
        assert self._detect("11") is None
        assert self._detect("99") is None

    def test_whitespace_handling(self):
        assert self._detect("  2  ") == 1
        assert self._detect("slot  1") == 0
