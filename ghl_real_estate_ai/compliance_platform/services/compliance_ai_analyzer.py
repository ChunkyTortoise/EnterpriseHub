"""
Enterprise AI Compliance Platform - AI-Powered Compliance Analyzer

Provides Claude-powered intelligent analysis for compliance assessments,
risk explanations, violation analysis, and remediation recommendations.

Supports EU AI Act, HIPAA, GDPR, SEC AI Guidance, and other regulatory frameworks.
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.core.llm_client import LLMClient, TaskComplexity
from ghl_real_estate_ai.ghl_utils.logger import get_logger

from ..models.compliance_models import (
    AIModelRegistration,
    ComplianceStatus,
    PolicyViolation,
    RegulationType,
    RiskAssessment,
    RiskLevel,
    ViolationSeverity,
)
from ..models.risk_models import RiskCategory, RiskIndicator

logger = get_logger(__name__)


# System prompts for compliance expertise
COMPLIANCE_EXPERT_SYSTEM_PROMPT = """You are a senior AI compliance expert with deep knowledge of:

REGULATORY FRAMEWORKS:
- EU AI Act (2024): Risk classification, documentation requirements, conformity assessment
- HIPAA: PHI protection, technical safeguards, breach notification
- GDPR: Data protection principles, lawful basis, subject rights, DPIAs
- SEC AI Guidance: Investment advisor fiduciary duties, disclosure requirements
- SOC 2: Trust service criteria, security controls
- NIST AI RMF: Risk management framework, MAP/MEASURE/MANAGE/GOVERN functions

EXPERTISE AREAS:
- Risk assessment methodology and scoring
- Policy violation analysis and remediation
- Compliance gap analysis and roadmap planning
- Executive-level compliance reporting
- Technical and procedural control recommendations

RESPONSE GUIDELINES:
- Be precise and actionable in recommendations
- Reference specific regulatory articles where applicable
- Prioritize by risk severity and business impact
- Use clear, professional language suitable for compliance reports
- Provide practical, implementable solutions"""


RISK_ANALYSIS_SYSTEM_PROMPT = f"""{COMPLIANCE_EXPERT_SYSTEM_PROMPT}

CURRENT TASK: Risk Dimension Analysis
Analyze the given risk dimension and scores to provide:
1. Clear explanation of the risk factors
2. Key concerns requiring attention
3. Specific mitigation strategies

Format your response as JSON with keys: explanation, key_concerns, mitigation_strategies"""


VIOLATION_ANALYSIS_SYSTEM_PROMPT = f"""{COMPLIANCE_EXPERT_SYSTEM_PROMPT}

CURRENT TASK: Violation Analysis
Analyze the compliance violation to provide:
1. Significance of the violation
2. Potential business impact
3. Remediation priority assessment
4. Concrete suggested actions

Format your response as JSON with keys: significance, business_impact, remediation_priority, suggested_actions"""


REMEDIATION_ROADMAP_SYSTEM_PROMPT = f"""{COMPLIANCE_EXPERT_SYSTEM_PROMPT}

CURRENT TASK: Remediation Roadmap Generation
Create a prioritized remediation roadmap including:
1. Prioritized actions (by urgency and impact)
2. Realistic timeline
3. Resource estimates
4. Quick wins for immediate progress

Format your response as JSON with keys: prioritized_actions, timeline, resource_estimates, quick_wins"""


class ComplianceAIAnalyzer:
    """
    AI-powered compliance analysis using Claude.

    Provides intelligent explanations, recommendations, and analysis
    for compliance assessments, risk dimensions, violations, and remediation planning.

    Features:
    - Risk dimension explanation with mitigation strategies
    - Violation analysis with business impact assessment
    - Remediation roadmap generation
    - Executive summary generation
    - Compliance Q&A with regulatory context
    - Response caching for performance optimization

    Attributes:
        llm_client: LLMClient instance for Claude API calls
        enable_caching: Whether to cache AI responses
        _cache: Dict-based response cache
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        enable_caching: bool = True,
    ):
        """
        Initialize the ComplianceAIAnalyzer.

        Args:
            llm_client: Optional LLMClient instance. If not provided,
                       creates a new Claude client.
            enable_caching: Whether to enable response caching.
                           Defaults to True for performance.
        """
        self.llm_client = llm_client or LLMClient(provider="claude")
        self.enable_caching = enable_caching
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 3600  # 1 hour default TTL

        logger.info(f"ComplianceAIAnalyzer initialized with caching={'enabled' if enable_caching else 'disabled'}")

    async def explain_risk_dimension(
        self,
        dimension: str,
        scores: Dict[str, float],
        model: AIModelRegistration,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate Claude explanation for a risk dimension.

        Analyzes a specific risk dimension (e.g., transparency, fairness)
        and provides actionable insights and mitigation strategies.

        Args:
            dimension: Risk dimension name (e.g., "transparency", "fairness")
            scores: Dict of score components for this dimension
            model: AIModelRegistration containing model details
            context: Optional additional context for analysis

        Returns:
            Dict containing:
                - explanation: str - Detailed explanation of the risk
                - key_concerns: List[str] - Primary concerns to address
                - mitigation_strategies: List[str] - Recommended mitigations

        Example:
            >>> result = await analyzer.explain_risk_dimension(
            ...     "transparency",
            ...     {"documentation": 45.0, "explainability": 60.0},
            ...     model_registration
            ... )
            >>> print(result["key_concerns"])
            ["Insufficient model documentation", "Limited explainability features"]
        """
        cache_key = self._get_cache_key("explain_risk_dimension", dimension, str(scores), model.model_id)

        prompt = self._build_risk_prompt(dimension, scores, model, context)

        try:
            response_text = await self._cached_generate(
                cache_key,
                prompt,
                RISK_ANALYSIS_SYSTEM_PROMPT,
                complexity=TaskComplexity.ROUTINE,
            )

            result = self._parse_json_response(response_text)

            # Ensure required keys exist
            return {
                "explanation": result.get("explanation", self._fallback_risk_explanation(dimension, scores)),
                "key_concerns": result.get("key_concerns", []),
                "mitigation_strategies": result.get("mitigation_strategies", []),
            }

        except Exception as e:
            logger.error(f"Error explaining risk dimension {dimension}: {e}")
            return self._fallback_risk_response(dimension, scores)

    async def generate_risk_recommendations(
        self,
        assessment: RiskAssessment,
        model: AIModelRegistration,
    ) -> List[str]:
        """
        Generate specific recommendations for risk mitigation.

        Analyzes a complete risk assessment and generates prioritized,
        actionable recommendations tailored to the model's specific risks.

        Args:
            assessment: RiskAssessment containing risk scores and factors
            model: AIModelRegistration with model details

        Returns:
            List of specific, actionable recommendation strings

        Example:
            >>> recommendations = await analyzer.generate_risk_recommendations(
            ...     risk_assessment,
            ...     model_registration
            ... )
            >>> print(recommendations[0])
            "Implement model explainability dashboard with SHAP values..."
        """
        cache_key = self._get_cache_key(
            "generate_risk_recommendations",
            assessment.assessment_id,
            model.model_id,
        )

        prompt = self._build_recommendations_prompt(assessment, model)

        try:
            response_text = await self._cached_generate(
                cache_key,
                prompt,
                COMPLIANCE_EXPERT_SYSTEM_PROMPT,
                complexity=TaskComplexity.COMPLEX,
            )

            # Parse recommendations from response
            recommendations = self._parse_recommendations(response_text)

            if not recommendations:
                recommendations = self._fallback_recommendations(assessment)

            return recommendations

        except Exception as e:
            logger.error(f"Error generating risk recommendations: {e}")
            return self._fallback_recommendations(assessment)

    async def explain_violation(
        self,
        violation: PolicyViolation,
        model: AIModelRegistration,
    ) -> Dict[str, Any]:
        """
        Generate detailed violation explanation.

        Provides comprehensive analysis of a compliance violation including
        significance, business impact, and prioritized remediation actions.

        Args:
            violation: PolicyViolation to analyze
            model: AIModelRegistration associated with the violation

        Returns:
            Dict containing:
                - significance: str - Why this violation matters
                - business_impact: str - Potential business consequences
                - remediation_priority: str - Priority level (critical/high/medium/low)
                - suggested_actions: List[str] - Concrete remediation steps

        Example:
            >>> result = await analyzer.explain_violation(violation, model)
            >>> print(result["remediation_priority"])
            "critical - immediate action required"
        """
        cache_key = self._get_cache_key(
            "explain_violation",
            violation.violation_id,
            model.model_id,
        )

        prompt = self._build_violation_prompt(violation, model)

        try:
            response_text = await self._cached_generate(
                cache_key,
                prompt,
                VIOLATION_ANALYSIS_SYSTEM_PROMPT,
                complexity=TaskComplexity.COMPLEX,
            )

            result = self._parse_json_response(response_text)

            return {
                "significance": result.get(
                    "significance", f"Violation of {violation.regulation.value} policy: {violation.title}"
                ),
                "business_impact": result.get("business_impact", self._estimate_business_impact(violation)),
                "remediation_priority": result.get("remediation_priority", violation.severity.value),
                "suggested_actions": result.get("suggested_actions", self._fallback_violation_actions(violation)),
            }

        except Exception as e:
            logger.error(f"Error explaining violation {violation.violation_id}: {e}")
            return self._fallback_violation_response(violation)

    async def generate_remediation_roadmap(
        self,
        violations: List[PolicyViolation],
        model: AIModelRegistration,
    ) -> Dict[str, Any]:
        """
        Generate prioritized remediation roadmap.

        Creates a comprehensive remediation plan for multiple violations,
        prioritizing by severity and identifying quick wins.

        Args:
            violations: List of PolicyViolation instances to remediate
            model: AIModelRegistration context

        Returns:
            Dict containing:
                - prioritized_actions: List of prioritized remediation actions
                - timeline: str - Suggested timeline for remediation
                - resource_estimates: Dict - Estimated resources needed
                - quick_wins: List[str] - Actions for immediate progress

        Example:
            >>> roadmap = await analyzer.generate_remediation_roadmap(
            ...     violations,
            ...     model
            ... )
            >>> print(roadmap["quick_wins"])
            ["Update privacy policy", "Enable audit logging"]
        """
        if not violations:
            return {
                "prioritized_actions": [],
                "timeline": "No remediation needed",
                "resource_estimates": {},
                "quick_wins": [],
            }

        cache_key = self._get_cache_key(
            "generate_remediation_roadmap",
            ",".join(v.violation_id for v in violations[:5]),  # Limit for cache key
            model.model_id,
        )

        prompt = self._build_roadmap_prompt(violations, model)

        try:
            response_text = await self._cached_generate(
                cache_key,
                prompt,
                REMEDIATION_ROADMAP_SYSTEM_PROMPT,
                complexity=TaskComplexity.COMPLEX,
            )

            result = self._parse_json_response(response_text)

            return {
                "prioritized_actions": result.get(
                    "prioritized_actions", self._fallback_prioritized_actions(violations)
                ),
                "timeline": result.get("timeline", self._estimate_timeline(violations)),
                "resource_estimates": result.get("resource_estimates", self._estimate_resources(violations)),
                "quick_wins": result.get("quick_wins", self._identify_quick_wins(violations)),
            }

        except Exception as e:
            logger.error(f"Error generating remediation roadmap: {e}")
            return self._fallback_roadmap_response(violations)

    async def generate_executive_summary(
        self,
        report_data: Dict[str, Any],
    ) -> str:
        """
        Generate narrative executive summary for C-suite.

        Creates a concise, business-focused summary suitable for
        executive leadership and board reporting.

        Args:
            report_data: Dict containing compliance report data including:
                - overall_score: Compliance score
                - violations_summary: Dict of violations by severity
                - risk_assessments: List of risk assessments
                - key_findings: List of key findings

        Returns:
            Formatted executive summary string

        Example:
            >>> summary = await analyzer.generate_executive_summary(report_data)
            >>> print(summary[:100])
            "Executive Compliance Summary - Q1 2024\n\nOverall Position: Strong..."
        """
        cache_key = self._get_cache_key(
            "generate_executive_summary",
            str(report_data.get("overall_score", {}).get("overall_score", 0)),
            str(len(report_data.get("violations_summary", {}))),
        )

        prompt = self._build_executive_summary_prompt(report_data)

        try:
            summary = await self._cached_generate(
                cache_key,
                prompt,
                COMPLIANCE_EXPERT_SYSTEM_PROMPT,
                complexity=TaskComplexity.COMPLEX,
            )

            return summary.strip()

        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return self._fallback_executive_summary(report_data)

    async def answer_compliance_question(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Answer compliance questions with model context.

        Provides expert answers to compliance-related questions,
        incorporating any provided model or regulatory context.

        Args:
            question: User's compliance question
            context: Optional context including:
                - model: AIModelRegistration
                - regulation: RegulationType
                - risk_assessment: RiskAssessment

        Returns:
            Expert answer string

        Example:
            >>> answer = await analyzer.answer_compliance_question(
            ...     "What documentation is required for high-risk AI under EU AI Act?",
            ...     {"regulation": RegulationType.EU_AI_ACT}
            ... )
        """
        context = context or {}

        # Build context-aware prompt
        prompt_parts = [f"Question: {question}"]

        if "model" in context:
            model = context["model"]
            prompt_parts.append(f"\nModel Context: {model.name} ({model.model_type})")
            prompt_parts.append(f"Risk Level: {model.risk_level.value}")
            prompt_parts.append(f"Use Case: {model.use_case_category}")

        if "regulation" in context:
            prompt_parts.append(f"\nPrimary Regulation: {context['regulation'].value}")

        if "risk_assessment" in context:
            assessment = context["risk_assessment"]
            prompt_parts.append(f"\nRisk Score: {assessment.risk_score}/100")

        prompt_parts.append("\nProvide a clear, actionable answer.")
        prompt = "\n".join(prompt_parts)

        try:
            # Don't cache Q&A as questions are highly variable
            response = await self.llm_client.agenerate(
                prompt=prompt,
                system_prompt=COMPLIANCE_EXPERT_SYSTEM_PROMPT,
                max_tokens=1024,
                temperature=0.3,
                complexity=TaskComplexity.ROUTINE,
            )

            return response.content.strip()

        except Exception as e:
            logger.error(f"Error answering compliance question: {e}")
            return (
                "I apologize, but I was unable to process your question at this time. "
                "Please consult your compliance officer or legal team for guidance."
            )

    # ========================================================================
    # Prompt Building Methods
    # ========================================================================

    def _build_risk_prompt(
        self,
        dimension: str,
        scores: Dict[str, float],
        model: AIModelRegistration,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build prompt for risk dimension analysis."""
        context = context or {}

        return f"""Analyze the following risk dimension for compliance assessment:

RISK DIMENSION: {dimension}

SCORE BREAKDOWN:
{json.dumps(scores, indent=2)}

MODEL DETAILS:
- Name: {model.name}
- Type: {model.model_type}
- Risk Level: {model.risk_level.value}
- Use Case: {model.use_case_category}
- Provider: {model.provider}
- Personal Data: {"Yes" if model.personal_data_processed else "No"}
- Sensitive Data: {"Yes" if model.sensitive_data_processed else "No"}

APPLICABLE REGULATIONS: {", ".join(r.value for r in model.applicable_regulations) or "Under review"}

ADDITIONAL CONTEXT: {json.dumps(context) if context else "None provided"}

Provide analysis as JSON with keys: explanation, key_concerns, mitigation_strategies"""

    def _build_violation_prompt(
        self,
        violation: PolicyViolation,
        model: AIModelRegistration,
    ) -> str:
        """Build prompt for violation explanation."""
        return f"""Analyze the following compliance violation:

VIOLATION DETAILS:
- ID: {violation.violation_id}
- Title: {violation.title}
- Regulation: {violation.regulation.value}
- Policy: {violation.policy_name}
- Article Reference: {violation.article_reference or "N/A"}
- Severity: {violation.severity.value}
- Description: {violation.description}

EVIDENCE:
{chr(10).join(f"- {e}" for e in violation.evidence) if violation.evidence else "- None documented"}

AFFECTED SYSTEMS: {", ".join(violation.affected_systems) or "Not specified"}
AFFECTED DATA SUBJECTS: {violation.affected_data_subjects}

POTENTIAL FINE: {violation.potential_fine_currency} {violation.potential_fine:,.2f} if violation.potential_fine else "Not estimated"
REPUTATIONAL RISK: {violation.reputational_risk}

MODEL CONTEXT:
- Model: {model.name} (v{model.version})
- Risk Level: {model.risk_level.value}
- Compliance Status: {model.compliance_status.value}

Provide analysis as JSON with keys: significance, business_impact, remediation_priority, suggested_actions"""

    def _build_roadmap_prompt(
        self,
        violations: List[PolicyViolation],
        model: AIModelRegistration,
    ) -> str:
        """Build prompt for remediation roadmap generation."""
        violations_summary = []
        for v in violations[:10]:  # Limit to top 10 for token efficiency
            violations_summary.append(
                {
                    "title": v.title,
                    "regulation": v.regulation.value,
                    "severity": v.severity.value,
                    "days_open": v.days_open,
                    "is_overdue": v.is_overdue,
                }
            )

        severity_counts = {}
        for v in violations:
            sev = v.severity.value
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        return f"""Create a remediation roadmap for the following compliance violations:

TOTAL VIOLATIONS: {len(violations)}

SEVERITY BREAKDOWN:
{json.dumps(severity_counts, indent=2)}

TOP VIOLATIONS (by severity):
{json.dumps(violations_summary, indent=2)}

MODEL CONTEXT:
- Model: {model.name}
- Current Compliance Status: {model.compliance_status.value}
- Risk Level: {model.risk_level.value}

APPLICABLE REGULATIONS: {", ".join(r.value for r in model.applicable_regulations) or "Multiple"}

Generate a prioritized remediation roadmap as JSON with keys:
- prioritized_actions: List of action objects with title, priority (1-5), category, estimated_hours
- timeline: Overall timeline recommendation
- resource_estimates: Dict with team, hours, and cost estimates
- quick_wins: List of actions achievable in <1 day"""

    def _build_recommendations_prompt(
        self,
        assessment: RiskAssessment,
        model: AIModelRegistration,
    ) -> str:
        """Build prompt for risk recommendations."""
        return f"""Generate specific risk mitigation recommendations:

RISK ASSESSMENT:
- Overall Risk Score: {assessment.risk_score}/100
- Risk Level: {assessment.risk_level.value}

DIMENSION SCORES:
- Transparency: {assessment.transparency_score}/100
- Fairness: {assessment.fairness_score}/100
- Accountability: {assessment.accountability_score}/100
- Robustness: {assessment.robustness_score}/100
- Privacy: {assessment.privacy_score}/100
- Security: {assessment.security_score}/100

IDENTIFIED RISK FACTORS:
{chr(10).join(f"- {f}" for f in assessment.risk_factors) if assessment.risk_factors else "- None identified"}

MITIGATING FACTORS:
{chr(10).join(f"- {f}" for f in assessment.mitigating_factors) if assessment.mitigating_factors else "- None identified"}

MODEL: {model.name} ({model.model_type})
USE CASE: {model.use_case_category}
REGULATIONS: {", ".join(r.value for r in assessment.applicable_regulations)}

Provide 5-7 specific, actionable recommendations prioritized by impact.
Format as a numbered list."""

    def _build_executive_summary_prompt(self, report_data: Dict[str, Any]) -> str:
        """Build prompt for executive summary generation."""
        score = report_data.get("overall_score", {})
        violations = report_data.get("violations_summary", {})

        return f"""Generate an executive summary for the compliance report:

COMPLIANCE SCORE: {score.get("overall_score", "N/A")}/100
GRADE: {score.get("grade", "N/A")}
TREND: {score.get("trend", "stable")} ({score.get("trend_percentage", 0):+.1f}%)

VIOLATIONS BY SEVERITY:
- Critical: {violations.get("critical", 0)}
- High: {violations.get("high", 0)}
- Medium: {violations.get("medium", 0)}
- Low: {violations.get("low", 0)}

MODELS ASSESSED: {report_data.get("models_assessed", 0)}
PERIOD: {report_data.get("period_start", "N/A")} to {report_data.get("period_end", "N/A")}

KEY FINDINGS:
{chr(10).join(f"- {f}" for f in report_data.get("key_findings", [])) or "- None specified"}

PRIORITY ACTIONS:
{chr(10).join(f"- {a}" for a in report_data.get("priority_actions", [])) or "- None specified"}

Write a concise executive summary (3-4 paragraphs) suitable for C-suite and board presentation.
Focus on: overall compliance posture, key risks, regulatory exposure, and recommended priorities."""

    # ========================================================================
    # Cache Management Methods
    # ========================================================================

    def _get_cache_key(self, method: str, *args) -> str:
        """
        Generate cache key for response caching.

        Creates a deterministic hash from method name and arguments.

        Args:
            method: Method name being cached
            *args: Arguments to include in cache key

        Returns:
            MD5 hash string as cache key
        """
        key_parts = [method] + [str(arg) for arg in args]
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    async def _cached_generate(
        self,
        cache_key: str,
        prompt: str,
        system_prompt: str,
        complexity: TaskComplexity = TaskComplexity.ROUTINE,
    ) -> str:
        """
        Generate with caching support.

        Checks cache first, generates if not found, and caches result.

        Args:
            cache_key: Cache key for lookup/storage
            prompt: User prompt for LLM
            system_prompt: System prompt for LLM
            complexity: Task complexity for model routing

        Returns:
            Generated response content
        """
        # Check cache first
        if self.enable_caching and cache_key in self._cache:
            cached = self._cache[cache_key]
            cache_time = cached.get("timestamp", 0)
            if (datetime.now(timezone.utc).timestamp() - cache_time) < self._cache_ttl:
                logger.debug(f"Cache hit for key: {cache_key[:16]}...")
                return cached["content"]

        # Generate new response
        response = await self.llm_client.agenerate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=2048,
            temperature=0.2,  # Lower temperature for consistent compliance responses
            complexity=complexity,
        )

        content = response.content

        # Cache the response
        if self.enable_caching:
            self._cache[cache_key] = {
                "content": content,
                "timestamp": datetime.now(timezone.utc).timestamp(),
            }

            # Limit cache size
            if len(self._cache) > 100:
                # Remove oldest entries
                sorted_keys = sorted(
                    self._cache.keys(),
                    key=lambda k: self._cache[k].get("timestamp", 0),
                )
                for key in sorted_keys[:20]:
                    del self._cache[key]

        return content

    def clear_cache(self) -> int:
        """
        Clear the response cache.

        Returns:
            Number of entries cleared
        """
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {count} cached responses")
        return count

    # ========================================================================
    # Response Parsing Methods
    # ========================================================================

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response.

        Handles various response formats including JSON blocks and raw JSON.

        Args:
            response_text: Raw response from LLM

        Returns:
            Parsed dict, or empty dict if parsing fails
        """
        try:
            # Try direct JSON parse
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find raw JSON object
        json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        logger.warning(f"Failed to parse JSON from response: {response_text[:200]}...")
        return {}

    def _parse_recommendations(self, response_text: str) -> List[str]:
        """Parse recommendations from numbered list response."""
        recommendations = []

        # Match numbered items
        pattern = r"^\d+[\.\)]\s*(.+)$"
        for line in response_text.split("\n"):
            match = re.match(pattern, line.strip())
            if match:
                recommendations.append(match.group(1).strip())

        # If no numbered items, try bullet points
        if not recommendations:
            for line in response_text.split("\n"):
                line = line.strip()
                if line.startswith(("- ", "* ", "+ ")):
                    recommendations.append(line[2:].strip())

        return recommendations

    # ========================================================================
    # Fallback Response Methods
    # ========================================================================

    def _fallback_risk_explanation(self, dimension: str, scores: Dict[str, float]) -> str:
        """Generate fallback risk explanation."""
        avg_score = sum(scores.values()) / len(scores) if scores else 0
        status = "concerning" if avg_score < 50 else "acceptable" if avg_score < 75 else "strong"

        return (
            f"The {dimension} dimension shows {status} performance with an average score of "
            f"{avg_score:.1f}/100. Key components evaluated include: {', '.join(scores.keys())}. "
            f"Please review the detailed scores for specific areas requiring attention."
        )

    def _fallback_risk_response(self, dimension: str, scores: Dict[str, float]) -> Dict[str, Any]:
        """Generate complete fallback risk response."""
        return {
            "explanation": self._fallback_risk_explanation(dimension, scores),
            "key_concerns": [f"Low score in {k} ({v:.1f}/100)" for k, v in scores.items() if v < 60]
            or ["No critical concerns identified"],
            "mitigation_strategies": [
                f"Review and improve {dimension} practices",
                "Implement monitoring for continuous assessment",
                "Document compliance measures for audit readiness",
            ],
        }

    def _fallback_recommendations(self, assessment: RiskAssessment) -> List[str]:
        """Generate fallback recommendations based on low scores."""
        recommendations = []

        score_map = {
            "transparency": assessment.transparency_score,
            "fairness": assessment.fairness_score,
            "accountability": assessment.accountability_score,
            "robustness": assessment.robustness_score,
            "privacy": assessment.privacy_score,
            "security": assessment.security_score,
        }

        for dimension, score in sorted(score_map.items(), key=lambda x: x[1]):
            if score < 60:
                recommendations.append(f"Priority: Improve {dimension} controls (current score: {score:.1f}/100)")
            if len(recommendations) >= 5:
                break

        if not recommendations:
            recommendations = [
                "Maintain current compliance posture",
                "Schedule regular compliance reviews",
                "Document all AI model changes and decisions",
            ]

        return recommendations

    def _fallback_violation_actions(self, violation: PolicyViolation) -> List[str]:
        """Generate fallback violation actions."""
        actions = []

        if violation.severity in [ViolationSeverity.CRITICAL, ViolationSeverity.HIGH]:
            actions.append("Immediate: Escalate to compliance team lead")
            actions.append("Within 24 hours: Document incident details and evidence")

        actions.extend(
            [
                f"Review {violation.policy_name} requirements",
                "Implement corrective controls",
                "Update documentation and procedures",
                "Schedule follow-up compliance verification",
            ]
        )

        return actions[:5]

    def _fallback_violation_response(self, violation: PolicyViolation) -> Dict[str, Any]:
        """Generate complete fallback violation response."""
        return {
            "significance": f"Violation of {violation.regulation.value}: {violation.title}",
            "business_impact": self._estimate_business_impact(violation),
            "remediation_priority": violation.severity.value,
            "suggested_actions": self._fallback_violation_actions(violation),
        }

    def _estimate_business_impact(self, violation: PolicyViolation) -> str:
        """Estimate business impact based on violation details."""
        impacts = []

        if violation.potential_fine:
            impacts.append(
                f"Potential financial exposure: {violation.potential_fine_currency} {violation.potential_fine:,.0f}"
            )

        if violation.affected_data_subjects > 0:
            impacts.append(f"{violation.affected_data_subjects:,} data subjects affected")

        if violation.reputational_risk in ["high", "critical"]:
            impacts.append(f"Significant reputational risk ({violation.reputational_risk})")

        if violation.is_overdue:
            impacts.append(f"Violation overdue by {violation.days_open} days - urgent attention needed")

        return "; ".join(impacts) if impacts else "Impact assessment pending"

    def _fallback_roadmap_response(self, violations: List[PolicyViolation]) -> Dict[str, Any]:
        """Generate fallback roadmap response."""
        return {
            "prioritized_actions": self._fallback_prioritized_actions(violations),
            "timeline": self._estimate_timeline(violations),
            "resource_estimates": self._estimate_resources(violations),
            "quick_wins": self._identify_quick_wins(violations),
        }

    def _fallback_prioritized_actions(self, violations: List[PolicyViolation]) -> List[Dict[str, Any]]:
        """Generate prioritized action list from violations."""
        actions = []

        # Sort by severity
        severity_order = {
            ViolationSeverity.CRITICAL: 0,
            ViolationSeverity.HIGH: 1,
            ViolationSeverity.MEDIUM: 2,
            ViolationSeverity.LOW: 3,
            ViolationSeverity.INFORMATIONAL: 4,
        }

        sorted_violations = sorted(violations, key=lambda v: (severity_order.get(v.severity, 5), -v.days_open))

        for i, v in enumerate(sorted_violations[:10], 1):
            actions.append(
                {
                    "title": f"Remediate: {v.title}",
                    "priority": min(i, 5),
                    "category": v.regulation.value,
                    "estimated_hours": self._estimate_violation_hours(v),
                }
            )

        return actions

    def _estimate_violation_hours(self, violation: PolicyViolation) -> int:
        """Estimate hours to remediate a violation."""
        base_hours = {
            ViolationSeverity.CRITICAL: 40,
            ViolationSeverity.HIGH: 24,
            ViolationSeverity.MEDIUM: 16,
            ViolationSeverity.LOW: 8,
            ViolationSeverity.INFORMATIONAL: 2,
        }
        return base_hours.get(violation.severity, 16)

    def _estimate_timeline(self, violations: List[PolicyViolation]) -> str:
        """Estimate overall remediation timeline."""
        if not violations:
            return "No remediation required"

        critical_count = sum(1 for v in violations if v.severity == ViolationSeverity.CRITICAL)
        high_count = sum(1 for v in violations if v.severity == ViolationSeverity.HIGH)

        if critical_count > 0:
            return f"Urgent: Critical items within 1 week, full remediation 4-6 weeks"
        elif high_count > 3:
            return f"Priority: High-priority items within 2 weeks, full remediation 6-8 weeks"
        elif len(violations) > 10:
            return f"Standard: Phased approach over 8-12 weeks"
        else:
            return f"Manageable: Complete remediation within 4 weeks"

    def _estimate_resources(self, violations: List[PolicyViolation]) -> Dict[str, Any]:
        """Estimate resources needed for remediation."""
        total_hours = sum(self._estimate_violation_hours(v) for v in violations)

        return {
            "estimated_hours": total_hours,
            "fte_weeks": round(total_hours / 40, 1),
            "team_recommendation": self._recommend_team_size(total_hours),
            "estimated_cost_range": f"${total_hours * 100:,.0f} - ${total_hours * 200:,.0f}",
        }

    def _recommend_team_size(self, total_hours: int) -> str:
        """Recommend team size based on hours."""
        if total_hours > 400:
            return "Dedicated compliance team (3-5 FTEs)"
        elif total_hours > 200:
            return "Small team (2-3 FTEs)"
        elif total_hours > 80:
            return "1-2 dedicated resources"
        else:
            return "Part-time resource allocation"

    def _identify_quick_wins(self, violations: List[PolicyViolation]) -> List[str]:
        """Identify quick win actions from violations."""
        quick_wins = []

        for v in violations:
            if v.severity == ViolationSeverity.INFORMATIONAL:
                quick_wins.append(f"Document: {v.title}")
            elif v.severity == ViolationSeverity.LOW and "documentation" in v.title.lower():
                quick_wins.append(f"Update documentation: {v.policy_name}")
            elif "policy" in v.title.lower() and v.severity != ViolationSeverity.CRITICAL:
                quick_wins.append(f"Review and update: {v.policy_name}")

        # Add standard quick wins if list is short
        if len(quick_wins) < 3:
            quick_wins.extend(
                [
                    "Enable comprehensive audit logging",
                    "Update privacy policy with AI disclosures",
                    "Implement automated compliance monitoring",
                ]
            )

        return quick_wins[:5]

    def _fallback_executive_summary(self, report_data: Dict[str, Any]) -> str:
        """Generate fallback executive summary."""
        score = report_data.get("overall_score", {})
        overall = score.get("overall_score", 0)
        grade = score.get("grade", "N/A")

        violations = report_data.get("violations_summary", {})
        critical = violations.get("critical", 0)
        high = violations.get("high", 0)

        status = "strong" if overall >= 80 else "acceptable" if overall >= 60 else "concerning"

        summary = f"""EXECUTIVE COMPLIANCE SUMMARY

Overall Compliance Position: {status.upper()} (Score: {overall}/100, Grade: {grade})

The organization's AI compliance posture is currently {status}. """

        if critical > 0:
            summary += f"URGENT ATTENTION REQUIRED: {critical} critical violation(s) detected requiring immediate remediation. "

        if high > 0:
            summary += f"Additionally, {high} high-priority issue(s) should be addressed within the next 72 hours. "

        summary += """

Key priorities for the executive team:
1. Review and approve the remediation roadmap
2. Allocate resources for compliance improvement
3. Schedule quarterly compliance review with the board

This summary was generated automatically. Please consult the detailed report for comprehensive findings."""

        return summary
