# Monday Zoom — Remaining Setup (20 min total)

**Status as of Feb 20, 2026**: All custom fields, calendar, and Railway are set.
Only 4 workflows remain. Jorge must do these as account owner.

---

## Pre-Zoom (Cayman does before call)
- [ ] Share `.env.jorge` with Jorge via secure link
- [ ] Confirm Railway `sparkling-light` project is running
- [ ] Connect GitHub repo: Railway dashboard → sparkling-light → Settings → Source → GitHub → ChunkyTortoise/EnterpriseHub

---

## Zoom: Create 6 Workflows (~25 min)

**Jorge logs in → Automation → Workflows → "+ Create Workflow" → Start from Scratch**

---

### Workflow 0: Seller Bot — First Message Trigger (~3 min) ⚠️ CRITICAL

**Name**: `Jorge — Seller Bot Trigger`

**Trigger**:
- Type: **Contact Tag Added**
- Tag: `Needs Qualifying`

**Actions** (in order):
1. **Custom Webhook** → Method: POST → URL: `https://sparkling-light.up.railway.app/api/ghl/tag-webhook`
   - Header: `X-GHL-Signature: change-me-to-a-32-char-random-secret`
   - Body (JSON):
   ```json
   {
     "tag": "Needs Qualifying",
     "contactId": "{{contact.id}}",
     "locationId": "{{location.id}}",
     "contact": {
       "contactId": "{{contact.id}}",
       "firstName": "{{contact.first_name}}",
       "lastName": "{{contact.last_name}}",
       "phone": "{{contact.phone}}"
     }
   }
   ```

**Publish** (no ID needed — not pasted into Railway)

> This is what makes the seller bot reach out FIRST. Without this, the bot only responds — it never initiates.

---

### Workflow 00: Buyer Bot — First Message Trigger (~3 min) ⚠️ CRITICAL

**Name**: `Jorge — Buyer Bot Trigger`

**Trigger**:
- Type: **Contact Tag Added**
- Tag: `Buyer-Lead`

**Actions** (in order):
1. **Send SMS** → To: `{{contact.phone}}` → Message: "Hi {{contact.first_name}}, this is Jorge. I help buyers find homes in Rancho Cucamonga. What area are you looking in and what's your ideal timeline? [AI-assisted message]"

**Publish** (no ID needed)

> Buyer bot doesn't auto-send via webhook yet — this GHL action sends the first message directly so the buyer bot can take over on their reply.

---

### Workflow 1: Hot Seller Alert (~3 min)

**Name**: `Jorge — Hot Seller Alert`

**Trigger**:
- Type: **Contact Tag Added**
- Tag: `Hot-Seller`

**Actions** (in order):
1. **Send Internal Notification** → Body: "🔥 HOT SELLER: {{contact.first_name}} {{contact.last_name}} answered all 4 questions. Call ASAP! Phone: {{contact.phone}}"
2. **Send SMS** → To: Jorge's phone → Message: "HOT SELLER ALERT: {{contact.first_name}} is ready. Call them now: {{contact.phone}}"

**Publish** → Copy ID from URL (`/automation/workflows/XXXXXXXX`)

Paste into Railway: `HOT_SELLER_WORKFLOW_ID=XXXXXXXX`

---

### Workflow 2: Warm Seller Nurture (~3 min)

**Name**: `Jorge — Warm Seller Nurture`

**Trigger**:
- Type: **Contact Tag Added**
- Tag: `Warm-Seller`

**Actions** (in order):
1. **Wait** → 2 days
2. **Send SMS** → To: `{{contact.phone}}` → Message: "Hey {{contact.first_name}}, just checking in — still thinking about selling? Happy to answer any questions. - Jorge"
3. **Wait** → 5 days
4. **Send SMS** → To: `{{contact.phone}}` → Message: "Hi {{contact.first_name}}, the Rancho Cucamonga market is moving fast right now. Want a quick update on what homes like yours are selling for? - Jorge"

**Publish** → Copy ID from URL

Paste into Railway: `WARM_SELLER_WORKFLOW_ID=XXXXXXXX`

---

### Workflow 3: Hot Buyer Alert (~3 min)

**Name**: `Jorge — Hot Buyer Alert`

**Trigger**:
- Type: **Contact Tag Added**
- Tag: `Hot-Lead`

**Actions** (in order):
1. **Send Internal Notification** → Body: "🏠 HOT BUYER: {{contact.first_name}} {{contact.last_name}} is pre-approved and ready for showings. Budget captured. Phone: {{contact.phone}}"
2. **Send SMS** → To: Jorge's phone → Message: "HOT BUYER: {{contact.first_name}} ready for showings. Call: {{contact.phone}}"

**Publish** → Copy ID from URL

Paste into Railway: `HOT_BUYER_WORKFLOW_ID=XXXXXXXX`

---

### Workflow 4: Agent Notification (~3 min)

**Name**: `Jorge — Agent Notification`

**Trigger**:
- Type: **Contact Tag Added**
- Tag: `Qualified`

**Actions** (in order):
1. **Send Internal Notification** → Body: "✅ QUALIFIED: {{contact.first_name}} {{contact.last_name}} has completed the AI qualification flow. Phone: {{contact.phone}}"
2. **Send Email** → To: `realtorjorgesalas@gmail.com` → Subject: "New Qualified Lead: {{contact.first_name}}" → Body: "Your AI bot qualified {{contact.first_name}} {{contact.last_name}}.\n\nPhone: {{contact.phone}}\nEmail: {{contact.email}}\n\nLog in to GHL to see their full profile and qualification answers."

**Publish** → Copy ID from URL

Paste into Railway: `NOTIFY_AGENT_WORKFLOW_ID=XXXXXXXX`

---

## After All 6 Workflows: Update Railway

In Railway `sparkling-light` → Variables tab → add all 4 IDs (Workflows 0 and 00 don't need IDs):

```
HOT_SELLER_WORKFLOW_ID=<paste ID 1>
WARM_SELLER_WORKFLOW_ID=<paste ID 2>
HOT_BUYER_WORKFLOW_ID=<paste ID 3>
NOTIFY_AGENT_WORKFLOW_ID=<paste ID 4>
```

Railway auto-redeploys on variable save.

---

## Smoke Test (~5 min)

1. In GHL → Contacts → find or create a test contact
2. Manually add tag `Hot-Seller`
3. Confirm: Internal notification fires + Jorge's SMS fires
4. Check Railway logs for any errors

---

## Also Needed (Jorge provides separately)

| Item | Where to get |
|------|-------------|
| `ANTHROPIC_API_KEY` | platform.anthropic.com → API Keys |
| A2P 10DLC registration | GHL Settings → Phone Numbers → Register (required for SMS) |

---

## Already Done ✅
- All 22 GHL custom fields: mapped in `.env.jorge`
- Calendar: `CrqysY0FVTxatzEczl7h` (Zoom Call With Jorge Sales)
- Railway: `sparkling-light` — 65 env vars set, Postgres + Redis added
- All 3 bots: code-complete, 114 tests passing
