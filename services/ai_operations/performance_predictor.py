#!/usr/bin/env python3
"""
Performance Predictor for AI-Enhanced Operations
Proactive performance optimization and bottleneck prevention using ML forecasting.

Performance Targets:
- Bottleneck prediction accuracy: >85%
- Performance improvement: >20% through optimization
- SLA violation prevention: >95%
- Optimization response time: <2 minutes
"""

import asyncio
import logging
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import numpy as np
from collections import deque, defaultdict

# ML and Data Processing
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    import scipy.optimize as optimize
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# Local imports
from ..base import BaseService
from ..logging_config import get_logger

logger = get_logger(__name__)

class BottleneckType(Enum):
    """Types of performance bottlenecks."""
    CPU_BOUND = "cpu_bound"
    MEMORY_BOUND = "memory_bound"
    IO_BOUND = "io_bound"
    NETWORK_BOUND = "network_bound"
    DATABASE_BOUND = "database_bound"
    CACHE_BOUND = "cache_bound"
    QUEUE_BOUND = "queue_bound"
    CONCURRENCY_BOUND = "concurrency_bound"

class OptimizationType(Enum):
    """Types of optimization strategies."""
    RESOURCE_SCALING = "resource_scaling"
    CACHE_OPTIMIZATION = "cache_optimization"
    QUERY_OPTIMIZATION = "query_optimization"
    LOAD_BALANCING = "load_balancing"
    CONCURRENCY_TUNING = "concurrency_tuning"
    ALGORITHM_OPTIMIZATION = "algorithm_optimization"
    MEMORY_MANAGEMENT = "memory_management"
    NETWORK_OPTIMIZATION = "network_optimization"

class SeverityLevel(Enum):
    """Severity levels for performance issues."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass(slots=True)
class PerformanceMetrics:
    """Comprehensive performance metrics snapshot."""
    timestamp: datetime
    service_name: str

    # Core metrics
    cpu_usage: np.float32
    memory_usage: np.float32
    disk_io_rate: np.float32
    network_io_rate: np.float32

    # Application metrics
    request_rate: np.float32
    response_time_avg: np.float32
    response_time_p95: np.float32
    response_time_p99: np.float32
    error_rate: np.float32
    throughput: np.float32

    # Database metrics
    db_connection_count: int
    db_query_time_avg: np.float32
    db_slow_queries: int
    db_deadlocks: int

    # Cache metrics
    cache_hit_rate: np.float32
    cache_memory_usage: np.float32
    cache_eviction_rate: np.float32

    # Queue metrics
    queue_depth: int
    queue_processing_time: np.float32
    queue_backlog: int

    # Concurrency metrics
    active_threads: int
    thread_pool_utilization: np.float32
    connection_pool_utilization: np.float32

@dataclass(slots=True)
class BottleneckPrediction:
    """Prediction of performance bottlenecks."""
    prediction_id: str
    service_name: str
    bottleneck_type: BottleneckType
    predicted_at: datetime
    expected_occurrence: datetime
    confidence: np.float32
    severity: SeverityLevel
    predicted_impact: Dict[str, Any]
    contributing_factors: List[str]
    recommended_actions: List[str]
    prevention_window: timedelta

@dataclass(slots=True)
class OptimizationRecommendation:
    """Performance optimization recommendation."""
    recommendation_id: str
    service_name: str
    optimization_type: OptimizationType
    current_performance: Dict[str, float]
    expected_improvement: Dict[str, float]
    implementation_effort: str  # low, medium, high
    risk_level: str  # low, medium, high
    cost_impact: str  # low, medium, high
    priority_score: np.float32
    detailed_steps: List[str]
    expected_timeline: timedelta
    rollback_plan: List[str]

@dataclass(slots=True)
class CapacityForecast:
    """Capacity planning forecast."""
    forecast_id: str
    service_name: str
    metric_name: str
    current_value: np.float32
    forecast_values: List[Tuple[datetime, np.float32]]
    confidence_intervals: List[Tuple[np.float32, np.float32]]
    capacity_limit: np.float32
    time_to_capacity: Optional[timedelta]
    growth_rate: np.float32
    seasonal_patterns: Dict[str, Any]

@dataclass(slots=True)
class SLAViolationRisk:
    """SLA violation risk assessment."""
    assessment_id: str
    service_name: str
    sla_metric: str
    sla_threshold: np.float32
    current_value: np.float32
    predicted_value: np.float32
    violation_probability: np.float32
    time_to_violation: Optional[timedelta]
    risk_factors: List[str]
    mitigation_strategies: List[str]

class PerformancePredictor(BaseService):
    """
    Advanced performance prediction and optimization system.

    Provides proactive bottleneck detection, optimization recommendations,
    capacity planning, and SLA violation prevention.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize performance predictor with ML models and forecasting."""
        super().__init__()
        self.config = config or {}

        # ML Models
        self.bottleneck_predictor: Optional[RandomForestRegressor] = None
        self.capacity_forecaster: Optional[GradientBoostingRegressor] = None
        self.response_time_predictor: Optional[Ridge] = None
        self.optimization_scorer: Optional[RandomForestRegressor] = None

        # Scalers
        self.metrics_scaler: Optional[StandardScaler] = None
        self.forecast_scaler: Optional[MinMaxScaler] = None

        # Data storage
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.bottleneck_predictions: Dict[str, List[BottleneckPrediction]] = defaultdict(list)
        self.optimization_recommendations: Dict[str, List[OptimizationRecommendation]] = defaultdict(list)
        self.capacity_forecasts: Dict[str, List[CapacityForecast]] = defaultdict(list)
        self.sla_assessments: Dict[str, List[SLAViolationRisk]] = defaultdict(list)

        # SLA Configuration
        self.sla_thresholds = self.config.get('sla_thresholds', {
            'response_time_avg': 1000,  # ms
            'response_time_p95': 2000,  # ms
            'response_time_p99': 5000,  # ms
            'error_rate': 0.01,  # 1%
            'availability': 0.999,  # 99.9%
            'throughput': 100  # requests/sec
        })

        # Optimization configuration
        self.optimization_config = self.config.get('optimization_config', {
            'min_improvement_threshold': 0.05,  # 5% minimum improvement
            'max_risk_tolerance': 'medium',
            'cost_sensitivity': 'medium',
            'implementation_preference': 'automated'
        })

        # Performance tracking
        self.metrics = {
            'predictions_made': 0,
            'predictions_accurate': 0,
            'bottlenecks_prevented': 0,
            'optimizations_applied': 0,
            'sla_violations_prevented': 0,
            'average_prediction_accuracy': 0.0,
            'average_improvement_achieved': 0.0
        }

        # Prediction windows
        self.prediction_windows = {
            'short_term': timedelta(minutes=15),
            'medium_term': timedelta(hours=2),
            'long_term': timedelta(hours=24)
        }

        logger.info("Performance predictor initialized")

    async def initialize_ml_models(self) -> bool:
        """Initialize and train ML models for performance prediction."""
        if not ML_AVAILABLE:
            logger.warning("ML libraries not available - using statistical fallbacks")
            return False

        try:
            # Initialize bottleneck predictor (Random Forest for multi-class prediction)
            self.bottleneck_predictor = RandomForestRegressor(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )

            # Initialize capacity forecaster (Gradient Boosting for time series)
            self.capacity_forecaster = GradientBoostingRegressor(
                n_estimators=150,
                learning_rate=0.1,
                max_depth=8,
                min_samples_split=4,
                min_samples_leaf=2,
                random_state=42
            )

            # Initialize response time predictor (Ridge for regression)
            self.response_time_predictor = Ridge(
                alpha=1.0,
                normalize=True,
                random_state=42
            )

            # Initialize optimization scorer
            self.optimization_scorer = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )

            # Initialize scalers
            self.metrics_scaler = StandardScaler()
            self.forecast_scaler = MinMaxScaler()

            # Train models with synthetic/historical data
            await self._train_prediction_models()

            logger.info("Performance prediction models initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize ML models: {e}")
            return False

    async def _train_prediction_models(self) -> None:
        """Train ML models using historical or synthetic performance data."""
        try:
            # Generate training data
            training_data = self._generate_training_data()

            if len(training_data) < 500:
                logger.info("Generating additional synthetic data for robust training")
                training_data.extend(self._generate_additional_training_data(2000))

            # Prepare features and targets
            features = []
            bottleneck_targets = []
            capacity_targets = []
            response_time_targets = []
            optimization_scores = []

            for data_point in training_data:
                # Feature vector: current metrics
                feature_vector = [
                    data_point['cpu_usage'],
                    data_point['memory_usage'],
                    data_point['disk_io_rate'],
                    data_point['network_io_rate'],
                    data_point['request_rate'],
                    data_point['response_time_avg'],
                    data_point['error_rate'],
                    data_point['throughput'],
                    data_point['db_query_time_avg'],
                    data_point['cache_hit_rate'],
                    data_point['queue_depth'],
                    data_point['active_threads'],
                    data_point['time_of_day'],  # Normalized 0-1
                    data_point['day_of_week'],  # Normalized 0-1
                    data_point['load_trend']    # -1, 0, 1 for decreasing, stable, increasing
                ]

                features.append(feature_vector)
                bottleneck_targets.append(data_point['bottleneck_severity'])
                capacity_targets.append(data_point['capacity_utilization'])
                response_time_targets.append(data_point['future_response_time'])
                optimization_scores.append(data_point['optimization_potential'])

            # Scale features
            features_scaled = self.metrics_scaler.fit_transform(features)

            # Train bottleneck predictor
            self.bottleneck_predictor.fit(features_scaled, bottleneck_targets)

            # Train capacity forecaster
            self.capacity_forecaster.fit(features_scaled, capacity_targets)

            # Train response time predictor
            self.response_time_predictor.fit(features_scaled, response_time_targets)

            # Train optimization scorer
            self.optimization_scorer.fit(features_scaled, optimization_scores)

            logger.info(f"Models trained with {len(training_data)} data points")

            # Evaluate model performance
            await self._evaluate_model_performance(features_scaled, {
                'bottleneck': bottleneck_targets,
                'capacity': capacity_targets,
                'response_time': response_time_targets,
                'optimization': optimization_scores
            })

        except Exception as e:
            logger.error(f"Failed to train prediction models: {e}")
            raise

    def _generate_training_data(self) -> List[Dict[str, Any]]:
        """Generate synthetic training data for performance prediction models."""
        training_data = []

        # Define performance scenarios
        scenarios = [
            # Normal operation
            {
                'base_cpu': 0.3, 'base_memory': 0.4, 'base_disk_io': 100,
                'base_network_io': 50, 'base_request_rate': 100, 'base_response_time': 200,
                'base_error_rate': 0.001, 'base_throughput': 90, 'scenario': 'normal'
            },
            # High load
            {
                'base_cpu': 0.7, 'base_memory': 0.6, 'base_disk_io': 300,
                'base_network_io': 150, 'base_request_rate': 300, 'base_response_time': 800,
                'base_error_rate': 0.02, 'base_throughput': 250, 'scenario': 'high_load'
            },
            # Memory pressure
            {
                'base_cpu': 0.5, 'base_memory': 0.9, 'base_disk_io': 200,
                'base_network_io': 80, 'base_request_rate': 150, 'base_response_time': 1200,
                'base_error_rate': 0.05, 'base_throughput': 120, 'scenario': 'memory_pressure'
            },
            # I/O bottleneck
            {
                'base_cpu': 0.4, 'base_memory': 0.5, 'base_disk_io': 800,
                'base_network_io': 400, 'base_request_rate': 200, 'base_response_time': 2000,
                'base_error_rate': 0.03, 'base_throughput': 80, 'scenario': 'io_bottleneck'
            },
            # Database load
            {
                'base_cpu': 0.6, 'base_memory': 0.7, 'base_disk_io': 400,
                'base_network_io': 100, 'base_request_rate': 180, 'base_response_time': 1500,
                'base_error_rate': 0.04, 'base_throughput': 140, 'scenario': 'database_load'
            }
        ]

        # Generate data points for each scenario
        for scenario in scenarios:
            for _ in range(100):  # 100 points per scenario
                # Add realistic variations
                data_point = {
                    'cpu_usage': np.clip(scenario['base_cpu'] + np.random.normal(0, 0.1), 0, 1),
                    'memory_usage': np.clip(scenario['base_memory'] + np.random.normal(0, 0.1), 0, 1),
                    'disk_io_rate': max(scenario['base_disk_io'] + np.random.normal(0, 50), 0),
                    'network_io_rate': max(scenario['base_network_io'] + np.random.normal(0, 20), 0),
                    'request_rate': max(scenario['base_request_rate'] + np.random.normal(0, 30), 1),
                    'response_time_avg': max(scenario['base_response_time'] + np.random.normal(0, 100), 10),
                    'error_rate': np.clip(scenario['base_error_rate'] + np.random.normal(0, 0.01), 0, 1),
                    'throughput': max(scenario['base_throughput'] + np.random.normal(0, 20), 1),

                    # Additional metrics
                    'db_query_time_avg': max(50 + np.random.normal(0, 20), 1),
                    'cache_hit_rate': np.clip(0.8 + np.random.normal(0, 0.1), 0, 1),
                    'queue_depth': max(int(np.random.gamma(2, 10)), 0),
                    'active_threads': max(int(np.random.gamma(5, 20)), 1),

                    # Time features
                    'time_of_day': np.random.random(),  # 0-1 normalized
                    'day_of_week': np.random.random(),   # 0-1 normalized
                    'load_trend': np.random.choice([-1, 0, 1])  # decreasing, stable, increasing
                }

                # Calculate targets based on scenario
                data_point.update(self._calculate_targets(data_point, scenario['scenario']))
                training_data.append(data_point)

        return training_data

    def _calculate_targets(self, metrics: Dict[str, float], scenario: str) -> Dict[str, float]:
        """Calculate target values for training based on metrics and scenario."""
        targets = {}

        # Bottleneck severity (0-1 scale)
        bottleneck_score = 0.0
        if metrics['cpu_usage'] > 0.8:
            bottleneck_score = max(bottleneck_score, 0.8)
        if metrics['memory_usage'] > 0.85:
            bottleneck_score = max(bottleneck_score, 0.9)
        if metrics['response_time_avg'] > 1000:
            bottleneck_score = max(bottleneck_score, 0.7)
        if metrics['error_rate'] > 0.02:
            bottleneck_score = max(bottleneck_score, 0.75)

        targets['bottleneck_severity'] = bottleneck_score

        # Capacity utilization (projected)
        capacity_util = max(metrics['cpu_usage'], metrics['memory_usage'])
        if scenario == 'high_load':
            capacity_util = min(capacity_util + 0.2, 1.0)
        elif scenario == 'memory_pressure':
            capacity_util = min(capacity_util + 0.15, 1.0)

        targets['capacity_utilization'] = capacity_util

        # Future response time (predictive)
        future_rt = metrics['response_time_avg']
        if bottleneck_score > 0.7:
            future_rt *= (1 + bottleneck_score)
        if metrics['load_trend'] > 0:  # increasing load
            future_rt *= 1.3

        targets['future_response_time'] = future_rt

        # Optimization potential (0-1 scale)
        opt_potential = 0.0
        if metrics['cache_hit_rate'] < 0.7:
            opt_potential += 0.3
        if metrics['cpu_usage'] > 0.8:
            opt_potential += 0.4
        if metrics['db_query_time_avg'] > 100:
            opt_potential += 0.3
        if metrics['queue_depth'] > 50:
            opt_potential += 0.2

        targets['optimization_potential'] = min(opt_potential, 1.0)

        return targets

    def _generate_additional_training_data(self, count: int) -> List[Dict[str, Any]]:
        """Generate additional synthetic data for robust training."""
        additional_data = []

        for _ in range(count):
            # Random performance state
            data_point = {
                'cpu_usage': np.random.beta(2, 3),
                'memory_usage': np.random.beta(2, 3),
                'disk_io_rate': np.random.gamma(3, 50),
                'network_io_rate': np.random.gamma(2, 25),
                'request_rate': np.random.gamma(3, 50),
                'response_time_avg': np.random.gamma(2, 200),
                'error_rate': np.random.exponential(0.01),
                'throughput': np.random.gamma(4, 30),
                'db_query_time_avg': np.random.gamma(2, 30),
                'cache_hit_rate': np.random.beta(8, 2),
                'queue_depth': int(np.random.gamma(2, 15)),
                'active_threads': int(np.random.gamma(3, 25)),
                'time_of_day': np.random.random(),
                'day_of_week': np.random.random(),
                'load_trend': np.random.choice([-1, 0, 1])
            }

            # Clip values to realistic ranges
            data_point['error_rate'] = min(data_point['error_rate'], 0.5)
            data_point['response_time_avg'] = min(data_point['response_time_avg'], 10000)
            data_point['cache_hit_rate'] = max(data_point['cache_hit_rate'], 0.1)

            # Determine scenario based on characteristics
            if data_point['memory_usage'] > 0.8:
                scenario = 'memory_pressure'
            elif data_point['cpu_usage'] > 0.8:
                scenario = 'high_load'
            elif data_point['disk_io_rate'] > 400:
                scenario = 'io_bottleneck'
            else:
                scenario = 'normal'

            # Calculate targets
            data_point.update(self._calculate_targets(data_point, scenario))
            additional_data.append(data_point)

        return additional_data

    async def _evaluate_model_performance(self, features: np.ndarray,
                                         targets: Dict[str, List[float]]) -> None:
        """Evaluate trained model performance."""
        try:
            # Split data for validation
            split_idx = int(0.8 * len(features))
            train_features, val_features = features[:split_idx], features[split_idx:]

            evaluations = {}

            for model_name, model in [
                ('bottleneck', self.bottleneck_predictor),
                ('capacity', self.capacity_forecaster),
                ('response_time', self.response_time_predictor),
                ('optimization', self.optimization_scorer)
            ]:
                if model is not None:
                    train_targets = targets[model_name][:split_idx]
                    val_targets = targets[model_name][split_idx:]

                    # Make predictions
                    predictions = model.predict(val_features)

                    # Calculate metrics
                    mae = mean_absolute_error(val_targets, predictions)
                    mse = mean_squared_error(val_targets, predictions)
                    rmse = np.sqrt(mse)

                    evaluations[model_name] = {
                        'mae': mae,
                        'rmse': rmse,
                        'accuracy': 1 - (rmse / (np.max(val_targets) - np.min(val_targets)))
                    }

            logger.info(f"Model evaluation results: {evaluations}")

            # Update metrics
            avg_accuracy = np.mean([eval_['accuracy'] for eval_ in evaluations.values()])
            self.metrics['average_prediction_accuracy'] = avg_accuracy

        except Exception as e:
            logger.error(f"Error evaluating model performance: {e}")

    async def collect_performance_metrics(self, service_name: str,
                                        raw_metrics: Dict[str, Any]) -> PerformanceMetrics:
        """Collect and process performance metrics for a service."""
        try:
            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                service_name=service_name,

                # Core metrics
                cpu_usage=np.float32(raw_metrics.get('cpu_usage', 0.0)),
                memory_usage=np.float32(raw_metrics.get('memory_usage', 0.0)),
                disk_io_rate=np.float32(raw_metrics.get('disk_io_rate', 0.0)),
                network_io_rate=np.float32(raw_metrics.get('network_io_rate', 0.0)),

                # Application metrics
                request_rate=np.float32(raw_metrics.get('request_rate', 0.0)),
                response_time_avg=np.float32(raw_metrics.get('response_time_avg', 0.0)),
                response_time_p95=np.float32(raw_metrics.get('response_time_p95', 0.0)),
                response_time_p99=np.float32(raw_metrics.get('response_time_p99', 0.0)),
                error_rate=np.float32(raw_metrics.get('error_rate', 0.0)),
                throughput=np.float32(raw_metrics.get('throughput', 0.0)),

                # Database metrics
                db_connection_count=int(raw_metrics.get('db_connection_count', 0)),
                db_query_time_avg=np.float32(raw_metrics.get('db_query_time_avg', 0.0)),
                db_slow_queries=int(raw_metrics.get('db_slow_queries', 0)),
                db_deadlocks=int(raw_metrics.get('db_deadlocks', 0)),

                # Cache metrics
                cache_hit_rate=np.float32(raw_metrics.get('cache_hit_rate', 0.0)),
                cache_memory_usage=np.float32(raw_metrics.get('cache_memory_usage', 0.0)),
                cache_eviction_rate=np.float32(raw_metrics.get('cache_eviction_rate', 0.0)),

                # Queue metrics
                queue_depth=int(raw_metrics.get('queue_depth', 0)),
                queue_processing_time=np.float32(raw_metrics.get('queue_processing_time', 0.0)),
                queue_backlog=int(raw_metrics.get('queue_backlog', 0)),

                # Concurrency metrics
                active_threads=int(raw_metrics.get('active_threads', 0)),
                thread_pool_utilization=np.float32(raw_metrics.get('thread_pool_utilization', 0.0)),
                connection_pool_utilization=np.float32(raw_metrics.get('connection_pool_utilization', 0.0))
            )

            # Store in history
            self.metrics_history[service_name].append(metrics)

            return metrics

        except Exception as e:
            logger.error(f"Error collecting metrics for {service_name}: {e}")
            raise

    async def predict_bottlenecks(self, service_name: str,
                                prediction_window: timedelta = None) -> List[BottleneckPrediction]:
        """Predict performance bottlenecks for a service."""
        try:
            if prediction_window is None:
                prediction_window = self.prediction_windows['medium_term']

            # Get recent metrics
            recent_metrics = list(self.metrics_history[service_name])[-100:]  # Last 100 data points

            if len(recent_metrics) < 10:
                logger.warning(f"Insufficient metrics history for {service_name}")
                return []

            predictions = []

            # Use ML model if available
            if self.bottleneck_predictor is not None and self.metrics_scaler is not None:
                predictions.extend(await self._predict_bottlenecks_ml(
                    service_name, recent_metrics, prediction_window
                ))
            else:
                predictions.extend(await self._predict_bottlenecks_statistical(
                    service_name, recent_metrics, prediction_window
                ))

            # Store predictions
            self.bottleneck_predictions[service_name].extend(predictions)
            self.metrics['predictions_made'] += len(predictions)

            logger.info(f"Generated {len(predictions)} bottleneck predictions for {service_name}")

            return predictions

        except Exception as e:
            logger.error(f"Error predicting bottlenecks for {service_name}: {e}")
            return []

    async def _predict_bottlenecks_ml(self, service_name: str,
                                    metrics_history: List[PerformanceMetrics],
                                    prediction_window: timedelta) -> List[BottleneckPrediction]:
        """Use ML models to predict bottlenecks."""
        predictions = []

        try:
            # Prepare features from recent metrics
            latest_metrics = metrics_history[-1]

            # Calculate trends
            cpu_trend = self._calculate_trend([m.cpu_usage for m in metrics_history[-10:]])
            memory_trend = self._calculate_trend([m.memory_usage for m in metrics_history[-10:]])
            response_time_trend = self._calculate_trend([m.response_time_avg for m in metrics_history[-10:]])

            # Create feature vector
            current_time = datetime.now()
            time_of_day = (current_time.hour * 60 + current_time.minute) / (24 * 60)
            day_of_week = current_time.weekday() / 6

            features = [
                float(latest_metrics.cpu_usage),
                float(latest_metrics.memory_usage),
                float(latest_metrics.disk_io_rate),
                float(latest_metrics.network_io_rate),
                float(latest_metrics.request_rate),
                float(latest_metrics.response_time_avg),
                float(latest_metrics.error_rate),
                float(latest_metrics.throughput),
                float(latest_metrics.db_query_time_avg),
                float(latest_metrics.cache_hit_rate),
                float(latest_metrics.queue_depth),
                float(latest_metrics.active_threads),
                time_of_day,
                day_of_week,
                cpu_trend
            ]

            # Scale features
            features_scaled = self.metrics_scaler.transform([features])

            # Get bottleneck severity prediction
            bottleneck_severity = self.bottleneck_predictor.predict(features_scaled)[0]

            if bottleneck_severity > 0.5:  # Threshold for significant bottleneck
                # Determine bottleneck type based on current metrics
                bottleneck_type = self._identify_bottleneck_type(latest_metrics)

                # Calculate confidence
                confidence = min(bottleneck_severity, 0.95)

                # Determine severity level
                if bottleneck_severity > 0.9:
                    severity = SeverityLevel.CRITICAL
                elif bottleneck_severity > 0.75:
                    severity = SeverityLevel.HIGH
                elif bottleneck_severity > 0.6:
                    severity = SeverityLevel.MEDIUM
                else:
                    severity = SeverityLevel.LOW

                # Calculate expected occurrence time
                occurrence_delay = self._estimate_bottleneck_timing(
                    bottleneck_severity, cpu_trend, memory_trend
                )
                expected_occurrence = current_time + occurrence_delay

                # Generate prediction
                prediction = BottleneckPrediction(
                    prediction_id=self._generate_prediction_id(service_name, bottleneck_type.value),
                    service_name=service_name,
                    bottleneck_type=bottleneck_type,
                    predicted_at=current_time,
                    expected_occurrence=expected_occurrence,
                    confidence=np.float32(confidence),
                    severity=severity,
                    predicted_impact=self._estimate_bottleneck_impact(latest_metrics, bottleneck_type),
                    contributing_factors=self._identify_contributing_factors(latest_metrics),
                    recommended_actions=self._generate_bottleneck_recommendations(bottleneck_type),
                    prevention_window=occurrence_delay
                )

                predictions.append(prediction)

            return predictions

        except Exception as e:
            logger.error(f"Error in ML bottleneck prediction: {e}")
            return []

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend direction from recent values."""
        if len(values) < 3:
            return 0.0

        # Simple linear regression for trend
        x = np.arange(len(values))
        slope, _ = np.polyfit(x, values, 1)
        return float(slope)

    def _identify_bottleneck_type(self, metrics: PerformanceMetrics) -> BottleneckType:
        """Identify the most likely bottleneck type based on metrics."""
        scores = {}

        # CPU bottleneck indicators
        scores[BottleneckType.CPU_BOUND] = (
            metrics.cpu_usage * 0.6 +
            (1 - metrics.cache_hit_rate) * 0.2 +
            min(metrics.response_time_avg / 1000, 1) * 0.2
        )

        # Memory bottleneck indicators
        scores[BottleneckType.MEMORY_BOUND] = (
            metrics.memory_usage * 0.5 +
            metrics.cache_eviction_rate * 0.3 +
            min(metrics.queue_depth / 100, 1) * 0.2
        )

        # I/O bottleneck indicators
        scores[BottleneckType.IO_BOUND] = (
            min(metrics.disk_io_rate / 1000, 1) * 0.4 +
            min(metrics.network_io_rate / 500, 1) * 0.3 +
            min(metrics.db_query_time_avg / 200, 1) * 0.3
        )

        # Database bottleneck indicators
        scores[BottleneckType.DATABASE_BOUND] = (
            min(metrics.db_query_time_avg / 100, 1) * 0.4 +
            min(metrics.db_slow_queries / 10, 1) * 0.3 +
            min(metrics.db_connection_count / 100, 1) * 0.3
        )

        # Queue bottleneck indicators
        scores[BottleneckType.QUEUE_BOUND] = (
            min(metrics.queue_depth / 50, 1) * 0.5 +
            min(metrics.queue_processing_time / 1000, 1) * 0.3 +
            min(metrics.queue_backlog / 100, 1) * 0.2
        )

        # Cache bottleneck indicators
        scores[BottleneckType.CACHE_BOUND] = (
            (1 - metrics.cache_hit_rate) * 0.6 +
            metrics.cache_eviction_rate * 0.4
        )

        # Concurrency bottleneck indicators
        scores[BottleneckType.CONCURRENCY_BOUND] = (
            metrics.thread_pool_utilization * 0.4 +
            metrics.connection_pool_utilization * 0.4 +
            min(metrics.active_threads / 200, 1) * 0.2
        )

        # Return type with highest score
        return max(scores.keys(), key=lambda k: scores[k])

    def _estimate_bottleneck_timing(self, severity: float, cpu_trend: float,
                                  memory_trend: float) -> timedelta:
        """Estimate when bottleneck will occur based on trends."""
        base_delay_minutes = 60  # Base delay of 1 hour

        # Adjust based on severity (higher severity = sooner occurrence)
        severity_factor = 1 - severity
        delay_minutes = base_delay_minutes * severity_factor

        # Adjust based on trends (positive trends reduce delay)
        if cpu_trend > 0 or memory_trend > 0:
            trend_factor = max(abs(cpu_trend), abs(memory_trend))
            delay_minutes *= (1 - trend_factor * 0.5)

        # Minimum delay of 5 minutes
        delay_minutes = max(delay_minutes, 5)

        return timedelta(minutes=delay_minutes)

    def _estimate_bottleneck_impact(self, metrics: PerformanceMetrics,
                                  bottleneck_type: BottleneckType) -> Dict[str, Any]:
        """Estimate the impact of predicted bottleneck."""
        impact = {
            'performance_degradation': 'medium',
            'user_experience_impact': 'medium',
            'business_impact': 'low',
            'estimated_affected_users': 0,
            'estimated_revenue_impact': 0.0
        }

        # Adjust based on current metrics
        if metrics.response_time_avg > 2000:
            impact['performance_degradation'] = 'high'
            impact['user_experience_impact'] = 'high'

        if metrics.error_rate > 0.05:
            impact['business_impact'] = 'medium'

        # Estimate affected users based on throughput
        impact['estimated_affected_users'] = int(metrics.throughput * 60)  # Users per minute

        # Simple revenue impact estimate
        if impact['business_impact'] == 'high':
            impact['estimated_revenue_impact'] = impact['estimated_affected_users'] * 0.10  # $0.10 per affected user
        elif impact['business_impact'] == 'medium':
            impact['estimated_revenue_impact'] = impact['estimated_affected_users'] * 0.05

        return impact

    def _identify_contributing_factors(self, metrics: PerformanceMetrics) -> List[str]:
        """Identify factors contributing to potential bottlenecks."""
        factors = []

        if metrics.cpu_usage > 0.8:
            factors.append("High CPU utilization")

        if metrics.memory_usage > 0.85:
            factors.append("High memory usage")

        if metrics.cache_hit_rate < 0.6:
            factors.append("Poor cache performance")

        if metrics.db_query_time_avg > 200:
            factors.append("Slow database queries")

        if metrics.queue_depth > 50:
            factors.append("Queue backlog")

        if metrics.error_rate > 0.02:
            factors.append("Elevated error rate")

        if metrics.thread_pool_utilization > 0.9:
            factors.append("Thread pool saturation")

        return factors

    def _generate_bottleneck_recommendations(self, bottleneck_type: BottleneckType) -> List[str]:
        """Generate recommendations to prevent or mitigate bottlenecks."""
        recommendations = []

        if bottleneck_type == BottleneckType.CPU_BOUND:
            recommendations.extend([
                "Scale out to add more CPU resources",
                "Optimize algorithms and reduce computational complexity",
                "Enable CPU affinity for critical processes",
                "Review and optimize hot code paths"
            ])

        elif bottleneck_type == BottleneckType.MEMORY_BOUND:
            recommendations.extend([
                "Scale up memory allocation",
                "Optimize memory usage patterns",
                "Enable memory compression",
                "Review object lifecycle management"
            ])

        elif bottleneck_type == BottleneckType.IO_BOUND:
            recommendations.extend([
                "Optimize disk I/O patterns",
                "Enable I/O caching",
                "Use faster storage (SSD)",
                "Implement asynchronous I/O operations"
            ])

        elif bottleneck_type == BottleneckType.DATABASE_BOUND:
            recommendations.extend([
                "Optimize slow queries",
                "Add database indexes",
                "Enable connection pooling",
                "Consider database sharding"
            ])

        elif bottleneck_type == BottleneckType.CACHE_BOUND:
            recommendations.extend([
                "Increase cache size",
                "Optimize cache eviction policies",
                "Add cache warming strategies",
                "Review cache key distribution"
            ])

        elif bottleneck_type == BottleneckType.QUEUE_BOUND:
            recommendations.extend([
                "Increase queue processing capacity",
                "Add more worker processes",
                "Optimize message processing logic",
                "Implement priority queuing"
            ])

        elif bottleneck_type == BottleneckType.CONCURRENCY_BOUND:
            recommendations.extend([
                "Increase thread pool size",
                "Optimize synchronization patterns",
                "Reduce lock contention",
                "Consider async programming model"
            ])

        return recommendations

    async def _predict_bottlenecks_statistical(self, service_name: str,
                                             metrics_history: List[PerformanceMetrics],
                                             prediction_window: timedelta) -> List[BottleneckPrediction]:
        """Statistical fallback for bottleneck prediction."""
        predictions = []

        try:
            latest_metrics = metrics_history[-1]

            # Simple threshold-based prediction
            if latest_metrics.cpu_usage > 0.85:
                predictions.append(self._create_statistical_prediction(
                    service_name, BottleneckType.CPU_BOUND, latest_metrics, 0.8
                ))

            if latest_metrics.memory_usage > 0.9:
                predictions.append(self._create_statistical_prediction(
                    service_name, BottleneckType.MEMORY_BOUND, latest_metrics, 0.85
                ))

            if latest_metrics.response_time_avg > 3000:
                predictions.append(self._create_statistical_prediction(
                    service_name, BottleneckType.IO_BOUND, latest_metrics, 0.7
                ))

            return predictions

        except Exception as e:
            logger.error(f"Error in statistical bottleneck prediction: {e}")
            return []

    def _create_statistical_prediction(self, service_name: str, bottleneck_type: BottleneckType,
                                     metrics: PerformanceMetrics, confidence: float) -> BottleneckPrediction:
        """Create a bottleneck prediction using statistical methods."""
        current_time = datetime.now()

        return BottleneckPrediction(
            prediction_id=self._generate_prediction_id(service_name, bottleneck_type.value),
            service_name=service_name,
            bottleneck_type=bottleneck_type,
            predicted_at=current_time,
            expected_occurrence=current_time + timedelta(minutes=30),
            confidence=np.float32(confidence),
            severity=SeverityLevel.HIGH,
            predicted_impact=self._estimate_bottleneck_impact(metrics, bottleneck_type),
            contributing_factors=self._identify_contributing_factors(metrics),
            recommended_actions=self._generate_bottleneck_recommendations(bottleneck_type),
            prevention_window=timedelta(minutes=30)
        )

    def _generate_prediction_id(self, service_name: str, bottleneck_type: str) -> str:
        """Generate unique prediction ID."""
        timestamp = datetime.now().isoformat()
        content = f"{service_name}_{bottleneck_type}_{timestamp}"
        return f"pred_{hashlib.md5(content.encode()).hexdigest()[:12]}"

    async def generate_optimization_recommendations(self, service_name: str) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations for a service."""
        try:
            # Get recent metrics
            recent_metrics = list(self.metrics_history[service_name])[-20:]  # Last 20 data points

            if len(recent_metrics) < 5:
                logger.warning(f"Insufficient metrics for optimization analysis: {service_name}")
                return []

            recommendations = []
            latest_metrics = recent_metrics[-1]

            # Generate different types of optimization recommendations
            recommendations.extend(await self._analyze_resource_optimization(service_name, latest_metrics))
            recommendations.extend(await self._analyze_cache_optimization(service_name, latest_metrics))
            recommendations.extend(await self._analyze_database_optimization(service_name, latest_metrics))
            recommendations.extend(await self._analyze_concurrency_optimization(service_name, latest_metrics))

            # Score and prioritize recommendations
            recommendations = self._prioritize_optimizations(recommendations)

            # Store recommendations
            self.optimization_recommendations[service_name] = recommendations
            self.metrics['optimizations_applied'] += len(recommendations)

            logger.info(f"Generated {len(recommendations)} optimization recommendations for {service_name}")

            return recommendations

        except Exception as e:
            logger.error(f"Error generating optimization recommendations for {service_name}: {e}")
            return []

    async def _analyze_resource_optimization(self, service_name: str,
                                           metrics: PerformanceMetrics) -> List[OptimizationRecommendation]:
        """Analyze resource optimization opportunities."""
        recommendations = []

        # CPU optimization
        if metrics.cpu_usage > 0.8 and metrics.response_time_avg > 1000:
            recommendations.append(OptimizationRecommendation(
                recommendation_id=f"cpu_opt_{service_name}_{int(time.time())}",
                service_name=service_name,
                optimization_type=OptimizationType.RESOURCE_SCALING,
                current_performance={'cpu_usage': float(metrics.cpu_usage), 'response_time': float(metrics.response_time_avg)},
                expected_improvement={'cpu_usage': float(metrics.cpu_usage * 0.7), 'response_time': float(metrics.response_time_avg * 0.6)},
                implementation_effort='medium',
                risk_level='low',
                cost_impact='medium',
                priority_score=np.float32(0.8),
                detailed_steps=[
                    "Analyze current CPU usage patterns",
                    "Scale out to 2x current instances",
                    "Monitor performance improvements",
                    "Adjust scaling if needed"
                ],
                expected_timeline=timedelta(hours=1),
                rollback_plan=["Scale back to original instance count", "Monitor stability"]
            ))

        # Memory optimization
        if metrics.memory_usage > 0.85:
            recommendations.append(OptimizationRecommendation(
                recommendation_id=f"mem_opt_{service_name}_{int(time.time())}",
                service_name=service_name,
                optimization_type=OptimizationType.MEMORY_MANAGEMENT,
                current_performance={'memory_usage': float(metrics.memory_usage)},
                expected_improvement={'memory_usage': float(metrics.memory_usage * 0.7)},
                implementation_effort='high',
                risk_level='medium',
                cost_impact='low',
                priority_score=np.float32(0.7),
                detailed_steps=[
                    "Profile memory allocation patterns",
                    "Identify memory leaks",
                    "Optimize object lifecycle management",
                    "Implement memory pooling"
                ],
                expected_timeline=timedelta(days=2),
                rollback_plan=["Revert to previous memory management", "Monitor for stability"]
            ))

        return recommendations

    async def _analyze_cache_optimization(self, service_name: str,
                                        metrics: PerformanceMetrics) -> List[OptimizationRecommendation]:
        """Analyze cache optimization opportunities."""
        recommendations = []

        if metrics.cache_hit_rate < 0.7:
            recommendations.append(OptimizationRecommendation(
                recommendation_id=f"cache_opt_{service_name}_{int(time.time())}",
                service_name=service_name,
                optimization_type=OptimizationType.CACHE_OPTIMIZATION,
                current_performance={'cache_hit_rate': float(metrics.cache_hit_rate)},
                expected_improvement={'cache_hit_rate': 0.9, 'response_time_reduction': 0.3},
                implementation_effort='medium',
                risk_level='low',
                cost_impact='low',
                priority_score=np.float32(0.85),
                detailed_steps=[
                    "Analyze cache miss patterns",
                    "Optimize cache key strategy",
                    "Implement cache warming",
                    "Tune cache eviction policies"
                ],
                expected_timeline=timedelta(days=1),
                rollback_plan=["Revert cache configuration", "Clear cache if needed"]
            ))

        return recommendations

    async def _analyze_database_optimization(self, service_name: str,
                                           metrics: PerformanceMetrics) -> List[OptimizationRecommendation]:
        """Analyze database optimization opportunities."""
        recommendations = []

        if metrics.db_query_time_avg > 200 or metrics.db_slow_queries > 5:
            recommendations.append(OptimizationRecommendation(
                recommendation_id=f"db_opt_{service_name}_{int(time.time())}",
                service_name=service_name,
                optimization_type=OptimizationType.QUERY_OPTIMIZATION,
                current_performance={'avg_query_time': float(metrics.db_query_time_avg), 'slow_queries': metrics.db_slow_queries},
                expected_improvement={'avg_query_time': float(metrics.db_query_time_avg * 0.5), 'slow_queries': 1},
                implementation_effort='high',
                risk_level='medium',
                cost_impact='low',
                priority_score=np.float32(0.9),
                detailed_steps=[
                    "Identify slow queries",
                    "Analyze query execution plans",
                    "Add appropriate indexes",
                    "Optimize query structure"
                ],
                expected_timeline=timedelta(days=3),
                rollback_plan=["Remove new indexes if needed", "Revert query changes"]
            ))

        return recommendations

    async def _analyze_concurrency_optimization(self, service_name: str,
                                              metrics: PerformanceMetrics) -> List[OptimizationRecommendation]:
        """Analyze concurrency optimization opportunities."""
        recommendations = []

        if metrics.thread_pool_utilization > 0.9 or metrics.connection_pool_utilization > 0.9:
            recommendations.append(OptimizationRecommendation(
                recommendation_id=f"concurrency_opt_{service_name}_{int(time.time())}",
                service_name=service_name,
                optimization_type=OptimizationType.CONCURRENCY_TUNING,
                current_performance={'thread_utilization': float(metrics.thread_pool_utilization)},
                expected_improvement={'thread_utilization': 0.7, 'response_time_improvement': 0.2},
                implementation_effort='medium',
                risk_level='medium',
                cost_impact='low',
                priority_score=np.float32(0.75),
                detailed_steps=[
                    "Analyze thread pool usage patterns",
                    "Increase thread pool size",
                    "Optimize task distribution",
                    "Monitor for thread contention"
                ],
                expected_timeline=timedelta(hours=6),
                rollback_plan=["Revert thread pool configuration", "Monitor system stability"]
            ))

        return recommendations

    def _prioritize_optimizations(self, recommendations: List[OptimizationRecommendation]) -> List[OptimizationRecommendation]:
        """Prioritize optimization recommendations based on impact and effort."""

        # Calculate priority scores
        for rec in recommendations:
            score = 0.0

            # Impact on performance
            if 'response_time_reduction' in rec.expected_improvement:
                score += rec.expected_improvement['response_time_reduction'] * 0.4

            if 'cache_hit_rate' in rec.expected_improvement:
                score += (rec.expected_improvement['cache_hit_rate'] -
                         rec.current_performance.get('cache_hit_rate', 0)) * 0.3

            # Implementation effort (inverse scoring)
            effort_scores = {'low': 0.3, 'medium': 0.2, 'high': 0.1}
            score += effort_scores.get(rec.implementation_effort, 0.1)

            # Risk level (inverse scoring)
            risk_scores = {'low': 0.2, 'medium': 0.1, 'high': 0.05}
            score += risk_scores.get(rec.risk_level, 0.05)

            # Cost impact (inverse scoring)
            cost_scores = {'low': 0.1, 'medium': 0.05, 'high': 0.02}
            score += cost_scores.get(rec.cost_impact, 0.02)

            rec.priority_score = np.float32(score)

        # Sort by priority score
        recommendations.sort(key=lambda x: x.priority_score, reverse=True)

        return recommendations

    async def forecast_capacity(self, service_name: str,
                              metric_name: str,
                              forecast_horizon: timedelta = None) -> Optional[CapacityForecast]:
        """Forecast capacity needs for a service metric."""
        try:
            if forecast_horizon is None:
                forecast_horizon = timedelta(days=7)

            # Get metric history
            recent_metrics = list(self.metrics_history[service_name])[-200:]  # Last 200 data points

            if len(recent_metrics) < 50:
                logger.warning(f"Insufficient data for capacity forecasting: {service_name}")
                return None

            # Extract specific metric values
            metric_values = []
            for metrics in recent_metrics:
                if hasattr(metrics, metric_name):
                    metric_values.append(float(getattr(metrics, metric_name)))

            if not metric_values:
                logger.warning(f"Metric {metric_name} not found in metrics")
                return None

            # Generate forecast
            if self.capacity_forecaster is not None:
                forecast = await self._forecast_capacity_ml(
                    service_name, metric_name, metric_values, forecast_horizon
                )
            else:
                forecast = await self._forecast_capacity_statistical(
                    service_name, metric_name, metric_values, forecast_horizon
                )

            if forecast:
                self.capacity_forecasts[service_name].append(forecast)

            return forecast

        except Exception as e:
            logger.error(f"Error forecasting capacity for {service_name}.{metric_name}: {e}")
            return None

    async def _forecast_capacity_ml(self, service_name: str, metric_name: str,
                                  metric_values: List[float],
                                  forecast_horizon: timedelta) -> Optional[CapacityForecast]:
        """Use ML models for capacity forecasting."""
        try:
            # Create time series features
            features = []
            targets = []

            window_size = 10
            for i in range(window_size, len(metric_values)):
                # Features: previous values, time features
                window_features = metric_values[i-window_size:i]
                time_features = [
                    i / len(metric_values),  # Time progression
                    np.sin(2 * np.pi * i / 24),  # Daily pattern
                    np.cos(2 * np.pi * i / 24),
                    np.sin(2 * np.pi * i / (24 * 7)),  # Weekly pattern
                    np.cos(2 * np.pi * i / (24 * 7))
                ]

                feature_vector = window_features + time_features
                features.append(feature_vector)
                targets.append(metric_values[i])

            if len(features) < 20:
                return None

            # Scale features
            if not hasattr(self, '_forecast_scaler_fitted'):
                self.forecast_scaler.fit(features)
                self._forecast_scaler_fitted = True

            features_scaled = self.forecast_scaler.transform(features)

            # Train model on this specific metric
            temp_forecaster = GradientBoostingRegressor(
                n_estimators=100, learning_rate=0.1, max_depth=6, random_state=42
            )
            temp_forecaster.fit(features_scaled, targets)

            # Generate forecast
            forecast_steps = int(forecast_horizon.total_seconds() / 3600)  # Hourly steps
            forecast_values = []
            current_values = metric_values[-window_size:]

            for step in range(forecast_steps):
                # Create feature vector for prediction
                time_offset = len(metric_values) + step
                time_features = [
                    time_offset / (len(metric_values) + forecast_steps),
                    np.sin(2 * np.pi * time_offset / 24),
                    np.cos(2 * np.pi * time_offset / 24),
                    np.sin(2 * np.pi * time_offset / (24 * 7)),
                    np.cos(2 * np.pi * time_offset / (24 * 7))
                ]

                pred_features = list(current_values) + time_features
                pred_features_scaled = self.forecast_scaler.transform([pred_features])

                # Predict next value
                next_value = temp_forecaster.predict(pred_features_scaled)[0]
                forecast_time = datetime.now() + timedelta(hours=step)

                forecast_values.append((forecast_time, np.float32(next_value)))

                # Update current values window
                current_values = current_values[1:] + [next_value]

            # Calculate growth rate
            current_value = np.float32(metric_values[-1])
            end_value = forecast_values[-1][1] if forecast_values else current_value
            growth_rate = np.float32((end_value - current_value) / len(forecast_values)) if forecast_values else 0.0

            # Simple confidence intervals (±20%)
            confidence_intervals = [(val * 0.8, val * 1.2) for _, val in forecast_values]

            # Estimate capacity limit and time to capacity
            capacity_limit = self._estimate_capacity_limit(metric_name, current_value)
            time_to_capacity = self._estimate_time_to_capacity(forecast_values, capacity_limit)

            return CapacityForecast(
                forecast_id=f"cap_{service_name}_{metric_name}_{int(time.time())}",
                service_name=service_name,
                metric_name=metric_name,
                current_value=current_value,
                forecast_values=forecast_values,
                confidence_intervals=confidence_intervals,
                capacity_limit=capacity_limit,
                time_to_capacity=time_to_capacity,
                growth_rate=growth_rate,
                seasonal_patterns=self._detect_seasonal_patterns(metric_values)
            )

        except Exception as e:
            logger.error(f"Error in ML capacity forecasting: {e}")
            return None

    async def _forecast_capacity_statistical(self, service_name: str, metric_name: str,
                                           metric_values: List[float],
                                           forecast_horizon: timedelta) -> Optional[CapacityForecast]:
        """Statistical fallback for capacity forecasting."""
        try:
            current_value = np.float32(metric_values[-1])

            # Simple linear trend
            recent_values = metric_values[-20:]
            x = np.arange(len(recent_values))
            slope, intercept = np.polyfit(x, recent_values, 1)

            # Generate forecast
            forecast_steps = int(forecast_horizon.total_seconds() / 3600)
            forecast_values = []

            for step in range(forecast_steps):
                predicted_value = intercept + slope * (len(recent_values) + step)
                forecast_time = datetime.now() + timedelta(hours=step)
                forecast_values.append((forecast_time, np.float32(predicted_value)))

            growth_rate = np.float32(slope)
            capacity_limit = self._estimate_capacity_limit(metric_name, current_value)
            time_to_capacity = self._estimate_time_to_capacity(forecast_values, capacity_limit)

            return CapacityForecast(
                forecast_id=f"cap_stat_{service_name}_{metric_name}_{int(time.time())}",
                service_name=service_name,
                metric_name=metric_name,
                current_value=current_value,
                forecast_values=forecast_values,
                confidence_intervals=[(val * 0.9, val * 1.1) for _, val in forecast_values],
                capacity_limit=capacity_limit,
                time_to_capacity=time_to_capacity,
                growth_rate=growth_rate,
                seasonal_patterns={}
            )

        except Exception as e:
            logger.error(f"Error in statistical capacity forecasting: {e}")
            return None

    def _estimate_capacity_limit(self, metric_name: str, current_value: float) -> np.float32:
        """Estimate capacity limit for a metric."""
        # Default capacity limits based on metric type
        limits = {
            'cpu_usage': 0.9,
            'memory_usage': 0.95,
            'disk_usage': 0.9,
            'thread_pool_utilization': 0.9,
            'connection_pool_utilization': 0.95,
            'cache_memory_usage': 0.9
        }

        # For rate-based metrics, estimate based on current performance
        if 'rate' in metric_name or 'time' in metric_name:
            return np.float32(current_value * 2)  # Assume 2x current as limit

        return np.float32(limits.get(metric_name, 1.0))

    def _estimate_time_to_capacity(self, forecast_values: List[Tuple[datetime, float]],
                                 capacity_limit: float) -> Optional[timedelta]:
        """Estimate time until capacity limit is reached."""
        try:
            for forecast_time, forecast_value in forecast_values:
                if forecast_value >= capacity_limit:
                    return forecast_time - datetime.now()

            return None  # Capacity limit not reached in forecast window

        except Exception:
            return None

    def _detect_seasonal_patterns(self, values: List[float]) -> Dict[str, Any]:
        """Detect seasonal patterns in metric values."""
        try:
            patterns = {}

            if len(values) > 48:  # At least 2 days of hourly data
                # Daily pattern
                daily_avg = []
                for hour in range(24):
                    hourly_values = [values[i] for i in range(hour, len(values), 24) if i < len(values)]
                    if hourly_values:
                        daily_avg.append(np.mean(hourly_values))

                if daily_avg:
                    patterns['daily_peak_hour'] = int(np.argmax(daily_avg))
                    patterns['daily_variance'] = float(np.var(daily_avg))

            if len(values) > 168:  # At least 1 week of hourly data
                # Weekly pattern
                weekly_avg = []
                for day in range(7):
                    daily_values = [values[i] for i in range(day * 24, len(values), 168) if i < len(values)]
                    if daily_values:
                        weekly_avg.append(np.mean(daily_values))

                if weekly_avg:
                    patterns['weekly_peak_day'] = int(np.argmax(weekly_avg))
                    patterns['weekly_variance'] = float(np.var(weekly_avg))

            return patterns

        except Exception:
            return {}

    async def assess_sla_violation_risk(self, service_name: str) -> List[SLAViolationRisk]:
        """Assess risk of SLA violations for a service."""
        try:
            assessments = []
            recent_metrics = list(self.metrics_history[service_name])[-10:]

            if len(recent_metrics) < 5:
                logger.warning(f"Insufficient data for SLA risk assessment: {service_name}")
                return []

            latest_metrics = recent_metrics[-1]

            # Check each SLA metric
            for sla_metric, threshold in self.sla_thresholds.items():
                if hasattr(latest_metrics, sla_metric):
                    current_value = float(getattr(latest_metrics, sla_metric))

                    # Predict future value
                    recent_values = [float(getattr(m, sla_metric)) for m in recent_metrics]
                    trend = self._calculate_trend(recent_values)
                    predicted_value = current_value + (trend * 6)  # Predict 6 time periods ahead

                    # Calculate violation probability
                    violation_prob = self._calculate_violation_probability(
                        current_value, predicted_value, threshold, sla_metric
                    )

                    if violation_prob > 0.1:  # Only report if >10% chance
                        # Estimate time to violation
                        time_to_violation = self._estimate_time_to_violation(
                            current_value, predicted_value, threshold, trend
                        )

                        assessment = SLAViolationRisk(
                            assessment_id=f"sla_{service_name}_{sla_metric}_{int(time.time())}",
                            service_name=service_name,
                            sla_metric=sla_metric,
                            sla_threshold=np.float32(threshold),
                            current_value=np.float32(current_value),
                            predicted_value=np.float32(predicted_value),
                            violation_probability=np.float32(violation_prob),
                            time_to_violation=time_to_violation,
                            risk_factors=self._identify_sla_risk_factors(latest_metrics, sla_metric),
                            mitigation_strategies=self._generate_sla_mitigation_strategies(sla_metric)
                        )

                        assessments.append(assessment)

            self.sla_assessments[service_name] = assessments
            if assessments:
                self.metrics['sla_violations_prevented'] += 1

            return assessments

        except Exception as e:
            logger.error(f"Error assessing SLA violation risk for {service_name}: {e}")
            return []

    def _calculate_violation_probability(self, current_value: float, predicted_value: float,
                                       threshold: float, metric_name: str) -> float:
        """Calculate probability of SLA violation."""
        try:
            # For metrics where higher values are worse (response time, error rate)
            worse_is_higher = metric_name in [
                'response_time_avg', 'response_time_p95', 'response_time_p99', 'error_rate'
            ]

            if worse_is_higher:
                if predicted_value > threshold:
                    # Calculate how much over threshold
                    excess = (predicted_value - threshold) / threshold
                    return min(0.5 + excess, 0.95)
                else:
                    # Calculate how close to threshold
                    proximity = predicted_value / threshold
                    return max(proximity - 0.8, 0) / 0.2 * 0.3  # Up to 30% risk when close
            else:
                # For metrics where lower values are worse (availability, throughput)
                if predicted_value < threshold:
                    deficit = (threshold - predicted_value) / threshold
                    return min(0.5 + deficit, 0.95)
                else:
                    proximity = threshold / predicted_value
                    return max(proximity - 0.8, 0) / 0.2 * 0.3

        except Exception:
            return 0.0

    def _estimate_time_to_violation(self, current_value: float, predicted_value: float,
                                  threshold: float, trend: float) -> Optional[timedelta]:
        """Estimate time until SLA violation occurs."""
        try:
            if trend == 0:
                return None

            # Calculate steps needed to reach threshold
            if trend > 0:  # Increasing trend
                steps_to_violation = (threshold - current_value) / trend
            else:  # Decreasing trend
                steps_to_violation = (current_value - threshold) / abs(trend)

            if steps_to_violation <= 0:
                return timedelta(minutes=15)  # Immediate risk

            # Assume each step is 10 minutes (adjust based on your metric collection interval)
            return timedelta(minutes=int(steps_to_violation * 10))

        except Exception:
            return None

    def _identify_sla_risk_factors(self, metrics: PerformanceMetrics, sla_metric: str) -> List[str]:
        """Identify factors that could contribute to SLA violations."""
        risk_factors = []

        if sla_metric in ['response_time_avg', 'response_time_p95', 'response_time_p99']:
            if metrics.cpu_usage > 0.8:
                risk_factors.append("High CPU usage affecting response time")
            if metrics.db_query_time_avg > 200:
                risk_factors.append("Slow database queries")
            if metrics.cache_hit_rate < 0.7:
                risk_factors.append("Poor cache performance")

        elif sla_metric == 'error_rate':
            if metrics.queue_depth > 50:
                risk_factors.append("Queue backlog causing timeouts")
            if metrics.thread_pool_utilization > 0.9:
                risk_factors.append("Thread pool saturation")

        elif sla_metric == 'throughput':
            if metrics.memory_usage > 0.9:
                risk_factors.append("Memory pressure limiting throughput")
            if metrics.disk_io_rate > 500:
                risk_factors.append("I/O bottleneck affecting throughput")

        return risk_factors

    def _generate_sla_mitigation_strategies(self, sla_metric: str) -> List[str]:
        """Generate strategies to mitigate SLA violation risk."""
        strategies = []

        if sla_metric in ['response_time_avg', 'response_time_p95', 'response_time_p99']:
            strategies.extend([
                "Scale out application instances",
                "Optimize slow database queries",
                "Increase cache size and hit rate",
                "Enable request queuing and load balancing"
            ])

        elif sla_metric == 'error_rate':
            strategies.extend([
                "Implement circuit breaker pattern",
                "Increase timeout thresholds",
                "Add retry logic with exponential backoff",
                "Scale up resources to handle load"
            ])

        elif sla_metric == 'throughput':
            strategies.extend([
                "Add more worker processes",
                "Optimize algorithm efficiency",
                "Implement asynchronous processing",
                "Scale up compute resources"
            ])

        elif sla_metric == 'availability':
            strategies.extend([
                "Implement health checks and auto-restart",
                "Set up failover to backup instances",
                "Monitor and prevent resource exhaustion",
                "Implement graceful degradation"
            ])

        return strategies

    async def get_performance_insights(self, service_name: str) -> Dict[str, Any]:
        """Get comprehensive performance insights for a service."""
        try:
            insights = {
                'service_name': service_name,
                'timestamp': datetime.now().isoformat(),
                'overall_health': 'unknown',
                'performance_score': 0.0,
                'bottleneck_predictions': [],
                'optimization_opportunities': [],
                'capacity_forecasts': [],
                'sla_risks': [],
                'recommendations': {
                    'immediate': [],
                    'short_term': [],
                    'long_term': []
                }
            }

            # Get latest performance data
            if service_name not in self.metrics_history or not self.metrics_history[service_name]:
                insights['overall_health'] = 'no_data'
                return insights

            latest_metrics = list(self.metrics_history[service_name])[-1]

            # Calculate performance score
            insights['performance_score'] = self._calculate_performance_score(latest_metrics)

            # Determine overall health
            if insights['performance_score'] >= 0.8:
                insights['overall_health'] = 'excellent'
            elif insights['performance_score'] >= 0.7:
                insights['overall_health'] = 'good'
            elif insights['performance_score'] >= 0.5:
                insights['overall_health'] = 'fair'
            elif insights['performance_score'] >= 0.3:
                insights['overall_health'] = 'poor'
            else:
                insights['overall_health'] = 'critical'

            # Get active predictions and recommendations
            insights['bottleneck_predictions'] = [
                {
                    'type': pred.bottleneck_type.value,
                    'severity': pred.severity.value,
                    'confidence': float(pred.confidence),
                    'expected_occurrence': pred.expected_occurrence.isoformat(),
                    'prevention_window_minutes': pred.prevention_window.total_seconds() / 60
                }
                for pred in self.bottleneck_predictions.get(service_name, [])[-3:]  # Latest 3
            ]

            insights['optimization_opportunities'] = [
                {
                    'type': opt.optimization_type.value,
                    'priority_score': float(opt.priority_score),
                    'expected_improvement': opt.expected_improvement,
                    'implementation_effort': opt.implementation_effort,
                    'timeline_hours': opt.expected_timeline.total_seconds() / 3600
                }
                for opt in self.optimization_recommendations.get(service_name, [])[:5]  # Top 5
            ]

            insights['capacity_forecasts'] = [
                {
                    'metric': forecast.metric_name,
                    'current_value': float(forecast.current_value),
                    'growth_rate': float(forecast.growth_rate),
                    'capacity_limit': float(forecast.capacity_limit),
                    'time_to_capacity_days': forecast.time_to_capacity.days if forecast.time_to_capacity else None
                }
                for forecast in self.capacity_forecasts.get(service_name, [])[-3:]  # Latest 3
            ]

            insights['sla_risks'] = [
                {
                    'metric': risk.sla_metric,
                    'violation_probability': float(risk.violation_probability),
                    'current_value': float(risk.current_value),
                    'threshold': float(risk.sla_threshold),
                    'time_to_violation_hours': risk.time_to_violation.total_seconds() / 3600 if risk.time_to_violation else None
                }
                for risk in self.sla_assessments.get(service_name, [])
            ]

            # Generate recommendations
            insights['recommendations'] = self._generate_performance_recommendations(
                latest_metrics, insights
            )

            return insights

        except Exception as e:
            logger.error(f"Error getting performance insights for {service_name}: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    def _calculate_performance_score(self, metrics: PerformanceMetrics) -> float:
        """Calculate overall performance score (0-1) based on metrics."""
        try:
            score = 0.0
            weights = {
                'response_time': 0.25,
                'error_rate': 0.20,
                'resource_utilization': 0.20,
                'throughput': 0.15,
                'cache_performance': 0.10,
                'queue_health': 0.10
            }

            # Response time score (lower is better)
            response_score = max(0, 1 - (float(metrics.response_time_avg) / 2000))  # 2s max
            score += response_score * weights['response_time']

            # Error rate score (lower is better)
            error_score = max(0, 1 - float(metrics.error_rate) * 20)  # 5% max
            score += error_score * weights['error_rate']

            # Resource utilization score (moderate is best)
            cpu_score = 1 - abs(float(metrics.cpu_usage) - 0.7) / 0.3  # Target 70% CPU
            memory_score = 1 - abs(float(metrics.memory_usage) - 0.6) / 0.4  # Target 60% memory
            resource_score = (cpu_score + memory_score) / 2
            score += max(0, resource_score) * weights['resource_utilization']

            # Throughput score (higher is better, but normalized)
            throughput_score = min(1, float(metrics.throughput) / 200)  # 200 as good throughput
            score += throughput_score * weights['throughput']

            # Cache performance score
            cache_score = float(metrics.cache_hit_rate)
            score += cache_score * weights['cache_performance']

            # Queue health score (lower depth is better)
            queue_score = max(0, 1 - float(metrics.queue_depth) / 100)  # 100 as max acceptable
            score += queue_score * weights['queue_health']

            return max(0, min(1, score))

        except Exception:
            return 0.5  # Default middle score

    def _generate_performance_recommendations(self, metrics: PerformanceMetrics,
                                            insights: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate categorized performance recommendations."""
        recommendations = {
            'immediate': [],
            'short_term': [],
            'long_term': []
        }

        try:
            performance_score = insights['performance_score']

            # Immediate recommendations (critical issues)
            if performance_score < 0.3:
                recommendations['immediate'].extend([
                    "Scale up resources immediately - system is in critical state",
                    "Enable emergency circuit breakers to prevent cascade failures",
                    "Investigate and resolve immediate bottlenecks"
                ])

            if metrics.error_rate > 0.1:
                recommendations['immediate'].append(
                    f"High error rate ({metrics.error_rate:.1%}) - investigate and fix immediately"
                )

            if metrics.response_time_avg > 5000:
                recommendations['immediate'].append(
                    f"Critical response time ({metrics.response_time_avg:.0f}ms) - immediate attention required"
                )

            # Short-term recommendations (performance improvements)
            if insights['bottleneck_predictions']:
                recommendations['short_term'].append(
                    f"Address predicted {len(insights['bottleneck_predictions'])} bottlenecks in next 2 hours"
                )

            if metrics.cache_hit_rate < 0.6:
                recommendations['short_term'].append(
                    f"Improve cache hit rate from {metrics.cache_hit_rate:.1%} to >80%"
                )

            if metrics.cpu_usage > 0.8:
                recommendations['short_term'].append("Scale out to reduce CPU utilization")

            # Long-term recommendations (optimization and capacity planning)
            if insights['capacity_forecasts']:
                recommendations['long_term'].append(
                    "Review capacity forecasts and plan for future scaling needs"
                )

            if insights['optimization_opportunities']:
                top_optimization = insights['optimization_opportunities'][0]
                recommendations['long_term'].append(
                    f"Implement {top_optimization['type']} optimization for long-term performance gains"
                )

            if performance_score > 0.8:
                recommendations['long_term'].append(
                    "System performing well - focus on efficiency optimizations and cost reduction"
                )

            return recommendations

        except Exception as e:
            logger.error(f"Error generating performance recommendations: {e}")
            return recommendations

    async def get_system_overview(self) -> Dict[str, Any]:
        """Get overview of performance prediction system status."""
        try:
            overview = {
                'system_status': 'active',
                'ml_models_available': ML_AVAILABLE,
                'services_monitored': len(self.metrics_history),
                'total_predictions_made': self.metrics['predictions_made'],
                'prediction_accuracy': self.metrics['average_prediction_accuracy'],
                'performance_metrics': self.metrics.copy(),
                'active_predictions': 0,
                'active_recommendations': 0,
                'system_health_score': 0.0,
                'last_updated': datetime.now().isoformat()
            }

            # Count active predictions and recommendations
            for service_predictions in self.bottleneck_predictions.values():
                overview['active_predictions'] += len([
                    p for p in service_predictions
                    if p.expected_occurrence > datetime.now()
                ])

            for service_recommendations in self.optimization_recommendations.values():
                overview['active_recommendations'] += len(service_recommendations)

            # Calculate system health score
            if overview['services_monitored'] > 0:
                service_scores = []
                for service_name in self.metrics_history:
                    if self.metrics_history[service_name]:
                        latest_metrics = list(self.metrics_history[service_name])[-1]
                        service_score = self._calculate_performance_score(latest_metrics)
                        service_scores.append(service_score)

                overview['system_health_score'] = np.mean(service_scores) if service_scores else 0.0

            # Add model status
            overview['model_status'] = {
                'bottleneck_predictor': 'active' if self.bottleneck_predictor is not None else 'unavailable',
                'capacity_forecaster': 'active' if self.capacity_forecaster is not None else 'unavailable',
                'response_time_predictor': 'active' if self.response_time_predictor is not None else 'unavailable',
                'optimization_scorer': 'active' if self.optimization_scorer is not None else 'unavailable'
            }

            return overview

        except Exception as e:
            logger.error(f"Error getting system overview: {e}")
            return {
                'system_status': 'error',
                'error': str(e),
                'last_updated': datetime.now().isoformat()
            }

    async def cleanup_old_data(self) -> Dict[str, int]:
        """Clean up old predictions, recommendations, and forecasts."""
        try:
            cleanup_counts = {
                'predictions_cleaned': 0,
                'recommendations_cleaned': 0,
                'forecasts_cleaned': 0,
                'assessments_cleaned': 0
            }

            cutoff_time = datetime.now() - timedelta(days=7)

            # Clean old predictions
            for service_name in self.bottleneck_predictions:
                original_count = len(self.bottleneck_predictions[service_name])
                self.bottleneck_predictions[service_name] = [
                    pred for pred in self.bottleneck_predictions[service_name]
                    if pred.predicted_at > cutoff_time
                ]
                cleanup_counts['predictions_cleaned'] += (
                    original_count - len(self.bottleneck_predictions[service_name])
                )

            # Clean old recommendations
            for service_name in self.optimization_recommendations:
                original_count = len(self.optimization_recommendations[service_name])
                # Keep only recent recommendations or high-priority ones
                self.optimization_recommendations[service_name] = [
                    rec for rec in self.optimization_recommendations[service_name]
                    if (rec.priority_score > 0.8 or
                        datetime.now() - timedelta(days=3) < datetime.now())  # Keep recent or high-priority
                ][:10]  # Keep max 10 per service

                cleanup_counts['recommendations_cleaned'] += (
                    original_count - len(self.optimization_recommendations[service_name])
                )

            # Clean old forecasts
            for service_name in self.capacity_forecasts:
                original_count = len(self.capacity_forecasts[service_name])
                self.capacity_forecasts[service_name] = [
                    forecast for forecast in self.capacity_forecasts[service_name]
                    if forecast.forecast_id and cutoff_time < datetime.now()  # Keep recent forecasts
                ][-5:]  # Keep only 5 most recent per service

                cleanup_counts['forecasts_cleaned'] += (
                    original_count - len(self.capacity_forecasts[service_name])
                )

            # Clean old SLA assessments
            for service_name in self.sla_assessments:
                original_count = len(self.sla_assessments[service_name])
                self.sla_assessments[service_name] = [
                    assessment for assessment in self.sla_assessments[service_name]
                    if assessment.time_to_violation is None or
                       assessment.time_to_violation > timedelta(hours=1)  # Keep active risks
                ]

                cleanup_counts['assessments_cleaned'] += (
                    original_count - len(self.sla_assessments[service_name])
                )

            total_cleaned = sum(cleanup_counts.values())
            if total_cleaned > 0:
                logger.info(f"Cleaned up {total_cleaned} old performance prediction records")

            return cleanup_counts

        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return {'error': str(e)}


# Testing and simulation functions
async def simulate_performance_prediction_test():
    """Simulate comprehensive performance prediction system test."""
    try:
        logger.info("🧪 Starting Performance Prediction System Simulation")

        # Initialize system
        predictor = PerformancePredictor({
            'sla_thresholds': {
                'response_time_avg': 1500,
                'response_time_p95': 3000,
                'error_rate': 0.02,
                'throughput': 80
            }
        })

        # Initialize ML models
        await predictor.initialize_ml_models()

        # Simulate various performance scenarios
        test_scenarios = [
            {
                'name': 'Normal Operations',
                'service': 'enhanced_ml_personalization_engine',
                'metrics': {
                    'cpu_usage': 0.45, 'memory_usage': 0.55, 'disk_io_rate': 120,
                    'network_io_rate': 60, 'request_rate': 150, 'response_time_avg': 800,
                    'error_rate': 0.005, 'throughput': 140, 'db_query_time_avg': 80,
                    'cache_hit_rate': 0.85, 'queue_depth': 15, 'active_threads': 45
                }
            },
            {
                'name': 'High Load Stress Test',
                'service': 'predictive_churn_prevention',
                'metrics': {
                    'cpu_usage': 0.88, 'memory_usage': 0.75, 'disk_io_rate': 350,
                    'network_io_rate': 180, 'request_rate': 400, 'response_time_avg': 1800,
                    'error_rate': 0.03, 'throughput': 300, 'db_query_time_avg': 250,
                    'cache_hit_rate': 0.65, 'queue_depth': 85, 'active_threads': 120
                }
            },
            {
                'name': 'Memory Pressure Scenario',
                'service': 'real_time_model_training',
                'metrics': {
                    'cpu_usage': 0.6, 'memory_usage': 0.94, 'disk_io_rate': 200,
                    'network_io_rate': 90, 'request_rate': 200, 'response_time_avg': 2200,
                    'error_rate': 0.06, 'throughput': 160, 'db_query_time_avg': 150,
                    'cache_hit_rate': 0.45, 'queue_depth': 65, 'active_threads': 80
                }
            },
            {
                'name': 'Database Bottleneck',
                'service': 'multimodal_communication_optimizer',
                'metrics': {
                    'cpu_usage': 0.5, 'memory_usage': 0.6, 'disk_io_rate': 180,
                    'network_io_rate': 70, 'request_rate': 180, 'response_time_avg': 3500,
                    'error_rate': 0.08, 'throughput': 120, 'db_query_time_avg': 450,
                    'cache_hit_rate': 0.75, 'queue_depth': 95, 'active_threads': 60
                }
            }
        ]

        test_results = []

        for scenario in test_scenarios:
            logger.info(f"\n🎯 Testing Scenario: {scenario['name']}")

            # Collect metrics
            metrics = await predictor.collect_performance_metrics(
                scenario['service'], scenario['metrics']
            )

            # Generate historical data for better predictions
            for _ in range(20):
                # Add slight variations to build history
                varied_metrics = scenario['metrics'].copy()
                for key, value in varied_metrics.items():
                    if isinstance(value, (int, float)):
                        varied_metrics[key] = value * (0.9 + 0.2 * np.random.random())

                await predictor.collect_performance_metrics(scenario['service'], varied_metrics)

            # Test bottleneck prediction
            bottleneck_predictions = await predictor.predict_bottlenecks(scenario['service'])

            # Test optimization recommendations
            optimizations = await predictor.generate_optimization_recommendations(scenario['service'])

            # Test capacity forecasting
            capacity_forecast = await predictor.forecast_capacity(
                scenario['service'], 'cpu_usage', timedelta(days=3)
            )

            # Test SLA risk assessment
            sla_risks = await predictor.assess_sla_violation_risk(scenario['service'])

            # Get comprehensive insights
            insights = await predictor.get_performance_insights(scenario['service'])

            # Collect results
            result = {
                'scenario': scenario['name'],
                'service': scenario['service'],
                'performance_score': insights.get('performance_score', 0),
                'overall_health': insights.get('overall_health', 'unknown'),
                'bottlenecks_predicted': len(bottleneck_predictions),
                'optimizations_recommended': len(optimizations),
                'capacity_forecast_available': capacity_forecast is not None,
                'sla_risks_identified': len(sla_risks),
                'insights_generated': len(insights.get('recommendations', {}).get('immediate', []))
            }

            if bottleneck_predictions:
                result['primary_bottleneck'] = bottleneck_predictions[0].bottleneck_type.value
                result['bottleneck_confidence'] = float(bottleneck_predictions[0].confidence)

            if optimizations:
                result['top_optimization'] = optimizations[0].optimization_type.value
                result['optimization_priority'] = float(optimizations[0].priority_score)

            if capacity_forecast:
                result['capacity_growth_rate'] = float(capacity_forecast.growth_rate)

            test_results.append(result)

            logger.info(f"✅ Scenario completed: {scenario['name']}")

        # Get system overview
        system_overview = await predictor.get_system_overview()

        # Performance summary
        avg_performance_score = np.mean([r.get('performance_score', 0) for r in test_results])
        total_predictions = sum(r.get('bottlenecks_predicted', 0) for r in test_results)
        total_optimizations = sum(r.get('optimizations_recommended', 0) for r in test_results)

        logger.info(f"\n📊 Performance Prediction Test Summary:")
        logger.info(f"   Average Performance Score: {avg_performance_score:.2f}")
        logger.info(f"   Total Bottleneck Predictions: {total_predictions}")
        logger.info(f"   Total Optimization Recommendations: {total_optimizations}")
        logger.info(f"   System Health Score: {system_overview.get('system_health_score', 0):.2f}")
        logger.info(f"   Services Monitored: {system_overview.get('services_monitored', 0)}")

        return {
            'test_results': test_results,
            'system_overview': system_overview,
            'summary': {
                'scenarios_tested': len(test_scenarios),
                'average_performance_score': avg_performance_score,
                'total_bottleneck_predictions': total_predictions,
                'total_optimization_recommendations': total_optimizations,
                'system_health_score': system_overview.get('system_health_score', 0)
            }
        }

    except Exception as e:
        logger.error(f"Error in performance prediction simulation: {e}")
        raise


if __name__ == "__main__":
    """Run performance prediction system simulation for testing."""
    import asyncio

    async def main():
        try:
            # Run simulation
            test_results = await simulate_performance_prediction_test()

            # Save results
            results_file = Path("scripts/performance_prediction_test_results.json")
            with open(results_file, 'w') as f:
                json.dump(test_results, f, indent=2, default=str)

            print(f"\n📄 Test results saved to: {results_file}")

        except Exception as e:
            print(f"❌ Test failed: {e}")
            raise

    asyncio.run(main())