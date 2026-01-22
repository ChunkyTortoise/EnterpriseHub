#!/usr/bin/env python3
"""
Test Suite for Service 6 AI Integration Layer
============================================

Tests the comprehensive AI orchestration, tiered caching, and error handling.
"""

import pytest
import pytest_asyncio
import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import asdict

from ghl_real_estate_ai.services.service6_ai_integration import (
    Service6AIOrchestrator, Service6AIConfig, Service6AIResponse,
    Service6EnhancedClaudePlatformCompanion, AIScoringError, 
    AIVoiceAnalysisError, AIPredictiveError, AIInferenceError, Service6AIError
)
from ghl_real_estate_ai.services.advanced_ml_lead_scoring_engine import MLScoringResult, MLFeatureVector
from ghl_real_estate_ai.services.claude_enhanced_lead_scorer import UnifiedScoringResult
from ghl_real_estate_ai.core.llm_client import LLMResponse, LLMProvider

@pytest_asyncio.fixture
async def mock_claude_client():
    """Mock Claude client for AI responses."""
    client = MagicMock()
    client.agenerate = AsyncMock()
    return client

@pytest.fixture
def mock_database_service():
    """Mock database service for lead data."""
    db = MagicMock()
    db.get_lead = AsyncMock()
    db.log_communication = AsyncMock()
    return db

@pytest_asyncio.fixture
async def mock_cache_service():
    """Mock tiered cache service."""
    cache = MagicMock()
    cache.start = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    return cache

@pytest.fixture
def sample_lead_data():
    """Sample lead data for testing."""
    return {
        'lead_id': 'test_lead_001',
        'first_name': 'Sarah',
        'last_name': 'Johnson',
        'email': 'sarah.j@example.com',
        'budget': 500000,
        'page_views': 12,
        'last_interaction': '2026-01-20T10:00:00Z'
    }

@pytest.fixture
def mock_ml_result():
    """Mock ML scoring result."""
    feature_vector = MLFeatureVector(
        email_open_rate=0.8, email_click_rate=0.4, response_velocity=2.5,
        conversation_depth=150.0, engagement_consistency=0.9, property_view_frequency=5.0,
        search_refinement_count=3, price_range_stability=0.85, location_focus_score=0.9,
        timing_urgency_signals=0.75, budget_clarity_score=0.8, financing_readiness=0.6,
        price_sensitivity=0.5, affordability_ratio=1.1, question_sophistication=0.8,
        decision_maker_confidence=0.9, family_situation_clarity=0.7, relocation_urgency=0.5,
        previous_interactions=10, conversion_funnel_stage=0.6, seasonal_patterns=0.8,
        market_conditions_score=0.7, communication_style_score=0.8, technical_sophistication=0.7,
        local_market_knowledge=0.6, data_completeness=0.9, recency_weight=0.95
    )
    
    return MLScoringResult(
        lead_id='test_lead_001',
        timestamp=datetime.now(),
        conversion_probability=85.0,
        intent_strength=80.0,
        timing_urgency=75.0,
        financial_readiness=90.0,
        engagement_quality=88.0,
        final_ml_score=85.5,
        confidence_interval=(0.8, 0.9),
        prediction_uncertainty=0.1,
        top_features=[{'email_open_rate': 0.4}, {'property_view_frequency': 0.3}],
        feature_vector=feature_vector,
        model_version='1.0.0',
        prediction_latency_ms=45.0,
        ensemble_agreement=0.92,
        recommended_actions=['Schedule call', 'Send neighborhood report'],
        optimal_contact_time=datetime.now(),
        expected_conversion_timeline='3 weeks',
        risk_factors=['Budget tight'],
        opportunity_signals=['High engagement']
    )

@pytest.fixture
def mock_enhanced_scorer_result():
    """Mock enhanced Claude scorer."""
    return UnifiedScoringResult(
        lead_id='test_lead_001',
        lead_name='Sarah Johnson',
        scored_at=datetime.now(),
        final_score=88.0,
        classification='hot',
        confidence_score=0.92,
        strategic_summary='High intent buyer',
        behavioral_insights='Active searcher',
        reasoning='Responded quickly to all touchpoints',
        risk_factors=[],
        opportunities=['Relocation candidate'],
        recommended_actions=['Prioritize follow-up'],
        next_best_action='Call today',
        expected_timeline='1 month',
        success_probability=0.85,
        analysis_time_ms=250,
        claude_reasoning_time_ms=120.0,
        jorge_score=85.0,
        ml_conversion_score=0.82,
        churn_risk_score=0.15,
        engagement_score=0.9,
        frs_score=0.88,
        pcs_score=0.85,
        feature_breakdown={},
        conversation_context={},
        sources=['ghl', 'website']
    )

@pytest_asyncio.fixture
async def ai_integration_service(mock_claude_client, mock_database_service, mock_cache_service,
                                 mock_enhanced_scorer_result):
    """Initialize Service6EnhancedClaudePlatformCompanion with mocks."""
    config = Service6AIConfig(
        enable_advanced_ml_scoring=True,
        enable_voice_ai=True,
        enable_predictive_analytics=True,
        enable_claude_enhancement=True
    )
    
    with patch('ghl_real_estate_ai.services.service6_ai_integration.create_advanced_ml_scoring_engine') as mock_ml_engine, \
         patch('ghl_real_estate_ai.services.service6_ai_integration.create_voice_ai_integration') as mock_voice_ai, \
         patch('ghl_real_estate_ai.services.service6_ai_integration.create_predictive_analytics_engine') as mock_predictive, \
         patch('ghl_real_estate_ai.services.service6_ai_integration.create_realtime_inference_engine') as mock_inference, \
         patch('ghl_real_estate_ai.services.service6_ai_integration.create_mlops_pipeline') as mock_mlops, \
         patch('ghl_real_estate_ai.services.service6_ai_integration.ClaudeEnhancedLeadScorer') as mock_scorer_class, \
         patch('ghl_real_estate_ai.services.service6_ai_integration.TieredCacheService', return_value=mock_cache_service), \
         patch('ghl_real_estate_ai.services.service6_ai_integration.MemoryService') as mock_memory_class:
        
        # Configure mocks to handle await
        mock_inference.return_value.start = AsyncMock()
        mock_mlops.return_value.start_background_monitoring = AsyncMock()
        
        mock_memory = mock_memory_class.return_value
        mock_memory.get_context = AsyncMock(return_value={})
        mock_memory.save_context = AsyncMock()
        
        mock_scorer = mock_scorer_class.return_value
        mock_scorer.analyze_lead_comprehensive = AsyncMock(return_value=mock_enhanced_scorer_result)
        
        service = Service6EnhancedClaudePlatformCompanion(config)
        # Manually set mocks that might have been initialized in __init__
        service.cache = mock_cache_service
        
        await service.initialize()
        return service

class TestService6AIIntegration:
    """Tests for the Service 6 AI Integration layer."""

    @pytest.mark.asyncio
    async def test_comprehensive_lead_analysis_success(self, ai_integration_service, sample_lead_data, 
                                                     mock_ml_result):
        """Test successful comprehensive lead analysis."""
        
        # Mock underlying components
        ai_integration_service.ml_scoring_engine.score_lead_comprehensive = AsyncMock(return_value=mock_ml_result)
        ai_integration_service.predictive_analytics.run_comprehensive_analysis = AsyncMock(return_value={
            'confidence_score': 0.85,
            'behavioral_patterns': ['Evening browser'],
            'comprehensive_insights': {'risks': [], 'opportunities': ['Ready to buy'], 'actions': []}
        })
        
        # Mock personalization
        mock_content = MagicMock()
        mock_content.engagement_probability = 0.85
        mock_content.content_type = 'email'
        mock_content.channel_optimization = 'email'
        mock_content.optimal_send_time = datetime.now()
        ai_integration_service.predictive_analytics.content_personalization.generate_personalized_content = AsyncMock(return_value=mock_content)
    
        # Execute
        result = await ai_integration_service.comprehensive_lead_analysis(
            'test_lead_001', sample_lead_data
        )        
        # Assert
        assert isinstance(result, Service6AIResponse)
        assert result.lead_id == 'test_lead_001'
        assert result.unified_lead_score > 0
        assert result.confidence_level > 0.7
        assert 'advanced_ml_scorer' in result.models_used
        assert 'predictive_analytics' in result.models_used
        
        # Verify caching
        ai_integration_service.cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_comprehensive_analysis_scoring_failure(self, ai_integration_service, sample_lead_data):
        """Test that specific scoring errors propagate and are not swallowed."""
        
        # Make ML scoring fail with specific error
        ai_integration_service.ml_scoring_engine.score_lead_comprehensive = AsyncMock(
            side_effect=Exception("Database connection timed out")
        )
        
        # Execute and expect AIScoringError (wrapped by our service)
        with pytest.raises(AIScoringError) as excinfo:
            await ai_integration_service.comprehensive_lead_analysis(
                'test_lead_001', sample_lead_data
            )
        
        assert "ML scoring analysis failed" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_comprehensive_analysis_no_engines_error(self, ai_integration_service, sample_lead_data):
        """Test that AIScoringError is raised when no engines are available."""
        
        # Disable all scoring engines in the service
        ai_integration_service.ml_scoring_engine = None
        ai_integration_service.enhanced_scorer = None
        
        # Mock other tasks to return results
        ai_integration_service._run_voice_analysis = AsyncMock(return_value=None)
        ai_integration_service._run_predictive_analysis = AsyncMock(return_value={})
        
        # Execute and expect AIScoringError
        with pytest.raises(AIScoringError) as excinfo:
            await ai_integration_service.comprehensive_lead_analysis(
                'test_lead_001', sample_lead_data
            )
        
        assert "No scoring engines available" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_tiered_cache_usage(self, ai_integration_service, sample_lead_data, mock_ml_result):
        """Test that the system uses TieredCacheService."""
        
        # 1. First call - Cache miss
        ai_integration_service.ml_scoring_engine.score_lead_comprehensive = AsyncMock(return_value=mock_ml_result)
        ai_integration_service.predictive_analytics.run_comprehensive_analysis = AsyncMock(return_value={})
        
        await ai_integration_service.comprehensive_lead_analysis('test_lead_001', sample_lead_data)
        
        # Verify cache was set
        assert ai_integration_service.cache.set.called
        
        # 2. Mock a cache hit for the next call
        cached_response = Service6AIResponse(
            operation_id='cached_op',
            lead_id='test_lead_001',
            timestamp=datetime.now(),
            ml_scoring_result=mock_ml_result,
            voice_analysis_result=None,
            predictive_insights={},
            personalized_content=None,
            unified_lead_score=85.0,
            confidence_level=0.9,
            priority_level='high',
            immediate_actions=[],
            strategic_recommendations=[],
            risk_alerts=[],
            opportunity_signals=[],
            processing_time_ms=10.0,
            models_used=['cached_model'],
            data_sources=[],
            enhanced_claude_integration=True,
            realtime_inference_active=True,
            voice_ai_enabled=True
        )
        
        # Note: In real usage we'd use the orchestrator which handles the cache check
        orchestrator = Service6AIOrchestrator()
        orchestrator.ai_companion = ai_integration_service
        
        # Mock orchestrator behavior (it would check cache)
        with patch.object(ai_integration_service.cache, 'get', return_value=asdict(cached_response)):
            # This is a bit of a placeholder since the orchestrator logic 
            # currently just delegates to companion.
            # Real implementation of cache-first logic often lives in the orchestrator.
            pass

    @pytest.mark.asyncio
    async def test_enhanced_claude_conversation(self, ai_integration_service):
        """Test enhanced Claude conversation with AI insights."""
        
        # Mock memory and cache
        ai_integration_service.cache.get = AsyncMock(return_value={'unified_lead_score': 88.0})
        ai_integration_service.memory.get_context = AsyncMock(return_value={'lead_id': 'test_lead_001'})
        
        # Mock the generation methods
        ai_integration_service.generate_intelligent_response = AsyncMock(return_value="Claude's smart response")
        
        result = await ai_integration_service.claude_enhanced_conversation(
            'test_lead_001', "What should I do next?", []
        )
        
        assert result['ai_enhanced'] is True
        assert result['response'] == "Claude's smart response"
        assert result['lead_score'] == 88.0

class TestService6Orchestrator:
    """Tests for the high-level Service6AIOrchestrator."""

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, mock_cache_service):
        """Test orchestrator initialization starts all sub-services."""
        
        with patch('ghl_real_estate_ai.services.service6_ai_integration.Service6EnhancedClaudePlatformCompanion') as mock_companion_class:
            mock_companion = mock_companion_class.return_value
            mock_companion.initialize = AsyncMock()
            
            orchestrator = Service6AIOrchestrator()
            await orchestrator.initialize()
            
            mock_companion.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_orchestrator_analyze_lead(self, ai_integration_service, sample_lead_data):
        """Test orchestrator analyze_lead delegation."""
        
        orchestrator = Service6AIOrchestrator()
        orchestrator.ai_companion = ai_integration_service
        
        # Mock companion method
        mock_response = MagicMock(spec=Service6AIResponse)
        ai_integration_service.comprehensive_lead_analysis = AsyncMock(return_value=mock_response)
        
        result = await orchestrator.analyze_lead('test_lead_001', sample_lead_data)
        
        assert result == mock_response
        ai_integration_service.comprehensive_lead_analysis.assert_called_once()
        assert orchestrator.operation_metrics['analyze_lead'] == 1
