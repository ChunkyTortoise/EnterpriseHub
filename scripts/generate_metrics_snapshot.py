#!/usr/bin/env python3
"""Generate weekly proof-pack metrics snapshot markdown."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def _git_ref() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def _load_coverage(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports/metrics_snapshot.md")
    parser.add_argument("--coverage-json", default="coverage.json")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    coverage = _load_coverage(Path(args.coverage_json))

    totals = coverage.get("totals", {}) if isinstance(coverage, dict) else {}
    covered = totals.get("covered_lines", "n/a")
    lines = totals.get("num_statements", "n/a")
    pct = totals.get("percent_covered", "n/a")

    report = f"""# Weekly Metrics Snapshot\n\n- Generated at (UTC): {now.isoformat()}\n- Git commit: `{_git_ref()}`\n- Coverage lines: {covered}/{lines}\n- Coverage percent: {pct}\n\n## Trust Gates\n\n- Parse/compile gate: `scripts/ci/compile_check.py`\n- No-mock production gate: `scripts/ci/no_mock_in_prod.py`\n\n## Revenue Ops Placeholder\n\n- Proposals sent this week: TODO\n- Qualified conversations this week: TODO\n- Deals closed this week: TODO\n- Pilot MRR: TODO\n"""

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
