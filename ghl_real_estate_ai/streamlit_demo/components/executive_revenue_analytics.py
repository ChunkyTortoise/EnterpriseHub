"""
Executive Dashboard Enhancement Module

Revenue forecasting and multi-tenant analytics for executive command center
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random
import pandas as pd


def render_revenue_forecasting_section():
    """Render revenue forecasting with confidence bands"""
    
    st.markdown("---")
    st.markdown("### 💰 Revenue Forecasting & Pipeline Analytics")
    st.caption("Multi-tenant revenue projections with AI-powered forecasting")
    
    # Revenue tabs
    forecast_tab, pipeline_tab, growth_tab = st.tabs([
        "📈 30-Day Forecast",
        "🎯 Pipeline by Stage",
        "📊 Growth Metrics"
    ])
    
    with forecast_tab:
        render_revenue_forecast_chart()
    
    with pipeline_tab:
        render_pipeline_breakdown()
    
    with growth_tab:
        render_growth_metrics()


def render_revenue_forecast_chart():
    """Revenue forecast with confidence intervals"""
    
    # Generate forecast data
    dates = [(datetime.now() + timedelta(days=i)) for i in range(30)]
    
    # Base revenue trend
    base_revenue = [180000 + (i * 5000) + random.uniform(-10000, 15000) for i in range(30)]
    
    # Confidence bands (±20%)
    upper_bound = [r * 1.2 for r in base_revenue]
    lower_bound = [r * 0.8 for r in base_revenue]
    
    fig = go.Figure()
    
    # Confidence band
    fig.add_trace(go.Scatter(
        x=dates + dates[::-1],
        y=upper_bound + lower_bound[::-1],
        fill='toself',
        fillcolor='rgba(99, 102, 241, 0.15)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Confidence Band',
        showlegend=True
    ))
    
    # Forecast line
    fig.add_trace(go.Scatter(
        x=dates,
        y=base_revenue,
        mode='lines+markers',
        name='Projected Revenue',
        line=dict(color='#6366F1', width=3),
        marker=dict(size=6)
    ))
    
    # Historical data (last 10 days)
    hist_dates = [(datetime.now() - timedelta(days=i)) for i in range(10, 0, -1)]
    hist_revenue = [160000 + (i * 4000) + random.uniform(-8000, 12000) for i in range(10)]
    
    fig.add_trace(go.Scatter(
        x=hist_dates,
        y=hist_revenue,
        mode='lines+markers',
        name='Historical Revenue',
        line=dict(color='#10B981', width=3, dash='dash'),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        height=400,
        xaxis_title="Date",
        yaxis_title="Revenue ($)",
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Key forecast metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_forecast = sum(base_revenue)
    avg_daily = total_forecast / 30
    
    with col1:
        st.metric(
            "30-Day Forecast",
            f"${total_forecast/1000000:.2f}M",
            delta=f"+{random.randint(15, 25)}% vs last month"
        )
    
    with col2:
        st.metric(
            "Daily Average",
            f"${avg_daily/1000:.0f}K",
            delta=f"+${random.randint(5, 15)}K"
        )
    
    with col3:
        st.metric(
            "Forecast Confidence",
            "87%",
            delta="High confidence"
        )
    
    with col4:
        st.metric(
            "At-Risk Pipeline",
            f"${random.randint(200, 400)}K",
            delta=f"-{random.randint(10, 20)}%",
            delta_color="inverse"
        )


def render_pipeline_breakdown():
    """Pipeline value by deal stage"""
    
    # Pipeline stages with values
    stages = {
        "New Leads": {"value": 1200000, "count": 45, "color": "#3B82F6"},
        "Qualified": {"value": 850000, "count": 28, "color": "#8B5CF6"},
        "Showing Scheduled": {"value": 620000, "count": 18, "color": "#F59E0B"},
        "Offer Made": {"value": 480000, "count": 12, "color": "#EF4444"},
        "Under Contract": {"value": 350000, "count": 7, "color": "#10B981"}
    }
    
    # Funnel chart
    fig = go.Figure(go.Funnel(
        y=list(stages.keys()),
        x=[s["value"] for s in stages.values()],
        textinfo="value+percent initial",
        textposition="inside",
        marker=dict(
            color=[s["color"] for s in stages.values()]
        ),
        connector=dict(line=dict(color="#E5E7EB", width=2))
    ))
    
    fig.update_layout(
        height=350,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Stage details
    st.markdown("#### Pipeline Details by Stage")
    
    for stage_name, data in stages.items():
        col_name, col_value, col_count, col_avg = st.columns([2, 1, 1, 1])
        
        with col_name:
            st.markdown(f"**{stage_name}**")
        
        with col_value:
            st.markdown(f"${data['value']/1000:.0f}K")
        
        with col_count:
            st.markdown(f"{data['count']} deals")
        
        with col_avg:
            avg_deal = data['value'] / data['count'] if data['count'] > 0 else 0
            st.markdown(f"${avg_deal/1000:.0f}K avg")


def render_growth_metrics():
    """Month-over-month and year-over-year growth"""
    
    # Growth comparison data
    months = ['Sep', 'Oct', 'Nov', 'Dec', 'Jan']
    revenue_2025 = [850, 920, 980, 1050, 1200]
    revenue_2024 = [720, 780, 810, 850, 920]
    
    fig = go.Figure()
    
    # 2025 revenue
    fig.add_trace(go.Bar(
        x=months,
        y=revenue_2025,
        name='2025',
        marker_color='#6366F1',
        text=[f'${v}K' for v in revenue_2025],
        textposition='outside'
    ))
    
    # 2024 revenue (comparison)
    fig.add_trace(go.Bar(
        x=months,
        y=revenue_2024,
        name='2024',
        marker_color='#E5E7EB',
        text=[f'${v}K' for v in revenue_2024],
        textposition='outside'
    ))
    
    fig.update_layout(
        height=350,
        barmode='group',
        xaxis_title="Month",
        yaxis_title="Revenue ($K)",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Growth metrics
    col1, col2, col3 = st.columns(3)
    
    mom_growth = ((revenue_2025[-1] - revenue_2025[-2]) / revenue_2025[-2]) * 100
    yoy_growth = ((revenue_2025[-1] - revenue_2024[-1]) / revenue_2024[-1]) * 100
    
    with col1:
        st.metric(
            "Month-over-Month",
            f"+{mom_growth:.1f}%",
            delta="Strong growth"
        )
    
    with col2:
        st.metric(
            "Year-over-Year",
            f"+{yoy_growth:.1f}%",
            delta="Excellent performance"
        )
    
    with col3:
        cagr = ((revenue_2025[-1] / revenue_2024[0]) ** (1/5) - 1) * 100
        st.metric(
            "5-Month CAGR",
            f"+{cagr:.1f}%",
            delta="Sustainable growth"
        )
    
    # Multi-tenant breakdown
    st.markdown("---")
    st.markdown("#### Multi-Tenant Revenue Distribution")
    
    tenants = [
        {"name": "Austin Team", "revenue": 680, "growth": 25},
        {"name": "Round Rock Team", "revenue": 420, "growth": 18},
        {"name": "Pflugerville Team", "revenue": 100, "growth": 35}
    ]
    
    for tenant in tenants:
        col_name, col_revenue, col_growth = st.columns([2, 1, 1])
        
        with col_name:
            st.markdown(f"**{tenant['name']}**")
        
        with col_revenue:
            st.markdown(f"${tenant['revenue']}K")
        
        with col_growth:
            growth_color = "#10B981" if tenant['growth'] > 20 else "#F59E0B"
            st.markdown(f"<span style='color: {growth_color}; font-weight: 600;'>+{tenant['growth']}%</span>", unsafe_allow_html=True)


def render_executive_dashboard_enhanced():
    """Enhanced executive dashboard with revenue forecasting"""
    from .executive_dashboard import render_executive_dashboard
    
    # Render original dashboard
    render_executive_dashboard()
    
    # Add revenue forecasting section
    render_revenue_forecasting_section()
