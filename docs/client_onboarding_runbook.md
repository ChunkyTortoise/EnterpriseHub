# Client Onboarding Runbook: AI Integration Accelerator

## 1. Discovery Intake (Day 0)

1. Collect client goals, target workflows, and existing tooling.
2. Choose vertical profile (`real_estate`, `professional_services`, `ecommerce_voice`).
3. Run `POST /api/v2/intake/diagnose`.

## 2. Blueprint Setup (Day 1-2)

1. Confirm channels and CRM field mappings with client stakeholders.
2. Run `POST /api/v2/workflows/bootstrap`.
3. Share generated blueprint and finalize escalation rules.

## 3. Baseline & Instrumentation (Day 3-5)

1. Capture baseline KPI snapshot.
2. Validate event feed quality and source completeness.
3. Confirm no missing KPI sources for the 14-day window.

## 4. Delivery Window (Day 6-14)

1. Execute automation sprint.
2. Monitor KPI streams daily.
3. Track incidents in audit notes.

## 5. Proof Pack Delivery (Day 14)

1. Run `POST /api/v2/reports/proof-pack`.
2. Run `GET /api/v2/reports/{engagement_id}`.
3. Deliver executive summary + KPI deltas + ROI estimate.

## 6. Expansion Decision

1. If KPI movement is positive, expand scope to secondary workflows.
2. If KPI movement is flat, run remediation sprint with tightened escalation and instrumentation.
