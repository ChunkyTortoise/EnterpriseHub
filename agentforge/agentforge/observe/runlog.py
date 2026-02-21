"""Structured run log utilities for observability reporting.

Provides:
- Run log schema models and validation
- JSON exporter for normalized run logs
- Markdown and JSON report generation for validation/errors/trends/roi
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, date, datetime
from pathlib import Path
from statistics import mean
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class RunLogEntry(BaseModel):
    """Normalized schema for a single workflow run log entry."""

    model_config = ConfigDict(extra="allow")

    run_id: str
    workflow: str
    latency_ms: float = Field(ge=0.0)
    tokens: int = Field(default=0, ge=0)
    cost_usd: float = Field(default=0.0, ge=0.0)
    errors: str | list[str] | None = None
    timestamp: datetime

    def has_errors(self) -> bool:
        """Return whether this run contains at least one error."""
        if self.errors is None:
            return False
        if isinstance(self.errors, str):
            return bool(self.errors.strip())
        return len(self.errors) > 0


class RunLogEnvelope(BaseModel):
    """Structured run log envelope for file export/import."""

    schema_version: str = "1.0"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    runs: list[RunLogEntry] = Field(default_factory=list)


class WorkflowDayStats(BaseModel):
    """Aggregated stats for a workflow on a calendar day."""

    workflow: str
    day: date
    run_count: int = 0
    error_count: int = 0
    avg_latency_ms: float = 0.0
    avg_cost_usd: float = 0.0


class RunLogValidationSummary(BaseModel):
    """High-level metadata returned by schema validation."""

    schema_version: str = "1.0"
    run_count: int = 0
    workflow_count: int = 0
    start_time: datetime | None = None
    end_time: datetime | None = None


class ROIReportSummary(BaseModel):
    """Computed ROI summary derived from run logs and a value assumption."""

    runs_analyzed: int
    successful_runs: int
    error_runs: int
    total_tokens: int
    total_cost_usd: float
    average_cost_per_run_usd: float
    value_per_successful_run_usd: float
    estimated_value_usd: float
    net_value_usd: float
    roi_percent: float | None


def validate_run_log_payload(payload: Any) -> list[RunLogEntry]:
    """Validate and normalize run log payload.

    Accepts either:
    - a list of run rows
    - an envelope dict with a ``runs`` key
    """
    rows: Any
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = payload.get("runs", [])
    else:
        raise ValueError("Invalid run log schema; expected list or {'runs': [...]}.")

    if not isinstance(rows, list):
        raise ValueError("Invalid run log schema; expected list or {'runs': [...]}.")

    try:
        return [RunLogEntry.model_validate(row) for row in rows]
    except ValidationError as exc:  # pragma: no cover - exercised through tests
        raise ValueError(f"Invalid run log schema: {exc}") from exc


def load_run_logs(path: str | Path) -> list[RunLogEntry]:
    """Load and validate run logs from JSON file."""
    input_path = Path(path)
    with open(input_path) as f:
        payload = json.load(f)
    return validate_run_log_payload(payload)


def validate_run_log_file(path: str | Path) -> RunLogValidationSummary:
    """Validate a run log file and return a compact summary."""
    input_path = Path(path)
    with open(input_path) as f:
        payload = json.load(f)

    rows = validate_run_log_payload(payload)
    timestamps = sorted(row.timestamp for row in rows)
    schema_version = payload.get("schema_version", "1.0") if isinstance(payload, dict) else "1.0"

    return RunLogValidationSummary(
        schema_version=schema_version,
        run_count=len(rows),
        workflow_count=len({row.workflow for row in rows}),
        start_time=timestamps[0] if timestamps else None,
        end_time=timestamps[-1] if timestamps else None,
    )


def validation_summary_to_dict(summary: RunLogValidationSummary) -> dict[str, Any]:
    """Convert a validation summary to a JSON-serializable dictionary."""
    return {
        "schema_status": "valid",
        "schema_version": summary.schema_version,
        "run_count": summary.run_count,
        "workflow_count": summary.workflow_count,
        "start_time": summary.start_time.isoformat() if summary.start_time else None,
        "end_time": summary.end_time.isoformat() if summary.end_time else None,
    }


def generate_validation_markdown(summary: RunLogValidationSummary) -> str:
    """Generate a markdown report for run log schema validation."""
    data = validation_summary_to_dict(summary)
    lines = [
        "# Run Log Validation Report",
        "",
        f"- Generated at: {datetime.now(UTC).isoformat()}",
        f"- Schema status: {data['schema_status']}",
        f"- Schema version: {data['schema_version']}",
        f"- Runs validated: {data['run_count']}",
        f"- Workflows found: {data['workflow_count']}",
        f"- Start time: {data['start_time'] or 'n/a'}",
        f"- End time: {data['end_time'] or 'n/a'}",
        "",
    ]
    return "\n".join(lines)


def generate_validate_runlog_markdown(summary: RunLogValidationSummary) -> str:
    """Backward-compatible alias for validation markdown renderer."""
    return generate_validation_markdown(summary)


def generate_validate_runlog_json(summary: RunLogValidationSummary) -> dict[str, Any]:
    """Generate JSON payload for validation reporting."""
    return validation_summary_to_dict(summary)


def export_run_logs(
    path: str | Path,
    runs: Sequence[RunLogEntry | dict[str, Any]],
    schema_version: str = "1.0",
) -> Path:
    """Export runs into a structured run log envelope."""
    normalized = [
        run if isinstance(run, RunLogEntry) else RunLogEntry.model_validate(run) for run in runs
    ]
    envelope = RunLogEnvelope(schema_version=schema_version, runs=normalized)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(envelope.model_dump(mode="json"), f, indent=2)
    return output_path


def aggregate_workflow_day_stats(runs: Sequence[RunLogEntry]) -> list[WorkflowDayStats]:
    """Aggregate runs by workflow and calendar day."""
    buckets: dict[tuple[str, date], list[RunLogEntry]] = defaultdict(list)
    for run in runs:
        buckets[(run.workflow, run.timestamp.date())].append(run)

    stats: list[WorkflowDayStats] = []
    for (workflow, day), rows in buckets.items():
        stats.append(
            WorkflowDayStats(
                workflow=workflow,
                day=day,
                run_count=len(rows),
                error_count=sum(1 for row in rows if row.has_errors()),
                avg_latency_ms=mean(row.latency_ms for row in rows),
                avg_cost_usd=mean(row.cost_usd for row in rows),
            )
        )

    return sorted(stats, key=lambda stat: (stat.workflow, stat.day))


def _percent_delta(previous: float, current: float) -> str:
    if previous <= 0:
        return "n/a"
    delta = ((current - previous) / previous) * 100.0
    return f"{delta:+.2f}%"


def _percent_delta_value(previous: float, current: float) -> float | None:
    if previous <= 0:
        return None
    return ((current - previous) / previous) * 100.0


def _daily_errors_report_data(runs: Sequence[RunLogEntry]) -> dict[str, Any]:
    """Build structured daily-errors report payload."""
    stats = aggregate_workflow_day_stats(runs)
    by_day: dict[date, list[WorkflowDayStats]] = defaultdict(list)
    by_workflow: dict[str, list[WorkflowDayStats]] = defaultdict(list)

    for stat in stats:
        by_day[stat.day].append(stat)
        by_workflow[stat.workflow].append(stat)

    total_errors = sum(1 for run in runs if run.has_errors())

    days: list[dict[str, Any]] = []
    for day in sorted(by_day):
        day_rows = by_day[day]
        day_runs = sum(item.run_count for item in day_rows)
        day_errors = sum(item.error_count for item in day_rows)
        rate = (day_errors / day_runs) * 100.0 if day_runs else 0.0
        days.append(
            {
                "day": day.isoformat(),
                "runs": day_runs,
                "error_runs": day_errors,
                "error_rate_percent": round(rate, 2),
            }
        )

    workflows: list[dict[str, Any]] = []
    for workflow in sorted(by_workflow):
        wf_stats = sorted(by_workflow[workflow], key=lambda item: item.day)
        latest = wf_stats[-1]
        previous = wf_stats[-2] if len(wf_stats) > 1 else None
        error_rate = (latest.error_count / latest.run_count) * 100.0 if latest.run_count else 0.0
        workflows.append(
            {
                "workflow": workflow,
                "latest_day": latest.day.isoformat(),
                "error_rate_percent": round(error_rate, 2),
                "avg_latency_ms": round(latest.avg_latency_ms, 2),
                "latency_day_over_day_percent": (
                    round(_percent_delta_value(previous.avg_latency_ms, latest.avg_latency_ms), 2)
                    if previous
                    and _percent_delta_value(previous.avg_latency_ms, latest.avg_latency_ms)
                    is not None
                    else None
                ),
                "avg_cost_usd": round(latest.avg_cost_usd, 4),
                "cost_day_over_day_percent": (
                    round(_percent_delta_value(previous.avg_cost_usd, latest.avg_cost_usd), 2)
                    if previous
                    and _percent_delta_value(previous.avg_cost_usd, latest.avg_cost_usd) is not None
                    else None
                ),
            }
        )

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "runs_analyzed": len(runs),
        "days_covered": len(by_day),
        "runs_with_errors": total_errors,
        "days": days,
        "workflow_summary": workflows,
    }


def generate_daily_errors_markdown(runs: Sequence[RunLogEntry]) -> str:
    """Generate a daily error summary markdown report."""
    data = _daily_errors_report_data(runs)

    lines = [
        "# Daily Error Report",
        "",
        f"- Generated at: {data['generated_at']}",
        f"- Runs analyzed: {data['runs_analyzed']}",
        f"- Days covered: {data['days_covered']}",
        f"- Runs with errors: {data['runs_with_errors']}",
        "",
        "## Error Volume by Day",
        "",
        "| Day | Runs | Error Runs | Error Rate |",
        "|---|---:|---:|---:|",
    ]

    for day_row in data["days"]:
        lines.append(
            "| "
            f"{day_row['day']} | {day_row['runs']} | {day_row['error_runs']} | "
            f"{day_row['error_rate_percent']:.2f}% |"
        )

    lines.extend(
        [
            "",
            "## Per-Workflow Latency/Cost Trend Summary",
            "",
            "| Workflow | Latest Day | Error Rate | Avg Latency (ms) | Latency DoD | Avg Cost (USD) | Cost DoD |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )

    for workflow_row in data["workflow_summary"]:
        latency_delta = (
            f"{workflow_row['latency_day_over_day_percent']:+.2f}%"
            if workflow_row["latency_day_over_day_percent"] is not None
            else "n/a"
        )
        cost_delta = (
            f"{workflow_row['cost_day_over_day_percent']:+.2f}%"
            if workflow_row["cost_day_over_day_percent"] is not None
            else "n/a"
        )
        lines.append(
            "| "
            f"{workflow_row['workflow']} | {workflow_row['latest_day']} | "
            f"{workflow_row['error_rate_percent']:.2f}% | "
            f"{workflow_row['avg_latency_ms']:.2f} | {latency_delta} | "
            f"{workflow_row['avg_cost_usd']:.4f} | {cost_delta} |"
        )

    return "\n".join(lines) + "\n"


def generate_daily_errors_json(runs: Sequence[RunLogEntry]) -> dict[str, Any]:
    """Generate structured data for daily error reporting."""
    return _daily_errors_report_data(runs)


def _trends_report_data(runs: Sequence[RunLogEntry]) -> dict[str, Any]:
    """Build structured trends report payload."""
    stats = aggregate_workflow_day_stats(runs)
    by_workflow: dict[str, list[WorkflowDayStats]] = defaultdict(list)
    for stat in stats:
        by_workflow[stat.workflow].append(stat)

    workflows: list[dict[str, Any]] = []
    for workflow in sorted(by_workflow):
        wf_stats = sorted(by_workflow[workflow], key=lambda item: item.day)
        first = wf_stats[0]
        latest = wf_stats[-1]
        workflows.append(
            {
                "workflow": workflow,
                "days": len(wf_stats),
                "first_avg_latency_ms": round(first.avg_latency_ms, 2),
                "latest_avg_latency_ms": round(latest.avg_latency_ms, 2),
                "latency_delta_percent": (
                    round(_percent_delta_value(first.avg_latency_ms, latest.avg_latency_ms), 2)
                    if _percent_delta_value(first.avg_latency_ms, latest.avg_latency_ms) is not None
                    else None
                ),
                "first_avg_cost_usd": round(first.avg_cost_usd, 4),
                "latest_avg_cost_usd": round(latest.avg_cost_usd, 4),
                "cost_delta_percent": (
                    round(_percent_delta_value(first.avg_cost_usd, latest.avg_cost_usd), 2)
                    if _percent_delta_value(first.avg_cost_usd, latest.avg_cost_usd) is not None
                    else None
                ),
            }
        )

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "runs_analyzed": len(runs),
        "workflows_analyzed": len(by_workflow),
        "workflows": workflows,
    }


def generate_trends_markdown(runs: Sequence[RunLogEntry]) -> str:
    """Generate latency/cost trends report grouped by workflow."""
    data = _trends_report_data(runs)

    lines = [
        "# Workflow Trends Report",
        "",
        f"- Generated at: {data['generated_at']}",
        f"- Runs analyzed: {data['runs_analyzed']}",
        f"- Workflows analyzed: {data['workflows_analyzed']}",
        "",
        "## Per-Workflow Latency/Cost Trends",
        "",
        "| Workflow | Days | First Avg Latency (ms) | Latest Avg Latency (ms) | Latency Delta | First Avg Cost (USD) | Latest Avg Cost (USD) | Cost Delta |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for workflow_row in data["workflows"]:
        latency_delta = (
            f"{workflow_row['latency_delta_percent']:+.2f}%"
            if workflow_row["latency_delta_percent"] is not None
            else "n/a"
        )
        cost_delta = (
            f"{workflow_row['cost_delta_percent']:+.2f}%"
            if workflow_row["cost_delta_percent"] is not None
            else "n/a"
        )
        lines.append(
            "| "
            f"{workflow_row['workflow']} | {workflow_row['days']} | "
            f"{workflow_row['first_avg_latency_ms']:.2f} | {workflow_row['latest_avg_latency_ms']:.2f} | "
            f"{latency_delta} | "
            f"{workflow_row['first_avg_cost_usd']:.4f} | {workflow_row['latest_avg_cost_usd']:.4f} | "
            f"{cost_delta} |"
        )

    return "\n".join(lines) + "\n"


def generate_trends_json(runs: Sequence[RunLogEntry]) -> dict[str, Any]:
    """Generate structured data for trends reporting."""
    return _trends_report_data(runs)


def generate_roi_summary(
    runs: Sequence[RunLogEntry],
    value_per_successful_run_usd: float = 1.0,
) -> ROIReportSummary:
    """Compute ROI summary from run logs with a value-per-success assumption."""
    successful_runs = sum(1 for run in runs if not run.has_errors())
    error_runs = len(runs) - successful_runs
    total_tokens = sum(run.tokens for run in runs)
    total_cost = sum(run.cost_usd for run in runs)
    estimated_value = successful_runs * value_per_successful_run_usd
    net_value = estimated_value - total_cost
    roi_percent = (net_value / total_cost) * 100.0 if total_cost > 0 else None

    return ROIReportSummary(
        runs_analyzed=len(runs),
        successful_runs=successful_runs,
        error_runs=error_runs,
        total_tokens=total_tokens,
        total_cost_usd=total_cost,
        average_cost_per_run_usd=(total_cost / len(runs)) if runs else 0.0,
        value_per_successful_run_usd=value_per_successful_run_usd,
        estimated_value_usd=estimated_value,
        net_value_usd=net_value,
        roi_percent=roi_percent,
    )


def generate_roi_markdown(
    runs: Sequence[RunLogEntry],
    value_per_successful_run_usd: float = 1.0,
) -> str:
    """Generate markdown ROI report from run logs."""
    roi = generate_roi_summary(runs, value_per_successful_run_usd=value_per_successful_run_usd)
    lines = [
        "# ROI Report",
        "",
        f"- Generated at: {datetime.now(UTC).isoformat()}",
        f"- Runs analyzed: {roi.runs_analyzed}",
        f"- Successful runs: {roi.successful_runs}",
        f"- Error runs: {roi.error_runs}",
        f"- Total tokens: {roi.total_tokens}",
        f"- Total cost (USD): {roi.total_cost_usd:.4f}",
        f"- Avg cost/run (USD): {roi.average_cost_per_run_usd:.4f}",
        f"- Value assumption per successful run (USD): {roi.value_per_successful_run_usd:.2f}",
        f"- Estimated value (USD): {roi.estimated_value_usd:.4f}",
        f"- Net value (USD): {roi.net_value_usd:.4f}",
        (
            f"- ROI: {roi.roi_percent:.2f}%"
            if roi.roi_percent is not None
            else "- ROI: n/a (total cost is zero)"
        ),
        "",
    ]
    return "\n".join(lines)


def generate_roi_json(
    runs: Sequence[RunLogEntry],
    value_per_successful_run_usd: float = 1.0,
) -> dict[str, Any]:
    """Generate structured data for ROI reporting."""
    summary = generate_roi_summary(runs, value_per_successful_run_usd=value_per_successful_run_usd)
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        **summary.model_dump(mode="json"),
    }


__all__ = [
    "ROIReportSummary",
    "RunLogValidationSummary",
    "RunLogEntry",
    "RunLogEnvelope",
    "WorkflowDayStats",
    "aggregate_workflow_day_stats",
    "export_run_logs",
    "generate_daily_errors_json",
    "generate_daily_errors_markdown",
    "generate_roi_json",
    "generate_roi_markdown",
    "generate_roi_summary",
    "generate_trends_json",
    "generate_trends_markdown",
    "generate_validate_runlog_json",
    "generate_validate_runlog_markdown",
    "generate_validation_markdown",
    "load_run_logs",
    "validate_run_log_file",
    "validate_run_log_payload",
    "validation_summary_to_dict",
]
