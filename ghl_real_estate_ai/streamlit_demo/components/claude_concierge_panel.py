from datetime import datetime

import streamlit as st

try:
    from ghl_real_estate_ai.services.claude_concierge_orchestrator import (
        ConciergeMode,
        ConciergeResponse,
        get_claude_concierge_orchestrator,
    )

    CONCIERGE_AVAILABLE = True
except ImportError:
    CONCIERGE_AVAILABLE = False


def render_claude_concierge_panel(hub_name: str):
    """
    Renders the persistent Claude Concierge panel in the sidebar.
    """
    st.sidebar.markdown("---")

    # Concierge Header with Elite Styling
    st.sidebar.markdown(
        f"""
        <div style='background: linear-gradient(135deg, #6D28D9 0%, #4C1D95 100%);
                    padding: 1.25rem; border-radius: 12px; color: white; margin-bottom: 1rem;
                    box-shadow: 0 4px 15px rgba(109, 40, 217, 0.3); position: relative; overflow: hidden;'>
            <div style='position: absolute; top: -10px; right: -10px; font-size: 3rem; opacity: 0.2;'>🧠</div>
            <h3 style='color: white !important; margin: 0; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;'>
                <span>Claude Concierge</span>
                <span style='background: #10B981; width: 8px; height: 8px; border-radius: 50%; display: inline-block; animation: pulse 2s infinite;'></span>
            </h3>
            <p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 0.8rem; line-height: 1.4;'>
                Omnipresent Platform Intelligence
            </p>
        </div>
        <style>
            @keyframes pulse {{
                0% {{ transform: scale(1); opacity: 1; }}
                50% {{ transform: scale(1.2); opacity: 0.7; }}
                100% {{ transform: scale(1); opacity: 1; }}
            }}
        </style>
    """,
        unsafe_allow_html=True,
    )

    if not CONCIERGE_AVAILABLE:
        st.sidebar.warning("Concierge Service Offline")
        return

    # Initialize orchestrator
    orchestrator = get_claude_concierge_orchestrator()

    # Get guidance (cached or live)
    with st.sidebar.expander("💡 Current Intelligence", expanded=True):
        if st.button("🔄 Refresh Insights", key="refresh_concierge", use_container_width=True):
            st.session_state.last_concierge_refresh = datetime.now()
            # Clear cache if needed (handled by TTL usually)

        # Generate guidance based on current hub
        try:
            # Wrap async call for Streamlit
            from ghl_real_estate_ai.streamlit_demo.async_utils import run_async

            response = run_async(
                orchestrator.generate_live_guidance(
                    current_page=hub_name,
                    mode=ConciergeMode.PROACTIVE,
                    session_id=st.session_state.get("session_id", "demo_session"),
                )
            )

            if response:
                st.markdown(f"**Insight:** {response.primary_guidance}")

                # Check for state-based coordination needs
                if hub_name == "🎯 Lead Command":
                    latest_analysis = st.session_state.get("latest_analysis", {})
                    if latest_analysis.get("overall_score", 0) > 85:
                        st.markdown("---")
                        st.warning("🤝 **Bot Relay Recommended**")
                        st.markdown("Lead is highly qualified. Recommend transferring to **Seller Negotiation** agent.")
                        if st.button("⚔️ Switch to Seller Command", use_container_width=True):
                            st.session_state.prev_hub = hub_name
                            st.session_state.hub_selection = "⚔️ Seller Command"  # This needs to match radio label
                            st.rerun()

                if response.immediate_actions:
                    st.markdown("---")
                    st.markdown("**Recommended Actions:**")
                    for idx, action in enumerate(response.immediate_actions):
                        if st.button(f"🎯 {action.get('description', 'Action')}", key=f"action_{idx}"):
                            st.toast(f"Executing: {action.get('description')}")
                            # Execute coordination logic here if needed

                # Bot Coordination Insights
                if hasattr(response, "bot_coordination_suggestions") and response.bot_coordination_suggestions:
                    st.markdown("---")
                    st.markdown("**Bot Relay Opportunities:**")
                    for suggestion in response.bot_coordination_suggestions:
                        st.info(f"🤖 {suggestion.get('suggestion')}")

        except Exception as e:
            st.error(f"Concierge Error: {e}")
            # Fallback mock guidance
            st.info(
                "Jorge, Sarah Chen is showing high intent (FRS: 88). Recommend initiating Price Negotiation sequence in Seller Command."
            )

    # Reactive Chat Interface
    with st.sidebar.expander("💬 Ask Claude", expanded=False):
        user_query = st.text_input(
            "Query platform state...", placeholder="Ex: Is Sarah ready to sell?", key="concierge_chat_input"
        )
        if user_query:
            st.markdown(f"*Analyzing platform state for: '{user_query}'*")
            try:
                from ghl_real_estate_ai.streamlit_demo.async_utils import run_async

                response = run_async(
                    orchestrator.generate_live_guidance(
                        current_page=st.session_state.get("current_page", "Dashboard"),
                        mode=ConciergeMode.REACTIVE,
                    )
                )
                st.markdown(response.primary_guidance)
            except Exception as e:
                st.warning(f"Could not get guidance: {e}")
                st.markdown("Platform intelligence temporarily unavailable.")


def render_concierge_coordination_card(hub_name: str):
    """
    Renders a coordination card at the top of hub dashboards.
    """
    st.markdown(
        f"""
        <div style='background: rgba(109, 40, 217, 0.1); border-left: 4px solid #6D28D9; padding: 1rem; border-radius: 4px; margin-bottom: 1.5rem;'>
            <h4 style='margin: 0; color: #6D28D9; font-size: 0.9rem;'>🧞 CLAUDE'S STRATEGIC RECOMMENDATION</h4>
            <p style='margin: 0.5rem 0 0 0; font-size: 0.85rem; color: #E5E7EB;'>
                Based on current <b>{hub_name}</b> state, I recommend accelerating the qualification for hot leads in the pipeline.
            </p>
        </div>
    """,
        unsafe_allow_html=True,
    )
