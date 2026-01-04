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
    from services.revenue_attribution import RevenueAttributionEngine
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
    .touchpoint-badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 15px;
        background-color: #667eea;
        color: white;
        font-size: 0.8em;
        margin: 3px;
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
    return RevenueAttributionEngine(data_dir="data")

attribution = get_attribution_engine()

# Sidebar - Settings
with st.sidebar:
    st.markdown("### 📅 Time Period")
    
    time_range = st.selectbox(
        "Select Range",
        ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Last Year", "Custom"]
    )
    
    if time_range == "Custom":
        start_date = st.date_input("Start", datetime.now() - timedelta(days=30))
        end_date = st.date_input("End", datetime.now())
    
    st.markdown("---")
    st.markdown("### 🎯 Attribution Model")
    
    attribution_model = st.selectbox(
        "Model Type",
        ["Last Touch", "First Touch", "Linear", "Time Decay", "Position Based"]
    )
    
    st.info(f"Using **{attribution_model}** attribution model")
    
    st.markdown("---")
    st.markdown("### 🔍 Filters")
    
    channel_filter = st.multiselect(
        "Channels",
        ["All", "Organic Search", "Paid Search", "Social Media", "Email", "Referral", "Direct"],
        default=["All"]
    )
    
    campaign_filter = st.multiselect(
        "Campaigns",
        ["All", "Spring Sale", "Holiday Promo", "Open House", "Newsletter"],
        default=["All"]
    )

# Get attribution data
location_id = "demo_location"
attribution_data = attribution.get_attribution_data(location_id, days=30)

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🎯 Channels", "🛤️ Customer Journey", "📈 ROI Analysis"])

with tab1:
    st.markdown("### 📊 Revenue Attribution Overview")
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_revenue = attribution_data.get("total_revenue", 285000)
        st.metric("Total Revenue", f"${total_revenue:,.0f}", "+12.5%")
    
    with col2:
        marketing_spend = attribution_data.get("marketing_spend", 45000)
        st.metric("Marketing Spend", f"${marketing_spend:,.0f}", "+5.2%")
    
    with col3:
        roi = ((total_revenue - marketing_spend) / marketing_spend * 100)
        st.metric("ROI", f"{roi:.1f}%", "+8.3%")
    
    with col4:
        attributed_revenue = attribution_data.get("attributed_revenue", 240000)
        attribution_rate = (attributed_revenue / total_revenue * 100)
        st.metric("Attribution Rate", f"{attribution_rate:.1f}%", "+2.1%")
    
    st.markdown("---")
    
    # Revenue by channel
    st.markdown("#### 💰 Revenue by Channel")
    
    channel_data = {
        "Organic Search": 85000,
        "Paid Search": 72000,
        "Social Media": 45000,
        "Email": 28000,
        "Referral": 35000,
        "Direct": 20000
    }
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig_waterfall = go.Figure(go.Waterfall(
            name="Revenue",
            orientation="v",
            x=list(channel_data.keys()) + ["Total"],
            y=list(channel_data.values()) + [sum(channel_data.values())],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            decreasing={"marker": {"color": "#dc3545"}},
            increasing={"marker": {"color": "#28a745"}},
            totals={"marker": {"color": "#667eea"}}
        ))
        
        fig_waterfall.update_layout(
            title="Revenue Attribution Waterfall",
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig_waterfall, use_container_width=True)
    
    with col2:
        st.markdown("#### 📊 Channel Distribution")
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=list(channel_data.keys()),
            values=list(channel_data.values()),
            hole=0.4,
            marker_colors=['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b', '#feca57']
        )])
        
        fig_pie.update_layout(height=400, showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    st.markdown("---")
    
    # Trend over time
    st.markdown("#### 📈 Revenue Trend by Channel")
    
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    
    fig_trend = go.Figure()
    
    for channel, base_value in list(channel_data.items())[:3]:  # Top 3 channels
        values = [base_value/30 + (i * 100) for i in range(30)]
        fig_trend.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode='lines',
            name=channel,
            stackgroup='one'
        ))
    
    fig_trend.update_layout(
        title="30-Day Revenue Attribution Trend",
        xaxis_title="Date",
        yaxis_title="Revenue ($)",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig_trend, use_container_width=True)

with tab2:
    st.markdown("### 🎯 Channel Performance Analysis")
    
    # Channel cards
    channels = [
        {
            "name": "Organic Search",
            "revenue": 85000,
            "cost": 5000,
            "conversions": 42,
            "cpa": 119,
            "roi": 1600
        },
        {
            "name": "Paid Search",
            "revenue": 72000,
            "cost": 18000,
            "conversions": 35,
            "cpa": 514,
            "roi": 300
        },
        {
            "name": "Social Media",
            "revenue": 45000,
            "cost": 8000,
            "conversions": 28,
            "cpa": 286,
            "roi": 462
        },
        {
            "name": "Email Marketing",
            "revenue": 28000,
            "cost": 2000,
            "conversions": 18,
            "cpa": 111,
            "roi": 1300
        },
        {
            "name": "Referral",
            "revenue": 35000,
            "cost": 3000,
            "conversions": 22,
            "cpa": 136,
            "roi": 1067
        },
        {
            "name": "Direct",
            "revenue": 20000,
            "cost": 1000,
            "conversions": 12,
            "cpa": 83,
            "roi": 1900
        }
    ]
    
    for idx, channel in enumerate(channels):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"""
            <div class="attribution-card">
                <h4>{channel['name']}</h4>
                <div style="display: flex; justify-content: space-between; margin-top: 15px;">
                    <div>
                        <p style="margin: 5px 0;"><strong>Revenue:</strong> ${channel['revenue']:,.0f}</p>
                        <p style="margin: 5px 0;"><strong>Cost:</strong> ${channel['cost']:,.0f}</p>
                    </div>
                    <div>
                        <p style="margin: 5px 0;"><strong>Conversions:</strong> {channel['conversions']}</p>
                        <p style="margin: 5px 0;"><strong>CPA:</strong> ${channel['cpa']}</p>
                    </div>
                    <div>
                        <p style="margin: 5px 0;"><strong>ROI:</strong> <span class="roi-positive">{channel['roi']}%</span></p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.button("📊 Details", key=f"details_{idx}"):
                st.info(f"Viewing details for {channel['name']}")
            if st.button("📈 Optimize", key=f"optimize_{idx}"):
                st.success(f"Optimization suggestions for {channel['name']}")
    
    st.markdown("---")
    
    # Performance comparison
    st.markdown("#### 📊 Channel Comparison Matrix")
    
    df_channels = pd.DataFrame(channels)
    
    fig_scatter = px.scatter(
        df_channels,
        x="cost",
        y="revenue",
        size="conversions",
        color="roi",
        hover_name="name",
        labels={"cost": "Marketing Spend ($)", "revenue": "Revenue ($)", "roi": "ROI (%)"},
        title="Cost vs Revenue (bubble size = conversions)",
        color_continuous_scale="RdYlGn"
    )
    
    fig_scatter.update_layout(height=500)
    st.plotly_chart(fig_scatter, use_container_width=True)

with tab3:
    st.markdown("### 🛤️ Customer Journey Analysis")
    
    st.info("💡 Track how customers interact with multiple touchpoints before conversion")
    
    # Journey example
    st.markdown("#### 🎯 Sample Customer Journey")
    
    journey = [
        {"step": 1, "touchpoint": "Organic Search", "date": "2026-01-01", "action": "Visited website"},
        {"step": 2, "touchpoint": "Email", "date": "2026-01-02", "action": "Opened newsletter"},
        {"step": 3, "touchpoint": "Social Media", "date": "2026-01-03", "action": "Clicked ad"},
        {"step": 4, "touchpoint": "Direct", "date": "2026-01-04", "action": "Converted"}
    ]
    
    # Visual journey
    cols = st.columns(len(journey))
    for idx, step in enumerate(journey):
        with cols[idx]:
            st.markdown(f"""
            <div style="text-align: center; padding: 15px; background-color: #f8f9fa; border-radius: 10px;">
                <h3 style="color: #667eea;">Step {step['step']}</h3>
                <p><strong>{step['touchpoint']}</strong></p>
                <p style="font-size: 0.9em;">{step['action']}</p>
                <p style="font-size: 0.8em; color: gray;">{step['date']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        if idx < len(journey) - 1:
            st.markdown("→", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Attribution by model
    st.markdown("#### 🎯 Attribution by Model")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Last Touch Attribution")
        st.bar_chart({
            "Organic Search": 0,
            "Email": 0,
            "Social Media": 0,
            "Direct": 100
        })
        st.caption("100% credit to final touchpoint")
    
    with col2:
        st.markdown("##### Linear Attribution")
        st.bar_chart({
            "Organic Search": 25,
            "Email": 25,
            "Social Media": 25,
            "Direct": 25
        })
        st.caption("Equal credit to all touchpoints")
    
    st.markdown("---")
    
    # Journey metrics
    st.markdown("#### 📊 Journey Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Avg Touchpoints", "3.8")
    with col2:
        st.metric("Avg Journey Time", "12 days")
    with col3:
        st.metric("Multi-touch Rate", "78%")
    with col4:
        st.metric("Direct Conv. Rate", "22%")
    
    st.markdown("---")
    
    # Sankey diagram
    st.markdown("#### 🌊 Journey Flow Visualization")
    
    fig_sankey = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=["Organic", "Social", "Email", "Qualified", "Converted"],
            color=["#667eea", "#764ba2", "#f093fb", "#4facfe", "#28a745"]
        ),
        link=dict(
            source=[0, 0, 1, 1, 2, 2, 3, 3],
            target=[3, 4, 3, 4, 3, 4, 4, 4],
            value=[30, 10, 20, 5, 15, 8, 25, 18]
        )
    )])
    
    fig_sankey.update_layout(
        title="Customer Journey Flow",
        height=400
    )
    
    st.plotly_chart(fig_sankey, use_container_width=True)

with tab4:
    st.markdown("### 📈 ROI Analysis & Optimization")
    
    # ROI summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="channel-card">
            <h4>Overall ROI</h4>
            <h2 style="margin: 20px 0;">533%</h2>
            <p>$5.33 return per $1 spent</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="channel-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <h4>Best Performer</h4>
            <h2 style="margin: 20px 0;">Direct</h2>
            <p>1900% ROI</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="channel-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <h4>Most Efficient</h4>
            <h2 style="margin: 20px 0;">Email</h2>
            <p>$111 CPA</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Budget optimization
    st.markdown("#### 💡 Budget Optimization Recommendations")
    
    st.success("✅ **Increase email marketing budget by 30%** - Highest ROI with lowest CPA")
    st.success("✅ **Maintain organic search efforts** - Strong performance with minimal cost")
    st.warning("⚠️ **Optimize paid search targeting** - High cost, moderate ROI")
    st.info("💡 **Test social media retargeting** - Potential to improve conversion rate")
    
    st.markdown("---")
    
    # ROI trend
    st.markdown("#### 📈 ROI Trend Over Time")
    
    dates = pd.date_range(end=datetime.now(), periods=12, freq='M')
    roi_values = [450, 475, 490, 510, 485, 520, 530, 515, 540, 525, 533, 545]
    
    fig_roi_trend = go.Figure()
    
    fig_roi_trend.add_trace(go.Scatter(
        x=dates,
        y=roi_values,
        mode='lines+markers',
        name='ROI',
        line=dict(color='#28a745', width=3),
        marker=dict(size=8),
        fill='tozeroy'
    ))
    
    fig_roi_trend.update_layout(
        title="12-Month ROI Trend",
        xaxis_title="Month",
        yaxis_title="ROI (%)",
        height=400
    )
    
    st.plotly_chart(fig_roi_trend, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    <p>💰 Revenue Attribution | Track marketing ROI and optimize spend</p>
    <p>Attribution Model: {} | Last updated: {}</p>
</div>
""".format(attribution_model, datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
