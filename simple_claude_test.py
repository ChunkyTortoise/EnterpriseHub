# Create: /Users/cave/enterprisehub/simple_claude_test.py
import streamlit as st
import json
from datetime import datetime

def test_claude_integration():
    st.title("🤖 Claude Integration Test")

    # Test 1: Basic greeting
    st.header("Test 1: Claude Greeting")
    if st.button("Show Claude Greeting"):
        st.balloons()
        st.success("👋 Hello! I'm Claude, your AI assistant for lead intelligence and real estate insights.")
        st.info("✅ Claude greeting is working!")

    # Test 2: Chat interface
    st.header("Test 2: Basic Chat")

    if "test_chat" not in st.session_state:
        st.session_state.test_chat = [
            {"role": "claude", "content": "Hi! I'm ready to help with lead analysis!", "time": "now"}
        ]

    # Display messages
    for msg in st.session_state.test_chat:
        if msg["role"] == "claude":
            st.info(f"🤖 Claude: {msg['content']}")
        else:
            st.success(f"👤 You: {msg['content']}")

    # Input
    user_input = st.text_input("Ask Claude something:", key="test_input")

    if st.button("Send to Claude", key="test_send"):
        if user_input:
            # Add user message
            st.session_state.test_chat.append({
                "role": "user",
                "content": user_input,
                "time": datetime.now().strftime("%H:%M")
            })

            # Add Claude response
            claude_response = f"I understand you're asking about: '{user_input}'. This is a test response showing Claude is working!"
            st.session_state.test_chat.append({
                "role": "claude",
                "content": claude_response,
                "time": datetime.now().strftime("%H:%M")
            })

            st.rerun()

    # Test 3: Context awareness
    st.header("Test 3: Context Tracking")

    if "claude_context" not in st.session_state:
        st.session_state.claude_context = {"section": "test", "user": "Jorge"}

    st.json(st.session_state.claude_context)

    if st.button("Update Context"):
        st.session_state.claude_context["section"] = "lead_intelligence"
        st.session_state.claude_context["timestamp"] = datetime.now().isoformat()
        st.rerun()

if __name__ == "__main__":
    test_claude_integration()