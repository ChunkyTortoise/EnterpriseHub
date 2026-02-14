"""
Claude Journey Orchestrator - Autonomous Lead Journey Management
Uses Claude AI to design, predict, and optimize personalized lead paths.
Now featuring a Functional Dispatcher and Autonomous Journey Triggers.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.services.claude_orchestrator import ClaudeRequest, ClaudeTaskType, get_claude_orchestrator
from ghl_real_estate_ai.services.ghl_sync_service import get_ghl_sync_service
from ghl_real_estate_ai.services.lead_lifecycle import LeadLifecycleTracker
from ghl_real_estate_ai.services.memory_service import MemoryService

logger = logging.getLogger(__name__)


@dataclass
class JourneyTouchpoint:
    """A specific interaction point in a lead journey."""

    step_number: int
    channel: str  # sms, email, call, portal
    timing: str  # e.g., "Immediate", "Day 2", "Week 1"
    purpose: str
    content_draft: str
    expected_outcome: str
    conversion_signal: str


@dataclass
class PersonalizedJourney:
    """A complete journey plan for a specific lead."""

    journey_id: str
    lead_id: str
    persona_type: str
    journey_strategy: str
    estimated_conversion_days: int
    confidence_score: float
    touchpoints: List[JourneyTouchpoint]
    dynamic_triggers: List[Dict[str, str]]
    next_best_action: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


class ClaudeJourneyOrchestrator:
    """
    Orchestrates the autonomous lead journey using Claude AI reasoning.
    """

    def __init__(self, claude_orchestrator: Optional[Any] = None, memory_service: Optional[MemoryService] = None):
        self.claude = claude_orchestrator or get_claude_orchestrator()
        self.memory = memory_service or MemoryService()
        self.lifecycle = LeadLifecycleTracker(location_id="demo_location")
        self.ghl_sync = get_ghl_sync_service()
        self.analytics = AnalyticsService()

    async def design_personalized_journey(self, lead_id: str, lead_profile: Dict[str, Any]) -> PersonalizedJourney:
        """
        Designs a custom sales journey path for a specific lead using Claude.
        """
        location_id = lead_profile.get("location_id", "unknown")
        await self.memory.get_context(lead_id)

        prompt = f"""
        As an Elite Real Estate Journey Strategist, design a personalized 30-day journey for this lead.
        
        LEAD PROFILE:
        {json.dumps(lead_profile, indent=2)}
        
        GOAL: Move the lead from their current stage to 'Appointment' or 'Closing'.
        
        Provide a structured journey in JSON format.
        """

        try:
            request = ClaudeRequest(
                task_type=ClaudeTaskType.CHAT_QUERY,
                context={"lead_id": lead_id, "task": "journey_design"},
                prompt=prompt,
                temperature=0.7,
            )

            response = await self.claude.process_request(request)
            data = self._parse_json_response(response.content)

            # Record usage
            await self.analytics.track_llm_usage(
                location_id=location_id,
                model=response.model or "claude-3-5-sonnet",
                provider=response.provider or "claude",
                input_tokens=response.input_tokens or 0,
                output_tokens=response.output_tokens or 0,
                cached=False,
                contact_id=lead_id,
            )

            touchpoints = [JourneyTouchpoint(**tp) for tp in data.get("touchpoints", [])]

            return PersonalizedJourney(
                journey_id=f"journey_{lead_id}_{int(datetime.now().timestamp())}",
                lead_id=lead_id,
                persona_type=data.get("persona_type", "Standard Lead"),
                journey_strategy=data.get("journey_strategy", "Nurture and qualify"),
                estimated_conversion_days=data.get("estimated_conversion_days", 45),
                confidence_score=response.confidence or 0.85,
                touchpoints=touchpoints,
                dynamic_triggers=data.get("dynamic_triggers", []),
                next_best_action=data.get("next_best_action", "Initial follow-up"),
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
            )
        except Exception as e:
            logger.error(f"Error designing journey: {e}")
            return self._get_fallback_journey(lead_id, lead_profile)

    async def monitor_and_dispatch(self, lead_id: str, lead_name: str, current_state: Dict[str, Any]):
        """
        Functional Dispatcher: Monitors lead state and triggers autonomous actions.
        """
        closing_readiness = current_state.get("closing_readiness", 0)
        logger.info(f"Monitoring journey for {lead_name} (Readiness: {closing_readiness:.2f})")

        # AUTONOMOUS TRIGGER: Priority Human Handoff
        if closing_readiness >= 0.85:
            await self.execute_priority_handoff(lead_id, lead_name, closing_readiness, current_state)
            return {"action": "priority_handoff", "status": "executed"}

        # AUTONOMOUS TRIGGER: Re-engagement for silent leads
        last_contact = current_state.get("last_interaction_at")
        if last_contact:
            last_dt = datetime.fromisoformat(last_contact.replace("Z", "+00:00"))
            hours_silent = (datetime.utcnow() - last_dt).total_seconds() / 3600

            if hours_silent >= 24:
                from ghl_real_estate_ai.services.reengagement_engine import ReengagementEngine

                reengagement = ReengagementEngine(ghl_client=self.ghl_sync.ghl_client, memory_service=self.memory)

                logger.info(f"Triggering autonomous re-engagement for {lead_name} ({hours_silent:.1f}h silent)")
                result = await reengagement.send_reengagement_message(lead_id, lead_name, current_state)

                if result:
                    return {"action": "reengagement", "status": "executed", "trigger": f"{int(hours_silent)}h"}

        # AUTONOMOUS TRIGGER: Content Pulse for stalled leads
        current_stage = current_state.get("conversation_stage", "unknown")
        # In a real app, we'd get the actual time in stage from LeadLifecycleTracker
        # For now, we use updated_at as a proxy if time_in_stage not found
        last_update = current_state.get("updated_at")
        if last_update:
            update_dt = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
            hours_stalled = (datetime.utcnow() - update_dt).total_seconds() / 3600

            if hours_stalled >= 48:
                from ghl_real_estate_ai.services.ai_content_personalization import AIContentPersonalizationService

                content_service = AIContentPersonalizationService()

                logger.info(
                    f"Triggering autonomous Content Pulse for {lead_name} (stalled in {current_stage} for {hours_stalled:.1f}h)"
                )

                # Generate personalized content
                message = content_service.generate_personalized_content(
                    lead_name=lead_name,
                    channel="SMS",
                    tone="Helpful",
                    context={**current_state, "task": "content_pulse", "stalled_stage": current_stage},
                )

                if message:
                    await self.ghl_sync.ghl_client.send_message(contact_id=lead_id, message=message, channel="SMS")
                    return {"action": "content_pulse", "status": "executed", "stage": current_stage}

        return {"status": "monitoring"}

    async def execute_priority_handoff(self, lead_id: str, lead_name: str, score: float, context: Dict[str, Any]):
        """
        Triggers a 'Priority Human Handoff' webhook to Jorge with Mission Dossier.
        """
        logger.warning(f"🚨 EXECUTING PRIORITY HANDOFF FOR {lead_name} (Ready: {score:.0%})")

        # 1. Sync final DNA to GHL
        await self.ghl_sync.sync_dna_to_ghl(lead_id, context)

        # 2. Trigger Priority Webhook (via GHL Sync Service Handoff Trigger)
        await self.ghl_sync.trigger_high_readiness_handoff(lead_id, lead_name, score)

        # 3. Store Handoff Mission Dossier in memory for the mobile app to pick up
        mission_dossier = {
            "lead_name": lead_name,
            "readiness_score": score,
            "top_3_psych_triggers": context.get("top_triggers", ["Investment ROI", "Family Safety", "Privacy"]),
            "suggested_opening_line": f"Hi {lead_name.split(' ')[0]}, I've just finalized the research on those Teravista properties you were analyzing...",
            "deal_killer_alerts": context.get("deal_killers", ["Competitor checking Manor area"]),
            "timestamp": datetime.now().isoformat(),
        }
        await self.memory.store_conversation_memory(f"mission_dossier_{lead_id}", mission_dossier)

        logger.info(f"✅ Mission Dossier for {lead_name} prepared and dispatched.")

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except (json.JSONDecodeError, TypeError, IndexError) as e:
            logger.debug(f"Failed to parse Claude JSON response: {e}")
            return {}

    def _get_fallback_journey(self, lead_id: str, lead_profile: Dict[str, Any]) -> PersonalizedJourney:
        return PersonalizedJourney(
            journey_id=f"fallback_{lead_id}",
            lead_id=lead_id,
            persona_type="General Buyer",
            journey_strategy="Standard qualification sequence",
            estimated_conversion_days=60,
            confidence_score=0.5,
            touchpoints=[],
            dynamic_triggers=[],
            next_best_action="Initial SMS contact",
        )


# Singleton instance
_journey_instance = None


def get_journey_orchestrator() -> ClaudeJourneyOrchestrator:
    global _journey_instance
    if _journey_instance is None:
        _journey_instance = ClaudeJourneyOrchestrator()
    return _journey_instance
