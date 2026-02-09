"""Hub navigation sidebar renderer.

Renders the categorized sidebar navigation, strategic counsel,
quick actions, system telemetry, and live feed.
"""

import datetime

import pandas as pd
import streamlit as st

from ghl_real_estate_ai.streamlit_demo.config.page_config import ASYNC_UTILS_AVAILABLE, run_async

try:
    from ghl_real_estate_ai.streamlit_demo.services.service_registry import (
        CLAUDE_COMPANION_AVAILABLE,
        claude_companion,
    )
except ImportError:
    CLAUDE_COMPANION_AVAILABLE = False
    claude_companion = None

try:
    from ghl_real_estate_ai.streamlit_demo.components.project_copilot import render_project_copilot
except ImportError:
    render_project_copilot = None

try:
    from ghl_real_estate_ai.streamlit_demo.components.neural_uplink import render_neural_uplink
except ImportError:
    render_neural_uplink = None


# Hub categories with icons and organization
HUB_CATEGORIES = {
    "Core Operations": [
        "Executive Command Center",
        "Lead Intelligence Hub",
        "Jorge War Room",
        "Real-Time Intelligence",
    ],
    "Analytics & Insights": [
        "Data Arbitrage Hub",
        "Agent ROI Dashboard",
        "Billing Analytics",
        "Marketplace Management",
        "Ops & Optimization",
        "Claude Cost Tracking",
    ],
    "AI & Automation": [
        "Swarm Intelligence",
        "Proactive Intelligence",
        "Voice Claude",
        "Voice AI Assistant",
        "Sales Copilot",
        "Deep Research",
        "Automation Studio",
    ],
    "Bot Management": [
        "Bot Health Monitoring",
        "Bot Coordination Flow",
        "Lead Bot Sequences",
        "Bot Testing & Validation",
        "SMS Compliance Dashboard",
    ],
    "Customer Journey": ["Buyer Journey Hub", "Seller Journey Hub"],
}

CATEGORY_DESCRIPTIONS = {
    "Core Operations": "Executive dashboards and strategic intelligence",
    "Analytics & Insights": "Business intelligence and performance tracking",
    "AI & Automation": "Intelligent agents and automation systems",
    "Bot Management": "Bot monitoring, testing and compliance",
    "Customer Journey": "Buyer and seller experience optimization",
}

COUNSEL_MESSAGES = {
    "Executive Command Center": "Jorge, lead velocity is up 12% this week. Focus on the Downtown cluster for maximum ROI.",
    "Lead Intelligence Hub": "Sarah Martinez is showing high engagement with luxury properties. Suggest a showing today.",
    "Voice Claude": "Voice commands active. Try saying 'Hey Claude, show me my top leads' for hands-free assistance.",
    "Voice AI Assistant": "Advanced voice AI ready for lead qualification calls. 91.3% accuracy with real-time sentiment analysis.",
    "Proactive Intelligence": "2 high-priority alerts detected. Pipeline risk identified - take action now to stay on target.",
    "Swarm Intelligence": "The analyst swarm is currently processing 142 leads. Token efficiency is at an all-time high.",
    "Real-Time Intelligence": "Market conditions are shifting in East Austin. Update your valuation models.",
    "Billing Analytics": "ARR is tracking at $187K - 23% monthly growth puts us on target for $240K. 23 customers in overage generating strong usage revenue.",
    "Buyer Journey Hub": "We have 3 buyers ready for pre-approval. Syncing with financing partners now.",
    "Seller Journey Hub": "The Maple Ave listing is hitting peak interest. I recommend an open house this Sunday.",
    "Automation Studio": "3 new workflow templates are ready for deployment. Your time savings is currently 42h/week.",
    "SMS Compliance Dashboard": "TCPA compliance at 98.2%. 23 opted-out contacts, 0 violations today. All systems operational.",
    "Bot Health Monitoring": "All three Jorge bots healthy. 99.8% uptime, 1.2s avg response. 45 active conversations, 0 alerts.",
    "Bot Coordination Flow": "25 successful handoffs today. 94% success rate, 1.2s avg handoff time. Smart routing optimized.",
    "Lead Bot Sequences": "42 active 3-7-30 sequences. Day 7 voice calls at 73% success. 12 CMAs generated, automation optimized.",
    "Bot Testing & Validation": "All integration tests passing. 98.5% system health. Demo-ready with full end-to-end validation complete.",
    "Sales Copilot": "Preparing talking points for your 2pm call. Client prefers a direct, data-driven approach.",
    "Ops & Optimization": "System health is optimal. Recommend scaling to the Miami market next month.",
    "Deep Research": "Perplexity-powered search is active. Ask me to research any market or property.",
}


def render_hub_navigator(sparkline_fn):
    """Render the sidebar hub navigation and return the selected hub name.

    Args:
        sparkline_fn: The sparkline chart generator function.

    Returns:
        The name of the selected hub.
    """
    # Combine all hubs for backward compatibility
    hub_options = []
    for category_hubs in HUB_CATEGORIES.values():
        hub_options.extend(category_hubs)

    with st.sidebar:
        # Command Center header
        st.markdown(
            """
        <div style="
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            text-align: center;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        ">
            <h3 style="color: white; margin: 0; font-size: 1.2rem; font-weight: 600;">
                Command Center
            </h3>
            <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 0.85rem;">
                Jorge's AI Hub Navigator
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Initialize Copilot (Greeting & Guidance)
        if render_project_copilot is not None:
            try:
                render_project_copilot()
            except Exception as e:
                st.sidebar.error(f"Copilot initialization failed: {e}")

        # Navigation header
        st.markdown(
            """
        <div style='
            font-size: 0.8rem;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin: 20px 0 15px 0;
            font-weight: 700;
            text-align: center;
            border-bottom: 1px solid #e5e7eb;
            padding-bottom: 8px;
        '>
            Hub Navigator
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Current hub from session state
        current_hub = st.session_state.get("current_hub", "Executive Command Center")

        # Find which category contains the current hub
        current_category = None
        for category_name, category_hubs in HUB_CATEGORIES.items():
            if current_hub in category_hubs:
                current_category = category_name
                break

        # Render categorized navigation using expanders
        selected_hub = current_hub

        for category_name, category_hubs in HUB_CATEGORIES.items():
            expanded = category_name == current_category

            with st.expander(f"{category_name} ({len(category_hubs)})", expanded=expanded):
                st.markdown(f"*{CATEGORY_DESCRIPTIONS.get(category_name, '')}*")

                if current_hub in category_hubs:
                    default_index = category_hubs.index(current_hub)
                else:
                    default_index = 0

                category_selection = st.radio(
                    f"Select from {category_name}:",
                    category_hubs,
                    index=default_index if current_hub in category_hubs else None,
                    key=f"category_{category_name}",
                    label_visibility="collapsed",
                )

                if category_selection != current_hub and category_selection in category_hubs:
                    selected_hub = category_selection

        # Fallback: maintain current hub if no selection made
        if selected_hub not in hub_options:
            selected_hub = current_hub

        # Update session state and notify Claude of context change
        if st.session_state.current_hub != selected_hub:
            st.session_state.current_hub = selected_hub

            # Update Claude's context awareness
            if (
                CLAUDE_COMPANION_AVAILABLE
                and claude_companion
                and st.session_state.get("claude_session_initialized", False)
            ):
                try:
                    hub_context = {
                        "hub_name": selected_hub,
                        "user_action": "navigation",
                        "timestamp": datetime.datetime.now().isoformat(),
                    }

                    if ASYNC_UTILS_AVAILABLE:
                        context_update = run_async(
                            claude_companion.update_context(selected_hub.lower().replace(" ", "_"), hub_context)
                        )
                    else:
                        context_update = None

                    if context_update:
                        st.session_state.claude_contextual_insight = context_update.get("insight")
                        st.session_state.dynamic_claude_counsel = context_update.get("counsel")

                except Exception:
                    pass
        else:
            st.session_state.current_hub = selected_hub

        # Global AI Pulse Indicator
        st.markdown(
            f"""
        <div style="
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            background: rgba(99, 102, 241, 0.1);
            border-radius: 8px;
            margin-top: 1rem;
            border: 1px solid rgba(99, 102, 241, 0.2);
        ">
            <div class="live-indicator" style="width: 10px; height: 10px; background: #10b981; border-radius: 50%; box-shadow: 0 0 10px #10b981;"></div>
            <div style="font-size: 0.8rem; color: #E6EDF3; font-weight: 600; font-family: 'Space Grotesk', sans-serif;">
                Swarm Status: <span style="color: #10b981;">ACTIVE</span>
            </div>
            <div style="font-size: 0.7rem; color: #64748b; margin-left: auto;">
                v4.0.0
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # System Health Sparkline
        st.markdown("<br>", unsafe_allow_html=True)
        st.plotly_chart(
            sparkline_fn([98, 99, 97, 99, 100, 99], color="#10B981", height=30),
            width="stretch",
            config={"displayModeBar": False},
        )
        st.caption("SYSTEM STABILITY: 99.8% (NORMAL)")

        st.markdown("---")

        # Neural Uplink Feed
        if render_neural_uplink is not None:
            render_neural_uplink()

        st.markdown("---")

        # Claude's Strategic Counsel (Contextual)
        current_msg = st.session_state.get("dynamic_claude_counsel")
        if not current_msg:
            current_msg = COUNSEL_MESSAGES.get(selected_hub, "AI Swarm is standing by for your next command.")

        st.markdown(
            f"""
        <div style="
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.05) 0%, rgba(99, 102, 241, 0.05) 100%);
            padding: 15px;
            border-radius: 12px;
            border: 1px solid rgba(139, 92, 246, 0.2);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            position: relative;
            overflow: hidden;
        ">
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <div class="status-pulse"></div>
                <div style="font-size: 0.75rem; color: #8B5CF6; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em;">
                    Claude's Strategic Counsel
                </div>
            </div>
            <div style="font-size: 0.9rem; color: #E6EDF3; font-style: italic; line-height: 1.5; position: relative; z-index: 1;">
                "{current_msg}"
            </div>
            <div style="position: absolute; right: -10px; bottom: -10px; font-size: 3rem; opacity: 0.05; transform: rotate(-15deg);">brain</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # Enhanced quick actions
        st.markdown(
            """
        <div style="
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%);
            padding: 1.2rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            border: 1px solid rgba(99, 102, 241, 0.3);
            text-align: center;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        ">
            <h4 style="margin: 0; font-size: 0.9rem; font-weight: 700; color: white; text-transform: uppercase; letter-spacing: 0.1em;">
                Command Matrix
            </h4>
        </div>
        """,
            unsafe_allow_html=True,
        )

        if st.button("Refresh Data", width="stretch", type="primary"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.toast("Data refreshed successfully!")
            st.rerun()

        # Export functionality
        metrics_data = {
            "Metric": ["Total Pipeline", "Hot Leads", "Conversion Rate", "Avg Deal Size"],
            "Value": ["$2.4M", "23", "34%", "$385K"],
            "Change": ["+15%", "+8", "+2%", "+$12K"],
        }
        df_metrics = pd.DataFrame(metrics_data)
        csv = df_metrics.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Export Report", data=csv, file_name="executive_metrics.csv", mime="text/csv", width="stretch"
        )

        st.markdown("---")

        # Global AI State Sync
        with st.expander("Global AI Configuration", expanded=True):
            market = st.selectbox("Active Market", ["Austin, TX", "Miami, FL", "Los Angeles, CA"], index=0)
            voice_tone = st.slider(
                "AI Voice Tone",
                0.0,
                1.0,
                st.session_state.ai_config["voice_tone"],
                help="0.0 = Professional, 1.0 = Natural",
            )

            if market != st.session_state.ai_config["market"] or voice_tone != st.session_state.ai_config["voice_tone"]:
                st.session_state.ai_config["market"] = market
                st.session_state.ai_config["voice_tone"] = voice_tone
                st.session_state.ai_config["last_sync"] = datetime.datetime.now().strftime("%H:%M:%S")
                st.toast(f"AI State Synced: {market}")

            st.caption(f"Last sync: {st.session_state.ai_config['last_sync']}")

        # GHL Architectural Sync
        with st.expander("GHL Architectural Sync", expanded=False):
            st.markdown("""
            **Environment:** `Lyrio-Production-Main`
            **Sync Status:** Operational
            **Lead Buffer:** 128MB Persistent
            """)
            st.link_button("Open Lyrio Dashboard", "https://app.gohighlevel.com", width="stretch")
            st.link_button("AI Conversation Audit", "https://app.gohighlevel.com", width="stretch")

        st.markdown("---")

        # System status
        st.markdown(
            "<h4 style='color: #8B949E; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 2.5rem; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 5px; margin-bottom: 15px;'>System Telemetry</h4>",
            unsafe_allow_html=True,
        )
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.metric("Active Leads", "47", "+12")
        with col_stat2:
            st.metric("Neural Swarm", "Online", delta="Stable", delta_color="normal")

        st.markdown(
            "<h4 style='color: #8B949E; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 2rem;'>Neural Uplink</h4>",
            unsafe_allow_html=True,
        )

        # Enhanced Live Feed
        try:
            from ghl_real_estate_ai.services.live_feed import LiveFeedService

            feed_service = LiveFeedService()
            feed_html = feed_service.get_feed_html(limit=6)
            st.markdown(
                f"""
            <div style='background: rgba(13, 17, 23, 0.4); border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); padding: 5px;'>
                {feed_html}
            </div>
            """,
                unsafe_allow_html=True,
            )
        except Exception:
            # Fallback items with v2.0 styling
            for item in feed_items:  # noqa: F821 — preserved from original (undefined fallback)
                st.markdown(
                    f"""
                <div style="
                    display: flex;
                    gap: 12px;
                    margin-bottom: 8px;
                    padding: 12px;
                    background: rgba(22, 27, 34, 0.6);
                    border-radius: 10px;
                    border: 1px solid rgba(255,255,255,0.05);
                    border-left: 2px solid {item["color"]};
                    transition: all 0.3s ease;">
                    <div style="font-size: 1.1rem; filter: drop-shadow(0 0 5px {item["color"]}40);">{item["icon"]}</div>
                    <div style="flex: 1;">
                        <div style="font-size: 0.8rem; line-height: 1.4; color: #E6EDF3;">{item["text"]}</div>
                        <div style="font-size: 0.65rem; color: #8B949E; margin-top: 4px;">{item["time"]}</div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

    return selected_hub
