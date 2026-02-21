"""Unit tests for TierManager — tier enforcement, limits, daily reset."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from devops_suite.billing.tier_manager import TierLimitExceeded, TierManager
from devops_suite.config import TIER_LIMITS, Tier


@pytest.fixture
def mgr():
    m = TierManager()
    m.register_tenant("t1", Tier.STARTER)
    m.register_tenant("t2", Tier.PRO)
    m.register_tenant("t3", Tier.TEAM)
    return m


class TestTenantRegistration:
    def test_register_sets_tier(self, mgr):
        assert mgr.get_tier("t1") == Tier.STARTER

    def test_unknown_tenant_returns_none(self, mgr):
        assert mgr.get_tier("unknown") is None

    def test_get_limits(self, mgr):
        limits = mgr.get_limits("t1")
        assert limits == TIER_LIMITS[Tier.STARTER]

    def test_unknown_tenant_limits_none(self, mgr):
        assert mgr.get_limits("unknown") is None

    def test_usage_counter_initialized(self, mgr):
        usage = mgr.get_usage("t1")
        assert usage is not None
        assert usage.events_today == 0

    def test_upgrade_tier(self, mgr):
        mgr.upgrade_tier("t1", Tier.PRO)
        assert mgr.get_tier("t1") == Tier.PRO


class TestCheckAndIncrement:
    def test_within_limits(self, mgr):
        result = mgr.check_and_increment("t1", "events_per_day", 1)
        assert result is True
        assert mgr.get_usage("t1").events_today == 1

    def test_exceeds_limit_raises(self, mgr):
        starter_limit = TIER_LIMITS[Tier.STARTER]["events_per_day"]
        # Fill up to the limit
        mgr.check_and_increment("t1", "events_per_day", starter_limit)
        # One more should raise
        with pytest.raises(TierLimitExceeded) as exc_info:
            mgr.check_and_increment("t1", "events_per_day", 1)
        assert exc_info.value.resource == "events_per_day"
        assert exc_info.value.tier == "starter"

    def test_unlimited_resource_always_succeeds(self, mgr):
        # Team tier has unlimited pipelines
        for _ in range(100):
            mgr.check_and_increment("t3", "pipelines", 1)
        assert mgr.get_usage("t3").pipelines_total == 100

    def test_unknown_tenant_raises(self, mgr):
        with pytest.raises(ValueError, match="Unknown tenant"):
            mgr.check_and_increment("unknown", "events_per_day", 1)

    def test_prompt_renders_tracked(self, mgr):
        mgr.check_and_increment("t1", "prompt_renders_per_day", 5)
        assert mgr.get_usage("t1").prompt_renders_today == 5

    def test_pipeline_runs_tracked(self, mgr):
        mgr.check_and_increment("t2", "pipeline_runs_per_day", 10)
        assert mgr.get_usage("t2").pipeline_runs_today == 10


class TestDailyReset:
    def test_resets_daily_counters(self, mgr):
        mgr.check_and_increment("t1", "events_per_day", 100)
        usage = mgr.get_usage("t1")
        assert usage.events_today == 100

        # Simulate next day by backdating last_reset
        usage.last_reset = datetime.utcnow() - timedelta(days=1)
        mgr.check_and_increment("t1", "events_per_day", 1)
        assert usage.events_today == 1  # Reset + 1

    def test_does_not_reset_total_counters(self, mgr):
        mgr.check_and_increment("t1", "prompts", 10)
        usage = mgr.get_usage("t1")
        usage.last_reset = datetime.utcnow() - timedelta(days=1)
        mgr.check_and_increment("t1", "prompts", 5)
        assert usage.prompts_total == 15  # Never reset


class TestTierLimitExceededException:
    def test_exception_message(self):
        exc = TierLimitExceeded("events_per_day", 10000, 10001, "starter")
        assert "events_per_day" in str(exc)
        assert "10000" in str(exc)
        assert "starter" in str(exc)
