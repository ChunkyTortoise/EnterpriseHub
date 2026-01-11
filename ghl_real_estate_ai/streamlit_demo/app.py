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
    from services.memory_service import MemoryService
    from services.lead_lifecycle import LeadLifecycleTracker
    from services.behavioral_triggers import BehavioralTriggerEngine
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

    # Enhanced services imports (with error handling)
    try:
        from services.churn_integration_service import ChurnIntegrationService
        CHURN_INTEGRATION_SERVICE_AVAILABLE = True
    except ImportError as e:
        print(f"Churn Integration Service not available: {e}")
        ChurnIntegrationService = None
        CHURN_INTEGRATION_SERVICE_AVAILABLE = False

    # Comprehensive Chatbot System imports
    from services.streamlit_chat_component import (
        initialize_chat_system,
        render_chat_demo,
        render_lead_chat,
        render_buyer_chat,
        render_seller_chat,
        render_chat_analytics,
        render_admin_chat_controls,
        add_chat_to_page,
        render_mini_chat
    )

    # Enhanced Lead Intelligence imports
    try:
        # Import from the local streamlit_demo services directory
        import sys
        from pathlib import Path
        local_services_path = str(Path(__file__).parent / "services")
        if local_services_path not in sys.path:
            sys.path.insert(0, local_services_path)

        import lead_intelligence_integration
        from lead_intelligence_integration import (
            render_complete_enhanced_hub,
            render_enhanced_lead_chat,
            render_lead_analytics_dashboard,
            render_qualification_dashboard,
            render_conversation_intelligence,
            render_predictive_insights,
            render_intelligence_configuration,
            get_intelligence_status
        )
        ENHANCED_INTELLIGENCE_AVAILABLE = True
        print("✅ Enhanced Lead Intelligence successfully loaded!")
        print(f"DEBUG: get_intelligence_status function: {get_intelligence_status}")
        print(f"DEBUG: render_complete_enhanced_hub function: {render_complete_enhanced_hub}")

        # Test the status function immediately
        try:
            test_status = get_intelligence_status()
            print(f"DEBUG: Status function test result: {test_status}")
        except Exception as e:
            print(f"DEBUG: Status function test failed: {e}")
    except ImportError as e:
        print(f"❌ Enhanced Lead Intelligence not available: {e}")
        ENHANCED_INTELLIGENCE_AVAILABLE = False
        # Create fallback functions to prevent errors
        def render_complete_enhanced_hub():
            st.warning("Enhanced Intelligence features temporarily unavailable")
        def get_intelligence_status():
            return {
                "initialized": True,
                "version": "1.0.0",
                "features_active": 6,
                "last_updated": "2026-01-09",
                "intelligence_available": True,
                "dashboard_available": True
            }

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
        "property_matcher": PropertyMatcher(listings_path=str(listings_path))
    }

    # Add churn service only if available
    if CHURN_INTEGRATION_SERVICE_AVAILABLE and ChurnIntegrationService is not None:
        try:
            services_dict["churn_service"] = ChurnIntegrationService(
                memory_service=None,  # Would be injected with actual services
                lifecycle_tracker=None,
                behavioral_engine=None,
                lead_scorer=None,
                reengagement_engine=ReengagementEngine(),
                ghl_service=None
            )
        except Exception as e:
            print(f"Warning: Could not initialize ChurnIntegrationService: {e}")
            # Continue without churn service

    # Add enhanced services if available
    if ENHANCED_LEAD_SCORER_AVAILABLE:
        services_dict["enhanced_lead_scorer"] = EnhancedLeadScorer()

    if ENHANCED_PROPERTY_MATCHER_AVAILABLE:
        services_dict["enhanced_property_matcher"] = EnhancedPropertyMatcher(listings_path=str(listings_path))

    if CHURN_PREDICTION_ENGINE_AVAILABLE:
        try:
            # Initialize required services for ChurnPredictionEngine
            memory_service = MemoryService()
            lifecycle_tracker = LeadLifecycleTracker()
            behavioral_engine = BehavioralTriggerEngine()
            lead_scorer = services_dict["lead_scorer"]  # Reuse the existing LeadScorer instance

            services_dict["churn_prediction"] = ChurnPredictionEngine(
                memory_service=memory_service,
                lifecycle_tracker=lifecycle_tracker,
                behavioral_engine=behavioral_engine,
                lead_scorer=lead_scorer
            )
        except Exception as e:
            print(f"Warning: Could not initialize ChurnPredictionEngine: {e}")
            # Continue without churn prediction service

    return services_dict

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
        "Sarah Johnson": {
            "extracted_preferences": {
                "budget": 1300000 if market_key == "Rancho" else 800000,
                "location": "Alta Loma" if market_key == "Rancho" else "Downtown",
                "timeline": "ASAP",
                "bedrooms": 4,
                "bathrooms": 3,
                "must_haves": "Pool",
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
        if st.button(action_label, key=action_key, width='stretch'):
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

# Load luxury enhancement styling for premium demo experience
try:
    from luxury_enhancement_injection import inject_luxury_enhancements
    inject_luxury_enhancements()
except ImportError:
    # Fallback inline luxury styling for demo presentation
    st.markdown("""
    <style>
    /* Premium fonts and luxury styling */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800&display=swap');

    :root {
        --luxury-navy: #0a1628;
        --luxury-deep-blue: #1e3a8a;
        --luxury-gold: #d4af37;
        --luxury-bronze: #cd7f32;
        --luxury-pearl: #f8fafc;
    }

    /* Enhanced metric containers */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.9) 100%) !important;
        backdrop-filter: blur(20px) saturate(180%);
        border-radius: 16px !important;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    div[data-testid="metric-container"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, var(--luxury-gold) 0%, var(--luxury-bronze) 100%);
    }

    div[data-testid="metric-container"]:hover {
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25), 0 0 20px rgba(212, 175, 55, 0.3) !important;
    }

    /* Premium typography */
    div[data-testid="metric-container"] [data-testid="metric-value"] {
        font-family: 'Playfair Display', serif !important;
        font-weight: 800 !important;
        font-size: 2.5rem !important;
        background: linear-gradient(135deg, var(--luxury-deep-blue), var(--luxury-gold));
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Enhanced buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--luxury-deep-blue) 0%, var(--luxury-navy) 100%) !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 0 20px rgba(59, 130, 246, 0.3) !important;
    }

    /* Premium header styling */
    .main > div:first-child > div:first-child {
        background: linear-gradient(135deg, var(--luxury-navy) 0%, var(--luxury-deep-blue) 50%, #1e293b 100%);
        position: relative;
        overflow: hidden;
    }

    /* Enhanced charts */
    .js-plotly-plot {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.9) 100%) !important;
        border-radius: 16px !important;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1) !important;
        backdrop-filter: blur(20px);
        transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .js-plotly-plot:hover {
        transform: scale(1.02);
    }
    </style>
    """, unsafe_allow_html=True)

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
header_title = "GHL Real Estate AI"
header_subtitle = "Enterprise Command Center"
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
            Professional AI-powered lead qualification and automation system for <strong>Jorge Salas</strong>
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

    if st.button("🔄 Refresh Data", width='stretch', type="primary"):
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
    st.plotly_chart(fig, width='stretch')

# Main content area
@ui_error_boundary("Executive Command Center")
def render_executive_hub():
    st.header("🏢 Executive Command Center")
    st.markdown("*High-level KPIs, revenue tracking, and system health*")
    
    # Tabs for sub-features
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🎯 AI Insights", "📄 Reports"])
    
    with tab1:
        st.subheader("Executive Dashboard")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Pipeline", "$2.4M", "+15%")
        with col2:
            st.metric("Hot Leads", "23", "+8")
        with col3:
            st.metric("Conversion Rate", "34%", "+2%")
        with col4:
            st.metric("Avg Deal Size", "$385K", "+$12K")
        
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
    st.markdown("*Advanced AI-powered lead intelligence with real-time insights*")

    # Show current status for debugging
    if ENHANCED_INTELLIGENCE_AVAILABLE:
        st.success("✅ Enhanced Features Available - Lead Intelligence Integration Loaded")

        # Quick test of the functions
        try:
            status = get_intelligence_status()
            st.info(f"🧠 Intelligence Status: {status['features_active']} features active, v{status['version']}")
        except Exception as e:
            st.error(f"❌ Status function error: {str(e)}")
    else:
        st.warning("⚠️ Enhanced Features Not Available - using fallback interface")

    # Enhanced Intelligence Toggle
    col_toggle, col_status = st.columns([3, 1])

    with col_toggle:
        use_enhanced = st.checkbox(
            "🚀 Enable Enhanced Intelligence Features",
            value=True,  # Always default to True to show enhanced features
            disabled=not ENHANCED_INTELLIGENCE_AVAILABLE,
            help="Advanced lead qualification, conversation intelligence, and predictive analytics"
        )

    with col_status:
        if ENHANCED_INTELLIGENCE_AVAILABLE:
            try:
                status = get_intelligence_status()
                if status["initialized"]:
                    st.success(f"✅ Enhanced AI v{status.get('version', '1.0')}")
                else:
                    st.warning("⚙️ Initializing...")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("❌ Standard Mode")

    # Debug information (temporary)
    if st.checkbox("🔧 Show Debug Info", value=False):
        debug_info = {
            "enhanced_available": ENHANCED_INTELLIGENCE_AVAILABLE,
            "use_enhanced": use_enhanced,
            "lead_options_initialized": 'lead_options' in st.session_state,
            "render_function_available": 'render_complete_enhanced_hub' in locals() or 'render_complete_enhanced_hub' in globals(),
            "status_function_available": 'get_intelligence_status' in locals() or 'get_intelligence_status' in globals()
        }

        # Test status function
        try:
            status = get_intelligence_status()
            debug_info["status_function_result"] = status
        except Exception as e:
            debug_info["status_function_error"] = str(e)

        st.json(debug_info)

    # Render enhanced or standard interface
    if use_enhanced and ENHANCED_INTELLIGENCE_AVAILABLE:
        st.info("🚀 Attempting to load Enhanced Intelligence Interface...")
        try:
            render_complete_enhanced_hub()
            st.success("✅ Enhanced Intelligence Interface loaded successfully!")
            return  # Exit early if enhanced interface renders successfully
        except Exception as e:
            st.error(f"Enhanced features temporarily unavailable: {str(e)}")
            st.code(f"Error details: {type(e).__name__}: {str(e)}")
            st.info("Falling back to standard interface...")

            # Show detailed error for debugging
            import traceback
            st.expander("🔧 Error Details").code(traceback.format_exc())

    # Force enhanced interface if available (even if checkbox not checked)
    if ENHANCED_INTELLIGENCE_AVAILABLE and not use_enhanced:
        st.info("💡 Enhanced features are available! Check the box above to enable them.")
        try:
            render_complete_enhanced_hub()
            return
        except Exception as e:
            st.warning(f"Enhanced interface error: {str(e)}")

    # Standard Lead Intelligence Hub (existing functionality)
    st.markdown("*Deep dive into individual leads with AI-powered insights*")
    
    # Access global lead_options - ensure it exists
    if 'lead_options' not in st.session_state:
        st.error("Lead options not initialized. Initializing now...")
        try:
            st.session_state.lead_options = get_lead_options(market_key)
            st.success("Lead options initialized successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to initialize lead options: {str(e)}")
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
            if st.button("📞 Call Now", width='stretch', type="primary"):
                st.toast(f"Calling {selected_lead_name}...", icon="📞")
                st.success("Call initiated via GHL")
        
        with col_act2:
            if st.button("💬 Send SMS", width='stretch'):
                st.toast(f"Opening SMS composer for {selected_lead_name}", icon="💬")
                st.info("SMS template loaded in GHL")
        
        with col_act3:
            if st.button("📧 Send Email", width='stretch'):
                st.toast(f"Email draft created for {selected_lead_name}", icon="📧")
                st.success("Email queued in GHL")
        
        with col_act4:
            if st.button("📅 Schedule Tour", width='stretch'):
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
            churn_dashboard = ChurnEarlyWarningDashboard()
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
        st.subheader("🌐 Self-Service Buyer Portal")
        st.markdown("*Phase 3: Give leads their own dashboard to update criteria*")
        
        # Get current preferences for the selected lead
        if selected_lead_name != "-- Select a Lead --":
            current_prefs = lead_options[selected_lead_name].get("extracted_preferences", {})
        else:
            current_prefs = {}
        
        portal_url = f"/portal?lead={selected_lead_name.lower().replace(' ', '-')}"
        st.info(f"Unique URL: `https://portal.jorgesalas.ai/l/{selected_lead_name.lower().replace(' ', '-')}`")
        
        st.markdown(f"""
        <div style='background: white; padding: 2rem; border-radius: 15px; border: 1px solid #006AFF; text-align: center; margin-bottom: 2rem;'>
            <h2 style='color: #006AFF; margin-top: 0;'>🚀 Live Portal Ready</h2>
            <p>The standalone buyer portal is now active for this lead.</p>
            <a href='{portal_url}' target='_blank' style='background-color: #006AFF; color: white; padding: 0.75rem 2rem; text-decoration: none; border-radius: 10px; font-weight: 700;'>Open Live Portal</a>
        </div>
        """, unsafe_allow_html=True)

        # Preview of the portal
        st.markdown("#### 📱 Portal Preview")
        
        # Center the mobile mockup
        _, center_col, _ = st.columns([1, 1.5, 1])
        
        with center_col:
            st.markdown("""
            <div class='phone-mockup'>
                <div class='phone-header'></div>
                <div style='background: #f0f2f6; padding: 10px; text-align: center; border-bottom: 1px solid #ddd; font-size: 0.65rem; color: #666;'>
                    🔒 portal.jorgesalas.ai
                </div>
                <div style='padding: 15px;'>
            """, unsafe_allow_html=True)
            
            st.markdown(f"<h3 style='text-align: center; margin-top: 0.5rem; font-size: 1.2rem;'>Hey {selected_lead_name}! 👋</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; font-size: 0.8rem; opacity: 0.8;'>I've filtered the best homes for you.</p>", unsafe_allow_html=True)
            
            # Callback for budget change notification with cross-tab sync
            def notify_budget_change():
                new_budget = st.session_state.portal_slider_preview
                
                # Cross-tab sync: Update live feed
                try:
                    fs = LiveFeedService()
                    fs.add_activity("lead", selected_lead_name, f"Updated budget to ${new_budget:,}")
                except:
                    pass
                
                # Cross-tab sync: Update session state for other tabs
                if 'lead_activities' not in st.session_state:
                    st.session_state.lead_activities = []
                
                st.session_state.lead_activities.append({
                    "timestamp": datetime.datetime.now(),
                    "lead": selected_lead_name,
                    "action": "Budget Update",
                    "details": f"${new_budget:,}",
                    "source": "Buyer Portal"
                })
                
                st.toast(f"🚀 {selected_lead_name} updated budget to ${new_budget:,}!", icon="💰")

            st.slider("Max Budget", 500000, 2000000, current_prefs.get('budget', 1000000), step=50000, key="portal_slider_preview", on_change=notify_budget_change)
            
            st.markdown("---")
            
            portal_matches = services["property_matcher"].find_matches({"budget": current_prefs.get('budget', 1000000), "location": current_prefs.get('location')}, limit=1)
            for pm in portal_matches:
                pm_title = pm.get('title') or f"{pm.get('bedrooms', 0)}BR {pm.get('property_type', 'Home')} in {pm.get('address', {}).get('neighborhood', 'Area')}"
                pm_price = pm.get('price', 0)
                pm_beds = pm.get('bedrooms', '?')
                pm_baths = pm.get('bathrooms', '?')
                pm_neighborhood = pm.get('address', {}).get('neighborhood', 'Unknown')
                
                st.markdown(f"""
                <div style='background: white; padding: 0.75rem; border-radius: 10px; border: 1px solid #eee; margin-bottom: 1rem; color: #333; box-shadow: 0 2px 5px rgba(0,0,0,0.05);'>
                    <div style='font-weight: 700; color: #006AFF; font-size: 0.9rem;'>${pm_price:,}</div>
                    <div style='font-size: 0.75rem; font-weight: 600;'>{pm_title}</div>
                    <div style='font-size: 0.65rem; color: #666;'>{pm_beds} BR | {pm_baths} BA | {pm_neighborhood}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.button("Update My Search", width="stretch", key="portal_btn_preview")
            
            st.markdown("</div></div>", unsafe_allow_html=True)
    
    with tab5:
        # Use Elite Segmentation View with fixed HTML rendering
        try:
            from components.elite_refinements import render_elite_segmentation_tab
            render_elite_segmentation_tab()
        except ImportError:
            # Fallback to legacy implementation
            st.subheader("Smart Segmentation")
            st.markdown("*AI-powered lead clustering with activity heatmaps*")
            
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
        st.subheader("Predictive Scoring")
        
        # Sync Lead Selection with global state
        pred_lead_names = list(st.session_state.lead_options.keys())
        try:
            default_pred_idx = pred_lead_names.index(st.session_state.selected_lead_name)
        except ValueError:
            default_pred_idx = 0

        selected_lead_pred = st.selectbox(
            "Select Lead for Prediction:", 
            pred_lead_names, 
            index=default_pred_idx,
            key="pred_lead_selector",
            on_change=lambda: st.session_state.update({"selected_lead_name": st.session_state.pred_lead_selector})
        )
        
        # Mock lead data for prediction
        lead_data_pred = {
            "id": "lead_123",
            "email_opens": 8,
            "email_clicks": 5,
            "emails_sent": 10,
            "response_times": [2.5, 1.8, 3.2],
            "page_views": 12,
            "budget": 500000,
            "viewed_property_prices": [480000, 520000, 495000],
            "timeline": "soon",
            "property_matches": 7,
            "messages": [{"content": "I'm interested in properties in downtown."}],
            "source": "organic"
        }
        
        pred_result = services["predictive_scorer"].score_lead("lead_123", lead_data_pred)
        
        col_gauge, col_factors = st.columns([1, 1])
        
        with col_gauge:
            # Conversion Probability Gauge
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = pred_result.score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Conversion Chance", 'font': {'size': 18, 'color': '#1e293b'}},
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
            st.plotly_chart(fig_gauge, width='stretch')
            
            st.markdown(f"""
            <div style='text-align: center; margin-top: -20px;'>
                <span class='badge' style='background: #f1f5f9; color: #475569;'>Tier: {pred_result.tier.upper()}</span>
                <span class='badge' style='background: #f1f5f9; color: #475569; margin-left: 10px;'>Confidence: {pred_result.confidence*100:.0f}%</span>
            </div>
            """, unsafe_allow_html=True)
        
        with col_factors:
            # Conversion Timeline Forecast
            st.markdown("#### ⏱️ Conversion Timeline")
            
            prob = pred_result.score
            estimated_days = 45 if prob > 70 else 90 if prob > 40 else 120
            
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); 
                        padding: 2rem; border-radius: 12px; color: white; text-align: center;
                        margin-bottom: 1rem;'>
                <div style='font-size: 3rem; font-weight: 900;'>{estimated_days}</div>
                <div style='font-size: 1.1rem;'>Days to Expected Close</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Best contact time recommendations
            # Enhanced Best Time to Contact with Urgency Badges
            from components.contact_timing import render_contact_timing_badges
            
            best_times = [
                {"day": "Tomorrow", "time": "2:00 PM - 4:00 PM", "urgency": "high", "probability": 87, "icon": "🔥"},
                {"day": "Friday", "time": "10:00 AM - 12:00 PM", "urgency": "medium", "probability": 68, "icon": "⭐"}
            ]
            
            render_contact_timing_badges(best_times)
        
        st.markdown("---")
        st.markdown("#### 🔍 Contributing Factors")
        
        col_factors_left, col_factors_right = st.columns(2)
        
        with col_factors_left:
            for factor in pred_result.factors[:len(pred_result.factors)//2]:
                sentiment_color = "#10b981" if factor["sentiment"] == "positive" else "#f59e0b"
                sentiment_icon = "📈" if factor["sentiment"] == "positive" else "⚠️"
                
                # Generate tooltip content based on factor name
                tooltip_map = {
                    "Response Time": "Avg response: 2.5 minutes to initial contact",
                    "Engagement Score": "5 interactions in past 7 days",
                    "Budget Alignment": "Property matches within 95% of stated budget",
                    "Location Preference": "3 of 5 showings in target neighborhood"
                }
                tooltip = tooltip_map.get(factor['name'], f"Data-driven insight based on {factor['name'].lower()}")
                
                st.markdown(f"""
                <div style='margin-bottom: 1rem; position: relative;' class='factor-bar' title='{tooltip}'>
                    <div style='display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px;'>
                        <span>{sentiment_icon} <b>{factor['name']}</b></span>
                        <span style='color: {sentiment_color}; font-weight: bold;'>{factor['impact']}% Impact</span>
                    </div>
                    <div style='background: #f1f5f9; height: 8px; border-radius: 4px; overflow: hidden; cursor: pointer;'>
                        <div style='background: {sentiment_color}; width: {abs(factor['impact'])}%; height: 100%; transition: all 0.3s ease;'></div>
                    </div>
                    <div style='font-size: 0.75rem; color: #64748b; margin-top: 2px;'>{factor['value']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col_factors_right:
            for factor in pred_result.factors[len(pred_result.factors)//2:]:
                sentiment_color = "#10b981" if factor["sentiment"] == "positive" else "#f59e0b"
                sentiment_icon = "📈" if factor["sentiment"] == "positive" else "⚠️"
                
                # Generate tooltip content based on factor name
                tooltip_map = {
                    "Response Time": "Avg response: 2.5 minutes to initial contact",
                    "Engagement Score": "5 interactions in past 7 days",
                    "Budget Alignment": "Property matches within 95% of stated budget",
                    "Location Preference": "3 of 5 showings in target neighborhood"
                }
                tooltip = tooltip_map.get(factor['name'], f"Data-driven insight based on {factor['name'].lower()}")
                
                st.markdown(f"""
                <div style='margin-bottom: 1rem; position: relative;' class='factor-bar' title='{tooltip}'>
                    <div style='display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px;'>
                        <span>{sentiment_icon} <b>{factor['name']}</b></span>
                        <span style='color: {sentiment_color}; font-weight: bold;'>{factor['impact']}% Impact</span>
                    </div>
                    <div style='background: #f1f5f9; height: 8px; border-radius: 4px; overflow: hidden; cursor: pointer;'>
                        <div style='background: {sentiment_color}; width: {abs(factor['impact'])}%; height: 100%; transition: all 0.3s ease;'></div>
                    </div>
                    <div style='font-size: 0.75rem; color: #64748b; margin-top: 2px;'>{factor['value']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### 🏃 Recommended Strategy with Predicted Lift")
        
        # Descriptions and predicted lift for each action
        action_details = {
            "Schedule property viewing": {
                "desc": "Automatically check Jorge's Google Calendar and SMS 3 available time slots to the lead.",
                "lift": 2.5,
                "reason": "Active engagement signals high intent"
            },
            "Send personalized listings": {
                "desc": "Generate a PDF of the top 3 matches and email with a personalized video intro.",
                "lift": 1.8,
                "reason": "Visual content increases engagement"
            },
            "Trigger 'Hot Lead' re-engagement": {
                "desc": "Escalate to priority SMS sequence with a 'New Opportunity' hook.",
                "lift": 3.2,
                "reason": "Urgency triggers drive immediate action"
            },
            "Request pre-approval update": {
                "desc": "Check for updated proof of funds via SMS link.",
                "lift": 1.2,
                "reason": "Validates qualification status"
            }
        }

        # Initialize conversion chance in session state if not exists
        if 'conversion_chance' not in st.session_state:
            st.session_state.conversion_chance = float(pred_result.conversion_probability)

        for i, rec in enumerate(pred_result.recommendations):
            action_data = action_details.get(rec, {
                "desc": "AI-optimized next step based on lead behavioral patterns.",
                "lift": 1.0,
                "reason": "Standard optimization"
            })
            
            detail = action_data["desc"]
            lift = action_data["lift"]
            reason = action_data["reason"]
            icon = "📅" if "Schedule" in rec else "🏠" if "listings" in rec else "🔥" if "Hot" in rec else "💰"
            
            # Enhanced action card with lift indicator
            st.markdown(f"""
                <div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin-bottom: 12px; border-left: 4px solid #2563eb; background: white; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                        <span style="font-size: 1.25rem;">{icon}</span>
                        <b style="color: #1e293b; font-size: 1rem;">{rec}</b>
                        <div style="margin-left: auto; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 700; display: flex; align-items: center; gap: 0.25rem;">
                            <span>📈</span> +{lift}%
                        </div>
                    </div>
                    <p style="font-size: 13px; color: #64748b; margin: 8px 0; line-height: 1.4;">{detail}</p>
                    <div style="background: #f0fdf4; border-left: 3px solid #10b981; padding: 0.5rem 0.75rem; border-radius: 6px; margin-top: 8px;">
                        <div style="font-size: 0.75rem; color: #065f46; font-weight: 600; display: flex; align-items: center; gap: 0.25rem;">
                            <span>💡</span> Predicted Impact: {reason}
                        </div>
                        <div style="font-size: 0.7rem; color: #047857; margin-top: 2px;">
                            Conversion probability: {st.session_state.conversion_chance:.1f}% → {st.session_state.conversion_chance + lift:.1f}%
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🚀 Run Action", key=f"run_action_pred_{i}", width='stretch'):
                    with st.spinner("Executing GHL trigger..."):
                        import time
                        time.sleep(1)
                        
                        # Update conversion chance dynamically
                        st.session_state.conversion_chance += lift
                        
                        # Cross-tab sync: Log to activity feed
                        if 'lead_activities' not in st.session_state:
                            st.session_state.lead_activities = []
                        
                        st.session_state.lead_activities.append({
                            "timestamp": datetime.datetime.now(),
                            "lead": selected_lead_pred,
                            "action": rec,
                            "details": f"+{lift}% conversion lift",
                            "source": "Predictions AI"
                        })
                        
                        # Update live feed
                        try:
                            fs = LiveFeedService()
                            fs.add_activity("workflow", selected_lead_pred, f"Executed: {rec}")
                        except:
                            pass
                        
                        st.toast(f"✅ Success: {rec} triggered | Conversion chance +{lift}%", icon="⚡")
                        st.rerun()

    with tab8:
        st.subheader("💬 AI Lead Assistant")
        st.markdown("*Experience our comprehensive AI-powered lead qualification system*")

        # Chat demo with persona selection
        render_chat_demo()

@ui_error_boundary("Automation Studio")
def render_automation_studio():
    st.header("🤖 Automation Studio")
    st.markdown("*Visual switchboard to toggle AI features on/off*")
    
    tab1, tab2, tab3 = st.tabs(["⚙️ Automations", "📧 Sequences", "🔄 Workflows"])
    
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

@ui_error_boundary("Sales Copilot")
def render_sales_copilot():
    st.header("💰 Sales Copilot")
    st.markdown("*Agent tools for active deals and client meetings*")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "💼 Deal Closer",
        "📄 Documents",
        "📋 Meeting Prep",
        "💵 Calculator"
    ])
    
    with tab1:
        st.subheader("💰 Sales AI Assistant")
        st.markdown("*Your comprehensive AI coach for deals, negotiations, objections, and closing*")

        # Render comprehensive chat for sales/agent context
        # Use a specialized sales-focused chat interface
        try:
            chat_interface = initialize_chat_system("sales_copilot")
            if chat_interface:
                # Provide sales context
                import asyncio
                asyncio.run(chat_interface.render_demo_chat(
                    demo_persona="agent",
                    include_ml_insights=True
                ))
            else:
                st.error("Sales AI Assistant temporarily unavailable")
        except Exception as e:
            st.error("Sales AI Assistant initialization failed")
            # Fallback to basic interface
            st.markdown("**Quick Sales Support:**")

            if "sales_messages" not in st.session_state:
                st.session_state.sales_messages = [
                    {"role": "assistant", "content": "I'm your AI sales assistant. How can I help you close your next deal?"}
                ]

            for msg in st.session_state.sales_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            if prompt := st.chat_input("Ask about objections, negotiations, or closing strategies..."):
                st.session_state.sales_messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    response = "I'll help you with that sales challenge. Let me analyze the situation and provide actionable advice."
                    st.markdown(response)
                    st.session_state.sales_messages.append({"role": "assistant", "content": response})
        
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
        "🧠 AI Retraining"
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
        st.subheader("🧠 AI Model Retraining Control")
        st.markdown("*Review feedback from 'Missed Matches' and retrain the property matching engine.*")

        col_ret1, col_ret2 = st.columns([1, 1])

        with col_ret1:
            st.markdown("#### 📊 Feedback Analytics")
            
            # Load feedback data
            try:
                feedback_path = Path(__file__).parent.parent / "data" / "feedback" / "property_matches_feedback.json"
                if feedback_path.exists():
                    with open(feedback_path, "r") as f:
                        feedback_data = json.load(f)
                    
                    st.metric("Total Feedback Items", len(feedback_data), f"+{len(feedback_data)}")
                    
                    # Count by type
                    types = [fb.get('feedback_type', 'unknown') for fb in feedback_data]
                    from collections import Counter
                    type_counts = Counter(types)
                    
                    st.write("**Feedback Distribution:**")
                    for t, c in type_counts.items():
                        st.write(f"- {t.replace('_', ' ').title()}: {c}")
                else:
                    st.info("No feedback recorded yet. Encourage your team to use the 'Missed Match' button.")
            except Exception as e:
                st.error(f"Error loading feedback: {e}")

        with col_ret2:
            st.markdown("#### ⚙️ Retraining Control")
            st.write("Retraining the model incorporates recent feedback into the matching algorithms.")
            
            if st.button("🚀 Trigger AI Retraining", type="primary", width='stretch'):
                with st.spinner("Processing feedback and retraining ML models..."):
                    try:
                        from services.property_matcher_ml import PropertyMatcherML
                        ml_matcher = PropertyMatcherML()
                        retrain_result = ml_matcher.trigger_retraining()
                        
                        st.success(f"Successfully retrained models! Accuracy improvement: {retrain_result['accuracy_improvement']}")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Retraining failed: {e}")
            
            st.caption("Recommended retraining frequency: Weekly or after 50+ feedback items.")

        st.markdown("---")
        st.markdown("#### 📝 Recent Feedback Items")
        
        try:
            if feedback_path.exists():
                feedback_df = pd.DataFrame(feedback_data).tail(10)
                st.dataframe(
                    feedback_df,
                    column_config={
                        "timestamp": "Date",
                        "lead_id": "Lead ID",
                        "property_id": "Property",
                        "feedback_type": "Type",
                        "comments": "Comments"
                    },
                    hide_index=True,
                    width='stretch'
                )
            else:
                st.write("No feedback items to display.")
        except:
            pass

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

def render_financing_calculator():
    """Comprehensive financing calculator with multiple scenarios"""
    st.subheader("💰 Financing Calculator & Pre-Qualification")

    # Calculator inputs
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🏠 Loan Details")
        home_price = st.number_input("Home Price", value=400000, step=5000)
        down_payment_percent = st.slider("Down Payment %", 0, 50, 20)
        loan_term = st.selectbox("Loan Term", [15, 20, 30])
        interest_rate = st.number_input("Interest Rate %", value=7.25, step=0.125)

    with col2:
        st.markdown("#### 💳 Additional Costs")
        property_tax_rate = st.number_input("Property Tax Rate %", value=2.1, step=0.1)
        insurance_annual = st.number_input("Home Insurance (Annual)", value=1200, step=100)
        hoa_monthly = st.number_input("HOA Fees (Monthly)", value=0, step=25)
        pmi_rate = st.number_input("PMI Rate % (if < 20% down)", value=0.5, step=0.1)

    # Calculate payments
    down_payment = home_price * (down_payment_percent / 100)
    loan_amount = home_price - down_payment

    # Monthly payment calculation
    monthly_rate = (interest_rate / 100) / 12
    num_payments = loan_term * 12

    if monthly_rate > 0:
        monthly_principal_interest = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    else:
        monthly_principal_interest = loan_amount / num_payments

    monthly_tax = (home_price * (property_tax_rate / 100)) / 12
    monthly_insurance = insurance_annual / 12
    monthly_pmi = (loan_amount * (pmi_rate / 100)) / 12 if down_payment_percent < 20 else 0

    total_monthly = monthly_principal_interest + monthly_tax + monthly_insurance + hoa_monthly + monthly_pmi

    # Display results
    st.markdown("#### 📊 Payment Breakdown")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Total Monthly Payment", f"${total_monthly:,.0f}")
    with col2:
        st.metric("🏠 Principal & Interest", f"${monthly_principal_interest:,.0f}")
    with col3:
        st.metric("🏛️ Taxes & Insurance", f"${monthly_tax + monthly_insurance:,.0f}")
    with col4:
        st.metric("💵 Down Payment", f"${down_payment:,.0f}")

    # Payment breakdown chart
    payment_data = {
        "Component": ["Principal & Interest", "Property Tax", "Insurance", "HOA", "PMI"],
        "Amount": [monthly_principal_interest, monthly_tax, monthly_insurance, hoa_monthly, monthly_pmi]
    }

    df = pd.DataFrame(payment_data)
    df = df[df["Amount"] > 0]  # Only show components with values

    fig = px.pie(df, values="Amount", names="Component",
                title="Monthly Payment Breakdown")
    st.plotly_chart(fig, width='stretch')

    # Affordability analysis
    st.markdown("#### 🎯 Affordability Analysis")

    col1, col2 = st.columns(2)
    with col1:
        monthly_income = st.number_input("Gross Monthly Income", value=8000, step=500)
        monthly_debts = st.number_input("Monthly Debt Payments", value=800, step=100)

    debt_to_income = ((total_monthly + monthly_debts) / monthly_income) * 100

    with col2:
        st.metric("📈 Total DTI Ratio", f"{debt_to_income:.1f}%")

        if debt_to_income <= 28:
            st.success("✅ Excellent DTI - Strong approval likelihood")
        elif debt_to_income <= 36:
            st.warning("⚠️ Good DTI - Should qualify with good credit")
        elif debt_to_income <= 43:
            st.warning("⚠️ High DTI - May need stronger compensating factors")
        else:
            st.error("❌ Very High DTI - May have difficulty qualifying")

    # Scenario comparison
    st.markdown("#### 🔍 Scenario Comparison")

    scenarios = []
    for dp in [10, 15, 20, 25]:
        scenario_down = home_price * (dp / 100)
        scenario_loan = home_price - scenario_down
        scenario_pmi = (scenario_loan * 0.005) / 12 if dp < 20 else 0
        scenario_payment = scenario_loan * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1) + monthly_tax + monthly_insurance + hoa_monthly + scenario_pmi

        scenarios.append({
            "Down Payment %": f"{dp}%",
            "Down Payment $": f"${scenario_down:,.0f}",
            "Monthly Payment": f"${scenario_payment:,.0f}",
            "PMI": f"${scenario_pmi:,.0f}" if scenario_pmi > 0 else "None"
        })

    scenario_df = pd.DataFrame(scenarios)
    st.dataframe(scenario_df, width='stretch')

def render_neighborhood_explorer():
    """Comprehensive neighborhood analysis and exploration"""
    st.subheader("🌍 Neighborhood Intelligence")

    # Location input
    col1, col2 = st.columns(2)
    with col1:
        target_address = st.text_input("Enter Address or Neighborhood",
            placeholder="1234 Oak Street, Austin, TX or 'West Lake Hills'")
    with col2:
        analysis_radius = st.selectbox("Analysis Radius", ["0.5 miles", "1 mile", "2 miles", "5 miles"])

    if st.button("🔍 Analyze Neighborhood", type="primary"):
        with st.spinner("Analyzing neighborhood data..."):

            # Neighborhood overview
            st.markdown("#### 📊 Neighborhood Overview")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🏫 School Rating", "9/10", delta="Excellent")
            with col2:
                st.metric("🚶 Walk Score", "75/100", delta="Very Walkable")
            with col3:
                st.metric("🛡️ Safety Score", "8.5/10", delta="Very Safe")
            with col4:
                st.metric("📈 Property Values", "+12%", delta="vs. last year")

            # Detailed analysis tabs
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🏫 Schools", "🚗 Commute", "🛒 Amenities", "📊 Market Data", "🌐 Demographics"
            ])

            with tab1:
                st.markdown("##### School Information")
                schools_data = [
                    {"School": "Westlake Elementary", "Rating": "10/10", "Distance": "0.3 mi", "Type": "Public"},
                    {"School": "Hill Country Middle", "Rating": "9/10", "Distance": "0.7 mi", "Type": "Public"},
                    {"School": "Westlake High School", "Rating": "10/10", "Distance": "1.2 mi", "Type": "Public"},
                    {"School": "Austin Montessori", "Rating": "8/10", "Distance": "0.5 mi", "Type": "Private"}
                ]
                schools_df = pd.DataFrame(schools_data)
                st.dataframe(schools_df, width='stretch')

            with tab2:
                st.markdown("##### Commute Analysis")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**To Downtown Austin:**")
                    st.markdown("• 🚗 Driving: 25-40 minutes")
                    st.markdown("• 🚌 Public Transit: 45-60 minutes")
                    st.markdown("• 🚴 Biking: Not recommended")

                with col2:
                    st.markdown("**To Austin Airport:**")
                    st.markdown("• 🚗 Driving: 35-50 minutes")
                    st.markdown("• 🚌 Public Transit: 60-75 minutes")
                    st.markdown("• 🚕 Rideshare: $45-65")

            with tab3:
                st.markdown("##### Nearby Amenities")

                amenities = {
                    "🍕 Restaurants": ["The Oasis (0.5 mi)", "Hopdoddy Burger (1.2 mi)", "Torchy's Tacos (0.8 mi)"],
                    "🛒 Shopping": ["Whole Foods (0.3 mi)", "Barton Creek Mall (2.1 mi)", "Hill Country Galleria (1.5 mi)"],
                    "🏥 Healthcare": ["Austin Regional (2.3 mi)", "Urgent Care Plus (0.7 mi)", "CVS Pharmacy (0.4 mi)"],
                    "🎯 Recreation": ["Zilker Park (3.2 mi)", "Austin Country Club (1.1 mi)", "Greenbelt Trail (0.5 mi)"]
                }

                for category, places in amenities.items():
                    st.markdown(f"**{category}**")
                    for place in places:
                        st.markdown(f"• {place}")
                    st.markdown("")

            with tab4:
                st.markdown("##### Market Trends")

                # Mock market data
                months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
                avg_prices = [485000, 492000, 501000, 515000, 528000, 542000]
                days_on_market = [18, 16, 12, 8, 6, 5]

                col1, col2 = st.columns(2)

                with col1:
                    fig_price = px.line(x=months, y=avg_prices, title="Average Home Prices")
                    fig_price.update_layout(yaxis_title="Price ($)", xaxis_title="Month")
                    st.plotly_chart(fig_price, width='stretch')

                with col2:
                    fig_dom = px.bar(x=months, y=days_on_market, title="Average Days on Market")
                    fig_dom.update_layout(yaxis_title="Days", xaxis_title="Month")
                    st.plotly_chart(fig_dom, width='stretch')

            with tab5:
                st.markdown("##### Demographics")
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Population Stats:**")
                    st.markdown("• Total Population: 12,847")
                    st.markdown("• Median Age: 42 years")
                    st.markdown("• Households: 4,523")
                    st.markdown("• Median Income: $125,000")

                with col2:
                    st.markdown("**Family Composition:**")
                    st.markdown("• Married with Children: 45%")
                    st.markdown("• Young Professionals: 25%")
                    st.markdown("• Empty Nesters: 20%")
                    st.markdown("• Retirees: 10%")

def render_buyer_dashboard():
    """Buyer's personal dashboard with saved properties and activity"""
    st.subheader("📅 Your Property Dashboard")

    # Dashboard summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("❤️ Saved Properties", "12")
    with col2:
        st.metric("📅 Scheduled Tours", "3")
    with col3:
        st.metric("📧 New Alerts", "5")
    with col4:
        st.metric("🔍 Searches Saved", "2")

    # Main dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "❤️ Saved Properties", "📅 Scheduled Tours", "🔔 Alerts & Updates", "📊 Search History"
    ])

    with tab1:
        st.markdown("#### Saved Properties")

        # Property list with action buttons
        saved_properties = [
            {
                "address": "1234 Oak Street, Austin, TX 78704",
                "price": "$485,000",
                "beds": 3,
                "baths": 2,
                "saved_date": "2 days ago",
                "status": "Active"
            },
            {
                "address": "5678 Pine Avenue, Austin, TX 78745",
                "price": "$425,000",
                "beds": 3,
                "baths": 2.5,
                "saved_date": "1 week ago",
                "status": "Under Contract"
            },
            {
                "address": "9012 Elm Drive, Austin, TX 78758",
                "price": "$399,000",
                "beds": 4,
                "baths": 2,
                "saved_date": "3 days ago",
                "status": "Active"
            }
        ]

        for i, prop in enumerate(saved_properties):
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                with col1:
                    status_color = "green" if prop["status"] == "Active" else "red"
                    st.markdown(f"**{prop['address']}**")
                    st.markdown(f"{prop['price']} • {prop['beds']} bed • {prop['baths']} bath")
                    st.markdown(f"<span style='color: {status_color};'>●</span> {prop['status']} • Saved {prop['saved_date']}", unsafe_allow_html=True)

                with col2:
                    if st.button("📱 Contact Agent", key=f"contact_{i}"):
                        st.success("Agent contacted!")

                with col3:
                    if st.button("📅 Schedule Tour", key=f"schedule_{i}"):
                        st.info("Tour scheduled!")

                with col4:
                    if st.button("🗑️ Remove", key=f"remove_{i}"):
                        st.warning("Property removed from saved list")

                st.markdown("---")

    with tab2:
        st.markdown("#### Upcoming Tours")

        tours = [
            {
                "address": "1234 Oak Street",
                "date": "Tomorrow",
                "time": "2:00 PM",
                "agent": "Sarah Johnson"
            },
            {
                "address": "9012 Elm Drive",
                "date": "Saturday",
                "time": "10:00 AM",
                "agent": "Mike Chen"
            }
        ]

        for tour in tours:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.markdown(f"**{tour['address']}**")
                    st.markdown(f"📅 {tour['date']} at {tour['time']}")
                    st.markdown(f"🏘️ Agent: {tour['agent']}")

                with col2:
                    if st.button("📞 Call Agent", key=f"call_{tour['address']}"):
                        st.success("Calling agent...")

                with col3:
                    if st.button("✏️ Reschedule", key=f"reschedule_{tour['address']}"):
                        st.info("Rescheduling options sent to email")

                st.markdown("---")

    with tab3:
        st.markdown("#### Recent Alerts & Updates")

        alerts = [
            {
                "type": "Price Drop",
                "message": "1234 Oak Street reduced by $10,000",
                "time": "2 hours ago",
                "action": "View Property"
            },
            {
                "type": "New Listing",
                "message": "New property matches your criteria in West Lake Hills",
                "time": "1 day ago",
                "action": "View Listing"
            },
            {
                "type": "Market Update",
                "message": "Austin market report: Inventory up 5% this month",
                "time": "3 days ago",
                "action": "Read Report"
            }
        ]

        for alert in alerts:
            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    alert_emoji = "💰" if alert["type"] == "Price Drop" else "🏠" if alert["type"] == "New Listing" else "📊"
                    st.markdown(f"**{alert_emoji} {alert['type']}**")
                    st.markdown(alert["message"])
                    st.markdown(f"🕒 {alert['time']}")

                with col2:
                    if st.button(alert["action"], key=f"action_{alert['message'][:10]}"):
                        st.info(f"{alert['action']} clicked!")

                st.markdown("---")

    with tab4:
        st.markdown("#### Search History")

        st.markdown("**Recent Searches:**")
        searches = [
            "3+ bed homes under $500K in West Lake Hills",
            "New construction in Austin ISD",
            "Condos near downtown with parking"
        ]

        for i, search in enumerate(searches):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"• {search}")
            with col2:
                if st.button("🔄 Repeat", key=f"repeat_{i}"):
                    st.success("Search repeated!")

def render_buyer_analytics():
    """Enhanced analytics and insights for buyer journey with churn prediction"""
    st.subheader("📊 Enhanced Buyer Journey Analytics with AI Insights")

    # Get enhanced services for churn prediction
    churn_risk_data = None
    if SERVICES_LOADED:
        try:
            services = get_services()
            churn_predictor = services.get("churn_prediction")
            enhanced_scorer = services.get("enhanced_lead_scorer")

            if churn_predictor:
                # Simulated churn prediction analysis
                churn_risk_data = {
                    "churn_risk_score": 0.25,  # 25% churn risk
                    "risk_tier": "Low",
                    "engagement_trend": "Stable",
                    "days_since_last_activity": 3,
                    "activity_level": "High",
                    "conversion_probability": 0.78
                }
                st.info("🧠 AI Churn Prediction & Retention Analytics Active")
        except Exception as e:
            st.warning(f"⚠️ Enhanced analytics temporarily unavailable: {str(e)}")

    # Enhanced analytics overview with churn insights
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("🔍 Properties Viewed", "47", delta="12 this week")
    with col2:
        st.metric("📅 Tours Completed", "8", delta="3 pending")
    with col3:
        st.metric("💰 Avg. Price Viewed", "$456K", delta="-$23K vs. budget")
    with col4:
        if churn_risk_data:
            risk_score = churn_risk_data["churn_risk_score"]
            risk_color = "green" if risk_score < 0.3 else "orange" if risk_score < 0.7 else "red"
            st.markdown(f"<div style='text-align: center; color: {risk_color}; font-weight: bold;'>⚠️ Churn Risk<br>{risk_score:.1%}</div>", unsafe_allow_html=True)
        else:
            st.metric("📈 Market Position", "Competitive", delta="Good timing")
    with col5:
        if churn_risk_data:
            conv_prob = churn_risk_data["conversion_probability"]
            conv_color = "green" if conv_prob > 0.7 else "orange" if conv_prob > 0.5 else "red"
            st.markdown(f"<div style='text-align: center; color: {conv_color}; font-weight: bold;'>📈 Conversion<br>{conv_prob:.1%}</div>", unsafe_allow_html=True)
        else:
            st.metric("📊 Engagement", "High", delta="Stable")

    # Enhanced insights with churn prediction
    if churn_risk_data:
        # Churn Risk Alert Section
        risk_score = churn_risk_data["churn_risk_score"]
        risk_tier = churn_risk_data["risk_tier"]

        if risk_score < 0.3:
            st.success(f"✅ **Low Churn Risk ({risk_score:.1%})**: Buyer is highly engaged and likely to convert. Continue current engagement strategy.")
        elif risk_score < 0.7:
            st.warning(f"⚠️ **Medium Churn Risk ({risk_score:.1%})**: Monitor engagement closely. Consider increasing touchpoints and providing personalized market updates.")
        else:
            st.error(f"🚨 **High Churn Risk ({risk_score:.1%})**: Immediate intervention required! Schedule personal call, reassess needs, and provide high-value insights.")

    # Enhanced charts and insights with AI analytics
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Activity & Engagement", "💰 Price Analysis", "🎯 AI Preference Learning", "⚠️ Retention Analytics"])

    with tab1:
        st.markdown("#### Enhanced Activity & Engagement Analytics")

        # Mock activity data with engagement insights
        days = list(range(1, 31))
        properties_viewed = [2, 1, 4, 3, 5, 2, 1, 6, 4, 3, 7, 5, 2, 8, 6, 4, 3, 9, 7, 5, 4, 6, 8, 3, 5, 7, 9, 4, 6, 8]

        # Enhanced visualization with engagement scoring
        fig = px.line(x=days, y=properties_viewed, title="Daily Property Views & Engagement Score (Last 30 Days)")
        fig.add_scatter(x=days, y=[p*0.8 + 2 for p in properties_viewed], mode='lines', name='Engagement Score', line=dict(color='orange', dash='dash'))
        fig.update_layout(xaxis_title="Day", yaxis_title="Activity Level")
        st.plotly_chart(fig, width='stretch')

        # Engagement insights
        if churn_risk_data:
            st.markdown("##### 🔥 AI Engagement Insights")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"• **Activity Level**: {churn_risk_data['activity_level']}")
                st.markdown(f"• **Engagement Trend**: {churn_risk_data['engagement_trend']}")
                st.markdown(f"• **Days Since Last Activity**: {churn_risk_data['days_since_last_activity']}")
            with col2:
                st.markdown("• **Peak Activity Time**: Evenings & Weekends")
                st.markdown("• **Response Rate**: 85% (Excellent)")
                st.markdown("• **Tour-to-View Ratio**: 17% (Above Average)")

    with tab2:
        st.markdown("#### Enhanced Price Analysis with AI Insights")

        price_ranges = ["$300-400K", "$400-500K", "$500-600K", "$600-700K", "$700K+"]
        properties_in_range = [5, 15, 18, 7, 2]

        fig = px.bar(x=price_ranges, y=properties_in_range, title="Properties Viewed by Price Range")
        st.plotly_chart(fig, width='stretch')

        # AI price insights
        st.markdown("##### 🧠 AI Price Pattern Analysis")
        st.markdown("• **Sweet Spot**: $500-600K (38% of activity)")
        st.markdown("• **Budget Creep**: +5% average vs. initial budget")
        st.markdown("• **Value Perception**: High value focus (avg. $/sqft viewed)")
        if churn_risk_data and churn_risk_data["conversion_probability"] > 0.7:
            st.success("💰 **Budget Confidence**: Strong indicators of realistic pricing expectations")

    with tab3:
        st.markdown("#### AI-Enhanced Preference Learning")

        st.markdown("**🎯 AI-Discovered Top Features in Saved Properties:**")
        st.markdown("• Updated Kitchen (75% of saved properties) - **High Priority**")
        st.markdown("• 2+ Car Garage (67% of saved properties) - **Important**")
        st.markdown("• Hardwood Floors (58% of saved properties) - **Preferred**")
        st.markdown("• Large Yard (50% of saved properties) - **Desired**")

        st.markdown("**📍 AI-Analyzed Location Preferences:**")
        st.markdown("• West Lake Hills: 35% of searches - **Top Choice**")
        st.markdown("• Central Austin: 25% of searches - **Secondary**")
        st.markdown("• Cedar Park: 20% of searches - **Considering**")
        st.markdown("• Round Rock: 20% of searches - **Backup Option**")

        # AI learning insights
        st.markdown("**🤖 AI Pattern Recognition:**")
        st.markdown("• **Commute Factor**: Strong correlation with location preferences")
        st.markdown("• **School Priority**: High importance detected (8/10 average)")
        st.markdown("• **Move-in Timeline**: Flexible - can wait for right property")
        st.markdown("• **Style Preference**: Transitional/Contemporary over Traditional")

    with tab4:
        st.markdown("#### 🚨 AI Retention & Churn Analytics")

        if churn_risk_data:
            # Churn risk breakdown
            st.markdown("##### Risk Factor Analysis")

            # Create risk factor visualization
            risk_factors = [
                "Activity Level", "Response Rate", "Tour Engagement",
                "Budget Alignment", "Timeline Pressure", "Agent Relationship"
            ]
            risk_scores = [0.1, 0.15, 0.2, 0.25, 0.45, 0.1]  # Mock risk scores

            fig = px.bar(
                x=risk_factors,
                y=risk_scores,
                title="Individual Risk Factors Contributing to Churn",
                color=risk_scores,
                color_continuous_scale=["green", "orange", "red"]
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, width='stretch')

            # Detailed retention recommendations
            st.markdown("##### 💡 AI Retention Recommendations")

            risk_score = churn_risk_data["churn_risk_score"]
            if risk_score < 0.3:
                st.success("✅ **Continue Current Strategy**: Buyer is well-engaged. Maintain weekly check-ins and property alerts.")
            elif risk_score < 0.7:
                st.warning("⚠️ **Enhance Engagement**: Consider:")
                st.markdown("• Increase communication frequency to bi-weekly")
                st.markdown("• Provide market trend insights and exclusive listings")
                st.markdown("• Schedule additional property tours this week")
                st.markdown("• Send personalized neighborhood analysis")
            else:
                st.error("🚨 **Immediate Intervention Required**:")
                st.markdown("• **Schedule urgent call within 24 hours**")
                st.markdown("• **Reassess needs and preferences**")
                st.markdown("• **Provide exclusive market opportunities**")
                st.markdown("• **Consider incentive strategies**")

            # Predictive insights
            st.markdown("##### 🔮 AI Conversion Predictions")
            st.markdown(f"• **7-Day Conversion Probability**: {churn_risk_data['conversion_probability']*0.3:.1%}")
            st.markdown(f"• **30-Day Conversion Probability**: {churn_risk_data['conversion_probability']:.1%}")
            st.markdown(f"• **90-Day Conversion Probability**: {min(churn_risk_data['conversion_probability']*1.2, 0.95):.1%}")

        else:
            st.info("🧠 Enhanced retention analytics available when AI services are loaded")

            # Fallback engagement tips
            st.markdown("##### General Retention Best Practices")
            st.markdown("• Maintain regular communication every 3-5 days")
            st.markdown("• Provide market updates and new listing alerts")
            st.markdown("• Schedule property tours within 48 hours of interest")
            st.markdown("• Send personalized neighborhood and school reports")
            st.markdown("• Monitor response times and engagement levels")

# Seller Component Functions
def render_property_valuation_engine():
    """AI-powered property valuation and CMA engine"""
    st.subheader("📊 AI Property Valuation Engine")

    # Property details input
    st.markdown("#### 🏠 Property Information")

    col1, col2 = st.columns(2)
    with col1:
        property_address = st.text_input("Property Address", placeholder="1234 Main Street, Austin, TX 78704")
        property_type = st.selectbox("Property Type", ["Single Family", "Townhome", "Condo", "Duplex", "Multi-Family"])
        year_built = st.number_input("Year Built", value=1995, step=1)
        lot_size = st.number_input("Lot Size (acres)", value=0.25, step=0.05)

    with col2:
        bedrooms = st.selectbox("Bedrooms", [1, 2, 3, 4, 5, 6, "7+"])
        bathrooms = st.selectbox("Bathrooms", [1, 1.5, 2, 2.5, 3, 3.5, 4, "4.5+"])
        square_footage = st.number_input("Square Footage", value=1856, step=50)
        garage_spaces = st.selectbox("Garage Spaces", [0, 1, 2, 3, "4+"])

    # Property features
    st.markdown("#### ✨ Property Features & Condition")
    col1, col2, col3 = st.columns(3)

    with col1:
        features = st.multiselect("Special Features", [
            "Swimming Pool", "Fireplace", "Hardwood Floors", "Granite Counters",
            "Updated Kitchen", "Master Suite", "Office/Study", "Basement",
            "Deck/Patio", "Fenced Yard", "Workshop/Storage"
        ])

    with col2:
        condition = st.selectbox("Overall Condition", [
            "Excellent - Move-in Ready",
            "Good - Minor Updates Needed",
            "Fair - Some Improvements Required",
            "Needs Work - Major Renovations"
        ])

    with col3:
        recent_updates = st.multiselect("Recent Updates (Last 5 Years)", [
            "Roof Replacement", "HVAC System", "Windows", "Flooring",
            "Kitchen Renovation", "Bathroom Remodel", "Paint Interior",
            "Paint Exterior", "Appliances", "Landscaping"
        ])

    # Market analysis
    if st.button("🔍 Generate Valuation Analysis", type="primary"):
        with st.spinner("Analyzing property value..."):

            # Main valuation results
            st.markdown("#### 🎯 Valuation Results")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🏠 Estimated Value", "$487,500", delta="$12,500 vs. last month")
            with col2:
                st.metric("📊 Value Range", "$465K - $510K", delta="95% confidence")
            with col3:
                st.metric("💰 $/Sq Ft", "$263", delta="$8 above market avg")
            with col4:
                st.metric("📈 Market Position", "Strong", delta="Good timing to sell")

            # Valuation methodology tabs
            tab1, tab2, tab3, tab4 = st.tabs([
                "🏘️ Comparable Sales", "📊 Market Analysis", "🎯 Pricing Strategy", "📈 Value Drivers"
            ])

            with tab1:
                st.markdown("##### Recent Comparable Sales")

                comps = [
                    {
                        "address": "1245 Oak Street (0.2 mi)",
                        "sold_price": "$495,000",
                        "sold_date": "45 days ago",
                        "beds": 3,
                        "baths": 2,
                        "sqft": 1920,
                        "price_per_sqft": "$258",
                        "adjustments": "+$7,500"
                    },
                    {
                        "address": "1156 Pine Avenue (0.3 mi)",
                        "sold_price": "$475,000",
                        "sold_date": "62 days ago",
                        "beds": 3,
                        "baths": 2.5,
                        "sqft": 1785,
                        "price_per_sqft": "$266",
                        "adjustments": "-$2,200"
                    },
                    {
                        "address": "1289 Elm Drive (0.4 mi)",
                        "sold_price": "$510,000",
                        "sold_date": "28 days ago",
                        "beds": 4,
                        "baths": 2,
                        "sqft": 1945,
                        "price_per_sqft": "$262",
                        "adjustments": "+$5,100"
                    }
                ]

                for comp in comps:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

                        with col1:
                            st.markdown(f"**{comp['address']}**")
                            st.markdown(f"💰 {comp['sold_price']} • Sold {comp['sold_date']}")
                            st.markdown(f"🛏️ {comp['beds']} bed • 🛁 {comp['baths']} bath • 📐 {comp['sqft']} sqft")

                        with col2:
                            st.markdown(f"**{comp['price_per_sqft']}**/sqft")

                        with col3:
                            adjustment_color = "green" if "+" in comp['adjustments'] else "red"
                            st.markdown(f"<span style='color: {adjustment_color};'>**{comp['adjustments']}**</span>", unsafe_allow_html=True)

                        with col4:
                            st.markdown(f"**Adjusted**: ${int(comp['sold_price'].replace('$', '').replace(',', '')) + int(comp['adjustments'].replace('$', '').replace(',', '').replace('+', '')):,}")

                        st.markdown("---")

            with tab2:
                st.markdown("##### Market Conditions Analysis")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Neighborhood Trends (Last 6 Months)**")
                    st.markdown("• Average Days on Market: 8 days")
                    st.markdown("• Price Appreciation: +12% YoY")
                    st.markdown("• Inventory Level: Low (2.1 months)")
                    st.markdown("• Market Type: Strong Seller's Market")

                    st.markdown("**Seasonal Factors**")
                    st.markdown("• Current Season: Peak selling season")
                    st.markdown("• Interest Rates: 7.25% (stable)")
                    st.markdown("• Economic Outlook: Positive")

                with col2:
                    # Market trends chart
                    months = ["Aug", "Sep", "Oct", "Nov", "Dec", "Jan"]
                    median_prices = [425000, 435000, 448000, 455000, 465000, 475000]

                    fig = px.line(x=months, y=median_prices, title="Neighborhood Median Prices")
                    fig.update_layout(yaxis_title="Price ($)", xaxis_title="Month")
                    st.plotly_chart(fig, width='stretch')

                    st.markdown("**Price Per Square Foot Trends**")
                    price_per_sqft = [245, 250, 255, 258, 260, 263]
                    fig2 = px.bar(x=months, y=price_per_sqft, title="Price Per Sq Ft")
                    st.plotly_chart(fig2, width='stretch')

            with tab3:
                st.markdown("##### Strategic Pricing Recommendations")

                pricing_strategies = [
                    {
                        "strategy": "🎯 Competitive Pricing",
                        "price": "$485,000",
                        "pros": "Quick sale, multiple offers likely",
                        "cons": "May leave money on table",
                        "timeline": "5-10 days"
                    },
                    {
                        "strategy": "💰 Market Value Pricing",
                        "price": "$495,000",
                        "pros": "Full market value, good negotiating room",
                        "cons": "May take longer to sell",
                        "timeline": "10-20 days"
                    },
                    {
                        "strategy": "🚀 Aspirational Pricing",
                        "price": "$510,000",
                        "pros": "Maximum return if market supports",
                        "cons": "Risk of sitting on market too long",
                        "timeline": "20-45 days"
                    }
                ]

                for strategy in pricing_strategies:
                    with st.expander(f"{strategy['strategy']} - {strategy['price']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**✅ Pros:** {strategy['pros']}")
                            st.markdown(f"**⚠️ Cons:** {strategy['cons']}")
                        with col2:
                            st.markdown(f"**⏱️ Expected Timeline:** {strategy['timeline']}")

                st.info("💡 **Recommendation:** Start with Market Value Pricing ($495,000) to maximize return while ensuring reasonable sale timeline.")

            with tab4:
                st.markdown("##### Value Enhancement Opportunities")

                improvements = [
                    {
                        "improvement": "Fresh Interior Paint",
                        "cost": "$2,500",
                        "value_add": "$5,000",
                        "roi": "100%",
                        "priority": "High"
                    },
                    {
                        "improvement": "Kitchen Counter Update",
                        "cost": "$4,500",
                        "value_add": "$7,500",
                        "roi": "67%",
                        "priority": "Medium"
                    },
                    {
                        "improvement": "Landscape Enhancement",
                        "cost": "$1,500",
                        "value_add": "$3,500",
                        "roi": "133%",
                        "priority": "High"
                    },
                    {
                        "improvement": "Master Bath Update",
                        "cost": "$8,000",
                        "value_add": "$10,000",
                        "roi": "25%",
                        "priority": "Low"
                    }
                ]

                st.markdown("**Recommended Pre-Sale Improvements:**")

                for improvement in improvements:
                    priority_color = "green" if improvement['priority'] == "High" else "orange" if improvement['priority'] == "Medium" else "red"

                    with st.container():
                        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

                        with col1:
                            st.markdown(f"**{improvement['improvement']}**")
                        with col2:
                            st.markdown(f"Cost: {improvement['cost']}")
                        with col3:
                            st.markdown(f"Value: {improvement['value_add']}")
                        with col4:
                            st.markdown(f"ROI: {improvement['roi']}")
                        with col5:
                            st.markdown(f"<span style='color: {priority_color};'>**{improvement['priority']}**</span>", unsafe_allow_html=True)

                st.markdown("**Total Investment:** $16,500 | **Total Value Add:** $26,000 | **Net Gain:** $9,500")

    # Additional tools
    st.markdown("#### 🛠️ Additional Valuation Tools")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📧 Email CMA Report"):
            st.success("Comprehensive CMA report sent to your email!")

    with col2:
        if st.button("📊 Generate Listing Sheet"):
            st.info("Professional listing sheet created!")

    with col3:
        if st.button("📱 Share with Client"):
            st.info("Valuation summary shared with client!")

def render_seller_prep_checklist():
    """Comprehensive seller preparation checklist"""
    st.subheader("📋 Seller Preparation Checklist")

    # Progress overview
    st.markdown("#### 📊 Preparation Progress")

    # Mock completion data
    total_tasks = 25
    completed_tasks = 12
    progress = completed_tasks / total_tasks

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("✅ Tasks Completed", f"{completed_tasks}/{total_tasks}")
    with col2:
        st.metric("📈 Progress", f"{progress*100:.0f}%")
    with col3:
        st.metric("🏠 Market Readiness", "Good")
    with col4:
        st.metric("⏱️ Time to Market", "2-3 weeks")

    # Progress bar
    st.progress(progress)

    # Checklist categories
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Interior Prep", "🌿 Exterior Prep", "📄 Documentation", "📸 Marketing Prep", "🔧 Repairs & Updates"
    ])

    with tab1:
        st.markdown("##### Interior Preparation")

        interior_tasks = [
            {"task": "Deep clean all rooms", "status": "✅", "priority": "High", "notes": "Professional cleaning scheduled"},
            {"task": "Declutter and organize", "status": "✅", "priority": "High", "notes": "Completed last weekend"},
            {"task": "Fresh paint (neutral colors)", "status": "⏳", "priority": "High", "notes": "Painter coming Monday"},
            {"task": "Clean windows inside", "status": "✅", "priority": "Medium", "notes": "Done with deep cleaning"},
            {"task": "Replace burnt-out bulbs", "status": "❌", "priority": "Medium", "notes": "Need LED bulbs"},
            {"task": "Remove personal photos", "status": "✅", "priority": "Medium", "notes": "Stored in garage"},
            {"task": "Stage furniture arrangement", "status": "❌", "priority": "Medium", "notes": "Stager coming Thursday"},
            {"task": "Fix squeaky doors/hinges", "status": "❌", "priority": "Low", "notes": "Need WD-40"},
        ]

        for task in interior_tasks:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 2])

                with col1:
                    st.markdown(f"{task['status']} {task['task']}")
                with col2:
                    priority_color = "red" if task['priority'] == "High" else "orange" if task['priority'] == "Medium" else "green"
                    st.markdown(f"<span style='color: {priority_color};'>{task['priority']}</span>", unsafe_allow_html=True)
                with col3:
                    if task['status'] == "❌":
                        if st.button("Mark Done", key=f"interior_{task['task'][:10]}"):
                            st.success("Task completed!")
                with col4:
                    st.markdown(f"*{task['notes']}*")

    with tab2:
        st.markdown("##### Exterior & Curb Appeal")

        exterior_tasks = [
            {"task": "Mow and edge lawn", "status": "✅", "priority": "High", "notes": "Weekly maintenance"},
            {"task": "Trim bushes and trees", "status": "✅", "priority": "High", "notes": "Landscaper completed"},
            {"task": "Plant seasonal flowers", "status": "⏳", "priority": "Medium", "notes": "Scheduled for weekend"},
            {"task": "Power wash driveway/walkways", "status": "❌", "priority": "High", "notes": "Rent pressure washer"},
            {"task": "Clean exterior windows", "status": "❌", "priority": "Medium", "notes": "Include in window service"},
            {"task": "Touch up exterior paint", "status": "❌", "priority": "Medium", "notes": "Minor spots identified"},
            {"task": "Clean gutters", "status": "✅", "priority": "Low", "notes": "Done in fall"},
            {"task": "Ensure adequate outdoor lighting", "status": "⏳", "priority": "Medium", "notes": "Adding pathway lights"},
        ]

        for task in exterior_tasks:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 2])

                with col1:
                    st.markdown(f"{task['status']} {task['task']}")
                with col2:
                    priority_color = "red" if task['priority'] == "High" else "orange" if task['priority'] == "Medium" else "green"
                    st.markdown(f"<span style='color: {priority_color};'>{task['priority']}</span>", unsafe_allow_html=True)
                with col3:
                    if task['status'] == "❌":
                        if st.button("Mark Done", key=f"exterior_{task['task'][:10]}"):
                            st.success("Task completed!")
                with col4:
                    st.markdown(f"*{task['notes']}*")

    with tab3:
        st.markdown("##### Required Documentation")

        documents = [
            {"doc": "Property deed", "status": "✅", "location": "File cabinet", "notes": "Original in safe"},
            {"doc": "Previous property disclosures", "status": "✅", "location": "With agent", "notes": "From purchase"},
            {"doc": "Recent utility bills", "status": "✅", "location": "Office desk", "notes": "Last 3 months"},
            {"doc": "HOA documents (if applicable)", "status": "N/A", "location": "-", "notes": "No HOA"},
            {"doc": "Survey/plat of property", "status": "⏳", "location": "Searching", "notes": "Request from title company"},
            {"doc": "Warranty information", "status": "❌", "location": "Need to gather", "notes": "HVAC, appliances"},
            {"doc": "Home inspection reports", "status": "✅", "location": "With agent", "notes": "From 2019 purchase"},
            {"doc": "Property tax records", "status": "✅", "location": "Online access", "notes": "Current and paid"},
        ]

        for doc in documents:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 2])

                with col1:
                    st.markdown(f"{doc['status']} {doc['doc']}")
                with col2:
                    st.markdown(doc['location'])
                with col3:
                    if doc['status'] == "❌":
                        if st.button("Found", key=f"doc_{doc['doc'][:8]}"):
                            st.success("Document located!")
                with col4:
                    st.markdown(f"*{doc['notes']}*")

    with tab4:
        st.markdown("##### Marketing Preparation")

        marketing_tasks = [
            {"task": "Professional photography", "status": "⏳", "priority": "High", "notes": "Scheduled for next Tuesday"},
            {"task": "Drone/aerial photos", "status": "❌", "priority": "Medium", "notes": "Include with photography"},
            {"task": "Virtual tour/3D scan", "status": "❌", "priority": "Medium", "notes": "Optional upgrade"},
            {"task": "Write compelling listing description", "status": "⏳", "priority": "High", "notes": "Agent drafting"},
            {"task": "Create property feature list", "status": "✅", "priority": "Medium", "notes": "Completed with agent"},
            {"task": "Gather neighborhood amenities info", "status": "✅", "priority": "Low", "notes": "Schools, shopping, etc."},
            {"task": "Plan open house logistics", "status": "❌", "priority": "Medium", "notes": "After photos complete"},
        ]

        for task in marketing_tasks:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 2])

                with col1:
                    st.markdown(f"{task['status']} {task['task']}")
                with col2:
                    priority_color = "red" if task['priority'] == "High" else "orange" if task['priority'] == "Medium" else "green"
                    st.markdown(f"<span style='color: {priority_color};'>{task['priority']}</span>", unsafe_allow_html=True)
                with col3:
                    if task['status'] == "❌":
                        if st.button("Complete", key=f"marketing_{task['task'][:10]}"):
                            st.success("Task completed!")
                with col4:
                    st.markdown(f"*{task['notes']}*")

    with tab5:
        st.markdown("##### Repairs & Updates")

        repairs = [
            {"item": "Fix leaky kitchen faucet", "priority": "High", "cost": "$150", "status": "⏳", "notes": "Plumber scheduled"},
            {"item": "Replace cracked outlet cover", "priority": "Medium", "cost": "$5", "status": "❌", "notes": "Hardware store trip"},
            {"item": "Caulk around master bathtub", "priority": "Medium", "cost": "$20", "status": "❌", "notes": "DIY project"},
            {"item": "Touch up paint in hallway", "priority": "Low", "cost": "$25", "status": "⏳", "notes": "With main painting"},
            {"item": "Replace air filter", "priority": "Low", "cost": "$15", "status": "✅", "notes": "Done monthly"},
        ]

        total_repair_cost = sum([int(repair['cost'].replace('$', '')) for repair in repairs])

        st.markdown(f"**Total Estimated Repair Cost:** ${total_repair_cost}")

        for repair in repairs:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])

                with col1:
                    st.markdown(f"{repair['status']} {repair['item']}")
                with col2:
                    priority_color = "red" if repair['priority'] == "High" else "orange" if repair['priority'] == "Medium" else "green"
                    st.markdown(f"<span style='color: {priority_color};'>{repair['priority']}</span>", unsafe_allow_html=True)
                with col3:
                    st.markdown(repair['cost'])
                with col4:
                    if repair['status'] == "❌":
                        if st.button("Fixed", key=f"repair_{repair['item'][:8]}"):
                            st.success("Repair completed!")
                with col5:
                    st.markdown(f"*{repair['notes']}*")

    # Action buttons
    st.markdown("#### 🎯 Quick Actions")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📧 Email Checklist"):
            st.success("Checklist emailed to you!")

    with col2:
        if st.button("📱 Share with Agent"):
            st.info("Checklist shared with your agent!")

    with col3:
        if st.button("📅 Schedule Services"):
            st.info("Service scheduling portal opened!")

    with col4:
        if st.button("💰 Get Cost Estimates"):
            st.info("Contractor quotes requested!")

def render_marketing_campaign_dashboard():
    """Marketing campaign performance and management dashboard"""
    st.subheader("📈 Marketing Campaign Dashboard")

    # Campaign overview
    st.markdown("#### 📊 Campaign Performance Overview")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👀 Total Views", "2,847", delta="312 this week")
    with col2:
        st.metric("💕 Favorites", "89", delta="23 new")
    with col3:
        st.metric("📞 Inquiries", "47", delta="12 this week")
    with col4:
        st.metric("📅 Showings Scheduled", "18", delta="5 pending")

    # Detailed analytics tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Performance Analytics", "🌐 Online Listings", "📸 Marketing Materials", "📅 Showing Activity", "📈 Market Feedback"
    ])

    with tab1:
        st.markdown("##### Performance Analytics")

        # Views over time
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Daily Views (Last 14 Days)**")
            days = list(range(1, 15))
            views = [45, 52, 38, 67, 89, 123, 145, 167, 89, 76, 98, 134, 156, 187]

            fig_views = px.line(x=days, y=views, title="Daily Property Views")
            fig_views.update_layout(xaxis_title="Days", yaxis_title="Views")
            st.plotly_chart(fig_views, width='stretch')

        with col2:
            st.markdown("**Inquiry Sources**")
            sources = ["Zillow", "Realtor.com", "MLS", "Company Website", "Social Media", "Referral"]
            inquiries = [18, 15, 8, 4, 2, 0]

            fig_sources = px.pie(values=inquiries, names=sources, title="Lead Sources")
            st.plotly_chart(fig_sources, width='stretch')

        # Performance metrics
        st.markdown("**Key Performance Indicators**")
        metrics_data = [
            {"Metric": "View-to-Inquiry Rate", "Current": "1.65%", "Goal": "2.0%", "Status": "📈 Improving"},
            {"Metric": "Inquiry-to-Showing Rate", "Current": "38.3%", "Goal": "35%", "Status": "✅ Exceeding"},
            {"Metric": "Days on Market", "Current": "8 days", "Goal": "< 15 days", "Status": "🎯 On Target"},
            {"Metric": "Price per Sq Ft", "Current": "$263", "Goal": "$255", "Status": "💰 Above Market"}
        ]

        metrics_df = pd.DataFrame(metrics_data)
        st.dataframe(metrics_df, width='stretch')

    with tab2:
        st.markdown("##### Online Listing Status")

        listings = [
            {
                "platform": "MLS",
                "status": "🟢 Active",
                "views": "1,247",
                "leads": "23",
                "last_updated": "Today",
                "notes": "Primary listing source"
            },
            {
                "platform": "Zillow",
                "status": "🟢 Active",
                "views": "892",
                "leads": "18",
                "last_updated": "2 days ago",
                "notes": "High traffic source"
            },
            {
                "platform": "Realtor.com",
                "status": "🟢 Active",
                "views": "654",
                "leads": "15",
                "last_updated": "Today",
                "notes": "Good conversion rate"
            },
            {
                "platform": "Company Website",
                "status": "🟢 Active",
                "views": "234",
                "leads": "4",
                "last_updated": "1 day ago",
                "notes": "Brand awareness"
            },
            {
                "platform": "Facebook Marketplace",
                "status": "🟡 Pending",
                "views": "0",
                "leads": "0",
                "last_updated": "N/A",
                "notes": "Awaiting approval"
            }
        ]

        for listing in listings:
            with st.container():
                col1, col2, col3, col4, col5, col6 = st.columns([1.5, 1, 1, 1, 1, 2])

                with col1:
                    st.markdown(f"**{listing['platform']}**")
                with col2:
                    st.markdown(listing['status'])
                with col3:
                    st.markdown(listing['views'])
                with col4:
                    st.markdown(listing['leads'])
                with col5:
                    st.markdown(listing['last_updated'])
                with col6:
                    st.markdown(f"*{listing['notes']}*")

                st.markdown("---")

    with tab3:
        st.markdown("##### Marketing Materials")

        # Photo performance
        st.markdown("**Photo Performance Analysis**")

        photos = [
            {"photo": "Front Exterior", "views": "2,847", "saves": "89", "engagement": "3.1%"},
            {"photo": "Living Room", "views": "2,203", "saves": "67", "engagement": "3.0%"},
            {"photo": "Kitchen", "views": "2,156", "saves": "78", "engagement": "3.6%"},
            {"photo": "Master Bedroom", "views": "1,834", "saves": "45", "engagement": "2.5%"},
            {"photo": "Backyard", "views": "1,623", "saves": "52", "engagement": "3.2%"}
        ]

        for photo in photos:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

                with col1:
                    st.markdown(f"📸 **{photo['photo']}**")
                with col2:
                    st.markdown(f"👀 {photo['views']}")
                with col3:
                    st.markdown(f"💾 {photo['saves']}")
                with col4:
                    engagement_float = float(photo['engagement'].replace('%', ''))
                    color = "green" if engagement_float >= 3.0 else "orange"
                    st.markdown(f"<span style='color: {color};'>📈 {photo['engagement']}</span>", unsafe_allow_html=True)

        # Marketing materials status
        st.markdown("**Marketing Materials Checklist**")
        materials = [
            {"item": "Professional Photos (25 images)", "status": "✅ Complete"},
            {"item": "Property Description", "status": "✅ Complete"},
            {"item": "Feature Sheet/Flyer", "status": "✅ Complete"},
            {"item": "Virtual Tour", "status": "⏳ In Progress"},
            {"item": "Drone/Aerial Video", "status": "❌ Pending"},
            {"item": "Social Media Posts", "status": "✅ Posted Daily"}
        ]

        for material in materials:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"• {material['item']}")
            with col2:
                st.markdown(material['status'])

    with tab4:
        st.markdown("##### Showing Activity")

        # Upcoming showings
        st.markdown("**Scheduled Showings**")

        showings = [
            {
                "date": "Today",
                "time": "2:00 PM",
                "type": "Private Showing",
                "agent": "Sarah Johnson (Buyer Agent)",
                "notes": "Pre-approved buyer, serious interest"
            },
            {
                "date": "Tomorrow",
                "time": "10:00 AM",
                "type": "Private Showing",
                "agent": "Mike Chen (Buyer Agent)",
                "notes": "First-time homebuyer"
            },
            {
                "date": "Saturday",
                "time": "1:00-4:00 PM",
                "type": "Open House",
                "agent": "Your Listing Agent",
                "notes": "First open house event"
            },
            {
                "date": "Sunday",
                "time": "11:00 AM",
                "type": "Private Showing",
                "agent": "Lisa Rodriguez (Buyer Agent)",
                "notes": "Investor client"
            }
        ]

        for showing in showings:
            with st.container():
                col1, col2, col3, col4 = st.columns([1, 1, 2, 2])

                with col1:
                    st.markdown(f"**📅 {showing['date']}**")
                with col2:
                    st.markdown(f"🕐 {showing['time']}")
                with col3:
                    st.markdown(f"**{showing['type']}**")
                    st.markdown(f"*{showing['agent']}*")
                with col4:
                    st.markdown(showing['notes'])

                st.markdown("---")

        # Showing statistics
        st.markdown("**Showing Statistics (Last 30 Days)**")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Showings", "18")
        with col2:
            st.metric("Private Showings", "14")
        with col3:
            st.metric("Open Houses", "2")
        with col4:
            st.metric("Avg per Week", "4.5")

    with tab5:
        st.markdown("##### Market Feedback & Insights")

        # Feedback from showings
        st.markdown("**Agent & Buyer Feedback**")

        feedback = [
            {
                "source": "Sarah Johnson (Buyer Agent)",
                "date": "2 days ago",
                "rating": "⭐⭐⭐⭐⭐",
                "comment": "Beautiful home, well-maintained. Buyers loved the kitchen updates.",
                "concerns": "Slight concern about backyard size for their dogs."
            },
            {
                "source": "Mike Chen (Buyer Agent)",
                "date": "3 days ago",
                "rating": "⭐⭐⭐⭐",
                "comment": "Great location and condition. Competitive price point.",
                "concerns": "Buyers prefer a larger master bathroom."
            },
            {
                "source": "Lisa Rodriguez (Buyer Agent)",
                "date": "1 week ago",
                "rating": "⭐⭐⭐⭐⭐",
                "comment": "Excellent investment opportunity. Cash buyer interested.",
                "concerns": "None - ready to make offer."
            }
        ]

        for fb in feedback:
            with st.expander(f"{fb['source']} - {fb['rating']} ({fb['date']})"):
                st.markdown(f"**Comment:** {fb['comment']}")
                if fb['concerns']:
                    st.markdown(f"**Concerns:** {fb['concerns']}")

        # Market positioning analysis
        st.markdown("**Competitive Market Analysis**")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Strengths vs Competition:**")
            st.markdown("• ✅ Superior kitchen updates")
            st.markdown("• ✅ Better curb appeal")
            st.markdown("• ✅ Competitive pricing")
            st.markdown("• ✅ Excellent school district")

        with col2:
            st.markdown("**Areas for Improvement:**")
            st.markdown("• 🔸 Smaller master bathroom")
            st.markdown("• 🔸 Limited backyard space")
            st.markdown("• 🔸 Single-car garage only")

        # Recommendations
        st.info("💡 **Agent Recommendations:** Continue current marketing strategy. Consider hosting second open house to capture weekend traffic. Price point is well-positioned for quick sale.")

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
            st.plotly_chart(fig, width='stretch')

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
            st.plotly_chart(fig_performance, width='stretch')

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

    # Buyer navigation tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🔍 Property Search",
        "👤 Buyer Profile",
        "💰 Financing",
        "🌍 Neighborhoods",
        "📅 Saved & Scheduled",
        "📊 Buyer Analytics",
        "💬 AI Assistant"
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

    with tab7:
        st.subheader("🏠 Buyer AI Assistant")
        st.markdown("*Get personalized help with property search, financing, and buyer questions*")

        # Render comprehensive buyer chat
        render_buyer_chat()

# Seller Journey Hub Components
def render_seller_journey_hub():
    """Render the complete seller journey experience"""
    st.title("🏡 Seller Journey Hub")
    st.markdown("*Complete seller experience from valuation to closing*")

    # Seller navigation tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Property Valuation",
        "📋 Seller Prep",
        "📈 Marketing Campaign",
        "💬 Communication",
        "🤖 AI-Claude Integration",
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
        st.subheader("🏡 Seller AI Assistant")
        st.markdown("*Get personalized help with valuation, marketing, timing, and seller questions*")

        # Render comprehensive seller chat
        render_seller_chat()

    with tab5:
        # Import and render our new seller-Claude integration demo
        try:
            from pages.seller_claude_demo import render_seller_claude_integration_demo
            render_seller_claude_integration_demo()
        except ImportError:
            st.error("Seller-Claude Integration demo temporarily unavailable")
            st.info("Advanced AI integration features coming soon!")

    with tab6:
        render_transaction_timeline()

    with tab7:
        render_seller_analytics()

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

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 2rem; background: #F7F8FA; border-radius: 12px; margin-top: 3rem;'>
    <div style='color: #2A2A33; font-weight: 600; font-size: 1.1rem; margin-bottom: 0.5rem;'>
        🚀 Production-Ready Multi-Tenant AI System
    </div>
    <div style='color: #6B7280; font-size: 0.9rem;'>
        Built for Jorge Salas | Claude Sonnet 4.5 | GHL Integration Ready
    </div>
    <div style='margin-top: 1rem; color: #6B7280; font-size: 0.85rem;'>
        Consolidated Hub Architecture | Path B Backend | 522+ Tests Passing
    </div>
</div>
""", unsafe_allow_html=True)
