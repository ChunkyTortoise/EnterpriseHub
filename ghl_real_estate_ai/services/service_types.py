"""
Service TypedDict Definitions

Central location for TypedDict definitions used across services.
These replace Dict[str, Any] annotations with proper type definitions.

Part of Spec 07: Type Safety - TypedDict Conversion
"""

from typing import Any, Dict, List, Optional, TypedDict

# ─────────────────────────────────────────────────────────────────────────────
# Handoff Types
# ─────────────────────────────────────────────────────────────────────────────


class BudgetRange(TypedDict, total=False):
    """Budget range for property search."""

    min: float
    max: float
    currency: str


class CMASummary(TypedDict, total=False):
    """Comparative Market Analysis summary."""

    estimated_value: float
    low_estimate: float
    high_estimate: float
    comparables_count: int
    avg_days_on_market: float


class KeyInsights(TypedDict, total=False):
    """Key insights from source bot for handoff."""

    qualification_score: float
    temperature: str
    urgency_level: str
    objection_types: List[str]
    conversation_summary: str


class HandoffData(TypedDict, total=False):
    """Data passed during bot-to-bot handoff."""

    source_bot: str
    target_bot: str
    contact_id: str
    location_id: str
    budget_range: BudgetRange
    property_address: Optional[str]
    cma_summary: CMASummary
    key_insights: KeyInsights
    conversation_history: List[Dict[str, Any]]
    timestamp: str


class HandoffActions(TypedDict, total=False):
    """GHL actions to execute a handoff."""

    action_type: str
    contact_id: str
    tags_to_add: List[str]
    tags_to_remove: List[str]
    custom_fields: Dict[str, Any]
    note: Optional[str]


class HandoffOutcome(TypedDict, total=False):
    """Outcome record for a handoff."""

    route: str
    outcome: str  # "completed", "failed", "blocked"
    timestamp: float
    metadata: Dict[str, Any]


# ─────────────────────────────────────────────────────────────────────────────
# Performance & Metrics Types
# ─────────────────────────────────────────────────────────────────────────────


class PerformanceStats(TypedDict, total=False):
    """Performance statistics for monitoring."""

    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    cache_hit_rate: float


class BotMetricsSnapshot(TypedDict, total=False):
    """Snapshot of bot metrics at a point in time."""

    bot_type: str
    timestamp: float
    total_interactions: int
    avg_response_time_ms: float
    handoff_count: int
    cache_hits: int
    cache_misses: int


class DeferralStats(TypedDict, total=False):
    """Statistics for deferred handoffs."""

    total_deferrals: int
    successful_retries: int
    failed_retries: int
    avg_retry_delay_seconds: float


# ─────────────────────────────────────────────────────────────────────────────
# Experiment & A/B Testing Types
# ─────────────────────────────────────────────────────────────────────────────


class ExperimentVariant(TypedDict, total=False):
    """A/B test variant configuration."""

    variant_name: str
    description: str
    config: Dict[str, Any]
    traffic_percentage: float


class ExperimentData(TypedDict, total=False):
    """A/B test experiment data."""

    experiment_name: str
    description: str
    status: str  # "draft", "running", "paused", "completed"
    variants: List[ExperimentVariant]
    start_date: Optional[str]
    end_date: Optional[str]
    created_at: str


class VariantConfig(TypedDict, total=False):
    """Configuration for an experiment variant."""

    variant_name: str
    prompt_template: Optional[str]
    temperature: Optional[float]
    max_tokens: Optional[int]
    custom_params: Dict[str, Any]


class MetricsSnapshot(TypedDict, total=False):
    """Snapshot of metrics for experiment analysis."""

    variant_name: str
    sample_size: int
    conversion_rate: float
    avg_value: float
    confidence_interval: tuple


# ─────────────────────────────────────────────────────────────────────────────
# Follow-up Types
# ─────────────────────────────────────────────────────────────────────────────


class FollowUpConfig(TypedDict, total=False):
    """Configuration for follow-up sequences."""

    follow_up_type: str  # "qualification", "temperature", "behavioral"
    sequence_position: int
    delay_hours: int
    message_template: str
    actions: List[HandoffActions]
    variant_config: Optional[VariantConfig]


class FollowUpResult(TypedDict, total=False):
    """Result of a follow-up action."""

    contact_id: str
    location_id: str
    success: bool
    message_sent: Optional[str]
    actions_executed: List[str]
    next_follow_up: Optional[FollowUpConfig]


# ─────────────────────────────────────────────────────────────────────────────
# Lead & Contact Types
# ─────────────────────────────────────────────────────────────────────────────


class SellerData(TypedDict, total=False):
    """Seller information from GHL contact."""

    contact_id: str
    location_id: str
    name: str
    phone: str
    email: Optional[str]
    property_address: Optional[str]
    listing_price: Optional[float]
    motivation_type: Optional[str]
    timeline: Optional[str]
    custom_fields: Dict[str, Any]
    tags: List[str]


class BuyerData(TypedDict, total=False):
    """Buyer information from GHL contact."""

    contact_id: str
    location_id: str
    name: str
    phone: str
    email: Optional[str]
    budget_min: Optional[float]
    budget_max: Optional[float]
    preferred_locations: List[str]
    property_type: Optional[str]
    timeline: Optional[str]
    preapproval_status: Optional[str]
    custom_fields: Dict[str, Any]
    tags: List[str]


class LeadProfile(TypedDict, total=False):
    """Comprehensive lead profile."""

    lead_id: str
    contact_id: str
    location_id: str
    source: str
    temperature: str  # "hot", "warm", "cold"
    qualification_score: float
    budget_range: BudgetRange
    timeline: str
    property_interest: Optional[str]
    conversation_history: List[Dict[str, Any]]
    last_contacted: Optional[str]
    next_action: Optional[str]


# ─────────────────────────────────────────────────────────────────────────────
# Webhook Types
# ─────────────────────────────────────────────────────────────────────────────


class WebhookPayload(TypedDict, total=False):
    """Generic webhook payload structure."""

    webhook_id: str
    location_id: str
    contact_id: str
    event_type: str
    timestamp: str
    data: Dict[str, Any]


class WebhookData(TypedDict, total=False):
    """Data extracted from webhook payloads."""

    contact_id: str
    location_id: str
    message: Optional[str]
    event_type: str
    custom_fields: Dict[str, Any]
    tags: List[str]


# ─────────────────────────────────────────────────────────────────────────────
# Market Data Types
# ─────────────────────────────────────────────────────────────────────────────


class MarketData(TypedDict, total=False):
    """Market information for analysis."""

    market_id: str
    location: str
    median_price: float
    avg_days_on_market: float
    inventory_count: int
    price_trend: str  # "rising", "stable", "falling"
    seasonality_factor: float


class PropertyData(TypedDict, total=False):
    """Property information for matching."""

    property_id: str
    address: str
    price: float
    bedrooms: int
    bathrooms: float
    sqft: int
    property_type: str
    year_built: Optional[int]
    amenities: List[str]
    market_data: MarketData


# ─────────────────────────────────────────────────────────────────────────────
# ROI & Attribution Types
# ─────────────────────────────────────────────────────────────────────────────


class ROIData(TypedDict, total=False):
    """ROI calculation data."""

    source_name: str
    total_leads: int
    converted_leads: int
    revenue: float
    cost: float
    roi_percentage: float
    conversion_rate: float


class AttributionResult(TypedDict, total=False):
    """Attribution analysis result."""

    lead_id: str
    source: str
    touchpoints: List[Dict[str, Any]]
    attributed_revenue: float
    confidence: float


# ─────────────────────────────────────────────────────────────────────────────
# Alert Types
# ─────────────────────────────────────────────────────────────────────────────


class AlertData(TypedDict, total=False):
    """Alert data structure."""

    alert_id: str
    rule_name: str
    severity: str  # "critical", "warning", "info"
    message: str
    triggered_at: float
    acknowledged: bool
    acknowledged_by: Optional[str]
    metadata: Dict[str, Any]


class AlertRule(TypedDict, total=False):
    """Alert rule configuration."""

    name: str
    condition: str  # JSON-encoded callable
    severity: str
    enabled: bool
    cooldown_seconds: int


# ─────────────────────────────────────────────────────────────────────────────
# Analytics Types
# ─────────────────────────────────────────────────────────────────────────────


class AnalyticsSummary(TypedDict, total=False):
    """Summary of analytics data."""

    total_events: int
    unique_contacts: int
    time_range_start: str
    time_range_end: str
    metrics: Dict[str, float]


class TimeSeriesPoint(TypedDict, total=False):
    """Single point in a time series."""

    timestamp: str
    value: float
    metadata: Dict[str, Any]


# ─────────────────────────────────────────────────────────────────────────────
# Response Types
# ─────────────────────────────────────────────────────────────────────────────


class ServiceResponse(TypedDict, total=False):
    """Standard service response structure."""

    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    metadata: Dict[str, Any]


class ErrorDetails(TypedDict, total=False):
    """Error information structure."""

    code: str
    message: str
    field: Optional[str]
    details: Dict[str, Any]
