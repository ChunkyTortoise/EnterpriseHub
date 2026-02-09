"""
Behavioral Learning Engine Interfaces

Enterprise-grade interfaces for AI-powered behavioral learning and personalization.
Supports multiple ML strategies, online learning, and real-time personalization.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class EventType(Enum):
    """Types of behavioral events tracked by the system"""

    PROPERTY_VIEW = "property_view"
    PROPERTY_SWIPE = "property_swipe"
    PROPERTY_LIKE = "property_like"
    PROPERTY_DISLIKE = "property_dislike"
    PROPERTY_SHARE = "property_share"
    PROPERTY_SAVE = "property_save"
    BOOKING_REQUEST = "booking_request"
    BOOKING_COMPLETED = "booking_completed"
    BOOKING_CANCELLED = "booking_cancelled"
    AGENT_INTERACTION = "agent_interaction"
    AGENT_ACTION = "agent_action"
    LEAD_INTERACTION = "lead_interaction"
    SEARCH_QUERY = "search_query"
    FILTER_APPLIED = "filter_applied"
    TOUR_SCHEDULED = "tour_scheduled"
    TOUR_COMPLETED = "tour_completed"
    FORM_SUBMISSION = "form_submission"
    EMAIL_OPENED = "email_opened"
    EMAIL_CLICKED = "email_clicked"
    PAGE_VIEW = "page_view"
    SESSION_START = "session_start"
    SESSION_END = "session_end"


class FeatureType(Enum):
    """Types of features extracted for machine learning"""

    NUMERICAL = "numerical"
    CATEGORICAL = "categorical"
    TEMPORAL = "temporal"
    EMBEDDING = "embedding"
    SEQUENCE = "sequence"
    BINARY = "binary"
    TEXT = "text"


class ModelType(Enum):
    """Types of machine learning models"""

    COLLABORATIVE_FILTERING = "collaborative_filtering"
    CONTENT_BASED = "content_based"
    MATRIX_FACTORIZATION = "matrix_factorization"
    MULTI_ARMED_BANDIT = "multi_armed_bandit"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    NEURAL_NETWORK = "neural_network"
    ENSEMBLE = "ensemble"
    LINEAR_REGRESSION = "linear_regression"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"


class LearningMode(Enum):
    """Learning modes for model training"""

    BATCH = "batch"
    ONLINE = "online"
    MINI_BATCH = "mini_batch"
    TRANSFER = "transfer"


class ConfidenceLevel(Enum):
    """Confidence levels for predictions"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


@dataclass
class BehavioralEvent:
    """
    Individual behavioral event tracked by the system.

    Core unit of data for the learning engine. Contains all necessary
    information for feature extraction and model training.
    """

    event_id: str
    event_type: EventType
    timestamp: datetime

    # Entity identifiers
    lead_id: Optional[str] = None
    agent_id: Optional[str] = None
    property_id: Optional[str] = None
    session_id: Optional[str] = None

    # Event context
    device_type: Optional[str] = None
    source_channel: Optional[str] = None
    campaign_id: Optional[str] = None

    # Event-specific data
    event_data: Dict[str, Any] = field(default_factory=dict)

    # Outcome tracking (for supervised learning)
    outcome: Optional[str] = None
    outcome_value: Optional[float] = None
    outcome_timestamp: Optional[datetime] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "lead_id": self.lead_id,
            "agent_id": self.agent_id,
            "property_id": self.property_id,
            "session_id": self.session_id,
            "device_type": self.device_type,
            "source_channel": self.source_channel,
            "campaign_id": self.campaign_id,
            "event_data": self.event_data,
            "outcome": self.outcome,
            "outcome_value": self.outcome_value,
            "outcome_timestamp": self.outcome_timestamp.isoformat() if self.outcome_timestamp else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BehavioralEvent":
        """Create from dictionary"""
        return cls(
            event_id=data["event_id"],
            event_type=EventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            lead_id=data.get("lead_id"),
            agent_id=data.get("agent_id"),
            property_id=data.get("property_id"),
            session_id=data.get("session_id"),
            device_type=data.get("device_type"),
            source_channel=data.get("source_channel"),
            campaign_id=data.get("campaign_id"),
            event_data=data.get("event_data", {}),
            outcome=data.get("outcome"),
            outcome_value=data.get("outcome_value"),
            outcome_timestamp=datetime.fromisoformat(data["outcome_timestamp"])
            if data.get("outcome_timestamp")
            else None,
            metadata=data.get("metadata", {}),
        )


@dataclass
class FeatureVector:
    """
    Feature vector representing an entity for machine learning.

    Contains all extracted features for a specific entity (lead, agent, property)
    along with metadata for tracking and debugging.
    """

    entity_id: str
    entity_type: str
    extraction_timestamp: datetime = field(default_factory=datetime.now)

    # Feature categories
    numerical_features: Dict[str, float] = field(default_factory=dict)
    categorical_features: Dict[str, str] = field(default_factory=dict)
    temporal_features: Dict[str, datetime] = field(default_factory=dict)
    embedding_features: Dict[str, List[float]] = field(default_factory=dict)
    sequence_features: Dict[str, List[Any]] = field(default_factory=dict)
    binary_features: Dict[str, bool] = field(default_factory=dict)
    text_features: Dict[str, str] = field(default_factory=dict)

    # Metadata
    feature_names: List[str] = field(default_factory=list)
    feature_version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_all_features(self) -> Dict[str, Any]:
        """Get all features as a flat dictionary"""
        all_features = {}
        all_features.update(self.numerical_features)
        all_features.update(self.categorical_features)
        all_features.update({k: v.isoformat() for k, v in self.temporal_features.items()})
        all_features.update(self.embedding_features)
        all_features.update({k: str(v) for k, v in self.binary_features.items()})
        all_features.update(self.text_features)
        return all_features

    def to_numpy_array(self) -> List[float]:
        """Convert numerical features to numpy-compatible array"""
        return [self.numerical_features.get(name, 0.0) for name in self.feature_names]


@dataclass
class LearningContext:
    """
    Context for machine learning operations.

    Provides additional information about the learning context,
    including A/B testing, performance requirements, and business rules.
    """

    session_id: Optional[str] = None
    user_id: Optional[str] = None
    experiment_id: Optional[str] = None
    model_version: Optional[str] = None

    # Performance requirements
    max_latency_ms: int = 100
    min_confidence: float = 0.5
    max_results: int = 10

    # Business context
    business_rules: Dict[str, Any] = field(default_factory=dict)
    feature_flags: Dict[str, bool] = field(default_factory=dict)

    # Tracking
    tracking_enabled: bool = True
    debug_mode: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "experiment_id": self.experiment_id,
            "model_version": self.model_version,
            "max_latency_ms": self.max_latency_ms,
            "min_confidence": self.min_confidence,
            "max_results": self.max_results,
            "business_rules": self.business_rules,
            "feature_flags": self.feature_flags,
            "tracking_enabled": self.tracking_enabled,
            "debug_mode": self.debug_mode,
        }


@dataclass
class ModelPrediction:
    """
    Prediction result from a machine learning model.

    Contains the prediction, confidence, and explainability information
    for transparency and debugging.
    """

    entity_id: str
    predicted_value: float
    confidence: float
    confidence_level: ConfidenceLevel

    # Model information
    model_id: str
    model_version: str
    prediction_timestamp: datetime = field(default_factory=datetime.now)

    # Explainability
    feature_importance: Dict[str, float] = field(default_factory=dict)
    reasoning: List[str] = field(default_factory=list)

    # Metadata
    processing_time_ms: Optional[float] = None
    model_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "entity_id": self.entity_id,
            "predicted_value": self.predicted_value,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level.value,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "prediction_timestamp": self.prediction_timestamp.isoformat(),
            "feature_importance": self.feature_importance,
            "reasoning": self.reasoning,
            "processing_time_ms": self.processing_time_ms,
            "model_metadata": self.model_metadata,
        }


@dataclass
class TrainingResult:
    """
    Result of model training operation.

    Contains metrics, model information, and training metadata
    for monitoring and evaluation.
    """

    model_id: str
    training_id: str
    training_timestamp: datetime

    # Training metrics
    training_loss: Optional[float] = None
    validation_loss: Optional[float] = None
    test_metrics: Dict[str, float] = field(default_factory=dict)

    # Model information
    model_version: str = "1.0"
    training_mode: LearningMode = LearningMode.BATCH
    training_duration_seconds: Optional[float] = None

    # Data information
    training_samples: int = 0
    validation_samples: int = 0
    test_samples: int = 0

    # Configuration
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    feature_names: List[str] = field(default_factory=list)

    # Results
    model_path: Optional[str] = None
    success: bool = False
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "model_id": self.model_id,
            "training_id": self.training_id,
            "training_timestamp": self.training_timestamp.isoformat(),
            "training_loss": self.training_loss,
            "validation_loss": self.validation_loss,
            "test_metrics": self.test_metrics,
            "model_version": self.model_version,
            "training_mode": self.training_mode.value,
            "training_duration_seconds": self.training_duration_seconds,
            "training_samples": self.training_samples,
            "validation_samples": self.validation_samples,
            "test_samples": self.test_samples,
            "hyperparameters": self.hyperparameters,
            "feature_names": self.feature_names,
            "model_path": self.model_path,
            "success": self.success,
            "error_message": self.error_message,
        }


# Core Interfaces
class IBehaviorTracker(ABC):
    """
    Interface for behavioral event tracking systems.

    Handles collection, storage, and retrieval of behavioral events
    for the learning engine.
    """

    @abstractmethod
    async def track_event(self, event: BehavioralEvent) -> bool:
        """
        Track a single behavioral event.

        Args:
            event: The behavioral event to track

        Returns:
            True if event was successfully tracked
        """
        pass

    @abstractmethod
    async def track_events_batch(self, events: List[BehavioralEvent]) -> int:
        """
        Track multiple events in batch for efficiency.

        Args:
            events: List of events to track

        Returns:
            Number of events successfully tracked
        """
        pass

    @abstractmethod
    async def get_events(
        self,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        event_types: Optional[List[EventType]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[BehavioralEvent]:
        """
        Retrieve events matching criteria.

        Args:
            entity_id: Filter by entity ID (lead_id, agent_id, property_id)
            entity_type: Filter by entity type
            event_types: Filter by event types
            start_time: Filter events after this time
            end_time: Filter events before this time
            limit: Maximum number of events to return

        Returns:
            List of matching behavioral events
        """
        pass

    @abstractmethod
    async def get_event_count(
        self, entity_id: Optional[str] = None, event_types: Optional[List[EventType]] = None
    ) -> int:
        """
        Count events matching criteria.

        Args:
            entity_id: Filter by entity ID
            event_types: Filter by event types

        Returns:
            Number of matching events
        """
        pass

    @abstractmethod
    async def record_outcome(self, event_id: str, outcome: str, outcome_value: Optional[float] = None) -> bool:
        """
        Record outcome for an event (for supervised learning).

        Args:
            event_id: ID of the original event
            outcome: Outcome description
            outcome_value: Numerical outcome value

        Returns:
            True if outcome was successfully recorded
        """
        pass


class IFeatureEngineer(ABC):
    """
    Interface for feature engineering systems.

    Transforms raw behavioral events into feature vectors
    suitable for machine learning.
    """

    @abstractmethod
    async def extract_features(
        self, entity_id: str, entity_type: str, events: List[BehavioralEvent], context: Optional[LearningContext] = None
    ) -> FeatureVector:
        """
        Extract features for a single entity.

        Args:
            entity_id: ID of entity to extract features for
            entity_type: Type of entity (lead, agent, property)
            events: List of behavioral events for this entity
            context: Additional context for feature extraction

        Returns:
            Feature vector for the entity
        """
        pass

    @abstractmethod
    async def batch_extract_features(
        self,
        entities: List[Tuple[str, str]],
        events_by_entity: Dict[str, List[BehavioralEvent]],
        context: Optional[LearningContext] = None,
    ) -> Dict[str, FeatureVector]:
        """
        Extract features for multiple entities efficiently.

        Args:
            entities: List of (entity_id, entity_type) tuples
            events_by_entity: Events grouped by entity_id
            context: Additional context for feature extraction

        Returns:
            Dictionary mapping entity_id to feature vector
        """
        pass

    @abstractmethod
    def get_feature_names(self) -> List[str]:
        """
        Get list of feature names that will be extracted.

        Returns:
            List of feature names
        """
        pass

    @abstractmethod
    def get_feature_types(self) -> Dict[str, FeatureType]:
        """
        Get mapping of feature names to their types.

        Returns:
            Dictionary mapping feature names to types
        """
        pass


class ILearningModel(ABC):
    """
    Interface for machine learning models.

    Supports both batch and online learning modes with
    consistent prediction interface.
    """

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Unique identifier for this model"""
        pass

    @property
    @abstractmethod
    def model_type(self) -> ModelType:
        """Type of machine learning model"""
        pass

    @property
    @abstractmethod
    def is_trained(self) -> bool:
        """Whether model has been trained and is ready for predictions"""
        pass

    @abstractmethod
    async def train(
        self,
        features: List[FeatureVector],
        targets: List[float],
        validation_features: Optional[List[FeatureVector]] = None,
        validation_targets: Optional[List[float]] = None,
        context: Optional[LearningContext] = None,
    ) -> TrainingResult:
        """
        Train the model on feature vectors and targets.

        Args:
            features: Training feature vectors
            targets: Training targets
            validation_features: Optional validation feature vectors
            validation_targets: Optional validation targets
            context: Training context

        Returns:
            Training result with metrics and model information
        """
        pass

    @abstractmethod
    async def predict(self, features: FeatureVector, context: Optional[LearningContext] = None) -> ModelPrediction:
        """
        Make prediction for a single entity.

        Args:
            features: Feature vector for entity
            context: Prediction context

        Returns:
            Model prediction with confidence and reasoning
        """
        pass

    @abstractmethod
    async def predict_batch(
        self, features: List[FeatureVector], context: Optional[LearningContext] = None
    ) -> List[ModelPrediction]:
        """
        Make predictions for multiple entities efficiently.

        Args:
            features: List of feature vectors
            context: Prediction context

        Returns:
            List of model predictions
        """
        pass

    @abstractmethod
    async def update_online(
        self, features: FeatureVector, target: float, context: Optional[LearningContext] = None
    ) -> bool:
        """
        Update model with new training example (online learning).

        Args:
            features: New feature vector
            target: Target value
            context: Learning context

        Returns:
            True if update was successful
        """
        pass

    @abstractmethod
    async def save(self, path: str) -> bool:
        """
        Save model to disk.

        Args:
            path: File path to save model

        Returns:
            True if save was successful
        """
        pass

    @abstractmethod
    async def load(self, path: str) -> bool:
        """
        Load model from disk.

        Args:
            path: File path to load model from

        Returns:
            True if load was successful
        """
        pass

    @abstractmethod
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance scores for explainability.

        Returns:
            Dictionary mapping feature names to importance scores
        """
        pass


class IPersonalizationEngine(ABC):
    """
    Interface for personalization engines.

    Orchestrates multiple models to provide personalized
    recommendations and predictions.
    """

    @abstractmethod
    async def get_recommendations(
        self, entity_id: str, entity_type: str, max_results: int = 10, context: Optional[LearningContext] = None
    ) -> List[ModelPrediction]:
        """
        Get personalized recommendations for an entity.

        Args:
            entity_id: ID of entity to get recommendations for
            entity_type: Type of entity
            max_results: Maximum number of recommendations
            context: Personalization context

        Returns:
            List of personalized predictions/recommendations
        """
        pass

    @abstractmethod
    async def get_explanation(
        self, entity_id: str, prediction: ModelPrediction, context: Optional[LearningContext] = None
    ) -> Dict[str, Any]:
        """
        Get explanation for a prediction.

        Args:
            entity_id: Entity ID the prediction was made for
            prediction: The prediction to explain
            context: Context for explanation

        Returns:
            Explanation dictionary with reasoning and feature importance
        """
        pass

    @abstractmethod
    async def record_feedback(
        self, entity_id: str, prediction_id: str, feedback: str, feedback_value: Optional[float] = None
    ) -> bool:
        """
        Record user feedback on a prediction.

        Args:
            entity_id: Entity ID the prediction was made for
            prediction_id: ID of the prediction
            feedback: Feedback description
            feedback_value: Numerical feedback value

        Returns:
            True if feedback was successfully recorded
        """
        pass


class ILearningService(ABC):
    """
    Main interface for the behavioral learning service.

    Provides high-level interface that orchestrates all
    learning components.
    """

    @abstractmethod
    async def track_interaction(
        self,
        event_type: EventType,
        entity_data: Dict[str, str],
        event_data: Dict[str, Any],
        context: Optional[LearningContext] = None,
    ) -> str:
        """
        Track user interaction and trigger learning.

        Args:
            event_type: Type of interaction
            entity_data: Entity identifiers (lead_id, property_id, etc.)
            event_data: Event-specific data
            context: Interaction context

        Returns:
            Event ID for tracking outcomes
        """
        pass

    @abstractmethod
    async def get_personalized_properties(
        self, lead_id: str, max_results: int = 10, context: Optional[LearningContext] = None
    ) -> List[ModelPrediction]:
        """
        Get personalized property recommendations for a lead.

        Args:
            lead_id: Lead ID to get recommendations for
            max_results: Maximum number of properties to recommend
            context: Recommendation context

        Returns:
            List of property predictions with scores
        """
        pass

    @abstractmethod
    async def get_agent_insights(self, agent_id: str, context: Optional[LearningContext] = None) -> Dict[str, Any]:
        """
        Get performance insights for an agent.

        Args:
            agent_id: Agent ID to analyze
            context: Analysis context

        Returns:
            Dictionary with agent performance insights
        """
        pass

    @abstractmethod
    async def record_outcome(self, event_id: str, outcome: str, outcome_value: Optional[float] = None) -> bool:
        """
        Record outcome for a tracked interaction.

        Args:
            event_id: ID of original event
            outcome: Outcome description
            outcome_value: Numerical outcome value

        Returns:
            True if outcome was successfully recorded
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Get health status of learning service.

        Returns:
            Health check results including model status and performance
        """
        pass


# Type aliases for convenience
EventFilter = Dict[str, Any]
FeatureDict = Dict[str, Any]
PredictionBatch = List[ModelPrediction]


# Exceptions
class LearningError(Exception):
    """Base exception for learning engine errors"""

    pass


class ModelNotTrainedError(LearningError):
    """Model has not been trained yet"""

    pass


class FeatureExtractionError(LearningError):
    """Error during feature extraction"""

    pass


class PredictionError(LearningError):
    """Error during prediction"""

    pass


class TrainingError(LearningError):
    """Error during model training"""

    pass
