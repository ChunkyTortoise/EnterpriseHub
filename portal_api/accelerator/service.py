from __future__ import annotations

from functools import lru_cache
from uuid import uuid4

from .adapters import AdapterCapability, ProfessionalServicesAdapter, RealEstateAdapter, VoiceCSAdapter
from .repository import AcceleratorRepository
from .schemas import (
    EngagementStatus,
    IntakeDiagnoseRequest,
    IntakeDiagnosisResponse,
    ProofPackFetchResponse,
    ProofPackGenerationRequest,
    ProofPackGenerationResponse,
    VerticalProfile,
    WorkflowBootstrapRequest,
    WorkflowBootstrapResponse,
)


class AcceleratorNotFoundError(Exception):
    pass


class AcceleratorValidationError(Exception):
    pass


class AcceleratorService:
    def __init__(self, repository: AcceleratorRepository | None = None) -> None:
        self.repository = repository or AcceleratorRepository()
        self._adapters: dict[VerticalProfile, AdapterCapability] = {
            VerticalProfile.real_estate: RealEstateAdapter(),
            VerticalProfile.professional_services: ProfessionalServicesAdapter(),
            VerticalProfile.ecommerce_voice: VoiceCSAdapter(),
        }

    def _adapter_for(self, vertical_profile: VerticalProfile) -> AdapterCapability:
        return self._adapters[vertical_profile]

    def diagnose(self, request: IntakeDiagnoseRequest) -> IntakeDiagnosisResponse:
        engagement_id = request.engagement_id or str(uuid4())
        adapter = self._adapter_for(request.vertical_profile)
        readiness_score, risks = adapter.validate_intake(
            goals=request.goals,
            channels=request.context.channels,
            event_volume_14d=request.context.event_volume_14d,
        )

        self.repository.create_or_update_engagement(
            engagement_id=engagement_id,
            vertical_profile=request.vertical_profile,
            client_name=request.client_name,
            status=EngagementStatus.draft,
        )
        audit = self.repository.append_audit_event(
            engagement_id=engagement_id,
            action="intake_diagnosed",
            details={"vertical_profile": request.vertical_profile, "readiness_score": readiness_score},
        )

        return IntakeDiagnosisResponse(
            engagement_id=engagement_id,
            status=EngagementStatus.draft,
            vertical_profile=request.vertical_profile,
            readiness_score=readiness_score,
            risks=risks,
            recommended_template=f"{request.vertical_profile.value}_integration_sprint",
            next_steps=[
                "Confirm automation channels and CRM field mapping.",
                "Bootstrap workflow and validate KPI instrumentation.",
                "Generate baseline proof pack for a 14-day window.",
            ],
            audit_id=audit.id,
        )

    def bootstrap(self, request: WorkflowBootstrapRequest) -> WorkflowBootstrapResponse:
        existing = self.repository.get_engagement(request.engagement_id)
        if not existing:
            raise AcceleratorNotFoundError(f"Engagement '{request.engagement_id}' was not found.")
        vertical_profile = request.vertical_profile or existing["vertical_profile"]
        adapter = self._adapter_for(vertical_profile)

        blueprint = adapter.generate_blueprint(
            channels=request.channels,
            triggers=request.triggers,
            crm_fields=request.crm_fields,
            escalation_rules=request.escalation_rules,
        )

        self.repository.create_or_update_engagement(
            engagement_id=request.engagement_id,
            vertical_profile=vertical_profile,
            client_name=existing["client_name"],
            status=EngagementStatus.active,
        )
        audit = self.repository.append_audit_event(
            engagement_id=request.engagement_id,
            action="workflow_bootstrapped",
            details={"delivery_window_days": request.delivery_window_days, "vertical_profile": vertical_profile},
        )
        return WorkflowBootstrapResponse(
            engagement_id=request.engagement_id,
            status=EngagementStatus.active,
            vertical_profile=vertical_profile,
            blueprint=blueprint,
            audit_id=audit.id,
        )

    def generate_proof_pack(self, request: ProofPackGenerationRequest) -> ProofPackGenerationResponse:
        existing = self.repository.get_engagement(request.engagement_id)
        if not existing:
            raise AcceleratorNotFoundError(f"Engagement '{request.engagement_id}' was not found.")
        if request.event_count <= 0:
            raise AcceleratorValidationError("event_count must be greater than zero for proof-pack generation.")
        if request.missing_sources:
            raise AcceleratorValidationError(f"Missing KPI source(s): {', '.join(sorted(request.missing_sources))}")
        vertical_profile = request.vertical_profile or existing["vertical_profile"]
        adapter = self._adapter_for(vertical_profile)

        baseline_kpis, current_kpis, risks = adapter.map_kpis(request)
        proof_pack = adapter.render_proof_pack(
            engagement_id=request.engagement_id,
            lookback_days=request.lookback_days,
            baseline_kpis=baseline_kpis,
            current_kpis=current_kpis,
            risks=risks,
        )

        persisted_pack, reused = self.repository.save_report_idempotent(
            request.engagement_id,
            payload=request.model_dump(mode="json", exclude_none=True),
            proof_pack=proof_pack,
        )
        status = EngagementStatus.delivered
        self.repository.create_or_update_engagement(
            engagement_id=request.engagement_id,
            vertical_profile=vertical_profile,
            client_name=existing["client_name"],
            status=status,
        )
        audit = self.repository.append_audit_event(
            engagement_id=request.engagement_id,
            action="proof_pack_generated",
            details={"vertical_profile": vertical_profile, "idempotent_reuse": reused},
        )

        return ProofPackGenerationResponse(
            engagement_id=request.engagement_id,
            status=status,
            proof_pack=persisted_pack,
            audit_id=audit.id,
        )

    def get_proof_pack(self, engagement_id: str) -> ProofPackFetchResponse:
        engagement = self.repository.get_engagement(engagement_id)
        if not engagement:
            raise AcceleratorNotFoundError(f"Engagement '{engagement_id}' was not found.")
        proof_pack = self.repository.get_report(engagement_id)
        if not proof_pack:
            raise AcceleratorNotFoundError(f"No proof pack has been generated for engagement '{engagement_id}'.")
        audit_trail = self.repository.list_audit_events(engagement_id)
        return ProofPackFetchResponse(
            engagement_id=engagement_id,
            status=engagement["status"],
            proof_pack=proof_pack,
            audit_trail=audit_trail,
        )


@lru_cache(maxsize=1)
def get_accelerator_service() -> AcceleratorService:
    return AcceleratorService()
