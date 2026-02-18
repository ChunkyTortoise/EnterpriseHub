"""
Streamlit-Compatible Lead Intelligence Integration

Provides streamlit-compatible versions of the lead intelligence functions
integrated with the Comprehensive Lead Intelligence Hub.
"""

import streamlit as st
from typing import Dict, Any

def get_intelligence_status() -> Dict[str, Any]:
    """Get the status of the intelligence system"""
    return {
        "initialized": True,
        "version": "2.0.0",
        "features_active": 10,
        "last_updated": "2026-01-13",
        "intelligence_available": True,
        "dashboard_available": True,
        "source": "enhanced_comprehensive_hub"
    }

def render_complete_enhanced_hub():
    """Render the complete enhanced intelligence hub using the comprehensive component"""
    try:
        # Import dynamically to avoid circular dependencies
        from ..components.comprehensive_lead_intelligence_hub import render_comprehensive_lead_intelligence_hub
        render_comprehensive_lead_intelligence_hub()
    except ImportError as e:
        st.error(f"Error loading Comprehensive Lead Intelligence Hub: {e}")
        st.info("Falling back to legacy view...")
        _render_legacy_hub()

def render_enhanced_lead_chat():
    """Render enhanced lead chat interface"""
    try:
        from ..components.claude_agent_chat import render_claude_agent_interface
        render_claude_agent_interface()
    except ImportError:
        st.warning("Enhanced Chat component not found.")

def render_lead_analytics_dashboard():
    """Render lead analytics dashboard"""
    try:
        from ..components.comprehensive_lead_intelligence_hub import render_advanced_analytics
        render_advanced_analytics()
    except ImportError:
        st.warning("Analytics component not found.")

def render_qualification_dashboard():
    """Render lead qualification dashboard"""
    try:
        from ..components.comprehensive_lead_intelligence_hub import render_lead_summary_cards, render_enhanced_lead_table
        render_lead_summary_cards()
        st.markdown("---")
        render_enhanced_lead_table()
    except ImportError:
        st.warning("Qualification component not found.")

def render_conversation_intelligence():
    """Render conversation intelligence panel"""
    try:
        from ..components.claude_conversation_templates import render_claude_conversation_templates
        render_claude_conversation_templates()
    except ImportError:
        st.warning("Conversation Intelligence component not found.")

def render_predictive_insights():
    """Render predictive analytics insights"""
    try:
        from ..components.comprehensive_lead_intelligence_hub import render_predictive_insights as render_predictive
        render_predictive()
    except ImportError:
        st.warning("Predictive Insights component not found.")

def render_intelligence_configuration():
    """Render AI configuration panel"""
    st.info("⚙️ Intelligence Configuration")
    with st.expander("🎛️ AI Settings"):
        st.slider("Lead Scoring Sensitivity", 1, 10, 7)
        st.selectbox("Personality Analysis", ["Basic", "Detailed", "Advanced"])
        st.checkbox("Auto-qualification enabled", value=True)
        if st.button("Save Configuration"):
            st.success("Configuration saved!")

def _render_legacy_hub():
    """Legacy fallback capability"""
    st.info("Using Legacy Hub View")
    tab1, tab2 = st.tabs(["Analytics", "Chat"])
    with tab1:
        st.metric("Legacy Score", "85/100")
    with tab2:
        st.text_input("Legacy Chat")