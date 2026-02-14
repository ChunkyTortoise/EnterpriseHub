# Stripe Environment Variable Migration Guide

## Overview
This document details the environment variable naming convention migration for Stripe price IDs in the EnterpriseHub codebase.

## Migration Summary

| Old Variable | New Variable |
|--------------|---------------|
| `STRIPE_PRICE_ID_STARTER` | `STRIPE_STARTER_PRICE_ID` |
| `STRIPE_PRICE_ID_PROFESSIONAL` | `STRIPE_PROFESSIONAL_PRICE_ID` |
| `STRIPE_PRICE_ID_ENTERPRISE` | `STRIPE_ENTERPRISE_PRICE_ID` |

### Annual Pricing Variables

| Old Variable | New Variable |
|--------------|---------------|
| `STRIPE_PRICE_ID_STARTER_ANNUAL` | `STRIPE_STARTER_ANNUAL_PRICE_ID` |
| `STRIPE_PRICE_ID_PROFESSIONAL_ANNUAL` | `STRIPE_PROFESSIONAL_ANNUAL_PRICE_ID` |
| `STRIPE_PRICE_ID_ENTERPRISE_ANNUAL` | `STRIPE_ENTERPRISE_ANNUAL_PRICE_ID` |

## Rationale
The new naming convention follows the project's established pattern:
- **Pattern**: `SERVICE_TIER_VARIABLE` (e.g., `STRIPE_STARTER_PRICE_ID`)
- **Consistency**: Aligns with other Stripe variables like `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`

## Implementation Details

### Code Changes
The environment variable mapping is handled in [`billing/stripe_client.py`](billing/stripe_client.py:486):

```python
env_var_map = {
    (PlanTier.STARTER, "month"): "STRIPE_STARTER_PRICE_ID",
    (PlanTier.STARTER, "year"): "STRIPE_STARTER_ANNUAL_PRICE_ID",
    (PlanTier.PROFESSIONAL, "month"): "STRIPE_PROFESSIONAL_PRICE_ID",
    (PlanTier.PROFESSIONAL, "year"): "STRIPE_PROFESSIONAL_ANNUAL_PRICE_ID",
    (PlanTier.ENTERPRISE, "month"): "STRIPE_ENTERPRISE_PRICE_ID",
    (PlanTier.ENTERPRISE, "year"): "STRIPE_ENTERPRISE_ANNUAL_PRICE_ID",
}
```

### Configuration
The template file [`.env.example`](.env.example:123) has been updated with the new naming convention:

```bash
# Monthly Prices
STRIPE_STARTER_PRICE_ID=price_starter_monthly_id
STRIPE_PROFESSIONAL_PRICE_ID=price_professional_monthly_id
STRIPE_ENTERPRISE_PRICE_ID=price_enterprise_monthly_id

# Annual Prices
STRIPE_STARTER_ANNUAL_PRICE_ID=price_starter_annual_id
STRIPE_PROFESSIONAL_ANNUAL_PRICE_ID=price_professional_annual_id
STRIPE_ENTERPRISE_ANNUAL_PRICE_ID=price_enterprise_annual_id
```

## Migration Steps

### For Production Environments
1. **Backup existing configuration**
2. **Update `.env` file**: Replace old variable names with new ones
3. **Restart services**: Ensure new environment variables are loaded
4. **Verify subscriptions**: Confirm pricing tiers work correctly

### Example Migration (bash)
```bash
# Create backup
cp .env .env.backup

# Replace old variable names with new ones
sed -i '' 's/STRIPE_PRICE_ID_STARTER/STRIPE_STARTER_PRICE_ID/g' .env
sed -i '' 's/STRIPE_PRICE_ID_PROFESSIONAL/STRIPE_PROFESSIONAL_PRICE_ID/g' .env
sed -i '' 's/STRIPE_PRICE_ID_ENTERPRISE/STRIPE_ENTERPRISE_PRICE_ID/g' .env
sed -i '' 's/STRIPE_PRICE_ID_STARTER_ANNUAL/STRIPE_STARTER_ANNUAL_PRICE_ID/g' .env
sed -i '' 's/STRIPE_PRICE_ID_PROFESSIONAL_ANNUAL/STRIPE_PROFESSIONAL_ANNUAL_PRICE_ID/g' .env
sed -i '' 's/STRIPE_PRICE_ID_ENTERPRISE_ANNUAL/STRIPE_ENTERPRISE_ANNUAL_PRICE_ID/g' .env
```

## Rollback Plan
If issues arise, restore from `.env.backup` and investigate before retrying the migration.

## Related Files
- [`billing/stripe_client.py`](billing/stripe_client.py) - Price ID resolution
- [`.env.example`](.env.example) - Environment template
- [`billing/subscription_service.py`](billing/subscription_service.py) - Subscription management

---
*Documented: 2026-02-13*  
*Migration for changeset: 417 files*
