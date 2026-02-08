"""
Personalized Retrieval Module

Provides user-aware result ranking, content filtering, and adaptive query expansion.
"""

from __future__ import annotations

import asyncio
import math
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Generic, List, Optional, Set, Tuple, TypeVar, Union

from src.personalization.user_profile import Interest, Preference, PreferenceCategory, UserProfile

T = TypeVar("T")


@dataclass
class ScoredItem(Generic[T]):
    """An item with a personalization score."""

    item: T
    base_score: float = 0.0
    personalization_score: float = 0.0
    final_score: float = 0.0
    score_components: Dict[str, float] = field(default_factory=dict)
    matched_preferences: List[str] = field(default_factory=list)
    matched_interests: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.score_components:
            self.score_components = {
                "base": self.base_score,
                "personalization": self.personalization_score,
            }


@dataclass
class RankingConfig:
    """Configuration for ranking behavior."""

    personalization_weight: float = 0.3
    diversity_weight: float = 0.1
    recency_weight: float = 0.1
    popularity_weight: float = 0.1
    max_items: int = 100
    min_score_threshold: float = 0.0
    diversity_window: int = 5
    enable_query_expansion: bool = True
    enable_content_filtering: bool = True


class ContentFilter:
    """Filter items based on user preferences."""

    def __init__(self, config: Optional[RankingConfig] = None):
        self.config = config or RankingConfig()

    async def filter_items(
        self,
        items: List[T],
        profile: UserProfile,
        item_extractor: Callable[[T], Dict[str, Any]],
    ) -> List[T]:
        """Filter items based on user preferences."""
        if not self.config.enable_content_filtering:
            return items

        filtered = []
        for item in items:
            item_data = item_extractor(item)

            # Check if item passes all preference filters
            if await self._passes_filters(item_data, profile):
                filtered.append(item)

        return filtered

    async def _passes_filters(
        self,
        item_data: Dict[str, Any],
        profile: UserProfile,
    ) -> bool:
        """Check if an item passes user preference filters."""
        # Check explicit exclusions
        for pref_name, pref in profile.preferences.items():
            if pref.confidence < 0.5:
                continue

            # Handle exclusion preferences (negative preferences)
            if pref_name.startswith("exclude_"):
                actual_name = pref_name[8:]  # Remove "exclude_" prefix
                if actual_name in item_data:
                    if item_data[actual_name] == pref.value:
                        return False

            # Handle range preferences
            if pref_name.startswith("min_"):
                actual_name = pref_name[4:]
                if actual_name in item_data:
                    if item_data[actual_name] < pref.value:
                        return False

            if pref_name.startswith("max_"):
                actual_name = pref_name[4:]
                if actual_name in item_data:
                    if item_data[actual_name] > pref.value:
                        return False

        return True

    async def calculate_filter_score(
        self,
        item_data: Dict[str, Any],
        profile: UserProfile,
    ) -> float:
        """Calculate how well an item matches user filters."""
        score = 1.0
        matches = 0

        for pref_name, pref in profile.preferences.items():
            if pref.confidence < 0.3:
                continue

            # Check for exact matches
            if pref_name in item_data:
                if item_data[pref_name] == pref.value:
                    score += pref.confidence * 0.2
                    matches += 1
                elif isinstance(pref.value, (list, set)):
                    if item_data[pref_name] in pref.value:
                        score += pref.confidence * 0.15
                        matches += 1

        # Boost score based on number of matches
        score += min(0.3, matches * 0.05)

        return min(1.0, score)


class QueryExpander:
    """Expand queries based on user interests and preferences."""

    def __init__(self, config: Optional[RankingConfig] = None):
        self.config = config or RankingConfig()
        self._synonyms: Dict[str, List[str]] = {}
        self._expansion_cache: Dict[str, Tuple[List[str], datetime]] = {}
        self._cache_ttl = timedelta(minutes=5)

    def add_synonyms(self, term: str, synonyms: List[str]) -> None:
        """Add synonyms for a term."""
        self._synonyms[term.lower()] = [s.lower() for s in synonyms]

    async def expand_query(
        self,
        query: str,
        profile: UserProfile,
        max_expansions: int = 5,
    ) -> List[str]:
        """Expand a query with user-specific terms."""
        if not self.config.enable_query_expansion:
            return [query]

        # Check cache
        cache_key = f"{query}:{profile.user_id}"
        if cache_key in self._expansion_cache:
            expansions, timestamp = self._expansion_cache[cache_key]
            if datetime.utcnow() - timestamp < self._cache_ttl:
                return expansions

        expansions = [query]
        query_lower = query.lower()
        words = set(query_lower.split())

        # Add synonyms
        for word in list(words):
            if word in self._synonyms:
                for synonym in self._synonyms[word]:
                    if synonym not in words:
                        expansions.append(query_lower.replace(word, synonym))

        # Add user interest terms
        top_interests = profile.get_top_interests(n=max_expansions)
        for interest in top_interests:
            if interest.calculate_decayed_score() > 0.3:
                # Only add if related to query
                if self._is_related(interest.topic, query_lower):
                    expansions.append(f"{query} {interest.topic}")

        # Add preference-based expansions
        for pref_name, pref in profile.preferences.items():
            if pref.confidence > 0.7 and pref.category == PreferenceCategory.CONTENT_TYPE:
                expansions.append(f"{query} {pref.value}")

        # Deduplicate and limit
        seen = set()
        unique_expansions = []
        for exp in expansions:
            exp_lower = exp.lower()
            if exp_lower not in seen:
                seen.add(exp_lower)
                unique_expansions.append(exp)

        result = unique_expansions[: max_expansions + 1]

        # Cache result
        self._expansion_cache[cache_key] = (result, datetime.utcnow())

        return result

    def _is_related(self, topic: str, query: str) -> bool:
        """Check if a topic is related to a query."""
        topic_words = set(topic.lower().split())
        query_words = set(query.lower().split())

        # Check for word overlap
        overlap = topic_words & query_words
        if len(overlap) > 0:
            return True

        # Check for substring match
        for word in query_words:
            if word in topic.lower() or topic.lower() in word:
                return True

        return False

    async def get_related_terms(self, profile: UserProfile, n: int = 10) -> List[str]:
        """Get terms related to user interests."""
        terms = []

        # From interests
        for interest in profile.get_top_interests(n=n):
            if interest.calculate_decayed_score() > 0.2:
                terms.append(interest.topic)

        # From preferences
        for pref in profile.preferences.values():
            if pref.confidence > 0.5:
                if isinstance(pref.value, str):
                    terms.append(pref.value)

        return list(set(terms))[:n]


class RankingEngine:
    """Score and rank items based on user profile."""

    def __init__(self, config: Optional[RankingConfig] = None):
        self.config = config or RankingConfig()
        self.content_filter = ContentFilter(config)

    async def rank_items(
        self,
        items: List[T],
        profile: UserProfile,
        base_scorer: Callable[[T], float],
        item_extractor: Callable[[T], Dict[str, Any]],
    ) -> List[ScoredItem[T]]:
        """Rank items based on user profile."""
        # Filter items first
        filtered_items = await self.content_filter.filter_items(items, profile, item_extractor)

        # Score items
        scored_items = await self._score_items(filtered_items, profile, base_scorer, item_extractor)

        # Apply diversity
        if self.config.diversity_weight > 0:
            scored_items = await self._apply_diversity(scored_items)

        # Sort by final score
        scored_items.sort(key=lambda x: x.final_score, reverse=True)

        # Apply limit
        return scored_items[: self.config.max_items]

    async def _score_items(
        self,
        items: List[T],
        profile: UserProfile,
        base_scorer: Callable[[T], float],
        item_extractor: Callable[[T], Dict[str, Any]],
    ) -> List[ScoredItem[T]]:
        """Calculate scores for all items."""
        scored_items = []

        for item in items:
            base_score = base_scorer(item)
            item_data = item_extractor(item)

            # Calculate personalization score
            personalization_score = await self._calculate_personalization_score(item_data, profile)

            # Calculate component scores
            components = {
                "base": base_score,
                "personalization": personalization_score,
            }

            # Calculate final score
            final_score = (
                base_score * (1 - self.config.personalization_weight)
                + personalization_score * self.config.personalization_weight
            )

            # Apply threshold
            if final_score < self.config.min_score_threshold:
                continue

            scored_item = ScoredItem(
                item=item,
                base_score=base_score,
                personalization_score=personalization_score,
                final_score=final_score,
                score_components=components,
                matched_preferences=[],
                matched_interests=[],
            )

            scored_items.append(scored_item)

        return scored_items

    async def _calculate_personalization_score(
        self,
        item_data: Dict[str, Any],
        profile: UserProfile,
    ) -> float:
        """Calculate personalization score for an item."""
        score = 0.0
        total_weight = 0.0

        # Interest matching
        for interest in profile.interests.values():
            decayed_score = interest.calculate_decayed_score()
            if decayed_score < 0.1:
                continue

            weight = interest.confidence * decayed_score
            total_weight += weight

            # Check if interest topic appears in item data
            for key, value in item_data.items():
                if isinstance(value, str):
                    if interest.topic.lower() in value.lower():
                        score += weight * 0.5
                    if value.lower() in interest.topic.lower():
                        score += weight * 0.3
                elif isinstance(value, (list, set)):
                    for v in value:
                        if isinstance(v, str) and interest.topic.lower() in v.lower():
                            score += weight * 0.4

        # Preference matching
        for pref in profile.preferences.values():
            if pref.confidence < 0.3:
                continue

            weight = pref.confidence
            total_weight += weight

            # Check for exact matches in item data
            if pref.name in item_data:
                if item_data[pref.name] == pref.value:
                    score += weight * 1.0

            # Check for value matches in any field
            if isinstance(pref.value, str):
                for key, value in item_data.items():
                    if isinstance(value, str) and pref.value.lower() in value.lower():
                        score += weight * 0.3

        # Normalize score
        if total_weight > 0:
            score = score / total_weight

        return min(1.0, score)

    async def _apply_diversity(self, items: List[ScoredItem[T]]) -> List[ScoredItem[T]]:
        """Apply diversity re-ranking to items."""
        if not items:
            return items

        diversified = [items[0]]
        remaining = items[1:]

        while remaining and len(diversified) < self.config.max_items:
            # Find item most different from recent items
            window_start = max(0, len(diversified) - self.config.diversity_window)
            recent_items = diversified[window_start:]

            best_item = None
            best_diversity_score = -1.0

            for item in remaining:
                # Calculate diversity as average dissimilarity to recent items
                diversity = 0.0
                for recent in recent_items:
                    diversity += self._calculate_dissimilarity(item, recent)
                diversity /= len(recent_items)

                # Combine with relevance score
                combined_score = (
                    item.final_score * (1 - self.config.diversity_weight) + diversity * self.config.diversity_weight
                )

                if combined_score > best_diversity_score:
                    best_diversity_score = combined_score
                    best_item = item

            if best_item:
                diversified.append(best_item)
                remaining.remove(best_item)
            else:
                break

        return diversified

    def _calculate_dissimilarity(
        self,
        item1: ScoredItem[T],
        item2: ScoredItem[T],
    ) -> float:
        """Calculate dissimilarity between two items."""
        # Use score components to estimate dissimilarity
        diff = 0.0

        for key in set(item1.score_components.keys()) | set(item2.score_components.keys()):
            v1 = item1.score_components.get(key, 0)
            v2 = item2.score_components.get(key, 0)
            diff += abs(v1 - v2)

        # Normalize to 0-1
        return min(1.0, diff / max(len(item1.score_components), 1))


class PersonalizedRetriever:
    """Main retrieval engine for personalized results."""

    def __init__(
        self,
        config: Optional[RankingConfig] = None,
        ranking_engine: Optional[RankingEngine] = None,
        query_expander: Optional[QueryExpander] = None,
    ):
        self.config = config or RankingConfig()
        self.ranking_engine = ranking_engine or RankingEngine(config)
        self.query_expander = query_expander or QueryExpander(config)

    async def retrieve(
        self,
        query: str,
        profile: UserProfile,
        item_provider: Callable[[str], List[T]],
        base_scorer: Callable[[T], float],
        item_extractor: Callable[[T], Dict[str, Any]],
    ) -> List[ScoredItem[T]]:
        """Retrieve personalized results for a query."""
        # Expand query
        expanded_queries = await self.query_expander.expand_query(query, profile)

        # Fetch items for all expanded queries
        all_items: Dict[str, T] = {}
        for expanded_query in expanded_queries:
            items = await asyncio.get_event_loop().run_in_executor(None, item_provider, expanded_query)
            for item in items:
                # Use item ID as key to deduplicate
                item_id = self._get_item_id(item, item_extractor)
                if item_id not in all_items:
                    all_items[item_id] = item

        items = list(all_items.values())

        # Rank items
        ranked_items = await self.ranking_engine.rank_items(items, profile, base_scorer, item_extractor)

        return ranked_items

    async def retrieve_batch(
        self,
        queries: List[str],
        profile: UserProfile,
        item_provider: Callable[[str], List[T]],
        base_scorer: Callable[[T], float],
        item_extractor: Callable[[T], Dict[str, Any]],
    ) -> Dict[str, List[ScoredItem[T]]]:
        """Retrieve personalized results for multiple queries."""
        results = {}
        for query in queries:
            results[query] = await self.retrieve(query, profile, item_provider, base_scorer, item_extractor)
        return results

    def _get_item_id(
        self,
        item: T,
        item_extractor: Callable[[T], Dict[str, Any]],
    ) -> str:
        """Extract unique ID from item."""
        item_data = item_extractor(item)
        if "id" in item_data:
            return str(item_data["id"])
        # Fallback to hash of item data
        return str(hash(str(item_data)))

    async def explain_ranking(
        self,
        scored_item: ScoredItem[T],
        profile: UserProfile,
        item_extractor: Callable[[T], Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Explain why an item was ranked as it was."""
        item_data = item_extractor(scored_item.item)

        explanation = {
            "final_score": scored_item.final_score,
            "base_score": scored_item.base_score,
            "personalization_score": scored_item.personalization_score,
            "components": scored_item.score_components,
            "matched_preferences": [],
            "matched_interests": [],
            "reasoning": [],
        }

        # Check interest matches
        for interest in profile.interests.values():
            decayed_score = interest.calculate_decayed_score()
            if decayed_score < 0.1:
                continue

            for key, value in item_data.items():
                match = False
                if isinstance(value, str):
                    if interest.topic.lower() in value.lower():
                        match = True
                elif isinstance(value, (list, set)):
                    for v in value:
                        if isinstance(v, str) and interest.topic.lower() in v.lower():
                            match = True

                if match:
                    explanation["matched_interests"].append(
                        {
                            "topic": interest.topic,
                            "score": decayed_score,
                            "confidence": interest.confidence,
                        }
                    )
                    explanation["reasoning"].append(
                        f"Matched interest '{interest.topic}' with score {decayed_score:.2f}"
                    )

        # Check preference matches
        for pref in profile.preferences.values():
            if pref.confidence < 0.3:
                continue

            if pref.name in item_data and item_data[pref.name] == pref.value:
                explanation["matched_preferences"].append(
                    {
                        "name": pref.name,
                        "value": pref.value,
                        "confidence": pref.confidence,
                    }
                )
                explanation["reasoning"].append(f"Matched preference '{pref.name}' = '{pref.value}'")

        return explanation
