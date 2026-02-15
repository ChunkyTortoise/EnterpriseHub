> **Status**: Tooling ready, setup deferred (2026-02-15)
> **Reason**: GHL access revoked - cannot obtain API key
> **Tooling**: Enhanced jorge_ghl_setup.py committed (93c68ce)
> **Next steps**: Resume when GHL access restored (~30 min to complete)

---

# GHL Custom Field Reference - Jorge Bots

**Last Updated**: 2026-02-15
**Location**: Jorge's Rancho Cucamonga Real Estate

---

## Quick Start

```bash
# List all custom fields in GHL
python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup --action=list

# Create missing Jorge fields
python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup --action=create

# Validate all field IDs in .env
python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup --action=validate

# Run end-to-end integration test
python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup --action=test

# Validate env var presence only (default)
python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup
```

---

## Jorge Bot Custom Fields

These fields are created and managed by the `--action=create` command.

| Env Var | GHL Display Name | Data Type | Bot | Critical | Purpose |
|---------|-----------------|-----------|-----|----------|---------|
| `GHL_CUSTOM_FIELD_FRS` | Financial Readiness Score | NUMERICAL | Lead | Yes | FRS score (0-100) for lead financial qualification |
| `GHL_CUSTOM_FIELD_PCS` | Psychological Commitment Score | NUMERICAL | Lead | Yes | PCS score (0-100) for buyer/seller commitment |
| `GHL_CUSTOM_FIELD_BUYER_INTENT` | Buyer Intent Confidence | NUMERICAL | Lead | Yes | Buyer intent (0.0-1.0) from intent decoder |
| `GHL_CUSTOM_FIELD_SELLER_INTENT` | Seller Intent Confidence | NUMERICAL | Lead | Yes | Seller intent (0.0-1.0) from intent decoder |
| `GHL_CUSTOM_FIELD_TEMPERATURE` | Lead Temperature | SINGLE_LINE | Lead | Yes | Hot/Warm/Cold lead classification |
| `GHL_CUSTOM_FIELD_HANDOFF_HISTORY` | Handoff History | LARGE_TEXT | Lead | No | JSON log of cross-bot handoff events |
| `GHL_CUSTOM_FIELD_LAST_BOT` | Last Bot Interaction | SINGLE_LINE | Lead | Yes | Which bot last handled this contact (lead/buyer/seller) |
| `GHL_CUSTOM_FIELD_CONVERSATION_CONTEXT` | Conversation Context | LARGE_TEXT | Lead | No | JSON context passed during bot handoffs |

---

## Standard Custom Fields

These fields are validated by the default (no action) mode.

### Seller Bot Fields

| Env Var | GHL Type | Critical | Purpose |
|---------|----------|----------|---------|
| `CUSTOM_FIELD_SELLER_TEMPERATURE` | dropdown | Yes | Hot/Warm/Cold seller classification |
| `CUSTOM_FIELD_SELLER_MOTIVATION` | text | No | Seller motivation notes |
| `CUSTOM_FIELD_RELOCATION_DESTINATION` | text | No | Where seller is relocating |
| `CUSTOM_FIELD_TIMELINE_URGENCY` | dropdown | Yes | Urgency level for selling |
| `CUSTOM_FIELD_PROPERTY_CONDITION` | dropdown | No | Property condition assessment |
| `CUSTOM_FIELD_PRICE_EXPECTATION` | currency | No | Expected sale price |
| `CUSTOM_FIELD_QUESTIONS_ANSWERED` | number | No | Count of qualification questions answered |
| `CUSTOM_FIELD_QUALIFICATION_SCORE` | number | No | Overall qualification score |
| `CUSTOM_FIELD_EXPECTED_ROI` | number | No | Expected return on investment |
| `CUSTOM_FIELD_LEAD_VALUE_TIER` | dropdown | No | Lead value classification |
| `CUSTOM_FIELD_AI_VALUATION_PRICE` | currency | No | AI-generated property valuation |
| `CUSTOM_FIELD_DETECTED_PERSONA` | dropdown | No | Seller persona type |
| `CUSTOM_FIELD_PSYCHOLOGY_TYPE` | text | No | Psychological profile |
| `CUSTOM_FIELD_URGENCY_LEVEL` | dropdown | No | Urgency classification |
| `CUSTOM_FIELD_MORTGAGE_BALANCE` | currency | No | Outstanding mortgage balance |
| `CUSTOM_FIELD_REPAIR_ESTIMATE` | currency | No | Estimated repair costs |
| `CUSTOM_FIELD_LISTING_HISTORY` | text | No | Previous listing details |
| `CUSTOM_FIELD_DECISION_MAKER_CONFIRMED` | boolean | No | Whether decision maker is confirmed |
| `CUSTOM_FIELD_PREFERRED_CONTACT_METHOD` | dropdown | No | SMS/Call/Email preference |
| `CUSTOM_FIELD_PROPERTY_ADDRESS` | text | No | Property street address |
| `CUSTOM_FIELD_PROPERTY_TYPE` | dropdown | No | SFR/Condo/Townhouse/Multi |
| `CUSTOM_FIELD_LAST_BOT_INTERACTION` | datetime | No | Timestamp of last bot message |
| `CUSTOM_FIELD_QUALIFICATION_COMPLETE` | boolean | No | Whether full qualification is done |

### Buyer Bot Fields

| Env Var | GHL Type | Critical | Purpose |
|---------|----------|----------|---------|
| `CUSTOM_FIELD_BUYER_TEMPERATURE` | dropdown | Yes | Hot/Warm/Cold buyer classification |
| `CUSTOM_FIELD_PRE_APPROVAL_STATUS` | dropdown | No | Mortgage pre-approval status |
| `CUSTOM_FIELD_PROPERTY_PREFERENCES` | text | No | Desired property features |
| `CUSTOM_FIELD_BUDGET` | currency | Yes | Buyer's budget range |

### Lead Bot Fields

| Env Var | GHL Type | Critical | Purpose |
|---------|----------|----------|---------|
| `CUSTOM_FIELD_LEAD_SCORE` | number | Yes | Overall lead score (0-100) |
| `CUSTOM_FIELD_LOCATION` | text | No | Lead's location/area |
| `CUSTOM_FIELD_TIMELINE` | dropdown | No | Purchase/sale timeline |

---

## Workflow IDs

| Env Var | Bot | Critical | Purpose |
|---------|-----|----------|---------|
| `HOT_SELLER_WORKFLOW_ID` | Seller | Yes | Triggered when seller scores Hot |
| `WARM_SELLER_WORKFLOW_ID` | Seller | No | Triggered for Warm sellers |
| `NOTIFY_AGENT_WORKFLOW_ID` | General | Yes | Notifies Jorge of important events |
| `HOT_BUYER_WORKFLOW_ID` | Buyer | Yes | Triggered when buyer scores Hot |
| `WARM_BUYER_WORKFLOW_ID` | Buyer | No | Triggered for Warm buyers |

---

## Calendar IDs

| Env Var | Critical | Purpose |
|---------|----------|---------|
| `GHL_CALENDAR_ID` | No | Jorge's appointment calendar for auto-booking |

---

## Temperature Tag Mapping

| Lead Score | Tag | Workflow Trigger | Actions |
|------------|-----|-----------------|---------|
| >= 80 | `Hot-Lead` | `HOT_SELLER_WORKFLOW_ID` / `HOT_BUYER_WORKFLOW_ID` | Priority notification, agent alert |
| 40-79 | `Warm-Lead` | `WARM_SELLER_WORKFLOW_ID` / `WARM_BUYER_WORKFLOW_ID` | Nurture sequence |
| < 40 | `Cold-Lead` | None | Educational content, periodic check-in |

---

## Setup Instructions

### Initial Setup

1. **Ensure credentials are set** in `.env`:
   ```
   GHL_API_KEY=eyJ...  (JWT from GHL Settings > Business Profile > API Keys)
   GHL_LOCATION_ID=xxx  (from GHL Settings > Business Profile)
   ```

2. **List existing fields** to see what's already configured:
   ```bash
   python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup --action=list
   ```

3. **Create missing fields**:
   ```bash
   python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup --action=create
   ```
   Copy the output field IDs into your `.env` file.

4. **Validate the setup**:
   ```bash
   python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup --action=validate
   ```

5. **Run integration test**:
   ```bash
   python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup --action=test
   ```

### Refreshing API Keys

GHL JWT tokens expire periodically. If you get `401 Invalid JWT`:
1. Go to GHL > Settings > Business Profile > API Keys
2. Generate a new key
3. Update `GHL_API_KEY` in `.env`
4. Re-run validation: `--action=validate`

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Invalid JWT` | API key expired or invalid | Regenerate key in GHL dashboard |
| `ERROR: GHL_API_KEY and GHL_LOCATION_ID must be set` | Missing .env values | Copy from .env.example and fill in |
| `INVALID (not found in GHL)` during validate | Field ID in .env doesn't match GHL | Run `--action=list` to get correct IDs |
| `Create test contact` fails | API permissions insufficient | Check API key has contact write access |
| Fields created but validation fails | .env not updated after create | Copy field IDs from create output to .env |
