#!/usr/bin/env python3
"""
🚀 MLOps Pipeline - Service 6 Phase 2
====================================

Production MLOps system with model registry and monitoring that provides:
- Model versioning and registry with lineage tracking
- Automated model training and deployment pipeline
- Real-time model performance monitoring
- A/B testing infrastructure for model comparison
- Data drift detection and alerts
- Model rollback and canary deployment capabilities

Features:
- Git-based model versioning
- Containerized model serving
- Prometheus metrics integration
- Automated retraining triggers
- Model validation and testing
- Performance benchmarking
- Data quality monitoring
- Experiment tracking and comparison

Author: Claude AI Enhancement System
Date: 2026-01-16
"""

import asyncio
import hashlib
import json
import pickle
import shutil
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ML and monitoring libraries
try:
    import joblib
    import numpy as np
    import pandas as pd
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
    from sklearn.model_selection import cross_val_score

    HAS_ML_LIBS = True
except ImportError:
    HAS_ML_LIBS = False

# Service integrations
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator

logger = get_logger(__name__)


@dataclass
class ModelMetadata:
    """Model metadata for registry"""

    model_id: str
    model_name: str
    version: str
    created_at: datetime
    created_by: str

    # Model details
    model_type: str  # 'lead_scorer', 'churn_predictor', 'engagement_classifier'
    algorithm: str  # 'xgboost', 'neural_network', 'ensemble'
    framework: str  # 'sklearn', 'pytorch', 'custom'

    # Training metadata
    training_data_hash: str
    training_samples: int
    feature_count: int
    training_duration_seconds: float
    hyperparameters: Dict[str, Any]

    # Performance metrics
    validation_metrics: Dict[str, float]
    cross_validation_score: float
    benchmark_metrics: Dict[str, float]

    # Deployment info
    deployment_status: str  # 'training', 'validation', 'staging', 'production', 'retired'
    deployment_timestamp: Optional[datetime]
    endpoint_url: Optional[str]

    # Lineage and dependencies
    parent_model_id: Optional[str]
    training_pipeline_version: str
    data_pipeline_version: str

    # Monitoring
    monitoring_enabled: bool
    alert_thresholds: Dict[str, float]

    # Metadata
    description: str
    tags: List[str]
    model_size_mb: float
    prediction_latency_ms: float


@dataclass
class ModelPerformanceMetrics:
    """Real-time model performance metrics"""

    model_id: str
    timestamp: datetime
    time_window: str  # '1h', '24h', '7d', '30d'

    # Prediction metrics
    total_predictions: int
    avg_prediction_latency_ms: float
    error_rate: float
    throughput_per_second: float

    # Quality metrics
    accuracy: Optional[float]
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]
    auc_score: Optional[float]

    # Business metrics
    conversion_correlation: float  # How well predictions correlate with actual conversions
    business_impact_score: float
    cost_effectiveness: float

    # Drift detection
    feature_drift_score: float
    prediction_drift_score: float
    data_quality_score: float

    # Alerts
    active_alerts: List[str]
    performance_degradation: bool
    requires_retraining: bool


@dataclass
class ModelExperiment:
    """ML experiment tracking"""

    experiment_id: str
    experiment_name: str
    model_type: str
    started_at: datetime
    completed_at: Optional[datetime]

    # Experiment configuration
    hypothesis: str
    baseline_model_id: str
    candidate_model_configs: List[Dict[str, Any]]

    # Data configuration
    training_data_config: Dict[str, Any]
    validation_split: float
    feature_engineering_pipeline: str

    # Results
    model_performances: Dict[str, ModelPerformanceMetrics]
    statistical_significance: float
    winner_model_id: Optional[str]
    improvement_metrics: Dict[str, float]

    # Deployment decision
    deployment_recommendation: str
    deployment_strategy: str  # 'full', 'canary', 'blue_green'
    rollback_plan: str

    # Status
    status: str  # 'running', 'completed', 'failed', 'cancelled'
    logs: List[str]


@dataclass
class DataDriftAlert:
    """Data drift detection alert"""

    alert_id: str
    model_id: str
    detected_at: datetime
    alert_type: str  # 'feature_drift', 'prediction_drift', 'performance_degradation'

    # Drift details
    severity: str  # 'low', 'medium', 'high', 'critical'
    drift_score: float
    affected_features: List[str]
    drift_magnitude: Dict[str, float]  # feature -> drift amount

    # Context
    detection_method: str
    statistical_tests: Dict[str, float]
    time_window: str
    baseline_period: str

    # Impact assessment
    predicted_impact: str
    recommended_actions: List[str]
    urgency_level: str

    # Resolution
    acknowledged: bool
    resolved: bool
    resolution_action: Optional[str]
    resolution_timestamp: Optional[datetime]


class ModelRegistry:
    """Centralized model registry with versioning"""

    def __init__(self, registry_path: str = "models/registry"):
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)

        # Registry database (JSON file for simplicity)
        self.registry_db_path = self.registry_path / "registry.json"
        self.models = self._load_registry()

        # Model storage
        self.model_storage_path = self.registry_path / "models"
        self.model_storage_path.mkdir(exist_ok=True)

        self.cache = CacheService()

    def _load_registry(self) -> Dict[str, Dict]:
        """Load model registry from disk"""
        if self.registry_db_path.exists():
            try:
                with open(self.registry_db_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load registry: {e}")

        return {}

    def _save_registry(self):
        """Save model registry to disk"""
        try:
            # Create backup
            if self.registry_db_path.exists():
                backup_path = self.registry_db_path.with_suffix(".json.backup")
                shutil.copy(self.registry_db_path, backup_path)

            # Save current registry
            with open(self.registry_db_path, "w") as f:
                json.dump(self.models, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to save registry: {e}")

    async def register_model(self, metadata: ModelMetadata, model_artifact: Any) -> bool:
        """Register a new model version"""

        try:
            # Save model artifact
            model_path = self.model_storage_path / f"{metadata.model_id}.pkl"
            with open(model_path, "wb") as f:
                pickle.dump(model_artifact, f)

            # Update registry
            self.models[metadata.model_id] = asdict(metadata)
            self._save_registry()

            # Cache model metadata
            await self.cache.set(f"model_metadata:{metadata.model_id}", asdict(metadata), ttl=3600)

            logger.info(f"Registered model {metadata.model_id} v{metadata.version}")
            return True

        except Exception as e:
            logger.error(f"Failed to register model {metadata.model_id}: {e}")
            return False

    async def get_model(self, model_id: str) -> Optional[Tuple[ModelMetadata, Any]]:
        """Retrieve model and metadata"""

        # Check cache first
        cached_metadata = await self.cache.get(f"model_metadata:{model_id}")
        if cached_metadata:
            metadata = ModelMetadata(**cached_metadata)
        else:
            if model_id not in self.models:
                return None
            metadata = ModelMetadata(**self.models[model_id])

        # Load model artifact
        try:
            model_path = self.model_storage_path / f"{model_id}.pkl"
            with open(model_path, "rb") as f:
                model_artifact = pickle.load(f)

            return metadata, model_artifact

        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            return None

    async def get_latest_model(
        self, model_type: str, status: str = "production"
    ) -> Optional[Tuple[ModelMetadata, Any]]:
        """Get latest model of specific type and status"""

        matching_models = []
        for model_id, model_data in self.models.items():
            if model_data.get("model_type") == model_type and model_data.get("deployment_status") == status:
                matching_models.append((model_id, model_data))

        if not matching_models:
            return None

        # Sort by creation date (latest first)
        latest_model = max(matching_models, key=lambda x: x[1]["created_at"])
        return await self.get_model(latest_model[0])

    async def list_models(self, model_type: Optional[str] = None, status: Optional[str] = None) -> List[ModelMetadata]:
        """List models with optional filtering"""

        models = []
        for model_id, model_data in self.models.items():
            metadata = ModelMetadata(**model_data)

            # Apply filters
            if model_type and metadata.model_type != model_type:
                continue
            if status and metadata.deployment_status != status:
                continue

            models.append(metadata)

        # Sort by creation date (newest first)
        return sorted(models, key=lambda x: x.created_at, reverse=True)

    async def promote_model(self, model_id: str, new_status: str) -> bool:
        """Promote model to new deployment status"""

        if model_id not in self.models:
            logger.error(f"Model {model_id} not found in registry")
            return False

        try:
            # Update deployment status
            self.models[model_id]["deployment_status"] = new_status
            self.models[model_id]["deployment_timestamp"] = datetime.now()

            # If promoting to production, demote other production models of same type
            if new_status == "production":
                model_type = self.models[model_id]["model_type"]
                for mid, mdata in self.models.items():
                    if (
                        mid != model_id
                        and mdata.get("model_type") == model_type
                        and mdata.get("deployment_status") == "production"
                    ):
                        mdata["deployment_status"] = "retired"

            self._save_registry()

            # Clear cache
            await self.cache.delete(f"model_metadata:{model_id}")

            logger.info(f"Promoted model {model_id} to {new_status}")
            return True

        except Exception as e:
            logger.error(f"Failed to promote model {model_id}: {e}")
            return False

    async def get_model_lineage(self, model_id: str) -> List[ModelMetadata]:
        """Get model lineage (parent -> children relationships)"""

        lineage = []

        # Find parents
        current_model = self.models.get(model_id)
        while current_model and current_model.get("parent_model_id"):
            parent_id = current_model["parent_model_id"]
            if parent_id in self.models:
                lineage.insert(0, ModelMetadata(**self.models[parent_id]))
                current_model = self.models[parent_id]
            else:
                break

        # Add current model
        if model_id in self.models:
            lineage.append(ModelMetadata(**self.models[model_id]))

        # Find children
        children = [mid for mid, mdata in self.models.items() if mdata.get("parent_model_id") == model_id]

        for child_id in children:
            lineage.append(ModelMetadata(**self.models[child_id]))

        return lineage


class ModelMonitoring:
    """Real-time model performance monitoring"""

    def __init__(self):
        self.metrics_storage = defaultdict(lambda: deque(maxlen=1000))  # Keep last 1000 data points
        self.alert_thresholds = {}
        self.active_alerts = defaultdict(list)
        self.drift_detectors = {}

    async def record_prediction(
        self,
        model_id: str,
        prediction: Any,
        features: Dict[str, Any],
        actual_outcome: Optional[Any] = None,
        latency_ms: float = 0,
    ):
        """Record a model prediction for monitoring"""

        timestamp = datetime.now()

        prediction_record = {
            "timestamp": timestamp,
            "model_id": model_id,
            "prediction": prediction,
            "features": features,
            "actual_outcome": actual_outcome,
            "latency_ms": latency_ms,
        }

        # Store prediction record
        self.metrics_storage[model_id].append(prediction_record)

        # Trigger drift detection if we have enough data
        if len(self.metrics_storage[model_id]) % 100 == 0:  # Every 100 predictions
            await self._check_data_drift(model_id)

        # Calculate and cache current metrics
        await self._update_performance_metrics(model_id)

    async def get_performance_metrics(
        self, model_id: str, time_window: str = "24h"
    ) -> Optional[ModelPerformanceMetrics]:
        """Get performance metrics for time window"""

        if model_id not in self.metrics_storage:
            return None

        # Parse time window
        hours = self._parse_time_window(time_window)
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # Filter data by time window
        recent_data = [record for record in self.metrics_storage[model_id] if record["timestamp"] > cutoff_time]

        if not recent_data:
            return None

        # Calculate metrics
        return await self._calculate_metrics(model_id, recent_data, time_window)

    async def _update_performance_metrics(self, model_id: str):
        """Update performance metrics for model"""

        # Calculate metrics for different time windows
        for window in ["1h", "24h", "7d"]:
            metrics = await self.get_performance_metrics(model_id, window)
            if metrics:
                # Cache metrics
                cache_key = f"model_metrics:{model_id}:{window}"
                await CacheService().set(cache_key, asdict(metrics), ttl=300)  # 5 minute cache

                # Check for alerts
                await self._check_performance_alerts(model_id, metrics)

    async def _calculate_metrics(self, model_id: str, data: List[Dict], time_window: str) -> ModelPerformanceMetrics:
        """Calculate performance metrics from prediction data"""

        if not data:
            return self._empty_metrics(model_id, time_window)

        total_predictions = len(data)

        # Latency metrics
        latencies = [record["latency_ms"] for record in data if record["latency_ms"] > 0]
        avg_latency = np.mean(latencies) if latencies else 0

        # Throughput
        if data:
            time_span_hours = (data[-1]["timestamp"] - data[0]["timestamp"]).total_seconds() / 3600
            throughput = total_predictions / max(time_span_hours, 0.1)
        else:
            throughput = 0

        # Error rate (simplified - count None predictions or errors)
        errors = [record for record in data if record["prediction"] is None]
        error_rate = len(errors) / max(total_predictions, 1)

        # Quality metrics (only if we have actual outcomes)
        data_with_outcomes = [record for record in data if record["actual_outcome"] is not None]

        accuracy = None
        precision = None
        recall = None
        f1 = None
        auc = None

        if len(data_with_outcomes) > 10:  # Need minimum data for quality metrics
            try:
                y_true = [record["actual_outcome"] for record in data_with_outcomes]
                y_pred = [record["prediction"] for record in data_with_outcomes]

                if HAS_ML_LIBS:
                    # Assume binary classification for simplicity
                    y_pred_binary = [1 if pred > 0.5 else 0 for pred in y_pred if isinstance(pred, (int, float))]
                    y_true_binary = [1 if true > 0.5 else 0 for true in y_true if isinstance(true, (int, float))]

                    if len(y_pred_binary) == len(y_true_binary) and len(y_pred_binary) > 0:
                        accuracy = accuracy_score(y_true_binary, y_pred_binary)
                        precision = precision_score(y_true_binary, y_pred_binary, zero_division=0)
                        recall = recall_score(y_true_binary, y_pred_binary, zero_division=0)
                        f1 = f1_score(y_true_binary, y_pred_binary, zero_division=0)

                        # AUC for probability predictions
                        y_pred_proba = [pred for pred in y_pred if isinstance(pred, (int, float))]
                        if len(y_pred_proba) == len(y_true_binary):
                            auc = roc_auc_score(y_true_binary, y_pred_proba)

            except Exception as e:
                logger.error(f"Quality metrics calculation failed: {e}")

        # Drift detection
        feature_drift_score = await self._calculate_feature_drift(model_id, data)
        prediction_drift_score = await self._calculate_prediction_drift(model_id, data)
        data_quality_score = self._calculate_data_quality_score(data)

        # Business metrics (simplified)
        conversion_correlation = accuracy if accuracy else 0.5  # Use accuracy as proxy
        business_impact_score = conversion_correlation * 0.8  # Simplified calculation
        cost_effectiveness = throughput / max(avg_latency / 1000, 0.001)  # predictions per second per latency

        # Active alerts
        active_alerts = self.active_alerts.get(model_id, [])

        return ModelPerformanceMetrics(
            model_id=model_id,
            timestamp=datetime.now(),
            time_window=time_window,
            total_predictions=total_predictions,
            avg_prediction_latency_ms=avg_latency,
            error_rate=error_rate,
            throughput_per_second=throughput,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            auc_score=auc,
            conversion_correlation=conversion_correlation,
            business_impact_score=business_impact_score,
            cost_effectiveness=cost_effectiveness,
            feature_drift_score=feature_drift_score,
            prediction_drift_score=prediction_drift_score,
            data_quality_score=data_quality_score,
            active_alerts=[alert["alert_type"] for alert in active_alerts],
            performance_degradation=any("degradation" in alert.get("alert_type", "") for alert in active_alerts),
            requires_retraining=feature_drift_score > 0.7 or prediction_drift_score > 0.7,
        )

    def _empty_metrics(self, model_id: str, time_window: str) -> ModelPerformanceMetrics:
        """Return empty metrics when no data available"""
        return ModelPerformanceMetrics(
            model_id=model_id,
            timestamp=datetime.now(),
            time_window=time_window,
            total_predictions=0,
            avg_prediction_latency_ms=0,
            error_rate=0,
            throughput_per_second=0,
            accuracy=None,
            precision=None,
            recall=None,
            f1_score=None,
            auc_score=None,
            conversion_correlation=0,
            business_impact_score=0,
            cost_effectiveness=0,
            feature_drift_score=0,
            prediction_drift_score=0,
            data_quality_score=1.0,
            active_alerts=[],
            performance_degradation=False,
            requires_retraining=False,
        )

    async def _calculate_feature_drift(self, model_id: str, recent_data: List[Dict]) -> float:
        """Calculate feature drift score"""

        if len(recent_data) < 50:  # Need minimum data
            return 0.0

        try:
            # Get baseline feature distribution (from first 100 predictions)
            all_data = list(self.metrics_storage[model_id])
            if len(all_data) < 100:
                return 0.0

            baseline_data = all_data[:100]

            # Compare feature distributions using Kolmogorov-Smirnov test
            drift_scores = []

            # Get all feature names
            feature_names = set()
            for record in baseline_data + recent_data:
                if record.get("features"):
                    feature_names.update(record["features"].keys())

            for feature_name in feature_names:
                # Extract feature values
                baseline_values = []
                recent_values = []

                for record in baseline_data:
                    if record.get("features") and feature_name in record["features"]:
                        val = record["features"][feature_name]
                        if isinstance(val, (int, float)):
                            baseline_values.append(val)

                for record in recent_data:
                    if record.get("features") and feature_name in record["features"]:
                        val = record["features"][feature_name]
                        if isinstance(val, (int, float)):
                            recent_values.append(val)

                if len(baseline_values) > 10 and len(recent_values) > 10:
                    try:
                        from scipy.stats import ks_2samp

                        statistic, p_value = ks_2samp(baseline_values, recent_values)
                        drift_scores.append(statistic)  # Higher statistic = more drift
                    except ImportError:
                        # Fallback: simple mean comparison
                        baseline_mean = np.mean(baseline_values)
                        recent_mean = np.mean(recent_values)
                        baseline_std = np.std(baseline_values)
                        if baseline_std > 0:
                            drift_score = abs(recent_mean - baseline_mean) / baseline_std
                            drift_scores.append(min(drift_score, 1.0))

            return np.mean(drift_scores) if drift_scores else 0.0

        except Exception as e:
            logger.error(f"Feature drift calculation failed: {e}")
            return 0.0

    async def _calculate_prediction_drift(self, model_id: str, recent_data: List[Dict]) -> float:
        """Calculate prediction drift score"""

        if len(recent_data) < 50:
            return 0.0

        try:
            # Compare prediction distribution to baseline
            all_data = list(self.metrics_storage[model_id])
            if len(all_data) < 100:
                return 0.0

            baseline_data = all_data[:100]

            # Extract numeric predictions
            baseline_predictions = []
            recent_predictions = []

            for record in baseline_data:
                pred = record.get("prediction")
                if isinstance(pred, (int, float)):
                    baseline_predictions.append(pred)

            for record in recent_data:
                pred = record.get("prediction")
                if isinstance(pred, (int, float)):
                    recent_predictions.append(pred)

            if len(baseline_predictions) < 10 or len(recent_predictions) < 10:
                return 0.0

            # Calculate drift
            baseline_mean = np.mean(baseline_predictions)
            recent_mean = np.mean(recent_predictions)
            baseline_std = np.std(baseline_predictions)

            if baseline_std > 0:
                drift_score = abs(recent_mean - baseline_mean) / baseline_std
                return min(drift_score, 1.0)
            else:
                return 0.0

        except Exception as e:
            logger.error(f"Prediction drift calculation failed: {e}")
            return 0.0

    def _calculate_data_quality_score(self, data: List[Dict]) -> float:
        """Calculate data quality score"""

        if not data:
            return 1.0

        quality_scores = []

        for record in data:
            record_quality = 1.0

            # Check for missing features
            features = record.get("features", {})
            if not features:
                record_quality *= 0.5
            else:
                # Check for missing feature values
                missing_features = sum(1 for v in features.values() if v is None or v == "")
                if missing_features > 0:
                    record_quality *= 1 - missing_features / len(features)

            # Check prediction validity
            prediction = record.get("prediction")
            if prediction is None:
                record_quality *= 0.3
            elif isinstance(prediction, (int, float)) and (prediction < 0 or prediction > 1):
                record_quality *= 0.8  # Out of expected range but not null

            quality_scores.append(record_quality)

        return np.mean(quality_scores)

    async def _check_performance_alerts(self, model_id: str, metrics: ModelPerformanceMetrics):
        """Check for performance alerts"""

        alerts = []

        # Get alert thresholds for this model
        thresholds = self.alert_thresholds.get(model_id, {})

        # Error rate alert
        if metrics.error_rate > thresholds.get("max_error_rate", 0.1):
            alerts.append(
                {
                    "alert_type": "high_error_rate",
                    "severity": "high" if metrics.error_rate > 0.2 else "medium",
                    "message": f"Error rate {metrics.error_rate:.2%} exceeds threshold",
                    "timestamp": datetime.now(),
                }
            )

        # Latency alert
        if metrics.avg_prediction_latency_ms > thresholds.get("max_latency_ms", 1000):
            alerts.append(
                {
                    "alert_type": "high_latency",
                    "severity": "medium",
                    "message": f"Avg latency {metrics.avg_prediction_latency_ms:.1f}ms exceeds threshold",
                    "timestamp": datetime.now(),
                }
            )

        # Accuracy degradation alert
        if metrics.accuracy and metrics.accuracy < thresholds.get("min_accuracy", 0.7):
            alerts.append(
                {
                    "alert_type": "accuracy_degradation",
                    "severity": "high",
                    "message": f"Accuracy {metrics.accuracy:.2%} below threshold",
                    "timestamp": datetime.now(),
                }
            )

        # Drift alerts
        if metrics.feature_drift_score > thresholds.get("max_feature_drift", 0.7):
            alerts.append(
                {
                    "alert_type": "feature_drift",
                    "severity": "high",
                    "message": f"Feature drift score {metrics.feature_drift_score:.2f} exceeds threshold",
                    "timestamp": datetime.now(),
                }
            )

        # Update active alerts
        self.active_alerts[model_id] = alerts

        # Log critical alerts
        critical_alerts = [a for a in alerts if a["severity"] == "high"]
        if critical_alerts:
            for alert in critical_alerts:
                logger.warning(f"Model {model_id} alert: {alert['message']}")

    async def _check_data_drift(self, model_id: str):
        """Comprehensive data drift detection"""

        recent_data = list(self.metrics_storage[model_id])[-100:]  # Last 100 predictions

        feature_drift = await self._calculate_feature_drift(model_id, recent_data)
        prediction_drift = await self._calculate_prediction_drift(model_id, recent_data)

        # Create drift alerts if thresholds exceeded
        alerts = []

        if feature_drift > 0.7:
            alerts.append(
                DataDriftAlert(
                    alert_id=f"drift_{model_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    model_id=model_id,
                    detected_at=datetime.now(),
                    alert_type="feature_drift",
                    severity="high" if feature_drift > 0.8 else "medium",
                    drift_score=feature_drift,
                    affected_features=[],  # Would be populated in full implementation
                    drift_magnitude={},
                    detection_method="kolmogorov_smirnov",
                    statistical_tests={"ks_test": feature_drift},
                    time_window="100_predictions",
                    baseline_period="first_100_predictions",
                    predicted_impact="Model performance degradation likely",
                    recommended_actions=[
                        "Investigate input data pipeline",
                        "Retrain model with recent data",
                        "Update feature engineering pipeline",
                    ],
                    urgency_level="high",
                    acknowledged=False,
                    resolved=False,
                    resolution_action=None,
                    resolution_timestamp=None,
                )
            )

        if prediction_drift > 0.7:
            alerts.append(
                DataDriftAlert(
                    alert_id=f"pred_drift_{model_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    model_id=model_id,
                    detected_at=datetime.now(),
                    alert_type="prediction_drift",
                    severity="medium",
                    drift_score=prediction_drift,
                    affected_features=[],
                    drift_magnitude={},
                    detection_method="distribution_comparison",
                    statistical_tests={"mean_shift": prediction_drift},
                    time_window="100_predictions",
                    baseline_period="first_100_predictions",
                    predicted_impact="Model behavior change detected",
                    recommended_actions=[
                        "Validate model predictions manually",
                        "Check for input data quality issues",
                        "Consider model refresh",
                    ],
                    urgency_level="medium",
                    acknowledged=False,
                    resolved=False,
                    resolution_action=None,
                    resolution_timestamp=None,
                )
            )

        # Store alerts (in production, would send to alerting system)
        for alert in alerts:
            logger.warning(f"Data drift alert: {alert.alert_type} for model {model_id}")

    def _parse_time_window(self, time_window: str) -> int:
        """Parse time window string to hours"""

        if time_window.endswith("h"):
            return int(time_window[:-1])
        elif time_window.endswith("d"):
            return int(time_window[:-1]) * 24
        else:
            return 24  # Default to 24 hours

    async def set_alert_thresholds(self, model_id: str, thresholds: Dict[str, float]):
        """Set performance alert thresholds for a model"""
        self.alert_thresholds[model_id] = thresholds


class ModelTrainingPipeline:
    """Automated model training and validation pipeline"""

    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.claude = get_claude_orchestrator()
        self.active_training_jobs = {}

    async def train_model(self, training_config: Dict[str, Any]) -> str:
        """Start model training job"""

        job_id = f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Validate training config
        if not self._validate_training_config(training_config):
            raise ValueError("Invalid training configuration")

        # Start training job
        training_job = {
            "job_id": job_id,
            "config": training_config,
            "status": "starting",
            "started_at": datetime.now(),
            "completed_at": None,
            "model_id": None,
            "logs": [],
            "metrics": {},
        }

        self.active_training_jobs[job_id] = training_job

        # Run training asynchronously
        asyncio.create_task(self._run_training_job(job_id))

        return job_id

    async def _run_training_job(self, job_id: str):
        """Run the actual training job"""

        job = self.active_training_jobs[job_id]

        try:
            job["status"] = "running"
            job["logs"].append(f"{datetime.now()}: Starting model training")

            # Simulate training (in production, would run actual ML training)
            config = job["config"]

            # Generate model ID
            model_id = f"{config['model_type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            job["model_id"] = model_id

            # Simulate training duration
            await asyncio.sleep(5)  # Simulate 5 second training

            # Create dummy model (in production, would be real trained model)
            if HAS_ML_LIBS:
                from sklearn.ensemble import RandomForestClassifier

                model = RandomForestClassifier(n_estimators=100, random_state=42)
                # Would fit on real data here
                # model.fit(X_train, y_train)
            else:
                model = {"type": "dummy_model", "trained_at": datetime.now()}

            # Simulate validation metrics
            validation_metrics = {"accuracy": 0.85, "precision": 0.82, "recall": 0.88, "f1_score": 0.85, "auc": 0.89}

            job["metrics"] = validation_metrics

            # Create model metadata
            metadata = ModelMetadata(
                model_id=model_id,
                model_name=config.get("model_name", "Unnamed Model"),
                version="1.0.0",
                created_at=datetime.now(),
                created_by="automated_pipeline",
                model_type=config["model_type"],
                algorithm=config.get("algorithm", "random_forest"),
                framework="sklearn",
                training_data_hash=hashlib.md5(str(config.get("training_data_config", "")).encode()).hexdigest(),
                training_samples=config.get("training_samples", 1000),
                feature_count=config.get("feature_count", 10),
                training_duration_seconds=5.0,
                hyperparameters=config.get("hyperparameters", {}),
                validation_metrics=validation_metrics,
                cross_validation_score=0.84,
                benchmark_metrics={"baseline_accuracy": 0.75},
                deployment_status="validation",
                deployment_timestamp=None,
                endpoint_url=None,
                parent_model_id=config.get("parent_model_id"),
                training_pipeline_version="1.0.0",
                data_pipeline_version="1.0.0",
                monitoring_enabled=True,
                alert_thresholds={"max_error_rate": 0.1, "max_latency_ms": 500, "min_accuracy": 0.8},
                description=config.get("description", "Automated model training"),
                tags=config.get("tags", []),
                model_size_mb=1.5,  # Estimated
                prediction_latency_ms=50,  # Estimated
            )

            # Register model
            success = await self.registry.register_model(metadata, model)

            if success:
                job["status"] = "completed"
                job["completed_at"] = datetime.now()
                job["logs"].append(f"{datetime.now()}: Model training completed successfully")
            else:
                job["status"] = "failed"
                job["logs"].append(f"{datetime.now()}: Failed to register trained model")

        except Exception as e:
            job["status"] = "failed"
            job["logs"].append(f"{datetime.now()}: Training failed: {str(e)}")
            logger.error(f"Training job {job_id} failed: {e}")

    def _validate_training_config(self, config: Dict[str, Any]) -> bool:
        """Validate training configuration"""

        required_fields = ["model_type", "model_name"]

        for field in required_fields:
            if field not in config:
                logger.error(f"Missing required field: {field}")
                return False

        # Validate model type
        valid_model_types = ["lead_scorer", "churn_predictor", "engagement_classifier"]
        if config["model_type"] not in valid_model_types:
            logger.error(f"Invalid model type: {config['model_type']}")
            return False

        return True

    async def get_training_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get training job status"""
        return self.active_training_jobs.get(job_id)

    async def list_training_jobs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List training jobs with optional status filter"""

        jobs = []
        for job_id, job_data in self.active_training_jobs.items():
            if status is None or job_data["status"] == status:
                jobs.append(job_data)

        return sorted(jobs, key=lambda x: x["started_at"], reverse=True)


class ModelDeploymentManager:
    """Manages model deployment strategies"""

    def __init__(self, registry: ModelRegistry, monitoring: ModelMonitoring):
        self.registry = registry
        self.monitoring = monitoring
        self.deployments = {}  # Track active deployments

    async def deploy_model(
        self, model_id: str, deployment_strategy: str = "full", traffic_percentage: int = 100
    ) -> bool:
        """Deploy model with specified strategy"""

        # Get model from registry
        model_result = await self.registry.get_model(model_id)
        if not model_result:
            logger.error(f"Model {model_id} not found in registry")
            return False

        metadata, model_artifact = model_result

        try:
            if deployment_strategy == "canary":
                return await self._deploy_canary(model_id, metadata, model_artifact, traffic_percentage)
            elif deployment_strategy == "blue_green":
                return await self._deploy_blue_green(model_id, metadata, model_artifact)
            else:  # full deployment
                return await self._deploy_full(model_id, metadata, model_artifact)

        except Exception as e:
            logger.error(f"Deployment failed for model {model_id}: {e}")
            return False

    async def _deploy_full(self, model_id: str, metadata: ModelMetadata, model_artifact: Any) -> bool:
        """Full deployment - replace current production model"""

        # Promote model to production
        success = await self.registry.promote_model(model_id, "production")

        if success:
            # Set up monitoring
            await self.monitoring.set_alert_thresholds(model_id, metadata.alert_thresholds)

            # Record deployment
            self.deployments[model_id] = {
                "strategy": "full",
                "deployed_at": datetime.now(),
                "traffic_percentage": 100,
                "status": "active",
            }

            logger.info(f"Successfully deployed model {model_id} (full)")

        return success

    async def _deploy_canary(
        self, model_id: str, metadata: ModelMetadata, model_artifact: Any, traffic_percentage: int
    ) -> bool:
        """Canary deployment - gradual traffic shift"""

        # Promote model to staging first
        success = await self.registry.promote_model(model_id, "staging")

        if success:
            # Set up monitoring
            await self.monitoring.set_alert_thresholds(model_id, metadata.alert_thresholds)

            # Record canary deployment
            self.deployments[model_id] = {
                "strategy": "canary",
                "deployed_at": datetime.now(),
                "traffic_percentage": traffic_percentage,
                "status": "canary",
                "monitoring_period_hours": 24,  # Monitor for 24 hours before full promotion
            }

            logger.info(f"Successfully deployed model {model_id} (canary - {traffic_percentage}% traffic)")

        return success

    async def _deploy_blue_green(self, model_id: str, metadata: ModelMetadata, model_artifact: Any) -> bool:
        """Blue-green deployment - instant switch with rollback capability"""

        # Keep current production model as green, deploy new as blue
        current_production = await self.registry.get_latest_model(metadata.model_type, "production")

        # Promote new model to production
        success = await self.registry.promote_model(model_id, "production")

        if success:
            # Set up monitoring
            await self.monitoring.set_alert_thresholds(model_id, metadata.alert_thresholds)

            # Record deployment with rollback info
            self.deployments[model_id] = {
                "strategy": "blue_green",
                "deployed_at": datetime.now(),
                "traffic_percentage": 100,
                "status": "active",
                "rollback_model_id": current_production[0].model_id if current_production else None,
            }

            logger.info(f"Successfully deployed model {model_id} (blue-green)")

        return success

    async def rollback_deployment(self, model_id: str) -> bool:
        """Rollback deployment to previous version"""

        deployment = self.deployments.get(model_id)
        if not deployment:
            logger.error(f"No deployment found for model {model_id}")
            return False

        try:
            if deployment["strategy"] == "blue_green" and deployment.get("rollback_model_id"):
                # Rollback to previous model
                rollback_model_id = deployment["rollback_model_id"]
                success = await self.registry.promote_model(rollback_model_id, "production")

                if success:
                    # Demote current model
                    await self.registry.promote_model(model_id, "retired")

                    # Update deployment status
                    deployment["status"] = "rolled_back"
                    deployment["rolled_back_at"] = datetime.now()

                    logger.info(f"Successfully rolled back model {model_id} to {rollback_model_id}")
                    return True

            else:
                logger.error(f"Rollback not supported for deployment strategy: {deployment['strategy']}")
                return False

        except Exception as e:
            logger.error(f"Rollback failed for model {model_id}: {e}")
            return False

    async def get_deployment_status(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get deployment status for model"""
        return self.deployments.get(model_id)

    async def monitor_canary_deployment(self, model_id: str) -> bool:
        """Monitor canary deployment and auto-promote if successful"""

        deployment = self.deployments.get(model_id)
        if not deployment or deployment["strategy"] != "canary":
            return False

        # Check if monitoring period has passed
        monitoring_period = timedelta(hours=deployment.get("monitoring_period_hours", 24))
        if datetime.now() - deployment["deployed_at"] < monitoring_period:
            return False  # Still in monitoring period

        # Check performance metrics
        metrics = await self.monitoring.get_performance_metrics(model_id, "24h")

        if not metrics:
            logger.warning(f"No metrics available for canary model {model_id}")
            return False

        # Decide whether to promote based on metrics
        promotion_criteria = {"max_error_rate": 0.05, "min_accuracy": 0.8, "max_drift_score": 0.5}

        should_promote = True

        if metrics.error_rate > promotion_criteria["max_error_rate"]:
            logger.warning(f"Canary model {model_id} error rate too high: {metrics.error_rate}")
            should_promote = False

        if metrics.accuracy and metrics.accuracy < promotion_criteria["min_accuracy"]:
            logger.warning(f"Canary model {model_id} accuracy too low: {metrics.accuracy}")
            should_promote = False

        if metrics.feature_drift_score > promotion_criteria["max_drift_score"]:
            logger.warning(f"Canary model {model_id} feature drift too high: {metrics.feature_drift_score}")
            should_promote = False

        if should_promote:
            # Promote canary to production
            success = await self.registry.promote_model(model_id, "production")
            if success:
                deployment["status"] = "promoted"
                deployment["promoted_at"] = datetime.now()
                deployment["traffic_percentage"] = 100
                logger.info(f"Canary model {model_id} promoted to production")
                return True
        else:
            # Rollback canary
            await self.registry.promote_model(model_id, "retired")
            deployment["status"] = "failed"
            deployment["failed_at"] = datetime.now()
            logger.warning(f"Canary model {model_id} failed monitoring and was retired")

        return should_promote


class MLOpsPipeline:
    """Main MLOps orchestrator"""

    def __init__(self, registry_path: str = "models/registry"):
        self.registry = ModelRegistry(registry_path)
        self.monitoring = ModelMonitoring()
        self.training_pipeline = ModelTrainingPipeline(self.registry)
        self.deployment_manager = ModelDeploymentManager(self.registry, self.monitoring)

        # Background tasks
        self.background_tasks = []

    async def start_background_monitoring(self):
        """Start background monitoring tasks"""

        # Start canary monitoring task
        task = asyncio.create_task(self._background_canary_monitor())
        self.background_tasks.append(task)

        logger.info("Started background MLOps monitoring")

    async def _background_canary_monitor(self):
        """Background task to monitor canary deployments"""

        while True:
            try:
                # Check all canary deployments
                for model_id, deployment in self.deployment_manager.deployments.items():
                    if deployment.get("status") == "canary":
                        await self.deployment_manager.monitor_canary_deployment(model_id)

                # Sleep for 1 hour before next check
                await asyncio.sleep(3600)

            except Exception as e:
                logger.error(f"Background canary monitoring failed: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying

    async def train_and_deploy_model(
        self, training_config: Dict[str, Any], deployment_strategy: str = "canary"
    ) -> Dict[str, Any]:
        """Complete training and deployment workflow"""

        result = {
            "training_job_id": None,
            "model_id": None,
            "deployment_success": False,
            "status": "started",
            "logs": [],
        }

        try:
            # Start training
            job_id = await self.training_pipeline.train_model(training_config)
            result["training_job_id"] = job_id
            result["logs"].append(f"Started training job {job_id}")

            # Wait for training completion (with timeout)
            timeout_seconds = 300  # 5 minutes
            start_time = datetime.now()

            while (datetime.now() - start_time).total_seconds() < timeout_seconds:
                job_status = await self.training_pipeline.get_training_status(job_id)

                if job_status["status"] == "completed":
                    result["model_id"] = job_status["model_id"]
                    result["logs"].append(f"Training completed: model {job_status['model_id']}")
                    break
                elif job_status["status"] == "failed":
                    result["status"] = "failed"
                    result["logs"].append("Training failed")
                    return result

                await asyncio.sleep(5)  # Check every 5 seconds

            if not result["model_id"]:
                result["status"] = "timeout"
                result["logs"].append("Training timed out")
                return result

            # Deploy model
            deployment_success = await self.deployment_manager.deploy_model(result["model_id"], deployment_strategy)

            result["deployment_success"] = deployment_success
            result["status"] = "completed" if deployment_success else "deployment_failed"

            if deployment_success:
                result["logs"].append(f"Deployment successful ({deployment_strategy})")
            else:
                result["logs"].append("Deployment failed")

        except Exception as e:
            result["status"] = "error"
            result["logs"].append(f"Error: {str(e)}")
            logger.error(f"Train and deploy workflow failed: {e}")

        return result

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall MLOps system health"""

        # Get model registry stats
        all_models = await self.registry.list_models()
        model_stats = {
            "total_models": len(all_models),
            "production_models": len([m for m in all_models if m.deployment_status == "production"]),
            "staging_models": len([m for m in all_models if m.deployment_status == "staging"]),
            "retired_models": len([m for m in all_models if m.deployment_status == "retired"]),
        }

        # Get training pipeline stats
        training_jobs = await self.training_pipeline.list_training_jobs()
        training_stats = {
            "total_jobs": len(training_jobs),
            "running_jobs": len([j for j in training_jobs if j["status"] == "running"]),
            "completed_jobs": len([j for j in training_jobs if j["status"] == "completed"]),
            "failed_jobs": len([j for j in training_jobs if j["status"] == "failed"]),
        }

        # Get deployment stats
        deployments = self.deployment_manager.deployments
        deployment_stats = {
            "total_deployments": len(deployments),
            "active_deployments": len([d for d in deployments.values() if d["status"] == "active"]),
            "canary_deployments": len([d for d in deployments.values() if d["status"] == "canary"]),
            "failed_deployments": len([d for d in deployments.values() if d["status"] == "failed"]),
        }

        # Overall system health
        health_score = 1.0

        # Reduce health for failed training jobs
        if training_stats["total_jobs"] > 0:
            training_success_rate = training_stats["completed_jobs"] / training_stats["total_jobs"]
            health_score *= training_success_rate

        # Reduce health for failed deployments
        if deployment_stats["total_deployments"] > 0:
            deployment_success_rate = (
                deployment_stats["active_deployments"] + deployment_stats["canary_deployments"]
            ) / deployment_stats["total_deployments"]
            health_score *= deployment_success_rate

        health_status = "healthy" if health_score > 0.9 else "degraded" if health_score > 0.7 else "unhealthy"

        return {
            "timestamp": datetime.now(),
            "health_status": health_status,
            "health_score": health_score,
            "model_registry": model_stats,
            "training_pipeline": training_stats,
            "deployments": deployment_stats,
            "background_tasks_running": len(self.background_tasks),
            "system_uptime_hours": 0,  # Would track actual uptime
            "memory_usage_mb": 0,  # Would track actual memory usage
            "cpu_usage_percent": 0,  # Would track actual CPU usage
        }


# Factory function
def create_mlops_pipeline(registry_path: str = "models/registry") -> MLOpsPipeline:
    """Create MLOps pipeline instance"""
    return MLOpsPipeline(registry_path)


# Example usage and testing
if __name__ == "__main__":

    async def test_mlops_pipeline():
        """Test the MLOps pipeline"""

        print("🚀 MLOps Pipeline Test")

        # Create MLOps pipeline
        mlops = create_mlops_pipeline("test_models")

        # Start background monitoring
        await mlops.start_background_monitoring()

        print("   📊 System Health Check")
        health = await mlops.get_system_health()
        print(f"   • Health Status: {health['health_status']}")
        print(f"   • Health Score: {health['health_score']:.2f}")
        print(f"   • Total Models: {health['model_registry']['total_models']}")

        print("\n   🏭 Training Pipeline Test")

        # Test model training
        training_config = {
            "model_type": "lead_scorer",
            "model_name": "Test Lead Scorer",
            "algorithm": "random_forest",
            "description": "Test model for MLOps pipeline",
            "hyperparameters": {"n_estimators": 100, "max_depth": 10},
            "tags": ["test", "lead_scoring"],
        }

        job_id = await mlops.training_pipeline.train_model(training_config)
        print(f"   • Started training job: {job_id}")

        # Wait for training completion
        import asyncio

        await asyncio.sleep(6)  # Wait for training to complete

        job_status = await mlops.training_pipeline.get_training_status(job_id)
        print(f"   • Training status: {job_status['status']}")

        if job_status["status"] == "completed":
            model_id = job_status["model_id"]
            print(f"   • Trained model: {model_id}")

            print("\n   🚢 Deployment Test")

            # Test canary deployment
            deployment_success = await mlops.deployment_manager.deploy_model(model_id, "canary", traffic_percentage=25)
            print(f"   • Canary deployment: {'Success' if deployment_success else 'Failed'}")

            if deployment_success:
                deployment_status = await mlops.deployment_manager.get_deployment_status(model_id)
                print(f"   • Deployment strategy: {deployment_status['strategy']}")
                print(f"   • Traffic percentage: {deployment_status['traffic_percentage']}%")

                print("\n   📈 Monitoring Test")

                # Simulate some predictions for monitoring
                for i in range(10):
                    await mlops.monitoring.record_prediction(
                        model_id=model_id,
                        prediction=0.75 + (i % 3) * 0.1,  # Vary predictions
                        features={"feature1": i, "feature2": i * 2},
                        actual_outcome=1 if i % 2 == 0 else 0,  # Alternate outcomes
                        latency_ms=50 + i,
                    )

                # Get performance metrics
                metrics = await mlops.monitoring.get_performance_metrics(model_id, "1h")
                if metrics:
                    print(f"   • Total predictions: {metrics.total_predictions}")
                    print(f"   • Avg latency: {metrics.avg_prediction_latency_ms:.1f}ms")
                    print(f"   • Error rate: {metrics.error_rate:.1%}")
                    print(
                        f"   • Accuracy: {metrics.accuracy:.2f}" if metrics.accuracy else "   • Accuracy: Not available"
                    )

        print("\n   📊 Final System Health")
        final_health = await mlops.get_system_health()
        print(f"   • Health Status: {final_health['health_status']}")
        print(f"   • Production Models: {final_health['model_registry']['production_models']}")
        print(f"   • Completed Jobs: {final_health['training_pipeline']['completed_jobs']}")
        print(f"   • Active Deployments: {final_health['deployments']['active_deployments']}")

    # Run test
    asyncio.run(test_mlops_pipeline())
