"""Snapshot the AgentMeshCoordinator's registered-agent registry.

Usage (from repo root):
    uv run python benchmarks/snapshot_mesh_registry.py

Output: benchmarks/results/mesh_registry_2026-05-27.json

The coordinator starts with an empty agent registry (self.agents = {}).
Agents are added only via register_agent(), which is async and requires a
passing health check plus external service attachment. This script captures
whatever state is observable at import+init time with no live services attached,
and describes the coordinator's schema, governance settings, and available
capability definitions.

Import notes:
    Requires the production dependency set (pydantic, pydantic-settings,
    fastapi, websockets, anthropic, redis, sqlalchemy, httpx and their
    transitive deps). The script inserts the repo root onto sys.path so
    it can be run as a standalone file from any working directory that
    contains the repo, without needing the package to be pip-installed.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the repo root (parent of benchmarks/) is on sys.path so the
# ghl_real_estate_ai package is importable regardless of working directory.
# ---------------------------------------------------------------------------
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

# ---------------------------------------------------------------------------
# Minimal env stubs so config validation passes without a real .env file.
# These values are never sent to any external service; they only satisfy
# pydantic-settings field validators at import time. Must be set BEFORE
# importing any ghl_real_estate_ai module because config is read at module
# load via pydantic-settings.
# ---------------------------------------------------------------------------
for _var, _stub in [
    ("ANTHROPIC_API_KEY", "sk-placeholder-snapshot"),
    ("GHL_API_KEY", "placeholder-snapshot"),
    ("GHL_LOCATION_ID", "placeholder-snapshot"),
]:
    os.environ.setdefault(_var, _stub)

# ---------------------------------------------------------------------------
# Import the coordinator and supporting types.
# ---------------------------------------------------------------------------
_import_error: str | None = None
try:
    from ghl_real_estate_ai.services.agent_mesh_coordinator import (  # noqa: E402
        AgentCapability,
        AgentMeshCoordinator,
        AgentStatus,
        TaskPriority,
    )
    _import_ok = True
except Exception as exc:
    _import_ok = False
    _import_error = f"{type(exc).__name__}: {exc}"


def _snapshot_capability_schema() -> list[dict]:
    """Return the static list of agent capability definitions from the enum."""
    return [{"name": cap.name, "value": cap.value} for cap in AgentCapability]


def _snapshot_status_schema() -> list[str]:
    return [s.value for s in AgentStatus]


def _snapshot_priority_schema() -> list[dict]:
    return [{"name": p.name, "level": p.value} for p in TaskPriority]


def _snapshot_governance(coord: AgentMeshCoordinator) -> dict:
    """Capture governance/budget settings visible on the instance."""
    return {
        "max_total_cost_per_hour_usd": coord.max_total_cost_per_hour,
        "max_tasks_per_user_per_hour": coord.max_tasks_per_user_per_hour,
        "emergency_shutdown_threshold_usd": coord.emergency_shutdown_threshold,
        "health_check_interval_seconds": coord.health_check_interval,
    }


def _snapshot_agents(coord: AgentMeshCoordinator) -> list[dict]:
    """Return per-agent identity and capabilities for all registered agents."""
    result = []
    for agent_id, agent in coord.agents.items():
        result.append(
            {
                "agent_id": agent_id,
                "name": agent.name,
                "capabilities": [cap.value for cap in agent.capabilities],
                "status": agent.status.value,
                "max_concurrent_tasks": agent.max_concurrent_tasks,
                "priority_level": agent.priority_level,
                "cost_per_token": agent.cost_per_token,
                "sla_response_time_seconds": agent.sla_response_time,
                "endpoint": agent.endpoint,
            }
        )
    return result


def build_snapshot() -> dict:
    """Build the full registry snapshot document."""
    ts = datetime.now(tz=timezone.utc).isoformat()

    if not _import_ok:
        return {
            "snapshot_at": ts,
            "method": "import-failed",
            "source": "ghl_real_estate_ai/services/agent_mesh_coordinator.py",
            "count": None,
            "agents": [],
            "import_error": _import_error,
            "notes": (
                "Import of AgentMeshCoordinator failed. "
                "No registry data could be captured. "
                "See import_error for the root cause."
            ),
        }

    coord = AgentMeshCoordinator()

    registered = _snapshot_agents(coord)
    count = len(registered)

    return {
        "snapshot_at": ts,
        "method": "import-and-init",
        "source": "ghl_real_estate_ai/services/agent_mesh_coordinator.py",
        "count": count,
        "agents": registered,
        "capability_schema": _snapshot_capability_schema(),
        "status_schema": _snapshot_status_schema(),
        "priority_schema": _snapshot_priority_schema(),
        "governance": _snapshot_governance(coord),
        "notes": (
            "No live services were attached at snapshot time. "
            "AgentMeshCoordinator.__init__() sets self.agents = {} and populates it "
            "only via register_agent() calls from external service handlers. "
            "count=0 is the correct observed value for a cold, unattached init. "
            "capability_schema, status_schema, and governance reflect static "
            "definitions embedded in the source at the time of this snapshot."
        ),
    }


def main() -> int:
    snapshot = build_snapshot()

    out_dir = Path(__file__).parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "mesh_registry_2026-05-27.json"

    out_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {out_path}")
    print(f"count={snapshot.get('count')}  method={snapshot.get('method')!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
