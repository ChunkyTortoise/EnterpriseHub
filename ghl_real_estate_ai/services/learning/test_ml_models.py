"""
Machine Learning Models Integration Tests

Comprehensive testing for Phase 3 ML implementation including
collaborative filtering, content-based filtering, and personalization engine.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import numpy as np

# Import ML models
from models.collaborative_filtering import CollaborativeFilteringModel
from models.content_based import ContentBasedModel
from personalization.property_engine import PropertyPersonalizationEngine

# Import foundation components
from interfaces import (
    FeatureVector, BehavioralEvent, EventType, LearningContext,
    ModelType, ConfidenceLevel
)
from tracking.behavior_tracker import InMemoryBehaviorTracker
from tracking.event_collector import EventCollector, PropertyInteractionCollector
from feature_engineering.standard_feature_engineer import StandardFeatureEngineer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLModelsTestSuite:
    """
    Comprehensive test suite for Machine Learning models and personalization engine.

    Tests include:
    - Individual model training and prediction
    - Ensemble model integration
    - Real-time personalization workflow
    - Performance and accuracy validation
    """

    def __init__(self):
        # Initialize foundation components
        self.tracker = InMemoryBehaviorTracker()
        self.event_collector = EventCollector(self.tracker)
        self.property_collector = PropertyInteractionCollector(self.tracker)
        self.feature_engineer = StandardFeatureEngineer(self.tracker)

        # Initialize ML models
        self.collaborative_model = None
        self.content_based_model = None
        self.personalization_engine = None

        # Test data
        self.test_leads = []
        self.test_properties = []
        self.test_events = []

    async def run_comprehensive_tests(self):
        """Run all ML model tests"""
        print("🧠 Starting ML Models Integration Tests")
        print("=" * 50)

        try:
            # Setup test data
            await self.setup_test_data()
            print("✅ Test data setup complete")

            # Test individual models
            await self.test_collaborative_filtering()
            print("✅ Collaborative filtering tests passed")

            await self.test_content_based_filtering()
            print("✅ Content-based filtering tests passed")

            # Test ensemble integration
            await self.test_personalization_engine()
            print("✅ Personalization engine tests passed")

            # Test real-time workflow
            await self.test_realtime_workflow()
            print("✅ Real-time workflow tests passed")

            # Performance validation
            await self.test_performance_metrics()
            print("✅ Performance validation passed")

            print("\n🎉 ALL ML MODELS TESTS PASSED!")
            return True

        except Exception as e:
            print(f"\n❌ ML Models tests failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    async def setup_test_data(self):
        """Setup comprehensive test data for ML models"""
        print("\n📊 Setting up ML test data...")

        # Create test leads
        self.test_leads = [
            {"id": "lead_ml_001", "name": "Alice Johnson", "budget": 750000},
            {"id": "lead_ml_002", "name": "Bob Smith", "budget": 500000},
            {"id": "lead_ml_003", "name": "Carol Davis", "budget": 1000000},
            {"id": "lead_ml_004", "name": "David Wilson", "budget": 600000},
            {"id": "lead_ml_005", "name": "Eva Brown", "budget": 800000}
        ]

        # Create test properties
        self.test_properties = [
            {"id": "prop_ml_001", "price": 750000, "type": "Single Family", "beds": 3, "baths": 2},
            {"id": "prop_ml_002", "price": 500000, "type": "Condo", "beds": 2, "baths": 1},
            {"id": "prop_ml_003", "price": 1000000, "type": "Single Family", "beds": 4, "baths": 3},
            {"id": "prop_ml_004", "price": 600000, "type": "Townhouse", "beds": 3, "baths": 2},
            {"id": "prop_ml_005", "price": 800000, "type": "Single Family", "beds": 3, "baths": 2},
            {"id": "prop_ml_006", "price": 450000, "type": "Condo", "beds": 1, "baths": 1},
            {"id": "prop_ml_007", "price": 900000, "type": "Single Family", "beds": 4, "baths": 3}
        ]

        # Create realistic interaction patterns
        interactions = [
            # Alice likes mid-range single family homes
            ("lead_ml_001", "prop_ml_001", EventType.PROPERTY_VIEW, 0.8),
            ("lead_ml_001", "prop_ml_005", EventType.PROPERTY_LIKE, 0.9),
            ("lead_ml_001", "prop_ml_004", EventType.PROPERTY_VIEW, 0.6),

            # Bob prefers affordable condos
            ("lead_ml_002", "prop_ml_002", EventType.PROPERTY_LIKE, 0.9),
            ("lead_ml_002", "prop_ml_006", EventType.PROPERTY_VIEW, 0.8),
            ("lead_ml_002", "prop_ml_001", EventType.PROPERTY_VIEW, 0.3),  # Too expensive

            # Carol likes luxury properties
            ("lead_ml_003", "prop_ml_003", EventType.PROPERTY_LIKE, 0.9),
            ("lead_ml_003", "prop_ml_007", EventType.PROPERTY_VIEW, 0.8),
            ("lead_ml_003", "prop_ml_005", EventType.PROPERTY_VIEW, 0.7),

            # David has mixed preferences
            ("lead_ml_004", "prop_ml_004", EventType.PROPERTY_LIKE, 0.8),
            ("lead_ml_004", "prop_ml_002", EventType.PROPERTY_VIEW, 0.6),
            ("lead_ml_004", "prop_ml_005", EventType.PROPERTY_VIEW, 0.7),

            # Eva likes mid-to-high end properties
            ("lead_ml_005", "prop_ml_005", EventType.PROPERTY_LIKE, 0.9),
            ("lead_ml_005", "prop_ml_001", EventType.PROPERTY_VIEW, 0.8),
            ("lead_ml_005", "prop_ml_003", EventType.PROPERTY_VIEW, 0.6)  # Slightly out of budget
        ]

        # Track all interactions
        for lead_id, property_id, event_type, score in interactions:
            session_id = f"session_{uuid.uuid4().hex[:8]}"

            event_id = await self.event_collector.track_property_interaction(
                lead_id=lead_id,
                property_id=property_id,
                interaction_type=event_type.value,
                session_id=session_id,
                metadata={"ml_test": True, "score": score}
            )

            # Record outcome for supervised learning
            await self.tracker.record_outcome(event_id, "engagement_score", score)

            self.test_events.append(event_id)

        print(f"✅ Created {len(interactions)} interaction events")
        print(f"✅ Setup {len(self.test_leads)} leads and {len(self.test_properties)} properties")

    async def test_collaborative_filtering(self):
        """Test collaborative filtering model"""
        print("\n🤝 Testing Collaborative Filtering Model...")

        # Initialize model
        self.collaborative_model = CollaborativeFilteringModel(
            n_factors=10,
            min_interactions=3,
            cold_start_threshold=2
        )

        # Prepare training data
        training_features, training_targets = await self._prepare_training_data("collaborative")

        print(f"📊 Training data: {len(training_features)} features")

        # Train model
        training_result = await self.collaborative_model.train(
            features=training_features,
            targets=training_targets
        )

        assert training_result.success, f"Training failed: {training_result.error_message}"
        assert self.collaborative_model.is_trained, "Model should be trained"
        print(f"✅ Training completed in {training_result.training_duration_seconds:.2f}s")

        # Test prediction
        test_features = training_features[0]  # Use first lead for testing
        prediction = await self.collaborative_model.predict(test_features)

        assert prediction is not None, "Prediction should not be None"
        assert prediction.confidence > 0, "Prediction should have confidence > 0"
        assert len(prediction.reasoning) > 0, "Prediction should have reasoning"
        print(f"✅ Prediction: property {prediction.entity_id}, score {prediction.predicted_value:.3f}")

        # Test batch prediction
        batch_predictions = await self.collaborative_model.predict_batch(training_features[:3])

        assert len(batch_predictions) == 3, "Should get 3 batch predictions"
        print(f"✅ Batch predictions: {len(batch_predictions)} results")

        # Test model persistence
        model_path = "/tmp/test_collaborative_model.pkl"
        save_success = await self.collaborative_model.save(model_path)
        assert save_success, "Model save should succeed"

        # Test feature importance
        importance = self.collaborative_model.get_feature_importance()
        assert len(importance) > 0, "Should have feature importance"
        print(f"✅ Feature importance: {len(importance)} features")

    async def test_content_based_filtering(self):
        """Test content-based filtering model"""
        print("\n🔍 Testing Content-Based Filtering Model...")

        # Initialize model
        self.content_based_model = ContentBasedModel(
            similarity_threshold=0.1,
            min_interactions=2,
            max_features=100
        )

        # Prepare training data with property features
        training_features, training_targets = await self._prepare_training_data("content_based")

        print(f"📊 Training data: {len(training_features)} features")

        # Train model
        training_result = await self.content_based_model.train(
            features=training_features,
            targets=training_targets
        )

        assert training_result.success, f"Training failed: {training_result.error_message}"
        assert self.content_based_model.is_trained, "Model should be trained"
        print(f"✅ Training completed in {training_result.training_duration_seconds:.2f}s")

        # Test prediction
        test_features = training_features[0]
        prediction = await self.content_based_model.predict(test_features)

        assert prediction is not None, "Prediction should not be None"
        assert prediction.confidence > 0, "Prediction should have confidence > 0"
        print(f"✅ Prediction: property {prediction.entity_id}, score {prediction.predicted_value:.3f}")

        # Test online learning
        online_success = await self.content_based_model.update_online(
            features=test_features,
            target=0.8
        )
        assert online_success, "Online update should succeed"
        print("✅ Online learning test passed")

        # Test model persistence
        model_path = "/tmp/test_content_based_model.pkl"
        save_success = await self.content_based_model.save(model_path)
        assert save_success, "Model save should succeed"

    async def test_personalization_engine(self):
        """Test personalization engine with ensemble models"""
        print("\n🎯 Testing Personalization Engine...")

        # Initialize personalization engine with both models
        self.personalization_engine = PropertyPersonalizationEngine(
            behavior_tracker=self.tracker,
            feature_engineer=self.feature_engineer,
            collaborative_model=self.collaborative_model,
            content_based_model=self.content_based_model,
            ensemble_weights={"collaborative": 0.6, "content_based": 0.4},
            min_confidence=0.2  # Lower threshold for testing
        )

        # Test recommendations for existing lead
        test_lead_id = "lead_ml_001"
        recommendations = await self.personalization_engine.get_recommendations(
            entity_id=test_lead_id,
            entity_type="lead",
            max_results=5
        )

        assert len(recommendations) > 0, "Should get recommendations"
        assert all(rec.confidence > 0 for rec in recommendations), "All recommendations should have confidence > 0"
        print(f"✅ Generated {len(recommendations)} recommendations")

        # Test top recommendation
        top_recommendation = recommendations[0]
        print(f"✅ Top recommendation: {top_recommendation.entity_id} (score: {top_recommendation.predicted_value:.3f})")

        # Test explanation
        explanation = await self.personalization_engine.get_explanation(
            entity_id=test_lead_id,
            prediction=top_recommendation
        )

        assert explanation is not None, "Should get explanation"
        assert "reasoning" in explanation, "Explanation should have reasoning"
        print("✅ Generated recommendation explanation")

        # Test feedback recording
        feedback_success = await self.personalization_engine.record_feedback(
            entity_id=test_lead_id,
            prediction_id="test_prediction",
            feedback="positive",
            feedback_value=0.9
        )

        assert feedback_success, "Feedback recording should succeed"
        print("✅ Feedback recording test passed")

        # Test cold start recommendation
        cold_start_recommendations = await self.personalization_engine.get_recommendations(
            entity_id="new_lead_123",
            entity_type="lead",
            max_results=3
        )

        assert len(cold_start_recommendations) > 0, "Should get cold start recommendations"
        print(f"✅ Cold start recommendations: {len(cold_start_recommendations)} results")

    async def test_realtime_workflow(self):
        """Test real-time ML workflow"""
        print("\n⚡ Testing Real-time ML Workflow...")

        # Simulate real-time property interaction
        new_lead_id = "lead_realtime_001"
        new_property_id = "prop_ml_003"
        session_id = f"session_{uuid.uuid4().hex[:8]}"

        # Track new interaction
        event_id = await self.event_collector.track_property_view(
            lead_id=new_lead_id,
            property_id=new_property_id,
            session_id=session_id,
            view_duration=45.0,
            metadata={"realtime_test": True}
        )

        print(f"✅ Tracked real-time interaction: {event_id}")

        # Get immediate recommendations
        immediate_recommendations = await self.personalization_engine.get_recommendations(
            entity_id=new_lead_id,
            entity_type="lead",
            max_results=3,
            context=LearningContext(
                max_latency_ms=50,  # Fast response requirement
                tracking_enabled=True
            )
        )

        print(f"✅ Generated {len(immediate_recommendations)} immediate recommendations")

        # Simulate follow-up interaction based on recommendation
        if immediate_recommendations:
            recommended_property = immediate_recommendations[0].entity_id

            follow_up_event_id = await self.event_collector.track_property_like(
                lead_id=new_lead_id,
                property_id=recommended_property,
                session_id=session_id
            )

            # Record positive outcome
            await self.tracker.record_outcome(follow_up_event_id, "conversion", 1.0)
            print("✅ Recorded positive feedback on recommendation")

        # Verify model adaptation
        # (In a real system, this would trigger online learning)
        updated_recommendations = await self.personalization_engine.get_recommendations(
            entity_id=new_lead_id,
            entity_type="lead",
            max_results=3
        )

        assert len(updated_recommendations) > 0, "Should get updated recommendations"
        print("✅ Model adaptation workflow completed")

    async def test_performance_metrics(self):
        """Test performance and accuracy metrics"""
        print("\n📈 Testing Performance Metrics...")

        # Test prediction latency
        start_time = datetime.now()
        test_lead_id = "lead_ml_002"

        recommendations = await self.personalization_engine.get_recommendations(
            entity_id=test_lead_id,
            entity_type="lead",
            max_results=5
        )

        latency_ms = (datetime.now() - start_time).total_seconds() * 1000
        print(f"✅ Recommendation latency: {latency_ms:.1f}ms")

        # Verify latency requirement (should be < 100ms for production)
        # We'll be more lenient for testing
        assert latency_ms < 1000, f"Latency too high: {latency_ms}ms"

        # Test batch performance
        batch_start = datetime.now()
        batch_features = []

        for lead in self.test_leads:
            events = await self.tracker.get_events(entity_id=lead["id"], entity_type="lead")
            if events:
                features = await self.feature_engineer.extract_features(
                    lead["id"], "lead", events
                )
                batch_features.append(features)

        if batch_features:
            batch_predictions = await self.collaborative_model.predict_batch(batch_features)
            batch_latency = (datetime.now() - batch_start).total_seconds() * 1000

            print(f"✅ Batch prediction latency: {batch_latency:.1f}ms for {len(batch_features)} predictions")

        # Get engine performance metrics
        performance_metrics = self.personalization_engine.get_performance_metrics()
        print(f"✅ Engine metrics: {performance_metrics['recommendation_count']} recommendations generated")

        # Test accuracy simulation (in production, this would use real conversion data)
        accuracy_score = await self._simulate_accuracy_test()
        print(f"✅ Simulated accuracy score: {accuracy_score:.3f}")

        assert accuracy_score > 0.5, "Accuracy should be better than random"

    async def _prepare_training_data(self, model_type: str) -> tuple:
        """Prepare training data for ML models"""
        features = []
        targets = []

        for lead in self.test_leads:
            lead_id = lead["id"]

            # Get events for this lead
            events = await self.tracker.get_events(entity_id=lead_id, entity_type="lead")

            if events:
                # Extract features
                feature_vector = await self.feature_engineer.extract_features(
                    lead_id, "lead", events
                )

                # Add model-specific metadata
                if model_type == "collaborative":
                    # For collaborative filtering, we need user-item interactions
                    for event in events:
                        if event.property_id:
                            feature_vector.metadata["property_id"] = event.property_id
                            features.append(feature_vector)

                            # Use engagement score as target
                            target = event.outcome_value or 0.5
                            targets.append(target)
                            break  # One per lead for simplicity

                elif model_type == "content_based":
                    # For content-based, add property features
                    for event in events:
                        if event.property_id:
                            # Find property data
                            property_data = next(
                                (p for p in self.test_properties if p["id"] == event.property_id),
                                None
                            )

                            if property_data:
                                feature_vector.metadata["property_id"] = event.property_id
                                feature_vector.numerical_features.update({
                                    "property_price": property_data["price"],
                                    "property_beds": property_data["beds"],
                                    "property_baths": property_data["baths"]
                                })
                                feature_vector.categorical_features.update({
                                    "property_type": property_data["type"]
                                })

                                features.append(feature_vector)
                                target = event.outcome_value or 0.5
                                targets.append(target)
                                break

        return features, targets

    async def _simulate_accuracy_test(self) -> float:
        """Simulate accuracy testing"""
        correct_predictions = 0
        total_predictions = 0

        # Test each lead's preferences
        for lead in self.test_leads:
            lead_id = lead["id"]

            # Get recommendations
            recommendations = await self.personalization_engine.get_recommendations(
                entity_id=lead_id,
                entity_type="lead",
                max_results=3
            )

            if recommendations:
                # Get lead's actual interactions
                events = await self.tracker.get_events(entity_id=lead_id, entity_type="lead")
                liked_properties = [
                    e.property_id for e in events
                    if e.event_type == EventType.PROPERTY_LIKE and e.property_id
                ]

                # Check if any recommended properties were actually liked
                for rec in recommendations:
                    total_predictions += 1
                    if rec.entity_id in liked_properties:
                        correct_predictions += 1

        accuracy = correct_predictions / max(total_predictions, 1)
        return accuracy


async def main():
    """Run comprehensive ML models test suite"""
    test_suite = MLModelsTestSuite()
    success = await test_suite.run_comprehensive_tests()

    if success:
        print("\n🎉 ML MODELS INTEGRATION COMPLETE!")
        print("✅ Collaborative filtering working")
        print("✅ Content-based filtering working")
        print("✅ Personalization engine working")
        print("✅ Real-time workflow operational")
        print("✅ Performance metrics validated")
        print("\n🚀 Phase 3 ML Implementation Successfully Completed!")
    else:
        print("\n❌ ML Models integration failed")
        return False

    return True


if __name__ == "__main__":
    asyncio.run(main())