"""Tests for WS-6 observability payload builder."""

import pytest

from ghl_real_estate_ai.services.jorge.ab_testing_service import ABTestingService
from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector
from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker
from ghl_real_estate_ai.services.jorge.ws6_reporting import build_ws6_observability_payload

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def reset_singletons():
    BotMetricsCollector.reset()
    PerformanceTracker.reset()
    ABTestingService.reset()
    yield
    BotMetricsCollector.reset()
    PerformanceTracker.reset()
    ABTestingService.reset()


async def test_build_ws6_observability_payload_includes_expected_sections():
    collector = BotMetricsCollector()
    tracker = PerformanceTracker()

    collector.record_bot_interaction("lead", duration_ms=120.0, success=True)
    collector.record_handoff("lead", "buyer", success=True, duration_ms=55.0)
    await tracker.track_operation("lead_bot", "process", 120.0, success=True)

    payload = await build_ws6_observability_payload(include_recent_events=True)

    assert payload["available"] is True
    assert payload["version"] == "ws6.v1"
    assert "dashboard" in payload
    assert "event_schemas" in payload
    assert "performance_deltas" in payload
    assert "experiments" in payload
    assert "recent_events" in payload
    assert len(payload["recent_events"]["bot_metrics"]) >= 1
    assert len(payload["recent_events"]["performance"]) >= 1


async def test_build_ws6_observability_payload_returns_guardrail_state():
    ab_service = ABTestingService()
    ab_service.create_experiment("ws6_guardrails", ["a", "b"])

    payload = await build_ws6_observability_payload(include_recent_events=False)

    assert payload["experiments"]["active"]
    assert any(
        item.get("experiment_id") == "ws6_guardrails" for item in payload["experiments"]["guardrails"]
    )
