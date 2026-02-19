# Jorge GHL Setup Guide — Connect Bots to Your Account

This guide walks through every step needed in Jorge's GHL dashboard to connect the AI bots. Estimated time: 30-45 minutes.

---

## Step 1: Get Your API Key & Location ID

1. Log into GHL → **Settings** → **Business Profile** → copy the **Location ID** from the URL
   - URL looks like: `https://app.gohighlevel.com/location/XXXXXX/...`
   - The `XXXXXX` part is your Location ID
2. Go to **Settings** → **API** → click **Generate Key**
3. Add both to your `.env`:
   ```
   GHL_API_KEY=your_api_key_here
   GHL_LOCATION_ID=your_location_id_here
   ```

---

## Step 2: Create Custom Fields

Go to **Settings** → **Custom Fields** → **Add Field** for each:

### Seller Fields (Required)
| Field Name | Field Type | Env Variable |
|-----------|-----------|-------------|
| Seller Temperature | Single Line Text | `CUSTOM_FIELD_SELLER_TEMPERATURE` |
| Seller Motivation | Single Line Text | `CUSTOM_FIELD_SELLER_MOTIVATION` |
| Timeline Urgency | Single Line Text | `CUSTOM_FIELD_TIMELINE_URGENCY` |
| Property Condition | Single Line Text | `CUSTOM_FIELD_PROPERTY_CONDITION` |
| Price Expectation | Number | `CUSTOM_FIELD_PRICE_EXPECTATION` |
| Questions Answered | Number | `CUSTOM_FIELD_QUESTIONS_ANSWERED` |
| Qualification Score | Number | `CUSTOM_FIELD_QUALIFICATION_SCORE` |
| Property Address | Single Line Text | `CUSTOM_FIELD_PROPERTY_ADDRESS` |
| Qualification Complete | Checkbox | `CUSTOM_FIELD_QUALIFICATION_COMPLETE` |

### Buyer Fields (Required)
| Field Name | Field Type | Env Variable |
|-----------|-----------|-------------|
| Buyer Temperature | Single Line Text | `CUSTOM_FIELD_BUYER_TEMPERATURE` |
| Pre Approval Status | Single Line Text | `CUSTOM_FIELD_PRE_APPROVAL_STATUS` |
| Property Preferences | Multi Line Text | `CUSTOM_FIELD_PROPERTY_PREFERENCES` |
| Budget | Number | `CUSTOM_FIELD_BUDGET` |

### Lead Fields (Required)
| Field Name | Field Type | Env Variable |
|-----------|-----------|-------------|
| Lead Score | Number | `CUSTOM_FIELD_LEAD_SCORE` |
| Location | Single Line Text | `CUSTOM_FIELD_LOCATION` |
| Timeline | Single Line Text | `CUSTOM_FIELD_TIMELINE` |

### Bot Tracking Fields (Recommended)
| Field Name | Field Type | Env Variable |
|-----------|-----------|-------------|
| Bot Buyer Persona | Single Line Text | `CUSTOM_FIELD_BOT_BUYER_PERSONA` |
| Bot Language | Single Line Text | `CUSTOM_FIELD_BOT_LANGUAGE` |
| Bot Conversation Stage | Single Line Text | `CUSTOM_FIELD_BOT_CONVERSATION_STAGE` |
| Bot Last Interaction | Single Line Text | `CUSTOM_FIELD_BOT_LAST_INTERACTION` |
| Bot Qualification Score | Number | `CUSTOM_FIELD_BOT_QUALIFICATION_SCORE` |
| Bot Active | Checkbox | `CUSTOM_FIELD_BOT_ACTIVE` |

These fields are optional but recommended for CRM reporting and workflow triggers.

**After creating each field**: Click on it → copy the **Field ID** from the URL or field details → paste into your `.env` file.

---

## Step 3: Create Workflows

Go to **Automation** → **Workflows** → **Create Workflow** for each:

### Workflow 1: Hot Seller Notification
- **Trigger**: None (triggered by API)
- **Actions**:
  1. Send SMS to Jorge: "HOT SELLER: {{contact.name}} answered all questions. Score: {{custom.qualification_score}}. Call them ASAP."
  2. Send Email to Jorge with full qualification summary
  3. Add to "Hot Sellers" pipeline stage
  4. Create task: "Call {{contact.name}} within 2 hours"
- Copy workflow ID → `.env`: `HOT_SELLER_WORKFLOW_ID=workflow_id`

### Workflow 2: Warm Seller Nurture
- **Trigger**: None (triggered by API)
- **Actions**:
  1. Wait 2 days
  2. Send SMS: "Hey {{contact.first_name}}, still thinking about selling? I found some recent sales in your area that might interest you."
  3. Wait 5 days
  4. Send Email with market update
- Copy workflow ID → `.env`: `WARM_SELLER_WORKFLOW_ID=workflow_id`

### Workflow 3: Hot Buyer Notification
- **Trigger**: None (triggered by API)
- **Actions**:
  1. Send SMS to Jorge: "HOT BUYER: {{contact.name}} is pre-approved, budget ${{custom.budget}}. Ready for showings."
  2. Send Email with buyer profile
  3. Create task: "Schedule showing for {{contact.name}}"
- Copy workflow ID → `.env`: `HOT_BUYER_WORKFLOW_ID=workflow_id`

### Workflow 4: Agent Notification (General)
- **Trigger**: None (triggered by API)
- **Actions**:
  1. Send Internal Notification to Jorge
  2. Send SMS: "New qualified lead: {{contact.name}} — {{custom.lead_score}} score"
- Copy workflow ID → `.env`: `NOTIFY_AGENT_WORKFLOW_ID=workflow_id`

---

## Step 4: Create Calendar (for HOT Seller Booking)

1. Go to **Calendars** → **Create Calendar**
2. Name: "Seller Consultation"
3. Set availability: Jorge's available time slots (e.g., Mon-Fri 9am-5pm PT)
4. Duration: 60 minutes
5. Buffer: 15 minutes between appointments
6. Copy Calendar ID → `.env`: `JORGE_CALENDAR_ID=calendar_id`
7. Copy Jorge's User ID → `.env`: `JORGE_USER_ID=user_id`

---

## Step 4b: Set Up Dual Pipelines (Opportunities)

Create two pipelines in **Opportunities** to track leads through qualification:

### Buyer Pipeline
Create stages in order:
1. **New Lead** — Contact enters when tagged `Buyer-Lead`
2. **Qualifying** — Bot is asking qualification questions
3. **Financially Ready** — Pre-approval confirmed, budget captured
4. **Showing Scheduled** — Appointment booked with Jorge
5. **Under Contract** — Offer accepted (move manually)
6. **Closed** — Deal closed
7. **Lost** — Opted out or disqualified

### Seller Pipeline
Create stages in order:
1. **New Lead** — Contact enters when tagged `Needs Qualifying` or `Seller-Lead`
2. **Qualifying** — Bot is asking 4 qualification questions
3. **Warm Seller** — Answered 3+ questions, engaged
4. **Hot Seller** — All 4 questions answered, timeline accepted
5. **Listing Appointment** — Consultation scheduled with Jorge
6. **Listed** — Property on market (move manually)
7. **Under Contract** — Accepted offer
8. **Closed** — Deal closed
9. **Lost** — Opted out or disqualified

Pipeline automation: Set up workflow triggers to move contacts between stages based on bot tags (e.g., `Hot-Seller` tag → move to "Hot Seller" stage).

---

## Step 5: Set Up Webhook

1. Go to **Settings** → **Webhooks** (or **Automation** → **Webhooks**)
2. Create webhook:
   - **URL**: `https://your-deployed-url.com/ghl/webhook`
   - **Events**: Inbound Message, Contact Tag Added
3. Copy the webhook secret → `.env`: `GHL_WEBHOOK_SECRET=secret_here`

---

## Step 6: Create Tags

These tags should already exist or be created:
- `Needs Qualifying` — Applied to new seller/lead contacts
- `Buyer-Lead` — Applied to buyer contacts
- `AI-Off` — Stops all bot processing
- `Stop-Bot` — Stops all bot processing

---

## Step 7: Enable Bot Modes

Update `.env` to activate:
```
JORGE_SELLER_MODE=true
JORGE_BUYER_MODE=true
JORGE_LEAD_MODE=true
```

---

## Step 8: Validate Setup

Run the validation script:
```bash
cd /Users/cave/Projects/EnterpriseHub_new
python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup
```

All critical fields should show `[OK]`. Fix any `[!!]` items before going live.

---

## Step 9: Smoke Test

1. Create a test contact in GHL
2. Add tag `Needs Qualifying`
3. Send an inbound SMS: "I'm thinking about selling my house"
4. Watch for:
   - Bot response within 15 seconds
   - First question asked (motivation/relocation)
   - Custom fields updating in GHL
5. Answer all 4 questions → verify `Hot-Seller` tag applied
6. Verify HOT workflow triggered (Jorge gets notified)

---

## Environment Variables Checklist

After completing all steps, verify these are set in `.env`:

```
# Core (should already be set)
GHL_API_KEY=✅
GHL_LOCATION_ID=✅
GHL_WEBHOOK_SECRET=

# Workflows (from Step 3)
HOT_SELLER_WORKFLOW_ID=
WARM_SELLER_WORKFLOW_ID=
HOT_BUYER_WORKFLOW_ID=
NOTIFY_AGENT_WORKFLOW_ID=

# Calendar (from Step 4)
JORGE_CALENDAR_ID=
JORGE_USER_ID=

# Custom Fields - Seller (from Step 2)
CUSTOM_FIELD_SELLER_TEMPERATURE=
CUSTOM_FIELD_SELLER_MOTIVATION=
CUSTOM_FIELD_TIMELINE_URGENCY=
CUSTOM_FIELD_PROPERTY_CONDITION=
CUSTOM_FIELD_PRICE_EXPECTATION=
CUSTOM_FIELD_QUESTIONS_ANSWERED=
CUSTOM_FIELD_QUALIFICATION_SCORE=
CUSTOM_FIELD_PROPERTY_ADDRESS=
CUSTOM_FIELD_QUALIFICATION_COMPLETE=

# Custom Fields - Buyer (from Step 2)
CUSTOM_FIELD_BUYER_TEMPERATURE=
CUSTOM_FIELD_PRE_APPROVAL_STATUS=
CUSTOM_FIELD_PROPERTY_PREFERENCES=
CUSTOM_FIELD_BUDGET=

# Custom Fields - Lead (from Step 2)
CUSTOM_FIELD_LEAD_SCORE=
CUSTOM_FIELD_LOCATION=
CUSTOM_FIELD_TIMELINE=

# Bot Modes (from Step 7)
JORGE_SELLER_MODE=true
JORGE_BUYER_MODE=true
JORGE_LEAD_MODE=true
```
