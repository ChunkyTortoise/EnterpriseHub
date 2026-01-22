"""
Jorge's AI Seller Bot - Unified Dashboard with Tactical Negotiation
Complete seller automation system integrating:
- 4-Question Qualification Engine
- Vague Answer Detection (Pillar 1)
- Take-Away Close Escalation
- Semantic Response Quality Analysis
- Vapi Voice AI Handoff Integration
- Tone & Compliance Monitoring

Built specifically for Jorge's GHL system.
"""

import streamlit as st
import asyncio
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import sys
import os

# Add the services directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../services'))

# Import Phase 5 CMA Generator
try:
    from ghl_real_estate_ai.agents.cma_generator import CMAGenerator
    from ghl_real_estate_ai.utils.pdf_renderer import PDFRenderer
    CMA_GENERATOR_AVAILABLE = True
except ImportError:
    CMA_GENERATOR_AVAILABLE = False

from ghl_real_estate_ai.streamlit_demo.obsidian_theme import (
    inject_elite_css,
    style_obsidian_chart,
    render_dossier_block,
    render_neural_progress,
    get_svg_icon,
    render_terminal_log,
    render_voice_waveform,
    render_tactical_dock,
    render_journey_line,
    render_biometric_heartbeat,
    render_moat_overlay,
    render_countdown_gauge
)

class JorgeSellerAPIClient:
    """Client for Jorge's Seller Negotiation API."""
    
    async def get_seller_metrics(self) -> Dict[str, Any]:
        return {
            "negotiation_stats": {
                "active_negotiations": 12,
                "qualification_rate": 68.5,
                "avg_motivation_score": 82.4,
                "vague_answers_caught": 45,
                "take_away_closes_triggered": 8,
                "expected_roi_total": 342.5,
                "total_commission_potential": 136700
            },
            "performance": {
                "conversion_rate": 12.5,
                "avg_response_time": "45s",
                "compliance_score": 99.8
            }
        }

    async def get_seller_pipeline(self) -> List[Dict[str, Any]]:
        return [
            {"id": "seller_001", "name": "Robert Miller", "property": "123 Maple St", "score": 92.5, "priority": "immediate", "motivation": "Relocating", "status": "Negotiation Active", "expected_roi": 450, "valuation": 650000},
            {"id": "seller_002", "name": "Linda Garcia", "property": "456 Oak Ave", "score": 78.2, "priority": "high", "motivation": "Upsizing", "status": "Qualification Phase", "expected_roi": 280, "valuation": 425000},
            {"id": "seller_003", "name": "Thomas Wright", "property": "789 Pine Dr", "score": 45.0, "priority": "cold", "motivation": "Just checking", "status": "Dormant", "expected_roi": 110, "valuation": 315000}
        ]

@st.cache_resource
def get_seller_api_client():
    return JorgeSellerAPIClient()

def render_negotiation_simulator():
    """Phase 3 & 4: Predictive Scenario Sliders & Sovereign Pivot."""
    st.markdown('<div class="elite-card" style="padding: 1.5rem;">', unsafe_allow_html=True)
    st.subheader("🎯 Negotiation Simulator")
    
    col1, col2, col3 = st.columns([3, 2, 2])
    
    with col1:
        aggression = st.slider("Aggression Level", 0, 100, 40)
        empathy = st.slider("Empathy Quotient", 0, 100, 75)
        urgency = st.select_slider("Lead Urgency", options=["low", "normal", "high", "critical"])
        
        # Phase 4: AI Strategy Pivot Component
        if aggression > 70 and empathy < 40:
            st.markdown("""
                <div class="pivot-warning-card" style="padding: 1rem; border-radius: 8px; margin-top: 1.5rem;">
                    <div style="color: var(--pivot-warning); font-family: 'Space Grotesk'; font-weight: 700; font-size: 0.7rem; letter-spacing: 0.1em; margin-bottom: 0.5rem;">
                        ⚠️ AI_STRATEGY_PIOT_DETECTED
                    </div>
                    <div style="color: white; font-size: 0.8rem; line-height: 1.4;">
                        High aggression/Low empathy detected. Suggesting <b>Autonomous Pivot</b> to softer tone to prevent deal friction.
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("EXECUTE AUTONOMOUS PIVOT", type="primary", use_container_width=True):
                st.session_state.global_decisions.append({
                    "action": "Strategy Pivot",
                    "why": "High aggression detected. Pivoting to empathy-first protocol.",
                    "time": datetime.now().strftime("%H:%M:%S")
                })
                st.toast("PIVOT EXECUTED: Tone recalibrated to 'Empathy-High'", icon="🧠")
    
    with col2:
        # Close Probability Logic
        prob = (empathy * 0.6) + (aggression * 0.2)
        if urgency == "critical": prob += 20
        prob = min(100, prob)
        
        # Animated Gauge Simulation
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = prob,
            title = {'text': "Close Probability", 'font': {'size': 14, 'color': 'white'}},
            gauge = {
                'axis': {'range': [None, 100], 'tickcolor': "white"},
                'bar': {'color': "#00E5FF"},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 2,
                'bordercolor': "rgba(255,255,255,0.1)",
                'steps': [
                    {'range': [0, 50], 'color': 'rgba(255, 0, 0, 0.1)'},
                    {'range': [50, 80], 'color': 'rgba(255, 255, 0, 0.1)'},
                    {'range': [80, 100], 'color': 'rgba(0, 255, 0, 0.1)'}
                ],
            }
        ))
        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)
        
        render_biometric_heartbeat(urgency=urgency)
    
    with col3:
        # Phase 4: Time-to-Close Clock
        days_map = {"low": 25, "normal": 14, "high": 7, "critical": 2}
        predicted_days = days_map.get(urgency, 14)
        
        # Adjust based on empathy/aggression balance
        if empathy > 80: predicted_days = max(1, predicted_days - 2)
        if aggression > 80: predicted_days += 3
        
        render_countdown_gauge(days_remaining=predicted_days)
        
        st.markdown(f"""
            <div style="text-align: center; padding: 0.5rem; border: 1px solid var(--obsidian-border); border-radius: 8px; background: rgba(255,255,255,0.02);">
                <div style="font-family: 'Space Grotesk'; font-size: 0.6rem; color: var(--negotiation-neon); font-weight: 700;">VELOCITY_SCORE</div>
                <div style="font-size: 1.2rem; font-weight: 800; color: white;">{85 - predicted_days}%</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def render_seller_negotiation_section(api_client: JorgeSellerAPIClient):
    """Render the Seller Negotiation section."""
    st.markdown(f'### {get_svg_icon("negotiation")} Tactical Negotiation Engine', unsafe_allow_html=True)
    
    metrics = asyncio.run(api_client.get_seller_metrics())
    stats = metrics["negotiation_stats"]
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("Active Deals", stats["active_negotiations"])
    with col2: st.metric("Vague Detected", stats["vague_answers_caught"])
    with col3: st.metric("Take-Away Closes", stats["take_away_closes_triggered"])
    with col4: st.metric("ROI Potential", f"{stats['expected_roi_total']}%")
    with col5: st.metric("Comm. Capture", f"${stats['total_commission_potential']//1000}K")
    
    render_negotiation_simulator()

    st.markdown('<div class="elite-card" style="padding: 1.5rem; margin-top: 1.5rem;">', unsafe_allow_html=True)
    st.subheader("🛡️ Zillow-Defense Strategy")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
            <p style="font-size: 0.9rem; color: #8B949E;">
                Generate a branded AI Valuation report to counter the Zestimate. 
                Includes real-time comps and narrative justification.
            </p>
        """, unsafe_allow_html=True)
        if st.button("📊 GENERATE ZILLOW-DEFENSE CMA", type="primary", use_container_width=True):
            if CMA_GENERATOR_AVAILABLE:
                with st.spinner("Decoding Zillow Variance..."):
                    generator = CMAGenerator()
                    # Mocking a property for the demo
                    report = asyncio.run(generator.generate_report("123 Maple St", zestimate=625000))
                    pdf_url = PDFRenderer.generate_pdf_url(report)
                    st.session_state['seller_cma_url'] = pdf_url
                    if 'global_decisions' in st.session_state:
                        st.session_state.global_decisions.append({
                            "action": "Zillow-Defense Active",
                            "why": "Generating competitive CMA to justify higher list price.",
                            "time": datetime.now().strftime("%H:%M:%S")
                        })
                    st.success("✅ CMA Generated Successfully")
            else:
                st.error("CMA Generator not available")

    with col2:
        if 'seller_cma_url' in st.session_state:
            st.markdown(f"""
                <div style="height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                    <a href="{st.session_state['seller_cma_url']}" target="_blank" style="text-decoration: none; width: 100%;">
                        <div style="padding: 1.5rem; background: var(--negotiation-neon); color: black; text-align: center; border-radius: 8px; font-weight: 800; font-family: 'Space Grotesk';">
                            📥 DOWNLOAD SELLER DOSSIER (PDF)
                        </div>
                    </a>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="height: 100%; display: flex; justify-content: center; align-items: center; border: 1px dashed rgba(255,255,255,0.1); border-radius: 8px;">
                    <span style="color: #4B5563; font-size: 0.8rem;">Ready for generation...</span>
                </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_seller_pipeline_section(api_client: JorgeSellerAPIClient):
    """Render the Seller Pipeline."""
    st.markdown(f'### {get_svg_icon("referral")} Seller Pipeline Dossier', unsafe_allow_html=True)
    
    pipeline = asyncio.run(api_client.get_seller_pipeline())
    
    for seller in pipeline:
        with st.container():
            st.markdown(f'<div class="elite-card" style="padding: 1.25rem; margin-bottom: 1rem;">', unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            
            with col1:
                st.markdown(f"**🏠 {seller['property']}**")
                st.caption(f"Seller: {seller['name']} | Motivation: {seller['motivation']}")
            
            with col2:
                temp = "hot" if seller['priority'] == "immediate" else "warm" if seller['priority'] == "high" else "cold"
                render_journey_line(temperature=temp, progress=seller['score'])
            
            with col3:
                st.markdown(f"""
                    <div style='text-align: center; border-left: 1px solid rgba(255,255,255,0.1);'>
                        <span style='font-size: 0.6rem; color: #8B949E;'>ROI_YIELD</span><br>
                        <span style='font-size: 1rem; font-weight: 700; color: #00E5FF;'>{seller['expected_roi']}%</span>
                    </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown(f"""
                    <div style='text-align: right;'>
                        <span style='font-size: 1.2rem; font-weight: bold; color: white;'>${seller['valuation']//1000}K</span><br>
                        <span style='font-size: 0.6rem; color: #8B949E;'>AI_VALUATION</span>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

def render_jorge_seller_bot_dashboard():
    """Main function to render Jorge's Seller Bot Dashboard."""
    inject_elite_css()
    
    # MOAT Overlay Toggle
    moat_active = st.sidebar.checkbox("Activate MOAT Security", value=True)
    render_moat_overlay(active=moat_active)
    
    st.markdown("""
        <div style="background: var(--obsidian-card); backdrop-filter: var(--glass-blur); padding: 1.5rem 2.5rem; border-radius: 16px; border: 0.5px solid var(--obsidian-border); border-top: 1px solid rgba(255, 255, 255, 0.12); margin-bottom: 2.5rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);">
            <div>
                <h1 style="font-family: 'Space Grotesk', sans-serif; font-size: 2.5rem; font-weight: 700; margin: 0; color: #FFFFFF; letter-spacing: -0.04em; text-transform: uppercase;">💼 SELLER COMMAND</h1>
                <p style="font-family: 'Inter', sans-serif; font-size: 1rem; margin: 0.5rem 0 0 0; color: #8B949E; font-weight: 500; letter-spacing: 0.02em;">Obsidian Command // Tactical Seller Intelligence v4.2.0</p>
            </div>
            <div style="text-align: right;">
                <div class="status-pulse" style="background: #00E5FF; box-shadow: 0 0 10px #00E5FF;"></div>
                <span style="color: #00E5FF; font-weight: 800; letter-spacing: 0.1em;">NEGOTIATION ACTIVE</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    api_client = get_seller_api_client()
    
    tab1, tab2, tab3 = st.tabs(["🎯 Negotiation", "📊 Pipeline", "🛡️ Compliance"])
    
    with tab1: render_seller_negotiation_section(api_client)
    with tab2: render_seller_pipeline_section(api_client)
    with tab3:
        st.markdown('<div class="elite-card" style="padding: 1.5rem;">', unsafe_allow_html=True)
        st.subheader("Security & Compliance")
        render_dossier_block("MOAT scrubbing active. All PII data is anonymized before neural processing.", title="DATA_SECURITY_REPORT")
        st.markdown('</div>', unsafe_allow_html=True)

    # Terminal
    render_terminal_log([
        {"prefix": "[NEGOTIATION]", "message": "Vague answer detected for Robert Miller. Pillar 1 logic engaged."},
        {"prefix": "[STRATEGY]", "message": "Triggering Take-Away close for 123 Maple St."},
        {"prefix": "[MOAT]", "message": "PII scrubbing successful for session S-9921."}
    ])
    
    render_tactical_dock()

if __name__ == "__main__":
    render_jorge_seller_bot_dashboard()
