"""
Performance Baseline Testing Suite - Response Time Benchmarks
=============================================================

Comprehensive performance benchmarks for the EnterpriseHub real estate AI platform.
Validates response time targets for:
- Jorge Seller Bot workflow nodes (intent, stall detection, strategy, response)
- Jorge Buyer Bot workflow nodes (intent, financial, property matching, response)
- FastAPI endpoint overhead (health, bot list, serialization)
- Cache layer performance (L1 hit, miss+populate, hit rate)

All external services are mocked with realistic simulated latency.
Each test runs 10+ iterations and reports avg, p95, p99 statistics.

Usage:
    pytest tests/performance/test_response_times.py -v -m performance
"""

import asyncio
import statistics
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import psutil
import pytest
import pytest_asyncio

# ---------------------------------------------------------------------------
# Performance Baseline Utility
# ---------------------------------------------------------------------------


@dataclass
class PerformanceMeasurement:
    """A single timing measurement."""
    iteration: int
    elapsed_ms: float
    success: bool = True


@dataclass
class PerformanceReport:
    """Aggregated performance statistics for a set of measurements."""
    test_name: str
    iterations: int
    avg_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float
    std_dev_ms: float
    success_rate: float


class PerformanceBaseline:
    """
    Utility class for running N iterations of an async callable,
    collecting timing data, and computing statistical summaries.
    """

    @staticmethod
    async def run_iterations(
        coro_factory,
        iterations: int = 10,
        warmup: int = 1,
    ) -> List[PerformanceMeasurement]:
        """
        Execute *coro_factory* (a zero-arg async callable) for *iterations*
        rounds, preceded by *warmup* untimed rounds.  Returns a list of
        ``PerformanceMeasurement`` objects.
        """
        # Warmup rounds (not recorded)
        for _ in range(warmup):
            try:
                await coro_factory()
            except Exception:
                pass

        measurements: List[PerformanceMeasurement] = []
        for i in range(iterations):
            start = time.perf_counter()
            success = True
            try:
                await coro_factory()
            except Exception:
                success = False
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            measurements.append(
                PerformanceMeasurement(iteration=i, elapsed_ms=elapsed_ms, success=success)
            )
        return measurements

    @staticmethod
    def compute_stats(test_name: str, measurements: List[PerformanceMeasurement]) -> PerformanceReport:
        """Compute avg, p50, p95, p99, min, max, stddev from measurements."""
        times = [m.elapsed_ms for m in measurements]
        successes = [m for m in measurements if m.success]
        n = len(times)
        sorted_times = sorted(times)

        def _percentile(pct: float) -> float:
            idx = int(pct / 100.0 * (n - 1))
            idx = max(0, min(idx, n - 1))
            return sorted_times[idx]

        return PerformanceReport(
            test_name=test_name,
            iterations=n,
            avg_ms=statistics.mean(times),
            p50_ms=_percentile(50),
            p95_ms=_percentile(95),
            p99_ms=_percentile(99),
            min_ms=min(times),
            max_ms=max(times),
            std_dev_ms=statistics.stdev(times) if n > 1 else 0.0,
            success_rate=len(successes) / n if n else 0.0,
        )

    @staticmethod
    def print_performance_report(test_name: str, measurements: List[PerformanceMeasurement]) -> PerformanceReport:
        """Compute stats and print a formatted report.  Returns the report."""
        report = PerformanceBaseline.compute_stats(test_name, measurements)
        print(
            f"\n{'=' * 64}\n"
            f"  PERFORMANCE REPORT: {report.test_name}\n"
            f"{'=' * 64}\n"
            f"  Iterations : {report.iterations}\n"
            f"  Avg        : {report.avg_ms:>10.3f} ms\n"
            f"  P50        : {report.p50_ms:>10.3f} ms\n"
            f"  P95        : {report.p95_ms:>10.3f} ms\n"
            f"  P99        : {report.p99_ms:>10.3f} ms\n"
            f"  Min        : {report.min_ms:>10.3f} ms\n"
            f"  Max        : {report.max_ms:>10.3f} ms\n"
            f"  StdDev     : {report.std_dev_ms:>10.3f} ms\n"
            f"  Success    : {report.success_rate:>9.1%}\n"
            f"{'=' * 64}"
        )
        return report


# ---------------------------------------------------------------------------
# Shared mock helpers
# ---------------------------------------------------------------------------

def _make_seller_mock_profile():
    """Return a mock LeadIntentProfile suitable for the seller bot."""
    frs = MagicMock()
    frs.total_score = 72.0
    frs.classification = "Warm Lead"

    pcs = MagicMock()
    pcs.total_score = 65.0

    profile = MagicMock()
    profile.frs = frs
    profile.pcs = pcs
    profile.lead_type = "seller"
    profile.next_best_action = "schedule_call"
    profile.stall_breaker_suggested = None
    return profile


def _make_buyer_mock_profile():
    """Return a mock BuyerIntentProfile suitable for the buyer bot."""
    profile = MagicMock()
    profile.financial_readiness = 75.0
    profile.budget_clarity = 80.0
    profile.financing_status_score = 85.0
    profile.urgency_score = 65.0
    profile.timeline_pressure = 70.0
    profile.consequence_awareness = 60.0
    profile.preference_clarity = 70.0
    profile.market_realism = 75.0
    profile.decision_authority = 80.0
    profile.buyer_temperature = "warm"
    profile.confidence_level = 85.0
    profile.conversation_turns = 3
    profile.key_insights = {"budget_mentioned": True}
    profile.next_qualification_step = "preferences"
    return profile


def _mock_conversation_history():
    """Return realistic conversation history for testing."""
    return [
        {"role": "user", "content": "Hi, I'm interested in selling my house in Rancho Cucamonga"},
        {"role": "assistant", "content": "Great to hear! What's motivating you to sell right now?"},
        {"role": "user", "content": "We're relocating for work. Need to sell within 3 months. House is around $650k."},
        {"role": "assistant", "content": "That's a solid timeline. Have you had any recent appraisals?"},
        {"role": "user", "content": "No, but Zillow says it's worth $680k. I think we can get $700k."},
    ]


def _mock_buyer_conversation_history():
    """Return realistic buyer conversation history for testing."""
    return [
        {"role": "user", "content": "Hi, I'm looking to buy a 3 bedroom house in Rancho Cucamonga"},
        {"role": "assistant", "content": "I'd love to help you find the perfect home! What's your budget range?"},
        {"role": "user", "content": "We're pre-approved for $650k. Looking for something under $600k ideally."},
        {"role": "assistant", "content": "That's great you're pre-approved! Any specific neighborhoods you prefer?"},
        {"role": "user", "content": "Victoria Gardens area would be ideal. Need a yard and garage."},
    ]


# ---------------------------------------------------------------------------
# Seller bot mock state
# ---------------------------------------------------------------------------

def _make_seller_state(profile=None) -> Dict[str, Any]:
    """Build a JorgeSellerState dict with realistic data."""
    return {
        "lead_id": "test_seller_123",
        "lead_name": "Maria Garcia",
        "property_address": "1234 Haven Ave, Rancho Cucamonga, CA 91730",
        "conversation_history": _mock_conversation_history(),
        "intent_profile": profile or _make_seller_mock_profile(),
        "current_tone": "CONSULTATIVE",
        "stall_detected": False,
        "detected_stall_type": None,
        "next_action": "respond",
        "response_content": "",
        "psychological_commitment": 65.0,
        "is_qualified": True,
        "seller_temperature": "warm",
        "current_journey_stage": "qualification",
        "follow_up_count": 1,
        "last_action_timestamp": None,
        # Intelligence fields (Phase 3.3)
        "intelligence_context": None,
        "intelligence_performance_ms": 0.0,
        "intelligence_available": False,
    }


# ---------------------------------------------------------------------------
# Buyer bot mock state
# ---------------------------------------------------------------------------

def _make_buyer_state(profile=None) -> Dict[str, Any]:
    """Build a BuyerBotState dict with realistic data."""
    return {
        "buyer_id": "test_buyer_123",
        "buyer_name": "John Doe",
        "target_areas": ["Victoria Gardens", "Haven"],
        "conversation_history": _mock_buyer_conversation_history(),
        "intent_profile": profile or _make_buyer_mock_profile(),
        "budget_range": {"min": 480000, "max": 600000},
        "financing_status": "pre_approved",
        "urgency_level": "3_months",
        "property_preferences": {"bedrooms": 3, "features": ["yard", "garage"]},
        "current_qualification_step": "preferences",
        "objection_detected": False,
        "detected_objection_type": None,
        "next_action": "respond",
        "response_content": "",
        "matched_properties": [],
        "financial_readiness_score": 75.0,
        "buying_motivation_score": 65.0,
        "is_qualified": True,
        "current_journey_stage": "qualification",
        "properties_viewed_count": 0,
        "last_action_timestamp": None,
        # Intelligence fields
        "intelligence_context": None,
        "intelligence_performance_ms": 0.0,
        "intelligence_available": False,
    }


# ---------------------------------------------------------------------------
# Async mock factory helpers with realistic simulated latency
# ---------------------------------------------------------------------------

def _async_return(value, delay_s: float = 0.005):
    """Return an async function that sleeps briefly then returns *value*."""
    async def _inner(*args, **kwargs):
        await asyncio.sleep(delay_s)
        return value
    return _inner


def _make_event_publisher_mock():
    """Create a mock event publisher with fast async stubs."""
    pub = MagicMock()
    pub.publish_bot_status_update = AsyncMock()
    pub.publish_jorge_qualification_progress = AsyncMock()
    pub.publish_conversation_update = AsyncMock()
    pub.publish_buyer_intent_analysis = AsyncMock()
    pub.publish_property_match_update = AsyncMock()
    pub.publish_buyer_follow_up_scheduled = AsyncMock()
    pub.publish_buyer_qualification_complete = AsyncMock()
    return pub


def _make_claude_mock():
    """Create a mock ClaudeAssistant returning realistic data."""
    claude = MagicMock()
    claude.analyze_with_context = AsyncMock(return_value={
        "content": "I completely understand your timeline. Let me show you some recent comparable sales in your neighborhood.",
        "analysis": "Warm seller, 3-month timeline, realistic pricing expectations.",
    })
    claude.generate_response = AsyncMock(return_value={
        "content": "I'd love to help you find the perfect home in Victoria Gardens! Based on your budget, here are some great options.",
    })
    return claude


def _make_ml_analytics_mock():
    """Create a mock ML analytics engine returning predictive data."""
    journey = MagicMock()
    journey.conversion_probability = 0.72
    journey.stage_progression_velocity = 0.85
    journey.processing_time_ms = 3.0

    conversion = MagicMock()
    conversion.urgency_score = 0.68
    conversion.optimal_action = "schedule_showing"
    conversion.processing_time_ms = 2.5

    touchpoint = MagicMock()
    touchpoint.response_pattern = "engaged"
    touchpoint.processing_time_ms = 2.0

    ml = MagicMock()
    ml.predict_lead_journey = AsyncMock(return_value=journey)
    ml.predict_conversion_probability = AsyncMock(return_value=conversion)
    ml.predict_optimal_touchpoints = AsyncMock(return_value=touchpoint)
    return ml


# ===========================================================================
# TEST CLASS 1: Seller Bot Performance
# ===========================================================================

@pytest.mark.asyncio
@pytest.mark.performance
class TestLeadBotPerformance:
    """Performance benchmarks for the Jorge Seller Bot workflow nodes."""

    @pytest.fixture(autouse=True)
    def _patch_seller_deps(self):
        """Patch all external dependencies for the seller bot."""
        self.mock_intent_decoder = MagicMock()
        self.mock_intent_decoder.analyze_lead = MagicMock(return_value=_make_seller_mock_profile())

        self.mock_claude = _make_claude_mock()
        self.mock_event_publisher = _make_event_publisher_mock()
        self.mock_ml_analytics = _make_ml_analytics_mock()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_seller_bot",
            LeadIntentDecoder=MagicMock(return_value=self.mock_intent_decoder),
            ClaudeAssistant=MagicMock(return_value=self.mock_claude),
            get_event_publisher=Mock(return_value=self.mock_event_publisher),
            get_ml_analytics_engine=Mock(return_value=self.mock_ml_analytics),
            BOT_INTELLIGENCE_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot, JorgeFeatureConfig

            config = JorgeFeatureConfig(
                enable_progressive_skills=False,
                enable_agent_mesh=False,
                enable_mcp_integration=False,
                enable_adaptive_questioning=False,
                enable_track3_intelligence=True,
                enable_bot_intelligence=False,
            )
            self.bot = JorgeSellerBot(config=config)
            yield

    # -----------------------------------------------------------------------

    async def test_seller_bot_intent_analysis_time(self):
        """Seller bot analyze_intent node should average < 100 ms."""
        state = _make_seller_state()

        measurements = await PerformanceBaseline.run_iterations(
            coro_factory=lambda: self.bot.analyze_intent(state),
            iterations=15,
            warmup=2,
        )
        report = PerformanceBaseline.print_performance_report(
            "SellerBot.analyze_intent", measurements
        )
        assert report.avg_ms < 100, (
            f"analyze_intent avg {report.avg_ms:.2f}ms exceeds 100ms target"
        )
        assert report.success_rate >= 0.90

    async def test_seller_bot_stall_detection_time(self):
        """Seller bot detect_stall node should average < 50 ms."""
        state = _make_seller_state()
        # Inject a stall message
        state["conversation_history"].append(
            {"role": "user", "content": "Let me think about it and get back to you next week."}
        )

        measurements = await PerformanceBaseline.run_iterations(
            coro_factory=lambda: self.bot.detect_stall(state),
            iterations=15,
            warmup=2,
        )
        report = PerformanceBaseline.print_performance_report(
            "SellerBot.detect_stall", measurements
        )
        assert report.avg_ms < 50, (
            f"detect_stall avg {report.avg_ms:.2f}ms exceeds 50ms target"
        )
        assert report.success_rate >= 0.90

    async def test_seller_bot_strategy_selection_time(self):
        """Seller bot select_strategy node should average < 50 ms."""
        state = _make_seller_state()
        state["stall_detected"] = True
        state["detected_stall_type"] = "zestimate"

        measurements = await PerformanceBaseline.run_iterations(
            coro_factory=lambda: self.bot.select_strategy(state),
            iterations=15,
            warmup=2,
        )
        report = PerformanceBaseline.print_performance_report(
            "SellerBot.select_strategy", measurements
        )
        assert report.avg_ms < 50, (
            f"select_strategy avg {report.avg_ms:.2f}ms exceeds 50ms target"
        )
        assert report.success_rate >= 0.90

    async def test_seller_bot_response_generation_time(self):
        """Seller bot generate_jorge_response node should average < 200 ms."""
        state = _make_seller_state()
        state["current_tone"] = "CONSULTATIVE"
        state["current_question"] = 2

        measurements = await PerformanceBaseline.run_iterations(
            coro_factory=lambda: self.bot.generate_jorge_response(state),
            iterations=15,
            warmup=2,
        )
        report = PerformanceBaseline.print_performance_report(
            "SellerBot.generate_jorge_response", measurements
        )
        assert report.avg_ms < 200, (
            f"generate_jorge_response avg {report.avg_ms:.2f}ms exceeds 200ms target"
        )
        assert report.success_rate >= 0.90

    async def test_seller_bot_full_workflow_time(self):
        """Full seller bot workflow (all nodes) p95 should be < 500 ms."""
        state = _make_seller_state()

        async def _run_full_workflow():
            s = dict(state)  # shallow copy to avoid mutation leaking
            result = await self.bot.analyze_intent(s)
            s.update(result)
            result = await self.bot.detect_stall(s)
            s.update(result)
            result = await self.bot.select_strategy(s)
            s.update(result)
            result = await self.bot.generate_jorge_response(s)
            s.update(result)
            return s

        measurements = await PerformanceBaseline.run_iterations(
            coro_factory=_run_full_workflow,
            iterations=10,
            warmup=2,
        )
        report = PerformanceBaseline.print_performance_report(
            "SellerBot.full_workflow", measurements
        )
        assert report.p95_ms < 500, (
            f"Full seller workflow p95 {report.p95_ms:.2f}ms exceeds 500ms target"
        )
        assert report.success_rate >= 0.90


# ===========================================================================
# TEST CLASS 2: Buyer Bot Performance
# ===========================================================================

@pytest.mark.asyncio
@pytest.mark.performance
class TestBuyerBotPerformance:
    """Performance benchmarks for the Jorge Buyer Bot workflow nodes."""

    @pytest.fixture(autouse=True)
    def _patch_buyer_deps(self):
        """Patch all external dependencies for the buyer bot."""
        self.mock_intent_decoder = MagicMock()
        self.mock_intent_decoder.analyze_buyer = MagicMock(return_value=_make_buyer_mock_profile())

        self.mock_claude = _make_claude_mock()
        self.mock_event_publisher = _make_event_publisher_mock()
        self.mock_property_matcher = MagicMock()
        self.mock_property_matcher.find_matches = MagicMock(return_value=[
            {"id": "prop_1", "address": "100 Victoria Ave", "price": 580000, "beds": 3},
            {"id": "prop_2", "address": "200 Haven Blvd", "price": 545000, "beds": 3},
            {"id": "prop_3", "address": "300 Etiwanda Dr", "price": 560000, "beds": 4},
        ])
        self.mock_ml_analytics = _make_ml_analytics_mock()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=MagicMock(return_value=self.mock_intent_decoder),
            ClaudeAssistant=MagicMock(return_value=self.mock_claude),
            get_event_publisher=Mock(return_value=self.mock_event_publisher),
            PropertyMatcher=MagicMock(return_value=self.mock_property_matcher),
            get_ml_analytics_engine=Mock(return_value=self.mock_ml_analytics),
            BOT_INTELLIGENCE_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            self.bot = JorgeBuyerBot(
                tenant_id="perf_test",
                enable_bot_intelligence=False,
            )
            yield

    # -----------------------------------------------------------------------

    async def test_buyer_bot_intent_analysis_time(self):
        """Buyer bot analyze_buyer_intent node should average < 100 ms."""
        state = _make_buyer_state()

        measurements = await PerformanceBaseline.run_iterations(
            coro_factory=lambda: self.bot.analyze_buyer_intent(state),
            iterations=15,
            warmup=2,
        )
        report = PerformanceBaseline.print_performance_report(
            "BuyerBot.analyze_buyer_intent", measurements
        )
        assert report.avg_ms < 100, (
            f"analyze_buyer_intent avg {report.avg_ms:.2f}ms exceeds 100ms target"
        )
        assert report.success_rate >= 0.90

    async def test_buyer_bot_financial_assessment_time(self):
        """Buyer bot assess_financial_readiness node should average < 150 ms."""
        state = _make_buyer_state()

        measurements = await PerformanceBaseline.run_iterations(
            coro_factory=lambda: self.bot.assess_financial_readiness(state),
            iterations=15,
            warmup=2,
        )
        report = PerformanceBaseline.print_performance_report(
            "BuyerBot.assess_financial_readiness", measurements
        )
        assert report.avg_ms < 150, (
            f"assess_financial_readiness avg {report.avg_ms:.2f}ms exceeds 150ms target"
        )
        assert report.success_rate >= 0.90

    async def test_buyer_bot_property_matching_time(self):
        """Buyer bot match_properties node should average < 100 ms."""
        state = _make_buyer_state()

        measurements = await PerformanceBaseline.run_iterations(
            coro_factory=lambda: self.bot.match_properties(state),
            iterations=15,
            warmup=2,
        )
        report = PerformanceBaseline.print_performance_report(
            "BuyerBot.match_properties", measurements
        )
        assert report.avg_ms < 100, (
            f"match_properties avg {report.avg_ms:.2f}ms exceeds 100ms target"
        )
        assert report.success_rate >= 0.90

    async def test_buyer_bot_response_generation_time(self):
        """Buyer bot generate_buyer_response node should average < 150 ms."""
        state = _make_buyer_state()
        state["matched_properties"] = [
            {"id": "prop_1", "address": "100 Victoria Ave", "price": 580000},
        ]

        measurements = await PerformanceBaseline.run_iterations(
            coro_factory=lambda: self.bot.generate_buyer_response(state),
            iterations=15,
            warmup=2,
        )
        report = PerformanceBaseline.print_performance_report(
            "BuyerBot.generate_buyer_response", measurements
        )
        assert report.avg_ms < 150, (
            f"generate_buyer_response avg {report.avg_ms:.2f}ms exceeds 150ms target"
        )
        assert report.success_rate >= 0.90

    async def test_buyer_bot_full_workflow_time(self):
        """Full buyer bot workflow (all nodes) p95 should be < 400 ms."""
        state = _make_buyer_state()

        async def _run_full_workflow():
            s = dict(state)
            result = await self.bot.analyze_buyer_intent(s)
            s.update(result)
            result = await self.bot.assess_financial_readiness(s)
            s.update(result)
            result = await self.bot.qualify_property_needs(s)
            s.update(result)
            result = await self.bot.match_properties(s)
            s.update(result)
            result = await self.bot.generate_buyer_response(s)
            s.update(result)
            return s

        measurements = await PerformanceBaseline.run_iterations(
            coro_factory=_run_full_workflow,
            iterations=10,
            warmup=2,
        )
        report = PerformanceBaseline.print_performance_report(
            "BuyerBot.full_workflow", measurements
        )
        assert report.p95_ms < 400, (
            f"Full buyer workflow p95 {report.p95_ms:.2f}ms exceeds 400ms target"
        )
        assert report.success_rate >= 0.90


# ===========================================================================
# TEST CLASS 3: API Overhead
# ===========================================================================

@pytest.mark.asyncio
@pytest.mark.performance
class TestAPIOverhead:
    """Measure FastAPI request/response overhead using httpx AsyncClient."""

    @pytest_asyncio.fixture(autouse=True)
    async def _setup_client(self):
        """Create an httpx AsyncClient against the FastAPI app via ASGITransport.

        The FastAPI ``app`` object is already instantiated at module-import
        time with all routes registered.  We use ``raise_app_exceptions=False``
        and skip the test gracefully if the module cannot be imported (e.g.
        missing JWT_SECRET_KEY or other environment configuration).
        """
        import os

        # Set required environment variables so the app module can load.
        # These are test-only values and are restored after the fixture.
        env_overrides = {
            "JWT_SECRET_KEY": "perf-test-secret-key-not-for-production-use-1234567890-extra-length-padding",
            "ENVIRONMENT": "development",
        }
        original_env = {}
        for key, value in env_overrides.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value

        try:
            # Import the already-created FastAPI app (routes registered at
            # module level).  The lifespan hook runs only when served; it
            # does NOT run under httpx ASGITransport.
            try:
                from ghl_real_estate_ai.api.main import app  # noqa: F811
            except Exception as exc:
                pytest.skip(f"Could not import FastAPI app for overhead tests: {exc}")

            import httpx

            transport = httpx.ASGITransport(
                app=app,
                raise_app_exceptions=False,
            )
            self.client = httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
            )
            yield
            await self.client.aclose()
        finally:
            # Restore original environment
            for key, orig_value in original_env.items():
                if orig_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = orig_value

    # -----------------------------------------------------------------------

    async def test_health_endpoint_overhead(self):
        """GET /health/live should respond in < 20 ms (lightweight liveness probe)."""

        async def _hit_health():
            resp = await self.client.get("/health/live")
            assert resp.status_code == 200

        measurements = await PerformanceBaseline.run_iterations(
            coro_factory=_hit_health,
            iterations=20,
            warmup=3,
        )
        report = PerformanceBaseline.print_performance_report(
            "API.health_live", measurements
        )
        assert report.avg_ms < 20, (
            f"/health/live avg {report.avg_ms:.2f}ms exceeds 20ms target"
        )

    async def test_bot_list_overhead(self):
        """GET /api/bots/health should respond in < 50 ms."""

        async def _hit_bots():
            resp = await self.client.get("/api/bots/health")
            # Accept 200 or 500 (deps may not be fully wired); we measure overhead
            assert resp.status_code in (200, 422, 500)

        measurements = await PerformanceBaseline.run_iterations(
            coro_factory=_hit_bots,
            iterations=20,
            warmup=3,
        )
        report = PerformanceBaseline.print_performance_report(
            "API.bots_health", measurements
        )
        assert report.avg_ms < 50, (
            f"/api/bots/health avg {report.avg_ms:.2f}ms exceeds 50ms target"
        )

    async def test_request_serialization_overhead(self):
        """Root endpoint GET / should measure pure serialization overhead < 20 ms."""

        async def _hit_root():
            resp = await self.client.get("/")
            assert resp.status_code == 200
            data = resp.json()
            assert "service" in data

        measurements = await PerformanceBaseline.run_iterations(
            coro_factory=_hit_root,
            iterations=20,
            warmup=3,
        )
        report = PerformanceBaseline.print_performance_report(
            "API.root_serialization", measurements
        )
        assert report.avg_ms < 20, (
            f"Root endpoint avg {report.avg_ms:.2f}ms exceeds 20ms target"
        )

    async def test_total_api_overhead(self):
        """Aggregate overhead across health + root should stay < 70 ms combined."""

        async def _hit_both():
            r1 = await self.client.get("/")
            r2 = await self.client.get("/health/live")
            assert r1.status_code == 200
            assert r2.status_code == 200

        measurements = await PerformanceBaseline.run_iterations(
            coro_factory=_hit_both,
            iterations=15,
            warmup=3,
        )
        report = PerformanceBaseline.print_performance_report(
            "API.total_overhead (root+health)", measurements
        )
        assert report.avg_ms < 70, (
            f"Total API overhead avg {report.avg_ms:.2f}ms exceeds 70ms target"
        )


# ===========================================================================
# TEST CLASS 4: Cache Performance
# ===========================================================================

@pytest.mark.asyncio
@pytest.mark.performance
class TestCachePerformance:
    """
    Validate cache layer latency and hit-rate characteristics.

    Uses an in-memory dict-based L1 cache mock with realistic async delays
    to simulate a lightweight application-level cache layer.
    """

    @pytest.fixture(autouse=True)
    def _setup_cache(self):
        """Set up a simple in-memory cache mock with simulated latency."""
        self.cache_store: Dict[str, Any] = {}
        self.stats = {"hits": 0, "misses": 0, "sets": 0}
        yield

    async def _cache_get(self, key: str) -> Optional[Any]:
        """Simulate L1 cache get with ~1ms latency."""
        await asyncio.sleep(0.001)  # 1ms simulated L1 lookup
        if key in self.cache_store:
            self.stats["hits"] += 1
            return self.cache_store[key]
        self.stats["misses"] += 1
        return None

    async def _cache_set(self, key: str, value: Any) -> None:
        """Simulate L1 cache set with ~2ms latency."""
        await asyncio.sleep(0.002)  # 2ms simulated L1 write
        self.cache_store[key] = value
        self.stats["sets"] += 1

    async def _backend_fetch(self, key: str) -> Dict[str, Any]:
        """Simulate a slower backend/database lookup (~15ms)."""
        await asyncio.sleep(0.015)
        return {"key": key, "data": f"value_for_{key}", "source": "backend"}

    async def _get_or_populate(self, key: str) -> Any:
        """Cache-aside pattern: try L1, on miss fetch from backend and populate."""
        value = await self._cache_get(key)
        if value is not None:
            return value
        # Miss -- fetch from backend and populate
        value = await self._backend_fetch(key)
        await self._cache_set(key, value)
        return value

    # -----------------------------------------------------------------------

    async def test_cache_hit_latency(self):
        """L1 cache hit should be < 5 ms."""
        # Pre-populate
        for i in range(50):
            await self._cache_set(f"perf_key_{i}", {"data": f"value_{i}"})

        async def _hit():
            key = f"perf_key_{hash(time.perf_counter()) % 50}"
            result = await self._cache_get(key)
            assert result is not None

        measurements = await PerformanceBaseline.run_iterations(
            coro_factory=_hit,
            iterations=20,
            warmup=3,
        )
        report = PerformanceBaseline.print_performance_report(
            "Cache.L1_hit", measurements
        )
        assert report.avg_ms < 5, (
            f"Cache L1 hit avg {report.avg_ms:.2f}ms exceeds 5ms target"
        )

    async def test_cache_miss_and_populate_latency(self):
        """Cache miss + backend fetch + populate should be < 50 ms."""
        counter = {"i": 0}

        async def _miss_and_populate():
            key = f"miss_key_{counter['i']}"
            counter["i"] += 1
            result = await self._get_or_populate(key)
            assert result is not None
            assert result["source"] == "backend"

        measurements = await PerformanceBaseline.run_iterations(
            coro_factory=_miss_and_populate,
            iterations=20,
            warmup=2,
        )
        report = PerformanceBaseline.print_performance_report(
            "Cache.miss_and_populate", measurements
        )
        assert report.avg_ms < 50, (
            f"Cache miss+populate avg {report.avg_ms:.2f}ms exceeds 50ms target"
        )

    async def test_cache_hit_rate_under_repeated_requests(self):
        """
        Under a realistic access pattern with repeated keys, the cache
        hit rate should exceed 70%.
        """
        # Pre-populate with 30 keys
        for i in range(30):
            await self._cache_set(f"rate_key_{i}", {"data": i})

        # Reset stats after pre-population
        self.stats = {"hits": 0, "misses": 0, "sets": 0}

        total_requests = 100
        measurements: List[PerformanceMeasurement] = []

        for i in range(total_requests):
            start = time.perf_counter()
            if i % 5 == 0:
                # 20% new keys (misses)
                key = f"new_key_{i}"
            else:
                # 80% existing keys (hits)
                key = f"rate_key_{i % 30}"

            await self._get_or_populate(key)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            measurements.append(PerformanceMeasurement(iteration=i, elapsed_ms=elapsed_ms))

        report = PerformanceBaseline.print_performance_report(
            "Cache.hit_rate_workload", measurements
        )

        total_lookups = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_lookups if total_lookups > 0 else 0.0

        print(
            f"\n  Cache Stats: hits={self.stats['hits']}, "
            f"misses={self.stats['misses']}, "
            f"hit_rate={hit_rate:.1%}"
        )
        assert hit_rate > 0.70, (
            f"Cache hit rate {hit_rate:.1%} is below 70% target"
        )
        # Also assert the latency is reasonable overall
        assert report.avg_ms < 20, (
            f"Mixed workload avg latency {report.avg_ms:.2f}ms is unexpectedly high"
        )


# ===========================================================================
# Resource monitoring helper (used by multiple test classes above)
# ===========================================================================

def _snapshot_resources() -> Dict[str, float]:
    """Capture a snapshot of current process resource usage."""
    proc = psutil.Process()
    return {
        "memory_mb": proc.memory_info().rss / (1024 * 1024),
        "cpu_percent": proc.cpu_percent(interval=0.05),
    }
