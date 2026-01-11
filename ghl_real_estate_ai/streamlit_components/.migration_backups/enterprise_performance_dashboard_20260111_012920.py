"""
Enterprise Design System Performance Dashboard
Real-time monitoring dashboard for enterprise UI component performance.

Provides comprehensive analytics, performance metrics, and optimization
insights for the enterprise design system.

Created: January 10, 2026
Author: EnterpriseHub Design Team
"""

# ============================================================================
# MIGRATION NOTES (Automated Migration - 2026-01-11)
# ============================================================================
# Changes Applied:
# # - Added base class: EnterpriseDashboardComponent
#
# This component has been migrated to enterprise standards.
# See migration documentation for details.
# ============================================================================



import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import asyncio
import json

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


# === UNIFIED ENTERPRISE THEME INTEGRATION ===
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
    from ..design_system.performance_monitor import (
        performance_monitor,
        ComponentMetrics,
        track_usage
    )
    UNIFIED_ENTERPRISE_THEME_AVAILABLE = True
except ImportError:
    UNIFIED_ENTERPRISE_THEME_AVAILABLE = False


class EnterprisePerformanceDashboard(EnterpriseDashboardComponent):
    """
    Comprehensive performance dashboard for enterprise design system monitoring.
    Provides real-time insights into component usage, performance, and optimization opportunities.
    """

    def __init__(self):
        """Initialize the performance dashboard."""
        self.refresh_interval = 30  # seconds
        self.auto_refresh = True

    def render_main_dashboard(self) -> None:
        """Render the main performance monitoring dashboard."""
        # Track dashboard usage
        if UNIFIED_ENTERPRISE_THEME_AVAILABLE:
            track_usage("enterprise_performance_dashboard", st.session_state.get("session_id", "default"))

        # Dashboard header
        st.title("🚀 Enterprise Design System Performance")
        st.markdown("**Real-time monitoring and analytics for enterprise UI components**")

        # Auto-refresh control
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown("### Performance Overview")
        with col2:
            auto_refresh = st.checkbox("Auto Refresh", value=self.auto_refresh)
        with col3:
            if st.button("🔄 Refresh Now"):
                st.rerun()

        # Get performance summary
        if UNIFIED_ENTERPRISE_THEME_AVAILABLE:
            summary = performance_monitor.get_performance_summary()
            self._render_overview_metrics(summary)
            self._render_component_performance(summary)
            self._render_theme_adoption(summary)
            self._render_alerts_and_recommendations(summary)
        else:
            st.warning("⚠️ Enterprise performance monitoring requires the unified theme system")
            self._render_fallback_dashboard()

        # Auto-refresh logic
        if auto_refresh:
            import time
            time.sleep(self.refresh_interval)
            st.rerun()

    def _render_overview_metrics(self, summary: dict) -> None:
        """Render overview performance metrics."""
        st.markdown("---")
        enterprise_section_header("📊 System Performance Overview", level="h3")

        overview = summary.get("overview", {})

        if UNIFIED_ENTERPRISE_THEME_AVAILABLE:
            overview_metrics = [
                {
                    "label": "Total Component Renders",
                    "value": f"{overview.get('total_renders', 0):,}",
                    "icon": "🔄",
                    "delta_type": "positive"
                },
                {
                    "label": "Overall Success Rate",
                    "value": f"{overview.get('overall_success_rate', 100):.1f}%",
                    "icon": "✅",
                    "delta_type": "positive" if overview.get('overall_success_rate', 100) >= 99 else "negative"
                },
                {
                    "label": "Components Monitored",
                    "value": str(overview.get('components_monitored', 0)),
                    "icon": "🧩",
                    "delta_type": "neutral"
                },
                {
                    "label": "Performance Score",
                    "value": f"{summary.get('performance_score', 100):.1f}/100",
                    "icon": "📈",
                    "delta_type": "positive" if summary.get('performance_score', 100) >= 85 else "negative"
                },
                {
                    "label": "Unified Theme Adoption",
                    "value": f"{overview.get('unified_theme_adoption', 100):.1f}%",
                    "icon": "🎨",
                    "delta_type": "positive" if overview.get('unified_theme_adoption', 100) >= 90 else "negative"
                },
                {
                    "label": "System Errors",
                    "value": str(overview.get('total_errors', 0)),
                    "icon": "⚠️",
                    "delta_type": "negative" if overview.get('total_errors', 0) > 0 else "positive"
                }
            ]
            enterprise_kpi_grid(overview_metrics, columns=3)
        else:
            # Legacy fallback
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Renders", f"{overview.get('total_renders', 0):,}")
                st.metric("Success Rate", f"{overview.get('overall_success_rate', 100):.1f}%")
            with col2:
                st.metric("Components", str(overview.get('components_monitored', 0)))
                st.metric("Performance Score", f"{summary.get('performance_score', 100):.1f}/100")
            with col3:
                st.metric("Theme Adoption", f"{overview.get('unified_theme_adoption', 100):.1f}%")
                st.metric("Errors", str(overview.get('total_errors', 0)))

    def _render_component_performance(self, summary: dict) -> None:
        """Render individual component performance metrics."""
        st.markdown("---")
        enterprise_section_header("🧩 Component Performance Analysis", level="h3")

        most_used = summary.get("most_used_components", [])
        if not most_used:
            st.info("No component performance data available yet.")
            return

        # Create performance chart
        df_performance = pd.DataFrame(most_used)

        # Performance comparison chart
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Render Count by Component")
            fig_renders = px.bar(
                df_performance,
                x='name',
                y='renders',
                title="Component Usage (Total Renders)",
                labels={'name': 'Component', 'renders': 'Render Count'}
            )
            fig_renders.update_xaxes(tickangle=45)

            if UNIFIED_ENTERPRISE_THEME_AVAILABLE:
                apply_plotly_theme(fig_renders)

            st.plotly_chart(fig_renders, use_container_width=True)

        with col2:
            st.markdown("#### Average Render Time")
            fig_time = px.bar(
                df_performance,
                x='name',
                y='avg_render_time',
                title="Component Performance (Render Time)",
                labels={'name': 'Component', 'avg_render_time': 'Avg Render Time (ms)'},
                color='avg_render_time',
                color_continuous_scale='RdYlGn_r'
            )
            fig_time.update_xaxes(tickangle=45)
            fig_time.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="100ms Target")

            if UNIFIED_ENTERPRISE_THEME_AVAILABLE:
                apply_plotly_theme(fig_time)

            st.plotly_chart(fig_time, use_container_width=True)

        # Detailed component metrics table
        st.markdown("#### Detailed Component Metrics")
        df_display = df_performance.copy()
        df_display.columns = ['Component', 'Render Count', 'Avg Render Time (ms)', 'Success Rate (%)']
        st.dataframe(df_display, use_container_width=True)

    def _render_theme_adoption(self, summary: dict) -> None:
        """Render theme adoption analytics."""
        st.markdown("---")
        enterprise_section_header("🎨 Theme Adoption Analysis", level="h3")

        theme_adoption = summary.get("theme_adoption", {})
        if not theme_adoption:
            st.info("No theme adoption data available yet.")
            return

        # Theme adoption pie chart
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Theme Mode Distribution")
            theme_data = list(theme_adoption.items())
            if theme_data:
                labels, values = zip(*theme_data)
                fig_theme = px.pie(
                    values=values,
                    names=labels,
                    title="Theme Mode Usage Distribution"
                )

                if UNIFIED_ENTERPRISE_THEME_AVAILABLE:
                    apply_plotly_theme(fig_theme)

                st.plotly_chart(fig_theme, use_container_width=True)

        with col2:
            st.markdown("#### Theme Adoption Insights")

            unified_percentage = theme_adoption.get("unified", 0)
            legacy_percentage = theme_adoption.get("legacy", 0)
            fallback_percentage = theme_adoption.get("fallback", 0)

            if unified_percentage >= 90:
                st.success(f"✅ Excellent unified theme adoption: {unified_percentage:.1f}%")
            elif unified_percentage >= 70:
                st.warning(f"⚠️ Good unified theme adoption: {unified_percentage:.1f}%")
            else:
                st.error(f"❌ Low unified theme adoption: {unified_percentage:.1f}%")

            st.markdown("**Recommendations:**")
            if legacy_percentage > 20:
                st.markdown("- Consider migrating legacy components to unified theme")
            if fallback_percentage > 10:
                st.markdown("- Investigate fallback usage - may indicate import issues")
            if unified_percentage < 80:
                st.markdown("- Focus on increasing unified theme adoption for better consistency")

    def _render_alerts_and_recommendations(self, summary: dict) -> None:
        """Render performance alerts and optimization recommendations."""
        st.markdown("---")
        enterprise_section_header("🚨 Alerts & Recommendations", level="h3")

        recent_alerts = summary.get("recent_alerts", [])

        if not recent_alerts:
            st.success("🎉 No performance alerts - all systems operating optimally!")
        else:
            st.markdown("#### Recent Performance Alerts")

            for alert in recent_alerts[-5:]:  # Show last 5 alerts
                severity = alert.get("severity", "info")
                if severity == "critical":
                    st.error(f"🔴 **{alert['component']}**: {alert['message']}")
                elif severity == "warning":
                    st.warning(f"🟡 **{alert['component']}**: {alert['message']}")
                else:
                    st.info(f"🔵 **{alert['component']}**: {alert['message']}")

        # Performance recommendations
        st.markdown("#### Optimization Recommendations")

        performance_score = summary.get("performance_score", 100)
        overview = summary.get("overview", {})

        recommendations = []

        if performance_score < 85:
            recommendations.append("📈 Consider optimizing slow-rendering components")
        if overview.get("overall_success_rate", 100) < 99:
            recommendations.append("🛠️ Investigate and fix component rendering errors")
        if overview.get("unified_theme_adoption", 100) < 90:
            recommendations.append("🎨 Migrate remaining components to unified theme")

        # Add component-specific recommendations
        most_used = summary.get("most_used_components", [])
        for component in most_used:
            if component.get("avg_render_time", 0) > 100:
                recommendations.append(f"⚡ Optimize {component['name']} - render time: {component['avg_render_time']:.1f}ms")

        if recommendations:
            for rec in recommendations:
                st.markdown(f"- {rec}")
        else:
            st.success("✅ All components performing optimally - no recommendations at this time")

        # Export options
        st.markdown("---")
        enterprise_section_header("📤 Export Performance Data", level="h4")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📄 Export JSON"):
                if UNIFIED_ENTERPRISE_THEME_AVAILABLE:
                    json_data = performance_monitor.export_metrics("json")
                    st.download_button(
                        label="Download JSON Report",
                        data=json_data,
                        file_name=f"enterprise_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )

        with col2:
            if st.button("📊 Export CSV"):
                if UNIFIED_ENTERPRISE_THEME_AVAILABLE:
                    csv_data = performance_monitor.export_metrics("csv")
                    st.download_button(
                        label="Download CSV Report",
                        data=csv_data,
                        file_name=f"enterprise_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )

        with col3:
            if st.button("🧹 Clean Old Data"):
                if UNIFIED_ENTERPRISE_THEME_AVAILABLE:
                    asyncio.run(performance_monitor.cleanup_old_data())
                    st.success("✅ Cleaned up old monitoring data")

    def _render_fallback_dashboard(self) -> None:
        """Render fallback dashboard when monitoring is not available."""
        st.info("🏗️ Performance monitoring is not available in this environment")

        st.markdown("### Mock Performance Data")

        # Mock metrics for demonstration
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Components", "12")
            st.metric("Success Rate", "99.2%")
        with col2:
            st.metric("Avg Render Time", "45ms")
            st.metric("Theme Adoption", "94.3%")
        with col3:
            st.metric("Performance Score", "92.1/100")
            st.metric("Total Renders", "15,847")

        st.markdown("""
        **To enable full performance monitoring:**
        1. Ensure the unified enterprise theme is properly imported
        2. Components should be wrapped with performance tracking
        3. Enable monitoring in your Streamlit configuration
        """)


# Create global dashboard instance
enterprise_performance_dashboard = EnterprisePerformanceDashboard()


def render_performance_dashboard():
    """Render the enterprise performance monitoring dashboard."""
    st.set_page_config(
        page_title="Enterprise Performance Dashboard",
        page_icon="🚀",
        layout="wide"
    )

    enterprise_performance_dashboard.render_main_dashboard()


if __name__ == "__main__":
    render_performance_dashboard()