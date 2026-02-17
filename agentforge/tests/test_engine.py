"""Comprehensive tests for the ExecutionEngine implementation.

This module tests all aspects of the ExecutionEngine class including:
- Parallel execution of independent nodes
- Sequential execution with dependencies
- Retry logic with exponential backoff
- Timeout handling
- Fail-fast mode
- Concurrency limiting
- Error propagation
- Execution hooks
- Cancellation support
"""

import asyncio

import pytest
from pydantic import ValidationError

from agentforge.core.agent import AgentInput, AgentOutput, BaseAgent
from agentforge.core.dag import DAG
from agentforge.core.engine import (
    Engine,
    ExecutionConfig,
    ExecutionEngine,
    ExecutionResult,
)
from agentforge.core.exceptions import ExecutionError, NodeNotFoundError
from agentforge.core.types import AgentConfig, AgentStatus


class MockAgent(BaseAgent):
    """Mock agent for testing purposes with configurable behavior."""

    def __init__(
        self,
        config: AgentConfig = None,
        response: str = "mock response",
        delay: float = 0.0,
        fail_count: int = 0,
        fail_message: str = "Intentional failure",
    ) -> None:
        super().__init__(config=config)
        self.response = response
        self.delay = delay
        self.fail_count = fail_count
        self.fail_message = fail_message
        self.call_count = 0
        self.call_times: list[float] = []

    async def execute(self, input: AgentInput) -> AgentOutput:
        """Execute with configurable delay and failure behavior."""
        import time
        self.call_count += 1
        self.call_times.append(time.monotonic())

        if self.delay > 0:
            await asyncio.sleep(self.delay)

        if self.call_count <= self.fail_count:
            raise Exception(self.fail_message)

        return AgentOutput(
            content=self.response,
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            metadata={"cost": 0.001},
        )


class SlowAgent(BaseAgent):
    """Agent that takes a long time to execute."""

    def __init__(self, config: AgentConfig = None, delay: float = 1.0) -> None:
        super().__init__(config=config)
        self.delay = delay

    async def execute(self, input: AgentInput) -> AgentOutput:
        await asyncio.sleep(self.delay)
        return AgentOutput(content="slow response")


class FailingAgent(BaseAgent):
    """Agent that always fails."""

    def __init__(self, config: AgentConfig = None, message: str = "Always fails") -> None:
        super().__init__(config=config)
        self.message = message

    async def execute(self, input: AgentInput) -> AgentOutput:
        raise Exception(self.message)


@pytest.fixture
def empty_dag():
    """Create an empty DAG for testing."""
    return DAG()


@pytest.fixture
def single_node_dag():
    """Create a DAG with a single node."""
    dag = DAG()
    agent = MockAgent(config=AgentConfig(name="single_agent"))
    dag.add_node("single", agent)
    return dag


@pytest.fixture
def parallel_dag():
    """Create a DAG with three independent nodes (parallel execution)."""
    dag = DAG()

    agent_a = MockAgent(config=AgentConfig(name="agent_a"), response="A", delay=0.1)
    agent_b = MockAgent(config=AgentConfig(name="agent_b"), response="B", delay=0.1)
    agent_c = MockAgent(config=AgentConfig(name="agent_c"), response="C", delay=0.1)

    dag.add_node("a", agent_a)
    dag.add_node("b", agent_b)
    dag.add_node("c", agent_c)

    return dag


@pytest.fixture
def sequential_dag():
    """Create a DAG with three nodes in sequence (a -> b -> c)."""
    dag = DAG()

    agent_a = MockAgent(config=AgentConfig(name="agent_a"), response="A")
    agent_b = MockAgent(config=AgentConfig(name="agent_b"), response="B")
    agent_c = MockAgent(config=AgentConfig(name="agent_c"), response="C")

    dag.add_node("a", agent_a)
    dag.add_node("b", agent_b)
    dag.add_node("c", agent_c)

    dag.add_edge("a", "b")
    dag.add_edge("b", "c")

    return dag


@pytest.fixture
def diamond_dag():
    """Create a diamond-shaped DAG (a -> b, a -> c, b -> d, c -> d)."""
    dag = DAG()

    agent_a = MockAgent(config=AgentConfig(name="agent_a"), response="A", delay=0.1)
    agent_b = MockAgent(config=AgentConfig(name="agent_b"), response="B", delay=0.1)
    agent_c = MockAgent(config=AgentConfig(name="agent_c"), response="C", delay=0.1)
    agent_d = MockAgent(config=AgentConfig(name="agent_d"), response="D", delay=0.1)

    dag.add_node("a", agent_a)
    dag.add_node("b", agent_b)
    dag.add_node("c", agent_c)
    dag.add_node("d", agent_d)

    dag.add_edge("a", "b")
    dag.add_edge("a", "c")
    dag.add_edge("b", "d")
    dag.add_edge("c", "d")

    return dag


class TestExecutionConfig:
    """Tests for ExecutionConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ExecutionConfig()
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.timeout is None
        assert config.fail_fast is False
        assert config.max_concurrency is None

    def test_custom_config(self):
        """Test custom configuration values."""
        config = ExecutionConfig(
            max_retries=5,
            retry_delay=0.5,
            timeout=30.0,
            fail_fast=True,
            max_concurrency=10,
        )
        assert config.max_retries == 5
        assert config.retry_delay == 0.5
        assert config.timeout == 30.0
        assert config.fail_fast is True
        assert config.max_concurrency == 10

    def test_validation_constraints(self):
        """Test that validation constraints are enforced."""
        # Negative values should be invalid
        with pytest.raises(ValidationError):
            ExecutionConfig(max_retries=-1)

        with pytest.raises(ValidationError):
            ExecutionConfig(retry_delay=-1.0)

        with pytest.raises(ValidationError):
            ExecutionConfig(max_concurrency=0)


class TestExecutionResult:
    """Tests for ExecutionResult model."""

    def test_default_result(self):
        """Test default result values."""
        result = ExecutionResult()
        assert result.outputs == {}
        assert result.status == {}
        assert result.errors == {}
        assert result.execution_time == 0.0
        assert result.total_tokens == 0
        assert result.total_cost == 0.0

    def test_custom_result(self):
        """Test custom result values."""
        output = AgentOutput(content="test")
        result = ExecutionResult(
            outputs={"node_a": output},
            status={"node_a": AgentStatus.COMPLETED},
            errors={},
            execution_time=1.5,
            total_tokens=100,
            total_cost=0.05,
        )
        assert result.outputs["node_a"] == output
        assert result.status["node_a"] == AgentStatus.COMPLETED
        assert result.execution_time == 1.5
        assert result.total_tokens == 100
        assert result.total_cost == 0.05


class TestExecutionEngine:
    """Tests for ExecutionEngine class."""

    def test_default_initialization(self):
        """Test default engine initialization."""
        engine = ExecutionEngine()
        assert engine.config.max_retries == 3
        assert engine._pre_hooks == []
        assert engine._post_hooks == []

    def test_custom_config_initialization(self):
        """Test engine initialization with custom config."""
        config = ExecutionConfig(max_retries=5, timeout=60.0)
        engine = ExecutionEngine(config=config)
        assert engine.config.max_retries == 5
        assert engine.config.timeout == 60.0

    @pytest.mark.asyncio
    async def test_execute_empty_dag(self, empty_dag):
        """Test executing an empty DAG."""
        engine = ExecutionEngine()
        result = await engine.execute(empty_dag)

        assert result.outputs == {}
        assert result.status == {}
        assert result.errors == {}
        assert result.execution_time >= 0

    @pytest.mark.asyncio
    async def test_execute_single_node(self, single_node_dag):
        """Test executing a DAG with a single node."""
        engine = ExecutionEngine()
        result = await engine.execute(single_node_dag)

        assert "single" in result.outputs
        assert result.outputs["single"].content == "mock response"
        assert result.status["single"] == AgentStatus.COMPLETED
        assert "single" not in result.errors

    @pytest.mark.asyncio
    async def test_parallel_execution(self, parallel_dag):
        """Test that independent nodes execute in parallel."""
        engine = ExecutionEngine()

        import time
        start = time.monotonic()
        result = await engine.execute(parallel_dag)
        elapsed = time.monotonic() - start

        # All three nodes should complete
        assert len(result.outputs) == 3
        assert all(result.status[n] == AgentStatus.COMPLETED for n in ["a", "b", "c"])

        # Parallel execution should take ~0.1s, not ~0.3s
        assert elapsed < 0.5, f"Parallel execution took {elapsed}s, expected < 0.5s"

    @pytest.mark.asyncio
    async def test_sequential_execution(self, sequential_dag):
        """Test that dependent nodes execute in sequence."""
        engine = ExecutionEngine()
        result = await engine.execute(sequential_dag)

        # All nodes should complete
        assert len(result.outputs) == 3
        assert all(result.status[n] == AgentStatus.COMPLETED for n in ["a", "b", "c"])

        # Verify execution order via call times
        agent_a = sequential_dag.get_node("a")
        agent_b = sequential_dag.get_node("b")
        agent_c = sequential_dag.get_node("c")

        # a should be called before b, b before c
        assert agent_a.call_times[0] <= agent_b.call_times[0]
        assert agent_b.call_times[0] <= agent_c.call_times[0]

    @pytest.mark.asyncio
    async def test_diamond_dependency(self, diamond_dag):
        """Test diamond-shaped dependency graph."""
        engine = ExecutionEngine()

        import time
        start = time.monotonic()
        result = await engine.execute(diamond_dag)
        elapsed = time.monotonic() - start

        # All nodes should complete
        assert len(result.outputs) == 4
        assert all(result.status[n] == AgentStatus.COMPLETED for n in ["a", "b", "c", "d"])

        # a runs first (0.1s), then b and c in parallel (0.1s), then d (0.1s)
        # Total should be ~0.3s, not 0.4s
        assert elapsed < 0.6, f"Diamond execution took {elapsed}s, expected < 0.6s"

    @pytest.mark.asyncio
    async def test_retry_logic_success(self):
        """Test that retry logic works when agent eventually succeeds."""
        dag = DAG()
        # Agent fails twice then succeeds
        agent = MockAgent(
            config=AgentConfig(name="retry_agent"),
            fail_count=2,
            response="success after retries",
        )
        dag.add_node("retry", agent)

        config = ExecutionConfig(max_retries=3, retry_delay=0.1)
        engine = ExecutionEngine(config=config)
        result = await engine.execute(dag)

        assert result.status["retry"] == AgentStatus.COMPLETED
        assert result.outputs["retry"].content == "success after retries"
        assert agent.call_count == 3  # 2 failures + 1 success

    @pytest.mark.asyncio
    async def test_retry_logic_exhausted(self):
        """Test that execution fails after all retries are exhausted."""
        dag = DAG()
        # Agent always fails
        agent = MockAgent(
            config=AgentConfig(name="always_fail"),
            fail_count=100,  # More than max_retries
        )
        dag.add_node("fail", agent)

        config = ExecutionConfig(max_retries=2, retry_delay=0.1)
        engine = ExecutionEngine(config=config)
        result = await engine.execute(dag)

        assert result.status["fail"] == AgentStatus.FAILED
        assert "fail" in result.errors
        assert agent.call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test that timeout cancels long-running agents."""
        dag = DAG()
        agent = SlowAgent(config=AgentConfig(name="slow"), delay=5.0)
        dag.add_node("slow", agent)

        config = ExecutionConfig(timeout=0.5, max_retries=0)
        engine = ExecutionEngine(config=config)
        result = await engine.execute(dag)

        assert result.status["slow"] == AgentStatus.FAILED
        assert "timeout" in result.errors["slow"].lower() or "timed out" in result.errors["slow"].lower()

    @pytest.mark.asyncio
    async def test_fail_fast_mode(self):
        """Test that fail_fast cancels remaining nodes on first failure."""
        dag = DAG()

        fail_agent = FailingAgent(config=AgentConfig(name="fail_fast"))
        success_agent = MockAgent(config=AgentConfig(name="success"), delay=0.5)

        dag.add_node("fail", fail_agent)
        dag.add_node("success", success_agent)

        config = ExecutionConfig(fail_fast=True, max_retries=0)
        engine = ExecutionEngine(config=config)

        # Should raise ExecutionError in fail_fast mode
        with pytest.raises(ExecutionError):
            await engine.execute(dag)

    @pytest.mark.asyncio
    async def test_fail_fast_disabled(self):
        """Test that non-fail-fast mode continues after failure."""
        dag = DAG()

        fail_agent = FailingAgent(config=AgentConfig(name="fail"))
        success_agent = MockAgent(config=AgentConfig(name="success"))

        dag.add_node("fail", fail_agent)
        dag.add_node("success", success_agent)

        config = ExecutionConfig(fail_fast=False, max_retries=0)
        engine = ExecutionEngine(config=config)
        result = await engine.execute(dag)

        # Both nodes should be processed
        assert result.status["fail"] == AgentStatus.FAILED
        assert result.status["success"] == AgentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_dependency_failure_blocks_downstream(self):
        """Test that downstream nodes are blocked when dependencies fail."""
        dag = DAG()

        fail_agent = FailingAgent(config=AgentConfig(name="fail"))
        child_agent = MockAgent(config=AgentConfig(name="child"))
        leaf_agent = MockAgent(config=AgentConfig(name="leaf"))

        dag.add_node("fail", fail_agent)
        dag.add_node("child", child_agent)
        dag.add_node("leaf", leaf_agent)
        dag.add_edge("fail", "child")
        dag.add_edge("child", "leaf")

        config = ExecutionConfig(fail_fast=False, max_retries=0)
        engine = ExecutionEngine(config=config)
        result = await engine.execute(dag)

        assert result.status["fail"] == AgentStatus.FAILED
        assert result.status["child"] == AgentStatus.FAILED
        assert result.status["leaf"] == AgentStatus.FAILED
        assert result.errors["child"] == "Blocked by failed dependency: fail"
        assert result.errors["leaf"] == "Blocked by failed dependency: child"
        assert child_agent.call_count == 0
        assert leaf_agent.call_count == 0

    @pytest.mark.asyncio
    async def test_concurrency_limiting(self):
        """Test that max_concurrency limits parallel execution."""
        dag = DAG()

        # Create 4 agents that track their execution time
        agents = []
        for i in range(4):
            agent = MockAgent(
                config=AgentConfig(name=f"agent_{i}"),
                delay=0.2,
            )
            dag.add_node(f"agent_{i}", agent)
            agents.append(agent)

        # Limit to 2 concurrent executions
        config = ExecutionConfig(max_concurrency=2)
        engine = ExecutionEngine(config=config)

        import time
        start = time.monotonic()
        result = await engine.execute(dag)
        elapsed = time.monotonic() - start

        # All should complete
        assert all(result.status[f"agent_{i}"] == AgentStatus.COMPLETED for i in range(4))

        # With 4 agents at 0.2s each and max 2 concurrent:
        # Should take ~0.4s (2 batches), not ~0.2s (all parallel)
        assert elapsed >= 0.3, f"Expected >= 0.3s with concurrency limit, got {elapsed}s"
        assert elapsed < 0.8, f"Expected < 0.8s, got {elapsed}s"

    @pytest.mark.asyncio
    async def test_execute_node_method(self, single_node_dag):
        """Test the execute_node method for single node execution."""
        engine = ExecutionEngine()
        result = await engine.execute_node(single_node_dag, "single", context={"key": "value"})

        assert result.content == "mock response"

    @pytest.mark.asyncio
    async def test_execute_node_not_found(self, empty_dag):
        """Test execute_node raises error for non-existent node."""
        engine = ExecutionEngine()

        with pytest.raises(NodeNotFoundError):
            await engine.execute_node(empty_dag, "nonexistent")

    @pytest.mark.asyncio
    async def test_execution_hooks(self, single_node_dag):
        """Test pre and post execution hooks."""
        pre_calls = []
        post_calls = []

        def pre_hook(node_id, agent, input):
            pre_calls.append((node_id, agent.config.name))

        def post_hook(node_id, agent, output):
            post_calls.append((node_id, output.content))

        engine = ExecutionEngine(
            pre_hooks=[pre_hook],
            post_hooks=[post_hook],
        )
        await engine.execute(single_node_dag)

        assert len(pre_calls) == 1
        assert pre_calls[0] == ("single", "single_agent")

        assert len(post_calls) == 1
        assert post_calls[0] == ("single", "mock response")

    @pytest.mark.asyncio
    async def test_add_hooks_after_init(self, single_node_dag):
        """Test adding hooks after engine initialization."""
        calls = []

        engine = ExecutionEngine()
        engine.add_pre_hook(lambda nid, a, i: calls.append(f"pre:{nid}"))
        engine.add_post_hook(lambda nid, a, o: calls.append(f"post:{nid}"))

        await engine.execute(single_node_dag)

        assert "pre:single" in calls
        assert "post:single" in calls

    @pytest.mark.asyncio
    async def test_cancellation(self, parallel_dag):
        """Test that cancel() stops processing new nodes."""
        engine = ExecutionEngine()

        # Start execution and cancel immediately
        async def execute_and_cancel():
            # Create a task for execution
            task = asyncio.create_task(engine.execute(parallel_dag))

            # Give it a moment to start
            await asyncio.sleep(0.05)

            # Cancel the engine
            engine.cancel()

            # Wait for task to complete
            try:
                result = await task
                return result
            except asyncio.CancelledError:
                return None

        result = await execute_and_cancel()

        # Some nodes may have started before cancellation
        if result:
            # At least some nodes should have been processed
            assert len(result.status) > 0

    @pytest.mark.asyncio
    async def test_token_and_cost_aggregation(self, parallel_dag):
        """Test that tokens and costs are aggregated correctly."""
        engine = ExecutionEngine()
        result = await engine.execute(parallel_dag)

        # Each agent returns 30 tokens and 0.001 cost
        assert result.total_tokens == 90  # 3 agents * 30 tokens
        assert result.total_cost == 0.003  # 3 agents * 0.001 cost

    @pytest.mark.asyncio
    async def test_engine_alias(self):
        """Test that Engine is an alias for ExecutionEngine."""
        assert Engine is ExecutionEngine


class TestExecutionError:
    """Tests for ExecutionError exception."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = ExecutionError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.node_id is None
        assert error.cause is None

    def test_error_with_node_id(self):
        """Test error with node ID."""
        error = ExecutionError("Node failed", node_id="test_node")
        assert "[test_node]" in str(error)
        assert error.node_id == "test_node"

    def test_error_with_cause(self):
        """Test error with underlying cause."""
        cause = ValueError("Original error")
        error = ExecutionError("Wrapped error", cause=cause)
        assert error.cause == cause


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_agent_with_none_response(self):
        """Test agent that returns None content."""
        dag = DAG()

        class NoneAgent(BaseAgent):
            async def execute(self, input: AgentInput) -> AgentOutput:
                return AgentOutput(content=None)

        dag.add_node("none", NoneAgent())
        engine = ExecutionEngine()
        result = await engine.execute(dag)

        assert result.status["none"] == AgentStatus.COMPLETED
        assert result.outputs["none"].content is None

    @pytest.mark.asyncio
    async def test_agent_with_tool_calls(self):
        """Test agent that returns tool calls."""
        dag = DAG()

        from agentforge.core.types import ToolCall

        class ToolAgent(BaseAgent):
            async def execute(self, input: AgentInput) -> AgentOutput:
                return AgentOutput(
                    content="Using tool",
                    tool_calls=[ToolCall(name="test_tool", arguments={"arg": "value"})],
                )

        dag.add_node("tool", ToolAgent())
        engine = ExecutionEngine()
        result = await engine.execute(dag)

        assert len(result.outputs["tool"].tool_calls) == 1
        assert result.outputs["tool"].tool_calls[0].name == "test_tool"

    @pytest.mark.asyncio
    async def test_hook_exception_does_not_fail_execution(self, single_node_dag):
        """Test that hook exceptions don't fail the execution."""
        def failing_hook(node_id, agent, input):
            raise Exception("Hook failed!")

        engine = ExecutionEngine(pre_hooks=[failing_hook])
        result = await engine.execute(single_node_dag)

        # Execution should still succeed
        assert result.status["single"] == AgentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        """Test that retry delay uses exponential backoff."""
        dag = DAG()

        agent = MockAgent(
            config=AgentConfig(name="backoff"),
            fail_count=2,
            delay=0.01,
        )
        dag.add_node("backoff", agent)

        config = ExecutionConfig(max_retries=3, retry_delay=0.1)
        engine = ExecutionEngine(config=config)

        import time
        start = time.monotonic()
        await engine.execute(dag)
        elapsed = time.monotonic() - start

        # With exponential backoff: 0.1s + 0.2s = 0.3s minimum delay
        # Plus execution time
        assert elapsed >= 0.25, f"Expected >= 0.25s with backoff, got {elapsed}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
