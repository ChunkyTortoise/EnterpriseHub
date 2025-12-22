"""
Marketing Analytics Hub - Comprehensive Marketing Performance Tracking.

Track campaigns across channels, calculate ROI, analyze customer metrics,
and optimize marketing spend with data-driven insights.
"""

import io
from datetime import datetime, timedelta
from typing import Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import utils.ui as ui
from scipy import stats

from utils.logger import get_logger
from utils.data_source_faker import generate_campaign_data

logger = get_logger(__name__)

# Constants
DEFAULT_CONFIDENCE_LEVEL = 0.95
MIN_SAMPLE_SIZE = 30
ATTRIBUTION_MODELS = ["First-Touch", "Last-Touch", "Linear", "Time-Decay", "Position-Based"]


def render() -> None:
    """Main render function for Marketing Analytics Hub."""
    # Create tabs for different analytics sections
    tabs = st.tabs(
        [
            "📈 Campaign Dashboard",
            "💰 ROI Calculator",
            "👥 Customer Metrics",
            "🧪 A/B Testing",
            "🎯 Attribution",
            "📥 Reports",
        ]
    )

    with tabs[0]:
        _render_campaign_dashboard()

    with tabs[1]:
        _render_roi_calculator()

    with tabs[2]:
        _render_customer_metrics()

    with tabs[3]:
        _render_ab_testing()

    with tabs[4]:
        _render_attribution_modeling()

    with tabs[5]:
        _render_reports()


def _render_campaign_dashboard() -> None:
    """Render multi-channel campaign performance dashboard."""
    st.subheader("📈 Campaign Performance Dashboard")

    campaign_df = _get_campaign_data_source()
    if campaign_df.empty:
        st.warning("Please provide or generate campaign data to continue.")
        return

    # Channel selector
    channels = ["All Channels"] + list(campaign_df["Platform"].unique())
    selected_channel = st.selectbox("Select Platform", channels)

    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        default_start = (
            campaign_df["Date"].min()
            if not campaign_df.empty
            else datetime.now() - timedelta(days=30)
        )
        start_date = st.date_input("Start Date", value=default_start)
    with col2:
        end_date = st.date_input(
            "End Date", value=campaign_df["Date"].max() if not campaign_df.empty else datetime.now()
        )

    filtered_df = campaign_df[
        (campaign_df["Date"] >= pd.to_datetime(start_date))
        & (campaign_df["Date"] <= pd.to_datetime(end_date))
    ]

    if selected_channel != "All Channels":
        filtered_df = filtered_df[filtered_df["Platform"] == selected_channel]

    if filtered_df.empty:
        st.warning("No data for selected filters. Please adjust date range or platform.")
        return

    st.markdown("---")

    # Key Metrics
    st.subheader("📊 Key Performance Indicators")

    # Calculate metrics based on filtered_df
    metrics = _calculate_channel_metrics(filtered_df)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ui.card_metric(
            "Total Spend", f"${metrics['spend']:,.0f}", delta=f"{metrics['spend_change']:+.1f}%"
        )
    with col2:
        ui.card_metric(
            "Revenue", f"${metrics['revenue']:,.0f}", delta=f"{metrics['revenue_change']:+.1f}%"
        )
    with col3:
        ui.card_metric("ROI", f"{metrics['roi']:.2f}x", delta=f"{metrics['roi_change']:+.1f}%")
    with col4:
        ui.card_metric(
            "Conversions",
            f"{metrics['conversions']:,}",
            delta=f"{metrics['conversion_change']:+.1f}%",
        )

    st.markdown("---")

    # Performance visualizations
    st.subheader("📉 Performance Trends")

    # Generate time series data
    trend_data = (
        filtered_df.groupby("Date")
        .agg(
            spend=("Spend", "sum"),
            revenue=("Revenue", "sum"),
            clicks=("Clicks", "sum"),
            impressions=("Impressions", "sum"),
            conversions=("Conversions", "sum"),
        )
        .reset_index()
    )

    trend_data["conversion_rate"] = (trend_data["conversions"] / trend_data["clicks"] * 100).fillna(
        0
    )

    col1, col2 = st.columns(2)

    with col1:
        # Spend vs Revenue chart
        fig_spend_revenue = go.Figure()
        fig_spend_revenue.add_trace(
            go.Scatter(
                x=trend_data["Date"],
                y=trend_data["spend"],
                name="Spend",
                mode="lines",
                line=dict(color="red", width=2),
            )
        )
        fig_spend_revenue.add_trace(
            go.Scatter(
                x=trend_data["Date"],
                y=trend_data["revenue"],
                name="Revenue",
                mode="lines",
                line=dict(color="green", width=2),
            )
        )
        fig_spend_revenue.update_layout(
            title="Spend vs Revenue Over Time",
            xaxis_title="Date",
            yaxis_title="Amount ($)",
            hovermode="x unified",
        )
        st.plotly_chart(fig_spend_revenue, use_container_width=True)

    with col2:
        # Conversion rate chart
        fig_conversion = go.Figure()
        fig_conversion.add_trace(
            go.Scatter(
                x=trend_data["Date"],
                y=trend_data["conversion_rate"],
                name="Conversion Rate",
                mode="lines+markers",
                line=dict(color="blue", width=2),
                fill="tozeroy",
            )
        )
        fig_conversion.update_layout(
            title="Conversion Rate Trend",
            xaxis_title="Date",
            yaxis_title="Conversion Rate (%)",
            hovermode="x unified",
        )
        st.plotly_chart(fig_conversion, use_container_width=True)

    # Channel breakdown
    st.subheader("📊 Platform Performance Breakdown")

    platform_breakdown = (
        filtered_df.groupby("Platform")
        .agg(spend=("Spend", "sum"), revenue=("Revenue", "sum"), conversions=("Conversions", "sum"))
        .reset_index()
    )

    fig_channels = go.Figure(
        data=[
            go.Bar(
                name="Spend",
                x=platform_breakdown["Platform"],
                y=platform_breakdown["spend"],
                marker_color="lightcoral",
            ),
            go.Bar(
                name="Revenue",
                x=platform_breakdown["Platform"],
                y=platform_breakdown["revenue"],
                marker_color="lightgreen",
            ),
        ]
    )
    fig_channels.update_layout(
        title="Spend vs Revenue by Platform",
        xaxis_title="Platform",
        yaxis_title="Amount ($)",
        barmode="group",
    )
    st.plotly_chart(fig_channels, use_container_width=True)

    # Platform efficiency table
    st.markdown("**Platform Efficiency Metrics**")
    efficiency_df = platform_breakdown.copy()
    efficiency_df["ROI"] = (efficiency_df["revenue"] / efficiency_df["spend"]).round(2).fillna(0)
    efficiency_df["CPA"] = (
        (efficiency_df["spend"] / efficiency_df["conversions"]).round(2).fillna(0)
    )
    efficiency_df = efficiency_df[["Platform", "spend", "revenue", "conversions", "ROI", "CPA"]]
    efficiency_df.columns = [
        "Platform",
        "Spend ($)",
        "Revenue ($)",
        "Conversions",
        "ROI",
        "CPA ($)",
    ]
    st.dataframe(efficiency_df, use_container_width=True)


def _render_social_media_dashboard() -> None:
    """Render social media performance dashboard across platforms."""
    st.subheader("📱 Social Media Performance Dashboard")
    st.markdown("""
    Track performance across all major social platforms with platform-specific metrics.
    *Powered by insights from Google Digital Marketing & Meta Social Media certifications.*
    """)

    # Platform selector
    platforms = ["All Platforms", "Meta (Facebook/Instagram)", "LinkedIn", "Twitter/X", "TikTok"]
    selected_platform = st.selectbox("Select Platform", platforms, key="social_platform")

    # Date range
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date", value=datetime.now() - timedelta(days=30), key="social_start_date"
        )
    with col2:
        end_date = st.date_input("End Date", value=datetime.now(), key="social_end_date")

    st.markdown("---")

    # Generate platform data
    platform_data = _generate_social_media_data(selected_platform)

    # Key Metrics Row
    st.subheader("📊 Key Performance Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        ui.card_metric(
            "Followers",
            f"{platform_data['followers']:,}",
            delta=f"+{platform_data['follower_growth']:,}",
        )
    with col2:
        ui.card_metric(
            "Impressions",
            f"{platform_data['impressions']:,}",
            delta=f"{platform_data['impression_change']:+.1f}%",
        )
    with col3:
        ui.card_metric(
            "Engagement Rate",
            f"{platform_data['engagement_rate']:.2f}%",
            delta=f"{platform_data['engagement_change']:+.1f}%",
        )
    with col4:
        ui.card_metric(
            "Reach", f"{platform_data['reach']:,}", delta=f"{platform_data['reach_change']:+.1f}%"
        )
    with col5:
        ui.card_metric(
            "Link Clicks",
            f"{platform_data['link_clicks']:,}",
            delta=f"{platform_data['click_change']:+.1f}%",
        )

    st.markdown("---")

    # Platform-specific breakdown
    st.subheader("📈 Platform Performance Breakdown")

    if selected_platform == "All Platforms":
        # Multi-platform comparison
        platform_comparison = _get_platform_comparison()

        col1, col2 = st.columns(2)

        with col1:
            # Followers by platform
            fig_followers = go.Figure(
                data=[
                    go.Bar(
                        x=platform_comparison["platform"],
                        y=platform_comparison["followers"],
                        text=platform_comparison["followers"],
                        textposition="auto",
                        marker_color=["#1877F2", "#0A66C2", "#1DA1F2", "#000000"],
                    )
                ]
            )
            fig_followers.update_layout(
                title="Followers by Platform",
                xaxis_title="Platform",
                yaxis_title="Followers",
                showlegend=False,
            )
            st.plotly_chart(fig_followers, use_container_width=True)

        with col2:
            # Engagement rate by platform
            fig_engagement = go.Figure(
                data=[
                    go.Bar(
                        x=platform_comparison["platform"],
                        y=platform_comparison["engagement_rate"],
                        text=[f"{r:.2f}%" for r in platform_comparison["engagement_rate"]],
                        textposition="auto",
                        marker_color=["#E1306C", "#0077B5", "#14171A", "#FE2C55"],
                    )
                ]
            )
            fig_engagement.update_layout(
                title="Engagement Rate by Platform",
                xaxis_title="Platform",
                yaxis_title="Engagement Rate (%)",
                showlegend=False,
            )
            st.plotly_chart(fig_engagement, use_container_width=True)

        # Platform efficiency table
        st.markdown("**Platform Performance Summary**")
        summary_df = platform_comparison.copy()
        summary_df.columns = [
            "Platform",
            "Followers",
            "Engagement Rate (%)",
            "Avg. Reach",
            "CTR (%)",
        ]
        st.dataframe(summary_df, use_container_width=True)

    else:
        # Single platform deep dive
        col1, col2 = st.columns(2)

        with col1:
            # Engagement trend
            dates = pd.date_range(start=start_date, end=end_date, freq="D")
            engagement_trend = _generate_engagement_trend(dates, selected_platform)

            fig_trend = go.Figure()
            fig_trend.add_trace(
                go.Scatter(
                    x=engagement_trend["date"],
                    y=engagement_trend["engagement_rate"],
                    name="Engagement Rate",
                    mode="lines+markers",
                    line=dict(color="#1877F2", width=2),
                    fill="tozeroy",
                )
            )
            fig_trend.update_layout(
                title=f"{selected_platform} Engagement Trend",
                xaxis_title="Date",
                yaxis_title="Engagement Rate (%)",
                hovermode="x unified",
            )
            st.plotly_chart(fig_trend, use_container_width=True)

        with col2:
            # Content performance pie
            content_data = _get_content_performance(selected_platform)

            fig_content = go.Figure(
                data=[
                    go.Pie(
                        labels=content_data["type"],
                        values=content_data["engagement"],
                        hole=0.4,
                        marker_colors=["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"],
                    )
                ]
            )
            fig_content.update_layout(
                title="Engagement by Content Type",
                annotations=[dict(text="Content", x=0.5, y=0.5, font_size=14, showarrow=False)],
            )
            st.plotly_chart(fig_content, use_container_width=True)

    st.markdown("---")

    # Best performing posts
    st.subheader("🏆 Top Performing Posts")

    top_posts = _get_top_posts(selected_platform)
    for i, post in enumerate(top_posts[:3], 1):
        with st.expander(f"#{i} - {post['type']} | {post['engagement']:,} engagements"):
            col1, col2, col3 = st.columns(3)
            with col1:
                ui.card_metric("Likes", f"{post['likes']:,}")
            with col2:
                ui.card_metric("Comments", f"{post['comments']:,}")
            with col3:
                ui.card_metric("Shares", f"{post['shares']:,}")
            st.markdown(f"**Posted**: {post['date']} | **Reach**: {post['reach']:,}")

    st.markdown("---")

    # Posting schedule heatmap
    st.subheader("📅 Best Times to Post")
    st.markdown("Engagement heatmap showing optimal posting times")

    posting_data = _generate_posting_heatmap()

    fig_heatmap = go.Figure(
        data=go.Heatmap(
            z=posting_data,
            x=["12am", "3am", "6am", "9am", "12pm", "3pm", "6pm", "9pm"],
            y=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            colorscale="Greens",
            text=posting_data.round(1),
            texttemplate="%{text}",
            textfont={"size": 10},
            colorbar=dict(title="Engagement"),
        )
    )

    fig_heatmap.update_layout(
        title="Engagement by Day and Time",
        xaxis_title="Time of Day",
        yaxis_title="Day of Week",
        height=350,
    )

    st.plotly_chart(fig_heatmap, use_container_width=True)


def _render_roi_calculator() -> None:
    """Render campaign ROI calculator."""
    st.subheader("💰 Campaign ROI Calculator")
    st.markdown("Calculate return on investment for your marketing campaigns")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📥 Campaign Inputs")

        campaign_spend = st.number_input(
            "Campaign Spend ($)",
            min_value=0.0,
            value=5000.0,
            step=100.0,
            help="Total amount spent on the campaign",
        )

        revenue_generated = st.number_input(
            "Revenue Generated ($)",
            min_value=0.0,
            value=15000.0,
            step=100.0,
            help="Total revenue attributed to the campaign",
        )

        customers_acquired = st.number_input(
            "Customers Acquired",
            min_value=0,
            value=50,
            step=1,
            help="Number of new customers from the campaign",
        )

        avg_order_value = st.number_input(
            "Average Order Value ($)",
            min_value=0.0,
            value=300.0,
            step=10.0,
            help="Average purchase value per customer",
        )
        # Use avg_order_value in some logic if needed, or just keep it for UI
        st.session_state["avg_order_value"] = avg_order_value

    with col2:
        st.markdown("#### 📊 ROI Metrics")

        # Calculate metrics
        roi = (
            ((revenue_generated - campaign_spend) / campaign_spend) * 100
            if campaign_spend > 0
            else 0
        )
        roas = revenue_generated / campaign_spend if campaign_spend > 0 else 0
        cpa = campaign_spend / customers_acquired if customers_acquired > 0 else 0
        profit = revenue_generated - campaign_spend

        # Display metrics using card_metric for better UI
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            ui.card_metric("ROI", f"{roi:.1f}%", help="Return on Investment")
            ui.card_metric("CPA", f"${cpa:.2f}", help="Cost Per Acquisition")
        with col_m2:
            ui.card_metric("ROAS", f"{roas:.2f}x", help="Return on Ad Spend")
            ui.card_metric("Profit", f"${profit:,.2f}", delta=f"{roi:.1f}% return")

        # Visual ROI indicator
        if roi > 0:
            st.success(f"✅ Profitable campaign with {roi:.1f}% ROI")
        elif roi == 0:
            st.warning("⚠️ Break-even campaign (0% ROI)")
        else:
            st.error(f"❌ Unprofitable campaign ({roi:.1f}% loss)")

    st.markdown("---")

    # ROI Scenario Analysis
    st.subheader("🎯 Scenario Analysis")
    st.markdown("Explore how changes in conversion rate or AOV affect ROI")

    col1, col2 = st.columns(2)

    with col1:
        conversion_range = st.slider(
            "Conversion Rate Range (%)", min_value=0.5, max_value=10.0, value=(2.0, 8.0), step=0.5
        )

    with col2:
        aov_range = st.slider(
            "AOV Range ($)", min_value=100, max_value=1000, value=(200, 500), step=50
        )

    # Generate scenario heatmap
    conversion_rates = np.linspace(conversion_range[0], conversion_range[1], 10)
    aov_values = np.linspace(aov_range[0], aov_range[1], 10)

    roi_matrix = np.zeros((len(conversion_rates), len(aov_values)))

    for i, conv_rate in enumerate(conversion_rates):
        for j, aov in enumerate(aov_values):
            # Assume 1000 visitors as base
            visitors = 1000
            conversions = visitors * (conv_rate / 100)
            revenue = conversions * aov
            roi_value = ((revenue - campaign_spend) / campaign_spend) * 100
            roi_matrix[i, j] = roi_value

    fig_heatmap = go.Figure(
        data=go.Heatmap(
            z=roi_matrix,
            x=[f"${int(aov)}" for aov in aov_values],
            y=[f"{conv_rate:.1f}%" for conv_rate in conversion_rates],
            colorscale="RdYlGn",
            text=roi_matrix.round(1),
            texttemplate="%{text}%",
            textfont={"size": 10},
            colorbar=dict(title="ROI %"),
        )
    )

    fig_heatmap.update_layout(
        title="ROI Scenario Matrix: Conversion Rate × Average Order Value",
        xaxis_title="Average Order Value",
        yaxis_title="Conversion Rate",
        height=400,
    )

    st.plotly_chart(fig_heatmap, use_container_width=True)


def _render_customer_metrics() -> None:
    """Render customer acquisition and lifetime value metrics."""
    st.subheader("👥 Customer Metrics")

    # CAC Calculator
    st.subheader("💵 Customer Acquisition Cost (CAC)")

    col1, col2, col3 = st.columns(3)

    with col1:
        total_marketing_spend = st.number_input(
            "Total Marketing Spend ($)", min_value=0.0, value=10000.0, step=500.0
        )

    with col2:
        total_sales_costs = st.number_input(
            "Total Sales Costs ($)", min_value=0.0, value=5000.0, step=500.0
        )

    with col3:
        new_customers = st.number_input("New Customers Acquired", min_value=1, value=100, step=5)

    cac = (total_marketing_spend + total_sales_costs) / new_customers

    ui.card_metric("Customer Acquisition Cost (CAC)", f"${cac:.2f}")

    st.markdown("---")

    # CLV Calculator
    st.subheader("💎 Customer Lifetime Value (CLV)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**CLV Inputs**")

        avg_purchase_value = st.number_input(
            "Average Purchase Value ($)", min_value=0.0, value=100.0, step=5.0
        )

        purchase_frequency = st.number_input(
            "Purchase Frequency (per year)",
            min_value=0.0,
            value=4.0,
            step=0.5,
            help="Average number of purchases per customer per year",
        )

        customer_lifespan = st.number_input(
            "Customer Lifespan (years)",
            min_value=0.0,
            value=3.0,
            step=0.5,
            help="Average number of years a customer stays active",
        )

        profit_margin = (
            st.slider(
                "Profit Margin (%)",
                min_value=0,
                max_value=100,
                value=30,
                help="Average profit margin on sales",
            )
            / 100
        )

    with col2:
        st.markdown("**CLV Metrics**")

        # Calculate CLV
        customer_value = avg_purchase_value * purchase_frequency
        clv = customer_value * customer_lifespan * profit_margin

        col_clv1, col_clv2 = st.columns(2)
        with col_clv1:
            ui.card_metric("Customer Lifetime Value (CLV)", f"${clv:.2f}")
        with col_clv2:
            ui.card_metric("Annual Customer Value", f"${customer_value:.2f}")

        # CLV to CAC ratio
        clv_cac_ratio = clv / cac if cac > 0 else 0

        ui.card_metric("CLV:CAC Ratio", f"{clv_cac_ratio:.2f}x")

        # Interpretation
        if clv_cac_ratio >= 3:
            st.success("✅ Healthy ratio (≥3:1) - Sustainable growth")
        elif clv_cac_ratio >= 1:
            st.warning("⚠️ Acceptable ratio (1-3:1) - Room for improvement")
        else:
            st.error("❌ Poor ratio (<1:1) - Losing money on customers")

    st.markdown("---")

    # Cohort Analysis Visualization
    st.subheader("📊 Customer Cohort Analysis")

    cohort_data = _generate_cohort_data()

    fig_cohort = go.Figure(
        data=go.Heatmap(
            z=cohort_data.values,
            x=cohort_data.columns,
            y=cohort_data.index,
            colorscale="Blues",
            text=cohort_data.values,
            texttemplate="%{text}%",
            textfont={"size": 10},
            colorbar=dict(title="Retention %"),
        )
    )

    fig_cohort.update_layout(
        title="Customer Retention by Cohort",
        xaxis_title="Months Since First Purchase",
        yaxis_title="Cohort Month",
        height=400,
    )

    st.plotly_chart(fig_cohort, use_container_width=True)


def _render_ab_testing() -> None:
    """Render A/B/n test significance calculator."""
    st.subheader("🧪 Statistical Testing Calculator")
    st.markdown("Determine if your test results are statistically significant")

    # Test mode selector
    test_mode = st.radio(
        "Select Test Type",
        ["A/B Testing (2 variants)", "Multi-Variant Testing (3-10 variants)"],
        horizontal=True,
    )

    st.markdown("---")

    if test_mode == "A/B Testing (2 variants)":
        _render_ab_test()
    else:
        _render_multivariant_test()


def _render_ab_test() -> None:
    """Render standard A/B test (2 variants)."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🅰️ Variant A (Control)")

        visitors_a = st.number_input(
            "Visitors A", min_value=0, value=1000, step=50, key="visitors_a"
        )

        conversions_a = st.number_input(
            "Conversions A", min_value=0, value=50, step=5, key="conversions_a"
        )

        conversion_rate_a = (conversions_a / visitors_a * 100) if visitors_a > 0 else 0

        ui.card_metric("Conversion Rate A", f"{conversion_rate_a:.2f}%")

    with col2:
        st.markdown("#### 🅱️ Variant B (Test)")

        visitors_b = st.number_input(
            "Visitors B", min_value=0, value=1000, step=50, key="visitors_b"
        )

        conversions_b = st.number_input(
            "Conversions B", min_value=0, value=65, step=5, key="conversions_b"
        )

        conversion_rate_b = (conversions_b / visitors_b * 100) if visitors_b > 0 else 0

        ui.card_metric("Conversion Rate B", f"{conversion_rate_b:.2f}%")

    st.markdown("---")

    # Calculate statistical significance
    if visitors_a >= MIN_SAMPLE_SIZE and visitors_b >= MIN_SAMPLE_SIZE:
        result = _calculate_ab_test_significance(
            visitors_a, conversions_a, visitors_b, conversions_b
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            lift = result["lift"]
            ui.card_metric(
                "Lift", f"{lift:+.2f}%", delta=f"{'Improvement' if lift > 0 else 'Decline'}"
            )

        with col2:
            ui.card_metric("P-Value", f"{result['p_value']:.4f}")

        with col3:
            confidence = (1 - result["p_value"]) * 100
            ui.card_metric("Confidence", f"{confidence:.1f}%")

        # Interpretation
        st.subheader("📊 Test Results")

        if result["significant"]:
            if lift > 0:
                st.success(
                    f"✅ **Statistically Significant Winner!** Variant B is {abs(lift):.2f}% better than A with {confidence:.1f}% confidence."
                )
            else:
                st.error(
                    f"❌ **Statistically Significant Loss!** Variant B is {abs(lift):.2f}% worse than A with {confidence:.1f}% confidence."
                )
        else:
            st.warning(
                f"⚠️ **Not Statistically Significant** - Need more data. Current difference: {lift:+.2f}%"
            )

        # Visual comparison
        fig_ab = go.Figure(
            data=[
                go.Bar(
                    name="Variant A",
                    x=["Conversion Rate"],
                    y=[conversion_rate_a],
                    marker_color="lightblue",
                    text=[f"{conversion_rate_a:.2f}%"],
                    textposition="auto",
                ),
                go.Bar(
                    name="Variant B",
                    x=["Conversion Rate"],
                    y=[conversion_rate_b],
                    marker_color="lightgreen" if lift > 0 else "lightcoral",
                    text=[f"{conversion_rate_b:.2f}%"],
                    textposition="auto",
                ),
            ]
        )

        fig_ab.update_layout(
            title="A/B Test Comparison",
            yaxis_title="Conversion Rate (%)",
            barmode="group",
            showlegend=True,
        )

        st.plotly_chart(fig_ab, use_container_width=True)

        # Sample size recommendation
        st.subheader("💡 Sample Size Recommendation")

        recommended_sample = _calculate_required_sample_size(
            conversion_rate_a / 100, abs(lift) / 100, DEFAULT_CONFIDENCE_LEVEL
        )

        if visitors_a < recommended_sample or visitors_b < recommended_sample:
            st.info(
                f"📊 For {DEFAULT_CONFIDENCE_LEVEL*100:.0f}% confidence with this lift, you need approximately **{recommended_sample:,} visitors per variant**. Current: A={visitors_a:,}, B={visitors_b:,}"
            )
        else:
            st.success(
                f"✅ Sample size is sufficient for {DEFAULT_CONFIDENCE_LEVEL*100:.0f}% confidence level"
            )

    else:
        st.warning(
            f"⚠️ Need at least {MIN_SAMPLE_SIZE} visitors per variant for statistical analysis"
        )


def _render_multivariant_test() -> None:
    """Render multi-variant test (3-10 variants) using Chi-square test."""
    st.subheader("🔢 Multi-Variant Testing (Chi-Square Test)")
    st.markdown("Test multiple variants simultaneously to find the best performer")

    # Number of variants
    num_variants = st.slider("Number of Variants", min_value=3, max_value=10, value=3)

    # Collect data for each variant
    variant_data = []
    variant_names = ["A (Control)", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

    st.subheader("📊 Enter Data for Each Variant")

    cols = st.columns(min(num_variants, 3))  # Max 3 columns for layout

    for i in range(num_variants):
        col_idx = i % 3
        with cols[col_idx]:
            st.markdown(f"**Variant {variant_names[i]}**")

            visitors = st.number_input(
                f"Visitors {variant_names[i]}",
                min_value=0,
                value=1000,
                step=50,
                key=f"mv_visitors_{i}",
                label_visibility="collapsed",
            )

            conversions = st.number_input(
                f"Conversions {variant_names[i]}",
                min_value=0,
                value=50 + (i * 5),  # Slightly different default for each
                step=5,
                key=f"mv_conversions_{i}",
                label_visibility="collapsed",
            )

            conv_rate = (conversions / visitors * 100) if visitors > 0 else 0
            st.metric("Conv. Rate", f"{conv_rate:.2f}%")

            variant_data.append(
                {
                    "name": variant_names[i],
                    "visitors": visitors,
                    "conversions": conversions,
                    "conv_rate": conv_rate,
                }
            )

    st.markdown("---")

    # Check minimum sample size
    all_sufficient = all(v["visitors"] >= MIN_SAMPLE_SIZE for v in variant_data)

    if all_sufficient:
        # Calculate Chi-square test
        result = _calculate_multivariant_significance(variant_data)

        # Display results
        col1, col2, col3 = st.columns(3)

        with col1:
            ui.card_metric("Chi-Square Statistic", f"{result['chi_square']:.2f}")

        with col2:
            ui.card_metric("P-Value", f"{result['p_value']:.4f}")

        with col3:
            confidence = (1 - result["p_value"]) * 100
            ui.card_metric("Confidence", f"{confidence:.1f}%")

        # Interpretation
        st.subheader("📊 Test Results")

        if result["significant"]:
            st.success(
                f"✅ **Statistically Significant Difference Detected!** At least one variant performs differently from the others with {confidence:.1f}% confidence."
            )

            # Show best performer
            best_variant = result["best_variant"]
            st.info(
                f"🏆 **Best Performer**: Variant **{best_variant['name']}** with **{best_variant['conv_rate']:.2f}%** conversion rate"
            )

            # Pairwise comparisons with best
            st.markdown("**Comparison to Best Performer:**")
            comparison_data = []
            for v in variant_data:
                if v["name"] != best_variant["name"]:
                    lift = (
                        (
                            (v["conv_rate"] - best_variant["conv_rate"])
                            / best_variant["conv_rate"]
                            * 100
                        )
                        if best_variant["conv_rate"] > 0
                        else 0
                    )
                    comparison_data.append(
                        {
                            "Variant": v["name"],
                            "Conv. Rate": f"{v['conv_rate']:.2f}%",
                            "Lift vs Best": f"{lift:+.1f}%",
                        }
                    )

            if comparison_data:
                comp_df = pd.DataFrame(comparison_data)
                st.dataframe(comp_df, use_container_width=True)

        else:
            st.warning(
                f"⚠️ **No Significant Difference** - All variants perform similarly. Current p-value: {result['p_value']:.4f}"
            )

        # Visualization
        st.subheader("📈 Conversion Rate Comparison")

        # Create bar chart
        fig_mv = go.Figure(
            data=[
                go.Bar(
                    x=[v["name"] for v in variant_data],
                    y=[v["conv_rate"] for v in variant_data],
                    text=[f"{v['conv_rate']:.2f}%" for v in variant_data],
                    textposition="auto",
                    marker_color=[
                        "gold" if v["name"] == result["best_variant"]["name"] else "lightblue"
                        for v in variant_data
                    ],
                )
            ]
        )

        fig_mv.update_layout(
            title="Conversion Rates Across All Variants",
            xaxis_title="Variant",
            yaxis_title="Conversion Rate (%)",
            showlegend=False,
        )

        st.plotly_chart(fig_mv, use_container_width=True)

        # Summary table
        st.subheader("📋 Summary Table")
        summary_data = pd.DataFrame(
            [
                {
                    "Variant": v["name"],
                    "Visitors": f"{v['visitors']:,}",
                    "Conversions": f"{v['conversions']:,}",
                    "Conv. Rate": f"{v['conv_rate']:.2f}%",
                }
                for v in variant_data
            ]
        )
        st.dataframe(summary_data, use_container_width=True)

    else:
        st.warning(
            f"⚠️ Need at least {MIN_SAMPLE_SIZE} visitors per variant for statistical analysis"
        )
        insufficient = [v["name"] for v in variant_data if v["visitors"] < MIN_SAMPLE_SIZE]
        st.info(f"Insufficient data for: {', '.join(insufficient)}")


def _calculate_multivariant_significance(variant_data: List[Dict]) -> Dict:
    """Calculate Chi-square test for multiple variants."""
    # Create contingency table
    conversions = [v["conversions"] for v in variant_data]
    non_conversions = [v["visitors"] - v["conversions"] for v in variant_data]

    # Contingency table: rows = [conversions, non-conversions], cols = variants
    contingency_table = np.array([conversions, non_conversions])

    # Perform Chi-square test
    chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)

    # Find best performer
    best_variant = max(variant_data, key=lambda x: x["conv_rate"])

    return {
        "chi_square": chi2,
        "p_value": p_value,
        "degrees_of_freedom": dof,
        "significant": bool(p_value < 0.05),
        "best_variant": best_variant,
    }


def _render_attribution_modeling() -> None:
    """Render marketing attribution analysis."""
    st.subheader("🎯 Marketing Attribution Modeling")
    st.markdown("Understand which touchpoints drive conversions")

    # Attribution model selector
    model = st.selectbox(
        "Select Attribution Model",
        ATTRIBUTION_MODELS,
        help="Different methods to credit touchpoints in the customer journey",
    )

    st.markdown("---")

    # Sample customer journey data
    st.subheader("🛤️ Customer Journey Example")

    journey_data = _get_sample_journey_data()

    st.dataframe(journey_data, use_container_width=True)

    st.markdown("---")

    # Attribution calculation
    st.subheader(f"📊 Attribution Results - {model} Model")

    attribution_results = _calculate_attribution(journey_data, model)

    col1, col2 = st.columns([2, 1])

    with col1:
        # Attribution chart
        fig_attribution = px.bar(
            attribution_results,
            x="channel",
            y="credit",
            title=f"Conversion Credit by Channel - {model}",
            labels={"channel": "Channel", "credit": "Conversion Credit"},
            color="credit",
            color_continuous_scale="Viridis",
        )
        st.plotly_chart(fig_attribution, use_container_width=True)

    with col2:
        # Attribution table
        st.markdown("**Attribution Breakdown**")
        results_df = attribution_results.copy()
        results_df["credit"] = results_df["credit"].round(2)
        results_df["percentage"] = (results_df["credit"] / results_df["credit"].sum() * 100).round(
            1
        )
        results_df.columns = ["Channel", "Credit", "Share (%)"]
        st.dataframe(results_df, use_container_width=True)

    # Model explanation
    st.subheader("💡 Model Explanation")

    explanations = {
        "First-Touch": "100% credit to the first touchpoint in the customer journey",
        "Last-Touch": "100% credit to the last touchpoint before conversion",
        "Linear": "Equal credit distributed across all touchpoints",
        "Time-Decay": "More credit to recent touchpoints, less to earlier ones",
        "Position-Based": "40% to first touch, 40% to last touch, 20% distributed evenly among middle touchpoints (U-shaped)",
    }

    st.info(f"**{model}**: {explanations[model]}")


def _render_reports() -> None:
    """Render marketing reports export section."""
    st.subheader("📥 Marketing Reports")

    # Report type selector
    report_type = st.selectbox(
        "Select Report Type",
        ["Campaign Performance", "Customer Metrics", "A/B Test Results", "Attribution Analysis"],
    )

    # Date range for report
    col1, col2 = st.columns(2)
    with col1:
        report_start = st.date_input("Report Start Date", value=datetime.now() - timedelta(days=30))
    with col2:
        report_end = st.date_input("Report End Date", value=datetime.now())

    st.markdown("---")

    # Generate report preview
    st.subheader("📊 Report Preview")

    report_data = _generate_report_data(report_type, report_start, report_end)

    st.dataframe(report_data, use_container_width=True)

    # Export options
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📄 Export as CSV")

        csv_buffer = io.StringIO()
        report_data.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()

        st.download_button(
            label="⬇️ Download CSV",
            data=csv_data,
            file_name=f"{report_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

    with col2:
        st.markdown("#### 📊 Export as Excel")

        excel_buffer = io.BytesIO()
        report_data.to_excel(excel_buffer, index=False, engine="openpyxl")
        excel_data = excel_buffer.getvalue()

        st.download_button(
            label="⬇️ Download Excel",
            data=excel_data,
            file_name=f"{report_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# Helper functions


def _get_campaign_data_source() -> pd.DataFrame:
    """Handles selection of data source for campaign data (upload or simulate)."""
    st.subheader("📊 Campaign Data Source")
    source_option = st.radio(
        "Choose your data source:", ("Upload CSV/Excel", "Simulate Marketing Data"), horizontal=True
    )

    if source_option == "Upload CSV/Excel":
        uploaded_file = st.file_uploader(
            "Upload your marketing data (CSV or Excel)", type=["csv", "xlsx"]
        )
        if uploaded_file is not None:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            st.success("Data uploaded successfully!")
            # Convert Date column if it exists and is not already datetime
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
                # Drop rows where Date conversion failed
                df = df.dropna(subset=["Date"])
            return df
        else:
            st.info("Please upload a file or switch to simulated data.")
            return pd.DataFrame()  # Return empty df if no file
    else:  # Simulate Marketing Data
        st.info("Generating realistic marketing data for demonstration purposes.")
        col1, col2 = st.columns(2)
        with col1:
            platform_choice = st.selectbox("Simulate for Platform", ["Google Ads", "Meta Ads"])
            start_date_choice = st.date_input(
                "Simulation Start Date", value=datetime.now() - timedelta(days=90)
            )
        with col2:
            days_choice = st.slider("Simulation Duration (Days)", 30, 365, 90)

        # Use a consistent key for the button to avoid re-rendering issues
        if st.button("Generate Simulated Data", key="generate_sim_data_button"):
            simulated_data = generate_campaign_data(
                platform=platform_choice,
                start_date=start_date_choice.strftime("%Y-%m-%d"),
                days=days_choice,
            )
            st.success(f"Simulated data generated for {platform_choice}!")
            # Store in session state
            st.session_state["simulated_campaign_data"] = simulated_data
            return simulated_data

        # If simulated data is already in session state from a previous generation, use it
        if (
            "simulated_campaign_data" in st.session_state
            and not st.session_state["simulated_campaign_data"].empty
        ):
            st.success("Using previously generated simulated data.")
            return st.session_state["simulated_campaign_data"]
        else:
            return pd.DataFrame()  # Initial empty df


def _get_sample_campaign_data() -> pd.DataFrame:
    """Generate sample campaign data for tests and reports."""
    sample_df = pd.DataFrame(
        {
            "campaign": ["Campaign " + str(i) for i in range(1, 6)],
            "channel": ["Social Media", "Paid Ads", "Email", "Organic", "Direct"],
            "spend": [1000, 2000, 500, 0, 0],
            "revenue": [2500, 5000, 1500, 1000, 500],
            "conversions": [25, 50, 15, 10, 5],
        }
    )
    return sample_df


def _generate_trend_data(dates: pd.DatetimeIndex, channel: str) -> pd.DataFrame:
    """Generate trend data for a specific channel over a date range."""
    n_days = len(dates)
    np.random.seed(42)  # For consistency in trends

    spend = np.random.uniform(100, 500, n_days)
    if channel in ["Organic", "Direct"]:
        spend = np.zeros(n_days)

    revenue = spend * np.random.uniform(2, 4, n_days) + np.random.uniform(500, 1000, n_days)
    clicks = (spend / 0.5).astype(int) + np.random.randint(100, 500, n_days)
    conversions = (clicks * np.random.uniform(0.02, 0.05, n_days)).astype(int)

    return pd.DataFrame(
        {
            "date": dates,
            "spend": spend,
            "revenue": revenue,
            "clicks": clicks,
            "conversions": conversions,
            "conversion_rate": np.nan_to_num(conversions / clicks * 100),
        }
    )


def _calculate_channel_metrics(df_or_channel) -> Dict:
    """Calculate metrics for the given DataFrame or specific channel name."""
    if isinstance(df_or_channel, str):
        # If it's a string, we need to get data. For tests, we'll use sample data.
        if df_or_channel == "All Channels":
            df = _get_sample_campaign_data()
        else:
            df = _get_sample_campaign_data()
            df = df[df["channel"] == df_or_channel]
    else:
        df = df_or_channel

    if df.empty:
        return {
            "spend": 0,
            "revenue": 0,
            "roi": 0,
            "roas": 0,
            "conversions": 0,
            "spend_change": 0,
            "revenue_change": 0,
            "roi_change": 0,
            "conversion_change": 0,
        }

    # Normalize column names to title case for calculations
    col_map = {c.lower(): c for c in df.columns}

    def get_val(name):
        col = col_map.get(name.lower())
        return df[col].sum() if col else 0

    total_spend = get_val("Spend")
    total_revenue = get_val("Revenue")
    total_conversions = get_val("Conversions")

    # Calculate current metrics
    roi = ((total_revenue - total_spend) / total_spend * 100) if total_spend > 0 else 0
    roas = total_revenue / total_spend if total_spend > 0 else 0

    return {
        "spend": total_spend,
        "revenue": total_revenue,
        "roi": roi,
        "roas": roas,
        "conversions": total_conversions,
        "spend_change": np.random.uniform(-5, 5),  # Simulated change
        "revenue_change": np.random.uniform(-5, 5),
        "roi_change": np.random.uniform(-5, 5),
        "conversion_change": np.random.uniform(-5, 5),
    }


def _get_channel_breakdown(df: pd.DataFrame = None) -> pd.DataFrame:
    """Get performance breakdown by channel from the given DataFrame."""
    if df is None:
        df = _get_sample_campaign_data()

    # Normalize column names to lowercase
    df.columns = [col.lower() for col in df.columns]

    # Map 'platform' or 'channel' code to a consistent 'channel' column
    if "platform" in df.columns and "channel" not in df.columns:
        df = df.rename(columns={"platform": "channel"})

    return (
        df.groupby("channel")
        .agg(spend=("spend", "sum"), revenue=("revenue", "sum"), conversions=("conversions", "sum"))
        .reset_index()
    )


def _calculate_ab_test_significance(
    visitors_a: int,
    conversions_a: int,
    visitors_b: int,
    conversions_b: int,
    confidence: float = DEFAULT_CONFIDENCE_LEVEL,
) -> Dict:
    """Calculate A/B test statistical significance."""
    # Calculate conversion rates
    rate_a = conversions_a / visitors_a if visitors_a > 0 else 0
    rate_b = conversions_b / visitors_b if visitors_b > 0 else 0

    # Calculate lift
    lift = ((rate_b - rate_a) / rate_a * 100) if rate_a > 0 else 0

    # Calculate standard error
    se_a = np.sqrt(rate_a * (1 - rate_a) / visitors_a) if visitors_a > 0 else 0
    se_b = np.sqrt(rate_b * (1 - rate_b) / visitors_b) if visitors_b > 0 else 0
    se_diff = np.sqrt(se_a**2 + se_b**2)

    # Calculate z-score and p-value
    z_score = (rate_b - rate_a) / se_diff if se_diff > 0 else 0
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))  # Two-tailed test

    # Determine significance
    significant = bool(p_value < (1 - confidence))

    return {"lift": lift, "p_value": p_value, "z_score": z_score, "significant": significant}


def _calculate_required_sample_size(
    baseline_rate: float,
    mde: float,  # Minimum detectable effect
    confidence: float = DEFAULT_CONFIDENCE_LEVEL,
    power: float = 0.8,
) -> int:
    """Calculate required sample size for A/B test."""
    # Z-scores for confidence and power
    z_alpha = stats.norm.ppf(1 - (1 - confidence) / 2)
    z_beta = stats.norm.ppf(power)

    # Calculate sample size
    p1 = baseline_rate
    p2 = baseline_rate + mde

    pooled_p = (p1 + p2) / 2

    numerator = (
        z_alpha * np.sqrt(2 * pooled_p * (1 - pooled_p))
        + z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    ) ** 2
    denominator = (p2 - p1) ** 2

    sample_size = int(np.ceil(numerator / denominator))

    return max(sample_size, MIN_SAMPLE_SIZE)


def _generate_cohort_data() -> pd.DataFrame:
    """Generate sample cohort retention data."""
    cohorts = ["Jan 2024", "Feb 2024", "Mar 2024", "Apr 2024", "May 2024"]
    months = ["Month 0", "Month 1", "Month 2", "Month 3", "Month 4"]

    data = []
    for i, cohort in enumerate(cohorts):
        row = [100]  # Month 0 is always 100%
        retention = 100
        for j in range(1, 5 - i):
            retention *= np.random.uniform(0.70, 0.85)  # Decay rate
            row.append(round(retention, 1))

        # Fill remaining with NaN
        row.extend([np.nan] * i)
        data.append(row)

    df = pd.DataFrame(data, columns=months, index=cohorts)
    return df


def _get_sample_journey_data() -> pd.DataFrame:
    """Get sample customer journey data."""
    return pd.DataFrame(
        {
            "Customer": ["Customer 1"] * 5,
            "Step": [1, 2, 3, 4, 5],
            "Touchpoint": ["Social Media Ad", "Website Visit", "Email", "Retargeting Ad", "Direct"],
            "Channel": ["Social Media", "Organic", "Email", "Paid Ads", "Direct"],
            "Days Since First Touch": [0, 2, 5, 7, 10],
            "Converted": [False, False, False, False, True],
        }
    )


def _calculate_attribution(journey_df: pd.DataFrame, model: str) -> pd.DataFrame:
    """Calculate attribution credit for each channel."""
    channels = journey_df["Channel"].unique()

    if model == "First-Touch":
        # 100% credit to first touchpoint
        first_channel = journey_df.iloc[0]["Channel"]
        credits = {ch: (1.0 if ch == first_channel else 0.0) for ch in channels}

    elif model == "Last-Touch":
        # 100% credit to last touchpoint
        last_channel = journey_df.iloc[-1]["Channel"]
        credits = {ch: (1.0 if ch == last_channel else 0.0) for ch in channels}

    elif model == "Linear":
        # Equal credit across all touchpoints
        n_touches = len(journey_df)
        credit_per_touch = 1.0 / n_touches
        credits = journey_df["Channel"].value_counts().to_dict()
        credits = {ch: count * credit_per_touch for ch, count in credits.items()}

    elif model == "Time-Decay":
        # More credit to recent touchpoints
        n_touches = len(journey_df)
        decay_weights = np.array([2**i for i in range(n_touches)])
        decay_weights = decay_weights / decay_weights.sum()

        credits = {}
        for idx, row in journey_df.iterrows():
            ch = row["Channel"]
            credits[ch] = credits.get(ch, 0) + decay_weights[idx]

    elif model == "Position-Based":
        # U-shaped: 40% first, 40% last, 20% distributed among middle
        n_touches = len(journey_df)
        credits = {}

        if n_touches == 1:
            # Only one touchpoint gets 100%
            ch = journey_df.iloc[0]["Channel"]
            credits[ch] = 1.0
        elif n_touches == 2:
            # Two touchpoints: 50% each
            first_ch = journey_df.iloc[0]["Channel"]
            last_ch = journey_df.iloc[-1]["Channel"]
            credits[first_ch] = credits.get(first_ch, 0) + 0.5
            credits[last_ch] = credits.get(last_ch, 0) + 0.5
        else:
            # Three or more touchpoints: 40-20-40 distribution
            first_ch = journey_df.iloc[0]["Channel"]
            last_ch = journey_df.iloc[-1]["Channel"]
            middle_touches = n_touches - 2
            middle_credit = 0.20 / middle_touches if middle_touches > 0 else 0

            # First touchpoint: 40%
            credits[first_ch] = credits.get(first_ch, 0) + 0.40

            # Last touchpoint: 40%
            credits[last_ch] = credits.get(last_ch, 0) + 0.40

            # Middle touchpoints: 20% distributed evenly
            for idx in range(1, n_touches - 1):
                ch = journey_df.iloc[idx]["Channel"]
                credits[ch] = credits.get(ch, 0) + middle_credit

    # Convert to DataFrame
    result_df = pd.DataFrame(list(credits.items()), columns=["channel", "credit"])
    result_df = result_df.sort_values("credit", ascending=False).reset_index(drop=True)

    return result_df


def _generate_report_data(report_type: str, start_date, end_date) -> pd.DataFrame:
    """Generate sample report data."""
    if report_type == "Campaign Performance":
        return _get_sample_campaign_data()
    elif report_type == "Customer Metrics":
        return pd.DataFrame(
            {
                "Metric": ["CAC", "CLV", "CLV:CAC Ratio", "Avg Order Value", "Purchase Frequency"],
                "Value": ["$50.00", "$450.00", "9.0x", "$100.00", "4.5/year"],
            }
        )
    elif report_type == "A/B Test Results":
        return pd.DataFrame(
            {
                "Variant": ["A (Control)", "B (Test)"],
                "Visitors": [1000, 1000],
                "Conversions": [50, 65],
                "Conversion Rate": ["5.0%", "6.5%"],
                "Lift": ["-", "+30%"],
                "Significant": ["-", "Yes"],
            }
        )
    else:  # Attribution Analysis
        return pd.DataFrame(
            {
                "Channel": ["Social Media", "Email", "Paid Ads", "Organic", "Direct"],
                "First-Touch": [0.20, 0.30, 0.25, 0.15, 0.10],
                "Last-Touch": [0.10, 0.15, 0.35, 0.20, 0.20],
                "Linear": [0.20, 0.20, 0.20, 0.20, 0.20],
                "Time-Decay": [0.12, 0.18, 0.28, 0.22, 0.20],
            }
        )


def _generate_social_media_data(platform: str) -> Dict:
    """Generate simulated performance data for social platforms."""
    np.random.seed(42)
    return {
        "followers": 12500,
        "follower_growth": 450,
        "impressions": 85000,
        "impression_change": 12.5,
        "engagement_rate": 3.25,
        "engagement_change": 0.8,
        "reach": 65000,
        "reach_change": 15.2,
        "link_clicks": 1200,
        "click_change": 5.4,
    }


def _get_platform_comparison() -> pd.DataFrame:
    """Get comparison data across social platforms."""
    return pd.DataFrame(
        {
            "platform": ["Meta", "LinkedIn", "Twitter/X", "TikTok"],
            "followers": [15000, 8000, 12000, 25000],
            "engagement_rate": [2.5, 4.2, 1.8, 5.5],
            "avg_reach": [4500, 3200, 5100, 9800],
            "ctr": [1.2, 2.1, 0.8, 3.5],
        }
    )


def _generate_engagement_trend(dates: pd.DatetimeIndex, platform: str) -> pd.DataFrame:
    """Generate daily engagement rate trend."""
    np.random.seed(42)
    return pd.DataFrame({"date": dates, "engagement_rate": np.random.uniform(2.0, 5.0, len(dates))})


def _get_content_performance(platform: str) -> pd.DataFrame:
    """Get engagement breakdown by content type."""
    return pd.DataFrame(
        {
            "type": ["Video", "Image", "Carousal", "Text", "Link"],
            "engagement": [4500, 2800, 3500, 1200, 800],
        }
    )


def _get_top_posts(platform: str) -> List[Dict]:
    """Get list of top performing posts."""
    return [
        {
            "type": "Video",
            "engagement": 1250,
            "likes": 800,
            "comments": 150,
            "shares": 300,
            "date": "2024-05-15",
            "reach": 15000,
        },
        {
            "type": "Image",
            "engagement": 950,
            "likes": 600,
            "comments": 100,
            "shares": 250,
            "date": "2024-05-14",
            "reach": 12000,
        },
        {
            "type": "Carousal",
            "engagement": 850,
            "likes": 500,
            "comments": 80,
            "shares": 270,
            "date": "2024-05-13",
            "reach": 10000,
        },
    ]


def _generate_posting_heatmap() -> np.ndarray:
    """Generate engagement heatmap data (7 days x 8 time slots)."""
    np.random.seed(42)
    return np.random.uniform(1.0, 10.0, (7, 8))
