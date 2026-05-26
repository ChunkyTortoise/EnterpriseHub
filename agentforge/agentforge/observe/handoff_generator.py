"""Client handoff markdown generators.

Renders the three project handoff documents bundled by the
``agentforge bundle handoff`` command:

- ``architecture.md``: high-level system diagram and execution profile
- ``api-contract-summary.md``: run log schema and report endpoints
- ``operations-checklist.md``: ownership table for ongoing operations
"""

from __future__ import annotations

from datetime import UTC, datetime


def generate_architecture_md(project: str, execution_profile: str) -> str:
    """Render the architecture overview markdown for a project handoff."""
    generated_at = datetime.now(UTC).isoformat()
    lines = [
        f"# Architecture Overview: {project}",
        "",
        f"- Generated at: {generated_at}",
        f"- Project: `{project}`",
        f"- Execution profile: `{execution_profile}`",
        "",
        "## System Topology",
        "",
        "```mermaid",
        "flowchart LR",
        "    Client[Client Application] --> API[AgentForge API]",
        "    API --> Engine[Execution Engine]",
        "    Engine --> Agents[Configurable Agents]",
        "    Agents --> Tools[Registered Tools]",
        "    Engine --> Observe[Observability Layer]",
        "    Observe --> RunLog[(Run Log Store)]",
        "    Observe --> Metrics[(Metrics Store)]",
        "    RunLog --> Reports[Daily Reports]",
        "    Metrics --> Reports",
        "```",
        "",
        "## Execution Profile",
        "",
        f"This deployment is configured with the `{execution_profile}` profile.",
        "Profile defaults govern retry budgets, timeout caps, and observer hooks.",
        "Operators should review the profile before promoting changes to production.",
        "",
        "## Boundaries",
        "",
        "- Inbound: REST and CLI entry points routed through the API layer.",
        "- Outbound: LLM provider calls, registered tool invocations, and run log writes.",
        "- Sidecar: Observability layer captures spans, metrics, and structured run logs.",
        "",
    ]
    return "\n".join(lines) + "\n"


def generate_api_contract_summary_md(project: str) -> str:
    """Render the API contract summary markdown for a project handoff."""
    generated_at = datetime.now(UTC).isoformat()
    lines = [
        f"# API Contract Summary: {project}",
        "",
        f"- Generated at: {generated_at}",
        f"- Project: `{project}`",
        "",
        "## Run Log Schema",
        "",
        "Each run log entry is validated against the `RunLogEntry` model.",
        "",
        "| Field | Type | Required | Notes |",
        "|---|---|---|---|",
        "| `run_id` | string | yes | Unique identifier for a single workflow run. |",
        "| `workflow` | string | yes | Logical workflow name (e.g., `lead_qualification`). |",
        "| `latency_ms` | float | yes | End-to-end wall time in milliseconds (>= 0). |",
        "| `tokens` | int | no | Total tokens consumed across LLM calls. |",
        "| `cost_usd` | float | no | Estimated cost in USD for this run. |",
        "| `errors` | string or list | no | Empty when the run succeeded. |",
        "| `timestamp` | datetime | yes | ISO-8601 timestamp for the run. |",
        "",
        "## Report Surface",
        "",
        "The CLI exposes the following reporting subcommands:",
        "",
        "- `agentforge report validate-runlog --input <file> --output <file>`",
        "- `agentforge report daily-errors --input <file> --output <file>`",
        "- `agentforge report trends --input <file> --output <file>`",
        "- `agentforge report pack --input <file> --output-dir <dir> [--format md|json]`",
        "",
        "## Handoff Bundle",
        "",
        "- `agentforge bundle handoff --output-dir <dir> --project <name> --execution-profile <profile>`",
        "",
        "Each command exits with status 0 on success and 1 on validation or I/O failure.",
        "",
    ]
    return "\n".join(lines) + "\n"


def generate_operations_checklist_md(project: str) -> str:
    """Render the operations checklist markdown for a project handoff."""
    generated_at = datetime.now(UTC).isoformat()
    lines = [
        f"# Operations Checklist: {project}",
        "",
        f"- Generated at: {generated_at}",
        f"- Project: `{project}`",
        "",
        "## Ongoing Operations",
        "",
        "| Task | Owner | Status |",
        "|---|---|---|",
        "| Rotate LLM provider API keys quarterly | Platform Lead | Pending |",
        "| Review run log volume and storage budget weekly | Observability Lead | Pending |",
        "| Validate run log schema on each deploy | Release Engineer | Pending |",
        "| Generate daily error and trends reports | On-call Engineer | Pending |",
        "| Confirm execution profile matches environment | Platform Lead | Pending |",
        "| Audit registered tools and agents monthly | Tech Lead | Pending |",
        "| Run handoff bundle before major releases | Release Engineer | Pending |",
        "",
        "## Escalation",
        "",
        "- Page the on-call engineer when validation reports show `schema_status` other than `valid`.",
        "- Notify the platform lead when daily error rate exceeds the agreed threshold.",
        "- Open an incident when run log writes fail or stall for longer than 15 minutes.",
        "",
    ]
    return "\n".join(lines) + "\n"


__all__ = [
    "generate_api_contract_summary_md",
    "generate_architecture_md",
    "generate_operations_checklist_md",
]
