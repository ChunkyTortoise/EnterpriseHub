from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_generate_weekly_executive_proof_pack_success(tmp_path: Path):
    csv_path = tmp_path / "kpis.csv"
    csv_path.write_text(
        "tenant_id,week_start,leads_received,qualified_leads,response_sla_pct,appointments_booked,cost_per_qualified_lead\n"
        "tenant_demo,2026-03-03,12,7,91.2,3,19.5\n",
        encoding="utf-8",
    )
    out_path = tmp_path / "proof-pack.md"

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/generate_weekly_executive_proof_pack.py",
            "--tenant-id",
            "tenant_demo",
            "--week-start",
            "2026-03-03",
            "--kpi-csv",
            str(csv_path),
            "--out-md",
            str(out_path),
        ],
        cwd=str(Path(__file__).resolve().parents[2]),
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, proc.stderr
    assert out_path.exists()
    text = out_path.read_text(encoding="utf-8")
    assert "Tenant ID: tenant_demo" in text
    assert "Cost per qualified lead: $19.5" in text


def test_generate_weekly_executive_proof_pack_missing_row_fails(tmp_path: Path):
    csv_path = tmp_path / "kpis.csv"
    csv_path.write_text(
        "tenant_id,week_start,leads_received,qualified_leads,response_sla_pct,appointments_booked,cost_per_qualified_lead\n"
        "tenant_demo,2026-03-03,12,7,91.2,3,19.5\n",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/generate_weekly_executive_proof_pack.py",
            "--tenant-id",
            "tenant_other",
            "--week-start",
            "2026-03-03",
            "--kpi-csv",
            str(csv_path),
            "--out-md",
            str(tmp_path / "proof-pack.md"),
        ],
        cwd=str(Path(__file__).resolve().parents[2]),
        capture_output=True,
        text=True,
    )

    assert proc.returncode != 0
    assert "No KPI record found" in (proc.stderr + proc.stdout)
