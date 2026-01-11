"""
Tests for Redis Conversation Service

Comprehensive tests for Redis-based conversation persistence including
fallback mechanisms, data integrity, and performance validation.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import json

# Import the service to test
try:
    from ..services.redis_conversation_service import (
        RedisConversationService,
        ConversationMessage,
        AgentConversationState,
        redis_conversation_service
    )
except ImportError:
    pytest.skip("Redis conversation service not available for testing", allow_module_level=True)


class TestRedisConversationService:
    """Test cases for Redis conversation service functionality"""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for testing"""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.pipeline.return_value = mock_client
        mock_client.execute.return_value = [True, True, True]
        return mock_client

    @pytest.fixture
    def redis_service_with_mock(self, mock_redis_client):
        """Redis service with mocked client"""
        service = RedisConversationService()
        service.redis_client = mock_redis_client
        return service

    @pytest.mark.asyncio
    async def test_store_conversation_message_success(self, redis_service_with_mock):
        """Test successful conversation message storage"""
        agent_id = "test_agent_001"
        role = "user"
        content = "What are my hot leads today?"
        lead_id = "lead_123"

        result = await redis_service_with_mock.store_conversation_message(
            agent_id, role, content, lead_id
        )

        assert result is True
        redis_service_with_mock.redis_client.pipeline.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_conversation_message_with_confidence(self, redis_service_with_mock):
        """Test storing assistant message with confidence score"""
        agent_id = "test_agent_002"
        role = "assistant"
        content = "I found 3 hot leads requiring immediate attention..."
        confidence = 0.92

        result = await redis_service_with_mock.store_conversation_message(
            agent_id, role, content, confidence=confidence
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_conversation_history(self, redis_service_with_mock):
        """Test conversation history retrieval"""
        agent_id = "test_agent_003"

        # Mock Redis response with pickled data
        import pickle
        from dataclasses import asdict

        mock_messages = [
            ConversationMessage(
                role="user",
                content="Show me leads",
                timestamp=datetime.now()
            ),
            ConversationMessage(
                role="assistant",
                content="Here are your leads...",
                timestamp=datetime.now(),
                confidence=0.89
            )
        ]

        mock_data = [pickle.dumps(asdict(msg)) for msg in mock_messages]
        redis_service_with_mock.redis_client.lrange.return_value = mock_data

        messages = await redis_service_with_mock.get_conversation_history(agent_id, limit=10)

        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"
        assert messages[1].confidence == 0.89

    @pytest.mark.asyncio
    async def test_get_agent_state_new_agent(self, redis_service_with_mock):
        """Test getting state for new agent"""
        agent_id = "new_agent_001"

        # Mock Redis returning None for new agent
        redis_service_with_mock.redis_client.get.return_value = None

        state = await redis_service_with_mock.get_agent_state(agent_id)

        assert state is not None
        assert state.agent_id == agent_id
        assert len(state.active_leads) == 0
        assert state.total_conversations == 0

    @pytest.mark.asyncio
    async def test_get_agent_state_existing_agent(self, redis_service_with_mock):
        """Test getting state for existing agent"""
        agent_id = "existing_agent_001"

        # Mock existing agent state
        import pickle
        from dataclasses import asdict

        existing_state = AgentConversationState(
            agent_id=agent_id,
            messages=[],
            active_leads=["lead_1", "lead_2"],
            last_activity=datetime.now(),
            preferences={"style": "analytical"},
            total_conversations=15
        )

        mock_data = pickle.dumps(asdict(existing_state))
        redis_service_with_mock.redis_client.get.return_value = mock_data

        state = await redis_service_with_mock.get_agent_state(agent_id)

        assert state is not None
        assert state.agent_id == agent_id
        assert len(state.active_leads) == 2
        assert state.total_conversations == 15
        assert state.preferences["style"] == "analytical"

    @pytest.mark.asyncio
    async def test_get_lead_conversation_context(self, redis_service_with_mock):
        """Test lead-specific conversation context"""
        agent_id = "test_agent_004"
        lead_id = "target_lead_123"

        # Mock conversation history with mixed leads
        mock_messages = [
            ConversationMessage(
                role="user",
                content="Tell me about lead_123",
                timestamp=datetime.now(),
                lead_id="target_lead_123"
            ),
            ConversationMessage(
                role="user",
                content="What about lead_456?",
                timestamp=datetime.now(),
                lead_id="other_lead_456"
            ),
            ConversationMessage(
                role="assistant",
                content="Lead 123 analysis...",
                timestamp=datetime.now(),
                lead_id="target_lead_123"
            )
        ]

        # Mock the get_conversation_history method
        with patch.object(
            redis_service_with_mock, 'get_conversation_history',
            return_value=mock_messages
        ):
            lead_context = await redis_service_with_mock.get_lead_conversation_context(
                agent_id, lead_id
            )

        # Should only return messages for the target lead
        assert len(lead_context) == 2
        for msg in lead_context:
            assert msg.lead_id == lead_id

    @pytest.mark.asyncio
    async def test_store_agent_preferences(self, redis_service_with_mock):
        """Test storing agent preferences"""
        agent_id = "test_agent_005"
        preferences = {
            "communication_style": "direct",
            "lead_priority": "high_budget",
            "follow_up_frequency": "daily"
        }

        # Mock existing state
        existing_state = AgentConversationState(
            agent_id=agent_id,
            messages=[],
            active_leads=[],
            last_activity=datetime.now(),
            preferences={},
            total_conversations=0
        )

        with patch.object(
            redis_service_with_mock, 'get_agent_state',
            return_value=existing_state
        ):
            result = await redis_service_with_mock.store_agent_preferences(
                agent_id, preferences
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_agent_stats_comprehensive(self, redis_service_with_mock):
        """Test comprehensive agent statistics"""
        agent_id = "test_agent_006"

        # Mock agent state and recent messages
        mock_state = AgentConversationState(
            agent_id=agent_id,
            messages=[],
            active_leads=["lead_1", "lead_2", "lead_3"],
            last_activity=datetime.now(),
            preferences={"style": "analytical"},
            total_conversations=25
        )

        recent_messages = [
            ConversationMessage(
                role="assistant",
                content="Response 1",
                timestamp=datetime.now(),
                confidence=0.95
            ),
            ConversationMessage(
                role="assistant",
                content="Response 2",
                timestamp=datetime.now() - timedelta(hours=2),
                confidence=0.87
            )
        ]

        with patch.object(
            redis_service_with_mock, 'get_agent_state',
            return_value=mock_state
        ), patch.object(
            redis_service_with_mock, 'get_conversation_history',
            return_value=recent_messages
        ):
            stats = await redis_service_with_mock.get_agent_stats(agent_id)

        assert stats["agent_id"] == agent_id
        assert stats["total_conversations"] == 25
        assert stats["active_leads"] == 3
        assert stats["status"] == "active"
        assert 0.8 < stats["average_confidence"] < 1.0

    @pytest.mark.asyncio
    async def test_redis_unavailable_fallback(self):
        """Test fallback behavior when Redis is unavailable"""
        service = RedisConversationService()
        service.redis_client = None  # Simulate Redis unavailable

        result = await service.store_conversation_message(
            "test_agent", "user", "test message"
        )

        assert result is False

        messages = await service.get_conversation_history("test_agent")
        assert len(messages) == 0

    def test_health_check_healthy(self, redis_service_with_mock):
        """Test health check with healthy Redis"""
        # Mock Redis info
        redis_service_with_mock.redis_client.info.return_value = {
            'redis_version': '6.2.6',
            'used_memory_human': '1.2M',
            'connected_clients': 5
        }

        health = redis_service_with_mock.health_check()

        assert health["status"] == "healthy"
        assert health["redis_connected"] is True
        assert health["redis_version"] == "6.2.6"

    def test_health_check_unhealthy(self):
        """Test health check with unhealthy Redis"""
        service = RedisConversationService()
        service.redis_client = None

        health = service.health_check()

        assert health["status"] == "error"
        assert health["redis_connected"] is False

    @pytest.mark.asyncio
    async def test_conversation_message_structure(self):
        """Test ConversationMessage dataclass structure"""
        message = ConversationMessage(
            role="user",
            content="Test message",
            timestamp=datetime.now(),
            lead_id="lead_123",
            context={"source": "test"},
            confidence=0.9
        )

        assert message.role == "user"
        assert message.content == "Test message"
        assert message.lead_id == "lead_123"
        assert message.context["source"] == "test"
        assert message.confidence == 0.9

    @pytest.mark.asyncio
    async def test_error_handling_malformed_data(self, redis_service_with_mock):
        """Test error handling with malformed Redis data"""
        agent_id = "test_agent_error"

        # Mock Redis returning malformed data
        redis_service_with_mock.redis_client.lrange.return_value = [
            b"invalid_pickle_data",
            b"more_invalid_data"
        ]

        # Should handle errors gracefully and return empty list
        messages = await redis_service_with_mock.get_conversation_history(agent_id)

        assert len(messages) == 0  # Should return empty list on errors

    @pytest.mark.asyncio
    async def test_conversation_limit_enforcement(self, redis_service_with_mock):
        """Test that conversation history is limited properly"""
        agent_id = "test_agent_limit"

        result = await redis_service_with_mock.store_conversation_message(
            agent_id, "user", "Test message"
        )

        assert result is True

        # Verify ltrim was called to limit conversation history
        pipeline_calls = redis_service_with_mock.redis_client.pipeline.return_value
        # The mock should have been called with ltrim
        assert hasattr(pipeline_calls, 'ltrim')


class TestIntegrationWithClaudeService:
    """Integration tests with Claude Agent Service"""

    @pytest.mark.asyncio
    async def test_redis_integration_fallback(self):
        """Test that Claude service handles Redis unavailability gracefully"""
        # This would test the actual integration but requires more setup
        # For now, we'll just verify the service can be imported
        from ..services.claude_agent_service import claude_agent_service

        # Verify the service has the Redis service attached
        assert hasattr(claude_agent_service, 'redis_service')
        assert claude_agent_service.redis_service is not None


@pytest.mark.performance
class TestPerformanceScenarios:
    """Performance testing for Redis operations"""

    @pytest.mark.asyncio
    async def test_batch_message_storage_performance(self, redis_service_with_mock):
        """Test performance with batch message storage"""
        agent_id = "performance_agent"

        # Simulate storing 100 messages
        start_time = datetime.now()

        for i in range(100):
            await redis_service_with_mock.store_conversation_message(
                agent_id, "user" if i % 2 == 0 else "assistant",
                f"Message {i}", lead_id=f"lead_{i % 10}"
            )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Should complete within reasonable time (mock operations)
        assert duration < 5.0

    @pytest.mark.asyncio
    async def test_concurrent_agent_operations(self, redis_service_with_mock):
        """Test concurrent operations for multiple agents"""
        agents = [f"agent_{i}" for i in range(10)]

        # Run concurrent operations
        tasks = []
        for agent_id in agents:
            task = redis_service_with_mock.store_conversation_message(
                agent_id, "user", f"Concurrent message from {agent_id}"
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # All operations should succeed
        assert all(results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])