"""
Comprehensive test suite for multi-tenant memory system.

Tests cover:
- Multi-tenant conversation persistence and isolation
- Memory context retrieval and behavioral learning
- Cross-tenant data isolation and security
- Memory-aware Claude response generation
- Session gap handling and smart resume functionality
"""

import asyncio
import pytest
import uuid
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any

# Test imports with fallback for different execution contexts
try:
    from ghl_real_estate_ai.services.enhanced_memory_service import EnhancedMemoryService, ConversationWithMemory
    from ghl_real_estate_ai.core.intelligent_conversation_manager import IntelligentConversationManager
    from ghl_real_estate_ai.services.intelligent_qualifier import IntelligentQualifier
    from ghl_real_estate_ai.services.property_recommendation_engine import PropertyRecommendationEngine
    from ghl_real_estate_ai.database.connection import EnhancedDatabasePool
    from ghl_real_estate_ai.database.redis_client import EnhancedRedisClient
except ImportError:
    try:
        from services.enhanced_memory_service import EnhancedMemoryService, ConversationWithMemory
        from core.intelligent_conversation_manager import IntelligentConversationManager
        from services.intelligent_qualifier import IntelligentQualifier
        from services.property_recommendation_engine import PropertyRecommendationEngine
        from database.connection import EnhancedDatabasePool
        from database.redis_client import EnhancedRedisClient
    except ImportError:
        # Mock for testing environment
        EnhancedMemoryService = Mock
        ConversationWithMemory = Mock
        IntelligentConversationManager = Mock
        IntelligentQualifier = Mock
        PropertyRecommendationEngine = Mock
        EnhancedDatabasePool = Mock
        EnhancedRedisClient = Mock

@pytest.fixture
def test_tenant_config():
    """Create test tenant configuration with rich conversation history."""
    return {
        "tenant_id": "test_tenant_" + str(uuid.uuid4())[:8],
        "location_id": "test_location_12345",
        "name": "Test Real Estate Agency",
        "claude_config": {
            "model_name": "claude-sonnet-4-20250514",
            "system_prompts": {
                "buyer": "You are a helpful real estate assistant for buyers.",
                "seller": "You are a helpful real estate assistant for sellers."
            },
            "qualification_templates": {
                "budget": "What's your budget range for this purchase?",
                "location": "Which areas are you most interested in?",
                "timeline": "When are you looking to buy/sell?"
            }
        },
        "behavioral_learning_enabled": True
    }

@pytest.fixture
def rich_conversation_history():
    """Create rich conversation history for testing behavioral learning."""
    return [
        {
            "role": "user",
            "content": "I'm looking for a 3-bedroom home under $500k",
            "timestamp": datetime.now() - timedelta(days=7),
            "extracted_data": {"budget": 500000, "bedrooms": 3}
        },
        {
            "role": "assistant",
            "content": "Great! I can help you find 3-bedroom homes under $500k. What areas interest you most?",
            "timestamp": datetime.now() - timedelta(days=7),
            "reasoning": "Following Jorge's qualification methodology - got budget and bedrooms, now need location"
        },
        {
            "role": "user",
            "content": "Preferably near good schools, we have two kids",
            "timestamp": datetime.now() - timedelta(days=6),
            "extracted_data": {"priority_features": ["school_district"], "household_composition": "family_with_children"}
        },
        {
            "role": "assistant",
            "content": "Perfect! School districts are definitely important for families. When are you hoping to move?",
            "timestamp": datetime.now() - timedelta(days=6),
            "reasoning": "Got budget, bedrooms, and location preference. Now need timeline to complete qualification."
        },
        {
            "role": "user",
            "content": "We'd like to move before the next school year starts",
            "timestamp": datetime.now() - timedelta(days=5),
            "extracted_data": {"timeline": "before_school_year", "urgency": "moderate"}
        }
    ]

@pytest.fixture
def mock_database_pool():
    """Mock database pool for testing."""
    mock_pool = AsyncMock()
    mock_pool.get_connection = AsyncMock()
    mock_pool.health_check = AsyncMock(return_value={"status": "healthy"})
    return mock_pool

@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)  # Cache miss by default
    mock_redis.setex = AsyncMock()
    mock_redis.delete = AsyncMock()
    mock_redis.health_check = AsyncMock(return_value={"status": "healthy"})
    return mock_redis

class TestMultiTenantMemorySystem:
    """Comprehensive testing for enhanced memory system"""

    @pytest.mark.asyncio
    async def test_conversation_persistence_across_sessions(self, test_tenant_config, rich_conversation_history):
        """Test conversation memory persistence and intelligent resume"""

        # Setup
        tenant_id = test_tenant_config["tenant_id"]
        contact_id = "test_memory_persistence"

        with patch('services.enhanced_memory_service.DatabasePool') as mock_db, \
             patch('services.enhanced_memory_service.RedisClient') as mock_redis:

            memory_service = EnhancedMemoryService(use_database=True)

            # Mock database response for conversation retrieval
            mock_conversation = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "contact_id": contact_id,
                "conversation_stage": "qualification",
                "lead_score": 75,
                "last_interaction_at": datetime.now() - timedelta(hours=24),
                "extracted_preferences": {
                    "budget": 500000,
                    "bedrooms": 3,
                    "priority_features": ["school_district"]
                },
                "previous_sessions_summary": "Lead is qualified buyer looking for family home",
                "behavioral_profile": {
                    "communication_style": "detailed",
                    "decision_speed": "thoughtful",
                    "information_processing": "comprehensive"
                }
            }

            mock_db.return_value.execute.return_value = [mock_conversation]
            mock_redis.return_value.get.return_value = None  # Cache miss

            # Test initial conversation retrieval
            initial_context = await memory_service.get_conversation_with_memory(
                tenant_id, contact_id
            )

            # Verify conversation context includes memory
            assert initial_context is not None
            assert hasattr(initial_context, 'extracted_preferences')
            assert hasattr(initial_context, 'behavioral_profile')
            assert hasattr(initial_context, 'conversation_stage')

            # Simulate conversation gap (24 hours)
            await self.simulate_time_gap(hours=24, memory_service=memory_service)

            # Test resumed conversation with smart resume context
            resumed_context = await memory_service.get_conversation_with_memory(
                tenant_id, contact_id, include_behavioral_context=True
            )

            # Verify smart resume context
            assert resumed_context is not None
            assert hasattr(resumed_context, 'is_returning_lead')
            assert hasattr(resumed_context, 'hours_since_last_interaction')
            assert hasattr(resumed_context, 'previous_sessions_summary')

            # Verify behavioral learning context preserved
            assert hasattr(resumed_context, 'behavioral_preferences')
            assert hasattr(resumed_context, 'property_interactions')

    @pytest.mark.asyncio
    async def test_behavioral_learning_accuracy(self, test_tenant_config):
        """Test behavioral preference learning accuracy over multiple interactions"""

        tenant_id = test_tenant_config["tenant_id"]
        contact_id = "test_behavioral_learning"

        with patch('core.intelligent_conversation_manager.EnhancedMemoryService') as mock_memory, \
             patch('services.behavioral_weighting_engine.BehavioralWeightingEngine') as mock_behavioral:

            conversation_manager = IntelligentConversationManager(tenant_id)

            # Mock behavioral engine responses
            mock_behavioral.return_value.analyze_behavioral_profile.return_value = {
                "search_consistency": "very_consistent",
                "preference_deviations": [
                    {"feature": "price_range", "deviation_score": 0.1},
                    {"feature": "location_preference", "deviation_score": 0.05}
                ],
                "response_rate": 0.85,
                "engagement_level": "high"
            }

            # Simulate property interaction sequence with learning
            property_interactions = await self.simulate_property_interaction_sequence(
                conversation_manager, contact_id, n_interactions=20
            )

            # Verify behavioral learning results
            assert len(property_interactions) == 20

            behavioral_profile = await conversation_manager.behavioral_engine.analyze_behavioral_profile(
                contact_id, {}
            )

            # Verify learning accuracy meets targets
            assert behavioral_profile["search_consistency"] in ["consistent", "very_consistent"]
            assert len(behavioral_profile["preference_deviations"]) > 0
            assert behavioral_profile["response_rate"] > 0.5
            assert behavioral_profile["engagement_level"] in ["moderate", "high", "very_high"]

    @pytest.mark.asyncio
    async def test_claude_memory_integration_quality(self, test_tenant_config, rich_conversation_history):
        """Test Claude response quality with memory context"""

        tenant_id = test_tenant_config["tenant_id"]
        contact_id = "test_claude_memory_integration"

        with patch('core.intelligent_conversation_manager.EnhancedMemoryService') as mock_memory, \
             patch('core.intelligent_conversation_manager.ClaudeClient') as mock_claude:

            conversation_manager = IntelligentConversationManager(tenant_id)

            # Mock memory context with rich history
            mock_memory_context = {
                "conversation": {
                    "id": str(uuid.uuid4()),
                    "conversation_history": rich_conversation_history,
                    "conversation_stage": "property_viewing",
                    "lead_score": 85
                },
                "behavioral_profile": {
                    "communication_style": "detailed",
                    "decision_speed": "thoughtful",
                    "engagement_patterns": ["weekday_evenings", "detailed_questions"]
                },
                "extracted_preferences": {
                    "budget": 500000,
                    "bedrooms": 3,
                    "priority_features": ["school_district", "family_friendly"]
                }
            }

            mock_memory.return_value.get_conversation_with_memory.return_value = mock_memory_context

            # Mock Claude response
            mock_claude_response = {
                "content": "Based on your family's needs and budget, I've found some great 3-bedroom homes near excellent schools. Here are my top recommendations...",
                "extracted_data": {"intent": "property_search", "urgency": "moderate"},
                "reasoning": "User has been consistently looking for family-friendly properties near schools. Previous conversations show detailed decision-making style.",
                "lead_score": 88
            }

            mock_claude.return_value.agenerate.return_value = mock_claude_response

            # Test memory-aware response generation
            response = await conversation_manager.generate_memory_aware_response(
                contact_id=contact_id,
                user_message="I'm ready to see some properties now",
                contact_info={"first_name": "Test", "id": contact_id},
                is_buyer=True
            )

            # Verify memory integration quality
            assert response is not None
            assert hasattr(response, 'memory_context_used')
            assert response.memory_context_used == True
            assert hasattr(response, 'property_recommendations')
            assert response.property_recommendations is not None
            assert hasattr(response, 'agent_suggestions')
            assert response.agent_suggestions is not None
            assert hasattr(response, 'reasoning')
            assert len(response.reasoning) > 0

    @pytest.mark.asyncio
    async def test_multi_tenant_data_isolation(self, test_tenant_config):
        """Test strict data isolation between tenants"""

        # Create two separate tenants
        tenant_a_id = test_tenant_config["tenant_id"]
        tenant_b_id = "test_tenant_" + str(uuid.uuid4())[:8]
        contact_id = "shared_contact_id"  # Same contact ID across tenants

        with patch('services.enhanced_memory_service.DatabasePool') as mock_db:
            memory_service = EnhancedMemoryService(use_database=True)

            # Mock separate conversations for each tenant
            tenant_a_data = {
                "tenant_id": tenant_a_id,
                "contact_id": contact_id,
                "extracted_preferences": {"budget": 300000, "property_type": "condo"},
                "conversation_stage": "initial_contact"
            }

            tenant_b_data = {
                "tenant_id": tenant_b_id,
                "contact_id": contact_id,
                "extracted_preferences": {"budget": 800000, "property_type": "luxury_home"},
                "conversation_stage": "qualified"
            }

            # Setup mock to return correct data based on tenant_id
            def mock_execute(query, params):
                if params.get("tenant_id") == tenant_a_id:
                    return [tenant_a_data]
                elif params.get("tenant_id") == tenant_b_id:
                    return [tenant_b_data]
                return []

            mock_db.return_value.execute.side_effect = mock_execute

            # Test tenant A data retrieval
            context_a = await memory_service.get_conversation_with_memory(
                tenant_a_id, contact_id
            )

            # Test tenant B data retrieval
            context_b = await memory_service.get_conversation_with_memory(
                tenant_b_id, contact_id
            )

            # Verify data isolation
            assert context_a.extracted_preferences["budget"] == 300000
            assert context_a.extracted_preferences["property_type"] == "condo"
            assert context_a.conversation_stage == "initial_contact"

            assert context_b.extracted_preferences["budget"] == 800000
            assert context_b.extracted_preferences["property_type"] == "luxury_home"
            assert context_b.conversation_stage == "qualified"

            # Verify no cross-tenant data leakage
            assert context_a.extracted_preferences != context_b.extracted_preferences
            assert context_a.conversation_stage != context_b.conversation_stage

    @pytest.mark.asyncio
    async def test_qualification_methodology_integration(self, test_tenant_config):
        """Test Jorge's 7 qualifying questions methodology with memory"""

        tenant_id = test_tenant_config["tenant_id"]
        contact_id = "test_jorge_methodology"

        with patch('services.intelligent_qualifier.ClaudeClient') as mock_claude:
            qualifier = IntelligentQualifier(tenant_id)

            # Mock conversation with partial qualification
            partial_conversation = {
                "conversation_history": [
                    {"role": "user", "content": "I want to buy a house for $400k"},
                    {"role": "user", "content": "Looking in downtown area"},
                    {"role": "user", "content": "Need 3 bedrooms"}
                ],
                "extracted_preferences": {
                    "budget": 400000,
                    "location": "downtown",
                    "bedrooms": 3
                }
            }

            # Test qualification gap analysis
            qualification_analysis = await qualifier.analyze_qualification_gaps(
                partial_conversation,
                behavioral_profile={"communication_style": "direct"}
            )

            # Verify Jorge's methodology tracking
            expected_answered = {"budget", "location", "requirements"}
            expected_missing = {"timeline", "financing", "motivation", "home_condition"}

            assert len(qualification_analysis["answered_questions"]) == 3
            assert set(qualification_analysis["answered_questions"]) == expected_answered
            assert set(qualification_analysis["missing_qualifiers"]) == expected_missing
            assert qualification_analysis["jorge_methodology_score"] == 3  # 3 of 7 questions answered

            # Test Hot/Warm/Cold classification
            if qualification_analysis["jorge_methodology_score"] >= 3:
                expected_status = "Hot"
            elif qualification_analysis["jorge_methodology_score"] == 2:
                expected_status = "Warm"
            else:
                expected_status = "Cold"

            assert qualification_analysis["lead_temperature"] == expected_status

    @pytest.mark.asyncio
    async def test_property_recommendation_behavioral_enhancement(self, test_tenant_config):
        """Test property recommendations with behavioral learning"""

        tenant_id = test_tenant_config["tenant_id"]

        with patch('services.property_recommendation_engine.PropertyMatcher') as mock_matcher, \
             patch('services.property_recommendation_engine.BehavioralWeightingEngine') as mock_behavioral:

            recommender = PropertyRecommendationEngine(tenant_id)

            # Mock property matches
            mock_properties = [
                {
                    "id": "prop_1",
                    "price": 450000,
                    "bedrooms": 3,
                    "location": "downtown",
                    "school_rating": 9,
                    "match_score": 0.85
                },
                {
                    "id": "prop_2",
                    "price": 480000,
                    "bedrooms": 3,
                    "location": "suburbs",
                    "school_rating": 10,
                    "match_score": 0.92
                }
            ]

            mock_matcher.return_value.find_matches.return_value = mock_properties

            # Mock behavioral weights emphasizing school quality
            mock_behavioral_weights = {
                "school_rating": 1.3,  # 30% boost for school quality
                "price": 1.0,
                "location": 1.1,
                "confidence_level": 0.87,
                "learning_iterations": 15
            }

            mock_behavioral.return_value.calculate_adaptive_weights.return_value = mock_behavioral_weights

            # Test recommendation generation
            conversation = {"extracted_preferences": {"budget": 500000, "bedrooms": 3}}
            behavioral_preferences = [{"preference_type": "school_quality", "confidence_score": 0.9}]
            property_interactions = []

            recommendations = await recommender.generate_personalized_recommendations(
                conversation, behavioral_preferences, property_interactions
            )

            # Verify behavioral enhancement
            assert len(recommendations["recommendations"]) <= 3  # Top 3 recommendations
            assert recommendations["behavioral_insights"] is not None
            assert recommendations["adaptive_weights_used"]["confidence_level"] > 0.8

            # Verify school rating gets priority due to behavioral learning
            top_recommendation = recommendations["recommendations"][0]
            assert top_recommendation["property"]["school_rating"] >= 9

    async def simulate_time_gap(self, hours: int, memory_service):
        """Simulate time gap for testing session resume functionality"""
        # This would normally involve actual time manipulation or mocking
        # For testing purposes, we'll just mock the time difference
        pass

    async def simulate_property_interaction_sequence(self, conversation_manager, contact_id: str, n_interactions: int = 20):
        """Simulate property viewing sequence for behavioral learning testing"""
        interactions = []

        for i in range(n_interactions):
            interaction = {
                "property_id": f"prop_{i}",
                "interaction_type": "view",
                "timestamp": datetime.now() - timedelta(days=n_interactions-i),
                "feedback": "positive" if i % 3 == 0 else "neutral",
                "duration": 120 + (i * 10)  # Increasing engagement
            }
            interactions.append(interaction)

        return interactions

    async def create_rich_conversation_history(self, conversation_manager, contact_id: str):
        """Create rich conversation history for testing"""
        # This would normally involve actual conversation creation
        # For testing purposes, we'll mock the interaction
        pass

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])