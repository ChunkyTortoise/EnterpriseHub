# Jorge Bots Sprint Breakdown (Epic B + C First)

Date: 2026-02-16  
Source Spec: `plans/JORGE_BOTS_VALUE_OPTIMIZATION_SPEC_FEB16_2026.md`  
Planning Horizon: Sprint 1 (10 working days), with follow-on backlog callouts.

## Sprint Goal
Ship Epic B + C to raise seller qualification depth and canonical GHL field completeness, while protecting existing routing behavior.

## Ticket List (Sprint 1)

| Ticket | Epic | Scope | Primary Files | Owner | Estimate |
|---|---|---|---|---|---|
| JBV-B1 | B | Expand seller qualification from legacy 4-question flow to expanded intake sequence. | `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py` | Seller Runtime Engineer | 5 pts |
| JBV-B2 | B | Update seller extraction prompt and normalization to capture expanded intake fields. | `ghl_real_estate_ai/core/conversation_manager.py` | Conversation Intelligence Engineer | 5 pts |
| JBV-B3 | B | Add deterministic intake completion gate and persist completion state in context. | `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py`, `ghl_real_estate_ai/core/conversation_manager.py` | Seller Runtime Engineer | 3 pts |
| JBV-C1 | C | Define canonical seller data contract + required/preferred field sets in config. | `ghl_real_estate_ai/ghl_utils/jorge_config.py` | Data Contract Engineer | 3 pts |
| JBV-C2 | C | Implement canonical field write policy (merge-no-erase + per-turn updates). | `ghl_real_estate_ai/core/conversation_manager.py`, `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py` | Seller Runtime Engineer | 5 pts |
| JBV-C3 | C | Build mapping validator for required canonical GHL custom fields. | `ghl_real_estate_ai/ghl_utils/jorge_config.py`, `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py` | GHL Integration Engineer | 3 pts |
| JBV-C4 | C | Add canonical env placeholders/IDs for phased deploy configs. | `deploy/phase1_seller_only.env`, `deploy/phase2_seller_buyer.env`, `deploy/phase3_all_bots.env` | DevOps Engineer | 2 pts |
| JBV-QA1 | B/C | Add/adjust unit + integration tests for expanded intake and canonical mapping validation. | `ghl_real_estate_ai/tests/test_jorge_config_validation.py`, `tests/jorge_seller/test_seller_engine.py` | QA Automation Engineer | 5 pts |
| JBV-OBS1 | B/C | Emit completeness/qualification telemetry for rollout dashboard review. | `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py` | Observability Engineer | 2 pts |

Total Planned: 33 points

## Owner-by-File Matrix

| File | Owner |
|---|---|
| `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py` | Seller Runtime Engineer |
| `ghl_real_estate_ai/core/conversation_manager.py` | Conversation Intelligence Engineer |
| `ghl_real_estate_ai/ghl_utils/jorge_config.py` | Data Contract Engineer |
| `deploy/phase1_seller_only.env` | DevOps Engineer |
| `deploy/phase2_seller_buyer.env` | DevOps Engineer |
| `deploy/phase3_all_bots.env` | DevOps Engineer |
| `ghl_real_estate_ai/tests/test_jorge_config_validation.py` | QA Automation Engineer |
| `tests/jorge_seller/test_seller_engine.py` | QA Automation Engineer |

## Delivery Sequence (Recommended)

1. JBV-C1 -> JBV-C3 (contract and validator foundation).
2. JBV-B2 -> JBV-B1 -> JBV-B3 (extraction, question flow, deterministic completion).
3. JBV-C2 -> JBV-C4 (write policy + deploy mapping readiness).
4. JBV-QA1 and JBV-OBS1 in parallel once core code paths are merged.

## Definition of Done (Sprint 1)

1. Expanded seller intake fields are captured and persisted without null-overwrite regressions.
2. Qualification state is deterministic and auditable (`qualification_complete`, `last_bot_interaction`, provenance).
3. Canonical contract mapping validator reports missing GHL field IDs before production rollout.
4. Phase env templates include canonical seller field mappings/placeholders for all rollout phases.
5. Test coverage includes expanded intake progression and mapping-validator behavior.

## Next Sprint Candidates (Not In Current Scope)

1. Epic D appointment path hardening (strict 30-minute consult type).
2. Epic E lifecycle cadence redesign (HOT daily, WARM weekly, COLD monthly).
3. Epic F tone/compliance lock and expanded guardrail matrix.
4. Epic G KPI dashboard and A/B auto-rollback controls.
