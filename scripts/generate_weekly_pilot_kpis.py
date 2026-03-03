#!/usr/bin/env python3
"""Generate weekly pilot KPI records from outcome events (fails fast on invalid input)."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ghl_real_estate_ai.api.schemas.revenue_v2 import OutcomeEvent, PilotKPIRecord


def _week_start(ts: datetime) -> datetime.date:
    utc_ts = ts.astimezone(timezone.utc)
    return (utc_ts - timedelta(days=utc_ts.weekday())).date()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--events",
        default="reports/outcome_events.jsonl",
        help="JSONL outcome events file",
    )
    parser.add_argument(
        "--out-csv",
        default="reports/weekly_pilot_kpis.csv",
        help="Output CSV path",
    )
    return parser.parse_args()


def load_events(path: Path) -> list[OutcomeEvent]:
    if not path.exists():
        raise FileNotFoundError(f"Missing events file: {path}")

    events: list[OutcomeEvent] = []
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {idx}: {exc}") from exc

        # Fail fast on schema issues.
        events.append(OutcomeEvent.model_validate(payload))

    if not events:
        raise ValueError("No valid outcome events found")

    return events


def compute_kpis(events: list[OutcomeEvent]) -> list[PilotKPIRecord]:
    buckets: dict[tuple[str, datetime.date], dict[str, float]] = defaultdict(
        lambda: {
            "leads_received": 0,
            "qualified_leads": 0,
            "appointments_booked": 0,
            "response_sla_hits": 0,
            "response_sla_total": 0,
            "cost_sum": 0.0,
            "cost_count": 0,
        }
    )

    for event in events:
        key = (event.tenant_id, _week_start(event.timestamp))
        bucket = buckets[key]

        if event.event_type == "lead_received":
            bucket["leads_received"] += 1
        elif event.event_type == "qualified_lead":
            bucket["qualified_leads"] += 1
        elif event.event_type == "appointment_booked":
            bucket["appointments_booked"] += 1
        elif event.event_type == "sla_hit":
            bucket["response_sla_hits"] += 1
            bucket["response_sla_total"] += 1
        elif event.event_type == "sla_miss":
            bucket["response_sla_total"] += 1
        elif event.event_type == "qualified_lead_cost":
            if event.event_value is None:
                raise ValueError(
                    f"qualified_lead_cost event is missing event_value (event_id={event.event_id})"
                )
            bucket["cost_sum"] += float(event.event_value)
            bucket["cost_count"] += 1

    records: list[PilotKPIRecord] = []
    for (tenant_id, week_start), values in sorted(buckets.items(), key=lambda item: (item[0][0], item[0][1])):
        total = int(values["response_sla_total"])
        hits = int(values["response_sla_hits"])
        response_sla_pct = round((hits / total * 100.0), 2) if total else 0.0

        cost_count = int(values["cost_count"])
        cost_per_qualified_lead = round(values["cost_sum"] / cost_count, 2) if cost_count else 0.0

        records.append(
            PilotKPIRecord(
                tenant_id=tenant_id,
                week_start=week_start,
                leads_received=int(values["leads_received"]),
                qualified_leads=int(values["qualified_leads"]),
                response_sla_pct=response_sla_pct,
                appointments_booked=int(values["appointments_booked"]),
                cost_per_qualified_lead=cost_per_qualified_lead,
            )
        )

    return records


def write_csv(path: Path, records: list[PilotKPIRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "tenant_id",
                "week_start",
                "leads_received",
                "qualified_leads",
                "response_sla_pct",
                "appointments_booked",
                "cost_per_qualified_lead",
            ]
        )
        for record in records:
            writer.writerow(
                [
                    record.tenant_id,
                    record.week_start.isoformat(),
                    record.leads_received,
                    record.qualified_leads,
                    record.response_sla_pct,
                    record.appointments_booked,
                    record.cost_per_qualified_lead,
                ]
            )


def main() -> int:
    args = parse_args()
    events = load_events(Path(args.events))
    records = compute_kpis(events)
    write_csv(Path(args.out_csv), records)
    print(f"Wrote {len(records)} weekly KPI rows to {args.out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
