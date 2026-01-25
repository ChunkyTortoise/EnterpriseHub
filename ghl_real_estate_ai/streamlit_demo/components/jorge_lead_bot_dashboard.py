"""
Jorge's AI Lead Bot - Unified Dashboard with Enhanced Lead Scoring

Complete lead automation system integrating:
- Enhanced AI Lead Scoring 2.0 (NEW!)
- Voice AI Phone Integration
- Automated Marketing Campaigns
- Client Retention & Referrals
- Market Prediction Analytics

Built specifically for Jorge's GHL system.
"""

import streamlit as st
from ghl_real_estate_ai.streamlit_demo.async_utils import run_async
import asyncio
import json
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import sys
import os

# Add the services directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../services'))

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Import the enhanced lead scorer
try:
    from enhanced_smart_lead_scorer import EnhancedSmartLeadScorer, LeadScoreBreakdown, LeadPriority, BuyingStage
    ENHANCED_SCORER_AVAILABLE = True
except ImportError:
    ENHANCED_SCORER_AVAILABLE = False
    # Fallback classes for when scorer isn't available
    class LeadPriority:
        IMMEDIATE = "immediate"
        HIGH = "high"
        MEDIUM = "medium"
        LOW = "low"
    class BuyingStage:
        READY_TO_BUY = "ready_to_buy"
        GETTING_SERIOUS = "getting_serious"
        JUST_LOOKING = "just_looking"

# Import Phase 5 Intent Decoder
try:
    from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder
    from ghl_real_estate_ai.models.lead_scoring import LeadIntentProfile
    INTENT_DECODER_AVAILABLE = True
except ImportError:
    INTENT_DECODER_AVAILABLE = False

# Import Phase 5 CMA Generator
try:
    from ghl_real_estate_ai.agents.cma_generator import CMAGenerator
    from ghl_real_estate_ai.utils.pdf_renderer import PDFRenderer
    CMA_GENERATOR_AVAILABLE = True
except ImportError:
    CMA_GENERATOR_AVAILABLE = False

# Import Phase 6 Lead Bot Workflow
try:
    from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow
    from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot
    from ghl_real_estate_ai.models.workflows import LeadFollowUpState
    LEAD_BOT_WORKFLOW_AVAILABLE = True
except ImportError:
    LEAD_BOT_WORKFLOW_AVAILABLE = False

# Import Phase 7 Whisper Coach
try:
    from ghl_real_estate_ai.services.whisper_coach import WhisperCoachEngine
    WHISPER_COACH_AVAILABLE = True
except ImportError:
    WHISPER_COACH_AVAILABLE = False

# Import Phase 8 Property Visualizer
try:
    import streamlit.components.v1 as components
    from ghl_real_estate_ai.streamlit_demo.async_utils import run_async
    from ghl_real_estate_ai.services.property_visualizer import PropertyVisualizer
    PROPERTY_VISUALIZER_AVAILABLE = True
except ImportError:
    PROPERTY_VISUALIZER_AVAILABLE = False

# Import the Property Matching service
try:
    from ghl_real_estate_ai.services.jorge_property_matching_service import JorgePropertyMatchingService
    PROPERTY_MATCHING_SERVICE_AVAILABLE = True
except ImportError:
    PROPERTY_MATCHING_SERVICE_AVAILABLE = False

# Import the Analytics service
try:
    from ghl_real_estate_ai.services.jorge_analytics_service import JorgeAnalyticsService
    ANALYTICS_SERVICE_AVAILABLE = True
except ImportError:
    ANALYTICS_SERVICE_AVAILABLE = False

# Mock API client for development
class JorgeAPIClient:
    """Client for Jorge's Advanced Features API, now integrated with live AnalyticsService."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        from ghl_real_estate_ai.services.analytics_service import AnalyticsService
        self.analytics = AnalyticsService()
        
    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get unified dashboard metrics from live analytics."""
        try:
            live_data = await self.analytics.get_jorge_bot_metrics(location_id="all", days=7)
            l_data = live_data["lead"]
            s_data = live_data["seller"]
            
            # Aggregate from multiple sources for a unified view
            return {
                "voice_ai": {
                    "total_calls": s_data["handoffs"],
                    "qualified_leads": s_data["temp_breakdown"]["hot"],
                    "avg_call_duration": 285,
                    "qualification_rate": (s_data["temp_breakdown"]["hot"] / s_data["total_interactions"] * 100) if s_data["total_interactions"] > 0 else 0,
                    "transfer_rate": 12.8
                },
                "marketing": {
                    "active_campaigns": 8,
                    "total_impressions": 15420,
                    "conversion_rate": 3.2,
                    "cost_per_lead": 18.50,
                    "roi": 340
                },
                "client_retention": {
                    "total_clients": 156,
                    "engagement_score": 84.2,
                    "retention_rate": 92.1,
                    "referrals_this_month": 12,
                    "lifetime_value": 28500
                },
                "market_predictions": {
                    "active_markets": 3,
                    "prediction_accuracy": 87.6,
                    "opportunities_found": 15,
                    "avg_roi_potential": 22.3
                },
                "integration_health": {
                    "ghl_status": "healthy",
                    "claude_status": "healthy",
                    "overall_uptime": 99.2
                },
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            # Fallback to defaults
            return {
                "voice_ai": {"total_calls": 0, "qualified_leads": 0, "avg_call_duration": 0, "qualification_rate": 0, "transfer_rate": 0},
                "marketing": {"active_campaigns": 0, "total_impressions": 0, "conversion_rate": 0, "cost_per_lead": 0, "roi": 0},
                "client_retention": {"total_clients": 0, "engagement_score": 0, "retention_rate": 0, "referrals_this_month": 0, "lifetime_value": 0},
                "market_predictions": {"active_markets": 0, "prediction_accuracy": 0, "opportunities_found": 0, "avg_roi_potential": 0},
                "integration_health": {"ghl_status": "error", "claude_status": "healthy", "overall_uptime": 0},
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
    
    async def get_voice_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get voice AI analytics from live seller handoff data."""
        try:
            live_data = await self.analytics.get_jorge_bot_metrics(location_id="all", days=days)
            s_data = live_data["seller"]
            return {
                "period_days": days,
                "analytics": {
                    "total_calls": s_data["handoffs"],
                    "successful_calls": int(s_data["handoffs"] * 0.8),
                    "qualified_leads": s_data["temp_breakdown"]["hot"],
                    "avg_qualification_score": s_data["avg_quality"] * 100,
                    "top_lead_sources": ["Zillow", "Facebook", "Referral"],
                    "call_outcomes": {
                        "Qualified Lead": s_data["temp_breakdown"]["hot"],
                        "Follow-up Scheduled": int(s_data["handoffs"] * 0.3),
                        "Not Interested": int(s_data["handoffs"] * 0.1),
                        "Wrong Number": 0
                    }
                }
            }
        except:
            return {"period_days": days, "analytics": {"total_calls": 0, "successful_calls": 0, "qualified_leads": 0, "avg_qualification_score": 0, "top_lead_sources": [], "call_outcomes": {}}}

    async def get_scoring_analytics(self) -> Dict[str, Any]:
        """Get analytics about lead scoring performance from live data."""
        try:
            live_data = await self.analytics.get_jorge_bot_metrics(location_id="all", days=30)
            l_data = live_data["lead"]
            return {
                "total_leads_scored": l_data["total_scored"],
                "avg_score": l_data["avg_score"],
                "score_distribution": {
                    "90-100": l_data["immediate_priority"],
                    "80-89": l_data["high_priority"],
                    "70-79": int(l_data["total_scored"] * 0.3),
                    "60-69": int(l_data["total_scored"] * 0.2),
                    "50-59": int(l_data["total_scored"] * 0.1),
                    "40-49": 0, "30-39": 0, "0-29": 0
                },
                "conversion_by_score": {"90-100": 0.85, "80-89": 0.72, "70-79": 0.54, "60-69": 0.34, "50-59": 0.18, "40-49": 0.08, "30-39": 0.03, "0-29": 0.01},
                "priority_breakdown": {
                    "immediate": l_data["immediate_priority"],
                    "high": l_data["high_priority"],
                    "medium": int(l_data["total_scored"] * 0.4),
                    "low": int(l_data["total_scored"] * 0.2),
                    "disqualified": 0
                },
                "accuracy_metrics": {"prediction_accuracy": 87.2, "false_positives": 8.1, "false_negatives": 4.7}
            }
        except:
            return {"total_leads_scored": 0, "avg_score": 0, "score_distribution": {}, "conversion_by_score": {}, "priority_breakdown": {}, "accuracy_metrics": {}}

    async def start_voice_call(self, phone_number: str, caller_name: str = None) -> Dict[str, str]:
        """Start a new voice call."""
        return {
            "call_id": f"call_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "status": "active",
            "message": "Voice AI call started successfully"
        }

    async def analyze_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a lead using the enhanced scoring system."""
        if ENHANCED_SCORER_AVAILABLE:
            try:
                scorer = EnhancedSmartLeadScorer()
                score_breakdown = await scorer.calculate_comprehensive_score(lead_data)

                return {
                    "overall_score": score_breakdown.overall_score,
                    "priority_level": score_breakdown.priority_level.value,
                    "buying_stage": score_breakdown.buying_stage.value,
                    "score_breakdown": {
                        "intent_score": score_breakdown.intent_score,
                        "financial_readiness": score_breakdown.financial_readiness,
                        "timeline_urgency": score_breakdown.timeline_urgency,
                        "engagement_quality": score_breakdown.engagement_quality,
                        "referral_potential": score_breakdown.referral_potential,
                        "local_connection": score_breakdown.local_connection
                    },
                    "recommended_actions": score_breakdown.recommended_actions,
                    "talking_points": score_breakdown.jorge_talking_points,
                    "risk_factors": score_breakdown.risk_factors
                }
            except Exception as e:
                return {"error": f"Scoring error: {str(e)}"}

        # Fallback mock data if scorer not available
        return {
            "overall_score": 75.5,
            "priority_level": "high",
            "buying_stage": "getting_serious",
            "score_breakdown": {
                "intent_score": 80, "financial_readiness": 90, "timeline_urgency": 60, "engagement_quality": 75, "referral_potential": 45, "local_connection": 70
            },
            "recommended_actions": ["📞 Call within 1 hour", "📧 Send market insights", "🏠 Curate 3-5 property matches"],
            "talking_points": ["🎯 'Based on your search...'", "💰 'With your budget...'", "🏫 'I know the best neighborhoods...'"],
            "risk_factors": ["⚠️ No pre-approval yet"]
        }

    async def get_lead_pipeline(self) -> List[Dict[str, Any]]:
        """Get current lead pipeline with enhanced scoring."""
        return [
            {"id": "lead_001", "name": "Sarah Johnson", "phone": "+1-555-123-4567", "email": "sarah.j@email.com", "score": 85.2, "priority": "immediate", "stage": "ready_to_buy", "last_contact": "2 hours ago", "source": "Zillow", "budget": "$750K-850K", "timeline": "30 days", "notes": "Pre-approved"},
            {"id": "lead_002", "name": "Mike Chen", "phone": "+1-555-234-5678", "email": "mike.c@email.com", "score": 72.8, "priority": "high", "stage": "getting_serious", "last_contact": "1 day ago", "source": "Facebook", "budget": "$650K-750K", "timeline": "60 days", "notes": "Teacher"},
            {"id": "lead_005", "name": "Jennifer White", "phone": "+1-555-567-8901", "email": "jennifer.w@email.com", "score": 91.7, "priority": "immediate", "stage": "ready_to_buy", "last_contact": "30 minutes ago", "source": "Referral", "budget": "$900K-1.2M", "timeline": "Immediate", "notes": "Cash buyer"}
        ]

    async def get_intent_profile(self, lead_id: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Fetch real intent profile using Phase 5 Intent Decoder."""
        if INTENT_DECODER_AVAILABLE:
            try:
                decoder = LeadIntentDecoder()
                profile = decoder.analyze_lead(lead_id, history)
                return profile.dict()
            except Exception as e:
                print(f"Decoder Error: {e}")
        return await self.analyze_intent_phase1(history)

    async def run_followup_simulation(self, lead_data: Dict[str, Any], step: str) -> Dict[str, Any]:
        """Simulate a step in the 3-7-30 follow-up sequence."""
        if LEAD_BOT_WORKFLOW_AVAILABLE:
            try:
                bot = LeadBotWorkflow()
                # Prepare state
                state: LeadFollowUpState = {
                    "lead_id": lead_data.get("id", "demo_lead"),
                    "lead_name": lead_data.get("name", "Demo Lead"),
                    "contact_phone": lead_data.get("phone", "+15551234567"),
                    "contact_email": lead_data.get("email", "demo@example.com"),
                    "property_address": lead_data.get("property", "123 Main St, Austin, TX"),
                    "conversation_history": lead_data.get("history", []),
                    "intent_profile": None,
                    "current_step": step,
                    "engagement_status": "ghosted",
                    "last_interaction_time": datetime.now(timezone.utc) - timedelta(days=3),
                    "stall_breaker_attempted": False,
                    "cma_generated": False
                }
                
                # We invoke the workflow. Since it's a LangGraph, we can run it 
                # (simplified here since we want to see a specific node result)
                # simulation, we'll manually call the node matching the step
                if step == "day_3":
                    result = await bot.send_day_3_sms(state)
                elif step == "day_7":
                    result = await bot.initiate_day_7_call(state)
                elif step == "day_14":
                    result = await bot.send_day_14_email(state)
                elif step == "day_30":
                    result = await bot.send_day_30_nudge(state)
                else:
                    result = {"current_step": step}
                
                return result
            except Exception as e:
                print(f"Workflow Simulation Error: {e}")
        
        return {"current_step": step, "status": "simulated"}

    async def analyze_intent_phase1(self, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Call Phase 1 Intent Analysis (2026 Roadmap)."""
        if INTENT_DECODER_AVAILABLE:
            try:
                decoder = LeadIntentDecoder()
                # Analyze lead using the real decoder
                profile = decoder.analyze_lead("demo_lead", conversation_history)
                return profile.dict()
            except Exception as e:
                print(f"Decoder Error: {e}")

        if REQUESTS_AVAILABLE:
            try:
                # Assuming localhost:8000 for now
                response = requests.post(
                    f"{self.base_url}/api/intelligence/analyze-intent",
                    json={"contact_id": "demo_lead", "conversation_history": conversation_history},
                    timeout=5
                )
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                print(f"API Error: {e}")
        
        # Fallback Mock for Demo if API fails or requests missing
        return {
            "lead_id": "demo_lead",
            "frs": {
                "total_score": 88.5,
                "classification": "Hot Lead",
                "motivation": {"score": 90, "category": "High Intent", "detected_markers": ["moving for job"]},
                "timeline": {"score": 90, "category": "High Commitment", "target_date": None},
                "condition": {"score": 85, "category": "Realistic", "acknowledged_defects": ["needs paint"]},
                "price": {"score": 80, "category": "Price-Aware", "zestimate_mentioned": True}
            },
            "pcs": {
                "total_score": 75,
                "response_velocity_score": 100,
                "message_length_score": 50,
                "question_depth_score": 60,
                "objection_handling_score": 50,
                "call_acceptance_score": 100,
                "last_updated": datetime.now(timezone.utc).isoformat()
            },
            "next_best_action": "Route to Jorge (Voice Call)",
            "stall_breaker_suggested": None
        }

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
    render_neural_heatmap
)

from ghl_real_estate_ai.services.war_room_service import WarRoomService

# Initialize API client and Enhanced Scorer
@st.cache_resource
def get_api_client():
    return JorgeAPIClient()

@st.cache_resource
def get_enhanced_scorer():
    if ENHANCED_SCORER_AVAILABLE:
        return EnhancedSmartLeadScorer()
    return None

@st.cache_resource
def get_war_room_service():
    return WarRoomService()

@st.cache_resource
def get_whisper_coach():
    return WhisperCoachEngine()

@st.cache_resource
def get_property_visualizer():
    return PropertyVisualizer()

@st.cache_resource
def get_jorge_seller_bot():
    return JorgeSellerBot()

def render_jorge_seller_bot_section(api_client: JorgeAPIClient):
    """Render the Phase 6 Jorge Seller Bot section."""
    st.markdown(f'### {get_svg_icon("negotiation")} Jorge Persona // Motivated Seller Bot', unsafe_allow_html=True)
    st.markdown("Confrontational qualification and stall-breaking protocol.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="elite-card" style="padding: 1.5rem;">', unsafe_allow_html=True)
        st.subheader("💬 Active Seller Chat")
        
        user_msg = st.text_area("Seller Message", "I'll get back to you next week, I'm pretty busy right now.", key="seller_msg_input")
        
        if st.button("🚀 ENGAGE JORGE PERSONA", type="primary", use_container_width=True):
            bot = get_jorge_seller_bot()
            history = [{"role": "user", "content": user_msg}]
            with st.spinner("Jorge is typing..."):
                result = run_async(bot.process_seller_message("demo_seller", "Robert Miller", history))
                st.session_state['jorge_seller_result'] = result
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        if 'jorge_seller_result' in st.session_state:
            res = st.session_state['jorge_seller_result']
            st.markdown(f'<div class="elite-card" style="padding: 1.5rem; border-top: 2px solid var(--negotiation-neon) !important;">', unsafe_allow_html=True)
            
            # Strategy Header
            st.markdown(f"#### 🎯 STRATEGY: {res['current_tone']}")
            
            if res['stall_detected']:
                st.error(f"⚠️ STALL DETECTED: {res['detected_stall_type'].upper()}")
            
            # The Response
            st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px; font-style: italic; border-left: 3px solid var(--negotiation-neon); margin: 1rem 0;">
                    "{res['response_content']}"
                </div>
            """, unsafe_allow_html=True)
            
            # Metrics
            st.caption(f"Psychological Commitment: {res['psychological_commitment']}%")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Enter a seller message to see Jorge's direct response.")

def render_voice_ai_section(api_client: JorgeAPIClient):
    """Render the Voice AI section."""
    st.markdown(f'### {get_svg_icon("voice")} Voice AI Phone Integration', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="elite-card" style="padding: 1.5rem;">', unsafe_allow_html=True)
        st.subheader("Quick Call Start")
        
        phone_number = st.text_input(
            "Phone Number",
            placeholder="+1 (555) 123-4567",
            help="Start an AI-powered lead qualification call"
        )
        
        caller_name = st.text_input(
            "Caller Name (Optional)",
            placeholder="John Smith"
        )
        
        if st.button("🚀 Start AI Call", type="primary", use_container_width=True):
            if phone_number:
                with st.spinner("Initiating AI call..."):
                    try:
                        result = run_async(api_client.start_voice_call(phone_number, caller_name))
                        st.success(f"✅ Call started! Call ID: {result['call_id']}")
                    except Exception as e:
                        st.error(f"❌ Failed to start call: {str(e)}")
            else:
                st.error("Please enter a phone number")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="elite-card" style="padding: 1.5rem;">', unsafe_allow_html=True)
        st.subheader("Voice AI Performance")
        
        render_voice_waveform()
        st.markdown("<br>", unsafe_allow_html=True)

        # Get analytics
        analytics = run_async(api_client.get_voice_analytics())
        voice_data = analytics["analytics"]
        
        # Key metrics
        col2_1, col2_2 = st.columns(2)
        with col2_1:
            st.metric(
                "Qualified Leads",
                voice_data["qualified_leads"],
                delta="+5 this week"
            )
            st.metric(
                "Avg Score",
                f"{voice_data['avg_qualification_score']:.1f}%",
                delta="+3.2%"
            )
        
        with col2_2:
            st.metric(
                "Total Calls",
                voice_data["total_calls"],
                delta="+12 today"
            )
            st.metric(
                "Success Rate",
                f"{(voice_data['successful_calls']/voice_data['total_calls']*100):.1f}%",
                delta="+2.1%"
            )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Call outcomes chart
        outcomes_df = pd.DataFrame(
            list(voice_data["call_outcomes"].items()),
            columns=["Outcome", "Count"]
        )
        
        st.subheader("Call Outcomes")
        fig = px.bar(outcomes_df, x="Outcome", y="Count", color="Count", color_continuous_scale='Blues')
        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)

def render_followup_orchestrator(api_client: JorgeAPIClient):
    """Render the Phase 6 Ghost-in-the-Machine Follow-Up Orchestrator."""
    st.markdown(f'### {get_svg_icon("intelligence")} Ghost-in-the-Machine // Follow-Up Orchestrator', unsafe_allow_html=True)
    st.markdown("Autonomous re-engagement engine for cold and ghosted leads.")
    
    if not LEAD_BOT_WORKFLOW_AVAILABLE:
        st.error("Lead Bot Workflow not available.")
        return

    # Simulation Controls
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown('<div class="elite-card" style="padding: 1.5rem;">', unsafe_allow_html=True)
        st.subheader("🤖 Sequence Controller")
        
        target_lead = st.selectbox("Select Lead to Simulate", ["Sarah Johnson", "Mike Chen", "Jennifer White"])
        
        simulation_step = st.select_slider(
            "Current Sequence Position",
            options=["initial", "day_3", "day_7", "day_14", "day_30"],
            value="day_7"
        )
        
        if st.button("🚀 EXECUTE CURRENT STEP", type="primary", use_container_width=True):
            with st.spinner(f"Executing {simulation_step} for {target_lead}..."):
                # Get lead details for simulation
                pipeline = run_async(api_client.get_lead_pipeline())
                lead_data = next((l for l in pipeline if l['name'] == target_lead), {"name": target_lead})
                
                # Run the simulation
                result = run_async(api_client.run_followup_simulation(lead_data, simulation_step))
                st.session_state['followup_simulation_result'] = result
                
                st.success(f"✅ {simulation_step.upper()} successfully executed!")
                st.toast(f"Sequence advanced for {target_lead}", icon="👻")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="elite-card" style="padding: 1.5rem;">', unsafe_allow_html=True)
        st.subheader("📊 Sequence Logic & Content")
        
        sim_result = st.session_state.get('followup_simulation_result')
        
        if sim_result and 'response_content' in sim_result:
            st.markdown(f"**Generated Response (Real-Time AI):**")
            st.info(sim_result['response_content'])
            
            # Display metadata if available
            if sim_result.get('optimized_timing_applied'):
                st.caption("✅ Behavioral timing optimization applied")
            if sim_result.get('personalization_applied'):
                st.caption("✅ Personality adaptation applied")
        else:
            if simulation_step == "day_3":
                st.markdown("**Channel:** SMS // **Tone:** Soft Check-in")
                st.info("💬 'Hi {Name}—just following up on your property. No pressure, but we have qualified buyers interested...'")
            elif simulation_step == "day_7":
                st.markdown("**Channel:** Voice AI // **Tone:** Jorge Stall-Breaker")
                st.warning("🔊 'Hey {Name}, I know I've reached out, but market conditions are shifting. Would 15 mins make sense?'")
            elif simulation_step == "day_14":
                st.markdown("**Channel:** Email // **Tone:** Value Injection")
                st.success("📄 [CMA Snapshot] 'Zillow's estimate is off by $50K. Here is the real analysis...'")
            elif simulation_step == "day_30":
                st.markdown("**Channel:** SMS // **Tone:** Final Nudge")
                st.error("💬 'Hi {Name}, still interested in selling or should I close the file?'")
        
        # Timeline view
        st.divider()
        st.markdown("**Journey Timeline:**")
        render_journey_line(temperature="hot" if simulation_step == "day_7" else "warm", progress=60)
        st.markdown('</div>', unsafe_allow_html=True)

def render_whisper_mode():
    """Render the Phase 7 Whisper Mode Real-Time Coaching Dashboard."""
    st.markdown(f'### {get_svg_icon("voice")} Whisper Mode // Real-Time Coaching', unsafe_allow_html=True)
    st.markdown("Live sentiment analysis and tactical cues for active calls.")
    
    if not WHISPER_COACH_AVAILABLE:
        st.error("Whisper Coach Engine not available.")
        return

    coach = get_whisper_coach()
    
    # Selection for active call
    active_call_id = "call_jorge_001"
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    # Fetch live coaching data (real or mock fallback)
    feed = run_async(coach.get_live_feed(active_call_id))
    
    with col1:
        st.markdown('<div class="elite-card" style="padding: 1.5rem;">', unsafe_allow_html=True)
        st.subheader("👤 Lead Profile")
        st.markdown("**Name:** Sarah Johnson")
        st.markdown("**Property:** 123 Maple St")
        st.markdown("**Last Intent:** Hot (88 FRS)")
        
        st.divider()
        st.markdown("**Key Motivation:** Relocating for job")
        st.markdown("**Top Objection:** Pricing / Zestimate")
        
        if 'transcript_peek' in feed:
            st.divider()
            st.caption(f"🎤 TRANSCRIPT PEEK: \"{feed['transcript_peek']}\"")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="elite-card" style="padding: 1.5rem; border-top: 2px solid var(--negotiation-neon) !important;">', unsafe_allow_html=True)
        st.subheader("💡 Coaching Cues")
        
        if feed['objection_type']:
            st.warning(f"⚠️ {feed['objection_type'].upper()} OBJECTION DETECTED")
        else:
            st.success("🟢 RAPPORT BUILDING PHASE")
            
        st.markdown(f"""
            <div style="font-size: 1.2rem; font-weight: 700; color: white; margin: 1rem 0; line-height: 1.4;">
                {feed['suggestion']}
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("📊 INJECT CMA SNAPSHOT", use_container_width=True):
            st.toast("CMA Data injected into Jorge's view!", icon="📊")
            if 'global_decisions' in st.session_state:
                st.session_state.global_decisions.append({
                    "action": "CMA Injection",
                    "why": "Countering price objection with real-time comp data.",
                    "time": datetime.now(timezone.utc).strftime("%H:%M:%S")
                })
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="elite-card" style="padding: 1.5rem;">', unsafe_allow_html=True)
        st.subheader("📈 Live Sentiment")
        
        # Sentiment Gauge
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = feed['sentiment'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [None, 100], 'tickcolor': "white"},
                'bar': {'color': "var(--negotiation-neon)"},
                'steps': [
                    {'range': [0, 40], 'color': "rgba(255, 0, 0, 0.1)"},
                    {'range': [40, 70], 'color': "rgba(255, 255, 0, 0.1)"},
                    {'range': [70, 100], 'color': "rgba(0, 255, 0, 0.1)"}
                ],
            }
        ))
        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)
        
        # Pulse animation for "Live"
        st.markdown("""
            <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
                <div class="status-pulse" style="background: #00E5FF; box-shadow: 0 0 10px #00E5FF; position: static; transform: none;"></div>
                <span style="color: #00E5FF; font-weight: 800; font-size: 0.7rem; letter-spacing: 0.2em;">LIVE_TRANSCRIPTION_STREAM</span>
            </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Transcription Stream View
    st.markdown('<div class="terminal-window" style="height: 150px; margin-top: 1.5rem;">', unsafe_allow_html=True)
    st.markdown("""
        <div style="font-weight: bold; color: var(--elite-accent); font-size: 0.7rem; margin-bottom: 8px;">
            > TRANSCRIPT_SYNC // {active_call_id}
        </div>
    """, unsafe_allow_html=True)
    
    # Mock some transcript history
    st.markdown(f'<div class="terminal-line"><span class="terminal-timestamp">[00:05]</span> <span style="color: #8B949E;">Jorge:</span> "Hey Sarah, I saw you were looking at 123 Maple St. What caught your eye?"</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="terminal-line"><span class="terminal-timestamp">[00:12]</span> <span style="color: #6366F1;">Sarah:</span> "Yeah, the kitchen is nice, but Zillow says it\'s overpriced for the area..."</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="terminal-line" style="border-right: 2px solid var(--negotiation-neon); width: fit-content; animation: blink 0.5s step-end infinite;">_</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_marketing_section():
    """Render the Marketing Automation section."""
    st.markdown(f'### {get_svg_icon("referral")} Automated Marketing Campaigns', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="elite-card" style="padding: 1.5rem;">', unsafe_allow_html=True)
        st.subheader("Create Campaign")
        
        campaign_name = st.text_input("Campaign Name", placeholder="Q1 Buyer Leads")
        
        trigger_type = st.selectbox(
            "Campaign Trigger",
            ["NEW_LEAD", "LEAD_SCORE_THRESHOLD", "LIFECYCLE_STAGE", "MARKET_OPPORTUNITY"]
        )
        
        target_audience = st.multiselect(
            "Target Audience",
            ["First-time Buyers", "Investors", "Sellers", "Past Clients", "Referrals"],
            default=["First-time Buyers"]
        )
        
        if st.button("🚀 Create AI Campaign", type="primary", use_container_width=True):
            with st.spinner("Creating campaign with AI..."):
                import time
                time.sleep(2)
                st.success(f"✅ Campaign '{campaign_name}' created successfully!")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="elite-card" style="padding: 1.5rem;">', unsafe_allow_html=True)
        st.subheader("Active Campaigns")
        
        # Mock campaign data
        campaigns = [
            {"name": "Q1 Buyers", "status": "Active", "leads": 34, "conversion": 3.2},
            {"name": "Investor Outreach", "status": "Active", "leads": 18, "conversion": 5.1},
            {"name": "Past Client Nurture", "status": "Active", "leads": 22, "conversion": 4.8},
        ]
        
        for camp in campaigns:
            with st.container():
                col_name, col_status, col_metrics = st.columns([3, 1, 2])
                with col_name: st.write(f"**{camp['name']}**")
                with col_status: st.write("🟢" if camp['status'] == "Active" else "🟡")
                with col_metrics: st.write(f"{camp['leads']} leads")
                st.divider()
        st.markdown('</div>', unsafe_allow_html=True)

def render_retention_section():
    """Render the Client Retention section."""
    st.markdown(f'### {get_svg_icon("referral")} Client Retention & Referrals', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="elite-card" style="padding: 1.5rem;">', unsafe_allow_html=True)
        st.subheader("Client Lifecycle Update")
        client_search = st.text_input("Search Client", placeholder="Enter name or email...")
        life_event = st.selectbox("Life Event Detected", ["PROPERTY_SOLD", "PROPERTY_PURCHASED", "ANNIVERSARY"])
        if st.button("📝 Update Lifecycle", type="primary", use_container_width=True):
            st.success("✅ Client lifecycle updated!")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="elite-card" style="padding: 1.5rem;">', unsafe_allow_html=True)
        st.subheader("Retention Metrics")
        col2_1, col2_2 = st.columns(2)
        with col2_1:
            st.metric("Retention Rate", "92.1%", delta="+1.3%")
        with col2_2:
            st.metric("Referrals", "12", delta="+4")
        st.markdown('</div>', unsafe_allow_html=True)

def render_property_digital_twin(address: str):
    """Render the Phase 8 Three.js Digital Twin for a property."""
    if not PROPERTY_VISUALIZER_AVAILABLE:
        st.error("Property Visualizer not available.")
        return

    visualizer = get_property_visualizer()
    html_content = visualizer.generate_threejs_html(address)
    
    st.markdown(f'<div style="text-align: center; font-family: \'Space Grotesk\'; font-size: 0.7rem; color: var(--elite-accent); letter-spacing: 0.2em; margin-bottom: 0.5rem;">3D_DIGITAL_TWIN_ACTIVE</div>', unsafe_allow_html=True)
    components.html(html_content, height=350)
    st.markdown(f'<div style="text-align: center; color: var(--text-secondary); font-size: 0.6rem;">{address.upper()} // INTERACTIVE NEURAL MESH</div>', unsafe_allow_html=True)

def render_market_prediction_section():
    """Render the Market Prediction section."""
    st.markdown(f'### {get_svg_icon("intelligence")} Market Intelligence Dossiers', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="elite-card" style="padding: 1.5rem;">', unsafe_allow_html=True)
        st.subheader("Market Analysis")
        
        neighborhood = st.selectbox(
            "Neighborhood",
            ["Rancho Cucamonga", "Upland", "Ontario", "Claremont", "Pomona"]
        )
        
        if st.button("🔮 Generate Prediction", type="primary", use_container_width=True):
            with st.spinner("Analyzing market data..."):
                import time
                time.sleep(2)
                st.success("✅ Analysis complete!")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Sparkline simulation
        sparkline_svg = '<svg width="100" height="30" viewBox="0 0 100 30"><path d="M0 25 L10 20 L20 22 L30 15 L40 18 L50 10 L60 12 L70 5 L80 8 L90 2 L100 5" fill="none" stroke="#00E5FF" stroke-width="2" /></svg>'
        
        content = f"""
        <div class="sparkline-container">
            <span>Price Appreciation Trend:</span>
            {sparkline_svg}
            <span style="color: #00E5FF; font-weight: bold;">+12.8%</span>
        </div>
        <p style="margin-top: 10px;">Market velocity is increasing. Inventory levels in {neighborhood} have dropped by 15% in the last 30 days.</p>
        """
        render_dossier_block(content, title=f"{neighborhood.upper()} INTELLIGENCE")
    
    with col2:
        st.markdown('<div class="elite-card" style="padding: 1.5rem; display: flex; flex-direction: column; align-items: center; justify-content: center;">', unsafe_allow_html=True)
        st.subheader("🏠 Property Digital Twin")
        selected_twin = st.selectbox("Select Property Model", ["123 Maple St", "456 Oak Ave"])
        render_property_digital_twin(selected_twin)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="elite-card" style="padding: 1.5rem; margin-top: 1.5rem;">', unsafe_allow_html=True)
        st.subheader("Recent Predictions")
        
        predictions = [
            {"area": "Rancho Cucamonga", "prediction": "+12.8%", "accuracy": "87%"},
            {"area": "Upland", "prediction": "+8.4%", "accuracy": "92%"},
        ]
        
        for pred in predictions:
            st.write(f"**{pred['area']}**: {pred['prediction']} (Accuracy: {pred['accuracy']})")
            st.divider()
        st.markdown('</div>', unsafe_allow_html=True)

def render_integration_dashboard(api_client: JorgeAPIClient):
    """Render the unified integration dashboard."""
    st.markdown(f'### {get_svg_icon("intelligence")} Jorge\'s Command Center', unsafe_allow_html=True)
    
    # Get dashboard metrics
    metrics = run_async(api_client.get_dashboard_metrics())
    
    # System health indicators
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        ghl_status = metrics["integration_health"]["ghl_status"]
        st.metric("GHL", "🟢" if ghl_status == "healthy" else "🔴")
    with col2:
        claude_status = metrics["integration_health"]["claude_status"]
        st.metric("Claude", "🟢" if claude_status == "healthy" else "🔴")
    with col3:
        st.metric("Uptime", f"{metrics['integration_health']['overall_uptime']}%" )
    with col4:
        st.metric("Enhanced AI", "🟢 Active")
    with col5:
        st.metric("Property AI", "🟢 Active")
    with col6:
        st.metric("Analytics", "🟢 Active")

    st.divider()

    # Enhanced Lead Scoring Summary
    st.subheader("🎯 Enhanced Lead Intelligence")
    scoring_analytics = run_async(api_client.get_scoring_analytics())

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("🔴 Immediate", scoring_analytics['priority_breakdown']['immediate'])
    with col2: st.metric("🟠 High", scoring_analytics['priority_breakdown']['high'])
    with col3: st.metric("📊 Avg Score", f"{scoring_analytics['avg_score']:.1f}/100")
    with col4: st.metric("🎯 Accuracy", f"{scoring_analytics['accuracy_metrics']['prediction_accuracy']:.1f}%")
    with col5: st.metric("🧠 Analyzed", f"{scoring_analytics['total_leads_scored']:,}")

def render_enhanced_lead_scoring_section(api_client: JorgeAPIClient):
    """Render the Enhanced Lead Scoring section."""
    st.markdown(f'### {get_svg_icon("negotiation")} Neural Health Scoring 2.0', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 3])

    with col1:
        st.markdown('<div class="elite-card" style="padding: 1.5rem;">', unsafe_allow_html=True)
        st.subheader("🔍 Lead Analysis")
        with st.form("lead_analysis_form"):
            lead_name = st.text_input("Lead Name", placeholder="Sarah Johnson")
            budget = st.number_input("Budget ($)", min_value=0, value=750000, step=50000)
            timeline = st.selectbox("Timeline", ["immediate", "30 days", "3 months", "6 months"])
            analyze_button = st.form_submit_button("🚀 Analyze Lead", type="primary")

        if analyze_button and lead_name:
            lead_data = {"name": lead_name, "budget": budget, "timeline": timeline}
            analysis = run_async(api_client.analyze_lead(lead_data))
            
            # Phase 5: Integrate Intent Decoder for deeper semantic analysis
            if INTENT_DECODER_AVAILABLE:
                decoder = LeadIntentDecoder()
                # Mock a conversation based on input for the demo
                mock_history = [{"role": "user", "content": f"I want to buy for {budget} in {timeline}."}]
                intent_profile = decoder.analyze_lead(lead_name, mock_history)
                analysis['intent_profile'] = intent_profile.dict()
            
            st.session_state['latest_analysis'] = analysis
            st.session_state['analyzed_lead_name'] = lead_name
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        if 'latest_analysis' in st.session_state:
            analysis = st.session_state['latest_analysis']
            lead_name = st.session_state.get('analyzed_lead_name', 'Lead')
            
            st.markdown(f'<div class="elite-card" style="padding: 1.5rem;">', unsafe_allow_html=True)
            st.markdown(f"### 🎯 {lead_name.upper()} // NEURAL HEALTH")
            
            # Neural Progress Bars
            breakdown = analysis['score_breakdown']
            render_neural_progress("Intent Strength", breakdown['intent_score'])
            render_neural_progress("Financial Readiness", breakdown['financial_readiness'])
            render_neural_progress("Timeline Urgency", breakdown['timeline_urgency'])
            
            # Phase 5: FRS/PCS Breakdown if available
            if 'intent_profile' in analysis:
                st.markdown("---")
                intent = analysis['intent_profile']
                frs = intent['frs']
                pcs = intent['pcs']
                
                st.markdown(f"#### 🧠 Intelligence Activation: {frs['classification']}")
                
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("Motivation", f"{frs['motivation']['score']}%")
                with c2: st.metric("Timeline", f"{frs['timeline']['score']}%")
                with c3: st.metric("Condition", f"{frs['condition']['score']}%")
                with c4: st.metric("Price", f"{frs['price']['score']}%")
                
                st.info(f"👉 **Commitment Level (PCS): {pcs['total_score']}%**")
                
                if intent['stall_breaker_suggested']:
                    st.warning(f"🔓 Stall-Breaker Triggered: {intent['stall_breaker_suggested']}")

            # Radar Chart
            st.markdown("---")
            score_df = pd.DataFrame({
                'Dimension': ['Intent', 'Financial', 'Timeline', 'Engagement', 'Referral', 'Local'],
                'Score': [breakdown['intent_score'], breakdown['financial_readiness'], breakdown['timeline_urgency'], 
                          breakdown['engagement_quality'], breakdown['referral_potential'], breakdown['local_connection']]
            })
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=score_df['Score'], theta=score_df['Dimension']))
            st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

def render_property_matching_integration_section():
    """Render the integrated Property Matching AI section."""
    st.header("🏠 Property Matching AI System")
    st.markdown("**AI-powered property recommendations with hybrid neural + rules matching**")
    try:
        from ghl_real_estate_ai.streamlit_demo.components.jorge_property_matching_dashboard import render_jorge_property_matching_dashboard
        render_jorge_property_matching_dashboard()
    except ImportError:
        st.error("⚠️ Property Matching AI system not available.")

def render_analytics_integration_section():
    """Render the integrated Advanced Analytics section."""
    st.header("📊 Advanced Analytics System")
    st.markdown("**Comprehensive business intelligence with forecasting and ROI attribution**")
    try:
        from ghl_real_estate_ai.streamlit_demo.components.jorge_analytics_dashboard import render_jorge_analytics_dashboard
        render_jorge_analytics_dashboard()
    except ImportError:
        st.error("⚠️ Advanced Analytics system not available.")

def render_lead_pipeline_section(api_client: JorgeAPIClient):
    """Render the Lead Pipeline section with Journey Glow Mapping."""
    st.markdown(f'### {get_svg_icon("referral")} Tactical Lead Pipeline', unsafe_allow_html=True)

    # Cache pipeline in session state to avoid redundant API calls (Performance optimization)
    cache_key = 'cached_lead_pipeline'
    cache_timestamp_key = 'lead_pipeline_cache_timestamp'
    cache_duration = 300  # 5 minutes cache duration

    current_time = time.time()

    # Check if cache is valid
    if (cache_key in st.session_state and
        cache_timestamp_key in st.session_state and
        current_time - st.session_state[cache_timestamp_key] < cache_duration):
        pipeline = st.session_state[cache_key]
    else:
        # Fetch fresh data and cache it
        pipeline = run_async(api_client.get_lead_pipeline())
        st.session_state[cache_key] = pipeline
        st.session_state[cache_timestamp_key] = current_time
    
    col_list, col_details = st.columns([3, 2])
    
    with col_list:
        selected_lead = None
        for lead in pipeline:
            with st.container():
                st.markdown(f'<div class="elite-card" style="padding: 1.25rem; margin-bottom: 1rem;">', unsafe_allow_html=True)
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.markdown(f"**👤 {lead['name']}**")
                    st.caption(f"Source: {lead['source']} | Budget: {lead['budget']}")
                
                with col2:
                    # Map priority to temperature
                    temp = "hot" if lead['priority'] == "immediate" else "warm" if lead['priority'] == "high" else "cold"
                    # Map score to progress
                    render_journey_line(temperature=temp, progress=lead['score'])
                
                with col3:
                    st.markdown(f"<div style='text-align: right;'><span style='font-size: 1.2rem; font-weight: bold; color: var(--elite-accent);'>{lead['score']}%</span><br><span style='font-size: 0.7rem; color: var(--text-secondary);'>{lead['priority'].upper()}</span></div>", unsafe_allow_html=True)
                    if st.button("Details", key=f"details_{lead['id']}", use_container_width=True):
                        st.session_state['selected_lead_id'] = lead['id']
                
                st.markdown('</div>', unsafe_allow_html=True)

    with col_details:
        lead_id = st.session_state.get('selected_lead_id')
        if lead_id:
            lead = next((l for l in pipeline if l['id'] == lead_id), None)
            if lead:
                st.markdown(f'<div class="elite-card" style="padding: 1.5rem; border-left: 4px solid var(--elite-accent) !important;">', unsafe_allow_html=True)
                st.subheader(f"📂 DOSSIER: {lead['name'].upper()}")
                
                # Digital Twin Integration
                address = "123 Maple St" # Mock mapping
                render_property_digital_twin(address)
                
                st.divider()
                st.markdown(f"**Budget:** {lead['budget']}")
                st.markdown(f"**Timeline:** {lead['timeline']}")
                st.markdown(f"**Notes:** {lead['notes']}")
                
                if st.button("💬 Start Conversation", use_container_width=True):
                    st.toast(f"Opening chat with {lead['name']}...", icon="💬")
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Select a lead from the pipeline to view their dossier and digital twin.")

def render_phase1_intent_analysis(api_client: JorgeAPIClient):
    """Render the Phase 1 Intent Analysis (FRS & PCS) section."""
    st.markdown(f'### {get_svg_icon("intelligence")} Phase 1: Intent Analysis (FRS & PCS)', unsafe_allow_html=True)
    st.markdown("Semantic & Psychographic Lead Analysis - 2026 Strategic Roadmap")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="elite-card" style="padding: 1.5rem;">', unsafe_allow_html=True)
        st.subheader("💬 Test Conversation")
        
        user_input = st.text_area("Lead Message", "I need to sell fast because I'm relocating for a job transfer. In 30 days. It needs work, selling as-is.", height=100)
        
        if st.button("🧠 Analyze Intent", type="primary", use_container_width=True):
            with st.spinner("Decoding semantic intent..."):
                # Mock a conversation history
                history = [{"role": "user", "content": user_input}]
                analysis = run_async(api_client.get_intent_profile("demo_lead", history))
                st.session_state['phase1_analysis'] = analysis
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        if 'phase1_analysis' in st.session_state:
            data = st.session_state['phase1_analysis']
            frs = data['frs']
            pcs = data['pcs']
            
            st.markdown('<div class="elite-card" style="padding: 1.5rem;">', unsafe_allow_html=True)
            st.markdown(f"#### FRS: {frs['total_score']} ({frs['classification']})")
            
            # FRS Breakdown
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                st.metric("Motivation", frs['motivation']['score'], help=frs['motivation']['category'])
                st.metric("Timeline", frs['timeline']['score'], help=frs['timeline']['category'])
            with col2_2:
                st.metric("Condition", frs['condition']['score'], help=frs['condition']['category'])
                st.metric("Price", frs['price']['score'], help=frs['price']['category'])
            
            st.markdown("---")
            st.markdown(f"#### PCS: {pcs['total_score']} (Commitment)")
            st.info(f"👉 Next Action: **{data['next_best_action']}**")
            
            if data['stall_breaker_suggested']:
                 st.warning(f"🔓 Stall Breaker: {data['stall_breaker_suggested']}")
                 if st.button("🚀 EXECUTE STALL-BREAKER", type="primary", use_container_width=True):
                     st.session_state.global_decisions.append({
                         "action": "Stall-Breaker Executed",
                         "why": f"Detected stall marker in message. Triggering Jorge-Style response.",
                         "time": datetime.now(timezone.utc).strftime("%H:%M:%S")
                     })
                     st.toast("STALL-BREAKER SENT: Engaging no-BS protocol.", icon="🧠")
            
            st.markdown("---")
            st.subheader("🛡️ Zillow Defense")
            if st.button("📊 Generate Zillow-Defense CMA", use_container_width=True):
                if CMA_GENERATOR_AVAILABLE:
                    with st.spinner("Calculating AI Valuation vs Zestimate..."):
                        generator = CMAGenerator()
                        report = run_async(generator.generate_report("Subject Property", zestimate=850000))
                        pdf_url = PDFRenderer.generate_pdf_url(report)
                        st.session_state['cma_report_url'] = pdf_url
                        st.session_state.global_decisions.append({
                            "action": "CMA Generated",
                            "why": "Zillow-Defense protocol activated for lead valuation.",
                            "time": datetime.now(timezone.utc).strftime("%H:%M:%S")
                        })
                        st.success("✅ Zillow-Defense CMA Ready!")
                else:
                    st.error("CMA Generator not available.")
            
            if 'cma_report_url' in st.session_state:
                st.markdown(f'<a href="{st.session_state["cma_report_url"]}" target="_blank" style="text-decoration: none;"><div style="padding: 10px; background: var(--elite-accent); color: black; text-align: center; border-radius: 8px; font-weight: bold;">📥 DOWNLOAD ZILLOW-DEFENSE PDF</div></a>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Enter a message to analyze lead intent.")

def render_war_room_section():
    """Render the Phase 10 War Room Heat Map and Pattern Discovery."""
    st.markdown(f'### {get_svg_icon("intelligence")} Jorge War Room: Market Heat', unsafe_allow_html=True)
    
    service = get_war_room_service()
    data = run_async(service.get_heat_map_data())
    
    # Summary Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Active Leads", data['market_summary']['total_active_leads'], delta="+12%")
    with col2: st.metric("Hottest Area", data['market_summary']['hottest_area'])
    with col3: st.metric("Avg Heat Value", f"{data['market_summary']['avg_market_heat']}/100", delta="3.2")
    with col4: st.metric("MOAT Status", "SECURE", help="Intelligence Layer Integrity")
    
    st.divider()
    
    col_map, col_graph = st.columns([2, 1])
    
    with col_map:
        st.markdown('<div class="elite-card" style="padding: 1rem;">', unsafe_allow_html=True)
        st.subheader("🔥 Property Heat Map")
        
        props_df = pd.DataFrame(data['properties'])
        
        if not props_df.empty:
            # Mapbox scatter plot (simplified for demo if token not present)
            fig = px.scatter(
                props_df,
                x="lng",
                y="lat",
                color="heat_value",
                size="leads_count",
                hover_name="address",
                color_continuous_scale="rdbu_r",
                title="Geographic Lead Density"
            )
            st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)
        else:
            st.info("No active property data available.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_graph:
        st.markdown('<div class="elite-card" style="padding: 1rem;">', unsafe_allow_html=True)
        st.subheader("🔗 Pattern Discovery")
        
        # Phase 10: AI Detected Patterns from Service
        patterns = data.get('patterns', [])
        
        for p in patterns:
            color = "var(--negotiation-neon)" if p.get('priority') == "HIGH" else "var(--elite-accent)"
            st.markdown(f"""
                <div style="margin-bottom: 12px; padding: 12px; border-left: 2px solid {color}; background: rgba(0,229,255,0.03); border-radius: 4px;">
                    <div style="font-size: 0.6rem; font-weight: 800; color: {color}; margin-bottom: 4px;">{p['type']}</div>
                    <div style="font-size: 0.8rem; line-height: 1.4; color: white;">{p['desc']}</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        st.subheader("🔗 Lead Relationships")
        
        # Enhanced Relationship Graph (Visual representation)
        rels = data['relationships']
        
        # Create a simple visual graph using dots and lines
        for rel in rels[:10]: # Limit to top 10 for UI clarity
            strength_width = int(rel['strength'] * 100)
            st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                    <div style="font-size: 0.7rem; color: #8B949E; width: 60px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{rel['source']}</div>
                    <div style="flex-grow: 1; height: 2px; background: rgba(255,255,255,0.1); position: relative;">
                        <div style="position: absolute; left: 0; top: 0; height: 100%; width: {strength_width}%; background: var(--negotiation-neon); box-shadow: 0 0 5px var(--negotiation-neon);"></div>
                    </div>
                    <div style="font-size: 0.7rem; color: var(--elite-accent); width: 60px;">{rel['target']}</div>
                </div>
            """, unsafe_allow_html=True)
            
        if len(rels) > 10:
            st.caption(f"+ {len(rels) - 10} more relationships detected")
        st.markdown('</div>', unsafe_allow_html=True)

def render_jorge_lead_bot_dashboard():
    """Main function to render Jorge's Lead Bot Dashboard."""
    inject_elite_css()
    
    # Header
    st.markdown("""
        <div style=\"background: var(--obsidian-card); backdrop-filter: var(--glass-blur); padding: 1.5rem 2.5rem; border-radius: 16px; border: 0.5px solid var(--obsidian-border); border-top: 1px solid rgba(255, 255, 255, 0.12); margin-bottom: 2.5rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);\">
            <div>
                <h1 style=\"font-family: 'Space Grotesk', sans-serif; font-size: 2.5rem; font-weight: 700; margin: 0; color: #FFFFFF; letter-spacing: -0.04em; text-transform: uppercase;\'>🎯 JORGE'S LEAD COMMAND</h1>
                <p style=\"font-family: 'Inter', sans-serif; font-size: 1rem; margin: 0.5rem 0 0 0; color: #8B949E; font-weight: 500; letter-spacing: 0.02em;\'>Obsidian Command // Elite Lead Intelligence v4.2.0</p>
            </div>
            <div style=\"text-align: right;">
                <div class=\"status-pulse\"></div>
                <span style=\"color: #6366F1; font-weight: 800; letter-spacing: 0.1em;\'>SYSTEM ONLINE</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    api_client = get_api_client()
    render_integration_dashboard(api_client)
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12 = st.tabs([
        "🎯 Neural Scoring",
        "📊 Pipeline",
        "🎤 Voice AI",
        "💼 Seller Bot",
        "👻 Follow-Up",
        "🤝 Retention",
        "📈 Market Intelligence",
        "🏠 Property AI",
        "📊 Analytics",
        "🧠 Intent Analysis",
        "🔥 War Room",
        "🎤 Whisper Mode"
    ])

    with tab1: render_enhanced_lead_scoring_section(api_client)
    with tab2: render_lead_pipeline_section(api_client)
    with tab3: render_voice_ai_section(api_client)
    with tab4: render_jorge_seller_bot_section(api_client)
    with tab5: render_followup_orchestrator(api_client)
    with tab6: render_retention_section()
    with tab7: render_market_prediction_section()
    with tab8: render_property_matching_integration_section()
    with tab9: render_analytics_integration_section()
    with tab10: render_phase1_intent_analysis(api_client)
    with tab11: render_war_room_section()
    with tab12: render_whisper_mode()

    # Neural Uplink Terminal at the bottom
    st.markdown("---")
    simulated_logs = [
        {"prefix": "[ANALYSIS]", "message": "Detecting buyer urgency for Sarah Johnson... high intent detected."},
        {"prefix": "[PROTOCOL]", "message": "Take-Away Mode engaged for 750K property bracket."},
        {"prefix": "[SYNTHESIS]", "message": "Neural Health score updated for Lead ID: 005."},
        {"prefix": "[VOICE_AI]", "message": "Active call session: +1-555-0192 (Qualification in progress)"},
        {"prefix": "[MARKET]", "message": "Predictive model identifying supply squeeze in Upland."},
    ]
    render_terminal_log(simulated_logs)

    # Floating Tactical Command Dock
    render_tactical_dock()

# Main function call
if __name__ == "__main__":
    render_jorge_lead_bot_dashboard()
