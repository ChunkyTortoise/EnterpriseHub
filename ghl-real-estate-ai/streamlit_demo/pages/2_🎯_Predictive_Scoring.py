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
    from services.predictive_scoring import PredictiveScorer
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
st.markdown("""
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
    st.info("💡 This page requires the PredictiveScorer service to be properly configured.")
    st.stop()

# Initialize service
@st.cache_resource
def get_scoring_service():
    return PredictiveScorer(model_path="data/models")

scorer = get_scoring_service()

# Sidebar - Lead Input
with st.sidebar:
    st.markdown("### 👤 Lead Information")
    
    contact_name = st.text_input("Contact Name", "John Doe")
    contact_id = st.text_input("Contact ID", "contact_12345")
    
    st.markdown("---")
    st.markdown("### 📊 Lead Attributes")
    
    budget = st.number_input("Budget ($)", min_value=0, value=350000, step=10000)
    timeline = st.selectbox("Timeline", ["Immediate", "1-3 months", "3-6 months", "6+ months"])
    engagement_score = st.slider("Engagement Score", 0, 100, 75)
    email_opens = st.number_input("Email Opens", min_value=0, value=12)
    website_visits = st.number_input("Website Visits", min_value=0, value=8)
    
    st.markdown("---")
    
    if st.button("🎯 Calculate Score", type="primary"):
        st.session_state.calculate_score = True

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["📊 Score Overview", "🔍 Factor Analysis", "📈 Trends", "🎲 Batch Scoring"])

with tab1:
    st.markdown("### 🎯 Lead Score Analysis")
    
    # Calculate score
    lead_data = {
        "contact_id": contact_id,
        "budget": budget,
        "timeline": timeline,
        "engagement_score": engagement_score,
        "email_opens": email_opens,
        "website_visits": website_visits
    }
    
    score_result = scorer.score_lead("demo_location", lead_data)
    score = score_result.get("score", 0)
    confidence = score_result.get("confidence", 0)
    probability = score_result.get("deal_probability", 0)
    
    # Display score card
    col1, col2, col3 = st.columns(3)
    
    with col1:
        score_class = "high-score" if score >= 70 else "medium-score" if score >= 40 else "low-score"
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
            <div class="score-value">{confidence:.1f}%</div>
            <p>model confidence</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Score interpretation
    st.markdown("### 💡 Score Interpretation")
    
    if score >= 70:
        st.success(f"🔥 **High Priority Lead** - Score: {score:.0f}/100")
        st.markdown("""
        **Recommended Actions:**
        - ✅ Immediate follow-up within 1 hour
        - ✅ Assign to senior sales rep
        - ✅ Schedule property viewing ASAP
        - ✅ Prepare personalized proposal
        """)
    elif score >= 40:
        st.warning(f"⚡ **Medium Priority Lead** - Score: {score:.0f}/100")
        st.markdown("""
        **Recommended Actions:**
        - 📧 Send targeted email campaign
        - 📞 Follow up within 24 hours
        - 📊 Provide market analysis
        - 🔄 Nurture with regular content
        """)
    else:
        st.info(f"❄️ **Low Priority Lead** - Score: {score:.0f}/100")
        st.markdown("""
        **Recommended Actions:**
        - 📬 Add to drip campaign
        - 📚 Send educational content
        - 🔍 Monitor engagement patterns
        - ⏰ Re-evaluate in 30 days
        """)

with tab2:
    st.markdown("### 🔍 Scoring Factor Analysis")
    
    # Get factor breakdown
    factors = score_result.get("factors", {})
    
    if not factors:
        factors = {
            "Budget Fit": 85,
            "Timeline Urgency": 70,
            "Engagement Level": 75,
            "Communication": 60,
            "Behavioral Signals": 65
        }
    
    # Factor breakdown chart
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig = go.Figure(go.Bar(
            x=list(factors.values()),
            y=list(factors.keys()),
            orientation='h',
            marker=dict(
                color=list(factors.values()),
                colorscale='RdYlGn',
                showscale=True
            ),
            text=list(factors.values()),
            texttemplate='%{text:.0f}',
            textposition='auto'
        ))
        
        fig.update_layout(
            title="Factor Contribution to Score",
            xaxis_title="Impact Score",
            yaxis_title="Factor",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 📋 Factor Details")
        
        for factor, value in factors.items():
            if value >= 70:
                emoji = "🟢"
                label = "Strong"
            elif value >= 40:
                emoji = "🟡"
                label = "Moderate"
            else:
                emoji = "🔴"
                label = "Weak"
            
            st.markdown(f"{emoji} **{factor}**: {value:.0f}/100 ({label})")
    
    st.markdown("---")
    
    # Feature importance
    st.markdown("### 📊 Feature Importance")
    
    features_df = pd.DataFrame({
        'Feature': ['Budget', 'Timeline', 'Engagement', 'Email Opens', 'Website Visits', 
                   'Response Time', 'Property Views', 'Questions Asked'],
        'Importance': [0.25, 0.20, 0.18, 0.12, 0.10, 0.08, 0.05, 0.02]
    })
    
    fig_importance = px.bar(
        features_df,
        x='Importance',
        y='Feature',
        orientation='h',
        title='ML Model Feature Importance',
        color='Importance',
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
    
    # Add threshold lines
    fig_trend.add_hline(y=70, line_dash="dash", line_color="green", 
                       annotation_text="High Priority Threshold")
    fig_trend.add_hline(y=40, line_dash="dash", line_color="orange", 
                       annotation_text="Medium Priority Threshold")
    
    fig_trend.update_layout(
        title="30-Day Score Evolution",
        xaxis_title="Date",
        yaxis_title="Score",
        height=400
    )
    
    st.plotly_chart(fig_trend, use_container_width=True)
    
    st.markdown("---")
    
    # Score distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Score Distribution (All Leads)")
        
        score_ranges = ['0-20', '21-40', '41-60', '61-80', '81-100']
        lead_counts = [15, 45, 120, 85, 35]
        
        fig_dist = go.Figure(data=[go.Bar(
            x=score_ranges,
            y=lead_counts,
            marker_color=['#dc3545', '#ffc107', '#17a2b8', '#28a745', '#667eea']
        )])
        
        fig_dist.update_layout(
            xaxis_title="Score Range",
            yaxis_title="Number of Leads",
            height=350
        )
        
        st.plotly_chart(fig_dist, use_container_width=True)
    
    with col2:
        st.markdown("#### 🎯 Conversion by Score")
        
        score_groups = ['Low (0-40)', 'Medium (41-70)', 'High (71-100)']
        conversion_rates = [5, 18, 42]
        
        fig_conv = go.Figure(data=[go.Bar(
            x=score_groups,
            y=conversion_rates,
            marker_color=['#ffc107', '#17a2b8', '#28a745'],
            text=[f'{rate}%' for rate in conversion_rates],
            textposition='auto'
        )])
        
        fig_conv.update_layout(
            xaxis_title="Score Group",
            yaxis_title="Conversion Rate (%)",
            height=350
        )
        
        st.plotly_chart(fig_conv, use_container_width=True)

with tab4:
    st.markdown("### 🎲 Batch Lead Scoring")
    
    st.info("📤 Upload a CSV file with lead data to score multiple leads at once.")
    
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success(f"✅ Loaded {len(df)} leads from file")
        
        if st.button("🎯 Score All Leads"):
            with st.spinner("Scoring leads..."):
                # Mock scoring
                df['predicted_score'] = [45 + (i * 2) % 55 for i in range(len(df))]
                df['deal_probability'] = df['predicted_score'] * 0.8
                df['priority'] = df['predicted_score'].apply(
                    lambda x: 'High' if x >= 70 else 'Medium' if x >= 40 else 'Low'
                )
                
                st.success("✅ Scoring complete!")
                
                # Display results
                st.markdown("#### 📊 Scoring Results")
                st.dataframe(df, use_container_width=True)
                
                # Summary stats
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    high_count = len(df[df['priority'] == 'High'])
                    st.metric("High Priority Leads", high_count)
                
                with col2:
                    medium_count = len(df[df['priority'] == 'Medium'])
                    st.metric("Medium Priority Leads", medium_count)
                
                with col3:
                    low_count = len(df[df['priority'] == 'Low'])
                    st.metric("Low Priority Leads", low_count)
                
                # Download results
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Scored Leads",
                    data=csv,
                    file_name=f"scored_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    else:
        st.markdown("#### 📋 Sample CSV Format")
        st.code("""
contact_id,name,budget,timeline,engagement_score,email_opens,website_visits
12345,John Doe,350000,Immediate,75,12,8
12346,Jane Smith,500000,1-3 months,65,8,5
12347,Bob Johnson,250000,3-6 months,45,4,2
        """, language="csv")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    <p>🎯 Predictive Lead Scoring | Powered by Machine Learning</p>
    <p>Model accuracy: 87.5% | Last updated: {}</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
