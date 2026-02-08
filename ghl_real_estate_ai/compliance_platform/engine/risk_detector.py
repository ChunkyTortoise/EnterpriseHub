"""
Enterprise AI Compliance Platform - Risk Detector

Production-grade real-time AI risk scoring engine with multi-dimensional
analysis aligned to EU AI Act, SEC, and HIPAA requirements.
"""

import asyncio
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
from uuid import uuid4

from ..models.compliance_models import (
    AIModelRegistration,
    ComplianceStatus,
    RegulationType,
    RiskAssessment,
    RiskLevel,
    ViolationSeverity,
)
from ..models.risk_models import (
    RiskCategory,
    RiskIndicator,
    RiskMatrix,
    RiskTrend,
)

if TYPE_CHECKING:
    from ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer import ComplianceAIAnalyzer


class RiskDetector:
    """
    AI-powered risk detection engine for compliance management.

    Performs multi-dimensional risk analysis across:
    - Transparency & Explainability
    - Fairness & Bias
    - Accountability & Governance
    - Robustness & Reliability
    - Privacy & Data Protection
    - Security Controls
    """

    # EU AI Act risk classification criteria
    EU_AI_ACT_HIGH_RISK_DOMAINS = {
        "biometric_identification",
        "critical_infrastructure",
        "education_training",
        "employment_worker_management",
        "essential_services",
        "law_enforcement",
        "migration_asylum",
        "justice_democratic_processes",
    }

    EU_AI_ACT_UNACCEPTABLE_USES = {
        "social_scoring",
        "subliminal_manipulation",
        "exploitation_vulnerabilities",
        "real_time_biometric_public_spaces",
        "emotion_recognition_workplace",
    }

    # Risk scoring weights
    RISK_WEIGHTS = {
        "transparency": 0.20,
        "fairness": 0.20,
        "accountability": 0.15,
        "robustness": 0.15,
        "privacy": 0.15,
        "security": 0.15,
    }

    def __init__(
        self,
        enable_ai_analysis: bool = True,
        risk_tolerance: float = 30.0,
        auto_classify: bool = True,
        ai_analyzer: Optional["ComplianceAIAnalyzer"] = None,
        enable_ai_explanations: bool = False,
    ):
        """
        Initialize the Risk Detector.

        Args:
            enable_ai_analysis: Enable Claude-powered deep analysis
            risk_tolerance: Organization's risk tolerance threshold
            auto_classify: Automatically classify risk levels
            ai_analyzer: Optional ComplianceAIAnalyzer for AI-generated explanations
            enable_ai_explanations: Whether to include AI-generated explanations in assessments
        """
        self.enable_ai_analysis = enable_ai_analysis
        self.risk_tolerance = risk_tolerance
        self.auto_classify = auto_classify
        self._ai_analyzer = ai_analyzer
        self.enable_ai_explanations = enable_ai_explanations

        # Initialize risk matrix
        self.risk_matrix = self._create_default_risk_matrix()

        # Risk history for trend analysis
        self._risk_history: Dict[str, RiskTrend] = {}

        # Cache for assessments
        self._assessment_cache: Dict[str, RiskAssessment] = {}

    def _create_default_risk_matrix(self) -> RiskMatrix:
        """Create default EU AI Act aligned risk matrix"""
        return RiskMatrix(
            name="EU AI Act Risk Matrix",
            description="Risk assessment matrix aligned with EU AI Act requirements",
            likelihood_levels=["rare", "unlikely", "possible", "likely", "almost_certain"],
            impact_levels=["negligible", "minor", "moderate", "major", "catastrophic"],
            risk_level_definitions={
                "unacceptable": {"min_score": 20, "color": "#7C3AED", "action": "prohibited"},
                "high": {"min_score": 15, "color": "#EF4444", "action": "immediate"},
                "limited": {"min_score": 8, "color": "#F59E0B", "action": "transparency"},
                "minimal": {"min_score": 0, "color": "#10B981", "action": "monitor"},
            },
        )

    async def assess_model(
        self,
        model: AIModelRegistration,
        context: Optional[Dict[str, Any]] = None,
    ) -> RiskAssessment:
        """
        Perform comprehensive risk assessment on an AI model.

        Args:
            model: AI model registration to assess
            context: Additional context for assessment

        Returns:
            Complete risk assessment with scores and recommendations
        """
        context = context or {}

        # Run all risk dimension assessments in parallel
        transparency_task = self._assess_transparency(model, context)
        fairness_task = self._assess_fairness(model, context)
        accountability_task = self._assess_accountability(model, context)
        robustness_task = self._assess_robustness(model, context)
        privacy_task = self._assess_privacy(model, context)
        security_task = self._assess_security(model, context)

        (
            transparency_result,
            fairness_result,
            accountability_result,
            robustness_result,
            privacy_result,
            security_result,
        ) = await asyncio.gather(
            transparency_task,
            fairness_task,
            accountability_task,
            robustness_task,
            privacy_task,
            security_task,
        )

        # Calculate overall risk score
        overall_score = self._calculate_overall_risk_score(
            {
                "transparency": transparency_result["score"],
                "fairness": fairness_result["score"],
                "accountability": accountability_result["score"],
                "robustness": robustness_result["score"],
                "privacy": privacy_result["score"],
                "security": security_result["score"],
            }
        )

        # Determine risk level
        risk_level = self._classify_risk_level(model, overall_score)

        # Collect all risk factors and recommendations
        risk_factors = []
        mitigating_factors = []
        recommendations = []

        for result in [
            transparency_result,
            fairness_result,
            accountability_result,
            robustness_result,
            privacy_result,
            security_result,
        ]:
            risk_factors.extend(result.get("risk_factors", []))
            mitigating_factors.extend(result.get("mitigating_factors", []))
            recommendations.extend(result.get("recommendations", []))

        # Determine applicable regulations
        applicable_regulations = self._determine_applicable_regulations(model)

        # Build regulatory requirements
        regulatory_requirements = {}
        for reg in applicable_regulations:
            regulatory_requirements[reg.value] = self._get_regulatory_requirements(reg, model)

        assessment = RiskAssessment(
            model_id=model.model_id,
            model_name=model.name,
            risk_level=risk_level,
            risk_score=overall_score,
            transparency_score=100 - transparency_result["score"],  # Convert to positive scale
            fairness_score=100 - fairness_result["score"],
            accountability_score=100 - accountability_result["score"],
            robustness_score=100 - robustness_result["score"],
            privacy_score=100 - privacy_result["score"],
            security_score=100 - security_result["score"],
            risk_factors=risk_factors[:10],  # Top 10
            mitigating_factors=mitigating_factors[:5],
            recommendations=self._prioritize_recommendations(recommendations)[:10],
            applicable_regulations=applicable_regulations,
            regulatory_requirements=regulatory_requirements,
        )

        # Optionally add AI-generated explanations
        if self.enable_ai_explanations and self._ai_analyzer is not None:
            ai_insights = await self._generate_ai_insights(
                model,
                assessment,
                {
                    "transparency": transparency_result,
                    "fairness": fairness_result,
                    "accountability": accountability_result,
                    "robustness": robustness_result,
                    "privacy": privacy_result,
                    "security": security_result,
                },
            )
            assessment.ai_insights = ai_insights

        # Cache the assessment
        self._assessment_cache[model.model_id] = assessment

        # Update trend history
        await self._update_risk_trend(model.model_id, model.name, overall_score)

        return assessment

    async def _assess_transparency(
        self,
        model: AIModelRegistration,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Assess transparency and explainability risks"""
        score = 0.0
        risk_factors = []
        mitigating_factors = []
        recommendations = []

        # Check for documentation
        if not model.description or len(model.description) < 50:
            score += 20
            risk_factors.append("Insufficient model documentation")
            recommendations.append(
                "Provide comprehensive model documentation including purpose, limitations, and intended use"
            )

        # Check for explainability
        if model.model_type in ["deep_learning", "neural_network", "transformer"]:
            if "explainability" not in context.get("features", []):
                score += 25
                risk_factors.append("Complex model architecture lacks explainability mechanisms")
                recommendations.append("Implement SHAP, LIME, or attention visualization for model explainability")
            else:
                mitigating_factors.append("Explainability mechanisms implemented")

        # Check for intended use clarity
        if not model.intended_use or len(model.intended_use) < 20:
            score += 15
            risk_factors.append("Unclear intended use specification")
            recommendations.append("Document specific intended use cases and deployment contexts")

        # Check for prohibited use documentation
        if not model.prohibited_uses:
            score += 10
            risk_factors.append("No documented prohibited uses")
            recommendations.append("Define and document prohibited use cases to prevent misuse")
        else:
            mitigating_factors.append(f"{len(model.prohibited_uses)} prohibited uses documented")

        # Check for user disclosure
        if context.get("requires_human_interaction", True):
            if not context.get("ai_disclosure", False):
                score += 15
                risk_factors.append("No AI system disclosure to users")
                recommendations.append("Implement clear AI disclosure per EU AI Act Article 52")

        return {
            "score": min(score, 100),
            "risk_factors": risk_factors,
            "mitigating_factors": mitigating_factors,
            "recommendations": recommendations,
        }

    async def _assess_fairness(
        self,
        model: AIModelRegistration,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Assess fairness and bias risks"""
        score = 0.0
        risk_factors = []
        mitigating_factors = []
        recommendations = []

        # High-risk use case assessment
        use_case = model.use_case_category.lower()
        if use_case in ["employment", "hr", "recruitment", "hiring"]:
            score += 30
            risk_factors.append("High-risk employment AI use case")
            recommendations.append("Implement mandatory bias testing for protected characteristics")

        if use_case in ["credit", "lending", "financial", "insurance"]:
            score += 25
            risk_factors.append("Financial services AI requires fairness monitoring")
            recommendations.append("Deploy disparate impact testing and fair lending compliance")

        if use_case in ["healthcare", "medical", "diagnostic"]:
            score += 20
            risk_factors.append("Healthcare AI requires demographic fairness validation")
            recommendations.append("Validate model performance across demographic groups")

        # Check for bias testing
        if context.get("bias_testing_performed", False):
            mitigating_factors.append("Bias testing has been performed")
            score -= 10
        else:
            score += 20
            risk_factors.append("No documented bias testing")
            recommendations.append("Conduct comprehensive bias audit across protected characteristics")

        # Check for training data documentation
        if not model.training_data_description:
            score += 15
            risk_factors.append("Training data composition undocumented")
            recommendations.append("Document training data sources, demographics, and potential biases")
        else:
            mitigating_factors.append("Training data documented")

        # Check for ongoing monitoring
        if not context.get("fairness_monitoring", False):
            score += 10
            risk_factors.append("No ongoing fairness monitoring")
            recommendations.append("Implement continuous fairness metrics monitoring in production")

        return {
            "score": min(max(score, 0), 100),
            "risk_factors": risk_factors,
            "mitigating_factors": mitigating_factors,
            "recommendations": recommendations,
        }

    async def _assess_accountability(
        self,
        model: AIModelRegistration,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Assess accountability and governance risks"""
        score = 0.0
        risk_factors = []
        mitigating_factors = []
        recommendations = []

        # Check for human oversight capability
        if not context.get("human_oversight", False):
            score += 25
            risk_factors.append("No human oversight mechanism defined")
            recommendations.append("Implement human-in-the-loop or human-on-the-loop oversight")
        else:
            mitigating_factors.append("Human oversight mechanism in place")

        # Check for decision reversal capability
        if not context.get("decision_reversal", False):
            score += 15
            risk_factors.append("No mechanism for decision reversal")
            recommendations.append("Implement process for contesting and reversing AI decisions")

        # Check for clear ownership
        if not model.registered_by:
            score += 20
            risk_factors.append("No accountable owner identified")
            recommendations.append("Designate accountable person/team for model governance")
        else:
            mitigating_factors.append(f"Accountable owner: {model.registered_by}")

        # Check for incident response
        if not context.get("incident_response_plan", False):
            score += 15
            risk_factors.append("No AI incident response plan")
            recommendations.append("Develop AI-specific incident response procedures")

        # Check for version control
        if not model.version:
            score += 10
            risk_factors.append("No version tracking")
            recommendations.append("Implement model versioning and change tracking")
        else:
            mitigating_factors.append(f"Version controlled: {model.version}")

        # Check for scheduled reviews
        if not model.next_review_date:
            score += 10
            risk_factors.append("No scheduled review date")
            recommendations.append("Establish regular model review schedule (quarterly minimum)")

        return {
            "score": min(score, 100),
            "risk_factors": risk_factors,
            "mitigating_factors": mitigating_factors,
            "recommendations": recommendations,
        }

    async def _assess_robustness(
        self,
        model: AIModelRegistration,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Assess robustness and reliability risks"""
        score = 0.0
        risk_factors = []
        mitigating_factors = []
        recommendations = []

        # Check for testing coverage
        if not context.get("test_coverage", 0) > 80:
            score += 20
            risk_factors.append("Insufficient test coverage")
            recommendations.append("Achieve minimum 80% test coverage including edge cases")
        else:
            mitigating_factors.append(f"Test coverage: {context.get('test_coverage')}%")

        # Check for adversarial testing
        if not context.get("adversarial_testing", False):
            score += 20
            risk_factors.append("No adversarial robustness testing")
            recommendations.append("Conduct adversarial testing and red team exercises")

        # Check for drift monitoring
        if not context.get("drift_monitoring", False):
            score += 15
            risk_factors.append("No model drift monitoring")
            recommendations.append("Implement data and concept drift detection")

        # Check for fallback mechanisms
        if not context.get("fallback_mechanism", False):
            score += 15
            risk_factors.append("No fallback for model failures")
            recommendations.append("Implement graceful degradation and fallback procedures")
        else:
            mitigating_factors.append("Fallback mechanism available")

        # Check for performance SLAs
        if not context.get("performance_sla", False):
            score += 10
            risk_factors.append("No defined performance SLAs")
            recommendations.append("Define and monitor performance SLAs (latency, accuracy)")

        # Check for redundancy
        if model.deployment_location == "single_instance":
            score += 10
            risk_factors.append("Single point of failure in deployment")
            recommendations.append("Implement redundancy for critical AI systems")

        return {
            "score": min(score, 100),
            "risk_factors": risk_factors,
            "mitigating_factors": mitigating_factors,
            "recommendations": recommendations,
        }

    async def _assess_privacy(
        self,
        model: AIModelRegistration,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Assess privacy and data protection risks"""
        score = 0.0
        risk_factors = []
        mitigating_factors = []
        recommendations = []

        # Check for personal data processing
        if model.personal_data_processed:
            score += 15
            risk_factors.append("Processes personal data")

            # Check for data protection measures
            if not context.get("encryption_at_rest", False):
                score += 15
                risk_factors.append("Personal data not encrypted at rest")
                recommendations.append("Implement encryption for all personal data at rest")
            else:
                mitigating_factors.append("Data encrypted at rest")

            if not context.get("encryption_in_transit", False):
                score += 10
                risk_factors.append("Data not encrypted in transit")
                recommendations.append("Implement TLS for all data transmission")

        # Check for sensitive data
        if model.sensitive_data_processed:
            score += 25
            risk_factors.append("Processes sensitive/special category data")
            recommendations.append("Conduct Data Protection Impact Assessment (DPIA)")

            if not context.get("dpia_completed", False):
                score += 15
                risk_factors.append("No DPIA for sensitive data processing")

        # Check for data minimization
        if not context.get("data_minimization", False):
            score += 10
            risk_factors.append("Data minimization not verified")
            recommendations.append("Review and minimize data collection to necessary elements")

        # Check for retention policy
        if model.data_retention_days > 365:
            score += 10
            risk_factors.append(f"Long data retention period: {model.data_retention_days} days")
            recommendations.append("Review data retention policy for compliance")
        elif model.data_retention_days > 0:
            mitigating_factors.append(f"Data retention: {model.data_retention_days} days")

        # Check for cross-border transfers
        if len(model.data_residency) > 1:
            score += 15
            risk_factors.append("Cross-border data transfers detected")
            recommendations.append("Verify adequacy decisions or SCCs for cross-border transfers")

        # Check for consent management
        if model.personal_data_processed and not context.get("consent_management", False):
            score += 15
            risk_factors.append("No consent management mechanism")
            recommendations.append("Implement documented consent collection and management")

        return {
            "score": min(score, 100),
            "risk_factors": risk_factors,
            "mitigating_factors": mitigating_factors,
            "recommendations": recommendations,
        }

    async def _assess_security(
        self,
        model: AIModelRegistration,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Assess security control risks"""
        score = 0.0
        risk_factors = []
        mitigating_factors = []
        recommendations = []

        # Check for access controls
        if not context.get("access_controls", False):
            score += 25
            risk_factors.append("No documented access controls")
            recommendations.append("Implement role-based access control for model and data")
        else:
            mitigating_factors.append("Access controls implemented")

        # Check for API security
        if model.api_endpoints:
            if not context.get("api_authentication", False):
                score += 20
                risk_factors.append("API endpoints lack authentication")
                recommendations.append("Implement API authentication (OAuth2/API keys)")

            if not context.get("rate_limiting", False):
                score += 10
                risk_factors.append("No API rate limiting")
                recommendations.append("Implement rate limiting to prevent abuse")

        # Check for audit logging
        if not context.get("audit_logging", False):
            score += 15
            risk_factors.append("No audit logging for model access")
            recommendations.append("Enable comprehensive audit logging")
        else:
            mitigating_factors.append("Audit logging enabled")

        # Check for vulnerability scanning
        if not context.get("vulnerability_scan", False):
            score += 15
            risk_factors.append("No regular vulnerability scanning")
            recommendations.append("Conduct regular security vulnerability assessments")

        # Check for model security
        if not context.get("model_signing", False):
            score += 10
            risk_factors.append("Model artifacts not cryptographically signed")
            recommendations.append("Implement model signing for integrity verification")

        # Third-party provider assessment
        if model.provider not in ["internal", "self"]:
            if not context.get("vendor_assessment", False):
                score += 15
                risk_factors.append(f"Third-party provider ({model.provider}) not assessed")
                recommendations.append("Conduct vendor security assessment")

        return {
            "score": min(score, 100),
            "risk_factors": risk_factors,
            "mitigating_factors": mitigating_factors,
            "recommendations": recommendations,
        }

    def _calculate_overall_risk_score(self, dimension_scores: Dict[str, float]) -> float:
        """Calculate weighted overall risk score"""
        total_score = 0.0
        total_weight = 0.0

        for dimension, score in dimension_scores.items():
            weight = self.RISK_WEIGHTS.get(dimension, 0.1)
            total_score += score * weight
            total_weight += weight

        return round(total_score / total_weight if total_weight > 0 else 0, 1)

    def _classify_risk_level(
        self,
        model: AIModelRegistration,
        risk_score: float,
    ) -> RiskLevel:
        """Classify risk level based on EU AI Act criteria"""

        # Check for unacceptable uses first
        intended_use_lower = model.intended_use.lower() if model.intended_use else ""
        for prohibited in self.EU_AI_ACT_UNACCEPTABLE_USES:
            if prohibited.replace("_", " ") in intended_use_lower:
                return RiskLevel.UNACCEPTABLE

        # Check for high-risk domains
        use_case_lower = model.use_case_category.lower()
        for high_risk_domain in self.EU_AI_ACT_HIGH_RISK_DOMAINS:
            if high_risk_domain.replace("_", " ") in use_case_lower:
                return RiskLevel.HIGH

        # Score-based classification
        if risk_score >= 70:
            return RiskLevel.HIGH
        elif risk_score >= 40:
            return RiskLevel.LIMITED
        elif risk_score >= 0:
            return RiskLevel.MINIMAL

        return RiskLevel.UNKNOWN

    def _determine_applicable_regulations(
        self,
        model: AIModelRegistration,
    ) -> List[RegulationType]:
        """Determine which regulations apply to this model"""
        regulations = []

        # EU AI Act - applies to AI systems in EU
        if "eu" in [r.lower() for r in model.data_residency]:
            regulations.append(RegulationType.EU_AI_ACT)

        # GDPR - personal data in EU
        if model.personal_data_processed and "eu" in [r.lower() for r in model.data_residency]:
            regulations.append(RegulationType.GDPR)

        # HIPAA - healthcare in US
        if model.use_case_category.lower() in ["healthcare", "medical", "diagnostic"]:
            if "us" in [r.lower() for r in model.data_residency]:
                regulations.append(RegulationType.HIPAA)

        # SEC - financial services
        if model.use_case_category.lower() in ["finance", "trading", "investment", "advisory"]:
            regulations.append(RegulationType.SEC_AI_GUIDANCE)

        # CCPA - California personal data
        if model.personal_data_processed and "us" in [r.lower() for r in model.data_residency]:
            regulations.append(RegulationType.CCPA)

        # Add existing certifications
        for cert in model.certifications:
            if "soc2" in cert.lower():
                regulations.append(RegulationType.SOC2)
            if "iso" in cert.lower() and "27001" in cert:
                regulations.append(RegulationType.ISO_27001)

        return list(set(regulations))

    def _get_regulatory_requirements(
        self,
        regulation: RegulationType,
        model: AIModelRegistration,
    ) -> List[str]:
        """Get specific requirements for a regulation"""
        requirements_map = {
            RegulationType.EU_AI_ACT: [
                "Risk management system implementation",
                "Data governance and quality assurance",
                "Technical documentation maintenance",
                "Record-keeping and logging",
                "Transparency and user information",
                "Human oversight mechanisms",
                "Accuracy, robustness, cybersecurity",
                "Conformity assessment (if high-risk)",
            ],
            RegulationType.HIPAA: [
                "PHI access controls",
                "Encryption of health data",
                "Audit trail maintenance",
                "Business Associate Agreement",
                "Breach notification procedures",
                "Minimum necessary standard",
            ],
            RegulationType.SEC_AI_GUIDANCE: [
                "Model risk management",
                "Disclosure of AI usage in investment decisions",
                "Fair dealing obligations",
                "Compliance monitoring",
                "Conflicts of interest management",
            ],
            RegulationType.GDPR: [
                "Lawful basis for processing",
                "Data subject rights implementation",
                "Privacy by design and default",
                "Data Protection Impact Assessment",
                "Records of processing activities",
                "International transfer safeguards",
            ],
            RegulationType.CCPA: [
                "Consumer disclosure rights",
                "Opt-out mechanisms",
                "Data deletion capabilities",
                "Non-discrimination requirements",
            ],
            RegulationType.SOC2: [
                "Security controls",
                "Availability monitoring",
                "Processing integrity",
                "Confidentiality measures",
                "Privacy controls",
            ],
        }

        return requirements_map.get(regulation, ["Consult regulatory documentation"])

    def _prioritize_recommendations(
        self,
        recommendations: List[str],
    ) -> List[str]:
        """Prioritize recommendations by importance"""
        # Priority keywords
        high_priority_keywords = ["security", "breach", "critical", "immediate", "DPIA", "encryption"]
        medium_priority_keywords = ["implement", "conduct", "establish", "deploy"]

        def priority_score(rec: str) -> int:
            rec_lower = rec.lower()
            score = 0
            for keyword in high_priority_keywords:
                if keyword in rec_lower:
                    score += 2
            for keyword in medium_priority_keywords:
                if keyword in rec_lower:
                    score += 1
            return score

        # Remove duplicates while preserving order
        seen = set()
        unique_recs = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recs.append(rec)

        return sorted(unique_recs, key=priority_score, reverse=True)

    async def _update_risk_trend(
        self,
        model_id: str,
        model_name: str,
        risk_score: float,
    ):
        """Update risk trend history for a model"""
        if model_id not in self._risk_history:
            self._risk_history[model_id] = RiskTrend(
                entity_type="ai_model",
                entity_id=model_id,
                entity_name=model_name,
                period="assessment",
            )

        status = "critical" if risk_score >= 70 else "warning" if risk_score >= 40 else "normal"
        self._risk_history[model_id].add_data_point(risk_score, status)

    def get_risk_trend(self, model_id: str) -> Optional[RiskTrend]:
        """Get risk trend for a model"""
        return self._risk_history.get(model_id)

    async def _generate_ai_insights(
        self,
        model: AIModelRegistration,
        assessment: RiskAssessment,
        dimension_results: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate AI-powered insights for risk dimensions.

        Args:
            model: AI model registration
            assessment: The risk assessment being generated
            dimension_results: Raw results from each dimension assessment

        Returns:
            Dict containing AI-generated explanations for each dimension
        """
        ai_insights: Dict[str, Any] = {
            "dimension_explanations": {},
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Lazy import to avoid circular imports
        if self._ai_analyzer is None:
            return ai_insights

        # Generate explanations for each dimension in parallel
        dimension_tasks = []
        dimensions = ["transparency", "fairness", "accountability", "robustness", "privacy", "security"]

        for dimension in dimensions:
            result = dimension_results.get(dimension, {})
            scores = {
                "dimension_score": result.get("score", 0),
                "risk_factors_count": len(result.get("risk_factors", [])),
                "mitigating_factors_count": len(result.get("mitigating_factors", [])),
            }
            task = self._ai_analyzer.explain_risk_dimension(
                dimension=dimension,
                scores=scores,
                model=model,
                context={"raw_result": result},
            )
            dimension_tasks.append((dimension, task))

        # Execute all dimension explanations concurrently
        for dimension, task in dimension_tasks:
            try:
                explanation = await task
                ai_insights["dimension_explanations"][dimension] = {
                    "ai_explanation": explanation.get("explanation", ""),
                    "key_concerns": explanation.get("key_concerns", []),
                    "mitigation_strategies": explanation.get("mitigation_strategies", []),
                }
            except Exception:
                # Gracefully handle AI failures - don't break the assessment
                ai_insights["dimension_explanations"][dimension] = {
                    "ai_explanation": None,
                    "error": "AI explanation generation failed",
                }

        return ai_insights

    async def get_ai_recommendations(
        self,
        assessment: RiskAssessment,
        model: AIModelRegistration,
    ) -> List[str]:
        """
        Get AI-generated recommendations for risk mitigation.

        Calls the AI analyzer to generate prioritized, actionable recommendations
        based on the risk assessment and model details.

        Args:
            assessment: RiskAssessment to analyze
            model: AIModelRegistration associated with the assessment

        Returns:
            List of AI-generated recommendation strings

        Raises:
            ValueError: If ai_analyzer is not configured
        """
        if self._ai_analyzer is None:
            raise ValueError("AI analyzer not configured. Initialize RiskDetector with ai_analyzer parameter.")

        return await self._ai_analyzer.generate_risk_recommendations(assessment, model)

    async def quick_scan(
        self,
        model_name: str,
        model_type: str,
        use_case: str,
        processes_personal_data: bool = False,
        data_residency: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform quick risk scan without full registration.

        Returns simplified risk assessment for demos and initial screening.
        """
        # Create temporary registration
        temp_model = AIModelRegistration(
            name=model_name,
            version="scan",
            description=f"Quick scan for {model_name}",
            model_type=model_type,
            provider="unknown",
            deployment_location="unknown",
            data_residency=data_residency or ["unknown"],
            intended_use=use_case,
            use_case_category=use_case,
            personal_data_processed=processes_personal_data,
            registered_by="quick_scan",
        )

        # Run assessment
        assessment = await self.assess_model(temp_model, {})

        return {
            "model_name": model_name,
            "risk_level": assessment.risk_level.value,
            "risk_score": assessment.risk_score,
            "applicable_regulations": [r.value for r in assessment.applicable_regulations],
            "top_risks": assessment.risk_factors[:5],
            "priority_actions": assessment.recommendations[:5],
            "dimension_scores": {
                "transparency": assessment.transparency_score,
                "fairness": assessment.fairness_score,
                "accountability": assessment.accountability_score,
                "robustness": assessment.robustness_score,
                "privacy": assessment.privacy_score,
                "security": assessment.security_score,
            },
        }

    def get_risk_indicators(self, model_id: str) -> List[RiskIndicator]:
        """Generate risk indicators for dashboard display"""
        assessment = self._assessment_cache.get(model_id)
        if not assessment:
            return []

        indicators = [
            RiskIndicator(
                category=RiskCategory.TRANSPARENCY,
                name="Transparency Score",
                description="Model explainability and documentation completeness",
                value=100 - assessment.transparency_score,
                status="normal" if assessment.transparency_score >= 70 else "warning",
            ),
            RiskIndicator(
                category=RiskCategory.FAIRNESS,
                name="Fairness Score",
                description="Bias detection and mitigation effectiveness",
                value=100 - assessment.fairness_score,
                status="normal" if assessment.fairness_score >= 70 else "warning",
            ),
            RiskIndicator(
                category=RiskCategory.ACCOUNTABILITY,
                name="Accountability Score",
                description="Governance and oversight mechanisms",
                value=100 - assessment.accountability_score,
                status="normal" if assessment.accountability_score >= 70 else "warning",
            ),
            RiskIndicator(
                category=RiskCategory.SYSTEM_RELIABILITY,
                name="Robustness Score",
                description="System reliability and testing coverage",
                value=100 - assessment.robustness_score,
                status="normal" if assessment.robustness_score >= 70 else "warning",
            ),
            RiskIndicator(
                category=RiskCategory.DATA_PROTECTION,
                name="Privacy Score",
                description="Data protection and privacy compliance",
                value=100 - assessment.privacy_score,
                status="normal" if assessment.privacy_score >= 70 else "warning",
            ),
            RiskIndicator(
                category=RiskCategory.SECURITY_VULNERABILITY,
                name="Security Score",
                description="Security controls and vulnerability management",
                value=100 - assessment.security_score,
                status="normal" if assessment.security_score >= 70 else "warning",
            ),
        ]

        return indicators
