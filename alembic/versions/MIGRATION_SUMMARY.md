# A/B Testing Tables Migration Summary

## Migration File Created
**Filename:** `2026_02_07_001_add_ab_testing_tables.py`
**Revision ID:** `001`
**Date:** 2026-02-07

## Tables Migrated

### 1. `ab_experiments`
- **Purpose:** A/B experiment definition
- **Columns:** id, experiment_name, description, hypothesis, target_bot, metric_type, minimum_sample_size, status, started_at, completed_at, default_traffic_split, winner_variant, statistical_significance, created_at, updated_at, created_by
- **Indexes:**
  - `idx_experiment_name` (unique)
  - `idx_experiment_status`
  - `idx_experiment_target_bot`
  - `idx_experiment_created_at`
- **Constraints:** Unique constraint on experiment_name

### 2. `ab_variants`
- **Purpose:** A/B test variant configuration
- **Columns:** id, experiment_id, variant_name, variant_label, description, response_template, system_prompt, config_overrides, traffic_weight, impressions, conversions, conversion_rate, total_value, confidence_interval_lower, confidence_interval_upper, is_control, created_at, updated_at
- **Indexes:**
  - `idx_variant_experiment`
  - `idx_variant_name`
- **Foreign Keys:** experiment_id → ab_experiments.id (CASCADE DELETE)
- **Constraints:**
  - Unique constraint on (experiment_id, variant_name)
  - Check constraint: traffic_weight >= 0 AND traffic_weight <= 1
  - Check constraint: conversion_rate >= 0 AND conversion_rate <= 1

### 3. `ab_assignments`
- **Purpose:** User-to-variant assignment tracking
- **Columns:** id, experiment_id, variant_id, user_id, session_id, assigned_at, bucket_value, has_converted, converted_at, metadata
- **Indexes:**
  - `idx_assignment_experiment`
  - `idx_assignment_user`
  - `idx_assignment_converted`
- **Foreign Keys:**
  - experiment_id → ab_experiments.id
  - variant_id → ab_variants.id
- **Constraints:** Unique constraint on (experiment_id, user_id)

### 4. `ab_metrics`
- **Purpose:** Conversion metrics per variant
- **Columns:** id, experiment_id, variant_id, assignment_id, event_type, event_value, event_data, event_timestamp, source, session_context, created_at
- **Indexes:**
  - `idx_metric_experiment`
  - `idx_metric_variant`
  - `idx_metric_event_type`
  - `idx_metric_timestamp`
- **Foreign Keys:**
  - experiment_id → ab_experiments.id
  - variant_id → ab_variants.id
  - assignment_id → ab_assignments.id

## Additional Database Objects

### ENUM Type
- **Name:** `experiment_status`
- **Values:** draft, active, paused, completed, archived

## Migration Features

### Upgrade Function
- Creates ENUM type `experiment_status`
- Creates all 4 tables in correct order (respecting foreign key dependencies)
- Creates all indexes
- Creates all constraints (unique, check, foreign keys)

### Downgrade Function
- Drops tables in reverse order (respecting foreign key dependencies)
- Drops all indexes
- Drops ENUM type

## Validation

✅ Migration file loads successfully with Alembic
✅ All tables from `ab_testing_schema.py` are included
✅ All foreign keys, indexes, and constraints are present
✅ Migration is reversible (downgrade function is complete)
✅ Follows existing code conventions (snake_case, PascalCase)
✅ Maintains backward compatibility (no breaking changes to existing tables)

## Testing Status

⚠️ **Migration not tested against live database**
- Reason: Docker daemon not running
- PostgreSQL database required for testing
- Migration file is syntactically correct and validated

## How to Test (When Database is Available)

1. Start PostgreSQL database:
   ```bash
   docker-compose -f docker-compose.db.yml up -d
   ```

2. Set DATABASE_URL environment variable:
   ```bash
   export DATABASE_URL="postgresql://admin:admin_password@localhost:5432/enterprise_hub"
   ```

3. Run migration:
   ```bash
   alembic upgrade head
   ```

4. Verify tables created:
   ```bash
   psql $DATABASE_URL -c "\dt ab_*"
   ```

5. Test rollback:
   ```bash
   alembic downgrade -1
   ```

6. Re-apply migration:
   ```bash
   alembic upgrade head
   ```

## Notes

- Migration uses PostgreSQL-specific features (UUID, JSONB, ENUM)
- Default values are set appropriately for all columns
- Foreign key cascades are configured (experiment_id in ab_variants has CASCADE DELETE)
- All indexes are non-unique except where specified
- Check constraints ensure data integrity for traffic_weight and conversion_rate
