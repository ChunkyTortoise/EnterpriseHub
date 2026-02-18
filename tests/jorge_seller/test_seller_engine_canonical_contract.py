from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from unittest.mock import patch

import pytest
import pytz

from ghl_real_estate_ai.api.schemas.ghl import ActionType, GHLAction
from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig
from ghl_real_estate_ai.services.calendar_scheduler import AppointmentType, TimeSlot
from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine, SellerQuestions


@pytest.fixture
def seller_engine():
    manager = AsyncMock()
    manager.get_context.return_value = {"seller_preferences": {}, "conversation_history": []}
    manager.extract_seller_data.return_value = {}
    ghl_client = AsyncMock()
    return JorgeSellerEngine(manager, ghl_client)


def test_seller_questions_use_expanded_order():
    seller_data = {
        "motivation": "Relocation",
        "timeline_acceptable": True,
        "property_condition": "move-in ready",
        "asking_price": 700000,
    }
    # First four answered, next prompt should move to property address.
    assert SellerQuestions.get_question_number(seller_data) == 5


def test_normalize_contract_preserves_existing_non_null_values(seller_engine):
    current = {"property_address": "111 Existing St", "motivation": "Downsizing"}
    incoming = {"property_address": None, "asking_price": "650k", "timeline_acceptable": True}

    normalized = seller_engine._normalize_seller_contract_data(incoming, current, "we can do 30 days")

    assert normalized["property_address"] == "111 Existing St"
    assert normalized["asking_price"] == 650000
    assert normalized["price_expectation"] == 650000
    assert normalized["timeline_days"] == 30


async def test_temperature_uses_timeline_days_and_motivation(seller_engine):
    seller_data = {
        "questions_answered": 4,
        "response_quality": 0.85,
        "timeline_days": 21,
        "motivation": "Job relocation",
    }
    result = await seller_engine._calculate_seller_temperature(seller_data)
    assert result["temperature"] == "hot"


async def test_create_seller_actions_includes_canonical_fields(seller_engine):
    pricing_result = SimpleNamespace(expected_roi=17.2, tier="A", final_price=680000)
    seller_data = {
        "motivation": "Relocation",
        "seller_motivation": "Relocation",
        "property_condition": "move-in ready",
        "timeline_days": 28,
        "asking_price": 700000,
        "mortgage_balance": 420000,
        "qualification_complete": True,
        "last_bot_interaction": "2026-02-16T00:00:00",
        "field_provenance": {"asking_price": "extracted"},
    }

    actions = await seller_engine._create_seller_actions(
        contact_id="c1",
        location_id="l1",
        temperature="warm",
        seller_data=seller_data,
        pricing_result=pricing_result,
        persona_data={},
    )

    updates = [a for a in actions if a["type"] == "update_custom_field"]
    updated_fields = {a["field"] for a in updates}

    assert "asking_price" in updated_fields
    assert "timeline_days" in updated_fields
    assert "qualification_complete" in updated_fields
    assert "field_provenance" in updated_fields


async def test_create_seller_actions_only_writes_changed_canonical_fields(seller_engine):
    previous_seller_data = {
        "seller_motivation": "Relocation",
        "property_condition": "move-in ready",
        "timeline_days": 28,
        "asking_price": 680000,
        "ai_valuation_price": 660000,
        "lead_value_tier": "A",
        "qualification_complete": True,
        "last_bot_interaction": "2026-02-16T00:00:00",
        "field_provenance": {"asking_price": "extracted"},
    }
    seller_data = {
        "seller_motivation": "Relocation",
        "property_condition": "move-in ready",
        "timeline_days": 28,
        "asking_price": 700000,  # changed
        "ai_valuation_price": 660000,
        "lead_value_tier": "A",
        "qualification_complete": True,
        "last_bot_interaction": "2026-02-16T00:00:00",
        "field_provenance": {"asking_price": "extracted"},
    }

    actions = await seller_engine._create_seller_actions(
        contact_id="c1",
        location_id="l1",
        temperature="warm",
        seller_data=seller_data,
        previous_seller_data=previous_seller_data,
        pricing_result=None,
        persona_data={},
    )

    updates = [a for a in actions if a["type"] == "update_custom_field"]
    updated_fields = {a["field"] for a in updates}

    assert "asking_price" in updated_fields
    assert "price_expectation" in updated_fields
    assert "timeline_days" not in updated_fields
    assert "property_condition" not in updated_fields
    assert "seller_motivation" not in updated_fields


async def test_create_seller_actions_fail_closed_blocks_canonical_writes(seller_engine):
    seller_data = {
        "seller_motivation": "Relocation",
        "property_condition": "move-in ready",
        "timeline_days": 30,
        "asking_price": 700000,
        "ai_valuation_price": 680000,
        "lead_value_tier": "A",
        "qualification_complete": True,
    }

    with (
        patch.object(
            JorgeSellerConfig,
            "validate_custom_field_mapping",
            return_value={"is_valid": False, "missing_fields": ["asking_price"], "resolved_fields": {}},
        ),
        patch.object(JorgeSellerConfig, "should_fail_on_missing_canonical_mapping", return_value=True),
    ):
        actions = await seller_engine._create_seller_actions(
            contact_id="c1",
            location_id="l1",
            temperature="warm",
            seller_data=seller_data,
            pricing_result=None,
            persona_data={},
        )

    assert any(a for a in actions if a["type"] == "add_tag" and a.get("tag") == "Canonical-Mapping-Missing")
    assert not any(a for a in actions if a["type"] == "update_custom_field")


async def test_ws3_hot_seller_offer_uses_strict_30_min_consult_type(seller_engine):
    tz = pytz.timezone("America/Los_Angeles")
    base_time = tz.localize(datetime(2026, 2, 17, 10, 0))
    slots = [
        TimeSlot(
            start_time=base_time + timedelta(hours=i),
            end_time=base_time + timedelta(hours=i, minutes=30),
            duration_minutes=30,
            appointment_type=AppointmentType.SELLER_CONSULTATION,
        )
        for i in range(3)
    ]

    scheduler = MagicMock()
    scheduler.HOT_SELLER_REQUIRED_SLOT_COUNT = 3
    scheduler.HOT_SELLER_APPOINTMENT_TYPE = AppointmentType.SELLER_CONSULTATION
    scheduler.get_hot_seller_consultation_slots = AsyncMock(return_value=slots)

    message, pending_data, actions, tracking = await seller_engine._build_hot_seller_slot_offer(
        scheduler=scheduler,
        contact_id="c-ws3",
    )

    assert "30 minute consultation" in message
    assert pending_data is not None
    assert pending_data["flow"] == "hot_seller_consultation_30min"
    assert len(pending_data["options"]) == 3
    assert all(opt["appointment_type"] == AppointmentType.SELLER_CONSULTATION.value for opt in pending_data["options"])
    assert actions == []
    assert tracking["appointment_slot_offer_sent"] is True


async def test_ws3_hot_seller_offer_falls_back_when_fewer_than_three_slots(seller_engine):
    tz = pytz.timezone("America/Los_Angeles")
    base_time = tz.localize(datetime(2026, 2, 17, 10, 0))
    slots = [
        TimeSlot(
            start_time=base_time + timedelta(hours=i),
            end_time=base_time + timedelta(hours=i, minutes=30),
            duration_minutes=30,
            appointment_type=AppointmentType.SELLER_CONSULTATION,
        )
        for i in range(2)
    ]

    scheduler = MagicMock()
    scheduler.HOT_SELLER_REQUIRED_SLOT_COUNT = 3
    scheduler.HOT_SELLER_APPOINTMENT_TYPE = AppointmentType.SELLER_CONSULTATION
    scheduler.get_hot_seller_consultation_slots = AsyncMock(return_value=slots)
    scheduler.get_manual_scheduling_message.return_value = "Manual scheduling fallback"
    scheduler.build_manual_scheduling_actions.return_value = [
        GHLAction(type=ActionType.ADD_TAG, tag="Needs-Manual-Scheduling")
    ]

    message, pending_data, actions, tracking = await seller_engine._build_hot_seller_slot_offer(
        scheduler=scheduler,
        contact_id="c-ws3",
    )

    assert message == "Manual scheduling fallback"
    assert pending_data is None
    assert any(a["type"] == "add_tag" and a["tag"] == "Needs-Manual-Scheduling" for a in actions)
    assert tracking["appointment_slot_offer_sent"] is False
