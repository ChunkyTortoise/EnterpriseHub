# AgentForge Revenue-First Further Development Spec

## 1) Purpose
Define a concrete, implementation-ready roadmap for the next development cycle after completion of:
- Phase 1 credibility fixes
- Phase 2 SMB/revenue packaging
- Phase 3 observability pack + incident-safe defaults + hardened handoff artifacts

This spec is intended to drive engineering execution, QA, docs, and release decisions with measurable acceptance criteria.

## 2) Current Baseline (As Of 2026-02-20)
- Full test suite passes locally.
- Coverage is above required threshold (>=80%).
- Structured run log schema + validator/exporter are implemented.
- CLI supports:
  - `agentforge report roi`
  - `agentforge report daily-errors`
  - `agentforge report trends`
  - `agentforge bundle handoff`
  - `agentforge profile`
- Execution profiles exist (`balanced`, `incident-safe`, `resilient`) and are wired into scaffold/template and YAML profile resolution.

## 3) Product Goal
Make AgentForge the default revenue-operations orchestration framework for SMB automation engagements by improving:
- Operational trust (incident behavior, run observability, supportability)
- Deployment velocity (repeatable onboarding + handoff)
- Business alignment (cost/latency/error data tied to workflow outcomes)

## 4) Success Metrics (Release-Level)
- Engineering quality:
  - 0 failing tests in CI
  - coverage >=80%
  - no backward-incompatible CLI changes without migration path
- Operator usability:
  - Time to produce handoff pack from existing run logs <= 5 minutes
  - At least 1 command path to produce weekly exec-ready report bundle
- Reliability posture:
  - Every generated project template defaults to a named execution profile
  - Daily error/trend reports generated from schema-valid logs only

## 5) Scope: Next Development Wave (Phase 4)

### 5.1 Outcome-Linked Reporting Pack
Add reporting focused on business outcomes, not just runtime metrics.

#### Features
- New command:
  - `agentforge report outcomes --input <run_log.json> --output <md> --events <events.json>`
- Correlate run metrics with outcome events (e.g., lead converted, appointment booked).
- Report per-workflow:
  - conversion count/rate
  - cost per conversion
  - average latency for converted vs non-converted runs

#### Data Contract
- `events.json` schema (v1):
  - `event_id` (string, required)
  - `run_id` (string, required)
  - `event_type` (string, required; enum in docs)
  - `event_value` (number, optional)
  - `timestamp` (ISO-8601 string, required)

#### Acceptance Criteria
- Invalid event schema returns non-zero with clear error.
- Output includes per-workflow table and summary recommendations.
- CLI tests cover success + schema failure + empty joins.

### 5.2 Observability Pack Command
Reduce operator command overhead.

#### Features
- New command:
  - `agentforge report pack --input <run_log.json> --output-dir <dir> [--events <events.json>]`
- Generates in one run:
  - `daily-errors.md`
  - `trends.md`
  - `roi.md`
  - `outcomes.md` (if `--events` provided)

#### Acceptance Criteria
- Existing report commands remain unchanged.
- Pack command is additive and deterministic.
- Integration tests assert all files created with expected headings.

### 5.3 Incident-Safe Runtime Guardrails
Move profile behavior from config-time into runtime controls.

#### Features
- Add optional runtime policy hooks in execution engine:
  - max consecutive node failures before soft abort
  - per-workflow error budget hinting in output metadata
- Add profile metadata fields:
  - `description`
  - `intended_use`
  - `risk_tradeoff`

#### Acceptance Criteria
- Default runtime behavior unchanged unless guardrails enabled.
- Guardrail behavior covered by deterministic unit tests.
- Profile display command surfaces new metadata.

### 5.4 Handoff Bundle v2
Increase client handoff completeness for real operations teams.

#### Features
- Extend `bundle handoff` output set:
  - `architecture.md` (existing, keep)
  - `api-contract-summary.md` (existing, keep)
  - `operations-checklist.md` (existing, keep)
  - `incident-runbook.md` (new)
  - `sla-slo-template.md` (new)
- Incident runbook sections:
  - alert intake
  - triage workflow
  - rollback and containment
  - escalation matrix

#### Acceptance Criteria
- Bundle command writes all artifacts atomically (all-or-fail behavior).
- Ops checklist still includes owner/status table.
- Tests validate presence and minimum key sections in new docs.

### 5.5 CLI UX and Validation Hardening

#### Features
- Consistent error messaging format:
  - `Error: <reason>.`
- Add `--format markdown|json` to report commands (default markdown).
- Add strict path checks for output collisions unless `--overwrite` passed.

#### Acceptance Criteria
- Backward-compatible defaults.
- JSON output is schema-documented and test-covered.

## 6) Technical Design

### 6.1 Modules
- `agentforge/observe/runlog.py`
  - keep schema/aggregation logic
  - extend with outcome correlation models
- `agentforge/cli/main.py`
  - route new `report outcomes` and `report pack`
  - add format/overwrite switches
- `agentforge/core/profiles.py`
  - enrich profile metadata
- `agentforge/core/engine.py`
  - optional runtime guardrails

### 6.2 Backward Compatibility Rules
- Do not remove existing commands or arguments.
- New args must be optional unless introducing new subcommand.
- Existing markdown report sections should retain current headings where possible.

### 6.3 Determinism Rules
- Tests/examples use mock provider only.
- Report ordering must be deterministic:
  - workflows sorted asc
  - days sorted asc

## 7) Test Strategy

### 7.1 Unit Tests
- Run log/event schema validation:
  - valid/invalid payloads
  - edge cases for empty errors and missing optional fields
- Profile resolution:
  - defaults
  - explicit override precedence

### 7.2 CLI Tests
- New commands:
  - `report outcomes`
  - `report pack`
- Output format tests:
  - markdown headings
  - json schema keys
- Negative tests:
  - missing input
  - invalid schema
  - output exists without `--overwrite`

### 7.3 Integration Tests
- End-to-end bundle/report generation from fixture logs.
- Verify generated files include required contract sections.

## 8) Documentation Plan
- Update README CLI section with only verifiable commands and paths.
- Add `docs/REPORT_SCHEMAS.md`:
  - run_log schema v1
  - events schema v1
  - json report output schema
- Add `docs/OPERATIONS_PLAYBOOK.md`:
  - daily/weekly operating cadence
  - incident-safe profile usage guidance

## 9) Delivery Plan (Execution Order)
1. Implement outcome schema + correlation report logic.
2. Implement report pack command.
3. Add runtime guardrail hooks + tests.
4. Expand handoff bundle v2 artifacts.
5. Finalize docs + fixtures.
6. Run full test suite and coverage checks.

## 10) Definition of Done (Phase 4)
- All planned Phase 4 commands implemented and tested.
- Full test suite green.
- Coverage >=80%.
- README/docs updated with no unverifiable claims.
- Handoff and report outputs are reproducible from included fixtures.

## 11) Risks and Mitigations
- Risk: Schema drift between markdown and json outputs.
  - Mitigation: shared typed models + golden fixture tests.
- Risk: CLI growth reduces maintainability.
  - Mitigation: extract report command handlers into dedicated module (`agentforge/cli/reporting.py`).
- Risk: Runtime guardrails change behavior unexpectedly.
  - Mitigation: feature-flag guardrails and default-off.

## 12) Suggested Ticket Breakdown
- AF-401: Outcome event schema + validator + model exports
- AF-402: `report outcomes` CLI + markdown/json renderers
- AF-403: `report pack` orchestration command
- AF-404: Runtime guardrail hooks in engine
- AF-405: Handoff bundle v2 docs artifacts
- AF-406: CLI output-format + overwrite policy
- AF-407: Docs update (`README`, `REPORT_SCHEMAS`, `OPERATIONS_PLAYBOOK`)
- AF-408: Full regression + coverage gate run

## 13) Open Decisions (Need Product/Client Input)
- Canonical list of outcome event types for SMB verticals.
- Whether to include revenue currency normalization in outcome reports.
- Preferred JSON schema versioning policy (`1.0`, `1.1`, etc.).
