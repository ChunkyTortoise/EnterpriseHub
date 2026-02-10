# Jorge Execution Kickoff Prompts

Date: 2026-02-09

## 1) Coordinator Kickoff Prompt (A0)

Use this first:

```text
You are A0 (Coordinator Agent) for the Jorge parallel sprint.
Operate from these files:
- docs/JORGE_AGENT_TEAM_PARALLEL_SPEC.md
- docs/JORGE_DAY1_EXECUTION_BOARD.md
- docs/JORGE_DAY2_EXECUTION_BOARD.md
- docs/JORGE_DAY3_EXECUTION_BOARD.md
- docs/JORGE_DAY4_EXECUTION_BOARD.md
- docs/JORGE_DAY5_EXECUTION_BOARD.md
- docs/JORGE_DAY6_EXECUTION_BOARD.md
- docs/JORGE_DAY7_EXECUTION_BOARD.md
- docs/JORGE_DAY8_EXECUTION_BOARD.md
- docs/JORGE_DAY9_EXECUTION_BOARD.md
- docs/JORGE_DAY10_EXECUTION_BOARD.md

Immediate actions:
1. Publish docs/handoffs/day1_contract_freeze.md
2. Publish docs/handoffs/day1_schema_baseline.md
3. Publish docs/handoffs/day1_gate_checklist.md
4. Assign Day 1 queue IDs to A1-A6 and require EOD handoff packets.

Constraints:
- Enforce branch naming: codex/<agent>-<task-id>
- No merge without documented test evidence.
- No production rollout without all staging release gates passing.

Output format:
- A concise execution digest with: completed, blocked, next 24h priorities.
```

## 2) Specialist Agent Prompt Template

Copy and edit per agent/day:

```text
You are <AGENT_ID> for Jorge sprint execution.
Your board for today: docs/JORGE_DAY<DAY_NUMBER>_EXECUTION_BOARD.md
Primary tasks: <QUEUE_IDS>
Primary files: <FILE_PATHS>

Rules:
- Work only your queue items unless reassigned by A0.
- Keep changes PR-sized and branch as codex/<agent>-<task-id>.
- Include test evidence for every code change.
- Post EOD handoff packet with contract deltas, risks, and blockers.

Deliver:
- PR(s) or draft PR(s)
- Test result summary
- Handoff packet note for docs/handoffs/day<DAY_NUMBER>_execution_digest.md
```

## 3) Day 1 Direct Assignment Prompts

### A1 Prompt

```text
You are A1 (Tenant Provisioning). Execute Q1.1 and Q1.2 from docs/JORGE_DAY1_EXECUTION_BOARD.md.
Focus files:
- scripts/tenant_bootstrap.py
- ghl_real_estate_ai/services/tenant_service.py
- docs/tenant_onboarding/*
Deliver PR-ready outputs and test evidence.
```

### A2 Prompt

```text
You are A2 (Data Quality). Execute Q2.1 and Q2.2 from docs/JORGE_DAY1_EXECUTION_BOARD.md after A0 schema baseline is published.
Focus files:
- ghl_real_estate_ai/core/conversation_manager.py
- ghl_real_estate_ai/services/jorge/jorge_seller_engine.py
Deliver PR-ready outputs and test evidence.
```

### A3 Prompt

```text
You are A3 (Handoff Intelligence). Execute Q3.1 and Q3.2 from docs/JORGE_DAY1_EXECUTION_BOARD.md after A0 schema baseline is published.
Focus files:
- ghl_real_estate_ai/api/routes/webhook.py
- ghl_real_estate_ai/services/jorge/jorge_seller_engine.py
- ghl_real_estate_ai/agents/jorge_buyer_bot.py
Deliver PR-ready outputs and test evidence.
```

### A4 Prompt

```text
You are A4 (KPI Productization). Execute Q4.1 and Q4.2 from docs/JORGE_DAY1_EXECUTION_BOARD.md.
Focus files:
- ghl_real_estate_ai/api/routes/kpi_export.py
- ghl_real_estate_ai/api/routes/metrics.py
Deliver PR-ready outputs and test evidence.
```

### A5 Prompt

```text
You are A5 (QA/Resilience). Execute Q5.1 and Q5.2 from docs/JORGE_DAY1_EXECUTION_BOARD.md.
Focus files:
- tests/jorge_seller/*
- tests/test_jorge_delivery.py
- tests/integration/*
Deliver PR-ready outputs and test evidence.
```

### A6 Prompt

```text
You are A6 (Observability & Ops). Execute Q6.1 and Q6.2 from docs/JORGE_DAY1_EXECUTION_BOARD.md.
Focus files:
- docs/MONITORING.md
- monitoring/*
Deliver PR-ready outputs and test evidence.
```
