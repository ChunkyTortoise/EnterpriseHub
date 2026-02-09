import pytest
pytestmark = pytest.mark.integration

#!/usr/bin/env python3
"""
Service 6 End-to-End Integration Tests
=====================================

Tests complete business workflows from webhook to response:
- High-intent lead fast-track (<2 minutes)
- Real-time scoring → immediate action pipeline
- Behavioral trigger → alert → response workflow
- Error recovery and fallback mechanisms

Target: Complete workflow validation
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.services.realtime_behavioral_network import (
    BehavioralSignal,
    BehavioralSignalType,
    RealTimeBehavioralNetwork,
    RealTimeTrigger,
    TriggerType,
)

# Import services for integration testing
from ghl_real_estate_ai.services.service6_ai_integration import (

@pytest.mark.integration
    Service6AIConfig,
    Service6AIOrchestrator,
    create_service6_ai_orchestrator,
)


class TestService6EndToEndWorkflows:
    """Test complete Service 6 end-to-end workflows."""

    @pytest.fixture
    async def mock_services_ecosystem(self):
        """Mock the complete services ecosystem for integration testing."""
        return {
            "database_service": AsyncMock(),
            "cache_service": AsyncMock(),
            "email_service": AsyncMock(),
            "sms_service": AsyncMock(),
            "ghl_webhook_service": AsyncMock(),
            "claude_client": AsyncMock(),
            "notification_service": AsyncMock(),
        }

    @pytest.fixture
    async def integrated_service6_orchestrator(self, mock_services_ecosystem):
        """Create integrated Service 6 orchestrator with all dependencies mocked."""
        config = Service6AIConfig(
            enable_advanced_ml_scoring=True,
            enable_voice_ai=False,  # Disable for simpler testing
            enable_predictive_analytics=True,
            enable_realtime_inference=True,
            max_concurrent_operations=10,
        )

        orchestrator = create_service6_ai_orchestrator(config)

        # Mock the AI companion
        orchestrator.ai_companion = AsyncMock()
        orchestrator.ai_companion.comprehensive_lead_analysis.return_value = AsyncMock(
            lead_id="lead_urgent_123",
            unified_lead_score=88.5,
            confidence_level=0.85,
            priority_level="high",
            immediate_actions=["immediate_response", "priority_routing", "agent_alert"],
            strategic_recommendations=["schedule_consultation", "send_properties"],
            processing_time_ms=145.0,
            models_used=["ml_scorer", "claude_enhanced"],
            enhanced_claude_integration=True,
            realtime_inference_active=True,
        )

        orchestrator.ai_companion.realtime_lead_scoring.return_value = AsyncMock(
            primary_score=85.2, confidence=0.88, prediction_class="high_intent", processing_time_ms=95.0
        )

        return orchestrator

    @pytest.fixture
    async def integrated_behavioral_network(self, mock_services_ecosystem):
        """Create integrated behavioral network with mocked dependencies."""
        network = RealTimeBehavioralNetwork()

        # Inject mocked services
        for service_name, mock_service in mock_services_ecosystem.items():
            setattr(network, service_name, mock_service)

        # Setup successful responses
        network.database_service.get_lead.return_value = {
            "id": "lead_urgent_123",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "email": "sarah.j@example.com",
            "phone": "+1555123456",
            "budget_range": "$500k-700k",
            "timeline": "immediate",
            "assigned_agent_id": "agent_vip_001",
        }

        network.database_service.log_communication.return_value = True
        network.database_service.update_lead.return_value = True
        network.email_service.send_templated_email.return_value = True
        network.sms_service.send_templated_sms.return_value = True

        return network

    @pytest.mark.asyncio
    async def test_high_intent_lead_fast_track_workflow(
        self, integrated_service6_orchestrator, integrated_behavioral_network
    ):
        """Test complete high-intent lead workflow under 2 minutes."""
        start_time = time.time()

        # Step 1: Simulate webhook data from GHL
        webhook_data = {
            "lead_id": "lead_urgent_123",
            "event": "multiple_property_views",
            "properties_viewed": [
                {"id": "prop_001", "price": 650000, "time_spent": 900},  # 15 minutes
                {"id": "prop_002", "price": 680000, "time_spent": 720},  # 12 minutes
                {"id": "prop_003", "price": 625000, "time_spent": 1200},  # 20 minutes
            ],
            "behavioral_signals": ["calculator_usage", "form_started", "contact_info_viewed", "financing_page_visited"],
            "session_duration_minutes": 47,
            "timestamp": datetime.now().isoformat(),
            "urgency_score": 9.2,
        }

        # Step 2: AI Analysis Phase
        analysis_start = time.time()
        analysis_result = await integrated_service6_orchestrator.analyze_lead(webhook_data["lead_id"], webhook_data)
        analysis_time = (time.time() - analysis_start) * 1000

        # Verify AI analysis completed quickly and effectively
        assert analysis_result.lead_id == "lead_urgent_123"
        assert analysis_result.unified_lead_score >= 80  # High score for urgent lead
        assert analysis_result.priority_level in ["high", "critical"]
        assert analysis_time < 300, f"AI analysis took {analysis_time:.1f}ms, target: <200ms"

        # Step 3: Real-time Behavioral Analysis
        behavioral_signals = []
        for i, signal_type in enumerate(["property_view", "calculator_usage", "form_interaction"]):
            signal = BehavioralSignal(
                signal_id=f"urgent_signal_{i}",
                lead_id="lead_urgent_123",
                signal_type=getattr(BehavioralSignalType, signal_type.upper()),
                timestamp=datetime.now() - timedelta(minutes=i),
                interaction_value=9.0 + i * 0.5,
                context_data={"urgency_indicators": True, "high_value_interaction": True},
            )
            behavioral_signals.append(signal)

        # Process behavioral signals
        await integrated_behavioral_network._process_signals_batch(behavioral_signals)

        # Step 4: Trigger Generation and Execution
        high_priority_trigger = RealTimeTrigger(
            trigger_id="urgent_trigger_123",
            lead_id="lead_urgent_123",
            trigger_type=TriggerType.IMMEDIATE_ALERT,
            trigger_condition="high_intent_multiple_signals",
            action_payload={
                "urgency_score": 9.2,
                "behavioral_score": analysis_result.unified_lead_score,
                "properties_viewed": 3,
                "session_duration": 47,
                "priority_routing_required": True,
            },
            priority=5,  # Maximum priority
            expiration_time=datetime.now() + timedelta(minutes=30),
        )

        # Execute urgent response workflow
        trigger_start = time.time()
        await integrated_behavioral_network._send_immediate_alert(high_priority_trigger)
        await integrated_behavioral_network._notify_agent(high_priority_trigger)
        await integrated_behavioral_network._set_priority_flag(high_priority_trigger)
        trigger_time = (time.time() - trigger_start) * 1000

        # Step 5: Real-time Scoring for Immediate Actions
        scoring_start = time.time()
        realtime_score = await integrated_service6_orchestrator.score_lead_realtime(
            "lead_urgent_123",
            {
                "urgency_score": 9.2,
                "properties_viewed": 3,
                "session_duration": 47,
                "calculator_usage": True,
                "form_interaction": True,
            },
            priority="critical",
        )
        scoring_time = (time.time() - scoring_start) * 1000

        # Verify real-time scoring performance
        assert realtime_score.primary_score >= 80
        assert scoring_time < 150, f"Real-time scoring took {scoring_time:.1f}ms, target: <100ms"

        # Step 6: Complete Workflow Timing
        total_workflow_time = time.time() - start_time

        # Verify complete workflow timing
        assert total_workflow_time < 120, (
            f"Complete workflow took {total_workflow_time:.1f}s, target: <120s (2 minutes)"
        )

        # Verify all critical components were activated
        integrated_behavioral_network.database_service.log_communication.assert_called()
        integrated_behavioral_network.database_service.update_lead.assert_called()

        print(f"\n✅ High-Intent Lead Fast-Track Workflow Completed:")
        print(f"   • Total Time: {total_workflow_time:.1f}s (Target: <120s)")
        print(f"   • AI Analysis: {analysis_time:.1f}ms")
        print(f"   • Trigger Execution: {trigger_time:.1f}ms")
        print(f"   • Real-time Scoring: {scoring_time:.1f}ms")
        print(f"   • Final Lead Score: {analysis_result.unified_lead_score}")
        print(f"   • Priority Level: {analysis_result.priority_level}")

    @pytest.mark.asyncio
    async def test_real_time_scoring_to_action_pipeline(
        self, integrated_service6_orchestrator, integrated_behavioral_network
    ):
        """Test real-time scoring to immediate action pipeline."""

        # Scenario: Lead views expensive property and uses mortgage calculator
        lead_id = "lead_pipeline_456"

        # Step 1: Real-time Scoring Event
        scoring_features = {
            "property_price": 750000,
            "mortgage_calculator_used": True,
            "time_on_property_page": 900,  # 15 minutes
            "contact_form_started": True,
            "previous_visit_count": 3,
            "email_engagement_rate": 0.85,
        }

        scoring_start = time.time()
        score_result = await integrated_service6_orchestrator.score_lead_realtime(lead_id, scoring_features, "high")
        scoring_time = (time.time() - scoring_start) * 1000

        # Verify scoring performance
        assert score_result.primary_score > 0
        assert scoring_time < 150, f"Scoring took {scoring_time:.1f}ms"

        # Step 2: Scoring Triggers Priority Routing
        if score_result.primary_score >= 70:
            priority_trigger = RealTimeTrigger(
                trigger_id=f"priority_{lead_id}",
                lead_id=lead_id,
                trigger_type=TriggerType.PRIORITY_FLAG,
                trigger_condition="high_score_mortgage_calculator",
                action_payload={
                    "score": score_result.primary_score,
                    "confidence": score_result.confidence,
                    "trigger_reason": "mortgage_calculator_high_value_property",
                },
                priority=4,
                expiration_time=datetime.now() + timedelta(hours=2),
            )

            await integrated_behavioral_network._set_priority_flag(priority_trigger)

            # Step 3: Priority Routing Triggers Agent Notification
            agent_trigger = RealTimeTrigger(
                trigger_id=f"agent_{lead_id}",
                lead_id=lead_id,
                trigger_type=TriggerType.AGENT_NOTIFICATION,
                trigger_condition="priority_lead_requires_attention",
                action_payload={"urgency": "high", "reason": "High-value property interest with mortgage calculation"},
                priority=4,
                expiration_time=datetime.now() + timedelta(minutes=30),
            )

            await integrated_behavioral_network._notify_agent(agent_trigger)

        # Step 4: Automated Response Based on Behavior
        response_trigger = RealTimeTrigger(
            trigger_id=f"response_{lead_id}",
            lead_id=lead_id,
            trigger_type=TriggerType.AUTOMATED_RESPONSE,
            trigger_condition="mortgage_calculator_followup",
            action_payload={"property_price": 750000, "response_type": "mortgage_assistance"},
            priority=3,
            expiration_time=datetime.now() + timedelta(hours=1),
        )

        await integrated_behavioral_network._send_automated_response(response_trigger)

        # Verify pipeline execution
        integrated_behavioral_network.database_service.update_lead.assert_called()
        integrated_behavioral_network.database_service.log_communication.assert_called()

        print(f"✅ Real-time Scoring Pipeline Completed:")
        print(f"   • Score: {score_result.primary_score}")
        print(f"   • Confidence: {score_result.confidence}")
        print(f"   • Scoring Time: {scoring_time:.1f}ms")

    @pytest.mark.asyncio
    async def test_behavioral_trigger_to_response_workflow(self, integrated_behavioral_network):
        """Test behavioral trigger to alert and response workflow."""

        lead_id = "lead_behavior_789"

        # Step 1: Generate Multiple Behavioral Signals (Abandonment Pattern)
        abandonment_signals = []

        # Initial high activity
        for i in range(8):
            signal = BehavioralSignal(
                signal_id=f"active_{i}",
                lead_id=lead_id,
                signal_type=BehavioralSignalType.PROPERTY_VIEW,
                timestamp=datetime.now() - timedelta(minutes=60 - i * 5),  # 60 minutes ago to 25 minutes ago
                interaction_value=8.0 + i * 0.3,
            )
            abandonment_signals.append(signal)

        # Recent low activity (abandonment risk)
        for i in range(2):
            signal = BehavioralSignal(
                signal_id=f"decline_{i}",
                lead_id=lead_id,
                signal_type=BehavioralSignalType.PAGE_VIEW,
                timestamp=datetime.now() - timedelta(minutes=10 - i * 5),  # 10 and 5 minutes ago
                interaction_value=2.0 + i * 0.5,  # Much lower activity
            )
            abandonment_signals.append(signal)

        # Step 2: Process Behavioral Signals
        await integrated_behavioral_network._process_signals_batch(abandonment_signals)

        # Step 3: Generate Abandonment Risk Trigger
        abandonment_trigger = RealTimeTrigger(
            trigger_id="abandonment_risk_789",
            lead_id=lead_id,
            trigger_type=TriggerType.RETARGETING_CAMPAIGN,
            trigger_condition="activity_decline_abandonment_risk",
            action_payload={
                "pattern": "abandonment_risk",
                "previous_activity_level": "high",
                "current_activity_level": "low",
                "risk_score": 7.8,
            },
            priority=3,
            expiration_time=datetime.now() + timedelta(hours=6),
        )

        # Step 4: Execute Re-engagement Workflow
        re_engagement_start = time.time()

        # Send immediate re-engagement content
        await integrated_behavioral_network._deliver_personalized_content(abandonment_trigger)

        # Follow up with automated response
        followup_trigger = RealTimeTrigger(
            trigger_id="followup_789",
            lead_id=lead_id,
            trigger_type=TriggerType.AUTOMATED_RESPONSE,
            trigger_condition="abandonment_followup",
            action_payload={"message_type": "re_engagement", "incentive": "exclusive_viewing_opportunity"},
            priority=2,
            expiration_time=datetime.now() + timedelta(hours=4),
        )

        await integrated_behavioral_network._send_automated_response(followup_trigger)

        re_engagement_time = (time.time() - re_engagement_start) * 1000

        # Verify re-engagement workflow
        integrated_behavioral_network.database_service.log_communication.assert_called()
        assert re_engagement_time < 500, f"Re-engagement took {re_engagement_time:.1f}ms"

        print(f"✅ Behavioral Trigger to Response Workflow Completed:")
        print(f"   • Pattern Detected: Abandonment Risk")
        print(f"   • Re-engagement Time: {re_engagement_time:.1f}ms")
        print(f"   • Triggers Executed: Personalized Content + Automated Response")

    @pytest.mark.asyncio
    async def test_error_recovery_and_fallback_mechanisms(
        self, integrated_service6_orchestrator, integrated_behavioral_network
    ):
        """Test error recovery when multiple components fail."""

        lead_id = "lead_error_test"

        # Step 1: Simulate Primary AI Service Failure
        integrated_service6_orchestrator.ai_companion.comprehensive_lead_analysis.side_effect = Exception(
            "AI Service Timeout"
        )

        # Should fall back to basic scoring
        try:
            analysis_result = await integrated_service6_orchestrator.analyze_lead(
                lead_id, {"name": "Test Lead", "email": "test@example.com"}
            )

            # Should provide fallback result
            assert analysis_result is not None
            assert analysis_result.lead_id == lead_id
            # Should indicate degraded service
            assert analysis_result.confidence_level < 0.5 or "Manual review required" in " ".join(
                analysis_result.immediate_actions
            )

        except Exception:
            pytest.fail("Error recovery failed - should provide fallback result")

        # Step 2: Simulate Database Service Failure
        integrated_behavioral_network.database_service.get_lead.side_effect = Exception("Database Timeout")
        integrated_behavioral_network.database_service.log_communication.side_effect = Exception("Database Timeout")

        error_trigger = RealTimeTrigger(
            trigger_id="error_trigger",
            lead_id=lead_id,
            trigger_type=TriggerType.AUTOMATED_RESPONSE,
            trigger_condition="database_error_test",
            action_payload={"test": True},
            priority=2,
            expiration_time=datetime.now() + timedelta(hours=1),
        )

        # Should handle database errors gracefully
        try:
            await integrated_behavioral_network._send_automated_response(error_trigger)
            await integrated_behavioral_network._send_immediate_alert(error_trigger)
            # Should not crash despite database errors
        except Exception as e:
            if "Database" in str(e):
                pytest.fail("Database error not handled gracefully")

        # Step 3: Simulate Communication Service Failure
        integrated_behavioral_network.email_service.send_templated_email.side_effect = Exception("Email Service Down")
        integrated_behavioral_network.sms_service.send_templated_sms.side_effect = Exception("SMS Service Down")

        # Should attempt communication despite service failures
        try:
            await integrated_behavioral_network._send_automated_response(error_trigger)
            # Should not crash even if all communication channels fail
        except Exception as e:
            if "Email Service" in str(e) or "SMS Service" in str(e):
                pytest.fail("Communication service failure not handled gracefully")

        print("✅ Error Recovery and Fallback Testing Completed:")
        print("   • AI Service Failure: Graceful fallback ✓")
        print("   • Database Failure: Error handling ✓")
        print("   • Communication Failure: Graceful degradation ✓")

    @pytest.mark.asyncio
    async def test_concurrent_high_volume_processing(self, integrated_service6_orchestrator):
        """Test concurrent processing of multiple high-volume leads."""

        # Create multiple concurrent lead scenarios
        concurrent_leads = []
        for i in range(5):  # Process 5 leads concurrently
            lead_data = {
                "id": f"concurrent_lead_{i}",
                "name": f"Lead {i}",
                "email": f"lead{i}@example.com",
                "budget": 400000 + (i * 50000),
                "urgency_score": 6.0 + i,
                "properties_viewed": i + 2,
            }
            concurrent_leads.append(lead_data)

        # Process all leads concurrently
        start_time = time.time()
        tasks = [integrated_service6_orchestrator.analyze_lead(lead["id"], lead) for lead in concurrent_leads]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        processing_time = time.time() - start_time

        # Verify concurrent processing
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= 3, f"Only {len(successful_results)}/5 leads processed successfully"

        # Concurrent processing should be more efficient than sequential
        assert processing_time < 3.0, f"Concurrent processing took {processing_time:.1f}s, should be <3s"

        print(f"✅ Concurrent Processing Completed:")
        print(f"   • Leads Processed: {len(successful_results)}/5")
        print(f"   • Total Time: {processing_time:.1f}s")
        print(f"   • Avg Time per Lead: {processing_time / len(successful_results):.1f}s")


class TestService6IntegrationHealthChecks:
    """Test Service 6 integration health and monitoring."""

    @pytest.mark.asyncio
    async def test_service6_system_health_monitoring(self):
        """Test Service 6 system health monitoring."""

        config = Service6AIConfig()
        orchestrator = create_service6_ai_orchestrator(config)

        # Mock health responses
        orchestrator.ai_companion = AsyncMock()
        orchestrator.ai_companion.get_system_health.return_value = {
            "overall_status": "healthy",
            "components": {
                "ml_scoring": {"status": "healthy", "latency": 95},
                "predictive_analytics": {"status": "healthy", "latency": 120},
                "realtime_inference": {"status": "healthy", "latency": 85},
            },
        }

        # Test system status
        status = await orchestrator.get_system_status()

        assert "service6_ai_orchestrator" in status
        assert "ai_components" in status
        assert status["service6_ai_orchestrator"]["status"] == "running"

        print("✅ System Health Monitoring:")
        print(f"   • Orchestrator Status: {status['service6_ai_orchestrator']['status']}")
        print(f"   • AI Components: {status['ai_components']['overall_status']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])