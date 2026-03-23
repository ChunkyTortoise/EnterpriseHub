# AgentForge SMB Implementation Checklist

## Pre-sales
- Confirm client workflow goal (lead qualification, follow-up, support triage).
- Confirm KPI baseline (response time, conversion rate, cost/run).
- Confirm data handling constraints (PII/PHI rules).

## Build
- Initialize scaffold: `agentforge init <project> --template smb-service --execution-profile incident-safe`.
- Configure providers (`mock` for dry runs, production provider for live).
- Validate DAG execution with sample inputs.
- Enable run log schema output for every workflow run (`schema_version` + `runs[]` envelope).
- Validate run logs with AgentForge run-log schema validator utilities before report generation.

## Deploy
- Package Docker + `.env.example` + healthcheck.
- Create handoff bundle: `agentforge bundle handoff --output-dir ./handoff --project <name> --execution-profile incident-safe`.
- Verify report generation from run logs:
  - `agentforge report validate-runlog --input <run_log.json> --output <validate-runlog.md>`
  - `agentforge report daily-errors --input <run_log.json> --output <daily-errors.md>`
  - `agentforge report trends --input <run_log.json> --output <trends.md>`
  - `agentforge report roi --input <run_log.json> --output <roi.md>`
  - `agentforge report pack --input <run_log.json> --output-dir <reports_dir>`
  - Optional structured outputs: add `--format json` to report commands.
- Confirm handoff artifacts include mermaid architecture diagram, API contract summary, and ops checklist owner/status table.

## Evidence links
- `/Users/cave/Projects/EnterpriseHub_new/agentforge/tests/test_reporting_integration.py`
- `/Users/cave/Projects/EnterpriseHub_new/agentforge/tests/test_runlog.py`
- `/Users/cave/Projects/EnterpriseHub_new/agentforge/tests/test_cli.py`

## Week-1 metrics
- Qualified leads/day
- Time to first response
- Follow-up reply rate
- Cost per run
- Error count/day
