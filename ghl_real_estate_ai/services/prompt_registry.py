"""Versioned prompt registry loader.

Reads prompts/registry.yaml and provides typed access by name + version.
Used by CostTracker.record() prompt_version field and evals/judge.py.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

import yaml  # PyYAML, already in requirements

REGISTRY_PATH = pathlib.Path(__file__).parents[2] / "ghl_real_estate_ai/prompts/registry.yaml"


@dataclass(frozen=True)
class PromptEntry:
    name: str
    version: str
    date: str
    category: str
    file: str
    model: str
    eval_baseline_ref: str
    rationale: str

    @property
    def version_key(self) -> str:
        return f"{self.name}@{self.version}"


class PromptRegistry:
    """Load and query the versioned prompt registry."""

    def __init__(self, path: pathlib.Path = REGISTRY_PATH) -> None:
        self._entries: dict[str, PromptEntry] = {}
        self._load(path)

    def _load(self, path: pathlib.Path) -> None:
        raw = yaml.safe_load(path.read_text())
        for item in raw:
            entry = PromptEntry(**item)
            self._entries[entry.version_key] = entry

    def get(self, name: str, version: str = "1.0") -> Optional[PromptEntry]:
        return self._entries.get(f"{name}@{version}")

    def all(self) -> list[PromptEntry]:
        return list(self._entries.values())

    def by_category(self, category: str) -> list[PromptEntry]:
        return [e for e in self._entries.values() if e.category == category]


@lru_cache(maxsize=1)
def get_registry() -> PromptRegistry:
    return PromptRegistry()
