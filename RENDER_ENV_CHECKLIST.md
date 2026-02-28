# Render Environment Variables Checklist — Jorge 3-Bot Production

**Service**: `jorge-realty-ai` (see `ghl_real_estate_ai/render.yaml`)
**Stack**: Python 3.11 / FastAPI / PostgreSQL / Redis / GoHighLevel / Claude AI
**Last audited**: 2026-02-27

> **How to set variables**: Render Dashboard → jorge-realty-ai → Environment → Add Environment Variable
>
> Variables marked `sync: false` in render.yaml must be set manually — Render never auto-populates them.
> Variables with a hardcoded `value:` are already baked into render.yaml and deploy automatically.

---

## Config Gap: `LEAD_ACTIVATION_TAG`

`render.yaml` currently ships with:

```yaml
- key: LEAD_ACTIVATION_TAG
  value: "lead-bot"
```

The `.env` template, `DEPLOYMENT_CHECKLIST.md`, activation tag table, and smoke-test procedure all specify `Needs Qualifying`. The value `lead-bot` is a mismatched placeholder that would prevent the lead bot from activating on contacts coming from GHL workflows.

**Fix**: In the Render dashboard change `LEAD_ACTIVATION_TAG` to `Needs Qualifying`. Also update `render.yaml` line 86 from `"lead-bot"` to `"Needs Qualifying"` before next deploy.

---

## CRITICAL — Bots fail completely without these

| Variable | Description | Where to get it | Set in render.yaml? |
|----------|-------------|-----------------|---------------------|
| `ANTHROPIC_API_KEY` | Claude AI — all bot responses | console.anthropic.com | `sync: false` — set manually |
| `GHL_API_KEY` | GHL CRM read/write | GHL → Settings → API | `sync: false` — set manually |
| `GHL_LOCATION_ID` | GHL location/sub-account | GHL URL when logged into sub-account | `sync: false` — set manually |
| `LOCATION_ID` | Duplicate of above — some services reference this key | Same as GHL_LOCATION_ID | `sync: false` — set manually |
| `GHL_WEBHOOK_SECRET` | Validates inbound GHL webhook signatures | Generate: `openssl rand -hex 32` | `sync: false` — set manually |
| `JWT_SECRET_KEY` | Signs internal JWT tokens | Generate: `openssl rand -hex 32` | `sync: false` — set manually |
| `DATABASE_URL` | PostgreSQL connection string | Auto-injected by Render from `jorge-realty-db` | Auto via `fromDatabase` |
| `REDIS_URL` | Redis connection string | Auto-injected by Render from `jorge-realty-redis` | Auto via `fromService` |

---

## HIGH — Bots work but miss key features without these

### Bot Mode Flags

| Variable | Required Value | Description | Set in render.yaml? |
|----------|---------------|-------------|---------------------|
| `JORGE_SELLER_MODE` | `true` | Enable seller qualification routing | `value: "true"` — already set |
| `JORGE_BUYER_MODE` | `true` | Enable buyer qualification routing | `value: "true"` — already set |
| `JORGE_LEAD_MODE` | `true` | Enable lead qualification routing | `value: "true"` — already set |
| `ENVIRONMENT` | `production` | Affects security validation, CORS, debug modes | `value: production` — already set |

### Tag Routing (CRITICAL for correct bot activation)

| Variable | Required Value | Description | Set in render.yaml? |
|----------|---------------|-------------|---------------------|
| `LEAD_ACTIVATION_TAG` | `Needs Qualifying` | Tag that routes contacts to lead bot | **BUG: currently `lead-bot` — fix manually** |
| `BUYER_LEAD_TAG` | `Buyer-Lead` | Tag that routes contacts to buyer bot | `value: "Buyer-Lead"` — already set |

### GHL Workflow IDs

All four bots will respond and qualify leads, but will not trigger any follow-up sequences or agent notifications without these.

| Variable | Description | Where to get it | Set in render.yaml? |
|----------|-------------|-----------------|---------------------|
| `HOT_SELLER_WORKFLOW_ID` | Triggers agent notification + handoff for hot sellers | GHL → Automation → Workflows → copy ID | `sync: false` — set manually |
| `WARM_SELLER_WORKFLOW_ID` | Triggers nurture sequence for warm sellers | GHL → Automation → Workflows → copy ID | `sync: false` — set manually |
| `HOT_BUYER_WORKFLOW_ID` | "Jorge — Bot Activation" workflow — handles Buyer-Lead + Needs Qualifying tag triggers (consolidated Feb 2026) | GHL → Automation → Workflows → copy ID | `sync: false` — set manually |
| `WARM_BUYER_WORKFLOW_ID` | Triggers buyer nurture sequence | GHL → Automation → Workflows → copy ID | `sync: false` — set manually |
| `NOTIFY_AGENT_WORKFLOW_ID` | SMS + email to agent for any qualified lead | GHL → Automation → Workflows → copy ID | `sync: false` — set manually |
| `MANUAL_SCHEDULING_WORKFLOW_ID` | Fallback when auto calendar booking fails | GHL → Automation → Workflows → copy ID | Not in render.yaml — add manually |

### Calendar & Appointment Booking

Without `JORGE_CALENDAR_ID`, HOT sellers get a fallback message asking for morning/afternoon preference instead of real slot selection.

| Variable | Description | Where to get it | Set in render.yaml? |
|----------|-------------|-----------------|---------------------|
| `JORGE_CALENDAR_ID` | GHL calendar ID for HOT seller booking | GHL → Calendars → copy calendar ID | `sync: false` — set manually |
| `GHL_CALENDAR_ID` | Alias used by some GHL client methods | Same value as JORGE_CALENDAR_ID | `sync: false` — set manually |
| `JORGE_USER_ID` | Jorge's GHL user ID — appointment ownership | GHL → Settings → Team → copy user ID | `sync: false` — set manually |

### GHL Custom Field IDs — Lead Bot

Without these, leads are qualified but scores are not written back to GHL.

| Variable | GHL Field Type | Description | Set in render.yaml? |
|----------|---------------|-------------|---------------------|
| `CUSTOM_FIELD_LEAD_SCORE` | number | Overall lead score 0-100 **[REQUIRED by validation script]** | `sync: false` — set manually |
| `CUSTOM_FIELD_LOCATION` | text | Lead's location/area | `sync: false` — set manually |
| `CUSTOM_FIELD_TIMELINE` | dropdown | Purchase/sale timeline | `sync: false` — set manually |

### GHL Custom Field IDs — Seller Bot

| Variable | GHL Field Type | Description | Set in render.yaml? |
|----------|---------------|-------------|---------------------|
| `CUSTOM_FIELD_SELLER_TEMPERATURE` | dropdown | Hot/Warm/Cold **[REQUIRED by validation script]** | `sync: false` — set manually |
| `CUSTOM_FIELD_TIMELINE_URGENCY` | dropdown | Urgency level **[REQUIRED by validation script]** | `sync: false` — set manually |
| `CUSTOM_FIELD_SELLER_MOTIVATION` | text | Seller motivation notes | `sync: false` — set manually |
| `CUSTOM_FIELD_PROPERTY_CONDITION` | dropdown | Property condition | `sync: false` — set manually |
| `CUSTOM_FIELD_PRICE_EXPECTATION` | currency | Expected sale price | `sync: false` — set manually |
| `CUSTOM_FIELD_QUESTIONS_ANSWERED` | number | Number of qualification questions answered | `sync: false` — set manually |
| `CUSTOM_FIELD_QUALIFICATION_SCORE` | number | Qualification score | `sync: false` — set manually |
| `CUSTOM_FIELD_PROPERTY_ADDRESS` | text | Property address | `sync: false` — set manually |
| `CUSTOM_FIELD_QUALIFICATION_COMPLETE` | boolean | Qualification finished flag | `sync: false` — set manually |
| `CUSTOM_FIELD_PROPERTY_TYPE` | dropdown | SFR/Condo/Townhouse | `sync: false` — set manually |
| `CUSTOM_FIELD_LAST_BOT_INTERACTION` | datetime | Timestamp of last bot message | `sync: false` — set manually |

### GHL Custom Field IDs — Buyer Bot

| Variable | GHL Field Type | Description | Set in render.yaml? |
|----------|---------------|-------------|---------------------|
| `CUSTOM_FIELD_BUYER_TEMPERATURE` | dropdown | Hot/Warm/Cold buyer **[REQUIRED by validation script]** | `sync: false` — set manually |
| `CUSTOM_FIELD_BUDGET` | currency | Buyer's budget range **[REQUIRED by validation script]** | `sync: false` — set manually |
| `CUSTOM_FIELD_PRE_APPROVAL_STATUS` | dropdown | Pre-approval status | `sync: false` — set manually |
| `CUSTOM_FIELD_PROPERTY_PREFERENCES` | text | Desired features | `sync: false` — set manually |

### Jorge Handoff Custom Field IDs

These power cross-bot context preservation and intent scoring. Without them handoffs work but context is lost between bots.

| Variable | GHL Field Type | Description | Set in render.yaml? |
|----------|---------------|-------------|---------------------|
| `GHL_CUSTOM_FIELD_FRS` | number | Financial Readiness Score 0-100 **[REQUIRED]** | `sync: false` — set manually |
| `GHL_CUSTOM_FIELD_PCS` | number | Psychological Commitment Score 0-100 **[REQUIRED]** | `sync: false` — set manually |
| `GHL_CUSTOM_FIELD_BUYER_INTENT` | number | Buyer intent confidence 0.0-1.0 **[REQUIRED]** | `sync: false` — set manually |
| `GHL_CUSTOM_FIELD_SELLER_INTENT` | number | Seller intent confidence 0.0-1.0 **[REQUIRED]** | `sync: false` — set manually |
| `GHL_CUSTOM_FIELD_TEMPERATURE` | dropdown | Hot/Warm/Cold classification **[REQUIRED]** | `sync: false` — set manually |
| `GHL_CUSTOM_FIELD_LAST_BOT` | text | Last handling bot name **[REQUIRED]** | `sync: false` — set manually |
| `GHL_CUSTOM_FIELD_HANDOFF_HISTORY` | text/JSON | JSON handoff event log | `sync: false` — set manually |
| `GHL_CUSTOM_FIELD_CONVERSATION_CONTEXT` | text/JSON | JSON context preserved across handoffs | `sync: false` — set manually |

---

## OPTIONAL — Nice to have, bots work without these

### GHL Setup

| Variable | Description | Notes |
|----------|-------------|-------|
| `GHL_AGENCY_API_KEY` | Agency-level API access | Only if managing multiple sub-accounts |
| `GHL_AGENCY_ID` | Agency ID | Only if using agency-level features |

### Additional Seller Fields

| Variable | Description |
|----------|-------------|
| `CUSTOM_FIELD_RELOCATION_DESTINATION` | Where seller is moving |
| `CUSTOM_FIELD_EXPECTED_ROI` | Expected ROI (analytics) |
| `CUSTOM_FIELD_LEAD_VALUE_TIER` | Lead value tier |
| `CUSTOM_FIELD_AI_VALUATION_PRICE` | AI property valuation |
| `CUSTOM_FIELD_DETECTED_PERSONA` | Persona type |
| `CUSTOM_FIELD_PSYCHOLOGY_TYPE` | Psychological profile |
| `CUSTOM_FIELD_URGENCY_LEVEL` | Urgency classification |
| `CUSTOM_FIELD_MORTGAGE_BALANCE` | Mortgage balance |
| `CUSTOM_FIELD_REPAIR_ESTIMATE` | Repair cost estimate |
| `CUSTOM_FIELD_LISTING_HISTORY` | Prior listings |
| `CUSTOM_FIELD_DECISION_MAKER_CONFIRMED` | Is this the decision maker? |
| `CUSTOM_FIELD_PREFERRED_CONTACT_METHOD` | SMS/Call/Email |
| `CUSTOM_FIELD_PCS_SCORE` | Property condition score |
| `CUSTOM_FIELD_SELLER_LIENS` | Seller liens/encumbrances |
| `CUSTOM_FIELD_SELLER_REPAIRS` | Needed repairs |
| `CUSTOM_FIELD_SELLER_LISTING_HISTORY` | Previous listing history |
| `CUSTOM_FIELD_SELLER_DECISION_MAKER` | Decision maker status |

### Appointment Custom Fields

| Variable | Description |
|----------|-------------|
| `CUSTOM_FIELD_APPOINTMENT_TIME` | Scheduled appointment time |
| `CUSTOM_FIELD_APPOINTMENT_TYPE` | Type of appointment |

### Alerting & Monitoring

| Variable | Default | Description |
|----------|---------|-------------|
| `JORGE_DIGEST_EMAIL` | (empty) | Email address for daily 7am performance digest |
| `ALERT_SLACK_ENABLED` | `false` | Enable Slack alert channel |
| `ALERT_SLACK_WEBHOOK_URL` | (empty) | Slack incoming webhook URL |
| `ALERT_SLACK_CHANNEL` | `#jorge-alerts` | Slack channel name |
| `ALERT_EMAIL_ENABLED` | `false` | Enable email alert channel |
| `ALERT_EMAIL_SMTP_HOST` | `smtp.gmail.com` | SMTP server |
| `ALERT_EMAIL_SMTP_USER` | (empty) | SMTP username |
| `ALERT_EMAIL_SMTP_PASSWORD` | (empty) | SMTP app password |
| `ALERT_EMAIL_TO` | (empty) | Recipient email(s) |

### MLS / Property Data

| Variable | Description |
|----------|-------------|
| `ATTOM_API_KEY` | Attom Data API for property valuations and comps |
| `MLS_RETS_URL` | MLS RETS feed URL |
| `MLS_RETS_USERNAME` | MLS RETS username |
| `MLS_RETS_PASSWORD` | MLS RETS password |
| `ENABLE_MLS_INTEGRATION` | Set `true` to activate real MLS/Attom lookups |

### AI Providers (Additional)

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` / `GEMINI_API_KEY` | Gemini AI (secondary provider) |
| `PERPLEXITY_API_KEY` | Market research queries |
| `OPENROUTER_API_KEY` | Unified LLM access with auto-fallback |

### Optimization Flags (already defaulted in .env)

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_CONVERSATION_OPTIMIZATION` | `true` | Phase 1-2 token optimizations |
| `ENABLE_ENHANCED_CACHING` | `true` | L1/L2/L3 cache layers |
| `ENABLE_SEMANTIC_RESPONSE_CACHING` | `true` | Semantic similarity cache |
| `SEMANTIC_CACHE_SIMILARITY_THRESHOLD` | `0.85` | Cosine similarity threshold |

---

## Gaps Found in render.yaml vs Full Feature Set

The following vars are referenced in `DEPLOYMENT_CHECKLIST.md` and `.env` but are **not present in `ghl_real_estate_ai/render.yaml`** and must be added manually in the Render dashboard:

| Missing Var | Priority | Impact if absent |
|-------------|----------|-----------------|
| `LEAD_ACTIVATION_TAG` | **CRITICAL (BUG)** | Lead bot never activates — currently set to `lead-bot` instead of `Needs Qualifying` |
| `MANUAL_SCHEDULING_WORKFLOW_ID` | HIGH | Calendar booking failure has no fallback workflow |
| `CUSTOM_FIELD_SELLER_MOTIVATION` | HIGH | Seller motivation not written to GHL |
| `CUSTOM_FIELD_PCS_SCORE` | HIGH | PCS score not persisted to GHL |
| `CUSTOM_FIELD_SELLER_LIENS` | HIGH | Liens field not written to GHL |
| `CUSTOM_FIELD_SELLER_REPAIRS` | HIGH | Repairs field not written to GHL |
| `CUSTOM_FIELD_SELLER_LISTING_HISTORY` | HIGH | Listing history not written to GHL |
| `CUSTOM_FIELD_SELLER_DECISION_MAKER` | HIGH | Decision maker flag not written to GHL |
| `CUSTOM_FIELD_APPOINTMENT_TIME` | MEDIUM | Appointment time not persisted to GHL field |
| `CUSTOM_FIELD_APPOINTMENT_TYPE` | MEDIUM | Appointment type not persisted to GHL field |
| `JORGE_DIGEST_EMAIL` | OPTIONAL | No daily performance digest emails |

---

## GHL Validation Script

After setting all variables, run the built-in validation to confirm all fields resolve:

```bash
python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup
```

- `[OK]` — field configured and resolves in GHL
- `[!!]` — missing CRITICAL field (block go-live)
- `[--]` — missing optional field (bot still works)

Required `[OK]` before going live:
- `CUSTOM_FIELD_SELLER_TEMPERATURE`
- `CUSTOM_FIELD_TIMELINE_URGENCY`
- `CUSTOM_FIELD_BUYER_TEMPERATURE`
- `CUSTOM_FIELD_BUDGET`
- `CUSTOM_FIELD_LEAD_SCORE`
- `HOT_SELLER_WORKFLOW_ID`
- `HOT_BUYER_WORKFLOW_ID`
- `NOTIFY_AGENT_WORKFLOW_ID`
