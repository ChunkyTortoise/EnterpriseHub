"""
Bot Intelligence Context Data Models - Phase 3.3
================================================

Data models for Bot Intelligence Middleware context aggregation.
Structures for property intelligence, conversation intelligence, and preference intelligence.

Features:
- Serializable models for caching and API responses
- Fallback context creation for error scenarios
- Performance metrics tracking
- Integration with Phase 2 intelligence services

Author: Jorge's Real Estate AI Platform - Phase 3.3 Bot Workflow Integration
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class PropertyIntelligence:
    """Property matching intelligence context for bot enhancement."""

    top_matches: List[Dict[str, Any]] = field(default_factory=list)
    match_count: int = 0
    best_match_score: float = 0.0
    presentation_strategy: Optional[str] = None
    optimal_presentation_time: Optional[str] = None
    behavioral_reasoning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PropertyIntelligence":
        """Create instance from dictionary."""
        return cls(**data)

    @classmethod
    def create_empty(cls) -> "PropertyIntelligence":
        """Create empty property intelligence for fallback scenarios."""
        return cls(
            top_matches=[],
            match_count=0,
            best_match_score=0.0,
            presentation_strategy=None,
            optimal_presentation_time=None,
            behavioral_reasoning="No property intelligence available",
        )


@dataclass
class ConversationIntelligence:
    """Conversation analysis intelligence context for bot enhancement."""

    objections_detected: List[Dict[str, Any]] = field(default_factory=list)
    overall_sentiment: float = 0.0
    sentiment_trend: str = "stable"
    conversation_quality_score: float = 50.0
    coaching_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    response_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    next_best_action: Optional[str] = None
    urgency_indicators: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationIntelligence":
        """Create instance from dictionary."""
        return cls(**data)

    @classmethod
    def create_empty(cls) -> "ConversationIntelligence":
        """Create empty conversation intelligence for fallback scenarios."""
        return cls(
            objections_detected=[],
            overall_sentiment=0.0,
            sentiment_trend="stable",
            conversation_quality_score=50.0,
            coaching_opportunities=[],
            response_recommendations=[],
            next_best_action=None,
            urgency_indicators=[],
        )


@dataclass
class PreferenceIntelligence:
    """Preference learning intelligence context for bot enhancement."""

    preference_profile: Dict[str, Any] = field(default_factory=dict)
    profile_completeness: float = 0.0
    budget_range: Optional[Dict[str, Any]] = None
    urgency_level: float = 0.5
    location_preferences: Dict[str, float] = field(default_factory=dict)
    feature_preferences: Dict[str, Any] = field(default_factory=dict)
    timeline_preference: Optional[str] = None
    confidence_score: float = 0.0
    preference_gaps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PreferenceIntelligence":
        """Create instance from dictionary."""
        return cls(**data)

    @classmethod
    def create_empty(cls) -> "PreferenceIntelligence":
        """Create empty preference intelligence for fallback scenarios."""
        return cls(
            preference_profile={},
            profile_completeness=0.0,
            budget_range=None,
            urgency_level=0.5,
            location_preferences={},
            feature_preferences={},
            timeline_preference=None,
            confidence_score=0.0,
            preference_gaps=["No preference data available"],
        )


@dataclass
class IntelligencePerformanceMetrics:
    """Performance metrics for intelligence gathering operations."""

    total_time_ms: float = 0.0
    property_matching_time_ms: float = 0.0
    conversation_analysis_time_ms: float = 0.0
    preference_learning_time_ms: float = 0.0
    cache_hit: bool = False
    cache_time_ms: float = 0.0
    service_failures: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    def mark_completion(self):
        """Mark operation completion and calculate total time."""
        self.completed_at = datetime.now(timezone.utc)
        if self.started_at:
            total_seconds = (self.completed_at - self.started_at).total_seconds()
            self.total_time_ms = total_seconds * 1000

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["started_at"] = self.started_at.isoformat() if self.started_at else None
        data["completed_at"] = self.completed_at.isoformat() if self.completed_at else None
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntelligencePerformanceMetrics":
        """Create instance from dictionary."""
        # Convert ISO strings back to datetime objects
        if data.get("started_at"):
            data["started_at"] = datetime.fromisoformat(data["started_at"].replace("Z", "+00:00"))
        if data.get("completed_at"):
            data["completed_at"] = datetime.fromisoformat(data["completed_at"].replace("Z", "+00:00"))
        return cls(**data)


@dataclass
class BotIntelligenceContext:
    """
    Comprehensive intelligence context for bot decision enhancement.

    Aggregates property, conversation, and preference intelligence for
    enhanced bot responses and decision making.
    """

    # Core identification
    lead_id: str
    location_id: str
    bot_type: str

    # Intelligence components
    property_intelligence: PropertyIntelligence
    conversation_intelligence: ConversationIntelligence
    preference_intelligence: PreferenceIntelligence

    # Metadata
    performance_metrics: IntelligencePerformanceMetrics
    cache_hit: bool = False
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Aggregated insights for quick bot access
    composite_engagement_score: float = 0.5  # 0-1 overall engagement
    recommended_approach: Optional[str] = None  # jorge-confrontational, jorge-consultative, lead-nurture
    priority_insights: List[str] = field(default_factory=list)  # Top 3 actionable insights

    def to_json(self) -> str:
        """Serialize to JSON for caching."""
        data = {
            "lead_id": self.lead_id,
            "location_id": self.location_id,
            "bot_type": self.bot_type,
            "property_intelligence": self.property_intelligence.to_dict(),
            "conversation_intelligence": self.conversation_intelligence.to_dict(),
            "preference_intelligence": self.preference_intelligence.to_dict(),
            "performance_metrics": self.performance_metrics.to_dict(),
            "cache_hit": self.cache_hit,
            "generated_at": self.generated_at.isoformat(),
            "composite_engagement_score": self.composite_engagement_score,
            "recommended_approach": self.recommended_approach,
            "priority_insights": self.priority_insights,
        }
        return json.dumps(data, default=str)

    @classmethod
    def from_json(cls, json_str: str) -> "BotIntelligenceContext":
        """Deserialize from JSON."""
        data = json.loads(json_str)

        # Reconstruct nested objects
        data["property_intelligence"] = PropertyIntelligence.from_dict(data["property_intelligence"])
        data["conversation_intelligence"] = ConversationIntelligence.from_dict(data["conversation_intelligence"])
        data["preference_intelligence"] = PreferenceIntelligence.from_dict(data["preference_intelligence"])
        data["performance_metrics"] = IntelligencePerformanceMetrics.from_dict(data["performance_metrics"])

        # Convert ISO string back to datetime
        data["generated_at"] = datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00"))

        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "lead_id": self.lead_id,
            "location_id": self.location_id,
            "bot_type": self.bot_type,
            "property_intelligence": self.property_intelligence.to_dict(),
            "conversation_intelligence": self.conversation_intelligence.to_dict(),
            "preference_intelligence": self.preference_intelligence.to_dict(),
            "performance_metrics": self.performance_metrics.to_dict(),
            "cache_hit": self.cache_hit,
            "generated_at": self.generated_at.isoformat(),
            "composite_engagement_score": self.composite_engagement_score,
            "recommended_approach": self.recommended_approach,
            "priority_insights": self.priority_insights,
        }

    @classmethod
    def create_fallback(
        cls, lead_id: str, location_id: str, bot_type: str, error_context: Optional[str] = None
    ) -> "BotIntelligenceContext":
        """
        Create fallback intelligence context when services fail.

        Provides neutral defaults that won't break bot operations while
        indicating that enhanced intelligence is unavailable.
        """
        # Create performance metrics with failure recorded
        performance_metrics = IntelligencePerformanceMetrics()
        performance_metrics.service_failures = ["fallback_context_created"]
        if error_context:
            performance_metrics.service_failures.append(error_context)
        performance_metrics.mark_completion()

        return cls(
            lead_id=lead_id,
            location_id=location_id,
            bot_type=bot_type,
            property_intelligence=PropertyIntelligence.create_empty(),
            conversation_intelligence=ConversationIntelligence.create_empty(),
            preference_intelligence=PreferenceIntelligence.create_empty(),
            performance_metrics=performance_metrics,
            cache_hit=False,
            composite_engagement_score=0.5,  # Neutral engagement level
            recommended_approach="standard",  # Safe default approach
            priority_insights=["Enhanced intelligence temporarily unavailable"],
        )

    def calculate_composite_scores(self):
        """Calculate composite scores from individual intelligence components."""
        # Composite engagement score (0-1)
        property_factor = min(self.property_intelligence.best_match_score / 100.0, 1.0)
        conversation_factor = max(0.0, (self.conversation_intelligence.overall_sentiment + 1.0) / 2.0)
        preference_factor = self.preference_intelligence.profile_completeness

        self.composite_engagement_score = (property_factor + conversation_factor + preference_factor) / 3.0

        # Determine recommended approach based on intelligence
        if self.bot_type == "jorge-seller":
            # Seller bot: use confrontational approach for high engagement, consultative for lower
            if self.composite_engagement_score > 0.7:
                self.recommended_approach = "jorge-confrontational"
            elif self.composite_engagement_score > 0.4:
                self.recommended_approach = "jorge-consultative"
            else:
                self.recommended_approach = "jorge-nurture"
        elif self.bot_type == "jorge-buyer":
            # Buyer bot: always consultative but adjust intensity
            if self.composite_engagement_score > 0.6:
                self.recommended_approach = "jorge-consultative-high"
            else:
                self.recommended_approach = "jorge-consultative-gentle"
        else:
            # Lead bot: focus on nurturing and qualification
            self.recommended_approach = "lead-nurture"

        # Generate priority insights
        insights = []

        # Property insights
        if self.property_intelligence.match_count > 0:
            insights.append(f"Found {self.property_intelligence.match_count} behavioral property matches")

        # Conversation insights
        if len(self.conversation_intelligence.objections_detected) > 0:
            insights.append(
                f"Detected {len(self.conversation_intelligence.objections_detected)} objections requiring attention"
            )

        # Preference insights
        if self.preference_intelligence.profile_completeness > 0.7:
            insights.append("High preference completeness - ready for targeted recommendations")
        elif self.preference_intelligence.profile_completeness < 0.3:
            insights.append("Low preference data - focus on discovery questions")

        # Sentiment insights
        if self.conversation_intelligence.overall_sentiment > 0.3:
            insights.append("Positive sentiment - opportunity for advancement")
        elif self.conversation_intelligence.overall_sentiment < -0.3:
            insights.append("Negative sentiment - requires careful handling")

        self.priority_insights = insights[:3]  # Keep top 3 insights
