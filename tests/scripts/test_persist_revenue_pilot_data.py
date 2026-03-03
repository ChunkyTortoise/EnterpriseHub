from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _write_events(path: Path) -> None:
    rows = [
        {
            "event_id": "evt_1",
            "tenant_id": "tenant_demo",
            "lead_id": "lead_1",
            "event_type": "lead_received",
            "timestamp": "2026-03-03T10:00:00Z",
        }
    ]
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def _write_kpis(path: Path) -> None:
    path.write_text(
        "tenant_id,week_start,leads_received,qualified_leads,response_sla_pct,appointments_booked,cost_per_qualified_lead\n"
        "tenant_demo,2026-03-03,12,7,91.2,3,19.5\n",
        encoding="utf-8",
    )


def test_persist_script_dry_run_success(tmp_path: Path):
    events = tmp_path / "events.jsonl"
    kpis = tmp_path / "kpis.csv"
    _write_events(events)
    _write_kpis(kpis)

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/persist_revenue_pilot_data.py",
            "--events",
            str(events),
            "--kpis",
            str(kpis),
            "--dry-run",
        ],
        cwd=str(Path(__file__).resolve().parents[2]),
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0
    assert "DRY_RUN_OK" in (proc.stdout + proc.stderr)


def test_persist_script_input_error_exit_code(tmp_path: Path):
    missing_events = tmp_path / "missing.jsonl"
    kpis = tmp_path / "kpis.csv"
    _write_kpis(kpis)

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/persist_revenue_pilot_data.py",
            "--events",
            str(missing_events),
            "--kpis",
            str(kpis),
            "--dry-run",
        ],
        cwd=str(Path(__file__).resolve().parents[2]),
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 2
    assert "INPUT_ERROR" in (proc.stdout + proc.stderr)


def test_persist_script_allow_db_unavailable_is_ci_safe(tmp_path: Path):
    events = tmp_path / "events.jsonl"
    kpis = tmp_path / "kpis.csv"
    _write_events(events)
    _write_kpis(kpis)

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/persist_revenue_pilot_data.py",
            "--events",
            str(events),
            "--kpis",
            str(kpis),
            "--allow-db-unavailable",
        ],
        cwd=str(Path(__file__).resolve().parents[2]),
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0
    out = proc.stdout + proc.stderr
    assert ("PERSIST_OK" in out) or ("DB_UNAVAILABLE_SKIPPED" in out)
