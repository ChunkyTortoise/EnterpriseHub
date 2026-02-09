"""Runner: execute all benchmarks and print a summary table.

Run:
    python -m benchmarks.run_all [--iterations N]

Exit code 0 if all targets met, 1 if any missed.
"""

from __future__ import annotations

import argparse
import sys
import time

from benchmarks.bench_cache import (
    run_cache_benchmark,
    check_targets as check_cache,
    print_results as print_cache,
)
from benchmarks.bench_orchestration import (
    run_orchestration_benchmark,
    check_targets as check_orchestration,
    print_results as print_orchestration,
)
from benchmarks.bench_api_response import (
    run_api_benchmark,
    check_targets as check_api,
    print_results as print_api,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run all EnterpriseHub synthetic benchmarks"
    )
    parser.add_argument(
        "--iterations", type=int, default=1_000,
        help="Base iteration count (default: 1000; cache uses 10x)",
    )
    args = parser.parse_args()

    all_pass = True
    wall_start = time.perf_counter()

    # ---- Cache benchmark (10x iterations for statistical significance) ----
    print()
    cache_result = run_cache_benchmark(iterations=args.iterations * 10)
    print_cache(cache_result)
    cache_targets = check_cache(cache_result)
    if not all(cache_targets.values()):
        all_pass = False

    # ---- Orchestration benchmark ----
    print()
    orch_result = run_orchestration_benchmark(iterations=args.iterations)
    print_orchestration(orch_result)
    orch_targets = check_orchestration(orch_result)
    if not all(orch_targets.values()):
        all_pass = False

    # ---- API benchmark ----
    print()
    api_result = run_api_benchmark(iterations=args.iterations)
    print_api(api_result)
    api_targets = check_api(api_result)
    if not all(api_targets.values()):
        all_pass = False

    # ---- Summary ----
    wall_elapsed = time.perf_counter() - wall_start
    print()
    print("=" * 72)
    print("  SUMMARY")
    print("=" * 72)
    fmt = "  {:<36} {:<10} {}"
    print(fmt.format("Check", "Result", "Detail"))
    print("  " + "-" * 68)

    def _row(name: str, passed: bool, detail: str = "") -> None:
        print(fmt.format(name, "PASS" if passed else "FAIL", detail))

    # Cache rows
    _row("Cache L1 P99 < 1ms", cache_targets["L1_p99_ms"],
         f"{cache_result.tiers['L1'].p99:.2f}ms")
    _row("Cache L2 P99 < 5ms", cache_targets["L2_p99_ms"],
         f"{cache_result.tiers['L2'].p99:.2f}ms")
    _row("Cache L3 P99 < 20ms", cache_targets["L3_p99_ms"],
         f"{cache_result.tiers['L3'].p99:.2f}ms")
    _row("Cache hit rate >= 87%", cache_targets["hit_rate"],
         f"{cache_result.hit_rate:.1%}")

    # Orchestration rows
    _row("Orchestration total P99 < 200ms", orch_targets["total_p99_ms"],
         f"{orch_result.p99:.4f}ms")

    # API rows
    for ep_name, passed in api_targets.items():
        ep = api_result.endpoints[ep_name]
        _row(f"API {ep_name} P99 < {ep.target_ms:.0f}ms", passed,
             f"{ep.p99:.2f}ms")

    print("  " + "-" * 68)
    total_checks = (
        len(cache_targets) + len(orch_targets) + len(api_targets)
    )
    passed_checks = (
        sum(cache_targets.values())
        + sum(orch_targets.values())
        + sum(api_targets.values())
    )
    overall = "ALL PASSED" if all_pass else "SOME FAILED"
    print(f"  {passed_checks}/{total_checks} checks passed  [{overall}]")
    print(f"  Wall time: {wall_elapsed:.1f}s")
    print("=" * 72)

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
