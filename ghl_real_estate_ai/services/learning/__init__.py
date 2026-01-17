"""
Behavioral Learning Engine

Enterprise-grade behavioral learning and personalization system for
GHL Real Estate AI platform.

Provides:
- Behavioral event tracking and analysis
- Feature engineering for machine learning
- Multiple ML strategies (collaborative filtering, content-based, etc.)
- Real-time personalization and recommendations
- Online learning with feedback loops
- A/B testing and model experimentation
"""

# Core interfaces and data structures
from .interfaces import (
    # Enums
    EventType,
    FeatureType,
    ModelType,
    LearningMode,
    ConfidenceLevel,

    # Data structures
    BehavioralEvent,
    FeatureVector,
    LearningContext,
    ModelPrediction,
    TrainingResult,

    # Core interfaces
    IBehaviorTracker,
    IFeatureEngineer,
    ILearningModel,
    IPersonalizationEngine,
    ILearningService,

    # Exceptions
    LearningError,
    ModelNotTrainedError,
    FeatureExtractionError,
    PredictionError,
    TrainingError,

    # Type aliases
    EventFilter,
    FeatureDict,
    PredictionBatch
)

# Version information
__version__ = "1.0.0"
__author__ = "GHL Real Estate AI Team"
__description__ = "Behavioral Learning Engine for intelligent personalization"

# Main exports for external usage
__all__ = [
    # Core enums
    "EventType",
    "FeatureType",
    "ModelType",
    "LearningMode",
    "ConfidenceLevel",

    # Data structures
    "BehavioralEvent",
    "FeatureVector",
    "LearningContext",
    "ModelPrediction",
    "TrainingResult",

    # Interfaces
    "IBehaviorTracker",
    "IFeatureEngineer",
    "ILearningModel",
    "IPersonalizationEngine",
    "ILearningService",

    # Exceptions
    "LearningError",
    "ModelNotTrainedError",
    "FeatureExtractionError",
    "PredictionError",
    "TrainingError",

    # Type aliases
    "EventFilter",
    "FeatureDict",
    "PredictionBatch"
]


def get_version_info():
    """Get version information for the learning engine"""
    return {
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "interfaces_count": len(__all__),
        "supported_event_types": len(EventType),
        "supported_model_types": len(ModelType)
    }


def create_behavioral_event(
    event_type: EventType,
    lead_id: str = None,
    agent_id: str = None,
    property_id: str = None,
    event_data: dict = None
) -> BehavioralEvent:
    """
    Convenience function to create behavioral events.

    Args:
        event_type: Type of event
        lead_id: Optional lead identifier
        agent_id: Optional agent identifier
        property_id: Optional property identifier
        event_data: Optional event-specific data

    Returns:
        Configured BehavioralEvent
    """
    import uuid
    from datetime import datetime

    return BehavioralEvent(
        event_id=f"evt_{uuid.uuid4().hex[:12]}",
        event_type=event_type,
        timestamp=datetime.now(),
        lead_id=lead_id,
        agent_id=agent_id,
        property_id=property_id,
        event_data=event_data or {}
    )


def create_learning_context(
    session_id: str = None,
    max_results: int = 10,
    min_confidence: float = 0.5,
    debug_mode: bool = False
) -> LearningContext:
    """
    Convenience function to create learning context.

    Args:
        session_id: Optional session identifier
        max_results: Maximum number of results to return
        min_confidence: Minimum confidence threshold
        debug_mode: Enable debug mode

    Returns:
        Configured LearningContext
    """
    return LearningContext(
        session_id=session_id,
        max_results=max_results,
        min_confidence=min_confidence,
        debug_mode=debug_mode,
        tracking_enabled=True
    )


# Quick start examples
EXAMPLE_EVENTS = {
    "property_view": lambda lead_id, property_id: create_behavioral_event(
        EventType.PROPERTY_VIEW,
        lead_id=lead_id,
        property_id=property_id,
        event_data={"view_duration_seconds": 30.5}
    ),

    "property_like": lambda lead_id, property_id: create_behavioral_event(
        EventType.PROPERTY_SWIPE,
        lead_id=lead_id,
        property_id=property_id,
        event_data={"swipe_direction": "right", "liked": True}
    ),

    "booking_request": lambda lead_id, agent_id, property_id: create_behavioral_event(
        EventType.BOOKING_REQUEST,
        lead_id=lead_id,
        agent_id=agent_id,
        property_id=property_id,
        event_data={"booking_type": "tour", "urgency": "high"}
    )
}


def get_quick_start_examples():
    """Get example usage patterns for quick start"""
    return {
        "track_property_view": """
# Track when a lead views a property
from ghl_real_estate_ai.services.learning import create_behavioral_event, EventType

event = create_behavioral_event(
    EventType.PROPERTY_VIEW,
    lead_id="lead_123",
    property_id="prop_456",
    event_data={"view_duration_seconds": 45.2}
)
""",

        "create_feature_vector": """
# Create feature vector for machine learning
from ghl_real_estate_ai.services.learning import FeatureVector

features = FeatureVector(
    entity_id="lead_123",
    entity_type="lead",
    numerical_features={
        "total_views": 25.0,
        "avg_view_time": 32.5,
        "like_rate": 0.75
    }
)
""",

        "setup_learning_context": """
# Setup context for personalized recommendations
from ghl_real_estate_ai.services.learning import create_learning_context

context = create_learning_context(
    session_id="session_abc",
    max_results=5,
    min_confidence=0.7,
    debug_mode=True
)
"""
    }


if __name__ == "__main__":
    # Quick demonstration
    print("🧠 GHL Real Estate AI - Behavioral Learning Engine")
    print(f"Version: {__version__}")
    print(f"Supported Event Types: {len(EventType)}")
    print(f"Supported Model Types: {len(ModelType)}")

    # Show example event creation
    example_event = EXAMPLE_EVENTS["property_view"]("lead_123", "prop_456")
    print(f"\nExample Event: {example_event.event_type.value}")
    print(f"Event ID: {example_event.event_id}")
    print(f"Timestamp: {example_event.timestamp}")