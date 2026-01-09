"""
Interactive Analytics Component for GHL Real Estate AI

Advanced analytics dashboard with:
- Interactive drill-down capabilities
- Real-time data visualization
- Conversion funnel analysis
- Performance trend tracking
- Mobile-responsive charts
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import time
from typing import Dict, List, Any, Optional, Tuple

def render_interactive_analytics_css():
    """Inject custom CSS for interactive analytics"""
    st.markdown("""
    <style>
    /* Interactive Analytics Styles */
    .analytics-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 15px 35px rgba(102, 126, 234, 0.1);
        position: relative;
        overflow: hidden;
    }

    .analytics-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
        pointer-events: none;
    }

    .analytics-header {
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        position: relative;
        z-index: 1;
    }

    .analytics-title {
        font-size: 2rem;
        font-weight: 700;
        margin: 0 0 0.5rem 0;
        background: linear-gradient(45deg, #fff, #e8f4ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .analytics-subtitle {
        font-size: 1rem;
        opacity: 0.9;
        margin: 0;
    }

    .chart-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .chart-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.15);
    }

    .chart-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #2c3e50;
        margin: 0 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e3f2fd;
        position: relative;
    }

    .chart-title::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 50px;
        height: 2px;
        background: linear-gradient(45deg, #667eea, #764ba2);
    }

    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
    }

    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        border-left: 4px solid;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, transparent 0%, rgba(102, 126, 234, 0.05) 100%);
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .metric-card:hover::before {
        opacity: 1;
    }

    .metric-card:hover {
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }

    .metric-card.positive {
        border-left-color: #2ecc71;
    }

    .metric-card.negative {
        border-left-color: #e74c3c;
    }

    .metric-card.neutral {
        border-left-color: #3498db;
    }

    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #2c3e50;
        margin: 0.5rem 0;
        position: relative;
        z-index: 1;
    }

    .metric-label {
        font-size: 0.9rem;
        color: #7f8c8d;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        position: relative;
        z-index: 1;
    }

    .metric-change {
        font-size: 0.8rem;
        font-weight: 600;
        margin-top: 0.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.25rem;
        position: relative;
        z-index: 1;
    }

    .metric-change.positive {
        color: #2ecc71;
    }

    .metric-change.negative {
        color: #e74c3c;
    }

    .filter-panel {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 2rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .filter-row {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        align-items: end;
    }

    .drill-down-nav {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 8px;
        padding: 0.75rem;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: white;
        font-weight: 500;
    }

    .drill-down-nav a {
        color: white;
        text-decoration: none;
        opacity: 0.8;
        transition: opacity 0.2s ease;
    }

    .drill-down-nav a:hover {
        opacity: 1;
        text-decoration: underline;
    }

    .chart-interactive-hint {
        background: rgba(52, 152, 219, 0.1);
        border-left: 3px solid #3498db;
        padding: 0.75rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
        color: #2c3e50;
        font-size: 0.9rem;
    }

    /* Mobile Responsive */
    @media (max-width: 768px) {
        .analytics-container {
            padding: 1rem;
            margin: 0.5rem 0;
        }

        .analytics-title {
            font-size: 1.5rem;
        }

        .chart-container {
            padding: 1rem;
            margin: 0.5rem 0;
        }

        .metric-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 0.5rem;
        }

        .metric-card {
            padding: 1rem;
        }

        .metric-value {
            font-size: 1.8rem;
        }

        .filter-row {
            grid-template-columns: 1fr;
            gap: 0.5rem;
        }
    }

    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .chart-container {
            background: rgba(44, 62, 80, 0.95);
            color: white;
        }

        .chart-title {
            color: white;
        }

        .metric-card {
            background: #34495e;
            color: white;
        }

        .metric-value {
            color: white;
        }
    }
    </style>
    """, unsafe_allow_html=True)

class InteractiveAnalytics:
    """Interactive analytics component with drill-down capabilities"""

    def __init__(self, realtime_service, state_manager):
        self.realtime_service = realtime_service
        self.state_manager = state_manager

        # Analytics state
        if 'analytics_state' not in st.session_state:
            st.session_state.analytics_state = {
                'current_view': 'overview',
                'drill_down_path': ['overview'],
                'selected_filters': {
                    'time_range': '30d',
                    'agent': 'all',
                    'source': 'all',
                    'status': 'all'
                },
                'selected_metric': None
            }

    def render(self, container_key: str = "interactive_analytics"):
        """Render the interactive analytics dashboard"""
        # Inject CSS
        render_interactive_analytics_css()

        # Main container
        st.markdown('<div class="analytics-container">', unsafe_allow_html=True)

        # Header
        self._render_header()

        # Filter panel
        self._render_filter_panel()

        # Drill-down navigation
        self._render_drill_down_nav()

        # Current view content
        current_view = st.session_state.analytics_state['current_view']

        if current_view == 'overview':
            self._render_overview_dashboard()
        elif current_view == 'conversion_funnel':
            self._render_conversion_funnel()
        elif current_view == 'agent_performance':
            self._render_agent_performance()
        elif current_view == 'source_analysis':
            self._render_source_analysis()
        elif current_view == 'time_trends':
            self._render_time_trends()

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_header(self):
        """Render analytics header"""
        st.markdown(f"""
        <div class="analytics-header">
            <h1 class="analytics-title">📊 Interactive Analytics</h1>
            <p class="analytics-subtitle">Real-time business intelligence with drill-down insights</p>
        </div>
        """, unsafe_allow_html=True)

    def _render_filter_panel(self):
        """Render filter controls"""
        st.markdown('<div class="filter-panel">', unsafe_allow_html=True)
        st.markdown('<div class="filter-row">', unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            time_range = st.selectbox(
                "📅 Time Range",
                ["7d", "30d", "90d", "1y"],
                index=1,
                key="analytics_time_range"
            )
            st.session_state.analytics_state['selected_filters']['time_range'] = time_range

        with col2:
            agent = st.selectbox(
                "👨‍💼 Agent",
                ["all", "Sarah Johnson", "Mike Chen", "Lisa Rodriguez", "David Kim"],
                index=0,
                key="analytics_agent"
            )
            st.session_state.analytics_state['selected_filters']['agent'] = agent

        with col3:
            source = st.selectbox(
                "📱 Source",
                ["all", "Website", "Facebook", "Google Ads", "Referral", "Direct"],
                index=0,
                key="analytics_source"
            )
            st.session_state.analytics_state['selected_filters']['source'] = source

        with col4:
            status = st.selectbox(
                "🎯 Status",
                ["all", "hot", "warm", "cold", "converted", "lost"],
                index=0,
                key="analytics_status"
            )
            st.session_state.analytics_state['selected_filters']['status'] = status

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    def _render_drill_down_nav(self):
        """Render drill-down navigation breadcrumb"""
        path = st.session_state.analytics_state['drill_down_path']

        if len(path) > 1:
            breadcrumb = " → ".join([p.replace('_', ' ').title() for p in path])
            st.markdown(f"""
            <div class="drill-down-nav">
                🗂️ <strong>Navigation:</strong> {breadcrumb}
            </div>
            """, unsafe_allow_html=True)

    def _render_overview_dashboard(self):
        """Render overview dashboard with key metrics"""
        # Get analytics data
        data = self._get_analytics_data()

        # Key metrics
        self._render_key_metrics(data)

        # Main charts
        col1, col2 = st.columns(2)

        with col1:
            self._render_leads_trend_chart(data)

        with col2:
            self._render_conversion_overview_chart(data)

        # Secondary charts
        col3, col4 = st.columns(2)

        with col3:
            self._render_source_distribution_chart(data)

        with col4:
            self._render_agent_performance_summary(data)

        # Quick drill-down options
        self._render_drill_down_options()

    def _render_key_metrics(self, data: Dict[str, Any]):
        """Render key performance metrics"""
        st.markdown('<div class="metric-grid">', unsafe_allow_html=True)

        metrics = [
            {
                'label': 'Total Leads',
                'value': data['total_leads'],
                'change': f"+{data['leads_change']}%",
                'trend': 'positive' if data['leads_change'] > 0 else 'negative'
            },
            {
                'label': 'Conversion Rate',
                'value': f"{data['conversion_rate']:.1f}%",
                'change': f"{data['conversion_change']:+.1f}%",
                'trend': 'positive' if data['conversion_change'] > 0 else 'negative'
            },
            {
                'label': 'Revenue Pipeline',
                'value': f"${data['revenue_pipeline']:,.0f}",
                'change': f"+{data['revenue_change']}%",
                'trend': 'positive' if data['revenue_change'] > 0 else 'negative'
            },
            {
                'label': 'Avg Response Time',
                'value': f"{data['avg_response_time']}min",
                'change': f"{data['response_time_change']:+}min",
                'trend': 'negative' if data['response_time_change'] > 0 else 'positive'
            },
            {
                'label': 'Hot Leads',
                'value': data['hot_leads'],
                'change': f"+{data['hot_leads_change']}",
                'trend': 'positive' if data['hot_leads_change'] > 0 else 'negative'
            },
            {
                'label': 'Agent Productivity',
                'value': f"{data['agent_productivity']:.1f}",
                'change': f"{data['productivity_change']:+.1f}",
                'trend': 'positive' if data['productivity_change'] > 0 else 'negative'
            }
        ]

        for metric in metrics:
            trend_icon = "📈" if metric['trend'] == 'positive' else "📉"
            trend_class = metric['trend']

            st.markdown(f"""
            <div class="metric-card {trend_class}">
                <div class="metric-label">{metric['label']}</div>
                <div class="metric-value">{metric['value']}</div>
                <div class="metric-change {trend_class}">
                    {trend_icon} {metric['change']}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_leads_trend_chart(self, data: Dict[str, Any]):
        """Render leads trend over time"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">📈 Leads Trend</h3>', unsafe_allow_html=True)

        # Generate trend data
        dates, leads_data = self._generate_trend_data(data['time_range'])

        fig = go.Figure()

        # Main trend line
        fig.add_trace(go.Scatter(
            x=dates,
            y=leads_data['total'],
            mode='lines+markers',
            name='Total Leads',
            line=dict(color='#3498db', width=3),
            marker=dict(size=6),
            hovertemplate='<b>Date:</b> %{x}<br><b>Total Leads:</b> %{y}<extra></extra>'
        ))

        # Hot leads overlay
        fig.add_trace(go.Scatter(
            x=dates,
            y=leads_data['hot'],
            mode='lines+markers',
            name='Hot Leads',
            line=dict(color='#e74c3c', width=2),
            marker=dict(size=4),
            hovertemplate='<b>Date:</b> %{x}<br><b>Hot Leads:</b> %{y}<extra></extra>'
        ))

        fig.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=20, b=0),
            hovermode='x unified',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Interactive hint
        st.markdown("""
        <div class="chart-interactive-hint">
            💡 <strong>Tip:</strong> Click on data points to drill down into daily details
        </div>
        """, unsafe_allow_html=True)

        # Drill-down button
        if st.button("🔍 Drill into Time Trends", key="drill_time_trends", use_container_width=True):
            self._navigate_to_view('time_trends')

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_conversion_overview_chart(self, data: Dict[str, Any]):
        """Render conversion funnel overview"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">🎯 Conversion Funnel</h3>', unsafe_allow_html=True)

        # Funnel data
        funnel_data = data['conversion_funnel']

        fig = go.Figure(go.Funnel(
            y=list(funnel_data.keys()),
            x=list(funnel_data.values()),
            textinfo="value+percent initial",
            marker=dict(
                color=['#3498db', '#e67e22', '#f39c12', '#2ecc71', '#e74c3c'],
                line=dict(width=2, color='white')
            ),
            hovertemplate='<b>Stage:</b> %{y}<br><b>Count:</b> %{x}<br><b>Rate:</b> %{percentInitial}<extra></extra>'
        ))

        fig.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=20, b=0)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Conversion rates
        col1, col2 = st.columns(2)

        with col1:
            lead_to_qualified = (funnel_data['Qualified'] / funnel_data['Leads']) * 100
            st.metric("Lead→Qualified", f"{lead_to_qualified:.1f}%")

        with col2:
            qualified_to_closed = (funnel_data['Closed'] / funnel_data['Qualified']) * 100
            st.metric("Qualified→Closed", f"{qualified_to_closed:.1f}%")

        # Drill-down button
        if st.button("🔍 Analyze Conversion Details", key="drill_conversion", use_container_width=True):
            self._navigate_to_view('conversion_funnel')

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_source_distribution_chart(self, data: Dict[str, Any]):
        """Render lead source distribution"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">📱 Lead Sources</h3>', unsafe_allow_html=True)

        source_data = data['source_distribution']

        fig = go.Figure(data=[go.Pie(
            labels=list(source_data.keys()),
            values=list(source_data.values()),
            hole=0.4,
            marker=dict(
                colors=['#3498db', '#e74c3c', '#f39c12', '#2ecc71', '#9b59b6'],
                line=dict(color='white', width=2)
            ),
            hovertemplate='<b>Source:</b> %{label}<br><b>Leads:</b> %{value}<br><b>Percentage:</b> %{percent}<extra></extra>'
        )])

        fig.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=20, b=0),
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Top performing source
        top_source = max(source_data, key=source_data.get)
        st.success(f"🏆 Top Source: **{top_source}** ({source_data[top_source]} leads)")

        # Drill-down button
        if st.button("🔍 Source Performance Analysis", key="drill_source", use_container_width=True):
            self._navigate_to_view('source_analysis')

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_agent_performance_summary(self, data: Dict[str, Any]):
        """Render agent performance summary"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">👥 Agent Performance</h3>', unsafe_allow_html=True)

        agent_data = data['agent_performance']

        agents = list(agent_data.keys())
        conversions = [agent_data[agent]['conversions'] for agent in agents]
        response_times = [agent_data[agent]['avg_response_time'] for agent in agents]

        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=['Conversions', 'Avg Response Time (min)'],
            vertical_spacing=0.1
        )

        # Conversions bar chart
        fig.add_trace(
            go.Bar(
                x=agents,
                y=conversions,
                name='Conversions',
                marker=dict(color='#2ecc71'),
                hovertemplate='<b>Agent:</b> %{x}<br><b>Conversions:</b> %{y}<extra></extra>'
            ),
            row=1, col=1
        )

        # Response time bar chart
        fig.add_trace(
            go.Bar(
                x=agents,
                y=response_times,
                name='Response Time',
                marker=dict(color='#3498db'),
                hovertemplate='<b>Agent:</b> %{x}<br><b>Response Time:</b> %{y} min<extra></extra>'
            ),
            row=2, col=1
        )

        fig.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=40, b=0),
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

        # Top performer
        top_agent = max(agents, key=lambda x: agent_data[x]['conversions'])
        st.info(f"🌟 Top Performer: **{top_agent}** ({agent_data[top_agent]['conversions']} conversions)")

        # Drill-down button
        if st.button("🔍 Detailed Agent Analysis", key="drill_agent", use_container_width=True):
            self._navigate_to_view('agent_performance')

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_drill_down_options(self):
        """Render quick drill-down navigation options"""
        st.markdown("### 🎯 Quick Analysis Options")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("📊 Conversion Funnel", key="nav_funnel", use_container_width=True):
                self._navigate_to_view('conversion_funnel')

        with col2:
            if st.button("👥 Agent Performance", key="nav_agents", use_container_width=True):
                self._navigate_to_view('agent_performance')

        with col3:
            if st.button("📱 Source Analysis", key="nav_sources", use_container_width=True):
                self._navigate_to_view('source_analysis')

        with col4:
            if st.button("📈 Time Trends", key="nav_trends", use_container_width=True):
                self._navigate_to_view('time_trends')

    def _render_conversion_funnel(self):
        """Render detailed conversion funnel analysis"""
        st.markdown("### 🎯 Detailed Conversion Funnel Analysis")

        data = self._get_analytics_data()
        funnel_data = data['conversion_funnel_detailed']

        # Enhanced funnel visualization
        fig = go.Figure()

        stages = list(funnel_data.keys())
        values = list(funnel_data.values())

        for i, (stage, value) in enumerate(zip(stages, values)):
            color_intensity = 1 - (i * 0.15)
            fig.add_trace(go.Funnel(
                y=[stage],
                x=[value],
                textinfo="value+percent initial",
                marker=dict(
                    color=f'rgba(52, 152, 219, {color_intensity})',
                    line=dict(width=2, color='white')
                ),
                name=stage
            ))

        fig.update_layout(
            height=500,
            title="Lead Conversion Funnel - Detailed View"
        )

        st.plotly_chart(fig, use_container_width=True)

        # Conversion rates table
        st.subheader("📋 Stage-by-Stage Analysis")

        conversion_df = pd.DataFrame([
            {
                'Stage': stage,
                'Count': value,
                'Drop Rate': f"{((values[i-1] - value) / values[i-1] * 100):.1f}%" if i > 0 else "N/A",
                'Conversion Rate': f"{(value / values[0] * 100):.1f}%"
            }
            for i, (stage, value) in enumerate(zip(stages, values))
        ])

        st.dataframe(conversion_df, use_container_width=True)

    def _render_agent_performance(self):
        """Render detailed agent performance analysis"""
        st.markdown("### 👥 Agent Performance Deep Dive")

        data = self._get_analytics_data()
        agent_data = data['agent_performance_detailed']

        # Create comprehensive agent comparison
        df = pd.DataFrame(agent_data).T
        df = df.reset_index().rename(columns={'index': 'Agent'})

        # Agent performance heatmap
        metrics = ['conversions', 'avg_response_time', 'leads_handled', 'satisfaction_score']
        heatmap_data = df[metrics].values

        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.T,
            x=df['Agent'],
            y=metrics,
            colorscale='RdYlBu_r',
            hovertemplate='<b>Agent:</b> %{x}<br><b>Metric:</b> %{y}<br><b>Value:</b> %{z}<extra></extra>'
        ))

        fig.update_layout(
            title="Agent Performance Heatmap",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        # Agent ranking table
        st.subheader("🏆 Agent Rankings")
        st.dataframe(df.sort_values('conversions', ascending=False), use_container_width=True)

    def _render_source_analysis(self):
        """Render detailed source analysis"""
        st.markdown("### 📱 Lead Source Performance Analysis")

        data = self._get_analytics_data()

        # Source performance over time
        source_trend = data['source_trend_data']

        fig = go.Figure()

        for source in source_trend:
            fig.add_trace(go.Scatter(
                x=source_trend[source]['dates'],
                y=source_trend[source]['values'],
                mode='lines+markers',
                name=source,
                hovertemplate=f'<b>Source:</b> {source}<br><b>Date:</b> %{{x}}<br><b>Leads:</b> %{{y}}<extra></extra>'
            ))

        fig.update_layout(
            title="Lead Source Trends Over Time",
            height=400,
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Source ROI analysis
        st.subheader("💰 Source ROI Analysis")

        roi_data = data['source_roi']
        roi_df = pd.DataFrame(roi_data).T
        roi_df = roi_df.reset_index().rename(columns={'index': 'Source'})

        st.dataframe(roi_df.sort_values('roi', ascending=False), use_container_width=True)

    def _render_time_trends(self):
        """Render detailed time trend analysis"""
        st.markdown("### 📈 Time Trend Analysis")

        data = self._get_analytics_data()

        # Multi-metric time series
        dates = data['time_series']['dates']

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Leads', 'Conversions', 'Response Time', 'Revenue'],
            vertical_spacing=0.08,
            horizontal_spacing=0.08
        )

        # Leads
        fig.add_trace(
            go.Scatter(x=dates, y=data['time_series']['leads'], name='Leads', line=dict(color='#3498db')),
            row=1, col=1
        )

        # Conversions
        fig.add_trace(
            go.Scatter(x=dates, y=data['time_series']['conversions'], name='Conversions', line=dict(color='#2ecc71')),
            row=1, col=2
        )

        # Response Time
        fig.add_trace(
            go.Scatter(x=dates, y=data['time_series']['response_time'], name='Response Time', line=dict(color='#e74c3c')),
            row=2, col=1
        )

        # Revenue
        fig.add_trace(
            go.Scatter(x=dates, y=data['time_series']['revenue'], name='Revenue', line=dict(color='#f39c12')),
            row=2, col=2
        )

        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    def _navigate_to_view(self, view_name: str):
        """Navigate to a specific view"""
        st.session_state.analytics_state['current_view'] = view_name

        # Update drill-down path
        if view_name not in st.session_state.analytics_state['drill_down_path']:
            st.session_state.analytics_state['drill_down_path'].append(view_name)

        st.rerun()

    def _get_analytics_data(self) -> Dict[str, Any]:
        """Get analytics data based on current filters"""
        # In production, this would query real data based on filters
        # For demo, return simulated data

        import random

        return {
            'total_leads': random.randint(850, 1200),
            'leads_change': random.randint(-5, 25),
            'conversion_rate': random.uniform(15, 30),
            'conversion_change': random.uniform(-3, 5),
            'revenue_pipeline': random.randint(800000, 1500000),
            'revenue_change': random.randint(-10, 35),
            'avg_response_time': random.randint(8, 25),
            'response_time_change': random.randint(-5, 8),
            'hot_leads': random.randint(45, 85),
            'hot_leads_change': random.randint(-8, 15),
            'agent_productivity': random.uniform(7.5, 9.2),
            'productivity_change': random.uniform(-0.5, 1.2),
            'time_range': st.session_state.analytics_state['selected_filters']['time_range'],
            'conversion_funnel': {
                'Leads': 1000,
                'Qualified': 450,
                'Proposal': 180,
                'Negotiation': 85,
                'Closed': 32
            },
            'conversion_funnel_detailed': {
                'Initial Contact': 1000,
                'Responded': 680,
                'Qualified': 450,
                'Demo Scheduled': 280,
                'Proposal Sent': 180,
                'Negotiation': 85,
                'Closed Won': 32
            },
            'source_distribution': {
                'Website': 350,
                'Facebook': 280,
                'Google Ads': 220,
                'Referral': 150,
                'Direct': 100
            },
            'agent_performance': {
                'Sarah Johnson': {'conversions': 28, 'avg_response_time': 12},
                'Mike Chen': {'conversions': 22, 'avg_response_time': 15},
                'Lisa Rodriguez': {'conversions': 31, 'avg_response_time': 8},
                'David Kim': {'conversions': 19, 'avg_response_time': 18}
            },
            'agent_performance_detailed': {
                'Sarah Johnson': {
                    'conversions': 28,
                    'avg_response_time': 12,
                    'leads_handled': 180,
                    'satisfaction_score': 4.7
                },
                'Mike Chen': {
                    'conversions': 22,
                    'avg_response_time': 15,
                    'leads_handled': 165,
                    'satisfaction_score': 4.4
                },
                'Lisa Rodriguez': {
                    'conversions': 31,
                    'avg_response_time': 8,
                    'leads_handled': 195,
                    'satisfaction_score': 4.9
                },
                'David Kim': {
                    'conversions': 19,
                    'avg_response_time': 18,
                    'leads_handled': 142,
                    'satisfaction_score': 4.2
                }
            },
            'source_trend_data': self._generate_source_trends(),
            'source_roi': {
                'Website': {'cost': 2500, 'revenue': 85000, 'roi': 3300},
                'Facebook': {'cost': 4200, 'revenue': 72000, 'roi': 1614},
                'Google Ads': {'cost': 6800, 'revenue': 95000, 'roi': 1297},
                'Referral': {'cost': 500, 'revenue': 68000, 'roi': 13500},
                'Direct': {'cost': 0, 'revenue': 45000, 'roi': float('inf')}
            },
            'time_series': self._generate_time_series()
        }

    def _generate_trend_data(self, time_range: str) -> Tuple[List[datetime], Dict[str, List[int]]]:
        """Generate realistic trend data"""
        import random

        days = {'7d': 7, '30d': 30, '90d': 90, '1y': 365}[time_range]
        dates = [datetime.now() - timedelta(days=i) for i in range(days, 0, -1)]

        total_leads = []
        hot_leads = []

        base_total = 45
        base_hot = 12

        for i in range(days):
            # Add some trend and seasonality
            trend = i * 0.5
            seasonality = 10 * np.sin(2 * np.pi * i / 7)  # Weekly pattern
            noise = random.gauss(0, 5)

            total = max(0, int(base_total + trend + seasonality + noise))
            hot = max(0, int(base_hot + trend * 0.3 + seasonality * 0.3 + noise * 0.5))

            total_leads.append(total)
            hot_leads.append(min(hot, total))

        return dates, {'total': total_leads, 'hot': hot_leads}

    def _generate_source_trends(self) -> Dict[str, Dict[str, List]]:
        """Generate source trend data"""
        import random

        sources = ['Website', 'Facebook', 'Google Ads', 'Referral', 'Direct']
        dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]

        trend_data = {}
        for source in sources:
            values = [random.randint(5, 25) for _ in range(30)]
            trend_data[source] = {'dates': dates, 'values': values}

        return trend_data

    def _generate_time_series(self) -> Dict[str, List]:
        """Generate time series data for multiple metrics"""
        import random

        dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]

        return {
            'dates': dates,
            'leads': [random.randint(35, 65) for _ in range(30)],
            'conversions': [random.randint(3, 12) for _ in range(30)],
            'response_time': [random.randint(8, 25) for _ in range(30)],
            'revenue': [random.randint(15000, 45000) for _ in range(30)]
        }


def render_interactive_analytics(realtime_service, state_manager):
    """Main function to render the interactive analytics"""
    analytics = InteractiveAnalytics(realtime_service, state_manager)
    analytics.render()


# Streamlit component integration
if __name__ == "__main__":
    # Demo mode for testing
    st.set_page_config(
        page_title="Interactive Analytics Demo",
        page_icon="📊",
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
    st.title("📊 Interactive Analytics Demo")
    render_interactive_analytics(MockRealtimeService(), MockStateManager())