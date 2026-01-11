"""
Real-Time Model Retraining and Continuous Learning System

This advanced service provides automatic model retraining, online learning capabilities,
performance monitoring, and adaptive optimization for all ML models in the lead
nurturing system. It ensures models continuously improve from real-world feedback.

Author: AI Assistant
Created: 2026-01-09
Version: 1.0.0
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
import threading
import pickle
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque
import statistics
import warnings
warnings.filterwarnings('ignore')

# Advanced ML imports
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import SGDClassifier, SGDRegressor, PassiveAggressiveClassifier
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    mean_squared_error, mean_absolute_error, r2_score
)
from sklearn.cluster import MiniBatchKMeans
import joblib
from pathlib import Path

# Online learning specific imports
from river import linear_model, ensemble, preprocessing, metrics, compose
from river.drift import ADWIN, PageHinkley
from scipy import stats
import xgboost as xgb

# Internal imports
from .enhanced_ml_personalization_engine import EnhancedMLPersonalizationEngine, LearningSignal
from .predictive_churn_prevention import PredictiveChurnPrevention
from services.claude_semantic_analyzer import ClaudeSemanticAnalyzer

logger = logging.getLogger(__name__)


# Real-time Learning Models

class ModelType(str, Enum):
    """Types of models in the system."""
    PERSONALIZATION = "personalization"
    CHURN_PREDICTION = "churn_prediction"
    ENGAGEMENT_SCORING = "engagement_scoring"
    TIMING_OPTIMIZATION = "timing_optimization"
    CHANNEL_SELECTION = "channel_selection"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    CONVERSION_PREDICTION = "conversion_prediction"
    BEHAVIORAL_CLUSTERING = "behavioral_clustering"


class LearningMode(str, Enum):
    """Different learning modes for model updates."""
    BATCH_RETRAIN = "batch_retrain"
    INCREMENTAL_UPDATE = "incremental_update"
    ONLINE_LEARNING = "online_learning"
    ENSEMBLE_UPDATE = "ensemble_update"
    DRIFT_ADAPTATION = "drift_adaptation"


class PerformanceMetric(str, Enum):
    """Performance metrics for model evaluation."""
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    ROC_AUC = "roc_auc"
    MSE = "mse"
    MAE = "mae"
    R2_SCORE = "r2_score"


class DriftStatus(str, Enum):
    """Data drift detection status."""
    STABLE = "stable"
    WARNING = "warning"
    DRIFT_DETECTED = "drift_detected"
    SEVERE_DRIFT = "severe_drift"


@dataclass
class TrainingDataPoint:
    """Single training data point with features and labels."""
    data_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    model_type: ModelType
    features: np.ndarray
    labels: Dict[str, Union[float, int, str]]
    metadata: Dict[str, Any]
    confidence_score: float
    data_quality: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ModelPerformanceSnapshot:
    """Performance snapshot for a model."""
    model_type: ModelType
    performance_metrics: Dict[PerformanceMetric, float]
    validation_score: float
    training_samples: int
    model_version: str
    drift_status: DriftStatus
    last_update: datetime
    improvement_trend: str  # "improving", "stable", "declining"


@dataclass
class RetrainingEvent:
    """Record of a model retraining event."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    model_type: ModelType
    learning_mode: LearningMode
    trigger_reason: str
    pre_training_performance: Dict[str, float]
    post_training_performance: Dict[str, float]
    training_samples_used: int
    training_duration: timedelta
    improvement_achieved: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class OnlineLearningState:
    """State tracking for online learning models."""
    model_type: ModelType
    samples_processed: int
    last_drift_check: datetime
    drift_detector: Any  # ADWIN or PageHinkley detector
    performance_buffer: deque  # Recent performance scores
    learning_rate: float
    adaptation_level: float


@dataclass
class ModelEnsembleConfig:
    """Configuration for model ensembles."""
    model_type: ModelType
    base_models: List[str]
    voting_strategy: str  # "hard", "soft", "weighted"
    weights: Optional[List[float]]
    update_strategy: str  # "all", "best", "rotating"
    ensemble_size: int


# Main Real-Time Training Service

class RealTimeModelTraining:
    """
    Real-Time Model Retraining and Continuous Learning Service

    Features:
    - Automatic model retraining based on performance degradation
    - Online learning for real-time adaptation
    - Concept drift detection and handling
    - Performance monitoring and alerting
    - A/B testing for model improvements
    - Ensemble model management
    """

    def __init__(self):
        """Initialize the real-time model training service."""
        self.enhanced_personalization = EnhancedMLPersonalizationEngine()
        self.churn_prevention = PredictiveChurnPrevention()
        self.semantic_analyzer = ClaudeSemanticAnalyzer()

        # Model storage and versioning
        self.models_dir = Path(__file__).parent.parent / "models" / "real_time_training"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.model_versions: Dict[ModelType, int] = defaultdict(int)

        # Training data management
        self.training_buffer: Dict[ModelType, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.validation_buffer: Dict[ModelType, deque] = defaultdict(lambda: deque(maxlen=2000))

        # Online learning models
        self.online_models: Dict[ModelType, Any] = {}
        self.online_learning_states: Dict[ModelType, OnlineLearningState] = {}

        # Performance monitoring
        self.performance_history: Dict[ModelType, List[ModelPerformanceSnapshot]] = defaultdict(list)
        self.retraining_events: List[RetrainingEvent] = []

        # Real-time processing
        self.processing_queue: asyncio.Queue = asyncio.Queue()
        self.is_processing = False
        self.training_lock = threading.RLock()

        # Configuration
        self.config = self._load_training_config()

        # Initialize online learning models
        self._initialize_online_models()

        # Start background processing
        self._start_background_processing()

        logger.info("Real-Time Model Training service initialized")

    def _load_training_config(self) -> Dict[str, Any]:
        """Load training configuration parameters."""
        return {
            "retraining_thresholds": {
                "performance_degradation": 0.05,  # 5% performance drop triggers retrain
                "sample_threshold": 500,           # Minimum samples for retrain
                "time_threshold": timedelta(hours=24),  # Maximum time between retrains
                "drift_threshold": 0.1             # Drift detection threshold
            },
            "online_learning": {
                "enabled": True,
                "learning_rate": 0.01,
                "batch_size": 50,
                "adaptation_rate": 0.1
            },
            "ensemble_config": {
                "enabled": True,
                "max_models": 5,
                "min_performance_gain": 0.02
            },
            "drift_detection": {
                "window_size": 1000,
                "delta": 0.002,
                "check_frequency": timedelta(minutes=30)
            }
        }

    def _initialize_online_models(self):
        """Initialize online learning models for real-time adaptation."""
        try:
            # River-based online learning models
            for model_type in ModelType:
                if model_type in [ModelType.CHURN_PREDICTION, ModelType.ENGAGEMENT_SCORING]:
                    # Classification models
                    online_model = compose.Pipeline(
                        preprocessing.StandardScaler(),
                        linear_model.LogisticRegression(l2=0.1)
                    )
                elif model_type in [ModelType.TIMING_OPTIMIZATION, ModelType.CONVERSION_PREDICTION]:
                    # Regression models
                    online_model = compose.Pipeline(
                        preprocessing.StandardScaler(),
                        linear_model.LinearRegression(l2=0.1)
                    )
                else:
                    # Default to ensemble approach
                    online_model = ensemble.AdaptiveRandomForestClassifier(
                        n_models=3,
                        max_features="sqrt",
                        lambda_value=6,
                        grace_period=50
                    )

                self.online_models[model_type] = online_model

                # Initialize drift detector
                drift_detector = ADWIN(delta=self.config["drift_detection"]["delta"])

                # Create learning state
                self.online_learning_states[model_type] = OnlineLearningState(
                    model_type=model_type,
                    samples_processed=0,
                    last_drift_check=datetime.now(),
                    drift_detector=drift_detector,
                    performance_buffer=deque(maxlen=100),
                    learning_rate=self.config["online_learning"]["learning_rate"],
                    adaptation_level=0.0
                )

            logger.info("Online learning models initialized")

        except Exception as e:
            logger.error(f"Online model initialization failed: {e}")

    def _start_background_processing(self):
        """Start background processing for continuous learning."""
        if not self.is_processing:
            self.is_processing = True
            asyncio.create_task(self._background_processor())

    async def _background_processor(self):
        """Background processor for continuous model training."""
        logger.info("Background model training processor started")

        while self.is_processing:
            try:
                # Process training queue
                await self._process_training_queue()

                # Check for retraining triggers
                await self._check_retraining_triggers()

                # Perform drift detection
                await self._check_concept_drift()

                # Update performance metrics
                await self._update_performance_metrics()

                # Sleep before next iteration
                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Background processing error: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    # Core Learning Methods

    async def add_training_data(
        self,
        model_type: ModelType,
        features: np.ndarray,
        labels: Dict[str, Union[float, int, str]],
        metadata: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0
    ):
        """Add new training data for a model."""
        try:
            # Validate data quality
            data_quality = self._assess_data_quality(features, labels)

            # Create training data point
            data_point = TrainingDataPoint(
                model_type=model_type,
                features=features,
                labels=labels,
                metadata=metadata or {},
                confidence_score=confidence,
                data_quality=data_quality
            )

            # Add to training buffer
            self.training_buffer[model_type].append(data_point)

            # Add to processing queue for immediate online learning
            await self.processing_queue.put(('online_update', data_point))

            logger.debug(f"Training data added for {model_type.value}")

        except Exception as e:
            logger.error(f"Failed to add training data: {e}")

    async def _process_training_queue(self):
        """Process items in the training queue."""
        try:
            # Process up to 10 items per iteration
            for _ in range(10):
                if self.processing_queue.empty():
                    break

                try:
                    action, data = await asyncio.wait_for(
                        self.processing_queue.get(),
                        timeout=0.1
                    )

                    if action == 'online_update':
                        await self._perform_online_update(data)
                    elif action == 'batch_retrain':
                        await self._perform_batch_retrain(data)

                except asyncio.TimeoutError:
                    break

        except Exception as e:
            logger.error(f"Training queue processing failed: {e}")

    async def _perform_online_update(self, data_point: TrainingDataPoint):
        """Perform online learning update with single data point."""
        try:
            model_type = data_point.model_type

            if model_type not in self.online_models:
                return

            online_model = self.online_models[model_type]
            state = self.online_learning_states[model_type]

            # Prepare features and labels
            features = data_point.features
            primary_label = list(data_point.labels.values())[0]

            # Create feature dict for River models
            feature_dict = {f"feature_{i}": float(features[i]) for i in range(len(features))}

            # Update model
            if hasattr(online_model, 'learn_one'):
                # River model
                if model_type in [ModelType.CHURN_PREDICTION, ModelType.ENGAGEMENT_SCORING]:
                    online_model.learn_one(feature_dict, primary_label)
                else:
                    online_model.learn_one(feature_dict, float(primary_label))

            # Update state
            state.samples_processed += 1

            # Predict and track performance
            if hasattr(online_model, 'predict_one'):
                try:
                    prediction = online_model.predict_one(feature_dict)
                    error = abs(float(prediction) - float(primary_label))
                    state.performance_buffer.append(1.0 - min(error, 1.0))
                except:
                    pass  # Skip performance tracking on prediction errors

            # Check for drift periodically
            if state.samples_processed % 100 == 0:
                await self._update_drift_detection(model_type, primary_label)

        except Exception as e:
            logger.error(f"Online update failed for {data_point.model_type}: {e}")

    async def _check_retraining_triggers(self):
        """Check if any models need retraining."""
        try:
            for model_type in ModelType:
                if await self._should_retrain_model(model_type):
                    await self._trigger_model_retraining(model_type)

        except Exception as e:
            logger.error(f"Retraining trigger check failed: {e}")

    async def _should_retrain_model(self, model_type: ModelType) -> bool:
        """Determine if a model should be retrained."""
        try:
            # Check if we have enough new training data
            buffer_size = len(self.training_buffer[model_type])
            if buffer_size < self.config["retraining_thresholds"]["sample_threshold"]:
                return False

            # Check performance degradation
            if model_type in self.performance_history:
                recent_performance = self.performance_history[model_type]
                if len(recent_performance) >= 2:
                    current_perf = recent_performance[-1].validation_score
                    previous_perf = recent_performance[-2].validation_score
                    degradation = previous_perf - current_perf

                    if degradation > self.config["retraining_thresholds"]["performance_degradation"]:
                        return True

            # Check time since last update
            if model_type in self.performance_history and self.performance_history[model_type]:
                last_update = self.performance_history[model_type][-1].last_update
                time_since_update = datetime.now() - last_update

                if time_since_update > self.config["retraining_thresholds"]["time_threshold"]:
                    return True

            # Check drift status
            if model_type in self.online_learning_states:
                state = self.online_learning_states[model_type]
                if hasattr(state.drift_detector, 'drift_detected'):
                    if state.drift_detector.drift_detected:
                        return True

            return False

        except Exception as e:
            logger.error(f"Retraining decision failed for {model_type}: {e}")
            return False

    async def _trigger_model_retraining(self, model_type: ModelType):
        """Trigger retraining for a specific model."""
        try:
            logger.info(f"Triggering retraining for {model_type.value}")

            # Get current performance baseline
            pre_training_perf = await self._evaluate_current_model(model_type)

            # Prepare training data
            training_data = list(self.training_buffer[model_type])
            if len(training_data) < 100:
                logger.warning(f"Insufficient data for {model_type.value} retraining")
                return

            # Perform retraining in thread pool to avoid blocking
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = asyncio.get_event_loop().run_in_executor(
                    executor,
                    self._retrain_model_sync,
                    model_type,
                    training_data
                )

                retrain_result = await future

            # Evaluate new performance
            post_training_perf = await self._evaluate_retrained_model(
                model_type, retrain_result["model"]
            )

            # Record retraining event
            improvement = post_training_perf.get("validation_score", 0) - pre_training_perf.get("validation_score", 0)

            event = RetrainingEvent(
                model_type=model_type,
                learning_mode=LearningMode.BATCH_RETRAIN,
                trigger_reason=retrain_result.get("trigger_reason", "Performance degradation"),
                pre_training_performance=pre_training_perf,
                post_training_performance=post_training_perf,
                training_samples_used=len(training_data),
                training_duration=retrain_result.get("duration", timedelta(0)),
                improvement_achieved=improvement
            )

            self.retraining_events.append(event)

            # Update model version
            self.model_versions[model_type] += 1

            # Save new model if improvement is significant
            if improvement > self.config["ensemble_config"]["min_performance_gain"]:
                await self._save_retrained_model(model_type, retrain_result["model"])
                logger.info(f"Model {model_type.value} retrained successfully. Improvement: {improvement:.3f}")
            else:
                logger.info(f"Model {model_type.value} retraining completed but no significant improvement")

        except Exception as e:
            logger.error(f"Model retraining failed for {model_type}: {e}")

    def _retrain_model_sync(self, model_type: ModelType, training_data: List[TrainingDataPoint]) -> Dict[str, Any]:
        """Synchronous model retraining (runs in thread pool)."""
        try:
            start_time = datetime.now()

            # Prepare training data
            X_train, y_train = self._prepare_training_data(training_data)

            # Select appropriate model based on type
            new_model = self._create_model_for_type(model_type)

            # Train the model
            new_model.fit(X_train, y_train)

            duration = datetime.now() - start_time

            return {
                "model": new_model,
                "duration": duration,
                "trigger_reason": "Scheduled retraining",
                "training_samples": len(training_data)
            }

        except Exception as e:
            logger.error(f"Synchronous retraining failed: {e}")
            raise

    def _prepare_training_data(self, training_data: List[TrainingDataPoint]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for model training."""
        try:
            # Extract features and primary labels
            features = []
            labels = []

            for data_point in training_data:
                if data_point.data_quality > 0.5:  # Quality filter
                    features.append(data_point.features)
                    # Use first label as primary target
                    primary_label = list(data_point.labels.values())[0]
                    labels.append(primary_label)

            X_train = np.array(features)
            y_train = np.array(labels)

            # Handle edge cases
            if len(X_train) == 0:
                raise ValueError("No valid training data after quality filtering")

            return X_train, y_train

        except Exception as e:
            logger.error(f"Training data preparation failed: {e}")
            raise

    def _create_model_for_type(self, model_type: ModelType):
        """Create appropriate model for the given type."""
        if model_type in [ModelType.CHURN_PREDICTION, ModelType.ENGAGEMENT_SCORING]:
            return RandomForestClassifier(
                n_estimators=100,
                max_depth=15,
                random_state=42,
                class_weight='balanced'
            )
        elif model_type in [ModelType.TIMING_OPTIMIZATION, ModelType.CONVERSION_PREDICTION]:
            return GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
        elif model_type == ModelType.SENTIMENT_ANALYSIS:
            return SGDClassifier(
                loss='log_loss',
                learning_rate='adaptive',
                eta0=0.01,
                random_state=42
            )
        else:
            # Default ensemble
            return RandomForestClassifier(
                n_estimators=50,
                max_depth=10,
                random_state=42
            )

    async def _evaluate_current_model(self, model_type: ModelType) -> Dict[str, float]:
        """Evaluate current model performance."""
        try:
            # Use validation buffer for evaluation
            if model_type not in self.validation_buffer or len(self.validation_buffer[model_type]) < 50:
                return {"validation_score": 0.5, "accuracy": 0.5}

            validation_data = list(self.validation_buffer[model_type])
            X_val, y_val = self._prepare_training_data(validation_data)

            if model_type in self.online_models:
                online_model = self.online_models[model_type]

                # Convert to River format for prediction
                predictions = []
                for i, features in enumerate(X_val):
                    feature_dict = {f"feature_{j}": float(features[j]) for j in range(len(features))}

                    if hasattr(online_model, 'predict_one'):
                        pred = online_model.predict_one(feature_dict)
                        predictions.append(pred)
                    else:
                        predictions.append(0.5)  # Default prediction

                # Calculate metrics
                predictions = np.array(predictions)

                if model_type in [ModelType.CHURN_PREDICTION, ModelType.ENGAGEMENT_SCORING]:
                    # Classification metrics
                    accuracy = accuracy_score(y_val, np.round(predictions))
                    return {"validation_score": accuracy, "accuracy": accuracy}
                else:
                    # Regression metrics
                    mse = mean_squared_error(y_val, predictions)
                    r2 = max(0, 1 - mse)  # Simplified R2
                    return {"validation_score": r2, "mse": mse}

        except Exception as e:
            logger.error(f"Current model evaluation failed: {e}")

        return {"validation_score": 0.5}

    async def _evaluate_retrained_model(self, model_type: ModelType, model) -> Dict[str, float]:
        """Evaluate newly retrained model."""
        try:
            # Use validation buffer
            if model_type not in self.validation_buffer or len(self.validation_buffer[model_type]) < 50:
                return {"validation_score": 0.6}

            validation_data = list(self.validation_buffer[model_type])
            X_val, y_val = self._prepare_training_data(validation_data)

            # Get predictions
            predictions = model.predict(X_val)

            # Calculate metrics based on model type
            if model_type in [ModelType.CHURN_PREDICTION, ModelType.ENGAGEMENT_SCORING]:
                accuracy = accuracy_score(y_val, predictions)
                return {"validation_score": accuracy, "accuracy": accuracy}
            else:
                mse = mean_squared_error(y_val, predictions)
                r2 = r2_score(y_val, predictions)
                return {"validation_score": r2, "mse": mse, "r2": r2}

        except Exception as e:
            logger.error(f"Retrained model evaluation failed: {e}")
            return {"validation_score": 0.6}

    async def _save_retrained_model(self, model_type: ModelType, model):
        """Save retrained model to disk."""
        try:
            model_filename = f"{model_type.value}_v{self.model_versions[model_type]}.joblib"
            model_path = self.models_dir / model_filename

            # Save in thread pool to avoid blocking
            with ThreadPoolExecutor(max_workers=1) as executor:
                await asyncio.get_event_loop().run_in_executor(
                    executor,
                    joblib.dump,
                    model,
                    model_path
                )

            logger.info(f"Saved retrained model: {model_filename}")

        except Exception as e:
            logger.error(f"Model saving failed: {e}")

    # Concept Drift Detection

    async def _check_concept_drift(self):
        """Check for concept drift in all models."""
        try:
            current_time = datetime.now()

            for model_type, state in self.online_learning_states.items():
                time_since_check = current_time - state.last_drift_check

                if time_since_check > self.config["drift_detection"]["check_frequency"]:
                    drift_detected = await self._detect_drift_for_model(model_type)

                    if drift_detected:
                        logger.warning(f"Concept drift detected for {model_type.value}")
                        await self._handle_concept_drift(model_type)

                    state.last_drift_check = current_time

        except Exception as e:
            logger.error(f"Drift detection failed: {e}")

    async def _detect_drift_for_model(self, model_type: ModelType) -> bool:
        """Detect concept drift for a specific model."""
        try:
            state = self.online_learning_states[model_type]

            # Check if drift detector indicates drift
            if hasattr(state.drift_detector, 'drift_detected'):
                return state.drift_detector.drift_detected

            # Statistical drift detection using performance buffer
            if len(state.performance_buffer) > 50:
                recent_performance = list(state.performance_buffer)[-25:]
                historical_performance = list(state.performance_buffer)[:-25]

                if len(historical_performance) > 25:
                    # Use Kolmogorov-Smirnov test for distribution change
                    ks_statistic, p_value = stats.ks_2samp(historical_performance, recent_performance)

                    # Drift detected if distributions are significantly different
                    return p_value < 0.05

            return False

        except Exception as e:
            logger.error(f"Drift detection failed for {model_type}: {e}")
            return False

    async def _update_drift_detection(self, model_type: ModelType, prediction_error: float):
        """Update drift detector with new prediction error."""
        try:
            state = self.online_learning_states[model_type]

            # Update ADWIN detector
            if hasattr(state.drift_detector, 'update'):
                state.drift_detector.update(prediction_error)

        except Exception as e:
            logger.error(f"Drift detector update failed: {e}")

    async def _handle_concept_drift(self, model_type: ModelType):
        """Handle detected concept drift."""
        try:
            logger.info(f"Handling concept drift for {model_type.value}")

            # Reset online model
            if model_type in self.online_models:
                self._initialize_single_online_model(model_type)

            # Trigger immediate retraining if we have enough data
            if len(self.training_buffer[model_type]) > 200:
                await self._trigger_model_retraining(model_type)

            # Reset drift detector
            state = self.online_learning_states[model_type]
            state.drift_detector = ADWIN(delta=self.config["drift_detection"]["delta"])
            state.adaptation_level += 0.1  # Increase adaptation rate

        except Exception as e:
            logger.error(f"Drift handling failed: {e}")

    def _initialize_single_online_model(self, model_type: ModelType):
        """Initialize online model for a specific type."""
        if model_type in [ModelType.CHURN_PREDICTION, ModelType.ENGAGEMENT_SCORING]:
            self.online_models[model_type] = compose.Pipeline(
                preprocessing.StandardScaler(),
                linear_model.LogisticRegression(l2=0.1)
            )
        else:
            self.online_models[model_type] = compose.Pipeline(
                preprocessing.StandardScaler(),
                linear_model.LinearRegression(l2=0.1)
            )

    # Performance Monitoring

    async def _update_performance_metrics(self):
        """Update performance metrics for all models."""
        try:
            for model_type in ModelType:
                snapshot = await self._create_performance_snapshot(model_type)
                if snapshot:
                    self.performance_history[model_type].append(snapshot)

                    # Keep only recent history
                    if len(self.performance_history[model_type]) > 100:
                        self.performance_history[model_type] = self.performance_history[model_type][-50:]

        except Exception as e:
            logger.error(f"Performance metrics update failed: {e}")

    async def _create_performance_snapshot(self, model_type: ModelType) -> Optional[ModelPerformanceSnapshot]:
        """Create performance snapshot for a model."""
        try:
            # Evaluate current model
            current_perf = await self._evaluate_current_model(model_type)

            # Calculate metrics
            metrics = {}
            for metric_name, value in current_perf.items():
                if metric_name in ["accuracy", "precision", "recall", "f1_score"]:
                    metrics[PerformanceMetric(metric_name)] = value

            # Determine drift status
            drift_status = DriftStatus.STABLE
            if model_type in self.online_learning_states:
                state = self.online_learning_states[model_type]
                if hasattr(state.drift_detector, 'drift_detected') and state.drift_detector.drift_detected:
                    drift_status = DriftStatus.DRIFT_DETECTED

            # Determine trend
            trend = "stable"
            if model_type in self.performance_history and len(self.performance_history[model_type]) > 2:
                recent_scores = [s.validation_score for s in self.performance_history[model_type][-3:]]
                if recent_scores[-1] > recent_scores[0] + 0.02:
                    trend = "improving"
                elif recent_scores[-1] < recent_scores[0] - 0.02:
                    trend = "declining"

            return ModelPerformanceSnapshot(
                model_type=model_type,
                performance_metrics=metrics,
                validation_score=current_perf.get("validation_score", 0.5),
                training_samples=len(self.training_buffer[model_type]),
                model_version=f"v{self.model_versions[model_type]}",
                drift_status=drift_status,
                last_update=datetime.now(),
                improvement_trend=trend
            )

        except Exception as e:
            logger.error(f"Performance snapshot creation failed: {e}")
            return None

    def _assess_data_quality(self, features: np.ndarray, labels: Dict[str, Any]) -> float:
        """Assess quality of training data point."""
        quality_score = 1.0

        # Check for missing values
        if np.any(np.isnan(features)) or np.any(np.isinf(features)):
            quality_score *= 0.5

        # Check feature range (simplified)
        if np.any(np.abs(features) > 1000):
            quality_score *= 0.8

        # Check label validity
        for label_value in labels.values():
            if isinstance(label_value, (int, float)) and (np.isnan(label_value) or np.isinf(label_value)):
                quality_score *= 0.3

        return quality_score

    # Public API Methods

    async def get_model_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report for all models."""
        try:
            report = {
                "overview": {
                    "total_models": len(ModelType),
                    "models_with_online_learning": len(self.online_models),
                    "total_training_samples": sum(len(buffer) for buffer in self.training_buffer.values()),
                    "retraining_events": len(self.retraining_events)
                },
                "model_performance": {},
                "drift_status": {},
                "retraining_history": []
            }

            # Individual model performance
            for model_type in ModelType:
                if model_type in self.performance_history and self.performance_history[model_type]:
                    latest_snapshot = self.performance_history[model_type][-1]

                    report["model_performance"][model_type.value] = {
                        "validation_score": latest_snapshot.validation_score,
                        "training_samples": latest_snapshot.training_samples,
                        "model_version": latest_snapshot.model_version,
                        "improvement_trend": latest_snapshot.improvement_trend,
                        "last_update": latest_snapshot.last_update.isoformat()
                    }

                    report["drift_status"][model_type.value] = latest_snapshot.drift_status.value

            # Recent retraining events
            report["retraining_history"] = [
                {
                    "model_type": event.model_type.value,
                    "improvement": event.improvement_achieved,
                    "samples_used": event.training_samples_used,
                    "timestamp": event.timestamp.isoformat()
                }
                for event in self.retraining_events[-10:]
            ]

            return report

        except Exception as e:
            logger.error(f"Performance report generation failed: {e}")
            return {"error": str(e)}

    async def force_model_retrain(self, model_type: ModelType, reason: str = "Manual trigger"):
        """Force immediate retraining of a specific model."""
        try:
            logger.info(f"Force retraining {model_type.value}: {reason}")

            if len(self.training_buffer[model_type]) < 50:
                raise ValueError(f"Insufficient training data for {model_type.value}")

            # Add to processing queue
            await self.processing_queue.put(('batch_retrain', {
                'model_type': model_type,
                'reason': reason
            }))

        except Exception as e:
            logger.error(f"Force retrain failed: {e}")
            raise

    async def get_online_learning_status(self) -> Dict[str, Any]:
        """Get status of online learning for all models."""
        try:
            status = {}

            for model_type, state in self.online_learning_states.items():
                recent_performance = list(state.performance_buffer)[-10:] if state.performance_buffer else []

                status[model_type.value] = {
                    "samples_processed": state.samples_processed,
                    "recent_performance": statistics.mean(recent_performance) if recent_performance else 0,
                    "learning_rate": state.learning_rate,
                    "adaptation_level": state.adaptation_level,
                    "drift_detected": hasattr(state.drift_detector, 'drift_detected') and state.drift_detector.drift_detected
                }

            return status

        except Exception as e:
            logger.error(f"Online learning status failed: {e}")
            return {}

    def stop_background_processing(self):
        """Stop background processing."""
        self.is_processing = False
        logger.info("Background processing stopped")


# Export main classes
__all__ = [
    'RealTimeModelTraining',
    'ModelType',
    'LearningMode',
    'TrainingDataPoint',
    'ModelPerformanceSnapshot',
    'RetrainingEvent',
    'DriftStatus'
]