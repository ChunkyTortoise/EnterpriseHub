import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
from ghl_real_estate_ai.services.jorge.jorge_followup_engine import JorgeFollowUpEngine, FollowUpType

@pytest.fixture
def followup_engine():
    return JorgeFollowUpEngine(AsyncMock(), AsyncMock())

@pytest.mark.asyncio
async def test_initial_sequence_determination(followup_engine):
    seller_data = {
        "seller_temperature": "cold",
        "last_contact_date": (datetime.now() - timedelta(days=2)).isoformat(),
        "questions_answered": 1
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
async def test_long_term_sequence_determination(followup_engine):
    seller_data = {
        "seller_temperature": "cold",
        "last_contact_date": (datetime.now() - timedelta(days=45)).isoformat(),
        "questions_answered": 4
    }
    
    result = await followup_engine._determine_follow_up_type(seller_data, "time_based")
    
    assert result["type"] == FollowUpType.LONG_TERM_NURTURE
    assert result["days_since_contact"] >= 45

@pytest.mark.asyncio
async def test_generate_followup_message(followup_engine):
    seller_data = {"contact_name": "John"}
    config = {
        "type": FollowUpType.INITIAL_NURTURE,
        "temperature": "cold",
        "position": 1,
        "days_since_contact": 2
    }
    
    message = await followup_engine._generate_follow_up_message(seller_data, config, "id")
    
    assert message.message_type == FollowUpType.INITIAL_NURTURE
    assert len(message.content) > 0
    assert "John" in message.content

@pytest.mark.asyncio
async def test_schedule_next_followup(followup_engine):
    seller_data = {}
    config = {
        "type": FollowUpType.INITIAL_NURTURE,
        "position": 1, # Day 2
        "days_since_contact": 2
    }
    
    # Next is day 5 (from index 1 in [2, 5, 8...])
    # So delta is 3 days
    
    next_sched = await followup_engine._schedule_next_follow_up(seller_data, config)
    
    assert next_sched is not None
    scheduled_date = datetime.fromisoformat(next_sched["scheduled_date"])
    assert scheduled_date > datetime.now()
    assert (scheduled_date - datetime.now()).days >= 2 # rough check
