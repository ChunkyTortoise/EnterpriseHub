from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig
from ghl_real_estate_ai.services.jorge.jorge_followup_engine import FollowUpSchedule
from ghl_real_estate_ai.services.jorge.jorge_followup_scheduler import JorgeFollowUpScheduler


@pytest.fixture
def scheduler(monkeypatch):
    scheduler = JorgeFollowUpScheduler.__new__(JorgeFollowUpScheduler)
    scheduler.schedule_config = FollowUpSchedule()
    scheduler.lifecycle_policy = JorgeSellerConfig.get_followup_lifecycle_policy()
    scheduler.logger = Mock()
    monkeypatch.setattr(scheduler, "_is_business_hours", lambda: True)
    return scheduler


async def test_hot_daily_trigger_allows_after_24_hours(scheduler):
    seller_data = {
        "seller_temperature": "hot",
        "last_followup_date": (datetime.now() - timedelta(hours=25)).isoformat(),
    }

    should_trigger = await scheduler._should_trigger_follow_up(seller_data)

    assert should_trigger is True


async def test_hot_daily_trigger_blocks_before_24_hours(scheduler):
    seller_data = {
        "seller_temperature": "hot",
        "last_followup_date": (datetime.now() - timedelta(hours=12)).isoformat(),
    }

    should_trigger = await scheduler._should_trigger_follow_up(seller_data)

    assert should_trigger is False


async def test_suppressed_contact_never_triggers_followup(scheduler):
    seller_data = {
        "seller_temperature": "warm",
        "followup_suppressed": True,
        "last_followup_date": (datetime.now() - timedelta(days=10)).isoformat(),
    }

    should_trigger = await scheduler._should_trigger_follow_up(seller_data)

    assert should_trigger is False


async def test_suppression_tags_block_followup(scheduler):
    seller_data = {
        "seller_temperature": "cold",
        "tags": ["AI-Off", "Needs Qualifying"],
        "last_followup_date": (datetime.now() - timedelta(days=40)).isoformat(),
    }

    should_trigger = await scheduler._should_trigger_follow_up(seller_data)

    assert should_trigger is False


async def test_hot_deescalation_requires_weekly_gap(scheduler):
    seller_data = {
        "seller_temperature": "hot",
        "followup_no_response_streak": 3,
        "last_followup_date": (datetime.now() - timedelta(days=2)).isoformat(),
    }

    should_trigger = await scheduler._should_trigger_follow_up(seller_data)

    assert should_trigger is False


async def test_retry_ceiling_blocks_additional_followups(scheduler):
    seller_data = {
        "seller_temperature": "warm",
        "followup_attempts_by_stage": {"warm": scheduler.lifecycle_policy["retry_ceiling"]["warm"]},
        "last_followup_date": (datetime.now() - timedelta(days=14)).isoformat(),
    }

    should_trigger = await scheduler._should_trigger_follow_up(seller_data)

    assert should_trigger is False
