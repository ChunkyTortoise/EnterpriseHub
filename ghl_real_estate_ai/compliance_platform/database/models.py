from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from ..models.compliance_models import ComplianceStatus, RegulationType, RemediationStatus, RiskLevel, ViolationSeverity


class Base(DeclarativeBase):
    pass


class DBModelRegistration(Base):
    __tablename__ = "model_registrations"

    model_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    model_type: Mapped[str] = mapped_column(String, nullable=False)

    provider: Mapped[str] = mapped_column(String, nullable=False)
    deployment_location: Mapped[str] = mapped_column(String, nullable=False)
    data_residency: Mapped[List[str]] = mapped_column(JSON, default=list)

    intended_use: Mapped[str] = mapped_column(Text, nullable=False)
    prohibited_uses: Mapped[List[str]] = mapped_column(JSON, default=list)
    target_users: Mapped[List[str]] = mapped_column(JSON, default=list)

    risk_level: Mapped[RiskLevel] = mapped_column(SQLEnum(RiskLevel), default=RiskLevel.UNKNOWN)
    use_case_category: Mapped[str] = mapped_column(String, default="general")

    training_data_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    personal_data_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    sensitive_data_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    data_retention_days: Mapped[int] = mapped_column(Integer, default=90)

    input_types: Mapped[List[str]] = mapped_column(JSON, default=list)
    output_types: Mapped[List[str]] = mapped_column(JSON, default=list)
    api_endpoints: Mapped[List[str]] = mapped_column(JSON, default=list)

    compliance_status: Mapped[ComplianceStatus] = mapped_column(
        SQLEnum(ComplianceStatus), default=ComplianceStatus.UNDER_REVIEW
    )
    applicable_regulations: Mapped[List[RegulationType]] = mapped_column(
        JSON, default=list
    )  # Stored as list of strings

    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    registered_by: Mapped[str] = mapped_column(String, default="system")
    last_assessment: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_review_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    decommissioned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    assessments: Mapped[List["DBRiskAssessment"]] = relationship(back_populates="model", cascade="all, delete-orphan")
    violations: Mapped[List["DBPolicyViolation"]] = relationship(back_populates="model", cascade="all, delete-orphan")
    compliance_score: Mapped[Optional["DBComplianceScore"]] = relationship(
        back_populates="model", uselist=False, cascade="all, delete-orphan"
    )


class DBRiskAssessment(Base):
    __tablename__ = "risk_assessments"

    assessment_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    model_id: Mapped[str] = mapped_column(ForeignKey("model_registrations.model_id"))
    model_name: Mapped[str] = mapped_column(String)

    risk_level: Mapped[RiskLevel] = mapped_column(SQLEnum(RiskLevel))
    risk_score: Mapped[float] = mapped_column(Float)

    transparency_score: Mapped[float] = mapped_column(Float, default=0.0)
    fairness_score: Mapped[float] = mapped_column(Float, default=0.0)
    accountability_score: Mapped[float] = mapped_column(Float, default=0.0)
    robustness_score: Mapped[float] = mapped_column(Float, default=0.0)
    privacy_score: Mapped[float] = mapped_column(Float, default=0.0)
    security_score: Mapped[float] = mapped_column(Float, default=0.0)

    assessed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    assessed_by: Mapped[str] = mapped_column(String, default="ai_compliance_engine")
    methodology: Mapped[str] = mapped_column(String, default="automated_assessment_v1")

    risk_factors: Mapped[List[str]] = mapped_column(JSON, default=list)
    mitigating_factors: Mapped[List[str]] = mapped_column(JSON, default=list)
    recommendations: Mapped[List[str]] = mapped_column(JSON, default=list)

    applicable_regulations: Mapped[List[str]] = mapped_column(JSON, default=list)
    regulatory_requirements: Mapped[Dict[str, List[str]]] = mapped_column(JSON, default=dict)

    ai_insights: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    model: Mapped["DBModelRegistration"] = relationship(back_populates="assessments")


class DBPolicyViolation(Base):
    __tablename__ = "policy_violations"

    violation_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    model_id: Mapped[str] = mapped_column(
        ForeignKey("model_registrations.model_id")
    )  # Adding FK to model for easier queries

    regulation: Mapped[RegulationType] = mapped_column(SQLEnum(RegulationType))
    policy_id: Mapped[str] = mapped_column(String)
    policy_name: Mapped[str] = mapped_column(String)
    article_reference: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    severity: Mapped[ViolationSeverity] = mapped_column(SQLEnum(ViolationSeverity))
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    evidence: Mapped[List[str]] = mapped_column(JSON, default=list)
    affected_systems: Mapped[List[str]] = mapped_column(JSON, default=list)
    affected_data_subjects: Mapped[int] = mapped_column(Integer, default=0)

    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    detected_by: Mapped[str] = mapped_column(String, default="compliance_engine")
    detection_method: Mapped[str] = mapped_column(String, default="automated_scan")

    status: Mapped[str] = mapped_column(String, default="open")
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    potential_fine: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    potential_fine_currency: Mapped[str] = mapped_column(String, default="EUR")
    reputational_risk: Mapped[str] = mapped_column(String, default="medium")

    model: Mapped["DBModelRegistration"] = relationship(back_populates="violations")
    remediation_actions: Mapped[List["DBRemediationAction"]] = relationship(
        back_populates="violation", cascade="all, delete-orphan"
    )


class DBRemediationAction(Base):
    __tablename__ = "remediation_actions"

    action_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    violation_id: Mapped[str] = mapped_column(ForeignKey("policy_violations.violation_id"))

    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    action_type: Mapped[str] = mapped_column(String)
    priority: Mapped[int] = mapped_column(Integer, default=2)

    assigned_to: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    due_date: Mapped[datetime] = mapped_column(DateTime)
    estimated_hours: Mapped[float] = mapped_column(Float, default=0.0)
    actual_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    status: Mapped[RemediationStatus] = mapped_column(SQLEnum(RemediationStatus), default=RemediationStatus.PENDING)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0)

    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    evidence_urls: Mapped[List[str]] = mapped_column(JSON, default=list)
    attachments: Mapped[List[str]] = mapped_column(JSON, default=list)

    violation: Mapped["DBPolicyViolation"] = relationship(back_populates="remediation_actions")


class DBComplianceScore(Base):
    __tablename__ = "compliance_scores"

    model_id: Mapped[str] = mapped_column(ForeignKey("model_registrations.model_id"), primary_key=True)

    overall_score: Mapped[float] = mapped_column(Float)
    regulation_scores: Mapped[Dict[str, float]] = mapped_column(JSON, default=dict)
    category_scores: Mapped[Dict[str, float]] = mapped_column(JSON, default=dict)

    trend: Mapped[str] = mapped_column(String, default="stable")
    trend_percentage: Mapped[float] = mapped_column(Float, default=0.0)

    last_assessed: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    assessor: Mapped[str] = mapped_column(String, default="automated")
    confidence_level: Mapped[float] = mapped_column(Float, default=0.95)

    model: Mapped["DBModelRegistration"] = relationship(back_populates="compliance_score")


class DBAuditRecord(Base):
    __tablename__ = "audit_trail"

    record_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))

    event_type: Mapped[str] = mapped_column(String)
    event_subtype: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    entity_type: Mapped[str] = mapped_column(String)
    entity_id: Mapped[str] = mapped_column(String)
    entity_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    action: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)

    old_value: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    new_value: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    metadata_info: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict, name="metadata"
    )  # "metadata" is reserved in SQLAlchemy Base

    actor_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    actor_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    actor_type: Mapped[str] = mapped_column(String, default="system")
    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    regulation: Mapped[Optional[RegulationType]] = mapped_column(SQLEnum(RegulationType), nullable=True)
    compliance_impact: Mapped[str] = mapped_column(String, default="none")
