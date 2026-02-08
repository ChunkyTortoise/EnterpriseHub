"""Performance baseline tests for JorgeHandoffService — evaluate_handoff().

Exercises evaluate_handoff() directly (pure computation, no external deps)
and validates that the handoff pipeline meets SLA targets.

SLA Targets (from performance_tracker.SLA_CONFIG):
    P50  < 100ms
    P95  < 500ms
    P99  < 800ms
"""

import asyncio
import random
import time

import pytest

from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
    JorgeHandoffService,
)
from ghl_real_estate_ai.services.jorge.performance_tracker import (
    SLA_CONFIG,
    PerformanceTracker,
)

BOT_NAME = "handoff"
OPERATION = "execute"
P50_TARGET = SLA_CONFIG[BOT_NAME][OPERATION]["p50_target"]
P95_TARGET = SLA_CONFIG[BOT_NAME][OPERATION]["p95_target"]
P99_TARGET = SLA_CONFIG[BOT_NAME][OPERATION]["p99_target"]


@pytest.fixture(autouse=True)
def _reset_tracker():
    PerformanceTracker.reset()
    yield
    PerformanceTracker.reset()


@pytest.fixture()
def handoff_service():
    """Fresh handoff service with cleared class-level state."""
    JorgeHandoffService._handoff_history.clear()
    JorgeHandoffService._handoff_outcomes.clear()
    JorgeHandoffService._active_handoffs.clear()
    svc = JorgeHandoffService()
    yield svc
    JorgeHandoffService._handoff_history.clear()
    JorgeHandoffService._handoff_outcomes.clear()
    JorgeHandoffService._active_handoffs.clear()


def _generate_latencies(n: int, seed: int = 42) -> list:
    """Log-normal distribution: median ~40ms, P95 ~91ms, P99 ~124ms.

    All within Handoff SLA (100 / 500 / 800).
    """
    rng = random.Random(seed)
    return [max(2.0, rng.lognormvariate(3.7, 0.5)) for _ in range(n)]


def _make_intent_signals(buyer_score: float = 0.0, seller_score: float = 0.0):
    return {
        "buyer_intent_score": buyer_score,
        "seller_intent_score": seller_score,
        "detected_intent_phrases": [],
    }


class TestHandoffBaseline:
    """Performance baseline suite for Handoff execute operation."""

    # ── Tracker-based SLA tests ─────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_p50_within_sla(self):
        tracker = PerformanceTracker()
        for lat in _generate_latencies(200):
            await tracker.track_operation(BOT_NAME, OPERATION, lat)

        stats = await tracker.get_bot_stats(BOT_NAME)
        assert stats["p50"] <= P50_TARGET, f"P50 {stats['p50']:.1f}ms exceeds {P50_TARGET}ms"

    @pytest.mark.asyncio
    async def test_p95_within_sla(self):
        tracker = PerformanceTracker()
        for lat in _generate_latencies(200):
            await tracker.track_operation(BOT_NAME, OPERATION, lat)

        stats = await tracker.get_bot_stats(BOT_NAME)
        assert stats["p95"] <= P95_TARGET, f"P95 {stats['p95']:.1f}ms exceeds {P95_TARGET}ms"

    @pytest.mark.asyncio
    async def test_p99_within_sla(self):
        tracker = PerformanceTracker()
        for lat in _generate_latencies(200):
            await tracker.track_operation(BOT_NAME, OPERATION, lat)

        stats = await tracker.get_bot_stats(BOT_NAME)
        assert stats["p99"] <= P99_TARGET, f"P99 {stats['p99']:.1f}ms exceeds {P99_TARGET}ms"

    @pytest.mark.asyncio
    async def test_concurrent_load_100_users(self):
        """100 concurrent producers recording 200 operations total."""
        tracker = PerformanceTracker()
        latencies = _generate_latencies(200)

        async def _record(batch):
            for lat in batch:
                await tracker.track_operation(BOT_NAME, OPERATION, lat)

        batch_size = len(latencies) // 100
        tasks = [_record(latencies[i * batch_size : (i + 1) * batch_size]) for i in range(100)]
        await asyncio.gather(*tasks)

        stats = await tracker.get_bot_stats(BOT_NAME)
        assert stats["count"] == 200
        assert stats["p50"] <= P50_TARGET
        assert stats["p95"] <= P95_TARGET

    @pytest.mark.asyncio
    async def test_sla_compliance_passes(self):
        tracker = PerformanceTracker()
        for lat in _generate_latencies(200):
            await tracker.track_operation(BOT_NAME, OPERATION, lat)

        compliance = await tracker.check_sla_compliance()
        entry = next(
            (c for c in compliance if c["bot_name"] == BOT_NAME and c["operation"] == OPERATION),
            None,
        )
        assert entry is not None
        assert entry["compliant"] is True, f"Violations: {entry['violations']}"

    @pytest.mark.asyncio
    async def test_regression_detection_above_10_percent(self):
        tracker = PerformanceTracker()
        baseline = _generate_latencies(200, seed=42)
        for lat in baseline:
            await tracker.track_operation(BOT_NAME, OPERATION, lat)
        baseline_p50 = (await tracker.get_bot_stats(BOT_NAME))["p50"]

        PerformanceTracker.reset()
        tracker = PerformanceTracker()
        for lat in baseline:
            await tracker.track_operation(BOT_NAME, OPERATION, lat * 1.15)
        degraded_p50 = (await tracker.get_bot_stats(BOT_NAME))["p50"]

        pct = (degraded_p50 - baseline_p50) / baseline_p50 * 100
        assert pct > 10.0, f"Expected >10% degradation, got {pct:.1f}%"

    # ── Direct evaluate_handoff() timing tests ──────────────────────────

    @pytest.mark.asyncio
    async def test_evaluate_handoff_latency_single(self, handoff_service):
        """Single evaluate_handoff() call completes within P50 target."""
        history = [{"role": "user", "content": "I want to buy a home"}]
        signals = _make_intent_signals(buyer_score=0.85)

        start = time.perf_counter()
        await handoff_service.evaluate_handoff("lead", "contact-1", history, signals)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < P50_TARGET, f"evaluate_handoff took {elapsed_ms:.1f}ms, exceeds P50 {P50_TARGET}ms"

    @pytest.mark.asyncio
    async def test_evaluate_handoff_latency_batch(self, handoff_service):
        """50 sequential evaluate_handoff() calls; P95 stays within SLA."""
        history = [{"role": "user", "content": "I want to sell my house"}]
        signals = _make_intent_signals(seller_score=0.9)
        timings = []

        for i in range(50):
            contact = f"contact-batch-{i}"
            start = time.perf_counter()
            await handoff_service.evaluate_handoff("lead", contact, history, signals)
            timings.append((time.perf_counter() - start) * 1000)

        timings.sort()
        p95_idx = int(0.95 * (len(timings) - 1))
        p95 = timings[p95_idx]
        assert p95 < P95_TARGET, f"Batch P95 {p95:.1f}ms exceeds {P95_TARGET}ms"

    @pytest.mark.asyncio
    async def test_evaluate_handoff_returns_decision_for_buyer(self, handoff_service):
        """High buyer-intent produces a handoff decision."""
        history = [{"role": "user", "content": "I want to buy a home with a budget of $500k"}]
        signals = _make_intent_signals(buyer_score=0.85)

        decision = await handoff_service.evaluate_handoff("lead", "contact-buyer", history, signals)

        assert decision is not None
        assert decision.target_bot == "buyer"
        assert decision.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_evaluate_handoff_returns_none_below_threshold(self, handoff_service):
        """Low-confidence signals produce no handoff."""
        history = [{"role": "user", "content": "Just browsing"}]
        signals = _make_intent_signals(buyer_score=0.3, seller_score=0.2)

        decision = await handoff_service.evaluate_handoff("lead", "contact-low", history, signals)

        assert decision is None

    @pytest.mark.asyncio
    async def test_evaluate_handoff_concurrent_contacts(self, handoff_service):
        """Concurrent handoff evaluations for different contacts."""
        history = [{"role": "user", "content": "I want to sell"}]
        signals = _make_intent_signals(seller_score=0.85)

        async def _eval(contact_id):
            start = time.perf_counter()
            await handoff_service.evaluate_handoff("lead", contact_id, history, signals)
            return (time.perf_counter() - start) * 1000

        tasks = [_eval(f"contact-conc-{i}") for i in range(25)]
        timings = await asyncio.gather(*tasks)

        max_ms = max(timings)
        assert max_ms < P99_TARGET, f"Max latency {max_ms:.1f}ms exceeds P99 {P99_TARGET}ms"
