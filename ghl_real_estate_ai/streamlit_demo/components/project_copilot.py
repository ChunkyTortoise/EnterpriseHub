"""
Project Copilot - Claude-Driven Project Navigator
Greets the user and provides guided walkthroughs of the platform.
"""

import asyncio

import streamlit as st

from ghl_real_estate_ai.services.claude_platform_companion import get_claude_platform_companion
from ghl_real_estate_ai.streamlit_demo.async_utils import run_async


def render_welcome_walkthrough():
    """Renders a prominent welcome and walkthrough in the main area on first load."""
    if "tour_greeted" not in st.session_state:
        st.session_state.tour_greeted = False

    if not st.session_state.tour_greeted:
        try:
            companion = get_claude_platform_companion()
            companion_available = True
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"Welcome tour initialization error: {e}")
            companion = None
            companion_available = False

        with st.container():
            # Premium Welcome Card
            st.markdown(
                f"""
            <div style='background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); 
                        padding: 2.5rem; border-radius: 20px; border: 1px solid rgba(99, 102, 241, 0.3);
                        margin-bottom: 2rem; box-shadow: 0 20px 50px rgba(0,0,0,0.5);'>
                <div style='display: flex; align-items: center; margin-bottom: 1.5rem;'>
                    <div style='font-size: 3.5rem; margin-right: 1.5rem; filter: drop-shadow(0 0 15px rgba(99, 102, 241, 0.6));'>🧠</div>
                    <div>
                        <h1 style='margin: 0; color: white; font-size: 2.2rem; font-family: "Space Grotesk", sans-serif;'>Welcome, Jorge.</h1>
                        <p style='margin: 0; color: #94a3b8; font-size: 1.1rem;'>Elite Real Estate AI Ecosystem v4.0 is Online.</p>
                    </div>
                </div>
            """,
                unsafe_allow_html=True,
            )

            # Get the real greeting
            greeting_text = "Elite Systems are operational. Your 5-Hub command center is ready to maximize your conversion velocity."

            if companion_available:
                with st.spinner("🤖 Claude is synthesizing your executive briefing..."):
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        greeting = run_async(companion.generate_project_greeting("Jorge"))
                        greeting_text = greeting
                    except Exception as e:
                        import logging

                        logging.getLogger(__name__).error(f"Tour greeting generation error: {e}")
                        pass

            st.session_state.claude_greeting_text = greeting_text

            st.markdown(
                f"""
                <div style='color: #e2e8f0; font-size: 1.25rem; line-height: 1.6; font-style: italic; margin-bottom: 2rem; border-left: 4px solid #6366F1; padding-left: 1.5rem;'>
                    "{st.session_state.claude_greeting_text}"
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("🚀 Start Tour", type="primary", use_container_width=True):
                    st.session_state.show_full_walkthrough = True
                    st.session_state.tour_greeted = True
                    st.rerun()
            with col2:
                if st.button("Enter Dashboard", use_container_width=True):
                    st.session_state.tour_greeted = True
                    st.rerun()

    elif st.session_state.get("show_full_walkthrough", False):
        st.markdown(
            """
        <div style='background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.95) 100%); 
                    padding: 2.5rem; border-radius: 20px; border: 1px solid #6366F1; margin-bottom: 2rem;
                    box-shadow: 0 15px 35px rgba(0,0,0,0.3);'>
            <h2 style='color: white; font-family: "Space Grotesk", sans-serif; margin-bottom: 1.5rem;'>🗺️ Elite Platform Walkthrough</h2>
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;'>
                <div style='padding: 1.5rem; background: rgba(99, 102, 241, 0.08); border-radius: 12px; border: 1px solid rgba(99, 102, 241, 0.2);'>
                    <h4 style='color: #6366F1; margin-top: 0;'>1. 🏢 Executive Hub</h4>
                    <p style='color: #cbd5e1; font-size: 0.95rem;'>The cockpit of your business. Monitor your $2.4M pipeline, multi-market ROI, and system health telemetry in one view.</p>
                </div>
                <div style='padding: 1.5rem; background: rgba(99, 102, 241, 0.08); border-radius: 12px; border: 1px solid rgba(99, 102, 241, 0.2);'>
                    <h4 style='color: #6366F1; margin-top: 0;'>2. 🧠 Lead Intelligence</h4>
                    <p style='color: #cbd5e1; font-size: 0.95rem;'>Where AI meets psychology. Decode Lead DNA with 25+ behavioral factors and deploy Swarm analysis for precision matching.</p>
                </div>
                <div style='padding: 1.5rem; background: rgba(99, 102, 241, 0.08); border-radius: 12px; border: 1px solid rgba(99, 102, 241, 0.2);'>
                    <h4 style='color: #6366F1; margin-top: 0;'>3. 🤖 Automation Studio</h4>
                    <p style='color: #cbd5e1; font-size: 0.95rem;'>The engine room. Configure your RAG knowledge base, tune AI personas, and design complex autonomous workflows.</p>
                </div>
                <div style='padding: 1.5rem; background: rgba(99, 102, 241, 0.08); border-radius: 12px; border: 1px solid rgba(99, 102, 241, 0.2);'>
                    <h4 style='color: #6366F1; margin-top: 0;'>4. 💰 Sales Copilot</h4>
                    <p style='color: #cbd5e1; font-size: 0.95rem;'>Your AI wingman. Real-time objection handling, live call coaching, and automated document generation for closing deals.</p>
                </div>
                <div style='padding: 1.5rem; background: rgba(99, 102, 241, 0.08); border-radius: 12px; border: 1px solid rgba(99, 102, 241, 0.2);'>
                    <h4 style='color: #6366F1; margin-top: 0;'>5. 📈 Ops & Optimization</h4>
                    <p style='color: #cbd5e1; font-size: 0.95rem;'>System governance. Audit AI decisions, run RLHF retraining loops, and ensure 99.9% operational excellence across all tenants.</p>
                </div>
                <div style='display: flex; align-items: center; justify-content: center; background: rgba(16, 185, 129, 0.05); border-radius: 12px; border: 1px dashed rgba(16, 185, 129, 0.3);'>
                    <p style='color: #10b981; font-weight: 600; text-align: center;'>Ready to Scale?<br><span style='font-size: 0.8rem; font-weight: 400;'>Neural Swarm is Active.</span></p>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        if st.button("Complete Tour & Enter Command Center", type="primary", use_container_width=True):
            st.session_state.show_full_walkthrough = False
            st.rerun()


def render_project_copilot():
    """Renders the Claude Copilot in the sidebar for ongoing guidance."""
    try:
        companion = get_claude_platform_companion()
        companion_available = True
    except Exception as e:
        import logging

        logging.getLogger(__name__).error(f"Project Copilot rendering error: {e}")
        companion = None
        companion_available = False

    # Ensure session state is initialized
    if "tour_greeted" not in st.session_state:
        st.session_state.tour_greeted = False

    # Sidebar Guide
    st.markdown("---")
    st.markdown("### 🤖 Claude Project Guide")

    with st.container(border=True):
        st.write(st.session_state.get("claude_greeting_text", "Elite Systems are operational."))

        # Contextual Guidance based on current Hub
        current_hub = st.session_state.get("current_hub", "Executive Hub")
        if st.button(f"📖 Guide me through {current_hub}"):
            if companion_available:
                with st.spinner("Synthesizing guidance..."):
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        guidance = run_async(companion.get_hub_guidance(current_hub))
                        st.info(guidance)
                    except Exception as e:
                        import logging

                        logging.getLogger(__name__).debug(f"Copilot advice generation error: {e}")
                        st.info(
                            f"The {current_hub} is optimized for Phase 6 operations. Focus on your high-intent leads."
                        )
            else:
                st.warning("Claude Companion unavailable. Please check system logs.")

        # Manual Tour Trigger
        if st.button("🚀 Retake Tour"):
            st.session_state.show_full_walkthrough = True
            st.rerun()
