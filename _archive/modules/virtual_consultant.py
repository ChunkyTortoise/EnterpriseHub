"""
Virtual Consultant Module
Implements the Persona-Orchestrator logic from PERSONA0.md as a functional chat widget.
Acts as an automated 'Virtual Architect' for lead intake and strategy alignment.
"""

import streamlit as st
import os
from datetime import datetime
from typing import List, Dict, Any

# Conditional imports
try:
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

import utils.ui as ui
from utils.logger import get_logger

logger = get_logger(__name__)

def load_persona_prompt():
    """Load the Persona-Orchestrator prompt from PERSONA0.md."""
    persona_path = "docs/PERSONA0.md"
    if not os.path.exists(persona_path):
        # Fallback if path is different (e.g. running from different dir)
        persona_path = "enterprisehub/docs/PERSONA0.md"
    
    try:
        with open(persona_path, "r") as f:
            content = f.read()
            # Extract the markdown content between the first and second ```markdown if it exists, 
            # or just take the whole file if it's the orchestrator prompt.
            if "```markdown" in content:
                parts = content.split("```markdown")
                if len(parts) > 1:
                    return parts[1].split("```")[0].strip()
            return content
    except Exception as e:
        logger.error(f"Error loading PERSONA0.md: {e}")
        return "You are a helpful AI Assistant specialized in AI Strategy."

def render():
    """Render the Virtual Consultant chat interface."""
    st.markdown("---")
    ui.section_header("🤖 Virtual AI Architect", "Strategic Lead Intake & Strategy Alignment")
    
    if not ANTHROPIC_AVAILABLE:
        st.error("Anthropic libraries not available. Please install `langchain-anthropic`.")
        return

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        st.warning("⚠️ ANTHROPIC_API_KEY not found in environment. Chat functionality will be limited to UI demonstration.")
        # We can still show the UI but maybe disable the input or mock the response
    
    # Initialize session state for chat
    if "consultant_messages" not in st.session_state:
        st.session_state.consultant_messages = [
            {"role": "assistant", "content": "Welcome! I am your Virtual AI Architect. I'm here to help you navigate our 31-service catalog and design a custom AI strategy for your business. \n\nWhat challenge can I help you solve today?"}
        ]

    # Display chat history
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.consultant_messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    # Chat input
    if prompt := st.chat_input("Describe your business challenge or goal..."):
        # Add user message
        st.session_state.consultant_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # Generate response
        with st.chat_message("assistant"):
            if not api_key:
                response = "I'm currently in 'UI Demo Mode' because no API key was provided. In a live environment, I would analyze your request using the Persona-Orchestrator logic to classify your task and guide you through a strategic diagnostic."
                st.write(response)
                st.session_state.consultant_messages.append({"role": "assistant", "content": response})
            else:
                with st.spinner("Architecting response..."):
                    try:
                        llm = ChatAnthropic(
                            model="claude-3-5-sonnet-20240620",
                            anthropic_api_key=api_key,
                            temperature=0.2
                        )
                        
                        system_prompt = load_persona_prompt()
                        
                        messages = [SystemMessage(content=system_prompt)]
                        for m in st.session_state.consultant_messages:
                            if m["role"] == "user":
                                messages.append(HumanMessage(content=m["content"]))
                            else:
                                messages.append(AIMessage(content=m["content"]))
                        
                        response = llm.invoke(messages)
                        content = response.content
                        
                        st.write(content)
                        st.session_state.consultant_messages.append({"role": "assistant", "content": content})
                    except Exception as e:
                        error_msg = f"I encountered an error while processing your request: {str(e)}"
                        st.error(error_msg)
                        logger.error(f"Chat error: {e}")

    # Sidebar clear button
    with st.sidebar:
        if st.button("Clear Consultant Chat", key="clear_consultant"):
            st.session_state.consultant_messages = [
                {"role": "assistant", "content": "Welcome! I am your Virtual AI Architect. I'm here to help you navigate our 31-service catalog and design a custom AI strategy for your business. \n\nWhat challenge can I help you solve today?"}
            ]
            st.rerun()
