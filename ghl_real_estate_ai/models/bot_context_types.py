"""
Bot Context TypedDicts

Structured type definitions for bot conversation contexts, responses, and handoff decisions.
Replaces Dict[str, Any] with specific, well-documented types for better type safety and IDE support.

Usage:
    from ghl_real_estate_ai.models.bot_context_types import BotResponse, ConversationMessage

    def process_message(history: list[ConversationMessage]) -> BotResponse:
        ...
"""

from __future__ import annotations

from typing import Any, TypedDict

from typing_extensions import NotRequired

# ── Conversation & Message Types ─────────────────────────────────────


class ConversationMessage(TypedDict, total=False):
    """A single message in a conversation history.
    
    Used in conversation_history lists across all bots.
    """

    role: str  # "user", "assistant", "system"
    content: str  # Message content
    timestamp: NotRequired[str]  # ISO format timestamp
    message: NotRequired[str]  # Alternate key for content (legacy)


class BotMetadata(TypedDict, total=False):
    """Optional metadata attached to bot operations."""

    location_id: NotRequired[str]
    source: NotRequired[str]
    channel: NotRequired[str]  # "sms", "email", "web", "voice"
    campaign_id: NotRequired[str]
    custom_fields: NotRequired[dict[str, Any]]


# ── Bot Response Types ────────────────────────────────────────────────


class LeadBotResponse(TypedDict, total=False):
    """Return value from LeadBotWorkflow.process_lead_conversation()."""

    conversation_id: str
    lead_id: str
    response_content: str
    current_step: str  # "awaiting_input", "qualifying", "nurturing"
    engagement_status: str  # "active", "dormant", "qualified", "error"
    temperature: NotRequired[str]  # "hot", "warm", "lukewarm", "cold"
    handoff_signals: NotRequired[dict[str, Any]]
    intelligence_context: NotRequired[Any]
    error: NotRequired[str]  # Error message on failure
    ab_test: NotRequired[dict[str, Any]]  # experiment_id + variant


class BuyerBotResponse(TypedDict, total=False):
    """Return value from JorgeBuyerBot.process_buyer_conversation()."""

    buyer_id: str
    lead_id: str
    response_content: str
    current_step: str  # "budget", "timeline", "preferences", "decision_makers"
    engagement_status: str  # "active", "dormant", "qualified", "opted_out"
    financial_readiness: float  # 0-100
    buying_motivation_score: NotRequired[float]  # 0-100
    buyer_temperature: NotRequired[str]  # "hot", "warm", "lukewarm", "cold"
    handoff_signals: NotRequired[dict[str, Any]]
    matched_properties: NotRequired[list[dict[str, Any]]]
    opt_out_detected: NotRequired[bool]  # True when TCPA opt-out triggered
    actions: NotRequired[list[dict[str, Any]]]  # GHL tag actions
    ab_test: NotRequired[dict[str, Any]]  # experiment_id + variant


class SellerBotResponse(TypedDict, total=False):
    """Return value from JorgeSellerBot.process_seller_message()."""

    lead_id: str
    seller_id: NotRequired[str]
    response_content: str
    current_step: NotRequired[str]
    engagement_status: NotRequired[str]  # "qualification", "error", etc.
    frs_score: float  # Financial Readiness Score (0-100)
    pcs_score: float  # Psychological Commitment Score (0-100)
    temperature: NotRequired[str]  # "hot", "warm", "lukewarm", "cold"
    handoff_signals: dict[str, Any]  # intent signals from handoff service
    is_qualified: NotRequired[bool]
    next_action: NotRequired[str]
    ab_test: NotRequired[dict[str, Any]]  # experiment_id + variant


# ── Intent & Handoff Types ────────────────────────────────────────────


class IntentSignals(TypedDict, total=False):
    """Intent detection signals for handoff evaluation."""

    buyer_intent_score: float  # 0.0-1.0
    seller_intent_score: float  # 0.0-1.0
    detected_intent_phrases: list[str]
    qualification_score: NotRequired[float]
    temperature: NotRequired[str]
    budget_range: NotRequired[dict[str, float]]
    property_address: NotRequired[str]
    cma_summary: NotRequired[dict[str, Any]]
    conversation_summary: NotRequired[str]
    key_insights: NotRequired[dict[str, Any]]
    urgency_level: NotRequired[str]


class HandoffDecisionDict(TypedDict, total=False):
    """Handoff decision data (TypedDict version of HandoffDecision dataclass)."""

    source_bot: str  # "lead", "buyer", "seller"
    target_bot: str  # "lead", "buyer", "seller"
    reason: str  # "buyer_intent_detected", "seller_intent_detected"
    confidence: float  # 0.0-1.0
    context: dict[str, Any]
    should_handoff: NotRequired[bool]


class EnrichedHandoffContext(TypedDict, total=False):
    """Enriched context data for cross-bot handoff."""

    source_qualification_score: float
    source_temperature: str
    budget_range: NotRequired[dict[str, Any]]
    property_address: NotRequired[str]
    cma_summary: NotRequired[dict[str, Any]]
    conversation_summary: str
    key_insights: dict[str, Any]
    urgency_level: str  # "browsing", "3_months", "immediate"


# ── Performance & Metrics Types ───────────────────────────────────────


class PerformanceMetrics(TypedDict, total=False):
    """Performance statistics from PerformanceTracker.get_bot_stats()."""

    p50: float  # P50 latency in ms
    p95: float  # P95 latency in ms
    p99: float  # P99 latency in ms
    mean: float
    min: float
    max: float
    count: int  # Total operations
    success_count: int
    error_count: int
    cache_hit_count: int
    cache_hit_rate: float  # 0.0-1.0
    success_rate: float  # 0.0-1.0


class SLAComplianceResult(TypedDict, total=False):
    """SLA compliance check result from PerformanceTracker.check_sla_compliance()."""

    bot_name: str
    operation: str
    compliant: bool
    p50_target: float
    p95_target: float
    p99_target: float
    p50_actual: float
    p95_actual: float
    p99_actual: float
    violations: list[str]


# ── A/B Testing Types ─────────────────────────────────────────────────


class ABTestOutcome(TypedDict, total=False):
    """A/B test outcome record from ABTestingService.record_outcome()."""

    experiment_id: str
    contact_id: str
    variant: str
    outcome: str  # "response", "engagement", "conversion", "handoff_success", "appointment_booked"
    value: float


class ABTestVariantStats(TypedDict, total=False):
    """Per-variant statistics from ABTestingService.get_experiment_results()."""

    variant: str
    impressions: int
    conversions: int
    total_value: float
    conversion_rate: float  # 0.0-1.0
    confidence_interval: tuple[float, float]


class ABTestExperimentResult(TypedDict, total=False):
    """Full A/B test result from ABTestingService.get_experiment_results()."""

    experiment_id: str
    status: str  # "active", "paused", "completed"
    variants: list[ABTestVariantStats]
    is_significant: bool
    p_value: NotRequired[float]
    winner: NotRequired[str]
    total_impressions: int
    total_conversions: int
    created_at: float
    duration_hours: float


# ── Psychology Analysis Types ─────────────────────────────────────────


class PriceDropAnalysis(TypedDict, total=False):
    """Price drop pattern analysis from SellerPsychologyAnalyzer."""

    pattern: str  # "no_drops", "aggressive_reducer", "incremental_reducer", "panic_reducer", "strategic_reducer"
    psychological_indicator: str
    total_reduction_pct: float
    avg_drop_size: float
    drop_frequency: int
    flexibility_signal: float  # 0.0-1.0


class MarketResponseAnalysis(TypedDict, total=False):
    """Market response analysis from SellerPsychologyAnalyzer."""

    market_feedback: str  # "poor", "mixed", "positive"
    seller_awareness: str  # "low", "learning", "moderate", "high"
    view_to_showing_ratio: float
    showing_to_offer_ratio: float
    engagement_quality: str  # "high_quality", "moderate_quality", "low_quality"


class BehavioralAnalysis(TypedDict, total=False):
    """Behavioral pattern analysis from SellerPsychologyAnalyzer._analyze_listing_behavior()."""

    behavioral_pattern: str  # ListingBehaviorPattern enum value
    price_drop_analysis: PriceDropAnalysis
    market_response: MarketResponseAnalysis
    listing_persistence: dict[str, Any]


class UrgencyAnalysis(TypedDict, total=False):
    """Urgency indicators from SellerPsychologyAnalyzer._analyze_urgency_indicators()."""

    urgency_level: str  # "low", "moderate", "high", "critical"
    urgency_score: float  # 0-100
    urgency_signals: list[str]
    time_pressure_factor: float  # 0.0-1.0


class MotivationAnalysis(TypedDict, total=False):
    """Motivation analysis from SellerPsychologyAnalyzer._analyze_seller_motivation()."""

    primary_motivation: str  # "emotional", "financial", "strategic", "distressed"
    motivation_scores: dict[str, int]
    motivation_confidence: float  # 0.0-1.0


class FlexibilityAnalysis(TypedDict, total=False):
    """Flexibility analysis from SellerPsychologyAnalyzer._analyze_negotiation_flexibility()."""

    flexibility_score: float  # 0-100
    flexibility_indicators: list[str]
    negotiation_openness: str  # "high", "moderate", "low"


class AIInsights(TypedDict, total=False):
    """AI-generated insights from SellerPsychologyAnalyzer._get_ai_psychological_insights()."""

    ai_emotional_assessment: str
    ai_relationship_potential: int  # 0-100
    ai_concerns: list[str]
    ai_hot_buttons: list[str]
    ai_confidence: int  # 0-100


# ── Qualification & Analysis Types ────────────────────────────────────


class QualificationData(TypedDict, total=False):
    """Qualification analysis data used across bot qualification methods."""

    lead_id: str
    qualification_score: float  # 0-100
    temperature: str  # "hot", "warm", "lukewarm", "cold"
    is_qualified: bool
    qualification_reasons: list[str]
    next_actions: list[str]
    intent_profile: NotRequired[Any]  # LeadIntentProfile or BuyerIntentProfile
    extracted_preferences: NotRequired[dict[str, Any]]


class PropertyMatchResult(TypedDict, total=False):
    """Property matching result for buyer bots."""

    property_id: str
    match_score: float  # 0.0-1.0
    property_address: str
    price: float
    bedrooms: int
    bathrooms: float
    sqft: int
    match_reasons: list[str]


# ── Handoff Analytics Types ───────────────────────────────────────────


class HandoffAnalytics(TypedDict, total=False):
    """Handoff analytics from JorgeHandoffService.get_analytics_summary()."""

    total_handoffs: int
    successful_handoffs: int
    failed_handoffs: int
    success_rate: float
    avg_processing_time_ms: float
    handoffs_by_route: dict[str, int]
    handoffs_by_hour: dict[int, int]
    peak_hour: int
    blocked_by_rate_limit: int
    blocked_by_circular: int


class LearnedAdjustments(TypedDict, total=False):
    """Learned threshold adjustments from JorgeHandoffService.get_learned_adjustments()."""

    adjustment: float  # -1.0 to 1.0
    success_rate: float  # 0.0-1.0
    sample_size: int
