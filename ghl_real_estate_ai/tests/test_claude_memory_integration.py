"""
Claude memory integration tests for multi-tenant system.

Tests cover:
- Claude API integration with memory context
- Adaptive system prompt generation based on behavioral learning
- Memory-aware response quality and relevance
- Cross-tenant Claude configuration isolation
- Intelligent qualification flow with Claude
- Property recommendation explanations
- Agent assistance and coaching integration
"""

import asyncio
import pytest
import uuid
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, List, Any

# Test imports with fallback for different execution contexts
try:
    from ghl_real_estate_ai.core.intelligent_conversation_manager import IntelligentConversationManager, EnhancedAIResponse
    from ghl_real_estate_ai.services.intelligent_qualifier import IntelligentQualifier, QualificationAnalysis
    from ghl_real_estate_ai.services.property_recommendation_engine import PropertyRecommendationEngine, PersonalizedRecommendations
    from ghl_real_estate_ai.services.agent_assistance_service import AgentAssistanceService
    from ghl_real_estate_ai.services.seller_insights_service import SellerInsightsService
except ImportError:
    try:
        from core.intelligent_conversation_manager import IntelligentConversationManager, EnhancedAIResponse
        from services.intelligent_qualifier import IntelligentQualifier, QualificationAnalysis
        from services.property_recommendation_engine import PropertyRecommendationEngine, PersonalizedRecommendations
        from services.agent_assistance_service import AgentAssistanceService
        from services.seller_insights_service import SellerInsightsService
    except ImportError:
        # Mock for testing environment
        IntelligentConversationManager = Mock
        EnhancedAIResponse = Mock
        IntelligentQualifier = Mock
        QualificationAnalysis = Mock
        PropertyRecommendationEngine = Mock
        PersonalizedRecommendations = Mock
        AgentAssistanceService = Mock
        SellerInsightsService = Mock

@pytest.fixture
def claude_client_mock():
    """Mock Claude client for testing"""
    mock_client = AsyncMock()
    mock_client.agenerate = AsyncMock()
    return mock_client

@pytest.fixture
def memory_context_rich():
    """Rich memory context for testing Claude integration"""
    return {
        "conversation": {
            "id": str(uuid.uuid4()),
            "conversation_history": [
                {
                    "role": "user",
                    "content": "I'm looking for a family home under $500k",
                    "timestamp": datetime.now() - timedelta(days=3),
                    "extracted_data": {"budget": 500000, "household_type": "family"}
                },
                {
                    "role": "assistant",
                    "content": "I understand you're looking for a family home. What areas interest you?",
                    "timestamp": datetime.now() - timedelta(days=3),
                    "reasoning": "Following Jorge's qualification - got budget, need location"
                },
                {
                    "role": "user",
                    "content": "Preferably near good schools, we have twin toddlers",
                    "timestamp": datetime.now() - timedelta(days=2),
                    "extracted_data": {"priority_features": ["school_district"], "children_ages": ["toddler", "toddler"]}
                }
            ],
            "conversation_stage": "qualification",
            "lead_score": 78,
            "extracted_preferences": {
                "budget": 500000,
                "household_type": "family_with_children",
                "priority_features": ["school_district", "safety", "family_friendly"],
                "bedrooms": 3,
                "bathrooms": 2
            }
        },
        "behavioral_profile": {
            "communication_style": "detailed",
            "decision_speed": "thoughtful",
            "information_processing": "comprehensive",
            "engagement_patterns": ["evening_responder", "weekend_browser"],
            "preference_consistency": 0.87,
            "response_rate": 0.92
        },
        "property_interactions": [
            {
                "property_id": "prop_123",
                "interaction_type": "view",
                "property_data": {
                    "price": 475000,
                    "bedrooms": 3,
                    "school_rating": 9,
                    "property_type": "single_family"
                },
                "feedback_category": "interested",
                "duration": 180,
                "timestamp": datetime.now() - timedelta(days=1)
            }
        ]
    }

@pytest.fixture
def tenant_claude_config():
    """Tenant-specific Claude configuration"""
    return {
        "model_name": "claude-sonnet-4-20250514",
        "api_key_encrypted": "encrypted_key_placeholder",
        "system_prompts": {
            "buyer": "You are an expert real estate assistant helping buyers find their perfect home.",
            "seller": "You are an expert real estate assistant helping sellers maximize their property value.",
            "qualification": "Focus on qualifying leads using Jorge's 7-question methodology."
        },
        "qualification_templates": {
            "budget": "What's your budget range for this purchase?",
            "location": "Which areas or neighborhoods interest you most?",
            "timeline": "When are you looking to make a purchase?",
            "requirements": "What are your must-have features in a home?",
            "financing": "Do you have pre-approval or need financing assistance?",
            "motivation": "What's motivating your move at this time?"
        },
        "temperature": 0.7,
        "max_tokens": 1000
    }

class TestClaudeMemoryIntegration:
    """Test Claude API integration with memory-aware context"""

    @pytest.mark.asyncio
    async def test_memory_aware_system_prompt_generation(self, memory_context_rich, tenant_claude_config):
        """Test adaptive system prompt generation based on memory context"""

        with patch('core.intelligent_conversation_manager.ClaudeClient') as mock_claude_class:
            mock_claude = AsyncMock()
            mock_claude_class.return_value = mock_claude

            conversation_manager = IntelligentConversationManager("test_tenant")

            # Test system prompt adaptation for buyer
            adaptive_prompt = await conversation_manager._build_memory_aware_system_prompt(
                memory_context_rich,
                qualification_analysis={
                    "answered_questions": ["budget", "requirements"],
                    "missing_qualifiers": ["timeline", "financing", "motivation"]
                },
                is_buyer=True
            )

            # Verify system prompt includes memory context
            assert "family_with_children" in adaptive_prompt
            assert "school_district" in adaptive_prompt
            assert "500000" in adaptive_prompt or "$500k" in adaptive_prompt
            assert "qualification" in adaptive_prompt.lower()
            assert "jorge" in adaptive_prompt.lower()

            # Verify behavioral adaptations
            assert "detailed" in adaptive_prompt or "comprehensive" in adaptive_prompt
            assert "thoughtful" in adaptive_prompt or "careful" in adaptive_prompt

    @pytest.mark.asyncio
    async def test_claude_response_with_memory_context(self, memory_context_rich, claude_client_mock):
        """Test Claude response generation with full memory context"""

        # Setup Claude response mock
        mock_response = {
            "content": "Based on your family's needs and your interest in excellent schools, I've found some great properties in districts with 8+ rated schools. Given your budget of $500k and preference for 3-bedroom homes, here are my recommendations...",
            "extracted_data": {
                "intent": "property_search",
                "urgency": "moderate",
                "lead_qualification_score": 85,
                "next_action": "property_recommendations"
            },
            "reasoning": "User has been consistently interested in school quality and family-friendly features. Previous interaction with prop_123 showed strong engagement with similar properties. Ready for specific recommendations.",
            "lead_score": 85
        }

        claude_client_mock.agenerate.return_value = mock_response

        with patch('core.intelligent_conversation_manager.EnhancedMemoryService') as mock_memory, \
             patch('core.intelligent_conversation_manager.PropertyRecommendationEngine') as mock_property_engine:

            mock_memory.return_value.get_conversation_with_memory.return_value = memory_context_rich

            mock_property_engine.return_value.generate_personalized_recommendations.return_value = {
                "recommendations": [
                    {
                        "property": {"id": "prop_456", "price": 485000, "school_rating": 9},
                        "explanation": "Perfect school district match",
                        "behavioral_confidence": 0.92
                    }
                ]
            }

            conversation_manager = IntelligentConversationManager("test_tenant")
            conversation_manager.claude_client = claude_client_mock

            # Generate memory-aware response
            response = await conversation_manager.generate_memory_aware_response(
                contact_id="test_contact",
                user_message="Can you show me some properties now?",
                contact_info={"first_name": "Sarah", "id": "test_contact"},
                is_buyer=True
            )

            # Verify memory context usage
            assert response.memory_context_used == True
            assert response.property_recommendations is not None
            assert response.lead_score >= 80
            assert "school" in response.message.lower()
            assert "family" in response.message.lower() or "children" in response.message.lower()

            # Verify Claude was called with memory-enhanced prompt
            claude_client_mock.agenerate.assert_called_once()
            call_kwargs = claude_client_mock.agenerate.call_args[1]
            assert "school_district" in call_kwargs.get("system_prompt", "")
            assert "family_with_children" in call_kwargs.get("system_prompt", "")

    @pytest.mark.asyncio
    async def test_intelligent_qualification_with_claude(self, claude_client_mock, tenant_claude_config):
        """Test intelligent qualification using Claude with behavioral adaptation"""

        # Mock Claude qualification analysis response
        mock_qualification_response = {
            "content": "Given Sarah's detailed communication style and the conversation flow, the most natural next question would be: 'When would you ideally like to be settled into your new home?'",
            "extracted_data": {
                "priority_qualifier": "timeline",
                "conversation_natural": True,
                "follow_up_strategy": "gentle_timeline_inquiry"
            },
            "reasoning": "User has provided budget, location preference, and requirements. Timeline is the logical next qualifier and fits naturally after discussing specific properties."
        }

        claude_client_mock.agenerate.return_value = mock_qualification_response

        # Test conversation with partial qualification
        conversation = {
            "conversation_history": [
                {"role": "user", "content": "I want a 3-bedroom home under $500k"},
                {"role": "user", "content": "Near good schools in the suburbs"}
            ],
            "extracted_preferences": {
                "budget": 500000,
                "bedrooms": 3,
                "location": "suburbs",
                "priority_features": ["school_district"]
            },
            "conversation_stage": "qualification"
        }

        behavioral_profile = {
            "communication_style": "detailed",
            "formality_level": "casual",
            "response_timing": "evening"
        }

        with patch('services.intelligent_qualifier.ClaudeClient') as mock_claude_class:
            mock_claude_class.return_value = claude_client_mock

            qualifier = IntelligentQualifier("test_tenant")

            # Test qualification gap analysis
            analysis = await qualifier.analyze_qualification_gaps(conversation, behavioral_profile)

            # Verify Jorge's methodology tracking
            assert "budget" in analysis["answered_questions"]
            assert "location" in analysis["answered_questions"]
            assert "requirements" in analysis["answered_questions"]
            assert "timeline" in analysis["missing_qualifiers"]
            assert analysis["jorge_methodology_score"] == 3

            # Test adaptive question crafting
            next_question = await qualifier.craft_next_question(
                "timeline",
                conversation_context={
                    "stage": "qualification",
                    "recent_messages": conversation["conversation_history"][-2:]
                },
                behavioral_style=behavioral_profile
            )

            assert "when" in next_question.lower() or "timeline" in next_question.lower()
            assert len(next_question) <= 160  # SMS-friendly length

    @pytest.mark.asyncio
    async def test_property_recommendations_with_claude_explanations(self, memory_context_rich, claude_client_mock):
        """Test property recommendations with Claude-generated explanations"""

        # Mock property recommendation with Claude explanation
        mock_property_explanation = {
            "content": "This property is perfect for your family because it's in the Riverside Elementary district (rated 9/10), has a large backyard for your toddlers, and the price of $485k fits comfortably within your $500k budget. The neighborhood is known for being very family-friendly with parks nearby.",
            "extracted_data": {
                "match_factors": ["school_rating", "family_friendly", "budget_fit", "outdoor_space"],
                "confidence_score": 0.94
            },
            "reasoning": "User consistently prioritizes school quality and family features. Property matches behavioral pattern from previous viewing of similar property."
        }

        claude_client_mock.agenerate.return_value = mock_property_explanation

        with patch('services.property_recommendation_engine.PropertyMatcher') as mock_matcher, \
             patch('services.property_recommendation_engine.BehavioralWeightingEngine') as mock_behavioral:

            # Mock property matches
            mock_properties = [
                {
                    "id": "prop_456",
                    "price": 485000,
                    "bedrooms": 3,
                    "bathrooms": 2,
                    "school_rating": 9,
                    "property_type": "single_family",
                    "features": ["backyard", "family_neighborhood"],
                    "match_score": 0.92
                }
            ]

            mock_matcher.return_value.find_matches.return_value = mock_properties
            mock_behavioral.return_value.calculate_adaptive_weights.return_value = {
                "school_rating": 1.4,  # 40% boost
                "family_friendly": 1.3,  # 30% boost
                "confidence_level": 0.91
            }

            recommender = PropertyRecommendationEngine("test_tenant")
            recommender.claude_client = claude_client_mock

            recommendations = await recommender.generate_personalized_recommendations(
                memory_context_rich["conversation"],
                memory_context_rich["behavioral_profile"],
                memory_context_rich["property_interactions"]
            )

            # Verify Claude explanation integration
            assert len(recommendations["recommendations"]) > 0
            top_rec = recommendations["recommendations"][0]
            assert top_rec["explanation"] is not None
            assert "school" in top_rec["explanation"].lower()
            assert "family" in top_rec["explanation"].lower()
            assert top_rec["behavioral_confidence"] > 0.9

    @pytest.mark.asyncio
    async def test_seller_insights_with_claude_analysis(self, claude_client_mock):
        """Test seller insights generation with Claude market analysis"""

        # Mock Claude seller analysis response
        mock_seller_response = {
            "content": "Based on current market conditions and your property details, I recommend the listing pathway. The market is strong for single-family homes in your area, with average days on market at 18 days. Your home's condition and features suggest an optimal listing price of $565k-$585k.",
            "extracted_data": {
                "recommended_pathway": "listing",
                "market_strength": "strong",
                "price_range": {"min": 565000, "max": 585000},
                "estimated_days_on_market": 18,
                "key_selling_points": ["location", "condition", "school_district"]
            },
            "reasoning": "Property condition is excellent, market timing is favorable, and comparable sales support strong pricing. Owner motivation suggests listing is preferable to wholesale."
        }

        claude_client_mock.agenerate.return_value = mock_seller_response

        seller_context = {
            "property_details": {
                "address": "123 Oak Street",
                "bedrooms": 4,
                "bathrooms": 3,
                "square_footage": 2200,
                "year_built": 2010,
                "condition": "excellent"
            },
            "seller_motivation": "job_relocation",
            "timeline": "3_months",
            "price_expectations": 580000
        }

        with patch('services.seller_insights_service.ClaudeClient') as mock_claude_class:
            mock_claude_class.return_value = claude_client_mock

            seller_service = SellerInsightsService("test_tenant")

            insights = await seller_service.generate_market_analysis(
                seller_context["property_details"],
                seller_context
            )

            # Verify Claude analysis integration
            assert insights is not None
            assert "listing" in insights.lower() or "market" in insights.lower()
            assert "565" in insights or "585" in insights  # Price range
            assert claude_client_mock.agenerate.called

    @pytest.mark.asyncio
    async def test_agent_assistance_with_claude_coaching(self, memory_context_rich, claude_client_mock):
        """Test agent assistance and coaching with Claude"""

        # Mock Claude agent coaching response
        mock_coaching_response = {
            "content": "This lead is highly qualified and engaged. Suggested approach: 1) Schedule property viewing for this weekend, 2) Prepare school district information packets, 3) Follow up within 2 hours while engagement is high. Avoid: Pushing financing discussion too early.",
            "extracted_data": {
                "urgency_level": "high",
                "suggested_actions": [
                    "schedule_viewing",
                    "prepare_school_info",
                    "follow_up_2_hours"
                ],
                "conversation_stage_assessment": "ready_for_properties",
                "objection_likelihood": "low"
            },
            "reasoning": "Lead shows consistent engagement, specific preferences, and behavioral patterns indicating serious buyer. School focus suggests family urgency."
        }

        claude_client_mock.agenerate.return_value = mock_coaching_response

        with patch('services.agent_assistance_service.ClaudeClient') as mock_claude_class:
            mock_claude_class.return_value = claude_client_mock

            agent_service = AgentAssistanceService("test_tenant")

            suggestions = await agent_service.suggest_conversation_strategies(
                memory_context_rich["conversation"],
                memory_context_rich["behavioral_profile"],
                memory_context_rich["conversation"]["conversation_stage"]
            )

            # Verify agent coaching quality
            assert suggestions is not None
            assert "schedule" in suggestions.lower() or "viewing" in suggestions.lower()
            assert "school" in suggestions.lower()
            assert claude_client_mock.agenerate.called

    @pytest.mark.asyncio
    async def test_cross_tenant_claude_configuration_isolation(self):
        """Test Claude configuration isolation between tenants"""

        tenant_a_config = {
            "model_name": "claude-sonnet-4-20250514",
            "temperature": 0.7,
            "system_prompts": {"buyer": "Luxury real estate specialist"}
        }

        tenant_b_config = {
            "model_name": "claude-haiku-4",
            "temperature": 0.3,
            "system_prompts": {"buyer": "First-time buyer helper"}
        }

        with patch('core.intelligent_conversation_manager.get_tenant_claude_config') as mock_config:
            # Test tenant A gets their config
            mock_config.return_value = tenant_a_config
            manager_a = IntelligentConversationManager("tenant_a")

            # Test tenant B gets their config
            mock_config.return_value = tenant_b_config
            manager_b = IntelligentConversationManager("tenant_b")

            # Verify configuration isolation
            assert mock_config.call_count >= 2
            calls = mock_config.call_args_list
            assert any("tenant_a" in str(call) for call in calls)
            assert any("tenant_b" in str(call) for call in calls)

    @pytest.mark.asyncio
    async def test_claude_error_handling_and_fallbacks(self, memory_context_rich):
        """Test Claude error handling and graceful fallbacks"""

        with patch('core.intelligent_conversation_manager.ClaudeClient') as mock_claude_class:
            # Simulate Claude API error
            mock_claude = AsyncMock()
            mock_claude.agenerate.side_effect = Exception("Claude API timeout")
            mock_claude_class.return_value = mock_claude

            conversation_manager = IntelligentConversationManager("test_tenant")

            # Test graceful fallback
            response = await conversation_manager.generate_memory_aware_response(
                contact_id="test_contact",
                user_message="Tell me about properties",
                contact_info={"first_name": "Test", "id": "test_contact"},
                is_buyer=True
            )

            # Verify system continues functioning with fallbacks
            assert response is not None
            assert hasattr(response, 'message')
            # Should have fallback message or basic response
            assert response.message is not None and len(response.message) > 0

    @pytest.mark.asyncio
    async def test_claude_response_consistency_with_memory(self, memory_context_rich, claude_client_mock):
        """Test Claude response consistency when memory context is available"""

        # Generate consistent responses with same memory context
        mock_responses = [
            {
                "content": "Based on your preference for school districts and family homes, here are some great options...",
                "extracted_data": {"intent": "property_search", "confidence": 0.9}
            },
            {
                "content": "Given your focus on excellent schools and family-friendly features, I recommend...",
                "extracted_data": {"intent": "property_search", "confidence": 0.85}
            }
        ]

        claude_client_mock.agenerate.side_effect = mock_responses

        with patch('core.intelligent_conversation_manager.EnhancedMemoryService') as mock_memory:
            mock_memory.return_value.get_conversation_with_memory.return_value = memory_context_rich

            conversation_manager = IntelligentConversationManager("test_tenant")
            conversation_manager.claude_client = claude_client_mock

            # Generate two responses with same memory context
            response1 = await conversation_manager.generate_memory_aware_response(
                contact_id="test_contact",
                user_message="Show me properties",
                contact_info={"first_name": "Test", "id": "test_contact"},
                is_buyer=True
            )

            response2 = await conversation_manager.generate_memory_aware_response(
                contact_id="test_contact",
                user_message="What properties do you recommend?",
                contact_info={"first_name": "Test", "id": "test_contact"},
                is_buyer=True
            )

            # Verify response consistency
            assert "school" in response1.message.lower() and "school" in response2.message.lower()
            assert "family" in response1.message.lower() or "family" in response2.message.lower()
            assert response1.extracted_data["intent"] == response2.extracted_data["intent"]

if __name__ == "__main__":
    # Run Claude integration tests
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])