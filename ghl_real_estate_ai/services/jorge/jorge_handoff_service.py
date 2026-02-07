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
import time
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


class JorgeHandoffService:
    """Evaluates and executes cross-bot handoffs based on intent signals."""

    TAG_MAP = {
        "lead": "Needs Qualifying",
        "buyer": "Buyer-Lead",
        "seller": "Needs Qualifying",
    }

    # Confidence thresholds per handoff direction
    THRESHOLDS = {
        ("lead", "buyer"): 0.7,
        ("lead", "seller"): 0.7,
        ("buyer", "seller"): 0.8,
        ("seller", "buyer"): 0.6,
    }

    CIRCULAR_WINDOW_SECONDS = 30 * 60
    HOURLY_HANDOFF_LIMIT = 3
    DAILY_HANDOFF_LIMIT = 10
    HOUR_SECONDS = 3600
    DAY_SECONDS = 86400

    _handoff_history: Dict[str, List[Dict[str, Any]]] = {}

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

    def __init__(self, analytics_service=None):
        self.analytics_service = analytics_service

    @classmethod
    def _cleanup_old_entries(cls, max_age: float = 86400) -> None:
        now = time.time()
        cutoff = now - max_age
        contacts_to_remove = []
        for contact_id, entries in cls._handoff_history.items():
            cls._handoff_history[contact_id] = [
                e for e in entries if e["timestamp"] > cutoff
            ]
            if not cls._handoff_history[contact_id]:
                contacts_to_remove.append(contact_id)
        for contact_id in contacts_to_remove:
            del cls._handoff_history[contact_id]

    @classmethod
    def _check_circular_handoff(
        cls, contact_id: str, source_bot: str, target_bot: str
    ) -> Optional[str]:
        now = time.time()
        cutoff = now - cls.CIRCULAR_WINDOW_SECONDS
        for entry in cls._handoff_history.get(contact_id, []):
            if (
                entry["from"] == source_bot
                and entry["to"] == target_bot
                and entry["timestamp"] > cutoff
            ):
                return (
                    f"Circular handoff blocked: {source_bot}->{target_bot} "
                    f"for contact {contact_id} occurred within last 30 minutes"
                )
        return None

    @classmethod
    def _check_rate_limit(cls, contact_id: str) -> Optional[str]:
        now = time.time()
        entries = cls._handoff_history.get(contact_id, [])
        hourly_count = sum(
            1 for e in entries if e["timestamp"] > now - cls.HOUR_SECONDS
        )
        if hourly_count >= cls.HOURLY_HANDOFF_LIMIT:
            return (
                f"Rate limit exceeded: {hourly_count} handoffs in the last hour "
                f"for contact {contact_id} (max {cls.HOURLY_HANDOFF_LIMIT}/hour)"
            )
        daily_count = sum(
            1 for e in entries if e["timestamp"] > now - cls.DAY_SECONDS
        )
        if daily_count >= cls.DAILY_HANDOFF_LIMIT:
            return (
                f"Rate limit exceeded: {daily_count} handoffs in the last 24 hours "
                f"for contact {contact_id} (max {cls.DAILY_HANDOFF_LIMIT}/day)"
            )
        return None

    @classmethod
    def _record_handoff(
        cls, contact_id: str, source_bot: str, target_bot: str
    ) -> None:
        if contact_id not in cls._handoff_history:
            cls._handoff_history[contact_id] = []
        cls._handoff_history[contact_id].append({
            "from": source_bot,
            "to": target_bot,
            "timestamp": time.time(),
        })

    async def evaluate_handoff(
        self,
        current_bot: str,
        contact_id: str,
        conversation_history: List[Dict],
        intent_signals: Dict[str, Any],
    ) -> Optional[HandoffDecision]:
        """Evaluate whether a handoff is needed based on intent signals."""
        buyer_score = intent_signals.get("buyer_intent_score", 0.0)
        seller_score = intent_signals.get("seller_intent_score", 0.0)
        detected_phrases = intent_signals.get("detected_intent_phrases", [])

        # Determine candidate target and score
        if current_bot in ("lead", "seller") and buyer_score > seller_score:
            target = "buyer"
            score = buyer_score
        elif current_bot in ("lead", "buyer") and seller_score > buyer_score:
            target = "seller"
            score = seller_score
        else:
            return None

        # No self-handoff
        if target == current_bot:
            return None

        threshold = self.THRESHOLDS.get((current_bot, target))
        if threshold is None or score < threshold:
            return None

        reason = f"{target}_intent_detected"
        return HandoffDecision(
            source_bot=current_bot,
            target_bot=target,
            reason=reason,
            confidence=score,
            context={
                "contact_id": contact_id,
                "detected_phrases": detected_phrases,
                "conversation_turns": len(conversation_history),
            },
        )

    async def execute_handoff(
        self,
        decision: HandoffDecision,
        contact_id: str,
        location_id: str = "",
    ) -> List[Dict[str, Any]]:
        """Generate GHL action dicts to execute the handoff."""
        self._cleanup_old_entries()

        circular_reason = self._check_circular_handoff(
            contact_id, decision.source_bot, decision.target_bot
        )
        if circular_reason:
            logger.warning(circular_reason)
            return [{"handoff_executed": False, "reason": circular_reason}]

        rate_reason = self._check_rate_limit(contact_id)
        if rate_reason:
            logger.warning(rate_reason)
            return [{"handoff_executed": False, "reason": rate_reason}]

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
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to log handoff analytics for {contact_id}: {e}")

        logger.info(
            f"Handoff: {decision.source_bot} -> {decision.target_bot} "
            f"for contact {contact_id} (confidence={decision.confidence:.2f}, "
            f"reason={decision.reason})"
        )

        self._record_handoff(contact_id, decision.source_bot, decision.target_bot)

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
