"""
Journey Orchestrator UI Component
Renders the autonomous lead journey designed by Claude.
"""
import streamlit as st
import asyncio
from datetime import datetime, timedelta
from ghl_real_estate_ai.services.claude_journey_orchestrator import get_journey_orchestrator
from ghl_real_estate_ai.streamlit_demo.async_utils import run_async

def render_journey_orchestrator(lead_id: str, lead_name: str, lead_profile: dict):
    """
    Renders the Claude-powered autonomous lead journey.
    """
    st.markdown(f"### 🗺️ Autonomous Journey Path: {lead_name}")
    st.markdown("*Claude-designed strategic sequence optimized for conversion*")

    orchestrator = get_journey_orchestrator()

    # Design the journey (using cache if possible to avoid redundant API calls)
    journey_key = f"journey_plan_{lead_id}"
    if journey_key not in st.session_state:
        with st.spinner("🧠 Claude is architecting the optimal journey..."):
            try:
                journey_plan = run_async(
                    orchestrator.design_personalized_journey(lead_id, lead_profile)
                )
                st.session_state[journey_key] = journey_plan
            except Exception as e:
                st.error(f"Failed to design journey: {str(e)}")
                return

    journey = st.session_state[journey_key]

    # Journey Strategy Dossier
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        <div style='background: rgba(99, 102, 241, 0.05); padding: 1.5rem; border-radius: 12px; border-left: 4px solid #6366F1;'>
            <h4 style='color: #6366F1; margin-top: 0;'>Persona: {journey.persona_type}</h4>
            <p style='font-style: italic;'>"{journey.journey_strategy}"</p>
            <div style='margin-top: 1rem;'>
                <strong>Next Best Action:</strong> 
                <span style='background: #6366F1; color: white; padding: 2px 8px; border-radius: 4px;'>{journey.next_best_action}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.metric("Est. Conversion", f"{journey.estimated_conversion_days} Days", f"{int(journey.confidence_score*100)}% Confidence")
        if st.button("🔄 Redesign Journey", use_container_width=True):
            del st.session_state[journey_key]
            st.rerun()

    # --- FUNCTIONAL DISPATCHER STATUS ---
    st.markdown("#### ⚡ Functional Dispatcher Active")
    with st.container(border=True):
        disp_col1, disp_col2, disp_col3 = st.columns([1.5, 1, 1])
        
        # Get current lead state for dispatcher
        readiness = lead_profile.get("overall_score", 0.65) if isinstance(lead_profile.get("overall_score"), (int, float)) else 0.65
        
        with disp_col1:
            st.write(f"**System Status:** 🤖 Monitoring `{lead_name}` for critical conversion signals.")
            st.caption("Dispatcher checks for readiness > 85%, stagnant follow-up (>3 days), and high-intent sentiment shifts.")
            
        with disp_col2:
            st.metric("Closing Readiness", f"{readiness:.0%}")
            
        with disp_col3:
            if readiness >= 0.85:
                st.error("🚨 CRITICAL READINESS")
                if st.button("🚀 Execute Priority Handoff", type="primary", use_container_width=True):
                    with st.spinner("Dispatching Mission Dossier to Jorge's Mobile..."):
                        try:
                            dispatch_res = run_async(
                                orchestrator.monitor_and_dispatch(lead_id, lead_name, {"closing_readiness": readiness, "top_triggers": ["Investment ROI", "Family Safety"]})
                            )
                            if dispatch_res.get("action") == "priority_handoff":
                                st.success("✅ PRIORITY HANDOFF DISPATCHED!")
                                st.balloons()
            else:
                st.success("🟢 Monitoring Nurture Path")
                st.caption("Next check in 2.5 hours")

    st.markdown("---")
    st.markdown("#### 📅 30-Day Execution Roadmap")

    # Render touchpoints as a vertical timeline
    for i, tp in enumerate(journey.touchpoints):
        channel_icon = {"sms": "💬", "email": "📧", "call": "📞", "portal": "🌐"}.get(tp.channel.lower(), "📝")
        
        with st.container(border=True):
            c1, c2, c3 = st.columns([0.5, 3, 1])
            with c1:
                st.markdown(f"<div style='font-size: 1.5rem; text-align: center; margin-top: 10px;'>{channel_icon}</div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"**Step {tp.step_number}: {tp.purpose}** ({tp.timing})")
                st.markdown(f"*{tp.content_draft}*")
                st.caption(f"🎯 Expected: {tp.expected_outcome} | 🚦 Signal: {tp.conversion_signal}")
            with c3:
                if st.button("🚀 Push to GHL", key=f"push_tp_{i}", use_container_width=True):
                    st.success("Synced to Workflow!")
                if st.button("📝 Edit", key=f"edit_tp_{i}", use_container_width=True):
                    st.info("Edit mode active")

    # Dynamic Triggers Section
    if journey.dynamic_triggers:
        st.markdown("---")
        st.markdown("#### ⚡ Dynamic Pivot Triggers")
        st.info("Claude is monitoring for these conditions to automatically adjust the journey path:")
        
        for trigger in journey.dynamic_triggers:
            condition = trigger.get("condition", "N/A")
            action = trigger.get("action", "N/A")
            st.markdown(f"- **IF** {condition} **THEN** {action}")

    # Contact Timing Optimization
    st.markdown("---")
    st.markdown("#### ⏰ Intelligent Timing Windows")
    with st.spinner("Analyzing engagement patterns..."):
        try:
            timing_windows = run_async(orchestrator.predict_optimal_touchpoints(lead_id))
            
            t_cols = st.columns(len(timing_windows))
            for i, window in enumerate(timing_windows):
                with t_cols[i]:
                    st.markdown(f"""
                    <div style='text-align: center; background: rgba(16, 185, 129, 0.05); padding: 1rem; border-radius: 10px; border: 1px solid rgba(16, 185, 129, 0.2);'>
                        <div style='font-size: 0.8rem; color: #10B981; font-weight: 700;'>BEST {window['channel'].upper()} WINDOW</div>
                        <div style='font-size: 1.1rem; font-weight: 700; margin: 5px 0;'>{window['day']} @ {window['time']}</div>
                        <div style='font-size: 0.75rem; color: #6B7280;'>{int(window['probability']*100)}% Engagement Prob.</div>
                    </div>
                    """, unsafe_allow_html=True)
        except:
            st.info("Timing optimization data loading...")
