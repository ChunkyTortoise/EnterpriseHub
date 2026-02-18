"""
Lead Intelligence Predictions Component
"Future Sight" - Predictive Scoring & Churn Analysis
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import random
from datetime import datetime, timedelta

def render_predictions_tab(lead_data: dict = None):
    """
    Renders the 'Predictions' tab within the Lead Intelligence Hub.
    
    Args:
        lead_data (dict): Optional lead data to pre-populate.
    """
    if not lead_data:
        lead_data = {
            "name": "Sarah Johnson",
            "score": 87,
            "confidence": 0.92,
            "churn_risk": "Low",
            "predicted_close_date": "2026-02-15"
        }

    st.markdown("### 🔮 Predictive AI & Future Outcomes")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Score Gauge Card
        st.markdown(f"""
        <div style='background: white; padding: 1rem; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; border: 1px solid #e2e8f0;'>
            <h4 style='margin:0; color:#64748b;'>Conversion Probability</h4>
            <div style='font-size: 3.5rem; font-weight: 800; color: #10b981;'>{lead_data['score']}%</div>
            <div style='font-size: 0.8rem; color: #64748b;'>Confidence: {int(lead_data['confidence']*100)}%</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Churn Risk Alert
        risk_color = "#10b981" if lead_data['churn_risk'] == "Low" else "#ef4444"
        st.markdown(f"""
        <div style='margin-top: 1rem; background: {risk_color}10; padding: 1rem; border-radius: 12px; border: 1px solid {risk_color};'>
            <div style='font-weight: 700; color: {risk_color};'>⚠️ Churn Risk: {lead_data['churn_risk']}</div>
            <div style='font-size: 0.8rem; margin-top:0.5rem;'>Monitor communication frequency to maintain interest.</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Timeline Prediction
        st.markdown("#### 📅 Predicted Timeline to Close")
        _render_timeline_prediction(lead_data)

    st.markdown("---")
    
    # Detailed Factor Analysis (Shapeley Values style)
    st.markdown("#### 📊 Why this score? (Explainable AI)")
    _render_factor_analysis()

def _render_timeline_prediction(lead_data):
    """Renders a gantt-like timeline for predicted milestones."""
    
    # Mock milestones
    milestones = [
        dict(Task="Engagement", Start='2026-01-01', Finish='2026-01-10', Completion=100),
        dict(Task="Pre-Approval", Start='2026-01-12', Finish='2026-01-20', Completion=80),
        dict(Task="Property Tours", Start='2026-01-22', Finish='2026-02-05', Completion=20),
        dict(Task="Offer Submission", Start='2026-02-06', Finish='2026-02-14', Completion=0),
        dict(Task="Closing", Start='2026-02-28', Finish='2026-03-30', Completion=0)
    ]
    
    df = pd.DataFrame(milestones)
    
    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Completion", color_continuous_scale="Teal")
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

def _render_factor_analysis():
    """Renders a waterfall or bar chart showing positive/negative factors."""
    factors = [
        {"name": "Email Opens", "impact": +15},
        {"name": "Property Views", "impact": +12},
        {"name": "Slow Response", "impact": -8},
        {"name": "Budget Match", "impact": +5},
        {"name": "Time on Site", "impact": +3}
    ]
    
    # Sort for visual clarity
    factors.sort(key=lambda x: x['impact'], reverse=True)
    
    names = [f['name'] for f in factors]
    impacts = [f['impact'] for f in factors]
    colors = ['#10b981' if x > 0 else '#ef4444' for x in impacts]
    
    fig = go.Figure(go.Bar(
        x=impacts,
        y=names,
        orientation='h',
        marker_color=colors
    ))
    
    fig.update_layout(
        title="",
        xaxis_title="Score Impact",
        height=300,
        margin=dict(l=10, r=10, t=30, b=10)
    )
    
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    render_predictions_tab()
