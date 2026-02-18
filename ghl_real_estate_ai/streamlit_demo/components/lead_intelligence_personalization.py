"""
Lead Intelligence Personalization Component
"Hyper-Personalization Dashboard" - DNA Analysis & Content Generation
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import random
from datetime import datetime

def render_personalization_tab(lead_data: dict = None):
    """
    Renders the 'Personalization' tab within the Lead Intelligence Hub.
    
    Args:
        lead_data (dict): Optional lead data to pre-populate.
    """
    if not lead_data:
        lead_data = {
            "name": "Sarah Johnson",
            "persona": "Analytical Buyer",
            "disc_profile": "C-Type (Conscientious)",
            "communication_style": "Direct & Detail-oriented",
            "interests": ["School districts", "Property value trends", "HOA definitions"],
            "last_interaction": "Asked about price/sqft in downtown"
        }

    st.markdown("### 🧬 Lead DNA & Personalization Engine")
    
    # Top "DNA" Card
    _render_dna_card(lead_data)
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 🧠 Psychographic Profile")
        _render_psychographics(lead_data)
        
    with col2:
        st.markdown("#### 🎨 Content Generator")
        _render_content_generator(lead_data)

def _render_dna_card(lead_data):
    """Renders the high-level 'DNA' summary of the lead."""
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); 
                padding: 1.5rem; border-radius: 12px; border-left: 5px solid #3b82f6;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);'>
        <div style='display: flex; align-items: center; justify-content: space-between;'>
            <div>
                <h3 style='margin: 0; color: #1e293b;'>{lead_data['name']}</h3>
                <p style='margin: 0; color: #64748b; font-size: 0.9rem;'>
                    {lead_data['persona']} • {lead_data['disc_profile']}
                </p>
                <div style='margin-top: 0.5rem; display: flex; gap: 0.5rem;'>
                    {''.join([f"<span style='background: #bfdbfe; color: #1e40af; padding: 0.2rem 0.6rem; border-radius: 999px; font-size: 0.75rem;'>{tag}</span>" for tag in lead_data['interests']])}
                </div>
            </div>
            <div style='text-align: right;'>
                <div style='font-size: 2.5rem;'>🧬</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def _render_psychographics(lead_data):
    """Renders visual psychographic traits."""
    
    # Mock data for radar chart
    categories = ['Price Sensitivity', 'Urgency', 'Feature Focus', 'Brand Loyalty', 'response_rate']
    values = [8, 4, 9, 3, 7]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        line_color='#3b82f6',
        fillcolor='rgba(59, 130, 246, 0.2)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )),
        showlegend=False,
        height=300,
        margin=dict(l=40, r=40, t=20, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.info(f"💡 **Insight**: {lead_data['name']} responds best to data-driven arguments. Avoid fluff; focus on investment value and specs.")

def _render_content_generator(lead_data):
    """Renders the AI content generator with tone adjustment."""
    st.markdown("Generate personalized outreach based on DNA.")
    
    channel = st.selectbox("Channel", ["Email", "SMS", "Script"], index=0)
    tone = st.select_slider("Tone", options=["Strictly Professional", "Helpful/Polite", "Casual/Friendly", "Hype/Excited"], value="Helpful/Polite")
    topic = st.text_input("Topic", value="Market Update for Q1")
    
    if st.button("✨ Generate Content", type="primary"):
        with st.spinner("Analyzing DNA and drafting..."):
            # Mock generation
            import time
            time.sleep(1.0)
            
            if tone == "Strictly Professional":
                content = f"Dear {lead_data['name']},\n\nRegarding your interest in {lead_data['interests'][0] if lead_data['interests'] else 'real estate'}, I have compiled the Q1 market data you requested. Please review the attached report focusing on value trends."
            elif tone == "Casual/Friendly":
                content = f"Hey {lead_data['name']}! 👋\n\nSaw you were checking out {lead_data['interests'][0]} lately. The new Q1 numbers just dropped and I thought of you—looks like prices are trending your way!"
            else:
                content = f"Hi {lead_data['name']},\n\nI wanted to share a quick update on the Q1 market trends, specifically regarding {lead_data['interests'][0]}. Given your focus on value, I think you'll find these numbers interesting."
            
            st.text_area("Generated Draft", value=content, height=150)
            
            col_copy, col_send = st.columns(2)
            with col_copy:
                st.button("📋 Copy", key="copy_btn")
            with col_send:
                st.button("🚀 Send to Drafts", key="send_btn")

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    render_personalization_tab()
