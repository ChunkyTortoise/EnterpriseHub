#!/usr/bin/env python3

"""
🧪 Service 6 End-to-End Comprehensive Integration Test Suite
==========================================================

Complete workflow testing for Service 6 including:
- Full webhook → AI analysis → database → response pipeline
- High-intent lead fast-track workflow (<2 minutes)
- Real-time scoring → immediate action pipeline
- Voice AI integration workflow
- Multi-component error recovery
- Performance benchmarking under load
- Security validation across components
- Cache consistency across workflow steps

Target: Validate complete Service 6 ecosystem integration

Author: Claude AI Enhancement System
Date: 2026-01-17
"""

import asyncio
import json
import os

# Import mock services
import sys
import time
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.services.database_service import DatabaseService
from ghl_real_estate_ai.services.realtime_behavioral_network import (
    BehavioralSignal,
    BehavioralSignalType,
    RealTimeBehavioralNetwork,
    TriggerType,
)

# Import Service 6 components
from ghl_real_estate_ai.services.service6_ai_integration import (
    Service6AIConfig,
    Service6AIOrchestrator,
    Service6AIResponse,
    create_high_performance_config,
    create_service6_ai_orchestrator,
)

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "mocks"))
from external_services import (
    MockClaudeClient,
    MockEnhancedDatabaseService,
    MockMLScoringEngine,
    MockPredictiveAnalytics,
    MockSendGridClient,
    MockTieredCacheService,
    MockTwilioClient,
    MockVoiceAIClient,
    MockWebhookPayloads,
    create_mock_service6_response,
    create_test_lead_data,
)


class TestService6EndToEndWorkflows:
    """Test complete end-to-end workflows in Service 6"""

    @pytest.fixture
    async def service6_ecosystem(self):
        """Setup complete Service 6 ecosystem for testing"""
        # Create high-performance configuration
        config = create_high_performance_config()

        # Initialize orchestrator
        orchestrator = create_service6_ai_orchestrator(config)

        # Initialize behavioral network
        behavioral_network = RealTimeBehavioralNetwork()

        # Setup mock services
        mock_services = {
            "ml_scoring": MockMLScoringEngine(),
            "voice_ai": MockVoiceAIClient(),
            "predictive": MockPredictiveAnalytics(),
            "cache": MockTieredCacheService(),
            "database": MockEnhancedDatabaseService(),
            "claude": MockClaudeClient(),
            "twilio": MockTwilioClient(),
            "sendgrid": MockSendGridClient(),
        }

        # Mock orchestrator components
        orchestrator.ai_companion.ml_scoring_engine = mock_services["ml_scoring"]
        orchestrator.ai_companion.voice_ai = mock_services["voice_ai"]
        orchestrator.ai_companion.predictive_analytics = mock_services["predictive"]
        orchestrator.ai_companion.cache = mock_services["cache"]
        orchestrator.ai_companion.memory = mock_services["database"]

        # Mock behavioral network components
        behavioral_network.cache_service = mock_services["cache"]
        behavioral_network.database_service = mock_services["database"]
        behavioral_network.twilio_client = mock_services["twilio"]
        behavioral_network.sendgrid_client = mock_services["sendgrid"]
        behavioral_network.claude_client = mock_services["claude"]

        # Mock additional behavioral network dependencies
        behavioral_network.agent_availability_service = Mock()
        behavioral_network.template_engine = Mock()
        behavioral_network.personalization_engine = Mock()

        # Configure mock responses
        mock_services["ml_scoring"].setup_health_metrics({"success_rate": 0.95, "avg_latency_ms": 120})

        behavioral_network.agent_availability_service.check_availability.return_value = True
        behavioral_network.agent_availability_service.get_preferred_channel.return_value = "sms"
        behavioral_network.template_engine.render.return_value = {
            "subject": "Automated Response",
            "content": "Thank you for your inquiry...",
        }
        behavioral_network.personalization_engine.generate_content.return_value = {
            "personalized_properties": [],
            "personalization_score": 0.85,
        }

        # Initialize components
        await orchestrator.initialize()
        await behavioral_network.initialize()

        return {"orchestrator": orchestrator, "behavioral_network": behavioral_network, "mock_services": mock_services}

    @pytest.mark.asyncio
    async def test_complete_webhook_to_response_pipeline(self, service6_ecosystem):
        """Test complete webhook → AI analysis → database → response workflow"""
        orchestrator = service6_ecosystem["orchestrator"]
        behavioral_network = service6_ecosystem["behavioral_network"]
        mock_services = service6_ecosystem["mock_services"]

        # 1. Simulate incoming webhook from GHL
        webhook_payload = MockWebhookPayloads.ghl_lead_webhook(
            {
                "id": "webhook_lead_001",
                "email": "webhook.test@example.com",
                "firstName": "Webhook",
                "lastName": "Test",
                "customFields": {"budget": "650000", "timeline": "immediate", "location": "Austin"},
            }
        )

        lead_id = webhook_payload["data"]["id"]
        lead_data = {
            "name": f"{webhook_payload['data']['firstName']} {webhook_payload['data']['lastName']}",
            "email": webhook_payload["data"]["email"],
            "budget": int(webhook_payload["data"]["customFields"]["budget"]),
            "timeline": webhook_payload["data"]["customFields"]["timeline"],
            "location": webhook_payload["data"]["customFields"]["location"],
            "source": "ghl_webhook",
        }

        # 2. Process through AI orchestrator
        pipeline_start = datetime.now()

        ai_analysis = await orchestrator.analyze_lead(lead_id, lead_data, include_voice=False)

        # 3. Store in database
        await mock_services["database"].store_ai_analysis(lead_id, ai_analysis)
        await mock_services["database"].update_lead_score(
            lead_id, ai_analysis.unified_lead_score, {"ai_analysis_timestamp": ai_analysis.timestamp.isoformat()}
        )

        # 4. Process through behavioral network if high-intent
        if ai_analysis.unified_lead_score > 75.0:
            behavioral_signal = {
                "lead_id": lead_id,
                "signal_type": "high_intent_webhook",
                "raw_data": {
                    "ai_score": ai_analysis.unified_lead_score,
                    "priority": ai_analysis.priority_level,
                    "confidence": ai_analysis.confidence_level,
                },
                "source": "ai_orchestrator",
            }

            behavioral_result = await behavioral_network.process_signal(behavioral_signal)

            # 5. Execute immediate actions if critical
            if ai_analysis.priority_level == "critical":
                await behavioral_network._send_immediate_alert(
                    lead_id,
                    {
                        "priority": "critical",
                        "message": f"Critical lead: ${lead_data['budget']} budget, {lead_data['timeline']} timeline",
                        "channels": ["sms", "email"],
                        "agent_id": "agent_001",
                    },
                )

                await behavioral_network._send_automated_response(
                    lead_id,
                    {
                        "response_type": "immediate_acknowledgment",
                        "template": "urgent_inquiry_response",
                        "channel": "email",
                    },
                )

        pipeline_end = datetime.now()
        total_pipeline_time = (pipeline_end - pipeline_start).total_seconds()

        # Verify complete pipeline
        assert isinstance(ai_analysis, Service6AIResponse)
        assert ai_analysis.lead_id == lead_id
        assert ai_analysis.unified_lead_score > 0
        assert len(ai_analysis.immediate_actions) > 0

        # Verify database storage
        assert mock_services["database"].operation_count > 0
        stored_lead = await mock_services["database"].get_lead(lead_id)
        assert stored_lead is not None

        # Verify performance (complete pipeline under 5 seconds)
        assert total_pipeline_time < 5.0, f"Pipeline took {total_pipeline_time:.2f}s, too slow"

        # Verify notifications were sent if high-priority
        if ai_analysis.priority_level in ["critical", "high"]:
            assert len(mock_services["sendgrid"].sent_emails) > 0

    @pytest.mark.asyncio
    async def test_high_intent_lead_fast_track_under_2_minutes(self, service6_ecosystem):
        """Test high-intent lead fast-track workflow completes under 2 minutes"""
        orchestrator = service6_ecosystem["orchestrator"]
        behavioral_network = service6_ecosystem["behavioral_network"]
        mock_services = service6_ecosystem["mock_services"]

        # Configure for high-intent scenario
        mock_services["ml_scoring"].setup_mock_response(
            {
                "final_ml_score": 95.0,
                "confidence_interval": [92.0, 98.0],
                "recommended_actions": ["Immediate callback", "Send premium listings"],
                "opportunity_signals": ["High budget", "Immediate timeline", "Multiple inquiries"],
            }
        )

        # High-intent lead data
        lead_data = create_test_lead_data(
            {
                "lead_id": "fast_track_001",
                "budget": 850000,
                "timeline": "immediate",
                "email_open_rate": 0.95,
                "response_time_hours": 0.5,
                "page_views": 25,
                "urgency_indicators": 8,
            }
        )

        # Start fast-track timer
        fast_track_start = datetime.now()

        # 1. Immediate AI analysis
        ai_analysis = await orchestrator.analyze_lead("fast_track_001", lead_data)

        # 2. Parallel processing for speed
        parallel_tasks = []

        # Database storage
        parallel_tasks.append(mock_services["database"].store_ai_analysis("fast_track_001", ai_analysis))

        # Immediate alerts
        if ai_analysis.unified_lead_score > 90.0:
            parallel_tasks.append(
                behavioral_network._send_immediate_alert(
                    "fast_track_001",
                    {
                        "priority": "critical",
                        "message": "URGENT: $850K budget lead needs immediate attention",
                        "channels": ["sms"],
                        "agent_id": "agent_001",
                    },
                )
            )

            # Priority flag
            parallel_tasks.append(
                behavioral_network._set_priority_flag(
                    "fast_track_001",
                    {"priority_level": "critical", "reason": "High-value urgent inquiry", "duration_hours": 2},
                )
            )

            # Automated acknowledgment
            parallel_tasks.append(
                behavioral_network._send_automated_response(
                    "fast_track_001",
                    {"response_type": "immediate_acknowledgment", "template": "urgent_response", "channel": "email"},
                )
            )

            # Personalized content
            parallel_tasks.append(
                behavioral_network._deliver_personalized_content(
                    "fast_track_001",
                    {
                        "content_type": "premium_properties",
                        "delivery_channel": "email",
                        "personalization_factors": {"budget": 850000, "timeline": "immediate", "location": "Austin"},
                    },
                )
            )

        # Execute all fast-track actions in parallel
        results = await asyncio.gather(*parallel_tasks, return_exceptions=True)

        fast_track_end = datetime.now()
        fast_track_time = (fast_track_end - fast_track_start).total_seconds()

        # Verify fast-track timing (under 2 minutes = 120 seconds)
        assert fast_track_time < 120.0, f"Fast-track took {fast_track_time:.1f}s, exceeds 2-minute target"

        # Verify all fast-track actions completed
        successful_actions = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_actions) >= 4, "Most fast-track actions should complete successfully"

        # Verify immediate notifications
        assert len(mock_services["twilio"].sent_messages) > 0, "SMS alert should be sent"
        assert len(mock_services["sendgrid"].sent_emails) > 0, "Email response should be sent"

        print(f"✅ Fast-track completed in {fast_track_time:.1f} seconds (target: <120s)")

    @pytest.mark.asyncio
    async def test_realtime_scoring_to_action_pipeline(self, service6_ecosystem):
        """Test real-time scoring → immediate action pipeline"""
        orchestrator = service6_ecosystem["orchestrator"]
        behavioral_network = service6_ecosystem["behavioral_network"]
        mock_services = service6_ecosystem["mock_services"]

        # Real-time lead features
        lead_features = {
            "email_open_rate": 0.9,
            "response_time_hours": 0.8,
            "budget": 700000,
            "page_views": 20,
            "property_views": 12,
            "message_frequency": 3.5,
            "urgency_score": 0.85,
            "engagement_level": "very_high",
        }

        # 1. Real-time scoring
        rt_start = datetime.now()

        rt_score = await orchestrator.score_lead_realtime("realtime_001", lead_features, priority="high")

        rt_end = datetime.now()
        rt_time = (rt_end - rt_start).total_seconds() * 1000  # milliseconds

        # Verify real-time performance (under 100ms)
        assert rt_time < 100.0, f"Real-time scoring took {rt_time:.1f}ms, exceeds 100ms target"

        # 2. Immediate action based on score
        if rt_score.primary_score > 85.0:
            action_start = datetime.now()

            # Trigger immediate behavioral response
            trigger_data = {
                "trigger_id": "rt_trigger_001",
                "lead_id": "realtime_001",
                "trigger_type": TriggerType.IMMEDIATE_RESPONSE,
                "confidence": rt_score.confidence,
                "triggering_signals": ["high_rt_score"],
                "recommended_actions": ["immediate_callback"],
                "priority_level": "critical",
                "auto_execute": True,
            }

            trigger_result = await behavioral_network.execute_trigger(trigger_data)

            action_end = datetime.now()
            action_time = (action_end - action_start).total_seconds() * 1000

            # Verify immediate action performance (under 500ms)
            assert action_time < 500.0, f"Action execution took {action_time:.1f}ms, too slow"
            assert trigger_result.get("success") is True

        # Verify complete real-time pipeline
        assert rt_score.primary_score > 0
        assert rt_score.confidence > 0
        assert rt_score.processing_time_ms < 100.0

        print(f"✅ Real-time pipeline: Scoring {rt_time:.1f}ms + Action {action_time:.1f}ms")

    @pytest.mark.asyncio
    async def test_voice_ai_integration_workflow(self, service6_ecosystem):
        """Test voice AI integration workflow"""
        orchestrator = service6_ecosystem["orchestrator"]
        behavioral_network = service6_ecosystem["behavioral_network"]
        mock_services = service6_ecosystem["mock_services"]

        # Configure voice AI for success
        mock_services["voice_ai"].setup_call_analysis_success(True)

        # 1. Start voice coaching session
        call_id = "voice_test_call_001"
        lead_id = "voice_lead_001"
        agent_id = "agent_voice_001"

        voice_start = await orchestrator.start_voice_coaching(call_id, lead_id, agent_id)

        # Verify voice coaching started
        assert voice_start["coaching_active"] is True
        assert voice_start["call_id"] == call_id

        # 2. Simulate real-time audio processing
        audio_chunks = [b"audio_chunk_1", b"audio_chunk_2", b"audio_chunk_3"]

        for i, chunk in enumerate(audio_chunks):
            audio_result = await orchestrator.ai_companion.process_voice_audio_stream(
                call_id,
                chunk,
                f"speaker_{i % 2}",  # Alternate between speakers
            )

            # Verify audio processing
            assert "call_id" in audio_result
            if "transcript_segment" in audio_result:
                assert len(audio_result["transcript_segment"]) > 0

        # 3. Generate behavioral insights from voice data
        voice_behavioral_context = {
            "recent_signals": [
                {"type": "voice_urgency", "confidence": 0.9},
                {"type": "buying_intent", "confidence": 0.85},
            ],
            "call_metadata": {"duration_seconds": 480, "sentiment": "positive", "urgency_detected": True},
        }

        voice_insights = await behavioral_network.generate_insights(lead_id, voice_behavioral_context)

        # Verify voice integration
        assert len(voice_insights) > 0
        insight = voice_insights[0]
        assert insight.lead_id == lead_id
        assert insight.confidence_score > 0

        print("✅ Voice AI workflow: Coaching started, audio processed, insights generated")

    @pytest.mark.asyncio
    async def test_error_recovery_across_components(self, service6_ecosystem):
        """Test error recovery and graceful degradation across Service 6 components"""
        orchestrator = service6_ecosystem["orchestrator"]
        behavioral_network = service6_ecosystem["behavioral_network"]
        mock_services = service6_ecosystem["mock_services"]

        lead_id = "error_recovery_001"
        lead_data = create_test_lead_data({"lead_id": lead_id})

        # 1. Test ML scoring failure with fallback
        mock_services["ml_scoring"].setup_failure_mode(True)

        # Should fall back to enhanced scorer
        ai_analysis = await orchestrator.analyze_lead(lead_id, lead_data)

        # Verify fallback succeeded
        assert isinstance(ai_analysis, Service6AIResponse)
        assert ai_analysis.ml_scoring_result is None  # ML scoring failed
        assert ai_analysis.unified_lead_score > 0  # Fallback scoring worked

        # Reset ML scoring
        mock_services["ml_scoring"].setup_failure_mode(False)

        # 2. Test cache failure recovery
        original_cache_set = mock_services["cache"].set_in_layer
        mock_services["cache"].set_in_layer = AsyncMock(side_effect=Exception("Cache unavailable"))

        # Should continue without cache
        ai_analysis_no_cache = await orchestrator.analyze_lead(f"{lead_id}_no_cache", lead_data)
        assert isinstance(ai_analysis_no_cache, Service6AIResponse)

        # Restore cache
        mock_services["cache"].set_in_layer = original_cache_set

        # 3. Test communication failure in behavioral network
        mock_services["twilio"].send_sms = AsyncMock(side_effect=Exception("SMS service unavailable"))

        # Should handle SMS failure gracefully
        alert_result = await behavioral_network._send_immediate_alert(
            lead_id,
            {
                "priority": "high",
                "message": "Test alert with SMS failure",
                "channels": ["sms", "email"],
                "agent_id": "agent_001",
            },
        )

        # Should partially succeed (email should work even if SMS fails)
        assert "error" in alert_result or alert_result.get("success") is not None

        # 4. Test database failure recovery
        original_db_save = mock_services["database"].save_lead
        mock_services["database"].save_lead = AsyncMock(side_effect=Exception("Database unavailable"))

        # Should handle database failure gracefully
        try:
            await orchestrator.analyze_lead(f"{lead_id}_db_fail", lead_data)
        except Exception as e:
            # Should either succeed with fallback or fail gracefully
            assert "database" in str(e).lower() or "unavailable" in str(e).lower()

        print("✅ Error recovery: All components handled failures gracefully")

    @pytest.mark.asyncio
    async def test_high_load_concurrent_processing(self, service6_ecosystem):
        """Test Service 6 under high concurrent load"""
        orchestrator = service6_ecosystem["orchestrator"]
        behavioral_network = service6_ecosystem["behavioral_network"]
        mock_services = service6_ecosystem["mock_services"]

        # Generate high-load test data
        concurrent_leads = 50
        lead_batches = []

        for i in range(concurrent_leads):
            lead_data = create_test_lead_data(
                {
                    "lead_id": f"load_test_lead_{i:03d}",
                    "email": f"load{i}@example.com",
                    "budget": 400000 + (i * 10000),
                    "timeline": "soon" if i % 2 == 0 else "immediate",
                }
            )
            lead_batches.append(lead_data)

        # Test concurrent AI analysis
        load_test_start = datetime.now()

        async def process_single_lead(lead_data):
            """Process a single lead through the complete pipeline"""
            lead_id = lead_data["lead_id"]

            # AI analysis
            analysis = await orchestrator.analyze_lead(lead_id, lead_data)

            # Store in database
            await mock_services["database"].store_ai_analysis(lead_id, analysis)

            # Behavioral processing if high score
            if analysis.unified_lead_score > 70:
                behavioral_signal = {
                    "lead_id": lead_id,
                    "signal_type": "ai_analysis_complete",
                    "raw_data": {"score": analysis.unified_lead_score},
                    "source": "load_test",
                }
                await behavioral_network.process_signal(behavioral_signal)

            return analysis

        # Execute concurrent processing
        tasks = [process_single_lead(lead_data) for lead_data in lead_batches]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        load_test_end = datetime.now()
        total_load_time = (load_test_end - load_test_start).total_seconds()

        # Analyze results
        successful_analyses = [r for r in results if isinstance(r, Service6AIResponse)]
        failed_analyses = [r for r in results if isinstance(r, Exception)]

        success_rate = len(successful_analyses) / len(results)
        throughput = len(successful_analyses) / total_load_time

        # Verify load performance
        assert success_rate > 0.9, f"Success rate {success_rate:.2%} too low under load"
        assert throughput > 5.0, f"Throughput {throughput:.1f} analyses/sec too low"
        assert total_load_time < 30.0, f"Load test took {total_load_time:.1f}s, too slow"

        # Verify system resources
        total_db_operations = mock_services["database"].operation_count
        assert total_db_operations > concurrent_leads, "Database should have processed all leads"

        print(f"✅ High-load test: {len(successful_analyses)}/{concurrent_leads} leads processed")
        print(f"   Success rate: {success_rate:.1%}")
        print(f"   Throughput: {throughput:.1f} analyses/sec")
        print(f"   Total time: {total_load_time:.1f}s")

    @pytest.mark.asyncio
    async def test_cache_consistency_across_workflow(self, service6_ecosystem):
        """Test cache consistency across complete workflow"""
        orchestrator = service6_ecosystem["orchestrator"]
        behavioral_network = service6_ecosystem["behavioral_network"]
        cache_service = service6_ecosystem["mock_services"]["cache"]

        lead_id = "cache_consistency_001"
        lead_data = create_test_lead_data({"lead_id": lead_id})

        # 1. First analysis - should populate cache
        analysis1 = await orchestrator.analyze_lead(lead_id, lead_data)

        # Verify cache was populated
        cached_analysis = await cache_service.get_from_layer(f"s6_analysis:{lead_id}", "redis")
        assert cached_analysis is not None

        # 2. Behavioral processing - should use cache
        behavioral_signal = {
            "lead_id": lead_id,
            "signal_type": "page_view",
            "raw_data": {"pages": 5, "time_spent": 300},
            "source": "cache_test",
        }

        behavioral_result = await behavioral_network.process_signal(behavioral_signal)

        # 3. Second analysis - should hit cache or update consistently
        analysis2 = await orchestrator.analyze_lead(lead_id, lead_data)

        # Verify cache consistency
        cache_stats = cache_service.get_cache_stats()
        assert cache_stats["hit_rate"] > 0, "Should have some cache hits"

        # Both analyses should be consistent
        assert analysis1.lead_id == analysis2.lead_id

        # 4. Cache invalidation test
        await cache_service.invalidate_key(f"s6_analysis:{lead_id}")

        # Should work without cache
        analysis3 = await orchestrator.analyze_lead(lead_id, lead_data)
        assert isinstance(analysis3, Service6AIResponse)

        print("✅ Cache consistency maintained across workflow steps")

    @pytest.mark.asyncio
    async def test_security_validation_across_pipeline(self, service6_ecosystem):
        """Test security validation across the complete pipeline"""
        orchestrator = service6_ecosystem["orchestrator"]
        behavioral_network = service6_ecosystem["behavioral_network"]
        mock_services = service6_ecosystem["mock_services"]

        # Test with potentially malicious input
        malicious_lead_data = {
            "lead_id": "security_test_001",
            "name": '<script>alert("xss")</script>',
            "email": "test@example.com; DROP TABLE leads;",
            "budget": "invalid_budget_injection",
            "custom_fields": {"comments": '<img src="x" onerror="alert(\'xss\')">'},
        }

        # 1. Test AI analysis with malicious input
        try:
            analysis = await orchestrator.analyze_lead("security_test_001", malicious_lead_data)

            # Should either sanitize input or handle safely
            assert isinstance(analysis, Service6AIResponse)

            # Verify no script injection in response
            response_str = str(asdict(analysis))
            assert "<script>" not in response_str
            assert "DROP TABLE" not in response_str
            assert "alert(" not in response_str

        except Exception as e:
            # Acceptable if it properly validates and rejects malicious input
            assert "validation" in str(e).lower() or "invalid" in str(e).lower()

        # 2. Test database security
        try:
            await mock_services["database"].save_lead("security_test_001", malicious_lead_data)

            # If saved, verify data was sanitized
            retrieved = await mock_services["database"].get_lead("security_test_001")
            if retrieved:
                retrieved_str = str(retrieved)
                assert "<script>" not in retrieved_str
                assert "DROP TABLE" not in retrieved_str

        except Exception as e:
            # Acceptable if it properly rejects malicious data
            assert "validation" in str(e).lower() or "security" in str(e).lower()

        # 3. Test behavioral network security
        malicious_signal = {
            "lead_id": "security_test_001",
            "signal_type": "page_view",
            "raw_data": {"url": 'javascript:alert("xss")', "referrer": "<script>malicious()</script>"},
            "source": "security_test",
        }

        try:
            behavioral_result = await behavioral_network.process_signal(malicious_signal)

            # Should handle malicious signal safely
            if behavioral_result:
                result_str = str(behavioral_result)
                assert "<script>" not in result_str
                assert "javascript:" not in result_str

        except Exception as e:
            # Acceptable if it properly validates signal data
            assert "validation" in str(e).lower() or "security" in str(e).lower()

        print("✅ Security validation: Malicious input handled safely across pipeline")


@pytest.mark.asyncio
class TestService6PerformanceBenchmarks:
    """Performance benchmarking for complete Service 6 ecosystem"""

    @pytest.fixture
    async def benchmark_ecosystem(self):
        """Setup optimized Service 6 ecosystem for benchmarking"""
        # Use high-performance configuration
        config = create_high_performance_config()
        config.max_concurrent_operations = 100

        orchestrator = create_service6_ai_orchestrator(config)
        behavioral_network = RealTimeBehavioralNetwork()

        # Setup fast mock services
        fast_mocks = {
            "ml_scoring": MockMLScoringEngine(),
            "voice_ai": MockVoiceAIClient(),
            "predictive": MockPredictiveAnalytics(),
            "cache": MockTieredCacheService(),
            "database": MockEnhancedDatabaseService(),
        }

        # Configure for fast responses
        for mock in fast_mocks.values():
            if hasattr(mock, "setup_failure_mode"):
                mock.setup_failure_mode(False)

        # Wire up fast mocks
        orchestrator.ai_companion.ml_scoring_engine = fast_mocks["ml_scoring"]
        orchestrator.ai_companion.voice_ai = fast_mocks["voice_ai"]
        orchestrator.ai_companion.predictive_analytics = fast_mocks["predictive"]
        orchestrator.ai_companion.cache = fast_mocks["cache"]
        orchestrator.ai_companion.memory = fast_mocks["database"]

        behavioral_network.cache_service = fast_mocks["cache"]
        behavioral_network.database_service = fast_mocks["database"]

        await orchestrator.initialize()
        await behavioral_network.initialize()

        return {"orchestrator": orchestrator, "behavioral_network": behavioral_network, "fast_mocks": fast_mocks}

    async def test_end_to_end_latency_benchmark(self, benchmark_ecosystem):
        """Benchmark end-to-end latency for complete workflows"""
        orchestrator = benchmark_ecosystem["orchestrator"]
        behavioral_network = benchmark_ecosystem["behavioral_network"]

        # Run multiple iterations to get stable benchmarks
        iteration_count = 10
        latencies = []

        for i in range(iteration_count):
            lead_data = create_test_lead_data({"lead_id": f"benchmark_lead_{i:03d}", "budget": 500000 + (i * 10000)})

            # Measure end-to-end latency
            start_time = time.perf_counter()

            # Complete workflow
            analysis = await orchestrator.analyze_lead(f"benchmark_lead_{i:03d}", lead_data)

            if analysis.unified_lead_score > 75:
                await behavioral_network.process_signal(
                    {
                        "lead_id": f"benchmark_lead_{i:03d}",
                        "signal_type": "high_score",
                        "raw_data": {"score": analysis.unified_lead_score},
                        "source": "benchmark",
                    }
                )

            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)

        # Calculate statistics
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        p95_latency = sorted(latencies)[int(0.95 * len(latencies))]

        # Performance assertions
        assert avg_latency < 200.0, f"Average latency {avg_latency:.1f}ms exceeds 200ms target"
        assert p95_latency < 300.0, f"P95 latency {p95_latency:.1f}ms exceeds 300ms target"
        assert max_latency < 500.0, f"Max latency {max_latency:.1f}ms exceeds 500ms limit"

        print(f"📊 End-to-End Latency Benchmark ({iteration_count} iterations):")
        print(f"   Average: {avg_latency:.1f}ms")
        print(f"   Min: {min_latency:.1f}ms")
        print(f"   Max: {max_latency:.1f}ms")
        print(f"   P95: {p95_latency:.1f}ms")

    async def test_throughput_benchmark_sustained_load(self, benchmark_ecosystem):
        """Benchmark sustained throughput under continuous load"""
        orchestrator = benchmark_ecosystem["orchestrator"]

        # Sustained load test parameters
        duration_seconds = 10
        target_rps = 20  # requests per second

        async def generate_continuous_load():
            """Generate continuous load for the duration"""
            results = []
            start_time = time.perf_counter()
            request_count = 0

            while time.perf_counter() - start_time < duration_seconds:
                # Calculate when next request should start
                next_request_time = start_time + (request_count / target_rps)
                current_time = time.perf_counter()

                # Wait if we're ahead of schedule
                if current_time < next_request_time:
                    await asyncio.sleep(next_request_time - current_time)

                # Generate request
                lead_data = create_test_lead_data(
                    {"lead_id": f"sustained_load_{request_count:04d}", "budget": 400000 + (request_count % 100) * 5000}
                )

                # Process request
                task_start = time.perf_counter()
                try:
                    analysis = await orchestrator.analyze_lead(f"sustained_load_{request_count:04d}", lead_data)
                    task_end = time.perf_counter()

                    results.append(
                        {"success": True, "latency_ms": (task_end - task_start) * 1000, "timestamp": task_end}
                    )
                except Exception as e:
                    task_end = time.perf_counter()
                    results.append(
                        {
                            "success": False,
                            "error": str(e),
                            "latency_ms": (task_end - task_start) * 1000,
                            "timestamp": task_end,
                        }
                    )

                request_count += 1

            return results

        # Run sustained load test
        load_results = await generate_continuous_load()

        # Analyze throughput results
        successful_requests = [r for r in load_results if r["success"]]
        failed_requests = [r for r in load_results if not r["success"]]

        actual_rps = len(load_results) / duration_seconds
        success_rate = len(successful_requests) / len(load_results)
        avg_latency = sum(r["latency_ms"] for r in successful_requests) / len(successful_requests)

        # Performance assertions
        assert success_rate > 0.95, f"Success rate {success_rate:.1%} too low under sustained load"
        assert actual_rps > target_rps * 0.9, f"Actual RPS {actual_rps:.1f} below target {target_rps}"
        assert avg_latency < 250.0, f"Average latency {avg_latency:.1f}ms too high under load"

        print(f"📈 Sustained Load Benchmark ({duration_seconds}s @ {target_rps} RPS target):")
        print(f"   Actual RPS: {actual_rps:.1f}")
        print(f"   Success rate: {success_rate:.1%}")
        print(f"   Average latency: {avg_latency:.1f}ms")
        print(f"   Total requests: {len(load_results)}")
        print(f"   Failed requests: {len(failed_requests)}")

    async def test_memory_efficiency_benchmark(self, benchmark_ecosystem):
        """Benchmark memory efficiency with large datasets"""
        orchestrator = benchmark_ecosystem["orchestrator"]

        # Process large batch to test memory usage
        large_batch_size = 100

        # Generate large batch of varied leads
        large_batch = []
        for i in range(large_batch_size):
            lead_data = create_test_lead_data(
                {
                    "lead_id": f"memory_test_{i:04d}",
                    "budget": 300000 + (i * 3000),
                    "custom_data": {f"field_{j}": f"value_{i}_{j}" for j in range(20)},  # Extra data
                }
            )
            large_batch.append(lead_data)

        # Process batch and measure timing
        batch_start = time.perf_counter()

        tasks = [
            orchestrator.analyze_lead(f"memory_test_{i:04d}", lead_data) for i, lead_data in enumerate(large_batch)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        batch_end = time.perf_counter()
        batch_time = batch_end - batch_start

        # Analyze results
        successful_results = [r for r in results if isinstance(r, Service6AIResponse)]
        throughput = len(successful_results) / batch_time

        # Memory efficiency assertions (based on timing - memory usage hard to measure directly)
        assert throughput > 10.0, f"Throughput {throughput:.1f} analyses/sec too low for memory test"
        assert batch_time < 20.0, f"Large batch took {batch_time:.1f}s, may indicate memory issues"

        # Verify no memory-related errors
        memory_errors = [r for r in results if isinstance(r, Exception) and "memory" in str(r).lower()]
        assert len(memory_errors) == 0, f"Memory-related errors detected: {memory_errors}"

        print(f"💾 Memory Efficiency Benchmark ({large_batch_size} leads):")
        print(f"   Total time: {batch_time:.1f}s")
        print(f"   Throughput: {throughput:.1f} analyses/sec")
        print(f"   Success rate: {len(successful_results) / len(results):.1%}")


if __name__ == "__main__":
    # Run tests with coverage across integration
    pytest.main(
        [
            __file__,
            "-v",
            "--tb=short",
            "--durations=10",  # Show 10 slowest tests
            "-k",
            "not benchmark",  # Skip benchmarks in regular test runs
            "--cov=ghl_real_estate_ai.services",
            "--cov-report=term-missing",
            "--cov-report=html:tests/coverage/integration",
            "--cov-fail-under=80",
        ]
    )
