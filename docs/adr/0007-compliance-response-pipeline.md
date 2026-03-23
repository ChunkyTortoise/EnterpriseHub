# ADR 0007: 7-Stage Compliance Response Pipeline

## Status

Accepted

## Context

SMS-based real estate AI conversations are subject to multiple overlapping regulatory requirements:

- **TCPA (Telephone Consumer Protection Act)**: Explicit opt-out ("STOP", "UNSUBSCRIBE", etc.) must be honored immediately; further messages after opt-out create legal liability
- **FHA (Fair Housing Act) / RESPA (Real Estate Settlement Procedures Act)**: Statements about property values, financing, or demographic suitability can constitute illegal steering even when unintentional
- **SB 243 (California)**: AI-generated communications must disclose their AI origin in a visible way
- **SMS character limits**: Carriers truncate messages over 160-320 characters, causing downstream parsing failures in CRM systems

Early implementations handled these as ad-hoc checks scattered across individual bot response functions. This created gaps: FHA checking was implemented in the Seller bot but not the Lead bot; AI disclosure logic was duplicated with inconsistent formatting; TCPA opt-out detection was only a string match with no downstream tagging.

## Decision

Replace ad-hoc checks with a linear `ResponsePipeline` that all three bots pass through before any message is sent. The pipeline is defined in `services/jorge/response_pipeline/pipeline.py` and instantiated via `create_default_pipeline()` in `factory.py`.

**Pipeline stages (in execution order):**

1. **LanguageMirrorProcessor** — Detects conversation language via `LanguageDetectionService`. Sets `context.detected_language` so all downstream stages can localize their output. Spanish-language contacts receive Spanish opt-out acknowledgments and AI disclosures.

2. **TCPAOptOutProcessor** — Matches against a curated list of opt-out phrases (STOP, CANCEL, UNSUBSCRIBE, QUIT, END, NO MORE, etc.). On match: short-circuits the pipeline with an acknowledgment message, adds `TCPA-Opt-Out` and `AI-Off` tags to the GHL contact, and returns immediately without executing further stages. This guarantees no additional AI messages reach opted-out contacts.

3. **ComplianceCheckProcessor** — Passes the drafted response through `ComplianceMiddleware.enforce()`, which performs FHA/RESPA pattern matching against a curated ruleset. On `BLOCKED` status, replaces the response with a safe fallback ("I'd like to connect you with a licensed agent who can answer that question") and adds a `Compliance-Alert` tag.

4. **AIDisclosureProcessor** — Appends the SB 243 required footer (`[AI-assisted message]`) in the detected language. Applied to all non-opt-out responses. Idempotent — checks for existing disclosure before appending to prevent double-tagging.

5. **SMSTruncationProcessor** — Enforces the 320-character SMS limit (configurable via `MAX_SMS_LENGTH` env var). Truncates at sentence boundaries (`.`, `?`, `!`) rather than mid-word to preserve readability.

**Optional stage (not in default pipeline):**

6. **ConversationRepairProcessor** — Detects conversation breakdowns (unanswered questions, repeated objections, sentiment decline). Applies a graduated repair ladder: clarification → topic change → human escalation. Adds `Human-Escalation-Needed` tag when all automated strategies are exhausted.

## Consequences

### Positive
- Compliance enforcement is centralized — adding a new regulation requires one pipeline stage, not modifications to three bots
- TCPA short-circuit guarantees zero post-opt-out messages regardless of bot logic
- Language-aware output for Spanish-speaking leads without per-bot localization code
- Pipeline is testable in isolation: each stage accepts a `PipelineContext` and returns a `PipelineResult`

### Negative
- Linear pipeline order creates coupling: if `TCPAOptOutProcessor` short-circuits, `AIDisclosureProcessor` never runs (by design, but tests must verify this explicitly)
- `ComplianceMiddleware` pattern matching has false positive risk on legitimate real estate terminology (e.g., "good school district" could trigger FHA review); threshold tuning is ongoing
- Adding stages increases average response latency; pipeline overhead measured at ~15ms per conversation turn
