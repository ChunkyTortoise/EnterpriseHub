"""Session state initialization for the Streamlit demo app."""

import datetime

import streamlit as st


def init_session_state():
    """Initialize all session state variables with defaults."""
    if "current_hub" not in st.session_state:
        st.session_state.current_hub = "Jorge AI Landing Page"
    if "selected_market" not in st.session_state:
        st.session_state.selected_market = "Rancho Cucamonga, CA"
    if "ai_tone" not in st.session_state:
        st.session_state.ai_tone = "Natural"
    if "elite_mode" not in st.session_state:
        st.session_state.elite_mode = False
    if "claude_greeting_shown" not in st.session_state:
        st.session_state.claude_greeting_shown = False
    if "claude_session_initialized" not in st.session_state:
        st.session_state.claude_session_initialized = False
    if "show_claude_sidebar" not in st.session_state:
        st.session_state.show_claude_sidebar = True
    if "ghl_verified" not in st.session_state:
        st.session_state.ghl_verified = False

    # Initialize Global AI State
    if "ai_config" not in st.session_state:
        st.session_state.ai_config = {
            "market": "Rancho Cucamonga, CA",
            "voice_tone": 0.5,  # 0.0 = Professional, 1.0 = Natural
            "response_speed": "Standard",
            "last_sync": datetime.datetime.now().strftime("%H:%M:%S"),
        }

    # Initialize Prompt Versioning
    if "prompt_versions" not in st.session_state:
        st.session_state.prompt_versions = [
            {
                "version": "v1.0",
                "tag": "Baseline",
                "content": "You are a helpful assistant.",
                "timestamp": "2026-01-01",
            },
            {
                "version": "v1.1",
                "tag": "Production",
                "content": "You are a professional real estate assistant.",
                "timestamp": "2026-01-05",
            },
            {
                "version": "v1.2",
                "tag": "Elite v4.0",
                "content": "You are an elite Real Estate AI closer.",
                "timestamp": "2026-01-11",
            },
        ]
