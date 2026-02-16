"""WS-6 focused tests for metrics schema, dashboard deltas, and A/B guardrails."""

import pytest

from ghl_real_estate_ai.services.jorge.ab_testing_service import ABTestingService
from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector
from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker


@pytest.fixture(autouse=True)
def reset_ws6_singletons():
    """Keep singleton state isolated per test."""
    BotMetricsCollector.reset()
    PerformanceTracker.reset()
    ABTestingService.reset()
    yield
    BotMetricsCollector.reset()
    PerformanceTracker.reset()
    ABTestingService.reset()


def test_ws6_metrics_events_follow_stable_schema():
    collector = BotMetricsCollector()
    collector.record_bot_interaction("lead", duration_ms=180.0, success=True, cache_hit=False)
    collector.record_handoff("lead", "seller", success=True, duration_ms=65.0)

    schema = collector.get_required_event_schema()
    events = collector.get_recent_events(limit=10)

    assert schema["event_version"] == "ws6.v1"
    assert len(events) == 2

    for event in events:
        for key in schema["required_event_keys"]:
            assert key in event
        expected_payload_keys = schema["payload_schema"][event["event_name"]]
        for payload_key in expected_payload_keys:
            assert payload_key in event["payload"]


def test_ws6_dashboard_snapshot_exposes_deltas_vs_baseline():
    collector = BotMetricsCollector()
    collector.record_bot_interaction("lead", duration_ms=200.0, success=True)
    collector.record_bot_interaction("buyer", duration_ms=100.0, success=True)

    baseline = {
        "funnel": 0.6,
        "efficiency": 100.0,
        "completeness": 0.7,
        "opt_out": 0.05,
    }

    snapshot = collector.get_dashboard_kpi_snapshot(
        baseline=baseline,
        completeness_rate=0.8,
        opt_out_rate=0.02,
    )

    assert snapshot["version"] == "ws6.v1"
    assert snapshot["kpis"]["funnel"]["delta"] == pytest.approx(0.4)
    assert snapshot["kpis"]["efficiency"]["delta"] == pytest.approx(50.0)
    assert snapshot["kpis"]["completeness"]["delta"] == pytest.approx(0.1)
    assert snapshot["kpis"]["opt_out"]["delta"] == pytest.approx(-0.03)


@pytest.mark.asyncio
async def test_ws6_performance_events_and_kpi_deltas():
    tracker = PerformanceTracker()
    await tracker.track_operation("lead_bot", "process", 100.0, success=True)

    schema = tracker.get_required_event_schema()
    events = tracker.get_recent_events(event_name="operation_tracked", limit=5)
    assert schema["event_version"] == "ws6.v1"
    assert len(events) == 1

    baseline = {
        "lead_bot": {
            "p95": 50.0,
            "success_rate": 0.5,
        }
    }
    deltas = await tracker.get_kpi_deltas_vs_baseline(baseline=baseline)

    assert deltas["version"] == "ws6.v1"
    assert deltas["bots"]["lead_bot"]["p95_delta"] == pytest.approx(50.0)
    assert deltas["bots"]["lead_bot"]["success_delta"] == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_ws6_guardrail_disables_variant_on_opt_out_breach():
    service = ABTestingService()
    service.create_experiment(
        "guardrail_opt_out",
        ["risky", "safe"],
        traffic_split={"risky": 1.0, "safe": 0.0},
    )
    service.set_guardrails(
        "guardrail_opt_out",
        min_samples=5,
        opt_out_rate_threshold=0.2,
        compliance_violation_rate_threshold=0.9,
    )

    for i in range(5):
        cid = f"contact_{i}"
        assigned = await service.get_variant("guardrail_opt_out", cid)
        assert assigned == "risky"
        outcome = await service.record_outcome("guardrail_opt_out", cid, assigned, "opt_out")

    assert outcome["guardrail_triggered"] is True

    status = service.get_guardrail_status("guardrail_opt_out")
    assert "risky" in status["disabled_variants"]
    assert any("opt_out_rate_threshold" in event["reasons"] for event in status["events"])

    reassigned = await service.get_variant("guardrail_opt_out", "contact_new")
    assert reassigned == "safe"


@pytest.mark.asyncio
async def test_ws6_guardrail_pauses_when_all_variants_disabled():
    service = ABTestingService()
    service.create_experiment(
        "guardrail_pause",
        ["risky", "safe"],
        traffic_split={"risky": 1.0, "safe": 0.0},
    )
    service.set_guardrails(
        "guardrail_pause",
        min_samples=1,
        opt_out_rate_threshold=0.5,
        compliance_violation_rate_threshold=0.9,
    )

    first = await service.get_variant("guardrail_pause", "first")
    assert first == "risky"
    await service.record_outcome("guardrail_pause", "first", first, "opt_out")

    second = await service.get_variant("guardrail_pause", "second")
    assert second == "safe"
    pause_outcome = await service.record_outcome("guardrail_pause", "second", second, "opt_out")

    assert pause_outcome["guardrail_triggered"] is True

    status = service.get_guardrail_status("guardrail_pause")
    assert status["status"] == "paused"
    assert set(status["disabled_variants"]) == {"risky", "safe"}

    with pytest.raises(ValueError, match="status=paused"):
        await service.get_variant("guardrail_pause", "third")
