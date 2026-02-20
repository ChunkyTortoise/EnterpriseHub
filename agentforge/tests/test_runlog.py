"""Tests for structured run log utilities."""

from pathlib import Path

import pytest

from agentforge.observe.runlog import (
    export_run_logs,
    generate_daily_errors_json,
    generate_daily_errors_markdown,
    generate_roi_json,
    generate_roi_markdown,
    generate_trends_json,
    generate_trends_markdown,
    generate_validation_markdown,
    load_run_logs,
    validate_run_log_file,
    validate_run_log_payload,
    validation_summary_to_dict,
)


@pytest.fixture
def sample_runs() -> list[dict[str, object]]:
    return [
        {
            "run_id": "1",
            "workflow": "lead_qualification",
            "latency_ms": 100,
            "tokens": 200,
            "cost_usd": 0.02,
            "errors": "",
            "timestamp": "2026-02-19T10:00:00Z",
        },
        {
            "run_id": "2",
            "workflow": "lead_qualification",
            "latency_ms": 120,
            "tokens": 220,
            "cost_usd": 0.03,
            "errors": "timeout",
            "timestamp": "2026-02-20T10:00:00Z",
        },
        {
            "run_id": "3",
            "workflow": "support_triage",
            "latency_ms": 90,
            "tokens": 180,
            "cost_usd": 0.01,
            "errors": [],
            "timestamp": "2026-02-20T11:00:00Z",
        },
    ]


def test_validate_payload_supports_list(sample_runs: list[dict[str, object]]) -> None:
    rows = validate_run_log_payload(sample_runs)
    assert len(rows) == 3
    assert rows[1].has_errors() is True


def test_validate_payload_supports_envelope(sample_runs: list[dict[str, object]]) -> None:
    rows = validate_run_log_payload({"schema_version": "1.0", "runs": sample_runs})
    assert len(rows) == 3


def test_validate_payload_rejects_invalid_schema() -> None:
    with pytest.raises(ValueError):
        validate_run_log_payload({"runs": {"bad": "shape"}})


def test_export_and_load_round_trip(tmp_path: Path, sample_runs: list[dict[str, object]]) -> None:
    output_path = tmp_path / "run_log.json"
    export_run_logs(output_path, sample_runs)

    loaded = load_run_logs(output_path)
    assert len(loaded) == 3
    assert loaded[0].workflow == "lead_qualification"


def test_validate_run_log_file_returns_summary(
    tmp_path: Path,
    sample_runs: list[dict[str, object]],
) -> None:
    input_path = tmp_path / "run_log.json"
    export_run_logs(input_path, sample_runs, schema_version="1.0")

    summary = validate_run_log_file(input_path)
    assert summary.schema_version == "1.0"
    assert summary.run_count == 3
    assert summary.workflow_count == 2
    assert summary.start_time is not None
    assert summary.end_time is not None


def test_validate_summary_json_and_markdown(
    tmp_path: Path,
    sample_runs: list[dict[str, object]],
) -> None:
    input_path = tmp_path / "run_log.json"
    export_run_logs(input_path, sample_runs)

    summary = validate_run_log_file(input_path)
    data = validation_summary_to_dict(summary)
    markdown = generate_validation_markdown(summary)

    assert data["schema_status"] == "valid"
    assert data["run_count"] == 3
    assert "Run Log Validation Report" in markdown
    assert "Schema status: valid" in markdown


def test_generate_daily_errors_markdown_contains_trends(
    sample_runs: list[dict[str, object]],
) -> None:
    markdown = generate_daily_errors_markdown(validate_run_log_payload(sample_runs))

    assert "Daily Error Report" in markdown
    assert "Per-Workflow Latency/Cost Trend Summary" in markdown
    assert "lead_qualification" in markdown


def test_generate_daily_errors_json_contains_expected_fields(
    sample_runs: list[dict[str, object]],
) -> None:
    payload = generate_daily_errors_json(validate_run_log_payload(sample_runs))

    assert payload["runs_analyzed"] == 3
    assert payload["days_covered"] == 2
    assert payload["runs_with_errors"] == 1
    assert payload["workflow_summary"][0]["workflow"] in {"lead_qualification", "support_triage"}


def test_generate_trends_markdown_contains_workflow_table(
    sample_runs: list[dict[str, object]],
) -> None:
    markdown = generate_trends_markdown(validate_run_log_payload(sample_runs))

    assert "Workflow Trends Report" in markdown
    assert "Per-Workflow Latency/Cost Trends" in markdown
    assert "support_triage" in markdown


def test_generate_trends_json_contains_workflow_rows(
    sample_runs: list[dict[str, object]],
) -> None:
    payload = generate_trends_json(validate_run_log_payload(sample_runs))

    assert payload["runs_analyzed"] == 3
    workflows = {row["workflow"] for row in payload["workflows"]}
    assert workflows == {"lead_qualification", "support_triage"}


def test_generate_roi_markdown_and_json(sample_runs: list[dict[str, object]]) -> None:
    runs = validate_run_log_payload(sample_runs)
    markdown = generate_roi_markdown(runs, value_per_successful_run_usd=2.5)
    payload = generate_roi_json(runs, value_per_successful_run_usd=2.5)

    assert "ROI Report" in markdown
    assert "Value assumption per successful run (USD): 2.50" in markdown
    assert payload["runs_analyzed"] == 3
    assert payload["successful_runs"] == 2
    assert payload["error_runs"] == 1
