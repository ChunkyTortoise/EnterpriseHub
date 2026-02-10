#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from portal_api import app

SNAPSHOT_PATH = ROOT_DIR / "portal_api/tests/openapi_snapshot.json"
SORTED_LIST_KEYS = {"enum", "required", "tags"}


def _normalize(value: Any, key: str | None = None) -> Any:
    if isinstance(value, dict):
        filtered = {
            k: v
            for k, v in value.items()
            if not (k == "additionalProperties" and isinstance(v, bool) and v is True)
        }
        return {k: _normalize(v, k) for k, v in sorted(filtered.items(), key=lambda item: item[0])}
    if isinstance(value, list):
        normalized = [_normalize(item, key) for item in value]
        if key in SORTED_LIST_KEYS and all(isinstance(item, str) for item in normalized):
            return sorted(normalized)
        return normalized
    return value


def main() -> None:
    normalized_openapi = _normalize(app.openapi())
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps(normalized_openapi, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"refreshed snapshot: {SNAPSHOT_PATH}")


if __name__ == "__main__":
    main()
