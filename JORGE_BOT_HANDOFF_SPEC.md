# Jorge Realty AI Bot — Full Debugging & Finalization Spec
**Date:** 2026-02-21  
**Render service:** `jorge-realty-ai` (`srv-d6cecon5r7bs738qgi10`)  
**Live URL:** `https://jorge-realty-ai.onrender.com`  
**Repo:** `https://github.com/ChunkyTortoise/EnterpriseHub.git` → branch `main`  
**Project root on disk:** `/Users/cave/Projects/EnterpriseHub_new`  
**Sub-project:** `ghl_real_estate_ai/`  
**GHL sub-account:** Lyrio — Location ID `3xt4qayAh35BlDLaUv7P`

---

## 1. Current Status (end of last chat)

### Commits pushed (newest first)

| Hash | Message |
|------|---------|
| `66f69ef5` | fix: propagate top-level tags in GHL flat webhook format |
| `2d173443` | fix: case-insensitive tag matching in webhook + pin Python 3.11 |
| `1b0a47d7` | fix: upgrade langgraph + fix GHL send_message conversationId lookup |

### Verification test result (after `66f69ef5`)
```
STATUS: 200
BODY: {"success": true, "message": "AI not triggered (activation tag missing)", "actions": []}
```
**Still failing.** The bot is not activating even with `"tags": ["needs qualifying"]` in the payload.

---

## 2. Root Cause Archaeology — What Was Found

### Issue A — `ForwardRef._evaluate()` TypeError (FIXED in `1b0a47d7`)
- `langgraph==0.0.55` pulled in old `langsmith` which pulled in pydantic v1 compat layer
- Called `ForwardRef._evaluate(globalns, localns, set())` — Python 3.12 requires `recursive_guard=` as keyword arg
- Crashed `JorgeSellerEngine` at import on every request
- **Fix:** `langgraph>=0.1.16,<0.3.0` + `langsmith>=0.1.0` in both `requirements.txt` and `requirements-prod.txt`

### Issue B — GHL `send_message` 400 Bad Request (FIXED in `1b0a47d7`)
- `ghl_client.py` `send_message()` was sending `contactId` to `POST /conversations/messages`
- GHL v2 requires `conversationId` (not `contactId`)
- **Fix:** Added `get_or_create_conversation_id(contact_id)` helper that calls `GET /conversations/search?locationId=…&contactId=…`, then uses returned `conversationId` in the message payload

### Issue C — Tag case mismatch (FIXED in `2d173443`)
- `webhook.py` hardcoded `"Needs Qualifying" in tags` (title case)
- GHL delivers tags as `"needs qualifying"` (lowercase)
- **Fix:** Added `tags_lower = {t.lower() for t in tags}` after all tag-fetching; all 7 checks now use `.lower() in tags_lower`
  - `handle_ghl_tag_webhook` guard
  - `should_activate` / `should_deactivate`
  - `jorge_seller_mode`
  - `jorge_buyer_mode`
  - `jorge_lead_mode`
  - Dual-bot collision guard

### Issue D — Top-level tags dropped in flat webhook (FIXED in `66f69ef5`)
- `api/schemas/ghl.py` validator synthesized `contact` with hardcoded `"tags": []`
- Silently discarded the top-level `"tags"` field from the payload
- **Fix:** `"tags": data.get("tags", [])` so top-level tags propagate into the contact object

### Issue E — **STILL FAILING** — Unknown activation blocker

Despite fixes C and D, the test still returns `"AI not triggered (activation tag missing)"`.

#### E1 (most likely): Render hasn't deployed `66f69ef5` yet
- Response comes back in ~1s (no cold start) — may still be on older deploy
- **Check:** Render dashboard → Deployments → confirm `66f69ef5` is "Live"

#### E2: `JORGE_SELLER_MODE` env var is `false` or missing
- Even if `should_activate` is True, `jorge_seller_mode` requires `jorge_settings.JORGE_SELLER_MODE`
- `render.yaml` sets it, but verify it's actually in Render dashboard env vars

#### E3: `ACTIVATION_TAGS` env var override in Render
- If `ACTIVATION_TAGS` is set in Render to a title-case-only list, it overrides `config.py` defaults
- `should_activate` would then fail for lowercase tags

#### E4: GHL API fetch returns empty tags for test contact
- If `66f69ef5` deploy hasn't landed, `event.contact.tags = []`
- Code falls back to `ghl_client_default.get_contact("INCSVVBKWW6qLFZ1oXnr")`
- Test contact may have no tags in GHL → `tags = []` → activation fails

---

## 3. Files That Matter

```
ghl_real_estate_ai/
├── api/
│   ├── routes/
│   │   └── webhook.py              ← Main bot logic (MODIFIED in 2d173443)
│   └── schemas/
│       └── ghl.py                  ← Webhook event schema (MODIFIED in 66f69ef5)
├── services/
│   ├── ghl_client.py               ← GHL API client (MODIFIED in 1b0a47d7)
│   └── jorge/
│       └── jorge_seller_engine.py  ← Seller AI engine (fixed by langgraph upgrade)
├── ghl_utils/
│   ├── config.py                   ← App settings (activation_tags lives here)
│   └── jorge_config.py             ← Jorge-specific settings
├── requirements.txt                ← (MODIFIED in 1b0a47d7)
├── requirements-prod.txt           ← (MODIFIED in 1b0a47d7)
├── .python-version                 ← (ADDED in 2d173443, pins 3.11.0)
└── render.yaml                     ← Render deploy config
```

---

## 4. Key Architecture: How a Webhook Activates the Seller Bot

```
GHL sends InboundMessage webhook (flat JSON)
    ↓
POST /api/ghl/webhook
    ↓
verify_webhook() — HMAC-SHA256 check against GHL_WEBHOOK_SECRET
    ↓
GHLWebhookEvent.handle_ghl_native_format() validator  [ghl.py]
    → flat format → nested
    → contact.tags = data.get("tags", [])              ← fix D
    ↓
handle_ghl_webhook()  [webhook.py]
    ↓
tags = event.contact.tags   (should have ["needs qualifying"])
    ↓
if not tags: fetch from GHL API → get_contact(contact_id)
    ↓
tags_lower = {t.lower() for t in tags}                 ← fix C
    ↓
should_activate = any(tag.lower() in tags_lower        ← fix C
                      for tag in settings.activation_tags)
  # settings.activation_tags = ["needs qualifying", "Needs Qualifying"]
    ↓
if not should_activate:
    return "AI not triggered (activation tag missing)"  ← still hitting this
    ↓
jorge_seller_mode = ("needs qualifying" in tags_lower  ← fix C
                     or "seller-lead" in tags_lower)
                    and jorge_settings.JORGE_SELLER_MODE
                    and not should_deactivate
    ↓
if jorge_seller_mode:
    → JorgeSellerEngine.process()   ← fixed by langgraph upgrade
```

---

## 5. Verification Tests

### Test A — Flat format (primary)
```python
import hmac, hashlib, json, requests

SECRET = "bc46c793aad3863d23e3e756f6a7a0bc2daa2747a5f9eddf457bc622e19b6b2d"
payload = {
    "type": "InboundMessage",
    "locationId": "3xt4qayAh35BlDLaUv7P",
    "contactId": "INCSVVBKWW6qLFZ1oXnr",
    "body": "Hi, I want to sell my house",
    "messageType": "SMS",
    "tags": ["needs qualifying"]
}
body = json.dumps(payload).encode()
sig = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
r = requests.post(
    "https://jorge-realty-ai.onrender.com/api/ghl/webhook",
    data=body,
    headers={"Content-Type": "application/json", "X-GHL-Signature": sig},
    timeout=90
)
print("STATUS:", r.status_code)
print("BODY:", json.dumps(r.json(), indent=2))
```

### Test B — Nested contact (isolates ghl.py fix)
```python
payload_b = {
    "type": "InboundMessage",
    "locationId": "3xt4qayAh35BlDLaUv7P",
    "contactId": "INCSVVBKWW6qLFZ1oXnr",
    "body": "Hi, I want to sell my house",
    "messageType": "SMS",
    "contact": {
        "contactId": "INCSVVBKWW6qLFZ1oXnr",
        "tags": ["needs qualifying"]
    },
    "message": {
        "type": "SMS",
        "body": "Hi, I want to sell my house",
        "direction": "inbound"
    }
}
# same sig/request pattern as Test A
```

**Decision tree:**
- Test B passes, Test A fails → `66f69ef5` not deployed yet, wait and retry
- Both fail with "AI not triggered" → env var problem (E2 or E3) — check Render dashboard
- Both fail with different error → deeper issue, check Render logs

---

## 6. Render Environment Variables to Verify

Dashboard → jorge-realty-ai → Environment:

| Variable | Required Value | Notes |
|----------|---------------|-------|
| `JORGE_SELLER_MODE` | `true` | Must be string `"true"` |
| `JORGE_BUYER_MODE` | `true` | |
| `JORGE_LEAD_MODE` | `true` | |
| `GHL_WEBHOOK_SECRET` | `bc46c793...b6b2d` | Full 64-char hex |
| `GHL_API_KEY` | JWT token | Starts with `eyJ` |
| `GHL_LOCATION_ID` | `3xt4qayAh35BlDLaUv7P` | |
| `LOCATION_ID` | `3xt4qayAh35BlDLaUv7P` | Duplicate for legacy code |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | |
| `ENVIRONMENT` | `production` | |

---

## 7. Debug Endpoint (add temporarily if still stuck)

Add to `webhook.py` to expose parsed state without running the full bot:

```python
@router.post("/debug/tags")
async def debug_tags(request: Request):
    """Temporary debug — REMOVE before final deploy."""
    import json
    data = json.loads(await request.body())
    from ghl_real_estate_ai.api.schemas.ghl import GHLWebhookEvent
    event = GHLWebhookEvent(**data)
    tags = (event.contact.tags if event.contact else []) or []
    tags_lower = {t.lower() for t in tags}
    from ghl_real_estate_ai.ghl_utils.config import settings as s
    from ghl_real_estate_ai.ghl_utils.jorge_config import settings as js
    return {
        "contact_tags_raw": event.contact.tags if event.contact else None,
        "tags": tags,
        "tags_lower": sorted(tags_lower),
        "activation_tags": s.activation_tags,
        "deactivation_tags": s.deactivation_tags,
        "should_activate": any(t.lower() in tags_lower for t in s.activation_tags),
        "should_deactivate": any(t.lower() in tags_lower for t in s.deactivation_tags),
        "JORGE_SELLER_MODE": js.JORGE_SELLER_MODE,
        "JORGE_BUYER_MODE": js.JORGE_BUYER_MODE,
        "JORGE_LEAD_MODE": js.JORGE_LEAD_MODE,
        "LEAD_ACTIVATION_TAG": js.LEAD_ACTIVATION_TAG,
        "BUYER_ACTIVATION_TAG": js.BUYER_ACTIVATION_TAG,
    }
```

Then hit it with the same payload (no signature needed — no verify_webhook call):
```bash
curl -s -X POST https://jorge-realty-ai.onrender.com/api/ghl/debug/tags \
  -H "Content-Type: application/json" \
  -d '{"type":"InboundMessage","locationId":"3xt4qayAh35BlDLaUv7P","contactId":"INCSVVBKWW6qLFZ1oXnr","body":"test","messageType":"SMS","tags":["needs qualifying"]}' | python3 -m json.tool
```

---

## 8. Remaining Issues After Bot Activates

### 8.1 Real SMS delivery
- Test contact `INCSVVBKWW6qLFZ1oXnr` has fake phone `+19095550123` (555)
- GHL will reject actual SMS delivery
- Use a real phone number for end-to-end test

### 8.2 GHL conversation lookup
- `send_message` now calls `get_or_create_conversation_id()` first
- Check Render logs for: `Found conversationId <id> for contact <id>`
- If you see `No conversation found for contact` → the fallback (contactId) fires, which may still 400

### 8.3 Seller engine response quality
Once activated, verify:
- First message asks for property address (Q0 in simple mode)
- No hyphens in response
- Message ≤ 320 chars
- No `Bot-Fallback-Active` tag

### 8.4 Tag lifecycle
After qualification completes:
- `"needs qualifying"` removed
- Temperature tag added (`Warm-Seller` / `Hot-Seller` / `Cold-Seller`)
- `"Seller-Qualified"` added for hot leads

---

## 9. Definition of "Bots Functioning Perfectly"

1. **Test A returns `200` + seller question** (not "AI not triggered")
2. **No ForwardRef errors** in Render logs
3. **No 400 on send_message** — logs show `Found conversationId`
4. **Tag lifecycle works** — qualifying tag removed, temperature tag added
5. **Real SMS delivers** to a real phone number
6. **Lead/seller collision handled** — seller takes priority, no duplicate messages
