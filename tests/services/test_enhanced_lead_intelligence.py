import pytest

pytestmark = pytest.mark.integration

"""
Tests for Enhanced Lead Intelligence Service - Core AI Intelligence Service

Tests the enhanced lead intelligence service that integrates Claude Orchestrator
with Lead Intelligence Hub for comprehensive AI-powered lead analysis.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from ghl_real_estate_ai.services.claude_enhanced_lead_scorer import UnifiedScoringResult
from ghl_real_estate_ai.services.enhanced_lead_intelligence import (
    EnhancedLeadIntelligence,
    get_enhanced_lead_intelligence,
)


def _make_mock_analysis_result(**overrides):
    """Helper to create a mock UnifiedScoringResult for testing."""
    defaults = dict(
        lead_id="lead_12345",
        lead_name="Sarah Johnson",
        scored_at=datetime.now(),
        final_score=82.0,
        confidence_score=0.88,
        classification="hot",
        jorge_score=5,
        ml_conversion_score=78.0,
        churn_risk_score=15.0,
        engagement_score=85.0,
        frs_score=72.0,
        pcs_score=68.0,
        strategic_summary="High-intent luxury buyer with strong financial capability.",
        behavioral_insights="Achievement-oriented professional seeking status symbol property",
        reasoning="Strong engagement signals and disclosed budget indicate high intent.",
        risk_factors=["price_negotiation", "move_timeline"],
        opportunities=["luxury_upgrade", "family_relocation"],
        recommended_actions=[
            {"action": "schedule_showing", "priority": "high"},
            {"action": "send_market_report", "priority": "medium"},
        ],
        next_best_action="Schedule private showing at 789 Dream Street",
        expected_timeline="2-4 weeks",
        success_probability=78.0,
        feature_breakdown={"engagement": 0.85, "budget_match": 0.92},
        conversation_context={
            "lead_id": "lead_12345",
            "extracted_preferences": {"location": "Alta Loma", "occupation": "Tech Executive"},
        },
        sources=["Claude AI", "Behavioral Analysis", "CRM Data"],
        analysis_time_ms=145,
        claude_reasoning_time_ms=98,
    )
    defaults.update(overrides)
    return UnifiedScoringResult(**defaults)


class TestEnhancedLeadIntelligence:
    """Test suite for EnhancedLeadIntelligence core functionality."""

    @pytest.fixture
    def intelligence_service(self):
        """Create an EnhancedLeadIntelligence instance for testing."""
        with (
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.get_claude_orchestrator"),
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeEnhancedLeadScorer"),
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeAutomationEngine"),
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.MemoryService"),
        ):
            return EnhancedLeadIntelligence()

    @pytest.fixture
    def sample_lead_name(self):
        """Sample lead name for testing."""
        return "John Smith - Rancho Cucamonga Premium Buyer"

    @pytest.fixture
    def sample_lead_context(self):
        """Sample lead context dict for methods that require it."""
        return {
            "lead_id": "lead_12345",
            "name": "Sarah Johnson",
            "extracted_preferences": {
                "location": "Alta Loma",
                "occupation": "Tech Executive",
            },
        }

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
                    "message": "I'm looking for a luxury home in Alta Loma",
                    "type": "inbound",
                    "channel": "email",
                    "response_time": None,
                },
                {
                    "timestamp": datetime.now() - timedelta(hours=5),
                    "message": "I can show you some excellent properties. What's your budget?",
                    "type": "outbound",
                    "channel": "email",
                    "response_time": None,
                },
                {
                    "timestamp": datetime.now() - timedelta(hours=3),
                    "message": "Budget is $800K to $1.2M. Need 4+ bedrooms.",
                    "type": "inbound",
                    "channel": "email",
                    "response_time": 120,  # 2 hours
                },
            ],
            # Property interaction data
            "property_views": [
                {
                    "property_id": "prop_789",
                    "address": "123 Luxury Lane, Alta Loma",
                    "price": 950000,
                    "bedrooms": 4,
                    "bathrooms": 3.5,
                    "sqft": 3200,
                    "viewed_at": datetime.now() - timedelta(hours=2),
                    "view_duration_seconds": 300,
                    "saved_to_favorites": True,
                },
                {
                    "property_id": "prop_890",
                    "address": "456 Hills Drive, Alta Loma",
                    "price": 1100000,
                    "bedrooms": 5,
                    "bathrooms": 4,
                    "sqft": 3800,
                    "viewed_at": datetime.now() - timedelta(hours=1),
                    "view_duration_seconds": 420,
                    "saved_to_favorites": True,
                },
            ],
            # Search and filter patterns
            "search_history": [
                {
                    "timestamp": datetime.now() - timedelta(hours=4),
                    "filters": {
                        "location": "Alta Loma, TX",
                        "min_price": 800000,
                        "max_price": 1200000,
                        "min_bedrooms": 4,
                        "property_type": "single_family",
                    },
                    "results_count": 15,
                    "time_spent_seconds": 180,
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
                "search_sessions": 8,
            },
            # Demographic and preference data
            "demographics": {
                "age_range": "35-44",
                "income_bracket": "high",
                "family_status": "married_with_children",
                "employment": "tech_executive",
                "previous_home_value": 650000,
                "move_timeline": "3-6_months",
                "motivation": ["job_relocation", "upgrade_home"],
            },
            # Social and external signals
            "external_signals": {
                "linkedin_job_change": True,
                "spouse_job_location": "Rancho Cucamonga, CA",
                "school_district_research": True,
                "mortgage_pre_approval": True,
                "credit_score_range": "excellent",
            },
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
                "smart_home_technology",
            ],
            "neighborhood": {
                "name": "Westlake Hills",
                "school_rating": 10,
                "walkability_score": 7,
                "crime_rating": "very_low",
                "amenities": ["parks", "shopping", "restaurants"],
            },
            "images": ["front_exterior.jpg", "kitchen.jpg", "master_bedroom.jpg", "pool.jpg"],
        }

    @pytest.fixture
    def mock_analysis_result(self):
        """Mock UnifiedScoringResult for tests that need one."""
        return _make_mock_analysis_result()

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
                "communication_preference": "detailed_information_with_data",
            },
            "property_fit_analysis": {
                "psychological_match_score": 0.87,
                "lifestyle_alignment": "excellent",
                "value_proposition": "Perfect blend of luxury and family functionality",
                "emotional_triggers": ["executive_prestige", "family_safety", "entertaining_space"],
                "potential_concerns": ["price_point", "maintenance_costs"],
            },
            "personalized_messaging": {
                "tone": "professional_confident",
                "key_themes": ["exclusivity", "family_benefits", "investment_wisdom"],
                "urgency_level": "moderate",
                "next_best_action": "schedule_private_showing",
            },
        }

    def test_service_initialization(self, intelligence_service):
        """Test that enhanced lead intelligence service initializes correctly."""
        assert isinstance(intelligence_service, EnhancedLeadIntelligence)
        assert hasattr(intelligence_service, "claude")
        assert hasattr(intelligence_service, "enhanced_scorer")
        assert hasattr(intelligence_service, "automation_engine")
        assert hasattr(intelligence_service, "memory")
        assert hasattr(intelligence_service, "analysis_cache")
        assert hasattr(intelligence_service, "performance_metrics")

    def test_get_enhanced_lead_intelligence_singleton(self):
        """Test that the global service function returns a singleton."""
        with (
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.get_claude_orchestrator"),
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeEnhancedLeadScorer"),
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeAutomationEngine"),
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.MemoryService"),
        ):
            service1 = get_enhanced_lead_intelligence()
            service2 = get_enhanced_lead_intelligence()
            assert service1 is service2
            assert isinstance(service1, EnhancedLeadIntelligence)

    @pytest.mark.asyncio
    async def test_get_cognitive_dossier(self, intelligence_service, sample_lead_name, sample_lead_context):
        """Test generation of cognitive dossier.

        Service signature: get_cognitive_dossier(lead_name: str, lead_context: Dict)
        Returns: {"success": bool, "dossier": str, "generated_at": str, "confidence": float}
        """
        mock_response = Mock()
        mock_response.content = "High-intent luxury buyer with strong financial capability."
        mock_response.confidence = 0.92

        with patch.object(intelligence_service.claude, "chat_query", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response

            result = await intelligence_service.get_cognitive_dossier(sample_lead_name, sample_lead_context)

            assert isinstance(result, dict)
            assert result["success"] is True
            assert "dossier" in result
            assert "generated_at" in result
            assert "confidence" in result

            # Verify Claude was called
            mock_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_psychological_property_fit(
        self, intelligence_service, sample_property_data, mock_analysis_result
    ):
        """Test psychological property fit analysis.

        Service signature: get_psychological_property_fit(property_data: Dict, analysis_result: UnifiedScoringResult)
        Returns: str (the fit analysis text)
        """
        mock_response = Mock()
        mock_response.content = "Excellent lifestyle alignment for this luxury executive family."

        with patch.object(intelligence_service.claude, "chat_query", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response

            result = await intelligence_service.get_psychological_property_fit(
                sample_property_data, mock_analysis_result
            )

            assert isinstance(result, str)
            assert len(result) > 0

            # Verify Claude was called
            mock_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_swipe_commentary(self, intelligence_service, sample_lead_name, sample_property_data):
        """Test real-time swipe commentary generation.

        Service signature: get_swipe_commentary(property_data: Dict, lead_name: str)
        Returns: str
        """
        mock_response = Mock()
        mock_response.content = "This luxury property perfectly matches your family needs and budget criteria"

        with patch.object(intelligence_service.claude, "chat_query", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response

            result = await intelligence_service.get_swipe_commentary(sample_property_data, sample_lead_name)

            assert isinstance(result, str)
            assert len(result) > 0

            # Verify Claude was called
            mock_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_comprehensive_lead_analysis_enterprise(self, intelligence_service, sample_comprehensive_data):
        """Test comprehensive enterprise-grade lead analysis.

        Service signature: get_comprehensive_lead_analysis_enterprise(lead_name: str, lead_context: Dict, force_refresh: bool)
        """
        mock_result = _make_mock_analysis_result()

        with (
            patch.object(
                intelligence_service, "_execute_comprehensive_analysis", new_callable=AsyncMock
            ) as mock_execute,
            patch.object(intelligence_service, "_ensure_initialized", new_callable=AsyncMock),
        ):
            mock_execute.return_value = mock_result

            lead_name = sample_comprehensive_data["name"]
            result = await intelligence_service.get_comprehensive_lead_analysis_enterprise(
                lead_name, sample_comprehensive_data
            )

            assert isinstance(result, UnifiedScoringResult)
            assert result.lead_id == mock_result.lead_id

            # Verify comprehensive analysis was executed with correct args
            mock_execute.assert_called_once_with(lead_name, sample_comprehensive_data, False)

    @pytest.mark.asyncio
    async def test_execute_comprehensive_analysis(self, intelligence_service, sample_comprehensive_data):
        """Test execution of comprehensive analysis pipeline.

        Service signature: _execute_comprehensive_analysis(lead_name: str, lead_context: Dict, force_refresh: bool)
        """
        mock_result = _make_mock_analysis_result()

        with patch.object(
            intelligence_service, "_enhanced_analysis_with_optimizations", new_callable=AsyncMock
        ) as mock_enhanced:
            mock_enhanced.return_value = mock_result

            lead_name = sample_comprehensive_data["name"]
            result = await intelligence_service._execute_comprehensive_analysis(lead_name, sample_comprehensive_data)

            assert isinstance(result, UnifiedScoringResult)
            mock_enhanced.assert_called_once()

    @pytest.mark.asyncio
    async def test_enhanced_analysis_with_optimizations(self, intelligence_service, sample_comprehensive_data):
        """Test enhanced analysis with performance optimizations.

        Service signature: _enhanced_analysis_with_optimizations(lead_name: str, lead_context: Dict, force_refresh: bool)
        """
        # Disable CQRS and optimized cache to test the direct analysis path
        intelligence_service.cqrs_service = None
        intelligence_service.optimized_cache = None
        intelligence_service.claude_breaker = None
        intelligence_service.cache_breaker = None

        mock_result = _make_mock_analysis_result()

        with patch.object(
            intelligence_service.enhanced_scorer, "analyze_lead_comprehensive", new_callable=AsyncMock
        ) as mock_scoring:
            mock_scoring.return_value = mock_result

            lead_name = sample_comprehensive_data["name"]
            result = await intelligence_service._enhanced_analysis_with_optimizations(
                lead_name, sample_comprehensive_data
            )

            assert isinstance(result, UnifiedScoringResult)

            # Verify scorer was called
            mock_scoring.assert_called_once()

    def test_convert_cqrs_to_unified_result(self, intelligence_service, sample_lead_context):
        """Test conversion of CQRS result to unified format.

        Service signature: _convert_cqrs_to_unified_result(cqrs_result, lead_name: str, lead_context: Dict)
        Returns: UnifiedScoringResult
        """
        # The service expects a cqrs_result object with .data and .latency_ms attributes
        cqrs_result = Mock()
        cqrs_result.data = {
            "lead_id": "lead_12345",
            "score": 85.0,
            "confidence": 0.88,
            "classification": "hot",
            "reasoning": "Strong engagement and disclosed budget.",
        }
        cqrs_result.latency_ms = 125

        unified_result = intelligence_service._convert_cqrs_to_unified_result(
            cqrs_result, "Sarah Johnson", sample_lead_context
        )

        assert isinstance(unified_result, UnifiedScoringResult)
        assert unified_result.lead_id == "lead_12345"
        assert unified_result.lead_name == "Sarah Johnson"
        assert unified_result.final_score == 85.0
        assert unified_result.confidence_score == 0.88
        assert unified_result.classification == "hot"
        assert unified_result.analysis_time_ms == 125

    @pytest.mark.asyncio
    async def test_get_comprehensive_lead_analysis(self, intelligence_service, sample_comprehensive_data):
        """Test comprehensive lead analysis (standard version).

        Service signature: get_comprehensive_lead_analysis(lead_name: str, lead_context: Dict, force_refresh: bool)
        """
        mock_result = _make_mock_analysis_result()

        with (
            patch.object(
                intelligence_service.enhanced_scorer, "analyze_lead_comprehensive", new_callable=AsyncMock
            ) as mock_scoring,
            patch.object(intelligence_service, "_update_metrics") as mock_metrics,
        ):
            mock_scoring.return_value = mock_result

            lead_name = sample_comprehensive_data["name"]
            result = await intelligence_service.get_comprehensive_lead_analysis(lead_name, sample_comprehensive_data)

            assert isinstance(result, UnifiedScoringResult)
            assert result.lead_id == mock_result.lead_id

            # Verify scoring was called
            mock_scoring.assert_called_once()
            mock_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_behavioral_insight(self, intelligence_service, mock_analysis_result):
        """Test behavioral insight generation.

        Service signature: generate_behavioral_insight(lead_name: str, analysis_result: UnifiedScoringResult)
        Returns: str
        """
        lead_name = "Sarah Johnson"
        result = await intelligence_service.generate_behavioral_insight(lead_name, mock_analysis_result)

        assert isinstance(result, str)
        assert len(result) > 0
        # Should return the behavioral_insights from the analysis_result
        assert result == mock_analysis_result.behavioral_insights

    @pytest.mark.asyncio
    async def test_generate_quick_action_script(self, intelligence_service, mock_analysis_result):
        """Test quick action script generation.

        Service signature: generate_quick_action_script(lead_name: str, script_type: str, analysis_result: UnifiedScoringResult)
        Returns: Dict with success, script, reasoning, etc.
        """
        mock_automated = Mock()
        mock_automated.primary_script = "Hi Sarah, I found the perfect property..."
        mock_automated.personalization_notes = "Tailored to luxury preferences"
        mock_automated.success_probability = 0.88
        mock_automated.channel = "sms"

        with patch.object(
            intelligence_service.automation_engine, "generate_personalized_script", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = mock_automated

            result = await intelligence_service.generate_quick_action_script(
                "Sarah Johnson", "sms", mock_analysis_result
            )

            assert isinstance(result, dict)
            assert result["success"] is True
            assert "script" in result
            assert "reasoning" in result

            mock_generate.assert_called_once()

    def test_get_persona_insight(self, intelligence_service, mock_analysis_result):
        """Test persona insight extraction.

        Service signature: _get_persona_insight(lead_name: str, analysis_result: UnifiedScoringResult)
        Returns: str
        """
        # Test with a known persona name
        insight = intelligence_service._get_persona_insight("Sarah Chen", mock_analysis_result)

        assert isinstance(insight, str)
        assert len(insight) > 0
        # Should contain the final_score from the analysis result
        assert str(int(mock_analysis_result.final_score)) in insight

    def test_create_fallback_analysis(self, intelligence_service, sample_comprehensive_data):
        """Test creation of fallback analysis when main analysis fails.

        Service signature: _create_fallback_analysis(lead_name: str, lead_context: Dict, error: str)
        Returns: UnifiedScoringResult
        """
        lead_name = sample_comprehensive_data["name"]
        error_msg = "Service temporarily unavailable"

        fallback = intelligence_service._create_fallback_analysis(lead_name, sample_comprehensive_data, error_msg)

        assert isinstance(fallback, UnifiedScoringResult)
        assert "fallback" in fallback.lead_id
        assert fallback.classification == "error"
        assert fallback.confidence_score == 0.1
        assert fallback.final_score == 50.0
        assert error_msg in fallback.strategic_summary

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

        # total_requests = analyses_completed + cache_hits = 165
        # cache_hit_rate = 65 / 165
        expected_hit_rate = 65 / 165
        assert abs(metrics["cache_hit_rate"] - expected_hit_rate) < 0.01

    @pytest.mark.asyncio
    async def test_error_handling_and_fallback(self, intelligence_service, sample_comprehensive_data):
        """Test error handling and fallback mechanisms."""
        # Mock enhanced scorer to raise an exception
        with patch.object(
            intelligence_service.enhanced_scorer, "analyze_lead_comprehensive", new_callable=AsyncMock
        ) as mock_scoring:
            mock_scoring.side_effect = Exception("Service temporarily unavailable")

            lead_name = sample_comprehensive_data["name"]
            # Should fall back to basic analysis without crashing
            result = await intelligence_service.get_comprehensive_lead_analysis(lead_name, sample_comprehensive_data)

            assert isinstance(result, UnifiedScoringResult)
            assert "fallback" in result.lead_id
            assert result.classification == "error"

    @pytest.mark.asyncio
    async def test_caching_behavior(self, intelligence_service, sample_comprehensive_data):
        """Test caching behavior for performance optimization."""
        mock_result = _make_mock_analysis_result()

        with patch.object(
            intelligence_service.enhanced_scorer, "analyze_lead_comprehensive", new_callable=AsyncMock
        ) as mock_scoring:
            mock_scoring.return_value = mock_result

            lead_name = sample_comprehensive_data["name"]

            # First call - cache miss, should call scorer
            result1 = await intelligence_service.get_comprehensive_lead_analysis(lead_name, sample_comprehensive_data)
            assert isinstance(result1, UnifiedScoringResult)
            assert mock_scoring.call_count == 1

            # Second call with same args - should hit cache
            result2 = await intelligence_service.get_comprehensive_lead_analysis(lead_name, sample_comprehensive_data)
            assert isinstance(result2, UnifiedScoringResult)
            # Scorer should NOT have been called again (cache hit)
            assert mock_scoring.call_count == 1
            assert intelligence_service.performance_metrics["cache_hits"] >= 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, intelligence_service, sample_comprehensive_data):
        """Test circuit breaker integration for resilience."""
        # The service gracefully handles when claude_breaker is None (default)
        # by falling back to direct analysis.
        mock_result = _make_mock_analysis_result()

        with patch.object(
            intelligence_service.enhanced_scorer, "analyze_lead_comprehensive", new_callable=AsyncMock
        ) as mock_scoring:
            mock_scoring.return_value = mock_result

            lead_name = sample_comprehensive_data["name"]
            result = await intelligence_service.get_comprehensive_lead_analysis(lead_name, sample_comprehensive_data)

            # Should still return a valid result
            assert isinstance(result, UnifiedScoringResult)
            assert result.lead_id == mock_result.lead_id


class TestEnhancedLeadIntelligenceIntegration:
    """Integration tests for enhanced lead intelligence service."""

    def _reset_shared_resources(self):
        """Reset class-level shared resources so patches take effect."""
        EnhancedLeadIntelligence._claude = None
        EnhancedLeadIntelligence._enhanced_scorer = None
        EnhancedLeadIntelligence._automation_engine = None
        EnhancedLeadIntelligence._memory = None
        EnhancedLeadIntelligence._attom_client = None
        EnhancedLeadIntelligence._latex_gen = None
        EnhancedLeadIntelligence._heygen = None

    @pytest.mark.asyncio
    async def test_full_intelligence_workflow(self):
        """Test complete intelligence workflow from lead data to actionable insights."""
        self._reset_shared_resources()
        with (
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.get_claude_orchestrator") as mock_claude_orch,
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeEnhancedLeadScorer") as mock_scorer_cls,
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeAutomationEngine") as mock_engine,
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.MemoryService") as mock_memory,
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.get_attom_client"),
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.get_latex_report_generator"),
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.get_heygen_service"),
        ):
            # Setup mocks
            mock_claude = Mock()
            mock_claude_orch.return_value = mock_claude

            mock_result = _make_mock_analysis_result(lead_id="test_integration_lead")

            mock_scorer_instance = Mock()
            mock_scorer_cls.return_value = mock_scorer_instance
            mock_scorer_instance.analyze_lead_comprehensive = AsyncMock(return_value=mock_result)

            # Create service
            service = EnhancedLeadIntelligence()

            # Test data
            lead_data = {
                "lead_id": "test_integration_lead",
                "name": "Integration Test User",
                "email": "test@example.com",
                "conversation_history": [{"message": "Looking for luxury property", "timestamp": datetime.now()}],
                "property_views": [{"property_id": "prop1", "price": 800000, "viewed_at": datetime.now()}],
                "demographics": {"income_bracket": "high", "family_status": "married"},
            }

            # Execute workflow with correct signature: (lead_name, lead_context)
            analysis = await service.get_comprehensive_lead_analysis("Integration Test User", lead_data)

            # Verify results
            assert isinstance(analysis, UnifiedScoringResult)
            assert analysis.lead_id == "test_integration_lead"

            # Verify scorer was called
            mock_scorer_instance.analyze_lead_comprehensive.assert_called_once()

    @pytest.mark.asyncio
    async def test_property_psychological_fit_workflow(self):
        """Test property psychological fit analysis workflow."""
        self._reset_shared_resources()
        with (
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.get_claude_orchestrator") as mock_claude_orch,
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeEnhancedLeadScorer"),
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeAutomationEngine"),
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.MemoryService"),
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.get_attom_client"),
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.get_latex_report_generator"),
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.get_heygen_service"),
        ):
            # Setup Claude mock for chat_query (used by get_psychological_property_fit)
            mock_claude = Mock()
            mock_claude_orch.return_value = mock_claude
            mock_response = Mock()
            mock_response.content = "Excellent match: luxury features align with executive lifestyle."
            mock_claude.chat_query = AsyncMock(return_value=mock_response)

            service = EnhancedLeadIntelligence()

            property_data = {
                "address": "123 Luxury Lane",
                "price": 1200000,
                "features": ["pool", "home_theater", "wine_cellar"],
                "neighborhood": {"school_rating": 10, "crime_rating": "very_low"},
            }

            # The service expects (property_data, analysis_result: UnifiedScoringResult)
            mock_result = _make_mock_analysis_result(lead_name="Executive Family Buyer")
            fit_analysis = await service.get_psychological_property_fit(property_data, mock_result)

            assert isinstance(fit_analysis, str)
            assert len(fit_analysis) > 0

            # Verify Claude was called
            mock_claude.chat_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test service performance under high load conditions."""
        self._reset_shared_resources()
        with (
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.get_claude_orchestrator"),
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeEnhancedLeadScorer") as mock_scorer_cls,
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeAutomationEngine") as mock_engine,
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.MemoryService"),
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.get_attom_client"),
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.get_latex_report_generator"),
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.get_heygen_service"),
        ):
            # Setup fast-responding mocks
            mock_scorer_instance = Mock()
            mock_scorer_cls.return_value = mock_scorer_instance

            def make_result(lead_id):
                return _make_mock_analysis_result(lead_id=lead_id)

            mock_scorer_instance.analyze_lead_comprehensive = AsyncMock(
                side_effect=lambda **kwargs: make_result(kwargs.get("lead_id", "unknown"))
            )

            service = EnhancedLeadIntelligence()

            # Generate 10 concurrent requests with correct signature: (lead_name, lead_context)
            tasks = []
            for i in range(10):
                lead_name = f"Load Test User {i}"
                lead_data = {
                    "lead_id": f"load_test_lead_{i}",
                    "name": lead_name,
                    "conversation_history": [],
                    "demographics": {"income_bracket": "medium"},
                }
                task = service.get_comprehensive_lead_analysis(lead_name, lead_data, force_refresh=True)
                tasks.append(task)

            # Execute concurrently and measure time
            start_time = datetime.now()
            results = await asyncio.gather(*tasks)
            end_time = datetime.now()

            processing_time = (end_time - start_time).total_seconds()

            # Verify all requests completed successfully
            assert len(results) == 10
            for result in results:
                assert isinstance(result, UnifiedScoringResult)

            # Performance should be reasonable (less than 10 seconds for 10 concurrent requests)
            assert processing_time < 10.0, f"Processing time {processing_time}s is too slow for load test"

    @pytest.mark.asyncio
    async def test_memory_integration(self):
        """Test integration with memory service for lead history."""
        self._reset_shared_resources()
        with (
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.get_claude_orchestrator") as mock_claude_orch,
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeEnhancedLeadScorer"),
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.ClaudeAutomationEngine"),
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.MemoryService") as mock_memory_service,
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.get_attom_client"),
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.get_latex_report_generator"),
            patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.get_heygen_service"),
        ):
            # Setup Claude mock for chat_query (used by get_cognitive_dossier)
            mock_claude = Mock()
            mock_claude_orch.return_value = mock_claude
            mock_response = Mock()
            mock_response.content = "Repeat luxury buyer with strong historical engagement."
            mock_response.confidence = 0.95
            mock_claude.chat_query = AsyncMock(return_value=mock_response)

            service = EnhancedLeadIntelligence()

            lead_name = "Returning Luxury Client"
            lead_context = {
                "lead_id": "returning_client_001",
                "previous_interactions": 5,
                "last_property_interest": "luxury_condo",
            }

            # get_cognitive_dossier(lead_name, lead_context)
            dossier = await service.get_cognitive_dossier(lead_name, lead_context)

            # Verify the dossier structure
            assert isinstance(dossier, dict)
            assert dossier["success"] is True
            assert "dossier" in dossier
            assert "generated_at" in dossier
            assert "confidence" in dossier

            # Verify Claude was called
            mock_claude.chat_query.assert_called_once()
