"""
GoHighLevel (GHL) Integration Module for EnterpriseHub

Unified webhook handling for Lead, Seller, and Buyer bots with:
- Signature validation (HMAC/RSA)
- Event deduplication (24h TTL)
- Exponential backoff retry (6 attempts + DLQ)
- Bidirectional state sync

## Structure

```
ghl_integration/
├── __init__.py              # Module exports
├── router.py                # FastAPI webhook router
├── validators.py            # Signature validation
├── deduplicator.py        # Event deduplication
├── retry_manager.py         # Retry logic + DLQ
├── state_sync.py           # Bidirectional sync
├── integration.py          # FastAPI integration helpers
└── handlers/
    ├── __init__.py
    ├── lead_handlers.py     # Lead bot webhooks
    ├── seller_handlers.py   # Seller bot webhooks
    └── buyer_handlers.py    # Buyer bot webhooks
```

## Quick Start

```python
from fastapi import FastAPI
from ghl_integration import initialize_ghl_integration

app = FastAPI()

@app.on_event("startup")
async def startup():
    await initialize_ghl_integration(app)
```

## Webhook Endpoints

All bots use unified endpoints:

```
POST /ghl/webhook/{bot_type}/{event_type}
```

### Lead Bot
- `POST /ghl/webhook/lead/new-lead` - ContactCreate
- `POST /ghl/webhook/lead/lead-response` - ConversationMessageCreate
- `POST /ghl/webhook/lead/lead-update` - ContactUpdate

### Seller Bot
- `POST /ghl/webhook/seller/seller-inquiry` - ContactCreate (seller tags)
- `POST /ghl/webhook/seller/listing-created` - OpportunityCreate
- `POST /ghl/webhook/seller/seller-response` - ConversationMessageCreate

### Buyer Bot
- `POST /ghl/webhook/buyer/buyer-inquiry` - ContactCreate (buyer tags)
- `POST /ghl/webhook/buyer/buyer-response` - ConversationMessageCreate
- `POST /ghl/webhook/buyer/pipeline-change` - PipelineStageChange

## Environment Variables

```bash
# Required
GHL_API_KEY=your_api_key
GHL_LOCATION_ID=your_location_id

# Optional but recommended
GHL_WEBHOOK_SECRET=webhook_signing_secret
GHL_SELLER_PIPELINE_IDS=pipe1,pipe2
GHL_BUYER_PIPELINE_IDS=pipe3,pipe4

# Development only
GHL_SKIP_SIGNATURE_VERIFICATION=true
```

## Retry Strategy

1. Immediate: 3 attempts (1s, 2s, 4s delays)
2. Delayed: 3 attempts (1min, 5min, 15min)
3. DLQ: After 6 failures, stored for manual review

## State Sync

Bidirectional sync keeps GHL and bot database in sync:
- GHL contact changes → Local DB updates
- Local analysis results → GHL custom fields
- Pipeline stage changes → Bot qualification stages

## Testing

```bash
# Run GHL integration tests
pytest tests/ghl_integration/ -v

# Run specific test file
pytest tests/ghl_integration/test_router.py -v
```
