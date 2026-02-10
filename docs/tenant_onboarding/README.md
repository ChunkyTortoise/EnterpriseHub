# Tenant Bootstrap Automation

Use the bootstrap script to register a subaccount and generate a completion checklist.

## Command

```bash
python scripts/tenant_bootstrap.py \
  --tenant-name "Acme Realty" \
  --location-id "loc_acme_001" \
  --anthropic-key "sk-ant-..." \
  --ghl-key "ghl-or-oauth-token" \
  --calendar-id "cal_acme_primary" \
  --confirmation-strategy sms_only
```

## Notes

- Default checklist output: `docs/tenant_onboarding/<location_id>_checklist.md`
- Use `--dry-run` to validate inputs and generate the checklist without writing tenant credentials.
- Use `--force` only when intentionally replacing an existing tenant config file.
- If `--confirmation-strategy sms_and_email` is used, provide `--confirmation-email-workflow-id`.

## Expected Artifacts

- `data/tenants/<location_id>.json`
- `docs/tenant_onboarding/<location_id>_checklist.md`

## Validation Gate

Do not mark onboarding complete until all 10 required checklist steps are done and evidence is captured.
