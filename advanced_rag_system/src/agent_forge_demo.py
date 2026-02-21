"""
AgentForge Demo - Streamlit Cloud Deployment
Agent selection, chat interface, and handoff simulation
Mock data - no real API calls needed
"""

import time
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(page_title="AgentForge Demo", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")

# Custom CSS
st.markdown(
    """
<style>
    .agent-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #f093fb, #f5576c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .chat-message {
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        max-width: 80%;
    }
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: auto;
    }
    .agent-message {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        color: #333;
    }
    .handoff-badge {
        background: #FFD93D;
        color: #333;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .confidence-meter {
        height: 20px;
        border-radius: 10px;
        background: linear-gradient(90deg, #ff6b6b, #ffd93d, #6bcb77);
    }
</style>
""",
    unsafe_allow_html=True,
)

# Agent configurations
AGENTS = {
    "LeadBot": {
        "icon": "📋",
        "color": "#667eea",
        "description": "Initial lead qualification and routing",
        "system_prompt": "You are LeadBot, an AI assistant for real estate lead qualification. Gather contact info, assess needs, and route to appropriate specialist.",
        "example_inputs": ["I'm looking to buy a home", "Tell me about your services", "How can you help me?"],
    },
    "BuyerBot": {
        "icon": "🏠",
        "color": "#764ba2",
        "description": "Buyer-specific assistance and property matching",
        "system_prompt": "You are BuyerBot, specializing in helping home buyers. Understand budget, preferences, and guide through purchase process.",
        "example_inputs": ["I have a $600k budget", "What areas do you serve?", "I'm pre-approved and ready to buy"],
    },
    "SellerBot": {
        "icon": "🏡",
        "color": "#f093fb",
        "description": "Seller consultation and CMA assistance",
        "system_prompt": "You are SellerBot, helping home sellers prepare their property for sale. Provide CMA insights and selling recommendations.",
        "example_inputs": ["I want to sell my house", "What's my home worth?", "How do I prepare to sell?"],
    },
}

# Mock responses for demo
MOCK_RESPONSES = {
    "LeadBot": [
        "Great! I'd love to learn more about your real estate goals. Could you tell me a bit about what you're looking for - buying, selling, or just exploring the market?",
        "Thanks for your interest in EnterpriseHub! I can help connect you with the right resources. Are you primarily looking at the Rancho Cucamonga area, or are you open to nearby markets?",
        "I'd be happy to assist you. To make sure I direct you to the best specialist, could you share whether you're a first-time buyer or have bought homes before?",
    ],
    "BuyerBot": [
        "Excellent! A $600,000 budget in Rancho Cucatonga can get you a lovely 3-bedroom home. Let me ask - are you pre-approved, or still working on financing?",
        "That's a solid budget for our market. I've helped many buyers in your price range find great properties. What's most important to you - location, square footage, or specific amenities?",
        "With that budget, you should be looking at properties in the $550-650K range to leave room for negotiations. Have you been working with a lender yet?",
    ],
    "SellerBot": [
        "Selling a home is a big decision! I can help you understand current market conditions and what your property might be worth. When did you last have an appraisal or market assessment?",
        "Great timing - the Rancho Cucamonga market is showing strong 8.5% year-over-year growth. I'd recommend we start with a Comparative Market Analysis to establish your listing price.",
        "To prepare your home for sale, we typically look at recent sales of similar homes in your neighborhood. Would you like me to pull a preliminary CMA for your address?",
    ],
}

# Handoff triggers
HANDOFF_TRIGGERS = {
    "LeadBot": {
        "keywords": ["buy", "budget", "pre-approval", "pre approved", "looking for home"],
        "target": "BuyerBot",
        "threshold": 0.7,
    },
    "LeadBot_seller": {
        "keywords": ["sell", "my house", "my home", "listing", "worth"],
        "target": "SellerBot",
        "threshold": 0.7,
    },
    "BuyerBot": {"keywords": ["sell", "my current home", "listing"], "target": "SellerBot", "threshold": 0.65},
}


def initialize_session_state():
    """Initialize chat session state"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_agent" not in st.session_state:
        st.session_state.current_agent = "LeadBot"
    if "handoff_pending" not in st.session_state:
        st.session_state.handoff_pending = False
    if "handoff_target" not in st.session_state:
        st.session_state.handoff_target = None


def get_mock_response(agent, user_input):
    """Generate mock bot response"""
    np.random.seed(hash(user_input.lower()) % (2**32))

    responses = MOCK_RESPONSES.get(agent, MOCK_RESPONSES["LeadBot"])
    response = np.random.choice(responses)

    # Check for handoff triggers
    handoff_info = check_handoff_triggers(agent, user_input)

    return response, handoff_info


def check_handoff_triggers(agent, user_input):
    """Check if user input triggers a handoff"""
    user_lower = user_input.lower()

    if agent == "LeadBot":
        # Check for buyer signals
        for trigger in ["buy", "budget", "pre-approval", "pre approved", "looking for home"]:
            if trigger in user_lower:
                return {"target": "BuyerBot", "confidence": np.random.uniform(0.75, 0.92)}
        # Check for seller signals
        for trigger in ["sell", "my house", "my home", "listing", "worth"]:
            if trigger in user_lower:
                return {"target": "SellerBot", "confidence": np.random.uniform(0.75, 0.92)}

    if agent == "BuyerBot":
        for trigger in ["sell", "my current home", "listing"]:
            if trigger in user_lower:
                return {"target": "SellerBot", "confidence": np.random.uniform(0.70, 0.85)}

    return None


def display_chat_message(role, content, agent=None):
    """Display a chat message"""
    if role == "user":
        st.markdown(
            f"""
        <div class="chat-message user-message">
            <strong>👤 You:</strong><br>
            {content}
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        icon = AGENTS.get(agent, {}).get("icon", "🤖")
        st.markdown(
            f"""
        <div class="chat-message agent-message">
            <strong>{icon} {agent}:</strong><br>
            {content}
        </div>
        """,
            unsafe_allow_html=True,
        )


def main():
    """Main demo application"""
    initialize_session_state()

    # Header
    st.markdown('<div class="agent-header">🤖 AgentForge Demo</div>', unsafe_allow_html=True)
    st.markdown("**Multi-Agent Real Estate AI System** | Jorge Bot Network")

    # Sidebar
    with st.sidebar:
        st.title("🎭 Agent Selection")

        selected_agent = st.selectbox(
            "Choose an Agent",
            list(AGENTS.keys()),
            index=list(AGENTS.keys()).index(st.session_state.current_agent),
            format_func=lambda x: f"{AGENTS[x]['icon']} {x}",
        )

        if selected_agent != st.session_state.current_agent:
            st.session_state.current_agent = selected_agent
            st.session_state.messages = []
            st.session_state.handoff_pending = False

        # Agent info
        agent_info = AGENTS[selected_agent]
        st.markdown(f"""
        **{agent_info["icon"]} {selected_agent}**
        
        {agent_info["description"]}
        """)

        st.markdown("---")
        st.markdown("### 💬 Example Inputs")
        for inp in agent_info["example_inputs"]:
            if st.button(inp, key=f"input_{inp}"):
                st.session_state.pending_input = inp

        st.markdown("---")
        st.markdown("### 📊 Session Stats")
        if "messages" in st.session_state:
            st.metric("Messages", len(st.session_state.messages))
        if st.session_state.get("handoff_count", 0) > 0:
            st.metric("Handoffs", st.session_state.handoff_count)

        st.markdown("---")
        st.markdown("### ℹ️ Demo Mode")
        st.info("Using mock responses for demonstration. Connect to live Claude API for production.")

    # Handle pending input from button click
    if hasattr(st.session_state, "pending_input"):
        pending = st.session_state.pending_input
        del st.session_state.pending_input
        st.session_state.user_input = pending

    # Main chat area
    col1, col2 = st.columns([3, 1])

    with col1:
        # Chat messages
        st.subheader("💬 Conversation")

        if not st.session_state.messages:
            st.info(f"Start chatting with **{selected_agent}** to see the AI in action!")

        for msg in st.session_state.messages:
            display_chat_message(msg["role"], msg["content"], msg.get("agent"))

    with col2:
        # Confidence meter
        st.subheader("🎯 Confidence")

        if st.session_state.messages:
            last_conf = st.session_state.messages[-1].get("confidence", 0.85)
            st.markdown(
                f"""
            <div class="confidence-meter" style="width: {last_conf * 100}%;"></div>
            <p style="text-align: center;">{last_conf:.1%}</p>
            """,
                unsafe_allow_html=True,
            )

        # Handoff panel
        st.markdown("---")
        st.subheader("🔄 Handoff Status")

        if st.session_state.get("handoff_pending"):
            target = st.session_state.handoff_target
            st.markdown(
                f"""
            <div style="text-align: center; padding: 20px; background: #fff3cd; border-radius: 10px;">
                <span class="handoff-badge">🔀 Handoff to {target}</span>
                <p style="margin-top: 10px;">Confidence: {st.session_state.get("handoff_confidence", 0):.0%}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            if st.button("✅ Accept Handoff", type="primary"):
                st.session_state.current_agent = st.session_state.handoff_target
                st.session_state.messages.append(
                    {
                        "role": "system",
                        "content": f"🔄 **Handoff complete** - Now speaking with {st.session_state.handoff_target}",
                        "agent": "System",
                    }
                )
                st.session_state.handoff_pending = False
                st.session_state.handoff_target = None
                st.rerun()
        else:
            st.caption("No pending handoffs")

    # Input area
    st.markdown("---")

    # Check for handoff from previous message
    if st.session_state.get("handoff_pending"):
        st.warning(
            f"🤖 **{st.session_state.current_agent}** suggests handing off to **{st.session_state.handoff_target}**"
        )

    # User input
    user_input = st.text_input(
        "Type your message:",
        value=st.session_state.get("user_input", ""),
        placeholder="Ask about buying, selling, or real estate...",
        label_visibility="collapsed",
        key="input_field",
    )

    col1, col2, col3 = st.columns([5, 1, 1])

    with col1:
        pass  # Spacer

    with col2:
        send_btn = st.button("📤 Send", type="primary", disabled=not user_input)

    with col3:
        clear_btn = st.button("🗑️ Clear")

    # Handle send
    if send_btn and user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Generate mock response
        with st.spinner("Thinking..."):
            time.sleep(0.5)  # Simulate processing time
            response, handoff_info = get_mock_response(st.session_state.current_agent, user_input)

            # Add bot response
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": response,
                    "agent": st.session_state.current_agent,
                    "confidence": np.random.uniform(0.82, 0.96),
                }
            )

            # Check for handoff
            if handoff_info:
                st.session_state.handoff_pending = True
                st.session_state.handoff_target = handoff_info["target"]
                st.session_state.handoff_confidence = handoff_info["confidence"]
                st.session_state.handoff_count = st.session_state.get("handoff_count", 0) + 1

                st.session_state.messages.append(
                    {
                        "role": "system",
                        "content": f"💡 **Handoff Suggested** - {st.session_state.current_agent} recommends transferring to {handoff_info['target']} (confidence: {handoff_info['confidence']:.0%})",
                        "agent": "System",
                    }
                )

        # Clear input
        st.session_state.user_input = ""
        st.rerun()

    # Handle clear
    if clear_btn:
        st.session_state.messages = []
        st.session_state.handoff_pending = False
        st.session_state.handoff_target = None
        st.session_state.user_input = ""
        st.rerun()


if __name__ == "__main__":
    main()
