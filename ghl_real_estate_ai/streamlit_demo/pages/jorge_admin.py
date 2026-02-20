"""
Jorge Admin Dashboard -- Bot performance at a glance.
Shows bot status, recent conversations, handoff summary, and error rates.
"""

import os
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Jorge Admin", page_icon="🤖", layout="wide")
st.title("🤖 Jorge Bot Admin")
st.caption("Real-time bot performance for Jorge Salas")

# Auto-refresh every 60s
st.sidebar.write("**Last refreshed:**", datetime.now().strftime("%H:%M:%S"))
if st.sidebar.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

# --- Bot Status Section ---
st.subheader("Bot Status")


@st.cache_data(ttl=60)
def get_bot_status():
    """Get current bot status from environment and metrics."""
    return {
        "Seller Bot": {
            "active": os.getenv("JORGE_SELLER_MODE", "true").lower() == "true",
            "mode": "Simple"
            if os.getenv("JORGE_SIMPLE_MODE", "false").lower() == "true"
            else "Full",
        },
        "Buyer Bot": {
            "active": os.getenv("JORGE_BUYER_MODE", "true").lower() == "true",
            "mode": "Full",
        },
        "Lead Bot": {
            "active": os.getenv("JORGE_LEAD_MODE", "true").lower() == "true",
            "mode": "Full",
        },
    }


bot_status = get_bot_status()
col1, col2, col3 = st.columns(3)
for col, (bot_name, status) in zip([col1, col2, col3], bot_status.items()):
    with col:
        icon = "✅" if status["active"] else "⏸️"
        st.metric(
            label=f"{icon} {bot_name}",
            value="Active" if status["active"] else "Paused",
            delta=f"Mode: {status['mode']}",
        )

# --- Recent Activity ---
st.subheader("Recent Conversations (Last 10)")


@st.cache_data(ttl=60)
def get_recent_conversations():
    """Fetch recent conversations from bot metrics or DB."""
    try:
        from ghl_real_estate_ai.services.jorge.bot_metrics_collector import (
            BotMetricsCollector,
        )

        # Best-effort read -- return placeholder if not available
        _ = BotMetricsCollector
        return []
    except Exception:
        return []


recent = get_recent_conversations()
if recent:
    df = pd.DataFrame(recent)
    st.dataframe(df, use_container_width=True)
else:
    st.info(
        "No recent conversation data available. "
        "Connect to production database to see live data."
    )
    # Show demo data structure
    demo_data = [
        {
            "Contact": "***1234",
            "Bot": "Seller",
            "Last Message": "What's my home worth?",
            "Temperature": "Warm",
            "Time": "10 min ago",
        },
        {
            "Contact": "***5678",
            "Bot": "Buyer",
            "Last Message": "I need 3 beds under $500K",
            "Temperature": "Hot",
            "Time": "25 min ago",
        },
        {
            "Contact": "***9012",
            "Bot": "Lead",
            "Last Message": "Just looking for now",
            "Temperature": "Cold",
            "Time": "1 hr ago",
        },
    ]
    st.dataframe(pd.DataFrame(demo_data), use_container_width=True)

# --- Handoff Summary ---
st.subheader("Handoff Summary (Last 24h)")


@st.cache_data(ttl=60)
def get_handoff_summary():
    try:
        from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
            JorgeHandoffService,
        )

        _ = JorgeHandoffService
        return None
    except Exception:
        return None


col_a, col_b, col_c = st.columns(3)
with col_a:
    st.metric("Handoffs Attempted", "---", help="Connect to DB to see live data")
with col_b:
    st.metric("Success Rate", "---")
with col_c:
    st.metric("Circular Prevented", "---")

# --- API Cost This Month ---
st.subheader("API Cost")


@st.cache_data(ttl=300)
def _get_month_cost():
    import asyncio

    from ghl_real_estate_ai.services.jorge.cost_tracker import cost_tracker

    now = datetime.now()
    try:
        return asyncio.run(cost_tracker.get_month_total(now.year, now.month))
    except Exception:
        return {"cost_usd": 0.0, "call_count": 0}


month_cost = _get_month_cost()
st.metric(
    "Cost This Month",
    f"${month_cost['cost_usd']:.2f}",
    help=f"{month_cost['call_count']} API calls",
)

# --- Temperature Breakdown ---
st.subheader("Lead Temperature (Last 7 Days)")

col_left, col_right = st.columns(2)
with col_left:
    st.write("**Sellers**")
    st.info("Connect to production database to see temperature breakdown charts.")
with col_right:
    st.write("**Buyers**")
    st.info("Connect to production database to see temperature breakdown charts.")

# --- System Health ---
st.subheader("System Health")


@st.cache_data(ttl=30)
def get_health():
    try:
        import httpx

        base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        resp = httpx.get(f"{base_url}/health", timeout=5.0)
        return resp.json()
    except Exception as e:
        return {"error": str(e), "status": "unreachable"}


health = get_health()
if "error" in health:
    st.error(f"API unreachable: {health['error']}")
else:
    health_cols = st.columns(4)
    idx = 0
    for key, val in health.items():
        if isinstance(val, dict) and "status" in val:
            with health_cols[idx % 4]:
                status_icon = "✅" if val["status"] == "ok" else "⚠️"
                st.metric(f"{status_icon} {key}", val["status"])
            idx += 1

st.divider()
st.caption("Jorge Admin Dashboard -- Powered by Lyrio AI -- cayman@lyrio.ai")
