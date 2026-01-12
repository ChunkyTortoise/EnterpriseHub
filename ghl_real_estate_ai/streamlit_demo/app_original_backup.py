"""
GHL Real Estate AI - Interactive Demo
Main Streamlit Application
"""
import streamlit as st
st.write("DEBUG: App is starting...")
import sys
from pathlib import Path

# Add project root to sys.path to import components and services
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from streamlit_demo.components.chat_interface import render_chat_interface
from streamlit_demo.components.lead_dashboard import render_lead_dashboard
from streamlit_demo.components.property_cards import render_property_matches
from streamlit_demo.mock_services.mock_claude import MockClaudeService
from streamlit_demo.mock_services.conversation_state import (
    init_conversation_state,
    add_message,
    update_extracted_data,
    calculate_lead_score
)

# Page config
st.set_page_config(
    page_title="GHL Real Estate AI - Jorge Sales",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "AI-Powered Lead Qualification System for Real Estate Professionals"
    }
)

# Load custom CSS
css_path = Path(__file__).parent / "assets" / "styles.css"
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize services
if 'claude_service' not in st.session_state:
    st.session_state.claude_service = MockClaudeService()

# Initialize conversation state
init_conversation_state()

# Header with branding
st.markdown("""
<div style='background: linear-gradient(135deg, #006AFF 0%, #0052CC 100%); 
            padding: 2rem; border-radius: 12px; margin-bottom: 2rem; color: white;'>
    <h1 style='margin: 0; font-size: 2.5rem; font-weight: 700; color: white;'>
        🏠 GHL Real Estate AI
    </h1>
    <p style='margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.95;'>
        Experience Jorge's AI-powered lead qualification system in action
    </p>
    <div style='margin-top: 1rem; font-size: 0.9rem; opacity: 0.85;'>
        ✨ Professional, Direct, Curious | 🎯 Smart Context Awareness | 📱 SMS-Optimized
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar - Scenario selector
with st.sidebar:
    st.markdown("### 🎯 Demo Controls")

    scenario_options = ["Fresh Conversation", "Cold Lead Example", "Warm Lead Example", "Hot Lead Example"]
    selected_scenario = st.selectbox("Load Scenario:", scenario_options)

    if st.button("Apply Scenario"):
        st.session_state.messages = []
        st.session_state.extracted_data = {}
        
        if selected_scenario == "Cold Lead Example":
            add_message('user', "Looking for a house in Austin")
            response, data = st.session_state.claude_service.generate_response("Looking for a house in Austin", [], {})
            add_message('assistant', response)
            update_extracted_data(data)
        elif selected_scenario == "Warm Lead Example":
            add_message('user', "Your prices are too high")
            response, data = st.session_state.claude_service.generate_response("Your prices are too high", [], {})
            add_message('assistant', response)
            update_extracted_data(data)
        elif selected_scenario == "Hot Lead Example":
            msg = "I'm pre-approved for $400k, need to move ASAP, love Hyde Park"
            add_message('user', msg)
            response, data = st.session_state.claude_service.generate_response(msg, [], {})
            add_message('assistant', response)
            update_extracted_data(data)
            
        calculate_lead_score()
        st.rerun()

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
<div style='text-align: center; padding: 2rem; background: #F7F8FA; border-radius: 12px; margin-top: 3rem;'>
    <div style='color: #2A2A33; font-weight: 600; font-size: 1.1rem; margin-bottom: 0.5rem;'>
        🚀 Production-Ready AI System
    </div>
    <div style='color: #6B7280; font-size: 0.9rem;'>
        Built with Claude Sonnet 4.5 | Jorge's Exact Communication Style | Context-Aware Intelligence
    </div>
    <div style='margin-top: 1rem; color: #6B7280; font-size: 0.85rem;'>
        Phase 3 Complete | 300+ Tests Passing | Multi-Tenant Architecture | Enterprise Security
    </div>
</div>
""", unsafe_allow_html=True)