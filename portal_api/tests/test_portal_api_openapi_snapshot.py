from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from portal_api import app

SNAPSHOT_PATH = Path("portal_api/tests/openapi_snapshot.json")
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


def test_portal_api_openapi_snapshot_locked() -> None:
    assert SNAPSHOT_PATH.exists(), "OpenAPI snapshot is missing; run scripts/refresh_portal_openapi_snapshot.py"
    expected = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    current = _normalize(app.openapi())
    assert current == expected
