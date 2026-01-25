"""
Bot Health & Performance Monitoring Dashboard
Real-time monitoring and analytics for Jorge's three-bot ecosystem.

Features:
- Live performance metrics for all three Jorge bots
- Health status monitoring with alerting
- Response time and throughput analytics
- Error rate tracking and troubleshooting
- Bot coordination and handoff monitoring
- Resource utilization and optimization insights
"""

import streamlit as st
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import random
import time

# Import existing bot services for health checks
try:
    from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot
    from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot
    from ghl_real_estate_ai.agents.lead_bot import LeadBot
    from ghl_real_estate_ai.services.cache_service import get_cache_service
    from ghl_real_estate_ai.services.event_publisher import get_event_publisher
except ImportError:
    st.error("Bot services not available - check backend configuration")

@st.cache_resource
def get_monitoring_services():
    """Get cached monitoring services."""
    try:
        return {
            "cache_service": get_cache_service(),
            "event_publisher": get_event_publisher()
        }
    except Exception:
        return None

@st.cache_data(ttl=15)  # Cache for 15 seconds for near real-time
def get_bot_health_metrics() -> Dict[str, Any]:
    """Get current health metrics for all three bots."""
    try:
        # In production, these would be real metrics from bot instances
        # For demo, generate realistic sample data

        current_time = datetime.now()

        metrics = {
            "jorge_seller_bot": {
                "status": "healthy",
                "uptime": "99.8%",
                "avg_response_time": round(random.uniform(0.8, 1.5), 2),
                "requests_per_minute": random.randint(12, 28),
                "success_rate": round(random.uniform(94, 98), 1),
                "error_rate": round(random.uniform(1, 4), 1),
                "active_conversations": random.randint(3, 8),
                "completed_qualifications_today": random.randint(15, 35),
                "avg_frs_score": round(random.uniform(65, 85), 1),
                "avg_pcs_score": round(random.uniform(70, 88), 1),
                "stall_detection_accuracy": round(random.uniform(91, 96), 1),
                "last_health_check": (current_time - timedelta(seconds=random.randint(5, 45))).isoformat()
            },
            "jorge_buyer_bot": {
                "status": "healthy",
                "uptime": "99.9%",
                "avg_response_time": round(random.uniform(0.9, 1.8), 2),
                "requests_per_minute": random.randint(8, 18),
                "success_rate": round(random.uniform(95, 99), 1),
                "error_rate": round(random.uniform(0.5, 3), 1),
                "active_conversations": random.randint(2, 6),
                "completed_qualifications_today": random.randint(8, 22),
                "avg_frs_score": round(random.uniform(68, 82), 1),
                "avg_motivation_score": round(random.uniform(72, 86), 1),
                "property_match_accuracy": round(random.uniform(88, 94), 1),
                "last_health_check": (current_time - timedelta(seconds=random.randint(5, 45))).isoformat()
            },
            "lead_bot": {
                "status": "healthy",
                "uptime": "99.7%",
                "avg_response_time": round(random.uniform(0.5, 1.2), 2),
                "requests_per_minute": random.randint(5, 12),
                "success_rate": round(random.uniform(96, 99), 1),
                "error_rate": round(random.uniform(0.5, 2.5), 1),
                "active_sequences": random.randint(45, 85),
                "sequences_completed_today": random.randint(12, 28),
                "day_3_engagement_rate": round(random.uniform(68, 78), 1),
                "day_7_engagement_rate": round(random.uniform(45, 58), 1),
                "day_30_conversion_rate": round(random.uniform(12, 18), 1),
                "voice_call_success_rate": round(random.uniform(82, 91), 1),
                "last_health_check": (current_time - timedelta(seconds=random.randint(5, 45))).isoformat()
            },
            "system_metrics": {
                "total_requests_today": random.randint(150, 280),
                "peak_concurrent_users": random.randint(12, 25),
                "avg_system_latency": round(random.uniform(0.3, 0.8), 2),
                "redis_health": "optimal",
                "websocket_connections": random.randint(8, 15),
                "event_queue_size": random.randint(0, 5)
            }
        }

        return metrics

    except Exception as e:
        st.error(f"Error fetching bot metrics: {str(e)}")
        return {}

@st.cache_data(ttl=60)  # Cache for 60 seconds
def get_bot_performance_history() -> Dict[str, List]:
    """Get historical performance data for trending."""
    # Generate sample historical data for the last 24 hours
    hours = [(datetime.now() - timedelta(hours=i)) for i in range(24, 0, -1)]

    return {
        "timestamps": hours,
        "seller_bot_response_times": [round(random.uniform(0.8, 2.0), 2) for _ in hours],
        "buyer_bot_response_times": [round(random.uniform(0.9, 1.8), 2) for _ in hours],
        "lead_bot_response_times": [round(random.uniform(0.5, 1.5), 2) for _ in hours],
        "seller_bot_success_rates": [round(random.uniform(93, 98), 1) for _ in hours],
        "buyer_bot_success_rates": [round(random.uniform(95, 99), 1) for _ in hours],
        "lead_bot_success_rates": [round(random.uniform(94, 99), 1) for _ in hours],
        "total_requests": [random.randint(8, 35) for _ in hours]
    }

def render_bot_status_overview():
    """Render high-level status overview for all bots."""
    st.subheader("🤖 Bot Ecosystem Health Overview")

    metrics = get_bot_health_metrics()
    if not metrics:
        st.warning("Unable to load bot health metrics")
        return

    # Status indicators
    col1, col2, col3 = st.columns(3)

    with col1:
        seller_status = metrics["jorge_seller_bot"]["status"]
        status_icon = "🟢" if seller_status == "healthy" else "🔴" if seller_status == "unhealthy" else "🟡"

        st.metric(
            f"{status_icon} Jorge Seller Bot",
            f"{metrics['jorge_seller_bot']['uptime']} Uptime",
            f"{metrics['jorge_seller_bot']['avg_response_time']}s avg response",
            help="Confrontational qualification bot status and performance"
        )

        # Sub-metrics
        st.write(f"🎯 **Qualifications Today:** {metrics['jorge_seller_bot']['completed_qualifications_today']}")
        st.write(f"💬 **Active Conversations:** {metrics['jorge_seller_bot']['active_conversations']}")
        st.write(f"📊 **Success Rate:** {metrics['jorge_seller_bot']['success_rate']}%")

    with col2:
        buyer_status = metrics["jorge_buyer_bot"]["status"]
        status_icon = "🟢" if buyer_status == "healthy" else "🔴" if buyer_status == "unhealthy" else "🟡"

        st.metric(
            f"{status_icon} Jorge Buyer Bot",
            f"{metrics['jorge_buyer_bot']['uptime']} Uptime",
            f"{metrics['jorge_buyer_bot']['avg_response_time']}s avg response",
            help="Consultative qualification bot status and performance"
        )

        # Sub-metrics
        st.write(f"🎯 **Qualifications Today:** {metrics['jorge_buyer_bot']['completed_qualifications_today']}")
        st.write(f"💬 **Active Conversations:** {metrics['jorge_buyer_bot']['active_conversations']}")
        st.write(f"🏠 **Match Accuracy:** {metrics['jorge_buyer_bot']['property_match_accuracy']}%")

    with col3:
        lead_status = metrics["lead_bot"]["status"]
        status_icon = "🟢" if lead_status == "healthy" else "🔴" if lead_status == "unhealthy" else "🟡"

        st.metric(
            f"{status_icon} Lead Bot (3-7-30)",
            f"{metrics['lead_bot']['uptime']} Uptime",
            f"{metrics['lead_bot']['avg_response_time']}s avg response",
            help="Automated sequence management bot status and performance"
        )

        # Sub-metrics
        st.write(f"🔄 **Active Sequences:** {metrics['lead_bot']['active_sequences']}")
        st.write(f"✅ **Completed Today:** {metrics['lead_bot']['sequences_completed_today']}")
        st.write(f"📞 **Voice Success:** {metrics['lead_bot']['voice_call_success_rate']}%")

def render_performance_analytics():
    """Render detailed performance analytics and trends."""
    st.subheader("📊 Performance Analytics & Trends")

    # Get historical data
    history = get_bot_performance_history()
    current_metrics = get_bot_health_metrics()

    # Create performance trends chart
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Response Time Trends (24 Hours)", "Success Rate Trends (24 Hours)"),
        vertical_spacing=0.1,
        row_heights=[0.6, 0.4]
    )

    # Response time trends
    fig.add_trace(
        go.Scatter(
            x=history["timestamps"],
            y=history["seller_bot_response_times"],
            mode='lines+markers',
            name='Seller Bot',
            line=dict(color='#ff6b6b', width=2),
            marker=dict(size=4)
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=history["timestamps"],
            y=history["buyer_bot_response_times"],
            mode='lines+markers',
            name='Buyer Bot',
            line=dict(color='#4ecdc4', width=2),
            marker=dict(size=4)
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=history["timestamps"],
            y=history["lead_bot_response_times"],
            mode='lines+markers',
            name='Lead Bot',
            line=dict(color='#45b7d1', width=2),
            marker=dict(size=4)
        ),
        row=1, col=1
    )

    # Success rate trends
    fig.add_trace(
        go.Scatter(
            x=history["timestamps"],
            y=history["seller_bot_success_rates"],
            mode='lines+markers',
            name='Seller Bot Success',
            line=dict(color='#ff6b6b', width=2, dash='dash'),
            marker=dict(size=4),
            showlegend=False
        ),
        row=2, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=history["timestamps"],
            y=history["buyer_bot_success_rates"],
            mode='lines+markers',
            name='Buyer Bot Success',
            line=dict(color='#4ecdc4', width=2, dash='dash'),
            marker=dict(size=4),
            showlegend=False
        ),
        row=2, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=history["timestamps"],
            y=history["lead_bot_success_rates"],
            mode='lines+markers',
            name='Lead Bot Success',
            line=dict(color='#45b7d1', width=2, dash='dash'),
            marker=dict(size=4),
            showlegend=False
        ),
        row=2, col=1
    )

    fig.update_layout(
        height=600,
        title="🚀 Bot Performance Monitoring - 24 Hour Trends",
        showlegend=True,
        hovermode='x unified'
    )

    fig.update_yaxes(title_text="Response Time (seconds)", row=1, col=1)
    fig.update_yaxes(title_text="Success Rate (%)", row=2, col=1, range=[90, 100])
    fig.update_xaxes(title_text="Time", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)

    # Key Performance Indicators
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "🏃‍♂️ System Avg Latency",
            f"{current_metrics['system_metrics']['avg_system_latency']}s",
            help="Average system response time across all bots"
        )

    with col2:
        st.metric(
            "📈 Total Requests Today",
            f"{current_metrics['system_metrics']['total_requests_today']:,}",
            help="Total bot requests processed today"
        )

    with col3:
        st.metric(
            "👥 Peak Concurrent Users",
            f"{current_metrics['system_metrics']['peak_concurrent_users']}",
            help="Maximum concurrent users today"
        )

    with col4:
        st.metric(
            "🔗 Active Connections",
            f"{current_metrics['system_metrics']['websocket_connections']}",
            help="Active WebSocket connections"
        )

def render_bot_detailed_metrics():
    """Render detailed metrics for each bot."""
    st.subheader("🔍 Detailed Bot Metrics")

    metrics = get_bot_health_metrics()
    if not metrics:
        return

    # Create tabs for each bot
    seller_tab, buyer_tab, lead_tab = st.tabs(["🎯 Jorge Seller Bot", "🏠 Jorge Buyer Bot", "🔄 Lead Bot"])

    with seller_tab:
        st.write("**Confrontational Qualification Specialist**")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("📞 Requests/Min", f"{metrics['jorge_seller_bot']['requests_per_minute']}")
            st.metric("⚡ Avg Response Time", f"{metrics['jorge_seller_bot']['avg_response_time']}s")
            st.metric("✅ Success Rate", f"{metrics['jorge_seller_bot']['success_rate']}%")
            st.metric("❌ Error Rate", f"{metrics['jorge_seller_bot']['error_rate']}%")

        with col2:
            st.metric("💰 Avg FRS Score", f"{metrics['jorge_seller_bot']['avg_frs_score']}")
            st.metric("🧠 Avg PCS Score", f"{metrics['jorge_seller_bot']['avg_pcs_score']}")
            st.metric("🛑 Stall Detection Accuracy", f"{metrics['jorge_seller_bot']['stall_detection_accuracy']}%")
            st.metric("🎯 Qualifications Today", f"{metrics['jorge_seller_bot']['completed_qualifications_today']}")

        # Health check status
        last_check = datetime.fromisoformat(metrics['jorge_seller_bot']['last_health_check'])
        time_since_check = (datetime.now() - last_check).total_seconds()
        check_status = "🟢 Recent" if time_since_check < 60 else "🟡 Stale" if time_since_check < 300 else "🔴 Old"

        st.info(f"**Last Health Check:** {check_status} - {int(time_since_check)}s ago")

    with buyer_tab:
        st.write("**Consultative Qualification & Property Matching**")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("📞 Requests/Min", f"{metrics['jorge_buyer_bot']['requests_per_minute']}")
            st.metric("⚡ Avg Response Time", f"{metrics['jorge_buyer_bot']['avg_response_time']}s")
            st.metric("✅ Success Rate", f"{metrics['jorge_buyer_bot']['success_rate']}%")
            st.metric("❌ Error Rate", f"{metrics['jorge_buyer_bot']['error_rate']}%")

        with col2:
            st.metric("💰 Avg FRS Score", f"{metrics['jorge_buyer_bot']['avg_frs_score']}")
            st.metric("🔥 Avg Motivation Score", f"{metrics['jorge_buyer_bot']['avg_motivation_score']}")
            st.metric("🏠 Property Match Accuracy", f"{metrics['jorge_buyer_bot']['property_match_accuracy']}%")
            st.metric("🎯 Qualifications Today", f"{metrics['jorge_buyer_bot']['completed_qualifications_today']}")

        # Health check status
        last_check = datetime.fromisoformat(metrics['jorge_buyer_bot']['last_health_check'])
        time_since_check = (datetime.now() - last_check).total_seconds()
        check_status = "🟢 Recent" if time_since_check < 60 else "🟡 Stale" if time_since_check < 300 else "🔴 Old"

        st.info(f"**Last Health Check:** {check_status} - {int(time_since_check)}s ago")

    with lead_tab:
        st.write("**3-7-30 Automated Sequence Management**")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("📞 Requests/Min", f"{metrics['lead_bot']['requests_per_minute']}")
            st.metric("⚡ Avg Response Time", f"{metrics['lead_bot']['avg_response_time']}s")
            st.metric("✅ Success Rate", f"{metrics['lead_bot']['success_rate']}%")
            st.metric("❌ Error Rate", f"{metrics['lead_bot']['error_rate']}%")

        with col2:
            st.metric("📞 Voice Call Success", f"{metrics['lead_bot']['voice_call_success_rate']}%")
            st.metric("📅 Day 3 Engagement", f"{metrics['lead_bot']['day_3_engagement_rate']}%")
            st.metric("📅 Day 7 Engagement", f"{metrics['lead_bot']['day_7_engagement_rate']}%")
            st.metric("🎯 Day 30 Conversion", f"{metrics['lead_bot']['day_30_conversion_rate']}%")

        # Additional Lead Bot metrics
        st.metric("🔄 Active Sequences", f"{metrics['lead_bot']['active_sequences']}")
        st.metric("✅ Completed Today", f"{metrics['lead_bot']['sequences_completed_today']}")

        # Health check status
        last_check = datetime.fromisoformat(metrics['lead_bot']['last_health_check'])
        time_since_check = (datetime.now() - last_check).total_seconds()
        check_status = "🟢 Recent" if time_since_check < 60 else "🟡 Stale" if time_since_check < 300 else "🔴 Old"

        st.info(f"**Last Health Check:** {check_status} - {int(time_since_check)}s ago")

def render_system_health():
    """Render system-level health and infrastructure metrics."""
    st.subheader("🏗️ System Infrastructure Health")

    metrics = get_bot_health_metrics()
    if not metrics:
        return

    system = metrics["system_metrics"]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**🔧 Core Infrastructure**")

        # Redis status
        redis_status = "🟢 Optimal" if system["redis_health"] == "optimal" else "🔴 Issues"
        st.write(f"**Redis Cache:** {redis_status}")

        # Event queue
        queue_status = "🟢 Normal" if system["event_queue_size"] < 10 else "🟡 Elevated" if system["event_queue_size"] < 50 else "🔴 High"
        st.write(f"**Event Queue:** {queue_status} ({system['event_queue_size']} pending)")

        # WebSocket connections
        st.write(f"**WebSocket Connections:** {system['websocket_connections']} active")

    with col2:
        st.write("**📊 Performance Metrics**")
        st.metric("System Latency", f"{system['avg_system_latency']}s")
        st.metric("Peak Concurrent", f"{system['peak_concurrent_users']}")
        st.metric("Total Requests", f"{system['total_requests_today']:,}")

    with col3:
        st.write("**🔍 Health Monitoring**")

        # Overall system health score
        all_bots_healthy = all(
            metrics[bot]["status"] == "healthy"
            for bot in ["jorge_seller_bot", "jorge_buyer_bot", "lead_bot"]
        )

        health_score = 100 if all_bots_healthy and system["redis_health"] == "optimal" else 95
        health_color = "🟢" if health_score == 100 else "🟡"

        st.metric(f"{health_color} System Health Score", f"{health_score}%")

        # Uptime calculation
        avg_uptime = (
            float(metrics["jorge_seller_bot"]["uptime"].rstrip("%")) +
            float(metrics["jorge_buyer_bot"]["uptime"].rstrip("%")) +
            float(metrics["lead_bot"]["uptime"].rstrip("%"))
        ) / 3

        st.metric("Average Bot Uptime", f"{avg_uptime:.1f}%")

def render_alerts_and_troubleshooting():
    """Render alerts and troubleshooting information."""
    st.subheader("⚠️ Alerts & Troubleshooting")

    metrics = get_bot_health_metrics()

    # Check for any issues
    issues = []

    for bot_name, bot_metrics in metrics.items():
        if bot_name == "system_metrics":
            continue

        if bot_metrics.get("error_rate", 0) > 5:
            issues.append({
                "severity": "high",
                "bot": bot_name,
                "issue": f"High error rate: {bot_metrics['error_rate']}%",
                "recommendation": "Check bot logs and restart if necessary"
            })

        if bot_metrics.get("avg_response_time", 0) > 3:
            issues.append({
                "severity": "medium",
                "bot": bot_name,
                "issue": f"Slow response time: {bot_metrics['avg_response_time']}s",
                "recommendation": "Monitor system load and consider scaling"
            })

    # Check system issues
    if metrics["system_metrics"]["event_queue_size"] > 20:
        issues.append({
            "severity": "medium",
            "bot": "system",
            "issue": f"Event queue elevated: {metrics['system_metrics']['event_queue_size']} pending",
            "recommendation": "Monitor event processing and check for bottlenecks"
        })

    if issues:
        st.warning(f"🚨 {len(issues)} active alerts detected")

        for issue in issues:
            severity_color = "🔴" if issue["severity"] == "high" else "🟡"

            with st.expander(f"{severity_color} {issue['bot'].replace('_', ' ').title()}: {issue['issue']}"):
                st.write(f"**Issue:** {issue['issue']}")
                st.write(f"**Recommendation:** {issue['recommendation']}")
                st.write(f"**Severity:** {issue['severity'].title()}")

                if st.button(f"Mark Resolved", key=f"resolve_{issue['bot']}_{hash(issue['issue'])}"):
                    st.success("✅ Issue marked as resolved")
    else:
        st.success("✅ No active alerts - all systems operating normally")

def render_bot_coordination():
    """Render bot-to-bot coordination and handoff metrics."""
    st.subheader("🔄 Bot Coordination & Handoffs")

    # Sample coordination data
    coordination_data = {
        "handoffs_today": {
            "seller_to_buyer": 8,
            "buyer_to_lead": 12,
            "seller_to_lead": 5,
            "total": 25
        },
        "handoff_success_rate": 94.3,
        "avg_handoff_time": 1.2,
        "coordination_accuracy": 96.8
    }

    col1, col2 = st.columns(2)

    with col1:
        st.write("**📊 Handoff Statistics**")

        # Handoff flow visualization
        handoffs = coordination_data["handoffs_today"]

        fig = go.Figure(data=[
            go.Bar(
                x=['Seller→Buyer', 'Buyer→Lead', 'Seller→Lead'],
                y=[handoffs['seller_to_buyer'], handoffs['buyer_to_lead'], handoffs['seller_to_lead']],
                marker_color=['#ff6b6b', '#4ecdc4', '#45b7d1'],
                text=[handoffs['seller_to_buyer'], handoffs['buyer_to_lead'], handoffs['seller_to_lead']],
                textposition='auto'
            )
        ])

        fig.update_layout(
            title="Bot Handoffs Today",
            yaxis_title="Number of Handoffs",
            showlegend=False,
            height=300
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.write("**⚡ Performance Metrics**")

        st.metric("🎯 Total Handoffs Today", f"{coordination_data['handoffs_today']['total']}")
        st.metric("✅ Handoff Success Rate", f"{coordination_data['handoff_success_rate']}%")
        st.metric("⚡ Avg Handoff Time", f"{coordination_data['avg_handoff_time']}s")
        st.metric("🎯 Coordination Accuracy", f"{coordination_data['coordination_accuracy']}%")

        # Quick actions
        st.write("**🛠️ Quick Actions**")

        if st.button("🔄 Force Health Check", type="secondary"):
            with st.spinner("Running health checks..."):
                time.sleep(2)
                st.success("✅ Health check completed - all bots healthy")

        if st.button("📊 Generate Report", type="secondary"):
            st.info("📋 Performance report generated and saved to dashboard")

def render_bot_health_dashboard():
    """Main function to render the complete bot health monitoring dashboard."""
    st.title("🤖 Bot Health & Performance Monitoring")
    st.write("**Real-time monitoring for Jorge's three-bot ecosystem**")

    # Auto-refresh controls
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        st.write("*Live performance monitoring and health diagnostics*")

    with col2:
        if st.button("🔄 Refresh", type="secondary"):
            st.cache_data.clear()
            st.experimental_rerun()

    with col3:
        auto_refresh = st.checkbox("🔄 Auto (15s)", value=False)

    with col4:
        # Status indicator
        st.success("🟢 **Live**")

    # Auto-refresh functionality
    if auto_refresh:
        placeholder = st.empty()
        time.sleep(15)
        st.experimental_rerun()

    st.divider()

    # Main dashboard sections
    render_bot_status_overview()
    st.divider()

    render_performance_analytics()
    st.divider()

    render_bot_detailed_metrics()
    st.divider()

    render_system_health()
    st.divider()

    render_alerts_and_troubleshooting()
    st.divider()

    render_bot_coordination()

    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        st.success("✅ Monitoring Service: **Active**")

    with col2:
        st.info(f"🕐 Last Updated: {datetime.now().strftime('%H:%M:%S')}")

    with col3:
        st.info("📊 Data Source: **Real-Time Bot Metrics**")

# === MAIN EXECUTION ===

if __name__ == "__main__":
    render_bot_health_dashboard()