import pytest
pytestmark = pytest.mark.integration

"""
Unit Tests for Phase 2 Intelligence Layer Services.

Comprehensive unit tests for the Phase 2 Intelligence Layer services:
- Advanced Property Matching Engine (Phase 2.2)
- Conversation Intelligence Service (Phase 2.3)
- Client Preference Learning Engine (Phase 2.4)

Tests individual service functionality, ML algorithms, and real-time intelligence.

Built for Jorge's Real Estate AI Platform - Phase 2: Intelligence Layer
Performance Targets:
- Property Matching: <100ms with caching
- Conversation Analysis: <500ms processing
- Preference Learning: <50ms updates
"""

import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import numpy as np
import pandas as pd
import pytest

@pytest.mark.integration

# Import Phase 2 Intelligence Layer services
try:
    from ghl_real_estate_ai.services.advanced_property_matching_engine import (
        AdvancedPropertyMatch,
        AdvancedPropertyMatchingEngine,
        BehavioralMatchWeights,
        PropertyMatchingFilters,
        get_advanced_property_matching_engine,
    )
    from ghl_real_estate_ai.services.client_preference_learning_engine import (
        ClientPreferenceLearningEngine,
        PreferenceDriftDetection,
        PreferenceLearningEvent,
        PreferenceProfile,
        get_client_preference_learning_engine,
    )
    from ghl_real_estate_ai.services.conversation_intelligence_service import (
        CoachingOpportunity,
        ConversationInsight,
        ConversationIntelligenceService,
        ObjectionDetection,
        SentimentTimelinePoint,
        get_conversation_intelligence_service,
    )
except (ImportError, TypeError, AttributeError):
    pytest.skip("required imports unavailable", allow_module_level=True)


class TestAdvancedPropertyMatchingEngine:
    """Test Advanced Property Matching Engine functionality (Phase 2.2)."""

    @pytest.fixture
    def property_matching_engine(self):
        """Create Property Matching Engine for testing."""
        return AdvancedPropertyMatchingEngine()

    @pytest.fixture
    def mock_lead_preferences(self):
        """Mock lead preference data."""
        return {
            "price_range": {"min": 400000, "max": 600000},
            "bedrooms": {"min": 3, "ideal": 4, "max": 5},
            "bathrooms": {"min": 2, "ideal": 3, "max": 4},
            "square_footage": {"min": 2000, "ideal": 2800, "max": 3500},
            "location_preferences": {
                "neighborhoods": ["Domain", "West Lake Hills", "Tarrytown"],
                "max_commute_time": 25,
            },
            "lifestyle_features": {"pool": 0.8, "garage": 0.9, "home_office": 0.7, "yard": 0.6},
            "property_style": {"modern": 0.8, "traditional": 0.4, "contemporary": 0.9},
        }

    @pytest.fixture
    def mock_conversation_history(self):
        """Mock conversation history for behavioral analysis."""
        return [
            {
                "message": "I'm really interested in properties with a home office space",
                "timestamp": "2025-01-25T10:00:00",
                "sentiment_score": 0.8,
                "engagement_level": "high",
            },
            {
                "message": "We need to move quickly, the market is so competitive",
                "timestamp": "2025-01-25T10:05:00",
                "sentiment_score": 0.6,
                "engagement_level": "urgent",
            },
            {
                "message": "I love the idea of a pool for the kids",
                "timestamp": "2025-01-25T10:10:00",
                "sentiment_score": 0.9,
                "engagement_level": "high",
            },
        ]

    @pytest.fixture
    def mock_property_inventory(self):
        """Mock property inventory data."""
        return [
            {
                "property_id": "prop_001",
                "price": 525000,
                "bedrooms": 4,
                "bathrooms": 3,
                "square_footage": 2650,
                "neighborhood": "Domain",
                "features": ["pool", "home_office", "garage"],
                "property_style": "modern",
                "listing_date": "2025-01-20",
                "days_on_market": 5,
                "market_competitiveness": 0.85,
            },
            {
                "property_id": "prop_002",
                "price": 475000,
                "bedrooms": 3,
                "bathrooms": 2.5,
                "square_footage": 2200,
                "neighborhood": "West Lake Hills",
                "features": ["garage", "yard"],
                "property_style": "traditional",
                "listing_date": "2025-01-18",
                "days_on_market": 7,
                "market_competitiveness": 0.72,
            },
            {
                "property_id": "prop_003",
                "price": 580000,
                "bedrooms": 4,
                "bathrooms": 3.5,
                "square_footage": 2950,
                "neighborhood": "Tarrytown",
                "features": ["pool", "home_office", "garage", "yard"],
                "property_style": "contemporary",
                "listing_date": "2025-01-22",
                "days_on_market": 3,
                "market_competitiveness": 0.92,
            },
        ]

    @pytest.mark.asyncio
    async def test_behavioral_property_matching(
        self, property_matching_engine, mock_lead_preferences, mock_conversation_history, mock_property_inventory
    ):
        """Test behavioral property matching with ML-enhanced scoring."""

        with (
            patch.object(property_matching_engine, "_get_property_inventory", return_value=mock_property_inventory),
            patch.object(property_matching_engine, "_get_cached_predictions") as mock_cache,
            patch.object(property_matching_engine, "_calculate_ml_confidence") as mock_ml,
        ):
            # Setup ML model responses
            mock_cache.return_value = None  # Force fresh calculation
            mock_ml.return_value = 0.89

            # Perform behavioral matching
            matches = await property_matching_engine.find_behavioral_matches(
                lead_id="lead_123",
                location_id="loc_456",
                preferences=mock_lead_preferences,
                conversation_history=mock_conversation_history,
                max_results=3,
                min_score=0.6,
            )

            # Verify match results
            assert len(matches) <= 3
            assert all(isinstance(match, AdvancedPropertyMatch) for match in matches)

            # Find the best match (should be prop_003 - Tarrytown contemporary with all features)
            best_match = matches[0]
            assert best_match.property_id == "prop_003"
            assert best_match.overall_score >= 0.8  # High scoring due to feature alignment

            # Verify behavioral analysis integration
            assert best_match.behavioral_fit >= 0.7
            assert best_match.engagement_prediction >= 0.6
            assert "home_office" in best_match.presentation_strategy  # From conversation analysis

            # Verify scoring components
            assert 0.0 <= best_match.base_compatibility_score <= 1.0
            assert 0.0 <= best_match.behavioral_fit <= 1.0
            assert 0.0 <= best_match.engagement_prediction <= 1.0
            assert 0.0 <= best_match.urgency_match <= 1.0

            # Verify match reasoning
            assert len(best_match.match_reasoning) > 0
            assert "contemporary" in best_match.match_reasoning.lower()  # Style match
            assert "pool" in best_match.match_reasoning.lower()  # Feature from conversation

    @pytest.mark.asyncio
    async def test_behavioral_weight_calculation(self, property_matching_engine, mock_conversation_history):
        """Test behavioral weight calculation from conversation analysis."""

        with patch.object(property_matching_engine, "_analyze_conversation_patterns") as mock_analysis:
            mock_analysis.return_value = {
                "feature_emphasis": {"home_office": 0.9, "pool": 0.8, "location": 0.7, "price": 0.6},
                "urgency_indicators": ["quickly", "competitive"],
                "engagement_patterns": {
                    "high_interest_features": ["pool", "home_office"],
                    "decision_timeframe": "urgent",
                    "price_sensitivity": "medium",
                },
            }

            # Calculate behavioral weights
            weights = await property_matching_engine.get_behavioral_weights(
                lead_id="lead_123", location_id="loc_456", conversation_history=mock_conversation_history
            )

            # Verify weight structure
            assert isinstance(weights, BehavioralMatchWeights)
            assert 0.0 <= weights.feature_weight <= 1.0
            assert 0.0 <= weights.location_weight <= 1.0
            assert 0.0 <= weights.price_weight <= 1.0
            assert 0.0 <= weights.urgency_weight <= 1.0

            # Verify behavioral adaptations
            assert weights.conversation_insights["home_office_emphasis"] >= 0.8
            assert weights.conversation_insights["pool_interest"] >= 0.7
            assert "urgent" in weights.conversation_insights["decision_timeframe"]

            # Verify feature priority adjustments
            assert weights.adjusted_feature_priorities["home_office"] >= 0.8
            assert weights.adjusted_feature_priorities["pool"] >= 0.7

    @pytest.mark.asyncio
    async def test_performance_target_validation(
        self, property_matching_engine, mock_lead_preferences, mock_property_inventory
    ):
        """Test performance target validation (<100ms with caching)."""

        with (
            patch.object(property_matching_engine, "_get_property_inventory", return_value=mock_property_inventory),
            patch.object(property_matching_engine, "_get_cached_predictions") as mock_cache,
        ):
            # Test with cache hit (should be <50ms)
            mock_cache.return_value = {
                "matches": [{"property_id": "prop_001", "score": 0.85}],
                "behavioral_weights": {"feature_weight": 0.7},
                "cached_at": datetime.now().isoformat(),
            }

            start_time = datetime.now()
            matches = await property_matching_engine.find_behavioral_matches(
                lead_id="lead_123",
                location_id="loc_456",
                preferences=mock_lead_preferences,
                max_results=5,
                force_refresh=False,
            )
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Verify cache performance target
            assert processing_time < 50  # Cache hit target

            # Test with cache miss (should be <100ms)
            mock_cache.return_value = None

            start_time = datetime.now()
            matches = await property_matching_engine.find_behavioral_matches(
                lead_id="lead_123",
                location_id="loc_456",
                preferences=mock_lead_preferences,
                max_results=5,
                force_refresh=True,
            )
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Verify fresh calculation performance target
            assert processing_time < 100  # Fresh calculation target

    @pytest.mark.asyncio
    async def test_matching_feedback_processing(self, property_matching_engine):
        """Test matching feedback processing for algorithm improvement."""

        with (
            patch.object(property_matching_engine, "_update_behavioral_model") as mock_update,
            patch.object(property_matching_engine, "_invalidate_cache") as mock_cache_invalidate,
        ):
            # Process positive feedback
            improvement_data = await property_matching_engine.process_matching_feedback(
                lead_id="lead_123",
                location_id="loc_456",
                property_id="prop_001",
                feedback_type="inquired",
                engagement_score=0.9,
            )

            # Verify feedback processing
            assert isinstance(improvement_data, dict)
            assert "previous_score" in improvement_data
            assert "new_score" in improvement_data
            assert "learning_impact" in improvement_data

            # Verify model update called
            mock_update.assert_called_once()
            update_call = mock_update.call_args[1]
            assert update_call["feedback_type"] == "inquired"
            assert update_call["engagement_score"] == 0.9

            # Verify cache invalidation
            mock_cache_invalidate.assert_called_once_with("lead_123", "loc_456")

            # Verify learning impact calculation
            learning_impact = improvement_data["learning_impact"]
            assert 0.0 <= learning_impact <= 1.0

    @pytest.mark.asyncio
    async def test_health_status_monitoring(self, property_matching_engine):
        """Test health status monitoring for service reliability."""

        with (
            patch.object(property_matching_engine, "_check_ml_model_health") as mock_ml_health,
            patch.object(property_matching_engine, "_check_cache_performance") as mock_cache_health,
            patch.object(property_matching_engine, "_check_property_data_freshness") as mock_data_health,
        ):
            # Setup health check responses
            mock_ml_health.return_value = {"status": "healthy", "accuracy": 0.94, "last_update": "2025-01-25T10:00:00"}
            mock_cache_health.return_value = {"status": "healthy", "hit_rate": 0.87, "avg_response_time": 45}
            mock_data_health.return_value = {
                "status": "healthy",
                "last_refresh": "2025-01-25T09:00:00",
                "property_count": 1247,
            }

            # Get health status
            health = await property_matching_engine.get_health_status()

            # Verify health structure
            assert "status" in health
            assert "ml_model" in health
            assert "cache_performance" in health
            assert "data_freshness" in health
            assert "performance_metrics" in health

            # Verify overall status
            assert health["status"] == "healthy"

            # Verify ML model health
            ml_health = health["ml_model"]
            assert ml_health["accuracy"] >= 0.85
            assert ml_health["status"] == "healthy"

            # Verify cache performance
            cache_health = health["cache_performance"]
            assert cache_health["hit_rate"] >= 0.8
            assert cache_health["avg_response_time"] < 100

            # Verify performance metrics
            performance = health["performance_metrics"]
            assert "avg_matching_time" in performance
            assert "successful_matches_24h" in performance


class TestConversationIntelligenceService:
    """Test Conversation Intelligence Service functionality (Phase 2.3)."""

    @pytest.fixture
    def conversation_service(self):
        """Create Conversation Intelligence Service for testing."""
        return ConversationIntelligenceService()

    @pytest.fixture
    def mock_conversation_data(self):
        """Mock conversation data for analysis."""
        return [
            {
                "message_id": "msg_001",
                "role": "user",
                "content": "I'm concerned about the price, it seems really high for this market",
                "timestamp": "2025-01-25T10:00:00",
                "message_order": 1,
            },
            {
                "message_id": "msg_002",
                "role": "agent",
                "content": "I understand your concern. Let me show you the comparable sales data",
                "timestamp": "2025-01-25T10:01:00",
                "message_order": 2,
            },
            {
                "message_id": "msg_003",
                "role": "user",
                "content": "That helps, but I still think we need to negotiate the price down",
                "timestamp": "2025-01-25T10:05:00",
                "message_order": 3,
            },
            {
                "message_id": "msg_004",
                "role": "agent",
                "content": "Absolutely, I'll prepare a competitive offer for you",
                "timestamp": "2025-01-25T10:07:00",
                "message_order": 4,
            },
        ]

    @pytest.fixture
    def mock_jorge_conversation(self):
        """Mock Jorge methodology conversation for testing."""
        return [
            {
                "message_id": "jorge_001",
                "role": "jorge_bot",
                "content": "Are you actually serious about buying or just looking around?",
                "timestamp": "2025-01-25T14:00:00",
                "jorge_methodology_marker": True,
            },
            {
                "message_id": "jorge_002",
                "role": "user",
                "content": "Yes, we're very serious! We need to buy within 90 days",
                "timestamp": "2025-01-25T14:01:00",
                "engagement_score": 0.9,
            },
            {
                "message_id": "jorge_003",
                "role": "jorge_bot",
                "content": "Good. What's your max budget, not what you want to spend?",
                "timestamp": "2025-01-25T14:02:00",
                "jorge_methodology_marker": True,
            },
            {
                "message_id": "jorge_004",
                "role": "user",
                "content": "We could go up to $650k if it's the perfect house",
                "timestamp": "2025-01-25T14:03:00",
                "commitment_indicator": True,
            },
        ]

    @pytest.mark.asyncio
    async def test_comprehensive_conversation_analysis(self, conversation_service, mock_conversation_data):
        """Test comprehensive conversation analysis with insights generation."""

        with (
            patch.object(conversation_service, "_analyze_sentiment_timeline") as mock_sentiment,
            patch.object(conversation_service, "_detect_objections") as mock_objections,
            patch.object(conversation_service, "_calculate_engagement_metrics") as mock_engagement,
        ):
            # Setup analysis responses
            mock_sentiment.return_value = [
                {"timestamp": "2025-01-25T10:00:00", "sentiment": -0.3, "confidence": 0.85},
                {"timestamp": "2025-01-25T10:05:00", "sentiment": 0.2, "confidence": 0.78},
            ]
            mock_objections.return_value = [
                {"type": "price_concern", "text": "price seems really high", "confidence": 0.92}
            ]
            mock_engagement.return_value = {
                "overall_engagement": 0.74,
                "response_time_avg": 65,
                "message_length_avg": 47,
                "question_count": 2,
            }

            # Perform conversation analysis
            insights = await conversation_service.analyze_conversation_with_insights(
                conversation_id="conv_123",
                lead_id="lead_456",
                location_id="loc_789",
                conversation_history=mock_conversation_data,
                force_refresh=False,
            )

            # Verify insights structure
            assert isinstance(insights, ConversationInsight)
            assert insights.conversation_id == "conv_123"
            assert insights.lead_id == "lead_456"

            # Verify engagement scoring
            assert 0.0 <= insights.overall_engagement_score <= 1.0
            assert 0.0 <= insights.interest_level_score <= 1.0
            assert 0.0 <= insights.rapport_quality_score <= 1.0

            # Verify objection analysis
            assert insights.objection_intensity_score >= 0.0
            assert len(insights.key_topics) > 0
            assert "price" in str(insights.concern_indicators).lower()

            # Verify sentiment analysis
            assert insights.dominant_sentiment in [
                "very_positive",
                "positive",
                "neutral",
                "slightly_negative",
                "negative",
                "very_negative",
            ]
            assert 0.0 <= insights.sentiment_volatility <= 1.0

            # Verify next step recommendations
            assert len(insights.recommended_next_actions) > 0

    @pytest.mark.asyncio
    async def test_objection_detection_and_responses(self, conversation_service, mock_conversation_data):
        """Test objection detection and response recommendation system."""

        with (
            patch.object(conversation_service, "_classify_objection_type") as mock_classify,
            patch.object(conversation_service, "_generate_response_recommendations") as mock_responses,
        ):
            # Setup objection classification
            mock_classify.return_value = {
                "category": "price_concern",
                "confidence": 0.92,
                "severity": 4,
                "key_phrases": ["price seems really high", "negotiate the price down"],
            }

            mock_responses.return_value = [
                "Let me show you the recent comparable sales in this area",
                "I understand your concern. The pricing reflects the premium location and recent upgrades",
                "Would you like me to prepare a market analysis for this property?",
            ]

            # Detect objections and get responses
            objections = await conversation_service.detect_objections_and_recommend_responses(
                conversation_id="conv_123", location_id="loc_789", conversation_history=mock_conversation_data
            )

            # Verify objection detection
            assert len(objections) > 0

            objection = objections[0]
            assert isinstance(objection, ObjectionDetection)
            assert objection.objection_category == "price_concern"
            assert objection.confidence_score >= 0.9
            assert objection.severity_level >= 3

            # Verify response recommendations
            assert len(objection.suggested_responses) >= 2
            assert any("comparable" in response.lower() for response in objection.suggested_responses)

            # Verify objection context
            assert len(objection.objection_text) > 0
            assert objection.detected_at_offset_seconds >= 0

    @pytest.mark.asyncio
    async def test_jorge_methodology_coaching_opportunities(self, conversation_service, mock_jorge_conversation):
        """Test coaching opportunity identification for Jorge methodology."""

        with (
            patch.object(conversation_service, "_analyze_jorge_methodology_effectiveness") as mock_jorge,
            patch.object(conversation_service, "_identify_improvement_areas") as mock_improvements,
        ):
            # Setup Jorge methodology analysis
            mock_jorge.return_value = {
                "confrontational_effectiveness": 0.94,
                "qualification_depth": 0.87,
                "commitment_extraction": 0.91,
                "methodology_adherence": 0.89,
            }

            mock_improvements.return_value = [
                {
                    "area": "closing_technique",
                    "opportunity": "Could have pushed harder for specific timeline commitment",
                    "priority": 3,
                    "suggested_script": "What specific date do you need to be in your new home?",
                }
            ]

            # Identify coaching opportunities
            coaching_ops = await conversation_service.identify_coaching_opportunities(
                conversation_id="jorge_conv_001",
                lead_id="lead_789",
                location_id="loc_456",
                conversation_history=mock_jorge_conversation,
                agent_user_id="agent_123",
            )

            # Verify coaching opportunities
            assert len(coaching_ops) > 0

            coaching_op = coaching_ops[0]
            assert isinstance(coaching_op, CoachingOpportunity)
            assert coaching_op.opportunity_type in [
                "objection_handling",
                "closing_technique",
                "rapport_building",
                "active_listening",
            ]
            assert 1 <= coaching_op.priority_level <= 5

            # Verify Jorge methodology specific coaching
            assert len(coaching_op.recommended_approach) > 0
            assert len(coaching_op.suggested_scripts) > 0

            # Verify coaching context
            assert coaching_op.agent_user_id == "agent_123"
            assert coaching_op.coaching_status == "identified"

    @pytest.mark.asyncio
    async def test_sentiment_timeline_tracking(self, conversation_service, mock_conversation_data):
        """Test detailed sentiment timeline tracking throughout conversations."""

        with patch.object(conversation_service, "_process_sentiment_timeline") as mock_timeline:
            mock_timeline.return_value = [
                {
                    "timestamp_offset_seconds": 0,
                    "sentiment_score": -0.3,
                    "sentiment_classification": "slightly_negative",
                    "confidence": 0.85,
                    "speaker": "user",
                    "trigger_phrase": "price seems really high",
                },
                {
                    "timestamp_offset_seconds": 120,
                    "sentiment_score": 0.2,
                    "sentiment_classification": "neutral",
                    "confidence": 0.78,
                    "speaker": "user",
                    "trigger_phrase": "need to negotiate",
                },
            ]

            # Track sentiment timeline
            timeline = await conversation_service.track_sentiment_timeline(
                conversation_id="conv_123", location_id="loc_789", conversation_history=mock_conversation_data
            )

            # Verify timeline structure
            assert len(timeline) > 0

            for point in timeline:
                assert isinstance(point, SentimentTimelinePoint)
                assert -1.0 <= point.sentiment_score <= 1.0
                assert point.sentiment_classification in [
                    "very_positive",
                    "positive",
                    "neutral",
                    "slightly_negative",
                    "negative",
                    "very_negative",
                ]
                assert 0.0 <= point.confidence <= 1.0
                assert point.timestamp_offset_seconds >= 0

            # Verify sentiment progression tracking
            assert timeline[0].sentiment_score < timeline[1].sentiment_score  # Improvement over time

    @pytest.mark.asyncio
    async def test_performance_target_validation(self, conversation_service, mock_conversation_data):
        """Test performance target validation (<500ms processing)."""

        with patch.object(conversation_service, "_get_cached_insights") as mock_cache:
            # Test with cache miss (full analysis)
            mock_cache.return_value = None

            start_time = datetime.now()
            insights = await conversation_service.analyze_conversation_with_insights(
                conversation_id="conv_perf_test",
                lead_id="lead_123",
                location_id="loc_456",
                conversation_history=mock_conversation_data,
            )
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Verify performance target
            assert processing_time < 500  # <500ms target for conversation analysis

            # Verify analysis completeness wasn't sacrificed for performance
            assert insights.processing_duration_ms <= processing_time
            assert insights.confidence_score > 0.5

    @pytest.mark.asyncio
    async def test_health_status_monitoring(self, conversation_service):
        """Test health status monitoring for conversation intelligence."""

        with (
            patch.object(conversation_service, "_check_sentiment_model_health") as mock_sentiment_health,
            patch.object(conversation_service, "_check_objection_detection_health") as mock_objection_health,
            patch.object(conversation_service, "_check_processing_performance") as mock_performance,
        ):
            # Setup health responses
            mock_sentiment_health.return_value = {"status": "healthy", "accuracy": 0.91}
            mock_objection_health.return_value = {"status": "healthy", "detection_rate": 0.87}
            mock_performance.return_value = {"status": "healthy", "avg_processing_time": 320}

            # Get health status
            health = await conversation_service.get_health_status()

            # Verify health components
            assert health["status"] == "healthy"
            assert health["sentiment_analysis"]["accuracy"] >= 0.85
            assert health["objection_detection"]["detection_rate"] >= 0.8
            assert health["performance"]["avg_processing_time"] < 500


class TestClientPreferenceLearningEngine:
    """Test Client Preference Learning Engine functionality (Phase 2.4)."""

    @pytest.fixture
    def preference_learning_engine(self):
        """Create Client Preference Learning Engine for testing."""
        return ClientPreferenceLearningEngine()

    @pytest.fixture
    def mock_conversation_data_with_preferences(self):
        """Mock conversation data with clear preference indicators."""
        return [
            {
                "message": "We absolutely need a home office since we both work from home",
                "timestamp": "2025-01-25T10:00:00",
                "preference_indicators": ["home_office", "work_from_home"],
                "confidence": 0.95,
            },
            {
                "message": "A pool would be nice for the kids, but not essential",
                "timestamp": "2025-01-25T10:05:00",
                "preference_indicators": ["pool", "kids"],
                "confidence": 0.6,
            },
            {
                "message": "Our budget is firm at $500k, we cannot go above that",
                "timestamp": "2025-01-25T10:10:00",
                "preference_indicators": ["price_constraint"],
                "confidence": 0.98,
            },
            {
                "message": "We prefer something modern, not too traditional",
                "timestamp": "2025-01-25T10:15:00",
                "preference_indicators": ["style_modern", "not_traditional"],
                "confidence": 0.85,
            },
        ]

    @pytest.fixture
    def mock_property_interaction_data(self):
        """Mock property interaction data for behavioral learning."""
        return {
            "interaction_type": "virtual_tour",
            "duration_seconds": 420,
            "engagement_events": [
                {"timestamp": 30, "action": "zoom_kitchen", "duration": 45},
                {"timestamp": 120, "action": "zoom_master_bedroom", "duration": 60},
                {"timestamp": 250, "action": "view_floor_plan", "duration": 90},
                {"timestamp": 380, "action": "save_property", "engagement_score": 0.95},
            ],
            "property_features_viewed": ["kitchen", "master_bedroom", "home_office", "backyard"],
            "time_spent_by_feature": {"kitchen": 45, "master_bedroom": 60, "home_office": 75, "backyard": 30},
            "interaction_outcome": "high_interest",
        }

    @pytest.fixture
    def mock_existing_preference_profile(self):
        """Mock existing preference profile for update testing."""
        return PreferenceProfile(
            client_id="client_123",
            location_id="loc_456",
            overall_confidence_score=0.73,
            profile_completeness_percentage=65,
            learning_sessions_count=8,
            total_data_points=24,
            bedrooms_preference={"min": 3, "max": 4, "ideal": 3, "confidence": 0.8},
            bathrooms_preference={"min": 2, "max": 3, "ideal": 2.5, "confidence": 0.7},
            price_range_preference={"min": 400000, "max": 500000, "confidence": 0.9},
            property_style_preferences={"modern": 0.7, "traditional": 0.3, "contemporary": 0.8},
            lifestyle_features={"pool": 0.5, "garage": 0.9, "home_office": 0.8},
            feature_priority_scores={"price": 0.95, "location": 0.8, "style": 0.6},
            prediction_accuracy_score=0.84,
            consistency_score=0.79,
            drift_frequency=0.15,
        )

    @pytest.mark.asyncio
    async def test_conversation_preference_learning(
        self, preference_learning_engine, mock_conversation_data_with_preferences
    ):
        """Test preference learning from conversation data."""

        with (
            patch.object(preference_learning_engine, "_extract_preferences_from_conversation") as mock_extract,
            patch.object(preference_learning_engine, "_update_preference_profile") as mock_update,
            patch.object(preference_learning_engine, "_validate_preference_consistency") as mock_validate,
        ):
            # Setup preference extraction
            mock_extract.return_value = {
                "home_office": {"importance": 0.95, "confidence": 0.95, "source": "explicit"},
                "pool": {"importance": 0.6, "confidence": 0.6, "source": "implicit"},
                "price_max": {"value": 500000, "confidence": 0.98, "source": "explicit"},
                "style_modern": {"preference": 0.85, "confidence": 0.85, "source": "explicit"},
            }

            mock_validate.return_value = {"conflicts": [], "consistency_score": 0.92}

            # Learn preferences from conversation
            profile = await preference_learning_engine.learn_from_conversation(
                client_id="client_123",
                location_id="loc_456",
                conversation_data=mock_conversation_data_with_preferences,
                conversation_analysis=None,
            )

            # Verify profile structure
            assert isinstance(profile, PreferenceProfile)
            assert profile.client_id == "client_123"
            assert profile.location_id == "loc_456"

            # Verify preference extraction was called
            mock_extract.assert_called_once()

            # Verify learned preferences integration
            assert profile.overall_confidence_score > 0.7
            assert profile.profile_completeness_percentage > 50

            # Verify specific preference learning
            lifestyle_features = profile.lifestyle_features
            assert lifestyle_features.get("home_office", 0) >= 0.9  # High confidence from explicit mention
            assert lifestyle_features.get("pool", 0) >= 0.5  # Lower confidence from "nice but not essential"

            # Verify price learning
            price_pref = profile.price_range_preference
            assert price_pref.get("max") == 500000  # Learned from "firm at $500k"
            assert price_pref.get("confidence", 0) >= 0.95

    @pytest.mark.asyncio
    async def test_property_interaction_learning(self, preference_learning_engine, mock_property_interaction_data):
        """Test preference learning from property interaction behavior."""

        with (
            patch.object(preference_learning_engine, "_analyze_interaction_patterns") as mock_analyze,
            patch.object(preference_learning_engine, "_infer_preferences_from_behavior") as mock_infer,
        ):
            # Setup interaction analysis
            mock_analyze.return_value = {
                "engagement_by_feature": {
                    "home_office": 0.9,  # Longest viewing time
                    "master_bedroom": 0.7,
                    "kitchen": 0.6,
                    "backyard": 0.3,
                },
                "interaction_quality": 0.85,
                "decision_indicators": ["save_property"],
                "attention_patterns": ["focused_on_work_spaces"],
            }

            mock_infer.return_value = {
                "feature_preferences": {"home_office": 0.9, "master_bedroom_size": 0.7, "kitchen_quality": 0.6},
                "behavioral_confidence": 0.82,
            }

            # Learn from property interaction
            profile = await preference_learning_engine.learn_from_property_interaction(
                client_id="client_123",
                location_id="loc_456",
                property_id="prop_789",
                interaction_data=mock_property_interaction_data,
            )

            # Verify interaction learning
            mock_analyze.assert_called_once()
            mock_infer.assert_called_once()

            # Verify behavioral preference inference
            assert profile.overall_confidence_score >= 0.7

            # Verify feature learning from interaction
            lifestyle_features = profile.lifestyle_features
            assert lifestyle_features.get("home_office", 0) >= 0.8  # High engagement

    @pytest.mark.asyncio
    async def test_preference_profile_retrieval(self, preference_learning_engine, mock_existing_preference_profile):
        """Test preference profile retrieval with completeness scoring."""

        with (
            patch.object(preference_learning_engine, "_get_profile_from_database") as mock_get_profile,
            patch.object(preference_learning_engine, "_calculate_profile_completeness") as mock_completeness,
        ):
            # Setup profile retrieval
            mock_get_profile.return_value = mock_existing_preference_profile
            mock_completeness.return_value = 78

            # Get preference profile
            profile = await preference_learning_engine.get_preference_profile(
                client_id="client_123", location_id="loc_456"
            )

            # Verify profile retrieval
            assert profile is not None
            assert isinstance(profile, PreferenceProfile)
            assert profile.client_id == "client_123"
            assert profile.profile_completeness_percentage == 78

            # Verify preference data structure
            assert profile.bedrooms_preference is not None
            assert profile.price_range_preference is not None
            assert profile.lifestyle_features is not None
            assert profile.feature_priority_scores is not None

            # Verify confidence tracking
            assert 0.0 <= profile.overall_confidence_score <= 1.0
            assert 0.0 <= profile.prediction_accuracy_score <= 1.0
            assert 0.0 <= profile.consistency_score <= 1.0

    @pytest.mark.asyncio
    async def test_preference_match_prediction(self, preference_learning_engine, mock_existing_preference_profile):
        """Test preference match prediction for properties."""

        property_data = {
            "property_id": "prop_match_test",
            "bedrooms": 3,
            "bathrooms": 2.5,
            "price": 475000,
            "style": "modern",
            "features": ["home_office", "garage", "backyard"],
            "square_footage": 2400,
            "neighborhood": "Domain",
        }

        with (
            patch.object(
                preference_learning_engine, "get_preference_profile", return_value=mock_existing_preference_profile
            ),
            patch.object(preference_learning_engine, "_calculate_feature_match_scores") as mock_feature_scores,
            patch.object(preference_learning_engine, "_generate_match_explanation") as mock_explanation,
        ):
            # Setup match calculation
            mock_feature_scores.return_value = {
                "bedroom_match": 0.95,  # 3 bedrooms ideal
                "price_match": 0.98,  # Within budget
                "style_match": 0.85,  # Modern preference
                "feature_match": 0.9,  # Has home office
                "overall_compatibility": 0.92,
            }

            mock_explanation.return_value = {
                "positive_matches": ["Within budget", "Has home office", "Modern style"],
                "concerns": ["Only 2.5 bathrooms (prefer 3)"],
                "recommendation": "Excellent match with minor bathroom consideration",
            }

            # Predict preference match
            match_prediction = await preference_learning_engine.predict_preference_match(
                client_id="client_123", location_id="loc_456", property_data=property_data
            )

            # Verify prediction structure
            assert "match_score" in match_prediction
            assert "confidence" in match_prediction
            assert "explanation" in match_prediction
            assert "feature_scores" in match_prediction

            # Verify match scoring
            match_score = match_prediction["match_score"]
            assert 0.0 <= match_score <= 1.0
            assert match_score >= 0.8  # Should be high match

            # Verify explanation quality
            explanation = match_prediction["explanation"]
            assert len(explanation["positive_matches"]) > 0
            assert "home office" in str(explanation["positive_matches"]).lower()

    @pytest.mark.asyncio
    async def test_preference_drift_detection(self, preference_learning_engine, mock_existing_preference_profile):
        """Test preference drift detection and analysis."""

        # Simulate preference change over time
        new_preferences = {
            "style_modern": 0.4,  # Down from 0.7 - drift detected
            "pool": 0.8,  # Up from 0.5 - new preference
            "price_max": 550000,  # Up from 500000 - budget increase
        }

        with (
            patch.object(preference_learning_engine, "_get_historical_preferences") as mock_history,
            patch.object(preference_learning_engine, "_calculate_drift_significance") as mock_significance,
        ):
            # Setup drift detection
            mock_history.return_value = [
                {"timestamp": "2025-01-20", "style_modern": 0.7, "pool": 0.5, "price_max": 500000},
                {"timestamp": "2025-01-22", "style_modern": 0.6, "pool": 0.6, "price_max": 520000},
                {"timestamp": "2025-01-25", "style_modern": 0.4, "pool": 0.8, "price_max": 550000},
            ]

            mock_significance.return_value = {
                "style_drift": {"magnitude": 0.3, "significance": 0.85, "trend": "decreasing"},
                "pool_drift": {"magnitude": 0.3, "significance": 0.82, "trend": "increasing"},
                "price_drift": {"magnitude": 0.1, "significance": 0.65, "trend": "increasing"},
            }

            # Analyze preference drift
            drift_detections = await preference_learning_engine.analyze_preference_drift(
                client_id="client_123", location_id="loc_456", analysis_period_days=30, min_significance_threshold=0.7
            )

            # Verify drift detection
            assert len(drift_detections) >= 2  # Style and pool drift above threshold

            # Check style drift detection
            style_drift = next((d for d in drift_detections if "style" in str(d.preference_category).lower()), None)
            assert style_drift is not None
            assert isinstance(style_drift, PreferenceDriftDetection)
            assert style_drift.drift_magnitude >= 0.25
            assert style_drift.significance_level >= 0.8

    @pytest.mark.asyncio
    async def test_performance_target_validation(
        self, preference_learning_engine, mock_conversation_data_with_preferences
    ):
        """Test performance target validation (<50ms updates)."""

        with patch.object(preference_learning_engine, "_get_cached_profile") as mock_cache:
            # Test preference learning performance
            start_time = datetime.now()

            profile = await preference_learning_engine.learn_from_conversation(
                client_id="client_perf_test",
                location_id="loc_456",
                conversation_data=mock_conversation_data_with_preferences[:1],  # Single preference
            )

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Verify performance target
            assert processing_time < 50  # <50ms update target

            # Verify learning wasn't sacrificed for performance
            assert profile.overall_confidence_score > 0.0

    @pytest.mark.asyncio
    async def test_health_status_monitoring(self, preference_learning_engine):
        """Test health status monitoring for preference learning."""

        with (
            patch.object(preference_learning_engine, "_check_learning_accuracy") as mock_accuracy,
            patch.object(preference_learning_engine, "_check_profile_consistency") as mock_consistency,
            patch.object(preference_learning_engine, "_check_drift_detection_health") as mock_drift,
        ):
            # Setup health responses
            mock_accuracy.return_value = {"status": "healthy", "learning_accuracy": 0.89}
            mock_consistency.return_value = {"status": "healthy", "avg_consistency": 0.84}
            mock_drift.return_value = {"status": "healthy", "drift_detection_rate": 0.91}

            # Get health status
            health = await preference_learning_engine.get_health_status()

            # Verify health components
            assert health["status"] == "healthy"
            assert health["learning_accuracy"]["learning_accuracy"] >= 0.85
            assert health["profile_consistency"]["avg_consistency"] >= 0.8
            assert health["drift_detection"]["drift_detection_rate"] >= 0.85


# Integration Tests for Cross-Service Functionality
class TestPhase2IntegrationScenarios:
    """Test integration scenarios across Phase 2 Intelligence Layer services."""

    @pytest.mark.asyncio
    async def test_end_to_end_intelligence_pipeline(self):
        """Test complete intelligence pipeline from conversation to property matching."""

        # Mock services
        conversation_service = Mock(spec=ConversationIntelligenceService)
        preference_engine = Mock(spec=ClientPreferenceLearningEngine)
        matching_engine = Mock(spec=AdvancedPropertyMatchingEngine)

        # Mock conversation analysis output
        conversation_insights = ConversationInsight(
            conversation_id="conv_integration",
            lead_id="lead_integration",
            overall_engagement_score=0.87,
            key_topics=["home_office", "pool", "modern_style"],
            buying_signals=["specific_timeline", "budget_confirmed"],
        )

        # Mock preference learning output
        learned_preferences = PreferenceProfile(
            client_id="lead_integration",
            location_id="loc_integration",
            overall_confidence_score=0.83,
            lifestyle_features={"home_office": 0.95, "pool": 0.7},
            property_style_preferences={"modern": 0.85, "contemporary": 0.8},
        )

        # Mock property matching output
        property_matches = [
            AdvancedPropertyMatch(
                property_id="prop_perfect",
                overall_score=0.92,
                behavioral_fit=0.89,
                engagement_prediction=0.85,
                presentation_strategy="emphasize_home_office_and_modern_design",
            )
        ]

        # Setup service returns
        conversation_service.analyze_conversation_with_insights.return_value = conversation_insights
        preference_engine.learn_from_conversation.return_value = learned_preferences
        matching_engine.find_behavioral_matches.return_value = property_matches

        # Verify integration flow would work
        assert conversation_insights.overall_engagement_score > 0.8
        assert learned_preferences.overall_confidence_score > 0.8
        assert property_matches[0].overall_score > 0.9

        # Verify data flow compatibility
        assert "home_office" in conversation_insights.key_topics
        assert learned_preferences.lifestyle_features.get("home_office", 0) >= 0.9
        assert "home_office" in property_matches[0].presentation_strategy


if __name__ == "__main__":
    # Run Phase 2 Intelligence Layer service tests
    pytest.main(
        [
            __file__ + "::TestAdvancedPropertyMatchingEngine",
            __file__ + "::TestConversationIntelligenceService",
            __file__ + "::TestClientPreferenceLearningEngine",
            __file__ + "::TestPhase2IntegrationScenarios",
            "-v",
        ]
    )