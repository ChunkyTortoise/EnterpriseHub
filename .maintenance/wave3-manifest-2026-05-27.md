# Wave 3 Manifest, 2026-05-27

Ticket: `nafr` (parent epic) and 5 per-stream tickets created in Phase 0.

## Stream tickets

| Stream | bd ID | Scope | Parallel? |
|---|---|---|---|
| A | `moqm` | Live cache counter (`bench_cache_live.py` `--json-out` + `cache_live_2026-05-27.json` + CLAIM_LEDGER line 19) | yes (with B/C/D) |
| B | `pnxo` | ADR 0011 mesh scaffold honesty + new CLAIM_LEDGER row + README mesh claim | yes |
| C | `if4w` | `bots_stub.is_stub` + ADR 0012 + test isolation + signature-safe FE wiring | yes |
| D | `x0wj` | `snapshot_mesh_registry.py` + `mesh_registry_2026-05-27.json` | yes |
| E | `k89u` | README + HIRING_REVIEW_GUIDE sync (links all new artifacts) | sequential after A-D |

## Phase 0 work done in this commit

- Updated `docs/CLAIM_LEDGER.md` route row from "Credible but needs context" to "Strong" (473 decorators landed in commit `9753af2a`)
- Created 5 per-stream bd tickets above
- Wrote this manifest

## Close-out

When all 5 streams complete and verification passes:
```bash
bd close moqm pnxo if4w x0wj k89u
bd close nafr --reason="Wave 3 spec executed via 5-stream swarm; see .maintenance/wave3-manifest-2026-05-27.md"
bd sync
```
