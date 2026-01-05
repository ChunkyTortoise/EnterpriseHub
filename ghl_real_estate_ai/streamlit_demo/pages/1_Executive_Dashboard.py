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
    from ghl_real_estate_ai.services.executive_dashboard import ExecutiveDashboardService
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
    .insight-card {
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
    st.info("💡 This page requires the ExecutiveDashboardService to be properly configured.")
    st.stop()

# Initialize service
@st.cache_resource
def get_dashboard_service():
    return ExecutiveDashboardService()

service = get_dashboard_service()

# Sidebar - Date range and filters
with st.sidebar:
    st.markdown("### 📅 Time Period")
    
    days = st.slider("Analysis Period (Days)", 1, 90, 30)
    
    st.markdown("---")
    
    if st.button("🔄 Refresh Dashboard"):
        st.cache_resource.clear()
        st.rerun()

# Get dashboard data
location_id = "demo_location"
summary = service.get_executive_summary(location_id, days=days)
metrics = summary["metrics"]

# Top KPI Cards
st.markdown("### 📈 Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_convos = metrics["conversations"]["total"]
    change = metrics["conversations"]["change_vs_previous"]
    st.metric(
        "Total Conversations",
        f"{total_convos:,}",
        f"{change:+.1f}%",
        delta_color="normal"
    )

with col2:
    hot_leads = metrics["lead_quality"]["hot_leads"]
    hot_pct = metrics["lead_quality"]["hot_percentage"]
    st.metric(
        "Hot Leads",
        f"{hot_leads:,}",
        f"{hot_pct:.1f}% of total"
    )

with col3:
    conversion_rate = metrics["conversion"]["conversion_rate"]
    st.metric(
        "Conversion Rate",
        f"{conversion_rate:.1f}%",
        "Target: 20%"
    )

with col4:
    pipeline_value = metrics["pipeline"]["value"]
    st.metric(
        "Pipeline Value",
        f"${pipeline_value:,.0f}",
        "Est. Commission"
    )

st.markdown("---")

# Insights and Action Items
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🧠 AI Business Insights")
    for insight in summary["insights"]:
        color = "#d4edda" if insight["type"] == "success" else "#fff3cd" if insight["type"] == "warning" else "#e2e3e5"
        border = "#28a745" if insight["type"] == "success" else "#ffc107" if insight["type"] == "warning" else "#6c757d"
        
        st.markdown(f"""
        <div style="background-color: {color}; border-left: 5px solid {border}; padding: 15px; margin-bottom: 10px; border-radius: 4px;">
            <strong style="color: #333;">{insight['title']}</strong><br>
            <span style="color: #555;">{insight['message']}</span>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown("### 🚨 Action Items")
    if not summary["action_items"]:
        st.success("No immediate actions required. System performing optimally.")
    else:
        for item in summary["action_items"]:
            st.markdown(f"""
            <div style="background-color: #f8d7da; border-left: 5px solid #dc3545; padding: 15px; margin-bottom: 10px; border-radius: 4px;">
                <strong style="color: #721c24;">{item['title']}</strong> (Priority: {item['priority'].upper()})<br>
                <span style="color: #721c24;">Action: {item['action']}</span><br>
                <em style="color: #721c24; font-size: 0.9em;">Impact: {item['impact']}</em>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# Trends
st.markdown("### 📊 Performance Trends")
trend_data = summary["trends"]["daily"]
if trend_data:
    df_trends = Path(project_root) # placeholder for actual dataframe conversion if needed
    
    dates = [d["date"] for d in trend_data]
    convos = [d["conversations"] for d in trend_data]
    hot = [d["hot_leads"] for d in trend_data]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=convos, name="Total Conversations", line=dict(color='#667eea', width=3)))
    fig.add_trace(go.Bar(x=dates, y=hot, name="Hot Leads", marker_color='#10B981'))
    
    fig.update_layout(
        title=f"{days}-Day Activity Trend",
        xaxis_title="Date",
        yaxis_title="Count",
        hovermode='x unified',
        height=400,
        barmode='group'
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Insufficient data to display trends.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    <p>📊 Executive Dashboard | Real-time KPI monitoring and business intelligence</p>
    <p>Last updated: {}</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)