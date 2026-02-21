"""Token usage and cost tracking for AgentForge.

This module provides metrics collection for monitoring LLM usage,
costs, and latencies across agent executions.

Features:
- Token usage tracking per agent
- Cost tracking in USD
- Latency percentile statistics (P50, P95, P99)
- Summary aggregation
"""

import time
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """Token usage record.

    Tracks prompt, completion, and total token counts.
    Supports addition for aggregation.

    Attributes:
        prompt_tokens: Number of tokens in the prompt.
        completion_tokens: Number of tokens in the completion.
        total_tokens: Total tokens (prompt + completion).

    Example:
        ```python
        usage1 = TokenUsage(prompt_tokens=100, completion_tokens=50)
        usage2 = TokenUsage(prompt_tokens=200, completion_tokens=100)
        total = usage1 + usage2  # TokenUsage(prompt_tokens=300, completion_tokens=150)
        ```
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        """Add two TokenUsage instances together."""
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> "TokenUsage":
        """Create TokenUsage from a dictionary.

        Args:
            data: Dictionary with token counts.

        Returns:
            TokenUsage instance.
        """
        return cls(
            prompt_tokens=data.get("prompt_tokens", 0),
            completion_tokens=data.get("completion_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
        )


class CostRecord(BaseModel):
    """Cost tracking record.

    Records a single cost event with metadata.

    Attributes:
        amount: Cost amount in USD.
        model: LLM model that generated the cost.
        provider: LLM provider (e.g., "openai", "anthropic").
        timestamp: When the cost was recorded.
        tokens: Optional token usage associated with this cost.
        metadata: Additional metadata about the cost event.

    Example:
        ```python
        cost = CostRecord(
            amount=0.002,
            model="gpt-4o",
            provider="openai",
            tokens=TokenUsage(prompt_tokens=100, completion_tokens=50)
        )
        ```
    """

    amount: float = Field(ge=0.0, description="Cost in USD")
    model: str = Field(description="LLM model name")
    provider: str = Field(default="unknown", description="LLM provider")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tokens: TokenUsage | None = None
    metadata: dict[str, Any] | None = None


class LatencyStats(BaseModel):
    """Latency statistics for an operation.

    Provides percentile-based latency metrics.

    Attributes:
        p50: 50th percentile latency (median).
        p95: 95th percentile latency.
        p99: 99th percentile latency.
        avg: Average latency.
        count: Number of samples.
    """

    p50: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    avg: float = 0.0
    count: int = 0


class MetricsCollector:
    """Collects and aggregates metrics for AgentForge.

    Tracks token usage, costs, and latencies across agent executions.
    Provides summary statistics and aggregation methods.

    Example:
        ```python
        metrics = MetricsCollector()

        # Record token usage
        metrics.record_tokens("lead-bot", TokenUsage(prompt_tokens=100, completion_tokens=50))

        # Record cost
        metrics.record_cost(CostRecord(amount=0.002, model="gpt-4o", provider="openai"))

        # Time an operation
        metrics.start_timer("llm_call")
        # ... do work ...
        latency = metrics.end_timer("llm_call")

        # Get summary
        print(metrics.get_summary())
        ```
    """

    def __init__(self):
        """Initialize the metrics collector."""
        self._token_usage: dict[str, TokenUsage] = {}  # by agent
        self._costs: list[CostRecord] = []
        self._latencies: dict[str, list[float]] = {}  # by operation
        self._start_times: dict[str, float] = {}

    def record_tokens(self, agent: str, usage: TokenUsage) -> None:
        """Record token usage for an agent.

        Args:
            agent: Name or ID of the agent.
            usage: Token usage to record.
        """
        if agent not in self._token_usage:
            self._token_usage[agent] = TokenUsage()
        self._token_usage[agent] = self._token_usage[agent] + usage

    def record_cost(self, cost: CostRecord) -> None:
        """Record a cost event.

        Args:
            cost: Cost record to add.
        """
        self._costs.append(cost)

    def record_cost_simple(
        self,
        amount: float,
        model: str,
        provider: str = "unknown",
        tokens: TokenUsage | None = None,
    ) -> None:
        """Record a cost event with simplified parameters.

        Args:
            amount: Cost in USD.
            model: LLM model name.
            provider: LLM provider name.
            tokens: Optional token usage.
        """
        self.record_cost(
            CostRecord(
                amount=amount,
                model=model,
                provider=provider,
                tokens=tokens,
            )
        )

    def start_timer(self, operation: str) -> None:
        """Start timing an operation.

        Args:
            operation: Name of the operation to time.
        """
        self._start_times[operation] = time.perf_counter()

    def end_timer(self, operation: str) -> float:
        """End timing and record latency.

        Args:
            operation: Name of the operation that was timed.

        Returns:
            The latency in seconds, or 0.0 if timer wasn't started.
        """
        start = self._start_times.pop(operation, None)
        if start is None:
            return 0.0
        latency = time.perf_counter() - start
        if operation not in self._latencies:
            self._latencies[operation] = []
        self._latencies[operation].append(latency)
        return latency

    def get_total_tokens(self) -> TokenUsage:
        """Get total token usage across all agents.

        Returns:
            TokenUsage with aggregated totals.
        """
        total = TokenUsage()
        for usage in self._token_usage.values():
            total = total + usage
        return total

    def get_agent_tokens(self, agent: str) -> TokenUsage | None:
        """Get token usage for a specific agent.

        Args:
            agent: Name or ID of the agent.

        Returns:
            TokenUsage for the agent, or None if not found.
        """
        return self._token_usage.get(agent)

    def get_total_cost(self) -> float:
        """Get total cost in USD.

        Returns:
            Sum of all recorded costs.
        """
        return sum(c.amount for c in self._costs)

    def get_cost_by_model(self) -> dict[str, float]:
        """Get costs grouped by model.

        Returns:
            Dictionary mapping model names to total costs.
        """
        costs: dict[str, float] = {}
        for record in self._costs:
            if record.model not in costs:
                costs[record.model] = 0.0
            costs[record.model] += record.amount
        return costs

    def get_latency_stats(self, operation: str) -> LatencyStats:
        """Get latency statistics for an operation.

        Args:
            operation: Name of the operation.

        Returns:
            LatencyStats with percentile metrics.
        """
        latencies = self._latencies.get(operation, [])
        if not latencies:
            return LatencyStats()

        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)

        return LatencyStats(
            p50=sorted_latencies[n // 2],
            p95=sorted_latencies[int(n * 0.95)] if n >= 20 else sorted_latencies[-1],
            p99=sorted_latencies[int(n * 0.99)] if n >= 100 else sorted_latencies[-1],
            avg=sum(sorted_latencies) / n,
            count=n,
        )

    def get_all_latency_stats(self) -> dict[str, LatencyStats]:
        """Get latency statistics for all operations.

        Returns:
            Dictionary mapping operation names to LatencyStats.
        """
        return {op: self.get_latency_stats(op) for op in self._latencies}

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of all metrics.

        Returns:
            Dictionary containing:
            - tokens: Total token usage
            - cost_usd: Total cost in USD
            - cost_by_model: Costs grouped by model
            - latencies: Latency stats for all operations
            - agent_tokens: Token usage by agent
        """
        return {
            "tokens": self.get_total_tokens().model_dump(),
            "cost_usd": self.get_total_cost(),
            "cost_by_model": self.get_cost_by_model(),
            "latencies": {k: self.get_latency_stats(k).model_dump() for k in self._latencies},
            "agent_tokens": {k: v.model_dump() for k, v in self._token_usage.items()},
        }

    def clear(self) -> None:
        """Clear all collected metrics."""
        self._token_usage.clear()
        self._costs.clear()
        self._latencies.clear()
        self._start_times.clear()

    @property
    def agent_count(self) -> int:
        """Number of agents with recorded token usage."""
        return len(self._token_usage)

    @property
    def cost_count(self) -> int:
        """Number of cost records."""
        return len(self._costs)


# Global metrics collector
_global_collector: MetricsCollector | None = None


def get_metrics() -> MetricsCollector:
    """Get or create the global metrics collector.

    Returns:
        The global MetricsCollector instance.

    Example:
        ```python
        metrics = get_metrics()
        metrics.record_tokens("agent-1", TokenUsage(prompt_tokens=100, completion_tokens=50))
        ```
    """
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


def reset_metrics() -> None:
    """Reset the global metrics collector.

    Useful for testing or clearing metrics between runs.
    """
    global _global_collector
    _global_collector = None


__all__ = [
    "TokenUsage",
    "CostRecord",
    "LatencyStats",
    "MetricsCollector",
    "get_metrics",
    "reset_metrics",
]
