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
    """Inject custom CSS for interactive analytics - Obsidian Command Edition"""
    st.markdown("\n    <style>\n    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;700&display=swap');\n\n    /* Interactive Analytics Styles */\n    .analytics-container {\n        background: rgba(5, 7, 10, 0.8) !important;\n        border-radius: 20px;\n        padding: 2.5rem;\n        margin: 1rem 0;\n        box-shadow: 0 25px 60px rgba(0, 0, 0, 0.9);\n        border: 1px solid rgba(255, 255, 255, 0.05);\n        position: relative;\n        overflow: hidden;\n        backdrop-filter: blur(20px);\n    }\n\n    .analytics-container::before {\n        content: '';\n        position: absolute;\n        top: 0;\n        left: 0;\n        right: 0;\n        bottom: 0;\n        background: radial-gradient(circle at 10% 10%, rgba(99, 102, 241, 0.05) 0%, transparent 50%);\n        pointer-events: none;\n    }\n\n    .analytics-header {\n        color: white;\n        text-align: left;\n        margin-bottom: 3rem;\n        position: relative;\n        z-index: 1;\n        border-bottom: 1px solid rgba(255,255,255,0.05);\n        padding-bottom: 2rem;\n    }\n\n    .analytics-title {\n        font-family: 'Space Grotesk', sans-serif !important;\n        font-size: 3rem;\n        font-weight: 700;\n        margin: 0;\n        color: #FFFFFF;\n        letter-spacing: -0.04em;\n        text-transform: uppercase;\n    }\n\n    .analytics-subtitle {\n        font-family: 'Inter', sans-serif;\n        font-size: 1.1rem;\n        margin: 0.75rem 0 0 0;\n        color: #8B949E;\n        font-weight: 500;\n    }\n\n    .chart-container {\n        background: rgba(22, 27, 34, 0.7) !important;\n        border-radius: 12px;\n        padding: 1.75rem;\n        margin: 1rem 0;\n        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);\n        backdrop-filter: blur(12px);\n        border: 1px solid rgba(255, 255, 255, 0.05);\n        border-top: 1px solid rgba(255, 255, 255, 0.1);\n        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);\n    }\n\n    .chart-container:hover {\n        transform: translateY(-5px);\n        border-color: rgba(99, 102, 241, 0.3);\n        box-shadow: 0 12px 48px rgba(99, 102, 241, 0.2);\n    }\n\n    .chart-title {\n        font-family: 'Space Grotesk', sans-serif !important;\n        font-size: 1.25rem;\n        font-weight: 700;\n        color: #FFFFFF;\n        margin: 0 0 1.5rem 0;\n        padding-bottom: 0.75rem;\n        border-bottom: 1px solid rgba(255,255,255,0.05);\n        text-transform: uppercase;\n        letter-spacing: 0.05em;\n    }\n\n    .metric-grid {\n        display: grid;\n        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));\n        gap: 1.25rem;\n        margin: 2rem 0;\n    }\n\n    .metric-card {\n        background: rgba(22, 27, 34, 0.8);\n        border-radius: 12px;\n        padding: 1.5rem;\n        text-align: left;\n        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);\n        border: 1px solid rgba(255, 255, 255, 0.05);\n        border-left: 4px solid;\n        transition: all 0.3s ease;\n    }\n\n    .metric-card:hover {\n        transform: translateY(-4px);\n        border-color: rgba(255,255,255,0.1);\n        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.6);\n    }\n\n    .metric-card.positive { border-left-color: #10b981; }\n    .metric-card.negative { border-left-color: #ef4444; }\n    .metric-card.neutral { border-left-color: #6366F1; }\n\n    .metric-value {\n        font-family: 'Space Grotesk', sans-serif !important;\n        font-size: 2rem;\n        font-weight: 700;\n        color: #FFFFFF;\n        margin: 0.5rem 0;\n        text-shadow: 0 0 10px rgba(255,255,255,0.1);\n    }\n\n    .metric-label {\n        font-family: 'Space Grotesk', sans-serif !important;\n        font-size: 0.75rem;\n        color: #8B949E;\n        font-weight: 700;\n        text-transform: uppercase;\n        letter-spacing: 0.1em;\n    }\n\n    .metric-change {\n        font-family: 'Inter', sans-serif;\n        font-size: 0.8rem;\n        font-weight: 700;\n        margin-top: 0.5rem;\n        display: flex;\n        align-items: center;\n        gap: 4px;\n    }\n\n    .filter-panel {\n        background: rgba(255, 255, 255, 0.03);\n        border-radius: 12px;\n        padding: 1.5rem;\n        margin-bottom: 2.5rem;\n        backdrop-filter: blur(10px);\n        border: 1px solid rgba(255, 255, 255, 0.05);\n    }\n\n    .drill-down-nav {\n        background: rgba(99, 102, 241, 0.1);\n        border-radius: 8px;\n        padding: 0.85rem 1.25rem;\n        margin: 1rem 0;\n        display: flex;\n        align-items: center;\n        gap: 0.75rem;\n        color: #6366F1;\n        font-weight: 700;\n        font-family: 'Space Grotesk', sans-serif;\n        text-transform: uppercase;\n        letter-spacing: 0.05em;\n        font-size: 0.8rem;\n        border: 1px solid rgba(99, 102, 241, 0.2);\n    }\n\n    .chart-interactive-hint {\n        background: rgba(99, 102, 241, 0.05);\n        border-left: 3px solid #6366F1;\n        padding: 0.75rem 1rem;\n        margin: 1rem 0;\n        border-radius: 0 8px 8px 0;\n        color: #E6EDF3;\n        font-size: 0.85rem;\n        font-family: 'Inter', sans-serif;\n    }\n\n    /* Mobile Responsive */\n    @media (max-width: 768px) {\n        .analytics-container {\n            padding: 1rem;\n            margin: 0.5rem 0;\n        }\n\n        .analytics-title {\n            font-size: 1.5rem;\n        }\n\n        .chart-container {\n            padding: 1rem;\n            margin: 0.5rem 0;\n        }\n\n        .metric-grid {\n            grid-template-columns: repeat(2, 1fr);\n            gap: 0.5rem;\n        }\n\n        .metric-card {\n            padding: 1rem;\n        }\n\n        .metric-value {\n            font-size: 1.8rem;\n        }\n\n        .filter-row {\n            grid-template-columns: 1fr;\n            gap: 0.5rem;\n        }\n    }\n\n    /* Dark mode support */\n    @media (prefers-color-scheme: dark) {\n        .chart-container {\n            background: rgba(44, 62, 80, 0.95);\n            color: white;\n        }\n\n        .chart-title {\n            color: white;\n        }\n\n        .metric-card {\n            background: #34495e;\n            color: white;\n        }\n\n        .metric-value {\n            color: white;\n        }\n    }\n    </style>\n    ", unsafe_allow_html=True)

class InteractiveAnalytics:
    """Interactive analytics component with drill-down capabilities"""

    def __init__(self, realtime_service, state_manager):
        self.realtime_service = realtime_service
        self.state_manager = state_manager
        if 'analytics_state' not in st.session_state:
            st.session_state.analytics_state = {'current_view': 'overview', 'drill_down_path': ['overview'], 'selected_filters': {'time_range': '30d', 'agent': 'all', 'source': 'all', 'status': 'all'}, 'selected_metric': None}

    def render(self, container_key: str='interactive_analytics'):
        """Render the interactive analytics dashboard"""
        render_interactive_analytics_css()
        st.markdown('<div class="analytics-container">', unsafe_allow_html=True)
        self._render_header()
        self._render_filter_panel()
        self._render_drill_down_nav()
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
        st.markdown(f'\n        <div class="analytics-header">\n            <h1 class="analytics-title">📊 Interactive Analytics</h1>\n            <p class="analytics-subtitle">Real-time business intelligence with drill-down insights</p>\n        </div>\n        ', unsafe_allow_html=True)

    def _render_filter_panel(self):
        """Render filter controls"""
        st.markdown('<div class="filter-panel">', unsafe_allow_html=True)
        st.markdown('<div class="filter-row">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            time_range = st.selectbox('📅 Time Range', ['7d', '30d', '90d', '1y'], index=1, key='analytics_time_range')
            st.session_state.analytics_state['selected_filters']['time_range'] = time_range
        with col2:
            agent = st.selectbox('👨\u200d💼 Agent', ['all', 'Sarah Johnson', 'Mike Chen', 'Lisa Rodriguez', 'David Kim'], index=0, key='analytics_agent')
            st.session_state.analytics_state['selected_filters']['agent'] = agent
        with col3:
            source = st.selectbox('📱 Source', ['all', 'Website', 'Facebook', 'Google Ads', 'Referral', 'Direct'], index=0, key='analytics_source')
            st.session_state.analytics_state['selected_filters']['source'] = source
        with col4:
            status = st.selectbox('🎯 Status', ['all', 'hot', 'warm', 'cold', 'converted', 'lost'], index=0, key='analytics_status')
            st.session_state.analytics_state['selected_filters']['status'] = status
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    def _render_drill_down_nav(self):
        """Render drill-down navigation breadcrumb"""
        path = st.session_state.analytics_state['drill_down_path']
        if len(path) > 1:
            breadcrumb = ' → '.join([p.replace('_', ' ').title() for p in path])
            st.markdown(f'\n            <div class="drill-down-nav">\n                🗂️ <strong>Navigation:</strong> {breadcrumb}\n            </div>\n            ', unsafe_allow_html=True)

    def _render_overview_dashboard(self):
        """Render overview dashboard with key metrics"""
        data = self._get_analytics_data()
        self._render_key_metrics(data)
        col1, col2 = st.columns(2)
        with col1:
            self._render_leads_trend_chart(data)
        with col2:
            self._render_conversion_overview_chart(data)
        col3, col4 = st.columns(2)
        with col3:
            self._render_source_distribution_chart(data)
        with col4:
            self._render_agent_performance_summary(data)
        self._render_drill_down_options()

    def _render_key_metrics(self, data: Dict[str, Any]):
        """Render key performance metrics - Obsidian Style"""
        st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
        metrics = [{'label': 'Total Nodes', 'value': data['total_leads'], 'change': f"+{data['leads_change']}%", 'trend': 'positive' if data['leads_change'] > 0 else 'negative'}, {'label': 'Conversion Rate', 'value': f"{data['conversion_rate']:.1f}%", 'change': f"{data['conversion_change']:+.1f}%", 'trend': 'positive' if data['conversion_change'] > 0 else 'negative'}, {'label': 'Revenue Pipeline', 'value': f"${data['revenue_pipeline']:,.0f}", 'change': f"+{data['revenue_change']}%", 'trend': 'positive' if data['revenue_change'] > 0 else 'negative'}, {'label': 'Avg Latency', 'value': f"{data['avg_response_time']}m", 'change': f"{data['response_time_change']:+}m", 'trend': 'negative' if data['response_time_change'] > 0 else 'positive'}, {'label': 'Hot Signals', 'value': data['hot_leads'], 'change': f"+{data['hot_leads_change']}", 'trend': 'positive' if data['hot_leads_change'] > 0 else 'negative'}, {'label': 'Node Velocity', 'value': f"{data['agent_productivity']:.1f}", 'change': f"{data['productivity_change']:+.1f}", 'trend': 'positive' if data['productivity_change'] > 0 else 'negative'}]
        for metric in metrics:
            trend = metric.get('trend', 'neutral')
            trend_icon = '📈' if trend == 'positive' else '📉'
            trend_class = trend
            st.markdown(f"""\n            <div class="metric-card {trend_class}">\n                <div class="metric-label">{metric['label']}</div>\n                <div class="metric-value">{metric['value']}</div>\n                <div class="metric-change {trend_class}">\n                    {trend_icon} {metric['change']}\n                </div>\n            </div>\n            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    def _render_leads_trend_chart(self, data: Dict[str, Any]):
        """Render leads trend over time - Obsidian Style"""
        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">📈 NODES DISCOVERY TREND</h3>', unsafe_allow_html=True)
        dates, leads_data = self._generate_trend_data(data['time_range'])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=leads_data['total'], mode='lines+markers', name='Total Nodes', line=dict(color='#6366F1', width=3), marker=dict(size=8, color='#6366F1', line=dict(color='#FFFFFF', width=1)), hovertemplate='<b>Date:</b> %{x}<br><b>Nodes:</b> %{y}<extra></extra>'))
        fig.add_trace(go.Scatter(x=dates, y=leads_data['hot'], mode='lines+markers', name='Hot Signals', line=dict(color='#ef4444', width=2), marker=dict(size=6, color='#ef4444'), hovertemplate='<b>Date:</b> %{x}<br><b>Hot Signals:</b> %{y}<extra></extra>'))
        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)
        st.markdown('\n        <div class="chart-interactive-hint">\n            💡 <strong>Tip:</strong> Click on data points to drill down into daily details\n        </div>\n        ', unsafe_allow_html=True)
        if st.button('🔍 Drill into Time Trends', key='drill_time_trends', use_container_width=True):
            self._navigate_to_view('time_trends')
        st.markdown('</div>', unsafe_allow_html=True)

    def _render_conversion_overview_chart(self, data: Dict[str, Any]):
        """Render conversion funnel overview - Obsidian Style"""
        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">🎯 CONVERSION TRAJECTORY</h3>', unsafe_allow_html=True)
        funnel_data = data['conversion_funnel']
        fig = go.Figure(go.Funnel(y=list(funnel_data.keys()), x=list(funnel_data.values()), textinfo='value+percent initial', marker=dict(color=['#6366F1', '#8b5cf6', '#f59e0b', '#10b981', '#ef4444'], line=dict(width=1, color='rgba(255,255,255,0.2)')), hovertemplate='<b>Stage:</b> %{y}<br><b>Count:</b> %{x}<extra></extra>'))
        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            lead_to_qualified = funnel_data['Qualified'] / funnel_data['Leads'] * 100
            st.metric('Lead→Qualified', f'{lead_to_qualified:.1f}%')
        with col2:
            qualified_to_closed = funnel_data['Closed'] / funnel_data['Qualified'] * 100
            st.metric('Qualified→Closed', f'{qualified_to_closed:.1f}%')
        if st.button('🔍 Analyze Conversion Details', key='drill_conversion', use_container_width=True):
            self._navigate_to_view('conversion_funnel')
        st.markdown('</div>', unsafe_allow_html=True)

    def _render_source_distribution_chart(self, data: Dict[str, Any]):
        """Render lead source distribution - Obsidian Style"""
        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">📱 SIGNAL ORIGIN</h3>', unsafe_allow_html=True)
        source_data = data['source_distribution']
        fig = go.Figure(data=[go.Pie(labels=list(source_data.keys()), values=list(source_data.values()), hole=0.6, marker=dict(colors=['#6366F1', '#8b5cf6', '#f59e0b', '#10b981', '#ef4444'], line=dict(color='rgba(255,255,255,0.1)', width=1)), hovertemplate='<b>Source:</b> %{label}<br><b>Count:</b> %{value}<extra></extra>')])
        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)

    def _render_agent_performance_summary(self, data: Dict[str, Any]):
        """Render agent performance summary - Obsidian Style"""
        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">👥 AGENT TELEMETRY</h3>', unsafe_allow_html=True)
        agent_data = data['agent_performance']
        agents = list(agent_data.keys())
        conversions = [agent_data[agent]['conversions'] for agent in agents]
        response_times = [agent_data[agent]['avg_response_time'] for agent in agents]
        fig = make_subplots(rows=2, cols=1, subplot_titles=['CONVERSIONS', 'LATENCY (MIN)'], vertical_spacing=0.15)
        fig.add_trace(go.Bar(x=agents, y=conversions, name='Conversions', marker=dict(color='#10b981')), row=1, col=1)
        fig.add_trace(go.Bar(x=agents, y=response_times, name='Latency', marker=dict(color='#6366F1')), row=2, col=1)
        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)
        top_agent = max(agents, key=lambda x: agent_data[x]['conversions'])
        st.info(f"🌟 Top Performer: **{top_agent}** ({agent_data[top_agent]['conversions']} conversions)")
        if st.button('🔍 Detailed Agent Analysis', key='drill_agent', use_container_width=True):
            self._navigate_to_view('agent_performance')
        st.markdown('</div>', unsafe_allow_html=True)

    def _render_drill_down_options(self):
        """Render quick drill-down navigation options"""
        st.markdown('### 🎯 Quick Analysis Options')
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button('📊 Conversion Funnel', key='nav_funnel', use_container_width=True):
                self._navigate_to_view('conversion_funnel')
        with col2:
            if st.button('👥 Agent Performance', key='nav_agents', use_container_width=True):
                self._navigate_to_view('agent_performance')
        with col3:
            if st.button('📱 Source Analysis', key='nav_sources', use_container_width=True):
                self._navigate_to_view('source_analysis')
        with col4:
            if st.button('📈 Time Trends', key='nav_trends', use_container_width=True):
                self._navigate_to_view('time_trends')

    def _render_conversion_funnel(self):
        """Render detailed conversion funnel analysis"""
        st.markdown('### 🎯 Detailed Conversion Funnel Analysis')
        data = self._get_analytics_data()
        funnel_data = data['conversion_funnel_detailed']
        fig = go.Figure()
        stages = list(funnel_data.keys())
        values = list(funnel_data.values())
        for i, (stage, value) in enumerate(zip(stages, values)):
            color_intensity = 1 - i * 0.15
            fig.add_trace(go.Funnel(y=[stage], x=[value], textinfo='value+percent initial', marker=dict(color=f'rgba(52, 152, 219, {color_intensity})', line=dict(width=2, color='white')), name=stage))
        fig.update_layout(height=500, title='Lead Conversion Funnel - Detailed View')
        st.plotly_chart(fig, use_container_width=True)
        st.subheader('📋 Stage-by-Stage Analysis')
        conversion_df = pd.DataFrame([{'Stage': stage, 'Count': value, 'Drop Rate': f'{(values[i - 1] - value) / values[i - 1] * 100:.1f}%' if i > 0 else 'N/A', 'Conversion Rate': f'{value / values[0] * 100:.1f}%'} for i, (stage, value) in enumerate(zip(stages, values))])
        st.dataframe(conversion_df, use_container_width=True)

    def _render_agent_performance(self):
        """Render detailed agent performance analysis"""
        st.markdown('### 👥 Agent Performance Deep Dive')
        data = self._get_analytics_data()
        agent_data = data['agent_performance_detailed']
        df = pd.DataFrame(agent_data).T
        df = df.reset_index().rename(columns={'index': 'Agent'})
        metrics = ['conversions', 'avg_response_time', 'leads_handled', 'satisfaction_score']
        heatmap_data = df[metrics].values
        fig = go.Figure(data=go.Heatmap(z=heatmap_data.T, x=df['Agent'], y=metrics, colorscale='RdYlBu_r', hovertemplate='<b>Agent:</b> %{x}<br><b>Metric:</b> %{y}<br><b>Value:</b> %{z}<extra></extra>'))
        fig.update_layout(title='Agent Performance Heatmap', height=400)
        st.plotly_chart(fig, use_container_width=True)
        st.subheader('🏆 Agent Rankings')
        st.dataframe(df.sort_values('conversions', ascending=False), use_container_width=True)

    def _render_source_analysis(self):
        """Render detailed source analysis"""
        st.markdown('### 📱 Lead Source Performance Analysis')
        data = self._get_analytics_data()
        source_trend = data['source_trend_data']
        fig = go.Figure()
        for source in source_trend:
            fig.add_trace(go.Scatter(x=source_trend[source]['dates'], y=source_trend[source]['values'], mode='lines+markers', name=source, hovertemplate=f'<b>Source:</b> {source}<br><b>Date:</b> %{{x}}<br><b>Leads:</b> %{{y}}<extra></extra>'))
        fig.update_layout(title='Lead Source Trends Over Time', height=400, hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
        st.subheader('💰 Source ROI Analysis')
        roi_data = data['source_roi']
        roi_df = pd.DataFrame(roi_data).T
        roi_df = roi_df.reset_index().rename(columns={'index': 'Source'})
        st.dataframe(roi_df.sort_values('roi', ascending=False), use_container_width=True)

    def _render_time_trends(self):
        """Render detailed time trend analysis"""
        st.markdown('### 📈 Time Trend Analysis')
        data = self._get_analytics_data()
        dates = data['time_series']['dates']
        fig = make_subplots(rows=2, cols=2, subplot_titles=['Leads', 'Conversions', 'Response Time', 'Revenue'], vertical_spacing=0.08, horizontal_spacing=0.08)
        fig.add_trace(go.Scatter(x=dates, y=data['time_series']['leads'], name='Leads', line=dict(color='#3498db')), row=1, col=1)
        fig.add_trace(go.Scatter(x=dates, y=data['time_series']['conversions'], name='Conversions', line=dict(color='#2ecc71')), row=1, col=2)
        fig.add_trace(go.Scatter(x=dates, y=data['time_series']['response_time'], name='Response Time', line=dict(color='#e74c3c')), row=2, col=1)
        fig.add_trace(go.Scatter(x=dates, y=data['time_series']['revenue'], name='Revenue', line=dict(color='#f39c12')), row=2, col=2)
        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    def _navigate_to_view(self, view_name: str):
        """Navigate to a specific view"""
        st.session_state.analytics_state['current_view'] = view_name
        if view_name not in st.session_state.analytics_state['drill_down_path']:
            st.session_state.analytics_state['drill_down_path'].append(view_name)
        st.rerun()

    def _get_analytics_data(self) -> Dict[str, Any]:
        """Get analytics data based on current filters"""
        import random
        return {'total_leads': random.randint(850, 1200), 'leads_change': random.randint(-5, 25), 'conversion_rate': random.uniform(15, 30), 'conversion_change': random.uniform(-3, 5), 'revenue_pipeline': random.randint(800000, 1500000), 'revenue_change': random.randint(-10, 35), 'avg_response_time': random.randint(8, 25), 'response_time_change': random.randint(-5, 8), 'hot_leads': random.randint(45, 85), 'hot_leads_change': random.randint(-8, 15), 'agent_productivity': random.uniform(7.5, 9.2), 'productivity_change': random.uniform(-0.5, 1.2), 'time_range': st.session_state.analytics_state['selected_filters']['time_range'], 'conversion_funnel': {'Leads': 1000, 'Qualified': 450, 'Proposal': 180, 'Negotiation': 85, 'Closed': 32}, 'conversion_funnel_detailed': {'Initial Contact': 1000, 'Responded': 680, 'Qualified': 450, 'Demo Scheduled': 280, 'Proposal Sent': 180, 'Negotiation': 85, 'Closed Won': 32}, 'source_distribution': {'Website': 350, 'Facebook': 280, 'Google Ads': 220, 'Referral': 150, 'Direct': 100}, 'agent_performance': {'Sarah Johnson': {'conversions': 28, 'avg_response_time': 12}, 'Mike Chen': {'conversions': 22, 'avg_response_time': 15}, 'Lisa Rodriguez': {'conversions': 31, 'avg_response_time': 8}, 'David Kim': {'conversions': 19, 'avg_response_time': 18}}, 'agent_performance_detailed': {'Sarah Johnson': {'conversions': 28, 'avg_response_time': 12, 'leads_handled': 180, 'satisfaction_score': 4.7}, 'Mike Chen': {'conversions': 22, 'avg_response_time': 15, 'leads_handled': 165, 'satisfaction_score': 4.4}, 'Lisa Rodriguez': {'conversions': 31, 'avg_response_time': 8, 'leads_handled': 195, 'satisfaction_score': 4.9}, 'David Kim': {'conversions': 19, 'avg_response_time': 18, 'leads_handled': 142, 'satisfaction_score': 4.2}}, 'source_trend_data': self._generate_source_trends(), 'source_roi': {'Website': {'cost': 2500, 'revenue': 85000, 'roi': 3300}, 'Facebook': {'cost': 4200, 'revenue': 72000, 'roi': 1614}, 'Google Ads': {'cost': 6800, 'revenue': 95000, 'roi': 1297}, 'Referral': {'cost': 500, 'revenue': 68000, 'roi': 13500}, 'Direct': {'cost': 0, 'revenue': 45000, 'roi': float('inf')}}, 'time_series': self._generate_time_series()}

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
            trend = i * 0.5
            seasonality = 10 * np.sin(2 * np.pi * i / 7)
            noise = random.gauss(0, 5)
            total = max(0, int(base_total + trend + seasonality + noise))
            hot = max(0, int(base_hot + trend * 0.3 + seasonality * 0.3 + noise * 0.5))
            total_leads.append(total)
            hot_leads.append(min(hot, total))
        return (dates, {'total': total_leads, 'hot': hot_leads})

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
        return {'dates': dates, 'leads': [random.randint(35, 65) for _ in range(30)], 'conversions': [random.randint(3, 12) for _ in range(30)], 'response_time': [random.randint(8, 25) for _ in range(30)], 'revenue': [random.randint(15000, 45000) for _ in range(30)]}

def render_interactive_analytics(realtime_service, state_manager):
    """Main function to render the interactive analytics"""
    analytics = InteractiveAnalytics(realtime_service, state_manager)
    analytics.render()
if __name__ == '__main__':
    st.set_page_config(page_title='Interactive Analytics Demo', page_icon='📊', layout='wide')

    class MockRealtimeService:

        @st.cache_data(ttl=300)
        def get_recent_events(self, event_type=None, limit=50, since=None):
            return []

    class MockStateManager:

        class UserPreferences:
            auto_refresh = True
        user_preferences = UserPreferences()
    st.title('📊 Interactive Analytics Demo')
    render_interactive_analytics(MockRealtimeService(), MockStateManager())