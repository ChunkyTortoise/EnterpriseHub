"""Driver: run bench_cache_live and write a committed JSON artifact.

This script is intentionally standalone (not wired into run_all.py) so it
can be run independently and re-executed without affecting other benchmark
streams.

Usage:
    python -m benchmarks.drive_cache_live
    python -m benchmarks.drive_cache_live --out benchmarks/results/cache_live_custom.json
    python -m benchmarks.drive_cache_live --ops 5000 --hot-keys 50

Exit codes:
    0  all performance targets met
    1  one or more targets missed (artifact still written)
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from benchmarks.bench_cache_live import (
    check_targets,
    print_results,
    result_to_dict,
    run_live_benchmark,
    write_json_out,
)

DEFAULT_OUT = "benchmarks/results/cache_live_2026-05-27.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run live cache benchmark and write JSON artifact"
    )
    parser.add_argument("--out", default=DEFAULT_OUT, metavar="PATH",
                        help=f"Output JSON path (default: {DEFAULT_OUT})")
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

    # Write JSON before printing so the artifact is always produced
    # regardless of whether targets are met (print_results exits on miss).
    write_json_out(
        result,
        args.out,
        ops=args.ops,
        hot_keys=args.hot_keys,
        cold_keys=args.cold_keys,
        hot_ratio=args.hot_ratio,
    )

    print_results(result)  # exits 1 on target miss; that is intentional

    return 0


if __name__ == "__main__":
    sys.exit(main())
