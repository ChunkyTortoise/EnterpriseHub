"""
EnterpriseHub BI Dashboard - Streamlit Cloud Deployment
Mock data for demo purposes - no real DB connection needed
"""

import hashlib
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="EnterpriseHub BI Dashboard", page_icon="🏠", layout="wide", initial_sidebar_state="expanded"
)

# Custom CSS for EnterpriseHub styling
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A5F;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 20px;
        color: white;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Mock data generators
@st.cache_data(ttl=3600)
def get_mock_leads():
    """Generate mock lead data for demo"""
    np.random.seed(42)
    n_leads = 150

    data = {
        "lead_id": [f"LD-{i:04d}" for i in range(n_leads)],
        "name": [f"Lead {i}" for i in range(n_leads)],
        "score": np.random.randint(20, 100, n_leads),
        "temperature": np.random.choice(["Hot", "Warm", "Cold"], n_leads, p=[0.2, 0.5, 0.3]),
        "source": np.random.choice(["Website", "Referral", "Social", "Paid Ads"], n_leads),
        "created_at": [datetime.now() - timedelta(days=np.random.randint(0, 30)) for _ in range(n_leads)],
        "status": np.random.choice(["New", "Contacted", "Qualified", "Proposal", "Closed"], n_leads),
        "budget": np.random.randint(300000, 2000000, n_leads),
    }
    return pd.DataFrame(data)


@st.cache_data(ttl=3600)
def get_mock_bot_performance():
    """Generate mock bot performance metrics"""
    np.random.seed(123)
    bots = ["LeadBot", "BuyerBot", "SellerBot"]

    data = {
        "bot": bots,
        "conversations": [np.random.randint(100, 500) for _ in bots],
        "avg_response_time": [np.random.uniform(0.5, 2.0) for _ in bots],
        "handoffs": [np.random.randint(5, 30) for _ in bots],
        "success_rate": [np.random.uniform(0.75, 0.95) for _ in bots],
        "satisfaction_score": [np.random.uniform(4.0, 5.0) for _ in bots],
    }
    return pd.DataFrame(data)


@st.cache_data(ttl=3600)
def get_mock_forecast_data():
    """Generate Monte Carlo forecast data"""
    np.random.seed(456)
    days = 30
    dates = [datetime.now() + timedelta(days=i) for i in range(days)]

    # Simulate Monte Carlo results
    base_value = 50
    forecasts = {
        "date": dates,
        "p10": [base_value + np.random.normal(0, 5) * i + i * 0.5 for i in range(days)],
        "p50": [base_value + np.random.normal(0, 3) * i + i * 0.7 for i in range(days)],
        "p90": [base_value + np.random.normal(0, 8) * i + i * 0.9 for i in range(days)],
    }
    return pd.DataFrame(forecasts)


@st.cache_data(ttl=3600)
def get_mock_revenue_data():
    """Generate mock revenue data"""
    np.random.seed(789)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]

    data = {
        "month": months,
        "revenue": [np.random.randint(50000, 150000) for _ in months],
        "leads": [np.random.randint(20, 60) for _ in months],
        "conversions": [np.random.randint(5, 20) for _ in months],
    }
    return pd.DataFrame(data)


def main():
    """Main dashboard application"""

    # Header
    st.markdown('<div class="main-header">🏠 EnterpriseHub BI Dashboard</div>', unsafe_allow_html=True)
    st.markdown("**Real Estate AI & Business Intelligence Platform** | Rancho Cucamonga Market")

    # Sidebar
    with st.sidebar:
        st.title("📊 Navigation")
        page = st.radio("Select View", ["Overview", "Lead Analytics", "Bot Performance", "Revenue Forecast"])

        st.markdown("---")
        st.markdown("### Demo Mode")
        st.info("Using mock data for demonstration. Connect to live database for production.")

        st.markdown("---")
        st.markdown("**Quick Stats**")
        leads = get_mock_leads()
        st.metric("Total Leads", len(leads))
        st.metric("Avg Score", f"{leads['score'].mean():.0f}")

    # Main content based on selection
    if page == "Overview":
        show_overview()
    elif page == "Lead Analytics":
        show_lead_analytics(leads)
    elif page == "Bot Performance":
        show_bot_performance()
    elif page == "Revenue Forecast":
        show_forecast()


def show_overview():
    """Overview dashboard"""
    col1, col2, col3, col4 = st.columns(4)

    leads = get_mock_leads()
    bots = get_mock_bot_performance()

    with col1:
        st.metric("Total Leads", len(leads), delta=f"+{np.random.randint(5, 20)}")
    with col2:
        hot_leads = len(leads[leads["temperature"] == "Hot"])
        st.metric("Hot Leads", hot_leads, delta=f"+{np.random.randint(1, 5)}")
    with col3:
        avg_score = leads["score"].mean()
        st.metric("Avg Score", f"{avg_score:.0f}", delta=f"+{np.random.randint(1, 5)}")
    with col4:
        total_conv = bots["conversations"].sum()
        st.metric("Conversations", total_conv, delta=f"+{np.random.randint(10, 50)}")

    st.markdown("---")

    # Charts row
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Lead Temperature Distribution")
        temp_counts = leads["temperature"].value_counts()
        fig = px.pie(
            values=temp_counts.values,
            names=temp_counts.index,
            color_discrete_sequence=["#FF6B6B", "#FFD93D", "#6BCB77"],
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Monthly Revenue Trend")
        rev_data = get_mock_revenue_data()
        fig = px.bar(rev_data, x="month", y="revenue", color_discrete_sequence=["#667eea"])
        st.plotly_chart(fig, use_container_width=True)


def show_lead_analytics(leads):
    """Lead analytics page"""
    st.subheader("🎯 Lead Analytics")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        temp_filter = st.multiselect("Temperature", ["Hot", "Warm", "Cold"], default=["Hot", "Warm", "Cold"])
    with col2:
        source_filter = st.multiselect("Source", leads["source"].unique())
    with col3:
        status_filter = st.multiselect("Status", leads["status"].unique())

    # Apply filters
    filtered = leads.copy()
    if temp_filter:
        filtered = filtered[filtered["temperature"].isin(temp_filter)]
    if source_filter:
        filtered = filtered[filtered["source"].isin(source_filter)]
    if status_filter:
        filtered = filtered[filtered["status"].isin(status_filter)]

    st.markdown(f"Showing **{len(filtered)}** leads")

    # Lead score distribution
    st.subheader("Lead Score Distribution")
    fig = px.histogram(
        filtered,
        x="score",
        color="temperature",
        color_discrete_map={"Hot": "#FF6B6B", "Warm": "#FFD93D", "Cold": "#6BCB77"},
    )
    st.plotly_chart(fig, use_container_width=True)

    # Data table
    st.subheader("Lead Details")
    st.dataframe(
        filtered[["lead_id", "name", "score", "temperature", "source", "status", "budget"]], use_container_width=True
    )


def show_bot_performance():
    """Bot performance metrics"""
    st.subheader("🤖 Bot Performance Metrics")

    bots = get_mock_bot_performance()

    # Metrics row
    col1, col2, col3 = st.columns(3)

    for idx, bot in bots.iterrows():
        with [col1, col2, col3][idx]:
            st.markdown(
                f"""
            <div class="metric-card">
                <div class="metric-label">{bot["bot"]}</div>
                <div class="metric-value">{bot["conversations"]}</div>
                <div>Conversations</div>
                <div>Success: {bot["success_rate"]:.1%}</div>
                <div>⭐ {bot["satisfaction_score"]:.1f}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("---")

    # Performance comparison
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Response Time by Bot")
        fig = px.bar(bots, x="bot", y="avg_response_time", color_discrete_sequence=["#667eea"])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Handoffs by Bot")
        fig = px.bar(
            bots, x="bot", y="handoffs", color="bot", color_discrete_sequence=["#667eea", "#764ba2", "#f093fb"]
        )
        st.plotly_chart(fig, use_container_width=True)


def show_forecast():
    """Revenue forecast with Monte Carlo simulation"""
    st.subheader("📈 Revenue Forecast (Monte Carlo)")

    forecast = get_mock_forecast_data()

    # Monte Carlo chart
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=forecast["date"],
            y=forecast["p90"],
            mode="lines",
            name="P90 (Optimistic)",
            line=dict(color="green", width=1),
            fill="tonexty",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=forecast["date"],
            y=forecast["p50"],
            mode="lines",
            name="P50 (Most Likely)",
            line=dict(color="blue", width=2),
            fill="tonexty",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=forecast["date"],
            y=forecast["p10"],
            mode="lines",
            name="P10 (Conservative)",
            line=dict(color="red", width=1),
            fill="tonexty",
        )
    )

    fig.update_layout(
        title="30-Day Revenue Forecast with Confidence Intervals",
        xaxis_title="Date",
        yaxis_title="Projected Revenue ($)",
        template="plotly_white",
    )

    st.plotly_chart(fig, use_container_width=True)

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Optimistic (P90)", f"${forecast['p90'].iloc[-1]:,.0f}")
    with col2:
        st.metric("Most Likely (P50)", f"${forecast['p50'].iloc[-1]:,.0f}")
    with col3:
        st.metric("Conservative (P10)", f"${forecast['p10'].iloc[-1]:,.0f}")


if __name__ == "__main__":
    main()
