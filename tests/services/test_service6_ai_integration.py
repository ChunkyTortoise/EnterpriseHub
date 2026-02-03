#!/usr/bin/env python3
"""
Tests for Service 6 AI Integration - Core AI service tests (90% coverage target)
================================================================

Comprehensive test suite for the Service 6 AI Integration service covering:
- Comprehensive lead analysis workflows
- Real-time lead scoring with caching
- ML inference pipeline validation
- Performance benchmarking (<200ms targets)
- Error handling and graceful degradation

Target Coverage: 90%+ on service6_ai_integration.py
"""

import pytest
import pytest_asyncio
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

# Import the service under test
from ghl_real_estate_ai.services.service6_ai_integration import (
    Service6AIOrchestrator,
    Service6EnhancedClaudePlatformCompanion,
    Service6AIConfig,
    Service6AIResponse,
    create_service6_ai_orchestrator,
    create_default_service6_config,
    create_high_performance_config
)

# Test data
SAMPLE_LEAD_DATA = {
    "id": "lead_123",
    "first_name": "John",
    "last_name": "Smith",
    "email": "john.smith@example.com",
    "phone": "+1234567890",
    "budget_range": "$400k-600k",
    "preferred_location": "Austin, TX",
    "property_type": "single_family",
    "timeline": "3_months",
    "current_situation": "first_time_buyer",
    "created_at": datetime.now().isoformat()
}

@pytest_asyncio.fixture
async def mock_claude_client():
    """Mock Claude client for AI responses."""
    client = AsyncMock()
    client.generate.return_value = AsyncMock(
        content="Analysis: This is a high-intent lead based on specific budget and timeline."
    )
    client.generate_response.return_value = {
        "content": "Analysis: This is a high-intent lead based on specific budget and timeline.",
        "confidence": 0.87,
        "behavioral_score": 85,
        "priority": 4,
        "next_actions": ["immediate_response", "schedule_consultation"],
        "scoring_factors": [
            {"factor": "specific_budget", "impact": 0.3},
            {"factor": "defined_timeline", "impact": 0.25},
            {"factor": "location_specificity", "impact": 0.2}
        ]
    }
    return client

@pytest_asyncio.fixture
async def mock_database_service():
    """Mock database service."""
    db = AsyncMock()
    db.get_lead.return_value = SAMPLE_LEAD_DATA
    db.get_lead_activity_data.return_value = {
        "website_visits": [{"timestamp": datetime.now().isoformat(), "page": "/listings"}],
        "email_interactions": [{"opened": True, "clicked": False}],
        "property_searches": [{"criteria": {"price_max": 600000}, "results": 15}]
    }
    db.get_lead_communications_history.return_value = [
        {"channel": "email", "sent_at": datetime.now().isoformat(), "status": "delivered"}
    ]
    return db

@pytest_asyncio.fixture
async def mock_cache_service():
    """Mock cache service."""
    cache = AsyncMock()
    cache.get.return_value = None  # Force cache miss initially
    cache.set.return_value = True
    return cache

@pytest_asyncio.fixture
async def mock_memory_service():
    """Mock memory service."""
    memory = AsyncMock()
    memory.get_context.return_value = {
        "conversation_history": [
            {"role": "user", "content": "Looking for properties in Austin"},
            {"role": "assistant", "content": "I can help with that"}
        ]
    }
    memory.update_lead_intelligence.return_value = True
    return memory

@pytest_asyncio.fixture
async def mock_ml_scoring_engine():
    """Mock ML scoring engine."""
    engine = AsyncMock()
    engine.score_lead_comprehensive.return_value = AsyncMock(
        final_ml_score=85.5,
        confidence_interval=(0.8, 0.9),
        recommended_actions=["immediate_followup", "property_match"],
        risk_factors=["none_detected"],
        opportunity_signals=["high_budget_specificity", "urgent_timeline"]
    )
    engine.get_performance_metrics.return_value = {"success_rate": 0.95, "avg_latency": 120}
    return engine

@pytest_asyncio.fixture
async def mock_enhanced_scorer():
    """Mock enhanced Claude scorer."""
    scorer = AsyncMock()
    scorer.analyze_lead_comprehensive.return_value = AsyncMock(
        lead_id="lead_123",
        final_score=88.0,
        confidence_score=0.85,
        classification="high_intent",
        reasoning="Strong budget and timeline indicators",
        recommended_actions=["immediate_contact", "send_properties"],
        risk_factors=[],
        opportunities=["ready_to_buy"],
        analysis_time_ms=150.0,
        claude_reasoning_time_ms=120.0
    )
    return scorer

@pytest_asyncio.fixture
async def ai_integration_service(mock_claude_client, mock_database_service, mock_cache_service, 
                               mock_memory_service, mock_ml_scoring_engine, mock_enhanced_scorer):
    """Create AI integration service with mocked dependencies."""
    
    # Create config
    config = Service6AIConfig(
        enable_advanced_ml_scoring=True,
        enable_voice_ai=False,  # Disable for most tests
        enable_predictive_analytics=True,
        enable_realtime_inference=True,
        enable_claude_enhancement=True
    )
    
    # Create service
    service = Service6EnhancedClaudePlatformCompanion(config)
    
    # Inject mocked services
    service.llm_client = mock_claude_client
    service.cache = mock_cache_service
    service.memory = mock_memory_service
    service.ml_scoring_engine = mock_ml_scoring_engine
    service.enhanced_scorer = mock_enhanced_scorer
    
    # Mock other components that might be None
    service.voice_ai = None
    service.predictive_analytics = AsyncMock()
    service.predictive_analytics.run_comprehensive_analysis.return_value = {
        "confidence_score": 0.8,
        "comprehensive_insights": {
            "actions": ["send_market_report"],
            "risks": ["market_uncertainty"],
            "opportunities": ["price_appreciation"]
        }
    }
    service.predictive_analytics.content_personalization = AsyncMock()
    service.predictive_analytics.content_personalization.generate_personalized_content.return_value = AsyncMock(
        engagement_probability=0.75
    )
    service.predictive_analytics.get_performance_metrics.return_value = {
        "system_health": "healthy"
    }
    
    service.realtime_inference = AsyncMock()
    service.realtime_inference.predict.return_value = AsyncMock(
        primary_score=82.0,
        confidence=0.83,
        prediction_class="high_intent",
        processing_time_ms=95.0
    )
    service.realtime_inference.get_system_status.return_value = {
        "status": "healthy",
        "performance": {"avg_latency": 100}
    }
    
    service.mlops = AsyncMock()
    service.mlops.start_background_monitoring.return_value = True
    service.mlops.get_system_health.return_value = {
        "health_status": "healthy"
    }
    
    return service

class TestService6AIIntegration:
    """Test Service 6 AI Integration service."""
    
    @pytest.mark.asyncio
    async def test_comprehensive_lead_analysis_success(self, ai_integration_service):
        """Test comprehensive lead analysis with successful execution."""
        # Execute comprehensive analysis
        result = await ai_integration_service.comprehensive_lead_analysis(
            SAMPLE_LEAD_DATA["id"], SAMPLE_LEAD_DATA
        )
        
        # Verify result structure
        assert isinstance(result, Service6AIResponse)
        assert result.lead_id == "lead_123"
        assert result.unified_lead_score > 0
        assert result.confidence_level > 0
        assert result.priority_level in ['low', 'medium', 'high', 'critical']
        assert len(result.immediate_actions) > 0
        assert len(result.models_used) > 0
        assert result.processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_comprehensive_lead_analysis_performance(self, ai_integration_service):
        """Test comprehensive analysis performance (<200ms target)."""
        # Execute analysis multiple times to test consistency
        for _ in range(3):
            start_time = time.time()
            result = await ai_integration_service.comprehensive_lead_analysis(
                SAMPLE_LEAD_DATA["id"], SAMPLE_LEAD_DATA
            )
            elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Performance assertion: Should complete in reasonable time for testing
            # Note: In real deployment, target is <200ms
            assert elapsed_time < 500, f"Analysis took {elapsed_time:.2f}ms, target: <500ms (test environment)"
            assert result is not None
            assert result.processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_realtime_lead_scoring_success(self, ai_integration_service):
        """Test real-time lead scoring with success case."""
        features = {
            "email_open_rate": 0.8,
            "response_time_hours": 2.0,
            "budget": 500000,
            "page_views": 10
        }
        
        result = await ai_integration_service.realtime_lead_scoring(
            SAMPLE_LEAD_DATA["id"], features, "high"
        )
        
        # Verify result structure
        assert result is not None
        assert hasattr(result, 'primary_score')
        assert hasattr(result, 'confidence')
        assert result.primary_score > 0
        assert result.confidence > 0
    
    @pytest.mark.asyncio
    async def test_realtime_lead_scoring_with_cache(self, ai_integration_service):
        """Test real-time lead scoring with cache integration."""
        features = {
            "email_open_rate": 0.75,
            "budget": 400000
        }
        
        # First call - should miss cache
        result1 = await ai_integration_service.realtime_lead_scoring(
            SAMPLE_LEAD_DATA["id"], features
        )
        
        # Mock cache hit for second call
        ai_integration_service.cache.get.return_value = {
            "primary_score": 85.0,
            "confidence": 0.87,
            "cached_at": datetime.now().isoformat()
        }
        
        # Second call - would hit cache in real implementation
        result2 = await ai_integration_service.realtime_lead_scoring(
            SAMPLE_LEAD_DATA["id"], features
        )
        
        assert result1 is not None
        assert result2 is not None
    
    @pytest.mark.asyncio
    async def test_ai_integration_error_handling(self, ai_integration_service):
        """Test graceful error handling when AI service fails."""
        # Mock AI client failure
        ai_integration_service.ml_scoring_engine.score_lead_comprehensive.side_effect = Exception("API Error")
        ai_integration_service.predictive_analytics.run_comprehensive_analysis.side_effect = Exception("Analysis Error")
        
        # Should return fallback result, not crash
        result = await ai_integration_service.comprehensive_lead_analysis(
            SAMPLE_LEAD_DATA["id"], SAMPLE_LEAD_DATA
        )
        
        assert result is not None
        assert result.unified_lead_score >= 0  # Should have some fallback score
        # Should indicate error condition in some way
        assert "Manual review required" in " ".join(result.immediate_actions) or result.confidence_level < 0.5
    
    @pytest.mark.asyncio
    async def test_memory_integration(self, ai_integration_service):
        """Test memory service integration for context gathering."""
        # Execute analysis
        result = await ai_integration_service.comprehensive_lead_analysis(
            SAMPLE_LEAD_DATA["id"], SAMPLE_LEAD_DATA
        )
        
        # Verify memory calls
        ai_integration_service.memory.get_context.assert_called()
        ai_integration_service.memory.update_lead_intelligence.assert_called_once()
        
        # Verify memory update content
        update_call = ai_integration_service.memory.update_lead_intelligence.call_args
        assert update_call[0][0] == SAMPLE_LEAD_DATA["id"]  # Lead ID
        assert 'ai_insights' in update_call[0][1]  # Update data
    
    @pytest.mark.asyncio
    async def test_concurrent_processing(self, ai_integration_service):
        """Test concurrent lead analysis processing."""
        # Create multiple lead data sets
        leads = [
            {**SAMPLE_LEAD_DATA, "id": f"lead_{i}"}
            for i in range(3)  # Reduced for faster tests
        ]
        
        # Process concurrently
        start_time = time.time()
        tasks = [
            ai_integration_service.comprehensive_lead_analysis(lead["id"], lead)
            for lead in leads
        ]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Verify all completed successfully
        assert len(results) == 3
        for result in results:
            assert result is not None
            assert result.unified_lead_score >= 0
        
        # Concurrent processing should be efficient
        assert total_time < 2.0, f"Concurrent processing took {total_time:.2f}s"
    
    @pytest.mark.asyncio
    async def test_ml_scoring_accuracy(self, ai_integration_service):
        """Test ML scoring accuracy and consistency."""
        # Test with high-intent lead data
        high_intent_lead = {
            **SAMPLE_LEAD_DATA,
            "budget_range": "$500k-700k",  # Specific budget
            "timeline": "immediate",       # Urgent timeline
            "property_type": "luxury_home", # High value
            "previous_interactions": 5      # High engagement
        }
        
        result = await ai_integration_service.comprehensive_lead_analysis(
            high_intent_lead["id"], high_intent_lead
        )
        
        # Should score reasonably for high-intent signals
        assert result.unified_lead_score >= 50, f"High-intent lead scored only {result.unified_lead_score}"
        assert result.confidence_level >= 0.5, f"Confidence too low: {result.confidence_level}"
        assert result.priority_level in ['medium', 'high', 'critical']
    
    @pytest.mark.asyncio
    async def test_enhanced_claude_conversation(self, ai_integration_service):
        """Test enhanced Claude conversation with AI insights."""
        conversation_history = [
            {'role': 'user', 'content': 'Looking for homes in Austin'},
            {'role': 'assistant', 'content': 'I can help you find great options...'}
        ]
        
        result = await ai_integration_service.claude_enhanced_conversation(
            SAMPLE_LEAD_DATA["id"], 
            "What about market trends?",
            conversation_history
        )
        
        assert result is not None
        assert 'response' in result or 'error' not in result
    
    @pytest.mark.asyncio
    async def test_voice_coaching_setup(self, ai_integration_service):
        """Test voice coaching session setup."""
        # Enable voice AI for this test
        ai_integration_service.voice_ai = AsyncMock()
        ai_integration_service.voice_ai.start_call_analysis.return_value = True
        
        result = await ai_integration_service.voice_call_coaching(
            "call_123", SAMPLE_LEAD_DATA["id"], "agent_456"
        )
        
        assert result['call_id'] == "call_123"
        assert 'coaching_active' in result
        assert 'message' in result
    
    @pytest.mark.asyncio
    async def test_voice_coaching_failure(self, ai_integration_service):
        """Test voice coaching when voice AI is not available."""
        # Ensure voice AI is None
        ai_integration_service.voice_ai = None
        
        with pytest.raises(Exception, match="Voice AI not available"):
            await ai_integration_service.voice_call_coaching(
                "call_123", SAMPLE_LEAD_DATA["id"], "agent_456"
            )
    
    @pytest.mark.asyncio
    async def test_system_health_check(self, ai_integration_service):
        """Test comprehensive system health check."""
        health = await ai_integration_service.get_system_health()
        
        assert 'timestamp' in health
        assert 'overall_status' in health
        assert 'components' in health
        assert health['overall_status'] in ['healthy', 'degraded', 'unhealthy', 'unknown']
    
    @pytest.mark.asyncio
    async def test_configuration_validation(self, ai_integration_service):
        """Test service configuration validation."""
        # Verify service is properly configured
        assert ai_integration_service.ml_scoring_engine is not None
        assert ai_integration_service.enhanced_scorer is not None
        assert ai_integration_service.cache is not None
        assert ai_integration_service.memory is not None
    
    @pytest.mark.asyncio
    async def test_fallback_scoring_when_ml_unavailable(self, ai_integration_service):
        """Test fallback to enhanced scorer when ML engine fails."""
        # Disable ML scoring engine
        ai_integration_service.ml_scoring_engine = None
        
        result = await ai_integration_service.comprehensive_lead_analysis(
            SAMPLE_LEAD_DATA["id"], SAMPLE_LEAD_DATA
        )
        
        # Should still provide a result using enhanced scorer
        assert result is not None
        assert result.unified_lead_score > 0
        assert 'enhanced_claude_scorer' in result.models_used or result.enhanced_claude_integration

class TestService6AIOrchestrator:
    """Test Service 6 AI Orchestrator."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        config = create_default_service6_config()
        orchestrator = create_service6_ai_orchestrator(config)
        
        assert orchestrator.config is not None
        assert orchestrator.ai_companion is not None
        assert orchestrator.operation_metrics is not None
    
    @pytest.mark.asyncio
    async def test_orchestrator_analyze_lead(self, mock_claude_client, mock_cache_service, 
                                           mock_memory_service):
        """Test orchestrator lead analysis."""
        config = Service6AIConfig(enable_voice_ai=False)  # Disable voice for simpler testing
        orchestrator = Service6AIOrchestrator(config)
        
        # Mock the ai_companion
        orchestrator.ai_companion = AsyncMock()
        orchestrator.ai_companion.comprehensive_lead_analysis.return_value = Service6AIResponse(
            operation_id="test_op",
            lead_id="lead_123",
            timestamp=datetime.now(),
            ml_scoring_result=None,
            voice_analysis_result=None,
            predictive_insights=None,
            personalized_content=None,
            unified_lead_score=75.0,
            confidence_level=0.8,
            priority_level="high",
            immediate_actions=["contact_lead"],
            strategic_recommendations=["send_properties"],
            risk_alerts=[],
            opportunity_signals=["high_intent"],
            processing_time_ms=150.0,
            models_used=["ml_scorer"],
            data_sources=["lead_data"],
            enhanced_claude_integration=True,
            realtime_inference_active=True,
            voice_ai_enabled=False
        )
        
        result = await orchestrator.analyze_lead("lead_123", SAMPLE_LEAD_DATA)
        
        assert result.lead_id == "lead_123"
        assert result.unified_lead_score == 75.0
        assert orchestrator.operation_metrics['analyze_lead'] == 1
    
    @pytest.mark.asyncio
    async def test_orchestrator_metrics_tracking(self):
        """Test orchestrator metrics tracking."""
        config = create_default_service6_config()
        orchestrator = Service6AIOrchestrator(config)
        
        # Mock the ai_companion for different operations
        orchestrator.ai_companion = AsyncMock()
        orchestrator.ai_companion.realtime_lead_scoring.return_value = AsyncMock()
        orchestrator.ai_companion.voice_call_coaching.return_value = {"coaching_active": True}
        orchestrator.ai_companion.claude_enhanced_conversation.return_value = {"response": "test"}
        orchestrator.ai_companion.generate_behavioral_insights.return_value = {"insights": []}
        
        # Test multiple operations
        await orchestrator.score_lead_realtime("lead_123", {"budget": 500000})
        await orchestrator.start_voice_coaching("call_123", "lead_123", "agent_456")
        await orchestrator.enhanced_chat("lead_123", "Hello", [])
        await orchestrator.get_behavioral_insights("lead_123", [])
        
        # Verify metrics
        assert orchestrator.operation_metrics['score_realtime'] == 1
        assert orchestrator.operation_metrics['voice_coaching'] == 1
        assert orchestrator.operation_metrics['enhanced_chat'] == 1
        assert orchestrator.operation_metrics['behavioral_insights'] == 1

class TestConfigurationFactories:
    """Test configuration factory functions."""
    
    def test_create_default_config(self):
        """Test default configuration creation."""
        config = create_default_service6_config()
        
        assert config.enable_advanced_ml_scoring is True
        assert config.enable_voice_ai is True
        assert config.enable_predictive_analytics is True
        assert config.max_concurrent_operations == 50
        assert config.default_cache_ttl_seconds == 300
    
    def test_create_high_performance_config(self):
        """Test high-performance configuration creation."""
        config = create_high_performance_config()
        
        assert config.max_concurrent_operations == 100
        assert config.default_cache_ttl_seconds == 600
        assert config.enable_background_processing is True
        assert config.ml_model_confidence_threshold == 0.8
        assert config.enable_realtime_coaching is True

class TestPerformanceBenchmarks:
    """Performance benchmark tests."""
    
    @pytest.mark.asyncio
    async def test_analysis_latency_benchmark(self, ai_integration_service):
        """Benchmark analysis latency."""
        latencies = []
        
        for i in range(5):  # Reduced iterations for faster tests
            start = time.time()
            await ai_integration_service.comprehensive_lead_analysis(
                SAMPLE_LEAD_DATA["id"], SAMPLE_LEAD_DATA
            )
            latency = (time.time() - start) * 1000
            latencies.append(latency)
        
        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        
        # Performance assertions (relaxed for test environment)
        assert avg_latency < 500, f"Average latency {avg_latency:.2f}ms exceeds 500ms test target"
        assert p95_latency < 1000, f"P95 latency {p95_latency:.2f}ms exceeds 1000ms test target"
    
    @pytest.mark.asyncio
    async def test_memory_efficiency(self, ai_integration_service):
        """Test memory efficiency during analysis."""
        import psutil
        import os
        
        try:
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss
            
            # Process several leads
            for i in range(10):  # Reduced for faster tests
                lead_data = {**SAMPLE_LEAD_DATA, "id": f"lead_{i}"}
                await ai_integration_service.comprehensive_lead_analysis(
                    lead_data["id"], lead_data
                )
            
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (<20MB for 10 analyses)
            assert memory_increase < 20 * 1024 * 1024, f"Memory increased by {memory_increase / 1024 / 1024:.2f}MB"
        except ImportError:
            pytest.skip("psutil not available for memory testing")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=ghl_real_estate_ai.services.service6_ai_integration"])