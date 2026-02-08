"""
Churn Early Warning Dashboard - Real-time Churn Risk Monitoring

This component provides a comprehensive dashboard for monitoring churn risk across
the lead portfolio with real-time alerts, risk distribution analytics, and
intervention tracking capabilities.

Features:
- Real-time churn risk monitoring with automatic refresh
- Risk distribution charts and trend analysis
- High-risk lead priority queue with intervention recommendations
- Intervention effectiveness tracking and analytics
- Predictive insights and early warning alerts
- Agent workload distribution and performance metrics

Author: EnterpriseHub AI
Last Updated: 2026-01-09
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# Component styling and configuration - only when run standalone
if __name__ == "__main__":
    st.set_page_config(
        page_title="Churn Early Warning System", page_icon="⚠️", layout="wide", initial_sidebar_state="expanded"
    )

# Custom CSS for enhanced styling - Obsidian Command Edition
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;700&display=swap');

    /* Global Aesthetic Overrides */
    .stApp {
        background: #05070A;
    }
    
    /* Obsidian Glass Cards */
    .glass-card {
        background: rgba(22, 27, 34, 0.7) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 16px !important;
        padding: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8) !important;
        margin-bottom: 1.5rem;
        color: #E6EDF3;
    }
    
    .metric-card {
        background: rgba(22, 27, 34, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.25rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(99, 102, 241, 0.2);
        border-color: rgba(99, 102, 241, 0.4);
    }

    /* Risk Status Badges - Obsidian Edition */
    .risk-critical-badge {
        background: rgba(220, 38, 38, 0.15);
        color: #ef4444;
        padding: 4px 14px;
        border-radius: 999px;
        font-weight: 700;
        font-size: 0.7rem;
        border: 1px solid rgba(220, 38, 38, 0.3);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .risk-high-badge {
        background: rgba(234, 88, 12, 0.15);
        color: #f97316;
        padding: 4px 14px;
        border-radius: 999px;
        font-weight: 700;
        font-size: 0.7rem;
        border: 1px solid rgba(234, 88, 12, 0.3);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Typography */
    h1, h2, h3, .space-font {
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: -0.03em !important;
        font-weight: 700 !important;
    }
    
    body, p, div {
        font-family: 'Inter', sans-serif;
    }

    /* Alert Banner Overlay */
    .alert-banner {
        background: linear-gradient(90deg, #ef4444 0%, #991b1b 100%);
        color: white;
        padding: 1rem;
        border-radius: 12px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 0 20px rgba(239, 68, 68, 0.3);
        font-family: 'Space Grotesk', sans-serif;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
</style>
""",
    unsafe_allow_html=True,
)


class ChurnEarlyWarningDashboard:
    """Main dashboard class for churn risk monitoring"""

    def __init__(self, claude_assistant=None):
        self.refresh_interval = 300  # 5 minutes
        self.claude = claude_assistant
        self.risk_thresholds = {"critical": 80.0, "high": 60.0, "medium": 30.0, "low": 0.0}

    def render_dashboard(self):
        """Render the complete early warning dashboard"""

        # 1. TACTICAL TOP BAR - Obsidian Edition
        st.markdown(
            """
            <div style="background: rgba(22, 27, 34, 0.85); backdrop-filter: blur(20px); padding: 1.25rem 2.5rem; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 3rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6); position: sticky; top: 1rem; z-index: 1000;">
                <div style="display: flex; align-items: center; gap: 20px;">
                    <div style="background: #6366F1; width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 900; font-size: 1.2rem; box-shadow: 0 0 15px rgba(99, 102, 241, 0.5);">⚠️</div>
                    <span style="font-weight: 700; color: #FFFFFF; letter-spacing: 0.1em; font-size: 1.25rem; font-family: 'Space Grotesk', sans-serif;">RETENTION COMMAND</span>
                </div>
                <div style="display: flex; gap: 15px; align-items: center;">
                    <span style="font-size: 0.75rem; font-weight: 600; color: #8B949E; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">Status:</span>
                    <span style='background: rgba(16, 185, 129, 0.1); color: #10b981; padding: 6px 16px; border-radius: 8px; font-size: 0.7rem; font-weight: 700; border: 1px solid rgba(16, 185, 129, 0.3); letter-spacing: 0.05em;'>LIVE TELEMETRY</span>
                </div>
            </div>
        """,
            unsafe_allow_html=True,
        )

        # 2. FILTERS & AUTO-REFRESH CONTROLS
        self._render_filters_and_controls()

        # PRO-F1: Render Retention Wizard Config Overlay if active
        if st.session_state.get("show_retention_wizard", False):
            self._render_retention_wizard()

        # Load dashboard data with filters
        with st.spinner("Processing behavioral telemetry..."):
            dashboard_data = self._load_dashboard_data()

        # Apply filters to data
        dashboard_data = self._apply_filters(dashboard_data)

        # Main dashboard layout
        self._render_alert_banner(dashboard_data)
        self._render_key_metrics(dashboard_data)

        # Glass Layout Grid
        col1, col2 = st.columns([1.5, 1])

        with col1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### 📉 Risk Velocity & Distribution")
            c_a, c_b = st.columns(2)
            with c_a:
                self._render_risk_distribution_chart(dashboard_data)
            with c_b:
                self._render_risk_trend_analysis(dashboard_data)
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### 🛡️ Intervention Effectiveness")
            self._render_intervention_effectiveness(dashboard_data)
            st.markdown("</div>", unsafe_allow_html=True)

        # High Priority Queue Full Width
        self._render_high_risk_queue(dashboard_data)

        # Detailed Analytics
        st.markdown("---")
        self._render_detailed_analytics(dashboard_data)
        self._render_intervention_tracking(dashboard_data)

    def _render_filters_and_controls(self):
        """Render interactive filters and auto-refresh controls"""
        with st.expander("⚙️ Filters & Controls", expanded=False):
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                # Date range filter
                date_options = ["Last 7 Days", "Last 14 Days", "Last 30 Days", "Last 90 Days"]
                st.selectbox("📅 Date Range", date_options, index=2, key="date_filter")

            with col2:
                # Risk level filter
                risk_options = ["All Leads", "Critical Only", "High+", "Medium+"]
                st.selectbox("🎯 Risk Level", risk_options, index=0, key="risk_filter")

            with col3:
                # Agent filter
                agents = ["All Agents", "Sarah Miller", "Mike Johnson", "Emma Davis", "Alex Chen"]
                st.multiselect("👤 Agents", agents[1:], default=None, key="agent_filter")

            with col4:
                # Auto-refresh toggle
                auto_refresh = st.checkbox("🔄 Auto-Refresh", value=False, key="auto_refresh_toggle")

                if auto_refresh:
                    refresh_options = ["30 seconds", "1 minute", "5 minutes", "15 minutes"]
                    refresh_interval = st.selectbox(
                        "Interval", refresh_options, index=1, key="refresh_interval", label_visibility="collapsed"
                    )

            with col5:
                # Manual refresh and last updated
                if st.button("🔄 Refresh Now", use_container_width=True):
                    st.rerun()

                last_updated = datetime.now().strftime("%H:%M:%S")
                st.caption(f"Last: {last_updated}")

            # Row 2: Advanced Ops
            if "show_retention_wizard" not in st.session_state:
                st.session_state.show_retention_wizard = False

            r2_c1, r2_c2 = st.columns([1, 1])
            with r2_c1:
                # Toggle Wizard
                if st.button(
                    f"{'❌ Close' if st.session_state.show_retention_wizard else '🧙 Strategy Wizard'}",
                    use_container_width=True,
                    type="primary" if not st.session_state.show_retention_wizard else "secondary",
                ):
                    st.session_state.show_retention_wizard = not st.session_state.show_retention_wizard
                    st.rerun()
            with r2_c2:
                st.caption("ℹ️ Data exports available in Detailed Analytics below")

    def _apply_filters(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply user-selected filters to dashboard data"""
        filtered_data = data.copy()

        # Apply risk level filter
        if "risk_filter" in st.session_state:
            risk_filter = st.session_state.risk_filter
            if risk_filter != "All Leads":
                predictions = data["predictions"]
                if risk_filter == "Critical Only":
                    predictions = [p for p in predictions if p["risk_score_14d"] >= 80]
                elif risk_filter == "High+":
                    predictions = [p for p in predictions if p["risk_score_14d"] >= 60]
                elif risk_filter == "Medium+":
                    predictions = [p for p in predictions if p["risk_score_14d"] >= 30]

                filtered_data["predictions"] = predictions
                filtered_data["total_leads"] = len(predictions)
                filtered_data["high_risk_count"] = len([p for p in predictions if p["risk_score_14d"] >= 60])
                filtered_data["critical_alerts"] = len([p for p in predictions if p["risk_score_14d"] >= 80])

        return filtered_data

    def _load_dashboard_data(self) -> Dict[str, Any]:
        """Load and prepare dashboard data"""
        # In production, this would load from actual services
        # For demo purposes, generating realistic sample data

        current_time = datetime.now()

        # Sample churn predictions
        sample_predictions = [
            {
                "lead_id": f"LEAD_{i:04d}",
                "lead_name": f"Client {i}",
                "risk_score_14d": np.random.beta(2, 5) * 100,  # Skewed toward lower scores
                "risk_tier": self._calculate_risk_tier(np.random.beta(2, 5) * 100),
                "confidence": np.random.uniform(0.6, 0.95),
                "last_interaction_days": np.random.exponential(5),
                "predicted_churn_date": current_time + timedelta(days=np.random.uniform(3, 30)),
                "top_risk_factors": [
                    ("days_since_last_interaction", np.random.uniform(0.1, 0.3)),
                    ("response_rate_7d", np.random.uniform(0.1, 0.25)),
                    ("engagement_trend", np.random.uniform(0.05, 0.2)),
                ],
            }
            for i in range(1, 151)  # 150 sample leads
        ]

        # Sample intervention data
        sample_interventions = [
            {
                "execution_id": f"INT_{i:04d}",
                "lead_id": f"LEAD_{np.random.randint(1, 151):04d}",
                "intervention_type": np.random.choice(
                    ["email_reengagement", "sms_urgent", "phone_callback", "property_alert", "agent_escalation"]
                ),
                "status": np.random.choice(["completed", "pending", "failed"], p=[0.7, 0.2, 0.1]),
                "scheduled_time": current_time - timedelta(hours=np.random.uniform(0, 72)),
                "success_metrics": {"engagement_increase": np.random.uniform(0, 30) if np.random.random() > 0.3 else 0},
            }
            for i in range(1, 101)  # 100 sample interventions
        ]

        return {
            "predictions": sample_predictions,
            "interventions": sample_interventions,
            "last_updated": current_time,
            "total_leads": len(sample_predictions),
            "high_risk_count": len([p for p in sample_predictions if p["risk_score_14d"] >= 60]),
            "critical_alerts": len([p for p in sample_predictions if p["risk_score_14d"] >= 80]),
        }

    def _calculate_risk_tier(self, score: float) -> str:
        """Calculate risk tier based on score"""
        if score >= 80:
            return "critical"
        elif score >= 60:
            return "high"
        elif score >= 30:
            return "medium"
        else:
            return "low"

    def _render_alert_banner(self, data: Dict[str, Any]):
        """Render critical alert banner if needed"""
        critical_count = data["critical_alerts"]

        if critical_count > 0:
            st.markdown(
                f'<div class="alert-banner">🚨 CRITICAL ALERT: {critical_count} leads require immediate intervention!</div>',
                unsafe_allow_html=True,
            )

    def _render_key_metrics(self, data: Dict[str, Any]):
        """Render key performance metrics with Premium Cards"""

        predictions = data["predictions"]
        interventions = data["interventions"]

        # Calculate metrics
        total_leads = len(predictions)
        critical_risk = len([p for p in predictions if p["risk_score_14d"] >= 80])
        high_risk = len([p for p in predictions if p["risk_score_14d"] >= 60])
        avg_risk_score = np.mean([p["risk_score_14d"] for p in predictions])

        # Intervention metrics
        completed_interventions = len([i for i in interventions if i["status"] == "completed"])
        intervention_success_rate = completed_interventions / len(interventions) * 100 if interventions else 0

        # Custom Metric Card Helper - Obsidian Edition
        def metric_card(label, value, delta, delta_color="text-green-500", icon="📊"):
            is_positive = "green" in delta_color
            delta_color_val = "#10b981" if is_positive else "#ef4444"
            glow_color = "rgba(16, 185, 129, 0.2)" if is_positive else "rgba(239, 68, 68, 0.2)"

            return f"""
            <div class="metric-card">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                    <span style="color: #8B949E; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">{label}</span>
                    <div style="background: {glow_color}; padding: 8px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">
                        <span style="font-size: 1.25rem;">{icon}</span>
                    </div>
                </div>
                <div style="font-size: 2.25rem; font-weight: 700; color: #FFFFFF; line-height: 1; font-family: 'Space Grotesk', sans-serif; text-shadow: 0 0 10px rgba(255,255,255,0.1);">{value}</div>
                <div style="font-size: 0.8rem; margin-top: 10px; font-weight: 700; color: {delta_color_val}; font-family: 'Inter', sans-serif; display: flex; align-items: center; gap: 4px;">
                    {delta}
                </div>
            </div>
            """

        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:
            st.markdown(
                metric_card("Telemetry Feed", f"{total_leads:,}", "↑ 12 Signals", "green", "📡"), unsafe_allow_html=True
            )
        with c2:
            st.markdown(
                metric_card("Critical Nodes", f"{critical_risk}", "🚨 System Alert", "red", "☢️"), unsafe_allow_html=True
            )
        with c3:
            st.markdown(
                metric_card("High Risk", f"{high_risk}", "↓ 2 vs Baseline", "green", "📉"), unsafe_allow_html=True
            )
        with c4:
            st.markdown(
                metric_card("System Variance", f"{avg_risk_score:.1f}%", "STABLE", "green", "📊"),
                unsafe_allow_html=True,
            )
        with c5:
            st.markdown(
                metric_card("Deflection Rate", f"{intervention_success_rate:.1f}%", "↑ 4.2%", "green", "🛡️"),
                unsafe_allow_html=True,
            )

    def _render_risk_distribution_chart(self, data: Dict[str, Any]):
        """Render risk distribution visualization"""
        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart

        st.markdown("##### 📊 Network Distribution")

        predictions = data["predictions"]
        risk_df = pd.DataFrame(predictions)

        # Risk tier distribution
        risk_counts = risk_df["risk_tier"].value_counts()

        fig = px.pie(
            values=risk_counts.values,
            names=risk_counts.index,
            color_discrete_map={"critical": "#ef4444", "high": "#f97316", "medium": "#84cc16", "low": "#6366F1"},
            hole=0.6,
        )

        fig.update_traces(textposition="outside", textinfo="label")
        # Add center text
        fig.add_annotation(
            text=f"{len(predictions)}",
            showarrow=False,
            font={"size": 28, "color": "#FFFFFF", "family": "Space Grotesk"},
            y=0.55,
        )
        fig.add_annotation(
            text="Leads", showarrow=False, font={"size": 12, "color": "#8B949E", "family": "Inter"}, y=0.42
        )

        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)

    def _render_risk_trend_analysis(self, data: Dict[str, Any]):
        """Render risk trend analysis"""
        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart

        st.markdown("##### 📈 Risk Velocity (30 Days)")

        # Generate sample trend data
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq="D")

        # Simulate trend data
        np.random.seed(42)  # For consistent demo data
        critical_trend = np.random.poisson(3, len(dates)) + np.sin(np.arange(len(dates)) * 0.2) * 2
        high_trend = np.random.poisson(8, len(dates)) + np.sin(np.arange(len(dates)) * 0.15) * 3

        trend_df = pd.DataFrame(
            {"date": dates, "critical_risk": np.maximum(0, critical_trend), "high_risk": np.maximum(0, high_trend)}
        )

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=trend_df["date"],
                y=trend_df["critical_risk"],
                mode="lines",
                name="Critical",
                line=dict(color="#ef4444", width=3, shape="spline"),
                fill="tozeroy",
                fillcolor="rgba(239, 68, 68, 0.1)",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=trend_df["date"],
                y=trend_df["high_risk"],
                mode="lines",
                name="High Risk",
                line=dict(color="#f97316", width=3, shape="spline"),
            )
        )

        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)

    def _render_intervention_effectiveness(self, data: Dict[str, Any]):
        """Render intervention effectiveness metrics"""
        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart

        st.markdown("##### 🎯 Deflection ROI")

        interventions = data["interventions"]
        intervention_df = pd.DataFrame(interventions)

        # Success rate by intervention type
        success_rates = []
        intervention_types = intervention_df["intervention_type"].unique()

        for int_type in intervention_types:
            type_interventions = intervention_df[intervention_df["intervention_type"] == int_type]
            success_rate = (
                len(type_interventions[type_interventions["status"] == "completed"]) / len(type_interventions) * 100
            )
            success_rates.append({"type": int_type, "success_rate": success_rate})

        success_df = pd.DataFrame(success_rates)

        fig = px.bar(
            success_df,
            x="type",
            y="success_rate",
            # title="Success Rate by Intervention Type",
            color="success_rate",
            color_continuous_scale="Purples",
        )

        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)

        # Intervention timeline
        intervention_df["scheduled_time"] = pd.to_datetime(intervention_df["scheduled_time"])
        daily_interventions = intervention_df.groupby(intervention_df["scheduled_time"].dt.date).size()

        fig2 = px.line(
            x=daily_interventions.index,
            y=daily_interventions.values,
            # title="Daily Intervention Volume",
            markers=True,
        )
        fig2.update_traces(line_color="#2563eb", line_width=2)

        fig2.update_layout(
            xaxis_title=None,
            yaxis_title="Volume",
            height=150,
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig2.update_xaxes(showgrid=False)
        fig2.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.05)")

        st.plotly_chart(fig2, use_container_width=True)

    def _render_agent_workload_distribution(self, data: Dict[str, Any]):
        """Render agent workload distribution"""
        st.markdown("##### 👥 Agent Load")

        # Simulate agent assignments
        agent_names = ["Sarah Miller", "Mike Johnson", "Emma Davis", "Alex Chen", "Lisa Rodriguez"]
        agent_workloads = []

        for agent in agent_names:
            critical_leads = np.random.randint(0, 8)
            high_risk_leads = np.random.randint(2, 15)
            total_interventions = np.random.randint(5, 25)

            agent_workloads.append(
                {
                    "agent": agent,
                    "critical_leads": critical_leads,
                    "high_risk_leads": high_risk_leads,
                    "total_interventions": total_interventions,
                    "workload_score": critical_leads * 3 + high_risk_leads * 2 + total_interventions,
                }
            )

        workload_df = pd.DataFrame(agent_workloads)

        # Workload balance chart
        fig = go.Figure()

        fig.add_trace(
            go.Bar(name="Critical", x=workload_df["agent"], y=workload_df["critical_leads"], marker_color="#ef4444")
        )

        fig.add_trace(
            go.Bar(name="High Risk", x=workload_df["agent"], y=workload_df["high_risk_leads"], marker_color="#f97316")
        )

        fig.update_layout(
            barmode="stack",
            height=250,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_tickangle=45,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.05)")

        st.plotly_chart(fig, use_container_width=True)

        # Workload balance table
        st.subheader("Workload Balance")
        workload_display = workload_df[
            ["agent", "critical_leads", "high_risk_leads", "total_interventions", "workload_score"]
        ]
        workload_display.columns = ["Agent", "Critical", "High Risk", "Interventions", "Score"]
        st.dataframe(workload_display, use_container_width=True)

    def _render_high_risk_queue(self, data: Dict[str, Any]):
        """Render high-risk leads priority queue"""

        st.markdown(
            """
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; margin-top: 1rem;">
            <h3 style="margin: 0;">🚨 Immediate Attention Required</h3>
            <span style="background: #fee2e2; color: #ef4444; font-size: 0.75rem; font-weight: 700; padding: 4px 12px; border-radius: 999px;">Top 10 Critical</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

        predictions = data["predictions"]
        high_risk_leads = [p for p in predictions if p["risk_score_14d"] >= 60]
        high_risk_leads.sort(key=lambda x: x["risk_score_14d"], reverse=True)

        for i, lead in enumerate(high_risk_leads[:10]):
            with st.container():
                st.markdown(
                    f"""
                <div class="glass-card" style="padding: 1.25rem; margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                         <div style="font-weight: 700; color: #FFFFFF; font-size: 1.25rem; font-family: 'Space Grotesk', sans-serif;">{lead["lead_name"]}</div>
                         <div class="risk-critical-badge">{lead["risk_score_14d"]:.1f}% Risk</div>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-bottom: 1rem; font-size: 0.85rem; color: #8B949E; font-family: 'Inter', sans-serif;">
                        <div>📡 Telemetry: <span style="color: #6366F1; font-weight: 600;">{lead["last_interaction_days"]:.0f}d Active</span></div>
                        <div>🧠 Confidence: <span style="color: #FFFFFF; font-weight: 600;">{lead["confidence"]:.0%}</span></div>
                        <div>🔮 Prediction: <span style="color: #ef4444; font-weight: 600;">{lead["predicted_churn_date"].strftime("%b %d")}</span></div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                # Inline Action Grid
                col_acts = st.columns([1, 1, 2])
                with col_acts[0]:
                    if st.button("📞 Call", key=f"call_{lead['lead_id']}", use_container_width=True):
                        st.success("Bridging call...")
                with col_acts[1]:
                    if st.button("✉️ Email", key=f"email_{lead['lead_id']}", use_container_width=True):
                        st.success("Draft created.")
                with col_acts[2]:
                    if st.button(
                        "🤖 Generate Retention Strategy",
                        key=f"ai_gen_{lead['lead_id']}",
                        use_container_width=True,
                        type="primary",
                    ):
                        if self.claude:
                            script_data = self.claude.generate_retention_script(lead)
                            st.session_state[f"script_{lead['lead_id']}"] = script_data

                # Drill-down details
                self._render_lead_drill_down(lead)

                # Script Display
                if f"script_{lead['lead_id']}" in st.session_state:
                    script = st.session_state[f"script_{lead['lead_id']}"]
                    st.markdown(
                        f"""
                    <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 1rem; margin-top: 10px; margin-bottom: 10px;">
                        <div style="font-size: 0.8rem; color: #166534; font-weight: 700; margin-bottom: 4px;">CLAUDE'S STRATEGY: {script["strategy"].upper()}</div>
                        <div style="font-style: italic; color: #14532d; font-size: 0.95rem;">"{script["script"]}"</div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

    def _render_lead_drill_down(self, lead):
        """Render expandable drill-down view for a lead"""
        expand_key = f"expand_{lead['lead_id']}"
        if expand_key not in st.session_state:
            st.session_state[expand_key] = False

        # Toggle button
        if st.button(
            f"{'▼ Hide' if st.session_state[expand_key] else '▶ Show'} Detailed Analysis",
            key=f"toggle_{lead['lead_id']}",
            use_container_width=True,
        ):
            st.session_state[expand_key] = not st.session_state[expand_key]

        # Detailed view
        if st.session_state[expand_key]:
            st.markdown(
                """
            <div style='background: #f8fafc; padding: 1rem; border-radius: 8px; margin-top: 1rem; border: 1px solid #e2e8f0;'>
            """,
                unsafe_allow_html=True,
            )

            # 1. Risk Factors
            st.markdown("**🎯 Risk Factor Contribution**")
            for factor_name, impact in lead.get("top_risk_factors", []):
                bar_width = min(impact * 300, 100)
                color = "#ef4444" if impact > 0.2 else "#f59e0b"
                st.markdown(
                    f"""
                <div style='margin-bottom: 5px;'>
                    <div style='display: flex; justify-content: space-between; font-size: 0.8rem;'>
                        <span>{factor_name.replace("_", " ").title()}</span>
                        <span style='color: {color}; font-weight: 600;'>{impact:.1%}</span>
                    </div>
                    <div style='background: #e2e8f0; height: 4px; border-radius: 2px;'>
                        <div style='background: {color}; width: {bar_width}%; height: 100%; border-radius: 2px;'></div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            # 2. Timeline (Simulated for demo)
            st.markdown("**📅 Recent Activity Timeline**")
            timeline_events = [
                {"date": "2d ago", "event": "📧 Email opened", "status": "positive"},
                {"date": "5d ago", "event": "🏠 Property viewed", "status": "positive"},
                {"date": "8d ago", "event": "❌ Missed call", "status": "negative"},
                {"date": "12d ago", "event": "💬 SMS replied", "status": "positive"},
            ]

            for event in timeline_events:
                bg = "#d1fae5" if event["status"] == "positive" else "#fee2e2"
                text = "#065f46" if event["status"] == "positive" else "#991b1b"
                st.markdown(
                    f"""
                <div style='display: flex; gap: 10px; align-items: center; margin-bottom: 8px; font-size: 0.85rem;'>
                    <div style='background: {bg}; color: {text}; padding: 2px 8px; border-radius: 4px; min-width: 60px; text-align: center; font-weight: 600;'>{event["date"]}</div>
                    <div>{event["event"]}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)

    def _render_retention_wizard(self):
        """Render the Retention Strategy Wizard - Obsidian Edition"""
        st.markdown(
            """
        <div class="glass-card" style="padding: 2.5rem; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
                <div style="display: flex; align-items: center; gap: 15px;">
                    <div style="font-size: 2.5rem; filter: drop-shadow(0 0 15px rgba(99, 102, 241, 0.4));">🧙</div>
                    <div>
                        <h2 style="margin: 0; font-size: 1.75rem; color: #FFFFFF; font-family: 'Space Grotesk', sans-serif;">RETENTION STRATEGY WIZARD</h2>
                        <div style="color: #6366F1; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em;">AI-Powered Deflection Engine</div>
                    </div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 2.5rem;">
                <div style="border-right: 1px solid rgba(255,255,255,0.05); padding-right: 2.5rem;">
                    <h4 style="color: #FFFFFF; margin-bottom: 1.5rem; font-family: 'Space Grotesk', sans-serif;">1. TARGET PARAMETERS</h4>
                    <div style="background: rgba(99, 102, 241, 0.05); padding: 1.25rem; border-radius: 12px; margin-bottom: 1.5rem; border: 1px solid rgba(99, 102, 241, 0.1);">
                        <div style="font-weight: 700; color: #E6EDF3; margin-bottom: 0.75rem; font-size: 0.8rem; text-transform: uppercase;">Risk Segment</div>
                        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                            <span class="risk-critical-badge">Critical (3)</span>
                            <span class="risk-high-badge">High (12)</span>
                        </div>
                    </div>
                    
                    <h4 style="color: #FFFFFF; margin-bottom: 1.5rem; margin-top: 2rem; font-family: 'Space Grotesk', sans-serif;">2. DEPLOYMENT TYPE</h4>
                    <div style="display: flex; flex-direction: column; gap: 12px;">
                        <div style="padding: 12px; border: 2px solid #6366F1; background: rgba(99, 102, 241, 0.1); border-radius: 10px; cursor: pointer; box-shadow: 0 0 15px rgba(99, 102, 241, 0.2);">
                            <div style="font-weight: 700; color: #FFFFFF;">❤️ Empathy & Check-in</div>
                            <div style="font-size: 0.8rem; color: #8B949E;">Soft approach focusing on needs</div>
                        </div>
                        <div style="padding: 12px; border: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.02); border-radius: 10px; cursor: pointer; opacity: 0.6;">
                            <div style="font-weight: 700; color: #E6EDF3;">🎁 Value & Offer</div>
                            <div style="font-size: 0.8rem; color: #8B949E;">Incentive-based retention</div>
                        </div>
                    </div>
                </div>
                
                <div>
                    <div style="background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 16px; padding: 2rem; height: 100%; position: relative; overflow: hidden;">
                        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 2px; background: #10b981; box-shadow: 0 0 10px #10b981;"></div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 1.5rem;">
                            <div style="font-weight: 700; color: #10b981; display: flex; align-items: center; gap: 10px; font-family: 'Space Grotesk', sans-serif; letter-spacing: 0.05em;">
                                <span class="status-pulse"></span>
                                <span>CLAUDE 3.5 INTELLIGENCE</span>
                            </div>
                            <div style="color: #8B949E; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">Synthesizing...</div>
                        </div>
                        
                        <div style="font-family: monospace; color: #E6EDF3; line-height: 1.7; white-space: pre-wrap; font-size: 0.95rem; opacity: 0.9;">
Subject: Checking in on your home search, [Client Name]

Hi [Client Name],

I was just reviewing some new market updates and thinking about your search for a property in [Location]. 

I know the process can sometimes feel overwhelming. I wanted to personally reach out and see how you're feeling about the options we've seen so far.

Are there any adjustments we should make to our criteria? I'm here to ensure we find exactly what fits your needs, on your timeline.

Best,
[Agent Name]
                        </div>
                        
                        <div style="margin-top: 2.5rem; display: flex; gap: 1rem; justify-content: flex-end;">
                            <button style="background: transparent; border: 1px solid rgba(255,255,255,0.2); color: #E6EDF3; padding: 0.6rem 1.25rem; border-radius: 8px; font-weight: 600; font-family: 'Space Grotesk', sans-serif; cursor: pointer; transition: all 0.2s;">REGENERATE</button>
                            <button style="background: #10b981; border: none; color: white; padding: 0.6rem 1.75rem; border-radius: 8px; font-weight: 700; font-family: 'Space Grotesk', sans-serif; box-shadow: 0 0 20px rgba(16, 185, 129, 0.3); cursor: pointer;">🚀 LAUNCH CAMPAIGN</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _generate_export_csv(self, data):
        """Generate CSV string for export"""
        df = pd.DataFrame(data["predictions"])
        return df.to_csv(index=False).encode("utf-8")

    def _generate_export_json(self, data):
        """Generate JSON string for export"""
        # Convert datetime objects to string
        json_data = data.copy()
        # Ensure comprehensive serialization handling would go here for production
        return json.dumps(json_data["predictions"], default=str).encode("utf-8")

    def _render_detailed_analytics(self, data: Dict[str, Any]):
        """Render detailed analytics section"""
        col_head, col_exp1, col_exp2 = st.columns([4, 1, 1])
        with col_head:
            st.subheader("📊 Detailed Analytics")

        with col_exp1:
            csv_data = self._generate_export_csv(data)
            st.download_button(
                label="📥 CSV",
                data=csv_data,
                file_name=f"churn_risk_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with col_exp2:
            json_data = self._generate_export_json(data)
            st.download_button(
                label="📥 JSON",
                data=json_data,
                file_name=f"churn_full_export_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True,
            )

        tab1, tab2, tab3, tab4 = st.tabs(
            ["Risk Factor Analysis", "Intervention Performance", "Lead Journey Mapping", "Predictive Insights"]
        )

        with tab1:
            self._render_risk_factor_analysis(data)

        with tab2:
            self._render_intervention_performance_details(data)

        with tab3:
            self._render_lead_journey_mapping(data)

        with tab4:
            self._render_predictive_insights(data)

    def _render_risk_factor_analysis(self, data: Dict[str, Any]):
        """Detailed risk factor analysis"""
        st.write("### Primary Risk Factors Contributing to Churn")

        # Aggregate risk factors
        factor_importance = {
            "days_since_last_interaction": 0.28,
            "response_rate_7d": 0.22,
            "engagement_trend": 0.18,
            "stage_stagnation_days": 0.12,
            "email_open_rate": 0.10,
            "call_pickup_rate": 0.06,
            "qualification_score_change": 0.04,
        }

        factor_df = pd.DataFrame(list(factor_importance.items()), columns=["Factor", "Importance"])
        factor_df["Importance_Pct"] = factor_df["Importance"] * 100

        fig = px.bar(
            factor_df,
            x="Importance_Pct",
            y="Factor",
            orientation="h",
            title="Risk Factor Importance Rankings",
            color="Importance_Pct",
            color_continuous_scale="Reds",
        )

        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

        # Factor correlation matrix
        st.write("### Risk Factor Correlations")

        # Generate sample correlation data
        factors = list(factor_importance.keys())[:5]  # Top 5 factors
        correlation_matrix = np.random.rand(len(factors), len(factors))
        correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2  # Make symmetric
        np.fill_diagonal(correlation_matrix, 1)  # Diagonal = 1

        fig = px.imshow(
            correlation_matrix,
            x=factors,
            y=factors,
            color_continuous_scale="RdBu",
            aspect="auto",
            title="Risk Factor Correlation Heatmap",
        )

        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    def _render_intervention_performance_details(self, data: Dict[str, Any]):
        """Detailed intervention performance analysis"""
        st.write("### Intervention ROI Analysis")

        # Sample intervention ROI data
        intervention_roi = {
            "email_reengagement": {"cost": 5, "success_rate": 65, "avg_revenue_impact": 1200},
            "sms_urgent": {"cost": 8, "success_rate": 75, "avg_revenue_impact": 1800},
            "phone_callback": {"cost": 25, "success_rate": 85, "avg_revenue_impact": 2500},
            "agent_escalation": {"cost": 100, "success_rate": 90, "avg_revenue_impact": 3500},
        }

        roi_data = []
        for intervention, metrics in intervention_roi.items():
            roi = (metrics["avg_revenue_impact"] * metrics["success_rate"] / 100) / metrics["cost"]
            roi_data.append(
                {
                    "intervention": intervention,
                    "cost": metrics["cost"],
                    "success_rate": metrics["success_rate"],
                    "avg_revenue": metrics["avg_revenue_impact"],
                    "roi": roi,
                }
            )

        roi_df = pd.DataFrame(roi_data)

        fig = px.scatter(
            roi_df,
            x="success_rate",
            y="avg_revenue",
            size="roi",
            color="intervention",
            title="Intervention Performance: Success Rate vs Revenue Impact",
            labels={"success_rate": "Success Rate (%)", "avg_revenue": "Average Revenue Impact ($)"},
        )

        st.plotly_chart(fig, use_container_width=True)

        # ROI ranking
        roi_df_sorted = roi_df.sort_values("roi", ascending=False)
        st.write("### ROI Rankings")
        st.dataframe(
            roi_df_sorted[["intervention", "cost", "success_rate", "avg_revenue", "roi"]].round(2),
            use_container_width=True,
        )

    def _render_lead_journey_mapping(self, data: Dict[str, Any]):
        """Lead journey and churn risk mapping"""
        st.write("### Lead Journey Risk Progression")

        # Sample journey stages with risk progression
        journey_stages = [
            "Initial Contact",
            "Qualification",
            "Property Search",
            "Property Viewing",
            "Offer Preparation",
            "Negotiation",
            "Closing",
        ]

        # Risk levels at each stage (sample data)
        stage_risks = [15, 25, 35, 45, 30, 20, 10]  # Risk decreases after offer

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=journey_stages,
                y=stage_risks,
                mode="lines+markers",
                name="Average Risk Level",
                line=dict(color="#e74c3c", width=3),
                marker=dict(size=10),
            )
        )

        # Add risk threshold lines
        fig.add_hline(y=30, line_dash="dash", line_color="orange", annotation_text="Medium Risk Threshold")
        fig.add_hline(y=60, line_dash="dash", line_color="red", annotation_text="High Risk Threshold")

        fig.update_layout(
            title="Churn Risk by Lead Journey Stage",
            xaxis_title="Journey Stage",
            yaxis_title="Average Churn Risk (%)",
            height=400,
            xaxis_tickangle=45,
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_predictive_insights(self, data: Dict[str, Any]):
        """Predictive insights and recommendations"""
        st.write("### Predictive Insights & Recommendations")

        # Key insights
        insights = [
            {
                "insight": "Email Engagement Drop",
                "description": "Leads with <30% email open rate in past 7 days have 75% higher churn risk",
                "action": "Switch to SMS or phone outreach",
                "urgency": "High",
            },
            {
                "insight": "Stage Stagnation Alert",
                "description": "Leads stuck in Property Search stage >14 days show 60% churn probability",
                "action": "Schedule consultation to address barriers",
                "urgency": "Medium",
            },
            {
                "insight": "Response Pattern Change",
                "description": "Sudden drop in response rate indicates 80% churn risk within 7 days",
                "action": "Immediate agent escalation required",
                "urgency": "Critical",
            },
            {
                "insight": "Weekend Engagement",
                "description": "Leads who engage on weekends have 40% lower churn risk",
                "action": "Prioritize weekend property viewings",
                "urgency": "Low",
            },
        ]

        for insight in insights:
            urgency_color = {"Critical": "#ff4757", "High": "#ffa726", "Medium": "#66bb6a", "Low": "#42a5f5"}

            st.markdown(
                f"""
            <div style="border-left: 4px solid {urgency_color[insight["urgency"]]};
                        padding: 1rem; margin: 1rem 0; background: #f8f9fa;">
                <h4 style="color: {urgency_color[insight["urgency"]]}; margin: 0;">
                    {insight["insight"]} ({insight["urgency"]} Priority)
                </h4>
                <p style="margin: 0.5rem 0;"><strong>Finding:</strong> {insight["description"]}</p>
                <p style="margin: 0;"><strong>Recommended Action:</strong> {insight["action"]}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

    def _render_intervention_tracking(self, data: Dict[str, Any]):
        """Render intervention tracking section"""
        st.subheader("📋 Active Intervention Tracking")

        interventions = data["interventions"]

        # Create tabs for different intervention statuses
        tab1, tab2, tab3 = st.tabs(["Pending", "Active", "Completed"])

        with tab1:
            pending_interventions = [i for i in interventions if i["status"] == "pending"]
            if pending_interventions:
                st.write(f"**{len(pending_interventions)} interventions pending execution**")

                for intervention in pending_interventions[:10]:
                    with st.container():
                        col1, col2, col3 = st.columns([2, 2, 1])

                        with col1:
                            st.write(f"**{intervention['lead_id']}**")
                            st.write(f"Type: {intervention['intervention_type']}")

                        with col2:
                            st.write(f"Scheduled: {intervention['scheduled_time'].strftime('%H:%M')}")
                            st.write("Status: ⏳ Pending")

                        with col3:
                            if st.button("Execute Now", key=f"exec_{intervention['execution_id']}"):
                                st.success("Intervention executed!")
            else:
                st.info("No pending interventions")

        with tab2:
            # Show interventions in progress (for demo, treating recent ones as active)
            recent_interventions = [
                i
                for i in interventions
                if i["status"] == "completed" and (datetime.now() - i["scheduled_time"]).total_seconds() / 3600 < 2
            ]

            if recent_interventions:
                st.write(f"**{len(recent_interventions)} interventions recently executed**")

                for intervention in recent_interventions:
                    st.markdown(
                        f"""
                    <div class="intervention-success">
                        <strong>{intervention["lead_id"]}</strong> - {intervention["intervention_type"]}<br>
                        Status: ✅ Recently Completed<br>
                        Engagement Increase: {intervention["success_metrics"].get("engagement_increase", 0):.1f}%
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No active interventions")

        with tab3:
            completed_interventions = [i for i in interventions if i["status"] == "completed"]

            if completed_interventions:
                success_count = len(
                    [i for i in completed_interventions if i["success_metrics"].get("engagement_increase", 0) > 0]
                )
                success_rate = success_count / len(completed_interventions) * 100

                st.metric(
                    label="Completed Interventions Success Rate",
                    value=f"{success_rate:.1f}%",
                    delta=f"+{success_rate - 65:.1f}%",
                )

                # Show recent completed interventions
                recent_completed = sorted(completed_interventions, key=lambda x: x["scheduled_time"], reverse=True)[:5]

                for intervention in recent_completed:
                    engagement_increase = intervention["success_metrics"].get("engagement_increase", 0)
                    success_class = "intervention-success" if engagement_increase > 0 else "intervention-failed"

                    st.markdown(
                        f"""
                    <div class="{success_class}">
                        <strong>{intervention["lead_id"]}</strong> - {intervention["intervention_type"]}<br>
                        Completed: {intervention["scheduled_time"].strftime("%m/%d %H:%M")}<br>
                        Engagement Impact: {"✅" if engagement_increase > 0 else "❌"} {engagement_increase:.1f}%
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )


# Main execution
def main():
    """Main function to run the dashboard"""
    dashboard = ChurnEarlyWarningDashboard()
    dashboard.render_dashboard()


if __name__ == "__main__":
    main()
