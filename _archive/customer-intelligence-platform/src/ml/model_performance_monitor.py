"""
Model Performance Monitoring and Automated Retraining System.

This module provides comprehensive model monitoring capabilities including:
- Real-time performance tracking and drift detection
- Automated retraining triggers and scheduling
- Model health monitoring and alerting
- Performance degradation detection
- A/B testing framework for model deployment
- Automated rollback mechanisms

Features:
- Continuous performance monitoring
- Statistical drift detection using KS test, PSI, and custom metrics
- Automated retraining workflows
- Model comparison and champion/challenger testing
- Performance alerting and notifications
- Historical performance tracking

Business Impact: Ensures optimal model performance through automated monitoring
Author: Customer Intelligence Platform Enhancement Team
Created: 2026-01-19
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum
import json
import uuid
from collections import defaultdict, deque
import warnings
from pathlib import Path

# Statistical libraries
from scipy import stats
from scipy.stats import ks_2samp, chi2_contingency
import joblib

# ML evaluation
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, mean_squared_error, mean_absolute_error, r2_score
)

# Internal imports
from .enhanced_model_trainer import EnhancedModelTrainer, EnhancedModelConfig, ModelPerformanceMetrics
from .scoring_pipeline import ModelType, ModelStatus
from ..utils.logger import get_logger
from ..database.service import DatabaseService

logger = get_logger(__name__)
warnings.filterwarnings("ignore", category=UserWarning)


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DriftType(Enum):
    """Types of model drift."""
    DATA_DRIFT = "data_drift"  # Input feature distribution changes
    CONCEPT_DRIFT = "concept_drift"  # Target variable relationship changes
    PREDICTION_DRIFT = "prediction_drift"  # Model output distribution changes
    PERFORMANCE_DRIFT = "performance_drift"  # Model performance degradation


class MonitoringStatus(Enum):
    """Model monitoring status."""
    HEALTHY = "healthy"
    WARNING = "warning"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    RETRAINING = "retraining"
    OFFLINE = "offline"


@dataclass
class DriftAlert:
    """Drift detection alert."""
    alert_id: str
    model_id: str
    model_type: ModelType
    drift_type: DriftType
    severity: AlertSeverity
    drift_score: float
    threshold: float
    affected_features: List[str]
    detection_timestamp: datetime
    description: str
    recommended_action: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelHealthMetrics:
    """Comprehensive model health metrics."""
    model_id: str
    model_type: ModelType
    health_score: float  # 0-100
    monitoring_status: MonitoringStatus
    
    # Performance metrics
    current_accuracy: float
    baseline_accuracy: float
    accuracy_drift: float
    
    # Drift metrics
    data_drift_score: float
    concept_drift_score: float
    prediction_drift_score: float
    
    # Volume metrics
    prediction_volume_24h: int
    prediction_volume_7d: int
    average_response_time_ms: float
    
    # Stability metrics
    error_rate: float
    null_prediction_rate: float
    feature_stability_score: float
    
    # Timestamps
    last_evaluation: datetime
    last_retrain: Optional[datetime]
    next_scheduled_retrain: Optional[datetime]
    
    # Alerts
    active_alerts: List[DriftAlert] = field(default_factory=list)
    recent_alerts: List[DriftAlert] = field(default_factory=list)


@dataclass
class RetrainingJob:
    """Automated retraining job configuration and status."""
    job_id: str
    model_id: str
    model_type: ModelType
    trigger_reason: str
    priority: str  # low, medium, high, critical
    
    # Job configuration
    training_config: EnhancedModelConfig
    training_data_start: datetime
    training_data_end: datetime
    
    # Status tracking
    status: str  # pending, running, completed, failed, cancelled
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    new_model_performance: Optional[ModelPerformanceMetrics] = None
    improvement_metrics: Dict[str, float] = field(default_factory=dict)
    deployment_decision: Optional[str] = None  # deploy, reject, a_b_test
    
    # Metadata
    triggered_by_alerts: List[str] = field(default_factory=list)
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)


class DriftDetector:
    """Advanced drift detection using multiple statistical methods."""
    
    def __init__(self):
        self.drift_thresholds = {
            DriftType.DATA_DRIFT: 0.05,  # KS test p-value threshold
            DriftType.CONCEPT_DRIFT: 0.1,  # Performance degradation threshold
            DriftType.PREDICTION_DRIFT: 0.05,  # Prediction distribution change
            DriftType.PERFORMANCE_DRIFT: 0.05  # Performance drop threshold
        }
    
    async def detect_data_drift(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        feature_subset: Optional[List[str]] = None
    ) -> Tuple[float, List[str], Dict[str, float]]:
        """Detect data drift using statistical tests."""
        
        if feature_subset:
            ref_features = reference_data[feature_subset]
            cur_features = current_data[feature_subset]
        else:
            # Use numeric features only
            numeric_features = reference_data.select_dtypes(include=[np.number]).columns
            ref_features = reference_data[numeric_features]
            cur_features = current_data[numeric_features]
        
        drift_scores = {}
        drifted_features = []
        
        for feature in ref_features.columns:
            try:
                # Kolmogorov-Smirnov test for continuous variables
                if ref_features[feature].dtype in [np.number]:
                    statistic, p_value = ks_2samp(
                        ref_features[feature].dropna(),
                        cur_features[feature].dropna()
                    )
                    drift_score = 1 - p_value  # Higher score = more drift
                    
                    if p_value < self.drift_thresholds[DriftType.DATA_DRIFT]:
                        drifted_features.append(feature)
                
                # Chi-square test for categorical variables
                else:
                    ref_counts = ref_features[feature].value_counts()
                    cur_counts = cur_features[feature].value_counts()
                    
                    # Align categories
                    all_categories = set(ref_counts.index) | set(cur_counts.index)
                    ref_aligned = [ref_counts.get(cat, 0) for cat in all_categories]
                    cur_aligned = [cur_counts.get(cat, 0) for cat in all_categories]
                    
                    if sum(ref_aligned) > 0 and sum(cur_aligned) > 0:
                        chi2, p_value, _, _ = chi2_contingency([ref_aligned, cur_aligned])
                        drift_score = min(1.0, chi2 / 100)  # Normalize chi2 score
                        
                        if p_value < self.drift_thresholds[DriftType.DATA_DRIFT]:
                            drifted_features.append(feature)
                    else:
                        drift_score = 0.0
                
                drift_scores[feature] = drift_score
                
            except Exception as e:
                logger.warning(f"Drift detection failed for feature {feature}: {e}")
                drift_scores[feature] = 0.0
        
        # Overall drift score (average of individual feature scores)
        overall_drift_score = np.mean(list(drift_scores.values())) if drift_scores else 0.0
        
        return overall_drift_score, drifted_features, drift_scores
    
    async def detect_concept_drift(
        self,
        model: Any,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        target_column: str
    ) -> Tuple[float, Dict[str, float]]:
        """Detect concept drift by comparing model performance."""
        
        if target_column not in reference_data.columns or target_column not in current_data.columns:
            return 0.0, {}
        
        try:
            # Prepare data
            ref_X = reference_data.drop([target_column], axis=1)
            ref_y = reference_data[target_column]
            cur_X = current_data.drop([target_column], axis=1)
            cur_y = current_data[target_column]
            
            # Align features
            common_features = list(set(ref_X.columns) & set(cur_X.columns))
            ref_X = ref_X[common_features]
            cur_X = cur_X[common_features]
            
            # Make predictions
            ref_predictions = model.predict(ref_X)
            cur_predictions = model.predict(cur_X)
            
            # Calculate performance metrics
            ref_accuracy = accuracy_score(ref_y, ref_predictions)
            cur_accuracy = accuracy_score(cur_y, cur_predictions)
            
            # Calculate drift metrics
            accuracy_drift = ref_accuracy - cur_accuracy
            concept_drift_score = max(0, accuracy_drift)  # Only positive drift
            
            metrics = {
                'reference_accuracy': ref_accuracy,
                'current_accuracy': cur_accuracy,
                'accuracy_drift': accuracy_drift,
                'concept_drift_score': concept_drift_score
            }
            
            return concept_drift_score, metrics
            
        except Exception as e:
            logger.error(f"Concept drift detection failed: {e}")
            return 0.0, {}
    
    async def detect_prediction_drift(
        self,
        reference_predictions: np.ndarray,
        current_predictions: np.ndarray
    ) -> Tuple[float, Dict[str, float]]:
        """Detect drift in model predictions using statistical tests."""
        
        try:
            # Kolmogorov-Smirnov test on prediction distributions
            statistic, p_value = ks_2samp(reference_predictions, current_predictions)
            
            # Population Stability Index (PSI)
            psi_score = self._calculate_psi(reference_predictions, current_predictions)
            
            # Combine metrics
            prediction_drift_score = max(1 - p_value, psi_score / 2.0)  # Normalize PSI
            
            metrics = {
                'ks_statistic': statistic,
                'ks_p_value': p_value,
                'psi_score': psi_score,
                'prediction_drift_score': prediction_drift_score
            }
            
            return prediction_drift_score, metrics
            
        except Exception as e:
            logger.error(f"Prediction drift detection failed: {e}")
            return 0.0, {}
    
    def _calculate_psi(
        self,
        reference_data: np.ndarray,
        current_data: np.ndarray,
        bins: int = 10
    ) -> float:
        """Calculate Population Stability Index (PSI)."""
        
        try:
            # Create bins based on reference data
            bin_edges = np.histogram_bin_edges(reference_data, bins=bins)
            
            # Calculate distributions
            ref_counts, _ = np.histogram(reference_data, bins=bin_edges)
            cur_counts, _ = np.histogram(current_data, bins=bin_edges)
            
            # Convert to proportions
            ref_props = ref_counts / len(reference_data)
            cur_props = cur_counts / len(current_data)
            
            # Calculate PSI
            psi = 0.0
            for i in range(len(ref_props)):
                if ref_props[i] > 0 and cur_props[i] > 0:
                    psi += (cur_props[i] - ref_props[i]) * np.log(cur_props[i] / ref_props[i])
                elif ref_props[i] > 0 and cur_props[i] == 0:
                    psi += 0.1  # Penalty for missing data in current
                elif ref_props[i] == 0 and cur_props[i] > 0:
                    psi += cur_props[i] * 4  # Penalty for new data in current
            
            return psi
            
        except Exception as e:
            logger.warning(f"PSI calculation failed: {e}")
            return 0.0


class ModelPerformanceMonitor:
    """Comprehensive model performance monitoring system."""
    
    def __init__(self, database_service: DatabaseService = None):
        self.db_service = database_service or DatabaseService()
        self.drift_detector = DriftDetector()
        self.model_trainer = EnhancedModelTrainer()
        
        # Monitoring state
        self.model_health_cache: Dict[str, ModelHealthMetrics] = {}
        self.active_alerts: Dict[str, List[DriftAlert]] = defaultdict(list)
        self.retraining_jobs: Dict[str, RetrainingJob] = {}
        
        # Monitoring configuration
        self.monitoring_interval_minutes = 60  # Check every hour
        self.performance_check_interval_hours = 24  # Daily performance check
        self.alert_cooldown_hours = 6  # Prevent alert spam
        
        # Performance thresholds
        self.performance_thresholds = {
            'accuracy_drop': 0.05,  # 5% accuracy drop triggers alert
            'error_rate': 0.1,  # 10% error rate
            'response_time_ms': 5000,  # 5 second response time
            'null_rate': 0.05,  # 5% null prediction rate
            'drift_score': 0.1  # Drift score threshold
        }
        
        # Automated retraining triggers
        self.retrain_triggers = {
            'performance_drop': 0.1,  # 10% performance drop
            'critical_drift': 0.2,  # High drift score
            'error_rate_spike': 0.15,  # 15% error rate
            'scheduled_interval': timedelta(days=7)  # Weekly retraining
        }
        
        logger.info("ModelPerformanceMonitor initialized")
    
    async def start_monitoring(self, model_ids: List[str]):
        """Start monitoring for specified models."""
        logger.info(f"Starting performance monitoring for {len(model_ids)} models")
        
        # Initialize model health metrics
        for model_id in model_ids:
            await self._initialize_model_health(model_id)
        
        # Start monitoring tasks
        monitoring_tasks = [
            asyncio.create_task(self._performance_monitoring_loop(model_ids)),
            asyncio.create_task(self._drift_monitoring_loop(model_ids)),
            asyncio.create_task(self._retraining_scheduler_loop(model_ids)),
            asyncio.create_task(self._alert_management_loop())
        ]
        
        await asyncio.gather(*monitoring_tasks)
    
    async def _initialize_model_health(self, model_id: str):
        """Initialize health metrics for a model."""
        
        try:
            # Get model information from database
            model_info = await self.db_service.get_model_info(model_id)
            if not model_info:
                logger.warning(f"Model {model_id} not found")
                return
            
            # Initialize health metrics
            health_metrics = ModelHealthMetrics(
                model_id=model_id,
                model_type=ModelType(model_info.get('model_type', 'lead_scoring')),
                health_score=100.0,
                monitoring_status=MonitoringStatus.HEALTHY,
                current_accuracy=model_info.get('accuracy', 0.0),
                baseline_accuracy=model_info.get('accuracy', 0.0),
                accuracy_drift=0.0,
                data_drift_score=0.0,
                concept_drift_score=0.0,
                prediction_drift_score=0.0,
                prediction_volume_24h=0,
                prediction_volume_7d=0,
                average_response_time_ms=0.0,
                error_rate=0.0,
                null_prediction_rate=0.0,
                feature_stability_score=100.0,
                last_evaluation=datetime.now(),
                last_retrain=datetime.now(),
                next_scheduled_retrain=datetime.now() + self.retrain_triggers['scheduled_interval']
            )
            
            self.model_health_cache[model_id] = health_metrics
            logger.info(f"Initialized health monitoring for model {model_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize health monitoring for model {model_id}: {e}")
    
    async def _performance_monitoring_loop(self, model_ids: List[str]):
        """Main performance monitoring loop."""
        
        while True:
            try:
                for model_id in model_ids:
                    await self._check_model_performance(model_id)
                    await asyncio.sleep(1)  # Prevent overwhelming the system
                
                await asyncio.sleep(self.monitoring_interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Performance monitoring loop error: {e}")
                await asyncio.sleep(60)  # Short retry delay
    
    async def _drift_monitoring_loop(self, model_ids: List[str]):
        """Drift detection monitoring loop."""
        
        while True:
            try:
                for model_id in model_ids:
                    await self._check_model_drift(model_id)
                    await asyncio.sleep(1)
                
                await asyncio.sleep(self.monitoring_interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Drift monitoring loop error: {e}")
                await asyncio.sleep(60)
    
    async def _retraining_scheduler_loop(self, model_ids: List[str]):
        """Automated retraining scheduler loop."""
        
        while True:
            try:
                for model_id in model_ids:
                    await self._check_retraining_triggers(model_id)
                    await asyncio.sleep(1)
                
                await asyncio.sleep(self.performance_check_interval_hours * 3600)
                
            except Exception as e:
                logger.error(f"Retraining scheduler error: {e}")
                await asyncio.sleep(3600)  # 1 hour retry delay
    
    async def _alert_management_loop(self):
        """Alert management and cleanup loop."""
        
        while True:
            try:
                await self._cleanup_old_alerts()
                await self._consolidate_alerts()
                await self._send_alert_summaries()
                
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error(f"Alert management loop error: {e}")
                await asyncio.sleep(3600)
    
    async def _check_model_performance(self, model_id: str):
        """Check model performance metrics."""
        
        try:
            if model_id not in self.model_health_cache:
                await self._initialize_model_health(model_id)
                return
            
            health_metrics = self.model_health_cache[model_id]
            
            # Get recent prediction data
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            recent_predictions = await self.db_service.get_model_predictions(
                model_id, start_time, end_time
            )
            
            if not recent_predictions:
                logger.debug(f"No recent predictions found for model {model_id}")
                return
            
            # Calculate performance metrics
            predictions_df = pd.DataFrame(recent_predictions)
            
            # Update volume metrics
            health_metrics.prediction_volume_24h = len(predictions_df)
            health_metrics.prediction_volume_7d = await self._get_prediction_volume_7d(model_id)
            
            # Calculate error rate
            if 'error' in predictions_df.columns:
                health_metrics.error_rate = predictions_df['error'].mean()
            
            # Calculate null prediction rate
            if 'prediction' in predictions_df.columns:
                null_predictions = predictions_df['prediction'].isnull().sum()
                health_metrics.null_prediction_rate = null_predictions / len(predictions_df)
            
            # Calculate response time
            if 'response_time_ms' in predictions_df.columns:
                health_metrics.average_response_time_ms = predictions_df['response_time_ms'].mean()
            
            # Calculate current accuracy if we have ground truth
            if 'actual' in predictions_df.columns and 'prediction' in predictions_df.columns:
                actual_values = predictions_df['actual'].dropna()
                predicted_values = predictions_df['prediction'].dropna()
                
                if len(actual_values) > 0 and len(predicted_values) > 0:
                    # Align indices
                    common_idx = actual_values.index.intersection(predicted_values.index)
                    if len(common_idx) > 0:
                        health_metrics.current_accuracy = accuracy_score(
                            actual_values[common_idx],
                            predicted_values[common_idx].round()
                        )
                        health_metrics.accuracy_drift = (
                            health_metrics.baseline_accuracy - health_metrics.current_accuracy
                        )
            
            # Update overall health score
            health_metrics.health_score = self._calculate_health_score(health_metrics)
            
            # Update monitoring status
            health_metrics.monitoring_status = self._determine_monitoring_status(health_metrics)
            
            # Update timestamp
            health_metrics.last_evaluation = datetime.now()
            
            # Check for alerts
            await self._check_performance_alerts(model_id, health_metrics)
            
            logger.debug(f"Updated performance metrics for model {model_id}")
            
        except Exception as e:
            logger.error(f"Performance check failed for model {model_id}: {e}")
    
    async def _check_model_drift(self, model_id: str):
        """Check for model drift."""
        
        try:
            if model_id not in self.model_health_cache:
                return
            
            health_metrics = self.model_health_cache[model_id]
            
            # Get baseline training data
            baseline_data = await self.db_service.get_model_training_data(model_id)
            if baseline_data is None or baseline_data.empty:
                logger.debug(f"No baseline data found for model {model_id}")
                return
            
            # Get recent prediction data
            end_time = datetime.now()
            start_time = end_time - timedelta(days=7)
            
            recent_data = await self.db_service.get_recent_prediction_features(
                model_id, start_time, end_time
            )
            
            if recent_data is None or recent_data.empty:
                logger.debug(f"No recent data found for model {model_id}")
                return
            
            # Load model
            model = await self.db_service.load_model(model_id)
            if model is None:
                logger.warning(f"Could not load model {model_id}")
                return
            
            # Detect data drift
            data_drift_score, drifted_features, feature_drift_scores = await self.drift_detector.detect_data_drift(
                baseline_data, recent_data
            )
            health_metrics.data_drift_score = data_drift_score
            
            # Detect concept drift (if we have target values)
            if 'target' in recent_data.columns:
                concept_drift_score, concept_metrics = await self.drift_detector.detect_concept_drift(
                    model, baseline_data, recent_data, 'target'
                )
                health_metrics.concept_drift_score = concept_drift_score
            
            # Detect prediction drift
            if len(baseline_data) > 0 and len(recent_data) > 0:
                try:
                    baseline_features = baseline_data.select_dtypes(include=[np.number])
                    recent_features = recent_data.select_dtypes(include=[np.number])
                    
                    # Align features
                    common_features = list(set(baseline_features.columns) & set(recent_features.columns))
                    if common_features:
                        baseline_predictions = model.predict(baseline_features[common_features])
                        recent_predictions = model.predict(recent_features[common_features])
                        
                        prediction_drift_score, prediction_metrics = await self.drift_detector.detect_prediction_drift(
                            baseline_predictions, recent_predictions
                        )
                        health_metrics.prediction_drift_score = prediction_drift_score
                except Exception as e:
                    logger.debug(f"Prediction drift detection failed for model {model_id}: {e}")
            
            # Generate drift alerts
            await self._check_drift_alerts(model_id, health_metrics, drifted_features)
            
            logger.debug(f"Checked drift for model {model_id}")
            
        except Exception as e:
            logger.error(f"Drift check failed for model {model_id}: {e}")
    
    async def _check_retraining_triggers(self, model_id: str):
        """Check if model needs retraining."""
        
        try:
            if model_id not in self.model_health_cache:
                return
            
            health_metrics = self.model_health_cache[model_id]
            
            # Check retraining triggers
            triggers = []
            
            # 1. Performance degradation
            if health_metrics.accuracy_drift > self.retrain_triggers['performance_drop']:
                triggers.append(f"Performance drop: {health_metrics.accuracy_drift:.3f}")
            
            # 2. High drift scores
            if health_metrics.data_drift_score > self.retrain_triggers['critical_drift']:
                triggers.append(f"Data drift: {health_metrics.data_drift_score:.3f}")
            
            if health_metrics.concept_drift_score > self.retrain_triggers['critical_drift']:
                triggers.append(f"Concept drift: {health_metrics.concept_drift_score:.3f}")
            
            # 3. High error rate
            if health_metrics.error_rate > self.retrain_triggers['error_rate_spike']:
                triggers.append(f"Error rate spike: {health_metrics.error_rate:.3f}")
            
            # 4. Scheduled retraining
            if (health_metrics.next_scheduled_retrain and 
                datetime.now() > health_metrics.next_scheduled_retrain):
                triggers.append("Scheduled retraining interval reached")
            
            # 5. Critical monitoring status
            if health_metrics.monitoring_status == MonitoringStatus.CRITICAL:
                triggers.append("Critical monitoring status")
            
            # Trigger retraining if needed
            if triggers:
                await self._trigger_retraining(model_id, triggers)
            
        except Exception as e:
            logger.error(f"Retraining trigger check failed for model {model_id}: {e}")
    
    async def _trigger_retraining(self, model_id: str, trigger_reasons: List[str]):
        """Trigger automated model retraining."""
        
        try:
            # Check if retraining is already in progress
            active_jobs = [job for job in self.retraining_jobs.values() 
                          if job.model_id == model_id and job.status in ['pending', 'running']]
            
            if active_jobs:
                logger.info(f"Retraining already in progress for model {model_id}")
                return
            
            health_metrics = self.model_health_cache[model_id]
            
            # Determine priority based on trigger severity
            priority = "high" if any("critical" in reason.lower() or "spike" in reason.lower() 
                               for reason in trigger_reasons) else "medium"
            
            # Get original model configuration
            model_config = await self.db_service.get_model_config(model_id)
            if not model_config:
                logger.error(f"Could not retrieve configuration for model {model_id}")
                return
            
            # Create retraining job
            job_id = f"retrain_{model_id}_{int(datetime.now().timestamp())}"
            
            retraining_job = RetrainingJob(
                job_id=job_id,
                model_id=model_id,
                model_type=health_metrics.model_type,
                trigger_reason="; ".join(trigger_reasons),
                priority=priority,
                training_config=model_config,
                training_data_start=datetime.now() - timedelta(days=90),  # 3 months of data
                training_data_end=datetime.now(),
                status="pending",
                created_at=datetime.now(),
                triggered_by_alerts=[alert.alert_id for alert in health_metrics.active_alerts]
            )
            
            self.retraining_jobs[job_id] = retraining_job
            
            # Update model status
            health_metrics.monitoring_status = MonitoringStatus.RETRAINING
            
            # Execute retraining asynchronously
            asyncio.create_task(self._execute_retraining(job_id))
            
            logger.info(f"Triggered retraining for model {model_id}, job ID: {job_id}")
            logger.info(f"Trigger reasons: {trigger_reasons}")
            
        except Exception as e:
            logger.error(f"Failed to trigger retraining for model {model_id}: {e}")
    
    async def _execute_retraining(self, job_id: str):
        """Execute automated retraining job."""
        
        try:
            job = self.retraining_jobs[job_id]
            job.status = "running"
            job.started_at = datetime.now()
            job.logs.append(f"Started retraining at {job.started_at}")
            
            logger.info(f"Executing retraining job {job_id} for model {job.model_id}")
            
            # Get training data
            training_data = await self.db_service.get_training_data_range(
                job.model_id, job.training_data_start, job.training_data_end
            )
            
            if training_data is None or training_data.empty:
                job.status = "failed"
                job.logs.append("No training data found")
                logger.error(f"No training data found for retraining job {job_id}")
                return
            
            job.logs.append(f"Retrieved {len(training_data)} training samples")
            
            # Train new model
            new_model, new_metrics = await self.model_trainer.train_enhanced_model(
                training_data, job.training_config
            )
            
            job.new_model_performance = new_metrics
            job.logs.append(f"New model trained with accuracy: {new_metrics.accuracy:.3f}")
            
            # Compare with existing model
            current_metrics = self.model_health_cache[job.model_id]
            improvement_metrics = {
                'accuracy_improvement': new_metrics.accuracy - current_metrics.current_accuracy,
                'precision_improvement': new_metrics.precision - (current_metrics.baseline_accuracy),  # Approximate
                'auc_improvement': new_metrics.auc_score - 0.5  # Placeholder comparison
            }
            
            job.improvement_metrics = improvement_metrics
            
            # Make deployment decision
            if improvement_metrics['accuracy_improvement'] > 0.02:  # 2% improvement threshold
                job.deployment_decision = "deploy"
                await self._deploy_retrained_model(job_id, new_model, new_metrics)
            elif improvement_metrics['accuracy_improvement'] > 0.005:  # 0.5% improvement
                job.deployment_decision = "a_b_test"
                await self._setup_ab_test(job_id, new_model, new_metrics)
            else:
                job.deployment_decision = "reject"
                job.logs.append("New model performance insufficient for deployment")
            
            job.status = "completed"
            job.completed_at = datetime.now()
            
            logger.info(f"Retraining job {job_id} completed with decision: {job.deployment_decision}")
            
        except Exception as e:
            job.status = "failed"
            job.logs.append(f"Retraining failed: {str(e)}")
            logger.error(f"Retraining job {job_id} failed: {e}")
    
    async def _deploy_retrained_model(self, job_id: str, new_model: Any, new_metrics: ModelPerformanceMetrics):
        """Deploy retrained model to production."""
        
        try:
            job = self.retraining_jobs[job_id]
            
            # Save new model
            model_path = f"models/{new_metrics.model_id}.joblib"
            joblib.dump(new_model, model_path)
            
            # Update database with new model
            await self.db_service.update_production_model(
                job.model_id, new_metrics.model_id, asdict(new_metrics)
            )
            
            # Update health metrics
            health_metrics = self.model_health_cache[job.model_id]
            health_metrics.current_accuracy = new_metrics.accuracy
            health_metrics.baseline_accuracy = new_metrics.accuracy
            health_metrics.accuracy_drift = 0.0
            health_metrics.last_retrain = datetime.now()
            health_metrics.next_scheduled_retrain = datetime.now() + self.retrain_triggers['scheduled_interval']
            health_metrics.monitoring_status = MonitoringStatus.HEALTHY
            
            # Clear active alerts
            health_metrics.active_alerts = []
            
            job.logs.append("Model deployed to production")
            logger.info(f"Successfully deployed retrained model for job {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to deploy retrained model for job {job_id}: {e}")
            job.logs.append(f"Deployment failed: {str(e)}")
    
    async def _setup_ab_test(self, job_id: str, new_model: Any, new_metrics: ModelPerformanceMetrics):
        """Set up A/B test for retrained model."""
        
        try:
            job = self.retraining_jobs[job_id]
            
            # Save challenger model
            challenger_path = f"models/challenger_{new_metrics.model_id}.joblib"
            joblib.dump(new_model, challenger_path)
            
            # Set up A/B test configuration
            ab_test_config = {
                'champion_model_id': job.model_id,
                'challenger_model_id': new_metrics.model_id,
                'traffic_split': 0.1,  # 10% to challenger
                'test_duration_days': 7,
                'success_metrics': ['accuracy', 'precision', 'auc_score'],
                'statistical_significance_threshold': 0.05
            }
            
            # Store A/B test configuration
            await self.db_service.create_ab_test(ab_test_config)
            
            job.logs.append("A/B test configured with 10% traffic to challenger")
            logger.info(f"A/B test set up for job {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to set up A/B test for job {job_id}: {e}")
            job.logs.append(f"A/B test setup failed: {str(e)}")
    
    def _calculate_health_score(self, health_metrics: ModelHealthMetrics) -> float:
        """Calculate overall model health score (0-100)."""
        
        # Base score
        score = 100.0
        
        # Accuracy drift penalty
        score -= min(50, health_metrics.accuracy_drift * 500)  # Max 50 point penalty
        
        # Error rate penalty
        score -= min(30, health_metrics.error_rate * 300)  # Max 30 point penalty
        
        # Response time penalty
        if health_metrics.average_response_time_ms > self.performance_thresholds['response_time_ms']:
            score -= 10
        
        # Drift penalties
        score -= min(20, health_metrics.data_drift_score * 100)
        score -= min(20, health_metrics.concept_drift_score * 100)
        score -= min(10, health_metrics.prediction_drift_score * 100)
        
        # Null prediction penalty
        score -= min(15, health_metrics.null_prediction_rate * 150)
        
        return max(0.0, score)
    
    def _determine_monitoring_status(self, health_metrics: ModelHealthMetrics) -> MonitoringStatus:
        """Determine monitoring status based on health metrics."""
        
        if health_metrics.health_score >= 90:
            return MonitoringStatus.HEALTHY
        elif health_metrics.health_score >= 70:
            return MonitoringStatus.WARNING
        elif health_metrics.health_score >= 50:
            return MonitoringStatus.DEGRADED
        else:
            return MonitoringStatus.CRITICAL
    
    async def _check_performance_alerts(self, model_id: str, health_metrics: ModelHealthMetrics):
        """Check for performance-based alerts."""
        
        alerts_to_create = []
        
        # Accuracy drop alert
        if health_metrics.accuracy_drift > self.performance_thresholds['accuracy_drop']:
            alerts_to_create.append({
                'drift_type': DriftType.PERFORMANCE_DRIFT,
                'severity': AlertSeverity.HIGH if health_metrics.accuracy_drift > 0.1 else AlertSeverity.MEDIUM,
                'drift_score': health_metrics.accuracy_drift,
                'threshold': self.performance_thresholds['accuracy_drop'],
                'description': f"Model accuracy dropped by {health_metrics.accuracy_drift:.1%}",
                'recommended_action': "Consider retraining model with recent data"
            })
        
        # Error rate alert
        if health_metrics.error_rate > self.performance_thresholds['error_rate']:
            alerts_to_create.append({
                'drift_type': DriftType.PERFORMANCE_DRIFT,
                'severity': AlertSeverity.CRITICAL if health_metrics.error_rate > 0.2 else AlertSeverity.HIGH,
                'drift_score': health_metrics.error_rate,
                'threshold': self.performance_thresholds['error_rate'],
                'description': f"High error rate: {health_metrics.error_rate:.1%}",
                'recommended_action': "Investigate model failures and data quality issues"
            })
        
        # Response time alert
        if health_metrics.average_response_time_ms > self.performance_thresholds['response_time_ms']:
            alerts_to_create.append({
                'drift_type': DriftType.PERFORMANCE_DRIFT,
                'severity': AlertSeverity.MEDIUM,
                'drift_score': health_metrics.average_response_time_ms / 1000,
                'threshold': self.performance_thresholds['response_time_ms'] / 1000,
                'description': f"Slow response time: {health_metrics.average_response_time_ms:.0f}ms",
                'recommended_action': "Optimize model inference or infrastructure"
            })
        
        # Create alerts
        for alert_data in alerts_to_create:
            await self._create_alert(model_id, health_metrics.model_type, alert_data)
    
    async def _check_drift_alerts(self, model_id: str, health_metrics: ModelHealthMetrics, drifted_features: List[str]):
        """Check for drift-based alerts."""
        
        alerts_to_create = []
        
        # Data drift alert
        if health_metrics.data_drift_score > self.performance_thresholds['drift_score']:
            alerts_to_create.append({
                'drift_type': DriftType.DATA_DRIFT,
                'severity': AlertSeverity.HIGH if health_metrics.data_drift_score > 0.2 else AlertSeverity.MEDIUM,
                'drift_score': health_metrics.data_drift_score,
                'threshold': self.performance_thresholds['drift_score'],
                'affected_features': drifted_features,
                'description': f"Data drift detected in {len(drifted_features)} features",
                'recommended_action': "Analyze feature distributions and consider retraining"
            })
        
        # Concept drift alert
        if health_metrics.concept_drift_score > self.performance_thresholds['drift_score']:
            alerts_to_create.append({
                'drift_type': DriftType.CONCEPT_DRIFT,
                'severity': AlertSeverity.HIGH,
                'drift_score': health_metrics.concept_drift_score,
                'threshold': self.performance_thresholds['drift_score'],
                'affected_features': [],
                'description': f"Concept drift detected: model performance degraded",
                'recommended_action': "Immediate retraining recommended"
            })
        
        # Prediction drift alert
        if health_metrics.prediction_drift_score > self.performance_thresholds['drift_score']:
            alerts_to_create.append({
                'drift_type': DriftType.PREDICTION_DRIFT,
                'severity': AlertSeverity.MEDIUM,
                'drift_score': health_metrics.prediction_drift_score,
                'threshold': self.performance_thresholds['drift_score'],
                'affected_features': [],
                'description': f"Prediction distribution has shifted",
                'recommended_action': "Monitor closely and consider retraining"
            })
        
        # Create alerts
        for alert_data in alerts_to_create:
            await self._create_alert(model_id, health_metrics.model_type, alert_data)
    
    async def _create_alert(self, model_id: str, model_type: ModelType, alert_data: Dict[str, Any]):
        """Create and store a drift alert."""
        
        try:
            # Check alert cooldown to prevent spam
            recent_alerts = [
                alert for alert in self.active_alerts[model_id]
                if (alert.drift_type == alert_data['drift_type'] and
                    datetime.now() - alert.detection_timestamp < timedelta(hours=self.alert_cooldown_hours))
            ]
            
            if recent_alerts:
                logger.debug(f"Alert cooldown active for model {model_id}, type {alert_data['drift_type']}")
                return
            
            # Create alert
            alert = DriftAlert(
                alert_id=str(uuid.uuid4()),
                model_id=model_id,
                model_type=model_type,
                drift_type=alert_data['drift_type'],
                severity=alert_data['severity'],
                drift_score=alert_data['drift_score'],
                threshold=alert_data['threshold'],
                affected_features=alert_data.get('affected_features', []),
                detection_timestamp=datetime.now(),
                description=alert_data['description'],
                recommended_action=alert_data['recommended_action']
            )
            
            # Store alert
            self.active_alerts[model_id].append(alert)
            
            # Update model health metrics
            if model_id in self.model_health_cache:
                self.model_health_cache[model_id].active_alerts.append(alert)
            
            # Save to database
            await self.db_service.store_alert(asdict(alert))
            
            logger.info(f"Created {alert.severity.value} alert for model {model_id}: {alert.description}")
            
        except Exception as e:
            logger.error(f"Failed to create alert for model {model_id}: {e}")
    
    async def _cleanup_old_alerts(self):
        """Clean up old alerts to prevent memory buildup."""
        
        cutoff_time = datetime.now() - timedelta(days=7)
        
        for model_id, alerts in list(self.active_alerts.items()):
            # Move old alerts to recent alerts and remove from active
            old_alerts = [alert for alert in alerts if alert.detection_timestamp < cutoff_time]
            active_alerts = [alert for alert in alerts if alert.detection_timestamp >= cutoff_time]
            
            self.active_alerts[model_id] = active_alerts
            
            # Update model health cache
            if model_id in self.model_health_cache:
                health_metrics = self.model_health_cache[model_id]
                health_metrics.active_alerts = active_alerts
                health_metrics.recent_alerts.extend(old_alerts)
                
                # Limit recent alerts to last 50
                health_metrics.recent_alerts = health_metrics.recent_alerts[-50:]
    
    async def _consolidate_alerts(self):
        """Consolidate similar alerts to reduce noise."""
        
        for model_id, alerts in self.active_alerts.items():
            if len(alerts) <= 1:
                continue
            
            # Group alerts by type and severity
            alert_groups = defaultdict(list)
            for alert in alerts:
                key = (alert.drift_type, alert.severity)
                alert_groups[key].append(alert)
            
            # Consolidate groups with multiple alerts
            consolidated_alerts = []
            for (drift_type, severity), group_alerts in alert_groups.items():
                if len(group_alerts) > 1:
                    # Create consolidated alert
                    consolidated_alert = DriftAlert(
                        alert_id=str(uuid.uuid4()),
                        model_id=model_id,
                        model_type=group_alerts[0].model_type,
                        drift_type=drift_type,
                        severity=severity,
                        drift_score=max(alert.drift_score for alert in group_alerts),
                        threshold=group_alerts[0].threshold,
                        affected_features=list(set().union(*(alert.affected_features for alert in group_alerts))),
                        detection_timestamp=max(alert.detection_timestamp for alert in group_alerts),
                        description=f"Multiple {drift_type.value} issues detected ({len(group_alerts)} alerts)",
                        recommended_action=group_alerts[0].recommended_action,
                        metadata={'consolidated_count': len(group_alerts)}
                    )
                    consolidated_alerts.append(consolidated_alert)
                else:
                    consolidated_alerts.extend(group_alerts)
            
            self.active_alerts[model_id] = consolidated_alerts
    
    async def _send_alert_summaries(self):
        """Send alert summaries (placeholder for notification system)."""
        
        # Count alerts by severity
        alert_summary = defaultdict(int)
        for alerts in self.active_alerts.values():
            for alert in alerts:
                alert_summary[alert.severity] += 1
        
        if alert_summary:
            logger.info(f"Alert Summary - Critical: {alert_summary[AlertSeverity.CRITICAL]}, "
                       f"High: {alert_summary[AlertSeverity.HIGH]}, "
                       f"Medium: {alert_summary[AlertSeverity.MEDIUM]}, "
                       f"Low: {alert_summary[AlertSeverity.LOW]}")
            
            # In a real system, this would send notifications via email, Slack, etc.
    
    async def _get_prediction_volume_7d(self, model_id: str) -> int:
        """Get 7-day prediction volume for a model."""
        
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=7)
            
            predictions = await self.db_service.get_model_predictions(
                model_id, start_time, end_time
            )
            
            return len(predictions) if predictions else 0
            
        except Exception as e:
            logger.debug(f"Failed to get 7d prediction volume for model {model_id}: {e}")
            return 0
    
    # Public API methods
    
    async def get_model_health(self, model_id: str) -> Optional[ModelHealthMetrics]:
        """Get current health metrics for a model."""
        return self.model_health_cache.get(model_id)
    
    async def get_all_model_health(self) -> Dict[str, ModelHealthMetrics]:
        """Get health metrics for all monitored models."""
        return self.model_health_cache.copy()
    
    async def get_active_alerts(self, model_id: Optional[str] = None) -> List[DriftAlert]:
        """Get active alerts for a specific model or all models."""
        
        if model_id:
            return self.active_alerts.get(model_id, [])
        else:
            all_alerts = []
            for alerts in self.active_alerts.values():
                all_alerts.extend(alerts)
            return all_alerts
    
    async def get_retraining_jobs(self, status: Optional[str] = None) -> List[RetrainingJob]:
        """Get retraining jobs, optionally filtered by status."""
        
        jobs = list(self.retraining_jobs.values())
        
        if status:
            jobs = [job for job in jobs if job.status == status]
        
        return jobs
    
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        
        for model_id, alerts in self.active_alerts.items():
            for i, alert in enumerate(alerts):
                if alert.alert_id == alert_id:
                    # Move to recent alerts
                    acknowledged_alert = alerts.pop(i)
                    
                    if model_id in self.model_health_cache:
                        self.model_health_cache[model_id].recent_alerts.append(acknowledged_alert)
                    
                    logger.info(f"Acknowledged alert {alert_id}")
                    return True
        
        return False
    
    async def manual_retrain_trigger(self, model_id: str, reason: str) -> str:
        """Manually trigger retraining for a model."""
        
        try:
            await self._trigger_retraining(model_id, [f"Manual trigger: {reason}"])
            
            # Find the latest job for this model
            latest_job = None
            for job in self.retraining_jobs.values():
                if job.model_id == model_id:
                    if latest_job is None or job.created_at > latest_job.created_at:
                        latest_job = job
            
            return latest_job.job_id if latest_job else ""
            
        except Exception as e:
            logger.error(f"Manual retrain trigger failed for model {model_id}: {e}")
            raise


# Factory function
def create_performance_monitor(database_service: DatabaseService = None) -> ModelPerformanceMonitor:
    """Create a model performance monitor instance."""
    return ModelPerformanceMonitor(database_service)