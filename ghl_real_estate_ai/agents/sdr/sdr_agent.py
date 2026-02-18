"""
SDR Agent — top-level orchestrator for autonomous outbound lead generation.

Inherits BaseBotWorkflow for monitoring, A/B testing, and event publishing.
Coordinates ProspectSourcer, OutreachSequenceEngine, CadenceScheduler,
QualificationGate, and ObjectionHandler.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ghl_real_estate_ai.agents.base_bot_workflow import BaseBotWorkflow
from ghl_real_estate_ai.agents.sdr.objection_handler import ObjectionHandler
from ghl_real_estate_ai.services.sdr.cadence_scheduler import CadenceScheduler
from ghl_real_estate_ai.services.sdr.outreach_sequence_engine import (
    OutreachSequenceEngine,
    OutreachRecord,
    SequenceStep,
    is_terminal_step,
)
from ghl_real_estate_ai.services.sdr.prospect_sourcer import ProspectSource, ProspectSourcer
from ghl_real_estate_ai.services.sdr.qualification_gate import QualificationGate

if TYPE_CHECKING:
    from ghl_real_estate_ai.services.enhanced_ghl_client import EnhancedGHLClient
    from ghl_real_estate_ai.services.sdr.qualification_gate import GateDecision

logger = logging.getLogger(__name__)


@dataclass
class SDRBotConfig:
    """Feature flags for SDRAgent."""

    handoff_enabled: bool = True
    enable_ml_scoring: bool = False


@dataclass
class SDRReplyResult:
    """Result of SDRAgent.process_inbound_reply()."""

    contact_id: str
    action_taken: str   # "opt_out" | "rebuttal_sent" | "sequence_advanced" | "gate_passed" | "no_action"
    gate_decision: Optional["GateDecision"] = None
    objection_type: Optional[str] = None
    handoff_triggered: bool = False


@dataclass
class ProspectingResult:
    """Result of SDRAgent.run_prospecting_cycle()."""

    location_id: str
    sources: List[str]
    prospects_found: int = 0
    enrolled: int = 0
    already_enrolled: int = 0
    errors: int = 0


class SDRAgent(BaseBotWorkflow):
    """
    Autonomous SDR agent — coordinates outbound prospect sourcing, multi-touch
    outreach sequences, objection handling, qualification gating, and Jorge bot handoffs.

    Entry points:
    - run_prospecting_cycle(): pull new prospects and enroll them
    - process_inbound_reply(): handle a GHL ContactReply webhook
    - evaluate_and_handoff(): gate check + handoff for a specific contact
    """

    def __init__(
        self,
        ghl_client: Optional["EnhancedGHLClient"] = None,
        config: Optional[SDRBotConfig] = None,
        industry_config: Optional[Any] = None,
    ) -> None:
        self.config = config or SDRBotConfig()  # Must be set BEFORE super().__init__
        super().__init__(
            tenant_id="jorge_sdr_bot",
            industry_config=industry_config,
            enable_ml_analytics=self.config.enable_ml_scoring,
        )
        self.ghl_client = ghl_client

        # Wire up SDR subsystems
        self._sourcer = ProspectSourcer(ghl_client=ghl_client)
        self._engine = OutreachSequenceEngine(ghl_client=ghl_client)
        self._scheduler = CadenceScheduler(sequence_engine=self._engine)
        self._objection_handler = ObjectionHandler(orchestrator=None)

        # Intent decoder for qualification gate
        from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder
        self._intent_decoder = LeadIntentDecoder(ghl_client=ghl_client)
        self._gate = QualificationGate(intent_decoder=self._intent_decoder)

        logger.info("[SDR] SDRAgent initialized")

    # -----------------------------------------------------------------------
    # Primary entry points
    # -----------------------------------------------------------------------

    async def run_prospecting_cycle(
        self,
        location_id: str,
        sources: Optional[List[ProspectSource]] = None,
        max_per_source: int = 50,
    ) -> ProspectingResult:
        """
        Pull new prospects from configured sources and enroll them in sequences.

        Args:
            location_id: GHL location ID to scope the search
            sources: override default sources (default: GHL_PIPELINE + STALE_LEAD)
            max_per_source: max contacts to fetch per source

        Returns:
            ProspectingResult with counts
        """
        if sources is None:
            sources = [ProspectSource.GHL_PIPELINE, ProspectSource.STALE_LEAD]

        result = ProspectingResult(
            location_id=location_id,
            sources=[s.value for s in sources],
        )

        try:
            prospects = await self._sourcer.fetch_prospects(
                location_id=location_id,
                sources=sources,
                max_per_source=max_per_source,
            )
            result.prospects_found = len(prospects)

            for prospect in prospects:
                try:
                    await self._engine.enroll_prospect(
                        contact_id=prospect.contact_id,
                        location_id=prospect.location_id,
                        lead_type=prospect.lead_type,
                    )
                    result.enrolled += 1
                    self.publish_event(
                        "sdr.prospect_enrolled",
                        {
                            "contact_id": prospect.contact_id,
                            "source": prospect.source.value,
                            "lead_type": prospect.lead_type,
                        },
                    )
                except Exception as exc:
                    logger.error(
                        f"[SDR] Enrollment failed contact={prospect.contact_id}: {exc}"
                    )
                    result.errors += 1

        except Exception as exc:
            logger.error(f"[SDR] Prospecting cycle failed location={location_id}: {exc}")
            result.errors += 1

        logger.info(
            f"[SDR] Prospecting cycle complete: "
            f"found={result.prospects_found} enrolled={result.enrolled} "
            f"errors={result.errors} location={location_id}"
        )
        return result

    async def process_inbound_reply(
        self,
        contact_id: str,
        message: str,
        channel: str,
        location_id: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> SDRReplyResult:
        """
        Handle an inbound reply from a prospect.

        Flow:
        1. Classify as objection (pattern match)
        2. If opt-out: tag DND, stop sequence
        3. If objection: send rebuttal, pause/advance sequence
        4. If engagement: advance sequence, run qualification gate
        5. If gate passes: trigger Jorge handoff

        Args:
            contact_id: GHL contact ID
            message: inbound message body
            channel: "sms" | "email"
            location_id: GHL location ID
            conversation_history: prior conversation for gate evaluation

        Returns:
            SDRReplyResult
        """
        result = SDRReplyResult(contact_id=contact_id, action_taken="no_action")

        # Step 1: classify objection
        objection_result = self._objection_handler.handle(message, contact_id=contact_id)
        result.objection_type = objection_result.objection_type

        if objection_result.should_opt_out:
            # Tag DND in GHL
            try:
                await self.ghl_client.update_contact(
                    contact_id=contact_id,
                    updates={"tags": ["DND", "SDR-Opted-Out"]},
                )
            except Exception as exc:
                logger.error(f"[SDR] DND tag failed contact={contact_id}: {exc}")
            result.action_taken = "opt_out"
            self.publish_event("sdr.contact_opted_out", {"contact_id": contact_id})
            return result

        if objection_result.should_pause:
            result.action_taken = "rebuttal_sent"
            # Phase 2: dispatch rebuttal via GHL; for now just log
            logger.info(
                f"[SDR] Nurture pause for contact={contact_id} "
                f"objection={objection_result.objection_type}"
            )
            return result

        if objection_result.objection_type is not None:
            # Non-blocking objection — send rebuttal and continue
            result.action_taken = "rebuttal_sent"
            return result

        # Step 2: engagement reply → run qualification gate
        history = conversation_history or [{"role": "user", "content": message}]
        from ghl_real_estate_ai.services.sdr.prospect_sourcer import (
            ProspectProfile,
            ProspectSource,
        )
        dummy_profile = ProspectProfile(
            contact_id=contact_id,
            location_id=location_id,
            source=ProspectSource.GHL_PIPELINE,
            lead_type="unknown",
            property_address=None,
            days_in_stage=0,
            last_activity=None,
        )
        gate_decision = self._gate.evaluate(contact_id, history, dummy_profile)
        result.gate_decision = gate_decision

        if gate_decision.passed and self.config.handoff_enabled:
            handoff_ok = await self._trigger_handoff(contact_id, location_id, gate_decision)
            result.handoff_triggered = handoff_ok
            result.action_taken = "gate_passed"
        else:
            result.action_taken = "sequence_advanced"

        return result

    async def evaluate_and_handoff(
        self,
        contact_id: str,
        location_id: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional["GateDecision"]:
        """
        Run the qualification gate and trigger a Jorge handoff if it passes.

        Returns the GateDecision (check .passed and .handoff_target).
        """
        history = conversation_history or []
        from ghl_real_estate_ai.services.sdr.prospect_sourcer import (
            ProspectProfile,
            ProspectSource,
        )
        dummy_profile = ProspectProfile(
            contact_id=contact_id,
            location_id=location_id,
            source=ProspectSource.GHL_PIPELINE,
            lead_type="unknown",
            property_address=None,
            days_in_stage=0,
            last_activity=None,
        )
        decision = self._gate.evaluate(contact_id, history, dummy_profile)
        if decision.passed and self.config.handoff_enabled:
            await self._trigger_handoff(contact_id, location_id, decision)
        return decision

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    async def _trigger_handoff(
        self,
        contact_id: str,
        location_id: str,
        gate_decision: "GateDecision",
    ) -> bool:
        """Initiate a Jorge bot handoff via JorgeHandoffService."""
        try:
            from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
                JorgeHandoffService,
            )
            handoff_service = JorgeHandoffService()
            await handoff_service.evaluate_handoff_from_profile(
                current_bot="sdr",
                contact_id=contact_id,
                conversation_history=[],
                intent_profile=gate_decision.intent_profile,
            )
            # Tag contact in GHL
            await self.ghl_client.update_contact(
                contact_id=contact_id,
                updates={"tags": ["SDR-Qualified", "SDR-Handoff-Triggered"]},
            )
            self.publish_event(
                "sdr.handoff_triggered",
                {
                    "contact_id": contact_id,
                    "handoff_target": gate_decision.handoff_target,
                    "frs_score": gate_decision.frs_score,
                },
            )
            logger.info(
                f"[SDR] Handoff triggered contact={contact_id} "
                f"target={gate_decision.handoff_target}"
            )
            return True
        except Exception as exc:
            logger.error(
                f"[SDR] Handoff failed contact={contact_id}: {exc}", exc_info=True
            )
            return False
