"""Hybrid property recommendation engine.

Combines content-based filtering (property feature vectors via cosine similarity)
with collaborative filtering (interaction history matrix factorization) using
weighted blending.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PropertyFeatures:
    """Feature vector for a property."""

    property_id: str
    price: float = 0.0
    sqft: float = 0.0
    bedrooms: int = 0
    bathrooms: float = 0.0
    year_built: int = 2000
    lot_size: float = 0.0
    garage_spaces: int = 0
    has_pool: bool = False
    zip_code: str = ""
    property_type: str = "single_family"  # single_family, condo, townhouse
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_vector(self) -> np.ndarray:
        """Convert to normalized feature vector for similarity computation."""
        return np.array(
            [
                self.price / 1_000_000,  # Normalize to millions
                self.sqft / 3000,  # Normalize to typical max
                self.bedrooms / 6,
                self.bathrooms / 4,
                (self.year_built - 1950) / 80,  # Normalize age
                self.lot_size / 20000,  # Normalize sqft
                self.garage_spaces / 3,
                float(self.has_pool),
                {"single_family": 1.0, "condo": 0.5, "townhouse": 0.75}.get(
                    self.property_type, 0.5
                ),
            ],
            dtype=np.float64,
        )


@dataclass
class Recommendation:
    """A property recommendation with score and explanation."""

    property_id: str
    score: float  # 0.0 - 1.0
    content_score: float = 0.0
    collaborative_score: float = 0.0
    explanation: str = ""
    property_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BuyerPreference:
    """Buyer preference profile built from interactions."""

    contact_id: str
    liked_properties: List[str] = field(default_factory=list)
    disliked_properties: List[str] = field(default_factory=list)
    viewed_properties: List[str] = field(default_factory=list)
    price_range: Tuple[float, float] = (0, float("inf"))
    min_beds: int = 0
    min_baths: float = 0
    preferred_areas: List[str] = field(default_factory=list)


class HybridPropertyRecommender:
    """Hybrid recommender combining content-based and collaborative filtering."""

    def __init__(
        self,
        content_weight: float = 0.6,
        collaborative_weight: float = 0.4,
    ):
        self._content_weight = content_weight
        self._collab_weight = collaborative_weight

        # Property catalog: property_id → PropertyFeatures
        self._properties: Dict[str, PropertyFeatures] = {}
        # Interaction matrix: contact_id → {property_id → score}
        self._interactions: Dict[str, Dict[str, float]] = {}

    def add_property(self, features: PropertyFeatures) -> None:
        """Add a property to the catalog."""
        self._properties[features.property_id] = features

    def add_properties(self, properties: List[PropertyFeatures]) -> None:
        """Add multiple properties to the catalog."""
        for p in properties:
            self._properties[p.property_id] = p

    def record_interaction(
        self,
        contact_id: str,
        property_id: str,
        score: float,
    ) -> None:
        """Record a buyer-property interaction.

        Args:
            contact_id: Buyer contact ID.
            property_id: Property ID.
            score: Interaction score (1.0=liked, 0.5=viewed, 0.0=disliked).
        """
        interactions = self._interactions.setdefault(contact_id, {})
        interactions[property_id] = score

    def recommend(
        self,
        contact_id: str,
        preference: Optional[BuyerPreference] = None,
        n: int = 5,
        exclude_seen: bool = True,
    ) -> List[Recommendation]:
        """Generate property recommendations for a buyer.

        Args:
            contact_id: Buyer contact ID.
            preference: Optional explicit buyer preferences.
            n: Number of recommendations to return.
            exclude_seen: Whether to exclude already-interacted properties.

        Returns:
            List of Recommendations sorted by score descending.
        """
        if not self._properties:
            return []

        # Get properties to score
        seen = set(self._interactions.get(contact_id, {}).keys())
        candidates = {
            pid: p
            for pid, p in self._properties.items()
            if not (exclude_seen and pid in seen)
        }

        if not candidates:
            return []

        # Content-based scores
        content_scores = self._content_based_scores(contact_id, candidates, preference)

        # Collaborative scores
        collab_scores = self._collaborative_scores(contact_id, candidates)

        # Blend scores
        recommendations = []
        for pid in candidates:
            cs = content_scores.get(pid, 0.5)
            co = collab_scores.get(pid, 0.5)
            blended = (self._content_weight * cs) + (self._collab_weight * co)
            blended = max(0.0, min(1.0, blended))

            prop = self._properties[pid]
            recommendations.append(
                Recommendation(
                    property_id=pid,
                    score=round(blended, 4),
                    content_score=round(cs, 4),
                    collaborative_score=round(co, 4),
                    explanation=self._explain(prop, cs, co),
                    property_data={
                        "price": prop.price,
                        "sqft": prop.sqft,
                        "bedrooms": prop.bedrooms,
                        "bathrooms": prop.bathrooms,
                        "zip_code": prop.zip_code,
                    },
                )
            )

        recommendations.sort(key=lambda r: r.score, reverse=True)
        return recommendations[:n]

    def _content_based_scores(
        self,
        contact_id: str,
        candidates: Dict[str, PropertyFeatures],
        preference: Optional[BuyerPreference],
    ) -> Dict[str, float]:
        """Score candidates based on similarity to liked properties."""
        interactions = self._interactions.get(contact_id, {})

        # Build preference vector from liked properties
        liked_vectors = []
        for pid, score in interactions.items():
            if score >= 0.7 and pid in self._properties:
                liked_vectors.append(self._properties[pid].to_vector())

        if not liked_vectors:
            # No interaction history: use preference filters if available
            return self._preference_filter_scores(candidates, preference)

        # Average liked property vector
        pref_vector = np.mean(liked_vectors, axis=0)

        scores = {}
        for pid, prop in candidates.items():
            prop_vector = prop.to_vector()
            sim = self._cosine_similarity(pref_vector, prop_vector)
            # Apply preference filters as bonus/penalty
            if preference:
                sim = self._apply_preference_bonus(sim, prop, preference)
            scores[pid] = max(0.0, min(1.0, (sim + 1) / 2))  # Normalize -1..1 to 0..1

        return scores

    def _preference_filter_scores(
        self,
        candidates: Dict[str, PropertyFeatures],
        preference: Optional[BuyerPreference],
    ) -> Dict[str, float]:
        """Score based on explicit preferences when no interaction history."""
        scores = {}
        for pid, prop in candidates.items():
            score = 0.5  # Base score
            if preference:
                # Price match
                min_p, max_p = preference.price_range
                if min_p <= prop.price <= max_p:
                    score += 0.2
                elif prop.price > max_p:
                    overage = (prop.price - max_p) / max_p if max_p > 0 else 1
                    score -= min(0.3, overage)

                # Bed/bath match
                if prop.bedrooms >= preference.min_beds:
                    score += 0.1
                if prop.bathrooms >= preference.min_baths:
                    score += 0.1

                # Area match
                if preference.preferred_areas and prop.zip_code in preference.preferred_areas:
                    score += 0.15

            scores[pid] = max(0.0, min(1.0, score))
        return scores

    def _collaborative_scores(
        self,
        contact_id: str,
        candidates: Dict[str, PropertyFeatures],
    ) -> Dict[str, float]:
        """Score candidates using collaborative filtering (user similarity)."""
        my_interactions = self._interactions.get(contact_id, {})
        if not my_interactions or len(self._interactions) < 2:
            return {pid: 0.5 for pid in candidates}

        # Find similar users
        similar_users = self._find_similar_users(contact_id, top_k=5)

        if not similar_users:
            return {pid: 0.5 for pid in candidates}

        # Weighted average of similar users' interactions
        scores = {}
        for pid in candidates:
            weighted_sum = 0.0
            weight_total = 0.0
            for other_id, similarity in similar_users:
                other_score = self._interactions.get(other_id, {}).get(pid)
                if other_score is not None:
                    weighted_sum += similarity * other_score
                    weight_total += similarity
            if weight_total > 0:
                scores[pid] = weighted_sum / weight_total
            else:
                scores[pid] = 0.5

        return scores

    def _find_similar_users(
        self, contact_id: str, top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Find users with similar interaction patterns."""
        my_interactions = self._interactions.get(contact_id, {})
        if not my_interactions:
            return []

        similarities = []
        for other_id, other_interactions in self._interactions.items():
            if other_id == contact_id:
                continue

            # Compute similarity on shared items
            shared = set(my_interactions.keys()) & set(other_interactions.keys())
            if len(shared) < 2:
                continue

            my_scores = np.array([my_interactions[pid] for pid in shared])
            other_scores = np.array([other_interactions[pid] for pid in shared])

            sim = self._cosine_similarity(my_scores, other_scores)
            if sim > 0:
                similarities.append((other_id, float(sim)))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    @staticmethod
    def _apply_preference_bonus(
        sim: float, prop: PropertyFeatures, pref: BuyerPreference
    ) -> float:
        """Apply preference-based bonus/penalty to similarity score."""
        min_p, max_p = pref.price_range
        if max_p < float("inf") and prop.price > max_p * 1.1:
            sim -= 0.2
        if prop.bedrooms < pref.min_beds:
            sim -= 0.1
        if pref.preferred_areas and prop.zip_code in pref.preferred_areas:
            sim += 0.1
        return sim

    @staticmethod
    def _explain(prop: PropertyFeatures, cs: float, co: float) -> str:
        """Generate explanation for a recommendation."""
        parts = []
        if cs > 0.7:
            parts.append("closely matches your preferences")
        elif cs > 0.5:
            parts.append("partially matches your preferences")

        if co > 0.7:
            parts.append("popular with similar buyers")
        elif co > 0.5:
            parts.append("viewed by similar buyers")

        if not parts:
            parts.append("may be of interest")

        return (
            f"{prop.bedrooms}BR/{prop.bathrooms}BA in {prop.zip_code or 'area'} — "
            + ", ".join(parts)
        )

    @property
    def property_count(self) -> int:
        return len(self._properties)

    @property
    def interaction_count(self) -> int:
        return sum(len(v) for v in self._interactions.values())


# Singleton
_recommender: Optional[HybridPropertyRecommender] = None


def get_hybrid_recommender() -> HybridPropertyRecommender:
    global _recommender
    if _recommender is None:
        _recommender = HybridPropertyRecommender()
    return _recommender
