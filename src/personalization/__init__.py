"""
Personalization Engine - A domain-agnostic personalization system for user-specific retrieval.

This package provides user profile management, personalized retrieval, feedback collection,
and storage backends for building personalized experiences.
"""

from src.personalization.feedback_collector import (
    ExplicitFeedback,
    FeedbackCollector,
    FeedbackContext,
    FeedbackProcessor,
    FeedbackType,
    ImplicitFeedback,
)
from src.personalization.personalized_retrieval import (
    ContentFilter,
    PersonalizedRetriever,
    QueryExpander,
    RankingConfig,
    RankingEngine,
    ScoredItem,
)
from src.personalization.profile_store import (
    InMemoryProfileStore,
    ProfileSerializer,
    ProfileStore,
    RedisProfileStore,
)
from src.personalization.user_profile import (
    Interaction,
    Interest,
    InterestModel,
    Preference,
    PreferenceCategory,
    PreferenceExtractor,
    PreferenceSource,
    ProfileManager,
    UserProfile,
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
