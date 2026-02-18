"""
SDR CadenceScheduler — cron-driven batch execution of due touches.

Runs on a 15-minute cron interval (called via POST /sdr/sequences/process-batch).
Phase 1: fixed config defaults for timing.
Phase 2: Claude-driven compute_next_touch_time().
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger

if TYPE_CHECKING:
    from ghl_real_estate_ai.services.sdr.outreach_sequence_engine import (
        OutreachRecord,
        OutreachSequenceEngine,
    )

logger = get_logger(__name__)


class CadenceScheduler:
    """
    Processes due outreach touches from the database and dispatches them.

    Interface mirrors JorgeFollowUpScheduler for consistency.
    """

    def __init__(
        self,
        sequence_engine: "OutreachSequenceEngine",
    ) -> None:
        self._engine = sequence_engine

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
        logger.info(
            f"[SDR] Webhook trigger contact={contact_id} "
            f"type={trigger_type} location={location_id}"
        )
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
                logger.error(
                    f"[SDR] CadenceScheduler error contact={record.contact_id}: {exc}"
                )
                errors += 1

        logger.info(
            f"[SDR] Batch complete: processed={processed} dispatched={dispatched} "
            f"skipped={skipped} errors={errors}"
        )
        return {
            "processed": processed,
            "dispatched": dispatched,
            "skipped": skipped,
            "errors": errors,
        }

    async def get_statistics(
        self,
        location_id: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Return basic scheduler statistics.
        Phase 3 will wire this into SDRPerformanceTracker rolling windows.
        """
        return {
            "location_id": location_id,
            "days": days,
            "note": "Full metrics available in Phase 3 (SDRPerformanceTracker)",
        }
