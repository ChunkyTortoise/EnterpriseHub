"""Compare eval results against baseline. Exit 1 if any rubric drops >10%."""
from __future__ import annotations

import json
import sys


def compare(results_path: str, baseline_path: str) -> None:
    with open(results_path) as f:
        report = json.load(f)
    with open(baseline_path) as f:
        baseline = json.load(f)

    baseline_rubrics = baseline.get("rubrics", {})
    if not baseline_rubrics:
        print("No baseline rubrics found -- skipping comparison.")
        return

    # Extract pass rate from pytest-json-report
    summary = report.get("summary", {})
    total = summary.get("total", 0)
    passed = summary.get("passed", 0)
    pass_rate = passed / total if total > 0 else 0.0

    print(f"Test results: {passed}/{total} passed ({pass_rate:.1%})")
    print(f"Baseline rubrics: {baseline_rubrics}")

    regressions: list[str] = []

    # Check overall pass rate against average baseline
    avg_baseline = sum(baseline_rubrics.values()) / len(baseline_rubrics)
    if pass_rate < avg_baseline - 0.10:
        regressions.append(
            f"Overall pass rate {pass_rate:.2f} dropped >10% below "
            f"baseline average {avg_baseline:.2f}"
        )

    if regressions:
        print("\nREGRESSIONS DETECTED:")
        for r in regressions:
            print(f"  - {r}")
        sys.exit(1)
    else:
        print("\nNo regressions detected. All scores within 10% of baseline.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <results.json> <baseline.json>")
        sys.exit(2)
    compare(sys.argv[1], sys.argv[2])
