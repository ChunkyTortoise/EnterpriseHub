"""
Seller Analytics Dashboard - Real-time Performance Visualizations

This module provides a comprehensive Streamlit dashboard for the Seller Analytics system,
featuring real-time visualizations, interactive KPI tracking, and cross-system insights
with performance monitoring and predictive analytics.

Business Value: Interactive interface for the $35K/year analytics system
Performance Targets:
- Dashboard Load Time: <500ms for real-time updates
- Chart Rendering: <200ms for complex visualizations
- Real-time Updates: <100ms for live metric refreshes

Author: EnterpriseHub Development Team
Created: January 11, 2026
Version: 1.0.0
"""

import asyncio
import logging
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import requests
from decimal import Decimal

from ..core.streamlit_utils import (
    create_metric_card,
    create_performance_gauge,
    create_trend_chart,
    format_currency,
    format_percentage,
    create_comparison_chart
)
from ..models.seller_analytics_models import (
    SellerPerformanceMetrics,
    AnalyticsTimeframe,
    MetricType,
    PerformanceLevel,
    AnalyticsCategory,
    TimeSeriesData,
    ComparativeBenchmark,
    PerformanceTrend
)
from ..services.seller_analytics_engine import get_seller_analytics_engine
from ..services.analytics_integration_layer import get_analytics_integration_layer
from ..streamlit_components.claude_component_mixin import ClaudeComponentMixin

logger = logging.getLogger(__name__)

class SellerAnalyticsDashboard(ClaudeComponentMixin):
    """
    Comprehensive Seller Analytics Dashboard with real-time visualizations.

    Features:
    - Real-time KPI monitoring with <500ms load times
    - Interactive performance metrics and trends
    - Cross-system analytics integration
    - Predictive insights and forecasting
    - Comparative benchmarking visualizations
    - Export and reporting capabilities
    - Claude AI integration for insights
    """

    def __init__(self):
        """Initialize the Seller Analytics Dashboard."""
        super().__init__(
            component_name="Seller Analytics Dashboard",
            default_seller_id="default_seller",
            real_time_updates=True
        )

        # Dashboard configuration
        self.update_interval_seconds = 30
        self.max_data_points = 100
        self.chart_theme = "plotly_white"

        # Performance tracking
        self.dashboard_load_time = 0.0
        self.last_update_time = datetime.now()

        # Cache for dashboard data
        self.cached_data = {}
        self.cache_expiry = 300  # 5 minutes

        # Component state
        self.selected_seller_id = None
        self.selected_timeframe = AnalyticsTimeframe.WEEKLY
        self.auto_refresh_enabled = True

    def render(self, seller_id: Optional[str] = None) -> None:
        """
        Render the complete Seller Analytics Dashboard.

        Args:
            seller_id: Optional seller ID to focus on
        """
        start_time = datetime.now()

        try:
            # Initialize session state
            self._initialize_session_state()

            # Dashboard header with controls
            self._render_dashboard_header()

            # Seller selection and timeframe controls
            selected_seller, selected_timeframe = self._render_control_panel()

            if selected_seller:
                # Main dashboard content
                col1, col2 = st.columns([2, 1])

                with col1:
                    # Key performance indicators
                    self._render_kpi_overview(selected_seller, selected_timeframe)

                    # Performance trends and charts
                    self._render_performance_trends(selected_seller, selected_timeframe)

                    # Cross-system analytics
                    self._render_cross_system_analytics(selected_seller, selected_timeframe)

                with col2:
                    # Real-time metrics sidebar
                    self._render_real_time_metrics(selected_seller)

                    # Performance insights
                    self._render_performance_insights(selected_seller, selected_timeframe)

                    # System health monitoring
                    self._render_system_health()

                # Advanced analytics section
                st.markdown("---")
                self._render_advanced_analytics(selected_seller, selected_timeframe)

                # Export and reporting section
                self._render_export_section(selected_seller, selected_timeframe)

            # Calculate and display dashboard performance
            self.dashboard_load_time = (datetime.now() - start_time).total_seconds() * 1000
            self._render_performance_footer()

        except Exception as e:
            st.error(f"Dashboard Error: {str(e)}")
            logger.error(f"Error rendering Seller Analytics Dashboard: {str(e)}")

    def _initialize_session_state(self) -> None:
        """Initialize Streamlit session state variables."""
        if "seller_analytics_data" not in st.session_state:
            st.session_state.seller_analytics_data = {}

        if "selected_seller_id" not in st.session_state:
            st.session_state.selected_seller_id = None

        if "dashboard_auto_refresh" not in st.session_state:
            st.session_state.dashboard_auto_refresh = True

        if "last_refresh" not in st.session_state:
            st.session_state.last_refresh = datetime.now()

    def _render_dashboard_header(self) -> None:
        """Render the dashboard header with title and status."""
        st.set_page_config(
            page_title="Seller Analytics Dashboard",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="collapsed"
        )

        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.title("📊 Seller Analytics Dashboard")
            st.caption("Real-time performance insights across all systems")

        with col2:
            # Auto-refresh toggle
            auto_refresh = st.checkbox(
                "Auto Refresh",
                value=st.session_state.dashboard_auto_refresh,
                key="auto_refresh_toggle"
            )
            st.session_state.dashboard_auto_refresh = auto_refresh

        with col3:
            # Manual refresh button
            if st.button("🔄 Refresh Now", type="primary"):
                st.session_state.last_refresh = datetime.now()
                st.rerun()

    def _render_control_panel(self) -> Tuple[Optional[str], AnalyticsTimeframe]:
        """Render seller selection and timeframe controls."""
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            # Seller selection
            available_sellers = self._get_available_sellers()
            selected_seller = st.selectbox(
                "Select Seller",
                options=available_sellers,
                index=0 if available_sellers else None,
                key="seller_selection"
            )

        with col2:
            # Timeframe selection
            selected_timeframe = st.selectbox(
                "Analysis Timeframe",
                options=[t.value for t in AnalyticsTimeframe],
                index=2,  # Default to WEEKLY
                key="timeframe_selection"
            )
            timeframe_enum = AnalyticsTimeframe(selected_timeframe)

        with col3:
            # Quick time filters
            quick_filter = st.selectbox(
                "Quick Filter",
                options=["Last 24 Hours", "Last 7 Days", "Last 30 Days", "Last 90 Days"],
                index=1,
                key="quick_filter"
            )

        with col4:
            # Advanced options
            show_predictions = st.checkbox("Predictions", value=True)

        return selected_seller, timeframe_enum

    def _render_kpi_overview(self, seller_id: str, timeframe: AnalyticsTimeframe) -> None:
        """Render key performance indicator overview."""
        st.subheader("🎯 Key Performance Indicators")

        try:
            # Get performance metrics
            analytics_data = self._get_seller_analytics_data(seller_id, timeframe)

            if analytics_data:
                metrics = analytics_data.get('seller_performance', {})

                # Create KPI metrics row
                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:
                    overall_score = metrics.get('overall_performance_score', 0)
                    performance_level = metrics.get('performance_level', 'unknown')

                    # Performance level color coding
                    if performance_level == 'excellent':
                        color = "🟢"
                    elif performance_level == 'good':
                        color = "🟡"
                    elif performance_level == 'average':
                        color = "🟠"
                    else:
                        color = "🔴"

                    st.metric(
                        label=f"{color} Overall Performance",
                        value=f"{overall_score:.1f}%",
                        delta=f"{performance_level.title()}"
                    )

                with col2:
                    conversion_rate = metrics.get('conversion_rate', 0)
                    st.metric(
                        label="🎯 Conversion Rate",
                        value=f"{conversion_rate:.1f}%",
                        delta=self._calculate_trend_delta(conversion_rate, 'conversion_rate')
                    )

                with col3:
                    engagement_rate = metrics.get('engagement_rate', 0)
                    st.metric(
                        label="👥 Engagement Rate",
                        value=f"{engagement_rate:.1f}%",
                        delta=self._calculate_trend_delta(engagement_rate, 'engagement_rate')
                    )

                with col4:
                    total_revenue = metrics.get('total_revenue_attributed', 0)
                    st.metric(
                        label="💰 Revenue",
                        value=format_currency(total_revenue),
                        delta=self._calculate_trend_delta(total_revenue, 'revenue')
                    )

                with col5:
                    total_activities = metrics.get('total_activities', 0)
                    st.metric(
                        label="📈 Activities",
                        value=f"{total_activities:,}",
                        delta=self._calculate_trend_delta(total_activities, 'activities')
                    )

                # Performance gauge chart
                self._render_performance_gauge(overall_score, performance_level)

        except Exception as e:
            st.error(f"Error loading KPI overview: {str(e)}")

    def _render_performance_gauge(self, score: float, level: str) -> None:
        """Render performance gauge visualization."""
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Performance Score"},
            delta = {'reference': 80},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))

        fig.update_layout(
            height=200,
            margin=dict(l=20, r=20, t=40, b=20),
            font={'color': "darkblue", 'family': "Arial"}
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_performance_trends(self, seller_id: str, timeframe: AnalyticsTimeframe) -> None:
        """Render performance trends and time-series charts."""
        st.subheader("📈 Performance Trends")

        try:
            # Get time-series data
            time_series_data = self._get_time_series_data(seller_id, timeframe)

            if time_series_data:
                # Create trend charts
                tab1, tab2, tab3, tab4 = st.tabs([
                    "Performance Score", "Revenue Trends", "Activity Metrics", "System Performance"
                ])

                with tab1:
                    self._render_performance_score_trend(time_series_data)

                with tab2:
                    self._render_revenue_trends(time_series_data)

                with tab3:
                    self._render_activity_metrics(time_series_data)

                with tab4:
                    self._render_system_performance_metrics(time_series_data)

        except Exception as e:
            st.error(f"Error loading performance trends: {str(e)}")

    def _render_performance_score_trend(self, time_series_data: List[Dict]) -> None:
        """Render performance score trend chart."""
        if not time_series_data:
            st.info("No time-series data available")
            return

        # Extract data for chart
        timestamps = [item['timestamp'] for item in time_series_data]
        performance_scores = [item.get('performance_score', 0) for item in time_series_data]
        conversion_rates = [item.get('conversion_rate', 0) for item in time_series_data]
        engagement_rates = [item.get('engagement_rate', 0) for item in time_series_data]

        # Create multi-line chart
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=timestamps,
            y=performance_scores,
            mode='lines+markers',
            name='Performance Score',
            line=dict(color='blue', width=3),
            marker=dict(size=6)
        ))

        fig.add_trace(go.Scatter(
            x=timestamps,
            y=conversion_rates,
            mode='lines+markers',
            name='Conversion Rate',
            line=dict(color='green', width=2),
            yaxis='y2'
        ))

        fig.add_trace(go.Scatter(
            x=timestamps,
            y=engagement_rates,
            mode='lines+markers',
            name='Engagement Rate',
            line=dict(color='orange', width=2),
            yaxis='y2'
        ))

        # Update layout with dual y-axes
        fig.update_layout(
            title='Performance Score and Key Metrics Trends',
            xaxis_title='Time',
            yaxis=dict(title='Performance Score (%)', side='left'),
            yaxis2=dict(title='Conversion & Engagement Rates (%)', side='right', overlaying='y'),
            height=400,
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_cross_system_analytics(self, seller_id: str, timeframe: AnalyticsTimeframe) -> None:
        """Render cross-system analytics and integrations."""
        st.subheader("🔗 Cross-System Analytics")

        try:
            # Get unified analytics data
            unified_data = self._get_unified_analytics_data(seller_id, timeframe)

            if unified_data:
                col1, col2 = st.columns(2)

                with col1:
                    # Property valuation analytics
                    self._render_property_valuation_metrics(unified_data)

                    # Document generation analytics
                    self._render_document_generation_metrics(unified_data)

                with col2:
                    # Marketing campaign analytics
                    self._render_marketing_campaign_metrics(unified_data)

                    # Workflow progression analytics
                    self._render_workflow_progression_metrics(unified_data)

                # Cross-system insights
                st.markdown("### 🧠 Cross-System Insights")
                insights = unified_data.get('cross_system_insights', [])

                if insights:
                    for insight in insights[:3]:  # Show top 3 insights
                        insight_type = insight.get('insight_type', 'Unknown')
                        description = insight.get('description', 'No description available')
                        confidence = insight.get('confidence_score', 0.0)

                        with st.expander(f"💡 {insight_type.replace('_', ' ').title()}", expanded=False):
                            st.write(description)
                            st.progress(confidence, text=f"Confidence: {confidence:.1%}")

                            recommendations = insight.get('recommended_actions', [])
                            if recommendations:
                                st.markdown("**Recommended Actions:**")
                                for action in recommendations:
                                    st.markdown(f"• {action}")
                else:
                    st.info("No cross-system insights available for this timeframe")

        except Exception as e:
            st.error(f"Error loading cross-system analytics: {str(e)}")

    def _render_real_time_metrics(self, seller_id: str) -> None:
        """Render real-time metrics sidebar."""
        st.markdown("### ⚡ Real-Time Metrics")

        try:
            # Get real-time data
            real_time_data = self._get_real_time_metrics(seller_id)

            if real_time_data:
                metrics = real_time_data.get('metrics', {})
                timestamp = real_time_data.get('timestamp', '')

                # Display real-time metrics
                st.metric(
                    label="Live Performance Score",
                    value=f"{metrics.get('overall_score', 0):.1f}%"
                )

                st.metric(
                    label="Current Conversion Rate",
                    value=f"{metrics.get('conversion_rate', 0):.1f}%"
                )

                st.metric(
                    label="Active Engagement Rate",
                    value=f"{metrics.get('engagement_rate', 0):.1f}%"
                )

                # Data freshness indicator
                freshness = real_time_data.get('data_freshness_seconds', 0)
                if freshness < 60:
                    freshness_text = f"{freshness}s ago"
                    freshness_color = "🟢"
                elif freshness < 300:
                    freshness_text = f"{freshness//60}m ago"
                    freshness_color = "🟡"
                else:
                    freshness_text = f"{freshness//60}m ago"
                    freshness_color = "🔴"

                st.caption(f"{freshness_color} Updated: {freshness_text}")

                # Auto-refresh countdown
                if st.session_state.dashboard_auto_refresh:
                    self._render_auto_refresh_countdown()

        except Exception as e:
            st.error(f"Error loading real-time metrics: {str(e)}")

    def _render_performance_insights(self, seller_id: str, timeframe: AnalyticsTimeframe) -> None:
        """Render AI-powered performance insights."""
        st.markdown("### 🤖 AI Insights")

        try:
            # Get Claude-generated insights
            insights = self.get_claude_insights(
                context=f"Seller {seller_id} performance analysis",
                data_summary=self._prepare_insights_data(seller_id, timeframe)
            )

            if insights:
                # Display insights with Claude branding
                st.markdown("**Claude AI Analysis:**")
                st.info(insights)

                # Insight categories
                insight_categories = [
                    "🎯 Performance Optimization",
                    "📈 Growth Opportunities",
                    "⚠️ Risk Factors",
                    "🔮 Predictive Insights"
                ]

                for category in insight_categories:
                    with st.expander(category, expanded=False):
                        category_insights = self._get_category_insights(
                            seller_id, timeframe, category
                        )
                        if category_insights:
                            st.write(category_insights)
                        else:
                            st.write("No specific insights available for this category.")

        except Exception as e:
            st.error(f"Error loading performance insights: {str(e)}")

    def _render_system_health(self) -> None:
        """Render system health monitoring."""
        st.markdown("### ⚕️ System Health")

        try:
            # Get system health data
            health_data = self._get_system_health()

            if health_data:
                overall_status = health_data.get('overall_status', 'unknown')
                health_percentage = health_data.get('health_percentage', 0)

                # Health status indicator
                if overall_status == 'excellent':
                    status_color = "🟢"
                    status_text = "Excellent"
                elif overall_status == 'good':
                    status_color = "🟡"
                    status_text = "Good"
                elif overall_status == 'warning':
                    status_color = "🟠"
                    status_text = "Warning"
                else:
                    status_color = "🔴"
                    status_text = "Critical"

                st.metric(
                    label=f"{status_color} System Status",
                    value=status_text,
                    delta=f"{health_percentage:.1f}% healthy"
                )

                # System component status
                components = health_data.get('system_details', {})
                for component, status in components.items():
                    if isinstance(status, dict):
                        component_health = status.get('healthy', False)
                        component_color = "🟢" if component_health else "🔴"
                        st.caption(f"{component_color} {component.replace('_', ' ').title()}")

        except Exception as e:
            st.error(f"Error loading system health: {str(e)}")

    def _render_advanced_analytics(self, seller_id: str, timeframe: AnalyticsTimeframe) -> None:
        """Render advanced analytics section."""
        st.subheader("🔬 Advanced Analytics")

        tab1, tab2, tab3, tab4 = st.tabs([
            "Predictive Analytics", "Benchmarking", "Correlation Analysis", "Custom Queries"
        ])

        with tab1:
            self._render_predictive_analytics(seller_id, timeframe)

        with tab2:
            self._render_benchmarking_analysis(seller_id, timeframe)

        with tab3:
            self._render_correlation_analysis(seller_id, timeframe)

        with tab4:
            self._render_custom_queries(seller_id, timeframe)

    def _render_export_section(self, seller_id: str, timeframe: AnalyticsTimeframe) -> None:
        """Render export and reporting section."""
        st.subheader("📊 Export & Reporting")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("📄 Export PDF Report"):
                self._export_pdf_report(seller_id, timeframe)

        with col2:
            if st.button("📊 Export Excel"):
                self._export_excel_report(seller_id, timeframe)

        with col3:
            if st.button("📈 Export Charts"):
                self._export_chart_images(seller_id, timeframe)

        with col4:
            if st.button("📋 Schedule Report"):
                self._schedule_automated_report(seller_id, timeframe)

    def _render_performance_footer(self) -> None:
        """Render performance metrics footer."""
        if self.dashboard_load_time > 0:
            # Performance indicators
            col1, col2, col3 = st.columns(3)

            with col1:
                load_time_color = "🟢" if self.dashboard_load_time < 500 else "🔴"
                st.caption(f"{load_time_color} Load Time: {self.dashboard_load_time:.1f}ms")

            with col2:
                st.caption(f"⚡ Last Updated: {st.session_state.last_refresh.strftime('%H:%M:%S')}")

            with col3:
                cache_status = "🟢 Cached" if hasattr(self, 'cache_hit') and self.cache_hit else "🔄 Live"
                st.caption(f"{cache_status}")

    # ==================================================================================
    # DATA RETRIEVAL METHODS
    # ==================================================================================

    def _get_seller_analytics_data(self, seller_id: str, timeframe: AnalyticsTimeframe) -> Dict[str, Any]:
        """Get seller analytics data from the API."""
        try:
            # Check cache first
            cache_key = f"{seller_id}_{timeframe.value}"
            if cache_key in self.cached_data:
                cached_time, data = self.cached_data[cache_key]
                if (datetime.now() - cached_time).seconds < self.cache_expiry:
                    return data

            # Get analytics engine and fetch data
            analytics_engine = get_seller_analytics_engine()
            result = analytics_engine.calculate_seller_performance_metrics(
                seller_id=seller_id,
                timeframe=timeframe,
                include_predictions=True
            )

            # Process and cache the result
            analytics_data = {
                'seller_performance': result.value.dict(),
                'calculation_metadata': {
                    'calculation_time_ms': result.calculation_time_ms,
                    'cache_hit': result.cache_hit,
                    'data_freshness_seconds': result.data_freshness_seconds
                }
            }

            self.cached_data[cache_key] = (datetime.now(), analytics_data)
            return analytics_data

        except Exception as e:
            logger.error(f"Error fetching seller analytics data: {str(e)}")
            return {}

    def _get_available_sellers(self) -> List[str]:
        """Get list of available sellers for selection."""
        try:
            # This would typically query the database or API
            # For demo purposes, return some sample seller IDs
            return [
                "seller_001 - John Smith",
                "seller_002 - Sarah Johnson",
                "seller_003 - Mike Wilson",
                "seller_004 - Emily Chen",
                "seller_005 - David Brown"
            ]
        except Exception as e:
            logger.error(f"Error fetching available sellers: {str(e)}")
            return ["demo_seller_001"]

    def _calculate_trend_delta(self, current_value: float, metric_type: str) -> str:
        """Calculate trend delta for metrics."""
        try:
            # This would typically compare with previous period
            # For demo purposes, return a sample delta
            import random
            delta = random.uniform(-10, 15)
            return f"{delta:+.1f}%"
        except:
            return "N/A"

    # ==================================================================================
    # UTILITY METHODS
    # ==================================================================================

    def _prepare_insights_data(self, seller_id: str, timeframe: AnalyticsTimeframe) -> str:
        """Prepare data summary for Claude insights generation."""
        try:
            analytics_data = self._get_seller_analytics_data(seller_id, timeframe)
            if analytics_data:
                metrics = analytics_data.get('seller_performance', {})
                return f"""
                Seller Performance Summary:
                - Overall Score: {metrics.get('overall_performance_score', 0):.1f}%
                - Conversion Rate: {metrics.get('conversion_rate', 0):.1f}%
                - Engagement Rate: {metrics.get('engagement_rate', 0):.1f}%
                - Revenue: ${metrics.get('total_revenue_attributed', 0):,.2f}
                - Activities: {metrics.get('total_activities', 0):,}
                """
            return "No performance data available"
        except Exception as e:
            return f"Error preparing insights data: {str(e)}"

# ==================================================================================
# DASHBOARD FACTORY AND UTILITIES
# ==================================================================================

def create_seller_analytics_dashboard() -> SellerAnalyticsDashboard:
    """Factory function to create a SellerAnalyticsDashboard instance."""
    return SellerAnalyticsDashboard()

def render_seller_analytics_dashboard(seller_id: Optional[str] = None) -> None:
    """Render the Seller Analytics Dashboard."""
    dashboard = create_seller_analytics_dashboard()
    dashboard.render(seller_id)

# Main dashboard entry point
if __name__ == "__main__":
    render_seller_analytics_dashboard()