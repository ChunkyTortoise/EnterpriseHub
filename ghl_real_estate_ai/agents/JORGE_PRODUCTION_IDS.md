# Jorge Bot — Production IDs Reference
# Last updated: 2026-02-28 (CC DTS workflow integration)
# Service: jorge-realty-ai-xxdf.onrender.com (srv-d6d5go15pdvs73fcjjq0)

---

## GHL Workflow IDs

| Env Var | Workflow Name | ID |
|---------|---------------|----|
| `HOT_SELLER_WORKFLOW_ID` | Hot Seller | `577d56c4-28af-4668-8d84-80f5db234f48` |
| `WARM_SELLER_WORKFLOW_ID` | Bot Activation (fka Seller Bot Trigger) | `64b82875-89fb-4e67-807c-ceba2116b838` |
| `HOT_BUYER_WORKFLOW_ID` | Bot Activation (fka Buyer Bot Trigger — DELETED) | `64b82875-89fb-4e67-807c-ceba2116b838` |
| `WARM_BUYER_WORKFLOW_ID` | Warm Buyer / Agent Notify | `f3fc268b-5f16-4854-af28-200024cb3c8b` |
| `NOTIFY_AGENT_WORKFLOW_ID` | Agent Notification | `f3fc268b-5f16-4854-af28-200024cb3c8b` |

> **2026-02-27 consolidation**: "Jorge — Seller Bot Trigger" (64b82875) and "Jorge — Buyer Bot
> Trigger" (1ea9197e) were merged into **"Jorge — Bot Activation"** (64b82875). The Buyer Bot
> Trigger workflow has been deleted. HOT_BUYER_WORKFLOW_ID now points to Bot Activation.
>
> Note: WARM_BUYER and NOTIFY_AGENT currently share the same ID. If Jorge creates a dedicated
> warm-buyer nurture workflow, update WARM_BUYER_WORKFLOW_ID separately.

---

## DTS Campaign Workflow IDs (CC-Patterned, Jorge's Own Location)

> **Note**: CC (Closer Control) is used as a **template reference**, not a linked location.
> Jorge must create equivalent workflows in his own GHL location and paste those IDs here
> and into the Render dashboard env vars. The CC template IDs are listed for reference only
> and will NOT work in Jorge's location.

| Env Var | Workflow Type | CC Template ID (ref only) | Trigger Condition |
|---------|---------------|--------------------------|-------------------|
| `CC_NEGATIVE_CONVO_WORKFLOW_ID` | Negative Conversation Added | `70524142-fdea-457d-97c6-aeaa9b8a7b85` | Angry/frustrated/disappointed sentiment |
| `CC_GHOSTING_WORKFLOW_ID` | DTS - Ghosting Campaign | `7174d3dc-2c95-418c-8bad-3dcedb0ba5fa` | Contact ghosts (no reply) |
| `CC_COLD_CAMPAIGN_WORKFLOW_ID` | DTS - Cold Campaign | `f66c0661-80b9-4aa4-97e7-95063df72f79` | Seller temperature == cold |
| `CC_10DIH_WORKFLOW_ID` | DTS - 10 Days in Heaven | `c946fc0d-29ca-4d3d-b3a0-33e5df9a8681` | First failed call / cold seller |
| `CC_INBOUND_SELLER_WORKFLOW_ID` | DTS - Inbound Seller Lead Email | `bec3f293-665f-4b30-a524-5964620dd75c` | New inbound seller lead (first message) |
| `CC_REJECTED_OFFER_WORKFLOW_ID` | DTS - Rejected Offer Campaign | `42a36bf2-fbec-478b-a0ee-af63e8b16d7e` | Offer rejected (manual trigger) |
| `CC_UNSTALE_LEAD_WORKFLOW_ID` | Un-Stale Lead Workflow | `f81f593f-8cff-4309-8864-b1fa4d779574` | Ghosted contact re-engages |
| `CC_SELLER_DISPO_WORKFLOW_ID` | Seller Disposition Changed | `57884662-61e8-4b56-bd1d-4eda63600bea` | Seller temp transitions to hot/warm |
| `CC_AI_TAG_WORKFLOW_ID` | AI Tag Workflow | `47fc0922-dae1-48d1-863f-a62bbc0c4e60` | AI tag added (manual trigger) |
| `CC_AI_OFF_TAG_WORKFLOW_ID` | AI Assistant Off | `bb7cb261-70ab-43d6-8094-ba82e2d4ac6b` | Bot session ends / opt-out detected |

**Setup**: Jorge creates these workflows in his GHL location → copies IDs into Render dashboard.
**Deduplication**: Redis key `cc_wf_enrolled:{contact_id}:{workflow_id[:8]}` (7-day TTL) prevents
duplicate enrollments.

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
| Bot Activation (handles both Seller + Buyer tags) | `https://jorge-realty-ai-xxdf.onrender.com/api/ghl/tag-webhook` |
