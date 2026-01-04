"""
GHL Real Estate AI - Executive Dashboard
Real-time KPIs and business intelligence for decision-makers
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

try:
    from services.executive_dashboard import ExecutiveDashboard
    SERVICE_AVAILABLE = True
except ImportError as e:
    SERVICE_AVAILABLE = False
    import_error = str(e)

# Page config
st.set_page_config(
    page_title="Executive Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .kpi-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    .alert-warning {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .alert-success {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .alert-danger {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("📊 Executive Dashboard")
st.markdown("**Real-time business intelligence and KPI monitoring**")
st.markdown("---")

# Check service availability
if not SERVICE_AVAILABLE:
    st.error(f"⚠️ Executive Dashboard service not available: {import_error}")
    st.info("💡 This page requires the ExecutiveDashboard service to be properly configured.")
    st.stop()

# Initialize service
@st.cache_resource
def get_dashboard_service():
    return ExecutiveDashboard(data_dir="data")

dashboard = get_dashboard_service()

# Sidebar - Date range and filters
with st.sidebar:
    st.markdown("### 📅 Time Period")
    
    time_period = st.selectbox(
        "Select Period:",
        ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Last Year", "Custom Range"]
    )
    
    if time_period == "Custom Range":
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
        end_date = st.date_input("End Date", datetime.now())
    else:
        end_date = datetime.now()
        if time_period == "Last 7 Days":
            start_date = end_date - timedelta(days=7)
        elif time_period == "Last 30 Days":
            start_date = end_date - timedelta(days=30)
        elif time_period == "Last 90 Days":
            start_date = end_date - timedelta(days=90)
        else:  # Last Year
            start_date = end_date - timedelta(days=365)
    
    st.markdown("---")
    st.markdown("### 🎯 Filters")
    
    location_filter = st.multiselect(
        "Locations:",
        ["All Locations", "Location A", "Location B", "Location C"],
        default=["All Locations"]
    )
    
    st.markdown("---")
    st.markdown("### 🔔 Alert Settings")
    
    alert_threshold = st.slider("Alert Threshold (%)", 0, 100, 80)
    
    if st.button("🔄 Refresh Dashboard"):
        st.cache_resource.clear()
        st.rerun()

# Get dashboard data
location_id = "demo_location"
dashboard_data = dashboard.get_dashboard_data(location_id, days=30)

# Top KPI Cards
st.markdown("### 📈 Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_revenue = dashboard_data.get("revenue", {}).get("total", 0)
    revenue_change = dashboard_data.get("revenue", {}).get("change_percent", 0)
    st.metric(
        "Total Revenue",
        f"${total_revenue:,.2f}",
        f"{revenue_change:+.1f}%",
        delta_color="normal"
    )

with col2:
    total_leads = dashboard_data.get("leads", {}).get("total", 0)
    leads_change = dashboard_data.get("leads", {}).get("change_percent", 0)
    st.metric(
        "Total Leads",
        f"{total_leads:,}",
        f"{leads_change:+.1f}%",
        delta_color="normal"
    )

with col3:
    conversion_rate = dashboard_data.get("conversion_rate", 0)
    conversion_change = dashboard_data.get("conversion_change", 0)
    st.metric(
        "Conversion Rate",
        f"{conversion_rate:.1f}%",
        f"{conversion_change:+.1f}%",
        delta_color="normal"
    )

with col4:
    avg_deal_size = dashboard_data.get("avg_deal_size", 0)
    deal_change = dashboard_data.get("deal_change", 0)
    st.metric(
        "Avg Deal Size",
        f"${avg_deal_size:,.0f}",
        f"{deal_change:+.1f}%",
        delta_color="normal"
    )

st.markdown("---")

# Revenue Trend Chart
st.markdown("### 💰 Revenue Trends")
col1, col2 = st.columns([2, 1])

with col1:
    # Generate trend data
    dates = [(datetime.now() - timedelta(days=x)).strftime("%Y-%m-%d") for x in range(30, 0, -1)]
    revenue_data = dashboard_data.get("revenue_trend", [15000 + (i * 500) for i in range(30)])
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=revenue_data,
        mode='lines+markers',
        name='Revenue',
        line=dict(color='#667eea', width=3),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title="30-Day Revenue Trend",
        xaxis_title="Date",
        yaxis_title="Revenue ($)",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### 📊 Revenue Breakdown")
    
    revenue_sources = {
        "New Leads": 45000,
        "Existing Clients": 32000,
        "Referrals": 18000,
        "Other": 5000
    }
    
    fig_pie = go.Figure(data=[go.Pie(
        labels=list(revenue_sources.keys()),
        values=list(revenue_sources.values()),
        hole=0.4,
        marker_colors=['#667eea', '#764ba2', '#f093fb', '#4facfe']
    )])
    
    fig_pie.update_layout(
        height=400,
        showlegend=True
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# Lead Performance
st.markdown("### 🎯 Lead Performance")
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Lead Stage Distribution")
    
    stages = ["New", "Contacted", "Qualified", "Negotiating", "Closed"]
    stage_counts = [120, 85, 45, 28, 15]
    
    fig_bar = go.Figure(data=[go.Bar(
        x=stages,
        y=stage_counts,
        marker_color=['#4facfe', '#00f2fe', '#43e97b', '#38f9d7', '#667eea'],
        text=stage_counts,
        textposition='auto'
    )])
    
    fig_bar.update_layout(
        xaxis_title="Stage",
        yaxis_title="Number of Leads",
        height=350
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.markdown("#### Conversion Funnel")
    
    funnel_stages = ["Visitors", "Leads", "Qualified", "Opportunities", "Closed"]
    funnel_values = [1000, 500, 250, 100, 30]
    
    fig_funnel = go.Figure(go.Funnel(
        y=funnel_stages,
        x=funnel_values,
        textinfo="value+percent initial",
        marker=dict(color=['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b'])
    ))
    
    fig_funnel.update_layout(height=350)
    
    st.plotly_chart(fig_funnel, use_container_width=True)

st.markdown("---")

# Performance Alerts
st.markdown("### 🔔 Performance Alerts")

alerts = dashboard_data.get("alerts", [])

if not alerts:
    st.success("✅ All systems operating normally. No alerts at this time.")
else:
    for alert in alerts:
        alert_type = alert.get("type", "info")
        message = alert.get("message", "Alert")
        
        if alert_type == "warning":
            st.markdown(f'<div class="alert-warning">⚠️ {message}</div>', unsafe_allow_html=True)
        elif alert_type == "danger":
            st.markdown(f'<div class="alert-danger">🚨 {message}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="alert-success">✅ {message}</div>', unsafe_allow_html=True)

st.markdown("---")

# System Health
st.markdown("### 🏥 System Health")
col1, col2, col3 = st.columns(3)

with col1:
    api_health = dashboard_data.get("api_health", 98.5)
    st.metric("API Uptime", f"{api_health}%", "+0.3%")
    
with col2:
    response_time = dashboard_data.get("avg_response_time", 245)
    st.metric("Avg Response Time", f"{response_time}ms", "-15ms")
    
with col3:
    active_users = dashboard_data.get("active_users", 47)
    st.metric("Active Users", active_users, "+5")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    <p>📊 Executive Dashboard | Real-time KPI monitoring and business intelligence</p>
    <p>Last updated: {}</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
