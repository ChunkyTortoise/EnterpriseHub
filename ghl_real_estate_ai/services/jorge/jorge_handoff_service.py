"""
Jorge Cross-Bot Handoff Service

Tag-driven handoff between lead, buyer, and seller bots.
When Bot A determines the contact should be handled by Bot B, it:
1. Removes Bot A's activation tag
2. Adds Bot B's activation tag
3. Adds a handoff tracking tag (e.g., Handoff-Lead-to-Buyer)
4. Logs the handoff event via analytics_service

The next inbound message routes to Bot B via existing tag-based routing.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class HandoffDecision:
    """Encapsulates a bot-to-bot handoff decision."""

    source_bot: str          # "lead", "buyer", "seller"
    target_bot: str          # "lead", "buyer", "seller"
    reason: str              # "buyer_intent_detected", "seller_intent_detected", etc.
    confidence: float        # 0.0-1.0
    context: Dict[str, Any] = field(default_factory=dict)

    def to_confidence_schema(self) -> Dict[str, Any]:
        """Normalize decision details into the WS3 handoff confidence schema."""
        evidence = dict(self.context or {})
        evidence.setdefault("source_bot", self.source_bot)
        evidence.setdefault("target_bot", self.target_bot)
        return JorgeHandoffService.build_handoff_confidence(
            mode=self.target_bot,
            score=self.confidence,
            reason=self.reason,
            evidence=evidence,
        )


class JorgeHandoffService:
    """Evaluates and executes cross-bot handoffs based on intent signals."""

    VALID_MODES = {"seller", "buyer", "lead", "fallback"}

    TAG_MAP = {
        "lead": "Needs Qualifying",
        "buyer": "Buyer-Lead",
        "seller": "Needs Qualifying",
    }

    # Default confidence thresholds per handoff direction
    DEFAULT_THRESHOLDS = {
        ("lead", "buyer"): 0.7,
        ("lead", "seller"): 0.7,
        ("buyer", "seller"): 0.8,
        ("seller", "buyer"): 0.6,
    }
    THRESHOLDS = DEFAULT_THRESHOLDS
    DEFAULT_LEAD_CONFLICT_PRIORITY = "seller"

    # Intent phrase patterns for signal boosting
    BUYER_INTENT_PATTERNS = [
        r"\bi\s+want\s+to\s+buy\b",
        r"\blooking\s+to\s+buy\b",
        r"\bbudget\b.*\$",
        r"\bpre[- ]?approv",
        r"\bpre[- ]?qualif",
        r"\bdown\s+payment\b",
        r"\bfha\b|\bva\s+loan\b|\bconventional\b",
        r"\bfind\s+(a|my)\s+(new\s+)?(home|house|place|property)\b",
    ]

    SELLER_INTENT_PATTERNS = [
        r"\bsell\s+my\s+(home|house|property)\b",
        r"\bwhat'?s\s+my\s+home\s+worth\b",
        r"\bhome\s+valu",
        r"\bcma\b",
        r"\blist(ing)?\s+my\s+(home|house|property)\b",
        r"\bneed\s+to\s+sell\b",
        r"\bsell\s+before\s+buy",
        r"\bsell\s+first\b",
    ]

    def __init__(
        self,
        analytics_service=None,
        thresholds: Optional[Dict[tuple[str, str], float]] = None,
        lead_conflict_priority: str = DEFAULT_LEAD_CONFLICT_PRIORITY,
    ):
        self.analytics_service = analytics_service
        self.thresholds = dict(self.DEFAULT_THRESHOLDS)
        if thresholds:
            for route, value in thresholds.items():
                if isinstance(route, tuple) and len(route) == 2:
                    self.thresholds[(str(route[0]), str(route[1]))] = float(value)
        if lead_conflict_priority not in {"buyer", "seller"}:
            logger.warning(
                "Invalid lead conflict priority '%s'; defaulting to '%s'",
                lead_conflict_priority,
                self.DEFAULT_LEAD_CONFLICT_PRIORITY,
            )
            lead_conflict_priority = self.DEFAULT_LEAD_CONFLICT_PRIORITY
        self.lead_conflict_priority = lead_conflict_priority

    @classmethod
    def build_handoff_confidence(
        cls,
        mode: str,
        score: float,
        reason: str,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a normalized WS3 handoff confidence payload."""
        normalized_mode = mode if mode in cls.VALID_MODES else "fallback"
        normalized_score = max(0.0, min(1.0, float(score or 0.0)))
        return {
            "mode": normalized_mode,
            "score": normalized_score,
            "reason": reason or "unspecified",
            "evidence": dict(evidence or {}),
        }

    @classmethod
    def build_signal_confidence(
        cls,
        mode: str,
        intent_signals: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build confidence payload from extracted intent signals."""
        signals = intent_signals or {}
        buyer_score = float(signals.get("buyer_intent_score", 0.0) or 0.0)
        seller_score = float(signals.get("seller_intent_score", 0.0) or 0.0)
        max_score = max(buyer_score, seller_score)
        detected_phrases = signals.get("detected_intent_phrases", [])

        reason = "intent_signal_detected" if max_score > 0 else "no_intent_signal"
        if buyer_score > 0 and seller_score > 0 and buyer_score == seller_score:
            reason = "conflicting_intent_signals"

        return cls.build_handoff_confidence(
            mode=mode,
            score=max_score,
            reason=reason,
            evidence={
                "buyer_intent_score": buyer_score,
                "seller_intent_score": seller_score,
                "detected_intent_phrases": detected_phrases,
            },
        )

    async def evaluate_handoff(
        self,
        current_bot: str,
        contact_id: str,
        conversation_history: List[Dict],
        intent_signals: Dict[str, Any],
    ) -> Optional[HandoffDecision]:
        """Evaluate whether a handoff is needed based on intent signals."""
        buyer_score = float(intent_signals.get("buyer_intent_score", 0.0) or 0.0)
        seller_score = float(intent_signals.get("seller_intent_score", 0.0) or 0.0)
        detected_phrases = intent_signals.get("detected_intent_phrases", [])

        target = ""
        score = 0.0
        reason = ""

        # Determine candidate target and score with deterministic tie-breaks
        if current_bot == "lead":
            if buyer_score > seller_score:
                target = "buyer"
                score = buyer_score
                reason = "buyer_intent_detected"
            elif seller_score > buyer_score:
                target = "seller"
                score = seller_score
                reason = "seller_intent_detected"
            elif buyer_score > 0 and seller_score > 0:
                target = self.lead_conflict_priority
                score = buyer_score if target == "buyer" else seller_score
                reason = f"conflict_priority_{target}"
        elif current_bot == "seller" and buyer_score > seller_score:
            target = "buyer"
            score = buyer_score
            reason = "buyer_intent_detected"
        elif current_bot == "buyer" and seller_score > buyer_score:
            target = "seller"
            score = seller_score
            reason = "seller_intent_detected"

        if not target:
            return None

        # No self-handoff
        if target == current_bot:
            return None

        threshold = self.thresholds.get((current_bot, target))
        if threshold is None or score < threshold:
            return None

        return HandoffDecision(
            source_bot=current_bot,
            target_bot=target,
            reason=reason,
            confidence=score,
            context={
                "contact_id": contact_id,
                "detected_phrases": detected_phrases,
                "conversation_turns": len(conversation_history),
                "buyer_intent_score": buyer_score,
                "seller_intent_score": seller_score,
                "threshold_used": threshold,
            },
        )

    async def execute_handoff(
        self,
        decision: HandoffDecision,
        contact_id: str,
        location_id: str = "",
    ) -> List[Dict[str, Any]]:
        """Generate GHL action dicts to execute the handoff."""
        actions: List[Dict[str, Any]] = []

        source_tag = self.TAG_MAP.get(decision.source_bot)
        target_tag = self.TAG_MAP.get(decision.target_bot)

        # Remove source bot's activation tag
        if source_tag:
            actions.append({"type": "remove_tag", "tag": source_tag})

        # Add target bot's activation tag
        if target_tag:
            actions.append({"type": "add_tag", "tag": target_tag})

        # Add tracking tag
        tracking_tag = (
            f"Handoff-{decision.source_bot.capitalize()}-to-{decision.target_bot.capitalize()}"
        )
        actions.append({"type": "add_tag", "tag": tracking_tag})

        # Log analytics event
        if self.analytics_service:
            try:
                confidence_schema = decision.to_confidence_schema()
                await self.analytics_service.track_event(
                    event_type="jorge_handoff",
                    location_id=location_id,
                    contact_id=contact_id,
                    data={
                        "source_bot": decision.source_bot,
                        "target_bot": decision.target_bot,
                        "reason": decision.reason,
                        "confidence": decision.confidence,
                        "detected_phrases": decision.context.get("detected_phrases", []),
                        "mode": confidence_schema["mode"],
                        "score": confidence_schema["score"],
                        "evidence": confidence_schema["evidence"],
                        "handoff_confidence": confidence_schema,
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to log handoff analytics for {contact_id}: {e}")

        logger.info(
            f"Handoff: {decision.source_bot} -> {decision.target_bot} "
            f"for contact {contact_id} (confidence={decision.confidence:.2f}, "
            f"reason={decision.reason})"
        )

        return actions

    @classmethod
    def extract_intent_signals(cls, message: str) -> Dict[str, Any]:
        """Extract intent signals from a user message for handoff evaluation."""
        buyer_matches = []
        for pattern in cls.BUYER_INTENT_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                buyer_matches.append(pattern)

        seller_matches = []
        for pattern in cls.SELLER_INTENT_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                seller_matches.append(pattern)

        # Score: each pattern match adds ~0.3, capped at 1.0
        buyer_score = min(1.0, len(buyer_matches) * 0.3) if buyer_matches else 0.0
        seller_score = min(1.0, len(seller_matches) * 0.3) if seller_matches else 0.0

        # Collect human-readable phrases
        detected = []
        if buyer_matches:
            detected.append("buyer intent detected")
        if seller_matches:
            detected.append("seller intent detected")

        return {
            "buyer_intent_score": buyer_score,
            "seller_intent_score": seller_score,
            "detected_intent_phrases": detected,
        }
