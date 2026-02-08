import asyncio
import json
import random
import traceback
from datetime import datetime

import pandas as pd
import streamlit as st

# Import enhanced services
try:
    from ghl_real_estate_ai.core.service_registry import ServiceRegistry
    from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator

    CLAUDE_ORCHESTRATOR_AVAILABLE = True
except ImportError:
    CLAUDE_ORCHESTRATOR_AVAILABLE = False


@st.cache_data(ttl=60)  # Cache for 1 minute
def get_dashboard_status():
    """Get dashboard status for caching"""
    return {"status": "online", "last_update": datetime.now().isoformat(), "components_loaded": True}


def render_realtime_intelligence_dashboard():
    """Render the Real-Time Intelligence Dashboard with all components - Obsidian Edition"""
    from ghl_real_estate_ai.streamlit_demo.obsidian_theme import render_dossier_block, style_obsidian_chart

    # Dashboard header with status indicator - Obsidian Style
    st.markdown(
        """
        <div style="background: rgba(22, 27, 34, 0.85); backdrop-filter: blur(20px); padding: 1.5rem 2.5rem; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 2.5rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);">
            <div>
                <h1 style="font-family: 'Space Grotesk', sans-serif; font-size: 2.5rem; font-weight: 700; margin: 0; color: #FFFFFF; letter-spacing: -0.04em; text-transform: uppercase;">⚡ REAL-TIME INTELLIGENCE</h1>
                <p style="font-family: 'Inter', sans-serif; font-size: 1rem; margin: 0.5rem 0 0 0; color: #8B949E; font-weight: 500; letter-spacing: 0.02em;">Live monitoring, cognitive telemetry, and autonomous intervention</p>
            </div>
            <div style="text-align: right;">
                <div style="background: rgba(16, 185, 129, 0.1); color: #10b981; padding: 10px 20px; border-radius: 12px; font-size: 0.85rem; font-weight: 800; border: 1px solid rgba(16, 185, 129, 0.3); letter-spacing: 0.1em; display: flex; align-items: center; gap: 10px;">
                    <div class="status-pulse" style="width: 10px; height: 10px; background: #10b981; border-radius: 50%;"></div>
                    STREAM ACTIVE
                </div>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # NEW: Market Pulse Scrolling Ticker
    st.markdown(
        """
        <div style="background: rgba(13, 17, 23, 0.9); padding: 10px 0; overflow: hidden; white-space: nowrap; border-bottom: 1px solid rgba(255,255,255,0.05); margin-bottom: 2rem;">
            <div style="display: inline-block; animation: marquee 30s linear infinite; color: #6366F1; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; font-weight: 700; letter-spacing: 0.05em;">
                <span style="color: #10b981;">[LIVE]</span> Sarah Martinez just qualified for 78704 Luxury cluster ... <span style="color: #f59e0b;">[WEBHOOK]</span> Inbound SMS from Node #9921 processed in 12ms ... <span style="color: #6366F1;">[SWARM]</span> Analyst Agent #4 identifying price-drop opportunities in West Lake ... <span style="color: #10b981;">[DEAL]</span> Emma Wilson win probability increased to 92% ... <span style="color: #ef4444;">[ALERT]</span> High-velocity lead David Kim requires manual handoff ... <span style="color: #6366F1;">[SYSTEM]</span> All 12 Austin Edge nodes operational ... 
            </div>
        </div>
        <style>
            @keyframes marquee {
                0% { transform: translateX(100%); }
                100% { transform: translateX(-100%); }
            }
        </style>
    """,
        unsafe_allow_html=True,
    )

    # Import and initialize services with error handling
    try:
        # Import components
        from components.alert_center import render_alert_center
        from components.interactive_analytics import render_interactive_analytics
        from components.live_lead_scoreboard import render_live_lead_scoreboard
        from components.mobile_responsive_layout import get_layout_manager
        from components.payload_monitor import render_payload_monitor
        from components.performance_dashboard import render_performance_dashboard

        from ghl_real_estate_ai.services.dashboard_state_manager import (
            dashboard_sidebar_controls,
            get_dashboard_state_manager,
        )
        from ghl_real_estate_ai.services.realtime_data_service import get_realtime_service
        from ghl_real_estate_ai.streamlit_demo.components.matrix_view import render_matrix_view

        # Initialize services
        realtime_service = get_realtime_service()
        state_manager = get_dashboard_state_manager()
        layout_manager = get_layout_manager()

        # Dashboard sidebar controls
        with st.sidebar:
            st.markdown("---")
            st.markdown("### ⚡ Real-Time Controls")
            dashboard_sidebar_controls()

        # Main dashboard tabs
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab_whisper = st.tabs(
            [
                "🎯 Live Overview",
                "📊 Lead Scoreboard",
                "🚨 Alert Center",
                "📈 Interactive Analytics",
                "🧬 Matrix View",
                "⚡ Performance",
                "📦 Payload Monitor",
                "🎙️ Whisper Mode",
            ]
        )

        with tab1:
            # Claude's Live Sentinel - Enhanced with real analysis
            with st.container(border=True):
                c_icon, c_text = st.columns([1, 8])
                with c_icon:
                    st.markdown("<div style='font-size: 3rem; text-align: center;'>🛰️</div>", unsafe_allow_html=True)
                with c_text:
                    st.markdown("### Claude's Live Sentinel")

                    if CLAUDE_ORCHESTRATOR_AVAILABLE:
                        orchestrator = get_claude_orchestrator()

                        # Get recent events for analysis
                        recent_events = realtime_service.get_recent_events(limit=10)
                        metrics = realtime_service.get_metrics()

                        if recent_events:
                            with st.spinner("Claude is synthesizing real-time intelligence..."):
                                try:
                                    # Run async analysis in Streamlit
                                    try:
                                        loop = asyncio.get_event_loop()
                                    except RuntimeError:
                                        loop = asyncio.new_event_loop()
                                        asyncio.set_event_loop(loop)

                                    # Format event data for Claude
                                    event_summary = []
                                    for e in recent_events:
                                        event_summary.append(
                                            {
                                                "time": e.timestamp.strftime("%H:%M:%S"),
                                                "type": e.event_type,
                                                "priority": e.priority,
                                                "data": e.data,
                                            }
                                        )

                                    # Build context
                                    analysis_context = {
                                        "metrics": metrics,
                                        "events": event_summary,
                                        "market": st.session_state.get("selected_market", "Austin"),
                                    }

                                    # Use report synthesis task for live summary
                                    analysis_result = loop.run_until_complete(
                                        orchestrator.synthesize_report(
                                            metrics=metrics,
                                            report_type="real_time_sentinel_brief",
                                            market_context={"location": analysis_context["market"]},
                                        )
                                    )

                                    st.markdown(analysis_result.content)

                                    # Handle recommended actions if any
                                    if analysis_result.recommended_actions:
                                        for action in analysis_result.recommended_actions[:1]:
                                            if st.button(
                                                f"⚡ {action.get('action', 'Execute Action')}", type="primary"
                                            ):
                                                st.toast(f"Executing: {action.get('action')}", icon="📨")
                                except Exception as e:
                                    st.error(f"Sentinel Analysis Error: {str(e)}")
                                    # Fallback
                                    st.markdown("""
                                    *I'm monitoring your market webhooks. Here is what's happening:*
                                    - **✅ System Pulse:** All webhooks are firing correctly.
                                    - **📈 Activity:** Lead engagement is up 12% in the last hour.
                                    """)
                        else:
                            st.info("📡 Monitoring live streams... Waiting for event patterns to emerge.")
                    else:
                        # Fallback if orchestrator not available
                        st.markdown("""
                        *I'm monitoring your market webhooks in milliseconds. Here is what's happening NOW:*
                        - **⚡ Instant Response:** Just sent an auto-responder to a new inquiry.
                        - **🔥 High Intent:** Increasing activity detected in high-value listings.
                        - **✅ System Pulse:** All 12 webhooks are firing correctly.
                        """)

            render_overview_dashboard(realtime_service, state_manager, layout_manager)

        with tab2:
            render_live_lead_scoreboard(realtime_service, state_manager)

        with tab3:
            render_alert_center(realtime_service, state_manager)

        with tab4:
            render_interactive_analytics(realtime_service, state_manager)

        with tab5:
            render_matrix_view()

        with tab6:
            render_performance_dashboard(realtime_service, state_manager)

        with tab7:
            render_payload_monitor()

        with tab_whisper:
            from ghl_real_estate_ai.streamlit_demo.components.whisper_dashboard import render_whisper_dashboard

            render_whisper_dashboard(
                lead_id="tech_professional_sarah", lead_name="Sarah Chen", property_address="789 Pine Ave, Austin, TX"
            )

    except ImportError as e:
        render_fallback_dashboard(f"Component import error: {str(e)}")
    except Exception as e:
        import sys
        import traceback

        error_details = traceback.format_exc()
        print(f"DEBUG DASHBOARD ERROR: {str(e)}")
        print(error_details)
        render_fallback_dashboard(f"Dashboard initialization error: {str(e)}\n\nTraceback:\n{error_details}")


def render_overview_dashboard(realtime_service, state_manager, layout_manager):
    """Render the overview dashboard with all components in a grid layout"""

    try:
        # Get performance metrics for overview
        recent_events = realtime_service.get_recent_events(limit=10)
        metrics = realtime_service.get_metrics()

        # Key metrics at the top
        st.subheader("📊 System Performance Telemetry")

        # NEW: System Heartbeat Visualization
        heart_col1, heart_col2 = st.columns([2, 1])

        with heart_col1:
            st.markdown("#### 💓 System Heartbeat")
            # Generate heartbeat data
            times = pd.date_range(end=datetime.now(), periods=50, freq="10s")
            # Simulated pulse: higher when events happen
            pulse = [random.uniform(20, 40) + (100 if i % 12 == 0 else 0) for i in range(50)]

            fig_heart = go.Figure()
            fig_heart.add_trace(
                go.Scatter(
                    x=times,
                    y=pulse,
                    mode="lines",
                    line=dict(color="#6366F1", width=2),
                    fill="tozeroy",
                    fillcolor="rgba(99, 102, 241, 0.05)",
                )
            )
            fig_heart.update_layout(
                height=150,
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 150]),
                margin=dict(l=0, r=0, t=0, b=0),
            )
            from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart

            st.plotly_chart(style_obsidian_chart(fig_heart), use_container_width=True, config={"displayModeBar": False})

        with heart_col2:
            st.markdown("#### 📡 Intelligence Feed")
            activity_log = [
                "🕵️ Lead 'Sarah C.' qualified",
                "🐝 Swarm Agent #4 delegated",
                "💰 Deal probability sync: 82%",
                "⚡ GHL Webhook processed (14ms)",
            ]
            for log in activity_log:
                st.markdown(
                    f"<div style='font-size: 0.8rem; color: #8B949E; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.03);'>{log}</div>",
                    unsafe_allow_html=True,
                )

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Live Events", metrics.get("events_processed", 0), delta=f"+{metrics.get('events_sent', 0)} sent")

        with col2:
            st.metric(
                "Active Subscribers",
                len(metrics.get("subscribers", {})),
                delta=f"{metrics.get('queue_size', 0)} queued",
            )

        with col3:
            uptime = metrics.get("uptime_seconds", 0)
            uptime_str = f"{uptime // 3600:.0f}h {(uptime % 3600) // 60:.0f}m"
            st.metric("Uptime", uptime_str, delta="🟢 Online" if metrics.get("is_running", False) else "🔴 Offline")

        with col4:
            cache_hit_rate = 0
            total_cache_ops = metrics.get("cache_hits", 0) + metrics.get("cache_misses", 0)
            if total_cache_ops > 0:
                cache_hit_rate = (metrics.get("cache_hits", 0) / total_cache_ops) * 100

            st.metric("Cache Hit Rate", f"{cache_hit_rate:.1f}%", delta=f"{total_cache_ops} ops")

        st.markdown("---")

        # Real-time dashboard preview grid
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("🎯 Live Lead Activity Preview")
            # Mini version of live scoreboard
            from components.live_lead_scoreboard import LiveLeadScoreboard

            scoreboard = LiveLeadScoreboard(realtime_service, state_manager)

            # Show just top 3 leads for overview
            leads_data = scoreboard._get_live_leads_data()[:3]

            if leads_data:
                for lead in leads_data:
                    score = lead["score"]
                    status = lead["status"]

                    col_a, col_b, col_c = st.columns([2, 1, 1])
                    with col_a:
                        st.write(f"**{lead['name']}**")
                    with col_b:
                        st.write(f"Score: {score}")
                    with col_c:
                        if status == "hot":
                            st.write("🔥 Hot")
                        elif status == "warm":
                            st.write("🌡️ Warm")
                        else:
                            st.write("❄️ Cold")

            if st.button("➡️ View Full Scoreboard", key="goto_scoreboard"):
                st.info("Switch to 'Lead Scoreboard' tab to see full details!")

        with col2:
            st.subheader("🚨 Recent Alerts Preview")
            # Mini version of alert center
            from components.alert_center import AlertCenter

            alert_center = AlertCenter(realtime_service, state_manager)

            alerts_data = alert_center._get_alerts_data()[:3]

            if alerts_data:
                for alert in alerts_data:
                    priority_emoji = {4: "🔴", 3: "🟠", 2: "🔵", 1: "🟢"}[alert["priority"]]
                    st.write(f"{priority_emoji} **{alert['type'].replace('_', ' ').title()}**")
                    st.write(f"_{alert['message'][:60]}..._")
                    st.markdown("---")

            if st.button("➡️ View Alert Center", key="goto_alerts"):
                st.info("Switch to 'Alert Center' tab for full alert management!")

        st.markdown("---")

        # Quick analytics preview
        st.subheader("📈 Analytics Preview")

        # Simple metrics chart
        import plotly.graph_objects as go

        fig = go.Figure()

        # Generate sample trend data for overview
        from datetime import timedelta

        dates = [datetime.now() - timedelta(days=i) for i in range(7, 0, -1)]
        values = [45 + i * 2 + (i % 3) * 5 for i in range(7)]

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=values,
                mode="lines+markers",
                name="Leads Processed",
                line=dict(color="#3498db", width=3),
                fill="tonexty",
                fillcolor="rgba(52, 152, 219, 0.1)",
            )
        )

        fig.update_layout(
            height=200, margin=dict(l=0, r=0, t=20, b=0), showlegend=False, xaxis_title="Date", yaxis_title="Count"
        )

        st.plotly_chart(fig, use_container_width=True)

        if st.button("➡️ View Full Analytics", key="goto_analytics"):
            st.info("Switch to 'Interactive Analytics' tab for detailed insights!")

        # Recent events log
        st.markdown("---")
        st.subheader("📋 Recent Events")

        if recent_events:
            events_df = pd.DataFrame(
                [
                    {
                        "Time": event.timestamp.strftime("%H:%M:%S"),
                        "Type": event.event_type.replace("_", " ").title(),
                        "Priority": "🔴"
                        if event.priority == 4
                        else "🟠"
                        if event.priority == 3
                        else "🔵"
                        if event.priority == 2
                        else "🟢",
                        "Source": event.source,
                        "Details": str(event.data)[:80] + "..." if len(str(event.data)) > 80 else str(event.data),
                    }
                    for event in recent_events[-5:]  # Last 5 events for overview
                ]
            )

            st.dataframe(events_df, use_container_width=True, hide_index=True)
        else:
            st.info("📡 Waiting for real-time events...")

        # Auto-refresh indicator
        if state_manager.user_preferences.auto_refresh:
            st.markdown(
                """
            <div style="position: fixed; top: 100px; right: 20px; background: rgba(46, 204, 113, 0.1);
                        color: #27ae60; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.8rem;
                        border: 1px solid rgba(46, 204, 113, 0.3); backdrop-filter: blur(10px);
                        z-index: 999;">
                🔄 Auto-refreshing every {}s
            </div>
            """.format(state_manager.user_preferences.refresh_interval),
                unsafe_allow_html=True,
            )

    except Exception as e:
        st.error(f"Error rendering overview dashboard: {str(e)}")
        st.info("💡 Try refreshing the page or check the real-time service status.")


def render_fallback_dashboard(error_message: str):
    """Render a fallback dashboard when components are not available"""

    st.warning("⚠️ Real-Time Dashboard Components Loading...")

    st.markdown(
        f"""
    <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 2rem; border-radius: 15px; text-align: center; margin: 2rem 0;">
        <h2>🔧 Dashboard Initializing</h2>
        <p>The Real-Time Intelligence Dashboard is starting up. This may take a moment.</p>
        <p><small>Technical details: {error_message}</small></p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Show demo metrics while loading
    st.subheader("📊 System Status")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Status", "Starting", delta="⏳")

    with col2:
        st.metric("Components", "Loading", delta="🔄")

    with col3:
        st.metric("Services", "Initializing", delta="⚙️")

    with col4:
        st.metric("Real-Time", "Connecting", delta="📡")

    st.markdown("---")

    # Show placeholder content
    st.subheader("🎯 Available Features")

    features = [
        {"name": "Live Lead Scoreboard", "icon": "📊", "status": "Ready"},
        {"name": "Alert Center", "icon": "🚨", "status": "Ready"},
        {"name": "Interactive Analytics", "icon": "📈", "status": "Ready"},
        {"name": "Performance Dashboard", "icon": "⚡", "status": "Ready"},
        {"name": "Mobile Responsive Design", "icon": "📱", "status": "Ready"},
        {"name": "Real-Time WebSocket Updates", "icon": "🔄", "status": "Connecting"},
    ]

    for feature in features:
        col1, col2, col3 = st.columns([3, 2, 1])

        with col1:
            st.write(f"{feature['icon']} **{feature['name']}**")

        with col2:
            status_color = "#2ecc71" if feature["status"] == "Ready" else "#f39c12"
            st.markdown(
                f'<span style="color: {status_color}; font-weight: bold;">{feature["status"]}</span>',
                unsafe_allow_html=True,
            )

        with col3:
            if feature["status"] == "Ready":
                st.write("✅")
            else:
                st.write("⏳")

    st.info(
        "💡 **Tip:** If components don't load, try refreshing the page or check that all required dependencies are installed."
    )

    # Refresh button
    if st.button("🔄 Refresh Dashboard", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
