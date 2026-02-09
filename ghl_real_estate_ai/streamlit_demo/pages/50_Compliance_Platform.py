"""
Enterprise AI Compliance & Risk Platform - Executive Dashboard

Production-grade compliance management dashboard for EU AI Act, SEC, HIPAA.
Designed for C-suite presentations and client acquisition.
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from ghl_real_estate_ai.streamlit_demo.async_utils import run_async

# Page configuration
st.set_page_config(
    page_title="AI Compliance Union[Platform, Enterprise] Risk Management",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import demo data generator
try:
    from ghl_real_estate_ai.compliance_platform.services.demo_data_generator import DemoDataGenerator

    PLATFORM_AVAILABLE = True
except ImportError:
    PLATFORM_AVAILABLE = False

# Import AI Analyzer (mocked if not available)
try:
    from ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer import ComplianceAIAnalyzer

    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


# ============================================================================
# AI ANALYZER MOCK (when service not available)
# ============================================================================


class MockComplianceAIAnalyzer:
    """Mock AI Analyzer for demo purposes when actual service is unavailable"""

    def __init__(self):
        self.model_name = "claude-3-sonnet (mock)"

    async def answer_compliance_question(self, question: str, context: str = None) -> str:
        """Generate mock response for compliance questions"""
        responses = {
            "risks": """Based on the current compliance data, your top 3 compliance risks are:

1. **HIPAA PHI Encryption Gap** (Critical)
   - Impact: Potential $1.5M fine and reputational damage
   - Root Cause: Legacy system integration lacking end-to-end encryption
   - Recommendation: Implement AES-256 encryption for PHI at rest and in transit

2. **EU AI Act Human Oversight Deficiency** (High)
   - Impact: Up to 15M EUR fine under Article 14 requirements
   - Root Cause: Automated decision systems without human review checkpoints
   - Recommendation: Implement mandatory human-in-the-loop for high-risk decisions

3. **GDPR DPIA Documentation** (High)
   - Impact: 20M EUR potential fine
   - Root Cause: Data Protection Impact Assessment not conducted for AI processing
   - Recommendation: Complete DPIA for all AI models processing personal data""",
            "eu_ai": """To achieve EU AI Act compliance, follow this roadmap:

**Phase 1: Risk Classification (2-4 weeks)**
- Classify all AI systems using Annex III criteria
- Document intended purposes and deployment contexts
- Identify high-risk systems requiring Article 6 compliance

**Phase 2: Technical Documentation (4-8 weeks)**
- Create technical documentation per Annex IV
- Document training data, algorithms, and validation procedures
- Establish logging and monitoring capabilities

**Phase 3: Human Oversight (4-6 weeks)**
- Implement human-in-the-loop mechanisms
- Design override and intervention protocols
- Train operators on oversight responsibilities

**Phase 4: Conformity Assessment (2-4 weeks)**
- Conduct internal conformity assessment
- Prepare CE marking documentation
- Register in EU AI database

**Estimated Timeline**: 12-22 weeks
**Estimated Investment**: 150,000-300,000 EUR""",
            "violations": """Your current violations analysis:

**Critical Violations (1)**
- PHI Encryption: Healthcare data transmitted without proper encryption
  - Status: 5 days open, remediation in progress
  - Assigned: Security Team
  - ETA: 3 business days

**High Violations (3)**
1. Human Oversight: DiagnosticAI lacks human review for critical decisions
2. Technical Documentation: Missing AI system documentation for 4 models
3. DPIA Not Conducted: 2 AI systems processing personal data without assessment

**Remediation Progress**: 45% complete
**Projected Resolution**: 21 days for all high/critical issues

**Recommended Actions**:
1. Prioritize PHI encryption fix (highest regulatory risk)
2. Schedule DPIA workshops for data processing AI systems
3. Implement documentation sprint for undocumented models""",
        }

        # Match question to response category
        question_lower = question.lower()
        if "risk" in question_lower or "biggest" in question_lower:
            return responses["risks"]
        elif "eu ai" in question_lower or "act" in question_lower:
            return responses["eu_ai"]
        elif "violation" in question_lower or "explain" in question_lower:
            return responses["violations"]
        else:
            return f"""Thank you for your compliance question. Based on the current data:

Your organization maintains an overall compliance score of 87.3%, with 8 of 12 AI models fully compliant. The primary areas requiring attention are:

1. HIPAA privacy controls (78% compliance)
2. EU AI Act human oversight requirements (85% compliance)
3. Technical documentation gaps for 4 AI systems

I recommend focusing on the critical PHI encryption violation first, as it carries the highest regulatory risk. Would you like me to elaborate on any specific area?"""

    async def analyze_model_risks(self, model_name: str, model_data: dict) -> dict:
        """Generate AI risk analysis for a specific model"""
        score = model_data.get("score", 75)
        risk_level = model_data.get("risk_level", "limited")

        risk_dimensions = {
            "transparency": {
                "score": min(100, score + 5),
                "assessment": "Model decision pathways are partially documented. Recommend implementing SHAP/LIME explanations for high-stakes decisions.",
                "priority": "medium",
            },
            "fairness": {
                "score": min(100, score - 3),
                "assessment": "Bias testing conducted quarterly. Consider expanding demographic parity analysis across protected classes.",
                "priority": "high" if score < 80 else "medium",
            },
            "accountability": {
                "score": min(100, score + 8),
                "assessment": "Audit trails in place. Human escalation paths defined for critical decisions.",
                "priority": "low",
            },
            "robustness": {
                "score": min(100, score - 5),
                "assessment": "Adversarial testing recommended. Model drift monitoring should be enhanced.",
                "priority": "high" if risk_level == "high" else "medium",
            },
            "privacy": {
                "score": min(100, score + 2),
                "assessment": "Data minimization principles applied. Consider differential privacy for sensitive attributes.",
                "priority": "medium",
            },
        }

        recommendations = [
            f"Implement continuous monitoring for {model_name} performance drift",
            "Enhance explainability documentation for regulatory compliance",
            "Schedule quarterly bias audits with external reviewers",
            "Deploy canary testing for production model updates",
        ]

        if risk_level == "high":
            recommendations.insert(0, "URGENT: Conduct comprehensive risk assessment per EU AI Act Annex III")

        return {
            "model_name": model_name,
            "risk_dimensions": risk_dimensions,
            "overall_risk_score": score,
            "recommendations": recommendations,
            "compliance_gaps": [
                "Article 14 human oversight requirements partially met",
                "Technical documentation needs update for Annex IV compliance",
            ]
            if score < 85
            else [],
        }

    async def generate_executive_summary(self, data: dict) -> str:
        """Generate executive summary report"""
        metrics = data.get("executive_metrics", {})
        score = metrics.get("average_compliance_score", 87.3)
        violations = metrics.get("total_violations", 7)
        exposure = metrics.get("potential_exposure", 35_000_000)

        return f"""# Executive Compliance Summary

## Overall Status: {"Satisfactory" if score >= 80 else "Requires Attention"}

**Reporting Period**: Last 90 Days
**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}

---

### Key Union[Metrics, Metric] | Union[Value, Trend] |
|--------|-------|-------|
| Compliance Score | {score:.1f}% | +5.2% |
| Active Violations | {violations} | -3 |
| Potential Exposure | {exposure / 1_000_000:.0f}M | -15M |
| Models Compliant | {metrics.get("compliant_models", 8)}/{metrics.get("total_models", 12)} | +2 |

---

### Risk Assessment

**Critical Issues**: {metrics.get("critical_violations", 1)}
- PHI Encryption gap requires immediate remediation
- Estimated resolution: 3-5 business days

**High Priority**: {metrics.get("high_violations", 3)}
- EU AI Act human oversight implementation
- GDPR DPIA completion for AI systems
- Technical documentation updates

---

### Regulatory Compliance by Framework

- **EU AI Act**: 85% compliant (Article 14 gaps identified)
- **HIPAA**: 78% compliant (PHI encryption in progress)
- **SEC Guidance**: 92% compliant (minor documentation gaps)
- **GDPR**: 88% compliant (DPIA completion needed)

---

### Recommendations

1. **Immediate (0-7 days)**: Complete PHI encryption implementation
2. **Short-term (7-30 days)**: Conduct missing DPIAs, implement human oversight
3. **Medium-term (30-90 days)**: Complete technical documentation sprint
4. **Ongoing**: Establish quarterly compliance review cadence

---

### Financial Impact Union[Analysis, Scenario] | Union[Probability, Potential] Fine |
|----------|-------------|----------------|
| PHI Breach (unencrypted) | 15% | 1.5M |
| EU AI Act Non-Union[compliance, 8]% | 15M |
| GDPR Union[Violation, 5]% | 20M |

**Expected Value at Risk**: 3.2M
**With Remediation**: <500K

---

*Report generated by AI Compliance Analyzer v1.0*
*This is an AI-generated summary for executive review*"""


def get_ai_analyzer():
    """Get AI analyzer instance (real or mock)"""
    if AI_AVAILABLE:
        return ComplianceAIAnalyzer()
    return MockComplianceAIAnalyzer()


# ============================================================================
# DEMO PREDICTIVE ANALYTICS DATA
# ============================================================================

DEMO_PREDICTIONS = {
    "lead_scorer": {
        "current_score": 78.5,
        "predicted_score": 82.3,
        "confidence": 0.85,
        "trend": "improving",
        "risk_factors": ["Minor documentation gaps", "Audit overdue"],
    },
    "property_matcher": {
        "current_score": 85.2,
        "predicted_score": 87.1,
        "confidence": 0.91,
        "trend": "stable",
        "risk_factors": ["Data quality monitoring needed"],
    },
    "diagnostic_ai": {
        "current_score": 72.0,
        "predicted_score": 68.5,
        "confidence": 0.78,
        "trend": "declining",
        "risk_factors": ["Human oversight gaps", "HIPAA compliance risk", "Technical debt"],
    },
    "fraud_guard": {
        "current_score": 94.0,
        "predicted_score": 95.2,
        "confidence": 0.93,
        "trend": "improving",
        "risk_factors": [],
    },
}

DEMO_ANOMALIES = [
    {
        "model": "Property Matcher",
        "type": "score_drop",
        "severity": "high",
        "detected": "2 hours ago",
        "description": "Sudden 12% score decrease detected",
    },
    {
        "model": "Lead Scorer",
        "type": "violation_surge",
        "severity": "medium",
        "detected": "1 day ago",
        "description": "3 new violations in 24h period",
    },
    {
        "model": "DiagnosticAI Pro",
        "type": "drift_detected",
        "severity": "high",
        "detected": "4 hours ago",
        "description": "Model performance drift exceeds threshold",
    },
    {
        "model": "CreditScore AI",
        "type": "bias_alert",
        "severity": "critical",
        "detected": "30 minutes ago",
        "description": "Potential bias detected in demographic groups",
    },
    {
        "model": "TalentMatch AI",
        "type": "data_quality",
        "severity": "medium",
        "detected": "6 hours ago",
        "description": "Input data quality degradation detected",
    },
]

# ============================================================================
# DEMO MULTI-TENANT DATA
# ============================================================================

DEMO_ORGANIZATIONS = [
    {"name": "Acme Corp", "tier": "enterprise", "models_limit": 50, "models_used": 12},
    {"name": "TechStart Inc", "tier": "professional", "models_limit": 25, "models_used": 18},
    {"name": "HealthAI Ltd", "tier": "professional", "models_limit": 25, "models_used": 8},
]

DEMO_USER_ROLES = {
    "compliance_officer": {
        "permissions": ["View Models", "Run Assessments", "Acknowledge Violations", "Generate Reports"],
        "title": "Compliance Officer",
    },
    "admin": {
        "permissions": [
            "View Models",
            "Run Assessments",
            "Acknowledge Violations",
            "Generate Reports",
            "Manage Users",
            "Configure Settings",
        ],
        "title": "Administrator",
    },
    "viewer": {"permissions": ["View Models", "Generate Reports"], "title": "Viewer"},
}

# ============================================================================
# DEMO ALERTS DATA
# ============================================================================

DEMO_ALERTS = [
    {
        "id": "alert-001",
        "severity": "critical",
        "model": "Lead Scorer",
        "type": "threshold_breach",
        "message": "Compliance score dropped below 50%",
        "timestamp": datetime.now() - timedelta(minutes=2),
        "status": "active",
    },
    {
        "id": "alert-002",
        "severity": "high",
        "model": "Property Matcher",
        "type": "violation_detected",
        "message": "New GDPR violation detected - missing consent documentation",
        "timestamp": datetime.now() - timedelta(minutes=15),
        "status": "active",
    },
    {
        "id": "alert-003",
        "severity": "high",
        "model": "DiagnosticAI Pro",
        "type": "audit_required",
        "message": "Human oversight checkpoint missed for 3 consecutive decisions",
        "timestamp": datetime.now() - timedelta(minutes=32),
        "status": "active",
    },
    {
        "id": "alert-004",
        "severity": "medium",
        "model": "CreditScore AI",
        "type": "drift_detected",
        "message": "Model drift detected - bias metrics exceeding threshold",
        "timestamp": datetime.now() - timedelta(hours=1, minutes=15),
        "status": "active",
    },
    {
        "id": "alert-005",
        "severity": "medium",
        "model": "TalentMatch AI",
        "type": "documentation_gap",
        "message": "Technical documentation outdated by 45+ days",
        "timestamp": datetime.now() - timedelta(hours=2, minutes=8),
        "status": "active",
    },
    {
        "id": "alert-006",
        "severity": "low",
        "model": "CustomerBot Pro",
        "type": "maintenance_due",
        "message": "Scheduled compliance review approaching deadline",
        "timestamp": datetime.now() - timedelta(hours=4),
        "status": "acknowledged",
    },
    {
        "id": "alert-007",
        "severity": "critical",
        "model": "PatientFlow Optimizer",
        "type": "phi_exposure",
        "message": "PHI data processing without encryption detected",
        "timestamp": datetime.now() - timedelta(hours=6),
        "status": "resolved",
    },
    {
        "id": "alert-008",
        "severity": "high",
        "model": "FraudGuard ML",
        "type": "access_anomaly",
        "message": "Unauthorized access attempt to model configuration",
        "timestamp": datetime.now() - timedelta(hours=12),
        "status": "resolved",
    },
    {
        "id": "alert-009",
        "severity": "medium",
        "model": "MarketSense Predictor",
        "type": "performance_degradation",
        "message": "Model accuracy dropped 8% in last 24 hours",
        "timestamp": datetime.now() - timedelta(days=1),
        "status": "acknowledged",
    },
    {
        "id": "alert-010",
        "severity": "low",
        "model": "ContractAnalyzer",
        "type": "update_available",
        "message": "New compliance rule updates available for SEC guidance",
        "timestamp": datetime.now() - timedelta(days=2),
        "status": "resolved",
    },
]


def get_demo_alerts() -> List[Dict[str, Any]]:
    """Get demo alerts with dynamic timestamps"""
    # Initialize alerts in session state if not present
    if "compliance_alerts" not in st.session_state:
        st.session_state.compliance_alerts = DEMO_ALERTS.copy()
    return st.session_state.compliance_alerts


def format_relative_time(dt: datetime) -> str:
    """Format datetime as relative time string"""
    now = datetime.now()
    diff = now - dt

    if diff.total_seconds() < 60:
        return "Just now"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} min{'s' if minutes != 1 else ''} ago"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = int(diff.total_seconds() / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"


def get_alert_metrics(alerts: List[Dict]) -> Dict[str, Any]:
    """Calculate alert metrics from alerts list"""
    active_alerts = [a for a in alerts if a["status"] == "active"]

    severity_counts = {
        "critical": len([a for a in active_alerts if a["severity"] == "critical"]),
        "high": len([a for a in active_alerts if a["severity"] == "high"]),
        "medium": len([a for a in active_alerts if a["severity"] == "medium"]),
        "low": len([a for a in active_alerts if a["severity"] == "low"]),
    }

    # Find last alert timestamp
    if alerts:
        last_alert = max(alerts, key=lambda x: x["timestamp"])
        last_alert_time = format_relative_time(last_alert["timestamp"])
    else:
        last_alert_time = "N/A"

    # Count unique models being monitored
    models_monitored = len(set(a["model"] for a in alerts))

    # Calculate system health based on critical/high alerts
    total_active = len(active_alerts)
    critical_high = severity_counts["critical"] + severity_counts["high"]

    if critical_high == 0:
        health_status = "healthy"
    elif critical_high <= 2:
        health_status = "warning"
    else:
        health_status = "critical"

    return {
        "total_active": total_active,
        "severity_counts": severity_counts,
        "last_alert_time": last_alert_time,
        "models_monitored": models_monitored,
        "health_status": health_status,
    }


def render_live_alerts_panel(alerts: List[Dict], max_alerts: int = 5):
    """Render the live alerts panel at the top of the page"""
    st.markdown("### Live Alerts")

    # Filter to show only active and recently acknowledged alerts
    display_alerts = [a for a in alerts if a["status"] in ["active", "acknowledged"]]
    display_alerts = sorted(display_alerts, key=lambda x: x["timestamp"], reverse=True)[:max_alerts]

    if not display_alerts:
        st.success("No active alerts at this time.")
        return

    for alert in display_alerts:
        severity = alert["severity"]
        status = alert["status"]

        # Create alert container based on severity
        if severity == "critical":
            alert_container = st.error
            icon = "🚨"
            badge_class = "violation-critical"
        elif severity == "high":
            alert_container = st.warning
            icon = "⚠️"
            badge_class = "violation-high"
        elif severity == "medium":
            alert_container = st.info
            icon = "🔔"
            badge_class = "violation-medium"
        else:  # low
            alert_container = st.info
            icon = "💡"
            badge_class = "violation-low"

        # Build alert message
        relative_time = format_relative_time(alert["timestamp"])
        status_badge = " [ACKNOWLEDGED]" if status == "acknowledged" else ""

        col_alert, col_action = st.columns([5, 1])

        with col_alert:
            alert_text = f"""
            {icon} **[{severity.upper()}]** {alert["model"]} - {alert["type"].replace("_", " ").title()}{status_badge}

            {alert["message"]} | _{relative_time}_
            """

            if severity == "critical":
                st.error(alert_text)
            elif severity == "high":
                st.warning(alert_text)
            elif severity == "medium":
                st.info(alert_text)
            else:
                st.info(alert_text)

        with col_action:
            if status == "active":
                if st.button("Acknowledge", key=f"ack_{alert['id']}", type="secondary"):
                    # Update alert status in session state
                    for a in st.session_state.compliance_alerts:
                        if a["id"] == alert["id"]:
                            a["status"] = "acknowledged"
                    st.toast(f"Alert {alert['id']} acknowledged", icon="✅")
                    st.rerun()


def render_alert_history_table(alerts: List[Dict]):
    """Render the alert history table with filtering and export options"""
    st.markdown("### Alert History")

    # Filter controls
    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        status_filter = st.selectbox(
            "Filter by Status", ["All", "Active", "Acknowledged", "Resolved"], key="alert_status_filter"
        )

    with filter_col2:
        severity_filter = st.selectbox(
            "Filter by Severity", ["All", "Critical", "High", "Medium", "Low"], key="alert_severity_filter"
        )

    with filter_col3:
        model_options = ["All"] + list(set(a["model"] for a in alerts))
        model_filter = st.selectbox("Filter by Model", model_options, key="alert_model_filter")

    # Apply filters
    filtered_alerts = alerts.copy()

    if status_filter != "All":
        filtered_alerts = [a for a in filtered_alerts if a["status"] == status_filter.lower()]

    if severity_filter != "All":
        filtered_alerts = [a for a in filtered_alerts if a["severity"] == severity_filter.lower()]

    if model_filter != "All":
        filtered_alerts = [a for a in filtered_alerts if a["model"] == model_filter]

    # Sort by timestamp descending
    filtered_alerts = sorted(filtered_alerts, key=lambda x: x["timestamp"], reverse=True)

    # Create DataFrame for display
    if filtered_alerts:
        df_data = []
        for alert in filtered_alerts:
            df_data.append(
                {
                    "ID": alert["id"],
                    "Severity": alert["severity"].upper(),
                    "Model": alert["model"],
                    "Type": alert["type"].replace("_", " ").title(),
                    "Message": alert["message"][:50] + "..." if len(alert["message"]) > 50 else alert["message"],
                    "Time": format_relative_time(alert["timestamp"]),
                    "Status": alert["status"].title(),
                }
            )

        df = pd.DataFrame(df_data)

        # Apply color styling based on severity
        def highlight_severity(row):
            severity = row["Severity"]
            if severity == "CRITICAL":
                return ["background-color: rgba(239, 68, 68, 0.3)"] * len(row)
            elif severity == "HIGH":
                return ["background-color: rgba(245, 158, 11, 0.3)"] * len(row)
            elif severity == "MEDIUM":
                return ["background-color: rgba(59, 130, 246, 0.2)"] * len(row)
            else:
                return ["background-color: rgba(16, 185, 129, 0.2)"] * len(row)

        styled_df = df.style.apply(highlight_severity, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        # Export option
        export_col1, export_col2 = st.columns([1, 4])
        with export_col1:
            csv_data = df.to_csv(index=False)
            st.download_button(
                "Export to CSV",
                data=csv_data,
                file_name=f"compliance_alerts_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
    else:
        st.info("No alerts match the current filters.")


# ============================================================================
# STYLING
# ============================================================================


def inject_custom_css():
    """Inject premium dark theme CSS"""
    st.markdown(
        """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

        /* Global Typography */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Space Grotesk', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em !important;
        }

        /* Premium gradient header */
        .compliance-header {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            padding: 2rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            border: 1px solid rgba(99, 102, 241, 0.2);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }

        .compliance-header h1 {
            background: linear-gradient(90deg, #6366f1, #8b5cf6, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }

        .compliance-header p {
            color: #94a3b8;
            font-size: 1.1rem;
        }

        /* Metric cards */
        .metric-card {
            background: linear-gradient(145deg, #1e1e2e, #252538);
            border: 1px solid rgba(99, 102, 241, 0.15);
            border-radius: 16px;
            padding: 1.5rem;
            transition: all 0.3s ease;
        }

        .metric-card:hover {
            transform: translateY(-4px);
            border-color: rgba(99, 102, 241, 0.4);
            box-shadow: 0 12px 40px rgba(99, 102, 241, 0.15);
        }

        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(90deg, #10b981, #34d399);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .metric-value.warning {
            background: linear-gradient(90deg, #f59e0b, #fbbf24);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .metric-value.danger {
            background: linear-gradient(90deg, #ef4444, #f87171);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .metric-label {
            color: #94a3b8;
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 0.5rem;
        }

        /* Violation badges */
        .violation-critical {
            background: linear-gradient(90deg, #7c3aed, #8b5cf6);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .violation-high {
            background: linear-gradient(90deg, #ef4444, #f87171);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .violation-medium {
            background: linear-gradient(90deg, #f59e0b, #fbbf24);
            color: #1a1a2e;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .violation-low {
            background: linear-gradient(90deg, #3b82f6, #60a5fa);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        /* Live alerts panel */
        .alerts-panel {
            background: linear-gradient(145deg, #1e1e2e, #252538);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 16px;
            padding: 1rem;
            margin-bottom: 1rem;
        }

        .alert-item {
            padding: 0.75rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
            border-left: 4px solid;
        }

        .alert-critical {
            background: rgba(239, 68, 68, 0.15);
            border-left-color: #ef4444;
        }

        .alert-high {
            background: rgba(245, 158, 11, 0.15);
            border-left-color: #f59e0b;
        }

        .alert-medium {
            background: rgba(59, 130, 246, 0.15);
            border-left-color: #3b82f6;
        }

        .alert-low {
            background: rgba(16, 185, 129, 0.15);
            border-left-color: #10b981;
        }

        .pulse-animation {
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }

        /* Status indicators */
        .status-compliant {
            color: #10b981;
        }

        .status-warning {
            color: #f59e0b;
        }

        .status-critical {
            color: #ef4444;
        }

        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: transparent;
        }

        .stTabs [data-baseweb="tab"] {
            background-color: rgba(99, 102, 241, 0.1);
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            border: 1px solid rgba(99, 102, 241, 0.2);
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(90deg, #6366f1, #8b5cf6);
            border-color: transparent;
        }

        /* Progress bars */
        .stProgress > div > div > div {
            background: linear-gradient(90deg, #6366f1, #8b5cf6);
        }

        /* Charts container */
        .chart-container {
            background: rgba(30, 30, 46, 0.5);
            border: 1px solid rgba(99, 102, 241, 0.1);
            border-radius: 16px;
            padding: 1rem;
        }

        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #1e1e2e;
        }

        ::-webkit-scrollbar-thumb {
            background: #6366f1;
            border-radius: 4px;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


def style_plotly_chart(fig, title: str = None):
    """Apply premium dark theme to Plotly charts"""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#e2e8f0", size=12),
        title=dict(
            text=title, font=dict(family="Space Grotesk, sans-serif", size=18, color="#ffffff"), x=0, xanchor="left"
        )
        if title
        else None,
        margin=dict(l=20, r=20, t=60 if title else 20, b=20),
        xaxis=dict(
            gridcolor="rgba(99, 102, 241, 0.1)",
            zerolinecolor="rgba(99, 102, 241, 0.2)",
        ),
        yaxis=dict(
            gridcolor="rgba(99, 102, 241, 0.1)",
            zerolinecolor="rgba(99, 102, 241, 0.2)",
        ),
        legend=dict(bgcolor="rgba(30, 30, 46, 0.8)", bordercolor="rgba(99, 102, 241, 0.2)", font=dict(size=11)),
        hoverlabel=dict(bgcolor="rgba(30, 30, 46, 0.95)", font_size=13, font_family="Inter"),
    )
    return fig


# ============================================================================
# DATA LOADING
# ============================================================================


@st.cache_data(ttl=300)
def load_demo_data() -> Dict[str, Any]:
    """Load demo data for dashboard"""
    if PLATFORM_AVAILABLE:
        generator = DemoDataGenerator(seed=42)
        return generator.generate_full_demo_dataset()
    else:
        # Fallback demo data
        return generate_fallback_data()


def generate_fallback_data() -> Dict[str, Any]:
    """Generate fallback data if platform not available"""
    import random

    random.seed(42)

    # Generate 90 days of trend data
    trends = []
    base_score = 75
    for i in range(90):
        date = datetime.now() - timedelta(days=90 - i - 1)
        improvement = i * 0.15
        noise = random.uniform(-2, 2)
        score = min(98, base_score + improvement + noise)
        trends.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "compliance_score": round(score, 1),
                "active_violations": max(1, int(8 - i * 0.05 + random.randint(-1, 1))),
                "models_assessed": random.randint(8, 12),
            }
        )

    return {
        "executive_metrics": {
            "total_models": 12,
            "compliant_models": 8,
            "average_compliance_score": 87.3,
            "total_violations": 7,
            "critical_violations": 1,
            "high_violations": 3,
            "potential_exposure": 35_000_000,
            "compliance_trend": 5.2,
            "remediation_rate": 85.0,
            "audit_readiness": 92.0,
        },
        "trends": trends,
        "heatmap": [
            {"category": "Transparency", "regulation": "EU AI Act", "risk_score": 35},
            {"category": "Fairness", "regulation": "EU AI Act", "risk_score": 45},
            {"category": "Accountability", "regulation": "EU AI Act", "risk_score": 28},
            {"category": "Robustness", "regulation": "EU AI Act", "risk_score": 55},
            {"category": "Privacy", "regulation": "EU AI Act", "risk_score": 32},
            {"category": "Security", "regulation": "EU AI Act", "risk_score": 25},
            {"category": "Transparency", "regulation": "HIPAA", "risk_score": 42},
            {"category": "Fairness", "regulation": "HIPAA", "risk_score": 38},
            {"category": "Accountability", "regulation": "HIPAA", "risk_score": 30},
            {"category": "Robustness", "regulation": "HIPAA", "risk_score": 48},
            {"category": "Privacy", "regulation": "HIPAA", "risk_score": 65},
            {"category": "Security", "regulation": "HIPAA", "risk_score": 35},
            {"category": "Transparency", "regulation": "SEC", "risk_score": 50},
            {"category": "Fairness", "regulation": "SEC", "risk_score": 58},
            {"category": "Accountability", "regulation": "SEC", "risk_score": 45},
            {"category": "Robustness", "regulation": "SEC", "risk_score": 40},
            {"category": "Privacy", "regulation": "SEC", "risk_score": 30},
            {"category": "Security", "regulation": "SEC", "risk_score": 28},
            {"category": "Transparency", "regulation": "GDPR", "risk_score": 38},
            {"category": "Fairness", "regulation": "GDPR", "risk_score": 42},
            {"category": "Accountability", "regulation": "GDPR", "risk_score": 35},
            {"category": "Robustness", "regulation": "GDPR", "risk_score": 45},
            {"category": "Privacy", "regulation": "GDPR", "risk_score": 55},
            {"category": "Security", "regulation": "GDPR", "risk_score": 32},
        ],
        "violations": [
            {
                "severity": "critical",
                "policy_name": "PHI Encryption",
                "regulation": "HIPAA",
                "days_open": 5,
                "potential_fine": 1500000,
            },
            {
                "severity": "high",
                "policy_name": "Human Oversight",
                "regulation": "EU AI Act",
                "days_open": 12,
                "potential_fine": 15000000,
            },
            {
                "severity": "high",
                "policy_name": "Technical Documentation",
                "regulation": "EU AI Act",
                "days_open": 8,
                "potential_fine": 7500000,
            },
            {
                "severity": "high",
                "policy_name": "DPIA Not Conducted",
                "regulation": "GDPR",
                "days_open": 15,
                "potential_fine": 20000000,
            },
            {
                "severity": "medium",
                "policy_name": "AI System Disclosure",
                "regulation": "EU AI Act",
                "days_open": 20,
                "potential_fine": 7500000,
            },
            {
                "severity": "medium",
                "policy_name": "Audit Controls",
                "regulation": "HIPAA",
                "days_open": 18,
                "potential_fine": 250000,
            },
            {
                "severity": "low",
                "policy_name": "Model Validation",
                "regulation": "SEC",
                "days_open": 25,
                "potential_fine": 0,
            },
        ],
        "models": [
            {"name": "DiagnosticAI Pro", "risk_level": "high", "status": "partially_compliant", "score": 72},
            {"name": "FraudGuard ML", "risk_level": "high", "status": "compliant", "score": 94},
            {"name": "CreditScore AI", "risk_level": "high", "status": "partially_compliant", "score": 78},
            {"name": "TalentMatch AI", "risk_level": "high", "status": "non_compliant", "score": 58},
            {"name": "CustomerBot Pro", "risk_level": "limited", "status": "compliant", "score": 91},
            {"name": "SentimentAnalyzer", "risk_level": "minimal", "status": "compliant", "score": 96},
            {"name": "SupplyChain Optimizer", "risk_level": "minimal", "status": "compliant", "score": 98},
            {"name": "QualityVision AI", "risk_level": "limited", "status": "compliant", "score": 89},
            {"name": "ContractAnalyzer", "risk_level": "limited", "status": "partially_compliant", "score": 82},
            {"name": "PatientFlow Optimizer", "risk_level": "limited", "status": "compliant", "score": 88},
            {"name": "MarketSense Predictor", "risk_level": "limited", "status": "compliant", "score": 90},
            {"name": "PerformancePredict", "risk_level": "high", "status": "partially_compliant", "score": 75},
        ],
    }


# ============================================================================
# VISUALIZATION COMPONENTS
# ============================================================================


def render_compliance_gauge(score: float, title: str = "Compliance Score"):
    """Render a compliance score gauge"""
    color = "#10b981" if score >= 80 else "#f59e0b" if score >= 60 else "#ef4444"

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=score,
            delta={
                "reference": 80,
                "relative": False,
                "increasing": {"color": "#10b981"},
                "decreasing": {"color": "#ef4444"},
            },
            title={"text": title, "font": {"size": 16, "color": "#e2e8f0"}},
            number={"font": {"size": 48, "color": color}, "suffix": "%"},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#64748b"},
                "bar": {"color": color, "thickness": 0.7},
                "bgcolor": "rgba(30, 30, 46, 0.5)",
                "borderwidth": 2,
                "bordercolor": "rgba(99, 102, 241, 0.3)",
                "steps": [
                    {"range": [0, 60], "color": "rgba(239, 68, 68, 0.2)"},
                    {"range": [60, 80], "color": "rgba(245, 158, 11, 0.2)"},
                    {"range": [80, 100], "color": "rgba(16, 185, 129, 0.2)"},
                ],
                "threshold": {"line": {"color": "#6366f1", "width": 3}, "thickness": 0.8, "value": 80},
            },
        )
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter"),
        height=280,
        margin=dict(l=30, r=30, t=60, b=30),
    )

    return fig


def render_risk_heatmap(heatmap_data: List[Dict]):
    """Render risk heatmap visualization"""
    df = pd.DataFrame(heatmap_data)
    pivot = df.pivot(index="category", columns="regulation", values="risk_score")

    # Define custom colorscale (green to red)
    colorscale = [
        [0, "#10b981"],  # Green (low risk)
        [0.4, "#fbbf24"],  # Yellow
        [0.6, "#f59e0b"],  # Orange
        [0.8, "#ef4444"],  # Red
        [1, "#7c3aed"],  # Purple (critical)
    ]

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale=colorscale,
            showscale=True,
            colorbar=dict(
                title="Risk Score",
                titleside="right",
                tickfont=dict(color="#e2e8f0"),
                titlefont=dict(color="#e2e8f0"),
            ),
            hovertemplate="<b>%{y}</b><br>%{x}: %{z}<extra></extra>",
        )
    )

    # Add annotations
    for i, cat in enumerate(pivot.index):
        for j, reg in enumerate(pivot.columns):
            val = pivot.iloc[i, j]
            text_color = "#ffffff" if val > 50 else "#1a1a2e"
            fig.add_annotation(
                x=reg,
                y=cat,
                text=f"{val:.0f}",
                showarrow=False,
                font=dict(color=text_color, size=12, family="Inter"),
            )

    fig = style_plotly_chart(fig, "Risk Assessment Matrix")
    fig.update_layout(height=400)

    return fig


def render_compliance_trend(trend_data: List[Dict]):
    """Render compliance trend chart"""
    df = pd.DataFrame(trend_data)
    df["date"] = pd.to_datetime(df["date"])

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=[0.7, 0.3],
        subplot_titles=("Compliance Score Trend", "Active Violations"),
    )

    # Compliance score area chart
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["compliance_score"],
            mode="lines",
            name="Compliance Score",
            line=dict(color="#6366f1", width=3),
            fill="tozeroy",
            fillcolor="rgba(99, 102, 241, 0.2)",
            hovertemplate="<b>%{x|%b %d}</b><br>Score: %{y:.1f}%<extra></extra>",
        ),
        row=1,
        col=1,
    )

    # Target line
    fig.add_hline(
        y=80,
        line_dash="dash",
        line_color="#10b981",
        annotation_text="Target: 80%",
        annotation_position="right",
        row=1,
        col=1,
    )

    # Violations bar chart
    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["active_violations"],
            name="Violations",
            marker=dict(
                color=df["active_violations"],
                colorscale=[[0, "#10b981"], [0.5, "#f59e0b"], [1, "#ef4444"]],
            ),
            hovertemplate="<b>%{x|%b %d}</b><br>Violations: %{y}<extra></extra>",
        ),
        row=2,
        col=1,
    )

    fig = style_plotly_chart(fig)
    fig.update_layout(
        height=500,
        showlegend=False,
        xaxis2=dict(title="Date"),
        yaxis=dict(title="Score %", range=[50, 100]),
        yaxis2=dict(title="Count"),
    )

    return fig


def render_regulation_pie(data: Dict):
    """Render regulation distribution pie chart"""
    regulations = ["EU AI Act", "HIPAA", "SEC", "GDPR"]
    values = [5, 3, 2, 4]  # Number of models per regulation

    fig = go.Figure(
        data=[
            go.Pie(
                labels=regulations,
                values=values,
                hole=0.6,
                marker=dict(colors=["#6366f1", "#8b5cf6", "#a855f7", "#c084fc"], line=dict(color="#1a1a2e", width=2)),
                textinfo="label+percent",
                textfont=dict(color="#e2e8f0", size=12),
                hovertemplate="<b>%{label}</b><br>Models: %{value}<br>%{percent}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        showlegend=False,
        annotations=[dict(text="Regulations", x=0.5, y=0.5, font_size=14, showarrow=False, font_color="#94a3b8")],
    )

    fig = style_plotly_chart(fig, "Regulatory Coverage")
    fig.update_layout(height=350)

    return fig


def render_model_scores_bar(models: List[Dict]):
    """Render model scores horizontal bar chart"""
    df = pd.DataFrame(models)
    df = df.sort_values("score", ascending=True)

    colors = df["score"].apply(lambda x: "#10b981" if x >= 80 else "#f59e0b" if x >= 60 else "#ef4444").tolist()

    fig = go.Figure(
        go.Bar(
            y=df["name"],
            x=df["score"],
            orientation="h",
            marker=dict(color=colors),
            text=df["score"].apply(lambda x: f"{x}%"),
            textposition="outside",
            textfont=dict(color="#e2e8f0", size=11),
            hovertemplate="<b>%{y}</b><br>Score: %{x}%<extra></extra>",
        )
    )

    # Add target line
    fig.add_vline(x=80, line_dash="dash", line_color="#6366f1", annotation_text="Target", annotation_position="top")

    fig = style_plotly_chart(fig, "AI Model Compliance Scores")
    fig.update_layout(
        height=450,
        xaxis=dict(title="Compliance Score %", range=[0, 105]),
        yaxis=dict(title=""),
    )

    return fig


# ============================================================================
# MAIN DASHBOARD
# ============================================================================


def main():
    """Main dashboard function"""
    inject_custom_css()

    # Load data
    data = load_demo_data()
    metrics = data["executive_metrics"]

    # Header
    st.markdown(
        """
    <div class="compliance-header">
        <h1>🛡️ Enterprise AI Compliance Platform</h1>
        <p>Real-time compliance monitoring for EU AI Act, SEC, HIPAA, and GDPR regulations</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # ========================================================================
    # TOP METRICS ROW
    # ========================================================================

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        score = metrics["average_compliance_score"]
        color_class = "" if score >= 80 else "warning" if score >= 60 else "danger"
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-value {color_class}">{score:.1f}%</div>
            <div class="metric-label">Compliance Score</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-value">{metrics["total_models"]}</div>
            <div class="metric-label">AI Models Tracked</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        violations = metrics["total_violations"]
        color_class = "danger" if violations > 5 else "warning" if violations > 2 else ""
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-value {color_class}">{violations}</div>
            <div class="metric-label">Active Violations</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        exposure = metrics["potential_exposure"]
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-value danger">€{exposure / 1_000_000:.0f}M</div>
            <div class="metric-label">Potential Exposure</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col5:
        trend = metrics["compliance_trend"]
        trend_icon = "📈" if trend > 0 else "📉"
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-value">{trend_icon} +{trend:.1f}%</div>
            <div class="metric-label">30-Day Trend</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ========================================================================
    # MAIN CONTENT TABS
    # ========================================================================

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        [
            "📊 Executive Overview",
            "⚠️ Violations Center",
            "🔥 Risk Heatmap",
            "🤖 AI Models",
            "📈 Trends & Analytics",
            "🧠 AI Insights",
            "📊 Predictive Analytics",
        ]
    )

    # ========================================================================
    # TAB 1: EXECUTIVE OVERVIEW
    # ========================================================================

    with tab1:
        # ====================================================================
        # LIVE ALERTS PANEL (at top before existing content)
        # ====================================================================
        alerts = get_demo_alerts()

        render_live_alerts_panel(alerts, max_alerts=5)

        st.markdown("---")

        # ====================================================================
        # ALERT HISTORY (expandable section)
        # ====================================================================
        with st.expander("📋 View Full Alert History", expanded=False):
            render_alert_history_table(alerts)

        st.markdown("---")

        # ====================================================================
        # EXISTING EXECUTIVE OVERVIEW CONTENT
        # ====================================================================
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.plotly_chart(
                render_compliance_gauge(metrics["average_compliance_score"], "Overall Compliance"),
                use_container_width=True,
                config={"displayModeBar": False},
            )

            # Quick stats
            st.markdown("### 📌 Quick Status")

            status_col1, status_col2 = st.columns(2)
            with status_col1:
                st.metric(
                    "Compliant Models",
                    f"{metrics['compliant_models']}/{metrics['total_models']}",
                    f"{(metrics['compliant_models'] / metrics['total_models'] * 100):.0f}%",
                )
                st.metric(
                    "Audit Readiness",
                    f"{metrics['audit_readiness']:.0f}%",
                    "+3%" if metrics["audit_readiness"] > 90 else "-2%",
                )

            with status_col2:
                st.metric("Remediation Rate", f"{metrics['remediation_rate']:.0f}%", "+5%")
                st.metric(
                    "Critical Issues",
                    metrics["critical_violations"],
                    "-1" if metrics["critical_violations"] <= 1 else "+1",
                    delta_color="inverse",
                )

        with col_right:
            st.plotly_chart(render_regulation_pie(data), use_container_width=True, config={"displayModeBar": False})

            # Regulation compliance breakdown
            st.markdown("### 🏛️ Regulation Compliance")

            regulations = [
                {"name": "EU AI Act", "score": 85, "status": "Partial"},
                {"name": "HIPAA", "score": 78, "status": "Partial"},
                {"name": "SEC Guidance", "score": 92, "status": "Compliant"},
                {"name": "GDPR", "score": 88, "status": "Compliant"},
            ]

            for reg in regulations:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.progress(reg["score"] / 100, text=f"{reg['name']}: {reg['score']}%")
                with col_b:
                    status_color = "🟢" if reg["status"] == "Compliant" else "🟡"
                    st.write(f"{status_color} {reg['status']}")

    # ========================================================================
    # TAB 2: VIOLATIONS CENTER
    # ========================================================================

    with tab2:
        st.markdown("### ⚠️ Active Compliance Violations")

        # Violation summary
        v_col1, v_col2, v_col3, v_col4 = st.columns(4)
        with v_col1:
            st.error(f"🔴 Critical: {metrics['critical_violations']}")
        with v_col2:
            st.warning(f"🟠 High: {metrics['high_violations']}")
        with v_col3:
            st.info(
                f"🟡 Medium: {metrics['total_violations'] - metrics['critical_violations'] - metrics['high_violations'] - 1}"
            )
        with v_col4:
            st.success(f"🟢 Low: 1")

        st.markdown("---")

        # Violations table
        violations = data.get("violations", [])

        for v in violations:
            severity = v.get("severity", "medium")
            severity_badge = {"critical": "🔴 CRITICAL", "high": "🟠 HIGH", "medium": "🟡 MEDIUM", "low": "🟢 LOW"}.get(
                severity, "🟡 MEDIUM"
            )

            with st.container(border=True):
                col_info, col_action = st.columns([4, 1])

                with col_info:
                    st.markdown(f"**{severity_badge}** | {v.get('regulation', 'Unknown')}")
                    st.markdown(f"### {v.get('policy_name', 'Policy Violation')}")
                    st.caption(
                        f"📅 Open for {v.get('days_open', 0)} days | 💰 Potential Fine: €{v.get('potential_fine', 0):,}"
                    )

                with col_action:
                    if st.button("🔧 Remediate", key=f"rem_{v.get('policy_name', '')}"):
                        st.toast(f"Opening remediation workflow for {v.get('policy_name', '')}", icon="🔧")

    # ========================================================================
    # TAB 3: RISK HEATMAP
    # ========================================================================

    with tab3:
        st.markdown("### 🔥 Risk Assessment Matrix")
        st.caption("Risk scores by compliance category and regulation (0 = Low Risk, 100 = Critical Risk)")

        st.plotly_chart(
            render_risk_heatmap(data["heatmap"]), use_container_width=True, config={"displayModeBar": False}
        )

        st.markdown("---")

        # Risk legend
        legend_col1, legend_col2, legend_col3, legend_col4 = st.columns(4)
        with legend_col1:
            st.markdown("🟢 **0-30**: Low Risk")
        with legend_col2:
            st.markdown("🟡 **31-50**: Moderate Risk")
        with legend_col3:
            st.markdown("🟠 **51-70**: High Risk")
        with legend_col4:
            st.markdown("🔴 **71-100**: Critical Risk")

    # ========================================================================
    # TAB 4: AI MODELS
    # ========================================================================

    with tab4:
        st.markdown("### 🤖 AI Model Registry & Compliance")

        st.plotly_chart(
            render_model_scores_bar(data["models"]), use_container_width=True, config={"displayModeBar": False}
        )

        st.markdown("---")
        st.markdown("### 📋 Model Details")

        # Model cards
        models = data.get("models", [])
        cols = st.columns(3)

        for i, model in enumerate(models):
            with cols[i % 3]:
                status_emoji = {"compliant": "✅", "partially_compliant": "⚠️", "non_compliant": "❌"}.get(
                    model.get("status", ""), "❓"
                )

                risk_emoji = {"high": "🔴", "limited": "🟡", "minimal": "🟢"}.get(model.get("risk_level", ""), "⚪")

                with st.container(border=True):
                    st.markdown(f"**{model['name']}**")
                    st.caption(f"{status_emoji} Status: {model.get('status', 'Unknown').replace('_', ' ').title()}")
                    st.caption(f"{risk_emoji} Risk Level: {model.get('risk_level', 'Unknown').title()}")
                    st.progress(model.get("score", 0) / 100, text=f"Score: {model.get('score', 0)}%")

    # ========================================================================
    # TAB 5: TRENDS & ANALYTICS
    # ========================================================================

    with tab5:
        st.markdown("### 📈 Compliance Trends (90 Days)")

        st.plotly_chart(
            render_compliance_trend(data["trends"]), use_container_width=True, config={"displayModeBar": False}
        )

        st.markdown("---")

        # Key insights
        st.markdown("### 💡 Key Insights")

        insight_col1, insight_col2 = st.columns(2)

        with insight_col1:
            st.success("""
            **📈 Positive Trends**
            - Compliance score improved 5.2% over 30 days
            - Critical violations reduced from 3 to 1
            - 85% remediation completion rate
            - Audit readiness at 92%
            """)

        with insight_col2:
            st.warning("""
            **⚠️ Areas of Focus**
            - 4 models below 80% compliance threshold
            - HIPAA privacy controls need attention
            - SEC model validation documentation gaps
            - EU AI Act human oversight requirements
            """)

    # ========================================================================
    # TAB 6: AI INSIGHTS
    # ========================================================================

    with tab6:
        st.markdown("### 🧠 AI-Powered Compliance Intelligence")

        # Initialize session state for chat history
        if "compliance_chat_history" not in st.session_state:
            st.session_state.compliance_chat_history = []

        # Check AI availability status
        if not AI_AVAILABLE:
            st.info(
                "ℹ️ Running in demo mode with mock AI responses. Connect ComplianceAIAnalyzer service for production use."
            )

        # Create three columns for the main layout
        ai_col1, ai_col2 = st.columns([2, 1])

        with ai_col1:
            st.markdown("#### 💬 Compliance Advisor Chat")

            # Context selector
            context_options = ["All Models", "High-Risk Models Only", "Non-Compliant Models", "Specific Regulation"]
            selected_context = st.selectbox(
                "Select Context", context_options, help="Choose which models/data the AI should focus on when answering"
            )

            # Example questions as buttons
            st.markdown("**Quick Questions:**")
            example_col1, example_col2, example_col3 = st.columns(3)

            with example_col1:
                if st.button("🎯 Biggest Risks", use_container_width=True):
                    st.session_state.pending_question = "What are our biggest compliance risks?"

            with example_col2:
                if st.button("🇪🇺 EU AI Act", use_container_width=True):
                    st.session_state.pending_question = "How do we achieve EU AI Act compliance?"

            with example_col3:
                if st.button("⚠️ Violations", use_container_width=True):
                    st.session_state.pending_question = "Explain our current violations"

            # Text input for custom questions
            user_question = st.text_input(
                "Ask a compliance question",
                placeholder="e.g., What steps do we need for HIPAA compliance?",
                key="compliance_question_input",
            )

            # Check for pending question from button click
            if "pending_question" in st.session_state:
                user_question = st.session_state.pending_question
                del st.session_state.pending_question

            # Process question
            if user_question:
                with st.spinner("🤔 Analyzing compliance data..."):
                    try:
                        analyzer = get_ai_analyzer()
                        # Run async function
                        response = run_async(
                            analyzer.answer_compliance_question(user_question, context=selected_context)
                        )

                        # Add to chat history
                        st.session_state.compliance_chat_history.append(
                            {
                                "question": user_question,
                                "response": response,
                                "timestamp": datetime.now().strftime("%H:%M"),
                                "context": selected_context,
                            }
                        )
                    except Exception as e:
                        st.error(f"Error generating response: {str(e)}")

            # Display chat history
            st.markdown("---")
            st.markdown("#### 📜 Conversation History")

            if st.session_state.compliance_chat_history:
                for i, chat in enumerate(reversed(st.session_state.compliance_chat_history)):
                    with st.expander(f"Q: {chat['question'][:50]}... ({chat['timestamp']})", expanded=(i == 0)):
                        st.markdown(f"**Context**: {chat['context']}")
                        st.markdown("---")
                        st.markdown(chat["response"])

                # Clear history button
                if st.button("🗑️ Clear History", key="clear_chat"):
                    st.session_state.compliance_chat_history = []
                    st.rerun()
            else:
                st.caption("No conversation history yet. Ask a question to get started.")

        with ai_col2:
            st.markdown("#### 🔍 AI Risk Analysis")

            # Model selector for risk analysis
            model_names = [m["name"] for m in data.get("models", [])]
            selected_model = st.selectbox(
                "Select Model to Analyze", model_names, help="Choose a registered AI model for detailed risk analysis"
            )

            # Get selected model data
            selected_model_data = next(
                (m for m in data.get("models", []) if m["name"] == selected_model),
                {"name": selected_model, "score": 75, "risk_level": "limited", "status": "partially_compliant"},
            )

            # Generate Analysis button
            if st.button("🔬 Generate AI Analysis", use_container_width=True, type="primary"):
                with st.spinner(f"Analyzing {selected_model}..."):
                    try:
                        analyzer = get_ai_analyzer()
                        analysis = run_async(analyzer.analyze_model_risks(selected_model, selected_model_data))

                        st.session_state.current_model_analysis = analysis
                    except Exception as e:
                        st.error(f"Analysis failed: {str(e)}")

            # Display analysis results
            if "current_model_analysis" in st.session_state:
                analysis = st.session_state.current_model_analysis

                st.markdown("---")
                st.markdown(f"**Model**: {analysis['model_name']}")
                st.metric("Overall Risk Score", f"{analysis['overall_risk_score']}%")

                # Risk dimensions
                st.markdown("##### Risk Dimensions")
                for dim_name, dim_data in analysis.get("risk_dimensions", {}).items():
                    priority_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(dim_data["priority"], "⚪")
                    with st.expander(f"{priority_color} {dim_name.title()} ({dim_data['score']}%)"):
                        st.progress(dim_data["score"] / 100)
                        st.caption(dim_data["assessment"])

                # Recommendations
                if analysis.get("recommendations"):
                    st.markdown("##### 💡 Recommendations")
                    for rec in analysis["recommendations"][:4]:
                        st.markdown(f"- {rec}")

                # Compliance gaps
                if analysis.get("compliance_gaps"):
                    st.markdown("##### ⚠️ Compliance Gaps")
                    for gap in analysis["compliance_gaps"]:
                        st.warning(gap)

        # Executive Summary Section (full width below)
        st.markdown("---")
        st.markdown("#### 📋 AI-Powered Report Generation")

        report_col1, report_col2, report_col3 = st.columns([1, 1, 2])

        with report_col1:
            if st.button("📊 Generate Executive Summary", use_container_width=True, type="primary"):
                with st.spinner("Generating executive summary..."):
                    try:
                        analyzer = get_ai_analyzer()
                        summary = run_async(analyzer.generate_executive_summary(data))
                        st.session_state.executive_summary = summary
                        st.toast("Executive summary generated!", icon="✅")
                    except Exception as e:
                        st.error(f"Failed to generate summary: {str(e)}")

        with report_col2:
            if "executive_summary" in st.session_state:
                if st.button("📋 Copy to Clipboard", use_container_width=True):
                    st.toast("Summary copied! (Use browser copy for actual clipboard)", icon="📋")

                st.download_button(
                    "📥 Download Report",
                    data=st.session_state.executive_summary,
                    file_name=f"compliance_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

        with report_col3:
            pass  # Spacer

        # Display generated summary
        if "executive_summary" in st.session_state:
            st.markdown("---")
            with st.expander("📄 Executive Summary Report", expanded=True):
                st.markdown(st.session_state.executive_summary)

    # ========================================================================
    # TAB 7: PREDICTIVE ANALYTICS
    # ========================================================================

    with tab7:
        st.header("📊 Predictive Analytics")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Score Forecasting")

            # Model selector
            forecast_models = list(DEMO_PREDICTIONS.keys())
            forecast_model_names = {
                "lead_scorer": "Lead Scorer",
                "property_matcher": "Property Matcher",
                "diagnostic_ai": "DiagnosticAI Pro",
                "fraud_guard": "FraudGuard ML",
            }

            selected_forecast_model = st.selectbox(
                "Select Model",
                forecast_models,
                format_func=lambda x: forecast_model_names.get(x, x),
                key="forecast_model_select",
            )

            # Timeframe selector
            timeframe = st.selectbox(
                "Forecast Timeframe", ["1 week", "2 weeks", "1 month", "3 months"], key="forecast_timeframe"
            )

            # Generate Forecast button
            if st.button("Generate Forecast", type="primary", use_container_width=True, key="generate_forecast"):
                st.session_state.show_forecast = True

            # Display forecast results
            if st.session_state.get("show_forecast", False) or selected_forecast_model:
                prediction = DEMO_PREDICTIONS.get(selected_forecast_model, DEMO_PREDICTIONS["lead_scorer"])

                st.markdown("---")

                # Current vs Predicted scores
                score_col1, score_col2, score_col3 = st.columns(3)

                with score_col1:
                    current = prediction["current_score"]
                    color = "normal" if current >= 80 else "off" if current >= 60 else "inverse"
                    st.metric("Current Score", f"{current}%", delta=None)

                with score_col2:
                    predicted = prediction["predicted_score"]
                    delta = predicted - current
                    st.metric(
                        "Predicted Score",
                        f"{predicted}%",
                        delta=f"{delta:+.1f}%",
                        delta_color="normal" if delta >= 0 else "inverse",
                    )

                with score_col3:
                    confidence = prediction["confidence"]
                    st.metric("Confidence", f"{confidence * 100:.0f}%", delta=None)

                # Trend indicator
                trend = prediction["trend"]
                trend_icons = {"improving": "📈", "stable": "➡️", "declining": "📉"}
                trend_colors = {"improving": "success", "stable": "info", "declining": "error"}

                if trend == "improving":
                    st.success(f"{trend_icons[trend]} Trend: {trend.title()} - Score expected to increase")
                elif trend == "stable":
                    st.info(f"{trend_icons[trend]} Trend: {trend.title()} - Score expected to remain consistent")
                else:
                    st.error(f"{trend_icons[trend]} Trend: {trend.title()} - Score expected to decrease")

                # Historical + Predicted trend line chart
                st.markdown("##### Score Trend (Historical + Forecast)")

                # Generate demo trend data
                import random

                random.seed(42)

                base_score = prediction["current_score"]
                dates = []
                scores = []
                is_forecast = []

                # Historical data (past 30 days)
                for i in range(30, 0, -1):
                    dates.append((datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"))
                    noise = random.uniform(-3, 3)
                    hist_score = base_score - (30 - i) * 0.1 + noise
                    scores.append(max(50, min(100, hist_score)))
                    is_forecast.append(False)

                # Current day
                dates.append(datetime.now().strftime("%Y-%m-%d"))
                scores.append(prediction["current_score"])
                is_forecast.append(False)

                # Forecast data
                forecast_days = {"1 week": 7, "2 weeks": 14, "1 month": 30, "3 months": 90}
                days_ahead = forecast_days.get(timeframe, 7)

                score_delta = prediction["predicted_score"] - prediction["current_score"]
                for i in range(1, days_ahead + 1):
                    dates.append((datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"))
                    progress = i / days_ahead
                    forecast_score = prediction["current_score"] + (score_delta * progress) + random.uniform(-1, 1)
                    scores.append(max(50, min(100, forecast_score)))
                    is_forecast.append(True)

                # Create chart
                trend_df = pd.DataFrame(
                    {
                        "Date": dates,
                        "Score": scores,
                        "Type": ["Historical" if not f else "Forecast" for f in is_forecast],
                    }
                )

                fig = px.line(
                    trend_df,
                    x="Date",
                    y="Score",
                    color="Type",
                    color_discrete_map={"Historical": "#6366f1", "Forecast": "#a855f7"},
                    markers=True,
                )

                fig.add_hline(y=80, line_dash="dash", line_color="#10b981", annotation_text="Target: 80%")
                fig = style_plotly_chart(fig)
                fig.update_layout(height=300)

                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        with col2:
            st.subheader("Risk Forecast")

            # Get prediction for selected model
            prediction = DEMO_PREDICTIONS.get(
                st.session_state.get("forecast_model_select", "lead_scorer"), DEMO_PREDICTIONS["lead_scorer"]
            )

            # Current vs Predicted risk level
            current_score = prediction["current_score"]
            predicted_score = prediction["predicted_score"]

            def get_risk_level(score):
                if score >= 85:
                    return ("Low", "🟢", "success")
                elif score >= 70:
                    return ("Medium", "🟡", "warning")
                else:
                    return ("High", "🔴", "error")

            current_risk, current_icon, current_color = get_risk_level(current_score)
            predicted_risk, predicted_icon, predicted_color = get_risk_level(predicted_score)

            risk_col1, risk_col2 = st.columns(2)

            with risk_col1:
                st.markdown("**Current Risk Level**")
                if current_color == "success":
                    st.success(f"{current_icon} {current_risk}")
                elif current_color == "warning":
                    st.warning(f"{current_icon} {current_risk}")
                else:
                    st.error(f"{current_icon} {current_risk}")

            with risk_col2:
                st.markdown("**Predicted Risk Level**")
                if predicted_color == "success":
                    st.success(f"{predicted_icon} {predicted_risk}")
                elif predicted_color == "warning":
                    st.warning(f"{predicted_icon} {predicted_risk}")
                else:
                    st.error(f"{predicted_icon} {predicted_risk}")

            st.markdown("---")

            # Contributing factors
            st.markdown("##### Contributing Factors")

            risk_factors = prediction.get("risk_factors", [])
            if risk_factors:
                for factor in risk_factors:
                    st.markdown(f"- ⚠️ {factor}")
            else:
                st.success("No significant risk factors identified")

            st.markdown("---")

            # Mitigation impact estimates
            st.markdown("##### Mitigation Impact Estimates")

            mitigations = [
                {"action": "Complete pending audits", "impact": "+3.5%", "effort": "Medium"},
                {"action": "Update documentation", "impact": "+2.1%", "effort": "Low"},
                {"action": "Implement human oversight", "impact": "+5.8%", "effort": "High"},
                {"action": "Resolve critical violations", "impact": "+4.2%", "effort": "Medium"},
            ]

            for m in mitigations:
                mit_col1, mit_col2, mit_col3 = st.columns([3, 1, 1])
                with mit_col1:
                    st.caption(m["action"])
                with mit_col2:
                    st.markdown(f"**{m['impact']}**")
                with mit_col3:
                    effort_color = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}.get(m["effort"], "⚪")
                    st.caption(f"{effort_color} {m['effort']}")

        st.markdown("---")

        # Anomaly Detection Section
        st.subheader("Anomaly Detection")

        # Table of detected anomalies
        anomaly_data = []
        for anomaly in DEMO_ANOMALIES:
            severity_badge = {"critical": "🔴 CRITICAL", "high": "🟠 HIGH", "medium": "🟡 MEDIUM", "low": "🟢 LOW"}.get(
                anomaly["severity"], "⚪ UNKNOWN"
            )

            anomaly_data.append(
                {
                    "Model": anomaly["model"],
                    "Type": anomaly["type"].replace("_", " ").title(),
                    "Severity": severity_badge,
                    "Detected": anomaly["detected"],
                    "Description": anomaly["description"],
                }
            )

        anomaly_df = pd.DataFrame(anomaly_data)

        # Apply color styling based on severity text
        def highlight_anomaly_severity(row):
            severity = row["Severity"]
            if "CRITICAL" in severity:
                return ["background-color: rgba(239, 68, 68, 0.3)"] * len(row)
            elif "HIGH" in severity:
                return ["background-color: rgba(245, 158, 11, 0.3)"] * len(row)
            elif "MEDIUM" in severity:
                return ["background-color: rgba(59, 130, 246, 0.2)"] * len(row)
            else:
                return ["background-color: rgba(16, 185, 129, 0.2)"] * len(row)

        styled_anomaly_df = anomaly_df.style.apply(highlight_anomaly_severity, axis=1)
        st.dataframe(styled_anomaly_df, use_container_width=True, hide_index=True)

        # Investigation recommendations
        st.markdown("##### Investigation Recommendations")

        critical_anomalies = [a for a in DEMO_ANOMALIES if a["severity"] == "critical"]
        high_anomalies = [a for a in DEMO_ANOMALIES if a["severity"] == "high"]

        if critical_anomalies:
            for anomaly in critical_anomalies:
                st.error(
                    f"**URGENT**: Investigate {anomaly['model']} - {anomaly['description']}. Immediate action required."
                )

        if high_anomalies:
            for anomaly in high_anomalies:
                st.warning(
                    f"**Priority**: Review {anomaly['model']} - {anomaly['description']}. Schedule investigation within 24 hours."
                )

        if not critical_anomalies and not high_anomalies:
            st.success("No critical or high-priority anomalies requiring immediate investigation.")

    # ========================================================================
    # SIDEBAR
    # ========================================================================

    with st.sidebar:
        # ====================================================================
        # ORGANIZATION SWITCHER (Multi-Tenant)
        # ====================================================================
        st.markdown("### 🏢 Organization")

        # Organization selector
        org_names = [org["name"] for org in DEMO_ORGANIZATIONS]
        selected_org_name = st.selectbox("Select Organization", org_names, key="org_selector")

        # Get selected organization data
        selected_org = next(
            (org for org in DEMO_ORGANIZATIONS if org["name"] == selected_org_name), DEMO_ORGANIZATIONS[0]
        )

        # Display organization tier
        tier = selected_org["tier"]
        tier_emoji = {"enterprise": "💎", "professional": "⭐", "starter": "🚀"}.get(tier, "📦")
        st.caption(f"Tier: {tier_emoji} {tier.title()}")

        # User role display
        org_email_domain = selected_org_name.lower().replace(" ", "").replace(".", "")
        st.markdown(f"**User:** compliance.officer@{org_email_domain}.com")
        st.markdown(f"**Role:** Compliance Officer")

        # ====================================================================
        # USER PERMISSIONS INDICATOR
        # ====================================================================
        with st.expander("🔐 Permissions"):
            user_permissions = DEMO_USER_ROLES["compliance_officer"]["permissions"]
            for permission in user_permissions:
                st.checkbox(permission, value=True, disabled=True, key=f"perm_{permission}")

        # ====================================================================
        # SUBSCRIPTION TIER BANNER
        # ====================================================================
        models_remaining = selected_org["models_limit"] - selected_org["models_used"]

        if tier != "enterprise":
            st.info(f"📦 **{tier.title()} Plan** - {models_remaining} models remaining. [Upgrade →](#)")
        else:
            st.success(f"💎 **Enterprise Plan** - Unlimited models")

        st.markdown("---")

        st.markdown("## 🎛️ Controls")

        # ====================================================================
        # REAL-TIME METRICS & AUTO-REFRESH
        # ====================================================================
        st.markdown("### 📡 Real-Time Monitoring")

        # Get current alerts and metrics
        alerts = get_demo_alerts()
        alert_metrics = get_alert_metrics(alerts)

        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=False, key="auto_refresh_toggle")

        if auto_refresh:
            st.caption("Dashboard will refresh automatically...")
            # Create a placeholder for countdown
            refresh_placeholder = st.empty()
            # Use st.empty() to show countdown and trigger rerun
            for remaining in range(30, 0, -1):
                refresh_placeholder.caption(f"Next refresh in: {remaining}s")
                time.sleep(1)
            refresh_placeholder.empty()
            st.rerun()

        st.markdown("---")

        # System Health Indicator
        health_status = alert_metrics["health_status"]
        if health_status == "healthy":
            st.success("System Health: HEALTHY")
        elif health_status == "warning":
            st.warning("System Health: WARNING")
        else:
            st.error("System Health: CRITICAL")

        # Alert Metrics Cards
        st.markdown("#### 🔔 Active Alerts")

        alert_col1, alert_col2 = st.columns(2)
        with alert_col1:
            st.metric("Total Active", alert_metrics["total_active"], delta=None)
        with alert_col2:
            st.metric("Models Monitored", alert_metrics["models_monitored"], delta=None)

        # Severity breakdown
        severity_counts = alert_metrics["severity_counts"]
        st.markdown("**Severity Breakdown:**")
        sev_col1, sev_col2 = st.columns(2)
        with sev_col1:
            st.markdown(f"🚨 Critical: **{severity_counts['critical']}**")
            st.markdown(f"🟡 Medium: **{severity_counts['medium']}**")
        with sev_col2:
            st.markdown(f"⚠️ High: **{severity_counts['high']}**")
            st.markdown(f"💡 Low: **{severity_counts['low']}**")

        st.caption(f"Last alert: {alert_metrics['last_alert_time']}")

        st.markdown("---")

        st.markdown("### 📅 Reporting Period")
        period = st.selectbox("Select Period", ["Last 30 Days", "Last 90 Days", "Last Year", "Custom"], index=1)

        st.markdown("### 🏛️ Regulations")
        eu_ai = st.checkbox("EU AI Act", value=True)
        hipaa = st.checkbox("HIPAA", value=True)
        sec = st.checkbox("SEC Guidance", value=True)
        gdpr = st.checkbox("GDPR", value=True)

        st.markdown("---")

        st.markdown("### 📤 Export Options")
        if st.button("📊 Generate Report", use_container_width=True):
            st.toast("Generating executive report...", icon="📊")

        if st.button("📑 Export Audit Package", use_container_width=True):
            st.toast("Preparing audit documentation...", icon="📑")

        if st.button("📧 Schedule Report", use_container_width=True):
            st.toast("Opening scheduler...", icon="📧")

        st.markdown("---")

        st.markdown("### ℹ️ Platform Info")
        st.caption("Version: 1.1.0")
        st.caption(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.caption("Built by Duke LLMOps-Certified Engineer")


if __name__ == "__main__":
    main()
