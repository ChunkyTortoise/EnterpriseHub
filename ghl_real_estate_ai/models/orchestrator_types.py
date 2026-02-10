"""
TypedDict definitions for Claude orchestrator contexts and responses.

Following the pattern established in seller_bot_state.py, these types provide
structured type hints for dictionary-based data across orchestrator services.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, TypedDict

from typing_extensions import NotRequired

# ============================================================================
# Claude Orchestrator Types
# ============================================================================


class OrchestratorContext(TypedDict, total=False):
    """Context data passed to Claude orchestrator requests."""

    # Core identifiers
    contact_id: str
    lead_id: str
    tenant_id: str
    session_id: str

    # Conversation data
    conversation_history: list[dict[str, str]]
    query_type: str
    task_type: str
    complexity: str

    # Intelligence context
    lead_data: dict[str, Any]
    market_data: dict[str, Any]
    bot_intelligence: dict[str, Any]
    semantic_memory: str
    extracted_preferences: dict[str, Any]

    # Scoring context
    scoring: dict[str, Any]
    churn_analysis: dict[str, Any]
    behavioral_score: Any  # BehavioralScore object

    # Platform context
    platform_context: dict[str, Any]
    jorge_preferences: dict[str, Any]
    concierge_mode: str
    intelligence_scope: str
    session_history: list[dict[str, Any]]


class ParsedOrchestratorResponse(TypedDict, total=False):
    """Parsed response from Claude orchestrator with structured metadata."""

    # Primary response
    response_text: str
    content: str
    reasoning: str

    # Confidence and quality
    confidence_score: float
    confidence: float

    # Actionable outputs
    recommended_actions: list[dict[str, Any]]
    risk_factors: list[dict[str, Any]]
    opportunities: list[dict[str, Any]]

    # Script generation
    script_variants: list[dict[str, str]]

    # Performance metadata
    response_time_ms: int
    input_tokens: int
    output_tokens: int
    model: str
    provider: str
    cache_hit: bool

    # Tool execution
    tool_executions: list[dict[str, Any]]

    # Error handling
    error: bool
    error_type: str
    parsing_error: str
    parsing_failed: bool


class MemoryContext(TypedDict, total=False):
    """Memory service context data."""

    relevant_knowledge: str
    conversation_history: list[dict[str, str]]
    extracted_preferences: dict[str, Any]
    memory_type: str
    entity_id: str
    content: str
    timestamp: str


class LeadAnalysisContext(TypedDict, total=False):
    """Context for lead analysis operations."""

    lead_id: str
    memory: dict[str, Any]
    scoring: dict[str, Any]
    churn_analysis: dict[str, Any]
    behavioral_score: Any  # BehavioralScore object
    activity_data: dict[str, Any]
    lead_profile: dict[str, Any]
    market_context: dict[str, Any]


# ============================================================================
# Concierge Orchestrator Types
# ============================================================================


class ConciergeSession(TypedDict, total=False):
    """Session context for Claude Concierge."""

    session_id: str
    user_id: str
    user_name: str
    current_page: str
    user_role: str
    device_type: str

    # Context data
    context: dict[str, Any]
    preferences: dict[str, Any]
    history: list[dict[str, str]]
    conversation_history: list[dict[str, str]]

    # Activity tracking
    activity_history: list[dict[str, Any]]
    current_context: str
    detected_intent: str
    competency_level: str


class ConciergeGuidanceContext(TypedDict, total=False):
    """Context for generating concierge guidance."""

    # Platform state
    platform_context: dict[str, Any]
    jorge_preferences: dict[str, Any]
    concierge_mode: str
    intelligence_scope: str
    session_history: list[dict[str, Any]]

    # Live data
    active_leads: list[dict[str, Any]]
    bot_statuses: dict[str, Any]
    user_activity: list[dict[str, Any]]
    business_metrics: dict[str, Any]
    active_properties: list[dict[str, Any]]

    # Market intelligence
    market_conditions: dict[str, Any]
    priority_actions: list[dict[str, Any]]
    pending_notifications: list[dict[str, Any]]


class ConciergeResponse(TypedDict, total=False):
    """Structured response from concierge agent."""

    # Core guidance
    primary_guidance: str
    urgency_level: str
    confidence_score: float
    reasoning: str

    # Actions
    immediate_actions: list[dict[str, Any]]
    background_tasks: list[dict[str, Any]]
    follow_up_reminders: list[dict[str, Any]]

    # Intelligence
    page_specific_tips: list[str]
    bot_coordination_suggestions: list[dict[str, Any]]
    revenue_optimization_ideas: list[dict[str, Any]]

    # Alerts
    risk_alerts: list[dict[str, Any]]
    opportunity_highlights: list[dict[str, Any]]
    learning_insights: list[dict[str, Any]]

    # Advanced
    handoff_recommendation: dict[str, Any]

    # Metadata
    response_time_ms: int
    data_sources_used: list[str]
    generated_at: str


# ============================================================================
# Follow-up Engine Types
# ============================================================================


class FollowupContext(TypedDict, total=False):
    """Context for autonomous follow-up operations."""

    lead_id: str
    sequence_day: int
    channel: str
    last_response_time: str
    lead_temperature: str

    # Lead intelligence
    previous_interactions: list[dict[str, str]]
    activity_data: dict[str, Any]
    follow_up_history: list[dict[str, Any]]
    response_data: dict[str, Any]
    lead_profile: dict[str, Any]

    # Agent context
    swarm_analysis: Any  # SwarmIntelligenceResult object
    behavioral_score: Any  # BehavioralScore object
    market_context: dict[str, Any]
    arbitrage_info: str

    # Conversation
    conversation_history: list[dict[str, str]]


class FollowupRecommendationData(TypedDict, total=False):
    """Data structure for follow-up recommendations."""

    agent_type: str
    confidence: float
    recommended_action: str
    reasoning: str

    # Timing
    optimal_timing: str
    timing_optimization: dict[str, Any]

    # Channel and content
    suggested_channel: str
    suggested_message: str
    subject_line: str

    # Escalation
    escalation_needed: bool

    # Metadata
    metadata: dict[str, Any]
    personalization_factors: list[str]
    analysis_method: str


class FollowupTaskData(TypedDict, total=False):
    """Data structure for follow-up tasks."""

    task_id: str
    lead_id: str
    contact_id: str
    channel: str
    message: str
    scheduled_time: str
    status: str
    priority: int
    intent_level: str

    # Metadata
    metadata: dict[str, Any]
    agent_consensus_score: float
    participating_agents: list[str]
    swarm_consensus_score: float
    lead_intelligence_score: float

    # Execution
    created_at: str
    executed_at: str
    result: dict[str, Any]


# ============================================================================
# Agent Mesh Types
# ============================================================================


class AgentTaskPayload(TypedDict, total=False):
    """Payload for agent mesh tasks."""

    # Task definition
    task_type: str
    action: str
    data: dict[str, Any]

    # Context
    lead_id: str
    contact_id: str
    conversation_history: list[dict[str, str]]

    # Requirements
    capabilities_required: list[str]
    max_cost: float
    deadline: str


class AgentTaskResult(TypedDict, total=False):
    """Result from agent task execution."""

    status: str
    message: str
    data: dict[str, Any]

    # Performance
    tokens_used: int
    execution_time: float
    cost: float

    # Metadata
    agent_id: str
    completed_at: str
    error: str


class AgentMetricsData(TypedDict, total=False):
    """Performance metrics for agents."""

    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    success_rate: float

    # Performance
    average_response_time: float
    tokens_used: int
    cost_incurred: float
    uptime_percent: float

    # Activity
    last_activity: str
    current_tasks: int
    load_factor: float


# ============================================================================
# Personalization & Intelligence Types
# ============================================================================


class PersonalizationData(TypedDict, total=False):
    """Data for personalizing responses and content."""

    # Lead info
    name: str
    email: str
    phone: str
    location: str
    budget: float
    property_type: str
    timeline: str

    # Preferences
    communication_style: str
    preferred_channels: list[str]
    tone: str
    interests: list[str]

    # Demographics
    demographics: dict[str, Any]
    market_area: str
    motivation: str


class MarketContextData(TypedDict, total=False):
    """Market intelligence context."""

    market_trend: str
    inventory_level: str
    median_price_trend: str
    price_direction: str

    # Arbitrage
    arbitrage_opportunities: list[dict[str, Any]]
    market_overview: dict[str, Any]

    # Timing
    market_urgency: bool
    market_messaging: str


class SessionMetadata(TypedDict, total=False):
    """Metadata about a user session."""

    timestamp: str
    session_start: str
    last_activity: str
    duration_seconds: float

    # Activity
    page: str
    action: str
    device: str
    user_agent: str

    # Tracking
    engagement_score: float
    interaction_count: int
    frustration_indicators: list[str]
