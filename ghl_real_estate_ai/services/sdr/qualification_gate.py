"""
SDR QualificationGate — FRS/PCS threshold evaluation.

Determines whether a prospect has been warmed up enough to hand off to a Jorge bot.
Thresholds mirror the existing JorgeHandoffService constants (0.70 confidence).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder
    from ghl_real_estate_ai.models.lead_scoring import LeadIntentProfile
    from ghl_real_estate_ai.services.sdr.prospect_sourcer import ProspectProfile

logger = logging.getLogger(__name__)


@dataclass
class GateDecision:
    """Result of QualificationGate.evaluate()."""

    passed: bool
    frs_score: float
    pcs_score: float
    lead_type: str  # "buyer" | "seller" | "ambiguous" | "unknown"
    confidence: float  # max(buyer_confidence, seller_confidence)
    intent_profile: "LeadIntentProfile"
    handoff_target: Optional[str]  # "lead_bot" | "buyer_bot" | "seller_bot"
    disqualify_reason: Optional[str]  # set when passed=False


class QualificationGate:
    """
    Evaluates whether a prospect meets the criteria to be handed off to Jorge bots.

    Thresholds (match JorgeHandoffService):
    - FRS >= 60.0
    - max(buyer_intent_confidence, seller_intent_confidence) >= 0.70
    """

    FRS_THRESHOLD: float = 60.0
    CONF_THRESHOLD: float = 0.70

    def __init__(self, intent_decoder: "LeadIntentDecoder") -> None:
        self._decoder = intent_decoder

    def evaluate(
        self,
        contact_id: str,
        conversation_history: List[Dict],
        prospect_profile: "ProspectProfile",
    ) -> GateDecision:
        """
        Run qualification scoring and return a GateDecision.

        Args:
            contact_id: GHL contact identifier
            conversation_history: list of {role, content} dicts
            prospect_profile: sourced prospect data (used for lead_type hint)

        Returns:
            GateDecision with passed=True when FRS >= 60 and confidence >= 0.70
        """
        intent_profile = self._decoder.analyze_lead(contact_id, conversation_history)

        frs_score = intent_profile.frs.total_score
        pcs_score = intent_profile.pcs.total_score
        buyer_conf = intent_profile.buyer_intent_confidence
        seller_conf = intent_profile.seller_intent_confidence
        confidence = max(buyer_conf, seller_conf)
        lead_type = intent_profile.lead_type or prospect_profile.lead_type

        frs_ok = frs_score >= self.FRS_THRESHOLD
        conf_ok = confidence >= self.CONF_THRESHOLD

        # Always compute handoff_target — useful for nurture routing even on failure
        handoff_target = self._select_handoff_target(buyer_conf, seller_conf, lead_type)

        if frs_ok and conf_ok:
            logger.info(
                f"[SDR] Gate PASSED contact={contact_id} "
                f"frs={frs_score:.1f} conf={confidence:.2f} target={handoff_target}"
            )
            return GateDecision(
                passed=True,
                frs_score=frs_score,
                pcs_score=pcs_score,
                lead_type=lead_type,
                confidence=confidence,
                intent_profile=intent_profile,
                handoff_target=handoff_target,
                disqualify_reason=None,
            )

        reason = _build_disqualify_reason(frs_score, confidence, self.FRS_THRESHOLD, self.CONF_THRESHOLD)
        logger.info(f"[SDR] Gate FAILED contact={contact_id} frs={frs_score:.1f} conf={confidence:.2f} reason={reason}")
        return GateDecision(
            passed=False,
            frs_score=frs_score,
            pcs_score=pcs_score,
            lead_type=lead_type,
            confidence=confidence,
            intent_profile=intent_profile,
            handoff_target=handoff_target,
            disqualify_reason=reason,
        )

    @staticmethod
    def _select_handoff_target(buyer_conf: float, seller_conf: float, lead_type: str) -> str:
        """Select the Jorge bot to route to based on intent signals."""
        if buyer_conf >= QualificationGate.CONF_THRESHOLD and buyer_conf >= seller_conf:
            return "buyer_bot"
        if seller_conf >= QualificationGate.CONF_THRESHOLD and seller_conf > buyer_conf:
            return "seller_bot"
        # Fallback: use lead_type hint
        if lead_type == "buyer":
            return "buyer_bot"
        if lead_type == "seller":
            return "seller_bot"
        return "lead_bot"


def _build_disqualify_reason(frs_score: float, confidence: float, frs_threshold: float, conf_threshold: float) -> str:
    parts = []
    if frs_score < frs_threshold:
        parts.append(f"FRS {frs_score:.1f} < {frs_threshold}")
    if confidence < conf_threshold:
        parts.append(f"intent confidence {confidence:.2f} < {conf_threshold}")
    return "; ".join(parts) if parts else "below thresholds"
