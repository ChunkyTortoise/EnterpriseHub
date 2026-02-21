"""
Integration tests for ROADMAP-021 through ROADMAP-025:
Agent lifecycle management — status updates, handoff coordination,
pause, resume, and graceful restart.
"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from ghl_real_estate_ai.api.routes.agent_ecosystem import (
    VALID_AGENT_STATUSES,
    _execute_handoff_with_coordination,
    _get_agent_state,
    _pause_agent_lifecycle,
    _restart_agent_lifecycle,
    _resume_agent_lifecycle,
    _set_agent_state,
    _update_agent_status_in_registry,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_cache():
    """Mock CacheService with dict-backed storage."""
    storage = {}

    cache = AsyncMock()

    async def mock_get(key):
        return storage.get(key)

    async def mock_set(key, value, ttl=300):
        storage[key] = value
        return True

    async def mock_delete(key):
        storage.pop(key, None)
        return True

    cache.get = AsyncMock(side_effect=mock_get)
    cache.set = AsyncMock(side_effect=mock_set)
    cache.delete = AsyncMock(side_effect=mock_delete)
    cache._storage = storage
    return cache


# ============================================================================
# ROADMAP-021: Agent Status Update Tests
# ============================================================================


class TestAgentStatusUpdate:
    """Tests for ROADMAP-021: Agent registry status management."""

    @pytest.mark.asyncio
    async def test_get_agent_state_empty(self, mock_cache):
        """Test getting state for non-existent agent returns None."""
        result = await _get_agent_state("agent-nonexistent", mock_cache)
        assert result is None

    @pytest.mark.asyncio
    async def test_set_and_get_agent_state(self, mock_cache):
        """Test persisting and retrieving agent state."""
        state = {"agent_id": "agent-1", "status": "active", "version": "1.0"}
        await _set_agent_state("agent-1", state, mock_cache)

        result = await _get_agent_state("agent-1", mock_cache)
        assert result is not None
        assert result["agent_id"] == "agent-1"
        assert result["status"] == "active"

    @pytest.mark.asyncio
    async def test_update_status_new_agent(self, mock_cache):
        """Test updating status for agent with no prior state creates entry."""
        result = await _update_agent_status_in_registry("agent-new", "active", mock_cache)
        assert result["old_status"] == "active"
        assert result["new_status"] == "active"
        assert result["agent_id"] == "agent-new"

        state = await _get_agent_state("agent-new", mock_cache)
        assert state["status"] == "active"
        assert "registered_at" in state

    @pytest.mark.asyncio
    async def test_update_status_tracks_transition(self, mock_cache):
        """Test status transition is tracked with old_status."""
        await _update_agent_status_in_registry("agent-1", "active", mock_cache)
        result = await _update_agent_status_in_registry("agent-1", "standby", mock_cache)

        assert result["old_status"] == "active"
        assert result["new_status"] == "standby"

        state = await _get_agent_state("agent-1", mock_cache)
        assert state["status"] == "standby"
        assert state["previous_status"] == "active"
        assert "status_changed_at" in state

    @pytest.mark.asyncio
    async def test_update_status_invalid_raises(self, mock_cache):
        """Test invalid status raises ValueError."""
        with pytest.raises(ValueError, match="Invalid status"):
            await _update_agent_status_in_registry("agent-1", "bogus", mock_cache)

    @pytest.mark.asyncio
    async def test_valid_agent_statuses_complete(self):
        """Test all expected statuses are in the valid set."""
        expected = {"active", "standby", "processing", "offline", "paused", "restarting"}
        assert VALID_AGENT_STATUSES == expected


# ============================================================================
# ROADMAP-022: Handoff Coordination Engine Tests
# ============================================================================


class TestHandoffCoordination:
    """Tests for ROADMAP-022: Handoff coordination with context preservation."""

    @pytest.mark.asyncio
    async def test_successful_handoff(self, mock_cache):
        """Test handoff between two active agents succeeds."""
        result = await _execute_handoff_with_coordination(
            from_agent="seller-bot",
            to_agent="buyer-bot",
            handoff_type="intent_switch",
            context_data={"lead_id": "lead-123", "reason": "buyer intent detected"},
            cache=mock_cache,
        )
        assert result["status"] == "completed"
        assert result["from_agent"] == "seller-bot"
        assert result["to_agent"] == "buyer-bot"
        assert "coordination_id" in result
        assert "completed_at" in result
        assert "duration_seconds" in result

    @pytest.mark.asyncio
    async def test_handoff_to_offline_agent_fails(self, mock_cache):
        """Test handoff fails when target agent is offline."""
        await _set_agent_state("buyer-bot", {"agent_id": "buyer-bot", "status": "offline"}, mock_cache)

        result = await _execute_handoff_with_coordination(
            from_agent="seller-bot",
            to_agent="buyer-bot",
            handoff_type="intent_switch",
            context_data={"lead_id": "lead-456"},
            cache=mock_cache,
        )
        assert result["status"] == "failed"
        assert "offline" in result["failure_reason"]

    @pytest.mark.asyncio
    async def test_handoff_to_paused_agent_fails(self, mock_cache):
        """Test handoff fails when target agent is paused."""
        await _set_agent_state("lead-bot", {"agent_id": "lead-bot", "status": "paused"}, mock_cache)

        result = await _execute_handoff_with_coordination(
            from_agent="seller-bot",
            to_agent="lead-bot",
            handoff_type="escalation",
            context_data={},
            cache=mock_cache,
        )
        assert result["status"] == "failed"
        assert "paused" in result["failure_reason"]

    @pytest.mark.asyncio
    async def test_handoff_to_restarting_agent_fails(self, mock_cache):
        """Test handoff fails when target agent is restarting."""
        await _set_agent_state("buyer-bot", {"agent_id": "buyer-bot", "status": "restarting"}, mock_cache)

        result = await _execute_handoff_with_coordination(
            from_agent="seller-bot",
            to_agent="buyer-bot",
            handoff_type="intent_switch",
            context_data={},
            cache=mock_cache,
        )
        assert result["status"] == "failed"
        assert "restarting" in result["failure_reason"]

    @pytest.mark.asyncio
    async def test_handoff_preserves_context(self, mock_cache):
        """Test handoff stores context for retrieval."""
        context = {"lead_id": "lead-789", "conversation_history": ["msg1", "msg2"]}

        result = await _execute_handoff_with_coordination(
            from_agent="lead-bot",
            to_agent="seller-bot",
            handoff_type="qualification",
            context_data=context,
            cache=mock_cache,
        )
        coordination_id = result["coordination_id"]

        # Verify handoff state is persisted in cache
        stored = await mock_cache.get(f"handoff:{coordination_id}")
        assert stored is not None
        assert stored["context_data"]["lead_id"] == "lead-789"
        assert stored["status"] == "completed"


# ============================================================================
# ROADMAP-023: Pause Agent Lifecycle Tests
# ============================================================================


class TestPauseAgent:
    """Tests for ROADMAP-023: Agent pause lifecycle."""

    @pytest.mark.asyncio
    async def test_pause_active_agent(self, mock_cache):
        """Test pausing an active agent succeeds."""
        await _update_agent_status_in_registry("agent-1", "active", mock_cache)

        result = await _pause_agent_lifecycle("agent-1", mock_cache)
        assert result["success"] is True
        assert result["action"] == "paused"
        assert result["previous_status"] == "active"

        state = await _get_agent_state("agent-1", mock_cache)
        assert state["status"] == "paused"
        assert "paused_at" in state

    @pytest.mark.asyncio
    async def test_pause_already_paused_agent_fails(self, mock_cache):
        """Test pausing an already paused agent returns failure."""
        await _update_agent_status_in_registry("agent-1", "paused", mock_cache)

        result = await _pause_agent_lifecycle("agent-1", mock_cache)
        assert result["success"] is False
        assert "already paused" in result["reason"]

    @pytest.mark.asyncio
    async def test_pause_offline_agent_fails(self, mock_cache):
        """Test pausing an offline agent returns failure."""
        await _update_agent_status_in_registry("agent-1", "offline", mock_cache)

        result = await _pause_agent_lifecycle("agent-1", mock_cache)
        assert result["success"] is False
        assert "offline" in result["reason"]

    @pytest.mark.asyncio
    async def test_pause_processing_agent(self, mock_cache):
        """Test pausing a processing agent succeeds (drains in-flight)."""
        await _update_agent_status_in_registry("agent-1", "processing", mock_cache)

        result = await _pause_agent_lifecycle("agent-1", mock_cache)
        assert result["success"] is True
        assert result["previous_status"] == "processing"


# ============================================================================
# ROADMAP-024: Resume Agent Lifecycle Tests
# ============================================================================


class TestResumeAgent:
    """Tests for ROADMAP-024: Agent resume lifecycle."""

    @pytest.mark.asyncio
    async def test_resume_paused_agent(self, mock_cache):
        """Test resuming a paused agent succeeds."""
        await _update_agent_status_in_registry("agent-1", "paused", mock_cache)

        result = await _resume_agent_lifecycle("agent-1", mock_cache)
        assert result["success"] is True
        assert result["action"] == "resumed"
        assert result["previous_status"] == "paused"

        state = await _get_agent_state("agent-1", mock_cache)
        assert state["status"] == "active"
        assert "resumed_at" in state
        assert "paused_at" not in state

    @pytest.mark.asyncio
    async def test_resume_active_agent_fails(self, mock_cache):
        """Test resuming an active agent returns failure."""
        await _update_agent_status_in_registry("agent-1", "active", mock_cache)

        result = await _resume_agent_lifecycle("agent-1", mock_cache)
        assert result["success"] is False
        assert "PAUSED state" in result["reason"]

    @pytest.mark.asyncio
    async def test_resume_offline_agent_fails(self, mock_cache):
        """Test resuming an offline agent returns failure."""
        await _update_agent_status_in_registry("agent-1", "offline", mock_cache)

        result = await _resume_agent_lifecycle("agent-1", mock_cache)
        assert result["success"] is False
        assert "PAUSED state" in result["reason"]

    @pytest.mark.asyncio
    async def test_pause_then_resume_round_trip(self, mock_cache):
        """Test full pause -> resume lifecycle."""
        await _update_agent_status_in_registry("agent-1", "active", mock_cache)

        pause_result = await _pause_agent_lifecycle("agent-1", mock_cache)
        assert pause_result["success"] is True

        resume_result = await _resume_agent_lifecycle("agent-1", mock_cache)
        assert resume_result["success"] is True

        state = await _get_agent_state("agent-1", mock_cache)
        assert state["status"] == "active"


# ============================================================================
# ROADMAP-025: Graceful Restart Tests
# ============================================================================


class TestGracefulRestart:
    """Tests for ROADMAP-025: Agent graceful restart lifecycle."""

    @pytest.mark.asyncio
    async def test_restart_active_agent(self, mock_cache):
        """Test restart of an active agent completes all phases."""
        await _update_agent_status_in_registry("agent-1", "active", mock_cache)

        result = await _restart_agent_lifecycle("agent-1", mock_cache)
        assert result["success"] is True
        assert result["final_status"] == "active"
        assert result["previous_status"] == "active"
        assert len(result["phases"]) == 4

        phase_names = [p["phase"] for p in result["phases"]]
        assert phase_names == ["drain", "stop", "start", "health_check"]

        # Verify all phases completed
        for phase in result["phases"]:
            assert phase["status"] in ("completed", "passed")

    @pytest.mark.asyncio
    async def test_restart_tracks_timestamps(self, mock_cache):
        """Test restart records start and completion timestamps."""
        result = await _restart_agent_lifecycle("agent-1", mock_cache)
        assert "restart_started_at" in result
        assert "restart_completed_at" in result

    @pytest.mark.asyncio
    async def test_restart_log_persisted_in_cache(self, mock_cache):
        """Test restart log is stored in cache for auditing."""
        result = await _restart_agent_lifecycle("agent-1", mock_cache)

        stored_log = await mock_cache.get("agent_restart_log:agent-1")
        assert stored_log is not None
        assert stored_log["agent_id"] == "agent-1"
        assert stored_log["success"] is True

    @pytest.mark.asyncio
    async def test_restart_from_standby(self, mock_cache):
        """Test restart from standby status."""
        await _update_agent_status_in_registry("agent-1", "standby", mock_cache)

        result = await _restart_agent_lifecycle("agent-1", mock_cache)
        assert result["success"] is True
        assert result["previous_status"] == "standby"
        assert result["final_status"] == "active"

    @pytest.mark.asyncio
    async def test_restart_preserves_agent_state_post_restart(self, mock_cache):
        """Test agent state is active after successful restart."""
        await _update_agent_status_in_registry("agent-1", "processing", mock_cache)

        await _restart_agent_lifecycle("agent-1", mock_cache)

        state = await _get_agent_state("agent-1", mock_cache)
        assert state["status"] == "active"
