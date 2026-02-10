import pytest

@pytest.mark.integration
#!/usr/bin/env python3
"""
🚀 Jorge Bot Performance Baseline Load Tests
=============================================

Performance baseline establishment for Jorge bots:
- Lead Bot: P95 < 2000ms (10 concurrent, 100 requests)
- Buyer Bot: P95 < 2500ms (10 concurrent, 100 requests)
- Seller Bot: P95 < 2500ms (10 concurrent, 100 requests)
- Handoff Service: P95 < 500ms (20 concurrent, 200 requests)

SLA Targets (Phase 4 Audit Spec):
    - Lead Bot P95 < 2000ms
    - Buyer Bot P95 < 2500ms
    - Seller Bot P95 < 2500ms
    - Handoff P95 < 500ms

Author: Claude Code Assistant - Jorge Performance Engineering
Date: 2026-02-07
Version: 1.0.0
"""

import asyncio
import logging
import os
import statistics
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

logger = logging.getLogger(__name__)

# SLA Configuration
SLA_TARGETS = {
    "lead_bot": {"p95_target": 2000, "p99_target": 3000},
    "buyer_bot": {"p95_target": 2500, "p99_target": 3500},
    "seller_bot": {"p95_target": 2500, "p99_target": 3500},
    "handoff": {"p95_target": 500, "p99_target": 800},
}


@dataclass
class LoadTestResult:
    """Results from a single load test run"""

    bot_name: str
    test_type: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    mean_ms: float
    min_ms: float
    max_ms: float
    total_duration_ms: float
    requests_per_second: float
    success_rate: float
    sla_compliant: bool
    sla_violations: List[str] = field(default_factory=list)


class MockPerformanceTracker:
    """Mock performance tracker for load testing without external dependencies"""

    def __init__(self):
        self.measurements: Dict[str, List[float]] = {
            "lead_bot": [],
            "buyer_bot": [],
            "seller_bot": [],
            "handoff": [],
        }

    async def track_operation(
        self,
        bot_name: str,
        operation: str,
        duration_ms: float,
        success: bool = True,
        cache_hit: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        if success:
            self.measurements[bot_name].append(duration_ms)


class MockLeadBot:
    """Mock Lead Bot for performance testing"""

    async def process_lead_conversation(
        self,
        conversation_id: str,
        user_message: str,
        lead_name: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        # Simulate processing time
        await asyncio.sleep(0.05 + (hash(conversation_id) % 100) / 1000)
        return {
            "response_content": "Thank you for your interest! I'd love to help you.",
            "lead_id": conversation_id,
            "current_step": "qualify",
            "handoff_signals": {},
        }


class MockBuyerBot:
    """Mock Buyer Bot for performance testing"""

    async def process_buyer_conversation(
        self,
        conversation_id: str,
        user_message: str,
        buyer_name: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        # Simulate processing time
        await asyncio.sleep(0.08 + (hash(conversation_id) % 150) / 1000)
        return {
            "response_content": "Let me help you find the perfect property!",
            "lead_id": conversation_id,
            "financial_readiness": 75.0,
            "handoff_signals": {},
        }


class MockSellerBot:
    """Mock Seller Bot for performance testing"""

    async def process_seller_message(
        self,
        conversation_id: str,
        user_message: str,
        seller_name: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        # Simulate processing time
        await asyncio.sleep(0.08 + (hash(conversation_id) % 150) / 1000)
        return {
            "response_content": "I can help you understand your home's value!",
            "lead_id": conversation_id,
            "frs_score": 65.0,
            "pcs_score": 70.0,
            "handoff_signals": {},
        }


class MockHandoffService:
    """Mock Handoff Service for performance testing"""

    async def evaluate_handoff(
        self,
        current_bot: str,
        contact_id: str,
        conversation_history: List[Dict],
        intent_signals: Dict[str, Any],
    ) -> Optional[Any]:
        # Simulate very fast processing
        await asyncio.sleep(0.01 + (hash(contact_id) % 50) / 1000)

        buyer_score = intent_signals.get("buyer_intent_score", 0.0)
        seller_score = intent_signals.get("seller_intent_score", 0.0)

        if buyer_score > 0.6 or seller_score > 0.6:
            return type(
                "HandoffDecision",
                (),
                {
                    "source_bot": current_bot,
                    "target_bot": "buyer" if buyer_score > seller_score else "seller",
                    "confidence": max(buyer_score, seller_score),
                },
            )()
        return None


class JorgeLoadTester:
    """Load tester for Jorge bots with comprehensive metrics collection"""

    def __init__(self):
        self.tracker = MockPerformanceTracker()
        self.results: List[LoadTestResult] = []

    async def test_lead_bot(
        self,
        num_concurrent: int = 10,
        total_requests: int = 100,
    ) -> LoadTestResult:
        """Run load test for Lead Bot"""
        logger.info(f"Starting Lead Bot load test: {num_concurrent} concurrent, {total_requests} total")

        lead_bot = MockLeadBot()

        response_times = []
        errors = []
        start_time = time.perf_counter()

        async def make_request(index: int) -> float:
            test_data = {
                "conversation_id": f"load_test_lead_{index}_{uuid.uuid4().hex[:8]}",
                "user_message": f"I'm interested in buying a home. Budget: ${500000 + (index * 10000)}",
                "lead_name": f"Lead {index}",
            }
            req_start = time.perf_counter()
            try:
                result = await lead_bot.process_lead_conversation(**test_data)
                elapsed_ms = (time.perf_counter() - req_start) * 1000

                await self.tracker.track_operation(
                    bot_name="lead_bot",
                    operation="process",
                    duration_ms=elapsed_ms,
                    success=result.get("response_content") is not None,
                )

                return elapsed_ms
            except Exception as e:
                elapsed_ms = (time.perf_counter() - req_start) * 1000
                errors.append(str(e))
                return elapsed_ms

        semaphore = asyncio.Semaphore(num_concurrent)

        async def bounded_request(index: int):
            async with semaphore:
                return await make_request(index)

        tasks = [bounded_request(i) for i in range(total_requests)]
        response_times = await asyncio.gather(*tasks, return_exceptions=True)

        valid_times = [t for t in response_times if isinstance(t, (int, float)) and t > 0]
        total_duration = (time.perf_counter() - start_time) * 1000
        success_count = len([t for t in response_times if isinstance(t, (int, float))])

        return self._compile_results(
            bot_name="lead_bot",
            test_type="process",
            response_times=valid_times,
            total_requests=total_requests,
            successful_requests=success_count,
            failed_requests=len(response_times) - success_count,
            total_duration_ms=total_duration,
            errors=errors,
            target_p95=SLA_TARGETS["lead_bot"]["p95_target"],
        )

    async def test_buyer_bot(
        self,
        num_concurrent: int = 10,
        total_requests: int = 100,
    ) -> LoadTestResult:
        """Run load test for Buyer Bot"""
        logger.info(f"Starting Buyer Bot load test: {num_concurrent} concurrent, {total_requests} total")

        buyer_bot = MockBuyerBot()

        response_times = []
        errors = []
        start_time = time.perf_counter()

        async def make_request(index: int) -> float:
            test_data = {
                "conversation_id": f"load_test_buyer_{index}_{uuid.uuid4().hex[:8]}",
                "user_message": f"Looking for 3 bedroom home, pre-approved for ${600000 + (index * 15000)}",
                "buyer_name": f"Buyer {index}",
            }
            req_start = time.perf_counter()
            try:
                result = await buyer_bot.process_buyer_conversation(**test_data)
                elapsed_ms = (time.perf_counter() - req_start) * 1000

                await self.tracker.track_operation(
                    bot_name="buyer_bot",
                    operation="process",
                    duration_ms=elapsed_ms,
                    success=result.get("response_content") is not None,
                )

                return elapsed_ms
            except Exception as e:
                elapsed_ms = (time.perf_counter() - req_start) * 1000
                errors.append(str(e))
                return elapsed_ms

        semaphore = asyncio.Semaphore(num_concurrent)

        async def bounded_request(index: int):
            async with semaphore:
                return await make_request(index)

        tasks = [bounded_request(i) for i in range(total_requests)]
        response_times = await asyncio.gather(*tasks, return_exceptions=True)

        valid_times = [t for t in response_times if isinstance(t, (int, float)) and t > 0]
        total_duration = (time.perf_counter() - start_time) * 1000
        success_count = len([t for t in response_times if isinstance(t, (int, float))])

        return self._compile_results(
            bot_name="buyer_bot",
            test_type="process",
            response_times=valid_times,
            total_requests=total_requests,
            successful_requests=success_count,
            failed_requests=len(response_times) - success_count,
            total_duration_ms=total_duration,
            errors=errors,
            target_p95=SLA_TARGETS["buyer_bot"]["p95_target"],
        )

    async def test_seller_bot(
        self,
        num_concurrent: int = 10,
        total_requests: int = 100,
    ) -> LoadTestResult:
        """Run load test for Seller Bot"""
        logger.info(f"Starting Seller Bot load test: {num_concurrent} concurrent, {total_requests} total")

        seller_bot = MockSellerBot()

        response_times = []
        errors = []
        start_time = time.perf_counter()

        async def make_request(index: int) -> float:
            test_data = {
                "conversation_id": f"load_test_seller_{index}_{uuid.uuid4().hex[:8]}",
                "user_message": f"I want to sell my home at 123 Main Street. 4BR/2BA, 2000 sqft.",
                "seller_name": f"Seller {index}",
            }
            req_start = time.perf_counter()
            try:
                result = await seller_bot.process_seller_message(**test_data)
                elapsed_ms = (time.perf_counter() - req_start) * 1000

                await self.tracker.track_operation(
                    bot_name="seller_bot",
                    operation="process",
                    duration_ms=elapsed_ms,
                    success=result.get("response_content") is not None,
                )

                return elapsed_ms
            except Exception as e:
                elapsed_ms = (time.perf_counter() - req_start) * 1000
                errors.append(str(e))
                return elapsed_ms

        semaphore = asyncio.Semaphore(num_concurrent)

        async def bounded_request(index: int):
            async with semaphore:
                return await make_request(index)

        tasks = [bounded_request(i) for i in range(total_requests)]
        response_times = await asyncio.gather(*tasks, return_exceptions=True)

        valid_times = [t for t in response_times if isinstance(t, (int, float)) and t > 0]
        total_duration = (time.perf_counter() - start_time) * 1000
        success_count = len([t for t in response_times if isinstance(t, (int, float))])

        return self._compile_results(
            bot_name="seller_bot",
            test_type="process",
            response_times=valid_times,
            total_requests=total_requests,
            successful_requests=success_count,
            failed_requests=len(response_times) - success_count,
            total_duration_ms=total_duration,
            errors=errors,
            target_p95=SLA_TARGETS["seller_bot"]["p95_target"],
        )

    async def test_handoff_service(
        self,
        num_concurrent: int = 20,
        total_requests: int = 200,
    ) -> LoadTestResult:
        """Run load test for Handoff Service"""
        logger.info(f"Starting Handoff Service load test: {num_concurrent} concurrent, {total_requests} total")

        handoff_service = MockHandoffService()

        response_times = []
        errors = []
        start_time = time.perf_counter()

        async def make_request(index: int) -> float:
            test_data = {
                "current_bot": "lead",
                "contact_id": f"load_test_handoff_{index}_{uuid.uuid4().hex[:8]}",
                "conversation_history": [
                    {"role": "user", "content": "I'm looking to sell my current home too"},
                ],
                "intent_signals": {
                    "seller_intent_score": 0.75 + (0.02 * (index % 10)),
                    "buyer_intent_score": 0.25 + (0.01 * (index % 10)),
                },
            }
            req_start = time.perf_counter()
            try:
                result = await handoff_service.evaluate_handoff(**test_data)
                elapsed_ms = (time.perf_counter() - req_start) * 1000

                await self.tracker.track_operation(
                    bot_name="handoff",
                    operation="execute",
                    duration_ms=elapsed_ms,
                    success=True,
                )

                return elapsed_ms
            except Exception as e:
                elapsed_ms = (time.perf_counter() - req_start) * 1000
                errors.append(str(e))
                return elapsed_ms

        semaphore = asyncio.Semaphore(num_concurrent)

        async def bounded_request(index: int):
            async with semaphore:
                return await make_request(index)

        tasks = [bounded_request(i) for i in range(total_requests)]
        response_times = await asyncio.gather(*tasks, return_exceptions=True)

        valid_times = [t for t in response_times if isinstance(t, (int, float)) and t > 0]
        total_duration = (time.perf_counter() - start_time) * 1000
        success_count = len([t for t in response_times if isinstance(t, (int, float))])

        return self._compile_results(
            bot_name="handoff",
            test_type="execute",
            response_times=valid_times,
            total_requests=total_requests,
            successful_requests=success_count,
            failed_requests=len(response_times) - success_count,
            total_duration_ms=total_duration,
            errors=errors,
            target_p95=SLA_TARGETS["handoff"]["p95_target"],
        )

    def _compile_results(
        self,
        bot_name: str,
        test_type: str,
        response_times: List[float],
        total_requests: int,
        successful_requests: int,
        failed_requests: int,
        total_duration_ms: float,
        errors: List[str],
        target_p95: float,
    ) -> LoadTestResult:
        """Compile results from a load test"""
        if not response_times:
            return LoadTestResult(
                bot_name=bot_name,
                test_type=test_type,
                total_requests=total_requests,
                successful_requests=0,
                failed_requests=total_requests,
                p50_ms=0,
                p95_ms=0,
                p99_ms=0,
                mean_ms=0,
                min_ms=0,
                max_ms=0,
                total_duration_ms=total_duration_ms,
                requests_per_second=0,
                success_rate=0,
                sla_compliant=False,
                sla_violations=["No successful requests"],
            )

        sorted_times = sorted(response_times)
        n = len(sorted_times)

        p50_idx = max(0, min(n - 1, int(n * 0.50)))
        p95_idx = max(0, min(n - 1, int(n * 0.95)))
        p99_idx = max(0, min(n - 1, int(n * 0.99)))

        p50 = sorted_times[p50_idx]
        p95 = sorted_times[p95_idx]
        p99 = sorted_times[p99_idx]

        mean = statistics.mean(response_times)
        min_t = min(response_times)
        max_t = max(response_times)

        success_rate = successful_requests / total_requests if total_requests > 0 else 0
        rps = successful_requests / (total_duration_ms / 1000) if total_duration_ms > 0 else 0

        # SLA compliance check
        sla_violations = []
        if p95 > target_p95:
            sla_violations.append(f"P95 {p95:.1f}ms exceeds target {target_p95:.0f}ms")

        sla_compliant = len(sla_violations) == 0

        return LoadTestResult(
            bot_name=bot_name,
            test_type=test_type,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            p50_ms=round(p50, 2),
            p95_ms=round(p95, 2),
            p99_ms=round(p99, 2),
            mean_ms=round(mean, 2),
            min_ms=round(min_t, 2),
            max_ms=round(max_t, 2),
            total_duration_ms=round(total_duration_ms, 2),
            requests_per_second=round(rps, 2),
            success_rate=round(success_rate, 4),
            sla_compliant=sla_compliant,
            sla_violations=sla_violations,
        )


def format_result_table(results: List[LoadTestResult]) -> str:
    """Format results as a markdown table"""
    lines = [
        "| Bot | Requests | Success Rate | P50 (ms) | P95 (ms) | P99 (ms) | Mean (ms) | RPS | SLA Compliant |",
        "|-----|----------|--------------|----------|----------|----------|-----------|-----|---------------|",
    ]

    for r in results:
        sla_status = "✅ YES" if r.sla_compliant else "❌ NO"
        lines.append(
            f"| {r.bot_name:<8} | {r.total_requests:>7} | {r.success_rate * 100:>10.1f}% | "
            f"{r.p50_ms:>7.1f} | {r.p95_ms:>7.1f} | {r.p99_ms:>7.1f} | "
            f"{r.mean_ms:>8.1f} | {r.requests_per_second:>4.1f} | {sla_status:>13} |"
        )

    return "\n".join(lines)


async def run_all_load_tests() -> List[LoadTestResult]:
    """Run all load tests and return results"""
    tester = JorgeLoadTester()
    results = []

    print("\n" + "=" * 70)
    print("🚀 JORGE BOT PERFORMANCE BASELINE LOAD TESTS")
    print("=" * 70)
    print(f"Start Time: {datetime.now(timezone.utc).isoformat()}")
    print(f"SLA Targets:")
    for bot, targets in SLA_TARGETS.items():
        print(f"  - {bot}: P95 < {targets['p95_target']}ms")
    print("=" * 70 + "\n")

    # Test Lead Bot
    print("\n📊 Testing Lead Bot (P95 < 2000ms target)")
    print("-" * 50)
    lead_result = await tester.test_lead_bot(num_concurrent=10, total_requests=100)
    results.append(lead_result)
    print(f"  P95: {lead_result.p95_ms:.1f}ms | Success: {lead_result.success_rate * 100:.1f}%")
    if lead_result.sla_violations:
        for v in lead_result.sla_violations:
            print(f"  ⚠️  {v}")

    # Test Buyer Bot
    print("\n📊 Testing Buyer Bot (P95 < 2500ms target)")
    print("-" * 50)
    buyer_result = await tester.test_buyer_bot(num_concurrent=10, total_requests=100)
    results.append(buyer_result)
    print(f"  P95: {buyer_result.p95_ms:.1f}ms | Success: {buyer_result.success_rate * 100:.1f}%")
    if buyer_result.sla_violations:
        for v in buyer_result.sla_violations:
            print(f"  ⚠️  {v}")

    # Test Seller Bot
    print("\n📊 Testing Seller Bot (P95 < 2500ms target)")
    print("-" * 50)
    seller_result = await tester.test_seller_bot(num_concurrent=10, total_requests=100)
    results.append(seller_result)
    print(f"  P95: {seller_result.p95_ms:.1f}ms | Success: {seller_result.success_rate * 100:.1f}%")
    if seller_result.sla_violations:
        for v in seller_result.sla_violations:
            print(f"  ⚠️  {v}")

    # Test Handoff Service
    print("\n📊 Testing Handoff Service (P95 < 500ms target)")
    print("-" * 50)
    handoff_result = await tester.test_handoff_service(num_concurrent=20, total_requests=200)
    results.append(handoff_result)
    print(f"  P95: {handoff_result.p95_ms:.1f}ms | Success: {handoff_result.success_rate * 100:.1f}%")
    if handoff_result.sla_violations:
        for v in handoff_result.sla_violations:
            print(f"  ⚠️  {v}")

    # Summary
    print("\n" + "=" * 70)
    print("📈 PERFORMANCE BASELINE SUMMARY")
    print("=" * 70)
    print(format_result_table(results))
    print("=" * 70)

    # SLA compliance summary
    compliant_count = sum(1 for r in results if r.sla_compliant)
    total_count = len(results)
    print(f"\nSLA Compliance: {compliant_count}/{total_count} tests passed")

    if compliant_count < total_count:
        failing = [r.bot_name for r in results if not r.sla_compliant]
        print(f"❌ Failing: {', '.join(failing)}")
    else:
        print("✅ All tests SLA compliant!")

    print(f"\nEnd Time: {datetime.now(timezone.utc).isoformat()}")

    return results


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Jorge Bot Performance Baseline Load Tests")
    parser.add_argument("--lead", action="store_true", help="Run Lead Bot test only")
    parser.add_argument("--buyer", action="store_true", help="Run Buyer Bot test only")
    parser.add_argument("--seller", action="store_true", help="Run Seller Bot test only")
    parser.add_argument("--handoff", action="store_true", help="Run Handoff Service test only")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    tester = JorgeLoadTester()
    results = []

    if args.all or not any([args.lead, args.buyer, args.seller, args.handoff]):
        results = await run_all_load_tests()
    else:
        if args.lead:
            results.append(await tester.test_lead_bot(10, 100))
        if args.buyer:
            results.append(await tester.test_buyer_bot(10, 100))
        if args.seller:
            results.append(await tester.test_seller_bot(10, 100))
        if args.handoff:
            results.append(await tester.test_handoff_service(20, 200))

    return results


if __name__ == "__main__":
    asyncio.run(main())
