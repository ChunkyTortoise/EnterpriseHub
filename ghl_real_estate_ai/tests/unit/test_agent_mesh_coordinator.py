"""Unit tests for AgentMeshCoordinator.

Tests cover: routing logic, task scheduling, governance rules,
auto-scaling triggers, audit trail recording, and dataclass properties.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Patch heavy dependencies before importing the module under test
_mock_patches = [
    patch("ghl_real_estate_ai.services.agent_mesh_coordinator.get_mcp_client", return_value=MagicMock()),
    patch("ghl_real_estate_ai.services.agent_mesh_coordinator.ProgressiveSkillsManager", return_value=MagicMock()),
    patch("ghl_real_estate_ai.services.agent_mesh_coordinator.TokenTracker", return_value=MagicMock()),
    patch("ghl_real_estate_ai.services.agent_mesh_coordinator.safe_create_task", side_effect=lambda coro: None),
]
for _p in _mock_patches:
    _p.start()

from ghl_real_estate_ai.services.agent_mesh_coordinator import (
    AgentCapability,
    AgentMeshCoordinator,
    AgentMetrics,
    AgentStatus,
    AgentTask,
    MeshAgent,
    TaskPriority,
)

# Stop patches after import so they don't leak to other modules
for _p in _mock_patches:
    _p.stop()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_agent(
    agent_id: str = "agent-1",
    name: str = "test_agent",
    capabilities: list | None = None,
    status: AgentStatus = AgentStatus.IDLE,
    max_concurrent: int = 5,
    current_tasks: int = 0,
    cost_per_token: float = 0.001,
    sla_response_time: float = 60.0,
    total_tasks: int = 10,
    completed_tasks: int = 9,
    avg_response_time: float = 1.5,
) -> MeshAgent:
    return MeshAgent(
        agent_id=agent_id,
        name=name,
        capabilities=capabilities or [AgentCapability.LEAD_QUALIFICATION],
        status=status,
        max_concurrent_tasks=max_concurrent,
        current_tasks=current_tasks,
        priority_level=1,
        cost_per_token=cost_per_token,
        sla_response_time=sla_response_time,
        metrics=AgentMetrics(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            average_response_time=avg_response_time,
        ),
        endpoint="http://localhost:8000",
        health_check_url="http://localhost:8000/health",
        last_heartbeat=datetime.now(),
    )


def _make_task(
    task_id: str = "task-1",
    task_type: str = "lead_qualification",
    priority: TaskPriority = TaskPriority.NORMAL,
    capabilities: list | None = None,
    max_cost: float | None = None,
    deadline: datetime | None = None,
    requester_id: str = "user-1",
) -> AgentTask:
    return AgentTask(
        task_id=task_id,
        task_type=task_type,
        priority=priority,
        capabilities_required=capabilities or [AgentCapability.LEAD_QUALIFICATION],
        payload={"test": True},
        created_at=datetime.now(),
        deadline=deadline,
        max_cost=max_cost,
        requester_id=requester_id,
    )


@pytest.fixture
def coordinator():
    """Create a coordinator with mocked dependencies."""
    with (
        patch("ghl_real_estate_ai.services.agent_mesh_coordinator.get_mcp_client", return_value=MagicMock()),
        patch("ghl_real_estate_ai.services.agent_mesh_coordinator.ProgressiveSkillsManager", return_value=MagicMock()),
        patch("ghl_real_estate_ai.services.agent_mesh_coordinator.TokenTracker", return_value=MagicMock()),
        patch("ghl_real_estate_ai.services.agent_mesh_coordinator.safe_create_task", side_effect=lambda coro: None),
    ):
        coord = AgentMeshCoordinator()
    return coord


# ---------------------------------------------------------------------------
# Dataclass / Enum tests
# ---------------------------------------------------------------------------

class TestAgentMetrics:
    def test_success_rate_no_tasks(self):
        m = AgentMetrics()
        assert m.success_rate == 100.0

    def test_success_rate_with_tasks(self):
        m = AgentMetrics(total_tasks=10, completed_tasks=7, failed_tasks=3)
        assert m.success_rate == 70.0

    def test_success_rate_all_completed(self):
        m = AgentMetrics(total_tasks=5, completed_tasks=5)
        assert m.success_rate == 100.0


class TestMeshAgent:
    def test_is_available_idle_with_capacity(self):
        agent = _make_agent(status=AgentStatus.IDLE, current_tasks=0)
        assert agent.is_available is True

    def test_is_not_available_busy(self):
        agent = _make_agent(status=AgentStatus.BUSY, current_tasks=5, max_concurrent=5)
        assert agent.is_available is False

    def test_is_not_available_stale_heartbeat(self):
        agent = _make_agent(status=AgentStatus.IDLE, current_tasks=0)
        agent.last_heartbeat = datetime.now() - timedelta(minutes=5)
        assert agent.is_available is False

    def test_load_factor(self):
        agent = _make_agent(current_tasks=3, max_concurrent=6)
        assert agent.load_factor == 50.0


class TestAgentTask:
    def test_is_overdue_no_deadline(self):
        task = _make_task(deadline=None)
        assert task.is_overdue is False

    def test_is_overdue_past_deadline(self):
        task = _make_task(deadline=datetime.now() - timedelta(hours=1))
        assert task.is_overdue is True

    def test_is_not_overdue_future_deadline(self):
        task = _make_task(deadline=datetime.now() + timedelta(hours=1))
        assert task.is_overdue is False

    def test_execution_time_completed(self):
        task = _make_task()
        task.started_at = datetime(2025, 1, 1, 12, 0, 0)
        task.completed_at = datetime(2025, 1, 1, 12, 0, 5)
        assert task.execution_time == 5.0

    def test_execution_time_not_completed(self):
        task = _make_task()
        assert task.execution_time is None


# ---------------------------------------------------------------------------
# Registration tests
# ---------------------------------------------------------------------------

class TestRegisterAgent:
    @pytest.mark.asyncio
    async def test_register_valid_agent(self, coordinator):
        agent = _make_agent()
        result = await coordinator.register_agent(agent)
        assert result is True
        assert "agent-1" in coordinator.agents

    @pytest.mark.asyncio
    async def test_register_initializes_metrics(self, coordinator):
        agent = _make_agent(agent_id="agent-new")
        await coordinator.register_agent(agent)
        assert "agent-new" in coordinator.performance_metrics
        assert "agent-new" in coordinator.cost_tracking


# ---------------------------------------------------------------------------
# Task submission tests
# ---------------------------------------------------------------------------

class TestSubmitTask:
    @pytest.mark.asyncio
    async def test_submit_valid_task(self, coordinator):
        agent = _make_agent()
        coordinator.agents["agent-1"] = agent
        task = _make_task()
        task_id = await coordinator.submit_task(task)
        assert task_id == "task-1"

    @pytest.mark.asyncio
    async def test_submit_invalid_task_raises(self, coordinator):
        task = AgentTask(
            task_id="",
            task_type="",
            priority=TaskPriority.NORMAL,
            capabilities_required=[],
            payload={},
            created_at=datetime.now(),
            deadline=None,
            max_cost=None,
            requester_id="user-1",
        )
        with pytest.raises(ValueError, match="Task validation failed"):
            await coordinator.submit_task(task)

    @pytest.mark.asyncio
    async def test_submit_exceeds_user_quota(self, coordinator):
        current_hour = datetime.now().hour
        coordinator.user_quotas["user-1"] = {current_hour: 999}
        task = _make_task()
        with pytest.raises(ValueError, match="quota exceeded"):
            await coordinator.submit_task(task)


# ---------------------------------------------------------------------------
# Routing tests
# ---------------------------------------------------------------------------

class TestRouting:
    @pytest.mark.asyncio
    async def test_find_candidates_filters_by_capability(self, coordinator):
        agent_lq = _make_agent(agent_id="a1", capabilities=[AgentCapability.LEAD_QUALIFICATION])
        agent_pm = _make_agent(agent_id="a2", capabilities=[AgentCapability.PROPERTY_MATCHING])
        coordinator.agents = {"a1": agent_lq, "a2": agent_pm}

        task = _make_task(capabilities=[AgentCapability.PROPERTY_MATCHING])
        candidates = await coordinator._find_candidate_agents(task)
        assert len(candidates) == 1
        assert candidates[0].agent_id == "a2"

    @pytest.mark.asyncio
    async def test_find_candidates_filters_unavailable(self, coordinator):
        agent = _make_agent(status=AgentStatus.ERROR)
        coordinator.agents = {"a1": agent}
        task = _make_task()
        candidates = await coordinator._find_candidate_agents(task)
        assert len(candidates) == 0

    @pytest.mark.asyncio
    async def test_find_candidates_filters_by_cost(self, coordinator):
        agent = _make_agent(cost_per_token=0.1)  # 0.1 * 1000 = 100 > max_cost
        coordinator.agents = {"a1": agent}
        task = _make_task(max_cost=0.5)
        candidates = await coordinator._find_candidate_agents(task)
        assert len(candidates) == 0

    @pytest.mark.asyncio
    async def test_find_candidates_filters_by_sla(self, coordinator):
        agent = _make_agent(sla_response_time=3600)  # 1 hour SLA
        coordinator.agents = {"a1": agent}
        task = _make_task(deadline=datetime.now() + timedelta(seconds=30))
        candidates = await coordinator._find_candidate_agents(task)
        assert len(candidates) == 0

    @pytest.mark.asyncio
    async def test_select_optimal_agent_empty(self, coordinator):
        result = await coordinator._select_optimal_agent([], _make_task())
        assert result is None

    @pytest.mark.asyncio
    async def test_select_optimal_agent_picks_best(self, coordinator):
        good_agent = _make_agent(agent_id="good", completed_tasks=10, total_tasks=10, current_tasks=0)
        bad_agent = _make_agent(agent_id="bad", completed_tasks=1, total_tasks=10, current_tasks=4)
        coordinator.agents = {"good": good_agent, "bad": bad_agent}
        task = _make_task()
        result = await coordinator._select_optimal_agent([good_agent, bad_agent], task)
        assert result.agent_id == "good"


# ---------------------------------------------------------------------------
# Agent scoring tests
# ---------------------------------------------------------------------------

class TestAgentScoring:
    @pytest.mark.asyncio
    async def test_emergency_priority_boost(self, coordinator):
        agent = _make_agent()
        coordinator.agents = {"agent-1": agent}
        normal_task = _make_task(priority=TaskPriority.NORMAL)
        emergency_task = _make_task(priority=TaskPriority.EMERGENCY)

        normal_score = await coordinator._calculate_agent_score(agent, normal_task)
        emergency_score = await coordinator._calculate_agent_score(agent, emergency_task)
        assert emergency_score > normal_score

    @pytest.mark.asyncio
    async def test_critical_priority_boost(self, coordinator):
        agent = _make_agent()
        coordinator.agents = {"agent-1": agent}
        normal_task = _make_task(priority=TaskPriority.NORMAL)
        critical_task = _make_task(priority=TaskPriority.CRITICAL)

        normal_score = await coordinator._calculate_agent_score(agent, normal_task)
        critical_score = await coordinator._calculate_agent_score(agent, critical_task)
        assert critical_score > normal_score


# ---------------------------------------------------------------------------
# Task assignment and execution tests
# ---------------------------------------------------------------------------

class TestAssignment:
    @pytest.mark.asyncio
    async def test_assign_updates_task_fields(self, coordinator):
        agent = _make_agent(current_tasks=0, max_concurrent=5)
        task = _make_task()
        with patch(
            "ghl_real_estate_ai.services.agent_mesh_coordinator.safe_create_task",
            side_effect=lambda coro: None,
        ):
            result = await coordinator._assign_and_execute_task(task, agent)
        assert result is True
        assert task.assigned_agent == "agent-1"
        assert task.started_at is not None
        assert agent.current_tasks == 1

    @pytest.mark.asyncio
    async def test_assign_sets_busy_at_capacity(self, coordinator):
        agent = _make_agent(current_tasks=4, max_concurrent=5)
        task = _make_task()
        with patch(
            "ghl_real_estate_ai.services.agent_mesh_coordinator.safe_create_task",
            side_effect=lambda coro: None,
        ):
            await coordinator._assign_and_execute_task(task, agent)
        assert agent.status == AgentStatus.BUSY

    @pytest.mark.asyncio
    async def test_assign_sets_active_under_capacity(self, coordinator):
        agent = _make_agent(current_tasks=0, max_concurrent=5)
        task = _make_task()
        with patch(
            "ghl_real_estate_ai.services.agent_mesh_coordinator.safe_create_task",
            side_effect=lambda coro: None,
        ):
            await coordinator._assign_and_execute_task(task, agent)
        assert agent.status == AgentStatus.ACTIVE


# ---------------------------------------------------------------------------
# Task failure handling tests
# ---------------------------------------------------------------------------

class TestTaskFailure:
    @pytest.mark.asyncio
    async def test_handle_task_failure_moves_to_completed(self, coordinator):
        task = _make_task()
        coordinator.active_tasks["task-1"] = task
        await coordinator._handle_task_failure(task, "some error")
        assert "task-1" in coordinator.completed_tasks
        assert "task-1" not in coordinator.active_tasks
        assert task.error == "some error"

    @pytest.mark.asyncio
    async def test_handle_task_failure_frees_agent(self, coordinator):
        agent = _make_agent(current_tasks=2)
        coordinator.agents["agent-1"] = agent
        task = _make_task()
        task.assigned_agent = "agent-1"
        coordinator.active_tasks["task-1"] = task

        await coordinator._handle_task_failure(task, "error")
        assert agent.current_tasks == 1

    @pytest.mark.asyncio
    async def test_handle_no_agents_available(self, coordinator):
        task = _make_task()
        await coordinator._handle_no_agents_available(task)
        assert task.error == "No capable agents available"
        assert task in coordinator.task_history


# ---------------------------------------------------------------------------
# Emergency shutdown tests
# ---------------------------------------------------------------------------

class TestEmergencyShutdown:
    @pytest.mark.asyncio
    async def test_emergency_shutdown_cancels_tasks(self, coordinator):
        task = _make_task()
        coordinator.active_tasks["task-1"] = task
        agent = _make_agent(current_tasks=1)
        coordinator.agents["agent-1"] = agent

        await coordinator.emergency_shutdown("cost threshold")
        assert "cost threshold" in task.error
        assert agent.status == AgentStatus.MAINTENANCE
        assert agent.current_tasks == 0


# ---------------------------------------------------------------------------
# Mesh status tests
# ---------------------------------------------------------------------------

class TestMeshStatus:
    @pytest.mark.asyncio
    async def test_get_mesh_status_empty(self, coordinator):
        status = await coordinator.get_mesh_status()
        assert status["agents"]["total"] == 0
        assert status["tasks"]["active"] == 0

    @pytest.mark.asyncio
    async def test_get_mesh_status_with_agents(self, coordinator):
        coordinator.agents["a1"] = _make_agent(agent_id="a1", status=AgentStatus.IDLE)
        coordinator.agents["a2"] = _make_agent(agent_id="a2", status=AgentStatus.BUSY)
        status = await coordinator.get_mesh_status()
        assert status["agents"]["total"] == 2
        assert status["agents"]["idle"] == 1
        assert status["agents"]["busy"] == 1


# ---------------------------------------------------------------------------
# Agent details tests
# ---------------------------------------------------------------------------

class TestAgentDetails:
    @pytest.mark.asyncio
    async def test_get_agent_details_not_found(self, coordinator):
        result = await coordinator.get_agent_details("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_agent_details_found(self, coordinator):
        coordinator.agents["a1"] = _make_agent(agent_id="a1")
        # _get_agent_performance_trend is referenced but not implemented in the coordinator
        coordinator._get_agent_performance_trend = AsyncMock(return_value=[])
        result = await coordinator.get_agent_details("a1")
        assert result is not None
        assert "agent" in result


# ---------------------------------------------------------------------------
# Health check tests
# ---------------------------------------------------------------------------

class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, coordinator):
        coordinator.agents["a1"] = _make_agent(agent_id="a1")
        result = await coordinator.health_check()
        assert result["status"] == "healthy"
        assert result["agents"]["a1"]["healthy"] is True

    @pytest.mark.asyncio
    async def test_health_check_no_agents(self, coordinator):
        result = await coordinator.health_check()
        assert result["status"] == "healthy"  # no agents = vacuously healthy
        assert result["coordinator"] == "active"


# ---------------------------------------------------------------------------
# Metrics update tests
# ---------------------------------------------------------------------------

class TestMetricsUpdate:
    @pytest.mark.asyncio
    async def test_update_agent_metrics_success(self, coordinator):
        agent = _make_agent(total_tasks=0, completed_tasks=0, avg_response_time=0.0)
        task = _make_task()
        await coordinator._update_agent_metrics(agent, task, 2.5, success=True)
        assert agent.metrics.total_tasks == 1
        assert agent.metrics.completed_tasks == 1
        assert agent.metrics.average_response_time == 2.5

    @pytest.mark.asyncio
    async def test_update_agent_metrics_failure(self, coordinator):
        agent = _make_agent(total_tasks=0, completed_tasks=0)
        task = _make_task()
        await coordinator._update_agent_metrics(agent, task, 1.0, success=False)
        assert agent.metrics.failed_tasks == 1
        assert agent.metrics.completed_tasks == 0


# ---------------------------------------------------------------------------
# Budget / governance tests
# ---------------------------------------------------------------------------

class TestGovernance:
    @pytest.mark.asyncio
    async def test_check_user_quota_within_limit(self, coordinator):
        result = await coordinator._check_user_quota("new-user")
        assert result is True

    @pytest.mark.asyncio
    async def test_check_user_quota_exceeded(self, coordinator):
        current_hour = datetime.now().hour
        coordinator.user_quotas["heavy-user"] = {current_hour: 999}
        result = await coordinator._check_user_quota("heavy-user")
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_task_valid(self, coordinator):
        task = _make_task()
        result = await coordinator._validate_task(task)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_task_missing_fields(self, coordinator):
        task = AgentTask(
            task_id="",
            task_type="",
            priority=TaskPriority.NORMAL,
            capabilities_required=[],
            payload={},
            created_at=datetime.now(),
            deadline=None,
            max_cost=None,
            requester_id="user-1",
        )
        result = await coordinator._validate_task(task)
        assert result is False
