#!/usr/bin/env python3
"""Fail CI if production v2 routes contain explicit mock/fallback behavior."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DEFAULT_TARGETS = [
    "ghl_real_estate_ai/api/routes/revenue_v2.py",
]

FORBIDDEN_PATTERNS = [
    re.compile(r"generate_mock", re.IGNORECASE),
    re.compile(r"\bmock_", re.IGNORECASE),
    re.compile(r"\bfallback\b", re.IGNORECASE),
    re.compile(r"hardcoded", re.IGNORECASE),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", default=DEFAULT_TARGETS)
    args = parser.parse_args()

    violations: list[str] = []

    for raw in args.paths:
        path = Path(raw)
        if not path.exists():
            violations.append(f"missing file: {path}")
            continue

        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PATTERNS:
            for match in pattern.finditer(text):
                line = text[: match.start()].count("\n") + 1
                violations.append(f"{path}:{line} -> forbidden pattern '{pattern.pattern}'")

    if violations:
        print("No-mock production guard failed:")
        for violation in violations:
            print(f"- {violation}")
        return 1

    print("No-mock production guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
