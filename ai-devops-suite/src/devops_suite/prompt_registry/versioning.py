"""Git-like prompt versioning with diffs and tags."""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PromptVersionRecord:
    version: int
    content: str
    variables: list[str]
    model_hint: str | None = None
    tags: list[str] = field(default_factory=list)
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.utcnow)
    parent_version: int | None = None
    changelog: str | None = None


@dataclass
class VersionDiff:
    from_version: int
    to_version: int
    unified_diff: str
    added_lines: int
    removed_lines: int


class PromptVersionManager:
    """Manages prompt versions with git-like semantics."""

    def __init__(self) -> None:
        self._prompts: dict[str, list[PromptVersionRecord]] = {}

    def create_version(
        self,
        prompt_id: str,
        content: str,
        variables: list[str] | None = None,
        model_hint: str | None = None,
        tags: list[str] | None = None,
        created_by: str = "system",
        changelog: str | None = None,
    ) -> PromptVersionRecord:
        if prompt_id not in self._prompts:
            self._prompts[prompt_id] = []

        versions = self._prompts[prompt_id]
        version_num = len(versions) + 1
        parent = versions[-1].version if versions else None

        if variables is None:
            variables = _extract_variables(content)

        record = PromptVersionRecord(
            version=version_num,
            content=content,
            variables=variables,
            model_hint=model_hint,
            tags=tags or [],
            created_by=created_by,
            parent_version=parent,
            changelog=changelog,
        )
        versions.append(record)
        return record

    def get_version(self, prompt_id: str, version: int | None = None) -> PromptVersionRecord | None:
        versions = self._prompts.get(prompt_id, [])
        if not versions:
            return None
        if version is None:
            return versions[-1]
        for v in versions:
            if v.version == version:
                return v
        return None

    def get_all_versions(self, prompt_id: str) -> list[PromptVersionRecord]:
        return list(self._prompts.get(prompt_id, []))

    def diff_versions(self, prompt_id: str, from_v: int, to_v: int) -> VersionDiff | None:
        v1 = self.get_version(prompt_id, from_v)
        v2 = self.get_version(prompt_id, to_v)
        if not v1 or not v2:
            return None

        diff_lines = list(
            difflib.unified_diff(
                v1.content.splitlines(keepends=True),
                v2.content.splitlines(keepends=True),
                fromfile=f"v{from_v}",
                tofile=f"v{to_v}",
            )
        )
        added = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))
        removed = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))

        return VersionDiff(
            from_version=from_v,
            to_version=to_v,
            unified_diff="".join(diff_lines),
            added_lines=added,
            removed_lines=removed,
        )

    def tag_version(self, prompt_id: str, version: int, tag: str) -> bool:
        # Remove tag from any other version of same prompt
        for v in self._prompts.get(prompt_id, []):
            if tag in v.tags:
                v.tags.remove(tag)
        record = self.get_version(prompt_id, version)
        if not record:
            return False
        record.tags.append(tag)
        return True

    def get_by_tag(self, prompt_id: str, tag: str) -> PromptVersionRecord | None:
        for v in self._prompts.get(prompt_id, []):
            if tag in v.tags:
                return v
        return None

    def list_prompts(self) -> list[str]:
        return list(self._prompts.keys())


def _extract_variables(content: str) -> list[str]:
    """Extract Jinja2-style variables from prompt content."""
    import re

    return sorted(set(re.findall(r"\{\{\s*(\w+)\s*\}\}", content)))
