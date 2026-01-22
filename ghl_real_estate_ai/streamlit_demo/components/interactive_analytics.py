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

# Import Primitive Components
from ghl_real_estate_ai.streamlit_demo.components.primitives import render_obsidian_card, CardConfig, icon, ICONS
from ghl_real_estate_ai.streamlit_demo.plotly_optimizer import plotly_optimizer

class InteractiveAnalytics:
    """Interactive analytics component with drill-down capabilities"""

    def __init__(self, realtime_service, state_manager):
        self.realtime_service = realtime_service
        self.state_manager = state_manager
        if 'analytics_state' not in st.session_state:
            st.session_state.analytics_state = {'current_view': 'overview', 'drill_down_path': ['overview'], 'selected_filters': {'time_range': '30d', 'agent': 'all', 'source': 'all', 'status': 'all'}, 'selected_metric': None}

    def render(self, container_key: str='interactive_analytics'):
        """Render the interactive analytics dashboard"""
        self._render_header()
        
        with st.container():
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

    def _render_header(self):
        """Render analytics header using obsidian card primitive"""
        render_obsidian_card(
            title="INTERACTIVE ANALYTICS",
            content="Real-time business intelligence with multi-dimensional drill-down insights.",
            config=CardConfig(variant='premium', padding='2rem'),
            icon='chart-mixed'
        )

    def _render_filter_panel(self):
        """Render filter controls"""
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            time_range = st.selectbox('📅 Time Range', ['7d', '30d', '90d', '1y'], index=1, key='analytics_time_range')
            st.session_state.analytics_state['selected_filters']['time_range'] = time_range
        with col2:
            agent = st.selectbox('👨‍💼 Agent', ['all', 'Sarah Johnson', 'Mike Chen', 'Lisa Rodriguez', 'David Kim'], index=0, key='analytics_agent')
            st.session_state.analytics_state['selected_filters']['agent'] = agent
        with col3:
            source = st.selectbox('📱 Source', ['all', 'Website', 'Facebook', 'Google Ads', 'Referral', 'Direct'], index=0, key='analytics_source')
            st.session_state.analytics_state['selected_filters']['source'] = source
        with col4:
            status = st.selectbox('🎯 Status', ['all', 'hot', 'warm', 'cold', 'converted', 'lost'], index=0, key='analytics_status')
            st.session_state.analytics_state['selected_filters']['status'] = status

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
        metrics = [
            {'label': 'Total Nodes', 'value': data['total_leads'], 'change': f"+{data['leads_change']}%", 'trend': 'positive', 'icon': 'users'},
            {'label': 'Conversion Rate', 'value': f"{data['conversion_rate']:.1f}%", 'change': f"{data['conversion_change']:+.1f}%", 'trend': 'positive' if data['conversion_change'] > 0 else 'negative', 'icon': 'bullseye'},
            {'label': 'Revenue Pipeline', 'value': f"${data['revenue_pipeline']:,.0f}", 'change': f"+{data['revenue_change']}%", 'trend': 'positive', 'icon': 'dollar-sign'},
            {'label': 'Avg Latency', 'value': f"{data['avg_response_time']}m", 'change': f"{data['response_time_change']:+}m", 'trend': 'negative' if data['response_time_change'] > 0 else 'positive', 'icon': 'clock'},
            {'label': 'Hot Signals', 'value': data['hot_leads'], 'change': f"+{data['hot_leads_change']}", 'trend': 'positive', 'icon': 'fire'},
            {'label': 'Node Velocity', 'value': f"{data['agent_productivity']:.1f}", 'change': f"{data['productivity_change']:+.1f}", 'trend': 'positive', 'icon': 'bolt'}
        ]
        
        cols = st.columns(3)
        for i, metric in enumerate(metrics):
            with cols[i % 3]:
                trend_color = '#10b981' if metric['trend'] == 'positive' else '#ef4444'
                render_obsidian_card(
                    title=metric['label'],
                    content=f"""
                    <div style='font-size: 2rem; font-weight: 700; color: #FFFFFF; margin: 0.5rem 0;'>{metric['value']}</div>
                    <div style='color: {trend_color}; font-size: 0.85rem; font-weight: 600;'>
                        {'↑' if metric['trend'] == 'positive' else '↓'} {metric['change']}
                    </div>
                    """,
                    config=CardConfig(variant='glass', padding='1.5rem'),
                    icon=metric['icon']
                )

    def _render_leads_trend_chart(self, data: Dict[str, Any]):
        """Render leads trend over time - Obsidian Style"""
        st.subheader('📈 NODES DISCOVERY TREND')
        dates, leads_data = self._generate_trend_data(data['time_range'])
        df_trend = pd.DataFrame({
            'Date': dates,
            'Total Nodes': leads_data['total'],
            'Hot Signals': leads_data['hot']
        })

        def create_trend_fig(df):
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['Date'], y=df['Total Nodes'], 
                mode='lines+markers', name='Total Nodes', 
                line=dict(color='#6366F1', width=3), 
                marker=dict(size=8, color='#6366F1', line=dict(color='#FFFFFF', width=1)), 
                hovertemplate='<b>Date:</b> %{x}<br><b>Nodes:</b> %{y}<extra></extra>'
            ))
            fig.add_trace(go.Scatter(
                x=df['Date'], y=df['Hot Signals'], 
                mode='lines+markers', name='Hot Signals', 
                line=dict(color='#ef4444', width=2), 
                marker=dict(size=6, color='#ef4444'), 
                hovertemplate='<b>Date:</b> %{x}<br><b>Hot Signals:</b> %{y}<extra></extra>'
            ))
            return fig

        plotly_optimizer.render_chart(create_trend_fig, df_trend, key="analytics_leads_trend")
        
        st.info('💡 **Tip:** Click on data points to drill down into daily details')
        
        if st.button('🔍 Drill into Time Trends', key='drill_time_trends', use_container_width=True):
            self._navigate_to_view('time_trends')

    def _render_conversion_overview_chart(self, data: Dict[str, Any]):
        """Render conversion funnel overview - Obsidian Style"""
        st.subheader('🎯 CONVERSION TRAJECTORY')
        funnel_data = data['conversion_funnel']
        
        def create_funnel_fig(data_dict):
            fig = go.Figure(go.Funnel(
                y=list(data_dict.keys()), 
                x=list(data_dict.values()), 
                textinfo='value+percent initial', 
                marker=dict(color=['#6366F1', '#8b5cf6', '#f59e0b', '#10b981', '#ef4444'], 
                line=dict(width=1, color='rgba(255,255,255,0.2)')), 
                hovertemplate='<b>Stage:</b> %{y}<br><b>Count:</b> %{x}<extra></extra>'
            ))
            return fig

        plotly_optimizer.render_chart(create_funnel_fig, funnel_data, key="analytics_conversion_funnel")

        col1, col2 = st.columns(2)
        with col1:
            lead_to_qualified = funnel_data['Qualified'] / funnel_data['Leads'] * 100
            st.metric('Lead→Qualified', f'{lead_to_qualified:.1f}%')
        with col2:
            qualified_to_closed = funnel_data['Closed'] / funnel_data['Qualified'] * 100
            st.metric('Qualified→Closed', f'{qualified_to_closed:.1f}%')
            
        if st.button('🔍 Analyze Conversion Details', key='drill_conversion', use_container_width=True):
            self._navigate_to_view('conversion_funnel')

    def _render_source_distribution_chart(self, data: Dict[str, Any]):
        """Render lead source distribution - Obsidian Style"""
        st.subheader('📱 SIGNAL ORIGIN')
        source_data = data['source_distribution']
        
        def create_pie_fig(data_dict):
            fig = go.Figure(data=[go.Pie(
                labels=list(data_dict.keys()), 
                values=list(data_dict.values()), 
                hole=0.6, 
                marker=dict(colors=['#6366F1', '#8b5cf6', '#f59e0b', '#10b981', '#ef4444'], 
                line=dict(color='rgba(255,255,255,0.1)', width=1)), 
                hovertemplate='<b>Source:</b> %{label}<br><b>Count:</b> %{value}<extra></extra>'
            )])
            return fig

        plotly_optimizer.render_chart(create_pie_fig, source_data, key="analytics_source_dist")

    def _render_agent_performance_summary(self, data: Dict[str, Any]):
        """Render agent performance summary - Obsidian Style"""
        st.subheader('👥 AGENT TELEMETRY')
        agent_data = data['agent_performance']
        agents = list(agent_data.keys())
        
        def create_agent_fig(data_dict):
            agents_list = list(data_dict.keys())
            conversions = [data_dict[agent]['conversions'] for agent in agents_list]
            response_times = [data_dict[agent]['avg_response_time'] for agent in agents_list]
            fig = make_subplots(rows=2, cols=1, subplot_titles=['CONVERSIONS', 'LATENCY (MIN)'], vertical_spacing=0.15)
            fig.add_trace(go.Bar(x=agents_list, y=conversions, name='Conversions', marker=dict(color='#10b981')), row=1, col=1)
            fig.add_trace(go.Bar(x=agents_list, y=response_times, name='Latency', marker=dict(color='#6366F1')), row=2, col=1)
            return fig

        plotly_optimizer.render_chart(create_agent_fig, agent_data, key="analytics_agent_summary")

        top_agent = max(agents, key=lambda x: agent_data[x]['conversions'])
        st.info(f"🌟 Top Performer: **{top_agent}** ({agent_data[top_agent]['conversions']} conversions)")
        if st.button('🔍 Detailed Agent Analysis', key='drill_agent', use_container_width=True):
            self._navigate_to_view('agent_performance')

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
        st.subheader('🎯 Detailed Conversion Funnel Analysis')
        data = self._get_analytics_data()
        funnel_data = data['conversion_funnel_detailed']
        
        def create_detailed_funnel(data_dict):
            fig = go.Figure()
            stages = list(data_dict.keys())
            values = list(data_dict.values())
            for i, (stage, value) in enumerate(zip(stages, values)):
                color_intensity = 1 - i * 0.15
                fig.add_trace(go.Funnel(
                    y=[stage], x=[value], 
                    textinfo='value+percent initial', 
                    marker=dict(color=f'rgba(99, 102, 241, {color_intensity})', 
                    line=dict(width=1, color='rgba(255,255,255,0.2)')), 
                    name=stage
                ))
            fig.update_layout(height=500)
            return fig

        plotly_optimizer.render_chart(create_detailed_funnel, funnel_data, key="analytics_funnel_detailed")
        
        st.subheader('📋 Stage-by-Stage Analysis')
        values = list(funnel_data.values())
        stages = list(funnel_data.keys())
        conversion_df = pd.DataFrame([{'Stage': stage, 'Count': value, 'Drop Rate': f'{(values[i - 1] - value) / values[i - 1] * 100:.1f}%' if i > 0 else 'N/A', 'Conversion Rate': f'{value / values[0] * 100:.1f}%'} for i, (stage, value) in enumerate(zip(stages, values))])
        st.dataframe(conversion_df, use_container_width=True)

    def _render_agent_performance(self):
        """Render detailed agent performance analysis"""
        st.subheader('👥 Agent Performance Deep Dive')
        data = self._get_analytics_data()
        agent_data = data['agent_performance_detailed']
        df = pd.DataFrame(agent_data).T
        df = df.reset_index().rename(columns={'index': 'Agent'})
        metrics = ['conversions', 'avg_response_time', 'leads_handled', 'satisfaction_score']
        
        def create_agent_heatmap(df_agents):
            heatmap_data = df_agents[metrics].values
            fig = go.Figure(data=go.Heatmap(
                z=heatmap_data.T, x=df_agents['Agent'], y=metrics, 
                colorscale='Viridis', 
                hovertemplate='<b>Agent:</b> %{x}<br><b>Metric:</b> %{y}<br><b>Value:</b> %{z}<extra></extra>'
            ))
            fig.update_layout(height=400)
            return fig

        plotly_optimizer.render_chart(create_agent_heatmap, df, key="analytics_agent_heatmap")
        
        st.subheader('🏆 Agent Rankings')
        st.dataframe(df.sort_values('conversions', ascending=False), use_container_width=True)

    def _render_source_analysis(self):
        """Render detailed source analysis"""
        st.subheader('📱 Lead Source Performance Analysis')
        data = self._get_analytics_data()
        source_trend = data['source_trend_data']
        
        def create_source_trend(trend_dict):
            fig = go.Figure()
            for source in trend_dict:
                fig.add_trace(go.Scatter(
                    x=trend_dict[source]['dates'], y=trend_dict[source]['values'], 
                    mode='lines+markers', name=source, 
                    hovertemplate=f'<b>Source:</b> {source}<br><b>Date:</b> %{{x}}<br><b>Leads:</b> %{{y}}<extra></extra>'
                ))
            fig.update_layout(height=400, hovermode='x unified')
            return fig

        plotly_optimizer.render_chart(create_source_trend, source_trend, key="analytics_source_trend_detailed")
        
        st.subheader('💰 Source ROI Analysis')
        roi_data = data['source_roi']
        roi_df = pd.DataFrame(roi_data).T
        roi_df = roi_df.reset_index().rename(columns={'index': 'Source'})
        st.dataframe(roi_df.sort_values('roi', ascending=False), use_container_width=True)

    def _render_time_trends(self):
        """Render detailed time trend analysis"""
        st.subheader('📈 Time Trend Analysis')
        data = self._get_analytics_data()
        
        def create_time_series_subplots(data_dict):
            dates = data_dict['time_series']['dates']
            fig = make_subplots(rows=2, cols=2, subplot_titles=['Leads', 'Conversions', 'Response Time', 'Revenue'], vertical_spacing=0.12, horizontal_spacing=0.1)
            fig.add_trace(go.Scatter(x=dates, y=data_dict['time_series']['leads'], name='Leads', line=dict(color='#6366F1')), row=1, col=1)
            fig.add_trace(go.Scatter(x=dates, y=data_dict['time_series']['conversions'], name='Conversions', line=dict(color='#10b981')), row=1, col=2)
            fig.add_trace(go.Scatter(x=dates, y=data_dict['time_series']['response_time'], name='Response Time', line=dict(color='#ef4444')), row=2, col=1)
            fig.add_trace(go.Scatter(x=dates, y=data_dict['time_series']['revenue'], name='Revenue', line=dict(color='#f59e0b')), row=2, col=2)
            fig.update_layout(height=600, showlegend=False)
            return fig

        plotly_optimizer.render_chart(create_time_series_subplots, data, key="analytics_time_trends_detailed")

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