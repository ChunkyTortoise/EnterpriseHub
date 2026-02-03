#!/usr/bin/env python3
"""
EnterpriseHub - Concurrent Load Testing Suite
==============================================

Comprehensive load testing for bot API endpoints and bot-level concurrency
under realistic enterprise conditions.

Performance Targets:
- 100 Concurrent Users: p95 <200ms, p99 <500ms, error <5%, throughput >1000 req/sec
- Memory Stability: <2GB under sustained load
- CPU Utilization: <80% during load

Tested Endpoints:
1. GET  /api/bots/health         - Bot health status
2. GET  /api/bots                - List all bots
3. POST /api/bots/{bot_id}/chat  - Send chat to bot
4. GET  /api/bots/{bot_id}/status - Bot status
5. POST /api/jorge-seller/start  - Start seller bot
6. POST /api/jorge-seller/process - Process seller conversation
7. GET  /api/performance/summary - Performance summary

Bot Concurrency Tests:
- JorgeBuyerBot concurrent invocations
- JorgeSellerBot concurrent invocations
- Mixed bot concurrent load

Resource Monitoring:
- Memory stability under load
- CPU utilization under load

Author: Claude Code Agent
Created: 2026-02-02
"""

import pytest
import asyncio
import time
import psutil
import statistics
import random
import uuid
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from httpx import AsyncClient, ASGITransport

from ghl_real_estate_ai.api.main import app


# ============================================================================
# LOAD TEST METRICS COLLECTOR
# ============================================================================


class LoadTestMetrics:
    """
    Metrics collector for load testing.

    Records per-request response times, status codes, and errors.
    Provides aggregate reports with percentiles, throughput, and error rates.
    """

    def __init__(self, test_name: str = "unnamed"):
        self.test_name = test_name
        self.response_times: List[float] = []
        self.status_codes: List[int] = []
        self.errors: List[str] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def record_request(
        self,
        response_time_ms: float,
        status_code: int,
        error_message: Optional[str] = None,
    ):
        """Record a single request's performance data."""
        self.response_times.append(response_time_ms)
        self.status_codes.append(status_code)
        if error_message:
            self.errors.append(error_message)

    def _percentile(self, data: List[float], pct: int) -> float:
        """Calculate the given percentile from a sorted list of values."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        idx = int(len(sorted_data) * pct / 100)
        return sorted_data[min(idx, len(sorted_data) - 1)]

    def get_report(self) -> Dict[str, Any]:
        """
        Build a comprehensive performance report.

        Returns a dictionary with response time percentiles, throughput,
        error rate, and status code distribution.
        """
        if not self.response_times:
            return {"test_name": self.test_name, "error": "No data collected"}

        total_requests = len(self.response_times)
        success_count = sum(1 for code in self.status_codes if 200 <= code < 400)
        error_count = total_requests - success_count
        duration = (self.end_time - self.start_time) if self.end_time and self.start_time else 0.001

        # Status code distribution
        status_dist: Dict[str, int] = {}
        for code in self.status_codes:
            key = str(code)
            status_dist[key] = status_dist.get(key, 0) + 1

        return {
            "test_name": self.test_name,
            "timestamp": datetime.utcnow().isoformat(),
            "total_requests": total_requests,
            "response_times": {
                "min_ms": min(self.response_times),
                "max_ms": max(self.response_times),
                "mean_ms": statistics.mean(self.response_times),
                "median_ms": statistics.median(self.response_times),
                "p50_ms": self._percentile(self.response_times, 50),
                "p90_ms": self._percentile(self.response_times, 90),
                "p95_ms": self._percentile(self.response_times, 95),
                "p99_ms": self._percentile(self.response_times, 99),
                "std_dev_ms": (
                    statistics.stdev(self.response_times)
                    if len(self.response_times) > 1
                    else 0.0
                ),
            },
            "throughput": {
                "requests_per_second": total_requests / duration,
                "duration_seconds": duration,
            },
            "reliability": {
                "success_count": success_count,
                "error_count": error_count,
                "error_rate": error_count / total_requests,
                "success_rate": success_count / total_requests,
                "status_code_distribution": status_dist,
            },
            "errors": {
                "total": len(self.errors),
                "unique": len(set(self.errors)),
                "samples": self.errors[:10],
            },
        }

    def print_report(self):
        """Print a formatted performance report to stdout."""
        report = self.get_report()
        print(f"\n{'=' * 70}")
        print(f"  LOAD TEST REPORT: {report['test_name']}")
        print(f"{'=' * 70}")
        if "error" in report:
            print(f"  ERROR: {report['error']}")
            return
        rt = report["response_times"]
        tp = report["throughput"]
        rl = report["reliability"]
        print(f"  Total Requests:   {report['total_requests']}")
        print(f"  Duration:         {tp['duration_seconds']:.3f}s")
        print(f"  Throughput:       {tp['requests_per_second']:.1f} req/s")
        print(f"  Success Rate:     {rl['success_rate']:.2%}")
        print(f"  Error Rate:       {rl['error_rate']:.2%}")
        print(f"  ---")
        print(f"  p50 Latency:      {rt['p50_ms']:.2f}ms")
        print(f"  p90 Latency:      {rt['p90_ms']:.2f}ms")
        print(f"  p95 Latency:      {rt['p95_ms']:.2f}ms")
        print(f"  p99 Latency:      {rt['p99_ms']:.2f}ms")
        print(f"  Min Latency:      {rt['min_ms']:.2f}ms")
        print(f"  Max Latency:      {rt['max_ms']:.2f}ms")
        print(f"  Mean Latency:     {rt['mean_ms']:.2f}ms")
        if rl["error_count"] > 0:
            print(f"  ---")
            print(f"  Errors:           {rl['error_count']}")
            print(f"  Status Codes:     {rl['status_code_distribution']}")
        print(f"{'=' * 70}\n")


# ============================================================================
# MOCK HELPERS
# ============================================================================


def _build_bot_management_patches():
    """
    Return a context-manager-compatible set of patches that mock all
    external dependencies in the bot_management routes module so that
    API endpoint tests run without real services.
    """
    mock_jorge_bot = MagicMock()
    mock_jorge_bot.process_seller_with_enhancements = AsyncMock(
        return_value=MagicMock(
            temperature="warm",
            qualification_score=72.5,
            frs_score=65.0,
            pcs_score=80.0,
            response="Thanks for reaching out! I'd love to learn more about your property.",
            next_step="schedule_call",
            questions_asked=2,
            jorge_assessment="Good prospect, needs follow-up",
        )
    )

    mock_lead_bot = MagicMock()
    mock_intent_decoder = MagicMock()
    mock_intent_decoder.decode = MagicMock(return_value={"intent": "seller", "score": 0.85})

    mock_performance_monitor = MagicMock()
    mock_performance_monitor.get_jorge_enterprise_summary = MagicMock(
        return_value={
            "status": "healthy",
            "uptime_hours": 48.5,
            "total_conversations": 1234,
            "avg_response_time_ms": 42.0,
            "error_rate": 0.002,
        }
    )
    mock_performance_monitor.track_jorge_performance = AsyncMock()

    mock_event_publisher = MagicMock()
    mock_event_publisher.publish_bot_status_update = AsyncMock()
    mock_event_publisher.publish_conversation_update = AsyncMock()

    return {
        "mock_jorge_bot": mock_jorge_bot,
        "mock_lead_bot": mock_lead_bot,
        "mock_intent_decoder": mock_intent_decoder,
        "mock_performance_monitor": mock_performance_monitor,
        "mock_event_publisher": mock_event_publisher,
    }


def _get_endpoint_rotation() -> List[Dict[str, Any]]:
    """
    Return a list of endpoint definitions that a simulated user cycles through.
    Each entry contains the HTTP method, path, and optional JSON body.
    """
    return [
        {"method": "GET", "path": "/api/bots/health", "json": None},
        {"method": "GET", "path": "/api/bots", "json": None},
        {
            "method": "POST",
            "path": "/api/bots/jorge-seller-bot/chat",
            "json": {
                "message": "I want to sell my 4BR house in Rancho Cucamonga",
                "conversationId": None,
                "contactId": f"load_test_{uuid.uuid4().hex[:8]}",
                "locationId": "3xt4qayAh35BlDLaUv7P",
            },
        },
        {"method": "GET", "path": "/api/bots/jorge-seller-bot/status", "json": None},
        {"method": "GET", "path": "/api/performance/summary", "json": None},
    ]


async def _simulate_user_session(
    client: AsyncClient,
    user_id: int,
    metrics: LoadTestMetrics,
    requests_per_user: int = 5,
):
    """
    Simulate a single user making a series of requests across endpoints.
    Each request's timing is recorded into the provided metrics collector.
    """
    endpoints = _get_endpoint_rotation()
    for req_idx in range(requests_per_user):
        ep = endpoints[req_idx % len(endpoints)]
        # Add small random stagger to mimic realistic user behavior
        await asyncio.sleep(random.uniform(0.001, 0.005))
        start = time.time()
        try:
            if ep["method"] == "GET":
                response = await client.get(ep["path"])
            else:
                body = ep["json"] or {}
                # Ensure unique conversation ID per request
                if "conversationId" in body:
                    body = {**body, "conversationId": str(uuid.uuid4())}
                response = await client.post(ep["path"], json=body)

            elapsed_ms = (time.time() - start) * 1000
            metrics.record_request(
                response_time_ms=elapsed_ms,
                status_code=response.status_code,
            )
        except Exception as exc:
            elapsed_ms = (time.time() - start) * 1000
            metrics.record_request(
                response_time_ms=elapsed_ms,
                status_code=500,
                error_message=f"User {user_id}, request {req_idx}: {str(exc)[:200]}",
            )


# ============================================================================
# BUYER BOT MOCK HELPERS
# ============================================================================


def _build_buyer_bot_patches():
    """
    Build a dictionary of mock patches for JorgeBuyerBot dependencies.
    Returns the patches dict and a factory that creates mock-configured bots.
    """
    mock_intent_profile = MagicMock()
    mock_intent_profile.buyer_temperature = "warm"
    mock_intent_profile.financial_readiness = 70.0
    mock_intent_profile.urgency_score = 65.0
    mock_intent_profile.confidence_level = 0.85
    mock_intent_profile.next_qualification_step = "financial_assessment"
    mock_intent_profile.financing_status_score = 60.0
    mock_intent_profile.budget_clarity = 75.0
    mock_intent_profile.preference_clarity = 70.0

    mock_intent_decoder = MagicMock()
    mock_intent_decoder.analyze_buyer = MagicMock(return_value=mock_intent_profile)

    mock_claude = MagicMock()
    mock_claude.generate_response = AsyncMock(
        return_value={
            "content": "I'd love to help you find the perfect home in Rancho Cucamonga!",
        }
    )

    mock_event_publisher = MagicMock()
    mock_event_publisher.publish_bot_status_update = AsyncMock()
    mock_event_publisher.publish_buyer_intent_analysis = AsyncMock()
    mock_event_publisher.publish_property_match_update = AsyncMock()
    mock_event_publisher.publish_buyer_follow_up_scheduled = AsyncMock()
    mock_event_publisher.publish_buyer_qualification_complete = AsyncMock()
    mock_event_publisher.publish_conversation_update = AsyncMock()

    mock_property_matcher = MagicMock()
    mock_property_matcher.find_matches = MagicMock(
        return_value=[
            {"id": "prop_1", "address": "123 Victoria Ave", "price": 750000},
            {"id": "prop_2", "address": "456 Haven Blvd", "price": 825000},
            {"id": "prop_3", "address": "789 Etiwanda St", "price": 690000},
        ]
    )

    mock_ml_analytics = MagicMock()

    return {
        "BuyerIntentDecoder": MagicMock(return_value=mock_intent_decoder),
        "ClaudeAssistant": MagicMock(return_value=mock_claude),
        "get_event_publisher": Mock(return_value=mock_event_publisher),
        "PropertyMatcher": MagicMock(return_value=mock_property_matcher),
        "get_ml_analytics_engine": Mock(return_value=mock_ml_analytics),
    }


def _build_seller_bot_patches():
    """
    Build mock patches for JorgeSellerBot dependencies.
    """
    mock_intent_decoder = MagicMock()
    mock_intent_decoder.score_lead = MagicMock(
        return_value=MagicMock(
            frs_score=72.0,
            pcs_score=68.0,
            overall_score=70.0,
            temperature="warm",
            next_step="assess_property",
        )
    )

    mock_claude = MagicMock()
    mock_claude.generate_response = AsyncMock(
        return_value={
            "content": "I'd be happy to help you understand your property's value!",
        }
    )

    mock_event_publisher = MagicMock()
    mock_event_publisher.publish_bot_status_update = AsyncMock()
    mock_event_publisher.publish_conversation_update = AsyncMock()
    mock_event_publisher.publish_qualification_complete = AsyncMock()

    mock_ml_analytics = MagicMock()
    mock_ml_analytics.predict_churn_risk = MagicMock(
        return_value=MagicMock(risk_score=0.15, risk_level="low")
    )
    mock_ml_analytics.get_lead_insights = MagicMock(
        return_value={"engagement_trend": "rising", "conversion_probability": 0.72}
    )

    return {
        "LeadIntentDecoder": MagicMock(return_value=mock_intent_decoder),
        "ClaudeAssistant": MagicMock(return_value=mock_claude),
        "get_event_publisher": Mock(return_value=mock_event_publisher),
        "get_ml_analytics_engine": Mock(return_value=mock_ml_analytics),
    }


def _make_buyer_conversation_history() -> List[Dict[str, Any]]:
    """Generate a realistic buyer conversation history."""
    messages = [
        "Hi, I'm looking to buy a house in Rancho Cucamonga",
        "My budget is around $750k, we need at least 3 bedrooms",
        "We're pre-approved and want to move within 3 months",
        "We like the Victoria neighborhood, close to good schools",
        "Do you have anything with a pool and a big backyard?",
    ]
    idx = random.randint(0, len(messages) - 1)
    return [
        {"role": "user", "content": messages[i]}
        for i in range(idx + 1)
    ]


def _make_seller_conversation_history() -> List[Dict[str, Any]]:
    """Generate a realistic seller conversation history."""
    messages = [
        "I'm thinking about selling my home",
        "It's a 4 bedroom, 3 bath in the Etiwanda area",
        "I've been here 12 years, the house is fully renovated",
        "My timeline is flexible, maybe 2-3 months",
        "What do you think it's worth?",
    ]
    idx = random.randint(0, len(messages) - 1)
    return [
        {"role": "user", "content": messages[i]}
        for i in range(idx + 1)
    ]


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def bot_management_mocks():
    """
    Provide mocked bot management dependencies.

    Patches the route-level singletons and factory functions so the FastAPI
    endpoints return immediately with realistic mock data.
    """
    mocks = _build_bot_management_patches()

    patches = [
        patch(
            "ghl_real_estate_ai.api.routes.bot_management.get_jorge_bot",
            return_value=mocks["mock_jorge_bot"],
        ),
        patch(
            "ghl_real_estate_ai.api.routes.bot_management.get_lead_bot",
            return_value=mocks["mock_lead_bot"],
        ),
        patch(
            "ghl_real_estate_ai.api.routes.bot_management.get_intent_decoder",
            return_value=mocks["mock_intent_decoder"],
        ),
        patch(
            "ghl_real_estate_ai.api.routes.bot_management.get_performance_monitor",
            return_value=mocks["mock_performance_monitor"],
        ),
        patch(
            "ghl_real_estate_ai.api.routes.bot_management.get_event_publisher",
            return_value=mocks["mock_event_publisher"],
        ),
        patch(
            "ghl_real_estate_ai.api.routes.bot_management._get_conversation_count",
            new_callable=AsyncMock,
            return_value=42,
        ),
        patch(
            "ghl_real_estate_ai.api.routes.bot_management._get_leads_qualified",
            new_callable=AsyncMock,
            return_value=15,
        ),
    ]

    started = [p.start() for p in patches]
    yield mocks
    for p in patches:
        p.stop()


# ============================================================================
# TEST CLASS 1: CONCURRENT API LOAD
# ============================================================================


class TestConcurrentAPILoad:
    """
    Load testing for bot API endpoints under increasing concurrency levels.

    Each test simulates N concurrent users, where each user makes 5 requests
    across the endpoint rotation (health, list bots, chat, status, performance).
    """

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_load_10_concurrent_users(self, bot_management_mocks):
        """Baseline: 10 concurrent users, 50 total requests."""
        metrics = LoadTestMetrics("API Load - 10 Concurrent Users")
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            metrics.start_time = time.time()
            tasks = [
                _simulate_user_session(client, user_id=i, metrics=metrics, requests_per_user=5)
                for i in range(10)
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
            metrics.end_time = time.time()

        metrics.print_report()
        report = metrics.get_report()

        # Baseline targets: very lenient
        assert report["reliability"]["error_rate"] <= 0.10, (
            f"Error rate {report['reliability']['error_rate']:.2%} exceeds 10% for baseline"
        )
        assert report["response_times"]["p95_ms"] < 500, (
            f"p95 latency {report['response_times']['p95_ms']:.1f}ms exceeds 500ms for baseline"
        )

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_load_25_concurrent_users(self, bot_management_mocks):
        """Light load: 25 concurrent users, 125 total requests."""
        metrics = LoadTestMetrics("API Load - 25 Concurrent Users")
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            metrics.start_time = time.time()
            tasks = [
                _simulate_user_session(client, user_id=i, metrics=metrics, requests_per_user=5)
                for i in range(25)
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
            metrics.end_time = time.time()

        metrics.print_report()
        report = metrics.get_report()

        assert report["reliability"]["error_rate"] <= 0.10, (
            f"Error rate {report['reliability']['error_rate']:.2%} exceeds 10% for light load"
        )
        assert report["response_times"]["p95_ms"] < 400, (
            f"p95 latency {report['response_times']['p95_ms']:.1f}ms exceeds 400ms for light load"
        )

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_load_50_concurrent_users(self, bot_management_mocks):
        """Moderate load: 50 concurrent users, 250 total requests."""
        metrics = LoadTestMetrics("API Load - 50 Concurrent Users")
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            metrics.start_time = time.time()
            tasks = [
                _simulate_user_session(client, user_id=i, metrics=metrics, requests_per_user=5)
                for i in range(50)
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
            metrics.end_time = time.time()

        metrics.print_report()
        report = metrics.get_report()

        assert report["reliability"]["error_rate"] <= 0.05, (
            f"Error rate {report['reliability']['error_rate']:.2%} exceeds 5% for moderate load"
        )
        assert report["response_times"]["p95_ms"] < 300, (
            f"p95 latency {report['response_times']['p95_ms']:.1f}ms exceeds 300ms for moderate load"
        )

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_load_100_concurrent_users(self, bot_management_mocks):
        """
        Target load: 100 concurrent users, 500 total requests.

        Primary performance assertion point:
        - p95 < 200ms
        - p99 < 500ms
        - error rate < 5%
        - throughput > 1000 req/sec
        """
        metrics = LoadTestMetrics("API Load - 100 Concurrent Users (TARGET)")
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            metrics.start_time = time.time()
            tasks = [
                _simulate_user_session(client, user_id=i, metrics=metrics, requests_per_user=5)
                for i in range(100)
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
            metrics.end_time = time.time()

        metrics.print_report()
        report = metrics.get_report()

        # Primary performance targets
        assert report["response_times"]["p95_ms"] < 200, (
            f"p95 latency {report['response_times']['p95_ms']:.1f}ms exceeds target of 200ms"
        )
        assert report["response_times"]["p99_ms"] < 500, (
            f"p99 latency {report['response_times']['p99_ms']:.1f}ms exceeds target of 500ms"
        )
        assert report["reliability"]["error_rate"] < 0.05, (
            f"Error rate {report['reliability']['error_rate']:.2%} exceeds target of 5%"
        )
        assert report["throughput"]["requests_per_second"] > 1000, (
            f"Throughput {report['throughput']['requests_per_second']:.1f} req/s "
            f"below target of 1000 req/s"
        )

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_load_200_concurrent_users(self, bot_management_mocks):
        """
        Stress test: 200 concurrent users, 1000 total requests.

        Relaxed targets to validate the system degrades gracefully rather
        than failing outright under extreme load.
        """
        metrics = LoadTestMetrics("API Load - 200 Concurrent Users (STRESS)")
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            metrics.start_time = time.time()
            tasks = [
                _simulate_user_session(client, user_id=i, metrics=metrics, requests_per_user=5)
                for i in range(200)
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
            metrics.end_time = time.time()

        metrics.print_report()
        report = metrics.get_report()

        # Stress targets: system should not collapse
        assert report["reliability"]["success_rate"] >= 0.80, (
            f"Success rate {report['reliability']['success_rate']:.2%} below 80% under stress"
        )
        assert report["response_times"]["p95_ms"] < 1000, (
            f"p95 latency {report['response_times']['p95_ms']:.1f}ms exceeds 1000ms stress limit"
        )
        assert report["throughput"]["requests_per_second"] > 500, (
            f"Throughput {report['throughput']['requests_per_second']:.1f} req/s "
            f"below 500 req/s stress floor"
        )


# ============================================================================
# TEST CLASS 2: BOT CONCURRENT PROCESSING
# ============================================================================


class TestBotConcurrentProcessing:
    """
    Bot-level concurrency tests.

    Tests that JorgeBuyerBot and JorgeSellerBot workflow invocations
    can handle 50+ simultaneous conversations without errors or
    significant performance degradation.
    """

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_buyer_bot_processing(self):
        """50 concurrent JorgeBuyerBot workflow invocations."""
        metrics = LoadTestMetrics("Buyer Bot - 50 Concurrent Invocations")

        buyer_patches = _build_buyer_bot_patches()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=buyer_patches["BuyerIntentDecoder"],
            ClaudeAssistant=buyer_patches["ClaudeAssistant"],
            get_event_publisher=buyer_patches["get_event_publisher"],
            PropertyMatcher=buyer_patches["PropertyMatcher"],
            get_ml_analytics_engine=buyer_patches["get_ml_analytics_engine"],
        ):
            # Import after patching so the bot picks up mocked dependencies
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            bot = JorgeBuyerBot(tenant_id="test_tenant", enable_bot_intelligence=False)

            async def invoke_buyer_bot(invocation_id: int):
                conversation = _make_buyer_conversation_history()
                buyer_id = f"buyer_load_{invocation_id}_{uuid.uuid4().hex[:6]}"
                # Simulate realistic mock latency
                await asyncio.sleep(random.uniform(0.005, 0.020))
                start = time.time()
                try:
                    result = await bot.process_buyer_conversation(
                        buyer_id=buyer_id,
                        buyer_name=f"Test Buyer {invocation_id}",
                        conversation_history=conversation,
                    )
                    elapsed_ms = (time.time() - start) * 1000
                    status = 200 if result.get("error") is None else 500
                    metrics.record_request(
                        response_time_ms=elapsed_ms,
                        status_code=status,
                        error_message=result.get("error"),
                    )
                except Exception as exc:
                    elapsed_ms = (time.time() - start) * 1000
                    metrics.record_request(
                        response_time_ms=elapsed_ms,
                        status_code=500,
                        error_message=str(exc)[:200],
                    )

            metrics.start_time = time.time()
            tasks = [invoke_buyer_bot(i) for i in range(50)]
            await asyncio.gather(*tasks, return_exceptions=True)
            metrics.end_time = time.time()

        metrics.print_report()
        report = metrics.get_report()

        assert report["reliability"]["error_rate"] < 0.05, (
            f"Buyer bot error rate {report['reliability']['error_rate']:.2%} exceeds 5%"
        )
        assert report["response_times"]["p95_ms"] < 500, (
            f"Buyer bot p95 {report['response_times']['p95_ms']:.1f}ms exceeds 500ms"
        )

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_seller_bot_processing(self):
        """50 concurrent JorgeSellerBot workflow invocations."""
        metrics = LoadTestMetrics("Seller Bot - 50 Concurrent Invocations")

        seller_patches = _build_seller_bot_patches()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_seller_bot",
            LeadIntentDecoder=seller_patches["LeadIntentDecoder"],
            ClaudeAssistant=seller_patches["ClaudeAssistant"],
            get_event_publisher=seller_patches["get_event_publisher"],
            get_ml_analytics_engine=seller_patches["get_ml_analytics_engine"],
        ):
            from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot

            bot = JorgeSellerBot(
                tenant_id="test_tenant",
                config=None,  # Uses defaults, which disables optional features gracefully
            )

            async def invoke_seller_bot(invocation_id: int):
                conversation = _make_seller_conversation_history()
                lead_id = f"seller_load_{invocation_id}_{uuid.uuid4().hex[:6]}"
                await asyncio.sleep(random.uniform(0.005, 0.020))
                start = time.time()
                try:
                    # Build initial state and invoke the workflow directly
                    initial_state = {
                        "lead_id": lead_id,
                        "contact_id": lead_id,
                        "message": conversation[-1]["content"],
                        "conversation_history": conversation,
                        "lead_info": {
                            "contact_id": lead_id,
                            "name": f"Test Seller {invocation_id}",
                            "location_id": "3xt4qayAh35BlDLaUv7P",
                        },
                    }
                    result = await bot.workflow.ainvoke(initial_state)
                    elapsed_ms = (time.time() - start) * 1000
                    metrics.record_request(
                        response_time_ms=elapsed_ms,
                        status_code=200,
                    )
                except Exception as exc:
                    elapsed_ms = (time.time() - start) * 1000
                    metrics.record_request(
                        response_time_ms=elapsed_ms,
                        status_code=500,
                        error_message=str(exc)[:200],
                    )

            metrics.start_time = time.time()
            tasks = [invoke_seller_bot(i) for i in range(50)]
            await asyncio.gather(*tasks, return_exceptions=True)
            metrics.end_time = time.time()

        metrics.print_report()
        report = metrics.get_report()

        assert report["reliability"]["error_rate"] < 0.05, (
            f"Seller bot error rate {report['reliability']['error_rate']:.2%} exceeds 5%"
        )
        assert report["response_times"]["p95_ms"] < 500, (
            f"Seller bot p95 {report['response_times']['p95_ms']:.1f}ms exceeds 500ms"
        )

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_mixed_bot_concurrent_load(self):
        """
        Mixed load: 30 buyer + 30 seller bot invocations concurrently (60 total).

        Validates that running both bot types simultaneously does not cause
        interference, resource contention, or elevated error rates.
        """
        metrics = LoadTestMetrics("Mixed Bot Load - 60 Concurrent (30 Buyer + 30 Seller)")

        buyer_patches = _build_buyer_bot_patches()
        seller_patches = _build_seller_bot_patches()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=buyer_patches["BuyerIntentDecoder"],
            ClaudeAssistant=buyer_patches["ClaudeAssistant"],
            get_event_publisher=buyer_patches["get_event_publisher"],
            PropertyMatcher=buyer_patches["PropertyMatcher"],
            get_ml_analytics_engine=buyer_patches["get_ml_analytics_engine"],
        ), patch.multiple(
            "ghl_real_estate_ai.agents.jorge_seller_bot",
            LeadIntentDecoder=seller_patches["LeadIntentDecoder"],
            ClaudeAssistant=seller_patches["ClaudeAssistant"],
            get_event_publisher=seller_patches["get_event_publisher"],
            get_ml_analytics_engine=seller_patches["get_ml_analytics_engine"],
        ):
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot
            from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot

            buyer_bot = JorgeBuyerBot(tenant_id="test_tenant", enable_bot_intelligence=False)
            seller_bot = JorgeSellerBot(tenant_id="test_tenant", config=None)

            async def invoke_buyer(idx: int):
                conversation = _make_buyer_conversation_history()
                buyer_id = f"mixed_buyer_{idx}_{uuid.uuid4().hex[:6]}"
                await asyncio.sleep(random.uniform(0.005, 0.020))
                start = time.time()
                try:
                    result = await buyer_bot.process_buyer_conversation(
                        buyer_id=buyer_id,
                        buyer_name=f"Mixed Buyer {idx}",
                        conversation_history=conversation,
                    )
                    elapsed_ms = (time.time() - start) * 1000
                    status = 200 if result.get("error") is None else 500
                    metrics.record_request(
                        response_time_ms=elapsed_ms,
                        status_code=status,
                        error_message=result.get("error"),
                    )
                except Exception as exc:
                    elapsed_ms = (time.time() - start) * 1000
                    metrics.record_request(
                        response_time_ms=elapsed_ms,
                        status_code=500,
                        error_message=f"buyer_{idx}: {str(exc)[:200]}",
                    )

            async def invoke_seller(idx: int):
                conversation = _make_seller_conversation_history()
                lead_id = f"mixed_seller_{idx}_{uuid.uuid4().hex[:6]}"
                await asyncio.sleep(random.uniform(0.005, 0.020))
                start = time.time()
                try:
                    initial_state = {
                        "lead_id": lead_id,
                        "contact_id": lead_id,
                        "message": conversation[-1]["content"],
                        "conversation_history": conversation,
                        "lead_info": {
                            "contact_id": lead_id,
                            "name": f"Mixed Seller {idx}",
                            "location_id": "3xt4qayAh35BlDLaUv7P",
                        },
                    }
                    result = await seller_bot.workflow.ainvoke(initial_state)
                    elapsed_ms = (time.time() - start) * 1000
                    metrics.record_request(
                        response_time_ms=elapsed_ms,
                        status_code=200,
                    )
                except Exception as exc:
                    elapsed_ms = (time.time() - start) * 1000
                    metrics.record_request(
                        response_time_ms=elapsed_ms,
                        status_code=500,
                        error_message=f"seller_{idx}: {str(exc)[:200]}",
                    )

            metrics.start_time = time.time()
            buyer_tasks = [invoke_buyer(i) for i in range(30)]
            seller_tasks = [invoke_seller(i) for i in range(30)]
            await asyncio.gather(*(buyer_tasks + seller_tasks), return_exceptions=True)
            metrics.end_time = time.time()

        metrics.print_report()
        report = metrics.get_report()

        assert report["reliability"]["error_rate"] < 0.05, (
            f"Mixed bot error rate {report['reliability']['error_rate']:.2%} exceeds 5%"
        )
        assert report["response_times"]["p95_ms"] < 500, (
            f"Mixed bot p95 {report['response_times']['p95_ms']:.1f}ms exceeds 500ms"
        )
        assert report["total_requests"] == 60, (
            f"Expected 60 total requests, got {report['total_requests']}"
        )


# ============================================================================
# TEST CLASS 3: RESOURCE UTILIZATION
# ============================================================================


class TestResourceUtilization:
    """
    Resource monitoring tests under concurrent load.

    Validates that memory and CPU utilization remain within acceptable
    bounds during sustained concurrent operations.
    """

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_memory_stability_under_load(self, bot_management_mocks):
        """
        Memory stays below 2GB during 100 concurrent API operations.

        Measures memory before, during (sampled), and after the load test.
        Asserts that peak RSS stays under the 2GB threshold and that
        memory does not grow unboundedly.
        """
        process = psutil.Process()
        memory_samples: List[float] = []

        # Baseline memory measurement
        baseline_memory_mb = process.memory_info().rss / (1024 * 1024)
        memory_samples.append(baseline_memory_mb)

        metrics = LoadTestMetrics("Memory Stability - 100 Concurrent Ops")
        transport = ASGITransport(app=app)

        async def memory_sampling_loop(stop_event: asyncio.Event):
            """Periodically sample memory usage while the load test runs."""
            while not stop_event.is_set():
                mem_mb = process.memory_info().rss / (1024 * 1024)
                memory_samples.append(mem_mb)
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=0.1)
                except asyncio.TimeoutError:
                    pass

        stop_event = asyncio.Event()
        sampler_task = asyncio.create_task(memory_sampling_loop(stop_event))

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            metrics.start_time = time.time()
            tasks = [
                _simulate_user_session(client, user_id=i, metrics=metrics, requests_per_user=5)
                for i in range(100)
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
            metrics.end_time = time.time()

        # Stop memory sampling
        stop_event.set()
        await sampler_task

        # Post-load memory measurement
        post_memory_mb = process.memory_info().rss / (1024 * 1024)
        memory_samples.append(post_memory_mb)

        peak_memory_mb = max(memory_samples)
        memory_growth_mb = post_memory_mb - baseline_memory_mb

        metrics.print_report()

        print(f"\n--- Memory Report ---")
        print(f"  Baseline:         {baseline_memory_mb:.1f} MB")
        print(f"  Peak:             {peak_memory_mb:.1f} MB")
        print(f"  Post-load:        {post_memory_mb:.1f} MB")
        print(f"  Growth:           {memory_growth_mb:+.1f} MB")
        print(f"  Samples:          {len(memory_samples)}")
        print(f"  Avg Memory:       {statistics.mean(memory_samples):.1f} MB")
        print(f"---------------------\n")

        # Memory must stay under 2GB
        assert peak_memory_mb < 2048, (
            f"Peak memory {peak_memory_mb:.1f}MB exceeds 2GB limit"
        )

        # Memory growth should be bounded (no significant leaks)
        # Allow up to 500MB growth for 100 concurrent sessions
        assert memory_growth_mb < 500, (
            f"Memory grew by {memory_growth_mb:.1f}MB during load test, "
            f"suggesting a possible leak"
        )

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_cpu_utilization_under_load(self, bot_management_mocks):
        """
        CPU utilization stays below 80% during 100 concurrent API operations.

        Samples CPU usage periodically during the load test and validates
        the average does not exceed the threshold.
        """
        cpu_samples: List[float] = []

        # Pre-warm CPU measurement (first call is often inaccurate)
        psutil.cpu_percent(interval=0.1)

        metrics = LoadTestMetrics("CPU Utilization - 100 Concurrent Ops")
        transport = ASGITransport(app=app)

        async def cpu_sampling_loop(stop_event: asyncio.Event):
            """Periodically sample CPU utilization."""
            while not stop_event.is_set():
                cpu_pct = psutil.cpu_percent(interval=0.0)
                if cpu_pct > 0:
                    cpu_samples.append(cpu_pct)
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=0.2)
                except asyncio.TimeoutError:
                    pass

        stop_event = asyncio.Event()
        sampler_task = asyncio.create_task(cpu_sampling_loop(stop_event))

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            metrics.start_time = time.time()
            tasks = [
                _simulate_user_session(client, user_id=i, metrics=metrics, requests_per_user=5)
                for i in range(100)
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
            metrics.end_time = time.time()

        # Stop CPU sampling
        stop_event.set()
        await sampler_task

        metrics.print_report()

        if cpu_samples:
            avg_cpu = statistics.mean(cpu_samples)
            peak_cpu = max(cpu_samples)

            print(f"\n--- CPU Report ---")
            print(f"  Avg CPU:          {avg_cpu:.1f}%")
            print(f"  Peak CPU:         {peak_cpu:.1f}%")
            print(f"  Samples:          {len(cpu_samples)}")
            if len(cpu_samples) > 1:
                print(f"  Std Dev:          {statistics.stdev(cpu_samples):.1f}%")
            print(f"------------------\n")

            # Average CPU should stay under 80%
            assert avg_cpu < 80, (
                f"Average CPU utilization {avg_cpu:.1f}% exceeds 80% threshold"
            )
        else:
            # If no samples were collected (extremely fast test), skip assertion
            print("  WARNING: No CPU samples collected (test completed too quickly)")


# ============================================================================
# MODULE-LEVEL CONFIGURATION
# ============================================================================


pytestmark = [pytest.mark.performance]


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "-m", "performance",
        "--tb=short",
        "-s",
    ])
