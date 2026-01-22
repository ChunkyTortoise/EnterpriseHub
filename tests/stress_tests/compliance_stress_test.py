
import asyncio
import time
import statistics
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from decimal import Decimal

# Add current directory to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "competitive-intelligence-engine", "src"))

from regulatory_intelligence.compliance_prediction_engine import (
    CompliancePredictionEngine, RegulatoryArea, RegulatoryJurisdiction
)
# Mock dependencies for the engine
class MockEventBus:
    async def publish(self, event, data): pass

class MockAIClient:
    async def generate_strategic_response(self, prompt):
        return "1. Strategy A\n2. Strategy B"

class MockAnalyticsEngine: pass

class MockForecaster:
    async def predict_regulatory_violation(self, features, area):
        # Simulate some processing time
        await asyncio.sleep(0.01) # 10ms processing
        return 0.85

async def simulate_compliance_check(engine: CompliancePredictionEngine, user_id: int):
    """Simulates a single bot compliance check during an SMS interaction."""
    start_time = time.time()
    
    # Simulate data for prediction
    business_context = {"regulatory_exposure": 0.6, "compliance_maturity": 0.8}
    competitor_actions = [{"competitor_id": "comp_1", "action": "aggressive_expansion"}]
    
    try:
        # We call the core prediction logic
        risks = await engine.predict_compliance_violations(
            business_context=business_context,
            competitor_actions=competitor_actions,
            time_horizon_months=6
        )
        
        latency = (time.time() - start_time) * 1000
        return {"success": True, "latency_ms": latency, "risks_found": len(risks)}
    except Exception as e:
        return {"success": False, "error": str(e), "latency_ms": (time.time() - start_time) * 1000}

async def run_compliance_stress_test(concurrent_users: int = 50, total_requests: int = 200):
    """Runs a stress test on the CompliancePredictionEngine."""
    print(f"\n🚀 Starting Compliance Engine Stress Test")
    print(f"Concurrency: {concurrent_users} users")
    print(f"Total Requests: {total_requests}")
    print("-" * 40)

    # Initialize Engine with mocks
    engine = CompliancePredictionEngine(
        event_bus=MockEventBus(),
        ai_client=MockAIClient(),
        analytics_engine=MockAnalyticsEngine(),
        forecaster=MockForecaster()
    )

    # Pre-warm (initialize caches if any)
    # The current implementation initializes models in __init__

    start_time = time.time()
    tasks = []
    
    # Semi-gradual ramp up (batches)
    results = []
    for i in range(0, total_requests, concurrent_users):
        batch = [simulate_compliance_check(engine, j) for j in range(i, min(i + concurrent_users, total_requests))]
        batch_results = await asyncio.gather(*batch)
        results.extend(batch_results)
        # Small sleep between batches to simulate SMS arrival patterns
        await asyncio.sleep(0.05)

    total_duration = time.time() - start_time
    
    # Process Results
    latencies = [r["latency_ms"] for r in results if r["success"]]
    errors = [r for r in results if not r["success"]]
    
    if not latencies:
        print("❌ All requests failed.")
        return

    avg_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
    throughput = len(results) / total_duration

    print("\n--- RESULTS ---")
    print(f"Total Requests: {len(results)}")
    print(f"Successful: {len(latencies)}")
    print(f"Failed: {len(errors)}")
    print(f"Throughput: {throughput:.2f} req/sec")
    print(f"Avg Latency: {avg_latency:.2f}ms")
    print(f"P95 Latency: {p95_latency:.2f}ms")
    print(f"Total Duration: {total_duration:.2f}s")
    
    if p95_latency < 100:
        print("\n✅ PERFORMANCE PASSED: P95 latency is below 100ms threshold.")
    else:
        print("\n⚠️  PERFORMANCE WARNING: P95 latency exceeded 100ms threshold.")

    if errors:
        print("\n--- ERRORS ---")
        for err in errors[:5]:
            print(f"Error: {err['error']}")

if __name__ == "__main__":
    # Ensure directory exists
    os.makedirs("tests/stress_tests", exist_ok=True)
    
    concurrency = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    total = int(sys.argv[2]) if len(sys.argv) > 2 else 250
    
    asyncio.run(run_compliance_stress_test(concurrency, total))
