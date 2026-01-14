
"""
Enhanced Chat Interface with Real Claude AI Integration
Connects to the Claude Orchestrator via API for intelligent responses
"""
import streamlit as st
import requests
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional


def render_chat_interface(api_base_url: str = "http://localhost:8000/api"):
    """
    Production Chat Interface with Real Claude Integration

    Features:
    - Real Claude API integration via Claude Orchestrator
    - Memory persistence and conversation history
    - Lead context integration
    - Source tracking and citations
    - Streaming response support
    """
    st.markdown("### 💬 Claude Intelligence Chat")

    # Enhanced CSS for production chat
    st.markdown("""
    <style>
        .chat-container {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
            padding: 1rem;
            max-height: 600px;
            overflow-y: auto;
            background: rgba(248, 250, 252, 0.5);
            border-radius: 16px;
            border: 1px solid #e2e8f0;
        }

        .chat-bubble {
            max-width: 85%;
            padding: 1rem 1.25rem;
            border-radius: 16px;
            font-size: 0.95rem;
            line-height: 1.5;
            position: relative;
            animation: slideUp 0.3s ease-out;
        }

        .bubble-user {
            align-self: flex-end;
            background: var(--primary-gradient, linear-gradient(135deg, #006AFF 0%, #0049CC 100%));
            color: white;
            border-bottom-right-radius: 4px;
            box-shadow: 0 4px 12px rgba(0, 106, 255, 0.2);
        }

        .bubble-ai {
            align-self: flex-start;
            background: white;
            color: #1e293b;
            border-bottom-left-radius: 4px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }

        .agent-info {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .agent-name-ai { color: #8B5CF6; }
        .agent-name-user { color: #64748B; text-align: right; justify-content: flex-end; width: 100%; }

        .reasoning-section {
            background: #f8fafc;
            border-radius: 8px;
            padding: 0.75rem;
            margin-top: 0.75rem;
            font-size: 0.8rem;
            color: #475569;
            border-left: 3px solid #8B5CF6;
        }

        .sources-section {
            background: #f0f9ff;
            border-radius: 8px;
            padding: 0.75rem;
            margin-top: 0.75rem;
            font-size: 0.8rem;
            color: #0369a1;
            border-left: 3px solid #0ea5e9;
        }

        .status-pill {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 9999px;
            font-size: 0.7rem;
            background: #dcfce7;
            color: #166534;
            margin-left: 8px;
        }

        .error-message {
            background: #fef2f2;
            color: #dc2626;
            padding: 0.75rem;
            border-radius: 8px;
            margin-top: 0.5rem;
            border-left: 3px solid #dc2626;
        }
    </style>
    """, unsafe_allow_html=True)

    # Initialize chat state
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []

    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = f"demo_user_{int(time.time())}"

    # Get current lead context
    contact_id = st.session_state.conversation_id
    selected_lead = st.session_state.get('selected_lead_name', 'No lead selected')
    market = st.session_state.get('current_market', 'Austin')

    # Chat header with context
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #6D28D9 0%, #4C1D95 100%);
                padding: 1rem; border-radius: 12px; color: white; margin-bottom: 1rem;
                display: flex; justify-content: space-between; align-items: center;'>
        <div>
            <h4 style='margin: 0; color: white;'>🤖 Claude Intelligence</h4>
            <p style='margin: 0; opacity: 0.9; font-size: 0.85rem;'>Lead: {selected_lead} | Market: {market}</p>
        </div>
        <div style='text-align: right;'>
            <div style='font-size: 0.75rem; opacity: 0.8;'>Messages</div>
            <div style='font-size: 1.5rem; font-weight: bold;'>{len(st.session_state.chat_messages)}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Render chat messages
    render_chat_messages()

    # Chat input
    handle_chat_input(api_base_url, contact_id, selected_lead)


def render_chat_messages():
    """Render all chat messages with enhanced styling"""

    if not st.session_state.chat_messages:
        # Show welcome message
        st.markdown("""
        <div style='text-align: center; padding: 2rem; color: #64748b;'>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>💬</div>
            <h3 style='color: #475569; margin-bottom: 0.5rem;'>Chat with Claude</h3>
            <p style='margin: 0;'>Ask questions about leads, generate scripts, or get strategic insights</p>

            <div style='margin-top: 1.5rem; display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap;'>
                <div style='background: white; padding: 0.75rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); font-size: 0.8rem;'>
                    💡 "Draft an SMS for Sarah"
                </div>
                <div style='background: white; padding: 0.75rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); font-size: 0.8rem;'>
                    📊 "What's the pipeline status?"
                </div>
                <div style='background: white; padding: 0.75rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); font-size: 0.8rem;'>
                    🏠 "Find properties for David"
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    for i, msg in enumerate(st.session_state.chat_messages):
        is_ai = msg['role'] == 'assistant'
        bubble_class = "bubble-ai" if is_ai else "bubble-user"
        agent_name = 'Claude' if is_ai else 'Jorge'

        st.markdown(f"""
        <div style="display: flex; flex-direction: column; width: 100%; margin-bottom: 1rem;">
            <div class="agent-info {'agent-name-ai' if is_ai else 'agent-name-user'}">
                {f'🤖 {agent_name}' if is_ai else f'{agent_name} 👤'}
                <span style='font-size: 0.7rem; opacity: 0.7; margin-left: 8px;'>
                    {msg.get('timestamp', datetime.now().strftime('%H:%M'))}
                </span>
            </div>
            <div class="chat-bubble {bubble_class}">
                {msg['content']}

                {render_reasoning_section(msg) if is_ai and msg.get('reasoning') else ''}
                {render_sources_section(msg) if is_ai and msg.get('sources') else ''}
                {render_actions_section(msg) if is_ai and msg.get('recommended_actions') else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def render_reasoning_section(msg: Dict[str, Any]) -> str:
    """Render Claude's reasoning section"""
    if not msg.get('reasoning'):
        return ""

    return f"""
    <div class="reasoning-section">
        <strong>🧠 Claude's Reasoning:</strong><br>
        {msg['reasoning']}
    </div>
    """


def render_sources_section(msg: Dict[str, Any]) -> str:
    """Render sources section"""
    sources = msg.get('sources', [])
    if not sources:
        return ""

    sources_html = "<br>".join([f"• {source}" for source in sources])
    return f"""
    <div class="sources-section">
        <strong>📚 Sources:</strong><br>
        {sources_html}
    </div>
    """


def render_actions_section(msg: Dict[str, Any]) -> str:
    """Render recommended actions section"""
    actions = msg.get('recommended_actions', [])
    if not actions:
        return ""

    actions_html = "<br>".join([f"• {action.get('title', action) if isinstance(action, dict) else action}"
                               for action in actions])
    return f"""
    <div style="background: #f0fdf4; border-radius: 8px; padding: 0.75rem; margin-top: 0.75rem;
                font-size: 0.8rem; color: #166534; border-left: 3px solid #22c55e;">
        <strong>🎯 Recommended Actions:</strong><br>
        {actions_html}
    </div>
    """


def handle_chat_input(api_base_url: str, contact_id: str, selected_lead: str):
    """Handle chat input and API communication"""

    # Input area - Tab-safe Form Implementation
    with st.form(key="claude_chat_input_form", clear_on_submit=True):
        col_in, col_btn = st.columns([4, 1])
        with col_in:
            user_input = st.text_input("Ask Claude about leads, scripts, or strategic insights...", placeholder="Ask Claude about leads, scripts, or strategic insights...", label_visibility="collapsed")
        with col_btn:
            submit = st.form_submit_button("Ask ✨", use_container_width=True)

    if submit and user_input:
        # Add user message immediately
        user_msg = {
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().strftime("%H:%M")
        }
        st.session_state.chat_messages.append(user_msg)

        # Show thinking indicator
        with st.spinner("🧠 Claude is analyzing..."):
            try:
                # Call Claude API
                response = call_claude_api(
                    api_base_url=api_base_url,
                    message=user_input,
                    contact_id=contact_id,
                    selected_lead=selected_lead
                )

                if response and response.get('success'):
                    # Add AI response
                    ai_msg = {
                        "role": "assistant",
                        "content": response.get('message', 'No response received'),
                        "reasoning": response.get('reasoning'),
                        "sources": response.get('sources', []),
                        "recommended_actions": response.get('recommended_actions', []),
                        "timestamp": datetime.now().strftime("%H:%M"),
                        "response_time_ms": response.get('response_time_ms', 0)
                    }
                    st.session_state.chat_messages.append(ai_msg)

                    # Show success toast
                    st.toast(f"✅ Claude responded in {response.get('response_time_ms', 0)}ms")

                else:
                    # Handle API error
                    error_msg = {
                        "role": "assistant",
                        "content": f"⚠️ Sorry, I encountered an issue: {response.get('detail', 'Unknown error')}",
                        "timestamp": datetime.now().strftime("%H:%M")
                    }
                    st.session_state.chat_messages.append(error_msg)
                    st.error("Failed to get response from Claude")

            except Exception as e:
                # Handle connection error
                error_msg = {
                    "role": "assistant",
                    "content": f"🔌 Connection error: {str(e)}. Make sure the API server is running on {api_base_url}",
                    "timestamp": datetime.now().strftime("%H:%M")
                }
                st.session_state.chat_messages.append(error_msg)
                st.error(f"Connection failed: {str(e)}")

        # Rerun to show new messages
        st.rerun()


def call_claude_api(api_base_url: str, message: str, contact_id: str, selected_lead: str) -> Optional[Dict[str, Any]]:
    """Make API call to Claude chat endpoint"""

    payload = {
        "message": message,
        "contact_id": contact_id,
        "selected_lead_name": selected_lead if selected_lead != "-- Select a Lead --" else None,
        "conversation_mode": "chat",
        "include_context": True,
        "stream": False
    }

    try:
        response = requests.post(
            f"{api_base_url}/claude/query",
            json=payload,
            timeout=30,  # 30 second timeout
            headers={"Content-Type": "application/json"}
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return {"success": False, "detail": str(e)}
    except json.JSONDecodeError as e:
        print(f"Failed to decode API response: {e}")
        return {"success": False, "detail": "Invalid response format"}


# Legacy functions for backward compatibility
def render_chat_interface_legacy():
    """Legacy mock chat interface"""
    render_chat_interface()


def simulate_typing():
    """Simulates a typing effect for better demo experience"""
    with st.empty():
        for i in range(3):
            st.markdown(f"Claude is thinking{'.' * (i+1)}")
            time.sleep(0.5)


# Export main function
__all__ = ['render_chat_interface', 'simulate_typing']
