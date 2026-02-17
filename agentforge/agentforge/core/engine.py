"""Async execution engine for AgentForge DAG orchestration.

This module provides the execution engine for running DAGs of agents
in parallel while respecting dependencies. It supports retry logic,
timeouts, concurrency limiting, and comprehensive error handling.

Example:
    ```python
    from agentforge.core import DAG, ExecutionEngine, ExecutionConfig

    # Create and configure DAG
    dag = DAG()
    dag.add_node("agent_a", agent_a)
    dag.add_node("agent_b", agent_b)
    dag.add_edge("agent_a", "agent_b")

    # Execute with custom config
    config = ExecutionConfig(max_retries=3, timeout=30.0)
    engine = ExecutionEngine(config)
    result = await engine.execute(dag)

    # Access results
    print(result.outputs["agent_a"].content)
    ```
"""

import asyncio
import logging
import time
from collections import deque
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from agentforge.core.agent import AgentInput, AgentOutput, BaseAgent
from agentforge.core.dag import DAG
from agentforge.core.exceptions import ExecutionError, NodeNotFoundError
from agentforge.core.types import AgentStatus

logger = logging.getLogger(__name__)


# Type aliases for hooks
PreExecutionHook = Callable[[str, BaseAgent, AgentInput], None]
PostExecutionHook = Callable[[str, BaseAgent, AgentOutput], None]


class ExecutionConfig(BaseModel):
    """Configuration for DAG execution.

    Attributes:
        max_retries: Maximum number of retry attempts for failed nodes.
        retry_delay: Initial delay in seconds between retries (exponential backoff).
        timeout: Optional timeout in seconds for each node execution.
        fail_fast: If True, cancel all pending nodes on first failure.
        max_concurrency: Optional limit on parallel node executions.
    """
    max_retries: int = Field(default=3, ge=0, description="Maximum retry attempts")
    retry_delay: float = Field(default=1.0, ge=0.0, description="Initial retry delay in seconds")
    timeout: float | None = Field(default=None, ge=0.0, description="Per-node timeout in seconds")
    fail_fast: bool = Field(default=False, description="Cancel on first failure")
    max_concurrency: int | None = Field(
        default=None,
        ge=1,
        description="Maximum parallel executions"
    )


class ExecutionResult(BaseModel):
    """Result of DAG execution.

    Attributes:
        outputs: Mapping of node IDs to their execution outputs.
        status: Mapping of node IDs to their final status.
        errors: Mapping of node IDs to error messages (if any).
        execution_time: Total execution time in seconds.
        total_tokens: Sum of tokens used across all nodes.
        total_cost: Estimated total cost in dollars.
    """
    outputs: dict[str, AgentOutput] = Field(default_factory=dict)
    status: dict[str, AgentStatus] = Field(default_factory=dict)
    errors: dict[str, str] = Field(default_factory=dict)
    execution_time: float = Field(default=0.0, description="Total execution time in seconds")
    total_tokens: int = Field(default=0, ge=0, description="Total tokens used")
    total_cost: float = Field(default=0.0, ge=0.0, description="Total cost in dollars")


class ExecutionEngine:
    """Async-first execution engine for DAG orchestration.

    Executes DAGs of agents in parallel while respecting dependencies.
    Supports retry logic with exponential backoff, per-node timeouts,
    concurrency limiting, and comprehensive error handling.

    Attributes:
        config: Execution configuration.

    Example:
        ```python
        engine = ExecutionEngine(ExecutionConfig(max_retries=2))
        result = await engine.execute(dag, AgentInput(messages=[...]))
        ```
    """

    def __init__(
        self,
        config: ExecutionConfig | None = None,
        pre_hooks: list[PreExecutionHook] | None = None,
        post_hooks: list[PostExecutionHook] | None = None,
    ) -> None:
        """Initialize the execution engine.

        Args:
            config: Execution configuration. Uses defaults if not provided.
            pre_hooks: List of hooks to call before each node execution.
            post_hooks: List of hooks to call after each node execution.
        """
        self.config = config or ExecutionConfig()
        self._pre_hooks = pre_hooks or []
        self._post_hooks = post_hooks or []
        self._semaphore: asyncio.Semaphore | None = None
        self._cancelled = False

    async def execute(
        self,
        dag: DAG,
        input: AgentInput | None = None
    ) -> ExecutionResult:
        """Execute all nodes in the DAG respecting dependencies.

        Nodes are executed in parallel when their dependencies are satisfied.
        The execution follows a level-by-level approach where all ready nodes
        at each level are executed concurrently.

        Args:
            dag: The DAG to execute.
            input: Optional input to pass to all agents.

        Returns:
            ExecutionResult containing outputs, status, errors, and metrics.

        Raises:
            ExecutionError: If fail_fast is True and a node fails.
        """
        start_time = time.monotonic()
        self._cancelled = False

        # Initialize semaphore for concurrency limiting
        if self.config.max_concurrency:
            self._semaphore = asyncio.Semaphore(self.config.max_concurrency)
        else:
            self._semaphore = None

        # Track execution state
        outputs: dict[str, AgentOutput] = {}
        status: dict[str, AgentStatus] = {}
        errors: dict[str, str] = {}
        completed: set[str] = set()

        # Initialize status for all nodes
        for node_id in dag.nodes:
            status[node_id] = AgentStatus.IDLE

        try:
            # Execute DAG level by level
            await self._execute_dag_levels(dag, input, outputs, status, errors, completed)
        except asyncio.CancelledError:
            # Mark remaining nodes as failed
            for node_id in dag.nodes:
                if node_id not in completed:
                    status[node_id] = AgentStatus.FAILED
                    errors[node_id] = "Execution cancelled"
            raise
        finally:
            # Calculate metrics
            execution_time = time.monotonic() - start_time
            total_tokens = sum(
                out.usage.get("total_tokens", 0)
                for out in outputs.values()
                if out.usage
            )
            total_cost = sum(
                out.metadata.get("cost", 0.0)
                for out in outputs.values()
            )

        return ExecutionResult(
            outputs=outputs,
            status=status,
            errors=errors,
            execution_time=execution_time,
            total_tokens=total_tokens,
            total_cost=total_cost,
        )

    async def _execute_dag_levels(
        self,
        dag: DAG,
        input: AgentInput | None,
        outputs: dict[str, AgentOutput],
        status: dict[str, AgentStatus],
        errors: dict[str, str],
        completed: set[str],
    ) -> None:
        """Execute DAG level by level with parallel execution within levels."""
        ready_queue: deque[str] = deque()

        # Seed with root nodes (no dependencies)
        for node_id in dag.nodes:
            if dag.in_degree(node_id) == 0:
                ready_queue.append(node_id)

        while ready_queue and not self._cancelled:
            # Gather all currently-ready nodes for parallel execution
            batch: list[str] = []
            while ready_queue:
                batch.append(ready_queue.popleft())

            if not batch:
                break

            # Execute batch in parallel
            batch_results = await asyncio.gather(
                *[self._execute_node_safe(dag, node_id, input, outputs, status)
                  for node_id in batch],
                return_exceptions=True,
            )

            # Process results and unlock successors
            for node_id, result in zip(batch, batch_results, strict=True):
                if isinstance(result, Exception):
                    # Handle exception
                    error_msg = str(result)
                    outputs[node_id] = AgentOutput(error=error_msg)
                    status[node_id] = AgentStatus.FAILED
                    errors[node_id] = error_msg
                    completed.add(node_id)

                    if self.config.fail_fast:
                        self._cancelled = True
                        if not isinstance(result, asyncio.CancelledError):
                            raise ExecutionError(
                                f"Node failed: {error_msg}",
                                node_id=node_id,
                                cause=result,
                            )
                else:
                    # Success
                    outputs[node_id] = result
                    status[node_id] = AgentStatus.COMPLETED
                    completed.add(node_id)

                self._queue_or_block_successors(
                    dag=dag,
                    node_id=node_id,
                    ready_queue=ready_queue,
                    outputs=outputs,
                    status=status,
                    errors=errors,
                    completed=completed,
                )

    def _queue_or_block_successors(
        self,
        dag: DAG,
        node_id: str,
        ready_queue: deque[str],
        outputs: dict[str, AgentOutput],
        status: dict[str, AgentStatus],
        errors: dict[str, str],
        completed: set[str],
    ) -> None:
        """Queue successors that are ready or mark them blocked by failed dependencies."""
        for successor in dag.successors(node_id):
            if successor in completed or successor in ready_queue:
                continue

            predecessors = set(dag.predecessors(successor))
            failed_predecessors = [
                predecessor
                for predecessor in predecessors
                if status.get(predecessor) == AgentStatus.FAILED
            ]

            if failed_predecessors:
                self._mark_blocked_subgraph(
                    dag=dag,
                    node_id=successor,
                    failed_predecessors=failed_predecessors,
                    outputs=outputs,
                    status=status,
                    errors=errors,
                    completed=completed,
                )
                continue

            if predecessors.issubset(completed):
                ready_queue.append(successor)

    def _mark_blocked_subgraph(
        self,
        dag: DAG,
        node_id: str,
        failed_predecessors: list[str],
        outputs: dict[str, AgentOutput],
        status: dict[str, AgentStatus],
        errors: dict[str, str],
        completed: set[str],
    ) -> None:
        """Mark a node and blocked downstream nodes as failed due to dependency failures."""
        if node_id in completed:
            return

        dependency_list = ", ".join(sorted(set(failed_predecessors)))
        error_msg = f"Blocked by failed dependency: {dependency_list}"
        outputs[node_id] = AgentOutput(error=error_msg)
        status[node_id] = AgentStatus.FAILED
        errors[node_id] = error_msg
        completed.add(node_id)

        for successor in dag.successors(node_id):
            if successor in completed:
                continue

            successor_predecessors = set(dag.predecessors(successor))
            successor_failed = [
                predecessor
                for predecessor in successor_predecessors
                if status.get(predecessor) == AgentStatus.FAILED
            ]
            if successor_failed:
                self._mark_blocked_subgraph(
                    dag=dag,
                    node_id=successor,
                    failed_predecessors=successor_failed,
                    outputs=outputs,
                    status=status,
                    errors=errors,
                    completed=completed,
                )

    async def _execute_node_safe(
        self,
        dag: DAG,
        node_id: str,
        input: AgentInput | None,
        outputs: dict[str, AgentOutput],
        status: dict[str, AgentStatus],
    ) -> AgentOutput:
        """Execute a single node with concurrency control and error handling."""
        agent = dag.get_node(node_id)
        if agent is None:
            raise NodeNotFoundError(node_id)

        # Apply concurrency limit
        if self._semaphore:
            async with self._semaphore:
                return await self._execute_node_with_hooks(node_id, agent, input, status)
        else:
            return await self._execute_node_with_hooks(node_id, agent, input, status)

    async def _execute_node_with_hooks(
        self,
        node_id: str,
        agent: BaseAgent,
        input: AgentInput | None,
        status: dict[str, AgentStatus],
    ) -> AgentOutput:
        """Execute node with pre/post hooks."""
        # Prepare input
        exec_input = input or AgentInput()

        # Run pre-execution hooks
        for hook in self._pre_hooks:
            try:
                hook(node_id, agent, exec_input)
            except Exception:
                logger.exception("Pre-execution hook failed for node '%s'", node_id)

        # Update status
        status[node_id] = AgentStatus.RUNNING
        agent.status = AgentStatus.RUNNING

        try:
            # Execute with retry and timeout
            output = await self._execute_with_retry(agent, exec_input)
            status[node_id] = AgentStatus.COMPLETED
            agent.status = AgentStatus.COMPLETED
        except Exception:
            status[node_id] = AgentStatus.FAILED
            agent.status = AgentStatus.FAILED
            raise

        # Run post-execution hooks
        for hook in self._post_hooks:
            try:
                hook(node_id, agent, output)
            except Exception:
                logger.exception("Post-execution hook failed for node '%s'", node_id)

        return output

    async def execute_node(
        self,
        dag: DAG,
        node_id: str,
        context: dict[str, Any] | None = None
    ) -> AgentOutput:
        """Execute a single node from the DAG.

        This method is useful for testing or selective execution.
        It does not respect dependencies - use execute() for full DAG execution.

        Args:
            dag: The DAG containing the node.
            node_id: ID of the node to execute.
            context: Optional context data to include in the input.

        Returns:
            AgentOutput from the node execution.

        Raises:
            NodeNotFoundError: If the node doesn't exist in the DAG.
            ExecutionError: If execution fails after all retries.
        """
        agent = dag.get_node(node_id)
        if agent is None:
            raise NodeNotFoundError(node_id)

        # Build input from context
        input = AgentInput()
        if context:
            input.context.metadata.update(context)

        # Initialize semaphore if needed
        if self.config.max_concurrency and not self._semaphore:
            self._semaphore = asyncio.Semaphore(self.config.max_concurrency)

        # Apply concurrency limit
        if self._semaphore:
            async with self._semaphore:
                return await self._execute_with_retry(agent, input)
        else:
            return await self._execute_with_retry(agent, input)

    async def _execute_with_retry(
        self,
        agent: BaseAgent,
        input: AgentInput
    ) -> AgentOutput:
        """Execute agent with exponential backoff retry.

        Retries on any exception up to max_retries times with exponential
        backoff delay between attempts.

        Args:
            agent: The agent to execute.
            input: The input for the agent.

        Returns:
            AgentOutput from successful execution.

        Raises:
            ExecutionError: If all retries are exhausted.
        """
        last_exception: Exception | None = None

        for attempt in range(self.config.max_retries + 1):
            if self._cancelled:
                raise asyncio.CancelledError()

            try:
                return await self._execute_with_timeout(agent, input)
            except asyncio.CancelledError:
                raise
            except TimeoutError as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
            except Exception as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)

        # All retries exhausted
        error_type = "Timeout" if isinstance(last_exception, asyncio.TimeoutError) else "Execution"
        raise ExecutionError(
            f"{error_type} failed after {self.config.max_retries + 1} attempts: {last_exception}",
            node_id=agent.agent_id,
            cause=last_exception,
        )

    async def _execute_with_timeout(
        self,
        agent: BaseAgent,
        input: AgentInput
    ) -> AgentOutput:
        """Execute agent with optional timeout.

        Args:
            agent: The agent to execute.
            input: The input for the agent.

        Returns:
            AgentOutput from execution.

        Raises:
            asyncio.TimeoutError: If timeout is set and exceeded.
            Exception: Any exception from agent execution.
        """
        if self.config.timeout:
            return await asyncio.wait_for(
                agent.execute(input),
                timeout=self.config.timeout,
            )
        else:
            return await agent.execute(input)

    def cancel(self) -> None:
        """Cancel ongoing execution.

        Sets a flag that will stop processing new nodes. Currently
        executing nodes will complete.
        """
        self._cancelled = True

    def add_pre_hook(self, hook: PreExecutionHook) -> None:
        """Add a pre-execution hook.

        Args:
            hook: Callable that receives (node_id, agent, input) before execution.
        """
        self._pre_hooks.append(hook)

    def add_post_hook(self, hook: PostExecutionHook) -> None:
        """Add a post-execution hook.

        Args:
            hook: Callable that receives (node_id, agent, output) after execution.
        """
        self._post_hooks.append(hook)


# Alias for backward compatibility
Engine = ExecutionEngine


__all__ = [
    "ExecutionConfig",
    "ExecutionResult",
    "ExecutionEngine",
    "Engine",
    "PreExecutionHook",
    "PostExecutionHook",
]
