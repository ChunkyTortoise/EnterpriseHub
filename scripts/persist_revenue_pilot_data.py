#!/usr/bin/env python3
"""Persist outcome events and weekly KPI records into PostgreSQL when available."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ghl_real_estate_ai.api.schemas.revenue_v2 import OutcomeEvent, PilotKPIRecord
from ghl_real_estate_ai.services.database_service import get_database

EXIT_OK = 0
EXIT_INPUT_ERROR = 2
EXIT_DB_UNAVAILABLE = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", default="reports/outcome_events.jsonl")
    parser.add_argument("--kpis", default="reports/weekly_pilot_kpis.csv")
    parser.add_argument(
        "--allow-db-unavailable",
        action="store_true",
        help="Exit 0 when DB is unavailable (for CI smoke checks without external DB).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and report counts without persisting to DB.",
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
            raise ValueError(f"Invalid JSON line {idx}: {exc}") from exc
        events.append(OutcomeEvent.model_validate(payload))
    return events


def load_kpis(path: Path) -> list[PilotKPIRecord]:
    if not path.exists():
        raise FileNotFoundError(f"Missing KPI CSV: {path}")

    records: list[PilotKPIRecord] = []
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            records.append(PilotKPIRecord.model_validate(row))
    return records


async def persist(events: list[OutcomeEvent], kpis: list[PilotKPIRecord]) -> None:
    db = await get_database()
    async with db.get_connection() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS outcome_events (
                event_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                lead_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_value DOUBLE PRECISION,
                timestamp TIMESTAMPTZ NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pilot_kpi_records (
                tenant_id TEXT NOT NULL,
                week_start DATE NOT NULL,
                leads_received INTEGER NOT NULL,
                qualified_leads INTEGER NOT NULL,
                response_sla_pct DOUBLE PRECISION NOT NULL,
                appointments_booked INTEGER NOT NULL,
                cost_per_qualified_lead DOUBLE PRECISION NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (tenant_id, week_start)
            )
            """
        )

        for event in events:
            await conn.execute(
                """
                INSERT INTO outcome_events (event_id, tenant_id, lead_id, event_type, event_value, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (event_id) DO UPDATE SET
                    tenant_id = EXCLUDED.tenant_id,
                    lead_id = EXCLUDED.lead_id,
                    event_type = EXCLUDED.event_type,
                    event_value = EXCLUDED.event_value,
                    timestamp = EXCLUDED.timestamp
                """,
                event.event_id,
                event.tenant_id,
                event.lead_id,
                event.event_type,
                event.event_value,
                event.timestamp,
            )

        for row in kpis:
            await conn.execute(
                """
                INSERT INTO pilot_kpi_records (
                    tenant_id, week_start, leads_received, qualified_leads,
                    response_sla_pct, appointments_booked, cost_per_qualified_lead
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (tenant_id, week_start) DO UPDATE SET
                    leads_received = EXCLUDED.leads_received,
                    qualified_leads = EXCLUDED.qualified_leads,
                    response_sla_pct = EXCLUDED.response_sla_pct,
                    appointments_booked = EXCLUDED.appointments_booked,
                    cost_per_qualified_lead = EXCLUDED.cost_per_qualified_lead,
                    updated_at = NOW()
                """,
                row.tenant_id,
                row.week_start,
                row.leads_received,
                row.qualified_leads,
                row.response_sla_pct,
                row.appointments_booked,
                row.cost_per_qualified_lead,
            )

    print(f"Persisted {len(events)} outcome events and {len(kpis)} KPI rows")


async def main() -> int:
    args = parse_args()
    try:
        events = load_events(Path(args.events))
        kpis = load_kpis(Path(args.kpis))
    except Exception as exc:
        print(f"INPUT_ERROR: {exc}")
        return EXIT_INPUT_ERROR

    if args.dry_run:
        print(f"DRY_RUN_OK: validated {len(events)} outcome events and {len(kpis)} KPI rows")
        return EXIT_OK

    try:
        await persist(events, kpis)
        print("PERSIST_OK")
        return EXIT_OK
    except Exception as exc:
        if args.allow_db_unavailable:
            print(f"DB_UNAVAILABLE_SKIPPED: {exc}")
            return EXIT_OK
        print(f"DB_ERROR: {exc}")
        return EXIT_DB_UNAVAILABLE


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
