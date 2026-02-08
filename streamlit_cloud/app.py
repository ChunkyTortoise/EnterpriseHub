"""
EnterpriseHub — Portfolio Demo
Real Estate AI Platform: Lead Qualification, Bot Orchestration, BI Dashboards
Runs on Streamlit Cloud with zero external dependencies (no DB, Redis, or API keys).
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import datetime
import json
from pathlib import Path

st.set_page_config(
    page_title="EnterpriseHub — Real Estate AI Platform",
    page_icon="https://raw.githubusercontent.com/ChunkyTortoise/EnterpriseHub/main/assets/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

LEADS = [
    {"name": "Sarah Chen", "email": "sarah.c@email.com", "source": "Zillow", "score": 87, "temp": "Hot",
     "budget": 480000, "timeline": "1-3 months", "status": "Qualified", "bot": "Buyer",
     "signals": ["Pre-approved", "Scheduled showing", "Responded <5min"]},
    {"name": "David Kim", "email": "david.k@email.com", "source": "Google Ads", "score": 72, "temp": "Warm",
     "budget": 355000, "timeline": "3-6 months", "status": "Nurturing", "bot": "Lead",
     "signals": ["Viewed 12 listings", "Budget confirmed"]},
    {"name": "Maria Garcia", "email": "maria.g@email.com", "source": "Referral", "score": 93, "temp": "Hot",
     "budget": 620000, "timeline": "Immediate", "status": "Qualified", "bot": "Buyer",
     "signals": ["Cash buyer", "Pre-approved $650K", "Tour booked"]},
    {"name": "James Wilson", "email": "james.w@email.com", "source": "Facebook", "score": 41, "temp": "Cold",
     "budget": 280000, "timeline": "6-12 months", "status": "New", "bot": "Lead",
     "signals": ["First inquiry", "No budget confirmed"]},
    {"name": "Lisa Park", "email": "lisa.p@email.com", "source": "Website", "score": 68, "temp": "Warm",
     "budget": 510000, "timeline": "3-6 months", "status": "Nurturing", "bot": "Lead",
     "signals": ["Visited 3x", "Downloaded guide"]},
    {"name": "Robert Chen", "email": "robert.c@email.com", "source": "GoHighLevel", "score": 82, "temp": "Hot",
     "budget": 750000, "timeline": "1-3 months", "status": "Qualified", "bot": "Seller",
     "signals": ["CMA requested", "Selling + buying", "Agent meeting set"]},
    {"name": "Emily Torres", "email": "emily.t@email.com", "source": "Zillow", "score": 55, "temp": "Warm",
     "budget": 390000, "timeline": "3-6 months", "status": "Nurturing", "bot": "Buyer",
     "signals": ["Pre-qualification started", "Viewed 8 listings"]},
    {"name": "Michael Brown", "email": "michael.b@email.com", "source": "Referral", "score": 91, "temp": "Hot",
     "budget": 1200000, "timeline": "Immediate", "status": "Qualified", "bot": "Buyer",
     "signals": ["Cash offer ready", "Relocating from NYC", "Needs 4BR+"]},
]

np.random.seed(42)
DAYS = 90
dates = pd.date_range(end=datetime.date.today(), periods=DAYS)
revenue_base = np.cumsum(np.random.normal(8500, 2000, DAYS)) + 500000
leads_daily = np.random.poisson(12, DAYS)
conversion = 0.18 + np.random.normal(0, 0.02, DAYS).cumsum() * 0.001
conversion = np.clip(conversion, 0.10, 0.35)

MONTHLY_REVENUE = [185000, 210000, 195000, 240000, 260000, 285000]
MONTHS = ["Sep", "Oct", "Nov", "Dec", "Jan", "Feb"]

# Token cost data
TOKEN_DATA = {
    "before": {"tokens_per_workflow": 93000, "monthly_cost": 4200, "cache_hit": 0},
    "after": {"tokens_per_workflow": 7800, "monthly_cost": 460, "cache_hit": 87},
}

# Handoff data
HANDOFFS = [
    {"from": "Lead Bot", "to": "Buyer Bot", "contact": "Sarah Chen", "confidence": 0.92, "trigger": "Pre-approval confirmed + budget stated"},
    {"from": "Lead Bot", "to": "Seller Bot", "contact": "Robert Chen", "confidence": 0.88, "trigger": "CMA request + 'sell my house'"},
    {"from": "Lead Bot", "to": "Buyer Bot", "contact": "Maria Garcia", "confidence": 0.95, "trigger": "Cash buyer + immediate timeline"},
    {"from": "Buyer Bot", "to": "Lead Bot", "contact": "Emily Torres", "confidence": 0.71, "trigger": "Budget uncertainty + early stage"},
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TEMP_COLORS = {"Hot": "#ef4444", "Warm": "#f59e0b", "Cold": "#3b82f6"}

def kpi_card(label, value, delta=None, prefix="", suffix=""):
    delta_html = ""
    if delta is not None:
        color = "#10b981" if delta >= 0 else "#ef4444"
        arrow = "+" if delta >= 0 else ""
        delta_html = f"<div style='color:{color};font-size:0.85rem;margin-top:2px'>{arrow}{delta}%</div>"
    st.markdown(f"""
    <div style='background:#1e293b;border-radius:12px;padding:20px;text-align:center'>
        <div style='color:#94a3b8;font-size:0.8rem;text-transform:uppercase;letter-spacing:1px'>{label}</div>
        <div style='color:#f8fafc;font-size:1.8rem;font-weight:700;margin:4px 0'>{prefix}{value}{suffix}</div>
        {delta_html}
    </div>""", unsafe_allow_html=True)

def temp_badge(temp):
    return f"<span style='background:{TEMP_COLORS[temp]}20;color:{TEMP_COLORS[temp]};padding:2px 10px;border-radius:9999px;font-size:0.75rem;font-weight:600'>{temp}</span>"

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### EnterpriseHub")
    st.caption("Real Estate AI Platform — Demo Mode")
    st.markdown("---")

    hub = st.radio("Navigate", [
        "Executive Dashboard",
        "Lead Intelligence",
        "Bot Orchestration",
        "AI Cost Tracking",
        "Pipeline Analytics",
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("**Stack**")
    st.caption("FastAPI + Streamlit + PostgreSQL + Redis")
    st.caption("Claude + Gemini + Perplexity AI")
    st.caption("GoHighLevel CRM Integration")
    st.markdown("---")
    st.markdown(
        "[![GitHub](https://img.shields.io/badge/GitHub-Source-181717?logo=github)](https://github.com/ChunkyTortoise/EnterpriseHub) "
        "[![Tests](https://img.shields.io/badge/tests-4%2C467-brightgreen)](https://github.com/ChunkyTortoise/EnterpriseHub)"
    )

# ---------------------------------------------------------------------------
# Executive Dashboard
# ---------------------------------------------------------------------------

if hub == "Executive Dashboard":
    st.title("Executive Command Center")
    st.caption("Real-time business intelligence across all operations")

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Monthly Revenue", "$285K", delta=12, prefix="")
    with c2: kpi_card("Active Leads", "847", delta=8)
    with c3: kpi_card("Conversion Rate", "23", delta=5, suffix="%")
    with c4: kpi_card("Avg Deal Size", "$425K", delta=-2)

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([2, 1])

    with col_left:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(len(MONTHS))), y=MONTHLY_REVENUE,
            mode="lines+markers", name="Revenue",
            line=dict(color="#6366f1", width=3),
            marker=dict(size=8),
            fill="tozeroy", fillcolor="rgba(99,102,241,0.1)"
        ))
        fig.update_layout(
            title="Revenue Trend (6 Months)",
            xaxis=dict(ticktext=MONTHS, tickvals=list(range(len(MONTHS)))),
            yaxis=dict(tickprefix="$", tickformat=","),
            template="plotly_dark", height=350,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=60, r=20, t=50, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        sources = pd.DataFrame(LEADS).groupby("source").size().reset_index(name="count")
        fig2 = px.pie(sources, values="count", names="source",
                      color_discrete_sequence=["#6366f1", "#06b6d4", "#10b981", "#f59e0b", "#ef4444"])
        fig2.update_layout(
            title="Lead Sources", template="plotly_dark", height=350,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Lead pipeline
    st.subheader("Lead Pipeline")
    df = pd.DataFrame(LEADS)
    for _, row in df.iterrows():
        c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 2])
        with c1: st.markdown(f"**{row['name']}**<br><span style='color:#94a3b8;font-size:0.8rem'>{row['email']}</span>", unsafe_allow_html=True)
        with c2: st.markdown(f"Score: **{row['score']}**/100")
        with c3: st.markdown(temp_badge(row["temp"]), unsafe_allow_html=True)
        with c4: st.markdown(f"${row['budget']:,}")
        with c5: st.caption(" | ".join(row["signals"][:2]))

# ---------------------------------------------------------------------------
# Lead Intelligence
# ---------------------------------------------------------------------------

elif hub == "Lead Intelligence":
    st.title("Lead Intelligence Hub")
    st.caption("AI-powered lead scoring with temperature classification")

    lead_names = [l["name"] for l in LEADS]
    selected = st.selectbox("Select Lead", lead_names)
    lead = next(l for l in LEADS if l["name"] == selected)

    c1, c2, c3 = st.columns(3)
    with c1: kpi_card("Lead Score", str(lead["score"]), suffix="/100")
    with c2: kpi_card("Temperature", lead["temp"])
    with c3: kpi_card("Budget", f"${lead['budget']:,}")

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Scoring Breakdown")
        categories = ["Engagement", "Financial", "Timeline", "Behavioral", "Source Quality"]
        scores = [min(100, lead["score"] + np.random.randint(-15, 15)) for _ in categories]
        scores = [max(20, s) for s in scores]
        fig = go.Figure(go.Bar(
            x=scores, y=categories, orientation="h",
            marker_color=["#6366f1", "#10b981", "#f59e0b", "#06b6d4", "#8b5cf6"]
        ))
        fig.update_layout(
            template="plotly_dark", height=300, xaxis=dict(range=[0, 100]),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=100, r=20, t=10, b=30)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Lead Signals")
        for signal in lead["signals"]:
            st.markdown(f"- {signal}")

        st.markdown("---")
        st.subheader("Temperature Classification")
        st.markdown(f"""
        | Score Range | Temperature | Action |
        |---|---|---|
        | 80-100 | {temp_badge('Hot')} | Priority workflow, agent notification |
        | 40-79 | {temp_badge('Warm')} | Nurture sequence, follow-up reminder |
        | 0-39 | {temp_badge('Cold')} | Educational content, periodic check-in |
        """, unsafe_allow_html=True)

        st.info(f"**{lead['name']}** scored **{lead['score']}** → classified as **{lead['temp']}-Lead** → assigned to **{lead['bot']} Bot**")

# ---------------------------------------------------------------------------
# Bot Orchestration
# ---------------------------------------------------------------------------

elif hub == "Bot Orchestration":
    st.title("Jorge Bot Orchestration")
    st.caption("3-bot system with cross-bot handoff and safeguards")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div style='background:#1e293b;border-radius:12px;padding:20px;border-left:4px solid #6366f1'>
            <div style='color:#6366f1;font-weight:700;font-size:1.1rem'>Lead Bot</div>
            <div style='color:#94a3b8;font-size:0.85rem;margin-top:8px'>Initial qualification, temperature scoring, intent detection</div>
            <div style='color:#f8fafc;margin-top:12px;font-size:0.9rem'>
                Port 8001 &bull; 340 leads/day<br>
                Avg response: 1.2s<br>
                Handoff rate: 38%
            </div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div style='background:#1e293b;border-radius:12px;padding:20px;border-left:4px solid #10b981'>
            <div style='color:#10b981;font-weight:700;font-size:1.1rem'>Buyer Bot</div>
            <div style='color:#94a3b8;font-size:0.85rem;margin-top:8px'>Property matching, financial readiness, showing scheduling</div>
            <div style='color:#f8fafc;margin-top:12px;font-size:0.9rem'>
                Port 8003 &bull; 130 buyers/day<br>
                Avg response: 1.8s<br>
                Conversion: 24%
            </div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div style='background:#1e293b;border-radius:12px;padding:20px;border-left:4px solid #f59e0b'>
            <div style='color:#f59e0b;font-weight:700;font-size:1.1rem'>Seller Bot</div>
            <div style='color:#94a3b8;font-size:0.85rem;margin-top:8px'>CMA generation, listing prep, marketing strategy</div>
            <div style='color:#f8fafc;margin-top:12px;font-size:0.9rem'>
                Port 8002 &bull; 85 sellers/day<br>
                Avg response: 2.1s<br>
                Listing rate: 67%
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Recent Handoffs")

    for h in HANDOFFS:
        conf_color = "#10b981" if h["confidence"] >= 0.85 else "#f59e0b" if h["confidence"] >= 0.7 else "#ef4444"
        st.markdown(f"""
        <div style='background:#1e293b;border-radius:8px;padding:14px 18px;margin-bottom:8px;display:flex;align-items:center;gap:16px'>
            <div style='color:#6366f1;font-weight:600;min-width:80px'>{h['from']}</div>
            <div style='color:#94a3b8;font-size:1.2rem'>→</div>
            <div style='color:#10b981;font-weight:600;min-width:80px'>{h['to']}</div>
            <div style='color:#f8fafc;flex:1'>{h['contact']}</div>
            <div style='color:{conf_color};font-weight:600'>{h['confidence']:.0%}</div>
            <div style='color:#94a3b8;font-size:0.8rem;max-width:250px'>{h['trigger']}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Handoff Safeguards")
        st.markdown("""
        | Safeguard | Setting |
        |---|---|
        | Confidence threshold | 0.70 minimum |
        | Circular prevention | Same source→target blocked within 30min |
        | Rate limiting | 3 handoffs/hr, 10/day per contact |
        | Conflict resolution | Contact-level locking |
        | Pattern learning | Dynamic thresholds (min 10 data points) |
        """)

    with col_right:
        st.subheader("Intent Triggers")
        st.markdown("""
        | Direction | Trigger Phrases |
        |---|---|
        | Lead → Buyer | "I want to buy", "budget $X", "pre-approval" |
        | Lead → Seller | "Sell my house", "home worth", "CMA" |
        | Buyer → Lead | Budget uncertainty, early exploration |
        | Seller → Lead | Not ready to list, exploring options |
        """)

# ---------------------------------------------------------------------------
# AI Cost Tracking
# ---------------------------------------------------------------------------

elif hub == "AI Cost Tracking":
    st.title("AI Cost Engineering")
    st.caption("89% token cost reduction via 3-tier caching, context optimization, and model routing")

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Tokens/Workflow", "7,800", delta=-92, prefix="")
    with c2: kpi_card("Monthly Cost", "$460", delta=-89, prefix="")
    with c3: kpi_card("Cache Hit Rate", "87", suffix="%")
    with c4: kpi_card("Orchestrator Overhead", "<200", suffix="ms")

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Token Usage: Before vs After")
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Before", x=["Tokens/Workflow", "Monthly Cost ($)"],
                             y=[93000, 4200], marker_color="#ef4444"))
        fig.add_trace(go.Bar(name="After", x=["Tokens/Workflow", "Monthly Cost ($)"],
                             y=[7800, 460], marker_color="#10b981"))
        fig.update_layout(
            barmode="group", template="plotly_dark", height=350,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=60, r=20, t=20, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Savings by Technique")
        techniques = ["L1/L2/L3 Caching", "Context Window", "Model Routing"]
        savings = [60, 25, 15]
        fig2 = go.Figure(go.Pie(
            labels=techniques, values=savings,
            marker=dict(colors=["#6366f1", "#06b6d4", "#10b981"]),
            hole=0.4
        ))
        fig2.update_layout(
            template="plotly_dark", height=350,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Three-Tier Cache Architecture")
    st.markdown("""
    | Layer | Scope | TTL | Lookup Time | Purpose |
    |---|---|---|---|---|
    | **L1 (In-Memory)** | Per-request | Request lifecycle | <1ms | Deduplicate within single orchestration flow |
    | **L2 (Redis)** | Cross-request | 5min – 1hr | ~2ms | Shared across bot instances, template responses |
    | **L3 (PostgreSQL)** | Persistent | 24hr | ~5ms | Graceful degradation when Redis unavailable |
    """)

    st.subheader("Model Routing")
    st.markdown("""
    | Task Complexity | Model | Example Tasks | Cost |
    |---|---|---|---|
    | **Routine** | Haiku (fast) | Classification, template fill, FAQ | $0.25/M tokens |
    | **Standard** | Sonnet | Lead scoring, property matching | $3/M tokens |
    | **High-Stakes** | Opus | Market analysis, deal negotiation | $15/M tokens |
    """)

# ---------------------------------------------------------------------------
# Pipeline Analytics
# ---------------------------------------------------------------------------

elif hub == "Pipeline Analytics":
    st.title("Pipeline Analytics")
    st.caption("Conversion funnel and lead velocity metrics")

    # Funnel
    stages = ["New Leads", "Contacted", "Qualified", "Showing Scheduled", "Offer Made", "Closed"]
    values = [847, 612, 389, 198, 87, 42]

    fig = go.Figure(go.Funnel(
        y=stages, x=values,
        textinfo="value+percent initial",
        marker=dict(color=["#6366f1", "#818cf8", "#06b6d4", "#10b981", "#f59e0b", "#ef4444"])
    ))
    fig.update_layout(
        title="Conversion Funnel",
        template="plotly_dark", height=400,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=150, r=20, t=50, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Lead Velocity (90 Days)")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=dates, y=leads_daily.cumsum(),
            mode="lines", name="Cumulative Leads",
            line=dict(color="#6366f1", width=2),
            fill="tozeroy", fillcolor="rgba(99,102,241,0.1)"
        ))
        fig2.update_layout(
            template="plotly_dark", height=300,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=60, r=20, t=10, b=40)
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col_right:
        st.subheader("Conversion Rate Trend")
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=dates, y=conversion * 100,
            mode="lines", name="Conversion %",
            line=dict(color="#10b981", width=2),
            fill="tozeroy", fillcolor="rgba(16,185,129,0.1)"
        ))
        fig3.update_layout(
            template="plotly_dark", height=300,
            yaxis=dict(ticksuffix="%"),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=60, r=20, t=10, b=40)
        )
        st.plotly_chart(fig3, use_container_width=True)

    # Performance table
    st.subheader("Bot Performance Summary")
    perf = pd.DataFrame({
        "Bot": ["Lead Bot", "Buyer Bot", "Seller Bot"],
        "Daily Volume": [340, 130, 85],
        "Avg Response (s)": [1.2, 1.8, 2.1],
        "P95 Latency (s)": [2.8, 3.4, 4.1],
        "Success Rate": ["97.2%", "95.8%", "96.5%"],
        "Handoff Rate": ["38%", "12%", "8%"],
    })
    st.dataframe(perf, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#64748b;font-size:0.8rem'>"
    "EnterpriseHub — Portfolio Demo &bull; "
    "<a href='https://github.com/ChunkyTortoise/EnterpriseHub' style='color:#6366f1'>Source Code</a> &bull; "
    "<a href='https://chunkytortoise.github.io' style='color:#6366f1'>Portfolio</a> &bull; "
    "4,467 tests &bull; FastAPI + Streamlit + PostgreSQL + Redis + Claude AI"
    "</div>",
    unsafe_allow_html=True
)
