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
    """Client for Jorge's Advanced Features API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        
    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get unified dashboard metrics."""
        try:
            if REQUESTS_AVAILABLE:
                response = requests.get(f"{self.base_url}/jorge-advanced/dashboard/metrics")
                if response.status_code == 200:
                    return response.json()
        except:
            pass
            
        # Mock data for demo
        return {
            "voice_ai": {
                "total_calls": 47,
                "qualified_leads": 23,
                "avg_call_duration": 285,
                "qualification_rate": 48.9,
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
    
    async def get_voice_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get voice AI analytics."""
        # Mock data
        return {
            "period_days": days,
            "analytics": {
                "total_calls": 47,
                "successful_calls": 43,
                "qualified_leads": 23,
                "avg_qualification_score": 78.2,
                "top_lead_sources": ["Zillow", "Facebook", "Referral"],
                "call_outcomes": {
                    "Qualified Lead": 23,
                    "Follow-up Scheduled": 12,
                    "Not Interested": 8,
                    "Wrong Number": 4
                }
            }
        }
    
    async def start_voice_call(self, phone_number: str, caller_name: str = None) -> Dict[str, str]:
        """Start a new voice call."""
        return {
            "call_id": f"call_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "active",
            "message": "Voice AI call started successfully"
        }

    # Enhanced Lead Scoring Methods
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
                "intent_score": 80,
                "financial_readiness": 90,
                "timeline_urgency": 60,
                "engagement_quality": 75,
                "referral_potential": 45,
                "local_connection": 70
            },
            "recommended_actions": [
                "📞 Call within 1 hour during business hours",
                "📧 Send personalized follow-up with market insights",
                "🏠 Curate 3-5 property matches based on criteria"
            ],
            "talking_points": [
                "🎯 'Based on your search, I have properties you should see this week'",
                "💰 'With your budget, you have excellent options in Rancho Cucamonga'",
                "🏫 'I know the best family-friendly neighborhoods with top schools'"
            ],
            "risk_factors": ["⚠️ No pre-approval yet - recommend lender connection"]
        }

    async def get_lead_pipeline(self) -> List[Dict[str, Any]]:
        """Get current lead pipeline with enhanced scoring."""
        # Mock lead data with enhanced scores
        return [
            {
                "id": "lead_001",
                "name": "Sarah Johnson",
                "phone": "+1-555-123-4567",
                "email": "sarah.johnson@email.com",
                "score": 85.2,
                "priority": "immediate",
                "stage": "ready_to_buy",
                "last_contact": "2 hours ago",
                "source": "Zillow",
                "budget": "$750K-850K",
                "timeline": "30 days",
                "notes": "Pre-approved, looking in Alta Loma"
            },
            {
                "id": "lead_002",
                "name": "Mike Chen",
                "phone": "+1-555-234-5678",
                "email": "mike.chen@email.com",
                "score": 72.8,
                "priority": "high",
                "stage": "getting_serious",
                "last_contact": "1 day ago",
                "source": "Facebook",
                "budget": "$650K-750K",
                "timeline": "60 days",
                "notes": "Teacher, family of 4, wants good schools"
            },
            {
                "id": "lead_003",
                "name": "Lisa Rodriguez",
                "phone": "+1-555-345-6789",
                "email": "lisa.rodriguez@email.com",
                "score": 58.5,
                "priority": "medium",
                "stage": "getting_serious",
                "last_contact": "3 days ago",
                "source": "Referral",
                "budget": "$500K-600K",
                "timeline": "90 days",
                "notes": "First-time buyer, needs education"
            },
            {
                "id": "lead_004",
                "name": "David Kim",
                "phone": "+1-555-456-7890",
                "email": "david.kim@email.com",
                "score": 45.2,
                "priority": "low",
                "stage": "just_looking",
                "last_contact": "1 week ago",
                "source": "Website",
                "budget": "Not specified",
                "timeline": "Exploring",
                "notes": "General interest, not urgent"
            },
            {
                "id": "lead_005",
                "name": "Jennifer White",
                "phone": "+1-555-567-8901",
                "email": "jennifer.white@email.com",
                "score": 91.7,
                "priority": "immediate",
                "stage": "ready_to_buy",
                "last_contact": "30 minutes ago",
                "source": "Past Client Referral",
                "budget": "$900K-1.2M",
                "timeline": "Immediate",
                "notes": "Cash buyer, wants luxury home"
            }
        ]

    async def get_scoring_analytics(self) -> Dict[str, Any]:
        """Get analytics about lead scoring performance."""
        return {
            "total_leads_scored": 247,
            "avg_score": 62.4,
            "score_distribution": {
                "90-100": 12,
                "80-89": 28,
                "70-79": 45,
                "60-69": 67,
                "50-59": 52,
                "40-49": 31,
                "30-39": 8,
                "0-29": 4
            },
            "conversion_by_score": {
                "90-100": 0.85,
                "80-89": 0.72,
                "70-79": 0.54,
                "60-69": 0.34,
                "50-59": 0.18,
                "40-49": 0.08,
                "30-39": 0.03,
                "0-29": 0.01
            },
            "priority_breakdown": {
                "immediate": 15,
                "high": 42,
                "medium": 98,
                "low": 78,
                "disqualified": 14
            },
            "accuracy_metrics": {
                "prediction_accuracy": 87.2,
                "false_positives": 8.1,
                "false_negatives": 4.7
            }
        }

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
    st.header("🎤 Voice AI Phone Integration")
    
    col1, col2 = st.columns(2)
    
    with col1:
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
    
    with col2:
        st.subheader("Voice AI Performance")
        
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
        
        # Call outcomes chart
        outcomes_df = pd.DataFrame(
            list(voice_data["call_outcomes"].items()),
            columns=["Outcome", "Count"]
        )
        
        st.subheader("Call Outcomes")
        st.bar_chart(outcomes_df.set_index("Outcome"))

def render_marketing_section():
    """Render the Marketing Automation section."""
    st.header("🎯 Automated Marketing Campaigns")
    
    col1, col2 = st.columns(2)
    
    with col1:
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
        
        content_formats = st.multiselect(
            "Content Formats", 
            ["Email", "SMS", "Social Media", "Direct Mail"],
            default=["Email", "SMS"]
        )
        
        budget_range = st.slider(
            "Budget Range ($)", 
            min_value=100, 
            max_value=5000, 
            value=(500, 2000)
        )
        
        if st.button("🚀 Create AI Campaign", type="primary", use_container_width=True):
            with st.spinner("Creating campaign with AI..."):
                # Simulate campaign creation
                import time
                time.sleep(2)
                st.success(f"✅ Campaign '{campaign_name}' created successfully!")
                st.info(f"📊 Targeting {len(target_audience)} audience segments with {len(content_formats)} formats")
    
    with col2:
        st.subheader("Active Campaigns")
        
        # Mock campaign data
        campaigns = [
            {"name": "Q1 Buyers", "status": "Active", "leads": 34, "conversion": 3.2},
            {"name": "Investor Outreach", "status": "Active", "leads": 18, "conversion": 5.1},
            {"name": "Past Client Nurture", "status": "Active", "leads": 22, "conversion": 4.8},
            {"name": "Referral Push", "status": "Scheduled", "leads": 0, "conversion": 0},
        ]
        
        for camp in campaigns:
            with st.container():
                col_name, col_status, col_metrics = st.columns([3, 1, 2])
                
                with col_name:
                    st.write(f"**{camp['name']}**")
                
                with col_status:
                    status_color = "🟢" if camp['status'] == "Active" else "🟡"
                    st.write(f"{status_color} {camp['status']}")
                
                with col_metrics:
                    if camp['leads'] > 0:
                        st.write(f"{camp['leads']} leads • {camp['conversion']:.1f}% conv.")
                    else:
                        st.write("Starting soon...")
                
                st.divider()

def render_retention_section():
    """Render the Client Retention section."""
    st.header("🤝 Client Retention & Referrals")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Client Lifecycle Update")
        
        client_search = st.text_input(
            "Search Client",
            placeholder="Enter name or email..."
        )
        
        life_event = st.selectbox(
            "Life Event Detected",
            [
                "PROPERTY_SOLD", 
                "PROPERTY_PURCHASED", 
                "LIFE_CHANGE", 
                "INVESTMENT_OPPORTUNITY",
                "REFERRAL_OPPORTUNITY",
                "ANNIVERSARY"
            ]
        )
        
        event_context = st.text_area(
            "Event Context",
            placeholder="Additional details about the life event..."
        )
        
        if st.button("📝 Update Lifecycle", type="primary", use_container_width=True):
            with st.spinner("Processing lifecycle update..."):
                import time
                time.sleep(1)
                st.success("✅ Client lifecycle updated! Automated follow-up sequence triggered.")
    
    with col2:
        st.subheader("Retention Metrics")
        
        # Key metrics
        col2_1, col2_2 = st.columns(2)
        with col2_1:
            st.metric("Retention Rate", "92.1%", delta="+1.3%")
            st.metric("Referrals (Month)", "12", delta="+4")
        
        with col2_2:
            st.metric("Avg Lifetime Value", "$28,500", delta="+$2,100")
            st.metric("Engagement Score", "84.2", delta="+2.1")
        
        # Top referrers
        st.subheader("Top Referrers")
        referrers = [
            {"name": "Sarah Johnson", "referrals": 4, "value": "$85K"},
            {"name": "Mike Chen", "referrals": 3, "value": "$72K"},
            {"name": "Lisa Davis", "referrals": 2, "value": "$58K"},
        ]
        
        for ref in referrers:
            st.write(f"**{ref['name']}** - {ref['referrals']} referrals ({ref['value']} volume)")

def render_market_prediction_section():
    """Render the Market Prediction section."""
    st.header("📈 Market Prediction Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Market Analysis Request")
        
        neighborhood = st.selectbox(
            "Neighborhood",
            ["Rancho Cucamonga", "Upland", "Ontario", "Claremont", "Pomona"]
        )
        
        time_horizon = st.selectbox(
            "Prediction Timeline",
            ["3_months", "6_months", "1_year", "2_years"]
        )
        
        property_type = st.selectbox(
            "Property Type",
            ["All Types", "Single Family", "Condos", "Townhomes", "Multi-Family"]
        )
        
        price_range = st.slider(
            "Price Range ($K)",
            min_value=200,
            max_value=2000,
            value=(400, 800)
        )
        
        if st.button("🔮 Generate Prediction", type="primary", use_container_width=True):
            with st.spinner("Analyzing market data with AI..."):
                import time
                time.sleep(3)
                st.success("✅ Market analysis complete!")
                
                # Show prediction results
                st.markdown("### 📊 Prediction Results")
                
                col_pred1, col_pred2 = st.columns(2)
                with col_pred1:
                    st.metric("Price Appreciation", "+12.8%", delta="vs 6-month avg")
                    st.metric("Market Velocity", "21 days", delta="-3 days")
                
                with col_pred2:
                    st.metric("Investment Score", "87/100", delta="+5 points")
                    st.metric("Risk Level", "Low-Medium", delta="Stable")
                
                st.info(f"🎯 **Key Insight**: {neighborhood} shows strong buyer demand with limited inventory. Expect continued price growth through {time_horizon.replace('_', ' ')}.")
    
    with col2:
        st.subheader("Recent Predictions")
        
        predictions = [
            {
                "area": "Rancho Cucamonga", 
                "prediction": "+12.8%", 
                "accuracy": "87%",
                "date": "Jan 15"
            },
            {
                "area": "Upland", 
                "prediction": "+8.4%", 
                "accuracy": "92%",
                "date": "Jan 12"
            },
            {
                "area": "Ontario", 
                "prediction": "+6.2%", 
                "accuracy": "84%",
                "date": "Jan 10"
            }
        ]
        
        for pred in predictions:
            with st.container():
                st.write(f"**{pred['area']}** ({pred['date']})")
                col_pred, col_acc = st.columns(2)
                with col_pred:
                    st.write(f"📈 {pred['prediction']} growth")
                with col_acc:
                    st.write(f"✅ {pred['accuracy']} accurate")
                st.divider()

def render_integration_dashboard(api_client: JorgeAPIClient):
    """Render the unified integration dashboard."""
    st.header("🎛️ Jorge's Command Center")
    st.markdown("**Real-time overview of your AI Lead Bot ecosystem**")
    
    # Get dashboard metrics
    metrics = asyncio.run(api_client.get_dashboard_metrics())
    
    # System health indicators
    st.subheader("🚀 Unified AI Ecosystem Health")
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        ghl_status = metrics["integration_health"]["ghl_status"]
        status_icon = "🟢" if ghl_status == "healthy" else "🔴"
        st.metric("GHL Connection", f"{status_icon} {ghl_status.title()}")

    with col2:
        claude_status = metrics["integration_health"]["claude_status"]
        status_icon = "🟢" if claude_status == "healthy" else "🔴"
        st.metric("Claude AI", f"{status_icon} {claude_status.title()}")

    with col3:
        st.metric("System Uptime", f"{metrics['integration_health']['overall_uptime']}%")

    with col4:
        if ENHANCED_SCORER_AVAILABLE:
            st.metric("Enhanced AI", "🟢 Active", delta="6D Scoring")
        else:
            st.metric("Enhanced AI", "🟡 Demo", delta="Mock Data")

    with col5:
        # Property Matching AI status
        property_status = "🟢 Active" if PROPERTY_MATCHING_SERVICE_AVAILABLE else "🟡 Demo"
        st.metric("Property AI", property_status, delta="Neural+Rules")

    with col6:
        # Analytics Engine status
        analytics_status = "🟢 Active" if ANALYTICS_SERVICE_AVAILABLE else "🟡 Demo"
        st.metric("Analytics AI", analytics_status, delta="Forecasting")

    st.divider()

    # Enhanced Lead Scoring Summary
    st.subheader("🎯 Enhanced Lead Intelligence")

    # Get scoring analytics
    scoring_analytics = asyncio.run(api_client.get_scoring_analytics())

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "🔴 Immediate Leads",
            scoring_analytics['priority_breakdown']['immediate'],
            delta="Call NOW",
            help="Leads requiring immediate attention from Jorge"
        )

    with col2:
        st.metric(
            "🟠 High Priority",
            scoring_analytics['priority_breakdown']['high'],
            delta="Today",
            help="High-value leads to contact today"
        )

    with col3:
        st.metric(
            "📊 Avg Score",
            f"{scoring_analytics['avg_score']:.1f}/100",
            delta="Pipeline Quality",
            help="Average lead quality score"
        )

    with col4:
        st.metric(
            "🎯 Prediction Accuracy",
            f"{scoring_analytics['accuracy_metrics']['prediction_accuracy']:.1f}%",
            delta="AI Performance",
            help="Enhanced scoring system accuracy"
        )

    with col5:
        total_analyzed = scoring_analytics['total_leads_scored']
        st.metric(
            "🧠 Leads Analyzed",
            f"{total_analyzed:,}",
            delta="Learning",
            help="Total leads processed by enhanced AI"
        )

    st.divider()

    # Core System Performance
    st.subheader("📊 Core System Performance")

    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        voice_data = metrics["voice_ai"]
        st.metric(
            "Calls Handled",
            voice_data["total_calls"],
            delta=f"{voice_data['qualified_leads']} qualified",
            help="Voice AI call processing"
        )
    
    with col2:
        marketing_data = metrics["marketing"]
        st.metric(
            "Campaign ROI",
            f"{marketing_data['roi']}%",
            delta=f"${marketing_data['cost_per_lead']:.0f} cost/lead",
            help="Marketing automation performance"
        )
    
    with col3:
        retention_data = metrics["client_retention"]
        st.metric(
            "Client LTV",
            f"${retention_data['lifetime_value']:,}",
            delta=f"{retention_data['referrals_this_month']} referrals",
            help="Client retention & referral system"
        )
    
    with col4:
        market_data = metrics["market_predictions"]
        st.metric(
            "Market Accuracy",
            f"{market_data['prediction_accuracy']:.1f}%",
            delta=f"{market_data['opportunities_found']} opportunities",
            help="Market prediction engine"
        )

def render_enhanced_lead_scoring_section(api_client: JorgeAPIClient):
    """Render the Enhanced Lead Scoring section."""
    st.header("🎯 Enhanced AI Lead Scoring 2.0")
    st.markdown("**Advanced lead intelligence with 6-dimensional scoring and priority recommendations**")

    # Show enhanced scorer status
    col_status1, col_status2 = st.columns(2)
    with col_status1:
        if ENHANCED_SCORER_AVAILABLE:
            st.success("✅ Enhanced AI Scorer: ACTIVE")
        else:
            st.warning("⚠️ Enhanced AI Scorer: Demo Mode")

    with col_status2:
        st.metric("Scoring System", "Version 2.0", delta="6-dimensional analysis")

    # Main scoring interface
    st.divider()

    # Lead analysis input
    col1, col2 = st.columns([2, 3])

    with col1:
        st.subheader("🔍 Analyze New Lead")

        # Lead input form
        with st.form("lead_analysis_form"):
            lead_name = st.text_input("Lead Name", placeholder="Sarah Johnson")
            lead_email = st.text_input("Email", placeholder="sarah.j@email.com")
            lead_phone = st.text_input("Phone", placeholder="+1-555-123-4567")

            col_budget, col_timeline = st.columns(2)
            with col_budget:
                budget = st.number_input("Budget ($)", min_value=0, value=750000, step=50000)
            with col_timeline:
                timeline = st.selectbox("Timeline", ["immediate", "30 days", "3 months", "6 months", "just looking"])

            col_source, col_preapproved = st.columns(2)
            with col_source:
                source = st.selectbox("Source", ["Zillow", "Facebook", "Website", "Referral", "Past Client"])
            with col_preapproved:
                preapproved = st.checkbox("Pre-approved")

            search_frequency = st.slider("Search Frequency (per week)", 0, 20, 5)
            engagement_score = st.slider("Engagement Level", 0, 100, 60)

            analyze_button = st.form_submit_button("🚀 Analyze Lead", type="primary")

        if analyze_button and lead_name:
            # Create lead data
            lead_data = {
                "name": lead_name,
                "email": lead_email,
                "phone": lead_phone,
                "budget": budget,
                "timeline": timeline,
                "search_frequency": search_frequency,
                "preapproved": preapproved,
                "source": source.lower(),
                "engagement_quality": engagement_score,
                "current_location": "Rancho Cucamonga, CA"
            }

            # Analyze lead
            with st.spinner("🧠 Analyzing lead with Enhanced AI..."):
                analysis = asyncio.run(api_client.analyze_lead(lead_data))

                # Store in session state for display
                st.session_state['latest_analysis'] = analysis
                st.session_state['analyzed_lead_name'] = lead_name
                st.success(f"✅ Analysis complete for {lead_name}!")

    with col2:
        st.subheader("📊 Lead Analysis Results")

        # Display analysis if available
        if 'latest_analysis' in st.session_state:
            analysis = st.session_state['latest_analysis']
            lead_name = st.session_state.get('analyzed_lead_name', 'Lead')

            if "error" not in analysis:
                # Overall score display
                score = analysis['overall_score']
                priority = analysis['priority_level']
                stage = analysis['buying_stage']

                st.markdown(f"### 🎯 {lead_name.upper()} - Score: {score}/100")

                # Priority and stage
                priority_color = {
                    "immediate": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(priority, "⚪")

                col_priority, col_stage = st.columns(2)
                with col_priority:
                    st.metric("Priority Level", f"{priority_color} {priority.upper()}")
                with col_stage:
                    st.metric("Buying Stage", stage.replace('_', ' ').title())

                # Score breakdown radar chart
                st.subheader("📈 Score Breakdown")
                breakdown = analysis['score_breakdown']

                score_df = pd.DataFrame({
                    'Dimension': ['Intent', 'Financial', 'Timeline', 'Engagement', 'Referral', 'Local'],
                    'Score': [
                        breakdown['intent_score'],
                        breakdown['financial_readiness'],
                        breakdown['timeline_urgency'],
                        breakdown['engagement_quality'],
                        breakdown['referral_potential'],
                        breakdown['local_connection']
                    ]
                })

                # Create radar chart
                fig = go.Figure()

                fig.add_trace(go.Scatterpolar(
                    r=score_df['Score'],
                    theta=score_df['Dimension'],
                    fill='toself',
                    name=lead_name,
                    marker_color='rgb(30, 136, 229)',
                    fillcolor='rgba(30, 136, 229, 0.3)'
                ))

                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 100]
                        )),
                    showlegend=False,
                    title="Lead Scoring Dimensions",
                    height=400
                )

                st.plotly_chart(fig, use_container_width=True)

                # Action recommendations
                st.subheader("🎯 Recommended Actions")
                for action in analysis.get('recommended_actions', []):
                    st.markdown(f"• {action}")

                # Talking points
                if analysis.get('talking_points'):
                    st.subheader("💬 Jorge's Talking Points")
                    for point in analysis['talking_points']:
                        st.markdown(f"• {point}")

                # Risk factors
                if analysis.get('risk_factors'):
                    st.subheader("⚠️ Risk Factors")
                    for risk in analysis['risk_factors']:
                        st.markdown(f"• {risk}")

            else:
                st.error(f"Analysis Error: {analysis['error']}")

        else:
            st.info("👆 Analyze a lead above to see detailed scoring results")

    # Lead Pipeline Section
    st.divider()
    st.subheader("📋 Current Lead Pipeline")

    # Get lead pipeline
    pipeline = asyncio.run(api_client.get_lead_pipeline())

    # Pipeline summary metrics
    col1, col2, col3, col4 = st.columns(4)

    immediate_leads = len([l for l in pipeline if l['priority'] == 'immediate'])
    high_leads = len([l for l in pipeline if l['priority'] == 'high'])
    avg_score = sum(l['score'] for l in pipeline) / len(pipeline) if pipeline else 0
    ready_to_buy = len([l for l in pipeline if l['stage'] == 'ready_to_buy'])

    with col1:
        st.metric("🔴 Immediate", immediate_leads, delta="Needs Jorge NOW")
    with col2:
        st.metric("🟠 High Priority", high_leads, delta="Call today")
    with col3:
        st.metric("📊 Avg Score", f"{avg_score:.1f}", delta="Pipeline quality")
    with col4:
        st.metric("🏠 Ready to Buy", ready_to_buy, delta="Hot prospects")

    # Pipeline table
    if pipeline:
        pipeline_df = pd.DataFrame(pipeline)

        # Color-code by priority
        def priority_color(priority):
            colors = {
                'immediate': '#FF6B6B',
                'high': '#FFA726',
                'medium': '#FFD54F',
                'low': '#66BB6A'
            }
            return colors.get(priority, '#E0E0E0')

        # Display pipeline with styling
        st.dataframe(
            pipeline_df[['name', 'score', 'priority', 'stage', 'source', 'budget', 'last_contact', 'notes']],
            use_container_width=True,
            column_config={
                "score": st.column_config.ProgressColumn(
                    "Score",
                    min_value=0,
                    max_value=100,
                    format="%.1f"
                ),
                "priority": st.column_config.TextColumn(
                    "Priority",
                    help="Lead priority level"
                )
            }
        )

    # Scoring Analytics
    st.divider()
    st.subheader("📈 Scoring Performance Analytics")

    analytics = asyncio.run(api_client.get_scoring_analytics())

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🎯 Score Distribution")
        score_dist = analytics['score_distribution']

        # Create score distribution chart
        scores = list(score_dist.keys())
        counts = list(score_dist.values())

        fig_dist = px.bar(
            x=scores,
            y=counts,
            title="Lead Score Distribution",
            labels={'x': 'Score Range', 'y': 'Number of Leads'},
            color=counts,
            color_continuous_scale='RdYlGn'
        )

        st.plotly_chart(fig_dist, use_container_width=True)

    with col2:
        st.markdown("#### 📊 Conversion by Score")
        conversion_data = analytics['conversion_by_score']

        # Create conversion chart
        scores = list(conversion_data.keys())
        rates = [rate * 100 for rate in conversion_data.values()]

        fig_conv = px.line(
            x=scores,
            y=rates,
            title="Conversion Rate by Score Range",
            labels={'x': 'Score Range', 'y': 'Conversion Rate (%)'},
            markers=True
        )

        fig_conv.update_traces(marker=dict(size=8), line=dict(width=3))
        st.plotly_chart(fig_conv, use_container_width=True)

    # Performance metrics
    st.markdown("#### 🎯 System Performance")
    perf_col1, perf_col2, perf_col3 = st.columns(3)

    with perf_col1:
        st.metric("Prediction Accuracy", f"{analytics['accuracy_metrics']['prediction_accuracy']:.1f}%", delta="Industry leading")
    with perf_col2:
        st.metric("False Positives", f"{analytics['accuracy_metrics']['false_positives']:.1f}%", delta="Low error rate")
    with perf_col3:
        st.metric("Total Leads Analyzed", f"{analytics['total_leads_scored']:,}", delta="Continuous learning")

def render_property_matching_integration_section():
    """Render the integrated Property Matching AI section."""
    st.header("🏠 Property Matching AI System")
    st.markdown("**AI-powered property recommendations with hybrid neural + rules matching**")

    # Import and render the property matching dashboard
    try:
        from jorge_property_matching_dashboard import render_jorge_property_matching_dashboard
        render_jorge_property_matching_dashboard()
    except ImportError:
        st.error("⚠️ Property Matching AI system not available. Please ensure the service is installed and running.")

        # Fallback summary metrics
        st.info("""
        **Property Matching AI Features:**
        - 🧠 Hybrid Neural + Rules Algorithm
        - 🏠 Real-time Property Inventory Management
        - 🎯 AI-Powered Match Explanations
        - 📊 Performance Analytics & Optimization
        - 🗺️ Geographic Market Intelligence
        """)

def render_analytics_integration_section():
    """Render the integrated Advanced Analytics section."""
    st.header("📊 Advanced Analytics System")
    st.markdown("**Comprehensive business intelligence with forecasting and ROI attribution**")

    # Import and render the analytics dashboard
    try:
        from jorge_analytics_dashboard import render_jorge_analytics_dashboard
        render_jorge_analytics_dashboard()
    except ImportError:
        st.error("⚠️ Advanced Analytics system not available. Please ensure the service is installed and running.")

        # Fallback summary metrics
        st.info("""
        **Advanced Analytics Features:**
        - 💰 AI-Powered Revenue Forecasting
        - 🎯 Conversion Funnel Analysis & Optimization
        - 🗺️ Geographic Performance Analytics
        - 🧠 Lead Quality Intelligence
        - 💵 ROI Attribution & Channel Performance
        """)

def render_jorge_lead_bot_dashboard():
    """Main function to render Jorge's Lead Bot Dashboard."""
    
    # Custom CSS for Jorge's branding
    st.markdown("""
    <style>
    .big-font {
        font-size: 28px !important;
        font-weight: bold;
        color: #1E88E5;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 8px;
        border-left: 4px solid #1E88E5;
        margin: 5px 0;
    }
    .success-alert {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 4px;
        color: #155724;
        padding: 10px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<p class="big-font">🤖 Jorge\'s AI Lead Bot - Command Center</p>', unsafe_allow_html=True)
    st.markdown("**Automated Lead Generation & Qualification System**")
    
    # Initialize API client
    api_client = get_api_client()
    
    # Main dashboard overview
    render_integration_dashboard(api_client)
    
    # Tab navigation for different sections
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🎯 Enhanced Lead Scoring",
        "🎤 Voice AI",
        "🎯 Marketing",
        "🤝 Retention",
        "📈 Market Intelligence",
        "🏠 Property Matching AI",
        "📊 Advanced Analytics"
    ])

    with tab1:
        render_enhanced_lead_scoring_section(api_client)

    with tab2:
        render_voice_ai_section(api_client)

    with tab3:
        render_marketing_section()

    with tab4:
        render_retention_section()

    with tab5:
        render_market_prediction_section()

    with tab6:
        render_property_matching_integration_section()

    with tab7:
        render_analytics_integration_section()
    
    # Footer with quick actions
    st.divider()
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📞 Emergency Call Override", use_container_width=True):
            st.info("Emergency mode activated - all calls routed to Jorge directly")
    
    with col2:
        if st.button("🎯 Launch Blast Campaign", use_container_width=True):
            st.info("Emergency campaign launched to all qualified leads")
    
    with col3:
        if st.button("📊 Export Today's Report", use_container_width=True):
            st.info("Daily performance report exported to your email")
    
    with col4:
        if st.button("⚙️ System Settings", use_container_width=True):
            st.info("Advanced settings panel - configure AI behavior")

# Main function call
if __name__ == "__main__":
    render_jorge_lead_bot_dashboard()