from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from ghl_real_estate_ai.services.jorge.jorge_followup_engine import FollowUpType, JorgeFollowUpEngine

pytestmark = pytest.mark.unit

@pytest.fixture
def followup_engine():
    return JorgeFollowUpEngine(AsyncMock(), AsyncMock())


@pytest.mark.asyncio
async def test_initial_sequence_determination(followup_engine):
    seller_data = {
        "seller_temperature": "cold",
        "last_contact_date": (datetime.now() - timedelta(days=2)).isoformat(),
        "questions_answered": 1,
    }

    result = await followup_engine._determine_follow_up_type(seller_data, "time_based")

    # Logic prioritizes qualification retry if < 4 questions answered and not hot
    assert result["type"] == FollowUpType.QUALIFICATION_RETRY
    # Position logic for qualification retry is based on days since contact too?
    # Actually QUALIFICATION_RETRY uses the same scheduling logic in _schedule_next_follow_up but
    # determine logic just sets the type.
    # Let's check what position is returned.
    # _determine_follow_up_type calls _get_initial_sequence_position(2) -> 1
    assert result["position"] == 1


@pytest.mark.asyncio
async def test_cold_monthly_sequence_determination(followup_engine):
    seller_data = {
        "seller_temperature": "cold",
        "last_contact_date": (datetime.now() - timedelta(days=45)).isoformat(),
        "questions_answered": 4,
    }

    result = await followup_engine._determine_follow_up_type(seller_data, "time_based")

    assert result["type"] == FollowUpType.COLD_MONTHLY_NURTURE
    assert result["cadence_days"] == 30
    assert result["days_since_contact"] >= 45


@pytest.mark.asyncio
async def test_generate_followup_message(followup_engine):
    seller_data = {"contact_name": "John"}
    config = {"type": FollowUpType.HOT_DAILY_NURTURE, "temperature": "hot", "position": 1, "days_since_contact": 2}

    message = await followup_engine._generate_follow_up_message(seller_data, config, "id")

    assert message.message_type == FollowUpType.HOT_DAILY_NURTURE
    assert len(message.content) > 0
    assert "John" in message.content


@pytest.mark.asyncio
async def test_schedule_next_followup(followup_engine):
    seller_data = {}
    config = {
        "type": FollowUpType.WARM_WEEKLY_NURTURE,
        "temperature": "warm",
        "position": 1,
        "days_since_contact": 2,
        "cadence_days": 7,
        "retry_ceiling": 12,
    }

    next_sched = await followup_engine._schedule_next_follow_up(seller_data, config)

    assert next_sched is not None
    scheduled_date = datetime.fromisoformat(next_sched["scheduled_date"])
    assert scheduled_date > datetime.now()
    assert (scheduled_date - datetime.now()).total_seconds() >= 6 * 24 * 3600


@pytest.mark.asyncio
async def test_hot_deescalates_to_warm_after_non_response_streak(followup_engine):
    seller_data = {
        "seller_temperature": "hot",
        "questions_answered": 4,
        "followup_no_response_streak": 3,
    }

    result = await followup_engine._determine_follow_up_type(seller_data, "time_based")

    assert result["temperature"] == "warm"
    assert result["type"] == FollowUpType.WARM_WEEKLY_NURTURE
    assert result["deescalated"] is True


@pytest.mark.asyncio
async def test_schedule_stops_when_retry_ceiling_reached(followup_engine):
    seller_data = {}
    config = {
        "type": FollowUpType.COLD_MONTHLY_NURTURE,
        "temperature": "cold",
        "position": 6,
        "days_since_contact": 60,
        "cadence_days": 30,
        "retry_ceiling": 6,
    }

    next_sched = await followup_engine._schedule_next_follow_up(seller_data, config)

    assert next_sched is None


@pytest.mark.asyncio
async def test_followup_actions_include_manual_escalation_tags(followup_engine):
    config = {
        "type": FollowUpType.WARM_WEEKLY_NURTURE,
        "temperature": "warm",
        "position": 3,
        "no_response_streak": 3,
        "escalation_required": True,
    }

    actions = await followup_engine._create_follow_up_actions("contact-1", "location-1", config, {})
    added_tags = {action["tag"] for action in actions if action.get("type") == "add_tag"}

    assert "Manual-Review-Required" in added_tags
    assert "FollowUp-Escalation" in added_tags
