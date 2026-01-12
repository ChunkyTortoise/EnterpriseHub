
import streamlit as st
import random
import time
import plotly.graph_objects as go

def render_voice_intelligence():
    """
    Elite Live Call Intelligence Interface.
    Visualizes real-time VAPI/Voice interactions with AI analysis.
    """
    st.subheader("🎙️ Live Call Intelligence")
    st.markdown("*Real-time AI assistance for live calls and automated voice reception.*")
    
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
        st.markdown("""
        <div style="padding: 10px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center; font-size: 0.8rem; font-weight: 600; color: #64748b;">
            Agent: <span style="color: #8B5CF6;">Elite Closer v4</span>
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
        with transcript_container:
            st.markdown("""
            <div style="font-size: 0.9rem; color: #64748b; margin-bottom: 10px;">[02:14] <b>AI:</b> Hello Sarah, I'm calling from Jorge Sales' team regarding your interest in the Downtown condo. How are you today?</div>
            <div style="font-size: 0.9rem; color: #1e293b; margin-bottom: 10px;">[02:18] <b>Sarah:</b> Oh hi! I'm good. I was just looking at the price, it seems a bit high for that square footage?</div>
            <div style="font-size: 0.9rem; color: #64748b; margin-bottom: 10px;">[02:22] <b>AI:</b> I understand. While the price per foot is slightly higher than the average, this unit actually includes private roof access and two premium parking spots, which adds about $150k in equity value.</div>
            <div style="font-size: 0.9rem; color: #1e293b; margin-bottom: 10px; background: rgba(59, 130, 246, 0.05); padding: 5px; border-radius: 4px;">[02:28] <b>Sarah:</b> <span style="color: #2563eb; font-weight: 600;">(Thinking)</span> I didn't realize it had roof access. That does change things. Is the HOA also high?</div>
            <div style="font-size: 0.9rem; color: #10b981; font-weight: 700;">[NOW] <b>AI:</b> Analyzing HOA impact...</div>
            """, unsafe_allow_html=True)

    with col_side:
        # Sentiment Analysis
        st.markdown("#### 🧠 Real-time Sentiment")
        sentiment_score = 72
        st.markdown(f"""
        <div style="background: white; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center;">
            <div style="font-size: 0.8rem; color: #64748b; text-transform: uppercase; font-weight: 700;">Lead Sentiment</div>
            <div style="font-size: 2rem; font-weight: 800; color: #10b981;">{sentiment_score}%</div>
            <div style="font-size: 0.75rem; color: #10b981; font-weight: 600;">Trending Up (Positive)</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # AI Battlecards
        st.markdown("#### ⚔️ AI Battlecards")
        st.markdown("""
        <div style="background: #fdf2f2; padding: 12px; border-radius: 8px; border-left: 4px solid #ef4444; margin-bottom: 10px;">
            <div style="font-size: 0.75rem; color: #991b1b; font-weight: 700;">OBJECTION DETECTED</div>
            <div style="font-size: 0.85rem; color: #1e293b; font-weight: 600;">"Price is too high"</div>
            <div style="font-size: 0.8rem; color: #4b5563; margin-top: 4px;">Action: Pivot to ROOFTOP ACCESS and APPRECIATION. Mention 8.4% annual growth.</div>
        </div>
        <div style="background: #f0fdf4; padding: 12px; border-radius: 8px; border-left: 4px solid #10b981;">
            <div style="font-size: 0.75rem; color: #166534; font-weight: 700;">CLOSING OPPORTUNITY</div>
            <div style="font-size: 0.85rem; color: #1e293b; font-weight: 600;">Interest confirmed</div>
            <div style="font-size: 0.8rem; color: #4b5563; margin-top: 4px;">Action: Offer a VIP showing this Saturday at 10 AM.</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔴 Take Over Call", use_container_width=True, type="primary"):
            st.toast("Human handoff initiated. Connecting Jorge...")

    st.markdown("---")
    
    # Call Summary
    st.markdown("#### 📊 Call Performance Metrics")
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.metric("Talk Ratio (AI/Lead)", "42% / 58%")
    with m_col2:
        st.metric("Objections Handled", "2/2", "+100%")
    with m_col3:
        st.metric("Probability of Close", "64%", "+15%")
