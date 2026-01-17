"""
Voice Claude Interface - Voice-Activated Claude Assistant UI
Provides hands-free interaction with Claude through voice commands.
"""

import streamlit as st
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Import voice-enabled Claude companion
try:
    from ghl_real_estate_ai.services.claude_platform_companion import get_claude_platform_companion
    VOICE_CLAUDE_AVAILABLE = True
except ImportError:
    VOICE_CLAUDE_AVAILABLE = False

def render_voice_claude_interface():
    """
    Voice-Activated Claude Interface.

    Features:
    - "Hey Claude" wake word activation
    - Natural language voice commands
    - Real-time speech recognition
    - Contextual voice responses
    - Voice command history
    """

    st.subheader("🎤 Voice-Activated Claude")
    st.markdown("*Say \"Hey Claude\" followed by your command for hands-free assistance.*")

    if not VOICE_CLAUDE_AVAILABLE:
        st.error("Voice Claude system not available. Please check configuration.")
        return

    # Initialize voice Claude
    companion = get_claude_platform_companion()

    # Voice system status
    voice_status = companion.get_voice_status()

    # Status indicators
    col_status1, col_status2, col_status3 = st.columns([1, 1, 1])

    with col_status1:
        status_color = "#10b981" if voice_status["voice_enabled"] else "#ef4444"
        status_text = "ACTIVE" if voice_status["voice_enabled"] else "OFFLINE"
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px; padding: 10px; background: rgba(16, 185, 129, 0.1); border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.2);">
            <div class="voice-indicator" style="width: 10px; height: 10px; background: {status_color}; border-radius: 50%; box-shadow: 0 0 10px {status_color};"></div>
            <div style="font-size: 0.8rem; color: #065f46; font-weight: 700;">VOICE CLAUDE: {status_text}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_status2:
        wake_status = "LISTENING" if voice_status["wake_word_active"] else "INACTIVE"
        st.markdown(f"""
        <div style="padding: 10px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center; font-size: 0.8rem; font-weight: 600; color: #64748b;">
            Wake Word: <span style="color: #3b82f6;">{wake_status}</span>
        </div>
        """, unsafe_allow_html=True)

    with col_status3:
        commands_count = voice_status["commands_processed"]
        st.markdown(f"""
        <div style="padding: 10px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center; font-size: 0.8rem; font-weight: 600; color: #64748b;">
            Commands: <span style="color: #8B5CF6;">{commands_count}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Main voice interface
    col_main, col_controls = st.columns([2, 1])

    with col_main:
        # Voice activation area
        st.markdown("#### 🎙️ Voice Command Center")

        # Voice waveform visualization
        if voice_status["wake_word_active"]:
            st.markdown("""
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin: 10px 0;">
                <div style="color: white; font-size: 1.2rem; font-weight: 700; margin-bottom: 15px;">🎤 Say "Hey Claude"</div>
                <div class="voice-wave-container" style="display: flex; justify-content: center; align-items: center; gap: 3px; height: 40px;">
                    <div class="voice-wave" style="width: 4px; height: 10px; background: rgba(255,255,255,0.7); border-radius: 2px; animation: wave 1s ease-in-out infinite; animation-delay: 0s;"></div>
                    <div class="voice-wave" style="width: 4px; height: 25px; background: rgba(255,255,255,0.8); border-radius: 2px; animation: wave 1s ease-in-out infinite; animation-delay: 0.1s;"></div>
                    <div class="voice-wave" style="width: 4px; height: 15px; background: rgba(255,255,255,0.7); border-radius: 2px; animation: wave 1s ease-in-out infinite; animation-delay: 0.2s;"></div>
                    <div class="voice-wave" style="width: 4px; height: 30px; background: rgba(255,255,255,0.9); border-radius: 2px; animation: wave 1s ease-in-out infinite; animation-delay: 0.3s;"></div>
                    <div class="voice-wave" style="width: 4px; height: 20px; background: rgba(255,255,255,0.8); border-radius: 2px; animation: wave 1s ease-in-out infinite; animation-delay: 0.4s;"></div>
                    <div class="voice-wave" style="width: 4px; height: 15px; background: rgba(255,255,255,0.7); border-radius: 2px; animation: wave 1s ease-in-out infinite; animation-delay: 0.5s;"></div>
                    <div class="voice-wave" style="width: 4px; height: 25px; background: rgba(255,255,255,0.8); border-radius: 2px; animation: wave 1s ease-in-out infinite; animation-delay: 0.6s;"></div>
                </div>
                <div style="color: rgba(255,255,255,0.8); font-size: 0.9rem; margin-top: 10px;">Listening for wake word...</div>
            </div>

            <style>
            @keyframes wave {
                0%, 100% { transform: scaleY(0.5); }
                50% { transform: scaleY(1.5); }
            }
            </style>
            """, unsafe_allow_html=True)

        # Voice command examples
        st.markdown("##### 💬 Try These Voice Commands:")

        example_commands = [
            "Hey Claude, show me my top leads",
            "Hey Claude, what's my performance today?",
            "Hey Claude, go to the properties section",
            "Hey Claude, schedule a meeting",
            "Hey Claude, tell me about the market trends"
        ]

        for cmd in example_commands:
            st.markdown(f"• **{cmd}**")

        # Voice command history
        st.markdown("##### 📜 Recent Voice Commands")
        command_history_container = st.container(height=200, border=True)

        with command_history_container:
            if voice_status["last_command"]:
                # Show recent commands (this would be populated from the actual history)
                sample_history = [
                    {"time": "2 minutes ago", "command": "Hey Claude, show me my leads", "response": "Displaying your 5 active leads with priority ranking"},
                    {"time": "5 minutes ago", "command": "Hey Claude, what's my performance?", "response": "Your conversion rate is up 15% this week"},
                    {"time": "8 minutes ago", "command": "Hey Claude, go to dashboard", "response": "Navigating to dashboard with today's insights"}
                ]

                for entry in sample_history:
                    st.markdown(f"""
                    <div style="margin-bottom: 15px; padding: 10px; background: #f8fafc; border-radius: 8px; border-left: 4px solid #3b82f6;">
                        <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 5px;">{entry["time"]}</div>
                        <div style="font-size: 0.9rem; color: #1e293b; font-weight: 600;">🎤 {entry["command"]}</div>
                        <div style="font-size: 0.85rem; color: #475569; margin-top: 5px;">🤖 {entry["response"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("*No voice commands yet. Try saying \"Hey Claude\" followed by a command.*")

    with col_controls:
        # Voice controls
        st.markdown("#### ⚙️ Voice Controls")

        # Voice activation toggle
        if st.button("🎤 Activate Voice", use_container_width=True, type="primary"):
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            success = loop.run_until_complete(companion.initialize_voice_commands())
            if success:
                st.success("Voice system activated!")
                st.rerun()
            else:
                st.error("Failed to activate voice system")

        # Voice style selection
        st.markdown("**Response Style:**")
        current_style = voice_status["response_style"]
        style_options = ["professional", "friendly", "enthusiastic"]

        selected_style = st.selectbox(
            "Choose voice style:",
            options=style_options,
            index=style_options.index(current_style),
            label_visibility="collapsed"
        )

        if selected_style != current_style:
            if companion.set_voice_response_style(selected_style):
                st.success(f"Style changed to {selected_style}")
                time.sleep(1)
                st.rerun()

        # Quick test commands
        st.markdown("**Quick Test:**")
        if st.button("Test \"Hey Claude\"", use_container_width=True):
            st.info("Say: \"Hey Claude, what's my status?\"")

        # Voice metrics
        st.markdown("**Voice Metrics:**")
        st.metric("Commands Today", commands_count, delta="+3")
        st.metric("Response Time", "1.2s", delta="-0.3s")
        st.metric("Accuracy", "94%", delta="+2%")

    st.markdown("---")

    # Real-time voice processing demo
    st.markdown("#### 🔊 Live Voice Processing Demo")

    demo_col1, demo_col2 = st.columns(2)

    with demo_col1:
        st.markdown("**Simulated Voice Input:**")
        test_command = st.text_input("Type a command to test voice processing:",
                                   placeholder="show me my leads")

        if st.button("Process Command"):
            if test_command.strip():
                with st.spinner("Processing voice command..."):
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                    # Simulate processing the command
                    response = loop.run_until_complete(
                        companion.process_voice_command(test_command)
                    )

                    st.success("Command processed!")
                    st.info(f"Claude's response: {response.response_text}")

                    if response.action_taken:
                        st.info(f"Action taken: {response.action_taken}")

    with demo_col2:
        st.markdown("**Command Analysis:**")
        if test_command.strip():
            # Analyze command intent
            command_lower = test_command.lower()

            if any(word in command_lower for word in ["show", "display", "go to"]):
                intent = "🧭 Navigation"
                confidence = "High (85%)"
            elif any(word in command_lower for word in ["what", "how", "tell me"]):
                intent = "❓ Query"
                confidence = "High (90%)"
            elif any(word in command_lower for word in ["call", "email", "schedule"]):
                intent = "⚡ Action"
                confidence = "Medium (75%)"
            else:
                intent = "💬 General"
                confidence = "Medium (70%)"

            st.markdown(f"**Intent:** {intent}")
            st.markdown(f"**Confidence:** {confidence}")
            st.markdown(f"**Processing:** Ready")

    # Claude voice features showcase
    with st.expander("🚀 Voice Claude Capabilities"):
        st.markdown("""
        ### What Voice Claude Can Do:

        **📍 Navigation Commands:**
        - "Go to leads section"
        - "Show me the dashboard"
        - "Open properties view"

        **📊 Status Queries:**
        - "What's my performance today?"
        - "Show me my top leads"
        - "Tell me about market trends"

        **⚡ Quick Actions:**
        - "Schedule a meeting"
        - "Call my hottest lead"
        - "Create a follow-up task"

        **💬 General Conversation:**
        - "How should I approach this lead?"
        - "What's the best time to contact clients?"
        - "Give me market insights"

        **🎯 Context Awareness:**
        - Claude knows what page you're on
        - Remembers your recent activities
        - Provides relevant suggestions
        """)

    st.markdown("---")
    # --- VOICE HUD: LIVE CALL COACHING OVERLAY ---
    st.markdown("### 🎦 Live Call Coaching HUD (HUD Concept)")
    
    if "live_call_active" not in st.session_state:
        st.session_state.live_call_active = False
        st.session_state.hud_dna = {
            "Security": 0.5, "Status": 0.4, "Investment": 0.6, 
            "Family": 0.5, "Convenience": 0.7, "Privacy": 0.4
        }
        st.session_state.hud_messages = []
        st.session_state.last_mention = None

    col_hud1, col_hud2 = st.columns([1, 2])
    
    with col_hud1:
        if not st.session_state.live_call_active:
            if st.button("📞 Start Live Call Simulation", type="primary", use_container_width=True):
                st.session_state.live_call_active = True
                st.rerun()
        else:
            if st.button("🛑 End Call", type="secondary", use_container_width=True):
                st.session_state.live_call_active = False
                st.rerun()
            
            st.success("🟢 Call in Progress...")
            st.write("**Lead:** Sarah Chen")
            st.write("**Duration:** 02:45")
    
    if st.session_state.live_call_active:
        with st.container(border=True):
            st.markdown("#### 🛡️ Live HUD Coaching Overlay")
            
            hud_col1, hud_col2, hud_col3 = st.columns([1.5, 2, 1.5])
            
            with hud_col1:
                st.markdown("**🧬 Real-time DNA Radar**")
                # Radar Chart for HUD
                categories = list(st.session_state.hud_dna.keys())
                values = list(st.session_state.hud_dna.values())
                
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    line_color='#00ff41' if st.session_state.last_mention == "safety" else '#6366F1'
                ))
                
                # Pulse effect if safety mentioned
                pulse_color = "rgba(0, 255, 65, 0.3)" if st.session_state.last_mention == "safety" else "rgba(99, 102, 241, 0.1)"
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 1], showticklabels=False, gridcolor="rgba(255,255,255,0.1)"),
                        angularaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                        bgcolor="rgba(0,0,0,0)"
                    ),
                    showlegend=False,
                    margin=dict(l=30, r=30, t=30, b=30),
                    height=250,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
                if st.session_state.last_mention == "safety":
                    st.markdown("""
                        <div style="text-align:center; color:#00ff41; font-weight:bold; animation: blink 1s infinite;">
                            ⚠️ SECURITY DIMENSION PULSING
                        </div>
                        <style>@keyframes blink { 0% {opacity:1;} 50% {opacity:0.3;} 100% {opacity:1;} }</style>
                    """, unsafe_allow_html=True)

            with hud_col2:
                st.markdown("**🎙️ Live Transcript (Detected Mentions)**")
                sim_speech = st.text_input("Simulate Lead Speech (e.g. 'Is the neighborhood safe?')", key="sim_speech")
                
                if sim_speech:
                    if "safe" in sim_speech.lower() or "safety" in sim_speech.lower() or "security" in sim_speech.lower():
                        st.session_state.hud_dna["Security"] = 0.95
                        st.session_state.last_mention = "safety"
                        st.toast("🎯 Keyword Detected: SAFETY", icon="🛡️")
                    elif "price" in sim_speech.lower() or "invest" in sim_speech.lower():
                        st.session_state.hud_dna["Investment"] = 0.9
                        st.session_state.last_mention = "investment"
                    
                    st.session_state.hud_messages.insert(0, f"Lead: \"{sim_speech}\"")
                
                for msg in st.session_state.hud_messages[:3]:
                    st.caption(msg)
                
            with hud_col3:
                st.markdown("**💡 Strategic Counsel**")
                if st.session_state.last_mention == "safety":
                    st.markdown("""
                        <div style="background:rgba(0, 255, 65, 0.1); padding:10px; border-radius:8px; border:1px solid #00ff41;">
                            <b style="color:#00ff41;">INSTANT TALKING POINT:</b><br>
                            "Sarah, Teravista actually just ranked in the Top 5% for safety in Austin. 
                            The local school district has a dedicated security patrol 24/7."
                        </div>
                        <div style="margin-top:10px; font-size:0.8rem; color:#8B949E;">
                            📊 School Safety Metric: 9.8/10
                        </div>
                    """, unsafe_allow_html=True)
                elif st.session_state.last_mention == "investment":
                    st.markdown("""
                        <div style="background:rgba(99, 102, 241, 0.1); padding:10px; border-radius:8px; border:1px solid #6366F1;">
                            <b style="color:#6366F1;">INSTANT TALKING POINT:</b><br>
                            "This zip code has seen a 12% year-over-year appreciation. 
                            It's one of the most resilient investment pockets in the market."
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.write("Listening for triggers...")
                    st.info("Try mentioning 'safety' or 'investment' in the simulation box.")

def render_voice_settings():
    """Render voice system configuration settings."""

    st.subheader("🎛️ Voice System Settings")

    if not VOICE_CLAUDE_AVAILABLE:
        st.error("Voice Claude system not available.")
        return

    companion = get_claude_platform_companion()

    # Wake word settings
    st.markdown("##### 🔊 Wake Word Configuration")
    col1, col2 = st.columns(2)

    with col1:
        wake_sensitivity = st.slider("Wake Word Sensitivity", 0.1, 1.0, 0.8, 0.1)
        st.markdown("*Higher sensitivity = responds to quieter \"Hey Claude\"*")

    with col2:
        response_delay = st.slider("Response Delay (seconds)", 0.5, 3.0, 1.0, 0.1)
        st.markdown("*Time to wait after wake word before listening*")

    # Voice quality settings
    st.markdown("##### 🎤 Voice Quality Settings")
    col3, col4 = st.columns(2)

    with col3:
        audio_quality = st.selectbox("Audio Quality", ["Standard", "High", "Ultra"])
        noise_reduction = st.checkbox("Noise Reduction", value=True)

    with col4:
        voice_timeout = st.number_input("Command Timeout (seconds)", 5, 30, 10)
        auto_response = st.checkbox("Auto-response Mode", value=False)

    # Advanced settings
    st.markdown("##### ⚙️ Advanced Settings")
    with st.expander("Advanced Voice Configuration"):
        st.checkbox("Enable Voice Analytics", value=True)
        st.checkbox("Store Voice History", value=True)
        st.checkbox("Background Listening", value=False)
        st.selectbox("Language Model", ["English (US)", "English (UK)", "Spanish"])

        if st.button("Reset Voice Settings"):
            st.success("Voice settings reset to defaults")

# Add CSS for voice interface animations
def add_voice_interface_css():
    """Add CSS styling for voice interface."""
    st.markdown("""
    <style>
    .voice-indicator {
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    .voice-wave {
        animation: wave 1s ease-in-out infinite;
    }

    @keyframes wave {
        0%, 100% {
            transform: scaleY(0.5);
            opacity: 0.5;
        }
        50% {
            transform: scaleY(1.5);
            opacity: 1;
        }
    }
    </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    # For testing the component
    render_voice_claude_interface()