# Jorge Bot — Production IDs Reference
# Last updated: 2026-02-27
# Service: jorge-realty-ai-xxdf.onrender.com (srv-d6d5go15pdvs73fcjjq0)

---

## GHL Workflow IDs

| Env Var | Workflow Name | ID |
|---------|---------------|----|
| `HOT_SELLER_WORKFLOW_ID` | Hot Seller | `577d56c4-28af-4668-8d84-80f5db234f48` |
| `WARM_SELLER_WORKFLOW_ID` | Warm Seller | `64b82875-89fb-4e67-807c-ceba2116b838` |
| `HOT_BUYER_WORKFLOW_ID` | Hot Buyer | `1ea9197e-143c-45bd-acb3-8162eeda84c9` |
| `WARM_BUYER_WORKFLOW_ID` | Warm Buyer / Agent Notify | `f3fc268b-5f16-4854-af28-200024cb3c8b` |
| `NOTIFY_AGENT_WORKFLOW_ID` | Agent Notification | `f3fc268b-5f16-4854-af28-200024cb3c8b` |

> Note: WARM_BUYER and NOTIFY_AGENT currently share the same ID. If Jorge creates a dedicated
> warm-buyer nurture workflow, update WARM_BUYER_WORKFLOW_ID separately.

---

## GHL Calendar & User

| Env Var | Value |
|---------|-------|
| `JORGE_CALENDAR_ID` | `CrqysY0FVTxatzEczl7h` |
| `GHL_CALENDAR_ID` | `CrqysY0FVTxatzEczl7h` |
| `JORGE_USER_ID` | `Or4ImSUxUarPJQyawA5W` |

---

## GHL Custom Field IDs — Core Scoring

| Env Var | GHL Field ID |
|---------|-------------|
| `CUSTOM_FIELD_LEAD_SCORE` | `barDqSiziV2XsVw6WKKb` |
| `CUSTOM_FIELD_BUDGET` | `2XyZHYEFD6YjXkv6D2xN` |
| `CUSTOM_FIELD_LOCATION` | `XdIrAUGWXHTZnFWKSOMY` |
| `CUSTOM_FIELD_TIMELINE` | `SJc5eQHa1wraqKvEn3GF` |

---

## GHL Custom Field IDs — Seller Bot

| Env Var | GHL Field ID |
|---------|-------------|
| `CUSTOM_FIELD_SELLER_TEMPERATURE` | `jkQFooyVp0OEcaYVNJQL` |
| `CUSTOM_FIELD_SELLER_MOTIVATION` | `70kCdEvjjia40FXwJCvZ` |
| `CUSTOM_FIELD_TIMELINE_URGENCY` | `5ekKqKwL8LCnYj0rvr7x` |
| `CUSTOM_FIELD_PROPERTY_CONDITION` | `HEsrvb0eSYHR9kIPVzVx` |
| `CUSTOM_FIELD_PRICE_EXPECTATION` | `TH5M68o73lTdJmvaodjN` |
| `CUSTOM_FIELD_PROPERTY_ADDRESS` | `AoCxlGK7K1MMiWrs6ZvF` |
| `CUSTOM_FIELD_QUALIFICATION_COMPLETE` | `bOfcrncwqL7L9ABwIVLM` |
| `CUSTOM_FIELD_QUALIFICATION_SCORE` | `vRKYsiyXLnFXUsQtqBLo` |
| `CUSTOM_FIELD_AI_VALUATION_PRICE` | `u1HiHi9wv9LKu9g5OJvc` |

---

## GHL Custom Field IDs — Buyer Bot

| Env Var | GHL Field ID |
|---------|-------------|
| `CUSTOM_FIELD_BUYER_TEMPERATURE` | `r1k8LHLKrIVqhy94glX2` |
| `CUSTOM_FIELD_PRE_APPROVAL_STATUS` | `jCnR8zng4FQjGvvAt9AI` |
| `CUSTOM_FIELD_PROPERTY_PREFERENCES` | `uhUBipWx4kijtUk2Mhbl` |

---

## GHL Custom Field IDs — Handoff & Intent Scoring

| Env Var | GHL Field ID |
|---------|-------------|
| `GHL_CUSTOM_FIELD_FRS` | `H6ogTJCOSJYkT1UaNUZ4` |
| `GHL_CUSTOM_FIELD_PCS` | `ZJmEZ7yfLYoGKxobUxEB` |
| `GHL_CUSTOM_FIELD_BUYER_INTENT` | `X40wlBi8kJE7JKo4cTY3` |
| `GHL_CUSTOM_FIELD_SELLER_INTENT` | `mqkuWxpQNjPCE1BCoTdN` |
| `GHL_CUSTOM_FIELD_TEMPERATURE` | `jkQFooyVp0OEcaYVNJQL` |
| `GHL_CUSTOM_FIELD_HANDOFF_HISTORY` | `2FpBMFbI74uk8OZrCAjx` |
| `GHL_CUSTOM_FIELD_LAST_BOT` | `0jGS8XMHWbHTXQmYTNZb` |
| `GHL_CUSTOM_FIELD_CONVERSATION_CONTEXT` | `fAh7vhfxWaOECV47sQ77` |

---

## Tag Routing

| Tag | Effect |
|-----|--------|
| `Needs Qualifying` | Activates seller bot (if JORGE_SELLER_MODE=true) or lead bot |
| `Seller-Lead` | Also activates seller bot |
| `Buyer-Lead` | Activates buyer bot |
| `AI-Off` | Deactivates all bots |
| `Stop-Bot` | Deactivates all bots |
| `Qualified` | Deactivates (qualification complete) |

---

## Secrets (stored on Render only — NOT shown here)

- `GHL_WEBHOOK_SECRET` — set on Render, starts with `bc46c793`. Source: X-GHL-Signature header in "Jorge AI Bot - Inbound Message Handler" workflow.
- `GHL_API_KEY` — set on Render
- `ANTHROPIC_API_KEY` — set on Render

---

## GHL Webhook URLs (active)

| Workflow | URL |
|----------|-----|
| Inbound Message Handler | `https://jorge-realty-ai-xxdf.onrender.com/api/ghl/webhook` |
| Seller Bot Trigger | `https://jorge-realty-ai-xxdf.onrender.com/api/ghl/tag-webhook` |
| Buyer Bot Trigger | `https://jorge-realty-ai-xxdf.onrender.com/api/ghl/tag-webhook` |
