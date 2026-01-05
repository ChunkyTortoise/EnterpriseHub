"""
GHL Real Estate AI - Competitive Benchmarking
Compare performance against industry benchmarks and competitors
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Any

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

try:
    from ghl_real_estate_ai.services.competitive_benchmarking import BenchmarkingEngine
    SERVICE_AVAILABLE = True
except ImportError as e:
    SERVICE_AVAILABLE = False
    import_error = str(e)

# Page config
st.set_page_config(
    page_title="Competitive Benchmarking",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .benchmark-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 15px 0;
    }
    .performance-badge {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        margin: 5px;
    }
    .badge-excellent {
        background-color: #28a745;
        color: white;
    }
    .badge-good {
        background-color: #17a2b8;
        color: white;
    }
    .badge-average {
        background-color: #ffc107;
        color: black;
    }
    .badge-below {
        background-color: #dc3545;
        color: white;
    }
    .competitor-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 8px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🏆 Competitive Benchmarking")
st.markdown("**Compare your performance against industry standards**")
st.markdown("---")

# Check service availability
if not SERVICE_AVAILABLE:
    st.error(f"⚠️ Benchmarking Engine not available: {import_error}")
    st.info("💡 This page requires the BenchmarkingEngine service to be properly configured.")
    st.stop()

# Initialize service
@st.cache_resource
def get_benchmarking_engine():
    return BenchmarkingEngine(data_dir="data")

benchmark = get_benchmarking_engine()

# Sidebar - Settings
with st.sidebar:
    st.markdown("### 🎯 Comparison Settings")
    
    industry = st.selectbox(
        "Industry",
        ["Real Estate", "Property Management", "Commercial RE", "Residential RE"]
    )
    
    market_size = st.selectbox(
        "Market Size",
        ["All Markets", "Enterprise", "Mid-Market", "Small Business"]
    )
    
    region = st.selectbox(
        "Region",
        ["All Regions", "North America", "Europe", "Asia-Pacific", "Latin America"]
    )
    
    st.markdown("---")
    st.markdown("### 📊 Metrics to Compare")
    
    compare_conversion = st.checkbox("Conversion Rate", value=True)
    compare_response = st.checkbox("Response Time", value=True)
    compare_roi = st.checkbox("ROI", value=True)
    compare_satisfaction = st.checkbox("Customer Satisfaction", value=True)
    
    st.markdown("---")
    
    if st.button("🔄 Refresh Data"):
        st.cache_resource.clear()
        st.rerun()

# Get benchmark data
location_id = "demo_location"
benchmark_data = benchmark.get_benchmarks(location_id, industry=industry)

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Performance Metrics", "🎯 Gap Analysis", "💡 Insights"])

with tab1:
    st.markdown("### 📊 Benchmarking Overview")
    
    # Performance summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px;">
            <h4>Overall Rank</h4>
            <h2 style="margin: 15px 0;">Top 15%</h2>
            <p>In your industry</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.metric("Metrics Above Avg", "7 of 10", "+2")
    
    with col3:
        st.metric("Industry Percentile", "85th", "+5")
    
    with col4:
        st.metric("Competitive Score", "8.2/10", "+0.3")
    
    st.markdown("---")
    
    # Performance badges
    st.markdown("#### 🏅 Performance Categories")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<span class="performance-badge badge-excellent">✓ Conversion Rate</span>', 
                   unsafe_allow_html=True)
    with col2:
        st.markdown('<span class="performance-badge badge-excellent">✓ Response Time</span>', 
                   unsafe_allow_html=True)
    with col3:
        st.markdown('<span class="performance-badge badge-good">✓ Lead Quality</span>', 
                   unsafe_allow_html=True)
    with col4:
        st.markdown('<span class="performance-badge badge-average">⚠ Close Rate</span>', 
                   unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Radar chart comparison
    st.markdown("#### 🎯 Multi-Dimensional Comparison")
    
    categories = ['Conversion', 'Response Time', 'Lead Quality', 'ROI', 'Satisfaction', 'Close Rate']
    
    fig_radar = go.Figure()
    
    # Your performance
    fig_radar.add_trace(go.Scatterpolar(
        r=[85, 92, 78, 88, 75, 68],
        theta=categories,
        fill='toself',
        name='Your Performance',
        line=dict(color='#667eea', width=2)
    ))
    
    # Industry average
    fig_radar.add_trace(go.Scatterpolar(
        r=[70, 75, 72, 73, 70, 71],
        theta=categories,
        fill='toself',
        name='Industry Average',
        line=dict(color='#ffc107', width=2)
    ))
    
    # Top performer
    fig_radar.add_trace(go.Scatterpolar(
        r=[95, 98, 92, 94, 90, 88],
        theta=categories,
        fill='toself',
        name='Top 10%',
        line=dict(color='#28a745', width=2),
        opacity=0.3
    ))
    
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        height=500
    )
    
    st.plotly_chart(fig_radar, use_container_width=True)
    
    st.markdown("---")
    
    # Quick insights
    st.markdown("#### 💡 Quick Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("✅ **Strengths:**")
        st.markdown("""
        - Response time 23% faster than average
        - Conversion rate in top quartile
        - ROI exceeding industry benchmark by 15%
        """)
    
    with col2:
        st.warning("⚠️ **Areas for Improvement:**")
        st.markdown("""
        - Close rate 4% below industry average
        - Customer satisfaction trailing top performers
        - Lead nurture cycle 20% longer than optimal
        """)

with tab2:
    st.markdown("### 📈 Detailed Performance Metrics")
    
    # Metric comparison table
    metrics = [
        {
            "metric": "Lead Conversion Rate",
            "your_value": "12.5%",
            "industry_avg": "9.8%",
            "top_10": "15.2%",
            "percentile": 78,
            "status": "excellent"
        },
        {
            "metric": "Avg Response Time",
            "your_value": "8 min",
            "industry_avg": "15 min",
            "top_10": "5 min",
            "percentile": 85,
            "status": "excellent"
        },
        {
            "metric": "Lead Quality Score",
            "your_value": "78/100",
            "industry_avg": "72/100",
            "top_10": "88/100",
            "percentile": 68,
            "status": "good"
        },
        {
            "metric": "Marketing ROI",
            "your_value": "425%",
            "industry_avg": "315%",
            "top_10": "520%",
            "percentile": 72,
            "status": "good"
        },
        {
            "metric": "Customer Satisfaction",
            "your_value": "4.2/5",
            "industry_avg": "4.1/5",
            "top_10": "4.7/5",
            "percentile": 62,
            "status": "average"
        },
        {
            "metric": "Deal Close Rate",
            "your_value": "28%",
            "industry_avg": "32%",
            "top_10": "42%",
            "percentile": 45,
            "status": "below"
        }
    ]
    
    for metric in metrics:
        st.markdown(f"""
        <div class="benchmark-card">
            <h4>{metric['metric']}</h4>
            <div style="display: flex; justify-content: space-between; margin: 15px 0;">
                <div>
                    <p><strong>Your Performance:</strong> <span style="font-size: 1.3em; color: #667eea;">{metric['your_value']}</span></p>
                </div>
                <div>
                    <p><strong>Industry Average:</strong> {metric['industry_avg']}</p>
                    <p><strong>Top 10%:</strong> {metric['top_10']}</p>
                </div>
                <div>
                    <p><strong>Percentile:</strong> {metric['percentile']}th</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Progress bar
        progress_color = {
            "excellent": "#28a745",
            "good": "#17a2b8",
            "average": "#ffc107",
            "below": "#dc3545"
        }[metric['status']]
        
        st.progress(metric['percentile'] / 100)
        
        st.markdown("---")

with tab3:
    st.markdown("### 🎯 Gap Analysis")
    
    st.info("💡 Identify opportunities to reach top performer status")
    
    # Gap analysis chart
    st.markdown("#### 📊 Performance Gaps vs Top 10%")
    
    gaps = {
        "Conversion Rate": {"current": 12.5, "target": 15.2, "gap": 2.7},
        "Response Time": {"current": 92, "target": 98, "gap": 6},
        "Lead Quality": {"current": 78, "target": 88, "gap": 10},
        "ROI": {"current": 88, "target": 94, "gap": 6},
        "Satisfaction": {"current": 75, "target": 90, "gap": 15},
        "Close Rate": {"current": 68, "target": 88, "gap": 20}
    }
    
    fig_gap = go.Figure()
    
    # Current performance
    fig_gap.add_trace(go.Bar(
        name='Current',
        x=list(gaps.keys()),
        y=[v['current'] for v in gaps.values()],
        marker_color='#667eea'
    ))
    
    # Target (Top 10%)
    fig_gap.add_trace(go.Bar(
        name='Target (Top 10%)',
        x=list(gaps.keys()),
        y=[v['target'] for v in gaps.values()],
        marker_color='#28a745'
    ))
    
    fig_gap.update_layout(
        barmode='group',
        title="Current vs Target Performance",
        yaxis_title="Performance Score",
        height=400
    )
    
    st.plotly_chart(fig_gap, use_container_width=True)
    
    st.markdown("---")
    
    # Priority improvements
    st.markdown("#### 🎯 Priority Improvements")
    
    improvements = [
        {
            "area": "Close Rate",
            "gap": "20 points",
            "impact": "High",
            "effort": "Medium",
            "priority": 1,
            "actions": ["Improve lead qualification", "Enhanced follow-up sequence", "Sales training"]
        },
        {
            "area": "Customer Satisfaction",
            "gap": "15 points",
            "impact": "High",
            "effort": "Medium",
            "priority": 2,
            "actions": ["Post-sale follow-up", "Feedback system", "Customer success program"]
        },
        {
            "area": "Lead Quality",
            "gap": "10 points",
            "impact": "Medium",
            "effort": "Low",
            "priority": 3,
            "actions": ["Refine targeting", "Better pre-qualification", "Source optimization"]
        }
    ]
    
    for imp in improvements:
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**{imp['priority']}. {imp['area']}** (Gap: {imp['gap']})")
            st.markdown(f"*Actions: {', '.join(imp['actions'])}*")
        
        with col2:
            st.markdown(f"**Impact:** {imp['impact']}")
            st.markdown(f"**Effort:** {imp['effort']}")
        
        with col3:
            if st.button(f"📋 Create Plan", key=f"plan_{imp['priority']}"):
                st.success(f"Action plan created for {imp['area']}")
        
        st.markdown("---")

with tab4:
    st.markdown("### 💡 Competitive Insights")
    
    # Market trends
    st.markdown("#### 📈 Industry Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="benchmark-card">
            <h4>📊 Rising Metrics</h4>
            <ul>
                <li><strong>AI Adoption:</strong> +45% YoY</li>
                <li><strong>Response Automation:</strong> +38% YoY</li>
                <li><strong>Multi-channel Engagement:</strong> +32% YoY</li>
                <li><strong>Predictive Analytics:</strong> +29% YoY</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="benchmark-card">
            <h4>📉 Declining Metrics</h4>
            <ul>
                <li><strong>Manual Follow-up:</strong> -28% YoY</li>
                <li><strong>Cold Calling:</strong> -35% YoY</li>
                <li><strong>Traditional Advertising:</strong> -22% YoY</li>
                <li><strong>Print Marketing:</strong> -41% YoY</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Competitive positioning
    st.markdown("#### 🎯 Competitive Positioning")
    
    competitors = [
        {"name": "Competitor A", "score": 8.5, "strength": "Technology", "weakness": "Customer Service"},
        {"name": "Competitor B", "score": 7.8, "strength": "Price", "weakness": "Innovation"},
        {"name": "Competitor C", "score": 8.9, "strength": "Brand", "weakness": "Speed"},
        {"name": "Your Company", "score": 8.2, "strength": "Response Time", "weakness": "Close Rate"},
        {"name": "Competitor D", "score": 7.5, "strength": "Coverage", "weakness": "Quality"}
    ]
    
    # Sort by score
    competitors_sorted = sorted(competitors, key=lambda x: x['score'], reverse=True)
    
    for idx, comp in enumerate(competitors_sorted):
        rank = idx + 1
        is_you = comp['name'] == "Your Company"
        
        bg_color = "background: linear-gradient(90deg, rgba(102,126,234,0.1) 0%, white 100%);" if is_you else ""
        
        st.markdown(f"""
        <div class="competitor-row" style="{bg_color}">
            <div>
                <strong>#{rank} {comp['name']}</strong>
                {"<span style='color: #667eea; margin-left: 10px;'>← You</span>" if is_you else ""}
            </div>
            <div>Score: <strong>{comp['score']}/10</strong></div>
            <div>💪 {comp['strength']}</div>
            <div>⚠️ {comp['weakness']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Recommendations
    st.markdown("#### 🎯 Strategic Recommendations")
    
    st.success("""
    **1. Capitalize on Response Time Advantage**
    - Your 8-minute average is 47% faster than competitors
    - Market this as a key differentiator
    - Build customer testimonials around quick response
    """)
    
    st.info("""
    **2. Close the Close Rate Gap**
    - Focus on sales training and process optimization
    - Implement better qualification criteria
    - Consider pipeline acceleration tools
    """)
    
    st.warning("""
    **3. Monitor Competitor C**
    - Leading in overall score (8.9/10)
    - Strong brand recognition
    - Study their marketing strategies
    """)
    
    st.info("""
    **4. Leverage Technology Trends**
    - AI adoption growing 45% YoY
    - Position your AI capabilities prominently
    - Invest in automation and predictive analytics
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    <p>🏆 Competitive Benchmarking | Data-driven competitive intelligence</p>
    <p>Industry: {} | Last updated: {}</p>
</div>
""".format(industry, datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
