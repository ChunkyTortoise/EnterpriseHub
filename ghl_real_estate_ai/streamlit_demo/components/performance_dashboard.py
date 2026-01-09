"""
Performance Dashboard Component for GHL Real Estate AI

Real-time performance monitoring with:
- Agent leaderboards and KPIs
- Campaign performance tracking
- Revenue attribution analysis
- Goal tracking and forecasting
- Mobile-responsive design
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import time
from typing import Dict, List, Any, Optional

def render_performance_dashboard_css():
    """Inject custom CSS for performance dashboard"""
    st.markdown("""
    <style>
    /* Performance Dashboard Styles */
    .performance-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 20px 40px rgba(102, 126, 234, 0.15);
        position: relative;
        overflow: hidden;
    }

    .performance-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.3), transparent 50%),
                    radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.15), transparent 50%);
        pointer-events: none;
    }

    .dashboard-header {
        text-align: center;
        color: white;
        margin-bottom: 2rem;
        position: relative;
        z-index: 1;
    }

    .dashboard-title {
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
        background: linear-gradient(45deg, #fff, #f0f8ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 2px 8px rgba(0,0,0,0.1);
        letter-spacing: 1px;
    }

    .dashboard-subtitle {
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-weight: 300;
    }

    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }

    .kpi-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(45deg, #667eea, #764ba2);
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }

    .kpi-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.15);
    }

    .kpi-card:hover::before {
        transform: scaleX(1);
    }

    .kpi-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        opacity: 0.8;
    }

    .kpi-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: #2c3e50;
        margin: 0.5rem 0;
        position: relative;
        background: linear-gradient(45deg, #2c3e50, #3498db);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .kpi-label {
        font-size: 0.95rem;
        color: #7f8c8d;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }

    .kpi-change {
        font-size: 0.9rem;
        font-weight: 700;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        margin-top: 0.5rem;
    }

    .kpi-change.positive {
        background: linear-gradient(45deg, #2ecc71, #27ae60);
        color: white;
    }

    .kpi-change.negative {
        background: linear-gradient(45deg, #e74c3c, #c0392b);
        color: white;
    }

    .kpi-change.neutral {
        background: linear-gradient(45deg, #95a5a6, #7f8c8d);
        color: white;
    }

    .leaderboard-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        position: relative;
    }

    .leaderboard-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: #2c3e50;
        margin: 0 0 1.5rem 0;
        text-align: center;
        padding-bottom: 0.75rem;
        border-bottom: 3px solid transparent;
        background: linear-gradient(white, white), linear-gradient(45deg, #667eea, #764ba2);
        background-clip: padding-box, border-box;
        border-image: linear-gradient(45deg, #667eea, #764ba2) 1;
    }

    .agent-row {
        display: flex;
        align-items: center;
        padding: 1rem 1.5rem;
        margin: 0.75rem 0;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
        border-left: 4px solid transparent;
    }

    .agent-row:hover {
        transform: translateX(8px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
    }

    .agent-row.rank-1 {
        border-left-color: #f39c12;
        background: linear-gradient(135deg, #fff9f0 0%, #ffeaa7 10%, white 10%);
    }

    .agent-row.rank-2 {
        border-left-color: #95a5a6;
        background: linear-gradient(135deg, #f8f9fa 0%, #ddd 10%, white 10%);
    }

    .agent-row.rank-3 {
        border-left-color: #e67e22;
        background: linear-gradient(135deg, #fff5f0 0%, #fab1a0 10%, white 10%);
    }

    .rank-badge {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: white;
        margin-right: 1rem;
        font-size: 1.1rem;
    }

    .rank-1 .rank-badge {
        background: linear-gradient(45deg, #f39c12, #e67e22);
        animation: gold-shine 2s infinite;
    }

    .rank-2 .rank-badge {
        background: linear-gradient(45deg, #95a5a6, #7f8c8d);
    }

    .rank-3 .rank-badge {
        background: linear-gradient(45deg, #e67e22, #d35400);
    }

    .rank-badge.default {
        background: linear-gradient(45deg, #3498db, #2980b9);
    }

    @keyframes gold-shine {
        0%, 100% { box-shadow: 0 0 20px rgba(243, 156, 18, 0.5); }
        50% { box-shadow: 0 0 30px rgba(243, 156, 18, 0.8); }
    }

    .agent-info {
        flex: 1;
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .agent-avatar {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: linear-gradient(45deg, #667eea, #764ba2);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 1.2rem;
    }

    .agent-details h4 {
        margin: 0 0 0.25rem 0;
        color: #2c3e50;
        font-weight: 600;
        font-size: 1.1rem;
    }

    .agent-details p {
        margin: 0;
        color: #7f8c8d;
        font-size: 0.9rem;
    }

    .agent-metrics {
        display: flex;
        gap: 2rem;
        text-align: right;
    }

    .metric-item {
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .metric-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #2c3e50;
        margin: 0;
    }

    .metric-label {
        font-size: 0.8rem;
        color: #7f8c8d;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .chart-section {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .chart-title {
        font-size: 1.4rem;
        font-weight: 600;
        color: #2c3e50;
        margin: 0 0 1rem 0;
        text-align: center;
    }

    .goal-progress-bar {
        background: #ecf0f1;
        border-radius: 10px;
        height: 12px;
        margin: 0.5rem 0;
        overflow: hidden;
        position: relative;
    }

    .goal-progress-fill {
        height: 100%;
        background: linear-gradient(45deg, #2ecc71, #27ae60);
        border-radius: 10px;
        transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    .goal-progress-fill::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.3) 50%, transparent 70%);
        animation: shine 2s infinite;
    }

    @keyframes shine {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }

    .performance-tabs {
        display: flex;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 0.25rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }

    .tab-button {
        flex: 1;
        padding: 0.75rem 1rem;
        border: none;
        background: transparent;
        color: white;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-weight: 500;
    }

    .tab-button.active {
        background: white;
        color: #2c3e50;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }

    .tab-button:hover:not(.active) {
        background: rgba(255, 255, 255, 0.1);
    }

    /* Mobile Responsive */
    @media (max-width: 768px) {
        .performance-container {
            padding: 1rem;
        }

        .dashboard-title {
            font-size: 1.8rem;
        }

        .kpi-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
        }

        .kpi-card {
            padding: 1rem;
        }

        .kpi-value {
            font-size: 2rem;
        }

        .leaderboard-container {
            padding: 1rem;
        }

        .agent-row {
            flex-direction: column;
            text-align: center;
            padding: 1rem;
        }

        .agent-metrics {
            gap: 1rem;
            margin-top: 1rem;
        }

        .chart-section {
            padding: 1rem;
        }
    }

    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .kpi-card, .leaderboard-container, .chart-section {
            background: rgba(44, 62, 80, 0.95);
            color: white;
        }

        .kpi-label, .metric-label {
            color: #bdc3c7;
        }

        .agent-details h4 {
            color: white;
        }

        .agent-details p {
            color: #bdc3c7;
        }
    }
    </style>
    """, unsafe_allow_html=True)

class PerformanceDashboard:
    """Performance dashboard with agent metrics and goal tracking"""

    def __init__(self, realtime_service, state_manager):
        self.realtime_service = realtime_service
        self.state_manager = state_manager

        # Initialize performance tabs state
        if 'performance_tab' not in st.session_state:
            st.session_state.performance_tab = 'overview'

    def render(self, container_key: str = "performance_dashboard"):
        """Render the performance dashboard"""
        # Inject CSS
        render_performance_dashboard_css()

        # Main container
        st.markdown('<div class="performance-container">', unsafe_allow_html=True)

        # Header
        self._render_header()

        # Tab navigation
        self._render_tab_navigation()

        # Tab content
        current_tab = st.session_state.performance_tab

        if current_tab == 'overview':
            self._render_overview_tab()
        elif current_tab == 'agents':
            self._render_agents_tab()
        elif current_tab == 'campaigns':
            self._render_campaigns_tab()
        elif current_tab == 'goals':
            self._render_goals_tab()

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_header(self):
        """Render dashboard header"""
        st.markdown(f"""
        <div class="dashboard-header">
            <h1 class="dashboard-title">⚡ Performance Command Center</h1>
            <p class="dashboard-subtitle">Real-time team performance monitoring and optimization</p>
        </div>
        """, unsafe_allow_html=True)

    def _render_tab_navigation(self):
        """Render tab navigation"""
        tabs = [
            ('overview', '📊 Overview'),
            ('agents', '👥 Agents'),
            ('campaigns', '📈 Campaigns'),
            ('goals', '🎯 Goals')
        ]

        col1, col2, col3, col4 = st.columns(4)
        columns = [col1, col2, col3, col4]

        for i, (tab_key, tab_label) in enumerate(tabs):
            with columns[i]:
                if st.button(
                    tab_label,
                    key=f"perf_tab_{tab_key}",
                    use_container_width=True,
                    type="primary" if st.session_state.performance_tab == tab_key else "secondary"
                ):
                    st.session_state.performance_tab = tab_key
                    st.rerun()

    def _render_overview_tab(self):
        """Render overview tab with key metrics"""
        # Get performance data
        data = self._get_performance_data()

        # Key Performance Indicators
        self._render_kpi_grid(data)

        # Charts section
        col1, col2 = st.columns(2)

        with col1:
            self._render_performance_trend_chart(data)

        with col2:
            self._render_revenue_breakdown_chart(data)

        # Team performance summary
        self._render_team_summary(data)

    def _render_kpi_grid(self, data: Dict[str, Any]):
        """Render KPI grid"""
        kpis = [
            {
                'icon': '💰',
                'label': 'Monthly Revenue',
                'value': f"${data['monthly_revenue']:,.0f}",
                'change': data['revenue_change'],
                'trend': 'positive' if data['revenue_change'] > 0 else 'negative'
            },
            {
                'icon': '🎯',
                'label': 'Conversion Rate',
                'value': f"{data['conversion_rate']:.1f}%",
                'change': data['conversion_change'],
                'trend': 'positive' if data['conversion_change'] > 0 else 'negative'
            },
            {
                'icon': '📞',
                'label': 'Calls Made',
                'value': f"{data['calls_made']:,}",
                'change': data['calls_change'],
                'trend': 'positive' if data['calls_change'] > 0 else 'negative'
            },
            {
                'icon': '📧',
                'label': 'Emails Sent',
                'value': f"{data['emails_sent']:,}",
                'change': data['emails_change'],
                'trend': 'positive' if data['emails_change'] > 0 else 'negative'
            },
            {
                'icon': '⏱️',
                'label': 'Avg Response Time',
                'value': f"{data['avg_response_time']}min",
                'change': data['response_time_change'],
                'trend': 'negative' if data['response_time_change'] > 0 else 'positive'
            },
            {
                'icon': '📈',
                'label': 'Lead Score Avg',
                'value': f"{data['avg_lead_score']:.0f}",
                'change': data['lead_score_change'],
                'trend': 'positive' if data['lead_score_change'] > 0 else 'negative'
            }
        ]

        st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)

        for kpi in kpis:
            trend_icon = "📈" if kpi['trend'] == 'positive' else "📉"
            change_sign = "+" if kpi['change'] > 0 else ""

            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon">{kpi['icon']}</div>
                <div class="kpi-label">{kpi['label']}</div>
                <div class="kpi-value">{kpi['value']}</div>
                <div class="kpi-change {kpi['trend']}">
                    {trend_icon} {change_sign}{kpi['change']:.1f}%
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_performance_trend_chart(self, data: Dict[str, Any]):
        """Render performance trend chart"""
        st.markdown('<div class="chart-section">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">📈 Performance Trends (30 Days)</h3>', unsafe_allow_html=True)

        # Generate trend data
        dates, metrics = self._generate_performance_trends()

        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=['Revenue & Leads', 'Conversion Rate & Response Time'],
            vertical_spacing=0.1,
            specs=[[{"secondary_y": True}], [{"secondary_y": True}]]
        )

        # Revenue trend (left y-axis)
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=metrics['revenue'],
                name='Revenue',
                line=dict(color='#2ecc71', width=3),
                hovertemplate='<b>Date:</b> %{x}<br><b>Revenue:</b> $%{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )

        # Leads trend (right y-axis)
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=metrics['leads'],
                name='Leads',
                line=dict(color='#3498db', width=2),
                yaxis='y2',
                hovertemplate='<b>Date:</b> %{x}<br><b>Leads:</b> %{y}<extra></extra>'
            ),
            row=1, col=1
        )

        # Conversion rate
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=metrics['conversion_rate'],
                name='Conversion Rate',
                line=dict(color='#e74c3c', width=3),
                hovertemplate='<b>Date:</b> %{x}<br><b>Conversion:</b> %{y:.1f}%<extra></extra>'
            ),
            row=2, col=1
        )

        # Response time (right y-axis)
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=metrics['response_time'],
                name='Response Time',
                line=dict(color='#f39c12', width=2),
                yaxis='y4',
                hovertemplate='<b>Date:</b> %{x}<br><b>Response Time:</b> %{y} min<extra></extra>'
            ),
            row=2, col=1
        )

        fig.update_layout(
            height=500,
            margin=dict(l=0, r=0, t=40, b=0),
            hovermode='x unified',
            showlegend=True
        )

        # Update y-axes labels
        fig.update_yaxes(title_text="Revenue ($)", row=1, col=1)
        fig.update_yaxes(title_text="Leads", secondary_y=True, row=1, col=1)
        fig.update_yaxes(title_text="Conversion Rate (%)", row=2, col=1)
        fig.update_yaxes(title_text="Response Time (min)", secondary_y=True, row=2, col=1)

        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    def _render_revenue_breakdown_chart(self, data: Dict[str, Any]):
        """Render revenue breakdown by source"""
        st.markdown('<div class="chart-section">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">💰 Revenue by Source</h3>', unsafe_allow_html=True)

        revenue_sources = data['revenue_by_source']

        fig = go.Figure(data=[go.Pie(
            labels=list(revenue_sources.keys()),
            values=list(revenue_sources.values()),
            hole=0.5,
            marker=dict(
                colors=['#3498db', '#e74c3c', '#f39c12', '#2ecc71', '#9b59b6'],
                line=dict(color='white', width=3)
            ),
            hovertemplate='<b>Source:</b> %{label}<br><b>Revenue:</b> $%{value:,.0f}<br><b>Percentage:</b> %{percent}<extra></extra>'
        )])

        fig.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.1)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Revenue insights
        top_source = max(revenue_sources, key=revenue_sources.get)
        top_revenue = revenue_sources[top_source]
        total_revenue = sum(revenue_sources.values())

        st.success(f"🏆 **Top Revenue Source:** {top_source} (${top_revenue:,.0f} - {(top_revenue/total_revenue*100):.1f}%)")

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_team_summary(self, data: Dict[str, Any]):
        """Render team performance summary"""
        st.markdown('<div class="leaderboard-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="leaderboard-title">👥 Team Performance Summary</h3>', unsafe_allow_html=True)

        agents = data['agent_summary']

        for i, agent in enumerate(agents[:5]):  # Top 5 agents
            rank = i + 1
            rank_class = f"rank-{rank}" if rank <= 3 else "default"

            # Calculate performance score
            performance_score = (
                agent['conversions'] * 10 +
                agent['calls_made'] * 0.1 +
                agent['emails_sent'] * 0.05 -
                agent['avg_response_time'] * 0.5
            )

            st.markdown(f"""
            <div class="agent-row rank-{rank}">
                <div class="rank-badge {rank_class}">{rank}</div>
                <div class="agent-info">
                    <div class="agent-avatar">{agent['name'][:2].upper()}</div>
                    <div class="agent-details">
                        <h4>{agent['name']}</h4>
                        <p>Performance Score: {performance_score:.1f}</p>
                    </div>
                </div>
                <div class="agent-metrics">
                    <div class="metric-item">
                        <div class="metric-value">{agent['conversions']}</div>
                        <div class="metric-label">Conversions</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">{agent['calls_made']}</div>
                        <div class="metric-label">Calls</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">{agent['avg_response_time']}m</div>
                        <div class="metric-label">Response</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_agents_tab(self):
        """Render detailed agent performance tab"""
        st.markdown("### 👥 Agent Performance Analysis")

        data = self._get_performance_data()
        agents = data['agents_detailed']

        # Agent comparison chart
        self._render_agent_comparison_chart(agents)

        # Individual agent cards
        self._render_agent_cards(agents)

    def _render_agent_comparison_chart(self, agents: List[Dict[str, Any]]):
        """Render agent comparison chart"""
        st.markdown('<div class="chart-section">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">📊 Agent Performance Comparison</h3>', unsafe_allow_html=True)

        # Create comparison metrics
        agent_names = [agent['name'] for agent in agents]
        metrics = {
            'Conversions': [agent['conversions'] for agent in agents],
            'Calls Made': [agent['calls_made'] for agent in agents],
            'Email Sent': [agent['emails_sent'] for agent in agents],
            'Lead Score Avg': [agent['avg_lead_score'] for agent in agents]
        }

        fig = go.Figure()

        colors = ['#3498db', '#e74c3c', '#f39c12', '#2ecc71']

        for i, (metric_name, values) in enumerate(metrics.items()):
            fig.add_trace(go.Bar(
                name=metric_name,
                x=agent_names,
                y=values,
                marker_color=colors[i],
                hovertemplate=f'<b>Agent:</b> %{{x}}<br><b>{metric_name}:</b> %{{y}}<extra></extra>'
            ))

        fig.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=20, b=0),
            barmode='group',
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    def _render_agent_cards(self, agents: List[Dict[str, Any]]):
        """Render individual agent performance cards"""
        st.markdown("### 📋 Individual Performance")

        cols = st.columns(2)

        for i, agent in enumerate(agents):
            with cols[i % 2]:
                with st.container():
                    st.markdown(f"""
                    <div style="
                        background: white;
                        padding: 1.5rem;
                        border-radius: 12px;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                        margin: 1rem 0;
                        border-left: 4px solid #3498db;
                    ">
                        <h4 style="margin: 0 0 1rem 0; color: #2c3e50;">{agent['name']}</h4>
                    </div>
                    """, unsafe_allow_html=True)

                    # Performance metrics
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Conversions", agent['conversions'], delta=f"+{agent['conversions_change']}")

                    with col2:
                        st.metric("Calls Made", agent['calls_made'], delta=f"+{agent['calls_change']}")

                    with col3:
                        st.metric("Response Time", f"{agent['avg_response_time']}m", delta=f"{agent['response_time_change']:+}m")

                    # Performance trend (simplified)
                    trend_data = agent['performance_trend']
                    fig = go.Figure()

                    fig.add_trace(go.Scatter(
                        x=list(range(len(trend_data))),
                        y=trend_data,
                        mode='lines+markers',
                        name='Performance Score',
                        line=dict(color='#3498db', width=2),
                        fill='tonexty',
                        fillcolor='rgba(52, 152, 219, 0.1)'
                    ))

                    fig.update_layout(
                        height=200,
                        margin=dict(l=0, r=0, t=20, b=0),
                        showlegend=False,
                        xaxis_title="Days",
                        yaxis_title="Score"
                    )

                    st.plotly_chart(fig, use_container_width=True)

    def _render_campaigns_tab(self):
        """Render campaign performance tab"""
        st.markdown("### 📈 Campaign Performance")

        data = self._get_performance_data()
        campaigns = data['campaigns']

        # Campaign performance table
        campaign_df = pd.DataFrame(campaigns)

        # Format the dataframe for better display
        campaign_df['ROI'] = campaign_df['roi'].apply(lambda x: f"{x:.1f}%")
        campaign_df['Cost'] = campaign_df['cost'].apply(lambda x: f"${x:,.0f}")
        campaign_df['Revenue'] = campaign_df['revenue'].apply(lambda x: f"${x:,.0f}")
        campaign_df['Conversion Rate'] = campaign_df['conversion_rate'].apply(lambda x: f"{x:.1f}%")

        display_df = campaign_df[['name', 'Cost', 'Revenue', 'Conversion Rate', 'ROI', 'status']]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

        # Campaign ROI chart
        st.markdown('<div class="chart-section">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">💰 Campaign ROI Analysis</h3>', unsafe_allow_html=True)

        fig = go.Figure()

        # ROI bar chart
        fig.add_trace(go.Bar(
            x=[c['name'] for c in campaigns],
            y=[c['roi'] for c in campaigns],
            marker=dict(
                color=[c['roi'] for c in campaigns],
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title="ROI (%)")
            ),
            hovertemplate='<b>Campaign:</b> %{x}<br><b>ROI:</b> %{y:.1f}%<extra></extra>'
        ))

        fig.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=20, b=0),
            xaxis_title="Campaign",
            yaxis_title="ROI (%)"
        )

        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    def _render_goals_tab(self):
        """Render goals and targets tab"""
        st.markdown("### 🎯 Goals & Targets")

        data = self._get_performance_data()
        goals = data['goals']

        # Goals progress
        for goal in goals:
            progress = min(goal['current'] / goal['target'] * 100, 100)

            st.markdown(f"""
            <div style="
                background: white;
                padding: 1.5rem;
                border-radius: 12px;
                margin: 1rem 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h4 style="margin: 0; color: #2c3e50;">{goal['name']}</h4>
                    <span style="font-weight: bold; color: #3498db;">{goal['current']:.0f} / {goal['target']:.0f}</span>
                </div>
                <div class="goal-progress-bar">
                    <div class="goal-progress-fill" style="width: {progress:.1f}%;"></div>
                </div>
                <div style="display: flex; justify-content: between; margin-top: 0.5rem; font-size: 0.9rem; color: #7f8c8d;">
                    <span>{progress:.1f}% Complete</span>
                    <span style="margin-left: auto;">Target Date: {goal['target_date']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Goal achievement forecast
        st.markdown('<div class="chart-section">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">📊 Goal Achievement Forecast</h3>', unsafe_allow_html=True)

        # Generate forecast data
        forecast_data = self._generate_goal_forecast(goals)

        fig = go.Figure()

        for goal_name, forecast in forecast_data.items():
            fig.add_trace(go.Scatter(
                x=forecast['dates'],
                y=forecast['projected'],
                mode='lines',
                name=f"{goal_name} (Projected)",
                line=dict(dash='dash'),
                hovertemplate=f'<b>Goal:</b> {goal_name}<br><b>Date:</b> %{{x}}<br><b>Projected:</b> %{{y:.0f}}<extra></extra>'
            ))

            fig.add_trace(go.Scatter(
                x=forecast['dates'][:len(forecast['actual'])],
                y=forecast['actual'],
                mode='lines+markers',
                name=f"{goal_name} (Actual)",
                line=dict(width=3),
                hovertemplate=f'<b>Goal:</b> {goal_name}<br><b>Date:</b> %{{x}}<br><b>Actual:</b> %{{y:.0f}}<extra></extra>'
            ))

        fig.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=20, b=0),
            hovermode='x unified',
            yaxis_title="Progress"
        )

        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    def _get_performance_data(self) -> Dict[str, Any]:
        """Get performance data for dashboard"""
        import random

        # Simulate real performance data
        return {
            'monthly_revenue': random.randint(180000, 250000),
            'revenue_change': random.uniform(-5, 15),
            'conversion_rate': random.uniform(18, 28),
            'conversion_change': random.uniform(-2, 5),
            'calls_made': random.randint(1200, 1800),
            'calls_change': random.uniform(-10, 20),
            'emails_sent': random.randint(3500, 5000),
            'emails_change': random.uniform(-8, 25),
            'avg_response_time': random.randint(8, 18),
            'response_time_change': random.uniform(-5, 3),
            'avg_lead_score': random.randint(72, 88),
            'lead_score_change': random.uniform(-3, 8),
            'revenue_by_source': {
                'Website': random.randint(45000, 75000),
                'Facebook': random.randint(35000, 60000),
                'Google Ads': random.randint(40000, 70000),
                'Referral': random.randint(25000, 45000),
                'Direct': random.randint(15000, 30000)
            },
            'agent_summary': [
                {
                    'name': 'Sarah Johnson',
                    'conversions': random.randint(25, 35),
                    'calls_made': random.randint(180, 250),
                    'emails_sent': random.randint(350, 450),
                    'avg_response_time': random.randint(8, 15)
                },
                {
                    'name': 'Mike Chen',
                    'conversions': random.randint(20, 30),
                    'calls_made': random.randint(160, 220),
                    'emails_sent': random.randint(320, 420),
                    'avg_response_time': random.randint(10, 18)
                },
                {
                    'name': 'Lisa Rodriguez',
                    'conversions': random.randint(28, 38),
                    'calls_made': random.randint(190, 260),
                    'emails_sent': random.randint(380, 480),
                    'avg_response_time': random.randint(6, 12)
                },
                {
                    'name': 'David Kim',
                    'conversions': random.randint(18, 28),
                    'calls_made': random.randint(150, 210),
                    'emails_sent': random.randint(300, 400),
                    'avg_response_time': random.randint(12, 20)
                },
                {
                    'name': 'Emily Davis',
                    'conversions': random.randint(22, 32),
                    'calls_made': random.randint(170, 230),
                    'emails_sent': random.randint(340, 440),
                    'avg_response_time': random.randint(9, 16)
                }
            ],
            'agents_detailed': self._generate_detailed_agent_data(),
            'campaigns': self._generate_campaign_data(),
            'goals': [
                {
                    'name': 'Monthly Revenue Goal',
                    'current': random.randint(180000, 220000),
                    'target': 250000,
                    'target_date': '2026-01-31'
                },
                {
                    'name': 'Conversion Rate Target',
                    'current': random.uniform(22, 26),
                    'target': 30,
                    'target_date': '2026-01-31'
                },
                {
                    'name': 'Lead Response Time',
                    'current': random.uniform(10, 14),
                    'target': 8,
                    'target_date': '2026-01-31'
                },
                {
                    'name': 'Team Productivity',
                    'current': random.uniform(85, 92),
                    'target': 95,
                    'target_date': '2026-01-31'
                }
            ]
        }

    def _generate_detailed_agent_data(self) -> List[Dict[str, Any]]:
        """Generate detailed agent performance data"""
        import random

        agents = ['Sarah Johnson', 'Mike Chen', 'Lisa Rodriguez', 'David Kim', 'Emily Davis']
        detailed_data = []

        for agent in agents:
            detailed_data.append({
                'name': agent,
                'conversions': random.randint(18, 38),
                'conversions_change': random.randint(-3, 8),
                'calls_made': random.randint(150, 260),
                'calls_change': random.randint(-15, 25),
                'emails_sent': random.randint(300, 480),
                'emails_change': random.randint(-20, 35),
                'avg_response_time': random.randint(6, 20),
                'response_time_change': random.randint(-5, 3),
                'avg_lead_score': random.randint(70, 90),
                'performance_trend': [random.randint(70, 95) for _ in range(30)]
            })

        return detailed_data

    def _generate_campaign_data(self) -> List[Dict[str, Any]]:
        """Generate campaign performance data"""
        import random

        campaigns = [
            'Facebook Lead Gen', 'Google Search Ads', 'LinkedIn Campaign',
            'Email Nurture Sequence', 'Referral Program', 'Website SEO'
        ]

        campaign_data = []
        for campaign in campaigns:
            cost = random.randint(2000, 8000)
            revenue = random.randint(cost * 1.2, cost * 5)
            roi = ((revenue - cost) / cost) * 100

            campaign_data.append({
                'name': campaign,
                'cost': cost,
                'revenue': revenue,
                'roi': roi,
                'conversion_rate': random.uniform(12, 35),
                'status': random.choice(['Active', 'Paused', 'Completed'])
            })

        return campaign_data

    def _generate_performance_trends(self):
        """Generate performance trend data"""
        import random

        dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]

        trends = {
            'revenue': [random.randint(6000, 12000) for _ in range(30)],
            'leads': [random.randint(25, 65) for _ in range(30)],
            'conversion_rate': [random.uniform(15, 30) for _ in range(30)],
            'response_time': [random.randint(8, 25) for _ in range(30)]
        }

        return dates, trends

    def _generate_goal_forecast(self, goals: List[Dict[str, Any]]) -> Dict[str, Dict[str, List]]:
        """Generate goal achievement forecast"""
        import random

        forecast_data = {}

        for goal in goals[:2]:  # First 2 goals for demo
            dates = [datetime.now() + timedelta(days=i) for i in range(-15, 16)]

            # Historical actual data (past 15 days)
            actual = [
                goal['current'] * (0.7 + i * 0.02 + random.uniform(-0.05, 0.05))
                for i in range(15)
            ]

            # Projected data (next 15 days)
            projected = actual + [
                actual[-1] * (1 + 0.03 + random.uniform(-0.01, 0.02))
                for _ in range(16)
            ]

            forecast_data[goal['name']] = {
                'dates': dates,
                'actual': actual,
                'projected': projected
            }

        return forecast_data


def render_performance_dashboard(realtime_service, state_manager):
    """Main function to render the performance dashboard"""
    dashboard = PerformanceDashboard(realtime_service, state_manager)
    dashboard.render()


# Streamlit component integration
if __name__ == "__main__":
    # Demo mode for testing
    st.set_page_config(
        page_title="Performance Dashboard Demo",
        page_icon="⚡",
        layout="wide"
    )

    # Mock services for demo
    class MockRealtimeService:
        def get_recent_events(self, event_type=None, limit=50, since=None):
            return []

    class MockStateManager:
        class UserPreferences:
            auto_refresh = True

        user_preferences = UserPreferences()

    # Render demo
    st.title("⚡ Performance Dashboard Demo")
    render_performance_dashboard(MockRealtimeService(), MockStateManager())