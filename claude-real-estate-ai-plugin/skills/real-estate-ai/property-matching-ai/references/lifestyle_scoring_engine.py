"""
Lifestyle Scoring Engine
Extracted from production real estate lifestyle intelligence system

Handles school ratings, commute analysis, walkability, and safety scoring
with real-world data integration patterns.
"""

from typing import Dict, List, Any, Optional, Tuple
import math
from dataclasses import dataclass


@dataclass
class SchoolScore:
    """School quality scoring with distance weighting."""
    elementary_rating: Optional[float]
    middle_rating: Optional[float]
    high_rating: Optional[float]
    average_rating: float
    distance_penalty: float
    overall_score: float
    top_school_name: Optional[str]
    reasoning: str


@dataclass
class CommuteScore:
    """Commute convenience scoring."""
    to_downtown_minutes: Optional[int]
    to_workplace_minutes: Optional[int]
    public_transit_access: float
    highway_access: float
    overall_score: float
    reasoning: str


class LifestyleScoringEngine:
    """
    Advanced lifestyle compatibility scoring for property matching.

    Integrates with external APIs and cached data for:
    - School ratings and distance analysis
    - Commute time calculations
    - Walkability and amenities scoring
    - Neighborhood safety assessment
    """

    def __init__(self):
        self.neighborhood_cache = self._load_neighborhood_data()

    def score_school_quality(
        self,
        property_data: Dict[str, Any],
        preferences: Dict[str, Any],
        weight: float
    ) -> SchoolScore:
        """
        Score school quality with distance weighting.

        Production pattern: Families care most about elementary schools,
        distance penalty increases significantly after 1 mile.
        """
        schools = property_data.get("schools", [])
        if not schools:
            return SchoolScore(
                elementary_rating=None,
                middle_rating=None,
                high_rating=None,
                average_rating=5.0,
                distance_penalty=0.0,
                overall_score=0.5 * weight,
                top_school_name=None,
                reasoning="School data not available"
            )

        # Extract ratings by level
        elementary_rating = self._extract_rating(schools, "Elementary")
        middle_rating = self._extract_rating(schools, "Middle")
        high_rating = self._extract_rating(schools, "High")

        # Weight elementary schools higher for families
        ratings = []
        if elementary_rating:
            ratings.extend([elementary_rating] * 3)  # 3x weight
        if middle_rating:
            ratings.append(middle_rating)
        if high_rating:
            ratings.append(high_rating)

        if not ratings:
            average_rating = 5.0
        else:
            average_rating = sum(ratings) / len(ratings)

        # Distance penalty (would integrate with real distance API)
        distance_penalty = 0.1  # Placeholder

        # Score calculation (5-10 scale normalized to 0-1)
        if average_rating >= 8.5:
            base_score = 1.0
        elif average_rating >= 7.5:
            base_score = 0.8
        elif average_rating >= 6.5:
            base_score = 0.6
        elif average_rating >= 5.5:
            base_score = 0.4
        else:
            base_score = 0.2

        overall_score = max(0, base_score - distance_penalty) * weight

        # Find top school
        top_school = max(schools, key=lambda s: s.get("rating", 0)) if schools else None
        top_school_name = top_school.get("name") if top_school else None

        # Reasoning
        if average_rating >= 9:
            quality_desc = "excellent"
        elif average_rating >= 8:
            quality_desc = "very good"
        elif average_rating >= 7:
            quality_desc = "good"
        else:
            quality_desc = "average"

        reasoning = f"Schools rated {average_rating:.1f}/10 ({quality_desc})"
        if top_school_name:
            reasoning += f", top school: {top_school_name}"

        return SchoolScore(
            elementary_rating=elementary_rating,
            middle_rating=middle_rating,
            high_rating=high_rating,
            average_rating=average_rating,
            distance_penalty=distance_penalty,
            overall_score=overall_score,
            top_school_name=top_school_name,
            reasoning=reasoning
        )

    def score_commute_convenience(
        self,
        property_data: Dict[str, Any],
        preferences: Dict[str, Any],
        weight: float
    ) -> CommuteScore:
        """
        Score commute convenience with multiple destination support.

        Production insight: Under 25 minutes = excellent, 25-35 = good,
        35-45 = acceptable, 45+ = poor for most professionals.
        """
        address = property_data.get("address", {})
        neighborhood = address.get("neighborhood", "").lower()
        city = address.get("city", "").lower()

        # Get cached commute data
        location_key = f"{neighborhood}_{city}".replace(" ", "_")
        cached_data = self.neighborhood_cache.get(location_key, {})

        # Downtown commute (most common)
        downtown_minutes = cached_data.get("downtown_commute_min")
        if not downtown_minutes:
            downtown_minutes = self._estimate_downtown_commute(neighborhood, city)

        # Workplace-specific commute
        workplace = preferences.get("workplace_location")
        workplace_minutes = None
        if workplace:
            workplace_minutes = self._estimate_workplace_commute(neighborhood, workplace)

        # Public transit and highway access
        public_transit = self._assess_transit_access(neighborhood, city)
        highway_access = self._assess_highway_access(neighborhood, city)

        # Calculate overall score
        commute_factors = []

        if downtown_minutes:
            if downtown_minutes <= 20:
                downtown_score = 1.0
            elif downtown_minutes <= 30:
                downtown_score = 0.8
            elif downtown_minutes <= 45:
                downtown_score = 0.6
            else:
                downtown_score = 0.3
            commute_factors.append(downtown_score * 0.4)

        if workplace_minutes:
            if workplace_minutes <= 15:
                workplace_score = 1.0
            elif workplace_minutes <= 25:
                workplace_score = 0.8
            elif workplace_minutes <= 40:
                workplace_score = 0.6
            else:
                workplace_score = 0.3
            commute_factors.append(workplace_score * 0.4)

        commute_factors.extend([
            public_transit * 0.1,
            highway_access * 0.1
        ])

        overall_score = sum(commute_factors) * weight

        # Generate reasoning
        reasoning_parts = []
        if downtown_minutes:
            reasoning_parts.append(f"~{downtown_minutes} min to downtown")
        if workplace_minutes:
            reasoning_parts.append(f"~{workplace_minutes} min to workplace")
        if public_transit > 0.7:
            reasoning_parts.append("good public transit")
        if highway_access > 0.7:
            reasoning_parts.append("excellent highway access")

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Commute analysis pending"

        return CommuteScore(
            to_downtown_minutes=downtown_minutes,
            to_workplace_minutes=workplace_minutes,
            public_transit_access=public_transit,
            highway_access=highway_access,
            overall_score=overall_score,
            reasoning=reasoning
        )

    def _extract_rating(self, schools: List[Dict], school_type: str) -> Optional[float]:
        """Extract rating for specific school type."""
        for school in schools:
            if school_type.lower() in school.get("type", "").lower():
                return school.get("rating")
        return None

    def _load_neighborhood_data(self) -> Dict[str, Any]:
        """Load neighborhood data cache."""
        # Production pattern: Load from Redis/database cache
        return {
            "hyde_park_austin": {
                "downtown_commute_min": 15,
                "public_transit_score": 0.8,
                "highway_access": 0.7,
                "walkability": 0.9,
                "safety_rating": 7.5
            },
            "steiner_ranch_austin": {
                "downtown_commute_min": 35,
                "public_transit_score": 0.3,
                "highway_access": 0.9,
                "walkability": 0.4,
                "safety_rating": 9.0
            }
            # ... more neighborhoods
        }

    def _estimate_downtown_commute(self, neighborhood: str, city: str) -> Optional[int]:
        """Estimate commute to downtown core."""
        # Production: Integrate with Google Maps/Mapbox API
        downtown_estimates = {
            "hyde park": 15,
            "east austin": 8,
            "west campus": 10,
            "steiner ranch": 35,
            "avery ranch": 40
        }
        return downtown_estimates.get(neighborhood)

    def _estimate_workplace_commute(self, neighborhood: str, workplace: str) -> Optional[int]:
        """Estimate commute to specific workplace."""
        # Production: Cache common workplace commutes
        workplace_map = {
            "domain": {"hyde park": 25, "steiner ranch": 15},
            "ut campus": {"hyde park": 10, "west campus": 5},
            "downtown": {"hyde park": 15, "east austin": 8}
        }

        for location, commutes in workplace_map.items():
            if location in workplace.lower():
                return commutes.get(neighborhood)
        return None

    def _assess_transit_access(self, neighborhood: str, city: str) -> float:
        """Assess public transit quality (0-1 scale)."""
        good_transit = ["hyde park", "east austin", "west campus"]
        moderate_transit = ["south austin", "north austin"]

        if neighborhood in good_transit:
            return 0.8
        elif neighborhood in moderate_transit:
            return 0.5
        else:
            return 0.2

    def _assess_highway_access(self, neighborhood: str, city: str) -> float:
        """Assess highway access quality (0-1 scale)."""
        excellent_access = ["steiner ranch", "avery ranch", "circle c"]
        good_access = ["hyde park", "east austin"]

        if neighborhood in excellent_access:
            return 0.9
        elif neighborhood in good_access:
            return 0.7
        else:
            return 0.5


# Usage patterns from production
"""
# Initialize lifestyle engine
engine = LifestyleScoringEngine()

# Score schools for family-focused property
school_score = engine.score_school_quality(
    property_data={
        "schools": [
            {"name": "Mathews Elementary", "rating": 9, "type": "Elementary"},
            {"name": "McCallum High School", "rating": 8, "type": "High"}
        ]
    },
    preferences={"segment": "family_with_kids"},
    weight=0.35  # High weight for families
)

# Score commute for professional
commute_score = engine.score_commute_convenience(
    property_data={
        "address": {"neighborhood": "Hyde Park", "city": "Austin"}
    },
    preferences={"workplace_location": "downtown Austin"},
    weight=0.30
)

print(f"School Score: {school_score.overall_score:.2f}")
print(f"Commute Score: {commute_score.overall_score:.2f}")
"""