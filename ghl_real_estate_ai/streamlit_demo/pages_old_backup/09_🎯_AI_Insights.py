"""
AI Insights Dashboard - Wow Feature Integration
Shows intelligent insights for all leads
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ai_lead_insights import AILeadInsightsService

# Page config
st.set_page_config(page_title="AI Insights", page_icon="🎯", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .insight-card {
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid;
    }
    .opportunity { border-left-color: #10B981; background: #F0FDF4; }
    .risk { border-left-color: #EF4444; background: #FEF2F2; }
    .action { border-left-color: #F59E0B; background: #FFFBEB; }
    .prediction { border-left-color: #3B82F6; background: #EFF6FF; }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1E3A8A;
    }
    .metric-label {
        font-size: 0.875rem;
        color: #6B7280;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🎯 AI Lead Insights Dashboard")
st.markdown("**Powered by Predictive Intelligence**")

# Initialize service
insights_service = AILeadInsightsService()

# Sidebar filters
st.sidebar.header("Filters")
tenant_id = st.sidebar.selectbox("Tenant", ["Jorge's Team", "North Miami Office", "Downtown Branch"])
date_range = st.sidebar.date_input("Date Range", value=(datetime.now() - timedelta(days=7), datetime.now()))
priority_filter = st.sidebar.multiselect("Priority", [1, 2, 3, 4, 5], default=[1, 2, 3])

# Demo data - in production this would come from database
def generate_demo_leads():
    return [
        {
            'lead_id': 'L001',
            'name': 'Maria Rodriguez',
            'conversations': [
                {'sender': 'agent', 'message': 'Hey! Looking to buy or sell?', 'timestamp': '2026-01-05T10:00:00'},
                {'sender': 'lead', 'message': 'Selling ASAP. Need cash offer.', 'timestamp': '2026-01-05T10:02:00'},
                {'sender': 'agent', 'message': 'Perfect! When can we view?', 'timestamp': '2026-01-05T10:03:00'},
                {'sender': 'lead', 'message': 'Tomorrow. This is urgent.', 'timestamp': '2026-01-05T10:05:00'},
            ],
            'score': 8.5,
            'metadata': {
                'lead_id': 'L001',
                'answered_questions': 6,
                'budget': 400000,
                'location': 'Miami Beach',
                'timeline': 'immediate'
            }
        },
        {
            'lead_id': 'L002',
            'name': 'Carlos Mendez',
            'conversations': [
                {'sender': 'agent', 'message': 'Hey! Still interested?', 'timestamp': '2026-01-03T14:00:00'},
                {'sender': 'lead', 'message': 'Maybe. Looking at other options too', 'timestamp': '2026-01-03T14:30:00'},
            ],
            'score': 5.2,
            'metadata': {
                'lead_id': 'L002',
                'answered_questions': 2,
                'budget': 250000,
                'location': 'Kendall'
            }
        },
        {
            'lead_id': 'L003',
            'name': 'Jennifer Smith',
            'conversations': [
                {'sender': 'agent', 'message': 'Hey Jennifer! Quick question about Doral properties', 'timestamp': '2026-01-04T09:00:00'},
                {'sender': 'lead', 'message': 'Yes! Send me what you have. Need 3 beds, good schools.', 'timestamp': '2026-01-04T09:05:00'},
                {'sender': 'agent', 'message': 'Perfect. What\'s your timeline?', 'timestamp': '2026-01-04T09:06:00'},
                {'sender': 'lead', 'message': 'Next 2 months. Already pre-approved.', 'timestamp': '2026-01-04T09:08:00'},
            ],
            'score': 7.8,
            'metadata': {
                'lead_id': 'L003',
                'answered_questions': 5,
                'budget': 500000,
                'location': 'Doral',
                'timeline': '60_days',
                'preapproval': True
            }
        }
    ]

demo_leads = generate_demo_leads()

# Generate insights for all leads
all_insights = []
for lead in demo_leads:
    lead_insights = insights_service.analyze_lead(lead)
    for insight in lead_insights:
        insight_dict = insight.to_dict()
        insight_dict['lead_name'] = lead['name']
        all_insights.append(insight_dict)

# Summary metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class='metric-card'>
        <div class='metric-value'>🔥 {}</div>
        <div class='metric-label'>High Priority Insights</div>
    </div>
    """.format(len([i for i in all_insights if i['priority'] == 1])), unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class='metric-card'>
        <div class='metric-value'>💰 {}</div>
        <div class='metric-label'>Revenue Opportunities</div>
    </div>
    """.format(len([i for i in all_insights if i['insight_type'] == 'opportunity'])), unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class='metric-card'>
        <div class='metric-value'>⚠️ {}</div>
        <div class='metric-label'>Risk Alerts</div>
    </div>
    """.format(len([i for i in all_insights if i['insight_type'] == 'risk'])), unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class='metric-card'>
        <div class='metric-value'>📊 {}</div>
        <div class='metric-label'>Total Insights</div>
    </div>
    """.format(len(all_insights)), unsafe_allow_html=True)

st.markdown("---")

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["🔥 Priority Insights", "📊 All Insights", "📈 Analytics"])

with tab1:
    st.subheader("Priority Actions Needed")
    
    priority_insights = [i for i in all_insights if i['priority'] in [1, 2]]
    priority_insights.sort(key=lambda x: (x['priority'], -x['confidence']))
    
    if priority_insights:
        for insight in priority_insights:
            icon = "🔥" if insight['priority'] == 1 else "⚠️"
            card_class = {
                'opportunity': 'opportunity',
                'risk': 'risk',
                'action': 'action',
                'prediction': 'prediction'
            }.get(insight['insight_type'], 'action')
            
            st.markdown(f"""
            <div class='insight-card {card_class}'>
                <h3>{icon} {insight['title']}</h3>
                <p><strong>Lead:</strong> {insight['lead_name']}</p>
                <p>{insight['description']}</p>
                <p><strong>🎯 Recommended Action:</strong> {insight['recommended_action']}</p>
                <p><small>Confidence: {insight['confidence']*100:.0f}% | Impact: {insight['estimated_impact']}</small></p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No high-priority insights at this time. Great job staying on top of leads!")

with tab2:
    st.subheader("All Insights")
    
    # Filter by insight type
    insight_type_filter = st.multiselect(
        "Filter by Type",
        ["opportunity", "risk", "action", "prediction"],
        default=["opportunity", "risk", "action", "prediction"]
    )
    
    filtered_insights = [i for i in all_insights if i['insight_type'] in insight_type_filter]
    
    for insight in filtered_insights:
        with st.expander(f"{insight['title']} - {insight['lead_name']}", expanded=False):
            col_a, col_b = st.columns([2, 1])
            
            with col_a:
                st.markdown(f"**Description:** {insight['description']}")
                st.markdown(f"**Recommended Action:** {insight['recommended_action']}")
            
            with col_b:
                st.metric("Confidence", f"{insight['confidence']*100:.0f}%")
                st.metric("Priority", f"P{insight['priority']}")
                st.metric("Impact", insight['estimated_impact'])

with tab3:
    st.subheader("Insights Analytics")
    
    # Insights by type
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("**Insights by Type**")
        insight_types = pd.DataFrame([
            {'Type': i['insight_type'].title(), 'Count': 1} 
            for i in all_insights
        ]).groupby('Type').count().reset_index()
        st.bar_chart(insight_types.set_index('Type'))
    
    with col_chart2:
        st.markdown("**Insights by Priority**")
        priorities = pd.DataFrame([
            {'Priority': f"P{i['priority']}", 'Count': 1} 
            for i in all_insights
        ]).groupby('Priority').count().reset_index()
        st.bar_chart(priorities.set_index('Priority'))
    
    # Average confidence
    avg_confidence = sum(i['confidence'] for i in all_insights) / len(all_insights) if all_insights else 0
    st.metric("Average Confidence Score", f"{avg_confidence*100:.1f}%")
    
    st.info("💡 **Pro Tip:** Sort leads by closing probability each morning and work from top to bottom for maximum efficiency.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6B7280; padding: 2rem;'>
    <p><strong>🎯 AI Lead Insights</strong> | Powered by Machine Learning</p>
    <p style='font-size: 0.875rem;'>Analyzing conversation patterns, engagement signals, and behavioral indicators to predict outcomes</p>
</div>
""", unsafe_allow_html=True)
