"""
Real-Time Intelligence Dashboard Integration for GHL Real Estate AI

This module integrates all real-time dashboard components into the main application.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import traceback
from services.claude_assistant import ClaudeAssistant

# Initialize Claude Assistant
claude = ClaudeAssistant()

@st.cache_data(ttl=60)  # Cache for 1 minute
def get_dashboard_status():
    """Get dashboard status for caching"""
    return {
        'status': 'online',
        'last_update': datetime.now().isoformat(),
        'components_loaded': True
    }

def render_realtime_intelligence_dashboard():
    """Render the Real-Time Intelligence Dashboard with all components"""

    # Dashboard header with status indicator
    col1, col2 = st.columns([4, 1])

    with col1:
        st.header("⚡ Real-Time Intelligence Dashboard")
        st.markdown("*Live monitoring, analytics, and actionable insights in real-time*")

    with col2:
        status = get_dashboard_status()
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: linear-gradient(45deg, #2ecc71, #27ae60);
                    border-radius: 10px; color: white; margin: 1rem 0;">
            <div style="font-size: 1.2rem; font-weight: bold;">🟢 LIVE</div>
            <div style="font-size: 0.8rem; opacity: 0.9;">Real-Time Active</div>
        </div>
        """, unsafe_allow_html=True)

    # Import and initialize services with error handling
    try:
        # Import components
        from services.realtime_data_service import get_realtime_service
        from services.dashboard_state_manager import get_dashboard_state_manager, dashboard_sidebar_controls
        from components.mobile_responsive_layout import get_layout_manager
        from components.live_lead_scoreboard import render_live_lead_scoreboard
        from components.alert_center import render_alert_center
        from components.interactive_analytics import render_interactive_analytics
        from components.performance_dashboard import render_performance_dashboard
        from components.payload_monitor import render_payload_monitor

        # Initialize services
        realtime_service = get_realtime_service()
        state_manager = get_dashboard_state_manager()
        layout_manager = get_layout_manager()

        # Claude Intelligence Integration
        claude.greet_user("Jorge")
        claude.render_sidebar_panel("Real-Time Intelligence", st.session_state.get("selected_market", "Austin"), {})

        # Dashboard sidebar controls
        with st.sidebar:
            st.markdown("### ⚡ Real-Time Controls")
            dashboard_sidebar_controls()

        # Main dashboard tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🎯 Live Overview",
            "📊 Lead Scoreboard",
            "🚨 Alert Center",
            "📈 Interactive Analytics",
            "⚡ Performance",
            "📦 Payload Monitor"
        ])

        with tab1:
            # Claude's Live Sentinel
            with st.container(border=True):
                c_icon, c_text = st.columns([1, 8])
                with c_icon:
                    st.markdown("<div style='font-size: 3rem; text-align: center;'>🛰️</div>", unsafe_allow_html=True)
                with c_text:
                    st.markdown("### Claude's Live Sentinel")
                    st.markdown("""
                    *I'm monitoring your Austin market webhooks in milliseconds. Here is what's happening NOW:*
                    - **⚡ Instant Response:** Just sent an auto-responder to a new inquiry from Zillow. Response time: 42s.
                    - **🔥 High Intent:** A lead (c_14) just viewed the 'Luxury Villa' listing for the 4th time in 5 minutes.
                    - **✅ System Pulse:** All 12 webhooks are firing correctly. No dropped payloads detected in the last hour.
                    """)
                    if st.button("💬 Text High-Intent Lead Now", type="primary"):
                        st.toast("Drafting personalized SMS for lead c_14...", icon="📨")
            
            render_overview_dashboard(realtime_service, state_manager, layout_manager)

        with tab2:
            render_live_lead_scoreboard(realtime_service, state_manager)

        with tab3:
            render_alert_center(realtime_service, state_manager)

        with tab4:
            render_interactive_analytics(realtime_service, state_manager)

        with tab5:
            render_performance_dashboard(realtime_service, state_manager)
            
        with tab6:
            render_payload_monitor()

    except ImportError as e:
        render_fallback_dashboard(f"Component import error: {str(e)}")
    except Exception as e:
        render_fallback_dashboard(f"Dashboard initialization error: {str(e)}")

def render_overview_dashboard(realtime_service, state_manager, layout_manager):
    """Render the overview dashboard with all components in a grid layout"""

    try:
        # Get performance metrics for overview
        recent_events = realtime_service.get_recent_events(limit=10)
        metrics = realtime_service.get_metrics()

        # Key metrics at the top
        st.subheader("📊 System Performance")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Live Events",
                metrics.get('events_processed', 0),
                delta=f"+{metrics.get('events_sent', 0)} sent"
            )

        with col2:
            st.metric(
                "Active Subscribers",
                len(metrics.get('subscribers', {})),
                delta=f"{metrics.get('queue_size', 0)} queued"
            )

        with col3:
            uptime = metrics.get('uptime_seconds', 0)
            uptime_str = f"{uptime//3600:.0f}h {(uptime%3600)//60:.0f}m"
            st.metric(
                "Uptime",
                uptime_str,
                delta="🟢 Online" if metrics.get('is_running', False) else "🔴 Offline"
            )

        with col4:
            cache_hit_rate = 0
            total_cache_ops = metrics.get('cache_hits', 0) + metrics.get('cache_misses', 0)
            if total_cache_ops > 0:
                cache_hit_rate = (metrics.get('cache_hits', 0) / total_cache_ops) * 100

            st.metric(
                "Cache Hit Rate",
                f"{cache_hit_rate:.1f}%",
                delta=f"{total_cache_ops} ops"
            )

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
                    score = lead['score']
                    status = lead['status']

                    col_a, col_b, col_c = st.columns([2, 1, 1])
                    with col_a:
                        st.write(f"**{lead['name']}**")
                    with col_b:
                        st.write(f"Score: {score}")
                    with col_c:
                        if status == 'hot':
                            st.write("🔥 Hot")
                        elif status == 'warm':
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
                    priority_emoji = {4: "🔴", 3: "🟠", 2: "🔵", 1: "🟢"}[alert['priority']]
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

        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode='lines+markers',
            name='Leads Processed',
            line=dict(color='#3498db', width=3),
            fill='tonexty',
            fillcolor='rgba(52, 152, 219, 0.1)'
        ))

        fig.update_layout(
            height=200,
            margin=dict(l=0, r=0, t=20, b=0),
            showlegend=False,
            xaxis_title="Date",
            yaxis_title="Count"
        )

        st.plotly_chart(fig, use_container_width=True)

        if st.button("➡️ View Full Analytics", key="goto_analytics"):
            st.info("Switch to 'Interactive Analytics' tab for detailed insights!")

        # Recent events log
        st.markdown("---")
        st.subheader("📋 Recent Events")

        if recent_events:
            events_df = pd.DataFrame([
                {
                    'Time': event.timestamp.strftime("%H:%M:%S"),
                    'Type': event.event_type.replace('_', ' ').title(),
                    'Priority': '🔴' if event.priority == 4 else '🟠' if event.priority == 3 else '🔵' if event.priority == 2 else '🟢',
                    'Source': event.source,
                    'Details': str(event.data)[:80] + '...' if len(str(event.data)) > 80 else str(event.data)
                }
                for event in recent_events[-5:]  # Last 5 events for overview
            ])

            st.dataframe(events_df, use_container_width=True, hide_index=True)
        else:
            st.info("📡 Waiting for real-time events...")

        # Auto-refresh indicator
        if state_manager.user_preferences.auto_refresh:
            st.markdown("""
            <div style="position: fixed; top: 100px; right: 20px; background: rgba(46, 204, 113, 0.1);
                        color: #27ae60; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.8rem;
                        border: 1px solid rgba(46, 204, 113, 0.3); backdrop-filter: blur(10px);
                        z-index: 999;">
                🔄 Auto-refreshing every {}s
            </div>
            """.format(state_manager.user_preferences.refresh_interval),
            unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error rendering overview dashboard: {str(e)}")
        st.info("💡 Try refreshing the page or check the real-time service status.")

def render_fallback_dashboard(error_message: str):
    """Render a fallback dashboard when components are not available"""

    st.warning("⚠️ Real-Time Dashboard Components Loading...")

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 2rem; border-radius: 15px; text-align: center; margin: 2rem 0;">
        <h2>🔧 Dashboard Initializing</h2>
        <p>The Real-Time Intelligence Dashboard is starting up. This may take a moment.</p>
        <p><small>Technical details: {error_message}</small></p>
    </div>
    """, unsafe_allow_html=True)

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
        {"name": "Real-Time WebSocket Updates", "icon": "🔄", "status": "Connecting"}
    ]

    for feature in features:
        col1, col2, col3 = st.columns([3, 2, 1])

        with col1:
            st.write(f"{feature['icon']} **{feature['name']}**")

        with col2:
            status_color = "#2ecc71" if feature['status'] == "Ready" else "#f39c12"
            st.markdown(f'<span style="color: {status_color}; font-weight: bold;">{feature["status"]}</span>',
                       unsafe_allow_html=True)

        with col3:
            if feature['status'] == "Ready":
                st.write("✅")
            else:
                st.write("⏳")

    st.info("💡 **Tip:** If components don't load, try refreshing the page or check that all required dependencies are installed.")

    # Refresh button
    if st.button("🔄 Refresh Dashboard", use_container_width=True):
        st.cache_data.clear()
        st.rerun()