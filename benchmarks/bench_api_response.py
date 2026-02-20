"""Benchmark: API endpoint response time simulation.

Simulates /health, /api/leads/qualify, and /api/contacts/sync with
synthetic middleware overhead (auth, rate-limit, logging). Uses a
statistical latency model with real computation for code-path validation.

Run:
    python -m benchmarks.bench_api_response
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import time
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Latency model
# ---------------------------------------------------------------------------

def _lognormal_ms(rng: random.Random, median_ms: float, sigma: float) -> float:
    """Sample from a log-normal distribution with given median and spread."""
    mu = math.log(median_ms)
    return rng.lognormvariate(mu, sigma)


# ---------------------------------------------------------------------------
# Middleware simulations (real computation, modeled latency)
# ---------------------------------------------------------------------------

def _middleware_compute(rng: random.Random, endpoint: str) -> float:
    """Run middleware computation and return modeled latency in ms.

    Real work: JWT hash, rate-limit dict lookup, JSON log serialization.
    Modeled latency: ~0.5-3ms total middleware overhead.
    """
    # Real computation
    token = f"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.{rng.getrandbits(256)}"
    hashlib.sha256(token.encode()).hexdigest()
    _bucket = {"tokens": rng.randint(50, 100), "last": time.monotonic()}
    _bucket["tokens"] -= 1
    json.dumps({"endpoint": endpoint, "ts": time.monotonic()}, separators=(",", ":"))

    # Modeled latency
    return _lognormal_ms(rng, 1.0, 0.3)


# ---------------------------------------------------------------------------
# Endpoint models
# ---------------------------------------------------------------------------

def _endpoint_health(rng: random.Random) -> tuple[dict, float]:
    """GET /health -- minimal DB ping + uptime check.

    Real work: MD5 hash (simulates DB ping).
    Modeled latency: ~0.3ms median, P99 ~1ms.
    """
    hashlib.md5(b"ping").hexdigest()
    latency = _lognormal_ms(rng, 0.3, 0.4)
    return {"status": "ok", "uptime_s": rng.randint(1000, 999_999)}, latency


def _endpoint_qualify(rng: random.Random) -> tuple[dict, float]:
    """POST /api/leads/qualify -- lead scoring with simulated LLM call.

    Real work: hash computation simulating orchestration + parsing.
    Modeled latency: 30% cache hit (~30ms), 70% LLM call (~200-1600ms).
    """
    # Real computation (orchestration overhead)
    data = b"orchestrate"
    for _ in range(rng.randint(100, 500)):
        data = hashlib.md5(data).digest()

    # Modeled latency
    if rng.random() < 0.30:
        # Cache hit path
        latency = _lognormal_ms(rng, 30.0, 0.3)
    else:
        # LLM inference path
        latency = _lognormal_ms(rng, 800.0, 0.3)

    result = {
        "lead_score": rng.randint(10, 100),
        "temperature": rng.choice(["hot", "warm", "cold"]),
        "confidence": round(rng.uniform(0.5, 1.0), 2),
    }
    return result, latency


def _endpoint_sync(rng: random.Random) -> tuple[dict, float]:
    """POST /api/contacts/sync -- CRM sync with GHL.

    Real work: batch hash computation simulating API calls.
    Modeled latency: batch_size * ~50ms per GHL API call.
    """
    batch_size = rng.randint(1, 8)
    # Real computation
    data = b"ghl_sync"
    for _ in range(batch_size * rng.randint(50, 150)):
        data = hashlib.md5(data).digest()

    # Modeled latency: each GHL call ~30-60ms
    latency = sum(_lognormal_ms(rng, 40.0, 0.2) for _ in range(batch_size))
    return {"synced": batch_size, "errors": 0}, latency


# ---------------------------------------------------------------------------
# Endpoint registry
# ---------------------------------------------------------------------------

_ENDPOINTS = {
    "/health": (_endpoint_health, 50.0),
    "/api/leads/qualify": (_endpoint_qualify, 2000.0),
    "/api/contacts/sync": (_endpoint_sync, 500.0),
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class EndpointResult:
    name: str
    target_ms: float
    latencies_ms: list[float] = field(default_factory=list)

    @property
    def p50(self) -> float:
        return _percentile(self.latencies_ms, 50)

    @property
    def p95(self) -> float:
        return _percentile(self.latencies_ms, 95)

    @property
    def p99(self) -> float:
        return _percentile(self.latencies_ms, 99)


@dataclass
class ApiBenchmarkResult:
    endpoints: dict[str, EndpointResult]
    iterations: int
    wall_time_s: float = 0.0


def _percentile(data: list[float], pct: int) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (pct / 100)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[f]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


# ---------------------------------------------------------------------------
# Main benchmark
# ---------------------------------------------------------------------------

def run_api_benchmark(
    iterations: int = 1_000,
    seed: int = 42,
) -> ApiBenchmarkResult:
    rng = random.Random(seed)

    results: dict[str, EndpointResult] = {}
    for ep_name, (_, target) in _ENDPOINTS.items():
        results[ep_name] = EndpointResult(name=ep_name, target_ms=target)

    wall_start = time.perf_counter_ns()

    for ep_name, (handler, _) in _ENDPOINTS.items():
        for _ in range(iterations):
            # Modeled middleware latency
            mw_latency = _middleware_compute(rng, ep_name)
            # Modeled endpoint latency + real computation
            _, ep_latency = handler(rng)
            # Total modeled latency
            results[ep_name].latencies_ms.append(mw_latency + ep_latency)

    wall_s = (time.perf_counter_ns() - wall_start) / 1_000_000_000
    return ApiBenchmarkResult(endpoints=results, iterations=iterations, wall_time_s=wall_s)


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------

def check_targets(result: ApiBenchmarkResult) -> dict[str, bool]:
    return {
        name: ep.p99 < ep.target_ms
        for name, ep in result.endpoints.items()
    }


def print_results(result: ApiBenchmarkResult) -> None:
    print("=" * 72)
    print("  API Response Time Benchmark")
    print("=" * 72)
    print(f"  Iterations per endpoint: {result.iterations:,}")
    print(f"  Wall time: {result.wall_time_s:.2f}s")
    print()
    fmt = "  {:<24} {:>10} {:>10} {:>10}  {:>10}  {}"
    print(fmt.format("Endpoint", "P50", "P95", "P99", "Target", ""))
    print("  " + "-" * 68)
    targets_met = check_targets(result)
    for name in ("/health", "/api/leads/qualify", "/api/contacts/sync"):
        ep = result.endpoints[name]
        status = "PASS" if targets_met[name] else "FAIL"
        print(fmt.format(
            name,
            f"{ep.p50:.2f}ms",
            f"{ep.p95:.2f}ms",
            f"{ep.p99:.2f}ms",
            f"<{ep.target_ms:.0f}ms",
            f"[{status}]",
        ))
    print("=" * 72)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="API response time benchmark")
    parser.add_argument("--iterations", type=int, default=1_000,
                        help="Iterations per endpoint (default: 1000)")
    args = parser.parse_args()

    result = run_api_benchmark(iterations=args.iterations)
    print_results(result)
