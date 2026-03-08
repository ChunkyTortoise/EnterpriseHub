"""Async CRUD repository for SDR pipeline persistence.

All operations use SQLAlchemy ORM with ``AsyncSession``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ghl_real_estate_ai.models.sdr_models import (
    SDRObjectionLog,
    SDROutreachSequence,
    SDROutreachTouch,
    SDRProspect,
)

logger = logging.getLogger(__name__)

# Steps that mark a sequence as terminal (no longer active).
_TERMINAL_STEPS = frozenset({"qualified", "opted_out", "expired", "converted"})


class SDRRepository:
    """Repository for SDR prospect, sequence, touch, and objection data."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Prospects
    # ------------------------------------------------------------------

    async def upsert_prospect(
        self,
        contact_id: str,
        location_id: str,
        source: str,
        lead_type: str = "unknown",
        enrolled_at: Optional[datetime] = None,
    ) -> SDRProspect:
        """Insert or return existing prospect for contact+location pair."""
        enrolled = enrolled_at or datetime.now(timezone.utc)

        existing = await self.get_prospect_by_contact(contact_id, location_id)
        if existing is not None:
            # Update mutable fields on re-enroll
            existing.source = source
            existing.lead_type = lead_type
            await self._session.flush()
            return existing

        prospect = SDRProspect(
            contact_id=contact_id,
            location_id=location_id,
            source=source,
            lead_type=lead_type,
            enrolled_at=enrolled,
        )
        self._session.add(prospect)
        await self._session.flush()
        return prospect

    async def get_prospect(self, prospect_id: str) -> Optional[SDRProspect]:
        return await self._session.get(SDRProspect, prospect_id)

    async def get_prospect_by_contact(
        self, contact_id: str, location_id: str
    ) -> Optional[SDRProspect]:
        stmt = select(SDRProspect).where(
            SDRProspect.contact_id == contact_id,
            SDRProspect.location_id == location_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_scores(
        self, prospect_id: str, frs_score: float, pcs_score: float
    ) -> None:
        stmt = (
            update(SDRProspect)
            .where(SDRProspect.id == prospect_id)
            .values(
                frs_score=frs_score,
                pcs_score=pcs_score,
                last_scored_at=datetime.now(timezone.utc),
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()

    # ------------------------------------------------------------------
    # Sequences
    # ------------------------------------------------------------------

    async def create_sequence(
        self,
        prospect_id: str,
        contact_id: str,
        location_id: str,
        current_step: str,
        enrolled_at: Optional[datetime] = None,
        ab_variant: Optional[str] = None,
    ) -> SDROutreachSequence:
        enrolled = enrolled_at or datetime.now(timezone.utc)
        seq = SDROutreachSequence(
            prospect_id=prospect_id,
            contact_id=contact_id,
            location_id=location_id,
            current_step=current_step,
            enrolled_at=enrolled,
            ab_variant=ab_variant,
        )
        self._session.add(seq)
        await self._session.flush()
        return seq

    async def get_active_sequence(
        self, contact_id: str, location_id: str
    ) -> Optional[SDROutreachSequence]:
        stmt = select(SDROutreachSequence).where(
            SDROutreachSequence.contact_id == contact_id,
            SDROutreachSequence.location_id == location_id,
            SDROutreachSequence.current_step.notin_(_TERMINAL_STEPS),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_sequence_step(
        self,
        sequence_id: str,
        step: str,
        next_touch_at: Optional[datetime] = None,
    ) -> None:
        stmt = (
            update(SDROutreachSequence)
            .where(SDROutreachSequence.id == sequence_id)
            .values(current_step=step, next_touch_at=next_touch_at)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def increment_reply_count(self, sequence_id: str) -> None:
        stmt = (
            update(SDROutreachSequence)
            .where(SDROutreachSequence.id == sequence_id)
            .values(reply_count=SDROutreachSequence.reply_count + 1)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def get_due_sequences(
        self, cutoff: datetime, limit: int = 50
    ) -> List[SDROutreachSequence]:
        stmt = (
            select(SDROutreachSequence)
            .where(
                SDROutreachSequence.next_touch_at <= cutoff,
                SDROutreachSequence.current_step.notin_(_TERMINAL_STEPS),
            )
            .order_by(SDROutreachSequence.next_touch_at)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Touches
    # ------------------------------------------------------------------

    async def record_touch(
        self,
        sequence_id: str,
        contact_id: str,
        step: str,
        channel: str,
        message_body: Optional[str] = None,
    ) -> SDROutreachTouch:
        touch = SDROutreachTouch(
            sequence_id=sequence_id,
            contact_id=contact_id,
            step=step,
            channel=channel,
            message_body=message_body,
            sent_at=datetime.now(timezone.utc),
        )
        self._session.add(touch)
        await self._session.flush()
        return touch

    async def record_reply(
        self, touch_id: str, reply_body: str, replied_at: datetime
    ) -> None:
        touch = await self._session.get(SDROutreachTouch, touch_id)
        if touch is not None:
            touch.reply_body = reply_body  # uses encrypted setter
            touch.replied_at = replied_at
            await self._session.flush()

    async def get_touches_for_sequence(
        self, sequence_id: str
    ) -> List[SDROutreachTouch]:
        stmt = (
            select(SDROutreachTouch)
            .where(SDROutreachTouch.sequence_id == sequence_id)
            .order_by(SDROutreachTouch.sent_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_touches_for_contact(
        self, contact_id: str, limit: int = 20
    ) -> List[SDROutreachTouch]:
        stmt = (
            select(SDROutreachTouch)
            .where(SDROutreachTouch.contact_id == contact_id)
            .order_by(SDROutreachTouch.sent_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Objections
    # ------------------------------------------------------------------

    async def log_objection(
        self,
        contact_id: str,
        objection_type: str,
        raw_message: str,
        rebuttal_used: Optional[str] = None,
    ) -> SDRObjectionLog:
        obj = SDRObjectionLog(
            contact_id=contact_id,
            objection_type=objection_type,
            rebuttal_used=rebuttal_used,
        )
        obj.raw_message = raw_message  # uses encrypted setter
        self._session.add(obj)
        await self._session.flush()
        return obj

    async def get_objection_logs(
        self, contact_id: str
    ) -> List[SDRObjectionLog]:
        stmt = (
            select(SDRObjectionLog)
            .where(SDRObjectionLog.contact_id == contact_id)
            .order_by(SDRObjectionLog.logged_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Aggregation (analytics)
    # ------------------------------------------------------------------

    async def count_enrolled(
        self, location_id: Optional[str], since: datetime
    ) -> int:
        stmt = select(func.count(SDRProspect.id)).where(
            SDRProspect.enrolled_at >= since
        )
        if location_id is not None:
            stmt = stmt.where(SDRProspect.location_id == location_id)
        result = await self._session.execute(stmt)
        return result.scalar_one() or 0

    async def count_touches_sent(
        self, location_id: Optional[str], since: datetime
    ) -> int:
        stmt = select(func.count(SDROutreachTouch.id)).where(
            SDROutreachTouch.sent_at >= since
        )
        if location_id is not None:
            stmt = stmt.join(SDROutreachSequence).where(
                SDROutreachSequence.location_id == location_id
            )
        result = await self._session.execute(stmt)
        return result.scalar_one() or 0

    async def count_replies(
        self, location_id: Optional[str], since: datetime
    ) -> int:
        stmt = select(func.count(SDROutreachTouch.id)).where(
            SDROutreachTouch.replied_at.isnot(None),
            SDROutreachTouch.sent_at >= since,
        )
        if location_id is not None:
            stmt = stmt.join(SDROutreachSequence).where(
                SDROutreachSequence.location_id == location_id
            )
        result = await self._session.execute(stmt)
        return result.scalar_one() or 0

    async def count_by_step(
        self, location_id: Optional[str], since: datetime
    ) -> Dict[str, int]:
        stmt = (
            select(
                SDROutreachSequence.current_step,
                func.count(SDROutreachSequence.id),
            )
            .where(SDROutreachSequence.enrolled_at >= since)
            .group_by(SDROutreachSequence.current_step)
        )
        if location_id is not None:
            stmt = stmt.where(SDROutreachSequence.location_id == location_id)
        result = await self._session.execute(stmt)
        return {row[0]: row[1] for row in result.all()}

    async def objection_distribution(
        self, location_id: Optional[str], since: datetime
    ) -> Dict[str, int]:
        stmt = (
            select(
                SDRObjectionLog.objection_type,
                func.count(SDRObjectionLog.id),
            )
            .where(SDRObjectionLog.logged_at >= since)
            .group_by(SDRObjectionLog.objection_type)
        )
        if location_id is not None:
            # objection_logs don't have location_id, join through touches/sequences
            # Since objection_logs are per-contact only, filter via contact's prospect
            stmt = stmt.join(
                SDRProspect,
                SDRProspect.contact_id == SDRObjectionLog.contact_id,
            ).where(SDRProspect.location_id == location_id)
        result = await self._session.execute(stmt)
        return {row[0]: row[1] for row in result.all()}
