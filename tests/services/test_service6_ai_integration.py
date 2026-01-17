#!/usr/bin/env python3
"""
Comprehensive tests for Service 6 AI Integration Layer.

Tests cover:
- Service6EnhancedClaudePlatformCompanion functionality
- Service6AIOrchestrator operations
- AI model integration (mocked)
- Caching and memory operations
- Error handling and fallback scenarios
- Performance and reliability metrics

Coverage Target: 90%+ for critical business logic paths
"""

import asyncio
import json
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

# Import the module under test
from ghl_real_estate_ai.services.service6_ai_integration import (
    Service6EnhancedClaudePlatformCompanion,
    Service6AIOrchestrator,
    Service6AIConfig,
    Service6AIResponse,
    create_service6_ai_orchestrator,
    create_default_service6_config,
    create_high_performance_config
)

# Import test utilities and mocks
from tests.mocks.external_services import (
    MockClaudeClient,
    MockRedisClient,
    MockDatabaseService,
    create_test_lead_data,
    create_mock_ml_scoring_result,
    create_mock_service6_response
)
from tests.fixtures.sample_data import (
    LeadProfiles,
    ConversationHistories,
    AnalyticsData
)


class TestService6AIConfig:
    """Test Service 6 AI configuration management"""
    
    def test_default_config_creation(self):
        """Test default configuration values"""
        config = create_default_service6_config()
        
        assert config.enable_advanced_ml_scoring is True
        assert config.enable_voice_ai is True
        assert config.enable_predictive_analytics is True
        assert config.enable_realtime_inference is True
        assert config.enable_claude_enhancement is True
        assert config.max_concurrent_operations == 50
        assert config.default_cache_ttl_seconds == 300
        assert config.ml_model_confidence_threshold == 0.7
        
    def test_high_performance_config_creation(self):
        """Test high-performance configuration values"""
        config = create_high_performance_config()
        
        assert config.max_concurrent_operations == 100
        assert config.default_cache_ttl_seconds == 600
        assert config.ml_model_confidence_threshold == 0.8
        assert config.voice_transcription_accuracy_threshold == 0.9
        assert config.enable_realtime_coaching is True
        
    def test_config_validation(self):
        """Test configuration parameter validation"""
        config = Service6AIConfig(
            max_concurrent_operations=200,
            ml_model_confidence_threshold=0.95,
            voice_transcription_accuracy_threshold=0.99
        )
        
        assert config.max_concurrent_operations == 200
        assert config.ml_model_confidence_threshold == 0.95
        assert config.voice_transcription_accuracy_threshold == 0.99


class TestService6EnhancedClaudePlatformCompanion:
    """Test the enhanced Claude Platform Companion"""
    
    @pytest.fixture
    async def companion(self):
        """Create companion instance with mocked dependencies"""
        config = create_default_service6_config()
        companion = Service6EnhancedClaudePlatformCompanion(config)
        
        # Mock external services
        companion.cache = MockRedisClient()
        companion.memory = MagicMock()
        companion.memory.get_context = AsyncMock(return_value={'conversation_history': []})
        companion.memory.update_lead_intelligence = AsyncMock(return_value=True)
        
        # Mock AI components
        companion.ml_scoring_engine = MagicMock()
        companion.ml_scoring_engine.score_lead_comprehensive = AsyncMock(
            return_value=create_mock_ml_scoring_result()
        )
        companion.ml_scoring_engine.get_performance_metrics = AsyncMock(
            return_value={'success_rate': 0.95, 'avg_latency_ms': 150}
        )
        
        companion.predictive_analytics = MagicMock()
        companion.predictive_analytics.run_comprehensive_analysis = AsyncMock(
            return_value={
                'confidence_score': 0.85,
                'comprehensive_insights': {
                    'actions': ['Schedule viewing', 'Send analysis'],
                    'risks': ['Market volatility'],
                    'opportunities': ['Quick decision maker']
                }
            }
        )
        companion.predictive_analytics.get_performance_metrics = AsyncMock(
            return_value={'system_health': 'healthy'}
        )
        
        companion.realtime_inference = MagicMock()
        companion.realtime_inference.start = AsyncMock(return_value=True)
        companion.realtime_inference.get_system_status = AsyncMock(
            return_value={'status': 'healthy', 'performance': {'latency': 50}}
        )
        
        companion.voice_ai = MagicMock()
        companion.voice_ai.get_performance_metrics = AsyncMock(
            return_value={'success_rate': 0.88}
        )
        
        companion.enhanced_scorer = MagicMock()
        companion.enhanced_scorer.analyze_lead_comprehensive = AsyncMock()
        
        companion.mlops = MagicMock()
        companion.mlops.start_background_monitoring = AsyncMock(return_value=True)
        companion.mlops.get_system_health = AsyncMock(
            return_value={'health_status': 'healthy'}
        )
        
        await companion.initialize()
        return companion
    
    @pytest.mark.asyncio
    async def test_initialization_success(self, companion):
        """Test successful initialization of all components"""
        # Verify initialization calls were made
        companion.realtime_inference.start.assert_called_once()
        companion.mlops.start_background_monitoring.assert_called_once()
        
        assert companion.cache is not None
        assert companion.memory is not None
    
    @pytest.mark.asyncio
    async def test_initialization_failure_handling(self):
        """Test initialization failure handling"""
        config = create_default_service6_config()
        companion = Service6EnhancedClaudePlatformCompanion(config)
        
        # Mock a failing initialization
        companion.realtime_inference = MagicMock()
        companion.realtime_inference.start = AsyncMock(side_effect=Exception("Connection failed"))
        
        with pytest.raises(Exception, match="Connection failed"):
            await companion.initialize()
    
    @pytest.mark.asyncio
    async def test_comprehensive_lead_analysis_success(self, companion):
        """Test successful comprehensive lead analysis"""
        lead_data = create_test_lead_data()
        
        result = await companion.comprehensive_lead_analysis(
            'test_lead_001', 
            lead_data,
            include_voice=False,
            include_predictive=True
        )
        
        # Verify result structure
        assert isinstance(result, Service6AIResponse)
        assert result.lead_id == 'test_lead_001'
        assert result.unified_lead_score > 0
        assert result.confidence_level > 0
        assert result.priority_level in ['critical', 'high', 'medium', 'low']
        assert len(result.immediate_actions) > 0
        assert result.processing_time_ms > 0
        
        # Verify AI components were called
        companion.ml_scoring_engine.score_lead_comprehensive.assert_called_once()
        companion.predictive_analytics.run_comprehensive_analysis.assert_called_once()
        
        # Verify caching
        cached_result = await companion.cache.get(f"s6_analysis:test_lead_001")
        assert cached_result is not None
        
    @pytest.mark.asyncio
    async def test_comprehensive_lead_analysis_with_voice(self, companion):
        """Test comprehensive analysis with voice data"""
        lead_data = create_test_lead_data()
        lead_data['call_data'] = {'call_id': 'test_call_123', 'duration': 180}
        
        result = await companion.comprehensive_lead_analysis(
            'test_lead_001',
            lead_data,
            include_voice=True
        )
        
        assert isinstance(result, Service6AIResponse)
        assert result.voice_ai_enabled is True
    
    @pytest.mark.asyncio 
    async def test_comprehensive_lead_analysis_ml_failure(self, companion):
        """Test analysis when ML scoring fails"""
        # Mock ML scoring failure
        companion.ml_scoring_engine.score_lead_comprehensive.side_effect = Exception("ML model unavailable")
        
        lead_data = create_test_lead_data()
        
        result = await companion.comprehensive_lead_analysis('test_lead_001', lead_data)
        
        # Should still return a result with fallback values
        assert isinstance(result, Service6AIResponse)
        assert result.ml_scoring_result is None
        assert result.unified_lead_score > 0  # Should use fallback scoring
        
    @pytest.mark.asyncio
    async def test_comprehensive_lead_analysis_complete_failure(self, companion):
        """Test analysis when all AI components fail"""
        # Mock all AI components to fail
        companion.ml_scoring_engine.score_lead_comprehensive.side_effect = Exception("ML failed")
        companion.predictive_analytics.run_comprehensive_analysis.side_effect = Exception("Analytics failed")
        companion.enhanced_scorer = None  # No fallback
        
        lead_data = create_test_lead_data()
        
        result = await companion.comprehensive_lead_analysis('test_lead_001', lead_data)
        
        # Should return minimal fallback response
        assert isinstance(result, Service6AIResponse)
        assert result.unified_lead_score == 50.0  # Neutral fallback
        assert result.confidence_level == 0.3
        assert result.priority_level == 'medium'
        assert "Manual review required" in result.immediate_actions[0]
        
    @pytest.mark.asyncio
    async def test_realtime_lead_scoring_success(self, companion):
        """Test successful real-time lead scoring"""
        from ghl_real_estate_ai.services.service6_ai_integration import InferenceResponse, RequestPriority
        
        # Mock successful inference
        mock_response = InferenceResponse(
            request_id="test_request",
            lead_id="test_lead_001",
            model_id="test_model",
            model_version="1.0",
            scores={'primary': 85.5},
            primary_score=85.5,
            confidence=0.92,
            prediction_class='high_value',
            feature_importance=None,
            reasoning=['Strong engagement signals'],
            risk_factors=[],
            opportunities=['Quick response time'],
            processed_at=datetime.now(),
            processing_time_ms=120.5,
            model_latency_ms=45.2,
            cache_hit=False,
            data_quality_score=0.95,
            prediction_uncertainty=0.08,
            requires_human_review=False
        )
        
        companion.realtime_inference.predict = AsyncMock(return_value=mock_response)
        
        features = {
            'email_open_rate': 0.85,
            'response_time_hours': 2.5,
            'budget': 550000
        }
        
        result = await companion.realtime_lead_scoring('test_lead_001', features, 'high')
        
        assert isinstance(result, InferenceResponse)
        assert result.primary_score == 85.5
        assert result.confidence == 0.92
        assert result.prediction_class == 'high_value'
        
        # Verify inference was called with correct parameters
        companion.realtime_inference.predict.assert_called_once()
        call_args = companion.realtime_inference.predict.call_args[0][0]
        assert call_args.lead_id == 'test_lead_001'
        assert call_args.features == features
        assert call_args.priority == RequestPriority.HIGH
        
    @pytest.mark.asyncio
    async def test_realtime_lead_scoring_fallback(self, companion):
        """Test real-time scoring fallback to enhanced scorer"""
        companion.realtime_inference = None  # Disable real-time inference
        
        # Mock enhanced scorer response
        mock_enhanced_result = MagicMock()
        mock_enhanced_result.lead_id = 'test_lead_001'
        mock_enhanced_result.final_score = 78.3
        mock_enhanced_result.confidence_score = 0.84
        mock_enhanced_result.classification = 'qualified'
        mock_enhanced_result.reasoning = 'Strong engagement metrics'
        mock_enhanced_result.risk_factors = []
        mock_enhanced_result.opportunities = ['High budget alignment']
        mock_enhanced_result.analysis_time_ms = 156.7
        mock_enhanced_result.claude_reasoning_time_ms = 89.2
        
        companion.enhanced_scorer.analyze_lead_comprehensive.return_value = mock_enhanced_result
        
        features = {'email_open_rate': 0.75}
        
        result = await companion.realtime_lead_scoring('test_lead_001', features)
        
        assert result.primary_score == 78.3
        assert result.confidence == 0.84
        assert result.prediction_class == 'qualified'
        
    @pytest.mark.asyncio
    async def test_realtime_lead_scoring_no_engines(self, companion):
        """Test real-time scoring when no engines are available"""
        companion.realtime_inference = None
        companion.enhanced_scorer = None
        
        features = {'email_open_rate': 0.75}
        
        with pytest.raises(Exception, match="No scoring engines available"):
            await companion.realtime_lead_scoring('test_lead_001', features)
    
    @pytest.mark.asyncio
    async def test_voice_call_coaching_success(self, companion):
        """Test successful voice call coaching initiation"""
        companion.voice_ai.start_call_analysis = AsyncMock(return_value=True)
        
        result = await companion.voice_call_coaching('call_123', 'lead_456', 'agent_789')
        
        assert result['call_id'] == 'call_123'
        assert result['coaching_active'] is True
        assert 'Real-time transcription' in result['features']
        
        companion.voice_ai.start_call_analysis.assert_called_once_with('call_123', 'lead_456', 'agent_789')
    
    @pytest.mark.asyncio
    async def test_voice_call_coaching_failure(self, companion):
        """Test voice call coaching failure"""
        companion.voice_ai.start_call_analysis = AsyncMock(return_value=False)
        
        result = await companion.voice_call_coaching('call_123', 'lead_456', 'agent_789')
        
        assert result['call_id'] == 'call_123'
        assert result['coaching_active'] is False
        assert 'Failed to start voice coaching' in result['message']
    
    @pytest.mark.asyncio
    async def test_voice_call_coaching_no_voice_ai(self, companion):
        """Test voice call coaching when voice AI is disabled"""
        companion.voice_ai = None
        
        with pytest.raises(Exception, match="Voice AI not available"):
            await companion.voice_call_coaching('call_123', 'lead_456', 'agent_789')
    
    @pytest.mark.asyncio
    async def test_process_voice_audio_stream(self, companion):
        """Test voice audio stream processing"""
        mock_result = {'transcription': 'Hello, I am interested...', 'sentiment': 'positive'}
        companion.voice_ai.process_audio_stream = AsyncMock(return_value=mock_result)
        
        audio_chunk = b'fake_audio_data'
        result = await companion.process_voice_audio_stream('call_123', audio_chunk, 'speaker_1')
        
        assert result == mock_result
        companion.voice_ai.process_audio_stream.assert_called_once_with('call_123', audio_chunk, 'speaker_1')
    
    @pytest.mark.asyncio
    async def test_generate_behavioral_insights(self, companion):
        """Test behavioral insights generation"""
        historical_context = [
            {'lead_id': 'hist_1', 'converted': True},
            {'lead_id': 'hist_2', 'converted': False}
        ]
        
        result = await companion.generate_behavioral_insights('test_lead_001', historical_context)
        
        assert 'confidence_score' in result
        companion.predictive_analytics.run_comprehensive_analysis.assert_called_with(
            {'lead_id': 'test_lead_001'}, 
            historical_context
        )
    
    @pytest.mark.asyncio
    async def test_claude_enhanced_conversation(self, companion):
        """Test enhanced Claude conversation"""
        # Mock cache result
        cached_analysis = create_mock_service6_response().__dict__
        await companion.cache.set('s6_analysis:test_lead_001', json.dumps(cached_analysis, default=str))
        
        # Mock enhanced scorer result
        mock_result = MagicMock()
        mock_result.final_score = 82.5
        mock_result.confidence_score = 0.89
        mock_result.recommended_actions = ['Action 1', 'Action 2', 'Action 3']
        
        companion.enhanced_scorer.analyze_lead_comprehensive.return_value = mock_result
        companion.generate_intelligent_response = AsyncMock(return_value="Intelligent Claude response")
        
        conversation_history = [
            {'role': 'user', 'content': 'Tell me about North Austin properties'}
        ]
        
        result = await companion.claude_enhanced_conversation(
            'test_lead_001', 
            'What about market conditions?',
            conversation_history
        )
        
        assert result['ai_enhanced'] is True
        assert result['lead_score'] == 82.5
        assert len(result['recommended_actions']) == 3
        assert result['confidence'] == 0.89
    
    @pytest.mark.asyncio
    async def test_claude_enhanced_conversation_fallback(self, companion):
        """Test Claude conversation fallback when enhancement fails"""
        companion.enhanced_scorer.analyze_lead_comprehensive.side_effect = Exception("Enhanced scorer failed")
        companion.generate_standard_response = AsyncMock(return_value={'response': 'Standard response'})
        
        conversation_history = [
            {'role': 'user', 'content': 'Hello'}
        ]
        
        result = await companion.claude_enhanced_conversation(
            'test_lead_001',
            'What about properties?', 
            conversation_history
        )
        
        assert result == {'response': 'Standard response'}
        companion.generate_standard_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_system_health_all_healthy(self, companion):
        """Test system health check when all components are healthy"""
        health = await companion.get_system_health()
        
        assert health['overall_status'] == 'healthy'
        assert 'components' in health
        assert 'timestamp' in health
        
        # Check individual component health
        components = health['components']
        assert 'ml_scoring' in components
        assert 'realtime_inference' in components
        assert 'voice_ai' in components
        assert 'predictive_analytics' in components
        assert 'mlops' in components
        
        # All components should be healthy
        for component_name, component_health in components.items():
            assert component_health['status'] in ['healthy', 'degraded']  # Allow degraded for some
    
    @pytest.mark.asyncio
    async def test_get_system_health_degraded(self, companion):
        """Test system health when components are degraded"""
        # Mock degraded component
        companion.ml_scoring_engine.get_performance_metrics.return_value = {'success_rate': 0.85}  # Below 0.9
        
        health = await companion.get_system_health()
        
        assert health['overall_status'] == 'degraded'
        assert health['components']['ml_scoring']['status'] == 'degraded'
    
    @pytest.mark.asyncio
    async def test_get_system_health_failure(self, companion):
        """Test system health check failure handling"""
        companion.ml_scoring_engine.get_performance_metrics.side_effect = Exception("Health check failed")
        
        health = await companion.get_system_health()
        
        assert health['overall_status'] == 'degraded'
        assert 'error' in health


class TestService6AIOrchestrator:
    """Test the Service 6 AI orchestrator"""
    
    @pytest.fixture
    async def orchestrator(self):
        """Create orchestrator instance with mocked companion"""
        config = create_default_service6_config()
        orchestrator = Service6AIOrchestrator(config)
        
        # Mock the AI companion
        orchestrator.ai_companion = MagicMock()
        orchestrator.ai_companion.initialize = AsyncMock()
        orchestrator.ai_companion.comprehensive_lead_analysis = AsyncMock(
            return_value=create_mock_service6_response()
        )
        orchestrator.ai_companion.realtime_lead_scoring = AsyncMock()
        orchestrator.ai_companion.voice_call_coaching = AsyncMock()
        orchestrator.ai_companion.claude_enhanced_conversation = AsyncMock()
        orchestrator.ai_companion.generate_behavioral_insights = AsyncMock()
        orchestrator.ai_companion.get_system_health = AsyncMock(
            return_value={'overall_status': 'healthy', 'components': {}}
        )
        
        await orchestrator.initialize()
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization"""
        orchestrator.ai_companion.initialize.assert_called_once()
        assert orchestrator.config is not None
        assert orchestrator.operation_metrics is not None
        assert orchestrator.start_time is not None
    
    @pytest.mark.asyncio
    async def test_analyze_lead(self, orchestrator):
        """Test lead analysis through orchestrator"""
        lead_data = create_test_lead_data()
        
        result = await orchestrator.analyze_lead('test_lead_001', lead_data, include_voice=True)
        
        assert isinstance(result, Service6AIResponse)
        assert orchestrator.operation_metrics['analyze_lead'] == 1
        
        orchestrator.ai_companion.comprehensive_lead_analysis.assert_called_once_with(
            'test_lead_001', lead_data, include_voice=True
        )
    
    @pytest.mark.asyncio
    async def test_score_lead_realtime(self, orchestrator):
        """Test real-time lead scoring through orchestrator"""
        features = {'email_open_rate': 0.85, 'budget': 500000}
        
        await orchestrator.score_lead_realtime('test_lead_001', features, 'high')
        
        assert orchestrator.operation_metrics['score_realtime'] == 1
        
        orchestrator.ai_companion.realtime_lead_scoring.assert_called_once_with(
            'test_lead_001', features, 'high'
        )
    
    @pytest.mark.asyncio
    async def test_start_voice_coaching(self, orchestrator):
        """Test voice coaching initiation through orchestrator"""
        await orchestrator.start_voice_coaching('call_123', 'lead_456', 'agent_789')
        
        assert orchestrator.operation_metrics['voice_coaching'] == 1
        
        orchestrator.ai_companion.voice_call_coaching.assert_called_once_with(
            'call_123', 'lead_456', 'agent_789'
        )
    
    @pytest.mark.asyncio
    async def test_enhanced_chat(self, orchestrator):
        """Test enhanced chat through orchestrator"""
        conversation_history = [{'role': 'user', 'content': 'Hello'}]
        
        await orchestrator.enhanced_chat('test_lead_001', 'What about properties?', conversation_history)
        
        assert orchestrator.operation_metrics['enhanced_chat'] == 1
        
        orchestrator.ai_companion.claude_enhanced_conversation.assert_called_once_with(
            'test_lead_001', 'What about properties?', conversation_history
        )
    
    @pytest.mark.asyncio
    async def test_get_behavioral_insights(self, orchestrator):
        """Test behavioral insights through orchestrator"""
        historical_context = [{'lead_id': 'hist_1'}]
        
        await orchestrator.get_behavioral_insights('test_lead_001', historical_context)
        
        assert orchestrator.operation_metrics['behavioral_insights'] == 1
        
        orchestrator.ai_companion.generate_behavioral_insights.assert_called_once_with(
            'test_lead_001', historical_context
        )
    
    @pytest.mark.asyncio
    async def test_get_system_status(self, orchestrator):
        """Test system status retrieval through orchestrator"""
        # Wait a bit to ensure uptime calculation
        await asyncio.sleep(0.1)
        
        status = await orchestrator.get_system_status()
        
        assert 'service6_ai_orchestrator' in status
        assert 'ai_components' in status
        
        orchestrator_status = status['service6_ai_orchestrator']
        assert orchestrator_status['status'] == 'running'
        assert orchestrator_status['uptime_hours'] > 0
        assert 'operations_processed' in orchestrator_status
        assert 'config' in orchestrator_status
    
    @pytest.mark.asyncio
    async def test_multiple_operations_metrics(self, orchestrator):
        """Test operation metrics tracking across multiple calls"""
        lead_data = create_test_lead_data()
        
        # Perform multiple operations
        await orchestrator.analyze_lead('lead_1', lead_data)
        await orchestrator.analyze_lead('lead_2', lead_data)
        await orchestrator.score_lead_realtime('lead_1', {'budget': 500000})
        
        assert orchestrator.operation_metrics['analyze_lead'] == 2
        assert orchestrator.operation_metrics['score_realtime'] == 1
        
        status = await orchestrator.get_system_status()
        ops = status['service6_ai_orchestrator']['operations_processed']
        
        assert ops['analyze_lead'] == 2
        assert ops['score_realtime'] == 1


class TestFactoryFunctions:
    """Test factory functions for creating Service 6 instances"""
    
    def test_create_service6_ai_orchestrator_default(self):
        """Test creating orchestrator with default config"""
        orchestrator = create_service6_ai_orchestrator()
        
        assert isinstance(orchestrator, Service6AIOrchestrator)
        assert isinstance(orchestrator.config, Service6AIConfig)
        assert orchestrator.config.enable_advanced_ml_scoring is True
    
    def test_create_service6_ai_orchestrator_custom_config(self):
        """Test creating orchestrator with custom config"""
        config = Service6AIConfig(
            enable_voice_ai=False,
            max_concurrent_operations=25
        )
        orchestrator = create_service6_ai_orchestrator(config)
        
        assert orchestrator.config.enable_voice_ai is False
        assert orchestrator.config.max_concurrent_operations == 25
    
    def test_create_default_service6_config(self):
        """Test default config factory"""
        config = create_default_service6_config()
        
        assert isinstance(config, Service6AIConfig)
        assert config.enable_advanced_ml_scoring is True
        assert config.max_concurrent_operations == 50
    
    def test_create_high_performance_config(self):
        """Test high-performance config factory"""
        config = create_high_performance_config()
        
        assert isinstance(config, Service6AIConfig)
        assert config.max_concurrent_operations == 100
        assert config.default_cache_ttl_seconds == 600
        assert config.ml_model_confidence_threshold == 0.8


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios"""
    
    @pytest.fixture
    async def minimal_companion(self):
        """Create companion with minimal configuration for edge case testing"""
        config = Service6AIConfig(
            enable_advanced_ml_scoring=False,
            enable_voice_ai=False,
            enable_predictive_analytics=False,
            enable_realtime_inference=False,
            enable_claude_enhancement=False
        )
        
        companion = Service6EnhancedClaudePlatformCompanion(config)
        companion.cache = MockRedisClient()
        companion.memory = MagicMock()
        companion.memory.get_context = AsyncMock(return_value={})
        companion.memory.update_lead_intelligence = AsyncMock(return_value=True)
        
        await companion.initialize()
        return companion
    
    @pytest.mark.asyncio
    async def test_analysis_with_no_ai_components(self, minimal_companion):
        """Test analysis when no AI components are enabled"""
        lead_data = create_test_lead_data()
        
        result = await minimal_companion.comprehensive_lead_analysis('test_lead_001', lead_data)
        
        assert isinstance(result, Service6AIResponse)
        assert result.ml_scoring_result is None
        assert result.voice_analysis_result is None
        assert result.predictive_insights is None
        assert result.unified_lead_score == 50.0  # Fallback score
        assert result.enhanced_claude_integration is False
        assert result.realtime_inference_active is False
        assert result.voice_ai_enabled is False
    
    @pytest.mark.asyncio
    async def test_cache_failure_handling(self):
        """Test handling of cache failures"""
        config = create_default_service6_config()
        companion = Service6EnhancedClaudePlatformCompanion(config)
        
        # Mock failing cache
        companion.cache = MagicMock()
        companion.cache.set = AsyncMock(side_effect=Exception("Cache connection failed"))
        companion.cache.get = AsyncMock(side_effect=Exception("Cache read failed"))
        
        companion.memory = MagicMock()
        companion.memory.get_context = AsyncMock(return_value={})
        companion.memory.update_lead_intelligence = AsyncMock(return_value=True)
        
        # Mock successful AI components
        companion.ml_scoring_engine = MagicMock()
        companion.ml_scoring_engine.score_lead_comprehensive = AsyncMock(
            return_value=create_mock_ml_scoring_result()
        )
        
        await companion.initialize()
        
        lead_data = create_test_lead_data()
        
        # Should still work despite cache failures
        result = await companion.comprehensive_lead_analysis('test_lead_001', lead_data)
        
        assert isinstance(result, Service6AIResponse)
        assert result.unified_lead_score > 0
    
    @pytest.mark.asyncio
    async def test_memory_service_failure_handling(self):
        """Test handling of memory service failures"""
        config = create_default_service6_config()
        companion = Service6EnhancedClaudePlatformCompanion(config)
        
        companion.cache = MockRedisClient()
        
        # Mock failing memory service
        companion.memory = MagicMock()
        companion.memory.get_context = AsyncMock(side_effect=Exception("Memory service failed"))
        companion.memory.update_lead_intelligence = AsyncMock(side_effect=Exception("Memory update failed"))
        
        # Mock AI components
        companion.ml_scoring_engine = MagicMock()
        companion.ml_scoring_engine.score_lead_comprehensive = AsyncMock(
            return_value=create_mock_ml_scoring_result()
        )
        
        await companion.initialize()
        
        lead_data = create_test_lead_data()
        
        # Should still work despite memory service failures
        result = await companion.comprehensive_lead_analysis('test_lead_001', lead_data)
        
        assert isinstance(result, Service6AIResponse)
        assert result.unified_lead_score > 0
    
    @pytest.mark.asyncio
    async def test_invalid_lead_data_handling(self):
        """Test handling of invalid lead data"""
        config = create_default_service6_config()
        companion = Service6EnhancedClaudePlatformCompanion(config)
        
        companion.cache = MockRedisClient()
        companion.memory = MagicMock()
        companion.memory.get_context = AsyncMock(return_value={})
        
        # Mock AI components that handle invalid data gracefully
        companion.ml_scoring_engine = MagicMock()
        companion.ml_scoring_engine.score_lead_comprehensive = AsyncMock(
            side_effect=Exception("Invalid lead data format")
        )
        
        await companion.initialize()
        
        # Invalid lead data
        invalid_lead_data = {'invalid': 'data', 'missing_required_fields': True}
        
        result = await companion.comprehensive_lead_analysis('test_lead_001', invalid_lead_data)
        
        # Should return fallback response
        assert isinstance(result, Service6AIResponse)
        assert result.unified_lead_score == 50.0
        assert "Manual review required" in result.immediate_actions[0]
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test performance characteristics under concurrent load"""
        config = create_high_performance_config()
        orchestrator = Service6AIOrchestrator(config)
        
        # Mock fast AI companion
        orchestrator.ai_companion = MagicMock()
        orchestrator.ai_companion.initialize = AsyncMock()
        
        async def fast_analysis(*args, **kwargs):
            await asyncio.sleep(0.01)  # Simulate 10ms processing
            return create_mock_service6_response()
        
        orchestrator.ai_companion.comprehensive_lead_analysis = fast_analysis
        
        await orchestrator.initialize()
        
        # Run concurrent operations
        lead_data = create_test_lead_data()
        start_time = time.time()
        
        tasks = []
        for i in range(20):
            task = orchestrator.analyze_lead(f'lead_{i}', lead_data)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Verify all operations completed
        assert len(results) == 20
        assert all(isinstance(r, Service6AIResponse) for r in results)
        
        # Check operation metrics
        assert orchestrator.operation_metrics['analyze_lead'] == 20
        
        # Performance should be reasonable (less than 1 second for 20 operations)
        execution_time = end_time - start_time
        assert execution_time < 1.0


@pytest.mark.performance
class TestPerformanceMetrics:
    """Performance-focused tests for Service 6 AI integration"""
    
    @pytest.mark.asyncio
    async def test_analysis_latency(self):
        """Test analysis latency is within acceptable bounds"""
        config = create_default_service6_config()
        companion = Service6EnhancedClaudePlatformCompanion(config)
        
        companion.cache = MockRedisClient()
        companion.memory = MagicMock()
        companion.memory.get_context = AsyncMock(return_value={})
        companion.memory.update_lead_intelligence = AsyncMock(return_value=True)
        
        # Mock AI components with realistic latencies
        companion.ml_scoring_engine = MagicMock()
        companion.ml_scoring_engine.score_lead_comprehensive = AsyncMock()
        
        async def realistic_ml_scoring(*args, **kwargs):
            await asyncio.sleep(0.1)  # 100ms ML processing
            return create_mock_ml_scoring_result()
        
        companion.ml_scoring_engine.score_lead_comprehensive = realistic_ml_scoring
        
        await companion.initialize()
        
        lead_data = create_test_lead_data()
        start_time = time.time()
        
        result = await companion.comprehensive_lead_analysis('test_lead_001', lead_data)
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        # Verify latency is reasonable (should be < 500ms for mocked components)
        assert latency_ms < 500
        assert result.processing_time_ms > 0
        
    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """Test caching performance and hit rates"""
        config = create_default_service6_config()
        companion = Service6EnhancedClaudePlatformCompanion(config)
        
        companion.cache = MockRedisClient()
        companion.memory = MagicMock()
        companion.memory.get_context = AsyncMock(return_value={})
        
        # Mock slow AI processing to make cache benefits obvious
        companion.ml_scoring_engine = MagicMock()
        
        async def slow_ml_scoring(*args, **kwargs):
            await asyncio.sleep(0.2)  # Slow processing
            return create_mock_ml_scoring_result()
        
        companion.ml_scoring_engine.score_lead_comprehensive = slow_ml_scoring
        
        await companion.initialize()
        
        lead_data = create_test_lead_data()
        
        # First analysis (should be slow)
        start_time = time.time()
        result1 = await companion.comprehensive_lead_analysis('test_lead_001', lead_data)
        first_time = time.time() - start_time
        
        # Second analysis (should use cache and be faster)
        start_time = time.time()
        result2 = await companion.comprehensive_lead_analysis('test_lead_001', lead_data)
        second_time = time.time() - start_time
        
        # Verify both results are valid
        assert isinstance(result1, Service6AIResponse)
        assert isinstance(result2, Service6AIResponse)
        
        # Cache operations should have been performed
        assert companion.cache.operation_count > 0


if __name__ == "__main__":
    # Run specific test classes for development
    pytest.main([
        "-v", 
        "tests/services/test_service6_ai_integration.py::TestService6AIConfig",
        "--tb=short"
    ])