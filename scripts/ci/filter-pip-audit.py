#!/usr/bin/env python3
"""Filter pip-audit JSON output against .osv-allowlist.json.

Exit 0 if all reported vulnerabilities are in the allowlist.
Exit 1 if any reported vulnerability is NOT in the allowlist (the gate failure).

Usage:
    pip-audit --format json | python3 scripts/ci/filter-pip-audit.py .osv-allowlist.json
    pip-audit --format json --output report.json
    python3 scripts/ci/filter-pip-audit.py .osv-allowlist.json < report.json
"""
import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: filter-pip-audit.py <allowlist.json>", file=sys.stderr)
        return 2
    allowlist_path = Path(sys.argv[1])
    if not allowlist_path.is_file():
        print(f"allowlist file not found: {allowlist_path}", file=sys.stderr)
        return 2
    allowlist = json.loads(allowlist_path.read_text())
    allowed_ids = {v["id"] for v in allowlist.get("vulnerabilities", [])}

    try:
        audit = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"failed to parse pip-audit json from stdin: {exc}", file=sys.stderr)
        return 2

    unallowed = []
    for dep in audit.get("dependencies", []):
        for v in dep.get("vulns", []):
            if v["id"] not in allowed_ids:
                unallowed.append(
                    {
                        "package": dep.get("name"),
                        "version": dep.get("version"),
                        "vuln_id": v["id"],
                        "fix_versions": v.get("fix_versions", []),
                    }
                )

    if unallowed:
        print("FAIL: pip-audit reported vulnerabilities not in allowlist", file=sys.stderr)
        print(json.dumps({"unallowed": unallowed}, indent=2), file=sys.stderr)
        print(
            "To accept these: add them to .osv-allowlist.json with a written reason.",
            file=sys.stderr,
        )
        return 1

    print(f"OK: all {len(allowed_ids)} known vulnerabilities are in the allowlist.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
