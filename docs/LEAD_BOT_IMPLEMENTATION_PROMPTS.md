# Lead Bot Implementation Prompts

Copy these prompts into a new Claude Code chat to implement the Lead Bot enhancements.

## Phase 1: Lead Bot Routing & Compliance

**File**: `ghl_real_estate_ai/api/routes/webhook.py` (lines 829-843)

**Prompt**:
```markdown
## Phase 1: Implement Lead Bot Routing & Compliance Enhancement

### Context
The Lead Bot section in `ghl_real_estate_ai/api/routes/webhook.py` (lines 829-843) is incomplete. It only checks for activation but has no processing logic, falling through to generic processing. The Seller and Buyer bots have full implementations that need to be replicated for the Lead Bot.

### Current Lead Bot Code (lines 829-843)
```python
# Step -0.3: Check for Jorge's Lead Mode (LEAD_ACTIVATION_TAG + JORGE_LEAD_MODE)
jorge_lead_mode = (
    jorge_settings.LEAD_ACTIVATION_TAG in tags and
    jorge_settings.JORGE_LEAD_MODE and
    not should_deactivate
)

if not jorge_lead_mode:
    # Raw fallback — no bot mode matched
    logger.info(f"No bot mode matched for contact {contact_id}")
    return GHLWebhookResponse(
        success=True,
        message="Thanks for reaching out! How can I help you today?",
        actions=[],
    )
```

### Required Changes
Replace lines 829-843 with a complete Lead Bot implementation that includes:

#### 1. Lead Bot Engine Call
- Initialize `LeadBotWorkflow` (similar to `JorgeSellerBot` / `JorgeBuyerBot`)
- Call `lead_bot.process_lead_conversation()` method
- Extract: `lead_result.get("response")`, `lead_result.get("lead_temperature")`, `lead_result.get("handoff_signals")`, `lead_result.get("is_qualified")`

#### 2. Temperature Tag Publishing
- Map `lead_temperature` to tags: "Hot-Lead", "Warm-Lead", "Cold-Lead"
- Add "Lead-Qualified" tag if `is_qualified` is True

#### 3. SMS Length Guard (320 char limit)
- Truncate message at sentence boundaries (". ", "! ", "? ") when exceeding 320 characters

#### 4. Compliance Guard Integration
- Call `compliance_guard.audit_message()` with mode="lead"
- Handle BLOCKED status with fallback message and "Compliance-Alert" tag

#### 5. Handoff Signals Integration
- If `handoff_signals` exist, call `handoff_service.evaluate_handoff()` with current_bot="lead"
- Execute handoff actions (add tags, owner assignment)

#### 6. Structured Logging
- Log: contact_id, lead_temperature, is_qualified, handoff_triggered, actions_count, compliance_status, message_length

#### 7. Safe Message/Actions Send
- Use `background_tasks.add_task()` with `safe_send_message()` and `safe_apply_actions()` wrappers (same pattern as Seller/Buyer bots)

#### 8. Error Handling
- Catch exceptions, add "Bot-Fallback-Active" tag, return generic fallback message

### Reference Files
- Seller Bot: lines 512-672 in webhook.py
- Buyer Bot: lines 674-827 in webhook.py
- Handoff Service: `ghl_real_estate_ai/services/jorge/jorge_handoff_service.py`
- Compliance Guard: Already imported and used in Seller/Buyer bots

### Scope
- Only modify `ghl_real_estate_ai/api/routes/webhook.py` lines 829-843
- Do NOT modify any other files
- Do NOT create tests (tests are Phase 2-5)
```

---

## Phase 2: Config Validation Tests

**File**: `ghl_real_estate_ai/ghl_utils/jorge_config.py`

**Prompt**:
```markdown
## Phase 2: Create Config Validation Tests (7 Tests)

### Context
The `jorge_config.py` file (`ghl_real_estate_ai/ghl_utils/jorge_config.py`) has a `validate_ghl_integration()` method that needs comprehensive test coverage. These tests verify configuration validation, environment variable overrides, and fallback behavior.

### Test File Location
Create: `ghl_real_estate_ai/tests/test_jorge_config_validation.py`

### Required Tests (7 total)

#### Test 1: test_validate_ghl_integration_empty_workflow_ids_warns
- Call `validate_ghl_integration()` with empty workflow IDs
- Verify warning log is emitted
- Verify it returns (True, []) with warnings in message

#### Test 2: test_validate_ghl_integration_empty_custom_field_ids_warns
- Call with empty custom field IDs
- Verify warning about missing field IDs
- Verify graceful fallback behavior

#### Test 3: test_validate_ghl_integration_missing_env_vars_warns
- Call with missing environment variables
- Verify warnings for JORGE_SELLER_MODE, JORGE_BUYER_MODE, JORGE_LEAD_MODE

#### Test 4: test_validate_ghl_integration_valid_config_returns_clean
- Call with all required settings populated
- Verify returns (True, []) with no warnings

#### Test 5: test_workflow_id_fallback_behavior
- Test that empty workflow IDs don't cause crashes
- Verify fallback to empty strings works

#### Test 6: test_custom_field_id_fallback_behavior
- Test that empty custom field IDs don't cause crashes
- Verify fallback values are used correctly

#### Test 7: test_env_var_override_behavior
- Test environment variable overrides are applied correctly
- Verify settings are loaded from environment when present

### Reference Files
- Config file: `ghl_real_estate_ai/ghl_utils/jorge_config.py`
- Existing tests: `ghl_real_estate_ai/tests/` directory
- pytest patterns from `advanced_rag_system/tests/core/`

### Scope
- Only create the test file `ghl_real_estate_ai/tests/test_jorge_config_validation.py`
- Do NOT modify jorge_config.py
- Follow existing test patterns in the project
```

---

## Phase 3: Lead Bot Handoff Tests

**File**: `ghl_real_estate_ai/services/jorge/jorge_handoff_service.py`

**Prompt**:
```markdown
## Phase 3: Create Lead Bot Handoff Tests (6 Tests)

### Context
The handoff service (`ghl_real_estate_ai/services/jorge/jorge_handoff_service.py`) is fully implemented and needs tests to verify lead-to-buyer and lead-to-seller handoff scenarios. These tests complement the existing 16 handoff service tests.

### Test File Location
Create: `ghl_real_estate_ai/tests/test_lead_bot_handoff.py`

### Required Tests (6 total)

#### Test 1: test_lead_to_buyer_handoff_high_confidence
- Create a lead with high buying intent signals
- Trigger handoff from lead to buyer bot
- Verify handoff is recommended (confidence > 0.7)
- Verify buyer tags are added

#### Test 2: test_lead_to_seller_handoff_listing_signals
- Create a lead with seller intent signals (wants to sell property)
- Trigger handoff from lead to seller bot
- Verify handoff is recommended
- Verify seller tags are added

#### Test 3: test_lead_handoff_confidence_thresholds
- Test confidence threshold behavior (0.7 for handoff)
- Verify low confidence (<0.7) doesn't trigger handoff
- Verify high confidence (>=0.7) triggers handoff

#### Test 4: test_lead_handoff_tag_swapping
- Test that lead tags are removed during handoff
- Verify new bot-specific tags are added
- Verify tag swapping logic works correctly

#### Test 5: test_lead_handoff_tracking_and_analytics
- Verify analytics are recorded for handoff events
- Verify lead_to_buyer and lead_to_seller counters increment
- Verify handoff duration is tracked

#### Test 6: test_lead_handoff_with_conversation_context
- Test handoff with full conversation history
- Verify intent signals are extracted from context
- Verify handoff decision uses context properly

### Reference Files
- Handoff Service: `ghl_real_estate_ai/services/jorge/jorge_handoff_service.py`
- Existing handoff tests: Check `ghl_real_estate_ai/tests/` for existing test patterns
- Lead Bot: `ghl_real_estate_ai/agents/lead_bot.py`

### Scope
- Only create the test file `ghl_real_estate_ai/tests/test_lead_bot_handoff.py`
- Do NOT modify the handoff service or lead bot
- Follow existing test patterns in the project
```

---

## Phase 4: Documentation Updates

**Files**: `CLAUDE.md`, `docs/JORGE_FINALIZATION_SPEC.md`

**Prompt**:
```markdown
## Phase 4: Documentation Updates (3 Tasks)

### Context
The Lead Bot routing enhancements have been implemented. Documentation needs to be updated to reflect:
1. New Lead Bot features and integration patterns
2. Updated architecture documentation
3. A new integration guide for the Lead Bot

### Task 1: Update CLAUDE.md
Location: `CLAUDE.md`

Add/update the following sections:
- Lead Bot status: COMPLETE (was PARTIAL)
- Temperature tag publishing (Hot-Lead/Warm-Lead/Cold-Lead)
- Lead bot handoff integration (0.7 confidence threshold)
- Compliance guard for lead mode

### Task 2: Update JORGE_FINALIZATION_SPEC.md
Location: Check for existing file in `docs/` or project root

Add:
- Lead Bot routing implementation details
- Updated feature matrix showing Lead Bot now has same features as Seller/Buyer
- Handoff integration documentation
- Configuration validation section

### Task 3: Create LEAD_BOT_INTEGRATION_GUIDE.md
Location: Create at `docs/LEAD_BOT_INTEGRATION_GUIDE.md`

Content should include:
1. Overview of Lead Bot capabilities
2. Temperature tag system (Hot/Warm/Cold)
3. Compliance requirements for lead mode
4. Handoff triggers and thresholds (0.7 confidence)
5. Integration with CRM workflows
6. Configuration reference
7. Troubleshooting guide
8. Test coverage summary

### Reference Files
- Implementation summary: `plans/jorge_bots_implementation_summary.md`
- Handoff service: `ghl_real_estate_ai/services/jorge/jorge_handoff_service.py`
- Webhook routes: `ghl_real_estate_ai/api/routes/webhook.py`
- Existing documentation in `docs/` and project root

### Scope
- Modify: `CLAUDE.md`
- Modify: `JORGE_FINALIZATION_SPEC.md` (if exists)
- Create: `docs/LEAD_BOT_INTEGRATION_GUIDE.md`
```

---

## Phase 5: Integration Tests

**File**: `ghl_real_estate_ai/tests/test_lead_bot_integration.py`

**Prompt**:
```markdown
## Phase 5: Create Integration Tests (4 Tests)

### Context
The Lead Bot implementation is complete. Integration tests are needed to verify end-to-end functionality with compliance, handoff scenarios, multi-bot cascade, and performance validation.

### Test File Location
Create: `ghl_real_estate_ai/tests/test_lead_bot_integration.py`

### Required Tests (4 total)

#### Test 1: test_lead_bot_e2e_with_compliance
- Simulate full webhook request with Lead Mode activation
- Process lead conversation through LeadBotWorkflow
- Verify compliance guard intercepts if needed
- Verify temperature tags are published
- Verify SMS is truncated to 320 chars if needed
- Verify final response is returned correctly

#### Test 2: test_lead_bot_handoff_scenarios
- Test lead→buyer handoff with buying intent
- Test lead→seller handoff with selling intent
- Verify handoff triggers at 0.7 confidence threshold
- Verify tags are swapped correctly
- Verify handoff analytics are recorded

#### Test 3: test_multi_bot_handoff_cascade
- Test cascade scenario: Lead → Buyer (then to Seller if intent changes)
- Verify smooth transition between bot modes
- Verify conversation context is preserved
- Verify tags accumulate correctly

#### Test 4: test_lead_bot_performance_validation
- Test latency (<42ms P95 target)
- Test cache hit rate (>80% target)
- Test bot success rate (>95% target)
- Use mocked services to avoid external dependencies
- Verify performance metrics are within thresholds

### Reference Files
- Webhook routes: `ghl_real_estate_ai/api/routes/webhook.py`
- Lead Bot: `ghl_real_estate_ai/agents/lead_bot.py`
- Handoff Service: `ghl_real_estate_ai/services/jorge/jorge_handoff_service.py`
- Compliance Guard: `ghl_real_estate_ai/services/compliance_guard.py`
- Performance targets: `plans/jorge_bots_implementation_summary.md`

### Scope
- Only create the test file `ghl_real_estate_ai/tests/test_lead_bot_integration.py`
- Use mocking for external services (GHL API, Claude AI, etc.)
- Follow existing test patterns in `ghl_real_estate_ai/tests/`
```

---

## Summary

| Phase | File Modified/Created | Tests | Status |
|-------|---------------------|-------|--------|
| 1 | `webhook.py` (lines 829-1005) | - | ✅ COMPLETE |
| 2 | `test_jorge_config_validation.py` | 14 | ✅ COMPLETE |
| 3 | `test_lead_bot_handoff.py` | 13 | ✅ COMPLETE |
| 4 | CLAUDE.md, docs/, LEAD_BOT_INTEGRATION_GUIDE.md | - | ✅ COMPLETE |
| 5 | `test_lead_bot_integration.py` | 17 | ✅ COMPLETE |
| **Total** | **7 files** | **197 tests** | |
