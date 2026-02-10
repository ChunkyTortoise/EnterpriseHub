"""
Jorge Handoff Outcome Publisher

Publishes handoff outcomes back to GHL as tags and custom fields,
making GHL the source-of-truth for handoff history.

When a handoff outcome is recorded, this service:
1. Adds an outcome tag (e.g., "Handoff-Lead-to-Buyer-Success")
2. Updates custom fields with outcome metadata
3. Batches updates to respect GHL rate limits (200 writes/min)
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class OutcomeUpdate:
    """Pending outcome update for batch processing."""

    contact_id: str
    source_bot: str
    target_bot: str
    outcome: str
    confidence: float
    timestamp: float


class OutcomePublisher:
    """Publishes handoff outcomes to GHL as tags and custom fields."""

    # GHL rate limit: 300 req/min, but we stay conservative at 200 writes/min
    MAX_WRITES_PER_MINUTE = 200
    BATCH_INTERVAL_SECONDS = 5.0

    # Custom field IDs for handoff metadata
    CUSTOM_FIELD_IDS = {
        "last_handoff_source": "handoff_source",
        "last_handoff_target": "handoff_target",
        "last_handoff_outcome": "handoff_outcome",
        "last_handoff_confidence": "handoff_confidence",
        "last_handoff_timestamp": "handoff_timestamp",
    }

    def __init__(self, ghl_client: Any):
        """Initialize outcome publisher with GHL client.

        Args:
            ghl_client: GHL client instance with add_tags and
                       update_custom_fields_batch methods.
        """
        self.ghl_client = ghl_client
        self._pending_updates: List[OutcomeUpdate] = []
        self._batch_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._write_timestamps: List[float] = []
        self._lock = asyncio.Lock()

    def start_batch_processor(self) -> None:
        """Start the background batch processor.

        Processes pending updates every BATCH_INTERVAL_SECONDS.
        """
        if self._is_running:
            logger.warning("Batch processor already running")
            return

        self._is_running = True
        self._batch_task = asyncio.create_task(self._batch_processor())
        logger.info("Outcome publisher batch processor started")

    async def stop_batch_processor(self) -> None:
        """Stop the background batch processor and flush pending updates."""
        if self._batch_task:
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass

        self._is_running = False

        # Flush remaining updates (even if was not running)
        await self._flush_all_pending()
        logger.info("Outcome publisher batch processor stopped")

    async def _flush_all_pending(self) -> None:
        """Flush all pending updates immediately, ignoring rate limits.

        Used during shutdown to ensure no updates are lost.
        """
        async with self._lock:
            batch = self._pending_updates[:]
            self._pending_updates = []

        success_count = 0
        for update in batch:
            if await self._publish_single_outcome(update):
                success_count += 1
                self._write_timestamps.append(time.time())

        if success_count > 0:
            logger.info(
                f"Flushed {success_count}/{len(batch)} pending handoff outcomes"
            )

    async def publish_handoff_outcome(
        self,
        contact_id: str,
        source_bot: str,
        target_bot: str,
        outcome: str,
        confidence: float,
        immediate: bool = False,
    ) -> bool:
        """Queue a handoff outcome for publication to GHL.

        Args:
            contact_id: GHL contact ID.
            source_bot: Source bot name (lead, buyer, seller).
            target_bot: Target bot name (lead, buyer, seller).
            outcome: Handoff outcome (successful, failed, timeout, reverted).
            confidence: Confidence score (0.0-1.0).
            immediate: If True, publish immediately instead of batching.

        Returns:
            True if queued/published successfully, False on error.
        """
        if not contact_id:
            logger.error("Cannot publish outcome: contact_id is required")
            return False

        valid_outcomes = {"successful", "failed", "reverted", "timeout"}
        if outcome not in valid_outcomes:
            logger.error(
                f"Cannot publish outcome: invalid outcome '{outcome}'. "
                f"Expected one of {valid_outcomes}"
            )
            return False

        update = OutcomeUpdate(
            contact_id=contact_id,
            source_bot=source_bot,
            target_bot=target_bot,
            outcome=outcome,
            confidence=confidence,
            timestamp=time.time(),
        )

        if immediate:
            return await self._publish_single_outcome(update)

        async with self._lock:
            self._pending_updates.append(update)

        logger.debug(
            f"Queued handoff outcome for publication: {source_bot}->{target_bot} "
            f"({outcome}) for contact {contact_id}"
        )
        return True

    async def _batch_processor(self) -> None:
        """Background task that processes pending updates in batches."""
        while self._is_running:
            try:
                await asyncio.sleep(self.BATCH_INTERVAL_SECONDS)
                await self._process_batch()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch processor: {e}", exc_info=True)

    async def _process_batch(self) -> None:
        """Process all pending updates, respecting rate limits."""
        async with self._lock:
            if not self._pending_updates:
                return

            # Rate limit check: remove timestamps older than 60 seconds
            now = time.time()
            self._write_timestamps = [
                ts for ts in self._write_timestamps if now - ts < 60
            ]

            # Calculate how many writes we can do
            available_capacity = self.MAX_WRITES_PER_MINUTE - len(self._write_timestamps)
            if available_capacity <= 0:
                logger.warning(
                    f"Rate limit reached: {len(self._write_timestamps)} writes "
                    f"in last 60s. Deferring batch."
                )
                return

            # Process up to available capacity
            batch = self._pending_updates[:available_capacity]
            self._pending_updates = self._pending_updates[available_capacity:]

        success_count = 0
        for update in batch:
            if await self._publish_single_outcome(update):
                success_count += 1
                self._write_timestamps.append(time.time())

        if success_count > 0:
            logger.info(
                f"Published {success_count}/{len(batch)} handoff outcomes to GHL"
            )

    async def _publish_single_outcome(self, update: OutcomeUpdate) -> bool:
        """Publish a single outcome update to GHL.

        Args:
            update: OutcomeUpdate to publish.

        Returns:
            True if successful, False on error.
        """
        try:
            # 1. Add outcome tag
            tag = self._format_outcome_tag(
                update.source_bot, update.target_bot, update.outcome
            )
            await self.ghl_client.add_tags(update.contact_id, [tag])

            # 2. Update custom fields
            custom_fields = {
                self.CUSTOM_FIELD_IDS["last_handoff_source"]: update.source_bot,
                self.CUSTOM_FIELD_IDS["last_handoff_target"]: update.target_bot,
                self.CUSTOM_FIELD_IDS["last_handoff_outcome"]: update.outcome,
                self.CUSTOM_FIELD_IDS["last_handoff_confidence"]: str(
                    round(update.confidence, 2)
                ),
                self.CUSTOM_FIELD_IDS["last_handoff_timestamp"]: str(
                    int(update.timestamp)
                ),
            }
            await self.ghl_client.update_custom_fields_batch(
                update.contact_id, custom_fields
            )

            logger.info(
                f"Published handoff outcome to GHL: {update.source_bot}->"
                f"{update.target_bot} ({update.outcome}) for contact "
                f"{update.contact_id}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to publish outcome for contact {update.contact_id}: {e}",
                exc_info=True,
            )
            return False

    @staticmethod
    def _format_outcome_tag(source_bot: str, target_bot: str, outcome: str) -> str:
        """Format outcome tag name.

        Args:
            source_bot: Source bot name.
            target_bot: Target bot name.
            outcome: Outcome (successful, failed, timeout, reverted).

        Returns:
            Formatted tag name, e.g., "Handoff-Lead-to-Buyer-Success".
        """
        source = source_bot.capitalize()
        target = target_bot.capitalize()
        outcome_cap = outcome.capitalize()
        return f"Handoff-{source}-to-{target}-{outcome_cap}"

    def get_stats(self) -> Dict[str, Any]:
        """Get publisher statistics.

        Returns:
            Dict with pending_updates count and writes_last_minute count.
        """
        now = time.time()
        recent_writes = [ts for ts in self._write_timestamps if now - ts < 60]
        return {
            "pending_updates": len(self._pending_updates),
            "writes_last_minute": len(recent_writes),
            "rate_limit_capacity": self.MAX_WRITES_PER_MINUTE - len(recent_writes),
        }
