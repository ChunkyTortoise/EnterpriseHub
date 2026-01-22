"""
Whisper Mode Dashboard - Section 3 of 2026 Strategic Roadmap
Real-time coaching interface for Jorge during live calls.
"""

import streamlit as st
from ghl_real_estate_ai.streamlit_demo.async_utils import run_async
import asyncio
import pandas as pd
from datetime import datetime
from ghl_real_estate_ai.services.whisper_coach import get_whisper_coach
from ghl_real_estate_ai.services.ghost_followup_engine import get_ghost_followup_engine

def render_whisper_dashboard(lead_id: str, lead_name: str, property_address: str):
    st.markdown(f"### 🎙️ Whisper Mode: Live Call with {lead_name}")
    
    coach = get_whisper_coach()
    ghost = get_ghost_followup_engine()
    
    # Obsidian Style War Room Layout
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.markdown("#### 👤 Lead Profile")
        with st.container(border=True):
            st.write(f"**Name:** {lead_name}")
            st.write(f"**Address:** {property_address}")
            st.metric("FRS Score", "72", delta="HOT")
            st.caption("Relocation mentioned in previous chat.")

    with col2:
        st.markdown("#### 💡 Live Coaching")
        cue_placeholder = st.empty()
        
    with col3:
        st.markdown("#### 📑 Value Injection")
        cma_placeholder = st.empty()

    st.markdown("---")
    st.markdown("#### 💬 Live Transcript Stream")
    transcript_container = st.container(height=300)
    
    # Simulation logic
    if "whisper_history" not in st.session_state:
        st.session_state.whisper_history = []
        
    sim_chunks = [
        "Hi Jorge, I'm still thinking about the proposal you sent.",
        "Zillow says my house is worth way more, it seems too expensive.",
        "I think I want to wait until next year to see if rates drop.",
        "Actually, that makes sense. Tell me more about your guarantee."
    ]
    
    if st.button("🚀 Start Live Call Simulation"):
        for chunk in sim_chunks:
            # 1. Add to transcript
            st.session_state.whisper_history.append({"role": "lead", "text": chunk, "time": datetime.now().strftime("%H:%M:%S")})
            
            # 2. Analyze with Coach
            import asyncio
            loop = asyncio.new_event_loop()
            cue = run_async(coach.analyze_transcript_chunk(chunk, {}))
            
            # 3. Update UI
            with transcript_container:
                for msg in st.session_state.whisper_history:
                    st.write(f"**[{msg['time']}] Lead:** {msg['text']}")
            
            with cue_placeholder:
                color = "#ef4444" if cue.sentiment == "RESISTANT" else "#10b981"
                st.markdown(f"""
                <div style="background: {color}22; border-left: 5px solid {color}; padding: 15px; border-radius: 8px;">
                    <strong style="color: {color};">SENTIMENT: {cue.sentiment}</strong><br>
                    <p style="font-size: 1.1rem; margin-top: 10px;">"{cue.suggested_phrase}"</p>
                </div>
                """, unsafe_allow_html=True)
                
            if cue.inject_cma:
                with cma_placeholder:
                    st.warning("⚠️ PRICE PUSHBACK DETECTED")
                    if st.button("📥 INJECT CMA NOW", key=f"inject_{datetime.now().timestamp()}"):
                        st.success("CMA Data URL sent to lead via Whisper Bridge.")
            
            import time
            time.sleep(2)
            st.rerun()
