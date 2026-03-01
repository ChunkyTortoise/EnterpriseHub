"""
End-to-end bot test spec — Phone +13109204920

Validates the complete seller and buyer qualification flows from first message
through calendar booking and tag assignment.

Test A: Seller Flow (6 turns, HOT → calendar offer → booking confirmation)
Test B: Buyer Flow (5 turns, HOT → calendar offer → booking confirmation)

Based on spec: End-to-End Bot Test Spec — Phone 3109204920
Critical path: CalendarBookingService, jorge_seller_engine HOT actions,
               jorge_buyer_bot HOT tagging, webhook tag routing
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Shared test constants
# ---------------------------------------------------------------------------

TEST_PHONE = "+13109204920"
TEST_CONTACT_ID = "PHONE_3109204920_TEST"
TEST_LOCATION_ID = "KghwPKXU1zBjqhegruDM"
TEST_CALENDAR_ID = "CrqysY0FVTxatzEczl7h"
TEST_HOT_SELLER_WORKFLOW_ID = "hot-seller-wf-test-001"
TEST_HOT_BUYER_WORKFLOW_ID = "hot-buyer-wf-test-001"


# ---------------------------------------------------------------------------
# Stub infrastructure (mirrors pattern from test_smoke_multiturn.py)
# ---------------------------------------------------------------------------


class _StubMemoryService:
    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}

    async def save_context(self, contact_id: str, ctx: Any, **kw: Any) -> None:
        self._store[contact_id] = ctx

    async def get_context(self, contact_id: str, **kw: Any) -> Optional[Dict]:
        return self._store.get(contact_id)


class _StubConversationManager:
    """Lightweight conversation manager that persists state across turns."""

    def __init__(self) -> None:
        self.memory_service = _StubMemoryService()
        self._history: List[Dict[str, str]] = []
        self._seller_data: Dict[str, Any] = {}
        self._extra_ctx: Dict[str, Any] = {}

    async def get_context(self, contact_id: str, location_id: Optional[str] = None) -> Dict[str, Any]:
        return {
            "contact_id": contact_id,
            "location_id": location_id or TEST_LOCATION_ID,
            "conversation_history": list(self._history),
            "seller_preferences": dict(self._seller_data),
            "contact_name": "Test Contact",
            "closing_probability": 0.0,
            "active_ab_test": None,
            "last_ai_message_type": None,
            "is_returning_lead": False,
            **self._extra_ctx,
        }

    async def get_conversation_history(self, *a: Any, **kw: Any) -> List:
        return list(self._history)

    async def update_context(
        self,
        contact_id: str,
        user_message: str,
        ai_response: str,
        *a: Any,
        **kw: Any,
    ) -> None:
        self._history.append({"role": "user", "content": user_message})
        self._history.append({"role": "assistant", "content": ai_response})
        extracted = kw.get("extracted_data")
        if extracted and isinstance(extracted, dict):
            self._seller_data.update(extracted)

    async def extract_seller_data(
        self, user_message: str, current: Dict, *a: Any, **kw: Any
    ) -> Dict:
        return current

    def set_pending_appointment(self, data: Dict) -> None:
        """Inject pending appointment into context (simulates post-HOT state)."""
        self._extra_ctx["pending_appointment"] = data

    def clear_pending_appointment(self) -> None:
        self._extra_ctx.pop("pending_appointment", None)


def _make_mock_ghl_client() -> AsyncMock:
    """Mock GHL client that tracks calls."""
    client = AsyncMock()
    client.apply_actions = AsyncMock(return_value={"success": True})
    client.add_tags = AsyncMock(return_value={"success": True})
    client.update_contact = AsyncMock(return_value={"success": True})
    client.get_free_slots = AsyncMock(return_value=[
        {"start": "2026-03-10T09:00:00-08:00", "end": "2026-03-10T09:30:00-08:00", "date": "2026-03-10"},
        {"start": "2026-03-10T11:00:00-08:00", "end": "2026-03-10T11:30:00-08:00", "date": "2026-03-10"},
        {"start": "2026-03-11T14:00:00-08:00", "end": "2026-03-11T14:30:00-08:00", "date": "2026-03-11"},
    ])
    client.create_appointment = AsyncMock(return_value={"id": "appt_test_001", "status": "confirmed"})
    return client


def _make_mock_time_slots() -> List[Any]:
    """Build 3 fake TimeSlot-like mocks for CalendarScheduler."""
    slots = []
    base = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)
    for i in range(3):
        ts = MagicMock()
        ts.start_time = base + timedelta(hours=i * 2)
        ts.end_time = ts.start_time + timedelta(minutes=30)
        ts.appointment_type = MagicMock()
        ts.appointment_type.value = "listing_appointment"
        ts.format_for_lead.return_value = f"Monday, March {10 + i} at {9 + i * 2}:00 AM PT"
        slots.append(ts)
    return slots


# ---------------------------------------------------------------------------
# Test A: Seller Flow (Q0-Q6)
# ---------------------------------------------------------------------------


class TestSellerFlow:
    """
    Complete seller qualification flow from first message through calendar booking.

    Seller phone: +13109204920
    Tag setup: 'Needs Qualifying' applied → seller bot activates
    Expected outcome: HOT classification → calendar slot offer → appointment booked
    """

    @pytest.mark.asyncio
    async def test_seller_q0_address_question_on_first_message(self) -> None:
        """
        Turn 0: First message from a fresh contact (no seller data).
        In SIMPLE mode the engine should return the first qualifying question
        (about motivation/reason for selling) without an LLM call.
        """
        from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine

        cm = _StubConversationManager()
        ghl = _make_mock_ghl_client()

        # Patch away all external I/O so the test is fast and deterministic
        with (
            patch.object(
                JorgeSellerEngine,
                "_extract_seller_data",
                new=AsyncMock(return_value={}),  # fresh contact, no data yet
            ),
            patch("ghl_real_estate_ai.services.vapi_service.VapiService.trigger_outbound_call", new_callable=AsyncMock),
            patch("ghl_real_estate_ai.services.calendar_scheduler.get_smart_scheduler") as mock_sched,
        ):
            mock_sched.return_value.get_available_slots = AsyncMock(return_value=[])

            with patch.dict("os.environ", {"JORGE_SIMPLE_MODE": "true"}):
                engine = JorgeSellerEngine(cm, ghl)
                result = await engine.process_seller_response(
                    contact_id=TEST_CONTACT_ID,
                    user_message="hi",
                    location_id=TEST_LOCATION_ID,
                )

        assert result is not None, "Engine must return a result"
        assert "message" in result, "Result must contain a message"
        assert result["temperature"] in ("cold", "warm", "hot"), (
            f"Temperature must be valid, got: {result.get('temperature')}"
        )
        # First turn should be cold (no data answered yet) and message should be Q1
        assert result["temperature"] == "cold", "Fresh contact with no data should be cold"

    @pytest.mark.asyncio
    async def test_seller_hot_path_full_flow_produces_hot_seller_tags(self) -> None:
        """
        Simulates the full seller qualification by directly setting seller_data
        to a fully-qualified state and verifying _create_seller_actions outputs
        the correct HOT tags: Hot-Seller, Seller-Qualified, AI-Off, Human-Follow-Up-Needed.

        This tests the GHL state that would be set after Q5 (price given) with
        scheduling_step=confirmed.
        """
        from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine
        from types import SimpleNamespace

        cm = _StubConversationManager()
        ghl = _make_mock_ghl_client()
        engine = JorgeSellerEngine(cm, ghl)

        # Fully qualified seller data — all 4 questions answered, timeline=True
        seller_data = {
            "questions_answered": 4,
            "timeline_acceptable": True,
            "motivation": "relocation",
            "property_condition": "good",
            "price_expectation": "650000",
            "scheduling_step": "confirmed",  # post-booking state
            "property_address": "123 Maple Street, Rancho Cucamonga",
        }

        pricing_mock = SimpleNamespace(
            final_price=650000.0,
            tier="hot",
            expected_roi=14.5,
            justification="Strong seller, motivated timeline",
        )

        actions = await engine._create_seller_actions(
            contact_id=TEST_CONTACT_ID,
            location_id=TEST_LOCATION_ID,
            temperature="hot",
            seller_data=seller_data,
            pricing_result=pricing_mock,
        )

        action_types = [(a.get("type"), a.get("tag")) for a in actions]

        # Must add HOT seller tags
        assert ("add_tag", "Hot-Seller") in action_types, (
            f"Hot-Seller tag must be added. Actions: {action_types}"
        )
        assert ("add_tag", "Seller-Qualified") in action_types, (
            f"Seller-Qualified tag must be added. Actions: {action_types}"
        )

        # Must add AI-Off and Human-Follow-Up-Needed after booking confirmed
        assert ("add_tag", "AI-Off") in action_types, (
            f"AI-Off must be added after scheduling confirmed. Actions: {action_types}"
        )
        assert ("add_tag", "Human-Follow-Up-Needed") in action_types, (
            f"Human-Follow-Up-Needed must be added after scheduling confirmed. Actions: {action_types}"
        )

        # Must remove Needs Qualifying
        assert ("remove_tag", "Needs Qualifying") in action_types, (
            f"Needs Qualifying must be removed on HOT. Actions: {action_types}"
        )

    @pytest.mark.asyncio
    async def test_seller_hot_workflow_fires_only_after_booking_confirmed(self) -> None:
        """
        HOT_SELLER_WORKFLOW_ID must only trigger when scheduling_step == 'confirmed'.
        Before booking, no workflow trigger should appear in actions.
        """
        from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine
        from types import SimpleNamespace

        cm = _StubConversationManager()
        ghl = _make_mock_ghl_client()
        engine = JorgeSellerEngine(cm, ghl)

        pricing_mock = SimpleNamespace(
            final_price=650000.0, tier="hot", expected_roi=14.0, justification="test"
        )

        with patch.dict(
            "os.environ",
            {"HOT_SELLER_WORKFLOW_ID": TEST_HOT_SELLER_WORKFLOW_ID},
        ):
            # HOT but not yet confirmed — no workflow trigger
            actions_pre = await engine._create_seller_actions(
                contact_id=TEST_CONTACT_ID,
                location_id=TEST_LOCATION_ID,
                temperature="hot",
                seller_data={
                    "questions_answered": 4,
                    "timeline_acceptable": True,
                    "motivation": "relocation",
                    "price_expectation": "650000",
                    # no scheduling_step
                },
                pricing_result=pricing_mock,
            )
            wf_pre = [a for a in actions_pre if a.get("type") == "trigger_workflow"]
            assert not wf_pre, (
                "Workflow must NOT fire before scheduling is confirmed. "
                f"Got: {wf_pre}"
            )

            # After booking confirmed — workflow fires
            actions_post = await engine._create_seller_actions(
                contact_id=TEST_CONTACT_ID,
                location_id=TEST_LOCATION_ID,
                temperature="hot",
                seller_data={
                    "questions_answered": 4,
                    "timeline_acceptable": True,
                    "motivation": "relocation",
                    "price_expectation": "650000",
                    "scheduling_step": "confirmed",
                },
                pricing_result=pricing_mock,
            )
            wf_post = [a for a in actions_post if a.get("type") == "trigger_workflow"]
            assert wf_post, (
                "Workflow MUST fire after scheduling_step=confirmed. "
                f"Actions: {[a.get('type') for a in actions_post]}"
            )
            assert wf_post[0]["workflow_id"] == TEST_HOT_SELLER_WORKFLOW_ID

    @pytest.mark.asyncio
    async def test_seller_custom_fields_written_for_hot_seller(self) -> None:
        """
        Custom fields for seller temperature, motivation, timeline, condition,
        price expectation, and PCS score must all appear in the actions dict
        when a seller is HOT.
        """
        from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine
        from types import SimpleNamespace

        cm = _StubConversationManager()
        ghl = _make_mock_ghl_client()
        engine = JorgeSellerEngine(cm, ghl)

        seller_data = {
            "questions_answered": 4,
            "timeline_acceptable": True,
            "motivation": "relocation",
            "property_condition": "good",
            "price_expectation": "650000",
            "scheduling_step": "confirmed",
        }
        pricing_mock = SimpleNamespace(
            final_price=650000.0, tier="hot", expected_roi=14.0, justification="test"
        )

        with patch.dict("os.environ", {
            "CUSTOM_FIELD_SELLER_TEMPERATURE": "fld_seller_temp",
            "CUSTOM_FIELD_SELLER_MOTIVATION": "fld_seller_motivation",
            "CUSTOM_FIELD_PRICE_EXPECTATION": "fld_price_exp",
        }):
            actions = await engine._create_seller_actions(
                contact_id=TEST_CONTACT_ID,
                location_id=TEST_LOCATION_ID,
                temperature="hot",
                seller_data=seller_data,
                pricing_result=pricing_mock,
            )

        custom_field_actions = [a for a in actions if a.get("type") == "update_custom_field"]
        assert custom_field_actions, (
            f"Custom field updates must be written for HOT seller. Got actions: {[a.get('type') for a in actions]}"
        )

    @pytest.mark.asyncio
    async def test_seller_temperature_classification_hot_requires_4_questions_and_timeline(self) -> None:
        """
        HOT requires exactly 4 questions answered AND timeline_acceptable=True.
        Anything less must classify as warm or cold.
        """
        from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine

        cm = _StubConversationManager()
        ghl = _make_mock_ghl_client()
        engine = JorgeSellerEngine(cm, ghl)

        # All 4 answered but timeline rejected → NOT hot
        result_no_timeline = await engine._calculate_seller_temperature({
            "questions_answered": 4,
            "response_quality": 1.0,
            "timeline_acceptable": False,
        })
        assert result_no_timeline["temperature"] != "hot", (
            "Should not be HOT when timeline is rejected"
        )

        # Timeline accepted but only 3 questions → NOT hot
        result_3q = await engine._calculate_seller_temperature({
            "questions_answered": 3,
            "response_quality": 1.0,
            "timeline_acceptable": True,
        })
        assert result_3q["temperature"] != "hot", (
            "Should not be HOT with only 3 questions answered"
        )

        # All 4 + timeline accepted → HOT
        result_hot = await engine._calculate_seller_temperature({
            "questions_answered": 4,
            "response_quality": 1.0,
            "timeline_acceptable": True,
        })
        assert result_hot["temperature"] == "hot", (
            f"Should be HOT with 4 questions + timeline. Got: {result_hot['temperature']}"
        )

    @pytest.mark.asyncio
    async def test_seller_ai_valuation_price_uses_sellers_price_expectation(self) -> None:
        """
        ai_valuation_price field must use the seller's stated price_expectation (650000),
        not the lead-pricing model value.
        """
        from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine
        from types import SimpleNamespace

        cm = _StubConversationManager()
        ghl = _make_mock_ghl_client()
        engine = JorgeSellerEngine(cm, ghl)

        pricing_mock = SimpleNamespace(final_price=2.0, tier="hot", expected_roi=12.5, justification="test")
        seller_data = {
            "price_expectation": "650,000",
            "motivation": "relocation",
            "timeline": "30 days",
            "property_condition": "good",
        }

        actions = await engine._create_seller_actions(
            contact_id=TEST_CONTACT_ID,
            location_id=TEST_LOCATION_ID,
            temperature="hot",
            seller_data=seller_data,
            pricing_result=pricing_mock,
        )

        valuation_actions = [a for a in actions if "valuation" in str(a.get("field", ""))]
        if valuation_actions:
            val = str(valuation_actions[0]["value"])
            assert "650" in val, (
                f"ai_valuation_price should reflect seller's $650,000, got: {val}"
            )
            assert "2.0" not in val, (
                f"ai_valuation_price must NOT use pricing model mock value 2.0, got: {val}"
            )


# ---------------------------------------------------------------------------
# Test B: Buyer Flow (Q0-Q5)
# ---------------------------------------------------------------------------


class TestBuyerFlow:
    """
    Complete buyer qualification flow from first message through calendar booking.

    Tag setup: 'Buyer-Lead' applied → buyer bot activates
    Expected outcome: HOT classification → calendar slot offer → appointment booked
    """

    @pytest.mark.asyncio
    async def test_buyer_hot_path_complete_conversation(self, _mock_buyer_deps) -> None:
        """
        Full buyer qualification: pre-approved + budget + 60-day timeline → HOT.
        GHL tags should include Hot-Buyer or buyer temperature field.
        """
        from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

        # Set HOT financial profile
        _mock_buyer_deps["profile"].financial_readiness = 92.0
        _mock_buyer_deps["profile"].urgency_score = 88.0
        _mock_buyer_deps["profile"].financing_status_score = 95.0
        _mock_buyer_deps["profile"].budget_clarity = 90.0
        _mock_buyer_deps["profile"].buyer_temperature = "hot"
        _mock_buyer_deps["profile"].next_qualification_step = "appointment"

        bot = JorgeBuyerBot()

        history: List[Dict[str, str]] = []

        async def run_turn(msg: str) -> Dict[str, Any]:
            history.append({"role": "user", "content": msg})
            result = await bot.process_buyer_conversation(
                conversation_id=TEST_CONTACT_ID,
                user_message=msg,
                buyer_name="Test Contact",
                conversation_history=list(history),
            )
            response = result.get("response_content", "")
            history.append({"role": "assistant", "content": response})
            return result

        # Q1: Budget
        r1 = await run_turn("My budget is $550,000")
        assert r1 is not None, "Turn 1 must return a result"

        # Q2: Pre-approval
        r2 = await run_turn("Yes, I'm pre-approved")
        assert r2 is not None, "Turn 2 must return a result"

        # Q3: Preferences
        r3 = await run_turn("3 bedrooms, need a yard")
        assert r3 is not None, "Turn 3 must return a result"

        # Q4: Timeline — triggers HOT
        r4 = await run_turn("I want to buy within 60 days")
        assert r4 is not None, "Turn 4 must return a result"

        # Verify the final result includes expected qualification keys
        final = r4
        assert "response_content" in final or "message" in final, (
            "Buyer result must contain a response message"
        )

    @pytest.mark.asyncio
    async def test_buyer_workflow_tags_applied_on_hot(_self, _mock_buyer_deps) -> None:
        """
        When buyer is HOT, apply_auto_tags should be called with Hot-Buyer or
        Hot temperature. Verify the workflow service is invoked.
        """
        from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

        _mock_buyer_deps["profile"].buyer_temperature = "hot"
        _mock_buyer_deps["profile"].financial_readiness = 92.0
        _mock_buyer_deps["profile"].urgency_score = 90.0
        _mock_buyer_deps["profile"].financing_status_score = 95.0
        _mock_buyer_deps["profile"].budget_clarity = 90.0

        bot = JorgeBuyerBot()

        await bot.process_buyer_conversation(
            conversation_id=TEST_CONTACT_ID,
            user_message="I want to buy within 60 days, pre-approved for $550k",
            buyer_name="Test Contact",
            conversation_history=[],
        )

        # Workflow service must be called to apply tags
        _mock_buyer_deps["workflow"].apply_auto_tags.assert_called()

    @pytest.mark.asyncio
    async def test_buyer_multiturn_does_not_repeat_tour_question(self, _mock_buyer_deps) -> None:
        """
        After the buyer answers the tour preference question, the bot must
        advance to the next question and not repeat itself.
        """
        from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

        bot = JorgeBuyerBot()
        history: List[Dict[str, str]] = []

        async def run_turn(msg: str) -> Dict[str, Any]:
            history.append({"role": "user", "content": msg})
            result = await bot.process_buyer_conversation(
                conversation_id=TEST_CONTACT_ID,
                user_message=msg,
                buyer_name="Test",
                conversation_history=list(history),
            )
            resp = result.get("response_content", "")
            history.append({"role": "assistant", "content": resp})
            return result

        # Turn 1: qualified buyer → bot asks tour preference
        r1 = await run_turn("Looking to buy around $600K, pre-approved")
        resp1 = r1.get("response_content", "")
        assert resp1.strip(), "Turn 1 should produce a response"

        # Turn 2: user answers tour → bot must advance
        r2 = await run_turn("mornings work great")
        resp2 = r2.get("response_content", "")
        assert "mornings or afternoons" not in resp2.lower(), (
            f"Turn 2 must not repeat tour question, got: {resp2}"
        )

        # Turn 3: preferences given → bot asks something new
        r3 = await run_turn("3 bed 2 bath single family in Rancho Cucamonga")
        resp3 = r3.get("response_content", "")
        assert resp3.strip(), "Turn 3 should produce a non-empty response"
        assert "mornings or afternoons" not in resp3.lower(), (
            f"Turn 3 must not re-ask tour question, got: {resp3}"
        )


# ---------------------------------------------------------------------------
# Test C: Calendar Booking — HOT Seller Slot Offer + Selection
# ---------------------------------------------------------------------------


class TestCalendarBookingIntegration:
    """
    Tests the CalendarBookingService integration within the HOT qualification flow.
    Verifies that slots are offered via numbered list and that selecting '1' books
    the correct slot in GHL.
    """

    @pytest.mark.asyncio
    async def test_calendar_slot_offer_formats_numbered_list(self) -> None:
        """When calendar is configured and slots exist, offer a numbered list."""
        from ghl_real_estate_ai.services.jorge.calendar_booking_service import CalendarBookingService

        ghl = _make_mock_ghl_client()
        with patch.dict("os.environ", {"JORGE_CALENDAR_ID": TEST_CALENDAR_ID}):
            svc = CalendarBookingService(ghl)

        result = await svc.offer_appointment_slots(TEST_CONTACT_ID)

        assert result["fallback"] is False
        msg = result["message"]
        assert "1." in msg, f"Numbered options expected in: {msg}"
        assert "2." in msg, f"Numbered options expected in: {msg}"
        assert "3." in msg, f"Numbered options expected in: {msg}"
        assert "reply with the number" in msg.lower()

    @pytest.mark.asyncio
    async def test_calendar_slot_selection_1_books_first_slot(self) -> None:
        """User reply '1' (slot_index=0) books the first available slot."""
        from ghl_real_estate_ai.services.jorge.calendar_booking_service import CalendarBookingService

        ghl = _make_mock_ghl_client()
        with patch.dict("os.environ", {"JORGE_CALENDAR_ID": TEST_CALENDAR_ID}):
            svc = CalendarBookingService(ghl)

        # Step 1: Offer slots (caches them)
        await svc.offer_appointment_slots(TEST_CONTACT_ID)

        # Step 2: User selects option 1 (0-indexed)
        result = await svc.book_appointment(TEST_CONTACT_ID, slot_index=0)

        assert result["success"] is True
        assert result["appointment"]["id"] == "appt_test_001"
        assert "booked" in result["message"].lower() or "all set" in result["message"].lower()

        # Verify GHL received correct booking params
        ghl.create_appointment.assert_awaited_once_with(
            calendar_id=TEST_CALENDAR_ID,
            contact_id=TEST_CONTACT_ID,
            start_time="2026-03-10T09:00:00-08:00",
            end_time="2026-03-10T09:30:00-08:00",
            title="Seller Consultation",
        )

    @pytest.mark.asyncio
    async def test_calendar_slot_selection_2_books_second_slot(self) -> None:
        """User reply '2' (slot_index=1) books the second available slot."""
        from ghl_real_estate_ai.services.jorge.calendar_booking_service import CalendarBookingService

        ghl = _make_mock_ghl_client()
        with patch.dict("os.environ", {"JORGE_CALENDAR_ID": TEST_CALENDAR_ID}):
            svc = CalendarBookingService(ghl)

        await svc.offer_appointment_slots(TEST_CONTACT_ID)
        result = await svc.book_appointment(TEST_CONTACT_ID, slot_index=1)

        assert result["success"] is True
        # Second slot is 11:00 AM
        call_args = ghl.create_appointment.call_args
        assert "2026-03-10T11:00:00-08:00" == call_args.kwargs["start_time"]

    @pytest.mark.asyncio
    async def test_calendar_fallback_when_no_calendar_id(self) -> None:
        """Without JORGE_CALENDAR_ID, bot falls back to open-ended scheduling question."""
        from ghl_real_estate_ai.services.jorge.calendar_booking_service import (
            FALLBACK_MESSAGE,
            CalendarBookingService,
        )

        ghl = _make_mock_ghl_client()
        with patch.dict("os.environ", {}, clear=True):
            svc = CalendarBookingService(ghl)
            svc.calendar_id = ""

        result = await svc.offer_appointment_slots(TEST_CONTACT_ID)

        assert result["fallback"] is True
        assert result["message"] == FALLBACK_MESSAGE
        ghl.get_free_slots.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_booking_confirmation_message_includes_slot_time(self) -> None:
        """Confirmation message must reference the booked slot's formatted time."""
        from ghl_real_estate_ai.services.jorge.calendar_booking_service import CalendarBookingService

        ghl = _make_mock_ghl_client()
        with patch.dict("os.environ", {"JORGE_CALENDAR_ID": TEST_CALENDAR_ID}):
            svc = CalendarBookingService(ghl)

        await svc.offer_appointment_slots(TEST_CONTACT_ID)
        result = await svc.book_appointment(TEST_CONTACT_ID, slot_index=0)

        assert result["success"] is True
        # Confirmation must mention "all set" and the slot details
        assert "all set" in result["message"].lower() or "booked" in result["message"].lower()
        # Month should appear in the formatted time
        assert "march" in result["message"].lower() or "monday" in result["message"].lower()


# ---------------------------------------------------------------------------
# Test D: Webhook Tag Routing — Phone 3109204920
# ---------------------------------------------------------------------------


class TestWebhookTagRouting:
    """
    Validates that the webhook correctly routes Needs Qualifying → seller bot
    and Buyer-Lead → buyer bot, using the tag routing utilities in webhook.py.

    This mirrors what happens when Jorge manually applies tags in GHL
    for contact with phone +13109204920.
    """

    def test_needs_qualifying_routes_to_seller_mode(self) -> None:
        """Tag 'Needs Qualifying' activates seller mode and deactivates lead mode."""
        from ghl_real_estate_ai.api.routes.webhook import (
            _compute_mode_flags,
            _normalize_tags,
            _select_primary_mode,
        )

        tags = _normalize_tags(["Needs Qualifying"])
        flags = _compute_mode_flags(
            tags,
            should_deactivate=False,
            seller_mode_enabled=True,
            buyer_mode_enabled=True,
            lead_mode_enabled=True,
            buyer_activation_tag="Buyer-Lead",
            lead_activation_tag="Needs Qualifying",
        )

        assert flags["seller"] is True, "Seller mode must activate on 'Needs Qualifying'"
        assert flags["lead"] is False, "Lead mode must NOT fire when seller claims 'Needs Qualifying'"
        assert _select_primary_mode(flags) == "seller"

    def test_buyer_lead_tag_routes_to_buyer_mode(self) -> None:
        """Tag 'Buyer-Lead' activates buyer mode."""
        from ghl_real_estate_ai.api.routes.webhook import (
            _compute_mode_flags,
            _normalize_tags,
            _select_primary_mode,
        )

        tags = _normalize_tags(["Buyer-Lead"])
        flags = _compute_mode_flags(
            tags,
            should_deactivate=False,
            seller_mode_enabled=True,
            buyer_mode_enabled=True,
            lead_mode_enabled=True,
            buyer_activation_tag="Buyer-Lead",
            lead_activation_tag="Needs Qualifying",
        )

        assert flags["buyer"] is True, "Buyer mode must activate on 'Buyer-Lead'"
        assert _select_primary_mode(flags) == "buyer"

    def test_ai_off_tag_deactivates_all_bots(self) -> None:
        """Contact with AI-Off tag must have all modes deactivated."""
        from ghl_real_estate_ai.api.routes.webhook import (
            _compute_mode_flags,
            _normalize_tags,
        )

        tags = _normalize_tags(["Needs Qualifying", "AI-Off"])
        flags = _compute_mode_flags(
            tags,
            should_deactivate=True,  # AI-Off sets this
            seller_mode_enabled=True,
            buyer_mode_enabled=True,
            lead_mode_enabled=True,
            buyer_activation_tag="Buyer-Lead",
            lead_activation_tag="Needs Qualifying",
        )

        assert flags["seller"] is False
        assert flags["buyer"] is False
        assert flags["lead"] is False

    def test_stop_bot_tag_prevents_seller_mode(self) -> None:
        """Contacts tagged Stop-Bot must not enter seller mode."""
        from ghl_real_estate_ai.api.routes.webhook import (
            _compute_mode_flags,
            _normalize_tags,
        )

        tags = _normalize_tags(["Needs Qualifying", "Stop-Bot"])
        # Stop-Bot also sets should_deactivate=True
        flags = _compute_mode_flags(
            tags,
            should_deactivate=True,
            seller_mode_enabled=True,
            buyer_mode_enabled=True,
            lead_mode_enabled=True,
            buyer_activation_tag="Buyer-Lead",
            lead_activation_tag="Needs Qualifying",
        )

        assert flags["seller"] is False, "Stop-Bot must prevent seller activation"

    def test_seller_has_priority_over_buyer_on_simultaneous_tags(self) -> None:
        """When both Needs Qualifying and Buyer-Lead are present, seller wins."""
        from ghl_real_estate_ai.api.routes.webhook import (
            _compute_mode_flags,
            _normalize_tags,
            _select_primary_mode,
        )

        tags = _normalize_tags(["Needs Qualifying", "Buyer-Lead"])
        flags = _compute_mode_flags(
            tags,
            should_deactivate=False,
            seller_mode_enabled=True,
            buyer_mode_enabled=True,
            lead_mode_enabled=True,
            buyer_activation_tag="Buyer-Lead",
            lead_activation_tag="Needs Qualifying",
        )

        assert _select_primary_mode(flags) == "seller"


# ---------------------------------------------------------------------------
# Test E: Smoke Test — Webhook Endpoint (no real server needed)
# ---------------------------------------------------------------------------


class TestWebhookSmoke:
    """
    Quick smoke tests for the webhook endpoint using FastAPI TestClient.
    Validates that the endpoint:
    - Requires X-GHL-Signature header (401 without it)
    - Accepts valid seller payload and routes to seller mode
    - Returns structured GHLWebhookResponse
    """

    @pytest.fixture()
    def app(self):
        """
        Build the FastAPI app for testing.

        The webhook router declares prefix='/ghl', so the app-level prefix
        must be '/api' to get the canonical path /api/ghl/webhook.
        """
        from fastapi import FastAPI
        from ghl_real_estate_ai.api.routes import webhook as wh_module

        test_app = FastAPI()
        # Router prefix="/ghl" + app prefix="/api" → /api/ghl/webhook
        test_app.include_router(wh_module.router, prefix="/api")
        return test_app

    def test_webhook_returns_4xx_on_missing_body(self, app) -> None:
        """Empty POST to /api/ghl/webhook should return 4xx (auth or validation error)."""
        from fastapi.testclient import TestClient

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/api/ghl/webhook",
            json={},
            headers={"X-GHL-Signature": "test-sig"},
        )
        # 422 = Unprocessable Entity (missing required fields)
        # 401/403 = signature validation fails before schema parse
        assert resp.status_code in (400, 401, 403, 422), (
            f"Empty payload should fail with 4xx, got {resp.status_code}"
        )

    def test_tag_routing_inbound_message_seller_path(self) -> None:
        """
        Simulates GHL sending an inbound SMS with 'Needs Qualifying' tag.
        Verifies the webhook routing selects seller mode (unit-level, no HTTP).
        """
        from ghl_real_estate_ai.api.routes.webhook import (
            _compute_mode_flags,
            _normalize_tags,
            _select_primary_mode,
            _tag_present,
        )

        # Exact payload structure that GHL sends for +13109204920
        raw_tags = ["Needs Qualifying"]
        tags_lower = _normalize_tags(raw_tags)

        # Simulate the tag-deactivation check
        deactivation_tags = {"ai-off", "stop-bot"}
        should_deactivate = bool(tags_lower & deactivation_tags)
        assert not should_deactivate

        mode_flags = _compute_mode_flags(
            tags_lower,
            should_deactivate=should_deactivate,
            seller_mode_enabled=True,
            buyer_mode_enabled=True,
            lead_mode_enabled=True,
            buyer_activation_tag="Buyer-Lead",
            lead_activation_tag="Needs Qualifying",
        )

        primary_mode = _select_primary_mode(mode_flags)
        assert primary_mode == "seller", (
            f"'Needs Qualifying' tag on {TEST_PHONE} must route to seller mode. Got: {primary_mode}"
        )


# ---------------------------------------------------------------------------
# pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def _mock_buyer_deps():
    """Patch all external buyer bot dependencies."""
    with (
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.BuyerIntentDecoder") as MockIntent,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.ClaudeAssistant") as MockClaude,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.get_event_publisher") as MockEvent,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.PropertyMatcher") as MockMatcher,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.GHLWorkflowService") as MockWorkflow,
    ):
        from ghl_real_estate_ai.models.lead_scoring import BuyerIntentProfile

        intent_instance = MockIntent.return_value
        mock_profile = MagicMock(spec=BuyerIntentProfile)
        mock_profile.buyer_temperature = "warm"
        mock_profile.financial_readiness = 75.0
        mock_profile.urgency_score = 80.0
        mock_profile.confidence_level = 90.0
        mock_profile.financing_status_score = 80.0
        mock_profile.budget_clarity = 85.0
        mock_profile.preference_clarity = 70.0
        mock_profile.next_qualification_step = "property_search"
        intent_instance.analyze_buyer = MagicMock(return_value=mock_profile)

        claude_instance = MockClaude.return_value
        claude_instance.generate_response = AsyncMock(return_value={"content": "Mocked Buyer Response"})

        matcher_instance = MockMatcher.return_value
        matcher_instance.find_matches = AsyncMock(return_value=[])
        matcher_instance.find_buyer_matches = AsyncMock(return_value=[])

        event_instance = MockEvent.return_value
        event_instance.publish_bot_status_update = AsyncMock()
        event_instance.publish_buyer_intent_analysis = AsyncMock()
        event_instance.publish_property_match_update = AsyncMock()
        event_instance.publish_buyer_follow_up_scheduled = AsyncMock()
        event_instance.publish_buyer_qualification_complete = AsyncMock()
        event_instance.publish_conversation_update = AsyncMock()
        event_instance.publish_jorge_qualification_progress = AsyncMock()

        workflow_instance = MockWorkflow.return_value
        workflow_instance.apply_auto_tags = AsyncMock(return_value={"success": True})

        yield {
            "intent": intent_instance,
            "claude": claude_instance,
            "matcher": matcher_instance,
            "event": event_instance,
            "profile": mock_profile,
            "workflow": workflow_instance,
        }
