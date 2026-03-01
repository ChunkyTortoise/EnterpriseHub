# EnterpriseHub 90-Day Audit-to-Revenue Execution Spec

## Operating Constraints
- Model: hybrid (services cashflow + recurring pilot)
- Segment: SMB real estate teams (2-20 agents)
- Capacity: solo founder, 40-50h/week
- Revenue target: $30K-$60K in 90 days

## Phase 1 (Weeks 1-2): Trust Stabilization
- Parse gate in CI via `scripts/ci/compile_check.py`
- No-mock guard for v2 production routes via `scripts/ci/no_mock_in_prod.py`
- Weekly proof-pack generation via `scripts/generate_metrics_snapshot.py`
- Revenue artifact QA via `scripts/ci/revenue_ops_qa.py`

## Phase 2 (Weeks 2-6): v2 Revenue APIs
- `/api/v2/billing/subscriptions/{location_id}`
- `/api/v2/prediction/deal-outcome/{deal_id}`
- `/api/v2/customer-journeys/{lead_id}`
- `/api/v2/property-intelligence/{property_id}`
- `/api/v2/sms-compliance/{location_id}`
- `/api/v2/market-intelligence/recommendations/stream`

### Contract Guarantees
- `source`: `database|cache|live_provider`
- Standardized error payload with `correlation_id`
- `X-Data-Freshness` and `X-Response-Source` headers
- SSE event types: `start`, `token`, `complete`, `error`

## Phase 3 (Weeks 1-5, parallel): Productized Offers
- `proposals/starter-sprint-one-pager.md`
- `proposals/growth-sprint-one-pager.md`
- `proposals/scale-sprint-one-pager.md`
- `proposals/SOW_TEMPLATE.md`
- `proposals/demo_scripts.md`

## Phase 4 (Weeks 2-12): Sales Execution
- Single source of truth: `reports/proposal_pipeline_tracker.csv`
- Weekly cadence target: 40 contacts, 8 qualified conversations, 2-3 proposals
- KPI and proof-pack update via `reports/metrics_snapshot.md`

## Phase 5 (Weeks 6-12): Recurring Pilot
- Offer: Lead Response Copilot
- Manual onboarding, recurring usage tracking on v2 routes
- Pilot target: 3 customers, $1.5K-$4K MRR
