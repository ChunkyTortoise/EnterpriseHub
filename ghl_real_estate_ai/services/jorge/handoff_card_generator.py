"""Warm handoff card generator.

Generates structured summary cards when conversations hand off between bots
or to human agents. Cards include key context so the receiving party can
continue the conversation without re-asking questions.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class HandoffCard:
    """Structured summary for handoff transitions."""

    # Source info
    source_bot: str
    target_bot: str
    handoff_reason: str
    confidence: float

    # Contact context
    contact_id: str
    contact_name: str = ""

    # Conversation summary
    conversation_summary: str = ""
    key_facts: List[str] = field(default_factory=list)
    unanswered_questions: List[str] = field(default_factory=list)

    # Qualification data
    qualification_score: float = 0.0
    temperature: str = "unknown"
    budget_range: Optional[Dict[str, Any]] = None
    timeline: str = "unknown"

    # Recommended approach
    recommended_approach: str = ""
    priority_level: str = "normal"  # "urgent", "high", "normal", "low"

    # Metadata
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_ghl_note(self) -> str:
        """Format as a GHL contact note."""
        lines = [
            f"=== Handoff Card: {self.source_bot.title()} -> {self.target_bot.title()} ===",
            f"Reason: {self.handoff_reason}",
            f"Confidence: {self.confidence:.0%}",
            f"Priority: {self.priority_level.upper()}",
            "",
        ]
        if self.conversation_summary:
            lines.append(f"Summary: {self.conversation_summary}")
            lines.append("")
        if self.key_facts:
            lines.append("Key Facts:")
            for fact in self.key_facts:
                lines.append(f"  - {fact}")
            lines.append("")
        if self.unanswered_questions:
            lines.append("Open Questions:")
            for q in self.unanswered_questions:
                lines.append(f"  - {q}")
            lines.append("")
        lines.append(
            f"Qualification: {self.qualification_score:.0%} | Temp: {self.temperature}"
        )
        if self.budget_range:
            lines.append(
                f"Budget: ${self.budget_range.get('min', '?'):,} - "
                f"${self.budget_range.get('max', '?'):,}"
            )
        if self.timeline != "unknown":
            lines.append(f"Timeline: {self.timeline}")
        if self.recommended_approach:
            lines.append(f"\nRecommended Approach: {self.recommended_approach}")
        lines.append(f"\nGenerated: {self.created_at}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "source_bot": self.source_bot,
            "target_bot": self.target_bot,
            "handoff_reason": self.handoff_reason,
            "confidence": self.confidence,
            "contact_id": self.contact_id,
            "contact_name": self.contact_name,
            "conversation_summary": self.conversation_summary,
            "key_facts": self.key_facts,
            "unanswered_questions": self.unanswered_questions,
            "qualification_score": self.qualification_score,
            "temperature": self.temperature,
            "budget_range": self.budget_range,
            "timeline": self.timeline,
            "recommended_approach": self.recommended_approach,
            "priority_level": self.priority_level,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


class HandoffCardGenerator:
    """Generates HandoffCards from handoff decisions and conversation context."""

    # Confidence -> priority mapping
    PRIORITY_THRESHOLDS = {
        0.9: "urgent",
        0.8: "high",
        0.6: "normal",
        0.0: "low",
    }

    def generate_card(
        self,
        source_bot: str,
        target_bot: str,
        contact_id: str,
        reason: str,
        confidence: float,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        enriched_context: Optional[Any] = None,  # EnrichedHandoffContext
        contact_name: str = "",
    ) -> HandoffCard:
        """Generate a handoff card from available context.

        Args:
            source_bot: Bot initiating handoff ("lead", "buyer", "seller")
            target_bot: Receiving bot or "human"
            contact_id: GHL contact ID
            reason: Handoff reason string
            confidence: 0.0-1.0 handoff confidence
            conversation_history: List of {"role": "user/assistant", "content": "..."} dicts
            enriched_context: EnrichedHandoffContext if available
            contact_name: Contact display name

        Returns:
            HandoffCard with all available context populated.
        """
        card = HandoffCard(
            source_bot=source_bot,
            target_bot=target_bot,
            handoff_reason=reason,
            confidence=confidence,
            contact_id=contact_id,
            contact_name=contact_name,
            priority_level=self._determine_priority(confidence),
        )

        # Extract from enriched context if available
        if enriched_context is not None:
            card.qualification_score = getattr(
                enriched_context, "source_qualification_score", 0.0
            )
            card.temperature = getattr(
                enriched_context, "source_temperature", "unknown"
            )
            card.budget_range = getattr(enriched_context, "budget_range", None)
            card.conversation_summary = getattr(
                enriched_context, "conversation_summary", ""
            )
            card.timeline = getattr(enriched_context, "urgency_level", "unknown")

            key_insights = getattr(enriched_context, "key_insights", {})
            if key_insights:
                card.key_facts = [f"{k}: {v}" for k, v in key_insights.items()]

        # Extract from conversation history
        if conversation_history:
            card.key_facts.extend(self._extract_key_facts(conversation_history))
            card.unanswered_questions = self._extract_unanswered_questions(
                conversation_history
            )
            if not card.conversation_summary:
                card.conversation_summary = self._summarize_conversation(
                    conversation_history
                )

        # Generate recommended approach
        card.recommended_approach = self._generate_approach(card)

        logger.info(
            "Generated handoff card: %s -> %s for %s (priority: %s)",
            source_bot,
            target_bot,
            contact_id,
            card.priority_level,
        )
        return card

    def _determine_priority(self, confidence: float) -> str:
        """Map confidence score to priority level."""
        for threshold, priority in sorted(
            self.PRIORITY_THRESHOLDS.items(), reverse=True
        ):
            if confidence >= threshold:
                return priority
        return "normal"

    def _extract_key_facts(self, history: List[Dict[str, str]]) -> List[str]:
        """Extract notable facts from conversation (budget mentions, timelines, etc.)."""
        facts: List[str] = []
        budget_keywords = [
            "budget",
            "afford",
            "price range",
            "$",
            "pre-approved",
            "pre-approval",
        ]
        timeline_keywords = [
            "asap",
            "soon",
            "months",
            "weeks",
            "timeline",
            "when",
            "ready",
        ]

        for msg in history:
            content = msg.get("content", "").lower()
            if msg.get("role") == "user":
                if any(kw in content for kw in budget_keywords):
                    facts.append(f"Budget mention: {msg['content'][:100]}")
                if any(kw in content for kw in timeline_keywords):
                    facts.append(f"Timeline mention: {msg['content'][:100]}")
        return facts[:5]  # Cap at 5 facts

    def _extract_unanswered_questions(
        self, history: List[Dict[str, str]]
    ) -> List[str]:
        """Find questions from the last bot message that weren't answered."""
        questions: List[str] = []
        for msg in reversed(history):
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                for sentence in content.split("?"):
                    sentence = sentence.strip()
                    if sentence and len(sentence) > 10:
                        questions.append(sentence + "?")
                break
        return questions[:3]

    def _summarize_conversation(self, history: List[Dict[str, str]]) -> str:
        """Create a brief conversation summary."""
        user_msgs = [m["content"] for m in history if m.get("role") == "user"]
        if not user_msgs:
            return "No user messages in history."
        msg_count = len(history)
        if len(user_msgs) >= 2:
            topics = ", ".join(user_msgs[-2:])[:200]
        else:
            topics = user_msgs[-1][:200]
        return f"{msg_count} messages exchanged. Recent topics: {topics}"

    def _generate_approach(self, card: HandoffCard) -> str:
        """Generate a recommended approach based on card data."""
        parts: List[str] = []
        if card.temperature in ("hot", "warm"):
            parts.append("Contact is engaged and responsive")
        elif card.temperature == "cold":
            parts.append("Contact may need re-engagement")

        if card.qualification_score > 0.7:
            parts.append("well-qualified")
        elif card.qualification_score > 0.4:
            parts.append("partially qualified — continue discovery")
        else:
            parts.append("early stage — focus on building rapport")

        if card.unanswered_questions:
            parts.append(f"address {len(card.unanswered_questions)} open question(s)")

        return ". ".join(parts).capitalize() + "." if parts else "Continue standard qualification."


# Singleton
_generator: Optional[HandoffCardGenerator] = None


def get_handoff_card_generator() -> HandoffCardGenerator:
    """Return the singleton HandoffCardGenerator instance."""
    global _generator
    if _generator is None:
        _generator = HandoffCardGenerator()
    return _generator
