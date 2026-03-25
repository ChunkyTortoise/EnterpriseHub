"""
SDR CadenceScheduler — cron-driven batch execution of due touches.

Runs on a 15-minute cron interval (called via POST /sdr/sequences/process-batch).
Phase 1: fixed config defaults for timing.
Phase 2: Claude-driven compute_next_touch_time().
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger

if TYPE_CHECKING:
    from ghl_real_estate_ai.repositories.sdr_repository import SDRRepository
    from ghl_real_estate_ai.services.sdr.outreach_sequence_engine import (
        OutreachRecord,
        OutreachSequenceEngine,
    )

logger = get_logger(__name__)

# Business-hours constraints for touch scheduling
_BIZ_HOUR_START = 9  # 9 AM
_BIZ_HOUR_END = 19  # 7 PM
_BLOCKED_WEEKDAY = 6  # Sunday (Monday=0)
_MIN_TOUCH_GAP_HOURS = 4
_MAX_TOUCH_GAP_HOURS = 72


class CadenceScheduler:
    """
    Processes due outreach touches from the database and dispatches them.

    Interface mirrors JorgeFollowUpScheduler for consistency.
    """

    def __init__(
        self,
        sequence_engine: "OutreachSequenceEngine",
        repository: Optional["SDRRepository"] = None,
    ) -> None:
        self._engine = sequence_engine
        self._repo = repository

    async def process_webhook_trigger(
        self,
        contact_id: str,
        location_id: str,
        trigger_type: str,
        webhook_data: Dict[str, Any],
    ) -> None:
        """
        Handle a real-time trigger from a GHL workflow webhook.

        Called by the API route when GHL sends a ContactReply or StageChange event.
        Loads the sequence record and calls advance_sequence.
        """
        logger.info(f"[SDR] Webhook trigger contact={contact_id} type={trigger_type} location={location_id}")
        # Record retrieval and persistence are the responsibility of SDRAgent.
        # The scheduler focuses on scheduling logic only.

    async def process_due_touches(
        self,
        records: List["OutreachRecord"],
        batch_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Process a batch of due outreach records.

        In Phase 1, the caller (SDRAgent) handles DB queries and passes
        in-memory records. The scheduler drives the advance_sequence calls.

        Args:
            records: OutreachRecord list where next_touch_at <= now
            batch_size: max to process in one call

        Returns:
            dict with processed/dispatched/skipped/errors counts
        """
        processed = 0
        dispatched = 0
        skipped = 0
        errors = 0

        for record in records[:batch_size]:
            from ghl_real_estate_ai.services.sdr.outreach_sequence_engine import is_terminal_step

            if is_terminal_step(record.current_step):
                skipped += 1
                continue

            try:
                updated = await self._engine.advance_sequence(record, reply_received=False)
                processed += 1
                if updated.current_step != record.current_step:
                    dispatched += 1
            except Exception as exc:
                logger.error(f"[SDR] CadenceScheduler error contact={record.contact_id}: {exc}")
                errors += 1

        logger.info(
            f"[SDR] Batch complete: processed={processed} dispatched={dispatched} skipped={skipped} errors={errors}"
        )
        return {
            "processed": processed,
            "dispatched": dispatched,
            "skipped": skipped,
            "errors": errors,
        }

    async def fetch_and_process_due_touches(
        self,
        batch_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Query the DB for sequences where next_touch_at <= now, build
        OutreachRecord objects, and delegate to process_due_touches.

        Returns stats dict from process_due_touches.
        """
        if self._repo is None:
            logger.warning("[SDR] CadenceScheduler.fetch_and_process_due_touches called without repository")
            return {"processed": 0, "dispatched": 0, "skipped": 0, "errors": 0}

        from ghl_real_estate_ai.services.sdr.outreach_sequence_engine import (
            OutreachRecord,
            SequenceStep,
        )

        now = datetime.now(timezone.utc)
        due_sequences = await self._repo.get_due_sequences(cutoff=now, limit=batch_size)

        records: List["OutreachRecord"] = []
        for seq in due_sequences:
            try:
                step = SequenceStep(seq.current_step)
            except ValueError:
                step = SequenceStep.ENROLLED
            records.append(
                OutreachRecord(
                    contact_id=seq.contact_id,
                    location_id=seq.location_id,
                    current_step=step,
                    enrolled_at=seq.enrolled_at,
                    next_touch_at=seq.next_touch_at,
                    reply_count=seq.reply_count,
                    lead_type="unknown",
                    ab_variant=seq.ab_variant,
                    sequence_id=seq.id,
                )
            )

        return await self.process_due_touches(records=records, batch_size=batch_size)

    @staticmethod
    def compute_next_touch_time(
        base_delay_hours: float,
        reply_count: int = 0,
        last_reply_latency_minutes: Optional[float] = None,
        now: Optional[datetime] = None,
    ) -> datetime:
        """
        Heuristic next-touch scheduler.

        Rules:
        - Start from base_delay_hours (from step config)
        - Fast replier (latency < 30 min): reduce delay by 25%
        - Engaged prospect (reply_count >= 2): reduce delay by 15%
        - Clamp to [_MIN_TOUCH_GAP_HOURS, _MAX_TOUCH_GAP_HOURS]
        - Snap to business hours (9 AM - 7 PM, avoid Sunday)
        """
        now = now or datetime.now(timezone.utc)
        delay = base_delay_hours

        # Fast replier discount
        if last_reply_latency_minutes is not None and last_reply_latency_minutes < 30:
            delay *= 0.75

        # Engagement discount
        if reply_count >= 2:
            delay *= 0.85

        # Clamp
        delay = max(_MIN_TOUCH_GAP_HOURS, min(delay, _MAX_TOUCH_GAP_HOURS))

        candidate = now + timedelta(hours=delay)

        # Snap to business hours
        candidate = _snap_to_business_hours(candidate)
        return candidate

    async def get_statistics(
        self,
        location_id: Optional[str] = None,
        days: int = 30,
        repository: Optional["SDRRepository"] = None,
    ) -> Dict[str, Any]:
        """Return SDR performance statistics via SDRPerformanceTracker when repo is available."""
        if repository is not None:
            from ghl_real_estate_ai.services.sdr.performance_tracker import SDRPerformanceTracker

            tracker = SDRPerformanceTracker(repository)
            stats = await tracker.get_stats(location_id=location_id, days=days)
            return stats.model_dump()
        return {
            "location_id": location_id,
            "days": days,
            "note": "Pass repository= for live DB metrics",
        }


def _snap_to_business_hours(dt: datetime) -> datetime:
    """Move *dt* to the next valid business-hour slot (9 AM-7 PM, no Sunday)."""
    # If before business hours, move to start
    if dt.hour < _BIZ_HOUR_START:
        dt = dt.replace(hour=_BIZ_HOUR_START, minute=0, second=0, microsecond=0)
    # If after business hours, move to next day start
    elif dt.hour >= _BIZ_HOUR_END:
        dt = (dt + timedelta(days=1)).replace(hour=_BIZ_HOUR_START, minute=0, second=0, microsecond=0)
    # Skip Sunday
    while dt.weekday() == _BLOCKED_WEEKDAY:
        dt = (dt + timedelta(days=1)).replace(hour=_BIZ_HOUR_START, minute=0, second=0, microsecond=0)
    return dt
