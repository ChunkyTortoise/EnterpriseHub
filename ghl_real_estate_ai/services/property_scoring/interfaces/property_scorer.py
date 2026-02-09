"""
Property Scorer Strategy Interface
Defines the contract for all property scoring algorithms
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ConfidenceLevel(Enum):
    """Confidence level classifications"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXCELLENT = "excellent"


@dataclass
class ScoringResult:
    """
    Comprehensive scoring result with detailed breakdown

    This standardizes the output across all scoring strategies
    """

    overall_score: float  # 0-100 scale
    confidence_level: ConfidenceLevel

    # Component scores (0-100 scale)
    budget_score: float = 0.0
    location_score: float = 0.0
    feature_score: float = 0.0
    market_score: float = 0.0

    # Detailed reasoning and insights
    reasoning: List[str] = field(default_factory=list)
    match_insights: Dict[str, Any] = field(default_factory=dict)

    # Risk and opportunity indicators
    risk_factors: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)

    # Metadata for audit trails
    scorer_type: str = ""
    scoring_timestamp: Optional[str] = None
    model_version: Optional[str] = None

    def to_legacy_format(self) -> Dict[str, Any]:
        """Convert to legacy format for backward compatibility"""
        return {
            "match_score": int(self.overall_score),
            "budget_match": self.budget_score > 80,
            "location_match": self.location_score > 80,
            "features_match": self.feature_score > 80,
            "match_reasons": self.reasoning[:5],  # Limit for UI
            "confidence_level": self.confidence_level.value,
            "ml_breakdown": {
                "budget_confidence": self.budget_score,
                "location_confidence": self.location_score,
                "feature_confidence": self.feature_score,
                "market_confidence": self.market_score,
            },
        }


class PropertyScorer(ABC):
    """
    Abstract Strategy Interface for Property Scoring

    All scoring algorithms must implement this interface to ensure
    consistent behavior and interchangeability
    """

    def __init__(self, name: str, version: str = "1.0.0"):
        """
        Initialize the scorer with metadata

        Args:
            name: Human-readable name of the scoring strategy
            version: Version for tracking algorithm changes
        """
        self.name = name
        self.version = version
        self.is_trained = False
        self.metadata = {}

    @abstractmethod
    def calculate_score(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> ScoringResult:
        """
        Calculate comprehensive property score for a lead

        Args:
            property_data: Complete property information
            lead_preferences: Lead's preferences and requirements

        Returns:
            ScoringResult with detailed scoring breakdown

        Raises:
            ValueError: If required data is missing or invalid
        """
        pass

    @abstractmethod
    def validate_inputs(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> bool:
        """
        Validate that inputs meet scorer requirements

        Args:
            property_data: Property information to validate
            lead_preferences: Lead preferences to validate

        Returns:
            True if inputs are valid

        Raises:
            ValueError: If validation fails with specific error message
        """
        pass

    def supports_feature(self, feature: str) -> bool:
        """
        Check if this scorer supports a specific feature

        Args:
            feature: Feature name to check

        Returns:
            True if feature is supported
        """
        return True  # Default implementation supports all features

    def get_required_fields(self) -> Dict[str, List[str]]:
        """
        Get required fields for this scorer

        Returns:
            Dict with 'property' and 'preferences' field lists
        """
        return {"property": ["price", "bedrooms", "address"], "preferences": ["budget"]}

    def get_metadata(self) -> Dict[str, Any]:
        """Get scorer metadata and capabilities"""
        return {
            "name": self.name,
            "version": self.version,
            "is_trained": self.is_trained,
            "supported_features": self.get_supported_features(),
            "required_fields": self.get_required_fields(),
            **self.metadata,
        }

    def get_supported_features(self) -> List[str]:
        """Get list of supported features"""
        return ["budget_matching", "location_matching", "feature_matching", "basic_reasoning"]

    def set_metadata(self, key: str, value: Any) -> None:
        """Set custom metadata for this scorer"""
        self.metadata[key] = value

    def warm_up(self) -> None:
        """
        Warm up the scorer (load models, initialize caches, etc.)
        Default implementation does nothing
        """
        pass

    def cleanup(self) -> None:
        """
        Clean up resources (close connections, clear caches, etc.)
        Default implementation does nothing
        """
        pass


class TrainableScorer(PropertyScorer):
    """
    Extended interface for ML-based scorers that support training
    """

    @abstractmethod
    def train(
        self, training_data: List[Dict[str, Any]], validation_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Train the scoring model

        Args:
            training_data: List of training examples with features and labels
            validation_data: Optional validation dataset

        Returns:
            Training results and metrics
        """
        pass

    @abstractmethod
    def save_model(self, path: str) -> None:
        """Save trained model to disk"""
        pass

    @abstractmethod
    def load_model(self, path: str) -> None:
        """Load trained model from disk"""
        pass

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the trained model"""
        return {"is_trained": self.is_trained, "model_type": self.__class__.__name__, "version": self.version}


class AdaptiveScorer(TrainableScorer):
    """
    Extended interface for adaptive scorers that learn from user feedback
    """

    @abstractmethod
    def update_from_feedback(
        self, property_id: str, lead_preferences: Dict[str, Any], feedback: Dict[str, Any]
    ) -> None:
        """
        Update scoring based on lead feedback

        Args:
            property_id: Property identifier
            lead_preferences: Lead preferences used in original scoring
            feedback: Lead feedback (viewing, interest, rejection reasons)
        """
        pass

    @abstractmethod
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get statistics about learning progress"""
        pass
