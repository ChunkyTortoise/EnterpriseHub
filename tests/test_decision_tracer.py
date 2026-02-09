"""Tests for RAG Decision Tracer."""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "advanced_rag_system"))

from advanced_rag_system.src.agents.decision_tracer import (
    AgentRoutingLog,
    AnalysisResult,
    DecisionSpan,
    DecisionTracer,
    QualityTraceAnalyzer,
    RoutingDecision,
)

# ---------------------------------------------------------------------------
# DecisionSpan dataclass
# ---------------------------------------------------------------------------


class TestDecisionSpan:
    def test_create_basic(self):
        span = DecisionSpan(
            span_id="abc",
            parent_id=None,
            operation="retrieve",
            rationale="needed context",
            tool_chosen="vector_search",
            alternatives=["web_search"],
            confidence=0.9,
            start_time=1000.0,
        )
        assert span.span_id == "abc"
        assert span.end_time is None
        assert span.metadata == {}
        assert span.alternatives == ["web_search"]

    def test_with_metadata(self):
        span = DecisionSpan(
            span_id="x",
            parent_id="p",
            operation="op",
            rationale="r",
            tool_chosen=None,
            alternatives=[],
            confidence=0.5,
            start_time=0.0,
            metadata={"key": "val"},
        )
        assert span.metadata == {"key": "val"}
        assert span.parent_id == "p"


# ---------------------------------------------------------------------------
# DecisionTracer
# ---------------------------------------------------------------------------


class TestDecisionTracer:
    def test_trace_id_unique(self):
        t1 = DecisionTracer()
        t2 = DecisionTracer()
        assert t1.trace_id != t2.trace_id

    def test_start_span(self):
        tracer = DecisionTracer()
        span = tracer.start_span("retrieve", "need docs", confidence=0.8)
        assert span.operation == "retrieve"
        assert span.parent_id is None
        assert span.confidence == 0.8
        assert span.end_time is None

    def test_end_span(self):
        tracer = DecisionTracer()
        span = tracer.start_span("op", "r")
        ended = tracer.end_span(span.span_id)
        assert ended.end_time is not None
        assert ended.end_time >= ended.start_time

    def test_get_trace_order(self):
        tracer = DecisionTracer()
        s1 = tracer.start_span("a", "r1")
        s2 = tracer.start_span("b", "r2")
        s3 = tracer.start_span("c", "r3")
        trace = tracer.get_trace()
        assert [s.span_id for s in trace] == [s1.span_id, s2.span_id, s3.span_id]

    def test_get_children(self):
        tracer = DecisionTracer()
        parent = tracer.start_span("root", "start")
        child1 = tracer.start_span("step1", "r", parent_id=parent.span_id)
        child2 = tracer.start_span("step2", "r", parent_id=parent.span_id)
        _other = tracer.start_span("unrelated", "r")
        children = tracer.get_children(parent.span_id)
        assert len(children) == 2
        ids = {c.span_id for c in children}
        assert child1.span_id in ids
        assert child2.span_id in ids

    def test_get_children_empty(self):
        tracer = DecisionTracer()
        s = tracer.start_span("leaf", "r")
        assert tracer.get_children(s.span_id) == []

    def test_get_critical_path_linear(self):
        tracer = DecisionTracer()
        s1 = tracer.start_span("a", "r")
        s2 = tracer.start_span("b", "r", parent_id=s1.span_id)
        s3 = tracer.start_span("c", "r", parent_id=s2.span_id)
        path = tracer.get_critical_path()
        assert [s.span_id for s in path] == [s1.span_id, s2.span_id, s3.span_id]

    def test_get_critical_path_branching(self):
        tracer = DecisionTracer()
        root = tracer.start_span("root", "r")
        left = tracer.start_span("left", "r", parent_id=root.span_id)
        right = tracer.start_span("right", "r", parent_id=root.span_id)
        right_child = tracer.start_span("right_child", "r", parent_id=right.span_id)
        path = tracer.get_critical_path()
        # Longest path is root -> right -> right_child (depth 3)
        assert len(path) == 3
        assert path[0].span_id == root.span_id
        assert path[-1].span_id == right_child.span_id

    def test_get_critical_path_empty(self):
        tracer = DecisionTracer()
        assert tracer.get_critical_path() == []

    def test_reset(self):
        tracer = DecisionTracer()
        old_id = tracer.trace_id
        tracer.start_span("op", "r")
        tracer.reset()
        assert tracer.trace_id != old_id
        assert tracer.get_trace() == []

    def test_start_span_with_tool_and_alternatives(self):
        tracer = DecisionTracer()
        span = tracer.start_span(
            "select_tool",
            "best retriever",
            tool_chosen="bm25",
            alternatives=["tfidf", "dense"],
        )
        assert span.tool_chosen == "bm25"
        assert span.alternatives == ["tfidf", "dense"]


# ---------------------------------------------------------------------------
# QualityTraceAnalyzer
# ---------------------------------------------------------------------------


class TestQualityTraceAnalyzer:
    def _make_spans(self) -> list[DecisionSpan]:
        """Create 3 spans with known latencies."""
        spans = []
        for i, (op, dur) in enumerate([("a", 0.1), ("b", 0.3), ("c", 0.1)]):
            s = DecisionSpan(
                span_id=f"s{i}",
                parent_id=None,
                operation=op,
                rationale="r",
                tool_chosen=None,
                alternatives=[],
                confidence=0.5 + i * 0.2,
                start_time=1000.0,
                end_time=1000.0 + dur,
            )
            spans.append(s)
        return spans

    def test_analyze(self):
        analyzer = QualityTraceAnalyzer()
        spans = self._make_spans()
        quality = {spans[0].span_id: 0.8, spans[1].span_id: 0.6}
        results = analyzer.analyze(spans, quality)
        assert len(results) == 3
        assert results[0].quality_score == 0.8
        assert results[2].quality_score == 0.0  # not in quality_scores

    def test_analyze_cost_contributions_sum_to_one(self):
        analyzer = QualityTraceAnalyzer()
        spans = self._make_spans()
        results = analyzer.analyze(spans, {})
        total_frac = sum(r.cost_contribution for r in results)
        assert abs(total_frac - 1.0) < 1e-6

    def test_identify_bottlenecks(self):
        analyzer = QualityTraceAnalyzer()
        spans = self._make_spans()
        bottlenecks = analyzer.identify_bottlenecks(spans, top_n=1)
        assert len(bottlenecks) == 1
        assert bottlenecks[0].operation == "b"  # 0.3s is longest

    def test_identify_low_confidence(self):
        analyzer = QualityTraceAnalyzer()
        spans = self._make_spans()
        # confidences: 0.5, 0.7, 0.9
        low = analyzer.identify_low_confidence(spans, threshold=0.6)
        assert len(low) == 1
        assert low[0].confidence == 0.5

    def test_identify_low_confidence_none(self):
        analyzer = QualityTraceAnalyzer()
        spans = self._make_spans()
        low = analyzer.identify_low_confidence(spans, threshold=0.1)
        assert low == []

    def test_bottlenecks_with_unfinished_spans(self):
        analyzer = QualityTraceAnalyzer()
        s = DecisionSpan(
            span_id="u",
            parent_id=None,
            operation="pending",
            rationale="r",
            tool_chosen=None,
            alternatives=[],
            confidence=1.0,
            start_time=1000.0,
            end_time=None,
        )
        bottlenecks = analyzer.identify_bottlenecks([s], top_n=1)
        assert len(bottlenecks) == 1


# ---------------------------------------------------------------------------
# AgentRoutingLog
# ---------------------------------------------------------------------------


class TestAgentRoutingLog:
    def test_log_routing(self):
        log = AgentRoutingLog()
        rd = log.log_routing("lead_bot", "buyer_bot", "buyer intent detected", 0.85)
        assert isinstance(rd, RoutingDecision)
        assert rd.from_agent == "lead_bot"
        assert rd.to_agent == "buyer_bot"

    def test_get_routing_history(self):
        log = AgentRoutingLog()
        log.log_routing("lead", "buyer", "intent", 0.9)
        log.log_routing("buyer", "seller", "switch", 0.7)
        log.log_routing("other", "other2", "test", 0.5)
        history = log.get_routing_history("buyer")
        assert len(history) == 2  # buyer appears as to_agent and from_agent

    def test_get_routing_history_empty(self):
        log = AgentRoutingLog()
        assert log.get_routing_history("nobody") == []

    def test_get_routing_stats(self):
        log = AgentRoutingLog()
        log.log_routing("a", "b", "r", 0.8)
        log.log_routing("a", "c", "r", 0.6)
        stats = log.get_routing_stats()
        assert stats["a"]["count"] == 2
        assert abs(stats["a"]["avg_confidence"] - 0.7) < 1e-9
        assert stats["b"]["count"] == 1
        assert stats["c"]["count"] == 1

    def test_get_routing_stats_empty(self):
        log = AgentRoutingLog()
        assert log.get_routing_stats() == {}

    def test_routing_with_context(self):
        log = AgentRoutingLog()
        rd = log.log_routing("a", "b", "reason", 0.9, context="user asked about buying")
        assert rd.context_summary == "user asked about buying"


# ---------------------------------------------------------------------------
# AnalysisResult dataclass
# ---------------------------------------------------------------------------


class TestAnalysisResult:
    def test_create(self):
        ar = AnalysisResult(
            span_id="s1",
            quality_score=0.85,
            cost_contribution=0.3,
            latency_contribution=150.0,
        )
        assert ar.span_id == "s1"
        assert ar.quality_score == 0.85


# ---------------------------------------------------------------------------
# RoutingDecision dataclass
# ---------------------------------------------------------------------------


class TestRoutingDecision:
    def test_create(self):
        rd = RoutingDecision(
            from_agent="a",
            to_agent="b",
            reason="test",
            confidence=0.5,
            timestamp=1000.0,
            context_summary="ctx",
        )
        assert rd.from_agent == "a"
        assert rd.context_summary == "ctx"
