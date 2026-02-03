"""
Personalization Engine - A domain-agnostic personalization system for user-specific retrieval.

This package provides user profile management, personalized retrieval, feedback collection,
and storage backends for building personalized experiences.
"""

from src.personalization.user_profile import (
    UserProfile,
    Preference,
    Interest,
    Interaction,
    PreferenceSource,
    PreferenceCategory,
    PreferenceExtractor,
    InterestModel,
    ProfileManager,
)

from src.personalization.profile_store import (
    ProfileStore,
    RedisProfileStore,
    InMemoryProfileStore,
    ProfileSerializer,
)

from src.personalization.personalized_retrieval import (
    PersonalizedRetriever,
    RankingEngine,
    QueryExpander,
    ContentFilter,
    ScoredItem,
    RankingConfig,
)

from src.personalization.feedback_collector import (
    FeedbackCollector,
    ExplicitFeedback,
    ImplicitFeedback,
    FeedbackProcessor,
    FeedbackType,
    FeedbackContext,
)

__version__ = "1.0.0"

__all__ = [
    # User Profile
    "UserProfile",
    "Preference",
    "Interest",
    "Interaction",
    "PreferenceSource",
    "PreferenceCategory",
    "PreferenceExtractor",
    "InterestModel",
    "ProfileManager",
    # Storage
    "ProfileStore",
    "RedisProfileStore",
    "InMemoryProfileStore",
    "ProfileSerializer",
    # Retrieval
    "PersonalizedRetriever",
    "RankingEngine",
    "QueryExpander",
    "ContentFilter",
    "ScoredItem",
    "RankingConfig",
    # Feedback
    "FeedbackCollector",
    "ExplicitFeedback",
    "ImplicitFeedback",
    "FeedbackProcessor",
    "FeedbackType",
    "FeedbackContext",
]
