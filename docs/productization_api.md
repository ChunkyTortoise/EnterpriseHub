# AI Integration Accelerator API (v2)

## Endpoints

### `POST /api/v2/intake/diagnose`
Create or update an engagement intake diagnosis.

### `POST /api/v2/workflows/bootstrap`
Generate a vertical-aware integration blueprint for an existing engagement.

### `POST /api/v2/reports/proof-pack`
Generate a 14-day (or configurable) proof pack with KPI deltas and ROI estimate.

### `GET /api/v2/reports/{engagement_id}`
Fetch generated proof pack plus audit trail.

## Supported Vertical Profiles

- `real_estate`
- `professional_services`
- `ecommerce_voice`

## Data Contracts

Key shared types:

- `VerticalProfile`
- `EngagementStatus` (`draft`, `active`, `validating`, `delivered`)
- `IntegrationBlueprint`
- `ProofPack`

## Failure Modes

- Missing engagement: `404 engagement_not_found`
- Missing proof pack: `404 report_not_found`
- Empty event stream: `400 invalid_proof_pack_request`
- Missing KPI source: `400 invalid_proof_pack_request`
- KPI schema mismatch: `400 kpi_validation_failed`

## Idempotency

`POST /api/v2/reports/proof-pack` is idempotent for identical payloads per engagement.  
If a payload fingerprint matches an existing report, the stored report is returned unchanged.
