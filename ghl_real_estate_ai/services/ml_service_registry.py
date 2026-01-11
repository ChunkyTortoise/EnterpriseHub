"""
ML Service Registry - GREEN Phase Implementation
=================================================

Central registry for ML-optimized services with coordination and monitoring.
This is the MINIMAL implementation to make tests pass (GREEN phase).

Features:
- Service registration with optimization configuration
- Optimized predictor factory
- Health monitoring and performance tracking
- Integration with MLInferenceOptimizer

Integration Pattern (2-line addition to services):
```python
# In ChurnPredictionService.__init__:
from services.ml_service_registry import get_ml_registry
self.ml_registry = get_ml_registry()

# In prediction method:
prediction = await self.ml_registry.predict("churn_model", features)
```

Author: TDD ML Integration Specialist Agent
Date: 2026-01-10
Phase: GREEN - Minimal implementation to pass tests
"""

import asyncio
import time
import uuid
import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from collections import defaultdict

from ghl_real_estate_ai.services.optimization.ml_inference_optimizer import (
    MLInferenceOptimizer,
    QuantizationConfig,
    BatchingConfig,
    CachingConfig
)

logger = logging.getLogger(__name__)


class MLServiceType(str, Enum):
    """ML service types"""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    RANKING = "ranking"


class OptimizationLevel(str, Enum):
    """Optimization aggressiveness levels"""
    NONE = "none"              # No optimization
    CONSERVATIVE = "conservative"  # Minimal optimization, max accuracy
    BALANCED = "balanced"      # Balance speed and accuracy
    AGGRESSIVE = "aggressive"  # Maximum speed optimization


@dataclass
class MLServiceConfig:
    """Configuration for ML service registration"""
    service_name: str
    service_type: MLServiceType
    model_name: str
    optimization_level: OptimizationLevel = OptimizationLevel.BALANCED
    enable_quantization: bool = True
    enable_batching: bool = True
    enable_caching: bool = True
    model_type: str = "sklearn"  # sklearn, tensorflow, pytorch
    target_inference_ms: float = 200.0
    accuracy_threshold: float = 0.92


@dataclass
class ServiceHealth:
    """Service health status"""
    status: str  # healthy, degraded, unhealthy
    total_predictions: int
    avg_inference_time_ms: float
    p95_inference_time_ms: float
    error_rate: float
    cache_hit_rate: float
    last_updated: datetime


class MLServiceRegistry:
    """
    Central registry for ML-optimized services.

    Provides:
    - Service registration with optimization
    - Optimized predictor functions
    - Health monitoring
    - Performance tracking
    """

    def __init__(self, ml_optimizer: Optional[MLInferenceOptimizer] = None):
        """
        Initialize ML Service Registry.

        Args:
            ml_optimizer: MLInferenceOptimizer instance (created if None)
        """
        self.ml_optimizer = ml_optimizer
        self.registered_services: Dict[str, MLServiceConfig] = {}
        self.service_health: Dict[str, ServiceHealth] = {}
        self.is_initialized = False

        # Performance tracking
        self.prediction_times: Dict[str, List[float]] = defaultdict(list)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.total_predictions: Dict[str, int] = defaultdict(int)

    async def initialize(self):
        """Initialize registry and ML optimizer"""
        if self.ml_optimizer is None:
            # Create default optimizer
            self.ml_optimizer = MLInferenceOptimizer(
                quantization_config=QuantizationConfig(),
                batching_config=BatchingConfig(),
                caching_config=CachingConfig()
            )

        await self.ml_optimizer.initialize()
        self.is_initialized = True
        logger.info("ML Service Registry initialized")

    async def register_service(self, config: MLServiceConfig) -> str:
        """
        Register an ML service with optimization configuration.

        Args:
            config: Service configuration

        Returns:
            Service ID for future reference
        """
        service_id = f"{config.service_name}_{uuid.uuid4().hex[:8]}"

        # Store configuration
        self.registered_services[service_id] = config

        # Initialize health tracking
        self.service_health[service_id] = ServiceHealth(
            status="healthy",
            total_predictions=0,
            avg_inference_time_ms=0.0,
            p95_inference_time_ms=0.0,
            error_rate=0.0,
            cache_hit_rate=0.0,
            last_updated=datetime.now()
        )

        logger.info(f"Registered ML service: {config.service_name} (ID: {service_id})")
        return service_id

    def get_service_config(self, service_id: str) -> Optional[MLServiceConfig]:
        """
        Get service configuration.

        Args:
            service_id: Service identifier

        Returns:
            Service configuration or None
        """
        return self.registered_services.get(service_id)

    def get_optimized_predictor(self, service_id: str) -> Optional[Callable]:
        """
        Get optimized predictor function for a service.

        Args:
            service_id: Service identifier

        Returns:
            Async prediction function
        """
        config = self.registered_services.get(service_id)
        if not config:
            logger.error(f"Service {service_id} not found")
            return None

        # Create async predictor function
        async def optimized_predictor(features: np.ndarray) -> Any:
            """
            Optimized prediction function with monitoring.

            Args:
                features: Input feature array

            Returns:
                Prediction result
            """
            start_time = time.time()

            try:
                # Use ML optimizer for prediction
                prediction = await self.ml_optimizer.predict(
                    model_name=config.model_name,
                    input_data=features,
                    use_cache=config.enable_caching,
                    use_batching=config.enable_batching
                )

                # Track performance
                inference_time_ms = (time.time() - start_time) * 1000
                self._track_prediction(service_id, inference_time_ms, success=True)

                return prediction

            except Exception as e:
                inference_time_ms = (time.time() - start_time) * 1000
                self._track_prediction(service_id, inference_time_ms, success=False)
                logger.error(f"Prediction failed for {service_id}: {e}")
                raise

        return optimized_predictor

    async def get_service_health(self, service_id: str) -> Dict[str, Any]:
        """
        Get health status for a service.

        Args:
            service_id: Service identifier

        Returns:
            Health status dictionary
        """
        if service_id not in self.service_health:
            return {
                'status': 'unknown',
                'total_predictions': 0,
                'avg_inference_time_ms': 0.0,
                'error_rate': 0.0
            }

        health = self.service_health[service_id]

        # Update with latest metrics
        prediction_times = self.prediction_times[service_id]
        total_preds = self.total_predictions[service_id]
        errors = self.error_counts[service_id]

        if prediction_times:
            avg_time = np.mean(prediction_times[-1000:])  # Last 1000
            p95_time = np.percentile(prediction_times[-1000:], 95)
        else:
            avg_time = 0.0
            p95_time = 0.0

        error_rate = errors / total_preds if total_preds > 0 else 0.0

        # Determine health status
        config = self.registered_services[service_id]
        if error_rate > 0.05 or avg_time > config.target_inference_ms * 2:
            status = "unhealthy"
        elif error_rate > 0.01 or avg_time > config.target_inference_ms * 1.5:
            status = "degraded"
        else:
            status = "healthy"

        return {
            'status': status,
            'total_predictions': total_preds,
            'avg_inference_time_ms': round(avg_time, 2),
            'p95_inference_time_ms': round(p95_time, 2),
            'error_rate': round(error_rate, 4),
            'cache_hit_rate': self._get_cache_hit_rate(service_id)
        }

    def _track_prediction(self, service_id: str, inference_time_ms: float, success: bool):
        """Track prediction performance"""
        self.total_predictions[service_id] += 1
        self.prediction_times[service_id].append(inference_time_ms)

        if not success:
            self.error_counts[service_id] += 1

        # Keep only recent history
        if len(self.prediction_times[service_id]) > 10000:
            self.prediction_times[service_id] = self.prediction_times[service_id][-5000:]

    def _get_cache_hit_rate(self, service_id: str) -> float:
        """Calculate cache hit rate"""
        # Get from ML optimizer cache stats
        if self.ml_optimizer:
            cache_stats = self.ml_optimizer.cache.get_cache_stats()
            config = self.registered_services.get(service_id)
            if config and config.model_name in cache_stats:
                return cache_stats[config.model_name].get('hit_rate', 0.0)
        return 0.0

    def get_all_services(self) -> Dict[str, MLServiceConfig]:
        """Get all registered services"""
        return self.registered_services.copy()

    async def shutdown(self):
        """Shutdown registry and cleanup resources"""
        logger.info("Shutting down ML Service Registry")
        self.is_initialized = False


# ============================================================================
# Global Registry Singleton
# ============================================================================

_ml_registry: Optional[MLServiceRegistry] = None


async def get_ml_registry() -> MLServiceRegistry:
    """
    Get or create global ML Service Registry singleton.

    Returns:
        MLServiceRegistry instance
    """
    global _ml_registry

    if _ml_registry is None:
        _ml_registry = MLServiceRegistry()
        await _ml_registry.initialize()

    return _ml_registry


def get_ml_registry_sync() -> MLServiceRegistry:
    """
    Get ML Service Registry (synchronous version).
    Creates uninitialized registry - must call initialize() async.

    Returns:
        MLServiceRegistry instance (uninitialized)
    """
    global _ml_registry

    if _ml_registry is None:
        _ml_registry = MLServiceRegistry()

    return _ml_registry
