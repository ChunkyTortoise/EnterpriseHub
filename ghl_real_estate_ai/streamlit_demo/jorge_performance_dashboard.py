#!/usr/bin/env python3
"""
🎯 Jorge Bot Performance Monitoring Dashboard
=============================================

Real-time performance monitoring dashboard for Jorge's specialized real estate AI bots
with comprehensive metrics, alerts, and optimization recommendations.

Dashboard Features:
- Real-time performance metrics
- Interactive performance charts
- Alert management and trending
- Optimization recommendations
- Business impact analysis
- Jorge methodology effectiveness tracking

Performance KPIs:
- Response Time: <500ms target
- Stall Detection: 91.3% accuracy target
- Re-engagement Rate: 78.5% target
- Property Matching: 89.7% accuracy target
- Memory Usage: <50MB per conversation
- Concurrent Conversations: 100+ supported

Author: Claude Code Assistant - Jorge Performance Engineering
Date: 2026-01-25
Version: 1.0.0
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# Jorge performance monitoring imports (mock for demo)
try:
    from ghl_real_estate_ai.services.jorge_optimization_engine import JorgeOptimizationEngine
    from ghl_real_estate_ai.services.jorge_performance_monitor import (
        AlertLevel,
        JorgeMetricType,
        JorgePerformanceMonitor,
    )

    JORGE_SERVICES_AVAILABLE = True
except ImportError:
    JORGE_SERVICES_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Jorge Performance Dashboard", page_icon="🎯", layout="wide", initial_sidebar_state="expanded"
)

# Custom CSS for performance dashboard
st.markdown(
    """
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .critical-alert {
        background-color: #ffebee;
        border-left-color: #f44336;
    }
    .warning-alert {
        background-color: #fff3e0;
        border-left-color: #ff9800;
    }
    .success-metric {
        border-left-color: #4caf50;
        background-color: #e8f5e8;
    }
    .performance-score {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
    }
    .trend-up {
        color: #4caf50;
    }
    .trend-down {
        color: #f44336;
    }
    .trend-stable {
        color: #ff9800;
    }
</style>
""",
    unsafe_allow_html=True,
)


class JorgePerformanceDashboard:
    """Jorge Bot Performance Dashboard"""

    def __init__(self):
        self.monitor = self._initialize_monitor()
        self.optimization_engine = self._initialize_optimization_engine()
        self.mock_data_enabled = not JORGE_SERVICES_AVAILABLE

    def _initialize_monitor(self):
        """Initialize performance monitor"""
        if JORGE_SERVICES_AVAILABLE:
            return JorgePerformanceMonitor()
        return None

    def _initialize_optimization_engine(self):
        """Initialize optimization engine"""
        if JORGE_SERVICES_AVAILABLE and self.monitor:
            return JorgeOptimizationEngine(self.monitor)
        return None

    def run_dashboard(self):
        """Run the main dashboard"""
        st.title("🎯 Jorge Bot Performance Dashboard")
        st.markdown("**Real-time monitoring for Jorge's specialized real estate AI bots**")

        # Sidebar controls
        with st.sidebar:
            st.header("⚙️ Dashboard Controls")

            # Time range selection
            time_range = st.selectbox(
                "Time Range", ["Last Hour", "Last 4 Hours", "Last 24 Hours", "Last 7 Days"], index=2
            )

            # Bot type filter
            bot_types = st.multiselect(
                "Bot Types", ["Seller Bot", "Lead Bot", "Buyer Bot"], default=["Seller Bot", "Lead Bot", "Buyer Bot"]
            )

            # Auto-refresh
            auto_refresh = st.checkbox("Auto-refresh (30s)", value=True)

            # Performance targets toggle
            show_targets = st.checkbox("Show Performance Targets", value=True)

            if auto_refresh:
                st.markdown("*Dashboard refreshes every 30 seconds*")

        # Main dashboard content
        col1, col2, col3, col4 = st.columns(4)

        # Performance overview metrics
        with col1:
            self._display_performance_score()

        with col2:
            self._display_active_conversations()

        with col3:
            self._display_alert_summary()

        with col4:
            self._display_system_health()

        st.markdown("---")

        # Performance charts row
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            self._display_response_time_chart(time_range)

        with chart_col2:
            self._display_accuracy_metrics_chart()

        st.markdown("---")

        # Second row of charts
        chart_col3, chart_col4 = st.columns(2)

        with chart_col3:
            self._display_memory_usage_chart(time_range)

        with chart_col4:
            self._display_business_metrics_chart()

        st.markdown("---")

        # Detailed sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            [
                "🚨 Alerts & Issues",
                "📊 Detailed Metrics",
                "⚡ Optimization",
                "💼 Business Impact",
                "🔧 Jorge Methodology",
            ]
        )

        with tab1:
            self._display_alerts_section()

        with tab2:
            self._display_detailed_metrics()

        with tab3:
            self._display_optimization_section()

        with tab4:
            self._display_business_impact()

        with tab5:
            self._display_jorge_methodology()

        # Auto-refresh functionality
        if auto_refresh:
            time.sleep(30)
            st.rerun()

    def _display_performance_score(self):
        """Display overall performance score"""
        st.markdown("### 🎯 Performance Score")

        # Mock performance score calculation
        score = self._get_performance_score()
        score_color = "#4caf50" if score >= 85 else "#ff9800" if score >= 70 else "#f44336"

        st.markdown(
            f"""
        <div class="performance-score" style="color: {score_color};">
            {score:.1f}/100
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Score components
        components = self._get_score_components()
        for component, value in components.items():
            trend = "↗️" if value > 80 else "↘️" if value < 60 else "➡️"
            st.metric(component, f"{value:.1f}%", trend)

    def _display_active_conversations(self):
        """Display active conversations metric"""
        st.markdown("### 💬 Active Conversations")

        active_count = self._get_active_conversations_count()
        max_capacity = 100  # Target capacity

        utilization = (active_count / max_capacity) * 100
        utilization_color = "#4caf50" if utilization < 70 else "#ff9800" if utilization < 85 else "#f44336"

        st.markdown(
            f"""
        <div class="metric-card">
            <h2 style="margin: 0; color: {utilization_color};">{active_count}</h2>
            <p style="margin: 0;">of {max_capacity} capacity</p>
            <p style="margin: 0; font-size: 0.9em; color: {utilization_color};">
                {utilization:.1f}% utilization
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Conversation breakdown by bot type
        conversation_breakdown = self._get_conversation_breakdown()
        for bot_type, count in conversation_breakdown.items():
            st.metric(f"{bot_type}", count)

    def _display_alert_summary(self):
        """Display alert summary"""
        st.markdown("### 🚨 Alert Summary")

        alerts = self._get_current_alerts()

        # Alert counts by severity
        critical_count = len([a for a in alerts if a.get("level") == "critical"])
        warning_count = len([a for a in alerts if a.get("level") == "warning"])

        # Critical alerts
        if critical_count > 0:
            st.markdown(
                f"""
            <div class="metric-card critical-alert">
                <h3 style="margin: 0; color: #f44336;">{critical_count}</h3>
                <p style="margin: 0;">Critical Alerts</p>
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
            <div class="metric-card success-metric">
                <h3 style="margin: 0; color: #4caf50;">0</h3>
                <p style="margin: 0;">Critical Alerts</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

        # Warning alerts
        st.markdown(
            f"""
        <div class="metric-card warning-alert">
            <h3 style="margin: 0; color: #ff9800;">{warning_count}</h3>
            <p style="margin: 0;">Warning Alerts</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _display_system_health(self):
        """Display system health metrics"""
        st.markdown("### 🖥️ System Health")

        health_metrics = self._get_system_health()

        # Memory usage
        memory_percent = health_metrics.get("memory_percent", 65)
        memory_color = "#4caf50" if memory_percent < 70 else "#ff9800" if memory_percent < 85 else "#f44336"

        st.markdown(
            f"""
        <div class="metric-card" style="border-left-color: {memory_color};">
            <h4 style="margin: 0;">Memory Usage</h4>
            <p style="margin: 0; color: {memory_color}; font-weight: bold;">
                {memory_percent:.1f}%
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # CPU usage
        cpu_percent = health_metrics.get("cpu_percent", 45)
        cpu_color = "#4caf50" if cpu_percent < 70 else "#ff9800" if cpu_percent < 85 else "#f44336"

        st.metric("CPU Usage", f"{cpu_percent:.1f}%", f"{cpu_percent - 40:.1f}%")

        # Cache hit rate
        cache_hit_rate = health_metrics.get("cache_hit_rate", 0.87)
        st.metric("Cache Hit Rate", f"{cache_hit_rate:.1%}", f"{(cache_hit_rate - 0.80) * 100:.1f}%")

    def _display_response_time_chart(self, time_range: str):
        """Display response time performance chart"""
        st.markdown("### ⚡ Response Time Performance")

        # Generate mock time series data
        times, response_times = self._generate_response_time_data(time_range)

        # Create chart
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=times,
                y=response_times,
                mode="lines+markers",
                name="Response Time",
                line=dict(color="#1f77b4", width=2),
                marker=dict(size=4),
            )
        )

        # Add target line
        target_line = [500] * len(times)  # 500ms target
        fig.add_trace(
            go.Scatter(
                x=times,
                y=target_line,
                mode="lines",
                name="Target (500ms)",
                line=dict(color="#ff7f0e", width=2, dash="dash"),
            )
        )

        fig.update_layout(
            title="Average Response Time",
            xaxis_title="Time",
            yaxis_title="Response Time (ms)",
            height=400,
            showlegend=True,
            hovermode="x unified",
        )

        st.plotly_chart(fig, use_container_width=True)

        # Summary statistics
        avg_response = np.mean(response_times)
        p95_response = np.percentile(response_times, 95)
        target_met = avg_response < 500

        col1, col2, col3 = st.columns(3)
        col1.metric("Average", f"{avg_response:.1f}ms", f"{avg_response - 400:.1f}ms")
        col2.metric("95th Percentile", f"{p95_response:.1f}ms")
        col3.metric("Target Met", "✅" if target_met else "❌", "500ms target")

    def _display_accuracy_metrics_chart(self):
        """Display accuracy metrics chart"""
        st.markdown("### 🎯 Accuracy Metrics")

        # Mock accuracy data
        accuracy_data = {
            "Stall Detection": {"current": 89.5, "target": 91.3},
            "Re-engagement": {"current": 76.8, "target": 78.5},
            "Property Matching": {"current": 92.1, "target": 89.7},
            "Close Rate Improvement": {"current": 65.3, "target": 67.8},
        }

        metrics = list(accuracy_data.keys())
        current_values = [accuracy_data[m]["current"] for m in metrics]
        target_values = [accuracy_data[m]["target"] for m in metrics]

        fig = go.Figure()

        # Current performance bars
        fig.add_trace(
            go.Bar(
                x=metrics,
                y=current_values,
                name="Current",
                marker_color="#1f77b4",
                text=[f"{v:.1f}%" for v in current_values],
                textposition="auto",
            )
        )

        # Target lines
        fig.add_trace(
            go.Scatter(
                x=metrics,
                y=target_values,
                mode="markers+lines",
                name="Target",
                marker=dict(color="#ff7f0e", size=8, symbol="diamond"),
                line=dict(color="#ff7f0e", width=2, dash="dash"),
            )
        )

        fig.update_layout(
            title="Jorge Bot Accuracy Metrics vs Targets", yaxis_title="Accuracy (%)", height=400, showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

    def _display_memory_usage_chart(self, time_range: str):
        """Display memory usage chart"""
        st.markdown("### 💾 Memory Usage")

        times, memory_usage = self._generate_memory_usage_data(time_range)

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=times,
                y=memory_usage,
                mode="lines+markers",
                name="Memory per Conversation",
                fill="tonexty",
                line=dict(color="#2ca02c", width=2),
                marker=dict(size=4),
            )
        )

        # Target line
        target_line = [50] * len(times)  # 50MB target
        fig.add_trace(
            go.Scatter(
                x=times,
                y=target_line,
                mode="lines",
                name="Target (50MB)",
                line=dict(color="#d62728", width=2, dash="dash"),
            )
        )

        fig.update_layout(
            title="Memory Usage per Conversation",
            xaxis_title="Time",
            yaxis_title="Memory (MB)",
            height=400,
            showlegend=True,
        )

        st.plotly_chart(fig, use_container_width=True)

    def _display_business_metrics_chart(self):
        """Display business impact metrics"""
        st.markdown("### 💼 Business Impact")

        # Mock business metrics
        metrics_data = {
            "Qualified Leads/Hour": 8.2,
            "Deals Closed/Day": 2.1,
            "Revenue Attribution": 94.5,
            "Customer Satisfaction": 87.3,
        }

        # Create gauge charts
        fig = make_subplots(
            rows=2,
            cols=2,
            specs=[[{"type": "indicator"}, {"type": "indicator"}], [{"type": "indicator"}, {"type": "indicator"}]],
            subplot_titles=list(metrics_data.keys()),
        )

        positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

        for i, (metric, value) in enumerate(metrics_data.items()):
            row, col = positions[i]

            if "Hour" in metric:
                max_val, suffix = 15, ""
            elif "Day" in metric:
                max_val, suffix = 5, ""
            else:
                max_val, suffix = 100, "%"

            fig.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=value,
                    ontario_mills={"x": [0, 1], "y": [0, 1]},
                    title={"text": metric},
                    number={"suffix": suffix},
                    gauge={
                        "axis": {"range": [None, max_val]},
                        "bar": {"color": colors[i]},
                        "steps": [
                            {"range": [0, max_val * 0.5], "color": "lightgray"},
                            {"range": [max_val * 0.5, max_val * 0.8], "color": "gray"},
                        ],
                        "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": max_val * 0.9},
                    },
                ),
                row=row,
                col=col,
            )

        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)

    def _display_alerts_section(self):
        """Display detailed alerts section"""
        st.markdown("## 🚨 Active Alerts & Issues")

        alerts = self._get_current_alerts()

        if not alerts:
            st.success("🎉 No active alerts! All systems performing within targets.")
            return

        # Group alerts by severity
        critical_alerts = [a for a in alerts if a["level"] == "critical"]
        warning_alerts = [a for a in alerts if a["level"] == "warning"]

        # Critical alerts
        if critical_alerts:
            st.markdown("### 🔴 Critical Alerts")
            for alert in critical_alerts:
                with st.expander(f"🚨 {alert['title']}", expanded=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**Description:** {alert['description']}")
                        st.markdown(f"**Impact:** {alert['impact']}")
                        st.markdown(f"**Recommendation:** {alert['recommendation']}")
                    with col2:
                        st.metric("Current Value", alert["current_value"])
                        st.metric("Threshold", alert["threshold"])
                        if st.button(f"Acknowledge", key=f"ack_{alert['id']}"):
                            st.success("Alert acknowledged!")

        # Warning alerts
        if warning_alerts:
            st.markdown("### 🟡 Warning Alerts")
            for alert in warning_alerts:
                with st.expander(f"⚠️ {alert['title']}"):
                    st.markdown(f"**Description:** {alert['description']}")
                    st.markdown(f"**Recommendation:** {alert['recommendation']}")

    def _display_detailed_metrics(self):
        """Display detailed performance metrics"""
        st.markdown("## 📊 Detailed Performance Metrics")

        # Create tabs for different metric categories
        metric_tab1, metric_tab2, metric_tab3 = st.tabs(["Response Time", "Accuracy", "System Performance"])

        with metric_tab1:
            self._display_response_time_details()

        with metric_tab2:
            self._display_accuracy_details()

        with metric_tab3:
            self._display_system_performance_details()

    def _display_optimization_section(self):
        """Display optimization recommendations"""
        st.markdown("## ⚡ Performance Optimization")

        # Optimization status
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Active Optimizations", 3, "2 completed this week")

        with col2:
            st.metric("Performance Improvement", "+18.5%", "Since last month")

        with col3:
            st.metric("Next Review", "2 days", "Scheduled optimization cycle")

        st.markdown("---")

        # Optimization recommendations
        st.markdown("### 🎯 Optimization Recommendations")

        recommendations = self._get_optimization_recommendations()

        for i, rec in enumerate(recommendations):
            priority_color = {"critical": "#f44336", "high": "#ff9800", "medium": "#2196f3", "low": "#4caf50"}.get(
                rec["priority"], "#666"
            )

            with st.expander(f"{rec['priority'].upper()} - {rec['title']}", expanded=(rec["priority"] == "critical")):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**Description:** {rec['description']}")
                    st.markdown(f"**Expected Improvement:** {rec['expected_improvement']}")
                    st.markdown(f"**Implementation Steps:**")
                    for step in rec["implementation_steps"]:
                        st.markdown(f"- {step}")

                with col2:
                    st.markdown(f"**Priority:** `{rec['priority'].upper()}`")
                    st.markdown(f"**Effort:** {rec['effort']}")
                    st.markdown(f"**Timeline:** {rec['timeline']}")

                    if st.button(f"Implement", key=f"implement_{i}"):
                        st.info("Implementation scheduled!")

    def _display_business_impact(self):
        """Display business impact analysis"""
        st.markdown("## 💼 Business Impact Analysis")

        # Revenue impact
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 💰 Revenue Attribution")

            revenue_data = {
                "Direct Revenue": 125000,
                "Pipeline Value": 245000,
                "Qualified Leads": 85,
                "Closed Deals": 12,
            }

            for metric, value in revenue_data.items():
                if "Revenue" in metric or "Value" in metric:
                    st.metric(metric, f"${value:,}", f"+{(value * 0.15):,.0f}")
                else:
                    st.metric(metric, value, f"+{int(value * 0.12)}")

        with col2:
            st.markdown("### 📈 Performance Trends")

            # Mock trend data
            trend_data = pd.DataFrame(
                {
                    "Week": ["Week 1", "Week 2", "Week 3", "Week 4"],
                    "Qualified Leads": [18, 22, 28, 32],
                    "Close Rate": [12.5, 15.2, 18.7, 21.3],
                    "Revenue": [45000, 52000, 68000, 75000],
                }
            )

            fig = px.line(trend_data, x="Week", y=["Qualified Leads", "Close Rate"], title="Weekly Performance Trends")
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # ROI Analysis
        st.markdown("### 📊 Jorge Methodology ROI Analysis")

        roi_metrics = {
            "Traditional Approach": {"close_rate": 45.2, "avg_cycle": 28, "leads_per_agent": 120},
            "Jorge Enhanced": {"close_rate": 67.8, "avg_cycle": 19, "leads_per_agent": 185},
            "Improvement": {"close_rate": 50.0, "avg_cycle": -32.1, "leads_per_agent": 54.2},
        }

        col1, col2, col3 = st.columns(3)

        for i, (approach, metrics) in enumerate(roi_metrics.items()):
            with [col1, col2, col3][i]:
                st.markdown(f"#### {approach}")
                for metric, value in metrics.items():
                    if approach == "Improvement":
                        sign = "+" if value > 0 else ""
                        unit = "%" if "rate" in metric else " days" if "cycle" in metric else " leads"
                        color = "green" if value > 0 else "red"
                        st.markdown(f"**{metric.replace('_', ' ').title()}:** :{color}[{sign}{value:.1f}{unit}]")
                    else:
                        unit = "%" if "rate" in metric else " days" if "cycle" in metric else " leads"
                        st.markdown(f"**{metric.replace('_', ' ').title()}:** {value:.1f}{unit}")

    def _display_jorge_methodology(self):
        """Display Jorge methodology analysis"""
        st.markdown("## 🔧 Jorge Methodology Analysis")

        # Methodology effectiveness
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🎯 Confrontational Approach Effectiveness")

            effectiveness_data = {
                "Stall Breaking Success": 89.3,
                "Timeline Pressure Effectiveness": 76.8,
                "Budget Reality Check Impact": 82.1,
                "Decision Acceleration Success": 71.4,
            }

            for technique, effectiveness in effectiveness_data.items():
                progress_color = "#4caf50" if effectiveness > 80 else "#ff9800" if effectiveness > 70 else "#f44336"
                st.markdown(
                    f"""
                **{technique}**
                <div style="background-color: #f0f0f0; border-radius: 5px; padding: 5px;">
                    <div style="background-color: {progress_color}; height: 20px; width: {effectiveness}%;
                         border-radius: 3px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                        {effectiveness:.1f}%
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

        with col2:
            st.markdown("### 📊 Methodology Usage Patterns")

            # Mock usage data
            usage_data = pd.DataFrame(
                {
                    "Intervention Type": [
                        "Timeline Pressure",
                        "Budget Reality",
                        "Decision Acceleration",
                        "Competitive Urgency",
                    ],
                    "Usage Frequency": [45, 38, 29, 22],
                    "Success Rate": [76.8, 82.1, 71.4, 68.9],
                }
            )

            fig = px.scatter(
                usage_data,
                x="Usage Frequency",
                y="Success Rate",
                size="Usage Frequency",
                text="Intervention Type",
                title="Intervention Effectiveness vs Usage",
            )
            fig.update_traces(textposition="top center")
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # Compliance and quality
        st.markdown("### ⚖️ Compliance & Quality Assurance")

        compliance_col1, compliance_col2, compliance_col3 = st.columns(3)

        with compliance_col1:
            st.metric("Fair Housing Compliance", "100%", "0 violations")

        with compliance_col2:
            st.metric("DRE Regulation Adherence", "98.7%", "+2.3%")

        with compliance_col3:
            st.metric("Professional Boundary Score", "95.4%", "+1.8%")

        # Recent methodology updates
        st.markdown("### 🔄 Recent Methodology Updates")

        updates = [
            {
                "date": "2026-01-20",
                "update": "Enhanced stall detection patterns for Rancho Cucamonga market",
                "impact": "+5.2% stall detection accuracy",
            },
            {
                "date": "2026-01-18",
                "update": "Refined confrontational intensity levels",
                "impact": "+3.8% intervention success rate",
            },
            {
                "date": "2026-01-15",
                "update": "Added compliance safeguards for aggressive tactics",
                "impact": "100% compliance maintenance",
            },
        ]

        for update in updates:
            st.markdown(f"""
            **{update["date"]}** - {update["update"]}
            - *Impact: {update["impact"]}*
            """)

    # Helper methods for mock data generation
    def _get_performance_score(self) -> float:
        """Get overall performance score"""
        return 82.3

    def _get_score_components(self) -> Dict[str, float]:
        """Get performance score components"""
        return {"Response Time": 78.5, "Accuracy": 87.2, "System Health": 91.4, "Business Impact": 84.1}

    def _get_active_conversations_count(self) -> int:
        """Get active conversations count"""
        return 67

    def _get_conversation_breakdown(self) -> Dict[str, int]:
        """Get conversation breakdown by bot type"""
        return {"Seller Bot": 28, "Lead Bot": 25, "Buyer Bot": 14}

    def _get_current_alerts(self) -> List[Dict[str, Any]]:
        """Get current alerts"""
        return [
            {
                "id": "alert_001",
                "level": "warning",
                "title": "Response Time Above Average",
                "description": "Average response time has increased to 485ms over the last hour",
                "current_value": "485ms",
                "threshold": "500ms",
                "impact": "User experience degradation",
                "recommendation": "Enable response caching for common patterns",
            },
            {
                "id": "alert_002",
                "level": "critical",
                "title": "Stall Detection Accuracy Below Target",
                "description": "Stall detection accuracy dropped to 87.2%, below 91.3% target",
                "current_value": "87.2%",
                "threshold": "91.3%",
                "impact": "Missed intervention opportunities",
                "recommendation": "Review and retrain stall detection patterns",
            },
        ]

    def _get_system_health(self) -> Dict[str, float]:
        """Get system health metrics"""
        return {"memory_percent": 67.8, "cpu_percent": 45.2, "cache_hit_rate": 0.87}

    def _generate_response_time_data(self, time_range: str) -> Tuple[List[datetime], List[float]]:
        """Generate mock response time data"""
        hours = {"Last Hour": 1, "Last 4 Hours": 4, "Last 24 Hours": 24, "Last 7 Days": 168}[time_range]

        # Generate time points
        now = datetime.now()
        times = [now - timedelta(hours=i) for i in range(hours, 0, -1)]

        # Generate response times with some variation
        base_time = 450
        response_times = []
        for i in range(len(times)):
            # Add some realistic variation
            variation = np.sin(i * 0.1) * 50 + np.random.normal(0, 30)
            response_time = max(200, base_time + variation)
            response_times.append(response_time)

        return times, response_times

    def _generate_memory_usage_data(self, time_range: str) -> Tuple[List[datetime], List[float]]:
        """Generate mock memory usage data"""
        hours = {"Last Hour": 1, "Last 4 Hours": 4, "Last 24 Hours": 24, "Last 7 Days": 168}[time_range]

        now = datetime.now()
        times = [now - timedelta(hours=i) for i in range(hours, 0, -1)]

        # Generate memory usage with gradual increase
        memory_usage = []
        for i in range(len(times)):
            base_memory = 42
            growth = i * 0.1  # Gradual memory growth
            variation = np.random.normal(0, 3)
            memory = max(25, base_memory + growth + variation)
            memory_usage.append(memory)

        return times, memory_usage

    def _get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get optimization recommendations"""
        return [
            {
                "priority": "critical",
                "title": "Response Time Optimization",
                "description": "Implement caching and async processing to reduce response times",
                "expected_improvement": "25-40% response time reduction",
                "implementation_steps": [
                    "Enable response caching for common patterns",
                    "Implement async processing for non-critical operations",
                    "Optimize database queries",
                ],
                "effort": "Medium",
                "timeline": "1-2 weeks",
            },
            {
                "priority": "high",
                "title": "Stall Detection Enhancement",
                "description": "Improve stall detection accuracy through pattern refinement",
                "expected_improvement": "5-8% accuracy improvement",
                "implementation_steps": [
                    "Analyze failed stall detection cases",
                    "Enhance pattern recognition algorithms",
                    "Add more conversation context",
                ],
                "effort": "Low",
                "timeline": "3-5 days",
            },
        ]

    def _display_response_time_details(self):
        """Display detailed response time metrics"""
        st.markdown("#### Response Time Breakdown")

        # Mock detailed response time data
        breakdown_data = {"AI Processing": 280, "Database Queries": 95, "Business Logic": 85, "Network Latency": 40}

        # Create pie chart
        fig = px.pie(
            values=list(breakdown_data.values()),
            names=list(breakdown_data.keys()),
            title="Response Time Component Breakdown",
        )
        st.plotly_chart(fig, use_container_width=True)

    def _display_accuracy_details(self):
        """Display detailed accuracy metrics"""
        st.markdown("#### Accuracy Trend Analysis")

        # Mock accuracy trends
        dates = pd.date_range(start="2026-01-18", end="2026-01-25", freq="D")
        accuracy_trends = pd.DataFrame(
            {
                "Date": dates,
                "Stall Detection": np.random.normal(90, 2, len(dates)),
                "Re-engagement": np.random.normal(78, 3, len(dates)),
                "Property Matching": np.random.normal(89, 2, len(dates)),
            }
        )

        fig = px.line(
            accuracy_trends,
            x="Date",
            y=["Stall Detection", "Re-engagement", "Property Matching"],
            title="Accuracy Trends (Last 7 Days)",
        )
        st.plotly_chart(fig, use_container_width=True)

    def _display_system_performance_details(self):
        """Display detailed system performance metrics"""
        st.markdown("#### System Resource Utilization")

        col1, col2 = st.columns(2)

        with col1:
            # Memory usage over time
            times = pd.date_range(start=datetime.now() - timedelta(hours=24), end=datetime.now(), freq="H")
            memory_data = pd.DataFrame({"Time": times, "Memory_MB": np.random.normal(42, 5, len(times))})

            fig = px.line(memory_data, x="Time", y="Memory_MB", title="Memory Usage (24 Hours)")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # CPU usage distribution
            cpu_data = pd.DataFrame({"CPU_Usage": np.random.beta(2, 5, 100) * 100})

            fig = px.histogram(cpu_data, x="CPU_Usage", nbins=20, title="CPU Usage Distribution")
            st.plotly_chart(fig, use_container_width=True)


# Main dashboard execution
def main():
    """Main dashboard function"""
    dashboard = JorgePerformanceDashboard()
    dashboard.run_dashboard()


if __name__ == "__main__":
    main()
