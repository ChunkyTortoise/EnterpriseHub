# Content Development Team - Quick Reference Card

**Purpose**: One-page cheat sheet for executing the content dev sprint
**Full Docs**: See `CONTENT_DEV_TEAM_SPEC.md` and `CONTENT_DEV_EXECUTION_RUNBOOK.md`

---

## Team At-A-Glance

```
Team: content-dev-team
Lead: portfolio-coordinator
Agents: 5 (video, visual, tech, copy, qa)
Deliverables: 23 assets
Timeline: 8-12 hours (vs 45h sequential)
Parallelization: 4-6x speedup
```

---

## Agent Roster

| Agent | Type | Focus | Deliverables |
|-------|------|-------|--------------|
| **video-agent** | content-marketing-engine | Scripts & guides | 6 video assets |
| **visual-agent** | dashboard-design | Screenshots & graphics | 6 visual specs |
| **tech-agent** | architecture-sentinel | Technical docs | 5 technical assets |
| **copy-agent** | content-marketing-engine | Marketing copy | 6 copy assets |
| **qa-agent** | quality-gate | Validation | 4 quality gates |

---

## Execution Phases

### Session 1: Setup + Wave 1 (4h)
```
[15m] Create 23 tasks (bd create x23)
[5m]  Set dependencies (bd dep add)
[5m]  Create team (TeamCreate)
[10m] Spawn 5 agents (5x Task tool)
[10m] Assign Wave 1 tasks
[3h]  Agents work (parallel)
[30m] QA Gate 1 validation
```

### Session 2: Wave 2 + Wave 3 (6h)
```
[5m]  Assign Wave 2 tasks
[3h]  Wave 2 execution
[30m] QA Gate 2 validation
[5m]  Assign Wave 3 tasks
[3h]  Wave 3 execution
[30m] QA Gate 3 validation
```

### Session 3: Final + Wrap (2h)
```
[1h]  QA Gate 4 (final validation)
[15m] Git commit & push
[10m] Close beads tasks
[5m]  Push changes
[10m] Shutdown team
[10m] Update portfolio status
```

---

## Wave Breakdown

### Wave 1 (Parallel - 3h wall-clock)
**Video**: 5 scripts + recording guide
**Visual**: 5 screenshot specs + master plan
**Tech**: 3 competitive matrices

### Wave 2 (Mixed - 3h wall-clock)
**Tech**: ROI calculator (spec → code, sequential)
**Copy**: 3 For-Executives docs (parallel)

### Wave 3 (Parallel - 3h wall-clock)
**Copy**: 3 case studies
**Visual**: Metrics graphics

### Wave 4 (Sequential - 2h)
**QA**: Final validation
**Lead**: Commit, close, push, shutdown

---

## Critical Commands

### Beads Task Management
```bash
# Create tasks
bd create --title="Task" --type=task --priority=0

# List tasks
bd list --status=open
bd ready  # Show unblocked tasks

# Update tasks
bd update beads-xxx --status=in_progress --assignee=agent

# Close tasks (batch)
bd close beads-xxx beads-yyy beads-zzz

# Dependencies
bd dep add beads-dependent beads-blocker

# Sync
bd sync
```

### Team Operations (Tell Claude)
```
"Create team: content-dev-team"

"Spawn all 5 agents in parallel using spec"

"Assign Wave 1 tasks to video, visual, tech agents"

"QA agent: Run Gate 1 validation"

"Send shutdown_request to all agents"

"Delete team after shutdown"
```

### Git Workflow
```bash
git status
git add content/ docs/
git commit -m "feat: Add 23 content assets"
git push origin main
```

---

## Quality Gates

### Gate 1: Wave 1 Complete
- ✅ Markdown linting passes
- ✅ No broken links
- ✅ Scripts have hook/demo/CTA
- ✅ Screenshot specs have dimensions
- ✅ Competitive matrices have 15+ criteria

### Gate 2: Wave 2 Complete
- ✅ ROI calculator runs
- ✅ For-Executives docs readable (FK grade <10)
- ✅ Metrics have citations
- ✅ CTAs are actionable

### Gate 3: Wave 3 Complete
- ✅ Case studies use STAR format
- ✅ All metrics quantified
- ✅ Graphics specs have color/font details

### Gate 4: Final
- ✅ All 23 deliverables exist
- ✅ No TODO/FIXME text
- ✅ Brand consistency
- ✅ Git status clean

---

## Output Locations

```
content/
├── video/
│   ├── enterprisehub-final.md
│   ├── agentforge-demo-script.md
│   ├── docqa-demo-script.md
│   ├── prompt-lab-script.md
│   ├── llm-starter-script.md
│   └── RECORDING_GUIDE.md
├── visual/
│   ├── SCREENSHOT_PLAN.md
│   ├── agentforge-screenshots.md
│   ├── docqa-screenshots.md
│   ├── insight-screenshots.md
│   ├── scraper-screenshots.md
│   └── metrics-graphics-spec.md
├── business/
│   ├── roi-calculator-spec.md
│   └── roi_calculator.py
└── case-studies/
    ├── enterprisehub-case-study.md
    ├── agentforge-case-study.md
    └── docqa-case-study.md

docs/
├── FOR_PROSPECTS.md (EnterpriseHub)
└── COMPETITIVE_ANALYSIS.md (EnterpriseHub vs DIY)

ai-orchestrator/docs/
├── COMPETITIVE_MATRIX.md
└── FOR_EXECUTIVES.md

docqa-engine/docs/
├── COMPETITIVE_MATRIX.md
└── FOR_EXECUTIVES.md
```

---

## Troubleshooting Quick Fixes

**Agent stuck?**
```
"Show output for [agent-name]"
"Stop [agent-name] task"
bd update beads-xxx --assignee=different-agent
```

**QA gate fails?**
```
bd create --title="Fix: [issue]" --priority=0
bd update beads-fix --assignee=responsible-agent
"QA: Re-run Gate [N] validation"
```

**Dependency blocking?**
```
bd show beads-xxx  # Check blockedBy
bd ready  # Find unblocked work
```

**Git conflict?**
```
git status  # See conflicts
code conflicted-file  # Resolve
git add conflicted-file
git commit -m "fix: Resolve conflict"
```

---

## Success Checklist

Sprint complete when:

- [ ] 23/23 tasks closed
- [ ] Epic closed
- [ ] All files committed
- [ ] Changes pushed
- [ ] Beads synced
- [ ] Team deleted
- [ ] Agents shutdown
- [ ] Gate 4 passed (100%)
- [ ] Portfolio status updated

---

## Key Principles

1. **Let agents work autonomously** - Don't micromanage
2. **Validate at gates** - Not during execution
3. **Parallel > Sequential** - Spawn agents in single message
4. **Dependencies matter** - Set them before agents start
5. **Quality gates are mandatory** - Don't skip validation
6. **Communication is explicit** - Agents report via SendMessage
7. **Idle is normal** - Agents idle between tasks
8. **Trust the spec** - Agents have detailed prompts

---

## Expected Timeline

```
Session 1:  4 hours  → 11 tasks done
Session 2:  6 hours  → 11 tasks done
Session 3:  2 hours  → 1 task + wrap
─────────────────────────────────────
Total:     12 hours  → 23 deliverables

Sequential: 45 hours (73% time saved!)
```

---

## Post-Sprint Actions

### Week 1
- [ ] Record videos (use scripts)
- [ ] Capture screenshots (follow specs)
- [ ] Deploy ROI calculator (Streamlit Cloud)
- [ ] Update Gumroad pages (add visuals)
- [ ] Update repo READMEs (add links)

### Week 2
- [ ] Launch cold outreach (use ROI calc)
- [ ] Measure impact (GA4, Gumroad analytics)
- [ ] Iterate based on data
- [ ] Plan next sprint

---

## Links

- **Full Spec**: `.claude/specs/CONTENT_DEV_TEAM_SPEC.md`
- **Execution Runbook**: `.claude/specs/CONTENT_DEV_EXECUTION_RUNBOOK.md`
- **Portfolio Audit**: `~/.claude/teams/portfolio-dev-team/`
- **Content Inventory**: `~/.claude/reference/freelance/content-assets.md`

---

## When to Start

**Prerequisites**:
- ✅ Git status clean (or work committed)
- ✅ Beads working (`bd stats`)
- ✅ Read the spec (30 min)
- ✅ 4-hour block available (Session 1)

**Ready?** Run Session 1, Step 1.1 from the Runbook!

---

**📞 Need Help?**

1. Re-read spec section
2. Check runbook Troubleshooting
3. Review agent prompts in spec
4. Use `bd prime` for Beads help

**🚀 Good luck with your sprint!**
