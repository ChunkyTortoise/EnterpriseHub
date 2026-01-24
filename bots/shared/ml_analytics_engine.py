"""
ML Analytics Engine - Jorge Real Estate AI Architecture
========================================================

Advanced machine learning analytics engine implementing:
- Core ML Prediction Service with model management
- Confidence-based escalation to Claude AI
- Real-time caching with Redis integration
- Performance targets: <50ms inference, 5min cache TTL
- XGBoost model support with scikit-learn compatibility
- Event-driven architecture for ML predictions
- Feature engineering pipeline compatibility
- Enterprise-grade error handling and monitoring

Integrates with:
- cache_service.py patterns for performance optimization
- lead_analyzer.py line 234 for ML → Claude escalation pipeline
- Event system for real-time ML analytics

Author: Claude Sonnet 4
Date: 2026-01-23
Version: 1.0.0
Performance: <50ms inference target, 0.85 confidence threshold
"""

import asyncio
import json
import logging
import time
import uuid
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import (
    Dict, List, Optional, Any, Union, Tuple,
    Callable, Awaitable, Protocol
)
from dataclasses import dataclass, asdict, field
from enum import Enum
from abc import ABC, abstractmethod
from pathlib import Path
import hashlib

# ML Libraries
try:
    import xgboost as xgb
    from sklearn.base import BaseEstimator
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    xgb = None

# Jorge AI Integration
from ghl_real_estate_ai.services.cache_service import get_cache_service, TenantScopedCache
from ghl_real_estate_ai.services.event_streaming_service import (
    EventStreamingService, StreamEvent, EventType, Priority
)
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class MLEventType(Enum):
    """ML-specific event types for analytics pipeline"""
    LEAD_ML_SCORED = "lead.ml.scored"
    LEAD_ML_ESCALATED = "lead.ml.escalated"  # Low confidence -> Claude AI
    LEAD_ML_CACHE_HIT = "lead.ml.cache_hit"
    MODEL_TRAINED = "model.trained"
    MODEL_LOADED = "model.loaded"
    FEATURE_ENGINEERING_COMPLETED = "feature.engineering.completed"
    PREDICTION_BATCH_COMPLETED = "prediction.batch.completed"
    CONFIDENCE_THRESHOLD_BREACHED = "confidence.threshold.breached"
    MODEL_DRIFT_DETECTED = "model.drift.detected"
    PERFORMANCE_DEGRADED = "performance.degraded"


class ModelType(Enum):
    """Supported ML model types"""
    XGBOOST_CLASSIFIER = "xgboost_classifier"
    XGBOOST_REGRESSOR = "xgboost_regressor"
    SKLEARN_ENSEMBLE = "sklearn_ensemble"
    NEURAL_NETWORK = "neural_network"
    CUSTOM_MODEL = "custom_model"


class ConfidenceLevel(Enum):
    """Confidence levels for prediction quality"""
    HIGH = "high"          # >= 0.85, use ML prediction
    MEDIUM = "medium"      # 0.65-0.85, use with caution
    LOW = "low"           # < 0.65, escalate to Claude AI
    UNCERTAIN = "uncertain" # Model unavailable/error


@dataclass
class MLPredictionRequest:
    """Structured request for ML prediction"""
    lead_id: str
    tenant_id: Optional[str] = None
    features: Optional[Dict[str, Any]] = None
    model_name: str = "default_lead_scorer"
    include_confidence: bool = True
    include_feature_importance: bool = False
    cache_ttl: int = 300  # 5 minutes
    request_id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: Optional[datetime] = field(default_factory=datetime.now)


@dataclass
class MLPredictionResult:
    """Comprehensive ML prediction result"""
    lead_id: str
    prediction: Union[float, int, str]
    confidence: float
    confidence_level: ConfidenceLevel
    model_name: str
    model_version: str
    feature_importance: Optional[Dict[str, float]] = None
    processing_time_ms: float = 0.0
    cache_hit: bool = False
    escalated_to_claude: bool = False
    raw_prediction_data: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    created_at: Optional[datetime] = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for caching/serialization"""
        result = asdict(self)
        result['confidence_level'] = self.confidence_level.value
        result['created_at'] = self.created_at.isoformat() if self.created_at else None
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MLPredictionResult':
        """Create from dictionary"""
        data = data.copy()
        if 'confidence_level' in data:
            data['confidence_level'] = ConfidenceLevel(data['confidence_level'])
        if 'created_at' in data and data['created_at']:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class ModelMetrics:
    """Model performance metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    last_trained: datetime
    training_samples: int
    feature_count: int
    avg_inference_time_ms: float
    total_predictions: int
    confidence_distribution: Dict[str, int]


@dataclass
class FeatureEngineeringConfig:
    """Configuration for feature engineering pipeline"""
    enabled_features: List[str]
    scaling_method: str = "standard"  # standard, minmax, robust
    categorical_encoding: str = "label"  # label, onehot, target
    handle_missing_values: str = "median"  # median, mean, mode, drop
    feature_selection_method: Optional[str] = None
    custom_transformations: Optional[Dict[str, Any]] = None


class AbstractMLModel(ABC):
    """Abstract base class for ML models"""

    @abstractmethod
    async def predict(self, features: Dict[str, Any]) -> Tuple[Any, float]:
        """Make prediction with confidence score"""
        pass

    @abstractmethod
    async def predict_batch(self, features_list: List[Dict[str, Any]]) -> List[Tuple[Any, float]]:
        """Batch prediction for efficiency"""
        pass

    @abstractmethod
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores"""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model metadata and info"""
        pass


class XGBoostModel(AbstractMLModel):
    """XGBoost model wrapper with Jorge AI patterns"""

    def __init__(self, model_path: Optional[str] = None, model_type: ModelType = ModelType.XGBOOST_CLASSIFIER):
        self.model_path = model_path
        self.model_type = model_type
        self.model: Optional[xgb.XGBModel] = None
        self.scaler: Optional[StandardScaler] = None
        self.label_encoder: Optional[LabelEncoder] = None
        self.feature_names: List[str] = []
        self.model_version = "1.0.0"
        self.last_loaded = None
        self.metrics: Optional[ModelMetrics] = None

    async def load_model(self) -> bool:
        """Load XGBoost model from disk"""
        if not XGBOOST_AVAILABLE:
            logger.error("XGBoost not available - install with: pip install xgboost")
            return False

        try:
            if self.model_path and Path(self.model_path).exists():
                self.model = xgb.XGBClassifier()
                self.model.load_model(self.model_path)

                # Load associated preprocessing objects
                base_path = Path(self.model_path).parent
                scaler_path = base_path / "scaler.pkl"
                encoder_path = base_path / "label_encoder.pkl"
                features_path = base_path / "feature_names.json"

                if scaler_path.exists():
                    with open(scaler_path, 'rb') as f:
                        self.scaler = pickle.load(f)

                if encoder_path.exists():
                    with open(encoder_path, 'rb') as f:
                        self.label_encoder = pickle.load(f)

                if features_path.exists():
                    with open(features_path, 'r') as f:
                        self.feature_names = json.load(f)

                self.last_loaded = datetime.now()
                logger.info(f"XGBoost model loaded successfully from {self.model_path}")
                return True
            else:
                # Create a mock model for development/demo purposes
                await self._create_mock_model()
                return True

        except Exception as e:
            logger.error(f"Failed to load XGBoost model: {e}")
            return False

    async def _create_mock_model(self):
        """Create a mock model for development/demo"""
        logger.info("Creating mock XGBoost model for development")

        # Generate synthetic training data
        np.random.seed(42)
        n_samples, n_features = 1000, 10

        # Create feature names matching Jorge's system
        self.feature_names = [
            "jorge_score", "engagement_score", "response_time_avg",
            "message_count", "question_depth", "price_range_fit",
            "location_preference_strength", "timeline_urgency",
            "communication_frequency", "market_activity_level"
        ]

        # Generate synthetic features
        X = np.random.randn(n_samples, n_features)
        # Create realistic target: higher scores for engaged leads
        y = (X[:, 0] + X[:, 1] + np.random.randn(n_samples) * 0.1 > 0).astype(int)

        # Initialize and train model
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            eval_metric='logloss'
        )

        # Initialize scaler
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Train model
        self.model.fit(X_scaled, y)

        # Calculate mock metrics
        y_pred = self.model.predict(X_scaled)
        y_proba = self.model.predict_proba(X_scaled)

        precision, recall, f1, _ = precision_recall_fscore_support(y, y_pred, average='binary')

        self.metrics = ModelMetrics(
            accuracy=accuracy_score(y, y_pred),
            precision=precision,
            recall=recall,
            f1_score=f1,
            last_trained=datetime.now(),
            training_samples=n_samples,
            feature_count=n_features,
            avg_inference_time_ms=2.5,
            total_predictions=0,
            confidence_distribution={"high": 0, "medium": 0, "low": 0}
        )

        self.last_loaded = datetime.now()
        logger.info("Mock XGBoost model created successfully")

    async def predict(self, features: Dict[str, Any]) -> Tuple[Any, float]:
        """Make single prediction with confidence"""
        if not self.model:
            await self.load_model()

        try:
            # Convert features to array
            feature_array = self._dict_to_array(features)

            # Scale features if scaler is available
            if self.scaler:
                feature_array = self.scaler.transform([feature_array])
            else:
                feature_array = np.array([feature_array])

            # Make prediction
            start_time = time.time()

            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(feature_array)[0]
                prediction = np.argmax(probabilities)
                confidence = float(np.max(probabilities))
            else:
                prediction = self.model.predict(feature_array)[0]
                confidence = 0.8  # Default confidence for non-probabilistic models

            inference_time = (time.time() - start_time) * 1000

            # Update metrics
            if self.metrics:
                self.metrics.total_predictions += 1
                # Update running average of inference time
                self.metrics.avg_inference_time_ms = (
                    (self.metrics.avg_inference_time_ms * (self.metrics.total_predictions - 1) + inference_time) /
                    self.metrics.total_predictions
                )

            return prediction, confidence

        except Exception as e:
            logger.error(f"XGBoost prediction failed: {e}")
            return None, 0.0

    async def predict_batch(self, features_list: List[Dict[str, Any]]) -> List[Tuple[Any, float]]:
        """Efficient batch prediction"""
        if not self.model:
            await self.load_model()

        try:
            # Convert all features to array
            feature_arrays = [self._dict_to_array(features) for features in features_list]
            feature_matrix = np.array(feature_arrays)

            # Scale if scaler available
            if self.scaler:
                feature_matrix = self.scaler.transform(feature_matrix)

            # Batch prediction
            start_time = time.time()

            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(feature_matrix)
                predictions = np.argmax(probabilities, axis=1)
                confidences = np.max(probabilities, axis=1)
            else:
                predictions = self.model.predict(feature_matrix)
                confidences = np.full(len(predictions), 0.8)

            inference_time = (time.time() - start_time) * 1000

            # Update metrics
            if self.metrics:
                batch_size = len(features_list)
                self.metrics.total_predictions += batch_size
                # Update running average
                self.metrics.avg_inference_time_ms = (
                    (self.metrics.avg_inference_time_ms * (self.metrics.total_predictions - batch_size) +
                     inference_time / batch_size * batch_size) / self.metrics.total_predictions
                )

            return list(zip(predictions.tolist(), confidences.tolist()))

        except Exception as e:
            logger.error(f"XGBoost batch prediction failed: {e}")
            return [(None, 0.0)] * len(features_list)

    def get_feature_importance(self) -> Dict[str, float]:
        """Get XGBoost feature importance"""
        if not self.model or not hasattr(self.model, 'feature_importances_'):
            return {}

        try:
            importance_scores = self.model.feature_importances_
            if len(self.feature_names) == len(importance_scores):
                return dict(zip(self.feature_names, importance_scores.tolist()))
            else:
                # Fallback to generic names
                return {f"feature_{i}": score for i, score in enumerate(importance_scores)}

        except Exception as e:
            logger.error(f"Failed to get feature importance: {e}")
            return {}

    def get_model_info(self) -> Dict[str, Any]:
        """Get comprehensive model information"""
        info = {
            "model_type": self.model_type.value,
            "model_version": self.model_version,
            "last_loaded": self.last_loaded.isoformat() if self.last_loaded else None,
            "feature_count": len(self.feature_names),
            "feature_names": self.feature_names,
            "has_scaler": self.scaler is not None,
            "has_label_encoder": self.label_encoder is not None,
            "xgboost_available": XGBOOST_AVAILABLE
        }

        if self.metrics:
            info["metrics"] = asdict(self.metrics)
            if info["metrics"]["last_trained"]:
                info["metrics"]["last_trained"] = self.metrics.last_trained.isoformat()

        return info

    def _dict_to_array(self, features: Dict[str, Any]) -> np.ndarray:
        """Convert feature dictionary to numpy array"""
        if self.feature_names:
            # Use specified feature order
            feature_vector = []
            for feature_name in self.feature_names:
                value = features.get(feature_name, 0.0)
                # Handle non-numeric values
                if isinstance(value, (str, bool)):
                    value = 1.0 if value else 0.0
                feature_vector.append(float(value))
            return np.array(feature_vector)
        else:
            # Fallback: use all numeric values in sorted key order
            numeric_features = {}
            for k, v in features.items():
                try:
                    if isinstance(v, (int, float)):
                        numeric_features[k] = float(v)
                    elif isinstance(v, bool):
                        numeric_features[k] = 1.0 if v else 0.0
                    elif isinstance(v, str) and v.replace('.', '').replace('-', '').isdigit():
                        numeric_features[k] = float(v)
                except (ValueError, TypeError):
                    continue

            # Sort by key for consistency
            sorted_features = sorted(numeric_features.items())
            return np.array([v for k, v in sorted_features])


class FeatureEngineeringPipeline:
    """Advanced feature engineering for Jorge Real Estate AI"""

    def __init__(self, config: Optional[FeatureEngineeringConfig] = None):
        self.config = config or FeatureEngineeringConfig(
            enabled_features=[
                "jorge_score", "engagement_score", "response_time_avg",
                "message_count", "question_depth", "price_range_fit",
                "location_preference_strength", "timeline_urgency",
                "communication_frequency", "market_activity_level"
            ]
        )
        self.cache = get_cache_service()

    async def engineer_features(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Engineer features from raw lead data"""
        try:
            features = {}

            # Base Jorge scoring features
            features.update(await self._extract_jorge_features(lead_data))

            # Engagement and behavioral features
            features.update(await self._extract_engagement_features(lead_data))

            # Temporal and market features
            features.update(await self._extract_temporal_features(lead_data))

            # Property preference features
            features.update(await self._extract_property_features(lead_data))

            # Communication pattern features
            features.update(await self._extract_communication_features(lead_data))

            # Filter to enabled features
            filtered_features = {
                k: v for k, v in features.items()
                if k in self.config.enabled_features
            }

            logger.debug(f"Engineered {len(filtered_features)} features from lead data")
            return filtered_features

        except Exception as e:
            logger.error(f"Feature engineering failed: {e}")
            # Return minimal feature set
            return {
                "jorge_score": lead_data.get("jorge_score", 0.0),
                "engagement_score": 0.5,
                "message_count": lead_data.get("message_count", 0)
            }

    async def _extract_jorge_features(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract Jorge's original scoring features"""
        return {
            "jorge_score": float(lead_data.get("jorge_score", 0.0)),
            "question_depth": float(lead_data.get("questions_asked", 0)),
            "qualification_stage": float(lead_data.get("qualification_stage", 0))
        }

    async def _extract_engagement_features(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract engagement and activity features"""
        messages = lead_data.get("messages", [])

        engagement_score = 0.0
        response_times = []

        if messages:
            # Calculate response time patterns
            for i in range(1, len(messages)):
                prev_msg = messages[i-1]
                curr_msg = messages[i]

                if prev_msg.get("sender") == "agent" and curr_msg.get("sender") == "lead":
                    # Lead responded to agent
                    try:
                        prev_time = datetime.fromisoformat(prev_msg.get("timestamp", ""))
                        curr_time = datetime.fromisoformat(curr_msg.get("timestamp", ""))
                        response_time = (curr_time - prev_time).total_seconds() / 60  # minutes
                        response_times.append(response_time)
                    except:
                        pass

            # Calculate engagement score
            message_count = len([m for m in messages if m.get("sender") == "lead"])
            avg_message_length = np.mean([len(m.get("content", "")) for m in messages if m.get("sender") == "lead"])

            engagement_score = min(1.0, (message_count * 0.1 + avg_message_length * 0.01) / 10)

        return {
            "engagement_score": engagement_score,
            "message_count": len(messages),
            "response_time_avg": np.mean(response_times) if response_times else 60.0,  # Default 1 hour
            "response_time_std": np.std(response_times) if len(response_times) > 1 else 0.0
        }

    async def _extract_temporal_features(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract time-based features"""
        created_at = lead_data.get("created_at")
        current_time = datetime.now()

        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        elif created_at is None:
            created_at = current_time

        # Calculate lead age
        lead_age_hours = (current_time - created_at).total_seconds() / 3600

        # Time-based urgency (peaks at 24-48 hours)
        timeline_urgency = max(0.0, min(1.0, (48 - lead_age_hours) / 48)) if lead_age_hours < 168 else 0.1

        # Communication frequency (messages per day)
        communication_frequency = lead_data.get("message_count", 0) / max(1, lead_age_hours / 24)

        return {
            "lead_age_hours": lead_age_hours,
            "timeline_urgency": timeline_urgency,
            "communication_frequency": min(10.0, communication_frequency)  # Cap at 10 per day
        }

    async def _extract_property_features(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract property preference and market fit features"""
        preferences = lead_data.get("property_preferences", {})

        # Price range fit (how specific/realistic is the price range)
        price_min = preferences.get("price_min", 0)
        price_max = preferences.get("price_max", 999999999)
        price_range_specificity = 1.0 - min(1.0, (price_max - price_min) / 500000)  # More specific = higher score

        # Location preference strength
        location_data = preferences.get("location", {})
        location_specificity = len([v for v in location_data.values() if v]) / max(1, len(location_data))

        # Market activity level (can be enhanced with real market data)
        market_activity_level = 0.7  # Default market activity

        return {
            "price_range_fit": price_range_specificity,
            "location_preference_strength": location_specificity,
            "market_activity_level": market_activity_level
        }

    async def _extract_communication_features(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract communication style and quality features"""
        messages = lead_data.get("messages", [])
        lead_messages = [m for m in messages if m.get("sender") == "lead"]

        if not lead_messages:
            return {
                "avg_message_length": 0.0,
                "question_ratio": 0.0,
                "sentiment_score": 0.5
            }

        # Message quality indicators
        total_length = sum(len(m.get("content", "")) for m in lead_messages)
        avg_message_length = total_length / len(lead_messages)

        # Question ratio (engagement indicator)
        question_count = sum(1 for m in lead_messages if "?" in m.get("content", ""))
        question_ratio = question_count / len(lead_messages)

        # Simple sentiment scoring (can be enhanced with NLP)
        positive_words = ["interested", "yes", "good", "great", "love", "perfect", "definitely"]
        negative_words = ["no", "not interested", "too expensive", "wrong", "bad", "hate"]

        all_text = " ".join(m.get("content", "").lower() for m in lead_messages)
        positive_score = sum(1 for word in positive_words if word in all_text)
        negative_score = sum(1 for word in negative_words if word in all_text)

        sentiment_score = 0.5 + (positive_score - negative_score) * 0.1
        sentiment_score = max(0.0, min(1.0, sentiment_score))

        return {
            "avg_message_length": min(200.0, avg_message_length),  # Cap at 200 chars
            "question_ratio": question_ratio,
            "sentiment_score": sentiment_score
        }


class MLAnalyticsEngine:
    """
    Enterprise ML Analytics Engine for Jorge Real Estate AI

    Features:
    - <50ms inference performance targets
    - Confidence-based escalation to Claude AI (threshold 0.85)
    - Real-time Redis caching (5min TTL)
    - XGBoost model support with scikit-learn compatibility
    - Event-driven architecture for ML analytics
    - Comprehensive error handling and monitoring
    - Integration with cache_service.py patterns
    """

    def __init__(self,
                 tenant_id: Optional[str] = None,
                 confidence_threshold: float = 0.85,
                 cache_ttl: int = 300):
        self.tenant_id = tenant_id
        self.confidence_threshold = confidence_threshold
        self.cache_ttl = cache_ttl

        # Core services
        self.cache = TenantScopedCache(tenant_id) if tenant_id else get_cache_service()
        self.event_service = EventStreamingService()
        self.feature_pipeline = FeatureEngineeringPipeline()

        # Model registry
        self.models: Dict[str, AbstractMLModel] = {}
        self.model_metadata: Dict[str, Dict[str, Any]] = {}

        # Performance tracking
        self.metrics = {
            "total_predictions": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "escalations_to_claude": 0,
            "avg_inference_time_ms": 0.0,
            "confidence_distribution": {"high": 0, "medium": 0, "low": 0},
            "error_count": 0
        }

        # Initialize default model
        asyncio.create_task(self._initialize_default_model())

    async def _initialize_default_model(self):
        """Initialize default XGBoost model"""
        try:
            default_model = XGBoostModel(
                model_type=ModelType.XGBOOST_CLASSIFIER
            )

            success = await default_model.load_model()
            if success:
                await self.register_model("default_lead_scorer", default_model)
                logger.info("Default XGBoost model initialized successfully")
            else:
                logger.warning("Failed to initialize default model")

        except Exception as e:
            logger.error(f"Error initializing default model: {e}")

    async def register_model(self, name: str, model: AbstractMLModel) -> bool:
        """Register a new ML model"""
        try:
            self.models[name] = model
            self.model_metadata[name] = {
                "registered_at": datetime.now().isoformat(),
                "model_info": model.get_model_info()
            }

            # Publish model loaded event
            await self._publish_event(
                MLEventType.MODEL_LOADED,
                {
                    "model_name": name,
                    "model_type": type(model).__name__,
                    "metadata": self.model_metadata[name]
                }
            )

            logger.info(f"Model '{name}' registered successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to register model '{name}': {e}")
            return False

    async def predict_lead_score(self, request: MLPredictionRequest) -> MLPredictionResult:
        """
        Main prediction method with caching and escalation logic

        Performance target: <50ms inference time
        Confidence threshold: 0.85 for Claude escalation
        Cache TTL: 5 minutes
        """
        start_time = time.time()
        request_id = request.request_id or str(uuid.uuid4())

        try:
            # Generate cache key
            cache_key = self._generate_cache_key(request)

            # Check cache first
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                self.metrics["cache_hits"] += 1
                result = MLPredictionResult.from_dict(cached_result)
                result.cache_hit = True
                result.processing_time_ms = (time.time() - start_time) * 1000

                # Publish cache hit event
                await self._publish_event(
                    MLEventType.LEAD_ML_CACHE_HIT,
                    {
                        "lead_id": request.lead_id,
                        "cache_key": cache_key,
                        "processing_time_ms": result.processing_time_ms
                    }
                )

                return result

            # Cache miss - perform ML prediction
            self.metrics["cache_misses"] += 1

            # Get or engineer features
            if request.features:
                features = request.features
            else:
                # Need to fetch lead data and engineer features
                lead_data = await self._fetch_lead_data(request.lead_id)
                features = await self.feature_pipeline.engineer_features(lead_data)

            # Get model
            model = self.models.get(request.model_name)
            if not model:
                logger.warning(f"Model '{request.model_name}' not found, using default")
                model = self.models.get("default_lead_scorer")

            if not model:
                raise ValueError("No ML models available")

            # Make prediction
            prediction, confidence = await model.predict(features)

            # Determine confidence level
            if confidence >= self.confidence_threshold:
                confidence_level = ConfidenceLevel.HIGH
            elif confidence >= 0.65:
                confidence_level = ConfidenceLevel.MEDIUM
            else:
                confidence_level = ConfidenceLevel.LOW

            # Get feature importance if requested
            feature_importance = None
            if request.include_feature_importance:
                feature_importance = model.get_feature_importance()

            # Create result
            processing_time = (time.time() - start_time) * 1000

            result = MLPredictionResult(
                lead_id=request.lead_id,
                prediction=prediction,
                confidence=confidence,
                confidence_level=confidence_level,
                model_name=request.model_name,
                model_version=model.get_model_info().get("model_version", "1.0.0"),
                feature_importance=feature_importance,
                processing_time_ms=processing_time,
                cache_hit=False,
                escalated_to_claude=False,
                request_id=request_id
            )

            # Cache the result
            await self.cache.set(cache_key, result.to_dict(), request.cache_ttl)

            # Update metrics
            self._update_metrics(result)

            # Check for Claude escalation
            if confidence_level == ConfidenceLevel.LOW:
                await self._escalate_to_claude(result)

            # Publish ML scored event
            await self._publish_event(
                MLEventType.LEAD_ML_SCORED,
                {
                    "lead_id": request.lead_id,
                    "prediction": prediction,
                    "confidence": confidence,
                    "confidence_level": confidence_level.value,
                    "processing_time_ms": processing_time,
                    "model_name": request.model_name
                }
            )

            return result

        except Exception as e:
            self.metrics["error_count"] += 1
            logger.error(f"ML prediction failed for lead {request.lead_id}: {e}")

            # Return uncertain result
            processing_time = (time.time() - start_time) * 1000
            return MLPredictionResult(
                lead_id=request.lead_id,
                prediction=0.5,  # Neutral prediction
                confidence=0.0,
                confidence_level=ConfidenceLevel.UNCERTAIN,
                model_name=request.model_name,
                model_version="error",
                processing_time_ms=processing_time,
                escalated_to_claude=True,  # Always escalate on errors
                request_id=request_id
            )

    async def predict_batch(self, requests: List[MLPredictionRequest]) -> List[MLPredictionResult]:
        """Efficient batch prediction with parallel processing"""
        if not requests:
            return []

        # Group requests by model for efficient batch processing
        model_groups = {}
        for request in requests:
            model_name = request.model_name
            if model_name not in model_groups:
                model_groups[model_name] = []
            model_groups[model_name].append(request)

        # Process each model group in parallel
        all_results = []
        tasks = []

        for model_name, model_requests in model_groups.items():
            task = asyncio.create_task(
                self._process_batch_for_model(model_name, model_requests)
            )
            tasks.append(task)

        # Wait for all tasks to complete
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results
        for result_group in batch_results:
            if isinstance(result_group, Exception):
                logger.error(f"Batch processing error: {result_group}")
                continue
            all_results.extend(result_group)

        # Publish batch completion event
        await self._publish_event(
            MLEventType.PREDICTION_BATCH_COMPLETED,
            {
                "batch_size": len(requests),
                "successful_predictions": len(all_results),
                "models_used": list(model_groups.keys())
            }
        )

        return all_results

    async def _process_batch_for_model(self, model_name: str, requests: List[MLPredictionRequest]) -> List[MLPredictionResult]:
        """Process batch of requests for a specific model"""
        try:
            model = self.models.get(model_name)
            if not model:
                model = self.models.get("default_lead_scorer")

            if not model:
                logger.error(f"No model available for batch processing")
                return []

            # Prepare features for all requests
            features_list = []
            for request in requests:
                if request.features:
                    features_list.append(request.features)
                else:
                    # Engineer features
                    lead_data = await self._fetch_lead_data(request.lead_id)
                    features = await self.feature_pipeline.engineer_features(lead_data)
                    features_list.append(features)

            # Batch prediction
            predictions_with_confidence = await model.predict_batch(features_list)

            # Create results
            results = []
            for i, (prediction, confidence) in enumerate(predictions_with_confidence):
                request = requests[i]

                # Determine confidence level
                if confidence >= self.confidence_threshold:
                    confidence_level = ConfidenceLevel.HIGH
                elif confidence >= 0.65:
                    confidence_level = ConfidenceLevel.MEDIUM
                else:
                    confidence_level = ConfidenceLevel.LOW

                result = MLPredictionResult(
                    lead_id=request.lead_id,
                    prediction=prediction,
                    confidence=confidence,
                    confidence_level=confidence_level,
                    model_name=model_name,
                    model_version=model.get_model_info().get("model_version", "1.0.0"),
                    processing_time_ms=5.0,  # Approximation for batch
                    cache_hit=False,
                    request_id=request.request_id
                )

                results.append(result)

                # Update metrics and handle escalation
                self._update_metrics(result)
                if confidence_level == ConfidenceLevel.LOW:
                    asyncio.create_task(self._escalate_to_claude(result))

            return results

        except Exception as e:
            logger.error(f"Batch processing failed for model {model_name}: {e}")
            return []

    async def _escalate_to_claude(self, result: MLPredictionResult):
        """Escalate low-confidence predictions to Claude AI"""
        try:
            result.escalated_to_claude = True
            self.metrics["escalations_to_claude"] += 1

            # Publish escalation event
            await self._publish_event(
                MLEventType.LEAD_ML_ESCALATED,
                {
                    "lead_id": result.lead_id,
                    "ml_prediction": result.prediction,
                    "ml_confidence": result.confidence,
                    "escalation_reason": "low_confidence",
                    "confidence_threshold": self.confidence_threshold
                }
            )

            logger.info(f"Escalated lead {result.lead_id} to Claude AI (confidence: {result.confidence:.3f})")

        except Exception as e:
            logger.error(f"Failed to escalate lead {result.lead_id}: {e}")

    async def _fetch_lead_data(self, lead_id: str) -> Dict[str, Any]:
        """Fetch lead data from database or cache"""
        # This would typically fetch from database
        # For now, return mock data
        return {
            "lead_id": lead_id,
            "jorge_score": 4.2,
            "created_at": datetime.now() - timedelta(hours=2),
            "message_count": 5,
            "messages": [
                {"sender": "lead", "content": "I'm interested in buying a house", "timestamp": datetime.now().isoformat()},
                {"sender": "agent", "content": "Great! What's your price range?", "timestamp": datetime.now().isoformat()},
                {"sender": "lead", "content": "Around $400k", "timestamp": datetime.now().isoformat()}
            ],
            "property_preferences": {
                "price_min": 350000,
                "price_max": 450000,
                "location": {"city": "Austin", "state": "TX"}
            }
        }

    def _generate_cache_key(self, request: MLPredictionRequest) -> str:
        """Generate cache key for prediction request"""
        # Create hash of key components
        key_components = {
            "lead_id": request.lead_id,
            "model_name": request.model_name,
            "feature_hash": self._hash_features(request.features) if request.features else "no_features"
        }

        key_string = json.dumps(key_components, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()

        return f"ml_prediction:{key_hash}"

    def _hash_features(self, features: Dict[str, Any]) -> str:
        """Generate hash of feature dictionary"""
        feature_string = json.dumps(features, sort_keys=True, default=str)
        return hashlib.md5(feature_string.encode()).hexdigest()[:8]

    def _update_metrics(self, result: MLPredictionResult):
        """Update performance metrics"""
        self.metrics["total_predictions"] += 1

        # Update confidence distribution
        confidence_level = result.confidence_level.value
        if confidence_level in self.metrics["confidence_distribution"]:
            self.metrics["confidence_distribution"][confidence_level] += 1

        # Update average inference time
        total_preds = self.metrics["total_predictions"]
        current_avg = self.metrics["avg_inference_time_ms"]
        new_time = result.processing_time_ms

        self.metrics["avg_inference_time_ms"] = (
            (current_avg * (total_preds - 1) + new_time) / total_preds
        )

    async def _publish_event(self, event_type: MLEventType, data: Dict[str, Any]):
        """Publish ML event to event streaming service"""
        try:
            event = StreamEvent(
                id=str(uuid.uuid4()),
                type=EventType.LEAD_SCORED,  # Map to existing event type
                timestamp=datetime.now().isoformat(),
                source_service="ml_analytics_engine",
                priority=Priority.MEDIUM,
                data={
                    "ml_event_type": event_type.value,
                    "tenant_id": self.tenant_id,
                    **data
                },
                correlation_id=data.get("lead_id", str(uuid.uuid4()))
            )

            # Publish if event service is available
            if hasattr(self.event_service, 'publish_event'):
                await self.event_service.publish_event("ml_analytics", event)

        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")

    async def get_model_performance(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        performance_data = {
            "engine_metrics": self.metrics.copy(),
            "models": {}
        }

        # Get metrics for all models or specific model
        models_to_check = [model_name] if model_name else list(self.models.keys())

        for name in models_to_check:
            if name in self.models:
                model_info = self.models[name].get_model_info()
                performance_data["models"][name] = {
                    "model_info": model_info,
                    "metadata": self.model_metadata.get(name, {})
                }

        # Calculate additional metrics
        total_requests = performance_data["engine_metrics"]["cache_hits"] + performance_data["engine_metrics"]["cache_misses"]
        if total_requests > 0:
            performance_data["engine_metrics"]["cache_hit_rate"] = (
                performance_data["engine_metrics"]["cache_hits"] / total_requests
            )
            performance_data["engine_metrics"]["escalation_rate"] = (
                performance_data["engine_metrics"]["escalations_to_claude"] / total_requests
            )

        return performance_data

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for ML Analytics Engine"""
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "performance": {}
        }

        try:
            # Check cache connection
            test_key = f"health_check_{int(time.time())}"
            await self.cache.set(test_key, {"test": True}, 10)
            cache_result = await self.cache.get(test_key)
            await self.cache.delete(test_key)

            health["components"]["cache"] = "healthy" if cache_result else "degraded"

            # Check models
            healthy_models = 0
            for name, model in self.models.items():
                try:
                    # Test prediction with dummy features
                    dummy_features = {"jorge_score": 3.5, "engagement_score": 0.7}
                    prediction, confidence = await model.predict(dummy_features)

                    if prediction is not None and 0.0 <= confidence <= 1.0:
                        healthy_models += 1
                        health["components"][f"model_{name}"] = "healthy"
                    else:
                        health["components"][f"model_{name}"] = "degraded"
                        health["status"] = "degraded"

                except Exception as e:
                    health["components"][f"model_{name}"] = f"failed: {str(e)}"
                    health["status"] = "degraded"

            # Performance indicators
            health["performance"] = {
                "avg_inference_time_ms": self.metrics["avg_inference_time_ms"],
                "total_predictions": self.metrics["total_predictions"],
                "cache_hit_rate": (
                    self.metrics["cache_hits"] / max(1, self.metrics["cache_hits"] + self.metrics["cache_misses"])
                ),
                "error_rate": self.metrics["error_count"] / max(1, self.metrics["total_predictions"]),
                "healthy_models": healthy_models,
                "total_models": len(self.models)
            }

            # Overall health determination
            if healthy_models == 0:
                health["status"] = "unhealthy"
            elif health["performance"]["avg_inference_time_ms"] > 100:  # > 100ms is concerning
                health["status"] = "degraded"
            elif health["performance"]["error_rate"] > 0.05:  # > 5% error rate
                health["status"] = "degraded"

        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)

        return health


# Factory functions and global instances
_ml_engine_instance: Optional[MLAnalyticsEngine] = None

def get_ml_analytics_engine(tenant_id: Optional[str] = None) -> MLAnalyticsEngine:
    """Get singleton ML Analytics Engine instance"""
    global _ml_engine_instance
    if _ml_engine_instance is None:
        _ml_engine_instance = MLAnalyticsEngine(tenant_id=tenant_id)
    return _ml_engine_instance

async def create_ml_prediction_request(
    lead_id: str,
    tenant_id: Optional[str] = None,
    features: Optional[Dict[str, Any]] = None,
    model_name: str = "default_lead_scorer"
) -> MLPredictionRequest:
    """Factory function for creating ML prediction requests"""
    return MLPredictionRequest(
        lead_id=lead_id,
        tenant_id=tenant_id,
        features=features,
        model_name=model_name,
        include_confidence=True,
        include_feature_importance=False,
        cache_ttl=300  # 5 minutes
    )


# Integration point for lead_analyzer.py line 234
async def integrate_ml_claude_escalation(
    lead_id: str,
    ml_result: MLPredictionResult,
    claude_orchestrator_instance: Any
) -> Dict[str, Any]:
    """
    Integration point for ML → Claude escalation pipeline
    Called from lead_analyzer.py line 234 when ML confidence < threshold
    """
    try:
        if ml_result.confidence_level == ConfidenceLevel.LOW or ml_result.escalated_to_claude:

            # Prepare context for Claude analysis
            claude_context = {
                "ml_prediction": {
                    "prediction": ml_result.prediction,
                    "confidence": ml_result.confidence,
                    "model_name": ml_result.model_name,
                    "processing_time_ms": ml_result.processing_time_ms,
                    "feature_importance": ml_result.feature_importance
                },
                "escalation_reason": "ml_low_confidence",
                "confidence_threshold": 0.85
            }

            # Call Claude for enhanced analysis
            from ghl_real_estate_ai.services.claude_orchestrator import ClaudeRequest, ClaudeTaskType

            claude_request = ClaudeRequest(
                task_type=ClaudeTaskType.LEAD_ANALYSIS,
                context=claude_context,
                prompt=f"""Analyze this lead where ML prediction has low confidence ({ml_result.confidence:.3f}).

                ML predicted: {ml_result.prediction}
                Lead ID: {lead_id}

                Provide strategic analysis considering why ML confidence might be low and recommend next steps.""",
                max_tokens=3000
            )

            claude_response = await claude_orchestrator_instance.process_request(claude_request)

            return {
                "escalation_successful": True,
                "ml_result": ml_result.to_dict(),
                "claude_analysis": claude_response.content,
                "combined_recommendation": claude_response.content,
                "escalation_timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"ML → Claude escalation failed for lead {lead_id}: {e}")

    # Fallback response
    return {
        "escalation_successful": False,
        "ml_result": ml_result.to_dict(),
        "error": "Escalation failed, using ML prediction only",
        "escalation_timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Example usage and testing
    async def main():
        print("🤖 Jorge Real Estate AI - ML Analytics Engine")
        print("=" * 60)

        # Initialize engine
        engine = get_ml_analytics_engine(tenant_id="demo_tenant")

        # Wait for model initialization
        await asyncio.sleep(1)

        # Test prediction
        test_request = await create_ml_prediction_request(
            lead_id="test_lead_123",
            tenant_id="demo_tenant",
            features={
                "jorge_score": 4.5,
                "engagement_score": 0.8,
                "message_count": 7,
                "response_time_avg": 15.0,
                "timeline_urgency": 0.9
            }
        )

        # Make prediction
        result = await engine.predict_lead_score(test_request)

        print(f"Prediction Result:")
        print(f"  Lead ID: {result.lead_id}")
        print(f"  Prediction: {result.prediction}")
        print(f"  Confidence: {result.confidence:.3f}")
        print(f"  Confidence Level: {result.confidence_level.value}")
        print(f"  Processing Time: {result.processing_time_ms:.2f}ms")
        print(f"  Cache Hit: {result.cache_hit}")
        print(f"  Escalated to Claude: {result.escalated_to_claude}")

        # Health check
        health = await engine.health_check()
        print(f"\nHealth Status: {health['status']}")
        print(f"Average Inference Time: {health['performance']['avg_inference_time_ms']:.2f}ms")

        # Performance metrics
        performance = await engine.get_model_performance()
        print(f"Total Predictions: {performance['engine_metrics']['total_predictions']}")
        print(f"Cache Hit Rate: {performance['engine_metrics'].get('cache_hit_rate', 0):.2%}")


    # Run if executed directly
    asyncio.run(main())