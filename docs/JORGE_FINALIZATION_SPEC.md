# Jorge Bot Finalization Spec

**Version**: 1.1
**Branch**: `feature/advanced-rag-benchmarks`
**Status**: 142 bot tests passing (Lead: 23, Buyer: 50, Seller: 64, Handoff: 16)
**Date**: 2026-02-06

---

## Table of Contents

1. [Current Architecture](#1-current-architecture)
2. [Phase 1: Lead Bot Routing & Compliance](#2-phase-1-lead-bot-routing--compliance)
3. [Phase 2: Configurable GHL IDs](#3-phase-2-configurable-ghl-ids)
4. [Phase 3: Cross-Bot Handoff](#4-phase-3-cross-bot-handoff)
5. [Phase 4: Real MLS Data Integration](#5-phase-4-real-mls-data-integration)
6. [Phase 5: Integration Tests & Load Testing](#6-phase-5-integration-tests--load-testing)
7. [Test Patterns Reference](#7-test-patterns-reference)
8. [File Reference Index](#8-file-reference-index)
9. [Acceptance Criteria](#9-acceptance-criteria)

---

## 1. Current Architecture

### 1.1 Webhook Routing Flow

```
Incoming GHL Webhook (POST /ghl/webhook)
    |
    +-- Loopback check: outbound messages ignored
    +-- Activation tag check (lines 133-178)
    |     activation_tags from settings + buyer tag
    |     deactivation_tags: ["AI-Off", "Qualified", "Stop-Bot", "AI-Qualified"]
    |
    +-- Opt-out detection (lines 180-201)
    |     OPT_OUT_PHRASES: "stop", "unsubscribe", "not interested", etc.
    |     Action: add "AI-Off" tag, send confirmation
    |
    +-- SELLER ROUTING (lines 203-335)
    |     Condition: "Needs Qualifying" in tags AND JORGE_SELLER_MODE=true
    |     Bot: JorgeSellerEngine.process_seller_response()
    |     Tags: Hot-Seller, Warm-Seller, Cold-Seller
    |     Compliance: audit_message() with seller fallback
    |     Workflows: hot_seller_workflow, warm_seller_workflow
    |
    +-- BUYER ROUTING (lines 336-461)
    |     Condition: BUYER_ACTIVATION_TAG in tags AND JORGE_BUYER_MODE=true
    |     Bot: JorgeBuyerBot.process_buyer_conversation()
    |     Tags: Hot-Buyer, Warm-Buyer, Cold-Buyer, Buyer-Qualified
    |     Compliance: audit_message() with buyer fallback
    |
    +-- LEAD ROUTING (lines 462-650) **[NEW - COMPLETE]**
    |     Condition: LEAD_ACTIVATION_TAG in tags AND JORGE_LEAD_MODE=true
    |     Bot: ConversationManager.generate_response()
    |     Tags: Hot-Lead, Warm-Lead, Cold-Lead
    |     Compliance: audit_message() with lead fallback
    |     SMS Length Guard: 320-char truncation with smart boundaries
    |     Handoff: Evaluate lead→buyer/seller at 0.7 confidence
    |
    +-- DEFAULT FALLBACK (no mode matched)
          Route: Minimal response, no AI processing
```

### 1.2 Bot Entry Points

| Bot | Class | Entry Method | Return Keys |
|-----|-------|-------------|-------------|
| Lead | `ConversationManager` | `generate_response()` via webhook fallback | `message`, `actions` (via `prepare_ghl_actions`) |
| Buyer | `JorgeBuyerBot` | `process_buyer_conversation(buyer_id, buyer_name, conversation_history)` | `buyer_temperature`, `is_qualified`, `response_content`, `matched_properties`, `financial_readiness_score`, `buying_motivation_score` |
| Seller | `JorgeSellerEngine` | `process_seller_response(contact_id, user_message, location_id, tenant_config, images)` | `message`, `actions`, `temperature`, `seller_data`, `questions_answered`, `analytics`, `pricing` |

### 1.3 Configuration Architecture

```
jorge_config.py
    +-- JorgeSellerConfig (dataclass, lines 17-335)
    |     Static config: tags, thresholds, workflows, custom fields, questions
    |     Helper methods: get_workflow_id(), get_ghl_custom_field_id()
    |
    +-- JorgeEnvironmentSettings (class, lines 337-412)
    |     Runtime config loaded from env vars
    |     Properties: JORGE_SELLER_MODE, JORGE_BUYER_MODE, BUYER_ACTIVATION_TAG
    |     List parsing: _parse_list_env() (JSON or CSV)
    |
    +-- JorgeMarketManager (class, lines 414-473)
    |     Market-specific config (Rancho Cucamonga)
    |
    +-- Module exports (lines 475-499)
          settings = JorgeEnvironmentSettings()
          Exported: JORGE_SELLER_MODE, ACTIVATION_TAGS, DEACTIVATION_TAGS
```

### 1.4 Compliance Guard

3-tier architecture in `services/compliance_guard.py`:

- **Tier 0**: Input length guard (>10,000 chars blocked)
- **Tier 1**: Regex pattern matching against protected keywords (race, religion, familial status, etc.)
- **Tier 2**: LLM cognitive audit via Claude Haiku (steering, discrimination, redlining, tone)

Returns: `(ComplianceStatus, reason, violations)` where status is `PASSED`, `FLAGGED`, or `BLOCKED`.

Integration pattern in webhook.py:
```python
status, reason, violations = await compliance_guard.audit_message(
    message, contact_context={"contact_id": contact_id, "mode": "seller"}
)
if status == ComplianceStatus.BLOCKED:
    message = SAFE_FALLBACK_MESSAGE
    actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Compliance-Alert"))
```

**Seller fallback**: `"Let's stick to the facts about your property. What price are you looking to get?"`
**Buyer fallback**: `"I'd love to help you find your next home. What's most important to you in a property?"`
**Lead fallback**: `"Thanks for reaching out! I'd love to help. What are you looking for in your next home?"`

---

## 1.5 Lead Bot Handoff Integration

The [`JorgeHandoffService`](ghl_real_estate_ai/services/jorge/jorge_handoff_service.py:33) enables cross-bot handoffs when intent signals exceed confidence thresholds.

### Handoff Flow

```
Lead Bot Processing
    |
    +-- Extract intent signals (buyer_intent_score, seller_intent_score)
    |     via JorgeHandoffService.extract_intent_signals()
    |
    +-- Evaluate handoff decision
    |     if buyer_score >= 0.7 AND buyer_score > seller_score
    |         -> Handoff to Buyer Bot
    |     elif seller_score >= 0.7 AND seller_score > buyer_score
    |         -> Handoff to Seller Bot
    |
    +-- Execute handoff actions
          1. Remove source activation tag
          2. Add target activation tag
          3. Add handoff tracking tag
          4. Log analytics event
```

### Confidence Thresholds

| Direction | Threshold | Trigger Phrases |
|-----------|-----------|----------------|
| Lead → Buyer | 0.7 | "I want to buy", "budget $", "pre-approval", "looking to buy" |
| Lead → Seller | 0.7 | "Sell my house", "home worth", "CMA", "list my home" |
| Buyer → Seller | 0.8 | "Need to sell first", "sell before buying" |
| Seller → Buyer | 0.6 | "Also looking to buy", "need to find a new place" |

### Handoff Actions

When a handoff executes, the following GHL actions are generated:

| Action | Description |
|--------|-------------|
| `remove_tag` | Removes source bot's activation tag |
| `add_tag` | Adds target bot's activation tag |
| `add_tag` | Adds tracking tag (e.g., `Handoff-Lead-to-Buyer`) |

### Intent Pattern Detection

**Buyer Intent Patterns** (regex):
- `\bi\s+want\s+to\s+buy\b`
- `\blooking\s+to\s+buy\b`
- `\bbudget\b.*\# Jorge Bot Finalization Spec

**Version**: 1.1
**Branch**: `feature/advanced-rag-benchmarks`
**Status**: 142 bot tests passing (Lead: 23, Buyer: 50, Seller: 64, Handoff: 16)
**Date**: 2026-02-06

---

## Table of Contents

1. [Current Architecture](#1-current-architecture)
2. [Phase 1: Lead Bot Routing & Compliance](#2-phase-1-lead-bot-routing--compliance)
3. [Phase 2: Configurable GHL IDs](#3-phase-2-configurable-ghl-ids)
4. [Phase 3: Cross-Bot Handoff](#4-phase-3-cross-bot-handoff)
5. [Phase 4: Real MLS Data Integration](#5-phase-4-real-mls-data-integration)
6. [Phase 5: Integration Tests & Load Testing](#6-phase-5-integration-tests--load-testing)
7. [Test Patterns Reference](#7-test-patterns-reference)
8. [File Reference Index](#8-file-reference-index)
9. [Acceptance Criteria](#9-acceptance-criteria)

---

## 1. Current Architecture

### 1.1 Webhook Routing Flow

```
Incoming GHL Webhook (POST /ghl/webhook)
    |
    +-- Loopback check: outbound messages ignored
    +-- Activation tag check (lines 133-178)
    |     activation_tags from settings + buyer tag
    |     deactivation_tags: ["AI-Off", "Qualified", "Stop-Bot", "AI-Qualified"]
    |
    +-- Opt-out detection (lines 180-201)
    |     OPT_OUT_PHRASES: "stop", "unsubscribe", "not interested", etc.
    |     Action: add "AI-Off" tag, send confirmation
    |
    +-- SELLER ROUTING (lines 203-335)
    |     Condition: "Needs Qualifying" in tags AND JORGE_SELLER_MODE=true
    |     Bot: JorgeSellerEngine.process_seller_response()
    |     Tags: Hot-Seller, Warm-Seller, Cold-Seller
    |     Compliance: audit_message() with seller fallback
    |     Workflows: hot_seller_workflow, warm_seller_workflow
    |
    +-- BUYER ROUTING (lines 336-461)
    |     Condition: BUYER_ACTIVATION_TAG in tags AND JORGE_BUYER_MODE=true
    |     Bot: JorgeBuyerBot.process_buyer_conversation()
    |     Tags: Hot-Buyer, Warm-Buyer, Cold-Buyer, Buyer-Qualified
    |     Compliance: audit_message() with buyer fallback
    |
    +-- LEAD ROUTING (lines 462-650) **[NEW - COMPLETE]**
    |     Condition: LEAD_ACTIVATION_TAG in tags AND JORGE_LEAD_MODE=true
    |     Bot: ConversationManager.generate_response()
    |     Tags: Hot-Lead, Warm-Lead, Cold-Lead
    |     Compliance: audit_message() with lead fallback
    |     SMS Length Guard: 320-char truncation with smart boundaries
    |     Handoff: Evaluate lead→buyer/seller at 0.7 confidence
    |
    +-- DEFAULT FALLBACK (no mode matched)
          Route: Minimal response, no AI processing
```

### 1.2 Bot Entry Points

| Bot | Class | Entry Method | Return Keys |
|-----|-------|-------------|-------------|
| Lead | `ConversationManager` | `generate_response()` via webhook fallback | `message`, `actions` (via `prepare_ghl_actions`) |
| Buyer | `JorgeBuyerBot` | `process_buyer_conversation(buyer_id, buyer_name, conversation_history)` | `buyer_temperature`, `is_qualified`, `response_content`, `matched_properties`, `financial_readiness_score`, `buying_motivation_score` |
| Seller | `JorgeSellerEngine` | `process_seller_response(contact_id, user_message, location_id, tenant_config, images)` | `message`, `actions`, `temperature`, `seller_data`, `questions_answered`, `analytics`, `pricing` |

### 1.3 Configuration Architecture

```
jorge_config.py
    +-- JorgeSellerConfig (dataclass, lines 17-335)
    |     Static config: tags, thresholds, workflows, custom fields, questions
    |     Helper methods: get_workflow_id(), get_ghl_custom_field_id()
    |
    +-- JorgeEnvironmentSettings (class, lines 337-412)
    |     Runtime config loaded from env vars
    |     Properties: JORGE_SELLER_MODE, JORGE_BUYER_MODE, BUYER_ACTIVATION_TAG
    |     List parsing: _parse_list_env() (JSON or CSV)
    |
    +-- JorgeMarketManager (class, lines 414-473)
    |     Market-specific config (Rancho Cucamonga)
    |
    +-- Module exports (lines 475-499)
          settings = JorgeEnvironmentSettings()
          Exported: JORGE_SELLER_MODE, ACTIVATION_TAGS, DEACTIVATION_TAGS
```


- `\bpre[- ]?approv\b`
- `\bfind\s+(a|my)\s+(new\s+)?(home|house|place|property)\b`

**Seller Intent Patterns** (regex):
- `\bsell\s+my\s+(home|house|property)\b`
- `\bwhat'?s\s+my\s+home\s+worth\b`
- `\bhome\s+valu\b`
- `\bcma\b`
- `\blist(ing)?\s+my\s+(home|house|property)\b`

---

## 2. Phase 1: Lead Bot Routing & Compliance

### 2.1 Problem

The lead bot only fires as the default fallback in webhook.py (lines 462+). It has no explicit activation tag, no mode flag, and no compliance guard. Buyer and seller both have dedicated routing blocks with tag detection, compliance, and temperature classification.

### 2.2 Changes Required

#### 2.2.1 `jorge_config.py` — Add Lead Bot Configuration

**Add to `JorgeEnvironmentSettings.__init__()` (after line 376):**

```python
# Lead bot mode
self.jorge_lead_mode = os.getenv("JORGE_LEAD_MODE", "true").lower() == "true"
self.lead_activation_tag = os.getenv("LEAD_ACTIVATION_TAG", "Needs Qualifying")
```

Note: `JORGE_LEAD_MODE` defaults to `true` because the lead bot is the original default behavior. This flag lets operators disable it explicitly.

**Add compatibility properties (after line 411):**

```python
@property
def JORGE_LEAD_MODE(self) -> bool:
    return self.jorge_lead_mode

@property
def LEAD_ACTIVATION_TAG(self) -> str:
    return self.lead_activation_tag
```

**Add to `__all__` exports.**

#### 2.2.2 `webhook.py` — Add Lead Bot Routing Block

Insert a new routing block between the buyer routing (line 461) and the current default fallback (line 462). The lead bot routing should mirror the seller/buyer pattern:

```
+-- LEAD BOT ROUTING (new, between buyer and current fallback)
      Condition: LEAD_ACTIVATION_TAG in tags
                 AND JORGE_LEAD_MODE=true
                 AND NOT seller mode matched
                 AND NOT buyer mode matched
      Bot: ConversationManager (existing logic from lines 462-816)
      Compliance: audit_message() with lead-specific fallback
      Tags: Hot-Lead, Warm-Lead, Cold-Lead (already in prepare_ghl_actions)
```

**Compliance guard for lead bot** — add after AI response generation, before sending:

```python
status, reason, violations = await compliance_guard.audit_message(
    ai_response,
    contact_context={"contact_id": contact_id, "mode": "lead"}
)
if status == ComplianceStatus.BLOCKED:
    ai_response = "Thanks for reaching out! I'd love to help. What are you looking for in your next home?"
    actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Compliance-Alert"))
```

The lead fallback message should be neutral and not assume buyer or seller intent.

#### 2.2.3 `.env.example` — Add Lead Bot Vars

Add to the Jorge Bot Mode Flags section (after line 157):

```bash
# Jorge Lead Mode — routes contacts through lead qualification (default: true)
JORGE_LEAD_MODE=true

# Tag that activates lead mode routing (default: Needs Qualifying)
LEAD_ACTIVATION_TAG=Needs Qualifying
```

#### 2.2.4 `railway.jorge.toml` — Add Lead Bot Deployment Config

Add alongside existing bot mode flags:

```toml
JORGE_LEAD_MODE = "true"
```

### 2.3 Tests Required

Add to `tests/test_jorge_delivery.py` following the existing buyer routing test pattern:

**Test fixture**: Create `_lead_webhook_patches()` context manager mirroring `_buyer_webhook_patches()`.

**9 lead routing tests** (mirror buyer routing test structure):

| # | Test | Asserts |
|---|------|---------|
| 1 | `test_lead_mode_activates_with_needs_qualifying_tag` | Lead bot processes when tag present + mode=true |
| 2 | `test_seller_mode_takes_priority_over_lead` | "Needs Qualifying" routes to seller when JORGE_SELLER_MODE=true |
| 3 | `test_lead_mode_respects_deactivation_tags` | AI-Off blocks lead routing |
| 4 | `test_lead_mode_disabled_skips_to_fallback` | JORGE_LEAD_MODE=false skips routing |
| 5 | `test_lead_mode_adds_temperature_tag` | Hot-Lead/Warm-Lead/Cold-Lead applied |
| 6 | `test_lead_mode_sms_guard_truncates` | Response truncated at 320 chars |
| 7 | `test_lead_mode_compliance_blocks_bad_message` | Compliance replaces blocked content |
| 8 | `test_lead_mode_error_falls_through` | Error doesn't crash webhook |
| 9 | `test_buyer_lead_tag_does_not_route_to_lead_bot` | "Buyer-Lead" tag goes to buyer, not lead |

**Priority note**: Test #2 is critical — when both `JORGE_SELLER_MODE=true` and the contact has "Needs Qualifying", the seller engine must take priority over the lead bot. This is the existing behavior and must be preserved.

### 2.4 Routing Priority (Final)

After this phase, the routing priority in webhook.py should be:

1. Loopback check
2. Activation/deactivation tag check
3. Opt-out detection
4. **Seller mode** (highest bot priority — "Needs Qualifying" + JORGE_SELLER_MODE)
5. **Buyer mode** (BUYER_ACTIVATION_TAG + JORGE_BUYER_MODE)
6. **Lead mode** (LEAD_ACTIVATION_TAG + JORGE_LEAD_MODE) — wraps existing fallback logic with compliance
7. **Raw fallback** (no mode matched — return minimal response)

---

## 3. Phase 2: Configurable GHL IDs

### 3.1 Problem

GHL workflow IDs and custom field IDs in `jorge_config.py` are placeholder strings. The existing helper methods (`get_workflow_id()`, `get_ghl_custom_field_id()`) already support env var overrides, but:

- The placeholders give false confidence that values are configured
- `.env.example` has placeholder field names, not real GHL UUIDs
- `railway.jorge.toml` is missing workflow ID and custom field variables
- No validation warns when placeholders are still in use

### 3.2 Changes Required

#### 3.2.1 `jorge_config.py` — Workflow IDs

**Current** (lines 72-74):
```python
HOT_SELLER_WORKFLOW_ID = "jorge_hot_seller_workflow"
WARM_SELLER_WORKFLOW_ID = "jorge_warm_seller_workflow"
AGENT_NOTIFICATION_WORKFLOW = "jorge_agent_notification"
```

**Change to**:
```python
HOT_SELLER_WORKFLOW_ID = ""   # Set via HOT_SELLER_WORKFLOW_ID env var
WARM_SELLER_WORKFLOW_ID = ""  # Set via WARM_SELLER_WORKFLOW_ID env var
AGENT_NOTIFICATION_WORKFLOW = ""  # Set via NOTIFY_AGENT_WORKFLOW_ID env var
```

Empty strings instead of placeholders. The `get_workflow_id()` method (lines 313-320) already falls back to env vars. Empty string is falsy, so `if workflow_id:` guards in webhook.py will correctly skip unconfigured workflows.

#### 3.2.2 `jorge_config.py` — Custom Field IDs

**Current** (lines 77-92): All values are placeholder strings like `"seller_temp_field_id"`.

**Change to**: Empty strings for all custom field entries in `CUSTOM_FIELDS` dict. The `get_ghl_custom_field_id()` method (lines 307-311) checks env vars first: `CUSTOM_FIELD_{field_name.upper()}`.

#### 3.2.3 `jorge_config.py` — Add Startup Validation

Add a validation method to `JorgeEnvironmentSettings`:

```python
def validate_ghl_integration(self) -> List[str]:
    """Return warnings for missing GHL configuration."""
    warnings = []
    if self.jorge_seller_mode:
        if not os.getenv("HOT_SELLER_WORKFLOW_ID"):
            warnings.append("HOT_SELLER_WORKFLOW_ID not set — hot seller workflows disabled")
        if not os.getenv("WARM_SELLER_WORKFLOW_ID"):
            warnings.append("WARM_SELLER_WORKFLOW_ID not set — warm seller workflows disabled")
    if self.jorge_buyer_mode:
        if not os.getenv("HOT_BUYER_WORKFLOW_ID"):
            warnings.append("HOT_BUYER_WORKFLOW_ID not set — hot buyer workflows disabled")
    # Check critical custom fields
    critical_fields = ["LEAD_SCORE", "SELLER_TEMPERATURE", "BUDGET"]
    for field in critical_fields:
        if not os.getenv(f"CUSTOM_FIELD_{field}"):
            warnings.append(f"CUSTOM_FIELD_{field} not set — field updates will use semantic names")
    return warnings
```

Call this at module level and log warnings:

```python
settings = JorgeEnvironmentSettings()
for warning in settings.validate_ghl_integration():
    logger.warning(f"GHL Config: {warning}")
```

#### 3.2.4 `JorgeEnvironmentSettings.__init__()` — Add Buyer Workflow IDs

The seller workflow IDs are already loaded (lines 371-372). Add buyer equivalents:

```python
self.hot_buyer_workflow_id = os.getenv("HOT_BUYER_WORKFLOW_ID")
self.warm_buyer_workflow_id = os.getenv("WARM_BUYER_WORKFLOW_ID")
```

#### 3.2.5 `.env.example` — Document All GHL IDs

Replace the existing custom field section (lines 216-235) with clearly documented sections:

```bash
# ==============================================================================
# GHL WORKFLOW IDS (Get from GHL Dashboard > Automation > Workflows)
# ==============================================================================
# These are REQUIRED for full automation. Without them, workflows won't trigger
# but the bots will still process and respond.

# Seller workflows
HOT_SELLER_WORKFLOW_ID=          # Triggers agent notification for hot sellers
WARM_SELLER_WORKFLOW_ID=         # Triggers nurture sequence for warm sellers

# Buyer workflows
HOT_BUYER_WORKFLOW_ID=           # Triggers showing coordination for hot buyers
WARM_BUYER_WORKFLOW_ID=          # Triggers buyer nurture sequence

# General
NOTIFY_AGENT_WORKFLOW_ID=        # Sends SMS/email to agent for qualified leads

# ==============================================================================
# GHL CUSTOM FIELD IDS (Get from GHL Dashboard > Settings > Custom Fields)
# ==============================================================================
# Format: UUID-style strings from GHL. If not set, semantic field names are used
# as fallback (may not map to actual GHL fields).

# Lead scoring fields
CUSTOM_FIELD_LEAD_SCORE=
CUSTOM_FIELD_BUDGET=
CUSTOM_FIELD_LOCATION=
CUSTOM_FIELD_TIMELINE=

# Seller qualification fields
CUSTOM_FIELD_SELLER_TEMPERATURE=
CUSTOM_FIELD_SELLER_MOTIVATION=
CUSTOM_FIELD_TIMELINE_URGENCY=
CUSTOM_FIELD_PROPERTY_CONDITION=
CUSTOM_FIELD_PRICE_EXPECTATION=

# Buyer qualification fields
CUSTOM_FIELD_BUYER_TEMPERATURE=
CUSTOM_FIELD_PRE_APPROVAL_STATUS=
CUSTOM_FIELD_PROPERTY_PREFERENCES=

# Analytics fields
CUSTOM_FIELD_EXPECTED_ROI=
CUSTOM_FIELD_LEAD_VALUE_TIER=
CUSTOM_FIELD_AI_VALUATION_PRICE=
CUSTOM_FIELD_DETECTED_PERSONA=
```

#### 3.2.6 `railway.jorge.toml` — Add All GHL Variables

Add to the `[env]` section:

```toml
# GHL Workflow IDs
HOT_SELLER_WORKFLOW_ID = { description = "GHL workflow for hot seller agent notification" }
WARM_SELLER_WORKFLOW_ID = { description = "GHL workflow for warm seller nurture" }
HOT_BUYER_WORKFLOW_ID = { description = "GHL workflow for hot buyer showing coordination" }
WARM_BUYER_WORKFLOW_ID = { description = "GHL workflow for warm buyer nurture" }
```

### 3.3 Tests Required

Add to a new test file `tests/test_jorge_config_validation.py`:

| # | Test | Asserts |
|---|------|---------|
| 1 | `test_validate_warns_on_missing_workflow_ids` | validate_ghl_integration() returns warnings when env vars absent |
| 2 | `test_validate_clean_when_all_set` | No warnings when all env vars present |
| 3 | `test_get_workflow_id_returns_env_over_default` | Env var takes priority over dataclass default |
| 4 | `test_get_workflow_id_returns_none_when_empty` | Empty default + no env var = None (falsy) |
| 5 | `test_get_custom_field_id_env_override` | CUSTOM_FIELD_X env var overrides static mapping |
| 6 | `test_get_custom_field_id_fallback` | Returns semantic name when env var not set |
| 7 | `test_seller_mode_disabled_skips_seller_validation` | No seller warnings when JORGE_SELLER_MODE=false |

---

## 4. Phase 3: Cross-Bot Handoff

### 4.1 Problem

The lead bot references a `jorge_handoffs` counter (lead_bot.py ~line 569) but doesn't implement actual handoff logic. There's no mechanism to transition a contact from one bot to another (e.g., lead qualifies as a buyer, lead identifies as a seller).

### 4.2 Design

Handoff is tag-driven. When Bot A determines the contact should be handled by Bot B, it:

1. Removes Bot A's activation tag
2. Adds Bot B's activation tag
3. Adds a handoff tracking tag (e.g., `Handoff-Lead-to-Buyer`)
4. Logs the handoff event via analytics_service

The next inbound message from the contact will route to Bot B via the existing tag-based routing.

### 4.3 Changes Required

#### 4.3.1 New Service: `services/jorge/jorge_handoff_service.py`

```python
class HandoffDecision:
    """Encapsulates a bot-to-bot handoff decision."""
    source_bot: str          # "lead", "buyer", "seller"
    target_bot: str          # "lead", "buyer", "seller"
    reason: str              # "buyer_intent_detected", "seller_intent_detected", etc.
    confidence: float        # 0.0-1.0
    context: Dict[str, Any]  # Conversation context to preserve

class JorgeHandoffService:
    TAG_MAP = {
        "lead": "Needs Qualifying",
        "buyer": "Buyer-Lead",
        "seller": "Needs Qualifying",  # Seller uses same tag, differentiated by mode
    }

    async def evaluate_handoff(
        self,
        current_bot: str,
        contact_id: str,
        conversation_history: List[Dict],
        intent_signals: Dict[str, Any]
    ) -> Optional[HandoffDecision]:
        """Evaluate whether a handoff is needed based on intent signals."""

    async def execute_handoff(
        self,
        decision: HandoffDecision,
        contact_id: str,
        ghl_client: GHLClient
    ) -> List[GHLAction]:
        """Generate GHL actions to execute the handoff."""
```

**Intent signal detection rules**:

| Current Bot | Signal | Target Bot | Confidence Threshold |
|-------------|--------|------------|---------------------|
| Lead | "I want to buy", budget mention, pre-approval mention | Buyer | 0.7 |
| Lead | "Sell my house", "what's my home worth", CMA request | Seller | 0.7 |
| Buyer | "Actually I need to sell first", "sell before buying" | Seller | 0.8 |
| Seller | "Also looking to buy", "need to find a new place" | Buyer | 0.6 (lower because common) |

#### 4.3.2 `webhook.py` — Integrate Handoff Actions

After each bot processes a response, check for handoff signals in the result and append handoff actions:

```python
# After seller response processing (line ~320)
if seller_result.get("handoff_signals"):
    handoff = await handoff_service.evaluate_handoff(
        current_bot="seller", contact_id=contact_id,
        conversation_history=history, intent_signals=seller_result["handoff_signals"]
    )
    if handoff:
        actions.extend(await handoff_service.execute_handoff(handoff, contact_id, ghl_client))
```

Same pattern after buyer and lead bot blocks.

#### 4.3.3 Bot Return Contract Extension

Each bot's return dict should include an optional `handoff_signals` key:

```python
{
    # ... existing fields ...
    "handoff_signals": {
        "buyer_intent_score": 0.85,   # From intent decoder
        "seller_intent_score": 0.1,
        "detected_intent_phrases": ["looking to buy", "budget around 600k"]
    }
}
```

### 4.4 Tests Required

New file: `tests/services/test_jorge_handoff_service.py`

| # | Test | Asserts |
|---|------|---------|
| 1 | `test_lead_to_buyer_handoff_on_buyer_intent` | Buyer intent score >0.7 triggers handoff |
| 2 | `test_lead_to_seller_handoff_on_seller_intent` | Seller intent phrases trigger handoff |
| 3 | `test_no_handoff_below_confidence_threshold` | Score 0.5 does not trigger |
| 4 | `test_handoff_generates_correct_tag_swap` | Removes source tag, adds target tag |
| 5 | `test_handoff_adds_tracking_tag` | "Handoff-Lead-to-Buyer" tag present |
| 6 | `test_handoff_logs_analytics_event` | analytics_service.track_event called |
| 7 | `test_seller_to_buyer_handoff` | Cross-direction handoff works |
| 8 | `test_buyer_to_seller_handoff` | Reverse handoff works |

Integration test in `tests/integration/test_full_jorge_flow.py`:

| # | Test |
|---|------|
| 1 | `test_lead_qualifies_as_buyer_full_flow` | Lead bot -> handoff -> buyer bot processes next message |
| 2 | `test_seller_also_buying_full_flow` | Seller bot -> handoff -> buyer bot on next message |

---

## 5. Phase 4: Real MLS Data Integration

### 5.1 Problem

`jorge_seller_engine.py` lines 225-231 use a mock `ListingHistory`:

```python
mock_history = ListingHistory(
    property_id=contact_id,
    days_on_market=context.get("days_since_first_contact", 0),
    original_list_price=float(extracted_seller_data.get("price_expectation", 0) or 0),
    current_price=float(extracted_seller_data.get("price_expectation", 0) or 0),
    price_drops=[]
)
```

This feeds into `seller_psychology_analyzer` which calculates negotiation stance and price sensitivity. With mock data, the psychology analysis is unreliable.

### 5.2 Changes Required

#### 5.2.1 New Integration: `services/mls_client.py`

```python
class MLSClient:
    """Client for MLS/Attom property data integration."""

    async def get_listing_history(self, property_address: str) -> Optional[ListingHistory]:
        """Fetch listing history from MLS data feed."""

    async def get_property_valuation(self, property_address: str) -> Optional[PropertyValuation]:
        """Fetch AVM (Automated Valuation Model) estimate."""

    async def get_comparable_sales(self, property_address: str, radius_miles: float = 1.0) -> List[ComparableSale]:
        """Fetch recent comparable sales for CMA generation."""
```

Data sources (in priority order):
1. **Attom API** — Property valuation, listing history, comparable sales
2. **MLS RETS feed** — Direct MLS data (requires board membership)
3. **Fallback** — Use contact-provided data (current behavior)

#### 5.2.2 `jorge_seller_engine.py` — Replace Mock

Replace lines 225-231 with:

```python
# Attempt real listing history lookup
listing_history = None
property_address = extracted_seller_data.get("property_address") or context.get("property_address")
if property_address and mls_client:
    try:
        listing_history = await mls_client.get_listing_history(property_address)
    except Exception as e:
        logger.warning(f"MLS lookup failed for {property_address}: {e}")

# Fallback to contact-provided data
if not listing_history:
    listing_history = ListingHistory(
        property_id=contact_id,
        days_on_market=context.get("days_since_first_contact", 0),
        original_list_price=float(extracted_seller_data.get("price_expectation", 0) or 0),
        current_price=float(extracted_seller_data.get("price_expectation", 0) or 0),
        price_drops=[]
    )
```

#### 5.2.3 Configuration

Add to `.env.example`:

```bash
# MLS/Property Data Integration
ATTOM_API_KEY=                   # Attom Data API key for property valuations
MLS_RETS_URL=                    # MLS RETS feed URL (if available)
MLS_RETS_USERNAME=
MLS_RETS_PASSWORD=
ENABLE_MLS_INTEGRATION=false     # Enable real MLS data lookups
```

### 5.3 Tests Required

| # | Test | Asserts |
|---|------|---------|
| 1 | `test_seller_engine_uses_mls_when_available` | Real listing history used when MLS returns data |
| 2 | `test_seller_engine_fallback_when_mls_fails` | Mock data used when MLS throws |
| 3 | `test_seller_engine_fallback_when_no_address` | Mock data used when no property address |
| 4 | `test_psychology_analyzer_with_real_listing_data` | Price drops detected in psychology profile |

---

## 6. Phase 5: Integration Tests & Load Testing

### 6.1 Comprehensive Webhook Routing Tests

New file: `tests/integration/test_webhook_routing_comprehensive.py`

Tests all three bot modes in a single test suite with shared fixtures:

| # | Test | Scenario |
|---|------|----------|
| 1 | `test_all_three_modes_concurrent` | Three contacts, each with different tags, all routed correctly |
| 2 | `test_priority_seller_over_lead` | "Needs Qualifying" + SELLER_MODE routes to seller, not lead |
| 3 | `test_priority_buyer_over_lead` | "Buyer-Lead" routes to buyer, not lead |
| 4 | `test_priority_seller_over_buyer` | Both tags present, seller wins |
| 5 | `test_deactivation_blocks_all_modes` | "AI-Off" stops all three bots |
| 6 | `test_opt_out_from_any_mode` | "stop" message deactivates regardless of bot mode |
| 7 | `test_mode_flags_disable_correctly` | All modes false = raw fallback response |
| 8 | `test_error_in_seller_falls_to_buyer` | Seller error, buyer tag present, buyer processes |
| 9 | `test_error_in_all_bots_returns_fallback` | All bots error, safe fallback returned |
| 10 | `test_compliance_enforced_all_modes` | Blocked message replaced in all three paths |

### 6.2 Load Testing

Extend `tests/load/test_jorge_platform_load_testing.py`:

| # | Test | Target |
|---|------|--------|
| 1 | `test_100_concurrent_seller_webhooks` | <2s p99 response time |
| 2 | `test_100_concurrent_buyer_webhooks` | <2s p99 response time |
| 3 | `test_100_concurrent_lead_webhooks` | <2s p99 response time |
| 4 | `test_mixed_mode_load_300_concurrent` | 100 each, <3s p99 |
| 5 | `test_handoff_under_load` | Handoff tag swaps complete correctly under concurrency |

### 6.3 Configuration Validation Tests

New file: `tests/test_deployment_readiness.py`

| # | Test | Asserts |
|---|------|---------|
| 1 | `test_all_env_vars_documented` | Every env var in code appears in .env.example |
| 2 | `test_railway_toml_matches_env_example` | Critical vars in railway.jorge.toml |
| 3 | `test_activation_tags_consistent` | Tags in config match tags in webhook routing |
| 4 | `test_no_placeholder_workflow_ids_in_production` | Env=production rejects empty workflow IDs |

---

## 7. Test Patterns Reference

### 7.1 Webhook Routing Test Pattern

```python
def _lead_webhook_patches(jorge_lead_mode=True, jorge_seller_mode=False, jorge_buyer_mode=False):
    """Context manager for lead bot webhook test isolation."""
    @contextmanager
    def _patches():
        mock_settings = MagicMock()
        mock_settings.JORGE_LEAD_MODE = jorge_lead_mode
        mock_settings.JORGE_SELLER_MODE = jorge_seller_mode
        mock_settings.JORGE_BUYER_MODE = jorge_buyer_mode
        mock_settings.LEAD_ACTIVATION_TAG = "Needs Qualifying"
        mock_settings.ACTIVATION_TAGS = ["Needs Qualifying"]
        mock_settings.DEACTIVATION_TAGS = ["AI-Off", "Qualified", "Stop-Bot"]

        mock_conversation_manager = AsyncMock()
        mock_conversation_manager.generate_response = AsyncMock(return_value={
            "message": "Test lead response",
            "actions": []
        })

        with patch("ghl_real_estate_ai.api.routes.webhook.jorge_settings", mock_settings), \
             patch("ghl_real_estate_ai.api.routes.webhook.conversation_manager", mock_conversation_manager), \
             patch("ghl_real_estate_ai.api.routes.webhook.compliance_guard") as mock_compliance, \
             patch("ghl_real_estate_ai.api.routes.webhook.analytics_service", AsyncMock()), \
             patch("ghl_real_estate_ai.api.routes.webhook.ghl_client_default", AsyncMock()):

            mock_compliance.audit_message = AsyncMock(
                return_value=(ComplianceStatus.PASSED, "", [])
            )
            yield {
                "settings": mock_settings,
                "conversation_manager": mock_conversation_manager,
                "compliance_guard": mock_compliance,
            }
    return _patches()
```

### 7.2 Bot Instance Test Pattern

```python
@pytest.fixture
def mock_dependencies(self):
    with patch.multiple(
        'ghl_real_estate_ai.agents.jorge_buyer_bot',
        BuyerIntentDecoder=AsyncMock,
        ClaudeAssistant=AsyncMock,
        get_event_publisher=Mock,
        PropertyMatcher=AsyncMock,
        get_ml_analytics_engine=Mock
    ) as mocks:
        yield mocks
```

### 7.3 Assertion Patterns

```python
# Temperature classification
assert result["buyer_temperature"] in ("hot", "warm", "cold")

# Tag presence
tag_names = [a.tag for a in response.actions if a.type == ActionType.ADD_TAG]
assert "Hot-Seller" in tag_names

# Compliance
assert len(response.message) <= 320  # SMS guard
assert "-" not in response.message   # No hyphens (Jorge rule)

# Mock verification
bot.event_publisher.publish_buyer_qualification_complete.assert_called_once()
call_kwargs = bot.event_publisher.publish_buyer_qualification_complete.call_args
assert call_kwargs.kwargs["status"] == "qualified"
```

### 7.4 Webhook Event Factory

```python
def _make_webhook_event(message_body: str, tags: List[str], contact_id: str = "test_123"):
    return GHLWebhookEvent(
        type="InboundMessage",
        contactId=contact_id,
        locationId="loc_test",
        message=GHLMessage(
            type=MessageType.SMS,
            body=message_body,
            direction=MessageDirection.INBOUND,
        ),
        contact=GHLContact(
            contactId=contact_id,
            firstName="Test",
            lastName="User",
            tags=tags,
            customFields={},
        ),
    )
```

---

## 8. File Reference Index

### Core Implementation Files

| File | Lines | Purpose |
|------|-------|---------|
| `ghl_real_estate_ai/api/routes/webhook.py` | ~1100 | Main webhook handler, all bot routing |
| `ghl_real_estate_ai/ghl_utils/jorge_config.py` | ~499 | JorgeSellerConfig, JorgeEnvironmentSettings, JorgeMarketManager |
| `ghl_real_estate_ai/agents/lead_bot.py` | ~2800 | Lead bot with 3-7-30 follow-up, LangGraph workflow |
| `ghl_real_estate_ai/agents/jorge_buyer_bot.py` | ~600 | Buyer bot with 6-node LangGraph workflow |
| `ghl_real_estate_ai/agents/jorge_seller_bot.py` | ~900 | Seller bot with 7-node LangGraph workflow |
| `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py` | ~900 | Seller engine (webhook entry point for seller) |
| `ghl_real_estate_ai/services/jorge/jorge_tone_engine.py` | ~200 | Confrontational tone generation, negotiation drift |
| `ghl_real_estate_ai/services/jorge/jorge_followup_engine.py` | ~200 | Follow-up sequence logic |
| `ghl_real_estate_ai/services/jorge/jorge_followup_scheduler.py` | ~200 | Distributed follow-up scheduling |
| `ghl_real_estate_ai/services/compliance_guard.py` | ~131 | 3-tier Fair Housing compliance |
| `ghl_real_estate_ai/services/ghl_client.py` | ~700 | GHL API client (send_message, add_tags, apply_actions) |
| `ghl_real_estate_ai/api/schemas/ghl.py` | ~113 | GHLWebhookEvent, GHLAction, GHLWebhookResponse |

### Configuration Files

| File | Purpose |
|------|---------|
| `.env.example` | Environment variable template (~301 lines) |
| `railway.jorge.toml` | Railway deployment config (~57 lines) |

### Test Files

| File | Tests | Bot |
|------|-------|-----|
| `tests/agents/test_buyer_bot.py` | 50 | Buyer |
| `tests/agents/test_jorge_seller_bot.py` | 64 | Seller |
| `tests/agents/test_lead_bot_day14.py` | ~7 | Lead (Day 14 flow) |
| `tests/agents/test_lead_bot_day14_cma.py` | ~7 | Lead (CMA PDF) |
| `tests/test_jorge_delivery.py` | ~20 | Webhook routing (seller + 9 buyer) |
| `tests/integration/test_full_jorge_flow.py` | varies | Cross-bot integration |
| `tests/security/test_jorge_webhook_security.py` | ~8 categories | Webhook security |

### Key Line References

| Reference | File | Lines |
|-----------|------|-------|
| Seller routing block | webhook.py | 203-335 |
| Buyer routing block | webhook.py | 336-461 |
| Default fallback | webhook.py | 462-816 |
| Activation tag check | webhook.py | 133-178 |
| Seller compliance guard | webhook.py | 288-307 |
| Buyer compliance guard | webhook.py | 414-423 |
| prepare_ghl_actions() | webhook.py | 820-1035 |
| JorgeSellerConfig class | jorge_config.py | 17-335 |
| JorgeEnvironmentSettings class | jorge_config.py | 337-412 |
| BUYER_ACTIVATION_TAG property | jorge_config.py | 401 |
| get_workflow_id() | jorge_config.py | 313-320 |
| get_ghl_custom_field_id() | jorge_config.py | 307-311 |
| _parse_list_env() | jorge_config.py | 377-386 |
| Mock ListingHistory | jorge_seller_engine.py | 225-231 |
| process_seller_response() | jorge_seller_engine.py | 152-434 |
| process_buyer_conversation() | jorge_buyer_bot.py | 1177-1242 |
| Jorge's 4 seller questions | jorge_seller_engine.py | 36-93 |

---

## 9. Acceptance Criteria

### Phase 1: Lead Bot Routing & Compliance
- [x] `JORGE_LEAD_MODE` env var controls lead bot routing
- [x] `LEAD_ACTIVATION_TAG` configurable (default: "Needs Qualifying")
- [x] Compliance guard intercepts lead bot responses before sending
- [x] Lead bot fallback message is neutral (not buyer/seller specific)
- [x] Seller mode still takes priority over lead when both could match
- [x] Buyer mode still takes priority over lead when buyer tag present
- [x] 9 new routing tests passing
- [x] All 128 existing tests still passing

### Phase 2: Configurable GHL IDs
- [x] All workflow IDs default to empty string (not placeholder)
- [x] All custom field IDs default to empty string (not placeholder)
- [x] Startup validation logs warnings for missing GHL config
- [x] `.env.example` documents all GHL variables with instructions
- [x] `railway.jorge.toml` includes all workflow ID variables
- [x] Buyer workflow IDs added to JorgeEnvironmentSettings
- [x] 7 new config validation tests passing

### Phase 3: Cross-Bot Handoff
- [x] JorgeHandoffService evaluates intent signals
- [x] Tag swap executes correctly (remove source tag, add target tag)
- [x] Handoff tracking tag added for analytics
- [x] Confidence threshold prevents false handoffs
- [x] All three handoff directions work (lead->buyer, lead->seller, buyer<->seller)
- [x] 8 new handoff service tests + 2 integration tests passing

### Phase 4: Real MLS Data Integration
- [x] MLSClient interfaces defined
- [x] Seller engine uses real listing data when available
- [x] Graceful fallback to mock data on MLS failure
- [x] Environment variables for Attom API configuration
- [x] 4 new MLS integration tests passing

### Phase 5: Integration Tests & Load Testing
- [x] 10 comprehensive webhook routing tests covering all modes
- [x] Load tests validate <2s p99 for each mode
- [x] Mixed mode load test validates <3s p99
- [x] Deployment readiness tests validate config consistency
- [x] All tests across all phases passing (target: 170+ total bot tests)

---

## Implementation Order

```
Phase 1 ─── Lead Bot Routing & Compliance ─── BLOCKING (no lead bot in production without this)
   |
Phase 2 ─── Configurable GHL IDs ─── BLOCKING (can't connect to real GHL workflows)
   |
Phase 3 ─── Cross-Bot Handoff ─── FUNCTIONAL (improves lead routing, not blocking)
   |
Phase 4 ─── Real MLS Data ─── ENHANCEMENT (improves seller analysis accuracy)
   |
Phase 5 ─── Integration & Load Tests ─── VALIDATION (confirms production readiness)
```

Phases 1 and 2 can be developed in parallel.
Phase 3 depends on Phase 1 (needs lead bot routing to exist).
Phase 4 is independent and can be developed at any time.
Phase 5 depends on all other phases.

---

## 10. Configuration Validation

### 10.1 Environment Variables Required

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JORGE_LEAD_MODE` | No | `true` | Enable Lead Bot routing |
| `LEAD_ACTIVATION_TAG` | No | `Needs Qualifying` | Tag that triggers Lead Bot |
| `JORGE_SELLER_MODE` | No | `false` | Enable Seller Bot routing |
| `JORGE_BUYER_MODE` | No | `false` | Enable Buyer Bot routing |
| `HOT_SELLER_WORKFLOW_ID` | No | `` | GHL workflow for hot sellers |
| `WARM_SELLER_WORKFLOW_ID` | No | `` | GHL workflow for warm sellers |
| `HOT_BUYER_WORKFLOW_ID` | No | `` | GHL workflow for hot buyers |
| `CUSTOM_FIELD_LEAD_SCORE` | No | `` | GHL custom field for lead score |
| `CUSTOM_FIELD_SELLER_TEMPERATURE` | No | `` | GHL custom field for seller temperature |
| `CUSTOM_FIELD_BUYER_TEMPERATURE` | No | `` | GHL custom field for buyer temperature |

### 10.2 Tag Configuration

| Bot | Activation Tag | Deactivation Tags |
|-----|----------------|-------------------|
| Lead | `Needs Qualifying` | `AI-Off`, `Qualified`, `Stop-Bot` |
| Buyer | `Buyer-Lead` | `AI-Off`, `Qualified`, `Stop-Bot` |
| Seller | `Needs Qualifying` | `AI-Off`, `Qualified`, `Stop-Bot` |

### 10.3 Routing Priority

When multiple activation tags are present, the routing priority is:

1. **Seller Bot** — Highest priority (when `JORGE_SELLER_MODE=true`)
2. **Buyer Bot** — When `BUYER_ACTIVATION_TAG` present (when `JORGE_BUYER_MODE=true`)
3. **Lead Bot** — When `LEAD_ACTIVATION_TAG` present (when `JORGE_LEAD_MODE=true`)
4. **Default Fallback** — No bot mode matched

### 10.4 Validation Checklist

- [ ] All required environment variables documented in `.env.example`
- [ ] `JORGE_LEAD_MODE` defaults to `true` (Lead Bot is the default behavior)
- [ ] `validate_ghl_integration()` runs at startup and logs warnings
- [ ] Tag names in config match GHL dashboard exactly
- [ ] Workflow IDs are valid UUIDs (not placeholder strings)
- [ ] Custom field IDs are valid UUIDs (not placeholder strings)

### 10.5 Startup Validation Output

When the application starts, it should output validation warnings for missing configuration:

```
GHL Config Warning: HOT_SELLER_WORKFLOW_ID not set — hot seller workflows disabled
GHL Config Warning: CUSTOM_FIELD_LEAD_SCORE not set — field updates will use semantic names
```

---

**Document Version**: 1.1
**Last Updated**: 2026-02-06
**Next Review**: After Phase 5 completion
