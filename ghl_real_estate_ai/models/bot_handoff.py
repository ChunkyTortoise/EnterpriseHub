"""
Bot Handoff Data Models - Phase 3.2
====================================

Data models for intelligence context preservation across bot transitions.
Enables seamless handoffs between Jorge's bot ecosystem with full context preservation.

Features:
- IntelligenceSnapshot for preserving complete intelligence state
- BotTransition for transition metadata and coordination
- ContextHandoff for handoff operation tracking
- TransitionHistory for audit trail and analytics

Use Cases:
- Jorge Seller → Jorge Buyer (qualified buyer transition)
- Lead Bot → Jorge Seller (lead activation)
- Jorge Buyer → Lead Bot (dormant lead return)
- Any Bot → Manual Agent (escalation scenarios)

Author: Jorge's Real Estate AI Platform - Phase 3.2 Implementation
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class PropertyMatchSummary(TypedDict, total=False):
    """TypedDict for property match summary in handoff context."""
    property_id: str
    address: str
    price: float
    match_score: float
    key_features: List[str]


class ObjectionSummary(TypedDict, total=False):
    """TypedDict for objection summary in handoff context."""
    objection_type: str
    description: str
    resolved: bool
    resolution_notes: Optional[str]


class ResponseRecommendationSummary(TypedDict, total=False):
    """TypedDict for response recommendation summary."""
    recommendation_type: str
    suggested_response: str
    context: str


class QualificationScoreDetail(TypedDict, total=False):
    """TypedDict for qualification score details."""
    category: str
    score: float
    max_score: float
    notes: Optional[str]


class ReadinessIndicatorDetail(TypedDict, total=False):
    """TypedDict for readiness indicator details."""
    indicator: str
    value: bool
    confidence: float


class BotType(str, Enum):
    """Bot types in Jorge's ecosystem."""

    JORGE_SELLER = "jorge-seller"
    JORGE_BUYER = "jorge-buyer"
    LEAD_BOT = "lead-bot"
    AI_CONCIERGE = "ai-concierge"
    MANUAL_AGENT = "manual-agent"


class TransitionReason(str, Enum):
    """Reasons for bot transitions."""

    QUALIFIED_BUYER = "qualified_buyer"  # Seller also wants to buy
    QUALIFIED_SELLER = "qualified_seller"  # Buyer also wants to sell
    LEAD_ACTIVATED = "lead_activated"  # Lead bot → qualified bot
    DORMANT_LEAD = "dormant_lead"  # Qualified bot → lead bot
    ESCALATION_REQUESTED = "escalation"  # Any bot → manual agent
    COACHING_REQUIRED = "coaching_required"  # Bot → AI concierge
    CONVERSATION_STALLED = "conversation_stalled"  # Bot → different approach
    MANUAL_OVERRIDE = "manual_override"  # Agent intervention
    SESSION_TIMEOUT = "session_timeout"  # Automatic timeout
    CLIENT_REQUEST = "client_request"  # Client requests change


class HandoffStatus(str, Enum):
    """Status of handoff operation."""

    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"  # Some intelligence preserved
    EXPIRED = "expired"  # Context expired before retrieval


@dataclass
class PreservedIntelligence:
    """
    Core intelligence preserved across transitions.

    Optimized for serialization and caching with minimal data size.
    """

    # Property intelligence (top matches only)
    top_property_matches: List[PropertyMatchSummary] = field(default_factory=list)
    best_match_score: float = 0.0
    property_presentation_strategy: Optional[str] = None

    # Conversation intelligence (key insights)
    conversation_quality_score: float = 50.0
    overall_sentiment: float = 0.0
    sentiment_trend: str = "stable"
    key_objections_detected: List[ObjectionSummary] = field(default_factory=list)
    resolved_objections: List[ObjectionSummary] = field(default_factory=list)
    pending_objections: List[ObjectionSummary] = field(default_factory=list)
    response_recommendations: List[ResponseRecommendationSummary] = field(default_factory=list)
    # Preference intelligence (core preferences)
    budget_range: Optional[Dict[str, float]] = None
    location_preferences: Dict[str, float] = field(default_factory=dict)
    feature_preferences: Dict[str, bool] = field(default_factory=dict)
    move_timeline: Optional[str] = None
    urgency_level: float = 0.5
    profile_completeness: float = 0.0

    # Behavioral insights
    engagement_pattern: str = "responsive"
    communication_style: str = "professional"
    decision_making_style: str = "analytical"
    risk_tolerance: str = "moderate"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for caching."""
        return {
            "top_property_matches": self.top_property_matches,
            "best_match_score": self.best_match_score,
            "property_presentation_strategy": self.property_presentation_strategy,
            "conversation_quality_score": self.conversation_quality_score,
            "overall_sentiment": self.overall_sentiment,
            "sentiment_trend": self.sentiment_trend,
            "key_objections_detected": self.key_objections_detected,
            "resolved_objections": self.resolved_objections,
            "pending_objections": self.pending_objections,
            "response_recommendations": self.response_recommendations,
            "budget_range": self.budget_range,
            "location_preferences": self.location_preferences,
            "feature_preferences": self.feature_preferences,
            "move_timeline": self.move_timeline,
            "urgency_level": self.urgency_level,
            "profile_completeness": self.profile_completeness,
            "engagement_pattern": self.engagement_pattern,
            "communication_style": self.communication_style,
            "decision_making_style": self.decision_making_style,
            "risk_tolerance": self.risk_tolerance,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PreservedIntelligence":
        """Create from cached dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def create_empty(cls) -> "PreservedIntelligence":
        """Create empty intelligence for fallback."""
        return cls()


@dataclass
class IntelligenceSnapshot:
    """
    Complete intelligence snapshot for bot handoff preservation.

    Captures the complete intelligence state at transition point for
    seamless context preservation across bot ecosystem.
    """

    # Snapshot metadata
    snapshot_id: str
    lead_id: str
    location_id: str
    source_bot: BotType
    target_bot: Optional[BotType]
    snapshot_timestamp: datetime

    # Preserved intelligence data
    preserved_intelligence: PreservedIntelligence

    # Conversation context
    conversation_summary: str  # Claude-generated strategic summary
    conversation_length: int = 0
    last_message_timestamp: Optional[datetime] = None

    # Qualification data
    qualification_scores: Dict[str, float] = field(default_factory=dict)  # FRS/PCS scores
    temperature_classification: Optional[str] = None  # hot/warm/lukewarm/cold
    readiness_indicators: List[str] = field(default_factory=list)

    # Strategic guidance for target bot
    recommended_next_actions: List[str] = field(default_factory=list)
    strategic_approach: str = "consultative"  # confrontational, consultative, nurturing
    conversation_goals: List[str] = field(default_factory=list)
    warning_flags: List[str] = field(default_factory=list)

    # Transition metadata
    transition_reason: TransitionReason = TransitionReason.MANUAL_OVERRIDE
    handoff_message: str = ""
    confidence_level: float = 1.0  # 0.0-1.0 preservation confidence
    data_completeness: float = 1.0  # 0.0-1.0 data preservation ratio

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for caching."""
        return {
            "snapshot_id": self.snapshot_id,
            "lead_id": self.lead_id,
            "location_id": self.location_id,
            "source_bot": self.source_bot.value if isinstance(self.source_bot, BotType) else self.source_bot,
            "target_bot": self.target_bot.value
            if self.target_bot and isinstance(self.target_bot, BotType)
            else self.target_bot,
            "snapshot_timestamp": self.snapshot_timestamp.isoformat(),
            "preserved_intelligence": self.preserved_intelligence.to_dict(),
            "conversation_summary": self.conversation_summary,
            "conversation_length": self.conversation_length,
            "last_message_timestamp": self.last_message_timestamp.isoformat() if self.last_message_timestamp else None,
            "qualification_scores": self.qualification_scores,
            "temperature_classification": self.temperature_classification,
            "readiness_indicators": self.readiness_indicators,
            "recommended_next_actions": self.recommended_next_actions,
            "strategic_approach": self.strategic_approach,
            "conversation_goals": self.conversation_goals,
            "warning_flags": self.warning_flags,
            "transition_reason": self.transition_reason.value
            if isinstance(self.transition_reason, TransitionReason)
            else self.transition_reason,
            "handoff_message": self.handoff_message,
            "confidence_level": self.confidence_level,
            "data_completeness": self.data_completeness,
        }

    def to_json(self) -> str:
        """Serialize to JSON for Redis caching."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntelligenceSnapshot":
        """Create from cached dictionary."""
        return cls(
            snapshot_id=data["snapshot_id"],
            lead_id=data["lead_id"],
            location_id=data["location_id"],
            source_bot=BotType(data["source_bot"]),
            target_bot=BotType(data["target_bot"]) if data["target_bot"] else None,
            snapshot_timestamp=datetime.fromisoformat(data["snapshot_timestamp"]),
            preserved_intelligence=PreservedIntelligence.from_dict(data["preserved_intelligence"]),
            conversation_summary=data["conversation_summary"],
            conversation_length=data.get("conversation_length", 0),
            last_message_timestamp=datetime.fromisoformat(data["last_message_timestamp"])
            if data.get("last_message_timestamp")
            else None,
            qualification_scores=data.get("qualification_scores", {}),
            temperature_classification=data.get("temperature_classification"),
            readiness_indicators=data.get("readiness_indicators", []),
            recommended_next_actions=data.get("recommended_next_actions", []),
            strategic_approach=data.get("strategic_approach", "consultative"),
            conversation_goals=data.get("conversation_goals", []),
            warning_flags=data.get("warning_flags", []),
            transition_reason=TransitionReason(data.get("transition_reason", "manual_override")),
            handoff_message=data.get("handoff_message", ""),
            confidence_level=data.get("confidence_level", 1.0),
            data_completeness=data.get("data_completeness", 1.0),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "IntelligenceSnapshot":
        """Deserialize from JSON (Redis cache)."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def create_empty(
        cls, lead_id: str, location_id: str, source_bot: BotType, target_bot: Optional[BotType] = None
    ) -> "IntelligenceSnapshot":
        """Create empty snapshot for fallback scenarios."""
        return cls(
            snapshot_id=str(uuid.uuid4()),
            lead_id=lead_id,
            location_id=location_id,
            source_bot=source_bot,
            target_bot=target_bot,
            snapshot_timestamp=datetime.now(timezone.utc),
            preserved_intelligence=PreservedIntelligence.create_empty(),
            conversation_summary="No conversation context available",
            confidence_level=0.0,
            data_completeness=0.0,
            transition_reason=TransitionReason.MANUAL_OVERRIDE,
            handoff_message="Fallback snapshot created due to intelligence service failure",
        )


@dataclass
class BotTransition:
    """
    Metadata for bot-to-bot transition.

    Defines the complete context of a bot handoff including
    source/target bots, reason, and strategic guidance.
    """

    transition_id: str
    lead_id: str
    location_id: str
    source_bot: BotType
    target_bot: BotType
    transition_reason: TransitionReason

    # Strategic guidance
    handoff_message: str
    recommended_approach: str = "consultative"
    priority_level: str = "normal"  # low, normal, high, urgent
    expected_outcome: str = ""

    # Timing
    initiated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expected_duration_minutes: Optional[int] = None

    # Context
    triggering_event: Optional[str] = None
    agent_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for event publishing."""
        return {
            "transition_id": self.transition_id,
            "lead_id": self.lead_id,
            "location_id": self.location_id,
            "source_bot": self.source_bot.value,
            "target_bot": self.target_bot.value,
            "transition_reason": self.transition_reason.value,
            "handoff_message": self.handoff_message,
            "recommended_approach": self.recommended_approach,
            "priority_level": self.priority_level,
            "expected_outcome": self.expected_outcome,
            "initiated_at": self.initiated_at.isoformat(),
            "expected_duration_minutes": self.expected_duration_minutes,
            "triggering_event": self.triggering_event,
            "agent_notes": self.agent_notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BotTransition":
        """Create from dictionary."""
        return cls(
            transition_id=data["transition_id"],
            lead_id=data["lead_id"],
            location_id=data["location_id"],
            source_bot=BotType(data["source_bot"]),
            target_bot=BotType(data["target_bot"]),
            transition_reason=TransitionReason(data["transition_reason"]),
            handoff_message=data["handoff_message"],
            recommended_approach=data.get("recommended_approach", "consultative"),
            priority_level=data.get("priority_level", "normal"),
            expected_outcome=data.get("expected_outcome", ""),
            initiated_at=datetime.fromisoformat(data["initiated_at"]),
            expected_duration_minutes=data.get("expected_duration_minutes"),
            triggering_event=data.get("triggering_event"),
            agent_notes=data.get("agent_notes", ""),
        )


@dataclass
class ContextHandoff:
    """
    Result of intelligence context handoff operation.

    Tracks the success/failure of intelligence preservation
    and provides metadata for monitoring and debugging.
    """

    # Operation result
    success: bool
    handoff_status: HandoffStatus
    error_message: Optional[str] = None

    # Handoff metadata
    lead_id: str = ""
    location_id: str = ""
    intelligence_snapshot_id: str = ""
    transition_id: str = ""

    # Performance metrics
    preservation_latency_ms: float = 0.0
    retrieval_latency_ms: float = 0.0
    data_size_bytes: int = 0

    # Cache metadata
    cache_key: str = ""
    cache_ttl_seconds: int = 7200  # 2 hours default
    cache_hit: bool = False

    # Timestamps
    handoff_initiated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    handoff_completed_at: Optional[datetime] = None
    context_expires_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for event publishing."""
        return {
            "success": self.success,
            "handoff_status": self.handoff_status.value,
            "error_message": self.error_message,
            "lead_id": self.lead_id,
            "location_id": self.location_id,
            "intelligence_snapshot_id": self.intelligence_snapshot_id,
            "transition_id": self.transition_id,
            "preservation_latency_ms": self.preservation_latency_ms,
            "retrieval_latency_ms": self.retrieval_latency_ms,
            "data_size_bytes": self.data_size_bytes,
            "cache_key": self.cache_key,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "cache_hit": self.cache_hit,
            "handoff_initiated_at": self.handoff_initiated_at.isoformat(),
            "handoff_completed_at": self.handoff_completed_at.isoformat() if self.handoff_completed_at else None,
            "context_expires_at": self.context_expires_at.isoformat() if self.context_expires_at else None,
        }

    @classmethod
    def create_success(
        cls,
        lead_id: str,
        location_id: str,
        intelligence_snapshot_id: str,
        transition_id: str,
        preservation_latency_ms: float,
        cache_key: str,
        cache_ttl_seconds: int = 7200,
    ) -> "ContextHandoff":
        """Create successful handoff result."""
        return cls(
            success=True,
            handoff_status=HandoffStatus.SUCCESS,
            lead_id=lead_id,
            location_id=location_id,
            intelligence_snapshot_id=intelligence_snapshot_id,
            transition_id=transition_id,
            preservation_latency_ms=preservation_latency_ms,
            cache_key=cache_key,
            cache_ttl_seconds=cache_ttl_seconds,
            handoff_completed_at=datetime.now(timezone.utc),
            context_expires_at=datetime.now(timezone.utc).replace(second=0, microsecond=0)
            + timedelta(seconds=cache_ttl_seconds),
        )

    @classmethod
    def create_failure(
        cls, lead_id: str, location_id: str, error_message: str, preservation_latency_ms: float = 0.0
    ) -> "ContextHandoff":
        """Create failed handoff result."""
        return cls(
            success=False,
            handoff_status=HandoffStatus.FAILED,
            error_message=error_message,
            lead_id=lead_id,
            location_id=location_id,
            preservation_latency_ms=preservation_latency_ms,
            handoff_completed_at=datetime.now(timezone.utc),
        )


@dataclass
class TransitionHistory:
    """
    Complete transition history for a lead.

    Maintains audit trail of all bot transitions for
    analytics, debugging, and compliance.
    """

    lead_id: str
    location_id: str
    transitions: List[BotTransition] = field(default_factory=list)
    handoffs: List[ContextHandoff] = field(default_factory=list)

    # Aggregate metrics
    total_transitions: int = 0
    successful_handoffs: int = 0
    failed_handoffs: int = 0
    average_handoff_latency_ms: float = 0.0

    # Timeline
    first_transition_at: Optional[datetime] = None
    last_transition_at: Optional[datetime] = None
    last_updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_transition(self, transition: BotTransition, handoff: ContextHandoff) -> None:
        """Add new transition to history."""
        self.transitions.append(transition)
        self.handoffs.append(handoff)

        # Update metrics
        self.total_transitions += 1
        if handoff.success:
            self.successful_handoffs += 1
        else:
            self.failed_handoffs += 1

        # Update latency average
        if handoff.preservation_latency_ms > 0:
            total_latency = self.average_handoff_latency_ms * (len(self.handoffs) - 1) + handoff.preservation_latency_ms
            self.average_handoff_latency_ms = total_latency / len(self.handoffs)

        # Update timeline
        if not self.first_transition_at:
            self.first_transition_at = transition.initiated_at
        self.last_transition_at = transition.initiated_at
        self.last_updated_at = datetime.now(timezone.utc)

    def get_recent_transitions(self, hours: int = 24) -> List[BotTransition]:
        """Get transitions within the last N hours."""
        cutoff = datetime.now(timezone.utc) - datetime.timedelta(hours=hours)
        return [t for t in self.transitions if t.initiated_at >= cutoff]

    def get_success_rate(self) -> float:
        """Calculate handoff success rate."""
        if self.total_transitions == 0:
            return 1.0
        return self.successful_handoffs / self.total_transitions

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for caching."""
        return {
            "lead_id": self.lead_id,
            "location_id": self.location_id,
            "transitions": [t.to_dict() for t in self.transitions],
            "handoffs": [h.to_dict() for h in self.handoffs],
            "total_transitions": self.total_transitions,
            "successful_handoffs": self.successful_handoffs,
            "failed_handoffs": self.failed_handoffs,
            "average_handoff_latency_ms": self.average_handoff_latency_ms,
            "first_transition_at": self.first_transition_at.isoformat() if self.first_transition_at else None,
            "last_transition_at": self.last_transition_at.isoformat() if self.last_transition_at else None,
            "last_updated_at": self.last_updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TransitionHistory":
        """Create from cached dictionary."""
        history = cls(
            lead_id=data["lead_id"],
            location_id=data["location_id"],
            total_transitions=data.get("total_transitions", 0),
            successful_handoffs=data.get("successful_handoffs", 0),
            failed_handoffs=data.get("failed_handoffs", 0),
            average_handoff_latency_ms=data.get("average_handoff_latency_ms", 0.0),
            first_transition_at=datetime.fromisoformat(data["first_transition_at"])
            if data.get("first_transition_at")
            else None,
            last_transition_at=datetime.fromisoformat(data["last_transition_at"])
            if data.get("last_transition_at")
            else None,
            last_updated_at=datetime.fromisoformat(data["last_updated_at"]),
        )

        # Reconstruct transitions and handoffs
        history.transitions = [BotTransition.from_dict(t) for t in data.get("transitions", [])]
        history.handoffs = [
            ContextHandoff(
                success=h["success"],
                handoff_status=HandoffStatus(h["handoff_status"]),
                error_message=h.get("error_message"),
                **{k: v for k, v in h.items() if k not in ["success", "handoff_status", "error_message"]},
            )
            for h in data.get("handoffs", [])
        ]

        return history

    @classmethod
    def create_empty(cls, lead_id: str, location_id: str) -> "TransitionHistory":
        """Create empty history for new lead."""
        return cls(lead_id=lead_id, location_id=location_id)
