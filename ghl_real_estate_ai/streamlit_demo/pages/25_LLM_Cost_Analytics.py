"""
LLM Cost Analytics Dashboard.

Visualizes token usage, cost trends, cache savings, and model-level
breakdown. Demonstrates production LLM cost optimization.
"""

import random
from datetime import datetime, timedelta

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ghl_real_estate_ai.streamlit_demo.obsidian_theme import inject_elite_css, style_obsidian_chart

st.set_page_config(
    page_title="LLM Cost Analytics | EnterpriseHub",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_elite_css()

st.title("LLM COST ANALYTICS")
st.markdown("### Token Usage | Cost Optimization | Cache Savings | Model Breakdown")

# ── Demo Data (production would read from llm_cost_log table) ────────────

random.seed(42)  # Reproducible demo data

# Generate 30 days of cost data
dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]
daily_data = []
for d in dates:
    input_tok = random.randint(8000, 25000)
    output_tok = random.randint(2000, 8000)
    cache_hits = random.randint(4000, 18000)
    cost = (input_tok * 3.0 / 1_000_000) + (output_tok * 15.0 / 1_000_000)
    savings = cache_hits * 3.0 / 1_000_000  # What cache hits saved
    daily_data.append({
        "date": d.strftime("%Y-%m-%d"),
        "input_tokens": input_tok,
        "output_tokens": output_tok,
        "cache_hits": cache_hits,
        "cost_usd": round(cost, 4),
        "savings_usd": round(savings, 4),
    })

# Model breakdown
model_data = [
    {"model": "claude-sonnet-4-20250514", "requests": 1842, "tokens": 2_450_000, "cost": 18.90, "cache_rate": 0.62},
    {"model": "claude-haiku-4-5-20251001", "requests": 3210, "tokens": 890_000, "cost": 2.45, "cache_rate": 0.71},
    {"model": "gemini-2.0-flash", "requests": 456, "tokens": 340_000, "cost": 0.85, "cache_rate": 0.45},
]

# Bot breakdown
bot_data = [
    {"bot": "Lead Bot", "requests": 2890, "avg_tokens": 1240, "avg_cost": 0.0042},
    {"bot": "Seller Bot", "requests": 1580, "avg_tokens": 1680, "avg_cost": 0.0058},
    {"bot": "Buyer Bot", "requests": 1038, "avg_tokens": 1520, "avg_cost": 0.0052},
]

# ── KPI Cards ────────────────────────────────────────────────────────────

col1, col2, col3, col4 = st.columns(4)

total_cost = sum(d["cost_usd"] for d in daily_data)
total_savings = sum(d["savings_usd"] for d in daily_data)
total_requests = sum(m["requests"] for m in model_data)
avg_cost_per_request = total_cost / total_requests if total_requests else 0

with col1:
    st.metric("30-Day Cost", f"${total_cost:.2f}", delta="-89% vs. no cache")

with col2:
    st.metric("Cache Savings", f"${total_savings:.2f}", delta=f"{total_savings/(total_cost+total_savings)*100:.0f}% saved")

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
    fig_cost.add_trace(go.Bar(
        x=[d["date"] for d in daily_data],
        y=[d["cost_usd"] for d in daily_data],
        name="Actual Cost",
        marker_color="#ef4444",
    ))
    fig_cost.add_trace(go.Bar(
        x=[d["date"] for d in daily_data],
        y=[d["savings_usd"] for d in daily_data],
        name="Cache Savings",
        marker_color="#22c55e",
    ))
    fig_cost.update_layout(
        barmode="stack"
        height=400,
        margin=dict(l=40, r=20, t=20, b=40),
        legend=dict(orientation="h", y=-0.15),
    )
    fig_cost = style_obsidian_chart(fig_cost)
    st.plotly_chart(fig_cost, use_container_width=True)

with col_right:
    st.subheader("Token Usage by Type")
    fig_tokens = go.Figure()
    fig_tokens.add_trace(go.Scatter(
        x=[d["date"] for d in daily_data],
        y=[d["input_tokens"] for d in daily_data],
        name="Input Tokens",
        mode="lines+markers",
        line=dict(color="#3b82f6"),
    ))
    fig_tokens.add_trace(go.Scatter(
        x=[d["date"] for d in daily_data],
        y=[d["output_tokens"] for d in daily_data],
        name="Output Tokens",
        mode="lines+markers",
        line=dict(color="#f59e0b"),
    ))
    fig_tokens.add_trace(go.Scatter(
        x=[d["date"] for d in daily_data],
        y=[d["cache_hits"] for d in daily_data],
        name="Cache Hits",
        mode="lines+markers",
        line=dict(color="#22c55e", dash="dot"),
    ))
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
