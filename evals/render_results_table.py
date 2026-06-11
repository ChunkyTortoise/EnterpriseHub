"""Publish nightly eval results: latest_results.json, badge.json, README block.

Usage: python evals/render_results_table.py <eval-results.json> [README.md]

Reads a pytest-json-report file from the nightly eval run, then writes:
  - evals/latest_results.json  (pass rate, counts, timestamp)
  - evals/badge.json           (shields.io endpoint schema)
  - rewrites the <!-- EVAL-RESULTS:START --> block in README.md

Designed to run with `if: always()` in CI so a regression night still updates
the badge instead of leaving a stale green number.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

EVALS_DIR = Path(__file__).parent
START_MARKER = "<!-- EVAL-RESULTS:START -->"
END_MARKER = "<!-- EVAL-RESULTS:END -->"


def _badge_color(pass_rate: float) -> str:
    if pass_rate >= 0.9:
        return "brightgreen"
    if pass_rate >= 0.75:
        return "yellow"
    return "red"


def publish(results_path: str, readme_path: str = "README.md") -> None:
    report = json.loads(Path(results_path).read_text())
    summary = report.get("summary", {})
    total = summary.get("total", 0)
    passed = summary.get("passed", 0)
    pass_rate = passed / total if total else 0.0
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    baseline = json.loads((EVALS_DIR / "baseline.json").read_text())

    latest = {
        "generated": generated,
        "total": total,
        "passed": passed,
        "pass_rate": round(pass_rate, 4),
        "baseline_rubrics": baseline.get("rubrics", {}),
    }
    (EVALS_DIR / "latest_results.json").write_text(json.dumps(latest, indent=2) + "\n")

    badge = {
        "schemaVersion": 1,
        "label": "nightly eval",
        "message": f"{passed}/{total} pass ({pass_rate:.0%})",
        "color": _badge_color(pass_rate),
    }
    (EVALS_DIR / "badge.json").write_text(json.dumps(badge, indent=2) + "\n")

    readme = Path(readme_path)
    if readme.exists():
        rubric_rows = "\n".join(
            f"| {name.capitalize()} | {score:.0%} |" for name, score in baseline.get("rubrics", {}).items()
        )
        block = (
            f"{START_MARKER}\n"
            f"**Nightly eval (last run {generated}):** {passed}/{total} harness checks pass "
            f"({pass_rate:.0%}). Baseline LLM-judge rubric scores on the 50-case golden dataset:\n\n"
            f"| Rubric | Baseline |\n|---|---|\n{rubric_rows}\n"
            f"{END_MARKER}"
        )
        content = readme.read_text()
        pattern = re.compile(re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL)
        if pattern.search(content):
            readme.write_text(pattern.sub(block, content))
            print(f"README block updated ({passed}/{total}, {pass_rate:.0%})")
        else:
            print("README markers not found; skipped README update")

    print(f"Wrote {EVALS_DIR / 'latest_results.json'} and {EVALS_DIR / 'badge.json'}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <eval-results.json> [README.md]")
        sys.exit(2)
    publish(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "README.md")
