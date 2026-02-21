#!/usr/bin/env python3
"""Compile tracked Python modules to catch syntax/parse regressions early."""

from __future__ import annotations

import argparse
import py_compile
import sys
from pathlib import Path

DEFAULT_TARGETS = [
    "ghl_real_estate_ai/api/routes/market_intelligence.py",
    "ghl_real_estate_ai/api/schemas/white_label.py",
    "ghl_real_estate_ai/services/learning/test_behavior_tracking.py",
    "ghl_real_estate_ai/api/routes/revenue_v2.py",
    "ghl_real_estate_ai/api/schemas/revenue_v2.py",
]


def _expand_targets(raw_targets: list[str]) -> list[Path]:
    expanded: list[Path] = []
    for raw in raw_targets:
        path = Path(raw)
        if path.is_dir():
            expanded.extend(sorted(path.rglob("*.py")))
        elif path.suffix == ".py":
            expanded.append(path)
    # de-duplicate while preserving order
    seen = set()
    unique = []
    for path in expanded:
        key = str(path)
        if key not in seen:
            unique.append(path)
            seen.add(key)
    return unique


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="*", default=DEFAULT_TARGETS)
    args = parser.parse_args()

    targets = _expand_targets(args.targets)
    failures: list[str] = []

    for target in targets:
        if not target.exists():
            failures.append(f"missing: {target}")
            continue
        try:
            py_compile.compile(str(target), doraise=True)
        except py_compile.PyCompileError as exc:
            failures.append(f"{target}: {exc.msg}")

    if failures:
        print("Compile check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Compile check passed ({len(targets)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
