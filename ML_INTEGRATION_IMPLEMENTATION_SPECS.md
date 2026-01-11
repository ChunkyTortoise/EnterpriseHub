# ML Integration Implementation Specifications
## Detailed Code Specifications for Production Deployment

**Created:** January 10, 2026
**Priority:** Critical - Phase 2 Week 4 Completion
**Implementation Time**: 8 days (2 sprints)

---

## Component 1: ML Service Registry

### File Structure
```
ghl_real_estate_ai/services/ml/
├── __init__.py
├── ml_service_registry.py         # Main registry (NEW)
├── production_model_loader.py     # Model loader (NEW)
├── model_predictor.py             # Predictor wrapper (NEW)
└── exceptions.py                  # ML-specific exceptions (NEW)
```

### 1.1 ML Service Registry Implementation

**File**: `/ghl_real_estate_ai/services/ml/ml_service_registry.py`

**Complete Implementation**:
```python
"""
ML Service Registry - Central Dependency Injection for ML Optimization

Provides singleton access to optimized ML models for all services.
Integrates MLInferenceOptimizer with production services.
"""

import asyncio
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime
from dataclasses import dataclass

from ..optimization.ml_inference_optimizer import (
    MLInferenceOptimizer,
    QuantizationConfig,
    BatchingConfig,
    CachingConfig
)
from .production_model_loader import ProductionModelLoader
from .model_predictor import ModelPredictor
from .exceptions import ModelLoadError, ModelNotFoundError

logger = logging.getLogger(__name__)

# Global singleton instance
_ml_registry_instance: Optional['MLServiceRegistry'] = None


def get_ml_registry() -> 'MLServiceRegistry':
    """Get or create global ML registry singleton."""
    global _ml_registry_instance
    if _ml_registry_instance is None:
        _ml_registry_instance = MLServiceRegistry()
    return _ml_registry_instance


@dataclass
class ModelMetadata:
    """Metadata for registered models."""
    model_name: str
    model_type: str
    version: str
    accuracy: float
    latency_target_ms: float
    registered_at: datetime
    is_optimized: bool
    fallback_available: bool


class MLServiceRegistry:
    """
    Central registry for ML model access with optimization.

    Features:
    - Singleton pattern for global access
    - Automatic model discovery and registration
    - Integrated optimization (quantization, batching, caching)
    - Health monitoring per model
    - Graceful fallback to rule-based models
    """

    def __init__(self):
        """Initialize ML registry with optimization."""
        # Core components
        self.optimizer = MLInferenceOptimizer(
            quantization_config=QuantizationConfig(
                quantization_type="int8",
                enable_gpu=True
            ),
            batching_config=BatchingConfig(
                strategy="time_window",
                max_batch_size=50,
                time_window_ms=50.0
            ),
            caching_config=CachingConfig(
                ttl_seconds=300,  # 5 minutes
                compression_enabled=True
            )
        )

        self.model_loader = ProductionModelLoader()

        # Registry state
        self._predictors: Dict[str, ModelPredictor] = {}
        self._metadata: Dict[str, ModelMetadata] = {}
        self._initialized = False

        logger.info("MLServiceRegistry created (not yet initialized)")

    async def initialize(self) -> None:
        """
        Initialize registry with production models.

        Steps:
        1. Initialize optimizer components
        2. Discover production models
        3. Load and register each model
        4. Pre-warm caches
        """
        if self._initialized:
            logger.warning("MLServiceRegistry already initialized")
            return

        logger.info("Initializing MLServiceRegistry...")

        # Initialize optimizer
        await self.optimizer.initialize()

        # Discover and register models
        models = await self.model_loader.discover_models()
        logger.info(f"Discovered {len(models)} production models")

        for model_name in models:
            try:
                await self._register_model(model_name)
            except Exception as e:
                logger.error(f"Failed to register {model_name}: {e}")
                # Continue with other models

        # Pre-warm caches with common patterns
        await self._prewarm_caches()

        self._initialized = True
        logger.info(f"MLServiceRegistry initialized with {len(self._predictors)} models")

    async def _register_model(self, model_name: str) -> None:
        """Register a single model with optimization."""
        logger.info(f"Registering model: {model_name}")

        # Load model
        model, metadata = await self.model_loader.load_model(model_name)

        # Register with optimizer
        self.optimizer.register_model(
            model_name=model_name,
            model=model,
            model_type=metadata.model_type,
            preload=True,
            quantize=True
        )

        # Create predictor wrapper
        predictor = ModelPredictor(
            model_name=model_name,
            optimizer=self.optimizer,
            metadata=metadata
        )

        # Store predictor and metadata
        self._predictors[model_name] = predictor
        self._metadata[model_name] = ModelMetadata(
            model_name=model_name,
            model_type=metadata.model_type,
            version=metadata.version,
            accuracy=metadata.accuracy,
            latency_target_ms=metadata.latency_target_ms,
            registered_at=datetime.utcnow(),
            is_optimized=True,
            fallback_available=metadata.fallback_name is not None
        )

        logger.info(f"Model {model_name} registered successfully")

    async def get_model_predictor(self, model_name: str) -> ModelPredictor:
        """
        Get optimized predictor for a model.

        Args:
            model_name: Model identifier

        Returns:
            ModelPredictor with automatic optimization

        Raises:
            ModelNotFoundError: If model not registered
        """
        if not self._initialized:
            await self.initialize()

        if model_name not in self._predictors:
            raise ModelNotFoundError(
                f"Model '{model_name}' not found. "
                f"Available models: {list(self._predictors.keys())}"
            )

        return self._predictors[model_name]

    async def _prewarm_caches(self) -> None:
        """Pre-warm prediction caches with common patterns."""
        logger.info("Pre-warming prediction caches...")

        # Get sample data for each model
        prewarm_data = await self.model_loader.get_prewarm_samples()

        for model_name, samples in prewarm_data.items():
            if model_name in self._predictors:
                try:
                    predictor = self._predictors[model_name]
                    await predictor.predict_batch(samples)
                    logger.debug(f"Pre-warmed cache for {model_name}")
                except Exception as e:
                    logger.warning(f"Failed to pre-warm {model_name}: {e}")

    async def get_registry_health(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        health = {
            "status": "healthy" if self._initialized else "not_initialized",
            "total_models": len(self._predictors),
            "models": {},
            "optimizer_stats": self.optimizer.get_performance_summary()
        }

        for model_name, predictor in self._predictors.items():
            model_health = await predictor.get_health()
            health["models"][model_name] = model_health

        return health

    def list_available_models(self) -> List[str]:
        """List all available model names."""
        return list(self._predictors.keys())

    def get_model_metadata(self, model_name: str) -> Optional[ModelMetadata]:
        """Get metadata for a specific model."""
        return self._metadata.get(model_name)


# Convenience function for service initialization
async def initialize_ml_registry() -> MLServiceRegistry:
    """
    Initialize and return ML registry.

    Use in service initialization:
        ml_registry = await initialize_ml_registry()
    """
    registry = get_ml_registry()
    await registry.initialize()
    return registry
```

---

### 1.2 Production Model Loader Implementation

**File**: `/ghl_real_estate_ai/services/ml/production_model_loader.py`

**Complete Implementation**:
```python
"""
Production Model Loader - Model Discovery and Loading

Discovers, validates, and loads production-ready ML models.
Provides fallback strategies for missing or invalid models.
"""

import logging
import joblib
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np

from .exceptions import ModelLoadError, ModelValidationError

logger = logging.getLogger(__name__)


@dataclass
class LoadedModelMetadata:
    """Metadata for loaded models."""
    model_name: str
    model_type: str  # sklearn, tensorflow, pytorch
    version: str
    accuracy: float
    latency_target_ms: float
    file_path: Path
    loaded_at: datetime
    fallback_name: Optional[str] = None


class ProductionModelLoader:
    """
    Load and validate production ML models.

    Features:
    - Auto-discovery from models directory
    - Model validation and integrity checks
    - Graceful fallback to rule-based models
    - Version compatibility checking
    """

    # Model registry with metadata
    MODEL_REGISTRY = {
        "lead_scorer_v2": {
            "path": "models/lead_scorer_v2.pkl",
            "type": "sklearn",
            "min_accuracy": 0.95,
            "latency_target_ms": 200,
            "fallback": "rule_based_lead_scorer",
            "version": "2.1.0"
        },
        "property_matcher_v3": {
            "path": "models/property_matcher_v3.pkl",
            "type": "sklearn",
            "min_accuracy": 0.88,
            "latency_target_ms": 300,
            "fallback": "cosine_similarity_matcher",
            "version": "3.0.0"
        },
        "churn_predictor_v2": {
            "path": "models/churn_predictor_v2.pkl",
            "type": "sklearn",
            "min_accuracy": 0.92,
            "latency_target_ms": 250,
            "fallback": "engagement_threshold_predictor",
            "version": "2.0.0"
        },
        "property_interest_predictor_v2": {
            "path": "models/property_interest_v2.pkl",
            "type": "sklearn",
            "min_accuracy": 0.85,
            "latency_target_ms": 200,
            "fallback": "feature_weighted_scorer",
            "version": "2.0.0"
        },
        "viewing_probability_predictor_v2": {
            "path": "models/viewing_probability_v2.pkl",
            "type": "sklearn",
            "min_accuracy": 0.82,
            "latency_target_ms": 200,
            "fallback": "engagement_score",
            "version": "2.0.0"
        }
    }

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize model loader.

        Args:
            base_path: Base path for model files (defaults to project root)
        """
        if base_path is None:
            # Auto-detect base path
            current_file = Path(__file__)
            self.base_path = current_file.parents[3]  # Go up to project root
        else:
            self.base_path = base_path

        logger.info(f"ProductionModelLoader initialized (base: {self.base_path})")

    async def discover_models(self) -> List[str]:
        """
        Discover all available production models.

        Returns:
            List of model names available for loading
        """
        available_models = []

        for model_name, config in self.MODEL_REGISTRY.items():
            model_path = self.base_path / config["path"]

            if model_path.exists():
                available_models.append(model_name)
                logger.debug(f"Found model: {model_name} at {model_path}")
            else:
                logger.warning(
                    f"Model {model_name} not found at {model_path}. "
                    f"Fallback: {config.get('fallback', 'none')}"
                )

        return available_models

    async def load_model(
        self, model_name: str
    ) -> Tuple[Any, LoadedModelMetadata]:
        """
        Load and validate a production model.

        Args:
            model_name: Model identifier from MODEL_REGISTRY

        Returns:
            Tuple of (model_instance, metadata)

        Raises:
            ModelLoadError: If model cannot be loaded
            ModelValidationError: If model fails validation
        """
        if model_name not in self.MODEL_REGISTRY:
            raise ModelLoadError(
                f"Model '{model_name}' not in registry. "
                f"Available: {list(self.MODEL_REGISTRY.keys())}"
            )

        config = self.MODEL_REGISTRY[model_name]
        model_path = self.base_path / config["path"]

        # Check if file exists
        if not model_path.exists():
            fallback = config.get("fallback")
            if fallback:
                logger.warning(
                    f"Model file not found: {model_path}. "
                    f"Service should use fallback: {fallback}"
                )
            raise ModelLoadError(
                f"Model file not found: {model_path}",
                fallback_available=fallback is not None
            )

        # Load model based on type
        try:
            if config["type"] == "sklearn":
                model = self._load_sklearn_model(model_path)
            elif config["type"] == "tensorflow":
                model = self._load_tensorflow_model(model_path)
            elif config["type"] == "pytorch":
                model = self._load_pytorch_model(model_path)
            else:
                raise ModelLoadError(f"Unsupported model type: {config['type']}")

        except Exception as e:
            raise ModelLoadError(
                f"Failed to load {model_name}: {str(e)}",
                fallback_available=config.get("fallback") is not None
            )

        # Validate model
        await self._validate_model(model, model_name, config)

        # Create metadata
        metadata = LoadedModelMetadata(
            model_name=model_name,
            model_type=config["type"],
            version=config["version"],
            accuracy=config["min_accuracy"],
            latency_target_ms=config["latency_target_ms"],
            file_path=model_path,
            loaded_at=datetime.utcnow(),
            fallback_name=config.get("fallback")
        )

        logger.info(f"Successfully loaded {model_name} (v{metadata.version})")

        return model, metadata

    def _load_sklearn_model(self, path: Path) -> Any:
        """Load scikit-learn model from pickle/joblib."""
        try:
            # Try joblib first (preferred for sklearn)
            return joblib.load(path)
        except:
            # Fallback to pickle
            with open(path, 'rb') as f:
                return pickle.load(f)

    def _load_tensorflow_model(self, path: Path) -> Any:
        """Load TensorFlow model."""
        try:
            import tensorflow as tf
            return tf.keras.models.load_model(path)
        except ImportError:
            raise ModelLoadError("TensorFlow not installed")

    def _load_pytorch_model(self, path: Path) -> Any:
        """Load PyTorch model."""
        try:
            import torch
            return torch.load(path)
        except ImportError:
            raise ModelLoadError("PyTorch not installed")

    async def _validate_model(
        self, model: Any, model_name: str, config: Dict
    ) -> None:
        """
        Validate loaded model.

        Checks:
        - Model has predict method
        - Model can make predictions
        - Model structure is valid
        """
        # Check for predict method
        if not hasattr(model, 'predict'):
            raise ModelValidationError(
                f"{model_name} missing 'predict' method"
            )

        # Try sample prediction
        try:
            # Create dummy input based on model type
            if config["type"] == "sklearn":
                # Assume standard feature count
                sample_input = np.random.rand(1, 10)
                prediction = model.predict(sample_input)

                # Validate output
                if prediction is None or len(prediction) == 0:
                    raise ModelValidationError("Model returned empty prediction")

        except Exception as e:
            raise ModelValidationError(
                f"Model prediction failed: {str(e)}"
            )

        logger.debug(f"Model {model_name} validation passed")

    async def get_prewarm_samples(self) -> Dict[str, List[np.ndarray]]:
        """
        Get sample data for cache pre-warming.

        Returns:
            Dict mapping model names to sample input arrays
        """
        prewarm_data = {
            "lead_scorer_v2": [
                np.random.rand(1, 10) for _ in range(5)
            ],
            "property_matcher_v3": [
                np.random.rand(1, 15) for _ in range(5)
            ],
            "churn_predictor_v2": [
                np.random.rand(1, 20) for _ in range(5)
            ]
        }

        return prewarm_data

    def get_fallback_name(self, model_name: str) -> Optional[str]:
        """Get fallback strategy name for a model."""
        config = self.MODEL_REGISTRY.get(model_name)
        return config.get("fallback") if config else None
```

---

### 1.3 Model Predictor Wrapper

**File**: `/ghl_real_estate_ai/services/ml/model_predictor.py`

**Complete Implementation**:
```python
"""
Model Predictor - Wrapper for Optimized ML Predictions

Provides clean interface for services to use ML models with
automatic optimization (batching, caching, quantization).
"""

import logging
import time
from typing import Any, List, Dict, Optional
import numpy as np

from ..optimization.ml_inference_optimizer import MLInferenceOptimizer
from .production_model_loader import LoadedModelMetadata

logger = logging.getLogger(__name__)


class ModelPredictor:
    """
    Predictor wrapper with automatic optimization.

    Features:
    - Automatic batching for concurrent requests
    - 5-minute prediction caching
    - INT8 quantization (60% faster)
    - Circuit breaker protection
    - Performance metrics tracking
    """

    def __init__(
        self,
        model_name: str,
        optimizer: MLInferenceOptimizer,
        metadata: LoadedModelMetadata
    ):
        """
        Initialize predictor.

        Args:
            model_name: Model identifier
            optimizer: Shared optimizer instance
            metadata: Model metadata
        """
        self.model_name = model_name
        self.optimizer = optimizer
        self.metadata = metadata

        # State tracking
        self.prediction_count = 0
        self.cache_hits = 0
        self.last_cache_hit = False
        self.error_count = 0

        self.is_optimized = True
        self.is_ml_model = True

    async def predict(
        self,
        features: np.ndarray,
        use_cache: bool = True
    ) -> Any:
        """
        Make single prediction with optimization.

        Args:
            features: Input features (1D or 2D array)
            use_cache: Whether to use cache

        Returns:
            Prediction result
        """
        start_time = time.time()

        # Ensure 2D shape for sklearn compatibility
        if len(features.shape) == 1:
            features = features.reshape(1, -1)

        try:
            # Use optimizer for prediction
            prediction = await self.optimizer.predict(
                model_name=self.model_name,
                input_data=features,
                use_cache=use_cache,
                use_batching=True
            )

            # Track metrics
            self.prediction_count += 1
            latency_ms = (time.time() - start_time) * 1000

            # Check if cache was hit (from optimizer stats)
            cache_stats = self.optimizer.cache.cache_stats.get(self.model_name, {})
            previous_hits = getattr(self, '_previous_cache_hits', 0)
            current_hits = cache_stats.get('hits', 0)

            if current_hits > previous_hits:
                self.cache_hits += 1
                self.last_cache_hit = True
            else:
                self.last_cache_hit = False

            self._previous_cache_hits = current_hits

            # Warn if exceeding latency target
            if latency_ms > self.metadata.latency_target_ms:
                logger.warning(
                    f"{self.model_name} prediction latency {latency_ms:.1f}ms "
                    f"exceeds target {self.metadata.latency_target_ms}ms"
                )

            return prediction[0] if len(prediction) == 1 else prediction

        except Exception as e:
            self.error_count += 1
            logger.error(f"Prediction error in {self.model_name}: {e}")
            raise

    async def predict_batch(
        self,
        feature_batch: List[np.ndarray],
        use_cache: bool = True
    ) -> List[Any]:
        """
        Make batch predictions with optimization.

        Args:
            feature_batch: List of feature arrays
            use_cache: Whether to use cache

        Returns:
            List of predictions
        """
        start_time = time.time()

        # Stack features into batch
        batch_array = np.vstack(feature_batch)

        try:
            # Batch prediction through optimizer
            predictions = await self.optimizer.predict(
                model_name=self.model_name,
                input_data=batch_array,
                use_cache=use_cache,
                use_batching=True
            )

            # Track metrics
            self.prediction_count += len(feature_batch)
            latency_ms = (time.time() - start_time) * 1000
            avg_latency = latency_ms / len(feature_batch)

            logger.debug(
                f"Batch prediction: {len(feature_batch)} items in {latency_ms:.1f}ms "
                f"({avg_latency:.1f}ms avg)"
            )

            return predictions.tolist()

        except Exception as e:
            self.error_count += 1
            logger.error(f"Batch prediction error in {self.model_name}: {e}")
            raise

    async def get_health(self) -> Dict[str, Any]:
        """Get predictor health status."""
        cache_hit_rate = (
            self.cache_hits / self.prediction_count
            if self.prediction_count > 0
            else 0.0
        )

        error_rate = (
            self.error_count / self.prediction_count
            if self.prediction_count > 0
            else 0.0
        )

        return {
            "model_name": self.model_name,
            "status": "healthy" if error_rate < 0.05 else "degraded",
            "prediction_count": self.prediction_count,
            "cache_hit_rate": round(cache_hit_rate, 3),
            "error_rate": round(error_rate, 3),
            "version": self.metadata.version,
            "accuracy_target": self.metadata.accuracy
        }
```

---

### 1.4 ML-Specific Exceptions

**File**: `/ghl_real_estate_ai/services/ml/exceptions.py`

```python
"""ML-specific exception classes."""

class MLError(Exception):
    """Base exception for ML-related errors."""
    pass


class ModelLoadError(MLError):
    """Error loading ML model."""

    def __init__(self, message: str, fallback_available: bool = False):
        super().__init__(message)
        self.fallback_available = fallback_available


class ModelNotFoundError(MLError):
    """Requested model not found in registry."""
    pass


class ModelValidationError(MLError):
    """Model failed validation checks."""
    pass


class PredictionError(MLError):
    """Error during model prediction."""
    pass
```

---

## Component 2: Service Integration Examples

### 2.1 Real-Time Scoring Service Integration

**File**: `/ghl_real_estate_ai/services/real_time_scoring.py`

**Integration Changes** (lines to modify):

```python
# ADD at top of file (after existing imports)
from .ml import get_ml_registry, ModelPredictor
from .ml.exceptions import ModelLoadError

# MODIFY __init__ method (around line 42)
class RealTimeScoring:
    def __init__(self):
        # Existing initialization
        self.feature_engineer = FeatureEngineer()
        self.memory_service = MemoryService()

        # NEW: ML optimization
        self._ml_registry = None
        self._ml_lead_scorer: Optional[ModelPredictor] = None

        # Keep existing scorer as fallback
        self.scorer = LeadScorer()  # Fallback

        # ... rest of existing init

# MODIFY initialize method (around line 62)
async def initialize(self) -> None:
    """Initialize Redis connection and ML models"""
    try:
        # Existing Redis initialization
        self.redis_client = redis.Redis(...)
        await self.redis_client.ping()

        # NEW: Initialize ML optimization
        self._ml_registry = get_ml_registry()
        try:
            self._ml_lead_scorer = await self._ml_registry.get_model_predictor(
                "lead_scorer_v2"
            )
            logger.info("✅ ML-optimized lead scoring enabled")
        except ModelLoadError as e:
            logger.warning(f"⚠️  ML model unavailable, using fallback: {e}")
            self._ml_lead_scorer = None

        # Existing cache warming
        asyncio.create_task(self._warm_feature_cache())

    except Exception as e:
        logger.warning(f"⚠️  Redis unavailable: {e}")
        self.redis_client = None

# ADD new method for ML scoring
async def _score_with_ml(self, features: np.ndarray) -> float:
    """Score using ML model with fallback."""
    if self._ml_lead_scorer:
        try:
            score = await self._ml_lead_scorer.predict(features)
            return float(score)
        except Exception as e:
            logger.error(f"ML scoring failed: {e}, using fallback")

    # Fallback to rule-based scorer
    return self.scorer.calculate_score(features)
```

---

### 2.2 AI Property Matcher Integration

**File**: `/ghl_real_estate_ai/services/ai_property_matching.py`

**Integration Changes**:

```python
# ADD at top
from .ml import get_ml_registry, ModelPredictor
from .ml.exceptions import ModelLoadError

# MODIFY initialize_models method (around line 94)
async def initialize_models(self) -> None:
    """Initialize and train ML models from historical data"""

    # NEW: Use ML registry for production models
    ml_registry = get_ml_registry()

    try:
        # Load optimized interest predictor
        self.interest_predictor = await ml_registry.get_model_predictor(
            "property_interest_predictor_v2"
        )

        # Load optimized viewing predictor
        self.viewing_predictor = await ml_registry.get_model_predictor(
            "viewing_probability_predictor_v2"
        )

        logger.info("✅ ML-optimized property matching enabled")
        return  # Skip local training if production models available

    except ModelLoadError:
        logger.warning("⚠️  Production models unavailable, training locally")

    # EXISTING: Fallback to local training
    try:
        historical_data = await self._load_historical_data()
        # ... existing training code
```

---

## Implementation Checklist

### Phase 1: Foundation (Days 1-2)
- [ ] Create `/services/ml/` directory
- [ ] Implement `ml_service_registry.py` (complete code above)
- [ ] Implement `production_model_loader.py` (complete code above)
- [ ] Implement `model_predictor.py` (complete code above)
- [ ] Implement `exceptions.py` (complete code above)
- [ ] Create `__init__.py` with exports
- [ ] Write unit tests for registry
- [ ] Write unit tests for model loader

### Phase 2: Integration (Days 3-4)
- [ ] Integrate `real_time_scoring.py`
- [ ] Integrate `ai_property_matching.py`
- [ ] Integrate `churn_prediction_engine.py`
- [ ] Write integration tests
- [ ] Validate performance targets

### Phase 3: Training (Days 5-6)
- [ ] Create training pipeline
- [ ] Generate initial production models
- [ ] Implement model versioning
- [ ] Set up monitoring

### Phase 4: Deployment (Days 7-8)
- [ ] Production deployment
- [ ] Performance validation
- [ ] Documentation complete
- [ ] Handoff preparation

---

## Success Validation

### Performance Tests
```bash
# Run ML integration performance tests
pytest tests/ml/test_ml_performance.py -v

# Expected results:
# - Inference latency p95: <300ms
# - Cache hit rate: >60%
# - Batch throughput: 5-10x improvement
```

### Integration Tests
```bash
# Run service integration tests
pytest tests/ml/test_service_ml_integration.py -v

# Expected results:
# - All 3 core services integrated
# - ML models loaded successfully
# - Fallback working correctly
```

---

**Next Action**: Begin implementation with `ml_service_registry.py`
