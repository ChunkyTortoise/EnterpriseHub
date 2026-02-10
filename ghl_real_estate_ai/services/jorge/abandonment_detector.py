"""Lead abandonment detection service.

Identifies leads that have gone silent (no response >24h) and determines
which recovery stage they're eligible for based on abandonment duration.

Abandonment stages:
- 24h: Initial silence detection
- 3d: First recovery attempt
- 7d: Second recovery attempt
- 14d: Third recovery attempt
- 30d: Final recovery attempt (Hail Mary)
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AbandonmentStage(str, Enum):
    """Recovery stage based on silence duration."""

    HOUR_24 = "24h"
    DAY_3 = "3d"
    DAY_7 = "7d"
    DAY_14 = "14d"
    DAY_30 = "30d"


# Stage thresholds in seconds
STAGE_THRESHOLDS = {
    AbandonmentStage.HOUR_24: 24 * 3600,
    AbandonmentStage.DAY_3: 3 * 24 * 3600,
    AbandonmentStage.DAY_7: 7 * 24 * 3600,
    AbandonmentStage.DAY_14: 14 * 24 * 3600,
    AbandonmentStage.DAY_30: 30 * 24 * 3600,
}


@dataclass
class AbandonedContact:
    """Contact that has gone silent and is eligible for recovery."""

    contact_id: str
    location_id: str
    bot_type: str  # "lead", "buyer", "seller"
    last_contact_timestamp: float
    silence_duration_hours: float
    current_stage: AbandonmentStage
    recovery_attempt_count: int
    contact_metadata: Dict[str, Any]

    @property
    def silence_duration_days(self) -> float:
        """Get silence duration in days."""
        return self.silence_duration_hours / 24.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contact_id": self.contact_id,
            "location_id": self.location_id,
            "bot_type": self.bot_type,
            "last_contact_timestamp": self.last_contact_timestamp,
            "last_contact_date": datetime.fromtimestamp(
                self.last_contact_timestamp, tz=timezone.utc
            ).isoformat(),
            "silence_duration_hours": round(self.silence_duration_hours, 2),
            "silence_duration_days": round(self.silence_duration_days, 2),
            "current_stage": self.current_stage.value,
            "recovery_attempt_count": self.recovery_attempt_count,
            "contact_metadata": self.contact_metadata,
        }


class AbandonmentDetector:
    """Detects silent leads and determines recovery eligibility.

    Uses GHL contact data and abandonment_events table to identify:
    1. Leads with no inbound message >24h
    2. Current abandonment stage (24h/3d/7d/14d/30d)
    3. Recovery attempts already made
    4. Next eligible recovery action
    """

    def __init__(self, ghl_client=None, db_pool=None):
        """Initialize detector with GHL client and database pool.

        Args:
            ghl_client: EnhancedGHLClient for fetching contact conversation history
            db_pool: asyncpg connection pool for abandonment_events table
        """
        self._ghl_client = ghl_client
        self._db_pool = db_pool
        logger.info("AbandonmentDetector initialized")

    async def detect_abandoned_contacts(
        self,
        location_id: str,
        max_contacts: int = 100,
    ) -> List[AbandonedContact]:
        """Scan for abandoned contacts eligible for recovery.

        Args:
            location_id: GHL location ID to scan
            max_contacts: Maximum number of contacts to return

        Returns:
            List of AbandonedContact objects sorted by priority (longest silent first)
        """
        if not self._ghl_client:
            logger.warning("No GHL client configured, returning empty list")
            return []

        abandoned_contacts = []
        current_time = time.time()

        try:
            # Get recent conversations from GHL
            # Note: This is a simplified approach - in production, you'd want to:
            # 1. Query GHL for contacts with recent bot interactions
            # 2. Filter by last_message_time from conversation history
            # 3. Cross-reference with abandonment_events table for recovery attempts

            # For now, we'll query the abandonment_events table to find contacts
            # that are due for recovery based on stage thresholds
            if self._db_pool:
                abandoned_contacts = await self._query_abandoned_from_db(
                    location_id, current_time, max_contacts
                )
            else:
                logger.warning("No database pool configured, skipping DB query")

        except Exception as exc:
            logger.error(f"Failed to detect abandoned contacts: {exc}")

        logger.info(
            f"Detected {len(abandoned_contacts)} abandoned contacts for location {location_id}"
        )
        return abandoned_contacts

    async def _query_abandoned_from_db(
        self,
        location_id: str,
        current_time: float,
        max_contacts: int,
    ) -> List[AbandonedContact]:
        """Query abandonment_events table for contacts due for recovery.

        Logic:
        - Find contacts with last_contact_timestamp >24h ago
        - Determine current stage based on silence duration
        - Check if already attempted recovery at this stage
        - Return contacts eligible for next recovery attempt
        """
        abandoned = []

        try:
            # Query abandonment_events for contacts with active abandonment tracking
            rows = await self._db_pool.fetch(
                """
                SELECT
                    contact_id,
                    location_id,
                    bot_type,
                    last_contact_timestamp,
                    current_stage,
                    recovery_attempt_count,
                    metadata
                FROM abandonment_events
                WHERE location_id = $1
                  AND last_contact_timestamp < $2
                ORDER BY last_contact_timestamp ASC
                LIMIT $3
                """,
                location_id,
                current_time - STAGE_THRESHOLDS[AbandonmentStage.HOUR_24],
                max_contacts,
            )

            for row in rows:
                silence_duration_sec = current_time - row["last_contact_timestamp"]
                silence_duration_hours = silence_duration_sec / 3600.0

                # Determine current stage based on silence duration
                current_stage = self._determine_stage(silence_duration_sec)

                # Check if we should attempt recovery at this stage
                # Only include if current_stage is ahead of last recovery stage
                last_recovery_stage = AbandonmentStage(row["current_stage"]) if row["current_stage"] else None

                if self._should_attempt_recovery(current_stage, last_recovery_stage):
                    abandoned.append(
                        AbandonedContact(
                            contact_id=row["contact_id"],
                            location_id=row["location_id"],
                            bot_type=row["bot_type"],
                            last_contact_timestamp=row["last_contact_timestamp"],
                            silence_duration_hours=silence_duration_hours,
                            current_stage=current_stage,
                            recovery_attempt_count=row["recovery_attempt_count"],
                            contact_metadata=row["metadata"] or {},
                        )
                    )

        except Exception as exc:
            logger.error(f"Database query failed: {exc}")

        return abandoned

    def _determine_stage(self, silence_duration_sec: float) -> AbandonmentStage:
        """Determine abandonment stage based on silence duration."""
        if silence_duration_sec >= STAGE_THRESHOLDS[AbandonmentStage.DAY_30]:
            return AbandonmentStage.DAY_30
        elif silence_duration_sec >= STAGE_THRESHOLDS[AbandonmentStage.DAY_14]:
            return AbandonmentStage.DAY_14
        elif silence_duration_sec >= STAGE_THRESHOLDS[AbandonmentStage.DAY_7]:
            return AbandonmentStage.DAY_7
        elif silence_duration_sec >= STAGE_THRESHOLDS[AbandonmentStage.DAY_3]:
            return AbandonmentStage.DAY_3
        else:
            return AbandonmentStage.HOUR_24

    def _should_attempt_recovery(
        self,
        current_stage: AbandonmentStage,
        last_recovery_stage: Optional[AbandonmentStage],
    ) -> bool:
        """Check if recovery should be attempted at current stage.

        Only attempt recovery if we haven't already recovered at this stage or later.
        """
        if last_recovery_stage is None:
            # Never attempted recovery, try at any stage
            return True

        # Define stage ordering
        stage_order = [
            AbandonmentStage.HOUR_24,
            AbandonmentStage.DAY_3,
            AbandonmentStage.DAY_7,
            AbandonmentStage.DAY_14,
            AbandonmentStage.DAY_30,
        ]

        current_idx = stage_order.index(current_stage)
        last_recovery_idx = stage_order.index(last_recovery_stage)

        # Only recover if current stage is ahead of last recovery
        return current_idx > last_recovery_idx

    async def mark_recovery_attempted(
        self,
        contact_id: str,
        stage: AbandonmentStage,
    ) -> None:
        """Mark that a recovery attempt was made for a contact at a specific stage.

        Updates abandonment_events table with recovery attempt metadata.
        """
        if not self._db_pool:
            logger.warning("No database pool, cannot mark recovery attempt")
            return

        try:
            await self._db_pool.execute(
                """
                UPDATE abandonment_events
                SET current_stage = $2,
                    recovery_attempt_count = recovery_attempt_count + 1,
                    updated_at = NOW()
                WHERE contact_id = $1
                """,
                contact_id,
                stage.value,
            )
            logger.info(f"Marked recovery attempt for {contact_id} at stage {stage.value}")
        except Exception as exc:
            logger.error(f"Failed to mark recovery attempt: {exc}")

    async def record_abandonment(
        self,
        contact_id: str,
        location_id: str,
        bot_type: str,
        last_contact_timestamp: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record or update abandonment event for a contact.

        Called when we detect a lead has gone silent or when updating
        last contact time after a response.
        """
        if not self._db_pool:
            logger.warning("No database pool, cannot record abandonment")
            return

        try:
            await self._db_pool.execute(
                """
                INSERT INTO abandonment_events
                    (contact_id, location_id, bot_type, last_contact_timestamp, current_stage, recovery_attempt_count, metadata)
                VALUES ($1, $2, $3, $4, $5, 0, $6)
                ON CONFLICT (contact_id)
                DO UPDATE SET
                    last_contact_timestamp = $4,
                    bot_type = $3,
                    metadata = $6,
                    updated_at = NOW()
                """,
                contact_id,
                location_id,
                bot_type,
                last_contact_timestamp,
                AbandonmentStage.HOUR_24.value,  # Start at 24h stage
                metadata or {},
            )
        except Exception as exc:
            logger.error(f"Failed to record abandonment: {exc}")

    async def clear_abandonment(self, contact_id: str) -> None:
        """Clear abandonment tracking for a contact that has re-engaged.

        Called when a previously silent lead responds.
        """
        if not self._db_pool:
            return

        try:
            await self._db_pool.execute(
                """
                DELETE FROM abandonment_events
                WHERE contact_id = $1
                """,
                contact_id,
            )
            logger.info(f"Cleared abandonment tracking for {contact_id}")
        except Exception as exc:
            logger.error(f"Failed to clear abandonment: {exc}")


# Singleton instance
_detector: Optional[AbandonmentDetector] = None


def get_abandonment_detector(ghl_client=None, db_pool=None) -> AbandonmentDetector:
    """Get or create singleton abandonment detector."""
    global _detector
    if _detector is None:
        _detector = AbandonmentDetector(ghl_client=ghl_client, db_pool=db_pool)
    return _detector
