# Jorge Bot Deployment Checklist

Production deployment guide for Jorge's 3 bots (Seller, Buyer, Lead).
205 passing tests. All bots feature-complete as of Feb 2026.

---

## Prerequisites

- [ ] GHL account with API access (Settings > API > Generate Key)
- [ ] GHL custom fields created (see GHL Setup Validation below)
- [ ] GHL workflows created for hot/warm routing
- [ ] GHL calendar configured for HOT seller booking
- [ ] Environment variables configured in `.env` (copy from `.env.example`)
- [ ] PostgreSQL and Redis running
- [ ] Python 3.11+ with dependencies installed

---

## Environment Variables

### Core (Required)

| Variable | Description |
|----------|-------------|
| `GHL_API_KEY` | GHL API key from Settings > API |
| `GHL_LOCATION_ID` | GHL location ID (from URL when logged in) |
| `GHL_WEBHOOK_SECRET` | Webhook signature verification secret |
| `ANTHROPIC_API_KEY` | Claude API key for AI responses |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |

### Bot Mode Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `JORGE_SELLER_MODE` | `false` | Enable seller qualification routing |
| `JORGE_BUYER_MODE` | `false` | Enable buyer qualification routing |
| `JORGE_LEAD_MODE` | `true` | Enable lead qualification routing |
| `JORGE_SIMPLE_MODE` | `true` | `true` = 4-question flow, `false` = 10-question flow |
| `FRIENDLY_APPROACH` | `true` | Warm, consultative tone |

### Seller Bot

| Variable | Default | Description |
|----------|---------|-------------|
| `HOT_SELLER_WORKFLOW_ID` | (empty) | GHL workflow for hot sellers |
| `WARM_SELLER_WORKFLOW_ID` | (empty) | GHL workflow for warm sellers |
| `CUSTOM_FIELD_SELLER_TEMPERATURE` | (empty) | GHL custom field ID |
| `CUSTOM_FIELD_SELLER_MOTIVATION` | (empty) | GHL custom field ID |
| `CUSTOM_FIELD_TIMELINE_URGENCY` | (empty) | GHL custom field ID |
| `CUSTOM_FIELD_PROPERTY_CONDITION` | (empty) | GHL custom field ID |
| `CUSTOM_FIELD_PRICE_EXPECTATION` | (empty) | GHL custom field ID |
| `CUSTOM_FIELD_QUESTIONS_ANSWERED` | (empty) | GHL custom field ID |
| `CUSTOM_FIELD_QUALIFICATION_SCORE` | (empty) | GHL custom field ID |
| `CUSTOM_FIELD_PROPERTY_ADDRESS` | (empty) | GHL custom field ID |
| `CUSTOM_FIELD_QUALIFICATION_COMPLETE` | (empty) | GHL custom field ID |

### Buyer Bot

| Variable | Default | Description |
|----------|---------|-------------|
| `HOT_BUYER_WORKFLOW_ID` | (empty) | GHL workflow for hot buyers |
| `WARM_BUYER_WORKFLOW_ID` | (empty) | GHL workflow for warm buyers |
| `CUSTOM_FIELD_BUYER_TEMPERATURE` | (empty) | GHL custom field ID |
| `CUSTOM_FIELD_PRE_APPROVAL_STATUS` | (empty) | GHL custom field ID |
| `CUSTOM_FIELD_PROPERTY_PREFERENCES` | (empty) | GHL custom field ID |
| `CUSTOM_FIELD_BUDGET` | (empty) | GHL custom field ID |
| `BUYER_LEAD_TAG` | `Buyer-Lead` | Tag that activates buyer routing |

### Lead Bot

| Variable | Default | Description |
|----------|---------|-------------|
| `CUSTOM_FIELD_LEAD_SCORE` | (empty) | GHL custom field ID |
| `CUSTOM_FIELD_LOCATION` | (empty) | GHL custom field ID |
| `CUSTOM_FIELD_TIMELINE` | (empty) | GHL custom field ID |
| `LEAD_ACTIVATION_TAG` | `Needs Qualifying` | Tag that activates lead routing |
| `NOTIFY_AGENT_WORKFLOW_ID` | (empty) | Agent notification workflow |

### Seller Bot (continued — additional fields)

| Variable | Default | Description |
|----------|---------|-------------|
| `CUSTOM_FIELD_PCS_SCORE` | (empty) | Property condition score field |
| `CUSTOM_FIELD_SELLER_LIENS` | (empty) | Seller liens/encumbrances field |
| `CUSTOM_FIELD_SELLER_REPAIRS` | (empty) | Seller needed repairs field |
| `CUSTOM_FIELD_SELLER_LISTING_HISTORY` | (empty) | Previous listing history field |
| `CUSTOM_FIELD_SELLER_DECISION_MAKER` | (empty) | Decision maker status field |

### Calendar & Appointment Booking

| Variable | Default | Description |
|----------|---------|-------------|
| `JORGE_CALENDAR_ID` | (empty) | GHL calendar ID for HOT seller booking |
| `JORGE_USER_ID` | (empty) | Jorge's GHL user ID for appointment assignment |
| `MANUAL_SCHEDULING_WORKFLOW_ID` | (empty) | Workflow fallback if auto-booking fails |
| `CUSTOM_FIELD_APPOINTMENT_TIME` | (empty) | GHL field for scheduled appointment time |
| `CUSTOM_FIELD_APPOINTMENT_TYPE` | (empty) | GHL field for appointment type |
| `APPOINTMENT_AUTO_BOOKING_ENABLED` | `true` | Enable/disable auto-booking for HOT sellers |
| `APPOINTMENT_BUFFER_MINUTES` | `15` | Buffer time between appointments |
| `APPOINTMENT_DEFAULT_DURATION` | `60` | Default appointment duration (minutes) |
| `APPOINTMENT_MAX_DAYS_AHEAD` | `14` | Max days ahead to show availability |
| `APPOINTMENT_TIMEZONE` | `America/Los_Angeles` | Business timezone |

### Message Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_SMS_LENGTH` | `320` | Max SMS character limit (2 segments) |
| `USE_WARM_LANGUAGE` | `true` | Strip special chars, keep friendly tone |
| `NO_HYPHENS` | `true` | Remove hyphens from messages |

### Thresholds (Optional Overrides)

| Variable | Default | Description |
|----------|---------|-------------|
| `HOT_SELLER_THRESHOLD` | `1.0` | Hot classification threshold |
| `WARM_SELLER_THRESHOLD` | `0.75` | Warm classification threshold |
| `HOT_QUESTIONS_REQUIRED` | `4` (simple) / `10` (full) | Questions needed for hot |
| `HOT_QUALITY_THRESHOLD` | `0.7` | Min response quality for hot |
| `BUYER_QUALIFICATION_HOT_THRESHOLD` | `75` | Buyer hot score threshold |
| `BUYER_QUALIFICATION_WARM_THRESHOLD` | `50` | Buyer warm score threshold |

---

## GHL Setup Validation

Run the validation script to verify all custom fields, workflows, and calendar IDs:

```bash
python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup
```

Expected output:
- `[OK]` for all configured fields
- `[!!]` for missing CRITICAL fields (must fix before production)
- `[--]` for missing optional fields (bot works without them)

Critical fields that must show `[OK]`:
- `CUSTOM_FIELD_SELLER_TEMPERATURE`
- `CUSTOM_FIELD_TIMELINE_URGENCY`
- `CUSTOM_FIELD_BUYER_TEMPERATURE`
- `CUSTOM_FIELD_BUDGET`
- `CUSTOM_FIELD_LEAD_SCORE`
- `HOT_SELLER_WORKFLOW_ID`
- `HOT_BUYER_WORKFLOW_ID`
- `NOTIFY_AGENT_WORKFLOW_ID`

---

## GHL Workflow Setup

Create these workflows in GHL Dashboard > Automation > Workflows:

1. **Hot Seller Workflow** - Triggered when seller answers all 4 questions with quality responses
   - Action: Notify agent via SMS/email, assign to team member
   - Set workflow ID in `HOT_SELLER_WORKFLOW_ID`

2. **Warm Seller Workflow** - Triggered for partially qualified sellers
   - Action: Add to nurture sequence, schedule follow-up
   - Set workflow ID in `WARM_SELLER_WORKFLOW_ID`

3. **Hot Buyer Workflow** - Triggered for financially qualified buyers
   - Action: Schedule property showing, notify agent
   - Set workflow ID in `HOT_BUYER_WORKFLOW_ID`

4. **Agent Notification Workflow** - General qualified lead alert
   - Action: SMS + email to assigned agent
   - Set workflow ID in `NOTIFY_AGENT_WORKFLOW_ID`

---

## GHL Calendar Setup

For HOT seller automatic booking:

1. Create a calendar in GHL Dashboard > Calendars
2. Set available time slots for seller consultations
3. Copy the calendar ID and set `JORGE_CALENDAR_ID`
4. If not configured, HOT sellers get a fallback message asking for morning/afternoon preference

---

## Activation / Deactivation Tags

| Tag | Effect |
|-----|--------|
| `Needs Qualifying` | Activates seller/lead qualification |
| `Buyer-Lead` | Activates buyer qualification |
| `AI-Off` | Deactivates all bot processing |
| `Stop-Bot` | Deactivates all bot processing |
| `Qualified` | Deactivates (qualification complete) |
| `Seller-Qualified` | Deactivates seller bot |
| `TCPA-Opt-Out` | Applied on opt-out detection (STOP/unsubscribe) |
| `Compliance-Alert` | Applied when FHA/RESPA violation detected |
| `Human-Escalation-Needed` | Applied when conversation repair exhausts automated strategies |

---

## Smoke Test Procedure

### 1. Seller Bot

- [ ] Send "I'm thinking about selling my house" to a test contact tagged `Needs Qualifying`
- [ ] Verify bot asks first question (motivation/relocation)
- [ ] Answer all 4 questions with specific responses
- [ ] Verify GHL `seller_temperature` field updated to `Hot-Seller`
- [ ] Verify HOT seller workflow triggered (or calendar slots offered if `JORGE_CALENDAR_ID` set)

### 2. Buyer Bot

- [ ] Tag a test contact with `Buyer-Lead`
- [ ] Send "I'm looking to buy a home around $600K"
- [ ] Verify budget parsing and financial readiness scoring
- [ ] Verify GHL `buyer_temperature` field updated
- [ ] Verify appropriate workflow triggered

### 3. Lead Bot

- [ ] Send an initial message to a test contact tagged `Needs Qualifying`
- [ ] Verify temperature assessment (Hot/Warm/Cold)
- [ ] Verify lead score written to `CUSTOM_FIELD_LEAD_SCORE`

### 4. Cross-Bot Handoff

- [ ] Start with lead bot, say "I want to sell my house"
- [ ] Verify handoff from lead bot to seller bot (0.7 confidence threshold)
- [ ] Verify context preservation (seller bot has conversation history)

### 5. Response Pipeline

- [ ] Send "STOP" and verify TCPA opt-out short-circuit
- [ ] Verify AI disclosure footer appears on responses (SB 243)
- [ ] Verify SMS messages are truncated to 320 chars
- [ ] Verify compliance check blocks discriminatory language

### 6. Calendar Booking (if configured)

- [ ] Complete seller qualification as HOT
- [ ] Verify free slots are offered
- [ ] Reply with slot number
- [ ] Verify appointment created in GHL calendar

---

## Monitoring

### Performance Tracker
- P50/P95/P99 latency tracking per bot operation
- SLA compliance monitoring (configurable targets)
- Rolling window metrics (1h, 24h, 7d)
- Env: `PERFORMANCE_TRACKING_ENABLED=true`

### Alerting (7 Default Rules)
1. SLA violation (P95 > target)
2. High error rate (> threshold)
3. Low cache hit rate
4. Handoff failure
5. Bot unresponsive
6. Circular handoff spike
7. Rate limit breach

- Env: `ALERTING_ENABLED=true`
- Channels: Email, Slack, PagerDuty, OpsGenie (see `.env.example`)

### Bot Metrics Collector
- Per-bot stats: response count, latency, cache hits
- Aggregated at configurable interval (default 60s)
- Env: `BOT_METRICS_ENABLED=true`

### Handoff Router
- Performance-based routing prevents handoffs to slow/failing bots
- Auto-deferral when P95 > 120% SLA or error rate > 10%
- Auto-recovery when performance improves
- 30-minute cooldown between retries, max 3 retries

### Key KPIs
- Qualification completion rate: target 60% (simple mode)
- Hot lead conversion rate: target 15%
- Agent handoff rate: target 20%
- Follow-up engagement rate: target 30%
- Opt-out rate: target < 5%

---

## Rollback

### Immediate Deactivation
Add any of these tags to a contact to stop bot processing:
- `AI-Off`
- `Stop-Bot`

### Disable Bot Modes
```bash
JORGE_SELLER_MODE=false
JORGE_BUYER_MODE=false
JORGE_LEAD_MODE=false
```

### Feature-Level Disabling
```bash
AB_TESTING_ENABLED=false
PERFORMANCE_TRACKING_ENABLED=false
ALERTING_ENABLED=false
BOT_METRICS_ENABLED=false
```

---

## Response Pipeline Stages

All bot responses pass through 5 processing stages (in order):

| Stage | Purpose | Can Short-Circuit |
|-------|---------|-------------------|
| 1. Language Mirror | Detect contact language, set context | No |
| 2. TCPA Opt-Out | Handle "STOP"/"unsubscribe" requests | Yes |
| 3. Compliance Check | FHA/RESPA enforcement | No |
| 4. AI Disclosure | SB 243 AI-generated content footer | No |
| 5. SMS Truncation | Enforce 320-char SMS limit | No |

**Optional stage** (not in default pipeline):

| Stage | Purpose | Can Short-Circuit |
|-------|---------|-------------------|
| Conversation Repair | Detect breakdowns (low confidence, repeated questions, contradictions) and apply graduated repair | No |

To add conversation repair, use `pipeline.add_stage(ConversationRepairProcessor())` after constructing the default pipeline.
