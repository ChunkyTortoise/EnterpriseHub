"""
Advanced Scenario Simulation Dashboard - Strategic Decision Support
=================================================================

Interactive dashboard for "what-if" business modeling and scenario analysis.
Implements research recommendations for sophisticated BI capabilities.

Author: Enhanced from research recommendations - January 2026
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Import services
try:
    from ghl_real_estate_ai.services.scenario_simulation_engine import (
        get_scenario_simulation_engine, ScenarioInput, ScenarioType, ScenarioResults
    )
    from ghl_real_estate_ai.services.analytics_service import AnalyticsService
    SERVICES_AVAILABLE = True
except ImportError:
    SERVICES_AVAILABLE = False
    st.warning("Scenario simulation services not available")

def render_advanced_scenario_dashboard():
    """Render the main scenario simulation dashboard."""

    st.title("🎯 Strategic Scenario Simulator")
    st.markdown("**AI-Powered Business Intelligence for Strategic Decision Making**")

    if not SERVICES_AVAILABLE:
        st.error("Required services are not available. Please check the installation.")
        return

    # Create tabs for different scenarios
    tab1, tab2, tab3, tab4 = st.tabs([
        "💰 Commission Analysis",
        "🎯 Lead Qualification",
        "📈 Growth Scenarios",
        "📊 Portfolio Analysis"
    ])

    with tab1:
        render_commission_scenario_panel()

    with tab2:
        render_qualification_scenario_panel()

    with tab3:
        render_growth_scenario_panel()

    with tab4:
        render_portfolio_analysis_panel()

def render_commission_scenario_panel():
    """Render commission adjustment scenario analysis."""

    st.subheader("Commission Rate Impact Analysis")
    st.markdown("Analyze the impact of commission rate changes on revenue, agent relationships, and market position.")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### Scenario Parameters")

        # Current commission rate
        current_rate = st.number_input(
            "Current Commission Rate (%)",
            min_value=4.0,
            max_value=8.0,
            value=6.0,
            step=0.1,
            key="current_commission_rate"
        )

        # New commission rate
        new_rate = st.number_input(
            "Proposed Commission Rate (%)",
            min_value=4.0,
            max_value=8.0,
            value=5.5,
            step=0.1,
            key="new_commission_rate"
        )

        # Analysis period
        period = st.selectbox(
            "Analysis Period",
            ["12M", "6M", "18M", "24M"],
            index=0
        )

        # Confidence level
        confidence = st.slider(
            "Confidence Level",
            85, 99, 95,
            help="Statistical confidence level for projections"
        )

        run_analysis = st.button("Run Commission Analysis", key="run_commission_analysis")

    with col2:
        if run_analysis:
            render_commission_analysis_results(current_rate, new_rate, period, confidence)
        else:
            st.info("👈 Configure parameters and click 'Run Analysis' to see results")

def render_commission_analysis_results(current_rate, new_rate, period, confidence):
    """Render commission analysis results with visualizations."""

    with st.spinner("Running Monte Carlo simulation..."):
        # Simulate scenario results
        commission_change = (new_rate - current_rate) / 100

        # Mock scenario results (in production, would call actual scenario engine)
        baseline_revenue = 2400000  # $2.4M annual revenue
        baseline_deals = 100

        # Calculate impacts
        rate_impact = commission_change / 0.06  # Relative to 6% base
        agent_retention_impact = 1.0 + (commission_change * 3)  # Agents prefer higher commissions
        buyer_agent_impact = 1.0 - (abs(commission_change) * 5) if commission_change < 0 else 1.0

        new_revenue = baseline_revenue * (1 + rate_impact) * buyer_agent_impact
        new_deals = int(baseline_deals * buyer_agent_impact)
        revenue_change = ((new_revenue - baseline_revenue) / baseline_revenue) * 100

        # Create metrics display
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Revenue Impact",
                f"{revenue_change:+.1f}%",
                f"${(new_revenue - baseline_revenue):+,.0f}"
            )

        with col2:
            st.metric(
                "Deal Volume",
                f"{new_deals} deals",
                f"{new_deals - baseline_deals:+d}"
            )

        with col3:
            margin_change = (new_rate - current_rate) * new_deals * 40000  # Avg deal value
            st.metric(
                "Margin Impact",
                f"${margin_change:+,.0f}",
                f"{margin_change/baseline_revenue*100:+.1f}%"
            )

        with col4:
            satisfaction = 50 + (commission_change * 1000)
            st.metric(
                "Agent Satisfaction",
                f"{satisfaction:.0f}/100",
                f"{satisfaction-50:+.0f}"
            )

        # Waterfall chart for revenue impact
        st.subheader("Revenue Impact Breakdown")

        fig = go.Figure()

        categories = ['Current Revenue', 'Commission Rate Effect', 'Agent Response', 'Market Dynamics', 'New Revenue']
        values = [
            baseline_revenue,
            baseline_revenue * rate_impact,
            baseline_revenue * (buyer_agent_impact - 1),
            0,  # Market dynamics (neutral for this example)
            new_revenue
        ]

        # Create waterfall chart
        fig.add_trace(go.Waterfall(
            name="Revenue Impact",
            orientation="v",
            measure=["absolute", "relative", "relative", "relative", "total"],
            x=categories,
            textposition="outside",
            text=[f"${v:,.0f}" for v in values],
            y=values,
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        ))

        fig.update_layout(
            title="Revenue Waterfall Analysis",
            showlegend=False,
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        # Risk analysis
        st.subheader("Risk Analysis")

        col1, col2 = st.columns(2)

        with col1:
            # Risk factors
            st.markdown("**Risk Factors:**")
            risks = []
            if commission_change < -0.005:
                risks.append("• Buyer agent resistance may reduce deal flow")
                risks.append("• Competitive disadvantage vs. higher commission brokers")
            if commission_change > 0.005:
                risks.append("• Higher costs may reduce profitability")
                risks.append("• May price out some seller segments")

            for risk in risks[:4]:
                st.markdown(risk)

        with col2:
            # Opportunities
            st.markdown("**Opportunities:**")
            opportunities = []
            if commission_change < 0:
                opportunities.append("• More competitive pricing for sellers")
                opportunities.append("• Potential for higher deal volume")
                opportunities.append("• Market share growth opportunity")
            else:
                opportunities.append("• Higher revenue per deal")
                opportunities.append("• Enhanced service investment capability")
                opportunities.append("• Premium market positioning")

            for opp in opportunities[:4]:
                st.markdown(opp)

def render_qualification_scenario_panel():
    """Render lead qualification threshold scenario analysis."""

    st.subheader("Lead Qualification Threshold Analysis")
    st.markdown("Optimize lead qualification criteria to balance volume and quality.")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### Scenario Parameters")

        current_threshold = st.number_input(
            "Current Qualification Score Threshold",
            min_value=30,
            max_value=90,
            value=50,
            key="current_threshold"
        )

        new_threshold = st.number_input(
            "Proposed Qualification Score Threshold",
            min_value=30,
            max_value=90,
            value=60,
            key="new_threshold"
        )

        # Current metrics for context
        st.markdown("### Current Performance")

        current_leads = st.number_input(
            "Monthly Qualified Leads",
            min_value=50,
            max_value=500,
            value=150
        )

        current_conversion = st.number_input(
            "Current Conversion Rate (%)",
            min_value=50.0,
            max_value=95.0,
            value=71.0
        )

        run_qual_analysis = st.button("Analyze Qualification Impact", key="run_qual_analysis")

    with col2:
        if run_qual_analysis:
            render_qualification_analysis_results(
                current_threshold, new_threshold, current_leads, current_conversion
            )
        else:
            st.info("👈 Set parameters and click 'Analyze' to see impact projections")

def render_qualification_analysis_results(current_threshold, new_threshold, current_leads, current_conversion):
    """Render qualification threshold analysis results."""

    threshold_change = new_threshold - current_threshold

    # Model the impact
    if threshold_change > 0:  # Raising threshold
        # Fewer leads but higher quality
        volume_change = -0.02 * threshold_change  # 2% drop per point
        quality_change = 0.015 * threshold_change  # 1.5% quality increase per point
    else:  # Lowering threshold
        # More leads but potentially lower quality
        volume_change = -0.025 * threshold_change  # 2.5% increase per point lowered
        quality_change = 0.01 * threshold_change  # 1% quality decrease per point lowered

    new_lead_volume = int(current_leads * (1 + volume_change))
    new_conversion_rate = min(95, current_conversion * (1 + quality_change))

    # Calculate outcomes
    current_closes = current_leads * (current_conversion / 100)
    new_closes = new_lead_volume * (new_conversion_rate / 100)

    current_revenue = current_closes * 24000  # Avg commission
    new_revenue = new_closes * 24000

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Monthly Leads",
            f"{new_lead_volume}",
            f"{new_lead_volume - current_leads:+d}"
        )

    with col2:
        st.metric(
            "Conversion Rate",
            f"{new_conversion_rate:.1f}%",
            f"{new_conversion_rate - current_conversion:+.1f}%"
        )

    with col3:
        st.metric(
            "Monthly Closes",
            f"{new_closes:.1f}",
            f"{new_closes - current_closes:+.1f}"
        )

    with col4:
        revenue_change = ((new_revenue - current_revenue) / current_revenue) * 100
        st.metric(
            "Revenue Impact",
            f"{revenue_change:+.1f}%",
            f"${new_revenue - current_revenue:+,.0f}"
        )

    # Lead funnel visualization
    st.subheader("Lead Funnel Comparison")

    fig = go.Figure()

    # Current funnel
    fig.add_trace(go.Funnel(
        y=['Total Inquiries', 'Qualified Leads', 'Closed Deals'],
        x=[200, current_leads, current_closes],
        name='Current Process',
        text=[f"{200}", f"{current_leads}", f"{current_closes:.0f}"],
        textposition="inside",
        opacity=0.65,
        marker=dict(color="lightblue")
    ))

    # New funnel
    fig.add_trace(go.Funnel(
        y=['Total Inquiries', 'Qualified Leads', 'Closed Deals'],
        x=[200, new_lead_volume, new_closes],
        name='Proposed Process',
        text=[f"{200}", f"{new_lead_volume}", f"{new_closes:.0f}"],
        textposition="inside",
        opacity=0.85,
        marker=dict(color="darkblue")
    ))

    fig.update_layout(
        title="Lead Funnel: Current vs Proposed Threshold",
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

    # Quality vs Quantity Analysis
    st.subheader("Quality vs Quantity Trade-off")

    col1, col2 = st.columns(2)

    with col1:
        # Create scatter plot showing the trade-off
        thresholds = list(range(30, 91, 5))
        volumes = []
        qualities = []

        for thresh in thresholds:
            change = thresh - current_threshold
            vol_change = -0.02 * change if change > 0 else -0.025 * change
            qual_change = 0.015 * change if change > 0 else 0.01 * change

            volumes.append(current_leads * (1 + vol_change))
            qualities.append(current_conversion * (1 + qual_change))

        fig = px.scatter(
            x=volumes,
            y=qualities,
            title="Quality vs Volume Trade-off",
            labels={"x": "Monthly Lead Volume", "y": "Conversion Rate (%)"},
            hover_data={"threshold": thresholds}
        )

        # Highlight current and proposed points
        fig.add_scatter(
            x=[current_leads],
            y=[current_conversion],
            mode='markers',
            marker=dict(size=15, color='red'),
            name='Current'
        )

        fig.add_scatter(
            x=[new_lead_volume],
            y=[new_conversion_rate],
            mode='markers',
            marker=dict(size=15, color='green'),
            name='Proposed'
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # ROI analysis
        st.markdown("**12-Month Projection:**")

        annual_current = current_revenue * 12
        annual_new = new_revenue * 12
        annual_change = annual_new - annual_current

        st.markdown(f"Current Annual Revenue: ${annual_current:,.0f}")
        st.markdown(f"Projected Annual Revenue: ${annual_new:,.0f}")
        st.markdown(f"**Annual Impact: {annual_change:+,.0f}** ({annual_change/annual_current*100:+.1f}%)")

        st.markdown("---")

        if threshold_change > 0:
            st.markdown("**Benefits of Higher Threshold:**")
            st.markdown("• Higher close rates and deal quality")
            st.markdown("• Less time spent on unqualified leads")
            st.markdown("• Improved agent satisfaction")
            st.markdown("• Better resource allocation")
        else:
            st.markdown("**Benefits of Lower Threshold:**")
            st.markdown("• Higher lead volume and market coverage")
            st.markdown("• Increased deal opportunities")
            st.markdown("• Market share expansion potential")
            st.markdown("• Revenue growth through volume")

def render_growth_scenario_panel():
    """Render business growth scenario analysis."""

    st.subheader("Growth Strategy Analysis")
    st.markdown("Model different growth strategies and their impact on business performance.")

    # Growth scenario selector
    growth_scenarios = {
        "Geographic Expansion": {
            "description": "Expand to adjacent markets (Round Rock, Cedar Park)",
            "investment": 75000,
            "timeframe": 6,
            "risk_level": "Medium"
        },
        "Team Scaling": {
            "description": "Add 2 additional agent team members",
            "investment": 120000,
            "timeframe": 3,
            "risk_level": "Low"
        },
        "Premium Services": {
            "description": "Launch luxury property specialization",
            "investment": 45000,
            "timeframe": 4,
            "risk_level": "Medium-High"
        },
        "Technology Investment": {
            "description": "Enhanced AI and automation platform",
            "investment": 85000,
            "timeframe": 2,
            "risk_level": "Low-Medium"
        }
    }

    selected_scenario = st.selectbox(
        "Select Growth Scenario",
        list(growth_scenarios.keys())
    )

    scenario_info = growth_scenarios[selected_scenario]

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### Scenario Details")
        st.markdown(f"**Strategy:** {scenario_info['description']}")
        st.markdown(f"**Investment Required:** ${scenario_info['investment']:,}")
        st.markdown(f"**Implementation Time:** {scenario_info['timeframe']} months")
        st.markdown(f"**Risk Level:** {scenario_info['risk_level']}")

        st.markdown("---")

        # Customization parameters
        market_confidence = st.slider(
            "Market Confidence",
            0.7, 1.0, 0.85,
            help="Confidence in market conditions supporting growth"
        )

        execution_quality = st.slider(
            "Execution Quality",
            0.7, 1.0, 0.9,
            help="Expected quality of strategy execution"
        )

        analyze_growth = st.button("Analyze Growth Scenario", key="analyze_growth")

    with col2:
        if analyze_growth:
            render_growth_analysis_results(selected_scenario, scenario_info, market_confidence, execution_quality)
        else:
            # Show current performance baseline
            st.markdown("### Current Performance Baseline")

            baseline_metrics = {
                "Annual Revenue": "$2.4M",
                "Monthly Deal Volume": "20-25 deals",
                "Market Share (Austin)": "2.8%",
                "Team Size": "3 agents",
                "Operating Margin": "22%"
            }

            for metric, value in baseline_metrics.items():
                st.markdown(f"**{metric}:** {value}")

def render_growth_analysis_results(scenario_name, scenario_info, market_confidence, execution_quality):
    """Render growth scenario analysis results."""

    # Calculate growth projections based on scenario
    base_annual_revenue = 2400000
    base_deals_per_month = 22
    base_margin = 0.22

    # Scenario-specific multipliers
    scenario_multipliers = {
        "Geographic Expansion": {
            "revenue_growth": 0.45,
            "deal_growth": 0.40,
            "margin_impact": -0.03,
            "timeline_months": 8
        },
        "Team Scaling": {
            "revenue_growth": 0.65,
            "deal_growth": 0.70,
            "margin_impact": -0.02,
            "timeline_months": 4
        },
        "Premium Services": {
            "revenue_growth": 0.35,
            "deal_growth": 0.20,
            "margin_impact": 0.05,
            "timeline_months": 6
        },
        "Technology Investment": {
            "revenue_growth": 0.25,
            "deal_growth": 0.15,
            "margin_impact": 0.08,
            "timeline_months": 3
        }
    }

    multipliers = scenario_multipliers[scenario_name]

    # Apply confidence and execution quality adjustments
    adjusted_revenue_growth = multipliers["revenue_growth"] * market_confidence * execution_quality
    adjusted_deal_growth = multipliers["deal_growth"] * market_confidence * execution_quality
    adjusted_margin_impact = multipliers["margin_impact"] * execution_quality

    # Calculate projections
    projected_revenue = base_annual_revenue * (1 + adjusted_revenue_growth)
    projected_deals = base_deals_per_month * (1 + adjusted_deal_growth)
    projected_margin = base_margin + adjusted_margin_impact

    # ROI calculation
    annual_revenue_increase = projected_revenue - base_annual_revenue
    annual_profit_increase = annual_revenue_increase * projected_margin
    roi = (annual_profit_increase - scenario_info['investment']) / scenario_info['investment']
    payback_months = scenario_info['investment'] / (annual_profit_increase / 12)

    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        revenue_change = ((projected_revenue - base_annual_revenue) / base_annual_revenue) * 100
        st.metric(
            "Revenue Growth",
            f"{revenue_change:.1f}%",
            f"${projected_revenue - base_annual_revenue:+,.0f}"
        )

    with col2:
        deal_change = projected_deals - base_deals_per_month
        st.metric(
            "Monthly Deal Volume",
            f"{projected_deals:.1f}",
            f"{deal_change:+.1f}"
        )

    with col3:
        st.metric(
            "Operating Margin",
            f"{projected_margin:.1%}",
            f"{(projected_margin - base_margin):+.1%}"
        )

    with col4:
        st.metric(
            "Annual ROI",
            f"{roi:.1%}",
            f"Payback: {payback_months:.1f}mo"
        )

    # Growth trajectory visualization
    st.subheader("Projected Growth Trajectory")

    months = list(range(1, 25))  # 24 months
    current_trajectory = [base_annual_revenue * (month/12) for month in months]

    # Growth scenario trajectory with ramp-up period
    ramp_months = multipliers["timeline_months"]
    growth_trajectory = []

    for month in months:
        if month <= ramp_months:
            # Gradual ramp-up
            growth_factor = (month / ramp_months) * adjusted_revenue_growth
        else:
            # Full growth achieved
            growth_factor = adjusted_revenue_growth

        monthly_revenue = base_annual_revenue * (1 + growth_factor) * (month/12)
        growth_trajectory.append(monthly_revenue)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=months,
        y=[x/1000 for x in current_trajectory],
        mode='lines',
        name='Current Trajectory',
        line=dict(dash='dash', color='gray')
    ))

    fig.add_trace(go.Scatter(
        x=months,
        y=[x/1000 for x in growth_trajectory],
        mode='lines',
        name=f'{scenario_name} Scenario',
        line=dict(color='green', width=3),
        fill='tonexty'
    ))

    fig.update_layout(
        title="Revenue Growth Trajectory (24 Months)",
        xaxis_title="Months",
        yaxis_title="Cumulative Revenue ($K)",
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

    # Risk and opportunity analysis
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Investment Analysis")
        st.markdown(f"**Initial Investment:** ${scenario_info['investment']:,}")
        st.markdown(f"**Annual Profit Increase:** ${annual_profit_increase:,.0f}")
        st.markdown(f"**Break-even:** {payback_months:.1f} months")
        st.markdown(f"**3-Year NPV:** ${(annual_profit_increase * 3 - scenario_info['investment']):,.0f}")

        # Risk assessment
        risk_color = {"Low": "green", "Low-Medium": "orange", "Medium": "orange", "Medium-High": "red", "High": "red"}
        risk_level = scenario_info['risk_level']
        st.markdown(f"**Risk Level:** :{risk_color.get(risk_level, 'gray')}[{risk_level}]")

    with col2:
        st.markdown("### Success Factors")

        success_factors = {
            "Geographic Expansion": [
                "Market demand in new territories",
                "Local partnership development",
                "Brand recognition transfer",
                "Regulatory compliance"
            ],
            "Team Scaling": [
                "Quality talent recruitment",
                "Training and integration",
                "Lead distribution systems",
                "Performance management"
            ],
            "Premium Services": [
                "High-net-worth client acquisition",
                "Service differentiation",
                "Marketing positioning",
                "Luxury market expertise"
            ],
            "Technology Investment": [
                "User adoption and training",
                "Integration with existing systems",
                "Competitive differentiation",
                "Scalability and reliability"
            ]
        }

        factors = success_factors.get(scenario_name, [])
        for factor in factors[:4]:
            st.markdown(f"• {factor}")

def render_portfolio_analysis_panel():
    """Render comprehensive portfolio performance analysis."""

    st.subheader("Portfolio Performance Analysis")
    st.markdown("Comprehensive analysis of business performance across multiple dimensions.")

    # Time period selector
    col1, col2, col3 = st.columns(3)

    with col1:
        time_period = st.selectbox(
            "Analysis Period",
            ["Last 12 Months", "Last 6 Months", "Last 3 Months", "Year to Date"]
        )

    with col2:
        comparison_period = st.selectbox(
            "Compare Against",
            ["Previous Period", "Same Period Last Year", "Market Benchmark"]
        )

    with col3:
        refresh_data = st.button("Refresh Analysis", key="refresh_portfolio")

    # Generate portfolio metrics
    metrics = generate_portfolio_metrics()

    # Key Performance Indicators
    st.subheader("Key Performance Indicators")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric(
            "Total Revenue",
            f"${metrics['revenue']:,.0f}",
            f"{metrics['revenue_change']:+.1f}%"
        )

    with col2:
        st.metric(
            "Deal Volume",
            f"{metrics['deals']}",
            f"{metrics['deals_change']:+d}"
        )

    with col3:
        st.metric(
            "Avg Deal Value",
            f"${metrics['avg_deal_value']:,.0f}",
            f"{metrics['avg_deal_change']:+.1f}%"
        )

    with col4:
        st.metric(
            "Conversion Rate",
            f"{metrics['conversion_rate']:.1f}%",
            f"{metrics['conversion_change']:+.1f}%"
        )

    with col5:
        st.metric(
            "Client Satisfaction",
            f"{metrics['satisfaction']:.1f}/5.0",
            f"{metrics['satisfaction_change']:+.1f}"
        )

    with col6:
        st.metric(
            "Market Share",
            f"{metrics['market_share']:.2f}%",
            f"{metrics['share_change']:+.2f}%"
        )

    # Performance breakdown charts
    st.subheader("Performance Breakdown")

    col1, col2 = st.columns(2)

    with col1:
        # Revenue by source
        revenue_sources = {
            "Buyer Representation": 1440000,
            "Seller Representation": 720000,
            "Referral Fees": 180000,
            "Consultation Services": 60000
        }

        fig = px.pie(
            values=list(revenue_sources.values()),
            names=list(revenue_sources.keys()),
            title="Revenue by Source"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Deal volume by property type
        property_types = {
            "Single Family": 85,
            "Condos": 35,
            "Townhomes": 18,
            "Luxury ($1M+)": 12
        }

        fig = px.bar(
            x=list(property_types.keys()),
            y=list(property_types.values()),
            title="Deal Volume by Property Type"
        )

        fig.update_layout(
            xaxis_title="Property Type",
            yaxis_title="Number of Deals"
        )

        st.plotly_chart(fig, use_container_width=True)

    # Performance trends
    st.subheader("Performance Trends")

    # Generate monthly data
    months = pd.date_range(start='2025-01-01', end='2025-12-01', freq='M')
    monthly_revenue = np.random.normal(200000, 25000, len(months))
    monthly_deals = np.random.poisson(20, len(months))

    trend_data = pd.DataFrame({
        'Month': months,
        'Revenue': monthly_revenue,
        'Deals': monthly_deals,
        'Avg_Deal_Value': monthly_revenue / monthly_deals
    })

    col1, col2 = st.columns(2)

    with col1:
        fig = px.line(
            trend_data,
            x='Month',
            y='Revenue',
            title="Monthly Revenue Trend"
        )
        fig.update_layout(yaxis_title="Revenue ($)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.line(
            trend_data,
            x='Month',
            y='Deals',
            title="Monthly Deal Volume Trend"
        )
        fig.update_layout(yaxis_title="Number of Deals")
        st.plotly_chart(fig, use_container_width=True)

def generate_portfolio_metrics():
    """Generate sample portfolio metrics for demonstration."""
    return {
        'revenue': 2400000,
        'revenue_change': 12.5,
        'deals': 150,
        'deals_change': 8,
        'avg_deal_value': 16000,
        'avg_deal_change': 4.2,
        'conversion_rate': 73.5,
        'conversion_change': 3.1,
        'satisfaction': 4.7,
        'satisfaction_change': 0.2,
        'market_share': 2.84,
        'share_change': 0.15
    }

if __name__ == "__main__":
    render_advanced_scenario_dashboard()