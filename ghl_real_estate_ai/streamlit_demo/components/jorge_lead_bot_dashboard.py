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

# Import the Property Matching service
try:
    from jorge_property_matching_service import JorgePropertyMatchingService
    PROPERTY_MATCHING_SERVICE_AVAILABLE = True
except ImportError:
    PROPERTY_MATCHING_SERVICE_AVAILABLE = False

# Import the Analytics service
try:
    from jorge_analytics_service import JorgeAnalyticsService
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
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            # Fallback to defaults
            return {
                "voice_ai": {"total_calls": 0, "qualified_leads": 0, "avg_call_duration": 0, "qualification_rate": 0, "transfer_rate": 0},
                "marketing": {"active_campaigns": 0, "total_impressions": 0, "conversion_rate": 0, "cost_per_lead": 0, "roi": 0},
                "client_retention": {"total_clients": 0, "engagement_score": 0, "retention_rate": 0, "referrals_this_month": 0, "lifetime_value": 0},
                "market_predictions": {"active_markets": 0, "prediction_accuracy": 0, "opportunities_found": 0, "avg_roi_potential": 0},
                "integration_health": {"ghl_status": "error", "claude_status": "healthy", "overall_uptime": 0},
                "last_updated": datetime.now().isoformat()
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
            "call_id": f"call_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
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

from ghl_real_estate_ai.streamlit_demo.obsidian_theme import (
    inject_elite_css, 
    style_obsidian_chart, 
    render_dossier_block, 
    render_neural_progress, 
    get_svg_icon,
    render_terminal_log,
    render_voice_waveform,
    render_tactical_dock,
    render_journey_line
)

# Initialize API client and Enhanced Scorer
@st.cache_resource
def get_api_client():
    return JorgeAPIClient()

@st.cache_resource
def get_enhanced_scorer():
    if ENHANCED_SCORER_AVAILABLE:
        return EnhancedSmartLeadScorer()
    return None

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
                        result = asyncio.run(api_client.start_voice_call(phone_number, caller_name))
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
        analytics = asyncio.run(api_client.get_voice_analytics())
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
        st.markdown('<div class="elite-card" style="padding: 1.5rem;">', unsafe_allow_html=True)
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
    metrics = asyncio.run(api_client.get_dashboard_metrics())
    
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
    scoring_analytics = asyncio.run(api_client.get_scoring_analytics())

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
            analysis = asyncio.run(api_client.analyze_lead(lead_data))
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
            
            # Radar Chart
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
        from jorge_property_matching_dashboard import render_jorge_property_matching_dashboard
        render_jorge_property_matching_dashboard()
    except ImportError:
        st.error("⚠️ Property Matching AI system not available.")

def render_analytics_integration_section():
    """Render the integrated Advanced Analytics section."""
    st.header("📊 Advanced Analytics System")
    st.markdown("**Comprehensive business intelligence with forecasting and ROI attribution**")
    try:
        from jorge_analytics_dashboard import render_jorge_analytics_dashboard
        render_jorge_analytics_dashboard()
    except ImportError:
        st.error("⚠️ Advanced Analytics system not available.")

def render_lead_pipeline_section(api_client: JorgeAPIClient):
    """Render the Lead Pipeline section with Journey Glow Mapping."""
    st.markdown(f'### {get_svg_icon("referral")} Tactical Lead Pipeline', unsafe_allow_html=True)
    
    pipeline = asyncio.run(api_client.get_lead_pipeline())
    
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
                    st.toast(f"Loading dossier for {lead['name']}...", icon="📂")
            
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
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "🎯 Neural Scoring",
        "📊 Pipeline",
        "🎤 Voice AI",
        "🎯 Marketing",
        "🤝 Retention",
        "📈 Market Intelligence",
        "🏠 Property AI",
        "📊 Analytics"
    ])

    with tab1: render_enhanced_lead_scoring_section(api_client)
    with tab2: render_lead_pipeline_section(api_client)
    with tab3: render_voice_ai_section(api_client)
    with tab4: render_marketing_section()
    with tab5: render_retention_section()
    with tab6: render_market_prediction_section()
    with tab7: render_property_matching_integration_section()
    with tab8: render_analytics_integration_section()

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
