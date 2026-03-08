from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _write(path: Path, rows: list[dict]) -> None:
    lines = [json.dumps(row) for row in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_weekly_kpi_generation_success(tmp_path: Path):
    events = tmp_path / "events.jsonl"
    output = tmp_path / "weekly.csv"
    _write(
        events,
        [
            {
                "event_id": "evt1",
                "tenant_id": "tenant_a",
                "lead_id": "lead_1",
                "event_type": "lead_received",
                "timestamp": "2026-03-02T10:00:00Z",
            },
            {
                "event_id": "evt2",
                "tenant_id": "tenant_a",
                "lead_id": "lead_1",
                "event_type": "qualified_lead",
                "timestamp": "2026-03-02T10:02:00Z",
            },
            {
                "event_id": "evt3",
                "tenant_id": "tenant_a",
                "lead_id": "lead_1",
                "event_type": "qualified_lead_cost",
                "event_value": 12.5,
                "timestamp": "2026-03-02T10:03:00Z",
            },
        ],
    )

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/generate_weekly_pilot_kpis.py",
            "--events",
            str(events),
            "--out-csv",
            str(output),
        ],
        cwd=str(Path(__file__).resolve().parents[2]),
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, proc.stderr
    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert (
        "tenant_id,week_start,leads_received,qualified_leads,response_sla_pct,appointments_booked,cost_per_qualified_lead"
        in content
    )


def test_weekly_kpi_generation_fails_on_missing_cost_value(tmp_path: Path):
    events = tmp_path / "events.jsonl"
    output = tmp_path / "weekly.csv"
    _write(
        events,
        [
            {
                "event_id": "evt1",
                "tenant_id": "tenant_a",
                "lead_id": "lead_1",
                "event_type": "qualified_lead_cost",
                "timestamp": "2026-03-02T10:03:00Z",
            }
        ],
    )

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/generate_weekly_pilot_kpis.py",
            "--events",
            str(events),
            "--out-csv",
            str(output),
        ],
        cwd=str(Path(__file__).resolve().parents[2]),
        capture_output=True,
        text=True,
    )

    assert proc.returncode != 0
    assert "missing event_value" in (proc.stderr + proc.stdout)
