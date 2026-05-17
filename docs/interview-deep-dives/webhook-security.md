# Webhook Security Deep Dive

EnterpriseHub treats GoHighLevel webhook input as untrusted. The flagship path is `ghl_real_estate_ai/api/routes/webhook.py`, which attaches `require_ghl_webhook_signature` at the router boundary so webhook handlers inherit signature verification.

## What To Inspect

- Router-level dependency on `require_ghl_webhook_signature`.
- `GHLWebhookEvent` and `GHLTagWebhookEvent` request schemas.
- Failure behavior for invalid payloads, LLM timeouts, and downstream delivery errors.
- Background task wrappers that log delivery failures and apply failure tags.

## Current Limitation

The file is still large and mid-migration. The safe next step is to move `/webhook` and `/tag-webhook` into smaller modules after targeted signature tests are green.
