"""
Service 6 Enhanced Lead Recovery Engine - Production Health Dashboard
Enterprise-grade monitoring dashboard with real-time system health visualization.
"""

from dataclasses import dataclass
from enum import Enum

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from ..services.cache_service import CacheService
from ..services.database_service import DatabaseService
from .service6_alerting_engine import Service6AlertingEngine
from .service6_metrics_collector import MetricType, Service6MetricsCollector


class HealthStatus(Enum):
    """System health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"


@dataclass
class SystemHealthMetrics:
    """Comprehensive system health metrics."""

    overall_status: HealthStatus
    agent_orchestration_health: float  # 0-100
    database_performance_health: float  # 0-100
    lead_processing_health: float  # 0-100
    revenue_impact_score: float  # 0-100
    active_alerts_count: int
    leads_processed_last_hour: int
    revenue_pipeline_health: float  # 0-100
    system_uptime_hours: float
    error_rate_percentage: float
    response_time_p95_ms: float


class Service6HealthDashboard:
    """
    Production health dashboard for Service 6 Enhanced Lead Recovery Engine.
    Provides real-time monitoring with executive-level insights.
    """

    def __init__(self):
        self.metrics_collector = Service6MetricsCollector()
        self.alerting_engine = Service6AlertingEngine()
        self.db_service = DatabaseService()
        self.cache_service = CacheService()

        # Dashboard refresh intervals (seconds)
        self.REAL_TIME_REFRESH = 10  # Critical metrics
        self.STANDARD_REFRESH = 60  # Standard metrics
        self.SLOW_REFRESH = 300  # Historical trends

    @st.cache_data(ttl=10, show_spinner=False)
    def get_real_time_health_metrics(self) -> SystemHealthMetrics:
        """Get real-time system health metrics with 10-second cache."""
        try:
            # Collect latest metrics
            agent_health = self._get_agent_orchestration_health()
            db_health = self._get_database_performance_health()
            lead_health = self._get_lead_processing_health()

            # Calculate overall health status
            overall_score = (agent_health + db_health + lead_health) / 3

            if overall_score >= 90:
                status = HealthStatus.HEALTHY
            elif overall_score >= 70:
                status = HealthStatus.DEGRADED
            elif overall_score >= 30:
                status = HealthStatus.CRITICAL
            else:
                status = HealthStatus.OFFLINE

            # Revenue impact calculation
            revenue_impact = self._calculate_revenue_impact_score(agent_health, db_health, lead_health)

            return SystemHealthMetrics(
                overall_status=status,
                agent_orchestration_health=agent_health,
                database_performance_health=db_health,
                lead_processing_health=lead_health,
                revenue_impact_score=revenue_impact,
                active_alerts_count=self._get_active_alerts_count(),
                leads_processed_last_hour=self._get_leads_processed_count(),
                revenue_pipeline_health=self._get_revenue_pipeline_health(),
                system_uptime_hours=self._get_system_uptime(),
                error_rate_percentage=self._get_error_rate(),
                response_time_p95_ms=self._get_response_time_p95(),
            )

        except Exception as e:
            st.error(f"Failed to collect health metrics: {e}")
            return self._get_fallback_metrics()

    def render_executive_dashboard(self) -> None:
        """Render executive-level dashboard with key business metrics."""
        st.title("🚀 Service 6 Enhanced Lead Recovery Engine")
        st.subheader("Executive Production Dashboard")

        # Get real-time metrics
        health_metrics = self.get_real_time_health_metrics()

        # Top-level status indicator
        self._render_overall_status(health_metrics)

        # Key business metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            self._render_revenue_impact_card(health_metrics)

        with col2:
            self._render_leads_processed_card(health_metrics)

        with col3:
            self._render_pipeline_health_card(health_metrics)

        with col4:
            self._render_system_uptime_card(health_metrics)

        # Critical alerts section
        if health_metrics.active_alerts_count > 0:
            self._render_critical_alerts_section()

        # Real-time performance charts
        self._render_performance_charts()

        # Agent orchestration health
        self._render_agent_health_section(health_metrics)

    def render_technical_dashboard(self) -> None:
        """Render technical dashboard for DevOps and engineering teams."""
        st.title("⚙️ Service 6 Technical Monitoring")
        st.subheader("DevOps & Engineering Dashboard")

        # Get detailed metrics
        health_metrics = self.get_real_time_health_metrics()

        # Technical metrics grid
        col1, col2, col3 = st.columns(3)

        with col1:
            self._render_database_metrics()

        with col2:
            self._render_agent_performance_metrics()

        with col3:
            self._render_system_performance_metrics()

        # Error tracking and debugging
        self._render_error_tracking_section()

        # Agent swarm performance analysis
        self._render_agent_swarm_analysis()

        # Database performance deep dive
        self._render_database_performance_deep_dive()

    def _render_overall_status(self, metrics: SystemHealthMetrics) -> None:
        """Render overall system status indicator."""
        status_colors = {
            HealthStatus.HEALTHY: "🟢",
            HealthStatus.DEGRADED: "🟡",
            HealthStatus.CRITICAL: "🟠",
            HealthStatus.OFFLINE: "🔴",
        }

        status_text = {
            HealthStatus.HEALTHY: "All Systems Operational",
            HealthStatus.DEGRADED: "Performance Degraded",
            HealthStatus.CRITICAL: "Critical Issues Detected",
            HealthStatus.OFFLINE: "System Offline",
        }

        icon = status_colors[metrics.overall_status]
        text = status_text[metrics.overall_status]

        st.markdown(
            f"""
        <div style="text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px; margin-bottom: 20px;">
            <h2>{icon} {text}</h2>
            <p>Overall System Health: {(metrics.agent_orchestration_health + metrics.database_performance_health + metrics.lead_processing_health) / 3:.1f}%</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _render_revenue_impact_card(self, metrics: SystemHealthMetrics) -> None:
        """Render revenue impact metric card."""
        impact_color = (
            "green" if metrics.revenue_impact_score >= 90 else "orange" if metrics.revenue_impact_score >= 70 else "red"
        )

        st.metric(
            label="💰 Revenue Impact Score",
            value=f"{metrics.revenue_impact_score:.1f}%",
            delta=f"{self._get_revenue_impact_delta():.1f}%",
            delta_color=impact_color,
        )

        # Revenue projection
        monthly_projection = self._calculate_monthly_revenue_projection(metrics.revenue_impact_score)
        st.caption(f"Projected Monthly Revenue: ${monthly_projection:,.0f}")

    def _render_leads_processed_card(self, metrics: SystemHealthMetrics) -> None:
        """Render leads processed metric card."""
        st.metric(
            label="📈 Leads Processed (Last Hour)",
            value=f"{metrics.leads_processed_last_hour:,}",
            delta=f"{self._get_leads_processed_delta()}",
            delta_color="normal",
        )

        # Processing velocity
        velocity = metrics.leads_processed_last_hour * 24  # Daily projection
        st.caption(f"Daily Velocity: {velocity:,} leads")

    def _render_pipeline_health_card(self, metrics: SystemHealthMetrics) -> None:
        """Render revenue pipeline health card."""
        pipeline_color = (
            "green"
            if metrics.revenue_pipeline_health >= 90
            else "orange"
            if metrics.revenue_pipeline_health >= 70
            else "red"
        )

        st.metric(
            label="🎯 Pipeline Health",
            value=f"{metrics.revenue_pipeline_health:.1f}%",
            delta=f"{self._get_pipeline_health_delta():.1f}%",
            delta_color=pipeline_color,
        )

        # Conversion insights
        conversion_rate = self._get_current_conversion_rate()
        st.caption(f"Lead→Opportunity: {conversion_rate:.1f}%")

    def _render_system_uptime_card(self, metrics: SystemHealthMetrics) -> None:
        """Render system uptime card."""
        uptime_days = metrics.system_uptime_hours / 24

        st.metric(
            label="⏱️ System Uptime",
            value=f"{uptime_days:.1f} days",
            delta=f"{metrics.error_rate_percentage:.2f}% error rate",
            delta_color="inverse",
        )

        # SLA compliance
        sla_compliance = self._calculate_sla_compliance(metrics.system_uptime_hours)
        st.caption(f"SLA Compliance: {sla_compliance:.1f}%")

    def _render_performance_charts(self) -> None:
        """Render real-time performance charts."""
        st.subheader("📊 Real-Time Performance Metrics")

        # Get time series data
        performance_data = self._get_performance_time_series()

        # Create subplots for multiple metrics
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=[
                "Lead Processing Rate",
                "Agent Response Times",
                "Database Query Performance",
                "Revenue Pipeline Velocity",
            ],
            specs=[[{"secondary_y": True}, {"secondary_y": True}], [{"secondary_y": True}, {"secondary_y": True}]],
        )

        # Lead processing rate
        fig.add_trace(
            go.Scatter(
                x=performance_data["timestamps"],
                y=performance_data["leads_per_minute"],
                name="Leads/Min",
                line=dict(color="blue", width=2),
            ),
            row=1,
            col=1,
        )

        # Agent response times
        fig.add_trace(
            go.Scatter(
                x=performance_data["timestamps"],
                y=performance_data["agent_response_times"],
                name="Response Time (ms)",
                line=dict(color="green", width=2),
            ),
            row=1,
            col=2,
        )

        # Database performance
        fig.add_trace(
            go.Scatter(
                x=performance_data["timestamps"],
                y=performance_data["db_query_times"],
                name="Query Time (ms)",
                line=dict(color="orange", width=2),
            ),
            row=2,
            col=1,
        )

        # Revenue pipeline velocity
        fig.add_trace(
            go.Scatter(
                x=performance_data["timestamps"],
                y=performance_data["pipeline_velocity"],
                name="Pipeline Velocity",
                line=dict(color="purple", width=2),
            ),
            row=2,
            col=2,
        )

        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    def _render_agent_health_section(self, metrics: SystemHealthMetrics) -> None:
        """Render agent orchestration health section."""
        st.subheader("🤖 Agent Orchestration Health")

        # Agent performance breakdown
        agent_performance = self._get_agent_performance_breakdown()

        col1, col2 = st.columns([2, 1])

        with col1:
            # Agent performance heatmap
            self._render_agent_performance_heatmap(agent_performance)

        with col2:
            # Top performing agents
            st.write("**Top Performing Agents:**")
            top_agents = sorted(agent_performance.items(), key=lambda x: x[1]["success_rate"], reverse=True)[:5]

            for agent, perf in top_agents:
                success_rate = perf["success_rate"]
                color = "green" if success_rate >= 95 else "orange" if success_rate >= 90 else "red"
                st.markdown(f"- **{agent}**: {success_rate:.1f}% success rate")

    # Helper methods for data collection
    def _get_agent_orchestration_health(self) -> float:
        """Calculate agent orchestration health score."""
        try:
            # Get agent performance metrics
            agent_metrics = self.metrics_collector.get_latest_metrics(MetricType.AGENT_PERFORMANCE)

            if not agent_metrics:
                return 50.0  # Default degraded state

            # Calculate weighted health score
            success_rates = [m.value for m in agent_metrics if m.metric_name.endswith("_success_rate")]
            response_times = [m.value for m in agent_metrics if m.metric_name.endswith("_response_time")]

            if not success_rates:
                return 50.0

            # Health = weighted average of success rate (70%) and response time performance (30%)
            avg_success_rate = sum(success_rates) / len(success_rates)

            # Penalize for slow response times (>5 seconds)
            response_penalty = 0
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                if avg_response_time > 5000:  # 5 seconds
                    response_penalty = min(20, (avg_response_time - 5000) / 1000 * 2)

            health_score = avg_success_rate * 0.7 + (100 - response_penalty) * 0.3
            return max(0, min(100, health_score))

        except Exception as e:
            st.error(f"Failed to calculate agent health: {e}")
            return 25.0  # Critical state on error

    def _get_database_performance_health(self) -> float:
        """Calculate database performance health score."""
        try:
            db_metrics = self.metrics_collector.get_latest_metrics(MetricType.SYSTEM_PERFORMANCE)

            # Default thresholds for health calculation
            query_time_threshold = 100  # ms
            connection_usage_threshold = 80  # %

            query_times = [m.value for m in db_metrics if "query_time" in m.metric_name]
            connection_usage = [m.value for m in db_metrics if "connection_pool" in m.metric_name]

            health_score = 100.0

            # Penalize slow queries
            if query_times:
                avg_query_time = sum(query_times) / len(query_times)
                if avg_query_time > query_time_threshold:
                    health_score -= min(30, (avg_query_time - query_time_threshold) / 10)

            # Penalize high connection usage
            if connection_usage:
                max_connection_usage = max(connection_usage)
                if max_connection_usage > connection_usage_threshold:
                    health_score -= min(20, (max_connection_usage - connection_usage_threshold) / 2)

            return max(0, health_score)

        except Exception as e:
            st.error(f"Failed to calculate database health: {e}")
            return 50.0

    def _get_lead_processing_health(self) -> float:
        """Calculate lead processing health score."""
        try:
            business_metrics = self.metrics_collector.get_latest_metrics(MetricType.BUSINESS_KPI)

            # Key lead processing indicators
            processing_rate = next(
                (m.value for m in business_metrics if m.metric_name == "leads_processed_per_hour"), 0
            )
            error_rate = next((m.value for m in business_metrics if m.metric_name == "lead_processing_error_rate"), 0)

            # Expected processing rate baseline (leads per hour)
            expected_rate = 100  # Configurable baseline

            # Calculate health based on processing performance
            rate_health = min(100, (processing_rate / expected_rate) * 100)
            error_penalty = min(50, error_rate * 5)  # 5% penalty per 1% error rate

            return max(0, rate_health - error_penalty)

        except Exception as e:
            st.error(f"Failed to calculate lead processing health: {e}")
            return 50.0

    def _calculate_revenue_impact_score(self, agent_health: float, db_health: float, lead_health: float) -> float:
        """Calculate revenue impact score based on system health."""
        # Revenue impact weights: Lead processing (50%), Agent health (30%), DB health (20%)
        weighted_score = lead_health * 0.5 + agent_health * 0.3 + db_health * 0.2

        # Apply revenue multipliers for high-performing systems
        if weighted_score >= 95:
            return min(100, weighted_score * 1.05)  # 5% bonus for exceptional performance
        elif weighted_score <= 50:
            return weighted_score * 0.8  # 20% penalty for poor performance

        return weighted_score

    def _get_fallback_metrics(self) -> SystemHealthMetrics:
        """Return fallback metrics when collection fails."""
        return SystemHealthMetrics(
            overall_status=HealthStatus.CRITICAL,
            agent_orchestration_health=0.0,
            database_performance_health=0.0,
            lead_processing_health=0.0,
            revenue_impact_score=0.0,
            active_alerts_count=99,
            leads_processed_last_hour=0,
            revenue_pipeline_health=0.0,
            system_uptime_hours=0.0,
            error_rate_percentage=100.0,
            response_time_p95_ms=999999.0,
        )

    # Additional helper methods would continue here...
    # (Implementations for _get_active_alerts_count, _get_leads_processed_count,
    #  _get_revenue_pipeline_health, _get_system_uptime, _get_error_rate,
    #  _get_response_time_p95, etc.)
