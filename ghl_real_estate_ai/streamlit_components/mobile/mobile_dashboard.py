"""
Mobile Performance Dashboard (Phase 4: Mobile Optimization)

Streamlit dashboard optimized for mobile devices to monitor Claude AI
performance, battery usage, and mobile-specific metrics.

Features:
- Touch-optimized interface
- Real-time performance metrics
- Mobile-specific visualizations
- Battery and data usage tracking
- Performance optimization suggestions
- Alert management
- Quick action buttons
- Responsive design for mobile screens

Performance Targets:
- Dashboard load time: <100ms
- Real-time updates: <50ms
- Touch response: <30ms
- Mobile viewport optimization: 100%
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import json
import asyncio

# Local imports
from ghl_real_estate_ai.services.mobile_performance_monitor import (
    MobilePerformanceMonitor,
    MetricType,
    AlertLevel,
    PerformanceMetric
)

# Initialize performance monitor
if "performance_monitor" not in st.session_state:
    st.session_state.performance_monitor = MobilePerformanceMonitor()

performance_monitor = st.session_state.performance_monitor


class MobileDashboard:
    """
    📱 Mobile Performance Dashboard

    Touch-optimized dashboard for monitoring Claude AI performance
    on mobile devices with real-time metrics and optimization suggestions.
    """

    def __init__(self):
        self.monitor = performance_monitor

        # Mobile-optimized styling
        self._apply_mobile_styles()

    def _apply_mobile_styles(self):
        """Apply mobile-optimized CSS styles"""
        st.markdown("""
        <style>
        /* Mobile-First Responsive Design */
        .main > div {
            padding: 0.5rem !important;
        }

        /* Touch-Friendly Buttons */
        .stButton > button {
            height: 3rem !important;
            font-size: 1.1rem !important;
            border-radius: 8px !important;
            margin: 0.25rem 0 !important;
        }

        /* Mobile-Optimized Metrics */
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
            color: white;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            margin: 0.5rem 0;
        }

        .metric-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }

        /* Alert Styling */
        .alert-critical {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        }

        .alert-warning {
            background: linear-gradient(135deg, #feca57 0%, #ff9ff3 100%);
        }

        .alert-info {
            background: linear-gradient(135deg, #54a0ff 0%, #5f27cd 100%);
        }

        /* Mobile Chart Containers */
        .plotly-chart {
            height: 300px !important;
        }

        /* Quick Action Buttons */
        .quick-action {
            display: inline-block;
            padding: 0.75rem 1.5rem;
            background: #4CAF50;
            color: white;
            border-radius: 25px;
            margin: 0.25rem;
            text-align: center;
            font-weight: bold;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }

        /* Battery Indicator */
        .battery-indicator {
            width: 60px;
            height: 30px;
            border: 2px solid #333;
            border-radius: 4px;
            position: relative;
            display: inline-block;
            margin-left: 10px;
        }

        .battery-level {
            height: 100%;
            border-radius: 2px;
            transition: width 0.3s ease;
        }

        .battery-high { background: #4CAF50; }
        .battery-medium { background: #FFC107; }
        .battery-low { background: #f44336; }

        /* Responsive Text */
        @media (max-width: 768px) {
            .metric-value { font-size: 1.5rem; }
            h1 { font-size: 1.8rem; }
            h2 { font-size: 1.4rem; }
            h3 { font-size: 1.2rem; }
        }
        </style>
        """, unsafe_allow_html=True)

    def render(self):
        """Render the mobile dashboard"""
        # Mobile-optimized header
        st.markdown("# 📱 Claude AI Mobile Dashboard")

        # Check if we have any agent data
        if not self.monitor.agent_profiles:
            self._render_empty_state()
            return

        # Mobile navigation tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "⚡ Performance", "🔋 Battery", "🚨 Alerts"])

        with tab1:
            self._render_overview_tab()

        with tab2:
            self._render_performance_tab()

        with tab3:
            self._render_battery_tab()

        with tab4:
            self._render_alerts_tab()

        # Quick actions footer
        self._render_quick_actions()

    def _render_empty_state(self):
        """Render empty state when no data is available"""
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h2>🚀 Getting Started</h2>
            <p>No performance data available yet. Start using Claude AI on mobile to see metrics here!</p>
            <div class="quick-action">
                Start Mobile Session
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Demo data button for testing
        if st.button("📊 Generate Demo Data", use_container_width=True):
            self._generate_demo_data()
            st.rerun()

    def _render_overview_tab(self):
        """Render system overview tab"""
        overview = self.monitor.get_system_performance_overview()

        # System health cards
        col1, col2, col3 = st.columns(3)

        with col1:
            total_agents = overview["system_health"]["total_agents"]
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total_agents}</div>
                <div class="metric-label">Active Agents</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            avg_score = overview["system_health"]["average_performance_score"]
            score_color = "alert-critical" if avg_score < 60 else "alert-warning" if avg_score < 80 else ""
            st.markdown(f"""
            <div class="metric-card {score_color}">
                <div class="metric-value">{avg_score:.1f}%</div>
                <div class="metric-label">Performance Score</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            active_alerts = overview["alerts"]["total_active"]
            alert_color = "alert-critical" if active_alerts > 5 else "alert-warning" if active_alerts > 0 else ""
            st.markdown(f"""
            <div class="metric-card {alert_color}">
                <div class="metric-value">{active_alerts}</div>
                <div class="metric-label">Active Alerts</div>
            </div>
            """, unsafe_allow_html=True)

        # Agent health breakdown
        st.markdown("### 📈 Agent Health Breakdown")
        health_data = overview["system_health"]

        fig = go.Figure(data=[
            go.Bar(
                x=['Healthy', 'Degraded', 'Critical'],
                y=[health_data["healthy_agents"], health_data["degraded_agents"], health_data["critical_agents"]],
                marker_color=['#4CAF50', '#FFC107', '#f44336']
            )
        ])

        fig.update_layout(
            title="Agent Performance Distribution",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Recent performance trends
        self._render_performance_trends()

    def _render_performance_tab(self):
        """Render performance metrics tab"""
        st.markdown("### ⚡ Performance Metrics")

        # Agent selector for mobile
        agent_ids = list(self.monitor.agent_profiles.keys())
        if not agent_ids:
            st.info("No agent data available")
            return

        selected_agent = st.selectbox(
            "Select Agent",
            agent_ids,
            key="performance_agent_selector"
        )

        if selected_agent:
            agent_summary = self.monitor.get_agent_performance_summary(selected_agent)

            # Performance score gauge
            performance_score = agent_summary["performance_score"]
            self._render_performance_gauge(performance_score)

            # Key metrics grid
            recent_performance = agent_summary.get("recent_performance", {})

            if recent_performance:
                st.markdown("### 📊 Key Metrics")

                # Create two columns for metrics
                col1, col2 = st.columns(2)

                metrics_displayed = 0
                for metric_name, metric_data in recent_performance.items():
                    if metrics_displayed >= 4:  # Limit for mobile
                        break

                    current_value = metric_data["current"]
                    average_value = metric_data["average"]

                    # Determine target column
                    col = col1 if metrics_displayed % 2 == 0 else col2

                    with col:
                        # Color coding based on performance
                        color_class = self._get_metric_color_class(metric_name, current_value)

                        st.markdown(f"""
                        <div class="metric-card {color_class}">
                            <div class="metric-value">{current_value:.1f}</div>
                            <div class="metric-label">{metric_name.replace('_', ' ').title()}</div>
                            <div style="font-size: 0.8rem;">Avg: {average_value:.1f}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    metrics_displayed += 1

            # Performance history chart
            self._render_performance_history(selected_agent)

    def _render_battery_tab(self):
        """Render battery optimization tab"""
        st.markdown("### 🔋 Battery Optimization")

        # Battery usage overview
        battery_metrics = [
            m for m in self.monitor.metrics[MetricType.BATTERY_USAGE]
            if m.timestamp > datetime.now() - timedelta(hours=1)
        ]

        if battery_metrics:
            # Current battery usage
            latest_metric = battery_metrics[-1]
            current_usage = latest_metric.value
            current_battery = latest_metric.context.get("current_battery_level", 75)

            # Battery indicator
            self._render_battery_indicator(current_battery, current_usage)

            # Battery usage chart
            self._render_battery_usage_chart(battery_metrics)

            # Battery optimization recommendations
            self._render_battery_recommendations()

        else:
            st.info("No battery data available. Battery monitoring will appear here once mobile sessions begin.")

    def _render_alerts_tab(self):
        """Render alerts and notifications tab"""
        st.markdown("### 🚨 Performance Alerts")

        active_alerts = self.monitor.active_alerts

        if not active_alerts:
            st.success("✅ No active alerts - System running smoothly!")
            return

        # Group alerts by level
        alert_groups = {"critical": [], "warning": [], "info": []}

        for alert in active_alerts:
            if alert.level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]:
                alert_groups["critical"].append(alert)
            elif alert.level == AlertLevel.WARNING:
                alert_groups["warning"].append(alert)
            else:
                alert_groups["info"].append(alert)

        # Render alert groups
        for level, alerts in alert_groups.items():
            if alerts:
                st.markdown(f"#### {level.title()} Alerts")

                for alert in alerts:
                    self._render_alert_card(alert)

    def _render_performance_gauge(self, score: float):
        """Render performance score gauge"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            title={'text': "Performance Score"},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={'axis': {'range': [None, 100]},
                   'bar': {'color': self._get_gauge_color(score)},
                   'steps': [
                       {'range': [0, 60], 'color': "lightgray"},
                       {'range': [60, 80], 'color': "yellow"},
                       {'range': [80, 100], 'color': "lightgreen"}],
                   'threshold': {'line': {'color': "red", 'width': 4},
                                'thickness': 0.75, 'value': 90}}
        ))

        fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

    def _render_battery_indicator(self, battery_level: float, usage_rate: float):
        """Render battery indicator with usage rate"""
        battery_class = "battery-high"
        if battery_level < 20:
            battery_class = "battery-low"
        elif battery_level < 50:
            battery_class = "battery-medium"

        usage_color = "#4CAF50" if usage_rate < 5 else "#FFC107" if usage_rate < 10 else "#f44336"

        st.markdown(f"""
        <div style="text-align: center; padding: 1rem;">
            <h3>Battery Status</h3>
            <div style="display: flex; justify-content: center; align-items: center;">
                <div class="battery-indicator">
                    <div class="battery-level {battery_class}" style="width: {battery_level}%;"></div>
                </div>
                <span style="margin-left: 1rem; font-size: 1.5rem; font-weight: bold;">
                    {battery_level:.0f}%
                </span>
            </div>
            <div style="margin-top: 1rem;">
                <div style="color: {usage_color}; font-size: 1.2rem;">
                    Usage Rate: {usage_rate:.1f}%/hour
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    def _render_performance_trends(self):
        """Render performance trends chart"""
        st.markdown("### 📈 Performance Trends")

        # Get recent metrics for trending
        recent_metrics = {}
        for metric_type in [MetricType.RESPONSE_TIME, MetricType.VOICE_PROCESSING]:
            metrics = [
                m for m in self.monitor.metrics[metric_type]
                if m.timestamp > datetime.now() - timedelta(hours=1)
            ]

            if metrics:
                # Group by 5-minute intervals
                df_data = []
                for metric in metrics:
                    df_data.append({
                        'timestamp': metric.timestamp,
                        'value': metric.value,
                        'type': metric_type.value
                    })

                if df_data:
                    recent_metrics[metric_type.value] = df_data

        if recent_metrics:
            # Create trends chart
            fig = make_subplots(
                rows=len(recent_metrics), cols=1,
                subplot_titles=list(recent_metrics.keys()),
                vertical_spacing=0.1
            )

            row = 1
            for metric_name, data in recent_metrics.items():
                df = pd.DataFrame(data)

                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=df['value'],
                        mode='lines+markers',
                        name=metric_name,
                        line=dict(width=2)
                    ),
                    row=row, col=1
                )
                row += 1

            fig.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

    def _render_performance_history(self, agent_id: str):
        """Render performance history for selected agent"""
        st.markdown("### 📊 Performance History")

        # Get metrics for this agent
        agent_metrics = {}
        for metric_type in MetricType:
            metrics = [
                m for m in self.monitor.metrics[metric_type]
                if m.agent_id == agent_id and
                m.timestamp > datetime.now() - timedelta(hours=2)
            ]

            if metrics:
                agent_metrics[metric_type.value] = metrics

        if not agent_metrics:
            st.info("No recent performance history available for this agent.")
            return

        # Create performance history chart
        fig = go.Figure()

        colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336']
        color_idx = 0

        for metric_name, metrics in agent_metrics.items():
            if color_idx >= len(colors):
                break

            timestamps = [m.timestamp for m in metrics]
            values = [m.value for m in metrics]

            fig.add_trace(go.Scatter(
                x=timestamps,
                y=values,
                mode='lines+markers',
                name=metric_name.replace('_', ' ').title(),
                line=dict(color=colors[color_idx], width=2)
            ))

            color_idx += 1

        fig.update_layout(
            title="Performance History (Last 2 Hours)",
            xaxis_title="Time",
            yaxis_title="Value",
            height=350,
            margin=dict(l=20, r=20, t=40, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_battery_usage_chart(self, battery_metrics: List[PerformanceMetric]):
        """Render battery usage chart"""
        st.markdown("#### 📊 Battery Usage Over Time")

        timestamps = [m.timestamp for m in battery_metrics]
        usage_values = [m.value for m in battery_metrics]
        battery_levels = [m.context.get("current_battery_level", 75) for m in battery_metrics]

        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Battery Level (%)", "Usage Rate (%/hour)"),
            vertical_spacing=0.1
        )

        # Battery level
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=battery_levels,
                mode='lines+markers',
                name='Battery Level',
                line=dict(color='#4CAF50', width=3),
                fill='tonexty'
            ),
            row=1, col=1
        )

        # Usage rate
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=usage_values,
                mode='lines+markers',
                name='Usage Rate',
                line=dict(color='#FF9800', width=2)
            ),
            row=2, col=1
        )

        fig.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

    def _render_battery_recommendations(self):
        """Render battery optimization recommendations"""
        st.markdown("#### 💡 Battery Optimization Tips")

        recommendations = [
            {
                "icon": "🔋",
                "title": "Enable Battery Saver Mode",
                "description": "Reduces Claude AI processing frequency",
                "action": "Enable Now"
            },
            {
                "icon": "📱",
                "title": "Use Offline Coaching",
                "description": "Switch to cached coaching suggestions",
                "action": "Switch Mode"
            },
            {
                "icon": "⚙️",
                "title": "Reduce Voice Processing",
                "description": "Lower audio quality for longer battery life",
                "action": "Adjust Settings"
            }
        ]

        for rec in recommendations:
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"""
                <div style="padding: 0.5rem;">
                    <span style="font-size: 1.5rem;">{rec['icon']}</span>
                    <strong> {rec['title']}</strong><br>
                    <small style="color: gray;">{rec['description']}</small>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                if st.button(rec['action'], key=f"battery_rec_{rec['title']}", use_container_width=True):
                    st.success(f"{rec['title']} activated!")

    def _render_alert_card(self, alert):
        """Render individual alert card"""
        alert_color = {
            AlertLevel.CRITICAL: "alert-critical",
            AlertLevel.EMERGENCY: "alert-critical",
            AlertLevel.WARNING: "alert-warning",
            AlertLevel.INFO: "alert-info"
        }.get(alert.level, "alert-info")

        recommendations_html = ""
        if alert.recommendations:
            rec_list = "<br>".join([f"• {rec}" for rec in alert.recommendations[:3]])
            recommendations_html = f"<div style='margin-top: 0.5rem; font-size: 0.8rem;'>{rec_list}</div>"

        st.markdown(f"""
        <div class="metric-card {alert_color}">
            <div style="font-weight: bold;">{alert.message}</div>
            <div style="font-size: 0.8rem; margin-top: 0.25rem;">
                {alert.timestamp.strftime('%H:%M:%S')} - Agent: {alert.agent_id}
            </div>
            {recommendations_html}
        </div>
        """, unsafe_allow_html=True)

    def _render_quick_actions(self):
        """Render quick action buttons"""
        st.markdown("---")
        st.markdown("### ⚡ Quick Actions")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.rerun()

        with col2:
            if st.button("💡 Optimize", use_container_width=True):
                st.success("Optimization recommendations updated!")

        with col3:
            if st.button("📊 Export Report", use_container_width=True):
                self._export_performance_report()

    def _get_metric_color_class(self, metric_name: str, value: float) -> str:
        """Get color class based on metric performance"""
        # Define thresholds for different metrics
        thresholds = {
            "response_time": {"critical": 500, "warning": 200},
            "voice_processing": {"critical": 300, "warning": 150},
            "battery_usage": {"critical": 15, "warning": 8},
            "data_usage": {"critical": 50, "warning": 10}
        }

        threshold = thresholds.get(metric_name, {"critical": float('inf'), "warning": float('inf')})

        if value >= threshold["critical"]:
            return "alert-critical"
        elif value >= threshold["warning"]:
            return "alert-warning"
        else:
            return ""

    def _get_gauge_color(self, score: float) -> str:
        """Get gauge color based on score"""
        if score >= 80:
            return "green"
        elif score >= 60:
            return "orange"
        else:
            return "red"

    def _generate_demo_data(self):
        """Generate demo data for testing"""
        import random

        # Generate demo metrics for a test agent
        agent_id = "demo_agent_001"

        # Add some demo metrics
        for i in range(20):
            timestamp_offset = timedelta(minutes=i * 3)
            base_time = datetime.now() - timedelta(hours=1) + timestamp_offset

            # Response time metrics
            self.monitor.record_metric(
                MetricType.RESPONSE_TIME,
                random.uniform(50, 250),
                "ms",
                agent_id,
                context={"request_type": "coaching"}
            )

            # Voice processing metrics
            self.monitor.record_metric(
                MetricType.VOICE_PROCESSING,
                random.uniform(80, 200),
                "ms",
                agent_id,
                context={"audio_quality": random.uniform(0.7, 0.95)}
            )

            # Battery usage
            self.monitor.record_metric(
                MetricType.BATTERY_USAGE,
                random.uniform(3, 12),
                "%/hour",
                agent_id,
                context={"current_battery_level": max(20, 90 - i * 2)}
            )

        st.success("Demo data generated! Refresh to see the metrics.")

    def _export_performance_report(self):
        """Export performance report"""
        # This would generate and download a performance report
        report_data = self.monitor.get_system_performance_overview()

        st.download_button(
            label="📄 Download JSON Report",
            data=json.dumps(report_data, indent=2, default=str),
            file_name=f"mobile_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )


# Function to render the dashboard
def render_mobile_dashboard():
    """Render the mobile dashboard"""
    dashboard = MobileDashboard()
    dashboard.render()


# Main execution for standalone testing
if __name__ == "__main__":
    render_mobile_dashboard()