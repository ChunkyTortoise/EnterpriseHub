# Jorge Bots Value Optimization Spec (Lead + Seller + Buyer)

Version: 1.0  
Date: 2026-02-16  
Status: Proposed for build execution  
Primary Goal: Increase business value to Jorge via higher qualification quality, faster handoff, better booking conversion, and lower manual workload.

---

## 1. Purpose

This spec defines the next development phase for Jorge's Lead, Seller, and Buyer bots to:

1. Align production behavior with the intended scope.
2. Standardize a consultative and friendly conversational style.
3. Improve conversion outcomes and appointment show rates.
4. Increase data completeness and decision quality in GHL.
5. Reduce Jorge's manual qualification overhead.

---

## 2. Business Outcomes and KPI Targets

Target measurement window: first 30 days post rollout.

1. Qualification completion rate: >= 70% (currently lower/inconsistent across flows).
2. HOT seller to appointment conversion: +25% relative lift.
3. Appointment show rate: +15% relative lift.
4. Median messages to qualify seller: <= 10.
5. Custom-field completion for qualified sellers: >= 95%.
6. Opt-out rate: <= 3.5% while increasing booked appointments.
7. Manual intervention rate (fallback/escalation): <= 10%.

---

## 3. Current State Snapshot (As-Is)

### 3.1 What is already strong

1. Routing architecture is in place in webhook handler with Seller, Buyer, and Lead modes.
2. Seller mode includes temperature tagging and slot-offer flow for HOT leads.
3. Buyer flow has qualification and supportive response generation.
4. Performance baselines exist and show ample latency headroom.
5. Tone engine now supports consultative-friendly generation and compliance checks.

### 3.2 Key gaps impacting Jorge value

1. Seller qualification is still effectively centered on a 4-question core, not full expanded seller intake.
2. Follow-up cadence does not fully match desired HOT daily / WARM weekly / COLD monthly behavior.
3. Hot-seller auto-book path currently leans on listing appointment type durations, not a strict 30-minute consultation path.
4. Some important seller fields are not consistently captured or persisted.
5. Opt-out currently uses `AI-Off`; explicit do-not-contact semantics should be stronger and standardized.
6. Historical doc/specs are inconsistent with current runtime behavior and need a single source of truth.

---

## 4. Product Scope (To-Be)

## 4.1 Cross-Bot Experience Requirements

1. Tone requirement: consultative, friendly, clear, and professional.
2. Questioning requirement: one question at a time unless user answers multiple at once.
3. Response requirement: human, non-robotic, and concise for SMS constraints.
4. Safety requirement: immediate opt-out with confirmation and suppression tagging.
5. Consistency requirement: standardized tags, field names, and status transitions.

## 4.2 Seller Bot Requirements

Activation:
1. Trigger when contact has `Needs Qualifying` and seller mode is enabled.

Qualification flow target:
1. Property address and property type.
2. Property condition.
3. Timeline to sell (capture numeric days where possible).
4. Motivation driver.
5. Asking price expectation.
6. Mortgage balance or lien status.
7. Repair estimate.
8. Prior listing history.
9. Decision maker confirmation.
10. Preferred contact method and availability windows.

Temperature logic target:
1. HOT: strong motivation + <= 30 day timeline + actionable conversation quality.
2. WARM: 30-90 day timeline or partial motivation.
3. COLD: exploratory with low intent and no immediate timeline.

Outcome actions:
1. HOT: offer 3 near-term slots and auto-book consult when selected.
2. WARM: enter weekly consultative nurture.
3. COLD: enter monthly market update drip with soft check-ins.

## 4.3 Buyer Bot Requirements

1. Maintain consultative, educational buyer style.
2. Preserve opt-out compliance parity with seller/lead.
3. Improve qualification actionability for handoff to human agent.
4. Persist buyer critical fields and confidence scores for routing decisions.

## 4.4 Lead Bot Requirements

1. Continue broad lead handling and intent decoding.
2. Improve handoff accuracy to seller or buyer bot with confidence thresholds.
3. Avoid generic fallback when clear seller/buyer intent exists.
4. Maintain consultative language in showing/offer guidance.

---

## 5. Canonical Data Contract (GHL Fields)

The system must support a canonical seller qualification schema with deterministic write rules.

| Field | Type | Required for Qualified Seller | Notes |
|---|---|---:|---|
| `seller_temperature` | enum(HOT,WARM,COLD) | Yes | Derived classification |
| `seller_motivation` | text | Yes | Free text summary |
| `property_condition` | enum | Yes | Normalize to canonical options |
| `timeline_days` | int | Yes | Numeric target when available |
| `asking_price` | currency | Yes | Seller target price |
| `ai_valuation_price` | currency | Yes | Model/market valuation |
| `mortgage_balance` | currency | Preferred | Capture lien debt when disclosed |
| `repair_estimate` | currency | Preferred | Range or numeric |
| `lead_value_tier` | enum(A,B,C,D) | Yes | Derived from pricing + intent |
| `last_bot_interaction` | datetime | Yes | Updated every bot response |
| `qualification_complete` | bool | Yes | True only when minimum required fields met |
| `decision_maker_confirmed` | bool | Preferred | Decision authority risk control |
| `best_contact_method` | enum(SMS,Call,Email) | Preferred | For follow-up channel tuning |
| `availability_windows` | text/json | Preferred | Scheduling optimization |
| `prior_listing_history` | text/json | Preferred | MLS or user-provided |

Write policy:
1. Write merged values after each message turn.
2. Never erase known non-null values unless explicitly corrected by the user.
3. Track provenance: extracted, inferred, user-confirmed.

---

## 6. Routing, State, and Tagging

Routing priority (deterministic):
1. Seller mode.
2. Buyer mode.
3. Lead mode.
4. Safe fallback.

Tagging standards:
1. Activation tags must be explicit and mode-specific.
2. Deactivation and suppression tags must include do-not-contact semantics.
3. Temperature tags must be mutually exclusive per bot domain.

Opt-out standard:
1. Immediate stop.
2. Add suppression tag(s): `AI-Off` plus `Do-Not-Contact`.
3. Remove active automation tags to prevent accidental restarts.

---

## 7. Appointment Engine Specification

For HOT sellers:
1. Offer exactly 3 next available slots in business hours.
2. Use 30-minute consultation appointment type for this flow.
3. Accept slot selection via ordinal input (`1`, `2`, `3`) or timestamp match.
4. Confirm booking via SMS and email.
5. Store booking metadata in context and custom fields.
6. If booking fails, provide graceful fallback and queue manual scheduler action.

Time and business-hour requirements:
1. Enforce timezone normalization.
2. Exclude closed-day hours.
3. Prevent stale slot booking with expiration checks.

---

## 8. Follow-Up Cadence and Lifecycle Rules

Cadence policy:
1. HOT: daily check-in until appointment completed or explicit pause.
2. WARM: weekly value-add follow-up.
3. COLD: monthly market update and soft recheck.

Lifecycle controls:
1. Max retry limits per stage.
2. De-escalate frequency after repeated non-response.
3. Escalate to human review when risk or high value thresholds are met.

Message policy:
1. Consultative prompts, no hard-pressure framing.
2. Keep messages SMS-safe and compliant.
3. Always provide clear next step choices.

---

## 9. Tone and Conversation Intelligence

Global tone policy:
1. Consultative and friendly by default.
2. Direct but respectful when clarifying vague responses.
3. No confrontational or shaming language.

Guardrails:
1. Compliance checks before outbound sends.
2. Aggressive phrase detector and rewrite fallback.
3. Max length and formatting constraints for SMS channels.

Quality scoring:
1. Keep semantic response quality scoring for extraction confidence.
2. Track vague streak and clarity trend.
3. Use confidence to decide clarification vs progression.

---

## 10. Optimization Framework

### 10.1 Experimentation (A/B or multi-variant)

Primary experiments:
1. Opening line style for seller qualification.
2. Slot-offer framing for HOT appointment booking.
3. Warm/cold nurture copy style.
4. Clarification prompt style for vague responses.

Guardrails for experiments:
1. No experiment may violate consultative tone policy.
2. No experiment may reduce compliance pass rates.
3. Roll back variant if opt-out increases above threshold.

### 10.2 Value Scoring

Compute lead value from:
1. Motivation intensity.
2. Timeline urgency.
3. Pricing realism.
4. Property condition and repair spread.
5. Engagement consistency and response quality.

---

## 11. Observability and Analytics

Required event stream:
1. `bot_message_generated`
2. `qualification_field_updated`
3. `temperature_changed`
4. `appointment_slot_offered`
5. `appointment_booked`
6. `followup_scheduled`
7. `opt_out_detected`
8. `manual_escalation_triggered`

Dashboard views:
1. Funnel: contacted -> qualified -> HOT -> booked -> showed.
2. Message efficiency: median turns to qualification.
3. Field completeness by stage.
4. Opt-out and compliance alerts by bot and variant.

---

## 12. Technical Implementation Backlog

## Epic A: Routing and contract hardening

Targets:
1. Normalize webhook contract calls and payloads across bots.
2. Standardize response keys for downstream actions.

Primary files:
1. `ghl_real_estate_ai/api/routes/webhook.py`
2. `ghl_real_estate_ai/agents/jorge_buyer_bot.py`
3. `ghl_real_estate_ai/agents/lead_bot.py`

## Epic B: Seller qualification expansion

Targets:
1. Expand beyond 4-question core into full seller intake contract.
2. Implement deterministic completion criteria.

Primary files:
1. `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py`
2. `ghl_real_estate_ai/ghl_utils/jorge_config.py`
3. `ghl_real_estate_ai/core/conversation_manager.py`

## Epic C: Field mapping and persistence

Targets:
1. Add missing canonical fields and enforce write policy.
2. Build mapping validator for missing GHL IDs.

Primary files:
1. `ghl_real_estate_ai/ghl_utils/jorge_config.py`
2. `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py`
3. `deploy/phase1_seller_only.env`
4. `deploy/phase2_seller_buyer.env`
5. `deploy/phase3_all_bots.env`

## Epic D: Appointment and confirmation optimization

Targets:
1. Enforce 30-minute HOT consult appointment type.
2. Support SMS + email confirmations with robust fallback.

Primary files:
1. `ghl_real_estate_ai/services/calendar_scheduler.py`
2. `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py`
3. `ghl_real_estate_ai/api/routes/webhook.py`

## Epic E: Follow-up lifecycle redesign

Targets:
1. Implement HOT daily / WARM weekly / COLD monthly logic.
2. Add pause/stop semantics and escalation windows.

Primary files:
1. `ghl_real_estate_ai/services/jorge/jorge_followup_engine.py`
2. `ghl_real_estate_ai/services/jorge/jorge_followup_scheduler.py`
3. `ghl_real_estate_ai/ghl_utils/jorge_config.py`

## Epic F: Tone and compliance polish

Targets:
1. Lock consultative style across all active templates.
2. Expand compliance fallback coverage and test matrix.

Primary files:
1. `ghl_real_estate_ai/services/jorge/jorge_tone_engine.py`
2. `ghl_real_estate_ai/services/compliance_guard.py`
3. `ghl_real_estate_ai/agents/lead_bot.py`
4. `ghl_real_estate_ai/agents/jorge_buyer_bot.py`

## Epic G: Metrics and optimization loop

Targets:
1. Complete event schema and KPI dashboards.
2. Enable controlled A/B testing rollout with auto-rollback.

Primary files:
1. `ghl_real_estate_ai/services/jorge/bot_metrics_collector.py`
2. `ghl_real_estate_ai/services/jorge/performance_tracker.py`
3. `ghl_real_estate_ai/services/jorge/ab_testing_service.py`

---

## 13. Test Strategy and Acceptance Tests

Unit tests:
1. Tone generation and compliance validation.
2. Temperature classification boundaries.
3. Field extraction and normalization.
4. Follow-up cadence scheduler behavior.

Integration tests:
1. Webhook route selection by tags and mode flags.
2. Seller HOT slot offer and booking completion.
3. Buyer and lead handoff correctness.
4. Opt-out suppression and tag actions.

E2E tests:
1. Seller full qualification conversation through appointment booking.
2. Warm and cold follow-up lifecycle transitions.
3. Failure modes: booking failure, compliance block, API timeout.

Performance tests:
1. Re-run bot baseline suites and compare regression thresholds.
2. Verify P95 remains within configured SLA targets.

---

## 14. Rollout Plan

Phase 0: Staging hardening (3-5 days)
1. Ship epics A, B, C in staging.
2. Run full integration and prompt-quality simulations.

Phase 1: Seller-first production (7+ days)
1. Enable seller optimizations only.
2. Monitor HOT booking conversion and opt-out rate daily.

Phase 2: Seller + Buyer production (7+ days)
1. Enable buyer improvements and cross-bot metrics.
2. Validate lead-to-buyer handoff precision.

Phase 3: Full three-bot optimization
1. Enable lead bot optimization and full experiment framework.
2. Run weekly KPI review with rollback thresholds.

---

## 15. Definition of Done

1. All required fields for qualified sellers persist at >= 95% completeness.
2. HOT flow books 30-minute consultations from top 3 slots with dual-channel confirmation.
3. Follow-up cadence matches HOT/WARM/COLD lifecycle policy.
4. Opt-out always suppresses automation with explicit DNC tagging.
5. Consultative and friendly tone is enforced in active runtime templates.
6. KPI dashboards show measurable conversion and efficiency improvements over baseline.

---

## 16. Immediate Execution Plan (Next Sprint)

1. Implement canonical seller data contract and field writer.
2. Refactor seller flow to expanded qualification stages.
3. Align appointment type and confirmation channels for HOT sellers.
4. Replace follow-up cadence engine with lifecycle-based scheduler.
5. Add integration tests for opt-out, booking flow, and field completeness.

---

## 17. Open Decisions

1. Final threshold definitions for HOT/WARM/COLD in production by market.
2. Exact DNC tag taxonomy in GHL (`Do-Not-Contact` naming standard).
3. Email template ownership for appointment confirmations.
4. Weekly KPI review owner and rollback authority.

