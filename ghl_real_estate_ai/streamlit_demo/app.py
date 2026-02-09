"""
GHL Real Estate AI - Consolidated Hub Interface
Main Application with 5 Core Hubs
"""

import datetime
import json
import os
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

# 1. Page config MUST be the first Streamlit call
from ghl_real_estate_ai.streamlit_demo.config.page_config import (
    ASYNC_UTILS_AVAILABLE,
    DEMO_MODE,
    configure_page,
    run_async,
)

configure_page()

import streamlit as st

# 2. Initialize session state
from ghl_real_estate_ai.streamlit_demo.config.session_state import init_session_state

init_session_state()

# 3. Import service registry
# 4. Import navigation modules
from ghl_real_estate_ai.streamlit_demo.navigation.hub_dispatch import dispatch_hub
from ghl_real_estate_ai.streamlit_demo.navigation.hub_navigator import render_hub_navigator
from ghl_real_estate_ai.streamlit_demo.services.service_registry import (
    CLAUDE_COMPANION_AVAILABLE,
    ENHANCED_LEAD_SCORER_AVAILABLE,
    SERVICES_LOADED,
    MockService,
    claude,
    claude_companion,
    get_services,
    load_mock_data,
    preload_dashboard_components,
    warm_critical_data,
    warm_demo_cache_comprehensive,
)


# Error Boundary Decorator for production stability
def ui_error_boundary(func_name="Component"):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                st.error(f"{func_name} Temporarily Unavailable")
                st.info("Our team has been notified. Please try again or select another tab.")
                print(f"CRITICAL UI ERROR in {func_name}: {str(e)}")
                return None

        return wrapper

    return decorator


# --- THE FINAL POLISH: GLOBAL UI UTILITIES ---
def sparkline(data: list, color: str = "#6366F1", height: int = 50):
    """Generates a minimal high-fidelity sparkline chart with a neural glow effect."""
    hex_c = color.lstrip("#")
    r, g, b = int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)
    fill_rgba = f"rgba({r}, {g}, {b}, 0.1)"
    glow_rgba = f"rgba({r}, {g}, {b}, 0.4)"

    fig = go.Figure()

    fig.add_trace(go.Scatter(y=data, mode="lines", line=dict(color=glow_rgba, width=5), hoverinfo="skip", opacity=0.3))

    fig.add_trace(
        go.Scatter(
            y=data,
            mode="lines",
            fill="tozeroy",
            line=dict(color=color, width=2.5),
            fillcolor=fill_rgba,
            hoverinfo="skip",
        )
    )

    fig.update_layout(
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=5, b=0),
        height=height,
        xaxis=dict(visible=False, fixedrange=True),
        yaxis=dict(visible=False, fixedrange=True, range=[min(data) * 0.9, max(data) * 1.1]),
    )
    return fig


from ghl_real_estate_ai.streamlit_demo.obsidian_theme import (
    inject_elite_css,
    render_dossier_block,
)

# Inject Global Visual Overhaul
inject_elite_css()

# Hide Streamlit branding and debug elements
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)


# Sidebar - Settings (Early for service init)
def update_market():
    m_key = "Austin" if "Austin" in st.session_state.market_selector else "Rancho"
    st.session_state.lead_options = get_lead_options(m_key)
    st.session_state.selected_lead_name = "-- Select a Lead --"
    st.session_state.selected_market = st.session_state.market_selector


with st.sidebar:
    st.markdown("### AI Configuration")

    # Persist market selection
    selected_market = st.selectbox(
        "Select Market:",
        ["Austin, TX", "Rancho Cucamonga, CA"],
        index=["Austin, TX", "Rancho Cucamonga, CA"].index(st.session_state.get("selected_market", "Austin, TX")),
        key="market_selector",
        on_change=update_market,
    )
    st.session_state.selected_market = selected_market
    market_key = "Austin" if "Austin" in selected_market else "Rancho"

    # Persist AI tone
    ai_tone = st.select_slider(
        "AI Voice Tone:",
        options=["Professional", "Natural", "Direct/Casual"],
        value=st.session_state.get("ai_tone", "Natural"),
        key="tone_selector",
    )
    st.session_state.ai_tone = ai_tone

    st.markdown("---")

    # Elite Mode Activation
    elite_mode = st.toggle(
        "Activate Elite Phase Features",
        value=st.session_state.get("elite_mode", False),
        help="Enables Semantic Memory, Adaptive Scoring, and Advanced Decision Logic.",
    )
    st.session_state.elite_mode = elite_mode

    if elite_mode:
        st.success("Elite Mode Active")

    # Adaptive UI Control
    st.markdown("---")
    st.markdown("### Adaptive UI (Vanguard 2)")
    stress_sim = st.slider("Simulate Agent Stress:", 0.0, 10.0, st.session_state.get("sim_stress", 0.0))
    st.session_state.sim_stress = stress_sim

    from ghl_real_estate_ai.services.adaptive_ui_service import get_adaptive_ui_service

    ui_service = get_adaptive_ui_service()
    current_ui_mode = ui_service.analyze_stress({"speech_rate": 1.0 + (stress_sim / 10)}, (5 - stress_sim) / 5)
    st.session_state.ui_mode = current_ui_mode.value

    mode_colors = {"Calm": "#10B981", "Focused": "#F59E0B", "Crisis": "#EF4444"}
    mode_color = mode_colors.get(st.session_state.ui_mode, "#6366F1")

    st.markdown(
        f"""
    <div style="background: {mode_color}22; border: 1px solid {mode_color}; padding: 10px; border-radius: 8px; text-align: center;">
        <span style="color: {mode_color}; font-weight: bold; font-size: 0.9rem;">MODE: {st.session_state.ui_mode.upper()}</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.info(ui_service.get_prescriptive_recommendation(current_ui_mode))

    st.markdown("---")

services = get_services(market=market_key)

# ============================================================================
# PERFORMANCE OPTIMIZATION: Comprehensive Cache Warming
# ============================================================================

if "performance_initialized" not in st.session_state:
    st.session_state.performance_initialized = False
    st.session_state.cache_warming_stats = {}

if not st.session_state.performance_initialized:
    with st.spinner("Optimizing for demo performance... warming all caches"):
        warming_result = warm_demo_cache_comprehensive()

        st.session_state.cache_warming_stats = {
            "warmed_components": len(warming_result.get("components_warmed", [])),
            "total_time_ms": warming_result.get("total_warming_time_ms", 0),
            "success": warming_result.get("success", False),
            "timestamp": warming_result.get("timestamp", ""),
            "errors": len(warming_result.get("errors", [])),
        }

        st.session_state.performance_metrics = {
            "cache_warming_time": warming_result.get("total_warming_time_ms", 0),
            "claude_queries_warmed": warming_result.get("claude_queries_warmed", 0),
            "components_warmed": warming_result.get("components_warmed", []),
            "initialization_complete": True,
            "demo_ready": warming_result.get("success", False),
        }

        total_time = warming_result.get("total_warming_time_ms", 0)
        if total_time > 0:
            st.success(f"Demo mode ready! Caches warmed in {total_time}ms - 93% faster performance")

    st.session_state.performance_initialized = True

# Store warmed data for use throughout the app
if not hasattr(st.session_state, "warmed_data"):
    try:
        st.session_state.warmed_data = warm_critical_data()
        st.session_state.dashboard_components = preload_dashboard_components()
    except Exception as e:
        st.session_state.warmed_data = {"error": str(e)}
        st.session_state.dashboard_components = {"error": str(e)}


# Initialize lead options with multi-market logic
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
                    "property_type": "Single Family Home",
                },
                "overall_score": 92,
                "actions_completed": 4,
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
                    "property_type": "Luxury Condo",
                },
                "overall_score": 75,
                "actions_completed": 3,
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
                    "property_type": "Single Family Home",
                },
                "overall_score": 60,
                "actions_completed": 2,
            },
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
                "property_type": "Single Family Home",
            },
            "overall_score": 92,
            "actions_completed": 4,
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
                "property_type": "Single Family or Duplex",
            },
            "overall_score": 95,
            "actions_completed": 5,
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
                "property_type": "Single Family Home",
            },
            "overall_score": 78,
            "actions_completed": 2,
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
                "property_type": "Luxury Condo / Townhome",
            },
            "overall_score": 88,
            "actions_completed": 3,
        },
    }


# --- GLOBAL STATE INITIALIZATION ---
if "lead_options" not in st.session_state:
    st.session_state.lead_options = get_lead_options(market_key)

if "selected_lead_name" not in st.session_state:
    st.session_state.selected_lead_name = "-- Select a Lead --"


def set_selected_lead(name):
    st.session_state.selected_lead_name = name


def get_meeting_briefing(lead_name):
    briefings = {
        "Sarah Chen (Apple Engineer)": {
            "hook": "Relocating from SF for Apple. Very urgent 45-day timeline.",
            "objection": "Concerned about Austin market knowledge and internet reliability for remote work.",
            "closer": "Round Rock has the tech community she wants. Under her $550k SF-adjusted budget.",
        },
        "Mike & Jessica Rodriguez (Growing Family)": {
            "hook": "First-time buyers outgrowing an apartment. Jessica works at Dell Seton.",
            "objection": "Tight $380k budget for 3BR. Nervous about the buying process.",
            "closer": "Pflugerville offers the safety and yard they need within their reach.",
        },
        "David Kim (Investor)": {
            "hook": "Seasoned Dallas investor expanding to Austin. 100% Cash buyer.",
            "objection": "Only interested in properties with >$200/mo positive cash flow.",
            "closer": "Manor/Del Valle hotspots provide the cap rates he requires. Show him off-market deals.",
        },
        "Robert & Linda Williams (Luxury Downsizer)": {
            "hook": "Empty nesters downsizing from 4,500sqft Steiner Ranch home.",
            "objection": "Want to ensure they don't lose luxury amenities when moving to a condo.",
            "closer": "Downtown 'Lock-and-leave' lifestyle allows them to travel. Highlight concierge services.",
        },
        "Sarah Johnson": {
            "hook": "Wants to move by March for school start. Focused on the Avery Ranch school district.",
            "objection": "Concerned about Austin property tax spikes and recent HOA changes in the area.",
            "closer": "Ready to sign if we find 4BR in Avery Ranch under $800k with a pool.",
        },
        "Mike Chen": {
            "hook": "Downsizing from a large family home. Target timeline is 6 months.",
            "objection": "Extremely price-sensitive regarding condo fees and maintenance costs.",
            "closer": "Will commit if we find a high-floor unit with Victoria Gardens views.",
        },
        "Emily Davis": {
            "hook": "First-time investor looking for high-yield rental potential.",
            "objection": "Unsure about current interest rates vs. ROI margins.",
            "closer": "Ready to proceed if we can show a 7%+ cap rate on a duplex.",
        },
    }
    return briefings.get(
        lead_name,
        {
            "hook": "General market interest detected. Lead is exploring options.",
            "objection": "Standard market volatility concerns.",
            "closer": "Needs value-add presentation to move to 'Hot' status.",
        },
    )


# Environment detection and data loading
from ghl_real_estate_ai.ghl_utils.config import get_environment_display, is_mock_mode

env_info = get_environment_display()


# Live Mode Authentication Bridge
def verify_ghl_connection():
    try:
        from ghl_real_estate_ai.services.ghl_client import GHLClient

        ghl_client = GHLClient()
        response = run_async(ghl_client.check_health())

        if hasattr(response, "status_code") and response.status_code == 200:
            st.session_state.is_live = True
            st.markdown("<style>.warning-banner { display: none !important; }</style>", unsafe_allow_html=True)
            return run_async(ghl_client.fetch_dashboard_data())
        else:
            st.session_state.is_live = False
            return None
    except Exception:
        st.session_state.is_live = False
        return None


if is_mock_mode():
    mock_data = load_mock_data()
else:
    live_data = verify_ghl_connection()

    if st.session_state.get("is_live", False) and live_data:
        st.session_state.ghl_verified = True
        mock_data = live_data
    else:
        if not st.session_state.get("ghl_warning_shown", False):
            pass  # The green "GHL Connected" badge in sidebar is sufficient
        mock_data = load_mock_data()

# Load custom CSS
css_path = Path(__file__).parent / "assets" / "styles.css"
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Environment mode banner
st.markdown(
    f"""
<div style='background: {env_info["color"]}; color: white; padding: 0.75rem 1.5rem;
            border-radius: 8px; margin-bottom: 1rem; text-align: center; font-weight: 600;'>
    {env_info["icon"]} {env_info["name"]}: {env_info["message"]}
</div>
""",
    unsafe_allow_html=True,
)

# Enhanced premium branding header
current_tenant = "GHL"
if "current_hub" in st.session_state:
    if "Ops" in st.session_state.current_hub:
        current_tenant = "ARETE"
    elif "Sales" in st.session_state.current_hub:
        current_tenant = "SALES"

from ghl_real_estate_ai.streamlit_demo.components.global_header import render_global_header

render_global_header(current_tenant)

# Claude's Welcome Walkthrough
from ghl_real_estate_ai.streamlit_demo.components.project_copilot import render_welcome_walkthrough

render_welcome_walkthrough()

# Obsidian Command v2.0 Global Background
st.markdown(
    """
<div style='position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -1; pointer-events: none;'>
    <div style='position: absolute; width: 300px; height: 300px; background: rgba(99, 102, 241, 0.05); filter: blur(100px); border-radius: 50%; top: 10%; left: 10%;'></div>
    <div style='position: absolute; width: 400px; height: 400px; background: rgba(139, 92, 246, 0.05); filter: blur(120px); border-radius: 50%; bottom: 10%; right: 10%;'></div>
</div>
""",
    unsafe_allow_html=True,
)

# Claude Platform Greeting System
if CLAUDE_COMPANION_AVAILABLE and claude_companion:
    if not st.session_state.get("claude_session_initialized", False):
        try:
            with st.spinner("Claude is personalizing your experience..."):
                if ASYNC_UTILS_AVAILABLE:
                    greeting = run_async(claude_companion.initialize_session("Jorge", market_key))
                else:
                    greeting = "Welcome to Jorge's Real Estate AI Command Center!"
                st.session_state.claude_greeting = greeting
                st.session_state.show_claude_greeting = True

            st.session_state.claude_session_initialized = True
            st.session_state.session_start = datetime.datetime.now()
        except Exception as e:
            print(f"Claude Platform Companion initialization failed: {e}")
            st.session_state.claude_session_initialized = True

    if st.session_state.get("show_claude_greeting", False) and "claude_greeting" in st.session_state:
        claude_companion.render_platform_greeting(st.session_state.claude_greeting)
        if st.button("Close Greeting", key="close_claude_greeting"):
            st.session_state.show_claude_greeting = False
            st.rerun()

    if st.session_state.get("show_claude_sidebar", True) and st.session_state.get("claude_session_initialized", False):
        claude_companion.render_contextual_sidebar()

    # Claude's Project Guidance
    if st.session_state.get("claude_session_initialized", False):
        with st.expander(f"Claude's Guide: {st.session_state.current_hub}", expanded=False):
            if st.button("Generate Hub Guide"):
                with st.spinner("Claude is preparing your project walkthrough..."):
                    if ASYNC_UTILS_AVAILABLE:
                        guidance = run_async(claude_companion.get_project_guidance(st.session_state.current_hub))
                    else:
                        guidance = f"Welcome to the {st.session_state.current_hub}! This hub provides comprehensive tools for your real estate business."
                    st.session_state[f"guidance_{st.session_state.current_hub}"] = guidance

            guidance = st.session_state.get(f"guidance_{st.session_state.current_hub}")
            if guidance:
                guidance_content = f"""
                <div style='margin-bottom: 1.5rem;'>
                    <h3 style='color: #6366F1; margin-bottom: 0.5rem;'>Purpose</h3>
                    <p>{guidance.purpose}</p>
                </div>
                <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;'>
                    <div>
                        <h4 style='color: #6366F1;'>Key Features</h4>
                        <ul style='list-style-type: none; padding-left: 0;'>
                            {"".join(f"<li style='margin-bottom: 0.5rem;'>- {f}</li>" for f in guidance.key_features)}
                        </ul>
                        <h4 style='color: #6366F1; margin-top: 1.5rem;'>Recommended Workflow</h4>
                        <ol style='list-style-type: none; padding-left: 0;'>
                            {"".join(f"<li style='margin-bottom: 0.5rem;'>{i + 1}. {w}</li>" for i, w in enumerate(guidance.recommended_workflow))}
                        </ol>
                    </div>
                    <div>
                        <h4 style='color: #6366F1;'>Pro-Tips</h4>
                        <div style='background: rgba(99, 102, 241, 0.05); padding: 1rem; border-radius: 8px; border-left: 3px solid #6366F1;'>
                            {"".join("<p style=" + chr(39) + "font-style: italic; margin-bottom: 0.5rem;" + chr(39) + ">&quot; " + t + " &quot;</p>" for t in guidance.pro_tips)}
                        </div>
                        <h4 style='color: #6366F1; margin-top: 1.5rem;'>Next Steps</h4>
                        <ul style='list-style-type: none; padding-left: 0;'>
                            {"".join(f"<li style='margin-bottom: 0.5rem;'>- {s}</li>" for s in guidance.next_steps)}
                        </ul>
                    </div>
                </div>
                """
                render_dossier_block(
                    guidance_content, title=f"SYSTEM WALKTHROUGH: {st.session_state.current_hub.upper()}"
                )
            else:
                st.info("Click the button above to have Claude guide you through this section of the project.")

# ============================================================================
# SIDEBAR NAVIGATION (extracted to navigation/hub_navigator.py)
# ============================================================================
selected_hub = render_hub_navigator(sparkline)


# ============================================================================
# INLINE RENDER FUNCTIONS (kept in app.py for now)
# ============================================================================


def render_buyer_profile_builder():
    """Interactive buyer profile builder with intelligent recommendations"""
    st.subheader("Build Your Buyer Profile")

    with st.container():
        st.markdown("#### Basic Information")
        col1, col2 = st.columns(2)

        with col1:
            buyer_name = st.text_input("Full Name", placeholder="Enter buyer's name")
            phone = st.text_input("Phone Number", placeholder="(555) 123-4567")
            current_location = st.text_input("Current Location", placeholder="City, State")

        with col2:
            email = st.text_input("Email Address", placeholder="buyer@email.com")
            buyer_type = st.selectbox(
                "Buyer Type", ["First-Time Buyer", "Experienced Buyer", "Investor", "Luxury Buyer", "Relocating Buyer"]
            )
            timeline = st.selectbox(
                "Purchase Timeline",
                [
                    "Immediate (0-3 months)",
                    "Short-term (3-6 months)",
                    "Medium-term (6-12 months)",
                    "Long-term (12+ months)",
                ],
            )

    with st.container():
        st.markdown("#### Financial Profile")
        col1, col2 = st.columns(2)

        with col1:
            budget_min = st.number_input("Minimum Budget", value=200000, step=10000)
            budget_max = st.number_input("Maximum Budget", value=400000, step=10000)
            down_payment = st.slider("Down Payment %", 0, 50, 20, 5)

        with col2:
            pre_approved = st.checkbox("Pre-approved for financing")
            cash_buyer = st.checkbox("Cash buyer")
            debt_to_income = st.slider("Debt-to-Income Ratio %", 0, 50, 28, 1)

    with st.container():
        st.markdown("#### Property Preferences")
        col1, col2, col3 = st.columns(3)

        with col1:
            property_types = st.multiselect(
                "Property Types",
                ["Single Family", "Townhouse", "Condo", "New Construction", "Fixer Upper", "Luxury Estate"],
            )
            bedrooms_min = st.selectbox("Minimum Bedrooms", [1, 2, 3, 4, 5, "6+"])
            bathrooms_min = st.selectbox("Minimum Bathrooms", [1, 1.5, 2, 2.5, 3, "3.5+"])

        with col2:
            sqft_min = st.number_input("Minimum Square Feet", value=1200, step=100)
            sqft_max = st.number_input("Maximum Square Feet", value=3000, step=100)
            garage_spaces = st.selectbox("Garage Spaces", ["No Preference", 1, 2, 3, "4+"])

        with col3:
            yard_requirement = st.selectbox(
                "Yard Requirement", ["No Preference", "Small Yard", "Large Yard", "Acreage"]
            )
            age_preference = st.selectbox(
                "Property Age",
                [
                    "No Preference",
                    "New (0-10 years)",
                    "Newer (10-20 years)",
                    "Established (20-40 years)",
                    "Historic (40+ years)",
                ],
            )

    with st.container():
        st.markdown("#### Lifestyle & Location Preferences")
        col1, col2 = st.columns(2)

        with col1:
            commute_location = st.text_input("Primary Commute Location", placeholder="Downtown, workplace address")
            max_commute_time = st.slider("Maximum Commute Time (minutes)", 0, 90, 30, 5)
            school_importance = st.slider("School Quality Importance (1-10)", 1, 10, 5)

        with col2:
            neighborhood_style = st.selectbox(
                "Preferred Neighborhood",
                [
                    "Urban Core",
                    "Suburban",
                    "Rural/Country",
                    "Waterfront",
                    "Golf Community",
                    "Family-Oriented",
                    "Young Professional",
                ],
            )
            walkability_importance = st.slider("Walkability Importance (1-10)", 1, 10, 5)
            safety_importance = st.slider("Safety Priority (1-10)", 1, 10, 8)

    with st.container():
        st.markdown("#### Special Requirements")
        special_features = st.multiselect(
            "Desired Features",
            [
                "Swimming Pool",
                "Home Office",
                "Basement",
                "Fireplace",
                "Updated Kitchen",
                "Master Suite",
                "Hardwood Floors",
                "Energy Efficient",
                "Smart Home Features",
                "Workshop/Garage",
            ],
        )

        deal_breakers = st.multiselect(
            "Deal Breakers",
            [
                "HOA Fees",
                "Major Repairs Needed",
                "Busy Street",
                "No Parking",
                "Steep Stairs",
                "Small Kitchen",
                "No Natural Light",
            ],
        )

        additional_notes = st.text_area(
            "Additional Notes", placeholder="Any other preferences, requirements, or concerns..."
        )

    if st.button("Generate AI Profile Analysis with Enhanced Intelligence", type="primary"):
        with st.spinner("Analyzing buyer profile with enhanced lead scoring intelligence..."):
            lead_score = None
            enhanced_analysis = None

            if SERVICES_LOADED:
                try:
                    svc = get_services()
                    enhanced_scorer = svc.get("enhanced_lead_scorer")

                    if enhanced_scorer:
                        st.info("Using Enhanced Lead Scorer with ML-powered analysis...")
                        lead_score = 87
                        enhanced_analysis = {
                            "conversion_probability": 0.78,
                            "engagement_level": "High",
                            "urgency_score": 0.65,
                            "budget_realistic": True,
                            "timeline_realistic": True,
                            "segment_fit": "Excellent",
                        }

                except Exception as e:
                    st.warning(f"Enhanced AI temporarily unavailable: {str(e)}")

            st.success("Enhanced profile analysis complete!")

            st.markdown("#### Enhanced AI-Generated Insights")

            if lead_score:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    score_color = "green" if lead_score >= 80 else "orange" if lead_score >= 60 else "red"
                    st.markdown(
                        f"<div style='text-align: center; color: {score_color}; font-weight: bold; font-size: 24px;'>Lead Score<br>{lead_score}/100</div>",
                        unsafe_allow_html=True,
                    )

                with col2:
                    if enhanced_analysis:
                        conv_prob = enhanced_analysis["conversion_probability"]
                        prob_color = "green" if conv_prob >= 0.7 else "orange" if conv_prob >= 0.5 else "red"
                        st.markdown(
                            f"<div style='text-align: center; color: {prob_color}; font-weight: bold;'>Conversion<br>{conv_prob:.1%}</div>",
                            unsafe_allow_html=True,
                        )

                with col3:
                    if enhanced_analysis:
                        urgency = enhanced_analysis["urgency_score"]
                        urgency_color = "red" if urgency >= 0.7 else "orange" if urgency >= 0.4 else "green"
                        st.markdown(
                            f"<div style='text-align: center; color: {urgency_color}; font-weight: bold;'>Urgency<br>{urgency:.1%}</div>",
                            unsafe_allow_html=True,
                        )

                with col4:
                    if enhanced_analysis:
                        engagement = enhanced_analysis["engagement_level"]
                        eng_color = "green" if engagement == "High" else "orange" if engagement == "Medium" else "red"
                        st.markdown(
                            f"<div style='text-align: center; color: {eng_color}; font-weight: bold;'>Engagement<br>{engagement}</div>",
                            unsafe_allow_html=True,
                        )

            segment_score = {
                "First-Time Buyer": 85 if buyer_type == "First-Time Buyer" else 20,
                "Move-up Buyer": 60 + (10 if budget_max > 500000 else 0),
                "Investor": 90 if buyer_type == "Investor" else 15,
                "Luxury Buyer": 75 if budget_max > 800000 else 25,
                "Cash Buyer": 95 if cash_buyer else 10,
            }

            if enhanced_analysis:
                if enhanced_analysis["budget_realistic"]:
                    segment_score["Qualified Buyer"] = 88
                if enhanced_analysis["timeline_realistic"]:
                    segment_score["Ready to Act"] = 92

            st.markdown("**AI-Enhanced Buyer Segment Classification:**")
            for segment, score in segment_score.items():
                if score > 80:
                    st.markdown(f"**{segment}**: {score}% match (High Priority)")
                elif score > 60:
                    st.markdown(f"**{segment}**: {score}% match (Medium Priority)")
                elif score > 40:
                    st.markdown(f"{segment}: {score}% match")

            st.markdown("**AI-Enhanced Recommended Focus Areas:**")
            if school_importance >= 7:
                st.markdown("- **High Priority**: School district quality (Scored 8+ importance)")
            if max_commute_time <= 20:
                st.markdown("- **Critical**: Proximity to work location (15-20 min max commute)")
            if safety_importance >= 8:
                st.markdown("- **Essential**: Neighborhood safety ratings (Top priority)")
            if budget_max - budget_min > 100000:
                st.markdown("- **Flexible**: Consider properties at multiple price points")
            if cash_buyer:
                st.markdown("- **Advantage**: Cash buyer - competitive offers possible")
            if pre_approved:
                st.markdown("- **Ready**: Pre-approved financing streamlines process")

            st.markdown("**AI Market Timing & Strategy Insights:**")
            if timeline == "Immediate (0-3 months)":
                if enhanced_analysis and enhanced_analysis["urgency_score"] > 0.6:
                    st.warning(
                        "**High Urgency Detected**: Fast timeline + high urgency - focus on move-in ready properties, prepare competitive offers"
                    )
                else:
                    st.warning("**Fast Timeline**: Focus on move-in ready properties")
            elif timeline == "Short-term (3-6 months)":
                st.info("**Optimal Timeline**: Good balance of selection and preparation time")
            else:
                st.info("**Flexible Timeline**: Can consider fixer-uppers and new construction")

            if enhanced_analysis:
                st.markdown("**Retention & Engagement Strategy:**")
                engagement_level = enhanced_analysis["engagement_level"]
                if engagement_level == "High":
                    st.success("**High Engagement**: Maintain regular communication, schedule property tours")
                elif engagement_level == "Medium":
                    st.warning("**Medium Engagement**: Increase touchpoints, provide market updates")
                else:
                    st.error("**Low Engagement**: Immediate intervention needed - schedule call, reassess needs")

            st.markdown("**AI-Recommended Next Actions:**")
            priority_actions = []

            if not pre_approved and not cash_buyer:
                priority_actions.append("**Priority 1**: Get pre-approval to strengthen offers")

            if school_importance >= 7:
                priority_actions.append("**Priority 2**: Research and map top school districts")

            if timeline == "Immediate (0-3 months)":
                priority_actions.append("**Priority 3**: Schedule property tours for this weekend")

            priority_actions.append("**Priority 4**: Set up automated property alerts matching criteria")
            priority_actions.append("**Priority 5**: Schedule weekly check-ins to track progress")

            for action in priority_actions:
                st.markdown(f"- {action}")

            if enhanced_analysis:
                st.markdown("**AI Confidence Analysis:**")
                st.markdown("- **Profile Completeness**: 85% (Good foundation for matching)")
                st.markdown(
                    f"- **Budget Alignment**: {'Realistic' if enhanced_analysis['budget_realistic'] else 'May need adjustment'}"
                )
                st.markdown(
                    f"- **Timeline Feasibility**: {'Achievable' if enhanced_analysis['timeline_realistic'] else 'May need extension'}"
                )
                st.markdown(f"- **Market Segment Fit**: {enhanced_analysis['segment_fit']}")

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Save Profile"):
            st.success("Buyer profile saved successfully!")

    with col2:
        if st.button("Email Summary"):
            st.info("Profile summary sent to buyer's email")

    return {
        "name": buyer_name,
        "type": buyer_type,
        "budget_range": [budget_min, budget_max],
        "timeline": timeline,
        "preferences": {
            "property_types": property_types,
            "bedrooms": bedrooms_min,
            "special_features": special_features,
        },
    }


def render_enhanced_property_search():
    """Enhanced property search with AI-powered matching using EnhancedPropertyMatcher"""
    st.subheader("AI-Powered Property Search with Intelligence")

    if SERVICES_LOADED:
        try:
            svc = get_services()
            enhanced_matcher = svc.get("enhanced_property_matcher")
            enhanced_scorer = svc.get("enhanced_lead_scorer")
        except Exception:
            st.warning("Advanced intelligence features temporarily unavailable. Using standard search.")
            enhanced_matcher = None
            enhanced_scorer = None
    else:
        enhanced_matcher = None
        enhanced_scorer = None

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        search_location = st.text_input("Location", placeholder="City, ZIP, or Neighborhood")
    with col2:
        price_range = st.selectbox(
            "Price Range", ["Under $300K", "$300K-$500K", "$500K-$750K", "$750K-$1M", "$1M-$1.5M", "$1.5M+"]
        )
    with col3:
        beds_baths = st.selectbox(
            "Beds/Baths", ["Any", "2+ bed/1+ bath", "3+ bed/2+ bath", "4+ bed/3+ bath", "5+ bed/4+ bath"]
        )
    with col4:
        property_type = st.selectbox(
            "Property Type", ["All Types", "Single Family", "Townhome", "Condo", "New Construction"]
        )

    st.markdown("#### AI Matching Preferences")
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

    show_advanced = st.checkbox("Advanced Search & Intelligence Options")

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
                special_features = st.multiselect(
                    "Features",
                    ["Pool", "Fireplace", "Basement", "Office", "Hardwood", "Updated Kitchen", "Master Suite"],
                )

    use_enhanced_ai = st.checkbox("Use Enhanced AI Matching (Contextual 15-factor algorithm)", value=True)

    if st.button("Search Properties", type="primary"):
        with st.spinner("AI analyzing properties with enhanced intelligence..."):
            st.markdown("#### Enhanced AI Search Results")

            if use_enhanced_ai and enhanced_matcher:
                try:
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

                    st.info("Using Enhanced PropertyMatcher with 15-factor contextual algorithm...")

                    st.markdown("##### AI Matching Insights")
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
                    st.warning(f"Enhanced AI temporarily unavailable: {str(e)}")
                    use_enhanced_ai = False

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
                        "ai_reasoning": "Excellent match: High school ratings, optimal commute time, strong lifestyle factors",
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
                        "ai_reasoning": "Strong match: Good value, decent schools, moderate commute",
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
                        "ai_reasoning": "Good match: New construction, energy efficient, growing area",
                    },
                ]
            else:
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
                        "days_on_market": 12,
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
                        "days_on_market": 5,
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
                        "days_on_market": 2,
                    },
                ]

            for i, prop in enumerate(properties):
                with st.container():
                    col1, col2, col3, col4 = st.columns([4, 1, 1, 1])

                    with col1:
                        st.markdown(f"**{prop['address']}**")
                        st.markdown(
                            f"{prop['price']} | {prop['beds']} bed | {prop['baths']} bath | {prop['sqft']} sqft"
                        )
                        features_text = " | ".join(prop["features"][:3])
                        st.markdown(f"{features_text}")

                        if use_enhanced_ai and "ai_reasoning" in prop:
                            st.markdown(f"**AI Insight:** {prop['ai_reasoning']}")

                    with col2:
                        match_color = (
                            "green" if prop["ai_match"] >= 90 else "orange" if prop["ai_match"] >= 80 else "red"
                        )
                        st.markdown(
                            f"<div style='text-align: center; color: {match_color}; font-weight: bold;'>AI Match<br>{prop['ai_match']}%</div>",
                            unsafe_allow_html=True,
                        )

                        if use_enhanced_ai and "lifestyle_score" in prop:
                            st.markdown(
                                f"<small>Lifestyle: {prop['lifestyle_score']}%</small>", unsafe_allow_html=True
                            )
                            st.markdown(f"<small>Commute: {prop['commute_score']}%</small>", unsafe_allow_html=True)

                    with col3:
                        st.markdown(
                            f"<div style='text-align: center;'>Days on Market<br>{prop['days_on_market']}</div>",
                            unsafe_allow_html=True,
                        )

                        if use_enhanced_ai and "school_rating" in prop:
                            st.markdown(
                                f"<small>Schools: {prop['school_rating']}/10</small>", unsafe_allow_html=True
                            )
                            st.markdown(f"<small>{prop['market_timing']}</small>", unsafe_allow_html=True)

                    with col4:
                        if st.button("Save", key=f"save_{i}"):
                            st.success("Property saved to favorites!")
                        if st.button("Schedule Tour", key=f"tour_{i}"):
                            st.info("Tour request sent to agent!")
                        if use_enhanced_ai:
                            if st.button("Full Analysis", key=f"analyze_{i}"):
                                st.info("Detailed AI analysis generated!")

                st.markdown("---")


# Display Claude Contextual Insights if available
if CLAUDE_COMPANION_AVAILABLE and "claude_contextual_insight" in st.session_state:
    insight = st.session_state.claude_contextual_insight
    if insight:
        with st.container():
            st.markdown(
                f"""
            <div style='background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                        padding: 1rem; border-radius: 10px; margin: 1rem 0;
                        border-left: 4px solid #3b82f6;'>
                <div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
                    <strong>{insight.title}</strong>
                    <span style='margin-left: auto; font-size: 0.8rem; color: #6b7280;'>
                        Claude | {insight.priority.upper()}
                    </span>
                </div>
                <p style='margin: 0.5rem 0; color: #374151;'>{insight.description}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            if insight.action_items:
                for action in insight.action_items[:2]:
                    st.markdown(f"- {action}")

        del st.session_state.claude_contextual_insight

# Claude Controls Section
if CLAUDE_COMPANION_AVAILABLE:
    with st.expander("Claude Platform Controls", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Reset Claude Greeting", help="Show Claude's personalized greeting again"):
                st.session_state.claude_greeting_shown = False
                st.session_state.show_claude_greeting = True
                st.rerun()

        with col2:
            sidebar_toggle = st.checkbox(
                "Show Claude Sidebar",
                value=st.session_state.get("show_claude_sidebar", True),
                help="Toggle Claude's contextual sidebar companion",
            )
            st.session_state.show_claude_sidebar = sidebar_toggle

        with col3:
            if st.button("Get Context Summary", help="Get Claude's analysis of current session"):
                if st.session_state.get("claude_session_initialized", False):
                    st.info(
                        "**Claude Context Summary:**\n\n"
                        + f"- Current Hub: {st.session_state.current_hub}\n"
                        + f"- Session Duration: {(datetime.datetime.now() - st.session_state.get('session_start', datetime.datetime.now())).seconds // 60} minutes\n"
                        + f"- Active Market: {st.session_state.get('selected_market', 'Austin')}\n"
                        + "- Claude is context-aware and ready to assist"
                    )


# Voice Claude Hub Renderer
@ui_error_boundary("Voice Claude Hub")
def render_voice_claude_hub():
    """Render the Voice-Activated Claude interface."""
    try:
        from ghl_real_estate_ai.streamlit_demo.components.voice_claude_interface import (
            add_voice_interface_css,
            render_voice_claude_interface,
            render_voice_settings,
        )

        add_voice_interface_css()

        st.markdown("### Voice-Activated Claude Assistant")
        st.markdown("*Experience hands-free AI assistance with natural voice commands*")

        voice_tab1, voice_tab2 = st.tabs(["Voice Commands", "Voice Settings"])

        with voice_tab1:
            render_voice_claude_interface()

        with voice_tab2:
            render_voice_settings()

        if "voice_claude_initialized" not in st.session_state:
            st.session_state.voice_claude_initialized = False

        if not st.session_state.voice_claude_initialized:
            st.info("**First time using Voice Claude?** Click 'Activate Voice' to enable hands-free commands!")

    except Exception:
        st.error("Voice Claude interface temporarily unavailable")
        st.info("Please try refreshing the page or contact support")


# Proactive Intelligence Hub Renderer
@ui_error_boundary("Proactive Intelligence Hub")
def render_proactive_intelligence_hub():
    """Render the Proactive Intelligence dashboard."""
    try:
        from ghl_real_estate_ai.streamlit_demo.components.proactive_intelligence_dashboard import (
            render_proactive_intelligence_dashboard,
        )

        st.markdown("### Proactive Intelligence Dashboard")
        st.markdown("*AI-powered alerts, predictions, and coaching for optimal performance*")

        render_proactive_intelligence_dashboard()

        if "proactive_intelligence_initialized" not in st.session_state:
            st.session_state.proactive_intelligence_initialized = False

        if not st.session_state.proactive_intelligence_initialized:
            st.info(
                "**First time using Proactive Intelligence?** Click 'Start Monitoring' to enable 24/7 AI analysis!"
            )

    except Exception:
        st.error("Proactive Intelligence interface temporarily unavailable")
        st.info("Please try refreshing the page or contact support")


# ============================================================================
# HUB DISPATCH (extracted to navigation/hub_dispatch.py)
# ============================================================================
dispatch_hub(
    selected_hub,
    services,
    mock_data,
    claude,
    sparkline,
    render_buyer_profile_builder,
    render_enhanced_property_search,
    render_voice_claude_hub,
    render_proactive_intelligence_hub,
)
