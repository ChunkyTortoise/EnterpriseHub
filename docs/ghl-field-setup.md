# GHL Field Setup Guide

> **Last Updated**: 2026-02-18
> **Applies To**: Jorge Lead/Buyer/Seller bots, EnterpriseHub CRM integration

This guide walks through configuring all GoHighLevel custom fields, workflows,
and calendar IDs required by the Jorge bot system.

---

## Prerequisites

- GoHighLevel sub-account with **API v2 access**
- Location ID (find at **Settings > Business Profile**)
- API Key / JWT (find at **Settings > Business Profile > API Keys**)
- A `.env` file in the project root (copy from `.env.example` if needed)

---

## Step 1: Add API Credentials to .env

```bash
# Required -- without these, no GHL integration works
GHL_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your-jwt-token
GHL_LOCATION_ID=your-location-id-here
GHL_WEBHOOK_SECRET=your-webhook-secret-32-chars-minimum
```

**Where to find these values:**

| Variable | Location in GHL Dashboard |
|----------|--------------------------|
| `GHL_API_KEY` | Settings > Business Profile > API Keys > Generate |
| `GHL_LOCATION_ID` | Settings > Business Profile (shown at top) |
| `GHL_WEBHOOK_SECRET` | Settings > API > Webhook Secret (or generate one) |

---

## Step 2: Run Field Audit

The field mapper scans your `.env` file and reports which GHL fields are
configured, missing (required), or missing (optional).

```bash
python -m ghl_real_estate_ai.ghl_utils.env_field_mapper
```

Or using Make:

```bash
make ghl-setup
```

This prints a color-coded report grouped by category (API, Contact Fields,
Workflows, Calendars).

---

## Step 3: Create Missing Custom Fields

### Option A: Automated (recommended)

If your API key is set, the setup tool can create missing Jorge-specific fields
in GHL automatically:

```bash
python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup --action=create
```

This creates the 8 Jorge bot custom fields (FRS, PCS, buyer/seller intent,
temperature, handoff history, last bot, conversation context) and prints
field IDs to copy into `.env`.

### Option B: Manual via GHL Dashboard

1. Go to **Settings > Custom Fields** in GHL
2. For each missing field listed in the audit, click **Add Field**
3. Use the data type shown in the audit report (NUMERICAL, SINGLE_LINE, etc.)
4. After creation, copy the field ID (UUID shown in the URL or field settings)

---

## Step 4: Get Field IDs

List all existing custom fields in your GHL location:

```bash
python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup --action=list
```

This displays a table of field names, IDs, and types, plus a `.env`-ready
copy-paste block.

---

## Step 5: Configure Workflows

Create these workflows in **GHL > Automation > Workflows**:

| Env Var | Purpose | Trigger |
|---------|---------|---------|
| `HOT_SELLER_WORKFLOW_ID` | Agent notification for hot sellers | Contact tagged "Hot-Lead" + seller context |
| `WARM_SELLER_WORKFLOW_ID` | Nurture sequence for warm sellers | Contact tagged "Warm-Lead" + seller context |
| `HOT_BUYER_WORKFLOW_ID` | Showing coordination for hot buyers | Contact tagged "Hot-Lead" + buyer context |
| `WARM_BUYER_WORKFLOW_ID` | Buyer nurture sequence | Contact tagged "Warm-Lead" + buyer context |
| `NOTIFY_AGENT_WORKFLOW_ID` | SMS/email to agent for qualified leads | Any Hot or high-FRS lead |

After creating each workflow, copy its ID from the URL:
`https://app.gohighlevel.com/.../workflows/<WORKFLOW_ID>`

---

## Step 6: Configure Calendars

| Env Var | Purpose |
|---------|---------|
| `GHL_CALENDAR_ID` | General appointment calendar |
| `JORGE_CALENDAR_ID` | HOT seller auto-booking calendar |

Find calendar IDs at **GHL > Calendars > (select calendar) > Copy Calendar ID**.

> **Note**: If `JORGE_CALENDAR_ID` is not set, HOT sellers receive a fallback
> message asking for morning/afternoon preference instead of auto-booking.

---

## Step 7: Update .env

Copy each field ID, workflow ID, and calendar ID into your `.env` file.
See the [Field Reference Table](#field-reference-table) below for the complete
list of variables.

---

## Step 8: Verify

Run the check-only mode to confirm all required fields are set:

```bash
python -m ghl_real_estate_ai.ghl_utils.env_field_mapper --check-only
```

Or:

```bash
make ghl-setup-check
```

Exit code `0` means all required fields are configured. Exit code `1` means
required fields are missing.

For a full end-to-end integration test (creates/deletes a test contact):

```bash
python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup --action=test
```

---

## Field Reference Table

### API Credentials

| Env Var | Required | Description |
|---------|----------|-------------|
| `GHL_API_KEY` | Yes | GoHighLevel API key (v2 JWT) |
| `GHL_LOCATION_ID` | Yes | GHL sub-account / location ID |
| `GHL_WEBHOOK_SECRET` | Yes | Webhook signature verification secret |

### Seller Custom Fields (23)

| Env Var | GHL Type | Required | Description |
|---------|----------|----------|-------------|
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

### Buyer Custom Fields (4)

| Env Var | GHL Type | Required | Description |
|---------|----------|----------|-------------|
| `CUSTOM_FIELD_BUYER_TEMPERATURE` | dropdown | Yes | Hot/Warm/Cold buyer classification |
| `CUSTOM_FIELD_PRE_APPROVAL_STATUS` | dropdown | No | Mortgage pre-approval status |
| `CUSTOM_FIELD_PROPERTY_PREFERENCES` | text | No | Desired property features |
| `CUSTOM_FIELD_BUDGET` | currency | Yes | Buyer's budget range |

### Lead Custom Fields (3)

| Env Var | GHL Type | Required | Description |
|---------|----------|----------|-------------|
| `CUSTOM_FIELD_LEAD_SCORE` | number | Yes | Overall lead score (0-100) |
| `CUSTOM_FIELD_LOCATION` | text | No | Lead's location / area |
| `CUSTOM_FIELD_TIMELINE` | dropdown | No | Purchase/sale timeline |

### Jorge Bot Custom Fields (8)

| Env Var | GHL Type | Required | Description |
|---------|----------|----------|-------------|
| `GHL_CUSTOM_FIELD_FRS` | NUMERICAL | Yes | Financial Readiness Score (0-100) |
| `GHL_CUSTOM_FIELD_PCS` | NUMERICAL | Yes | Psychological Commitment Score (0-100) |
| `GHL_CUSTOM_FIELD_BUYER_INTENT` | NUMERICAL | Yes | Buyer intent confidence (0.0-1.0) |
| `GHL_CUSTOM_FIELD_SELLER_INTENT` | NUMERICAL | Yes | Seller intent confidence (0.0-1.0) |
| `GHL_CUSTOM_FIELD_TEMPERATURE` | SINGLE_LINE | Yes | Hot/Warm/Cold lead classification |
| `GHL_CUSTOM_FIELD_HANDOFF_HISTORY` | LARGE_TEXT | No | JSON log of cross-bot handoff events |
| `GHL_CUSTOM_FIELD_LAST_BOT` | SINGLE_LINE | Yes | Which bot last handled this contact |
| `GHL_CUSTOM_FIELD_CONVERSATION_CONTEXT` | LARGE_TEXT | No | JSON context passed during handoffs |

### Workflow IDs (5)

| Env Var | Required | Description |
|---------|----------|-------------|
| `HOT_SELLER_WORKFLOW_ID` | Yes | Triggered when seller scores Hot |
| `WARM_SELLER_WORKFLOW_ID` | No | Nurture sequence for Warm sellers |
| `NOTIFY_AGENT_WORKFLOW_ID` | Yes | Sends SMS/email to agent for qualified leads |
| `HOT_BUYER_WORKFLOW_ID` | Yes | Triggered when buyer scores Hot |
| `WARM_BUYER_WORKFLOW_ID` | No | Nurture sequence for Warm buyers |

### Calendar IDs (2)

| Env Var | Required | Description |
|---------|----------|-------------|
| `GHL_CALENDAR_ID` | No | General appointment calendar |
| `JORGE_CALENDAR_ID` | No | HOT seller auto-booking calendar |

---

## Temperature Tag Mapping

| Lead Score | Tag | Workflow Trigger | Actions |
|------------|-----|-----------------|---------|
| >= 80 | `Hot-Lead` | `HOT_SELLER_WORKFLOW_ID` / `HOT_BUYER_WORKFLOW_ID` | Priority notification, agent alert |
| 40-79 | `Warm-Lead` | `WARM_SELLER_WORKFLOW_ID` / `WARM_BUYER_WORKFLOW_ID` | Nurture sequence |
| < 40 | `Cold-Lead` | None | Educational content, periodic check-in |

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Invalid JWT` | API key expired or invalid | Regenerate key in GHL dashboard |
| `GHL_API_KEY and GHL_LOCATION_ID must be set` | Missing .env values | Copy from `.env.example` and fill in |
| `INVALID (not found in GHL)` during validate | Field ID in .env does not match GHL | Run `--action=list` to get correct IDs |
| `Create test contact` fails | API permissions insufficient | Check API key has contact write access |
| Fields created but validation fails | `.env` not updated after create | Copy field IDs from create output to `.env` |

---

## Related Documentation

- `ghl_real_estate_ai/docs/GHL_FIELD_REFERENCE.md` -- Full field reference with GHL types
- `ghl_real_estate_ai/ghl_utils/jorge_ghl_setup.py` -- CLI tool for GHL field management
- `ghl_real_estate_ai/ghl_utils/env_field_mapper.py` -- Environment variable auditor
- `ghl_real_estate_ai/agents/DEPLOYMENT_CHECKLIST.md` -- Full deployment guide
