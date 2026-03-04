from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from portal_api import app
from portal_api.accelerator.service import get_accelerator_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_accelerator_service_cache() -> None:
    get_accelerator_service.cache_clear()


def _diagnose(profile: str, engagement_id: str = "eng-demo-1") -> str:
    response = client.post(
        "/api/v2/intake/diagnose",
        json={
            "engagement_id": engagement_id,
            "vertical_profile": profile,
            "client_name": "Acme Client",
            "goals": ["increase conversion"],
            "context": {"channels": ["sms"], "crm_system": "ghl", "event_volume_14d": 50},
        },
    )
    assert response.status_code == 200
    return response.json()["engagement_id"]


def test_intake_validation_missing_required_fields_returns_422() -> None:
    response = client.post("/api/v2/intake/diagnose", json={"vertical_profile": "real_estate"})
    assert response.status_code == 422


def test_intake_diagnose_returns_draft_with_readiness() -> None:
    response = client.post(
        "/api/v2/intake/diagnose",
        json={
            "engagement_id": "eng-realestate-1",
            "vertical_profile": "real_estate",
            "client_name": "Jorge Team",
            "goals": ["improve 5-minute response SLA", "increase qualified leads"],
            "context": {"channels": ["sms", "web_form"], "event_volume_14d": 120},
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "draft"
    assert payload["vertical_profile"] == "real_estate"
    assert 0 <= payload["readiness_score"] <= 100
    assert payload["audit_id"]


def test_workflow_bootstrap_returns_blueprint() -> None:
    _diagnose("professional_services", "eng-pro-1")
    response = client.post(
        "/api/v2/workflows/bootstrap",
        json={
            "engagement_id": "eng-pro-1",
            "delivery_window_days": 14,
            "channels": ["email"],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "active"
    assert payload["vertical_profile"] == "professional_services"
    assert "automation_sequence" in payload["blueprint"]
    assert payload["audit_id"]


@pytest.mark.parametrize(
    ("profile", "baseline", "current"),
    [
        (
            "real_estate",
            {"response_sla_seconds": 300.0, "qualified_leads": 10.0, "attributed_revenue": 10000.0},
            {"response_sla_seconds": 120.0, "qualified_leads": 15.0, "attributed_revenue": 17000.0},
        ),
        (
            "professional_services",
            {"review_sla_hours": 24.0, "throughput": 20.0, "escalation_rate": 0.2, "hours_saved": 0.0},
            {"review_sla_hours": 8.0, "throughput": 35.0, "escalation_rate": 0.1, "hours_saved": 18.0},
        ),
        (
            "ecommerce_voice",
            {"ttfb_ms": 1800.0, "resolution_rate": 0.5, "fallback_rate": 0.25},
            {"ttfb_ms": 900.0, "resolution_rate": 0.72, "fallback_rate": 0.11},
        ),
    ],
)
def test_proof_pack_generation_succeeds_for_each_vertical(
    profile: str, baseline: dict[str, float], current: dict[str, float]
) -> None:
    engagement_id = f"eng-{profile}"
    _diagnose(profile, engagement_id)
    client.post("/api/v2/workflows/bootstrap", json={"engagement_id": engagement_id})

    response = client.post(
        "/api/v2/reports/proof-pack",
        json={
            "engagement_id": engagement_id,
            "event_count": 22,
            "lookback_days": 14,
            "baseline_kpis": baseline,
            "current_kpis": current,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "delivered"
    assert payload["proof_pack"]["vertical_profile"] == profile
    assert payload["proof_pack"]["executive_summary"]
    assert payload["audit_id"]


def test_proof_pack_generation_fails_for_missing_kpi_source() -> None:
    _diagnose("real_estate", "eng-missing-source")
    response = client.post(
        "/api/v2/reports/proof-pack",
        json={
            "engagement_id": "eng-missing-source",
            "event_count": 20,
            "missing_sources": ["crm_sync"],
            "baseline_kpis": {"response_sla_seconds": 280.0, "qualified_leads": 8.0, "attributed_revenue": 8000.0},
            "current_kpis": {"response_sla_seconds": 140.0, "qualified_leads": 11.0, "attributed_revenue": 12000.0},
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_proof_pack_request"


def test_proof_pack_generation_fails_for_empty_event_stream() -> None:
    _diagnose("ecommerce_voice", "eng-empty-stream")
    response = client.post(
        "/api/v2/reports/proof-pack",
        json={
            "engagement_id": "eng-empty-stream",
            "event_count": 0,
            "baseline_kpis": {"ttfb_ms": 1800.0, "resolution_rate": 0.5, "fallback_rate": 0.25},
            "current_kpis": {"ttfb_ms": 900.0, "resolution_rate": 0.72, "fallback_rate": 0.11},
        },
    )
    assert response.status_code == 400
    assert "event_count" in response.json()["error"]["message"]


def test_partial_telemetry_is_carried_to_risks() -> None:
    _diagnose("professional_services", "eng-partial")
    response = client.post(
        "/api/v2/reports/proof-pack",
        json={
            "engagement_id": "eng-partial",
            "event_count": 9,
            "partial_telemetry": True,
            "baseline_kpis": {"review_sla_hours": 24.0, "throughput": 20.0, "escalation_rate": 0.2, "hours_saved": 0.0},
            "current_kpis": {"review_sla_hours": 8.0, "throughput": 35.0, "escalation_rate": 0.1, "hours_saved": 18.0},
        },
    )
    assert response.status_code == 200
    risks = response.json()["proof_pack"]["risks"]
    assert any("Partial telemetry" in risk for risk in risks)


def test_idempotent_report_regeneration_returns_same_generated_at() -> None:
    _diagnose("real_estate", "eng-idempotent")
    payload = {
        "engagement_id": "eng-idempotent",
        "event_count": 33,
        "baseline_kpis": {"response_sla_seconds": 300.0, "qualified_leads": 10.0, "attributed_revenue": 10000.0},
        "current_kpis": {"response_sla_seconds": 120.0, "qualified_leads": 15.0, "attributed_revenue": 17000.0},
    }
    first = client.post("/api/v2/reports/proof-pack", json=payload)
    second = client.post("/api/v2/reports/proof-pack", json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["proof_pack"]["generated_at"] == second.json()["proof_pack"]["generated_at"]


def test_parallel_engagement_creation_is_reliable() -> None:
    def _create(i: int) -> int:
        response = client.post(
            "/api/v2/intake/diagnose",
            json={
                "engagement_id": f"eng-parallel-{i}",
                "vertical_profile": "real_estate",
                "client_name": f"Client {i}",
                "goals": ["increase conversion"],
                "context": {"channels": ["sms"], "event_volume_14d": 10 + i},
            },
        )
        return response.status_code

    with ThreadPoolExecutor(max_workers=8) as pool:
        codes = list(pool.map(_create, range(20)))
    assert all(code == 200 for code in codes)


def test_report_fetch_includes_audit_trail() -> None:
    _diagnose("ecommerce_voice", "eng-audit")
    client.post("/api/v2/workflows/bootstrap", json={"engagement_id": "eng-audit"})
    client.post(
        "/api/v2/reports/proof-pack",
        json={
            "engagement_id": "eng-audit",
            "event_count": 5,
            "baseline_kpis": {"ttfb_ms": 1800.0, "resolution_rate": 0.5, "fallback_rate": 0.25},
            "current_kpis": {"ttfb_ms": 900.0, "resolution_rate": 0.72, "fallback_rate": 0.11},
        },
    )
    response = client.get("/api/v2/reports/eng-audit")
    assert response.status_code == 200
    payload = response.json()
    assert payload["proof_pack"]["engagement_id"] == "eng-audit"
    assert len(payload["audit_trail"]) >= 2


def test_report_fetch_returns_404_when_missing() -> None:
    response = client.get("/api/v2/reports/eng-does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "report_not_found"
