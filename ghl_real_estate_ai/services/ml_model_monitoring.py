"""
ML Model Monitoring Service for GHL Real Estate AI Platform

Comprehensive monitoring system for ML models with performance tracking,
drift detection, A/B testing, and automated alerting.

Features:
- Real-time performance monitoring for lead scoring, churn prediction, and property matching
- Statistical drift detection for features and predictions
- A/B testing framework for model improvements
- Automated alerting with escalation rules
- Streamlit dashboard integration
- Historical performance analysis

Performance Targets:
- Model accuracy monitoring: Lead Scoring 95%→98%+, Churn Prediction 92%→95%+, Property Matching 88%→95%+
- Drift detection: <100ms per analysis
- Alert delivery: <30 seconds
- Dashboard refresh: Real-time updates
- Storage efficiency: 1MB per 10k predictions

Author: EnterpriseHub AI - Production ML Monitoring
Date: 2026-01-10
"""

import asyncio
import json
import numpy as np
import pandas as pd
import pickle
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
from collections import defaultdict, deque
import logging
from abc import ABC, abstractmethod

# Statistical packages for drift detection
try:
    from scipy import stats
    from scipy.stats import ks_2samp, chi2_contingency
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False

# ML model imports
from ghl_real_estate_ai.services.ai_predictive_lead_scoring import PredictiveLeadScorer
from ghl_real_estate_ai.services.churn_prediction_service import ChurnPredictionService
from ghl_real_estate_ai.services.property_matcher import PropertyMatcher
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class ModelType(Enum):
    """Types of ML models being monitored"""
    LEAD_SCORING = "lead_scoring"
    CHURN_PREDICTION = "churn_prediction"
    PROPERTY_MATCHING = "property_matching"


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class DriftType(Enum):
    """Types of drift that can be detected"""
    FEATURE_DRIFT = "feature_drift"
    PREDICTION_DRIFT = "prediction_drift"
    CONFIDENCE_DRIFT = "confidence_drift"


@dataclass
class ModelPerformanceMetrics:
    """Performance metrics for ML models"""
    model_name: str
    timestamp: datetime

    # Classification metrics
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    auc_roc: Optional[float] = None

    # Regression/satisfaction metrics (for property matching)
    satisfaction_score: Optional[float] = None
    match_quality: Optional[float] = None
    relevance_score: Optional[float] = None

    # Performance metrics
    inference_time_ms: float = 0.0
    response_time_ms: Optional[float] = None
    prediction_count: int = 0

    # Error metrics
    error_rate: Optional[float] = None
    failure_count: int = 0

    # Additional metadata
    model_version: Optional[str] = None
    data_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return asdict(self)


@dataclass
class DriftAnalysisResult:
    """Results from drift analysis"""
    model_name: str
    analysis_timestamp: datetime
    drift_type: DriftType

    # Overall drift assessment
    overall_drift_detected: bool
    drift_magnitude: float  # 0-1 scale
    drift_score: float      # Statistical test p-value

    # Feature-level drift (for feature drift analysis)
    feature_drift_scores: Dict[str, float] = field(default_factory=dict)
    drifted_features: List[str] = field(default_factory=list)

    # Prediction drift details
    prediction_distribution_change: Optional[float] = None
    confidence_distribution_change: Optional[float] = None

    # Recommendations
    recommended_actions: List[str] = field(default_factory=list)
    urgency_level: str = "low"

    # Additional metadata
    sample_size: int = 0
    baseline_period: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class AlertConfiguration:
    """Configuration for automated alerts"""
    model_name: str
    metric: str
    threshold: float
    comparison: str  # "greater_than", "less_than", "equal_to"
    severity: AlertSeverity
    cooldown_minutes: int = 30

    # Escalation rules
    escalation_after_alerts: Optional[int] = None
    escalation_severity: Optional[AlertSeverity] = None

    # Notification settings
    notification_channels: List[str] = field(default_factory=lambda: ['email'])
    recipients: List[str] = field(default_factory=list)


@dataclass
class ABTestResult:
    """A/B test statistical analysis result"""
    test_id: str
    test_name: str
    model_a: str
    model_b: str

    # Statistical results
    is_significant: bool
    p_value: float
    confidence_interval: Tuple[float, float]
    effect_size: float

    # Sample sizes
    sample_size_a: int
    sample_size_b: int

    # Performance comparison
    metric_a_mean: float
    metric_b_mean: float
    improvement_percentage: float

    # Conclusion
    winning_model: Optional[str] = None
    recommendation: str = "continue_test"
    notes: str = ""


class StorageBackend(ABC):
    """Abstract base class for storage backends"""

    @abstractmethod
    async def store_metric(self, metric: ModelPerformanceMetrics) -> None:
        """Store a performance metric"""
        pass

    @abstractmethod
    async def get_metrics(self, model_name: str, start_time: datetime,
                         end_time: Optional[datetime] = None) -> List[ModelPerformanceMetrics]:
        """Retrieve metrics for a model within time range"""
        pass

    @abstractmethod
    async def store_drift_result(self, drift_result: DriftAnalysisResult) -> None:
        """Store drift analysis result"""
        pass

    @abstractmethod
    async def get_drift_results(self, model_name: str, hours: int = 24) -> List[DriftAnalysisResult]:
        """Get recent drift analysis results"""
        pass


class MemoryStorageBackend(StorageBackend):
    """In-memory storage backend for testing"""

    def __init__(self, max_entries: int = 10000):
        self.metrics: deque = deque(maxlen=max_entries)
        self.drift_results: deque = deque(maxlen=max_entries)
        self.ab_tests: Dict[str, Dict] = {}
        self.alerts: deque = deque(maxlen=max_entries)

    async def store_metric(self, metric: ModelPerformanceMetrics) -> None:
        self.metrics.append(metric)

    async def get_metrics(self, model_name: str, start_time: datetime,
                         end_time: Optional[datetime] = None) -> List[ModelPerformanceMetrics]:
        end_time = end_time or datetime.now()

        return [
            metric for metric in self.metrics
            if (metric.model_name == model_name and
                start_time <= metric.timestamp <= end_time)
        ]

    async def store_drift_result(self, drift_result: DriftAnalysisResult) -> None:
        self.drift_results.append(drift_result)

    async def get_drift_results(self, model_name: str, hours: int = 24) -> List[DriftAnalysisResult]:
        cutoff_time = datetime.now() - timedelta(hours=hours)

        return [
            result for result in self.drift_results
            if (result.model_name == model_name and
                result.analysis_timestamp >= cutoff_time)
        ]


class SQLiteStorageBackend(StorageBackend):
    """SQLite storage backend for production"""

    def __init__(self, db_path: str = "ml_monitoring.db"):
        self.db_path = db_path
        self._initialized = False

    async def _initialize(self):
        """Initialize database schema"""
        if self._initialized:
            return

        if not SQLITE_AVAILABLE:
            raise RuntimeError("SQLite not available")

        conn = sqlite3.connect(self.db_path)

        # Create metrics table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS model_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                accuracy REAL,
                precision REAL,
                recall REAL,
                f1_score REAL,
                auc_roc REAL,
                satisfaction_score REAL,
                match_quality REAL,
                relevance_score REAL,
                inference_time_ms REAL NOT NULL,
                response_time_ms REAL,
                prediction_count INTEGER,
                error_rate REAL,
                failure_count INTEGER,
                model_version TEXT,
                data_version TEXT
            )
        """)

        # Create drift results table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS drift_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                analysis_timestamp DATETIME NOT NULL,
                drift_type TEXT NOT NULL,
                overall_drift_detected BOOLEAN,
                drift_magnitude REAL,
                drift_score REAL,
                feature_drift_scores TEXT,
                drifted_features TEXT,
                recommended_actions TEXT,
                urgency_level TEXT,
                sample_size INTEGER,
                error_message TEXT
            )
        """)

        # Create indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_model_time ON model_metrics(model_name, timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_drift_model_time ON drift_results(model_name, analysis_timestamp)")

        conn.commit()
        conn.close()

        self._initialized = True

    async def store_metric(self, metric: ModelPerformanceMetrics) -> None:
        await self._initialize()

        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO model_metrics
            (model_name, timestamp, accuracy, precision, recall, f1_score, auc_roc,
             satisfaction_score, match_quality, relevance_score, inference_time_ms,
             response_time_ms, prediction_count, error_rate, failure_count,
             model_version, data_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metric.model_name, metric.timestamp, metric.accuracy, metric.precision,
            metric.recall, metric.f1_score, metric.auc_roc, metric.satisfaction_score,
            metric.match_quality, metric.relevance_score, metric.inference_time_ms,
            metric.response_time_ms, metric.prediction_count, metric.error_rate,
            metric.failure_count, metric.model_version, metric.data_version
        ))
        conn.commit()
        conn.close()

    async def get_metrics(self, model_name: str, start_time: datetime,
                         end_time: Optional[datetime] = None) -> List[ModelPerformanceMetrics]:
        await self._initialize()

        end_time = end_time or datetime.now()

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("""
            SELECT * FROM model_metrics
            WHERE model_name = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
        """, (model_name, start_time, end_time))

        metrics = []
        for row in cursor.fetchall():
            metric = ModelPerformanceMetrics(
                model_name=row['model_name'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                accuracy=row['accuracy'],
                precision=row['precision'],
                recall=row['recall'],
                f1_score=row['f1_score'],
                auc_roc=row['auc_roc'],
                satisfaction_score=row['satisfaction_score'],
                match_quality=row['match_quality'],
                relevance_score=row['relevance_score'],
                inference_time_ms=row['inference_time_ms'],
                response_time_ms=row['response_time_ms'],
                prediction_count=row['prediction_count'] or 0,
                error_rate=row['error_rate'],
                failure_count=row['failure_count'] or 0,
                model_version=row['model_version'],
                data_version=row['data_version']
            )
            metrics.append(metric)

        conn.close()
        return metrics

    async def store_drift_result(self, drift_result: DriftAnalysisResult) -> None:
        await self._initialize()

        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO drift_results
            (model_name, analysis_timestamp, drift_type, overall_drift_detected,
             drift_magnitude, drift_score, feature_drift_scores, drifted_features,
             recommended_actions, urgency_level, sample_size, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            drift_result.model_name, drift_result.analysis_timestamp,
            drift_result.drift_type.value, drift_result.overall_drift_detected,
            drift_result.drift_magnitude, drift_result.drift_score,
            json.dumps(drift_result.feature_drift_scores),
            json.dumps(drift_result.drifted_features),
            json.dumps(drift_result.recommended_actions),
            drift_result.urgency_level, drift_result.sample_size,
            drift_result.error_message
        ))
        conn.commit()
        conn.close()

    async def get_drift_results(self, model_name: str, hours: int = 24) -> List[DriftAnalysisResult]:
        await self._initialize()

        cutoff_time = datetime.now() - timedelta(hours=hours)

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("""
            SELECT * FROM drift_results
            WHERE model_name = ? AND analysis_timestamp >= ?
            ORDER BY analysis_timestamp DESC
        """, (model_name, cutoff_time))

        results = []
        for row in cursor.fetchall():
            drift_result = DriftAnalysisResult(
                model_name=row['model_name'],
                analysis_timestamp=datetime.fromisoformat(row['analysis_timestamp']),
                drift_type=DriftType(row['drift_type']),
                overall_drift_detected=bool(row['overall_drift_detected']),
                drift_magnitude=row['drift_magnitude'],
                drift_score=row['drift_score'],
                feature_drift_scores=json.loads(row['feature_drift_scores'] or '{}'),
                drifted_features=json.loads(row['drifted_features'] or '[]'),
                recommended_actions=json.loads(row['recommended_actions'] or '[]'),
                urgency_level=row['urgency_level'],
                sample_size=row['sample_size'],
                error_message=row['error_message']
            )
            results.append(drift_result)

        conn.close()
        return results


class ModelPerformanceTracker:
    """Tracks model performance metrics over time"""

    def __init__(self, storage_backend: StorageBackend, retention_days: int = 90):
        self.storage_backend = storage_backend
        self.retention_days = retention_days
        self.performance_thresholds: Dict[str, Dict] = {}

    async def record_metric(self, metric: ModelPerformanceMetrics) -> None:
        """Record a performance metric"""
        try:
            await self.storage_backend.store_metric(metric)
            logger.debug(f"Recorded metric for {metric.model_name}: accuracy={metric.accuracy}")

        except Exception as e:
            logger.error(f"Failed to record metric: {e}")
            raise

    async def get_metrics(self, model_name: str, start_time: datetime,
                         end_time: Optional[datetime] = None) -> List[ModelPerformanceMetrics]:
        """Get metrics for a model within time range"""
        try:
            return await self.storage_backend.get_metrics(model_name, start_time, end_time)

        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return []

    async def analyze_performance_trend(self, model_name: str, metric_name: str,
                                       days: int = 7) -> Dict[str, Any]:
        """Analyze performance trend for a specific metric"""
        try:
            start_time = datetime.now() - timedelta(days=days)
            metrics = await self.get_metrics(model_name, start_time)

            if len(metrics) < 2:
                return {
                    'trend_direction': 'insufficient_data',
                    'change_rate': 0.0,
                    'significance_level': 1.0,
                    'sample_size': len(metrics)
                }

            # Extract metric values
            values = []
            timestamps = []

            for metric in metrics:
                value = getattr(metric, metric_name, None)
                if value is not None:
                    values.append(value)
                    timestamps.append(metric.timestamp.timestamp())

            if len(values) < 2:
                return {
                    'trend_direction': 'insufficient_data',
                    'change_rate': 0.0,
                    'significance_level': 1.0,
                    'sample_size': len(values)
                }

            # Calculate trend using linear regression
            if SCIPY_AVAILABLE:
                slope, intercept, r_value, p_value, std_err = stats.linregress(timestamps, values)

                trend_direction = 'stable'
                if abs(slope) > std_err and p_value < 0.05:
                    trend_direction = 'improving' if slope > 0 else 'declining'

                return {
                    'trend_direction': trend_direction,
                    'change_rate': slope,
                    'significance_level': p_value,
                    'r_squared': r_value ** 2,
                    'sample_size': len(values),
                    'start_value': values[0],
                    'end_value': values[-1]
                }
            else:
                # Simple trend calculation without scipy
                change_rate = (values[-1] - values[0]) / len(values)
                trend_direction = 'improving' if change_rate > 0.01 else ('declining' if change_rate < -0.01 else 'stable')

                return {
                    'trend_direction': trend_direction,
                    'change_rate': change_rate,
                    'significance_level': 0.5,  # Unknown without statistical test
                    'sample_size': len(values)
                }

        except Exception as e:
            logger.error(f"Failed to analyze trend: {e}")
            return {
                'trend_direction': 'error',
                'change_rate': 0.0,
                'significance_level': 1.0,
                'error': str(e)
            }

    async def set_performance_thresholds(self, model_name: str, thresholds: Dict[str, Dict]) -> None:
        """Set performance thresholds for a model"""
        self.performance_thresholds[model_name] = thresholds

    async def check_threshold_violations(self, metric: ModelPerformanceMetrics) -> List[Dict[str, Any]]:
        """Check if metric violates any thresholds"""
        violations = []

        thresholds = self.performance_thresholds.get(metric.model_name, {})

        for metric_name, threshold_config in thresholds.items():
            value = getattr(metric, metric_name, None)
            if value is None:
                continue

            # Check minimum threshold
            if 'min' in threshold_config and value < threshold_config['min']:
                violations.append({
                    'metric': metric_name,
                    'value': value,
                    'threshold': threshold_config['min'],
                    'violation_type': 'below_minimum',
                    'severity': 'high' if value < threshold_config['min'] * 0.9 else 'medium'
                })

            # Check maximum threshold
            if 'max' in threshold_config and value > threshold_config['max']:
                violations.append({
                    'metric': metric_name,
                    'value': value,
                    'threshold': threshold_config['max'],
                    'violation_type': 'above_maximum',
                    'severity': 'high' if value > threshold_config['max'] * 1.1 else 'medium'
                })

        return violations


class ModelDriftDetector:
    """Detects model drift using statistical tests"""

    def __init__(self, drift_threshold: float = 0.05, min_samples: int = 100):
        self.drift_threshold = drift_threshold  # p-value threshold for significance
        self.min_samples = min_samples
        self.baseline_distributions: Dict[str, Dict] = {}
        self.baseline_predictions: Dict[str, np.ndarray] = {}
        self.baseline_confidence: Dict[str, np.ndarray] = {}

    async def set_baseline_distribution(self, model_name: str,
                                       features: Dict[str, np.ndarray]) -> None:
        """Set baseline feature distribution for drift detection"""
        self.baseline_distributions[model_name] = {}

        for feature_name, feature_values in features.items():
            if len(feature_values) >= self.min_samples:
                self.baseline_distributions[model_name][feature_name] = feature_values.copy()
            else:
                logger.warning(f"Insufficient samples for baseline {feature_name}: {len(feature_values)}")

    async def get_baseline_distribution(self, model_name: str) -> Optional[Dict[str, np.ndarray]]:
        """Get baseline distribution for a model"""
        return self.baseline_distributions.get(model_name)

    async def detect_feature_drift(self, model_name: str,
                                  current_features: Dict[str, np.ndarray]) -> DriftAnalysisResult:
        """Detect drift in feature distributions using KS test"""
        try:
            baseline_features = self.baseline_distributions.get(model_name)

            if not baseline_features:
                return DriftAnalysisResult(
                    model_name=model_name,
                    analysis_timestamp=datetime.now(),
                    drift_type=DriftType.FEATURE_DRIFT,
                    overall_drift_detected=False,
                    drift_magnitude=0.0,
                    drift_score=1.0,
                    error_message="No baseline distribution available"
                )

            if not SCIPY_AVAILABLE:
                return DriftAnalysisResult(
                    model_name=model_name,
                    analysis_timestamp=datetime.now(),
                    drift_type=DriftType.FEATURE_DRIFT,
                    overall_drift_detected=False,
                    drift_magnitude=0.0,
                    drift_score=1.0,
                    error_message="SciPy not available for statistical tests"
                )

            feature_drift_scores = {}
            drifted_features = []
            max_drift_score = 0.0

            for feature_name, current_values in current_features.items():
                if feature_name in baseline_features and len(current_values) >= self.min_samples:
                    baseline_values = baseline_features[feature_name]

                    # Perform Kolmogorov-Smirnov test
                    ks_statistic, p_value = ks_2samp(baseline_values, current_values)

                    feature_drift_scores[feature_name] = p_value
                    max_drift_score = max(max_drift_score, ks_statistic)

                    if p_value < self.drift_threshold:
                        drifted_features.append(feature_name)

            # Determine overall drift
            overall_drift_detected = len(drifted_features) > 0
            drift_magnitude = min(max_drift_score, 1.0)

            # Generate recommendations
            recommended_actions = []
            urgency_level = "low"

            if overall_drift_detected:
                if len(drifted_features) > len(feature_drift_scores) * 0.5:
                    urgency_level = "high"
                    recommended_actions.extend([
                        "Investigate data quality issues",
                        "Consider model retraining",
                        "Review feature engineering pipeline"
                    ])
                else:
                    urgency_level = "medium"
                    recommended_actions.extend([
                        "Monitor drifted features closely",
                        "Investigate root cause of drift"
                    ])

            return DriftAnalysisResult(
                model_name=model_name,
                analysis_timestamp=datetime.now(),
                drift_type=DriftType.FEATURE_DRIFT,
                overall_drift_detected=overall_drift_detected,
                drift_magnitude=drift_magnitude,
                drift_score=min(feature_drift_scores.values()) if feature_drift_scores else 1.0,
                feature_drift_scores=feature_drift_scores,
                drifted_features=drifted_features,
                recommended_actions=recommended_actions,
                urgency_level=urgency_level,
                sample_size=len(current_values) if current_values else 0
            )

        except Exception as e:
            logger.error(f"Failed to detect feature drift: {e}")
            return DriftAnalysisResult(
                model_name=model_name,
                analysis_timestamp=datetime.now(),
                drift_type=DriftType.FEATURE_DRIFT,
                overall_drift_detected=False,
                drift_magnitude=0.0,
                drift_score=1.0,
                error_message=str(e)
            )

    async def set_baseline_predictions(self, model_name: str, predictions: np.ndarray) -> None:
        """Set baseline prediction distribution"""
        self.baseline_predictions[model_name] = predictions.copy()

    async def detect_prediction_drift(self, model_name: str,
                                    current_predictions: np.ndarray) -> Dict[str, Any]:
        """Detect drift in prediction distributions"""
        try:
            baseline_predictions = self.baseline_predictions.get(model_name)

            if baseline_predictions is None:
                return {
                    'drift_detected': False,
                    'drift_magnitude': 0.0,
                    'error': 'No baseline predictions available'
                }

            if len(current_predictions) < self.min_samples:
                return {
                    'drift_detected': False,
                    'drift_magnitude': 0.0,
                    'error': 'Insufficient samples for drift detection'
                }

            if SCIPY_AVAILABLE:
                # KS test for prediction distribution drift
                ks_statistic, p_value = ks_2samp(baseline_predictions, current_predictions)

                return {
                    'drift_detected': p_value < self.drift_threshold,
                    'drift_magnitude': ks_statistic,
                    'p_value': p_value,
                    'sample_size': len(current_predictions)
                }
            else:
                # Simple distribution comparison
                baseline_mean = np.mean(baseline_predictions)
                current_mean = np.mean(current_predictions)
                mean_diff = abs(current_mean - baseline_mean)

                return {
                    'drift_detected': mean_diff > 0.1,  # Simple threshold
                    'drift_magnitude': mean_diff,
                    'baseline_mean': baseline_mean,
                    'current_mean': current_mean
                }

        except Exception as e:
            logger.error(f"Failed to detect prediction drift: {e}")
            return {
                'drift_detected': False,
                'drift_magnitude': 0.0,
                'error': str(e)
            }

    async def set_baseline_confidence(self, model_name: str, confidence_scores: np.ndarray) -> None:
        """Set baseline confidence distribution"""
        self.baseline_confidence[model_name] = confidence_scores.copy()

    async def detect_confidence_drift(self, model_name: str,
                                    current_confidence: np.ndarray) -> Dict[str, Any]:
        """Detect drift in confidence distributions"""
        try:
            baseline_confidence = self.baseline_confidence.get(model_name)

            if baseline_confidence is None:
                return {
                    'drift_detected': False,
                    'mean_confidence_change': 0.0,
                    'error': 'No baseline confidence available'
                }

            if len(current_confidence) < self.min_samples:
                return {
                    'drift_detected': False,
                    'mean_confidence_change': 0.0,
                    'error': 'Insufficient samples'
                }

            baseline_mean = np.mean(baseline_confidence)
            current_mean = np.mean(current_confidence)
            confidence_change = current_mean - baseline_mean

            # Detect significant confidence drift (>10% change)
            drift_detected = abs(confidence_change) > 0.1

            if SCIPY_AVAILABLE:
                # Statistical test for confidence drift
                ks_statistic, p_value = ks_2samp(baseline_confidence, current_confidence)
                drift_detected = p_value < self.drift_threshold

            return {
                'drift_detected': drift_detected,
                'mean_confidence_change': confidence_change,
                'baseline_mean_confidence': baseline_mean,
                'current_mean_confidence': current_mean,
                'sample_size': len(current_confidence)
            }

        except Exception as e:
            logger.error(f"Failed to detect confidence drift: {e}")
            return {
                'drift_detected': False,
                'mean_confidence_change': 0.0,
                'error': str(e)
            }


class ModelABTestFramework:
    """A/B testing framework for model improvements"""

    def __init__(self, statistical_power: float = 0.8, significance_level: float = 0.05,
                 minimum_sample_size: int = 100):
        self.statistical_power = statistical_power
        self.significance_level = significance_level
        self.minimum_sample_size = minimum_sample_size
        self.active_tests: Dict[str, Dict] = {}
        self.test_results: Dict[str, List] = defaultdict(list)

    async def create_ab_test(self, test_config: Dict[str, Any]) -> str:
        """Create a new A/B test"""
        import uuid
        test_id = str(uuid.uuid4())

        self.active_tests[test_id] = {
            'name': test_config['name'],
            'model_a': test_config['model_a'],
            'model_b': test_config['model_b'],
            'traffic_split': test_config.get('traffic_split', 0.5),
            'success_metric': test_config['success_metric'],
            'minimum_sample_size': test_config.get('minimum_sample_size', self.minimum_sample_size),
            'max_duration_days': test_config.get('max_duration_days', 14),
            'created_at': datetime.now(),
            'status': 'active'
        }

        self.test_results[test_id] = []

        logger.info(f"Created A/B test {test_id}: {test_config['name']}")
        return test_id

    async def get_test_info(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get test information"""
        return self.active_tests.get(test_id)

    async def get_model_assignment(self, test_id: str, user_id: str) -> Optional[str]:
        """Get model assignment for a user in an A/B test"""
        test_info = self.active_tests.get(test_id)
        if not test_info or test_info['status'] != 'active':
            return None

        # Simple hash-based assignment for consistency
        import hashlib
        hash_input = f"{test_id}:{user_id}".encode()
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
        assignment_ratio = (hash_value % 1000) / 1000.0

        if assignment_ratio < test_info['traffic_split']:
            return test_info['model_b']
        else:
            return test_info['model_a']

    async def record_result(self, test_id: str, model_name: str, result_value: float) -> None:
        """Record a result for an A/B test"""
        if test_id not in self.active_tests:
            logger.warning(f"Test {test_id} not found")
            return

        self.test_results[test_id].append({
            'model': model_name,
            'value': result_value,
            'timestamp': datetime.now()
        })

    async def calculate_test_significance(self, test_id: str) -> ABTestResult:
        """Calculate statistical significance of A/B test"""
        test_info = self.active_tests.get(test_id)
        if not test_info:
            raise ValueError(f"Test {test_id} not found")

        results = self.test_results[test_id]

        # Separate results by model
        model_a_results = [r['value'] for r in results if r['model'] == test_info['model_a']]
        model_b_results = [r['value'] for r in results if r['model'] == test_info['model_b']]

        # Check if we have enough data
        if len(model_a_results) < self.minimum_sample_size or len(model_b_results) < self.minimum_sample_size:
            return ABTestResult(
                test_id=test_id,
                test_name=test_info['name'],
                model_a=test_info['model_a'],
                model_b=test_info['model_b'],
                is_significant=False,
                p_value=1.0,
                confidence_interval=(0.0, 0.0),
                effect_size=0.0,
                sample_size_a=len(model_a_results),
                sample_size_b=len(model_b_results),
                metric_a_mean=np.mean(model_a_results) if model_a_results else 0.0,
                metric_b_mean=np.mean(model_b_results) if model_b_results else 0.0,
                improvement_percentage=0.0,
                notes="Insufficient data for significance testing"
            )

        # Calculate statistics
        mean_a = np.mean(model_a_results)
        mean_b = np.mean(model_b_results)
        improvement_percentage = ((mean_b - mean_a) / mean_a) * 100 if mean_a != 0 else 0.0

        # Statistical significance test
        is_significant = False
        p_value = 1.0
        confidence_interval = (0.0, 0.0)

        if SCIPY_AVAILABLE:
            # Perform t-test
            t_statistic, p_value = stats.ttest_ind(model_b_results, model_a_results)
            is_significant = p_value < self.significance_level

            # Calculate confidence interval for difference
            std_error = np.sqrt(np.var(model_a_results) / len(model_a_results) +
                               np.var(model_b_results) / len(model_b_results))
            margin_of_error = stats.t.ppf(1 - self.significance_level / 2,
                                         len(model_a_results) + len(model_b_results) - 2) * std_error

            difference = mean_b - mean_a
            confidence_interval = (difference - margin_of_error, difference + margin_of_error)

        # Determine winning model
        winning_model = None
        if is_significant:
            winning_model = test_info['model_b'] if mean_b > mean_a else test_info['model_a']

        # Calculate effect size (Cohen's d)
        pooled_std = np.sqrt(((len(model_a_results) - 1) * np.var(model_a_results) +
                             (len(model_b_results) - 1) * np.var(model_b_results)) /
                            (len(model_a_results) + len(model_b_results) - 2))
        effect_size = (mean_b - mean_a) / pooled_std if pooled_std > 0 else 0.0

        return ABTestResult(
            test_id=test_id,
            test_name=test_info['name'],
            model_a=test_info['model_a'],
            model_b=test_info['model_b'],
            is_significant=is_significant,
            p_value=p_value,
            confidence_interval=confidence_interval,
            effect_size=effect_size,
            sample_size_a=len(model_a_results),
            sample_size_b=len(model_b_results),
            metric_a_mean=mean_a,
            metric_b_mean=mean_b,
            improvement_percentage=improvement_percentage,
            winning_model=winning_model,
            recommendation="deploy_winner" if is_significant else "continue_test"
        )


class ModelAlertingSystem:
    """Automated alerting system for model monitoring"""

    def __init__(self, notification_channels: List[str] = None, escalation_rules: bool = True):
        self.notification_channels = notification_channels or ['email']
        self.escalation_rules = escalation_rules
        self.alert_configurations: Dict[str, AlertConfiguration] = {}
        self.alert_history: deque = deque(maxlen=10000)
        self.last_alert_times: Dict[Tuple[str, str], datetime] = {}
        self.alert_counts: Dict[str, int] = defaultdict(int)

    async def configure_alert(self, alert_name: str, config: AlertConfiguration) -> None:
        """Configure an alert"""
        self.alert_configurations[alert_name] = config
        logger.info(f"Configured alert {alert_name} for {config.model_name}")

    async def get_alert_configurations(self) -> Dict[str, AlertConfiguration]:
        """Get all alert configurations"""
        return self.alert_configurations.copy()

    async def check_and_trigger_alert(self, alert_name: str, metric_data: Dict[str, Any]) -> bool:
        """Check if an alert should be triggered and trigger if necessary"""
        config = self.alert_configurations.get(alert_name)
        if not config:
            return False

        # Check if metric matches alert
        if metric_data.get('model_name') != config.model_name:
            return False

        if metric_data.get('metric') != config.metric:
            return False

        # Check cooldown
        cooldown_key = (alert_name, config.model_name)
        last_alert_time = self.last_alert_times.get(cooldown_key)

        if last_alert_time:
            time_since_last = datetime.now() - last_alert_time
            if time_since_last.total_seconds() < config.cooldown_minutes * 60:
                return False

        # Check threshold violation
        value = metric_data.get('value')
        if value is None:
            return False

        threshold_violated = False

        if config.comparison == 'greater_than' and value > config.threshold:
            threshold_violated = True
        elif config.comparison == 'less_than' and value < config.threshold:
            threshold_violated = True
        elif config.comparison == 'equal_to' and value == config.threshold:
            threshold_violated = True

        if not threshold_violated:
            return False

        # Trigger alert
        alert_data = {
            'alert_name': alert_name,
            'model_name': config.model_name,
            'metric': config.metric,
            'value': value,
            'threshold': config.threshold,
            'severity': config.severity.value,
            'timestamp': metric_data.get('timestamp', datetime.now()),
            'comparison': config.comparison
        }

        # Check for escalation
        if self.escalation_rules and config.escalation_after_alerts:
            self.alert_counts[alert_name] += 1

            if (self.alert_counts[alert_name] >= config.escalation_after_alerts and
                config.escalation_severity):
                alert_data['severity'] = config.escalation_severity.value
                alert_data['escalated'] = True
                logger.warning(f"Alert {alert_name} escalated to {config.escalation_severity.value}")

        # Store alert
        self.alert_history.append(alert_data)
        self.last_alert_times[cooldown_key] = datetime.now()

        # Send notification (would integrate with actual notification system)
        await self._send_notification(alert_data, config)

        logger.warning(f"Alert triggered: {alert_name} - {config.metric}={value} ({config.comparison} {config.threshold})")
        return True

    async def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        return [
            alert for alert in self.alert_history
            if alert['timestamp'] >= cutoff_time
        ]

    async def _send_notification(self, alert_data: Dict[str, Any], config: AlertConfiguration) -> None:
        """Send alert notification (mock implementation)"""
        # In production, this would integrate with email, Slack, PagerDuty, etc.
        logger.info(f"ALERT NOTIFICATION: {alert_data['alert_name']} - {alert_data['severity']}")


class ModelMonitoringDashboard:
    """Dashboard integration for model monitoring"""

    def __init__(self, refresh_interval_seconds: int = 30, max_data_points: int = 1000):
        self.refresh_interval_seconds = refresh_interval_seconds
        self.max_data_points = max_data_points
        self.real_time_metrics: deque = deque(maxlen=max_data_points)
        self.active_feeds: Dict[str, List[str]] = {}

    async def aggregate_performance_data(self, performance_data: List[Dict[str, Any]],
                                       interval: str = 'hour') -> List[Dict[str, Any]]:
        """Aggregate performance data for dashboard display"""
        try:
            df = pd.DataFrame(performance_data)

            if df.empty:
                return []

            # Set timestamp as index
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)

            # Resample based on interval
            if interval == 'minute':
                resampled = df.resample('1min')
            elif interval == 'hour':
                resampled = df.resample('1H')
            elif interval == 'day':
                resampled = df.resample('1D')
            else:
                resampled = df.resample('1H')  # Default to hourly

            # Aggregate numeric columns
            aggregated = resampled.agg({
                col: 'mean' for col in df.select_dtypes(include=[np.number]).columns
            }).reset_index()

            # Rename columns to indicate aggregation
            rename_map = {col: f"{col}_avg" for col in df.select_dtypes(include=[np.number]).columns}
            aggregated.rename(columns=rename_map, inplace=True)

            return aggregated.to_dict('records')

        except Exception as e:
            logger.error(f"Failed to aggregate performance data: {e}")
            return []

    def create_real_time_feed(self, model_names: List[str]) -> str:
        """Create a real-time metrics feed for specified models"""
        import uuid
        feed_id = str(uuid.uuid4())
        self.active_feeds[feed_id] = model_names
        return feed_id

    async def push_real_time_metric(self, metric_data: Dict[str, Any]) -> None:
        """Push a metric to real-time feeds"""
        metric_data['timestamp'] = datetime.now()
        self.real_time_metrics.append(metric_data)

    async def get_latest_metrics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get latest real-time metrics"""
        return list(self.real_time_metrics)[-limit:]


class MLModelMonitoringService:
    """Main ML Model Monitoring Service coordinating all components"""

    def __init__(self, lead_scorer: PredictiveLeadScorer,
                 churn_predictor: ChurnPredictionService,
                 property_matcher: PropertyMatcher,
                 storage_backend: str = "sqlite"):

        # ML Models
        self.lead_scorer = lead_scorer
        self.churn_predictor = churn_predictor
        self.property_matcher = property_matcher

        # Storage backend
        if storage_backend == "sqlite":
            self.storage_backend = SQLiteStorageBackend()
        else:
            self.storage_backend = MemoryStorageBackend()

        # Core components
        self.performance_tracker = ModelPerformanceTracker(self.storage_backend)
        self.drift_detector = ModelDriftDetector()
        self.ab_test_framework = ModelABTestFramework()
        self.alerting_system = ModelAlertingSystem()
        self.dashboard = ModelMonitoringDashboard()

        # Registered models
        self.registered_models = {}

    async def initialize(self) -> None:
        """Initialize the monitoring service"""
        try:
            # Register models
            self.registered_models = {
                'lead_scoring': self.lead_scorer,
                'churn_prediction': self.churn_predictor,
                'property_matching': self.property_matcher
            }

            # Set up default performance thresholds
            await self._setup_default_thresholds()

            # Set up default alerts
            await self._setup_default_alerts()

            logger.info("ML Model Monitoring Service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize ML Model Monitoring Service: {e}")
            raise

    async def get_registered_models(self) -> Dict[str, Any]:
        """Get list of registered models"""
        return list(self.registered_models.keys())

    async def record_model_performance(self, model_name: str,
                                     performance_data: Dict[str, Any]) -> None:
        """Record performance metrics for a model"""
        try:
            # Create performance metric object
            metric = ModelPerformanceMetrics(
                model_name=model_name,
                timestamp=performance_data.get('timestamp', datetime.now()),
                accuracy=performance_data.get('accuracy'),
                precision=performance_data.get('precision'),
                recall=performance_data.get('recall'),
                f1_score=performance_data.get('f1_score'),
                auc_roc=performance_data.get('auc_roc'),
                satisfaction_score=performance_data.get('satisfaction_score'),
                match_quality=performance_data.get('match_quality'),
                relevance_score=performance_data.get('relevance_score'),
                inference_time_ms=performance_data.get('inference_time_ms', 0.0),
                response_time_ms=performance_data.get('response_time_ms'),
                prediction_count=performance_data.get('prediction_count', 0),
                error_rate=performance_data.get('error_rate'),
                failure_count=performance_data.get('failure_count', 0),
                model_version=performance_data.get('model_version'),
                data_version=performance_data.get('data_version')
            )

            # Record metric
            await self.performance_tracker.record_metric(metric)

            # Check for threshold violations and trigger alerts
            violations = await self.performance_tracker.check_threshold_violations(metric)

            for violation in violations:
                await self.alerting_system.check_and_trigger_alert(
                    f"{model_name}_{violation['metric']}_threshold",
                    {
                        'model_name': model_name,
                        'metric': violation['metric'],
                        'value': violation['value'],
                        'timestamp': metric.timestamp
                    }
                )

            # Update dashboard
            await self.dashboard.push_real_time_metric({
                'model': model_name,
                'timestamp': metric.timestamp,
                **performance_data
            })

        except Exception as e:
            logger.error(f"Failed to record model performance: {e}")
            raise

    async def get_model_performance(self, model_name: str,
                                   hours: int = 24) -> List[ModelPerformanceMetrics]:
        """Get performance metrics for a model"""
        start_time = datetime.now() - timedelta(hours=hours)
        return await self.performance_tracker.get_metrics(model_name, start_time)

    async def process_live_prediction(self, prediction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a live prediction for monitoring"""
        try:
            model_name = prediction_data['model']

            # Record prediction for monitoring
            # This would be called from the actual prediction endpoints

            # Update real-time performance metrics
            inference_time = prediction_data.get('inference_time_ms', 0.0)

            # Check for drift (simplified - would need more data)
            drift_detected = False

            # Update dashboard
            await self.dashboard.push_real_time_metric({
                'model': model_name,
                'prediction': prediction_data.get('prediction'),
                'confidence': prediction_data.get('confidence'),
                'inference_time_ms': inference_time
            })

            return {
                'status': 'processed',
                'drift_detected': drift_detected,
                'performance_updated': True,
                'inference_time_ms': inference_time
            }

        except Exception as e:
            logger.error(f"Failed to process live prediction: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    async def _setup_default_thresholds(self) -> None:
        """Set up default performance thresholds"""
        # Lead Scoring thresholds
        lead_scoring_thresholds = {
            'accuracy': {'min': 0.90, 'target': 0.95},
            'precision': {'min': 0.88, 'target': 0.93},
            'recall': {'min': 0.87, 'target': 0.92},
            'inference_time_ms': {'max': 200, 'target': 150}
        }

        await self.performance_tracker.set_performance_thresholds(
            'lead_scoring',
            lead_scoring_thresholds
        )

        # Churn Prediction thresholds
        churn_prediction_thresholds = {
            'accuracy': {'min': 0.88, 'target': 0.92},
            'precision': {'min': 0.90, 'target': 0.94},
            'recall': {'min': 0.85, 'target': 0.89},
            'inference_time_ms': {'max': 250, 'target': 200}
        }

        await self.performance_tracker.set_performance_thresholds(
            'churn_prediction',
            churn_prediction_thresholds
        )

        # Property Matching thresholds
        property_matching_thresholds = {
            'satisfaction_score': {'min': 0.80, 'target': 0.88},
            'match_quality': {'min': 0.75, 'target': 0.86},
            'relevance_score': {'min': 0.82, 'target': 0.91},
            'response_time_ms': {'max': 150, 'target': 100}
        }

        await self.performance_tracker.set_performance_thresholds(
            'property_matching',
            property_matching_thresholds
        )

    async def _setup_default_alerts(self) -> None:
        """Set up default alerts"""
        # Lead Scoring alerts
        lead_scoring_accuracy_alert = AlertConfiguration(
            model_name='lead_scoring',
            metric='accuracy',
            threshold=0.90,
            comparison='less_than',
            severity=AlertSeverity.HIGH,
            cooldown_minutes=30,
            escalation_after_alerts=3,
            escalation_severity=AlertSeverity.CRITICAL
        )

        await self.alerting_system.configure_alert(
            'lead_scoring_accuracy_degradation',
            lead_scoring_accuracy_alert
        )

        # Churn Prediction alerts
        churn_prediction_alert = AlertConfiguration(
            model_name='churn_prediction',
            metric='precision',
            threshold=0.90,
            comparison='less_than',
            severity=AlertSeverity.HIGH,
            cooldown_minutes=30
        )

        await self.alerting_system.configure_alert(
            'churn_prediction_precision_drop',
            churn_prediction_alert
        )

        # Property Matching alerts
        property_matching_alert = AlertConfiguration(
            model_name='property_matching',
            metric='satisfaction_score',
            threshold=0.80,
            comparison='less_than',
            severity=AlertSeverity.MEDIUM,
            cooldown_minutes=60
        )

        await self.alerting_system.configure_alert(
            'property_matching_satisfaction_drop',
            property_matching_alert
        )


# Global service instance
_ml_monitoring_service = None


async def get_ml_monitoring_service() -> MLModelMonitoringService:
    """Get singleton instance of MLModelMonitoringService"""
    global _ml_monitoring_service

    if _ml_monitoring_service is None:
        # Import models
        from ghl_real_estate_ai.services.ai_predictive_lead_scoring import PredictiveLeadScorer
        from ghl_real_estate_ai.services.churn_prediction_service import get_churn_prediction_service
        from ghl_real_estate_ai.services.property_matcher import PropertyMatcher

        # Create model instances
        lead_scorer = PredictiveLeadScorer()
        churn_predictor = await get_churn_prediction_service()
        property_matcher = PropertyMatcher()

        # Create monitoring service
        _ml_monitoring_service = MLModelMonitoringService(
            lead_scorer=lead_scorer,
            churn_predictor=churn_predictor,
            property_matcher=property_matcher,
            storage_backend="sqlite"
        )

        await _ml_monitoring_service.initialize()

    return _ml_monitoring_service


# Convenience functions
async def record_lead_scoring_performance(performance_data: Dict[str, Any]) -> None:
    """Record lead scoring performance metrics"""
    service = await get_ml_monitoring_service()
    await service.record_model_performance('lead_scoring', performance_data)


async def record_churn_prediction_performance(performance_data: Dict[str, Any]) -> None:
    """Record churn prediction performance metrics"""
    service = await get_ml_monitoring_service()
    await service.record_model_performance('churn_prediction', performance_data)


async def record_property_matching_performance(performance_data: Dict[str, Any]) -> None:
    """Record property matching performance metrics"""
    service = await get_ml_monitoring_service()
    await service.record_model_performance('property_matching', performance_data)


async def detect_model_drift(model_name: str, current_features: Dict[str, np.ndarray]) -> DriftAnalysisResult:
    """Detect drift for a specific model"""
    service = await get_ml_monitoring_service()
    return await service.drift_detector.detect_feature_drift(model_name, current_features)