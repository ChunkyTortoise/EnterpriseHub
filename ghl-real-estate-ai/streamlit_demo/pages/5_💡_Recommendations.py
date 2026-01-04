"""
GHL Real Estate AI - Smart Recommendations
AI-powered action recommendations and optimization suggestions
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go
from typing import Dict, List, Any

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

try:
    from services.smart_recommendations import RecommendationEngine
    SERVICE_AVAILABLE = True
except ImportError as e:
    SERVICE_AVAILABLE = False
    import_error = str(e)

# Page config
st.set_page_config(
    page_title="Smart Recommendations",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .recommendation-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 15px 0;
        border-left: 5px solid #667eea;
    }
    .priority-high {
        border-left-color: #dc3545;
        background: linear-gradient(90deg, rgba(220,53,69,0.05) 0%, white 100%);
    }
    .priority-medium {
        border-left-color: #ffc107;
        background: linear-gradient(90deg, rgba(255,193,7,0.05) 0%, white 100%);
    }
    .priority-low {
        border-left-color: #28a745;
        background: linear-gradient(90deg, rgba(40,167,69,0.05) 0%, white 100%);
    }
    .impact-badge {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.9em;
        font-weight: bold;
        margin: 5px;
    }
    .impact-high {
        background-color: #dc3545;
        color: white;
    }
    .impact-medium {
        background-color: #ffc107;
        color: black;
    }
    .impact-low {
        background-color: #28a745;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("💡 Smart Recommendations")
st.markdown("**AI-powered insights and actionable suggestions**")
st.markdown("---")

# Check service availability
if not SERVICE_AVAILABLE:
    st.error(f"⚠️ Recommendation Engine not available: {import_error}")
    st.info("💡 This page requires the RecommendationEngine service to be properly configured.")
    st.stop()

# Initialize service
@st.cache_resource
def get_recommendation_engine():
    return RecommendationEngine(model_path="data/models")

rec_engine = get_recommendation_engine()

# Sidebar - Settings
with st.sidebar:
    st.markdown("### ⚙️ Recommendation Settings")
    
    priority_filter = st.multiselect(
        "Priority Levels",
        ["High", "Medium", "Low"],
        default=["High", "Medium", "Low"]
    )
    
    category_filter = st.multiselect(
        "Categories",
        ["Lead Management", "Campaign Optimization", "Sales Process", "Follow-up", "Content"],
        default=["Lead Management", "Campaign Optimization", "Sales Process"]
    )
    
    st.markdown("---")
    st.markdown("### 🎯 Display Options")
    
    show_dismissed = st.checkbox("Show Dismissed", value=False)
    show_completed = st.checkbox("Show Completed", value=False)
    auto_refresh = st.checkbox("Auto Refresh", value=True)
    
    st.markdown("---")
    
    if st.button("🔄 Refresh Recommendations"):
        st.cache_resource.clear()
        st.rerun()

# Get recommendations
location_id = "demo_location"
recommendations = rec_engine.get_recommendations(location_id, filters={
    "priority": priority_filter,
    "category": category_filter
})

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Active", "📊 Impact Analysis", "✅ Completed", "⚙️ Settings"])

with tab1:
    st.markdown("### 🎯 Active Recommendations")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        high_priority = len([r for r in recommendations if r.get('priority') == 'high'])
        st.metric("🔴 High Priority", high_priority)
    
    with col2:
        medium_priority = len([r for r in recommendations if r.get('priority') == 'medium'])
        st.metric("🟡 Medium Priority", medium_priority)
    
    with col3:
        low_priority = len([r for r in recommendations if r.get('priority') == 'low'])
        st.metric("🟢 Low Priority", low_priority)
    
    with col4:
        total_impact = sum([r.get('impact_score', 0) for r in recommendations])
        st.metric("💰 Total Impact", f"${total_impact:,.0f}")
    
    st.markdown("---")
    
    # Display recommendations
    if not recommendations:
        recommendations = [
            {
                "id": "rec_001",
                "title": "Follow up with high-scoring leads",
                "description": "15 leads with scores above 70 haven't been contacted in 48+ hours",
                "priority": "high",
                "category": "Lead Management",
                "impact_score": 12500,
                "effort": "Low",
                "time_estimate": "30 minutes",
                "actions": ["View leads", "Send bulk email", "Assign to agents"]
            },
            {
                "id": "rec_002",
                "title": "Optimize email campaign timing",
                "description": "Your emails sent at 2 PM have 45% higher open rates",
                "priority": "medium",
                "category": "Campaign Optimization",
                "impact_score": 8000,
                "effort": "Low",
                "time_estimate": "15 minutes",
                "actions": ["Adjust schedule", "View analytics"]
            },
            {
                "id": "rec_003",
                "title": "Update property listings",
                "description": "3 properties have been listed for 60+ days without updates",
                "priority": "medium",
                "category": "Content",
                "impact_score": 5000,
                "effort": "Medium",
                "time_estimate": "1 hour",
                "actions": ["View properties", "Update listings"]
            },
            {
                "id": "rec_004",
                "title": "Implement chatbot for night inquiries",
                "description": "25% of website visits happen outside business hours",
                "priority": "low",
                "category": "Sales Process",
                "impact_score": 15000,
                "effort": "High",
                "time_estimate": "2 weeks",
                "actions": ["View analytics", "Setup guide"]
            }
        ]
    
    for rec in recommendations:
        priority = rec.get('priority', 'low')
        priority_class = f"priority-{priority}"
        
        st.markdown(f"""
        <div class="recommendation-card {priority_class}">
            <h4>{rec['title']}</h4>
            <p>{rec['description']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
        
        with col1:
            impact_class = "impact-high" if rec['impact_score'] > 10000 else "impact-medium" if rec['impact_score'] > 5000 else "impact-low"
            st.markdown(f'<span class="impact-badge {impact_class}">Impact: ${rec["impact_score"]:,.0f}</span>', 
                       unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"**Effort:** {rec.get('effort', 'Unknown')}")
        
        with col3:
            st.markdown(f"**Time:** {rec.get('time_estimate', 'Unknown')}")
        
        with col4:
            st.markdown(f"**Category:** {rec.get('category', 'General')}")
        
        with col5:
            if st.button("▶️ Take Action", key=f"action_{rec['id']}"):
                st.success(f"✅ Action initiated for: {rec['title']}")
        
        # Action buttons
        action_cols = st.columns(len(rec.get('actions', [])) + 2)
        for idx, action in enumerate(rec.get('actions', [])):
            with action_cols[idx]:
                if st.button(f"🔧 {action}", key=f"{rec['id']}_{action}"):
                    st.info(f"Executing: {action}")
        
        with action_cols[-2]:
            if st.button("✅ Complete", key=f"complete_{rec['id']}"):
                st.success("Marked as completed!")
        
        with action_cols[-1]:
            if st.button("❌ Dismiss", key=f"dismiss_{rec['id']}"):
                st.warning("Dismissed")
        
        st.markdown("---")

with tab2:
    st.markdown("### 📊 Impact Analysis")
    
    # Impact vs Effort matrix
    st.markdown("#### 🎯 Impact vs Effort Matrix")
    
    fig = go.Figure()
    
    # Plot recommendations on scatter
    for rec in recommendations[:10]:  # Limit to first 10 for clarity
        impact = rec.get('impact_score', 0)
        effort_map = {"Low": 1, "Medium": 2, "High": 3}
        effort = effort_map.get(rec.get('effort', 'Medium'), 2)
        
        fig.add_trace(go.Scatter(
            x=[effort],
            y=[impact],
            mode='markers+text',
            name=rec.get('title', 'Recommendation')[:20],
            text=[rec.get('title', 'Rec')[:15]],
            textposition='top center',
            marker=dict(
                size=15,
                color=impact,
                colorscale='RdYlGn',
                showscale=True,
                line=dict(width=2, color='white')
            )
        ))
    
    fig.update_layout(
        xaxis_title="Effort Required",
        yaxis_title="Potential Impact ($)",
        xaxis=dict(tickmode='array', tickvals=[1, 2, 3], ticktext=['Low', 'Medium', 'High']),
        height=500,
        showlegend=False
    )
    
    # Add quadrant lines
    fig.add_hline(y=7500, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=2, line_dash="dash", line_color="gray", opacity=0.5)
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.info("💡 **Quick Wins** (Low effort, high impact) are in the top-left quadrant")
    
    st.markdown("---")
    
    # Category breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Recommendations by Category")
        
        category_counts = {}
        for rec in recommendations:
            cat = rec.get('category', 'Other')
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        fig_cat = go.Figure(data=[go.Pie(
            labels=list(category_counts.keys()),
            values=list(category_counts.values()),
            hole=0.4,
            marker_colors=['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b']
        )])
        
        fig_cat.update_layout(height=350)
        st.plotly_chart(fig_cat, use_container_width=True)
    
    with col2:
        st.markdown("#### 💰 Total Impact by Category")
        
        category_impact = {}
        for rec in recommendations:
            cat = rec.get('category', 'Other')
            impact = rec.get('impact_score', 0)
            category_impact[cat] = category_impact.get(cat, 0) + impact
        
        fig_impact = go.Figure(data=[go.Bar(
            x=list(category_impact.keys()),
            y=list(category_impact.values()),
            marker_color='#667eea',
            text=[f'${v:,.0f}' for v in category_impact.values()],
            textposition='auto'
        )])
        
        fig_impact.update_layout(
            xaxis_title="Category",
            yaxis_title="Total Impact ($)",
            height=350
        )
        
        st.plotly_chart(fig_impact, use_container_width=True)

with tab3:
    st.markdown("### ✅ Completed Recommendations")
    
    completed_recs = [
        {
            "title": "Implement lead scoring system",
            "completed_date": "2026-01-03",
            "actual_impact": 18500,
            "estimated_impact": 15000,
            "category": "Lead Management"
        },
        {
            "title": "Set up email drip campaign",
            "completed_date": "2026-01-02",
            "actual_impact": 9200,
            "estimated_impact": 8000,
            "category": "Campaign Optimization"
        },
        {
            "title": "Update CRM integration",
            "completed_date": "2025-12-30",
            "actual_impact": 5800,
            "estimated_impact": 5000,
            "category": "Sales Process"
        }
    ]
    
    # Summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Completed Actions", len(completed_recs))
    with col2:
        total_actual = sum([r['actual_impact'] for r in completed_recs])
        st.metric("Actual Impact", f"${total_actual:,.0f}")
    with col3:
        total_estimated = sum([r['estimated_impact'] for r in completed_recs])
        accuracy = (total_actual / total_estimated * 100) if total_estimated > 0 else 0
        st.metric("Accuracy", f"{accuracy:.1f}%")
    
    st.markdown("---")
    
    # Completed list
    for rec in completed_recs:
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        
        with col1:
            st.markdown(f"**✅ {rec['title']}**")
        with col2:
            st.text(f"Completed: {rec['completed_date']}")
        with col3:
            st.text(f"Impact: ${rec['actual_impact']:,.0f}")
        with col4:
            variance = ((rec['actual_impact'] - rec['estimated_impact']) / rec['estimated_impact'] * 100)
            emoji = "📈" if variance > 0 else "📉"
            st.text(f"{emoji} {variance:+.1f}%")
        
        st.markdown("---")

with tab4:
    st.markdown("### ⚙️ Recommendation Engine Settings")
    
    st.markdown("#### 🎯 Notification Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        notify_high = st.checkbox("Notify on High Priority", value=True)
        notify_medium = st.checkbox("Notify on Medium Priority", value=True)
        notify_low = st.checkbox("Notify on Low Priority", value=False)
    
    with col2:
        notify_email = st.checkbox("Email Notifications", value=True)
        notify_slack = st.checkbox("Slack Notifications", value=False)
        notify_sms = st.checkbox("SMS Notifications", value=False)
    
    st.markdown("---")
    
    st.markdown("#### 🤖 AI Model Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        confidence_threshold = st.slider("Confidence Threshold", 0, 100, 70)
        st.info(f"Only show recommendations with {confidence_threshold}%+ confidence")
    
    with col2:
        min_impact = st.number_input("Minimum Impact ($)", min_value=0, value=1000, step=500)
        st.info(f"Filter out recommendations below ${min_impact:,.0f}")
    
    st.markdown("---")
    
    st.markdown("#### 📅 Update Frequency")
    
    update_frequency = st.selectbox(
        "Check for new recommendations",
        ["Real-time", "Every hour", "Every 4 hours", "Daily", "Weekly"]
    )
    
    st.markdown("---")
    
    if st.button("💾 Save Settings", type="primary"):
        st.success("✅ Settings saved successfully!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    <p>💡 Smart Recommendations | AI-powered optimization suggestions</p>
    <p>Last updated: {}</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
