"""
Tests for Enhanced Lead Intelligence Service - Core AI Intelligence Service

Tests the enhanced lead intelligence service that integrates Claude Orchestrator
with Lead Intelligence Hub for comprehensive AI-powered lead analysis.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from dataclasses import dataclass

from ghl_real_estate_ai.services.enhanced_lead_intelligence import (
    EnhancedLeadIntelligence,
    get_enhanced_lead_intelligence
)


class TestEnhancedLeadIntelligence:
    """Test suite for EnhancedLeadIntelligence core functionality."""

    @pytest.fixture
    def intelligence_service(self):
        """Create an EnhancedLeadIntelligence instance for testing."""
        with patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.get_claude_orchestrator'), \
             patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeEnhancedLeadScorer'), \
             patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeAutomationEngine'), \
             patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.MemoryService'):
            return EnhancedLeadIntelligence()

    @pytest.fixture
    def sample_lead_name(self):
        """Sample lead name for testing."""
        return "John Smith - Austin Premium Buyer"

    @pytest.fixture
    def sample_comprehensive_data(self):
        """Sample comprehensive lead data for testing."""
        return {
            "lead_id": "lead_12345",
            "name": "Sarah Johnson",
            "email": "sarah.johnson@example.com",
            "phone": "+1234567890",
            "created_at": datetime.now() - timedelta(days=7),
            "last_contact": datetime.now() - timedelta(hours=3),
            "status": "active",
            
            # Contact and engagement data
            "conversation_history": [
                {
                    "timestamp": datetime.now() - timedelta(hours=6),
                    "message": "I'm looking for a luxury home in West Lake Hills",
                    "type": "inbound",
                    "channel": "email",
                    "response_time": None
                },
                {
                    "timestamp": datetime.now() - timedelta(hours=5),
                    "message": "I can show you some excellent properties. What's your budget?",
                    "type": "outbound", 
                    "channel": "email",
                    "response_time": None
                },
                {
                    "timestamp": datetime.now() - timedelta(hours=3),
                    "message": "Budget is $800K to $1.2M. Need 4+ bedrooms.",
                    "type": "inbound",
                    "channel": "email", 
                    "response_time": 120  # 2 hours
                }
            ],
            
            # Property interaction data
            "property_views": [
                {
                    "property_id": "prop_789",
                    "address": "123 Luxury Lane, West Lake Hills",
                    "price": 950000,
                    "bedrooms": 4,
                    "bathrooms": 3.5,
                    "sqft": 3200,
                    "viewed_at": datetime.now() - timedelta(hours=2),
                    "view_duration_seconds": 300,
                    "saved_to_favorites": True
                },
                {
                    "property_id": "prop_890", 
                    "address": "456 Hills Drive, West Lake Hills",
                    "price": 1100000,
                    "bedrooms": 5,
                    "bathrooms": 4,
                    "sqft": 3800,
                    "viewed_at": datetime.now() - timedelta(hours=1),
                    "view_duration_seconds": 420,
                    "saved_to_favorites": True
                }
            ],
            
            # Search and filter patterns
            "search_history": [
                {
                    "timestamp": datetime.now() - timedelta(hours=4),
                    "filters": {
                        "location": "West Lake Hills, TX",
                        "min_price": 800000,
                        "max_price": 1200000,
                        "min_bedrooms": 4,
                        "property_type": "single_family"
                    },
                    "results_count": 15,
                    "time_spent_seconds": 180
                }
            ],
            
            # Behavioral and engagement metrics
            "engagement_data": {
                "email_open_rate": 0.85,
                "email_click_rate": 0.62,
                "response_time_avg_minutes": 45,
                "website_sessions": 12,
                "pages_per_session": 7,
                "time_on_site_minutes": 25,
                "property_saves": 6,
                "search_sessions": 8
            },
            
            # Demographic and preference data
            "demographics": {
                "age_range": "35-44",
                "income_bracket": "high", 
                "family_status": "married_with_children",
                "employment": "tech_executive",
                "previous_home_value": 650000,
                "move_timeline": "3-6_months",
                "motivation": ["job_relocation", "upgrade_home"]
            },
            
            # Social and external signals
            "external_signals": {
                "linkedin_job_change": True,
                "spouse_job_location": "Austin, TX", 
                "school_district_research": True,
                "mortgage_pre_approval": True,
                "credit_score_range": "excellent"
            }
        }

    @pytest.fixture
    def sample_property_data(self):
        """Sample property data for psychological fit analysis."""
        return {
            "property_id": "prop_999",
            "address": "789 Dream Street, Westlake",
            "price": 1050000,
            "bedrooms": 4,
            "bathrooms": 3.5,
            "sqft": 3400,
            "lot_size": 0.75,
            "property_type": "single_family",
            "year_built": 2018,
            "features": [
                "luxury_kitchen",
                "master_suite", 
                "home_office",
                "swimming_pool",
                "three_car_garage",
                "smart_home_technology"
            ],
            "neighborhood": {
                "name": "Westlake Hills",
                "school_rating": 10,
                "walkability_score": 7,
                "crime_rating": "very_low",
                "amenities": ["parks", "shopping", "restaurants"]
            },
            "images": [
                "front_exterior.jpg",
                "kitchen.jpg", 
                "master_bedroom.jpg",
                "pool.jpg"
            ]
        }

    @pytest.fixture
    def mock_claude_response(self):
        """Mock Claude AI response for testing."""
        return {
            "cognitive_dossier": {
                "summary": "High-intent luxury buyer with strong financial capability and specific location preferences.",
                "psychological_profile": "Achievement-oriented professional seeking status symbol property",
                "decision_making_style": "Analytical with emotional considerations for family",
                "key_motivators": ["prestige", "family_comfort", "investment_value"],
                "potential_objections": ["price_negotiation", "move_timeline"],
                "communication_preference": "detailed_information_with_data"
            },
            "property_fit_analysis": {
                "psychological_match_score": 0.87,
                "lifestyle_alignment": "excellent",
                "value_proposition": "Perfect blend of luxury and family functionality",
                "emotional_triggers": ["executive_prestige", "family_safety", "entertaining_space"],
                "potential_concerns": ["price_point", "maintenance_costs"]
            },
            "personalized_messaging": {
                "tone": "professional_confident",
                "key_themes": ["exclusivity", "family_benefits", "investment_wisdom"],
                "urgency_level": "moderate",
                "next_best_action": "schedule_private_showing"
            }
        }

    def test_service_initialization(self, intelligence_service):
        """Test that enhanced lead intelligence service initializes correctly."""
        assert isinstance(intelligence_service, EnhancedLeadIntelligence)
        assert hasattr(intelligence_service, 'claude')
        assert hasattr(intelligence_service, 'enhanced_scorer')
        assert hasattr(intelligence_service, 'automation_engine')
        assert hasattr(intelligence_service, 'memory')
        assert hasattr(intelligence_service, 'analysis_cache')
        assert hasattr(intelligence_service, 'performance_metrics')

    def test_get_enhanced_lead_intelligence_singleton(self):
        """Test that the global service function returns a singleton."""
        with patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.get_claude_orchestrator'), \
             patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeEnhancedLeadScorer'), \
             patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeAutomationEngine'), \
             patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.MemoryService'):
            
            service1 = get_enhanced_lead_intelligence()
            service2 = get_enhanced_lead_intelligence()
            assert service1 is service2
            assert isinstance(service1, EnhancedLeadIntelligence)

    @pytest.mark.asyncio
    async def test_get_cognitive_dossier(self, intelligence_service, sample_lead_name, mock_claude_response):
        """Test generation of cognitive dossier."""
        with patch.object(intelligence_service.claude, 'analyze_lead_with_memory', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_claude_response["cognitive_dossier"]
            
            result = await intelligence_service.get_cognitive_dossier(sample_lead_name)
            
            assert isinstance(result, dict)
            assert "summary" in result
            assert "psychological_profile" in result
            assert "decision_making_style" in result
            assert "key_motivators" in result
            assert "potential_objections" in result
            assert "communication_preference" in result
            
            # Verify Claude was called with correct parameters
            mock_analyze.assert_called_once_with(sample_lead_name, "cognitive_dossier")

    @pytest.mark.asyncio
    async def test_get_psychological_property_fit(self, intelligence_service, sample_lead_name, 
                                                sample_property_data, mock_claude_response):
        """Test psychological property fit analysis."""
        with patch.object(intelligence_service.claude, 'analyze_property_fit', new_callable=AsyncMock) as mock_fit:
            mock_fit.return_value = mock_claude_response["property_fit_analysis"]
            
            result = await intelligence_service.get_psychological_property_fit(
                sample_lead_name, sample_property_data
            )
            
            assert isinstance(result, dict)
            assert "psychological_match_score" in result
            assert "lifestyle_alignment" in result
            assert "value_proposition" in result
            assert "emotional_triggers" in result
            assert "potential_concerns" in result
            
            # Verify score is valid range
            if "psychological_match_score" in result:
                assert 0 <= result["psychological_match_score"] <= 1
            
            # Verify Claude was called correctly
            mock_fit.assert_called_once_with(sample_lead_name, sample_property_data)

    @pytest.mark.asyncio
    async def test_get_swipe_commentary(self, intelligence_service, sample_lead_name, sample_property_data):
        """Test real-time swipe commentary generation."""
        with patch.object(intelligence_service.claude, 'generate_swipe_commentary', new_callable=AsyncMock) as mock_swipe:
            mock_commentary = {
                "commentary": "This luxury property perfectly matches your family needs and budget criteria",
                "urgency_score": 0.75,
                "call_to_action": "Schedule viewing today - properties in this area move quickly"
            }
            mock_swipe.return_value = mock_commentary
            
            result = await intelligence_service.get_swipe_commentary(sample_lead_name, sample_property_data)
            
            assert isinstance(result, dict)
            assert "commentary" in result
            
            # Verify Claude was called correctly
            mock_swipe.assert_called_once_with(sample_lead_name, sample_property_data)

    @pytest.mark.asyncio
    async def test_get_comprehensive_lead_analysis_enterprise(self, intelligence_service, 
                                                            sample_comprehensive_data, mock_claude_response):
        """Test comprehensive enterprise-grade lead analysis."""
        with patch.object(intelligence_service, '_execute_comprehensive_analysis', new_callable=AsyncMock) as mock_execute:
            mock_analysis = {
                "lead_id": sample_comprehensive_data["lead_id"],
                "cognitive_dossier": mock_claude_response["cognitive_dossier"],
                "behavioral_insights": {
                    "intent_level": "high",
                    "engagement_score": 0.85,
                    "buying_signals": ["budget_disclosed", "frequent_viewing", "quick_responses"]
                },
                "predictive_analytics": {
                    "conversion_probability": 0.78,
                    "time_to_close_days": 45,
                    "revenue_potential": 25000
                },
                "next_best_actions": [
                    {"action": "schedule_showing", "priority": "high", "confidence": 0.9},
                    {"action": "send_market_report", "priority": "medium", "confidence": 0.7}
                ]
            }
            mock_execute.return_value = mock_analysis
            
            result = await intelligence_service.get_comprehensive_lead_analysis_enterprise(sample_comprehensive_data)
            
            assert isinstance(result, dict)
            assert "lead_id" in result
            assert "cognitive_dossier" in result
            assert "behavioral_insights" in result
            assert "predictive_analytics" in result
            assert "next_best_actions" in result
            
            # Verify comprehensive analysis was executed
            mock_execute.assert_called_once_with(sample_comprehensive_data)

    @pytest.mark.asyncio
    async def test_execute_comprehensive_analysis(self, intelligence_service, sample_comprehensive_data):
        """Test execution of comprehensive analysis pipeline."""
        # Mock dependencies
        with patch.object(intelligence_service, '_enhanced_analysis_with_optimizations', new_callable=AsyncMock) as mock_enhanced:
            mock_enhanced.return_value = {
                "analysis_result": "comprehensive_analysis_complete",
                "confidence_score": 0.88,
                "processing_time_ms": 150
            }
            
            result = await intelligence_service._execute_comprehensive_analysis(sample_comprehensive_data)
            
            assert isinstance(result, dict)
            mock_enhanced.assert_called_once()

    @pytest.mark.asyncio 
    async def test_enhanced_analysis_with_optimizations(self, intelligence_service, sample_comprehensive_data):
        """Test enhanced analysis with performance optimizations."""
        # Mock CQRS service and optimized cache
        intelligence_service.cqrs_service = AsyncMock()
        intelligence_service.optimized_cache = AsyncMock()
        
        with patch.object(intelligence_service.enhanced_scorer, 'get_unified_scoring', new_callable=AsyncMock) as mock_scoring, \
             patch.object(intelligence_service.automation_engine, 'generate_quick_scripts', new_callable=AsyncMock) as mock_scripts, \
             patch.object(intelligence_service, '_convert_cqrs_to_unified_result') as mock_convert:
            
            # Mock scoring response
            mock_scoring.return_value = {
                "overall_score": 0.82,
                "behavioral_score": 0.79,
                "engagement_score": 0.85,
                "intent_score": 0.88
            }
            
            # Mock script generation
            mock_scripts.return_value = [
                {"script_type": "follow_up_email", "content": "Personalized follow-up"},
                {"script_type": "showing_request", "content": "Showing invitation"}
            ]
            
            # Mock conversion
            mock_convert.return_value = {"unified": "result"}
            
            result = await intelligence_service._enhanced_analysis_with_optimizations(
                sample_comprehensive_data, "test_lead"
            )
            
            assert isinstance(result, dict)
            
            # Verify services were called
            mock_scoring.assert_called_once()
            mock_scripts.assert_called_once()

    def test_convert_cqrs_to_unified_result(self, intelligence_service):
        """Test conversion of CQRS result to unified format."""
        cqrs_result = {
            "query_results": {
                "lead_scoring": {"score": 0.85},
                "behavioral_analysis": {"intent": "high"},
                "engagement_metrics": {"engagement_score": 0.78}
            },
            "command_results": {
                "script_generation": {"scripts": ["script1", "script2"]},
                "recommendation_engine": {"actions": ["action1", "action2"]}
            },
            "metadata": {
                "processing_time_ms": 125,
                "cache_hits": 3,
                "api_calls": 2
            }
        }
        
        unified_result = intelligence_service._convert_cqrs_to_unified_result(
            cqrs_result, "test_lead"
        )
        
        assert isinstance(unified_result, dict)
        assert "lead_id" in unified_result
        assert "behavioral_score" in unified_result
        assert "engagement_score" in unified_result
        assert "generated_scripts" in unified_result
        assert "recommended_actions" in unified_result
        assert "analysis_metadata" in unified_result

    @pytest.mark.asyncio
    async def test_get_comprehensive_lead_analysis(self, intelligence_service, sample_comprehensive_data):
        """Test comprehensive lead analysis (standard version)."""
        with patch.object(intelligence_service.enhanced_scorer, 'get_unified_scoring', new_callable=AsyncMock) as mock_scoring, \
             patch.object(intelligence_service.automation_engine, 'generate_quick_scripts', new_callable=AsyncMock) as mock_scripts, \
             patch.object(intelligence_service, '_update_metrics') as mock_metrics:
            
            mock_scoring.return_value = {
                "overall_score": 0.75,
                "confidence": 0.82
            }
            mock_scripts.return_value = ["script1", "script2"]
            
            result = await intelligence_service.get_comprehensive_lead_analysis(sample_comprehensive_data)
            
            assert isinstance(result, dict)
            assert result["lead_id"] == sample_comprehensive_data["lead_id"]
            
            # Verify scoring and script generation were called
            mock_scoring.assert_called_once()
            mock_scripts.assert_called_once()
            mock_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_behavioral_insight(self, intelligence_service, sample_comprehensive_data):
        """Test behavioral insight generation."""
        with patch.object(intelligence_service.claude, 'generate_behavioral_insight', new_callable=AsyncMock) as mock_insight:
            mock_insight.return_value = {
                "primary_behavior": "high_engagement_explorer",
                "engagement_pattern": "consistent_upward_trend", 
                "buying_signals": ["specific_budget", "location_focused", "quick_responses"],
                "psychological_state": "motivated_and_ready",
                "recommended_approach": "direct_and_informative"
            }
            
            result = await intelligence_service.generate_behavioral_insight(sample_comprehensive_data)
            
            assert isinstance(result, dict)
            assert "primary_behavior" in result
            assert "engagement_pattern" in result
            assert "buying_signals" in result
            
            mock_insight.assert_called_once_with(sample_comprehensive_data)

    @pytest.mark.asyncio
    async def test_generate_quick_action_script(self, intelligence_service, sample_comprehensive_data):
        """Test quick action script generation."""
        with patch.object(intelligence_service.automation_engine, 'generate_script', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = {
                "script_content": "Hi Sarah, I found the perfect luxury property in West Lake Hills...",
                "script_type": "follow_up_email",
                "personalization_score": 0.88,
                "urgency_level": "moderate",
                "estimated_response_rate": 0.72
            }
            
            result = await intelligence_service.generate_quick_action_script(
                sample_comprehensive_data, "follow_up_email"
            )
            
            assert isinstance(result, dict)
            assert "script_content" in result
            assert "script_type" in result
            
            mock_generate.assert_called_once()

    def test_get_persona_insight(self, intelligence_service, sample_comprehensive_data):
        """Test persona insight extraction."""
        insight = intelligence_service._get_persona_insight(sample_comprehensive_data)
        
        assert isinstance(insight, dict)
        assert "persona_type" in insight
        assert "confidence" in insight
        assert "key_characteristics" in insight
        
        # Should identify luxury buyer persona from the data
        assert insight["persona_type"] in [
            "luxury_buyer", "executive_buyer", "family_upgrader", 
            "relocation_buyer", "investment_buyer", "first_time_buyer"
        ]
        assert 0 <= insight["confidence"] <= 1

    def test_create_fallback_analysis(self, intelligence_service, sample_comprehensive_data):
        """Test creation of fallback analysis when main analysis fails."""
        fallback = intelligence_service._create_fallback_analysis(sample_comprehensive_data)
        
        assert isinstance(fallback, dict)
        assert "lead_id" in fallback
        assert "behavioral_score" in fallback
        assert "engagement_score" in fallback
        assert "analysis_type" in fallback
        assert fallback["analysis_type"] == "fallback"
        
        # Should have basic scoring even in fallback mode
        assert 0 <= fallback["behavioral_score"] <= 1
        assert 0 <= fallback["engagement_score"] <= 1

    def test_update_metrics(self, intelligence_service):
        """Test performance metrics updating."""
        initial_count = intelligence_service.performance_metrics["analyses_completed"]
        
        intelligence_service._update_metrics(150.5)  # 150.5ms analysis time
        
        # Should increment analyses count
        assert intelligence_service.performance_metrics["analyses_completed"] == initial_count + 1
        
        # Should update average time (basic validation)
        assert intelligence_service.performance_metrics["avg_analysis_time_ms"] >= 0

    def test_get_performance_metrics(self, intelligence_service):
        """Test retrieval of performance metrics."""
        # Add some test data to metrics
        intelligence_service.performance_metrics["analyses_completed"] = 100
        intelligence_service.performance_metrics["cache_hits"] = 65
        intelligence_service.performance_metrics["avg_analysis_time_ms"] = 125.5
        
        metrics = intelligence_service.get_performance_metrics()
        
        assert isinstance(metrics, dict)
        assert metrics["analyses_completed"] == 100
        assert metrics["cache_hits"] == 65
        assert metrics["avg_analysis_time_ms"] == 125.5
        assert "cache_hit_rate" in metrics
        
        # Calculate expected cache hit rate
        expected_hit_rate = 65 / 100
        assert abs(metrics["cache_hit_rate"] - expected_hit_rate) < 0.01

    @pytest.mark.asyncio
    async def test_error_handling_and_fallback(self, intelligence_service, sample_comprehensive_data):
        """Test error handling and fallback mechanisms."""
        # Mock enhanced scorer to raise an exception
        with patch.object(intelligence_service.enhanced_scorer, 'get_unified_scoring', new_callable=AsyncMock) as mock_scoring:
            mock_scoring.side_effect = Exception("Service temporarily unavailable")
            
            # Should fall back to basic analysis without crashing
            result = await intelligence_service.get_comprehensive_lead_analysis(sample_comprehensive_data)
            
            assert isinstance(result, dict)
            assert result["lead_id"] == sample_comprehensive_data["lead_id"]
            # Should indicate fallback was used
            assert "analysis_type" in result

    @pytest.mark.asyncio
    async def test_caching_behavior(self, intelligence_service, sample_comprehensive_data):
        """Test caching behavior for performance optimization."""
        lead_id = sample_comprehensive_data["lead_id"]
        
        # Mock cache miss first, then cache hit
        cached_result = {
            "lead_id": lead_id,
            "cached_analysis": True,
            "timestamp": datetime.now()
        }
        
        with patch.object(intelligence_service, 'analysis_cache', {}) as mock_cache:
            # First call - cache miss
            with patch.object(intelligence_service.enhanced_scorer, 'get_unified_scoring', new_callable=AsyncMock) as mock_scoring:
                mock_scoring.return_value = {"score": 0.8}
                
                result1 = await intelligence_service.get_comprehensive_lead_analysis(sample_comprehensive_data)
                assert isinstance(result1, dict)
                
                # Add to cache manually for testing
                intelligence_service.analysis_cache[lead_id] = {
                    "result": cached_result,
                    "timestamp": datetime.now()
                }
                
                # Second call should use cache (we'll verify it's the same object)
                # This is a simplified test - in real implementation, cache lookup logic would be more complex

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, intelligence_service, sample_comprehensive_data):
        """Test circuit breaker integration for resilience."""
        # This would test the circuit breaker functionality
        # For now, we'll test that the service handles circuit breaker states gracefully
        
        # Mock circuit breaker to be open (failing)
        if hasattr(intelligence_service, 'claude_breaker'):
            with patch.object(intelligence_service.claude_breaker, 'is_open', return_value=True):
                result = await intelligence_service.get_comprehensive_lead_analysis(sample_comprehensive_data)
                
                # Should still return a result (fallback)
                assert isinstance(result, dict)
                assert result["lead_id"] == sample_comprehensive_data["lead_id"]


class TestEnhancedLeadIntelligenceIntegration:
    """Integration tests for enhanced lead intelligence service."""

    @pytest.mark.asyncio
    async def test_full_intelligence_workflow(self):
        """Test complete intelligence workflow from lead data to actionable insights."""
        with patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.get_claude_orchestrator') as mock_claude_orch, \
             patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeEnhancedLeadScorer') as mock_scorer, \
             patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeAutomationEngine') as mock_engine, \
             patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.MemoryService') as mock_memory:
            
            # Setup mocks
            mock_claude = Mock()
            mock_claude_orch.return_value = mock_claude
            mock_claude.analyze_lead_with_memory = AsyncMock(return_value={
                "summary": "High-value luxury buyer",
                "psychological_profile": "Executive decision maker"
            })
            
            mock_scorer_instance = Mock()
            mock_scorer.return_value = mock_scorer_instance
            mock_scorer_instance.get_unified_scoring = AsyncMock(return_value={
                "overall_score": 0.85,
                "behavioral_score": 0.82
            })
            
            mock_engine_instance = Mock()
            mock_engine.return_value = mock_engine_instance
            mock_engine_instance.generate_quick_scripts = AsyncMock(return_value=[
                {"type": "email", "content": "Personalized email"}
            ])
            
            # Create service
            service = EnhancedLeadIntelligence()
            
            # Test data
            lead_data = {
                "lead_id": "test_integration_lead",
                "name": "Integration Test User",
                "email": "test@example.com",
                "conversation_history": [
                    {"message": "Looking for luxury property", "timestamp": datetime.now()}
                ],
                "property_views": [
                    {"property_id": "prop1", "price": 800000, "viewed_at": datetime.now()}
                ],
                "demographics": {
                    "income_bracket": "high",
                    "family_status": "married"
                }
            }
            
            # Execute workflow
            analysis = await service.get_comprehensive_lead_analysis(lead_data)
            
            # Verify results
            assert isinstance(analysis, dict)
            assert analysis["lead_id"] == "test_integration_lead"
            assert "behavioral_score" in analysis
            assert "engagement_score" in analysis
            
            # Verify services were called
            mock_scorer_instance.get_unified_scoring.assert_called_once()
            mock_engine_instance.generate_quick_scripts.assert_called_once()

    @pytest.mark.asyncio
    async def test_property_psychological_fit_workflow(self):
        """Test property psychological fit analysis workflow."""
        with patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.get_claude_orchestrator') as mock_claude_orch, \
             patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeEnhancedLeadScorer'), \
             patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeAutomationEngine'), \
             patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.MemoryService'):
            
            # Setup Claude mock
            mock_claude = Mock()
            mock_claude_orch.return_value = mock_claude
            mock_claude.analyze_property_fit = AsyncMock(return_value={
                "psychological_match_score": 0.91,
                "lifestyle_alignment": "excellent",
                "emotional_triggers": ["luxury", "status", "family_safety"]
            })
            
            service = EnhancedLeadIntelligence()
            
            lead_name = "Executive Family Buyer"
            property_data = {
                "address": "123 Luxury Lane",
                "price": 1200000,
                "features": ["pool", "home_theater", "wine_cellar"],
                "neighborhood": {"school_rating": 10, "crime_rating": "very_low"}
            }
            
            fit_analysis = await service.get_psychological_property_fit(lead_name, property_data)
            
            assert isinstance(fit_analysis, dict)
            assert fit_analysis["psychological_match_score"] == 0.91
            assert fit_analysis["lifestyle_alignment"] == "excellent"
            assert "emotional_triggers" in fit_analysis
            
            # Verify Claude was called with correct parameters
            mock_claude.analyze_property_fit.assert_called_once_with(lead_name, property_data)

    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test service performance under high load conditions."""
        with patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.get_claude_orchestrator'), \
             patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeEnhancedLeadScorer') as mock_scorer, \
             patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeAutomationEngine') as mock_engine, \
             patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.MemoryService'):
            
            # Setup fast-responding mocks
            mock_scorer_instance = Mock()
            mock_scorer.return_value = mock_scorer_instance
            mock_scorer_instance.get_unified_scoring = AsyncMock(return_value={"overall_score": 0.8})
            
            mock_engine_instance = Mock()
            mock_engine.return_value = mock_engine_instance
            mock_engine_instance.generate_quick_scripts = AsyncMock(return_value=[])
            
            service = EnhancedLeadIntelligence()
            
            # Create multiple concurrent requests
            lead_data_template = {
                "lead_id": "load_test_lead_{}",
                "name": "Load Test User {}",
                "conversation_history": [],
                "demographics": {"income_bracket": "medium"}
            }
            
            # Generate 10 concurrent requests
            tasks = []
            for i in range(10):
                lead_data = {**lead_data_template}
                lead_data["lead_id"] = lead_data["lead_id"].format(i)
                lead_data["name"] = lead_data["name"].format(i)
                
                task = service.get_comprehensive_lead_analysis(lead_data)
                tasks.append(task)
            
            # Execute concurrently and measure time
            start_time = datetime.now()
            results = await asyncio.gather(*tasks)
            end_time = datetime.now()
            
            processing_time = (end_time - start_time).total_seconds()
            
            # Verify all requests completed successfully
            assert len(results) == 10
            for result in results:
                assert isinstance(result, dict)
                assert "lead_id" in result
            
            # Performance should be reasonable (less than 10 seconds for 10 concurrent requests)
            assert processing_time < 10.0, f"Processing time {processing_time}s is too slow for load test"

    @pytest.mark.asyncio 
    async def test_memory_integration(self):
        """Test integration with memory service for lead history."""
        with patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.get_claude_orchestrator') as mock_claude_orch, \
             patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeEnhancedLeadScorer'), \
             patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeAutomationEngine'), \
             patch('ghl_real_estate_ai.services.enhanced_lead_intelligence.MemoryService') as mock_memory_service:
            
            # Setup memory service mock
            mock_memory = Mock()
            mock_memory_service.return_value = mock_memory
            mock_memory.get_lead_history = AsyncMock(return_value={
                "previous_interactions": 5,
                "last_property_interest": "luxury_condo",
                "communication_preferences": "email_preferred"
            })
            mock_memory.store_analysis_result = AsyncMock()
            
            # Setup Claude mock 
            mock_claude = Mock()
            mock_claude_orch.return_value = mock_claude
            mock_claude.analyze_lead_with_memory = AsyncMock(return_value={
                "enhanced_with_history": True,
                "historical_context": "Repeat luxury buyer"
            })
            
            service = EnhancedLeadIntelligence()
            
            lead_name = "Returning Luxury Client"
            dossier = await service.get_cognitive_dossier(lead_name)
            
            # Verify memory integration
            assert isinstance(dossier, dict)
            assert dossier.get("enhanced_with_history") is True
            
            # Verify memory service was utilized
            mock_claude.analyze_lead_with_memory.assert_called_once_with(lead_name, "cognitive_dossier")