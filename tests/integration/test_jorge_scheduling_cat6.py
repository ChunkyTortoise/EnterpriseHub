"""
CAT-6: Scheduling edge-case integration tests.

Covers five scenarios identified in the RT audit that were untested:
  1. Scheduling attempt before HOT threshold (cold/warm seller gets no slot offer)
  2. Jorge skips slot offer when appointment is already pending
  3. Double-booking attempt (duplicate slot-offer suppressed on second HOT turn)
  4. Out-of-hours slot fetch returns empty — engine falls through to text response
  5. No calendar integration (JORGE_CALENDAR_ID unset) — engine omits slot offer

All GHL and LLM calls are mocked. No real API calls.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.critical]

from unittest.mock import AsyncMock, MagicMock, patch

# Skip whole module gracefully if full app deps are absent (minimal CI sandbox).
try:
    from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine

    _ENGINE_AVAILABLE = True
except ImportError:
    _ENGINE_AVAILABLE = False

_needs_engine = pytest.mark.skipif(
    not _ENGINE_AVAILABLE,
    reason="Full app deps not installed (aiohttp/aiosqlite missing)",
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_conversation_manager(seller_prefs: dict | None = None, pending_appointment=None) -> AsyncMock:
    """Return a minimal stub conversation manager with configurable context."""
    cm = AsyncMock()
    ctx: dict = {
        "seller_preferences": seller_prefs or {},
        "conversation_history": [],
        "contact_name": "Test Seller",
        "closing_probability": 0.0,
    }
    if pending_appointment is not None:
        ctx["pending_appointment"] = pending_appointment

    cm.get_context = AsyncMock(return_value=ctx)
    cm.update_context = AsyncMock()
    cm.get_conversation_history = AsyncMock(return_value=[])

    class _MemoryService:
        async def save_context(self, *a, **kw):
            pass

    cm.memory_service = _MemoryService()
    return cm


def _make_ghl_client() -> MagicMock:
    """Return a minimal GHL client stub (no calendar methods needed for most CAT-6 tests)."""
    client = MagicMock()
    client.apply_actions = AsyncMock(return_value=[])
    return client


def _build_engine(conversation_manager, ghl_client=None) -> "JorgeSellerEngine":
    """Construct a JorgeSellerEngine with mocked sub-services."""
    if ghl_client is None:
        ghl_client = _make_ghl_client()
    return JorgeSellerEngine(conversation_manager=conversation_manager, ghl_client=ghl_client)


# ---------------------------------------------------------------------------
# Patch target constants
# ---------------------------------------------------------------------------

_SCHEDULER_PATH = "ghl_real_estate_ai.services.calendar_scheduler.get_smart_scheduler"
_CALENDAR_IMPORT_PATH = "ghl_real_estate_ai.services.calendar_scheduler.get_smart_scheduler"


# ---------------------------------------------------------------------------
# Scenario 1: Scheduling attempt before HOT threshold
# ---------------------------------------------------------------------------


@_needs_engine
@pytest.mark.asyncio
async def test_no_slot_offer_when_below_hot_threshold() -> None:
    """A seller who has answered fewer than 4 questions must not receive a slot
    offer — the temperature will be cold/warm and the scheduling block is gated
    on ``temperature == "hot"``.
    """
    # Only motivation answered — far below HOT threshold (needs 4 + timeline=True)
    seller_prefs = {
        "motivation": "downsizing after kids moved out",
        "timeline_acceptable": None,
        "property_condition": None,
        "price_expectation": None,
        "questions_answered": 1,
        "response_quality": 0.7,
    }
    cm = _make_conversation_manager(seller_prefs=seller_prefs)
    engine = _build_engine(cm)

    with patch(_SCHEDULER_PATH) as mock_sched_factory:
        result = await engine.process_seller_response(
            contact_id="cat6-below-hot-001",
            user_message="I want to downsize now that the kids left",
            location_id="loc-test",
        )

    # Scheduler must never be called — temperature is not hot
    mock_sched_factory.assert_not_called()

    # Response should not contain the slot-offer phrasing
    msg = result.get("message", "")
    assert "Reply with 1, 2, or 3" not in msg, "Slot offer must not appear for a below-HOT seller"
    assert result.get("temperature") in ("cold", "warm"), (
        f"Expected cold or warm temperature, got: {result.get('temperature')!r}"
    )


# ---------------------------------------------------------------------------
# Scenario 2: Jorge skips slot offer when appointment already pending
# ---------------------------------------------------------------------------


@_needs_engine
@pytest.mark.asyncio
async def test_no_duplicate_slot_offer_when_appointment_already_pending() -> None:
    """If the contact already has a ``pending_appointment`` in context, the engine
    must not offer a second set of slots, even for a HOT seller.  The guard is the
    ``not context.get("pending_appointment")`` check at line 445.
    """
    seller_prefs = {
        "motivation": "relocating for work",
        "timeline_acceptable": True,
        "property_condition": "move-in ready",
        "price_expectation": "650000",
        "questions_answered": 4,
        "response_quality": 1.0,
    }
    pending = {
        "status": "awaiting_selection",
        "options": [
            {
                "label": "1",
                "display": "Thursday, March 1 at 10:00 AM",
                "start_time": "2026-03-01T10:00:00Z",
                "end_time": "2026-03-01T11:00:00Z",
                "appointment_type": "listing_appointment",
            }
        ],
        "attempts": 0,
    }
    cm = _make_conversation_manager(seller_prefs=seller_prefs, pending_appointment=pending)
    engine = _build_engine(cm)

    with patch(_SCHEDULER_PATH) as mock_sched_factory:
        result = await engine.process_seller_response(
            contact_id="cat6-already-pending-002",
            user_message="I am ready to move forward",
            location_id="loc-test",
        )

    # Scheduler must never be invoked — pending_appointment already exists
    mock_sched_factory.assert_not_called()

    msg = result.get("message", "")
    assert "Reply with 1, 2, or 3" not in msg, "Slot offer must not repeat when a pending appointment already exists"


# ---------------------------------------------------------------------------
# Scenario 3: Double-booking attempt
# ---------------------------------------------------------------------------


@_needs_engine
@pytest.mark.asyncio
async def test_double_booking_suppressed_on_second_hot_turn() -> None:
    """A HOT seller sends a second message after already receiving a slot offer.
    The engine must not produce a second slot offer; it should respond as if
    the appointment is still pending (already guarded by the context flag).
    """
    seller_prefs = {
        "motivation": "upsizing",
        "timeline_acceptable": True,
        "property_condition": "needs work",
        "price_expectation": "700000",
        "questions_answered": 4,
        "response_quality": 1.0,
    }
    # Simulate that the first turn already stored pending_appointment
    pending = {
        "status": "awaiting_selection",
        "options": [
            {
                "label": "1",
                "display": "Friday, March 2 at 2:00 PM",
                "start_time": "2026-03-02T14:00:00Z",
                "end_time": "2026-03-02T15:00:00Z",
                "appointment_type": "listing_appointment",
            }
        ],
        "attempts": 0,
    }
    cm = _make_conversation_manager(seller_prefs=seller_prefs, pending_appointment=pending)
    engine = _build_engine(cm)

    slot_offer_count = 0

    async def _counting_process(*args, **kwargs):
        nonlocal slot_offer_count
        r = await engine.process_seller_response(*args, **kwargs)
        if "Reply with 1, 2, or 3" in r.get("message", ""):
            slot_offer_count += 1
        return r

    with patch(_SCHEDULER_PATH) as mock_sched_factory:
        # First follow-up turn
        r1 = await engine.process_seller_response(
            contact_id="cat6-double-book-003",
            user_message="Actually, can we make it sooner?",
            location_id="loc-test",
        )
        # Second follow-up turn (context still has pending_appointment)
        r2 = await engine.process_seller_response(
            contact_id="cat6-double-book-003",
            user_message="Hello?",
            location_id="loc-test",
        )

    # Scheduler must never be called across both turns
    mock_sched_factory.assert_not_called()

    for i, r in enumerate([r1, r2], start=1):
        assert "Reply with 1, 2, or 3" not in r.get("message", ""), (
            f"Turn {i} should not re-offer slots when pending_appointment exists"
        )


# ---------------------------------------------------------------------------
# Scenario 4: Out-of-hours request (scheduler returns empty slots)
# ---------------------------------------------------------------------------


@_needs_engine
@pytest.mark.asyncio
async def test_out_of_hours_empty_slots_falls_through_to_text_response() -> None:
    """When the scheduler returns no available slots (e.g. out-of-hours or weekend),
    the engine must fall through to _generate_seller_response rather than offering
    an empty slot menu.  The response must not contain the slot-offer string.
    """
    seller_prefs = {
        "motivation": "relocating",
        "timeline_acceptable": True,
        "property_condition": "move-in ready",
        "price_expectation": "600000",
        "questions_answered": 4,
        "response_quality": 1.0,
    }
    cm = _make_conversation_manager(seller_prefs=seller_prefs)
    engine = _build_engine(cm)

    # Scheduler exists but returns zero slots
    mock_scheduler = MagicMock()
    mock_scheduler.get_available_slots = AsyncMock(return_value=[])

    with patch(_SCHEDULER_PATH, return_value=mock_scheduler):
        result = await engine.process_seller_response(
            contact_id="cat6-out-of-hours-004",
            user_message="I want to sell as soon as possible",
            location_id="loc-test",
        )

    msg = result.get("message", "")
    assert "Reply with 1, 2, or 3" not in msg, "No slot offer should appear when get_available_slots returns []"
    assert len(msg) > 0, "Engine must still produce a non-empty response"
    assert not isinstance(result, Exception), f"Engine raised an exception: {result}"


# ---------------------------------------------------------------------------
# Scenario 5: No calendar integration configured
# ---------------------------------------------------------------------------


@_needs_engine
@pytest.mark.asyncio
async def test_no_slot_offer_when_calendar_not_configured() -> None:
    """When get_smart_scheduler raises (simulating missing JORGE_CALENDAR_ID or
    import error), the engine's try/except swallows it and falls through to a
    regular seller response — no slot offer, no crash.
    """
    seller_prefs = {
        "motivation": "estate sale",
        "timeline_acceptable": True,
        "property_condition": "needs work",
        "price_expectation": "450000",
        "questions_answered": 4,
        "response_quality": 1.0,
    }
    cm = _make_conversation_manager(seller_prefs=seller_prefs)
    engine = _build_engine(cm)

    with patch(
        _SCHEDULER_PATH,
        side_effect=RuntimeError("JORGE_CALENDAR_ID not configured"),
    ):
        result = await engine.process_seller_response(
            contact_id="cat6-no-calendar-005",
            user_message="Ready to list whenever",
            location_id="loc-test",
        )

    msg = result.get("message", "")
    assert "Reply with 1, 2, or 3" not in msg, "Slot offer must not appear when calendar integration is unavailable"
    assert len(msg) > 0, "Engine must produce a fallback response even with no calendar"
    # No exception bubbled up
    assert "error" not in result or result.get("temperature") is not None, (
        "process_seller_response must not surface calendar errors to callers"
    )
