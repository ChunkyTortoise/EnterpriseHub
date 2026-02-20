"""Execution profile presets for incident-safe runtime defaults."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExecutionProfile(BaseModel):
    """Preset execution settings for workflow runs."""

    name: str
    max_retries: int = Field(ge=0)
    timeout: float | None = Field(default=None, ge=0.0)
    fail_fast: bool = False
    description: str


EXECUTION_PROFILES: dict[str, ExecutionProfile] = {
    "balanced": ExecutionProfile(
        name="balanced",
        max_retries=3,
        timeout=None,
        fail_fast=False,
        description="General-purpose default with moderate retries and full workflow completion.",
    ),
    "incident-safe": ExecutionProfile(
        name="incident-safe",
        max_retries=1,
        timeout=45.0,
        fail_fast=True,
        description="Fast failure and short timeout to reduce blast radius during incidents.",
    ),
    "resilient": ExecutionProfile(
        name="resilient",
        max_retries=5,
        timeout=180.0,
        fail_fast=False,
        description="Higher retry budget for unstable upstream dependencies.",
    ),
}


def list_execution_profiles() -> list[str]:
    """Return available execution profile names."""
    return sorted(EXECUTION_PROFILES.keys())


def get_execution_profile(name: str) -> ExecutionProfile:
    """Return an execution profile by name."""
    profile = EXECUTION_PROFILES.get(name)
    if profile is None:
        available = ", ".join(list_execution_profiles())
        raise ValueError(f"Unknown execution profile '{name}'. Available profiles: {available}")
    return profile


__all__ = [
    "ExecutionProfile",
    "EXECUTION_PROFILES",
    "get_execution_profile",
    "list_execution_profiles",
]
