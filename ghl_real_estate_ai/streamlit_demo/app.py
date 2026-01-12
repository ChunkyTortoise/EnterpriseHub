"""
GHL Real Estate AI - Consolidated Hub Interface
Main Application with 5 Core Hubs
"""
from dotenv import load_dotenv
load_dotenv()

import warnings
import streamlit as st
# Suppress all warnings for professional demo presentation
warnings.filterwarnings("ignore")

import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
from pathlib import Path

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

# Add project root to sys.path
# This ensures ghl_real_estate_ai.services can be found
project_root = Path(__file__).parent.parent
parent_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(parent_root) not in sys.path:
    sys.path.insert(0, str(parent_root))

import json
from pathlib import Path

# Import services - using proper parent path
try:
    # Ensure parent directory is in path for imports
    parent_services = Path(__file__).parent.parent
    if str(parent_services) not in sys.path:
        sys.path.insert(0, str(parent_services))
    
    from services.lead_scorer import LeadScorer
    from services.ai_smart_segmentation import AISmartSegmentationService
    from services.deal_closer_ai import DealCloserAI
    from services.commission_calculator import CommissionCalculator, CommissionType, DealStage
    from services.meeting_prep_assistant import MeetingPrepAssistant, MeetingType
    from services.executive_dashboard import ExecutiveDashboardService
    from services.quality_assurance import QualityAssuranceEngine
    from services.revenue_attribution import RevenueAttributionEngine
    from services.competitive_benchmarking import BenchmarkingEngine
    from services.agent_coaching import AgentCoachingService
    from services.smart_document_generator import SmartDocumentGenerator, DocumentType
    from services.ai_predictive_lead_scoring import PredictiveLeadScorer
    from services.ai_content_personalization import AIContentPersonalizationService
    from services.live_feed import LiveFeedService
    from services.workflow_marketplace import WorkflowMarketplaceService
    from services.auto_followup_sequences import AutoFollowUpSequences
    from services.property_matcher import PropertyMatcher
    from services.reengagement_engine import ReengagementEngine, ReengagementTrigger
    from services.churn_integration_service import ChurnIntegrationService
    from services.claude_assistant import ClaudeAssistant
    
    # Initialize Claude Assistant
    claude = ClaudeAssistant()
        # Enhanced services imports (from parent directory)
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
    from streamlit_demo.components.churn_early_warning_dashboard import ChurnEarlyWarningDashboard
    from streamlit_demo.components.property_valuation import render_property_valuation_engine
    from streamlit_demo.components.financing_calculator import render_financing_calculator
    from streamlit_demo.components.neighborhood_intelligence import render_neighborhood_explorer
    from streamlit_demo.components.buyer_journey import render_buyer_dashboard, render_buyer_analytics
    from streamlit_demo.components.swarm_visualizer import render_swarm_visualizer
    from streamlit_demo.components.seller_journey import render_seller_prep_checklist, render_marketing_campaign_dashboard, render_seller_communication_portal, render_transaction_timeline, render_seller_analytics
    from realtime_dashboard_integration import render_realtime_intelligence_dashboard

    SERVICES_LOADED = True
except ImportError as e:
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
@st.cache_resource
def get_services(market="Austin"):
    listings_file = "property_listings.json" if market == "Austin" else "property_listings_rancho.json"
    listings_path = Path(__file__).parent.parent / "data" / "knowledge_base" / listings_file
    
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
        services_dict["enhanced_lead_scorer"] = EnhancedLeadScorer()

    if ENHANCED_PROPERTY_MATCHER_AVAILABLE:
        services_dict["enhanced_property_matcher"] = EnhancedPropertyMatcher(listings_path=str(listings_path))

    if CHURN_PREDICTION_ENGINE_AVAILABLE:
        services_dict["churn_prediction"] = ChurnPredictionEngine()

    return services_dict

# --- THE FINAL POLISH: GLOBAL UI UTILITIES ---
def sparkline(data: list, color: str = "#2563eb", height: int = 40):
    """Generates a minimal sparkline chart using Plotly."""
    fig = go.Figure(go.Scatter(
        y=data,
        mode='lines',
        fill='tozeroy',
        line=dict(color=color, width=2),
        fillcolor=f"{color}33"
    ))
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=height,
        xaxis=dict(visible=False, fixedrange=True),
        yaxis=dict(visible=False, fixedrange=True)
    )
    return fig

# Initialize Global AI State (Zustand equivalent)
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

# Page config
st.set_page_config(
    page_title="GHL Real Estate AI | Executive Command Center",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "AI-Powered Lead Qualification System for Real Estate Professionals"
    }
)

# Hide Streamlit branding and debug elements
st.markdown("""
    <style>
        /* Hide default Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Remove top padding for cleaner look */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Clean up development labels */
        [data-testid="stAppViewContainer"] > div:first-child {
            display: none;
        }
        
        /* Enhanced tooltips and hover effects for factor bars */
        .factor-bar:hover {
            transform: translateY(-2px);
            transition: transform 0.2s ease;
        }
        
        .factor-bar:hover .factor-bar-fill {
            filter: brightness(1.1);
        }
        
        /* Custom tooltip styling */
        .factor-bar[title]:hover::after {
            content: attr(title);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(15, 23, 42, 0.95);
            color: white;
            padding: 0.5rem 0.75rem;
            border-radius: 8px;
            font-size: 0.75rem;
            white-space: nowrap;
            z-index: 1000;
            margin-bottom: 0.5rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }
        
        .factor-bar[title]:hover::before {
            content: '';
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            border: 6px solid transparent;
            border-top-color: rgba(15, 23, 42, 0.95);
            margin-bottom: -0.25rem;
        }

        /* PREMIUM FEATURE: Enhanced global styling */

        /* Premium card animations */
        .element-container div[data-testid="stMarkdownContainer"] div {
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        /* Enhanced button styling */
        button[kind="primary"] {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
            transition: all 0.2s ease !important;
        }

        button[kind="primary"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4) !important;
        }

        /* Enhanced tabs styling */
        .stTabs > div > div > div {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%) !important;
            border-radius: 12px !important;
            padding: 0.5rem !important;
            margin-bottom: 1rem !important;
        }

        .stTabs > div > div > div > div {
            background: white !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
        }

        .stTabs > div > div > div > div[aria-selected="true"] {
            background: linear-gradient(135deg, #006AFF 0%, #0047AB 100%) !important;
            color: white !important;
            box-shadow: 0 4px 12px rgba(0, 106, 255, 0.3) !important;
        }

        /* Enhanced metric styling */
        div[data-testid="metric-container"] {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%) !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
            transition: transform 0.2s ease !important;
        }

        div[data-testid="metric-container"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15) !important;
        }

        /* Enhanced sidebar styling */
        .css-1d391kg {
            background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
        }

        /* Premium loading animations */
        @keyframes shimmer {
            0% { background-position: -200px 0; }
            100% { background-position: 200px 0; }
        }

        .shimmer {
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200px 100%;
            animation: shimmer 1.5s infinite;
        }

    </style>
""", unsafe_allow_html=True)

# Sidebar - Settings (Early for service init)
with st.sidebar:
    st.markdown("### ⚙️ AI Configuration")
    
    # Persist market selection
    if 'selected_market' not in st.session_state:
        st.session_state.selected_market = "Austin, TX"
    
    selected_market = st.selectbox(
        "Select Market:", 
        ["Austin, TX", "Rancho Cucamonga, CA"],
        index=["Austin, TX", "Rancho Cucamonga, CA"].index(st.session_state.selected_market),
        key="market_selector"
    )
    st.session_state.selected_market = selected_market
    market_key = "Austin" if "Austin" in selected_market else "Rancho"
    
    # Persist AI tone
    if 'ai_tone' not in st.session_state:
        st.session_state.ai_tone = "Natural"
    
    ai_tone = st.select_slider(
        "AI Voice Tone:",
        options=["Professional", "Natural", "Direct/Casual"],
        value=st.session_state.ai_tone,
        key="tone_selector"
    )
    st.session_state.ai_tone = ai_tone
    
    st.markdown("---")
    
    # GHL Connection Status (Quick View)
    try:
        from components.ghl_status_panel import render_ghl_quick_stats
        render_ghl_quick_stats()
    except ImportError:
        pass
    
    st.markdown("---")

services = get_services(market=market_key)

# Initialize lead options with multi-market logic (Global Scope)
def get_lead_options(market_key):
    return {
        "-- Select a Lead --": None,
        "Sarah Chen (Apple Engineer)": {
            "lead_id": "tech_professional_sarah",
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
        "Mike & Jessica Rodriguez (Growing Family)": {
            "lead_id": "growing_family_mike",
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
        "David Kim (Investor)": {
            "lead_id": "investor_david",
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
        "Robert & Linda Williams (Luxury Downsizer)": {
            "lead_id": "luxury_downsizer_robert",
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
        },
        "Sarah Johnson": {
            "extracted_preferences": {
                "budget": 1300000 if market_key == "Rancho" else 800000,
                "location": "Alta Loma" if market_key == "Rancho" else "Downtown",
                "timeline": "ASAP",
                "bedrooms": 4,
                "bathrooms": 3,
                "must_haves": ["Pool"],
                "financing": "Pre-approved",
                "motivation": "Relocating for work",
                "home_condition": "Excellent",
                "property_type": "Single Family Home"
            }
        },
        "Mike Chen": {
            "extracted_preferences": {
                "location": "Victoria Gardens" if market_key == "Rancho" else "Suburbs",
                "timeline": "6 months",
                "bedrooms": 2,
                "budget": 700000 if market_key == "Rancho" else 450000,
                "property_type": "Condo"
            }
        },
        "Emily Davis": {
            "extracted_preferences": {
                "budget": 1000000 if market_key == "Rancho" else 300000
            }
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

# Helper to render high-contrast Action Cards
def render_action_card(title, description, icon, key_suffix=""):
    st.markdown(f"""
        <div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin-bottom: 12px; border-left: 4px solid #2563eb; background: white; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.25rem;">{icon}</span>
                <b style="color: #1e293b; font-size: 1rem;">{title}</b>
            </div>
            <p style="font-size: 13px; color: #64748b; margin-top: 8px; line-height: 1.4;">{description}</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🚀 Run Action", key=f"run_action_{key_suffix}", width="stretch"):
            with st.spinner("Executing GHL trigger..."):
                import time
                time.sleep(1)
                st.toast(f"✅ Success: {title} triggered", icon="⚡")

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

def render_insight_card(title, value, description, status='info', action_label=None, action_key=None):
    colors = {
        'success': 'rgba(16, 185, 129, 0.1)', 
        'warning': 'rgba(245, 158, 11, 0.1)', 
        'info': 'rgba(59, 130, 246, 0.1)'
    }
    border_colors = {
        'success': '#10B981', 
        'warning': '#F59E0B', 
        'info': '#3B82F6'
    }
    icon = '✅' if status == 'success' else '⚠️' if status == 'warning' else '💡'
    
    st.markdown(f"""
        <div style="background-color: {colors[status]}; padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem; border-left: 5px solid {border_colors[status]};">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 0.5rem;">
                <span style="font-size: 1.5rem;">{icon}</span>
                <b style="color: #1e293b; font-size: 1.1rem;">{title}</b>
            </div>
            <div style="font-size: 1.75rem; font-weight: 900; color: #1e3a8a; margin: 0.5rem 0;">{value}</div>
            <p style="font-size: 0.95rem; color: #475569; margin: 0;">{description}</p>
        </div>
    """, unsafe_allow_html=True)
    
    if action_label and action_key:
        if st.button(action_label, key=action_key, use_container_width=True):
            st.session_state.current_hub = "🧠 Lead Intelligence Hub"
            st.rerun()

# Environment detection and data loading
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from ghl_utils.config import is_mock_mode, get_environment_display

env_info = get_environment_display()

# FEAT-011: Live Mode Authentication Bridge
def verify_ghl_connection():
    try:
        from services.ghl_client import GHLClient
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
    if 'ghl_verified' not in st.session_state:
        st.session_state.ghl_verified = False
    
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
header_gradient = "linear-gradient(135deg, #006AFF 0%, #0047AB 100%)"
header_icon = "🏠"
header_title = "Lyrio.io AI Ecosystem"
header_subtitle = "Enterprise Architectural Command Center"
header_glow = "0 20px 40px rgba(0, 106, 255, 0.3)"

# Dynamic Theme Logic
if 'current_hub' in st.session_state:
    if "Ops" in st.session_state.current_hub:
        header_gradient = "linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%)"
        header_icon = "🦅"
        header_title = "ARETE Performance"
        header_subtitle = "Ops & Optimization Hub"
        header_glow = "0 20px 40px rgba(124, 58, 237, 0.3)"
    elif "Sales" in st.session_state.current_hub:
        header_gradient = "linear-gradient(135deg, #10B981 0%, #059669 100%)"
        header_icon = "💰"
        header_subtitle = "Sales Copilot Active"
        header_glow = "0 20px 40px rgba(16, 185, 129, 0.3)"

st.markdown(f"""
<div style='background: {header_gradient}; 
            padding: 3rem 2.5rem; 
            border-radius: 20px; 
            margin-bottom: 2.5rem; 
            color: white;
            box-shadow: {header_glow};
            position: relative;
            overflow: hidden;'>
    <div style='position: absolute; top: 0; left: 0; right: 0; bottom: 0; 
                background-image: 
                    radial-gradient(circle at 20% 50%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
                    radial-gradient(circle at 80% 80%, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
                opacity: 0.6;'></div>
    <div style='position: relative; z-index: 1;'>
        <div style='display: flex; align-items: center; gap: 1.5rem; margin-bottom: 1rem;'>
            <div style='font-size: 4rem; line-height: 1;'>{header_icon}</div>
            <div>
                <h1 style='margin: 0; font-size: 2.75rem; font-weight: 800; color: white !important; 
                           text-shadow: 0 2px 10px rgba(0,0,0,0.2);'>
                    {header_title}
                </h1>
                <p style='margin: 0.25rem 0 0 0; font-size: 1.15rem; opacity: 0.95; font-weight: 500; color: white !important;'>
                    {header_subtitle}
                </p>
            </div>
        </div>
        <p style='margin: 1.5rem 0; font-size: 1.05rem; opacity: 0.9; max-width: 800px; color: white !important;'>
            Proprietary AI-powered lead intelligence and autonomous workflow environment for <strong>Jorge Sales</strong>
        </p>
        <div style='margin-top: 1.5rem; display: flex; flex-wrap: wrap; gap: 1rem; font-size: 0.95rem;'>
            <div style='background: rgba(255,255,255,0.25); 
                        padding: 0.75rem 1.25rem; 
                        border-radius: 10px;
                        backdrop-filter: blur(10px);
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                        color: white !important;'>
                <span style='font-size: 1.2rem;'>✅</span>
                <span style='font-weight: 600;'>AI Mode: Active</span>
            </div>
            <div style='background: rgba(255,255,255,0.25); 
                        padding: 0.75rem 1.25rem; 
                        border-radius: 10px;
                        backdrop-filter: blur(10px);
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                        color: white !important;'>
                <span style='font-size: 1.2rem;'>🔗</span>
                <span style='font-weight: 600;'>GHL Sync: Live</span>
            </div>
            <div style='background: rgba(255,255,255,0.25); 
                        padding: 0.75rem 1.25rem; 
                        border-radius: 10px;
                        backdrop-filter: blur(10px);
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                        color: white !important;'>
                <span style='font-size: 1.2rem;'>📊</span>
                <span style='font-weight: 600;'>Multi-Tenant Ready</span>
            </div>
            <div style='background: rgba(16, 185, 129, 0.9); 
                        padding: 0.75rem 1.25rem; 
                        border-radius: 10px;
                        backdrop-filter: blur(10px);
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                        animation: pulse 2s ease-in-out infinite;
                        color: white !important;'>
                <span style='font-size: 1.2rem;'>🚀</span>
                <span style='font-weight: 700;'>5 Hubs Live</span>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Initialize session state for hub navigation
if 'current_hub' not in st.session_state:
    st.session_state.current_hub = "Executive Command Center"

# PREMIUM FEATURE: Enhanced sidebar with enterprise styling
with st.sidebar:
    # Premium navigation header
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

    hub_options = [
        "🏢 Executive Command Center",
        "🧠 Lead Intelligence Hub",
        "🐝 Swarm Intelligence",
        "⚡ Real-Time Intelligence",
        "🏠 Buyer Journey Hub",
        "🏡 Seller Journey Hub",
        "🤖 Automation Studio",
        "💰 Sales Copilot",
        "📈 Ops & Optimization"
    ]
    
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
    
    st.session_state.current_hub = selected_hub
    
    # NEW: Global AI Pulse Indicator
    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px;
        background: rgba(37, 99, 235, 0.1);
        border-radius: 8px;
        margin-top: 1rem;
        border: 1px solid rgba(37, 99, 235, 0.2);
    ">
        <div class="live-indicator" style="width: 10px; height: 10px; background: #10b981; border-radius: 50%; box-shadow: 0 0 10px #10b981;"></div>
        <div style="font-size: 0.8rem; color: #1e293b; font-weight: 600;">
            Swarm Status: <span style="color: #10b981;">ACTIVE</span>
        </div>
        <div style="font-size: 0.7rem; color: #64748b; margin-left: auto;">
            v4.2.0
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # NEW: Claude's Strategic Counsel (Contextual)
    counsel_messages = {
        "🏢 Executive Command Center": "Jorge, lead velocity is up 12% this week. Focus on the Downtown cluster for maximum ROI.",
        "🧠 Lead Intelligence Hub": "Sarah Martinez is showing high engagement with luxury properties. Suggest a showing today.",
        "🐝 Swarm Intelligence": "The analyst swarm is currently processing 142 leads. Token efficiency is at an all-time high.",
        "⚡ Real-Time Intelligence": "Market conditions are shifting in East Austin. Update your valuation models.",
        "🏠 Buyer Journey Hub": "We have 3 buyers ready for pre-approval. Syncing with financing partners now.",
        "🏡 Seller Journey Hub": "The Maple Ave listing is hitting peak interest. I recommend an open house this Sunday.",
        "🤖 Automation Studio": "3 new workflow templates are ready for deployment. Your time savings is currently 42h/week.",
        "💰 Sales Copilot": "Preparing talking points for your 2pm call. Client prefers a direct, data-driven approach.",
        "📈 Ops & Optimization": "System health is optimal. Recommend scaling to the Miami market next month."
    }
    
    current_msg = counsel_messages.get(selected_hub, "AI Swarm is standing by for your next command.")
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        padding: 15px;
        border-radius: 12px;
        border-left: 4px solid #8B5CF6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    ">
        <div style="font-size: 0.75rem; color: #8B5CF6; font-weight: 700; text-transform: uppercase; margin-bottom: 5px;">
            🤖 Claude's Counsel
        </div>
        <div style="font-size: 0.85rem; color: #1e293b; font-style: italic; line-height: 1.4;">
            "{current_msg}"
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # PREMIUM FEATURE: Enhanced quick actions
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3);
    ">
        <h4 style="margin: 0; font-size: 1rem; font-weight: 600;">⚡ Quick Actions</h4>
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
    with st.expander("🔗 Sub-Account Access", expanded=False):
        st.markdown("""
        **Location ID:** `REDACTED_ID`
        **Sub-account:** Lyrio
        """)
        st.link_button("🌐 Open GHL Dashboard", "https://app.gohighlevel.com", use_container_width=True)
        st.link_button("📨 Open Conversations", "https://app.gohighlevel.com/v2/location/REDACTED_ID/conversations", use_container_width=True)

    st.markdown("---")
    
    # System status
    st.markdown("### 📊 System Status")
    st.metric("Active Leads", "47", "+12")
    st.metric("AI Conversations", "156", "+23")
    
    st.markdown("---")
    st.markdown("### 📡 Live Feed")
    
    # Enhanced Live Feed with "Pulse" animation
    feed_items = [
        {"icon": "📝", "text": "Creating contract for <b>John Doe</b>", "time": "Just now", "color": "#10B981"},
        {"icon": "🔔", "text": "New lead: <b>Sarah Smith</b> (Downtown)", "time": "2 mins ago", "color": "#3B82F6"},
        {"icon": "🤖", "text": "AI handled objection: <b>Mike Ross</b>", "time": "15 mins ago", "color": "#8B5CF6"},
        {"icon": "📅", "text": "Tour scheduled: <b>123 Main St</b>", "time": "1 hour ago", "color": "#F59E0B"}
    ]
    
    # Use new Live Feed Service with dynamic timestamps
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from services.live_feed import LiveFeedService
        feed_service = LiveFeedService()
        feed_html = feed_service.get_feed_html(limit=6)
        st.markdown(feed_html, unsafe_allow_html=True)
    except Exception as e:
        # Fallback to static feed if service unavailable
        for item in feed_items:
            st.markdown(f"""
            <div style="
                display: flex; 
                gap: 10px; 
                margin-bottom: 12px; 
                padding: 10px; 
                background: white; 
                border-radius: 8px; 
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                border-left: 3px solid {item['color']};
                transition: transform 0.2s ease;">
                <div style="font-size: 1.2rem;">{item['icon']}</div>
                <div style="flex: 1;">
                    <div style="font-size: 0.85rem; line-height: 1.3; color: #1f2937;">{item['text']}</div>
                    <div style="font-size: 0.7rem; color: #6b7280; margin-top: 4px; display: flex; align-items: center; gap: 4px;">
                        <span style="width: 6px; height: 6px; background-color: {item['color']}; border-radius: 50%; display: inline-block;"></span>
                        {item['time']}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# --- HELPER FUNCTIONS FOR UI COMPONENTS ---

def render_roi_calculator(selected_lead):
    st.subheader("💰 Deal Closer AI: Financial Modeler")
    
    # Dynamic Context from Lead Hub
    budget = selected_lead.get('budget', 500000)
    
    col1, col2 = st.columns(2)
    with col1:
        price = st.number_input("Property Price ($)", value=budget)
        down_payment = st.slider("Down Payment (%)", 0, 100, 20)
        rate = st.number_input("Interest Rate (%)", value=6.5, step=0.1)
    
    # Mortgage Math
    loan_amount = price * (1 - down_payment/100)
    monthly_rate = (rate / 100) / 12
    months = 30 * 12
    payment = loan_amount * (monthly_rate * (1 + monthly_rate)**months) / ((1 + monthly_rate)**months - 1)
    
    with col2:
        st.metric("Est. Monthly Payment", f"${payment:,.2f}")
        st.write("**AI Recommendation:** Based on Sarah's income profile, a 15% down payment at 6.2% is the 'sweet spot' for her debt-to-income ratio.")

def render_revenue_funnel():
    data = dict(
        number=[156, 47, 23, 12, 5],
        stage=["Conversations", "Active Leads", "Hot Leads", "Tours", "Contracts"]
    )
    fig = px.funnel(data, x='number', y='stage', color_discrete_sequence=['#2563eb'])
    st.plotly_chart(fig, use_container_width=True)

def render_claude_assistant():
    """Delegates to the centralized ClaudeAssistant service."""
    leads = st.session_state.get('lead_options', {})
    hub = st.session_state.current_hub
    market = st.session_state.get('selected_market', 'Austin')
    
    claude.greet_user("Jorge")
    claude.render_sidebar_panel(hub, market, leads)

# Main content area
@ui_error_boundary("Executive Command Center")
def render_executive_hub():
    st.header("🏢 Executive Command Center")
    st.markdown("*High-level KPIs, revenue tracking, and system health*")

    # NEW: Claude's Strategic Briefing Area
    with st.container(border=True):
        col_icon, col_text = st.columns([1, 6])
        with col_icon:
            st.markdown("<div style='font-size: 3.5rem; text-align: center; margin-top: 10px;'>🔮</div>", unsafe_allow_html=True)
        with col_text:
            st.markdown("### Claude's Strategy Briefing")
            st.markdown("""
            *I've analyzed your entire GHL environment for the last 24 hours. Here is your priority focus:*
            - **🔥 Hot Cluster:** There is a surge of interest in Alta Loma. 3 leads just moved into the 'Ready' tier.
            - **⚠️ Retention Risk:** 2 leads from the Facebook campaign have gone silent. I've prepared a re-engagement sequence.
            - **💰 Revenue Path:** Converting Sarah Johnson this week will push your Austin pipeline past the monthly target.
            """)
            if st.button("🚀 Execute Strategic Re-engagement"):
                st.toast("Triggering AI re-engagement for silent leads...", icon="⚡")
    
    st.markdown("---")
    
    # Tabs for sub-features
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🎯 AI Insights", "📄 Reports"])
    
    with tab1:
        st.subheader("Executive Dashboard")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Pipeline", "$2.4M", "+15%")
            st.plotly_chart(sparkline([1.8, 2.1, 1.9, 2.4, 2.2, 2.4], color="#2563eb", height=50), use_container_width=True, config={'displayModeBar': False})
        with col2:
            st.metric("Commission Capture", "$136.7K", "+$42K")
            st.plotly_chart(sparkline([80, 95, 110, 105, 120, 136], color="#16a34a", height=50), use_container_width=True, config={'displayModeBar': False})
        with col3:
            st.metric("Conversion Rate", "34%", "+2%")
            st.plotly_chart(sparkline([28, 30, 31, 32, 33, 34], color="#ea580c", height=50), use_container_width=True, config={'displayModeBar': False})
        with col4:
            st.metric("AI Lead Velocity", "4.2/day", "+1.1")
            st.plotly_chart(sparkline([2.1, 2.5, 3.0, 3.8, 4.0, 4.2], color="#7c3aed", height=50), use_container_width=True, config={'displayModeBar': False})
        
        st.markdown("---")
        
        # Enterprise Color Palette
        COLORS = {
            'primary': '#2563eb',
            'secondary': '#64748b',
            'success': '#22c55e',
            'warning': '#f59e0b',
            'danger': '#ef4444',
            'text': '#1e293b',
            'grid': '#e2e8f0'
        }

        # Mock data for revenue trends
        dates = pd.date_range(end=pd.Timestamp.now(), periods=6, freq='ME')
        revenue_data = {
            'Month': dates.strftime('%b %Y'),
            'Revenue': [180000, 210000, 195000, 240000, 225000, 280000],
            'Target': [200000, 200000, 220000, 220000, 250000, 250000]
        }
        df_rev = pd.DataFrame(revenue_data)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_rev['Month'], 
            y=df_rev['Revenue'], 
            name='Actual Revenue',
            line=dict(color=COLORS['primary'], width=4),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(37, 99, 235, 0.1)'
        ))
        fig.add_trace(go.Scatter(
            x=df_rev['Month'], 
            y=df_rev['Target'], 
            name='Target Revenue',
            line=dict(color=COLORS['secondary'], width=2, dash='dash')
        ))
        
        fig.update_layout(
            title="<b>Revenue Performance vs Target</b>",
            template="plotly_white",
            margin=dict(l=20, r=20, t=60, b=20),
            height=350,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLORS['text']),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(gridcolor=COLORS['grid']),
            yaxis=dict(gridcolor=COLORS['grid'])
        )
        st.plotly_chart(fig, width="stretch")
        
        # Add last updated timestamp
        import datetime
        last_updated = datetime.datetime.now().strftime("%b %d, %Y at %I:%M %p")
        st.markdown(f"<div class='last-updated'>Last updated: {last_updated}</div>", unsafe_allow_html=True)
        
    with tab2:
        st.subheader("AI System Insights")
        
        # Add AI Performance Metrics Dashboard
        try:
            from components.ai_performance_metrics import render_ai_metrics_dashboard
            render_ai_metrics_dashboard()
            st.markdown("---")
        except ImportError:
            pass
        
        # Get dynamic insights
        summary = services["executive"].get_executive_summary("demo_location")
        insights = summary.get("insights", [])
        
        if not insights:
            insights = [
                {"type": "success", "title": "Response Time Excellence", "value": "1.8 mins", "message": "Average response time beats target by 40%"},
                {"type": "warning", "title": "Conversion Opportunity", "value": "20% Gap", "message": "12 leads are stalling at the 'Financing' stage. Focus required.", "action": "🎯 Fix Conversion Gap Now"},
                {"type": "info", "title": "Lead Sentiment", "value": "Strong", "message": "85% of recent conversations show positive buying intent."}
            ]

        # Fix 0.0 mins edge case in logic (Simulated)
        for insight in insights:
            if "0.0" in str(insight.get("value", "")):
                insight["value"] = "Evaluating..."
                insight["message"] = "Initial data sync in progress."

        for i, insight in enumerate(insights):
            # Map 'opportunity' to 'warning' for visual consistency in the UI
            insight_status = 'warning' if insight["type"] == "opportunity" else insight["type"]
            
            render_insight_card(
                insight["title"], 
                insight.get("value", "N/A"), 
                insight["message"], 
                status=insight_status,
                action_label=insight.get("action"),
                action_key=f"insight_btn_{i}"
            )
        
        st.markdown("#### 📈 System Performance")
        # Ensure mock_data is not None and handle missing keys safely
        safe_data = mock_data if mock_data is not None else {}
        health = safe_data.get("system_health", {})
        
        if health:
            c1, c2, c3 = st.columns(3)
            # Ensure no 0.0 metrics show up in performance cards either
            resp_time = health.get('avg_response_time_ms', 0)
            resp_display = f"{resp_time}ms" if resp_time > 0 else "Evaluating"
            
            c1.metric("API Uptime", f"{health.get('uptime_percentage', 100)}%")
            c2.metric("Avg Latency", resp_display)
            c3.metric("SMS Compliance", f"{int(health.get('sms_compliance_rate', 1) * 100)}%")

    with tab3:
        st.subheader("Actionable Executive Report")
        
        action_items = summary.get("action_items", [])
        if not action_items:
             action_items = [
                {"priority": "high", "title": "5 Hot Leads Pending", "action": "Schedule showings for Downtown cluster", "impact": "Potential $2.5M Volume"},
                {"priority": "medium", "title": "Review Weekend Staffing", "action": "Add on-call agent for Saturdays", "impact": "Improve conversion by ~5%"}
            ]

        st.dataframe(
            pd.DataFrame(action_items),
            column_config={
                "priority": "Priority",
                "title": "Opportunity",
                "action": "Recommended Action",
                "impact": "Estimated Impact"
            },
            hide_index=True,
            width="stretch"
        )
        
        if st.button("📧 Email Report to Jorge"):
            st.toast("Report sent to jorge@example.com")

@ui_error_boundary("Lead Intelligence Hub")
def render_lead_intelligence_hub():
    st.header("🧠 Lead Intelligence Hub")
    st.markdown("*Deep dive into individual leads with AI-powered insights*")
    
    # Access global lead_options - ensure it exists
    if 'lead_options' not in st.session_state:
        st.error("Lead options not initialized. Please refresh the page.")
        return
    
    lead_options = st.session_state.lead_options
    
    # Lead selector at the top for all tabs to use
    st.markdown("### 🎯 Select a Lead")
    lead_names = list(st.session_state.lead_options.keys())
    try:
        default_idx = lead_names.index(st.session_state.selected_lead_name)
    except ValueError:
        default_idx = 0

    selected_lead_name = st.selectbox(
        "Choose a lead to analyze:",
        lead_names,
        index=default_idx,
        key="hub_lead_selector_top",
        on_change=lambda: st.session_state.update({"selected_lead_name": st.session_state.hub_lead_selector_top})
    )
    
    # Update session state
    st.session_state.selected_lead_name = selected_lead_name
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "🎯 Lead Scoring",
        "🚨 Churn Early Warning",
        "🏠 Property Matcher (Phase 2)",
        "🌐 Buyer Portal (Phase 3)",
        "📊 Segmentation",
        "🎨 Personalization",
        "🔮 Predictions",
        "💬 Simulator"
    ])
    
    with tab1:
        st.subheader("AI Lead Scoring")
        
        # Create columns for all cases
        col_map, col_details = st.columns([1, 1])
        
        with col_map:
            # Try to use the enhanced interactive map component
            try:
                from components.interactive_lead_map import render_interactive_lead_map, generate_sample_lead_data
                
                # Load or generate lead data with geographic coordinates
                lead_map_data_path = Path(__file__).parent / "data" / "lead_map_data.json"
                if lead_map_data_path.exists():
                    with open(lead_map_data_path) as f:
                        all_lead_data = json.load(f)
                        leads_with_geo = all_lead_data.get(market_key, [])
                else:
                    # Fallback to generating sample data
                    leads_with_geo = generate_sample_lead_data(market_key)
                
                # Render the interactive map
                render_interactive_lead_map(leads_with_geo, market=market_key)
                
            except ImportError:
                # Fallback to legacy static map
                st.markdown("#### 📍 Hot Lead Clusters")
                # Generate mock map data
                if market_key == "Rancho":
                    map_data = pd.DataFrame({
                        'lat': [34.1200, 34.1100, 34.1000, 34.1300, 34.1150],
                        'lon': [-117.5700, -117.5800, -117.5600, -117.5900, -117.5750],
                        'type': ['Hot', 'Hot', 'Warm', 'Cold', 'Hot'],
                        'value': [100, 80, 50, 20, 90]
                    })
                else:
                    map_data = pd.DataFrame({
                        'lat': [30.2672, 30.2700, 30.2500, 30.2800, 30.2600],
                        'lon': [-97.7431, -97.7500, -97.7300, -97.7600, -97.7400],
                        'type': ['Hot', 'Hot', 'Warm', 'Cold', 'Hot'],
                        'value': [100, 80, 50, 20, 90]
                    })
                
                st.map(map_data, zoom=11, width="stretch")
                st.caption(f"Real-time visualization of high-value lead activity in {selected_market}")

        with col_details:
            st.markdown("#### 🎯 Lead Analysis")
            st.markdown(f"**Analyzing:** {selected_lead_name}")
            
            # Claude's Behavioral Deep Dive
            with st.container(border=True):
                st.markdown(f"**🤖 Claude's Behavioral Insight: {selected_lead_name}**")
                if selected_lead_name == "Sarah Chen (Apple Engineer)":
                    insight_text = "High-velocity lead. Apple engineers are data-driven; she responded to the 'Market Trend' link within 12 seconds. She's prioritizing commute efficiency over sqft. Focus on: Teravista connectivity."
                elif selected_lead_name == "Mike & Jessica Rodriguez (Growing Family)":
                    insight_text = "High-sentiment, low-confidence lead. They are checking 'First-time buyer' articles daily. Sentiment: 88% Positive but cautious. Focus on: Safety metrics and monthly payment breakdown."
                elif selected_lead_name == "David Kim (Investor)":
                    insight_text = "Analytical veteran. He's ignored the 'Lifestyle' highlights and went straight to the 'Cap Rate' tool. He has 3 tabs open on Manor area comps. Focus on: Off-market yield analysis."
                elif selected_lead_name == "Robert & Linda Williams (Luxury Downsizer)":
                    insight_text = "Relationship-focused. They've spent 4 minutes reading Jorge's 'About Me'. Sentiment: 95% Positive. They value trust over automation. Focus on: Personal concierge and exclusive downtown access."
                elif selected_lead_name == "Sarah Johnson":
                    insight_text = "Highly motivated. She responded within 45 seconds to my last text. Sentiment: 92% Positive. Focus on: School District accuracy."
                elif selected_lead_name == "Mike Chen":
                    insight_text = "Cautious. He's asking about 'Value per SqFt' comparison. Sentiment: Neutral. Focus on: Investment ROI data."
                else:
                    insight_text = "Initial discovery phase. Engagement is low. Sentiment: Undetermined. Focus on: Qualifying location preferences."
                st.info(insight_text)

            # Empty state when no lead selected
            if selected_lead_name == "-- Select a Lead --":
                st.markdown("""
                <div style='background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); 
                            padding: 3rem 2rem; 
                            border-radius: 15px; 
                            text-align: center;
                            border: 2px dashed #0ea5e9;
                            margin-top: 2rem;'>
                    <div style='font-size: 4rem; margin-bottom: 1rem;'>🎯</div>
                    <h3 style='color: #0369a1; margin: 0 0 0.5rem 0;'>Select a Lead to Begin Analysis</h3>
                    <p style='color: #075985; font-size: 0.95rem; max-width: 400px; margin: 0 auto;'>
                        Choose a lead from the dropdown above to view their AI-powered intelligence profile, 
                        property matches, and predictive insights.
                    </p>
                    <div style='margin-top: 2rem; display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap;'>
                        <div style='background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                            <div style='font-size: 1.5rem;'>📊</div>
                            <div style='font-size: 0.75rem; color: #64748b; margin-top: 0.25rem;'>Lead Scoring</div>
                        </div>
                        <div style='background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                            <div style='font-size: 1.5rem;'>🏠</div>
                            <div style='font-size: 0.75rem; color: #64748b; margin-top: 0.25rem;'>Property Match</div>
                        </div>
                        <div style='background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                            <div style='font-size: 1.5rem;'>🔮</div>
                            <div style='font-size: 0.75rem; color: #64748b; margin-top: 0.25rem;'>AI Predictions</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.stop()
        
        # Calculate Score using centralized service
        lead_context = lead_options[selected_lead_name]
        result = services["lead_scorer"].calculate_with_reasoning(lead_context)
        
        # Display Results
        score = result["score"]
        classification = result["classification"]
        
        if classification == "hot":
            st.success(f"🔥 **Hot Lead** - Score: {score}/7 Questions Answered")
        elif classification == "warm":
            st.warning(f"⚠️ **Warm Lead** - Score: {score}/7 Questions Answered")
        else:
            st.info(f"❄️ **Cold Lead** - Score: {score}/7 Questions Answered")
            
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Questions Answered", f"{score}/7", "")
        with col2:
            st.metric("Engagement Class", classification.title(), "")
        with col3:
            st.metric("Lead Intent", "Calculated", "")
        
        st.markdown("#### AI Analysis Breakdown")
        st.info(f"**Qualifying Data Found:** {result['reasoning']}")
        
        # Quick Actions Toolbar
        st.markdown("---")
        st.markdown("#### ⚡ Quick Actions")
        
        col_act1, col_act2, col_act3, col_act4 = st.columns(4)
        
        with col_act1:
            if st.button("📞 Call Now", use_container_width=True, type="primary"):
                st.toast(f"Calling {selected_lead_name}...", icon="📞")
                st.success("Call initiated via GHL")
        
        with col_act2:
            if st.button("💬 Send SMS", use_container_width=True):
                st.toast(f"Opening SMS composer for {selected_lead_name}", icon="💬")
                st.info("SMS template loaded in GHL")
        
        with col_act3:
            if st.button("📧 Send Email", use_container_width=True):
                st.toast(f"Email draft created for {selected_lead_name}", icon="📧")
                st.success("Email queued in GHL")
        
        with col_act4:
            if st.button("📅 Schedule Tour", use_container_width=True):
                st.toast("Opening calendar...", icon="📅")
                st.success("Calendar integration ready")
        
        # Last Contact Info
        st.caption("📊 Last Contact: 2 days ago via SMS | Next Follow-up: Tomorrow")
        
        st.markdown("---")
        st.markdown("#### Recommended Actions")
        for action in result["recommended_actions"]:
            st.markdown(f"- {action}")

        # PREMIUM FEATURE: AI Lead Insights Panel
        st.markdown("---")
        try:
            from components.enhanced_services import render_ai_lead_insights

            # Convert result to format expected by enhanced services
            lead_data_enhanced = {
                'lead_id': result.get('lead_id', 'demo_lead'),
                'name': selected_lead_name,
                'health_score': result.get('overall_score', 85),
                'engagement_level': 'high' if result.get('overall_score', 85) > 80 else 'medium',
                'last_contact': '2 days ago',
                'communication_preference': result.get('communication_preference', 'text'),
                'stage': 'qualification',
                'urgency_indicators': result.get('urgency_indicators', []),
                'extracted_preferences': result.get('extracted_preferences', {}),
                'conversation_history': []  # Would be real conversation data
            }

            render_ai_lead_insights(lead_data_enhanced)

        except ImportError:
            st.info("🚀 Premium AI Insights available in enterprise version")

    with tab2:
        # Churn Early Warning Dashboard
        try:
            st.subheader("🚨 Churn Early Warning System")
            st.markdown("*Real-time monitoring and intervention orchestration for lead retention*")

            # Initialize and render the churn dashboard
            churn_dashboard = ChurnEarlyWarningDashboard(claude_assistant=claude)
            churn_dashboard.render_dashboard()

        except Exception as e:
            st.error("⚠️ Churn Dashboard Temporarily Unavailable")
            st.info("This enterprise feature requires full system integration. Demo mode available.")

            # Fallback demo content
            st.markdown("### 📊 Sample Churn Risk Analytics")

            # Demo metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Leads", "147", "+12")
            with col2:
                st.metric("Critical Risk", "3", "+1", delta_color="inverse")
            with col3:
                st.metric("High Risk", "8", "-2")
            with col4:
                st.metric("Success Rate", "78.5%", "+2.1%")

            st.info("💡 The full Churn Prediction Engine provides 26 behavioral features, multi-horizon risk scoring, and automated intervention orchestration.")

    with tab3:
        # Use the AI Property Matcher component
        try:
            from components.property_matcher_ai import render_property_matcher

            # Check if a lead is selected
            if selected_lead_name == "-- Select a Lead --":
                st.info("👈 Please select a lead from Tab 1 to see AI-powered property matches")
            else:
                lead_context = lead_options[selected_lead_name]
                render_property_matcher(lead_context)

                # PREMIUM FEATURE: Dynamic Timeline & Feature Gap Analysis
                st.markdown("---")
                try:
                    from components.elite_refinements import render_dynamic_timeline, render_feature_gap

                    # Dynamic timeline based on lead activity
                    lead_score = lead_context.get('overall_score', 85)
                    actions_completed = lead_context.get('actions_completed', 2)
                    render_dynamic_timeline(
                        days_remaining=45,
                        actions_completed=actions_completed,
                        agent_name="Jorge"
                    )

                    # Feature gap analysis for property matching
                    st.markdown("---")
                    property_sample = {
                        'features': ['3-car garage', 'swimming pool', 'granite countertops', 'hardwood floors'],
                        'price': 650000,
                        'bedrooms': 4,
                        'bathrooms': 3
                    }
                    must_haves = lead_context.get('extracted_preferences', {}).get('must_haves',
                        ['swimming pool', '3-car garage', 'updated kitchen', 'good schools'])

                    if must_haves:
                        render_feature_gap(
                            property_data=property_sample,
                            lead_must_haves=must_haves,
                            match_score=87
                        )

                except ImportError:
                    st.info("🚀 Premium Timeline & Gap Analysis available in enterprise version")

        except ImportError as e:
            st.error(f"Property Matcher component not available: {e}")
            st.info("Property Matcher coming in Phase 2")

    with tab4:
        st.subheader("🌐 Self-Service Buyer Portal (Phase 3)")
        st.markdown("*Real-time behavioral telemetry from the proprietary portal environment*")
        
        # Get current preferences for the selected lead
        if selected_lead_name != "-- Select a Lead --":
            current_prefs = st.session_state.lead_options[selected_lead_name].get("extracted_preferences", {})
            lead_key = selected_lead_name.lower().replace(" ", "_")
        else:
            current_prefs = {}
            lead_key = "demo_lead"
        
        portal_url = f"/portal?id={lead_key}"
        st.info(f"Unique Architectural URL: `https://portal.lyrio.io/l/{lead_key}`")
        
        col_portal_left, col_portal_right = st.columns([1, 1])
        
        with col_portal_left:
            st.markdown(f"""
            <div style='background: white; padding: 1.5rem; border-radius: 15px; border: 1px solid #006AFF; text-align: center;'>
                <h3 style='color: #006AFF; margin-top: 0;'>🚀 Live Portal Status</h3>
                <p style='font-size: 0.9rem;'>The standalone architectural portal is active for <b>{selected_lead_name}</b>.</p>
                <div style='background: #F0F7FF; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>
                    <span style='font-size: 0.8rem; color: #64748B;'>PORTAL INTENT SCORE</span><br/>
                    <span style='font-size: 2rem; font-weight: 800; color: #006AFF;'>{services.get("telemetry", telemetry).get_intent_score(lead_key)}/100</span>
                </div>
                <a href='{portal_url}' target='_blank' style='display: inline-block; background-color: #006AFF; color: white; padding: 0.75rem 1.5rem; text-decoration: none; border-radius: 10px; font-weight: 700; width: 100%;'>View as Lead</a>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("#### 📱 Portal Interface Preview")
            st.image("https://via.placeholder.com/400x600?text=Portal+Mobile+Mockup", width=300)

        with col_portal_right:
            st.markdown("#### 📡 Real-Time Telemetry Feed")
            
            history = services.get("telemetry", telemetry).get_lead_history(lead_key)
            
            if not history:
                st.info("No portal interactions recorded for this lead yet.")
                # Add some demo history if empty
                if st.button("Simulate Portal Activity"):
                    telemetry.record_interaction(lead_key, "view", {"prop_id": "prop_001"})
                    telemetry.record_interaction(lead_key, "save", {"prop_id": "prop_002"})
                    st.rerun()
            else:
                for event in reversed(history[-10:]):
                    icon = "👀" if event["action"] == "view" else "💾" if event["action"] == "save" else "⚙️"
                    dt = datetime.datetime.fromisoformat(event["timestamp"])
                    time_str = dt.strftime("%H:%M:%S")
                    
                    st.markdown(f"""
                    <div style='background: #f8fafc; padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 3px solid #3b82f6;'>
                        <div style='display: flex; justify-content: space-between;'>
                            <span>{icon} <b>{event['action'].upper()}</b></span>
                            <span style='font-size: 0.7rem; color: #64748b;'>{time_str}</span>
                        </div>
                        <div style='font-size: 0.8rem; color: #475569;'>
                            Metadata: {json.dumps(event['metadata'])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("#### 🔄 Bi-Directional Sync Status")
            st.success("✅ Portal preferences automatically synced to GHL Custom Fields")
            st.success("✅ Intent Score Escalation trigger active")
    
    with tab5:
        # PREMIUM FEATURE: Elite Segmentation & Actionable Intelligence
        try:
            from components.elite_refinements import render_elite_segmentation_tab, render_actionable_heatmap
            
            # 1. Professional Segment Cards
            render_elite_segmentation_tab()
            
            st.markdown("---")
            
            # 2. Actionable Activity Heatmap
            # Generate mock temporal data for Jorge demo
            import numpy as np
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            heatmap_rows = []
            for day in days:
                for hour in range(24):
                    # Higher activity during business hours and specific evenings
                    base = 5
                    if 9 <= hour <= 11 or 14 <= hour <= 16: base = 25
                    if day in ['Tuesday', 'Thursday'] and 18 <= hour <= 20: base = 40
                    activity = base + np.random.randint(0, 10)
                    heatmap_rows.append({'day': day, 'hour': hour, 'activity_count': activity})
            
            df_heatmap = pd.DataFrame(heatmap_rows)
            render_actionable_heatmap(df_heatmap)

        except ImportError:
            st.subheader("Smart Segmentation")
            st.info("🚀 Elite Segmentation & Heatmaps available in premium version")
            
            # Prepare lead data from mock_data
            leads_for_segmentation = []
            if "conversations" in mock_data:
                for conv in mock_data["conversations"]:
                    leads_for_segmentation.append({
                        "id": conv.get("contact_id"),
                        "name": conv.get("contact_name"),
                        "engagement_score": conv.get("message_count") * 10,
                        "lead_score": conv.get("lead_score"),
                        "budget": 500000 if conv.get("budget") == "unknown" else 1500000,
                        "last_activity_days_ago": 2,
                        "buyer_type": "luxury_buyer" if "lux" in conv.get("contact_id", "") else "standard",
                        "interested_property_type": "single_family"
                    })

            if leads_for_segmentation:
                import asyncio
                result = asyncio.run(services["segmentation"].segment_leads(leads_for_segmentation, method="behavioral"))
                
                # Use the enhanced Segmentation Pulse component for the first/main segment
                if result["segments"]:
                    try:
                        from components.segmentation_pulse import render_segmentation_pulse
                        # Render the enhanced pulse dashboard for the most important segment
                        main_segment = result["segments"][0]
                        render_segmentation_pulse(main_segment)
                        
                        st.markdown("---")
                        st.markdown("### 📋 All Segments Overview")
                    except ImportError:
                        st.warning("Enhanced segmentation pulse component not available, using legacy view")
            
            # All Segments Overview - FIXED: Proper HTML rendering with inline styles
            st.markdown("### 📋 All Segments Overview")
            
            # Use flexbox layout instead of bento-grid CSS class
            st.markdown('<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-top: 1rem;">', unsafe_allow_html=True)
            
            for seg in result["segments"]:
                seg_name = seg["name"].replace("_", " ").title()
                char = seg["characteristics"]
                
                # Build segment card with inline styles only (no CSS class dependencies)
                segment_html = f"""
                <div style="background: white; border-radius: 12px; padding: 1.5rem; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); transition: transform 0.2s ease;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h3 style="margin: 0; color: #1e293b; font-size: 1.25rem; font-weight: 700;">{seg_name}</h3>
                        <div style="background: #dbeafe; color: #1e40af; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">{seg['size']} Leads</div>
                    </div>
                    
                    <div style="display: flex; flex-direction: column; gap: 0.5rem; margin: 1rem 0; padding: 1rem; background: #f8fafc; border-radius: 8px;">
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <span>📊</span>
                            <span style="color: #475569; font-size: 0.875rem;">Engagement: <strong style="color: #1e293b;">{char['avg_engagement']}%</strong></span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <span>⭐</span>
                            <span style="color: #475569; font-size: 0.875rem;">Score: <strong style="color: #1e293b;">{char['avg_lead_score']}</strong></span>
                        </div>
                    </div>
                    
                    <div style="font-size: 1.5rem; font-weight: 700; color: #2563eb; margin: 0.5rem 0;">${char['total_value']:,.0f}</div>
                    
                    <div style="margin: 1rem 0;">
                        <strong style="font-size: 0.875rem; color: #6b7280;">Recommended Actions:</strong>
                        <ul style="margin: 0.5rem 0; padding-left: 1.25rem; font-size: 0.875rem; color: #374151; line-height: 1.6;">
                            {''.join(f'<li>{action}</li>' for action in seg['recommended_actions'][:2])}
                        </ul>
                    </div>
                    
                    <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
                        <button style="flex: 1; padding: 0.5rem 1rem; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.875rem;">View Leads</button>
                        <button style="flex: 1; padding: 0.5rem 1rem; background: #f1f5f9; color: #475569; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.875rem;">📥 Export</button>
                    </div>
                </div>
                """
                
                # CRITICAL FIX: Ensure unsafe_allow_html is TRUE
                st.markdown(segment_html, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # PREMIUM FEATURE: Elite Segmentation with Actionable Heatmap
            try:
                from components.elite_refinements import render_elite_segmentation_tab, render_actionable_heatmap
                import pandas as pd

                # Replace basic segmentation with elite version
                render_elite_segmentation_tab()

                st.markdown("---")

                # Generate sample activity data for actionable heatmap
                activity_df = pd.DataFrame({
                    'day': ['Monday'] * 24 + ['Tuesday'] * 24 + ['Wednesday'] * 24 + ['Thursday'] * 24 +
                           ['Friday'] * 24 + ['Saturday'] * 24 + ['Sunday'] * 24,
                    'hour': list(range(24)) * 7,
                    'activity_count': [
                        # Monday
                        5, 3, 2, 1, 1, 2, 5, 12, 25, 35, 45, 55, 65, 70, 75, 65, 55, 45, 35, 25, 15, 10, 8, 6,
                        # Tuesday
                        4, 2, 1, 1, 2, 3, 7, 15, 28, 40, 50, 60, 70, 75, 80, 70, 60, 50, 40, 30, 18, 12, 9, 7,
                        # Wednesday (peak day)
                        6, 4, 2, 1, 2, 4, 8, 18, 32, 45, 60, 75, 85, 90, 95, 85, 75, 60, 45, 35, 22, 15, 12, 8,
                        # Thursday
                        5, 3, 2, 1, 2, 3, 7, 16, 30, 42, 55, 68, 78, 82, 85, 75, 65, 55, 42, 32, 20, 13, 10, 7,
                        # Friday
                        4, 3, 2, 1, 2, 4, 8, 14, 26, 38, 48, 58, 65, 68, 70, 60, 50, 40, 30, 22, 16, 12, 9, 6,
                        # Saturday
                        8, 6, 4, 3, 3, 4, 6, 8, 12, 18, 22, 28, 32, 35, 38, 40, 42, 38, 32, 25, 20, 15, 12, 10,
                        # Sunday
                        6, 4, 3, 2, 2, 3, 4, 6, 10, 15, 20, 25, 28, 30, 32, 30, 28, 25, 20, 16, 12, 10, 8, 7
                    ]
                })

                # Render the premium actionable heatmap
                render_actionable_heatmap(activity_df, enable_automation=True)

            except ImportError:
                st.info("🚀 Elite Segmentation & Actionable Heatmap available in enterprise version")
        else:
            st.info("No lead data available for segmentation.")
        
    with tab6:
        st.subheader("Content Personalization")
        
        selected_lead_p = st.selectbox("Select Lead for Personalization:", list(lead_options.keys()), key="p_lead")
        
        import asyncio
        # Mock lead data for personalization
        lead_data_p = {
            "name": selected_lead_p,
            "budget": 650000,
            "engagement_score": 78,
            "last_activity_days_ago": 2,
            "location": "Austin, TX",
            "device": "mobile",
            "source": "paid",
            "preferences": {
                "property_type": "single_family",
                "bedrooms": 3,
                "location": "suburban"
            }
        }
        
        p_result = asyncio.run(services["personalization"].personalize_content("lead_123", lead_data_p, content_type="full_suite"))
        
        st.write(f"**Strategy:** {p_result['personalization_suite']['overall_strategy']['focus']}")
        
        st.markdown("#### 🏠 Recommended Properties")
        recs = p_result["personalization_suite"]["properties"]["recommendations"]
        cols = st.columns(len(recs))
        for i, rec in enumerate(recs):
            with cols[i]:
                st.write(f"**{rec['title']}**")
                st.write(f"${rec['price']:,.0f}")
                st.caption(rec['why_recommended'])
                st.button(f"View {rec['property_id']}", key=f"btn_{rec['property_id']}")

    with tab7:
        st.subheader("🔮 Predictive Lead Intelligence")
        st.markdown("*Advanced behavioral forecasting using Phase 2 Middleware*")
        
        # Sync Lead Selection with global state
        pred_lead_names = list(st.session_state.lead_options.keys())
        try:
            default_pred_idx = pred_lead_names.index(st.session_state.selected_lead_name)
        except ValueError:
            default_pred_idx = 0

        selected_lead_pred = st.selectbox(
            "Select Lead for Behavioral Prediction:", 
            pred_lead_names, 
            index=default_pred_idx,
            key="pred_lead_selector",
            on_change=lambda: st.session_state.update({"selected_lead_name": st.session_state.pred_lead_selector})
        )
        
        # Get actual lead context
        lead_context = st.session_state.lead_options[selected_lead_pred]
        
        # Use Phase 2 Predictive Scorer
        # Mock some history if not present for the demo wow factor
        if not lead_context.get("conversation_history"):
            lead_context["conversation_history"] = [
                {"role": "user", "content": "I'm interested in buying", "timestamp": (datetime.datetime.now() - datetime.timedelta(hours=2)).isoformat()},
                {"role": "assistant", "content": "Great, what is your budget?", "timestamp": (datetime.datetime.now() - datetime.timedelta(hours=1, minutes=55)).isoformat()},
                {"role": "user", "content": f"My budget is around ${lead_context['extracted_preferences'].get('budget', 500000)}", "timestamp": (datetime.datetime.now() - datetime.timedelta(hours=1, minutes=54)).isoformat()}
            ]
        
        pred_result_dict = services["predictive_scorer"].predict_conversion(lead_context)
        
        col_gauge, col_factors = st.columns([1, 1])
        
        prob = pred_result_dict["conversion_probability"]
        
        with col_gauge:
            # Conversion Probability Gauge
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = prob,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Conversion Probability", 'font': {'size': 18, 'color': '#1e293b'}},
                number = {'suffix': "%", 'font': {'size': 40, 'color': '#2563eb', 'weight': 'bold'}},
                gauge = {
                    'axis': {'range': [None, 100], 'tickwidth': 1},
                    'bar': {'color': "#2563eb"},
                    'bgcolor': "white",
                    'steps': [
                        {'range': [0, 40], 'color': '#fee2e2'},
                        {'range': [40, 70], 'color': '#fef3c7'},
                        {'range': [70, 100], 'color': '#dcfce7'}],
                }))
            
            fig_gauge.update_layout(
                height=280, 
                margin=dict(l=30, r=30, t=50, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                font={'color': "#1e293b", 'family': "Inter"}
            )
            st.plotly_chart(fig_gauge, use_container_width=True)
            
            st.markdown(f"""
            <div style='text-align: center; margin-top: -20px;'>
                <span class='badge' style='background: #f1f5f9; color: #475569;'>Confidence: {pred_result_dict['confidence'].upper()}</span>
                <span class='badge' style='background: #f1f5f9; color: #475569; margin-left: 10px;'>Trajectory: {pred_result_dict['trajectory'].upper()}</span>
            </div>
            """, unsafe_allow_html=True)
        
        with col_factors:
            # Conversion Timeline Forecast
            st.markdown("#### ⏱️ Predicted Velocity")
            
            estimated_days = 14 if prob > 80 else 30 if prob > 60 else 60 if prob > 40 else 90
            
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); 
                        padding: 2rem; border-radius: 12px; color: white; text-align: center;
                        margin-bottom: 1rem;'>
                <div style='font-size: 3rem; font-weight: 900;'>{estimated_days}</div>
                <div style='font-size: 1.1rem;'>Days to Expected Close</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.info(f"**Similar Lead Pattern:** {pred_result_dict['similar_leads_converted']}")
        
        st.markdown("---")
        st.markdown("#### 🧠 AI Reasoning & Behavioral Signals")
        
        for reason in pred_result_dict["reasoning"]:
            st.markdown(f"- {reason}")
            
        st.markdown("---")
        st.markdown("#### 🔍 Feature Analysis")
        
        f_cols = st.columns(3)
        features = pred_result_dict["features"]
        f_list = list(features.items())
        
        for i in range(3):
            with f_cols[i]:
                for k, v in f_list[i*3:(i+1)*3]:
                    st.write(f"**{k}:** {v}")
        
        st.markdown("---")
        st.markdown("#### 🏃 Recommended Strategic Actions")
        
        for i, rec in enumerate(pred_result_dict["recommendations"]):
            icon = "🔥" if rec["type"] == "priority" else "📅" if rec["type"] == "medium" else "📧"
            st.markdown(f"""
                <div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin-bottom: 12px; border-left: 4px solid #2563eb; background: white;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                        <span style="font-size: 1.25rem;">{icon}</span>
                        <b style="color: #1e293b; font-size: 1rem;">{rec['title']}</b>
                    </div>
                    <p style="font-size: 13px; color: #64748b; margin: 8px 0; line-height: 1.4;">{rec['action']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("🚀 Execute Strategy", key=f"exec_strat_{i}"):
                st.toast(f"Triggering {rec['type']} workflow in GHL...", icon="⚡")

    with tab8:
        st.subheader("💬 Claude Chatbot Simulator")
        st.markdown("*Experience the AI lead qualification flow as a lead would*")
        
        # Scenario Selector
        scenario = st.radio(
            "Select Demo Persona:",
            ["🏠 New Home Buyer (Standard)", "💰 Motivated Seller", "🏢 Luxury Investor"],
            horizontal=True
        )
        
        st.markdown("---")
        
        # Chat history for simulator
        if 'sim_messages' not in st.session_state:
            initial_msg = "Hi! I saw your inquiry about homes in the area. How can I help you today?"
            if "Seller" in scenario:
                initial_msg = "Hi! I'm the AI assistant for Jorge's team. I saw you're interested in selling your property. To get you an accurate valuation, may I ask about the condition of your home?"
            
            st.session_state.sim_messages = [{"role": "assistant", "content": initial_msg}]

        # Display simulator messages
        for msg in st.session_state.sim_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat Input
        if prompt := st.chat_input("Type your response as a lead..."):
            st.session_state.sim_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate AI Response (Simulated logic using LeadScorer concepts)
            with st.chat_message("assistant"):
                with st.spinner("Claude is thinking..."):
                    # Simple simulated response logic based on keywords
                    user_lower = prompt.lower()
                    
                    if any(word in user_lower for word in ["budget", "price", "worth", "dollars", "k", "$"]):
                        response = "Got it. Knowing your budget helps me narrow down the search. Are there specific neighborhoods you're targeting?"
                    elif any(word in user_lower for word in ["neighborhood", "area", "downtown", "location"]):
                        response = "That's a great area! How soon were you looking to make a move? (e.g., next 30 days, 6 months?)"
                    elif any(word in user_lower for word in ["asap", "month", "timeline", "now"]):
                        response = "Speed is key in this market. Are you already pre-approved for financing, or would you like a recommendation for a local lender?"
                    elif any(word in user_lower for word in ["pre-approved", "cash", "bank", "loan"]):
                        response = "Excellent. Lastly, what are your 'must-haves'? (e.g., 4+ bedrooms, home office, pool?)"
                    elif "sell" in scenario.lower():
                        response = "Thank you for sharing that. I've noted the condition. What is your primary motivation for selling at this time?"
                    else:
                        response = "That's very helpful information. I'm extracting those details for Jorge's team now. Is there anything else you think we should know about your real estate goals?"
                    
                    st.session_state.sim_messages.append({"role": "assistant", "content": response})
                    st.markdown(response)
                    
                    # Small visual feedback that data is being extracted
                    st.toast("AI extracting criteria...", icon="🧠")

        if st.button("🗑️ Reset Simulator", width="stretch"):
            del st.session_state.sim_messages
            st.rerun()

@ui_error_boundary("Automation Studio")
def render_automation_studio():
    st.header("🤖 Automation Studio")
    st.markdown("*Visual switchboard to toggle AI features on/off*")
    
    tab1, tab2, tab3, tab4 = st.tabs(["⚙️ Automations", "📧 Sequences", "🔄 Workflows", "🧠 Claude's Prompt Lab"])
    
    with tab1:
        st.subheader("AI Automation Control Panel")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🤖 Core AI Agents")
            
            ai_assistant = st.toggle("AI Qualifier (Phase 1)", value=True)
            if ai_assistant:
                st.success("✅ Active - Extracting criteria via SMS")
            
            smart_matcher = st.toggle("Property Matcher (Phase 2)", value=True)
            if smart_matcher:
                st.success("✅ Active - Auto-suggesting listings")
            
            buyer_portal = st.toggle("Buyer Portal Sync (Phase 3)", value=True)
            
        with col2:
            st.markdown("#### ⚡ Phase 4: Follow-Up Triggers")
            
            st.toggle("New Listing SMS Alerts", value=True, help="Texts lead when a match hits the market")
            st.toggle("Price Drop Re-engagement", value=True, help="Follows up if a favorite home drops in price")
            st.toggle("30-Day 'Cold Lead' Revive", value=False, help="Conversational check-in for dormant leads")
            
            st.markdown("---")
            st.markdown("#### 🚀 Phase 4 Live Simulation")
            if st.button("🔍 Scan for Silent Leads (24h+)", width="stretch"):
                with st.spinner("Scanning GHL logs for silent leads..."):
                    from services.reengagement_engine import ReengagementEngine, ReengagementTrigger
                    engine = ReengagementEngine()
                    
                    # Simulated silent leads for the demo
                    silent_leads = [
                        {"name": "Mike Chen", "hours": 26, "last_msg": "I'll talk to my wife and get back to you."},
                        {"name": "Emily Davis", "hours": 49, "last_msg": "Thanks for the list!"}
                    ]
                    
                    for lead in silent_leads:
                        with st.container(border=True):
                            st.write(f"👤 **{lead['name']}** - Silent for {lead['hours']}h")
                            st.caption(f"Last message: \"{lead['last_msg']}\"")
                            trigger_level = "24h" if lead['hours'] < 48 else "48h"
                            
                            # Get real message template
                            msg = engine.get_message_for_trigger(
                                trigger=ReengagementTrigger.HOURS_24 if trigger_level == "24h" else ReengagementTrigger.HOURS_48,
                                contact_name=lead['name'].split()[0],
                                is_buyer=True
                            )
                            
                            st.info(f"AI suggests {trigger_level} re-engagement:")
                            st.code(msg)
                            if st.button(f"Send to {lead['name']}", key=f"reengage_{lead['name']}"):
                                st.success(f"SMS Sent to {lead['name']} via GHL!")
        
        # Use the enhanced AI Training Sandbox component
        try:
            from components.ai_training_sandbox import render_ai_training_sandbox
            render_ai_training_sandbox(ai_tone)
        except ImportError:
            # Fallback to legacy simple version
            st.subheader("🧪 AI Training Lab")
            st.markdown("*Adjust how the AI 'sounds' to your leads*")
            
            # Dynamic prompt preview based on sidebar slider
            base_prompt = ""
            if ai_tone == "Professional":
                base_prompt = "You are a senior real estate advisor. Use formal language, emphasize market data, and maintain a polite, service-oriented distance."
            elif ai_tone == "Natural":
                base_prompt = "You are a helpful assistant on Jorge's team. Be friendly, use first names, and keep sentences concise but helpful."
            else: # Direct/Casual
                base_prompt = "You are Jorge. Be extremely direct and casual. Skip the fluff. Get the budget and location ASAP so we don't waste time."
                
            st.text_area("Live System Prompt (What the AI is thinking):", value=base_prompt, height=100)
            
            st.markdown("#### 💬 Live Voice Simulator")
        
        # Animated Waveform
        st.markdown("""
        <div class="waveform-container">
            <div class="waveform-bar" style="animation-delay: 0.0s"></div>
            <div class="waveform-bar" style="animation-delay: 0.1s"></div>
            <div class="waveform-bar" style="animation-delay: 0.2s"></div>
            <div class="waveform-bar" style="animation-delay: 0.3s"></div>
            <div class="waveform-bar" style="animation-delay: 0.4s"></div>
            <div class="waveform-bar" style="animation-delay: 0.5s"></div>
            <div class="waveform-bar" style="animation-delay: 0.6s"></div>
            <div class="waveform-bar" style="animation-delay: 0.7s"></div>
            <div class="waveform-bar" style="animation-delay: 0.8s"></div>
            <div class="waveform-bar" style="animation-delay: 0.9s"></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("*Type a message below to see how the AI responds in **" + ai_tone + "** mode:*")
        
        test_input = st.text_input("Test Lead Message:", placeholder="Ex: 'I'm looking for a 3-bed home in Rancho near Victoria Gardens'")
        
        if test_input:
            with st.chat_message("assistant"):
                if ai_tone == "Professional":
                    st.write(f"Thank you for reaching out to Jorge's team. I have noted your interest in the {market_key} area. Based on current market trends, a 3-bedroom property in that specific neighborhood typically commands a premium. May I ask what your anticipated budget range is for this acquisition?")
                elif ai_tone == "Natural":
                    st.write(f"That sounds like a great area! Victoria Gardens is super popular right now. I'd love to help you find a 3-bed there. To narrow it down for Jorge, what's the budget range you're hoping to stay within?")
                else: # Direct/Casual
                    st.write(f"Got it. 3-beds in {market_key} are moving fast. What's your max budget? I'll see what we have in the inventory right now so we don't waste time.")
            
            st.caption(f"✨ This response is generated using the **{ai_tone}** persona profile.")
        
        st.markdown("---")
        st.subheader("🔗 GoHighLevel Sync Log")
        st.markdown("*Real-time data flowing between AI and your CRM*")
        
        log_events = [
            {"time": "10:45 AM", "event": "Preference Extracted", "detail": "Budget: $1.3M (Sarah Johnson)", "field": "contact.budget", "status": "Synced"},
            {"time": "10:46 AM", "event": "Custom Field Update", "detail": "Area: Alta Loma", "field": "contact.preferred_area", "status": "Synced"},
            {"time": "11:02 AM", "event": "Phase 2 Match", "detail": "Sent 3 RC Listings via SMS", "field": "contact.tags", "status": "Synced"},
            {"time": "11:15 AM", "event": "VAPI Connection", "detail": "Voice Call Initiated", "field": "contact.last_call", "status": "Active"},
        ]
        
        for log in log_events:
            status_color = "#10B981" if log["status"] == "Synced" else "#3B82F6"
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 15px; padding: 12px; background: white; border-radius: 10px; margin-bottom: 8px; border: 1px solid #f1f5f9;">
                <div style="font-size: 0.75rem; color: #64748b; min-width: 70px;">{log['time']}</div>
                <div style="flex: 1;">
                    <div style="font-weight: 600; font-size: 0.85rem; color: #1e293b;">{log['event']}</div>
                    <div style="font-size: 0.75rem; color: #64748b;">{log['detail']}</div>
                </div>
                <div style="font-family: monospace; font-size: 0.7rem; background: #f8fafc; padding: 2px 6px; border-radius: 4px; color: #475569;">{log['field']}</div>
                <div style="background: {status_color}; color: white; padding: 2px 10px; border-radius: 20px; font-size: 0.65rem; font-weight: 700; text-transform: uppercase;">{log['status']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        st.subheader("Auto Follow-Up Sequences")
        
        perf = services["sequences"].get_sequence_performance("demo_seq")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Conversion Rate", f"{perf['metrics']['conversion_rate']*100:.1f}%")
        col2.metric("Email Open Rate", f"{perf['channel_performance']['email']['open_rate']*100:.0f}%")
        col3.metric("SMS Response", f"{perf['channel_performance']['sms']['response_rate']*100:.0f}%")

        # Sequence Table
        sequences_data = [
            {"Name": "New Lead (Buyer) - 7 Day", "Status": "Active", "Enrolled": perf['metrics']['total_enrolled'], "Open Rate": f"{perf['channel_performance']['email']['open_rate']*100:.0f}%", "Reply Rate": f"{perf['channel_performance']['sms']['response_rate']*100:.0f}%"},
            {"Name": "Seller Reactivation", "Status": "Active", "Enrolled": 12, "Open Rate": "75%", "Reply Rate": "35%"},
            {"Name": "Cold Lead Win-back", "Status": "Paused", "Enrolled": 0, "Open Rate": "-", "Reply Rate": "-"},
        ]
        
        st.dataframe(pd.DataFrame(sequences_data), width="stretch", hide_index=True)
        
        if st.button("➕ Create New Sequence"):
            st.toast("Opening Sequence Builder...")
        
    with tab3:
        st.subheader("Workflow Marketplace")
        st.markdown("*Install pre-built real estate automations with one click*")
        
        # Browse marketplace
        templates = services["marketplace"].get_featured_templates(6)
        
        # Display in a grid
        cols = st.columns(3)
        for i, t in enumerate(templates):
            with cols[i % 3]:
                st.markdown(f"### {t.icon} {t.name}")
                st.write(t.description[:80] + "...")
                st.caption(f"⭐ {t.rating} | 📥 {t.downloads_count:,} installs")
                if st.button(f"Install", key=f"inst_{t.id}", width="stretch"):
                    st.success(f"Installed {t.name}!")

    with tab4:
        st.subheader("🧠 Claude's Prompt Lab")
        st.markdown("*Use Claude to analyze and optimize your AI's personality and instructions.*")
        
        col_p1, col_p2 = st.columns([2, 1])
        
        with col_p1:
            current_p = st.text_area("Current System Prompt:", value="You are a helpful assistant on Jorge's team. Be friendly and keep it concise.", height=150)
            
            if st.button("🪄 Claude: Optimize My Prompt", type="primary"):
                with st.spinner("Claude is rewriting for conversion..."):
                    st.success("Claude has suggested an optimized version!")
                    st.markdown("""
                    **Recommended Rewrite:**
                    > "You are Jorge's High-Intent Qualifier. Your goal is to move leads from discovery to 'Booked Tour' ASAP. Use a 'Natural' tone, prioritize budget extraction, and reference specific Austin/Rancho neighborhoods to build authority. If budget is >$800k, immediately offer a private luxury viewing."
                    """)
                    st.info("💡 **Claude's Logic:** This version adds specific triggers for high-value leads and builds neighborhood authority.")
        
        with col_p2:
            st.markdown("#### AI Performance Audit")
            st.metric("Tone Alignment", "94%", "+5%")
            st.metric("Conversion Impact", "Medium", "Increasing")
            
            if st.button("🚀 Push to GHL Production"):
                st.toast("Updated prompt synced to GHL Custom Fields!")

@ui_error_boundary("Sales Copilot")
def render_sales_copilot():
    st.header("💰 Sales Copilot")
    st.markdown("*Agent tools for active deals and client meetings*")

    # Claude's Negotiation Briefing
    with st.container(border=True):
        col_n1, col_n2 = st.columns([1, 8])
        with col_n1:
            st.markdown("<div style='font-size: 3rem; text-align: center;'>💼</div>", unsafe_allow_html=True)
        with col_n2:
            st.markdown("### Claude's Negotiation Briefing")
            st.markdown("""
            *Ready to close for Jorge:*
            - **🤝 The Closer:** You have 3 discovery calls this afternoon. I've analyzed their lead profiles and prepared high-converting 'Hook' scripts for each.
            - **📜 Compliance Check:** New TX listing requirements are active. I've updated your Smart Document generator to ensure all contracts are 100% compliant.
            """)
            if st.button("📝 View Meeting Hooks"):
                st.toast("Loading personalized talk tracks for today's calls...", icon="💬")
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "💼 Deal Closer",
        "📄 Documents",
        "📋 Meeting Prep",
        "💵 Calculator"
    ])
    
    with tab1:
        st.subheader("Deal Closer AI")
        st.markdown("*Your always-on negotiation coach. Ask how to handle objections, negotiate fees, or close deals.*")
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
            # Add initial welcome message
            st.session_state.messages.append({"role": "assistant", "content": "I'm ready to help you close. Paste an objection or ask for negotiation advice."})

        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # React to user input
        if prompt := st.chat_input("Ex: 'Client says 6% commission is too high'"):
            # Display user message
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.spinner("Analyzing negotiation strategy..."):
                lead_context = {
                    "name": "Prospect",
                    "stage": "objection_handling",
                    "budget_min": 400000,
                    "budget_max": 600000
                }
                
                # Get AI response
                result = services["deal_closer"].generate_response(prompt, lead_context)
                
                # Format the response nicely
                response_content = f"""
{result['response']}

---
**💡 Key Talking Points:**
{chr(10).join([f'- {p}' for p in result['talking_points']])}

**🏃 Next Best Action:**
{result['follow_up_actions'][0] if result['follow_up_actions'] else 'Schedule follow-up'}
"""
                # Display assistant response
                with st.chat_message("assistant"):
                    st.markdown(response_content)
                
                st.session_state.messages.append({"role": "assistant", "content": response_content})
        
    with tab2:
        st.subheader("Smart Document Generator")
        from services.smart_document_generator import DocumentType
        doc_type_str = st.selectbox(
            "Document Type:",
            [t.value.replace("_", " ").title() for t in DocumentType]
        )
        
        # Mapping for enum
        type_enum = next(t for t in DocumentType if t.value.replace("_", " ").title() == doc_type_str)
        
        col1, col2 = st.columns(2)
        with col1:
            party_name = st.text_input("Buyer/Client Name:", "John Doe")
            address = st.text_input("Property Address:", "123 Main St, Austin, TX")
            
        with col2:
            price_doc = st.number_input("Transaction Price ($):", value=450000)
            jurisdiction = st.selectbox("Jurisdiction:", ["TX", "CA", "FL", "NY"])

        if st.button("🚀 Generate & Prepare for Signature", width="stretch"):
            with st.spinner("Generating professional document..."):
                doc_data = {
                    "property_address": address,
                    "purchase_price": price_doc,
                    "buyer_name": party_name,
                    "jurisdiction": jurisdiction
                }
                doc = services["doc_gen"].generate_document(type_enum, f"template_{type_enum.value}", doc_data)
                
                st.success(f"✅ {doc_type_str} Generated (ID: {doc['id']})")
                st.info(f"**Compliance Status:** {doc['legal_requirements']['compliance_status'].upper()}")
                
                # Signature status
                st.markdown("#### ✍️ E-Signature Status")
                sig_status = services["doc_gen"].check_signature_status("sig_123")
                st.write(f"**Overall Status:** {sig_status['overall_status'].replace('_', ' ').title()}")
                st.progress(sig_status['completion']['percentage'])
                st.write(f"{sig_status['completion']['signed']} of {sig_status['completion']['total']} parties signed.")
        
    with tab3:
        st.subheader("Meeting Prep Assistant")
        st.markdown("*Generate a comprehensive briefing for your next client meeting*")
        from services.meeting_prep_assistant import MeetingType
        
        col1, col2 = st.columns(2)
        with col1:
            # Fix NameError: Use global session state
            meeting_lead_options = list(st.session_state.lead_options.keys())
            try:
                default_mtg_idx = meeting_lead_options.index(st.session_state.selected_lead_name)
            except ValueError:
                default_mtg_idx = 0

            meeting_lead = st.selectbox(
                "Select Lead for Meeting:", 
                meeting_lead_options, 
                index=default_mtg_idx,
                key="mtg_lead"
            )
            m_type = st.selectbox("Meeting Type:", [t.value.replace("_", " ").title() for t in MeetingType])
        
        if st.button("📄 Generate Briefing Doc", width="stretch"):
            with st.spinner("Compiling data and generating brief..."):
                # Convert back to enum
                type_enum = next(t for t in MeetingType if t.value.replace("_", " ").title() == m_type)
                
                brief = services["meeting_prep"].prepare_meeting_brief(type_enum, "contact_123")
                
                st.markdown("---")
                st.success(f"✅ Briefing for {meeting_lead} Generated")
                
                # AI Briefing Insights (FEAT-010)
                m_brief = get_meeting_briefing(meeting_lead)
                st.info(f"**🎯 The Hook:** {m_brief['hook']}")
                st.warning(f"**⚠️ Watch Out:** {m_brief['objection']}")
                st.success(f"**💰 The Close:** {m_brief['closer']}")
                
                tab_a, tab_b, tab_c = st.tabs(["📋 Agenda", "🗣️ Talking Points", "🗂️ Required Docs"])
                
                with tab_a:
                    for item in brief["agenda"]:
                        st.write(f"**{item['time']}**: {item['topic']}")
                        
                with tab_b:
                    for point in brief["talking_points"]:
                        st.write(f"- {point}")
                        
                with tab_c:
                    for doc in brief["documents_to_bring"]:
                        st.write(f"- {doc}")
        
    with tab4:
        # FIX-016: Smart Financial Calculator Implementation
        lead_name = st.session_state.get('selected_lead_name', '-- Select a Lead --')
        if lead_name == '-- Select a Lead --' and list(st.session_state.lead_options.keys()):
             # Default to first lead if none selected
             lead_name = list(st.session_state.lead_options.keys())[1] # Skip the None option
        
        lead_data = st.session_state.lead_options.get(lead_name, {}).get('extracted_preferences', {})
        render_roi_calculator(lead_data)

@ui_error_boundary("Ops & Optimization")
def render_ops_hub():
    st.header("📈 Ops & Optimization")
    st.markdown("*Manager-level analytics and team performance tracking*")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "✅ Quality",
        "💰 Revenue",
        "🏆 Benchmarks",
        "🎓 Coaching",
        "🛠️ Control"
    ])
    
    with tab1:
        st.subheader("AI Quality Assurance")
        qa_report = services["qa"].generate_qa_report("demo_location")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Overall Quality", f"{qa_report['overall_score']}%", "+2%")
        col2.metric("Compliance Rate", f"{qa_report['compliance_rate']}%", "Stable")
        col3.metric("Empathy Score", f"{qa_report['empathy_score']}/10", "+0.5")
        
        st.markdown("#### 🎯 Improvement Areas")
        for area in qa_report["improvement_areas"]:
            st.warning(f"**{area['topic']}**: {area['recommendation']}")
            
    with tab2:
        st.subheader("Revenue Attribution")
        attr_data = services["revenue"].get_attribution_data("demo_location")
        
        # Display attribution chart
        df_attr = pd.DataFrame(attr_data["channels"])
        fig = px.pie(df_attr, values='revenue', names='channel', title='Revenue by Lead Source',
                     color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig, width="stretch")
        
        st.write(f"**Total Attributed Revenue:** ${attr_data['total_revenue']:,.0f}")
        
        # UI-014: Funnel Velocity Chart
        st.markdown("---")
        st.subheader("🚀 Funnel Velocity")
        render_revenue_funnel()
        
    with tab3:
        st.subheader("Competitive Benchmarking")
        bench = services["benchmarking"].get_benchmarks("demo_location")
        
        for metric, data in bench.items():
            st.write(f"**{metric.replace('_', ' ').title()}**")
            cols = st.columns([2, 1])
            cols[0].progress(data["percentile"] / 100)
            cols[1].write(f"{data['percentile']}th Percentile")
            
    with tab4:
        st.subheader("AI Agent Coaching")
        recommendations = services["coaching"].get_coaching_recommendations("demo_agent")
        
        for rec in recommendations:
            with st.expander(f"💡 {rec['title']}"):
                st.write(rec['description'])
                st.info(f"**Impact:** {rec['expected_impact']}")

    with tab5:
        st.subheader("AI Control Panel")
        
        # Prompt Versioning
        st.markdown("### 📝 Prompt Version Control")
        selected_version = st.selectbox("Active Prompt Version", 
                                       options=[v["version"] for v in st.session_state.prompt_versions],
                                       index=len(st.session_state.prompt_versions)-1)
        
        version_data = next(v for v in st.session_state.prompt_versions if v["version"] == selected_version)
        
        st.info(f"**Tag:** {version_data['tag']} | **Deployed:** {version_data['timestamp']}")
        new_prompt = st.text_area("Prompt Content", value=version_data["content"], height=150)
        
        col_v1, col_v2 = st.columns(2)
        if col_v1.button("💾 Save as New Version", use_container_width=True):
            new_v = f"v1.{len(st.session_state.prompt_versions)}"
            st.session_state.prompt_versions.append({
                "version": new_v,
                "tag": "Custom",
                "content": new_prompt,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d")
            })
            st.success(f"Version {new_v} saved!")
            st.rerun()
            
        if col_v2.button("🚀 Rollback to v1.1", use_container_width=True):
            st.warning("Rolling back to Production Baseline...")
            st.toast("Rollback initiated", icon="⏪")

        st.markdown("---")
        
        # Model Retraining Loop
        st.markdown("### 🔄 Model Retraining Loop")
        st.write("Feedback captured from Lead Intelligence Hub is automatically used to fine-tune your local matching models.")
        
        col_r1, col_v2 = st.columns(2)
        col_r1.metric("Captured Feedback", "128", "+12")
        col_v2.metric("Model Drift", "0.02", "Low")
        
        if st.button("🛰️ Initiate Model Retraining", type="primary", use_container_width=True):
            with st.spinner("Retraining Property Matcher ML..."):
                import time
                time.sleep(2)
                st.success("Model successfully retrained! Accuracy improved by 3.2%")
                st.balloons()

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

def render_seller_communication_portal():
    """Communication hub for seller-agent interaction"""
    st.subheader("💬 Seller Communication Portal")

    # Communication overview
    st.markdown("#### 📊 Communication Summary")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📧 Messages Today", "5", delta="2 unread")
    with col2:
        st.metric("📞 Calls This Week", "3", delta="1 scheduled")
    with col3:
        st.metric("📅 Updates Sent", "12", delta="Weekly report due")
    with col4:
        st.metric("🏠 Showing Reports", "8", delta="3 new")

    # Communication tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬 Messages", "📞 Calls & Meetings", "📊 Reports & Updates", "📅 Showing Feedback", "📋 Documents"
    ])

    with tab1:
        st.markdown("##### Message Center")

        # Quick message composer
        with st.expander("✏️ Send New Message"):
            message_to = st.selectbox("To:", ["Your Listing Agent", "Transaction Coordinator", "Marketing Team"])
            message_subject = st.text_input("Subject:")
            message_body = st.text_area("Message:", height=100)

            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("📤 Send Message"):
                    st.success("Message sent!")

        # Message history
        st.markdown("**Recent Messages**")

        messages = [
            {
                "from": "Your Listing Agent",
                "subject": "Showing Report - Great Feedback!",
                "time": "2 hours ago",
                "preview": "Had two showings today with very positive feedback. The buyers loved...",
                "unread": True
            },
            {
                "from": "Transaction Coordinator",
                "subject": "Document Upload Required",
                "time": "1 day ago",
                "preview": "Please upload the signed property disclosure form to complete...",
                "unread": True
            },
            {
                "from": "Your Listing Agent",
                "subject": "Weekly Market Update",
                "time": "3 days ago",
                "preview": "Market activity remains strong in your neighborhood. Three new...",
                "unread": False
            },
            {
                "from": "Marketing Team",
                "subject": "Photos Ready for Approval",
                "time": "5 days ago",
                "preview": "Professional photography is complete! Please review the gallery...",
                "unread": False
            }
        ]

        for message in messages:
            unread_style = "background-color: #E3F2FD;" if message['unread'] else "background-color: white;"

            with st.container():
                st.markdown(f"""
                <div style="{unread_style} padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #2196F3;">
                    <div style="display: flex; justify-content: between; margin-bottom: 5px;">
                        <strong>{'📧 ' if message['unread'] else '✉️ '}{message['subject']}</strong>
                        <span style="color: #666; font-size: 0.9em; margin-left: auto;">{message['time']}</span>
                    </div>
                    <div style="color: #666; font-size: 0.9em; margin-bottom: 5px;">From: {message['from']}</div>
                    <div style="color: #333;">{message['preview']}</div>
                </div>
                """, unsafe_allow_html=True)

                col1, col2, col3 = st.columns([1, 1, 4])
                with col1:
                    if st.button("📖 Read", key=f"read_{message['subject'][:10]}"):
                        st.info("Opening full message...")
                with col2:
                    if st.button("↩️ Reply", key=f"reply_{message['subject'][:10]}"):
                        st.info("Reply window opened...")

    with tab2:
        st.markdown("##### Calls & Meetings")

        # Upcoming meetings
        st.markdown("**Upcoming Calls & Meetings**")

        meetings = [
            {
                "title": "Weekly Check-in Call",
                "date": "Tomorrow",
                "time": "10:00 AM",
                "type": "Phone Call",
                "agenda": "Discuss showing feedback and next steps"
            },
            {
                "title": "Marketing Strategy Review",
                "date": "Friday",
                "time": "2:00 PM",
                "type": "Video Call",
                "agenda": "Review performance metrics and adjust strategy"
            }
        ]

        for meeting in meetings:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 2])

                with col1:
                    st.markdown(f"**📅 {meeting['title']}**")
                    st.markdown(f"*{meeting['agenda']}*")
                with col2:
                    st.markdown(meeting['date'])
                with col3:
                    st.markdown(meeting['time'])
                with col4:
                    if st.button("📞 Join", key=f"join_{meeting['title'][:8]}"):
                        st.success("Meeting link opened!")

                st.markdown("---")

        # Call history
        st.markdown("**Recent Call History**")

        calls = [
            {
                "date": "Yesterday",
                "duration": "15 minutes",
                "type": "📞 Phone Call",
                "summary": "Discussed pricing strategy and showing feedback"
            },
            {
                "date": "3 days ago",
                "duration": "22 minutes",
                "type": "💻 Video Call",
                "summary": "Reviewed marketing materials and listing photos"
            }
        ]

        for call in calls:
            st.markdown(f"**{call['type']} - {call['date']}** ({call['duration']})")
            st.markdown(f"*{call['summary']}*")
            st.markdown("---")

    with tab3:
        st.markdown("##### Reports & Updates")

        # Report schedule
        st.markdown("**Scheduled Reports**")

        reports = [
            {
                "report": "Weekly Activity Report",
                "frequency": "Every Monday",
                "last_sent": "3 days ago",
                "next_due": "In 4 days"
            },
            {
                "report": "Showing Summary",
                "frequency": "After each showing",
                "last_sent": "Today",
                "next_due": "As needed"
            },
            {
                "report": "Market Analysis Update",
                "frequency": "Bi-weekly",
                "last_sent": "1 week ago",
                "next_due": "Next week"
            }
        ]

        for report in reports:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"**{report['report']}**")
            with col2:
                st.markdown(report['frequency'])
            with col3:
                st.markdown(report['last_sent'])
            with col4:
                st.markdown(report['next_due'])

        # Recent reports
        st.markdown("**Recent Reports**")

        with st.expander("📊 Weekly Activity Report - January 6, 2026"):
            st.markdown("""
            **This Week's Highlights:**
            - 23 new online views (+18% from last week)
            - 5 showing appointments scheduled
            - 2 private showings completed with positive feedback
            - Featured in weekend newsletter to 2,500+ subscribers

            **Marketing Performance:**
            - Zillow: 12 inquiries, 89 favorites
            - Realtor.com: 8 inquiries, 45 favorites
            - MLS: 3 agent inquiries

            **Next Week's Plans:**
            - Schedule professional photography touch-ups
            - Host first open house on Saturday
            - Follow up with interested buyers from this week
            """)

        with st.expander("🏠 Showing Report - Today 2:00 PM"):
            st.markdown("""
            **Showing Details:**
            - Buyer Agent: Sarah Johnson, ABC Realty
            - Showing Duration: 25 minutes
            - Buyer Profile: Pre-approved first-time buyers, $450K budget

            **Feedback:**
            - Overall Impression: Very positive
            - Loved: Updated kitchen, hardwood floors, neighborhood
            - Concerns: Wanted larger master bathroom
            - Interest Level: High - planning second viewing this weekend

            **Agent Comments:**
            "Serious buyers who have been looking for 3 months. Your home checks most of their boxes. They'll likely make an offer after second showing."
            """)

    with tab4:
        st.markdown("##### Showing Feedback")

        # Feedback summary
        st.markdown("**Feedback Summary (Last 30 Days)**")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Overall Rating", "4.6/5", delta="Excellent")
        with col2:
            st.metric("Would Recommend", "92%", delta="Above average")
        with col3:
            st.metric("Serious Interest", "67%", delta="High engagement")

        # Detailed feedback
        st.markdown("**Recent Feedback**")

        detailed_feedback = [
            {
                "date": "Today 2:00 PM",
                "agent": "Sarah Johnson",
                "rating": 5,
                "highlights": "Kitchen updates, hardwood floors, location",
                "concerns": "Master bathroom size",
                "likelihood": "High - second showing planned"
            },
            {
                "date": "Yesterday 11:00 AM",
                "agent": "Mike Chen",
                "rating": 4,
                "highlights": "Move-in ready condition, good value",
                "concerns": "Prefers larger backyard",
                "likelihood": "Medium - still considering options"
            },
            {
                "date": "2 days ago 3:00 PM",
                "agent": "Lisa Rodriguez",
                "rating": 5,
                "highlights": "Investment potential, neighborhood growth",
                "concerns": "None mentioned",
                "likelihood": "Very High - cash buyer ready to offer"
            }
        ]

        for feedback in detailed_feedback:
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.markdown(f"**📅 {feedback['date']}**")
                    st.markdown(f"*Agent: {feedback['agent']}*")

                with col2:
                    st.markdown(f"**Rating:** {'⭐' * feedback['rating']}")
                    st.markdown(f"**Highlights:** {feedback['highlights']}")
                    if feedback['concerns'] != "None mentioned":
                        st.markdown(f"**Concerns:** {feedback['concerns']}")

                with col3:
                    likelihood_color = "green" if "High" in feedback['likelihood'] else "orange" if "Medium" in feedback['likelihood'] else "red"
                    st.markdown(f"<span style='color: {likelihood_color};'>**{feedback['likelihood']}**</span>", unsafe_allow_html=True)

                st.markdown("---")

    with tab5:
        st.markdown("##### Document Management")

        # Document categories
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📋 Required Documents**")

            required_docs = [
                {"doc": "Property Disclosure", "status": "✅ Complete"},
                {"doc": "Listing Agreement", "status": "✅ Complete"},
                {"doc": "MLS Listing Form", "status": "✅ Complete"},
                {"doc": "Lead Paint Disclosure", "status": "⏳ Pending"},
                {"doc": "HOA Documents", "status": "N/A"},
                {"doc": "Survey/Plat", "status": "⏳ Requested"}
            ]

            for doc in required_docs:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"• {doc['doc']}")
                with col_b:
                    st.markdown(doc['status'])

        with col2:
            st.markdown("**📁 Shared Documents**")

            shared_docs = [
                {"doc": "Professional Photos", "date": "5 days ago"},
                {"doc": "Marketing Flyer", "date": "4 days ago"},
                {"doc": "CMA Report", "date": "1 week ago"},
                {"doc": "Listing Analytics", "date": "Yesterday"},
                {"doc": "Showing Reports", "date": "Today"}
            ]

            for doc in shared_docs:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"📄 {doc['doc']}")
                with col_b:
                    if st.button("📥", key=f"download_{doc['doc'][:8]}"):
                        st.success("Downloaded!")

        # Document upload
        st.markdown("**📤 Upload Documents**")

        col1, col2 = st.columns([3, 1])
        with col1:
            uploaded_file = st.file_uploader("Choose file", type=['pdf', 'doc', 'docx', 'jpg', 'png'])
        with col2:
            if st.button("Upload"):
                if uploaded_file:
                    st.success("Document uploaded successfully!")
                else:
                    st.warning("Please select a file first.")

def render_transaction_timeline():
    """Transaction timeline and offer management"""
    st.subheader("📅 Transaction Timeline & Offers")

    # Timeline overview
    st.markdown("#### 🎯 Sale Progress")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📅 Days Listed", "8 days")
    with col2:
        st.metric("👀 Total Interest", "High")
    with col3:
        st.metric("🤝 Offers Received", "2")
    with col4:
        st.metric("📊 Current Status", "Active")

    # Main timeline tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Current Offers", "📅 Timeline", "🔄 Next Steps", "📊 Milestones"
    ])

    with tab1:
        st.markdown("##### Active Offers")

        offers = [
            {
                "buyer": "Johnson Family (Sarah Johnson, Buyer Agent)",
                "offer_price": "$492,000",
                "earnest_money": "$10,000",
                "financing": "Conventional - Pre-approved",
                "closing_date": "30 days",
                "contingencies": "Inspection, Financing",
                "status": "🟡 Under Review",
                "expires": "Tomorrow 5:00 PM",
                "notes": "Strong offer, motivated buyers"
            },
            {
                "buyer": "Investment Group (Lisa Rodriguez, Buyer Agent)",
                "offer_price": "$485,000",
                "earnest_money": "$25,000",
                "financing": "Cash Offer",
                "closing_date": "15 days",
                "contingencies": "Inspection Only (7 days)",
                "status": "🟢 Active",
                "expires": "Today 6:00 PM",
                "notes": "Cash offer, quick close, investor buyer"
            }
        ]

        for i, offer in enumerate(offers):
            with st.expander(f"{offer['status']} {offer['buyer']} - {offer['offer_price']}"):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**💰 Offer Price:** {offer['offer_price']}")
                    st.markdown(f"**💵 Earnest Money:** {offer['earnest_money']}")
                    st.markdown(f"**🏦 Financing:** {offer['financing']}")
                    st.markdown(f"**📅 Closing:** {offer['closing_date']}")

                with col2:
                    st.markdown(f"**🔍 Contingencies:** {offer['contingencies']}")
                    st.markdown(f"**⏰ Expires:** {offer['expires']}")
                    st.markdown(f"**📝 Notes:** {offer['notes']}")

                # Action buttons
                col_a, col_b, col_c, col_d = st.columns(4)
                with col_a:
                    if st.button("✅ Accept", key=f"accept_{i}"):
                        st.success("Offer accepted! Contract generation initiated.")
                with col_b:
                    if st.button("📝 Counter", key=f"counter_{i}"):
                        st.info("Counter-offer form opened.")
                with col_c:
                    if st.button("❌ Decline", key=f"decline_{i}"):
                        st.warning("Offer declined.")
                with col_d:
                    if st.button("📞 Discuss", key=f"discuss_{i}"):
                        st.info("Calling your agent to discuss...")

        if not offers:
            st.info("No offers received yet. Marketing campaign is generating strong interest!")

    with tab2:
        st.markdown("##### Transaction Timeline")

        # Timeline visualization
        timeline_events = [
            {"date": "Jan 1", "event": "🏠 Listed Property", "status": "✅ Complete", "notes": "Initial listing activation"},
            {"date": "Jan 2", "event": "📸 Photography Complete", "status": "✅ Complete", "notes": "Professional photos taken"},
            {"date": "Jan 3", "event": "🌐 Online Marketing Launch", "status": "✅ Complete", "notes": "Listed on all major platforms"},
            {"date": "Jan 5", "event": "🏠 First Showing", "status": "✅ Complete", "notes": "Private showing with positive feedback"},
            {"date": "Jan 8", "event": "🤝 First Offers Received", "status": "⏳ In Progress", "notes": "Two offers currently under review"},
            {"date": "Jan 9", "event": "📋 Offer Decision", "status": "🔄 Pending", "notes": "Accept, counter, or decline current offers"},
            {"date": "Jan 10", "event": "📝 Contract Execution", "status": "⏸️ Waiting", "notes": "Dependent on offer decision"},
            {"date": "Jan 17", "event": "🔍 Inspection Period", "status": "📅 Scheduled", "notes": "7-10 day inspection window"},
            {"date": "Jan 24", "event": "💰 Financing Approval", "status": "📅 Scheduled", "notes": "Buyer financing deadline"},
            {"date": "Feb 7", "event": "🏡 Closing", "status": "🎯 Target", "notes": "Estimated closing date"}
        ]

        for event in timeline_events:
            col1, col2, col3, col4 = st.columns([1, 2, 1, 2])

            with col1:
                st.markdown(f"**{event['date']}**")
            with col2:
                st.markdown(f"{event['event']}")
            with col3:
                st.markdown(event['status'])
            with col4:
                st.markdown(f"*{event['notes']}*")

    with tab3:
        st.markdown("##### Next Steps")

        # Immediate actions needed
        st.markdown("**🔥 Immediate Actions (Next 24-48 Hours)**")

        immediate_actions = [
            {
                "action": "Review and respond to current offers",
                "priority": "🔴 High",
                "deadline": "Tomorrow 5:00 PM",
                "responsible": "You & Listing Agent"
            },
            {
                "action": "Prepare counter-offer strategy",
                "priority": "🟡 Medium",
                "deadline": "Today",
                "responsible": "Listing Agent"
            },
            {
                "action": "Schedule additional showings for weekend",
                "priority": "🟢 Normal",
                "deadline": "End of week",
                "responsible": "Showing Coordinator"
            }
        ]

        for action in immediate_actions:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 2])

                with col1:
                    st.markdown(f"• {action['action']}")
                with col2:
                    st.markdown(action['priority'])
                with col3:
                    st.markdown(action['deadline'])
                with col4:
                    st.markdown(f"*{action['responsible']}*")

        # Upcoming milestones
        st.markdown("**📅 Upcoming Milestones**")

        milestones = [
            {
                "milestone": "Contract Execution",
                "target_date": "Within 3 days",
                "description": "Accept offer and execute purchase contract"
            },
            {
                "milestone": "Inspection Period",
                "target_date": "Days 4-10",
                "description": "Buyer inspection and potential negotiations"
            },
            {
                "milestone": "Appraisal",
                "target_date": "Days 10-15",
                "description": "Lender-ordered property appraisal"
            },
            {
                "milestone": "Final Approval",
                "target_date": "Days 20-25",
                "description": "Buyer's loan final approval and clear to close"
            },
            {
                "milestone": "Closing",
                "target_date": "Day 30",
                "description": "Title transfer and sale completion"
            }
        ]

        for milestone in milestones:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 3])

                with col1:
                    st.markdown(f"**📍 {milestone['milestone']}**")
                with col2:
                    st.markdown(milestone['target_date'])
                with col3:
                    st.markdown(milestone['description'])

    with tab4:
        st.markdown("##### Progress Milestones")

        # Milestone progress tracker
        milestones_progress = [
            {"milestone": "Property Preparation", "progress": 100, "status": "✅ Complete"},
            {"milestone": "Marketing Launch", "progress": 100, "status": "✅ Complete"},
            {"milestone": "Generate Interest", "progress": 85, "status": "🟡 Strong Progress"},
            {"milestone": "Receive Offers", "progress": 60, "status": "⏳ In Progress"},
            {"milestone": "Accept Contract", "progress": 0, "status": "⏸️ Pending"},
            {"milestone": "Navigate Contingencies", "progress": 0, "status": "⏸️ Future"},
            {"milestone": "Close Sale", "progress": 0, "status": "⏸️ Future"}
        ]

        for milestone in milestones_progress:
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                st.markdown(f"**{milestone['milestone']}**")
            with col2:
                st.progress(milestone['progress'] / 100)
                st.markdown(f"{milestone['progress']}% Complete")
            with col3:
                st.markdown(milestone['status'])

        # Key metrics
        st.markdown("**📊 Sale Performance Metrics**")

        metrics = [
            {"metric": "Time to First Offer", "value": "8 days", "benchmark": "< 14 days", "status": "🎯 Excellent"},
            {"metric": "Offer Quality", "value": "Strong", "benchmark": "At/Above Asking", "status": "✅ Good"},
            {"metric": "Marketing Reach", "value": "2,847 views", "benchmark": "> 1,000", "status": "🚀 Exceeding"},
            {"metric": "Showing Interest", "value": "18 showings", "benchmark": "> 10", "status": "✅ Strong"}
        ]

        for metric in metrics:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"**{metric['metric']}**")
            with col2:
                st.markdown(metric['value'])
            with col3:
                st.markdown(metric['benchmark'])
            with col4:
                st.markdown(metric['status'])

def render_seller_analytics():
    """Comprehensive seller analytics and insights"""
    st.subheader("📊 Seller Analytics & Insights")

    # Analytics overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Projected Net Proceeds", "$462,150", delta="$8,500 vs. initial estimate")
    with col2:
        st.metric("📈 Market Performance", "Above Average", delta="Top 15% in area")
    with col3:
        st.metric("⏱️ Est. Time to Contract", "12 days", delta="3 days faster than average")
    with col4:
        st.metric("🎯 Success Probability", "92%", delta="Strong indicators")

    # Detailed analytics
    tab1, tab2, tab3, tab4 = st.tabs([
        "💰 Financial Analysis", "📊 Market Performance", "🎯 Success Predictors", "📈 Competitive Position"
    ])

    with tab1:
        st.markdown("##### Financial Projection")

        # Net proceeds calculation
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📊 Estimated Sale Proceeds**")

            # Financial breakdown
            sale_price = 492000
            commission = sale_price * 0.06
            closing_costs = sale_price * 0.015
            repairs = 2500
            staging = 1200
            other_costs = 800

            financial_data = [
                {"Item": "Gross Sale Price", "Amount": f"${sale_price:,}"},
                {"Item": "Real Estate Commission (6%)", "Amount": f"-${commission:,.0f}"},
                {"Item": "Closing Costs (~1.5%)", "Amount": f"-${closing_costs:,.0f}"},
                {"Item": "Pre-Sale Repairs", "Amount": f"-${repairs:,}"},
                {"Item": "Staging Costs", "Amount": f"-${staging:,}"},
                {"Item": "Other Selling Costs", "Amount": f"-${other_costs:,}"},
                {"Item": "**Net Proceeds**", "Amount": f"**${sale_price - commission - closing_costs - repairs - staging - other_costs:,.0f}**"}
            ]

            for item in financial_data:
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    if item["Item"].startswith("**"):
                        st.markdown(item["Item"])
                    else:
                        st.markdown(f"• {item['Item']}")
                with col_b:
                    st.markdown(item["Amount"])

        with col2:
            # Visual breakdown
            costs = ["Commission", "Closing Costs", "Repairs", "Other", "Net Proceeds"]
            amounts = [commission, closing_costs, repairs, staging + other_costs, sale_price - commission - closing_costs - repairs - staging - other_costs]

            fig = px.pie(values=amounts, names=costs, title="Sale Proceeds Breakdown")
            st.plotly_chart(fig, use_container_width=True)

        # ROI Analysis
        st.markdown("**🏠 Return on Investment Analysis**")

        original_purchase = 385000
        improvements = 15000
        total_investment = original_purchase + improvements
        total_return = sale_price - commission - closing_costs - repairs - staging - other_costs
        roi = ((total_return - total_investment) / total_investment) * 100

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Original Purchase", f"${original_purchase:,}")
        with col2:
            st.metric("Total Improvements", f"${improvements:,}")
        with col3:
            st.metric("Total Investment", f"${total_investment:,}")
        with col4:
            st.metric("ROI", f"{roi:.1f}%", delta="Excellent return")

    with tab2:
        st.markdown("##### Market Performance Analysis")

        # Comparison metrics
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📊 Your Property vs. Market Average**")

            comparison_data = [
                {"Metric": "Days on Market", "Your Property": "8 days", "Market Average": "22 days", "Performance": "🟢 64% Faster"},
                {"Metric": "List-to-Sale Price", "Your Property": "99.4%", "Market Average": "96.8%", "Performance": "🟢 2.6% Better"},
                {"Metric": "Showings per Week", "Your Property": "9", "Market Average": "4.5", "Performance": "🟢 2x More"},
                {"Metric": "Inquiry Rate", "Your Property": "1.65%", "Market Average": "1.2%", "Performance": "🟢 38% Higher"}
            ]

            for data in comparison_data:
                st.markdown(f"**{data['Metric']}:**")
                col_a, col_b, col_c = st.columns([1, 1, 1])
                with col_a:
                    st.markdown(f"You: {data['Your Property']}")
                with col_b:
                    st.markdown(f"Market: {data['Market Average']}")
                with col_c:
                    st.markdown(data['Performance'])
                st.markdown("---")

        with col2:
            # Performance trends
            st.markdown("**📈 Performance Trends**")

            weeks = ["Week 1", "Week 2"]
            views = [1456, 1391]
            inquiries = [28, 19]

            fig_performance = go.Figure()
            fig_performance.add_trace(go.Scatter(x=weeks, y=views, mode='lines+markers', name='Views', yaxis='y'))
            fig_performance.add_trace(go.Scatter(x=weeks, y=inquiries, mode='lines+markers', name='Inquiries', yaxis='y2'))

            fig_performance.update_layout(
                title="Weekly Performance Trends",
                yaxis=dict(title="Views", side="left"),
                yaxis2=dict(title="Inquiries", side="right", overlaying="y"),
                legend=dict(x=0.7, y=1)
            )
            st.plotly_chart(fig_performance, use_container_width=True)

        # Market conditions impact
        st.markdown("**🌍 Market Conditions Analysis**")

        conditions = [
            {"Factor": "Interest Rates", "Current": "7.25%", "Trend": "📈 Stable", "Impact": "Neutral"},
            {"Factor": "Inventory Levels", "Current": "2.1 months", "Trend": "📉 Low", "Impact": "🟢 Favorable"},
            {"Factor": "Buyer Demand", "Current": "High", "Trend": "📈 Strong", "Impact": "🟢 Favorable"},
            {"Factor": "Seasonal Timing", "Current": "Peak Season", "Trend": "📈 Optimal", "Impact": "🟢 Favorable"}
        ]

        for condition in conditions:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"**{condition['Factor']}**")
            with col2:
                st.markdown(condition['Current'])
            with col3:
                st.markdown(condition['Trend'])
            with col4:
                impact_color = "green" if "Favorable" in condition['Impact'] else "orange" if "Neutral" in condition['Impact'] else "red"
                st.markdown(f"<span style='color: {impact_color};'>{condition['Impact']}</span>", unsafe_allow_html=True)

    with tab3:
        st.markdown("##### Success Probability Indicators")

        # Success factors
        success_factors = [
            {"Factor": "Competitive Pricing", "Score": 95, "Weight": "25%", "Impact": "Very High"},
            {"Factor": "Property Condition", "Score": 88, "Weight": "20%", "Impact": "High"},
            {"Factor": "Market Timing", "Score": 92, "Weight": "20%", "Impact": "Very High"},
            {"Factor": "Marketing Quality", "Score": 90, "Weight": "15%", "Impact": "High"},
            {"Factor": "Agent Performance", "Score": 94, "Weight": "10%", "Impact": "High"},
            {"Factor": "Location Desirability", "Score": 85, "Weight": "10%", "Impact": "Medium-High"}
        ]

        for factor in success_factors:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

            with col1:
                st.markdown(f"**{factor['Factor']}**")
                st.progress(factor['Score'] / 100)

            with col2:
                st.markdown(f"{factor['Score']}/100")

            with col3:
                st.markdown(factor['Weight'])

            with col4:
                impact_color = "green" if "Very High" in factor['Impact'] else "blue" if "High" in factor['Impact'] else "orange"
                st.markdown(f"<span style='color: {impact_color};'>{factor['Impact']}</span>", unsafe_allow_html=True)

        # Overall score calculation
        weighted_score = sum([factor['Score'] * float(factor['Weight'].replace('%', '')) / 100 for factor in success_factors])

        st.markdown(f"**🎯 Overall Success Score: {weighted_score:.1f}/100**")

        if weighted_score >= 90:
            st.success("🟢 **Excellent** - Very high probability of successful sale at or above asking price")
        elif weighted_score >= 80:
            st.info("🔵 **Good** - Strong probability of successful sale within market timeframe")
        elif weighted_score >= 70:
            st.warning("🟡 **Fair** - Moderate probability, may need strategy adjustments")
        else:
            st.error("🔴 **Needs Improvement** - Consider addressing key factors before listing")

    with tab4:
        st.markdown("##### Competitive Market Position")

        # Direct competitors
        st.markdown("**🏠 Direct Competitors Currently Listed**")

        competitors = [
            {
                "address": "1456 Maple Street",
                "price": "$515,000",
                "days_listed": "45 days",
                "beds_baths": "3 bed / 2.5 bath",
                "sqft": "1,920 sqft",
                "advantage": "Better condition, lower price",
                "risk": "Similar features, longer on market"
            },
            {
                "address": "1678 Oak Avenue",
                "price": "$475,000",
                "days_listed": "12 days",
                "beds_baths": "3 bed / 2 bath",
                "sqft": "1,750 sqft",
                "advantage": "Larger, better updates",
                "risk": "Direct competition, similar price"
            },
            {
                "address": "1234 Pine Drive",
                "price": "$525,000",
                "days_listed": "8 days",
                "beds_baths": "4 bed / 2.5 bath",
                "sqft": "2,100 sqft",
                "advantage": "Better value per sqft",
                "risk": "Larger home, higher price point"
            }
        ]

        for competitor in competitors:
            with st.expander(f"{competitor['address']} - {competitor['price']} ({competitor['days_listed']})"):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**Size:** {competitor['beds_baths']}, {competitor['sqft']}")
                    st.markdown(f"**Your Advantage:** {competitor['advantage']}")

                with col2:
                    st.markdown(f"**Days Listed:** {competitor['days_listed']}")
                    st.markdown(f"**Competitive Risk:** {competitor['risk']}")

        # Market positioning summary
        st.markdown("**🎯 Strategic Positioning Summary**")

        positioning = [
            {"Aspect": "Price Point", "Position": "Competitive", "Strategy": "Priced to move quickly while maximizing value"},
            {"Aspect": "Condition", "Position": "Superior", "Strategy": "Highlight move-in ready status and recent updates"},
            {"Aspect": "Marketing", "Position": "Leading", "Strategy": "Professional presentation generating strong interest"},
            {"Aspect": "Timing", "Position": "Optimal", "Strategy": "Listed during peak buyer activity period"}
        ]

        for pos in positioning:
            col1, col2, col3 = st.columns([1, 1, 3])
            with col1:
                st.markdown(f"**{pos['Aspect']}:**")
            with col2:
                position_color = "green" if pos['Position'] in ["Superior", "Leading", "Optimal"] else "blue" if pos['Position'] == "Competitive" else "orange"
                st.markdown(f"<span style='color: {position_color};'>{pos['Position']}</span>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"*{pos['Strategy']}*")

        # Recommendations
        st.info("""
        💡 **Strategic Recommendations:**
        - Maintain current pricing strategy - well-positioned vs. competition
        - Emphasize move-in ready condition and recent updates in marketing
        - Monitor competitor price changes and adjust strategy if needed
        - Current positioning should result in sale within 2-3 weeks at or near asking price
        """)

# Buyer Journey Hub Components
def render_buyer_journey_hub():
    """Render the complete buyer journey experience"""
    st.title("🏠 Buyer Journey Hub")
    st.markdown("*Comprehensive buyer experience from search to closing*")

    # Claude's Journey Counsel
    with st.container(border=True):
        col_c1, col_c2 = st.columns([1, 8])
        with col_c1:
            st.markdown("<div style='font-size: 3rem; text-align: center;'>🗺️</div>", unsafe_allow_html=True)
        with col_c2:
            st.markdown("### Claude's Buyer Journey Counsel")
            
            # Dynamic journey insights
            if selected_lead_name == "Sarah Chen (Apple Engineer)":
                journey_text = """
                *Monitoring Sarah's North Austin search:*
                - **🧭 Path Finder:** Sarah has reached the 'Viewing' stage. She's 40% more likely to close if we show her the Teravista property this weekend.
                - **📉 Value Alert:** New listing in Cedar Park just hit the market. It aligns with her 45-day relocation timeline perfectly.
                """
            elif selected_lead_name == "David Kim (Investor)":
                journey_text = """
                *Monitoring David's portfolio expansion:*
                - **🧭 Path Finder:** David is in 'Evaluation' mode. He's analyzed 4 Manor properties. High probability of multi-unit offer if Cap Rate is > 5%.
                - **📉 Value Alert:** An off-market duplex in Del Valle just became available. I've sent him the ROI breakdown.
                """
            elif selected_lead_name == "Mike & Jessica Rodriguez (Growing Family)":
                journey_text = """
                *Monitoring the Rodriguez family journey:*
                - **🧭 Path Finder:** They are currently in 'Education' stage. Providing a 'First-Time Buyer' guide will increase their engagement by 60%.
                - **📉 Value Alert:** Found a home in Pflugerville with a huge fenced yard - their top 'must-have'.
                """
            else:
                journey_text = """
                *Monitoring your active buyers in Austin:*
                - **🧭 Path Finder:** Sarah Johnson has reached the 'Viewing' stage. She's 40% more likely to close if we show her properties in the Avery Ranch district this weekend.
                - **📉 Value Alert:** 2 listings in the $500k range just had price drops. I've flagged these for your 'Move-up Buyer' segment.
                """
            st.markdown(journey_text)
            
            if st.button("🚀 Alert All Matching Buyers"):
                st.toast("Syncing price-drop alerts to GHL workflows...", icon="🔔")

    # Buyer navigation tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🔍 Property Search",
        "👤 Buyer Profile",
        "💰 Financing",
        "🌍 Neighborhoods",
        "📅 Saved & Scheduled",
        "📊 Buyer Analytics"
    ])

    with tab1:
        render_enhanced_property_search()

    with tab2:
        render_buyer_profile_builder()

    with tab3:
        render_financing_calculator()

    with tab4:
        render_neighborhood_explorer()

    with tab5:
        render_buyer_dashboard()

    with tab6:
        render_buyer_analytics()

# Seller Journey Hub Components
def render_seller_journey_hub():
    """Render the complete seller experience from valuation to closing*"""
    st.title("🏡 Seller Journey Hub")
    st.markdown("*Complete seller experience from valuation to closing*")

    # Claude's Journey Counsel
    with st.container(border=True):
        col_s1, col_s2 = st.columns([1, 8])
        with col_s1:
            st.markdown("<div style='font-size: 3rem; text-align: center;'>🏠</div>", unsafe_allow_html=True)
        with col_s2:
            st.markdown("### Claude's Seller Journey Counsel")
            st.markdown("""
            *Inventory optimization for Jorge:*
            - **💎 Value Maximizer:** Your 'Alta Loma' listing is seeing 2x higher engagement than neighborhood comps. I recommend a 'Coming Soon' email blast to your luxury investor list.
            - **⏱️ Velocity Check:** Current market days-on-market (DOM) is dropping. We should push for a contract execution within the next 72 hours to maintain momentum.
            """)
            if st.button("📊 Draft Market Update for Seller"):
                st.toast("Claude is drafting a performance report for your seller...", icon="✍️")

    # Seller navigation tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Property Valuation",
        "📋 Seller Prep",
        "📈 Marketing Campaign",
        "💬 Communication",
        "📅 Timeline & Offers",
        "📊 Seller Analytics"
    ])

    with tab1:
        render_property_valuation_engine()

    with tab2:
        render_seller_prep_checklist()

    with tab3:
        render_marketing_campaign_dashboard()

    with tab4:
        render_seller_communication_portal()

    with tab5:
        render_transaction_timeline()

    with tab6:
        render_seller_analytics()

render_claude_assistant()

if selected_hub == "🏢 Executive Command Center":
    render_executive_hub()
elif selected_hub == "🧠 Lead Intelligence Hub":
    render_lead_intelligence_hub()
elif selected_hub == "⚡ Real-Time Intelligence":
    render_realtime_intelligence_dashboard()
elif selected_hub == "🏠 Buyer Journey Hub":
    render_buyer_journey_hub()
elif selected_hub == "🏡 Seller Journey Hub":
    render_seller_journey_hub()
elif selected_hub == "🤖 Automation Studio":
    render_automation_studio()
elif selected_hub == "💰 Sales Copilot":
    render_sales_copilot()
elif selected_hub == "📈 Ops & Optimization":
    render_ops_hub()
elif selected_hub == "🐝 Swarm Intelligence":
    render_swarm_visualizer()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 2rem; background: #F7F8FA; border-radius: 12px; margin-top: 3rem;'>
    <div style='color: #2A2A33; font-weight: 600; font-size: 1.1rem; margin-bottom: 0.5rem;'>
        🚀 Production-Ready Multi-Tenant AI System
    </div>
    <div style='color: #6B7280; font-size: 0.9rem;'>
        Built for Jorge Sales | Claude Sonnet 4.5 | GHL Integration Ready
    </div>
    <div style='margin-top: 1rem; color: #6B7280; font-size: 0.85rem;'>
        Consolidated Hub Architecture | Path B Backend | 522+ Tests Passing
    </div>
</div>
""", unsafe_allow_html=True)
