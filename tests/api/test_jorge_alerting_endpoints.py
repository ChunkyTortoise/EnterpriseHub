import pytest
pytestmark = pytest.mark.integration

"""
Test suite for Jorge Alerting API endpoints.

Tests all 5 endpoints:
    GET  /api/jorge/alerts
    POST /api/jorge/alerts/{alert_id}/acknowledge
    GET  /api/jorge/alerts/{alert_id}/status
    GET  /api/jorge/alert-rules
    PATCH /api/jorge/alert-rules/{rule_name}
"""

import time
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from ghl_real_estate_ai.api.main import app
from ghl_real_estate_ai.services.jorge.alerting_service import (

@pytest.mark.integration
    Alert,
    AlertingService,
    AlertRule,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_alerting_singleton():
    """Reset AlertingService singleton before each test."""
    AlertingService.reset()
    yield
    AlertingService.reset()


def _make_alert(
    alert_id: str = "abc12345",
    rule_name: str = "high_error_rate",
    severity: str = "critical",
    acknowledged: bool = False,
) -> Alert:
    """Create a test Alert instance."""
    return Alert(
        id=alert_id,
        rule_name=rule_name,
        severity=severity,
        message=f"[{severity.upper()}] {rule_name} triggered",
        triggered_at=time.time() - 60,
        performance_stats={"error_rate": 0.08},
        channels_sent=["slack"],
        acknowledged=acknowledged,
        acknowledged_at=time.time() if acknowledged else None,
        acknowledged_by="tester" if acknowledged else None,
    )


# ── GET /api/jorge/alerts ─────────────────────────────────────────────


class TestListAlerts:
    """Tests for the list alerts endpoint."""

    def test_list_alerts_empty(self):
        """Returns empty list when no alerts exist."""
        response = client.get("/api/jorge/alerts")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_alerts_returns_alerts(self):
        """Returns alerts from alert history."""
        svc = AlertingService()
        alert = _make_alert()
        svc._alerts.append(alert)

        response = client.get("/api/jorge/alerts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "abc12345"
        assert data[0]["rule_name"] == "high_error_rate"
        assert data[0]["severity"] == "critical"

    def test_list_alerts_active_only(self):
        """Filters to only unacknowledged alerts when active_only=true."""
        svc = AlertingService()
        svc._alerts.append(_make_alert(alert_id="active1", acknowledged=False))
        svc._alerts.append(_make_alert(alert_id="acked1", acknowledged=True))

        response = client.get("/api/jorge/alerts?active_only=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "active1"

    def test_list_alerts_with_limit(self):
        """Respects the limit query parameter."""
        svc = AlertingService()
        for i in range(5):
            svc._alerts.append(_make_alert(alert_id=f"alert_{i}"))

        response = client.get("/api/jorge/alerts?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


# ── POST /api/jorge/alerts/{alert_id}/acknowledge ─────────────────────


class TestAcknowledgeAlert:
    """Tests for the acknowledge alert endpoint."""

    def test_acknowledge_alert_success(self):
        """Acknowledges an existing alert."""
        svc = AlertingService()
        svc._alerts.append(_make_alert(alert_id="ack_me"))

        response = client.post(
            "/api/jorge/alerts/ack_me/acknowledge",
            json={"acknowledged_by": "operator"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["alert_id"] == "ack_me"
        assert data["acknowledged_by"] == "operator"
        assert "time_to_ack_seconds" in data

    def test_acknowledge_alert_without_name(self):
        """Acknowledges without specifying acknowledged_by."""
        svc = AlertingService()
        svc._alerts.append(_make_alert(alert_id="ack_anon"))

        response = client.post(
            "/api/jorge/alerts/ack_anon/acknowledge",
            json={},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["acknowledged_by"] is None

    def test_acknowledge_alert_not_found(self):
        """Returns 404 for non-existent alert ID."""
        response = client.post(
            "/api/jorge/alerts/nonexistent/acknowledge",
            json={"acknowledged_by": "tester"},
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data.get("error", {}).get("message", "").lower()


# ── GET /api/jorge/alerts/{alert_id}/status ───────────────────────────


class TestGetAlertStatus:
    """Tests for the alert status endpoint."""

    def test_get_status_unacknowledged(self):
        """Returns status of an unacknowledged alert."""
        svc = AlertingService()
        svc._alerts.append(_make_alert(alert_id="status1", acknowledged=False))

        response = client.get("/api/jorge/alerts/status1/status")
        assert response.status_code == 200
        data = response.json()
        assert data["alert_id"] == "status1"
        assert data["acknowledged"] is False

    def test_get_status_acknowledged(self):
        """Returns status of an acknowledged alert with timing."""
        svc = AlertingService()
        alert = _make_alert(alert_id="status2", acknowledged=True)
        svc._alerts.append(alert)

        response = client.get("/api/jorge/alerts/status2/status")
        assert response.status_code == 200
        data = response.json()
        assert data["acknowledged"] is True
        assert "acknowledged_at" in data
        assert "time_to_ack_seconds" in data

    def test_get_status_not_found(self):
        """Returns 404 for non-existent alert ID."""
        response = client.get("/api/jorge/alerts/missing123/status")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data.get("error", {}).get("message", "").lower()


# ── GET /api/jorge/alert-rules ────────────────────────────────────────


class TestListAlertRules:
    """Tests for the list alert rules endpoint."""

    def test_list_rules_returns_defaults(self):
        """Returns the 7 default alert rules."""
        # Instantiate to trigger default rule loading
        AlertingService()

        response = client.get("/api/jorge/alert-rules")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 7

        rule_names = {r["name"] for r in data}
        assert "sla_violation" in rule_names
        assert "high_error_rate" in rule_names
        assert "low_cache_hit_rate" in rule_names
        assert "handoff_failure" in rule_names
        assert "bot_unresponsive" in rule_names
        assert "circular_handoff_spike" in rule_names
        assert "rate_limit_breach" in rule_names

    def test_list_rules_includes_active_flag(self):
        """Each rule includes an 'active' boolean flag."""
        AlertingService()

        response = client.get("/api/jorge/alert-rules")
        data = response.json()
        for rule in data:
            assert "active" in rule
            assert isinstance(rule["active"], bool)

    def test_list_rules_shows_disabled(self):
        """Disabled rules show active=false."""
        svc = AlertingService()
        svc._disabled_rules.add("low_cache_hit_rate")

        response = client.get("/api/jorge/alert-rules")
        data = response.json()
        cache_rule = next(r for r in data if r["name"] == "low_cache_hit_rate")
        assert cache_rule["active"] is False


# ── PATCH /api/jorge/alert-rules/{rule_name} ──────────────────────────


class TestUpdateAlertRule:
    """Tests for the update alert rule endpoint."""

    def test_disable_rule(self):
        """Disabling a rule sets active=false."""
        AlertingService()

        response = client.patch(
            "/api/jorge/alert-rules/sla_violation",
            json={"active": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "sla_violation"
        assert data["active"] is False

    def test_enable_rule(self):
        """Re-enabling a disabled rule sets active=true."""
        svc = AlertingService()
        svc._disabled_rules.add("sla_violation")

        response = client.patch(
            "/api/jorge/alert-rules/sla_violation",
            json={"active": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["active"] is True

    def test_update_rule_not_found(self):
        """Returns 404 for non-existent rule name."""
        AlertingService()

        response = client.patch(
            "/api/jorge/alert-rules/nonexistent_rule",
            json={"active": False},
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data.get("error", {}).get("message", "").lower()

    def test_disable_rule_skips_check_alerts(self):
        """Disabled rules are skipped during check_alerts."""
        import asyncio

        svc = AlertingService()
        # This would normally trigger high_error_rate
        stats = {"error_rate": 0.10}

        # First: verify it triggers when active
        alerts = asyncio.get_event_loop().run_until_complete(svc.check_alerts(stats))
        triggered_names = [a.rule_name for a in alerts]
        assert "high_error_rate" in triggered_names

        # Reset cooldowns
        svc._last_fired.clear()

        # Now disable and verify it does not trigger
        asyncio.get_event_loop().run_until_complete(svc.disable_rule("high_error_rate"))
        alerts = asyncio.get_event_loop().run_until_complete(svc.check_alerts(stats))
        triggered_names = [a.rule_name for a in alerts]
        assert "high_error_rate" not in triggered_names