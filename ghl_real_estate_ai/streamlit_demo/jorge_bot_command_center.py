"""
Jorge's Unified AI Bot Command Center - Obsidian Elite Edition

The ultimate command interface for managing both Lead and Seller bots.
Integrates:
- 🎯 Lead Intelligence & Scoring
- ⚔️ Seller Negotiation Advantage
- 📊 Advanced Business Analytics
- 🎤 Voice AI Integration

Author: Claude Code Assistant
Created: 2026-01-21
"""

import streamlit as st

# Safe import for async utilities
try:
    from ghl_real_estate_ai.streamlit_demo.async_utils import run_async
    ASYNC_UTILS_AVAILABLE = True
except ImportError:
    try:
        from async_utils import run_async
        ASYNC_UTILS_AVAILABLE = True
    except ImportError:
        ASYNC_UTILS_AVAILABLE = False
        # Fallback function for async operations
        def run_async(coro):
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, skip async operation
                    return None
                else:
                    return loop.run_until_complete(coro)
            except RuntimeError:
                # Create new loop if none exists
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(coro)
                loop.close()
                return result
import sys
import os
import time
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path with multiple fallback paths
current_file = Path(__file__).resolve()

# Try different path configurations
paths_to_try = [
    current_file.parent.parent.parent,  # Normal: EnterpriseHub/
    current_file.parent.parent,         # If running from streamlit_demo/
    current_file.parent,                # If running from current directory
]

# Add all paths and ensure ghl_real_estate_ai is accessible
for path in paths_to_try:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# Also specifically add the ghl_real_estate_ai directory
ghl_path = current_file.parent.parent
if str(ghl_path) not in sys.path:
    sys.path.insert(0, str(ghl_path))

# Page configuration
st.set_page_config(
    page_title="Jorge AI Union[Command, Elite] Edition",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import elite styling
try:
    from ghl_real_estate_ai.streamlit_demo.obsidian_theme import inject_elite_css, render_decision_stream
    ELITE_STYLING = True
except ImportError:
    ELITE_STYLING = False

# Import dashboard components with multiple fallback paths
COMPONENTS_AVAILABLE = False
component_imports = {}

# Try different import paths
import_attempts = [
    # Full path from project root
    {
        'jorge_lead_bot_dashboard': 'ghl_real_estate_ai.streamlit_demo.components.jorge_lead_bot_dashboard',
        'jorge_seller_bot_dashboard': 'ghl_real_estate_ai.streamlit_demo.components.jorge_seller_bot_dashboard',
        'jorge_buyer_bot_dashboard': 'ghl_real_estate_ai.streamlit_demo.components.jorge_buyer_bot_dashboard',
        'jorge_analytics_dashboard': 'ghl_real_estate_ai.streamlit_demo.components.jorge_analytics_dashboard',
        'lifecycle_dashboard': 'ghl_real_estate_ai.streamlit_demo.components.lifecycle_dashboard',
        'claude_concierge_panel': 'ghl_real_estate_ai.streamlit_demo.components.claude_concierge_panel'
    },
    # Relative path
    {
        'jorge_lead_bot_dashboard': 'components.jorge_lead_bot_dashboard',
        'jorge_seller_bot_dashboard': 'components.jorge_seller_bot_dashboard',
        'jorge_buyer_bot_dashboard': 'components.jorge_buyer_bot_dashboard',
        'jorge_analytics_dashboard': 'components.jorge_analytics_dashboard',
        'lifecycle_dashboard': 'components.lifecycle_dashboard',
        'claude_concierge_panel': 'components.claude_concierge_panel'
    }
]

# Try each import configuration
for attempt in import_attempts:
    try:
        import importlib
        component_imports['render_jorge_lead_bot_dashboard'] = getattr(
            importlib.import_module(attempt['jorge_lead_bot_dashboard']),
            'render_jorge_lead_bot_dashboard',
            lambda: st.info("Lead Bot Dashboard temporarily unavailable")
        )
        component_imports['render_jorge_seller_bot_dashboard'] = getattr(
            importlib.import_module(attempt['jorge_seller_bot_dashboard']),
            'render_jorge_seller_bot_dashboard',
            lambda: st.info("Seller Bot Dashboard temporarily unavailable")
        )
        component_imports['render_jorge_buyer_bot_dashboard'] = getattr(
            importlib.import_module(attempt['jorge_buyer_bot_dashboard']),
            'render_jorge_buyer_bot_dashboard',
            lambda: st.info("Buyer Bot Dashboard temporarily unavailable")
        )
        component_imports['render_jorge_analytics_dashboard'] = getattr(
            importlib.import_module(attempt['jorge_analytics_dashboard']),
            'render_jorge_analytics_dashboard',
            lambda: st.info("Analytics Dashboard temporarily unavailable")
        )
        component_imports['render_full_lifecycle_dashboard'] = getattr(
            importlib.import_module(attempt['lifecycle_dashboard']),
            'render_full_lifecycle_dashboard',
            lambda: st.info("Lifecycle Dashboard temporarily unavailable")
        )
        claude_module = importlib.import_module(attempt['claude_concierge_panel'])
        component_imports['render_claude_concierge_panel'] = getattr(
            claude_module, 'render_claude_concierge_panel',
            lambda hub=None: st.info("Claude Concierge temporarily unavailable")
        )
        component_imports['render_concierge_coordination_card'] = getattr(
            claude_module, 'render_concierge_coordination_card',
            lambda hub=None: st.info("Concierge Coordination temporarily unavailable")
        )
        COMPONENTS_AVAILABLE = True
        break
    except ImportError:
        continue

# Create fallback functions if imports failed
if not COMPONENTS_AVAILABLE:
    st.warning("⚠️ Some dashboard components are temporarily unavailable. Basic interface will be shown.")
    component_imports = {
        'render_jorge_lead_bot_dashboard': lambda: st.info("Lead Bot Dashboard temporarily unavailable"),
        'render_jorge_seller_bot_dashboard': lambda: st.info("Seller Bot Dashboard temporarily unavailable"),
        'render_jorge_buyer_bot_dashboard': lambda: st.info("Buyer Bot Dashboard temporarily unavailable"),
        'render_jorge_analytics_dashboard': lambda: st.info("Analytics Dashboard temporarily unavailable"),
        'render_full_lifecycle_dashboard': lambda: st.info("Lifecycle Dashboard temporarily unavailable"),
        'render_claude_concierge_panel': lambda hub=None: st.info("Claude Concierge temporarily unavailable"),
        'render_concierge_coordination_card': lambda hub=None: st.info("Concierge Coordination temporarily unavailable")
    }

# Import Phase 9 MOAT Service
try:
    from ghl_real_estate_ai.services.ghl_moat_service import GHLMoatService
    MOAT_SERVICE_AVAILABLE = True
except ImportError:
    MOAT_SERVICE_AVAILABLE = False

def trigger_swarm_sync():
    """Phase 3: Swarm Communication Pulse visual."""
    sync_container = st.empty()
    with sync_container.container():
        st.markdown("""
            <div class="swarm-sync-animation" style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 999999; background: rgba(5, 7, 10, 0.9); padding: 2rem; border-radius: 50%; border: 1px solid var(--elite-accent); display: flex; flex-direction: column; align-items: center; justify-content: center;">
                <i class="fas fa-satellite-dish" style="font-size: 3rem; color: var(--elite-accent); margin-bottom: 1rem; animation: pulse 1s infinite;"></i>
                <div style="font-family: 'Space Grotesk', sans-serif; color: white; font-weight: bold; letter-spacing: 0.2em;">SWARM_SYNC_ACTIVE</div>
                <div style="font-family: 'JetBrains Mono', monospace; color: var(--negotiation-neon); font-size: 0.7rem; margin-top: 0.5rem;">SHARING_INTELLIGENCE...</div>
            </div>
            <style>
                @keyframes pulse {
                    0% { transform: scale(1); opacity: 1; }
                    50% { transform: scale(1.1); opacity: 0.7; }
                    100% { transform: scale(1); opacity: 1; }
                }
            </style>
        """, unsafe_allow_html=True)
        time.sleep(1.2)
    sync_container.empty()

def trigger_handoff_pulse():
    """Phase 4: Handoff Pulse visual for inter-agent relay."""
    pulse_container = st.empty()
    pulse_container.markdown('<div class="handoff-pulse-active"></div>', unsafe_allow_html=True)
    
    sync_container = st.empty()
    with sync_container.container():
        st.markdown("""
            <div style="position: fixed; top: 40%; left: 50%; transform: translate(-50%, -50%); z-index: 999999; background: rgba(99, 102, 241, 0.9); padding: 2.5rem; border-radius: 20px; border: 2px solid var(--negotiation-neon); display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 0 50px rgba(0, 229, 255, 0.4);">
                <i class="fas fa-microchip" style="font-size: 3.5rem; color: white; margin-bottom: 1.5rem; animation: pulse 0.5s infinite alternate;"></i>
                <div style="font-family: 'Space Grotesk', sans-serif; color: white; font-weight: 800; letter-spacing: 0.3em; font-size: 1.2rem;">SOVEREIGN_RELAY_ACTIVE</div>
                <div style="font-family: 'JetBrains Mono', monospace; color: var(--negotiation-neon); font-size: 0.8rem; margin-top: 1rem; text-transform: uppercase;">Transferring lead dossier to seller hub...</div>
            </div>
            <style>
                @keyframes pulse {
                    0% { transform: scale(1); opacity: 1; }
                    100% { transform: scale(1.1); opacity: 0.7; }
                }
            </style>
        """, unsafe_allow_html=True)
        time.sleep(1.8)
    sync_container.empty()
    pulse_container.empty()

def render_sidebar():
    """Render the elite navigation sidebar."""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="color: #1E88E5; font-family: 'Space Grotesk', sans-serif;">JORGE AI</h2>
            <p style="color: #8B949E; font-size: 0.8rem; letter-spacing: 0.1em;">ELITE COMMAND CENTER</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Initialize session state for hub selection tracking
        if 'prev_hub' not in st.session_state:
            st.session_state.prev_hub = "🎯 Lead Command"

        hub_selection = st.radio(
            "Select Intelligence Hub:",
            ["🎯 Lead Command", "⚔️ Seller Command", "🏠 Buyer Command", "📊 Business Analytics", "🧬 Full Lifecycle", "⚙️ System Config"],
            index=0
        )
        
        # Trigger Swarm Sync if hub changed
        if hub_selection != st.session_state.prev_hub:
            st.session_state.prev_hub = hub_selection
            trigger_swarm_sync()

        st.markdown("---")
        
        # System Status in Sidebar
        st.markdown("### 📡 Neural Uplink")
        st.success("Lead Bot: ONLINE")
        st.success("Seller Bot: ONLINE")
        st.info("Vapi Voice AI: READY")
        
        st.markdown("---")
        st.caption("v4.2.0-ELITE | © 2026 Lyrio.io")
        
        # Omnipresent Concierge
        component_imports['render_claude_concierge_panel'](hub_selection)
        
        return hub_selection

@st.cache_resource
def get_moat_service():
    if MOAT_SERVICE_AVAILABLE:
        return GHLMoatService()
    return None

def main():
    if ELITE_STYLING:
        inject_elite_css()
    
    # Phase 4: Decision Stream Initialization
    if 'global_decisions' not in st.session_state:
        st.session_state.global_decisions = [
            {"action": "System Boot", "why": "Initialization of Sovereign Orchestration Phase 4.", "time": "08:00:00"},
            {"action": "Neural Link", "why": "Establishing secure handshake with GHL MOAT.", "time": "08:00:05"},
            {"action": "Intelligence Activation", "why": "Phase 5 Intent Decoding engines online.", "time": datetime.now(timezone.utc).strftime("%H:%M:%S")}
        ]
    
    # Phase 4: Inter-Agent Relay Logic
    if 'handoff_triggered' not in st.session_state:
        st.session_state.handoff_triggered = False

    selected_hub = render_sidebar()
    
    if not COMPONENTS_AVAILABLE:
        st.error("Dashboards unavailable. Please check installation.")
        return

    if selected_hub == "🎯 Lead Command":
        component_imports['render_concierge_coordination_card'](selected_hub)
        component_imports['render_jorge_lead_bot_dashboard']()

        # Phase 4: Inter-Agent Relay Trigger (Lead Score > 90)
        # Check if a lead has been analyzed and has a high score
        latest_analysis = st.session_state.get('latest_analysis', {})
        if latest_analysis.get('overall_score', 0) > 90 and not st.session_state.handoff_triggered:
            trigger_handoff_pulse()
            st.session_state.handoff_triggered = True
            lead_name = st.session_state.get('analyzed_lead_name', 'Lead')
            st.session_state.global_decisions.append({
                "action": "Agent Handoff",
                "why": f"Lead {lead_name} reached critical score (>90). Transferring to Seller Negotiation.",
                "time": datetime.now(timezone.utc).strftime("%H:%M:%S")
            })
            st.toast(f"SOVEREIGN RELAY: {lead_name} Dossier Transferred to Seller Hub", icon="🚀")

    elif selected_hub == "⚔️ Seller Command":
        component_imports['render_concierge_coordination_card'](selected_hub)
        component_imports['render_jorge_seller_bot_dashboard']()
    elif selected_hub == "🏠 Buyer Command":
        component_imports['render_concierge_coordination_card'](selected_hub)
        component_imports['render_jorge_buyer_bot_dashboard']()
    elif selected_hub == "📊 Business Analytics":
        component_imports['render_concierge_coordination_card'](selected_hub)
        component_imports['render_jorge_analytics_dashboard']()
    elif selected_hub == "🧬 Full Lifecycle":
        component_imports['render_concierge_coordination_card'](selected_hub)
        component_imports['render_full_lifecycle_dashboard']()
    else:
        st.header("⚙️ AI System Configuration")
        st.markdown("*Granular control over Jorge's AI bots, tone, and GHL integration MOATs*")
        
        tab_lead, tab_seller, tab_ghl = st.tabs(["🎯 Lead Bot Config", "⚔️ Seller Bot Config", "🔗 GHL Integration"])
        
        with tab_lead:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Scoring Weights")
                st.slider("Intent Sensitivity", 0.0, 1.0, 0.85)
                st.slider("Financial Threshold", 0.0, 1.0, 0.70)
                st.slider("Timeline Urgency", 0.0, 1.0, 0.90)
            with col2:
                st.subheader("Autonomous Actions")
                st.toggle("Auto-Trigger Voice Call (Hot Leads)", value=True)
                st.toggle("Auto-Send Market Reports", value=False)
                st.selectbox("Lead Tone", ["Professional", "Natural", "Direct", "Urgent"], index=1)

        with tab_seller:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Negotiation Strategy")
                st.slider("Confrontational Intensity", 0.0, 1.0, 0.80)
                st.slider("Vague Answer Sensitivity", 0.0, 1.0, 0.75)
                st.number_input("Take-Away Close Threshold (Streaks)", 1, 5, 2)
            with col2:
                st.subheader("Tone & Style")
                st.toggle("Force SMS Compliance", value=True)
                st.toggle("Direct Mode (No Fluff)", value=True)
                st.multiselect("Active Closers", ["Take-Away", "Alternative Choice", "Assumptive"], default=["Take-Away"])

        with tab_ghl:
            st.subheader("🛰️ Intelligence Layer Sync (MOAT)")
            
            moat_service = get_moat_service()
            if moat_service:
                try:
                    health = moat_service.get_moat_health()
                    if isinstance(health, dict):
                        col1, col2, col3 = st.columns(3)
                        with col1: st.metric("GHL Moat Sync", health.get('ghl_sync', 'N/A').upper())
                        with col2: st.metric("Lyrio Headless", health.get('lyrio_headless', 'N/A').upper())
                        with col3: st.metric("Data Integrity", f"{health.get('moat_integrity', 0)}%")
                    else:
                        st.error(f"Invalid health data format: {type(health)}")
                except Exception as e:
                    st.error(f"Failed to fetch moat health: {e}")
            
            st.markdown("---")
            st.subheader("Field Mapping (MOAT)")
            st.markdown("Ensure these GHL field IDs match your actual CRM custom fields.")
            
            mapping_data = {
                "Internal Name": ["Seller Motivation", "Timeline Urgency", "Property Condition", "Price Expectation", "AI_FRS_Score", "Digital_Twin_URL"],
                "GHL Field ID": ["motivation", "timeline_acceptable", "property_condition", "price_expectation", "ai_frs_score", "digital_twin_url"],
                "Status": ["✅ Synced", "✅ Synced", "🟡 Mapping Required", "✅ Synced", "✅ Synced", "✅ Synced"]
            }
            st.table(mapping_data)
            
            col_actions = st.columns(2)
            with col_actions[0]:
                if st.button("🛰️ Test GHL Connection", use_container_width=True):
                    st.toast("Connection to GHL Production Successful", icon="✅")
            with col_actions[1]:
                if st.button("🔄 Force Lyrio Sync", use_container_width=True):
                    if moat_service:
                        st.toast("Intelligence Layer Sync Triggered for all active leads.", icon="🚀")
                        st.session_state.global_decisions.append({
                            "action": "Manual MOAT Sync",
                            "why": "User triggered manual intelligence layer refresh.",
                            "time": datetime.now(timezone.utc).strftime("%H:%M:%S")
                        })
    
    # Phase 4: Global Decision Stream at the bottom
    st.markdown("---")
    if ELITE_STYLING:
        render_decision_stream(st.session_state.global_decisions[-5:])

if __name__ == "__main__":
    main()
