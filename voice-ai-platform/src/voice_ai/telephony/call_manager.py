"""Call lifecycle management — state machine for call status transitions."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from voice_ai.models.call import Call, CallDirection, CallStatus

logger = logging.getLogger(__name__)

# Valid state transitions
VALID_TRANSITIONS: dict[CallStatus, set[CallStatus]] = {
    CallStatus.INITIATED: {CallStatus.RINGING, CallStatus.FAILED},
    CallStatus.RINGING: {CallStatus.IN_PROGRESS, CallStatus.NO_ANSWER, CallStatus.FAILED},
    CallStatus.IN_PROGRESS: {CallStatus.COMPLETED, CallStatus.FAILED},
    CallStatus.COMPLETED: set(),
    CallStatus.FAILED: set(),
    CallStatus.NO_ANSWER: set(),
}


class CallManager:
    """Manages call lifecycle: create, update status, end."""

    def __init__(self, db_session: Any):
        self.db = db_session

    async def create_call(
        self,
        tenant_id: str,
        direction: str,
        from_number: str,
        to_number: str,
        bot_type: str = "lead",
        twilio_call_sid: str | None = None,
        agent_persona_id: str | None = None,
    ) -> Call:
        """Create a new call record."""
        call = Call(
            id=uuid.uuid4(),
            tenant_id=uuid.UUID(tenant_id),
            direction=CallDirection(direction),
            from_number=from_number,
            to_number=to_number,
            bot_type=bot_type,
            twilio_call_sid=twilio_call_sid,
            agent_persona_id=uuid.UUID(agent_persona_id) if agent_persona_id else None,
            status=CallStatus.INITIATED,
        )
        self.db.add(call)
        await self.db.flush()
        logger.info("Call created: %s (%s, %s)", call.id, direction, bot_type)
        return call

    async def update_status(self, call_id: str, new_status: CallStatus) -> Call | None:
        """Update call status with state machine validation."""
        from sqlalchemy import select

        result = await self.db.execute(select(Call).where(Call.id == uuid.UUID(call_id)))
        call = result.scalar_one_or_none()
        if not call:
            logger.warning("Call not found: %s", call_id)
            return None

        current = call.status
        if new_status not in VALID_TRANSITIONS.get(current, set()):
            logger.warning(
                "Invalid state transition for call %s: %s -> %s", call_id, current, new_status
            )
            return None

        call.status = new_status

        if new_status in (CallStatus.COMPLETED, CallStatus.FAILED, CallStatus.NO_ANSWER):
            call.ended_at = datetime.now(UTC)
            if call.created_at and call.ended_at:
                call.duration_seconds = (call.ended_at - call.created_at).total_seconds()

        await self.db.flush()
        logger.info("Call %s status updated: %s -> %s", call_id, current, new_status)
        return call

    async def get_call(self, call_id: str) -> Call | None:
        """Get a call by ID."""
        from sqlalchemy import select

        result = await self.db.execute(select(Call).where(Call.id == uuid.UUID(call_id)))
        return result.scalar_one_or_none()

    async def get_call_by_sid(self, twilio_call_sid: str) -> Call | None:
        """Get a call by Twilio SID."""
        from sqlalchemy import select

        result = await self.db.execute(
            select(Call).where(Call.twilio_call_sid == twilio_call_sid)
        )
        return result.scalar_one_or_none()

    async def list_calls(
        self,
        tenant_id: str,
        status: CallStatus | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Call]:
        """List calls for a tenant with optional filtering."""
        from sqlalchemy import select

        query = select(Call).where(Call.tenant_id == uuid.UUID(tenant_id))
        if status:
            query = query.where(Call.status == status)
        query = query.order_by(Call.created_at.desc()).offset(offset).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_call_costs(
        self,
        call_id: str,
        cost_stt: float = 0,
        cost_tts: float = 0,
        cost_llm: float = 0,
        cost_telephony: float = 0,
    ) -> None:
        """Update cost tracking fields on a call."""
        from sqlalchemy import select

        result = await self.db.execute(select(Call).where(Call.id == uuid.UUID(call_id)))
        call = result.scalar_one_or_none()
        if call:
            call.cost_stt = cost_stt
            call.cost_tts = cost_tts
            call.cost_llm = cost_llm
            call.cost_telephony = cost_telephony
            await self.db.flush()
