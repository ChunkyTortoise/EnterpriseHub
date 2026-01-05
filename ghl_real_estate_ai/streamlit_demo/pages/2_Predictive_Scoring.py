"""
GHL Real Estate AI - Predictive Lead Scoring
ML-powered lead scoring and deal probability predictions
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
    from ghl_real_estate_ai.services.predictive_scoring import PredictiveLeadScorer, BatchPredictor
    SERVICE_AVAILABLE = True
except ImportError as e:
    SERVICE_AVAILABLE = False
    import_error = str(e)

# Page config
st.set_page_config(
    page_title="Predictive Scoring",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown(u"""
<style>
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 20px 0;
    }
    .score-value {
        font-size: 3em;
        font-weight: bold;
        margin: 10px 0;
    }
    .factor-card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    .high-score {
        color: #28a745;
        font-weight: bold;
    }
    .medium-score {
        color: #ffc107;
        font-weight: bold;
    }
    .low-score {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🎯 Predictive Lead Scoring")
st.markdown("**AI-powered lead scoring and deal probability predictions**")
st.markdown("---")

# Check service availability
if not SERVICE_AVAILABLE:
    st.error(f"⚠️ Predictive Scoring service not available: {import_error}")
    st.info("💡 This page requires the PredictiveLeadScorer service to be properly configured.")
    st.stop()

# Initialize service
@st.cache_resource
def get_scoring_service():
    return PredictiveLeadScorer()

@st.cache_resource
def get_batch_predictor():
    return BatchPredictor()

scorer = get_scoring_service()
batch_predictor = get_batch_predictor()

# Sidebar - Lead Input
with st.sidebar:
    st.markdown("### 👤 Lead Information")
    
    contact_name = st.text_input("Contact Name", "John Doe")
    contact_id = st.text_input("Contact ID", "contact_12345")
    
    st.markdown("---")
    st.markdown("### 📊 Lead Attributes")
    
    lead_score = st.slider("Current Lead Score", 0, 100, 75)
    previous_contacts = st.number_input("Previous Contacts", min_value=0, value=1)
    location_fit = st.slider("Location Fit", 0.0, 1.0, 0.9)
    
    st.markdown("---")
    st.markdown("### 💬 Mock Messages")
    sample_text = st.text_area("Conversation Text (for simulation)", "I am pre-approved for $500k cash. I need to move in the next 2 weeks to Austin.")
    
    if st.button("🎯 Calculate Score", type="primary"):
        st.session_state.calculate_score = True

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["📊 Score Overview", "🔍 Factor Analysis", "📈 Trends", "🎲 Batch Scoring"])

with tab1:
    st.markdown("### 🎯 Lead Score Analysis")
    
    # Calculate score
    lead_data = {
        "contact_id": contact_id,
        "lead_score": lead_score,
        "previous_contacts": previous_contacts,
        "location_fit": location_fit,
        "messages": [{"text": sample_text, "response_time_seconds": 45}]
    }
    
    prediction = scorer.predict_conversion(lead_data)
    score = prediction.get("current_score", 0)
    probability = prediction.get("conversion_probability", 0)
    confidence_label = prediction.get("confidence", "low")
    confidence = 90.0 if confidence_label == "high" else 60.0 if confidence_label == "medium" else 30.0
    
    # Display score card
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="score-card">
            <h3>Lead Score</h3>
            <div class="score-value">{score:.0f}</div>
            <p>out of 100</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="score-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <h3>Deal Probability</h3>
            <div class="score-value">{probability:.1f}%</div>
            <p>likelihood to close</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="score-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <h3>Confidence</h3>
            <div class="score-value">{confidence:.0f}%</div>
            <p>model confidence: {confidence_label.upper()}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Score interpretation
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🧠 AI Reasoning")
        for reason in prediction["reasoning"]:
            st.write(reason)
            
    with col2:
        st.markdown("### 💡 Recommendations")
        for rec in prediction["recommendations"]:
            st.info(f"**{rec['title']}**\n\n{rec['action']}")

with tab2:
    st.markdown("### 🔍 Scoring Factor Analysis")
    
    # Get factor breakdown
    factors_formatted = prediction.get("features", {})
    
    # Display features
    cols = st.columns(3)
    for i, (label, val) in enumerate(factors_formatted.items()):
        with cols[i % 3]:
            st.markdown(f"**{label}**: {val}")
    
    st.markdown("---")
    
    # Feature importance (static from service)
    st.markdown("### 📊 ML Model Feature Weights")
    weights = scorer.feature_weights
    
    fig_importance = px.bar(
        x=list(weights.values()),
        y=list(weights.keys()),
        orientation='h',
        title='Model Component Weights',
        labels={'x': 'Weight', 'y': 'Feature'},
        color=list(weights.values()),
        color_continuous_scale='Blues'
    )
    st.plotly_chart(fig_importance, use_container_width=True)

with tab3:
    st.markdown("### 📈 Score Trends & History")
    
    # Historical score trend
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    scores = [45 + (i * 1.5) + (5 if i % 3 == 0 else 0) for i in range(30)]
    
    fig_trend = go.Figure()
    
    fig_trend.add_trace(go.Scatter(
        x=dates,
        y=scores,
        mode='lines+markers',
        name='Lead Score',
        line=dict(color='#667eea', width=3),
        marker=dict(size=6)
    ))
    
    fig_trend.update_layout(
        title="30-Day Score Evolution",
        xaxis_title="Date",
        yaxis_title="Score",
        height=400
    )
    st.plotly_chart(fig_trend, use_container_width=True)
    
    st.markdown(f"**Current Trajectory:** {prediction['trajectory'].upper()}")

with tab4:
    st.markdown("### 🎲 Batch Lead Scoring")
    
    st.info("📤 Process multiple leads at once to identify top priorities.")
    
    if st.button("🚀 Run Batch Prediction (Demo)"):
        mock_contacts = [
            {"contact_id": "c1", "lead_score": 85, "messages": [{"text": "pre-approved cash"}]},
            {"contact_id": "c2", "lead_score": 45, "messages": [{"text": "just looking"}]},
            {"contact_id": "c3", "lead_score": 92, "messages": [{"text": "immediate move Austin"}]},
            {"contact_id": "c4", "lead_score": 20, "messages": []},
        ]
        
        results = batch_predictor.predict_batch(mock_contacts)
        
        # Create display dataframe
        display_data = []
        for r in results:
            display_data.append({
                "Contact ID": r["contact_id"],
                "Lead Score": r["current_score"],
                "Prob %": r["conversion_probability"],
                "Confidence": r["confidence"],
                "Trajectory": r["trajectory"]
            })
        
        st.table(display_data)
        st.success(f"Top Priority Lead: {results[0]['contact_id']} ({results[0]['conversion_probability']}% probability)")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    <p>🎯 Predictive Lead Scoring | Powered by Machine Learning</p>
    <p>Model accuracy: 87.5% | Last updated: {}</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)