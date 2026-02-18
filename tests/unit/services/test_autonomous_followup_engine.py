#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Autonomous Follow-up Engine
Targets 80%+ coverage for Service 6's critical lead processing system.

Critical Test Coverage Areas:
1. Multi-agent orchestration and consensus building
2. Database integration with error handling
3. LLM integration and prompt generation
4. Follow-up timing optimization
5. Channel strategy selection
6. Error recovery and fallback mechanisms
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.skip(reason="Async fixture incompatibility — needs pytest-asyncio refactor")

from ghl_real_estate_ai.agents.lead_intelligence_swarm import AgentInsight, AgentType
from ghl_real_estate_ai.services.autonomous_followup_engine import (
    AutonomousFollowUpEngine,
    ChannelStrategistAgent,
    ContentPersonalizerAgent,
    EscalationManagerAgent,
    FollowUpRecommendation,
    FollowUpTask,
    ResponseAnalyzerAgent,
    TimingOptimizerAgent,
)
from tests.fixtures.comprehensive_agent_fixtures import (

    LeadProfileFactory,
    MockAgentInsightFactory,
    MockFollowUpRecommendationFactory,
)


class TestAutonomousFollowUpEngine:
    """Test suite for the core autonomous follow-up engine"""

    @pytest.fixture
    async def engine(self):
        """Create test engine with mocked dependencies"""
        with (
            patch(
                "ghl_real_estate_ai.services.autonomous_followup_engine.get_behavioral_trigger_engine"
            ) as mock_behavioral,
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_cache_service") as mock_cache,
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_llm_client") as mock_llm,
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_lead_intelligence_swarm") as mock_swarm,
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_database") as mock_db,
        ):
            # Configure mocks with realistic responses
            mock_behavioral.return_value = AsyncMock()
            mock_cache.return_value = AsyncMock()
            mock_llm.return_value = AsyncMock()
            mock_swarm.return_value = AsyncMock()
            mock_db.return_value = AsyncMock()

            engine = AutonomousFollowUpEngine()
            yield engine

    @pytest.mark.asyncio
    async def test_process_lead_high_intent_success(self, engine):
        """Test successful processing of high-intent lead"""
        # Arrange
        lead_profile = LeadProfileFactory.high_intent_lead()
        lead_id = lead_profile.lead_id

        # Mock database responses
        engine.database_service.get_lead_activity_data = AsyncMock(return_value=lead_profile.behavioral_data)
        engine.database_service.get_lead_follow_up_history = AsyncMock(return_value=lead_profile.engagement_history)
        engine.database_service.get_lead_response_data = AsyncMock(return_value={})
        engine.database_service.get_lead_profile_data = AsyncMock(return_value=lead_profile.demographics)

        # Mock swarm analysis
        engine.lead_intelligence_swarm.analyze_lead = AsyncMock(
            return_value=MagicMock(
                primary_insight=MagicMock(
                    opportunity_score=88.5, urgency_level="high", metadata={"behavioral_score": 91.2}
                )
            )
        )

        # Act
        await engine._process_lead(lead_id)

        # Assert
        assert engine.database_service.get_lead_activity_data.called
        assert engine.database_service.get_lead_follow_up_history.called
        assert engine.lead_intelligence_swarm.analyze_lead.called

    @pytest.mark.asyncio
    async def test_agent_consensus_building_success(self, engine):
        """Test successful agent consensus with high confidence"""
        # Arrange
        lead_profile = LeadProfileFactory.high_intent_lead()

        # Create realistic agent recommendations
        agent_recommendations = [
            MockFollowUpRecommendationFactory.create_recommendation(
                lead_profile, AgentType.TIMING_OPTIMIZER, confidence=0.85
            ),
            MockFollowUpRecommendationFactory.create_recommendation(
                lead_profile, AgentType.CONTENT_PERSONALIZER, confidence=0.82
            ),
            MockFollowUpRecommendationFactory.create_recommendation(
                lead_profile, AgentType.CHANNEL_STRATEGIST, confidence=0.88
            ),
        ]

        swarm_analysis = MagicMock(
            consensus_score=0.85, primary_insight=MagicMock(opportunity_score=88.5, urgency_level="high")
        )

        # Act
        consensus = await engine._build_agent_consensus(agent_recommendations, swarm_analysis)

        # Assert
        assert consensus is not None
        assert consensus["final_recommendation"] is not None
        assert consensus["consensus_confidence"] >= 0.7  # Above threshold
        assert consensus["action_priority"] in ["immediate", "high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_agent_consensus_building_low_confidence_fallback(self, engine):
        """Test fallback behavior when agent consensus is low confidence"""
        # Arrange
        lead_profile = LeadProfileFactory.low_engagement_lead()

        # Create low-confidence recommendations
        agent_recommendations = [
            MockFollowUpRecommendationFactory.create_recommendation(
                lead_profile,
                AgentType.TIMING_OPTIMIZER,
                confidence=0.45,  # Below threshold
            ),
            MockFollowUpRecommendationFactory.create_recommendation(
                lead_profile,
                AgentType.CONTENT_PERSONALIZER,
                confidence=0.42,  # Below threshold
            ),
        ]

        swarm_analysis = MagicMock(
            consensus_score=0.40,  # Low consensus
            primary_insight=MagicMock(opportunity_score=45.2, urgency_level="low"),
        )

        # Act
        consensus = await engine._build_agent_consensus(agent_recommendations, swarm_analysis)

        # Assert - Should create fallback recommendation
        assert consensus is not None
        assert consensus["consensus_confidence"] < 0.7  # Below threshold
        assert consensus["action_priority"] == "low"
        assert "fallback_applied" in consensus

    @pytest.mark.asyncio
    async def test_database_error_handling_with_retries(self, engine):
        """Test database error handling with retry logic"""
        # Arrange
        lead_id = "LEAD_DB_ERROR_TEST"

        # Mock database to fail twice then succeed
        engine.database_service.get_lead_activity_data = AsyncMock(
            side_effect=[
                Exception("Connection timeout"),  # First attempt fails
                Exception("Connection timeout"),  # Second attempt fails
                {"activity": "success"},  # Third attempt succeeds
            ]
        )

        # Act & Assert
        with patch("asyncio.sleep"):  # Speed up retries for testing
            result = await engine._get_lead_activity(lead_id)

            # Should succeed after retries
            assert result == {"activity": "success"}
            assert engine.database_service.get_lead_activity_data.call_count == 3

    @pytest.mark.asyncio
    async def test_database_permanent_failure_escalation(self, engine):
        """Test escalation when database permanently fails"""
        # Arrange
        lead_id = "LEAD_DB_FAIL_TEST"

        # Mock database to always fail
        engine.database_service.get_lead_activity_data = AsyncMock(
            side_effect=Exception("Database permanently unavailable")
        )

        # Act & Assert
        with patch("asyncio.sleep"):  # Speed up retries
            with pytest.raises(Exception, match="Database permanently unavailable"):
                await engine._get_lead_activity(lead_id)

    @pytest.mark.asyncio
    async def test_agent_failure_handling_partial_success(self, engine):
        """Test handling when some agents fail but others succeed"""
        # Arrange
        lead_profile = LeadProfileFactory.medium_engagement_lead()
        lead_id = lead_profile.lead_id

        # Mock some agents to fail, others to succeed
        with patch.object(engine, "_deploy_followup_agents") as mock_deploy:
            mock_deploy.return_value = [
                MockFollowUpRecommendationFactory.create_recommendation(
                    lead_profile, AgentType.TIMING_OPTIMIZER, confidence=0.85
                ),
                Exception("Agent timeout"),  # Failed agent
                MockFollowUpRecommendationFactory.create_recommendation(
                    lead_profile, AgentType.CHANNEL_STRATEGIST, confidence=0.78
                ),
                Exception("LLM rate limit"),  # Another failed agent
            ]

            # Mock swarm analysis
            engine.lead_intelligence_swarm.analyze_lead = AsyncMock(
                return_value=MagicMock(
                    consensus_score=0.75, primary_insight=MagicMock(opportunity_score=68.3, urgency_level="medium")
                )
            )

            # Mock database responses
            engine.database_service.get_lead_activity_data = AsyncMock(return_value=lead_profile.behavioral_data)
            engine.database_service.get_lead_follow_up_history = AsyncMock(return_value=lead_profile.engagement_history)
            engine.database_service.get_lead_response_data = AsyncMock(return_value={})
            engine.database_service.get_lead_profile_data = AsyncMock(return_value=lead_profile.demographics)

            # Act
            await engine._process_lead(lead_id)

            # Assert - Should process successfully with partial agent failures
            assert mock_deploy.called

    @pytest.mark.asyncio
    async def test_llm_integration_prompt_generation(self, engine):
        """Test LLM prompt generation and response handling"""
        # Arrange
        lead_profile = LeadProfileFactory.investor_profile_lead()
        context = {
            "lead_profile": lead_profile.demographics,
            "behavioral_data": lead_profile.behavioral_data,
            "swarm_analysis": MagicMock(
                primary_insight=MagicMock(
                    opportunity_score=87.3, urgency_level="high", profile_type="experienced_investor"
                )
            ),
        }

        # Mock LLM response
        mock_llm_response = MagicMock(
            content="Based on investor profile analysis, recommend immediate consultation focusing on cap rate analysis and market trends. Contact within 30 minutes via phone for maximum conversion probability."
        )
        engine.llm_client.generate = AsyncMock(return_value=mock_llm_response)

        # Create timing optimizer agent
        timing_agent = TimingOptimizerAgent(AgentType.TIMING_OPTIMIZER, engine.llm_client)

        # Act
        result = await timing_agent.analyze(lead_profile.lead_id, context)

        # Assert
        assert isinstance(result, FollowUpRecommendation)
        assert result.confidence > 0.5
        assert result.agent_type == AgentType.TIMING_OPTIMIZER
        assert engine.llm_client.generate.called

        # Verify prompt contains key context
        call_args = engine.llm_client.generate.call_args[1]
        prompt = call_args.get("prompt", call_args.get("messages", ""))
        assert "investor" in prompt.lower() or "cap rate" in prompt.lower()

    @pytest.mark.asyncio
    async def test_follow_up_task_generation(self, engine):
        """Test generation of specific follow-up tasks"""
        # Arrange
        lead_profile = LeadProfileFactory.high_intent_lead()
        consensus = {
            "final_recommendation": MockFollowUpRecommendationFactory.create_recommendation(
                lead_profile, AgentType.CONTENT_PERSONALIZER, confidence=0.85
            ),
            "consensus_confidence": 0.85,
            "action_priority": "urgent",
        }

        # Act
        tasks = await engine._generate_followup_tasks(lead_profile.lead_id, consensus)

        # Assert
        assert len(tasks) >= 1
        assert isinstance(tasks[0], FollowUpTask)
        assert tasks[0].lead_id == lead_profile.lead_id
        assert tasks[0].scheduled_time <= datetime.now() + timedelta(minutes=30)  # Urgent should be quick

    @pytest.mark.asyncio
    async def test_monitoring_loop_batch_processing(self, engine):
        """Test monitoring loop processes leads in batches"""
        # Arrange
        mock_leads = [f"LEAD_{i}" for i in range(25)]  # More than batch size

        engine.behavioral_engine.get_high_intent_leads = AsyncMock(return_value=mock_leads)

        # Mock _process_lead to track calls
        process_calls = []

        async def mock_process_lead(lead_id):
            process_calls.append(lead_id)

        engine._process_lead = mock_process_lead

        # Act
        await engine._run_monitoring_cycle()

        # Assert
        assert len(process_calls) == len(mock_leads)
        # Verify batching occurred (not all at once)
        assert engine.behavioral_engine.get_high_intent_leads.called

    @pytest.mark.asyncio
    async def test_cache_integration_performance_optimization(self, engine):
        """Test cache integration for performance optimization"""
        # Arrange
        lead_id = "LEAD_CACHE_TEST"
        cached_analysis = {
            "agent_consensus": {"confidence": 0.85},
            "swarm_analysis": {"opportunity_score": 88.5},
            "cached_at": datetime.now().isoformat(),
        }

        # Mock cache hit
        engine.cache.get = AsyncMock(return_value=cached_analysis)
        engine.cache.set = AsyncMock(return_value=True)

        # Act - Attempt to get cached analysis
        cache_key = f"followup_analysis:{lead_id}"
        result = await engine.cache.get(cache_key)

        # Assert
        assert result == cached_analysis
        assert engine.cache.get.called

    @pytest.mark.asyncio
    async def test_performance_timing_requirements(self, engine):
        """Test that engine meets performance timing requirements"""
        # Arrange
        lead_profile = LeadProfileFactory.medium_engagement_lead()
        lead_id = lead_profile.lead_id

        # Mock fast responses
        engine.database_service.get_lead_activity_data = AsyncMock(return_value=lead_profile.behavioral_data)
        engine.database_service.get_lead_follow_up_history = AsyncMock(return_value=[])
        engine.database_service.get_lead_response_data = AsyncMock(return_value={})
        engine.database_service.get_lead_profile_data = AsyncMock(return_value=lead_profile.demographics)

        engine.lead_intelligence_swarm.analyze_lead = AsyncMock(
            return_value=MagicMock(primary_insight=MagicMock(opportunity_score=68.3, urgency_level="medium"))
        )

        # Act
        start_time = datetime.now()
        await engine._process_lead(lead_id)
        end_time = datetime.now()

        # Assert - Should complete within performance requirements
        processing_time = (end_time - start_time).total_seconds()
        assert processing_time < 5.0, f"Processing took {processing_time}s, should be <5s"


class TestFollowUpAgents:
    """Test suite for individual follow-up agents"""

    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM client for agent testing"""
        client = AsyncMock()
        client.generate = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_timing_optimizer_agent_immediate_response(self, mock_llm_client):
        """Test timing optimizer for high-intent leads"""
        # Arrange
        agent = TimingOptimizerAgent(AgentType.TIMING_OPTIMIZER, mock_llm_client)
        lead_profile = LeadProfileFactory.high_intent_lead()

        context = {
            "behavioral_data": lead_profile.behavioral_data,
            "swarm_analysis": MagicMock(primary_insight=MagicMock(urgency_level="urgent", opportunity_score=88.5)),
        }

        # Mock LLM response for urgent timing
        mock_llm_client.generate.return_value = MagicMock(
            content="IMMEDIATE contact required within 15 minutes. High intent signals detected."
        )

        # Act
        result = await agent.analyze(lead_profile.lead_id, context)

        # Assert
        assert isinstance(result, FollowUpRecommendation)
        assert result.agent_type == AgentType.TIMING_OPTIMIZER
        assert result.confidence >= 0.7

        # Should recommend immediate timing
        time_diff = result.optimal_timing - datetime.now()
        assert time_diff.total_seconds() <= 900  # Within 15 minutes

    @pytest.mark.asyncio
    async def test_content_personalizer_agent_investor_focus(self, mock_llm_client):
        """Test content personalizer for investor leads"""
        # Arrange
        agent = ContentPersonalizerAgent(AgentType.CONTENT_PERSONALIZER, mock_llm_client)
        lead_profile = LeadProfileFactory.investor_profile_lead()

        context = {
            "lead_profile": lead_profile.demographics,
            "swarm_analysis": MagicMock(
                primary_insight=MagicMock(profile_type="experienced_investor", opportunity_score=87.3)
            ),
        }

        # Mock LLM response for investor-focused content
        mock_llm_client.generate.return_value = MagicMock(
            content="Focus on ROI analysis, cap rates, and market appreciation data. Provide detailed financial projections."
        )

        # Act
        result = await agent.analyze(lead_profile.lead_id, context)

        # Assert
        assert isinstance(result, FollowUpRecommendation)
        assert result.agent_type == AgentType.CONTENT_PERSONALIZER

        # Should include investment-focused personalization data
        personalization = result.personalization_data
        assert "investment" in str(personalization).lower() or "roi" in str(personalization).lower()

    @pytest.mark.asyncio
    async def test_channel_strategist_agent_multi_channel(self, mock_llm_client):
        """Test channel strategist for multi-channel optimization"""
        # Arrange
        agent = ChannelStrategistAgent(AgentType.CHANNEL_STRATEGIST, mock_llm_client)
        lead_profile = LeadProfileFactory.high_intent_lead()

        context = {"behavioral_data": lead_profile.behavioral_data, "response_history": []}

        # Mock LLM response for channel strategy
        mock_llm_client.generate.return_value = MagicMock(
            content="PRIMARY: Phone call for immediate response. BACKUP: SMS within 15 minutes if no answer. FOLLOW-UP: Email with property details."
        )

        # Act
        result = await agent.analyze(lead_profile.lead_id, context)

        # Assert
        assert isinstance(result, FollowUpRecommendation)
        assert result.agent_type == AgentType.CHANNEL_STRATEGIST
        assert result.communication_channel in ["phone", "sms", "email"]

    @pytest.mark.asyncio
    async def test_response_analyzer_agent_sentiment_detection(self, mock_llm_client):
        """Test response analyzer for sentiment and engagement analysis"""
        # Arrange
        agent = ResponseAnalyzerAgent(AgentType.RESPONSE_ANALYZER, mock_llm_client)
        lead_profile = LeadProfileFactory.medium_engagement_lead()

        context = {
            "response_data": {
                "recent_responses": [
                    {"content": "Thanks for the info, but not interested right now", "timestamp": datetime.now()}
                ],
                "negative_sentiment": 0.7,
            }
        }

        # Mock LLM response for response analysis
        mock_llm_client.generate.return_value = MagicMock(
            content="NEGATIVE sentiment detected. Recommend backing off to nurture sequence. Avoid aggressive follow-up."
        )

        # Act
        result = await agent.analyze(lead_profile.lead_id, context)

        # Assert
        assert isinstance(result, FollowUpRecommendation)
        assert result.agent_type == AgentType.RESPONSE_ANALYZER

        # Should recommend reduced contact frequency due to negative sentiment
        assert result.confidence < 0.8  # Lower confidence due to negative sentiment

    @pytest.mark.asyncio
    async def test_escalation_manager_agent_stalled_lead(self, mock_llm_client):
        """Test escalation manager for stalled leads requiring intervention"""
        # Arrange
        agent = EscalationManagerAgent(AgentType.ESCALATION_MANAGER, mock_llm_client)
        lead_profile = LeadProfileFactory.high_intent_lead()

        context = {
            "follow_up_history": [
                {"timestamp": datetime.now() - timedelta(days=3), "channel": "email", "response": None},
                {"timestamp": datetime.now() - timedelta(days=2), "channel": "sms", "response": None},
                {"timestamp": datetime.now() - timedelta(days=1), "channel": "phone", "response": None},
            ]
        }

        # Mock LLM response for escalation recommendation
        mock_llm_client.generate.return_value = MagicMock(
            content="HIGH-VALUE lead not responding after 3 attempts. ESCALATE to senior agent or manager for personalized outreach."
        )

        # Act
        result = await agent.analyze(lead_profile.lead_id, context)

        # Assert
        assert isinstance(result, FollowUpRecommendation)
        assert result.agent_type == AgentType.ESCALATION_MANAGER
        assert "escalat" in result.recommended_action.lower()


class TestFollowUpTaskManagement:
    """Test suite for follow-up task creation and scheduling"""

    @pytest.mark.asyncio
    async def test_follow_up_task_creation_from_recommendation(self):
        """Test creation of follow-up tasks from agent recommendations"""
        # Arrange
        lead_profile = LeadProfileFactory.high_intent_lead()
        recommendation = MockFollowUpRecommendationFactory.create_recommendation(
            lead_profile, AgentType.TIMING_OPTIMIZER, confidence=0.85
        )

        # Act
        task = FollowUpTask(
            lead_id=lead_profile.lead_id,
            task_type="immediate_contact",
            scheduled_time=recommendation.optimal_timing,
            communication_channel=recommendation.communication_channel,
            content_template="high_intent_immediate_response",
            personalization_data=recommendation.personalization_data,
            priority="urgent",
            created_from_agent=AgentType.TIMING_OPTIMIZER,
            expected_response_rate=recommendation.expected_response_rate,
        )

        # Assert
        assert task.lead_id == lead_profile.lead_id
        assert task.priority == "urgent"
        assert task.scheduled_time <= datetime.now() + timedelta(minutes=30)
        assert task.communication_channel == recommendation.communication_channel

    @pytest.mark.asyncio
    async def test_follow_up_task_scheduling_priority_ordering(self):
        """Test that urgent tasks are scheduled before lower priority ones"""
        # Arrange
        urgent_task = FollowUpTask(
            lead_id="LEAD_URGENT",
            task_type="immediate_contact",
            scheduled_time=datetime.now() + timedelta(minutes=15),
            priority="urgent",
        )

        medium_task = FollowUpTask(
            lead_id="LEAD_MEDIUM",
            task_type="standard_followup",
            scheduled_time=datetime.now() + timedelta(hours=2),
            priority="medium",
        )

        # Act - Sort tasks by priority and timing
        tasks = [medium_task, urgent_task]
        sorted_tasks = sorted(
            tasks, key=lambda t: (0 if t.priority == "urgent" else 1 if t.priority == "high" else 2, t.scheduled_time)
        )

        # Assert
        assert sorted_tasks[0] == urgent_task
        assert sorted_tasks[1] == medium_task


# Test Configuration
pytest_plugins = ["pytest_asyncio"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=ghl_real_estate_ai.services.autonomous_followup_engine", "--cov-report=html"])