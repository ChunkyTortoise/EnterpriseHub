"""
SDR Agent — OutreachState TypedDict.

Represents the full in-memory state of a contact's outreach journey.
LangGraph-compatible if the sequence is wired as a graph in a future phase.
"""

from __future__ import annotations

from typing import List, Optional
from typing_extensions import TypedDict


class OutreachState(TypedDict, total=False):
    """Mutable state dict threaded through SDR sequence steps."""

    contact_id: str
    location_id: str
    current_step: str           # SequenceStep.value
    enrolled_at: str            # ISO-8601 string for JSON-serializability
    next_touch_at: Optional[str]
    reply_count: int
    objections_hit: List[str]   # list of classified objection types hit so far
    last_reply: Optional[str]   # most recent reply body (plain text, not encrypted)
    frs_score: Optional[float]
    pcs_score: Optional[float]
    lead_type: str              # "buyer" | "seller" | "unknown"
    handoff_triggered: bool
    ab_variant: Optional[str]
    last_touch_channel: Optional[str]  # "sms" | "email" | "voicemail"
    last_touch_step: Optional[str]
