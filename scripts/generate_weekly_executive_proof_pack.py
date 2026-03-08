#!/usr/bin/env python3
"""Generate weekly executive proof-pack markdown from KPI CSV."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", required=True, help="Tenant ID to render")
    parser.add_argument("--week-start", default=None, help="Week start date (YYYY-MM-DD); defaults to latest")
    parser.add_argument("--kpi-csv", default="reports/weekly_pilot_kpis.csv")
    parser.add_argument("--out-md", default="reports/weekly_executive_proof_pack.md")
    return parser.parse_args()


def load_row(path: Path, tenant_id: str, week_start: str | None) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"Missing KPI CSV: {path}")

    tenant_rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row.get("tenant_id") == tenant_id:
                tenant_rows.append(row)

    if not tenant_rows:
        raise ValueError(f"No KPI records found for tenant_id={tenant_id}")

    if week_start:
        for row in tenant_rows:
            if row.get("week_start") == week_start:
                return row
        raise ValueError(f"No KPI record found for tenant_id={tenant_id}, week_start={week_start}")

    tenant_rows.sort(key=lambda r: r.get("week_start", ""), reverse=True)
    return tenant_rows[0]


def render(row: dict[str, str]) -> str:
    generated_at = datetime.now(timezone.utc).isoformat()
    return f"""# Weekly Executive Proof-Pack

## Tenant
- Tenant ID: {row["tenant_id"]}
- Week Start: {row["week_start"]}
- Report Generated At (UTC): {generated_at}

## KPI Summary
- 5-minute response SLA attainment: {row["response_sla_pct"]}%
- Lead qualification throughput: {row["qualified_leads"]} qualified / {row["leads_received"]} received
- Appointments booked: {row["appointments_booked"]}
- Cost per qualified lead: ${row["cost_per_qualified_lead"]}

## Operational Highlights
- Wins: TODO
- Risks: TODO
- Notable incidents and remediation status: TODO

## Contractual API Health
- GET /api/v2/billing/subscriptions/{{location_id}}: PASS/FAIL
- GET /api/v2/prediction/deal-outcome/{{deal_id}}: PASS/FAIL
- GET /api/v2/customer-journeys/{{lead_id}}: PASS/FAIL
- GET /api/v2/property-intelligence/{{property_id}}: PASS/FAIL
- GET /api/v2/sms-compliance/{{location_id}}: PASS/FAIL
- GET /api/v2/market-intelligence/recommendations/stream: PASS/FAIL

## Next Week Plan
- Contacts target (40): TODO
- Qualified conversations target (8): TODO
- Proposals target (2-3): TODO
"""


def main() -> int:
    args = parse_args()
    row = load_row(Path(args.kpi_csv), args.tenant_id, args.week_start)
    output = render(row)
    out_path = Path(args.out_md)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(output, encoding="utf-8")
    print(f"Wrote executive proof-pack to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
