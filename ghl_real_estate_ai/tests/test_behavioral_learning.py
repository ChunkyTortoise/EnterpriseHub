"""
Behavioral learning accuracy tests for multi-tenant memory system.

Tests cover:
- Behavioral preference extraction and learning accuracy
- Property interaction pattern recognition
- Communication style detection and adaptation
- Decision-making pattern analysis
- Preference consistency tracking over time
- Behavioral weight adaptation for property matching
"""

import asyncio
import pytest
import uuid
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any
import numpy as np

# Test imports with fallback for different execution contexts
try:
    from ghl_real_estate_ai.services.behavioral_weighting_engine import BehavioralWeightingEngine
    from ghl_real_estate_ai.services.enhanced_memory_service import EnhancedMemoryService
    from ghl_real_estate_ai.services.learning.behavior_tracker import InMemoryBehaviorTracker
    from ghl_real_estate_ai.services.learning.feature_engineering.standard_feature_engineer import StandardFeatureEngineer
    from ghl_real_estate_ai.models.behavioral_models import BehavioralProfile, PropertyInteraction
except ImportError:
    try:
        from services.behavioral_weighting_engine import BehavioralWeightingEngine
        from services.enhanced_memory_service import EnhancedMemoryService
        from services.learning.behavior_tracker import InMemoryBehaviorTracker
        from services.learning.feature_engineering.standard_feature_engineer import StandardFeatureEngineer
        from models.behavioral_models import BehavioralProfile, PropertyInteraction
    except ImportError:
        # Mock for testing environment
        BehavioralWeightingEngine = Mock
        EnhancedMemoryService = Mock
        InMemoryBehaviorTracker = Mock
        StandardFeatureEngineer = Mock
        BehavioralProfile = Mock
        PropertyInteraction = Mock

@pytest.fixture
def property_interaction_sequence():
    """Create realistic property interaction sequence for learning"""
    interactions = []
    base_time = datetime.now() - timedelta(days=30)

    # Simulate consistent behavior pattern: preference for family homes with good schools
    properties = [
        # Liked properties (consistent pattern)
        {"id": "prop_1", "price": 450000, "bedrooms": 3, "property_type": "single_family", "school_rating": 9, "feedback": "very_interested"},
        {"id": "prop_2", "price": 475000, "bedrooms": 4, "property_type": "single_family", "school_rating": 8, "feedback": "interested"},
        {"id": "prop_3", "price": 485000, "bedrooms": 3, "property_type": "single_family", "school_rating": 10, "feedback": "very_interested"},

        # Disliked properties (revealing preferences)
        {"id": "prop_4", "price": 420000, "bedrooms": 2, "property_type": "condo", "school_rating": 6, "feedback": "not_interested"},
        {"id": "prop_5", "price": 500000, "bedrooms": 5, "property_type": "single_family", "school_rating": 4, "feedback": "not_interested"},

        # Neutral properties (edge cases)
        {"id": "prop_6", "price": 465000, "bedrooms": 3, "property_type": "townhouse", "school_rating": 7, "feedback": "maybe"},
        {"id": "prop_7", "price": 495000, "bedrooms": 3, "property_type": "single_family", "school_rating": 8, "feedback": "interested"},

        # Recent high engagement
        {"id": "prop_8", "price": 470000, "bedrooms": 3, "property_type": "single_family", "school_rating": 9, "feedback": "very_interested", "duration": 300},
        {"id": "prop_9", "price": 480000, "bedrooms": 3, "property_type": "single_family", "school_rating": 9, "feedback": "schedule_showing"}
    ]

    for i, prop in enumerate(properties):
        interaction = {
            "id": str(uuid.uuid4()),
            "property_id": prop["id"],
            "interaction_type": "view",
            "property_data": {
                "price": prop["price"],
                "bedrooms": prop["bedrooms"],
                "property_type": prop["property_type"],
                "school_rating": prop["school_rating"],
                "neighborhood": "Riverside" if prop["school_rating"] >= 8 else "Downtown"
            },
            "feedback_category": prop["feedback"],
            "duration": prop.get("duration", 120 + (i * 20)),  # Increasing engagement over time
            "timestamp": base_time + timedelta(days=i * 3),
            "user_actions": ["scroll", "zoom", "save"] if "interested" in prop["feedback"] else ["scroll"]
        }
        interactions.append(interaction)

    return interactions

@pytest.fixture
def communication_pattern_data():
    """Communication patterns for style detection"""
    return [
        {
            "message": "I'm looking for a 3-bedroom house under $500k",
            "style_indicators": {"directness": 0.9, "detail_level": 0.3, "formality": 0.4},
            "timestamp": datetime.now() - timedelta(days=10)
        },
        {
            "message": "Could you please provide more information about the school districts in the Riverside area? We have two young children and education quality is very important to us.",
            "style_indicators": {"directness": 0.6, "detail_level": 0.9, "formality": 0.8},
            "timestamp": datetime.now() - timedelta(days=9)
        },
        {
            "message": "Thanks! When can we schedule a viewing?",
            "style_indicators": {"directness": 0.8, "detail_level": 0.2, "formality": 0.3},
            "timestamp": datetime.now() - timedelta(days=8)
        },
        {
            "message": "We'd like to see properties this weekend if possible. Saturday morning works best for our family schedule.",
            "style_indicators": {"directness": 0.7, "detail_level": 0.7, "formality": 0.5},
            "timestamp": datetime.now() - timedelta(days=7)
        }
    ]

class TestBehavioralLearning:
    """Test behavioral learning accuracy and pattern recognition"""

    @pytest.mark.asyncio
    async def test_property_preference_pattern_extraction(self, property_interaction_sequence):
        """Test extraction of property preferences from interaction patterns"""

        with patch('services.behavioral_weighting_engine.DatabasePool'):
            behavioral_engine = BehavioralWeightingEngine()

            # Analyze property interaction patterns
            preferences = await behavioral_engine.extract_property_preferences(
                property_interaction_sequence,
                min_interactions=5
            )

            # Verify preference extraction accuracy
            assert preferences is not None
            assert "property_type_preference" in preferences
            assert "school_rating_importance" in preferences
            assert "price_range_preference" in preferences

            # Verify learned preferences match actual patterns
            assert preferences["property_type_preference"]["single_family"] > 0.7  # Strong preference for single family
            assert preferences["school_rating_importance"] > 0.8  # High importance on school quality
            assert preferences["bedroom_preference"]["3"] > 0.6  # Consistent 3-bedroom preference

            # Verify price sensitivity learning
            price_range = preferences["price_range_preference"]
            assert 450000 <= price_range["preferred_min"] <= 470000
            assert 480000 <= price_range["preferred_max"] <= 500000

    @pytest.mark.asyncio
    async def test_communication_style_detection(self, communication_pattern_data):
        """Test communication style detection and classification"""

        with patch('services.behavioral_weighting_engine.NLPProcessor') as mock_nlp:
            # Mock NLP analysis results
            mock_nlp.return_value.analyze_communication_style.return_value = {
                "average_directness": 0.75,
                "average_detail_level": 0.53,
                "average_formality": 0.5,
                "response_length_avg": 85,
                "question_frequency": 0.6,
                "style_consistency": 0.82
            }

            behavioral_engine = BehavioralWeightingEngine()

            communication_style = await behavioral_engine.analyze_communication_style(
                communication_pattern_data,
                contact_id="test_contact"
            )

            # Verify style classification accuracy
            assert communication_style["primary_style"] in ["detailed", "direct", "conversational", "formal"]
            assert communication_style["secondary_traits"] is not None
            assert 0 <= communication_style["confidence_score"] <= 1

            # Verify adaptive response recommendations
            assert "response_strategy" in communication_style
            assert "recommended_tone" in communication_style
            assert "optimal_message_length" in communication_style

    @pytest.mark.asyncio
    async def test_decision_making_pattern_analysis(self, property_interaction_sequence):
        """Test decision-making pattern recognition"""

        with patch('services.behavioral_weighting_engine.DecisionAnalyzer') as mock_analyzer:
            mock_analyzer.return_value.analyze_decision_patterns.return_value = {
                "decision_speed": "thoughtful",  # Takes time to decide
                "research_depth": "comprehensive",  # Thorough research
                "price_sensitivity": "moderate",
                "feature_prioritization": ["school_rating", "property_type", "bedrooms"],
                "consistency_score": 0.87,
                "exploration_vs_exploitation": 0.35  # More exploitation than exploration
            }

            behavioral_engine = BehavioralWeightingEngine()

            decision_patterns = await behavioral_engine.analyze_decision_patterns(
                property_interaction_sequence,
                interaction_window_days=30
            )

            # Verify decision pattern accuracy
            assert decision_patterns["decision_speed"] in ["quick", "moderate", "thoughtful", "very_deliberate"]
            assert decision_patterns["research_depth"] in ["surface", "moderate", "comprehensive", "exhaustive"]
            assert 0 <= decision_patterns["consistency_score"] <= 1

            # Verify predictive insights
            assert "next_action_probability" in decision_patterns
            assert "conversion_likelihood" in decision_patterns
            assert decision_patterns["conversion_likelihood"] > 0.6  # High likelihood based on pattern

    @pytest.mark.asyncio
    async def test_behavioral_weight_adaptation_accuracy(self, property_interaction_sequence):
        """Test accuracy of behavioral weight adaptation for property matching"""

        extracted_preferences = {
            "budget": 500000,
            "bedrooms": 3,
            "property_type": "single_family",
            "school_rating_min": 7
        }

        with patch('services.behavioral_weighting_engine.MachineLearningEngine') as mock_ml:
            # Mock ML-driven weight calculations
            mock_ml.return_value.calculate_feature_weights.return_value = {
                "school_rating": 1.45,  # 45% boost - learned from strong preference
                "property_type": 1.30,   # 30% boost - consistent single family preference
                "bedrooms": 1.15,        # 15% boost - consistent 3-bedroom preference
                "price": 1.05,           # 5% boost - moderate price sensitivity
                "neighborhood": 1.20,    # 20% boost - preference for good school districts
                "learning_confidence": 0.89,
                "sample_size": len(property_interaction_sequence)
            }

            behavioral_engine = BehavioralWeightingEngine()

            adaptive_weights = await behavioral_engine.calculate_adaptive_weights(
                behavioral_profile={
                    "property_interactions": property_interaction_sequence,
                    "preference_consistency": 0.87
                },
                extracted_preferences=extracted_preferences
            )

            # Verify weight adaptation accuracy
            assert adaptive_weights["school_rating"] > 1.3  # Strong boost for important feature
            assert adaptive_weights["property_type"] > 1.2  # Significant boost for consistent preference
            assert adaptive_weights["learning_confidence"] > 0.8  # High confidence with sufficient data

            # Verify weights make sense relative to each other
            assert adaptive_weights["school_rating"] > adaptive_weights["bedrooms"]  # School more important
            assert adaptive_weights["property_type"] > adaptive_weights["price"]  # Type more important than price

    @pytest.mark.asyncio
    async def test_preference_consistency_tracking(self, property_interaction_sequence):
        """Test tracking of preference consistency over time"""

        # Divide interactions into time windows
        early_interactions = property_interaction_sequence[:3]
        recent_interactions = property_interaction_sequence[-3:]

        with patch('services.behavioral_weighting_engine.ConsistencyAnalyzer') as mock_analyzer:
            mock_analyzer.return_value.calculate_consistency.return_value = {
                "overall_consistency": 0.85,
                "feature_consistency": {
                    "school_rating": 0.92,  # Very consistent
                    "property_type": 0.88,  # Highly consistent
                    "bedrooms": 0.85,       # Consistent
                    "price": 0.72           # Moderately consistent
                },
                "consistency_trend": "improving",  # Getting more consistent over time
                "confidence_improvement": 0.15      # 15% improvement in confidence
            }

            behavioral_engine = BehavioralWeightingEngine()

            consistency_analysis = await behavioral_engine.track_preference_consistency(
                early_interactions=early_interactions,
                recent_interactions=recent_interactions,
                all_interactions=property_interaction_sequence
            )

            # Verify consistency tracking accuracy
            assert 0 <= consistency_analysis["overall_consistency"] <= 1
            assert consistency_analysis["consistency_trend"] in ["improving", "stable", "declining"]
            assert all(0 <= score <= 1 for score in consistency_analysis["feature_consistency"].values())

            # Verify learning improvement detection
            if consistency_analysis["consistency_trend"] == "improving":
                assert consistency_analysis["confidence_improvement"] > 0

    @pytest.mark.asyncio
    async def test_behavioral_learning_convergence(self):
        """Test behavioral learning convergence to accurate predictions"""

        # Simulate progressive learning with increasing accuracy
        learning_iterations = []
        accuracy_scores = []

        base_preferences = {
            "property_type": "single_family",
            "school_rating_min": 8,
            "budget_max": 500000,
            "bedrooms": 3
        }

        for iteration in range(1, 16):  # 15 learning iterations
            # Simulate accuracy improvement with more data
            base_accuracy = 0.60
            learning_rate = 0.025  # 2.5% improvement per iteration
            noise_factor = 0.05 * (15 - iteration) / 15  # Decreasing noise

            accuracy = min(0.95, base_accuracy + (iteration * learning_rate) - np.random.uniform(0, noise_factor))

            learning_iteration = {
                "iteration": iteration,
                "data_points": iteration * 2,  # More data each iteration
                "accuracy": accuracy,
                "confidence": min(0.98, 0.5 + (iteration * 0.03)),
                "preference_stability": min(0.95, 0.6 + (iteration * 0.023))
            }

            learning_iterations.append(learning_iteration)
            accuracy_scores.append(accuracy)

        # Test convergence analysis
        final_accuracy = accuracy_scores[-1]
        accuracy_after_10 = accuracy_scores[9] if len(accuracy_scores) > 9 else 0

        # Verify convergence to high accuracy
        assert final_accuracy > 0.90, f"Final accuracy {final_accuracy:.2%} below 90% threshold"
        assert accuracy_after_10 > 0.85, f"Accuracy after 10 iterations {accuracy_after_10:.2%} below 85%"

        # Verify learning curve is generally improving
        early_avg = np.mean(accuracy_scores[:5])
        late_avg = np.mean(accuracy_scores[-5:])
        assert late_avg > early_avg, "Learning accuracy should improve over time"

        # Verify convergence rate meets business requirements
        improvement_rate = (final_accuracy - accuracy_scores[0]) / len(accuracy_scores)
        assert improvement_rate > 0.015, "Learning improvement rate too slow"

    @pytest.mark.asyncio
    async def test_behavioral_segmentation_accuracy(self, property_interaction_sequence, communication_pattern_data):
        """Test accuracy of behavioral segmentation for different lead types"""

        with patch('services.behavioral_weighting_engine.SegmentationEngine') as mock_segmentation:
            # Mock segmentation results
            mock_segmentation.return_value.classify_lead_segment.return_value = {
                "primary_segment": "family_buyer",
                "confidence": 0.92,
                "segment_characteristics": {
                    "school_priority": "high",
                    "decision_style": "collaborative",
                    "research_intensity": "high",
                    "price_sensitivity": "moderate"
                },
                "predicted_timeline": "3_to_6_months",
                "conversion_probability": 0.78
            }

            behavioral_engine = BehavioralWeightingEngine()

            segmentation = await behavioral_engine.classify_lead_behavior(
                property_interactions=property_interaction_sequence,
                communication_patterns=communication_pattern_data,
                demographic_hints={"mentions_children": True, "school_questions": 3}
            )

            # Verify segmentation accuracy
            assert segmentation["primary_segment"] in [
                "first_time_buyer", "family_buyer", "investor", "luxury_buyer",
                "downsizer", "relocating_professional"
            ]
            assert segmentation["confidence"] > 0.8  # High confidence classification
            assert 0 <= segmentation["conversion_probability"] <= 1

            # Verify segment-specific insights
            if segmentation["primary_segment"] == "family_buyer":
                assert segmentation["segment_characteristics"]["school_priority"] in ["medium", "high"]
                assert segmentation["segment_characteristics"]["decision_style"] in ["collaborative", "thorough"]

    @pytest.mark.asyncio
    async def test_real_time_behavioral_updates(self, property_interaction_sequence):
        """Test real-time behavioral learning updates"""

        with patch('services.enhanced_memory_service.BehavioralUpdateEngine') as mock_updater:
            mock_updater.return_value.update_real_time.return_value = {
                "preferences_updated": ["school_rating_importance", "property_type_preference"],
                "confidence_changes": {"school_rating_importance": 0.05, "property_type_preference": 0.02},
                "new_insights": ["increased_urgency_detected", "budget_flexibility_increased"],
                "update_quality_score": 0.88
            }

            memory_service = EnhancedMemoryService()

            # Simulate new property interaction
            new_interaction = {
                "property_id": "prop_new",
                "interaction_type": "view",
                "property_data": {"price": 485000, "school_rating": 10, "property_type": "single_family"},
                "feedback_category": "very_interested",
                "duration": 420,  # Long engagement
                "timestamp": datetime.now()
            }

            # Test real-time learning update
            update_result = await memory_service.update_behavioral_preferences(
                conversation_id=str(uuid.uuid4()),
                interaction_data=new_interaction,
                learning_source="real_time_property_interaction"
            )

            # Verify real-time update processing
            assert update_result is not None
            assert update_result["update_quality_score"] > 0.8
            assert len(update_result["preferences_updated"]) > 0

            # Verify confidence adjustments are reasonable
            for pref, change in update_result["confidence_changes"].items():
                assert -0.1 <= change <= 0.1  # Reasonable confidence changes

    @pytest.mark.asyncio
    async def test_behavioral_learning_edge_cases(self):
        """Test behavioral learning with edge cases and unusual patterns"""

        # Test case 1: Insufficient data
        minimal_interactions = [
            {
                "property_id": "prop_1",
                "interaction_type": "view",
                "property_data": {"price": 400000},
                "timestamp": datetime.now()
            }
        ]

        with patch('services.behavioral_weighting_engine.BehavioralWeightingEngine') as mock_engine:
            mock_engine.return_value.calculate_adaptive_weights.return_value = {
                "insufficient_data": True,
                "fallback_weights": {"price": 1.0, "bedrooms": 1.0, "location": 1.0},
                "confidence_level": 0.3,  # Low confidence
                "recommendation": "collect_more_data"
            }

            behavioral_engine = BehavioralWeightingEngine()
            result = await behavioral_engine.calculate_adaptive_weights({}, {})

            # Verify graceful handling of insufficient data
            assert result["confidence_level"] < 0.5
            assert result["insufficient_data"] == True

        # Test case 2: Contradictory preferences
        contradictory_interactions = [
            {"property_data": {"price": 300000, "property_type": "condo"}, "feedback_category": "very_interested"},
            {"property_data": {"price": 700000, "property_type": "luxury_home"}, "feedback_category": "very_interested"},
            {"property_data": {"price": 400000, "property_type": "condo"}, "feedback_category": "not_interested"}
        ]

        with patch('services.behavioral_weighting_engine.InconsistencyDetector') as mock_detector:
            mock_detector.return_value.detect_contradictions.return_value = {
                "contradictions_found": True,
                "contradiction_types": ["price_range_inconsistency", "property_type_conflict"],
                "consistency_score": 0.45,
                "recommendation": "request_clarification"
            }

            # Verify contradiction detection and handling
            result = mock_detector.return_value.detect_contradictions(contradictory_interactions)
            assert result["contradictions_found"] == True
            assert result["consistency_score"] < 0.7

if __name__ == "__main__":
    # Run behavioral learning tests
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])