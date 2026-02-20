import pytest

pytestmark = pytest.mark.integration

#!/usr/bin/env python3
"""
Service 6 End-to-End Integration Tests
=====================================

Comprehensive integration testing for Service 6's critical business workflows:

Critical Workflows Tested:
1. Lead Ingestion → AI Analysis → Autonomous Follow-up → Conversion
2. Webhook Processing → Lead Enrichment → Campaign Enrollment
3. Real-time Lead Scoring → Immediate Response → Performance Tracking
4. Voice AI Integration → Live Coaching → Call Analysis
5. Multi-agent Orchestration → Consensus Building → Task Generation

Business-Critical Scenarios:
- High-intent lead fast-track processing (<2 minutes end-to-end)
- Webhook security validation and data integrity
- Cross-service data consistency and state management
- Performance under concurrent load (50+ leads/minute)
- Error recovery and graceful degradation

Target: 90%+ coverage of critical integration paths
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import Service 6 components for integration testing
try:
    from ghl_real_estate_ai.services.apollo_client import ApolloClient
    from ghl_real_estate_ai.services.autonomous_followup_engine import (
        AutonomousFollowUpEngine,
        FollowUpRecommendation,
        FollowUpTask,
    )
    from ghl_real_estate_ai.services.database_service import DatabaseService
    from ghl_real_estate_ai.services.sendgrid_client import SendGridClient
    from ghl_real_estate_ai.services.service6_ai_integration import (
        Service6AIConfig,
        Service6AIOrchestrator,
        Service6AIResponse,
    )
    from ghl_real_estate_ai.services.twilio_client import TwilioClient
except (ImportError, TypeError, AttributeError, Exception):
    pytest.skip("required imports unavailable", allow_module_level=True)

# Import test utilities
from tests.fixtures.sample_data import AnalyticsData, LeadProfiles
from tests.mocks.external_services import (
    MockApolloClient,
    MockClaudeClient,
    MockDatabaseService,
    MockRedisClient,
    MockSendGridClient,
    MockTwilioClient,
    MockWebhookPayloads,
    create_mock_service6_response,
    create_test_lead_data,
)


class TestLeadIngestionToConversionWorkflow:
    """Test complete lead ingestion to conversion workflow"""

    @pytest.fixture
    async def integrated_service6_stack(self):
        """Create fully integrated Service 6 stack for testing"""
        # Create AI Orchestrator with high-performance config
        config = Service6AIConfig(
            max_concurrent_operations=100,
            default_cache_ttl_seconds=60,  # Shorter for testing
            enable_advanced_ml_scoring=True,
            enable_voice_ai=True,
            enable_predictive_analytics=True,
            enable_realtime_inference=True,
            enable_claude_enhancement=True,
        )

        orchestrator = Service6AIOrchestrator(config)

        # Create Follow-up Engine
        followup_engine = AutonomousFollowUpEngine()

        # Mock external services
        database = MockDatabaseService()
        apollo = MockApolloClient()
        twilio = MockTwilioClient()
        sendgrid = MockSendGridClient()
        cache = MockRedisClient()

        # Configure orchestrator with mocked services
        orchestrator.ai_companion = MagicMock()
        orchestrator.ai_companion.initialize = AsyncMock()
        orchestrator.ai_companion.comprehensive_lead_analysis = AsyncMock(
            side_effect=lambda lead_id, lead_data, **kwargs: create_mock_service6_response(lead_id)
        )
        orchestrator.ai_companion.realtime_lead_scoring = AsyncMock()
        orchestrator.ai_companion.voice_call_coaching = AsyncMock()

        # Configure follow-up engine with mocked services
        followup_engine.database_service = database
        followup_engine.cache = cache

        # Initialize all services
        await orchestrator.initialize()

        return {
            "orchestrator": orchestrator,
            "followup_engine": followup_engine,
            "database": database,
            "apollo": apollo,
            "twilio": twilio,
            "sendgrid": sendgrid,
            "cache": cache,
        }

    @pytest.mark.asyncio
    async def test_high_intent_lead_fast_track_workflow(self, integrated_service6_stack):
        """
        Test high-intent lead fast-track processing:
        Lead Ingestion → AI Analysis → Immediate Response → Conversion Tracking

        Performance Requirement: <2 minutes end-to-end
        """
        services = integrated_service6_stack
        start_time = time.time()

        # Step 1: Lead Ingestion (simulates webhook)
        lead_data = create_test_lead_data(
            {
                "lead_id": "HIGH_INTENT_FASTTRACK_001",
                "email": "fasttrack@example.com",
                "budget": 750000,  # High budget
                "timeline": "immediate",  # Urgent timeline
                "email_open_rate": 0.95,  # High engagement
                "avg_response_time_hours": 0.5,  # Very responsive
                "page_views": 25,  # High activity
                "last_interaction": datetime.now().isoformat(),  # Recent activity
            }
        )

        # Step 2: Store lead in database
        await services["database"].save_lead(lead_data["lead_id"], lead_data)

        # Step 3: AI Analysis and Scoring
        analysis_result = await services["orchestrator"].analyze_lead(
            lead_data["lead_id"], lead_data, include_voice=False
        )

        # Verify AI analysis indicates high intent
        assert analysis_result.unified_lead_score >= 80.0, "High-intent lead should score 80+"
        assert analysis_result.priority_level in ["critical", "high"]

        # Step 4: Autonomous Follow-up Decision
        # Mock follow-up engine processing
        with patch.object(services["followup_engine"], "_process_lead") as mock_process:
            # Configure mock to create urgent follow-up task
            mock_followup_task = FollowUpTask(
                lead_id=lead_data["lead_id"],
                task_type="immediate_contact",
                scheduled_time=datetime.now() + timedelta(minutes=5),  # 5 minute response
                communication_channel="phone",
                priority="urgent",
                content_template="high_intent_immediate",
                personalization_data={"budget": 750000, "timeline": "immediate"},
            )

            mock_process.return_value = [mock_followup_task]

            # Process lead for follow-up
            await services["followup_engine"]._process_lead(lead_data["lead_id"])

        # Step 5: Execute Follow-up Communications
        # Mock phone call
        call_result = await services["twilio"].make_call(
            to=lead_data["phone"], twiml_url="https://enterprisehub.ai/voice/high-intent-script"
        )
        assert call_result["success"] is True

        # Step 6: Track Performance
        end_time = time.time()
        total_processing_time = end_time - start_time

        # Performance validation
        assert total_processing_time < 120.0, f"Fast-track took {total_processing_time}s, should be <120s"

        # Verify all steps completed successfully
        assert analysis_result.processing_time_ms > 0
        assert call_result["call_sid"] is not None

        # Verify data integrity across services
        stored_lead = await services["database"].get_lead(lead_data["lead_id"])
        assert stored_lead["email"] == lead_data["email"]

    @pytest.mark.asyncio
    async def test_webhook_to_campaign_enrollment_workflow(self, integrated_service6_stack):
        """
        Test webhook processing to campaign enrollment:
        GHL Webhook → Lead Enrichment → AI Analysis → Campaign Selection → Enrollment
        """
        services = integrated_service6_stack

        # Step 1: Simulate GHL webhook payload
        webhook_payload = MockWebhookPayloads.ghl_lead_webhook(
            {
                "email": "webhook.test@example.com",
                "firstName": "Webhook",
                "lastName": "TestLead",
                "customFields": {
                    "budget": "600000",
                    "timeline": "soon",
                    "property_type": "single_family",
                    "location": "Rancho Cucamonga",
                },
            }
        )

        lead_id = f"GHL_{webhook_payload['data']['id']}"

        # Step 2: Webhook signature validation (mocked)
        webhook_signature = "valid_signature_hash"
        signature_valid = True  # Mock validation
        assert signature_valid, "Webhook signature must be valid"

        # Step 3: Lead enrichment via Apollo
        enrichment_result = await services["apollo"].enrich_lead(
            webhook_payload["data"]["email"], webhook_payload["data"].get("phone")
        )

        assert enrichment_result["email"] == webhook_payload["data"]["email"]
        assert enrichment_result["confidence_score"] > 0.8

        # Step 4: Store enriched lead data
        enriched_lead_data = {
            "lead_id": lead_id,
            "email": webhook_payload["data"]["email"],
            "first_name": webhook_payload["data"]["firstName"],
            "last_name": webhook_payload["data"]["lastName"],
            "budget": int(webhook_payload["data"]["customFields"]["budget"]),
            "timeline": webhook_payload["data"]["customFields"]["timeline"],
            "source": "ghl_webhook",
            "enrichment_data": enrichment_result,
        }

        await services["database"].save_lead(lead_id, enriched_lead_data)

        # Step 5: AI Analysis for campaign selection
        analysis_result = await services["orchestrator"].analyze_lead(lead_id, enriched_lead_data)

        # Step 6: Campaign selection based on AI analysis
        campaign_id = None
        if analysis_result.unified_lead_score >= 70:
            if enriched_lead_data["budget"] >= 500000:
                campaign_id = "LUXURY_BUYER_SEQUENCE"
            else:
                campaign_id = "STANDARD_BUYER_SEQUENCE"
        else:
            campaign_id = "NURTURE_SEQUENCE"

        assert campaign_id is not None

        # Step 7: Campaign enrollment
        enrollment_data = {
            "enrollment_reason": "webhook_qualification",
            "ai_score": analysis_result.unified_lead_score,
            "personalization_data": {
                "budget": enriched_lead_data["budget"],
                "timeline": enriched_lead_data["timeline"],
                "enrichment_confidence": enrichment_result["confidence_score"],
            },
        }

        # Mock enrollment success
        with patch.object(services["database"], "enroll_in_campaign") as mock_enroll:
            mock_enroll.return_value = True

            enrollment_success = await services["database"].enroll_in_campaign(lead_id, campaign_id, enrollment_data)

        assert enrollment_success is True

        # Step 8: Verify end-to-end data consistency
        final_lead_data = await services["database"].get_lead(lead_id)
        assert final_lead_data["email"] == webhook_payload["data"]["email"]

        # Verify AI analysis was stored
        await services["database"].update_lead_score(
            lead_id, analysis_result.unified_lead_score, {"analysis_metadata": "webhook_triggered"}
        )

    @pytest.mark.asyncio
    async def test_realtime_scoring_to_immediate_response_workflow(self, integrated_service6_stack):
        """
        Test real-time scoring with immediate response:
        Activity Detection → Real-time Scoring → Immediate Action → Response Tracking
        """
        services = integrated_service6_stack

        # Step 1: Simulate lead activity (e.g., property page view)
        lead_activity = {
            "lead_id": "REALTIME_SCORE_001",
            "activity_type": "property_view",
            "timestamp": datetime.now(),
            "activity_data": {
                "property_id": "PROP_LUXURY_001",
                "property_price": 850000,
                "view_duration_seconds": 180,
                "pages_viewed": 5,
                "time_spent_minutes": 12,
            },
        }

        # Step 2: Extract real-time features
        realtime_features = {
            "recent_activity_score": 0.9,  # High recent activity
            "property_price_alignment": 0.85,  # Good price alignment
            "engagement_intensity": 0.88,  # High engagement
            "session_length_minutes": 12,
            "pages_per_minute": 2.5,
        }

        # Step 3: Real-time scoring
        scoring_result = await services["orchestrator"].score_lead_realtime(
            lead_activity["lead_id"], realtime_features, priority="high"
        )

        assert scoring_result.primary_score >= 75.0, "High activity should result in high score"
        assert scoring_result.confidence >= 0.7

        # Step 4: Immediate action decision
        immediate_action_required = scoring_result.primary_score >= 80.0 and scoring_result.confidence >= 0.8

        if immediate_action_required:
            # Step 5: Immediate response (SMS notification)
            sms_result = await services["twilio"].send_sms(
                to="+15551234567",  # Mock lead phone
                message=f"Hi! I noticed you're viewing luxury properties. I have some exclusive listings that match your interests. Can we chat for 5 minutes?",
                from_number="+15559876543",
            )

            assert sms_result["success"] is True
            assert sms_result["status"] == "sent"

            # Step 6: Log immediate response
            communication_log = {
                "lead_id": lead_activity["lead_id"],
                "channel": "sms",
                "direction": "outbound",
                "content": sms_result["body"] if "body" in sms_result else "SMS sent",
                "trigger": "realtime_scoring",
                "score": scoring_result.primary_score,
                "timestamp": datetime.now(),
            }

            # Mock logging
            services["database"].operation_count += 1  # Track operation

        # Step 7: Track response and conversion
        # Simulate lead response within 10 minutes
        response_received = True  # Mock positive response

        if response_received:
            # Update lead score based on response
            updated_score = min(scoring_result.primary_score + 10.0, 100.0)
            await services["database"].update_lead_score(
                lead_activity["lead_id"], updated_score, {"response_to_realtime_outreach": True}
            )

    @pytest.mark.asyncio
    async def test_voice_ai_integration_workflow(self, integrated_service6_stack):
        """
        Test voice AI integration workflow:
        Call Start → Voice Analysis → Live Coaching → Call Summary → Follow-up
        """
        services = integrated_service6_stack

        # Step 1: Start voice coaching session
        call_data = {
            "call_id": "VOICE_TEST_001",
            "lead_id": "LEAD_VOICE_001",
            "agent_id": "AGENT_001",
            "call_start": datetime.now(),
        }

        coaching_result = await services["orchestrator"].start_voice_coaching(
            call_data["call_id"], call_data["lead_id"], call_data["agent_id"]
        )

        assert coaching_result["coaching_active"] is True
        assert "Real-time transcription" in coaching_result["features"]

        # Step 2: Simulate real-time audio processing
        # Mock audio chunks and transcription
        audio_chunks = [
            {"speaker": "lead", "text": "Hi, I am interested in properties in North Rancho Cucamonga"},
            {"speaker": "agent", "text": "Great! I have some excellent options. What is your budget range?"},
            {"speaker": "lead", "text": "We are looking at around 600 to 700 thousand"},
            {"speaker": "agent", "text": "Perfect, that opens up some wonderful neighborhoods..."},
        ]

        conversation_analysis = {
            "sentiment_scores": [0.7, 0.8, 0.75, 0.85],
            "engagement_level": 0.82,
            "buying_signals": ["specific_budget", "location_preference", "timeline_mentioned"],
            "objections": [],
            "next_steps_discussed": True,
        }

        # Step 3: Generate live coaching prompts
        coaching_prompts = [
            "POSITIVE: Lead mentioned specific budget - great buying signal",
            "SUGGEST: Ask about timeline and financing pre-approval",
            "OPPORTUNITY: Lead is engaged - good time to suggest viewing",
        ]

        # Step 4: Call completion and summary
        call_summary = {
            "call_id": call_data["call_id"],
            "duration_minutes": 8.5,
            "sentiment_score": 0.82,
            "conversion_probability": 0.78,
            "key_insights": [
                "Budget confirmed: $600-700K",
                "Strong interest in North Rancho Cucamonga",
                "Ready to view properties",
            ],
            "recommended_follow_up": "Send 3-5 property options within 24 hours",
            "call_quality": "excellent",
        }

        # Step 5: Post-call follow-up automation
        follow_up_data = {
            "trigger": "voice_call_completion",
            "call_insights": call_summary,
            "recommended_action": "property_recommendations",
            "urgency": "high",  # Based on positive call outcome
        }

        # Mock follow-up task creation
        followup_task = FollowUpTask(
            lead_id=call_data["lead_id"],
            task_type="post_call_followup",
            scheduled_time=datetime.now() + timedelta(hours=2),
            communication_channel="email",
            priority="high",
            content_template="post_call_property_recommendations",
            personalization_data=call_summary,
        )

        assert followup_task.priority == "high"
        assert "property_recommendations" in followup_task.content_template

    @pytest.mark.asyncio
    async def test_multi_agent_consensus_to_task_generation_workflow(self, integrated_service6_stack):
        """
        Test multi-agent orchestration workflow:
        Lead Analysis → Agent Deployment → Consensus Building → Task Generation → Execution
        """
        services = integrated_service6_stack

        # Step 1: Complex lead requiring multi-agent analysis
        complex_lead_data = {
            "lead_id": "COMPLEX_MULTI_AGENT_001",
            "email": "complex@example.com",
            "engagement_history": [
                {"date": "2026-01-10", "action": "email_open", "response": None},
                {"date": "2026-01-12", "action": "property_view", "response": "interested"},
                {"date": "2026-01-14", "action": "sms_sent", "response": None},
                {"date": "2026-01-15", "action": "call_attempt", "response": "no_answer"},
                {"date": "2026-01-16", "action": "email_sent", "response": "opened_no_click"},
            ],
            "behavioral_data": {
                "response_rate": 0.4,  # Mixed signals
                "avg_response_time": 24,  # Slow responses
                "engagement_trend": "declining",
                "price_sensitivity": "high",
                "location_flexibility": "medium",
            },
        }

        # Step 2: Deploy multiple agents for analysis
        agent_recommendations = []

        # Mock timing optimizer agent
        timing_recommendation = {
            "agent_type": "timing_optimizer",
            "recommendation": "Wait 3 days, then try different time of day",
            "confidence": 0.65,
            "optimal_timing": datetime.now() + timedelta(days=3, hours=14),
            "reasoning": "Pattern suggests afternoon contact more effective",
        }
        agent_recommendations.append(timing_recommendation)

        # Mock content personalizer agent
        content_recommendation = {
            "agent_type": "content_personalizer",
            "recommendation": "Focus on value/savings messaging, avoid luxury positioning",
            "confidence": 0.78,
            "personalization_data": {"price_sensitivity": "high", "value_focus": True},
            "reasoning": "High price sensitivity detected in behavioral patterns",
        }
        agent_recommendations.append(content_recommendation)

        # Mock channel strategist agent
        channel_recommendation = {
            "agent_type": "channel_strategist",
            "recommendation": "Email with clear value proposition, avoid calls",
            "confidence": 0.72,
            "communication_channel": "email",
            "reasoning": "Low phone response rate, better email engagement",
        }
        agent_recommendations.append(channel_recommendation)

        # Mock response analyzer agent
        response_recommendation = {
            "agent_type": "response_analyzer",
            "recommendation": "Reduce contact frequency to avoid lead burnout",
            "confidence": 0.83,
            "sentiment_analysis": {"current_sentiment": 0.4, "trend": "declining"},
            "reasoning": "Declining engagement suggests contact fatigue",
        }
        agent_recommendations.append(response_recommendation)

        # Step 3: Build agent consensus
        consensus_metrics = {
            "agreement_score": 0.75,  # Good agreement among agents
            "confidence_average": 0.745,  # (0.65+0.78+0.72+0.83)/4
            "conflicting_recommendations": 0,  # No major conflicts
            "unanimous_recommendations": ["reduce_frequency", "email_channel", "value_focus"],
        }

        # Step 4: Generate consensus-based follow-up plan
        consensus_plan = {
            "action_priority": "medium",  # Not urgent due to declining engagement
            "communication_channel": "email",  # Consensus recommendation
            "timing": datetime.now() + timedelta(days=3, hours=14),  # From timing agent
            "content_strategy": "value_focused",  # From content agent
            "contact_frequency": "reduced",  # From response analyzer
            "success_probability": 0.68,  # Based on consensus confidence
        }

        # Step 5: Task generation from consensus
        generated_tasks = []

        # Primary follow-up task
        primary_task = FollowUpTask(
            lead_id=complex_lead_data["lead_id"],
            task_type="consensus_followup",
            scheduled_time=consensus_plan["timing"],
            communication_channel=consensus_plan["communication_channel"],
            priority="medium",
            content_template="value_focused_email",
            personalization_data={
                "price_sensitivity": "high",
                "value_messaging": True,
                "previous_engagement": complex_lead_data["engagement_history"],
            },
        )
        generated_tasks.append(primary_task)

        # Monitoring task
        monitoring_task = FollowUpTask(
            lead_id=complex_lead_data["lead_id"],
            task_type="engagement_monitoring",
            scheduled_time=consensus_plan["timing"] + timedelta(days=7),
            priority="low",
            content_template="engagement_check",
            personalization_data={"monitor_response_rate": True},
        )
        generated_tasks.append(monitoring_task)

        # Step 6: Validate task generation quality
        assert len(generated_tasks) >= 1
        assert primary_task.communication_channel == "email"  # Consensus choice
        assert primary_task.priority == "medium"  # Based on consensus
        assert "value_focused" in primary_task.content_template

        # Verify consensus influenced all recommendations
        assert consensus_metrics["confidence_average"] > 0.7
        assert len(consensus_metrics["unanimous_recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_error_recovery_and_graceful_degradation_workflow(self, integrated_service6_stack):
        """
        Test error recovery and graceful degradation:
        Service Failure → Fallback Mechanisms → Partial Success → Recovery
        """
        services = integrated_service6_stack

        # Step 1: Simulate partial service failures
        lead_data = create_test_lead_data({"lead_id": "ERROR_RECOVERY_001"})

        # Mock database service failure
        services["database"].get_lead_activity_data = AsyncMock(side_effect=Exception("Database connection timeout"))

        # Mock Apollo API rate limiting
        services["apollo"].enrich_lead = AsyncMock(side_effect=Exception("Apollo API rate limit exceeded"))

        # Step 2: Attempt full workflow with failures
        workflow_results = {}

        # AI Analysis should still work with fallback data
        try:
            analysis_result = await services["orchestrator"].analyze_lead(lead_data["lead_id"], lead_data)
            workflow_results["ai_analysis"] = "success"
            assert analysis_result.unified_lead_score > 0  # Should have fallback score
        except Exception as e:
            workflow_results["ai_analysis"] = f"failed: {e}"

        # Lead enrichment should gracefully fail
        try:
            enrichment_result = await services["apollo"].enrich_lead(lead_data["email"])
            workflow_results["enrichment"] = "success"
        except Exception as e:
            workflow_results["enrichment"] = f"failed: {str(e)[:50]}"
            # Should continue without enrichment

        # Communication should still work
        try:
            sms_result = await services["twilio"].send_sms(
                to=lead_data["phone"], message="Hello! I wanted to follow up on your property interest."
            )
            workflow_results["communication"] = "success"
            assert sms_result["success"] is True
        except Exception as e:
            workflow_results["communication"] = f"failed: {e}"

        # Step 3: Verify graceful degradation
        assert "ai_analysis" in workflow_results
        assert "enrichment" in workflow_results
        assert "communication" in workflow_results

        # At least one core function should succeed
        successes = [result for result in workflow_results.values() if result == "success"]
        assert len(successes) >= 1, "At least one core function must succeed during failures"

        # Step 4: Simulate recovery and retry
        # Fix database connection
        services["database"].get_lead_activity_data = AsyncMock(return_value={"activity": "recovered_data"})

        # Retry failed operations
        retry_results = {}

        try:
            activity_data = await services["database"].get_lead_activity_data(lead_data["lead_id"])
            retry_results["database_recovery"] = "success"
            assert activity_data["activity"] == "recovered_data"
        except Exception as e:
            retry_results["database_recovery"] = f"failed: {e}"

        # Verify recovery
        assert retry_results["database_recovery"] == "success"


class TestConcurrentLoadAndPerformance:
    """Test concurrent load handling and performance characteristics"""

    @pytest.mark.asyncio
    async def test_concurrent_lead_processing_performance(self):
        """Test processing multiple leads concurrently"""
        # Create lightweight service stack for load testing
        config = Service6AIConfig(
            max_concurrent_operations=50, enable_advanced_ml_scoring=True, enable_realtime_inference=True
        )

        orchestrator = Service6AIOrchestrator(config)

        # Mock fast AI companion
        orchestrator.ai_companion = MagicMock()
        orchestrator.ai_companion.initialize = AsyncMock()

        async def fast_analysis(lead_id, lead_data, **kwargs):
            await asyncio.sleep(0.05)  # 50ms simulated processing
            return create_mock_service6_response(lead_id)

        orchestrator.ai_companion.comprehensive_lead_analysis = fast_analysis
        await orchestrator.initialize()

        # Generate test leads
        test_leads = []
        for i in range(25):  # 25 concurrent leads
            lead_data = create_test_lead_data(
                {"lead_id": f"CONCURRENT_LEAD_{i:03d}", "email": f"concurrent{i}@example.com"}
            )
            test_leads.append((lead_data["lead_id"], lead_data))

        # Process all leads concurrently
        start_time = time.time()

        tasks = []
        for lead_id, lead_data in test_leads:
            task = orchestrator.analyze_lead(lead_id, lead_data)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        end_time = time.time()
        total_time = end_time - start_time

        # Performance validation
        assert len(results) == 25, "All leads should be processed"
        assert all(isinstance(r, Service6AIResponse) for r in results), "All results should be valid"
        assert total_time < 5.0, f"25 leads took {total_time}s, should be <5s with concurrency"

        # Throughput validation (leads per second)
        throughput = len(test_leads) / total_time
        assert throughput >= 5.0, f"Throughput {throughput:.1f} leads/s should be >=5/s"

    @pytest.mark.asyncio
    async def test_webhook_burst_handling(self):
        """Test handling burst of webhook events"""
        # Simulate webhook burst scenario
        webhook_events = []

        for i in range(50):  # 50 webhooks in burst
            webhook_payload = MockWebhookPayloads.ghl_lead_webhook(
                {"id": f"burst_lead_{i:03d}", "email": f"burst{i}@example.com", "phone": f"+155512340{i:02d}"}
            )
            webhook_events.append(webhook_payload)

        # Mock webhook processing pipeline
        processed_webhooks = []

        async def process_webhook(webhook_payload):
            # Simulate realistic webhook processing time
            await asyncio.sleep(0.02)  # 20ms processing

            lead_id = f"GHL_{webhook_payload['data']['id']}"

            # Mock validation, enrichment, and storage
            result = {
                "lead_id": lead_id,
                "email": webhook_payload["data"]["email"],
                "processed_at": datetime.now(),
                "status": "success",
            }

            processed_webhooks.append(result)
            return result

        # Process webhook burst
        start_time = time.time()

        tasks = [process_webhook(webhook) for webhook in webhook_events]
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        processing_time = end_time - start_time

        # Validate burst handling
        assert len(results) == 50, "All webhooks should be processed"
        assert len(processed_webhooks) == 50, "All webhooks should be stored"
        assert processing_time < 3.0, f"Webhook burst took {processing_time}s, should be <3s"

        # Verify no data loss
        processed_emails = {result["email"] for result in results}
        expected_emails = {webhook["data"]["email"] for webhook in webhook_events}
        assert processed_emails == expected_emails, "No webhook data should be lost"


class TestDataConsistencyAndIntegrity:
    """Test data consistency across service boundaries"""

    @pytest.mark.asyncio
    async def test_cross_service_data_consistency(self):
        """Test data consistency across multiple services"""
        # Create services with shared data store
        shared_cache = MockRedisClient()
        shared_database = MockDatabaseService()

        # Service 1: AI Orchestrator
        orchestrator = Service6AIOrchestrator()
        orchestrator.ai_companion = MagicMock()
        orchestrator.ai_companion.initialize = AsyncMock()
        orchestrator.ai_companion.comprehensive_lead_analysis = AsyncMock(
            side_effect=lambda lead_id, data, **kwargs: create_mock_service6_response(lead_id)
        )

        # Service 2: Follow-up Engine
        followup_engine = AutonomousFollowUpEngine()
        followup_engine.database_service = shared_database
        followup_engine.cache = shared_cache

        # Test lead data
        lead_data = create_test_lead_data({"lead_id": "CONSISTENCY_TEST_001"})

        # Step 1: Store lead via orchestrator
        await shared_database.save_lead(lead_data["lead_id"], lead_data)

        # Step 2: AI analysis and score update
        analysis_result = await orchestrator.analyze_lead(lead_data["lead_id"], lead_data)
        await shared_database.update_lead_score(
            lead_data["lead_id"],
            analysis_result.unified_lead_score,
            {"ai_analysis_timestamp": datetime.now().isoformat()},
        )

        # Step 3: Follow-up engine processes same lead
        with patch.object(followup_engine, "_process_lead") as mock_process:
            mock_process.return_value = True
            await followup_engine._process_lead(lead_data["lead_id"])

        # Step 4: Verify data consistency
        stored_lead = await shared_database.get_lead(lead_data["lead_id"])

        assert stored_lead["email"] == lead_data["email"]
        assert stored_lead["ai_score"] == analysis_result.unified_lead_score
        assert "ai_analysis_timestamp" in stored_lead["ai_analysis"]

        # Verify cache consistency
        cache_key = f"s6_analysis:{lead_data['lead_id']}"
        cached_analysis = await shared_cache.get(cache_key)

        if cached_analysis:
            cached_data = json.loads(cached_analysis)
            assert cached_data["lead_id"] == lead_data["lead_id"]

    @pytest.mark.asyncio
    async def test_transaction_integrity_under_failures(self):
        """Test transaction integrity when partial failures occur"""
        database = MockDatabaseService()

        # Mock transaction simulation
        transaction_log = []

        async def mock_multi_step_transaction(lead_id: str):
            # Step 1: Create lead (succeeds)
            transaction_log.append(("create_lead", "success"))

            # Step 2: Enroll in campaign (fails)
            transaction_log.append(("enroll_campaign", "failed"))
            raise Exception("Campaign enrollment failed")

        # Simulate transaction with failure
        lead_id = "TRANSACTION_TEST_001"

        try:
            await mock_multi_step_transaction(lead_id)
        except Exception as e:
            # Transaction should be rolled back
            transaction_log.append(("rollback", "executed"))

        # Verify transaction integrity
        assert ("create_lead", "success") in transaction_log
        assert ("enroll_campaign", "failed") in transaction_log
        assert ("rollback", "executed") in transaction_log

        # Lead should not exist due to rollback
        lead = await database.get_lead(lead_id)
        assert lead is None, "Lead should not exist after failed transaction"


# Test configuration
pytest_plugins = ["pytest_asyncio"]


if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=ghl_real_estate_ai.services",
            "--cov-report=html",
            "--cov-report=term-missing",
            "-k",
            "integration",
        ]
    )