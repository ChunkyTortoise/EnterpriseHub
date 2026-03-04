from __future__ import annotations

from typing import Protocol

from .schemas import (
    IntegrationBlueprint,
    ProofPack,
    ProofPackGenerationRequest,
    VerticalProfile,
)


class AdapterCapability(Protocol):
    vertical: VerticalProfile

    def validate_intake(self, goals: list[str], channels: list[str], event_volume_14d: int) -> tuple[int, list[str]]: ...

    def generate_blueprint(
        self,
        channels: list[str],
        triggers: list[str],
        crm_fields: list[str],
        escalation_rules: list[str],
    ) -> IntegrationBlueprint: ...

    def map_kpis(self, request: ProofPackGenerationRequest) -> tuple[dict[str, float], dict[str, float], list[str]]: ...

    def render_proof_pack(
        self,
        *,
        engagement_id: str,
        lookback_days: int,
        baseline_kpis: dict[str, float],
        current_kpis: dict[str, float],
        risks: list[str],
    ) -> ProofPack: ...


class _BaseAdapter:
    vertical: VerticalProfile

    def validate_intake(self, goals: list[str], channels: list[str], event_volume_14d: int) -> tuple[int, list[str]]:
        score = 55 + min(len(goals) * 10, 20) + min(len(channels) * 5, 15)
        risks: list[str] = []
        if event_volume_14d <= 0:
            risks.append("No event telemetry from the last 14 days.")
            score -= 20
        if not channels:
            risks.append("No delivery channels selected; defaults will be applied.")
            score -= 10
        return max(0, min(score, 100)), risks

    def _merge_defaults(self, incoming: list[str], defaults: list[str]) -> list[str]:
        if not incoming:
            return list(defaults)
        merged = list(dict.fromkeys(incoming + defaults))
        return merged

    def _delta(self, baseline_kpis: dict[str, float], current_kpis: dict[str, float]) -> dict[str, float]:
        deltas: dict[str, float] = {}
        keys = set(baseline_kpis.keys()) | set(current_kpis.keys())
        for key in keys:
            deltas[key] = current_kpis.get(key, 0.0) - baseline_kpis.get(key, 0.0)
        return deltas


class RealEstateAdapter(_BaseAdapter):
    vertical = VerticalProfile.real_estate

    def generate_blueprint(
        self,
        channels: list[str],
        triggers: list[str],
        crm_fields: list[str],
        escalation_rules: list[str],
    ) -> IntegrationBlueprint:
        return IntegrationBlueprint(
            triggers=self._merge_defaults(triggers, ["new_inbound_lead", "seller_intent_detected"]),
            channels=self._merge_defaults(channels, ["sms", "web_form"]),
            crm_fields=self._merge_defaults(crm_fields, ["lead_temperature", "bot_type", "response_sla_seconds"]),
            escalation_rules=self._merge_defaults(
                escalation_rules,
                [
                    "Escalate to human when lead score >= 90",
                    "Escalate when no response after 2 bot turns",
                ],
            ),
            automation_sequence=[
                "Capture lead intent",
                "Run qualification flow (Q0-Q4)",
                "Apply temperature tags and sync CRM",
                "Trigger follow-up workflow",
            ],
        )

    def map_kpis(self, request: ProofPackGenerationRequest) -> tuple[dict[str, float], dict[str, float], list[str]]:
        required = {"response_sla_seconds", "qualified_leads", "attributed_revenue"}
        if not required.issubset(request.current_kpis):
            missing = sorted(required - set(request.current_kpis))
            raise ValueError(f"Missing required real estate KPIs: {', '.join(missing)}")
        baseline = {k: request.baseline_kpis.get(k, 0.0) for k in required}
        current = {k: request.current_kpis.get(k, 0.0) for k in required}
        risks = list(request.missing_sources)
        if request.partial_telemetry:
            risks.append("Partial telemetry detected for some lead sources.")
        return baseline, current, risks

    def render_proof_pack(
        self,
        *,
        engagement_id: str,
        lookback_days: int,
        baseline_kpis: dict[str, float],
        current_kpis: dict[str, float],
        risks: list[str],
    ) -> ProofPack:
        delta = self._delta(baseline_kpis, current_kpis)
        baseline_sla = max(baseline_kpis.get("response_sla_seconds", 1.0), 1.0)
        current_sla = current_kpis.get("response_sla_seconds", 0.0)
        sla_adherence = round(max(0.0, 1.0 - (current_sla / baseline_sla)), 4)
        roi_estimate = round((delta.get("attributed_revenue", 0.0) / max(current_kpis.get("qualified_leads", 1.0), 1.0)), 2)
        return ProofPack(
            engagement_id=engagement_id,
            vertical_profile=self.vertical,
            lookback_days=lookback_days,
            baseline_kpis=baseline_kpis,
            current_kpis=current_kpis,
            delta_kpis=delta,
            sla_adherence=sla_adherence,
            roi_estimate=roi_estimate,
            executive_summary="Lead response and qualification automation improved pipeline velocity and attributable revenue.",
            risks=risks,
            recommendations=[
                "Increase hot-lead human callback window to under 3 minutes.",
                "Expand CRM tag automation to referral source segmentation.",
            ],
        )


class ProfessionalServicesAdapter(_BaseAdapter):
    vertical = VerticalProfile.professional_services

    def generate_blueprint(
        self,
        channels: list[str],
        triggers: list[str],
        crm_fields: list[str],
        escalation_rules: list[str],
    ) -> IntegrationBlueprint:
        return IntegrationBlueprint(
            triggers=self._merge_defaults(triggers, ["new_client_intake", "document_requires_review"]),
            channels=self._merge_defaults(channels, ["web_form", "email"]),
            crm_fields=self._merge_defaults(crm_fields, ["matter_type", "intake_status", "review_priority"]),
            escalation_rules=self._merge_defaults(
                escalation_rules,
                [
                    "Escalate to specialist when confidence < 0.75",
                    "Escalate when SLA breach risk exceeds 20%",
                ],
            ),
            automation_sequence=[
                "Capture structured intake",
                "Run document extraction and validation",
                "Queue for reviewer assignment",
                "Push status updates to CRM and client channel",
            ],
        )

    def map_kpis(self, request: ProofPackGenerationRequest) -> tuple[dict[str, float], dict[str, float], list[str]]:
        required = {"review_sla_hours", "throughput", "escalation_rate", "hours_saved"}
        if not required.issubset(request.current_kpis):
            missing = sorted(required - set(request.current_kpis))
            raise ValueError(f"Missing required professional services KPIs: {', '.join(missing)}")
        baseline = {k: request.baseline_kpis.get(k, 0.0) for k in required}
        current = {k: request.current_kpis.get(k, 0.0) for k in required}
        risks = list(request.missing_sources)
        if request.partial_telemetry:
            risks.append("Partial telemetry in intake queue metadata.")
        return baseline, current, risks

    def render_proof_pack(
        self,
        *,
        engagement_id: str,
        lookback_days: int,
        baseline_kpis: dict[str, float],
        current_kpis: dict[str, float],
        risks: list[str],
    ) -> ProofPack:
        delta = self._delta(baseline_kpis, current_kpis)
        baseline_sla = max(baseline_kpis.get("review_sla_hours", 1.0), 1.0)
        current_sla = current_kpis.get("review_sla_hours", 0.0)
        sla_adherence = round(max(0.0, 1.0 - (current_sla / baseline_sla)), 4)
        roi_estimate = round(delta.get("hours_saved", 0.0) * 125.0, 2)
        return ProofPack(
            engagement_id=engagement_id,
            vertical_profile=self.vertical,
            lookback_days=lookback_days,
            baseline_kpis=baseline_kpis,
            current_kpis=current_kpis,
            delta_kpis=delta,
            sla_adherence=sla_adherence,
            roi_estimate=roi_estimate,
            executive_summary="Intake and review automation reduced turnaround times and increased processed matters per week.",
            risks=risks,
            recommendations=[
                "Add reviewer claim queue balancing by specialization.",
                "Expand QA checks for high-risk matter categories.",
            ],
        )


class VoiceCSAdapter(_BaseAdapter):
    vertical = VerticalProfile.ecommerce_voice

    def generate_blueprint(
        self,
        channels: list[str],
        triggers: list[str],
        crm_fields: list[str],
        escalation_rules: list[str],
    ) -> IntegrationBlueprint:
        return IntegrationBlueprint(
            triggers=self._merge_defaults(triggers, ["inbound_call", "resolution_failure"]),
            channels=self._merge_defaults(channels, ["voice", "sms"]),
            crm_fields=self._merge_defaults(crm_fields, ["call_outcome", "fallback_reason", "agent_handoff"]),
            escalation_rules=self._merge_defaults(
                escalation_rules,
                [
                    "Escalate to live agent on sentiment drop below threshold",
                    "Escalate after 2 fallback responses",
                ],
            ),
            automation_sequence=[
                "Transcribe and classify intent",
                "Attempt first-contact resolution",
                "Fallback to handoff policy when confidence is low",
                "Sync transcript and disposition to CRM",
            ],
        )

    def map_kpis(self, request: ProofPackGenerationRequest) -> tuple[dict[str, float], dict[str, float], list[str]]:
        required = {"ttfb_ms", "resolution_rate", "fallback_rate"}
        if not required.issubset(request.current_kpis):
            missing = sorted(required - set(request.current_kpis))
            raise ValueError(f"Missing required voice KPIs: {', '.join(missing)}")
        baseline = {k: request.baseline_kpis.get(k, 0.0) for k in required}
        current = {k: request.current_kpis.get(k, 0.0) for k in required}
        risks = list(request.missing_sources)
        if request.partial_telemetry:
            risks.append("Partial telemetry in call analytics stream.")
        return baseline, current, risks

    def render_proof_pack(
        self,
        *,
        engagement_id: str,
        lookback_days: int,
        baseline_kpis: dict[str, float],
        current_kpis: dict[str, float],
        risks: list[str],
    ) -> ProofPack:
        delta = self._delta(baseline_kpis, current_kpis)
        baseline_ttfb = max(baseline_kpis.get("ttfb_ms", 1.0), 1.0)
        current_ttfb = current_kpis.get("ttfb_ms", 0.0)
        sla_adherence = round(max(0.0, 1.0 - (current_ttfb / baseline_ttfb)), 4)
        roi_estimate = round((delta.get("resolution_rate", 0.0) * 1000.0) - (delta.get("fallback_rate", 0.0) * 500.0), 2)
        return ProofPack(
            engagement_id=engagement_id,
            vertical_profile=self.vertical,
            lookback_days=lookback_days,
            baseline_kpis=baseline_kpis,
            current_kpis=current_kpis,
            delta_kpis=delta,
            sla_adherence=sla_adherence,
            roi_estimate=roi_estimate,
            executive_summary="Voice automation improved first-contact resolution while reducing fallback handoffs.",
            risks=risks,
            recommendations=[
                "Tune fallback prompts for top 3 unresolved intents.",
                "Add live-agent warm transfer for billing and refund intents.",
            ],
        )
