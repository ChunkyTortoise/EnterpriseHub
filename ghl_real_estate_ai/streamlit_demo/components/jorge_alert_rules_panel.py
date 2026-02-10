"""
Jorge Alert Rules Panel

Streamlit component for managing alert rules via the Jorge Alerting API.
Falls back to demo data when the API is unreachable, allowing the panel
to render in standalone Streamlit Cloud deployments without a running
FastAPI backend.

Usage:
    from ghl_real_estate_ai.streamlit_demo.components.jorge_alert_rules_panel import (
        render_jorge_alert_rules_panel,
    )

    render_jorge_alert_rules_panel()
"""

import logging
from typing import Any, Dict, List

import streamlit as st

logger = logging.getLogger(__name__)

API_BASE_URL = "http://localhost:8000"

# Severity color mapping for visual indicators
_SEVERITY_COLORS = {
    "critical": "#ef4444",
    "warning": "#f59e0b",
    "info": "#3b82f6",
}

# Demo data matching the 7 default alert rules from alerting_service.py
_DEMO_RULES: List[Dict[str, Any]] = [
    {
        "name": "sla_violation",
        "severity": "critical",
        "cooldown_seconds": 300,
        "channels": ["email", "slack", "webhook"],
        "description": "P95 latency exceeds SLA target (Lead: 2000ms, Buyer/Seller: 2500ms)",
        "active": True,
    },
    {
        "name": "high_error_rate",
        "severity": "critical",
        "cooldown_seconds": 300,
        "channels": ["email", "slack", "webhook"],
        "description": "Error rate exceeds 5%",
        "active": True,
    },
    {
        "name": "low_cache_hit_rate",
        "severity": "warning",
        "cooldown_seconds": 600,
        "channels": ["slack"],
        "description": "Cache hit rate below 50%",
        "active": True,
    },
    {
        "name": "handoff_failure",
        "severity": "critical",
        "cooldown_seconds": 300,
        "channels": ["email", "slack"],
        "description": "Handoff success rate below 95%",
        "active": True,
    },
    {
        "name": "bot_unresponsive",
        "severity": "critical",
        "cooldown_seconds": 600,
        "channels": ["email", "slack", "webhook"],
        "description": "No bot responses for 5 minutes",
        "active": True,
    },
    {
        "name": "circular_handoff_spike",
        "severity": "warning",
        "cooldown_seconds": 600,
        "channels": ["slack"],
        "description": "More than 10 blocked handoffs in the last hour",
        "active": True,
    },
    {
        "name": "rate_limit_breach",
        "severity": "warning",
        "cooldown_seconds": 300,
        "channels": ["slack"],
        "description": "Rate limit error rate exceeds 10%",
        "active": True,
    },
]


def _fetch_rules() -> List[Dict[str, Any]]:
    """Fetch alert rules from the API, falling back to demo data.

    Returns:
        List of rule dicts with name, severity, cooldown_seconds,
        channels, description, and active fields.
    """
    try:
        import requests

        response = requests.get(
            f"{API_BASE_URL}/api/jorge/alert-rules",
            timeout=2,
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.debug(f"API unreachable, using demo alert rules: {e}")
    return [dict(r) for r in _DEMO_RULES]


def _toggle_rule(name: str, active: bool) -> bool:
    """Toggle a rule's active state via the API.

    Args:
        name: Rule name to toggle.
        active: Desired active state.

    Returns:
        True if the API call succeeded, False otherwise.
    """
    try:
        import requests

        response = requests.patch(
            f"{API_BASE_URL}/api/jorge/alert-rules/{name}",
            json={"active": active},
            timeout=2,
        )
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"Could not toggle rule '{name}' (API unreachable): {e}")
        return False


def _format_cooldown(seconds: int) -> str:
    """Format cooldown seconds as a human-readable string."""
    if seconds >= 3600:
        return f"{seconds // 3600}h {(seconds % 3600) // 60}m"
    if seconds >= 60:
        return f"{seconds // 60}m"
    return f"{seconds}s"


def render_jorge_alert_rules_panel() -> None:
    """Render the alert rules management panel.

    Displays each rule as an expandable card with severity indicator,
    description, cooldown, channels, and an active/inactive toggle.
    """
    st.subheader("Alert Rules Configuration")
    st.caption(
        "Manage the 7 default alert rules for Jorge bot monitoring. "
        "Disabled rules are skipped during periodic alert checks."
    )

    rules = _fetch_rules()

    if not rules:
        st.info("No alert rules configured.")
        return

    # Summary metrics
    active_count = sum(1 for r in rules if r.get("active", True))
    critical_count = sum(1 for r in rules if r.get("severity") == "critical")
    warning_count = sum(1 for r in rules if r.get("severity") == "warning")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Rules", len(rules))
    col2.metric("Active", active_count)
    col3.metric("Critical", critical_count)
    col4.metric("Warning", warning_count)

    st.divider()

    # Render each rule
    for rule in rules:
        rule_name = rule.get("name", "unknown")
        severity = rule.get("severity", "info")
        color = _SEVERITY_COLORS.get(severity, "#6b7280")
        is_active = rule.get("active", True)

        label = f"{'[ACTIVE]' if is_active else '[DISABLED]'} {rule_name} ({severity})"
        with st.expander(label, expanded=False):
            st.markdown(
                f"**Severity:** <span style='color:{color}'>{severity.upper()}</span>",
                unsafe_allow_html=True,
            )
            st.write(f"**Description:** {rule.get('description', 'N/A')}")
            st.write(f"**Cooldown:** {_format_cooldown(rule.get('cooldown_seconds', 300))}")
            st.write(f"**Channels:** {', '.join(rule.get('channels', []))}")

            # Toggle switch
            new_active = st.checkbox(
                "Active",
                value=is_active,
                key=f"rule_toggle_{rule_name}",
            )

            if new_active != is_active:
                success = _toggle_rule(rule_name, new_active)
                if success:
                    st.success(
                        f"Rule '{rule_name}' {'enabled' if new_active else 'disabled'}"
                    )
                else:
                    st.warning(
                        f"Could not update rule '{rule_name}' (API unreachable). "
                        "Change will not persist."
                    )
