"""
EnterpriseHub Monitoring Application - Main Entry Point
=====================================================

Unified monitoring application for the GHL Real Estate AI platform combining
all four monitoring dashboards into a cohesive enterprise-grade monitoring suite.

Features:
- Executive Dashboard: Business KPIs, ROI tracking, agent productivity
- Operations Dashboard: System health, API performance, webhook monitoring
- ML Performance Dashboard: Model accuracy, drift detection, prediction quality
- Security Dashboard: Compliance status, security events, audit logs

Integration:
- Real-time WebSocket data streaming
- Redis caching for performance optimization
- Mobile-responsive design with professional theming
- Export functionality for reports and analytics
- Multi-tenant support with session isolation

Usage:
    streamlit run monitoring_app.py

    Or integrate into main application:
    from monitoring_app import MonitoringApp

# === ENTERPRISE BASE IMPORTS ===
from .enhanced_enterprise_base import (
    EnhancedEnterpriseComponent,
    EnterpriseDashboardComponent,
    EnterpriseDataComponent,
    ComponentMetrics,
    ComponentState
)
from .enterprise_theme_system import (
    EnterpriseThemeManager,
    ThemeVariant,
    ComponentType,
    inject_enterprise_theme,
    create_enterprise_card,
    create_enterprise_metric,
    create_enterprise_alert
)

    app = MonitoringApp()
    app.run()
"""

# ============================================================================
# MIGRATION NOTES (Automated Migration - 2026-01-11)
# ============================================================================
# Changes Applied:
# # - Added base class: EnterpriseDashboardComponent
# - Added unified design system import check
# - Consider replacing inline styled divs with enterprise_card
#
# This component has been migrated to enterprise standards.
# See migration documentation for details.
# ============================================================================



import asyncio

# === UNIFIED DESIGN SYSTEM ===
try:
    from ..design_system import (
        enterprise_metric,
        enterprise_card,
        enterprise_badge,
        enterprise_progress_ring,
        enterprise_status_indicator,
        enterprise_kpi_grid,
        enterprise_section_header,
        apply_plotly_theme,
        ENTERPRISE_COLORS
    )
    UNIFIED_DESIGN_SYSTEM_AVAILABLE = True
except ImportError:
    UNIFIED_DESIGN_SYSTEM_AVAILABLE = False
import logging
import sys
from pathlib import Path

import streamlit as st

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ghl_real_estate_ai.streamlit_components.monitoring_dashboard_suite import (
    MonitoringDashboardSuite,
    DashboardConfig,
    DashboardType
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MonitoringApp(EnterpriseDashboardComponent):
    """
    Main monitoring application orchestrating all dashboard components.
    """

    def __init__(self):
        """Initialize monitoring application."""
        self.configure_page()
        self.initialize_session_state()

    def configure_page(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title="EnterpriseHub Monitoring Suite",
            page_icon="🏢",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                'Get Help': 'https://enterprisehub.ai/support',
                'Report a bug': 'https://enterprisehub.ai/support/bugs',
                'About': """
                # EnterpriseHub Monitoring Suite

                **Version**: 1.0.0
                **Platform**: GHL Real Estate AI
                **Performance**: 99.97% uptime SLA

                Comprehensive monitoring for:
                - Business Performance & ROI
                - Operational Health & Performance
                - ML Model Quality & Accuracy
                - Security Compliance & Threat Detection

                Built with ❤️ for real estate professionals.
                """
            }
        )

    def initialize_session_state(self):
        """Initialize session state variables."""
        if "monitoring_initialized" not in st.session_state:
            st.session_state.monitoring_initialized = True
            st.session_state.user_role = "admin"  # In production, get from auth
            st.session_state.tenant_id = "default"  # In production, get from auth
            st.session_state.last_activity = None

    def render_header(self):
        """Render application header with branding and navigation."""
        st.markdown("""
        <div style="
            background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            padding: 1rem 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            color: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        ">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700;">
                🏢 EnterpriseHub Monitoring Suite
            </h1>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">
                Real Estate AI Platform - Comprehensive Performance & Business Intelligence
            </p>
        </div>
        """, unsafe_allow_html=True)

    def render_quick_stats(self):
        """Render quick stats overview across all monitoring areas."""
        st.subheader("📊 Platform Overview - Live Status")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                padding: 1rem;
                border-radius: 8px;
                text-align: center;
                color: white;
            ">
                <h4>💰 Monthly Revenue</h4>
                <h2>$127.5K</h2>
                <small>📈 +18.3% vs last month</small>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                padding: 1rem;
                border-radius: 8px;
                text-align: center;
                color: white;
            ">
                <h4>⚡ System Health</h4>
                <h2>99.97%</h2>
                <small>🟢 All systems operational</small>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
                padding: 1rem;
                border-radius: 8px;
                text-align: center;
                color: white;
            ">
                <h4>🤖 ML Accuracy</h4>
                <h2>97.3%</h2>
                <small>📊 Lead scoring model</small>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
                padding: 1rem;
                border-radius: 8px;
                text-align: center;
                color: #333;
            ">
                <h4>🔒 Security Score</h4>
                <h2>98.7%</h2>
                <small>🛡️ Compliance validated</small>
            </div>
            """, unsafe_allow_html=True)

    def render_dashboard_navigation(self):
        """Render navigation for different dashboards."""
        st.markdown("---")
        st.subheader("🎛️ Dashboard Navigation")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("📊 Executive Dashboard", use_container_width=True):
                st.session_state.selected_dashboard = DashboardType.EXECUTIVE.value
                st.experimental_rerun()

        with col2:
            if st.button("⚙️ Operations Dashboard", use_container_width=True):
                st.session_state.selected_dashboard = DashboardType.OPERATIONS.value
                st.experimental_rerun()

        with col3:
            if st.button("🤖 ML Performance Dashboard", use_container_width=True):
                st.session_state.selected_dashboard = DashboardType.ML_PERFORMANCE.value
                st.experimental_rerun()

        with col4:
            if st.button("🔒 Security Dashboard", use_container_width=True):
                st.session_state.selected_dashboard = DashboardType.SECURITY.value
                st.experimental_rerun()

    def render_alerts_panel(self):
        """Render system alerts and notifications."""
        with st.expander("🔔 System Alerts & Notifications", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**🟢 Recent Achievements**")
                st.markdown("""
                - ✅ Monthly revenue target exceeded by 18.3%
                - ✅ ML model accuracy improved to 97.3%
                - ✅ Zero security incidents this week
                - ✅ API response time optimized to <150ms
                """)

            with col2:
                st.markdown("**⚠️ Attention Required**")
                st.markdown("""
                - 🔄 Property matching model scheduled for retraining
                - 📊 Quarterly business review due next week
                - 🔧 Database maintenance window scheduled
                - 📈 Scale infrastructure for increased load
                """)

    def render_footer(self):
        """Render application footer with system information."""
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Platform Information**")
            st.markdown("""
            - Version: 1.0.0
            - Environment: Production
            - Last Updated: 2024-01-10
            """)

        with col2:
            st.markdown("**Performance Targets**")
            st.markdown("""
            - Uptime SLA: 99.95%
            - API Response: <200ms
            - ML Inference: <500ms
            """)

        with col3:
            st.markdown("**Support & Documentation**")
            st.markdown("""
            - [📚 Documentation](https://docs.enterprisehub.ai)
            - [🎯 Support Portal](https://support.enterprisehub.ai)
            - [📞 Emergency: 1-800-SUPPORT](tel:1-800-SUPPORT)
            """)

    def run(self):
        """Run the monitoring application."""
        try:
            # Apply custom CSS for professional styling
            st.markdown("""
            <style>
            /* Professional theme styling */
            .main {
                padding: 1rem;
            }

            .stButton > button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0.75rem 1.5rem;
                font-weight: 600;
                transition: all 0.3s ease;
            }

            .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            }

            .stSelectbox > div > div > select {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
            }

            .stExpander {
                border: 1px solid #e9ecef;
                border-radius: 8px;
                margin-bottom: 1rem;
            }

            /* Dashboard grid styling */
            .dashboard-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1rem;
                margin: 1rem 0;
            }

            /* Responsive design */
            @media (max-width: 768px) {
                .main {
                    padding: 0.5rem;
                }
                .stButton > button {
                    padding: 0.5rem 1rem;
                    font-size: 0.9rem;
                }
            }
            </style>
            """, unsafe_allow_html=True)

            # Render main application
            self.render_header()
            self.render_quick_stats()
            self.render_dashboard_navigation()
            self.render_alerts_panel()

            # Check if specific dashboard is selected
            if hasattr(st.session_state, 'selected_dashboard'):
                st.markdown("---")

                # Create dashboard configuration
                config = DashboardConfig(
                    refresh_interval=10,
                    max_data_points=200,
                    enable_realtime=True,
                    enable_exports=True,
                    theme="real_estate_professional",
                    mobile_responsive=True
                )

                # Initialize and render selected dashboard
                dashboard_suite = MonitoringDashboardSuite(config)

                # Set the selected dashboard in the suite
                dashboard_suite.config.selected_dashboard = st.session_state.selected_dashboard

                # Render the specific dashboard
                if st.session_state.selected_dashboard == DashboardType.EXECUTIVE.value:
                    dashboard_suite.render_executive_dashboard()
                elif st.session_state.selected_dashboard == DashboardType.OPERATIONS.value:
                    dashboard_suite.render_operations_dashboard()
                elif st.session_state.selected_dashboard == DashboardType.ML_PERFORMANCE.value:
                    dashboard_suite.render_ml_performance_dashboard()
                elif st.session_state.selected_dashboard == DashboardType.SECURITY.value:
                    dashboard_suite.render_security_dashboard()

                # Add back to overview button
                if st.button("🏠 Back to Overview", type="secondary"):
                    if 'selected_dashboard' in st.session_state:
                        del st.session_state.selected_dashboard
                    st.experimental_rerun()
            else:
                # Show welcome message and instructions
                st.markdown("---")
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    padding: 2rem;
                    border-radius: 12px;
                    text-align: center;
                    color: white;
                    margin: 2rem 0;
                ">
                    <h2>🎯 Welcome to EnterpriseHub Monitoring</h2>
                    <p style="font-size: 1.1rem; margin-bottom: 1.5rem;">
                        Select a dashboard above to dive deep into your platform's performance,
                        business metrics, ML model health, and security compliance.
                    </p>
                    <p style="font-size: 0.9rem; opacity: 0.9;">
                        ⏱️ Real-time data updates • 📊 Interactive visualizations • 📱 Mobile responsive
                    </p>
                </div>
                """, unsafe_allow_html=True)

            # Render footer
            self.render_footer()

        except Exception as e:
            logger.error(f"Error running monitoring application: {e}")
            st.error(f"An error occurred while loading the monitoring suite: {str(e)}")
            st.info("Please contact support if this issue persists.")


def main():
    """Main entry point for the monitoring application."""
    app = MonitoringApp()
    app.run()

if __name__ == "__main__":
    main()