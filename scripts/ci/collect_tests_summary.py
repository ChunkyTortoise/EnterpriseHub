#!/usr/bin/env python3
"""Run pytest collection and print a reviewer-friendly summary."""

import re
import subprocess

COLLECT_RE = re.compile(r"(?P<count>[0-9,]+) tests collected in (?P<seconds>[0-9.]+)s")


def main() -> int:
    cmd = ["pytest", "--collect-only", "--override-ini=addopts=", "-q"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = f"{result.stdout}\n{result.stderr}".strip()

    if result.returncode != 0:
        print("Pytest collection failed. Last 80 output lines:")
        for line in output.splitlines()[-80:]:
            print(line)
        return result.returncode

    match = COLLECT_RE.search(output)
    if not match:
        print("Pytest collection passed, but the collection count was not found.")
        for line in output.splitlines()[-20:]:
            print(line)
        return 0

    print(f"Pytest collection passed: {match.group('count')} tests collected in {match.group('seconds')}s")

    warning_lines = [line for line in output.splitlines() if "warning" in line.lower() or "deprecated" in line.lower()]
    if warning_lines:
        print(f"Warnings mentioned during collection: {len(warning_lines)} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
