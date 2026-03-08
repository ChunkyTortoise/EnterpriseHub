# Release Checklist: Integration Accelerator v2

## API & Contracts

- [ ] `/api/v2/intake/diagnose` returns typed response.
- [ ] `/api/v2/workflows/bootstrap` returns typed `IntegrationBlueprint`.
- [ ] `/api/v2/reports/proof-pack` handles idempotent regeneration.
- [ ] `/api/v2/reports/{engagement_id}` includes audit trail.

## Validation & Failure Modes

- [ ] Missing engagement returns 404.
- [ ] Missing KPI source returns 400.
- [ ] Empty event stream returns 400.
- [ ] Partial telemetry appears in proof-pack risks.

## Testing

- [ ] Run `portal_api/tests/test_integration_accelerator_api.py`.
- [ ] Verify OpenAPI snapshot is refreshed and committed.

## Delivery Assets

- [ ] `scripts/smoke_productization.sh` runs against local API.
- [ ] `docs/productization_api.md` reflects current schema.
- [ ] `docs/client_onboarding_runbook.md` shared with delivery team.
- [ ] Proof-pack templates are ready for client-facing output.
