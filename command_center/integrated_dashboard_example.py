"""
Integrated Dashboard Example - Command Center Components

Demonstrates complete integration of:
- Predictive Insights Dashboard (350+ lines)
- Global Filters for consistent filtering
- Theme Manager for enterprise styling
- Jorge's business rules and 6% commission rate
- ML Analytics Engine integration

This example shows how all components work together to create
a comprehensive enterprise dashboard experience.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add components to path
sys.path.insert(0, str(Path(__file__).parent))

from components.predictive_insights import PredictiveInsightsDashboard
from components.global_filters import create_global_filters
from components.theme_manager import apply_enterprise_theme

def main():
    """Main dashboard application"""
    
    # Configure page
    st.set_page_config(
        page_title="Jorge's Predictive Command Center",
        page_icon="🔮",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply enterprise theme
    theme = apply_enterprise_theme()
    
    # Main header
    theme.render_header(
        title="Predictive Intelligence Command Center",
        subtitle="Advanced ML-powered forecasting and business intelligence for Jorge's Real Estate AI",
        icon="🔮"
    )
    
    # Global filters in sidebar
    filters = create_global_filters("command_center")
    
    with st.sidebar:
        st.markdown("### 🔧 Dashboard Controls")
        st.markdown("---")
        
        # Filter controls
        filter_values = filters.render_filters(layout="sidebar")
        
        st.markdown("---")
        
        # Dashboard options
        st.markdown("### ⚙️ Dashboard Options")
        
        # Forecast horizons
        forecast_horizons = st.multiselect(
            "📊 Forecast Horizons (days)",
            options=[7, 14, 30, 60, 90],
            default=[30, 60, 90],
            help="Select forecasting time horizons"
        )
        
        # Alert sensitivity
        alert_sensitivity = st.selectbox(
            "🚨 Alert Sensitivity",
            options=["Low", "Medium", "High"],
            index=1,
            help="Sensitivity for anomaly detection"
        )
        
        # Commission rate display
        st.markdown("### 💰 Commission Settings")
        st.metric(
            "Jorge's Commission Rate",
            "6.0%",
            help="Standard commission rate for calculations"
        )
        
        # Refresh data
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Main dashboard content
    with st.container():
        # Key performance indicators
        render_kpi_summary(filter_values, theme)
        
        # Predictive insights dashboard
        st.markdown("---")
        dashboard = PredictiveInsightsDashboard()
        dashboard.render("main_dashboard")
        
        # Additional analytics section
        st.markdown("---")
        render_additional_analytics(filter_values, theme)

def render_kpi_summary(filter_values, theme):
    """Render key performance indicators summary"""
    
    st.markdown("### 📊 Executive Summary")
    
    # Generate sample KPI data
    kpi_data = generate_sample_kpis(filter_values)
    
    # Display KPIs in grid
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(theme.render_metric_card(
            "Monthly Revenue",
            f"${kpi_data['revenue']:,.0f}",
            f"{kpi_data['revenue_change']:+.1f}%",
            "positive" if kpi_data['revenue_change'] > 0 else "negative",
            "💰"
        ), unsafe_allow_html=True)
    
    with col2:
        commission = kpi_data['revenue'] * 0.06  # Jorge's 6% rate
        st.markdown(theme.render_metric_card(
            "Commission Earned",
            f"${commission:,.0f}",
            f"{kpi_data['revenue_change']:+.1f}%",
            "positive" if kpi_data['revenue_change'] > 0 else "negative",
            "🏆"
        ), unsafe_allow_html=True)
    
    with col3:
        st.markdown(theme.render_metric_card(
            "Conversion Rate",
            f"{kpi_data['conversion_rate']:.1f}%",
            f"{kpi_data['conversion_change']:+.1f}%",
            "positive" if kpi_data['conversion_change'] > 0 else "negative",
            "🎯"
        ), unsafe_allow_html=True)
    
    with col4:
        st.markdown(theme.render_metric_card(
            "Lead Quality Score",
            f"{kpi_data['quality_score']:.0f}",
            f"{kpi_data['quality_change']:+.1f}%",
            "positive" if kpi_data['quality_change'] > 0 else "negative",
            "⭐"
        ), unsafe_allow_html=True)
    
    # Show filter impact
    if filter_values:
        show_filter_impact(filter_values, theme)

def show_filter_impact(filter_values, theme):
    """Show impact of current filters"""
    
    # Calculate filter impact
    active_filters = []
    
    if filter_values.get('lead_source') and len(filter_values['lead_source']) < 6:
        active_filters.append(f"Sources: {', '.join(filter_values['lead_source'][:3])}")
    
    if filter_values.get('quality_range'):
        if isinstance(filter_values['quality_range'], tuple):
            min_q, max_q = filter_values['quality_range']
            if min_q > 0 or max_q < 100:
                active_filters.append(f"Quality: {min_q}-{max_q}")
        else:
            active_filters.append(f"Min Quality: {filter_values['quality_range']}")
    
    if filter_values.get('geographic') and filter_values['geographic'] != 'All Regions':
        active_filters.append(f"Region: {filter_values['geographic']}")
    
    if active_filters:
        filter_text = " • ".join(active_filters)
        theme.render_alert(
            f"Active Filters: {filter_text}",
            "info",
            "Filter Status",
            "🔍"
        )

def render_additional_analytics(filter_values, theme):
    """Render additional analytics section"""
    
    st.markdown("### 📈 Advanced Analytics")
    
    # Create tabs for different analytics
    tab1, tab2, tab3 = st.tabs(["🔄 Real-time Metrics", "📊 Trend Analysis", "⚡ Performance Insights"])
    
    with tab1:
        render_realtime_metrics(theme)
    
    with tab2:
        render_trend_analysis(theme)
    
    with tab3:
        render_performance_insights(theme)

def render_realtime_metrics(theme):
    """Render real-time metrics"""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    # Generate real-time data
    realtime_data = generate_realtime_data()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(theme.create_chart_container("Live Lead Volume", "📊"), unsafe_allow_html=True)
        
        # Live lead volume chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=realtime_data['times'],
            y=realtime_data['lead_volume'],
            mode='lines+markers',
            name='Lead Volume',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=8)
        ))
        
        styled_fig = theme.style_plotly_chart(fig, height=300)
        st.plotly_chart(styled_fig, use_container_width=True)
        st.markdown(theme.close_chart_container(), unsafe_allow_html=True)
    
    with col2:
        st.markdown(theme.create_chart_container("Quality Distribution", "⭐"), unsafe_allow_html=True)
        
        # Quality distribution
        quality_data = np.random.beta(2, 1.2, 1000) * 100
        fig = go.Figure(data=go.Histogram(
            x=quality_data,
            nbinsx=20,
            marker_color='rgba(16, 185, 129, 0.7)',
            marker_line_color='#10b981',
            marker_line_width=2
        ))
        
        styled_fig = theme.style_plotly_chart(fig, height=300)
        st.plotly_chart(styled_fig, use_container_width=True)
        st.markdown(theme.close_chart_container(), unsafe_allow_html=True)

def render_trend_analysis(theme):
    """Render trend analysis"""
    import plotly.express as px
    
    # Generate trend data
    trend_data = generate_trend_data()
    
    st.markdown(theme.create_chart_container("Multi-Metric Trend Analysis", "📈"), unsafe_allow_html=True)
    
    # Multi-line trend chart
    fig = go.Figure()
    
    # Add multiple trend lines
    metrics = ['conversion_rate', 'lead_quality', 'deal_velocity', 'commission_rate']
    colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6']
    
    for metric, color in zip(metrics, colors):
        fig.add_trace(go.Scatter(
            x=trend_data['dates'],
            y=trend_data[metric],
            mode='lines',
            name=metric.replace('_', ' ').title(),
            line=dict(color=color, width=3)
        ))
    
    styled_fig = theme.style_plotly_chart(fig, height=400)
    st.plotly_chart(styled_fig, use_container_width=True)
    st.markdown(theme.close_chart_container(), unsafe_allow_html=True)

def render_performance_insights(theme):
    """Render performance insights"""
    
    # Performance insights grid
    insights = [
        {
            'title': 'Peak Performance Window',
            'value': 'Tuesday 2-4 PM',
            'description': '23% higher conversion rates during this time window',
            'impact': 'High',
            'recommendation': 'Increase ad spend allocation during peak hours'
        },
        {
            'title': 'Top Converting Source',
            'value': 'Google Ads',
            'description': '15.7% conversion rate, 35% of total volume',
            'impact': 'High', 
            'recommendation': 'Optimize keyword targeting and budget allocation'
        },
        {
            'title': 'Quality Improvement Opportunity', 
            'value': 'Facebook Leads',
            'description': '12% below average quality score',
            'impact': 'Medium',
            'recommendation': 'Refine audience targeting and ad creative'
        },
        {
            'title': 'Commission Optimization',
            'value': '+$12K Monthly',
            'description': 'Potential revenue increase through lead routing optimization',
            'impact': 'High',
            'recommendation': 'Implement intelligent lead distribution system'
        }
    ]
    
    col1, col2 = st.columns(2)
    
    for i, insight in enumerate(insights):
        col = col1 if i % 2 == 0 else col2
        
        with col:
            impact_color = {
                'High': '#ef4444',
                'Medium': '#f59e0b', 
                'Low': '#10b981'
            }.get(insight['impact'], '#3b82f6')
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(147, 51, 234, 0.1));
                border: 1px solid rgba(59, 130, 246, 0.2);
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1rem 0;
                backdrop-filter: blur(10px);
            ">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
                    <h4 style="margin: 0; color: white; font-weight: 600;">{insight['title']}</h4>
                    <span style="
                        background: {impact_color};
                        color: white;
                        padding: 0.25rem 0.75rem;
                        border-radius: 4px;
                        font-size: 0.75rem;
                        font-weight: 600;
                    ">{insight['impact']}</span>
                </div>
                <div style="font-family: 'Space Mono', monospace; font-size: 1.5rem; font-weight: 700; color: #3b82f6; margin: 0.5rem 0;">
                    {insight['value']}
                </div>
                <p style="margin: 0.5rem 0; color: #cbd5e1; font-size: 0.9rem;">
                    {insight['description']}
                </p>
                <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(148, 163, 184, 0.2);">
                    <strong style="color: #10b981;">💡 Recommendation:</strong>
                    <span style="color: #cbd5e1; font-size: 0.85rem;">{insight['recommendation']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

def generate_sample_kpis(filter_values):
    """Generate sample KPI data based on filters"""
    np.random.seed(42)  # For consistent results
    
    base_revenue = 450000
    base_conversion = 12.5
    base_quality = 82
    
    # Adjust based on filters (simulate filter impact)
    if filter_values:
        # Lead source impact
        if filter_values.get('lead_source'):
            source_count = len(filter_values['lead_source'])
            if source_count < 3:
                base_conversion *= 1.1  # Fewer sources = higher quality
            
        # Quality filter impact
        if filter_values.get('quality_range'):
            if isinstance(filter_values['quality_range'], tuple):
                min_q, _ = filter_values['quality_range']
                if min_q > 70:
                    base_conversion *= 1.15
    
    return {
        'revenue': base_revenue + np.random.normal(0, 50000),
        'revenue_change': np.random.uniform(-5, 15),
        'conversion_rate': base_conversion + np.random.normal(0, 1),
        'conversion_change': np.random.uniform(-2, 5),
        'quality_score': base_quality + np.random.normal(0, 3),
        'quality_change': np.random.uniform(-3, 8)
    }

def generate_realtime_data():
    """Generate sample real-time data"""
    np.random.seed(42)
    
    # Last 24 hours in hourly increments
    now = datetime.now()
    times = [now - timedelta(hours=i) for i in range(24, 0, -1)]
    
    # Generate realistic lead volume pattern
    base_volume = 15
    hourly_pattern = np.array([
        8, 6, 4, 3, 4, 6, 12, 20, 25, 28, 30, 32,
        35, 33, 31, 28, 25, 22, 20, 18, 15, 12, 10, 9
    ])
    
    lead_volume = hourly_pattern + np.random.poisson(3, 24)
    
    return {
        'times': times,
        'lead_volume': lead_volume
    }

def generate_trend_data():
    """Generate sample trend analysis data"""
    np.random.seed(42)
    
    # 30 days of data
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    
    # Generate correlated trends
    base_conversion = 12.5 + np.random.normal(0, 0.5, 30).cumsum() * 0.1
    base_quality = 80 + np.random.normal(0, 0.3, 30).cumsum() * 0.2
    base_velocity = 14 + np.random.normal(0, 0.4, 30).cumsum() * 0.1
    base_commission = 6.0 + np.random.normal(0, 0.02, 30).cumsum() * 0.01
    
    return {
        'dates': dates,
        'conversion_rate': np.maximum(base_conversion, 8),
        'lead_quality': np.maximum(base_quality, 60),
        'deal_velocity': np.maximum(base_velocity, 10),
        'commission_rate': np.clip(base_commission, 5.5, 6.5)
    }

if __name__ == "__main__":
    main()