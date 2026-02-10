# Day 1 Contract Freeze

Date: 2026-02-09  
Owner: A0 (Coordinator)  
Status: Active

## Freeze Window

- Start: 2026-02-09 09:00 local
- End: 2026-02-09 18:00 local
- Rule: No schema or contract changes merge without A0 approval and explicit update to `day1_schema_baseline.md`.

## Shared Contracts Locked for Day 1

1. WS2/WS3 shared handoff event shape.
2. Routing confidence schema: `mode`, `score`, `reason`, `evidence`.
3. WS4/WS6 KPI telemetry fields required for freshness/error alerting.
4. Tenant attribution field requirements for outbound paths.

## Ownership Map

- A1: WS1 (`T1.1`, `T1.2`)
- A2: WS2 (`T2.1`, `T2.2`)
- A3: WS3 (`T3.1`, `T3.2`)
- A4: WS4 (`T4.1`, `T4.2`)
- A5: WS5 (`T5.1`, `T5.4 seed`)
- A6: WS6 (`T6.1`, `T6.2`)

## Change Control

1. Agent proposes contract change in PR description with rationale.
2. A0 reviews impact to WS2, WS3, WS4, WS6 and QA fixtures.
3. If approved, A0 updates schema baseline and posts digest note.
4. If rejected, change is deferred to next freeze window.

## Day 1 Required Outputs

- `docs/handoffs/day1_schema_baseline.md`
- `docs/handoffs/day1_gate_checklist.md`
- `docs/handoffs/day1_execution_digest.md`
