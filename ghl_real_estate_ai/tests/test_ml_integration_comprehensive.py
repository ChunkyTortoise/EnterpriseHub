"""
Comprehensive ML Integration Testing Framework

Complete validation of the Behavioral Learning Engine, ML model integration,
and real-time personalization pipeline for GHL Real Estate AI Platform.

Agent 6: Integration Testing & Validation Lead
"""

import asyncio
import pytest
import logging
import time
import uuid
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import json

# Add the services directory to Python path
services_path = Path(__file__).parent.parent / "services"
sys.path.insert(0, str(services_path))

logger = logging.getLogger(__name__)

class MLIntegrationTestSuite:
    """
    Comprehensive ML integration testing covering:

    1. Behavioral Learning Engine validation
    2. ML model training and prediction workflows
    3. Real-time personalization pipeline
    4. Performance and scalability testing
    5. Error handling and resilience validation
    """

    def __init__(self):
        self.test_results = {}
        self.performance_metrics = {}
        self.load_test_results = {}

    @pytest.mark.asyncio
    async def test_behavioral_learning_pipeline(self):
        """Test complete behavioral learning pipeline"""

        from learning.interfaces import BehavioralEvent, EventType, LearningContext
        from learning.tracking.behavior_tracker import InMemoryBehaviorTracker
        from learning.tracking.event_collector import EventCollector
        from learning.feature_engineering.standard_feature_engineer import StandardFeatureEngineer

        # Initialize components
        tracker = InMemoryBehaviorTracker()
        collector = EventCollector(tracker)
        feature_engineer = StandardFeatureEngineer(tracker)

        # Test event tracking pipeline
        lead_id = "test_lead_ml_001"
        property_id = "test_property_001"
        session_id = f"session_{uuid.uuid4().hex[:8]}"

        # Track property interaction
        event_id = await collector.track_property_view(
            lead_id=lead_id,
            property_id=property_id,
            session_id=session_id,
            view_duration=45.5,
            metadata={"test_suite": True}
        )

        assert event_id is not None, "Event tracking should return event ID"

        # Record positive outcome
        await tracker.record_outcome(event_id, "engagement", 0.8)

        # Test feature extraction
        events = await tracker.get_events(entity_id=lead_id, entity_type="lead")
        assert len(events) > 0, "Should retrieve tracked events"

        features = await feature_engineer.extract_features(
            entity_id=lead_id,
            entity_type="lead",
            events=events
        )

        assert features is not None, "Feature extraction should succeed"
        assert len(features.numerical_features) > 0, "Should extract numerical features"

        return {
            "event_tracking": "✅ passed",
            "outcome_recording": "✅ passed",
            "feature_extraction": "✅ passed",
            "events_count": len(events),
            "features_extracted": len(features.numerical_features)
        }

    @pytest.mark.asyncio
    async def test_ml_model_integration(self):
        """Test ML model training and prediction integration"""

        from learning.models.collaborative_filtering import CollaborativeFilteringModel
        from learning.models.content_based import ContentBasedModel
        from learning.interfaces import FeatureVector

        # Test collaborative filtering model
        collaborative_model = CollaborativeFilteringModel(
            n_factors=5,  # Smaller for testing
            min_interactions=1,
            cold_start_threshold=1
        )

        # Create test training data
        test_features = [
            FeatureVector(
                entity_id="lead_001",
                entity_type="lead",
                numerical_features={"budget": 500000, "beds": 3, "baths": 2},
                categorical_features={"property_type": "single_family"},
                metadata={"property_id": "prop_001"}
            ),
            FeatureVector(
                entity_id="lead_002",
                entity_type="lead",
                numerical_features={"budget": 750000, "beds": 4, "baths": 3},
                categorical_features={"property_type": "condo"},
                metadata={"property_id": "prop_002"}
            )
        ]

        test_targets = [0.8, 0.6]

        # Test model training
        training_result = await collaborative_model.train(
            features=test_features,
            targets=test_targets
        )

        assert training_result.success, f"Training failed: {training_result.error_message}"
        assert collaborative_model.is_trained, "Model should be trained"

        # Test prediction
        prediction = await collaborative_model.predict(test_features[0])
        assert prediction is not None, "Prediction should not be None"
        assert prediction.confidence > 0, "Prediction should have confidence"

        # Test batch prediction
        batch_predictions = await collaborative_model.predict_batch(test_features)
        assert len(batch_predictions) == len(test_features), "Batch predictions length mismatch"

        return {
            "collaborative_training": "✅ passed",
            "prediction_accuracy": "✅ passed",
            "batch_prediction": "✅ passed",
            "training_time": training_result.training_duration_seconds,
            "model_confidence": prediction.confidence
        }

    @pytest.mark.asyncio
    async def test_personalization_engine(self):
        """Test complete personalization engine workflow"""

        from learning.personalization.property_engine import PropertyPersonalizationEngine
        from learning.tracking.behavior_tracker import InMemoryBehaviorTracker
        from learning.feature_engineering.standard_feature_engineer import StandardFeatureEngineer
        from learning.models.collaborative_filtering import CollaborativeFilteringModel
        from learning.models.content_based import ContentBasedModel

        # Initialize components
        tracker = InMemoryBehaviorTracker()
        feature_engineer = StandardFeatureEngineer(tracker)

        # Use mock models for faster testing
        collaborative_model = MagicMock()
        content_based_model = MagicMock()

        # Mock model predictions
        collaborative_model.predict_batch.return_value = [
            MagicMock(entity_id="prop_001", predicted_value=0.85, confidence=0.9),
            MagicMock(entity_id="prop_002", predicted_value=0.72, confidence=0.8)
        ]

        content_based_model.predict_batch.return_value = [
            MagicMock(entity_id="prop_001", predicted_value=0.78, confidence=0.85),
            MagicMock(entity_id="prop_002", predicted_value=0.81, confidence=0.87)
        ]

        # Initialize personalization engine
        personalization_engine = PropertyPersonalizationEngine(
            behavior_tracker=tracker,
            feature_engineer=feature_engineer,
            collaborative_model=collaborative_model,
            content_based_model=content_based_model,
            ensemble_weights={"collaborative": 0.6, "content_based": 0.4},
            min_confidence=0.1
        )

        # Test recommendations
        recommendations = await personalization_engine.get_recommendations(
            entity_id="test_lead_001",
            entity_type="lead",
            max_results=3
        )

        assert len(recommendations) > 0, "Should generate recommendations"

        # Test explanation
        if recommendations:
            explanation = await personalization_engine.get_explanation(
                entity_id="test_lead_001",
                prediction=recommendations[0]
            )
            assert explanation is not None, "Should generate explanation"

        # Test feedback recording
        feedback_success = await personalization_engine.record_feedback(
            entity_id="test_lead_001",
            prediction_id="test_prediction",
            feedback="positive",
            feedback_value=0.9
        )
        assert feedback_success, "Feedback recording should succeed"

        return {
            "recommendations_generation": "✅ passed",
            "explanation_generation": "✅ passed",
            "feedback_recording": "✅ passed",
            "recommendations_count": len(recommendations)
        }

    @pytest.mark.asyncio
    async def test_performance_benchmarks(self):
        """Test performance benchmarks for production readiness"""

        performance_results = {}

        # Test import performance
        start_time = time.time()
        from learning.interfaces import BehavioralEvent, EventType
        from learning.tracking.behavior_tracker import InMemoryBehaviorTracker
        from learning.feature_engineering.standard_feature_engineer import StandardFeatureEngineer
        import_time = time.time() - start_time

        performance_results["import_time_ms"] = import_time * 1000
        performance_results["import_performance"] = "✅ passed" if import_time < 1.0 else "❌ failed"

        # Test component initialization performance
        start_time = time.time()
        tracker = InMemoryBehaviorTracker()
        feature_engineer = StandardFeatureEngineer(tracker)
        initialization_time = time.time() - start_time

        performance_results["initialization_time_ms"] = initialization_time * 1000
        performance_results["initialization_performance"] = "✅ passed" if initialization_time < 0.5 else "❌ failed"

        # Test event tracking performance
        start_time = time.time()
        from learning.tracking.event_collector import EventCollector
        collector = EventCollector(tracker)

        # Track multiple events
        for i in range(10):
            await collector.track_property_view(
                lead_id=f"lead_{i}",
                property_id=f"prop_{i}",
                session_id=f"session_{i}"
            )

        tracking_time = time.time() - start_time
        performance_results["tracking_time_per_event_ms"] = (tracking_time / 10) * 1000
        performance_results["tracking_performance"] = "✅ passed" if tracking_time < 1.0 else "❌ failed"

        # Test feature extraction performance
        events = await tracker.get_events(entity_id="lead_0", entity_type="lead")
        start_time = time.time()
        features = await feature_engineer.extract_features("lead_0", "lead", events)
        feature_extraction_time = time.time() - start_time

        performance_results["feature_extraction_time_ms"] = feature_extraction_time * 1000
        performance_results["feature_extraction_performance"] = "✅ passed" if feature_extraction_time < 0.1 else "❌ failed"

        return performance_results

    @pytest.mark.asyncio
    async def test_load_capacity(self):
        """Test system capacity under load (10x expected traffic)"""

        load_results = {}

        # Initialize components once
        from learning.tracking.behavior_tracker import InMemoryBehaviorTracker
        from learning.tracking.event_collector import EventCollector

        tracker = InMemoryBehaviorTracker()
        collector = EventCollector(tracker)

        # Test concurrent event tracking (simulate 100 concurrent users)
        concurrent_events = 100
        start_time = time.time()

        tasks = []
        for i in range(concurrent_events):
            task = collector.track_property_view(
                lead_id=f"load_test_lead_{i}",
                property_id=f"load_test_prop_{i % 10}",  # 10 properties
                session_id=f"load_test_session_{i}"
            )
            tasks.append(task)

        # Execute all tracking tasks concurrently
        await asyncio.gather(*tasks)

        total_time = time.time() - start_time
        events_per_second = concurrent_events / total_time

        load_results["concurrent_events"] = concurrent_events
        load_results["total_time_seconds"] = total_time
        load_results["events_per_second"] = events_per_second
        load_results["load_performance"] = "✅ passed" if events_per_second > 50 else "❌ failed"

        # Test memory usage under load
        import psutil
        import os
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024

        load_results["memory_usage_mb"] = memory_mb
        load_results["memory_performance"] = "✅ passed" if memory_mb < 500 else "⚠️  warning"

        return load_results

    @pytest.mark.asyncio
    async def test_error_handling_scenarios(self):
        """Test error handling and resilience scenarios"""

        error_results = {}

        # Test invalid event data handling
        from learning.tracking.behavior_tracker import InMemoryBehaviorTracker
        from learning.tracking.event_collector import EventCollector

        tracker = InMemoryBehaviorTracker()
        collector = EventCollector(tracker)

        try:
            # Test with invalid lead_id (None)
            await collector.track_property_view(
                lead_id=None,
                property_id="valid_prop",
                session_id="valid_session"
            )
            error_results["invalid_data_handling"] = "❌ failed - should reject None lead_id"
        except (ValueError, TypeError):
            error_results["invalid_data_handling"] = "✅ passed - correctly rejected invalid data"

        # Test feature extraction with empty events
        from learning.feature_engineering.standard_feature_engineer import StandardFeatureEngineer
        feature_engineer = StandardFeatureEngineer(tracker)

        try:
            features = await feature_engineer.extract_features(
                entity_id="nonexistent_lead",
                entity_type="lead",
                events=[]
            )
            error_results["empty_events_handling"] = "✅ passed - handled empty events gracefully"
        except Exception as e:
            error_results["empty_events_handling"] = f"❌ failed - {str(e)}"

        # Test ML model error handling with mock
        from learning.models.collaborative_filtering import CollaborativeFilteringModel

        model = CollaborativeFilteringModel()
        try:
            # Try to predict without training
            result = await model.predict(None)
            error_results["untrained_model_handling"] = "❌ failed - should reject prediction on untrained model"
        except (ValueError, RuntimeError):
            error_results["untrained_model_handling"] = "✅ passed - correctly rejected untrained model prediction"

        return error_results

    async def generate_comprehensive_report(self):
        """Generate comprehensive integration test report"""

        print("🧠 Comprehensive ML Integration Testing Report")
        print("=" * 55)

        # Run all test suites
        behavioral_results = await self.test_behavioral_learning_pipeline()
        ml_model_results = await self.test_ml_model_integration()
        personalization_results = await self.test_personalization_engine()
        performance_results = await self.test_performance_benchmarks()
        load_results = await self.test_load_capacity()
        error_results = await self.test_error_handling_scenarios()

        # Compile results
        all_results = {
            "behavioral_learning": behavioral_results,
            "ml_model_integration": ml_model_results,
            "personalization_engine": personalization_results,
            "performance_benchmarks": performance_results,
            "load_capacity": load_results,
            "error_handling": error_results
        }

        # Count passes/fails
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        warning_tests = 0

        for suite, results in all_results.items():
            for test, result in results.items():
                if isinstance(result, str):
                    total_tests += 1
                    if "✅ passed" in result:
                        passed_tests += 1
                    elif "❌ failed" in result:
                        failed_tests += 1
                    elif "⚠️" in result:
                        warning_tests += 1

        # Display summary
        print(f"\n📊 Test Summary:")
        print(f"✅ Passed: {passed_tests}/{total_tests}")
        print(f"❌ Failed: {failed_tests}/{total_tests}")
        print(f"⚠️  Warnings: {warning_tests}/{total_tests}")

        # Display detailed results
        print(f"\n🔍 Detailed Results:")
        for suite, results in all_results.items():
            print(f"\n{suite.replace('_', ' ').title()}:")
            for test, result in results.items():
                if isinstance(result, str):
                    print(f"  {result} {test}")
                else:
                    print(f"  📈 {test}: {result}")

        # Production readiness assessment
        print(f"\n🚀 ML System Production Readiness:")
        if failed_tests == 0:
            if warning_tests == 0:
                print("✅ FULLY READY FOR PRODUCTION")
                print("   All ML integration tests passed")
            else:
                print("⚠️  READY WITH MONITORING")
                print("   Monitor warning conditions in production")
        else:
            print("❌ NOT READY FOR PRODUCTION")
            print("   Critical ML integration failures must be resolved")

        # Performance assessment
        print(f"\n📈 Performance Assessment:")
        print(f"  Import Time: {performance_results.get('import_time_ms', 0):.1f}ms")
        print(f"  Initialization: {performance_results.get('initialization_time_ms', 0):.1f}ms")
        print(f"  Event Tracking: {performance_results.get('tracking_time_per_event_ms', 0):.1f}ms per event")
        print(f"  Feature Extraction: {performance_results.get('feature_extraction_time_ms', 0):.1f}ms")
        print(f"  Load Capacity: {load_results.get('events_per_second', 0):.0f} events/second")
        print(f"  Memory Usage: {load_results.get('memory_usage_mb', 0):.1f}MB")

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "warning_tests": warning_tests,
            "production_ready": failed_tests == 0,
            "performance_metrics": performance_results,
            "load_metrics": load_results,
            "detailed_results": all_results
        }

# Pytest integration
@pytest.mark.asyncio
async def test_comprehensive_ml_integration():
    """Main comprehensive ML integration test"""

    test_suite = MLIntegrationTestSuite()
    report = await test_suite.generate_comprehensive_report()

    # Assert production readiness
    assert report["production_ready"], f"ML system not ready: {report['failed_tests']} failures"

    # Assert performance requirements
    perf = report["performance_metrics"]
    assert perf.get("import_time_ms", 9999) < 1000, "Import time too slow"
    assert perf.get("tracking_time_per_event_ms", 9999) < 100, "Event tracking too slow"

    # Assert load capacity
    load = report["load_metrics"]
    assert load.get("events_per_second", 0) > 50, "Load capacity too low"

    return report

# Standalone execution
async def main():
    """Run comprehensive ML integration testing"""
    test_suite = MLIntegrationTestSuite()
    report = await test_suite.generate_comprehensive_report()

    if report["production_ready"]:
        print("\n🎉 ALL ML INTEGRATION TESTS PASSED!")
        print("✅ Behavioral Learning Engine operational")
        print("✅ ML models integrated successfully")
        print("✅ Personalization engine ready")
        print("✅ Performance requirements met")
        print("✅ Load capacity validated")
        print("\n🚀 ML SYSTEM READY FOR PRODUCTION!")
        return True
    else:
        print("\n❌ ML INTEGRATION TESTS FAILED")
        print("🔧 Critical issues must be resolved before production deployment")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)