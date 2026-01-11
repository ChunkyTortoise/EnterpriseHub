"""
Agent Performance Data Models
================================

Comprehensive data models for advanced AI coaching analytics, performance prediction,
and gamification systems. Supports $60K-90K/year productivity improvements through
intelligent coaching and performance optimization.

Models:
- AgentPerformanceMetrics: Core agent performance tracking
- CoachingSession: Individual coaching session data
- PerformancePrediction: ML-based success prediction
- GamificationAchievement: Achievement and reward tracking
- LearningPathProgress: Personalized learning journey tracking
- CoachingROIMetrics: Financial impact measurement
"""

from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field, validator, root_validator
from pydantic.config import ConfigDict


# Enums for standardized values
class AgentSkillLevel(str, Enum):
    """Agent skill proficiency levels."""
    NOVICE = "novice"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MASTER = "master"


class CoachingInterventionType(str, Enum):
    """Types of coaching interventions."""
    REAL_TIME_GUIDANCE = "real_time_guidance"
    POST_CALL_REVIEW = "post_call_review"
    SKILL_DEVELOPMENT = "skill_development"
    PERFORMANCE_CORRECTION = "performance_correction"
    BEST_PRACTICE_SHARING = "best_practice_sharing"
    ADVANCED_TECHNIQUE = "advanced_technique"
    MOTIVATION_BOOST = "motivation_boost"


class PerformanceTrend(str, Enum):
    """Performance trajectory indicators."""
    RAPIDLY_IMPROVING = "rapidly_improving"
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    RAPIDLY_DECLINING = "rapidly_declining"
    VOLATILE = "volatile"


class AchievementCategory(str, Enum):
    """Categories for gamification achievements."""
    CONVERSION_MASTERY = "conversion_mastery"
    COMMUNICATION_EXCELLENCE = "communication_excellence"
    SPEED_EFFICIENCY = "speed_efficiency"
    LEARNING_DEDICATION = "learning_dedication"
    OBJECTION_HANDLING = "objection_handling"
    RELATIONSHIP_BUILDING = "relationship_building"
    MARKET_KNOWLEDGE = "market_knowledge"
    TECHNOLOGY_ADOPTION = "technology_adoption"


# Core Performance Models
class ConversationPerformanceMetrics(BaseModel):
    """Metrics for individual conversation performance."""
    model_config = ConfigDict(validate_assignment=True)

    conversation_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Core metrics
    duration_seconds: int = Field(..., ge=0)
    lead_score_improvement: float = Field(default=0.0, ge=-100.0, le=100.0)
    qualification_completion_rate: float = Field(default=0.0, ge=0.0, le=100.0)
    objections_handled: int = Field(default=0, ge=0)
    next_steps_secured: bool = Field(default=False)

    # Quality indicators
    sentiment_score: float = Field(default=5.0, ge=0.0, le=10.0)
    engagement_score: float = Field(default=5.0, ge=0.0, le=10.0)
    rapport_score: float = Field(default=5.0, ge=0.0, le=10.0)
    professionalism_score: float = Field(default=5.0, ge=0.0, le=10.0)

    # Outcome indicators
    appointment_scheduled: bool = Field(default=False)
    property_tour_scheduled: bool = Field(default=False)
    offer_submitted: bool = Field(default=False)

    # AI coaching integration
    coaching_suggestions_used: int = Field(default=0, ge=0)
    ai_intervention_count: int = Field(default=0, ge=0)
    coaching_effectiveness_score: float = Field(default=0.0, ge=0.0, le=10.0)


class AgentPerformanceMetrics(BaseModel):
    """Comprehensive agent performance tracking."""
    model_config = ConfigDict(validate_assignment=True)

    agent_id: str
    measurement_period_start: datetime
    measurement_period_end: datetime

    # Productivity metrics
    total_conversations: int = Field(default=0, ge=0)
    total_leads_contacted: int = Field(default=0, ge=0)
    average_conversations_per_hour: float = Field(default=0.0, ge=0.0)
    average_conversation_duration_seconds: int = Field(default=0, ge=0)

    # Quality metrics
    average_lead_score_improvement: float = Field(default=0.0)
    average_qualification_completion_rate: float = Field(default=0.0, ge=0.0, le=100.0)
    average_sentiment_score: float = Field(default=5.0, ge=0.0, le=10.0)
    average_engagement_score: float = Field(default=5.0, ge=0.0, le=10.0)

    # Conversion metrics
    appointments_scheduled: int = Field(default=0, ge=0)
    property_tours_scheduled: int = Field(default=0, ge=0)
    offers_submitted: int = Field(default=0, ge=0)
    conversion_rate: float = Field(default=0.0, ge=0.0, le=100.0)

    # Skill proficiency
    objection_handling_score: float = Field(default=5.0, ge=0.0, le=10.0)
    rapport_building_score: float = Field(default=5.0, ge=0.0, le=10.0)
    closing_effectiveness_score: float = Field(default=5.0, ge=0.0, le=10.0)
    market_knowledge_score: float = Field(default=5.0, ge=0.0, le=10.0)

    # AI coaching metrics
    coaching_sessions_completed: int = Field(default=0, ge=0)
    coaching_suggestions_used: int = Field(default=0, ge=0)
    coaching_acceptance_rate: float = Field(default=0.0, ge=0.0, le=100.0)

    # Performance trend
    performance_trend: PerformanceTrend = Field(default=PerformanceTrend.STABLE)
    trend_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # Overall scores
    overall_performance_score: float = Field(default=50.0, ge=0.0, le=100.0)
    productivity_score: float = Field(default=50.0, ge=0.0, le=100.0)
    quality_score: float = Field(default=50.0, ge=0.0, le=100.0)


class PerformancePrediction(BaseModel):
    """ML-based performance and success prediction."""
    model_config = ConfigDict(validate_assignment=True)

    agent_id: str
    prediction_id: str
    prediction_timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Success probability predictions
    next_conversation_success_probability: float = Field(..., ge=0.0, le=1.0)
    appointment_scheduling_probability: float = Field(..., ge=0.0, le=1.0)
    conversion_probability: float = Field(..., ge=0.0, le=1.0)

    # Performance trajectory
    predicted_performance_trend: PerformanceTrend
    predicted_performance_score_7days: float = Field(..., ge=0.0, le=100.0)
    predicted_performance_score_30days: float = Field(..., ge=0.0, le=100.0)

    # Skill development predictions
    predicted_skill_improvements: Dict[str, float] = Field(default_factory=dict)
    estimated_time_to_next_level: Optional[int] = Field(None, description="Hours to next skill level")

    # Optimal coaching timing
    optimal_coaching_intervention_time: Optional[datetime] = Field(None)
    intervention_urgency: float = Field(default=0.0, ge=0.0, le=10.0)
    recommended_intervention_type: Optional[CoachingInterventionType] = Field(None)

    # Lead assignment optimization
    optimal_lead_types: List[str] = Field(default_factory=list)
    avoid_lead_types: List[str] = Field(default_factory=list)
    recommended_lead_complexity: AgentSkillLevel

    # Model metadata
    model_version: str = Field(default="1.0.0")
    prediction_confidence: float = Field(..., ge=0.0, le=1.0)
    feature_importance: Dict[str, float] = Field(default_factory=dict)


class CoachingSession(BaseModel):
    """Individual coaching session tracking."""
    model_config = ConfigDict(validate_assignment=True)

    session_id: str
    agent_id: str
    session_timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Session details
    intervention_type: CoachingInterventionType
    session_duration_seconds: int = Field(..., ge=0)
    trigger_event: str = Field(..., description="What triggered this coaching session")

    # Content
    coaching_focus_areas: List[str] = Field(default_factory=list)
    key_insights_shared: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)
    resources_provided: List[str] = Field(default_factory=list)

    # Effectiveness
    agent_engagement_score: float = Field(default=5.0, ge=0.0, le=10.0)
    content_relevance_score: float = Field(default=5.0, ge=0.0, le=10.0)
    immediate_application_success: bool = Field(default=False)

    # Follow-up
    follow_up_scheduled: bool = Field(default=False)
    follow_up_date: Optional[datetime] = Field(None)
    skills_to_practice: List[str] = Field(default_factory=list)

    # Impact measurement
    pre_session_performance_score: float = Field(..., ge=0.0, le=100.0)
    post_session_performance_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    performance_improvement: Optional[float] = Field(None)
    roi_value_dollars: Optional[Decimal] = Field(None)


class LearningPathProgress(BaseModel):
    """Personalized learning journey tracking."""
    model_config = ConfigDict(validate_assignment=True)

    agent_id: str
    learning_path_id: str
    path_name: str

    # Progress tracking
    total_modules: int = Field(..., gt=0)
    completed_modules: int = Field(default=0, ge=0)
    current_module: Optional[str] = Field(None)
    completion_percentage: float = Field(default=0.0, ge=0.0, le=100.0)

    # Skill development
    target_skill_level: AgentSkillLevel
    current_skill_level: AgentSkillLevel
    skill_gap_score: float = Field(default=0.0, ge=0.0, le=100.0)

    # Time tracking
    started_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_completion_date: Optional[datetime] = Field(None)
    last_activity_date: datetime = Field(default_factory=datetime.utcnow)
    total_learning_time_hours: float = Field(default=0.0, ge=0.0)

    # Adaptive learning
    learning_pace: str = Field(default="normal")  # slow, normal, fast, accelerated
    difficulty_adjustments: List[Dict[str, Any]] = Field(default_factory=list)
    personalization_factors: Dict[str, Any] = Field(default_factory=dict)

    # Performance correlation
    performance_improvement_since_start: float = Field(default=0.0)
    skills_acquired: List[str] = Field(default_factory=list)
    certifications_earned: List[str] = Field(default_factory=list)


class GamificationAchievement(BaseModel):
    """Achievement and reward tracking."""
    model_config = ConfigDict(validate_assignment=True)

    achievement_id: str
    agent_id: str
    achievement_name: str
    category: AchievementCategory

    # Achievement details
    description: str
    points_awarded: int = Field(..., gt=0)
    badge_icon: str
    difficulty_level: int = Field(..., ge=1, le=5)

    # Unlock criteria
    criteria_description: str
    criteria_threshold: float
    current_progress: float = Field(default=0.0)
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)

    # Status
    unlocked: bool = Field(default=False)
    unlocked_at: Optional[datetime] = Field(None)
    times_earned: int = Field(default=0, ge=0)

    # Social/competitive
    achievement_rarity: float = Field(default=0.0, ge=0.0, le=100.0)
    leaderboard_position: Optional[int] = Field(None)
    shareable: bool = Field(default=True)


class CoachingROIMetrics(BaseModel):
    """Financial impact and ROI measurement."""
    model_config = ConfigDict(validate_assignment=True)

    agent_id: str
    measurement_period_start: datetime
    measurement_period_end: datetime

    # Time savings
    training_time_reduction_hours: float = Field(default=0.0, ge=0.0)
    onboarding_time_reduction_hours: float = Field(default=0.0, ge=0.0)
    average_time_to_productivity_hours: float = Field(default=0.0, ge=0.0)

    # Productivity gains
    conversations_per_hour_improvement: float = Field(default=0.0)
    conversion_rate_improvement_percent: float = Field(default=0.0)
    average_deal_value_improvement_percent: float = Field(default=0.0)

    # Financial impact (annualized)
    time_savings_value_annual: Decimal = Field(default=Decimal("0.00"))
    productivity_gains_value_annual: Decimal = Field(default=Decimal("0.00"))
    quality_improvement_value_annual: Decimal = Field(default=Decimal("0.00"))
    total_roi_value_annual: Decimal = Field(default=Decimal("0.00"))

    # Cost comparison
    traditional_training_cost_annual: Decimal = Field(default=Decimal("0.00"))
    ai_coaching_cost_annual: Decimal = Field(default=Decimal("0.00"))
    cost_savings_annual: Decimal = Field(default=Decimal("0.00"))
    roi_percentage: float = Field(default=0.0)

    # Quality metrics
    error_reduction_rate: float = Field(default=0.0, ge=0.0, le=100.0)
    customer_satisfaction_improvement: float = Field(default=0.0)
    retention_improvement_rate: float = Field(default=0.0, ge=0.0, le=100.0)


class AgentBenchmarkComparison(BaseModel):
    """Comparison against team and industry benchmarks."""
    model_config = ConfigDict(validate_assignment=True)

    agent_id: str
    comparison_timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Team comparison
    team_average_performance_score: float = Field(..., ge=0.0, le=100.0)
    agent_performance_score: float = Field(..., ge=0.0, le=100.0)
    percentile_rank_in_team: float = Field(..., ge=0.0, le=100.0)

    # Industry comparison
    industry_average_performance_score: float = Field(..., ge=0.0, le=100.0)
    percentile_rank_in_industry: float = Field(..., ge=0.0, le=100.0)

    # Skill-specific comparisons
    skill_benchmarks: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    strengths: List[str] = Field(default_factory=list)
    improvement_areas: List[str] = Field(default_factory=list)

    # Progress tracking
    improvement_rate_vs_team: float = Field(default=0.0)
    improvement_rate_vs_industry: float = Field(default=0.0)
    gap_to_top_performer: float = Field(default=0.0)


class CoachingAnalyticsSnapshot(BaseModel):
    """Comprehensive analytics snapshot for dashboard."""
    model_config = ConfigDict(validate_assignment=True)

    snapshot_id: str
    agent_id: str
    snapshot_timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Current performance
    current_metrics: AgentPerformanceMetrics
    performance_prediction: PerformancePrediction
    benchmark_comparison: AgentBenchmarkComparison

    # Coaching insights
    recent_coaching_sessions: List[CoachingSession] = Field(default_factory=list)
    active_learning_paths: List[LearningPathProgress] = Field(default_factory=list)
    unlocked_achievements: List[GamificationAchievement] = Field(default_factory=list)

    # ROI tracking
    roi_metrics: CoachingROIMetrics

    # Recommendations
    recommended_focus_areas: List[str] = Field(default_factory=list)
    suggested_coaching_interventions: List[Dict[str, Any]] = Field(default_factory=list)
    next_best_actions: List[str] = Field(default_factory=list)


# Export all models
__all__ = [
    # Enums
    "AgentSkillLevel",
    "CoachingInterventionType",
    "PerformanceTrend",
    "AchievementCategory",

    # Core models
    "ConversationPerformanceMetrics",
    "AgentPerformanceMetrics",
    "PerformancePrediction",
    "CoachingSession",
    "LearningPathProgress",
    "GamificationAchievement",
    "CoachingROIMetrics",
    "AgentBenchmarkComparison",
    "CoachingAnalyticsSnapshot",
]
