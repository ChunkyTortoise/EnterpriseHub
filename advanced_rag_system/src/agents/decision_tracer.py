"""RAG Decision Tracer for EnterpriseHub.

Provides W3C-style trace context for RAG pipeline decisions, quality
correlation analysis, and agent routing logging.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class DecisionSpan:
    """A single span in a decision trace."""

    span_id: str
    parent_id: Optional[str]
    operation: str
    rationale: str
    tool_chosen: Optional[str]
    alternatives: List[str]
    confidence: float
    start_time: float
    end_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DecisionTracer:
    """W3C-style trace context for RAG decision pipelines."""

    def __init__(self) -> None:
        self._trace_id: str = uuid4().hex
        self._spans: Dict[str, DecisionSpan] = {}
        self._order: List[str] = []

    @property
    def trace_id(self) -> str:
        return self._trace_id

    def start_span(
        self,
        operation: str,
        rationale: str,
        parent_id: Optional[str] = None,
        tool_chosen: Optional[str] = None,
        alternatives: Optional[List[str]] = None,
        confidence: float = 1.0,
    ) -> DecisionSpan:
        """Create and register a new span."""
        span = DecisionSpan(
            span_id=uuid4().hex,
            parent_id=parent_id,
            operation=operation,
            rationale=rationale,
            tool_chosen=tool_chosen,
            alternatives=alternatives or [],
            confidence=confidence,
            start_time=time.time(),
        )
        self._spans[span.span_id] = span
        self._order.append(span.span_id)
        return span

    def end_span(self, span_id: str) -> DecisionSpan:
        """Mark a span as completed."""
        span = self._spans[span_id]
        span.end_time = time.time()
        return span

    def get_trace(self) -> List[DecisionSpan]:
        """Return all spans in creation order."""
        return [self._spans[sid] for sid in self._order]

    def get_children(self, span_id: str) -> List[DecisionSpan]:
        """Return immediate children of a span."""
        return [s for s in self._spans.values() if s.parent_id == span_id]

    def get_critical_path(self) -> List[DecisionSpan]:
        """Return the longest chain of parent-child spans.

        Builds a tree from root spans and finds the deepest path.
        """
        if not self._spans:
            return []

        # Build children lookup
        children_map: Dict[Optional[str], List[str]] = {}
        for sid, span in self._spans.items():
            children_map.setdefault(span.parent_id, []).append(sid)

        # DFS to find longest path
        def _longest_path(span_id: str) -> List[DecisionSpan]:
            kids = children_map.get(span_id, [])
            if not kids:
                return [self._spans[span_id]]
            best: List[DecisionSpan] = []
            for kid_id in kids:
                candidate = _longest_path(kid_id)
                if len(candidate) > len(best):
                    best = candidate
            return [self._spans[span_id]] + best

        # Find roots (no parent or parent not in spans)
        roots = [sid for sid, s in self._spans.items() if s.parent_id is None or s.parent_id not in self._spans]

        overall_best: List[DecisionSpan] = []
        for root_id in roots:
            path = _longest_path(root_id)
            if len(path) > len(overall_best):
                overall_best = path
        return overall_best

    def reset(self) -> None:
        """Clear all spans and generate a new trace ID."""
        self._spans.clear()
        self._order.clear()
        self._trace_id = uuid4().hex


# ---------------------------------------------------------------------------
# Quality Trace Analyzer
# ---------------------------------------------------------------------------


@dataclass
class AnalysisResult:
    """Result of correlating a span with quality metrics."""

    span_id: str
    quality_score: float
    cost_contribution: float
    latency_contribution: float


class QualityTraceAnalyzer:
    """Correlate decision spans with quality scores."""

    def analyze(
        self,
        trace: List[DecisionSpan],
        quality_scores: Dict[str, float],
    ) -> List[AnalysisResult]:
        """Produce an AnalysisResult per span.

        quality_scores maps span_id -> quality score.
        Cost contribution is approximated as the fraction of total trace
        latency consumed by each span.
        """
        total_latency = sum(self._span_latency(s) for s in trace)
        results: List[AnalysisResult] = []
        for span in trace:
            lat = self._span_latency(span)
            cost_frac = (lat / total_latency) if total_latency > 0 else 0.0
            results.append(
                AnalysisResult(
                    span_id=span.span_id,
                    quality_score=quality_scores.get(span.span_id, 0.0),
                    cost_contribution=cost_frac,
                    latency_contribution=lat,
                )
            )
        return results

    def identify_bottlenecks(
        self,
        trace: List[DecisionSpan],
        top_n: int = 3,
    ) -> List[DecisionSpan]:
        """Return the top-N slowest spans."""
        ranked = sorted(trace, key=lambda s: self._span_latency(s), reverse=True)
        return ranked[:top_n]

    def identify_low_confidence(
        self,
        trace: List[DecisionSpan],
        threshold: float = 0.5,
    ) -> List[DecisionSpan]:
        """Return spans below the confidence threshold."""
        return [s for s in trace if s.confidence < threshold]

    @staticmethod
    def _span_latency(span: DecisionSpan) -> float:
        if span.end_time is None:
            return 0.0
        return max(0.0, span.end_time - span.start_time)


# ---------------------------------------------------------------------------
# Agent Routing Log
# ---------------------------------------------------------------------------


@dataclass
class RoutingDecision:
    """A logged routing decision between agents."""

    from_agent: str
    to_agent: str
    reason: str
    confidence: float
    timestamp: float
    context_summary: str


class AgentRoutingLog:
    """Log and query routing decisions between agents."""

    def __init__(self) -> None:
        self._decisions: List[RoutingDecision] = []

    def log_routing(
        self,
        from_agent: str,
        to_agent: str,
        reason: str,
        confidence: float,
        context: str = "",
    ) -> RoutingDecision:
        """Record a routing decision."""
        decision = RoutingDecision(
            from_agent=from_agent,
            to_agent=to_agent,
            reason=reason,
            confidence=confidence,
            timestamp=time.time(),
            context_summary=context,
        )
        self._decisions.append(decision)
        return decision

    def get_routing_history(self, agent_name: str) -> List[RoutingDecision]:
        """Return all routing decisions involving the given agent (source or dest)."""
        return [d for d in self._decisions if d.from_agent == agent_name or d.to_agent == agent_name]

    def get_routing_stats(self) -> Dict[str, Any]:
        """Return per-agent routing counts and average confidence."""
        stats: Dict[str, Dict[str, Any]] = {}
        for d in self._decisions:
            for agent in (d.from_agent, d.to_agent):
                if agent not in stats:
                    stats[agent] = {"count": 0, "total_confidence": 0.0}
                stats[agent]["count"] += 1
                stats[agent]["total_confidence"] += d.confidence
        result: Dict[str, Any] = {}
        for agent, data in stats.items():
            result[agent] = {
                "count": data["count"],
                "avg_confidence": data["total_confidence"] / data["count"] if data["count"] else 0.0,
            }
        return result
