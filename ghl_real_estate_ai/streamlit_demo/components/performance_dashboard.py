"""
Performance Dashboard Component for GHL Real Estate AI

Real-time performance monitoring with:
- Agent leaderboards and KPIs
- Campaign performance tracking
- Revenue attribution analysis
- Goal tracking and forecasting
- Mobile-responsive design
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


def render_performance_dashboard_css():
    """Inject custom CSS for performance dashboard - Obsidian Command Edition"""
    st.markdown(
        "\n    <style>\n    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;700&display=swap');\n\n    /* Performance Dashboard Styles */\n    .performance-container {\n        background: rgba(5, 7, 10, 0.8) !important;\n        border-radius: 20px;\n        padding: 2.5rem;\n        margin: 1rem 0;\n        box-shadow: 0 25px 60px rgba(0, 0, 0, 0.9);\n        border: 1px solid rgba(255, 255, 255, 0.05);\n        position: relative;\n        overflow: hidden;\n        backdrop-filter: blur(20px);\n    }\n\n    .performance-container::before {\n        content: '';\n        position: absolute;\n        top: 0;\n        left: 0;\n        right: 0;\n        bottom: 0;\n        background: radial-gradient(circle at 10% 10%, rgba(99, 102, 241, 0.05) 0%, transparent 50%),\n                    radial-gradient(circle at 90% 90%, rgba(16, 185, 129, 0.03) 0%, transparent 50%);\n        pointer-events: none;\n    }\n\n    .dashboard-header {\n        text-align: left;\n        color: white;\n        margin-bottom: 3rem;\n        position: relative;\n        z-index: 1;\n        border-bottom: 1px solid rgba(255,255,255,0.05);\n        padding-bottom: 2rem;\n    }\n\n    .dashboard-title {\n        font-family: 'Space Grotesk', sans-serif !important;\n        font-size: 3rem;\n        font-weight: 700;\n        margin: 0;\n        color: #FFFFFF;\n        letter-spacing: -0.04em;\n        text-transform: uppercase;\n    }\n\n    .dashboard-subtitle {\n        font-family: 'Inter', sans-serif;\n        font-size: 1.1rem;\n        margin: 0.75rem 0 0 0;\n        color: #8B949E;\n        font-weight: 500;\n        letter-spacing: 0.02em;\n    }\n\n    .kpi-grid {\n        display: grid;\n        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));\n        gap: 1.5rem;\n        margin: 2rem 0;\n    }\n\n    .kpi-card {\n        background: rgba(22, 27, 34, 0.7) !important;\n        border-radius: 12px;\n        padding: 1.75rem;\n        text-align: left;\n        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);\n        backdrop-filter: blur(12px);\n        border: 1px solid rgba(255, 255, 255, 0.05);\n        border-top: 1px solid rgba(255, 255, 255, 0.1);\n        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);\n        position: relative;\n        overflow: hidden;\n    }\n\n    .kpi-card:hover {\n        transform: translateY(-5px);\n        box-shadow: 0 12px 48px rgba(99, 102, 241, 0.2);\n        border-color: rgba(99, 102, 241, 0.3);\n    }\n\n    .kpi-icon {\n        font-size: 1.75rem;\n        margin-bottom: 1.25rem;\n        background: rgba(99, 102, 241, 0.1);\n        width: 50px;\n        height: 50px;\n        display: flex;\n        align-items: center;\n        justify-content: center;\n        border-radius: 10px;\n        border: 1px solid rgba(99, 102, 241, 0.2);\n    }\n\n    .kpi-value {\n        font-family: 'Space Grotesk', sans-serif !important;\n        font-size: 2.5rem;\n        font-weight: 700;\n        color: #FFFFFF;\n        margin: 0.5rem 0;\n        text-shadow: 0 0 15px rgba(255,255,255,0.1);\n    }\n\n    .kpi-label {\n        font-family: 'Space Grotesk', sans-serif !important;\n        font-size: 0.75rem;\n        color: #8B949E;\n        font-weight: 700;\n        text-transform: uppercase;\n        letter-spacing: 0.1em;\n    }\n\n    .kpi-change {\n        font-family: 'Inter', sans-serif;\n        font-size: 0.8rem;\n        font-weight: 700;\n        padding: 4px 10px;\n        border-radius: 6px;\n        display: inline-flex;\n        align-items: center;\n        gap: 0.25rem;\n        margin-top: 0.75rem;\n    }\n\n    .kpi-change.positive {\n        background: rgba(16, 185, 129, 0.1);\n        color: #10b981;\n        border: 1px solid rgba(16, 185, 129, 0.2);\n    }\n\n    .kpi-change.negative {\n        background: rgba(239, 68, 68, 0.1);\n        color: #ef4444;\n        border: 1px solid rgba(239, 68, 68, 0.2);\n    }\n\n    .leaderboard-container {\n        background: rgba(22, 27, 34, 0.6) !important;\n        border-radius: 16px;\n        padding: 2rem;\n        margin: 1.5rem 0;\n        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);\n        backdrop-filter: blur(10px);\n        border: 1px solid rgba(255, 255, 255, 0.05);\n    }\n\n    .leaderboard-title {\n        font-family: 'Space Grotesk', sans-serif !important;\n        font-size: 1.5rem;\n        font-weight: 700;\n        color: #FFFFFF;\n        margin: 0 0 2rem 0;\n        text-transform: uppercase;\n        letter-spacing: 0.05em;\n        display: flex;\n        align-items: center;\n        gap: 12px;\n    }\n\n    .agent-row {\n        display: flex;\n        align-items: center;\n        padding: 1.25rem 1.75rem;\n        margin: 0.75rem 0;\n        background: rgba(255, 255, 255, 0.02);\n        border-radius: 12px;\n        border: 1px solid rgba(255, 255, 255, 0.05);\n        transition: all 0.3s ease;\n    }\n\n    .agent-row:hover {\n        transform: translateX(10px);\n        background: rgba(99, 102, 241, 0.05);\n        border-color: rgba(99, 102, 241, 0.2);\n    }\n\n    .rank-badge {\n        width: 36px;\n        height: 36px;\n        border-radius: 8px;\n        display: flex;\n        align-items: center;\n        justify-content: center;\n        font-weight: 700;\n        font-family: 'Space Grotesk', sans-serif;\n        color: white;\n        margin-right: 1.5rem;\n    }\n\n    .rank-1 .rank-badge {\n        background: #f59e0b;\n        box-shadow: 0 0 15px rgba(245, 158, 11, 0.4);\n    }\n\n    .rank-badge.default {\n        background: rgba(255, 255, 255, 0.1);\n    }\n\n    .agent-avatar {\n        width: 44px;\n        height: 44px;\n        border-radius: 10px;\n        background: #6366F1;\n        display: flex;\n        align-items: center;\n        justify-content: center;\n        color: white;\n        font-weight: 700;\n        font-family: 'Space Grotesk', sans-serif;\n    }\n\n    .agent-details h4 {\n        margin: 0 0 4px 0;\n        color: #FFFFFF;\n        font-weight: 600;\n        font-family: 'Space Grotesk', sans-serif;\n    }\n\n    .agent-details p {\n        margin: 0;\n        color: #8B949E;\n        font-size: 0.85rem;\n    }\n\n    .metric-value {\n        font-family: 'Space Grotesk', sans-serif !important;\n        font-size: 1.5rem;\n        font-weight: 700;\n        color: #FFFFFF;\n    }\n\n    .metric-label {\n        font-family: 'Space Grotesk', sans-serif !important;\n        font-size: 0.7rem;\n        color: #8B949E;\n        font-weight: 700;\n        text-transform: uppercase;\n        letter-spacing: 0.05em;\n    }\n\n    .chart-section {\n        background: rgba(22, 27, 34, 0.6) !important;\n        border-radius: 16px;\n        padding: 2rem;\n        margin: 1.5rem 0;\n        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);\n        border: 1px solid rgba(255, 255, 255, 0.05);\n    }\n\n    .goal-progress-bar {\n        background: rgba(255, 255, 255, 0.05);\n        border-radius: 4px;\n        height: 8px;\n        margin: 1rem 0;\n        overflow: hidden;\n    }\n\n    .goal-progress-fill {\n        height: 100%;\n        background: #6366F1;\n        box-shadow: 0 0 10px #6366F1;\n        transition: width 1s ease-in-out;\n    }\n    </style>\n    ",
        unsafe_allow_html=True,
    )


class PerformanceDashboard:
    """Performance dashboard with agent metrics and goal tracking"""

    def __init__(self, realtime_service, state_manager):
        self.realtime_service = realtime_service
        self.state_manager = state_manager
        if "performance_tab" not in st.session_state:
            st.session_state.performance_tab = "overview"

    def render(self, container_key: str = "performance_dashboard"):
        """Render the performance dashboard"""
        render_performance_dashboard_css()
        st.markdown('<div class="performance-container">', unsafe_allow_html=True)
        self._render_header()
        self._render_tab_navigation()
        current_tab = st.session_state.performance_tab
        if current_tab == "overview":
            self._render_overview_tab()
        elif current_tab == "agents":
            self._render_agents_tab()
        elif current_tab == "campaigns":
            self._render_campaigns_tab()
        elif current_tab == "goals":
            self._render_goals_tab()
        st.markdown("</div>", unsafe_allow_html=True)

    def _render_header(self):
        """Render dashboard header"""
        st.markdown(
            f'\n        <div class="dashboard-header">\n            <h1 class="dashboard-title">⚡ Performance Command Center</h1>\n            <p class="dashboard-subtitle">Real-time team performance monitoring and optimization</p>\n        </div>\n        ',
            unsafe_allow_html=True,
        )

    def _render_tab_navigation(self):
        """Render tab navigation"""
        tabs = [
            ("overview", "📊 Overview"),
            ("agents", "👥 Agents"),
            ("campaigns", "📈 Campaigns"),
            ("goals", "🎯 Goals"),
        ]
        col1, col2, col3, col4 = st.columns(4)
        columns = [col1, col2, col3, col4]
        for i, (tab_key, tab_label) in enumerate(tabs):
            with columns[i]:
                if st.button(
                    tab_label,
                    key=f"perf_tab_{tab_key}",
                    use_container_width=True,
                    type="primary" if st.session_state.performance_tab == tab_key else "secondary",
                ):
                    st.session_state.performance_tab = tab_key
                    st.rerun()

    def _render_overview_tab(self):
        """Render overview tab with key metrics"""
        data = self._get_performance_data()
        self._render_kpi_grid(data)
        col1, col2 = st.columns(2)
        with col1:
            self._render_performance_trend_chart(data)
        with col2:
            self._render_revenue_breakdown_chart(data)
        self._render_team_summary(data)

    def _render_kpi_grid(self, data: Dict[str, Any]):
        """Render KPI grid"""
        kpis = [
            {
                "icon": "💰",
                "label": "Monthly Revenue",
                "value": f"${data['monthly_revenue']:,.0f}",
                "change": data["revenue_change"],
                "trend": "positive" if data["revenue_change"] > 0 else "negative",
            },
            {
                "icon": "🎯",
                "label": "Conversion Rate",
                "value": f"{data['conversion_rate']:.1f}%",
                "change": data["conversion_change"],
                "trend": "positive" if data["conversion_change"] > 0 else "negative",
            },
            {
                "icon": "📞",
                "label": "Calls Made",
                "value": f"{data['calls_made']:,}",
                "change": data["calls_change"],
                "trend": "positive" if data["calls_change"] > 0 else "negative",
            },
            {
                "icon": "📧",
                "label": "Emails Sent",
                "value": f"{data['emails_sent']:,}",
                "change": data["emails_change"],
                "trend": "positive" if data["emails_change"] > 0 else "negative",
            },
            {
                "icon": "⏱️",
                "label": "Avg Response Time",
                "value": f"{data['avg_response_time']}min",
                "change": data["response_time_change"],
                "trend": "negative" if data["response_time_change"] > 0 else "positive",
            },
            {
                "icon": "📈",
                "label": "Lead Score Avg",
                "value": f"{data['avg_lead_score']:.0f}",
                "change": data["lead_score_change"],
                "trend": "positive" if data["lead_score_change"] > 0 else "negative",
            },
        ]
        st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
        for kpi in kpis:
            trend = kpi.get("trend", "neutral")
            trend_icon = "📈" if trend == "positive" else "📉"
            change_sign = "+" if kpi["change"] > 0 else ""
            st.markdown(
                f"""\n            <div class="kpi-card">\n                <div class="kpi-icon">{kpi["icon"]}</div>\n                <div class="kpi-label">{kpi["label"]}</div>\n                <div class="kpi-value">{kpi["value"]}</div>\n                <div class="kpi-change {trend}">\n                    {trend_icon} {change_sign}{kpi["change"]:.1f}%\n                </div>\n            </div>\n            """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    def _render_performance_trend_chart(self, data: Dict[str, Any]):
        """Render performance trend chart - Obsidian Style"""
        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart

        st.markdown('<div class="chart-section">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">📈 PERFORMANCE TELEMETRY (30D)</h3>', unsafe_allow_html=True)
        dates, metrics = self._generate_performance_trends()
        fig = make_subplots(
            rows=2,
            cols=1,
            subplot_titles=["REVENUE & NODES", "CONVERSION & LATENCY"],
            vertical_spacing=0.15,
            specs=[[{"secondary_y": True}], [{"secondary_y": True}]],
        )
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=metrics["revenue"],
                name="Revenue",
                line=dict(color="#10b981", width=3),
                hovertemplate="<b>Date:</b> %{x}<br><b>Revenue:</b> $%{y:,.0f}<extra></extra>",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=metrics["leads"],
                name="Nodes",
                line=dict(color="#6366F1", width=2),
                yaxis="y2",
                hovertemplate="<b>Date:</b> %{x}<br><b>Nodes:</b> %{y}<extra></extra>",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=metrics["conversion_rate"],
                name="Conversion",
                line=dict(color="#f59e0b", width=3),
                hovertemplate="<b>Date:</b> %{x}<br><b>Conversion:</b> %{y:.1f}%<extra></extra>",
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=metrics["response_time"],
                name="Latency",
                line=dict(color="#8b5cf6", width=2),
                yaxis="y4",
                hovertemplate="<b>Date:</b> %{x}<br><b>Latency:</b> %{y} min<extra></extra>",
            ),
            row=2,
            col=1,
        )
        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    def _render_revenue_breakdown_chart(self, data: Dict[str, Any]):
        """Render revenue breakdown by source - Obsidian Style"""
        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart

        st.markdown('<div class="chart-section">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">💰 REVENUE ATTRIBUTION</h3>', unsafe_allow_html=True)
        revenue_sources = data["revenue_by_source"]
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=list(revenue_sources.keys()),
                    values=list(revenue_sources.values()),
                    hole=0.6,
                    marker=dict(
                        colors=["#6366F1", "#8b5cf6", "#f59e0b", "#10b981", "#ef4444"],
                        line=dict(color="rgba(255,255,255,0.1)", width=1),
                    ),
                    hovertemplate="<b>Source:</b> %{label}<br><b>Revenue:</b> $%{value:,.0f}<extra></extra>",
                )
            ]
        )
        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)
        top_source = max(revenue_sources, key=revenue_sources.get)
        top_revenue = revenue_sources[top_source]
        total_revenue = sum(revenue_sources.values())
        st.success(
            f"🏆 **Top Revenue Source:** {top_source} (${top_revenue:,.0f} - {top_revenue / total_revenue * 100:.1f}%)"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    def _render_team_summary(self, data: Dict[str, Any]):
        """Render team performance summary"""
        st.markdown('<div class="leaderboard-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="leaderboard-title">👥 Team Performance Summary</h3>', unsafe_allow_html=True)
        agents = data["agent_summary"]
        for i, agent in enumerate(agents[:5]):
            rank = i + 1
            rank_class = f"rank-{rank}" if rank <= 3 else "default"
            performance_score = (
                agent["conversions"] * 10
                + agent["calls_made"] * 0.1
                + agent["emails_sent"] * 0.05
                - agent["avg_response_time"] * 0.5
            )
            st.markdown(
                f"""\n            <div class="agent-row rank-{rank}">\n                <div class="rank-badge {rank_class}">{rank}</div>\n                <div class="agent-info">\n                    <div class="agent-avatar">{agent["name"][:2].upper()}</div>\n                    <div class="agent-details">\n                        <h4>{agent["name"]}</h4>\n                        <p>Performance Score: {performance_score:.1f}</p>\n                    </div>\n                </div>\n                <div class="agent-metrics">\n                    <div class="metric-item">\n                        <div class="metric-value">{agent["conversions"]}</div>\n                        <div class="metric-label">Conversions</div>\n                    </div>\n                    <div class="metric-item">\n                        <div class="metric-value">{agent["calls_made"]}</div>\n                        <div class="metric-label">Calls</div>\n                    </div>\n                    <div class="metric-item">\n                        <div class="metric-value">{agent["avg_response_time"]}m</div>\n                        <div class="metric-label">Response</div>\n                    </div>\n                </div>\n            </div>\n            """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    def _render_agents_tab(self):
        """Render detailed agent performance tab - Obsidian Style"""
        st.markdown("### 👥 AGENT PERFORMANCE TELEMETRY")
        data = self._get_performance_data()
        agents = data["agents_detailed"]
        self._render_agent_comparison_chart(agents)
        self._render_agent_cards(agents)

    def _render_agent_comparison_chart(self, agents: List[Dict[str, Any]]):
        """Render agent comparison chart - Obsidian Style"""
        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart

        st.markdown('<div class="chart-section">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">📊 CROSS-AGENT COMPARISON</h3>', unsafe_allow_html=True)
        agent_names = [agent["name"] for agent in agents]
        metrics = {
            "Conversions": [agent["conversions"] for agent in agents],
            "Calls": [agent["calls_made"] for agent in agents],
            "Signals": [agent["emails_sent"] for agent in agents],
            "Score": [agent["avg_lead_score"] for agent in agents],
        }
        fig = go.Figure()
        colors = ["#6366F1", "#8b5cf6", "#f59e0b", "#10b981"]
        for i, (metric_name, values) in enumerate(metrics.items()):
            fig.add_trace(
                go.Bar(
                    name=metric_name,
                    x=agent_names,
                    y=values,
                    marker_color=colors[i],
                    hovertemplate=f"<b>Agent:</b> %{{x}}<br><b>{metric_name}:</b> %{{y}}<extra></extra>",
                )
            )
        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    def _render_agent_cards(self, agents: List[Dict[str, Any]]):
        """Render individual agent performance cards - Obsidian Style"""
        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart

        st.markdown("### 📋 INDIVIDUAL TELEMETRY")
        cols = st.columns(2)
        for i, agent in enumerate(agents):
            with cols[i % 2]:
                with st.container():
                    st.markdown(
                        f"""\n                    <div style="\n                        background: rgba(22, 27, 34, 0.7);\n                        padding: 1.75rem;\n                        border-radius: 12px;\n                        box-shadow: 0 8px 32px rgba(0,0,0,0.6);\n                        margin: 1rem 0;\n                        border-left: 4px solid #6366F1;\n                        border: 1px solid rgba(255,255,255,0.05);\n                        border-left: 4px solid #6366F1;\n                        backdrop-filter: blur(12px);\n                    ">\n                        <h4 style="margin: 0 0 1rem 0; color: #FFFFFF; font-family: 'Space Grotesk', sans-serif; text-transform: uppercase;">{agent["name"]}</h4>\n                    </div>\n                    """,
                        unsafe_allow_html=True,
                    )
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Conversions", agent["conversions"], delta=f"+{agent['conversions_change']}")
                    with col2:
                        st.metric("Calls Made", agent["calls_made"], delta=f"+{agent['calls_change']}")
                    with col3:
                        st.metric(
                            "Latency", f"{agent['avg_response_time']}m", delta=f"{agent['response_time_change']:+}m"
                        )
                    trend_data = agent["performance_trend"]
                    fig = go.Figure()
                    fig.add_trace(
                        go.Scatter(
                            x=list(range(len(trend_data))),
                            y=trend_data,
                            mode="lines",
                            name="Score",
                            line=dict(color="#6366F1", width=3),
                            fill="tozeroy",
                            fillcolor="rgba(99, 102, 241, 0.1)",
                        )
                    )
                    st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)

    def _render_campaigns_tab(self):
        """Render campaign performance tab"""
        st.markdown("### 📈 Campaign Performance")
        data = self._get_performance_data()
        campaigns = data["campaigns"]
        campaign_df = pd.DataFrame(campaigns)
        campaign_df["ROI"] = campaign_df["roi"].apply(lambda x: f"{x:.1f}%")
        campaign_df["Cost"] = campaign_df["cost"].apply(lambda x: f"${x:,.0f}")
        campaign_df["Revenue"] = campaign_df["revenue"].apply(lambda x: f"${x:,.0f}")
        campaign_df["Conversion Rate"] = campaign_df["conversion_rate"].apply(lambda x: f"{x:.1f}%")
        display_df = campaign_df[["name", "Cost", "Revenue", "Conversion Rate", "ROI", "status"]]
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        st.markdown('<div class="chart-section">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">💰 Campaign ROI Analysis</h3>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=[c["name"] for c in campaigns],
                y=[c["roi"] for c in campaigns],
                marker=dict(
                    color=[c["roi"] for c in campaigns],
                    colorscale="RdYlGn",
                    showscale=True,
                    colorbar=dict(title="ROI (%)"),
                ),
                hovertemplate="<b>Campaign:</b> %{x}<br><b>ROI:</b> %{y:.1f}%<extra></extra>",
            )
        )
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=20, b=0), xaxis_title="Campaign", yaxis_title="ROI (%)")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    def _render_goals_tab(self):
        """Render goals and targets tab - Obsidian Style"""
        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart

        st.markdown("### 🎯 MISSION OBJECTIVES")
        data = self._get_performance_data()
        goals = data["goals"]
        for goal in goals:
            progress = min(goal["current"] / goal["target"] * 100, 100)
            st.markdown(
                f"""\n            <div style="\n                background: rgba(22, 27, 34, 0.7);\n                padding: 1.75rem;\n                border-radius: 12px;\n                margin: 1.25rem 0;\n                box-shadow: 0 8px 32px rgba(0,0,0,0.6);\n                border: 1px solid rgba(255,255,255,0.05);\n                backdrop-filter: blur(12px);\n            ">\n                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem;">\n                    <h4 style="margin: 0; color: #FFFFFF; font-family: 'Space Grotesk', sans-serif;">{goal["name"].upper()}</h4>\n                    <span style="font-weight: 700; color: #6366F1; font-family: 'Space Grotesk', sans-serif;">{goal["current"]:.0f} / {goal["target"]:.0f}</span>\n                </div>\n                <div class="goal-progress-bar">\n                    <div class="goal-progress-fill" style="width: {progress:.1f}%;"></div>\n                </div>\n                <div style="display: flex; justify-content: space-between; margin-top: 0.75rem; font-size: 0.8rem; color: #8B949E; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">\n                    <span>{progress:.1f}% COMPLETE</span>\n                    <span>TARGET: {goal["target_date"]}</span>\n                </div>\n            </div>\n            """,
                unsafe_allow_html=True,
            )
        st.markdown('<div class="chart-section">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">📊 ACHIEVEMENT PROJECTIONS</h3>', unsafe_allow_html=True)
        forecast_data = self._generate_goal_forecast(goals)
        fig = go.Figure()
        for goal_name, forecast in forecast_data.items():
            fig.add_trace(
                go.Scatter(
                    x=forecast["dates"],
                    y=forecast["projected"],
                    mode="lines",
                    name=f"{goal_name} (PROJ)",
                    line=dict(dash="dash", color="#6366F1"),
                    hovertemplate=f"<b>Goal:</b> {goal_name}<br><b>Date:</b> %{{x}}<br><b>Projected:</b> %{{y:.0f}}<extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=forecast["dates"][: len(forecast["actual"])],
                    y=forecast["actual"],
                    mode="lines+markers",
                    name=f"{goal_name} (ACTUAL)",
                    line=dict(width=3, color="#10b981"),
                    hovertemplate=f"<b>Goal:</b> {goal_name}<br><b>Date:</b> %{{x}}<br><b>Actual:</b> %{{y:.0f}}<extra></extra>",
                )
            )
        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    def _get_performance_data(self) -> Dict[str, Any]:
        """Get performance data for dashboard"""
        import random

        return {
            "monthly_revenue": random.randint(180000, 250000),
            "revenue_change": random.uniform(-5, 15),
            "conversion_rate": random.uniform(18, 28),
            "conversion_change": random.uniform(-2, 5),
            "calls_made": random.randint(1200, 1800),
            "calls_change": random.uniform(-10, 20),
            "emails_sent": random.randint(3500, 5000),
            "emails_change": random.uniform(-8, 25),
            "avg_response_time": random.randint(8, 18),
            "response_time_change": random.uniform(-5, 3),
            "avg_lead_score": random.randint(72, 88),
            "lead_score_change": random.uniform(-3, 8),
            "revenue_by_source": {
                "Website": random.randint(45000, 75000),
                "Facebook": random.randint(35000, 60000),
                "Google Ads": random.randint(40000, 70000),
                "Referral": random.randint(25000, 45000),
                "Direct": random.randint(15000, 30000),
            },
            "agent_summary": [
                {
                    "name": "Sarah Johnson",
                    "conversions": random.randint(25, 35),
                    "calls_made": random.randint(180, 250),
                    "emails_sent": random.randint(350, 450),
                    "avg_response_time": random.randint(8, 15),
                },
                {
                    "name": "Mike Chen",
                    "conversions": random.randint(20, 30),
                    "calls_made": random.randint(160, 220),
                    "emails_sent": random.randint(320, 420),
                    "avg_response_time": random.randint(10, 18),
                },
                {
                    "name": "Lisa Rodriguez",
                    "conversions": random.randint(28, 38),
                    "calls_made": random.randint(190, 260),
                    "emails_sent": random.randint(380, 480),
                    "avg_response_time": random.randint(6, 12),
                },
                {
                    "name": "David Kim",
                    "conversions": random.randint(18, 28),
                    "calls_made": random.randint(150, 210),
                    "emails_sent": random.randint(300, 400),
                    "avg_response_time": random.randint(12, 20),
                },
                {
                    "name": "Emily Davis",
                    "conversions": random.randint(22, 32),
                    "calls_made": random.randint(170, 230),
                    "emails_sent": random.randint(340, 440),
                    "avg_response_time": random.randint(9, 16),
                },
            ],
            "agents_detailed": self._generate_detailed_agent_data(),
            "campaigns": self._generate_campaign_data(),
            "goals": [
                {
                    "name": "Monthly Revenue Goal",
                    "current": random.randint(180000, 220000),
                    "target": 250000,
                    "target_date": "2026-01-31",
                },
                {
                    "name": "Conversion Rate Target",
                    "current": random.uniform(22, 26),
                    "target": 30,
                    "target_date": "2026-01-31",
                },
                {
                    "name": "Lead Response Time",
                    "current": random.uniform(10, 14),
                    "target": 8,
                    "target_date": "2026-01-31",
                },
                {
                    "name": "Team Productivity",
                    "current": random.uniform(85, 92),
                    "target": 95,
                    "target_date": "2026-01-31",
                },
            ],
        }

    def _generate_detailed_agent_data(self) -> List[Dict[str, Any]]:
        """Generate detailed agent performance data"""
        import random

        agents = ["Sarah Johnson", "Mike Chen", "Lisa Rodriguez", "David Kim", "Emily Davis"]
        detailed_data = []
        for agent in agents:
            detailed_data.append(
                {
                    "name": agent,
                    "conversions": random.randint(18, 38),
                    "conversions_change": random.randint(-3, 8),
                    "calls_made": random.randint(150, 260),
                    "calls_change": random.randint(-15, 25),
                    "emails_sent": random.randint(300, 480),
                    "emails_change": random.randint(-20, 35),
                    "avg_response_time": random.randint(6, 20),
                    "response_time_change": random.randint(-5, 3),
                    "avg_lead_score": random.randint(70, 90),
                    "performance_trend": [random.randint(70, 95) for _ in range(30)],
                }
            )
        return detailed_data

    def _generate_campaign_data(self) -> List[Dict[str, Any]]:
        """Generate campaign performance data"""
        import random

        campaigns = [
            "Facebook Lead Gen",
            "Google Search Ads",
            "LinkedIn Campaign",
            "Email Nurture Sequence",
            "Referral Program",
            "Website SEO",
        ]
        campaign_data = []
        for campaign in campaigns:
            cost = random.randint(2000, 8000)
            revenue = random.randint(cost * 1.2, cost * 5)
            roi = (revenue - cost) / cost * 100
            campaign_data.append(
                {
                    "name": campaign,
                    "cost": cost,
                    "revenue": revenue,
                    "roi": roi,
                    "conversion_rate": random.uniform(12, 35),
                    "status": random.choice(["Active", "Paused", "Completed"]),
                }
            )
        return campaign_data

    def _generate_performance_trends(self):
        """Generate performance trend data"""
        import random

        dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]
        trends = {
            "revenue": [random.randint(6000, 12000) for _ in range(30)],
            "leads": [random.randint(25, 65) for _ in range(30)],
            "conversion_rate": [random.uniform(15, 30) for _ in range(30)],
            "response_time": [random.randint(8, 25) for _ in range(30)],
        }
        return (dates, trends)

    def _generate_goal_forecast(self, goals: List[Dict[str, Any]]) -> Dict[str, Dict[str, List]]:
        """Generate goal achievement forecast"""
        import random

        forecast_data = {}
        for goal in goals[:2]:
            dates = [datetime.now() + timedelta(days=i) for i in range(-15, 16)]
            actual = [goal["current"] * (0.7 + i * 0.02 + random.uniform(-0.05, 0.05)) for i in range(15)]
            projected = actual + [actual[-1] * (1 + 0.03 + random.uniform(-0.01, 0.02)) for _ in range(16)]
            forecast_data[goal["name"]] = {"dates": dates, "actual": actual, "projected": projected}
        return forecast_data


def render_performance_dashboard(realtime_service, state_manager):
    """Main function to render the performance dashboard"""
    dashboard = PerformanceDashboard(realtime_service, state_manager)
    dashboard.render()


if __name__ == "__main__":
    st.set_page_config(page_title="Performance Dashboard Demo", page_icon="⚡", layout="wide")

    class MockRealtimeService:
        @st.cache_data(ttl=300)
        def get_recent_events(self, event_type=None, limit=50, since=None):
            return []

    class MockStateManager:
        class UserPreferences:
            auto_refresh = True

        user_preferences = UserPreferences()

    st.title("⚡ Performance Dashboard Demo")
    render_performance_dashboard(MockRealtimeService(), MockStateManager())
