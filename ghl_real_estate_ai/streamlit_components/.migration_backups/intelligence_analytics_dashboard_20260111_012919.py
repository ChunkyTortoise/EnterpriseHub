"""
Intelligence Analytics Dashboard
Real-time performance monitoring and business intelligence visualization.

This module provides comprehensive analytics dashboard for monitoring
the performance, usage, and business impact of the intelligence system.

Features:
- Real-time performance metrics visualization
- Business intelligence analytics and ROI tracking
- Component health monitoring
- User behavior analysis
- Claude AI service performance tracking
- Automated alerts and recommendations
- Exportable analytics reports

Created: January 10, 2026
Author: EnterpriseHub Development Team
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



import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

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
    UNIFIED_ENTERPRISE_THEME_AVAILABLE = True
except ImportError:
    UNIFIED_ENTERPRISE_THEME_AVAILABLE = False

from ..services.intelligence_performance_monitor import (
    IntelligencePerformanceMonitor,
    performance_monitor,
    track_interaction,
    track_performance
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntelligenceAnalyticsDashboard(EnterpriseDashboardComponent):
    """
    Comprehensive analytics dashboard for intelligence system monitoring.
    Provides real-time insights into performance, usage, and business impact.
    """

    def __init__(self):
        """Initialize the analytics dashboard."""
        self.monitor = performance_monitor
        self.refresh_interval = 30  # seconds

    @track_performance("analytics_dashboard", "initialize")
    async def initialize(self) -> None:
        """Initialize the performance monitor and dashboard state."""
        try:
            await self.monitor.initialize()

            # Initialize session state
            if 'analytics_initialized' not in st.session_state:
                st.session_state.analytics_initialized = True
                st.session_state.analytics_filters = {
                    'time_range': '24h',
                    'component_filter': 'all',
                    'metric_type': 'performance'
                }
                st.session_state.auto_refresh = True

            logger.info("Analytics dashboard initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize analytics dashboard: {e}")
            st.error(f"Failed to initialize analytics: {e}")

    @track_interaction("analytics_dashboard")
    def render_main_dashboard(self) -> None:
        """Render the main analytics dashboard."""
        st.title("🔍 Intelligence Analytics Dashboard")
        st.markdown("**Real-time performance monitoring and business intelligence**")

        # Initialize if needed
        if not st.session_state.get('analytics_initialized'):
            asyncio.run(self.initialize())

        # Dashboard controls
        self._render_dashboard_controls()

        # Main dashboard content
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.subheader("📊 System Overview")
            asyncio.run(self._render_system_overview())

        with col2:
            st.subheader("⚡ Performance Metrics")
            asyncio.run(self._render_performance_metrics())

        with col3:
            st.subheader("🚨 Alerts")
            asyncio.run(self._render_alerts_panel())

        # Detailed analytics sections
        st.markdown("---")

        # Business Intelligence section
        st.subheader("💼 Business Intelligence")
        asyncio.run(self._render_business_intelligence())

        st.markdown("---")

        # Component Performance section
        st.subheader("🧩 Component Performance")
        asyncio.run(self._render_component_performance())

        st.markdown("---")

        # Claude AI Services section
        st.subheader("🤖 Claude AI Services")
        asyncio.run(self._render_claude_services_performance())

        st.markdown("---")

        # User Analytics section
        st.subheader("👥 User Analytics")
        asyncio.run(self._render_user_analytics())

        # Auto-refresh
        if st.session_state.get('auto_refresh', False):
            time.sleep(self.refresh_interval)
            st.rerun()

    def _render_dashboard_controls(self) -> None:
        """Render dashboard control panel."""
        st.markdown("### Dashboard Controls")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            time_range = st.selectbox(
                "Time Range",
                options=["1h", "6h", "24h", "7d", "30d"],
                index=2,  # Default to 24h
                key="analytics_time_range"
            )
            st.session_state.analytics_filters['time_range'] = time_range

        with col2:
            component_filter = st.selectbox(
                "Component",
                options=["all", "journey_map", "sentiment_dashboard",
                        "competitive_intel", "content_engine"],
                index=0,
                key="analytics_component"
            )
            st.session_state.analytics_filters['component_filter'] = component_filter

        with col3:
            metric_type = st.selectbox(
                "Metric Type",
                options=["performance", "business", "user_behavior"],
                index=0,
                key="analytics_metric_type"
            )
            st.session_state.analytics_filters['metric_type'] = metric_type

        with col4:
            st.session_state.auto_refresh = st.checkbox(
                "Auto Refresh",
                value=st.session_state.get('auto_refresh', True),
                key="analytics_auto_refresh"
            )

        # Export controls
        col1, col2, col3 = st.columns([2, 1, 1])

        with col2:
            if st.button("📄 Export Report", key="export_analytics"):
                asyncio.run(self._export_analytics_report())

        with col3:
            if st.button("🔄 Refresh Now", key="manual_refresh"):
                st.rerun()

    async def _render_system_overview(self) -> None:
        """Render system health overview."""
        try:
            health_metrics = await self.monitor.get_dashboard_health()

            # Health metrics cards with unified enterprise design
            if UNIFIED_ENTERPRISE_THEME_AVAILABLE:
                health_metrics_data = [
                    {
                        "label": "System Uptime",
                        "value": f"{health_metrics.uptime_percentage:.1f}%",
                        "icon": "⏱️",
                        "delta_type": "positive" if health_metrics.uptime_percentage > 99.5 else "neutral"
                    },
                    {
                        "label": "Active Users (24h)",
                        "value": str(health_metrics.active_users_24h),
                        "icon": "👥",
                        "delta_type": "positive"
                    },
                    {
                        "label": "Sessions Today",
                        "value": str(health_metrics.total_sessions_today),
                        "icon": "📊",
                        "delta_type": "positive"
                    }
                ]
                enterprise_kpi_grid(health_metrics_data, columns=3)
            else:
                # Legacy fallback
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "System Uptime",
                        f"{health_metrics.uptime_percentage:.1f}%",
                        delta=None
                    )

                with col2:
                    st.metric(
                        "Active Users (24h)",
                        health_metrics.active_users_24h,
                        delta=None
                    )

                with col3:
                    st.metric(
                        "Sessions Today",
                        health_metrics.total_sessions_today,
                        delta=None
                    )

            # Health status indicators
            col1, col2, col3 = st.columns(3)

            with col1:
                avg_load_time = health_metrics.avg_page_load_time
                color = "green" if avg_load_time < 2.0 else "orange" if avg_load_time < 5.0 else "red"
                st.markdown(f"**Page Load:** :{color}[{avg_load_time:.1f}s]")

            with col2:
                data_freshness = health_metrics.data_freshness_score
                color = "green" if data_freshness > 90 else "orange" if data_freshness > 70 else "red"
                st.markdown(f"**Data Freshness:** :{color}[{data_freshness:.0f}%]")

            with col3:
                redis_status = health_metrics.redis_health
                color = "green" if redis_status else "red"
                status_text = "Connected" if redis_status else "Disconnected"
                st.markdown(f"**Redis:** :{color}[{status_text}]")

        except Exception as e:
            st.error(f"Failed to load system overview: {e}")

    async def _render_performance_metrics(self) -> None:
        """Render performance metrics charts."""
        try:
            # Get component performance data
            components = ["journey_map", "sentiment_dashboard", "competitive_intel", "content_engine"]
            performance_data = []

            for component in components:
                perf = await self.monitor.get_component_performance(component, 24)
                performance_data.append({
                    'Component': component.replace('_', ' ').title(),
                    'Avg Response Time (ms)': perf.avg_render_time,
                    'Error Rate (%)': perf.error_rate * 100,
                    'Performance Score': perf.performance_score
                })

            df = pd.DataFrame(performance_data)

            # Response time chart with enterprise theming
            fig_response = px.bar(
                df,
                x='Component',
                y='Avg Response Time (ms)',
                title="Average Response Times",
                color='Avg Response Time (ms)',
                color_continuous_scale='RdYlGn_r'
            )
            fig_response.add_hline(y=500, line_dash="dash", line_color="red",
                                 annotation_text="500ms Threshold")

            # Apply enterprise theme
            if UNIFIED_ENTERPRISE_THEME_AVAILABLE:
                apply_plotly_theme(fig_response)

            st.plotly_chart(fig_response, use_container_width=True)

            # Performance score gauge
            avg_score = df['Performance Score'].mean()
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=avg_score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Overall Performance Score"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "red"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig_gauge.update_layout(height=300)

            # Apply enterprise theme
            if UNIFIED_ENTERPRISE_THEME_AVAILABLE:
                apply_plotly_theme(fig_gauge)

            st.plotly_chart(fig_gauge, use_container_width=True)

        except Exception as e:
            st.error(f"Failed to load performance metrics: {e}")

    async def _render_alerts_panel(self) -> None:
        """Render alerts and recommendations panel."""
        try:
            recommendations = await self.monitor.get_performance_recommendations()

            if not recommendations:
                st.success("✅ All systems operating normally")
                return

            # Categorize alerts by priority
            high_priority = [r for r in recommendations if r.get('priority') == 'high']
            medium_priority = [r for r in recommendations if r.get('priority') == 'medium']
            low_priority = [r for r in recommendations if r.get('priority') == 'low']

            # High priority alerts
            if high_priority:
                st.error(f"🚨 {len(high_priority)} High Priority Issues")
                for alert in high_priority:
                    st.markdown(f"**{alert['component']}**: {alert['issue']}")

            # Medium priority alerts
            if medium_priority:
                st.warning(f"⚠️ {len(medium_priority)} Medium Priority Issues")
                for alert in medium_priority[:3]:  # Show top 3
                    st.markdown(f"**{alert['component']}**: {alert['issue']}")

            # Low priority recommendations
            if low_priority:
                st.info(f"💡 {len(low_priority)} Optimization Opportunities")

            # Show detailed recommendations in expander
            if st.button("View Detailed Recommendations"):
                self._show_detailed_recommendations(recommendations)

        except Exception as e:
            st.error(f"Failed to load alerts: {e}")

    def _show_detailed_recommendations(self, recommendations: List[Dict[str, Any]]) -> None:
        """Show detailed recommendations in modal."""
        with st.expander("Detailed Performance Recommendations", expanded=True):
            for rec in recommendations:
                priority_color = {
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(rec.get('priority', 'low'), '🟢')

                st.markdown(f"""
                {priority_color} **{rec['component']}** - {rec['issue']}
                - **Current**: {rec['current_value']}
                - **Threshold**: {rec['threshold']}
                - **Recommendation**: {rec['recommendation']}
                """)

    async def _render_business_intelligence(self) -> None:
        """Render business intelligence metrics."""
        try:
            bi_metrics = await self.monitor.get_business_intelligence()

            if not bi_metrics:
                st.info("No business intelligence data available")
                return

            # Create metrics cards with unified enterprise design
            if UNIFIED_ENTERPRISE_THEME_AVAILABLE:
                bi_metrics_data = []
                for metric in bi_metrics[:6]:  # Show top 6 metrics
                    # Format trend indicator
                    trend_icon = {
                        'up': '📈',
                        'down': '📉',
                        'stable': '➡️'
                    }.get(metric.trend_direction, '📊')

                    # Calculate delta if comparison available
                    delta = None
                    delta_type = "neutral"
                    if metric.comparison_period:
                        delta_value = metric.value - metric.comparison_period
                        if metric.trend_direction == 'down' and 'time' in metric.metric_name:
                            # For time-based metrics, down is good
                            delta = f"-{abs(delta_value):.1f}"
                            delta_type = "positive" if delta_value < 0 else "negative"
                        else:
                            delta = f"+{delta_value:.1f}" if delta_value > 0 else f"{delta_value:.1f}"
                            delta_type = "positive" if delta_value > 0 else "negative"

                    # Display metric
                    metric_name = metric.metric_name.replace('_', ' ').title()
                    unit_suffix = ""
                    if metric.unit == "percentage":
                        unit_suffix = "%"
                    elif metric.unit == "minutes":
                        unit_suffix = " min"
                    elif metric.unit == "score":
                        unit_suffix = "/100"

                    bi_metrics_data.append({
                        "label": metric_name,
                        "value": f"{metric.value:.1f}{unit_suffix}",
                        "delta": delta,
                        "delta_type": delta_type,
                        "icon": trend_icon
                    })

                enterprise_kpi_grid(bi_metrics_data, columns=3)
            else:
                # Legacy fallback
                col1, col2, col3 = st.columns(3)

                for i, metric in enumerate(bi_metrics[:6]):  # Show top 6 metrics
                    col = [col1, col2, col3][i % 3]

                    with col:
                        # Format trend indicator
                        trend_icon = {
                            'up': '📈',
                            'down': '📉',
                            'stable': '➡️'
                        }.get(metric.trend_direction, '➡️')

                        # Calculate delta if comparison available
                        delta = None
                        if metric.comparison_period:
                            if metric.trend_direction == 'down' and 'time' in metric.metric_name:
                                # For time-based metrics, down is good
                                delta = f"-{metric.value - metric.comparison_period:.1f}"
                            else:
                                delta = f"{metric.value - metric.comparison_period:.1f}"

                        # Display metric
                        metric_name = metric.metric_name.replace('_', ' ').title()
                        unit_suffix = ""
                        if metric.unit == "percentage":
                            unit_suffix = "%"
                        elif metric.unit == "minutes":
                            unit_suffix = " min"
                        elif metric.unit == "score":
                            unit_suffix = "/100"

                        st.metric(
                            f"{trend_icon} {metric_name}",
                            f"{metric.value:.1f}{unit_suffix}",
                            delta=delta
                        )

            # Business intelligence trends chart
            st.markdown("#### Business Intelligence Trends")

            # Create sample trend data for visualization
            trend_data = []
            for metric in bi_metrics:
                if metric.comparison_period:
                    trend_data.extend([
                        {
                            'Metric': metric.metric_name.replace('_', ' ').title(),
                            'Period': 'Previous',
                            'Value': metric.comparison_period
                        },
                        {
                            'Metric': metric.metric_name.replace('_', ' ').title(),
                            'Period': 'Current',
                            'Value': metric.value
                        }
                    ])

            if trend_data:
                df_trends = pd.DataFrame(trend_data)
                fig_trends = px.bar(
                    df_trends,
                    x='Metric',
                    y='Value',
                    color='Period',
                    barmode='group',
                    title="Current vs Previous Period Comparison"
                )
                fig_trends.update_xaxes(tickangle=45)

                # Apply enterprise theme
                if UNIFIED_ENTERPRISE_THEME_AVAILABLE:
                    apply_plotly_theme(fig_trends)

                st.plotly_chart(fig_trends, use_container_width=True)

        except Exception as e:
            st.error(f"Failed to load business intelligence: {e}")

    async def _render_component_performance(self) -> None:
        """Render detailed component performance analysis."""
        try:
            # Component selection
            selected_component = st.selectbox(
                "Select Component for Detailed Analysis",
                options=["journey_map", "sentiment_dashboard", "competitive_intel", "content_engine"],
                format_func=lambda x: x.replace('_', ' ').title()
            )

            # Get detailed performance data
            perf = await self.monitor.get_component_performance(selected_component, 24)

            # Performance summary cards with unified enterprise design
            if UNIFIED_ENTERPRISE_THEME_AVAILABLE:
                performance_data = [
                    {
                        "label": "Total Renders",
                        "value": str(perf.total_renders),
                        "icon": "🔄",
                        "delta_type": "positive"
                    },
                    {
                        "label": "Avg Render Time",
                        "value": f"{perf.avg_render_time:.1f}ms",
                        "delta": f"{perf.avg_render_time - 500:.1f}ms" if perf.avg_render_time > 0 else None,
                        "delta_type": "negative" if perf.avg_render_time > 500 else "positive",
                        "icon": "⏱️"
                    },
                    {
                        "label": "Error Rate",
                        "value": f"{perf.error_rate:.2%}",
                        "delta": f"{(perf.error_rate - 0.05)*100:.1f}%" if perf.error_rate > 0 else None,
                        "delta_type": "negative" if perf.error_rate > 0.05 else "positive",
                        "icon": "⚠️"
                    },
                    {
                        "label": "Performance Score",
                        "value": f"{perf.performance_score:.0f}/100",
                        "delta": f"{perf.performance_score - 85:.0f}" if perf.performance_score > 0 else None,
                        "delta_type": "positive" if perf.performance_score > 85 else "negative",
                        "icon": "📊"
                    }
                ]
                enterprise_kpi_grid(performance_data, columns=4)
            else:
                # Legacy fallback
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Total Renders", perf.total_renders)

                with col2:
                    st.metric(
                        "Avg Render Time",
                        f"{perf.avg_render_time:.1f}ms",
                        delta=f"{perf.avg_render_time - 500:.1f}ms" if perf.avg_render_time > 0 else None
                    )

                with col3:
                    st.metric(
                        "Error Rate",
                        f"{perf.error_rate:.2%}",
                        delta=f"{(perf.error_rate - 0.05)*100:.1f}%" if perf.error_rate > 0 else None
                    )

                with col4:
                    score_color = "normal"
                    if perf.performance_score > 90:
                        score_color = "inverse"
                    elif perf.performance_score < 70:
                        score_color = "off"

                    st.metric(
                        "Performance Score",
                        f"{perf.performance_score:.0f}/100",
                        delta=f"{perf.performance_score - 85:.0f}" if perf.performance_score > 0 else None
                    )

            # Performance percentiles
            st.markdown("#### Response Time Distribution")

            percentile_data = {
                'Percentile': ['Average', 'P95', 'P99'],
                'Response Time (ms)': [
                    perf.avg_render_time,
                    perf.p95_render_time,
                    perf.p99_render_time
                ]
            }

            df_percentiles = pd.DataFrame(percentile_data)
            fig_percentiles = px.bar(
                df_percentiles,
                x='Percentile',
                y='Response Time (ms)',
                title=f"{selected_component.replace('_', ' ').title()} Performance Distribution"
            )
            fig_percentiles.add_hline(y=500, line_dash="dash", line_color="red")
            st.plotly_chart(fig_percentiles, use_container_width=True)

        except Exception as e:
            st.error(f"Failed to load component performance: {e}")

    async def _render_claude_services_performance(self) -> None:
        """Render Claude AI services performance metrics."""
        try:
            # Get Claude service metrics
            services = ["claude_agent_service", "semantic_analyzer", "action_planner"]
            claude_data = []

            for service in services:
                metrics = await self.monitor.get_claude_service_metrics(service, 24)
                claude_data.append({
                    'Service': service.replace('_', ' ').title(),
                    'Avg Response (ms)': metrics.avg_response_time,
                    'Requests/Min': metrics.requests_per_minute,
                    'Success Rate (%)': metrics.success_rate * 100,
                    'Cache Hit Rate (%)': metrics.cache_hit_rate * 100,
                    'Token Usage': metrics.token_usage,
                    'Cost per Request ($)': metrics.cost_per_request
                })

            df_claude = pd.DataFrame(claude_data)

            # Claude services overview with unified enterprise design
            if UNIFIED_ENTERPRISE_THEME_AVAILABLE:
                avg_response_time = df_claude['Avg Response (ms)'].mean()
                total_requests = df_claude['Requests/Min'].sum()
                avg_success_rate = df_claude['Success Rate (%)'].mean()

                claude_overview_data = [
                    {
                        "label": "Avg Claude Response",
                        "value": f"{avg_response_time:.1f}ms",
                        "delta": f"{avg_response_time - 200:.1f}ms",
                        "delta_type": "negative" if avg_response_time > 200 else "positive",
                        "icon": "🤖"
                    },
                    {
                        "label": "Total Requests/Min",
                        "value": f"{total_requests:.0f}",
                        "icon": "📈",
                        "delta_type": "positive"
                    },
                    {
                        "label": "Overall Success Rate",
                        "value": f"{avg_success_rate:.1f}%",
                        "delta": f"{avg_success_rate - 99:.1f}%",
                        "delta_type": "positive" if avg_success_rate >= 99 else "negative",
                        "icon": "✅"
                    }
                ]
                enterprise_kpi_grid(claude_overview_data, columns=3)
            else:
                # Legacy fallback
                col1, col2, col3 = st.columns(3)

                with col1:
                    avg_response_time = df_claude['Avg Response (ms)'].mean()
                    st.metric(
                        "Avg Claude Response",
                        f"{avg_response_time:.1f}ms",
                        delta=f"{avg_response_time - 200:.1f}ms"
                    )

                with col2:
                    total_requests = df_claude['Requests/Min'].sum()
                    st.metric("Total Requests/Min", f"{total_requests:.0f}")

                with col3:
                    avg_success_rate = df_claude['Success Rate (%)'].mean()
                    st.metric(
                        "Overall Success Rate",
                        f"{avg_success_rate:.1f}%",
                        delta=f"{avg_success_rate - 99:.1f}%"
                    )

            # Claude performance charts
            col1, col2 = st.columns(2)

            with col1:
                fig_response = px.bar(
                    df_claude,
                    x='Service',
                    y='Avg Response (ms)',
                    title="Claude Service Response Times"
                )
                fig_response.add_hline(y=200, line_dash="dash", line_color="red")
                st.plotly_chart(fig_response, use_container_width=True)

            with col2:
                fig_cache = px.bar(
                    df_claude,
                    x='Service',
                    y='Cache Hit Rate (%)',
                    title="Cache Hit Rates"
                )
                fig_cache.add_hline(y=80, line_dash="dash", line_color="green")
                st.plotly_chart(fig_cache, use_container_width=True)

            # Cost analysis with unified enterprise design
            st.markdown("#### Cost Analysis")

            total_cost = df_claude['Token Usage'].sum() * df_claude['Cost per Request ($)'].mean()
            monthly_cost = total_cost * 30

            if UNIFIED_ENTERPRISE_THEME_AVAILABLE:
                cost_analysis_data = [
                    {
                        "label": "Daily Token Usage",
                        "value": f"{df_claude['Token Usage'].sum():,}",
                        "icon": "🔤",
                        "delta_type": "neutral"
                    },
                    {
                        "label": "Estimated Daily Cost",
                        "value": f"${total_cost:.2f}",
                        "icon": "💰",
                        "delta_type": "neutral"
                    },
                    {
                        "label": "Estimated Monthly Cost",
                        "value": f"${monthly_cost:.2f}",
                        "icon": "📅",
                        "delta_type": "neutral"
                    }
                ]
                enterprise_kpi_grid(cost_analysis_data, columns=3)
            else:
                # Legacy fallback
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Daily Token Usage", f"{df_claude['Token Usage'].sum():,}")

                with col2:
                    st.metric("Estimated Daily Cost", f"${total_cost:.2f}")

                with col3:
                    st.metric("Estimated Monthly Cost", f"${monthly_cost:.2f}")

        except Exception as e:
            st.error(f"Failed to load Claude services performance: {e}")

    async def _render_user_analytics(self) -> None:
        """Render user behavior analytics."""
        try:
            # Mock user analytics data for demonstration
            user_data = {
                'Component Usage': {
                    'Journey Map': 45,
                    'Sentiment Dashboard': 38,
                    'Competitive Intel': 25,
                    'Content Engine': 32
                },
                'User Engagement': {
                    'Average Session Duration': '12.5 minutes',
                    'Pages per Session': '4.2',
                    'Bounce Rate': '23%',
                    'Return User Rate': '67%'
                }
            }

            # Component usage chart
            col1, col2 = st.columns(2)

            with col1:
                fig_usage = px.pie(
                    values=list(user_data['Component Usage'].values()),
                    names=list(user_data['Component Usage'].keys()),
                    title="Component Usage Distribution"
                )
                st.plotly_chart(fig_usage, use_container_width=True)

            with col2:
                st.markdown("#### User Engagement Metrics")
                if UNIFIED_ENTERPRISE_THEME_AVAILABLE:
                    engagement_metrics_data = []
                    for metric, value in user_data['User Engagement'].items():
                        icon = "⏱️" if "Duration" in metric else "📊" if "Pages" in metric else "↩️" if "Bounce" in metric else "🔄"
                        engagement_metrics_data.append({
                            "label": metric,
                            "value": value,
                            "icon": icon,
                            "delta_type": "positive"
                        })

                    # Use single column layout for these specific metrics
                    for metric_data in engagement_metrics_data:
                        enterprise_metric(
                            metric_data["label"],
                            metric_data["value"],
                            icon=metric_data["icon"]
                        )
                else:
                    # Legacy fallback
                    for metric, value in user_data['User Engagement'].items():
                        st.metric(metric, value)

            # User behavior trends (mock data)
            st.markdown("#### User Activity Trends")

            # Generate sample trend data
            dates = pd.date_range(
                start=datetime.now() - timedelta(days=7),
                end=datetime.now(),
                freq='D'
            )

            trend_data = pd.DataFrame({
                'Date': dates,
                'Active Users': [45, 52, 48, 61, 58, 65, 72],
                'Sessions': [120, 145, 132, 168, 155, 178, 195],
                'Page Views': [480, 580, 528, 672, 620, 712, 780]
            })

            fig_trends = make_subplots(
                rows=3, cols=1,
                subplot_titles=('Active Users', 'Sessions', 'Page Views'),
                shared_xaxes=True
            )

            fig_trends.add_trace(
                go.Scatter(x=trend_data['Date'], y=trend_data['Active Users'],
                          mode='lines+markers', name='Active Users'),
                row=1, col=1
            )

            fig_trends.add_trace(
                go.Scatter(x=trend_data['Date'], y=trend_data['Sessions'],
                          mode='lines+markers', name='Sessions'),
                row=2, col=1
            )

            fig_trends.add_trace(
                go.Scatter(x=trend_data['Date'], y=trend_data['Page Views'],
                          mode='lines+markers', name='Page Views'),
                row=3, col=1
            )

            fig_trends.update_layout(height=600, showlegend=False)
            st.plotly_chart(fig_trends, use_container_width=True)

        except Exception as e:
            st.error(f"Failed to load user analytics: {e}")

    async def _export_analytics_report(self) -> None:
        """Export comprehensive analytics report."""
        try:
            st.info("Generating analytics report...")

            # Calculate date range based on filter
            time_range = st.session_state.analytics_filters.get('time_range', '24h')
            end_date = datetime.now()

            if time_range == '1h':
                start_date = end_date - timedelta(hours=1)
            elif time_range == '6h':
                start_date = end_date - timedelta(hours=6)
            elif time_range == '24h':
                start_date = end_date - timedelta(days=1)
            elif time_range == '7d':
                start_date = end_date - timedelta(days=7)
            else:  # 30d
                start_date = end_date - timedelta(days=30)

            # Generate report
            report = await self.monitor.export_analytics_report(
                start_date=start_date,
                end_date=end_date,
                format_type='json'
            )

            # Display download button
            report_json = json.dumps(report, indent=2, default=str)
            filename = f"intelligence_analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            st.download_button(
                label="📄 Download Analytics Report",
                data=report_json,
                file_name=filename,
                mime="application/json"
            )

            st.success("Analytics report generated successfully!")

        except Exception as e:
            st.error(f"Failed to export analytics report: {e}")

    @track_performance("analytics_dashboard", "render_mini_widget")
    def render_mini_performance_widget(self) -> None:
        """Render a mini performance widget for embedding in other dashboards."""
        try:
            with st.container():
                st.markdown("**⚡ System Performance**")

                # Quick health indicators
                col1, col2, col3 = st.columns(3)

                with col1:
                    # Mock real-time data
                    response_time = 145.2  # Would come from actual monitoring
                    color = "green" if response_time < 200 else "orange" if response_time < 500 else "red"
                    st.markdown(f"Response: :{color}[{response_time:.0f}ms]")

                with col2:
                    uptime = 99.8  # Would come from actual monitoring
                    color = "green" if uptime > 99.5 else "orange" if uptime > 99 else "red"
                    st.markdown(f"Uptime: :{color}[{uptime:.1f}%]")

                with col3:
                    errors = 0.02  # Would come from actual monitoring
                    color = "green" if errors < 0.05 else "orange" if errors < 0.1 else "red"
                    st.markdown(f"Errors: :{color}[{errors:.1%}]")

        except Exception as e:
            st.error(f"Performance widget error: {e}")

    def render_real_time_alerts(self) -> None:
        """Render real-time alerts component."""
        try:
            # This would show live alerts
            alerts = []  # Would come from actual monitoring

            if not alerts:
                st.success("✅ All systems operational")
            else:
                for alert in alerts:
                    st.warning(f"⚠️ {alert['message']}")

        except Exception as e:
            st.error(f"Alerts component error: {e}")


# Create global instance
analytics_dashboard = IntelligenceAnalyticsDashboard()


# Demo function for testing
def render_analytics_demo():
    """Render analytics dashboard demo."""
    st.set_page_config(
        page_title="Intelligence Analytics Dashboard",
        page_icon="📊",
        layout="wide"
    )

    analytics_dashboard.render_main_dashboard()


if __name__ == "__main__":
    render_analytics_demo()