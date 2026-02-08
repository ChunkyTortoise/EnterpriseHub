"""
Scoring Context and Data Models
Standardized data structures for property scoring
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class PropertyType(Enum):
    """Standardized property types"""

    SINGLE_FAMILY = "single_family"
    TOWNHOME = "townhome"
    CONDO = "condo"
    MULTI_FAMILY = "multi_family"
    OTHER = "other"


class PriorityLevel(Enum):
    """Lead preference priority levels"""

    MUST_HAVE = "must_have"
    HIGHLY_PREFERRED = "highly_preferred"
    PREFERRED = "preferred"
    NICE_TO_HAVE = "nice_to_have"


@dataclass
class LocationPreference:
    """Structured location preference"""

    primary_areas: List[str] = field(default_factory=list)
    secondary_areas: List[str] = field(default_factory=list)
    excluded_areas: List[str] = field(default_factory=list)
    max_commute_time: Optional[int] = None  # minutes
    walkability_importance: float = 0.5  # 0-1 scale


@dataclass
class FeaturePreference:
    """Feature preference with priority"""

    feature: str
    priority: PriorityLevel
    specific_requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BudgetConstraints:
    """Detailed budget constraints"""

    max_budget: float
    comfortable_budget: Optional[float] = None
    absolute_max: Optional[float] = None
    down_payment_percentage: Optional[float] = None
    monthly_payment_target: Optional[float] = None


@dataclass
class LeadPreferences:
    """
    Comprehensive lead preferences structure

    This standardizes how lead preferences are represented across
    all scoring strategies
    """

    # Basic requirements
    budget_constraints: BudgetConstraints
    property_types: List[PropertyType] = field(default_factory=list)
    min_bedrooms: Optional[int] = None
    max_bedrooms: Optional[int] = None
    min_bathrooms: Optional[float] = None

    # Location preferences
    location_preferences: LocationPreference = field(default_factory=LocationPreference)

    # Feature preferences
    feature_preferences: List[FeaturePreference] = field(default_factory=list)

    # Timeline and urgency
    urgency_level: str = "medium"  # low, medium, high
    move_in_timeline: Optional[str] = None

    # Previous interactions and learning
    viewed_properties: List[str] = field(default_factory=list)
    rejected_properties: List[str] = field(default_factory=list)
    interested_properties: List[str] = field(default_factory=list)
    feedback_history: List[Dict[str, Any]] = field(default_factory=list)

    # Contextual information
    lead_source: Optional[str] = None
    agent_notes: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    @classmethod
    def from_legacy_format(cls, legacy_prefs: Dict[str, Any]) -> "LeadPreferences":
        """Convert from legacy preference format"""
        budget = legacy_prefs.get("budget", 800000)
        budget_constraints = BudgetConstraints(max_budget=budget, comfortable_budget=budget * 0.9)

        # Convert property type
        property_types = []
        legacy_type = legacy_prefs.get("property_type", "").lower()
        if "single family" in legacy_type:
            property_types.append(PropertyType.SINGLE_FAMILY)
        elif "condo" in legacy_type:
            property_types.append(PropertyType.CONDO)
        elif "townhome" in legacy_type:
            property_types.append(PropertyType.TOWNHOME)

        # Convert location
        location_pref = LocationPreference()
        if legacy_prefs.get("location"):
            location_pref.primary_areas = [legacy_prefs["location"]]

        # Convert features
        feature_preferences = []
        for must_have in legacy_prefs.get("must_haves", []):
            feature_preferences.append(FeaturePreference(must_have, PriorityLevel.MUST_HAVE))
        for nice_to_have in legacy_prefs.get("nice_to_haves", []):
            feature_preferences.append(FeaturePreference(nice_to_have, PriorityLevel.NICE_TO_HAVE))

        return cls(
            budget_constraints=budget_constraints,
            property_types=property_types,
            min_bedrooms=legacy_prefs.get("bedrooms"),
            location_preferences=location_pref,
            feature_preferences=feature_preferences,
        )

    def to_legacy_format(self) -> Dict[str, Any]:
        """Convert to legacy format for backward compatibility"""
        return {
            "budget": self.budget_constraints.max_budget,
            "bedrooms": self.min_bedrooms,
            "location": (
                self.location_preferences.primary_areas[0] if self.location_preferences.primary_areas else None
            ),
            "property_type": (self.property_types[0].value.replace("_", " ") if self.property_types else ""),
            "must_haves": [fp.feature for fp in self.feature_preferences if fp.priority == PriorityLevel.MUST_HAVE],
            "nice_to_haves": [
                fp.feature for fp in self.feature_preferences if fp.priority == PriorityLevel.NICE_TO_HAVE
            ],
        }


@dataclass
class ScoringContext:
    """
    Context information for scoring operations

    Provides additional context that may influence scoring decisions
    """

    # Market context
    market_conditions: Dict[str, Any] = field(default_factory=dict)
    comparative_properties: List[Dict[str, Any]] = field(default_factory=list)

    # Operational context
    scoring_purpose: str = "lead_matching"  # lead_matching, market_analysis, etc.
    urgency: str = "normal"  # high, normal, low
    agent_id: Optional[str] = None

    # Configuration overrides
    score_weights: Optional[Dict[str, float]] = None
    feature_boosts: Optional[Dict[str, float]] = None

    # Caching and performance
    enable_caching: bool = True
    cache_ttl: int = 300  # seconds

    # Quality and compliance
    quality_threshold: float = 0.6
    compliance_checks: List[str] = field(default_factory=list)

    def get_effective_weights(self, default_weights: Dict[str, float]) -> Dict[str, float]:
        """Get effective scoring weights with any overrides applied"""
        if not self.score_weights:
            return default_weights

        effective = default_weights.copy()
        effective.update(self.score_weights)
        return effective
