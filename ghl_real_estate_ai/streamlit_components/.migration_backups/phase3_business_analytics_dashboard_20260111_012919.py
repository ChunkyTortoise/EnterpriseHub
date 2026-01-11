"""
Phase 3 Business Analytics Dashboard
====================================

Real-time business impact measurement and A/B testing visualization for Phase 3 features.

Features:
- Daily revenue impact by feature
- Progressive rollout management
- A/B test results with statistical significance
- ROI tracking and projections
- Feature flag control interface

Phase 3 Features Tracked:
- Real-Time Intelligence ($75K-120K/year target)
- Property Intelligence ($45K-60K/year target)
- Churn Prevention ($55K-80K/year target)
- AI Coaching ($60K-90K/year target)

Performance Targets:
- Dashboard load: <500ms
- Real-time updates: Every 30 seconds
- ROI calculation: <100ms

Author: EnterpriseHub Development Team
Created: January 2026
Version: 1.0.0
"""

# ============================================================================
# MIGRATION NOTES (Automated Migration - 2026-01-11)
# ============================================================================
# Changes Applied:
# # - Upgraded base class from EnterpriseComponent to EnterpriseDashboardComponent
# - Added unified design system import check
# - Consider using enterprise_metric for consistent styling
#
# This component has been migrated to enterprise standards.
# See migration documentation for details.
# ============================================================================



import asyncio

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
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

from ghl_real_estate_ai.streamlit_components.base import EnterpriseComponent
from ghl_real_estate_ai.services.phase3_business_impact_tracker import (
    get_business_impact_tracker,
    MetricType,
    FeaturePhase
)
from ghl_real_estate_ai.services.feature_flag_manager import (
    get_feature_flag_manager,
    RolloutStage,
    FeatureStatus,
    initialize_phase3_flags
)

logger = logging.getLogger(__name__)


class Phase3BusinessAnalyticsDashboard(EnterpriseDashboardComponent):
    """
    Real-time business analytics and A/B testing dashboard for Phase 3 features.

    Provides:
    - Revenue impact tracking by feature
    - Progressive rollout management
    - A/B test statistical analysis
    - ROI monitoring and projections
    - Feature flag control interface
    """

    def __init__(self):
        """Initialize dashboard component."""
        super().__init__()
        self.component_id = "phase3_business_analytics"
        self.tracker = None
        self.flag_manager = None

    async def _initialize_services(self) -> None:
        """Initialize business impact tracker and feature flag manager."""
        if not self.tracker:
            self.tracker = await get_business_impact_tracker()

        if not self.flag_manager:
            self.flag_manager = await get_feature_flag_manager()
            # Ensure Phase 3 flags are initialized
            await initialize_phase3_flags()

    def render(
        self,
        auto_refresh: bool = True,
        show_feature_flags: bool = True,
        show_ab_tests: bool = True
    ) -> None:
        """
        Render Phase 3 business analytics dashboard.

        Args:
            auto_refresh: Enable 30-second auto-refresh
            show_feature_flags: Show feature flag management
            show_ab_tests: Show A/B test results
        """
        try:
            # Initialize services
            asyncio.run(self._initialize_services())

            # Dashboard header
            st.title("📊 Phase 3 Business Analytics Dashboard")
            st.markdown(
                "**Real-time revenue tracking and A/B testing for high-value features**"
            )

            # Success metrics banner
            self._render_success_metrics_banner()

            # Tabs for different views
            tab1, tab2, tab3, tab4 = st.tabs([
                "💰 Revenue Impact",
                "🔄 Progressive Rollout",
                "🧪 A/B Test Results",
                "⚙️ Feature Flags"
            ])

            with tab1:
                self._render_revenue_impact_tab()

            with tab2:
                self._render_progressive_rollout_tab()

            with tab3:
                if show_ab_tests:
                    self._render_ab_test_results_tab()

            with tab4:
                if show_feature_flags:
                    self._render_feature_flag_management_tab()

            # Auto-refresh
            if auto_refresh:
                st.markdown("---")
                st.caption("🔄 Auto-refreshing every 30 seconds")
                import time
                time.sleep(30)
                st.experimental_rerun()

        except Exception as e:
            logger.error(f"Error rendering Phase 3 analytics dashboard: {e}")
            st.error(f"❌ Dashboard error: {str(e)}")

    def _render_success_metrics_banner(self) -> None:
        """Render success metrics banner at top."""
        st.markdown("### 🎯 Phase 3 Success Tracking")

        # Load daily summary
        summary = asyncio.run(self.tracker.get_daily_summary())

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_revenue = summary.get('total_revenue_impact', 0) * 365
            st.metric(
                "Total Annual Revenue Impact",
                f"${total_revenue:,.0f}",
                delta=f"Target: $265K-440K",
                help="Projected annual revenue from Phase 3 features"
            )

        with col2:
            total_savings = summary.get('total_cost_savings', 0) * 365
            st.metric(
                "Annual Cost Savings",
                f"${total_savings:,.0f}",
                help="Cost savings from automation and efficiency"
            )

        with col3:
            total_value = (total_revenue + total_savings)
            st.metric(
                "Total Annual Value",
                f"${total_value:,.0f}",
                help="Combined revenue impact and cost savings"
            )

        with col4:
            roi = summary.get('total_roi', 0)
            roi_color = "normal" if roi > 300 else "inverse"
            st.metric(
                "Platform ROI",
                f"{roi:.1f}%",
                delta="Target: >300%",
                delta_color=roi_color,
                help="Return on investment for Phase 3 features"
            )

    def _render_revenue_impact_tab(self) -> None:
        """Render revenue impact analysis tab."""
        st.header("💰 Revenue Impact by Feature")

        # Feature selection
        feature_options = {
            "All Features": None,
            "Real-Time Intelligence": "realtime_intelligence",
            "Property Intelligence": "property_intelligence",
            "Churn Prevention": "churn_prevention",
            "AI Coaching": "ai_coaching"
        }

        selected_feature = st.selectbox(
            "Select Feature",
            options=list(feature_options.keys())
        )

        feature_id = feature_options[selected_feature]

        # Time range selection
        time_ranges = {
            "Last 7 days": 7,
            "Last 30 days": 30,
            "Last 90 days": 90
        }

        selected_range = st.selectbox(
            "Time Range",
            options=list(time_ranges.keys()),
            index=1
        )

        days = time_ranges[selected_range]

        # Feature-specific analysis
        if feature_id:
            self._render_feature_roi_analysis(feature_id, days)
        else:
            self._render_all_features_comparison(days)

    def _render_feature_roi_analysis(
        self,
        feature_id: str,
        days: int
    ) -> None:
        """Render detailed ROI analysis for specific feature."""
        roi = asyncio.run(
            self.tracker.calculate_feature_roi(feature_id, days)
        )

        if not roi:
            st.warning(f"No data available for {feature_id}")
            return

        # Feature details
        st.subheader(f"📈 {roi.feature_name}")

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Revenue Impact",
                f"${roi.revenue_impact:,.0f}",
                help="Direct revenue impact from feature"
            )

        with col2:
            st.metric(
                "Cost Savings",
                f"${roi.cost_savings:,.0f}",
                help="Cost savings from automation"
            )

        with col3:
            st.metric(
                "Net Value",
                f"${roi.net_value:,.0f}",
                delta=f"ROI: {roi.roi_percentage:.1f}%",
                help="Net value after costs"
            )

        with col4:
            roi_color = "🟢" if roi.roi_percentage > 300 else "🟡" if roi.roi_percentage > 100 else "🔴"
            st.metric(
                "ROI",
                f"{roi_color} {roi.roi_percentage:.1f}%",
                help="Return on investment percentage"
            )

        # Performance lift metrics
        st.markdown("#### 📊 Performance Improvements")

        perf_cols = st.columns(4)

        with perf_cols[0]:
            if roi.conversion_lift > 0:
                st.metric(
                    "Conversion Lift",
                    f"+{roi.conversion_lift:.1f}%"
                )

        with perf_cols[1]:
            if roi.satisfaction_lift > 0:
                st.metric(
                    "Satisfaction Lift",
                    f"+{roi.satisfaction_lift:.1f}%"
                )

        with perf_cols[2]:
            if roi.productivity_lift > 0:
                st.metric(
                    "Productivity Lift",
                    f"+{roi.productivity_lift:.1f}%"
                )

        with perf_cols[3]:
            if roi.churn_reduction > 0:
                st.metric(
                    "Churn Reduction",
                    f"-{roi.churn_reduction:.1f}%"
                )

        # Cost breakdown
        st.markdown("#### 💵 Cost Analysis")

        cost_data = {
            'Category': ['Infrastructure', 'API Costs', 'Revenue Impact', 'Cost Savings'],
            'Amount': [
                -roi.infrastructure_cost,
                -roi.api_costs,
                roi.revenue_impact,
                roi.cost_savings
            ],
            'Type': ['Cost', 'Cost', 'Benefit', 'Benefit']
        }

        cost_df = pd.DataFrame(cost_data)

        fig = go.Figure()

        fig.add_trace(go.Waterfall(
            x=cost_df['Category'],
            y=cost_df['Amount'],
            measure=['relative', 'relative', 'relative', 'total'],
            text=[f"${abs(v):,.0f}" for v in cost_df['Amount']],
            textposition="outside",
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        ))

        fig.update_layout(
            title="ROI Waterfall Analysis",
            showlegend=False,
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_all_features_comparison(self, days: int) -> None:
        """Render comparison of all Phase 3 features."""
        st.subheader("🔍 All Features Comparison")

        # Calculate ROI for all features
        feature_data = []

        for feature_id in ['realtime_intelligence', 'property_intelligence',
                          'churn_prevention', 'ai_coaching']:
            roi = asyncio.run(
                self.tracker.calculate_feature_roi(feature_id, days)
            )

            if roi:
                feature_data.append({
                    'Feature': roi.feature_name,
                    'Revenue Impact': roi.revenue_impact,
                    'Cost Savings': roi.cost_savings,
                    'Net Value': roi.net_value,
                    'ROI %': roi.roi_percentage,
                    'Sample Size': roi.sample_size
                })

        if not feature_data:
            st.info("No feature data available yet")
            return

        df = pd.DataFrame(feature_data)

        # Feature comparison table
        st.dataframe(
            df.style.format({
                'Revenue Impact': '${:,.0f}',
                'Cost Savings': '${:,.0f}',
                'Net Value': '${:,.0f}',
                'ROI %': '{:.1f}%'
            }),
            use_container_width=True
        )

        # Comparison charts
        col1, col2 = st.columns(2)

        with col1:
            # Net value comparison
            fig = px.bar(
                df,
                x='Feature',
                y='Net Value',
                title="Net Value by Feature",
                color='ROI %',
                color_continuous_scale='RdYlGn'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # ROI percentage comparison
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df['Feature'],
                y=df['ROI %'],
                marker_color=['green' if x > 300 else 'orange' if x > 100 else 'red'
                             for x in df['ROI %']],
                text=[f"{x:.0f}%" for x in df['ROI %']],
                textposition='outside'
            ))

            fig.add_hline(
                y=300,
                line_dash="dash",
                line_color="green",
                annotation_text="Target ROI (300%)"
            )

            fig.update_layout(
                title="ROI % by Feature",
                yaxis_title="ROI %",
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

    def _render_progressive_rollout_tab(self) -> None:
        """Render progressive rollout management tab."""
        st.header("🔄 Progressive Rollout Management")

        # Get all Phase 3 flags
        flags = asyncio.run(self.flag_manager.get_all_flags())
        phase3_flags = [
            f for f in flags
            if f.feature_id in ['realtime_intelligence', 'property_intelligence',
                               'churn_prevention', 'ai_coaching']
        ]

        if not phase3_flags:
            st.warning("Phase 3 feature flags not initialized")
            return

        # Rollout status overview
        st.subheader("📊 Rollout Status")

        status_data = []
        for flag in phase3_flags:
            status_data.append({
                'Feature': flag.name,
                'Stage': flag.rollout_stage.value,
                'Traffic %': flag.percentage,
                'Status': flag.status.value,
                'Current ROI': flag.current_roi,
                'Target ROI': flag.roi_target
            })

        status_df = pd.DataFrame(status_data)

        st.dataframe(
            status_df.style.format({
                'Traffic %': '{:.1f}%',
                'Current ROI': '${:,.0f}',
                'Target ROI': '${:,.0f}'
            }),
            use_container_width=True
        )

        # Rollout timeline visualization
        st.subheader("📈 Rollout Timeline")

        # Create Gantt-like chart
        fig = go.Figure()

        stage_order = {
            'disabled': 0,
            'internal': 1,
            'beta_10': 2,
            'beta_25': 3,
            'beta_50': 4,
            'ga': 5
        }

        for flag in phase3_flags:
            stage_value = stage_order.get(flag.rollout_stage.value, 0)

            fig.add_trace(go.Bar(
                y=[flag.name],
                x=[stage_value],
                orientation='h',
                name=flag.name,
                text=f"{flag.rollout_stage.value} ({flag.percentage:.0f}%)",
                textposition='inside'
            ))

        fig.update_layout(
            title="Feature Rollout Progress",
            xaxis=dict(
                tickmode='array',
                tickvals=list(stage_order.values()),
                ticktext=list(stage_order.keys())
            ),
            barmode='stack',
            height=300,
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

        # Rollout controls
        st.subheader("⚙️ Rollout Controls")

        col1, col2 = st.columns(2)

        with col1:
            selected_feature = st.selectbox(
                "Select Feature to Manage",
                options=[f.name for f in phase3_flags]
            )

            selected_flag = next(
                f for f in phase3_flags if f.name == selected_feature
            )

        with col2:
            new_stage = st.selectbox(
                "Update Rollout Stage",
                options=[
                    "Disabled",
                    "Internal Testing",
                    "Beta 10%",
                    "Beta 25%",
                    "Beta 50%",
                    "General Availability"
                ]
            )

            stage_mapping = {
                "Disabled": RolloutStage.DISABLED,
                "Internal Testing": RolloutStage.INTERNAL,
                "Beta 10%": RolloutStage.BETA_10,
                "Beta 25%": RolloutStage.BETA_25,
                "Beta 50%": RolloutStage.BETA_50,
                "General Availability": RolloutStage.GA
            }

        if st.button("🚀 Update Rollout Stage", type="primary"):
            new_stage_enum = stage_mapping[new_stage]

            success = asyncio.run(
                self.flag_manager.update_rollout_stage(
                    selected_flag.feature_id,
                    new_stage_enum
                )
            )

            if success:
                st.success(f"✅ Rollout updated: {selected_feature} → {new_stage}")
                st.experimental_rerun()
            else:
                st.error("❌ Failed to update rollout stage")

    def _render_ab_test_results_tab(self) -> None:
        """Render A/B test results and statistical analysis."""
        st.header("🧪 A/B Test Results")

        # Feature and metric selection
        col1, col2 = st.columns(2)

        with col1:
            feature_names = {
                "Real-Time Intelligence": "realtime_intelligence",
                "Property Intelligence": "property_intelligence",
                "Churn Prevention": "churn_prevention",
                "AI Coaching": "ai_coaching"
            }

            selected_name = st.selectbox(
                "Select Feature",
                options=list(feature_names.keys())
            )

            feature_id = feature_names[selected_name]

        with col2:
            metric_options = {
                "Real-Time Intelligence": MetricType.RESPONSE_TIME,
                "Property Intelligence": MetricType.SATISFACTION_RATE,
                "Churn Prevention": MetricType.CHURN_RATE,
                "AI Coaching": MetricType.TRAINING_TIME
            }

            metric_type = metric_options[selected_name]

        # Run A/B test analysis
        with st.spinner("🔬 Running statistical analysis..."):
            result = asyncio.run(
                self.tracker.run_ab_test_analysis(
                    feature_id,
                    metric_type,
                    days=30
                )
            )

        if not result:
            st.warning("No A/B test data available")
            return

        # Results display
        st.subheader(f"📊 {selected_name} A/B Test Results")

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Control Mean",
                f"{result.control_mean:.2f}",
                help=f"Sample size: {result.control_count}"
            )

        with col2:
            st.metric(
                "Treatment Mean",
                f"{result.treatment_mean:.2f}",
                delta=f"{result.lift_percentage:+.1f}%",
                help=f"Sample size: {result.treatment_count}"
            )

        with col3:
            significance_color = "🟢" if result.is_significant else "🔴"
            st.metric(
                "Statistical Significance",
                f"{significance_color} {result.confidence_level:.1f}%",
                help=f"P-value: {result.p_value:.4f}"
            )

        with col4:
            action_emoji = {
                "roll_forward": "✅",
                "rollback": "🔴",
                "continue_testing": "🔄",
                "neutral": "⚪",
                "insufficient_data": "📊"
            }.get(result.recommended_action, "❓")

            st.metric(
                "Recommendation",
                f"{action_emoji} {result.recommended_action.replace('_', ' ').title()}"
            )

        # Distribution comparison
        st.subheader("📈 Distribution Comparison")

        col1, col2 = st.columns(2)

        with col1:
            # Box plot
            fig = go.Figure()

            fig.add_trace(go.Box(
                y=[result.control_mean] * 100,  # Simplified visualization
                name='Control',
                marker_color='lightblue'
            ))

            fig.add_trace(go.Box(
                y=[result.treatment_mean] * 100,
                name='Treatment',
                marker_color='lightgreen'
            ))

            fig.update_layout(
                title="Control vs Treatment Distribution",
                yaxis_title=metric_type.value.replace('_', ' ').title(),
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Recommendation details
            if result.is_significant:
                if result.lift_percentage > 5:
                    st.success(
                        f"✅ **Positive Impact Detected**\n\n"
                        f"Treatment shows {abs(result.lift_percentage):.1f}% improvement. "
                        f"Recommend rolling forward to next stage."
                    )
                elif result.lift_percentage < -5:
                    st.error(
                        f"🔴 **Negative Impact Detected**\n\n"
                        f"Treatment shows {abs(result.lift_percentage):.1f}% degradation. "
                        f"Recommend rollback."
                    )
                else:
                    st.info(
                        "⚪ **Neutral Result**\n\n"
                        "No significant difference detected. Continue monitoring."
                    )
            else:
                st.warning(
                    f"📊 **Insufficient Data**\n\n"
                    f"Sample sizes: Control={result.control_count}, Treatment={result.treatment_count}\n\n"
                    f"Recommendation: Continue testing to reach statistical significance."
                )

            # Next steps
            st.markdown("**Next Steps:**")
            if result.recommended_action == "roll_forward":
                st.markdown("• Increase rollout percentage")
                st.markdown("• Monitor for regression")
                st.markdown("• Document success metrics")
            elif result.recommended_action == "rollback":
                st.markdown("• Rollback to previous version")
                st.markdown("• Investigate root cause")
                st.markdown("• Implement fixes")
            else:
                st.markdown("• Continue data collection")
                st.markdown("• Monitor daily trends")
                st.markdown("• Re-analyze in 7 days")

    def _render_feature_flag_management_tab(self) -> None:
        """Render feature flag management interface."""
        st.header("⚙️ Feature Flag Management")

        # Get all flags
        flags = asyncio.run(self.flag_manager.get_all_flags())

        phase3_flags = [
            f for f in flags
            if f.feature_id in ['realtime_intelligence', 'property_intelligence',
                               'churn_prevention', 'ai_coaching']
        ]

        for flag in phase3_flags:
            with st.expander(f"🚩 {flag.name}", expanded=False):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**Description:** {flag.description}")
                    st.markdown(f"**Feature ID:** `{flag.feature_id}`")
                    st.markdown(f"**Status:** {flag.status.value}")
                    st.markdown(f"**Rollout Stage:** {flag.rollout_stage.value}")
                    st.markdown(f"**Traffic:** {flag.percentage:.1f}%")

                with col2:
                    st.markdown(f"**ROI Target:** ${flag.roi_target:,.0f}/year")
                    st.markdown(f"**Current ROI:** ${flag.current_roi:,.0f}/year")
                    st.markdown(f"**Error Rate Threshold:** {flag.error_rate_threshold}%")
                    st.markdown(f"**Latency Threshold:** {flag.latency_threshold_ms}ms")

                # Tenant controls
                st.markdown("**Tenant Access Control:**")

                tenant_col1, tenant_col2 = st.columns(2)

                with tenant_col1:
                    whitelist_str = st.text_area(
                        "Whitelist (one per line)",
                        value="\n".join(flag.tenant_whitelist),
                        key=f"whitelist_{flag.feature_id}",
                        height=100
                    )

                with tenant_col2:
                    blacklist_str = st.text_area(
                        "Blacklist (one per line)",
                        value="\n".join(flag.tenant_blacklist),
                        key=f"blacklist_{flag.feature_id}",
                        height=100
                    )

                if st.button(f"💾 Save {flag.name} Configuration", key=f"save_{flag.feature_id}"):
                    flag.tenant_whitelist = [
                        t.strip() for t in whitelist_str.split('\n') if t.strip()
                    ]
                    flag.tenant_blacklist = [
                        t.strip() for t in blacklist_str.split('\n') if t.strip()
                    ]

                    success = asyncio.run(self.flag_manager.create_flag(flag))

                    if success:
                        st.success(f"✅ Configuration saved for {flag.name}")
                    else:
                        st.error(f"❌ Failed to save configuration")

        # Performance metrics
        st.markdown("---")
        st.subheader("📊 Feature Flag Performance")

        metrics = asyncio.run(self.flag_manager.get_performance_metrics())

        if metrics.get('message') != "No metrics available":
            perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)

            with perf_col1:
                st.metric(
                    "Total Lookups",
                    f"{metrics.get('total_lookups', 0):,}"
                )

            with perf_col2:
                st.metric(
                    "Avg Latency",
                    f"{metrics.get('avg_latency_ms', 0):.2f}ms",
                    delta="Target: <1ms"
                )

            with perf_col3:
                st.metric(
                    "P95 Latency",
                    f"{metrics.get('p95_latency_ms', 0):.2f}ms"
                )

            with perf_col4:
                st.metric(
                    "Cache Size",
                    f"{metrics.get('cache_size', 0)}"
                )


# Component factory
def create_phase3_business_analytics() -> Phase3BusinessAnalyticsDashboard:
    """Create Phase 3 business analytics dashboard."""
    return Phase3BusinessAnalyticsDashboard()


# Example usage
if __name__ == "__main__":
    dashboard = Phase3BusinessAnalyticsDashboard()
    dashboard.render(auto_refresh=False)
