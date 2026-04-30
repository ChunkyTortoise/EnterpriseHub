"""Live measurement of the L1/L2 tiered cache against real counters.

WHAT THIS IS:
    Runs actual get/set operations against TieredCacheService and reads
    empirical hit/miss counters directly from CacheMetrics. The reported
    hit rates are measured, not sampled from a design-target distribution.

WHAT THIS IS NOT:
    Not a simulation. Every number here reflects real code-path execution.
    Redis (L2) degrades gracefully if unavailable — L2 stats are omitted
    from the report when Redis is not reachable.

RUN:
    python -m benchmarks.bench_cache_live
    python -m benchmarks.bench_cache_live --ops 5000 --hot-keys 50
"""

from __future__ import annotations

import asyncio
import random
import sys
import time
from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Singleton reset helper
# ---------------------------------------------------------------------------
# TieredCacheService uses a class-level singleton. Reset it before each run
# so the metrics counters start at zero.

def _reset_singleton() -> None:
    from ghl_real_estate_ai.services import tiered_cache_service as _mod
    _mod.TieredCacheService._instance = None


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class LiveBenchResult:
    ops: int
    l1_hits: int
    l1_misses: int
    l2_hits: int
    l2_misses: int
    l2_enabled: bool
    wall_time_s: float

    @property
    def l1_hit_rate(self) -> float:
        total = self.l1_hits + self.l1_misses
        return self.l1_hits / total if total else 0.0

    @property
    def l2_hit_rate(self) -> float:
        total = self.l2_hits + self.l2_misses
        return self.l2_hits / total if total else 0.0

    @property
    def overall_hit_rate(self) -> float:
        hits = self.l1_hits + self.l2_hits
        total = hits + self.l2_misses  # a request misses overall only on L2 miss
        return hits / total if total else 0.0


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------


async def run_live_benchmark(
    ops: int = 2_000,
    hot_keys: int = 20,
    cold_keys: int = 200,
    hot_ratio: float = 0.70,
    ttl: int = 300,
    seed: int = 42,
) -> LiveBenchResult:
    """
    Measure real cache hit rates by running get/set against TieredCacheService.

    Workload:
      - hot_keys: frequently-accessed keys (hot_ratio of all reads)
      - cold_keys: infrequently-accessed keys (1 - hot_ratio of reads)
      - Warm phase seeds all hot_keys before measurement starts.
    """
    _reset_singleton()

    from ghl_real_estate_ai.services.tiered_cache_service import TieredCacheService

    cache = TieredCacheService()
    await cache.start()

    rng = random.Random(seed)
    hot_pool = [f"hot:{i}" for i in range(hot_keys)]
    cold_pool = [f"cold:{i}" for i in range(cold_keys)]

    # Warm phase: seed all hot keys so L1 has them
    for key in hot_pool:
        await cache.set(key, f"value:{key}", ttl=ttl)

    # Reset metrics so warm phase doesn't count
    from ghl_real_estate_ai.services.tiered_cache_service import CacheMetrics
    cache.metrics = CacheMetrics()
    cache.l1_cache.set_metrics_ref(cache.metrics)

    wall_start = time.perf_counter()

    for _ in range(ops):
        if rng.random() < hot_ratio:
            key = rng.choice(hot_pool)
        else:
            key = rng.choice(cold_pool)

        val: Any = await cache.get(key)
        if val is None:
            # Cache miss: populate so future reads can hit
            await cache.set(key, f"value:{key}", ttl=ttl)

    wall_time_s = time.perf_counter() - wall_start

    m = cache.metrics
    result = LiveBenchResult(
        ops=ops,
        l1_hits=m.l1_hits,
        l1_misses=m.l1_misses,
        l2_hits=m.l2_hits,
        l2_misses=m.l2_misses,
        l2_enabled=cache.l2_backend.enabled,
        wall_time_s=wall_time_s,
    )

    await cache.stop()
    return result


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------

TARGETS = {
    "l1_hit_rate": 0.60,   # ≥60% of reads served from memory
    "overall_hit_rate": 0.85,  # ≥85% overall (L1 + L2)
}


def check_targets(r: LiveBenchResult) -> dict[str, bool]:
    return {
        "l1_hit_rate": r.l1_hit_rate >= TARGETS["l1_hit_rate"],
        "overall_hit_rate": r.overall_hit_rate >= TARGETS["overall_hit_rate"],
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def print_results(r: LiveBenchResult) -> None:
    ok = check_targets(r)
    l2_note = "" if r.l2_enabled else "  (Redis unavailable — L2 stats not applicable)"

    print("=" * 64)
    print("  3-Tier Cache  —  LIVE MEASUREMENT  (not a simulation)")
    print("=" * 64)
    print(f"  Ops measured      : {r.ops:,}")
    print(f"  Wall time         : {r.wall_time_s:.2f}s  ({r.ops / r.wall_time_s:,.0f} ops/s)")
    print()
    print(f"  L1 (memory)  hits={r.l1_hits:,}  misses={r.l1_misses:,}  "
          f"hit_rate={r.l1_hit_rate:.1%}  "
          f"[{'PASS' if ok['l1_hit_rate'] else 'FAIL'} ≥{TARGETS['l1_hit_rate']:.0%}]")
    if r.l2_enabled:
        print(f"  L2 (Redis)   hits={r.l2_hits:,}  misses={r.l2_misses:,}  "
              f"hit_rate={r.l2_hit_rate:.1%}")
    else:
        print(f"  L2 (Redis)   {l2_note.strip()}")
    print()
    print(f"  Overall hit rate  : {r.overall_hit_rate:.1%}  "
          f"[{'PASS' if ok['overall_hit_rate'] else 'FAIL'} ≥{TARGETS['overall_hit_rate']:.0%}]")
    print("=" * 64)

    failed = [k for k, v in ok.items() if not v]
    if failed:
        print(f"\n  WARN: targets not met: {', '.join(failed)}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Live cache hit-rate measurement")
    parser.add_argument("--ops", type=int, default=2_000)
    parser.add_argument("--hot-keys", type=int, default=20)
    parser.add_argument("--cold-keys", type=int, default=200)
    parser.add_argument("--hot-ratio", type=float, default=0.70)
    args = parser.parse_args()

    result = asyncio.run(
        run_live_benchmark(
            ops=args.ops,
            hot_keys=args.hot_keys,
            cold_keys=args.cold_keys,
            hot_ratio=args.hot_ratio,
        )
    )
    print_results(result)
