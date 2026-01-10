"""
Market Intelligence & Territory Management Dashboard

Comprehensive Streamlit interface for market analysis, competitive intelligence,
territory management, and performance optimization. Combines market insights
with territory assignments for strategic decision-making.

Features:
- Market overview and trend analysis
- Competitive intelligence and analysis
- Territory assignment and management
- Performance tracking and optimization
- Market opportunity identification
- Territory coverage analysis

Created: January 2026
Author: GHL Real Estate AI Platform
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
import logging

# Import the market intelligence and territory management services
try:
    from services.market_intelligence_service import (
        market_intelligence_service,
        MarketTrend,
        OpportunityType,
        MarketOpportunity,
        MarketForecast
    )
    from services.territory_management_service import (
        territory_management_service,
        TerritoryStatus,
        AssignmentType,
        TerritoryType,
        PerformanceLevel
    )
except ImportError:
    st.error("Market intelligence services not found. Please check the service installation.")

# Configure logging
logger = logging.getLogger(__name__)

def render_market_intelligence_dashboard():
    """Render the market intelligence and territory management dashboard."""
    st.header("📊 Market Intelligence & Territory Management")
    st.markdown("*Comprehensive market analysis and territory optimization platform*")

    # User role selection for demo purposes
    user_role = st.selectbox(
        "Select Your Role",
        ["Agent", "Manager", "Administrator"],
        key="market_intelligence_role"
    )

    # Agent selection
    agent_options = ["agent_001", "agent_002", "agent_003", "new_agent"]
    selected_agent = st.selectbox(
        "Select Agent",
        agent_options,
        key="market_intelligence_agent"
    )

    if user_role == "Agent":
        render_agent_market_interface(selected_agent)
    elif user_role == "Manager":
        render_manager_market_interface()
    else:
        render_admin_market_interface()

def render_agent_market_interface(agent_id: str):
    """Render the agent-focused market intelligence interface."""

    # Create tabs for different agent views
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏠 My Territories", "📈 Market Overview", "🎯 Opportunities",
        "🏆 Performance", "🔍 Competition", "🔮 Forecasts"
    ])

    with tab1:
        render_agent_territories(agent_id)

    with tab2:
        render_market_overview()

    with tab3:
        render_market_opportunities()

    with tab4:
        render_territory_performance(agent_id)

    with tab5:
        render_competitive_analysis()

    with tab6:
        render_market_forecasts()

def render_agent_territories(agent_id: str):
    """Render agent's territory assignments and management."""
    st.subheader("🏠 My Territory Assignments")

    try:
        # Get agent territories
        territories = asyncio.run(territory_management_service.get_agent_territories(agent_id))

        if not territories:
            st.info("🗺️ No territories assigned yet. Contact your manager for territory assignments.")
            return

        # Territory overview metrics
        col1, col2, col3, col4 = st.columns(4)

        total_territories = len(territories)
        primary_territories = len([t for t in territories if t["assignment_type"] == "primary"])
        total_market_potential = sum(t["market_potential"] for t in territories)
        avg_potential = total_market_potential / total_territories if total_territories > 0 else 0

        with col1:
            st.metric("Total Territories", total_territories)
        with col2:
            st.metric("Primary Territories", primary_territories)
        with col3:
            st.metric("Market Potential", f"{total_market_potential:.1f}")
        with col4:
            st.metric("Avg Potential", f"{avg_potential:.1f}")

        # Territory details
        st.subheader("Territory Details")

        for territory in territories:
            with st.expander(f"🏘️ {territory['name']} - {territory['assignment_type'].title()} Assignment"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"**Description:** {territory['description']}")
                    st.write(f"**Specialization:** {territory['specialization'].title()}")
                    st.write(f"**Population:** {territory['population']:,}")
                    st.write(f"**Competition:** {territory['competition_level'].title()}")
                    st.write(f"**Market Potential:** {territory['market_potential']:.1f}/100")

                    # Performance goals
                    if territory["performance_goals"]:
                        st.write("**Performance Goals:**")
                        for goal, value in territory["performance_goals"].items():
                            st.write(f"- {goal.replace('_', ' ').title()}: {value:,.0f}")

                with col2:
                    st.write(f"**Priority:** {get_priority_badge(territory['priority_level'])}")
                    st.write(f"**Assignment Date:** {territory['start_date'][:10]}")

                    # View performance button
                    if st.button(f"View Performance", key=f"perf_{territory['territory_id']}"):
                        st.session_state.selected_territory = territory['territory_id']

                    # View opportunities button
                    if st.button(f"View Opportunities", key=f"opp_{territory['territory_id']}"):
                        st.session_state.territory_opportunities = territory['territory_id']

    except Exception as e:
        st.error(f"Error loading territories: {e}")
        logger.error(f"Error in render_agent_territories: {e}")

def render_market_overview():
    """Render comprehensive market overview."""
    st.subheader("📈 Market Overview")

    try:
        # Get market overview
        overview = asyncio.run(market_intelligence_service.get_market_overview())

        if not overview.get("areas"):
            st.error("No market data available")
            return

        # Summary metrics
        summary = overview["summary_metrics"]
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Areas", summary["total_areas"])
        with col2:
            st.metric("Total Sales", f"{summary['total_sales']:,}")
        with col3:
            st.metric("Avg Inventory", f"{summary['avg_inventory_months']:.1f} months")
        with col4:
            health_score = summary["market_health_score"]
            health_color = "green" if health_score > 70 else "orange" if health_score > 50 else "red"
            st.markdown(f"**Market Health:** <span style='color: {health_color}'>{health_score:.1f}/100</span>",
                       unsafe_allow_html=True)

        # Market areas overview
        st.subheader("Market Areas Performance")

        areas_data = overview["areas"]
        areas_df = pd.DataFrame([
            {
                "Area": area["name"],
                "Avg Price": area["metrics"]["avg_sale_price"],
                "Sales": area["metrics"]["total_sales"],
                "DOM": area["metrics"]["days_on_market"],
                "Price Change": area["metrics"]["price_change_30d"],
                "Trend": area["trend_indicator"],
                "Absorption": area["metrics"]["absorption_rate"]
            }
            for area in areas_data
        ])

        st.dataframe(areas_df, use_container_width=True)

        # Market trends visualization
        col1, col2 = st.columns(2)

        with col1:
            # Price comparison chart
            fig = px.bar(
                areas_df,
                x="Area",
                y="Avg Price",
                color="Price Change",
                color_continuous_scale="RdYlGn",
                title="Average Sale Price by Area",
                labels={"Avg Price": "Average Sale Price ($)"}
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Market activity chart
            fig = px.scatter(
                areas_df,
                x="DOM",
                y="Sales",
                size="Absorption",
                color="Price Change",
                hover_data=["Area"],
                title="Market Activity Analysis",
                labels={"DOM": "Days on Market", "Sales": "Total Sales"}
            )
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading market overview: {e}")

def render_market_opportunities():
    """Render market opportunities identification."""
    st.subheader("🎯 Market Opportunities")

    try:
        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            opportunity_types = ["All"] + [e.value for e in OpportunityType]
            selected_type = st.selectbox("Opportunity Type", opportunity_types)

        with col2:
            min_confidence = st.slider("Minimum Confidence", 0.0, 1.0, 0.5, 0.05)

        with col3:
            min_value = st.number_input("Minimum Value ($)", min_value=0, value=100000, step=50000)

        # Get opportunities
        all_opportunities = asyncio.run(market_intelligence_service.get_market_opportunities())

        # Apply filters
        filtered_opportunities = []
        for opp in all_opportunities:
            if selected_type != "All" and opp.opportunity_type.value != selected_type:
                continue
            if opp.confidence_score < min_confidence:
                continue
            if opp.potential_value < min_value:
                continue
            filtered_opportunities.append(opp)

        if not filtered_opportunities:
            st.info("No opportunities match your filter criteria.")
            return

        # Opportunities overview
        st.write(f"**Found {len(filtered_opportunities)} opportunities matching your criteria**")

        # Opportunities list
        for i, opportunity in enumerate(filtered_opportunities):
            with st.expander(
                f"{get_opportunity_emoji(opportunity.opportunity_type)} {opportunity.title} "
                f"(${opportunity.potential_value:,.0f} - {opportunity.confidence_score:.0%} confidence)"
            ):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"**Description:** {opportunity.description}")
                    st.write(f"**Area:** {opportunity.area_id}")
                    st.write(f"**Type:** {opportunity.opportunity_type.value.replace('_', ' ').title()}")

                    st.write("**Supporting Data:**")
                    for key, value in opportunity.supporting_data.items():
                        if isinstance(value, list):
                            st.write(f"• {key.replace('_', ' ').title()}: {', '.join(map(str, value))}")
                        else:
                            st.write(f"• {key.replace('_', ' ').title()}: {value}")

                    st.write("**Recommended Actions:**")
                    for action in opportunity.recommended_actions:
                        st.write(f"• {action}")

                with col2:
                    # Confidence score
                    confidence_color = "green" if opportunity.confidence_score > 0.8 else "orange" if opportunity.confidence_score > 0.6 else "red"
                    st.markdown(f"**Confidence:** <span style='color: {confidence_color}'>{opportunity.confidence_score:.1%}</span>",
                               unsafe_allow_html=True)

                    # Key metrics
                    st.write(f"**Value:** ${opportunity.potential_value:,.0f}")
                    st.write(f"**Effort:** {opportunity.effort_level.title()}")
                    st.write(f"**Urgency:** {opportunity.time_sensitivity.title()}")
                    st.write(f"**Created:** {opportunity.created_date.strftime('%Y-%m-%d')}")

                    # Action button
                    if st.button(f"Take Action", key=f"action_{opportunity.opportunity_id}"):
                        st.success(f"✅ Opportunity flagged for follow-up: {opportunity.title}")

    except Exception as e:
        st.error(f"Error loading opportunities: {e}")

def render_territory_performance(agent_id: str):
    """Render territory performance dashboard."""
    st.subheader("🏆 Territory Performance Dashboard")

    try:
        # Get agent territories for performance analysis
        territories = asyncio.run(territory_management_service.get_agent_territories(agent_id))

        if not territories:
            st.info("No territories assigned for performance analysis.")
            return

        # Territory selection for detailed analysis
        territory_options = {t["territory_id"]: t["name"] for t in territories}
        selected_territory_id = st.selectbox(
            "Select Territory for Performance Analysis",
            list(territory_options.keys()),
            format_func=lambda x: territory_options[x]
        )

        # Get performance data
        performance = asyncio.run(territory_management_service.get_territory_performance(agent_id, selected_territory_id))

        if "error" in performance:
            st.error(performance["error"])
            return

        # Performance summary
        current = performance["current_metrics"]
        level = performance["performance_level"]

        # Performance level badge
        level_color = {
            "excellent": "green",
            "above_average": "lightgreen",
            "average": "orange",
            "below_average": "red",
            "needs_improvement": "darkred"
        }.get(level, "gray")

        st.markdown(f"""
        <div style="background-color: {level_color}; color: white; padding: 10px; border-radius: 5px; text-align: center; margin: 10px 0;">
            <h3>Performance Level: {level.replace('_', ' ').title()}</h3>
        </div>
        """, unsafe_allow_html=True)

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Revenue",
                f"${current['revenue_generated']:,.0f}",
                delta=performance["trends"]["revenue"].replace('_', ' ').title() if "trends" in performance else None
            )

        with col2:
            st.metric(
                "Sales Volume",
                f"{current['total_sales']:,}",
                delta=performance["trends"]["sales"].replace('_', ' ').title() if "trends" in performance else None
            )

        with col3:
            st.metric(
                "Market Share",
                f"{current['market_share']:.1f}%"
            )

        with col4:
            st.metric(
                "Client Satisfaction",
                f"{current['client_satisfaction']:.1f}/5.0",
                delta=performance["trends"]["satisfaction"].replace('_', ' ').title() if "trends" in performance else None
            )

        # Additional performance metrics
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Conversion Rate", f"{current['conversion_rate']:.1f}%")

        with col2:
            st.metric("Profit Margin", f"{current['profit_margin']:.1f}%")

    except Exception as e:
        st.error(f"Error loading performance data: {e}")

def render_competitive_analysis():
    """Render competitive intelligence analysis."""
    st.subheader("🔍 Competitive Intelligence")
    st.info("Select a market area to view detailed competitive analysis including competitor profiles, market share distribution, and strategic recommendations.")

def render_market_forecasts():
    """Render market forecasts and predictions."""
    st.subheader("🔮 Market Forecasts & Predictions")
    st.info("Access predictive market analytics including price forecasts, inventory projections, and investment recommendations for strategic planning.")

def render_manager_market_interface():
    """Render manager-focused market intelligence interface."""
    st.subheader("👥 Team Market Intelligence")

    tab1, tab2, tab3 = st.tabs(["Territory Coverage", "Team Performance", "Market Analysis"])

    with tab1:
        render_territory_coverage_analysis()

    with tab2:
        st.info("Team performance analytics would be implemented here for manager oversight.")

    with tab3:
        st.info("Comparative market analysis tools would be available here.")

def render_territory_coverage_analysis():
    """Render territory coverage analysis for managers."""
    st.write("### Territory Coverage Analysis")

    try:
        coverage = asyncio.run(territory_management_service.get_territory_coverage_analysis())

        # Coverage overview
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Territories", coverage["total_territories"])
        with col2:
            st.metric("Assigned", coverage["assigned_territories"])
        with col3:
            st.metric("Unassigned", coverage["unassigned_territories"])
        with col4:
            st.metric("Shared", coverage["shared_territories"])

        # Agent workload analysis
        if coverage.get("agent_workload"):
            st.subheader("Agent Workload Distribution")

            workload_data = []
            for agent_id, workload in coverage["agent_workload"].items():
                workload_data.append({
                    "Agent": agent_id,
                    "Territories": workload["total_territories"],
                    "Primary": workload["primary_territories"],
                    "Market Potential": workload["total_market_potential"],
                    "Workload Level": workload["workload_level"].title()
                })

            if workload_data:
                workload_df = pd.DataFrame(workload_data)
                st.dataframe(workload_df, use_container_width=True)

                # Workload visualization
                fig = px.bar(
                    workload_df,
                    x="Agent",
                    y="Market Potential",
                    color="Workload Level",
                    title="Agent Market Potential Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)

        # Coverage gaps
        if coverage.get("coverage_gaps"):
            st.subheader("⚠️ Coverage Gaps")
            for gap in coverage["coverage_gaps"]:
                st.warning(f"🗺️ {gap['name']} (Potential: {gap['market_potential']:.1f}) - {gap['reason']}")

    except Exception as e:
        st.error(f"Error loading coverage analysis: {e}")

def render_admin_market_interface():
    """Render administrator interface for system-wide market intelligence."""
    st.subheader("⚙️ Market Intelligence Administration")

    tab1, tab2, tab3 = st.tabs(["System Metrics", "Data Management", "Configuration"])

    with tab1:
        st.info("Administrator market intelligence metrics would be displayed here.")

    with tab2:
        st.info("Market data import, export, and management tools would be available here.")

    with tab3:
        st.info("System configuration and settings for market intelligence services would be implemented here.")

# Helper functions
def get_priority_badge(priority: int) -> str:
    """Get priority badge for display."""
    if priority == 5:
        return "🔴 Critical"
    elif priority == 4:
        return "🟠 High"
    elif priority == 3:
        return "🟡 Medium"
    elif priority == 2:
        return "🟢 Low"
    else:
        return "⚪ Minimal"

def get_opportunity_emoji(opportunity_type: OpportunityType) -> str:
    """Get emoji for opportunity type."""
    emoji_map = {
        OpportunityType.UNDERVALUED_PROPERTY: "💎",
        OpportunityType.EMERGING_NEIGHBORHOOD: "🌱",
        OpportunityType.PRICE_REDUCTION: "📉",
        OpportunityType.NEW_DEVELOPMENT: "🏗️",
        OpportunityType.INVESTMENT_OPPORTUNITY: "💰",
        OpportunityType.FIRST_TIME_BUYER_MARKET: "🏠",
        OpportunityType.LUXURY_EXPANSION: "✨",
        OpportunityType.COMMERCIAL_OPPORTUNITY: "🏢"
    }
    return emoji_map.get(opportunity_type, "🎯")

# Export the render function for use in the main dashboard
if __name__ == "__main__":
    render_market_intelligence_dashboard()
            return None
        except Exception as e:
            st.error(f"Failed to initialize market intelligence service: {e}")
            return None

    def render(self, tenant_id: str) -> None:
        """Render the complete market intelligence dashboard."""
        st.header("📊 Market Intelligence Center")
        st.caption("Advanced market insights and competitive analysis")

        # Dashboard tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Market Overview",
            "🏘️ Competitive Analysis",
            "💡 Investment Opportunities",
            "📋 Market Reports"
        ])

        with tab1:
            self._render_market_overview(tenant_id)

        with tab2:
            self._render_competitive_analysis(tenant_id)

        with tab3:
            self._render_investment_opportunities(tenant_id)

        with tab4:
            self._render_market_reports(tenant_id)

    def _render_market_overview(self, tenant_id: str) -> None:
        """Render market overview and trends."""
        st.subheader("📈 Market Overview")

        # Market health indicators
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Market Health Score",
                value="8.4/10",
                delta="0.6 ↑ this quarter"
            )

        with col2:
            st.metric(
                label="Avg Price/SqFt",
                value="$342",
                delta="$18 ↑ (5.6%)"
            )

        with col3:
            st.metric(
                label="Days on Market",
                value="28 days",
                delta="-7 days (faster)"
            )

        with col4:
            st.metric(
                label="Inventory Levels",
                value="3.2 months",
                delta="-0.8 months"
            )

        # Market trend charts
        col1, col2 = st.columns(2)

        with col1:
            # Price trends by property type
            dates = pd.date_range('2025-07-01', periods=26, freq='W')
            price_trends = pd.DataFrame({
                'Date': dates,
                'Single Family': [450000 + i*3000 + np.random.normal(0, 5000) for i in range(26)],
                'Condos': [320000 + i*2000 + np.random.normal(0, 3000) for i in range(26)],
                'Townhomes': [380000 + i*2500 + np.random.normal(0, 4000) for i in range(26)]
            })

            fig_prices = go.Figure()

            for property_type in ['Single Family', 'Condos', 'Townhomes']:
                fig_prices.add_trace(go.Scatter(
                    x=price_trends['Date'],
                    y=price_trends[property_type],
                    mode='lines+markers',
                    name=property_type,
                    line=dict(width=3)
                ))

            fig_prices.update_layout(
                title="Median Price Trends by Property Type",
                xaxis_title="Date",
                yaxis_title="Median Price ($)",
                height=400
            )

            st.plotly_chart(fig_prices, use_container_width=True)

        with col2:
            # Market volume and inventory
            volume_data = pd.DataFrame({
                'Month': ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan'],
                'Sales Volume': [245, 268, 234, 198, 176, 142, 189],
                'New Listings': [312, 298, 276, 245, 198, 167, 223],
                'Active Inventory': [892, 856, 823, 798, 765, 734, 756]
            })

            fig_volume = make_subplots(
                rows=2, cols=1,
                subplot_titles=("Monthly Sales & New Listings", "Active Inventory"),
                specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
            )

            # Sales and listings
            fig_volume.add_trace(
                go.Bar(x=volume_data['Month'], y=volume_data['Sales Volume'], name="Sales Volume", marker_color='#1f77b4'),
                row=1, col=1
            )

            fig_volume.add_trace(
                go.Bar(x=volume_data['Month'], y=volume_data['New Listings'], name="New Listings", marker_color='#ff7f0e'),
                row=1, col=1
            )

            # Inventory
            fig_volume.add_trace(
                go.Scatter(x=volume_data['Month'], y=volume_data['Active Inventory'], name="Active Inventory", line=dict(color='#2ca02c', width=3)),
                row=2, col=1
            )

            fig_volume.update_layout(height=500, showlegend=True)
            st.plotly_chart(fig_volume, use_container_width=True)

        # Geographic market heat map
        st.subheader("Geographic Market Performance")

        # Mock neighborhood data
        neighborhoods = [
            {"name": "Downtown", "lat": 40.7128, "lon": -74.0060, "avg_price": 650000, "growth": 12.5, "volume": 45},
            {"name": "Midtown", "lat": 40.7589, "lon": -73.9851, "avg_price": 580000, "growth": 8.3, "volume": 67},
            {"name": "Brooklyn Heights", "lat": 40.6962, "lon": -73.9961, "avg_price": 720000, "growth": 15.2, "volume": 32},
            {"name": "Queens Village", "lat": 40.7282, "lon": -73.8370, "avg_price": 420000, "growth": 6.8, "volume": 89},
            {"name": "Staten Island", "lat": 40.5795, "lon": -74.1502, "avg_price": 380000, "growth": 9.1, "volume": 56}
        ]

        neighborhood_df = pd.DataFrame(neighborhoods)

        col1, col2 = st.columns(2)

        with col1:
            # Price vs growth scatter
            fig_scatter = px.scatter(
                neighborhood_df,
                x='avg_price',
                y='growth',
                size='volume',
                hover_name='name',
                title="Price vs Growth by Neighborhood",
                labels={'avg_price': 'Average Price ($)', 'growth': 'Price Growth (%)', 'volume': 'Sales Volume'}
            )

            fig_scatter.update_layout(height=400)
            st.plotly_chart(fig_scatter, use_container_width=True)

        with col2:
            # Top performing neighborhoods
            top_neighborhoods = neighborhood_df.nlargest(5, 'growth').sort_values('growth', ascending=True)

            fig_neighborhoods = px.bar(
                top_neighborhoods,
                x='growth',
                y='name',
                orientation='h',
                title="Top Growth Neighborhoods",
                labels={'growth': 'Price Growth (%)', 'name': 'Neighborhood'}
            )

            fig_neighborhoods.update_layout(height=400)
            st.plotly_chart(fig_neighborhoods, use_container_width=True)

        # Market indicators table
        st.subheader("Key Market Indicators")

        market_indicators = pd.DataFrame({
            'Indicator': [
                'Absorption Rate',
                'Price-to-Income Ratio',
                'Mortgage Delinquency',
                'Construction Permits',
                'Population Growth',
                'Employment Rate'
            ],
            'Current Value': ['4.2 months', '5.8x', '2.1%', '892 permits', '1.8%', '94.2%'],
            'Previous Period': ['4.8 months', '5.6x', '2.3%', '756 permits', '1.6%', '93.8%'],
            'Change': ['↓ 0.6 months', '↑ 0.2x', '↓ 0.2%', '↑ 136 permits', '↑ 0.2%', '↑ 0.4%'],
            'Status': ['Improving', 'Stable', 'Improving', 'Strong Growth', 'Stable', 'Improving']
        })

        st.dataframe(market_indicators, use_container_width=True)

    def _render_competitive_analysis(self, tenant_id: str) -> None:
        """Render competitive analysis."""
        st.subheader("🏘️ Competitive Analysis")

        # Competitor overview
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Market Share",
                value="23.4%",
                delta="2.1% ↑"
            )

        with col2:
            st.metric(
                label="Avg Days to Sell",
                value="18 days",
                delta="5 days faster than competitors"
            )

        with col3:
            st.metric(
                label="Price Competitiveness",
                value="98.5%",
                delta="1.2% ↑"
            )

        with col4:
            st.metric(
                label="Client Satisfaction",
                value="9.2/10",
                delta="0.8 points above average"
            )

        # Competitor comparison table
        st.subheader("Competitor Comparison")

        competitors_data = pd.DataFrame({
            'Company': ['Your Agency', 'Elite Realty', 'Metro Homes', 'Prime Properties', 'City Real Estate'],
            'Market Share (%)': [23.4, 18.7, 15.2, 14.8, 12.3],
            'Avg Sale Price': [485000, 462000, 451000, 478000, 441000],
            'Avg Days on Market': [18, 23, 28, 21, 32],
            'Client Rating': [9.2, 8.4, 8.1, 8.7, 7.9],
            'Active Listings': [156, 134, 98, 112, 87]
        })

        # Style the dataframe to highlight your agency
        def highlight_your_agency(row):
            if row['Company'] == 'Your Agency':
                return ['background-color: #90EE90'] * len(row)
            return [''] * len(row)

        styled_df = competitors_data.style.apply(highlight_your_agency, axis=1)
        st.dataframe(styled_df, use_container_width=True)

        # Competitive positioning charts
        col1, col2 = st.columns(2)

        with col1:
            # Market share pie chart
            fig_market_share = px.pie(
                competitors_data,
                values='Market Share (%)',
                names='Company',
                title="Market Share Distribution",
                color_discrete_sequence=px.colors.qualitative.Set3
            )

            fig_market_share.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_market_share, use_container_width=True)

        with col2:
            # Performance vs market share scatter
            fig_performance = px.scatter(
                competitors_data,
                x='Market Share (%)',
                y='Client Rating',
                size='Active Listings',
                hover_name='Company',
                title="Performance vs Market Share",
                labels={'Client Rating': 'Client Satisfaction Rating'}
            )

            fig_performance.update_layout(height=400)
            st.plotly_chart(fig_performance, use_container_width=True)

        # Competitive pricing analysis
        st.subheader("Pricing Analysis")

        # Price comparison by property type
        pricing_data = pd.DataFrame({
            'Property Type': ['Single Family', 'Condo', 'Townhome', 'Luxury', 'Starter Home'],
            'Your Pricing': [485000, 342000, 398000, 850000, 285000],
            'Market Average': [478000, 338000, 392000, 835000, 278000],
            'Elite Realty': [462000, 329000, 385000, 820000, 268000],
            'Metro Homes': [451000, 334000, 378000, 795000, 272000]
        })

        fig_pricing = go.Figure()

        companies = ['Your Pricing', 'Market Average', 'Elite Realty', 'Metro Homes']
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

        for i, company in enumerate(companies):
            fig_pricing.add_trace(go.Bar(
                name=company,
                x=pricing_data['Property Type'],
                y=pricing_data[company],
                marker_color=colors[i]
            ))

        fig_pricing.update_layout(
            title="Average Pricing by Property Type",
            xaxis_title="Property Type",
            yaxis_title="Average Price ($)",
            barmode='group',
            height=400
        )

        st.plotly_chart(fig_pricing, use_container_width=True)

        # Competitive strengths and weaknesses
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Competitive Strengths")
            strengths = [
                "🏆 Fastest average sales time (18 days)",
                "⭐ Highest client satisfaction (9.2/10)",
                "📈 Growing market share (+2.1%)",
                "💰 Premium pricing capability",
                "🎯 Strong digital marketing presence"
            ]

            for strength in strengths:
                st.write(strength)

        with col2:
            st.subheader("Areas for Improvement")
            improvements = [
                "📊 Increase luxury market presence",
                "🌍 Expand to emerging neighborhoods",
                "📱 Enhance mobile app features",
                "🤝 Build more strategic partnerships",
                "💡 Invest in AI-powered tools"
            ]

            for improvement in improvements:
                st.write(improvement)

        # Competitive alerts
        st.subheader("⚠️ Competitive Alerts")

        alerts = [
            {
                "type": "Price Drop",
                "competitor": "Elite Realty",
                "message": "Reduced listing prices by 3% in Downtown area",
                "impact": "Medium",
                "action": "Consider competitive pricing review"
            },
            {
                "type": "New Listing",
                "competitor": "Metro Homes",
                "message": "Listed 5 new luxury properties this week",
                "impact": "Low",
                "action": "Monitor luxury market activity"
            },
            {
                "type": "Marketing Campaign",
                "competitor": "Prime Properties",
                "message": "Launched aggressive digital advertising campaign",
                "impact": "High",
                "action": "Increase marketing budget allocation"
            }
        ]

        for alert in alerts:
            impact_color = {"High": "red", "Medium": "orange", "Low": "green"}[alert['impact']]

            st.markdown(f"""
            <div style="border: 1px solid {impact_color}; border-radius: 5px; padding: 10px; margin: 5px 0;">
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-weight: bold;">{alert['type']} - {alert['competitor']}</span>
                    <span style="color: {impact_color}; font-weight: bold;">{alert['impact']} Impact</span>
                </div>
                <p style="margin: 5px 0;">{alert['message']}</p>
                <small style="color: #666;">Recommended Action: {alert['action']}</small>
            </div>
            """, unsafe_allow_html=True)

    def _render_investment_opportunities(self, tenant_id: str) -> None:
        """Render investment opportunities."""
        st.subheader("💡 Investment Opportunities")

        # Opportunity overview
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Active Opportunities",
                value="27",
                delta="8 new this week"
            )

        with col2:
            st.metric(
                label="Avg ROI Potential",
                value="18.5%",
                delta="2.3% ↑"
            )

        with col3:
            st.metric(
                label="Total Investment Value",
                value="$12.4M",
                delta="$3.2M new opportunities"
            )

        with col4:
            st.metric(
                label="Success Rate",
                value="73%",
                delta="5% ↑ this quarter"
            )

        # Investment opportunities table
        st.subheader("Top Investment Opportunities")

        opportunities = pd.DataFrame({
            'Property': ['123 Oak Street', '456 Pine Avenue', '789 Maple Drive', '321 Elm Street', '654 Birch Lane'],
            'Type': ['Flip', 'Rental', 'Development', 'Rental', 'Flip'],
            'Price': [285000, 420000, 1200000, 380000, 310000],
            'Est. Value': [365000, 520000, 1650000, 470000, 395000],
            'ROI (%)': [28.1, 23.8, 37.5, 23.7, 27.4],
            'Risk Level': ['Medium', 'Low', 'High', 'Low', 'Medium'],
            'Timeline': ['6 months', '1 year', '18 months', '1 year', '4 months']
        })

        # Color code by risk level
        def color_risk(val):
            if val == 'Low':
                return 'background-color: #90EE90'
            elif val == 'Medium':
                return 'background-color: #FFD700'
            else:
                return 'background-color: #FFB6C1'

        styled_opportunities = opportunities.style.applymap(color_risk, subset=['Risk Level'])
        st.dataframe(styled_opportunities, use_container_width=True)

        # Opportunity analysis charts
        col1, col2 = st.columns(2)

        with col1:
            # ROI vs Risk scatter plot
            fig_roi_risk = px.scatter(
                opportunities,
                x='Risk Level',
                y='ROI (%)',
                size='Price',
                hover_name='Property',
                title="ROI vs Risk Analysis",
                color='Type',
                category_orders={'Risk Level': ['Low', 'Medium', 'High']}
            )

            fig_roi_risk.update_layout(height=400)
            st.plotly_chart(fig_roi_risk, use_container_width=True)

        with col2:
            # Investment type distribution
            type_counts = opportunities['Type'].value_counts()

            fig_types = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title="Investment Types Distribution"
            )

            fig_types.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_types, use_container_width=True)

        # Detailed opportunity analysis
        st.subheader("Opportunity Deep Dive")

        selected_property = st.selectbox(
            "Select Property for Analysis",
            opportunities['Property'].tolist()
        )

        selected_opportunity = opportunities[opportunities['Property'] == selected_property].iloc[0]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("Financial Analysis")
            st.write(f"**Purchase Price:** ${selected_opportunity['Price']:,}")
            st.write(f"**Estimated Value:** ${selected_opportunity['Est. Value']:,}")
            st.write(f"**Potential Profit:** ${selected_opportunity['Est. Value'] - selected_opportunity['Price']:,}")
            st.write(f"**ROI:** {selected_opportunity['ROI (%)']:.1f}%")
            st.write(f"**Timeline:** {selected_opportunity['Timeline']}")

        with col2:
            st.subheader("Market Context")
            st.write("**Neighborhood Growth:** 12.3% (annual)")
            st.write("**Comparable Sales:** $342-$398/sqft")
            st.write("**Rental Demand:** High")
            st.write("**School District:** A-rated")
            st.write("**Transportation:** Excellent access")

        with col3:
            st.subheader("Risk Assessment")
            risk_factors = {
                "Market Risk": "Low",
                "Renovation Risk": "Medium" if selected_opportunity['Type'] == 'Flip' else "Low",
                "Financing Risk": "Low",
                "Timeline Risk": "Medium",
                "Overall Risk": selected_opportunity['Risk Level']
            }

            for factor, level in risk_factors.items():
                color = {"Low": "green", "Medium": "orange", "High": "red"}[level]
                st.markdown(f"**{factor}:** <span style='color: {color}'>{level}</span>", unsafe_allow_html=True)

        # Investment recommendation
        if selected_opportunity['ROI (%)'] > 25 and selected_opportunity['Risk Level'] in ['Low', 'Medium']:
            st.success(f"🎯 **RECOMMENDED INVESTMENT**\nThis property shows excellent ROI potential ({selected_opportunity['ROI (%)']:.1f}%) with manageable risk ({selected_opportunity['Risk Level'].lower()} risk level).")
        elif selected_opportunity['ROI (%)'] > 20:
            st.warning(f"⚠️ **MODERATE RECOMMENDATION**\nGood ROI potential but requires careful risk management.")
        else:
            st.info(f"ℹ️ **UNDER REVIEW**\nProperty may require additional analysis or improved terms.")

    def _render_market_reports(self, tenant_id: str) -> None:
        """Render market reports and insights."""
        st.subheader("📋 Market Reports")

        # Report generation options
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Generate Custom Report")

            # Report configuration
            report_type = st.selectbox(
                "Report Type",
                ["Market Overview", "Competitive Analysis", "Investment Opportunities", "Price Trends", "Neighborhood Analysis"]
            )

            date_range = st.selectbox(
                "Time Period",
                ["Last Month", "Last Quarter", "Last 6 Months", "Last Year", "YTD"]
            )

            regions = st.multiselect(
                "Select Regions",
                ["Downtown", "Midtown", "Brooklyn Heights", "Queens Village", "Staten Island"],
                default=["Downtown", "Midtown"]
            )

            property_types = st.multiselect(
                "Property Types",
                ["Single Family", "Condo", "Townhome", "Luxury", "Commercial"],
                default=["Single Family", "Condo"]
            )

            if st.button("🔄 Generate Report"):
                st.success("Report generated successfully! Download link sent to your email.")

        with col2:
            st.subheader("Quick Insights")

            insights = [
                "📈 Prices up 8.3% QoQ",
                "🏘️ Inventory down 15%",
                "⚡ Sales velocity +23%",
                "🎯 Best ROI: Flip investments",
                "🏆 Leading neighborhood: Brooklyn Heights"
            ]

            for insight in insights:
                st.write(insight)

        # Recent reports
        st.subheader("Recent Market Reports")

        recent_reports = [
            {
                "title": "Q4 2025 Market Analysis",
                "date": "2026-01-05",
                "type": "Quarterly Report",
                "status": "Published",
                "downloads": 156
            },
            {
                "title": "Luxury Market Deep Dive",
                "date": "2025-12-28",
                "type": "Special Report",
                "status": "Published",
                "downloads": 89
            },
            {
                "title": "Investment Opportunities January",
                "date": "2026-01-01",
                "type": "Monthly Report",
                "status": "Published",
                "downloads": 203
            }
        ]

        for report in recent_reports:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                with col1:
                    st.write(f"**{report['title']}**")
                    st.caption(f"{report['type']} - {report['date']}")

                with col2:
                    status_color = "green" if report['status'] == "Published" else "orange"
                    st.markdown(f"Status: <span style='color: {status_color}'>{report['status']}</span>", unsafe_allow_html=True)

                with col3:
                    st.write(f"Downloads: {report['downloads']}")

                with col4:
                    if st.button("📥", key=f"download_{report['title']}"):
                        st.success("Report downloaded!")

                st.divider()

        # Market insights and recommendations
        st.subheader("📊 AI-Powered Market Insights")

        insights_data = [
            {
                "insight": "Emerging Opportunity",
                "description": "Queens Village showing 15% price appreciation potential based on infrastructure improvements",
                "confidence": 87,
                "action": "Increase marketing focus in Queens Village area"
            },
            {
                "insight": "Pricing Strategy",
                "description": "Luxury market premium pricing window closing in 4-6 weeks",
                "confidence": 92,
                "action": "Accelerate luxury listings and pricing"
            },
            {
                "insight": "Competitive Threat",
                "description": "Metro Homes gaining market share in starter home segment",
                "confidence": 78,
                "action": "Review starter home pricing and marketing"
            }
        ]

        for insight in insights_data:
            with st.container():
                confidence_color = "green" if insight['confidence'] > 85 else "orange" if insight['confidence'] > 70 else "red"

                st.markdown(f"""
                <div style="border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin: 10px 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: bold; color: #1f77b4;">{insight['insight']}</span>
                        <span style="color: {confidence_color}; font-weight: bold;">Confidence: {insight['confidence']}%</span>
                    </div>
                    <p style="margin: 10px 0;">{insight['description']}</p>
                    <div style="background-color: #f0f2f6; padding: 8px; border-radius: 3px;">
                        <strong>Recommended Action:</strong> {insight['action']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Export options
        st.subheader("Export Options")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📊 Export Market Data"):
                st.success("Market data exported to Excel")

        with col2:
            if st.button("📈 Export Charts & Graphs"):
                st.success("Charts exported as PDF")

        with col3:
            if st.button("📋 Export Full Report"):
                st.success("Comprehensive report exported")


def render_market_intelligence_dashboard(tenant_id: str) -> None:
    """Main function to render market intelligence dashboard."""
    dashboard = MarketIntelligenceDashboard()
    dashboard.render(tenant_id)


# Example usage for testing
if __name__ == "__main__":
    st.set_page_config(page_title="Market Intelligence Dashboard", layout="wide")
    render_market_intelligence_dashboard("test_tenant_123")