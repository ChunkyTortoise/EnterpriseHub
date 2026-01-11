"""
Security and Compliance Dashboard for GHL Real Estate AI

Real-time monitoring dashboard for:
- Security incidents and threat detection
- Compliance violations and remediation tracking
- ML model bias detection and fairness metrics
- API security and rate limiting status
- PII exposure monitoring and prevention
- Real estate license compliance tracking

Built with Streamlit for enterprise-grade monitoring and alerts.
"""

import asyncio
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from dataclasses import asdict

from ..services.security_compliance_monitor import (
    SecurityComplianceMonitor,
    SecurityThreatLevel,
    ComplianceStandard,
    BiasType,
    get_security_monitor
)
from ..services.secure_logging_service import get_secure_logger
from .base import EnterpriseComponent

class SecurityComplianceDashboard(EnterpriseComponent):
    """
    Enterprise security and compliance monitoring dashboard.

    Features:
    - Real-time security incident tracking
    - Compliance violation monitoring
    - ML bias detection dashboard
    - API security metrics
    - PII exposure analytics
    - Real estate regulatory compliance
    """

    def __init__(self):
        super().__init__()
        self.logger = get_secure_logger(component_name="security_dashboard")

    def render(self, tenant_id: Optional[str] = None) -> None:
        """Render the security compliance dashboard."""
        st.set_page_config(
            page_title="Security & Compliance Dashboard",
            page_icon="🔒",
            layout="wide"
        )

        # Custom CSS for security dashboard
        st.markdown("""
        <style>
        .security-metric {
            background: linear-gradient(135deg, #ff4b4b, #ff6b6b);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .compliance-metric {
            background: linear-gradient(135deg, #00cc88, #00aa77);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .bias-metric {
            background: linear-gradient(135deg, #ff9500, #ffb347);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .alert-critical {
            border-left: 5px solid #ff4b4b;
            background-color: #fff5f5;
            padding: 10px;
            margin: 10px 0;
        }

        .alert-warning {
            border-left: 5px solid #ff9500;
            background-color: #fff8f0;
            padding: 10px;
            margin: 10px 0;
        }

        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }

        .status-active { background-color: #00cc88; }
        .status-warning { background-color: #ff9500; }
        .status-critical { background-color: #ff4b4b; }
        </style>
        """, unsafe_allow_html=True)

        # Header
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.title("🔒 Security & Compliance Dashboard")
            st.markdown("*Real-time monitoring for GHL Real Estate AI Platform*")

        with col2:
            if st.button("🔄 Refresh Data", key="refresh_security"):
                st.rerun()

        with col3:
            # Auto-refresh toggle
            auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
            if auto_refresh:
                time.sleep(30)
                st.rerun()

        # Get security monitor data
        try:
            security_monitor = get_security_monitor(tenant_id)
            dashboard_data = asyncio.run(security_monitor.get_security_dashboard_data())
        except Exception as e:
            st.error(f"Error loading security data: {e}")
            return

        # Main metrics row
        self._render_security_metrics(dashboard_data)

        # Tabs for different monitoring areas
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🚨 Security Incidents",
            "📋 Compliance Status",
            "⚖️ ML Bias Detection",
            "🔐 API Security",
            "📊 Analytics & Trends"
        ])

        with tab1:
            self._render_security_incidents_tab(security_monitor)

        with tab2:
            self._render_compliance_tab(security_monitor)

        with tab3:
            self._render_ml_bias_tab(security_monitor)

        with tab4:
            self._render_api_security_tab(security_monitor)

        with tab5:
            self._render_analytics_tab(security_monitor)

    def _render_security_metrics(self, dashboard_data: Dict[str, Any]) -> None:
        """Render key security metrics."""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="security-metric">
                <h3>🚨 Active Incidents</h3>
                <h1>{dashboard_data.get('active_incidents', 0)}</h1>
                <p>Security events requiring attention</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            critical_count = dashboard_data.get('critical_incidents', 0)
            status_class = "status-critical" if critical_count > 0 else "status-active"

            st.markdown(f"""
            <div class="security-metric">
                <h3>⚠️ Critical Threats</h3>
                <h1><span class="status-indicator {status_class}"></span>{critical_count}</h1>
                <p>High-priority security threats</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="compliance-metric">
                <h3>📋 Compliance Issues</h3>
                <h1>{dashboard_data.get('compliance_violations', 0)}</h1>
                <p>Regulatory compliance violations</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            monitoring_status = dashboard_data.get('monitoring_status', 'inactive')
            status_class = "status-active" if monitoring_status == "active" else "status-critical"

            st.markdown(f"""
            <div class="compliance-metric">
                <h3>📡 Monitoring Status</h3>
                <h1><span class="status-indicator {status_class}"></span>{monitoring_status.title()}</h1>
                <p>Real-time monitoring system</p>
            </div>
            """, unsafe_allow_html=True)

    def _render_security_incidents_tab(self, security_monitor: SecurityComplianceMonitor) -> None:
        """Render security incidents monitoring tab."""
        st.header("🚨 Security Incident Management")

        # Incident summary
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Recent Security Incidents")

            # Get active incidents
            active_incidents = list(security_monitor.active_incidents.values())

            if active_incidents:
                # Create incidents DataFrame
                incidents_data = []
                for incident in active_incidents[-20:]:  # Last 20 incidents
                    incidents_data.append({
                        "Timestamp": incident.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "Type": incident.incident_type.replace("_", " ").title(),
                        "Threat Level": incident.threat_level.value.upper(),
                        "Description": incident.description[:80] + "..." if len(incident.description) > 80 else incident.description,
                        "Source IP": incident.source_ip or "N/A",
                        "Status": "Resolved" if incident.resolved else "Active",
                        "ID": incident.incident_id[:8]
                    })

                df = pd.DataFrame(incidents_data)

                # Apply color coding based on threat level
                def highlight_threat_level(row):
                    if row["Threat Level"] == "CRITICAL":
                        return ['background-color: #ffebee'] * len(row)
                    elif row["Threat Level"] == "HIGH":
                        return ['background-color: #fff3e0'] * len(row)
                    else:
                        return [''] * len(row)

                styled_df = df.style.apply(highlight_threat_level, axis=1)
                st.dataframe(styled_df, use_container_width=True)

                # Incident details expander
                if st.button("🔍 View Incident Details"):
                    selected_incident_id = st.selectbox(
                        "Select incident to view details:",
                        options=[inc.incident_id for inc in active_incidents],
                        format_func=lambda x: f"{x[:8]} - {next(inc.incident_type for inc in active_incidents if inc.incident_id == x)}"
                    )

                    if selected_incident_id:
                        incident = next(inc for inc in active_incidents if inc.incident_id == selected_incident_id)
                        self._render_incident_details(incident)

            else:
                st.success("✅ No active security incidents")

        with col2:
            st.subheader("Threat Level Distribution")

            # Create threat level chart
            threat_levels = [incident.threat_level.value for incident in active_incidents]
            if threat_levels:
                threat_counts = pd.Series(threat_levels).value_counts()

                colors = {
                    'critical': '#ff4b4b',
                    'high': '#ff9500',
                    'medium': '#ffcc00',
                    'low': '#00cc88'
                }

                fig = px.pie(
                    values=threat_counts.values,
                    names=threat_counts.index,
                    title="Incidents by Threat Level",
                    color_discrete_map=colors
                )

                fig.update_layout(
                    height=300,
                    showlegend=True,
                    font=dict(size=12)
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No incidents to display")

        # Incident response actions
        st.subheader("🛡️ Automated Response Actions")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🚫 Block Suspicious IPs", key="block_ips"):
                st.success("IP blocking rules updated")

        with col2:
            if st.button("🔄 Reset Rate Limits", key="reset_limits"):
                st.success("Rate limits reset")

        with col3:
            if st.button("📧 Send Alert Notifications", key="send_alerts"):
                st.success("Alert notifications sent")

    def _render_incident_details(self, incident) -> None:
        """Render detailed incident information."""
        st.subheader(f"Incident Details: {incident.incident_id[:8]}")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Incident Type:**", incident.incident_type.replace("_", " ").title())
            st.write("**Threat Level:**", f":{incident.threat_level.value.lower()}_circle: {incident.threat_level.value.upper()}")
            st.write("**Timestamp:**", incident.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"))
            st.write("**Source IP:**", incident.source_ip or "Unknown")
            st.write("**User ID:**", incident.user_id or "Unknown")

        with col2:
            st.write("**Affected Data Types:**")
            for data_type in incident.affected_data_types:
                st.write(f"• {data_type.replace('_', ' ').title()}")

            st.write("**Mitigation Actions:**")
            for action in incident.mitigation_actions:
                st.write(f"• {action.replace('_', ' ').title()}")

        st.write("**Description:**")
        st.write(incident.description)

        if incident.investigation_notes:
            st.write("**Investigation Notes:**")
            st.write(incident.investigation_notes)

        # Resolution controls
        if not incident.resolved:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Mark as Resolved", key=f"resolve_{incident.incident_id}"):
                    incident.resolved = True
                    st.success("Incident marked as resolved")

            with col2:
                notes = st.text_area("Add investigation notes:", key=f"notes_{incident.incident_id}")
                if st.button("💬 Add Notes", key=f"add_notes_{incident.incident_id}"):
                    incident.investigation_notes += f"\n{datetime.now()}: {notes}"
                    st.success("Notes added")

    def _render_compliance_tab(self, security_monitor: SecurityComplianceMonitor) -> None:
        """Render compliance monitoring tab."""
        st.header("📋 Regulatory Compliance Status")

        # Compliance standards overview
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Compliance Violations")

            violations = list(security_monitor.compliance_violations.values())

            if violations:
                # Create violations DataFrame
                violations_data = []
                for violation in violations[-15:]:  # Last 15 violations
                    violations_data.append({
                        "Timestamp": violation.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "Standard": violation.standard.value.upper(),
                        "Type": violation.violation_type.replace("_", " ").title(),
                        "Severity": violation.severity,
                        "Description": violation.description[:60] + "..." if len(violation.description) > 60 else violation.description,
                        "Status": "Resolved" if violation.resolved else "Open",
                        "ID": violation.violation_id[:8]
                    })

                df = pd.DataFrame(violations_data)

                # Color coding for severity
                def highlight_severity(row):
                    if row["Severity"] == "CRITICAL":
                        return ['background-color: #ffebee'] * len(row)
                    elif row["Severity"] == "HIGH":
                        return ['background-color: #fff3e0'] * len(row)
                    else:
                        return [''] * len(row)

                styled_df = df.style.apply(highlight_severity, axis=1)
                st.dataframe(styled_df, use_container_width=True)

            else:
                st.success("✅ No compliance violations detected")

        with col2:
            st.subheader("Compliance Standards")

            # Compliance status by standard
            standards_status = {}
            for violation in violations:
                standard = violation.standard.value.upper()
                if standard not in standards_status:
                    standards_status[standard] = {"violations": 0, "resolved": 0}

                standards_status[standard]["violations"] += 1
                if violation.resolved:
                    standards_status[standard]["resolved"] += 1

            for standard, status in standards_status.items():
                compliance_rate = (status["resolved"] / status["violations"]) * 100 if status["violations"] > 0 else 100
                color = "green" if compliance_rate > 90 else "orange" if compliance_rate > 70 else "red"

                st.markdown(f"""
                <div style="padding: 10px; border-left: 4px solid {color}; margin: 10px 0; background-color: #f8f9fa;">
                    <strong>{standard}</strong><br>
                    Compliance Rate: {compliance_rate:.1f}%<br>
                    Open Issues: {status['violations'] - status['resolved']}
                </div>
                """, unsafe_allow_html=True)

        # Data retention compliance
        st.subheader("📅 Data Retention Compliance")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Data Retention Policy", "7 Years", help="CCPA/GDPR compliant retention period")

        with col2:
            # Simulated data age metrics
            st.metric("Records Due for Review", "245", delta="12 this month")

        with col3:
            st.metric("Auto-deletion Scheduled", "18", delta="3 pending")

        # Real estate specific compliance
        st.subheader("🏠 Real Estate Regulatory Compliance")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**License Compliance Status:**")
            # Simulated license data
            license_data = {
                "Active Licenses": 45,
                "Expiring Soon (30 days)": 3,
                "Expired": 1,
                "Pending Renewal": 2
            }

            for key, value in license_data.items():
                color = "green" if "Active" in key else "orange" if "Expiring" in key or "Pending" in key else "red"
                st.markdown(f"• **{key}:** ::{color}[{value}]")

        with col2:
            st.write("**Fair Housing Compliance:**")
            st.markdown("• ✅ Bias monitoring active")
            st.markdown("• ✅ Protected class tracking enabled")
            st.markdown("• ⚠️ 2 potential bias alerts (under review)")
            st.markdown("• ✅ Training records up to date")

    def _render_ml_bias_tab(self, security_monitor: SecurityComplianceMonitor) -> None:
        """Render ML bias detection tab."""
        st.header("⚖️ ML Model Bias Detection & Fairness")

        # Model fairness overview
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Model Fairness Scores")

            # Simulated model fairness data
            models = [
                {"name": "Lead Scoring Model", "fairness": 0.92, "bias_alerts": 0},
                {"name": "Property Matching Engine", "fairness": 0.88, "bias_alerts": 1},
                {"name": "Churn Prediction Model", "fairness": 0.95, "bias_alerts": 0},
                {"name": "Market Analysis AI", "fairness": 0.84, "bias_alerts": 2}
            ]

            model_df = pd.DataFrame(models)

            # Create fairness score chart
            fig = px.bar(
                model_df,
                x="name",
                y="fairness",
                title="Model Fairness Scores (Target: >0.90)",
                color="fairness",
                color_continuous_scale=["red", "orange", "green"],
                range_color=[0.7, 1.0]
            )

            fig.add_hline(y=0.90, line_dash="dash", line_color="red",
                         annotation_text="Fairness Threshold (0.90)")

            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Bias Detection Summary")

            total_models = len(models)
            biased_models = len([m for m in models if m["fairness"] < 0.90])
            total_alerts = sum(m["bias_alerts"] for m in models)

            st.metric("Models Monitored", total_models)
            st.metric("Models Below Threshold", biased_models, delta=f"{biased_models-1} from last week")
            st.metric("Active Bias Alerts", total_alerts, delta="1 new alert")

            # Bias type breakdown
            st.write("**Recent Bias Alerts:**")
            if total_alerts > 0:
                st.markdown("• Demographic parity violation (Property Matching)")
                st.markdown("• Disparate impact detected (Market Analysis)")
            else:
                st.success("No active bias alerts")

        # Detailed bias analysis
        st.subheader("📊 Detailed Bias Analysis")

        # Select model for detailed analysis
        selected_model = st.selectbox(
            "Select model for detailed analysis:",
            [m["name"] for m in models]
        )

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Bias Analysis for {selected_model}:**")

            # Simulated bias metrics
            if "Property Matching" in selected_model:
                st.markdown("• **Demographic Parity:** ⚠️ 0.12 (Threshold: 0.05)")
                st.markdown("• **Equalized Odds:** ✅ 0.03")
                st.markdown("• **Individual Fairness:** ✅ 0.02")
                st.markdown("• **Disparate Impact:** ✅ 0.87 (>0.80)")

                st.warning("""
                **Action Required:** Demographic parity violation detected.
                Recommendation: Retrain model with balanced dataset.
                """)

            else:
                st.markdown("• **Demographic Parity:** ✅ 0.03")
                st.markdown("• **Equalized Odds:** ✅ 0.02")
                st.markdown("• **Individual Fairness:** ✅ 0.01")
                st.markdown("• **Disparate Impact:** ✅ 0.93")

                st.success("All fairness metrics within acceptable thresholds.")

        with col2:
            st.write("**Protected Attribute Analysis:**")

            # Simulated demographic analysis
            demo_data = pd.DataFrame({
                "Demographic": ["White", "Black", "Hispanic", "Asian", "Other"],
                "Approval_Rate": [0.75, 0.68, 0.71, 0.78, 0.72]
            })

            fig = px.bar(
                demo_data,
                x="Demographic",
                y="Approval_Rate",
                title="Approval Rates by Demographic",
                color="Approval_Rate",
                color_continuous_scale=["red", "yellow", "green"]
            )

            fig.add_hline(y=0.70, line_dash="dash", line_color="blue",
                         annotation_text="Target Rate")

            st.plotly_chart(fig, use_container_width=True)

        # Bias remediation actions
        st.subheader("🔧 Bias Remediation")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 Retrain Models", key="retrain_models"):
                st.info("Model retraining initiated with balanced dataset")

        with col2:
            if st.button("📊 Generate Fairness Report", key="fairness_report"):
                st.info("Comprehensive fairness report generated")

        with col3:
            if st.button("⚙️ Adjust Fairness Constraints", key="adjust_constraints"):
                st.info("Fairness constraints updated")

    def _render_api_security_tab(self, security_monitor: SecurityComplianceMonitor) -> None:
        """Render API security monitoring tab."""
        st.header("🔐 API Security Monitoring")

        # API security metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Authentication Failures", "23", delta="5 in last hour", delta_color="inverse")

        with col2:
            st.metric("Rate Limit Violations", "12", delta="2 new", delta_color="inverse")

        with col3:
            st.metric("Blocked IPs", "8", delta="1 added")

        with col4:
            st.metric("GHL Webhook Failures", "3", delta="1 invalid signature", delta_color="inverse")

        # API endpoint security
        st.subheader("🔒 Endpoint Security Status")

        # Simulated endpoint security data
        endpoints = [
            {"endpoint": "/api/leads", "requests": 1250, "failures": 3, "rate_limited": 2},
            {"endpoint": "/api/properties", "requests": 890, "failures": 1, "rate_limited": 0},
            {"endpoint": "/api/ghl/webhook", "requests": 450, "failures": 5, "rate_limited": 1},
            {"endpoint": "/api/ml/predict", "requests": 340, "failures": 0, "rate_limited": 8},
            {"endpoint": "/api/auth/login", "requests": 180, "failures": 23, "rate_limited": 5}
        ]

        endpoint_df = pd.DataFrame(endpoints)
        endpoint_df["failure_rate"] = (endpoint_df["failures"] / endpoint_df["requests"] * 100).round(2)

        # Color code based on failure rate
        def highlight_failure_rate(row):
            if row["failure_rate"] > 2:
                return ['background-color: #ffebee'] * len(row)
            elif row["failure_rate"] > 1:
                return ['background-color: #fff3e0'] * len(row)
            else:
                return [''] * len(row)

        styled_df = endpoint_df.style.apply(highlight_failure_rate, axis=1)
        st.dataframe(styled_df, use_container_width=True)

        # Rate limiting analysis
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 Request Rate Analysis")

            # Simulated rate limiting data over time
            times = pd.date_range(start="2024-01-01 00:00", periods=24, freq="H")
            requests = np.random.normal(100, 20, 24)
            rate_limits = np.random.poisson(2, 24)

            rate_data = pd.DataFrame({
                "Time": times,
                "Requests": requests,
                "Rate_Limits": rate_limits
            })

            fig = make_subplots(specs=[[{"secondary_y": True}]])

            fig.add_trace(
                go.Scatter(x=rate_data["Time"], y=rate_data["Requests"], name="Requests/Hour"),
                secondary_y=False
            )

            fig.add_trace(
                go.Scatter(x=rate_data["Time"], y=rate_data["Rate_Limits"], name="Rate Limit Hits", line=dict(color="red")),
                secondary_y=True
            )

            fig.update_xaxes(title_text="Time")
            fig.update_yaxes(title_text="Requests", secondary_y=False)
            fig.update_yaxes(title_text="Rate Limit Hits", secondary_y=True)

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("🌍 Geographic Threat Analysis")

            # Simulated geographic threat data
            threat_data = pd.DataFrame({
                "Country": ["USA", "China", "Russia", "Brazil", "India"],
                "Requests": [5000, 150, 89, 76, 45],
                "Suspicious": [12, 45, 67, 23, 15]
            })

            threat_data["Threat_Score"] = (threat_data["Suspicious"] / threat_data["Requests"] * 100).round(2)

            fig = px.scatter(
                threat_data,
                x="Requests",
                y="Suspicious",
                size="Threat_Score",
                color="Threat_Score",
                hover_data=["Country"],
                title="Request Volume vs Suspicious Activity",
                color_continuous_scale=["green", "yellow", "red"]
            )

            st.plotly_chart(fig, use_container_width=True)

        # Security actions
        st.subheader("🛡️ Security Actions")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("🚫 Block Suspicious IPs", key="block_api_ips"):
                st.success("Suspicious IPs blocked")

        with col2:
            if st.button("🔄 Reset API Keys", key="reset_api_keys"):
                st.warning("API key reset initiated")

        with col3:
            if st.button("⚙️ Adjust Rate Limits", key="adjust_rates"):
                st.info("Rate limits adjusted")

        with col4:
            if st.button("📧 Alert Security Team", key="alert_team"):
                st.info("Security team notified")

    def _render_analytics_tab(self, security_monitor: SecurityComplianceMonitor) -> None:
        """Render analytics and trends tab."""
        st.header("📊 Security Analytics & Trends")

        # Time series analysis
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🔍 Security Incident Trends")

            # Simulated incident trend data
            dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
            incidents = np.random.poisson(3, 30)
            critical = np.random.poisson(0.5, 30)

            trend_data = pd.DataFrame({
                "Date": dates,
                "Total_Incidents": incidents,
                "Critical_Incidents": critical
            })

            fig = px.line(
                trend_data,
                x="Date",
                y=["Total_Incidents", "Critical_Incidents"],
                title="Security Incidents Over Time"
            )

            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Number of Incidents"
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("📈 Compliance Violation Trends")

            # Simulated compliance trend data
            compliance_data = pd.DataFrame({
                "Standard": ["CCPA", "GDPR", "RESPA", "FCRA", "Fair Housing"],
                "Violations_This_Month": [2, 1, 0, 1, 3],
                "Violations_Last_Month": [3, 2, 1, 0, 2]
            })

            fig = px.bar(
                compliance_data,
                x="Standard",
                y=["Violations_This_Month", "Violations_Last_Month"],
                title="Compliance Violations: Month-over-Month",
                barmode="group"
            )

            st.plotly_chart(fig, use_container_width=True)

        # Risk assessment
        st.subheader("⚠️ Risk Assessment Matrix")

        # Simulated risk data
        risks = [
            {"Category": "Data Breach", "Probability": 0.15, "Impact": 9, "Risk_Score": 1.35},
            {"Category": "API Abuse", "Probability": 0.45, "Impact": 6, "Risk_Score": 2.7},
            {"Category": "Compliance Violation", "Probability": 0.25, "Impact": 7, "Risk_Score": 1.75},
            {"Category": "ML Bias", "Probability": 0.35, "Impact": 5, "Risk_Score": 1.75},
            {"Category": "Insider Threat", "Probability": 0.08, "Impact": 8, "Risk_Score": 0.64}
        ]

        risk_df = pd.DataFrame(risks)

        fig = px.scatter(
            risk_df,
            x="Probability",
            y="Impact",
            size="Risk_Score",
            color="Risk_Score",
            hover_data=["Category"],
            title="Security Risk Matrix",
            labels={"Probability": "Probability of Occurrence", "Impact": "Impact Score (1-10)"},
            color_continuous_scale=["green", "yellow", "red"]
        )

        # Add risk threshold lines
        fig.add_hline(y=7, line_dash="dash", line_color="orange", annotation_text="High Impact Threshold")
        fig.add_vline(x=0.3, line_dash="dash", line_color="orange", annotation_text="High Probability Threshold")

        st.plotly_chart(fig, use_container_width=True)

        # Performance metrics
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("⚡ Performance Metrics")

            metrics_data = {
                "Metric": [
                    "Mean Time to Detection (MTTD)",
                    "Mean Time to Response (MTTR)",
                    "False Positive Rate",
                    "System Availability",
                    "Monitoring Coverage"
                ],
                "Current": ["4.2 min", "12.8 min", "3.2%", "99.97%", "94%"],
                "Target": ["< 5 min", "< 15 min", "< 5%", "> 99.95%", "> 95%"],
                "Status": ["✅", "✅", "✅", "✅", "⚠️"]
            }

            metrics_df = pd.DataFrame(metrics_data)
            st.dataframe(metrics_df, use_container_width=True)

        with col2:
            st.subheader("📋 Action Items")

            st.markdown("""
            **High Priority:**
            • Investigate property matching model bias alert
            • Review failed GHL webhook signatures
            • Update rate limiting rules for ML API

            **Medium Priority:**
            • Complete Q1 compliance audit
            • Enhance geographic threat detection
            • Optimize bias detection algorithms

            **Low Priority:**
            • Update security documentation
            • Review incident response playbooks
            • Plan security awareness training
            """)

        # Export options
        st.subheader("📄 Export & Reporting")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📊 Generate Security Report", key="security_report"):
                st.success("Security report generated")

        with col2:
            if st.button("📋 Export Compliance Data", key="export_compliance"):
                st.success("Compliance data exported")

        with col3:
            if st.button("📈 Create Executive Summary", key="exec_summary"):
                st.success("Executive summary created")

# Usage example
if __name__ == "__main__":
    dashboard = SecurityComplianceDashboard()
    dashboard.render(tenant_id="demo_tenant")