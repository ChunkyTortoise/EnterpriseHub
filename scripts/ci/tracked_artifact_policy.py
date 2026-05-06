#!/usr/bin/env python3
"""Fail when tracked local artifacts or secret-shaped files exist in the tree."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


FORBIDDEN_PATTERNS = [
    re.compile(r"(^|/)\.jwt_secret$"),
    re.compile(r"\.dump$"),
    re.compile(r"^deploy/.*\.env$"),
    re.compile(r"^configs/production/secrets\.production\.yml$"),
    re.compile(r"^\.playwright-mcp/"),
    re.compile(r"^advanced_rag_system/venv312/"),
    re.compile(r"^\.debug_chroma/"),
    re.compile(r"^data/embeddings/chroma_db/"),
]


def tracked_paths() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def is_forbidden(path: str) -> bool:
    if path.endswith((".template", ".example")):
        return False
    return any(pattern.search(path) for pattern in FORBIDDEN_PATTERNS)


def main() -> int:
    # Deleted-but-unstaged paths still appear in git ls-files. Ignore paths that
    # no longer exist so this gate can pass before the cleanup is staged.
    offenders = [path for path in tracked_paths() if Path(path).exists() and is_forbidden(path)]

    if offenders:
        print("Tracked artifact policy failed:")
        for path in offenders:
            print(f"- {path}")
        return 1

    print("Tracked artifact policy passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
