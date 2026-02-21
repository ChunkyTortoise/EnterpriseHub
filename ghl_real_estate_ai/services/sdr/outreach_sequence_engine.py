"""
SDR OutreachSequenceEngine — multi-touch cadence state machine.

Manages enrollment, step progression, and GHL dispatch.
Phase 1: fixed-schedule timing from sdr_config.yaml (no AI timing yet).
Phase 2 will add: Claude-driven compute_next_touch_time.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger

if TYPE_CHECKING:
    from ghl_real_estate_ai.services.enhanced_ghl_client import EnhancedGHLClient

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Step definitions
# ---------------------------------------------------------------------------


class SequenceStep(Enum):
    """All possible states in the SDR outreach sequence."""

    ENROLLED = "enrolled"
    SMS_1 = "sms_1"
    EMAIL_1 = "email_1"
    SMS_2 = "sms_2"
    VOICEMAIL_1 = "voicemail_1"
    EMAIL_2 = "email_2"
    SMS_3 = "sms_3"
    VOICEMAIL_2 = "voicemail_2"
    NURTURE_PAUSE = "nurture_pause"
    # Terminal states
    QUALIFIED = "qualified"
    BOOKED = "booked"
    DISQUALIFIED = "disqualified"
    OPTED_OUT = "opted_out"


_TERMINAL_STEPS = {
    SequenceStep.QUALIFIED,
    SequenceStep.BOOKED,
    SequenceStep.DISQUALIFIED,
    SequenceStep.OPTED_OUT,
}

_STEP_ORDER = [
    SequenceStep.ENROLLED,
    SequenceStep.SMS_1,
    SequenceStep.EMAIL_1,
    SequenceStep.SMS_2,
    SequenceStep.VOICEMAIL_1,
    SequenceStep.EMAIL_2,
    SequenceStep.SMS_3,
    SequenceStep.VOICEMAIL_2,
    SequenceStep.NURTURE_PAUSE,
]


def is_terminal_step(step: SequenceStep) -> bool:
    """Return True if this step ends the sequence."""
    return step in _TERMINAL_STEPS


def get_next_step(step: SequenceStep) -> Optional[SequenceStep]:
    """Return the next step in the sequence, or None if terminal/last."""
    if is_terminal_step(step):
        return None
    try:
        idx = _STEP_ORDER.index(step)
        if idx + 1 < len(_STEP_ORDER):
            return _STEP_ORDER[idx + 1]
    except ValueError:
        pass
    return None


# ---------------------------------------------------------------------------
# Default wait windows (hours) — used when sdr_config.yaml isn't loaded
# ---------------------------------------------------------------------------

_DEFAULT_MIN_WAIT: Dict[str, int] = {
    "sms_1": 0,
    "email_1": 20,
    "sms_2": 60,
    "voicemail_1": 110,
    "email_2": 160,
    "sms_3": 230,
    "voicemail_2": 325,
    "nurture_pause": 480,
}

_STEP_CHANNEL: Dict[str, str] = {
    "sms_1": "sms",
    "email_1": "email",
    "sms_2": "sms",
    "voicemail_1": "voicemail",
    "email_2": "email",
    "sms_3": "sms",
    "voicemail_2": "voicemail",
    "nurture_pause": "email",
}


# ---------------------------------------------------------------------------
# OutreachRecord
# ---------------------------------------------------------------------------


@dataclass
class OutreachRecord:
    """In-memory representation of a contact's sequence state."""

    contact_id: str
    location_id: str
    current_step: SequenceStep
    enrolled_at: datetime
    next_touch_at: Optional[datetime] = None
    reply_count: int = 0
    objections_hit: List[str] = field(default_factory=list)
    lead_type: str = "unknown"
    ab_variant: Optional[str] = None
    sequence_id: Optional[str] = None  # FK to sdr_outreach_sequences.id


# ---------------------------------------------------------------------------
# OutreachSequenceEngine
# ---------------------------------------------------------------------------


class OutreachSequenceEngine:
    """
    Manages the SDR multi-touch outreach sequence.

    Phase 1 capabilities:
    - Enroll a prospect and dispatch first touch
    - Advance sequence with fixed-schedule timing
    - Dispatch touch via GHL (SMS workflow, email workflow, voicemail workflow)

    Phase 2 will add: Claude-generated personalized messages, AI timing.
    """

    SMS_MAX_LENGTH = 160  # TCPA-compliant SMS truncation

    def __init__(self, ghl_client: "EnhancedGHLClient") -> None:
        self._ghl = ghl_client
        self._sdr_workflow_sms = os.getenv("SDR_WORKFLOW_SMS_1", "")
        self._sdr_workflow_email = os.getenv("SDR_WORKFLOW_EMAIL_1", "")
        self._sdr_workflow_voicemail = os.getenv("SDR_WORKFLOW_VOICEMAIL_DROP", "")

    async def enroll_prospect(
        self,
        contact_id: str,
        location_id: str,
        lead_type: str = "unknown",
        sequence_variant: str = "default",
    ) -> OutreachRecord:
        """
        Enroll a prospect in the SDR sequence.

        Creates the OutreachRecord, dispatches SMS_1, and computes next_touch_at.
        Database persistence is handled by the caller (SDRAgent).
        """
        now = datetime.now(timezone.utc)
        record = OutreachRecord(
            contact_id=contact_id,
            location_id=location_id,
            current_step=SequenceStep.ENROLLED,
            enrolled_at=now,
            lead_type=lead_type,
            ab_variant=sequence_variant,
        )

        # Advance to first touch
        record = await self.advance_sequence(record, reply_received=False)
        logger.info(f"[SDR] Enrolled contact={contact_id} first_step={record.current_step.value}")
        return record

    async def advance_sequence(
        self,
        record: OutreachRecord,
        reply_received: bool = False,
        engagement_signal: Optional[str] = None,
    ) -> OutreachRecord:
        """
        Move to the next step in the sequence and dispatch the touch.

        If the current step is ENROLLED, dispatches SMS_1.
        Otherwise, moves to the next step in _STEP_ORDER.
        """
        if is_terminal_step(record.current_step):
            logger.info(
                f"[SDR] advance_sequence called on terminal step "
                f"contact={record.contact_id} step={record.current_step.value}"
            )
            return record

        next_step = get_next_step(record.current_step)
        if next_step is None:
            logger.info(f"[SDR] Sequence exhausted for contact={record.contact_id}")
            return record

        # Dispatch touch for the next step
        dispatched = await self.dispatch_touch(
            record=record,
            step=next_step,
            personalization_context={
                "lead_type": record.lead_type,
                "reply_received": reply_received,
                "engagement_signal": engagement_signal,
            },
        )

        if dispatched:
            record.current_step = next_step
            record.next_touch_at = self._compute_next_touch_at(next_step)

        return record

    async def dispatch_touch(
        self,
        record: OutreachRecord,
        step: SequenceStep,
        personalization_context: Dict[str, Any],
    ) -> bool:
        """
        Dispatch a single outreach touch via the appropriate GHL workflow.

        Returns True if dispatched successfully.
        """
        channel = _STEP_CHANNEL.get(step.value, "sms")
        workflow_id = self._get_workflow_id(channel)

        if not workflow_id:
            logger.warning(
                f"[SDR] No workflow ID for channel={channel} step={step.value} "
                f"contact={record.contact_id} — skipping dispatch"
            )
            return False

        try:
            await self._ghl.trigger_workflow(
                contact_id=record.contact_id,
                workflow_id=workflow_id,
                location_id=record.location_id,
                event_data={
                    "sdr_step": step.value,
                    "sdr_channel": channel,
                    "lead_type": record.lead_type,
                },
            )
            logger.info(f"[SDR] Dispatched step={step.value} channel={channel} contact={record.contact_id}")
            return True
        except Exception as exc:
            logger.error(f"[SDR] Dispatch failed step={step.value} contact={record.contact_id}: {exc}")
            return False

    def _get_workflow_id(self, channel: str) -> str:
        """Return the GHL workflow ID for a given channel."""
        return {
            "sms": self._sdr_workflow_sms,
            "email": self._sdr_workflow_email,
            "voicemail": self._sdr_workflow_voicemail,
        }.get(channel, "")

    def _compute_next_touch_at(self, step: SequenceStep) -> Optional[datetime]:
        """Compute when the next touch should fire based on config default wait times."""
        next_step = get_next_step(step)
        if next_step is None or is_terminal_step(next_step):
            return None
        wait_hours = _DEFAULT_MIN_WAIT.get(next_step.value, 24)
        return datetime.now(timezone.utc) + timedelta(hours=wait_hours)
