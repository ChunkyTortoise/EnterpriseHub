"""
Enterprise Compliance Platform - Core Data Models

Production-ready Pydantic models for compliance management across
EU AI Act, SEC regulations, and HIPAA requirements.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ComplianceStatus(str, Enum):
    """Overall compliance status levels"""

    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    UNDER_REVIEW = "under_review"
    PENDING_CERTIFICATION = "pending_certification"
    EXEMPTED = "exempted"


class RiskLevel(str, Enum):
    """EU AI Act risk classification levels"""

    UNACCEPTABLE = "unacceptable"  # Banned under EU AI Act
    HIGH = "high"  # Strict requirements
    LIMITED = "limited"  # Transparency obligations
    MINIMAL = "minimal"  # No specific requirements
    UNKNOWN = "unknown"  # Needs assessment


class RegulationType(str, Enum):
    """Supported regulatory frameworks"""

    EU_AI_ACT = "eu_ai_act"
    SEC_AI_GUIDANCE = "sec_ai_guidance"
    HIPAA = "hipaa"
    GDPR = "gdpr"
    SOC2 = "soc2"
    ISO_27001 = "iso_27001"
    NIST_AI_RMF = "nist_ai_rmf"
    CCPA = "ccpa"
    SOX = "sox"
    ISO_42001 = "iso_42001"
    NYC_AEDT = "nyc_aedt"
    COLORADO_AI_ACT = "colorado_ai_act"


class ViolationSeverity(str, Enum):
    """Severity levels for compliance violations"""

    CRITICAL = "critical"  # Immediate action required, potential legal exposure
    HIGH = "high"  # Action required within 24 hours
    MEDIUM = "medium"  # Action required within 7 days
    LOW = "low"  # Action required within 30 days
    INFORMATIONAL = "informational"  # For awareness only


class RemediationStatus(str, Enum):
    """Status of remediation actions"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"
    FAILED = "failed"
    ESCALATED = "escalated"


class ComplianceScore(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "overall_score": 85.5,
                "regulation_scores": {"eu_ai_act": 90.0, "gdpr": 82.5},
                "category_scores": {"privacy": 88.0, "fairness": 92.0},
                "trend": "improving",
                "trend_percentage": 5.2,
                "last_assessed": "2026-01-21T12:00:00Z",
                "assessor": "automated_v1",
            }
        },
    )
    """Quantified compliance score with breakdown"""
    overall_score: float = Field(..., ge=0, le=100, description="Overall compliance percentage")
    regulation_scores: Dict[str, float] = Field(default_factory=dict)
    category_scores: Dict[str, float] = Field(default_factory=dict)
    trend: str = Field(default="stable", description="improving, stable, declining")
    trend_percentage: float = Field(default=0.0)
    last_assessed: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    assessor: str = Field(default="automated")
    confidence_level: float = Field(default=0.95, ge=0, le=1)

    @property
    def grade(self) -> str:
        """Letter grade for compliance score"""
        if self.overall_score >= 95:
            return "A+"
        elif self.overall_score >= 90:
            return "A"
        elif self.overall_score >= 85:
            return "B+"
        elif self.overall_score >= 80:
            return "B"
        elif self.overall_score >= 75:
            return "C+"
        elif self.overall_score >= 70:
            return "C"
        elif self.overall_score >= 60:
            return "D"
        return "F"


class RiskAssessment(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "model_id": "mod_12345",
                "model_name": "Proprietary LLM v2",
                "risk_level": "high",
                "risk_score": 45.0,
                "transparency_score": 60.0,
                "fairness_score": 75.0,
                "assessed_at": "2026-01-21T12:00:00Z",
                "risk_factors": ["Processing of sensitive financial data", "Limited explainability"],
                "recommendations": ["Implement human-in-the-loop validation", "Enhance data logging"],
            }
        },
    )
    """Comprehensive risk assessment for an AI model or system"""
    assessment_id: str = Field(default_factory=lambda: str(uuid4()))
    model_id: str
    model_name: str
    risk_level: RiskLevel
    risk_score: float = Field(..., ge=0, le=100)

    # Risk factors breakdown
    transparency_score: float = Field(default=0.0, ge=0, le=100)
    fairness_score: float = Field(default=0.0, ge=0, le=100)
    accountability_score: float = Field(default=0.0, ge=0, le=100)
    robustness_score: float = Field(default=0.0, ge=0, le=100)
    privacy_score: float = Field(default=0.0, ge=0, le=100)
    security_score: float = Field(default=0.0, ge=0, le=100)

    # Assessment metadata
    assessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    assessed_by: str = Field(default="ai_compliance_engine")
    methodology: str = Field(default="automated_assessment_v1")

    # Findings
    risk_factors: List[str] = Field(default_factory=list)
    mitigating_factors: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

    # Regulatory mapping
    applicable_regulations: List[RegulationType] = Field(default_factory=list)
    regulatory_requirements: Dict[str, List[str]] = Field(default_factory=dict)

    # AI-generated insights (optional, populated when enable_ai_explanations=True)
    ai_insights: Dict[str, Any] = Field(default_factory=dict)

    def to_executive_summary(self) -> Dict[str, Any]:
        """Generate executive summary for C-suite reporting"""
        return {
            "model": self.model_name,
            "risk_classification": self.risk_level.value.upper(),
            "overall_risk_score": f"{self.risk_score:.1f}/100",
            "key_concerns": self.risk_factors[:3],
            "priority_actions": self.recommendations[:3],
            "assessment_date": self.assessed_at.strftime("%Y-%m-%d"),
        }


class PolicyViolation(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "violation_id": "viol_67890",
                "regulation": "eu_ai_act",
                "severity": "critical",
                "title": "Unauthorized Personal Data Processing",
                "description": "Model processed biometric data without explicit user consent.",
                "detected_at": "2026-01-21T12:00:00Z",
                "status": "open",
                "potential_fine": 150000.0,
                "reputational_risk": "high",
            }
        },
    )
    """Detected policy or compliance violation"""
    violation_id: str = Field(default_factory=lambda: str(uuid4()))

    # What was violated
    regulation: RegulationType
    policy_id: str
    policy_name: str
    article_reference: Optional[str] = None

    # Violation details
    severity: ViolationSeverity
    title: str
    description: str
    evidence: List[str] = Field(default_factory=list)
    affected_systems: List[str] = Field(default_factory=list)
    affected_data_subjects: int = Field(default=0)

    # Detection
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    detected_by: str = Field(default="compliance_engine")
    detection_method: str = Field(default="automated_scan")

    # Status tracking
    status: str = Field(default="open")  # open, acknowledged, in_remediation, resolved, false_positive
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

    # Risk impact
    potential_fine: Optional[float] = None
    potential_fine_currency: str = Field(default="EUR")
    reputational_risk: str = Field(default="medium")  # low, medium, high, critical

    @property
    def days_open(self) -> int:
        """Days since violation was detected"""
        if self.resolved_at:
            return (self.resolved_at - self.detected_at).days
        return (datetime.now(timezone.utc) - self.detected_at).days

    @property
    def is_overdue(self) -> bool:
        """Check if remediation is overdue based on severity"""
        sla_days = {
            ViolationSeverity.CRITICAL: 1,
            ViolationSeverity.HIGH: 3,
            ViolationSeverity.MEDIUM: 7,
            ViolationSeverity.LOW: 30,
            ViolationSeverity.INFORMATIONAL: 90,
        }
        return self.status == "open" and self.days_open > sla_days.get(self.severity, 30)


class RemediationAction(BaseModel):
    """Remediation action for a compliance violation"""

    action_id: str = Field(default_factory=lambda: str(uuid4()))
    violation_id: str

    # Action details
    title: str
    description: str
    action_type: str  # technical, procedural, documentation, training
    priority: int = Field(default=2, ge=1, le=5)  # 1 = highest

    # Assignment
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    department: Optional[str] = None

    # Timeline
    due_date: datetime
    estimated_hours: float = Field(default=0.0)
    actual_hours: Optional[float] = None

    # Status
    status: RemediationStatus = Field(default=RemediationStatus.PENDING)
    progress_percentage: int = Field(default=0, ge=0, le=100)

    # Completion
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = None
    verification_notes: Optional[str] = None

    # Evidence
    evidence_urls: List[str] = Field(default_factory=list)
    attachments: List[str] = Field(default_factory=list)


class AuditRecord(BaseModel):
    """Compliance audit trail record"""

    record_id: str = Field(default_factory=lambda: str(uuid4()))

    # Event classification
    event_type: str  # assessment, violation, remediation, certification, review
    event_subtype: Optional[str] = None

    # Context
    entity_type: str  # ai_model, policy, violation, user, system
    entity_id: str
    entity_name: Optional[str] = None

    # Event details
    action: str
    description: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Actor
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    actor_type: str = Field(default="system")  # system, user, integration
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Timestamp
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Compliance relevance
    regulation: Optional[RegulationType] = None
    compliance_impact: str = Field(default="none")  # none, low, medium, high


class AIModelRegistration(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "Market Predictor",
                "version": "1.4.2",
                "description": "Real estate market trend analysis engine",
                "model_type": "regression",
                "provider": "internal",
                "deployment_location": "cloud",
                "intended_use": "Predicting residential property price fluctuations",
                "applicable_regulations": ["gdpr", "eu_ai_act"],
                "personal_data_processed": True,
            }
        },
    )
    """AI Model registration for compliance tracking"""
    model_id: str = Field(default_factory=lambda: str(uuid4()))

    # Model identification
    name: str
    version: str
    description: str
    model_type: str  # classification, regression, nlp, computer_vision, etc.

    # Provider information
    provider: str  # internal, anthropic, openai, google, etc.
    deployment_location: str  # cloud, on_premise, hybrid
    data_residency: List[str] = Field(default_factory=list)  # eu, us, etc.

    # Use case classification
    intended_use: str
    prohibited_uses: List[str] = Field(default_factory=list)
    target_users: List[str] = Field(default_factory=list)

    # Risk classification
    risk_level: RiskLevel = Field(default=RiskLevel.UNKNOWN)
    use_case_category: str = Field(default="general")  # healthcare, finance, hr, etc.

    # Data handling
    training_data_description: Optional[str] = None
    personal_data_processed: bool = Field(default=False)
    sensitive_data_processed: bool = Field(default=False)
    data_retention_days: int = Field(default=90)

    # Technical details
    input_types: List[str] = Field(default_factory=list)
    output_types: List[str] = Field(default_factory=list)
    api_endpoints: List[str] = Field(default_factory=list)

    # Compliance status
    compliance_status: ComplianceStatus = Field(default=ComplianceStatus.UNDER_REVIEW)
    applicable_regulations: List[RegulationType] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)

    # Lifecycle
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    registered_by: str
    last_assessment: Optional[datetime] = None
    next_review_date: Optional[datetime] = None
    is_active: bool = Field(default=True)
    decommissioned_at: Optional[datetime] = None


class ComplianceCertification(BaseModel):
    """Compliance certification record"""

    certification_id: str = Field(default_factory=lambda: str(uuid4()))

    # Certification details
    regulation: RegulationType
    certification_name: str
    certification_body: str
    certificate_number: Optional[str] = None

    # Scope
    scope_description: str
    covered_models: List[str] = Field(default_factory=list)
    covered_systems: List[str] = Field(default_factory=list)

    # Validity
    issued_date: datetime
    expiry_date: datetime
    status: str = Field(default="active")  # active, expired, revoked, suspended

    # Assessment
    assessment_date: Optional[datetime] = None
    assessor: Optional[str] = None
    assessment_report_url: Optional[str] = None

    # Renewal
    renewal_reminder_days: int = Field(default=90)
    auto_renewal: bool = Field(default=False)

    @property
    def is_valid(self) -> bool:
        """Check if certification is currently valid"""
        return self.status == "active" and self.expiry_date > datetime.now(timezone.utc)

    @property
    def days_until_expiry(self) -> int:
        """Days until certification expires"""
        return (self.expiry_date - datetime.now(timezone.utc)).days


class ComplianceReport(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "report_id": "rep_55555",
                "report_type": "executive_summary",
                "title": "Quarterly Compliance Audit Q1 2026",
                "period_start": "2026-01-01T00:00:00Z",
                "period_end": "2026-03-31T23:59:59Z",
                "overall_status": "compliant",
                "models_assessed": 12,
                "violations_summary": {"critical": 0, "high": 2, "medium": 5},
                "key_findings": ["All high-risk models have undergone assessment", "Remediation time improved by 15%"],
            }
        },
    )
    """Comprehensive compliance report"""
    report_id: str = Field(default_factory=lambda: str(uuid4()))

    # Report metadata
    report_type: str  # executive_summary, detailed, audit, regulatory
    title: str
    description: Optional[str] = None

    # Time period
    period_start: datetime
    period_end: datetime
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    generated_by: str = Field(default="compliance_engine")

    # Compliance summary
    overall_score: ComplianceScore
    overall_status: ComplianceStatus

    # Breakdowns
    regulations_covered: List[RegulationType] = Field(default_factory=list)
    models_assessed: int = Field(default=0)
    violations_summary: Dict[str, int] = Field(default_factory=dict)  # severity -> count
    remediations_summary: Dict[str, int] = Field(default_factory=dict)  # status -> count

    # Detailed findings
    risk_assessments: List[RiskAssessment] = Field(default_factory=list)
    active_violations: List[PolicyViolation] = Field(default_factory=list)
    pending_remediations: List[RemediationAction] = Field(default_factory=list)
    certifications: List[ComplianceCertification] = Field(default_factory=list)

    # Recommendations
    executive_summary: str = Field(default="")
    key_findings: List[str] = Field(default_factory=list)
    priority_actions: List[str] = Field(default_factory=list)

    # Export
    format: str = Field(default="json")  # json, pdf, html
    export_url: Optional[str] = None
