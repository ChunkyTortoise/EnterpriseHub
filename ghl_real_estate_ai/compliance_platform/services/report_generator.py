"""
Enterprise AI Compliance Platform - Report Generator

Production-grade compliance report generation for regulatory submissions,
executive summaries, and audit documentation.

Supports optional AI-powered narratives via ComplianceAIAnalyzer integration.
"""

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import uuid4

from ghl_real_estate_ai.ghl_utils.logger import get_logger

from ..models.compliance_models import (
    ComplianceReport,
    ComplianceScore,
    ComplianceStatus,
    PolicyViolation,
    RegulationType,
    RiskAssessment,
)

if TYPE_CHECKING:
    from .compliance_ai_analyzer import ComplianceAIAnalyzer

logger = get_logger(__name__)


class ComplianceReportGenerator:
    """
    Generate compliance reports for various stakeholders and purposes.

    Supports:
    - Executive summaries
    - Detailed compliance reports
    - Regulatory submission packages
    - Audit documentation
    - AI-powered narratives (optional)

    Attributes:
        compliance_service: ComplianceService instance for data access
        ai_analyzer: Optional ComplianceAIAnalyzer for AI-powered insights
        enable_ai_narratives: Whether to use AI for generating narratives
    """

    def __init__(
        self,
        compliance_service: Any,
        ai_analyzer: Optional["ComplianceAIAnalyzer"] = None,
        enable_ai_narratives: bool = False,
    ):
        """
        Initialize the Report Generator.

        Args:
            compliance_service: ComplianceService instance
            ai_analyzer: Optional ComplianceAIAnalyzer for AI-powered insights.
                        If provided and enable_ai_narratives=True, AI will be used
                        to generate executive summaries and strategic recommendations.
            enable_ai_narratives: Whether to use AI for generating narratives.
                                 Defaults to False for backwards compatibility.
        """
        self.compliance_service = compliance_service
        self.ai_analyzer = ai_analyzer
        self.enable_ai_narratives = enable_ai_narratives and ai_analyzer is not None

        if enable_ai_narratives and ai_analyzer is None:
            logger.warning("enable_ai_narratives=True but no ai_analyzer provided. AI narratives will be disabled.")

    async def generate_executive_summary(
        self,
        period_days: int = 30,
    ) -> ComplianceReport:
        """
        Generate executive summary report.

        Args:
            period_days: Reporting period in days

        Returns:
            Executive summary compliance report
        """
        period_start = datetime.now(timezone.utc) - timedelta(days=period_days)
        period_end = datetime.now(timezone.utc)

        # Get dashboard data
        dashboard_data = await self.compliance_service.generate_executive_dashboard_data()

        # Collect all assessments
        models = self.compliance_service.list_models()
        assessments = []
        violations = []

        for model in models:
            assessment = self.compliance_service.get_risk_assessment(model.model_id)
            if assessment:
                assessments.append(assessment)

            model_violations = self.compliance_service.policy_enforcer.get_active_violations(model_id=model.model_id)
            violations.extend(model_violations)

        # Calculate overall score
        scores = [self.compliance_service.get_compliance_score(m.model_id) for m in models]
        scores = [s for s in scores if s]

        if scores:
            overall_score = ComplianceScore(
                overall_score=sum(s.overall_score for s in scores) / len(scores),
                regulation_scores={},
                category_scores={},
            )
        else:
            overall_score = ComplianceScore(overall_score=0, regulation_scores={}, category_scores={})

        # Determine overall status
        if dashboard_data["summary"]["critical_violations"] > 0:
            overall_status = ComplianceStatus.NON_COMPLIANT
        elif dashboard_data["summary"]["total_violations"] > 5:
            overall_status = ComplianceStatus.PARTIALLY_COMPLIANT
        elif overall_score.overall_score >= 90:
            overall_status = ComplianceStatus.COMPLIANT
        else:
            overall_status = ComplianceStatus.PARTIALLY_COMPLIANT

        # Generate key findings
        key_findings = []
        if dashboard_data["summary"]["critical_violations"] > 0:
            key_findings.append(
                f"{dashboard_data['summary']['critical_violations']} critical violations require immediate attention"
            )
        if dashboard_data["risk_distribution"].get("high", 0) > 0:
            key_findings.append(f"{dashboard_data['risk_distribution']['high']} high-risk AI systems identified")
        if overall_score.overall_score < 80:
            key_findings.append(
                f"Overall compliance score of {overall_score.overall_score:.1f}% below target threshold"
            )
        if dashboard_data["summary"]["potential_exposure"] > 0:
            key_findings.append(
                f"Potential regulatory exposure of €{dashboard_data['summary']['potential_exposure']:,.0f}"
            )

        # Generate priority actions
        priority_actions = []
        if dashboard_data["summary"]["critical_violations"] > 0:
            priority_actions.append("Address critical compliance violations within 24 hours")
        if dashboard_data["risk_distribution"].get("high", 0) > 0:
            priority_actions.append("Complete risk mitigation for high-risk AI systems")
        priority_actions.append("Review and update compliance documentation")
        priority_actions.append("Schedule quarterly compliance training")

        # Prepare report data for AI analysis
        report_data = {
            "overall_score": {
                "overall_score": overall_score.overall_score,
                "grade": overall_score.grade,
                "trend": "stable",
                "trend_percentage": 0,
            },
            "violations_summary": {
                "critical": sum(1 for v in violations if v.severity.value == "critical"),
                "high": sum(1 for v in violations if v.severity.value == "high"),
                "medium": sum(1 for v in violations if v.severity.value == "medium"),
                "low": sum(1 for v in violations if v.severity.value == "low"),
            },
            "models_assessed": len(models),
            "period_start": period_start.strftime("%Y-%m-%d"),
            "period_end": period_end.strftime("%Y-%m-%d"),
            "key_findings": key_findings,
            "priority_actions": priority_actions,
            "risk_distribution": dashboard_data["risk_distribution"],
            "potential_exposure": dashboard_data["summary"]["potential_exposure"],
        }

        # Try AI-generated executive summary if enabled
        executive_summary = await self._generate_executive_summary_text(
            report_data=report_data,
            period_start=period_start,
            period_end=period_end,
            overall_score=overall_score,
            models=models,
            violations=violations,
            dashboard_data=dashboard_data,
            priority_actions=priority_actions,
        )

        return ComplianceReport(
            report_type="executive_summary",
            title=f"AI Compliance Executive Summary - {period_end.strftime('%B %Y')}",
            description="Monthly compliance overview for executive leadership",
            period_start=period_start,
            period_end=period_end,
            overall_score=overall_score,
            overall_status=overall_status,
            regulations_covered=list(set(a.applicable_regulations[0] for a in assessments if a.applicable_regulations)),
            models_assessed=len(models),
            violations_summary={
                "critical": sum(1 for v in violations if v.severity.value == "critical"),
                "high": sum(1 for v in violations if v.severity.value == "high"),
                "medium": sum(1 for v in violations if v.severity.value == "medium"),
                "low": sum(1 for v in violations if v.severity.value == "low"),
            },
            risk_assessments=assessments[:5],  # Top 5 for summary
            active_violations=[v for v in violations if v.severity.value in ["critical", "high"]][:10],
            executive_summary=executive_summary,
            key_findings=key_findings,
            priority_actions=priority_actions,
        )

    async def generate_regulatory_report(
        self,
        regulation: RegulationType,
        period_days: int = 90,
    ) -> ComplianceReport:
        """
        Generate report for specific regulation submission.

        Args:
            regulation: Regulation to report on
            period_days: Reporting period

        Returns:
            Regulatory compliance report
        """
        period_start = datetime.now(timezone.utc) - timedelta(days=period_days)
        period_end = datetime.now(timezone.utc)

        # Get models and filter by regulation
        models = self.compliance_service.list_models()
        relevant_models = []
        assessments = []
        violations = []

        for model in models:
            assessment = self.compliance_service.get_risk_assessment(model.model_id)
            if assessment and regulation in assessment.applicable_regulations:
                relevant_models.append(model)
                assessments.append(assessment)

                model_violations = self.compliance_service.policy_enforcer.get_active_violations(
                    model_id=model.model_id,
                    regulation=regulation,
                )
                violations.extend(model_violations)

        # Get audit records
        audit_report = await self.compliance_service.audit_tracker.generate_compliance_report(
            regulation=regulation,
            period_start=period_start,
            period_end=period_end,
        )

        # Calculate regulation-specific score
        reg_scores = []
        for model in relevant_models:
            score = self.compliance_service.get_compliance_score(model.model_id)
            if score and regulation.value in score.regulation_scores:
                reg_scores.append(score.regulation_scores[regulation.value])

        avg_score = sum(reg_scores) / len(reg_scores) if reg_scores else 0

        overall_score = ComplianceScore(
            overall_score=avg_score,
            regulation_scores={regulation.value: avg_score},
            category_scores={},
        )

        # Determine status
        critical_count = sum(1 for v in violations if v.severity.value == "critical")
        if critical_count > 0:
            overall_status = ComplianceStatus.NON_COMPLIANT
        elif len(violations) > 3:
            overall_status = ComplianceStatus.PARTIALLY_COMPLIANT
        elif avg_score >= 90:
            overall_status = ComplianceStatus.COMPLIANT
        else:
            overall_status = ComplianceStatus.PARTIALLY_COMPLIANT

        # Regulation-specific summary
        reg_name = regulation.value.replace("_", " ").upper()
        executive_summary = f"""
## {reg_name} Compliance Report

**Reporting Period**: {period_start.strftime("%Y-%m-%d")} to {period_end.strftime("%Y-%m-%d")}

### Scope
- **AI Systems Covered**: {len(relevant_models)}
- **Compliance Score**: {avg_score:.1f}%
- **Active Violations**: {len(violations)}

### Audit Summary
- Total Audit Events: {audit_report["summary"]["total_events"]}
- Risk Assessments Performed: {audit_report["summary"]["risk_assessments"]}
- AI Decisions Logged: {audit_report["summary"]["ai_decisions"]}
- Human Overrides: {audit_report["summary"]["human_overrides"]}

### Compliance Metrics
- Violation Resolution Rate: {audit_report["compliance_metrics"]["violation_resolution_rate"]}
- Human Oversight Active: {"Yes" if audit_report["compliance_metrics"]["human_oversight_active"] else "No"}
- Audit Trail Complete: {"Yes" if audit_report["compliance_metrics"]["audit_trail_complete"] else "No"}

### Systems Inventory
{self._format_model_list(relevant_models)}
        """.strip()

        return ComplianceReport(
            report_type="regulatory",
            title=f"{reg_name} Compliance Report - Q{(period_end.month - 1) // 3 + 1} {period_end.year}",
            description=f"Quarterly compliance report for {reg_name} requirements",
            period_start=period_start,
            period_end=period_end,
            overall_score=overall_score,
            overall_status=overall_status,
            regulations_covered=[regulation],
            models_assessed=len(relevant_models),
            violations_summary={
                "critical": sum(1 for v in violations if v.severity.value == "critical"),
                "high": sum(1 for v in violations if v.severity.value == "high"),
                "medium": sum(1 for v in violations if v.severity.value == "medium"),
                "low": sum(1 for v in violations if v.severity.value == "low"),
            },
            risk_assessments=assessments,
            active_violations=violations,
            executive_summary=executive_summary,
            key_findings=[
                f"{len(relevant_models)} AI systems subject to {reg_name}",
                f"Average compliance score: {avg_score:.1f}%",
                f"{len(violations)} active compliance gaps identified",
            ],
            priority_actions=[
                f"Address {critical_count} critical violations"
                if critical_count > 0
                else "Maintain compliance posture",
                "Complete quarterly compliance documentation update",
                "Conduct staff training on regulation requirements",
            ],
        )

    async def generate_audit_package(
        self,
        period_start: datetime,
        period_end: datetime,
        regulations: Optional[List[RegulationType]] = None,
    ) -> Dict[str, Any]:
        """
        Generate complete audit documentation package.

        Args:
            period_start: Audit period start
            period_end: Audit period end
            regulations: Specific regulations to include

        Returns:
            Complete audit package
        """
        # Export audit trail
        audit_export = await self.compliance_service.audit_tracker.export(
            start_time=period_start,
            end_time=period_end,
            format_type="json",
        )

        # Get all models and their documentation
        models = self.compliance_service.list_models()
        model_documentation = []

        for model in models:
            assessment = self.compliance_service.get_risk_assessment(model.model_id)
            score = self.compliance_service.get_compliance_score(model.model_id)
            history = await self.compliance_service.audit_tracker.get_entity_history(model.model_id)

            if regulations:
                if assessment and not any(r in assessment.applicable_regulations for r in regulations):
                    continue

            model_documentation.append(
                {
                    "model_id": model.model_id,
                    "model_name": model.name,
                    "version": model.version,
                    "registration": model.model_dump(),
                    "risk_assessment": assessment.model_dump() if assessment else None,
                    "compliance_score": score.model_dump() if score else None,
                    "audit_history": [h.model_dump() for h in history],
                }
            )

        # Get violations and remediations
        violations = self.compliance_service.policy_enforcer.get_active_violations()
        if regulations:
            violations = [v for v in violations if v.regulation in regulations]

        return {
            "package_id": str(uuid4()),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat(),
            },
            "regulations_covered": [r.value for r in (regulations or [])],
            "model_count": len(model_documentation),
            "violation_count": len(violations),
            "contents": {
                "models": model_documentation,
                "violations": [v.model_dump() for v in violations],
                "audit_trail": audit_export,
            },
            "integrity_hash": self._compute_package_hash(model_documentation, violations),
        }

    async def _generate_executive_summary_text(
        self,
        report_data: Dict[str, Any],
        period_start: datetime,
        period_end: datetime,
        overall_score: ComplianceScore,
        models: List[Any],
        violations: List[PolicyViolation],
        dashboard_data: Dict[str, Any],
        priority_actions: List[str],
    ) -> str:
        """
        Generate executive summary text, using AI if enabled.

        Attempts AI generation first if enabled, falls back to template
        if AI fails or is not enabled.

        Args:
            report_data: Structured report data for AI analysis
            period_start: Report period start
            period_end: Report period end
            overall_score: Calculated compliance score
            models: List of AI models assessed
            violations: List of active violations
            dashboard_data: Dashboard metrics data
            priority_actions: List of priority action items

        Returns:
            Executive summary text string
        """
        # Try AI-generated summary if enabled
        if self.enable_ai_narratives and self.ai_analyzer:
            try:
                logger.info("Generating AI-powered executive summary")
                ai_summary = await self.ai_analyzer.generate_executive_summary(report_data)
                if ai_summary and len(ai_summary) > 100:  # Basic validation
                    logger.info("Successfully generated AI executive summary")
                    return ai_summary
                else:
                    logger.warning("AI summary too short, falling back to template")
            except Exception as e:
                logger.error(f"AI executive summary generation failed: {e}. Using template.")

        # Fall back to template-based summary
        return f"""
## Compliance Status Overview

The organization's AI compliance posture for the period {period_start.strftime("%Y-%m-%d")} to {period_end.strftime("%Y-%m-%d")} shows:

- **Overall Compliance Score**: {overall_score.overall_score:.1f}% ({overall_score.grade})
- **AI Models Tracked**: {len(models)}
- **Active Violations**: {len(violations)}
- **Potential Regulatory Exposure**: €{dashboard_data["summary"]["potential_exposure"]:,.0f}

### Risk Distribution
- High Risk: {dashboard_data["risk_distribution"].get("high", 0)} systems
- Limited Risk: {dashboard_data["risk_distribution"].get("limited", 0)} systems
- Minimal Risk: {dashboard_data["risk_distribution"].get("minimal", 0)} systems

### Compliance by Regulation
{self._format_regulation_summary(dashboard_data["regulation_coverage"])}

### Immediate Actions Required
{self._format_actions(priority_actions)}
        """.strip()

    async def generate_ai_strategic_recommendations(
        self,
        report_data: Dict[str, Any],
    ) -> List[str]:
        """
        Generate AI-powered strategic recommendations based on compliance posture.

        Uses the ComplianceAIAnalyzer to generate contextual, actionable
        recommendations tailored to the organization's specific compliance situation.

        Args:
            report_data: Dict containing compliance report data including:
                - overall_score: Dict with overall_score, grade, trend
                - violations_summary: Dict of violations by severity
                - risk_distribution: Dict of risk levels
                - key_findings: List of key findings
                - models_assessed: Number of models assessed

        Returns:
            List of strategic recommendation strings.
            Returns empty list if AI is not enabled or fails.

        Example:
            >>> recommendations = await generator.generate_ai_strategic_recommendations({
            ...     "overall_score": {"overall_score": 72, "grade": "C"},
            ...     "violations_summary": {"critical": 2, "high": 5},
            ...     "models_assessed": 15,
            ... })
            >>> print(recommendations[0])
            "Establish a dedicated AI compliance task force to address critical violations..."
        """
        if not self.enable_ai_narratives or not self.ai_analyzer:
            logger.debug("AI narratives disabled, returning empty recommendations")
            return []

        try:
            logger.info("Generating AI strategic recommendations")

            # Build comprehensive prompt for strategic recommendations
            prompt = self._build_strategic_recommendations_prompt(report_data)

            # Use the AI analyzer's question answering capability for flexibility
            response = await self.ai_analyzer.answer_compliance_question(
                question=prompt,
                context={"report_data": report_data},
            )

            # Parse recommendations from response
            recommendations = self._parse_recommendations_from_response(response)

            if recommendations:
                logger.info(f"Generated {len(recommendations)} AI strategic recommendations")
                return recommendations
            else:
                logger.warning("No recommendations parsed from AI response")
                return []

        except Exception as e:
            logger.error(f"Failed to generate AI strategic recommendations: {e}")
            return []

    def _build_strategic_recommendations_prompt(self, report_data: Dict[str, Any]) -> str:
        """Build prompt for strategic recommendations generation."""
        score_data = report_data.get("overall_score", {})
        violations = report_data.get("violations_summary", {})
        risk_dist = report_data.get("risk_distribution", {})

        return f"""Based on the following compliance posture, provide 5-7 strategic recommendations
for executive leadership to improve the organization's AI compliance position:

COMPLIANCE OVERVIEW:
- Overall Score: {score_data.get("overall_score", "N/A")}/100 (Grade: {score_data.get("grade", "N/A")})
- Trend: {score_data.get("trend", "stable")} ({score_data.get("trend_percentage", 0):+.1f}%)
- Models Assessed: {report_data.get("models_assessed", 0)}

VIOLATIONS:
- Critical: {violations.get("critical", 0)}
- High: {violations.get("high", 0)}
- Medium: {violations.get("medium", 0)}
- Low: {violations.get("low", 0)}

RISK DISTRIBUTION:
- High Risk Systems: {risk_dist.get("high", 0)}
- Limited Risk: {risk_dist.get("limited", 0)}
- Minimal Risk: {risk_dist.get("minimal", 0)}

KEY FINDINGS:
{chr(10).join(f"- {f}" for f in report_data.get("key_findings", [])) or "- None specified"}

Provide strategic, actionable recommendations that:
1. Address the most critical compliance gaps
2. Consider resource allocation and prioritization
3. Include both immediate actions and long-term improvements
4. Are specific to the compliance posture described

Format as a numbered list (1. 2. 3. etc.)"""

    def _parse_recommendations_from_response(self, response: str) -> List[str]:
        """Parse recommendations from AI response text."""
        import re

        recommendations = []

        # Match numbered items (1. or 1) format)
        pattern = r"^\d+[\.\)]\s*(.+)$"
        for line in response.split("\n"):
            match = re.match(pattern, line.strip())
            if match:
                rec = match.group(1).strip()
                if len(rec) > 20:  # Filter out very short items
                    recommendations.append(rec)

        # If no numbered items found, try bullet points
        if not recommendations:
            for line in response.split("\n"):
                line = line.strip()
                if line.startswith(("- ", "* ", "+ ")):
                    rec = line[2:].strip()
                    if len(rec) > 20:
                        recommendations.append(rec)

        return recommendations[:7]  # Limit to 7 recommendations

    async def generate_detailed_report_with_ai_insights(
        self,
        regulation: RegulationType,
        period_days: int = 90,
    ) -> ComplianceReport:
        """
        Generate detailed regulatory report with optional AI insights.

        Extends the standard regulatory report with AI-generated insights
        when AI narratives are enabled.

        Args:
            regulation: Regulation to report on
            period_days: Reporting period in days

        Returns:
            ComplianceReport with optional ai_insights field in metadata
        """
        # Generate the base regulatory report
        report = await self.generate_regulatory_report(regulation, period_days)

        # Add AI insights if enabled
        if self.enable_ai_narratives and self.ai_analyzer:
            try:
                logger.info(f"Generating AI insights for {regulation.value} report")

                # Prepare report data for AI analysis
                report_data = {
                    "overall_score": {
                        "overall_score": report.overall_score.overall_score,
                        "grade": report.overall_score.grade,
                        "trend": "stable",
                        "trend_percentage": 0,
                    },
                    "violations_summary": report.violations_summary,
                    "models_assessed": report.models_assessed,
                    "key_findings": report.key_findings,
                    "priority_actions": report.priority_actions,
                    "regulation": regulation.value,
                }

                # Generate strategic recommendations
                ai_recommendations = await self.generate_ai_strategic_recommendations(report_data)

                # Generate AI risk narrative for active violations
                ai_risk_narrative = ""
                if report.active_violations:
                    try:
                        # Use first model for context if available
                        models = self.compliance_service.list_models()
                        if models:
                            roadmap = await self.ai_analyzer.generate_remediation_roadmap(
                                violations=report.active_violations[:5],  # Limit for performance
                                model=models[0],
                            )
                            ai_risk_narrative = f"Quick Wins: {', '.join(roadmap.get('quick_wins', [])[:3])}"
                    except Exception as e:
                        logger.warning(f"Failed to generate AI risk narrative: {e}")

                # Add AI insights to report metadata
                report.metadata = report.metadata or {}
                report.metadata["ai_insights"] = {
                    "strategic_recommendations": ai_recommendations,
                    "risk_narrative": ai_risk_narrative,
                    "ai_generated": True,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                }

                logger.info("Successfully added AI insights to report")

            except Exception as e:
                logger.error(f"Failed to add AI insights to report: {e}")
                # Report is still valid without AI insights

        return report

    def _format_regulation_summary(self, regulation_coverage: Dict[str, int]) -> str:
        """Format regulation coverage for report"""
        lines = []
        for reg, count in regulation_coverage.items():
            lines.append(f"- {reg.replace('_', ' ').upper()}: {count} systems")
        return "\n".join(lines) if lines else "- No regulations tracked"

    def _format_actions(self, actions: List[str]) -> str:
        """Format action items"""
        return "\n".join(f"{i + 1}. {action}" for i, action in enumerate(actions))

    def _format_model_list(self, models: List[Any]) -> str:
        """Format model list for report"""
        lines = []
        for model in models[:10]:
            lines.append(f"- {model.name} (v{model.version}): {model.use_case_category}")
        if len(models) > 10:
            lines.append(f"- ... and {len(models) - 10} more systems")
        return "\n".join(lines) if lines else "- No systems registered"

    def _compute_package_hash(self, models: List, violations: List) -> str:
        """Compute hash for audit package integrity"""
        import hashlib
        import json

        content = json.dumps(
            {
                "model_count": len(models),
                "violation_count": len(violations),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            sort_keys=True,
        )

        return hashlib.sha256(content.encode()).hexdigest()[:16]
