import pytest
pytestmark = pytest.mark.integration

"""
Tests for Autonomous Follow-up Engine - AI-Powered Lead Nurturing System

Tests the autonomous follow-up engine that uses multi-agent intelligence to automatically
nurture leads, optimize communication timing, personalize content, and maximize conversions.
"""

import asyncio
from dataclasses import asdict
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from ghl_real_estate_ai.services.autonomous_followup_engine import (
    AgentType,
    AutonomousFollowUpEngine,
    ChannelStrategistAgent,
    ContentPersonalizerAgent,
    ConversionOptimizerAgent,
    EscalationManagerAgent,
    FollowUpAgent,
    FollowUpChannel,
    FollowUpRecommendation,
    FollowUpStatus,
    FollowUpTask,
    MarketContextAgent,
    ObjectionHandlerAgent,
    PerformanceTrackerAgent,
    ResponseAnalyzerAgent,
    SentimentAnalystAgent,
    TimingOptimizerAgent,
    get_autonomous_followup_engine,
)
from ghl_real_estate_ai.services.behavioral_trigger_engine import IntentLevel


class TestAutonomousFollowUpEngine:
    """Test suite for AutonomousFollowUpEngine core functionality."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies for the engine."""
        with (
            patch(
                "ghl_real_estate_ai.services.autonomous_followup_engine.get_behavioral_trigger_engine"
            ) as mock_behavioral,
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_cache_service") as mock_cache,
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_llm_client") as mock_llm,
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_lead_intelligence_swarm") as mock_swarm,
        ):
            yield {
                "behavioral": mock_behavioral.return_value,
                "cache": mock_cache.return_value,
                "llm": mock_llm.return_value,
                "swarm": mock_swarm.return_value,
            }

    @pytest.fixture
    def engine(self, mock_dependencies):
        """Create an AutonomousFollowUpEngine instance for testing."""
        return AutonomousFollowUpEngine()

    @pytest.fixture
    def sample_follow_up_task(self):
        """Sample follow-up task for testing."""
        return FollowUpTask(
            task_id="task_123",
            lead_id="lead_456",
            contact_id="contact_456",
            channel=FollowUpChannel.EMAIL,
            message="Personalized follow-up message about luxury properties",
            scheduled_time=datetime.now() + timedelta(hours=2),
            priority=1,
            status=FollowUpStatus.PENDING,
            metadata={},
            created_at=datetime.now(),
        )

    @pytest.fixture
    def sample_lead_data(self):
        """Sample lead data for follow-up processing."""
        return {
            "lead_id": "lead_789",
            "name": "Michael Johnson",
            "email": "michael.j@example.com",
            "phone": "+1234567890",
            "created_at": datetime.now() - timedelta(days=10),
            "last_contact": datetime.now() - timedelta(hours=48),
            "status": "warm",
            "conversation_history": [
                {
                    "timestamp": datetime.now() - timedelta(hours=72),
                    "message": "Interested in properties around $600K in north Rancho Cucamonga",
                    "type": "inbound",
                    "channel": "email",
                    "sentiment": "positive",
                },
                {
                    "timestamp": datetime.now() - timedelta(hours=49),
                    "message": "I have some great options to show you. When are you available?",
                    "type": "outbound",
                    "channel": "email",
                },
            ],
            "behavioral_data": {
                "response_time_avg_hours": 6,
                "engagement_score": 0.72,
                "preferred_contact_times": ["9-11am", "2-4pm"],
                "channel_preferences": {"email": 0.8, "sms": 0.6, "phone": 0.4},
                "last_website_visit": datetime.now() - timedelta(hours=18),
                "property_views_count": 8,
                "saved_properties": 3,
            },
            "demographics": {
                "age_range": "28-35",
                "income_bracket": "medium_high",
                "family_status": "young_professional",
                "location": "North Rancho Cucamonga, CA",
                "buy_timeline": "3-6_months",
            },
            "current_sentiment": "interested_but_cautious",
            "objections": ["price_concerns", "location_uncertainty"],
            "interests": ["modern_homes", "good_schools", "commute_friendly"],
        }

    @pytest.fixture
    def sample_agent_recommendations(self):
        """Sample recommendations from different agents."""
        return [
            FollowUpRecommendation(
                agent_type=AgentType.TIMING_OPTIMIZER,
                confidence=0.87,
                recommended_action="send_email",
                reasoning="Best historical response time for this lead profile",
                optimal_timing=datetime.now() + timedelta(hours=24),
                suggested_channel=FollowUpChannel.EMAIL,
                metadata={},
            ),
            FollowUpRecommendation(
                agent_type=AgentType.CONTENT_PERSONALIZER,
                confidence=0.82,
                recommended_action="personalize_content",
                reasoning="Lead shows interest in family-oriented features",
                suggested_channel=FollowUpChannel.EMAIL,
                suggested_message="Personalized content about school districts and commute times",
                metadata={"tone": "professional_friendly", "urgency": "moderate"},
            ),
            FollowUpRecommendation(
                agent_type=AgentType.SENTIMENT_ANALYST,
                confidence=0.79,
                recommended_action="reassure_lead",
                reasoning="Lead is engaged but needs reassurance",
                metadata={"current_sentiment": "cautiously_optimistic", "engagement_level": "moderate_high"},
            ),
        ]

    def test_engine_initialization(self, engine):
        """Test that the autonomous follow-up engine initializes correctly."""
        assert isinstance(engine, AutonomousFollowUpEngine)
        assert hasattr(engine, "behavioral_engine")
        assert hasattr(engine, "cache")
        assert hasattr(engine, "llm_client")
        assert hasattr(engine, "lead_intelligence_swarm")

        # Verify all specialized agents are initialized
        assert hasattr(engine, "timing_optimizer")
        assert hasattr(engine, "content_personalizer")
        assert hasattr(engine, "channel_strategist")
        assert hasattr(engine, "response_analyzer")
        assert hasattr(engine, "escalation_manager")
        assert hasattr(engine, "sentiment_analyst")
        assert hasattr(engine, "objection_handler")
        assert hasattr(engine, "conversion_optimizer")
        assert hasattr(engine, "market_context_agent")
        assert hasattr(engine, "performance_tracker")

        # Verify task management components
        assert isinstance(engine.pending_tasks, list)
        assert hasattr(engine, "task_lock")
        assert engine.is_running is False
        assert engine.monitor_task is None

        # Verify configuration parameters
        assert engine.monitoring_interval_seconds > 0
        assert engine.max_daily_followups_per_lead > 0
        assert engine.batch_size > 0
        assert 0 < engine.agent_consensus_threshold <= 1

    def test_get_autonomous_followup_engine_singleton(self):
        """Test that the global engine function returns a singleton."""
        with (
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_behavioral_trigger_engine"),
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_cache_service"),
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_llm_client"),
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_lead_intelligence_swarm"),
        ):
            engine1 = get_autonomous_followup_engine()
            engine2 = get_autonomous_followup_engine()
            assert engine1 is engine2
            assert isinstance(engine1, AutonomousFollowUpEngine)

    @pytest.mark.asyncio
    async def test_start_monitoring(self, engine):
        """Test starting the monitoring loop."""
        with patch.object(engine, "_monitoring_loop", new_callable=AsyncMock) as mock_loop:
            await engine.start_monitoring()

            assert engine.is_running is True
            assert engine.monitor_task is not None

    @pytest.mark.asyncio
    async def test_stop_monitoring(self, engine):
        """Test stopping the monitoring loop."""

        # Create a real asyncio task that we can cancel
        async def dummy_loop():
            await asyncio.sleep(3600)

        engine.is_running = True
        engine.monitor_task = asyncio.ensure_future(dummy_loop())

        await engine.stop_monitoring()

        assert engine.is_running is False
        assert engine.monitor_task.cancelled()

    @pytest.mark.asyncio
    async def test_monitoring_loop(self, engine):
        """Test the core monitoring loop functionality."""
        engine.is_running = True

        with (
            patch.object(engine, "monitor_and_respond", new_callable=AsyncMock) as mock_monitor,
            patch.object(engine, "execute_pending_tasks", new_callable=AsyncMock) as mock_execute,
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            # Mock monitor_and_respond to stop after first iteration
            mock_monitor.side_effect = [None, Exception("Stop loop")]

            try:
                await engine._monitoring_loop()
            except Exception:
                pass  # Expected to stop the loop

            # Verify both monitoring and execution were called
            mock_monitor.assert_called()
            mock_execute.assert_called()
            mock_sleep.assert_called()

    @pytest.mark.asyncio
    async def test_monitor_and_respond(self, engine):
        """Test monitoring and responding to lead activities."""
        # Mock behavioral engine returning high-intent leads
        engine.behavioral_engine.get_high_intent_leads = AsyncMock(return_value=["lead_1", "lead_2"])

        with patch.object(engine, "_process_lead", new_callable=AsyncMock) as mock_process:
            await engine.monitor_and_respond()

            # Verify leads were processed
            assert mock_process.call_count == 2
            mock_process.assert_any_call("lead_1")
            mock_process.assert_any_call("lead_2")

    @pytest.mark.asyncio
    async def test_execute_pending_tasks(self, engine, sample_follow_up_task):
        """Test execution of pending follow-up tasks."""
        # Set task to SCHEDULED and due now
        sample_follow_up_task.status = FollowUpStatus.SCHEDULED
        sample_follow_up_task.scheduled_time = datetime.now() - timedelta(minutes=1)
        engine.pending_tasks = [sample_follow_up_task]

        with (
            patch.object(engine, "_execute_task", new_callable=AsyncMock) as mock_execute,
            patch(
                "ghl_real_estate_ai.services.autonomous_followup_engine.get_database", new_callable=AsyncMock
            ) as mock_db,
        ):
            # Mock database returning no tasks, so fallback to in-memory
            mock_db.return_value.get_pending_follow_up_tasks = AsyncMock(return_value=None)

            await engine.execute_pending_tasks()

            # Verify task execution was attempted
            mock_execute.assert_called_once_with(sample_follow_up_task)

    @pytest.mark.asyncio
    async def test_execute_task_email(self, engine, sample_follow_up_task):
        """Test execution of email follow-up task."""
        sample_follow_up_task.channel = FollowUpChannel.EMAIL
        sample_follow_up_task.status = FollowUpStatus.SCHEDULED
        engine.pending_tasks = [sample_follow_up_task]

        with (
            patch.object(engine, "_send_email", new_callable=AsyncMock, return_value=True) as mock_send,
            patch(
                "ghl_real_estate_ai.services.autonomous_followup_engine.get_database", new_callable=AsyncMock
            ) as mock_db,
        ):
            mock_db.return_value.update_follow_up_task = AsyncMock()

            await engine._execute_task(sample_follow_up_task)

            # Verify email was sent with contact_id and message
            mock_send.assert_called_once_with(sample_follow_up_task.contact_id, sample_follow_up_task.message)

            # Verify task status was updated to SENT
            assert sample_follow_up_task.status == FollowUpStatus.SENT

    @pytest.mark.asyncio
    async def test_execute_task_sms(self, engine, sample_follow_up_task):
        """Test execution of SMS follow-up task."""
        sample_follow_up_task.channel = FollowUpChannel.SMS
        sample_follow_up_task.status = FollowUpStatus.SCHEDULED
        engine.pending_tasks = [sample_follow_up_task]

        with (
            patch.object(engine, "_send_sms", new_callable=AsyncMock, return_value=True) as mock_send,
            patch(
                "ghl_real_estate_ai.services.autonomous_followup_engine.get_database", new_callable=AsyncMock
            ) as mock_db,
        ):
            mock_db.return_value.update_follow_up_task = AsyncMock()

            await engine._execute_task(sample_follow_up_task)

            # Verify SMS was sent with contact_id and message
            mock_send.assert_called_once_with(sample_follow_up_task.contact_id, sample_follow_up_task.message)

            # Verify task status was updated to SENT
            assert sample_follow_up_task.status == FollowUpStatus.SENT

    @pytest.mark.asyncio
    async def test_execute_task_call(self, engine, sample_follow_up_task):
        """Test execution of call follow-up task."""
        sample_follow_up_task.channel = FollowUpChannel.CALL
        sample_follow_up_task.status = FollowUpStatus.SCHEDULED
        engine.pending_tasks = [sample_follow_up_task]

        with (
            patch.object(engine, "_initiate_call", new_callable=AsyncMock, return_value=True) as mock_call,
            patch(
                "ghl_real_estate_ai.services.autonomous_followup_engine.get_database", new_callable=AsyncMock
            ) as mock_db,
        ):
            mock_db.return_value.update_follow_up_task = AsyncMock()

            await engine._execute_task(sample_follow_up_task)

            # Verify call was initiated with contact_id
            mock_call.assert_called_once_with(sample_follow_up_task.contact_id)

            # Verify task status was updated to SENT
            assert sample_follow_up_task.status == FollowUpStatus.SENT

    @pytest.mark.asyncio
    async def test_execute_task_failure_handling(self, engine, sample_follow_up_task):
        """Test handling of task execution failures."""
        sample_follow_up_task.channel = FollowUpChannel.EMAIL
        sample_follow_up_task.status = FollowUpStatus.SCHEDULED
        engine.pending_tasks = [sample_follow_up_task]

        with (
            patch.object(engine, "_send_email", new_callable=AsyncMock, return_value=False) as mock_send,
            patch(
                "ghl_real_estate_ai.services.autonomous_followup_engine.get_database", new_callable=AsyncMock
            ) as mock_db,
        ):
            mock_db.return_value.update_follow_up_task = AsyncMock()

            await engine._execute_task(sample_follow_up_task)

            # Verify email send was attempted
            mock_send.assert_called_once_with(sample_follow_up_task.contact_id, sample_follow_up_task.message)

            # Verify task status was updated to FAILED
            assert sample_follow_up_task.status == FollowUpStatus.FAILED

    @pytest.mark.asyncio
    async def test_build_agent_consensus(self, engine, sample_agent_recommendations):
        """Test building consensus among specialized agents."""
        # Create a mock swarm_analysis object
        mock_swarm_analysis = MagicMock()
        mock_swarm_analysis.consensus.intent_level = IntentLevel.HOT

        consensus = await engine._build_agent_consensus(sample_agent_recommendations, mock_swarm_analysis)

        # Verify consensus is a dict with expected keys
        assert isinstance(consensus, dict)
        assert "confidence" in consensus
        assert "timing" in consensus
        assert "message" in consensus
        assert "channel" in consensus
        assert "priority" in consensus

    @pytest.mark.asyncio
    async def test_handle_escalation(self, engine):
        """Test escalation handling for leads."""
        lead_id = "lead_123"
        escalation_rec = FollowUpRecommendation(
            agent_type=AgentType.ESCALATION_MANAGER,
            confidence=0.9,
            recommended_action="Escalate to human agent",
            reasoning="Multiple attempts without response",
            escalation_needed=True,
        )
        mock_swarm_analysis = MagicMock()
        mock_swarm_analysis.consensus.urgency_level = "high"
        mock_swarm_analysis.consensus.primary_finding = "Lead needs human intervention"

        engine.cache.set = AsyncMock()

        await engine._handle_escalation(lead_id, escalation_rec, mock_swarm_analysis)

        # Verify escalation was recorded in cache
        engine.cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_agent_performance(self, engine, sample_agent_recommendations):
        """Test updating agent performance metrics."""
        await engine._update_agent_performance(sample_agent_recommendations)

        # Verify performance was updated for recommendations
        for rec in sample_agent_recommendations:
            agent_perf = engine.agent_performance.get(rec.agent_type)
            assert agent_perf is not None
            assert agent_perf["total_recommendations"] >= 1

    @pytest.mark.asyncio
    async def test_get_follow_up_history(self, engine):
        """Test retrieval of follow-up history."""
        lead_id = "lead_123"

        with patch(
            "ghl_real_estate_ai.services.autonomous_followup_engine.get_database", new_callable=AsyncMock
        ) as mock_db:
            mock_db.return_value.get_lead_follow_up_history = AsyncMock(return_value=[])

            history = await engine._get_follow_up_history(lead_id)

            # Should return list
            assert isinstance(history, list)

    @pytest.mark.asyncio
    async def test_get_response_data(self, engine):
        """Test retrieval of response data."""
        lead_id = "lead_123"

        with patch(
            "ghl_real_estate_ai.services.autonomous_followup_engine.get_database", new_callable=AsyncMock
        ) as mock_db:
            mock_db.return_value.get_lead_response_data = AsyncMock(
                return_value={
                    "responses": [],
                    "negative_sentiment": False,
                    "last_response_time": None,
                    "total_responses": 0,
                    "avg_sentiment": 0,
                }
            )

            response_data = await engine._get_response_data(lead_id)

            assert isinstance(response_data, dict)

    @pytest.mark.asyncio
    async def test_get_lead_profile(self, engine, sample_lead_data):
        """Test retrieval of comprehensive lead profile."""
        lead_id = "lead_789"

        with patch(
            "ghl_real_estate_ai.services.autonomous_followup_engine.get_database", new_callable=AsyncMock
        ) as mock_db:
            mock_db.return_value.get_lead_profile_data = AsyncMock(return_value=sample_lead_data)

            profile = await engine._get_lead_profile(lead_id)

            assert profile == sample_lead_data

    @pytest.mark.asyncio
    async def test_generate_contextual_followup(self, engine):
        """Test generation of contextual follow-up content."""
        lead_id = "lead_789"

        # Create mock behavioral_score with required attributes
        mock_behavioral_score = MagicMock()
        mock_behavioral_score.intent_level = IntentLevel.HOT
        mock_behavioral_score.likelihood_score = 75.0
        mock_behavioral_score.key_signals = []
        mock_behavioral_score.market_context = {}
        mock_behavioral_score.recommended_message = "Default follow-up message"

        activity_data = {"property_searches": []}

        # Mock llm_client.generate to return a response with content
        engine.llm_client.generate = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Hi! I noticed your interest in properties"
        engine.llm_client.generate.return_value = mock_response

        message = await engine._generate_contextual_followup(lead_id, mock_behavioral_score, activity_data)

        # Should return a string message
        assert isinstance(message, str)
        assert len(message) > 0

    @pytest.mark.asyncio
    async def test_get_lead_activity(self, engine):
        """Test retrieval of lead activity data."""
        lead_id = "lead_123"

        with patch(
            "ghl_real_estate_ai.services.autonomous_followup_engine.get_database", new_callable=AsyncMock
        ) as mock_db:
            mock_activity = {
                "property_searches": [],
                "email_interactions": [],
                "website_visits": [],
            }
            mock_db.return_value.get_lead_activity_data = AsyncMock(return_value=mock_activity)

            activity = await engine._get_lead_activity(lead_id)

            assert isinstance(activity, dict)

    @pytest.mark.asyncio
    async def test_calculate_send_time(self, engine):
        """Test calculation of optimal send time."""
        optimal_window = (9, 17)  # 9 AM to 5 PM

        send_time = await engine._calculate_send_time(optimal_window)

        assert isinstance(send_time, datetime)
        assert send_time > datetime.now() - timedelta(minutes=1)  # Should be now or future

    def test_calculate_priority(self, engine):
        """Test calculation of task priority."""
        # Test with different intent levels
        priority_urgent = engine._calculate_priority(IntentLevel.URGENT)
        priority_hot = engine._calculate_priority(IntentLevel.HOT)
        priority_warm = engine._calculate_priority(IntentLevel.WARM)
        priority_cold = engine._calculate_priority(IntentLevel.COLD)

        assert isinstance(priority_urgent, int)
        assert isinstance(priority_hot, int)
        assert priority_urgent > priority_hot
        assert priority_hot > priority_warm
        assert priority_warm > priority_cold

    @pytest.mark.asyncio
    async def test_send_email(self, engine):
        """Test email sending functionality."""
        with patch("ghl_real_estate_ai.services.ghl_client.GHLClient") as mock_ghl:
            mock_client = mock_ghl.return_value
            mock_client.send_message = AsyncMock(return_value=True)

            result = await engine._send_email("contact_123", "Test message")

            assert result is True

    @pytest.mark.asyncio
    async def test_send_sms(self, engine):
        """Test SMS sending functionality."""
        with patch("ghl_real_estate_ai.services.ghl_client.GHLClient") as mock_ghl:
            mock_client = mock_ghl.return_value
            mock_client.send_message = AsyncMock(return_value=True)

            result = await engine._send_sms("contact_123", "Test SMS")

            assert result is True

    @pytest.mark.asyncio
    async def test_initiate_call(self, engine):
        """Test phone call initiation functionality."""
        with (
            patch("ghl_real_estate_ai.services.vapi_service.VapiService") as mock_vapi,
            patch.object(engine, "_get_lead_profile", new_callable=AsyncMock) as mock_profile,
            patch.object(engine, "_get_lead_activity", new_callable=AsyncMock) as mock_activity,
            patch("ghl_real_estate_ai.services.negotiation_drift_detector.get_drift_detector") as mock_detector,
        ):
            mock_profile.return_value = {
                "phone": "+1234567890",
                "name": "Test Lead",
                "demographics": {"city": "Rancho Cucamonga"},
            }
            mock_activity.return_value = {"sms_responses": []}
            mock_detector.return_value.analyze_drift.return_value = {"drift_score": 0.5, "recommendation": "maintain"}
            mock_vapi_instance = mock_vapi.return_value
            mock_vapi_instance.trigger_outbound_call.return_value = True

            result = await engine._initiate_call("contact_123")

            assert result is True

    def test_get_task_stats(self, engine):
        """Test retrieval of task statistics."""
        # Add some sample tasks with proper metadata
        mock_task1 = MagicMock()
        mock_task1.status = MagicMock()
        mock_task1.status.value = "pending"
        mock_task1.metadata = {}

        mock_task2 = MagicMock()
        mock_task2.status = MagicMock()
        mock_task2.status.value = "sent"
        mock_task2.metadata = {"agent_consensus_score": 0.85}

        engine.pending_tasks = [mock_task1, mock_task2]

        stats = engine.get_task_stats()

        assert isinstance(stats, dict)
        assert "total_tasks" in stats
        assert "status_breakdown" in stats
        assert "is_running" in stats
        assert "agent_consensus_threshold" in stats

        # Basic validation
        assert stats["total_tasks"] == 2

    def test_get_agent_insights(self, engine):
        """Test retrieval of agent insights and performance."""
        insights = engine.get_agent_insights()

        assert isinstance(insights, dict)
        assert "total_agents" in insights
        assert "agents" in insights
        assert "overall_effectiveness" in insights

        # Verify agent data exists
        assert len(insights["agents"]) > 0


class TestFollowUpTask:
    """Test suite for FollowUpTask dataclass."""

    def test_follow_up_task_creation(self):
        """Test creating follow-up tasks."""
        task = FollowUpTask(
            task_id="test_task",
            lead_id="test_lead",
            contact_id="contact_test",
            channel=FollowUpChannel.EMAIL,
            message="Test follow-up message",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=1,
            status=FollowUpStatus.PENDING,
            metadata={},
            created_at=datetime.now(),
        )

        assert task.task_id == "test_task"
        assert task.lead_id == "test_lead"
        assert task.channel == FollowUpChannel.EMAIL
        assert task.message == "Test follow-up message"
        assert task.priority == 1
        assert task.status == FollowUpStatus.PENDING


class TestFollowUpAgent:
    """Test suite for FollowUpAgent base class."""

    def test_follow_up_agent_initialization(self):
        """Test agent initialization."""
        mock_llm = MagicMock()
        agent = FollowUpAgent(AgentType.TIMING_OPTIMIZER, mock_llm)

        assert agent.agent_type == AgentType.TIMING_OPTIMIZER
        assert agent.llm_client is mock_llm

    @pytest.mark.asyncio
    async def test_agent_analyze_method(self):
        """Test base agent analyze method."""
        mock_llm = MagicMock()
        agent = FollowUpAgent(AgentType.TIMING_OPTIMIZER, mock_llm)

        lead_id = "test_lead"
        context = {"lead_id": "test_lead"}

        # Base agent should raise NotImplementedError (to be implemented by subclasses)
        with pytest.raises(NotImplementedError):
            await agent.analyze(lead_id, context)


class TestSpecializedAgents:
    """Test suite for specialized follow-up agents."""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM client for agent testing."""
        return MagicMock()

    @pytest.fixture
    def sample_agent_data(self):
        """Sample data for agent testing."""
        return {
            "lead_data": {"lead_id": "test_lead", "last_contact": datetime.now() - timedelta(hours=24)},
            "follow_up_history": [],
            "response_data": {"avg_response_time_hours": 6},
            "lead_profile": {"name": "Test Lead", "preferences": {"email": True}},
        }

    def test_timing_optimizer_agent(self, sample_agent_data, mock_llm):
        """Test timing optimizer agent."""
        agent = TimingOptimizerAgent(mock_llm)

        assert agent.agent_type == AgentType.TIMING_OPTIMIZER

    def test_content_personalizer_agent(self, sample_agent_data, mock_llm):
        """Test content personalizer agent."""
        agent = ContentPersonalizerAgent(mock_llm)

        assert agent.agent_type == AgentType.CONTENT_PERSONALIZER

    def test_channel_strategist_agent(self, sample_agent_data, mock_llm):
        """Test channel strategist agent."""
        agent = ChannelStrategistAgent(mock_llm)

        assert agent.agent_type == AgentType.CHANNEL_STRATEGIST

    def test_sentiment_analyst_agent(self, sample_agent_data, mock_llm):
        """Test sentiment analyst agent."""
        agent = SentimentAnalystAgent(mock_llm)

        assert agent.agent_type == AgentType.SENTIMENT_ANALYST

    def test_response_analyzer_agent(self, sample_agent_data, mock_llm):
        """Test response analyzer agent."""
        agent = ResponseAnalyzerAgent(mock_llm)

        assert agent.agent_type == AgentType.RESPONSE_ANALYZER

    def test_escalation_manager_agent(self, sample_agent_data, mock_llm):
        """Test escalation manager agent."""
        agent = EscalationManagerAgent(mock_llm)

        assert agent.agent_type == AgentType.ESCALATION_MANAGER

    def test_objection_handler_agent(self, sample_agent_data, mock_llm):
        """Test objection handler agent."""
        agent = ObjectionHandlerAgent(mock_llm)

        assert agent.agent_type == AgentType.OBJECTION_HANDLER

    def test_conversion_optimizer_agent(self, sample_agent_data, mock_llm):
        """Test conversion optimizer agent."""
        agent = ConversionOptimizerAgent(mock_llm)

        assert agent.agent_type == AgentType.CONVERSION_OPTIMIZER

    def test_market_context_agent(self, sample_agent_data, mock_llm):
        """Test market context agent."""
        agent = MarketContextAgent(mock_llm)

        assert agent.agent_type == AgentType.MARKET_CONTEXT_AGENT

    def test_performance_tracker_agent(self, sample_agent_data, mock_llm):
        """Test performance tracker agent."""
        agent = PerformanceTrackerAgent(mock_llm)

        assert agent.agent_type == AgentType.PERFORMANCE_TRACKER


# Integration tests for complete autonomous follow-up workflows
class TestAutonomousFollowUpIntegration:
    """Integration tests for autonomous follow-up engine workflows."""

    @pytest.mark.asyncio
    async def test_complete_autonomous_followup_workflow(self):
        """Test complete autonomous follow-up workflow from lead activity to task execution."""
        with (
            patch(
                "ghl_real_estate_ai.services.autonomous_followup_engine.get_behavioral_trigger_engine"
            ) as mock_behavioral,
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_cache_service") as mock_cache,
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_llm_client") as mock_llm,
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_lead_intelligence_swarm") as mock_swarm,
        ):
            # Setup mocks
            mock_behavioral_engine = Mock()
            mock_behavioral.return_value = mock_behavioral_engine
            mock_behavioral_engine.get_high_intent_leads = AsyncMock(return_value=["lead_integration"])

            mock_cache_service = Mock()
            mock_cache.return_value = mock_cache_service
            mock_cache_service.get = AsyncMock(return_value=None)
            mock_cache_service.set = AsyncMock()

            mock_llm_client = Mock()
            mock_llm.return_value = mock_llm_client

            mock_swarm_service = Mock()
            mock_swarm.return_value = mock_swarm_service

            # Create engine and run workflow
            engine = AutonomousFollowUpEngine()

            # Simulate monitoring and response
            await engine.monitor_and_respond()

            # Should have attempted to process leads
            assert mock_behavioral_engine.get_high_intent_leads.called

    @pytest.mark.asyncio
    async def test_multi_channel_follow_up_strategy(self):
        """Test multi-channel follow-up strategy optimization."""
        with (
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_behavioral_trigger_engine"),
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_cache_service"),
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_llm_client"),
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_lead_intelligence_swarm"),
        ):
            engine = AutonomousFollowUpEngine()

            # Verify engine can handle multi-channel configuration
            assert hasattr(engine, "channel_strategist")
            assert hasattr(engine, "timing_optimizer")
            assert hasattr(engine, "content_personalizer")

    @pytest.mark.asyncio
    async def test_performance_monitoring_and_optimization(self):
        """Test performance monitoring and optimization features."""
        with (
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_behavioral_trigger_engine"),
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_cache_service"),
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_llm_client"),
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_lead_intelligence_swarm"),
        ):
            engine = AutonomousFollowUpEngine()

            # Update performance metrics using the actual API
            recommendations = [
                FollowUpRecommendation(
                    agent_type=AgentType.TIMING_OPTIMIZER,
                    confidence=0.85,
                    recommended_action="Schedule follow-up",
                    reasoning="Optimal timing detected",
                ),
            ]
            await engine._update_agent_performance(recommendations)

            # Get performance insights
            stats = engine.get_task_stats()
            insights = engine.get_agent_insights()

            # Verify metrics are tracked
            assert isinstance(stats, dict)
            assert isinstance(insights, dict)

    @pytest.mark.asyncio
    async def test_error_handling_and_resilience(self):
        """Test error handling and system resilience."""
        with (
            patch(
                "ghl_real_estate_ai.services.autonomous_followup_engine.get_behavioral_trigger_engine"
            ) as mock_behavioral,
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_cache_service"),
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_llm_client"),
            patch("ghl_real_estate_ai.services.autonomous_followup_engine.get_lead_intelligence_swarm"),
        ):
            # Setup behavioral engine to fail
            mock_behavioral_engine = Mock()
            mock_behavioral.return_value = mock_behavioral_engine
            mock_behavioral_engine.get_high_intent_leads = AsyncMock(side_effect=Exception("Service unavailable"))

            engine = AutonomousFollowUpEngine()

            # Should handle errors gracefully without crashing
            try:
                await engine.monitor_and_respond()
                # Should not raise exception
            except Exception as e:
                pytest.fail(f"Engine should handle errors gracefully, but raised: {e}")

            # Engine should continue to function
            assert engine.is_running is False  # Default state