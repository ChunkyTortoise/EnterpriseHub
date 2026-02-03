"""
Tests for Autonomous Follow-up Engine - AI-Powered Lead Nurturing System

Tests the autonomous follow-up engine that uses multi-agent intelligence to automatically
nurture leads, optimize communication timing, personalize content, and maximize conversions.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from dataclasses import asdict

from ghl_real_estate_ai.services.autonomous_followup_engine import (
    AutonomousFollowUpEngine,
    get_autonomous_followup_engine,
    FollowUpStatus,
    FollowUpChannel,
    FollowUpTask,
    AgentType,
    FollowUpRecommendation,
    FollowUpAgent,
    TimingOptimizerAgent,
    ContentPersonalizerAgent,
    ChannelStrategistAgent,
    ResponseAnalyzerAgent,
    EscalationManagerAgent,
    SentimentAnalystAgent,
    ObjectionHandlerAgent,
    ConversionOptimizerAgent,
    MarketContextAgent,
    PerformanceTrackerAgent
)


class TestAutonomousFollowUpEngine:
    """Test suite for AutonomousFollowUpEngine core functionality."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies for the engine."""
        with patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_behavioral_trigger_engine') as mock_behavioral, \
             patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_cache_service') as mock_cache, \
             patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_llm_client') as mock_llm, \
             patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_lead_intelligence_swarm') as mock_swarm:
            
            yield {
                'behavioral': mock_behavioral.return_value,
                'cache': mock_cache.return_value,
                'llm': mock_llm.return_value,
                'swarm': mock_swarm.return_value
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
            channel=FollowUpChannel.EMAIL,
            content="Personalized follow-up message about luxury properties",
            scheduled_time=datetime.now() + timedelta(hours=2),
            priority=0.8,
            status=FollowUpStatus.PENDING,
            created_at=datetime.now(),
            agent_consensus=0.85
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
                    "message": "Interested in properties around $600K in north Austin",
                    "type": "inbound",
                    "channel": "email",
                    "sentiment": "positive"
                },
                {
                    "timestamp": datetime.now() - timedelta(hours=49),
                    "message": "I have some great options to show you. When are you available?",
                    "type": "outbound", 
                    "channel": "email"
                }
            ],
            
            "behavioral_data": {
                "response_time_avg_hours": 6,
                "engagement_score": 0.72,
                "preferred_contact_times": ["9-11am", "2-4pm"],
                "channel_preferences": {
                    "email": 0.8,
                    "sms": 0.6,
                    "phone": 0.4
                },
                "last_website_visit": datetime.now() - timedelta(hours=18),
                "property_views_count": 8,
                "saved_properties": 3
            },
            
            "demographics": {
                "age_range": "28-35",
                "income_bracket": "medium_high",
                "family_status": "young_professional",
                "location": "North Austin, TX",
                "buy_timeline": "3-6_months"
            },
            
            "current_sentiment": "interested_but_cautious",
            "objections": ["price_concerns", "location_uncertainty"],
            "interests": ["modern_homes", "good_schools", "commute_friendly"]
        }

    @pytest.fixture
    def sample_agent_recommendations(self):
        """Sample recommendations from different agents."""
        return {
            AgentType.TIMING_OPTIMIZER: FollowUpRecommendation(
                agent_type=AgentType.TIMING_OPTIMIZER,
                recommendation_score=0.85,
                suggested_channel=FollowUpChannel.EMAIL,
                suggested_timing=datetime.now() + timedelta(hours=24),
                reasoning="Best historical response time for this lead profile",
                confidence=0.87
            ),
            AgentType.CONTENT_PERSONALIZER: FollowUpRecommendation(
                agent_type=AgentType.CONTENT_PERSONALIZER,
                recommendation_score=0.78,
                suggested_channel=FollowUpChannel.EMAIL,
                content_suggestions={
                    "tone": "professional_friendly",
                    "topics": ["school_districts", "commute_times", "value_appreciation"],
                    "urgency": "moderate"
                },
                reasoning="Lead shows interest in family-oriented features",
                confidence=0.82
            ),
            AgentType.SENTIMENT_ANALYST: FollowUpRecommendation(
                agent_type=AgentType.SENTIMENT_ANALYST,
                recommendation_score=0.73,
                sentiment_analysis={
                    "current_sentiment": "cautiously_optimistic",
                    "emotional_state": "researching_carefully",
                    "engagement_level": "moderate_high"
                },
                reasoning="Lead is engaged but needs reassurance",
                confidence=0.79
            )
        }

    def test_engine_initialization(self, engine):
        """Test that the autonomous follow-up engine initializes correctly."""
        assert isinstance(engine, AutonomousFollowUpEngine)
        assert hasattr(engine, 'behavioral_engine')
        assert hasattr(engine, 'cache')
        assert hasattr(engine, 'llm_client')
        assert hasattr(engine, 'lead_intelligence_swarm')
        
        # Verify all specialized agents are initialized
        assert hasattr(engine, 'timing_optimizer')
        assert hasattr(engine, 'content_personalizer')
        assert hasattr(engine, 'channel_strategist')
        assert hasattr(engine, 'response_analyzer')
        assert hasattr(engine, 'escalation_manager')
        assert hasattr(engine, 'sentiment_analyst')
        assert hasattr(engine, 'objection_handler')
        assert hasattr(engine, 'conversion_optimizer')
        assert hasattr(engine, 'market_context_agent')
        assert hasattr(engine, 'performance_tracker')
        
        # Verify task management components
        assert isinstance(engine.pending_tasks, list)
        assert hasattr(engine, 'task_lock')
        assert engine.is_running is False
        assert engine.monitor_task is None
        
        # Verify configuration parameters
        assert engine.monitoring_interval_seconds > 0
        assert engine.max_daily_followups_per_lead > 0
        assert engine.batch_size > 0
        assert 0 < engine.agent_consensus_threshold <= 1

    def test_get_autonomous_followup_engine_singleton(self):
        """Test that the global engine function returns a singleton."""
        with patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_behavioral_trigger_engine'), \
             patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_cache_service'), \
             patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_llm_client'), \
             patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_lead_intelligence_swarm'):
            
            engine1 = get_autonomous_followup_engine()
            engine2 = get_autonomous_followup_engine()
            assert engine1 is engine2
            assert isinstance(engine1, AutonomousFollowUpEngine)

    @pytest.mark.asyncio
    async def test_start_monitoring(self, engine):
        """Test starting the monitoring loop."""
        with patch.object(engine, '_monitoring_loop', new_callable=AsyncMock) as mock_loop:
            await engine.start_monitoring()
            
            assert engine.is_running is True
            assert engine.monitor_task is not None
            
            # Verify monitoring loop was started
            mock_loop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_monitoring(self, engine):
        """Test stopping the monitoring loop."""
        # Start monitoring first
        engine.is_running = True
        engine.monitor_task = Mock()
        engine.monitor_task.cancel = Mock()
        
        await engine.stop_monitoring()
        
        assert engine.is_running is False
        engine.monitor_task.cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_monitoring_loop(self, engine):
        """Test the core monitoring loop functionality."""
        engine.is_running = True
        
        with patch.object(engine, 'monitor_and_respond', new_callable=AsyncMock) as mock_monitor, \
             patch.object(engine, 'execute_pending_tasks', new_callable=AsyncMock) as mock_execute, \
             patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            
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
    async def test_monitor_and_respond(self, engine, sample_lead_data):
        """Test monitoring and responding to lead activities."""
        # Mock getting leads requiring follow-up
        mock_leads = [sample_lead_data]
        
        with patch.object(engine, '_get_lead_activity', new_callable=AsyncMock, return_value=mock_leads) as mock_activity, \
             patch.object(engine, '_process_lead', new_callable=AsyncMock) as mock_process:
            
            await engine.monitor_and_respond()
            
            # Verify lead activity was monitored
            mock_activity.assert_called_once()
            
            # Verify leads were processed
            assert mock_process.call_count == len(mock_leads)
            mock_process.assert_any_call(sample_lead_data)

    @pytest.mark.asyncio
    async def test_execute_pending_tasks(self, engine, sample_follow_up_task):
        """Test execution of pending follow-up tasks."""
        # Add task to pending queue
        engine.pending_tasks = [sample_follow_up_task]
        
        with patch.object(engine, '_execute_task', new_callable=AsyncMock) as mock_execute:
            await engine.execute_pending_tasks()
            
            # Verify task execution
            mock_execute.assert_called_once_with(sample_follow_up_task)

    @pytest.mark.asyncio
    async def test_process_lead(self, engine, sample_lead_data, sample_agent_recommendations):
        """Test comprehensive lead processing workflow."""
        with patch.object(engine, '_get_follow_up_history', new_callable=AsyncMock, return_value=[]) as mock_history, \
             patch.object(engine, '_get_response_data', new_callable=AsyncMock, return_value={}) as mock_response, \
             patch.object(engine, '_get_lead_profile', new_callable=AsyncMock, return_value=sample_lead_data) as mock_profile, \
             patch.object(engine, '_build_agent_consensus', new_callable=AsyncMock, return_value=sample_agent_recommendations) as mock_consensus, \
             patch.object(engine, '_generate_contextual_followup', new_callable=AsyncMock) as mock_generate:
            
            mock_task = FollowUpTask(
                task_id="generated_task",
                lead_id=sample_lead_data["lead_id"],
                channel=FollowUpChannel.EMAIL,
                content="Generated follow-up",
                scheduled_time=datetime.now() + timedelta(hours=1),
                priority=0.8,
                status=FollowUpStatus.PENDING,
                created_at=datetime.now()
            )
            mock_generate.return_value = mock_task
            
            await engine._process_lead(sample_lead_data)
            
            # Verify complete workflow
            mock_history.assert_called_once()
            mock_response.assert_called_once()
            mock_profile.assert_called_once()
            mock_consensus.assert_called_once()
            mock_generate.assert_called_once()
            
            # Verify task was added to pending queue
            assert len(engine.pending_tasks) == 1
            assert engine.pending_tasks[0] == mock_task

    @pytest.mark.asyncio
    async def test_execute_task_email(self, engine, sample_follow_up_task):
        """Test execution of email follow-up task."""
        sample_follow_up_task.channel = FollowUpChannel.EMAIL
        
        with patch.object(engine, '_send_email', new_callable=AsyncMock, return_value=True) as mock_send, \
             patch.object(engine, '_update_agent_performance', new_callable=AsyncMock) as mock_update:
            
            await engine._execute_task(sample_follow_up_task)
            
            # Verify email was sent
            mock_send.assert_called_once_with(sample_follow_up_task)
            
            # Verify task status was updated
            assert sample_follow_up_task.status == FollowUpStatus.COMPLETED
            
            # Verify agent performance tracking
            mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_task_sms(self, engine, sample_follow_up_task):
        """Test execution of SMS follow-up task."""
        sample_follow_up_task.channel = FollowUpChannel.SMS
        
        with patch.object(engine, '_send_sms', new_callable=AsyncMock, return_value=True) as mock_send, \
             patch.object(engine, '_update_agent_performance', new_callable=AsyncMock) as mock_update:
            
            await engine._execute_task(sample_follow_up_task)
            
            # Verify SMS was sent
            mock_send.assert_called_once_with(sample_follow_up_task)
            
            # Verify task status was updated  
            assert sample_follow_up_task.status == FollowUpStatus.COMPLETED
            
            # Verify agent performance tracking
            mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_task_phone(self, engine, sample_follow_up_task):
        """Test execution of phone follow-up task."""
        sample_follow_up_task.channel = FollowUpChannel.PHONE
        
        with patch.object(engine, '_initiate_call', new_callable=AsyncMock, return_value=True) as mock_call, \
             patch.object(engine, '_update_agent_performance', new_callable=AsyncMock) as mock_update:
            
            await engine._execute_task(sample_follow_up_task)
            
            # Verify call was initiated
            mock_call.assert_called_once_with(sample_follow_up_task)
            
            # Verify task status was updated
            assert sample_follow_up_task.status == FollowUpStatus.COMPLETED
            
            # Verify agent performance tracking
            mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_task_failure_handling(self, engine, sample_follow_up_task):
        """Test handling of task execution failures."""
        sample_follow_up_task.channel = FollowUpChannel.EMAIL
        
        with patch.object(engine, '_send_email', new_callable=AsyncMock, return_value=False) as mock_send, \
             patch.object(engine, '_handle_escalation', new_callable=AsyncMock) as mock_escalate:
            
            await engine._execute_task(sample_follow_up_task)
            
            # Verify email send was attempted
            mock_send.assert_called_once_with(sample_follow_up_task)
            
            # Verify task status was updated to failed
            assert sample_follow_up_task.status == FollowUpStatus.FAILED
            
            # Verify escalation was triggered
            mock_escalate.assert_called_once_with(sample_follow_up_task)

    @pytest.mark.asyncio
    async def test_build_agent_consensus(self, engine, sample_lead_data):
        """Test building consensus among specialized agents."""
        # Mock agent recommendations
        mock_recommendations = {
            AgentType.TIMING_OPTIMIZER: Mock(recommendation_score=0.85),
            AgentType.CONTENT_PERSONALIZER: Mock(recommendation_score=0.78),
            AgentType.CHANNEL_STRATEGIST: Mock(recommendation_score=0.82),
            AgentType.SENTIMENT_ANALYST: Mock(recommendation_score=0.79)
        }
        
        with patch.object(engine.timing_optimizer, 'analyze', new_callable=AsyncMock, return_value=mock_recommendations[AgentType.TIMING_OPTIMIZER]), \
             patch.object(engine.content_personalizer, 'analyze', new_callable=AsyncMock, return_value=mock_recommendations[AgentType.CONTENT_PERSONALIZER]), \
             patch.object(engine.channel_strategist, 'analyze', new_callable=AsyncMock, return_value=mock_recommendations[AgentType.CHANNEL_STRATEGIST]), \
             patch.object(engine.sentiment_analyst, 'analyze', new_callable=AsyncMock, return_value=mock_recommendations[AgentType.SENTIMENT_ANALYST]):
            
            consensus = await engine._build_agent_consensus(
                sample_lead_data, [], {}, sample_lead_data
            )
            
            # Verify all agents were consulted
            assert len(consensus) == 4
            assert all(agent_type in consensus for agent_type in mock_recommendations.keys())

    @pytest.mark.asyncio
    async def test_handle_escalation(self, engine, sample_follow_up_task):
        """Test escalation handling for failed tasks."""
        with patch.object(engine.escalation_manager, 'handle_escalation', new_callable=AsyncMock) as mock_handle:
            await engine._handle_escalation(sample_follow_up_task)
            
            # Verify escalation manager was called
            mock_handle.assert_called_once_with(sample_follow_up_task)

    @pytest.mark.asyncio
    async def test_update_agent_performance(self, engine, sample_follow_up_task):
        """Test updating agent performance metrics."""
        success = True
        
        with patch.object(engine.performance_tracker, 'update_performance', new_callable=AsyncMock) as mock_update:
            await engine._update_agent_performance(sample_follow_up_task, success)
            
            # Verify performance tracker was called
            mock_update.assert_called_once_with(sample_follow_up_task, success)

    @pytest.mark.asyncio
    async def test_get_follow_up_history(self, engine):
        """Test retrieval of follow-up history."""
        lead_id = "lead_123"
        
        with patch.object(engine.cache, 'get', new_callable=AsyncMock, return_value=None):
            history = await engine._get_follow_up_history(lead_id)
            
            # Should return empty list when no history
            assert isinstance(history, list)

    @pytest.mark.asyncio
    async def test_get_response_data(self, engine):
        """Test retrieval of response data."""
        lead_id = "lead_123"
        
        with patch.object(engine.behavioral_engine, 'analyze_lead_behavior', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {
                "response_patterns": {"avg_response_time_hours": 8},
                "engagement_metrics": {"email_open_rate": 0.75}
            }
            
            response_data = await engine._get_response_data(lead_id)
            
            assert isinstance(response_data, dict)
            mock_analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_lead_profile(self, engine, sample_lead_data):
        """Test retrieval of comprehensive lead profile."""
        lead_id = sample_lead_data["lead_id"]
        
        with patch.object(engine.lead_intelligence_swarm, 'get_lead_profile', new_callable=AsyncMock, return_value=sample_lead_data):
            profile = await engine._get_lead_profile(lead_id)
            
            assert profile == sample_lead_data

    @pytest.mark.asyncio
    async def test_generate_contextual_followup(self, engine, sample_lead_data, sample_agent_recommendations):
        """Test generation of contextual follow-up content."""
        follow_up_history = []
        response_data = {"avg_response_time_hours": 6}
        
        with patch.object(engine, '_calculate_send_time', return_value=datetime.now() + timedelta(hours=6)) as mock_time, \
             patch.object(engine, '_calculate_priority', return_value=0.8) as mock_priority:
            
            task = await engine._generate_contextual_followup(
                sample_lead_data, sample_agent_recommendations, follow_up_history, response_data
            )
            
            assert isinstance(task, FollowUpTask)
            assert task.lead_id == sample_lead_data["lead_id"]
            assert task.status == FollowUpStatus.PENDING
            assert isinstance(task.content, str)
            assert len(task.content) > 0
            
            # Verify timing and priority calculation
            mock_time.assert_called_once()
            mock_priority.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_lead_activity(self, engine):
        """Test retrieval of leads requiring follow-up."""
        with patch.object(engine.behavioral_engine, 'get_high_intent_leads', new_callable=AsyncMock) as mock_get_leads:
            mock_leads = [{"lead_id": "lead_1"}, {"lead_id": "lead_2"}]
            mock_get_leads.return_value = mock_leads
            
            leads = await engine._get_lead_activity()
            
            assert leads == mock_leads
            mock_get_leads.assert_called_once()

    def test_calculate_send_time(self, engine, sample_agent_recommendations):
        """Test calculation of optimal send time."""
        timing_rec = sample_agent_recommendations[AgentType.TIMING_OPTIMIZER]
        
        send_time = engine._calculate_send_time(sample_agent_recommendations, {})
        
        assert isinstance(send_time, datetime)
        assert send_time > datetime.now()  # Should be in the future

    def test_calculate_priority(self, engine):
        """Test calculation of task priority."""
        agent_consensus = {
            AgentType.TIMING_OPTIMIZER: Mock(recommendation_score=0.8),
            AgentType.CONTENT_PERSONALIZER: Mock(recommendation_score=0.7),
            AgentType.SENTIMENT_ANALYST: Mock(recommendation_score=0.9)
        }
        
        priority = engine._calculate_priority(agent_consensus)
        
        assert isinstance(priority, float)
        assert 0 <= priority <= 1

    @pytest.mark.asyncio
    async def test_send_email(self, engine, sample_follow_up_task):
        """Test email sending functionality."""
        # Mock email sending service
        with patch.object(engine.llm_client, 'send_email', new_callable=AsyncMock, return_value=True) as mock_send:
            result = await engine._send_email(sample_follow_up_task)
            
            assert result is True
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_sms(self, engine, sample_follow_up_task):
        """Test SMS sending functionality."""
        # Mock SMS sending service
        with patch.object(engine.llm_client, 'send_sms', new_callable=AsyncMock, return_value=True) as mock_send:
            result = await engine._send_sms(sample_follow_up_task)
            
            assert result is True
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_initiate_call(self, engine, sample_follow_up_task):
        """Test phone call initiation functionality."""
        # Mock call initiation service
        with patch.object(engine.llm_client, 'initiate_call', new_callable=AsyncMock, return_value=True) as mock_call:
            result = await engine._initiate_call(sample_follow_up_task)
            
            assert result is True
            mock_call.assert_called_once()

    def test_get_task_stats(self, engine):
        """Test retrieval of task statistics."""
        # Add some sample tasks
        engine.pending_tasks = [
            Mock(status=FollowUpStatus.PENDING),
            Mock(status=FollowUpStatus.COMPLETED),
            Mock(status=FollowUpStatus.FAILED)
        ]
        
        stats = engine.get_task_stats()
        
        assert isinstance(stats, dict)
        assert "total_tasks" in stats
        assert "pending_tasks" in stats
        assert "completed_tasks" in stats
        assert "failed_tasks" in stats
        
        # Basic validation
        assert stats["total_tasks"] >= 0
        assert stats["pending_tasks"] >= 0
        assert stats["completed_tasks"] >= 0
        assert stats["failed_tasks"] >= 0

    def test_get_agent_insights(self, engine):
        """Test retrieval of agent insights and performance."""
        # Mock some agent performance data
        engine.agent_performance = {
            AgentType.TIMING_OPTIMIZER: {
                "total_recommendations": 100,
                "successful_outcomes": 85,
                "avg_confidence": 0.82
            },
            AgentType.CONTENT_PERSONALIZER: {
                "total_recommendations": 95,
                "successful_outcomes": 78,
                "avg_confidence": 0.75
            }
        }
        
        insights = engine.get_agent_insights()
        
        assert isinstance(insights, dict)
        
        # Verify insights for each agent type
        for agent_type in [AgentType.TIMING_OPTIMIZER, AgentType.CONTENT_PERSONALIZER]:
            assert agent_type in insights
            agent_insight = insights[agent_type]
            assert "performance_score" in agent_insight
            assert "recommendation_count" in agent_insight
            assert "success_rate" in agent_insight


class TestFollowUpTask:
    """Test suite for FollowUpTask dataclass."""

    def test_follow_up_task_creation(self):
        """Test creating follow-up tasks."""
        task = FollowUpTask(
            task_id="test_task",
            lead_id="test_lead",
            channel=FollowUpChannel.EMAIL,
            content="Test follow-up message",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=0.8,
            status=FollowUpStatus.PENDING,
            created_at=datetime.now()
        )
        
        assert task.task_id == "test_task"
        assert task.lead_id == "test_lead"
        assert task.channel == FollowUpChannel.EMAIL
        assert task.content == "Test follow-up message"
        assert task.priority == 0.8
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
            "lead_profile": {"name": "Test Lead", "preferences": {"email": True}}
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
        assert hasattr(agent, 'performance_metrics')


# Integration tests for complete autonomous follow-up workflows
class TestAutonomousFollowUpIntegration:
    """Integration tests for autonomous follow-up engine workflows."""

    @pytest.mark.asyncio
    async def test_complete_autonomous_followup_workflow(self):
        """Test complete autonomous follow-up workflow from lead activity to task execution."""
        with patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_behavioral_trigger_engine') as mock_behavioral, \
             patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_cache_service') as mock_cache, \
             patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_llm_client') as mock_llm, \
             patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_lead_intelligence_swarm') as mock_swarm:
            
            # Setup mocks
            mock_behavioral_engine = Mock()
            mock_behavioral.return_value = mock_behavioral_engine
            mock_behavioral_engine.get_high_intent_leads = AsyncMock(return_value=[
                {
                    "lead_id": "integration_lead",
                    "name": "Integration Test Lead", 
                    "last_contact": datetime.now() - timedelta(hours=48),
                    "behavioral_data": {"engagement_score": 0.8}
                }
            ])
            mock_behavioral_engine.analyze_lead_behavior = AsyncMock(return_value={
                "response_patterns": {"avg_response_time_hours": 6},
                "engagement_metrics": {"email_open_rate": 0.75}
            })
            
            mock_cache_service = Mock()
            mock_cache.return_value = mock_cache_service
            mock_cache_service.get = AsyncMock(return_value=None)
            mock_cache_service.set = AsyncMock()
            
            mock_llm_client = Mock() 
            mock_llm.return_value = mock_llm_client
            mock_llm_client.send_email = AsyncMock(return_value=True)
            
            mock_swarm_service = Mock()
            mock_swarm.return_value = mock_swarm_service
            mock_swarm_service.get_lead_profile = AsyncMock(return_value={
                "lead_id": "integration_lead",
                "preferences": {"email": True}
            })
            
            # Create engine and run workflow
            engine = AutonomousFollowUpEngine()
            
            # Simulate monitoring and response
            await engine.monitor_and_respond()
            
            # Should have processed leads and created tasks
            assert mock_behavioral_engine.get_high_intent_leads.called
            
            # Execute any pending tasks
            if engine.pending_tasks:
                await engine.execute_pending_tasks()

    @pytest.mark.asyncio
    async def test_multi_channel_follow_up_strategy(self):
        """Test multi-channel follow-up strategy optimization."""
        with patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_behavioral_trigger_engine'), \
             patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_cache_service'), \
             patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_llm_client'), \
             patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_lead_intelligence_swarm'):
            
            engine = AutonomousFollowUpEngine()
            
            # Create lead data with multi-channel preferences
            lead_data = {
                "lead_id": "multi_channel_lead",
                "behavioral_data": {
                    "channel_preferences": {
                        "email": 0.8,
                        "sms": 0.6, 
                        "phone": 0.4
                    },
                    "response_rates": {
                        "email": 0.65,
                        "sms": 0.45,
                        "phone": 0.75
                    }
                }
            }
            
            # Mock agent recommendations for different channels
            with patch.object(engine, '_build_agent_consensus', new_callable=AsyncMock) as mock_consensus:
                mock_consensus.return_value = {
                    AgentType.CHANNEL_STRATEGIST: Mock(
                        suggested_channel=FollowUpChannel.EMAIL,
                        recommendation_score=0.85
                    ),
                    AgentType.TIMING_OPTIMIZER: Mock(
                        suggested_timing=datetime.now() + timedelta(hours=2),
                        recommendation_score=0.78
                    )
                }
                
                # Process the lead
                await engine._process_lead(lead_data)
                
                # Verify agent consensus was built
                mock_consensus.assert_called_once()

    @pytest.mark.asyncio
    async def test_performance_monitoring_and_optimization(self):
        """Test performance monitoring and optimization features."""
        with patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_behavioral_trigger_engine'), \
             patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_cache_service'), \
             patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_llm_client'), \
             patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_lead_intelligence_swarm'):
            
            engine = AutonomousFollowUpEngine()
            
            # Simulate task executions with varying success rates
            successful_task = FollowUpTask(
                task_id="success_task",
                lead_id="test_lead", 
                channel=FollowUpChannel.EMAIL,
                content="Successful follow-up",
                scheduled_time=datetime.now(),
                priority=0.8,
                status=FollowUpStatus.COMPLETED,
                created_at=datetime.now()
            )
            
            failed_task = FollowUpTask(
                task_id="failed_task",
                lead_id="test_lead",
                channel=FollowUpChannel.SMS,
                content="Failed follow-up",
                scheduled_time=datetime.now(),
                priority=0.6,
                status=FollowUpStatus.FAILED,
                created_at=datetime.now()
            )
            
            # Update performance metrics
            await engine._update_agent_performance(successful_task, True)
            await engine._update_agent_performance(failed_task, False)
            
            # Get performance insights
            stats = engine.get_task_stats()
            insights = engine.get_agent_insights()
            
            # Verify metrics are tracked
            assert isinstance(stats, dict)
            assert isinstance(insights, dict)

    @pytest.mark.asyncio 
    async def test_error_handling_and_resilience(self):
        """Test error handling and system resilience."""
        with patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_behavioral_trigger_engine') as mock_behavioral, \
             patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_cache_service'), \
             patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_llm_client'), \
             patch('ghl_real_estate_ai.services.autonomous_followup_engine.get_lead_intelligence_swarm'):
            
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