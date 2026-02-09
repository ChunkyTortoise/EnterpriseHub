"""Hierarchical Context Memory for Jorge bots.

Three-tier memory system:
- Short-term: In-memory recent messages (current session)
- Medium-term: Summarized conversation history (stored as embeddings)
- Long-term: Entity store (key facts about contacts)

Provides context retrieval for bot workflows so they can recall
prior interactions without re-asking questions.
"""

import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Maximum items per tier
MAX_SHORT_TERM = 20  # Recent messages
MAX_MEDIUM_TERM = 50  # Conversation summaries
MAX_LONG_TERM = 100  # Entity facts


@dataclass
class MemoryEntry:
    """A single memory entry in any tier."""

    content: str
    entry_type: str  # "message", "summary", "entity"
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    relevance_score: float = 1.0


@dataclass
class EntityFact:
    """A key fact about a contact stored in long-term memory."""

    key: str  # e.g., "budget", "timeline", "preapproval_status"
    value: str
    confidence: float = 1.0
    source: str = ""  # Which bot/conversation extracted this
    updated_at: float = field(default_factory=time.time)


@dataclass
class ContextResult:
    """Retrieved context for a bot workflow."""

    recent_messages: List[Dict[str, str]]
    conversation_summary: str
    entity_facts: Dict[str, EntityFact]
    metadata: Dict[str, Any] = field(default_factory=dict)


class HierarchicalContextMemory:
    """Three-tier memory system for cross-session context retrieval."""

    def __init__(
        self,
        max_short_term: int = MAX_SHORT_TERM,
        max_medium_term: int = MAX_MEDIUM_TERM,
        max_long_term: int = MAX_LONG_TERM,
    ):
        self._max_short_term = max_short_term
        self._max_medium_term = max_medium_term
        self._max_long_term = max_long_term

        # contact_id → tier data
        self._short_term: Dict[str, List[MemoryEntry]] = {}
        self._medium_term: Dict[str, List[MemoryEntry]] = {}
        self._long_term: Dict[str, Dict[str, EntityFact]] = {}

    def add_message(
        self,
        contact_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a message to short-term memory."""
        entries = self._short_term.setdefault(contact_id, [])
        entries.append(
            MemoryEntry(
                content=content,
                entry_type="message",
                metadata={"role": role, **(metadata or {})},
            )
        )
        # Evict oldest if over limit
        if len(entries) > self._max_short_term:
            self._short_term[contact_id] = entries[-self._max_short_term :]

    def add_summary(
        self,
        contact_id: str,
        summary: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a conversation summary to medium-term memory."""
        entries = self._medium_term.setdefault(contact_id, [])
        entries.append(
            MemoryEntry(
                content=summary,
                entry_type="summary",
                metadata=metadata or {},
            )
        )
        if len(entries) > self._max_medium_term:
            self._medium_term[contact_id] = entries[-self._max_medium_term :]

    def set_entity_fact(
        self,
        contact_id: str,
        key: str,
        value: str,
        confidence: float = 1.0,
        source: str = "",
    ) -> None:
        """Store or update a key fact about a contact."""
        facts = self._long_term.setdefault(contact_id, {})
        existing = facts.get(key)

        # Only update if new confidence is higher or fact doesn't exist
        if existing is None or confidence >= existing.confidence:
            facts[key] = EntityFact(
                key=key,
                value=value,
                confidence=confidence,
                source=source,
            )

        # Evict lowest-confidence facts if over limit
        if len(facts) > self._max_long_term:
            sorted_facts = sorted(facts.items(), key=lambda x: x[1].confidence)
            for k, _ in sorted_facts[: len(facts) - self._max_long_term]:
                del facts[k]

    def get_context(
        self,
        contact_id: str,
        max_recent: int = 10,
        include_summaries: bool = True,
        include_entities: bool = True,
    ) -> ContextResult:
        """Retrieve context for a bot workflow.

        Args:
            contact_id: GHL contact ID.
            max_recent: Max recent messages to include.
            include_summaries: Whether to include medium-term summaries.
            include_entities: Whether to include entity facts.

        Returns:
            ContextResult with available context.
        """
        # Short-term: recent messages
        short_entries = self._short_term.get(contact_id, [])
        recent_messages = [
            {"role": e.metadata.get("role", "unknown"), "content": e.content}
            for e in short_entries[-max_recent:]
        ]

        # Medium-term: conversation summaries
        summary = ""
        if include_summaries:
            medium_entries = self._medium_term.get(contact_id, [])
            if medium_entries:
                summaries = [e.content for e in medium_entries[-3:]]
                summary = " | ".join(summaries)

        # Long-term: entity facts
        entity_facts = {}
        if include_entities:
            entity_facts = dict(self._long_term.get(contact_id, {}))

        return ContextResult(
            recent_messages=recent_messages,
            conversation_summary=summary,
            entity_facts=entity_facts,
        )

    def clear_short_term(self, contact_id: str) -> None:
        """Clear short-term memory for a contact (session end)."""
        self._short_term.pop(contact_id, None)

    def clear_all(self, contact_id: str) -> None:
        """Clear all memory tiers for a contact."""
        self._short_term.pop(contact_id, None)
        self._medium_term.pop(contact_id, None)
        self._long_term.pop(contact_id, None)

    def get_stats(self, contact_id: str) -> Dict[str, int]:
        """Get memory statistics for a contact."""
        return {
            "short_term": len(self._short_term.get(contact_id, [])),
            "medium_term": len(self._medium_term.get(contact_id, [])),
            "long_term": len(self._long_term.get(contact_id, {})),
        }


# Singleton
_memory: Optional[HierarchicalContextMemory] = None


def get_context_memory() -> HierarchicalContextMemory:
    global _memory
    if _memory is None:
        _memory = HierarchicalContextMemory()
    return _memory
