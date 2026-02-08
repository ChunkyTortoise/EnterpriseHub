import streamlit as st


def render_claude_assistant(claude):
    """Delegates to the centralized ClaudeAssistant service."""
    leads = st.session_state.get("lead_options", {})
    hub = st.session_state.current_hub
    market = st.session_state.get("selected_market", "Austin")

    claude.greet_user("Jorge")
    claude.render_sidebar_panel(hub, market, leads)
