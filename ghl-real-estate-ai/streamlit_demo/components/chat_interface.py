"""
Chat interface component - SMS-style conversation display.
"""
import streamlit as st
from streamlit_chat import message


def render_chat_interface():
    """Render the chat conversation interface."""
    st.markdown("### 💬 Conversation")

    # Display message history
    messages = st.session_state.get('messages', [])

    for i, msg in enumerate(messages):
        if msg['role'] == 'user':
            message(msg['content'], is_user=True, key=f"user_{i}")
        else:
            message(msg['content'], is_user=False, key=f"ai_{i}")

    # Spacer
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)