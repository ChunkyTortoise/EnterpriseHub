"""
Lifestyle Intelligence Service for Enhanced Property Matching

Provides advanced scoring for lifestyle compatibility factors:
- School quality with distance weighting
- Commute analysis to workplace/downtown
- Walkability and amenities proximity
- Neighborhood safety assessment
- Quality of life indicators

Integrates with external APIs and cached data sources.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.matching_models import (
    CommuteScore,
    LifestyleScores,
    SafetyScore,
    SchoolScore,
    WalkabilityScore,
)

logger = get_logger(__name__)


class LifestyleIntelligenceService:
    """
    Service for calculating lifestyle compatibility scores.

    Analyzes property locations for lifestyle factors that matter to different
    lead segments: families prioritize schools, professionals prioritize commute,
    etc.
    """

    def __init__(self, enable_external_apis: bool = False):
        """
        Initialize the lifestyle intelligence service.

        Args:
            enable_external_apis: Whether to use external APIs (Walk Score, Google Maps)
                                 Set to False for demo/testing with cached data
        """
        self.enable_external_apis = enable_external_apis
        self._load_lifestyle_data()
        self._load_neighborhood_profiles()

    def calculate_lifestyle_score(
        self, property_data: Dict[str, Any], preferences: Dict[str, Any], lead_profile: Optional[Dict[str, Any]] = None
    ) -> LifestyleScores:
        """
        Calculate comprehensive lifestyle compatibility score.

        Args:
            property_data: Property information including address, schools
            preferences: Lead preferences including workplace, family status
            lead_profile: Optional behavioral profile for personalization

        Returns:
            LifestyleScores object with detailed scoring breakdown
        """
        logger.info(f"Calculating lifestyle score for property {property_data.get('id', 'unknown')}")

        # Calculate individual lifestyle factors
        school_score = self.calculate_school_score(property_data, preferences, lead_profile)
        commute_score = self.calculate_commute_score(property_data, preferences)
        walkability_score = self.calculate_walkability_score(property_data, preferences)
        safety_score = self.calculate_safety_score(property_data, preferences)
        amenities_score = self.calculate_amenities_proximity(property_data, preferences)

        # Weight factors based on lead profile
        weights = self._determine_lifestyle_weights(preferences, lead_profile)

        # Calculate weighted overall score
        overall_score = (
            school_score.overall_score * weights.get("schools", 0.25)
            + commute_score.overall_score * weights.get("commute", 0.25)
            + walkability_score.overall_score * weights.get("walkability", 0.25)
            + safety_score.overall_score * weights.get("safety", 0.15)
            + amenities_score * weights.get("amenities", 0.10)
        )

        return LifestyleScores(
            schools=school_score,
            commute=commute_score,
            walkability=walkability_score,
            safety=safety_score,
            amenities_proximity=amenities_score,
            overall_score=overall_score,
        )

    def calculate_school_score(
        self, property_data: Dict[str, Any], preferences: Dict[str, Any], lead_profile: Optional[Dict[str, Any]] = None
    ) -> SchoolScore:
        """
        Calculate school quality score with distance weighting.

        Considers:
        - Individual school ratings (elementary, middle, high)
        - Distance decay function (closer schools weighted higher)
        - School district reputation
        - Special programs (GT, magnet, etc.)
        """
        schools = property_data.get("schools", [])
        if not schools:
            return self._create_no_school_data_score()

        # Extract ratings by school level
        elementary_rating = None
        middle_rating = None
        high_rating = None
        top_school_name = None
        max_rating = 0

        for school in schools:
            rating = school.get("rating", 5)
            school_type = school.get("type", "").lower()
            name = school.get("name", "")

            if "elementary" in school_type:
                elementary_rating = rating
            elif "middle" in school_type:
                middle_rating = rating
            elif "high" in school_type:
                high_rating = rating

            if rating > max_rating:
                max_rating = rating
                top_school_name = name

        # Calculate average rating with level weighting
        ratings = []
        if elementary_rating:
            ratings.extend([elementary_rating] * 3)  # Weight elementary higher for families
        if middle_rating:
            ratings.append(middle_rating)
        if high_rating:
            ratings.append(high_rating)

        if not ratings:
            return self._create_no_school_data_score()

        average_rating = sum(ratings) / len(ratings)

        # Distance penalty (placeholder - would integrate with actual distances)
        distance_penalty = 0.1  # Assume reasonable distance for now

        # Normalize rating (5-10 scale to 0-1)
        normalized_rating = (average_rating - 5) / 5
        overall_score = max(0, min(1, normalized_rating * (1 - distance_penalty)))

        # Generate reasoning
        if average_rating >= 9:
            quality_desc = "excellent"
        elif average_rating >= 8:
            quality_desc = "very good"
        elif average_rating >= 7:
            quality_desc = "good"
        elif average_rating >= 6:
            quality_desc = "average"
        else:
            quality_desc = "below average"

        reasoning = f"Schools rated {average_rating:.1f}/10 ({quality_desc}). Top school: {top_school_name}"

        return SchoolScore(
            elementary_rating=elementary_rating,
            middle_rating=middle_rating,
            high_rating=high_rating,
            average_rating=average_rating,
            distance_penalty=distance_penalty,
            overall_score=overall_score,
            top_school_name=top_school_name,
            reasoning=reasoning,
        )

    def calculate_commute_score(self, property_data: Dict[str, Any], preferences: Dict[str, Any]) -> CommuteScore:
        """
        Calculate commute convenience score.

        Factors:
        - Distance/time to downtown core
        - Distance/time to specified workplace
        - Public transit accessibility
        - Highway access and traffic patterns
        - Commute alternatives (WFH-friendly areas)
        """
        address = property_data.get("address", {})
        neighborhood = address.get("neighborhood", "").lower()
        city = address.get("city", "").lower()

        # Estimate commute times based on neighborhood (placeholder for real API)
        to_downtown_minutes = self._estimate_downtown_commute(neighborhood, city)
        to_workplace_minutes = self._estimate_workplace_commute(neighborhood, preferences.get("workplace_location"))

        # Public transit access based on neighborhood
        public_transit_access = self._assess_public_transit(neighborhood, city)

        # Highway access assessment
        highway_access = self._assess_highway_access(neighborhood, city)

        # Calculate overall commute score
        # Favor shorter commutes with good transportation options
        commute_factors = []

        if to_downtown_minutes:
            # Ideal commute: under 20 min = 1.0, 20-30 = 0.8, 30-45 = 0.6, 45+ = 0.3
            if to_downtown_minutes <= 20:
                downtown_score = 1.0
            elif to_downtown_minutes <= 30:
                downtown_score = 0.8
            elif to_downtown_minutes <= 45:
                downtown_score = 0.6
            else:
                downtown_score = 0.3
            commute_factors.append(downtown_score * 0.4)

        if to_workplace_minutes:
            # Similar scoring for workplace commute
            if to_workplace_minutes <= 15:
                workplace_score = 1.0
            elif to_workplace_minutes <= 25:
                workplace_score = 0.8
            elif to_workplace_minutes <= 40:
                workplace_score = 0.6
            else:
                workplace_score = 0.3
            commute_factors.append(workplace_score * 0.4)

        commute_factors.extend([public_transit_access * 0.1, highway_access * 0.1])

        overall_score = sum(commute_factors) if commute_factors else 0.5

        # Generate reasoning
        reasoning_parts = []
        if to_downtown_minutes:
            reasoning_parts.append(f"~{to_downtown_minutes} min to downtown")
        if to_workplace_minutes:
            reasoning_parts.append(f"~{to_workplace_minutes} min to workplace")
        if public_transit_access > 0.7:
            reasoning_parts.append("good public transit")
        if highway_access > 0.7:
            reasoning_parts.append("excellent highway access")

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Commute analysis pending"

        return CommuteScore(
            to_downtown_minutes=to_downtown_minutes,
            to_workplace_minutes=to_workplace_minutes,
            public_transit_access=public_transit_access,
            highway_access=highway_access,
            overall_score=overall_score,
            reasoning=reasoning,
        )

    def calculate_walkability_score(
        self, property_data: Dict[str, Any], preferences: Dict[str, Any]
    ) -> WalkabilityScore:
        """
        Calculate walkability and urban amenities score.

        Factors:
        - Walk Score (if available from API or cached data)
        - Nearby restaurants, shops, services
        - Grocery store proximity
        - Parks and recreation access
        - Pedestrian infrastructure
        """
        address = property_data.get("address", {})
        neighborhood = address.get("neighborhood", "").lower()
        city = address.get("city", "").lower()

        # Check for cached/known Walk Score
        walk_score = self._get_walk_score(neighborhood, city)

        # Count nearby amenities from neighborhood profile
        amenities_data = self._get_neighborhood_amenities(neighborhood, city)
        nearby_amenities_count = amenities_data.get("total_amenities", 0)

        # Estimate distances (would integrate with real mapping API)
        grocery_distance = amenities_data.get("grocery_distance_miles", 2.0)
        restaurant_density = amenities_data.get("restaurant_density", 0.5)
        park_access = amenities_data.get("park_access_score", 0.5)

        # Calculate overall walkability score
        if walk_score:
            # Use Walk Score if available (0-100 scale)
            base_score = walk_score / 100
        else:
            # Calculate from amenities
            base_score = min(1.0, (nearby_amenities_count / 20) * 0.7 + 0.3)

        # Adjust for specific factors
        grocery_factor = 1.0 if grocery_distance <= 0.5 else max(0.3, 1.0 - grocery_distance * 0.2)
        restaurant_factor = min(1.0, restaurant_density)
        park_factor = park_access

        overall_score = base_score * 0.5 + grocery_factor * 0.2 + restaurant_factor * 0.2 + park_factor * 0.1

        # Generate reasoning
        if walk_score:
            walkability_desc = self._walk_score_description(walk_score)
            reasoning = f"Walk Score: {walk_score}/100 ({walkability_desc})"
        else:
            reasoning = f"{nearby_amenities_count} amenities nearby"

        if grocery_distance <= 0.5:
            reasoning += ", walking distance to grocery"

        return WalkabilityScore(
            walk_score=walk_score,
            nearby_amenities_count=nearby_amenities_count,
            grocery_distance_miles=grocery_distance,
            restaurant_density=restaurant_density,
            park_access=park_access,
            overall_score=overall_score,
            reasoning=reasoning,
        )

    def calculate_safety_score(self, property_data: Dict[str, Any], preferences: Dict[str, Any]) -> SafetyScore:
        """
        Calculate neighborhood safety score.

        Factors:
        - Crime statistics (if available)
        - Neighborhood safety ratings
        - Police response times
        - Community factors (HOA, gated, etc.)
        - Perceived safety indicators
        """
        address = property_data.get("address", {})
        neighborhood = address.get("neighborhood", "").lower()
        city = address.get("city", "").lower()
        zip_code = address.get("zip", "")

        # Get safety data from neighborhood profiles
        safety_data = self._get_neighborhood_safety(neighborhood, city, zip_code)

        crime_rate = safety_data.get("crime_rate_per_1000")
        safety_rating = safety_data.get("safety_rating")  # 1-10 scale
        response_time = safety_data.get("police_response_minutes")

        # Calculate overall safety score
        if safety_rating:
            # Normalize 1-10 scale to 0-1
            base_score = (safety_rating - 1) / 9
        else:
            # Default to moderate safety
            base_score = 0.6

        # Adjust for crime rate if available
        if crime_rate:
            # Lower crime rate = higher safety
            # Typical range: 10-50 crimes per 1000 people
            crime_factor = max(0.2, 1.0 - (crime_rate - 10) / 40)
            base_score = (base_score + crime_factor) / 2

        # Bonus for community features
        features = property_data.get("features", [])
        description = property_data.get("description", "")
        all_text = " ".join(features + [description]).lower()

        safety_features = ["gated", "security", "safe", "quiet", "family-friendly"]
        safety_bonus = sum(0.05 for feature in safety_features if feature in all_text)

        overall_score = min(1.0, base_score + safety_bonus)

        # Generate reasoning
        reasoning_parts = []
        if safety_rating:
            reasoning_parts.append(f"Neighborhood safety: {safety_rating:.1f}/10")
        if crime_rate:
            reasoning_parts.append(f"Crime rate: {crime_rate:.1f} per 1000 residents")
        if safety_bonus > 0:
            reasoning_parts.append("Additional safety features noted")

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Safety assessment based on neighborhood data"

        return SafetyScore(
            crime_rate_per_1000=crime_rate,
            neighborhood_safety_rating=safety_rating,
            police_response_time=response_time,
            overall_score=overall_score,
            reasoning=reasoning,
        )

    def calculate_amenities_proximity(self, property_data: Dict[str, Any], preferences: Dict[str, Any]) -> float:
        """
        Calculate proximity to important amenities.

        Factors:
        - Healthcare facilities
        - Shopping centers
        - Recreation facilities
        - Educational institutions
        - Entertainment venues
        """
        address = property_data.get("address", {})
        neighborhood = address.get("neighborhood", "").lower()
        city = address.get("city", "").lower()

        # Get amenities data
        amenities = self._get_neighborhood_amenities(neighborhood, city)

        # Score different amenity types
        healthcare_score = min(1.0, amenities.get("healthcare_count", 0) / 3)
        shopping_score = min(1.0, amenities.get("shopping_count", 0) / 5)
        recreation_score = amenities.get("recreation_score", 0.5)
        education_score = min(1.0, amenities.get("education_count", 0) / 2)

        # Weighted average
        overall_score = healthcare_score * 0.3 + shopping_score * 0.3 + recreation_score * 0.2 + education_score * 0.2

        return overall_score

    # Helper methods for data retrieval and estimation

    def _load_lifestyle_data(self):
        """Load cached lifestyle data for neighborhoods."""
        try:
            lifestyle_data_path = Path(__file__).parent.parent / "data" / "enrichment" / "lifestyle_data.json"
            if lifestyle_data_path.exists():
                with open(lifestyle_data_path, "r") as f:
                    self.lifestyle_data = json.load(f)
            else:
                # Create default data structure
                self.lifestyle_data = self._create_default_lifestyle_data()
                self._save_lifestyle_data()
        except Exception as e:
            logger.warning(f"Could not load lifestyle data: {e}")
            self.lifestyle_data = self._create_default_lifestyle_data()

    def _load_neighborhood_profiles(self):
        """Load neighborhood-specific profiles and scores."""
        # This would typically come from external data sources
        # For now, create a basic profile database
        self.neighborhood_profiles = {
            "etiwanda": {
                "walk_score": 85,
                "safety_rating": 7.5,
                "downtown_commute_min": 15,
                "amenities": {"total_amenities": 25, "grocery_distance_miles": 0.3},
                "crime_rate_per_1000": 15.2,
            },
            "rancho etiwanda": {
                "walk_score": 35,
                "safety_rating": 9.0,
                "downtown_commute_min": 35,
                "amenities": {"total_amenities": 12, "grocery_distance_miles": 2.0},
                "crime_rate_per_1000": 8.1,
            },
            "east rancho_cucamonga": {
                "walk_score": 92,
                "safety_rating": 6.8,
                "downtown_commute_min": 8,
                "amenities": {"total_amenities": 35, "grocery_distance_miles": 0.2},
                "crime_rate_per_1000": 22.5,
            },
            "avery ranch": {
                "walk_score": 25,
                "safety_rating": 8.5,
                "downtown_commute_min": 40,
                "amenities": {"total_amenities": 8, "grocery_distance_miles": 3.0},
                "crime_rate_per_1000": 9.3,
            },
            "chaffey district": {
                "walk_score": 95,
                "safety_rating": 7.2,
                "downtown_commute_min": 10,
                "amenities": {"total_amenities": 40, "grocery_distance_miles": 0.1},
                "crime_rate_per_1000": 18.7,
            },
        }

    def _create_default_lifestyle_data(self) -> Dict[str, Any]:
        """Create default lifestyle data structure."""
        return {
            "version": "1.0",
            "last_updated": datetime.utcnow().isoformat(),
            "data_sources": ["cached", "estimated"],
            "neighborhoods": {},
            "commute_hubs": {
                "downtown_rancho_cucamonga": {"lat": 30.2672, "lng": -97.7431},
                "ut_campus": {"lat": 30.2849, "lng": -97.7341},
                "ontario_mills": {"lat": 30.3987, "lng": -97.7262},
            },
        }

    def _save_lifestyle_data(self):
        """Save lifestyle data to cache file."""
        try:
            lifestyle_data_path = Path(__file__).parent.parent / "data" / "enrichment"
            lifestyle_data_path.mkdir(parents=True, exist_ok=True)

            with open(lifestyle_data_path / "lifestyle_data.json", "w") as f:
                json.dump(self.lifestyle_data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save lifestyle data: {e}")

    def _estimate_downtown_commute(self, neighborhood: str, city: str) -> Optional[int]:
        """Estimate commute time to downtown."""
        if city != "rancho_cucamonga":
            return None

        profile = self.neighborhood_profiles.get(neighborhood, {})
        return profile.get("downtown_commute_min")

    def _estimate_workplace_commute(self, neighborhood: str, workplace: Optional[str]) -> Optional[int]:
        """Estimate commute time to specified workplace."""
        if not workplace:
            return None

        # Basic workplace mapping (would integrate with real mapping API)
        workplace_commutes = {
            "ontario_mills": {"etiwanda": 25, "rancho etiwanda": 15, "east rancho_cucamonga": 30},
            "ut campus": {"etiwanda": 10, "chaffey district": 5, "east rancho_cucamonga": 15},
            "downtown": {"etiwanda": 15, "east rancho_cucamonga": 8, "chaffey district": 10},
        }

        workplace_lower = workplace.lower()
        for location, commutes in workplace_commutes.items():
            if location in workplace_lower:
                return commutes.get(neighborhood)

        return None

    def _assess_public_transit(self, neighborhood: str, city: str) -> float:
        """Assess public transit access (0-1 scale)."""
        # Rancho Cucamonga public transit assessment
        good_transit = ["east rancho_cucamonga", "chaffey district", "etiwanda"]
        moderate_transit = ["south rancho_cucamonga", "north rancho_cucamonga"]

        if neighborhood in good_transit:
            return 0.8
        elif neighborhood in moderate_transit:
            return 0.5
        else:
            return 0.2

    def _assess_highway_access(self, neighborhood: str, city: str) -> float:
        """Assess highway access quality (0-1 scale)."""
        # Major highway access in Rancho Cucamonga
        excellent_access = ["rancho etiwanda", "avery ranch", "circle c ranch"]
        good_access = ["etiwanda", "east rancho_cucamonga"]

        if neighborhood in excellent_access:
            return 0.9
        elif neighborhood in good_access:
            return 0.7
        else:
            return 0.5

    def _get_walk_score(self, neighborhood: str, city: str) -> Optional[int]:
        """Get Walk Score for the area."""
        profile = self.neighborhood_profiles.get(neighborhood, {})
        return profile.get("walk_score")

    def _get_neighborhood_amenities(self, neighborhood: str, city: str) -> Dict[str, Any]:
        """Get amenities data for neighborhood."""
        profile = self.neighborhood_profiles.get(neighborhood, {})
        return profile.get(
            "amenities",
            {
                "total_amenities": 10,
                "grocery_distance_miles": 1.5,
                "restaurant_density": 0.5,
                "park_access_score": 0.5,
                "healthcare_count": 1,
                "shopping_count": 2,
                "recreation_score": 0.5,
                "education_count": 1,
            },
        )

    def _get_neighborhood_safety(self, neighborhood: str, city: str, zip_code: str) -> Dict[str, Any]:
        """Get safety data for neighborhood."""
        profile = self.neighborhood_profiles.get(neighborhood, {})
        return {
            "safety_rating": profile.get("safety_rating", 6.0),
            "crime_rate_per_1000": profile.get("crime_rate_per_1000", 20.0),
            "police_response_minutes": profile.get("police_response_minutes", 8),
        }

    def _walk_score_description(self, score: int) -> str:
        """Convert Walk Score to description."""
        if score >= 90:
            return "Walker's Paradise"
        elif score >= 70:
            return "Very Walkable"
        elif score >= 50:
            return "Somewhat Walkable"
        elif score >= 25:
            return "Car-Dependent"
        else:
            return "Car-Dependent"

    def _determine_lifestyle_weights(
        self, preferences: Dict[str, Any], lead_profile: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Determine lifestyle factor weights based on lead profile."""

        # Default weights
        weights = {"schools": 0.20, "commute": 0.25, "walkability": 0.25, "safety": 0.20, "amenities": 0.10}

        # Adjust based on preferences
        if preferences.get("bedrooms", 0) >= 3:
            # Likely family - prioritize schools and safety
            weights.update({"schools": 0.35, "safety": 0.25, "commute": 0.20, "walkability": 0.15, "amenities": 0.05})

        elif preferences.get("property_type", "").lower() in ["condo", "townhome"]:
            # Likely young professional - prioritize walkability and commute
            weights.update({"commute": 0.35, "walkability": 0.30, "amenities": 0.15, "safety": 0.15, "schools": 0.05})

        # Adjust for workplace specified
        if preferences.get("workplace_location"):
            weights["commute"] = min(0.4, weights["commute"] + 0.1)

        return weights

    def _create_no_school_data_score(self) -> SchoolScore:
        """Create school score when no school data is available."""
        return SchoolScore(
            elementary_rating=None,
            middle_rating=None,
            high_rating=None,
            average_rating=5.0,  # Neutral
            distance_penalty=0.0,
            overall_score=0.5,  # Neutral
            top_school_name=None,
            reasoning="School data not available for this area",
        )


# Demo function
def demo_lifestyle_intelligence():
    """Demo the lifestyle intelligence service."""
    print("🏡 Lifestyle Intelligence Service Demo\n")

    service = LifestyleIntelligenceService()

    # Test properties from different neighborhoods
    test_properties = [
        {
            "id": "test_1",
            "address": {"neighborhood": "Alta Loma", "city": "Rancho Cucamonga", "zip": "91737"},
            "schools": [
                {"name": "Mathews Elementary", "rating": 9, "type": "Elementary"},
                {"name": "McCallum High School", "rating": 8, "type": "High"},
            ],
            "features": ["Walkable neighborhood", "Family-friendly"],
        },
        {
            "id": "test_2",
            "address": {"neighborhood": "North Rancho", "city": "Rancho Cucamonga", "zip": "91739"},
            "schools": [
                {"name": "River Ridge Elementary", "rating": 9, "type": "Elementary"},
                {"name": "Vandegrift High School", "rating": 10, "type": "High"},
            ],
            "features": ["Gated community", "Resort-style amenities"],
        },
    ]

    test_preferences = [
        {"bedrooms": 3, "workplace_location": "downtown"},  # Family
        {"bedrooms": 1, "property_type": "condo", "workplace_location": "UT Campus"},  # Young professional
    ]

    for i, (prop, prefs) in enumerate(zip(test_properties, test_preferences)):
        print(f"\n{'=' * 60}")
        print(f"Property {i + 1}: {prop['address']['neighborhood']}")
        print(f"Lead Profile: {prefs}")
        print(f"{'=' * 60}")

        lifestyle_scores = service.calculate_lifestyle_score(prop, prefs)

        print(f"\n📚 Schools: {lifestyle_scores.schools.overall_score:.2f}")
        print(f"    {lifestyle_scores.schools.reasoning}")

        print(f"\n🚗 Commute: {lifestyle_scores.commute.overall_score:.2f}")
        print(f"    {lifestyle_scores.commute.reasoning}")

        print(f"\n🚶 Walkability: {lifestyle_scores.walkability.overall_score:.2f}")
        print(f"    {lifestyle_scores.walkability.reasoning}")

        print(f"\n🔒 Safety: {lifestyle_scores.safety.overall_score:.2f}")
        print(f"    {lifestyle_scores.safety.reasoning}")

        print(f"\n🏆 Overall Lifestyle Score: {lifestyle_scores.overall_score:.2f}")


if __name__ == "__main__":
    demo_lifestyle_intelligence()
