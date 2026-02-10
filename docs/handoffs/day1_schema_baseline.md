# Day 1 Schema Baseline

Date: 2026-02-09  
Owner: A0 (Coordinator)  
Status: Approved for Day 1 and Day 2 entry gate

## 1) Handoff Confidence Schema (WS3)

Required fields for routing/handoff events:

- `mode` (string): `seller`, `buyer`, `lead`, `fallback`
- `score` (number): normalized confidence score in `[0.0, 1.0]`
- `reason` (string): short reason code for selected routing path
- `evidence` (object): supporting tags/signals used by classifier/router

## 2) WS2 Completeness and Numeric Parsing Baseline

Required seller data categories for completeness checks:

- Timeline context
- Price expectation or range
- Mortgage/liens context
- Repairs/condition context
- Motivation/next-step intent

Numeric parser behavior contract:

- Bounded retries only (no unbounded loops)
- Retry limit must be explicit constant
- Unrecoverable parse/write failures emit structured warning event

## 3) WS4/WS6 KPI Telemetry Contract Baseline

Required KPI telemetry fields:

- `tenant_id`
- `job_id`
- `job_status`
- `started_at`
- `finished_at`
- `duration_ms`
- `retry_count`
- `timed_out` (boolean)
- `freshness_age_hours`

## 4) Compatibility and Controls

- Preserve backward compatibility for existing consumers where possible.
- Any new required field must include defaulting/backfill behavior.
- A5 test fixtures are source of truth for regression validation.

## 5) Approval Record

- Approved by: A0
- Effective for: Day 1 and Day 2 (unless superseded by approved delta)
- Supersedes: none

## 6) Day 2 A3 Verification Addendum (2026-02-10)

- Contract delta: `none`.
- WS3 schema remains: `mode`, `score`, `reason`, `evidence`.
- Routing-surface integration note:
  - Seller and buyer webhook interaction telemetry now records handoff confidence after deterministic routing evaluation, matching lead route semantics while preserving schema shape.
