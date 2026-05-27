"""
LLM Cost Analytics Dashboard.

Visualizes token usage, cost trends, cache savings, and model-level
breakdown. Demonstrates production LLM cost optimization.
"""

import json
import pathlib

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ghl_real_estate_ai.streamlit_demo.obsidian_theme import inject_elite_css, style_obsidian_chart

# Load cost data from committed sample file
_SAMPLE_PATH = pathlib.Path(__file__).parents[4] / "benchmarks/results/llm_cost_sample.json"


def _load_cost_data() -> tuple[list[dict], list[dict], list[dict]]:
    """Load cost data from sample JSON. Returns (daily_data, model_data, bot_data)."""
    if _SAMPLE_PATH.exists():
        data = json.loads(_SAMPLE_PATH.read_text())
        return data["daily"], data["by_model"], data["by_bot"]
    return [], [], []


daily_data, model_data, bot_data = _load_cost_data()

st.set_page_config(
    page_title="LLM Cost Analytics | EnterpriseHub",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_elite_css()

st.title("LLM COST ANALYTICS")
st.markdown("### Token Usage | Cost Optimization | Cache Savings | Model Breakdown")
st.info("Sample data from test-run records. " "Connect PostgreSQL (DATABASE_URL) for live cost tracking.")

# ── KPI Cards ────────────────────────────────────────────────────────────

col1, col2, col3, col4 = st.columns(4)

total_cost = sum(d["cost_usd"] for d in daily_data)
total_savings = sum(d["savings_usd"] for d in daily_data)
total_requests = sum(m["requests"] for m in model_data)
avg_cost_per_request = total_cost / total_requests if total_requests else 0

with col1:
    st.metric("30-Day Cost", f"${total_cost:.2f}", delta="-89% vs. no cache")

with col2:
    st.metric(
        "Cache Savings",
        f"${total_savings:.2f}",
        delta=f"{total_savings / (total_cost + total_savings) * 100:.0f}% saved",
    )

with col3:
    st.metric("Total Requests", f"{total_requests:,}")

with col4:
    st.metric("Avg Cost/Request", f"${avg_cost_per_request:.4f}")

st.markdown("---")

# ── Cost Trend Chart ─────────────────────────────────────────────────────

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Daily Cost vs. Cache Savings")
    fig_cost = go.Figure()
    fig_cost.add_trace(
        go.Bar(
            x=[d["date"] for d in daily_data],
            y=[d["cost_usd"] for d in daily_data],
            name="Actual Cost",
            marker_color="#ef4444",
        )
    )
    fig_cost.add_trace(
        go.Bar(
            x=[d["date"] for d in daily_data],
            y=[d["savings_usd"] for d in daily_data],
            name="Cache Savings",
            marker_color="#22c55e",
        )
    )
    fig_cost.update_layout(
        barmode="stack",
        height=400,
        margin=dict(l=40, r=20, t=20, b=40),
        legend=dict(orientation="h", y=-0.15),
    )
    fig_cost = style_obsidian_chart(fig_cost)
    st.plotly_chart(fig_cost, use_container_width=True)

with col_right:
    st.subheader("Token Usage by Type")
    fig_tokens = go.Figure()
    fig_tokens.add_trace(
        go.Scatter(
            x=[d["date"] for d in daily_data],
            y=[d["input_tokens"] for d in daily_data],
            name="Input Tokens",
            mode="lines+markers",
            line=dict(color="#3b82f6"),
        )
    )
    fig_tokens.add_trace(
        go.Scatter(
            x=[d["date"] for d in daily_data],
            y=[d["output_tokens"] for d in daily_data],
            name="Output Tokens",
            mode="lines+markers",
            line=dict(color="#f59e0b"),
        )
    )
    fig_tokens.add_trace(
        go.Scatter(
            x=[d["date"] for d in daily_data],
            y=[d["cache_hits"] for d in daily_data],
            name="Cache Hits",
            mode="lines+markers",
            line=dict(color="#22c55e", dash="dot"),
        )
    )
    fig_tokens.update_layout(
        height=400,
        margin=dict(l=40, r=20, t=20, b=40),
        legend=dict(orientation="h", y=-0.15),
    )
    fig_tokens = style_obsidian_chart(fig_tokens)
    st.plotly_chart(fig_tokens, use_container_width=True)

# ── Model Breakdown ──────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Cost by Model")

col_model_left, col_model_right = st.columns(2)

with col_model_left:
    fig_model = px.bar(
        model_data,
        x="model",
        y="cost",
        color="model",
        text_auto=".2f",
        color_discrete_sequence=["#3b82f6", "#22c55e", "#f59e0b"],
    )
    fig_model.update_layout(
        height=350,
        showlegend=False,
        xaxis_title="",
        yaxis_title="Cost (USD)",
        margin=dict(l=40, r=20, t=20, b=80),
    )
    fig_model = style_obsidian_chart(fig_model)
    st.plotly_chart(fig_model, use_container_width=True)

with col_model_right:
    st.markdown("#### Model Performance")
    for m in model_data:
        st.markdown(f"**{m['model']}**")
        cols = st.columns(3)
        cols[0].metric("Requests", f"{m['requests']:,}")
        cols[1].metric("Cost", f"${m['cost']:.2f}")
        cols[2].metric("Cache Rate", f"{m['cache_rate']:.0%}")

# ── Bot Breakdown ────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Cost by Bot")

for bot in bot_data:
    col_b1, col_b2, col_b3, col_b4 = st.columns(4)
    col_b1.markdown(f"**{bot['bot']}**")
    col_b2.metric("Requests", f"{bot['requests']:,}")
    col_b3.metric("Avg Tokens", f"{bot['avg_tokens']:,}")
    col_b4.metric("Avg Cost", f"${bot['avg_cost']:.4f}")

# ── Cost Optimization Insights ───────────────────────────────────────────

st.markdown("---")
st.subheader("Cost Optimization Stack")

st.markdown("""
| Layer | Strategy | Impact |
|-------|----------|--------|
| **L1 Cache** | In-memory LRU (1,000 items) | 59% hit rate, <1ms |
| **L2 Cache** | Redis (15min TTL) | 21% hit rate, <5ms |
| **L3 Cache** | PostgreSQL (persistent) | 8% hit rate, <20ms |
| **Model Routing** | Haiku for simple tasks, Sonnet for complex | 40% cost reduction |
| **Prompt Caching** | Claude cache_control blocks | 90% discount on repeated context |
| **Emergency Shutdown** | Agent Mesh $100/hr spend limit | Prevents runaway costs |
""")

st.markdown("---")
st.caption(
    "EnterpriseHub LLM Cost Analytics v2026.1 | "
    "Data: demo mode (production reads from llm_cost_log table via CostTracker)"
)
