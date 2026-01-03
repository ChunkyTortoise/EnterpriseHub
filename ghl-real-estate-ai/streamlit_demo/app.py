"""
GHL Real Estate AI - Interactive Demo
Main Streamlit Application
"""
import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from components.chat_interface import render_chat_interface
from components.lead_dashboard import render_lead_dashboard
from components.property_cards import render_property_matches
from mock_services.mock_claude import MockClaudeService
from mock_services.conversation_state import (
    init_conversation_state,
    add_message,
    update_extracted_data,
    calculate_lead_score
)

# Page config
st.set_page_config(
    page_title="GHL Real Estate AI Demo",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize services
if 'claude_service' not in st.session_state:
    st.session_state.claude_service = MockClaudeService()

# Initialize conversation state
init_conversation_state()

# Title
st.title("🏠 GHL Real Estate AI - Interactive Demo")
st.markdown("**Experience AI-powered lead qualification in real-time**")
st.markdown("---")

# Sidebar - Scenario selector
with st.sidebar:
    st.markdown("### 🎯 Demo Controls")

    scenario = st.selectbox(
        "Load Scenario:",
        ["Fresh Conversation", "Cold Lead Example", "Warm Lead Example", "Hot Lead Example"]
    )

    if st.button("Reset Conversation"):
        st.session_state.messages = []
        st.session_state.extracted_data = {}
        st.session_state.lead_score = 0
        st.session_state.tags = []
        st.rerun()

    st.markdown("---")
    st.markdown("### 💡 Try These:")
    st.markdown("""
    **Cold Lead:**
    - "Looking for a house in Austin"

    **Objection:**
    - "Your prices are too high"

    **Hot Lead:**
    - "I'm pre-approved for $400k, need to move ASAP, love Hyde Park"
    """)

# Main layout - 2 columns
col1, col2 = st.columns([2, 1])

with col1:
    # Chat interface
    render_chat_interface()

    # User input
    user_input = st.chat_input("Type your message here...")

    if user_input:
        # Add user message
        add_message('user', user_input)

        # Generate AI response
        response, updated_data = st.session_state.claude_service.generate_response(
            user_input,
            st.session_state.messages,
            st.session_state.extracted_data
        )

        # Update state
        add_message('assistant', response)
        update_extracted_data(updated_data)
        calculate_lead_score()

        # Rerun to update UI
        st.rerun()

with col2:
    # Lead intelligence dashboard
    render_lead_dashboard()

# Bottom section - Property matches
st.markdown("---")
render_property_matches()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    <p>🤖 Built with Claude Sonnet 4.5 | 📊 Lead Scoring Algorithm | 🏠 RAG-Powered Property Matching</p>
    <p>This is a demo environment - production deployment ready after approval</p>
</div>
""", unsafe_allow_html=True)
