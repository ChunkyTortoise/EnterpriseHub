# Statement of Work (SOW) - AgentForge SMB Automation

## Scope
Implement AgentForge workflows for:
- Lead qualification
- Appointment follow-up
- Support triage

## Deliverables
- Configured AgentForge project scaffold
- Production deployment pack (Docker, env template, healthcheck, runbook)
- Observability reporting pipeline from run logs (`validate-runlog`, `daily-errors`, `trends`, `roi`)
- Report pack orchestration command for weekly handoff prep (`report pack`)
- Optional JSON mode for report outputs (`--format json`)
- Client handoff artifact bundle (mermaid architecture, API contract summary, ops checklist with owner/status)

## Timeline
- Week 1: Discovery + workflow baseline + scaffold
- Week 2: Workflow implementation + test validation
- Week 3: Deployment + monitoring + handoff

## Acceptance criteria
- Workflows execute successfully in client environment
- Run logs adhere to schema (`run_id`, `workflow`, `latency_ms`, `tokens`, `cost_usd`, `errors`, `timestamp`)
- Daily error and trend reports generate from production logs
- Ops checklist includes owner/status and is completed with client sign-off

## Evidence links
- `/Users/cave/Projects/EnterpriseHub_new/agentforge/tests/test_reporting_integration.py`
- `/Users/cave/Projects/EnterpriseHub_new/agentforge/tests/test_runlog.py`
- `/Users/cave/Projects/EnterpriseHub_new/agentforge/tests/test_cli.py`

## KPIs
- Response-time improvement target: ____
- Conversion improvement target: ____
- Cost/run ceiling: ____
- Error budget per week: ____
