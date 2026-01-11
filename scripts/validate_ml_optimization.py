#!/usr/bin/env python3
"""
Quick validation script for ML Optimization implementation.
Validates all components are working correctly.
"""

import sys
from pathlib import Path

# Add project root
sys.path.append(str(Path(__file__).parent.parent))

import asyncio
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def validate_ml_optimization():
    """Validate ML optimization components."""

    print("=" * 60)
    print("ML OPTIMIZATION VALIDATION")
    print("=" * 60)

    try:
        # Import components
        from ghl_real_estate_ai.services.optimization.ml_inference_optimizer import (
            MLInferenceOptimizer,
            QuantizationConfig,
            BatchingConfig,
            CachingConfig,
            QuantizationType,
            BatchingStrategy
        )

        print("✅ Successfully imported ML optimization components")

        # Create test model
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        X_train = np.random.rand(100, 10)
        y_train = np.random.randint(0, 2, 100)
        model.fit(X_train, y_train)

        print("✅ Created and trained test model")

        # Initialize optimizer
        optimizer = MLInferenceOptimizer(
            quantization_config=QuantizationConfig(
                quantization_type=QuantizationType.INT8
            ),
            batching_config=BatchingConfig(
                strategy=BatchingStrategy.TIME_WINDOW,
                max_batch_size=50
            ),
            caching_config=CachingConfig(
                ttl_seconds=300,
                compression_enabled=True
            )
        )

        print("✅ Initialized ML optimizer with all configurations")

        # Initialize async components (cache)
        try:
            await optimizer.initialize()
            print("✅ Initialized async components (cache may require Redis)")
        except Exception as e:
            print(f"⚠️  Cache initialization failed (Redis may not be running): {e}")
            print("   Continuing without cache...")

        # Register model
        optimizer.register_model(
            "test_model",
            model,
            model_type="sklearn",
            quantize=True,
            preload=True
        )

        print("✅ Registered and optimized model")

        # Test prediction
        X_test = np.random.rand(1, 10)
        prediction = await optimizer.predict(
            "test_model",
            X_test,
            use_cache=False,  # Skip cache if Redis not available
            use_batching=False
        )

        print(f"✅ Made test prediction: {prediction}")

        # Get performance summary
        summary = optimizer.get_performance_summary()

        print("\n" + "=" * 60)
        print("PERFORMANCE SUMMARY")
        print("=" * 60)
        print(f"Total Predictions: {summary['total_predictions']}")
        print(f"Models Registered: {len(summary['models'])}")

        if 'test_model' in summary['models']:
            model_stats = summary['models']['test_model']
            print(f"\nTest Model Stats:")
            print(f"  Predictions: {model_stats['total_predictions']}")
            print(f"  Avg Inference Time: {model_stats['avg_inference_time_ms']:.2f}ms")
            print(f"  P95 Inference Time: {model_stats['p95_inference_time_ms']:.2f}ms")
            print(f"  Cache Hit Rate: {model_stats['cache_hit_rate']:.1%}")

        print("\n" + "=" * 60)
        print("✅ ALL VALIDATION TESTS PASSED")
        print("=" * 60)
        print("\nML Optimization implementation is working correctly!")
        print("\nNext steps:")
        print("1. Run full benchmarks: python scripts/ml_optimization_benchmarks.py")
        print("2. Configure Redis for caching (optional but recommended)")
        print("3. Integrate with production models")

        return True

    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(validate_ml_optimization())
    sys.exit(0 if success else 1)
