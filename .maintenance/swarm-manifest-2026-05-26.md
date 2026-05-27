# Swarm Manifest 2026-05-26

## Phase 0 complete
- Branch fix/credibility-drift-2026-05-19 merged to main (8 commits)
- Partially addressed 65o0: portal_api/ and ghl health.py/webhook.py done
- Partially addressed Jorge past-tense: README, CASE_STUDY, CLAIM_LEDGER updated

## Open swarm targets
| Stream | Ticket | Scope | Status |
|---|---|---|---|
| A | jut5 | .github/workflows/ CI investigation | OPEN |
| B | 65o0 | Top-10 ghl routes (auth, leads, sdr, crm, billing, analytics, compliance, webhook, jorge_advanced, reports) | OPEN |
| C | c4kd | Commented-import sweep across source files | OPEN |
| D | 62q4 | docs/DEMO_SCRIPT.md new file | OPEN |

## Skipped this cycle
- nura (content/ relocation risks breaking 16 scripts, needs sequential planning)
- Jorge past-tense stream (done in Phase 0)
- Remaining 70+ ghl routes (too large for one swarm cycle; top-10 is the hiring-reviewer path)

## Parent rules
- Parent only: git commit, bd close, bd sync, git push
- Each stream appends one JSON line to .maintenance/team-log.jsonl on completion
- No em-dashes, no AI-tell words, no marketing language in any written output
