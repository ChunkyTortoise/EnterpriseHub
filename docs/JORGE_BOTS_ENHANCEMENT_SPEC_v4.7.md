# Jorge Buyer & Seller Bot Enhancement Spec v4.7

**Version**: 4.7 | **Date**: 2026-02-09 | **Status**: Ready for Agent Execution
**Scope**: Comprehensive improvements to Jorge Buyer Bot, Seller Bot, and shared infrastructure
**Prerequisite**: All 4,937 existing tests passing, CI green

---

## Table of Contents

1. [Current State Summary](#1-current-state-summary)
2. [Enhancement Categories](#2-enhancement-categories)
3. [Phase 1 — Compliance & Safety (P0)](#3-phase-1--compliance--safety-p0)
4. [Phase 2 — Buyer Bot Enhancements (P1)](#4-phase-2--buyer-bot-enhancements-p1)
5. [Phase 3 — Seller Bot Enhancements (P1)](#5-phase-3--seller-bot-enhancements-p1)
6. [Phase 4 — Shared Infrastructure (P1)](#6-phase-4--shared-infrastructure-p1)
7. [Phase 5 — Intelligence & Analytics (P2)](#7-phase-5--intelligence--analytics-p2)
8. [Phase 6 — Integration Hardening (P2)](#8-phase-6--integration-hardening-p2)
9. [Testing Strategy](#9-testing-strategy)
10. [File Reference Index](#10-file-reference-index)
11. [Agent Execution Guide](#11-agent-execution-guide)

---

## 1. Current State Summary

### Architecture

| Component | File | Lines | Workflow |
|-----------|------|-------|----------|
| Buyer Bot | `agents/jorge_buyer_bot.py` | 1,554 | 13-node LangGraph |
| Buyer Intent Decoder | `agents/buyer_intent_decoder.py` | 525 | 9 scoring dimensions |
| Buyer State | `models/buyer_bot_state.py` | 66 | 30+ TypedDict fields |
| Buyer Config | `ghl_utils/jorge_config.py` (BuyerBudgetConfig) | 149 | env-based overrides |
| Seller Bot | `agents/jorge_seller_bot.py` | ~2,000 | 9-node LangGraph (standard) + 7-node adaptive |
| Seller Engine | `services/jorge/jorge_seller_engine.py` | ~1,500 | Business logic processor |
| Seller Intent Decoder | `agents/seller_intent_decoder.py` | 514 | 6 scoring dimensions |
| Seller Config | `ghl_utils/jorge_config.py` (SellerBotConfig) | 37 | env-based overrides |
| Handoff Service | `services/jorge/jorge_handoff_service.py` | 987 | Tag-driven cross-bot |
| A/B Testing | `services/jorge/ab_testing_service.py` | 695 | z-test significance |
| Performance Tracker | `services/jorge/performance_tracker.py` | 632 | P50/P95/P99 |
| Alerting Service | `services/jorge/alerting_service.py` | 986 | 7 default rules |
| Bot Metrics | `services/jorge/bot_metrics_collector.py` | 501 | Per-bot aggregation |
| Telemetry | `services/jorge/telemetry.py` | 233 | OTel stubs |
| CRM Protocol | `services/crm/protocol.py` | 52 | ABC interface |
| GHL Adapter | `services/crm/ghl_adapter.py` | ~200 | GHL v2 API |
| HubSpot Adapter | `services/crm/hubspot_adapter.py` | — | HubSpot v3 API |
| Salesforce Adapter | `services/crm/salesforce_adapter.py` | — | OAuth 2.0 |

### Scoring Dimensions

**Buyer (9)**: financial_readiness, budget_clarity, financing_status, urgency, timeline_pressure, consequence_awareness, preference_clarity, market_realism, decision_authority

**Seller (6)**: condition_anxiety, valuation_confidence, prep_readiness, listing_urgency, price_flexibility, motivation_strength

### Existing Test Count
- Buyer Bot: ~70+ test methods across 11 files
- Seller Bot: ~900+ tests across 7 files
- Handoff: ~80+ tests
- Shared Services: ~100+ tests

---

## 2. Enhancement Categories

| Category | Items | Priority | Est. Tests |
|----------|-------|----------|------------|
| Compliance & Safety | 4 | P0 | +30 |
| Buyer Bot Features | 6 | P1 | +55 |
| Seller Bot Features | 5 | P1 | +45 |
| Shared Infrastructure | 5 | P1 | +40 |
| Intelligence & Analytics | 5 | P2 | +35 |
| Integration Hardening | 4 | P2 | +25 |
| **Total** | **29 items** | — | **+230** |

---

## 3. Phase 1 — Compliance & Safety (P0)

### 3.1 SMS Opt-Out Handling for Buyer Bot

**Problem**: Seller bot has `SMSComplianceService` integration but buyer bot lacks TCPA opt-out handling. Legal risk.

**Current State**: `jorge_buyer_bot.py` line 1321-1325 checks `SMS_MAX_LENGTH` but no opt-out processing.

**Required Changes**:

```
File: ghl_real_estate_ai/agents/jorge_buyer_bot.py
Action: Add opt-out detection before response generation

1. Import SMSComplianceService (already used by seller engine)
2. In process_buyer_conversation(), before returning response:
   - Check message against OPT_OUT_PHRASES from webhook.py (lines 180-201)
   - If opt-out detected: add "AI-Off" tag, send confirmation, skip AI response
3. Add opt-out_detected flag to response dict
```

**Test Requirements** (file: `tests/agents/test_buyer_bot.py`):
- `test_buyer_opt_out_stop_keyword` — "stop" triggers opt-out
- `test_buyer_opt_out_unsubscribe` — "unsubscribe" triggers opt-out
- `test_buyer_opt_out_adds_ai_off_tag` — GHL tag applied
- `test_buyer_opt_out_sends_confirmation` — Confirmation message returned
- `test_buyer_normal_message_not_opt_out` — Regular messages pass through

**Acceptance Criteria**:
- [ ] All OPT_OUT_PHRASES from webhook.py recognized
- [ ] "AI-Off" tag added via GHL client
- [ ] Confirmation message < 160 chars
- [ ] Bot stops processing after opt-out
- [ ] 5 tests passing

---

### 3.2 PII Redaction in Logs

**Problem**: `buyer_phone`, `buyer_email` stored in state and logged without redaction. CCPA/privacy risk.

**Current State**: No PII handling in either bot's logging.

**Required Changes**:

```
File: ghl_real_estate_ai/utils/pii_redactor.py (NEW)
Action: Create PII redaction utility

1. PIIRedactor class with methods:
   - redact_phone(text) — mask to "***-***-1234" (last 4 visible)
   - redact_email(text) — mask to "j***@***.com" (first char + ontario_mills TLD)
   - redact_ssn(text) — mask to "***-**-6789"
   - redact_all(text) — apply all redactions
   - safe_log(data: dict) — deep-copy and redact all string values

2. Regex patterns:
   - Phone: r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
   - Email: r'\b[\w.-]+@[\w.-]+\.\w+\b'
   - SSN: r'\b\d{3}-\d{2}-\d{4}\b'
```

```
File: ghl_real_estate_ai/agents/jorge_buyer_bot.py
File: ghl_real_estate_ai/services/jorge/jorge_seller_engine.py
Action: Wrap all logger.info/debug calls that include state data with safe_log()
```

**Test Requirements** (file: `tests/utils/test_pii_redactor.py`):
- `test_redact_phone_formats` — (xxx) xxx-xxxx, xxx-xxx-xxxx, xxxxxxxxxx
- `test_redact_email` — standard, subontario_mills, plus-addressing
- `test_redact_ssn` — standard format
- `test_redact_all_mixed` — text containing multiple PII types
- `test_safe_log_deep_copy` — original dict not modified
- `test_safe_log_nested_dicts` — handles nested structures
- `test_no_false_positives` — "$500,000" not redacted as phone

**Acceptance Criteria**:
- [ ] All PII types redacted before logging
- [ ] Original data never modified (deep copy)
- [ ] No false positives on dollar amounts or dates
- [ ] 7 tests passing

---

### 3.3 Per-Contact Rate Limiting

**Problem**: No per-buyer/seller conversation rate limiting. Spam/abuse vulnerability.

**Current State**: Handoff service has rate limiting (3/hr, 10/day) but bot conversation endpoints don't.

**Required Changes**:

```
File: ghl_real_estate_ai/utils/conversation_rate_limiter.py (NEW)
Action: Create conversation rate limiter

1. ConversationRateLimiter class:
   - __init__(max_per_minute=5, max_per_hour=30, max_per_day=200)
   - check_rate_limit(contact_id: str) -> RateLimitResult
   - record_interaction(contact_id: str)
   - _cleanup_expired()

2. RateLimitResult dataclass:
   - allowed: bool
   - retry_after_seconds: Optional[int]
   - limit_type: Optional[str]  # "minute", "hour", "day"

3. Thread-safe with Lock
4. In-memory with deque (like PerformanceTracker pattern)
```

```
File: ghl_real_estate_ai/agents/jorge_buyer_bot.py
File: ghl_real_estate_ai/services/jorge/jorge_seller_engine.py
Action: Check rate limit before processing conversation
- If rate limited: return polite "We'll get back to you shortly" message
- Log rate limit events for monitoring
```

**Test Requirements** (file: `tests/utils/test_conversation_rate_limiter.py`):
- `test_under_limit_allowed` — normal traffic passes
- `test_minute_limit_blocks` — 6th message in 1 minute blocked
- `test_hour_limit_blocks` — 31st message in 1 hour blocked
- `test_different_contacts_independent` — limits are per-contact
- `test_expired_entries_cleaned` — old entries don't count
- `test_retry_after_seconds` — correct retry-after calculation
- `test_thread_safety` — concurrent access doesn't corrupt state

**Acceptance Criteria**:
- [ ] Rate limits enforced per contact
- [ ] Polite response returned when rate limited
- [ ] Thread-safe implementation
- [ ] 7 tests passing

---

### 3.4 Compliance Escalation Parity

**Problem**: Buyer bot has compliance escalation (lines 1004-1101) but seller bot lacks equivalent depth.

**Current State**: Seller engine relies on `ComplianceGuard` 3-tier check but doesn't have buyer-style structured escalation with severity mapping and audit trails.

**Required Changes**:

```
File: ghl_real_estate_ai/services/jorge/jorge_seller_engine.py
Action: Add structured compliance escalation matching buyer bot pattern

1. Add compliance violation types: fair_housing, privacy, financial_regulation, licensing
2. Severity mapping: critical/high → immediate bot pause + notification
3. Audit trail logging with violation evidence
4. CRM flagging (add "Compliance-Flagged" tag)
```

**Test Requirements** (file: `tests/services/test_seller_compliance_escalation.py`):
- `test_fair_housing_violation_pauses_bot`
- `test_privacy_violation_logs_audit_trail`
- `test_critical_severity_notifies_compliance_officer`
- `test_crm_flagging_adds_tag`
- `test_violation_evidence_preserved`

**Acceptance Criteria**:
- [ ] All 4 violation types handled
- [ ] Severity mapping matches buyer bot
- [ ] Audit trail persisted
- [ ] 5 tests passing

---

## 4. Phase 2 — Buyer Bot Enhancements (P1)

### 4.1 Property Tour Scheduling Integration

**Problem**: `schedule_next_action` node emits event but has no calendar integration. Manual follow-up required.

**Current State**: Lines 1179-1190 in `jorge_buyer_bot.py` — event published but no booking.

**Required Changes**:

```
File: ghl_real_estate_ai/services/tour_scheduler.py (NEW)
Action: Tour scheduling service

1. TourScheduler class:
   - __init__(ghl_client, calendar_provider="ghl")
   - async get_available_slots(agent_id: str, days_ahead: int = 7) -> List[TimeSlot]
   - async book_tour(buyer_id: str, property_id: str, slot: TimeSlot) -> BookingResult
   - async cancel_tour(booking_id: str) -> bool
   - async get_buyer_tours(buyer_id: str) -> List[Tour]

2. TimeSlot dataclass:
   - start: datetime, end: datetime, agent_name: str, location: str

3. BookingResult dataclass:
   - success: bool, booking_id: str, confirmation_message: str

4. Integration with GHL calendar API:
   - GET /calendars/{calendar_id}/free-slots
   - POST /calendars/{calendar_id}/appointments

5. SMS confirmation message template (< 160 chars):
   "Your property tour is confirmed for {date} at {time}.
   Address: {address}. Reply CANCEL to reschedule. - Jorge"
```

```
File: ghl_real_estate_ai/agents/jorge_buyer_bot.py
Action: Wire TourScheduler into schedule_next_action node

1. For hot buyers (qualification ≥ 75):
   - Fetch 3 available slots
   - Present options in response: "Reply 1, 2, or 3"
   - Store pending_tour in state
2. For warm buyers (50-74):
   - Suggest tour with softer CTA
3. Track tour_offered, tour_booked metrics
```

**Test Requirements** (file: `tests/services/test_tour_scheduler.py`):
- `test_get_available_slots_returns_within_range`
- `test_book_tour_creates_appointment`
- `test_book_tour_sends_confirmation_sms`
- `test_cancel_tour_removes_appointment`
- `test_sms_confirmation_under_160_chars`
- `test_no_slots_available_returns_empty`
- `test_hot_buyer_gets_tour_offer`
- `test_warm_buyer_gets_soft_cta`

**Acceptance Criteria**:
- [ ] GHL calendar API integration
- [ ] 3-slot selection flow for hot buyers
- [ ] SMS confirmation < 160 chars
- [ ] Cancel/reschedule support
- [ ] 8 tests passing

---

### 4.2 Multi-Property Comparison Matrix

**Problem**: Returns top 5 matches as flat list. Buyers get analysis paralysis with no comparison framework.

**Current State**: Lines 581-585 in `jorge_buyer_bot.py` — `matched_properties` is a list of dicts.

**Required Changes**:

```
File: ghl_real_estate_ai/services/property_comparison.py (NEW)
Action: Property comparison service

1. PropertyComparator class:
   - compare(properties: List[Dict], buyer_preferences: Dict) -> ComparisonMatrix
   - rank_by_fit(properties, preferences) -> List[RankedProperty]
   - generate_summary(matrix: ComparisonMatrix) -> str  # SMS-friendly

2. ComparisonMatrix dataclass:
   - properties: List[RankedProperty]
   - comparison_dimensions: List[str]  # price, beds, sqft, lot_size, year_built
   - best_overall: RankedProperty
   - best_value: RankedProperty
   - closest_to_budget: RankedProperty

3. RankedProperty dataclass:
   - property_data: Dict
   - fit_score: float  # 0-100
   - pros: List[str]
   - cons: List[str]
   - price_vs_budget: str  # "under", "at", "over"

4. SMS-friendly summary format (< 320 chars):
   "Top 3 matches for you:
   1. 123 Oak St - $599K, 4bd/2ba - Best Overall
   2. 456 Elm Dr - $549K, 3bd/2ba - Best Value
   3. 789 Pine Ln - $575K, 4bd/3ba - Closest to Budget
   Reply # for details!"
```

```
File: ghl_real_estate_ai/agents/jorge_buyer_bot.py
Action: Add comparison logic to match_properties node

1. After finding matches, run PropertyComparator.compare()
2. Store comparison_matrix in state
3. Include SMS summary in response
4. Track comparison_offered metric
```

**Test Requirements** (file: `tests/services/test_property_comparison.py`):
- `test_compare_ranks_by_fit_score`
- `test_best_overall_selected_correctly`
- `test_best_value_lowest_price_per_sqft`
- `test_closest_to_budget_calculation`
- `test_pros_cons_generated`
- `test_sms_summary_under_320_chars`
- `test_single_property_comparison`
- `test_empty_properties_handled`

**Acceptance Criteria**:
- [ ] Fit score calculated per property
- [ ] Best overall/value/budget picks identified
- [ ] Pros/cons generated per property
- [ ] SMS summary < 320 chars
- [ ] 8 tests passing

---

### 4.3 Offer Strategy Advisor

**Problem**: Buyer workflow ends at property matching. No guidance on offers.

**Current State**: No offer-related workflow nodes.

**Required Changes**:

```
File: ghl_real_estate_ai/services/offer_advisor.py (NEW)
Action: Offer strategy service

1. OfferAdvisor class:
   - async analyze_offer_position(
       property_data: Dict,
       buyer_profile: Dict,
       market_conditions: Dict
     ) -> OfferStrategy

2. OfferStrategy dataclass:
   - suggested_price: float
   - price_rationale: str
   - contingencies: List[str]  # inspection, appraisal, financing, sale
   - earnest_money_pct: float  # 1-3% typical
   - escalation_clause: Optional[Dict]  # max_price, increment
   - closing_timeline_days: int
   - competitive_assessment: str  # "strong", "moderate", "weak"

3. Market-aware logic:
   - Seller's market: suggest at or above list, fewer contingencies
   - Buyer's market: suggest below list, more contingencies
   - Days on market factor: >30 DOM → more aggressive pricing
   - Multiple offer detection: adjust escalation clause
```

```
File: ghl_real_estate_ai/agents/jorge_buyer_bot.py
Action: Add offer_strategy node to LangGraph workflow

1. New node: prepare_offer_strategy (after match_properties)
2. Conditional: only for hot buyers with selected property
3. Include in response: "Based on market data, here's our recommended approach..."
4. Store offer_strategy in state for follow-up reference
```

**Test Requirements** (file: `tests/services/test_offer_advisor.py`):
- `test_sellers_market_suggests_at_list`
- `test_buyers_market_suggests_below_list`
- `test_high_dom_more_aggressive`
- `test_earnest_money_percentage`
- `test_contingency_recommendations`
- `test_escalation_clause_generation`
- `test_competitive_assessment`
- `test_closing_timeline_reasonable`

**Acceptance Criteria**:
- [ ] Market condition-aware pricing
- [ ] Contingency recommendations
- [ ] Escalation clause logic
- [ ] DOM-adjusted strategy
- [ ] 8 tests passing

---

### 4.4 Mortgage Pre-Qualification Flow

**Problem**: Buyer bot detects pre-approval status from conversation but can't initiate or track the process.

**Current State**: Lines 403-451 — `assess_financial_readiness` scores but doesn't act.

**Required Changes**:

```
File: ghl_real_estate_ai/services/mortgage_tracker.py (NEW)
Action: Mortgage pre-qualification tracking

1. MortgageTracker class:
   - async assess_readiness(buyer_data: Dict) -> MortgageReadiness
   - async create_prequalification_referral(buyer_id: str, lender: str) -> Referral
   - async check_status(referral_id: str) -> ReferralStatus
   - get_lender_recommendation(buyer_profile: Dict) -> str

2. MortgageReadiness dataclass:
   - status: str  # "pre_approved", "pre_qualified", "needs_prequalification", "unknown"
   - estimated_buying_power: Optional[float]
   - recommended_action: str
   - lender_suggestions: List[str]

3. Referral tracking:
   - Store referral_id, lender, timestamp, status
   - CRM custom field update: "Mortgage-Status"
   - Tag: "Pre-Qualification-Sent" or "Pre-Approved"

4. Conversation templates:
   - Not pre-approved: "Getting pre-approved is a great first step! It shows
     sellers you're serious. Would you like me to connect you with a trusted
     lender who specializes in the Rancho Cucamonga area?"
   - In progress: "Great that you're working on pre-approval! Have you heard
     back from your lender yet?"
```

```
File: ghl_real_estate_ai/agents/jorge_buyer_bot.py
Action: Wire MortgageTracker into financial readiness node

1. If financing_status == "unknown" or "needs_approval":
   - Offer pre-qualification referral
   - Track in state: mortgage_referral_offered
2. If financing_status == "pre_approved":
   - Celebrate and boost urgency score
   - Update CRM tag
```

**Test Requirements** (file: `tests/services/test_mortgage_tracker.py`):
- `test_assess_readiness_pre_approved`
- `test_assess_readiness_needs_prequalification`
- `test_create_referral_stores_id`
- `test_crm_tag_updated_on_referral`
- `test_lender_recommendation_by_profile`
- `test_buying_power_estimation`
- `test_conversation_template_not_approved`

**Acceptance Criteria**:
- [ ] Readiness assessment from conversation data
- [ ] Referral tracking with CRM updates
- [ ] Buying power estimation
- [ ] Appropriate conversation templates
- [ ] 7 tests passing

---

### 4.5 Buyer Saved Search & Alerts

**Problem**: One-time property matching in conversation. No ongoing notifications.

**Current State**: Lines 539-590 — one-time `match_properties` call.

**Required Changes**:

```
File: ghl_real_estate_ai/services/saved_search.py (NEW)
Action: Saved search and alert service

1. SavedSearchService class:
   - async create_search(buyer_id: str, criteria: SearchCriteria) -> SavedSearch
   - async check_new_matches(search_id: str) -> List[Dict]
   - async notify_buyer(buyer_id: str, new_matches: List[Dict])
   - async deactivate_search(search_id: str)
   - async get_active_searches(buyer_id: str) -> List[SavedSearch]

2. SearchCriteria dataclass:
   - budget_min: Optional[float]
   - budget_max: Optional[float]
   - beds_min: Optional[int]
   - baths_min: Optional[int]
   - features: List[str]
   - neighborhoods: List[str]
   - max_dom: Optional[int]  # days on market

3. SavedSearch dataclass:
   - id: str
   - buyer_id: str
   - criteria: SearchCriteria
   - created_at: datetime
   - last_checked: datetime
   - matches_sent: int
   - active: bool

4. Notification template (< 160 chars):
   "New listing alert! {address} - ${price}, {beds}bd/{baths}ba just
   listed in {area}. Reply INFO for details or STOP to unsubscribe."
```

```
File: ghl_real_estate_ai/agents/jorge_buyer_bot.py
Action: Offer saved search creation after property matching

1. After presenting matches: "Want me to alert you when new homes matching
   your criteria hit the market? Reply YES to set up alerts."
2. Parse YES response → create saved search from extracted preferences
3. Store saved_search_id in state
```

**Test Requirements** (file: `tests/services/test_saved_search.py`):
- `test_create_search_from_criteria`
- `test_check_new_matches_returns_only_new`
- `test_notify_buyer_sms_format`
- `test_deactivate_search`
- `test_notification_under_160_chars`
- `test_multiple_searches_per_buyer`

**Acceptance Criteria**:
- [ ] Search criteria persistence
- [ ] New-only match detection
- [ ] SMS notification < 160 chars
- [ ] Deactivation support
- [ ] 6 tests passing

---

### 4.6 Buyer Journey Stage Tracking

**Problem**: No explicit tracking of where buyer is in the purchase funnel.

**Current State**: Temperature classification exists but not journey stage.

**Required Changes**:

```
File: ghl_real_estate_ai/services/buyer_journey.py (NEW)
Action: Buyer journey stage tracker

1. BuyerJourneyTracker class:
   - determine_stage(buyer_state: Dict) -> JourneyStage
   - get_stage_actions(stage: JourneyStage) -> List[str]
   - track_progression(buyer_id: str, from_stage: str, to_stage: str)

2. JourneyStage enum:
   - AWARENESS — browsing, no budget, no timeline
   - CONSIDERATION — has budget, comparing options
   - PRE_APPROVAL — working on financing
   - ACTIVE_SEARCH — touring properties, making offers
   - UNDER_CONTRACT — offer accepted, in escrow
   - CLOSED — transaction complete

3. Stage determination rules:
   - AWARENESS: financial_readiness < 30, no budget mentioned
   - CONSIDERATION: budget_clarity > 40, preference_clarity > 30
   - PRE_APPROVAL: financing_status in ("needs_approval", "in_progress")
   - ACTIVE_SEARCH: financing_status == "pre_approved", urgency > 50
   - UNDER_CONTRACT: offer_accepted flag (from CRM)
   - CLOSED: transaction_closed flag (from CRM)

4. GHL tag management:
   - Add stage tag: "Stage-Active-Search"
   - Remove previous stage tag
```

**Test Requirements** (file: `tests/services/test_buyer_journey.py`):
- `test_awareness_stage_low_scores`
- `test_consideration_stage_has_budget`
- `test_active_search_pre_approved`
- `test_stage_progression_tracking`
- `test_ghl_tag_updated_on_stage_change`
- `test_stage_actions_appropriate`

**Acceptance Criteria**:
- [ ] 6 journey stages defined
- [ ] Automatic stage determination from scores
- [ ] CRM tag management
- [ ] Stage progression logging
- [ ] 6 tests passing

---

## 5. Phase 3 — Seller Bot Enhancements (P1)

### 5.1 CMA Real Data Integration

**Problem**: `CMAGenerator` exists but uses mock data. No real MLS/valuation integration.

**Current State**: Seller bot `generate_cma` node calls CMA service but gets stubbed responses.

**Required Changes**:

```
File: ghl_real_estate_ai/services/cma_generator.py (MODIFY)
Action: Add real comparable data sources

1. Add data source interface:
   - MLSDataSource (fetch from MLS API)
   - PublicRecordSource (county assessor data)
   - AVM Source (existing valuation engine integration)

2. CMA generation pipeline:
   - Fetch 5-10 comparable sales (within 0.5mi, last 6 months)
   - Adjust for: sqft diff, age diff, condition, lot size
   - Calculate suggested list price range (low/mid/high)
   - Generate confidence score

3. CMA output enrichment:
   - price_per_sqft_comparison
   - days_on_market_avg for comps
   - price_trend (appreciation/depreciation % over 12 months)
   - zestimate_vs_cma_delta (for Zestimate objection defense)

4. Fallback: If no real data available, return current mock with
   "estimated" flag = True
```

**Test Requirements** (file: `tests/services/test_cma_generator.py`):
- `test_cma_with_comparable_sales`
- `test_cma_price_adjustments`
- `test_cma_confidence_score`
- `test_cma_fallback_to_mock`
- `test_price_per_sqft_calculation`
- `test_zestimate_delta_calculation`
- `test_price_trend_over_12_months`

**Acceptance Criteria**:
- [ ] Comparable sales fetching (with fallback)
- [ ] Price adjustments for property differences
- [ ] Confidence score generation
- [ ] Zestimate comparison data
- [ ] 7 tests passing

---

### 5.2 Listing Preparation Checklist Service

**Problem**: `prepare_listing` workflow node exists but has minimal implementation.

**Current State**: Node exists at line 404 in `jorge_seller_bot.py` but doesn't generate actionable checklists.

**Required Changes**:

```
File: ghl_real_estate_ai/services/listing_prep.py (NEW)
Action: Listing preparation service

1. ListingPrepService class:
   - generate_checklist(seller_profile: Dict, property_data: Dict) -> PrepChecklist
   - get_condition_recommendations(condition: str) -> List[Recommendation]
   - estimate_prep_timeline(checklist: PrepChecklist) -> int  # days
   - estimate_prep_cost(checklist: PrepChecklist) -> float

2. PrepChecklist dataclass:
   - items: List[PrepItem]
   - priority_order: List[str]  # ordered by ROI impact
   - estimated_days: int
   - estimated_cost: float
   - roi_improvement_pct: float

3. PrepItem dataclass:
   - category: str  # "repair", "staging", "declutter", "curb_appeal", "documentation"
   - description: str
   - priority: str  # "must_do", "recommended", "optional"
   - estimated_cost: float
   - roi_multiplier: float  # e.g., 3.0 means $1 spent = $3 value added

4. Condition-based recommendations:
   - "excellent": Minimal — staging, photos
   - "good": Moderate — minor repairs, paint touch-up, staging
   - "needs_work": Extensive — repairs, paint, flooring, staging, landscaping
   - "major_renovation": Investor-focused — as-is pricing strategy

5. SMS-friendly summary (< 320 chars):
   "Your listing prep plan:
   1. Fresh paint (interior) - ~$2K, 3x ROI
   2. Professional staging - ~$1.5K, 2x ROI
   3. Landscaping refresh - ~$800, 4x ROI
   Est. timeline: 2 weeks. Want details on any item?"
```

**Test Requirements** (file: `tests/services/test_listing_prep.py`):
- `test_excellent_condition_minimal_items`
- `test_needs_work_extensive_items`
- `test_priority_ordered_by_roi`
- `test_cost_estimation`
- `test_timeline_estimation`
- `test_roi_improvement_calculation`
- `test_sms_summary_format`

**Acceptance Criteria**:
- [ ] Condition-based recommendations
- [ ] ROI-ordered priority
- [ ] Cost and timeline estimates
- [ ] SMS-friendly output
- [ ] 7 tests passing

---

### 5.3 Seller Net Sheet Calculator

**Problem**: Sellers don't know their estimated proceeds. Critical for motivation.

**Required Changes**:

```
File: ghl_real_estate_ai/services/seller_net_sheet.py (NEW)
Action: Seller net sheet calculation

1. SellerNetSheet class:
   - calculate(
       sale_price: float,
       mortgage_balance: float,
       commission_pct: float = 5.0,
       location: str = "rancho_cucamonga"
     ) -> NetSheetResult

2. NetSheetResult dataclass:
   - sale_price: float
   - commission: float
   - title_insurance: float  # ~0.5% of sale price
   - escrow_fees: float  # ~1% of sale price
   - transfer_tax: float  # $1.10 per $1000 (CA)
   - recording_fees: float  # ~$100 flat
   - property_tax_proration: float
   - mortgage_payoff: float
   - estimated_net_proceeds: float
   - breakdown: Dict[str, float]

3. California-specific calculations:
   - Transfer tax: $1.10 per $1,000 of sale price
   - Documentary transfer tax (county)
   - Natural hazard disclosure costs
   - HOA transfer fees (if applicable)

4. SMS-friendly summary (< 320 chars):
   "Estimated net from $750K sale:
   Sale price: $750,000
   - Commission: -$37,500
   - Closing costs: -$11,250
   - Mortgage payoff: -$400,000
   = Est. proceeds: $301,250
   Want a detailed breakdown?"
```

**Test Requirements** (file: `tests/services/test_seller_net_sheet.py`):
- `test_basic_net_calculation`
- `test_commission_calculation`
- `test_ca_transfer_tax`
- `test_escrow_and_title_fees`
- `test_no_mortgage_full_equity`
- `test_underwater_mortgage_warning`
- `test_sms_summary_format`

**Acceptance Criteria**:
- [ ] CA-specific fee calculations
- [ ] Mortgage payoff factored in
- [ ] Underwater mortgage detection
- [ ] SMS-friendly breakdown
- [ ] 7 tests passing

---

### 5.4 Follow-Up Automation Engine

**Problem**: Scheduling logic exists but execution is manual.

**Current State**: `ACTIVE_FOLLOWUP_SCHEDULE` defined in config (days 1,3,7,14,21,30) but no automated execution.

**Required Changes**:

```
File: ghl_real_estate_ai/services/followup_engine.py (NEW)
Action: Automated follow-up engine

1. FollowUpEngine class:
   - async schedule_followup(
       contact_id: str,
       bot_type: str,  # "buyer" or "seller"
       followup_type: str,
       scheduled_at: datetime
     ) -> FollowUp
   - async get_pending_followups(before: datetime) -> List[FollowUp]
   - async execute_followup(followup: FollowUp) -> FollowUpResult
   - async cancel_followup(followup_id: str)

2. FollowUp dataclass:
   - id: str
   - contact_id: str
   - bot_type: str
   - followup_type: str  # "check_in", "market_update", "new_listing", "nurture"
   - scheduled_at: datetime
   - message_template: str
   - status: str  # "pending", "sent", "cancelled", "failed"

3. Message templates per type:
   - check_in: "Hey {name}, just checking in! Any updates on your {search/sale}?"
   - market_update: "Quick market update for {area}: {metric}. Want to discuss?"
   - nurture: "Hi {name}, {seasonal_content}. Ready to take the next step?"

4. Integration points:
   - GHL SMS API for message delivery
   - BotMetricsCollector for tracking
   - AlertingService for failed delivery alerts
```

```
File: ghl_real_estate_ai/agents/jorge_buyer_bot.py
File: ghl_real_estate_ai/services/jorge/jorge_seller_engine.py
Action: Replace manual follow-up event with FollowUpEngine.schedule_followup()
```

**Test Requirements** (file: `tests/services/test_followup_engine.py`):
- `test_schedule_followup_creates_pending`
- `test_get_pending_before_datetime`
- `test_execute_followup_sends_sms`
- `test_cancel_followup_updates_status`
- `test_failed_delivery_logged`
- `test_message_template_personalization`
- `test_buyer_check_in_template`
- `test_seller_nurture_template`

**Acceptance Criteria**:
- [ ] Scheduled follow-up persistence
- [ ] Template-based message generation
- [ ] SMS delivery via GHL
- [ ] Failed delivery handling
- [ ] 8 tests passing

---

### 5.5 Seller Psychology-Aware Messaging

**Problem**: `SellerPsychologyAnalyzer` exists but end-to-end integration with message generation is incomplete.

**Current State**: Psychology profiling runs (lines 218-256 in engine) but message adaptation is limited.

**Required Changes**:

```
File: ghl_real_estate_ai/services/jorge/jorge_tone_engine.py (MODIFY)
Action: Add psychology-aware tone adaptation

1. Add method: adapt_tone_for_psychology(
     base_message: str,
     psychology_profile: Dict,
     motivation_type: str
   ) -> str

2. Tone adjustments by motivation type:
   - financial: Emphasize ROI, equity, market timing, net proceeds
   - relocation: Focus on timeline, logistics, seamless transition
   - downsizing: Highlight lifestyle benefits, equity liberation
   - divorce: Sensitive, non-judgmental, focus on fresh start
   - investment: Data-driven, cap rates, market opportunity
   - estate: Compassionate, simplified process, family considerations

3. Urgency adjustments:
   - critical: Direct, action-oriented, specific next steps
   - high: Firm but supportive, clear timeline
   - medium: Educational, market insights, gentle nudges
   - low: Relationship building, long-term value proposition

4. Never violate Fair Housing regardless of psychology type
```

**Test Requirements** (file: `tests/services/test_psychology_messaging.py`):
- `test_financial_motivation_emphasizes_roi`
- `test_divorce_motivation_sensitive_tone`
- `test_investment_motivation_data_driven`
- `test_critical_urgency_action_oriented`
- `test_low_urgency_relationship_building`
- `test_fair_housing_never_violated`

**Acceptance Criteria**:
- [ ] 6 motivation types handled
- [ ] 4 urgency levels adjusted
- [ ] Fair Housing compliance maintained
- [ ] 6 tests passing

---

## 6. Phase 4 — Shared Infrastructure (P1)

### 6.1 Token Cost Tracking

**Problem**: No per-conversation cost attribution. Can't optimize expensive interactions.

**Required Changes**:

```
File: ghl_real_estate_ai/services/jorge/cost_tracker.py (NEW)
Action: AI token cost tracking service

1. CostTracker class (singleton):
   - record_usage(
       bot_type: str,
       contact_id: str,
       input_tokens: int,
       output_tokens: int,
       model: str = "claude-sonnet-4-5-20250929"
     )
   - get_conversation_cost(contact_id: str) -> float
   - get_bot_costs(bot_type: str, period: str = "24h") -> CostSummary
   - get_system_costs(period: str = "24h") -> CostSummary

2. CostSummary dataclass:
   - total_cost: float
   - total_input_tokens: int
   - total_output_tokens: int
   - conversation_count: int
   - avg_cost_per_conversation: float
   - most_expensive_conversation: Dict

3. Pricing (as of Feb 2026):
   - claude-sonnet-4-5: $3/1M input, $15/1M output
   - claude-haiku-4-5: $0.80/1M input, $4/1M output
   - claude-opus-4-6: $15/1M input, $75/1M output

4. Integration: Instrument ClaudeOrchestrator.process_request() to
   auto-record usage from API response metadata
```

**Test Requirements** (file: `tests/services/test_cost_tracker.py`):
- `test_record_usage_calculates_cost`
- `test_conversation_cost_aggregation`
- `test_bot_costs_by_period`
- `test_system_costs_summary`
- `test_most_expensive_conversation`
- `test_different_model_pricing`

**Acceptance Criteria**:
- [ ] Per-conversation cost tracking
- [ ] Per-bot cost aggregation
- [ ] Model-aware pricing
- [ ] 6 tests passing

---

### 6.2 CRM Adapter Retry Logic

**Problem**: CRM adapters lack retry logic for transient failures.

**Current State**: `ghl_adapter.py`, `hubspot_adapter.py`, `salesforce_adapter.py` — no retry on 429/500/503.

**Required Changes**:

```
File: ghl_real_estate_ai/services/crm/retry_mixin.py (NEW)
Action: Retry mixin for CRM adapters

1. CRMRetryMixin class:
   - async retry_with_backoff(
       func: Callable,
       max_retries: int = 3,
       base_delay: float = 1.0,
       retryable_statuses: Set[int] = {429, 500, 502, 503}
     ) -> Any

2. Features:
   - Exponential backoff with jitter
   - Respect Retry-After header for 429 responses
   - Log retries with attempt number and delay
   - Circuit breaker: after 5 consecutive failures, open circuit for 60s
   - Metrics: retry_count, circuit_breaker_trips

3. Apply to all three adapters:
   - GHLAdapter.create_contact, update_contact, get_contact, search_contacts
   - HubSpotAdapter (same methods)
   - SalesforceAdapter (same methods)
```

**Test Requirements** (file: `tests/services/crm/test_retry_mixin.py`):
- `test_retry_on_429_with_backoff`
- `test_retry_on_500_server_error`
- `test_no_retry_on_400_client_error`
- `test_respect_retry_after_header`
- `test_max_retries_exceeded_raises`
- `test_circuit_breaker_opens_after_5_failures`
- `test_circuit_breaker_resets_after_timeout`

**Acceptance Criteria**:
- [ ] Exponential backoff with jitter
- [ ] Retry-After header respected
- [ ] Circuit breaker pattern
- [ ] Applied to all 3 adapters
- [ ] 7 tests passing

---

### 6.3 CRM Bulk Operations

**Problem**: CRM protocol lacks bulk create/update. Inefficient for batch operations.

**Current State**: `protocol.py` — only single-record CRUD.

**Required Changes**:

```
File: ghl_real_estate_ai/services/crm/protocol.py (MODIFY)
Action: Add bulk operation methods to CRMProtocol

1. Add to Protocol:
   - async bulk_create_contacts(contacts: List[CRMContact]) -> BulkResult
   - async bulk_update_contacts(updates: List[Dict]) -> BulkResult
   - async bulk_add_tags(contact_ids: List[str], tags: List[str]) -> BulkResult

2. BulkResult dataclass:
   - succeeded: int
   - failed: int
   - errors: List[Dict]  # {contact_id, error}
   - duration_ms: float
```

```
File: ghl_real_estate_ai/services/crm/ghl_adapter.py (MODIFY)
File: ghl_real_estate_ai/services/crm/hubspot_adapter.py (MODIFY)
File: ghl_real_estate_ai/services/crm/salesforce_adapter.py (MODIFY)
Action: Implement bulk operations per CRM's native API

- GHL: Loop with rate limiting (no native bulk API)
- HubSpot: POST /crm/v3/objects/contacts/batch/create
- Salesforce: POST /services/data/v57.0/composite/sobjects
```

**Test Requirements** (file: `tests/services/crm/test_bulk_operations.py`):
- `test_bulk_create_contacts`
- `test_bulk_update_contacts`
- `test_bulk_add_tags`
- `test_partial_failure_reported`
- `test_empty_batch_no_error`
- `test_ghl_rate_limited_batch`

**Acceptance Criteria**:
- [ ] Bulk operations on all 3 adapters
- [ ] Partial failure handling
- [ ] Rate limiting respected
- [ ] 6 tests passing

---

### 6.4 Handoff Analytics Dashboard Data

**Problem**: No handoff analytics aggregation for dashboards.

**Current State**: `_analytics` dict in `JorgeHandoffService` tracks raw counts but no aggregation endpoints.

**Required Changes**:

```
File: ghl_real_estate_ai/services/jorge/jorge_handoff_service.py (MODIFY)
Action: Add analytics aggregation methods

1. Add methods:
   - get_handoff_analytics(period: str = "24h") -> HandoffAnalytics
   - get_route_performance() -> Dict[str, RouteMetrics]
   - get_hourly_distribution() -> Dict[int, int]

2. HandoffAnalytics dataclass:
   - total: int
   - successful: int
   - failed: int
   - success_rate: float
   - avg_confidence: float
   - blocked_circular: int
   - blocked_rate_limit: int
   - by_route: Dict[str, int]
   - top_failure_reasons: List[str]
   - avg_processing_time_ms: float

3. RouteMetrics dataclass:
   - route: str  # "lead->buyer", "buyer->seller", etc.
   - count: int
   - success_rate: float
   - avg_confidence: float
   - avg_processing_time_ms: float
```

**Test Requirements** (file: `tests/services/test_handoff_analytics.py`):
- `test_analytics_aggregation_24h`
- `test_success_rate_calculation`
- `test_route_performance_breakdown`
- `test_hourly_distribution`
- `test_top_failure_reasons`
- `test_empty_analytics_zero_defaults`

**Acceptance Criteria**:
- [ ] Period-based aggregation
- [ ] Route-level metrics
- [ ] Failure reason tracking
- [ ] 6 tests passing

---

### 6.5 A/B Test Auto-Promotion

**Problem**: A/B testing service has no auto-promotion of winning variants.

**Current State**: `ab_testing_service.py` — manual experiment analysis only.

**Required Changes**:

```
File: ghl_real_estate_ai/services/jorge/ab_testing_service.py (MODIFY)
Action: Add auto-promotion logic

1. Add methods:
   - async check_experiment_winner(experiment_id: str) -> Optional[str]
   - async promote_variant(experiment_id: str, variant_id: str)
   - async get_promotion_history() -> List[PromotionEvent]

2. Winner detection criteria:
   - Minimum 100 observations per variant
   - Statistical significance p < 0.05 (already implemented)
   - Winner must have ≥ 5% relative improvement
   - Minimum experiment duration: 7 days

3. Promotion action:
   - Set winning variant to 100% traffic
   - Archive losing variants
   - Log PromotionEvent with timestamp, confidence, improvement_pct
   - Publish event for dashboard notification

4. Safety: Never auto-promote if total sample < 200 or duration < 7 days
```

**Test Requirements** (file: `tests/services/test_ab_auto_promotion.py`):
- `test_winner_detected_above_threshold`
- `test_no_winner_insufficient_data`
- `test_no_winner_insufficient_duration`
- `test_promote_sets_100_pct_traffic`
- `test_promotion_event_logged`
- `test_safety_minimum_sample_size`

**Acceptance Criteria**:
- [ ] Automatic winner detection
- [ ] Safety guardrails (min samples, min duration)
- [ ] Promotion event logging
- [ ] 6 tests passing

---

## 7. Phase 5 — Intelligence & Analytics (P2)

### 7.1 Conversation Quality Scorer

**Problem**: No automated assessment of bot conversation quality.

**Required Changes**:

```
File: ghl_real_estate_ai/services/jorge/conversation_scorer.py (NEW)
Action: Automated conversation quality scoring

1. ConversationScorer class:
   - score_conversation(messages: List[Dict]) -> QualityScore
   - score_response(bot_response: str, context: Dict) -> float

2. QualityScore dataclass:
   - overall: float  # 0-100
   - engagement: float  # Did buyer/seller respond substantively?
   - relevance: float  # Was bot response on-topic?
   - progression: float  # Did conversation move forward?
   - tone_appropriateness: float  # Professional, warm, not pushy?
   - compliance: float  # No Fair Housing violations?

3. Scoring heuristics (no AI call required):
   - Engagement: response length > 10 chars, question answered
   - Relevance: keyword overlap with bot question
   - Progression: new information extracted vs previous turn
   - Tone: absence of negative markers (ALL CAPS, "!!!", aggressive)
   - Compliance: absence of protected class mentions
```

**Test Requirements**: 6 tests
**Acceptance Criteria**: Heuristic-based scoring, no AI dependency, 6 tests passing

---

### 7.2 Lead Source Attribution

**Problem**: No tracking of which channels produce best-converting leads.

**Required Changes**:

```
File: ghl_real_estate_ai/services/jorge/lead_attribution.py (NEW)

1. LeadAttributionService class:
   - record_source(contact_id: str, source: str, medium: str)
   - get_source_performance(period: str) -> Dict[str, SourceMetrics]
   - get_conversion_by_source() -> Dict[str, float]

2. Sources: "ghl_form", "website", "zillow", "realtor.com",
   "referral", "social_media", "direct"

3. SourceMetrics: leads_count, qualified_count, conversion_rate,
   avg_qualification_time, avg_temperature
```

**Test Requirements**: 5 tests
**Acceptance Criteria**: Source tracking, conversion rate by source, 5 tests passing

---

### 7.3 Predictive Churn Detection

**Problem**: No early warning for leads going cold.

**Required Changes**:

```
File: ghl_real_estate_ai/services/jorge/churn_detector.py (NEW)

1. ChurnDetector class:
   - assess_churn_risk(contact_id: str, interaction_history: List) -> ChurnRisk
   - get_at_risk_contacts(threshold: float = 0.7) -> List[Dict]

2. ChurnRisk dataclass:
   - risk_score: float (0-1)
   - risk_factors: List[str]
   - recommended_action: str
   - days_since_last_interaction: int

3. Risk factors:
   - No response in 3+ days
   - Decreasing response length trend
   - Temperature dropping (hot → warm → cold)
   - Negative sentiment detected
   - Objection unresolved
```

**Test Requirements**: 6 tests
**Acceptance Criteria**: Multi-factor risk scoring, actionable recommendations, 6 tests passing

---

### 7.4 Buyer-Seller Match Detection

**Problem**: No detection of sell-first-then-buy scenarios (same contact as both buyer and seller).

**Required Changes**:

```
File: ghl_real_estate_ai/services/jorge/dual_intent_detector.py (NEW)

1. DualIntentDetector class:
   - detect_dual_intent(contact_id: str, messages: List[str]) -> DualIntentResult
   - create_linked_journey(contact_id: str, buyer_id: str, seller_id: str)

2. DualIntentResult dataclass:
   - is_dual: bool
   - primary_intent: str  # "buy_first" or "sell_first"
   - confidence: float
   - detected_signals: List[str]

3. Detection signals:
   - "sell before buy", "need to sell first"
   - "looking to upgrade/downsize"
   - "moving to/from {area}"
   - Contact has both buyer and seller tags

4. Linked journey enables coordinated messaging:
   - Seller bot: "Once we get your home sold, Jorge can help find your next home"
   - Buyer bot: "Let's also get your current home on the market to strengthen your offer"
```

**Test Requirements**: 6 tests
**Acceptance Criteria**: Dual intent detection, linked journey creation, 6 tests passing

---

### 7.5 Bot Performance Comparison Dashboard Data

**Problem**: No head-to-head comparison data between bots.

**Required Changes**:

```
File: ghl_real_estate_ai/services/jorge/bot_comparison.py (NEW)

1. BotComparisonService class:
   - compare_bots(period: str = "7d") -> BotComparison
   - get_efficiency_ranking() -> List[Dict]

2. BotComparison dataclass:
   - Per bot: qualification_rate, avg_conversations_to_qualify,
     avg_response_time_ms, cost_per_qualified_lead,
     handoff_success_rate, churn_rate

3. Efficiency ranking formula:
   score = (qualification_rate * 40) + (1/avg_time * 30) +
           (1/cost * 20) + (handoff_success * 10)
```

**Test Requirements**: 5 tests
**Acceptance Criteria**: Cross-bot comparison, efficiency ranking, 5 tests passing

---

## 8. Phase 6 — Integration Hardening (P2)

### 8.1 Chaos Engineering Test Suite

**Problem**: No failure injection tests. Unknown behavior under service failures.

**Required Changes**:

```
File: tests/chaos/test_buyer_bot_resilience.py (NEW)
File: tests/chaos/test_seller_bot_resilience.py (NEW)

Tests to implement:
1. Claude API timeout → verify fallback response returned
2. GHL API 500 error → verify graceful degradation
3. Property matcher unavailable → verify bot continues without matches
4. Handoff service failure → verify bot continues independently
5. Database connection failure → verify in-memory operation
6. Redis cache failure → verify bypass to direct API calls
7. All external services down → verify minimal safe response
```

**Test Requirements**: 14 tests (7 per bot)
**Acceptance Criteria**: All failure scenarios handled gracefully, no unhandled exceptions

---

### 8.2 Concurrent Conversation Handling

**Problem**: Unknown behavior under 50+ simultaneous conversations.

**Required Changes**:

```
File: tests/load/test_concurrent_conversations.py (NEW)

Tests to implement:
1. 10 concurrent buyer conversations → all complete correctly
2. 10 concurrent seller conversations → all complete correctly
3. Mixed buyer+seller concurrent → no cross-contamination
4. State isolation verification → each conversation independent
5. Performance under load → P95 < 3000ms with 20 concurrent
```

**Test Requirements**: 5 tests
**Acceptance Criteria**: No state leakage, performance within SLA

---

### 8.3 Long Conversation Handling

**Problem**: No tests for conversation pruning at MAX_CONVERSATION_HISTORY (50 messages).

**Required Changes**:

```
File: tests/agents/test_long_conversations.py (NEW)

Tests to implement:
1. 50+ message conversation → verify pruning behavior
2. State preservation after pruning → key context retained
3. Qualification data survives pruning → scores not lost
4. Handoff context preserved → enriched context intact
5. Token budget respected → response within limits
```

**Test Requirements**: 5 tests
**Acceptance Criteria**: Context preserved through pruning, no data loss

---

### 8.4 Buyer-Seller Handoff Round-Trip

**Problem**: No integration test for complete buyer→seller→response flow.

**Required Changes**:

```
File: tests/integration/test_buyer_seller_handoff.py (NEW)

Tests to implement:
1. Buyer detects seller intent → handoff executes
2. Seller bot receives enriched context → skips re-qualification
3. Seller detects buyer intent → reverse handoff
4. Circular handoff prevention → blocked within 30 minutes
5. Context preservation across handoff → scores, preferences carried
6. Rate limiting across handoff chain → 3/hr respected
```

**Test Requirements**: 6 tests
**Acceptance Criteria**: Full round-trip verified, context preserved, safeguards enforced

---

## 9. Testing Strategy

### Test Organization

```
tests/
├── agents/
│   ├── test_buyer_bot.py          # Existing + Phase 1/2 additions
│   └── test_long_conversations.py # Phase 6 NEW
├── services/
│   ├── test_tour_scheduler.py          # Phase 2 NEW
│   ├── test_property_comparison.py     # Phase 2 NEW
│   ├── test_offer_advisor.py           # Phase 2 NEW
│   ├── test_mortgage_tracker.py        # Phase 2 NEW
│   ├── test_saved_search.py            # Phase 2 NEW
│   ├── test_buyer_journey.py           # Phase 2 NEW
│   ├── test_cma_generator.py           # Phase 3 NEW
│   ├── test_listing_prep.py            # Phase 3 NEW
│   ├── test_seller_net_sheet.py        # Phase 3 NEW
│   ├── test_followup_engine.py         # Phase 3 NEW
│   ├── test_psychology_messaging.py    # Phase 3 NEW
│   ├── test_cost_tracker.py            # Phase 4 NEW
│   ├── test_handoff_analytics.py       # Phase 4 NEW
│   ├── test_ab_auto_promotion.py       # Phase 4 NEW
│   ├── test_seller_compliance_escalation.py  # Phase 1 NEW
│   ├── crm/
│   │   ├── test_retry_mixin.py         # Phase 4 NEW
│   │   └── test_bulk_operations.py     # Phase 4 NEW
│   └── jorge/
│       ├── test_conversation_scorer.py   # Phase 5 NEW
│       ├── test_lead_attribution.py      # Phase 5 NEW
│       ├── test_churn_detector.py        # Phase 5 NEW
│       ├── test_dual_intent_detector.py  # Phase 5 NEW
│       └── test_bot_comparison.py        # Phase 5 NEW
├── utils/
│   ├── test_pii_redactor.py               # Phase 1 NEW
│   └── test_conversation_rate_limiter.py  # Phase 1 NEW
├── chaos/
│   ├── test_buyer_bot_resilience.py    # Phase 6 NEW
│   └── test_seller_bot_resilience.py   # Phase 6 NEW
├── integration/
│   └── test_buyer_seller_handoff.py    # Phase 6 NEW
└── load/
    └── test_concurrent_conversations.py # Phase 6 NEW
```

### Test Conventions

- All tests use `pytest` with `pytest-asyncio` for async
- Mock external dependencies (Claude API, GHL, MLS) — never call real APIs
- Use `@pytest.fixture` for shared setup
- Use `@pytest.mark.parametrize` for multi-case testing
- Target: < 100ms per unit test
- Use factories (not raw dicts) for test data
- Follow existing patterns in `tests/agents/test_buyer_bot.py`

### Running Tests

```bash
# All new tests
pytest tests/ -k "test_tour_scheduler or test_property_comparison or test_offer_advisor" -v

# By phase
pytest tests/ -k "test_pii_redactor or test_conversation_rate_limiter or test_buyer_opt_out" -v  # Phase 1
pytest tests/services/test_tour_scheduler.py tests/services/test_property_comparison.py -v  # Phase 2

# Full suite
pytest tests/ -v --tb=short
```

---

## 10. File Reference Index

### Files to CREATE (19)

| File | Phase | Purpose |
|------|-------|---------|
| `utils/pii_redactor.py` | 1 | PII redaction utility |
| `utils/conversation_rate_limiter.py` | 1 | Per-contact rate limiting |
| `services/tour_scheduler.py` | 2 | Property tour booking |
| `services/property_comparison.py` | 2 | Multi-property comparison |
| `services/offer_advisor.py` | 2 | Offer strategy recommendations |
| `services/mortgage_tracker.py` | 2 | Pre-qualification tracking |
| `services/saved_search.py` | 2 | Buyer saved search alerts |
| `services/buyer_journey.py` | 2 | Journey stage tracking |
| `services/listing_prep.py` | 3 | Listing preparation checklists |
| `services/seller_net_sheet.py` | 3 | Seller net proceeds calculator |
| `services/followup_engine.py` | 3 | Automated follow-up execution |
| `services/jorge/cost_tracker.py` | 4 | Token cost tracking |
| `services/crm/retry_mixin.py` | 4 | CRM adapter retry logic |
| `services/jorge/conversation_scorer.py` | 5 | Conversation quality scoring |
| `services/jorge/lead_attribution.py` | 5 | Lead source tracking |
| `services/jorge/churn_detector.py` | 5 | Churn risk assessment |
| `services/jorge/dual_intent_detector.py` | 5 | Buy+sell intent detection |
| `services/jorge/bot_comparison.py` | 5 | Cross-bot comparison |
| Multiple test files | All | See Section 9 |

### Files to MODIFY (9)

| File | Phase | Changes |
|------|-------|---------|
| `agents/jorge_buyer_bot.py` | 1,2 | Opt-out, tour scheduling, comparison, offer advisor, journey tracking |
| `services/jorge/jorge_seller_engine.py` | 1,3 | Compliance escalation, listing prep, net sheet, follow-up |
| `services/jorge/jorge_tone_engine.py` | 3 | Psychology-aware messaging |
| `services/cma_generator.py` | 3 | Real data sources |
| `services/crm/protocol.py` | 4 | Bulk operation methods |
| `services/crm/ghl_adapter.py` | 4 | Retry mixin, bulk ops |
| `services/crm/hubspot_adapter.py` | 4 | Retry mixin, bulk ops |
| `services/crm/salesforce_adapter.py` | 4 | Retry mixin, bulk ops |
| `services/jorge/ab_testing_service.py` | 4 | Auto-promotion |
| `services/jorge/jorge_handoff_service.py` | 4 | Analytics aggregation |

---

## 11. Agent Execution Guide

### How to Use This Spec

Each section (3.1 through 8.4) is a **self-contained work item** designed for agent execution:

1. **Read the problem statement** — understand what's missing
2. **Read the current state** — check referenced files/lines
3. **Implement the required changes** — follow the spec precisely
4. **Write all specified tests** — match the test requirements exactly
5. **Verify acceptance criteria** — all checkboxes must pass
6. **Run existing tests** — ensure no regressions

### Phase Execution Order

```
Phase 1 (P0) → Phase 2 (P1) → Phase 3 (P1) → Phase 4 (P1) → Phase 5 (P2) → Phase 6 (P2)
```

Within each phase, items are independent and can be parallelized.

### Conventions

- All new files under `ghl_real_estate_ai/` (not project root)
- All new test files under `tests/` (not `ghl_real_estate_ai/tests/`)
- Follow existing import patterns (see `jorge_buyer_bot.py` for reference)
- Use `@dataclass` for simple data, Pydantic `BaseModel` for validated data
- All async methods use `async def` with proper `await`
- All services follow singleton pattern (like `PerformanceTracker`)
- SMS messages always < 160 chars (or 320 for multi-part)
- Log with `logger = logging.getLogger(__name__)`

### Estimated Scope

| Phase | Items | New Files | Modified Files | New Tests |
|-------|-------|-----------|----------------|-----------|
| 1 | 4 | 3 | 2 | +24 |
| 2 | 6 | 6 | 1 | +43 |
| 3 | 5 | 4 | 2 | +35 |
| 4 | 5 | 2 | 5 | +31 |
| 5 | 5 | 5 | 0 | +28 |
| 6 | 4 | 5 | 0 | +30 |
| **Total** | **29** | **25** | **10** | **+191** |

---

**End of Spec v4.7**
