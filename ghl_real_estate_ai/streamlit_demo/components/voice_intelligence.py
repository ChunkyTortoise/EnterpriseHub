import asyncio
import json
import random
import time

import plotly.graph_objects as go
import streamlit as st

from ghl_real_estate_ai.streamlit_demo.async_utils import run_async

# Import enhanced services
try:
    from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator

    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False


def render_voice_intelligence():
    """
    Elite Live Call Intelligence Interface.
    Visualizes real-time VAPI/Voice interactions with AI analysis.
    """
    st.subheader("🎙️ Live Call Intelligence")
    st.markdown("*Real-time AI assistance for live calls and automated voice reception.*")

    # Get current lead context for the call
    selected_lead = st.session_state.get("selected_lead_name", "Prospect")
    lead_options = st.session_state.get("lead_options", {})
    lead_context = lead_options.get(selected_lead, {})
    lead_id = lead_context.get("lead_id", "demo_lead")

    # Connection Status - Obsidian Edition
    col_status1, col_status2, col_status3 = st.columns([1, 1, 1])
    with col_status1:
        st.markdown(
            """
        <div style="display: flex; align-items: center; gap: 12px; padding: 12px; background: rgba(16, 185, 129, 0.1); border-radius: 10px; border: 1px solid rgba(16, 185, 129, 0.2); box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
            <div class="status-pulse" style="width: 10px; height: 10px; background: #10b981; border-radius: 50%;"></div>
            <div style="font-size: 0.75rem; color: #10b981; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">STREAM: ACTIVE</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col_status2:
        st.markdown(
            """
        <div style="padding: 12px; background: rgba(22, 27, 34, 0.6); border-radius: 10px; border: 1px solid rgba(255,255,255,0.05); text-align: center; font-size: 0.75rem; font-weight: 700; color: #8B949E; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">
            LATENCY: <span style="color: #6366F1;">142ms</span>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col_status3:
        st.markdown(
            f"""
        <div style="padding: 12px; background: rgba(22, 27, 34, 0.6); border-radius: 10px; border: 1px solid rgba(255,255,255,0.05); text-align: center; font-size: 0.75rem; font-weight: 700; color: #8B949E; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">
            NODE: <span style="color: #6366F1;">{selected_lead.upper()}</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    col_main, col_side = st.columns([2, 1])

    with col_main:
        # Voice Waveform - Obsidian Edition
        st.markdown("#### 🌊 AUDIO SPECTRUM")
        st.markdown(
            """
        <div class="waveform-container" style="background: rgba(5, 7, 10, 0.8); border-radius: 16px; height: 120px; border: 1px solid rgba(255,255,255,0.05); box-shadow: inset 0 0 20px rgba(0,0,0,0.5);">
            <div class="waveform-bar" style="animation-delay: 0.1s; background: #6366F1;"></div>
            <div class="waveform-bar" style="animation-delay: 0.3s; background: #8b5cf6;"></div>
            <div class="waveform-bar" style="animation-delay: 0.2s; background: #6366F1;"></div>
            <div class="waveform-bar" style="animation-delay: 0.5s; background: #8b5cf6;"></div>
            <div class="waveform-bar" style="animation-delay: 0.4s; background: #6366F1;"></div>
            <div class="waveform-bar" style="animation-delay: 0.1s; background: #8b5cf6;"></div>
            <div class="waveform-bar" style="animation-delay: 0.3s; background: #6366F1;"></div>
            <div class="waveform-bar" style="animation-delay: 0.2s; background: #8b5cf6;"></div>
            <div class="waveform-bar" style="animation-delay: 0.5s; background: #6366F1;"></div>
            <div class="waveform-bar" style="animation-delay: 0.4s; background: #8b5cf6;"></div>
            <div class="waveform-bar" style="animation-delay: 0.1s; background: #6366F1;"></div>
            <div class="waveform-bar" style="animation-delay: 0.3s; background: #8b5cf6;"></div>
            <div class="waveform-bar" style="animation-delay: 0.2s; background: #6366F1;"></div>
            <div class="waveform-bar" style="animation-delay: 0.5s; background: #8b5cf6;"></div>
            <div class="waveform-bar" style="animation-delay: 0.4s; background: #6366F1;"></div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Live Transcript
        st.markdown("#### 📜 LIVE COMMAND TRANSCRIPT")
        transcript_container = st.container(height=300, border=True)

        current_transcript = [
            {
                "role": "AI",
                "time": "02:14",
                "text": f"Hello {selected_lead.split()[0]}, I'm calling from Jorge Sales' team regarding your interest in the Downtown properties. How are you today?",
            },
            {
                "role": "Lead",
                "time": "02:18",
                "text": "Oh hi! I'm good. I was just looking at the pricing, it seems a bit higher than I expected for the area?",
            },
            {
                "role": "AI",
                "time": "02:22",
                "text": "I understand. While the initial price point reflects the current demand, these units specifically feature superior appreciation rates due to the upcoming tech corridor expansion.",
            },
            {
                "role": "Lead",
                "time": "02:28",
                "text": "I didn't realize there was an expansion planned there. That does change the math. What about the financing options?",
            },
        ]

        with transcript_container:
            for entry in current_transcript:
                role_color = "#8B949E" if entry["role"] == "AI" else "#E6EDF3"
                st.markdown(
                    f'<div style="font-size: 0.95rem; color: {role_color}; margin-bottom: 12px; font-family: \'Inter\', sans-serif;">[{entry["time"]}] <b style="color: #6366F1;">{entry["role"]}:</b> {entry["text"]}</div>',
                    unsafe_allow_html=True,
                )

            st.markdown(
                f"<div style=\"font-size: 0.95rem; color: #10b981; font-weight: 700; font-family: 'Space Grotesk', sans-serif;\">[NOW] <b>AI:</b> CLAUDE SYNTHESIZING RESPONSE...</div>",
                unsafe_allow_html=True,
            )

    with col_side:
        # Real-time Intelligence via Claude
        st.markdown("#### 🧠 LIVE AI COACHING")

        if CLAUDE_AVAILABLE:
            with st.spinner("Analyzing audio stream..."):
                try:
                    orchestrator = get_claude_orchestrator()

                    # Synthesize transcript for Claude
                    transcript_text = "\n".join([f"{e['role']}: {e['text']}" for e in current_transcript])

                    # Get coaching result
                    coaching_result = run_async(
                        orchestrator.chat_query(
                            query="Provide 2 real-time battlecards and current lead sentiment based on this call transcript.",
                            context={
                                "transcript": transcript_text,
                                "lead_name": selected_lead,
                                "task": "live_call_coaching",
                            },
                            lead_id=lead_id,
                        )
                    )

                    st.markdown(
                        f"""
                    <div style="background: rgba(22, 27, 34, 0.7); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 8px 32px rgba(0,0,0,0.4); backdrop-filter: blur(12px);">
                        <div style="font-size: 0.75rem; color: #6366F1; text-transform: uppercase; font-weight: 800; margin-bottom: 12px; font-family: 'Space Grotesk', sans-serif; letter-spacing: 0.1em;">Claude's Live Intelligence:</div>
                        <div style="font-size: 0.95rem; line-height: 1.6; color: #E6EDF3; font-family: 'Inter', sans-serif;">{coaching_result.content}</div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                except Exception as e:
                    st.error(f"Coaching Error: {e}")
        else:
            # Fallback - Obsidian Command Style
            st.markdown(
                """
            <div style="background: rgba(239, 68, 68, 0.1); padding: 1.25rem; border-radius: 12px; border-left: 4px solid #ef4444; margin-bottom: 1rem; border: 1px solid rgba(239, 68, 68, 0.2); border-left: 4px solid #ef4444;">
                <div style="font-size: 0.75rem; color: #ef4444; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">OBJECTION DETECTED</div>
                <div style="font-size: 1rem; color: #FFFFFF; font-weight: 700; margin-top: 4px; font-family: 'Space Grotesk', sans-serif;">"Pricing is too high"</div>
                <div style="font-size: 0.9rem; color: #8B949E; margin-top: 8px; line-height: 1.5; font-family: 'Inter', sans-serif;">Directive: Pivot to TECH CORRIDOR expansion. Highlight 12% projected appreciation.</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        if st.button("🔴 Take Over Call", use_container_width=True, type="primary"):
            st.toast("Human handoff initiated. Connecting Jorge...", icon="📞")

    st.markdown("---")

    # Call Summary
    st.markdown("#### 📊 Call Performance Metrics")
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.metric("Talk Ratio (AI/Lead)", "38% / 62%")
    with m_col2:
        st.metric("Signals Detected", "4 High-Intent", "+2")
    with m_col3:
        st.metric("Probability of Close", "71%", "+7%")
