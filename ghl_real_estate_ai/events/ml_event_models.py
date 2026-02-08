"""
ML Event Models - Jorge AI Lead Scoring System Integration
Extends the existing ComplianceEvent system for ML-specific events

Integrates with existing Jorge architectural patterns:
- Redis pub/sub event publishing
- Pydantic models for type safety
- JSON serialization for event transport
- Channel-based routing for scalability
"""

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field

from ghl_real_estate_ai.compliance_platform.realtime.event_publisher import ComplianceEvent, ComplianceEventType
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class MLEventType(str, Enum):
    """ML-specific event types for Jorge lead scoring system"""

    # ML Lead Scoring Events
    LEAD_ML_SCORED = "ml.lead.scored"
    LEAD_ML_ESCALATED = "ml.lead.escalated"
    LEAD_ML_CACHE_HIT = "ml.lead.cache_hit"

    # ML Model Events
    ML_MODEL_TRAINED = "ml.model.trained"
    ML_MODEL_DEPLOYED = "ml.model.deployed"
    ML_PREDICTION_COMPLETED = "ml.prediction.completed"

    # ML Performance Events
    ML_CONFIDENCE_LOW = "ml.confidence.low"
    ML_ACCURACY_DEGRADED = "ml.accuracy.degraded"
    ML_DRIFT_DETECTED = "ml.drift.detected"


class LeadMLScoredEvent(BaseModel):
    """Event fired when a lead receives ML scoring"""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: MLEventType = MLEventType.LEAD_ML_SCORED
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "jorge_ml_system"

    # Lead identification
    lead_id: str
    lead_name: str

    # ML Scoring results
    ml_score: float = Field(..., ge=0.0, le=100.0, description="ML confidence score 0-100")
    ml_confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence 0-1")
    ml_classification: str = Field(..., description="hot, warm, cold")

    # Feature importance (top 5 features that drove the score)
    feature_importance: Dict[str, float] = Field(default_factory=dict)

    # ML model metadata
    model_version: str = "v1.0"
    model_name: str = "lead_scoring_rf"

    # Performance metrics
    prediction_time_ms: float = 0.0

    # Context for handoff to Claude if needed
    escalation_reason: Optional[str] = None
    claude_handoff: bool = False

    def to_compliance_event(self) -> ComplianceEvent:
        """Convert to ComplianceEvent for existing pub/sub system"""
        return ComplianceEvent(
            event_id=self.event_id,
            event_type=ComplianceEventType.SCORE_CHANGED,  # Map to existing type
            timestamp=self.timestamp,
            source=self.source,
            model_id=self.model_name,
            model_name=self.model_name,
            payload={
                "lead_id": self.lead_id,
                "lead_name": self.lead_name,
                "ml_score": self.ml_score,
                "ml_confidence": self.ml_confidence,
                "ml_classification": self.ml_classification,
                "feature_importance": self.feature_importance,
                "prediction_time_ms": self.prediction_time_ms,
                "claude_handoff": self.claude_handoff,
                "escalation_reason": self.escalation_reason,
            },
            metadata={
                "event_subtype": "ml_lead_scored",
                "model_version": self.model_version,
                "performance_tier": "ml_fast_tier",
            },
        )


class LeadMLEscalatedEvent(BaseModel):
    """Event fired when ML confidence is low and lead escalates to Claude"""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: MLEventType = MLEventType.LEAD_ML_ESCALATED
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "jorge_ml_system"

    # Lead identification
    lead_id: str
    lead_name: str

    # ML Results that triggered escalation
    ml_score: float
    ml_confidence: float
    escalation_threshold: float = 0.85
    escalation_reason: str

    # Context for Claude analysis
    lead_context: Dict[str, Any] = Field(default_factory=dict)
    ml_feature_analysis: Dict[str, Any] = Field(default_factory=dict)

    # Performance tracking
    ml_processing_time_ms: float = 0.0

    def to_compliance_event(self) -> ComplianceEvent:
        """Convert to ComplianceEvent for existing pub/sub system"""
        return ComplianceEvent(
            event_id=self.event_id,
            event_type=ComplianceEventType.REMEDIATION_STARTED,  # Escalation is like starting remediation
            timestamp=self.timestamp,
            source=self.source,
            model_id="claude_escalation",
            model_name="claude_lead_analyzer",
            payload={
                "lead_id": self.lead_id,
                "lead_name": self.lead_name,
                "ml_score": self.ml_score,
                "ml_confidence": self.ml_confidence,
                "escalation_threshold": self.escalation_threshold,
                "escalation_reason": self.escalation_reason,
                "lead_context": self.lead_context,
                "ml_feature_analysis": self.ml_feature_analysis,
            },
            metadata={
                "event_subtype": "ml_escalated_to_claude",
                "performance_tier": "claude_deep_analysis",
                "processing_time_ms": self.ml_processing_time_ms,
            },
        )


class LeadMLCacheHitEvent(BaseModel):
    """Event fired when ML prediction comes from cache (performance optimization)"""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: MLEventType = MLEventType.LEAD_ML_CACHE_HIT
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "jorge_cache_system"

    # Lead identification
    lead_id: str
    lead_name: str

    # Cache metadata
    cache_key: str
    cache_age_seconds: float
    cache_ttl_remaining: float

    # Cached ML results
    cached_ml_score: float
    cached_ml_confidence: float
    cached_classification: str

    # Performance benefits
    cache_hit_time_ms: float = 0.0
    estimated_compute_savings_ms: float = 0.0

    def to_compliance_event(self) -> ComplianceEvent:
        """Convert to ComplianceEvent for existing pub/sub system"""
        return ComplianceEvent(
            event_id=self.event_id,
            event_type=ComplianceEventType.ASSESSMENT_COMPLETED,  # Cache hit is completed assessment
            timestamp=self.timestamp,
            source=self.source,
            model_id="cache_service",
            model_name="lead_ml_cache",
            payload={
                "lead_id": self.lead_id,
                "lead_name": self.lead_name,
                "cache_key": self.cache_key,
                "cache_age_seconds": self.cache_age_seconds,
                "cached_ml_score": self.cached_ml_score,
                "cached_ml_confidence": self.cached_ml_confidence,
                "cached_classification": self.cached_classification,
            },
            metadata={
                "event_subtype": "ml_cache_hit",
                "performance_tier": "cache_optimization",
                "cache_hit_time_ms": self.cache_hit_time_ms,
                "compute_savings_ms": self.estimated_compute_savings_ms,
            },
        )


# Extended EventType Union for backward compatibility
ExtendedEventType = Union[ComplianceEventType, MLEventType]


def create_ml_event(
    event_type: str, lead_id: str, lead_name: str, **kwargs
) -> Union[LeadMLScoredEvent, LeadMLEscalatedEvent, LeadMLCacheHitEvent]:
    """
    Factory function to create ML events - follows Jorge architectural patterns

    Args:
        event_type: Type of ML event to create
        lead_id: Lead identifier
        lead_name: Lead name
        **kwargs: Additional event-specific parameters

    Returns:
        Appropriate ML event instance

    Raises:
        ValueError: If event_type is not recognized
    """

    if event_type == "lead_ml_scored":
        return LeadMLScoredEvent(
            lead_id=lead_id,
            lead_name=lead_name,
            ml_score=kwargs.get("ml_score", 50.0),
            ml_confidence=kwargs.get("ml_confidence", 0.5),
            ml_classification=kwargs.get("ml_classification", "warm"),
            feature_importance=kwargs.get("feature_importance", {}),
            model_version=kwargs.get("model_version", "v1.0"),
            model_name=kwargs.get("model_name", "lead_scoring_rf"),
            prediction_time_ms=kwargs.get("prediction_time_ms", 0.0),
            escalation_reason=kwargs.get("escalation_reason"),
            claude_handoff=kwargs.get("claude_handoff", False),
        )

    elif event_type == "lead_ml_escalated":
        return LeadMLEscalatedEvent(
            lead_id=lead_id,
            lead_name=lead_name,
            ml_score=kwargs.get("ml_score", 50.0),
            ml_confidence=kwargs.get("ml_confidence", 0.5),
            escalation_threshold=kwargs.get("escalation_threshold", 0.85),
            escalation_reason=kwargs.get("escalation_reason", "Low ML confidence"),
            lead_context=kwargs.get("lead_context", {}),
            ml_feature_analysis=kwargs.get("ml_feature_analysis", {}),
            ml_processing_time_ms=kwargs.get("ml_processing_time_ms", 0.0),
        )

    elif event_type == "lead_ml_cache_hit":
        return LeadMLCacheHitEvent(
            lead_id=lead_id,
            lead_name=lead_name,
            cache_key=kwargs.get("cache_key", f"ml_lead_{lead_id}"),
            cache_age_seconds=kwargs.get("cache_age_seconds", 0.0),
            cache_ttl_remaining=kwargs.get("cache_ttl_remaining", 300.0),
            cached_ml_score=kwargs.get("cached_ml_score", 50.0),
            cached_ml_confidence=kwargs.get("cached_ml_confidence", 0.5),
            cached_classification=kwargs.get("cached_classification", "warm"),
            cache_hit_time_ms=kwargs.get("cache_hit_time_ms", 0.0),
            estimated_compute_savings_ms=kwargs.get("estimated_compute_savings_ms", 150.0),
        )

    else:
        raise ValueError(f"Unknown ML event type: {event_type}")


class MLEventPublisher:
    """
    ML Event Publisher - Extends Jorge's existing event publishing system

    Publishes ML events to Redis pub/sub channels using the existing infrastructure
    while maintaining backward compatibility with ComplianceEvent system
    """

    def __init__(self, compliance_publisher=None):
        """
        Initialize ML event publisher with optional ComplianceEventPublisher

        Args:
            compliance_publisher: Optional existing ComplianceEventPublisher instance
        """
        self.compliance_publisher = compliance_publisher
        if not self.compliance_publisher:
            # Import here to avoid circular dependency
            from ghl_real_estate_ai.compliance_platform.realtime.event_publisher import ComplianceEventPublisher

            self.compliance_publisher = ComplianceEventPublisher(channel_prefix="jorge_ml")

    async def publish_ml_scored(
        self,
        lead_id: str,
        lead_name: str,
        ml_score: float,
        ml_confidence: float,
        ml_classification: str,
        feature_importance: Dict[str, float] = None,
        prediction_time_ms: float = 0.0,
    ) -> int:
        """Publish LeadMLScoredEvent"""

        event = LeadMLScoredEvent(
            lead_id=lead_id,
            lead_name=lead_name,
            ml_score=ml_score,
            ml_confidence=ml_confidence,
            ml_classification=ml_classification,
            feature_importance=feature_importance or {},
            prediction_time_ms=prediction_time_ms,
            claude_handoff=ml_confidence < 0.85,
        )

        # Convert to ComplianceEvent and publish
        compliance_event = event.to_compliance_event()
        return await self.compliance_publisher.publish(compliance_event)

    async def publish_ml_escalated(
        self,
        lead_id: str,
        lead_name: str,
        ml_score: float,
        ml_confidence: float,
        escalation_reason: str,
        lead_context: Dict[str, Any],
        ml_processing_time_ms: float = 0.0,
    ) -> int:
        """Publish LeadMLEscalatedEvent"""

        event = LeadMLEscalatedEvent(
            lead_id=lead_id,
            lead_name=lead_name,
            ml_score=ml_score,
            ml_confidence=ml_confidence,
            escalation_reason=escalation_reason,
            lead_context=lead_context,
            ml_processing_time_ms=ml_processing_time_ms,
        )

        # Convert to ComplianceEvent and publish
        compliance_event = event.to_compliance_event()
        return await self.compliance_publisher.publish(compliance_event)

    async def publish_ml_cache_hit(
        self,
        lead_id: str,
        lead_name: str,
        cache_key: str,
        cache_age_seconds: float,
        cached_ml_score: float,
        cached_ml_confidence: float,
        cached_classification: str,
        cache_hit_time_ms: float = 0.0,
    ) -> int:
        """Publish LeadMLCacheHitEvent"""

        event = LeadMLCacheHitEvent(
            lead_id=lead_id,
            lead_name=lead_name,
            cache_key=cache_key,
            cache_age_seconds=cache_age_seconds,
            cached_ml_score=cached_ml_score,
            cached_ml_confidence=cached_ml_confidence,
            cached_classification=cached_classification,
            cache_hit_time_ms=cache_hit_time_ms,
            estimated_compute_savings_ms=150.0,  # Estimated ML compute time saved
        )

        # Convert to ComplianceEvent and publish
        compliance_event = event.to_compliance_event()
        return await self.compliance_publisher.publish(compliance_event)

    async def connect(self) -> bool:
        """Connect the underlying publisher"""
        return await self.compliance_publisher.connect()

    async def disconnect(self) -> None:
        """Disconnect the underlying publisher"""
        await self.compliance_publisher.disconnect()
