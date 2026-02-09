"""
Enterprise AI Compliance Platform - Policy Enforcer

Production-grade policy enforcement engine with rule-based violation
detection, automated remediation suggestions, and continuous monitoring.

Supports optional AI-enhanced analysis via ComplianceAIAnalyzer integration.
"""

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

from ..models.compliance_models import (
    AIModelRegistration,
    ComplianceStatus,
    PolicyViolation,
    RegulationType,
    RemediationAction,
    RemediationStatus,
    ViolationSeverity,
)

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from ..services.compliance_ai_analyzer import ComplianceAIAnalyzer


class PolicyType(str, Enum):
    """Types of compliance policies"""

    MANDATORY = "mandatory"  # Must comply
    RECOMMENDED = "recommended"  # Should comply
    CONDITIONAL = "conditional"  # Depends on context
    EXEMPTABLE = "exemptable"  # Can be exempted with approval


class PolicyScope(str, Enum):
    """Scope of policy application"""

    GLOBAL = "global"  # Applies to all models
    HIGH_RISK = "high_risk"  # Only high-risk models
    PERSONAL_DATA = "personal_data"  # Models processing personal data
    HEALTHCARE = "healthcare"  # Healthcare domain
    FINANCE = "finance"  # Financial services
    SPECIFIC_MODEL = "specific"  # Specific model types


@dataclass
class CompliancePolicy:
    """Definition of a compliance policy/rule"""

    policy_id: str
    name: str
    description: str
    regulation: RegulationType
    article_reference: Optional[str] = None

    # Policy characteristics
    policy_type: PolicyType = PolicyType.MANDATORY
    scope: PolicyScope = PolicyScope.GLOBAL
    severity_if_violated: ViolationSeverity = ViolationSeverity.MEDIUM

    # Rule definition
    check_function: Optional[Callable] = None
    required_conditions: List[str] = field(default_factory=list)
    prohibited_conditions: List[str] = field(default_factory=list)

    # Remediation
    remediation_guidance: str = ""
    remediation_deadline_days: int = 30
    auto_remediation_available: bool = False
    auto_remediation_action: Optional[str] = None

    # Status
    is_active: bool = True
    effective_from: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    effective_until: Optional[datetime] = None

    # Metadata
    created_by: str = "system"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: Optional[datetime] = None
    version: str = "1.0"


class PolicyEnforcer:
    """
    Policy enforcement engine for AI compliance.

    Provides:
    - Rule-based policy checking
    - Automated violation detection
    - Remediation tracking
    - Continuous compliance monitoring
    """

    def __init__(
        self,
        auto_remediate: bool = False,
        strict_mode: bool = True,
        violation_callback: Optional[Callable] = None,
        ai_analyzer: Optional["ComplianceAIAnalyzer"] = None,
        enable_ai_analysis: bool = False,
    ):
        """
        Initialize the Policy Enforcer.

        Args:
            auto_remediate: Automatically apply available remediations
            strict_mode: Fail on any mandatory policy violation
            violation_callback: Callback function when violations detected
            ai_analyzer: Optional ComplianceAIAnalyzer instance for AI-enhanced
                        violation explanations and remediation recommendations
            enable_ai_analysis: Enable AI-powered analysis when ai_analyzer is provided.
                               When True and ai_analyzer is set, violations will be
                               enhanced with AI explanations and remediations will
                               use AI-generated recommendations.
        """
        self.auto_remediate = auto_remediate
        self.strict_mode = strict_mode
        self.violation_callback = violation_callback
        self.ai_analyzer = ai_analyzer
        self.enable_ai_analysis = enable_ai_analysis

        # Policy registry
        self._policies: Dict[str, CompliancePolicy] = {}

        # Violations tracking
        self._active_violations: Dict[str, PolicyViolation] = {}
        self._remediation_queue: List[RemediationAction] = []

        # Exemptions
        self._exemptions: Dict[str, Dict[str, Any]] = {}

        # Initialize with default policies
        self._register_default_policies()

    def _register_default_policies(self):
        """Register default compliance policies from regulations"""

        # EU AI Act Policies
        self._register_eu_ai_act_policies()

        # HIPAA Policies
        self._register_hipaa_policies()

        # SEC AI Guidance Policies
        self._register_sec_policies()

        # GDPR Policies
        self._register_gdpr_policies()

        # Fair Housing Act (FHA) Policies
        self._register_fha_policies()

    def _register_fha_policies(self):
        """Register Fair Housing Act compliance policies for Real Estate AI."""

        policies = [
            CompliancePolicy(
                policy_id="FHA-001",
                name="Protected Class Discrimination",
                description="Prohibits discrimination based on race, color, religion, sex, handicap, familial status, or national origin.",
                regulation=RegulationType.EU_AI_ACT,  # Using as placeholder if FHA not in Enum
                policy_type=PolicyType.MANDATORY,
                scope=PolicyScope.GLOBAL,
                severity_if_violated=ViolationSeverity.CRITICAL,
                prohibited_conditions=["discriminatory_steering", "protected_class_reference", "exclusionary_language"],
                remediation_guidance="Remove any references to protected classes or steering language. Use neutral, property-focused descriptions.",
                remediation_deadline_days=0,
            ),
            CompliancePolicy(
                policy_id="FHA-002",
                name="Advertising Compliance",
                description="Ensures all real estate advertising is inclusive and non-discriminatory.",
                regulation=RegulationType.EU_AI_ACT,
                policy_type=PolicyType.MANDATORY,
                scope=PolicyScope.GLOBAL,
                severity_if_violated=ViolationSeverity.HIGH,
                required_conditions=["equal_housing_opportunity_disclosure"],
                remediation_guidance="Include Equal Housing Opportunity disclaimer in all advertising materials.",
                remediation_deadline_days=1,
            ),
        ]

        for policy in policies:
            self._policies[policy.policy_id] = policy

    async def intercept_message(self, message_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Intercepts and analyzes a message for real-time compliance.

        Returns:
            Dict containing 'allowed' (bool), 'violations' (list), and 'suggestion' (str).
        """
        violations = []

        # Simple pattern-based detection for FHA (in production, use LLM-based analysis)
        fha_keywords = [
            r"\b(Union[white, black]|Union[asian, hispanic])\s+(Union[neighborhood, area]|people)\b",
            r"\b(Union[christian, jewish]|Union[muslim, catholic])\b",
            r"\b(no\s+Union[kids, adults]\s+Union[only, no]\s+families)\b",
            r"\b(perfect\s+for\s+Union[singles, man]\s+Union[cave, bachelor]\s+pad)\b",
            r"\b(Union[restricted, exclusive]|private)\s+community\b",
        ]

        for pattern in fha_keywords:
            if re.search(pattern, message_text, re.IGNORECASE):
                violations.append(
                    {
                        "policy_id": "FHA-001",
                        "severity": "CRITICAL",
                        "message": f"Potential FHA violation detected: {pattern}",
                    }
                )

        if not violations:
            return {"allowed": True, "violations": [], "suggestion": None}

        # If violations found, provide a suggestion (placeholder)
        suggestion = "This property is open to everyone. It features [Property Features] and is located in [Location]."

        return {"allowed": False, "violations": violations, "suggestion": suggestion}

    def _register_eu_ai_act_policies(self):
        """Register EU AI Act compliance policies"""

        policies = [
            CompliancePolicy(
                policy_id="EUAI-001",
                name="Risk Management System",
                description="High-risk AI systems must implement a risk management system",
                regulation=RegulationType.EU_AI_ACT,
                article_reference="Article 9",
                policy_type=PolicyType.MANDATORY,
                scope=PolicyScope.HIGH_RISK,
                severity_if_violated=ViolationSeverity.HIGH,
                required_conditions=["risk_assessment_completed", "risk_mitigation_plan"],
                remediation_guidance="Implement comprehensive risk management including identification, analysis, evaluation, and mitigation of risks",
                remediation_deadline_days=90,
            ),
            CompliancePolicy(
                policy_id="EUAI-002",
                name="Data Governance",
                description="Training, validation, and testing data must meet quality criteria",
                regulation=RegulationType.EU_AI_ACT,
                article_reference="Article 10",
                policy_type=PolicyType.MANDATORY,
                scope=PolicyScope.HIGH_RISK,
                severity_if_violated=ViolationSeverity.HIGH,
                required_conditions=["data_governance_policy", "data_quality_metrics"],
                remediation_guidance="Establish data governance framework with quality controls for training data",
                remediation_deadline_days=60,
            ),
            CompliancePolicy(
                policy_id="EUAI-003",
                name="Technical Documentation",
                description="AI systems must have comprehensive technical documentation",
                regulation=RegulationType.EU_AI_ACT,
                article_reference="Article 11",
                policy_type=PolicyType.MANDATORY,
                scope=PolicyScope.HIGH_RISK,
                severity_if_violated=ViolationSeverity.MEDIUM,
                required_conditions=["technical_documentation", "system_description"],
                remediation_guidance="Create and maintain technical documentation per Annex IV requirements",
                remediation_deadline_days=30,
            ),
            CompliancePolicy(
                policy_id="EUAI-004",
                name="Record-Keeping (Logging)",
                description="High-risk AI must automatically log events throughout its operation",
                regulation=RegulationType.EU_AI_ACT,
                article_reference="Article 12",
                policy_type=PolicyType.MANDATORY,
                scope=PolicyScope.HIGH_RISK,
                severity_if_violated=ViolationSeverity.HIGH,
                required_conditions=["audit_logging_enabled", "log_retention_policy"],
                remediation_guidance="Enable automatic logging of AI system events with appropriate retention",
                remediation_deadline_days=14,
                auto_remediation_available=True,
                auto_remediation_action="enable_audit_logging",
            ),
            CompliancePolicy(
                policy_id="EUAI-005",
                name="Transparency",
                description="AI systems must provide clear information to users about AI usage",
                regulation=RegulationType.EU_AI_ACT,
                article_reference="Article 13",
                policy_type=PolicyType.MANDATORY,
                scope=PolicyScope.GLOBAL,
                severity_if_violated=ViolationSeverity.MEDIUM,
                required_conditions=["user_disclosure", "ai_system_info_available"],
                remediation_guidance="Implement transparency measures including clear AI disclosure to users",
                remediation_deadline_days=30,
            ),
            CompliancePolicy(
                policy_id="EUAI-006",
                name="Human Oversight",
                description="High-risk AI must allow for human oversight and intervention",
                regulation=RegulationType.EU_AI_ACT,
                article_reference="Article 14",
                policy_type=PolicyType.MANDATORY,
                scope=PolicyScope.HIGH_RISK,
                severity_if_violated=ViolationSeverity.CRITICAL,
                required_conditions=["human_oversight_mechanism", "intervention_capability"],
                remediation_guidance="Implement human-in-the-loop or human-on-the-loop oversight mechanisms",
                remediation_deadline_days=30,
            ),
            CompliancePolicy(
                policy_id="EUAI-007",
                name="Accuracy and Robustness",
                description="AI systems must achieve appropriate accuracy and robustness",
                regulation=RegulationType.EU_AI_ACT,
                article_reference="Article 15",
                policy_type=PolicyType.MANDATORY,
                scope=PolicyScope.HIGH_RISK,
                severity_if_violated=ViolationSeverity.HIGH,
                required_conditions=["accuracy_metrics_defined", "robustness_testing"],
                remediation_guidance="Define and validate accuracy and robustness requirements",
                remediation_deadline_days=60,
            ),
            CompliancePolicy(
                policy_id="EUAI-008",
                name="Prohibited AI Practices",
                description="Social scoring and manipulation systems are prohibited",
                regulation=RegulationType.EU_AI_ACT,
                article_reference="Article 5",
                policy_type=PolicyType.MANDATORY,
                scope=PolicyScope.GLOBAL,
                severity_if_violated=ViolationSeverity.CRITICAL,
                prohibited_conditions=["social_scoring", "subliminal_manipulation", "exploitation_vulnerable"],
                remediation_guidance="Immediately cease prohibited AI practices",
                remediation_deadline_days=0,  # Immediate
            ),
        ]

        for policy in policies:
            self._policies[policy.policy_id] = policy

    def _register_hipaa_policies(self):
        """Register HIPAA compliance policies"""

        policies = [
            CompliancePolicy(
                policy_id="HIPAA-001",
                name="PHI Access Controls",
                description="Protected Health Information must have access controls",
                regulation=RegulationType.HIPAA,
                article_reference="45 CFR 164.312(a)(1)",
                policy_type=PolicyType.MANDATORY,
                scope=PolicyScope.HEALTHCARE,
                severity_if_violated=ViolationSeverity.CRITICAL,
                required_conditions=["phi_access_controls", "unique_user_identification"],
                remediation_guidance="Implement technical safeguards for PHI access",
                remediation_deadline_days=30,
            ),
            CompliancePolicy(
                policy_id="HIPAA-002",
                name="PHI Encryption",
                description="PHI must be encrypted at rest and in transit",
                regulation=RegulationType.HIPAA,
                article_reference="45 CFR 164.312(a)(2)(iv)",
                policy_type=PolicyType.MANDATORY,
                scope=PolicyScope.HEALTHCARE,
                severity_if_violated=ViolationSeverity.CRITICAL,
                required_conditions=["encryption_at_rest", "encryption_in_transit"],
                remediation_guidance="Implement AES-256 encryption for PHI",
                remediation_deadline_days=14,
            ),
            CompliancePolicy(
                policy_id="HIPAA-003",
                name="Audit Controls",
                description="Systems containing PHI must have audit controls",
                regulation=RegulationType.HIPAA,
                article_reference="45 CFR 164.312(b)",
                policy_type=PolicyType.MANDATORY,
                scope=PolicyScope.HEALTHCARE,
                severity_if_violated=ViolationSeverity.HIGH,
                required_conditions=["hipaa_audit_logging", "access_audit_trail"],
                remediation_guidance="Enable comprehensive audit logging for PHI access",
                remediation_deadline_days=14,
                auto_remediation_available=True,
                auto_remediation_action="enable_hipaa_audit",
            ),
            CompliancePolicy(
                policy_id="HIPAA-004",
                name="Business Associate Agreement",
                description="Third-party processors of PHI require BAA",
                regulation=RegulationType.HIPAA,
                article_reference="45 CFR 164.502(e)",
                policy_type=PolicyType.MANDATORY,
                scope=PolicyScope.HEALTHCARE,
                severity_if_violated=ViolationSeverity.HIGH,
                required_conditions=["baa_executed"],
                remediation_guidance="Execute Business Associate Agreement with all PHI processors",
                remediation_deadline_days=30,
            ),
            CompliancePolicy(
                policy_id="HIPAA-005",
                name="Minimum Necessary",
                description="Only minimum necessary PHI should be accessed",
                regulation=RegulationType.HIPAA,
                article_reference="45 CFR 164.502(b)",
                policy_type=PolicyType.MANDATORY,
                scope=PolicyScope.HEALTHCARE,
                severity_if_violated=ViolationSeverity.MEDIUM,
                required_conditions=["minimum_necessary_policy", "data_minimization"],
                remediation_guidance="Implement data minimization practices for PHI",
                remediation_deadline_days=30,
            ),
        ]

        for policy in policies:
            self._policies[policy.policy_id] = policy

    def _register_sec_policies(self):
        """Register SEC AI guidance policies"""

        policies = [
            CompliancePolicy(
                policy_id="SEC-001",
                name="Model Risk Management",
                description="AI models used in investment decisions require risk management",
                regulation=RegulationType.SEC_AI_GUIDANCE,
                policy_type=PolicyType.MANDATORY,
                scope=PolicyScope.FINANCE,
                severity_if_violated=ViolationSeverity.HIGH,
                required_conditions=["model_risk_framework", "model_validation"],
                remediation_guidance="Implement model risk management framework per SR 11-7",
                remediation_deadline_days=60,
            ),
            CompliancePolicy(
                policy_id="SEC-002",
                name="AI Disclosure",
                description="Material use of AI in investment decisions must be disclosed",
                regulation=RegulationType.SEC_AI_GUIDANCE,
                policy_type=PolicyType.MANDATORY,
                scope=PolicyScope.FINANCE,
                severity_if_violated=ViolationSeverity.HIGH,
                required_conditions=["ai_usage_disclosure", "client_notification"],
                remediation_guidance="Disclose AI usage in investment decision-making to clients",
                remediation_deadline_days=30,
            ),
            CompliancePolicy(
                policy_id="SEC-003",
                name="Fair Dealing",
                description="AI must not create unfair advantages or front-running",
                regulation=RegulationType.SEC_AI_GUIDANCE,
                policy_type=PolicyType.MANDATORY,
                scope=PolicyScope.FINANCE,
                severity_if_violated=ViolationSeverity.CRITICAL,
                prohibited_conditions=["front_running", "unfair_advantage"],
                remediation_guidance="Ensure AI systems comply with fair dealing requirements",
                remediation_deadline_days=7,
            ),
        ]

        for policy in policies:
            self._policies[policy.policy_id] = policy

    def _register_gdpr_policies(self):
        """Register GDPR compliance policies"""

        policies = [
            CompliancePolicy(
                policy_id="GDPR-001",
                name="Lawful Basis",
                description="Personal data processing must have lawful basis",
                regulation=RegulationType.GDPR,
                article_reference="Article 6",
                policy_type=PolicyType.MANDATORY,
                scope=PolicyScope.PERSONAL_DATA,
                severity_if_violated=ViolationSeverity.CRITICAL,
                required_conditions=["lawful_basis_documented"],
                remediation_guidance="Document lawful basis for all personal data processing",
                remediation_deadline_days=14,
            ),
            CompliancePolicy(
                policy_id="GDPR-002",
                name="Data Subject Rights",
                description="Systems must support data subject rights (access, deletion, etc.)",
                regulation=RegulationType.GDPR,
                article_reference="Articles 15-22",
                policy_type=PolicyType.MANDATORY,
                scope=PolicyScope.PERSONAL_DATA,
                severity_if_violated=ViolationSeverity.HIGH,
                required_conditions=["data_access_capability", "data_deletion_capability"],
                remediation_guidance="Implement technical capabilities for data subject rights",
                remediation_deadline_days=30,
            ),
            CompliancePolicy(
                policy_id="GDPR-003",
                name="DPIA Requirement",
                description="High-risk processing requires Data Protection Impact Assessment",
                regulation=RegulationType.GDPR,
                article_reference="Article 35",
                policy_type=PolicyType.CONDITIONAL,
                scope=PolicyScope.PERSONAL_DATA,
                severity_if_violated=ViolationSeverity.HIGH,
                required_conditions=["dpia_completed"],
                remediation_guidance="Conduct DPIA for high-risk personal data processing",
                remediation_deadline_days=60,
            ),
            CompliancePolicy(
                policy_id="GDPR-004",
                name="International Transfers",
                description="Cross-border data transfers require appropriate safeguards",
                regulation=RegulationType.GDPR,
                article_reference="Articles 44-49",
                policy_type=PolicyType.MANDATORY,
                scope=PolicyScope.PERSONAL_DATA,
                severity_if_violated=ViolationSeverity.HIGH,
                required_conditions=["transfer_mechanism"],
                remediation_guidance="Implement SCCs or other transfer mechanism for cross-border data",
                remediation_deadline_days=30,
            ),
        ]

        for policy in policies:
            self._policies[policy.policy_id] = policy

    def register_policy(self, policy: CompliancePolicy) -> bool:
        """Register a custom compliance policy"""
        if policy.policy_id in self._policies:
            return False
        self._policies[policy.policy_id] = policy
        return True

    def get_policy(self, policy_id: str) -> Optional[CompliancePolicy]:
        """Get a policy by ID"""
        return self._policies.get(policy_id)

    def list_policies(
        self,
        regulation: Optional[RegulationType] = None,
        scope: Optional[PolicyScope] = None,
        active_only: bool = True,
    ) -> List[CompliancePolicy]:
        """List policies with optional filtering"""
        policies = list(self._policies.values())

        if active_only:
            policies = [p for p in policies if p.is_active]

        if regulation:
            policies = [p for p in policies if p.regulation == regulation]

        if scope:
            policies = [p for p in policies if p.scope == scope]

        return policies

    async def check_compliance(
        self,
        model: AIModelRegistration,
        context: Dict[str, Any],
    ) -> Tuple[ComplianceStatus, List[PolicyViolation]]:
        """
        Check model compliance against all applicable policies.

        Args:
            model: AI model to check
            context: Context including model capabilities and configurations

        Returns:
            Tuple of overall compliance status and list of violations
        """
        violations: List[PolicyViolation] = []

        # Determine applicable policies
        applicable_policies = self._get_applicable_policies(model)

        # Check each policy
        for policy in applicable_policies:
            # Skip exempted policies
            exemption_key = f"{model.model_id}:{policy.policy_id}"
            if exemption_key in self._exemptions:
                continue

            violation = await self._check_policy(policy, model, context)
            if violation:
                violations.append(violation)
                self._active_violations[violation.violation_id] = violation

                # Trigger callback if configured
                if self.violation_callback:
                    await self._safe_callback(self.violation_callback, violation)

                # Auto-remediate if configured
                if self.auto_remediate and policy.auto_remediation_available:
                    await self._auto_remediate(violation, policy)

        # Determine overall status
        status = self._determine_compliance_status(violations)

        return status, violations

    def _get_applicable_policies(
        self,
        model: AIModelRegistration,
    ) -> List[CompliancePolicy]:
        """Get policies applicable to a model"""
        applicable = []

        for policy in self._policies.values():
            if not policy.is_active:
                continue

            # Check scope
            if policy.scope == PolicyScope.GLOBAL:
                applicable.append(policy)
            elif policy.scope == PolicyScope.HIGH_RISK:
                if model.risk_level and model.risk_level.value in ["high", "unacceptable"]:
                    applicable.append(policy)
            elif policy.scope == PolicyScope.PERSONAL_DATA:
                if model.personal_data_processed:
                    applicable.append(policy)
            elif policy.scope == PolicyScope.HEALTHCARE:
                if model.use_case_category.lower() in ["healthcare", "medical", "diagnostic"]:
                    applicable.append(policy)
            elif policy.scope == PolicyScope.FINANCE:
                if model.use_case_category.lower() in ["finance", "trading", "investment"]:
                    applicable.append(policy)

        return applicable

    async def _check_policy(
        self,
        policy: CompliancePolicy,
        model: AIModelRegistration,
        context: Dict[str, Any],
    ) -> Optional[PolicyViolation]:
        """Check a single policy against a model"""

        # Check prohibited conditions
        for prohibited in policy.prohibited_conditions:
            if context.get(prohibited, False) or prohibited in model.intended_use.lower():
                return PolicyViolation(
                    regulation=policy.regulation,
                    policy_id=policy.policy_id,
                    policy_name=policy.name,
                    article_reference=policy.article_reference,
                    severity=policy.severity_if_violated,
                    title=f"Prohibited Condition: {prohibited}",
                    description=f"Model {model.name} violates policy {policy.name}. "
                    f"Prohibited condition detected: {prohibited}",
                    evidence=[f"Context contains prohibited condition: {prohibited}"],
                    affected_systems=[model.model_id],
                    detected_by="policy_enforcer",
                    detection_method="automated_policy_check",
                    potential_fine=self._estimate_fine(policy),
                )

        # Check required conditions
        missing_conditions = []
        for required in policy.required_conditions:
            if not context.get(required, False):
                missing_conditions.append(required)

        if missing_conditions:
            return PolicyViolation(
                regulation=policy.regulation,
                policy_id=policy.policy_id,
                policy_name=policy.name,
                article_reference=policy.article_reference,
                severity=policy.severity_if_violated,
                title=f"Missing Requirements: {policy.name}",
                description=f"Model {model.name} is missing required conditions for {policy.name}: "
                f"{', '.join(missing_conditions)}",
                evidence=[f"Missing: {cond}" for cond in missing_conditions],
                affected_systems=[model.model_id],
                detected_by="policy_enforcer",
                detection_method="automated_policy_check",
                potential_fine=self._estimate_fine(policy),
            )

        # Custom check function if provided
        if policy.check_function:
            try:
                result = await policy.check_function(model, context)
                if result:
                    return result
            except Exception as e:
                # Log but don't fail on check function errors
                pass

        return None

    def _estimate_fine(self, policy: CompliancePolicy) -> Optional[float]:
        """Estimate potential fine for policy violation"""
        fine_estimates = {
            RegulationType.EU_AI_ACT: {
                ViolationSeverity.CRITICAL: 35_000_000,  # €35M or 7% turnover
                ViolationSeverity.HIGH: 15_000_000,  # €15M or 3% turnover
                ViolationSeverity.MEDIUM: 7_500_000,  # €7.5M or 1.5% turnover
                ViolationSeverity.LOW: 1_000_000,
            },
            RegulationType.GDPR: {
                ViolationSeverity.CRITICAL: 20_000_000,  # €20M or 4% turnover
                ViolationSeverity.HIGH: 10_000_000,  # €10M or 2% turnover
                ViolationSeverity.MEDIUM: 5_000_000,
                ViolationSeverity.LOW: 1_000_000,
            },
            RegulationType.HIPAA: {
                ViolationSeverity.CRITICAL: 1_500_000,  # Per violation per year
                ViolationSeverity.HIGH: 250_000,
                ViolationSeverity.MEDIUM: 50_000,
                ViolationSeverity.LOW: 25_000,
            },
        }

        regulation_fines = fine_estimates.get(policy.regulation, {})
        return regulation_fines.get(policy.severity_if_violated)

    def _determine_compliance_status(
        self,
        violations: List[PolicyViolation],
    ) -> ComplianceStatus:
        """Determine overall compliance status from violations"""
        if not violations:
            return ComplianceStatus.COMPLIANT

        severities = [v.severity for v in violations]

        if ViolationSeverity.CRITICAL in severities:
            return ComplianceStatus.NON_COMPLIANT

        if self.strict_mode and severities:
            return ComplianceStatus.NON_COMPLIANT

        if ViolationSeverity.HIGH in severities:
            return ComplianceStatus.PARTIALLY_COMPLIANT

        if ViolationSeverity.MEDIUM in severities:
            return ComplianceStatus.PARTIALLY_COMPLIANT

        return ComplianceStatus.PARTIALLY_COMPLIANT

    async def _auto_remediate(
        self,
        violation: PolicyViolation,
        policy: CompliancePolicy,
    ):
        """Attempt automatic remediation"""
        action = RemediationAction(
            violation_id=violation.violation_id,
            title=f"Auto-remediation: {policy.name}",
            description=policy.remediation_guidance,
            action_type="technical",
            priority=1 if policy.severity_if_violated == ViolationSeverity.CRITICAL else 2,
            due_date=datetime.now(timezone.utc) + timedelta(days=policy.remediation_deadline_days),
            status=RemediationStatus.IN_PROGRESS,
        )

        self._remediation_queue.append(action)

        # Execute auto-remediation action if defined
        if policy.auto_remediation_action:
            # This would integrate with actual remediation systems
            pass

    async def _safe_callback(
        self,
        callback: Callable,
        violation: PolicyViolation,
    ):
        """Safely execute violation callback"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(violation)
            else:
                callback(violation)
        except Exception:
            pass  # Don't let callback errors affect enforcement

    def create_remediation(
        self,
        violation_id: str,
        title: str,
        description: str,
        action_type: str = "technical",
        due_date: Optional[datetime] = None,
        assigned_to: Optional[str] = None,
    ) -> RemediationAction:
        """Create a remediation action for a violation"""
        violation = self._active_violations.get(violation_id)
        if not violation:
            raise ValueError(f"Violation {violation_id} not found")

        policy = self._policies.get(violation.policy_id)
        deadline_days = policy.remediation_deadline_days if policy else 30

        action = RemediationAction(
            violation_id=violation_id,
            title=title,
            description=description,
            action_type=action_type,
            due_date=due_date or datetime.now(timezone.utc) + timedelta(days=deadline_days),
            assigned_to=assigned_to,
        )

        self._remediation_queue.append(action)
        return action

    def grant_exemption(
        self,
        model_id: str,
        policy_id: str,
        reason: str,
        approved_by: str,
        expires_at: Optional[datetime] = None,
    ) -> bool:
        """Grant exemption for a policy"""
        if policy_id not in self._policies:
            return False

        policy = self._policies[policy_id]
        if policy.policy_type != PolicyType.EXEMPTABLE:
            return False

        exemption_key = f"{model_id}:{policy_id}"
        self._exemptions[exemption_key] = {
            "reason": reason,
            "approved_by": approved_by,
            "approved_at": datetime.now(timezone.utc),
            "expires_at": expires_at,
        }

        return True

    def get_active_violations(
        self,
        model_id: Optional[str] = None,
        regulation: Optional[RegulationType] = None,
        severity: Optional[ViolationSeverity] = None,
    ) -> List[PolicyViolation]:
        """Get active violations with optional filtering"""
        violations = list(self._active_violations.values())

        if model_id:
            violations = [v for v in violations if model_id in v.affected_systems]

        if regulation:
            violations = [v for v in violations if v.regulation == regulation]

        if severity:
            violations = [v for v in violations if v.severity == severity]

        return violations

    def acknowledge_violation(
        self,
        violation_id: str,
        acknowledged_by: str,
    ) -> bool:
        """Acknowledge a violation"""
        if violation_id not in self._active_violations:
            return False

        violation = self._active_violations[violation_id]
        violation.status = "acknowledged"
        violation.acknowledged_at = datetime.now(timezone.utc)
        violation.acknowledged_by = acknowledged_by

        return True

    def resolve_violation(
        self,
        violation_id: str,
        resolved_by: str,
        resolution_notes: Optional[str] = None,
    ) -> bool:
        """Mark a violation as resolved"""
        if violation_id not in self._active_violations:
            return False

        violation = self._active_violations[violation_id]
        violation.status = "resolved"
        violation.resolved_at = datetime.now(timezone.utc)
        violation.resolved_by = resolved_by

        return True

    def get_compliance_summary(
        self,
        model_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get compliance summary statistics"""
        violations = self.get_active_violations(model_id=model_id)

        return {
            "total_violations": len(violations),
            "by_severity": {
                "critical": len([v for v in violations if v.severity == ViolationSeverity.CRITICAL]),
                "high": len([v for v in violations if v.severity == ViolationSeverity.HIGH]),
                "medium": len([v for v in violations if v.severity == ViolationSeverity.MEDIUM]),
                "low": len([v for v in violations if v.severity == ViolationSeverity.LOW]),
            },
            "by_regulation": {reg.value: len([v for v in violations if v.regulation == reg]) for reg in RegulationType},
            "by_status": {
                "open": len([v for v in violations if v.status == "open"]),
                "acknowledged": len([v for v in violations if v.status == "acknowledged"]),
                "in_remediation": len([v for v in violations if v.status == "in_remediation"]),
            },
            "overdue_count": len([v for v in violations if v.is_overdue]),
            "total_potential_fines": sum(v.potential_fine or 0 for v in violations),
            "pending_remediations": len(self._remediation_queue),
        }

    # =========================================================================
    # AI-Enhanced Analysis Methods
    # =========================================================================

    async def enhance_violation_with_ai(
        self,
        violation: PolicyViolation,
        model: AIModelRegistration,
    ) -> Tuple[PolicyViolation, Dict[str, Any]]:
        """
        Enhance a violation with AI-generated explanation and analysis.

        Uses the configured ComplianceAIAnalyzer to generate detailed
        explanations of the violation's significance, business impact,
        and suggested remediation actions.

        Args:
            violation: PolicyViolation to enhance
            model: AIModelRegistration associated with the violation

        Returns:
            Tuple containing:
                - PolicyViolation with updated description (if AI analysis succeeded)
                - Dict with full AI analysis including:
                    - significance: str
                    - business_impact: str
                    - remediation_priority: str
                    - suggested_actions: List[str]

        Raises:
            ValueError: If ai_analyzer is not configured or AI analysis is disabled

        Example:
            >>> enforcer = PolicyEnforcer(
            ...     ai_analyzer=ComplianceAIAnalyzer(),
            ...     enable_ai_analysis=True
            ... )
            >>> enhanced_violation, ai_analysis = await enforcer.enhance_violation_with_ai(
            ...     violation, model
            ... )
            >>> print(ai_analysis["significance"])
        """
        if not self.ai_analyzer:
            raise ValueError(
                "AI analyzer not configured. Initialize PolicyEnforcer with "
                "ai_analyzer parameter to use AI-enhanced analysis."
            )

        if not self.enable_ai_analysis:
            raise ValueError(
                "AI analysis is disabled. Set enable_ai_analysis=True to use AI-enhanced violation analysis."
            )

        # Get AI explanation for the violation
        ai_analysis = await self.ai_analyzer.explain_violation(violation, model)

        # Update violation description with AI-enhanced explanation
        original_description = violation.description
        enhanced_description = (
            f"{original_description}\n\n"
            f"[AI Analysis]\n"
            f"Significance: {ai_analysis.get('significance', 'N/A')}\n"
            f"Business Impact: {ai_analysis.get('business_impact', 'N/A')}\n"
            f"Remediation Priority: {ai_analysis.get('remediation_priority', 'N/A')}"
        )

        # Create updated violation with enhanced description
        # Note: PolicyViolation is a Pydantic model, so we copy and update
        violation_dict = violation.model_dump()
        violation_dict["description"] = enhanced_description
        enhanced_violation = PolicyViolation(**violation_dict)

        return enhanced_violation, ai_analysis

    async def generate_ai_remediation_roadmap(
        self,
        violations: List[PolicyViolation],
        model: AIModelRegistration,
    ) -> Dict[str, Any]:
        """
        Generate an AI-powered remediation roadmap for multiple violations.

        Uses the configured ComplianceAIAnalyzer to create a comprehensive,
        prioritized remediation plan with timeline estimates and quick wins.

        Args:
            violations: List of PolicyViolation instances to remediate
            model: AIModelRegistration context for the remediation

        Returns:
            Dict containing:
                - prioritized_actions: List of prioritized remediation actions
                  with title, priority (1-5), category, and estimated_hours
                - timeline: str - Suggested overall timeline
                - resource_estimates: Dict with team, hours, and cost estimates
                - quick_wins: List[str] - Actions achievable in <1 day

        Raises:
            ValueError: If ai_analyzer is not configured or AI analysis is disabled

        Example:
            >>> roadmap = await enforcer.generate_ai_remediation_roadmap(
            ...     violations, model
            ... )
            >>> print(roadmap["quick_wins"])
            ["Update privacy policy", "Enable audit logging"]
        """
        if not self.ai_analyzer:
            raise ValueError(
                "AI analyzer not configured. Initialize PolicyEnforcer with "
                "ai_analyzer parameter to generate AI remediation roadmaps."
            )

        if not self.enable_ai_analysis:
            raise ValueError(
                "AI analysis is disabled. Set enable_ai_analysis=True to use AI-generated remediation roadmaps."
            )

        if not violations:
            return {
                "prioritized_actions": [],
                "timeline": "No remediation needed",
                "resource_estimates": {},
                "quick_wins": [],
            }

        # Generate AI-powered remediation roadmap
        roadmap = await self.ai_analyzer.generate_remediation_roadmap(violations, model)

        return roadmap

    def suggest_remediation(
        self,
        violation: PolicyViolation,
    ) -> Dict[str, Any]:
        """
        Suggest remediation actions for a violation.

        When enable_ai_analysis=True and ai_analyzer is configured,
        this method can be enhanced with AI-generated recommendations
        via enhance_violation_with_ai(). Otherwise, uses template-based
        suggestions from policy definitions.

        Args:
            violation: PolicyViolation to get remediation suggestions for

        Returns:
            Dict containing:
                - guidance: str - Remediation guidance text
                - deadline_days: int - Recommended deadline in days
                - auto_remediation_available: bool - Whether auto-remediation exists
                - priority: str - Priority level based on severity
                - ai_enhanced: bool - Whether AI enhancement is available

        Example:
            >>> suggestion = enforcer.suggest_remediation(violation)
            >>> print(suggestion["guidance"])
            "Implement comprehensive risk management..."
        """
        policy = self._policies.get(violation.policy_id)

        if not policy:
            return {
                "guidance": f"Review and address violation: {violation.title}",
                "deadline_days": 30,
                "auto_remediation_available": False,
                "priority": violation.severity.value,
                "ai_enhanced": False,
            }

        # Determine priority from severity
        priority_map = {
            ViolationSeverity.CRITICAL: "immediate",
            ViolationSeverity.HIGH: "urgent",
            ViolationSeverity.MEDIUM: "standard",
            ViolationSeverity.LOW: "low",
            ViolationSeverity.INFORMATIONAL: "informational",
        }

        return {
            "guidance": policy.remediation_guidance,
            "deadline_days": policy.remediation_deadline_days,
            "auto_remediation_available": policy.auto_remediation_available,
            "auto_remediation_action": policy.auto_remediation_action,
            "priority": priority_map.get(violation.severity, "standard"),
            "ai_enhanced": self.enable_ai_analysis and self.ai_analyzer is not None,
        }
