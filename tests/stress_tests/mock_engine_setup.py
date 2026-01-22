
import asyncio
import time
import statistics
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Absolute path to competitive-intelligence-engine/src
ENGINE_SRC = os.path.join(os.getcwd(), "competitive-intelligence-engine", "src")
sys.path.insert(0, ENGINE_SRC)

# Mock modules to provide required classes
class MockModule:
    pass

# We don't need sys.modules hacks if we mock the classes before import
# or provide them in a way the engine can find them.
# But since the engine does 'from core.event_bus import EventBus',
# we need 'core.event_bus' to be importable or mocked in sys.modules.

def mock_sys_module(name, classes):
    m = MockModule()
    for cl in classes:
        setattr(m, cl.__name__, cl)
    sys.modules[name] = m

class EventBus:
    async def publish(self, event, data): pass

class AIClient:
    async def generate_strategic_response(self, prompt):
        return "1. Strategy A\n2. Strategy B"

class ExecutiveAnalyticsEngine: pass

class DeepLearningForecaster:
    async def predict_regulatory_violation(self, features, area):
        await asyncio.sleep(0.01) # 10ms processing
        return 0.85

mock_sys_module("core.event_bus", [EventBus])
mock_sys_module("core.ai_client", [AIClient])
mock_sys_module("analytics.executive_analytics_engine", [ExecutiveAnalyticsEngine])
mock_sys_module("prediction.deep_learning_forecaster", [DeepLearningForecaster])

# Also need to mock the packages themselves if they are imported
mock_sys_module("core", [])
mock_sys_module("analytics", [])
mock_sys_module("prediction", [])

# Now we can import the engine
from regulatory_intelligence.compliance_prediction_engine import (
    CompliancePredictionEngine, RegulatoryArea, RegulatoryJurisdiction
)

async def simulate_compliance_check(engine: CompliancePredictionEngine):
    """Simulates a single bot compliance check during an SMS interaction."""
    start_time = time.time()
    
    business_context = {"regulatory_exposure": 0.6, "compliance_maturity": 0.8}
    competitor_actions = [{"competitor_id": "comp_1", "action": "aggressive_expansion"}]
    
    try:
        # Core prediction logic
        risks = await engine.predict_compliance_violations(
            business_context=business_context,
            competitor_actions=competitor_actions,
            time_horizon_months=6
        )
        
        latency = (time.time() - start_time) * 1000
        return {"success": True, "latency_ms": latency, "risks_found": len(risks)}
    except Exception as e:
        return {"success": False, "error": str(e), "latency_ms": (time.time() - start_time) * 1000}

async def run_stress_test(concurrent_users: int = 50, total_requests: int = 250):
    print(f"\n🚀 Starting Compliance Engine Stress Test")
    print(f"Concurrency: {concurrent_users} users")
    print(f"Total Requests: {total_requests}")
    print("-" * 40)

    engine = CompliancePredictionEngine(
        event_bus=EventBus(),
        ai_client=AIClient(),
        analytics_engine=ExecutiveAnalyticsEngine(),
        forecaster=DeepLearningForecaster()
    )

    start_time = time.time()
    results = []
    
    for i in range(0, total_requests, concurrent_users):
        batch_size = min(concurrent_users, total_requests - i)
        batch = [simulate_compliance_check(engine) for _ in range(batch_size)]
        batch_results = await asyncio.gather(*batch)
        results.extend(batch_results)
        await asyncio.sleep(0.02) # Small network-like jitter

    total_duration = time.time() - start_time
    
    latencies = [r["latency_ms"] for r in results if r["success"]]
    errors = [r for r in results if not r["success"]]
    
    if not latencies:
        print("❌ All requests failed.")
        if errors: print(f"Sample Error: {errors[0]['error']}")
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

if __name__ == "__main__":
    c = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    t = int(sys.argv[2]) if len(sys.argv) > 2 else 250
    asyncio.run(run_stress_test(c, t))