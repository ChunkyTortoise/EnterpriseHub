# Database Migration & Schema Review

**Reviewed:** 2026-03-19
**Scope:** All 14 Alembic migrations + `transaction_schema.py` + key ORM models
**Service focus:** `transaction_service.py` query patterns on `transaction_id`, `milestone_type`, `contact_id`

---

## Migration Inventory

14 migration files in a single linear chain. Revision IDs are inconsistent across the chain (described below under ordering issues).

| # | File | Revision ID | down_revision | Tables Created |
|---|------|------------|---------------|---------------|
| 1 | `2026_02_07_001_add_ab_testing_tables.py` | `001` | `None` (root) | ab_experiments, ab_variants, ab_assignments, ab_metrics |
| 2 | `2026_02_08_002_add_jorge_metrics_tables.py` | `002` | `001` | jorge_bot_interactions, jorge_handoff_events, jorge_performance_operations, jorge_alert_rules, jorge_alerts |
| 3 | `2026_02_08_003_add_handoff_outcomes_table.py` | `003` | `002` | jorge_handoff_outcomes |
| 4 | `2026_02_10_004_add_abandonment_events_table.py` | `004` | `003` | abandonment_events |
| 5 | `2026_02_10_005_add_lead_source_metrics_tables.py` | `005` | `004` | lead_source_contacts, lead_source_conversions, lead_source_metrics, lead_source_costs |
| 6 | `2026_02_10_006_add_objection_events_table.py` | `006` | `005` | objection_events |
| 7 | `2026_02_10_007_add_ab_promotion_events_table.py` | `007` | `006` | ab_promotion_events |
| 8 | `2026_02_10_008_add_buyer_personas_table.py` | `008` | `007` | buyer_personas |
| 9 | `2026_02_10_009_add_sentiment_tables.py` | `2026_02_10_009` | `2026_02_10_008` | conversation_sentiments, sentiment_escalations |
| 10 | `2026_02_10_010_add_composite_lead_scores_table.py` | `2026_02_10_010` | `2026_02_10_009` | composite_lead_scores |
| 11 | `2026_02_10_011_add_ghl_workflow_tables.py` | `2026_02_10_011` | `2026_02_10_010` | ghl_workflow_operations, pipeline_stage_history, bot_appointments |
| 12 | `2026_02_10_012_add_churn_tables.py` | `2026_02_10_012` | `2026_02_10_011` | churn_risk_assessments, recovery_actions, recovery_outcomes |
| 13 | `2026_03_03_013_add_revenue_reporting_tables.py` | `2026_03_03_013` | `2026_02_10_012` | outcome_events, pilot_kpi_records |
| 14 | `2026_03_04_014_add_sdr_tables.py` | `2026_03_04_014` | `2026_03_03_013` | sdr_prospects, sdr_outreach_sequences, sdr_outreach_touches, sdr_objection_logs |

**Total tables created by migrations: 32**
**Tables in `transaction_schema.py` (not in migrations): 6** — `real_estate_transactions`, `transaction_milestones`, `transaction_events`, `transaction_predictions`, `transaction_celebrations`, `transaction_templates`, `transaction_metrics`

---

## Indexing Analysis

### Missing Indexes (Critical)

#### 1. `transaction_id` (string lookup) — `real_estate_transactions`
`transaction_service.py` queries `real_estate_transactions` by the `transaction_id` **string column** (e.g., "TXN-20260319-abc123") on virtually every request:
```python
select(RealEstateTransaction).where(RealEstateTransaction.transaction_id == transaction_id)
```
The column has a `UNIQUE` constraint, which creates an implicit B-tree index in PostgreSQL, so this is **covered**. However, the constraint is declared only via `unique=True` on the column — there is no explicit named index for observability or query hint purposes.

#### 2. `milestone_type` composite with `transaction_id` — `transaction_milestones`
`transaction_schema.py` defines `idx_milestone_sequence` on `(transaction_id, order_sequence)` and `idx_milestone_type` on `milestone_type` alone, but `transaction_service.py` and the `milestone_timeline_view` query by `milestone_type` **scoped to a transaction**:
```sql
WHERE transaction_id = ... AND milestone_type = '...'
```
A composite index `(transaction_id, milestone_type)` is missing. With 12 milestones per transaction this is low-cardinality today but becomes significant at scale.

#### 3. `contact_id` — `jorge_handoff_outcomes`
Migration 003 (`jorge_handoff_outcomes`) indexes `(source_bot, target_bot)` and `timestamp` but **has no index on `contact_id`**, even though the service retrieves handoff history per contact for circular-prevention and rate-limiting checks. This is a critical lookup path.

#### 4. `contact_id` — `outcome_events` (migration 013)
`outcome_events` indexes `(tenant_id, timestamp DESC)` but **has no index on `lead_id`** (the column that maps to contact_id in this table). Queries filtering by lead are unindexed.

#### 5. `contact_id` / `enrolled_at` composite — `sdr_prospects`
The scheduler queries `sdr_prospects` by `location_id` filtered to recently enrolled records for batch cadence processing. There is no composite index on `(location_id, enrolled_at)`. The current `idx_sdr_prospects_location_id` forces a full index scan + sort.

#### 6. `replied_at` — `sdr_outreach_touches`
Reply analytics (`reply_rate`, `conversion_by_step`) aggregate on `replied_at IS NOT NULL` grouped by step. There is no partial index on `replied_at` or `(step, replied_at)`.

#### 7. `timestamp` (Float epoch) — `jorge_bot_interactions`, `jorge_handoff_events`, `jorge_performance_operations`, `jorge_alerts`
These tables store Unix timestamps as `Float` rather than `TIMESTAMPTZ`. Range queries (e.g., "last 24 hours") work correctly but are less efficient than native timestamp types and cannot use PostgreSQL's built-in date truncation functions efficiently. The indexes exist, but the type choice limits query expressiveness.

#### 8. `transaction_id` (string) — `transaction_service.py` raw SQL queries
The `get_milestone_timeline` and `get_dashboard_summary` methods use raw f-string SQL against views that do a subquery:
```sql
WHERE transaction_id = (
    SELECT id FROM real_estate_transactions WHERE transaction_id = '{transaction_id}'
)
```
This double-lookup pattern relies on the `transaction_id` unique index on the parent table being used. It works but is one query more than necessary; the ORM models already have `idx_transaction_ghl_lead` but no named index specifically for this pattern.

### Existing Indexes (Complete Inventory)

**`real_estate_transactions`** (from `transaction_schema.py`):
- `idx_transaction_ghl_lead` (ghl_lead_id)
- `idx_transaction_status` (status)
- `idx_transaction_progress` (progress_percentage)
- `idx_transaction_health` (health_score)
- `idx_transaction_expected_closing` (expected_closing_date)
- `idx_transaction_delay_risk` (delay_risk_score)
- Implicit unique index on `transaction_id`

**`transaction_milestones`**:
- `idx_milestone_transaction` (transaction_id)
- `idx_milestone_type` (milestone_type)
- `idx_milestone_status` (status)
- `idx_milestone_sequence` (transaction_id, order_sequence) — composite, good
- `idx_milestone_target_completion` (target_completion_date)

**`transaction_events`**:
- `idx_event_transaction` (transaction_id)
- `idx_event_type` (event_type)
- `idx_event_timestamp` (event_timestamp)
- `idx_event_priority` (priority)
- `idx_event_client_visible` (client_visible, event_timestamp) — composite, good

**`transaction_predictions`**:
- `idx_prediction_transaction`, `idx_prediction_type`, `idx_prediction_confidence`, `idx_prediction_risk`, `idx_prediction_date`

**`transaction_celebrations`**:
- `idx_celebration_transaction`, `idx_celebration_trigger`, `idx_celebration_type`, `idx_celebration_triggered`
- `idx_celebration_engagement` (client_viewed, engagement_duration)

**`ab_experiments`**: idx on name (unique), status, target_bot, created_at
**`ab_variants`**: idx on experiment_id, variant_name
**`ab_assignments`**: idx on experiment_id, user_id, has_converted
**`ab_metrics`**: idx on experiment_id, variant_id, event_type, event_timestamp
**`jorge_bot_interactions`**: idx on timestamp, bot_type
**`jorge_handoff_events`**: idx on timestamp only — **missing contact_id**
**`jorge_performance_operations`**: idx on timestamp, bot_name
**`jorge_alert_rules`**: idx on name (unique)
**`jorge_alerts`**: idx on triggered_at, rule_name
**`jorge_handoff_outcomes`**: idx on (source_bot, target_bot), timestamp — **missing contact_id**
**`abandonment_events`**: unique idx on contact_id, composite (location_id, last_contact_timestamp), current_stage
**`lead_source_contacts`**: contact_id (unique), source_name, stage, created_at
**`lead_source_conversions`**: contact_id, stage, created_at
**`lead_source_metrics`**: source_name (unique), conversion_rate, total_revenue
**`lead_source_costs`**: source_name, date, unique (source_name, date)
**`objection_events`**: contact_id, objection_type, objection_category (inline), composite (contact_id, objection_category), (objection_type, outcome), created_at
**`ab_promotion_events`**: experiment_id, canary_status, created_at, composite (experiment_id, canary_status)
**`buyer_personas`**: lead_id (unique), persona_type, confidence, created_at
**`conversation_sentiments`**: conversation_id, sentiment, escalation_level
**`sentiment_escalations`**: contact_id, escalation_level
**`composite_lead_scores`**: contact_id, classification, total_score, calculated_at
**`ghl_workflow_operations`**: contact_id, operation_type, status
**`pipeline_stage_history`**: contact_id, to_stage, transitioned_at
**`bot_appointments`**: contact_id, status, start_time
**`churn_risk_assessments`**: contact_id, risk_level, assessed_at DESC
**`recovery_actions`**: contact_id, status, scheduled_at
**`recovery_outcomes`**: recovery_action_id, contact_id, outcome
**`outcome_events`**: composite (tenant_id, timestamp DESC) — **missing lead_id**
**`pilot_kpi_records`**: composite (tenant_id, week_start DESC) — covered by PK
**`sdr_prospects`**: contact_id, location_id
**`sdr_outreach_sequences`**: contact_id, location_id, next_touch_at
**`sdr_outreach_touches`**: contact_id, sent_at
**`sdr_objection_logs`**: contact_id

---

## Data Integrity Issues

### 1. `contacts` and `conversations` tables not created by any migration — CRITICAL
Migrations 009–012 reference `ForeignKey("contacts.id", ondelete="CASCADE")` and `ForeignKey("conversations.id", ondelete="CASCADE")` extensively:
- `conversation_sentiments.conversation_id → conversations.id`
- `sentiment_escalations.conversation_id → conversations.id`
- `sentiment_escalations.contact_id → contacts.id`
- `composite_lead_scores.contact_id → contacts.id`
- `ghl_workflow_operations.contact_id → contacts.id`
- `pipeline_stage_history.contact_id → contacts.id`
- `bot_appointments.contact_id → contacts.id`
- `churn_risk_assessments.contact_id → contacts.id`
- `recovery_actions.contact_id → contacts.id`
- `recovery_outcomes.contact_id → contacts.id`

**Neither `contacts` nor `conversations` is created in any migration file in `alembic/versions/`.** These tables must be pre-existing in the database (likely created outside Alembic, or by a pre-migration-001 schema). There is no migration that establishes these base tables, so:
- A fresh `alembic upgrade head` on an empty database will fail at migration 009 with a FK constraint violation
- The Alembic chain has an undocumented dependency on out-of-band schema
- `alembic env.py` sets `target_metadata = None`, so autogenerate cannot detect or warn about this drift

### 2. `transaction_schema.py` tables have no corresponding Alembic migration — HIGH
The 7 tables in `ghl_real_estate_ai/database/transaction_schema.py` (`real_estate_transactions`, `transaction_milestones`, `transaction_events`, `transaction_predictions`, `transaction_celebrations`, `transaction_templates`, `transaction_metrics`) are defined as SQLAlchemy ORM models with full `__table_args__` but have no corresponding Alembic migration. They rely on `Base.metadata.create_all()` called separately, which bypasses Alembic's version tracking entirely. A database created via `alembic upgrade head` will be missing these 7 tables; a database created by calling `create_all()` directly will be missing the 32 migration-managed tables.

### 3. Dual-schema creation pattern — HIGH
There are two incompatible schema creation mechanisms running in parallel:
1. Alembic migrations (14 files, 32 tables)
2. `transaction_schema.py` `Base.create_all()` / raw SQL (7 tables + 2 views)

These two `Base` objects (`declarative_base()` from `transaction_schema.py` vs. `Base` from `ghl_real_estate_ai/models/base.py`) are separate. Cross-table foreign keys between these two groups are impossible without careful initialization ordering.

### 4. Nullable `contact_id` in analytics tables — MEDIUM
Several analytics tables store `contact_id` as `VARCHAR` or `String` without FK enforcement to a canonical contacts table, because the table doesn't exist in migrations. This means:
- `jorge_handoff_outcomes.contact_id` (String 100, NOT NULL) — no FK
- `objection_events.contact_id` (String 255, NOT NULL, inline index) — no FK
- `buyer_personas.lead_id` (String 255, NOT NULL) — no FK
- `abandonment_events.contact_id` (String 100, NOT NULL, unique) — no FK
- `lead_source_contacts.contact_id` (String 255, NOT NULL, unique) — no FK

Without FK constraints, orphaned rows accumulate silently when contacts are deleted from GHL. Cascade deletes that work correctly for migration-012 tables (`churn_risk_assessments`) will not fire for these string-keyed tables.

### 5. Revision ID inconsistency — MEDIUM
Migrations 001–008 use short numeric IDs (`001`, `002`, ... `008`). Starting at migration 009, IDs switch to datestamp format (`2026_02_10_009`, etc.). Alembic stores these as-is in the `alembic_version` table. The chain is still linear and correct, but the inconsistency:
- Breaks the convention of unique, non-guessable revision IDs
- Short IDs like `001` could collide with revision IDs in other Alembic branches if multiple developers work on features simultaneously
- Downgrade scripts for 001–008 use `op.drop_index("name", "table")` which is the correct two-argument form, but the style differs from 009+ which uses `op.drop_index("name", table_name="table")`

### 6. `ab_assignments` foreign keys missing `ondelete` — LOW
`ab_assignments` has FKs to `ab_experiments.id` and `ab_variants.id` without `ondelete="CASCADE"`. If an experiment is deleted, assignments will be orphaned (FK violation on delete). The child table `ab_metrics` also lacks cascade. Only `ab_variants → ab_experiments` has `ondelete="CASCADE"`.

### 7. `sdr_outreach_sequences` missing `ondelete` — LOW
The FK `prospect_id → sdr_prospects.id` in migration 014 has no `ondelete` clause (defaults to RESTRICT in PostgreSQL). The ORM model in `sdr_models.py` uses `cascade="all, delete-orphan"` at the relationship level, which only works when deletion goes through the ORM session. Direct SQL deletes of `sdr_prospects` rows will fail or be blocked, inconsistent with the explicit CASCADE defined at the DB level for other tables.

### 8. Float used for financial values — LOW
`purchase_price`, `loan_amount`, `down_payment`, `estimated_closing_costs` in `real_estate_transactions` are `Float` (IEEE 754 double), not `NUMERIC(precision, scale)`. Floating-point arithmetic is inappropriate for currency — 0.1 + 0.2 != 0.3. Migration-managed tables correctly use `sa.Numeric(precision=5, scale=2)` for scores. The transaction schema inconsistently uses `Float` throughout.

---

## Constraint Recommendations

### 1. Add `CHECK` constraints for enum-like string columns (High Priority)
Several columns store bounded string enums but have no CHECK constraints:
- `jorge_handoff_outcomes.outcome` — should be CHECK `IN ('success', 'failure', 'timeout', ...)`
- `abandonment_events.current_stage` — should be CHECK `IN ('24h', '3d', '7d', '14d', '30d')`
- `recovery_actions.status` — should be CHECK `IN ('pending', 'sent', 'delivered', 'failed')`
- `bot_appointments.status` — should be CHECK `IN ('scheduled', 'confirmed', 'cancelled', 'completed')`
- `sdr_objection_logs.outcome` — should be CHECK `IN ('sequence_continued', 'opted_out', 'qualified', 'paused')`

### 2. Add `NOT NULL` + `DEFAULT NOW()` for `updated_at` columns
Multiple tables have `updated_at TIMESTAMPTZ` defined as nullable with `server_default=NOW()` but no `onupdate` trigger and no NOT NULL constraint. Examples:
- `sdr_outreach_sequences.updated_at` — `nullable=True`, no `onupdate`
- `buyer_personas.updated_at` — nullable
- `abandonment_events.updated_at` — nullable

These columns will stay at their insert-time value unless the application explicitly sets them, making them unreliable for change tracking.

### 3. Add `UNIQUE` constraint to `jorge_handoff_outcomes` for idempotency
The Jorge handoff service has rate-limiting (3/hr, 10/day) enforced in application code. Adding a `UNIQUE (contact_id, source_bot, target_bot, timestamp::date)` or similar partial unique constraint would prevent double-recording at the DB level and simplify the application logic.

### 4. Make `outcome_events.tenant_id` + `lead_id` composite unique or add separate lead_id index
`outcome_events` is the revenue-reporting event log. Queries filter by `lead_id` but no index exists. Recommendation: `CREATE INDEX idx_outcome_events_lead_ts ON outcome_events (lead_id, timestamp DESC)`.

### 5. Formalize `contacts` and `conversations` tables in migrations
The missing base tables should either:
- Be added as a migration 000 that creates `contacts` and `conversations` with appropriate schema, OR
- Be documented explicitly with a guard in migration 009 that checks for table existence before adding FKs

Without this, `alembic upgrade head` is not idempotent on a fresh database.

---

## Performance Impact Estimates

| Issue | Tables Affected | Estimated Impact |
|-------|-----------------|-----------------|
| Missing `contact_id` index on `jorge_handoff_outcomes` | `jorge_handoff_outcomes` | Handoff rate-limiting check does seq scan. At 10K rows: ~5–20ms overhead per webhook. At 100K rows: 50–200ms, breaking <200ms SLA. |
| Missing `(transaction_id, milestone_type)` composite | `transaction_milestones` | Current 12-row-per-transaction table is trivial. At scale (1K+ transactions, 12K milestones): optimizer may not use existing single-column index. Low risk today. |
| Missing `lead_id` index on `outcome_events` | `outcome_events` | Revenue reporting dashboard queries are user-triggered (not hot path), but weekly KPI computation will degrade at >10K events. |
| Missing `(location_id, enrolled_at)` on `sdr_prospects` | `sdr_prospects` | SDR scheduler batch (cadence processing) runs on a timer. With >5K prospects per location, the batch query will seq scan location_id index then sort — adding 10–50ms per batch run. |
| Float vs NUMERIC for currency | `real_estate_transactions` | Functional issue, not performance. Rounding errors in `purchase_price` aggregations accumulate in `transaction_metrics` reporting. |
| `target_metadata = None` in env.py | All | Alembic autogenerate is disabled — schema drift between ORM models and DB cannot be detected. Running `alembic check` will always report "no new upgrade ops detected" even if models have diverged. |
| Dual `Base` / dual creation path | Transaction tables vs migration tables | Two independent schema managers. Cannot be unified in a single `alembic upgrade head` without refactoring `transaction_schema.py` into a migration. Risk: production deployments may miss transaction tables entirely if only `alembic upgrade head` is run. |

---

## Summary of Top Issues by Priority

| Priority | Issue | File |
|----------|-------|------|
| P0 | `contacts`/`conversations` not in migrations — `alembic upgrade head` fails on fresh DB | migrations 009–012 |
| P0 | `transaction_schema.py` 7 tables bypass Alembic entirely | `database/transaction_schema.py` |
| P1 | `jorge_handoff_outcomes` missing `contact_id` index | migration 003 |
| P1 | `outcome_events` missing `lead_id` index | migration 013 |
| P1 | `ab_assignments` / `ab_metrics` FKs missing `ondelete` cascade | migration 001 |
| P2 | `sdr_outreach_sequences` FK missing `ondelete` (ORM vs DB mismatch) | migration 014 / `sdr_models.py` |
| P2 | `updated_at` nullable and no `onupdate` in 4+ tables | migrations 004, 008, 014 |
| P2 | `Float` for currency in transaction schema | `transaction_schema.py` |
| P3 | Revision ID inconsistency (001–008 short IDs vs datestamp) | all migrations |
| P3 | `target_metadata = None` disables autogenerate drift detection | `alembic/env.py` |
| P3 | Missing CHECK constraints on bounded-string columns | migrations 003, 004, 011, 012, 014 |
