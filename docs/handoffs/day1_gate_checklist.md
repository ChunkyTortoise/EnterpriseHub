# Day 1 Gate Checklist

Date: 2026-02-09  
Owner: A0 (Coordinator)

## Merge Gate Checklist (Per PR)

- [ ] Branch follows `codex/<agent>-<task-id>`
- [ ] PR scope is limited to assigned queue item(s)
- [ ] Unit/integration tests for touched modules pass
- [ ] `tests/test_jorge_delivery.py` passes for touched behavior
- [ ] `tests/jorge_seller/test_scope_alignment.py` passes for touched behavior
- [ ] No compliance/opt-out regression indicator
- [ ] Tenant attribution preserved for outbound paths
- [ ] Contract delta is explicit (`none` allowed)
- [ ] Risk + rollback notes included

## End-of-Day Packet Checklist (Per Agent)

- [ ] Branch and PR link
- [ ] Queue IDs covered
- [ ] What changed
- [ ] Test commands + pass/fail summary
- [ ] Blockers and Day 2 impact

## Coordinator Closeout Checklist (A0)

- [ ] Confirm Q0.1/Q0.2/Q0.3 delivered
- [ ] Confirm all agents submitted EOD packet
- [ ] Publish `day1_execution_digest.md`
- [ ] Publish Day 2 dependency map and carry-over order
