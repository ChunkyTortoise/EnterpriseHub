# ADR 0013: Handoff State Isolation Across Workers

## Status

Accepted

## Context

This ADR fulfills REQ-W3-2 of the 2026-04-27 hireability spec and closes audit A item P1-4. ADR 0003 specified the Jorge handoff safeguards (0.7 confidence threshold, 30-minute circular-prevention window, 3/hour and 10/day rate limits, contact-level locking) but described locking as "Redis ensures only one handoff can execute per contact" with an in-memory fallback noted only as "single-worker only." That note understates the gap. This ADR pins where handoff state actually lives in the code at the commit it is filed against, and records the latency-vs-consistency tradeoff that gap forces.

`JorgeHandoffService` (`ghl_real_estate_ai/services/jorge/jorge_handoff_service.py`) keeps four pieces of gating state:

- `_handoff_history`: per-contact list of recent `{from, to, timestamp}` transitions, read by circular prevention and rate limiting.
- `_active_handoffs`: per-contact lock timestamp, read by the conflict guard.
- `_handoff_outcomes`: per-route outcome records that feed threshold learning.
- `_analytics`: an aggregate counter ledger for the BI dashboard.

All four are declared as class-level dicts (lines 145-158) and re-initialized as instance dicts in `__init__` (lines 191-194). Both declarations carry an explicit warning that they are "NOT safe for multi-worker deployments" (lines 133-137, 189-190).

The hot-path gate is a chain of classmethods that read and write those dicts directly:

| Check | Method | Lines | State touched |
|-------|--------|-------|---------------|
| Circular prevention | `_check_circular_prevention` | 544-594 | `_handoff_history` |
| Rate limiting | `_check_rate_limit` | 596-612 | `_handoff_history` |
| Conflict lock | `_acquire_handoff_lock` / `_release_handoff_lock` | 626-645 | `_active_handoffs` |
| History append | `_record_handoff` | 614-624 | `_handoff_history` |

A Redis-backed repository exists (`handoff_repository.py`, `RedisHandoffRepository`) and implements cluster-wide equivalents: `record_handoff_history` / `get_handoff_history` (sorted set per contact, 7-day TTL), and `acquire_lock` / `release_lock` (`SET NX EX`, 30-second TTL matching `HANDOFF_LOCK_TIMEOUT`). It is the right primitive. But `set_repository` (lines 437-441) wires the repository only into outcome persistence and the router; the synchronous gating classmethods above never call `record_handoff_history`, `get_handoff_history`, or `acquire_lock`. A grep for those method names finds zero call sites in the service or the router. So today the repository persists outcomes across restarts, while circular prevention, rate limiting, and the conflict lock still run entirely against the process-local in-memory dicts.

Deployment makes this latent rather than theoretical. The primary API (`ghl_real_estate_ai/render.yaml`) runs `uvicorn ... --workers 1`, so a single process owns all gating state and the checks are correct there. But `compliance_platform/Dockerfile.api` runs `--workers 4`, and the BI backend (`docker/production/entrypoint-bi.sh`) starts gunicorn with a configurable `$WORKERS` count. Any deployment that raises the worker count past one gives each worker its own copy of `_handoff_history` and `_active_handoffs`. Two workers handling interleaved messages for the same contact then enforce circular prevention, rate limits, and the conflict lock against two independent views.

## Decision

Document, not change. The runtime behavior stays as built; this ADR fixes the shared, accurate baseline and records the tradeoff so the next change starts from it.

**Where handoff state lives today.** Per worker process, in the class-level and instance dicts on `JorgeHandoffService`. The Redis repository persists outcomes (and can survive a restart) but does not back the hot-path gate. State is not shared across workers.

**The tradeoff this encodes.** The in-memory gate is the low-latency, low-consistency end of the spectrum.

- *In-memory dicts (current).* A circular-prevention or rate-limit check is a dict lookup plus a list scan over one contact's recent entries: sub-millisecond, no network call, no added failure mode on the message hot path. ADR 0003 budgets 10-30ms for the whole signal-checking step; the state lookups are a rounding error inside that budget. The cost is consistency. With N workers, the effective rate limit is up to N times the configured value (each worker counts only the handoffs it served), the 30-minute circular window only blocks loops that happen to land on the same worker, and the contact lock guarantees mutual exclusion only within a process. Two workers can execute conflicting handoffs for one contact concurrently.
- *Redis-backed gate (available, not wired).* Routing each gate check through `RedisHandoffRepository` makes the window, the limits, and the lock cluster-wide and correct under any worker count. `acquire_lock` already uses `SET NX EX`, the standard single-round-trip atomic lock. The cost is one Redis round-trip per check on every message that reaches handoff evaluation, plus a new dependency on Redis liveness in the hot path. The repository fails permissive on a Redis error (`acquire_lock` returns `True`, history reads return `[]`), so a Redis outage degrades back toward the in-memory consistency level rather than blocking handoffs, but it does so silently.

**Why single-worker is the current correct configuration.** Because the gate is process-local, the only configuration in which the ADR 0003 safeguards hold exactly is one worker per service instance. The primary API is already pinned there. The compliance and BI services run multiple workers; their handoff gating is best-effort, not exact, and should be read that way until the gate is moved to Redis.

**Graduation path (when multi-worker correctness is required).** Route the four gating classmethods through the repository instead of the in-memory dicts: replace the `_handoff_history` reads in `_check_circular_prevention` and `_check_rate_limit` with `get_handoff_history`, replace `_record_handoff` with `record_handoff_history`, and replace `_acquire_handoff_lock` / `_release_handoff_lock` with the repository's `acquire_lock` / `release_lock`. These methods become async, so their callers (`evaluate_handoff` and the router path around lines 968-973) must await them. The in-memory dicts then serve only as the permissive fallback when the repository is disabled. No schema or data-model change is needed; the repository contract already matches.

## Consequences

### Positive

- The handoff gate adds effectively zero latency to message evaluation at the current single-worker configuration, well inside the 10-30ms budget from ADR 0003.
- The Redis migration has a clean, contract-stable insertion point: the repository methods already exist and mirror the in-memory operations, so the graduation step is a wiring change, not a redesign.
- Writing the gap down stops future contributors from reading ADR 0003's "Redis ensures only one handoff" line as a description of current behavior and building multi-worker logic on a guarantee the hot path does not provide.
- Outcome persistence already survives restarts through the repository, so threshold learning is not lost on redeploy even though the gate is in-memory.

### Negative

- Any deployment that runs more than one worker silently weakens three safeguards at once: rate limits scale up by the worker count, the circular-prevention window only catches same-worker loops, and the contact lock no longer guarantees one handoff per contact. The compliance (`--workers 4`) and BI services are in this state now.
- The Redis repository implements history and lock methods that nothing on the hot path calls. A reader who sees the repository can reasonably assume the gate is cluster-safe; only tracing the call sites reveals it is not. This ADR is the pointer that prevents that misreading.
- The permissive fallback hides Redis failures from callers once the gate is migrated. After graduation, a Redis outage will quietly drop the gate back to per-process consistency with only a warning log, so the migration should land with an alert on `RedisHandoffRepository` health, not just the log line.
- Pinning the primary API to one worker caps its per-instance concurrency. Scaling that service means adding instances (each a single worker) until the gate is moved to Redis, rather than raising the worker count in place.
