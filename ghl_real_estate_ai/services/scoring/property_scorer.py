"""
Property Scoring Strategy Interface

Enterprise-grade Strategy Pattern implementation for flexible property scoring algorithms.
Follows SOLID principles and enables runtime strategy switching.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence level indicators for scoring results"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ScoringResult:
    """
    Standardized scoring result with confidence metrics and reasoning.

    Provides transparent AI decision making with explainable factors.
    """
    overall_score: float  # 0-100 percentage
    confidence_level: ConfidenceLevel
    budget_match: float  # 0-100 budget alignment score
    location_match: float  # 0-100 location preference score
    feature_match: float  # 0-100 feature requirements score
    market_context: float  # 0-100 market condition score
    reasoning: List[str]  # Human-readable explanations
    metadata: Dict[str, Any]  # Additional scoring context

    def get_confidence_level(self) -> ConfidenceLevel:
        """Calculate confidence level based on overall score"""
        if self.overall_score >= 85:
            return ConfidenceLevel.HIGH
        elif self.overall_score >= 70:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def to_legacy_format(self) -> Dict[str, Any]:
        """Convert to legacy format for backward compatibility"""
        return {
            'match_score': int(self.overall_score),
            'budget_match': self.budget_match > 80,
            'location_match': self.location_match > 80,
            'features_match': self.feature_match > 80,
            'match_reasons': self.reasoning,
            'confidence_level': self.confidence_level.value
        }


class PropertyScorer(ABC):
    """
    Strategy interface for property scoring algorithms.

    Implements Strategy Pattern enabling runtime algorithm switching
    while maintaining consistent interface.
    """

    @abstractmethod
    def calculate_score(
        self,
        property_data: Dict[str, Any],
        lead_preferences: Dict[str, Any]
    ) -> ScoringResult:
        """
        Calculate property match score against lead preferences.

        Args:
            property_data: Property details (price, location, features, etc.)
            lead_preferences: Lead requirements and preferences

        Returns:
            ScoringResult with score breakdown and reasoning

        Raises:
            ValueError: If input data is invalid or insufficient
        """
        pass

    @abstractmethod
    def validate_inputs(
        self,
        property_data: Dict[str, Any],
        lead_preferences: Dict[str, Any]
    ) -> bool:
        """
        Validate that inputs are sufficient for scoring.

        Args:
            property_data: Property details to validate
            lead_preferences: Lead preferences to validate

        Returns:
            True if inputs are valid, False otherwise
        """
        pass

    def get_strategy_name(self) -> str:
        """Get human-readable name for this scoring strategy"""
        return self.__class__.__name__

    def get_performance_characteristics(self) -> Dict[str, str]:
        """Get performance metadata for strategy selection"""
        return {
            'speed': 'unknown',
            'accuracy': 'unknown',
            'complexity': 'unknown',
            'use_case': 'general'
        }


class TrainableScorer(PropertyScorer):
    """
    Extension interface for ML-based scorers that can be trained.

    Adds training capabilities while maintaining base Strategy interface.
    """

    @abstractmethod
    def train(self, training_data: List[Dict[str, Any]]) -> None:
        """
        Train the scoring model with historical data.

        Args:
            training_data: List of property-lead-outcome examples
        """
        pass

    @abstractmethod
    def is_trained(self) -> bool:
        """Check if the model has been trained and is ready for scoring"""
        pass


class AdaptiveScorer(PropertyScorer):
    """
    Extension interface for scorers that learn from user behavior.

    Enables personalization and continuous improvement based on interactions.
    """

    @abstractmethod
    def update_preferences(
        self,
        lead_id: str,
        property_id: str,
        interaction_type: str,
        feedback: Dict[str, Any]
    ) -> None:
        """
        Update scoring based on user interaction feedback.

        Args:
            lead_id: Unique lead identifier
            property_id: Property that was interacted with
            interaction_type: Type of interaction (view, click, tour, offer)
            feedback: Additional feedback data
        """
        pass

    @abstractmethod
    def get_learned_preferences(self, lead_id: str) -> Dict[str, Any]:
        """
        Get accumulated preference learning for a specific lead.

        Args:
            lead_id: Lead to get learned preferences for

        Returns:
            Dictionary of learned preferences and weights
        """
        pass


@dataclass
class ScoringContext:
    """
    Configuration and metadata for scoring operations.

    Provides context for strategy selection and execution.
    """
    lead_id: Optional[str] = None
    agent_id: Optional[str] = None
    market_area: Optional[str] = None
    urgency_level: str = "normal"  # low, normal, high, urgent
    performance_priority: str = "balanced"  # speed, accuracy, balanced
    enable_learning: bool = True
    enable_fallback: bool = True
    max_properties: int = 50
    min_confidence: float = 60.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}