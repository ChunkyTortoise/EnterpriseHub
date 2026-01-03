"""
Chat interface component - SMS-style conversation display.
"""
import streamlit as st


def render_chat_interface():
    """Render the chat conversation interface."""
    st.markdown("### 💬 Conversation")

    # Display message history
    messages = st.session_state.get('messages', [])

    for i, msg in enumerate(messages):
        if msg['role'] == 'user':
            # User message (right-aligned, blue background)
            st.markdown(f"""
            <div style='text-align: right; margin: 10px 0;'>
                <div style='display: inline-block; background-color: #007bff; color: white; padding: 10px 15px; border-radius: 18px; max-width: 70%;'>
                    {msg['content']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # AI message (left-aligned, gray background)
            st.markdown(f"""
            <div style='text-align: left; margin: 10px 0;'>
                <div style='display: inline-block; background-color: #f1f3f5; color: #212529; padding: 10px 15px; border-radius: 18px; max-width: 70%;'>
                    {msg['content']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Spacer
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
