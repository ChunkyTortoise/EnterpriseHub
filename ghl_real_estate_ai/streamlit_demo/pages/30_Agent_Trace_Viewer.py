"""
Agent Trace Viewer Dashboard.

Visualizes agent mesh routing decisions, task lifecycle, latency by agent,
and the Think-Act-Observe execution loop. Demonstrates production-grade
observability for multi-agent AI systems.
"""

import random
from datetime import datetime, timedelta

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ghl_real_estate_ai.streamlit_demo.obsidian_theme import inject_elite_css

st.set_page_config(
    page_title="Agent Trace Viewer | EnterpriseHub",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_elite_css()

st.title("AGENT TRACE VIEWER")
st.markdown("### Agent Mesh Routing | Task Lifecycle | Latency Analytics | Execution Traces")

# ── Demo Data ────────────────────────────────────────────────────────────

random.seed(43)

agents = [
    {"name": "Lead Qualifier", "type": "qualification", "p50_ms": 340, "p95_ms": 890, "success_rate": 0.96, "tasks_24h": 142},
    {"name": "Seller Scorer", "type": "scoring", "p50_ms": 280, "p95_ms": 720, "success_rate": 0.98, "tasks_24h": 89},
    {"name": "Buyer Matcher", "type": "matching", "p50_ms": 450, "p95_ms": 1200, "success_rate": 0.94, "tasks_24h": 67},
    {"name": "CMA Generator", "type": "analysis", "p50_ms": 1200, "p95_ms": 2800, "success_rate": 0.91, "tasks_24h": 23},
    {"name": "Compliance Checker", "type": "compliance", "p50_ms": 120, "p95_ms": 280, "success_rate": 0.99, "tasks_24h": 298},
    {"name": "Intent Decoder", "type": "classification", "p50_ms": 180, "p95_ms": 420, "success_rate": 0.97, "tasks_24h": 312},
    {"name": "Handoff Router", "type": "routing", "p50_ms": 45, "p95_ms": 120, "success_rate": 0.99, "tasks_24h": 56},
    {"name": "Follow-up Scheduler", "type": "scheduling", "p50_ms": 90, "p95_ms": 210, "success_rate": 0.98, "tasks_24h": 178},
]

# Trace example
trace_steps = [
    {"step": 1, "phase": "Think", "action": "Analyze incoming message intent", "duration_ms": 45, "confidence": 0.0},
    {"step": 2, "phase": "Act", "action": "Route to Intent Decoder agent", "duration_ms": 180, "confidence": 0.87},
    {"step": 3, "phase": "Observe", "action": "Intent: seller_inquiry (0.87 confidence)", "duration_ms": 12, "confidence": 0.87},
    {"step": 4, "phase": "Think", "action": "Check handoff thresholds (0.87 > 0.70)", "duration_ms": 8, "confidence": 0.87},
    {"step": 5, "phase": "Act", "action": "Route to Seller Scorer agent", "duration_ms": 280, "confidence": 0.91},
    {"step": 6, "phase": "Observe", "action": "FRS: 72/100, PCS: 68/100 — Warm Seller", "duration_ms": 15, "confidence": 0.91},
    {"step": 7, "phase": "Think", "action": "Generate qualification response", "duration_ms": 22, "confidence": 0.91},
    {"step": 8, "phase": "Act", "action": "Call Claude Sonnet for response generation", "duration_ms": 890, "confidence": 0.93},
    {"step": 9, "phase": "Observe", "action": "Response generated (148 chars, compliant)", "duration_ms": 120, "confidence": 0.93},
    {"step": 10, "phase": "Act", "action": "Apply compliance pipeline (7 stages)", "duration_ms": 45, "confidence": 0.93},
]

# ── KPI Cards ────────────────────────────────────────────────────────────

col1, col2, col3, col4 = st.columns(4)

total_tasks = sum(a["tasks_24h"] for a in agents)
avg_p95 = sum(a["p95_ms"] for a in agents) / len(agents)
avg_success = sum(a["success_rate"] for a in agents) / len(agents)

with col1:
    st.metric("Active Agents", f"{len(agents)}/22")
with col2:
    st.metric("Tasks (24h)", f"{total_tasks:,}")
with col3:
    st.metric("Avg P95 Latency", f"{avg_p95:.0f}ms")
with col4:
    st.metric("Avg Success Rate", f"{avg_success:.1%}")

st.markdown("---")

# ── Agent Latency Comparison ─────────────────────────────────────────────

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Agent Latency (P50 vs P95)")
    fig_latency = go.Figure()
    fig_latency.add_trace(go.Bar(
        y=[a["name"] for a in agents],
        x=[a["p50_ms"] for a in agents],
        name="P50",
        orientation="h",
        marker_color="#3b82f6",
    ))
    fig_latency.add_trace(go.Bar(
        y=[a["name"] for a in agents],
        x=[a["p95_ms"] for a in agents],
        name="P95",
        orientation="h",
        marker_color="#ef4444",
    ))
    fig_latency.update_layout(
        barmode="overlay",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=400,
        margin=dict(l=140, r=20, t=20, b=40),
        xaxis_title="Latency (ms)",
        legend=dict(orientation="h", y=-0.12),
    )
    st.plotly_chart(fig_latency, use_container_width=True)

with col_right:
    st.subheader("Task Volume by Agent")
    fig_volume = px.pie(
        values=[a["tasks_24h"] for a in agents],
        names=[a["name"] for a in agents],
        color_discrete_sequence=px.colors.qualitative.Set3,
        hole=0.4,
    )
    fig_volume.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=400,
        margin=dict(l=20, r=20, t=20, b=40),
    )
    st.plotly_chart(fig_volume, use_container_width=True)

# ── Execution Trace ──────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Execution Trace: Seller Lead Qualification")
st.markdown("*Think-Act-Observe loop for contact `jorge_lead_847`*")

# Confidence trajectory
fig_confidence = go.Figure()
fig_confidence.add_trace(go.Scatter(
    x=[s["step"] for s in trace_steps],
    y=[s["confidence"] for s in trace_steps],
    mode="lines+markers",
    name="Confidence",
    line=dict(color="#22c55e", width=3),
    marker=dict(size=10),
))
fig_confidence.add_hline(y=0.70, line_dash="dash", line_color="#f59e0b",
                          annotation_text="Handoff Threshold (0.70)")
fig_confidence.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    height=250,
    margin=dict(l=40, r=20, t=20, b=40),
    xaxis_title="Step",
    yaxis_title="Confidence",
    yaxis=dict(range=[0, 1.0]),
)
st.plotly_chart(fig_confidence, use_container_width=True)

# Step-by-step trace table
phase_colors = {"Think": "#3b82f6", "Act": "#22c55e", "Observe": "#f59e0b"}

for step in trace_steps:
    color = phase_colors[step["phase"]]
    cols = st.columns([1, 1, 5, 2])
    cols[0].markdown(f"**Step {step['step']}**")
    cols[1].markdown(f"<span style='color:{color};font-weight:bold'>{step['phase']}</span>", unsafe_allow_html=True)
    cols[2].markdown(step["action"])
    cols[3].markdown(f"`{step['duration_ms']}ms`")

# ── Agent Mesh Governance ────────────────────────────────────────────────

st.markdown("---")
st.subheader("Agent Mesh Governance")

st.markdown("""
| Control | Threshold | Status |
|---------|-----------|--------|
| **Emergency Shutdown** | $100/hr spend | Armed |
| **Throttle** | $50/hr spend | Armed |
| **SLA Enforcement** | P95 < 2,000ms | All agents passing |
| **Error Rate Gate** | < 10% per agent | All agents passing |
| **Handoff Confidence** | > 0.70 (Lead→Buyer/Seller) | Active |
| **Circular Prevention** | 30-minute window | Active |
| **Rate Limiting** | 3 handoffs/hr, 10/day per contact | Active |
""")

st.markdown("---")
st.caption(
    "EnterpriseHub Agent Trace Viewer v2026.1 | "
    "Data: demo mode (production reads from AgentMeshCoordinator metrics)"
)
