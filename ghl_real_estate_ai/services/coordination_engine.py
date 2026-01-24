"""
Bot Coordination Engine for Jorge's Real Estate AI Platform

Handles bot handoff requests, coaching opportunities, and context synchronization
for seamless coordination across the Jorge bot ecosystem.

Features:
- Bot-to-bot handoff orchestration with context transfer
- Real-time coaching opportunity detection and delivery
- Context synchronization across active bot sessions
- Performance metrics and coordination analytics
- WebSocket event integration for real-time updates
"""

import asyncio
import time
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)


class HandoffStatus(Enum):
    """Bot handoff status levels."""
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CoachingUrgency(Enum):
    """Coaching delivery urgency levels."""
    IMMEDIATE = "immediate"
    NEXT_MESSAGE = "next_message"
    INFORMATIONAL = "informational"


@dataclass
class BotSession:
    """Active bot session tracking."""
    session_id: str
    bot_type: str
    conversation_id: str
    contact_id: str
    location_id: str
    started_at: datetime
    last_activity: datetime
    current_step: Optional[str] = None
    context_data: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HandoffRequest:
    """Bot handoff request data."""
    handoff_id: str
    conversation_id: str
    from_bot: str
    to_bot: str
    contact_id: str
    location_id: str
    handoff_reason: str
    urgency: str
    context_transfer: Dict[str, Any]
    requested_at: datetime
    status: HandoffStatus = HandoffStatus.REQUESTED
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class CoachingRequest:
    """Real-time coaching request data."""
    coaching_id: str
    conversation_id: str
    coaching_type: str
    coaching_message: str
    urgency: CoachingUrgency
    target_bot: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    delivered_at: Optional[datetime] = None
    acknowledged: bool = False


class CoordinationEngine:
    """
    Bot Coordination Engine for Jorge's AI Platform

    Orchestrates coordination between Jorge bots including handoffs,
    coaching, and context synchronization for seamless user experiences.
    """

    def __init__(self):
        self.event_publisher = get_event_publisher()
        self.cache_service = get_cache_service()

        # Session tracking
        self.active_sessions: Dict[str, BotSession] = {}
        self.conversation_sessions: Dict[str, List[str]] = {}  # conversation_id -> session_ids

        # Handoff management
        self.active_handoffs: Dict[str, HandoffRequest] = {}
        self.handoff_history: List[HandoffRequest] = []

        # Coaching management
        self.pending_coaching: Dict[str, List[CoachingRequest]] = {}  # conversation_id -> coaching requests
        self.coaching_history: List[CoachingRequest] = []

        # Performance metrics
        self.metrics = {
            "total_handoffs": 0,
            "successful_handoffs": 0,
            "failed_handoffs": 0,
            "avg_handoff_time_ms": 0.0,
            "coaching_opportunities_detected": 0,
            "coaching_delivered": 0,
            "active_coordinations": 0,
            "context_syncs": 0
        }

        # Configuration
        self.handoff_timeout_minutes = 5
        self.max_concurrent_sessions = 50
        self.coaching_queue_size = 100

        logger.info("Bot Coordination Engine initialized")

    async def register_bot_session(
        self,
        bot_type: str,
        conversation_id: str,
        contact_id: str,
        location_id: str,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Register a new bot session for coordination tracking."""
        session_id = f"{bot_type}_{conversation_id}_{int(time.time())}"

        session = BotSession(
            session_id=session_id,
            bot_type=bot_type,
            conversation_id=conversation_id,
            contact_id=contact_id,
            location_id=location_id,
            started_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc),
            context_data=initial_context or {}
        )

        self.active_sessions[session_id] = session

        # Track by conversation
        if conversation_id not in self.conversation_sessions:
            self.conversation_sessions[conversation_id] = []
        self.conversation_sessions[conversation_id].append(session_id)

        # Emit session registration event
        await self.event_publisher.publish_bot_status_update(
            bot_type=bot_type,
            contact_id=contact_id,
            status="active",
            current_step="session_started"
        )

        await self._emit_coordination_status_update("session_registered", {
            "session_id": session_id,
            "bot_type": bot_type,
            "conversation_id": conversation_id
        })

        logger.info(f"Bot session registered: {session_id} ({bot_type})")
        return session_id

    async def update_session_activity(
        self,
        session_id: str,
        current_step: Optional[str] = None,
        context_update: Optional[Dict[str, Any]] = None,
        performance_metrics: Optional[Dict[str, Any]] = None
    ):
        """Update session activity and context."""
        if session_id not in self.active_sessions:
            logger.warning(f"Attempt to update unknown session: {session_id}")
            return

        session = self.active_sessions[session_id]
        session.last_activity = datetime.now(timezone.utc)

        if current_step:
            session.current_step = current_step

        if context_update:
            session.context_data.update(context_update)

        if performance_metrics:
            session.performance_metrics.update(performance_metrics)

        logger.debug(f"Updated session activity: {session_id}")

    async def request_bot_handoff(
        self,
        conversation_id: str,
        from_bot: str,
        to_bot: str,
        contact_id: str,
        location_id: str,
        handoff_reason: str,
        context_transfer: Dict[str, Any],
        urgency: str = "normal"
    ) -> str:
        """Request a bot handoff with context transfer."""
        handoff_id = f"handoff_{int(time.time() * 1000)}_{conversation_id}"

        handoff_request = HandoffRequest(
            handoff_id=handoff_id,
            conversation_id=conversation_id,
            from_bot=from_bot,
            to_bot=to_bot,
            contact_id=contact_id,
            location_id=location_id,
            handoff_reason=handoff_reason,
            urgency=urgency,
            context_transfer=context_transfer,
            requested_at=datetime.now(timezone.utc)
        )

        self.active_handoffs[handoff_id] = handoff_request
        self.metrics["total_handoffs"] += 1

        # Emit handoff request event
        await self.event_publisher.publish_bot_handoff_request(
            handoff_id=handoff_id,
            from_bot=from_bot,
            to_bot=to_bot,
            contact_id=contact_id,
            handoff_reason=handoff_reason,
            context_transfer=context_transfer,
            urgency=urgency,
            location_id=location_id
        )

        # Start handoff timeout monitoring
        asyncio.create_task(self._monitor_handoff_timeout(handoff_id))

        logger.info(f"Bot handoff requested: {from_bot} → {to_bot} (ID: {handoff_id})")
        return handoff_id

    async def accept_bot_handoff(self, handoff_id: str) -> bool:
        """Accept a bot handoff request."""
        if handoff_id not in self.active_handoffs:
            logger.warning(f"Attempt to accept unknown handoff: {handoff_id}")
            return False

        handoff = self.active_handoffs[handoff_id]
        if handoff.status != HandoffStatus.REQUESTED:
            logger.warning(f"Handoff {handoff_id} not in requested state: {handoff.status}")
            return False

        handoff.status = HandoffStatus.ACCEPTED

        # Emit handoff accepted event
        await self._emit_coordination_event(
            "BOT_HANDOFF_ACCEPTED",
            {
                "handoff_id": handoff_id,
                "from_bot": handoff.from_bot,
                "to_bot": handoff.to_bot,
                "conversation_id": handoff.conversation_id
            }
        )

        logger.info(f"Bot handoff accepted: {handoff_id}")
        return True

    async def complete_bot_handoff(
        self,
        handoff_id: str,
        success: bool,
        error_message: Optional[str] = None
    ) -> bool:
        """Complete a bot handoff."""
        if handoff_id not in self.active_handoffs:
            logger.warning(f"Attempt to complete unknown handoff: {handoff_id}")
            return False

        handoff = self.active_handoffs[handoff_id]
        handoff.status = HandoffStatus.COMPLETED if success else HandoffStatus.FAILED
        handoff.completed_at = datetime.now(timezone.utc)
        handoff.error_message = error_message

        # Update metrics
        if success:
            self.metrics["successful_handoffs"] += 1
            handoff_time = (handoff.completed_at - handoff.requested_at).total_seconds() * 1000
            self.metrics["avg_handoff_time_ms"] = (
                (self.metrics["avg_handoff_time_ms"] * (self.metrics["successful_handoffs"] - 1) + handoff_time) /
                self.metrics["successful_handoffs"]
            )
        else:
            self.metrics["failed_handoffs"] += 1

        # Emit handoff completion event
        await self._emit_coordination_event(
            "BOT_HANDOFF_COMPLETED",
            {
                "handoff_id": handoff_id,
                "from_bot": handoff.from_bot,
                "to_bot": handoff.to_bot,
                "conversation_id": handoff.conversation_id,
                "success": success,
                "error_message": error_message
            }
        )

        # Move to history
        self.handoff_history.append(handoff)
        del self.active_handoffs[handoff_id]

        logger.info(f"Bot handoff completed: {handoff_id} ({'success' if success else 'failed'})")
        return True

    async def detect_coaching_opportunity(
        self,
        conversation_id: str,
        coaching_type: str,
        coaching_message: str,
        urgency: CoachingUrgency = CoachingUrgency.INFORMATIONAL,
        target_bot: Optional[str] = None
    ) -> str:
        """Detect and queue a coaching opportunity."""
        coaching_id = f"coaching_{int(time.time() * 1000)}_{conversation_id}"

        coaching_request = CoachingRequest(
            coaching_id=coaching_id,
            conversation_id=conversation_id,
            coaching_type=coaching_type,
            coaching_message=coaching_message,
            urgency=urgency,
            target_bot=target_bot
        )

        # Queue coaching request
        if conversation_id not in self.pending_coaching:
            self.pending_coaching[conversation_id] = []

        self.pending_coaching[conversation_id].append(coaching_request)
        self.metrics["coaching_opportunities_detected"] += 1

        # Emit coaching opportunity detected event
        await self._emit_coordination_event(
            "COACHING_OPPORTUNITY_DETECTED",
            {
                "coaching_id": coaching_id,
                "conversation_id": conversation_id,
                "coaching_type": coaching_type,
                "urgency": urgency.value,
                "target_bot": target_bot
            }
        )

        # Auto-deliver immediate coaching
        if urgency == CoachingUrgency.IMMEDIATE:
            await self.deliver_coaching(coaching_id)

        logger.info(f"Coaching opportunity detected: {coaching_type} (ID: {coaching_id})")
        return coaching_id

    async def deliver_coaching(self, coaching_id: str) -> bool:
        """Deliver coaching to the target bot."""
        # Find coaching request
        coaching_request = None
        conversation_id = None

        for conv_id, coaching_list in self.pending_coaching.items():
            for coaching in coaching_list:
                if coaching.coaching_id == coaching_id:
                    coaching_request = coaching
                    conversation_id = conv_id
                    break
            if coaching_request:
                break

        if not coaching_request:
            logger.warning(f"Coaching request not found: {coaching_id}")
            return False

        # Mark as delivered
        coaching_request.delivered_at = datetime.now(timezone.utc)
        self.metrics["coaching_delivered"] += 1

        # Emit coaching accepted event
        await self._emit_coordination_event(
            "COACHING_ACCEPTED",
            {
                "coaching_id": coaching_id,
                "conversation_id": conversation_id,
                "coaching_type": coaching_request.coaching_type,
                "coaching_message": coaching_request.coaching_message
            }
        )

        # Move to history
        self.coaching_history.append(coaching_request)
        if conversation_id in self.pending_coaching:
            self.pending_coaching[conversation_id] = [
                c for c in self.pending_coaching[conversation_id]
                if c.coaching_id != coaching_id
            ]

        logger.info(f"Coaching delivered: {coaching_id}")
        return True

    async def sync_context_across_bots(self, conversation_id: str, context_update: Dict[str, Any]):
        """Synchronize context across all active bots for a conversation."""
        if conversation_id not in self.conversation_sessions:
            logger.warning(f"No active sessions for conversation: {conversation_id}")
            return

        session_ids = self.conversation_sessions[conversation_id]
        updated_sessions = []

        for session_id in session_ids:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.context_data.update(context_update)
                session.last_activity = datetime.now(timezone.utc)
                updated_sessions.append({
                    "session_id": session_id,
                    "bot_type": session.bot_type
                })

        self.metrics["context_syncs"] += 1

        # Emit context sync event
        await self._emit_coordination_event(
            "CONTEXT_SYNC_UPDATE",
            {
                "conversation_id": conversation_id,
                "context_update": context_update,
                "updated_sessions": updated_sessions,
                "sync_timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

        logger.info(f"Context synchronized across {len(updated_sessions)} sessions for conversation {conversation_id}")

    async def deregister_bot_session(self, session_id: str):
        """Deregister a bot session."""
        if session_id not in self.active_sessions:
            logger.warning(f"Attempt to deregister unknown session: {session_id}")
            return

        session = self.active_sessions[session_id]
        conversation_id = session.conversation_id

        # Remove from active sessions
        del self.active_sessions[session_id]

        # Remove from conversation tracking
        if conversation_id in self.conversation_sessions:
            self.conversation_sessions[conversation_id] = [
                sid for sid in self.conversation_sessions[conversation_id]
                if sid != session_id
            ]
            if not self.conversation_sessions[conversation_id]:
                del self.conversation_sessions[conversation_id]

        # Emit session deregistration event
        await self._emit_coordination_status_update("session_deregistered", {
            "session_id": session_id,
            "bot_type": session.bot_type,
            "conversation_id": conversation_id,
            "session_duration": (datetime.now(timezone.utc) - session.started_at).total_seconds()
        })

        logger.info(f"Bot session deregistered: {session_id}")

    async def _monitor_handoff_timeout(self, handoff_id: str):
        """Monitor handoff timeout and handle failures."""
        await asyncio.sleep(self.handoff_timeout_minutes * 60)

        if handoff_id in self.active_handoffs:
            handoff = self.active_handoffs[handoff_id]
            if handoff.status == HandoffStatus.REQUESTED:
                await self.complete_bot_handoff(
                    handoff_id,
                    success=False,
                    error_message=f"Handoff timed out after {self.handoff_timeout_minutes} minutes"
                )

    async def _emit_coordination_event(self, event_type: str, data: Dict[str, Any]):
        """Emit coordination-related events."""
        # Map internal events to WebSocket events
        event_mapping = {
            "BOT_HANDOFF_ACCEPTED": "bot_handoff_accepted",
            "BOT_HANDOFF_COMPLETED": "bot_handoff_completed",
            "COACHING_OPPORTUNITY_DETECTED": "coaching_opportunity_detected",
            "COACHING_ACCEPTED": "coaching_accepted",
            "CONTEXT_SYNC_UPDATE": "context_sync_update"
        }

        websocket_event = event_mapping.get(event_type, event_type.lower())

        # Emit via event publisher (would need appropriate event type in enum)
        await self._emit_coordination_status_update(websocket_event, data)

    async def _emit_coordination_status_update(self, status_type: str, data: Dict[str, Any]):
        """Emit coordination status update via WebSocket."""
        # Use the existing system alert for now - in production would have dedicated coordination events
        from ghl_real_estate_ai.services.event_publisher import publish_system_alert
        await publish_system_alert(
            alert_type="coordination_update",
            message=f"Coordination event: {status_type}",
            severity="info",
            details=data
        )

    def get_coordination_metrics(self) -> Dict[str, Any]:
        """Get coordination engine performance metrics."""
        self.metrics["active_coordinations"] = len(self.active_sessions)

        return {
            **self.metrics,
            "active_sessions": len(self.active_sessions),
            "active_handoffs": len(self.active_handoffs),
            "pending_coaching": sum(len(coaching_list) for coaching_list in self.pending_coaching.values()),
            "conversation_count": len(self.conversation_sessions),
            "handoff_success_rate": (
                self.metrics["successful_handoffs"] / max(1, self.metrics["total_handoffs"])
            ),
            "coaching_delivery_rate": (
                self.metrics["coaching_delivered"] / max(1, self.metrics["coaching_opportunities_detected"])
            )
        }

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get list of active bot sessions."""
        return [
            {
                "session_id": session.session_id,
                "bot_type": session.bot_type,
                "conversation_id": session.conversation_id,
                "contact_id": session.contact_id,
                "location_id": session.location_id,
                "started_at": session.started_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "current_step": session.current_step,
                "performance_metrics": session.performance_metrics
            }
            for session in self.active_sessions.values()
        ]

    def get_conversation_sessions(self, conversation_id: str) -> List[BotSession]:
        """Get all active sessions for a conversation."""
        if conversation_id not in self.conversation_sessions:
            return []

        return [
            self.active_sessions[session_id]
            for session_id in self.conversation_sessions[conversation_id]
            if session_id in self.active_sessions
        ]

    async def cleanup_stale_sessions(self, max_age_minutes: int = 60):
        """Clean up stale sessions that haven't been active."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)
        stale_sessions = []

        for session_id, session in self.active_sessions.items():
            if session.last_activity < cutoff_time:
                stale_sessions.append(session_id)

        for session_id in stale_sessions:
            await self.deregister_bot_session(session_id)

        if stale_sessions:
            logger.info(f"Cleaned up {len(stale_sessions)} stale bot sessions")


# Global instance
_coordination_engine = None


def get_coordination_engine() -> CoordinationEngine:
    """Get singleton CoordinationEngine instance."""
    global _coordination_engine
    if _coordination_engine is None:
        _coordination_engine = CoordinationEngine()
    return _coordination_engine


# Convenience functions
async def register_bot_session(bot_type: str, conversation_id: str, contact_id: str, location_id: str, **kwargs) -> str:
    """Register a new bot session for coordination tracking."""
    engine = get_coordination_engine()
    return await engine.register_bot_session(bot_type, conversation_id, contact_id, location_id, **kwargs)


async def request_bot_handoff(conversation_id: str, from_bot: str, to_bot: str, contact_id: str, location_id: str, handoff_reason: str, context_transfer: Dict[str, Any], **kwargs) -> str:
    """Request a bot handoff with context transfer."""
    engine = get_coordination_engine()
    return await engine.request_bot_handoff(conversation_id, from_bot, to_bot, contact_id, location_id, handoff_reason, context_transfer, **kwargs)


async def detect_coaching_opportunity(conversation_id: str, coaching_type: str, coaching_message: str, **kwargs) -> str:
    """Detect and queue a coaching opportunity."""
    engine = get_coordination_engine()
    return await engine.detect_coaching_opportunity(conversation_id, coaching_type, coaching_message, **kwargs)


async def get_coordination_metrics() -> Dict[str, Any]:
    """Get coordination engine performance metrics."""
    engine = get_coordination_engine()
    return engine.get_coordination_metrics()