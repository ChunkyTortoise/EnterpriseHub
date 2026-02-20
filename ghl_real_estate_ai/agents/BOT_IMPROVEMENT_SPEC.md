# Jorge Bot Improvement Spec
**Authored**: 2026-02-20
**Scope**: All three bots (Seller, Buyer, Lead) + GHL integration layer
**Goal**: Fix critical bugs, activate dead features, and improve lead conversion quality
**Execution**: 4 parallel agent workstreams → integration test → deploy

---

## Workstream A — Bug Fixes (Blocker: none)
*Pure code correctness. No architecture changes. Run first.*

### A1: Fix `lead_score` NameError in billing path
**File**: `ghl_real_estate_ai/api/routes/webhook.py:1154`
**Problem**: `lead_score` variable is used in `_handle_billing_usage(contact_id, location_id, lead_score)` but is never assigned in the lead bot code path. Raises `NameError` silently on every lead bot call (background task swallows the error).
**Fix**: Derive `lead_score` from `lead_result`:
```python
lead_score = lead_result.get("lead_score", 1 if lead_temp in ("hot", "warm") else 0)
```
Insert immediately before line 1154.
**Test**: Unit test that `lead_score` is always an int before billing call; no NameError raised with any `lead_result` shape.

---

### A2: Guard against dual-bot routing collision
**Files**: `api/routes/webhook.py:999-1000`, `ghl_utils/jorge_config.py:614`
**Problem**: `LEAD_ACTIVATION_TAG` defaults to `"Needs Qualifying"` — the same tag that activates seller mode. When `JORGE_SELLER_MODE=true` is enabled (at Zoom call), both bots will race for the same contact.
**Fix**:
1. In webhook.py, add guard before lead bot block: `if jorge_seller_mode and "Needs Qualifying" in tags: skip lead bot`
2. Log a warning when both modes are active and the same activation tag is detected
3. Add comment to jorge_config.py noting that `LEAD_ACTIVATION_TAG` must differ from the seller activation tag when both modes run

**Test**: Mock contact with `["Needs Qualifying"]` tag + both modes enabled → assert only seller bot fires.

---

### A3: Fix buyer bot argument contract
**File**: `api/routes/webhook.py:831-835`
**Problem**: Webhook calls `buyer_bot.process_buyer_conversation(buyer_id=contact_id, ...)` but the method signature uses `conversation_id`. The current message `user_message` is also not passed explicitly; it only arrives via `conversation_history[-1]`, which is fragile.
**Fix**:
```python
buyer_result = await buyer_bot.process_buyer_conversation(
    conversation_id=contact_id,
    user_message=user_message,
    buyer_name=event.contact.first_name or "there",
    conversation_history=conversation_history,
)
```
**Test**: Assert `conversation_id` and `user_message` reach the bot method correctly; assert opt-out check runs on the actual message.

---

### A4: Fix SMS length default (160 → 320)
**File**: `ghl_utils/jorge_config.py:367,594`
**Problem**: `get_environment_config()` and `JorgeEnvironmentSettings` both default `MAX_SMS_LENGTH` to 160 when the env var is unset. Every other constant and the pipeline's `SMSTruncationProcessor` use 320.
**Fix**: Change both default strings from `"160"` to `"320"`:
- Line 367: `int(os.getenv("MAX_SMS_LENGTH", "320"))`
- Line 594: `int(os.getenv("MAX_SMS_LENGTH", "320"))`

**Test**: Assert `get_environment_config()["max_sms_length"] == 320` when env var is unset. Assert `JorgeEnvironmentSettings().max_sms_length == 320`.

---

## Workstream B — GHL Integration Activation (Blocker: none)
*Wire existing classified data into GHL actions. These features are already computed but never sent.*

### B1: Fire hot/warm buyer workflows from webhook
**File**: `api/routes/webhook.py` (after buyer temperature tag block, ~line 845)
**Problem**: Buyer temperature tags (`Hot-Buyer`, `Warm-Buyer`) are applied correctly but `HOT_BUYER_WORKFLOW_ID` and `WARM_BUYER_WORKFLOW_ID` are never triggered. Hot buyers get a tag and no follow-up.
**Fix**: After temperature tag logic, add:
```python
if buyer_temp == "hot" and jorge_settings.hot_buyer_workflow_id:
    actions.append(GHLAction(type=ActionType.TRIGGER_WORKFLOW,
                             workflow_id=jorge_settings.hot_buyer_workflow_id))
elif buyer_temp == "warm" and jorge_settings.warm_buyer_workflow_id:
    actions.append(GHLAction(type=ActionType.TRIGGER_WORKFLOW,
                             workflow_id=jorge_settings.warm_buyer_workflow_id))
```
**Test**: Mock `jorge_settings.hot_buyer_workflow_id = "wf-123"`, assert `TRIGGER_WORKFLOW` action in response for hot buyer.

---

### B2: Write `classify_offer_type()` result to GHL
**Files**: `services/jorge/jorge_seller_engine.py` (`_create_seller_actions()`), `ghl_utils/jorge_config.py:127-169`
**Problem**: `JorgeSellerConfig.classify_offer_type()` correctly classifies sellers as `wholesale`, `listing`, or `unknown` using property condition, motivation, and timeline signals. The result is never written to the GHL `offer_type` custom field.
**Fix**: In `_create_seller_actions()`, after extracting seller data:
```python
offer_type = JorgeSellerConfig.classify_offer_type(
    property_condition=seller_data.get("property_condition", ""),
    seller_motivation=seller_data.get("motivation", ""),
    timeline_urgency=seller_data.get("timeline_urgency", ""),
)
offer_type_field_id = JorgeSellerConfig.CUSTOM_FIELDS.get("offer_type", {}).get("id", "")
if offer_type_field_id:
    actions.append({"type": "update_custom_field",
                    "field": offer_type_field_id, "value": offer_type})
```
**Test**: Seller data with `property_condition="poor"` + `motivation="financial distress"` → assert `offer_type="wholesale"` action in response.

---

## Workstream C — Conversation Quality (Blocker: A1, A3 complete)
*Prompt improvements and question flow changes. Highest conversion impact.*

### C1: Add Rancho Cucamonga market context to seller prompt
**File**: `agents/seller/response_generator.py:177-207`
**Problem**: Seller bot prompt identifies Jorge as "a caring and knowledgeable real estate professional" with no geographic anchor. Leads get generic responses.
**Fix**: Add `MARKET_CONTEXT` block to the system prompt before the persona description:
```
MARKET CONTEXT:
- Jorge specializes exclusively in Rancho Cucamonga, CA (Inland Empire, San Bernardino County)
- Typical single-family home range: $550K–$1.2M; luxury above $1.2M
- Key neighborhoods/areas: Etiwanda, Alta Loma, Day Creek, Victoria Groves, Heritage,
  Caryn, Windrows, Old Alta Loma
- Market dynamics: strong demand, fast-moving inventory, commuter-friendly (SR-210/I-15
  access, 55-65 min to downtown LA), highly ranked schools (CVUSD)
- When relevant, reference specific neighborhoods, school names, or local landmarks to
  demonstrate market expertise
- Common seller motivations: upsizing, relocating out of state, estate sales,
  investor exits, divorce
```
Also add to the closing instruction: "If you know the property address, reference its specific neighborhood. Never give a generic 'your home might be worth X' — always qualify with local comp data."

---

### C2: Add Rancho Cucamonga market context to buyer prompt
**File**: `agents/buyer/response_generator.py:158-181`
**Problem**: Buyer prompt is even weaker — just "As Jorge's Buyer Bot, generate a helpful and supportive response." No market, no location, no persona.
**Fix**: Add same `MARKET_CONTEXT` block plus buyer-specific context:
```
BUYER CONTEXT:
- Common buyer profiles: first-time buyers (often FHA/VA), move-up buyers from
  LA/OC looking for more space, investors, and remote workers seeking Inland Empire value
- Price sensitivity: FHA loan limits ~$730K; jumbo threshold ~$766K
- Key buyer concerns: commute time, school district (CVUSD highly valued),
  HOA fees, new vs resale
- Always establish WHERE they want to live and WHY before discussing finances
- One question per message. Never ask two questions in the same response.
```

---

### C3: Add address capture to simple mode seller flow
**File**: `ghl_utils/jorge_config.py:200-205` (SIMPLE_MODE_QUESTIONS)
**Problem**: Simple mode asks 4 questions (motivation, timeline, condition, price) but never asks for the property address. Without an address, MLS lookup, psychology profiler, and CMA generation silently skip. GHL `property_address` field is never populated.
**Fix**: Prepend a 0th question to `SIMPLE_MODE_QUESTIONS`:
```python
"Q0": "Before we dive in — what's the property address? Just so I can look up the right information for your area.",
```
Update question routing logic so Q0 is asked only on `is_first_message=True` and the bot moves to Q1 (motivation) once an address is detected in the reply.
**Test**: First message to seller bot → response contains address request; second message with address → bot asks Q1.

---

### C4: Reorder buyer bot graph — location/motivation before financial assessment
**File**: `agents/jorge_buyer_bot.py:237-287` (LangGraph node order)
**Problem**: Graph runs: `analyze_buyer_intent → classify_buyer_persona → assess_financial_readiness → calculate_affordability → qualify_property_needs → match_properties`. Financial questions before property preference causes early opt-outs from FHA/VA buyers who find money discussions abrupt.
**Fix**: Reorder to: `analyze_buyer_intent → classify_buyer_persona → qualify_property_needs → assess_financial_readiness → calculate_affordability → match_properties`
This mirrors how a skilled buyer's agent works: understand what they want first, then qualify them financially.
**Test**: Run buyer graph from fresh state → assert first substantive question is about location/property preference, not budget or pre-approval.

---

## Workstream D — Nurture Sequence Activation (Blocker: A1, A2 complete)
*Activate the existing 3/7/14/30-day follow-up system that is currently dead.*

### D1: Read sequence_day from conversation context
**File**: `api/routes/webhook.py:1024-1029`
**Problem**: `sequence_day=0` is hardcoded on every webhook call. The lead bot has a full 3/7/14/30-day follow-up graph but it is never reached because the webhook always starts at day 0.
**Fix**:
1. Before calling `process_enhanced_lead_sequence`, load the contact's conversation context
2. Read `sequence_day = context.get("lead_sequence_day", 0)`
3. Read `first_contact_at = context.get("first_contact_at")` — set on first interaction
4. If `first_contact_at` is set, compute `sequence_day` from elapsed calendar days
5. Update `lead_sequence_day` in context after each interaction

```python
ctx = await conversation_manager.get_context(contact_id, location_id)
first_contact = ctx.get("first_contact_at")
if not first_contact:
    ctx["first_contact_at"] = datetime.utcnow().isoformat()
    sequence_day = 0
else:
    delta = datetime.utcnow() - datetime.fromisoformat(first_contact)
    sequence_day = delta.days
await conversation_manager.memory_service.save_context(contact_id, ctx, location_id=location_id)

lead_result = await lead_bot.process_enhanced_lead_sequence(
    lead_id=contact_id,
    sequence_day=sequence_day,
    conversation_history=conversation_history,
)
```
**Test**: Mock context with `first_contact_at` 7 days ago → assert `sequence_day=7` passed to lead bot.

---

## Integration & Validation (Blocker: all workstreams complete)

### E1: Run full test suite
- `pytest ghl_real_estate_ai/tests/ -v --tb=short`
- All existing 88 tests must still pass
- New tests added in A1–D1 must pass

### E2: Live smoke test
- Send test message to seller bot (tag: "Needs Qualifying") → verify address question fires
- Send test message to buyer bot (tag: "Buyer-Lead") → verify location question fires before finance
- Send lead bot message → verify sequence_day is logged correctly
- Verify GHL actions array contains workflow triggers for hot contacts

### E3: Deploy to Railway
- Push to GitHub → Railway auto-deploys
- Update GHL webhook URL in "Jorge AI Bot - Inbound Message Handler" workflow to Railway URL
- Confirm health endpoint returns `{"status":"healthy"}`

---

## Agent Assignment

| Workstream | Agent | Tasks | Est. |
|---|---|---|---|
| A: Bug Fixes | `general-purpose` | A1, A2, A3, A4 | 30 min |
| B: GHL Integration | `general-purpose` | B1, B2 | 20 min |
| C: Conversation Quality | `general-purpose` | C1, C2, C3, C4 | 45 min |
| D: Nurture Sequence | `general-purpose` | D1 | 20 min |
| E: Integration/Validate | `general-purpose` | E1, E2, E3 | 20 min |

**A + B + C + D run in parallel. E blocks on all four.**

---

## Files Modified (summary)

| File | Workstreams |
|------|------------|
| `api/routes/webhook.py` | A1, A2, A3, B1, D1 |
| `ghl_utils/jorge_config.py` | A2, A4 |
| `services/jorge/jorge_seller_engine.py` | B2 |
| `agents/seller/response_generator.py` | C1 |
| `agents/buyer/response_generator.py` | C2 |
| `agents/jorge_buyer_bot.py` | C4 |
| `core/conversation_manager.py` | D1 (context read/write) |

---

## Success Criteria

- [ ] Zero NameErrors in lead bot billing path
- [ ] Seller + lead bot never fire simultaneously for same contact
- [ ] Buyer bot receives correct `conversation_id` and `user_message`
- [ ] All SMS defaults are 320 chars
- [ ] Seller bot references Rancho Cucamonga neighborhoods in responses
- [ ] Buyer bot asks location/preference before financial questions
- [ ] Address is captured in simple mode before Q1
- [ ] `offer_type` written to GHL after seller qualification
- [ ] Hot/warm buyer workflows fire when thresholds met
- [ ] Lead sequence_day advances correctly across days
- [ ] All 88+ tests pass
