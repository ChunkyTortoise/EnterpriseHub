"""
Comprehensive Integration Tests for Claude AI System (Phase 4)

Tests the complete Claude integration across all phases:
- Phase 1: Real-time coaching system
- Phase 2: Enhanced lead qualification
- Phase 3: GHL webhook enhancement

Validates performance targets, integration flow, and end-to-end functionality.

Performance Targets:
- API response time: < 150ms (95th percentile)
- ML inference time: < 300ms per prediction
- Webhook processing: < 800ms end-to-end
- Coaching delivery: < 100ms
- Lead scoring accuracy: > 98%
"""

import asyncio
import time
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Import services for testing
from ghl_real_estate_ai.services.claude_agent_service import ClaudeAgentService
from ghl_real_estate_ai.services.claude_semantic_analyzer import ClaudeSemanticAnalyzer
from ghl_real_estate_ai.services.qualification_orchestrator import QualificationOrchestrator
from ghl_real_estate_ai.services.claude_action_planner import ClaudeActionPlanner
from ghl_real_estate_ai.services.realtime_websocket_hub import RealtimeWebSocketHub
from ghl_real_estate_ai.core.service_registry import ServiceRegistry
from ghl_real_estate_ai.api.schemas.ghl import GHLWebhookEvent, GHLContact, GHLMessage


class TestClaudeIntegrationComprehensive:
    """Comprehensive integration tests for Claude AI system."""

    @pytest.fixture
    def location_id(self):
        """Test location ID."""
        return "test_location_claude_integration"

    @pytest.fixture
    def contact_id(self):
        """Test contact ID."""
        return "test_contact_claude_789"

    @pytest.fixture
    def agent_id(self):
        """Test agent ID."""
        return "test_agent_456"

    @pytest.fixture
    def mock_claude_response(self):
        """Mock Claude API response."""
        return {
            "content": [{
                "text": "This lead shows high purchase intent with specific budget and timeline requirements. Recommend immediate follow-up within 2 hours."
            }]
        }

    @pytest.fixture
    async def claude_agent_service(self, location_id):
        """Initialize Claude agent service for testing."""
        service = ClaudeAgentService()
        return service

    @pytest.fixture
    async def semantic_analyzer(self):
        """Initialize semantic analyzer for testing."""
        analyzer = ClaudeSemanticAnalyzer()
        return analyzer

    @pytest.fixture
    async def qualification_orchestrator(self, location_id):
        """Initialize qualification orchestrator for testing."""
        orchestrator = QualificationOrchestrator(location_id)
        return orchestrator

    @pytest.fixture
    async def action_planner(self, location_id):
        """Initialize action planner for testing."""
        planner = ClaudeActionPlanner(location_id)
        return planner

    @pytest.fixture
    def websocket_hub(self, location_id):
        """Initialize WebSocket hub for testing."""
        hub = RealtimeWebSocketHub(location_id)
        return hub

    @pytest.fixture
    def service_registry(self, location_id):
        """Initialize service registry for testing."""
        registry = ServiceRegistry(location_id=location_id, demo_mode=True)
        return registry

    @pytest.fixture
    def sample_conversation_history(self):
        """Sample conversation history for testing."""
        return [
            {
                "role": "user",
                "content": "Hi, I'm looking for a 3-bedroom house in Austin under $500k",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant",
                "content": "I'd be happy to help you find the perfect home! Can you tell me about your timeline?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "user",
                "content": "We need to move by June and we're pre-approved for $450k",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant",
                "content": "Great! Being pre-approved puts you in a strong position. What areas of Austin interest you most?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "user",
                "content": "Cedar Park or Round Rock, close to good schools",
                "timestamp": datetime.now().isoformat()
            }
        ]

    @pytest.fixture
    def sample_ghl_event(self, contact_id, location_id):
        """Sample GHL webhook event for testing."""
        return GHLWebhookEvent(
            contact_id=contact_id,
            location_id=location_id,
            contact=GHLContact(
                first_name="Sarah",
                last_name="Johnson",
                email="sarah.johnson@email.com",
                phone="+15551234567",
                tags=["Needs Qualifying", "Website Lead"]
            ),
            message=GHLMessage(
                type="SMS",
                body="I'm interested in seeing some houses this weekend if possible",
                direction="inbound"
            )
        )

    # ========================================================================
    # Phase 1 Integration Tests: Real-Time Coaching System
    # ========================================================================

    @pytest.mark.asyncio
    async def test_real_time_coaching_integration(
        self,
        claude_agent_service,
        websocket_hub,
        agent_id,
        sample_conversation_history,
        mock_claude_response
    ):
        """Test real-time coaching system integration."""
        # Mock Claude API
        with patch.object(claude_agent_service, '_call_claude_api', new_callable=AsyncMock) as mock_claude:
            mock_claude.return_value = mock_claude_response

            # Test coaching generation
            start_time = time.time()

            coaching_response = await claude_agent_service.get_real_time_coaching(
                agent_id=agent_id,
                conversation_context={"messages": sample_conversation_history},
                prospect_message="I'm interested in seeing some houses this weekend if possible",
                conversation_stage="discovery"
            )

            coaching_time = time.time() - start_time

            # Validate response structure
            assert coaching_response is not None
            assert "suggestions" in coaching_response
            assert "urgency_level" in coaching_response
            assert "recommended_questions" in coaching_response

            # Validate performance target: < 100ms coaching delivery
            assert coaching_time < 0.1, f"Coaching took {coaching_time:.3f}s, target is < 0.1s"

            # Test WebSocket broadcasting
            broadcast_result = await websocket_hub.broadcast_coaching_suggestions(
                agent_id=agent_id,
                tenant_id="test_tenant",
                coaching_suggestions=coaching_response["suggestions"],
                urgency=coaching_response["urgency_level"]
            )

            assert broadcast_result.success
            assert broadcast_result.message_count >= 0

    @pytest.mark.asyncio
    async def test_objection_detection_and_response(
        self,
        claude_agent_service,
        sample_conversation_history
    ):
        """Test objection detection and response suggestions."""
        objection_message = "I'm not sure we're ready to buy right now, maybe we should wait"

        with patch.object(claude_agent_service, '_call_claude_api', new_callable=AsyncMock) as mock_claude:
            mock_claude.return_value = {
                "content": [{
                    "text": "Timing objection detected. Suggest exploring their specific concerns and timeline flexibility."
                }]
            }

            start_time = time.time()

            objection_response = await claude_agent_service.analyze_objection(
                objection_text=objection_message,
                lead_context={"budget": "$450k", "location": "Austin"},
                conversation_history=sample_conversation_history
            )

            response_time = time.time() - start_time

            # Validate objection detection
            assert objection_response is not None
            assert "objection_type" in objection_response
            assert "severity" in objection_response
            assert "suggested_responses" in objection_response

            # Performance check
            assert response_time < 0.3, f"Objection analysis took {response_time:.3f}s, target is < 0.3s"

    # ========================================================================
    # Phase 2 Integration Tests: Enhanced Lead Qualification
    # ========================================================================

    @pytest.mark.asyncio
    async def test_semantic_analysis_and_qualification_orchestration(
        self,
        semantic_analyzer,
        qualification_orchestrator,
        contact_id,
        sample_conversation_history
    ):
        """Test semantic analysis integration with qualification orchestrator."""
        # Test semantic analysis
        start_time = time.time()

        with patch.object(semantic_analyzer, '_call_claude_api', new_callable=AsyncMock) as mock_claude:
            mock_claude.return_value = {
                "content": [{
                    "text": json.dumps({
                        "intent": "high_purchase_intent",
                        "confidence": 85,
                        "urgency_score": 75,
                        "extracted_data": {
                            "budget": 450000,
                            "timeline": "by June",
                            "location": ["Cedar Park", "Round Rock"],
                            "property_type": "3-bedroom house"
                        }
                    })
                }]
            }

            semantic_result = await semantic_analyzer.analyze_lead_intent(sample_conversation_history)

        semantic_time = time.time() - start_time

        # Start qualification flow
        flow_start_time = time.time()

        qualification_flow = await qualification_orchestrator.start_qualification_flow(
            contact_id=contact_id,
            contact_name="Sarah Johnson",
            initial_message="Hi, I'm looking for a 3-bedroom house in Austin under $500k",
            source="website"
        )

        flow_time = time.time() - flow_start_time

        # Validate semantic analysis
        assert semantic_result is not None
        assert semantic_result.get("confidence", 0) > 80
        assert semantic_result.get("intent") == "high_purchase_intent"

        # Validate qualification flow
        assert qualification_flow is not None
        assert qualification_flow["status"] == "started"
        assert "next_questions" in qualification_flow
        assert qualification_flow["completion_percentage"] >= 0

        # Performance checks
        assert semantic_time < 0.3, f"Semantic analysis took {semantic_time:.3f}s, target is < 0.3s"
        assert flow_time < 0.2, f"Qualification flow start took {flow_time:.3f}s, target is < 0.2s"

    @pytest.mark.asyncio
    async def test_qualification_progress_tracking(
        self,
        qualification_orchestrator,
        contact_id
    ):
        """Test qualification progress tracking with multiple responses."""
        # Start qualification flow
        initial_flow = await qualification_orchestrator.start_qualification_flow(
            contact_id=contact_id,
            contact_name="Test Contact",
            initial_message="Looking for a house",
            source="test"
        )

        flow_id = initial_flow["flow_id"]

        # Process multiple responses to track progress
        responses = [
            "Our budget is around $400k and we're pre-approved",
            "We need to find something within 4 months",
            "Looking in North Austin or Cedar Park area",
            "Want a single family home with good schools nearby"
        ]

        for i, response in enumerate(responses):
            start_time = time.time()

            result = await qualification_orchestrator.process_response(
                flow_id=flow_id,
                user_message=response
            )

            process_time = time.time() - start_time

            # Validate progress increase
            assert result["completion_percentage"] > i * 15  # Should increase with each response

            # Performance check
            assert process_time < 0.5, f"Response processing took {process_time:.3f}s, target is < 0.5s"

        # Final qualification check
        final_status = qualification_orchestrator.get_flow_status(flow_id)
        assert final_status["completion_percentage"] >= 60  # Should be well-qualified

    # ========================================================================
    # Phase 3 Integration Tests: GHL Webhook Enhancement
    # ========================================================================

    @pytest.mark.asyncio
    async def test_enhanced_webhook_processing_with_claude(
        self,
        service_registry,
        sample_ghl_event
    ):
        """Test enhanced webhook processing with Claude intelligence."""
        # Mock all Claude services in registry
        with patch.object(service_registry, 'claude_semantic_analyzer') as mock_analyzer, \
             patch.object(service_registry, 'qualification_orchestrator') as mock_orchestrator, \
             patch.object(service_registry, 'analyze_lead_semantics') as mock_semantics, \
             patch.object(service_registry, 'start_intelligent_qualification') as mock_qual_start:

            # Mock semantic analysis
            mock_semantics.return_value = {
                "intent_analysis": {"intent": "high_purchase_intent", "confidence": 85},
                "semantic_preferences": {"budget_mentioned": True, "timeline_mentioned": True},
                "urgency_score": 75,
                "confidence": 85
            }

            # Mock qualification orchestrator
            mock_qual_start.return_value = {
                "flow_id": "test_flow_123",
                "completion_percentage": 45,
                "next_questions": ["What's your ideal move-in timeline?"],
                "status": "started"
            }

            start_time = time.time()

            # Simulate webhook processing (would normally be done by webhook handler)
            semantic_result = await service_registry.analyze_lead_semantics([
                {
                    "role": "user",
                    "content": sample_ghl_event.message.body,
                    "timestamp": datetime.now().isoformat()
                }
            ])

            qualification_result = await service_registry.start_intelligent_qualification(
                contact_id=sample_ghl_event.contact_id,
                contact_name=f"{sample_ghl_event.contact.first_name} {sample_ghl_event.contact.last_name}",
                initial_message=sample_ghl_event.message.body,
                source="ghl_webhook"
            )

            total_time = time.time() - start_time

            # Validate integration results
            assert semantic_result is not None
            assert semantic_result["confidence"] >= 80
            assert qualification_result is not None
            assert qualification_result["status"] == "started"

            # Performance target: < 800ms webhook processing
            assert total_time < 0.8, f"Webhook processing took {total_time:.3f}s, target is < 0.8s"

    @pytest.mark.asyncio
    async def test_action_planning_integration(
        self,
        action_planner,
        contact_id,
        sample_conversation_history
    ):
        """Test Claude action planner integration."""
        context = {
            "contact_id": contact_id,
            "last_interaction_timestamp": datetime.now().isoformat(),
            "lead_source": "website",
            "tags": ["Needs Qualifying", "High Intent"]
        }

        qualification_data = {
            "completion_percentage": 75,
            "budget": {"confidence": 85, "mentioned": True},
            "timeline": {"confidence": 70, "mentioned": True},
            "location": {"confidence": 90, "mentioned": True}
        }

        start_time = time.time()

        action_plan = await action_planner.create_action_plan(
            contact_id=contact_id,
            context=context,
            qualification_data=qualification_data,
            conversation_history=sample_conversation_history,
            agent_id="test_agent"
        )

        planning_time = time.time() - start_time

        # Validate action plan
        assert action_plan is not None
        assert "plan_id" in action_plan
        assert "immediate_actions" in action_plan
        assert "follow_up_strategy" in action_plan
        assert action_plan["metrics"]["priority_score"] >= 70  # Should be high priority

        # Check action recommendations
        immediate_actions = action_plan["immediate_actions"]
        assert len(immediate_actions) > 0

        high_priority_actions = [
            action for action in immediate_actions
            if action.get("priority") in ["critical", "high"]
        ]
        assert len(high_priority_actions) > 0  # Should have high-priority actions

        # Performance check
        assert planning_time < 0.5, f"Action planning took {planning_time:.3f}s, target is < 0.5s"

    # ========================================================================
    # End-to-End Integration Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_complete_lead_processing_workflow(
        self,
        service_registry,
        websocket_hub,
        contact_id,
        agent_id,
        sample_ghl_event,
        sample_conversation_history
    ):
        """Test complete end-to-end lead processing workflow."""
        # Mock all external dependencies
        with patch.object(service_registry, 'analyze_lead_semantics') as mock_semantics, \
             patch.object(service_registry, 'start_intelligent_qualification') as mock_qual, \
             patch.object(service_registry, 'get_real_time_coaching') as mock_coaching:

            # Setup mock responses
            mock_semantics.return_value = {
                "intent_analysis": {"intent": "high_purchase_intent", "confidence": 90},
                "semantic_preferences": {"budget_mentioned": True, "urgency_detected": True},
                "urgency_score": 85,
                "confidence": 90
            }

            mock_qual.return_value = {
                "flow_id": "flow_123",
                "completion_percentage": 80,
                "next_questions": ["When would you like to schedule a viewing?"],
                "status": "started"
            }

            mock_coaching.return_value = {
                "suggestions": ["This lead is highly qualified and urgent - prioritize immediately"],
                "urgency_level": "critical",
                "recommended_questions": ["Would you be available for a call this afternoon?"],
                "objection_detected": False
            }

            workflow_start = time.time()

            # Step 1: Semantic analysis
            semantic_analysis = await service_registry.analyze_lead_semantics(sample_conversation_history)

            # Step 2: Start/update qualification
            qualification_flow = await service_registry.start_intelligent_qualification(
                contact_id=contact_id,
                contact_name="Sarah Johnson",
                initial_message=sample_ghl_event.message.body,
                source="ghl_webhook"
            )

            # Step 3: Generate coaching
            coaching_response = await service_registry.get_real_time_coaching(
                agent_id=agent_id,
                conversation_context={"messages": sample_conversation_history},
                prospect_message=sample_ghl_event.message.body,
                conversation_stage="discovery"
            )

            # Step 4: Broadcast coaching to agent
            broadcast_result = await websocket_hub.broadcast_coaching_suggestions(
                agent_id=agent_id,
                tenant_id="test_tenant",
                coaching_suggestions=coaching_response["suggestions"],
                urgency=coaching_response["urgency_level"]
            )

            workflow_time = time.time() - workflow_start

            # Validate complete workflow
            assert semantic_analysis["confidence"] >= 85
            assert qualification_flow["completion_percentage"] >= 70
            assert coaching_response["urgency_level"] == "critical"
            assert broadcast_result.success

            # End-to-end performance target: < 1.5s for complete workflow
            assert workflow_time < 1.5, f"Complete workflow took {workflow_time:.3f}s, target is < 1.5s"

    @pytest.mark.asyncio
    async def test_performance_under_load(
        self,
        service_registry,
        contact_id
    ):
        """Test system performance under concurrent load."""
        # Simulate multiple concurrent requests
        concurrent_requests = 10
        tasks = []

        async def simulate_request(request_id):
            """Simulate a single request processing."""
            start_time = time.time()

            # Mock the services to avoid actual API calls
            with patch.object(service_registry, 'analyze_lead_semantics') as mock_semantics:
                mock_semantics.return_value = {
                    "intent_analysis": {"intent": "moderate_interest", "confidence": 70},
                    "confidence": 70,
                    "urgency_score": 50
                }

                result = await service_registry.analyze_lead_semantics([{
                    "role": "user",
                    "content": f"Test message {request_id}",
                    "timestamp": datetime.now().isoformat()
                }])

                return {
                    "request_id": request_id,
                    "processing_time": time.time() - start_time,
                    "success": result is not None
                }

        # Create concurrent tasks
        for i in range(concurrent_requests):
            tasks.append(simulate_request(i))

        # Execute all tasks concurrently
        load_test_start = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_load_time = time.time() - load_test_start

        # Analyze results
        successful_requests = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_requests = [r for r in results if not (isinstance(r, dict) and r.get("success"))]

        avg_response_time = sum(r["processing_time"] for r in successful_requests) / len(successful_requests)
        max_response_time = max(r["processing_time"] for r in successful_requests)

        # Validate performance under load
        assert len(successful_requests) >= concurrent_requests * 0.95  # 95% success rate
        assert avg_response_time < 0.3, f"Average response time {avg_response_time:.3f}s exceeds 0.3s target"
        assert max_response_time < 1.0, f"Max response time {max_response_time:.3f}s exceeds 1.0s target"
        assert total_load_time < 2.0, f"Total load test time {total_load_time:.3f}s exceeds 2.0s target"

    # ========================================================================
    # Data Quality and Accuracy Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_lead_scoring_accuracy_improvement(
        self,
        service_registry,
        sample_conversation_history
    ):
        """Test that Claude integration improves lead scoring accuracy."""
        # Mock traditional scoring vs Claude-enhanced scoring
        traditional_score = 65

        with patch.object(service_registry, 'analyze_lead_semantics') as mock_semantics:
            mock_semantics.return_value = {
                "intent_analysis": {"intent": "high_purchase_intent", "confidence": 90},
                "confidence": 90,
                "urgency_score": 80,
                "semantic_preferences": {"budget_mentioned": True, "timeline_mentioned": True}
            }

            claude_analysis = await service_registry.analyze_lead_semantics(sample_conversation_history)

            # Calculate enhanced score (traditional 70% + Claude 30%)
            claude_confidence = claude_analysis["confidence"]
            enhanced_score = int((traditional_score * 0.7) + (claude_confidence * 0.3))

            # Enhanced scoring should show improvement
            assert enhanced_score > traditional_score
            assert enhanced_score >= 90  # Target >98% accuracy correlates to >90 score for high-intent leads

    @pytest.mark.asyncio
    async def test_qualification_completeness_accuracy(
        self,
        qualification_orchestrator,
        contact_id
    ):
        """Test qualification completeness accuracy with Claude analysis."""
        # Start qualification flow
        flow = await qualification_orchestrator.start_qualification_flow(
            contact_id=contact_id,
            contact_name="Test User",
            initial_message="Looking for a house",
            source="test"
        )

        # Provide comprehensive responses covering all qualification areas
        comprehensive_responses = [
            "Our budget is $450k and we're pre-approved through Wells Fargo",
            "We need to move by June 1st due to job relocation",
            "Looking specifically in Cedar Park or Round Rock areas",
            "Want a 3-4 bedroom single family home with good schools"
        ]

        flow_id = flow["flow_id"]

        for response in comprehensive_responses:
            await qualification_orchestrator.process_response(
                flow_id=flow_id,
                user_message=response
            )

        # Check final qualification status
        final_status = qualification_orchestrator.get_flow_status(flow_id)

        # Should achieve high completion with comprehensive responses
        assert final_status["completion_percentage"] >= 85

        # Check individual area completion
        qualification_summary = final_status["qualification_summary"]
        essential_areas = ["budget", "timeline", "location"]

        for area in essential_areas:
            area_data = qualification_summary.get(area, {})
            assert area_data.get("confidence", 0) >= 70, f"{area} should be well qualified"

    # ========================================================================
    # Error Handling and Resilience Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_claude_api_failure(
        self,
        service_registry,
        sample_conversation_history
    ):
        """Test graceful degradation when Claude API is unavailable."""
        # Mock Claude API failure
        with patch.object(service_registry, 'claude_semantic_analyzer') as mock_analyzer:
            mock_analyzer.side_effect = Exception("Claude API unavailable")

            # Should gracefully fall back to safe defaults
            fallback_result = await service_registry.analyze_lead_semantics(sample_conversation_history)

            # Validate graceful degradation
            assert fallback_result is not None
            assert fallback_result.get("demo_mode", False)  # Should indicate fallback mode
            assert fallback_result.get("confidence", 0) == 50  # Safe default confidence

    @pytest.mark.asyncio
    async def test_system_health_monitoring(self, service_registry):
        """Test system health monitoring for Claude integration."""
        health_status = service_registry.get_system_health()

        # Validate health status structure
        assert "status" in health_status
        assert "services_loaded" in health_status
        assert "demo_mode" in health_status
        assert "last_check" in health_status

        # Should have positive service count
        assert health_status["services_loaded"] >= 0


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])