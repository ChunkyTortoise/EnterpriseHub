"""
Test Suite for Advanced Personalization Engine (Phase 5)

Comprehensive tests for ML-driven personalization system with >92% accuracy,
real-time adaptation, and intelligent profile generation.
"""

import pytest
import asyncio
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from ghl_real_estate_ai.services.claude.advanced.advanced_personalization_engine import (
    AdvancedPersonalizationEngine,
    PersonalizationProfile,
    PersonalizedRecommendation,
    CommunicationAdaptation,
    PersonalityType,
    CommunicationStyle,
    PersonalizationChannel,
    IndustryVertical,
    get_advanced_personalization_engine
)


class TestAdvancedPersonalizationEngine:
    """Test suite for Advanced Personalization Engine"""

    @pytest.fixture
    async def personalization_engine(self):
        """Create personalization engine for testing"""
        engine = AdvancedPersonalizationEngine()
        # Mock the behavioral analyzer dependency
        mock_analyzer = AsyncMock()
        engine.behavioral_analyzer = mock_analyzer
        return engine

    @pytest.fixture
    def sample_conversation_history(self):
        """Sample conversation history for testing"""
        return [
            {
                "content": "I'm looking for a luxury property in downtown with high-end amenities",
                "timestamp": datetime.now() - timedelta(hours=2),
                "speaker": "lead"
            },
            {
                "content": "I need detailed specifications and market analysis",
                "timestamp": datetime.now() - timedelta(hours=1),
                "speaker": "lead"
            },
            {
                "content": "What's the ROI potential for investment properties?",
                "timestamp": datetime.now() - timedelta(minutes=30),
                "speaker": "lead"
            }
        ]

    @pytest.fixture
    def sample_behavioral_data(self):
        """Sample behavioral data for testing"""
        return {
            "engagement_score": 0.8,
            "avg_response_time": 1.5,
            "avg_session_duration": 8.0,
            "sessions_per_week": 3.5,
            "mobile_usage_ratio": 0.6,
            "engagement_by_hour": {10: 0.8, 14: 0.9, 19: 0.7},
            "response_by_day": {"tuesday": 0.8, "wednesday": 0.9}
        }

    @pytest.fixture
    def sample_property_interactions(self):
        """Sample property interactions for testing"""
        return [
            {
                "property_type": "luxury_condo",
                "price": 850000,
                "features_viewed": ["location", "amenities", "price", "square_footage"],
                "view_duration": 180
            },
            {
                "property_type": "downtown_apartment",
                "price": 650000,
                "features_viewed": ["location", "price", "investment_potential"],
                "view_duration": 120
            }
        ]

    @pytest.mark.asyncio
    async def test_create_personalized_profile_performance(
        self,
        personalization_engine,
        sample_conversation_history,
        sample_behavioral_data,
        sample_property_interactions
    ):
        """Test personalized profile creation performance (<200ms target)"""
        start_time = datetime.now()

        profile = await personalization_engine.create_personalized_profile(
            lead_id="test_lead_001",
            conversation_history=sample_conversation_history,
            behavioral_data=sample_behavioral_data,
            property_interactions=sample_property_interactions
        )

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds() * 1000

        # Performance assertions
        assert processing_time < 200, f"Profile generation took {processing_time}ms (target: <200ms)"

        # Profile quality assertions
        assert isinstance(profile, PersonalizationProfile)
        assert profile.lead_id == "test_lead_001"
        assert profile.personality_confidence > 0.5
        assert profile.style_confidence > 0.5
        assert len(profile.preferred_channels) > 0
        assert len(profile.content_topics) > 0

    @pytest.mark.asyncio
    async def test_personalized_profile_accuracy_targets(
        self,
        personalization_engine,
        sample_conversation_history,
        sample_behavioral_data,
        sample_property_interactions
    ):
        """Test personalized profile meets >92% accuracy targets"""
        profile = await personalization_engine.create_personalized_profile(
            lead_id="accuracy_test_lead",
            conversation_history=sample_conversation_history,
            behavioral_data=sample_behavioral_data,
            property_interactions=sample_property_interactions
        )

        # Accuracy assertions
        assert profile.accuracy_metrics.get("overall_accuracy", 0) >= 0.92, \
            f"Overall accuracy {profile.accuracy_metrics.get('overall_accuracy')} below 92% target"

        # Profile completeness assertions
        assert profile.personality_type in PersonalityType
        assert profile.communication_style in CommunicationStyle
        assert profile.industry_vertical in IndustryVertical
        assert 0.0 <= profile.message_complexity_preference <= 1.0
        assert 0.0 <= profile.urgency_sensitivity <= 1.0
        assert 0.0 <= profile.detail_preference <= 1.0

    @pytest.mark.asyncio
    async def test_personality_detection_analytical(
        self,
        personalization_engine
    ):
        """Test analytical personality detection"""
        analytical_conversation = [
            {
                "content": "I need detailed market data and statistical analysis before making any decisions",
                "timestamp": datetime.now(),
                "speaker": "lead"
            },
            {
                "content": "Can you provide comparative analysis with supporting research?",
                "timestamp": datetime.now(),
                "speaker": "lead"
            }
        ]

        profile = await personalization_engine.create_personalized_profile(
            lead_id="analytical_test",
            conversation_history=analytical_conversation,
            behavioral_data={"engagement_score": 0.7},
            property_interactions=[]
        )

        assert profile.personality_type == PersonalityType.ANALYTICAL
        assert profile.personality_confidence > 0.6
        assert profile.detail_preference > 0.7  # Analytical types prefer detail

    @pytest.mark.asyncio
    async def test_personality_detection_driver(
        self,
        personalization_engine
    ):
        """Test driver personality detection"""
        driver_conversation = [
            {
                "content": "I need to make a quick decision. Show me the best properties now.",
                "timestamp": datetime.now(),
                "speaker": "lead"
            },
            {
                "content": "I want to close fast. What's available immediately?",
                "timestamp": datetime.now(),
                "speaker": "lead"
            }
        ]

        profile = await personalization_engine.create_personalized_profile(
            lead_id="driver_test",
            conversation_history=driver_conversation,
            behavioral_data={"engagement_score": 0.8},
            property_interactions=[]
        )

        assert profile.personality_type == PersonalityType.DRIVER
        assert profile.urgency_sensitivity > 0.7  # Driver types are urgency-sensitive

    @pytest.mark.asyncio
    async def test_industry_vertical_detection_luxury(
        self,
        personalization_engine
    ):
        """Test luxury vertical detection"""
        luxury_conversation = [
            {
                "content": "I'm interested in luxury waterfront properties with premium amenities",
                "timestamp": datetime.now(),
                "speaker": "lead"
            }
        ]

        luxury_interactions = [
            {
                "property_type": "luxury_estate",
                "price": 2500000,
                "features_viewed": ["luxury", "waterfront", "premium"]
            }
        ]

        profile = await personalization_engine.create_personalized_profile(
            lead_id="luxury_test",
            conversation_history=luxury_conversation,
            behavioral_data={"engagement_score": 0.8},
            property_interactions=luxury_interactions
        )

        assert profile.industry_vertical == IndustryVertical.LUXURY
        assert profile.specialization_confidence > 0.6

    @pytest.mark.asyncio
    async def test_generate_personalized_recommendations_performance(
        self,
        personalization_engine
    ):
        """Test personalized recommendation generation performance (<150ms target)"""
        # Create a profile first
        profile = PersonalizationProfile(
            lead_id="recommendation_test",
            personality_type=PersonalityType.ANALYTICAL,
            personality_confidence=0.85,
            communication_style=CommunicationStyle.TECHNICAL_DETAILED,
            style_confidence=0.80,
            preferred_channels=[PersonalizationChannel.EMAIL],
            optimal_contact_times=[("Tuesday", 10)],
            message_complexity_preference=0.8,
            urgency_sensitivity=0.3,
            detail_preference=0.9,
            content_topics=["market_analysis", "property_features"],
            preferred_property_features=["location", "investment_potential"],
            visual_vs_text_preference=0.4,
            data_driven_preference=0.9,
            interaction_patterns={},
            response_triggers=["data", "analysis"],
            objection_patterns=["price_concerns"],
            decision_making_factors=["investment_potential"],
            primary_language="en",
            cultural_considerations=[],
            formality_level=0.7,
            industry_vertical=IndustryVertical.INVESTMENT,
            specialization_confidence=0.8,
            vertical_specific_preferences={},
            profile_created=datetime.now(),
            last_updated=datetime.now(),
            profile_version="5.1.0",
            accuracy_metrics={"overall_accuracy": 0.92}
        )

        # Cache the profile
        personalization_engine.profile_cache["recommendation_test"] = profile

        start_time = datetime.now()

        recommendations = await personalization_engine.generate_personalized_recommendations(
            lead_id="recommendation_test",
            current_context={"recent_inquiry": "investment_properties"}
        )

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds() * 1000

        # Performance assertions
        assert processing_time < 150, f"Recommendation generation took {processing_time}ms (target: <150ms)"

        # Recommendation quality assertions
        assert len(recommendations) > 0
        assert all(isinstance(rec, PersonalizedRecommendation) for rec in recommendations)
        assert all(rec.confidence_score > 0.5 for rec in recommendations)

    @pytest.mark.asyncio
    async def test_communication_style_adaptation_performance(
        self,
        personalization_engine
    ):
        """Test communication style adaptation performance (<100ms target)"""
        # Create and cache a profile
        profile = PersonalizationProfile(
            lead_id="adaptation_test",
            personality_type=PersonalityType.DRIVER,
            personality_confidence=0.85,
            communication_style=CommunicationStyle.CONCISE_DIRECT,
            style_confidence=0.80,
            preferred_channels=[PersonalizationChannel.SMS],
            optimal_contact_times=[("Wednesday", 14)],
            message_complexity_preference=0.3,
            urgency_sensitivity=0.9,
            detail_preference=0.2,
            content_topics=["quick_decisions"],
            preferred_property_features=["location", "price"],
            visual_vs_text_preference=0.6,
            data_driven_preference=0.7,
            interaction_patterns={},
            response_triggers=["urgency"],
            objection_patterns=[],
            decision_making_factors=["quick_decision"],
            primary_language="en",
            cultural_considerations=[],
            formality_level=0.4,
            industry_vertical=IndustryVertical.RESIDENTIAL,
            specialization_confidence=0.7,
            vertical_specific_preferences={},
            profile_created=datetime.now(),
            last_updated=datetime.now(),
            profile_version="5.1.0",
            accuracy_metrics={"overall_accuracy": 0.90}
        )

        personalization_engine.profile_cache["adaptation_test"] = profile

        original_message = "I would be delighted to provide you with comprehensive property information and detailed market analysis at your convenience."

        start_time = datetime.now()

        adaptation = await personalization_engine.adapt_communication_style(
            original_message=original_message,
            lead_id="adaptation_test",
            target_channel=PersonalizationChannel.SMS
        )

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds() * 1000

        # Performance assertions
        assert processing_time < 100, f"Communication adaptation took {processing_time}ms (target: <100ms)"

        # Adaptation quality assertions
        assert isinstance(adaptation, CommunicationAdaptation)
        assert adaptation.adapted_message != adaptation.original_message
        assert adaptation.adaptation_confidence > 0.8
        assert adaptation.style_match_score > 0.8

        # Driver personality should get concise, direct message
        assert len(adaptation.adapted_message) < len(adaptation.original_message)

    @pytest.mark.asyncio
    async def test_formal_to_casual_adaptation(
        self,
        personalization_engine
    ):
        """Test formal to casual communication adaptation"""
        # Create casual/expressive profile
        profile = PersonalizationProfile(
            lead_id="casual_test",
            personality_type=PersonalityType.EXPRESSIVE,
            personality_confidence=0.80,
            communication_style=CommunicationStyle.CASUAL_FRIENDLY,
            style_confidence=0.85,
            preferred_channels=[PersonalizationChannel.WHATSAPP],
            optimal_contact_times=[("Friday", 19)],
            message_complexity_preference=0.4,
            urgency_sensitivity=0.6,
            detail_preference=0.5,
            content_topics=["lifestyle", "community"],
            preferred_property_features=["amenities", "neighborhood"],
            visual_vs_text_preference=0.8,
            data_driven_preference=0.3,
            interaction_patterns={},
            response_triggers=["enthusiasm"],
            objection_patterns=[],
            decision_making_factors=["lifestyle_factors"],
            primary_language="en",
            cultural_considerations=[],
            formality_level=0.2,
            industry_vertical=IndustryVertical.RESIDENTIAL,
            specialization_confidence=0.8,
            vertical_specific_preferences={},
            profile_created=datetime.now(),
            last_updated=datetime.now(),
            profile_version="5.1.0",
            accuracy_metrics={"overall_accuracy": 0.88}
        )

        personalization_engine.profile_cache["casual_test"] = profile

        formal_message = "Dear Valued Client, I would like to respectfully inform you that we have identified several properties that may be suitable for your consideration."

        adaptation = await personalization_engine.adapt_communication_style(
            original_message=formal_message,
            lead_id="casual_test"
        )

        # Should become more casual and friendly
        adapted_lower = adaptation.adapted_message.lower()
        assert "dear valued client" not in adapted_lower or "hi" in adapted_lower
        assert adaptation.tone_adjustments.get("formality") == "decreased"
        assert "excited" in adaptation.adapted_message.lower() or "love" in adaptation.adapted_message.lower()

    @pytest.mark.asyncio
    async def test_technical_detail_adaptation(
        self,
        personalization_engine
    ):
        """Test technical detail adaptation for analytical personalities"""
        # Create technical/analytical profile
        profile = PersonalizationProfile(
            lead_id="technical_test",
            personality_type=PersonalityType.TECHNICAL,
            personality_confidence=0.90,
            communication_style=CommunicationStyle.TECHNICAL_DETAILED,
            style_confidence=0.88,
            preferred_channels=[PersonalizationChannel.EMAIL],
            optimal_contact_times=[("Tuesday", 10)],
            message_complexity_preference=0.9,
            urgency_sensitivity=0.3,
            detail_preference=0.95,
            content_topics=["specifications", "technical_analysis"],
            preferred_property_features=["square_footage", "technical_specs"],
            visual_vs_text_preference=0.3,
            data_driven_preference=0.95,
            interaction_patterns={},
            response_triggers=["specifications"],
            objection_patterns=[],
            decision_making_factors=["technical_requirements"],
            primary_language="en",
            cultural_considerations=[],
            formality_level=0.8,
            industry_vertical=IndustryVertical.COMMERCIAL,
            specialization_confidence=0.85,
            vertical_specific_preferences={},
            profile_created=datetime.now(),
            last_updated=datetime.now(),
            profile_version="5.1.0",
            accuracy_metrics={"overall_accuracy": 0.94}
        )

        personalization_engine.profile_cache["technical_test"] = profile

        basic_message = "Here are some properties you might like."

        adaptation = await personalization_engine.adapt_communication_style(
            original_message=basic_message,
            lead_id="technical_test"
        )

        # Should add technical details
        adapted_lower = adaptation.adapted_message.lower()
        assert ("specifications" in adapted_lower or
                "technical" in adapted_lower or
                "detailed" in adapted_lower or
                "square footage" in adapted_lower)

    @pytest.mark.asyncio
    async def test_multi_language_support(
        self,
        personalization_engine
    ):
        """Test multi-language communication adaptation"""
        profile = PersonalizationProfile(
            lead_id="spanish_test",
            personality_type=PersonalityType.AMIABLE,
            personality_confidence=0.75,
            communication_style=CommunicationStyle.FORMAL_PROFESSIONAL,
            style_confidence=0.80,
            preferred_channels=[PersonalizationChannel.EMAIL],
            optimal_contact_times=[("Monday", 9)],
            message_complexity_preference=0.6,
            urgency_sensitivity=0.4,
            detail_preference=0.7,
            content_topics=["family_considerations"],
            preferred_property_features=["schools", "neighborhood"],
            visual_vs_text_preference=0.5,
            data_driven_preference=0.5,
            interaction_patterns={},
            response_triggers=["family"],
            objection_patterns=[],
            decision_making_factors=["family_considerations"],
            primary_language="es",
            cultural_considerations=["formal_address", "family_considerations"],
            formality_level=0.8,
            industry_vertical=IndustryVertical.RESIDENTIAL,
            specialization_confidence=0.7,
            vertical_specific_preferences={},
            profile_created=datetime.now(),
            last_updated=datetime.now(),
            profile_version="5.1.0",
            accuracy_metrics={"overall_accuracy": 0.87}
        )

        personalization_engine.profile_cache["spanish_test"] = profile

        message = "Hello, I have some properties to show you."

        adaptation = await personalization_engine.adapt_communication_style(
            original_message=message,
            lead_id="spanish_test"
        )

        # Should adapt for Spanish cultural considerations
        adapted_message = adaptation.adapted_message
        assert ("estimado" in adapted_message.lower() or
                "dear client" in adapted_message.lower() or
                adaptation.additional_context)

    @pytest.mark.asyncio
    async def test_channel_specific_adaptation(
        self,
        personalization_engine
    ):
        """Test channel-specific message adaptation"""
        profile = PersonalizationProfile(
            lead_id="channel_test",
            personality_type=PersonalityType.DRIVER,
            personality_confidence=0.80,
            communication_style=CommunicationStyle.CONCISE_DIRECT,
            style_confidence=0.85,
            preferred_channels=[PersonalizationChannel.SMS],
            optimal_contact_times=[("Wednesday", 15)],
            message_complexity_preference=0.3,
            urgency_sensitivity=0.8,
            detail_preference=0.3,
            content_topics=["quick_decisions"],
            preferred_property_features=["price", "location"],
            visual_vs_text_preference=0.6,
            data_driven_preference=0.7,
            interaction_patterns={},
            response_triggers=["quick"],
            objection_patterns=[],
            decision_making_factors=["quick_decision"],
            primary_language="en",
            cultural_considerations=[],
            formality_level=0.3,
            industry_vertical=IndustryVertical.RESIDENTIAL,
            specialization_confidence=0.8,
            vertical_specific_preferences={},
            profile_created=datetime.now(),
            last_updated=datetime.now(),
            profile_version="5.1.0",
            accuracy_metrics={"overall_accuracy": 0.89}
        )

        personalization_engine.profile_cache["channel_test"] = profile

        long_message = "I wanted to take this opportunity to reach out and provide you with comprehensive information about several exceptional properties that have recently become available in your area of interest. These properties feature numerous amenities and benefits that I believe would be perfectly suited to your specific requirements and preferences."

        # Test SMS adaptation (should truncate)
        sms_adaptation = await personalization_engine.adapt_communication_style(
            original_message=long_message,
            lead_id="channel_test",
            target_channel=PersonalizationChannel.SMS
        )

        assert len(sms_adaptation.adapted_message) <= 160  # SMS length limit

        # Test WhatsApp adaptation (should add emoji)
        whatsapp_adaptation = await personalization_engine.adapt_communication_style(
            original_message="Here are some great properties",
            lead_id="channel_test",
            target_channel=PersonalizationChannel.WHATSAPP
        )

        assert "🏠" in whatsapp_adaptation.adapted_message

    @pytest.mark.asyncio
    async def test_recommendation_types_generation(
        self,
        personalization_engine
    ):
        """Test generation of different recommendation types"""
        profile = PersonalizationProfile(
            lead_id="rec_types_test",
            personality_type=PersonalityType.ANALYTICAL,
            personality_confidence=0.85,
            communication_style=CommunicationStyle.CONSULTATIVE,
            style_confidence=0.80,
            preferred_channels=[PersonalizationChannel.EMAIL],
            optimal_contact_times=[("Tuesday", 14)],
            message_complexity_preference=0.7,
            urgency_sensitivity=0.4,
            detail_preference=0.8,
            content_topics=["market_analysis", "investment_potential"],
            preferred_property_features=["location", "roi"],
            visual_vs_text_preference=0.5,
            data_driven_preference=0.9,
            interaction_patterns={},
            response_triggers=["data"],
            objection_patterns=["price_concerns"],
            decision_making_factors=["investment_potential"],
            primary_language="en",
            cultural_considerations=[],
            formality_level=0.6,
            industry_vertical=IndustryVertical.INVESTMENT,
            specialization_confidence=0.9,
            vertical_specific_preferences={},
            profile_created=datetime.now(),
            last_updated=datetime.now(),
            profile_version="5.1.0",
            accuracy_metrics={"overall_accuracy": 0.93}
        )

        personalization_engine.profile_cache["rec_types_test"] = profile

        recommendation_types = [
            'next_message',
            'property_suggestion',
            'engagement_strategy',
            'objection_handling',
            'follow_up_timing'
        ]

        recommendations = await personalization_engine.generate_personalized_recommendations(
            lead_id="rec_types_test",
            current_context={"stage": "consideration"},
            recommendation_types=recommendation_types
        )

        # Should generate recommendations for each type
        rec_types_generated = [rec.recommendation_type for rec in recommendations]

        assert 'next_message' in rec_types_generated
        assert 'property_suggestion' in rec_types_generated
        assert 'objection_handling' in rec_types_generated  # Has objection patterns

        # Check recommendation quality
        for rec in recommendations:
            assert rec.confidence_score > 0.6
            assert rec.expected_response_probability > 0.6
            assert len(rec.personalization_factors) > 0

    @pytest.mark.asyncio
    async def test_cache_performance_optimization(
        self,
        personalization_engine,
        sample_conversation_history,
        sample_behavioral_data,
        sample_property_interactions
    ):
        """Test caching improves performance for repeated requests"""
        lead_id = "cache_test_lead"

        # First request (should cache)
        start_time1 = datetime.now()
        profile1 = await personalization_engine.create_personalized_profile(
            lead_id=lead_id,
            conversation_history=sample_conversation_history,
            behavioral_data=sample_behavioral_data,
            property_interactions=sample_property_interactions
        )
        time1 = (datetime.now() - start_time1).total_seconds() * 1000

        # Second request (should use cache)
        start_time2 = datetime.now()
        profile2 = await personalization_engine.create_personalized_profile(
            lead_id=lead_id,
            conversation_history=sample_conversation_history,
            behavioral_data=sample_behavioral_data,
            property_interactions=sample_property_interactions
        )
        time2 = (datetime.now() - start_time2).total_seconds() * 1000

        # Cache should make second request much faster
        assert time2 < time1 * 0.5, f"Cached request ({time2}ms) not significantly faster than first ({time1}ms)"
        assert profile1.lead_id == profile2.lead_id
        assert profile1.personality_type == profile2.personality_type

    @pytest.mark.asyncio
    async def test_profile_accuracy_calculation(
        self,
        personalization_engine,
        sample_conversation_history,
        sample_behavioral_data,
        sample_property_interactions
    ):
        """Test profile accuracy calculation meets targets"""
        profile = await personalization_engine.create_personalized_profile(
            lead_id="accuracy_calc_test",
            conversation_history=sample_conversation_history,
            behavioral_data=sample_behavioral_data,
            property_interactions=sample_property_interactions
        )

        accuracy_metrics = profile.accuracy_metrics

        # Check all accuracy components
        assert "overall_accuracy" in accuracy_metrics
        assert "personality_confidence" in accuracy_metrics
        assert "style_confidence" in accuracy_metrics
        assert "data_completeness" in accuracy_metrics

        # Overall accuracy should meet target
        overall_accuracy = accuracy_metrics["overall_accuracy"]
        assert overall_accuracy >= 0.75, f"Overall accuracy {overall_accuracy} below minimum threshold"

        # Data completeness should reflect conversation length
        data_completeness = accuracy_metrics["data_completeness"]
        expected_completeness = min(1.0, len(sample_conversation_history) / 10)
        assert abs(data_completeness - expected_completeness) < 0.1

    @pytest.mark.asyncio
    async def test_error_handling_and_fallbacks(
        self,
        personalization_engine
    ):
        """Test error handling and fallback behavior"""
        # Test with minimal data
        minimal_profile = await personalization_engine.create_personalized_profile(
            lead_id="minimal_data_test",
            conversation_history=[],
            behavioral_data={},
            property_interactions=[]
        )

        # Should create fallback profile
        assert minimal_profile.lead_id == "minimal_data_test"
        assert minimal_profile.personality_type == PersonalityType.AMIABLE  # Default
        assert minimal_profile.communication_style == CommunicationStyle.CONSULTATIVE  # Default
        assert "fallback" in minimal_profile.profile_version

        # Test adaptation with non-existent lead
        adaptation = await personalization_engine.adapt_communication_style(
            original_message="Test message",
            lead_id="non_existent_lead"
        )

        # Should return original message with low confidence
        assert adaptation.adapted_message == "Test message"
        assert adaptation.adaptation_confidence == 0.5
        assert "no_profile" in adaptation.adaptation_factors

    @pytest.mark.asyncio
    async def test_mobile_optimization_compatibility(
        self,
        personalization_engine
    ):
        """Test mobile optimization features"""
        # Test mobile-optimized profile creation
        mobile_behavioral_data = {
            "engagement_score": 0.8,
            "mobile_usage_ratio": 0.9,  # High mobile usage
            "avg_session_duration": 3.0,  # Shorter mobile sessions
            "touch_interactions": 150,
            "scroll_depth": 0.75
        }

        profile = await personalization_engine.create_personalized_profile(
            lead_id="mobile_test",
            conversation_history=[{"content": "Quick property search", "timestamp": datetime.now()}],
            behavioral_data=mobile_behavioral_data,
            property_interactions=[]
        )

        # High mobile usage should prefer mobile-friendly channels
        assert (PersonalizationChannel.SMS in profile.preferred_channels or
                PersonalizationChannel.WHATSAPP in profile.preferred_channels)

        # Should adapt for shorter attention spans
        assert profile.message_complexity_preference <= 0.6

    @pytest.mark.asyncio
    async def test_industry_vertical_specialization(
        self,
        personalization_engine
    ):
        """Test industry vertical specialization patterns"""
        # Test luxury vertical
        luxury_conversation = [
            {"content": "Looking for exclusive luxury properties", "timestamp": datetime.now()}
        ]
        luxury_interactions = [
            {"property_type": "luxury_estate", "price": 3000000, "features_viewed": ["luxury", "exclusive"]}
        ]

        luxury_profile = await personalization_engine.create_personalized_profile(
            lead_id="luxury_vertical_test",
            conversation_history=luxury_conversation,
            behavioral_data={"engagement_score": 0.9},
            property_interactions=luxury_interactions
        )

        assert luxury_profile.industry_vertical == IndustryVertical.LUXURY
        assert luxury_profile.vertical_specific_preferences.get("exclusivity_preference", 0) > 0.7

        # Test commercial vertical
        commercial_conversation = [
            {"content": "Need office space for business expansion", "timestamp": datetime.now()}
        ]
        commercial_interactions = [
            {"property_type": "office_building", "price": 1500000, "features_viewed": ["location", "business"]}
        ]

        commercial_profile = await personalization_engine.create_personalized_profile(
            lead_id="commercial_vertical_test",
            conversation_history=commercial_conversation,
            behavioral_data={"engagement_score": 0.8},
            property_interactions=commercial_interactions
        )

        assert commercial_profile.industry_vertical == IndustryVertical.COMMERCIAL
        assert commercial_profile.vertical_specific_preferences.get("roi_focus", 0) > 0.8

    @pytest.mark.asyncio
    async def test_personalization_metrics(
        self,
        personalization_engine
    ):
        """Test personalization performance metrics collection"""
        metrics = await personalization_engine.get_personalization_metrics()

        # Check core metrics structure
        assert "model_status" in metrics
        assert "performance_targets" in metrics
        assert "cache_status" in metrics
        assert "language_support" in metrics
        assert "feature_capabilities" in metrics

        # Check performance targets
        performance_targets = metrics["performance_targets"]
        assert performance_targets["profile_generation_ms"] == 200
        assert performance_targets["recommendation_latency_ms"] == 150
        assert performance_targets["personalization_accuracy"] == 0.92
        assert performance_targets["adaptation_latency_ms"] == 100

        # Check language support
        language_support = metrics["language_support"]
        assert "en" in language_support["supported_languages"]
        assert len(language_support["supported_languages"]) >= 6

        # Check feature capabilities
        capabilities = metrics["feature_capabilities"]
        assert len(capabilities["personality_types"]) == len(PersonalityType)
        assert len(capabilities["communication_styles"]) == len(CommunicationStyle)
        assert len(capabilities["industry_verticals"]) == len(IndustryVertical)


class TestPersonalizationIntegration:
    """Test integration with existing Phase 1-4 services"""

    @pytest.mark.asyncio
    async def test_behavioral_analyzer_integration(self):
        """Test integration with behavioral analyzer"""
        from ghl_real_estate_ai.services.claude.advanced.predictive_behavior_analyzer import (
            get_advanced_behavior_analyzer
        )

        # Get behavioral analyzer
        analyzer = await get_advanced_behavior_analyzer()

        # Get personalization engine
        personalization_engine = await get_advanced_personalization_engine()

        # Should integrate properly
        assert personalization_engine is not None
        assert analyzer is not None

    @pytest.mark.asyncio
    async def test_claude_semantic_analyzer_integration(self):
        """Test integration with Claude semantic analyzer"""
        personalization_engine = await get_advanced_personalization_engine()

        # Should have Claude analyzer integrated
        assert personalization_engine.claude_analyzer is not None
        assert hasattr(personalization_engine.claude_analyzer, 'analyze_lead_intent')

    def test_mobile_settings_integration(self):
        """Test integration with mobile performance settings"""
        from ghl_real_estate_ai.config.mobile.settings import MOBILE_PERFORMANCE_TARGETS

        personalization_engine = AdvancedPersonalizationEngine()

        # Should respect mobile performance targets
        assert personalization_engine.adaptation_latency_target <= MOBILE_PERFORMANCE_TARGETS.get("max_response_time", 200)

    @pytest.mark.asyncio
    async def test_global_instance_access(self):
        """Test global instance access pattern"""
        engine1 = await get_advanced_personalization_engine()
        engine2 = await get_advanced_personalization_engine()

        # Should return same instance
        assert engine1 is engine2
        assert id(engine1) == id(engine2)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])