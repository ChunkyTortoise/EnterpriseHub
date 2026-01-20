"""
Analytics Dashboard Component for Customer Intelligence Platform

Interactive analytics dashboard with:
- Customer engagement metrics
- Lead scoring analytics
- Conversion funnel analysis
- Department performance tracking
- Real-time data visualization
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
import asyncio


def render_analytics_css():
    """Inject custom CSS for analytics dashboard"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    /* Analytics Container Styles */
    .analytics-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        color: white;
    }

    .analytics-header {
        text-align: center;
        margin-bottom: 2rem;
        border-bottom: 2px solid rgba(255,255,255,0.1);
        padding-bottom: 1rem;
    }

    .analytics-title {
        font-family: 'Inter', sans-serif;
        font-size: 2.5rem;
        font-weight: 600;
        margin: 0;
        color: #FFFFFF;
    }

    .analytics-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        margin: 0.5rem 0 0 0;
        color: #E8E8F0;
        font-weight: 400;
    }

    .chart-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        color: #333;
    }

    .chart-title {
        font-family: 'Inter', sans-serif;
        font-size: 1.2rem;
        font-weight: 600;
        color: #2D3748;
        margin: 0 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #E2E8F0;
    }

    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
    }

    .metric-card {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
        transition: all 0.3s ease;
    }

    .metric-value {
        font-family: 'Inter', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: #FFFFFF;
        margin: 0.5rem 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .metric-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        color: #E8E8F0;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .metric-change {
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }

    .metric-change.positive { color: #48BB78; }
    .metric-change.negative { color: #F56565; }
    .metric-change.neutral { color: #A0AEC0; }

    .filter-panel {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .drill-down-nav {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #FFFFFF;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    /* Mobile Responsive */
    @media (max-width: 768px) {
        .analytics-container {
            padding: 1rem;
            margin: 0.5rem 0;
        }

        .analytics-title {
            font-size: 1.8rem;
        }

        .chart-container {
            padding: 1rem;
        }

        .metric-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 0.5rem;
        }

        .metric-value {
            font-size: 1.8rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)


class CustomerAnalytics:
    """Customer Intelligence Analytics Dashboard"""

    def __init__(self):
        # Initialize session state
        if 'analytics_state' not in st.session_state:
            st.session_state.analytics_state = {
                'current_view': 'overview',
                'drill_down_path': ['overview'],
                'selected_filters': {
                    'time_range': '30d',
                    'department': 'all',
                    'model_type': 'all'
                }
            }

    def render(self):
        """Render the main analytics dashboard"""
        render_analytics_css()

        st.markdown('<div class="analytics-container">', unsafe_allow_html=True)

        self._render_header()
        self._render_filter_panel()
        self._render_drill_down_nav()

        current_view = st.session_state.analytics_state['current_view']

        if current_view == 'overview':
            self._render_overview_dashboard()
        elif current_view == 'engagement_analysis':
            self._render_engagement_analysis()
        elif current_view == 'scoring_performance':
            self._render_scoring_performance()
        elif current_view == 'department_comparison':
            self._render_department_comparison()
        elif current_view == 'conversion_trends':
            self._render_conversion_trends()

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_header(self):
        """Render dashboard header"""
        st.markdown("""
        <div class="analytics-header">
            <h1 class="analytics-title">📊 Customer Intelligence Analytics</h1>
            <p class="analytics-subtitle">Real-time insights into customer engagement and conversion patterns</p>
        </div>
        """, unsafe_allow_html=True)

    def _render_filter_panel(self):
        """Render filter controls"""
        st.markdown('<div class="filter-panel">', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            time_range = st.selectbox(
                '📅 Time Range',
                ['7d', '30d', '90d', '1y'],
                index=1,
                key='analytics_time_range'
            )
            st.session_state.analytics_state['selected_filters']['time_range'] = time_range

        with col2:
            department = st.selectbox(
                '🏢 Department',
                ['all', 'sales', 'marketing', 'support', 'product'],
                index=0,
                key='analytics_department'
            )
            st.session_state.analytics_state['selected_filters']['department'] = department

        with col3:
            model_type = st.selectbox(
                '🎯 Model Type',
                ['all', 'lead_scoring', 'engagement_prediction', 'churn_prediction'],
                index=0,
                key='analytics_model'
            )
            st.session_state.analytics_state['selected_filters']['model_type'] = model_type

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_drill_down_nav(self):
        """Render breadcrumb navigation"""
        path = st.session_state.analytics_state['drill_down_path']
        if len(path) > 1:
            breadcrumb = ' → '.join([p.replace('_', ' ').title() for p in path])
            st.markdown(f"""
            <div class="drill-down-nav">
                🗂️ <strong>Navigation:</strong> {breadcrumb}
            </div>
            """, unsafe_allow_html=True)

    def _render_overview_dashboard(self):
        """Render main overview dashboard"""
        data = self._get_analytics_data()

        # Key metrics
        self._render_key_metrics(data)

        # Charts grid
        col1, col2 = st.columns(2)

        with col1:
            self._render_engagement_trend_chart(data)

        with col2:
            self._render_conversion_funnel_chart(data)

        col3, col4 = st.columns(2)

        with col3:
            self._render_scoring_distribution_chart(data)

        with col4:
            self._render_department_performance_chart(data)

        # Drill-down options
        self._render_drill_down_options()

    def _render_key_metrics(self, data: Dict[str, Any]):
        """Render key performance metrics"""
        st.markdown('<div class="metric-grid">', unsafe_allow_html=True)

        metrics = [
            {
                'label': 'Total Customers',
                'value': f"{data['total_customers']:,}",
                'change': f"+{data['customer_growth']}%",
                'trend': 'positive' if data['customer_growth'] > 0 else 'negative'
            },
            {
                'label': 'Engagement Rate',
                'value': f"{data['engagement_rate']:.1f}%",
                'change': f"{data['engagement_change']:+.1f}%",
                'trend': 'positive' if data['engagement_change'] > 0 else 'negative'
            },
            {
                'label': 'Conversion Rate',
                'value': f"{data['conversion_rate']:.1f}%",
                'change': f"{data['conversion_change']:+.1f}%",
                'trend': 'positive' if data['conversion_change'] > 0 else 'negative'
            },
            {
                'label': 'Avg Lead Score',
                'value': f"{data['avg_lead_score']:.1f}",
                'change': f"{data['score_change']:+.1f}",
                'trend': 'positive' if data['score_change'] > 0 else 'negative'
            },
            {
                'label': 'Churn Risk',
                'value': f"{data['churn_risk']:.1f}%",
                'change': f"{data['churn_change']:+.1f}%",
                'trend': 'negative' if data['churn_change'] > 0 else 'positive'
            },
            {
                'label': 'Avg Response Time',
                'value': f"{data['avg_response_time']:.0f}min",
                'change': f"{data['response_time_change']:+.0f}min",
                'trend': 'negative' if data['response_time_change'] > 0 else 'positive'
            }
        ]

        for metric in metrics:
            trend_class = metric.get('trend', 'neutral')
            trend_icon = '📈' if trend_class == 'positive' else '📉' if trend_class == 'negative' else '➡️'

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{metric['label']}</div>
                <div class="metric-value">{metric['value']}</div>
                <div class="metric-change {trend_class}">
                    {trend_icon} {metric['change']}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_engagement_trend_chart(self, data: Dict[str, Any]):
        """Render customer engagement trend chart"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">📈 Customer Engagement Trends</h3>', unsafe_allow_html=True)

        dates, engagement_data = self._generate_trend_data(data['time_range'])

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=engagement_data['total_engagement'],
            mode='lines+markers',
            name='Total Engagement',
            line=dict(color='#667eea', width=3),
            marker=dict(size=8, color='#667eea')
        ))

        fig.add_trace(go.Scatter(
            x=dates,
            y=engagement_data['high_engagement'],
            mode='lines+markers',
            name='High Engagement',
            line=dict(color='#f093fb', width=2),
            marker=dict(size=6, color='#f093fb')
        ))

        fig.update_layout(
            height=300,
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig, use_container_width=True)

        if st.button('🔍 Detailed Engagement Analysis', key='drill_engagement', use_container_width=True):
            self._navigate_to_view('engagement_analysis')

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_conversion_funnel_chart(self, data: Dict[str, Any]):
        """Render conversion funnel chart"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">🎯 Conversion Funnel</h3>', unsafe_allow_html=True)

        funnel_data = data['conversion_funnel']

        fig = go.Figure(go.Funnel(
            y=list(funnel_data.keys()),
            x=list(funnel_data.values()),
            textinfo="value+percent initial",
            marker=dict(
                color=['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe'],
                line=dict(width=2, color='rgba(255,255,255,0.2)')
            )
        ))

        fig.update_layout(
            height=300,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig, use_container_width=True)

        if st.button('🔍 Conversion Analysis', key='drill_conversion', use_container_width=True):
            self._navigate_to_view('conversion_trends')

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_scoring_distribution_chart(self, data: Dict[str, Any]):
        """Render lead score distribution chart"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">📊 Lead Score Distribution</h3>', unsafe_allow_html=True)

        score_data = data['score_distribution']

        fig = go.Figure(data=[
            go.Histogram(
                x=score_data,
                nbinsx=20,
                marker=dict(
                    color='#667eea',
                    line=dict(color='white', width=1)
                )
            )
        ])

        fig.update_layout(
            height=300,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig, use_container_width=True)

        if st.button('🔍 Scoring Performance', key='drill_scoring', use_container_width=True):
            self._navigate_to_view('scoring_performance')

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_department_performance_chart(self, data: Dict[str, Any]):
        """Render department performance comparison"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">🏢 Department Performance</h3>', unsafe_allow_html=True)

        dept_data = data['department_performance']
        departments = list(dept_data.keys())
        conversions = [dept_data[dept]['conversions'] for dept in departments]

        fig = go.Figure(data=[
            go.Bar(
                x=departments,
                y=conversions,
                marker=dict(
                    color=['#667eea', '#764ba2', '#f093fb', '#f5576c'],
                    line=dict(color='white', width=1)
                )
            )
        ])

        fig.update_layout(
            height=300,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig, use_container_width=True)

        if st.button('🔍 Department Comparison', key='drill_dept', use_container_width=True):
            self._navigate_to_view('department_comparison')

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_drill_down_options(self):
        """Render drill-down navigation options"""
        st.markdown('### 🎯 Quick Analysis Options')

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button('📈 Engagement Analysis', key='nav_engagement', use_container_width=True):
                self._navigate_to_view('engagement_analysis')

        with col2:
            if st.button('🎯 Scoring Performance', key='nav_scoring', use_container_width=True):
                self._navigate_to_view('scoring_performance')

        with col3:
            if st.button('🏢 Department Comparison', key='nav_departments', use_container_width=True):
                self._navigate_to_view('department_comparison')

        with col4:
            if st.button('📊 Conversion Trends', key='nav_trends', use_container_width=True):
                self._navigate_to_view('conversion_trends')

    def _render_engagement_analysis(self):
        """Render detailed engagement analysis"""
        st.markdown('### 📈 Customer Engagement Deep Dive')

        data = self._get_analytics_data()

        # Engagement metrics over time
        engagement_df = self._generate_engagement_data()

        fig = px.line(
            engagement_df,
            x='date',
            y=['high_engagement', 'medium_engagement', 'low_engagement'],
            title='Engagement Levels Over Time'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Engagement factors
        st.subheader('🔍 Engagement Drivers')
        factors_data = data['engagement_factors']
        factors_df = pd.DataFrame(list(factors_data.items()), columns=['Factor', 'Impact Score'])
        st.dataframe(factors_df.sort_values('Impact Score', ascending=False), use_container_width=True)

    def _render_scoring_performance(self):
        """Render model scoring performance analysis"""
        st.markdown('### 🎯 Model Scoring Performance')

        # Model accuracy comparison
        model_data = {
            'Lead Scoring': {'accuracy': 0.85, 'precision': 0.82, 'recall': 0.78},
            'Engagement Prediction': {'accuracy': 0.79, 'precision': 0.81, 'recall': 0.76},
            'Churn Prediction': {'accuracy': 0.88, 'precision': 0.84, 'recall': 0.83}
        }

        df = pd.DataFrame(model_data).T
        df.index.name = 'Model'

        fig = px.bar(
            df.reset_index(),
            x='Model',
            y=['accuracy', 'precision', 'recall'],
            barmode='group',
            title='Model Performance Comparison'
        )

        st.plotly_chart(fig, use_container_width=True)

        st.subheader('📊 Score Distribution Analysis')
        st.dataframe(df, use_container_width=True)

    def _render_department_comparison(self):
        """Render department comparison analysis"""
        st.markdown('### 🏢 Department Performance Comparison')

        data = self._get_analytics_data()
        dept_detailed = data['department_detailed']

        df = pd.DataFrame(dept_detailed).T
        df.index.name = 'Department'

        # Performance heatmap
        fig = px.imshow(
            df.values,
            x=df.columns,
            y=df.index,
            color_continuous_scale='Blues',
            title='Department Performance Heatmap'
        )

        st.plotly_chart(fig, use_container_width=True)

        st.subheader('📈 Department Rankings')
        st.dataframe(df.sort_values('conversion_rate', ascending=False), use_container_width=True)

    def _render_conversion_trends(self):
        """Render conversion trends analysis"""
        st.markdown('### 📊 Conversion Trends Analysis')

        # Multi-metric trends
        dates, trends_data = self._generate_conversion_trends()

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Conversions', 'Lead Quality', 'Response Time', 'Customer Satisfaction'],
            vertical_spacing=0.08,
            horizontal_spacing=0.08
        )

        fig.add_trace(go.Scatter(x=dates, y=trends_data['conversions'], name='Conversions'), row=1, col=1)
        fig.add_trace(go.Scatter(x=dates, y=trends_data['quality'], name='Quality'), row=1, col=2)
        fig.add_trace(go.Scatter(x=dates, y=trends_data['response_time'], name='Response Time'), row=2, col=1)
        fig.add_trace(go.Scatter(x=dates, y=trends_data['satisfaction'], name='Satisfaction'), row=2, col=2)

        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    def _navigate_to_view(self, view_name: str):
        """Navigate to a specific view"""
        st.session_state.analytics_state['current_view'] = view_name
        if view_name not in st.session_state.analytics_state['drill_down_path']:
            st.session_state.analytics_state['drill_down_path'].append(view_name)
        st.rerun()

    def _get_analytics_data(self) -> Dict[str, Any]:
        """Generate mock analytics data"""
        return {
            'total_customers': np.random.randint(2500, 3500),
            'customer_growth': np.random.randint(-3, 15),
            'engagement_rate': np.random.uniform(65, 85),
            'engagement_change': np.random.uniform(-2, 5),
            'conversion_rate': np.random.uniform(12, 25),
            'conversion_change': np.random.uniform(-3, 6),
            'avg_lead_score': np.random.uniform(0.6, 0.85),
            'score_change': np.random.uniform(-0.05, 0.1),
            'churn_risk': np.random.uniform(5, 15),
            'churn_change': np.random.uniform(-2, 3),
            'avg_response_time': np.random.uniform(15, 45),
            'response_time_change': np.random.uniform(-5, 8),
            'time_range': st.session_state.analytics_state['selected_filters']['time_range'],
            'conversion_funnel': {
                'Visitors': 5000,
                'Leads': 1200,
                'Qualified': 480,
                'Proposals': 180,
                'Customers': 65
            },
            'score_distribution': np.random.beta(2, 2, 1000),
            'department_performance': {
                'Sales': {'conversions': 45, 'engagement': 78},
                'Marketing': {'conversions': 32, 'engagement': 82},
                'Support': {'conversions': 28, 'engagement': 85},
                'Product': {'conversions': 15, 'engagement': 72}
            },
            'department_detailed': {
                'Sales': {'conversion_rate': 15.2, 'engagement_score': 78, 'response_time': 25},
                'Marketing': {'conversion_rate': 12.8, 'engagement_score': 82, 'response_time': 18},
                'Support': {'conversion_rate': 18.5, 'engagement_score': 85, 'response_time': 15},
                'Product': {'conversion_rate': 8.9, 'engagement_score': 72, 'response_time': 35}
            },
            'engagement_factors': {
                'Response Time': 85,
                'Message Quality': 78,
                'Personalization': 72,
                'Follow-up Frequency': 65,
                'Channel Preference': 58
            }
        }

    def _generate_trend_data(self, time_range: str) -> Tuple[List[datetime], Dict[str, List[int]]]:
        """Generate engagement trend data"""
        days = {'7d': 7, '30d': 30, '90d': 90, '1y': 365}[time_range]
        dates = [datetime.now() - timedelta(days=i) for i in range(days, 0, -1)]

        total_engagement = []
        high_engagement = []

        base_total = 150
        base_high = 45

        for i in range(days):
            trend = i * 0.8
            seasonality = 20 * np.sin(2 * np.pi * i / 7)
            noise = np.random.normal(0, 8)

            total = max(0, int(base_total + trend + seasonality + noise))
            high = max(0, int(base_high + trend * 0.4 + seasonality * 0.2 + noise * 0.5))

            total_engagement.append(total)
            high_engagement.append(min(high, total))

        return dates, {
            'total_engagement': total_engagement,
            'high_engagement': high_engagement
        }

    def _generate_engagement_data(self) -> pd.DataFrame:
        """Generate detailed engagement data"""
        dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]

        data = {
            'date': dates,
            'high_engagement': np.random.randint(40, 60, 30),
            'medium_engagement': np.random.randint(80, 120, 30),
            'low_engagement': np.random.randint(20, 40, 30)
        }

        return pd.DataFrame(data)

    def _generate_conversion_trends(self) -> Tuple[List[datetime], Dict[str, List[float]]]:
        """Generate conversion trends data"""
        dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]

        trends_data = {
            'conversions': [np.random.randint(8, 25) for _ in range(30)],
            'quality': [np.random.uniform(0.6, 0.9) for _ in range(30)],
            'response_time': [np.random.uniform(10, 35) for _ in range(30)],
            'satisfaction': [np.random.uniform(4.0, 5.0) for _ in range(30)]
        }

        return dates, trends_data


def render_analytics_dashboard():
    """Main function to render the analytics dashboard"""
    analytics = CustomerAnalytics()
    analytics.render()


if __name__ == '__main__':
    st.set_page_config(
        page_title='Customer Intelligence Analytics',
        page_icon='📊',
        layout='wide'
    )

    st.title('📊 Customer Intelligence Platform - Analytics Demo')
    render_analytics_dashboard()