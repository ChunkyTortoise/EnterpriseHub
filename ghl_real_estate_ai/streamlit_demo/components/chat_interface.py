"""
Enhanced Chat Interface with Real Claude AI Integration
Connects to the Claude Orchestrator via API for intelligent responses
"""

import json
import time
from datetime import datetime
from typing import Any, Dict, Optional

import requests
import streamlit as st


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

    # Enhanced CSS for production chat - Obsidian Edition
    st.markdown(
        """

        <style>

            .chat-container {

                display: flex;

                flex-direction: column;

                gap: 1.5rem;

                padding: 1.5rem;

                max-height: 600px;

                overflow-y: auto;

                background: rgba(5, 7, 10, 0.6);

                border-radius: 16px;

                border: 1px solid rgba(255, 255, 255, 0.05);

                backdrop-filter: blur(10px);

                box-shadow: inset 0 0 20px rgba(0,0,0,0.5);

            }

    

            .chat-bubble {

                max-width: 85%;

                padding: 1.25rem 1.5rem;

                border-radius: 12px;

                font-size: 0.95rem;

                line-height: 1.6;

                position: relative;

                animation: slideUp 0.3s ease-out;

                font-family: 'Inter', sans-serif;

            }

    

            .bubble-user {

                align-self: flex-end;

                background: rgba(99, 102, 241, 0.1);

                color: #E6EDF3;

                border: 1px solid rgba(99, 102, 241, 0.3);

                border-bottom-right-radius: 4px;

                box-shadow: 0 4px 15px rgba(99, 102, 241, 0.1);

            }

    

            .bubble-ai {

                align-self: flex-start;

                background: rgba(22, 27, 34, 0.8);

                color: #FFFFFF;

                border-bottom-left-radius: 4px;

                border: 1px solid rgba(255, 255, 255, 0.1);

                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);

            }

    

            .agent-info {

                display: flex;

                align-items: center;

                gap: 8px;

                margin-bottom: 8px;

                font-size: 0.7rem;

                font-weight: 700;

                text-transform: uppercase;

                letter-spacing: 0.1em;

                font-family: 'Space Grotesk', sans-serif;

            }

    

            .agent-name-ai { color: #6366F1; }

            .agent-name-user { color: #8B949E; text-align: right; justify-content: flex-end; width: 100%; }

    

            .reasoning-section {

                background: rgba(99, 102, 241, 0.05);

                border-radius: 8px;

                padding: 1rem;

                margin-top: 1rem;

                font-size: 0.85rem;

                color: #E6EDF3;

                border-left: 3px solid #6366F1;

                border: 1px solid rgba(99, 102, 241, 0.1);

                border-left: 3px solid #6366F1;

            }

    

            .sources-section {

                background: rgba(255, 255, 255, 0.02);

                border-radius: 8px;

                padding: 1rem;

                margin-top: 1rem;

                font-size: 0.85rem;

                color: #8B949E;

                border-left: 3px solid rgba(255, 255, 255, 0.2);

            }

    

            .status-pill {

                display: inline-block;

                padding: 2px 8px;

                border-radius: 4px;

                font-size: 0.65rem;

                background: rgba(16, 185, 129, 0.1);

                color: #10b981;

                margin-left: 8px;

                font-weight: 700;

                text-transform: uppercase;

                border: 1px solid rgba(16, 185, 129, 0.2);

            }

        </style>

        """,
        unsafe_allow_html=True,
    )

    # Initialize chat state
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = f"demo_user_{int(time.time())}"

    # Get current lead context
    contact_id = st.session_state.conversation_id
    selected_lead = st.session_state.get("selected_lead_name", "No lead selected")
    market = st.session_state.get("current_market", "Austin")

    # Chat header with context - Obsidian Command Edition
    st.markdown(
        f"""
    <div style='background: linear-gradient(135deg, #05070A 0%, #1E1B4B 100%);
                padding: 1.25rem 1.5rem; border-radius: 12px; color: white; margin-bottom: 1.5rem;
                display: flex; justify-content: space-between; align-items: center;
                border: 1px solid rgba(255,255,255,0.05); border-top: 1px solid rgba(255,255,255,0.1);
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.6);'>
        <div>
            <h4 style='margin: 0; color: white; font-family: "Space Grotesk", sans-serif; letter-spacing: 0.05em; text-transform: uppercase;'>🤖 CLAUDE INTELLIGENCE</h4>
            <p style='margin: 0.25rem 0 0 0; opacity: 0.7; font-size: 0.8rem; font-family: "Inter", sans-serif; font-weight: 500;'>NODE: {selected_lead.upper()} | SECTOR: {market.upper()}</p>
        </div>
        <div style='text-align: right;'>
            <div style='font-size: 0.65rem; opacity: 0.6; text-transform: uppercase; font-weight: 700; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif;'>Signals</div>
            <div style='font-size: 1.5rem; font-weight: 700; color: #6366F1; font-family: "Space Grotesk", sans-serif;'>{len(st.session_state.chat_messages)}</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Render chat messages
    render_chat_messages()

    # Chat input
    handle_chat_input(api_base_url, contact_id, selected_lead)


def render_chat_messages():
    """Render all chat messages with enhanced styling"""

    if not st.session_state.chat_messages:
        # Show welcome message - Obsidian Edition
        st.markdown(
            """
        <div style='text-align: center; padding: 3rem 2rem; color: #8B949E;'>
            <div style='font-size: 3.5rem; margin-bottom: 1.5rem; filter: drop-shadow(0 0 15px rgba(99, 102, 241, 0.3));'>💬</div>
            <h3 style='color: #FFFFFF; margin-bottom: 0.75rem; font-family: "Space Grotesk", sans-serif; text-transform: uppercase; letter-spacing: 0.05em;'>Neural Command Link</h3>
            <p style='margin: 0; font-family: "Inter", sans-serif; font-size: 1rem; opacity: 0.8;'>Initialize query for lead intelligence, script synthesis, or strategic modeling.</p>

            <div style='margin-top: 2.5rem; display: flex; justify-content: center; gap: 1.25rem; flex-wrap: wrap;'>
                <div style='background: rgba(22, 27, 34, 0.7); padding: 1rem 1.5rem; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 4px 15px rgba(0,0,0,0.3); font-size: 0.85rem; color: #E6EDF3; font-family: "Inter", sans-serif;'>
                    <span style="color: #6366F1; font-weight: 700;">▷</span> "Draft an SMS for Sarah"
                </div>
                <div style='background: rgba(22, 27, 34, 0.7); padding: 1rem 1.5rem; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 4px 15px rgba(0,0,0,0.3); font-size: 0.85rem; color: #E6EDF3; font-family: "Inter", sans-serif;'>
                    <span style="color: #6366F1; font-weight: 700;">▷</span> "Analyze current pipeline velocity"
                </div>
                <div style='background: rgba(22, 27, 34, 0.7); padding: 1rem 1.5rem; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 4px 15px rgba(0,0,0,0.3); font-size: 0.85rem; color: #E6EDF3; font-family: "Inter", sans-serif;'>
                    <span style="color: #6366F1; font-weight: 700;">▷</span> "Synthesize property matches for David"
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        return

    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    for i, msg in enumerate(st.session_state.chat_messages):
        is_ai = msg["role"] == "assistant"
        bubble_class = "bubble-ai" if is_ai else "bubble-user"
        agent_name = "Claude" if is_ai else "Jorge"

        st.markdown(
            f"""
        <div style="display: flex; flex-direction: column; width: 100%; margin-bottom: 1rem;">
            <div class="agent-info {"agent-name-ai" if is_ai else "agent-name-user"}">
                {f"🤖 {agent_name}" if is_ai else f"{agent_name} 👤"}
                <span style='font-size: 0.7rem; opacity: 0.7; margin-left: 8px;'>
                    {msg.get("timestamp", datetime.now().strftime("%H:%M"))}
                </span>
            </div>
            <div class="chat-bubble {bubble_class}">
                {msg["content"]}

                {render_tool_executions(msg) if is_ai and msg.get("tool_executions") else ""}
                {render_reasoning_section(msg) if is_ai and msg.get("reasoning") else ""}
                {render_sources_section(msg) if is_ai and msg.get("sources") else ""}
                {render_actions_section(msg) if is_ai and msg.get("recommended_actions") else ""}
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def render_tool_executions(msg: Dict[str, Any]) -> str:
    """Render the tool orchestration process (Phase 2 UI Bridge)"""
    executions = msg.get("tool_executions", [])
    if not executions:
        return ""

    tools_html = ""
    for step in executions:
        if "tool_calls" in step:
            for tc in step["tool_calls"]:
                tools_html += f"""
                <div style="margin: 8px 0; padding: 8px; background: rgba(99, 102, 241, 0.1); border-radius: 6px; border: 1px solid rgba(99, 102, 241, 0.2);">
                    <div style="font-size: 0.7rem; color: #6366F1; font-weight: bold; text-transform: uppercase;">🛠️ Calling Tool</div>
                    <div style="font-family: 'Space Mono', monospace; font-size: 0.8rem; margin: 4px 0;">{tc["name"]}({json.dumps(tc["args"])})</div>
                </div>
                """
        elif "content" in step and "Tool Result" in str(step["content"]):
            # Handle old format if present, but new format is list of dicts with type: tool_result
            pass
        elif isinstance(step.get("content"), list):
            for block in step["content"]:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    # Shorten long results
                    res = str(block.get("content", ""))
                    if len(res) > 200:
                        res = res[:197] + "..."

                    tools_html += f"""
                    <div style="margin: 8px 0; padding: 8px; background: rgba(16, 185, 129, 0.05); border-radius: 6px; border: 1px solid rgba(16, 185, 129, 0.1);">
                        <div style="font-size: 0.7rem; color: #10b981; font-weight: bold; text-transform: uppercase;">📥 Result</div>
                        <div style="font-family: 'Space Mono', monospace; font-size: 0.75rem; margin: 4px 0; opacity: 0.8;">{res}</div>
                    </div>
                    """

    return f"""
    <div style="margin-top: 1rem; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 1rem;">
        <div style="font-size: 0.65rem; color: #8B949E; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px; font-weight: 700;">Tool Orchestration Log</div>
        {tools_html}
    </div>
    """


def render_reasoning_section(msg: Dict[str, Any]) -> str:
    """Render Claude's reasoning section"""
    if not msg.get("reasoning"):
        return ""

    return f"""
    <div class="reasoning-section">
        <strong>🧠 Claude's Reasoning:</strong><br>
        {msg["reasoning"]}
    </div>
    """


def render_sources_section(msg: Dict[str, Any]) -> str:
    """Render sources section"""
    sources = msg.get("sources", [])
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
    """Render recommended actions section - Obsidian Style"""
    actions = msg.get("recommended_actions", [])
    if not actions:
        return ""

    actions_html = "".join(
        [
            f'<div style="margin: 6px 0; display: flex; align-items: center; gap: 8px;"><span style="color: #10b981; font-weight: bold;">✓</span> <span>{action.get("title", action) if isinstance(action, dict) else action}</span></div>'
            for action in actions
        ]
    )
    return f"""
    <div style="background: rgba(16, 185, 129, 0.05); border-radius: 8px; padding: 1rem; margin-top: 1rem;
                font-size: 0.85rem; color: #E6EDF3; border-left: 3px solid #10b981; border: 1px solid rgba(16, 185, 129, 0.1); border-left: 3px solid #10b981;">
        <strong style="color: #10b981; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">Recommended Directives:</strong><br>
        <div style="margin-top: 8px; opacity: 0.9;">
            {actions_html}
        </div>
    </div>
    """


def handle_chat_input(api_base_url: str, contact_id: str, selected_lead: str):
    """Handle chat input and API communication"""

    # Input area - Tab-safe Form Implementation
    with st.form(key="claude_chat_input_form", clear_on_submit=True):
        col_in, col_btn = st.columns([4, 1])
        with col_in:
            user_input = st.text_input(
                "Ask Claude about leads, scripts, or strategic insights...",
                placeholder="Ask Claude about leads, scripts, or strategic insights...",
                label_visibility="collapsed",
            )
        with col_btn:
            submit = st.form_submit_button("Ask ✨", use_container_width=True)

    if submit and user_input:
        # Add user message immediately
        user_msg = {"role": "user", "content": user_input, "timestamp": datetime.now().strftime("%H:%M")}
        st.session_state.chat_messages.append(user_msg)

        # Show thinking indicator
        with st.spinner("🧠 Claude is analyzing..."):
            try:
                # Call Claude API
                response = call_claude_api(
                    api_base_url=api_base_url, message=user_input, contact_id=contact_id, selected_lead=selected_lead
                )

                if response and response.get("success"):
                    # Add AI response
                    ai_msg = {
                        "role": "assistant",
                        "content": response.get("message", "No response received"),
                        "reasoning": response.get("reasoning"),
                        "sources": response.get("sources", []),
                        "recommended_actions": response.get("recommended_actions", []),
                        "tool_executions": response.get("tool_executions", []),
                        "timestamp": datetime.now().strftime("%H:%M"),
                        "response_time_ms": response.get("response_time_ms", 0),
                    }
                    st.session_state.chat_messages.append(ai_msg)

                    # Show success toast
                    st.toast(f"✅ Claude responded in {response.get('response_time_ms', 0)}ms")

                else:
                    # Handle API error
                    error_msg = {
                        "role": "assistant",
                        "content": f"⚠️ Sorry, I encountered an issue: {response.get('detail', 'Unknown error')}",
                        "timestamp": datetime.now().strftime("%H:%M"),
                    }
                    st.session_state.chat_messages.append(error_msg)
                    st.error("Failed to get response from Claude")

            except Exception as e:
                # Handle connection error
                error_msg = {
                    "role": "assistant",
                    "content": f"🔌 Connection error: {str(e)}. Make sure the API server is running on {api_base_url}",
                    "timestamp": datetime.now().strftime("%H:%M"),
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
        "stream": False,
    }

    try:
        response = requests.post(
            f"{api_base_url}/claude/query",
            json=payload,
            timeout=30,  # 30 second timeout
            headers={"Content-Type": "application/json"},
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
            st.markdown(f"Claude is thinking{'.' * (i + 1)}")
            time.sleep(0.5)


# Export main function
__all__ = ["render_chat_interface", "simulate_typing"]
