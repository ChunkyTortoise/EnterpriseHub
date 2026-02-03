"""
Jorge Bot Operations Dashboard

Operational monitoring for Jorge's three-bot ecosystem (Seller, Buyer, Lead).
Tracks real-time performance against SUCCESS_METRICS and PERFORMANCE_THRESHOLDS
defined in jorge_config.py.

Sections:
1. Bot Status Header
2. Temperature Distribution
3. Compliance Monitor
4. Handoff Tracker (Sankey)
5. Response Time Monitor
6. Qualification Funnel
7. GHL Integration Health
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random
import time

# Import bot services and config with graceful fallback
try:
    from ghl_real_estate_ai.ghl_utils.jorge_config import (
        JorgeSellerConfig,
        settings as jorge_settings,
    )
    SUCCESS_METRICS = JorgeSellerConfig.SUCCESS_METRICS
    PERFORMANCE_THRESHOLDS = JorgeSellerConfig.PERFORMANCE_THRESHOLDS
except ImportError:
    # Fallback values matching jorge_config.py
    SUCCESS_METRICS = {
        "qualification_completion_rate": 0.60,
        "hot_lead_conversion_rate": 0.15,
        "agent_handoff_rate": 0.20,
        "followup_engagement_rate": 0.30,
        "opt_out_rate": 0.05,
    }
    PERFORMANCE_THRESHOLDS = {
        "webhook_response_time": 2.0,
        "message_delivery_rate": 0.99,
        "classification_accuracy": 0.90,
        "sms_compliance_rate": 1.0,
    }

try:
    from ghl_real_estate_ai.services.analytics_service import AnalyticsService
except ImportError:
    AnalyticsService = None

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Jorge Bot Operations",
    page_icon="🤖",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BOT_NAMES = ["Seller", "Buyer", "Lead"]
BOT_COLORS = {
    "Seller": "#ff6b6b",
    "Buyer": "#4ecdc4",
    "Lead": "#45b7d1",
}
SLA_RESPONSE_TIME = PERFORMANCE_THRESHOLDS["webhook_response_time"]  # 2.0s


# ---------------------------------------------------------------------------
# Demo data generators (cached for near real-time refresh)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=15)
def get_bot_status_data() -> Dict[str, Dict[str, Any]]:
    """Per-bot operational status metrics (demo data)."""
    now = datetime.now()
    data = {}
    for bot in BOT_NAMES:
        avg_rt = round(random.uniform(0.6, 2.4), 2)
        msgs_today = random.randint(40, 180)
        enabled = random.random() > 0.05  # 95% chance enabled
        data[bot] = {
            "enabled": enabled,
            "messages_today": msgs_today,
            "avg_response_time": avg_rt,
            "status": "ok" if avg_rt < SLA_RESPONSE_TIME * 0.8 else (
                "warning" if avg_rt < SLA_RESPONSE_TIME else "critical"
            ),
            "last_heartbeat": (now - timedelta(seconds=random.randint(2, 30))).isoformat(),
        }
    return data


@st.cache_data(ttl=15)
def get_temperature_distribution(period_days: int) -> pd.DataFrame:
    """Temperature distribution per bot over the requested period (demo)."""
    rows = []
    for bot in BOT_NAMES:
        total = random.randint(80, 300) * (period_days // 7)
        hot_pct = random.uniform(0.10, 0.22)
        warm_pct = random.uniform(0.25, 0.45)
        cold_pct = 1.0 - hot_pct - warm_pct
        rows.append({"Bot": bot, "Temperature": "Hot", "Count": int(total * hot_pct)})
        rows.append({"Bot": bot, "Temperature": "Warm", "Count": int(total * warm_pct)})
        rows.append({"Bot": bot, "Temperature": "Cold", "Count": int(total * cold_pct)})
    return pd.DataFrame(rows)


@st.cache_data(ttl=15)
def get_compliance_blocks() -> pd.DataFrame:
    """Recent compliance-blocked messages (demo)."""
    violation_types = [
        "Fair Housing Violation",
        "DRE Disclosure Missing",
        "CCPA Opt-Out Ignored",
        "Unlicensed Advice",
        "Price Guarantee Language",
        "CAN-SPAM Non-Compliant",
    ]
    now = datetime.now()
    rows = []
    for i in range(random.randint(4, 12)):
        ts = now - timedelta(minutes=random.randint(5, 1440))
        contact_id = f"***{random.randint(1000, 9999)}"
        bot_mode = random.choice(BOT_NAMES)
        violation = random.choice(violation_types)
        rows.append({
            "Timestamp": ts.strftime("%Y-%m-%d %H:%M"),
            "Contact ID": contact_id,
            "Bot Mode": bot_mode,
            "Violation Type": violation,
        })
    df = pd.DataFrame(rows)
    df = df.sort_values("Timestamp", ascending=False).reset_index(drop=True)
    return df


@st.cache_data(ttl=15)
def get_compliance_trend() -> pd.DataFrame:
    """Daily block rate over last 14 days (demo)."""
    rows = []
    for i in range(14, 0, -1):
        day = datetime.now() - timedelta(days=i)
        total_msgs = random.randint(200, 600)
        blocks = random.randint(0, max(1, int(total_msgs * 0.012)))
        rows.append({
            "Date": day.strftime("%Y-%m-%d"),
            "Block Rate (%)": round((blocks / total_msgs) * 100, 3),
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=15)
def get_handoff_data() -> Dict[str, Any]:
    """Handoff volumes and success rates between bots (demo)."""
    directions = [
        ("Lead", "Buyer"),
        ("Lead", "Seller"),
        ("Buyer", "Seller"),
        ("Seller", "Buyer"),
    ]
    volumes = {}
    success_rates = {}
    for src, dst in directions:
        key = f"{src} -> {dst}"
        volumes[key] = random.randint(5, 45)
        success_rates[key] = round(random.uniform(0.82, 0.98), 2)
    return {"volumes": volumes, "success_rates": success_rates}


@st.cache_data(ttl=15)
def get_response_time_series() -> Dict[str, Any]:
    """p50 / p95 / p99 response times per bot over 24h (demo)."""
    hours = [(datetime.now() - timedelta(hours=i)) for i in range(24, 0, -1)]
    series: Dict[str, Dict[str, List[float]]] = {}
    for bot in BOT_NAMES:
        base = random.uniform(0.5, 1.0)
        p50 = [round(base + random.uniform(-0.15, 0.25), 3) for _ in hours]
        p95 = [round(v + random.uniform(0.3, 0.8), 3) for v in p50]
        p99 = [round(v + random.uniform(0.2, 0.6), 3) for v in p95]
        series[bot] = {"p50": p50, "p95": p95, "p99": p99}
    return {"timestamps": hours, "series": series}


@st.cache_data(ttl=15)
def get_qualification_funnel() -> Dict[str, Dict[str, int]]:
    """Funnel data per bot: Total -> Activated -> Qualified -> Appointment -> Handoff (demo)."""
    funnels: Dict[str, Dict[str, int]] = {}
    for bot in BOT_NAMES:
        total = random.randint(200, 500)
        activated = int(total * random.uniform(0.70, 0.90))
        qualified = int(activated * random.uniform(0.50, 0.70))
        appointment = int(qualified * random.uniform(0.30, 0.55))
        handoff = int(appointment * random.uniform(0.40, 0.70))
        funnels[bot] = {
            "Total Contacts": total,
            "Activated": activated,
            "Qualified": qualified,
            "Appointment Set": appointment,
            "Agent Handoff": handoff,
        }
    return funnels


@st.cache_data(ttl=15)
def get_ghl_integration_health() -> Dict[str, Dict[str, Any]]:
    """GHL integration metrics (demo)."""
    metrics = {}
    for name, target in [
        ("Message Delivery Rate", 0.99),
        ("Tag Success Rate", 0.99),
        ("Workflow Trigger Rate", 0.99),
        ("Custom Field Update Rate", 0.99),
    ]:
        current = round(random.uniform(0.975, 1.0), 4)
        previous = round(random.uniform(0.975, 1.0), 4)
        metrics[name] = {
            "current": current,
            "previous": previous,
            "target": target,
            "delta": round(current - previous, 4),
        }
    return metrics


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------

def render_bot_status_header() -> None:
    """Section 1: Bot status cards with color-coded SLA indicators."""
    st.subheader("Bot Status Overview")

    status_data = get_bot_status_data()
    cols = st.columns(3)

    for idx, bot in enumerate(BOT_NAMES):
        info = status_data[bot]
        with cols[idx]:
            # Determine color label
            if not info["enabled"]:
                color_label = "DISABLED"
            elif info["status"] == "ok":
                color_label = "HEALTHY"
            elif info["status"] == "warning":
                color_label = "WARNING"
            else:
                color_label = "CRITICAL"

            # Build CSS class indicator
            if color_label == "HEALTHY":
                indicator = ":green[HEALTHY]"
            elif color_label == "WARNING":
                indicator = ":orange[WARNING]"
            elif color_label == "CRITICAL":
                indicator = ":red[CRITICAL]"
            else:
                indicator = ":gray[DISABLED]"

            st.markdown(f"### {bot} Bot  {indicator}")
            st.metric(
                label="Messages Today",
                value=info["messages_today"],
            )
            delta_color = "normal" if info["avg_response_time"] <= SLA_RESPONSE_TIME else "inverse"
            st.metric(
                label="Avg Response Time",
                value=f"{info['avg_response_time']}s",
                delta=f"SLA: {SLA_RESPONSE_TIME}s",
                delta_color=delta_color,
            )
            st.caption(
                f"Enabled: {'Yes' if info['enabled'] else 'No'} | "
                f"Last heartbeat: {info['last_heartbeat'][11:19]}"
            )


def render_temperature_distribution() -> None:
    """Section 2: Stacked bar chart of Hot/Warm/Cold per bot."""
    st.subheader("Temperature Distribution")

    period = st.radio(
        "Time period",
        options=[7, 30],
        format_func=lambda d: f"{d} days",
        horizontal=True,
        key="temp_period",
    )

    df = get_temperature_distribution(period)

    color_map = {"Hot": "#e74c3c", "Warm": "#f39c12", "Cold": "#3498db"}
    fig = px.bar(
        df,
        x="Bot",
        y="Count",
        color="Temperature",
        barmode="stack",
        color_discrete_map=color_map,
        title=f"Lead Temperature Distribution (Last {period} Days)",
    )

    # Overlay target lines
    hot_target = SUCCESS_METRICS["hot_lead_conversion_rate"]
    qual_target = SUCCESS_METRICS["qualification_completion_rate"]

    # Compute totals for annotation reference
    totals = df.groupby("Bot")["Count"].sum()
    max_total = totals.max() if len(totals) > 0 else 100

    fig.add_hline(
        y=int(max_total * hot_target),
        line_dash="dash",
        line_color="#e74c3c",
        annotation_text=f"Hot Target ({hot_target:.0%})",
        annotation_position="top left",
    )
    fig.add_hline(
        y=int(max_total * qual_target),
        line_dash="dash",
        line_color="#2ecc71",
        annotation_text=f"Qualification Target ({qual_target:.0%})",
        annotation_position="bottom left",
    )

    fig.update_layout(height=420, yaxis_title="Lead Count", xaxis_title="Bot")
    st.plotly_chart(fig, use_container_width=True)


def render_compliance_monitor() -> None:
    """Section 3: Recent compliance blocks table and block rate trend."""
    st.subheader("Compliance Monitor")

    col_table, col_chart = st.columns([3, 2])

    with col_table:
        st.markdown("**Recent Compliance Blocks**")
        blocks_df = get_compliance_blocks()
        st.dataframe(blocks_df, use_container_width=True, hide_index=True)

    with col_chart:
        st.markdown("**Block Rate Trend (14 Days)**")
        trend_df = get_compliance_trend()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend_df["Date"],
            y=trend_df["Block Rate (%)"],
            mode="lines+markers",
            name="Block Rate",
            line=dict(color="#e74c3c", width=2),
            marker=dict(size=5),
        ))
        fig.add_hline(
            y=1.0,
            line_dash="dash",
            line_color="#2ecc71",
            annotation_text="Target: <1%",
            annotation_position="top left",
        )
        fig.update_layout(
            height=350,
            yaxis_title="Block Rate (%)",
            xaxis_title="Date",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)


def render_handoff_tracker() -> None:
    """Section 4: Sankey diagram of handoff volumes + success rates."""
    st.subheader("Handoff Tracker")

    handoff_data = get_handoff_data()
    volumes = handoff_data["volumes"]
    success_rates = handoff_data["success_rates"]

    # Build Sankey node/link structures
    labels = ["Lead (src)", "Buyer (src)", "Seller (src)",
              "Buyer (dst)", "Seller (dst)", "Lead (dst)"]
    # Map source/dest names to indices
    src_idx = {"Lead": 0, "Buyer": 1, "Seller": 2}
    dst_idx = {"Buyer": 3, "Seller": 4, "Lead": 5}

    sources = []
    targets = []
    values = []
    link_labels = []

    for direction, vol in volumes.items():
        src_name, dst_name = direction.split(" -> ")
        sources.append(src_idx[src_name])
        targets.append(dst_idx[dst_name])
        values.append(vol)
        sr = success_rates[direction]
        link_labels.append(f"{direction}: {vol} handoffs ({sr:.0%} success)")

    node_colors = [
        BOT_COLORS["Lead"], BOT_COLORS["Buyer"], BOT_COLORS["Seller"],
        BOT_COLORS["Buyer"], BOT_COLORS["Seller"], BOT_COLORS["Lead"],
    ]

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20,
            thickness=25,
            line=dict(color="black", width=0.5),
            label=labels,
            color=node_colors,
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            label=link_labels,
            color=[f"rgba(150,150,150,0.4)"] * len(sources),
        ),
    )])

    fig.update_layout(
        title="Bot-to-Bot Handoff Flow",
        height=420,
        font_size=12,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Success rate summary
    sr_cols = st.columns(len(success_rates))
    for idx, (direction, rate) in enumerate(success_rates.items()):
        with sr_cols[idx]:
            status = "normal" if rate >= 0.90 else "inverse"
            st.metric(
                label=direction,
                value=f"{rate:.0%}",
                delta="On target" if rate >= 0.90 else "Below target",
                delta_color=status,
            )


def render_response_time_monitor() -> None:
    """Section 5: p50/p95/p99 response time lines per bot with SLA threshold."""
    st.subheader("Response Time Monitor (24h)")

    rt_data = get_response_time_series()
    timestamps = rt_data["timestamps"]
    series = rt_data["series"]

    fig = make_subplots(
        rows=len(BOT_NAMES), cols=1,
        subplot_titles=[f"{bot} Bot" for bot in BOT_NAMES],
        vertical_spacing=0.08,
        shared_xaxes=True,
    )

    p99_breach = False

    for row_idx, bot in enumerate(BOT_NAMES, start=1):
        bot_series = series[bot]
        color = BOT_COLORS[bot]

        # p50
        fig.add_trace(go.Scatter(
            x=timestamps, y=bot_series["p50"],
            mode="lines", name=f"{bot} p50",
            line=dict(color=color, width=2),
            legendgroup=bot, showlegend=(row_idx == 1),
        ), row=row_idx, col=1)

        # p95
        fig.add_trace(go.Scatter(
            x=timestamps, y=bot_series["p95"],
            mode="lines", name=f"{bot} p95",
            line=dict(color=color, width=1.5, dash="dash"),
            legendgroup=bot, showlegend=(row_idx == 1),
        ), row=row_idx, col=1)

        # p99
        fig.add_trace(go.Scatter(
            x=timestamps, y=bot_series["p99"],
            mode="lines", name=f"{bot} p99",
            line=dict(color=color, width=1, dash="dot"),
            legendgroup=bot, showlegend=(row_idx == 1),
        ), row=row_idx, col=1)

        # SLA line
        fig.add_hline(
            y=SLA_RESPONSE_TIME, row=row_idx, col=1,
            line_dash="dash", line_color="red", line_width=1,
            annotation_text=f"SLA {SLA_RESPONSE_TIME}s" if row_idx == 1 else None,
        )

        fig.update_yaxes(title_text="Seconds", row=row_idx, col=1)

        if max(bot_series["p99"]) > SLA_RESPONSE_TIME:
            p99_breach = True

    fig.update_layout(height=220 * len(BOT_NAMES) + 80, hovermode="x unified")
    fig.update_xaxes(title_text="Time", row=len(BOT_NAMES), col=1)

    st.plotly_chart(fig, use_container_width=True)

    if p99_breach:
        st.warning(
            f"p99 response time exceeds the {SLA_RESPONSE_TIME}s SLA threshold "
            "for one or more bots. Investigate webhook processing latency."
        )
    else:
        st.success("All bots operating within the SLA response time threshold.")


def render_qualification_funnel() -> None:
    """Section 6: Funnel chart per bot with conversion rates vs targets."""
    st.subheader("Qualification Funnel")

    funnels = get_qualification_funnel()
    tabs = st.tabs([f"{bot} Bot" for bot in BOT_NAMES])

    for tab, bot in zip(tabs, BOT_NAMES):
        with tab:
            funnel = funnels[bot]
            stages = list(funnel.keys())
            values = list(funnel.values())

            fig = go.Figure(go.Funnel(
                y=stages,
                x=values,
                textinfo="value+percent initial+percent previous",
                marker=dict(color=[
                    "#3498db", "#2ecc71", "#f39c12", "#e67e22", "#e74c3c"
                ]),
                connector=dict(line=dict(color="#aaa", width=1)),
            ))
            fig.update_layout(
                title=f"{bot} Bot Qualification Funnel",
                height=380,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Conversion rate comparison vs targets
            total = funnel["Total Contacts"]
            qualified = funnel["Qualified"]
            handoff = funnel["Agent Handoff"]

            qual_rate = qualified / total if total else 0
            handoff_rate = handoff / total if total else 0

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric(
                    "Qualification Rate",
                    f"{qual_rate:.1%}",
                    delta=f"Target: {SUCCESS_METRICS['qualification_completion_rate']:.0%}",
                    delta_color="normal" if qual_rate >= SUCCESS_METRICS["qualification_completion_rate"] else "inverse",
                )
            with c2:
                st.metric(
                    "Handoff Rate",
                    f"{handoff_rate:.1%}",
                    delta=f"Target: {SUCCESS_METRICS['agent_handoff_rate']:.0%}",
                    delta_color="normal" if handoff_rate >= SUCCESS_METRICS["agent_handoff_rate"] else "inverse",
                )
            with c3:
                hot_count = int(total * random.uniform(0.10, 0.20))
                hot_rate = hot_count / total if total else 0
                st.metric(
                    "Hot Lead Rate",
                    f"{hot_rate:.1%}",
                    delta=f"Target: {SUCCESS_METRICS['hot_lead_conversion_rate']:.0%}",
                    delta_color="normal" if hot_rate >= SUCCESS_METRICS["hot_lead_conversion_rate"] else "inverse",
                )


def render_ghl_integration_health() -> None:
    """Section 7: GHL integration metrics with delta indicators."""
    st.subheader("GHL Integration Health")

    ghl_metrics = get_ghl_integration_health()
    cols = st.columns(len(ghl_metrics))

    for idx, (name, info) in enumerate(ghl_metrics.items()):
        with cols[idx]:
            meets_target = info["current"] >= info["target"]
            st.metric(
                label=name,
                value=f"{info['current']:.2%}",
                delta=f"{info['delta']:+.2%} vs prev",
                delta_color="normal" if info["delta"] >= 0 else "inverse",
            )
            if meets_target:
                st.caption(f":green[Target {info['target']:.0%} met]")
            else:
                st.caption(f":red[Below target {info['target']:.0%}]")


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------

def main() -> None:
    """Render the full Jorge Bot Operations dashboard."""
    st.title("Jorge Bot Operations")
    st.caption("Real-time operational monitoring for the Seller, Buyer, and Lead bots")

    # Toolbar
    toolbar_left, toolbar_right = st.columns([4, 1])
    with toolbar_right:
        if st.button("Refresh Data", type="primary"):
            st.cache_data.clear()
            st.rerun()
    with toolbar_left:
        auto = st.checkbox("Auto-refresh (15s)", value=False)

    st.divider()

    # Organize sections with tabs for a clean layout
    tab_status, tab_temp, tab_compliance, tab_handoff, tab_rt, tab_funnel, tab_ghl = st.tabs([
        "Bot Status",
        "Temperature",
        "Compliance",
        "Handoffs",
        "Response Times",
        "Funnel",
        "GHL Health",
    ])

    with tab_status:
        render_bot_status_header()

    with tab_temp:
        render_temperature_distribution()

    with tab_compliance:
        render_compliance_monitor()

    with tab_handoff:
        render_handoff_tracker()

    with tab_rt:
        render_response_time_monitor()

    with tab_funnel:
        render_qualification_funnel()

    with tab_ghl:
        render_ghl_integration_health()

    # Footer
    st.divider()
    f1, f2, f3 = st.columns(3)
    with f1:
        st.caption(f"Last rendered: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    with f2:
        st.caption("Data source: Demo/Sample (pre-production)")
    with f3:
        st.caption(
            f"SLA: {SLA_RESPONSE_TIME}s | "
            f"Qual target: {SUCCESS_METRICS['qualification_completion_rate']:.0%} | "
            f"Hot target: {SUCCESS_METRICS['hot_lead_conversion_rate']:.0%}"
        )

    # Auto-refresh via rerun
    if auto:
        time.sleep(15)
        st.rerun()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
else:
    # When loaded as a Streamlit page, execute main directly
    main()
