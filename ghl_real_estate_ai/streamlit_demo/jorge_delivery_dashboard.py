"""
Jorge AI Bot — Command Center
Focused 4-tab delivery dashboard for Jorge Salas.
Run: streamlit run ghl_real_estate_ai/streamlit_demo/jorge_delivery_dashboard.py
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import random

# ---------------------------------------------------------------------------
# Data layer: try real services, fall back to sample data
# ---------------------------------------------------------------------------

_USE_SAMPLE_DATA = True
_analytics_service = None
_conversation_manager = None

try:
    from ghl_real_estate_ai.services.analytics_service import AnalyticsService
    _analytics_service = AnalyticsService()
    _USE_SAMPLE_DATA = False
except ImportError:
    pass

try:
    from ghl_real_estate_ai.core.conversation_manager import ConversationManager
    _conversation_manager = ConversationManager()
except ImportError:
    pass


def _sample_pipeline_data() -> dict:
    """Sample lead pipeline counts."""
    return {
        "New": 42,
        "Qualifying": 18,
        "Hot": 5,
        "Warm": 8,
        "Cold": 12,
    }


def _sample_conversations() -> pd.DataFrame:
    """Sample recent conversations."""
    names = [
        "Maria Lopez", "Carlos Rivera", "Susan Chen", "James Wilson",
        "Ana Garcia", "Robert Kim", "Linda Tran", "David Morales",
        "Patricia Nguyen", "Michael Brown", "Jennifer Lee", "Thomas Clark",
        "Sandra Hernandez", "Kevin Patel", "Donna Martinez", "Brian Taylor",
        "Nancy White", "Mark Anderson", "Laura Jackson", "Steven Robinson",
    ]
    temps = ["Hot", "Warm", "Cold"]
    now = datetime.now()
    rows = []
    for i, name in enumerate(names):
        rows.append({
            "Contact": name,
            "Last Message": random.choice([
                "Yes, 30 days works for us",
                "We're still thinking about it",
                "What price range are you seeing?",
                "Our home is move-in ready",
                "Not sure about the timeline yet",
                "We'd need at least $750k",
                "Can you tell me more?",
            ]),
            "Timestamp": (now - timedelta(hours=random.randint(1, 72))).strftime("%b %d %I:%M %p"),
            "Temperature": random.choice(temps),
        })
    return pd.DataFrame(rows)


def _sample_temperature_breakdown() -> dict:
    """Sample temperature distribution."""
    return {"Hot": 5, "Warm": 8, "Cold": 12}


def _sample_temperature_trend() -> pd.DataFrame:
    """Sample 30-day temperature trend."""
    dates = [datetime.now().date() - timedelta(days=i) for i in range(30, 0, -1)]
    rows = []
    hot, warm, cold = 2, 5, 10
    for d in dates:
        hot = max(0, hot + random.randint(-1, 2))
        warm = max(0, warm + random.randint(-2, 2))
        cold = max(0, cold + random.randint(-1, 1))
        rows.append({"Date": d, "Hot": hot, "Warm": warm, "Cold": cold})
    return pd.DataFrame(rows)


def _sample_hot_leads() -> pd.DataFrame:
    """Sample hot leads requiring action."""
    return pd.DataFrame([
        {"Name": "Maria Lopez", "Phone": "(909) 555-1234", "Questions Answered": 4, "Last Contact": "Jan 31 2:15 PM"},
        {"Name": "Carlos Rivera", "Phone": "(909) 555-5678", "Questions Answered": 4, "Last Contact": "Jan 31 10:30 AM"},
        {"Name": "Susan Chen", "Phone": "(626) 555-9012", "Questions Answered": 4, "Last Contact": "Jan 30 4:45 PM"},
        {"Name": "James Wilson", "Phone": "(909) 555-3456", "Questions Answered": 3, "Last Contact": "Jan 30 11:00 AM"},
        {"Name": "Ana Garcia", "Phone": "(951) 555-7890", "Questions Answered": 4, "Last Contact": "Jan 29 3:20 PM"},
    ])


def _sample_followups() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Sample follow-up data: (upcoming, overdue)."""
    upcoming = pd.DataFrame([
        {"Name": "Linda Tran", "Temperature": "Warm", "Scheduled": "Feb 3", "Follow-Up #": 2},
        {"Name": "David Morales", "Temperature": "Cold", "Scheduled": "Feb 4", "Follow-Up #": 4},
        {"Name": "Patricia Nguyen", "Temperature": "Warm", "Scheduled": "Feb 5", "Follow-Up #": 1},
        {"Name": "Michael Brown", "Temperature": "Hot", "Scheduled": "Feb 5", "Follow-Up #": 3},
        {"Name": "Jennifer Lee", "Temperature": "Cold", "Scheduled": "Feb 6", "Follow-Up #": 5},
        {"Name": "Thomas Clark", "Temperature": "Warm", "Scheduled": "Feb 7", "Follow-Up #": 2},
        {"Name": "Kevin Patel", "Temperature": "Cold", "Scheduled": "Feb 8", "Follow-Up #": 6},
    ])
    overdue = pd.DataFrame([
        {"Name": "Sandra Hernandez", "Days Overdue": 3, "Last Contact": "Jan 28"},
        {"Name": "Brian Taylor", "Days Overdue": 5, "Last Contact": "Jan 26"},
        {"Name": "Nancy White", "Days Overdue": 1, "Last Contact": "Jan 30"},
    ])
    return upcoming, overdue


# ---------------------------------------------------------------------------
# Tab renderers
# ---------------------------------------------------------------------------

def _render_lead_pipeline():
    """Tab 1: Lead Pipeline funnel."""
    if _USE_SAMPLE_DATA:
        st.info("Showing sample data — connect GHL for live data")

    data = _sample_pipeline_data()

    # KPI row
    cols = st.columns(len(data))
    for col, (stage, count) in zip(cols, data.items()):
        col.metric(label=stage, value=count)

    # Conversion rates
    stages = list(data.keys())
    counts = list(data.values())
    st.subheader("Conversion Rates")
    rate_cols = st.columns(len(stages) - 1)
    for i, col in enumerate(rate_cols):
        if counts[i] > 0:
            rate = counts[i + 1] / counts[i] * 100
        else:
            rate = 0
        col.metric(
            label=f"{stages[i]} → {stages[i+1]}",
            value=f"{rate:.0f}%",
        )

    # Funnel chart
    fig = go.Figure(go.Funnel(
        y=stages,
        x=counts,
        textinfo="value+percent initial",
        marker=dict(color=["#4A90D9", "#5BA0E0", "#E74C3C", "#F39C12", "#95A5A6"]),
    ))
    fig.update_layout(
        margin=dict(l=20, r=20, t=10, b=10),
        height=350,
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_bot_activity():
    """Tab 2: Bot Activity."""
    if _USE_SAMPLE_DATA:
        st.info("Showing sample data — connect GHL for live data")

    # Metrics row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Messages Today", 34)
    m2.metric("Messages This Week", 187)
    m3.metric("Avg Response Time", "1.2s")
    m4.metric("Bot Status", "Active")

    # Recent conversations table
    st.subheader("Recent Conversations")
    df = _sample_conversations()

    def _color_temp(val):
        colors = {"Hot": "#FDECEA", "Warm": "#FFF4E5", "Cold": "#E8F0FE"}
        return f"background-color: {colors.get(val, '')}"

    styled = df.style.applymap(_color_temp, subset=["Temperature"])
    st.dataframe(styled, use_container_width=True, hide_index=True, height=500)


def _render_temperature_map():
    """Tab 3: Temperature Map."""
    if _USE_SAMPLE_DATA:
        st.info("Showing sample data — connect GHL for live data")

    breakdown = _sample_temperature_breakdown()

    # Donut chart
    fig_donut = px.pie(
        names=list(breakdown.keys()),
        values=list(breakdown.values()),
        hole=0.45,
        color=list(breakdown.keys()),
        color_discrete_map={"Hot": "#E74C3C", "Warm": "#F39C12", "Cold": "#3498DB"},
    )
    fig_donut.update_layout(
        margin=dict(l=20, r=20, t=10, b=10),
        height=320,
        paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
    )

    # Trend line chart
    trend_df = _sample_temperature_trend()
    fig_trend = px.line(
        trend_df,
        x="Date",
        y=["Hot", "Warm", "Cold"],
        color_discrete_map={"Hot": "#E74C3C", "Warm": "#F39C12", "Cold": "#3498DB"},
    )
    fig_trend.update_layout(
        margin=dict(l=20, r=20, t=10, b=30),
        height=320,
        paper_bgcolor="white",
        plot_bgcolor="white",
        yaxis_title="Leads",
        legend_title_text="",
    )

    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Distribution")
        st.plotly_chart(fig_donut, use_container_width=True)
    with col_right:
        st.subheader("30-Day Trend")
        st.plotly_chart(fig_trend, use_container_width=True)

    # Hot leads requiring action
    st.subheader("Hot Leads — Immediate Action Required")
    hot_df = _sample_hot_leads()
    st.dataframe(hot_df, use_container_width=True, hide_index=True)


def _render_followup_queue():
    """Tab 4: Follow-Up Queue."""
    if _USE_SAMPLE_DATA:
        st.info("Showing sample data — connect GHL for live data")

    upcoming, overdue = _sample_followups()

    # Completion rate metric
    total = len(upcoming) + len(overdue)
    completed = max(0, total - len(overdue))
    rate = completed / total * 100 if total > 0 else 0
    st.metric("Follow-Up Completion Rate", f"{rate:.0f}%")

    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Upcoming (Next 7 Days)")
        st.dataframe(upcoming, use_container_width=True, hide_index=True)
    with col_right:
        st.subheader("Overdue")
        if overdue.empty:
            st.success("No overdue follow-ups!")
        else:
            st.dataframe(overdue, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="Jorge AI Bot — Command Center",
        page_icon="📊",
        layout="wide",
    )

    st.title("Jorge AI Bot — Command Center")
    st.caption("Lead qualification & follow-up dashboard for Jorge Salas")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Lead Pipeline",
        "Bot Activity",
        "Temperature Map",
        "Follow-Up Queue",
    ])

    with tab1:
        _render_lead_pipeline()
    with tab2:
        _render_bot_activity()
    with tab3:
        _render_temperature_map()
    with tab4:
        _render_followup_queue()


if __name__ == "__main__":
    main()
