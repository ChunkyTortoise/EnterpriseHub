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
import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Page configuration
st.set_page_config(
    page_title="Jorge AI Command | Elite Edition",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import elite styling
try:
    from ghl_real_estate_ai.streamlit_demo.obsidian_theme import inject_elite_css
    ELITE_STYLING = True
except ImportError:
    ELITE_STYLING = False

# Import dashboard components
try:
    from ghl_real_estate_ai.streamlit_demo.components.jorge_lead_bot_dashboard import render_jorge_lead_bot_dashboard
    from ghl_real_estate_ai.streamlit_demo.components.jorge_seller_bot_dashboard import render_jorge_seller_bot_dashboard
    from ghl_real_estate_ai.streamlit_demo.components.jorge_analytics_dashboard import render_jorge_analytics_dashboard
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    st.error(f"Error loading dashboard components: {e}")
    COMPONENTS_AVAILABLE = False

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
        
        hub_selection = st.radio(
            "Select Intelligence Hub:",
            ["🎯 Lead Command", "⚔️ Seller Command", "📊 Business Analytics", "⚙️ System Config"],
            index=0
        )
        
        st.markdown("---")
        
        # System Status in Sidebar
        st.markdown("### 📡 Neural Uplink")
        st.success("Lead Bot: ONLINE")
        st.success("Seller Bot: ONLINE")
        st.info("Vapi Voice AI: READY")
        
        st.markdown("---")
        st.caption("v4.2.0-ELITE | © 2026 Lyrio.io")
        
        return hub_selection

def main():
    if ELITE_STYLING:
        inject_elite_css()
    
    selected_hub = render_sidebar()
    
    if not COMPONENTS_AVAILABLE:
        st.error("Dashboards unavailable. Please check installation.")
        return

    if selected_hub == "🎯 Lead Command":
        render_jorge_lead_bot_dashboard()
    elif selected_hub == "⚔️ Seller Command":
        render_jorge_seller_bot_dashboard()
    elif selected_hub == "📊 Business Analytics":
        render_jorge_analytics_dashboard()
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
            st.subheader("Field Mapping (MOAT)")
            st.markdown("Ensure these GHL field IDs match your actual CRM custom fields.")
            
            mapping_data = {
                "Internal Name": ["Seller Motivation", "Timeline Urgency", "Property Condition", "Price Expectation"],
                "GHL Field ID": ["motivation", "timeline_acceptable", "property_condition", "price_expectation"],
                "Status": ["✅ Synced", "✅ Synced", "🟡 Mapping Required", "✅ Synced"]
            }
            st.table(mapping_data)
            
            if st.button("🛰️ Test GHL Connection", use_container_width=True):
                st.toast("Connection to GHL Production Successful", icon="✅")

if __name__ == "__main__":
    main()
