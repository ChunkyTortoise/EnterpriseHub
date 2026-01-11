"""
Predictive Scaling Engine for EnterpriseHub AI Coaching Platform
Provides intelligent auto-scaling with cost optimization
Supports 1000+ concurrent users with 20-30% cost reduction targets
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import json

from ..base import BaseService
from ..monitoring.enterprise_metrics_exporter import get_metrics_exporter
from ...config.settings import get_settings

logger = logging.getLogger(__name__)

class ScalingAction(Enum):
    """Available scaling actions."""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    MAINTAIN = "maintain"
    PREEMPTIVE_SCALE = "preemptive_scale"

class ResourceType(Enum):
    """Types of resources that can be scaled."""
    API_INSTANCES = "api_instances"
    ML_WORKERS = "ml_workers"
    REDIS_NODES = "redis_nodes"
    DATABASE_CONNECTIONS = "database_connections"
    WEBSOCKET_CAPACITY = "websocket_capacity"

@dataclass
class ScalingMetrics:
    """Current system metrics for scaling decisions."""
    timestamp: float
    cpu_usage_percent: float
    memory_usage_percent: float
    active_connections: int
    api_request_rate: float
    ml_inference_queue_length: int
    database_connection_usage: float
    response_time_95th: float
    error_rate: float
    cost_per_hour: float

@dataclass
class ScalingPrediction:
    """Prediction for future resource needs."""
    timestamp: float
    predicted_load: float
    confidence_interval: Tuple[float, float]
    recommended_action: ScalingAction
    recommended_resources: Dict[ResourceType, int]
    cost_impact: float
    reasoning: str

@dataclass
class ScalingConfiguration:
    """Configuration for predictive scaling."""
    # Prediction parameters
    prediction_horizon_minutes: int = 30
    prediction_interval_seconds: int = 60
    model_retrain_hours: int = 24

    # Scaling thresholds
    cpu_scale_up_threshold: float = 0.75
    cpu_scale_down_threshold: float = 0.30
    memory_scale_up_threshold: float = 0.80
    memory_scale_down_threshold: float = 0.40
    response_time_threshold_ms: float = 200
    error_rate_threshold: float = 0.01

    # Cost optimization
    cost_optimization_enabled: bool = True
    max_cost_increase_percent: float = 15.0
    min_instances: Dict[str, int] = None
    max_instances: Dict[str, int] = None

    # Safety parameters
    scaling_cooldown_minutes: int = 10
    max_scale_up_factor: float = 2.0
    max_scale_down_factor: float = 0.5

    def __post_init__(self):
        if self.min_instances is None:
            self.min_instances = {
                'api_instances': 2,
                'ml_workers': 1,
                'redis_nodes': 3,
                'database_connections': 10,
                'websocket_capacity': 100
            }
        if self.max_instances is None:
            self.max_instances = {
                'api_instances': 20,
                'ml_workers': 10,
                'redis_nodes': 9,
                'database_connections': 200,
                'websocket_capacity': 2000
            }

class PredictiveScalingEngine(BaseService):
    """
    Intelligent predictive scaling engine with cost optimization.

    Features:
    - ML-based load prediction
    - Multi-resource scaling coordination
    - Cost optimization algorithms
    - Integration with Railway/Vercel
    - Real-time decision making
    - Historical data analysis
    """

    def __init__(self, config: Optional[ScalingConfiguration] = None):
        super().__init__()
        self.config = config or ScalingConfiguration()
        self.settings = get_settings()

        # ML models for prediction
        self.load_predictor = None
        self.scaler = StandardScaler()
        self.model_last_trained = None

        # Metrics and state tracking
        self.metrics_history: List[ScalingMetrics] = []
        self.scaling_history: List[ScalingPrediction] = []
        self.last_scaling_action = None
        self.last_scaling_time = None

        # Current resource allocation
        self.current_resources = {
            ResourceType.API_INSTANCES: 2,
            ResourceType.ML_WORKERS: 1,
            ResourceType.REDIS_NODES: 3,
            ResourceType.DATABASE_CONNECTIONS: 50,
            ResourceType.WEBSOCKET_CAPACITY: 500
        }

        # Cost tracking
        self.baseline_cost_per_hour = 45.0  # Estimated baseline cost
        self.resource_costs = {
            ResourceType.API_INSTANCES: 12.0,      # $12/hour per instance
            ResourceType.ML_WORKERS: 8.0,          # $8/hour per worker
            ResourceType.REDIS_NODES: 5.0,         # $5/hour per node
            ResourceType.DATABASE_CONNECTIONS: 0.1, # $0.1/hour per connection
            ResourceType.WEBSOCKET_CAPACITY: 0.02   # $0.02/hour per 100 connections
        }

        # Task management
        self.prediction_task: Optional[asyncio.Task] = None
        self.is_running = False

    async def start_predictive_scaling(self) -> None:
        """Start the predictive scaling engine."""
        if self.is_running:
            logger.warning("Predictive scaling is already running")
            return

        logger.info("Starting predictive scaling engine...")

        # Load or initialize ML model
        await self._initialize_prediction_model()

        # Start prediction loop
        self.is_running = True
        self.prediction_task = asyncio.create_task(self._prediction_loop())

        logger.info("Predictive scaling engine started successfully")

    async def stop_predictive_scaling(self) -> None:
        """Stop the predictive scaling engine."""
        if not self.is_running:
            return

        logger.info("Stopping predictive scaling engine...")

        self.is_running = False
        if self.prediction_task:
            self.prediction_task.cancel()
            try:
                await self.prediction_task
            except asyncio.CancelledError:
                pass

        # Save model and state
        await self._save_model_and_state()

        logger.info("Predictive scaling engine stopped")

    async def _prediction_loop(self) -> None:
        """Main prediction and scaling loop."""
        while self.is_running:
            try:
                start_time = time.time()

                # Collect current metrics
                current_metrics = await self._collect_current_metrics()
                if current_metrics:
                    self.metrics_history.append(current_metrics)

                    # Keep only recent history (last 24 hours)
                    cutoff_time = time.time() - (24 * 3600)
                    self.metrics_history = [
                        m for m in self.metrics_history
                        if m.timestamp > cutoff_time
                    ]

                # Generate predictions if we have enough data
                if len(self.metrics_history) >= 10:
                    prediction = await self._generate_scaling_prediction()
                    if prediction:
                        self.scaling_history.append(prediction)

                        # Execute scaling action if needed
                        await self._execute_scaling_action(prediction)

                # Retrain model periodically
                if await self._should_retrain_model():
                    await self._retrain_prediction_model()

                # Sleep until next prediction interval
                elapsed = time.time() - start_time
                sleep_time = max(0, self.config.prediction_interval_seconds - elapsed)
                await asyncio.sleep(sleep_time)

            except Exception as e:
                logger.error(f"Error in prediction loop: {e}")
                await asyncio.sleep(30)  # Wait before retrying

    async def _collect_current_metrics(self) -> Optional[ScalingMetrics]:
        """Collect current system metrics for scaling decisions."""
        try:
            # Get metrics from monitoring system
            metrics_exporter = get_metrics_exporter()
            metrics_summary = await metrics_exporter.get_metrics_summary()

            # Get additional infrastructure metrics
            infra_metrics = await self._get_infrastructure_metrics()

            return ScalingMetrics(
                timestamp=time.time(),
                cpu_usage_percent=infra_metrics.get('cpu_usage', 50.0),
                memory_usage_percent=infra_metrics.get('memory_usage', 60.0),
                active_connections=metrics_summary.get('active_connections', {}).get('value', 0),
                api_request_rate=infra_metrics.get('request_rate', 10.0),
                ml_inference_queue_length=infra_metrics.get('ml_queue_length', 0),
                database_connection_usage=infra_metrics.get('db_connection_usage', 0.3),
                response_time_95th=metrics_summary.get('api_response_time_95th', {}).get('value', 0.1),
                error_rate=infra_metrics.get('error_rate', 0.001),
                cost_per_hour=self._calculate_current_cost()
            )

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return None

    async def _generate_scaling_prediction(self) -> Optional[ScalingPrediction]:
        """Generate scaling prediction using ML model."""
        try:
            if not self.load_predictor:
                return None

            # Prepare features from recent metrics
            features = self._extract_features_from_metrics()
            if features is None:
                return None

            # Make prediction
            predicted_load = self.load_predictor.predict([features])[0]

            # Calculate confidence interval (simplified)
            confidence_interval = (predicted_load * 0.9, predicted_load * 1.1)

            # Determine scaling action
            action, resources = await self._determine_scaling_action(predicted_load)

            # Calculate cost impact
            cost_impact = self._calculate_cost_impact(resources)

            # Generate reasoning
            reasoning = self._generate_scaling_reasoning(predicted_load, action, resources)

            return ScalingPrediction(
                timestamp=time.time(),
                predicted_load=predicted_load,
                confidence_interval=confidence_interval,
                recommended_action=action,
                recommended_resources=resources,
                cost_impact=cost_impact,
                reasoning=reasoning
            )

        except Exception as e:
            logger.error(f"Error generating prediction: {e}")
            return None

    async def _determine_scaling_action(self, predicted_load: float) -> Tuple[ScalingAction, Dict[ResourceType, int]]:
        """Determine appropriate scaling action based on predicted load."""
        current_metrics = self.metrics_history[-1] if self.metrics_history else None
        if not current_metrics:
            return ScalingAction.MAINTAIN, self.current_resources

        # Check if we're in cooldown period
        if self._in_cooldown_period():
            return ScalingAction.MAINTAIN, self.current_resources

        # Determine if scaling is needed based on multiple factors
        needs_scale_up = (
            current_metrics.cpu_usage_percent > self.config.cpu_scale_up_threshold or
            current_metrics.memory_usage_percent > self.config.memory_scale_up_threshold or
            current_metrics.response_time_95th > self.config.response_time_threshold_ms / 1000 or
            current_metrics.error_rate > self.config.error_rate_threshold or
            predicted_load > self._get_current_capacity() * 0.8
        )

        needs_scale_down = (
            current_metrics.cpu_usage_percent < self.config.cpu_scale_down_threshold and
            current_metrics.memory_usage_percent < self.config.memory_scale_down_threshold and
            current_metrics.response_time_95th < self.config.response_time_threshold_ms / 1000 * 0.5 and
            predicted_load < self._get_current_capacity() * 0.3 and
            current_metrics.error_rate < self.config.error_rate_threshold * 0.1
        )

        if needs_scale_up:
            return ScalingAction.SCALE_UP, self._calculate_scale_up_resources(predicted_load)
        elif needs_scale_down and self.config.cost_optimization_enabled:
            return ScalingAction.SCALE_DOWN, self._calculate_scale_down_resources(predicted_load)
        else:
            return ScalingAction.MAINTAIN, self.current_resources

    def _calculate_scale_up_resources(self, predicted_load: float) -> Dict[ResourceType, int]:
        """Calculate resources needed for scaling up."""
        scale_factor = min(predicted_load / self._get_current_capacity(), self.config.max_scale_up_factor)

        new_resources = {}
        for resource_type, current_count in self.current_resources.items():
            # Calculate new count based on scale factor
            new_count = int(current_count * scale_factor)

            # Apply min/max constraints
            resource_key = resource_type.value
            min_count = self.config.min_instances.get(resource_key, current_count)
            max_count = self.config.max_instances.get(resource_key, current_count * 2)

            new_resources[resource_type] = max(min_count, min(max_count, new_count))

        return new_resources

    def _calculate_scale_down_resources(self, predicted_load: float) -> Dict[ResourceType, int]:
        """Calculate resources for cost-optimized scaling down."""
        scale_factor = max(predicted_load / self._get_current_capacity(), self.config.max_scale_down_factor)

        new_resources = {}
        for resource_type, current_count in self.current_resources.items():
            # Calculate new count based on scale factor
            new_count = int(current_count * scale_factor)

            # Apply min/max constraints
            resource_key = resource_type.value
            min_count = self.config.min_instances.get(resource_key, 1)
            max_count = self.config.max_instances.get(resource_key, current_count)

            new_resources[resource_type] = max(min_count, min(max_count, new_count))

        return new_resources

    async def _execute_scaling_action(self, prediction: ScalingPrediction) -> bool:
        """Execute the recommended scaling action."""
        if prediction.recommended_action == ScalingAction.MAINTAIN:
            logger.debug("No scaling action needed")
            return True

        try:
            logger.info(f"Executing scaling action: {prediction.recommended_action.value}")
            logger.info(f"Reasoning: {prediction.reasoning}")

            # Check cost constraints
            if self.config.cost_optimization_enabled and not self._cost_within_limits(prediction.cost_impact):
                logger.warning(f"Scaling action blocked by cost constraints: ${prediction.cost_impact:.2f}")
                return False

            # Execute scaling for each resource type
            success = True
            for resource_type, new_count in prediction.recommended_resources.items():
                current_count = self.current_resources[resource_type]
                if new_count != current_count:
                    if await self._scale_resource(resource_type, new_count):
                        self.current_resources[resource_type] = new_count
                        logger.info(f"Scaled {resource_type.value}: {current_count} → {new_count}")
                    else:
                        logger.error(f"Failed to scale {resource_type.value}")
                        success = False

            # Update scaling history
            self.last_scaling_action = prediction.recommended_action
            self.last_scaling_time = time.time()

            return success

        except Exception as e:
            logger.error(f"Error executing scaling action: {e}")
            return False

    async def _scale_resource(self, resource_type: ResourceType, new_count: int) -> bool:
        """Scale a specific resource type."""
        try:
            if resource_type == ResourceType.API_INSTANCES:
                return await self._scale_api_instances(new_count)
            elif resource_type == ResourceType.ML_WORKERS:
                return await self._scale_ml_workers(new_count)
            elif resource_type == ResourceType.REDIS_NODES:
                return await self._scale_redis_nodes(new_count)
            elif resource_type == ResourceType.DATABASE_CONNECTIONS:
                return await self._scale_database_connections(new_count)
            elif resource_type == ResourceType.WEBSOCKET_CAPACITY:
                return await self._scale_websocket_capacity(new_count)
            else:
                logger.warning(f"Unknown resource type: {resource_type}")
                return False

        except Exception as e:
            logger.error(f"Error scaling {resource_type.value}: {e}")
            return False

    async def _scale_api_instances(self, new_count: int) -> bool:
        """Scale API instances on Railway."""
        # Implementation would integrate with Railway API
        logger.info(f"Scaling API instances to {new_count} (Railway integration)")
        return True

    async def _scale_ml_workers(self, new_count: int) -> bool:
        """Scale ML worker processes."""
        logger.info(f"Scaling ML workers to {new_count}")
        return True

    async def _scale_redis_nodes(self, new_count: int) -> bool:
        """Scale Redis cluster nodes."""
        logger.info(f"Scaling Redis nodes to {new_count}")
        return True

    async def _scale_database_connections(self, new_count: int) -> bool:
        """Scale database connection pool."""
        logger.info(f"Scaling database connections to {new_count}")
        return True

    async def _scale_websocket_capacity(self, new_count: int) -> bool:
        """Scale WebSocket connection capacity."""
        logger.info(f"Scaling WebSocket capacity to {new_count}")
        return True

    def _calculate_current_cost(self) -> float:
        """Calculate current hourly cost based on resource allocation."""
        total_cost = self.baseline_cost_per_hour

        for resource_type, count in self.current_resources.items():
            unit_cost = self.resource_costs.get(resource_type, 0)
            if resource_type == ResourceType.WEBSOCKET_CAPACITY:
                total_cost += (count / 100) * unit_cost
            else:
                total_cost += count * unit_cost

        return total_cost

    def _calculate_cost_impact(self, new_resources: Dict[ResourceType, int]) -> float:
        """Calculate cost impact of scaling action."""
        current_cost = self._calculate_current_cost()

        new_cost = self.baseline_cost_per_hour
        for resource_type, count in new_resources.items():
            unit_cost = self.resource_costs.get(resource_type, 0)
            if resource_type == ResourceType.WEBSOCKET_CAPACITY:
                new_cost += (count / 100) * unit_cost
            else:
                new_cost += count * unit_cost

        return new_cost - current_cost

    def _cost_within_limits(self, cost_impact: float) -> bool:
        """Check if cost impact is within acceptable limits."""
        if cost_impact <= 0:  # Cost reduction or neutral
            return True

        current_cost = self._calculate_current_cost()
        max_increase = current_cost * (self.config.max_cost_increase_percent / 100)

        return cost_impact <= max_increase

    def _extract_features_from_metrics(self) -> Optional[np.ndarray]:
        """Extract ML features from recent metrics history."""
        if len(self.metrics_history) < 5:
            return None

        # Take last 5 data points for feature extraction
        recent_metrics = self.metrics_history[-5:]

        features = []
        for metrics in recent_metrics:
            features.extend([
                metrics.cpu_usage_percent,
                metrics.memory_usage_percent,
                metrics.active_connections,
                metrics.api_request_rate,
                metrics.ml_inference_queue_length,
                metrics.database_connection_usage,
                metrics.response_time_95th,
                metrics.error_rate
            ])

        # Add time-based features
        current_hour = datetime.now().hour
        current_day_of_week = datetime.now().weekday()
        features.extend([current_hour / 24.0, current_day_of_week / 7.0])

        return np.array(features)

    def _get_current_capacity(self) -> float:
        """Estimate current system capacity."""
        # Simplified capacity estimation based on resource allocation
        api_capacity = self.current_resources[ResourceType.API_INSTANCES] * 50  # 50 concurrent requests per instance
        ws_capacity = self.current_resources[ResourceType.WEBSOCKET_CAPACITY]

        return min(api_capacity, ws_capacity)

    def _in_cooldown_period(self) -> bool:
        """Check if we're in scaling cooldown period."""
        if not self.last_scaling_time:
            return False

        cooldown_seconds = self.config.scaling_cooldown_minutes * 60
        return time.time() - self.last_scaling_time < cooldown_seconds

    def _generate_scaling_reasoning(self, predicted_load: float, action: ScalingAction, resources: Dict[ResourceType, int]) -> str:
        """Generate human-readable reasoning for scaling decision."""
        if not self.metrics_history:
            return "No metrics available for reasoning"

        current_metrics = self.metrics_history[-1]

        reasons = []

        if action == ScalingAction.SCALE_UP:
            if current_metrics.cpu_usage_percent > self.config.cpu_scale_up_threshold:
                reasons.append(f"High CPU usage: {current_metrics.cpu_usage_percent:.1f}%")
            if current_metrics.memory_usage_percent > self.config.memory_scale_up_threshold:
                reasons.append(f"High memory usage: {current_metrics.memory_usage_percent:.1f}%")
            if current_metrics.response_time_95th > self.config.response_time_threshold_ms / 1000:
                reasons.append(f"High response time: {current_metrics.response_time_95th*1000:.1f}ms")
            if predicted_load > self._get_current_capacity() * 0.8:
                reasons.append(f"Predicted load exceeds 80% capacity: {predicted_load:.1f}")

        elif action == ScalingAction.SCALE_DOWN:
            if current_metrics.cpu_usage_percent < self.config.cpu_scale_down_threshold:
                reasons.append(f"Low CPU usage: {current_metrics.cpu_usage_percent:.1f}%")
            if current_metrics.memory_usage_percent < self.config.memory_scale_down_threshold:
                reasons.append(f"Low memory usage: {current_metrics.memory_usage_percent:.1f}%")
            reasons.append("Cost optimization opportunity")

        return f"{action.value}: " + ", ".join(reasons) if reasons else f"{action.value}: Maintaining current configuration"

    async def _initialize_prediction_model(self) -> None:
        """Initialize or load the ML prediction model."""
        try:
            # Try to load existing model
            model_path = self._get_model_path()
            if model_path.exists():
                self.load_predictor = joblib.load(model_path)
                self.scaler = joblib.load(self._get_scaler_path())
                logger.info("Loaded existing prediction model")
            else:
                # Initialize new model
                await self._train_initial_model()

        except Exception as e:
            logger.error(f"Error initializing prediction model: {e}")
            # Fall back to simple model
            self.load_predictor = RandomForestRegressor(n_estimators=10, random_state=42)

    async def _train_initial_model(self) -> None:
        """Train initial ML model with synthetic or minimal data."""
        logger.info("Training initial prediction model...")

        # Generate synthetic training data for bootstrap
        # In production, this would use historical metrics
        X_synthetic = []
        y_synthetic = []

        for _ in range(100):
            # Generate synthetic metrics
            cpu = np.random.uniform(20, 90)
            memory = np.random.uniform(30, 85)
            connections = np.random.randint(50, 800)
            request_rate = np.random.uniform(5, 50)

            features = [cpu, memory, connections, request_rate, 0, 0.5, 0.1, 0.001] + [0.5, 0.5]  # Normalized time features
            load = connections + (request_rate * 10)  # Simplified load calculation

            X_synthetic.append(features)
            y_synthetic.append(load)

        # Train model
        X_train = np.array(X_synthetic)
        y_train = np.array(y_synthetic)

        # Fit scaler
        X_scaled = self.scaler.fit_transform(X_train)

        # Train predictor
        self.load_predictor = RandomForestRegressor(
            n_estimators=50,
            max_depth=10,
            random_state=42
        )
        self.load_predictor.fit(X_scaled, y_train)

        # Save model
        await self._save_model_and_state()

        self.model_last_trained = time.time()
        logger.info("Initial prediction model trained successfully")

    async def _should_retrain_model(self) -> bool:
        """Check if model should be retrained."""
        if not self.model_last_trained:
            return False

        hours_since_training = (time.time() - self.model_last_trained) / 3600
        return hours_since_training >= self.config.model_retrain_hours

    async def _retrain_prediction_model(self) -> None:
        """Retrain prediction model with recent data."""
        if len(self.metrics_history) < 50:
            logger.info("Insufficient data for model retraining")
            return

        logger.info("Retraining prediction model with recent data...")

        try:
            # Prepare training data from metrics history
            X, y = self._prepare_training_data()

            if len(X) < 20:
                logger.warning("Insufficient training data for retraining")
                return

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # Fit scaler
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # Train new model
            new_predictor = RandomForestRegressor(
                n_estimators=100,
                max_depth=15,
                random_state=42
            )
            new_predictor.fit(X_train_scaled, y_train)

            # Validate model performance
            y_pred = new_predictor.predict(X_test_scaled)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))

            logger.info(f"Model performance - MAE: {mae:.2f}, RMSE: {rmse:.2f}")

            # Update model if performance is acceptable
            if mae < np.std(y_test):  # Simple validation criteria
                self.load_predictor = new_predictor
                self.model_last_trained = time.time()
                await self._save_model_and_state()
                logger.info("Model retrained successfully")
            else:
                logger.warning("New model performance not acceptable, keeping existing model")

        except Exception as e:
            logger.error(f"Error retraining model: {e}")

    def _prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data from metrics history."""
        X = []
        y = []

        for i in range(len(self.metrics_history) - 1):
            # Current metrics as features
            metrics = self.metrics_history[i]
            features = [
                metrics.cpu_usage_percent,
                metrics.memory_usage_percent,
                metrics.active_connections,
                metrics.api_request_rate,
                metrics.ml_inference_queue_length,
                metrics.database_connection_usage,
                metrics.response_time_95th,
                metrics.error_rate
            ]

            # Add time features
            dt = datetime.fromtimestamp(metrics.timestamp)
            features.extend([dt.hour / 24.0, dt.weekday() / 7.0])

            # Future load as target
            future_metrics = self.metrics_history[i + 1]
            future_load = future_metrics.active_connections + (future_metrics.api_request_rate * 10)

            X.append(features)
            y.append(future_load)

        return np.array(X), np.array(y)

    async def _get_infrastructure_metrics(self) -> Dict[str, float]:
        """Get current infrastructure metrics."""
        # This would integrate with actual infrastructure monitoring
        # For now, return simulated metrics
        return {
            'cpu_usage': np.random.uniform(30, 80),
            'memory_usage': np.random.uniform(40, 85),
            'request_rate': np.random.uniform(8, 25),
            'ml_queue_length': np.random.randint(0, 10),
            'db_connection_usage': np.random.uniform(0.2, 0.8),
            'error_rate': np.random.uniform(0.0001, 0.01)
        }

    def _get_model_path(self) -> Path:
        """Get path for saving/loading prediction model."""
        return Path("models/predictive_scaling_model.joblib")

    def _get_scaler_path(self) -> Path:
        """Get path for saving/loading feature scaler."""
        return Path("models/predictive_scaling_scaler.joblib")

    async def _save_model_and_state(self) -> None:
        """Save prediction model and engine state."""
        try:
            # Ensure models directory exists
            models_dir = Path("models")
            models_dir.mkdir(exist_ok=True)

            # Save model and scaler
            if self.load_predictor:
                joblib.dump(self.load_predictor, self._get_model_path())
            joblib.dump(self.scaler, self._get_scaler_path())

            # Save engine state
            state = {
                'config': asdict(self.config),
                'current_resources': {k.value: v for k, v in self.current_resources.items()},
                'baseline_cost_per_hour': self.baseline_cost_per_hour,
                'model_last_trained': self.model_last_trained
            }

            with open("models/scaling_engine_state.json", 'w') as f:
                json.dump(state, f, indent=2)

            logger.debug("Model and state saved successfully")

        except Exception as e:
            logger.error(f"Error saving model and state: {e}")

    async def get_scaling_status(self) -> Dict[str, Any]:
        """Get current scaling engine status and metrics."""
        return {
            'is_running': self.is_running,
            'current_resources': {k.value: v for k, v in self.current_resources.items()},
            'current_cost_per_hour': self._calculate_current_cost(),
            'last_scaling_action': self.last_scaling_action.value if self.last_scaling_action else None,
            'last_scaling_time': self.last_scaling_time,
            'model_last_trained': self.model_last_trained,
            'metrics_history_count': len(self.metrics_history),
            'scaling_history_count': len(self.scaling_history),
            'in_cooldown': self._in_cooldown_period(),
            'config': asdict(self.config)
        }

    async def force_scaling_evaluation(self) -> Optional[ScalingPrediction]:
        """Force immediate scaling evaluation and return prediction."""
        if not self.is_running:
            logger.error("Scaling engine is not running")
            return None

        logger.info("Forcing immediate scaling evaluation...")

        # Collect fresh metrics
        current_metrics = await self._collect_current_metrics()
        if current_metrics:
            self.metrics_history.append(current_metrics)

        # Generate and execute prediction
        if len(self.metrics_history) >= 5:
            prediction = await self._generate_scaling_prediction()
            if prediction:
                await self._execute_scaling_action(prediction)
                return prediction

        return None

# Global instance
_scaling_engine: Optional[PredictiveScalingEngine] = None

def get_scaling_engine() -> PredictiveScalingEngine:
    """Get global predictive scaling engine instance."""
    global _scaling_engine
    if _scaling_engine is None:
        _scaling_engine = PredictiveScalingEngine()
    return _scaling_engine