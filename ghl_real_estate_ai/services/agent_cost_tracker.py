"""Agent Decision Cost Tracker for EnterpriseHub.

Tracks per-agent and per-decision-type costs, detects anomalies,
and computes token efficiency metrics for cost optimization.
"""

from __future__ import annotations

import math
import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DecisionCost:
    """Single decision cost record."""

    agent_name: str
    decision_type: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentCostSummary:
    """Aggregated cost summary for a single agent."""

    total_cost: float
    avg_cost: float
    total_tokens: int
    decision_count: int
    avg_latency: float


@dataclass
class CostReport:
    """Full cost report across all agents."""

    agent_summaries: Dict[str, AgentCostSummary]
    total_cost: float
    total_tokens: int
    anomalies: List[int]
    efficiency_rankings: Dict[str, float]
    generated_at: float


class DecisionCostTracker:
    """Tracks costs per agent and decision type."""

    def __init__(self) -> None:
        self._records: List[DecisionCost] = []

    def record(
        self,
        agent_name: str,
        decision_type: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        latency_ms: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DecisionCost:
        """Record a single decision cost entry."""
        entry = DecisionCost(
            agent_name=agent_name,
            decision_type=decision_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            timestamp=time.time(),
            metadata=metadata or {},
        )
        self._records.append(entry)
        return entry

    def get_agent_summary(self, agent_name: str) -> AgentCostSummary:
        """Return aggregated cost summary for a given agent."""
        agent_records = [r for r in self._records if r.agent_name == agent_name]
        if not agent_records:
            return AgentCostSummary(
                total_cost=0.0,
                avg_cost=0.0,
                total_tokens=0,
                decision_count=0,
                avg_latency=0.0,
            )
        total_cost = sum(r.cost_usd for r in agent_records)
        total_tokens = sum(r.total_tokens for r in agent_records)
        avg_cost = total_cost / len(agent_records)
        avg_latency = sum(r.latency_ms for r in agent_records) / len(agent_records)
        return AgentCostSummary(
            total_cost=total_cost,
            avg_cost=avg_cost,
            total_tokens=total_tokens,
            decision_count=len(agent_records),
            avg_latency=avg_latency,
        )

    def get_decision_type_summary(self, decision_type: str) -> Dict[str, Any]:
        """Return aggregated summary for a given decision type."""
        type_records = [r for r in self._records if r.decision_type == decision_type]
        if not type_records:
            return {
                "decision_type": decision_type,
                "total_cost": 0.0,
                "avg_cost": 0.0,
                "total_tokens": 0,
                "decision_count": 0,
                "avg_latency": 0.0,
            }
        total_cost = sum(r.cost_usd for r in type_records)
        return {
            "decision_type": decision_type,
            "total_cost": total_cost,
            "avg_cost": total_cost / len(type_records),
            "total_tokens": sum(r.total_tokens for r in type_records),
            "decision_count": len(type_records),
            "avg_latency": sum(r.latency_ms for r in type_records) / len(type_records),
        }

    def get_all_summaries(self) -> Dict[str, AgentCostSummary]:
        """Return summaries for all tracked agents."""
        agent_names = {r.agent_name for r in self._records}
        return {name: self.get_agent_summary(name) for name in sorted(agent_names)}

    def get_top_costly_agents(self, n: int) -> List[str]:
        """Return the top-N agents by total cost (descending)."""
        summaries = self.get_all_summaries()
        ranked = sorted(summaries.items(), key=lambda kv: kv[1].total_cost, reverse=True)
        return [name for name, _ in ranked[:n]]

    def get_cost_trend(self, agent_name: str, window_size: int) -> List[float]:
        """Return rolling average cost trend for an agent."""
        agent_records = [r for r in self._records if r.agent_name == agent_name]
        costs = [r.cost_usd for r in agent_records]
        if not costs or window_size <= 0:
            return []
        result: List[float] = []
        for i in range(len(costs)):
            start = max(0, i - window_size + 1)
            window = costs[start : i + 1]
            result.append(sum(window) / len(window))
        return result


class CostAnomalyDetector:
    """Detect unusual cost spikes using z-score analysis."""

    def detect_anomalies(self, costs: List[float], threshold_std: float = 2.0) -> List[int]:
        """Return indices of anomalous cost entries.

        Uses z-score: any value more than threshold_std standard deviations
        from the mean is flagged.
        """
        if len(costs) < 2:
            return []
        mean = statistics.mean(costs)
        stdev = statistics.stdev(costs)
        if stdev == 0:
            return []
        return [i for i, c in enumerate(costs) if abs(c - mean) / stdev > threshold_std]

    def is_anomalous(self, value: float, history: List[float]) -> bool:
        """Check if a single value is anomalous given historical data."""
        if len(history) < 2:
            return False
        mean = statistics.mean(history)
        stdev = statistics.stdev(history)
        if stdev == 0:
            return value != mean
        z_score = abs(value - mean) / stdev
        return z_score > 2.0


class TokenEfficiencyMetrics:
    """Compute quality-to-cost ratios for agent evaluation."""

    def compute_efficiency(self, quality_score: float, token_count: int) -> float:
        """Return quality per token (higher is better)."""
        if token_count <= 0:
            return 0.0
        return quality_score / token_count

    def compute_cost_per_quality(self, cost_usd: float, quality_score: float) -> float:
        """Return cost per unit of quality (lower is better)."""
        if quality_score <= 0:
            return math.inf
        return cost_usd / quality_score

    def compare_agents(self, summaries: Dict[str, AgentCostSummary]) -> Dict[str, float]:
        """Rank agents by token efficiency (total_tokens / decision_count).

        Lower ratio means fewer tokens per decision (more efficient).
        """
        rankings: Dict[str, float] = {}
        for name, summary in summaries.items():
            if summary.decision_count > 0:
                rankings[name] = summary.total_tokens / summary.decision_count
            else:
                rankings[name] = 0.0
        return dict(sorted(rankings.items(), key=lambda kv: kv[1]))
