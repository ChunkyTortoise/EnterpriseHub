"""Streamlit dashboard for voice call analytics.

Run with: streamlit run src/voice_ai/dashboard/call_analytics_app.py
"""

from __future__ import annotations

try:
    import datetime

    import streamlit as st

    st.set_page_config(page_title="Voice AI Analytics", page_icon="📞", layout="wide")
    st.title("Voice AI Platform — Call Analytics")

    # Sidebar filters
    st.sidebar.header("Filters")
    period = st.sidebar.selectbox("Time Period", ["1d", "7d", "30d", "90d"], index=1)
    bot_type = st.sidebar.multiselect(
        "Bot Type", ["lead", "buyer", "seller"], default=["lead", "buyer", "seller"]
    )

    # Main metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Calls", "0", delta=None)
    with col2:
        st.metric("Avg Duration", "0:00", delta=None)
    with col3:
        st.metric("Appointments Booked", "0", delta=None)
    with col4:
        st.metric("Avg Sentiment", "N/A", delta=None)

    st.divider()

    # Charts
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.subheader("Call Volume")
        st.info("Connect to the API to see call volume data.")

    with chart_col2:
        st.subheader("Sentiment Distribution")
        st.info("Connect to the API to see sentiment data.")

    # Cost breakdown
    st.subheader("Cost Breakdown")
    cost_col1, cost_col2, cost_col3 = st.columns(3)
    with cost_col1:
        st.metric("Total Revenue", "$0.00")
    with cost_col2:
        st.metric("Total COGS", "$0.00")
    with cost_col3:
        st.metric("Gross Margin", "0%")

    st.divider()

    # Recent calls table
    st.subheader("Recent Calls")
    st.info("Connect to the API to see recent calls.")

except ImportError:
    # Allow importing without streamlit installed (for testing)
    pass
