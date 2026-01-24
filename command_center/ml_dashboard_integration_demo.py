#!/usr/bin/env python3
"""
ML Dashboard Integration Demo - Jorge's Real Estate AI Platform

This demo shows how to integrate the ML Scoring Dashboard with the existing
command center dashboard, including:
- Global filters integration
- Theme consistency with Jorge's patterns
- Real-time WebSocket updates (simulated)
- Authentication integration
- Navigation between dashboard sections

Usage:
    streamlit run command_center/ml_dashboard_integration_demo.py

Author: Jorge's AI Assistant
Version: 1.0.0
"""

import streamlit as st
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import dashboard components
from command_center.components.ml_scoring_dashboard import (
    apply_ml_dashboard_styles,
    render_dashboard_header,
    render_model_performance_overview,
    render_performance_visualizations,
    render_ab_testing_dashboard,
    render_inference_performance_dashboard,
    render_model_health_alerts
)

from command_center.components.global_filters import (
    GlobalFilters,
    render_ml_dashboard_filters
)

# Import Jorge's existing components (simulate imports)
try:
    from ghl_real_estate_ai.streamlit_demo.components.auth_component import (
        check_authentication, render_login_form, render_user_menu, require_permission
    )
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    st.warning("⚠️ Authentication components not available. Running in demo mode.")

# Configure Streamlit page
st.set_page_config(
    page_title="Jorge's ML Intelligence Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get help': 'https://github.com/jorge-real-estate-ai/help',
        'Report a bug': 'https://github.com/jorge-real-estate-ai/issues',
        'About': """
        # Jorge's ML Intelligence Dashboard

        **Advanced Machine Learning Analytics Platform**

        Real-time model performance monitoring and A/B testing interface
        for Jorge's Real Estate AI ecosystem.

        Features:
        - Model Performance Metrics UI with real-time tracking
        - ROC-AUC, precision, recall visualization using Plotly charts
        - Confidence Distribution Analysis
        - A/B Testing Dashboard for champion vs challenger comparison
        - Integration with existing dashboard patterns

        Built with ❤️ by Jorge's AI Assistant
        """
    }
)

def render_navigation_sidebar():
    """Render navigation sidebar with dashboard sections."""
    with st.sidebar:
        st.markdown("## 🏠 Jorge's Command Center")

        # Main navigation
        st.markdown("### 🧭 Navigation")

        nav_options = {
            "🏠 Main Dashboard": "main",
            "🤖 ML Intelligence": "ml_dashboard",
            "📈 Performance Analytics": "performance",
            "🧪 A/B Testing": "ab_testing",
            "⚡ Inference Monitoring": "inference",
            "🚨 Health & Alerts": "health"
        }

        # Use session state for navigation
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'ml_dashboard'

        for label, page_key in nav_options.items():
            if st.button(label, use_container_width=True, key=f"nav_{page_key}"):
                st.session_state.current_page = page_key
                st.rerun()

        st.markdown("---")

        # System status indicators
        st.markdown("### 📊 System Status")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Models", "3", help="Active ML models")
        with col2:
            st.metric("Tests", "1", help="Active A/B tests")

        col3, col4 = st.columns(2)
        with col3:
            st.metric("Uptime", "99.9%", help="System uptime")
        with col4:
            st.metric("Latency", "45ms", help="Avg inference latency")

        st.markdown("---")

def render_main_dashboard_page():
    """Render the main dashboard overview page."""
    st.header("🏠 Jorge's Command Center Overview")

    st.markdown("""
    Welcome to Jorge's Real Estate AI Command Center! This integrated platform
    provides comprehensive analytics and monitoring for your AI-powered real estate operations.

    ### 🚀 Available Dashboards

    **🤖 ML Intelligence Dashboard**
    - Advanced model performance monitoring
    - ROC-AUC, precision, recall analytics
    - Confidence distribution analysis
    - Real-time inference metrics

    **🧪 A/B Testing Platform**
    - Champion vs challenger model comparison
    - Statistical significance analysis
    - Performance improvement tracking
    - Automated winner selection

    **📈 Performance Analytics**
    - Model latency and throughput monitoring
    - Cache hit rate optimization
    - Resource utilization tracking
    - Historical performance trends

    **🚨 Health & Alerts**
    - Model performance degradation alerts
    - System health monitoring
    - Automated notification system
    - Performance threshold management
    """)

    # Quick metrics overview
    st.markdown("### 📊 Quick Metrics Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Average Model Performance",
            "87.3%",
            delta="2.1%",
            help="Average ROC-AUC across all models"
        )

    with col2:
        st.metric(
            "Active A/B Tests",
            "1",
            delta="0",
            help="Currently running A/B tests"
        )

    with col3:
        st.metric(
            "Total Predictions Today",
            "15,247",
            delta="12%",
            help="Number of predictions made today"
        )

    with col4:
        st.metric(
            "System Health Score",
            "98.5%",
            delta="0.3%",
            help="Overall system health score"
        )

    # Recent activity
    st.markdown("### 📋 Recent Activity")

    activity_data = [
        {
            "timestamp": "2026-01-23 14:30:00",
            "event": "A/B Test Completed",
            "details": "Lead Scoring v2.1 shows 1.3% improvement over v2.0",
            "status": "success"
        },
        {
            "timestamp": "2026-01-23 13:45:00",
            "event": "Model Deployed",
            "details": "Property Valuation v1.3 deployed to production",
            "status": "success"
        },
        {
            "timestamp": "2026-01-23 12:15:00",
            "event": "Performance Alert",
            "details": "Churn Prediction model latency increased to 85ms",
            "status": "warning"
        },
        {
            "timestamp": "2026-01-23 11:00:00",
            "event": "Cache Optimization",
            "details": "Cache hit rate improved to 83.4%",
            "status": "info"
        }
    ]

    for activity in activity_data:
        status_colors = {
            "success": "🟢",
            "warning": "🟡",
            "error": "🔴",
            "info": "🔵"
        }

        st.markdown(f"""
        **{status_colors[activity['status']]} {activity['event']}**
        *{activity['timestamp']}*
        {activity['details']}
        """)

def render_ml_dashboard_main():
    """Render the main ML dashboard with all components."""
    # Apply custom styling
    apply_ml_dashboard_styles()

    # Render filters in sidebar
    filters = render_ml_dashboard_filters()

    # Render main content based on current page
    current_page = st.session_state.get('current_page', 'ml_dashboard')

    if current_page == 'main':
        render_main_dashboard_page()

    elif current_page == 'ml_dashboard':
        # Render header
        render_dashboard_header()

        # Create tabs for different ML dashboard sections
        tab1, tab2 = st.tabs(["📊 Model Overview", "📈 Performance Charts"])

        with tab1:
            render_model_performance_overview()

        with tab2:
            render_performance_visualizations()

    elif current_page == 'ab_testing':
        st.header("🧪 A/B Testing Dashboard")
        render_ab_testing_dashboard()

    elif current_page == 'inference':
        st.header("⚡ Inference Performance Monitoring")
        render_inference_performance_dashboard()

    elif current_page == 'health':
        st.header("🚨 Model Health & Alerts")
        render_model_health_alerts()

    else:
        st.header("🚧 Dashboard Section")
        st.info(f"The {current_page} dashboard section is under development.")

def render_footer():
    """Render dashboard footer with status and controls."""
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if st.button("🔄 Refresh All Data", help="Refresh all dashboard data"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.rerun()

    with col2:
        st.write("🟢 **Status:** All Systems Operational")

    with col3:
        st.write(f"⏰ **Updated:** {datetime.now().strftime('%H:%M:%S')}")

    with col4:
        st.write("🤖 **Version:** ML Dashboard v1.0")

    with col5:
        # Auto-refresh toggle
        auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", help="Automatically refresh every 30 seconds")

        if auto_refresh:
            # Implement auto-refresh using st.empty() and time.sleep in a thread
            # Note: In production, this would use WebSocket connections
            st.info("⚠️ Auto-refresh is simulated in demo mode")

def simulate_real_time_updates():
    """Simulate real-time updates via WebSocket (demo implementation)."""
    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now()

    # Simulate periodic updates every 30 seconds
    current_time = datetime.now()
    time_diff = (current_time - st.session_state.last_update).seconds

    if time_diff >= 30:
        st.session_state.last_update = current_time
        st.toast("🔄 Dashboard data refreshed", icon="🔄")
        st.cache_data.clear()

def main():
    """Main application entry point."""
    try:
        # Simulate real-time updates
        simulate_real_time_updates()

        # Check authentication if available
        user = None
        if AUTH_AVAILABLE:
            user = check_authentication()

            if not user:
                # Show login form
                st.markdown("""
                <div style="text-align: center; padding: 2rem;">
                    <h1>🤖 Jorge's ML Intelligence Dashboard</h1>
                    <p style="font-size: 1.2rem; color: #6b7280; margin-bottom: 3rem;">
                        Advanced machine learning analytics platform
                    </p>
                </div>
                """, unsafe_allow_html=True)

                render_login_form()
                return

            # Render user menu
            render_user_menu(user)

            # Check ML dashboard access permission
            if not require_permission(user, 'ml_dashboard', 'read'):
                st.error("🚫 You don't have permission to access the ML dashboard.")
                st.stop()

        # Render navigation sidebar
        render_navigation_sidebar()

        # Show welcome message
        if user and AUTH_AVAILABLE:
            st.success(f"Welcome to Jorge's ML Intelligence Dashboard, {user.username}! 🚀")
        else:
            st.info("🚀 Running Jorge's ML Intelligence Dashboard in demo mode")

        # Render main dashboard content
        render_ml_dashboard_main()

        # Render footer
        render_footer()

    except Exception as e:
        st.error(f"🚨 Dashboard error: {str(e)}")

        # Debug information in development
        if st.checkbox("🔍 Show Debug Info"):
            st.exception(e)

        if st.button("🔄 Force Refresh"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.rerun()

if __name__ == "__main__":
    main()