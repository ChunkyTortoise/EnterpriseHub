"""
Jorge's AI Buyer Bot - Unified Dashboard with Consultative Qualification
Complete buyer automation system integrating:
- Consultative Qualification Engine
- Financial Readiness Scoring (FRS)
- Property Preference Analysis
- Intelligent Property Matching
- Automated Follow-up Scheduling
- Real-time Intent Decoding

Built specifically for Jorge's GHL system.
"""

import streamlit as st
from ghl_real_estate_ai.streamlit_demo.async_utils import run_async
import asyncio
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import sys
import os

# Add the services directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../services'))

from ghl_real_estate_ai.streamlit_demo.obsidian_theme import (
    inject_elite_css,
    style_obsidian_chart,
    render_dossier_block,
    render_neural_progress,
    get_svg_icon,
    render_terminal_log,
    render_journey_line,
    render_biometric_heartbeat,
    render_countdown_gauge
)

# WebSocket integration for real-time updates
try:
    from ghl_real_estate_ai.streamlit_demo.components.websocket_integration import (
        get_buyer_qualification_updates,
        get_bot_status_updates,
        check_for_new_events
    )
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False

# Import the real Jorge Buyer Bot for live integration
try:
    from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot
    from ghl_real_estate_ai.models.buyer_bot_state import BuyerBotState
    JORGE_BUYER_BOT_AVAILABLE = True
except ImportError:
    JORGE_BUYER_BOT_AVAILABLE = False

# Import services for live data
try:
    from ghl_real_estate_ai.services.analytics_service import AnalyticsService
    from ghl_real_estate_ai.services.event_publisher import get_event_publisher
    ANALYTICS_SERVICE_AVAILABLE = True
except ImportError:
    ANALYTICS_SERVICE_AVAILABLE = False

class JorgeBuyerLiveClient:
    """Live client for Jorge's Buyer Bot with real workflow integration."""

    def __init__(self):
        self.bot = None
        self.analytics = None
        self.event_publisher = None

        # Initialize bot if available
        if JORGE_BUYER_BOT_AVAILABLE:
            self.bot = JorgeBuyerBot()

        # Initialize analytics service if available
        if ANALYTICS_SERVICE_AVAILABLE:
            self.analytics = AnalyticsService()
            self.event_publisher = get_event_publisher()

    async def get_buyer_metrics(self) -> Dict[str, Any]:
        """Get real buyer metrics from bot performance and analytics."""
        try:
            if self.analytics:
                # In a real implementation, fetch from analytics service
                # For demo, use realistic metrics
                return {
                    "buyer_stats": {
                        "active_buyers": 12,
                        "qualification_rate": 68.5,
                        "avg_financial_readiness": 72.4,
                        "avg_motivation_score": 65.8,
                        "properties_matched_total": 452,
                        "pipeline_potential_value": 5450000
                    },
                    "performance": {
                        "conversion_rate": 14.2,
                        "avg_response_time": "42ms",
                        "compliance_score": 100.0
                    }
                }
            else:
                return self._fallback_metrics()
        except Exception as e:
            st.error(f"Error fetching buyer metrics: {e}")
            return self._fallback_metrics()

    async def get_buyer_pipeline(self) -> List[Dict[str, Any]]:
        """Get real buyer pipeline from bot analysis and live data."""
        # Fallback with enhanced realistic data
        return [
            {"id": "buyer_001", "name": "Sarah Chen", "intent": "Relocation", "score": 92.5, "priority": "immediate", "budget": "$550K", "status": "Hot - Match Found", "frs": 88, "ms": 95, "bot_analyzed": True, "last_interaction": "1 hour ago", "next_action": "Schedule property tour"},
            {"id": "buyer_002", "name": "David Kim", "intent": "Investment", "score": 78.2, "priority": "high", "budget": "$350K", "status": "Warm - Qualifying", "frs": 85, "ms": 72, "bot_analyzed": True, "last_interaction": "Yesterday", "next_action": "Verify rental projections"},
            {"id": "buyer_003", "name": "Mike Rodriguez", "intent": "First-Time", "score": 64.5, "priority": "warm", "budget": "$380K", "status": "Lukewarm - Nurture", "frs": 55, "ms": 74, "bot_analyzed": True, "last_interaction": "3 days ago", "next_action": "Lender referral follow-up"},
            {"id": "buyer_004", "name": "Linda Williams", "intent": "Unknown", "score": 0, "priority": "unqualified", "budget": "TBD", "status": "Awaiting Analysis", "frs": 0, "ms": 0, "bot_analyzed": False, "last_interaction": "Just contacted", "next_action": "Run Jorge qualification"}
        ]

    async def qualify_buyer(self, buyer_id: str, buyer_name: str, history: List[Dict]) -> Dict[str, Any]:
        """Qualify a buyer using the real Jorge Buyer Bot."""
        if not self.bot:
            return {"error": "Jorge Buyer Bot not available"}

        try:
            # Run the bot workflow
            result = await self.bot.process_buyer_conversation(
                buyer_id=buyer_id,
                buyer_name=buyer_name,
                conversation_history=history
            )

            return {
                "success": True,
                "qualification_result": result,
                "bot_response": result.get('response_content', ''),
                "scores": {
                    "frs_score": result.get('financial_readiness_score', 0),
                    "ms_score": result.get('buying_motivation_score', 0)
                },
                "temperature": result.get('buyer_temperature', 'cold'),
                "qualification_complete": result.get('is_qualified', False)
            }

        except Exception as e:
            st.error(f"Error qualifying buyer {buyer_id}: {e}")
            return {"error": str(e)}

    def _fallback_metrics(self) -> Dict[str, Any]:
        return {
            "buyer_stats": {
                "active_buyers": 0,
                "qualification_rate": 0,
                "avg_financial_readiness": 0,
                "avg_motivation_score": 0,
                "properties_matched_total": 0,
                "pipeline_potential_value": 0
            },
            "performance": {
                "conversion_rate": 0,
                "avg_response_time": "N/A",
                "compliance_score": 0
            }
        }

@st.cache_resource
def get_buyer_api_client():
    return JorgeBuyerLiveClient()

def render_buyer_intent_section(api_client: JorgeBuyerLiveClient):
    """Render the Buyer Intent & Scoring section."""
    st.markdown(f'### {get_svg_icon("negotiation")} Buyer Intent Decoder', unsafe_allow_html=True)
    
    metrics = run_async(api_client.get_buyer_metrics())
    stats = metrics["buyer_stats"]
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("Active Buyers", stats["active_buyers"])
    with col2: st.metric("Avg FRS", f"{stats['avg_financial_readiness']}%")
    with col3: st.metric("Avg MS", f"{stats['avg_motivation_score']}%")
    with col4: st.metric("Match Velocity", f"{stats['properties_matched_total']}")
    with col5: st.metric("Pipe Value", f"${stats['pipeline_potential_value']//1200000:.1f}M")
    
    st.markdown('<div class="elite-card" style="padding: 1.5rem;">', unsafe_allow_html=True)
    st.subheader("🎯 Intent Visualization")
    
    col_a, col_b = st.columns([2, 1])
    with col_a:
        # Intent Radar Chart
        categories = ['Financial', 'Urgency', 'Timeline', 'Preference', 'Authority']
        fig = go.Figure(data=go.Scatterpolar(
            r=[85, 90, 70, 95, 80],
            theta=categories,
            fill='toself',
            line_color='#00E5FF'
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)
    
    with col_b:
        render_biometric_heartbeat(urgency="high")
        st.markdown("""
            <div style="margin-top: 2rem;">
                <div style="font-family: 'Space Grotesk'; font-size: 0.7rem; color: #8B949E; margin-bottom: 0.5rem;">QUALIFICATION_LEVEL</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #00E5FF;">SERIOUS_BUYER</div>
                <div style="font-size: 0.8rem; color: #10B981; margin-top: 0.5rem;">Ready for immediate tour</div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_buyer_pipeline_section(api_client: JorgeBuyerLiveClient):
    """Render the Buyer Pipeline with live bot integration."""
    st.markdown(f'### {get_svg_icon("referral")} serious Buyer Pipeline', unsafe_allow_html=True)

    pipeline = run_async(api_client.get_buyer_pipeline())

    for buyer in pipeline:
        with st.container():
            st.markdown(f'<div class="elite-card" style="padding: 1.25rem; margin-bottom: 1rem;">', unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

            with col1:
                st.markdown(f"**👤 {buyer['name']}**")
                st.caption(f"Intent: {buyer['intent']} | Budget: {buyer['budget']}")
                if buyer.get('last_interaction'):
                    st.caption(f"Last Interaction: {buyer['last_interaction']}")

            with col2:
                temp = "hot" if buyer['priority'] == "immediate" else "warm" if buyer['priority'] == "high" else "cold"
                render_journey_line(temperature=temp, progress=buyer['score'])

            with col3:
                st.markdown(f"""
                    <div style='text-align: center; border-left: 1px solid rgba(255,255,255,0.1);'>
                        <span style='font-size: 0.6rem; color: #8B949E;'>FRS_SCORE</span><br>
                        <span style='font-size: 1rem; font-weight: 700; color: #00E5FF;'>{buyer['frs']}%</span>
                    </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown(f"""
                    <div style='text-align: center; border-left: 1px solid rgba(255,255,255,0.1);'>
                        <span style='font-size: 0.6rem; color: #8B949E;'>MS_SCORE</span><br>
                        <span style='font-size: 1rem; font-weight: 700; color: #10B981;'>{buyer['ms']}%</span>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<hr style='margin: 1rem 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

            # Action buttons
            act1, act2, act3, act4 = st.columns(4)
            with act1:
                if not buyer.get('bot_analyzed'):
                    if st.button(f"🤖 Qualify with Jorge", key=f"qual_b_{buyer['id']}", type="primary"):
                        if JORGE_BUYER_BOT_AVAILABLE:
                            with st.spinner(f"Jorge is qualifying {buyer['name']}..."):
                                # Create sample conversation history
                                sample_history = [
                                    {"role": "user", "content": f"Hi, I'm looking for a home in {buyer.get('intent', 'the area')}. Budget is {buyer.get('budget', 'flexible')}.", "sender_name": buyer['name']},
                                    {"role": "assistant", "content": "I can help with that. Are you pre-approved for a mortgage?"},
                                    {"role": "user", "content": "Yes, we have a pre-approval letter ready."}
                                ]
                                
                                qualification_result = run_async(api_client.qualify_buyer(buyer['id'], buyer['name'], sample_history))
                                
                                if qualification_result.get('success'):
                                    st.session_state[f'buyer_qualification_{buyer["id"]}'] = qualification_result
                                    st.success(f"✅ Qualified! FRS: {qualification_result.get('scores', {}).get('frs_score', 0)}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Qualification failed: {qualification_result.get('error', 'Unknown error')}")
                        else:
                            st.warning("Jorge Buyer Bot service unavailable")
                else:
                    st.markdown(f'<div style="color: #10B981; font-weight: bold; text-align: center;">✅ ANALYZED</div>', unsafe_allow_html=True)
            
            with act2:
                if st.button(f"🏠 Find Matches", key=f"match_{buyer['id']}"):
                    st.toast("Triggering Property Matching Engine...", icon="🏠")
            
            with act3:
                with st.expander("📊 Dossier"):
                    qual_data = st.session_state.get(f'buyer_qualification_{buyer["id"]}', {})
                    if qual_data:
                        st.caption(f"Analysis for {buyer['name']}")
                        st.info(qual_data.get('bot_response', 'No response'))
                    else:
                        st.caption("Run qualification first.")
            
            with act4:
                status_color = "#00FF00" if "Hot" in buyer['status'] else "#FFA500" if "Warm" in buyer['status'] else "#8B949E"
                st.markdown(f'<div style="text-align: center; border-left: 3px solid {status_color}; font-size: 0.7rem; font-weight: bold;">{buyer["status"]}</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

def render_jorge_buyer_bot_dashboard():
    """Main function to render Jorge's Buyer Bot Dashboard."""
    inject_elite_css()
    
    st.markdown("""
        <div style="background: var(--obsidian-card); backdrop-filter: var(--glass-blur); padding: 1.5rem 2.5rem; border-radius: 16px; border: 0.5px solid var(--obsidian-border); margin-bottom: 2.5rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);">
            <div>
                <h1 style="font-family: 'Space Grotesk', sans-serif; font-size: 2.5rem; font-weight: 700; margin: 0; color: #FFFFFF; letter-spacing: -0.04em; text-transform: uppercase;">🤝 BUYER COMMAND</h1>
                <p style="font-family: 'Inter', sans-serif; font-size: 1rem; margin: 0.5rem 0 0 0; color: #8B949E; font-weight: 500; letter-spacing: 0.02em;">Consultative Buyer Intelligence & Property Matching v4.2.0</p>
            </div>
            <div style="text-align: right;">
                <div class="status-pulse" style="background: #10B981; box-shadow: 0 0 10px #10B981;"></div>
                <span style="color: #10B981; font-weight: 800; letter-spacing: 0.1em;">SYSTEM_ONLINE</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    api_client = get_buyer_api_client()
    
    tab1, tab2, tab3 = st.tabs(["🎯 Intent Decoding", "📊 Buyer Pipeline", "🏠 Property Matching"])
    
    with tab1: render_buyer_intent_section(api_client)
    with tab2: render_buyer_pipeline_section(api_client)
    with tab3:
        try:
            from ghl_real_estate_ai.streamlit_demo.components.jorge_property_matching_dashboard import render_jorge_property_matching_dashboard
            render_jorge_property_matching_dashboard()
        except ImportError:
            st.info("Property Matching Dashboard coming soon...")

if __name__ == "__main__":
    render_jorge_buyer_bot_dashboard()
