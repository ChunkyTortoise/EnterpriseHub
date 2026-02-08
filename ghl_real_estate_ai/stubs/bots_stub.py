"""
Stub module providing fallback implementations when the jorge bots package
(bots.shared.ml_analytics_engine / bots.shared.feature_engineering) is not
available. All classes are no-op stubs that allow EnterpriseHub to import
and run without the cross-repo dependency.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# --- ml_analytics_engine stubs ---


class ModelType(str, Enum):
    LEAD_SCORING = "lead_scoring"
    CONVERSION = "conversion"
    CHURN = "churn"


@dataclass
class MLPredictionRequest:
    model_type: str = "lead_scoring"
    features: Dict[str, Any] = field(default_factory=dict)
    lead_id: Optional[str] = None


@dataclass
class MLPredictionResult:
    score: float = 0.0
    confidence: float = 0.0
    model_type: str = "lead_scoring"
    features_used: List[str] = field(default_factory=list)


@dataclass
class LeadJourneyPrediction:
    predicted_stage: str = "unknown"
    confidence: float = 0.0
    recommended_actions: List[str] = field(default_factory=list)


@dataclass
class ConversionProbabilityAnalysis:
    probability: float = 0.0
    key_factors: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class TouchpointOptimization:
    optimal_channel: str = "email"
    optimal_time: Optional[str] = None
    expected_lift: float = 0.0


class MLAnalyticsEngine:
    """No-op stub for MLAnalyticsEngine."""

    async def extract_features(self, lead_id: str, location_id: str = "") -> Dict[str, Any]:
        return {}

    async def predict(self, request: MLPredictionRequest) -> MLPredictionResult:
        return MLPredictionResult()

    async def get_lead_journey(self, lead_id: str) -> LeadJourneyPrediction:
        return LeadJourneyPrediction()

    async def get_conversion_probability(self, lead_id: str) -> ConversionProbabilityAnalysis:
        return ConversionProbabilityAnalysis()

    async def get_touchpoint_optimization(self, lead_id: str) -> TouchpointOptimization:
        return TouchpointOptimization()


_engine_instance: Optional[MLAnalyticsEngine] = None


def get_ml_analytics_engine() -> MLAnalyticsEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = MLAnalyticsEngine()
    return _engine_instance


def get_ml_engine() -> MLAnalyticsEngine:
    return get_ml_analytics_engine()


# --- feature_engineering stubs ---


@dataclass
class LeadFeatures:
    features: Dict[str, Any] = field(default_factory=dict)
    lead_id: Optional[str] = None


class FeatureEngineeringPipeline:
    """No-op stub for FeatureEngineeringPipeline."""

    def transform(self, data: Dict[str, Any]) -> LeadFeatures:
        return LeadFeatures(features=data)


_feature_engineer: Optional[FeatureEngineeringPipeline] = None


def get_feature_engineer() -> FeatureEngineeringPipeline:
    global _feature_engineer
    if _feature_engineer is None:
        _feature_engineer = FeatureEngineeringPipeline()
    return _feature_engineer
