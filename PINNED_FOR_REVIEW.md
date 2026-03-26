# Technical Review Guide

> For hiring managers and senior engineers: these 7 files best represent the engineering quality of this codebase.

---

## 1. Circuit Breaker — `ghl_real_estate_ai/services/circuit_breaker.py`
**Pattern:** CLOSED / OPEN / HALF_OPEN state machine with fallback dispatch
**Why it matters:** The three-state machine is the correct implementation of the Fowler circuit breaker — HALF_OPEN allows controlled recovery probes rather than full reopening, which prevents cascading failures from flapping. Unexpected exceptions are intentionally excluded from failure counting (line 157-161), which is a subtle but important correctness detail most implementations get wrong.
**Key lines:** `_should_allow_request` (112-130), `_handle_failure` half-open re-trip (207-210), `_run_function` sync/async unification (163-170)

---

## 2. Response Pipeline — `ghl_real_estate_ai/services/jorge/response_pipeline/pipeline.py`
**Pattern:** Chain of Responsibility with short-circuit and stage audit log
**Why it matters:** Each stage is isolated behind an abstract base (`base.py`) and returns an immutable-style `ProcessedResponse` rather than mutating shared state. The pipeline records a `stage_log` on every pass, which gives full traceability of which stage modified a message — invaluable for debugging compliance or TCPA edge cases in production without adding out-of-band logging calls.
**Key lines:** `process` loop with `SHORT_CIRCUIT` check (58-69), exception isolation per stage (70-76), `stage_log` append (61)

---

## 3. Response Pipeline Tests — `ghl_real_estate_ai/tests/services/test_response_pipeline.py`
**Pattern:** Parametrized unit tests per stage + integration test for full chain
**Why it matters:** Each of the 6 pipeline stages gets its own test class with both positive and negative cases. The TCPA opt-out tests parametrize 13 keyword variants including Spanish (`parar`, `cancelar`) — this level of coverage for a compliance-critical path is exactly what separates tests that find production bugs from tests that just satisfy a coverage threshold.
**Key lines:** `TestTCPAOptOutProcessor` parametrized exact-keyword tests (88-113), Spanish opt-out response assertion (143-147), `test_opt_out_compliance_flag` contact-ID assertion (163-173)

---

## 4. JWT Authentication — `ghl_real_estate_ai/api/middleware/jwt_auth.py`
**Pattern:** Fail-fast startup validation + structured security event logging
**Why it matters:** Most JWT middleware silently falls back to a weak default secret when the env var is missing. This implementation raises a `ValueError` at import time if `JWT_SECRET_KEY` is absent or shorter than 32 characters (lines 21-35), so a misconfigured deploy fails loudly rather than shipping with a weak secret. Every auth event is logged with a structured `error_id` (JWT_001 through JWT_009), which makes SIEM correlation possible without grep-based log mining.
**Key lines:** fail-fast secret validation (21-35), `jti` per-token UUID for revocation tracking (69), security-event structured logging throughout `verify_token` (183-244)

---

## 5. Handoff Service — `ghl_real_estate_ai/services/jorge/jorge_handoff_service.py`
**Pattern:** Directional confidence thresholds + circular handoff prevention + rate limiting
**Why it matters:** Different handoff routes carry different stakes: moving a contact from buyer-to-seller requires 0.8 confidence, but seller-to-buyer requires only 0.6 (lines 119-124). This asymmetric threshold design reflects real business cost rather than a single magic number. The service also enforces per-contact rate limits (3/hour, 10/day) and circular handoff detection with a 30-minute window — both are necessary to prevent infinite bot loops that would destroy CRM data quality.
**Key lines:** `THRESHOLDS` dict by route (119-124), `HOURLY_HANDOFF_LIMIT`/`DAILY_HANDOFF_LIMIT` (127-128), `EnrichedHandoffContext` dataclass context pass-through (79-94)

---

## 6. Claude Orchestrator — `ghl_real_estate_ai/services/claude_orchestrator.py`
**Pattern:** Multi-turn tool loop with specialist persona injection + L1 response cache
**Why it matters:** The orchestrator upgrades the system prompt mid-conversation based on which tool category was last invoked (lines 342-350). When the model runs a discovery tool, the next turn gets the "Market Discovery Specialist" persona injected; when it runs a strategy tool, it gets the "Negotiation Strategist." This keeps tool-use coherent across turns without requiring the caller to know anything about internal routing. The SHA-256 response cache (lines 275-294) deduplicates identical task+context combinations, reducing LLM spend on repeated analytical queries.
**Key lines:** specialist handoff prompt injection (338-350), `_make_response_cache_key` with SHA-256 hash (275-280), 5-turn orchestration loop (335-368)

---

## 7. Enterprise Security Config — `ghl_real_estate_ai/security/enterprise_security_config.py`
**Pattern:** Strategy pattern for security level + compliance matrix as first-class config
**Why it matters:** Rather than scattered `if ENVIRONMENT == "production"` checks throughout the codebase, all security posture decisions are consolidated into one `EnterpriseSecurityConfig` class that takes a `SecurityLevel` enum and adjusts every policy — JWT expiry, rate limits, CSP headers, HIPAA flags — in one place. The `validate_configuration` method (lines 383-411) returns a list of violations rather than raising, enabling CI to run a security gate check before deploy.
**Key lines:** `_apply_security_level` full policy cascade (351-381), `validate_configuration` returning issues list (383-411), `HIGH_SECURITY` activating HIPAA+PCI_DSS+SOC2 in one line (376-381)
