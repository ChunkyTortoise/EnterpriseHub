
import streamlit as st
import random
import time
import asyncio
import json
import plotly.graph_objects as go

# Import enhanced services
try:
    from services.claude_orchestrator import get_claude_orchestrator
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
    selected_lead = st.session_state.get('selected_lead_name', 'Prospect')
    lead_options = st.session_state.get('lead_options', {})
    lead_context = lead_options.get(selected_lead, {})
    lead_id = lead_context.get('lead_id', 'demo_lead')

    # Connection Status
    col_status1, col_status2, col_status3 = st.columns([1, 1, 1])
    with col_status1:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; padding: 10px; background: rgba(16, 185, 129, 0.1); border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.2);">
            <div class="live-indicator" style="width: 10px; height: 10px; background: #10b981; border-radius: 50%; box-shadow: 0 0 10px #10b981;"></div>
            <div style="font-size: 0.8rem; color: #065f46; font-weight: 700;">VAPI STREAM: ACTIVE</div>
        </div>
        """, unsafe_allow_html=True)
    with col_status2:
        st.markdown("""
        <div style="padding: 10px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center; font-size: 0.8rem; font-weight: 600; color: #64748b;">
            Latency: <span style="color: #3b82f6;">142ms</span>
        </div>
        """, unsafe_allow_html=True)
    with col_status3:
        st.markdown(f"""
        <div style="padding: 10px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center; font-size: 0.8rem; font-weight: 600; color: #64748b;">
            Lead: <span style="color: #8B5CF6;">{selected_lead}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    col_main, col_side = st.columns([2, 1])

    with col_main:
        # Voice Waveform
        st.markdown("#### 🌊 Audio Spectrum")
        st.markdown("""
        <div class="waveform-container" style="background: #0f172a; border-radius: 12px; height: 100px;">
            <div class="waveform-bar" style="animation-delay: 0.1s; background: #3b82f6;"></div>
            <div class="waveform-bar" style="animation-delay: 0.3s; background: #60a5fa;"></div>
            <div class="waveform-bar" style="animation-delay: 0.2s; background: #93c5fd;"></div>
            <div class="waveform-bar" style="animation-delay: 0.5s; background: #3b82f6;"></div>
            <div class="waveform-bar" style="animation-delay: 0.4s; background: #60a5fa;"></div>
            <div class="waveform-bar" style="animation-delay: 0.1s; background: #93c5fd;"></div>
            <div class="waveform-bar" style="animation-delay: 0.3s; background: #3b82f6;"></div>
            <div class="waveform-bar" style="animation-delay: 0.2s; background: #60a5fa;"></div>
            <div class="waveform-bar" style="animation-delay: 0.5s; background: #93c5fd;"></div>
            <div class="waveform-bar" style="animation-delay: 0.4s; background: #3b82f6;"></div>
            <div class="waveform-bar" style="animation-delay: 0.1s; background: #60a5fa;"></div>
            <div class="waveform-bar" style="animation-delay: 0.3s; background: #93c5fd;"></div>
            <div class="waveform-bar" style="animation-delay: 0.2s; background: #3b82f6;"></div>
            <div class="waveform-bar" style="animation-delay: 0.5s; background: #60a5fa;"></div>
            <div class="waveform-bar" style="animation-delay: 0.4s; background: #93c5fd;"></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Live Transcript
        st.markdown("#### 📜 Live Transcript")
        transcript_container = st.container(height=300, border=True)
        
        current_transcript = [
            {"role": "AI", "time": "02:14", "text": f"Hello {selected_lead.split()[0]}, I'm calling from Jorge Sales' team regarding your interest in the Downtown properties. How are you today?"},
            {"role": "Lead", "time": "02:18", "text": "Oh hi! I'm good. I was just looking at the pricing, it seems a bit higher than I expected for the area?"},
            {"role": "AI", "time": "02:22", "text": "I understand. While the initial price point reflects the current demand, these units specifically feature superior appreciation rates due to the upcoming tech corridor expansion."},
            {"role": "Lead", "time": "02:28", "text": "I didn't realize there was an expansion planned there. That does change the math. What about the financing options?"}
        ]

        with transcript_container:
            for entry in current_transcript:
                role_color = "#64748b" if entry["role"] == "AI" else "#1e293b"
                st.markdown(f'<div style="font-size: 0.9rem; color: {role_color}; margin-bottom: 10px;">[{entry["time"]}] <b>{entry["role"]}:</b> {entry["text"]}</div>', unsafe_allow_html=True)
            
            st.markdown(f'<div style="font-size: 0.9rem; color: #10b981; font-weight: 700;">[NOW] <b>AI:</b> Claude is analyzing financing response...</div>', unsafe_allow_html=True)

    with col_side:
        # Real-time Intelligence via Claude
        st.markdown("#### 🧠 Live AI Coaching")
        
        if CLAUDE_AVAILABLE:
            with st.spinner("Claude is listening..."):
                try:
                    orchestrator = get_claude_orchestrator()
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    # Synthesize transcript for Claude
                    transcript_text = "\n".join([f"{e['role']}: {e['text']}" for e in current_transcript])
                    
                    # Get coaching result
                    coaching_result = loop.run_until_complete(
                        orchestrator.chat_query(
                            query="Provide 2 real-time battlecards and current lead sentiment based on this call transcript.",
                            context={"transcript": transcript_text, "lead_name": selected_lead, "task": "live_call_coaching"},
                            lead_id=lead_id
                        )
                    )
                    
                    st.markdown(f"""
                    <div style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem;">
                        <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase; font-weight: 800; margin-bottom: 10px;">Claude's Live Feed:</div>
                        <div style="font-size: 0.9rem; line-height: 1.5;">{coaching_result.content}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Coaching Error: {e}")
        else:
            # Fallback
            st.markdown("""
            <div style="background: #fdf2f2; padding: 12px; border-radius: 8px; border-left: 4px solid #ef4444; margin-bottom: 10px;">
                <div style="font-size: 0.75rem; color: #991b1b; font-weight: 700;">OBJECTION DETECTED</div>
                <div style="font-size: 0.85rem; color: #1e293b; font-weight: 600;">"Pricing is too high"</div>
                <div style="font-size: 0.8rem; color: #4b5563; margin-top: 4px;">Action: Pivot to TECH CORRIDOR EXPANSION. Mention 12% projected growth.</div>
            </div>
            """, unsafe_allow_html=True)
        
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

