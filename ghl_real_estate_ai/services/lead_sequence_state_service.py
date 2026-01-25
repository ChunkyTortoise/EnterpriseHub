"""
Lead Sequence State Service - Persistent tracking for 3-7-30 lead nurture sequences.

Manages sequence progression state in Redis to ensure continuity across conversation sessions.
Tracks which day each lead is on, completion status, and next scheduled actions.
"""
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from ghl_real_estate_ai.services.cache_service import get_cache_service, CacheService
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class SequenceDay(Enum):
    """Enumeration of sequence days in the 3-7-30 automation."""
    INITIAL = "initial"
    DAY_3 = "day_3"
    DAY_7 = "day_7"
    DAY_14 = "day_14"
    DAY_30 = "day_30"
    NURTURE = "nurture"
    QUALIFIED = "qualified"

class SequenceStatus(Enum):
    """Status of sequence execution."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"


# Valid state transitions for the sequence state machine
# Format: {from_status: [allowed_to_statuses]}
VALID_STATUS_TRANSITIONS: Dict[SequenceStatus, List[SequenceStatus]] = {
    SequenceStatus.PENDING: [SequenceStatus.IN_PROGRESS, SequenceStatus.PAUSED, SequenceStatus.FAILED],
    SequenceStatus.IN_PROGRESS: [SequenceStatus.COMPLETED, SequenceStatus.PAUSED, SequenceStatus.FAILED],
    SequenceStatus.PAUSED: [SequenceStatus.IN_PROGRESS, SequenceStatus.COMPLETED, SequenceStatus.FAILED],
    SequenceStatus.COMPLETED: [],  # Terminal state - no transitions allowed
    SequenceStatus.FAILED: [SequenceStatus.PENDING],  # Can retry from failed
}

# Valid day transitions for the sequence days
# Format: {from_day: [allowed_to_days]}
VALID_DAY_TRANSITIONS: Dict[SequenceDay, List[SequenceDay]] = {
    SequenceDay.INITIAL: [SequenceDay.DAY_3],
    SequenceDay.DAY_3: [SequenceDay.DAY_7, SequenceDay.QUALIFIED, SequenceDay.NURTURE],
    SequenceDay.DAY_7: [SequenceDay.DAY_14, SequenceDay.QUALIFIED, SequenceDay.NURTURE],
    SequenceDay.DAY_14: [SequenceDay.DAY_30, SequenceDay.QUALIFIED, SequenceDay.NURTURE],
    SequenceDay.DAY_30: [SequenceDay.NURTURE, SequenceDay.QUALIFIED],
    SequenceDay.NURTURE: [SequenceDay.QUALIFIED],  # Can still qualify from nurture
    SequenceDay.QUALIFIED: [],  # Terminal state
}


class InvalidStateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    def __init__(self, from_state: str, to_state: str, state_type: str = "status"):
        self.from_state = from_state
        self.to_state = to_state
        self.state_type = state_type
        super().__init__(
            f"Invalid {state_type} transition from '{from_state}' to '{to_state}'"
        )

@dataclass
class LeadSequenceState:
    """Complete state tracking for a lead's sequence progression."""
    lead_id: str
    current_day: SequenceDay
    sequence_status: SequenceStatus

    # Timeline tracking
    sequence_started_at: datetime
    last_action_at: Optional[datetime] = None
    next_scheduled_at: Optional[datetime] = None

    # Progress tracking
    day_3_completed: bool = False
    day_7_completed: bool = False
    day_14_completed: bool = False
    day_30_completed: bool = False

    # Action tracking
    day_3_delivered_at: Optional[datetime] = None
    day_7_delivered_at: Optional[datetime] = None
    day_14_delivered_at: Optional[datetime] = None
    day_30_delivered_at: Optional[datetime] = None

    # Engagement tracking
    engagement_status: str = "new"
    response_count: int = 0
    last_response_at: Optional[datetime] = None

    # CMA/Content tracking
    cma_generated: bool = False
    cma_generated_at: Optional[datetime] = None
    stall_breaker_attempts: int = 0

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert enums to values
        data['current_day'] = self.current_day.value
        data['sequence_status'] = self.sequence_status.value
        # Convert datetime objects to ISO strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LeadSequenceState':
        """Create instance from dictionary."""
        # Convert enum values back to enums
        data['current_day'] = SequenceDay(data['current_day'])
        data['sequence_status'] = SequenceStatus(data['sequence_status'])

        # Convert ISO strings back to datetime objects
        datetime_fields = [
            'sequence_started_at', 'last_action_at', 'next_scheduled_at',
            'day_3_delivered_at', 'day_7_delivered_at', 'day_14_delivered_at', 'day_30_delivered_at',
            'last_response_at', 'cma_generated_at', 'created_at', 'updated_at'
        ]

        for field in datetime_fields:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])

        return cls(**data)

class LeadSequenceStateService:
    """Service for managing lead sequence state persistence."""

    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache = cache_service or get_cache_service()
        self.key_prefix = "lead_sequence"
        self.state_ttl = 60 * 60 * 24 * 90  # 90 days
        logger.info("Initialized LeadSequenceStateService")

    def _get_state_key(self, lead_id: str) -> str:
        """Generate cache key for lead sequence state."""
        return f"{self.key_prefix}:{lead_id}"

    def _get_active_sequences_key(self) -> str:
        """Key for tracking active sequences."""
        return f"{self.key_prefix}:active"

    def _validate_status_transition(
        self,
        from_status: SequenceStatus,
        to_status: SequenceStatus,
        lead_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a status transition is allowed.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if from_status == to_status:
            return True, None  # No-op transitions are allowed

        allowed_transitions = VALID_STATUS_TRANSITIONS.get(from_status, [])
        if to_status not in allowed_transitions:
            error_msg = (
                f"Invalid status transition for lead {lead_id}: "
                f"'{from_status.value}' -> '{to_status.value}'. "
                f"Allowed transitions: {[s.value for s in allowed_transitions]}"
            )
            logger.warning(error_msg)
            return False, error_msg

        return True, None

    def _validate_day_transition(
        self,
        from_day: SequenceDay,
        to_day: SequenceDay,
        lead_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a day transition is allowed.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if from_day == to_day:
            return True, None  # No-op transitions are allowed

        allowed_transitions = VALID_DAY_TRANSITIONS.get(from_day, [])
        if to_day not in allowed_transitions:
            error_msg = (
                f"Invalid day transition for lead {lead_id}: "
                f"'{from_day.value}' -> '{to_day.value}'. "
                f"Allowed transitions: {[d.value for d in allowed_transitions]}"
            )
            logger.warning(error_msg)
            return False, error_msg

        return True, None

    async def transition_status(
        self,
        lead_id: str,
        new_status: SequenceStatus,
        force: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Transition sequence status with validation.

        Args:
            lead_id: The lead ID
            new_status: Target status
            force: If True, skip validation (use for recovery scenarios)

        Returns:
            Tuple of (success, error_message)
        """
        state = await self.get_state(lead_id)
        if not state:
            return False, f"No sequence state found for lead {lead_id}"

        if not force:
            is_valid, error_msg = self._validate_status_transition(
                state.sequence_status, new_status, lead_id
            )
            if not is_valid:
                return False, error_msg

        old_status = state.sequence_status
        state.sequence_status = new_status
        await self.save_state(state)

        logger.info(f"Lead {lead_id} status transition: {old_status.value} -> {new_status.value}")
        return True, None

    async def create_sequence(
        self,
        lead_id: str,
        initial_day: SequenceDay = SequenceDay.DAY_3
    ) -> LeadSequenceState:
        """Create a new sequence for a lead."""
        now = datetime.now()

        state = LeadSequenceState(
            lead_id=lead_id,
            current_day=initial_day,
            sequence_status=SequenceStatus.PENDING,
            sequence_started_at=now,
            created_at=now,
            updated_at=now
        )

        await self.save_state(state)
        await self._add_to_active_sequences(lead_id)

        logger.info(f"Created sequence for lead {lead_id} starting at {initial_day.value}")
        return state

    async def get_state(self, lead_id: str) -> Optional[LeadSequenceState]:
        """Retrieve current sequence state for a lead."""
        state_key = self._get_state_key(lead_id)

        try:
            state_data = await self.cache.get(state_key)
            if state_data:
                return LeadSequenceState.from_dict(state_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get sequence state for lead {lead_id}: {e}", exc_info=True)
            return None

    async def save_state(self, state: LeadSequenceState) -> bool:
        """Save sequence state to cache."""
        state.updated_at = datetime.now()
        state_key = self._get_state_key(state.lead_id)

        try:
            state_data = state.to_dict()
            await self.cache.set(state_key, state_data, self.state_ttl)

            logger.debug(f"Saved sequence state for lead {state.lead_id}: {state.current_day.value}")
            return True
        except Exception as e:
            logger.error(f"Failed to save sequence state for lead {state.lead_id}: {e}", exc_info=True)
            return False

    async def advance_to_next_day(self, lead_id: str, force: bool = False) -> Optional[LeadSequenceState]:
        """
        Advance lead to the next sequence day with validation.

        Args:
            lead_id: The lead ID
            force: If True, skip validation (use for recovery scenarios)

        Returns:
            Updated state or None if not found or validation fails
        """
        state = await self.get_state(lead_id)
        if not state:
            logger.warning(f"No sequence state found for lead {lead_id}")
            return None

        now = datetime.now()
        old_day = state.current_day

        # Determine the next day based on current day
        next_day_map = {
            SequenceDay.DAY_3: SequenceDay.DAY_7,
            SequenceDay.DAY_7: SequenceDay.DAY_14,
            SequenceDay.DAY_14: SequenceDay.DAY_30,
            SequenceDay.DAY_30: SequenceDay.NURTURE,
        }

        next_day = next_day_map.get(state.current_day)
        if not next_day:
            logger.warning(
                f"Cannot advance lead {lead_id} from terminal state: {state.current_day.value}"
            )
            return None

        # Validate the transition unless forced
        if not force:
            is_valid, error_msg = self._validate_day_transition(old_day, next_day, lead_id)
            if not is_valid:
                logger.error(error_msg)
                return None

        # Mark current day as completed and advance
        if state.current_day == SequenceDay.DAY_3:
            state.day_3_completed = True
            state.day_3_delivered_at = now
            state.current_day = SequenceDay.DAY_7
            state.next_scheduled_at = now + timedelta(days=4)  # Day 7 is 4 days after Day 3

        elif state.current_day == SequenceDay.DAY_7:
            state.day_7_completed = True
            state.day_7_delivered_at = now
            state.current_day = SequenceDay.DAY_14
            state.next_scheduled_at = now + timedelta(days=7)  # Day 14 is 7 days after Day 7

        elif state.current_day == SequenceDay.DAY_14:
            state.day_14_completed = True
            state.day_14_delivered_at = now
            state.current_day = SequenceDay.DAY_30
            state.next_scheduled_at = now + timedelta(days=16)  # Day 30 is 16 days after Day 14

        elif state.current_day == SequenceDay.DAY_30:
            state.day_30_completed = True
            state.day_30_delivered_at = now
            state.current_day = SequenceDay.NURTURE
            state.sequence_status = SequenceStatus.COMPLETED
            state.next_scheduled_at = None
            await self._remove_from_active_sequences(lead_id)

        state.last_action_at = now
        await self.save_state(state)

        logger.info(f"Advanced lead {lead_id}: {old_day.value} -> {state.current_day.value}")
        return state

    async def mark_action_completed(
        self,
        lead_id: str,
        day: SequenceDay,
        action_type: str = "delivered"
    ) -> bool:
        """Mark a specific day's action as completed."""
        state = await self.get_state(lead_id)
        if not state:
            return False

        now = datetime.now()

        if day == SequenceDay.DAY_3:
            state.day_3_completed = True
            state.day_3_delivered_at = now
        elif day == SequenceDay.DAY_7:
            state.day_7_completed = True
            state.day_7_delivered_at = now
        elif day == SequenceDay.DAY_14:
            state.day_14_completed = True
            state.day_14_delivered_at = now
        elif day == SequenceDay.DAY_30:
            state.day_30_completed = True
            state.day_30_delivered_at = now

        state.last_action_at = now
        await self.save_state(state)

        logger.info(f"Marked {day.value} action as {action_type} for lead {lead_id}")
        return True

    async def record_engagement(self, lead_id: str, engagement_type: str = "response") -> bool:
        """Record lead engagement (response, click, etc.)."""
        state = await self.get_state(lead_id)
        if not state:
            return False

        now = datetime.now()
        state.response_count += 1
        state.last_response_at = now
        state.engagement_status = "responsive"

        # If lead responds, they're re-engaged
        if state.sequence_status == SequenceStatus.IN_PROGRESS:
            state.engagement_status = "re_engaged"

        await self.save_state(state)

        logger.info(f"Recorded {engagement_type} for lead {lead_id} (total responses: {state.response_count})")
        return True

    async def set_cma_generated(self, lead_id: str) -> bool:
        """Mark CMA as generated for a lead."""
        state = await self.get_state(lead_id)
        if not state:
            return False

        now = datetime.now()
        state.cma_generated = True
        state.cma_generated_at = now

        await self.save_state(state)

        logger.info(f"Marked CMA as generated for lead {lead_id}")
        return True

    async def increment_stall_breaker_attempts(self, lead_id: str) -> int:
        """Increment stall-breaker attempt counter."""
        state = await self.get_state(lead_id)
        if not state:
            return 0

        state.stall_breaker_attempts += 1
        await self.save_state(state)

        return state.stall_breaker_attempts

    async def get_sequences_due_for_action(self, within_hours: int = 1) -> List[LeadSequenceState]:
        """Get sequences that have actions due within the specified timeframe."""
        active_leads = await self._get_active_sequences()
        due_sequences = []

        now = datetime.now()
        cutoff = now + timedelta(hours=within_hours)

        for lead_id in active_leads:
            state = await self.get_state(lead_id)
            if state and state.next_scheduled_at and state.next_scheduled_at <= cutoff:
                if state.sequence_status == SequenceStatus.PENDING:
                    due_sequences.append(state)

        logger.debug(f"Found {len(due_sequences)} sequences due for action within {within_hours} hours")
        return due_sequences

    async def pause_sequence(self, lead_id: str, reason: str = "manual") -> Tuple[bool, Optional[str]]:
        """
        Pause a sequence with validation.

        Returns:
            Tuple of (success, error_message)
        """
        state = await self.get_state(lead_id)
        if not state:
            return False, f"No sequence state found for lead {lead_id}"

        # Validate the transition
        is_valid, error_msg = self._validate_status_transition(
            state.sequence_status, SequenceStatus.PAUSED, lead_id
        )
        if not is_valid:
            return False, error_msg

        old_status = state.sequence_status
        state.sequence_status = SequenceStatus.PAUSED
        await self.save_state(state)

        logger.info(f"Paused sequence for lead {lead_id} ({old_status.value} -> paused), reason: {reason}")
        return True, None

    async def resume_sequence(self, lead_id: str) -> Tuple[bool, Optional[str]]:
        """
        Resume a paused sequence with validation.

        Returns:
            Tuple of (success, error_message)
        """
        state = await self.get_state(lead_id)
        if not state:
            return False, f"No sequence state found for lead {lead_id}"

        # Validate the transition
        is_valid, error_msg = self._validate_status_transition(
            state.sequence_status, SequenceStatus.IN_PROGRESS, lead_id
        )
        if not is_valid:
            return False, error_msg

        old_status = state.sequence_status
        state.sequence_status = SequenceStatus.IN_PROGRESS
        await self.save_state(state)

        logger.info(f"Resumed sequence for lead {lead_id} ({old_status.value} -> in_progress)")
        return True, None

    async def complete_sequence(self, lead_id: str, final_status: str = "qualified") -> Tuple[bool, Optional[str]]:
        """
        Mark sequence as completed with validation.

        Returns:
            Tuple of (success, error_message)
        """
        state = await self.get_state(lead_id)
        if not state:
            return False, f"No sequence state found for lead {lead_id}"

        # Validate the transition
        is_valid, error_msg = self._validate_status_transition(
            state.sequence_status, SequenceStatus.COMPLETED, lead_id
        )
        if not is_valid:
            return False, error_msg

        old_status = state.sequence_status
        state.sequence_status = SequenceStatus.COMPLETED
        state.engagement_status = final_status
        await self.save_state(state)
        await self._remove_from_active_sequences(lead_id)

        logger.info(f"Completed sequence for lead {lead_id} ({old_status.value} -> completed) with status: {final_status}")
        return True, None

    async def get_sequence_summary(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of the lead's sequence progress."""
        state = await self.get_state(lead_id)
        if not state:
            return None

        now = datetime.now()
        days_in_sequence = (now - state.sequence_started_at).days if state.sequence_started_at else 0

        return {
            'lead_id': lead_id,
            'current_day': state.current_day.value,
            'sequence_status': state.sequence_status.value,
            'engagement_status': state.engagement_status,
            'days_in_sequence': days_in_sequence,
            'response_count': state.response_count,
            'progress': {
                'day_3_completed': state.day_3_completed,
                'day_7_completed': state.day_7_completed,
                'day_14_completed': state.day_14_completed,
                'day_30_completed': state.day_30_completed,
            },
            'next_scheduled_at': state.next_scheduled_at.isoformat() if state.next_scheduled_at else None,
            'cma_generated': state.cma_generated,
            'stall_breaker_attempts': state.stall_breaker_attempts,
        }

    async def _add_to_active_sequences(self, lead_id: str) -> bool:
        """Add lead to active sequences tracking."""
        try:
            key = self._get_active_sequences_key()
            current_active = await self.cache.get(key) or set()
            current_active.add(lead_id)
            await self.cache.set(key, current_active, self.state_ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to add {lead_id} to active sequences: {e}", exc_info=True)
            return False

    async def _remove_from_active_sequences(self, lead_id: str) -> bool:
        """Remove lead from active sequences tracking."""
        try:
            key = self._get_active_sequences_key()
            current_active = await self.cache.get(key) or set()
            current_active.discard(lead_id)
            await self.cache.set(key, current_active, self.state_ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to remove {lead_id} from active sequences: {e}", exc_info=True)
            return False

    async def _get_active_sequences(self) -> set:
        """Get set of currently active sequence lead IDs."""
        try:
            key = self._get_active_sequences_key()
            return await self.cache.get(key) or set()
        except Exception as e:
            logger.error(f"Failed to get active sequences: {e}", exc_info=True)
            return set()

    async def get_all_active_sequences(self) -> List[LeadSequenceState]:
        """Get all currently active sequences."""
        active_leads = await self._get_active_sequences()
        sequences = []

        for lead_id in active_leads:
            state = await self.get_state(lead_id)
            if state:
                sequences.append(state)

        return sequences

    async def cleanup_expired_sequences(self, older_than_days: int = 90) -> int:
        """Clean up sequences older than specified days."""
        active_leads = await self._get_active_sequences()
        cleaned_count = 0
        cutoff_date = datetime.now() - timedelta(days=older_than_days)

        for lead_id in active_leads:
            state = await self.get_state(lead_id)
            if state and state.sequence_started_at and state.sequence_started_at < cutoff_date:
                await self.cache.delete(self._get_state_key(lead_id))
                await self._remove_from_active_sequences(lead_id)
                cleaned_count += 1

        logger.info(f"Cleaned up {cleaned_count} expired sequences older than {older_than_days} days")
        return cleaned_count

# Global service instance
_sequence_service: Optional[LeadSequenceStateService] = None

def get_sequence_service() -> LeadSequenceStateService:
    """Get global sequence service instance."""
    global _sequence_service
    if _sequence_service is None:
        _sequence_service = LeadSequenceStateService()
    return _sequence_service