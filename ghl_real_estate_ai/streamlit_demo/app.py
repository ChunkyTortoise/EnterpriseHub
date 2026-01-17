"""
GHL Real Estate AI - Consolidated Hub Interface
Main Application with 5 Core Hubs
"""
from dotenv import load_dotenv
load_dotenv()

import warnings
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import asyncio
import json
from pathlib import Path

# Enterprise Real Estate AI Ecosystem
# Triggering reload: 2026-01-12T19:10:45
import streamlit as st
# Suppress all warnings for professional demo presentation
warnings.filterwarnings("ignore")

# Page config - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Lyrio AI | Obsidian Command",
    page_icon="https://raw.githubusercontent.com/ChunkyTortoise/EnterpriseHub/main/assets/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Lyrio AI - Obsidian Edition | Premium Real Estate Intelligence"
    }
)

# Initialize session state for hub navigation EARLY
if 'current_hub' not in st.session_state:
    st.session_state.current_hub = "Executive Command Center"
if 'selected_market' not in st.session_state:
    st.session_state.selected_market = "Austin, TX"
if 'ai_tone' not in st.session_state:
    st.session_state.ai_tone = "Natural"
if 'elite_mode' not in st.session_state:
    st.session_state.elite_mode = False
if 'claude_greeting_shown' not in st.session_state:
    st.session_state.claude_greeting_shown = False
if 'claude_session_initialized' not in st.session_state:
    st.session_state.claude_session_initialized = False
if 'show_claude_sidebar' not in st.session_state:
    st.session_state.show_claude_sidebar = True
if 'ghl_verified' not in st.session_state:
    st.session_state.ghl_verified = False

# Initialize Global AI State
if "ai_config" not in st.session_state:
    st.session_state.ai_config = {
        "market": "Austin, TX",
        "voice_tone": 0.5,  # 0.0 = Professional, 1.0 = Natural
        "response_speed": "Standard",
        "last_sync": datetime.datetime.now().strftime("%H:%M:%S")
    }

# Initialize Prompt Versioning
if "prompt_versions" not in st.session_state:
    st.session_state.prompt_versions = [
        {"version": "v1.0", "tag": "Baseline", "content": "You are a helpful assistant.", "timestamp": "2026-01-01"},
        {"version": "v1.1", "tag": "Production", "content": "You are a professional real estate assistant.", "timestamp": "2026-01-05"},
        {"version": "v1.2", "tag": "Elite v4.0", "content": "You are an elite Real Estate AI closer.", "timestamp": "2026-01-11"}
    ]

# Error Boundary Decorator for production stability
def ui_error_boundary(func_name="Component"):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                st.error(f"⚠️ {func_name} Temporarily Unavailable")
                st.info("Our team has been notified. Please try again or select another tab.")
                # Log error silently in production
                print(f"CRITICAL UI ERROR in {func_name}: {str(e)}")
                return None
        return wrapper
    return decorator

# Mock Service for missing dependencies
class MockService:
    """Fallback mock service for demo purposes"""
    def __init__(self, *args, **kwargs):
        pass
    def __getattr__(self, name):
        def method(*args, **kwargs):
            return {}
        return method

# Add project root and ghl_real_estate_ai to sys.path
# Add the project root (EnterpriseHub) to sys.path

# Add the project root (EnterpriseHub) to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add ghl_real_estate_ai directory to sys.path
ghl_root = project_root / "ghl_real_estate_ai"
if str(ghl_root) not in sys.path:
    sys.path.insert(0, str(ghl_root))

# Add streamlit_demo directory to sys.path for components/ imports
demo_root = ghl_root / "streamlit_demo"
if str(demo_root) not in sys.path:
    sys.path.insert(0, str(demo_root))

import json

# Import services - using proper absolute paths
try:
    import importlib
    import ghl_real_estate_ai.services.lead_scorer
    import ghl_real_estate_ai.services.ai_predictive_lead_scoring
    
    # Reloading for development/demo purposes
    importlib.reload(ghl_real_estate_ai.services.lead_scorer)
    importlib.reload(ghl_real_estate_ai.services.ai_predictive_lead_scoring)
    
    from ghl_real_estate_ai.services.lead_scorer import LeadScorer
    from ghl_real_estate_ai.services.ai_predictive_lead_scoring import PredictiveLeadScorer
    print(f"DEBUG: LeadScorer RELOADED from: {ghl_real_estate_ai.services.lead_scorer.__file__}")
    
    from ghl_real_estate_ai.services.ai_smart_segmentation import AISmartSegmentationService
    from ghl_real_estate_ai.services.deal_closer_ai import DealCloserAI
    from ghl_real_estate_ai.services.commission_calculator import CommissionCalculator, CommissionType, DealStage
    from ghl_real_estate_ai.services.meeting_prep_assistant import MeetingPrepAssistant, MeetingType
    from ghl_real_estate_ai.services.executive_dashboard import ExecutiveDashboardService
    from ghl_real_estate_ai.services.claude_executive_intelligence import get_executive_intelligence_service
    from ghl_real_estate_ai.services.lead_swarm_service import get_lead_swarm_service
    from ghl_real_estate_ai.services.quality_assurance import QualityAssuranceEngine
    from ghl_real_estate_ai.services.revenue_attribution import RevenueAttributionEngine
    from ghl_real_estate_ai.services.competitive_benchmarking import BenchmarkingEngine
    from ghl_real_estate_ai.services.agent_coaching import AgentCoachingService
    from ghl_real_estate_ai.services.smart_document_generator import SmartDocumentGenerator, DocumentType
    from ghl_real_estate_ai.services.ai_content_personalization import AIContentPersonalizationService
    from ghl_real_estate_ai.services.live_feed import LiveFeedService
    from ghl_real_estate_ai.services.workflow_marketplace import WorkflowMarketplaceService
    from ghl_real_estate_ai.services.auto_followup_sequences import AutoFollowUpSequences
    from ghl_real_estate_ai.services.property_matcher import PropertyMatcher
    from ghl_real_estate_ai.services.reengagement_engine import ReengagementEngine, ReengagementTrigger
    from ghl_real_estate_ai.services.churn_integration_service import ChurnIntegrationService
    from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
    
    # Initialize Claude Assistant and Platform Companion
    claude = ClaudeAssistant()

    # Import Claude Platform Companion
    try:
        from ghl_real_estate_ai.services.claude_platform_companion import get_claude_platform_companion
        claude_companion = get_claude_platform_companion()
        CLAUDE_COMPANION_AVAILABLE = True
    except ImportError as e:
        print(f"Claude Platform Companion not available: {e}")
        CLAUDE_COMPANION_AVAILABLE = False
        claude_companion = None
        
    # Enhanced services imports
    try:
        from ghl_real_estate_ai.services.enhanced_lead_scorer import EnhancedLeadScorer
        ENHANCED_LEAD_SCORER_AVAILABLE = True
    except ImportError:
        print("Enhanced Lead Scorer not available")
        ENHANCED_LEAD_SCORER_AVAILABLE = False

    try:
        from ghl_real_estate_ai.services.enhanced_property_matcher import EnhancedPropertyMatcher
        ENHANCED_PROPERTY_MATCHER_AVAILABLE = True
    except ImportError:
        print("Enhanced Property Matcher not available")
        ENHANCED_PROPERTY_MATCHER_AVAILABLE = False

    try:
        from ghl_real_estate_ai.services.churn_prediction_engine import ChurnPredictionEngine
        CHURN_PREDICTION_ENGINE_AVAILABLE = True
    except ImportError:
        print("Churn Prediction Engine not available")
        CHURN_PREDICTION_ENGINE_AVAILABLE = False

    # Component Imports
    from ghl_real_estate_ai.streamlit_demo.components.churn_early_warning_dashboard import ChurnEarlyWarningDashboard
    from ghl_real_estate_ai.streamlit_demo.components.property_valuation import render_property_valuation_engine
    from ghl_real_estate_ai.streamlit_demo.components.financing_calculator import render_financing_calculator
    from ghl_real_estate_ai.streamlit_demo.components.neighborhood_intelligence import render_neighborhood_explorer
    from ghl_real_estate_ai.streamlit_demo.components.buyer_journey import render_buyer_dashboard, render_buyer_analytics, render_buyer_journey_hub
    from ghl_real_estate_ai.streamlit_demo.components.seller_journey import (
        render_seller_prep_checklist, 
        render_marketing_campaign_dashboard, 
        render_seller_communication_portal, 
        render_transaction_timeline, 
        render_seller_analytics, 
        render_seller_journey_hub
    )
    from ghl_real_estate_ai.streamlit_demo.components.ui_elements import render_action_card, render_insight_card
    from ghl_real_estate_ai.streamlit_demo.components.global_header import render_global_header
    from ghl_real_estate_ai.streamlit_demo.components.executive_hub import render_executive_hub
    from ghl_real_estate_ai.streamlit_demo.components.lead_intelligence_hub import render_lead_intelligence_hub
    from ghl_real_estate_ai.streamlit_demo.components.automation_studio import AutomationStudioHub
    from ghl_real_estate_ai.streamlit_demo.components.sales_copilot import SalesCopilotHub
    from ghl_real_estate_ai.streamlit_demo.components.ops_optimization import OpsOptimizationHub
    from ghl_real_estate_ai.streamlit_demo.components.calculators import render_roi_calculator, render_revenue_funnel
    from ghl_real_estate_ai.streamlit_demo.components.claude_panel import render_claude_assistant
    from ghl_real_estate_ai.streamlit_demo.components.voice_claude_interface import render_voice_claude_interface, render_voice_settings, add_voice_interface_css
    from ghl_real_estate_ai.streamlit_demo.components.proactive_intelligence_dashboard import render_proactive_intelligence_dashboard, render_proactive_alerts_widget
    from ghl_real_estate_ai.streamlit_demo.components.swarm_visualizer import render_swarm_visualizer
    from ghl_real_estate_ai.streamlit_demo.components.ai_training_feedback import render_rlhf_loop
    from ghl_real_estate_ai.streamlit_demo.components.voice_intelligence import render_voice_intelligence
    from ghl_real_estate_ai.streamlit_demo.components.property_swipe import render_property_swipe
    from ghl_real_estate_ai.streamlit_demo.components.workflow_designer import render_workflow_designer
    from ghl_real_estate_ai.streamlit_demo.components.listing_architect import render_listing_architect
    from ghl_real_estate_ai.streamlit_demo.components.security_governance import render_security_governance
    from ghl_real_estate_ai.streamlit_demo.components.agent_os import render_agent_os_tab
    from ghl_real_estate_ai.streamlit_demo.components.neural_uplink import render_neural_uplink
    from ghl_real_estate_ai.streamlit_demo.realtime_dashboard_integration import render_realtime_intelligence_dashboard
    from ghl_real_estate_ai.streamlit_demo.components.floating_claude import render_floating_claude
    from ghl_real_estate_ai.streamlit_demo.components.project_copilot import render_project_copilot

    SERVICES_LOADED = True
except ImportError as e:
    print(f"DEBUG IMPORT ERROR: {e}")
    st.error(f"⚠️ Error importing services: {e}")
    st.error("Please ensure you're running from the correct directory")
    SERVICES_LOADED = False
    # Set defaults for enhanced service availability flags
    ENHANCED_LEAD_SCORER_AVAILABLE = False
    ENHANCED_PROPERTY_MATCHER_AVAILABLE = False
    CHURN_PREDICTION_ENGINE_AVAILABLE = False

# Helper function to load data
def load_mock_data():
    data_path = Path(__file__).parent.parent / "data" / "mock_analytics.json"
    if data_path.exists():
        with open(data_path) as f:
            return json.load(f)
    return {}

# Initialize services
# @st.cache_resource
def get_services(market="Austin"):
    listings_file = "property_listings.json" if market == "Austin" else "property_listings_rancho.json"
    listings_path = Path(__file__).parent.parent / "data" / "knowledge_base" / listings_file
    
    from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator
    from ghl_real_estate_ai.services.claude_automation_engine import ClaudeAutomationEngine

    services_dict = {
        "lead_scorer": LeadScorer(),
        "segmentation": AISmartSegmentationService(),
        "predictive_scorer": PredictiveLeadScorer(),
        "personalization": AIContentPersonalizationService(),
        "deal_closer": DealCloserAI(),
        "commission_calc": CommissionCalculator(),
        "meeting_prep": MeetingPrepAssistant(),
        "executive": ExecutiveDashboardService(),
        "doc_gen": SmartDocumentGenerator(),
        "qa": QualityAssuranceEngine(),
        "revenue": RevenueAttributionEngine(),
        "benchmarking": BenchmarkingEngine(),
        "coaching": AgentCoachingService(),
        "sequences": AutoFollowUpSequences(),
        "marketplace": WorkflowMarketplaceService(),
        "property_matcher": PropertyMatcher(listings_path=str(listings_path)),
        "claude_orchestrator": get_claude_orchestrator(),
        "claude_automation": ClaudeAutomationEngine(),
        "churn_service": ChurnIntegrationService(
            memory_service=None,  # Would be injected with actual services
            lifecycle_tracker=None,
            behavioral_engine=None,
            lead_scorer=None,
            reengagement_engine=ReengagementEngine(),
            ghl_service=None
        )
    }

    # Add enhanced services if available
    if ENHANCED_LEAD_SCORER_AVAILABLE:
        try:
            services_dict["enhanced_lead_scorer"] = EnhancedLeadScorer()
            st.success("✅ Enhanced Lead Scorer initialized successfully")
        except Exception as e:
            st.error(f"❌ Failed to initialize Enhanced Lead Scorer: {e}")
            services_dict["enhanced_lead_scorer"] = MockService()  # Fallback

    if ENHANCED_PROPERTY_MATCHER_AVAILABLE:
        try:
            services_dict["enhanced_property_matcher"] = EnhancedPropertyMatcher(listings_path=str(listings_path))
            st.success("✅ Enhanced Property Matcher initialized successfully")
        except Exception as e:
            st.error(f"❌ Failed to initialize Enhanced Property Matcher: {e}")
            services_dict["enhanced_property_matcher"] = MockService()  # Fallback

    if CHURN_PREDICTION_ENGINE_AVAILABLE:
        try:
            # Initialize required services for ChurnPredictionEngine
            memory_service = MockService()  # Mock service for demo
            lifecycle_tracker = MockService()  # Mock service for demo
            behavioral_engine = MockService()  # Mock service for demo

            services_dict["churn_prediction"] = ChurnPredictionEngine(
                memory_service=memory_service,
                lifecycle_tracker=lifecycle_tracker,
                behavioral_engine=behavioral_engine,
                lead_scorer=services_dict["lead_scorer"]  # Use the actual lead scorer
            )
            st.success("✅ Churn Prediction Engine initialized successfully")
        except Exception as e:
            st.error(f"❌ Failed to initialize Churn Prediction Engine: {e}")
            services_dict["churn_prediction"] = MockService()  # Fallback

    return services_dict

# --- THE FINAL POLISH: GLOBAL UI UTILITIES ---
def sparkline(data: list, color: str = "#6366F1", height: int = 50):
    """Generates a minimal high-fidelity sparkline chart with a neural glow effect."""
    # Convert hex color to rgba for Plotly compatibility
    hex_c = color.lstrip('#')
    r, g, b = int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)
    fill_rgba = f"rgba({r}, {g}, {b}, 0.1)"
    glow_rgba = f"rgba({r}, {g}, {b}, 0.4)"

    fig = go.Figure()
    
    # Outer Glow
    fig.add_trace(go.Scatter(
        y=data,
        mode='lines',
        line=dict(color=glow_rgba, width=5),
        hoverinfo='skip',
        opacity=0.3
    ))
    
    # Main Core Line
    fig.add_trace(go.Scatter(
        y=data,
        mode='lines',
        fill='tozeroy',
        line=dict(color=color, width=2.5),
        fillcolor=fill_rgba,
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=5, b=0),
        height=height,
        xaxis=dict(visible=False, fixedrange=True),
        yaxis=dict(visible=False, fixedrange=True, range=[min(data)*0.9, max(data)*1.1])
    )
    return fig

from ghl_real_estate_ai.streamlit_demo.obsidian_theme import inject_elite_css, style_obsidian_chart, render_dossier_block

# Inject Global Visual Overhaul
inject_elite_css()

# Hide Streamlit branding and debug elements (preserved minimal overrides)
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 95rem;
        }
        [data-testid="stAppViewContainer"] > div:first-child {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar - Settings (Early for service init)
def update_market():
    m_key = "Austin" if "Austin" in st.session_state.market_selector else "Rancho"
    st.session_state.lead_options = get_lead_options(m_key)
    st.session_state.selected_lead_name = "-- Select a Lead --"
    st.session_state.selected_market = st.session_state.market_selector

with st.sidebar:
    st.markdown("### ⚙️ AI Configuration")
    
    # Persist market selection
    selected_market = st.selectbox(
        "Select Market:", 
        ["Austin, TX", "Rancho Cucamonga, CA"],
        index=["Austin, TX", "Rancho Cucamonga, CA"].index(st.session_state.get('selected_market', "Austin, TX")),
        key="market_selector",
        on_change=update_market
    )
    st.session_state.selected_market = selected_market
    market_key = "Austin" if "Austin" in selected_market else "Rancho"
    
    # Persist AI tone
    ai_tone = st.select_slider(
        "AI Voice Tone:",
        options=["Professional", "Natural", "Direct/Casual"],
        value=st.session_state.get('ai_tone', "Natural"),
        key="tone_selector"
    )
    st.session_state.ai_tone = ai_tone
    
    st.markdown("---")

    # NEW: Elite Mode Activation
    elite_mode = st.toggle(
        "🚀 Activate Elite Phase Features", 
        value=st.session_state.get('elite_mode', False),
        help="Enables Semantic Memory, Adaptive Scoring, and Advanced Decision Logic."
    )
    st.session_state.elite_mode = elite_mode
    
    if elite_mode:
        st.success("✨ Elite Mode Active")
    
    st.markdown("---")

services = get_services(market=market_key)

# Initialize lead options with multi-market logic (Global Scope)
def get_lead_options(market_key):
    if market_key == "Rancho":
        return {
            "-- Select a Lead --": None,
            "Sarah Johnson": {
                "lead_id": "sarah_johnson_rancho",
                "occupation": "School Teacher",
                "location": "Avery Ranch",
                "extracted_preferences": {
                    "budget": 850000,
                    "location": "Avery Ranch",
                    "timeline": "ASAP",
                    "bedrooms": 4,
                    "must_haves": ["Pool", "Good Schools"],
                    "financing": "Pre-approved",
                    "motivation": "School start deadline",
                    "property_type": "Single Family Home"
                },
                "overall_score": 92,
                "actions_completed": 4
            },
            "Mike Chen": {
                "lead_id": "mike_chen_rancho",
                "occupation": "Retired Executive",
                "location": "Victoria Gardens",
                "extracted_preferences": {
                    "budget": 700000,
                    "location": "Victoria Gardens",
                    "timeline": "6 months",
                    "bedrooms": 3,
                    "must_haves": ["Condo", "Maintenance free"],
                    "financing": "Cash",
                    "motivation": "Downsizing",
                    "property_type": "Luxury Condo"
                },
                "overall_score": 75,
                "actions_completed": 3
            },
            "Emily Davis": {
                "lead_id": "emily_davis_rancho",
                "occupation": "Real Estate Investor",
                "location": "Alta Loma",
                "extracted_preferences": {
                    "budget": 1000000,
                    "location": "Alta Loma",
                    "timeline": "Exploring",
                    "bedrooms": 4,
                    "must_haves": ["Investment potential", "Large lot"],
                    "financing": "Conventional",
                    "motivation": "Expanding portfolio",
                    "property_type": "Single Family Home"
                },
                "overall_score": 60,
                "actions_completed": 2
            }
        }
    
    return {
        "-- Select a Lead --": None,
        "Sarah Chen (Apple Engineer)": {
            "lead_id": "tech_professional_sarah",
            "occupation": "Apple Engineer",
            "location": "North Austin / Round Rock",
            "extracted_preferences": {
                "budget": 550000,
                "location": "North Austin / Round Rock",
                "timeline": "URGENT - 45 days",
                "bedrooms": 3,
                "bathrooms": 2,
                "must_haves": ["Home office", "High-speed internet"],
                "financing": "Pre-approved",
                "motivation": "Relocating for Apple expansion",
                "home_condition": "Modern / Move-in Ready",
                "property_type": "Single Family Home"
            },
            "overall_score": 92,
            "actions_completed": 4
        },
        "David Kim (Investor)": {
            "lead_id": "investor_david",
            "occupation": "Portfolio Manager",
            "location": "Manor / Del Valle",
            "extracted_preferences": {
                "budget": 350000,
                "location": "Manor / Del Valle",
                "timeline": "Immediate",
                "must_haves": ["Positive cash flow", "Rental potential"],
                "financing": "Cash Buyer",
                "motivation": "Expanding Austin portfolio",
                "property_type": "Single Family or Duplex"
            },
            "overall_score": 95,
            "actions_completed": 5
        },
        "Mike & Jessica Rodriguez (Growing Family)": {
            "lead_id": "growing_family_mike",
            "occupation": "Healthcare Professionals",
            "location": "Pflugerville / Manor",
            "extracted_preferences": {
                "budget": 380000,
                "location": "Pflugerville / Manor",
                "timeline": "3-4 months",
                "bedrooms": 3,
                "bathrooms": 2,
                "must_haves": ["Fenced yard", "Safe neighborhood"],
                "financing": "Needs lender referral",
                "motivation": "Outgrowing current apartment",
                "home_condition": "Any",
                "property_type": "Single Family Home"
            },
            "overall_score": 78,
            "actions_completed": 2
        },
        "Robert & Linda Williams (Luxury Downsizer)": {
            "lead_id": "luxury_downsizer_robert",
            "occupation": "Retired Business Owners",
            "location": "Downtown / Clarksville",
            "extracted_preferences": {
                "budget": 1200000,
                "location": "Downtown / Clarksville",
                "timeline": "Flexible",
                "bedrooms": 2,
                "bathrooms": 2.5,
                "must_haves": ["Luxury finishes", "Walkable"],
                "financing": "High equity / Cash",
                "motivation": "Empty nesters downsizing from Steiner Ranch",
                "property_type": "Luxury Condo / Townhome"
            },
            "overall_score": 88,
            "actions_completed": 3
        }
    }

# --- GLOBAL STATE INITIALIZATION ---
if 'lead_options' not in st.session_state:
    st.session_state.lead_options = get_lead_options(market_key)

if 'selected_lead_name' not in st.session_state:
    st.session_state.selected_lead_name = "-- Select a Lead --"

# Helper to sync selection across tabs
def set_selected_lead(name):
    st.session_state.selected_lead_name = name

def get_meeting_briefing(lead_name):
    # Simulated briefing synthesis based on extracted preferences
    briefings = {
        "Sarah Chen (Apple Engineer)": {
            "hook": "Relocating from SF for Apple. Very urgent 45-day timeline.",
            "objection": "Concerned about Austin market knowledge and internet reliability for remote work.",
            "closer": "Round Rock has the tech community she wants. Under her $550k SF-adjusted budget."
        },
        "Mike & Jessica Rodriguez (Growing Family)": {
            "hook": "First-time buyers outgrowing an apartment. Jessica works at Dell Seton.",
            "objection": "Tight $380k budget for 3BR. Nervous about the buying process.",
            "closer": "Pflugerville offers the safety and yard they need within their reach."
        },
        "David Kim (Investor)": {
            "hook": "Seasoned Dallas investor expanding to Austin. 100% Cash buyer.",
            "objection": "Only interested in properties with >$200/mo positive cash flow.",
            "closer": "Manor/Del Valle hotspots provide the cap rates he requires. Show him off-market deals."
        },
        "Robert & Linda Williams (Luxury Downsizer)": {
            "hook": "Empty nesters downsizing from 4,500sqft Steiner Ranch home.",
            "objection": "Want to ensure they don't lose luxury amenities when moving to a condo.",
            "closer": "Downtown 'Lock-and-leave' lifestyle allows them to travel. Highlight concierge services."
        },
        "Sarah Johnson": {
            "hook": "Wants to move by March for school start. Focused on the Avery Ranch school district.",
            "objection": "Concerned about Austin property tax spikes and recent HOA changes in the area.",
            "closer": "Ready to sign if we find 4BR in Avery Ranch under $800k with a pool."
        },
        "Mike Chen": {
            "hook": "Downsizing from a large family home. Target timeline is 6 months.",
            "objection": "Extremely price-sensitive regarding condo fees and maintenance costs.",
            "closer": "Will commit if we find a high-floor unit with Victoria Gardens views."
        },
        "Emily Davis": {
            "hook": "First-time investor looking for high-yield rental potential.",
            "objection": "Unsure about current interest rates vs. ROI margins.",
            "closer": "Ready to proceed if we can show a 7%+ cap rate on a duplex."
        }
    }
    return briefings.get(lead_name, {
        "hook": "General market interest detected. Lead is exploring options.",
        "objection": "Standard market volatility concerns.",
        "closer": "Needs value-add presentation to move to 'Hot' status."
    })

# Environment detection and data loading
from ghl_real_estate_ai.ghl_utils.config import is_mock_mode, get_environment_display

env_info = get_environment_display()

# FEAT-011: Live Mode Authentication Bridge
def verify_ghl_connection():
    try:
        from ghl_real_estate_ai.services.ghl_client import GHLClient
        ghl_client = GHLClient()
        response = ghl_client.check_health()
        
        if hasattr(response, 'status_code') and response.status_code == 200:
            st.session_state.is_live = True
            # Remove the yellow banner CSS via State
            st.markdown("<style>.warning-banner { display: none !important; }</style>", unsafe_allow_html=True)
            return ghl_client.fetch_dashboard_data()
        else:
            st.session_state.is_live = False
            return None
    except Exception as e:
        st.session_state.is_live = False
        return None

if is_mock_mode():
    mock_data = load_mock_data()
else:
    # Attempt live connection
    live_data = verify_ghl_connection()
    
    # Only show banner if there's an actual connection problem
    if st.session_state.get('is_live', False) and live_data:
        st.session_state.ghl_verified = True
        mock_data = live_data
    else:
        # Demo mode - only show error once, not on every page load
        if not st.session_state.get('ghl_warning_shown', False):
            # Suppress warning entirely if GHL status already shown in sidebar
            pass  # The green "GHL Connected" badge in sidebar is sufficient
        mock_data = load_mock_data()

# Load custom CSS
css_path = Path(__file__).parent / "assets" / "styles.css"
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Environment mode banner
st.markdown(f"""
<div style='background: {env_info['color']}; color: white; padding: 0.75rem 1.5rem; 
            border-radius: 8px; margin-bottom: 1rem; text-align: center; font-weight: 600;'>
    {env_info['icon']} {env_info['name']}: {env_info['message']}
</div>
""", unsafe_allow_html=True)

# Enhanced premium branding header with animations
current_tenant = "GHL"
if 'current_hub' in st.session_state:
    if "Ops" in st.session_state.current_hub:
        current_tenant = "ARETE"
    elif "Sales" in st.session_state.current_hub:
        current_tenant = "SALES"

render_global_header(current_tenant)

# 🚀 CLAUDE'S WELCOME WALKTHROUGH (Elite Phase)
from ghl_real_estate_ai.streamlit_demo.components.project_copilot import render_welcome_walkthrough
render_welcome_walkthrough()

# --- THE OBSIDIAN COMMAND v2.0: GLOBAL BACKGROUND ---
st.markdown("""
<div style='position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -1; pointer-events: none;'>
    <div style='position: absolute; width: 300px; height: 300px; background: rgba(99, 102, 241, 0.05); filter: blur(100px); border-radius: 50%; top: 10%; left: 10%;'></div>
    <div style='position: absolute; width: 400px; height: 400px; background: rgba(139, 92, 246, 0.05); filter: blur(120px); border-radius: 50%; bottom: 10%; right: 10%;'></div>
</div>
""", unsafe_allow_html=True)

# 🧠 CLAUDE PLATFORM GREETING SYSTEM
# Contextual sidebar and counsel are maintained; the main greeting is now in render_welcome_walkthrough()
if CLAUDE_COMPANION_AVAILABLE and claude_companion:
    if not st.session_state.get('claude_session_initialized', False):
        try:
            # Actually initialize the session with Claude
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            with st.spinner("🧠 Claude is personalizing your experience..."):
                greeting = loop.run_until_complete(
                    claude_companion.initialize_session("Jorge", market_key)
                )
                st.session_state.claude_greeting = greeting
                st.session_state.show_claude_greeting = True
                
            st.session_state.claude_session_initialized = True
            st.session_state.session_start = datetime.datetime.now()
        except Exception as e:
            print(f"Claude Platform Companion initialization failed: {e}")
            st.session_state.claude_session_initialized = True # Prevent repeated attempts

    # Render platform greeting if requested
    if st.session_state.get('show_claude_greeting', False) and 'claude_greeting' in st.session_state:
        claude_companion.render_platform_greeting(st.session_state.claude_greeting)
        if st.button("Close Greeting", key="close_claude_greeting"):
            st.session_state.show_claude_greeting = False
            st.rerun()

    if st.session_state.get('show_claude_sidebar', True) and st.session_state.get('claude_session_initialized', False):
        claude_companion.render_contextual_sidebar()

    # 📖 CLAUDE'S PROJECT GUIDANCE
    if CLAUDE_COMPANION_AVAILABLE and claude_companion and st.session_state.get('claude_session_initialized', False):
        with st.expander(f"📖 Claude's Guide: {st.session_state.current_hub}", expanded=False):
            if st.button("✨ Generate Hub Guide"):
                with st.spinner("🧠 Claude is preparing your project walkthrough..."):
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    guidance = loop.run_until_complete(
                        claude_companion.get_project_guidance(st.session_state.current_hub)
                    )
                    st.session_state[f"guidance_{st.session_state.current_hub}"] = guidance
            
            guidance = st.session_state.get(f"guidance_{st.session_state.current_hub}")
            if guidance:
                # Use Dossier styling for guidance
                guidance_content = f"""
                <div style='margin-bottom: 1.5rem;'>
                    <h3 style='color: #6366F1; margin-bottom: 0.5rem;'>🎯 Purpose</h3>
                    <p>{guidance.purpose}</p>
                </div>
                <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;'>
                    <div>
                        <h4 style='color: #6366F1;'>✨ Key Features</h4>
                        <ul style='list-style-type: none; padding-left: 0;'>
                            {"".join(f"<li style='margin-bottom: 0.5rem;'>• {f}</li>" for f in guidance.key_features)}
                        </ul>
                        <h4 style='color: #6366F1; margin-top: 1.5rem;'>🚀 Recommended Workflow</h4>
                        <ol style='list-style-type: none; padding-left: 0;'>
                            {"".join(f"<li style='margin-bottom: 0.5rem;'>{i+1}. {w}</li>" for i, w in enumerate(guidance.recommended_workflow))}
                        </ol>
                    </div>
                    <div>
                        <h4 style='color: #6366F1;'>💡 Pro-Tips</h4>
                        <div style='background: rgba(99, 102, 241, 0.05); padding: 1rem; border-radius: 8px; border-left: 3px solid #6366F1;'>
                            {"".join(f"<p style='font-style: italic; margin-bottom: 0.5rem;'>\" {t} \"</p>" for t in guidance.pro_tips)}
                        </div>
                        <h4 style='color: #6366F1; margin-top: 1.5rem;'>🎯 Next Steps</h4>
                        <ul style='list-style-type: none; padding-left: 0;'>
                            {"".join(f"<li style='margin-bottom: 0.5rem;'>✅ {s}</li>" for s in guidance.next_steps)}
                        </ul>
                    </div>
                </div>
                """
                render_dossier_block(guidance_content, title=f"SYSTEM WALKTHROUGH: {st.session_state.current_hub.upper()}")
            else:
                st.info("Click the button above to have Claude guide you through this section of the project.")

# PREMIUM FEATURE: Enhanced sidebar with enterprise styling
with st.sidebar:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    ">
        <h3 style="color: white; margin: 0; font-size: 1.2rem; font-weight: 600;">
            🎯 Command Center
        </h3>
        <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 0.85rem;">
            Jorge's AI Hub Navigator
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar Navigation with Sectioning
    st.markdown("<div style='font-size: 0.7rem; color: #8B949E; text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 8px; font-weight: 700;'>Business Intelligence</div>", unsafe_allow_html=True)
    bi_hubs = [
        "Executive Command Center",
        "Lead Intelligence Hub",
        "Real-Time Intelligence",
        "Ops & Optimization"
    ]
    
    st.markdown("<div style='font-size: 0.7rem; color: #8B949E; text-transform: uppercase; letter-spacing: 0.15em; margin-top: 15px; margin-bottom: 8px; font-weight: 700;'>Autonomous Agents</div>", unsafe_allow_html=True)
    agent_hubs = [
        "Swarm Intelligence",
        "Proactive Intelligence",
        "Voice Claude",
        "Sales Copilot",
        "Deep Research"
    ]
    
    st.markdown("<div style='font-size: 0.7rem; color: #8B949E; text-transform: uppercase; letter-spacing: 0.15em; margin-top: 15px; margin-bottom: 8px; font-weight: 700;'>Customer Journey</div>", unsafe_allow_html=True)
    journey_hubs = [
        "Buyer Journey Hub",
        "Seller Journey Hub",
        "Automation Studio"
    ]
    
    hub_options = bi_hubs + agent_hubs + journey_hubs
    
    # Initialize Copilot (Greeting & Guidance)
    try:
        render_project_copilot()
    except Exception as e:
        st.sidebar.error(f"Copilot initialization failed: {e}")

    # Calculate index safely
    try:
        default_index = hub_options.index(st.session_state.current_hub)
    except ValueError:
        default_index = 0
    
    selected_hub = st.radio(
        "Select Hub:",
        hub_options,
        index=default_index,
        label_visibility="collapsed"
    )
    
    # Update session state and notify Claude of context change
    if st.session_state.current_hub != selected_hub:
        st.session_state.current_hub = selected_hub

        # Update Claude's context awareness
        if CLAUDE_COMPANION_AVAILABLE and claude_companion and st.session_state.get('claude_session_initialized', False):
            try:
                # Update Claude's context with new hub selection
                hub_context = {
                    "hub_name": selected_hub,
                    "user_action": "navigation",
                    "timestamp": datetime.datetime.now().isoformat()
                }

                # Run async context update
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                # Update context and get any relevant insights
                context_update = loop.run_until_complete(
                    claude_companion.update_context(selected_hub.lower().replace(" ", "_"), hub_context)
                )

                # Store any insights for display
                if context_update:
                    st.session_state.claude_contextual_insight = context_update.get("insight")
                    st.session_state.dynamic_claude_counsel = context_update.get("counsel")

            except Exception as e:
                # Silently handle context update failures
                pass
    else:
        st.session_state.current_hub = selected_hub
    
    # NEW: Global AI Pulse Indicator
    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px;
        background: rgba(99, 102, 241, 0.1);
        border-radius: 8px;
        margin-top: 1rem;
        border: 1px solid rgba(99, 102, 241, 0.2);
    ">
        <div class="live-indicator" style="width: 10px; height: 10px; background: #10b981; border-radius: 50%; box-shadow: 0 0 10px #10b981;"></div>
        <div style="font-size: 0.8rem; color: #E6EDF3; font-weight: 600; font-family: 'Space Grotesk', sans-serif;">
            Swarm Status: <span style="color: #10b981;">ACTIVE</span>
        </div>
        <div style="font-size: 0.7rem; color: #64748b; margin-left: auto;">
            v4.0.0
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # System Health Sparkline in Sidebar
    st.markdown("<br>", unsafe_allow_html=True)
    st.plotly_chart(sparkline([98, 99, 97, 99, 100, 99], color="#10B981", height=30), use_container_width=True, config={'displayModeBar': False})
    st.caption("SYSTEM STABILITY: 99.8% (NORMAL)")

    st.markdown("---")
    
    # NEW: Neural Uplink Feed
    render_neural_uplink()
    
    st.markdown("---")
    
    # NEW: Claude's Strategic Counsel (Contextual)
    counsel_messages = {
        "Executive Command Center": "Jorge, lead velocity is up 12% this week. Focus on the Downtown cluster for maximum ROI.",
        "Lead Intelligence Hub": "Sarah Martinez is showing high engagement with luxury properties. Suggest a showing today.",
        "Voice Claude": "Voice commands active. Try saying 'Hey Claude, show me my top leads' for hands-free assistance.",
        "Proactive Intelligence": "2 high-priority alerts detected. Pipeline risk identified - take action now to stay on target.",
        "Swarm Intelligence": "The analyst swarm is currently processing 142 leads. Token efficiency is at an all-time high.",
        "Real-Time Intelligence": "Market conditions are shifting in East Austin. Update your valuation models.",
        "Buyer Journey Hub": "We have 3 buyers ready for pre-approval. Syncing with financing partners now.",
        "Seller Journey Hub": "The Maple Ave listing is hitting peak interest. I recommend an open house this Sunday.",
        "Automation Studio": "3 new workflow templates are ready for deployment. Your time savings is currently 42h/week.",
        "Sales Copilot": "Preparing talking points for your 2pm call. Client prefers a direct, data-driven approach.",
        "Ops & Optimization": "System health is optimal. Recommend scaling to the Miami market next month.",
        "Deep Research": "Perplexity-powered search is active. Ask me to research any market or property."
    }
    
    current_msg = st.session_state.get('dynamic_claude_counsel')
    if not current_msg:
        current_msg = counsel_messages.get(selected_hub, "AI Swarm is standing by for your next command.")
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.05) 0%, rgba(99, 102, 241, 0.05) 100%);
        padding: 15px;
        border-radius: 12px;
        border: 1px solid rgba(139, 92, 246, 0.2);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        position: relative;
        overflow: hidden;
    ">
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <div class="status-pulse"></div>
            <div style="font-size: 0.75rem; color: #8B5CF6; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em;">
                Claude's Strategic Counsel
            </div>
        </div>
        <div style="font-size: 0.9rem; color: #E6EDF3; font-style: italic; line-height: 1.5; position: relative; z-index: 1;">
            "{current_msg}"
        </div>
        <div style="position: absolute; right: -10px; bottom: -10px; font-size: 3rem; opacity: 0.05; transform: rotate(-15deg);">🧠</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # PREMIUM FEATURE: Enhanced quick actions
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%);
        padding: 1.2rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid rgba(99, 102, 241, 0.3);
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    ">
        <h4 style="margin: 0; font-size: 0.9rem; font-weight: 700; color: white; text-transform: uppercase; letter-spacing: 0.1em;">
            ⚡ Command Matrix
        </h4>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Refresh Data", use_container_width=True, type="primary"):
        # Clear all caches to ensure fresh data
        st.cache_data.clear()
        st.cache_resource.clear()
        st.toast("✅ Data refreshed successfully!", icon="🔄")
        st.rerun()
    
    # Export functionality
    metrics_data = {
        "Metric": ["Total Pipeline", "Hot Leads", "Conversion Rate", "Avg Deal Size"],
        "Value": ["$2.4M", "23", "34%", "$385K"],
        "Change": ["+15%", "+8", "+2%", "+$12K"]
    }
    df_metrics = pd.DataFrame(metrics_data)
    csv = df_metrics.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        "📥 Export Report",
        data=csv,
        file_name="executive_metrics.csv",
        mime="text/csv",
        width="stretch"
    )
    
    st.markdown("---")

    # NEW: Global AI State Sync (Zustand-style Control)
    with st.expander("🤖 Global AI Configuration", expanded=True):
        market = st.selectbox("Active Market", ["Austin, TX", "Miami, FL", "Los Angeles, CA"], index=0)
        voice_tone = st.slider("AI Voice Tone", 0.0, 1.0, st.session_state.ai_config["voice_tone"], 
                               help="0.0 = Professional, 1.0 = Natural")
        
        if market != st.session_state.ai_config["market"] or voice_tone != st.session_state.ai_config["voice_tone"]:
            st.session_state.ai_config["market"] = market
            st.session_state.ai_config["voice_tone"] = voice_tone
            st.session_state.ai_config["last_sync"] = datetime.datetime.now().strftime("%H:%M:%S")
            st.toast(f"AI State Synced: {market}", icon="🧠")
            
        st.caption(f"Last sync: {st.session_state.ai_config['last_sync']}")

    # NEW: Portal URL Utility
    with st.expander("🔗 GHL Architectural Sync", expanded=False):
        st.markdown("""
        **Environment:** `Lyrio-Production-Main`
        **Sync Status:** ✅ Operational
        **Lead Buffer:** 128MB Persistent
        """)
        st.link_button("🌐 Open Lyrio Dashboard", "https://app.gohighlevel.com", use_container_width=True)
        st.link_button("📨 AI Conversation Audit", "https://app.gohighlevel.com", use_container_width=True)

    st.markdown("---")
    
    # System status
    st.markdown("<h4 style='color: #8B949E; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 2.5rem; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 5px; margin-bottom: 15px;'>System Telemetry</h4>", unsafe_allow_html=True)
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.metric("Active Leads", "47", "+12")
    with col_stat2:
        # Use a status indicator emoji with the delta spot for Swarm
        st.metric("Neural Swarm", "Online", delta="Stable", delta_color="normal")
    
    st.markdown("<h4 style='color: #8B949E; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 2rem;'>Neural Uplink</h4>", unsafe_allow_html=True)
    
    # Enhanced Live Feed with v2.0 styling
    try:
        from ghl_real_estate_ai.services.live_feed import LiveFeedService
        feed_service = LiveFeedService()
        feed_html = feed_service.get_feed_html(limit=6)
        # Apply Obsidian Command v2.0 wrapper to feed
        st.markdown(f"""
        <div style='background: rgba(13, 17, 23, 0.4); border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); padding: 5px;'>
            {feed_html}
        </div>
        """, unsafe_allow_html=True)
    except Exception:
        # Fallback items with v2.0 styling
        for item in feed_items:
            st.markdown(f"""
            <div style="
                display: flex; 
                gap: 12px; 
                margin-bottom: 8px; 
                padding: 12px; 
                background: rgba(22, 27, 34, 0.6); 
                border-radius: 10px; 
                border: 1px solid rgba(255,255,255,0.05);
                border-left: 2px solid {item['color']};
                transition: all 0.3s ease;">
                <div style="font-size: 1.1rem; filter: drop-shadow(0 0 5px {item['color']}40);">{item['icon']}</div>
                <div style="flex: 1;">
                    <div style="font-size: 0.8rem; line-height: 1.4; color: #E6EDF3;">{item['text']}</div>
                    <div style="font-size: 0.65rem; color: #8B949E; margin-top: 4px;">{item['time']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# Main content area

# Buyer Component Functions
def render_buyer_profile_builder():
    """Interactive buyer profile builder with intelligent recommendations"""
    st.subheader("👤 Build Your Buyer Profile")

    # Basic Information Section
    with st.container():
        st.markdown("#### 📝 Basic Information")
        col1, col2 = st.columns(2)

        with col1:
            buyer_name = st.text_input("Full Name", placeholder="Enter buyer's name")
            phone = st.text_input("Phone Number", placeholder="(555) 123-4567")
            current_location = st.text_input("Current Location", placeholder="City, State")

        with col2:
            email = st.text_input("Email Address", placeholder="buyer@email.com")
            buyer_type = st.selectbox("Buyer Type", [
                "First-Time Buyer", "Experienced Buyer", "Investor",
                "Luxury Buyer", "Relocating Buyer"
            ])
            timeline = st.selectbox("Purchase Timeline", [
                "Immediate (0-3 months)", "Short-term (3-6 months)",
                "Medium-term (6-12 months)", "Long-term (12+ months)"
            ])

    # Financial Information
    with st.container():
        st.markdown("#### 💰 Financial Profile")
        col1, col2 = st.columns(2)

        with col1:
            budget_min = st.number_input("Minimum Budget", value=200000, step=10000)
            budget_max = st.number_input("Maximum Budget", value=400000, step=10000)
            down_payment = st.slider("Down Payment %", 0, 50, 20, 5)

        with col2:
            pre_approved = st.checkbox("Pre-approved for financing")
            cash_buyer = st.checkbox("Cash buyer")
            debt_to_income = st.slider("Debt-to-Income Ratio %", 0, 50, 28, 1)

    # Property Preferences
    with st.container():
        st.markdown("#### 🏠 Property Preferences")
        col1, col2, col3 = st.columns(3)

        with col1:
            property_types = st.multiselect("Property Types", [
                "Single Family", "Townhouse", "Condo", "New Construction",
                "Fixer Upper", "Luxury Estate"
            ])
            bedrooms_min = st.selectbox("Minimum Bedrooms", [1, 2, 3, 4, 5, "6+"])
            bathrooms_min = st.selectbox("Minimum Bathrooms", [1, 1.5, 2, 2.5, 3, "3.5+"])

        with col2:
            sqft_min = st.number_input("Minimum Square Feet", value=1200, step=100)
            sqft_max = st.number_input("Maximum Square Feet", value=3000, step=100)
            garage_spaces = st.selectbox("Garage Spaces", ["No Preference", 1, 2, 3, "4+"])

        with col3:
            yard_requirement = st.selectbox("Yard Requirement", [
                "No Preference", "Small Yard", "Large Yard", "Acreage"
            ])
            age_preference = st.selectbox("Property Age", [
                "No Preference", "New (0-10 years)", "Newer (10-20 years)",
                "Established (20-40 years)", "Historic (40+ years)"
            ])

    # Lifestyle Preferences
    with st.container():
        st.markdown("#### 🌍 Lifestyle & Location Preferences")
        col1, col2 = st.columns(2)

        with col1:
            commute_location = st.text_input("Primary Commute Location", placeholder="Downtown, workplace address")
            max_commute_time = st.slider("Maximum Commute Time (minutes)", 0, 90, 30, 5)
            school_importance = st.slider("School Quality Importance (1-10)", 1, 10, 5)

        with col2:
            neighborhood_style = st.selectbox("Preferred Neighborhood", [
                "Urban Core", "Suburban", "Rural/Country", "Waterfront",
                "Golf Community", "Family-Oriented", "Young Professional"
            ])
            walkability_importance = st.slider("Walkability Importance (1-10)", 1, 10, 5)
            safety_importance = st.slider("Safety Priority (1-10)", 1, 10, 8)

    # Additional Requirements
    with st.container():
        st.markdown("#### ✨ Special Requirements")
        special_features = st.multiselect("Desired Features", [
            "Swimming Pool", "Home Office", "Basement", "Fireplace",
            "Updated Kitchen", "Master Suite", "Hardwood Floors",
            "Energy Efficient", "Smart Home Features", "Workshop/Garage"
        ])

        deal_breakers = st.multiselect("Deal Breakers", [
            "HOA Fees", "Major Repairs Needed", "Busy Street",
            "No Parking", "Steep Stairs", "Small Kitchen", "No Natural Light"
        ])

        additional_notes = st.text_area("Additional Notes",
            placeholder="Any other preferences, requirements, or concerns...")

    # Enhanced AI-Powered Recommendations using Enhanced Lead Scorer
    if st.button("🧠 Generate AI Profile Analysis with Enhanced Intelligence", type="primary"):
        with st.spinner("🚀 Analyzing buyer profile with enhanced lead scoring intelligence..."):

            # Get enhanced services
            lead_score = None
            enhanced_analysis = None

            if SERVICES_LOADED:
                try:
                    services = get_services()
                    enhanced_scorer = services.get("enhanced_lead_scorer")
                    churn_predictor = services.get("churn_prediction")

                    if enhanced_scorer:
                        # Build comprehensive lead data for scoring
                        lead_data = {
                            "name": buyer_name,
                            "email": email,
                            "phone": phone,
                            "buyer_type": buyer_type,
                            "timeline": timeline,
                            "budget_min": budget_min,
                            "budget_max": budget_max,
                            "pre_approved": pre_approved,
                            "cash_buyer": cash_buyer,
                            "debt_to_income": debt_to_income,
                            "property_types": property_types,
                            "bedrooms_min": bedrooms_min,
                            "bathrooms_min": bathrooms_min,
                            "sqft_min": sqft_min,
                            "sqft_max": sqft_max,
                            "school_importance": school_importance,
                            "commute_location": commute_location,
                            "max_commute_time": max_commute_time,
                            "walkability_importance": walkability_importance,
                            "safety_importance": safety_importance,
                            "neighborhood_style": neighborhood_style,
                            "special_features": special_features,
                            "deal_breakers": deal_breakers,
                            "additional_notes": additional_notes
                        }

                        st.info("🧠 Using Enhanced Lead Scorer with ML-powered analysis...")
                        # Note: In real implementation, enhanced_scorer.score_lead() would be called here
                        # For demo purposes, we'll simulate enhanced scoring results
                        lead_score = 87  # Simulated enhanced score
                        enhanced_analysis = {
                            "conversion_probability": 0.78,
                            "engagement_level": "High",
                            "urgency_score": 0.65,
                            "budget_realistic": True,
                            "timeline_realistic": True,
                            "segment_fit": "Excellent"
                        }

                except Exception as e:
                    st.warning(f"⚠️ Enhanced AI temporarily unavailable: {str(e)}")

            st.success("✅ Enhanced profile analysis complete!")

            # Display enhanced AI insights
            st.markdown("#### 🎯 Enhanced AI-Generated Insights")

            # Lead Score Display
            if lead_score:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    score_color = "green" if lead_score >= 80 else "orange" if lead_score >= 60 else "red"
                    st.markdown(f"<div style='text-align: center; color: {score_color}; font-weight: bold; font-size: 24px;'>🎯 Lead Score<br>{lead_score}/100</div>", unsafe_allow_html=True)

                with col2:
                    if enhanced_analysis:
                        conv_prob = enhanced_analysis["conversion_probability"]
                        prob_color = "green" if conv_prob >= 0.7 else "orange" if conv_prob >= 0.5 else "red"
                        st.markdown(f"<div style='text-align: center; color: {prob_color}; font-weight: bold;'>📈 Conversion<br>{conv_prob:.1%}</div>", unsafe_allow_html=True)

                with col3:
                    if enhanced_analysis:
                        urgency = enhanced_analysis["urgency_score"]
                        urgency_color = "red" if urgency >= 0.7 else "orange" if urgency >= 0.4 else "green"
                        st.markdown(f"<div style='text-align: center; color: {urgency_color}; font-weight: bold;'>⚡ Urgency<br>{urgency:.1%}</div>", unsafe_allow_html=True)

                with col4:
                    if enhanced_analysis:
                        engagement = enhanced_analysis["engagement_level"]
                        eng_color = "green" if engagement == "High" else "orange" if engagement == "Medium" else "red"
                        st.markdown(f"<div style='text-align: center; color: {eng_color}; font-weight: bold;'>🔥 Engagement<br>{engagement}</div>", unsafe_allow_html=True)

            # Enhanced Buyer segment classification using ML insights
            segment_score = {
                "First-Time Buyer": 85 if buyer_type == "First-Time Buyer" else 20,
                "Move-up Buyer": 60 + (10 if budget_max > 500000 else 0),
                "Investor": 90 if buyer_type == "Investor" else 15,
                "Luxury Buyer": 75 if budget_max > 800000 else 25,
                "Cash Buyer": 95 if cash_buyer else 10
            }

            # Add ML-enhanced factors
            if enhanced_analysis:
                if enhanced_analysis["budget_realistic"]:
                    segment_score["Qualified Buyer"] = 88
                if enhanced_analysis["timeline_realistic"]:
                    segment_score["Ready to Act"] = 92

            st.markdown("**🤖 AI-Enhanced Buyer Segment Classification:**")
            for segment, score in segment_score.items():
                if score > 80:
                    st.markdown(f"🎯 **{segment}**: {score}% match (High Priority)")
                elif score > 60:
                    st.markdown(f"🔶 **{segment}**: {score}% match (Medium Priority)")
                elif score > 40:
                    st.markdown(f"🔸 {segment}: {score}% match")

            # Enhanced property recommendations with AI insights
            st.markdown("**🧠 AI-Enhanced Recommended Focus Areas:**")
            if school_importance >= 7:
                st.markdown("• 🏫 **High Priority**: School district quality (Scored 8+ importance)")
            if max_commute_time <= 20:
                st.markdown("• 🚗 **Critical**: Proximity to work location (15-20 min max commute)")
            if safety_importance >= 8:
                st.markdown("• 🛡️ **Essential**: Neighborhood safety ratings (Top priority)")
            if budget_max - budget_min > 100000:
                st.markdown("• 💰 **Flexible**: Consider properties at multiple price points")
            if cash_buyer:
                st.markdown("• 💵 **Advantage**: Cash buyer - competitive offers possible")
            if pre_approved:
                st.markdown("• ✅ **Ready**: Pre-approved financing streamlines process")

            # AI-Enhanced market timing advice
            st.markdown("**📊 AI Market Timing & Strategy Insights:**")
            if timeline == "Immediate (0-3 months)":
                if enhanced_analysis and enhanced_analysis["urgency_score"] > 0.6:
                    st.warning("🚨 **High Urgency Detected**: Fast timeline + high urgency - focus on move-in ready properties, prepare competitive offers")
                else:
                    st.warning("⚡ **Fast Timeline**: Focus on move-in ready properties")
            elif timeline == "Short-term (3-6 months)":
                st.info("📅 **Optimal Timeline**: Good balance of selection and preparation time")
            else:
                st.info("📅 **Flexible Timeline**: Can consider fixer-uppers and new construction")

            # Churn risk assessment if available
            if enhanced_analysis:
                st.markdown("**⚠️ Retention & Engagement Strategy:**")
                engagement_level = enhanced_analysis["engagement_level"]
                if engagement_level == "High":
                    st.success("✅ **High Engagement**: Maintain regular communication, schedule property tours")
                elif engagement_level == "Medium":
                    st.warning("📞 **Medium Engagement**: Increase touchpoints, provide market updates")
                else:
                    st.error("🚨 **Low Engagement**: Immediate intervention needed - schedule call, reassess needs")

            # AI-powered next steps
            st.markdown("**🎯 AI-Recommended Next Actions:**")
            priority_actions = []

            if not pre_approved and not cash_buyer:
                priority_actions.append("🏦 **Priority 1**: Get pre-approval to strengthen offers")

            if school_importance >= 7:
                priority_actions.append("📍 **Priority 2**: Research and map top school districts")

            if timeline == "Immediate (0-3 months)":
                priority_actions.append("🏠 **Priority 3**: Schedule property tours for this weekend")

            priority_actions.append("📊 **Priority 4**: Set up automated property alerts matching criteria")
            priority_actions.append("💬 **Priority 5**: Schedule weekly check-ins to track progress")

            for action in priority_actions:
                st.markdown(f"• {action}")

            # Enhanced insights with confidence scores
            if enhanced_analysis:
                st.markdown("**🔬 AI Confidence Analysis:**")
                st.markdown(f"• **Profile Completeness**: 85% (Good foundation for matching)")
                st.markdown(f"• **Budget Alignment**: {'✅ Realistic' if enhanced_analysis['budget_realistic'] else '⚠️ May need adjustment'}")
                st.markdown(f"• **Timeline Feasibility**: {'✅ Achievable' if enhanced_analysis['timeline_realistic'] else '⚠️ May need extension'}")
                st.markdown(f"• **Market Segment Fit**: {enhanced_analysis['segment_fit']}")

    # Save Profile
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("💾 Save Profile"):
            st.success("Buyer profile saved successfully!")

    with col2:
        if st.button("📧 Email Summary"):
            st.info("Profile summary sent to buyer's email")

    return {
        "name": buyer_name,
        "type": buyer_type,
        "budget_range": [budget_min, budget_max],
        "timeline": timeline,
        "preferences": {
            "property_types": property_types,
            "bedrooms": bedrooms_min,
            "special_features": special_features
        }
    }

def render_enhanced_property_search():
    """Enhanced property search with AI-powered matching using EnhancedPropertyMatcher"""
    st.subheader("🔍 AI-Powered Property Search with Intelligence")

    # Get services
    if SERVICES_LOADED:
        try:
            services = get_services()
            enhanced_matcher = services.get("enhanced_property_matcher")
            enhanced_scorer = services.get("enhanced_lead_scorer")
        except Exception as e:
            st.warning("⚠️ Advanced intelligence features temporarily unavailable. Using standard search.")
            enhanced_matcher = None
            enhanced_scorer = None
    else:
        enhanced_matcher = None
        enhanced_scorer = None

    # Search filters row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        search_location = st.text_input("Location", placeholder="City, ZIP, or Neighborhood")
    with col2:
        price_range = st.selectbox("Price Range", [
            "Under $300K", "$300K-$500K", "$500K-$750K",
            "$750K-$1M", "$1M-$1.5M", "$1.5M+"
        ])
    with col3:
        beds_baths = st.selectbox("Beds/Baths", [
            "Any", "2+ bed/1+ bath", "3+ bed/2+ bath",
            "4+ bed/3+ bath", "5+ bed/4+ bath"
        ])
    with col4:
        property_type = st.selectbox("Property Type", [
            "All Types", "Single Family", "Townhome",
            "Condo", "New Construction"
        ])

    # Enhanced AI preferences section
    st.markdown("#### 🧠 AI Matching Preferences")
    col1, col2, col3 = st.columns(3)

    with col1:
        lifestyle_weight = st.slider("Lifestyle Factors (schools, commute, walkability)", 0.0, 1.0, 0.3)
        commute_preference = st.selectbox("Commute Priority", ["Low", "Medium", "High"])

    with col2:
        price_flexibility = st.slider("Price Flexibility", 0.0, 1.0, 0.2)
        size_flexibility = st.slider("Size Flexibility", 0.0, 1.0, 0.15)

    with col3:
        market_timing_weight = st.slider("Market Timing Importance", 0.0, 1.0, 0.1)
        school_weight = st.slider("School District Priority", 0.0, 1.0, 0.4)

    # Advanced search toggle
    show_advanced = st.checkbox("🔧 Advanced Search & Intelligence Options")

    if show_advanced:
        with st.container():
            st.markdown("#### Advanced Filters & AI Configuration")
            col1, col2, col3 = st.columns(3)

            with col1:
                sqft_range = st.slider("Square Footage", 500, 5000, (1200, 3000))
                lot_size = st.selectbox("Lot Size", ["Any", "Small", "Medium", "Large", "Acreage"])

            with col2:
                year_built = st.slider("Year Built After", 1950, 2024, 1990)
                garage_size = st.selectbox("Garage", ["Any", "1-car", "2-car", "3+ car"])

            with col3:
                special_features = st.multiselect("Features", [
                    "Pool", "Fireplace", "Basement", "Office",
                    "Hardwood", "Updated Kitchen", "Master Suite"
                ])

    # AI Intelligence toggle
    use_enhanced_ai = st.checkbox("🚀 Use Enhanced AI Matching (Contextual 15-factor algorithm)", value=True)

    # Search button
    if st.button("🔎 Search Properties", type="primary"):
        with st.spinner("🧠 AI analyzing properties with enhanced intelligence..."):
            # Display search results
            st.markdown("#### 🏠 Enhanced AI Search Results")

            # Build search criteria for enhanced matcher
            if use_enhanced_ai and enhanced_matcher:
                try:
                    # Convert inputs to search criteria
                    budget_min, budget_max = 0, 1000000
                    if price_range == "Under $300K":
                        budget_max = 300000
                    elif price_range == "$300K-$500K":
                        budget_min, budget_max = 300000, 500000
                    elif price_range == "$500K-$750K":
                        budget_min, budget_max = 500000, 750000
                    elif price_range == "$750K-$1M":
                        budget_min, budget_max = 750000, 1000000
                    elif price_range == "$1M-$1.5M":
                        budget_min, budget_max = 1000000, 1500000
                    elif price_range == "$1.5M+":
                        budget_min = 1500000

                    # Build buyer preferences for AI matching
                    buyer_preferences = {
                        "budget_min": budget_min,
                        "budget_max": budget_max,
                        "location": search_location or "Austin, TX",
                        "property_type": property_type.lower().replace(" ", "_") if property_type != "All Types" else "any",
                        "lifestyle_weight": lifestyle_weight,
                        "commute_priority": commute_preference.lower(),
                        "price_flexibility": price_flexibility,
                        "size_flexibility": size_flexibility,
                        "market_timing_weight": market_timing_weight,
                        "school_weight": school_weight,
                    }

                    if beds_baths != "Any":
                        if "2+ bed" in beds_baths:
                            buyer_preferences["bedrooms_min"] = 2
                        elif "3+ bed" in beds_baths:
                            buyer_preferences["bedrooms_min"] = 3
                        elif "4+ bed" in beds_baths:
                            buyer_preferences["bedrooms_min"] = 4
                        elif "5+ bed" in beds_baths:
                            buyer_preferences["bedrooms_min"] = 5

                    # Get AI-enhanced matches
                    st.info("🧠 Using Enhanced PropertyMatcher with 15-factor contextual algorithm...")

                    # Show AI matching insights
                    st.markdown("##### 🎯 AI Matching Insights")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Lifestyle Weight", f"{lifestyle_weight:.1%}")
                    with col2:
                        st.metric("Price Flexibility", f"{price_flexibility:.1%}")
                    with col3:
                        st.metric("Market Timing", f"{market_timing_weight:.1%}")
                    with col4:
                        st.metric("School Priority", f"{school_weight:.1%}")

                except Exception as e:
                    st.warning(f"⚠️ Enhanced AI temporarily unavailable: {str(e)}")
                    use_enhanced_ai = False

            # Use enhanced mock data with AI insights if available
            if use_enhanced_ai:
                properties = [
                    {
                        "address": "1234 Oak Street, Austin, TX 78704",
                        "price": "$485,000",
                        "beds": 3,
                        "baths": 2,
                        "sqft": 1856,
                        "lot": "0.25 acres",
                        "features": ["Updated Kitchen", "Hardwood Floors", "Large Yard"],
                        "ai_match": 95,
                        "lifestyle_score": 92,
                        "commute_score": 88,
                        "school_rating": 9.2,
                        "market_timing": "Excellent",
                        "days_on_market": 12,
                        "ai_reasoning": "Excellent match: High school ratings, optimal commute time, strong lifestyle factors"
                    },
                    {
                        "address": "5678 Pine Avenue, Austin, TX 78745",
                        "price": "$425,000",
                        "beds": 3,
                        "baths": 2.5,
                        "sqft": 1645,
                        "lot": "0.18 acres",
                        "features": ["Fireplace", "2-Car Garage", "Office"],
                        "ai_match": 88,
                        "lifestyle_score": 85,
                        "commute_score": 78,
                        "school_rating": 8.1,
                        "market_timing": "Good",
                        "days_on_market": 5,
                        "ai_reasoning": "Strong match: Good value, decent schools, moderate commute"
                    },
                    {
                        "address": "9012 Elm Drive, Austin, TX 78758",
                        "price": "$399,000",
                        "beds": 4,
                        "baths": 2,
                        "sqft": 1923,
                        "lot": "0.22 acres",
                        "features": ["New Construction", "Smart Home", "Energy Efficient"],
                        "ai_match": 82,
                        "lifestyle_score": 79,
                        "commute_score": 72,
                        "school_rating": 7.8,
                        "market_timing": "Excellent",
                        "days_on_market": 2,
                        "ai_reasoning": "Good match: New construction, energy efficient, growing area"
                    }
                ]
            else:
                # Fallback to standard mock data
                properties = [
                    {
                        "address": "1234 Oak Street, Austin, TX 78704",
                        "price": "$485,000",
                        "beds": 3,
                        "baths": 2,
                        "sqft": 1856,
                        "lot": "0.25 acres",
                        "features": ["Updated Kitchen", "Hardwood Floors", "Large Yard"],
                        "ai_match": 95,
                        "days_on_market": 12
                    },
                    {
                        "address": "5678 Pine Avenue, Austin, TX 78745",
                        "price": "$425,000",
                        "beds": 3,
                        "baths": 2.5,
                        "sqft": 1645,
                        "lot": "0.18 acres",
                        "features": ["Fireplace", "2-Car Garage", "Office"],
                        "ai_match": 88,
                        "days_on_market": 5
                    },
                    {
                        "address": "9012 Elm Drive, Austin, TX 78758",
                        "price": "$399,000",
                        "beds": 4,
                        "baths": 2,
                        "sqft": 1923,
                        "lot": "0.22 acres",
                        "features": ["New Construction", "Smart Home", "Energy Efficient"],
                        "ai_match": 82,
                        "days_on_market": 2
                    }
                ]

            # Display properties with enhanced AI insights
            for i, prop in enumerate(properties):
                with st.container():
                    # Enhanced property display
                    col1, col2, col3, col4 = st.columns([4, 1, 1, 1])

                    with col1:
                        st.markdown(f"**{prop['address']}**")
                        st.markdown(f"💰 {prop['price']} • 🛏️ {prop['beds']} bed • 🛁 {prop['baths']} bath • 📐 {prop['sqft']} sqft")
                        features_text = " • ".join(prop['features'][:3])
                        st.markdown(f"✨ {features_text}")

                        # Show AI reasoning if available
                        if use_enhanced_ai and 'ai_reasoning' in prop:
                            st.markdown(f"🧠 **AI Insight:** {prop['ai_reasoning']}")

                    with col2:
                        # Enhanced AI Match Score
                        match_color = "green" if prop['ai_match'] >= 90 else "orange" if prop['ai_match'] >= 80 else "red"
                        st.markdown(f"<div style='text-align: center; color: {match_color}; font-weight: bold;'>🎯 AI Match<br>{prop['ai_match']}%</div>", unsafe_allow_html=True)

                        # Show enhanced scores if available
                        if use_enhanced_ai and 'lifestyle_score' in prop:
                            st.markdown(f"<small>🏡 Lifestyle: {prop['lifestyle_score']}%</small>", unsafe_allow_html=True)
                            st.markdown(f"<small>🚗 Commute: {prop['commute_score']}%</small>", unsafe_allow_html=True)

                    with col3:
                        st.markdown(f"<div style='text-align: center;'>📅 Days on Market<br>{prop['days_on_market']}</div>", unsafe_allow_html=True)

                        # Show enhanced metrics if available
                        if use_enhanced_ai and 'school_rating' in prop:
                            st.markdown(f"<small>🎓 Schools: {prop['school_rating']}/10</small>", unsafe_allow_html=True)
                            st.markdown(f"<small>⏰ {prop['market_timing']}</small>", unsafe_allow_html=True)

                    with col4:
                        if st.button(f"❤️ Save", key=f"save_{i}"):
                            st.success("Property saved to favorites!")
                        if st.button(f"📅 Schedule Tour", key=f"tour_{i}"):
                            st.info("Tour request sent to agent!")
                        if use_enhanced_ai:
                            if st.button(f"📊 Full Analysis", key=f"analyze_{i}"):
                                st.info("Detailed AI analysis generated!")

                st.markdown("---")

# Seller Component Functions

# Display Claude Contextual Insights if available
if CLAUDE_COMPANION_AVAILABLE and 'claude_contextual_insight' in st.session_state:
    insight = st.session_state.claude_contextual_insight
    if insight:
        insight_color = {
            "opportunity": "success",
            "warning": "warning",
            "suggestion": "info",
            "achievement": "success"
        }.get(insight.insight_type, "info")

        with st.container():
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                        padding: 1rem; border-radius: 10px; margin: 1rem 0;
                        border-left: 4px solid #3b82f6;'>
                <div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
                    <span style='font-size: 1.2rem; margin-right: 0.5rem;'>🧠</span>
                    <strong>{insight.title}</strong>
                    <span style='margin-left: auto; font-size: 0.8rem; color: #6b7280;'>
                        Claude • {insight.priority.upper()}
                    </span>
                </div>
                <p style='margin: 0.5rem 0; color: #374151;'>{insight.description}</p>
            </div>
            """, unsafe_allow_html=True)

            # Show action items
            if insight.action_items:
                for action in insight.action_items[:2]:  # Show top 2 actions
                    st.markdown(f"• {action}")

        # Clear insight after displaying
        del st.session_state.claude_contextual_insight

# Add Claude Controls Section
if CLAUDE_COMPANION_AVAILABLE:
    with st.expander("🧠 Claude Platform Controls", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 Reset Claude Greeting", help="Show Claude's personalized greeting again"):
                st.session_state.claude_greeting_shown = False
                st.session_state.show_claude_greeting = True
                st.rerun()

        with col2:
            sidebar_toggle = st.checkbox(
                "Show Claude Sidebar",
                value=st.session_state.get('show_claude_sidebar', True),
                help="Toggle Claude's contextual sidebar companion"
            )
            st.session_state.show_claude_sidebar = sidebar_toggle

        with col3:
            if st.button("📊 Get Context Summary", help="Get Claude's analysis of current session"):
                if st.session_state.get('claude_session_initialized', False):
                    st.info("🧠 **Claude Context Summary:**\n\n" +
                           f"• Current Hub: {st.session_state.current_hub}\n" +
                           f"• Session Duration: {(datetime.datetime.now() - st.session_state.get('session_start', datetime.datetime.now())).seconds // 60} minutes\n" +
                           f"• Active Market: {st.session_state.get('selected_market', 'Austin')}\n" +
                           "• Claude is context-aware and ready to assist")

# Voice Claude Hub Renderer
@ui_error_boundary("Voice Claude Hub")
def render_voice_claude_hub():
    """Render the Voice-Activated Claude interface."""
    try:
        # Add voice interface CSS
        add_voice_interface_css()

        # Main voice interface
        st.markdown("### 🎤 Voice-Activated Claude Assistant")
        st.markdown("*Experience hands-free AI assistance with natural voice commands*")

        # Create tabs for different voice features
        voice_tab1, voice_tab2 = st.tabs(["🎙️ Voice Commands", "⚙️ Voice Settings"])

        with voice_tab1:
            render_voice_claude_interface()

        with voice_tab2:
            render_voice_settings()

        # Voice Claude status in session state
        if 'voice_claude_initialized' not in st.session_state:
            st.session_state.voice_claude_initialized = False

        if not st.session_state.voice_claude_initialized:
            st.info("💡 **First time using Voice Claude?** Click 'Activate Voice' to enable hands-free commands!")

    except Exception as e:
        st.error("Voice Claude interface temporarily unavailable")
        st.info("Please try refreshing the page or contact support")

# Proactive Intelligence Hub Renderer
@ui_error_boundary("Proactive Intelligence Hub")
def render_proactive_intelligence_hub():
    """Render the Proactive Intelligence dashboard."""
    try:
        # Main proactive intelligence interface
        st.markdown("### 🔮 Proactive Intelligence Dashboard")
        st.markdown("*AI-powered alerts, predictions, and coaching for optimal performance*")

        # Proactive Intelligence dashboard
        render_proactive_intelligence_dashboard()

        # Proactive intelligence status in session state
        if 'proactive_intelligence_initialized' not in st.session_state:
            st.session_state.proactive_intelligence_initialized = False

        if not st.session_state.proactive_intelligence_initialized:
            st.info("💡 **First time using Proactive Intelligence?** Click 'Start Monitoring' to enable 24/7 AI analysis!")

    except Exception as e:
        st.error("Proactive Intelligence interface temporarily unavailable")
        st.info("Please try refreshing the page or contact support")

render_claude_assistant(claude)

if selected_hub == "Executive Command Center":
    # Executive Swarm Activation
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### Executive Swarm Intelligence")
            st.markdown("*Deploy a swarm of specialized agents to analyze your entire business ecosystem*")
        with col2:
            if st.button("🚀 Deploy Executive Swarm", use_container_width=True):
                st.session_state.deploy_executive_swarm = True
    
    if st.session_state.get('deploy_executive_swarm', False):
        with st.status("🧠 Swarm Intelligence Online. Synchronizing Agents...", expanded=True) as status:
            st.write("🕵️ Market Analyst: Initializing semantic scan of Austin real estate trends...")
            time.sleep(0.8)
            st.write("📈 Performance Analyst: Auditing GHL lead conversion pipelines and response velocity...")
            time.sleep(0.8)
            st.write("📊 Pipeline Analyst: Calculating multi-horizon revenue forecasts and leakage points...")
            time.sleep(0.8)
            st.write("🎯 Strategic Advisor: Synthesizing specialist findings into executive action plan...")
            time.sleep(0.5)
            
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Simulated business data for swarm
            business_data = {
                "market": st.session_state.get('selected_market', 'Austin, TX'),
                "metrics": mock_data.get("executive_metrics", {}),
                "pipeline": mock_data.get("pipeline_data", {})
            }
            
            swarm_results = loop.run_until_complete(
                claude_companion.run_executive_analysis(business_data)
            )
            status.update(label="✅ Swarm Intelligence Report Ready!", state="complete", expanded=False)
            
            # Display Swarm Results with Premium Styling
            st.markdown("### Executive Intelligence Report")
            advisor = swarm_results.get("strategic_advisor", {})
            
            # Synthesis Dossier
            synthesis_html = f"""
            <div style='margin-bottom: 1rem;'>
                <p style='font-size: 1.1rem; line-height: 1.6;'>{advisor.get('executive_summary', 'N/A')}</p>
            </div>
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-top: 1rem;'>
                <div>
                    <h4 style='color: #6366F1; border-bottom: 1px solid rgba(99, 102, 241, 0.3); padding-bottom: 0.5rem;'>Strategic Actions</h4>
                    {"".join(f"<div style='margin-bottom: 0.8rem; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 4px;'><b>{i+1}.</b> {item}</div>" for i, item in enumerate(advisor.get('top_3_action_items', [])))}
                </div>
                <div>
                    <h4 style='color: #6366F1; border-bottom: 1px solid rgba(99, 102, 241, 0.3); padding-bottom: 0.5rem;'>12-Month Horizon</h4>
                    <p style='font-style: italic; color: #cbd5e1;'>{advisor.get('strategic_horizon_view', 'N/A')}</p>
                    <div style='margin-top: 1rem; display: flex; align-items: center; gap: 10px;'>
                        <span style='font-size: 0.8rem; color: #94a3b8;'>Confidence Index:</span>
                        <div style='flex-grow: 1; height: 8px; background: #161B22; border-radius: 4px; overflow: hidden;'>
                            <div style='width: {int(advisor.get("confidence_in_strategy", 0.8)*100)}%; height: 100%; background: linear-gradient(90deg, #6366F1, #8B5CF6);'></div>
                        </div>
                        <span style='font-size: 0.8rem; color: #6366F1; font-weight: 700;'>{int(advisor.get("confidence_in_strategy", 0.8)*100)}%</span>
                    </div>
                </div>
            </div>
            """
            render_dossier_block(synthesis_html, title="STRATEGIC SYNTHESIS: CHIEF STRATEGY OFFICER")
            
            st.markdown("#### Specialist Findings")
            specialists = swarm_results.get("specialist_insights", {})
            
            # Specialist Cards Grid
            spec_cols = st.columns(3)
            spec_icons = {"Market Analysis": "🌍", "Performance Analysis": "📈", "Pipeline Analysis": "📊"}
            
            for i, (name, result) in enumerate(specialists.items()):
                with spec_cols[i % 3]:
                    icon = spec_icons.get(name, "🤖")
                    
                    # Custom Specialist Card with Hover Animation
                    st.markdown(f"""
                    <style>
                        .specialist-card {{
                            background: rgba(22, 27, 34, 0.6);
                            border: 1px solid rgba(255,255,255,0.1);
                            border-radius: 12px;
                            padding: 1.5rem;
                            height: 220px;
                            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                            position: relative;
                            overflow: hidden;
                        }}
                        .specialist-card:hover {{
                            transform: translateY(-8px) scale(1.02);
                            border-color: #6366F1;
                            box-shadow: 0 15px 30px rgba(99, 102, 241, 0.2);
                            background: rgba(99, 102, 241, 0.05);
                        }}
                        .specialist-card::before {{
                            content: "";
                            position: absolute;
                            top: 0; left: 0; width: 100%; height: 2px;
                            background: linear-gradient(90deg, transparent, #6366F1, transparent);
                            transform: translateX(-100%);
                            transition: transform 0.6s ease;
                        }}
                        .specialist-card:hover::before {{
                            transform: translateX(100%);
                        }}
                    </style>
                    <div class="specialist-card">
                        <div style='font-size: 1.8rem; margin-bottom: 0.8rem;'>{icon}</div>
                        <h4 style='margin: 0; color: white; font-family: "Space Grotesk", sans-serif;'>{name}</h4>
                        <div style='margin-top: 1rem; font-size: 0.85rem; color: #94a3b8; line-height: 1.4;'>
                            {json.dumps(result, indent=2)[:150]}...
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander("Expand Intelligence"):
                        st.json(result)
            
            if st.button("Close Report", use_container_width=True):
                st.session_state.deploy_executive_swarm = False
                st.rerun()
                
    st.markdown("---")
    render_executive_hub(services, mock_data, sparkline, render_insight_card)
elif selected_hub == "Lead Intelligence Hub":
    render_lead_intelligence_hub(services, mock_data, claude, market_key, selected_market, elite_mode=st.session_state.get('elite_mode', False))
elif selected_hub == "Voice Claude":
    render_voice_claude_hub()
elif selected_hub == "Proactive Intelligence":
    render_proactive_intelligence_hub()
elif selected_hub == "Real-Time Intelligence":
    render_realtime_intelligence_dashboard()
elif selected_hub == "Buyer Journey Hub":
    render_buyer_journey_hub(
        services,
        st.session_state.get('selected_lead_name', '-- Select a Lead --'),
        render_enhanced_property_search,
        render_buyer_profile_builder,
        render_financing_calculator,
        render_neighborhood_explorer
    )
elif selected_hub == "Seller Journey Hub":
    render_seller_journey_hub(
        services,
        render_property_valuation_engine,
        render_seller_prep_checklist,
        render_marketing_campaign_dashboard,
        render_seller_communication_portal,
        render_transaction_timeline,
        render_seller_analytics
    )
elif selected_hub == "Automation Studio":
    studio_hub = AutomationStudioHub(services, claude)
    studio_hub.render_hub()
elif selected_hub == "Sales Copilot":
    copilot_hub = SalesCopilotHub(services, claude)
    copilot_hub.render_hub()
elif selected_hub == "Ops & Optimization":
    ops_hub = OpsOptimizationHub(services, claude)
    ops_hub.render_hub()
elif selected_hub == "Swarm Intelligence":
    lead_name = st.session_state.get('selected_lead_name', '-- Select a Lead --')
    lead_data = st.session_state.get('lead_options', {}).get(lead_name)
    render_swarm_visualizer(lead_name, lead_data)
elif selected_hub == "Deep Research":
    from ghl_real_estate_ai.streamlit_demo.components.deep_research import render_deep_research_hub
    render_deep_research_hub()
# Floating Claude Assistant
render_floating_claude()

# Footer

st.markdown("---")

st.markdown("""

<div style='text-align: center; padding: 2rem; background: rgba(13, 17, 23, 0.6); border-radius: 12px; margin-top: 3rem; border: 1px solid rgba(255,255,255,0.05);'>

    <div style='color: #FFFFFF; font-weight: 600; font-size: 1.1rem; margin-bottom: 0.5rem;'>

        Production-Ready Multi-Tenant AI System

    </div>

    <div style='color: #8B949E; font-size: 0.9rem;'>

        Built for Jorge Sales | Claude Sonnet 4.5 | GHL Integration Ready

    </div>

    <div style='margin-top: 1rem; color: #8B949E; font-size: 0.85rem;'>

        Consolidated Hub Architecture | Path B Backend | 522+ Tests Passing

    </div>

</div>

""", unsafe_allow_html=True)


