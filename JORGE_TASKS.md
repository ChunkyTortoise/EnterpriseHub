# Jorge Delivery — Unified Task List

> **Shared across all parallel agent sessions.**
> **Before starting a task: check this file. If status is `DONE` or `IN-PROGRESS [Agent X]`, skip it.**
> **After completing a task: update status to `DONE` with a one-line summary of what changed.**
> **Reference JORGE_SPEC.md for all requirements.**

---

## Stream A: Seller Bot Core Fixes

| ID | Task | Status | Owner | Files |
|----|------|--------|-------|-------|
| A1 | Remove "Hit List" from activation_tags | `DONE` | Stream A | `ghl_real_estate_ai/ghl_utils/config.py` — Removed "Hit List" and "Need to Qualify", kept only "Needs Qualifying"; changed bot_active_disposition to "Needs Qualifying" |
| A2 | Add JORGE_SIMPLE_MODE config flag | `DONE` | Stream A | `ghl_real_estate_ai/ghl_utils/jorge_config.py` — Added JORGE_SIMPLE_MODE: bool = True to JorgeSellerConfig |
| A3 | Gate enterprise branches in seller engine behind JORGE_SIMPLE_MODE | `DONE` | Stream A | `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py` — Added early guard + _generate_simple_response with 4 paths only |
| A4 | Remove duplicate arbitrage code block (lines ~860-900 duplicate of ~791-831) | `DONE` | Stream A | `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py` — Deleted duplicate investor arbitrage block |
| A5 | Add opt-out message detection in webhook handler | `DONE` | Stream A | `ghl_real_estate_ai/api/routes/webhook.py` — Added OPT_OUT_PHRASES check before Jorge seller mode, applies AI-Off tag |
| A6 | Add initiate-qualification endpoint | `DONE` | Stream A | `ghl_real_estate_ai/api/routes/webhook.py` — Added POST /api/ghl/initiate-qualification endpoint |
| A7 | Verify tone engine strips emojis, hyphens, enforces 160 char | `DONE` | Stream A | `ghl_real_estate_ai/services/jorge/jorge_tone_engine.py` — Verified: all 5 checks pass, no changes needed |

### A1: Remove "Hit List" from activation_tags

**File**: `ghl_real_estate_ai/ghl_utils/config.py`
**Line**: 136
**Current**: `activation_tags: list[str] = ["Hit List", "Need to Qualify", "Needs Qualifying"]`
**Target**: `activation_tags: list[str] = ["Needs Qualifying"]`
**Also**: Line 140 — change `bot_active_disposition: str = "Hit List"` → `"Needs Qualifying"`

Jorge said: "I do NOT want the 'hit list' being part of the triggers/tags."

### A2: Add JORGE_SIMPLE_MODE config flag

**File**: `ghl_real_estate_ai/ghl_utils/jorge_config.py`
**Add to JorgeSellerConfig class**:
```python
# Simple mode: disables enterprise features (investor arbitrage, loss aversion,
# psychology profiling, Voss negotiation, drift detection, market insights)
# When True, bot follows strict 4-question flow only
JORGE_SIMPLE_MODE: bool = True
```

### A3: Gate enterprise branches in seller engine

**File**: `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py`
**Method**: `_generate_seller_response` (line 615+)

When `self.config.JORGE_SIMPLE_MODE is True`, the response should ONLY follow these paths:
1. `temperature == "hot"` → handoff message
2. `questions_answered < 4` → next qualification question (or confrontational follow-up if vague)
3. `vague_streak >= 2` → take-away close
4. All 4 answered but not hot → warm/cold classification + appropriate message

Skip these enterprise paths entirely when JORGE_SIMPLE_MODE:
- Loss aversion / cost of waiting (line ~663)
- Negotiation drift / Voss closure (line ~683)
- Drift softening / ROI proforma (line ~703)
- Net yield justification (line ~725)
- Investor arbitrage pitch (lines ~791, ~860)
- Market-aware insight injection (line ~833)

**Implementation**: Add early guard at top of method:
```python
if self.config.JORGE_SIMPLE_MODE:
    return await self._generate_simple_response(seller_data, temperature, contact_id)
```
Create `_generate_simple_response` with ONLY the 4 paths listed above.

### A4: Remove duplicate arbitrage code

**File**: `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py`
Lines ~860-900 are an exact duplicate of lines ~791-831 (investor arbitrage pitch).
Remove the second occurrence entirely.

### A5: Add opt-out message detection

**File**: `ghl_real_estate_ai/api/routes/webhook.py`
**Insert BEFORE** the Jorge seller mode check (before line 158).

```python
# Opt-out detection (Jorge spec: "end automation immediately")
OPT_OUT_PHRASES = [
    "stop", "unsubscribe", "don't contact", "dont contact",
    "remove me", "not interested", "no more", "opt out",
    "leave me alone", "take me off", "no thanks"
]
msg_lower = user_message.lower().strip()
if any(phrase in msg_lower for phrase in OPT_OUT_PHRASES):
    logger.info(f"Opt-out detected for contact {contact_id}")
    # Apply deactivation tag
    background_tasks.add_task(ghl_client_default.add_tags, contact_id, ["AI-Off"])
    return GHLWebhookResponse(
        success=True,
        message="No problem at all, reach out whenever you're ready",
        actions=[GHLAction(type=ActionType.ADD_TAG, tag="AI-Off")],
    )
```

### A6: Add initiate-qualification endpoint

**File**: `ghl_real_estate_ai/api/routes/webhook.py`
Add new endpoint:

```python
@router.post("/initiate-qualification")
async def initiate_qualification(contact_id: str, location_id: str, background_tasks: BackgroundTasks):
    """
    Called by GHL workflow when 'Needs Qualifying' tag is applied.
    Sends initial outreach message to start qualification.
    """
    # 1. Fetch contact info from GHL
    contact = await ghl_client_default.get_contact(contact_id)
    first_name = contact.get("firstName", "there")

    # 2. Generate opening message
    opening = f"Hey {first_name}, saw your property inquiry. Are you still thinking about selling?"

    # 3. Return as response for GHL to send
    return GHLWebhookResponse(
        success=True,
        message=opening,
        actions=[],
    )
```

### A7: Verify tone engine

**File**: `ghl_real_estate_ai/services/jorge/jorge_tone_engine.py`
Read and verify:
- `_remove_emojis()` method exists and works
- `_ensure_sms_compliance()` strips hyphens and enforces 160 char
- `_remove_softening_language()` catches all AI-sounding words
- `_apply_confrontational_tone()` makes messages direct
No changes expected unless gaps found.

---

## Stream B: Buyer Bot & Lead Bot

| ID | Task | Status | Owner | Files |
|----|------|--------|-------|-------|
| B1 | Verify buyer bot imports and instantiation | `DONE` | — | `ghl_real_estate_ai/agents/jorge_buyer_bot.py` |
| B2 | Test buyer bot 6-node workflow end-to-end | `DONE` | Stream B | `tests/test_buyer_bot_e2e.py` — E2E test with mocked deps validates 6-node workflow processes buyer conversation, matches properties, generates response |
| B3 | Add Rancho Cucamonga sample property data | `DONE` | Stream A | `ghl_real_estate_ai/data/sample_properties.json` — 13 properties: 5 entry ($549-685k), 5 mid ($749k-1.1M), 3 luxury ($1.35-1.95M) across 7 neighborhoods |
| B4 | Wire PropertyMatcher to sample data | `DONE` | Stream A | `ghl_real_estate_ai/services/property_matcher.py` — _load_sample_data() fallback already wired to sample_properties.json |
| B5 | Add buyer follow-up sequence config | `DONE` | Stream A | `ghl_real_estate_ai/ghl_utils/jorge_config.py` — Added BUYER_FOLLOWUP_SCHEDULE, BUYER_LONGTERM_INTERVAL, BUYER_TEMPERATURE_TAGS |
| B6 | Verify lead bot intent routing | `DONE` | Stream A | `ghl_real_estate_ai/agents/lead_bot.py` — Verified: detect_lead_type() uses buyer/seller keyword scoring, routing via FRS classification works |

### B3: Sample Property Data

Create `ghl_real_estate_ai/data/sample_properties.json` with 10-15 Rancho Cucamonga listings:
```json
[
  {
    "id": "prop_001",
    "address": "1234 Victoria Park Ln, Rancho Cucamonga, CA 91730",
    "price": 650000,
    "beds": 4,
    "baths": 3,
    "sqft": 2200,
    "condition": "Move-in Ready",
    "neighborhood": "Victoria",
    "description": "Updated 4bd/3ba in Victoria neighborhood, close to schools"
  }
]
```

Price ranges per JORGE_SPEC.md:
- Entry-level: $500-700k (5 properties)
- Mid-market: $700k-1.2M (5 properties)
- Luxury: $1.2M+ (3 properties)

Neighborhoods: Victoria, Haven, Etiwanda, Terra Vista, Central Park

### B5: Buyer Follow-Up Config

Add to `JorgeSellerConfig` (or create `JorgeBuyerConfig`):
```python
# Buyer follow-up schedule (mirrors seller pattern)
BUYER_FOLLOWUP_SCHEDULE = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29]
BUYER_LONGTERM_INTERVAL = 14
BUYER_FOLLOWUP_CONTENT = "property_updates"  # Send new matching listings
```

---

## Stream C: Dashboard

| ID | Task | Status | Owner | Files |
|----|------|--------|-------|-------|
| C1 | Create jorge_delivery_dashboard.py | `DONE` | Stream C | Created 306-line dashboard with 4 tabs, sample data fallback, Plotly charts |
| C2 | Implement Tab 1: Lead Pipeline | `DONE` | Stream C | Funnel chart, stage metrics, conversion rates |
| C3 | Implement Tab 2: Bot Activity | `DONE` | Stream C | Recent conversations table, messages/response time/status metrics |
| C4 | Implement Tab 3: Temperature Map | `DONE` | Stream C | Donut chart, 30-day trend line, hot leads action table |
| C5 | Implement Tab 4: Follow-Up Queue | `DONE` | Stream C | Upcoming/overdue tables, completion rate metric |
| C6 | Wire to real data services | `DONE` | Stream C | AnalyticsService + ConversationManager imports with graceful fallback |

See JORGE_SPEC.md Section 5 for exact dashboard requirements.

---

## Stream D: Testing & Packaging

| ID | Task | Status | Owner | Files |
|----|------|--------|-------|-------|
| D1 | Create seller bot E2E test | `DONE` | Stream D | `tests/test_jorge_delivery.py` — TestSellerQualificationFlow: 3 tests (hot flow E2E, question sequence, SMS compliance) |
| D2 | Create opt-out test | `DONE` | Stream D | Same file — TestOptOutHandling: 3 tests (all variants, AI-Off tag, exit message) |
| D3 | Create edge case tests | `DONE` | Stream D | Same file — TestEdgeCases: 5 tests (vague, multi-answer, no response, off-topic, question tracking) |
| D4 | Test tone output for human quality | `DONE` | Stream D | Same file — TestToneCompliance: 8 tests (emoji, hyphen, length, AI phrases, style, SMS strip, truncation) |
| D5 | Write JORGE_DEPLOYMENT_GUIDE.md | `DONE` | Stream D | `JORGE_DEPLOYMENT_GUIDE.md` — 9-step guide: prerequisites, env vars, GHL webhook, workflow, tags, custom fields, testing, dashboard, troubleshooting |
| D6 | Verify all tests pass | `DONE` | Stream D | 19/19 tests pass in tests/test_jorge_delivery.py |

### D1-D4: Test Structure

```python
# tests/test_jorge_delivery.py
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestSellerQualificationFlow:
    """E2E: 5-message conversation → Hot seller"""

class TestOptOutHandling:
    """Opt-out keywords → AI-Off tag + exit message"""

class TestEdgeCases:
    """Vague answers, multi-answer, no response, off-topic"""

class TestToneCompliance:
    """No emojis, no hyphens, <160 chars, no AI-sounding phrases"""
```

### D5: Deployment Guide Structure

```markdown
# Jorge AI Bot — Setup Guide

## Step 1: Environment Variables
## Step 2: GHL Webhook Configuration
## Step 3: GHL Workflow Setup (Tag → Initiate Qualification)
## Step 4: Required GHL Tags to Create
## Step 5: Test the Bot
## Step 6: Dashboard Access
## Troubleshooting
```

---

## Dependencies

```
Stream A (tasks A1-A7) ─── no dependencies, start immediately
Stream B (tasks B1-B6) ─── no dependencies, start immediately
Stream C (tasks C1-C6) ─── no dependencies, start immediately
Stream D (tasks D1-D4) ─── blocked by Streams A + B completion
Stream D (task D5-D6)  ─── blocked by all other streams
```
