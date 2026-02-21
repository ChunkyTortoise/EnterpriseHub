"""Integration-style tests for reporting and handoff outputs."""

from pathlib import Path

import pytest

from agentforge.cli import CLI
from agentforge.observe.runlog import export_run_logs


def _seed_run_log(path: Path) -> None:
    export_run_logs(
        path,
        [
            {
                "run_id": "r-1",
                "workflow": "lead_qualification",
                "latency_ms": 120.0,
                "tokens": 300,
                "cost_usd": 0.02,
                "errors": "",
                "timestamp": "2026-02-19T10:00:00Z",
            },
            {
                "run_id": "r-2",
                "workflow": "lead_qualification",
                "latency_ms": 140.0,
                "tokens": 340,
                "cost_usd": 0.025,
                "errors": "timeout",
                "timestamp": "2026-02-20T10:00:00Z",
            },
            {
                "run_id": "r-3",
                "workflow": "support_triage",
                "latency_ms": 90.0,
                "tokens": 210,
                "cost_usd": 0.011,
                "errors": "",
                "timestamp": "2026-02-20T11:00:00Z",
            },
        ],
    )


def test_reporting_and_handoff_end_to_end(tmp_path: Path) -> None:
    cli = CLI()
    run_log_path = tmp_path / "run_log.json"
    reports_dir = tmp_path / "reports"
    handoff_dir = tmp_path / "handoff"

    _seed_run_log(run_log_path)

    assert (
        cli.run(
            [
                "report",
                "daily-errors",
                "--input",
                str(run_log_path),
                "--output",
                str(reports_dir / "daily-errors.md"),
            ]
        )
        == 0
    )
    assert (
        cli.run(
            [
                "report",
                "trends",
                "--input",
                str(run_log_path),
                "--output",
                str(reports_dir / "trends.md"),
            ]
        )
        == 0
    )
    assert (
        cli.run(
            [
                "report",
                "validate-runlog",
                "--input",
                str(run_log_path),
                "--output",
                str(reports_dir / "validate.md"),
            ]
        )
        == 0
    )
    assert (
        cli.run(
            [
                "bundle",
                "handoff",
                "--output-dir",
                str(handoff_dir),
                "--project",
                "client-x",
                "--execution-profile",
                "incident-safe",
            ]
        )
        == 0
    )

    daily_errors = (reports_dir / "daily-errors.md").read_text()
    trends = (reports_dir / "trends.md").read_text()
    validate = (reports_dir / "validate.md").read_text()
    architecture = (handoff_dir / "architecture.md").read_text()
    api_contract = (handoff_dir / "api-contract-summary.md").read_text()
    ops_checklist = (handoff_dir / "operations-checklist.md").read_text()

    assert "Per-Workflow Latency/Cost Trend Summary" in daily_errors
    assert "lead_qualification" in daily_errors
    assert "Per-Workflow Latency/Cost Trends" in trends
    assert "support_triage" in trends
    assert "Schema status: valid" in validate
    assert "```mermaid" in architecture
    assert "Execution profile: `incident-safe`" in architecture
    assert "Run Log Schema" in api_contract
    assert "| Task | Owner | Status |" in ops_checklist


def test_report_pack_end_to_end(tmp_path: Path) -> None:
    cli = CLI()
    run_log_path = tmp_path / "run_log.json"
    reports_dir = tmp_path / "reports-pack"
    _seed_run_log(run_log_path)

    assert (
        cli.run(
            [
                "report",
                "pack",
                "--input",
                str(run_log_path),
                "--output-dir",
                str(reports_dir),
            ]
        )
        == 0
    )

    assert "Run Log Validation Report" in (reports_dir / "validate-runlog.md").read_text()
    assert "Daily Error Report" in (reports_dir / "daily-errors.md").read_text()
    assert "Workflow Trends Report" in (reports_dir / "trends.md").read_text()
    assert "ROI Report" in (reports_dir / "roi.md").read_text()


def test_report_pack_supports_json_output(tmp_path: Path) -> None:
    cli = CLI()
    run_log_path = tmp_path / "run_log.json"
    reports_dir = tmp_path / "reports-pack-json"
    _seed_run_log(run_log_path)

    assert (
        cli.run(
            [
                "report",
                "pack",
                "--input",
                str(run_log_path),
                "--output-dir",
                str(reports_dir),
                "--format",
                "json",
            ]
        )
        == 0
    )

    assert '"schema_status": "valid"' in (reports_dir / "validate-runlog.json").read_text()
    assert '"runs_analyzed": 3' in (reports_dir / "daily-errors.json").read_text()
    assert '"workflows_analyzed": 2' in (reports_dir / "trends.json").read_text()
    assert '"runs_analyzed": 3' in (reports_dir / "roi.json").read_text()


def test_handoff_bundle_is_atomic_on_write_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = CLI()
    handoff_dir = tmp_path / "handoff"
    handoff_dir.mkdir(parents=True, exist_ok=True)
    (handoff_dir / "sentinel.txt").write_text("keep-me")

    original_write_text = Path.write_text

    def flaky_write_text(path: Path, data: str, *args, **kwargs) -> int:
        if path.name == "operations-checklist.md":
            raise OSError("simulated write failure")
        return original_write_text(path, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", flaky_write_text)

    assert (
        cli.run(
            [
                "bundle",
                "handoff",
                "--output-dir",
                str(handoff_dir),
                "--project",
                "client-x",
                "--execution-profile",
                "incident-safe",
            ]
        )
        == 1
    )

    assert (handoff_dir / "sentinel.txt").read_text() == "keep-me"
    assert not (handoff_dir / "architecture.md").exists()
    assert not (handoff_dir / "api-contract-summary.md").exists()
    assert not (handoff_dir / "operations-checklist.md").exists()
