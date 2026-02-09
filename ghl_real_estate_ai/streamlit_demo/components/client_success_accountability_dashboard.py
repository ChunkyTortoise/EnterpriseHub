"""
Client Success & Accountability Dashboard

Transparent performance measurement and value demonstration platform
that builds trust through verified results and justifies premium pricing.

Features:
- Public-facing agent report card
- Real-time verified metrics
- Value delivered tracking
- Client testimonials showcase
- Premium pricing justification
"""

import asyncio

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from ghl_real_estate_ai.streamlit_demo.async_utils import run_async

from ...services.client_success_scoring_service import get_client_success_service


@st.cache_resource
def get_success_service():
    """Get cached success scoring service"""
    return get_client_success_service()


@st.cache_data(ttl=300)  # 5-minute cache
def load_agent_performance_data(agent_id: str, period_days: int = 30):
    """Load agent performance data with caching"""
    try:
        service = get_success_service()

        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            report = run_async(service.generate_agent_performance_report(agent_id, period_days))
            dashboard_data = run_async(service.get_transparency_dashboard_data(agent_id))
            return report, dashboard_data
        finally:
            loop.close()

    except Exception as e:
        st.error(f"Error loading performance data: {e}")
        return None, None


@st.cache_data(ttl=300)
def load_roi_data(client_id: str, agent_id: str):
    """Load client ROI data with caching"""
    try:
        service = get_success_service()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            roi_report = run_async(service.calculate_client_roi(client_id, agent_id))
            return roi_report
        finally:
            loop.close()

    except Exception as e:
        st.error(f"Error loading ROI data: {e}")
        return None


@st.cache_data(ttl=300)
def load_pricing_justification(agent_id: str, proposed_rate: float):
    """Load pricing justification data"""
    try:
        service = get_success_service()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            justification = run_async(service.justify_premium_pricing(agent_id, proposed_rate))
            return justification
        finally:
            loop.close()

    except Exception as e:
        st.error(f"Error loading pricing justification: {e}")
        return None


def render_client_success_accountability_dashboard():
    """Render the complete Client Success & Accountability Dashboard"""

    # Dashboard Header
    st.markdown(
        """
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 15px; margin-bottom: 2rem;">
        <h1 style="color: white; margin: 0; text-align: center; font-size: 2.5rem;">
            🏆 Client Success & Accountability Center
        </h1>
        <p style="color: white; text-align: center; font-size: 1.2rem; margin-top: 1rem;">
            Transparent Performance Measurement • Verified Results • Premium Value Demonstration
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Configuration Section
    with st.expander("🎯 Dashboard Configuration", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            agent_id = st.selectbox(
                "Select Agent",
                ["jorge_sales", "demo_agent_1", "demo_agent_2"],
                help="Choose agent for performance analysis",
            )

        with col2:
            period_days = st.selectbox("Performance Period", [30, 60, 90, 365], index=0, help="Analysis period in days")

        with col3:
            view_type = st.selectbox(
                "Dashboard View",
                ["Public Report Card", "Executive Summary", "Client ROI", "Pricing Justification"],
                help="Choose dashboard view type",
            )

    # Load data
    report, dashboard_data = load_agent_performance_data(agent_id, period_days)

    if not report:
        st.error("⚠️ Unable to load performance data. Please try again.")
        return

    # Main Dashboard Content
    if view_type == "Public Report Card":
        render_public_report_card(report, dashboard_data)
    elif view_type == "Executive Summary":
        render_executive_summary(report, dashboard_data)
    elif view_type == "Client ROI":
        render_client_roi_view(agent_id)
    elif view_type == "Pricing Justification":
        render_pricing_justification_view(agent_id)


def render_public_report_card(report, dashboard_data):
    """Render public-facing agent report card"""

    if not dashboard_data or "public_metrics" not in dashboard_data:
        st.error("Public metrics not available")
        return

    metrics = dashboard_data["public_metrics"]

    # Agent Success Score (Hero Section)
    st.markdown(
        """
    <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                padding: 2rem; border-radius: 15px; margin-bottom: 2rem; text-align: center;">
        <h2 style="color: white; margin: 0;">Agent Success Score</h2>
        <div style="font-size: 4rem; font-weight: bold; color: white; margin: 1rem 0;">
            {}
        </div>
        <p style="color: white; font-size: 1.2rem; margin: 0;">
            Verified Performance Rating • {} Metrics Verified
        </p>
    </div>
    """.format(f"{metrics['agent_success_score']:.0f}/100", metrics["verification_rate"]),
        unsafe_allow_html=True,
    )

    # Key Performance Metrics
    st.subheader("🎯 Verified Performance Metrics")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Negotiation Performance
        nego_data = metrics["verified_metrics"]["negotiation_performance"]

        st.markdown(
            f"""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; 
                    border-left: 5px solid #ff6b6b; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h4 style="margin-top: 0; color: #ff6b6b;">💰 Negotiation Performance</h4>
            <div style="font-size: 2rem; font-weight: bold; color: #333;">
                {nego_data["achievement"]}
            </div>
            <p style="color: #666; margin-bottom: 0;">
                {nego_data["vs_market"]}
            </p>
            <div style="margin-top: 1rem; padding: 0.5rem; background: #fff5f5; border-radius: 5px;">
                <small style="color: #ff6b6b;">✓ Verified with MLS data</small>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        # Timeline Efficiency
        timeline_data = metrics["verified_metrics"]["timeline_efficiency"]

        st.markdown(
            f"""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; 
                    border-left: 5px solid #4ecdc4; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h4 style="margin-top: 0; color: #4ecdc4;">⚡ Timeline Efficiency</h4>
            <div style="font-size: 2rem; font-weight: bold; color: #333;">
                {timeline_data["achievement"]}
            </div>
            <p style="color: #666; margin-bottom: 0;">
                {timeline_data["vs_market"]}
            </p>
            <div style="margin-top: 1rem; padding: 0.5rem; background: #f0fffe; border-radius: 5px;">
                <small style="color: #4ecdc4;">✓ Verified with transaction data</small>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        # Client Satisfaction
        satisfaction_data = metrics["verified_metrics"]["client_satisfaction"]

        st.markdown(
            f"""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; 
                    border-left: 5px solid #45b7d1; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h4 style="margin-top: 0; color: #45b7d1;">⭐ Client Satisfaction</h4>
            <div style="font-size: 2rem; font-weight: bold; color: #333;">
                {satisfaction_data["achievement"]}
            </div>
            <p style="color: #666; margin-bottom: 0;">
                {satisfaction_data["review_count"]} verified reviews<br>
                {satisfaction_data["vs_market"]}
            </p>
            <div style="margin-top: 1rem; padding: 0.5rem; background: #f0f9ff; border-radius: 5px;">
                <small style="color: #45b7d1;">✓ Verified third-party reviews</small>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Market Ranking & Value Delivered
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1.5rem; border-radius: 15px; text-align: center;">
            <h4 style="color: white; margin-top: 0;">🏅 Market Ranking</h4>
            <div style="font-size: 3rem; font-weight: bold; color: white;">
                {metrics["market_ranking"]}
            </div>
            <p style="color: white; margin-bottom: 0;">
                Performance vs. Local Agents
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                    padding: 1.5rem; border-radius: 15px; text-align: center;">
            <h4 style="color: white; margin-top: 0;">💎 Total Value Delivered</h4>
            <div style="font-size: 3rem; font-weight: bold; color: white;">
                ${metrics["total_value_delivered"]:,.0f}
            </div>
            <p style="color: white; margin-bottom: 0;">
                Client Savings & Benefits
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Success Stories & Testimonials
    st.subheader("🌟 Success Stories & Client Testimonials")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Recent Success Stories**")
        for i, story in enumerate(report.success_stories[:3], 1):
            st.markdown(
                f"""
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;
                        border-left: 4px solid #28a745;">
                <h6 style="margin: 0; color: #28a745;">Success Story #{i}</h6>
                <p style="margin: 0.5rem 0; font-weight: bold;">{story.get("title", "Success Story")}</p>
                <p style="margin: 0; color: #666;">{story.get("description", "Achieved exceptional results")}</p>
                <small style="color: #28a745;">✓ Verified • Value: ${story.get("value_delivered", 0):,.0f}</small>
            </div>
            """,
                unsafe_allow_html=True,
            )

    with col2:
        st.markdown("**Client Testimonials**")
        for testimonial in metrics["recent_testimonials"]:
            stars = "⭐" * int(testimonial.get("rating", 5))
            st.markdown(
                f"""
            <div style="background: #fff; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="margin-bottom: 0.5rem;">{stars}</div>
                <p style="margin: 0.5rem 0; font-style: italic;">"{testimonial.get("comment", "")}"</p>
                <small style="color: #666;">
                    Client {testimonial.get("client_id", "")} • 
                    ✓ Verified Review
                </small>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # Verification Status
    st.subheader("🔐 Verification & Transparency")

    st.markdown(
        f"""
    <div style="background: #e8f5e8; padding: 1.5rem; border-radius: 10px; 
                border: 2px solid #28a745;">
        <h5 style="margin-top: 0; color: #28a745;">
            <i class="fas fa-shield-check"></i> Data Verification Status
        </h5>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>{metrics["verification_rate"]}</strong> of metrics verified<br>
                <small>Last updated: {dashboard_data["last_updated"][:19]}</small>
            </div>
            <div style="text-align: right;">
                <strong>{metrics["success_stories_count"]}</strong> verified success stories<br>
                <small>All data sources validated</small>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_executive_summary(report, dashboard_data):
    """Render executive performance summary"""

    st.subheader("📊 Executive Performance Summary")

    # Performance Trends Chart
    create_performance_trends_chart(report)

    # Detailed Metrics Table
    st.subheader("📋 Detailed Performance Metrics")

    metrics_data = []
    for metric_name, metric_data in report.metrics.items():
        if metric_data:
            metrics_data.append(
                {
                    "Metric": metric_name.replace("_", " ").title(),
                    "Value": metric_data.get("value", 0),
                    "Count": metric_data.get("count", 0),
                    "Verification Rate": f"{metric_data.get('verification_rate', 0):.1%}",
                    "Market Comparison": f"{report.market_comparison.get(metric_name, 0):+.1%}",
                }
            )

    if metrics_data:
        df = pd.DataFrame(metrics_data)
        st.dataframe(df, use_container_width=True)

    # Value Delivered Breakdown
    st.subheader("💰 Value Delivered Breakdown")

    value_data = report.value_delivered
    fig = px.pie(values=list(value_data.values()), names=list(value_data.keys()), title="Client Value Distribution")
    fig.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True)


def render_client_roi_view(agent_id: str):
    """Render client ROI analysis view"""

    st.subheader("💎 Client ROI Analysis")

    # Client Selection
    client_id = st.selectbox(
        "Select Client for ROI Analysis",
        ["client_123", "client_456", "client_789"],
        help="Choose client for detailed ROI calculation",
    )

    # Load ROI data
    roi_report = load_roi_data(client_id, agent_id)

    if not roi_report:
        st.warning("ROI data not available for selected client")
        return

    # ROI Summary Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total ROI",
            f"{roi_report.roi_percentage:.1f}%",
            delta=f"+{roi_report.roi_percentage - 100:.1f}% vs break-even",
            delta_color="normal",
        )

    with col2:
        st.metric(
            "Value Delivered",
            f"${roi_report.total_value_delivered:,.0f}",
            delta=f"+${roi_report.total_value_delivered - roi_report.fees_paid:,.0f}",
            delta_color="normal",
        )

    with col3:
        st.metric(
            "Negotiation Savings",
            f"${roi_report.negotiation_savings:,.0f}",
            help="Savings from superior negotiation performance",
        )

    with col4:
        st.metric(
            "Time Value", f"${roi_report.time_savings_value:,.0f}", help="Value of time savings from efficient process"
        )

    # ROI Breakdown Chart
    st.subheader("📊 ROI Value Breakdown")

    fig = go.Figure(
        data=[
            go.Bar(
                name="Value Delivered",
                x=["Negotiation Savings", "Time Savings", "Risk Prevention", "Fees Paid"],
                y=[
                    roi_report.negotiation_savings,
                    roi_report.time_savings_value,
                    roi_report.risk_prevention_value,
                    -roi_report.fees_paid,
                ],
                marker_color=["green", "blue", "orange", "red"],
            )
        ]
    )

    fig.update_layout(title="Value vs. Cost Analysis", yaxis_title="Value ($)", showlegend=False)

    st.plotly_chart(fig, use_container_width=True)

    # Competitive Advantage
    st.subheader("🏆 Competitive Advantages")

    for advantage, description in roi_report.competitive_advantage.items():
        st.markdown(f"**{advantage.replace('_', ' ').title()}:** {description}")


def render_pricing_justification_view(agent_id: str):
    """Render premium pricing justification"""

    st.subheader("💰 Premium Pricing Justification")

    # Pricing Configuration
    col1, col2 = st.columns(2)

    with col1:
        proposed_rate = st.slider(
            "Proposed Commission Rate",
            min_value=0.025,
            max_value=0.06,
            value=0.035,
            step=0.0025,
            format="%.1%%",
            help="Your proposed commission rate",
        )

    with col2:
        market_rate = st.slider(
            "Market Average Rate",
            min_value=0.02,
            max_value=0.05,
            value=0.03,
            step=0.0025,
            format="%.1%%",
            help="Market average commission rate",
        )

    # Load justification data
    justification = load_pricing_justification(agent_id, proposed_rate)

    if not justification:
        st.warning("Pricing justification data not available")
        return

    # Premium Percentage
    premium_pct = justification["premium_percentage"]
    justified_pct = justification["justified_premium"]

    col1, col2 = st.columns(2)

    with col1:
        color = "green" if justified_pct >= premium_pct else "orange"
        st.markdown(
            f"""
        <div style="background: {color}; color: white; padding: 1.5rem; 
                    border-radius: 15px; text-align: center;">
            <h4 style="margin: 0;">Premium Requested</h4>
            <div style="font-size: 3rem; font-weight: bold;">{premium_pct:.1f}%</div>
            <p style="margin: 0;">Above Market Rate</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div style="background: #28a745; color: white; padding: 1.5rem; 
                    border-radius: 15px; text-align: center;">
            <h4 style="margin: 0;">Performance Justified</h4>
            <div style="font-size: 3rem; font-weight: bold;">{justified_pct:.1f}%</div>
            <p style="margin: 0;">Premium Supported</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Value Factors
    st.subheader("📈 Value Justification Factors")

    for factor_name, factor_data in justification["value_factors"].items():
        with st.expander(f"📊 {factor_name.replace('_', ' ').title()}", expanded=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Your Performance", f"{factor_data['agent_performance']:.3f}", help=factor_data["description"]
                )

            with col2:
                st.metric("Market Average", f"{factor_data['market_average']:.3f}")

            with col3:
                advantage = (
                    factor_data.get("value_add")
                    or factor_data.get("days_saved")
                    or factor_data.get("quality_advantage", 0)
                )
                st.metric("Your Advantage", f"+{advantage:.3f}", delta_color="normal")

    # ROI Analysis for Client
    st.subheader("💎 Client ROI on Premium")

    roi_data = justification["roi_analysis"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Additional Fee", f"${roi_data['additional_fee']:,.0f}", help="Extra cost for premium service")

    with col2:
        st.metric("Negotiation Value", f"${roi_data['negotiation_value']:,.0f}", help="Value from superior negotiation")

    with col3:
        st.metric("Time Value", f"${roi_data['time_value']:,.0f}", help="Value of time savings")

    with col4:
        st.metric(
            "Net Benefit",
            f"${roi_data['net_benefit']:,.0f}",
            delta=f"ROI: {roi_data['roi_percentage']:.0f}%",
            delta_color="normal",
        )

    # Recommendation
    st.subheader("🎯 Pricing Recommendation")

    recommendation = justification["recommendation"]

    if recommendation["justified"]:
        st.success(f"""
        ✅ **Premium Pricing Justified**
        
        Recommended Rate: **{recommendation["suggested_rate"]:.1%}**
        
        **Reasoning:** {recommendation["reasoning"]}
        """)
    else:
        st.warning(f"""
        ⚠️ **Premium Not Fully Justified**
        
        Recommended Rate: **{recommendation["suggested_rate"]:.1%}**
        
        **Reasoning:** {recommendation["reasoning"]}
        """)


def create_performance_trends_chart(report):
    """Create performance trends visualization"""

    # Sample trend data (in real implementation, this would come from historical data)
    dates = pd.date_range(start=report.report_period[0], end=report.report_period[1], freq="W")

    # Generate sample trend data
    negotiation_trend = [0.94 + i * 0.005 + (i % 3) * 0.01 for i in range(len(dates))]
    satisfaction_trend = [4.2 + i * 0.1 + (i % 2) * 0.2 for i in range(len(dates))]
    timeline_trend = [25 - i * 0.5 - (i % 4) * 1 for i in range(len(dates))]

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Negotiation Performance Trend",
            "Client Satisfaction Trend",
            "Timeline Efficiency Trend",
            "Overall Score Trend",
        ),
        specs=[[{"secondary_y": False}, {"secondary_y": False}], [{"secondary_y": False}, {"secondary_y": False}]],
    )

    # Add traces
    fig.add_trace(go.Scatter(x=dates, y=negotiation_trend, name="Negotiation %", line=dict(color="red")), row=1, col=1)

    fig.add_trace(go.Scatter(x=dates, y=satisfaction_trend, name="Satisfaction", line=dict(color="blue")), row=1, col=2)

    fig.add_trace(go.Scatter(x=dates, y=timeline_trend, name="Days to Close", line=dict(color="green")), row=2, col=1)

    # Calculate overall score trend
    overall_trend = [
        (n * 20 + s * 20 + (30 - t) * 3.33) for n, s, t in zip(negotiation_trend, satisfaction_trend, timeline_trend)
    ]
    fig.add_trace(go.Scatter(x=dates, y=overall_trend, name="Overall Score", line=dict(color="purple")), row=2, col=2)

    fig.update_layout(height=600, title_text="Performance Trends Over Time", showlegend=True)

    st.plotly_chart(fig, use_container_width=True)


# Main component function
def client_success_accountability_dashboard():
    """Main entry point for the Client Success & Accountability Dashboard"""
    render_client_success_accountability_dashboard()


if __name__ == "__main__":
    client_success_accountability_dashboard()
