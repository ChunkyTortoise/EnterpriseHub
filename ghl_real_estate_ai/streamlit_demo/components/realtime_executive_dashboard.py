"""
Real-Time Executive Dashboard - Service 6 Advanced Analytics Visualization
Comprehensive executive command center with live KPI tracking, revenue attribution, and predictive insights
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant


@dataclass
class ExecutiveMetrics:
    """Executive-level metrics for real-time dashboard"""

    revenue_pipeline: float
    hot_leads_count: int
    response_velocity: float  # average response time in minutes
    conversion_rate: float
    agent_efficiency: float
    market_velocity_score: int
    revenue_attribution: Dict[str, float]
    predictive_revenue: List[float]
    lead_velocity_trend: List[int]
    competitive_position: float


@dataclass
class MarketIntelligence:
    """Market intelligence data"""

    neighborhood_activity: Dict[str, int]
    price_trends: Dict[str, float]
    inventory_levels: Dict[str, int]
    competition_analysis: Dict[str, Any]
    market_opportunities: List[str]


class RealTimeExecutiveDashboard:
    """
    Real-time executive dashboard with advanced analytics and predictive insights
    """

    def __init__(self):
        self.cache_service = get_cache_service()
        self.claude_assistant = ClaudeAssistant(context_type="executive_dashboard")
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize session state for dashboard"""
        if "executive_view_mode" not in st.session_state:
            st.session_state.executive_view_mode = "overview"
        if "dashboard_auto_refresh" not in st.session_state:
            st.session_state.dashboard_auto_refresh = True
        if "selected_time_range" not in st.session_state:
            st.session_state.selected_time_range = "24h"

    @st.cache_data(ttl=30)  # Refresh every 30 seconds
    def _get_executive_metrics(_self) -> ExecutiveMetrics:
        """Generate real-time executive metrics"""
        return ExecutiveMetrics(
            revenue_pipeline=2_400_000.0,
            hot_leads_count=3,
            response_velocity=2.3,
            conversion_rate=27.0,
            agent_efficiency=94.0,
            market_velocity_score=78,
            revenue_attribution={
                "AI Lead Qualification": 35.2,
                "Automated Follow-up": 28.1,
                "Manual Outreach": 22.4,
                "Referrals": 14.3,
            },
            predictive_revenue=[2.4, 3.1, 4.2, 5.5, 6.8],
            lead_velocity_trend=[10, 15, 8, 22, 18, 25, 30],
            competitive_position=82.5,
        )

    @st.cache_data(ttl=300)  # Refresh every 5 minutes
    def _get_market_intelligence(_self) -> MarketIntelligence:
        """Generate market intelligence data"""
        return MarketIntelligence(
            neighborhood_activity={
                "Downtown Rancho Cucamonga": 42,
                "South Lamar": 45,
                "Fontana": 38,
                "East Rancho Cucamonga": 31,
                "Ontario": 19,
                "Ontario Mills": 28,
                "Victoria Gardens": 15,
            },
            price_trends={
                "Downtown": 5.2,
                "South Lamar": 7.8,
                "Fontana": 3.1,
                "East Rancho Cucamonga": 12.4,
                "Ontario Mills": 2.9,
            },
            inventory_levels={"Under $300K": 45, "$300K-$500K": 78, "$500K-$750K": 34, "$750K+": 12},
            competition_analysis={
                "market_share": 15.7,
                "top_competitors": ["Keller Williams", "RE/MAX", "Coldwell Banker"],
                "competitive_advantages": ["AI Integration", "Response Speed", "Market Knowledge"],
            },
            market_opportunities=[
                "First-time buyers in Fontana",
                "Luxury segment downtown",
                "Investment properties east side",
            ],
        )

    def render_executive_header(self):
        """Render executive dashboard header with real-time status"""
        current_time = datetime.now().strftime("%H:%M:%S")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown(
                f"""
            <div style='display: flex; align-items: center; gap: 1rem;'>
                <div>
                    <h1 style='margin: 0; font-size: 2.5rem; font-weight: 800; color: #FFFFFF; font-family: "Space Grotesk", sans-serif;'>
                        EXECUTIVE COMMAND
                    </h1>
                    <p style='margin: 0.5rem 0 0 0; color: #8B949E; font-size: 1.1rem; font-weight: 500;'>
                        Real-time tactical intelligence • Last update: {current_time}
                    </p>
                </div>
                <div style='
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    background: #10B981;
                    box-shadow: 0 0 20px #10B981;
                    animation: pulse 2s infinite;
                '></div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col2:
            # Time range selector
            time_ranges = ["1h", "24h", "7d", "30d"]
            selected_range = st.selectbox(
                "Time Range",
                time_ranges,
                index=time_ranges.index(st.session_state.selected_time_range),
                key="time_range_selector",
            )
            st.session_state.selected_time_range = selected_range

        with col3:
            # Dashboard controls
            col3a, col3b = st.columns(2)
            with col3a:
                auto_refresh = st.checkbox(
                    "Auto-refresh", value=st.session_state.dashboard_auto_refresh, key="auto_refresh_toggle"
                )
                st.session_state.dashboard_auto_refresh = auto_refresh

            with col3b:
                if st.button("🔄 Refresh Now", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()

    def render_kpi_overview(self):
        """Render executive KPI overview with advanced metrics"""
        metrics = self._get_executive_metrics()

        st.markdown("### 📊 EXECUTIVE KPI OVERVIEW")

        # Primary KPIs row
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            self._render_advanced_metric_card(
                "🔥 HOT LEADS",
                str(metrics.hot_leads_count),
                "+2 since baseline",
                "#EF4444",
                trend_data=[1, 2, 1, 3, 2, 3, 3],
            )

        with col2:
            self._render_advanced_metric_card(
                "💰 PIPELINE",
                f"${metrics.revenue_pipeline / 1000000:.1f}M",
                "+15% QoQ",
                "#10B981",
                trend_data=[1.8, 2.1, 2.0, 2.3, 2.2, 2.4, 2.4],
            )

        with col3:
            self._render_advanced_metric_card(
                "⚡ VELOCITY",
                f"{metrics.response_velocity:.1f}m",
                "-30s avg",
                "#6366F1",
                trend_data=[3.2, 2.8, 2.9, 2.5, 2.4, 2.3, 2.3],
            )

        with col4:
            self._render_advanced_metric_card(
                "📈 CONVERSION",
                f"{metrics.conversion_rate:.0f}%",
                "+5% MoM",
                "#F59E0B",
                trend_data=[22, 24, 23, 25, 26, 27, 27],
            )

        with col5:
            self._render_advanced_metric_card(
                "🎯 EFFICIENCY",
                f"{metrics.agent_efficiency:.0f}%",
                "+2% today",
                "#8B5CF6",
                trend_data=[90, 92, 91, 93, 92, 94, 94],
            )

    def _render_advanced_metric_card(self, title: str, value: str, change: str, color: str, trend_data: List[float]):
        """Render advanced metric card with inline sparkline"""
        # Generate mini sparkline
        sparkline_svg = self._generate_svg_sparkline(trend_data, color)

        st.markdown(
            f"""
        <div style='
            background: rgba(22, 27, 34, 0.8);
            padding: 1.5rem;
            border-radius: 12px;
            border-left: 4px solid {color};
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            height: 140px;
        '>
            <div style='
                font-size: 0.7rem;
                opacity: 0.8;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: {color};
                margin-bottom: 0.8rem;
                font-family: "Space Grotesk", sans-serif;
            '>{title}</div>
            <div style='
                font-size: 2.2rem;
                font-weight: 800;
                color: #FFFFFF;
                margin-bottom: 0.8rem;
                font-family: "Space Grotesk", sans-serif;
            '>{value}</div>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div style='
                    font-size: 0.75rem;
                    color: {"#10B981" if change.startswith("+") else "#EF4444" if change.startswith("-") else "#8B949E"};
                    font-weight: 600;
                '>{change}</div>
                <div style='width: 60px; height: 20px;'>
                    {sparkline_svg}
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _generate_svg_sparkline(self, data: List[float], color: str) -> str:
        """Generate SVG sparkline for metric cards"""
        if not data or len(data) < 2:
            return ""

        min_val, max_val = min(data), max(data)
        if max_val == min_val:
            return ""

        width, height = 60, 20
        points = []

        for i, val in enumerate(data):
            x = (i / (len(data) - 1)) * width
            y = height - ((val - min_val) / (max_val - min_val)) * height
            points.append(f"{x},{y}")

        path = "M" + "L".join(points)

        return f"""
        <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">
            <path d="{path}" stroke="{color}" stroke-width="1.5" fill="none" opacity="0.8"/>
        </svg>
        """

    def render_revenue_attribution(self):
        """Render revenue attribution analysis"""
        metrics = self._get_executive_metrics()

        st.markdown("### 💰 REVENUE ATTRIBUTION ANALYSIS")

        col1, col2 = st.columns([1, 1])

        with col1:
            # Revenue attribution pie chart
            fig_attribution = go.Figure(
                data=[
                    go.Pie(
                        labels=list(metrics.revenue_attribution.keys()),
                        values=list(metrics.revenue_attribution.values()),
                        hole=0.6,
                        marker_colors=["#10B981", "#6366F1", "#F59E0B", "#8B5CF6"],
                    )
                ]
            )

            fig_attribution.update_layout(
                title="Revenue by Source (%)",
                title_font_size=16,
                title_font_color="#FFFFFF",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#FFFFFF"),
                showlegend=True,
                legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.1),
                height=300,
            )

            # Add center annotation
            fig_attribution.add_annotation(
                text=f"${metrics.revenue_pipeline / 1000000:.1f}M<br>Total Pipeline",
                x=0.5,
                y=0.5,
                font_size=14,
                font_color="#FFFFFF",
                showarrow=False,
            )

            st.plotly_chart(fig_attribution, use_container_width=True)

        with col2:
            # Revenue breakdown details
            st.markdown("#### 📈 Attribution Details")

            for source, percentage in metrics.revenue_attribution.items():
                revenue_amount = (percentage / 100) * metrics.revenue_pipeline

                st.markdown(
                    f"""
                <div style='
                    background: rgba(22, 27, 34, 0.6);
                    padding: 1rem;
                    border-radius: 8px;
                    margin-bottom: 0.8rem;
                    border: 1px solid rgba(255,255,255,0.05);
                '>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <div style='font-weight: 600; color: #FFFFFF; font-size: 0.9rem;'>{source}</div>
                            <div style='color: #8B949E; font-size: 0.8rem; margin-top: 0.3rem;'>${revenue_amount / 1000:.0f}K revenue</div>
                        </div>
                        <div style='
                            font-size: 1.2rem;
                            font-weight: 700;
                            color: #10B981;
                        '>{percentage}%</div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

    def render_predictive_analytics(self):
        """Render predictive analytics and forecasting"""
        metrics = self._get_executive_metrics()

        st.markdown("### 🔮 PREDICTIVE REVENUE ROADMAP")

        # Revenue forecast chart
        months = ["Jan", "Feb", "Mar", "Apr", "May"]
        forecast = metrics.predictive_revenue

        # Generate confidence bands
        confidence_upper = [val * 1.15 for val in forecast]
        confidence_lower = [val * 0.85 for val in forecast]

        fig_forecast = go.Figure()

        # Add confidence band
        fig_forecast.add_trace(
            go.Scatter(
                x=months + months[::-1],
                y=confidence_upper + confidence_lower[::-1],
                fill="toself",
                fillcolor="rgba(99, 102, 241, 0.1)",
                line=dict(color="rgba(255,255,255,0)"),
                hoverinfo="skip",
                showlegend=False,
                name="Confidence Band",
            )
        )

        # Add forecast line
        fig_forecast.add_trace(
            go.Scatter(
                x=months,
                y=forecast,
                mode="lines+markers",
                name="AI Projection",
                line=dict(color="#6366F1", width=4),
                marker=dict(size=8, color="#6366F1"),
            )
        )

        fig_forecast.update_layout(
            title="Revenue Projection (Next 5 Months)",
            title_font_size=18,
            title_font_color="#FFFFFF",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#FFFFFF"),
            showlegend=True,
            legend=dict(x=0, y=1),
            height=400,
            yaxis=dict(title="Revenue ($M)", gridcolor="rgba(255,255,255,0.1)", title_font_color="#8B949E"),
            xaxis=dict(title="Month", gridcolor="rgba(255,255,255,0.1)", title_font_color="#8B949E"),
        )

        st.plotly_chart(fig_forecast, use_container_width=True)

        # Forecast insights
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                f"""
            <div style='
                background: rgba(16, 185, 129, 0.1);
                padding: 1rem;
                border-radius: 8px;
                border: 1px solid rgba(16, 185, 129, 0.2);
                text-align: center;
            '>
                <div style='font-size: 1.8rem; font-weight: 700; color: #10B981; margin-bottom: 0.5rem;'>
                    ${forecast[-1]:.1f}M
                </div>
                <div style='color: #E6EDF3; font-size: 0.9rem;'>Projected May Revenue</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col2:
            growth_rate = ((forecast[-1] - forecast[0]) / forecast[0]) * 100
            st.markdown(
                f"""
            <div style='
                background: rgba(245, 158, 11, 0.1);
                padding: 1rem;
                border-radius: 8px;
                border: 1px solid rgba(245, 158, 11, 0.2);
                text-align: center;
            '>
                <div style='font-size: 1.8rem; font-weight: 700; color: #F59E0B; margin-bottom: 0.5rem;'>
                    +{growth_rate:.0f}%
                </div>
                <div style='color: #E6EDF3; font-size: 0.9rem;'>Growth Trajectory</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col3:
            confidence_score = 87  # AI confidence in prediction
            st.markdown(
                f"""
            <div style='
                background: rgba(139, 92, 246, 0.1);
                padding: 1rem;
                border-radius: 8px;
                border: 1px solid rgba(139, 92, 246, 0.2);
                text-align: center;
            '>
                <div style='font-size: 1.8rem; font-weight: 700; color: #8B5CF6; margin-bottom: 0.5rem;'>
                    {confidence_score}%
                </div>
                <div style='color: #E6EDF3; font-size: 0.9rem;'>AI Confidence</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    def render_market_intelligence_heatmap(self):
        """Render advanced market intelligence visualization"""
        market_data = self._get_market_intelligence()

        st.markdown("### 🗺️ MARKET INTELLIGENCE HEATMAP")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Neighborhood activity heatmap
            neighborhoods = list(market_data.neighborhood_activity.keys())
            activity_levels = list(market_data.neighborhood_activity.values())

            # Create 2D grid for heatmap visualization
            grid_size = 4
            heatmap_data = np.random.rand(grid_size, grid_size) * 100

            # Map actual data to grid
            for i, activity in enumerate(activity_levels[: grid_size * grid_size]):
                row, col = divmod(i, grid_size)
                if row < grid_size and col < grid_size:
                    heatmap_data[row][col] = activity

            fig_heatmap = go.Figure(
                data=go.Heatmap(
                    z=heatmap_data,
                    colorscale=[[0, "#0F172A"], [0.3, "#1E40AF"], [0.6, "#F59E0B"], [1, "#EF4444"]],
                    showscale=True,
                    colorbar=dict(
                        title="Lead Activity", titlefont=dict(color="#FFFFFF"), tickfont=dict(color="#FFFFFF")
                    ),
                )
            )

            fig_heatmap.update_layout(
                title="Lead Density by Area (Last 24h)",
                title_font_size=16,
                title_font_color="#FFFFFF",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=300,
                xaxis=dict(showticklabels=False),
                yaxis=dict(showticklabels=False),
            )

            st.plotly_chart(fig_heatmap, use_container_width=True)

        with col2:
            # Neighborhood rankings
            st.markdown("#### 🏆 Top Performing Areas")

            sorted_areas = sorted(market_data.neighborhood_activity.items(), key=lambda x: x[1], reverse=True)

            for i, (area, activity) in enumerate(sorted_areas[:5]):
                rank_colors = ["#EF4444", "#F59E0B", "#10B981", "#6366F1", "#8B5CF6"]
                color = rank_colors[i] if i < len(rank_colors) else "#8B949E"

                st.markdown(
                    f"""
                <div style='
                    background: rgba(22, 27, 34, 0.6);
                    padding: 0.8rem;
                    border-radius: 6px;
                    margin-bottom: 0.5rem;
                    border-left: 3px solid {color};
                    border: 1px solid rgba(255,255,255,0.05);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                '>
                    <div>
                        <div style='font-weight: 600; color: #FFFFFF; font-size: 0.9rem;'>#{i + 1} {area}</div>
                        <div style='color: #8B949E; font-size: 0.75rem;'>Last 24 hours</div>
                    </div>
                    <div style='
                        font-size: 1.1rem;
                        font-weight: 700;
                        color: {color};
                    '>{activity}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

    def render_competitive_analysis(self):
        """Render competitive analysis dashboard"""
        market_data = self._get_market_intelligence()
        metrics = self._get_executive_metrics()

        st.markdown("### ⚔️ COMPETITIVE INTELLIGENCE")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Market share gauge
            market_share = market_data.competition_analysis["market_share"]

            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=market_share,
                    ontario_mills={"x": [0, 1], "y": [0, 1]},
                    title={"text": "Market Share", "font": {"size": 14, "color": "#FFFFFF"}},
                    delta={"reference": 12.5, "suffix": "%"},
                    gauge={
                        "axis": {"range": [0, 30], "tickwidth": 1, "tickcolor": "#8B949E"},
                        "bar": {"color": "#10B981"},
                        "bgcolor": "rgba(255,255,255,0.05)",
                        "borderwidth": 1,
                        "bordercolor": "rgba(255,255,255,0.1)",
                        "steps": [
                            {"range": [0, 10], "color": "rgba(239, 68, 68, 0.1)"},
                            {"range": [10, 20], "color": "rgba(245, 158, 11, 0.1)"},
                            {"range": [20, 30], "color": "rgba(16, 185, 129, 0.1)"},
                        ],
                    },
                )
            )

            fig_gauge.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={"color": "#FFFFFF"}, height=250
            )

            st.plotly_chart(fig_gauge, use_container_width=True)

        with col2:
            # Competitive position
            st.markdown("#### 🎯 Position Analysis")

            position_score = metrics.competitive_position

            st.markdown(
                f"""
            <div style='
                background: rgba(22, 27, 34, 0.8);
                padding: 1.5rem;
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,0.05);
                text-align: center;
            '>
                <div style='
                    font-size: 3rem;
                    font-weight: 800;
                    color: #10B981;
                    margin-bottom: 0.5rem;
                '>{position_score:.0f}</div>
                <div style='color: #E6EDF3; font-size: 1rem; margin-bottom: 1rem;'>Competitive Score</div>
                <div style='
                    background: rgba(255,255,255,0.05);
                    height: 8px;
                    border-radius: 4px;
                    overflow: hidden;
                    margin-bottom: 0.5rem;
                '>
                    <div style='
                        background: #10B981;
                        width: {position_score}%;
                        height: 100%;
                        box-shadow: 0 0 10px #10B981;
                    '></div>
                </div>
                <div style='color: #8B949E; font-size: 0.8rem;'>Top 10% in market</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col3:
            # Competitive advantages
            st.markdown("#### 💪 Key Advantages")

            advantages = market_data.competition_analysis["competitive_advantages"]

            for advantage in advantages:
                st.markdown(
                    f"""
                <div style='
                    background: rgba(16, 185, 129, 0.1);
                    padding: 0.8rem;
                    border-radius: 6px;
                    margin-bottom: 0.5rem;
                    border: 1px solid rgba(16, 185, 129, 0.2);
                '>
                    <div style='color: #10B981; font-weight: 600; font-size: 0.9rem;'>
                        ✅ {advantage}
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

    def render_live_activity_feed(self):
        """Render live activity feed with real-time updates"""
        st.markdown("### 📡 LIVE INTELLIGENCE FEED")

        # Generate real-time activities
        activities = [
            {
                "timestamp": datetime.now() - timedelta(minutes=2),
                "type": "hot_lead",
                "message": "Sarah Martinez elevated to HOT status - Pre-approved $425K",
                "priority": "high",
            },
            {
                "timestamp": datetime.now() - timedelta(minutes=8),
                "type": "appointment",
                "message": "Showing scheduled: Mike Johnson - Tomorrow 3:00 PM",
                "priority": "medium",
            },
            {
                "timestamp": datetime.now() - timedelta(minutes=15),
                "type": "ai_action",
                "message": "AI dispatched personalized follow-up sequence to 8 warm leads",
                "priority": "low",
            },
            {
                "timestamp": datetime.now() - timedelta(minutes=23),
                "type": "market_alert",
                "message": "Price drop detected: 3 properties in target neighborhoods",
                "priority": "medium",
            },
            {
                "timestamp": datetime.now() - timedelta(minutes=35),
                "type": "conversion",
                "message": "Jennifer Wu signed purchase agreement - $500K closing",
                "priority": "high",
            },
        ]

        for activity in activities:
            self._render_activity_item(activity)

    def _render_activity_item(self, activity: Dict[str, Any]):
        """Render individual activity item"""
        priority_colors = {"high": "#EF4444", "medium": "#F59E0B", "low": "#10B981"}

        type_icons = {
            "hot_lead": "🔥",
            "appointment": "📅",
            "ai_action": "🤖",
            "market_alert": "📊",
            "conversion": "💰",
        }

        color = priority_colors.get(activity["priority"], "#6366F1")
        icon = type_icons.get(activity["type"], "📌")
        time_ago = (datetime.now() - activity["timestamp"]).total_seconds() / 60

        st.markdown(
            f"""
        <div style='
            background: rgba(22, 27, 34, 0.6);
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 0.8rem;
            border-left: 3px solid {color};
            border: 1px solid rgba(255,255,255,0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
        '>
            <div style='display: flex; align-items: center; gap: 0.8rem;'>
                <span style='font-size: 1.2rem;'>{icon}</span>
                <div>
                    <div style='color: #E6EDF3; font-weight: 500; font-size: 0.95rem; line-height: 1.4;'>
                        {activity["message"]}
                    </div>
                    <div style='color: #8B949E; font-size: 0.75rem; margin-top: 0.3rem;'>
                        {time_ago:.0f} minutes ago
                    </div>
                </div>
            </div>
            <div style='
                background: {color}20;
                color: {color};
                padding: 0.3rem 0.8rem;
                border-radius: 12px;
                font-size: 0.7rem;
                font-weight: 700;
                text-transform: uppercase;
                border: 1px solid {color}40;
            '>
                {activity["priority"]}
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def render_complete_executive_dashboard(self):
        """Render the complete real-time executive dashboard"""
        st.set_page_config(
            page_title="Service 6 - Real-Time Executive Command",
            page_icon="⚡",
            layout="wide",
            initial_sidebar_state="collapsed",
        )

        # Apply executive styling
        st.markdown(
            """
        <style>
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .main > div {
            padding-top: 1rem;
        }
        
        .stButton > button {
            background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
            border: none;
            border-radius: 6px;
            color: white;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .element-container:has(.stSelectbox) {
            background: rgba(22, 27, 34, 0.8);
            border-radius: 8px;
            padding: 0.5rem;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        # Header
        self.render_executive_header()
        st.markdown("---")

        # KPI Overview
        self.render_kpi_overview()
        st.markdown("---")

        # Main analytics section
        col1, col2 = st.columns([2, 1])

        with col1:
            # Revenue Attribution
            self.render_revenue_attribution()
            st.markdown("---")

            # Predictive Analytics
            self.render_predictive_analytics()

        with col2:
            # Market Intelligence
            self.render_market_intelligence_heatmap()
            st.markdown("---")

            # Competitive Analysis
            self.render_competitive_analysis()

        st.markdown("---")

        # Bottom section - Live feed and controls
        col1, col2 = st.columns([2, 1])

        with col1:
            self.render_live_activity_feed()

        with col2:
            # Quick action center
            st.markdown("### ⚡ EXECUTIVE ACTIONS")

            action_buttons = [
                ("🚀 Launch Campaign Blast", "primary"),
                ("📊 Generate Executive Report", "secondary"),
                ("🎯 Trigger Hot Lead Alerts", "secondary"),
                ("💬 AI Strategy Consultation", "secondary"),
            ]

            for label, style in action_buttons:
                if st.button(label, use_container_width=True, key=f"exec_action_{label}"):
                    st.toast(f"✅ {label} initiated")

        # Auto-refresh indicator
        if st.session_state.dashboard_auto_refresh:
            st.markdown(
                f"""
            <div style='
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: rgba(22, 27, 34, 0.95);
                padding: 0.8rem 1.2rem;
                border-radius: 20px;
                border: 1px solid rgba(239, 68, 68, 0.3);
                color: #EF4444;
                font-size: 0.75rem;
                font-weight: 600;
                backdrop-filter: blur(10px);
                box-shadow: 0 4px 20px rgba(239, 68, 68, 0.2);
            '>
                🔴 LIVE • Auto-refresh enabled
            </div>
            """,
                unsafe_allow_html=True,
            )


def render_realtime_executive_dashboard():
    """Main function to render the real-time executive dashboard"""
    dashboard = RealTimeExecutiveDashboard()
    dashboard.render_complete_executive_dashboard()


if __name__ == "__main__":
    render_realtime_executive_dashboard()
