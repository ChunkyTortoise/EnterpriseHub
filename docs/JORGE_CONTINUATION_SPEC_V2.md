# Jorge Lead, Seller, and Buyer Bots
## Continuation and Improvement Spec (V2)

Version: 2.0  
Date: 2026-02-09  
Owner: Engineering  
Status: Ready for implementation

---

## 1) Purpose

Define the next development phase for Jorge's GHL-native bot system so the team can:

- Keep shipping against the original Path B scope (webhook/backend-only, no external chat UI).
- Tighten production reliability and behavior consistency.
- Improve conversion and handoff quality while preserving compliance.
- Support multi-subaccount onboarding and usage-based billing operations.

This document supersedes planning intent in `docs/JORGE_FINALIZATION_SPEC.md` and serves as the active execution spec.

---

## 2) Product Goals

1. Qualify seller and buyer leads with human-like, direct messaging in under 10 messages when possible.
2. Classify lead temperature accurately and deterministically (HOT/WARM/COLD).
3. Book qualified seller appointments automatically with constrained slot options.
4. Populate required GHL custom fields and tags reliably.
5. Reduce Jorge/manual team qualification time by at least 80 percent.
6. Ensure every outbound interaction is attributable to the correct subaccount for billing.

---

## 3) Scope

### In Scope

- GHL webhook-driven orchestration.
- Seller bot qualification, objection handling, temperature tiering, and appointment flow.
- Buyer bot qualification and routing.
- Cross-bot handoff rules.
- Follow-up cadence and opt-out controls.
- Tenant/subaccount-aware configuration and operational onboarding.
- KPI telemetry and reporting exports.

### Out of Scope

- Standalone web chat UI as primary runtime.
- Full CRM replacement.
- Human agent desktop UI redesign.

---

## 4) Current Baseline (as of 2026-02-09)

### Implemented

- Activation/deactivation tag gating in webhook routing.
- Opt-out detection with `AI-Off` + `Do Not Contact` handling.
- Seller mode routing and buyer fallback on seller failure.
- Seller slot offering flow with next 3 options.
- Scope field writes for seller: temperature, motivation, asking price, timeline days, mortgage balance, repair estimate, lead value tier, qualification complete, last interaction.
- Follow-up cadence after qualification: HOT daily, WARM weekly, COLD monthly.
- Seller consultation appointment type set to 30 minutes.
- Compliance audit interceptor integrated in seller and buyer response paths.
- Expanded seller extraction prompt for additional qualification context.

### Verified Test Baseline

- Targeted regression and scope tests passing: 44 passed.

---

## 5) Canonical Requirements

### 5.1 Triggering and Runtime Controls

1. AI starts only when an activation condition is true.
2. AI stops immediately when deactivation condition is true.
3. Opt-out phrases must stop all bot flows and set DNC tags in the same event cycle.
4. Seller mode has priority over buyer and lead mode when multiple tags are present.

### 5.2 Conversation Behavior

1. One-question-at-a-time by default.
2. Tone profile: professional, friendly, direct, curious.
3. Challenger style allowed, but avoid "hit list" language.
4. Must handle vague answers with clear pushback and either re-ask or disqualify path.
5. Must keep SMS-safe length and avoid robotic phrasing.

### 5.3 Temperature Classification

Temperature must be deterministic and configurable per bot mode:

- Seller profile default:
  - HOT: complete qualification + urgent timeline + high response quality.
  - WARM: partial qualification with moderate quality.
  - COLD: low engagement/low data.
- Buyer profile default:
  - HOT: 3 or more qualifying question groups answered.
  - WARM: 2 groups answered.
  - COLD: 0-1 groups answered.

Implementation requirement: classification thresholds must be runtime-configurable by env or tenant profile.

### 5.4 Seller Qualification Data Contract

Minimum required persisted fields:

- `seller_temperature`
- `seller_motivation`
- `property_condition`
- `timeline_days`
- `ai_valuation_price`
- `asking_price`
- `mortgage_balance`
- `repair_estimate`
- `lead_value_tier`
- `last_bot_interaction`
- `qualification_complete`

Additional recommended fields:

- `property_address`
- `property_type`
- `prior_listing_history`
- `decision_maker_confirmed`
- `preferred_contact_method`
- `contact_availability`

### 5.5 Calendar and Confirmation

1. HOT seller flow must offer only the next 3 available slots in business hours.
2. Slot type for seller qualification must be `seller_consultation` at 30 minutes.
3. Booking confirmation must send SMS.
4. Email confirmation behavior must be explicit:
   - Option A: bot sends email action.
   - Option B: rely on native GHL appointment workflow/email automation.
   - One option must be selected and validated in staging.

### 5.6 Follow-Up Cadence

- HOT: daily until appointment booked/completed or lead deactivated.
- WARM: weekly check-ins.
- COLD: monthly check-ins.
- Opt-out always overrides cadence and scheduling.

---

## 6) Target Architecture

### 6.1 Runtime Flow

1. Receive inbound webhook.
2. Load tenant settings and tag state.
3. Validate activation/deactivation.
4. Evaluate opt-out.
5. Handle pending appointment selection if present.
6. Route to seller, buyer, or lead mode by precedence.
7. Run response generation + compliance audit.
8. Queue outbound message + action application.
9. Record telemetry + usage/billing events.

### 6.2 State and Persistence

Primary state locations:

- GHL contact tags and custom fields (system-of-record for CRM state).
- Conversation context store (bot memory, pending appointment state, handoff hints).
- Telemetry store (event logs, KPI rollups).
- Billing usage ledger (tenant-attributed outbound and compute usage).

### 6.3 Tenant Model

Each tenant/subaccount must support:

- Unique GHL API credentials and calendar IDs.
- Workflow and custom-field mappings.
- Optional tenant-level classification thresholds.
- Isolated usage attribution for billing.

---

## 7) Improvement Roadmap (Execution Epics)

### Epic A: Behavior Hardening and Scope Lock

Goals:

- Enforce one-question flow guardrails.
- Normalize tone controls and forbidden phrasing.
- Resolve ambiguity in seller vs buyer threshold profiles.

Deliverables:

- Policy layer for message linting before send.
- Config profile schema (`seller_profile`, `buyer_profile`) with defaults.
- Test matrix for tone and disqualification paths.

Acceptance Criteria:

- No forbidden language in 100 percent of scenario tests.
- At least 95 percent of qualification flows follow one-question-step progression.

### Epic B: Qualification Data Quality

Goals:

- Increase extraction recall and consistency.
- Ensure every required field write either succeeds or emits recoverable warning.

Deliverables:

- Field completeness validator after each seller turn.
- Automatic retry/repair for malformed numeric fields.
- Daily data quality report by tenant.

Acceptance Criteria:

- 98 percent+ successful writes for required fields.
- Less than 2 percent invalid numeric parsing in sampled transcripts.

### Epic C: Calendar and Appointment Reliability

Goals:

- Make booking deterministic, observable, and tenant-safe.

Deliverables:

- Slot expiration + stale state cleanup.
- Confirmation pathway decision (SMS only vs SMS+Email) documented and implemented.
- Booking fallback escalation policy with tags and task creation.

Acceptance Criteria:

- 99 percent+ successful processing for valid slot selections.
- 0 unresolved pending appointment states older than TTL.

### Epic D: Follow-Up Orchestration and Nurture Intelligence

Goals:

- Keep cadence correct while improving re-engagement quality.

Deliverables:

- Follow-up suppression rules (DNC, booked, closed-lost, manual takeover).
- Content variation templates by temperature and intent.
- Re-engagement scoring for warm/cold prioritization.

Acceptance Criteria:

- Cadence compliance above 99 percent in scheduler audits.
- Opt-out violations: zero tolerated.

### Epic E: Billing and Multi-Subaccount Provisioning

Goals:

- Ensure outbound usage is billed to the correct tenant and new subaccounts are easy to onboard.

Deliverables:

- Usage ledger schema + attribution middleware.
- Tenant bootstrap script and checklist.
- Golden template for GHL workflows/tags/fields.

Acceptance Criteria:

- 100 percent of outbound events have tenant attribution.
- New tenant setup time under 15 minutes with checklist.

### Epic F: KPI and Analytics Productization

Goals:

- Make performance visible and actionable.

Deliverables:

- KPI endpoints/export jobs:
  - qualification completion rate
  - HOT to appointment conversion
  - average messages to qualify
  - opt-out rate
  - appointment show rate
  - lead tier distribution
- Daily and weekly rollup jobs.

Acceptance Criteria:

- KPI pipeline freshness under 24 hours.
- Report generation success rate above 99 percent.

---

## 8) Backlog (Prioritized)

P0 (Immediate):

1. Enforce tone guardrails + phrase blacklist tests.
2. Finalize confirmation strategy (SMS only vs SMS+Email) and implement.
3. Add tenant usage attribution checks to webhook send/apply paths.
4. Add e2e regression for seller HOT booking with 30-minute consultation.

P1 (Next):

1. Tenant bootstrap automation for new subaccounts.
2. Field completeness and parser repair pipeline.
3. Cross-bot handoff confidence tuning and audit logs.
4. KPI export endpoint hardening.

P2 (Then):

1. A/B experimentation for prompt variants and close rates.
2. Adaptive follow-up content generation with safety constraints.
3. SLA-based alerting and operations dashboard.

---

## 9) Testing Strategy

### 9.1 Required Test Layers

- Unit:
  - scoring thresholds
  - field mapping
  - cadence scheduling
  - slot parsing/selection
- Integration:
  - webhook routing precedence
  - compliance fallback behavior
  - seller booking flow end-to-end
  - opt-out from all modes
- Contract:
  - GHL payload/response schema compatibility
  - tenant config shape validation
- Load/Resilience:
  - concurrent inbound webhook bursts
  - temporary GHL API failures and retry behavior

### 9.2 Gate Criteria Before Production Changes

1. All P0 tests green.
2. No regression in existing Jorge routing suite.
3. Staging validation with real tenant config and calendar.
4. Observability signals present (events, errors, latency, tenant attribution).

---

## 10) Deployment and Rollout Plan

Stage 1: Internal Staging

- Enable for test tenant(s) only.
- Run scripted scenario pack for seller, buyer, lead.

Stage 2: Limited Production

- Enable for one live subaccount with close monitoring.
- Daily review of KPI and error logs.

Stage 3: Template Rollout

- Publish onboarding kit for all existing and new subaccounts.
- Enable tenant self-service bootstrap where possible.

Rollback Strategy:

- Feature flags per mode (`JORGE_SELLER_MODE`, `JORGE_BUYER_MODE`, `JORGE_LEAD_MODE`).
- Deactivation tag override (`AI-Off`) always available.
- Safe fallback response path retained in webhook.

---

## 11) Observability and Operations

Required metrics:

- Webhook latency p50/p95/p99.
- Message send success and failure rates by mode and tenant.
- Action application success rates by action type.
- Booking conversion and booking failure reasons.
- Compliance flagged/blocked counts.
- DNC/opt-out event counts.

Required alerts:

- Spike in send/apply failures.
- Missing tenant attribution in usage ledger.
- KPI data freshness over SLA.
- Abnormal opt-out rate increase.

---

## 12) Open Decisions (Must Resolve)

1. Email confirmation ownership:
   - Bot-driven action or GHL-native workflow?
2. Seller hot threshold profile default:
   - strict 4-question + urgency vs 3-question engagement profile?
3. Per-tenant billing model:
   - message-based, token-based, or hybrid?
4. New subaccount onboarding:
   - full auto provisioning vs semi-automated checklist?

---

## 13) Definition of Done for This Spec

This spec is considered implemented when:

1. P0 backlog items are complete and deployed to staging.
2. End-to-end regression suite passes with tenant config and real calendar sandbox.
3. KPI dashboard/report confirms baseline measurements for one live tenant.
4. Operational runbook and tenant onboarding checklist are published.

---

## 14) Implementation File Map (Primary)

- Webhook orchestration: `ghl_real_estate_ai/api/routes/webhook.py`
- Seller engine: `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py`
- Buyer engine/bot: `ghl_real_estate_ai/agents/jorge_buyer_bot.py`
- Follow-up engine: `ghl_real_estate_ai/services/jorge/jorge_followup_engine.py`
- Calendar scheduling: `ghl_real_estate_ai/services/calendar_scheduler.py`
- Conversation extraction: `ghl_real_estate_ai/core/conversation_manager.py`
- Config and tenant toggles: `ghl_real_estate_ai/ghl_utils/jorge_config.py`
- Scope-alignment tests: `tests/jorge_seller/test_scope_alignment.py`
