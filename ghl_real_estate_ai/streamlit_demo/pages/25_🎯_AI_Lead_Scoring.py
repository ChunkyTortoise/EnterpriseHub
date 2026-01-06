#!/usr/bin/env python3
"""
🎯 AI-Powered Lead Scoring Demo
================================

Interactive demo of the Predictive Lead Scoring AI service.

Features:
- Real-time lead scoring
- Interactive feature adjustment
- Explainable AI visualization
- Tier assignment
- Action recommendations
"""

import streamlit as st
import sys
from pathlib import Path

# Add services to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services"))

from ai_predictive_lead_scoring import PredictiveLeadScorer, LeadFeatures

# Page config
st.set_page_config(
    page_title="AI Lead Scoring",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 AI-Powered Predictive Lead Scoring")
st.markdown("---")

# Initialize scorer
@st.cache_resource
def get_scorer():
    return PredictiveLeadScorer()

scorer = get_scorer()

# Sidebar - Feature Input
st.sidebar.header("📊 Lead Information")
st.sidebar.markdown("Adjust the values to see real-time scoring")

# Engagement metrics
st.sidebar.subheader("📧 Engagement Metrics")
email_opens = st.sidebar.slider("Email Opens", 0, 20, 8)
email_clicks = st.sidebar.slider("Email Clicks", 0, 15, 5)
emails_sent = st.sidebar.slider("Emails Sent", 1, 25, 10)

# Response behavior
st.sidebar.subheader("⏱️ Response Behavior")
avg_response_time = st.sidebar.slider("Avg Response Time (hours)", 0.0, 72.0, 2.5, 0.5)

# Property interest
st.sidebar.subheader("🏠 Property Interest")
page_views = st.sidebar.slider("Property Page Views", 0, 30, 12)
property_matches = st.sidebar.slider("Matching Properties", 0, 20, 7)

# Financial fit
st.sidebar.subheader("💰 Financial Profile")
budget = st.sidebar.number_input("Budget ($)", 0, 2000000, 500000, 50000)
viewed_prices = st.sidebar.multiselect(
    "Viewed Property Prices",
    options=[400000, 450000, 480000, 495000, 520000, 550000, 600000],
    default=[480000, 520000, 495000]
)

# Timeline
st.sidebar.subheader("📅 Purchase Timeline")
timeline = st.sidebar.select_slider(
    "Timeline",
    options=["exploring", "soon", "immediate"],
    value="soon"
)

# Source
st.sidebar.subheader("📍 Lead Source")
source = st.sidebar.selectbox(
    "Source",
    options=["organic", "referral", "paid", "other"],
    index=0
)

# Communication quality
st.sidebar.subheader("💬 Communication Quality")
message_count = st.sidebar.slider("Messages Sent", 0, 10, 2)
message_quality = st.sidebar.slider("Message Quality", 0.0, 1.0, 0.7, 0.1)

# Build lead data
lead_data = {
    "id": "demo_lead",
    "email_opens": email_opens,
    "email_clicks": email_clicks,
    "emails_sent": emails_sent,
    "response_times": [avg_response_time],
    "page_views": page_views,
    "budget": budget,
    "viewed_property_prices": viewed_prices if viewed_prices else [budget],
    "timeline": timeline,
    "property_matches": property_matches,
    "messages": [{"content": "Sample message " * int(message_quality * 10)}] * message_count,
    "source": source
}

# Score the lead
result = scorer.score_lead("demo_lead", lead_data, include_explanation=True)

# Main display
col1, col2, col3 = st.columns([2, 2, 3])

with col1:
    st.subheader("📊 Lead Score")
    
    # Score gauge
    score_color = "🔴" if result.tier == "cold" else "🟡" if result.tier == "warm" else "🟢"
    st.metric(
        label="Score",
        value=f"{result.score:.1f}/100",
        delta=f"{result.tier.upper()} {score_color}"
    )
    
    # Confidence
    confidence_pct = result.confidence * 100
    st.metric(
        label="Confidence",
        value=f"{confidence_pct:.1f}%"
    )
    
    # Visual gauge
    st.progress(result.score / 100)

with col2:
    st.subheader("🎯 Tier Assignment")
    
    if result.tier == "hot":
        st.success("🔥 **HOT LEAD**")
        st.write("High conversion probability")
    elif result.tier == "warm":
        st.warning("🌤️ **WARM LEAD**")
        st.write("Good potential, needs nurturing")
    else:
        st.info("❄️ **COLD LEAD**")
        st.write("Requires significant engagement")

with col3:
    st.subheader("💡 Top Factors")
    
    for i, factor in enumerate(result.factors[:3], 1):
        sentiment_icon = "✅" if factor['sentiment'] == "positive" else "➖"
        st.write(f"{i}. {sentiment_icon} **{factor['name']}**")
        st.write(f"   {factor['value']}")
        st.progress(factor['impact'] / 25)  # Normalize to 0-1 (max impact ~25%)
        st.write("")

# Recommendations section
st.markdown("---")
st.subheader("🎬 Recommended Actions")

cols = st.columns(2)
for i, rec in enumerate(result.recommendations):
    with cols[i % 2]:
        st.info(rec)

# Detailed analysis
st.markdown("---")
st.subheader("🔍 Detailed Factor Analysis")

# Create tabs for different views
tab1, tab2, tab3 = st.tabs(["📊 All Factors", "📈 Feature Values", "🧪 Test Different Scenarios"])

with tab1:
    st.write("Impact of all scoring factors:")
    
    import pandas as pd
    
    factors_df = pd.DataFrame([
        {
            "Factor": f['name'],
            "Value": f['value'],
            "Impact": f['impact'],
            "Sentiment": f['sentiment']
        }
        for f in result.factors
    ])
    
    if not factors_df.empty:
        st.dataframe(factors_df, use_container_width=True)
        
        # Bar chart
        import plotly.express as px
        fig = px.bar(
            factors_df,
            x="Impact",
            y="Factor",
            orientation='h',
            color="Sentiment",
            title="Factor Impact on Lead Score"
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.write("Current feature values:")
    
    features = scorer.extract_features(lead_data)
    
    feature_data = {
        "Feature": [
            "Engagement Score",
            "Response Time",
            "Page Views",
            "Budget Match",
            "Timeline Urgency",
            "Property Matches",
            "Communication Quality",
            "Source Quality"
        ],
        "Value": [
            f"{features.engagement_score:.2f}",
            f"{features.response_time:.1f} hours",
            str(features.page_views),
            f"{features.budget_match:.2f}",
            features.timeline_urgency,
            str(features.property_matches),
            f"{features.communication_quality:.2f}",
            features.source_quality
        ]
    }
    
    st.table(pd.DataFrame(feature_data))

with tab3:
    st.write("Quick scenario testing:")
    
    scenario_col1, scenario_col2 = st.columns(2)
    
    with scenario_col1:
        if st.button("🔥 Perfect Lead Scenario"):
            st.session_state.scenario = "perfect"
            st.rerun()
        
        if st.button("🌤️ Average Lead Scenario"):
            st.session_state.scenario = "average"
            st.rerun()
    
    with scenario_col2:
        if st.button("❄️ Poor Lead Scenario"):
            st.session_state.scenario = "poor"
            st.rerun()
        
        if st.button("🔄 Reset to Current"):
            if 'scenario' in st.session_state:
                del st.session_state.scenario
            st.rerun()

# API Integration section
st.markdown("---")
st.subheader("🔌 API Integration")

with st.expander("View API Request/Response"):
    st.code(f"""
# API Request
POST /api/ai/lead-score
{{
    "lead_id": "demo_lead",
    "include_explanation": true
}}

# API Response
{{
    "lead_id": "{result.lead_id}",
    "score": {result.score:.2f},
    "confidence": {result.confidence:.3f},
    "tier": "{result.tier}",
    "factors": [
        {{"name": "{result.factors[0]['name']}", "impact": {result.factors[0]['impact']}}},
        ...
    ],
    "recommendations": {result.recommendations[:2]},
    "scored_at": "{result.scored_at.isoformat()}"
}}
""", language="json")

# Footer
st.markdown("---")
st.caption(f"⚡ Scored in < 100ms | Model Confidence: {confidence_pct:.1f}% | Powered by AI")
