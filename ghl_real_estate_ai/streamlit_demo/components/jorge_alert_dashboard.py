"""Jorge Operational Alert Dashboard

Streamlit component for managing Jorge bot operational alerts.
Displays active alerts, alert history, and escalation status using
the AlertingService singleton.

Separate from the GHL Alert Center (alert_center.py) which handles
real-time CRM alerts (hot leads, bookings, etc.). This dashboard
focuses on *operational* alerts: SLA violations, error rates, cache
degradation, handoff failures, and bot health.

Usage:
    from ghl_real_estate_ai.streamlit_demo.components.jorge_alert_dashboard import (
        render_jorge_alert_dashboard,
    )
    render_jorge_alert_dashboard()
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple

import streamlit as st

logger = logging.getLogger(__name__)

# Severity color mapping
SEVERITY_COLORS: Dict[str, str] = {
    "critical": "#ef4444",
    "warning": "#f97316",
    "info": "#3b82f6",
}

SEVERITY_EMOJI: Dict[str, str] = {
    "critical": "🔴",
    "warning": "🟡",
    "info": "🔵",
}


def format_timestamp(ts: float) -> str:
    """Format a unix timestamp for display."""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def format_time_ago(ts: float) -> str:
    """Format a unix timestamp as relative time."""
    import time

    delta = time.time() - ts
    if delta < 60:
        return f"{int(delta)}s ago"
    elif delta < 3600:
        return f"{int(delta // 60)}m ago"
    elif delta < 86400:
        return f"{int(delta // 3600)}h ago"
    else:
        return f"{int(delta // 86400)}d ago"


def get_alert_data(alerting_service) -> Dict[str, Any]:
    """Extract alert data from the AlertingService for display.

    Returns:
        Dict with active_alerts, alert_history, escalations, and rule_count.
    """
    import asyncio

    loop = asyncio.new_event_loop()
    try:
        active = loop.run_until_complete(alerting_service.get_active_alerts())
        history = loop.run_until_complete(alerting_service.get_alert_history(limit=50))
        escalations = loop.run_until_complete(alerting_service.check_escalations())
    finally:
        loop.close()

    return {
        "active_alerts": active,
        "alert_history": history,
        "escalations": escalations,
        "rule_count": len(alerting_service._rules),
    }


def format_alert_row(alert) -> Dict[str, str]:
    """Format a single alert into display-ready strings.

    Args:
        alert: An Alert dataclass instance.

    Returns:
        Dict with severity_emoji, severity, rule_name, message_preview,
        triggered_at, time_ago, ack_status, alert_id.
    """
    emoji = SEVERITY_EMOJI.get(alert.severity, "⚪")
    msg_preview = alert.message.split("\n")[0][:80] if alert.message else ""
    ack_status = "Acknowledged" if alert.acknowledged else "Active"

    return {
        "severity_emoji": emoji,
        "severity": alert.severity,
        "rule_name": alert.rule_name,
        "message_preview": msg_preview,
        "triggered_at": format_timestamp(alert.triggered_at),
        "time_ago": format_time_ago(alert.triggered_at),
        "ack_status": ack_status,
        "alert_id": alert.id,
    }


def format_escalation_row(
    alert,
    level,
) -> Dict[str, str]:
    """Format an escalation entry for display.

    Args:
        alert: An Alert dataclass instance.
        level: An EscalationLevel dataclass instance.

    Returns:
        Dict with level, rule_name, description, channels, time_ago.
    """
    return {
        "level": f"L{level.level}",
        "rule_name": alert.rule_name,
        "description": level.description,
        "channels": ", ".join(level.channels),
        "time_ago": format_time_ago(alert.triggered_at),
    }


def render_jorge_alert_dashboard(alerting_service=None) -> None:
    """Render the Jorge operational alert management dashboard.

    Args:
        alerting_service: Optional AlertingService instance. If None,
            creates a new singleton instance.
    """
    if alerting_service is None:
        from ghl_real_estate_ai.services.jorge.alerting_service import AlertingService

        alerting_service = AlertingService()

    data = get_alert_data(alerting_service)
    active_alerts = data["active_alerts"]
    alert_history = data["alert_history"]
    escalations = data["escalations"]

    # Header with stats
    st.subheader("Jorge Operational Alerts")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Active Alerts", len(active_alerts))
    with col2:
        critical_count = sum(1 for a in active_alerts if a.severity == "critical")
        st.metric("Critical", critical_count)
    with col3:
        st.metric("Escalations", len(escalations))
    with col4:
        st.metric("Rules", data["rule_count"])

    # Tabs
    tab_active, tab_history, tab_escalations = st.tabs(["Active Alerts", "Alert History", "Escalation Monitor"])

    with tab_active:
        _render_active_alerts(active_alerts, alerting_service)

    with tab_history:
        _render_alert_history(alert_history)

    with tab_escalations:
        _render_escalation_monitor(escalations)


def _render_active_alerts(alerts: list, alerting_service) -> None:
    """Render the active alerts section with acknowledge buttons."""
    if not alerts:
        st.info("No active alerts. All systems operational.")
        return

    for alert in alerts:
        row = format_alert_row(alert)
        color = SEVERITY_COLORS.get(alert.severity, "#6b7280")

        with st.container():
            cols = st.columns([0.5, 1.5, 3, 1.5, 1])
            with cols[0]:
                st.markdown(
                    f"<span style='color:{color};font-size:1.5em'>{row['severity_emoji']}</span>",
                    unsafe_allow_html=True,
                )
            with cols[1]:
                st.text(row["rule_name"])
            with cols[2]:
                st.text(row["message_preview"])
            with cols[3]:
                st.text(row["time_ago"])
            with cols[4]:
                if st.button(
                    "Ack",
                    key=f"ack_{alert.id}",
                    use_container_width=True,
                ):
                    _acknowledge_alert(alerting_service, alert.id)

        st.divider()


def _acknowledge_alert(alerting_service, alert_id: str) -> None:
    """Acknowledge an alert via the AlertingService."""
    import asyncio

    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(alerting_service.acknowledge_alert(alert_id, acknowledged_by="dashboard_user"))
        st.success(f"Alert {alert_id} acknowledged ({result.get('time_to_ack_seconds', 0):.1f}s after trigger)")
    except KeyError:
        st.error(f"Alert {alert_id} not found")
    except Exception as e:
        st.error(f"Failed to acknowledge: {e}")
    finally:
        loop.close()


def _render_alert_history(alerts: list) -> None:
    """Render the alert history tab with severity filter."""
    if not alerts:
        st.info("No alert history.")
        return

    severity_filter = st.selectbox(
        "Filter by severity",
        ["all", "critical", "warning", "info"],
        key="jorge_alert_severity_filter",
    )

    filtered = alerts
    if severity_filter != "all":
        filtered = [a for a in alerts if a.severity == severity_filter]

    if not filtered:
        st.info(f"No {severity_filter} alerts in history.")
        return

    rows = []
    for alert in filtered:
        row = format_alert_row(alert)
        rows.append(
            {
                "Severity": f"{row['severity_emoji']} {row['severity']}",
                "Rule": row["rule_name"],
                "Message": row["message_preview"],
                "Triggered": row["triggered_at"],
                "Status": row["ack_status"],
            }
        )

    st.dataframe(rows, use_container_width=True)


def _render_escalation_monitor(
    escalations: List[Tuple],
) -> None:
    """Render the escalation monitor tab."""
    if not escalations:
        st.info("No pending escalations.")
        return

    st.warning(f"{len(escalations)} alert(s) pending escalation")

    for alert, level in escalations:
        row = format_escalation_row(alert, level)
        with st.container():
            cols = st.columns([0.5, 1.5, 2, 1.5, 1])
            with cols[0]:
                st.markdown(
                    f"**{row['level']}**",
                )
            with cols[1]:
                st.text(row["rule_name"])
            with cols[2]:
                st.text(row["description"])
            with cols[3]:
                st.text(row["channels"])
            with cols[4]:
                st.text(row["time_ago"])

        st.divider()
