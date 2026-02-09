"""Tests for jorge_alert_dashboard component.

Tests the data preparation helpers and formatting functions.
Does not test Streamlit rendering (requires st.testing).
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.streamlit_demo.components.jorge_alert_dashboard import (

@pytest.mark.unit
    SEVERITY_COLORS,
    SEVERITY_EMOJI,
    format_alert_row,
    format_escalation_row,
    format_time_ago,
    format_timestamp,
    get_alert_data,
)


@dataclass
class MockAlert:
    id: str
    rule_name: str
    severity: str
    message: str
    triggered_at: float
    performance_stats: Dict[str, Any] = field(default_factory=dict)
    channels_sent: List[str] = field(default_factory=list)
    acknowledged: bool = False
    acknowledged_at: Optional[float] = None
    acknowledged_by: Optional[str] = None


@dataclass
class MockEscalationLevel:
    level: int
    delay_seconds: int
    channels: List[str]
    description: str = ""


# ── format_timestamp ──────────────────────────────────────────────────


def test_format_timestamp():
    result = format_timestamp(1707400000.0)
    assert isinstance(result, str)
    assert "-" in result  # date separator
    assert ":" in result  # time separator


# ── format_time_ago ───────────────────────────────────────────────────


def test_format_time_ago_seconds():
    result = format_time_ago(time.time() - 30)
    assert result.endswith("s ago")


def test_format_time_ago_minutes():
    result = format_time_ago(time.time() - 300)
    assert result.endswith("m ago")


def test_format_time_ago_hours():
    result = format_time_ago(time.time() - 7200)
    assert result.endswith("h ago")


def test_format_time_ago_days():
    result = format_time_ago(time.time() - 200000)
    assert result.endswith("d ago")


# ── format_alert_row ──────────────────────────────────────────────────


def test_format_alert_row_active():
    alert = MockAlert(
        id="abc123",
        rule_name="high_error_rate",
        severity="critical",
        message="[CRITICAL] high_error_rate\nError Rate: 6.00%",
        triggered_at=time.time() - 120,
    )
    row = format_alert_row(alert)
    assert row["severity_emoji"] == SEVERITY_EMOJI["critical"]
    assert row["severity"] == "critical"
    assert row["rule_name"] == "high_error_rate"
    assert row["ack_status"] == "Active"
    assert row["alert_id"] == "abc123"
    assert "high_error_rate" in row["message_preview"]


def test_format_alert_row_acknowledged():
    alert = MockAlert(
        id="def456",
        rule_name="low_cache_hit_rate",
        severity="warning",
        message="Cache hit rate below 50%",
        triggered_at=time.time() - 600,
        acknowledged=True,
        acknowledged_at=time.time() - 300,
        acknowledged_by="admin",
    )
    row = format_alert_row(alert)
    assert row["ack_status"] == "Acknowledged"
    assert row["severity_emoji"] == SEVERITY_EMOJI["warning"]


def test_format_alert_row_info_severity():
    alert = MockAlert(
        id="ghi789",
        rule_name="test_rule",
        severity="info",
        message="Info message",
        triggered_at=time.time(),
    )
    row = format_alert_row(alert)
    assert row["severity_emoji"] == SEVERITY_EMOJI["info"]


def test_format_alert_row_unknown_severity():
    alert = MockAlert(
        id="xyz",
        rule_name="custom",
        severity="unknown",
        message="test",
        triggered_at=time.time(),
    )
    row = format_alert_row(alert)
    assert row["severity_emoji"] == "⚪"


def test_format_alert_row_empty_message():
    alert = MockAlert(
        id="e001",
        rule_name="test",
        severity="warning",
        message="",
        triggered_at=time.time(),
    )
    row = format_alert_row(alert)
    assert row["message_preview"] == ""


# ── format_escalation_row ─────────────────────────────────────────────


def test_format_escalation_row():
    alert = MockAlert(
        id="esc1",
        rule_name="sla_violation",
        severity="critical",
        message="P95 latency exceeded",
        triggered_at=time.time() - 600,
    )
    level = MockEscalationLevel(
        level=2,
        delay_seconds=300,
        channels=["email", "slack"],
        description="5min unack: all channels",
    )
    row = format_escalation_row(alert, level)
    assert row["level"] == "L2"
    assert row["rule_name"] == "sla_violation"
    assert row["channels"] == "email, slack"
    assert "5min unack" in row["description"]


# ── get_alert_data ────────────────────────────────────────────────────


def test_get_alert_data():
    mock_service = MagicMock()
    mock_service._rules = {"rule1": None, "rule2": None}

    active = [
        MockAlert("a1", "rule1", "critical", "msg", time.time()),
    ]
    history = [
        MockAlert("a1", "rule1", "critical", "msg", time.time()),
        MockAlert("a2", "rule2", "warning", "msg2", time.time() - 100),
    ]
    escalation_level = MockEscalationLevel(2, 300, ["email"])
    escalations = [(active[0], escalation_level)]

    mock_service.get_active_alerts = AsyncMock(return_value=active)
    mock_service.get_alert_history = AsyncMock(return_value=history)
    mock_service.check_escalations = AsyncMock(return_value=escalations)

    data = get_alert_data(mock_service)

    assert len(data["active_alerts"]) == 1
    assert len(data["alert_history"]) == 2
    assert len(data["escalations"]) == 1
    assert data["rule_count"] == 2


# ── Severity mappings ─────────────────────────────────────────────────


def test_severity_colors_complete():
    assert "critical" in SEVERITY_COLORS
    assert "warning" in SEVERITY_COLORS
    assert "info" in SEVERITY_COLORS


def test_severity_emoji_complete():
    assert "critical" in SEVERITY_EMOJI
    assert "warning" in SEVERITY_EMOJI
    assert "info" in SEVERITY_EMOJI