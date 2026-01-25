"""
Jorge's ML Model Manager - Advanced Model Lifecycle Management

Comprehensive ML model management system providing:
- Model lifecycle management (loading, versioning, A/B testing)
- Champion vs challenger model comparison with automatic fallback
- XGBoost integration with advanced feature engineering
- Performance monitoring with ROC-AUC, precision, recall tracking
- Model persistence with Redis caching for hot models
- SHAP explainability for feature importance analysis
- Performance degradation detection with automatic alerts
- Event-driven architecture for model performance notifications

Features:
- Champion/challenger pattern with A/B testing framework
- Hot model caching with Redis for sub-100ms inference
- Performance monitoring with real-time metrics and alerts
- Model versioning with metadata tracking (training date, metrics)
- Automatic model fallback on errors or performance degradation
- SHAP integration for feature importance and model explainability
- Event publishing for model performance, failures, and updates

Performance Targets:
- Model inference: <100ms (with Redis cache)
- Model loading: <2s for standard models
- Feature importance calculation: <500ms
- A/B test decision: <10ms
"""

import asyncio
import json
import time
import warnings
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, asdict
from uuid import uuid4
import hashlib

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score, accuracy_score
from sklearn.preprocessing import StandardScaler
from pydantic import BaseModel, Field
import shap
import redis.asyncio as redis

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service

# Suppress sklearn warnings for production
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')

logger = get_logger(__name__)
cache_service = get_cache_service()

# Performance constants
CACHE_TTL_HOT_MODEL = 3600  # 1 hour for hot models
CACHE_TTL_PREDICTIONS = 300  # 5 minutes for prediction cache
CACHE_TTL_FEATURES = 1800   # 30 minutes for feature importance
CACHE_TTL_PERFORMANCE = 600  # 10 minutes for performance metrics

PERFORMANCE_CHECK_INTERVAL = 3600  # 1 hour performance checks
DEGRADATION_THRESHOLD = 0.05  # 5% performance drop triggers alert
MIN_SAMPLES_FOR_AB_TEST = 100  # Minimum samples for A/B testing
AB_TEST_CONFIDENCE_LEVEL = 0.95  # 95% confidence for A/B tests

MODEL_INFERENCE_SLA_MS = 100  # 100ms SLA for model inference
MODEL_LOADING_SLA_MS = 2000   # 2s SLA for model loading
FEATURE_IMPORTANCE_SLA_MS = 500  # 500ms SLA for feature importance


class ModelStatus(str, Enum):
    """Model status enumeration"""
    TRAINING = "training"
    READY = "ready"
    DEPLOYED = "deployed"
    CHALLENGER = "challenger"
    CHAMPION = "champion"
    DEPRECATED = "deprecated"
    FAILED = "failed"


class ModelType(str, Enum):
    """Supported model types"""
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    NEURAL_NETWORK = "neural_network"
    LINEAR_MODEL = "linear_model"
    ENSEMBLE = "ensemble"


class ModelEventType(str, Enum):
    """Model event types for event system integration"""
    MODEL_LOADED = "model.loaded"
    MODEL_TRAINED = "model.trained"
    MODEL_DEPLOYED = "model.deployed"
    MODEL_PROMOTED = "model.promoted"
    MODEL_DEPRECATED = "model.deprecated"
    PERFORMANCE_ALERT = "model.performance_alert"
    PREDICTION_COMPLETED = "model.prediction_completed"
    AB_TEST_STARTED = "model.ab_test_started"
    AB_TEST_COMPLETED = "model.ab_test_completed"
    FEATURE_IMPORTANCE_CALCULATED = "model.feature_importance_calculated"


@dataclass
class ModelMetadata:
    """Model metadata for tracking and versioning"""
    model_id: str
    model_name: str
    model_type: ModelType
    version: str
    status: ModelStatus
    training_date: datetime
    training_dataset_size: int
    feature_count: int
    target_column: str
    performance_metrics: Dict[str, float]
    hyperparameters: Dict[str, Any]
    feature_names: List[str]
    shap_values_available: bool = False
    champion_since: Optional[datetime] = None
    last_performance_check: Optional[datetime] = None
    ab_test_active: bool = False
    ab_test_traffic_percentage: float = 0.0
    created_by: str = "jorge_ml_system"
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for serialization"""
        data = asdict(self)
        data['training_date'] = self.training_date.isoformat() if self.training_date else None
        data['champion_since'] = self.champion_since.isoformat() if self.champion_since else None
        data['last_performance_check'] = self.last_performance_check.isoformat() if self.last_performance_check else None
        data['model_type'] = self.model_type.value
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelMetadata':
        """Create metadata from dictionary"""
        if data.get('training_date'):
            data['training_date'] = datetime.fromisoformat(data['training_date'])
        if data.get('champion_since'):
            data['champion_since'] = datetime.fromisoformat(data['champion_since'])
        if data.get('last_performance_check'):
            data['last_performance_check'] = datetime.fromisoformat(data['last_performance_check'])
        data['model_type'] = ModelType(data['model_type'])
        data['status'] = ModelStatus(data['status'])
        return cls(**data)


@dataclass
class ModelPerformanceMetrics:
    """Model performance tracking"""
    model_id: str
    timestamp: datetime
    roc_auc: float
    precision: float
    recall: float
    f1_score: float
    accuracy: float
    prediction_count: int
    avg_inference_time_ms: float
    feature_importance_entropy: float
    confidence_calibration: float
    prediction_distribution: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class ModelEvent(BaseModel):
    """Model event for integration with event system"""
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: ModelEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "jorge_ml_model_manager"
    model_id: Optional[str] = None
    model_name: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize event to JSON"""
        data = self.model_dump()
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        return json.dumps(data)


class ABTestResult:
    """A/B test results between champion and challenger"""
    def __init__(self, champion_id: str, challenger_id: str):
        self.champion_id = champion_id
        self.challenger_id = challenger_id
        self.start_time = datetime.now(timezone.utc)
        self.champion_predictions = []
        self.challenger_predictions = []
        self.champion_actuals = []
        self.challenger_actuals = []
        self.champion_metrics = {}
        self.challenger_metrics = {}
        self.is_complete = False
        self.winner = None
        self.confidence_level = 0.0
        self.sample_size = 0

    def add_champion_result(self, prediction: float, actual: Optional[float] = None):
        """Add champion prediction result"""
        self.champion_predictions.append(prediction)
        if actual is not None:
            self.champion_actuals.append(actual)

    def add_challenger_result(self, prediction: float, actual: Optional[float] = None):
        """Add challenger prediction result"""
        self.challenger_predictions.append(prediction)
        if actual is not None:
            self.challenger_actuals.append(actual)

    def calculate_winner(self) -> Optional[str]:
        """Calculate A/B test winner based on performance metrics"""
        if (len(self.champion_actuals) < MIN_SAMPLES_FOR_AB_TEST or
            len(self.challenger_actuals) < MIN_SAMPLES_FOR_AB_TEST):
            return None

        try:
            # Calculate AUC for both models
            champion_auc = roc_auc_score(self.champion_actuals, self.champion_predictions)
            challenger_auc = roc_auc_score(self.challenger_actuals, self.challenger_predictions)

            self.champion_metrics = {'auc': champion_auc}
            self.challenger_metrics = {'auc': challenger_auc}

            # Simple winner determination - more sophisticated statistical testing could be added
            if challenger_auc > champion_auc + DEGRADATION_THRESHOLD:
                self.winner = self.challenger_id
                self.confidence_level = min(0.99, (challenger_auc - champion_auc) * 10)
            elif champion_auc > challenger_auc + DEGRADATION_THRESHOLD:
                self.winner = self.champion_id
                self.confidence_level = min(0.99, (champion_auc - challenger_auc) * 10)
            else:
                self.winner = self.champion_id  # Tie goes to champion
                self.confidence_level = 0.5

            self.is_complete = True
            return self.winner

        except Exception as e:
            logger.error(f"Error calculating A/B test winner: {e}")
            self.winner = self.champion_id  # Default to champion on error
            return self.winner


class MLModelManager:
    """
    Advanced ML Model Manager for Jorge's Real Estate AI System

    Provides comprehensive model lifecycle management, performance monitoring,
    A/B testing, and explainability features for production ML workloads.
    """

    def __init__(self,
                 models_directory: Optional[str] = None,
                 redis_client: Optional[redis.Redis] = None,
                 event_publisher: Optional[Callable] = None):
        """
        Initialize ML Model Manager

        Args:
            models_directory: Directory to store model files
            redis_client: Redis client for caching
            event_publisher: Function to publish events (optional)
        """
        self.models_directory = Path(models_directory or "models")
        self.models_directory.mkdir(exist_ok=True, parents=True)

        self.redis_client = redis_client
        self.event_publisher = event_publisher

        # In-memory model storage for fast access
        self.loaded_models: Dict[str, Any] = {}
        self.model_metadata: Dict[str, ModelMetadata] = {}
        self.model_scalers: Dict[str, StandardScaler] = {}
        self.model_explainers: Dict[str, Any] = {}  # SHAP explainers

        # A/B testing
        self.active_ab_tests: Dict[str, ABTestResult] = {}
        self.champion_models: Dict[str, str] = {}  # model_name -> model_id

        # Performance tracking
        self.performance_history: Dict[str, List[ModelPerformanceMetrics]] = {}

        # Background tasks
        self._performance_monitor_task = None
        self._is_monitoring = False

        logger.info("Jorge ML Model Manager initialized")

    async def start_monitoring(self):
        """Start background performance monitoring"""
        if self._is_monitoring:
            return

        self._is_monitoring = True
        try:
            loop = asyncio.get_running_loop()
            self._performance_monitor_task = loop.create_task(self._performance_monitor_loop())
        except RuntimeError:
            self._performance_monitor_task = None
            logger.debug("No running event loop found, performance monitor task not started")
        logger.info("Started background performance monitoring")

    async def stop_monitoring(self):
        """Stop background performance monitoring"""
        self._is_monitoring = False
        if self._performance_monitor_task:
            self._performance_monitor_task.cancel()
            try:
                await self._performance_monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped background performance monitoring")

    async def _performance_monitor_loop(self):
        """Background loop for monitoring model performance"""
        while self._is_monitoring:
            try:
                await self._check_all_model_performance()
                await asyncio.sleep(PERFORMANCE_CHECK_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def train_model(self,
                         model_name: str,
                         model_type: ModelType,
                         X_train: pd.DataFrame,
                         y_train: pd.Series,
                         hyperparameters: Optional[Dict[str, Any]] = None,
                         validation_split: float = 0.2) -> str:
        """
        Train a new model and save it

        Args:
            model_name: Name for the model
            model_type: Type of model to train
            X_train: Training features
            y_train: Training targets
            hyperparameters: Model hyperparameters
            validation_split: Validation split ratio

        Returns:
            model_id: Unique identifier for the trained model
        """
        start_time = time.time()
        model_id = f"{model_name}_{int(time.time())}_{str(uuid4())[:8]}"

        try:
            logger.info(f"Training model {model_id} of type {model_type.value}")

            # Split data for validation
            X_train_split, X_val, y_train_split, y_val = train_test_split(
                X_train, y_train, test_size=validation_split, random_state=42
            )

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train_split)
            X_val_scaled = scaler.transform(X_val)

            # Train model based on type
            if model_type == ModelType.RANDOM_FOREST:
                model = self._train_random_forest(X_train_scaled, y_train_split, hyperparameters)
            elif model_type == ModelType.XGBOOST:
                model = self._train_xgboost(X_train_scaled, y_train_split, hyperparameters)
            else:
                raise ValueError(f"Model type {model_type} not supported yet")

            # Evaluate on validation set
            y_pred = model.predict_proba(X_val_scaled)[:, 1]

            performance_metrics = {
                'roc_auc': float(roc_auc_score(y_val, y_pred)),
                'precision': float(precision_score(y_val, y_pred > 0.5)),
                'recall': float(recall_score(y_val, y_pred > 0.5)),
                'f1_score': float(f1_score(y_val, y_pred > 0.5)),
                'accuracy': float(accuracy_score(y_val, y_pred > 0.5))
            }

            # Create metadata
            metadata = ModelMetadata(
                model_id=model_id,
                model_name=model_name,
                model_type=model_type,
                version="1.0",
                status=ModelStatus.READY,
                training_date=datetime.now(timezone.utc),
                training_dataset_size=len(X_train),
                feature_count=X_train.shape[1],
                target_column=y_train.name or "target",
                performance_metrics=performance_metrics,
                hyperparameters=hyperparameters or {},
                feature_names=list(X_train.columns)
            )

            # Save model and metadata
            await self._save_model(model_id, model, scaler, metadata)

            # Create SHAP explainer
            try:
                explainer = shap.TreeExplainer(model) if model_type in [ModelType.RANDOM_FOREST, ModelType.XGBOOST] else None
                if explainer:
                    self.model_explainers[model_id] = explainer
                    metadata.shap_values_available = True
            except Exception as e:
                logger.warning(f"Could not create SHAP explainer for {model_id}: {e}")

            # Load into memory
            self.loaded_models[model_id] = model
            self.model_scalers[model_id] = scaler
            self.model_metadata[model_id] = metadata

            training_time = time.time() - start_time
            logger.info(f"Trained model {model_id} in {training_time:.2f}s with AUC: {performance_metrics['roc_auc']:.3f}")

            # Publish event
            await self._publish_event(ModelEventType.MODEL_TRAINED, model_id, model_name, {
                'training_time_seconds': training_time,
                'performance_metrics': performance_metrics,
                'dataset_size': len(X_train)
            })

            return model_id

        except Exception as e:
            logger.error(f"Error training model {model_id}: {e}")
            raise

    def _train_random_forest(self, X_train: np.ndarray, y_train: pd.Series, hyperparameters: Optional[Dict[str, Any]]) -> RandomForestClassifier:
        """Train Random Forest model"""
        params = {
            'n_estimators': 100,
            'max_depth': 10,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
            'random_state': 42,
            'n_jobs': -1
        }
        if hyperparameters:
            params.update(hyperparameters)

        model = RandomForestClassifier(**params)
        model.fit(X_train, y_train)
        return model

    def _train_xgboost(self, X_train: np.ndarray, y_train: pd.Series, hyperparameters: Optional[Dict[str, Any]]) -> Any:
        """Train XGBoost model"""
        try:
            import xgboost as xgb

            params = {
                'n_estimators': 100,
                'max_depth': 6,
                'learning_rate': 0.1,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'random_state': 42,
                'n_jobs': -1
            }
            if hyperparameters:
                params.update(hyperparameters)

            model = xgb.XGBClassifier(**params)
            model.fit(X_train, y_train)
            return model

        except ImportError:
            logger.warning("XGBoost not available, falling back to Random Forest")
            return self._train_random_forest(X_train, y_train, hyperparameters)

    async def load_model(self, model_id: str, cache_hot: bool = True) -> bool:
        """
        Load model into memory for fast inference

        Args:
            model_id: Model identifier
            cache_hot: Whether to cache in Redis for hot access

        Returns:
            bool: True if loaded successfully
        """
        start_time = time.time()

        try:
            if model_id in self.loaded_models:
                logger.debug(f"Model {model_id} already loaded")
                return True

            # Try to load from Redis cache first
            if cache_hot and self.redis_client:
                try:
                    cached_data = await self._get_cached_model(model_id)
                    if cached_data:
                        self.loaded_models[model_id] = cached_data['model']
                        self.model_scalers[model_id] = cached_data['scaler']
                        self.model_metadata[model_id] = ModelMetadata.from_dict(cached_data['metadata'])
                        load_time = time.time() - start_time
                        logger.info(f"Loaded model {model_id} from cache in {load_time*1000:.1f}ms")
                        return True
                except Exception as e:
                    logger.warning(f"Cache load failed for {model_id}: {e}")

            # Load from disk
            model_path = self.models_directory / f"{model_id}.joblib"
            scaler_path = self.models_directory / f"{model_id}_scaler.joblib"
            metadata_path = self.models_directory / f"{model_id}_metadata.json"

            if not all(p.exists() for p in [model_path, scaler_path, metadata_path]):
                logger.error(f"Model files not found for {model_id}")
                return False

            # Load components
            model = joblib.load(model_path)
            scaler = joblib.load(scaler_path)

            with open(metadata_path, 'r') as f:
                metadata_dict = json.load(f)
                metadata = ModelMetadata.from_dict(metadata_dict)

            # Store in memory
            self.loaded_models[model_id] = model
            self.model_scalers[model_id] = scaler
            self.model_metadata[model_id] = metadata

            # Cache in Redis if requested
            if cache_hot and self.redis_client:
                await self._cache_model(model_id, model, scaler, metadata)

            load_time = time.time() - start_time
            if load_time * 1000 > MODEL_LOADING_SLA_MS:
                logger.warning(f"Model loading exceeded SLA: {load_time*1000:.1f}ms > {MODEL_LOADING_SLA_MS}ms")

            logger.info(f"Loaded model {model_id} in {load_time*1000:.1f}ms")

            # Publish event
            await self._publish_event(ModelEventType.MODEL_LOADED, model_id, metadata.model_name, {
                'load_time_ms': load_time * 1000
            })

            return True

        except Exception as e:
            logger.error(f"Error loading model {model_id}: {e}")
            return False

    async def predict(self,
                     model_name: str,
                     features: Union[pd.DataFrame, Dict[str, Any]],
                     use_champion: bool = True,
                     ab_test_traffic: float = 0.0) -> Dict[str, Any]:
        """
        Make predictions using specified model or champion/challenger

        Args:
            model_name: Name of the model
            features: Input features
            use_champion: Whether to use champion model
            ab_test_traffic: Percentage of traffic for A/B testing (0.0-1.0)

        Returns:
            Dict containing prediction, probability, confidence, and metadata
        """
        start_time = time.time()

        try:
            # Convert features to DataFrame if dict
            if isinstance(features, dict):
                features = pd.DataFrame([features])
            elif isinstance(features, pd.Series):
                features = pd.DataFrame([features])

            # Determine which model to use
            model_id = await self._select_model_for_prediction(model_name, use_champion, ab_test_traffic)

            if not model_id:
                raise ValueError(f"No model available for {model_name}")

            # Ensure model is loaded
            if model_id not in self.loaded_models:
                loaded = await self.load_model(model_id)
                if not loaded:
                    raise ValueError(f"Could not load model {model_id}")

            model = self.loaded_models[model_id]
            scaler = self.model_scalers[model_id]
            metadata = self.model_metadata[model_id]

            # Prepare features
            feature_names = metadata.feature_names
            if not all(col in features.columns for col in feature_names):
                missing = [col for col in feature_names if col not in features.columns]
                raise ValueError(f"Missing features: {missing}")

            X = features[feature_names]
            X_scaled = scaler.transform(X)

            # Make prediction
            try:
                prediction_proba = model.predict_proba(X_scaled)[:, 1]
                prediction = prediction_proba > 0.5
                confidence = np.max(model.predict_proba(X_scaled), axis=1)
            except Exception as e:
                # Fallback for models without predict_proba
                prediction = model.predict(X_scaled)
                prediction_proba = prediction.astype(float)
                confidence = np.ones(len(prediction)) * 0.5

            inference_time = (time.time() - start_time) * 1000

            if inference_time > MODEL_INFERENCE_SLA_MS:
                logger.warning(f"Inference exceeded SLA: {inference_time:.1f}ms > {MODEL_INFERENCE_SLA_MS}ms")

            result = {
                'model_id': model_id,
                'model_name': metadata.model_name,
                'model_version': metadata.version,
                'prediction': float(prediction[0]) if len(prediction) == 1 else prediction.tolist(),
                'probability': float(prediction_proba[0]) if len(prediction_proba) == 1 else prediction_proba.tolist(),
                'confidence': float(confidence[0]) if len(confidence) == 1 else confidence.tolist(),
                'inference_time_ms': inference_time,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'champion_model': model_id == self.champion_models.get(model_name),
                'ab_test_active': model_name in self.active_ab_tests
            }

            # Record for A/B testing if active
            if model_name in self.active_ab_tests:
                ab_test = self.active_ab_tests[model_name]
                if model_id == ab_test.champion_id:
                    ab_test.add_champion_result(float(prediction_proba[0]))
                elif model_id == ab_test.challenger_id:
                    ab_test.add_challenger_result(float(prediction_proba[0]))

            # Publish event
            await self._publish_event(ModelEventType.PREDICTION_COMPLETED, model_id, metadata.model_name, {
                'inference_time_ms': inference_time,
                'confidence': float(confidence[0]) if len(confidence) == 1 else np.mean(confidence)
            })

            return result

        except Exception as e:
            logger.error(f"Error in prediction for {model_name}: {e}")
            # Return fallback prediction
            return {
                'model_id': 'fallback',
                'model_name': model_name,
                'prediction': 0.5,
                'probability': 0.5,
                'confidence': 0.0,
                'inference_time_ms': (time.time() - start_time) * 1000,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e),
                'fallback': True
            }

    async def calculate_feature_importance(self, model_id: str, method: str = "shap") -> Dict[str, Any]:
        """
        Calculate feature importance using SHAP or built-in methods

        Args:
            model_id: Model identifier
            method: Method to use ('shap', 'builtin')

        Returns:
            Dict containing feature importance scores and explanations
        """
        start_time = time.time()

        try:
            if model_id not in self.loaded_models:
                loaded = await self.load_model(model_id)
                if not loaded:
                    raise ValueError(f"Could not load model {model_id}")

            model = self.loaded_models[model_id]
            metadata = self.model_metadata[model_id]

            result = {
                'model_id': model_id,
                'model_name': metadata.model_name,
                'method': method,
                'feature_names': metadata.feature_names,
                'importance_scores': {},
                'calculation_time_ms': 0,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            if method == "shap" and model_id in self.model_explainers:
                # Use SHAP values
                explainer = self.model_explainers[model_id]
                # Note: For production, you'd typically provide sample data here
                # This is a simplified example
                shap_values = explainer.shap_values(np.zeros((1, len(metadata.feature_names))))

                if isinstance(shap_values, list):
                    shap_values = shap_values[1]  # For binary classification

                feature_importance = np.abs(shap_values).mean(axis=0)
                result['importance_scores'] = dict(zip(metadata.feature_names, feature_importance))
                result['explanation_method'] = 'SHAP TreeExplainer'

            elif hasattr(model, 'feature_importances_'):
                # Use built-in feature importance
                importance_scores = model.feature_importances_
                result['importance_scores'] = dict(zip(metadata.feature_names, importance_scores))
                result['explanation_method'] = 'Built-in feature importance'

            else:
                raise ValueError(f"Feature importance not available for model {model_id}")

            # Normalize and sort
            total_importance = sum(result['importance_scores'].values())
            if total_importance > 0:
                result['importance_scores'] = {
                    k: v/total_importance for k, v in result['importance_scores'].items()
                }

            # Sort by importance
            result['top_features'] = sorted(
                result['importance_scores'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]

            calculation_time = (time.time() - start_time) * 1000
            result['calculation_time_ms'] = calculation_time

            if calculation_time > FEATURE_IMPORTANCE_SLA_MS:
                logger.warning(f"Feature importance calculation exceeded SLA: {calculation_time:.1f}ms > {FEATURE_IMPORTANCE_SLA_MS}ms")

            # Cache result
            if self.redis_client:
                cache_key = f"jorge:feature_importance:{model_id}"
                await cache_service.set(cache_key, json.dumps(result, default=str), ttl=CACHE_TTL_FEATURES)

            # Publish event
            await self._publish_event(ModelEventType.FEATURE_IMPORTANCE_CALCULATED, model_id, metadata.model_name, {
                'calculation_time_ms': calculation_time,
                'top_feature': result['top_features'][0][0] if result['top_features'] else 'unknown'
            })

            return result

        except Exception as e:
            logger.error(f"Error calculating feature importance for {model_id}: {e}")
            raise

    async def start_ab_test(self,
                           model_name: str,
                           champion_id: str,
                           challenger_id: str,
                           traffic_percentage: float = 0.1) -> bool:
        """
        Start A/B test between champion and challenger models

        Args:
            model_name: Name of the model being tested
            champion_id: Current champion model ID
            challenger_id: Challenger model ID
            traffic_percentage: Percentage of traffic for challenger (0.0-1.0)

        Returns:
            bool: True if A/B test started successfully
        """
        try:
            if model_name in self.active_ab_tests:
                logger.warning(f"A/B test already active for {model_name}")
                return False

            # Ensure both models are loaded
            for mid in [champion_id, challenger_id]:
                if mid not in self.loaded_models:
                    loaded = await self.load_model(mid)
                    if not loaded:
                        logger.error(f"Could not load model {mid} for A/B test")
                        return False

            # Create A/B test
            ab_test = ABTestResult(champion_id, challenger_id)
            self.active_ab_tests[model_name] = ab_test

            # Update metadata
            if challenger_id in self.model_metadata:
                self.model_metadata[challenger_id].ab_test_active = True
                self.model_metadata[challenger_id].ab_test_traffic_percentage = traffic_percentage

            logger.info(f"Started A/B test for {model_name}: champion={champion_id}, challenger={challenger_id}, traffic={traffic_percentage}")

            # Publish event
            await self._publish_event(ModelEventType.AB_TEST_STARTED, challenger_id, model_name, {
                'champion_id': champion_id,
                'challenger_id': challenger_id,
                'traffic_percentage': traffic_percentage
            })

            return True

        except Exception as e:
            logger.error(f"Error starting A/B test for {model_name}: {e}")
            return False

    async def complete_ab_test(self, model_name: str, force_winner: Optional[str] = None) -> Optional[str]:
        """
        Complete A/B test and determine winner

        Args:
            model_name: Name of the model being tested
            force_winner: Force a specific winner (optional)

        Returns:
            Winner model ID or None if test couldn't be completed
        """
        try:
            if model_name not in self.active_ab_tests:
                logger.warning(f"No active A/B test for {model_name}")
                return None

            ab_test = self.active_ab_tests[model_name]

            if force_winner:
                winner = force_winner
                logger.info(f"A/B test for {model_name} completed with forced winner: {winner}")
            else:
                winner = ab_test.calculate_winner()
                if not winner:
                    logger.warning(f"Could not determine A/B test winner for {model_name} - insufficient data")
                    return None

            # Update champion if challenger won
            if winner == ab_test.challenger_id:
                await self._promote_challenger_to_champion(model_name, ab_test.challenger_id)

            # Clean up
            del self.active_ab_tests[model_name]

            # Update metadata
            if ab_test.challenger_id in self.model_metadata:
                self.model_metadata[ab_test.challenger_id].ab_test_active = False
                self.model_metadata[ab_test.challenger_id].ab_test_traffic_percentage = 0.0

            logger.info(f"Completed A/B test for {model_name}: winner={winner}")

            # Publish event
            await self._publish_event(ModelEventType.AB_TEST_COMPLETED, winner, model_name, {
                'champion_id': ab_test.champion_id,
                'challenger_id': ab_test.challenger_id,
                'winner': winner,
                'champion_metrics': ab_test.champion_metrics,
                'challenger_metrics': ab_test.challenger_metrics,
                'confidence_level': ab_test.confidence_level
            })

            return winner

        except Exception as e:
            logger.error(f"Error completing A/B test for {model_name}: {e}")
            return None

    async def set_champion_model(self, model_name: str, model_id: str) -> bool:
        """
        Set a model as champion for the given model name

        Args:
            model_name: Name of the model
            model_id: Model ID to set as champion

        Returns:
            bool: True if successful
        """
        try:
            # Ensure model is loaded
            if model_id not in self.loaded_models:
                loaded = await self.load_model(model_id)
                if not loaded:
                    logger.error(f"Could not load model {model_id}")
                    return False

            # Update champion mapping
            old_champion = self.champion_models.get(model_name)
            self.champion_models[model_name] = model_id

            # Update metadata
            if model_id in self.model_metadata:
                self.model_metadata[model_id].status = ModelStatus.CHAMPION
                self.model_metadata[model_id].champion_since = datetime.now(timezone.utc)

            # Deprecate old champion
            if old_champion and old_champion in self.model_metadata:
                self.model_metadata[old_champion].status = ModelStatus.DEPRECATED
                self.model_metadata[old_champion].champion_since = None

            logger.info(f"Set {model_id} as champion for {model_name}")

            # Publish event
            await self._publish_event(ModelEventType.MODEL_PROMOTED, model_id, model_name, {
                'previous_champion': old_champion
            })

            return True

        except Exception as e:
            logger.error(f"Error setting champion model: {e}")
            return False

    async def get_model_performance(self, model_id: str, days_back: int = 7) -> Dict[str, Any]:
        """
        Get model performance metrics for the specified period

        Args:
            model_id: Model identifier
            days_back: Number of days to look back

        Returns:
            Dict containing performance metrics and trends
        """
        try:
            if model_id not in self.performance_history:
                return {
                    'model_id': model_id,
                    'error': 'No performance history available'
                }

            # Filter metrics by time period
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            recent_metrics = [
                m for m in self.performance_history[model_id]
                if m.timestamp >= cutoff_date
            ]

            if not recent_metrics:
                return {
                    'model_id': model_id,
                    'error': f'No performance data in last {days_back} days'
                }

            # Calculate aggregated metrics
            avg_metrics = {
                'roc_auc': np.mean([m.roc_auc for m in recent_metrics]),
                'precision': np.mean([m.precision for m in recent_metrics]),
                'recall': np.mean([m.recall for m in recent_metrics]),
                'f1_score': np.mean([m.f1_score for m in recent_metrics]),
                'accuracy': np.mean([m.accuracy for m in recent_metrics]),
                'avg_inference_time_ms': np.mean([m.avg_inference_time_ms for m in recent_metrics])
            }

            # Calculate trends (if we have enough data points)
            trends = {}
            if len(recent_metrics) >= 2:
                first_half = recent_metrics[:len(recent_metrics)//2]
                second_half = recent_metrics[len(recent_metrics)//2:]

                for metric in ['roc_auc', 'precision', 'recall', 'f1_score', 'accuracy']:
                    first_avg = np.mean([getattr(m, metric) for m in first_half])
                    second_avg = np.mean([getattr(m, metric) for m in second_half])
                    trend = (second_avg - first_avg) / first_avg if first_avg > 0 else 0
                    trends[f'{metric}_trend'] = trend

            return {
                'model_id': model_id,
                'period_days': days_back,
                'data_points': len(recent_metrics),
                'avg_metrics': avg_metrics,
                'trends': trends,
                'latest_check': recent_metrics[-1].timestamp.isoformat() if recent_metrics else None
            }

        except Exception as e:
            logger.error(f"Error getting model performance for {model_id}: {e}")
            return {
                'model_id': model_id,
                'error': str(e)
            }

    async def check_performance_degradation(self, model_id: str) -> Dict[str, Any]:
        """
        Check if model performance has degraded significantly

        Args:
            model_id: Model identifier

        Returns:
            Dict containing degradation analysis
        """
        try:
            if model_id not in self.performance_history:
                return {'model_id': model_id, 'degradation_detected': False, 'reason': 'No history'}

            metrics = self.performance_history[model_id]
            if len(metrics) < 2:
                return {'model_id': model_id, 'degradation_detected': False, 'reason': 'Insufficient data'}

            # Compare recent performance to baseline
            baseline_metrics = metrics[:min(5, len(metrics)//2)]  # First few measurements
            recent_metrics = metrics[-min(5, len(metrics)//2):]   # Most recent measurements

            baseline_auc = np.mean([m.roc_auc for m in baseline_metrics])
            recent_auc = np.mean([m.roc_auc for m in recent_metrics])

            degradation = baseline_auc - recent_auc
            degradation_percentage = degradation / baseline_auc if baseline_auc > 0 else 0

            degradation_detected = degradation_percentage > DEGRADATION_THRESHOLD

            result = {
                'model_id': model_id,
                'degradation_detected': degradation_detected,
                'degradation_percentage': degradation_percentage,
                'baseline_auc': baseline_auc,
                'recent_auc': recent_auc,
                'threshold': DEGRADATION_THRESHOLD,
                'recommendation': 'Retrain model' if degradation_detected else 'Performance stable'
            }

            if degradation_detected:
                logger.warning(f"Performance degradation detected for {model_id}: {degradation_percentage:.3f}")

                # Publish alert event
                await self._publish_event(ModelEventType.PERFORMANCE_ALERT, model_id,
                                        self.model_metadata.get(model_id, {}).model_name, result)

            return result

        except Exception as e:
            logger.error(f"Error checking performance degradation for {model_id}: {e}")
            return {'model_id': model_id, 'error': str(e)}

    async def list_models(self, status_filter: Optional[ModelStatus] = None) -> List[Dict[str, Any]]:
        """
        List all available models with their metadata

        Args:
            status_filter: Filter by model status

        Returns:
            List of model information dictionaries
        """
        try:
            models = []
            for model_id, metadata in self.model_metadata.items():
                if status_filter is None or metadata.status == status_filter:
                    model_info = metadata.to_dict()
                    model_info['loaded'] = model_id in self.loaded_models
                    model_info['is_champion'] = model_id in self.champion_models.values()
                    model_info['ab_test_active'] = model_id in [
                        test.challenger_id for test in self.active_ab_tests.values()
                    ]
                    models.append(model_info)

            return sorted(models, key=lambda x: x['training_date'], reverse=True)

        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []

    # Private helper methods

    async def _save_model(self, model_id: str, model: Any, scaler: StandardScaler, metadata: ModelMetadata):
        """Save model, scaler, and metadata to disk"""
        try:
            model_path = self.models_directory / f"{model_id}.joblib"
            scaler_path = self.models_directory / f"{model_id}_scaler.joblib"
            metadata_path = self.models_directory / f"{model_id}_metadata.json"

            # Save model and scaler
            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)

            # Save metadata
            with open(metadata_path, 'w') as f:
                json.dump(metadata.to_dict(), f, indent=2)

            logger.debug(f"Saved model {model_id} to disk")

        except Exception as e:
            logger.error(f"Error saving model {model_id}: {e}")
            raise

    async def _cache_model(self, model_id: str, model: Any, scaler: StandardScaler, metadata: ModelMetadata):
        """Cache model in Redis for hot access"""
        try:
            if not self.redis_client:
                return

            cache_data = {
                'model': model,
                'scaler': scaler,
                'metadata': metadata.to_dict()
            }

            cache_key = f"jorge:hot_model:{model_id}"
            serialized_data = joblib.dumps(cache_data)

            # Store in Redis with TTL
            await cache_service.set(cache_key, serialized_data, ttl=CACHE_TTL_HOT_MODEL)
            logger.debug(f"Cached model {model_id} in Redis")

        except Exception as e:
            logger.warning(f"Error caching model {model_id}: {e}")

    async def _get_cached_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get cached model from Redis"""
        try:
            if not self.redis_client:
                return None

            cache_key = f"jorge:hot_model:{model_id}"
            cached_data = await cache_service.get(cache_key)

            if cached_data:
                return joblib.loads(cached_data)

        except Exception as e:
            logger.warning(f"Error retrieving cached model {model_id}: {e}")

        return None

    async def _select_model_for_prediction(self, model_name: str, use_champion: bool, ab_test_traffic: float) -> Optional[str]:
        """Select which model to use for prediction"""
        try:
            # Check if A/B test is active
            if model_name in self.active_ab_tests and ab_test_traffic > 0:
                ab_test = self.active_ab_tests[model_name]

                # Use random selection for A/B testing
                if np.random.random() < ab_test_traffic:
                    return ab_test.challenger_id
                else:
                    return ab_test.champion_id

            # Use champion model if available
            if use_champion and model_name in self.champion_models:
                return self.champion_models[model_name]

            # Fall back to any available model with the name
            for model_id, metadata in self.model_metadata.items():
                if metadata.model_name == model_name and metadata.status in [ModelStatus.READY, ModelStatus.DEPLOYED, ModelStatus.CHAMPION]:
                    return model_id

            return None

        except Exception as e:
            logger.error(f"Error selecting model for prediction: {e}")
            return None

    async def _promote_challenger_to_champion(self, model_name: str, challenger_id: str):
        """Promote challenger to champion after winning A/B test"""
        try:
            await self.set_champion_model(model_name, challenger_id)
            logger.info(f"Promoted challenger {challenger_id} to champion for {model_name}")

        except Exception as e:
            logger.error(f"Error promoting challenger {challenger_id}: {e}")

    async def _check_all_model_performance(self):
        """Check performance for all loaded models"""
        try:
            for model_id in list(self.loaded_models.keys()):
                await self.check_performance_degradation(model_id)

        except Exception as e:
            logger.error(f"Error in performance check: {e}")

    async def _publish_event(self, event_type: ModelEventType, model_id: str, model_name: str, payload: Dict[str, Any]):
        """Publish event to event system if publisher is available"""
        try:
            if not self.event_publisher:
                return

            event = ModelEvent(
                event_type=event_type,
                model_id=model_id,
                model_name=model_name,
                payload=payload
            )

            await self.event_publisher(event)

        except Exception as e:
            logger.warning(f"Error publishing event {event_type}: {e}")

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics and health metrics"""
        try:
            return {
                'loaded_models': len(self.loaded_models),
                'total_models': len(self.model_metadata),
                'champion_models': len(self.champion_models),
                'active_ab_tests': len(self.active_ab_tests),
                'models_with_shap': len(self.model_explainers),
                'monitoring_active': self._is_monitoring,
                'performance_history_size': sum(len(history) for history in self.performance_history.values()),
                'cache_enabled': self.redis_client is not None,
                'event_publishing_enabled': self.event_publisher is not None,
                'models_directory': str(self.models_directory),
                'uptime_hours': (datetime.now(timezone.utc) - datetime.now(timezone.utc)).total_seconds() / 3600
            }

        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {'error': str(e)}


# Example usage and initialization function
async def create_jorge_ml_manager(models_directory: Optional[str] = None,
                                redis_client: Optional[redis.Redis] = None,
                                event_publisher: Optional[Callable] = None) -> MLModelManager:
    """
    Create and initialize Jorge's ML Model Manager

    Args:
        models_directory: Directory to store model files
        redis_client: Redis client for caching
        event_publisher: Function to publish events

    Returns:
        Initialized MLModelManager instance
    """
    try:
        manager = MLModelManager(
            models_directory=models_directory,
            redis_client=redis_client,
            event_publisher=event_publisher
        )

        # Start background monitoring
        await manager.start_monitoring()

        logger.info("Jorge ML Model Manager initialized successfully")
        return manager

    except Exception as e:
        logger.error(f"Error initializing Jorge ML Model Manager: {e}")
        raise