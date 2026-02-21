#!/usr/bin/env python3
"""Validate revenue-ops artifacts required for repeatable proposal delivery."""

from __future__ import annotations

import csv
from pathlib import Path

REQUIRED_FILES = [
    Path("proposals/starter-sprint-one-pager.md"),
    Path("proposals/growth-sprint-one-pager.md"),
    Path("proposals/scale-sprint-one-pager.md"),
    Path("proposals/SOW_TEMPLATE.md"),
    Path("proposals/demo_scripts.md"),
    Path("reports/proposal_pipeline_tracker.csv"),
    Path("reports/metrics_snapshot.md"),
]

REQUIRED_CSV_HEADERS = [
    "week_start",
    "lead_name",
    "segment",
    "status",
    "proposal_sent_at",
    "package",
    "deal_value",
    "close_probability",
    "next_action",
    "owner",
]


def main() -> int:
    errors: list[str] = []

    for path in REQUIRED_FILES:
        if not path.exists():
            errors.append(f"Missing required artifact: {path}")

    tracker = Path("reports/proposal_pipeline_tracker.csv")
    if tracker.exists():
        with tracker.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, [])
        if header != REQUIRED_CSV_HEADERS:
            errors.append("proposal_pipeline_tracker.csv header does not match required schema")

    if errors:
        print("Revenue ops QA failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("Revenue ops QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
