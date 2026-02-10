from fastapi.testclient import TestClient
import pytest

import jorge_fastapi_lead_bot as lead_api
from runtime_metrics import RuntimeMetricsRegistry


class FakeHealthResponse:
    def __init__(self, status_code=200):
        self.status_code = status_code


class FakeGHLClient:
    def check_health(self):
        return FakeHealthResponse(200)

    async def update_contact_custom_fields(self, contact_id, updates):
        return True

    async def add_contact_tags(self, contact_id, tags):
        return True

    async def send_message(self, contact_id, message):
        return {"sent": True}


@pytest.fixture
def metrics_client(monkeypatch):
    monkeypatch.setattr(lead_api, "metrics_registry", RuntimeMetricsRegistry())
    monkeypatch.setattr(lead_api, "ghl_client", FakeGHLClient())

    call_count = {"value": 0}

    async def fake_analyze_lead_for_jorge(message, contact_id=None, location_id=None, context=None, force_ai=False):
        call_count["value"] += 1
        cache_hit = (call_count["value"] % 2 == 0)
        return {
            "lead_score": 82,
            "lead_temperature": "HOT",
            "jorge_priority": "high",
            "estimated_commission": 12000,
            "actions": [],
            "follow_up": None,
            "performance": {
                "response_time_ms": 35,
                "analysis_type": "pattern",
                "cache_hit": cache_hit,
                "five_minute_compliant": True,
                "claude_used": False,
            },
        }

    monkeypatch.setattr(lead_api, "analyze_lead_for_jorge", fake_analyze_lead_for_jorge)
    monkeypatch.setattr(
        lead_api,
        "get_five_minute_compliance_status",
        lambda: {
            "avg_response_time": 0.04,
            "total_responses": 2,
            "compliance_rate": 1.0,
            "last_24h_violations": [],
        },
    )

    return TestClient(lead_api.app)


def test_middleware_increments_request_metrics(metrics_client):
    before = lead_api.metrics_registry.snapshot()["counters"]["requests_total"]
    response = metrics_client.get("/health")
    after = lead_api.metrics_registry.snapshot()["counters"]["requests_total"]

    assert response.status_code == 200
    assert after == before + 1


def test_performance_and_metrics_return_live_values(metrics_client):
    payload = {
        "contact_id": "contact-obs-1",
        "location_id": "loc-obs-1",
        "message": "Need to buy in Plano and ready this month",
        "contact_data": {"source": "test"},
    }

    first = metrics_client.post("/analyze-lead", json=payload)
    second = metrics_client.post("/analyze-lead", json=payload)
    perf = metrics_client.get("/performance")
    metrics = metrics_client.get("/metrics")

    assert first.status_code == 200
    assert second.status_code == 200
    assert perf.status_code == 200
    assert metrics.status_code == 200

    perf_body = perf.json()
    current = perf_body["current_performance"]
    assert current["total_requests"] >= 2
    assert current["avg_response_time_ms"] != 150
    assert current["p95_response_time_ms"] > 0
    assert 0.0 <= current["cache_hit_rate"] <= 1.0
    assert 0.0 <= current["ghl_success_rate"] <= 1.0

    metrics_body = metrics.json()["runtime_metrics"]
    counters = metrics_body["counters"]
    assert counters["requests_total"] >= 3
    assert counters["ghl_calls_total"] >= 2
    assert counters["latency_ms_count"] >= 3
    assert "feature_flag_evaluations_total" in counters
    assert "growth_feature_events_total" in counters

    growth_rollout = metrics.json()["growth_rollout"]
    assert "flags" in growth_rollout
    assert "writeback_toggles" in growth_rollout
    assert "lead_source" in growth_rollout["writeback_toggles"]
    assert "conversion_feedback" in growth_rollout["writeback_toggles"]


def test_metrics_include_growth_feature3_and_feature4_event_keys(metrics_client):
    analysis_result = {"lead_score": 90, "jorge_priority": "high", "lead_temperature": "HOT"}

    lead_api._apply_ab_response_style_testing(
        analysis_result=analysis_result,
        contact_id="contact-obs-ab-1",
        lead_source="facebook",
        feature_enabled=False,
        feature_reason="flag_disabled",
    )
    lead_api._apply_ab_response_style_testing(
        analysis_result={"lead_score": 90, "jorge_priority": "high", "lead_temperature": "HOT"},
        contact_id="contact-obs-ab-1",
        lead_source="facebook",
        feature_enabled=True,
        feature_reason="enabled",
    )
    lead_api._evaluate_sla_handoff_thresholds(
        analysis_result={"lead_score": 90, "jorge_priority": "high"},
        follow_up_data={"timing_bucket": "immediate"},
        lead_source="facebook",
        elapsed_processing_ms=4000,
        feature_enabled=True,
        feature_reason="enabled",
    )
    lead_api._evaluate_sla_handoff_thresholds(
        analysis_result={"lead_score": 50, "jorge_priority": "normal"},
        follow_up_data={"timing_bucket": "nurture"},
        lead_source="facebook",
        elapsed_processing_ms=1000,
        feature_enabled=False,
        feature_reason="flag_disabled",
    )

    metrics = metrics_client.get("/metrics")
    assert metrics.status_code == 200
    growth_events = metrics.json()["runtime_metrics"]["counters"]["growth_feature_events_total"]

    assert growth_events["ab_response_style_testing:assignment_observed"] >= 2
    assert growth_events["ab_response_style_testing:applied"] >= 1
    assert growth_events["ab_response_style_testing:bypassed_flag_disabled"] >= 1
    assert (
        growth_events.get("ab_response_style_testing:variant_a", 0)
        + growth_events.get("ab_response_style_testing:variant_b", 0)
        >= 1
    )
    assert growth_events["sla_handoff_thresholds:observed"] >= 2
    assert growth_events["sla_handoff_thresholds:handoff_recommended"] >= 1
    assert growth_events["sla_handoff_thresholds:bypassed_flag_disabled"] >= 1
