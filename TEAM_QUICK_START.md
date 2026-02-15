# Portfolio & GHL Team - Quick Start Guide

**Read full spec**: [`PORTFOLIO_GHL_TEAM_SPEC.md`](./PORTFOLIO_GHL_TEAM_SPEC.md)

---

## 🚀 Quick Start (For Claude)

### 1. Create Team
```python
TeamCreate(
    team_name="portfolio-ghl-team",
    description="Portfolio quick-wins (Formspree + GA4) and GHL field validation",
    agent_type="portfolio-coordinator"
)
```

### 2. Create Tasks (in parallel)
```python
# Task 1: Fix Formspree Form
TaskCreate(
    subject="Fix Formspree email form on portfolio",
    description="Create Formspree account, get form ID, update index.html:55, test, commit. Closes: EnterpriseHub-weekly-plan-001",
    activeForm="Fixing Formspree email form"
)

# Task 2: Add Google Analytics
TaskCreate(
    subject="Add GA4 tracking to portfolio sites",
    description="Create GA4 property, add tracking to all pages, configure events, test, commit. Closes: EnterpriseHub-weekly-plan-002",
    activeForm="Adding Google Analytics tracking"
)

# Task 3: Validate GHL Setup
TaskCreate(
    subject="List GHL fields, create missing, populate .env",
    description="Use jorge_ghl_setup to list fields, create missing, update .env with IDs, validate, test. Closes: EnterpriseHub-mq1g. BLOCKED: Needs GHL_API_KEY and GHL_LOCATION_ID in .env first.",
    activeForm="Validating GHL integration setup"
)

# Task 4: Quality Validation
TaskCreate(
    subject="Validate all deliverables",
    description="Test Formspree form, verify GA4 tracking, validate GHL integration. Create test reports.",
    activeForm="Validating all deliverables"
)

# Task 5: Create Documentation
TaskCreate(
    subject="Document Formspree, GA4, and GHL setup",
    description="Create reference guides for all three systems. Capture lessons learned.",
    activeForm="Creating documentation"
)
```

### 3. Spawn Agents (in parallel)
```python
# Marketing Agent - Formspree
Task(
    subagent_type="general-purpose",
    description="Fix Formspree form",
    team_name="portfolio-ghl-team",
    name="marketing-agent",
    prompt="""You are the marketing agent for portfolio-ghl-team.

Your task: Fix Formspree email form on chunkytortoise.github.io

Steps:
1. Clone repo: git clone https://github.com/ChunkyTortoise/chunkytortoise.github.io.git
2. Create Formspree account at formspree.io (chunktort@gmail.com)
3. Create form: "Portfolio Contact Form"
4. Get form ID
5. Update index.html:55 - replace YOUR_FORM_ID with real ID
6. Test form submission
7. Commit and push
8. Verify live deployment
9. Close beads issue: bd close EnterpriseHub-weekly-plan-001
10. Report completion to team lead

See PORTFOLIO_GHL_TEAM_SPEC.md section A1 for full details."""
)

# Analytics Agent - GA4
Task(
    subagent_type="general-purpose",
    description="Setup Google Analytics",
    team_name="portfolio-ghl-team",
    name="analytics-agent",
    prompt="""You are the analytics agent for portfolio-ghl-team.

Your task: Add Google Analytics 4 tracking to portfolio sites

Steps:
1. Create GA4 property at analytics.google.com (chunktort@gmail.com)
2. Property name: "ChunkyTortoise Portfolio"
3. Get Measurement ID (G-XXXXXXXXXX)
4. Add tracking code to chunkytortoise.github.io (all HTML pages)
5. Configure enhanced measurement
6. Test real-time tracking
7. Commit and push
8. Verify live deployment
9. Close beads issue: bd close EnterpriseHub-weekly-plan-002
10. Report completion to team lead

See PORTFOLIO_GHL_TEAM_SPEC.md section A2 for full details."""
)

# GHL Integration Agent
Task(
    subagent_type="api-consistency",
    description="Validate GHL integration",
    team_name="portfolio-ghl-team",
    name="ghl-integration-agent",
    prompt="""You are the GHL integration agent for portfolio-ghl-team.

Your task: Validate GHL custom field setup

BLOCKER: This task requires GHL_API_KEY and GHL_LOCATION_ID in .env file.
If not present, notify team lead and wait.

Steps (after credentials provided):
1. python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup --action=list
2. python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup --action=create
3. Update .env with all field IDs
4. python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup --action=validate
5. python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup --action=test
6. Create docs/GHL_FIELD_REFERENCE.md
7. Commit and push (exclude .env if sensitive)
8. Close beads issue: bd close EnterpriseHub-mq1g
9. Report completion to team lead

See PORTFOLIO_GHL_TEAM_SPEC.md section B1 for full details."""
)
```

### 4. Monitor Progress
- Check team status: `cat ~/.claude/teams/portfolio-ghl-team/status.md`
- Check task list: `TaskList`
- Receive agent messages automatically

### 5. Final Steps (Team Lead)
- Validate all work completed
- Run `bd sync` to sync beads
- Run `git push` to push changes
- Generate final report
- Shutdown team: `TeamDelete`

---

## 📋 Checklist (Copy-Paste)

**Before Starting:**
```
[ ] GHL credentials ready (or acknowledge Workstream B blocked)
[ ] Read full spec: PORTFOLIO_GHL_TEAM_SPEC.md
[ ] Understand success criteria
[ ] Ready to monitor for 4-5 hours
```

**Team Creation:**
```
[ ] TeamCreate (portfolio-ghl-team)
[ ] TaskCreate (5 tasks)
[ ] Spawn marketing-agent
[ ] Spawn analytics-agent
[ ] Spawn ghl-integration-agent
```

**Execution:**
```
[ ] Monitor agent messages
[ ] Respond to blockers
[ ] Validate intermediate outputs
```

**Completion:**
```
[ ] All 3 beads issues closed
[ ] All changes committed and pushed
[ ] Documentation created
[ ] Team report generated
[ ] Team shutdown
```

---

## ⚠️ Critical User Actions Required

### GHL Credentials (BLOCKING for Workstream B)
```bash
# Add to EnterpriseHub/.env
GHL_API_KEY=your_actual_api_key_here
GHL_LOCATION_ID=your_actual_location_id_here
```

How to get:
1. Log into GoHighLevel
2. Settings → Integrations → API → Generate Key
3. Dashboard URL: `app.gohighlevel.com/location/{LOCATION_ID}/`

### Account Access (for Workstream A)
- **Formspree**: chunktort@gmail.com (agent can create account)
- **Google Analytics**: chunktort@gmail.com (agent can create property)

---

## 🎯 Expected Outputs

### Beads Issues Closed
- ✓ EnterpriseHub-weekly-plan-001 (Formspree)
- ✓ EnterpriseHub-weekly-plan-002 (GA4)
- ✓ EnterpriseHub-mq1g (GHL fields)

### Files Changed
```
chunkytortoise.github.io/
├── index.html (updated)
└── *.html (GA4 tracking added)

EnterpriseHub/
├── .env (GHL field IDs - NOT committed)
├── ghl_real_estate_ai/docs/GHL_FIELD_REFERENCE.md (NEW)
├── docs/FORMSPREE_SETUP.md (NEW)
└── docs/GA4_SETUP.md (NEW)
```

### Git Commits
- 3-5 commits following conventional format
- All linked to beads issues
- All pushed to remote

---

## 🚨 Troubleshooting

### Agent Not Responding
- Check if idle (normal between tasks)
- Send message: `SendMessage(type="message", recipient="agent-name", content="Status check?")`
- If stuck >30min, spawn debugging agent

### GHL Task Blocked
- Verify .env has GHL_API_KEY and GHL_LOCATION_ID
- Test: `python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup --action=list`
- If still fails, update beads issue with details

### Portfolio Repo Not Found
- Clone manually: `git clone https://github.com/ChunkyTortoise/chunkytortoise.github.io.git`
- Verify path: `ls ~/chunkytortoise.github.io/`

---

## 📊 Timeline

| Time | Activity |
|------|----------|
| 0:00 | Team creation + agent spawning |
| 0:10 | Agents start parallel work |
| 1:30 | Formspree complete (expected) |
| 2:00 | GA4 complete (expected) |
| 2:30 | GHL validation complete (expected) |
| 3:00 | Quality validation |
| 3:30 | Documentation |
| 4:00 | Final commits + beads sync |
| 4:15 | Team shutdown |

**Total**: 4-5 hours

---

## 📞 Communication Protocol

### Agent → Team Lead
Every 30 minutes:
```
Status: [in_progress|blocked|completed]
Task: [task_name]
Progress: [X%]
Blockers: [none|list]
Next: [next_steps]
```

### Team Lead → User
On blockers or completion:
```
Team Status: [summary]
Completed: [list]
Blockers: [list with user actions needed]
Next: [what's happening next]
```

---

**Ready to execute?** Review spec, confirm GHL credentials, then proceed!
