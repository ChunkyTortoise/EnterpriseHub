# Jorge Bot Finalization Spec

**Date**: 2026-02-14
**Status**: Ready for execution
**Scope**: Complete all three Jorge bots to production-ready state aligned with original client spec

---

## Current State Summary

| Metric | Value |
|--------|-------|
| Total bot files | 60+ across agents/, services/jorge/ |
| Tests | 21 passing, 4 failing |
| Seller bot | 1813 lines + 12 sub-modules |
| Buyer bot | 948 lines + 11 sub-modules |
| Lead bot | 2750+ lines + 12 sub-modules |
| Jorge services | 28 service modules |
| Intent decoders | 3 (Lead, Seller, Buyer) |

### Tone Decision
**Friendly/consultative is CORRECT.** The "almost confrontational" language in the original Upwork spec was aspirational. The current `FRIENDLY_APPROACH=True` default is what Jorge actually wants. The `JorgeToneEngine` confrontational templates should be deprecated in favor of the existing warm, professional tone.

---

## Work Packages (7 total)

### WP1: Fix 4 Failing Tests
**Priority**: P0 (blocking)
**Agent**: test-engineering
**Estimated effort**: Small

4 tests are currently failing:

1. `test_jorge_seller_bot.py::test_jorge_seller_bot_stall_breaking`
2. `test_jorge_seller_bot.py::test_jorge_seller_bot_educational_mode`
3. `test_jorge_buyer_bot.py::test_jorge_buyer_bot_qualification_flow`
4. `test_jorge_buyer_bot.py::test_jorge_buyer_bot_low_qualification`

**Tasks**:
- Read each failing test and the code it exercises
- Identify root cause (likely method signature drift or mock mismatches after refactoring)
- Fix tests to match current implementation
- Verify all 25 Jorge tests pass

**Acceptance**: `pytest ghl_real_estate_ai/tests/ -k "jorge" --tb=short` = 25/25 passing

---

### WP2: Deprecate Confrontational Tone, Consolidate Friendly Mode
**Priority**: P1
**Agent**: general-purpose
**Estimated effort**: Medium

The `JorgeToneEngine` in `services/jorge/jorge_tone_engine.py` has confrontational templates (take-away close, net yield justification, arbitrage pitch, Chris Voss patterns) that conflict with the friendly approach. These need to be cleanly deprecated without breaking existing imports.

**Tasks**:
- In `jorge_tone_engine.py`: Mark confrontational methods as deprecated (add `warnings.warn` + docstring note). Do NOT delete them yet — other code may import them
- Verify `JorgeSellerConfig.FRIENDLY_APPROACH = True` and `USE_WARM_LANGUAGE = True` remain the defaults (they are — just confirm no env override paths flip them)
- In `seller/strategy_selector.py`: Confirm strategy selection uses CONSULTATIVE/EDUCATIONAL/ENTHUSIASTIC/UNDERSTANDING (friendly strategies) as primary paths
- In `seller/stall_detector.py`: Confirm `FRIENDLY_RESPONSES` are the ones used in the active flow
- In `seller/objection_handler.py`: Review objection handling tone — ensure graduated responses stay professional/helpful, not aggressive
- In `seller/response_generator.py`: Confirm response generation uses warm language patterns
- Run `grep -r "confrontational\|take_away_close\|arbitrage_pitch\|net_yield_justification" --include="*.py"` to find all references and ensure none are in hot paths
- Add a `TONE_DEPRECATION.md` note in services/jorge/ explaining the decision

**Acceptance**: No confrontational language in any active code path. All friendly defaults confirmed. Deprecation warnings on old methods.

---

### WP3: GHL Field ID and Workflow ID Configuration
**Priority**: P1
**Agent**: ghl-integration-specialist
**Estimated effort**: Medium

All 18 custom field IDs in `JorgeSellerConfig.CUSTOM_FIELDS` are empty strings `""`. All 3 workflow IDs are empty. The bot generates qualification data but can't write it to GHL.

**Tasks**:
- In `jorge_config.py`: Document that each field maps to env var `CUSTOM_FIELD_{FIELD_NAME_UPPER}` (this pattern already exists in `get_ghl_custom_field_id`)
- Create `ghl_real_estate_ai/ghl_utils/jorge_ghl_setup.py` — a setup/validation script that:
  - Lists all required GHL custom fields with their expected types (dropdown, text, number, currency, boolean, datetime)
  - Lists all required GHL workflow IDs
  - Validates that env vars are set and non-empty
  - Outputs a clear report of what's configured vs missing
  - Can be run as `python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup` to check deployment readiness
- In `EnhancedGHLClient`: Verify that `update_contact()` handles the case where field IDs are empty strings (should log warning, not crash)
- In `GHLWorkflowService`: Verify that empty workflow IDs are handled gracefully (skip trigger, log warning)
- Add env var template to `.env.example` with all CUSTOM_FIELD_* and WORKFLOW_ID vars documented
- Write tests for the setup validation script

**Acceptance**: `python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup` runs and reports field status. Empty IDs don't crash bots. `.env.example` has complete template.

---

### WP4: Calendar Booking for HOT Sellers
**Priority**: P1
**Agent**: general-purpose
**Estimated effort**: Medium

HOT sellers currently get a handoff message asking "morning or afternoon?" but no actual GHL calendar appointment is created. The original spec requires autonomous booking.

**Tasks**:
- In `EnhancedGHLClient` (or new method): Add `create_appointment()` method that calls GHL Calendar API:
  - Endpoint: `POST /calendars/{calendarId}/appointments` (GHL v2 API)
  - Params: `contactId`, `startTime`, `endTime`, `title`, `calendarId`
  - Calendar ID sourced from env var `JORGE_CALENDAR_ID`
- In `EnhancedGHLClient`: Add `get_free_slots()` method:
  - Endpoint: `GET /calendars/{calendarId}/free-slots`
  - Returns next 3 available 30-min slots within business hours (9am-5pm PT)
- In the seller bot's hot seller handoff flow (`jorge_seller_bot.py` or `seller/handoff_manager.py`):
  - After classification as HOT: call `get_free_slots()` to get available times
  - Present slots in the handoff message: "Great news! I have these times available for a quick call: [slot1], [slot2], [slot3]. Which works best?"
  - When seller responds with a slot choice: call `create_appointment()` to book it
  - Send SMS + email confirmation (via GHL workflow trigger or direct API)
- Handle edge cases:
  - No available slots: "Our team is booked solid right now. Someone will reach out within 24 hours to schedule."
  - Calendar ID not configured: Log warning, fall back to current "morning or afternoon?" behavior
  - API failure: Log error, fall back to manual scheduling
- Write tests with mocked GHL API responses

**Acceptance**: HOT sellers get real appointment offers. Appointments appear in Jorge's GHL calendar. Graceful fallback when calendar not configured.

---

### WP5: End-to-End Conversation Flow Tests
**Priority**: P1
**Agent**: test-engineering
**Estimated effort**: Large
**Blocked by**: WP1

The bots need integration tests that simulate full conversations from first contact to qualification complete. Currently tests are mostly unit-level.

**Tasks**:
- Create `tests/integration/test_jorge_seller_e2e.py`:
  - **Happy path (HOT)**: 4-question simple flow → all answered well → HOT classification → handoff message → GHL fields populated
  - **Warm path**: 3 of 4 questions answered → WARM classification → nurture sequence triggered
  - **Cold path**: 1-2 questions answered, vague responses → COLD classification → long-term drip
  - **Opt-out**: Seller says "stop" or "not interested" at any point → TCPA opt-out → "Do Not Contact" tag
  - **Stall/abandon**: Seller stops responding → stall detection → follow-up sequence triggered
  - **Handoff from lead bot**: Lead bot detects seller intent → handoff context passed → seller bot skips re-qualification of known data
- Create `tests/integration/test_jorge_buyer_e2e.py`:
  - **Qualified buyer**: Financial readiness + urgency + preferences → HOT buyer → property matching → scheduling
  - **Window shopper**: Low urgency, vague budget → COLD → educational content
  - **Handoff from lead bot**: Lead bot detects buyer intent → handoff to buyer bot with context
- Create `tests/integration/test_jorge_lead_e2e.py`:
  - **New lead**: Initial contact → temperature assessment → routing to seller or buyer bot
  - **Ambiguous lead**: Mentions both buying and selling → correct routing decision
  - **Re-engagement**: Cold lead responds after 30 days → re-qualification
- Create `tests/integration/test_jorge_handoff_e2e.py`:
  - **Lead → Seller**: Full handoff flow with context preservation
  - **Lead → Buyer**: Full handoff flow with context preservation
  - **Seller → Buyer**: Cross-qualification handoff (seller also wants to buy)
  - **Circular prevention**: Seller → Buyer → Seller blocked within 30min window
  - **Rate limiting**: 4th handoff in 1 hour blocked

All tests should use mocked GHL client and Claude API. No real API calls.

**Acceptance**: All e2e tests pass. Cover happy path, edge cases, and error scenarios for each bot and handoff direction.

---

### WP6: Response Pipeline Validation
**Priority**: P2
**Agent**: general-purpose
**Estimated effort**: Medium

The response pipeline (`services/jorge/response_pipeline/`) has 6 stages that process every bot response before delivery. Need to verify each stage works correctly with the friendly tone.

**Tasks**:
- **TCPA Opt-Out** (`tcpa_opt_out.py`): Verify opt-out keywords are comprehensive ("stop", "unsubscribe", "opt out", "do not contact", "remove me"). Confirm it applies "Do Not Contact" tag and halts conversation.
- **Compliance Check** (`compliance_check.py`): Verify DRE, Fair Housing, CCPA compliance checks. Ensure no discriminatory language patterns in bot responses.
- **AI Disclosure** (`ai_disclosure.py`): Verify AI disclosure is included per California requirements. Should appear in first message of conversation only (not every message).
- **SMS Truncation** (`sms_truncation.py`): Verify 160-char limit with tail-preserving truncation (keeps CTA/question at end). Test with messages that are 159, 160, 161, 200, 320 chars.
- **Conversation Repair** (`conversation_repair.py`): Verify repair logic for garbled/unclear messages. Should ask for clarification in friendly tone.
- **Language Mirror** (`language_mirror.py`): Verify language detection and mirroring. If seller writes in Spanish, bot should acknowledge and continue in English (or Spanish if configured).
- Write unit tests for each pipeline stage
- Write integration test that runs a message through all 6 stages in order

**Acceptance**: Each pipeline stage has dedicated tests. Full pipeline integration test passes. TCPA compliance verified. SMS truncation handles edge cases.

---

### WP7: Documentation and Deployment Readiness
**Priority**: P2
**Agent**: general-purpose
**Estimated effort**: Small
**Blocked by**: WP1, WP2, WP3

**Tasks**:
- Update `CLAUDE.md` Bot Public APIs section to reflect final state
- Create `ghl_real_estate_ai/agents/DEPLOYMENT_CHECKLIST.md`:
  - Pre-deployment: env vars, GHL field IDs, workflow IDs, calendar ID
  - Smoke test: send test message through each bot, verify GHL field updates
  - Monitoring: alerting rules, performance thresholds, KPI dashboards
  - Rollback: how to disable bots (deactivation tags)
- Verify all `__init__.py` exports are clean
- Run full test suite and confirm pass rate
- Update `.env.example` with all Jorge-specific env vars

**Acceptance**: Deployment checklist complete. All env vars documented. Test suite green.

---

## Execution Order

```
WP1 (Fix Tests) ─────────────────┐
                                  ├──► WP5 (E2E Tests)
WP2 (Tone Consolidation) ────────┤
                                  ├──► WP7 (Docs/Deploy)
WP3 (GHL Field IDs) ─────────────┘

WP4 (Calendar Booking) ──────────────► (independent)

WP6 (Response Pipeline) ─────────────► (independent)
```

**Parallel tracks**:
- Track A: WP1 → WP5 → WP7
- Track B: WP2 (parallel with WP1)
- Track C: WP3 (parallel with WP1)
- Track D: WP4 (independent)
- Track E: WP6 (independent)

**Agents needed**: 5 concurrent (one per track), coordinated by team lead

---

## Out of Scope (Confirmed)

These items exist in the codebase but are NOT required for Jorge's delivery:

- Voice/phone call integration (RetellClient, LyrioClient)
- Document upload/processing
- MLS/property data API integration (CMA uses manual/mock data)
- Multi-language support (English only for now)
- Photo/media handling
- Automated seller net sheet calculator
- Progressive skills manager (enterprise feature)
- Agent mesh coordination (enterprise feature)
- MCP protocol integration (enterprise feature)
- Healthcare/industry verticals

---

## Success Criteria

| Criterion | Target |
|-----------|--------|
| All Jorge tests passing | 25/25 + new e2e tests |
| Seller bot 4-question flow | Complete, friendly tone |
| Buyer bot qualification | Complete, friendly tone |
| Lead bot routing | Correct buyer/seller detection |
| Handoff between all 3 bots | Working with context preservation |
| GHL field population | Env-var configured, graceful fallback |
| Calendar booking (HOT) | API integration or graceful fallback |
| TCPA/compliance | Opt-out, AI disclosure, Fair Housing |
| SMS compliance | 160 char, no hyphens, no emojis |
| Response pipeline | All 6 stages verified |
| Deployment docs | Complete checklist |
