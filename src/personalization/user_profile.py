"""
User Profile Management Module

Provides user profile data structures, preference extraction, and interest modeling.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, Generic, List, Optional, Set, TypeVar


class PreferenceSource(Enum):
    """Source of a preference value."""

    EXPLICIT = auto()
    IMPLICIT = auto()
    INFERRED = auto()
    DEFAULT = auto()


class PreferenceCategory(Enum):
    """Category of preference for grouping and organization."""

    GENERAL = auto()
    CONTENT_TYPE = auto()
    PRICE_RANGE = auto()
    LOCATION = auto()
    TIME = auto()
    QUALITY = auto()
    BRAND = auto()
    FEATURE = auto()


@dataclass
class Preference:
    """A single user preference with metadata."""

    name: str
    value: Any
    confidence: float = 1.0
    source: PreferenceSource = PreferenceSource.DEFAULT
    category: PreferenceCategory = PreferenceCategory.GENERAL
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert preference to dictionary for serialization."""
        return {
            "name": self.name,
            "value": self.value,
            "confidence": self.confidence,
            "source": self.source.name,
            "category": self.category.name,
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Preference:
        """Create preference from dictionary."""
        return cls(
            name=data["name"],
            value=data["value"],
            confidence=data["confidence"],
            source=PreferenceSource[data["source"]],
            category=PreferenceCategory[data["category"]],
            last_updated=datetime.fromisoformat(data["last_updated"]),
        )


@dataclass
class Interest:
    """User interest with confidence scoring and decay."""

    topic: str
    score: float = 0.0
    confidence: float = 0.0
    interaction_count: int = 0
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_interaction: datetime = field(default_factory=datetime.utcnow)
    decay_rate: float = 0.01  # Daily decay rate

    def __post_init__(self):
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be between 0.0 and 1.0, got {self.score}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

    def calculate_decayed_score(self, as_of: Optional[datetime] = None) -> float:
        """Calculate score with time decay applied."""
        reference_time = as_of or datetime.utcnow()
        days_passed = (reference_time - self.last_interaction).total_seconds() / 86400
        decay_factor = max(0.0, 1.0 - (self.decay_rate * days_passed))
        return self.score * decay_factor

    def update_score(self, new_score: float, weight: float = 1.0) -> None:
        """Update interest score with new interaction."""
        # Exponential moving average
        self.score = (self.score * (1 - weight)) + (new_score * weight)
        self.score = max(0.0, min(1.0, self.score))
        self.interaction_count += 1
        self.last_interaction = datetime.utcnow()

        # Update confidence based on interaction count
        self.confidence = min(1.0, self.confidence + 0.1)

    def to_dict(self) -> Dict[str, Any]:
        """Convert interest to dictionary for serialization."""
        return {
            "topic": self.topic,
            "score": self.score,
            "confidence": self.confidence,
            "interaction_count": self.interaction_count,
            "first_seen": self.first_seen.isoformat(),
            "last_interaction": self.last_interaction.isoformat(),
            "decay_rate": self.decay_rate,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Interest:
        """Create interest from dictionary."""
        return cls(
            topic=data["topic"],
            score=data["score"],
            confidence=data["confidence"],
            interaction_count=data["interaction_count"],
            first_seen=datetime.fromisoformat(data["first_seen"]),
            last_interaction=datetime.fromisoformat(data["last_interaction"]),
            decay_rate=data.get("decay_rate", 0.01),
        )


@dataclass
class Interaction:
    """Record of a user interaction with an item."""

    item_id: str
    interaction_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert interaction to dictionary for serialization."""
        return {
            "item_id": self.item_id,
            "interaction_type": self.interaction_type,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Interaction:
        """Create interaction from dictionary."""
        return cls(
            item_id=data["item_id"],
            interaction_type=data["interaction_type"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            duration_ms=data["duration_ms"],
            metadata=data.get("metadata", {}),
        )


@dataclass
class UserProfile:
    """Complete user profile containing preferences, interests, and history."""

    user_id: str
    preferences: Dict[str, Preference] = field(default_factory=dict)
    interests: Dict[str, Interest] = field(default_factory=dict)
    interaction_history: List[Interaction] = field(default_factory=list)
    explicit_preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1

    def get_preference(self, name: str, default: Any = None) -> Optional[Preference]:
        """Get a preference by name."""
        return self.preferences.get(name) if name in self.preferences else default

    def set_preference(
        self,
        name: str,
        value: Any,
        category: PreferenceCategory = PreferenceCategory.GENERAL,
        source: PreferenceSource = PreferenceSource.EXPLICIT,
        confidence: float = 1.0,
    ) -> None:
        """Set a preference value."""
        self.preferences[name] = Preference(
            name=name,
            value=value,
            confidence=confidence,
            source=source,
            category=category,
            last_updated=datetime.utcnow(),
        )
        self.updated_at = datetime.utcnow()
        self.version += 1

    def get_interest(self, topic: str) -> Optional[Interest]:
        """Get an interest by topic."""
        return self.interests.get(topic)

    def add_interaction(self, interaction: Interaction) -> None:
        """Add an interaction to history."""
        self.interaction_history.append(interaction)
        self.updated_at = datetime.utcnow()

        # Keep only last 1000 interactions
        if len(self.interaction_history) > 1000:
            self.interaction_history = self.interaction_history[-1000:]

    def get_recent_interactions(
        self,
        interaction_type: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Interaction]:
        """Get recent interactions with optional filtering."""
        interactions = self.interaction_history

        if since:
            interactions = [i for i in interactions if i.timestamp >= since]

        if interaction_type:
            interactions = [i for i in interactions if i.interaction_type == interaction_type]

        return sorted(interactions, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_top_interests(self, n: int = 10, min_confidence: float = 0.0) -> List[Interest]:
        """Get top N interests by decayed score."""
        scored_interests = [
            (interest, interest.calculate_decayed_score())
            for interest in self.interests.values()
            if interest.confidence >= min_confidence
        ]
        scored_interests.sort(key=lambda x: x[1], reverse=True)
        return [interest for interest, _ in scored_interests[:n]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for serialization."""
        return {
            "user_id": self.user_id,
            "preferences": {k: v.to_dict() for k, v in self.preferences.items()},
            "interests": {k: v.to_dict() for k, v in self.interests.items()},
            "interaction_history": [i.to_dict() for i in self.interaction_history],
            "explicit_preferences": self.explicit_preferences,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UserProfile:
        """Create profile from dictionary."""
        return cls(
            user_id=data["user_id"],
            preferences={k: Preference.from_dict(v) for k, v in data.get("preferences", {}).items()},
            interests={k: Interest.from_dict(v) for k, v in data.get("interests", {}).items()},
            interaction_history=[Interaction.from_dict(i) for i in data.get("interaction_history", [])],
            explicit_preferences=data.get("explicit_preferences", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            version=data.get("version", 1),
        )


class PreferenceExtractor:
    """Extract preferences from user interactions and behavior."""

    def __init__(self):
        self._extractors: Dict[str, Callable[[Interaction], Optional[Preference]]] = {}

    def register_extractor(
        self,
        interaction_type: str,
        extractor: Callable[[Interaction], Optional[Preference]],
    ) -> None:
        """Register an extractor for a specific interaction type."""
        self._extractors[interaction_type] = extractor

    async def extract_preferences(
        self,
        profile: UserProfile,
        interactions: Optional[List[Interaction]] = None,
    ) -> Dict[str, Preference]:
        """Extract preferences from user interactions."""
        interactions = interactions or profile.interaction_history
        extracted: Dict[str, Preference] = {}

        for interaction in interactions:
            extractor = self._extractors.get(interaction.interaction_type)
            if extractor:
                try:
                    preference = extractor(interaction)
                    if preference:
                        # Merge with existing if present
                        if preference.name in extracted:
                            existing = extracted[preference.name]
                            preference.confidence = max(existing.confidence, preference.confidence)
                        extracted[preference.name] = preference
                except Exception as e:
                    # Log error but continue processing
                    continue

        return extracted

    async def extract_from_metadata(
        self,
        interactions: List[Interaction],
        key: str,
        category: PreferenceCategory = PreferenceCategory.GENERAL,
    ) -> Optional[Preference]:
        """Extract a preference by aggregating values from interaction metadata."""
        values: List[Any] = []

        for interaction in interactions:
            if key in interaction.metadata:
                values.append(interaction.metadata[key])

        if not values:
            return None

        # Determine most common value
        value_counts: Dict[Any, int] = defaultdict(int)
        for value in values:
            value_counts[value] += 1

        most_common = max(value_counts.items(), key=lambda x: x[1])
        confidence = most_common[1] / len(values)

        return Preference(
            name=key,
            value=most_common[0],
            confidence=confidence,
            source=PreferenceSource.IMPLICIT,
            category=category,
        )


class InterestModel:
    """Model user interests from interactions and content."""

    def __init__(
        self,
        decay_rate: float = 0.01,
        min_confidence: float = 0.1,
        max_interests: int = 100,
    ):
        self.decay_rate = decay_rate
        self.min_confidence = min_confidence
        self.max_interests = max_interests

    async def update_from_interaction(
        self,
        profile: UserProfile,
        interaction: Interaction,
        topics: List[str],
        score: float = 0.5,
    ) -> None:
        """Update interests based on an interaction with topics."""
        for topic in topics:
            if topic not in profile.interests:
                profile.interests[topic] = Interest(
                    topic=topic,
                    decay_rate=self.decay_rate,
                )

            interest = profile.interests[topic]

            # Weight based on interaction type and duration
            weight = self._calculate_weight(interaction)
            interest.update_score(score, weight)

            # Update confidence
            interest.confidence = min(1.0, interest.confidence + 0.05)

        # Prune low-confidence interests if over limit
        if len(profile.interests) > self.max_interests:
            await self._prune_interests(profile)

    def _calculate_weight(self, interaction: Interaction) -> float:
        """Calculate weight for an interaction based on engagement."""
        base_weight = 0.1

        # Increase weight for longer interactions
        if interaction.duration_ms > 0:
            duration_weight = min(0.5, interaction.duration_ms / 60000)  # Max at 1 minute
            base_weight += duration_weight

        # Boost for certain interaction types
        type_multipliers = {
            "click": 1.0,
            "view": 0.5,
            "like": 1.5,
            "share": 2.0,
            "save": 1.8,
            "purchase": 3.0,
            "dwell": 0.8,
        }
        multiplier = type_multipliers.get(interaction.interaction_type, 1.0)

        return min(1.0, base_weight * multiplier)

    async def _prune_interests(self, profile: UserProfile) -> None:
        """Remove low-confidence interests to maintain limit."""
        # Sort by confidence * decayed score
        scored = [
            (topic, interest.confidence * interest.calculate_decayed_score())
            for topic, interest in profile.interests.items()
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        # Keep top interests
        to_keep = {topic for topic, _ in scored[: self.max_interests]}
        profile.interests = {topic: interest for topic, interest in profile.interests.items() if topic in to_keep}

    async def get_relevant_topics(
        self,
        profile: UserProfile,
        context: Optional[Dict[str, Any]] = None,
        n: int = 5,
    ) -> List[str]:
        """Get most relevant topics for a given context."""
        top_interests = profile.get_top_interests(n=n * 2, min_confidence=self.min_confidence)

        # Filter by context if provided
        if context and "category" in context:
            category = context["category"]
            top_interests = [interest for interest in top_interests if interest.topic.startswith(f"{category}:")]

        return [interest.topic for interest in top_interests[:n]]


class ProfileManager:
    """Manage user profile lifecycle and operations."""

    def __init__(
        self,
        preference_extractor: Optional[PreferenceExtractor] = None,
        interest_model: Optional[InterestModel] = None,
    ):
        self.extractor = preference_extractor or PreferenceExtractor()
        self.interest_model = interest_model or InterestModel()

    async def create_profile(self, user_id: str) -> UserProfile:
        """Create a new user profile."""
        return UserProfile(user_id=user_id)

    async def update_from_interactions(
        self,
        profile: UserProfile,
        interactions: List[Interaction],
    ) -> None:
        """Update profile from a batch of interactions."""
        # Add interactions to history
        for interaction in interactions:
            profile.add_interaction(interaction)

        # Extract preferences
        preferences = await self.extractor.extract_preferences(profile, interactions)
        for name, preference in preferences.items():
            if name not in profile.preferences:
                profile.preferences[name] = preference
            else:
                # Merge with existing
                existing = profile.preferences[name]
                if preference.confidence > existing.confidence:
                    profile.preferences[name] = preference

        # Update interests from interactions
        for interaction in interactions:
            if "topics" in interaction.metadata:
                await self.interest_model.update_from_interaction(
                    profile,
                    interaction,
                    interaction.metadata["topics"],
                    interaction.metadata.get("interest_score", 0.5),
                )

    async def merge_profiles(
        self,
        primary: UserProfile,
        secondary: UserProfile,
    ) -> UserProfile:
        """Merge two profiles, with primary taking precedence."""
        # Merge preferences
        for name, preference in secondary.preferences.items():
            if name not in primary.preferences:
                primary.preferences[name] = preference
            elif preference.confidence > primary.preferences[name].confidence:
                primary.preferences[name] = preference

        # Merge interests
        for topic, interest in secondary.interests.items():
            if topic not in primary.interests:
                primary.interests[topic] = interest
            else:
                # Combine scores
                primary.interests[topic].score = max(
                    primary.interests[topic].score,
                    interest.score,
                )
                primary.interests[topic].confidence = max(
                    primary.interests[topic].confidence,
                    interest.confidence,
                )

        # Merge history
        primary.interaction_history.extend(secondary.interaction_history)
        primary.interaction_history.sort(key=lambda x: x.timestamp)

        # Keep only last 1000
        if len(primary.interaction_history) > 1000:
            primary.interaction_history = primary.interaction_history[-1000:]

        primary.updated_at = datetime.utcnow()
        primary.version += 1

        return primary

    async def anonymize_profile(self, profile: UserProfile) -> UserProfile:
        """Create an anonymized version of the profile."""
        return UserProfile(
            user_id=f"anon_{hash(profile.user_id) % 1000000}",
            preferences=profile.preferences,
            interests=profile.interests,
            interaction_history=[],  # Remove specific interactions
            explicit_preferences={},  # Remove explicit PII
            created_at=profile.created_at,
            updated_at=profile.updated_at,
            version=profile.version,
        )
