"""EnterpriseHub Performance Benchmarks

Measures key performance characteristics without requiring external services.
All benchmarks use mock data and in-memory operations for reproducibility.
"""
import time
import statistics
import json
from pathlib import Path


def benchmark_cache_operations():
    """Benchmark L1 in-memory cache performance."""
    cache = {}
    times = []
    for i in range(10000):
        key = f"conv_{i % 100}:msg_{i}"
        start = time.perf_counter()
        cache[key] = {"response": f"cached_response_{i}", "tokens": 150}
        _ = cache.get(key)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    return {
        "operation": "L1 Cache Read/Write",
        "iterations": 10000,
        "p50_ms": round(statistics.median(times), 4),
        "p95_ms": round(sorted(times)[int(len(times) * 0.95)], 4),
        "p99_ms": round(sorted(times)[int(len(times) * 0.99)], 4),
        "ops_per_sec": round(len(times) / (sum(times) / 1000), 1),
    }


def benchmark_json_parsing():
    """Benchmark response parsing throughput."""
    sample_response = json.dumps({
        "confidence": 0.85,
        "temperature": "hot",
        "handoff_signals": ["budget_mentioned", "pre_approval"],
        "recommended_actions": [
            {"action": "schedule_showing", "priority": "high"},
            {"action": "send_listings", "priority": "medium"},
        ],
        "risk_factors": [{"factor": "timeline_pressure", "severity": "medium"}],
    })
    times = []
    for _ in range(10000):
        start = time.perf_counter()
        parsed = json.loads(sample_response)
        _ = parsed.get("confidence", 0)
        _ = parsed.get("handoff_signals", [])
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    return {
        "operation": "Response JSON Parsing",
        "iterations": 10000,
        "p50_ms": round(statistics.median(times), 4),
        "p95_ms": round(sorted(times)[int(len(times) * 0.95)], 4),
        "p99_ms": round(sorted(times)[int(len(times) * 0.99)], 4),
        "ops_per_sec": round(len(times) / (sum(times) / 1000), 1),
    }


def benchmark_lead_scoring():
    """Benchmark lead temperature scoring computation."""
    import random
    random.seed(42)
    times = []
    for _ in range(5000):
        engagement = random.uniform(0, 100)
        recency_days = random.randint(0, 90)
        tag_count = random.randint(0, 15)
        start = time.perf_counter()
        # Scoring algorithm
        base = engagement * 0.4
        recency_factor = max(0, 1 - (recency_days / 90)) * 30
        tag_boost = min(tag_count * 2, 20)
        score = min(100, base + recency_factor + tag_boost)
        if score >= 80:
            temp = "hot"
        elif score >= 40:
            temp = "warm"
        else:
            temp = "cold"
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    return {
        "operation": "Lead Temperature Scoring",
        "iterations": 5000,
        "p50_ms": round(statistics.median(times), 4),
        "p95_ms": round(sorted(times)[int(len(times) * 0.95)], 4),
        "p99_ms": round(sorted(times)[int(len(times) * 0.99)], 4),
        "ops_per_sec": round(len(times) / (sum(times) / 1000), 1),
    }


def benchmark_handoff_evaluation():
    """Benchmark handoff decision logic."""
    import re
    patterns = {
        "buyer": [r"(?i)want to buy", r"(?i)budget \$", r"(?i)pre.?approv"],
        "seller": [r"(?i)sell my", r"(?i)home worth", r"(?i)\bcma\b"],
    }
    messages = [
        "I want to buy a house with a budget of $500k",
        "Can you tell me what my home is worth?",
        "Just browsing listings in Rancho Cucamonga",
        "I have pre-approval from my bank for $600k",
        "I want to sell my house and need a CMA",
    ]
    times = []
    for _ in range(5000):
        for msg in messages:
            start = time.perf_counter()
            scores = {}
            for direction, pats in patterns.items():
                hits = sum(1 for p in pats if re.search(p, msg))
                scores[direction] = hits / len(pats)
            best = max(scores, key=scores.get)
            confidence = scores[best]
            should_handoff = confidence >= 0.7
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
    return {
        "operation": "Handoff Evaluation",
        "iterations": 25000,
        "p50_ms": round(statistics.median(times), 4),
        "p95_ms": round(sorted(times)[int(len(times) * 0.95)], 4),
        "p99_ms": round(sorted(times)[int(len(times) * 0.99)], 4),
        "ops_per_sec": round(len(times) / (sum(times) / 1000), 1),
    }


def main():
    print("=" * 60)
    print("EnterpriseHub Performance Benchmarks")
    print("=" * 60)
    benchmarks = [
        benchmark_cache_operations,
        benchmark_json_parsing,
        benchmark_lead_scoring,
        benchmark_handoff_evaluation,
    ]
    results = []
    for bench in benchmarks:
        print(f"\nRunning {bench.__doc__.strip()}...")
        result = bench()
        results.append(result)
        print(f"  P50: {result['p50_ms']}ms | P95: {result['p95_ms']}ms | P99: {result['p99_ms']}ms")
        print(f"  Throughput: {result['ops_per_sec']} ops/sec")

    # Write results markdown
    output = Path(__file__).parent / "RESULTS.md"
    with open(output, "w") as f:
        f.write("# EnterpriseHub Benchmark Results\n\n")
        f.write(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("**Python**: 3.11+\n\n")
        f.write("| Operation | Iterations | P50 (ms) | P95 (ms) | P99 (ms) | Throughput |\n")
        f.write("|-----------|-----------|----------|----------|----------|------------|\n")
        for r in results:
            f.write(f"| {r['operation']} | {r['iterations']:,} | {r['p50_ms']} | {r['p95_ms']} | {r['p99_ms']} | {r['ops_per_sec']:,.0f} ops/sec |\n")
        f.write("\n> All benchmarks use mock data for reproducibility. No external services required.\n")
    print(f"\nResults written to {output}")


if __name__ == "__main__":
    main()
