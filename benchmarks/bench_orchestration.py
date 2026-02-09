"""Benchmark: Claude Orchestrator overhead simulation.

Measures the overhead of request routing, cache key generation, and
response parsing without making real LLM calls. Target: <200ms total.

Run:
    python -m benchmarks.bench_orchestration
"""

from __future__ import annotations

import hashlib
import json
import random
import re
import time
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Simulated orchestrator phases
# ---------------------------------------------------------------------------

# Task types the orchestrator classifies incoming requests into.
_TASK_TYPES = [
    "lead_qualification", "buyer_intent", "seller_intent",
    "general_inquiry", "scheduling", "property_search",
    "price_negotiation", "document_request",
]

# Model options selected based on task complexity.
_MODELS = ["haiku", "sonnet", "opus"]


def _phase_route(payload: dict) -> str:
    """Simulate task-type classification and model selection.

    In production this inspects the message, checks keyword heuristics,
    and picks a model. Here we simulate the CPU work with string ops.
    """
    text = payload.get("message", "")
    # Keyword scan (simulates regex + heuristic scoring)
    scores = {}
    for task in _TASK_TYPES:
        scores[task] = sum(1 for w in task.split("_") if w in text.lower())
    best = max(scores, key=scores.get)  # type: ignore[arg-type]

    # Model selection heuristic
    complexity = len(text)
    if complexity > 500:
        model = "opus"
    elif complexity > 200:
        model = "sonnet"
    else:
        model = "haiku"

    return f"{best}:{model}"


def _phase_cache_key(payload: dict) -> str:
    """Generate a deterministic cache key from the request payload."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


# Simulated LLM response bodies for multi-strategy parsing.
_RESPONSE_TEMPLATES = [
    # Clean JSON
    '{"intent": "buy", "confidence": 0.92, "entities": ["3br", "pool"]}',
    # JSON in markdown fence
    '```json\n{"intent": "sell", "confidence": 0.85, "entities": ["condo"]}\n```',
    # Plain text needing extraction
    'The lead is interested in buying a 4-bedroom house with a budget of $650k.',
    # JSON with trailing text
    '{"intent": "inquiry", "confidence": 0.78}\nAdditional notes here.',
    # Nested structure
    '{"response": {"text": "Hello!", "metadata": {"tokens": 42}}}',
]

_JSON_PATTERN = re.compile(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}")


def _phase_parse(raw_response: str) -> dict:
    """Multi-strategy JSON extraction from LLM response."""
    # Strategy 1: direct parse
    try:
        return json.loads(raw_response)
    except (json.JSONDecodeError, TypeError):
        pass

    # Strategy 2: extract from markdown fence
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw_response, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except (json.JSONDecodeError, TypeError):
            pass

    # Strategy 3: regex extraction of first JSON object
    json_match = _JSON_PATTERN.search(raw_response)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except (json.JSONDecodeError, TypeError):
            pass

    # Fallback: return raw text wrapped
    return {"raw_text": raw_response, "parsed": False}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class PhaseResult:
    name: str
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
class OrchestrationBenchmarkResult:
    phases: dict[str, PhaseResult]
    total_latencies_ms: list[float]
    iterations: int

    @property
    def p50(self) -> float:
        return _percentile(self.total_latencies_ms, 50)

    @property
    def p95(self) -> float:
        return _percentile(self.total_latencies_ms, 95)

    @property
    def p99(self) -> float:
        return _percentile(self.total_latencies_ms, 99)


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
# Synthetic payloads
# ---------------------------------------------------------------------------

_SAMPLE_MESSAGES = [
    "I want to buy a 3-bedroom house with a pool near Rancho Cucamonga",
    "What is my home worth? I'm thinking of selling my condo.",
    "Can you schedule a showing for 1234 Oak Street tomorrow at 2pm?",
    "I have a pre-approval for $500k and need something move-in ready",
    "Tell me about the school districts in the area",
    "I need help with the purchase agreement document",
    "Is the price negotiable on the listing at 567 Elm Ave?",
    "Hi, just browsing listings in the 91730 zip code",
]


def _make_payload(rng: random.Random) -> dict:
    msg = rng.choice(_SAMPLE_MESSAGES)
    return {
        "message": msg,
        "contact_id": f"contact_{rng.randint(1000, 9999)}",
        "channel": rng.choice(["sms", "web_chat", "email"]),
        "timestamp": f"2026-02-09T{rng.randint(0,23):02d}:{rng.randint(0,59):02d}:00Z",
    }


# ---------------------------------------------------------------------------
# Main benchmark
# ---------------------------------------------------------------------------

def run_orchestration_benchmark(
    iterations: int = 1_000,
    seed: int = 42,
) -> OrchestrationBenchmarkResult:
    rng = random.Random(seed)

    phases = {
        "routing": PhaseResult(name="routing"),
        "cache_key": PhaseResult(name="cache_key"),
        "parsing": PhaseResult(name="parsing"),
    }
    total_latencies: list[float] = []

    for _ in range(iterations):
        payload = _make_payload(rng)
        raw_response = rng.choice(_RESPONSE_TEMPLATES)

        total_start = time.perf_counter_ns()

        # Phase 1: routing
        start = time.perf_counter_ns()
        _phase_route(payload)
        phases["routing"].latencies_ms.append(
            (time.perf_counter_ns() - start) / 1_000_000
        )

        # Phase 2: cache key generation
        start = time.perf_counter_ns()
        _phase_cache_key(payload)
        phases["cache_key"].latencies_ms.append(
            (time.perf_counter_ns() - start) / 1_000_000
        )

        # Phase 3: response parsing
        start = time.perf_counter_ns()
        _phase_parse(raw_response)
        phases["parsing"].latencies_ms.append(
            (time.perf_counter_ns() - start) / 1_000_000
        )

        total_latencies.append(
            (time.perf_counter_ns() - total_start) / 1_000_000
        )

    return OrchestrationBenchmarkResult(
        phases=phases,
        total_latencies_ms=total_latencies,
        iterations=iterations,
    )


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------
TARGETS = {
    "total_p99_ms": 200.0,
}


def check_targets(result: OrchestrationBenchmarkResult) -> dict[str, bool]:
    return {
        "total_p99_ms": result.p99 < TARGETS["total_p99_ms"],
    }


def print_results(result: OrchestrationBenchmarkResult) -> None:
    print("=" * 62)
    print("  Orchestration Overhead Benchmark")
    print("=" * 62)
    print(f"  Iterations: {result.iterations:,}")
    print()
    fmt = "  {:<12} {:>10} {:>10} {:>10}"
    print(fmt.format("Phase", "P50", "P95", "P99"))
    print("  " + "-" * 44)
    for name in ("routing", "cache_key", "parsing"):
        p = result.phases[name]
        print(fmt.format(name, f"{p.p50:.4f}ms", f"{p.p95:.4f}ms", f"{p.p99:.4f}ms"))
    print("  " + "-" * 44)
    targets_met = check_targets(result)
    status = "PASS" if targets_met["total_p99_ms"] else "FAIL"
    print(fmt.format("TOTAL", f"{result.p50:.4f}ms", f"{result.p95:.4f}ms", f"{result.p99:.4f}ms"))
    print(f"\n  Target: <200ms total P99 [{status}]")
    print("=" * 62)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Orchestration overhead benchmark")
    parser.add_argument("--iterations", type=int, default=1_000,
                        help="Number of iterations (default: 1000)")
    args = parser.parse_args()

    result = run_orchestration_benchmark(iterations=args.iterations)
    print_results(result)
