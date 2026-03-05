from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class VerticalProfile(str, Enum):
    real_estate = "real_estate"
    professional_services = "professional_services"
    ecommerce_voice = "ecommerce_voice"


class EngagementStatus(str, Enum):
    draft = "draft"
    active = "active"
    validating = "validating"
    delivered = "delivered"


class IntegrationBlueprint(BaseModel):
    triggers: list[str] = Field(default_factory=list)
    channels: list[str] = Field(default_factory=list)
    crm_fields: list[str] = Field(default_factory=list)
    escalation_rules: list[str] = Field(default_factory=list)
    automation_sequence: list[str] = Field(default_factory=list)


class ProofPack(BaseModel):
    engagement_id: str
    vertical_profile: VerticalProfile
    lookback_days: int
    baseline_kpis: dict[str, float]
    current_kpis: dict[str, float]
    delta_kpis: dict[str, float]
    sla_adherence: float
    roi_estimate: float
    executive_summary: str
    risks: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class AuditEvent(BaseModel):
    id: str
    engagement_id: str
    action: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    details: dict[str, Any] = Field(default_factory=dict)


class IntakeContext(BaseModel):
    channels: list[str] = Field(default_factory=list)
    crm_system: str | None = None
    event_volume_14d: int = Field(default=0, ge=0)
    metrics: dict[str, float] = Field(default_factory=dict)


class IntakeDiagnoseRequest(BaseModel):
    engagement_id: str | None = None
    vertical_profile: VerticalProfile
    client_name: str = Field(min_length=2)
    goals: list[str] = Field(min_length=1)
    context: IntakeContext = Field(default_factory=IntakeContext)


class IntakeDiagnosisResponse(BaseModel):
    engagement_id: str
    status: EngagementStatus
    vertical_profile: VerticalProfile
    readiness_score: int = Field(ge=0, le=100)
    risks: list[str] = Field(default_factory=list)
    recommended_template: str
    next_steps: list[str] = Field(default_factory=list)
    audit_id: str


class WorkflowBootstrapRequest(BaseModel):
    engagement_id: str
    vertical_profile: VerticalProfile | None = None
    delivery_window_days: int = Field(default=14, ge=7, le=30)
    channels: list[str] = Field(default_factory=list)
    triggers: list[str] = Field(default_factory=list)
    crm_fields: list[str] = Field(default_factory=list)
    escalation_rules: list[str] = Field(default_factory=list)


class WorkflowBootstrapResponse(BaseModel):
    engagement_id: str
    status: EngagementStatus
    vertical_profile: VerticalProfile
    blueprint: IntegrationBlueprint
    audit_id: str


class ProofPackGenerationRequest(BaseModel):
    engagement_id: str
    vertical_profile: VerticalProfile | None = None
    lookback_days: int = Field(default=14, ge=7, le=30)
    event_count: int = Field(default=0, ge=0)
    missing_sources: list[str] = Field(default_factory=list)
    partial_telemetry: bool = False
    baseline_kpis: dict[str, float] = Field(default_factory=dict)
    current_kpis: dict[str, float] = Field(default_factory=dict)


class ProofPackGenerationResponse(BaseModel):
    engagement_id: str
    status: EngagementStatus
    proof_pack: ProofPack
    audit_id: str


class ProofPackFetchResponse(BaseModel):
    engagement_id: str
    status: EngagementStatus
    proof_pack: ProofPack
    audit_trail: list[AuditEvent] = Field(default_factory=list)
