"""
Lead Pipeline Orchestrator

Coordinates demo-ready lead intake, qualification, lifecycle tracking, GHL sync,
appointment scheduling, follow-up enrollment, and real-time events.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ghl_real_estate_ai.core.conversation_manager import ConversationManager
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.auto_followup_sequences import AutoFollowUpSequences, TriggerType
from ghl_real_estate_ai.services.calendar_scheduler import CalendarScheduler
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.services.ghl_client import GHLClient
from ghl_real_estate_ai.services.lead_lifecycle import LeadLifecycleTracker
from ghl_real_estate_ai.services.lead_scorer import LeadScorer
from ghl_real_estate_ai.services.tenant_service import TenantService

logger = get_logger(__name__)


@dataclass
class LeadPipelineResult:
    """Simple result wrapper for pipeline actions."""
    success: bool
    message: str = ""
    metadata: Optional[Dict[str, Any]] = None


class LeadPipelineOrchestrator:
    """
    Orchestrates lead pipeline stages and downstream updates.
    """

    def __init__(self, conversation_manager: Optional[ConversationManager] = None):
        self.conversation_manager = conversation_manager or ConversationManager()
        self.lead_scorer = LeadScorer()
        self.calendar_scheduler = CalendarScheduler()
        self.followup_sequences = AutoFollowUpSequences()
        self.tenant_service = TenantService()
        self.event_publisher = get_event_publisher()
        self._lifecycle_trackers: Dict[str, LeadLifecycleTracker] = {}

    async def _get_tenant_ghl_client(self, location_id: str) -> GHLClient:
        tenant_config = await self.tenant_service.get_tenant_config(location_id)
        if tenant_config and tenant_config.get("ghl_api_key"):
            return GHLClient(api_key=tenant_config["ghl_api_key"], location_id=location_id)
        return GHLClient()

    def _get_lifecycle_tracker(self, location_id: str) -> LeadLifecycleTracker:
        if location_id not in self._lifecycle_trackers:
            self._lifecycle_trackers[location_id] = LeadLifecycleTracker(location_id)
        return self._lifecycle_trackers[location_id]

    async def process_new_lead(
        self,
        contact_id: str,
        location_id: str,
        source: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> LeadPipelineResult:
        """Start lifecycle tracking and emit initial events."""
        tracker = self._get_lifecycle_tracker(location_id)
        lead_name = "Lead"
        if context:
            lead_name = context.get("contact_name") or context.get("name") or lead_name

        journey_id = tracker.start_journey(
            contact_id=contact_id,
            contact_name=lead_name,
            source=source,
            initial_data=context or {},
        )

        ctx = context or {}
        ctx["journey_id"] = journey_id
        ctx.setdefault("pipeline_source", source)
        ctx.setdefault("ingested_at", datetime.utcnow().isoformat())
        await self.conversation_manager.memory_service.save_context(
            contact_id, ctx, location_id=location_id
        )

        await self.event_publisher.publish_lead_update(
            lead_id=contact_id,
            lead_data={
                "name": lead_name,
                "source": source,
                "lead_score": 0,
                "classification": "cold",
            },
            action="created",
            location_id=location_id,
        )

        await self.event_publisher.publish_lead_metric_update(
            lead_id=contact_id,
            metrics={
                "lead_score": 0,
                "classification": "cold",
                "stage": "new",
                "source": source,
            },
            location_id=location_id,
        )

        return LeadPipelineResult(success=True, message="Lead journey started", metadata={"journey_id": journey_id})

    async def update_qualification(
        self,
        contact_id: str,
        score: int,
        classification: str,
        extracted_preferences: Optional[Dict[str, Any]] = None,
        location_id: Optional[str] = None,
        predictive_score: Optional[Dict[str, Any]] = None,
    ) -> LeadPipelineResult:
        """Update lifecycle stage, sync GHL, enroll follow-up, and emit events."""
        if not location_id:
            location_id = settings.ghl_location_id

        tracker = self._get_lifecycle_tracker(location_id)
        context = await self.conversation_manager.get_context(contact_id, location_id=location_id)
        journey_id = context.get("journey_id")
        if not journey_id:
            journey_id = tracker.start_journey(contact_id, context.get("contact_name", "Lead"), source=context.get("pipeline_source", "unknown"))
            context["journey_id"] = journey_id

        now = datetime.utcnow().isoformat()
        if not context.get("first_response_at"):
            context["first_response_at"] = now
        if context.get("ingested_at") and not context.get("ttfr_seconds"):
            try:
                ingested_at = datetime.fromisoformat(context["ingested_at"]).replace(tzinfo=None)
                first_response_at = datetime.fromisoformat(context["first_response_at"]).replace(tzinfo=None)
                context["ttfr_seconds"] = max(0, int((first_response_at - ingested_at).total_seconds()))
            except Exception:
                context["ttfr_seconds"] = None

        context["lead_score"] = score
        context["lead_classification"] = classification
        context["lead_score_percent"] = self.lead_scorer.get_percentage_score(score)
        if extracted_preferences:
            context.setdefault("extracted_preferences", {}).update(extracted_preferences)
        if predictive_score:
            context["predictive_score"] = predictive_score

        await self.conversation_manager.memory_service.save_context(
            contact_id, context, location_id=location_id
        )

        # Lifecycle stage transitions
        target_stage = "contacted"
        if classification == "warm":
            target_stage = "qualified"
        elif classification == "hot":
            target_stage = "hot"

        stage_order = ["new", "contacted", "qualified", "hot", "appointment", "converted"]
        current_stage = tracker.journeys.get(journey_id, {}).get("current_stage", "new")

        if current_stage in stage_order and target_stage in stage_order:
            current_index = stage_order.index(current_stage)
            target_index = stage_order.index(target_stage)
            for stage in stage_order[current_index + 1: target_index + 1]:
                tracker.transition_stage(journey_id, stage, reason="qualification_update", lead_score=score)

        # GHL sync actions
        actions = []
        if score >= 2:
            actions.append({"type": "add_tag", "tag": "Status-Qualified"})
        if score >= 3:
            actions.append({"type": "add_tag", "tag": "Status-Hot"})

        percentage_score = self.lead_scorer.get_percentage_score(score)
        if settings.custom_field_lead_score:
            actions.append({
                "type": "update_custom_field",
                "field": settings.custom_field_lead_score,
                "value": percentage_score,
            })

        if actions:
            ghl_client = await self._get_tenant_ghl_client(location_id)
            from ghl_real_estate_ai.api.schemas.ghl import GHLAction, ActionType
            formatted_actions = []
            for action in actions:
                if action["type"] == "add_tag":
                    formatted_actions.append(GHLAction(type=ActionType.ADD_TAG, tag=action["tag"]))
                elif action["type"] == "update_custom_field":
                    formatted_actions.append(GHLAction(
                        type=ActionType.UPDATE_CUSTOM_FIELD,
                        field=action["field"],
                        value=action["value"],
                    ))
            if formatted_actions:
                await ghl_client.apply_actions(contact_id, formatted_actions)

        await self._enroll_followup(contact_id, classification, context)

        await self.event_publisher.publish_lead_update(
            lead_id=contact_id,
            lead_data={
                "lead_score": score,
                "classification": classification,
                "lead_score_percent": percentage_score,
            },
            action=classification if classification in ["hot", "warm"] else "contacted",
            location_id=location_id,
        )

        await self.event_publisher.publish_lead_metric_update(
            lead_id=contact_id,
            metrics={
                "lead_score": score,
                "classification": classification,
                "lead_score_percent": percentage_score,
                "stage": target_stage,
                "ttfr_seconds": context.get("ttfr_seconds"),
            },
            location_id=location_id,
        )

        if classification == "hot":
            await self.event_publisher.publish_system_alert(
                alert_type="hot_lead",
                message=f"Hot lead qualified: {contact_id}",
                severity="warning",
                details={"lead_score": score, "classification": classification},
            )

        return LeadPipelineResult(success=True, message="Qualification updated")

    async def offer_appointment(
        self,
        contact_id: str,
        score: int,
        calendar_id: Optional[str] = None,
        location_id: Optional[str] = None,
        extracted_preferences: Optional[Dict[str, Any]] = None,
        contact_info: Optional[Dict[str, Any]] = None,
        message_content: str = "",
    ) -> LeadPipelineResult:
        """Offer or auto-book appointments for qualified leads."""
        if not location_id:
            location_id = settings.ghl_location_id

        if score < settings.appointment_booking_threshold:
            return LeadPipelineResult(success=False, message="Lead score below booking threshold")

        if not contact_info:
            return LeadPipelineResult(success=False, message="Missing contact info for appointment booking")

        booking_attempted, booking_message, booking_actions = await self.calendar_scheduler.handle_appointment_request(
            contact_id=contact_id,
            contact_info=contact_info,
            lead_score=score,
            extracted_data=extracted_preferences or {},
            message_content=message_content,
        )

        if booking_attempted and booking_actions:
            ghl_client = await self._get_tenant_ghl_client(location_id)
            await ghl_client.apply_actions(contact_id, booking_actions)

        appointment_status = "attempted" if booking_attempted else "not_attempted"
        await self.event_publisher.publish_lead_metric_update(
            lead_id=contact_id,
            metrics={
                "appointment_status": appointment_status,
            },
            location_id=location_id,
        )

        return LeadPipelineResult(success=True, message=booking_message or "Appointment offer processed")

    async def record_appointment(
        self,
        contact_id: str,
        appointment_time: str,
        appointment_type: str,
        location_id: Optional[str] = None,
    ) -> LeadPipelineResult:
        """Record confirmed appointment and update lifecycle + GHL fields."""
        if not location_id:
            location_id = settings.ghl_location_id

        tracker = self._get_lifecycle_tracker(location_id)
        context = await self.conversation_manager.get_context(contact_id, location_id=location_id)
        journey_id = context.get("journey_id")
        if journey_id:
            tracker.transition_stage(journey_id, "appointment", reason="appointment_booked")

        context["appointment_time"] = appointment_time
        context["appointment_type"] = appointment_type
        await self.conversation_manager.memory_service.save_context(contact_id, context, location_id=location_id)

        actions = []
        from ghl_real_estate_ai.api.schemas.ghl import GHLAction, ActionType
        if settings.custom_field_appointment_time:
            actions.append(GHLAction(
                type=ActionType.UPDATE_CUSTOM_FIELD,
                field=settings.custom_field_appointment_time,
                value=appointment_time,
            ))
        if settings.custom_field_appointment_type:
            actions.append(GHLAction(
                type=ActionType.UPDATE_CUSTOM_FIELD,
                field=settings.custom_field_appointment_type,
                value=appointment_type,
            ))
        actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Appointment-Booked"))

        ghl_client = await self._get_tenant_ghl_client(location_id)
        await ghl_client.apply_actions(contact_id, actions)

        await self.event_publisher.publish_lead_metric_update(
            lead_id=contact_id,
            metrics={
                "appointment_status": "booked",
                "appointment_time": appointment_time,
                "appointment_type": appointment_type,
            },
            location_id=location_id,
        )

        return LeadPipelineResult(success=True, message="Appointment recorded")

    async def _enroll_followup(self, contact_id: str, classification: str, context: Dict[str, Any]) -> None:
        """Enroll contact in follow-up sequence based on classification."""
        if classification == "hot":
            sequence = self.followup_sequences.create_sequence(
                name="Hot Lead Rapid Response",
                trigger=TriggerType.NEW_LEAD,
                steps=[
                    {"channel": "sms", "delay_hours": 0.02, "content": "Hi {{first_name}}, Jorge here. I can help right away."},
                    {"channel": "call", "delay_hours": 1, "content": "Call task: hot lead follow-up."},
                ],
            )
        elif classification == "warm":
            sequence = self.followup_sequences.create_sequence(
                name="Warm Lead Follow-Up",
                trigger=TriggerType.NEW_LEAD,
                steps=[
                    {"channel": "sms", "delay_hours": 6, "content": "Quick check-in on your home search."},
                    {"channel": "email", "delay_hours": 24, "content": {"subject": "Next steps", "body": "Here are some options..."}},
                ],
            )
        else:
            sequence = self.followup_sequences.create_sequence(
                name="Cold Lead Nurture",
                trigger=TriggerType.NEW_LEAD,
                steps=[
                    {"channel": "sms", "delay_hours": 72, "content": "Just following up with some tips."},
                    {"channel": "email", "delay_hours": 168, "content": {"subject": "Market update", "body": "Sharing recent trends."}},
                    {"channel": "email", "delay_hours": 720, "content": {"subject": "Still interested?", "body": "Happy to help anytime."}},
                ],
            )

        contact_data = {
            "first_name": context.get("first_name") or "there",
            "last_name": context.get("last_name") or "",
            "email": context.get("email"),
            "phone": context.get("phone"),
        }
        self.followup_sequences.enroll_contact(sequence["id"], contact_id, contact_data)
