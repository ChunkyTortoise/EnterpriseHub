"""
Feedback Collection Module

Provides explicit and implicit feedback collection with profile update mechanisms.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union

from src.personalization.profile_store import InMemoryProfileStore, ProfileStore
from src.personalization.user_profile import (
    Interaction,
    InterestModel,
    PreferenceCategory,
    PreferenceSource,
    ProfileManager,
    UserProfile,
)


class FeedbackType(Enum):
    """Types of feedback that can be collected."""

    EXPLICIT_RATING = auto()
    THUMBS_UP = auto()
    THUMBS_DOWN = auto()
    CLICK = auto()
    DWELL_TIME = auto()
    SCROLL_DEPTH = auto()
    CONVERSION = auto()
    DISMISS = auto()
    SHARE = auto()
    SAVE = auto()


@dataclass
class FeedbackContext:
    """Context information for feedback events."""

    query: Optional[str] = None
    position: Optional[int] = None
    page_type: Optional[str] = None
    device_type: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    ab_test_group: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "query": self.query,
            "position": self.position,
            "page_type": self.page_type,
            "device_type": self.device_type,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "ab_test_group": self.ab_test_group,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FeedbackContext:
        """Create context from dictionary."""
        return cls(
            query=data.get("query"),
            position=data.get("position"),
            page_type=data.get("page_type"),
            device_type=data.get("device_type"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            session_id=data.get("session_id"),
            ab_test_group=data.get("ab_test_group"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ExplicitFeedback:
    """Explicit user feedback (ratings, likes, etc.)."""

    user_id: str
    item_id: str
    feedback_type: FeedbackType
    value: float
    context: FeedbackContext = field(default_factory=FeedbackContext)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    weight: float = 1.0

    def __post_init__(self):
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"Feedback value must be between 0.0 and 1.0, got {self.value}")
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"Feedback weight must be between 0.0 and 1.0, got {self.weight}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "item_id": self.item_id,
            "feedback_type": self.feedback_type.name,
            "value": self.value,
            "context": self.context.to_dict(),
            "timestamp": self.timestamp.isoformat(),
            "weight": self.weight,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExplicitFeedback:
        """Create from dictionary."""
        return cls(
            user_id=data["user_id"],
            item_id=data["item_id"],
            feedback_type=FeedbackType[data["feedback_type"]],
            value=data["value"],
            context=FeedbackContext.from_dict(data["context"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            weight=data.get("weight", 1.0),
        )


@dataclass
class ImplicitFeedback:
    """Implicit user feedback (clicks, dwell time, etc.)."""

    user_id: str
    item_id: str
    feedback_type: FeedbackType
    value: float
    duration_ms: int = 0
    context: FeedbackContext = field(default_factory=FeedbackContext)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    confidence: float = 0.5

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "item_id": self.item_id,
            "feedback_type": self.feedback_type.name,
            "value": self.value,
            "duration_ms": self.duration_ms,
            "context": self.context.to_dict(),
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ImplicitFeedback:
        """Create from dictionary."""
        return cls(
            user_id=data["user_id"],
            item_id=data["item_id"],
            feedback_type=FeedbackType[data["feedback_type"]],
            value=data["value"],
            duration_ms=data.get("duration_ms", 0),
            context=FeedbackContext.from_dict(data["context"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            confidence=data.get("confidence", 0.5),
        )


class FeedbackProcessor:
    """Process feedback and update user profiles."""

    def __init__(
        self,
        interest_model: Optional[InterestModel] = None,
        decay_half_life_days: float = 30.0,
    ):
        self.interest_model = interest_model or InterestModel()
        self.decay_half_life_days = decay_half_life_days
        self._feedback_weights: Dict[FeedbackType, float] = {
            FeedbackType.EXPLICIT_RATING: 1.0,
            FeedbackType.THUMBS_UP: 0.9,
            FeedbackType.THUMBS_DOWN: 0.9,
            FeedbackType.CONVERSION: 1.0,
            FeedbackType.SHARE: 0.8,
            FeedbackType.SAVE: 0.7,
            FeedbackType.CLICK: 0.5,
            FeedbackType.DWELL_TIME: 0.4,
            FeedbackType.SCROLL_DEPTH: 0.3,
            FeedbackType.DISMISS: 0.6,
        }

    def calculate_feedback_weight(
        self,
        feedback: Union[ExplicitFeedback, ImplicitFeedback],
    ) -> float:
        """Calculate effective weight for feedback considering decay."""
        base_weight = self._feedback_weights.get(feedback.feedback_type, 0.5)

        # Apply time decay
        days_old = (datetime.utcnow() - feedback.timestamp).total_seconds() / 86400
        decay_factor = 0.5 ** (days_old / self.decay_half_life_days)

        # Apply explicit weight for explicit feedback
        if isinstance(feedback, ExplicitFeedback):
            base_weight *= feedback.weight

        # Apply confidence for implicit feedback
        if isinstance(feedback, ImplicitFeedback):
            base_weight *= feedback.confidence

        return base_weight * decay_factor

    async def process_explicit_feedback(
        self,
        profile: UserProfile,
        feedback: ExplicitFeedback,
        item_topics: Optional[List[str]] = None,
    ) -> None:
        """Process explicit feedback and update profile."""
        weight = self.calculate_feedback_weight(feedback)

        # Create interaction record
        interaction = Interaction(
            item_id=feedback.item_id,
            interaction_type=feedback.feedback_type.name,
            timestamp=feedback.timestamp,
            metadata={
                "value": feedback.value,
                "weight": weight,
                "query": feedback.context.query,
            },
        )
        profile.add_interaction(interaction)

        # Update interests if topics provided
        if item_topics:
            interest_score = feedback.value * weight
            await self.interest_model.update_from_interaction(
                profile,
                interaction,
                item_topics,
                interest_score,
            )

        # Update explicit preferences based on feedback type
        if feedback.feedback_type == FeedbackType.THUMBS_UP:
            await self._process_positive_feedback(profile, feedback, weight)
        elif feedback.feedback_type == FeedbackType.THUMBS_DOWN:
            await self._process_negative_feedback(profile, feedback, weight)

    async def process_implicit_feedback(
        self,
        profile: UserProfile,
        feedback: ImplicitFeedback,
        item_topics: Optional[List[str]] = None,
    ) -> None:
        """Process implicit feedback and update profile."""
        weight = self.calculate_feedback_weight(feedback)

        # Create interaction record
        interaction = Interaction(
            item_id=feedback.item_id,
            interaction_type=feedback.feedback_type.name,
            timestamp=feedback.timestamp,
            duration_ms=feedback.duration_ms,
            metadata={
                "value": feedback.value,
                "weight": weight,
                "query": feedback.context.query,
                "confidence": feedback.confidence,
            },
        )
        profile.add_interaction(interaction)

        # Update interests if topics provided
        if item_topics:
            # Adjust score based on feedback type
            if feedback.feedback_type == FeedbackType.DWELL_TIME:
                # Longer dwell time = higher interest
                interest_score = min(1.0, feedback.value * weight * 1.5)
            elif feedback.feedback_type == FeedbackType.CLICK:
                interest_score = feedback.value * weight
            elif feedback.feedback_type == FeedbackType.SCROLL_DEPTH:
                interest_score = feedback.value * weight * 0.8
            else:
                interest_score = feedback.value * weight

            await self.interest_model.update_from_interaction(
                profile,
                interaction,
                item_topics,
                interest_score,
            )

    async def _process_positive_feedback(
        self,
        profile: UserProfile,
        feedback: ExplicitFeedback,
        weight: float,
    ) -> None:
        """Process positive explicit feedback."""
        # Could infer preferences from context
        if feedback.context.query:
            # User likes results for this query
            pref_name = f"liked_query_{feedback.context.query.lower().replace(' ', '_')}"
            current = profile.preferences.get(pref_name)
            new_confidence = min(1.0, (current.confidence if current else 0.0) + 0.1 * weight)
            profile.set_preference(
                name=pref_name,
                value=True,
                category=PreferenceCategory.GENERAL,
                source=PreferenceSource.IMPLICIT,
                confidence=new_confidence,
            )

    async def _process_negative_feedback(
        self,
        profile: UserProfile,
        feedback: ExplicitFeedback,
        weight: float,
    ) -> None:
        """Process negative explicit feedback."""
        # Could infer negative preferences
        if feedback.context.query:
            pref_name = f"disliked_query_{feedback.context.query.lower().replace(' ', '_')}"
            current = profile.preferences.get(pref_name)
            new_confidence = min(1.0, (current.confidence if current else 0.0) + 0.1 * weight)
            profile.set_preference(
                name=pref_name,
                value=True,
                category=PreferenceCategory.GENERAL,
                source=PreferenceSource.IMPLICIT,
                confidence=new_confidence,
            )

    async def batch_process(
        self,
        profile: UserProfile,
        feedbacks: List[Union[ExplicitFeedback, ImplicitFeedback]],
        item_topics_map: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """Process multiple feedback items in batch."""
        for feedback in feedbacks:
            item_topics = None
            if item_topics_map and feedback.item_id in item_topics_map:
                item_topics = item_topics_map[feedback.item_id]

            if isinstance(feedback, ExplicitFeedback):
                await self.process_explicit_feedback(profile, feedback, item_topics)
            else:
                await self.process_implicit_feedback(profile, feedback, item_topics)


class FeedbackCollector:
    """Collect and manage user feedback."""

    def __init__(
        self,
        store: Optional[ProfileStore] = None,
        processor: Optional[FeedbackProcessor] = None,
        profile_manager: Optional[ProfileManager] = None,
    ):
        self.store = store or InMemoryProfileStore()
        self.processor = processor or FeedbackProcessor()
        self.profile_manager = profile_manager or ProfileManager()
        self._buffer: List[Union[ExplicitFeedback, ImplicitFeedback]] = []
        self._buffer_lock = asyncio.Lock()
        self._buffer_size = 100
        self._flush_interval = 60  # seconds
        self._running = False
        self._flush_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the feedback collector background tasks."""
        if self._running:
            return

        self._running = True
        await self.store.connect()
        self._flush_task = asyncio.create_task(self._flush_loop())

    async def stop(self) -> None:
        """Stop the feedback collector and flush remaining feedback."""
        self._running = False

        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Final flush
        await self._flush_buffer()
        await self.store.disconnect()

    async def _flush_loop(self) -> None:
        """Background task to periodically flush feedback buffer."""
        while self._running:
            try:
                await asyncio.sleep(self._flush_interval)
                await self._flush_buffer()
            except asyncio.CancelledError:
                break
            except Exception:
                # Log error but continue
                continue

    async def _flush_buffer(self) -> None:
        """Flush buffered feedback to profiles."""
        async with self._buffer_lock:
            if not self._buffer:
                return

            feedbacks = self._buffer[:]
            self._buffer = []

        # Group feedback by user
        by_user: Dict[str, List[Union[ExplicitFeedback, ImplicitFeedback]]] = defaultdict(list)
        for feedback in feedbacks:
            by_user[feedback.user_id].append(feedback)

        # Process for each user
        for user_id, user_feedbacks in by_user.items():
            try:
                profile = await self.store.get_or_create(user_id)
                await self.processor.batch_process(profile, user_feedbacks)
                await self.store.set(user_id, profile)
            except Exception:
                # Log error but continue with other users
                continue

    async def collect_explicit(
        self,
        user_id: str,
        item_id: str,
        feedback_type: FeedbackType,
        value: float,
        context: Optional[FeedbackContext] = None,
        item_topics: Optional[List[str]] = None,
        immediate: bool = False,
    ) -> ExplicitFeedback:
        """Collect explicit feedback from a user."""
        feedback = ExplicitFeedback(
            user_id=user_id,
            item_id=item_id,
            feedback_type=feedback_type,
            value=value,
            context=context or FeedbackContext(),
        )

        if immediate:
            # Process immediately
            profile = await self.store.get_or_create(user_id)
            await self.processor.process_explicit_feedback(profile, feedback, item_topics)
            await self.store.set(user_id, profile)
        else:
            # Buffer for batch processing
            async with self._buffer_lock:
                self._buffer.append(feedback)
                if len(self._buffer) >= self._buffer_size:
                    asyncio.create_task(self._flush_buffer())

        return feedback

    async def collect_implicit(
        self,
        user_id: str,
        item_id: str,
        feedback_type: FeedbackType,
        value: float,
        duration_ms: int = 0,
        context: Optional[FeedbackContext] = None,
        item_topics: Optional[List[str]] = None,
        immediate: bool = False,
    ) -> ImplicitFeedback:
        """Collect implicit feedback from a user."""
        feedback = ImplicitFeedback(
            user_id=user_id,
            item_id=item_id,
            feedback_type=feedback_type,
            value=value,
            duration_ms=duration_ms,
            context=context or FeedbackContext(),
        )

        if immediate:
            # Process immediately
            profile = await self.store.get_or_create(user_id)
            await self.processor.process_implicit_feedback(profile, feedback, item_topics)
            await self.store.set(user_id, profile)
        else:
            # Buffer for batch processing
            async with self._buffer_lock:
                self._buffer.append(feedback)
                if len(self._buffer) >= self._buffer_size:
                    asyncio.create_task(self._flush_buffer())

        return feedback

    async def record_click(
        self,
        user_id: str,
        item_id: str,
        position: Optional[int] = None,
        query: Optional[str] = None,
        context: Optional[FeedbackContext] = None,
    ) -> ImplicitFeedback:
        """Record a click event."""
        ctx = context or FeedbackContext()
        ctx.position = position
        ctx.query = query or ctx.query

        return await self.collect_implicit(
            user_id=user_id,
            item_id=item_id,
            feedback_type=FeedbackType.CLICK,
            value=1.0,
            context=ctx,
        )

    async def record_dwell_time(
        self,
        user_id: str,
        item_id: str,
        duration_ms: int,
        query: Optional[str] = None,
        context: Optional[FeedbackContext] = None,
    ) -> ImplicitFeedback:
        """Record dwell time on an item."""
        ctx = context or FeedbackContext()
        ctx.query = query or ctx.query

        # Normalize dwell time to 0-1 range (assuming 5 minutes is max engaged time)
        normalized_value = min(1.0, duration_ms / 300000)

        return await self.collect_implicit(
            user_id=user_id,
            item_id=item_id,
            feedback_type=FeedbackType.DWELL_TIME,
            value=normalized_value,
            duration_ms=duration_ms,
            context=ctx,
        )

    async def record_rating(
        self,
        user_id: str,
        item_id: str,
        rating: float,
        query: Optional[str] = None,
        context: Optional[FeedbackContext] = None,
    ) -> ExplicitFeedback:
        """Record an explicit rating."""
        ctx = context or FeedbackContext()
        ctx.query = query or ctx.query

        return await self.collect_explicit(
            user_id=user_id,
            item_id=item_id,
            feedback_type=FeedbackType.EXPLICIT_RATING,
            value=rating / 5.0,  # Normalize 5-star to 0-1
            context=ctx,
        )

    async def record_thumbs(
        self,
        user_id: str,
        item_id: str,
        is_up: bool,
        query: Optional[str] = None,
        context: Optional[FeedbackContext] = None,
    ) -> ExplicitFeedback:
        """Record a thumbs up/down."""
        ctx = context or FeedbackContext()
        ctx.query = query or ctx.query

        feedback_type = FeedbackType.THUMBS_UP if is_up else FeedbackType.THUMBS_DOWN
        value = 1.0 if is_up else 0.0

        return await self.collect_explicit(
            user_id=user_id,
            item_id=item_id,
            feedback_type=feedback_type,
            value=value,
            context=ctx,
        )

    async def get_feedback_stats(
        self,
        user_id: str,
        since: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get feedback statistics for a user."""
        profile = await self.store.get(user_id)
        if not profile:
            return {
                "total_interactions": 0,
                "feedback_types": {},
                "average_rating": None,
            }

        since = since or datetime.utcnow() - timedelta(days=30)
        interactions = profile.get_recent_interactions(since=since)

        stats = {
            "total_interactions": len(interactions),
            "feedback_types": {},
            "ratings": [],
        }

        for interaction in interactions:
            feedback_type = interaction.interaction_type
            stats["feedback_types"][feedback_type] = stats["feedback_types"].get(feedback_type, 0) + 1

            if "value" in interaction.metadata:
                stats["ratings"].append(interaction.metadata["value"])

        if stats["ratings"]:
            stats["average_rating"] = sum(stats["ratings"]) / len(stats["ratings"])
        else:
            stats["average_rating"] = None

        return stats
