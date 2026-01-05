"""
GHL Real Estate AI - Revenue Attribution
Track ROI and attribute revenue to marketing channels and campaigns
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Any

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

try:
    from ghl_real_estate_ai.services.revenue_attribution import RevenueAttributionEngine
    SERVICE_AVAILABLE = True
except ImportError as e:
    SERVICE_AVAILABLE = False
    import_error = str(e)

# Page config
st.set_page_config(
    page_title="Revenue Attribution",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .attribution-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 15px 0;
    }
    .channel-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        text-align: center;
    }
    .roi-positive {
        color: #28a745;
        font-weight: bold;
    }
    .roi-negative {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("💰 Revenue Attribution")
st.markdown("**Track ROI and attribute revenue to marketing touchpoints**")
st.markdown("---")

# Check service availability
if not SERVICE_AVAILABLE:
    st.error(f"⚠️ Revenue Attribution service not available: {import_error}")
    st.info("💡 This page requires the RevenueAttributionEngine service to be properly configured.")
    st.stop()

# Initialize service
@st.cache_resource
def get_attribution_engine():
    return RevenueAttributionEngine()

engine = get_attribution_engine()

# Sidebar - Settings
with st.sidebar:
    st.markdown("### 📅 Time Period")
    
    days = st.slider("Analysis Period (Days)", 1, 180, 90)
    start_date = datetime.now() - timedelta(days=days)
    end_date = datetime.now()
    
    st.markdown("---")
    st.markdown("### 🎯 Attribution Model")
    attribution_model = st.selectbox(
        "Model Type",
        ["Last Touch", "First Touch", "Linear", "Time Decay", "Position Based"]
    )
    st.info(f"Using **{attribution_model}** model")

# Get attribution data
location_id = "demo_location"
report = engine.get_full_attribution_report(location_id, start_date=start_date, end_date=end_date)
summary = report["summary"]

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🎯 Channels", "🛤️ Conversion Funnel", "📈 ROI Analysis"])

with tab1:
    st.markdown("### 📊 Revenue Attribution Overview")
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Revenue", f"${summary['total_revenue']:,.0f}", "+12.5%")
    with col2:
        st.metric("Total Deals", summary['total_deals'], "+2")
    with col3:
        st.metric("Avg Deal Value", f"${summary['avg_deal_value']:,.0f}")
    with col4:
        st.metric("Pipeline Value", f"${summary['pipeline_value']:,.0f}")
    
    st.markdown("---")
    
    # Revenue timeline
    st.markdown("#### 📈 Revenue Timeline")
    timeline_data = report["revenue_timeline"]
    if timeline_data:
        periods = [t["period"] for t in timeline_data]
        revenues = [t["revenue"] for t in timeline_data]
        
        fig = go.Figure(go.Scatter(x=periods, y=revenues, mode='lines+markers+text', 
                                  text=[f"${r:,.0f}" for r in revenues], textposition="top center"))
        fig.update_layout(height=400, title="Monthly Revenue Growth")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("### 🎯 Channel Performance Analysis")
    
    channels = report["channel_performance"]
    for channel in channels:
        st.markdown(f"""
        <div class="attribution-card">
            <h4 style="color: #667eea;">{channel['channel']}</h4>
            <div style="display: flex; justify-content: space-between; margin-top: 10px;">
                <div>
                    <strong>Conversations:</strong> {channel['conversations']}<br>
                    <strong>Deals:</strong> {channel['deals']}
                </div>
                <div>
                    <strong>Revenue:</strong> ${channel['revenue']:,.0f}<br>
                    <strong>Conv. Rate:</strong> {channel['conversion_rate']}%
                </div>
                <div>
                    <strong>Cost:</strong> ${channel['cost']:,.0f}<br>
                    <strong>ROI:</strong> <span class="roi-positive">{channel['roi']:.1f}%</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with tab3:
    st.markdown("### 🛤️ Lead-to-Revenue Funnel")
    funnel_data = report["conversion_funnel"]["stages"]
    
    fig = go.Figure(go.Funnel(
        y=[s["stage"] for s in funnel_data],
        x=[s["count"] for s in funnel_data],
        textinfo="value+percent initial"
    ))
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    st.info(f"**Overall Conversion Rate:** {report['conversion_funnel']['overall_conversion_rate']}%")
    st.warning(f"**Biggest Drop-off:** {report['conversion_funnel']['biggest_drop_off']}")

with tab4:
    st.markdown("### 📈 ROI Analysis & Top Performers")
    
    roi_data = report["roi_by_source"]
    df_roi = pd.DataFrame(roi_data)
    
    fig = px.bar(df_roi, x='source', y='profit', color='roi_percentage', 
                 title="Profit by Source", labels={'profit': 'Net Profit ($)', 'source': 'Source'})
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("#### 🏆 Top Performers")
    top = report["top_performers"]
    cols = st.columns(2)
    with cols[0]:
        st.write(f"**Best Channel:** {top['best_channel']}")
        st.write(f"**Best Time:** {top['best_time']}")
    with cols[1]:
        st.write(f"**Best Template:** {top['best_message_template']}")
        st.write(f"**Highest Conversion:** {top['highest_conversion_source']}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    <p>💰 Revenue Attribution | Track marketing ROI and optimize spend</p>
    <p>Generated at: {}</p>
</div>
""".format(report["generated_at"]), unsafe_allow_html=True)