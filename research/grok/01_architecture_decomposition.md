# Architecture Decomposition Analysis

**Generated**: 2026-03-19
**Analyst**: Claude Sonnet 4.6
**Scope**: `ghl_real_estate_ai/` package — FastAPI monorepo for Rancho Cucamonga real estate AI

---

## Current Service Structure

### File Counts (raw)
| Location | Count |
|---|---|
| `services/` root (`.py` files, no subdirs) | 428 |
| `services/jorge/` | ~45 |
| `services/scoring/` | 7 |
| `services/assistant/` | 5 |
| `services/crm/` | 4 |
| `api/routes/` | 86 |
| **Total Python files (entire package)** | **1,352** |

### God-Class Files (top 6 by line count)
| File | Lines | Responsibility Sprawl |
|---|---|---|
| `services/event_publisher.py` | 3,144 | 75 `publish_*` methods, batching, routing, metrics, filtering, grade calculations |
| `agents/lead_bot.py` | 2,815 | Graph construction, day-3/7/14/30 logic, handoff, sequence scheduling, ML analytics, email sending, CMA |
| `api/routes/webhook.py` | 2,715 | Tag routing, mode detection, bot dispatch, billing, handoff, compliance, slot selection |
| `services/realtime_behavioral_network.py` | 2,584 | Real-time inference + behavioral network logic |
| `services/jorge/jorge_seller_engine.py` | 2,456 | Full seller conversation engine embedded in a single class |
| `api/routes/billing.py` | 1,525 | 10+ endpoints + retry logic + internal billing helpers |

### Versioned/Duplicate Service Files (partial)
428 flat service files include heavy naming collisions:
- **Cache**: `cache_service.py`, `cache_service_optimized.py`, `optimized_cache_service.py`, `tiered_cache_service.py`, `semantic_cache_service.py`, `semantic_cache_optimized.py`, `bi_cache_service.py` (7 files)
- **Event publishing**: `event_publisher.py`, `optimized_event_publisher.py`, `enhanced_event_publisher_extensions.py`, `event_streaming_service.py` (4 files)
- **Analytics**: `analytics_engine.py`, `analytics_service.py`, `advanced_analytics.py`, `advanced_analytics_engine.py`, `advanced_analytics_visualization_engine.py`, `campaign_analytics.py`, `bi_stream_processor.py`, `bi_websocket_server.py`, `business_intelligence_reporting_engine.py` (9 files)
- **Lead scoring**: `lead_scorer.py`, `lead_scoring_service.py`, `lead_scoring_v2.py`, `enhanced_lead_scorer.py`, `enhanced_lead_scoring.py`, `enhanced_smart_lead_scorer.py`, `claude_enhanced_lead_scorer.py`, `advanced_ml_lead_scoring_engine.py`, `ai_predictive_lead_scoring.py`, `ensemble_lead_scoring.py`, `lead_scoring_integration.py` (11 files)
- **GHL client**: `ghl_client.py`, `enhanced_ghl_client.py`, `ghl_api_client.py`, `ghl_batch_client.py`, `secure_ghl_client.py`, `ghl_service.py` (6 files)
- **Behavioral triggers**: `behavioral_triggers.py`, `behavioral_trigger_engine.py`, `behavioral_trigger_detector.py`, `ai_behavioral_triggers.py`, `behavioral_signal_extractor.py`, `behavioral_weighting_engine.py` (6 files)
- **Claude AI**: `claude_orchestrator.py`, `claude_assistant.py`, `claude_assistant_optimized.py`, `claude_concierge_orchestrator.py`, `claude_automation_engine.py`, `claude_platform_companion.py`, `claude_lead_qualification.py`, `claude_conversation_intelligence.py` (8 files)
- **Churn**: `churn_prediction_engine.py`, `churn_detection_service.py`, `churn_integration_service.py`, `churn_intervention_orchestrator.py`, `churn_bot_integration.py` (5 files)
- **Routes duplication**: `market_intelligence.py` + `market_intelligence_v2.py` + `market_intelligence_phase7.py` + `rc_market_intelligence.py`; `lead_intelligence.py` + `lead_intelligence_v2.py`; `revenue_optimization.py` + `revenue_v2.py`; `compliance.py` + `fha_respa_compliance.py` + `inbound_compliance.py` + `sms_compliance.py`

### Import Fragmentation (measured)
| Service Group | Import Count Across Codebase |
|---|---|
| `cache_service*` variants | 269 |
| `claude_orchestrator*` variants | 112 |
| `event_publisher*` variants | 64 |
| `analytics_service*` variants | 66 |
| `lead_scorer*` variants | 28 |
| `ghl_client*` variants | 52 |

---

## Domain Boundaries Identified

Seven natural bounded contexts emerge from the codebase:

### 1. Bot Conversation Domain (`bots/`)
**What it is**: The three Jorge bots (Lead, Buyer, Seller) plus the multi-bot handoff orchestration.

**Current files**:
- `agents/lead_bot.py`, `agents/jorge_buyer_bot.py`, `agents/jorge_seller_bot.py`
- `services/jorge/` (45 files): handoff, A/B testing, performance tracking, alerting, cost tracking, analytics sub-package
- `agents/intent_decoder.py`, `agents/cma_generator.py`, `agents/base_bot_workflow.py`
- `services/bot_intelligence_middleware.py`, `services/agent_mesh_coordinator.py`

**Owns**: conversation state, qualification flows, handoff routing, sequence scheduling, bot metrics, prompt experiments

**Does NOT own**: GHL API calls (uses GHL domain), lead scoring (uses Intelligence domain), compliance checks (uses Compliance domain)

---

### 2. Intelligence & Scoring Domain (`intelligence/`)
**What it is**: All ML-based lead scoring, behavioral analytics, churn prediction, and predictive models.

**Current files**:
- `services/lead_scorer.py` + 10 duplicates
- `services/behavioral_trigger_engine.py` + 5 duplicates
- `services/churn_prediction_engine.py` + 4 related
- `services/predictive_analytics_engine.py`, `services/advanced_ml_lead_scoring_engine.py`
- `services/psychographic_segmentation_engine.py`, `services/sentiment_drift_engine.py`
- `services/ensemble_lead_scoring.py`, `services/dynamic_scoring_weights.py`

**Owns**: scoring models, feature extraction, behavioral signal classification, churn risk, propensity scoring

**Does NOT own**: event broadcasting, GHL field updates, conversation logic

---

### 3. GHL Integration Domain (`crm/`)
**What it is**: All GoHighLevel CRM interaction — contacts, conversations, workflows, tags, custom fields, webhooks.

**Current files**:
- `services/ghl_client.py`, `services/enhanced_ghl_client.py`, `services/ghl_api_client.py`, `services/ghl_batch_client.py`, `services/secure_ghl_client.py`
- `services/ghl_service.py`, `services/ghl_sync_service.py`, `services/ghl_live_data_service.py`
- `services/ghl_conversation_bridge.py`, `services/ghl_webhook_service.py`
- `services/ghl_workflow_service.py`, `services/ghl_workflow_integration.py`
- `api/routes/webhook.py` (dispatch logic), `api/routes/crm.py`
- `services/crm/` subdirectory (adapters for GHL, HubSpot, Salesforce)

**Owns**: GHL API calls, tag management, custom field writes, conversation threading, webhook parsing, rate limiting

---

### 4. Real-Time & Events Domain (`realtime/`)
**What it is**: WebSocket server, event publishing pipeline, BI data streaming, and real-time cache warming.

**Current files**:
- `services/event_publisher.py` + 3 duplicates
- `services/websocket_server.py`, `services/bi_websocket_server.py`
- `services/bi_stream_processor.py`, `services/event_streaming_service.py`
- `services/realtime_data_service.py`, `services/realtime_integration.py`
- `api/routes/websocket_routes.py`, `api/routes/bi_websocket_routes.py`, `api/routes/websocket_performance.py`

**Owns**: WebSocket connections, event fanout, event batching/aggregation, real-time dashboard feeds

---

### 5. Analytics & BI Domain (`analytics/`)
**What it is**: Business intelligence reporting, campaign analytics, attribution, market intelligence, and Streamlit dashboards.

**Current files**:
- `services/analytics_engine.py`, `services/analytics_service.py`, `services/advanced_analytics_engine.py`, `services/advanced_analytics.py`
- `services/campaign_analytics.py`, `services/attribution_analytics.py`, `services/revenue_attribution_system.py`
- `services/business_intelligence_reporting_engine.py`, `services/bi_cache_service.py`
- `services/market_intelligence_engine.py`, `services/market_intelligence.py`, `services/rancho_cucamonga_market_service.py`
- `streamlit_demo/` (entire Streamlit BI layer)
- `api/routes/analytics.py`, `api/routes/enterprise_analytics.py`, `api/routes/business_intelligence.py`
- `api/routes/market_intelligence.py`, `api/routes/market_intelligence_v2.py`, `api/routes/market_intelligence_phase7.py`

**Owns**: KPI computation, report generation, market data aggregation, visualization data prep

---

### 6. Billing & Subscriptions Domain (`billing/`)
**What it is**: Stripe integration, subscription lifecycle, usage metering, invoice management.

**Current files**:
- `services/billing_service.py`, `services/subscription_manager.py`, `services/usage_billing_service.py`
- `services/corporate_billing_service.py`, `services/revenue_attribution.py`, `services/revenue_attribution_service.py`
- `api/routes/billing.py`, `api/routes/checkout.py`, `api/routes/revenue_optimization.py`, `api/routes/revenue_v2.py`

**Owns**: Stripe webhooks, subscription state, metered billing, invoice generation, tier enforcement

---

### 7. Compliance & Security Domain (`compliance/`)
**What it is**: TCPA, FHA/RESPA, Fair Housing, CCPA enforcement plus auth, PII encryption, and rate limiting.

**Current files**:
- `services/compliance_guard.py`, `services/compliance_middleware.py`, `services/enhanced_compliance_risk.py`, `services/compliance_escalation.py`
- `services/sms_compliance_service.py`, `services/security_framework.py`, `services/security_monitor.py`
- `services/auth_service.py`, `services/auth_middleware.py`, `services/enhanced_database_security.py`
- `compliance_platform/` (standalone sub-package with engine, realtime monitoring, multi-tenancy)
- `api/routes/compliance.py`, `api/routes/fha_respa_compliance.py`, `api/routes/inbound_compliance.py`, `api/routes/sms_compliance.py`, `api/routes/security.py`
- `services/jorge/response_pipeline/` (TCPA opt-out processor, AI disclosure processor)

**Owns**: regulatory enforcement, opt-out handling, PII masking, JWT auth, rate limiting, audit trails

---

### 8. Property & Market Domain (`property/`) — *overlaps with Analytics*
**What it is**: MLS data, property matching, listing generation, market timing, neighborhood intelligence.

**Current files**:
- `services/mls_client.py`, `services/attom_client.py`, `services/simulated_mls_feed.py`
- `services/property_matcher.py` + 4 variants, `services/advanced_property_matching_engine.py`
- `services/market_intelligence.py`, `services/real_time_market_intelligence.py`, `services/market_prediction_engine.py`
- `services/neighborhood_intelligence_service.py`, `services/neighborhood_insights.py`
- `services/ai_listing_writer.py`, `services/listing_intelligence_service.py`, `services/intelligent_listing_generator.py`
- `api/routes/properties.py`, `api/routes/property_intelligence.py`, `api/routes/neighborhood_intelligence.py`

**Owns**: property search, MLS feed parsing, CMA data, market comps, neighborhood scoring

---

## God-Class Decomposition Plans

### Plan A: `services/event_publisher.py` (3,144 lines → 4 modules)

**Problem**: A single `EventPublisher` class with 75 domain-specific `publish_*` methods, private batching infrastructure, private routing helpers, and module-level convenience functions. The class knows about bot qualification progress, churn alerts, property matches, billing events, sentiment warnings, and WebSocket connections simultaneously.

**Decomposition**:

```
services/realtime/
├── __init__.py
├── event_publisher.py          # Core EventPublisher (start/stop, _publish_event, batching, metrics)
│                               # ~400 lines — infrastructure only
├── lead_events.py              # publish_lead_update, publish_conversation_update,
│                               # publish_lead_bot_sequence_update, publish_intent_analysis_complete
│                               # ~250 lines
├── bot_events.py               # publish_jorge_qualification_progress, publish_bot_handoff_request,
│                               # publish_seller_bot_message_processed, publish_bot_status_update,
│                               # publish_buyer_qualification_*, publish_coaching_opportunity
│                               # ~500 lines
├── property_events.py          # publish_property_alert, publish_property_match_generated,
│                               # publish_property_inventory_update, publish_behavioral_match_improvement,
│                               # publish_preference_learning_complete, publish_preference_drift_detected
│                               # ~600 lines
├── behavioral_events.py        # publish_churn_risk_alert, publish_behavior_category_change,
│                               # publish_engagement_trend_change, publish_behavioral_prediction,
│                               # publish_sentiment_warning, publish_objection_detected
│                               # ~600 lines
└── system_events.py            # publish_system_alert, publish_performance_update,
                                # publish_dashboard_refresh, publish_system_health_update,
                                # publish_ai_concierge_status_update, publish_commission_update
                                # ~300 lines
```

**Migration path**: Core `EventPublisher` stays at `services/event_publisher.py` for backward compatibility. The domain-specific publishers become mixins or delegates. All 50 existing import sites continue to work through re-exports in `services/event_publisher.py`.

**Circular risk eliminated**: Domain publishers import only the core `EventPublisher` and `RealTimeEvent` — no cross-domain dependencies.

---

### Plan B: `agents/lead_bot.py` (2,815 lines → 5 modules)

**Problem**: `LeadBotWorkflow` is responsible for: (1) LangGraph graph construction for standard and enhanced flows, (2) all day-3/7/14/30 follow-up message generation, (3) CMA email rendering and attachment, (4) ghost re-engagement strategy, (5) ML analytics integration, (6) handoff signal detection, (7) sequence scheduling coordination, (8) voice call initiation via Retell, (9) performance metrics and health checks.

**Decomposition**:

```
agents/lead/
├── __init__.py                  # Re-exports LeadBotWorkflow for backward compat
├── lead_bot.py                  # LeadBotWorkflow (thin orchestrator)
│                                # __init__, process_lead_conversation, health_check, factory classmethods
│                                # ~300 lines
├── lead_graph_builder.py        # _build_standard_graph(), _build_enhanced_graph(), _build_unified_graph()
│                                # Route functions, graph wiring
│                                # ~250 lines
├── sequence_nodes.py            # gather_lead_intelligence, analyze_intent, determine_path,
│                                # send_day_3_sms, initiate_day_7_call, send_day_14_email,
│                                # send_day_30_nudge, send_optimized_day_3, initiate_predictive_day_7,
│                                # send_adaptive_day_14, send_intelligent_day_30
│                                # ~900 lines — pure async graph nodes
├── follow_up_messages.py        # _construct_intelligent_day3_message, _construct_adaptive_day14_message,
│                                # _construct_intelligent_day30_message, _select_stall_breaker,
│                                # _determine_escrow_milestone, _get_milestone_message,
│                                # _build_cma_email_html
│                                # ~400 lines — message templates and construction
└── lead_intelligence.py         # analyze_behavioral_patterns, predict_sequence_optimization,
                                 # apply_track3_market_intelligence, _apply_market_timing_intelligence,
                                 # _detect_critical_scenarios, check_handoff_signals,
                                 # _extract_churn_risk_from_intelligence
                                 # ~600 lines — ML/analytics integration layer
```

**Migration path**: `agents/lead_bot.py` becomes a thin re-export shim for 6 months. The existing `from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow` import at `services/ghl_live_data_service.py` and all test files continue to work.

**Key insight**: `sequence_nodes.py` methods are stateless graph nodes that only read from `state: LeadFollowUpState` and return dicts — they have zero internal coupling to each other. This makes the split mechanical.

---

### Plan C: `api/routes/webhook.py` (2,715 lines → 4 route modules + 2 utility modules)

**Problem**: A single router (`/ghl`) handles: (1) tag-based bot routing (selecting lead/buyer/seller/off mode), (2) full bot dispatch for all 3 bot types, (3) response post-processing pipeline, (4) GHL action building (tags, custom fields), (5) billing usage recording, (6) compliance check inline, (7) calendar slot selection logic, (8) health check, and (9) qualification initiation. It also instantiates 10 services as module-level singletons.

**Decomposition**:

```
api/routes/ghl/
├── __init__.py
├── webhook_core.py              # handle_ghl_webhook() — main entry point only, delegates to handlers
│                                # handle_ghl_tag_webhook() — tag classification and mode detection
│                                # _compute_mode_flags(), _select_primary_mode(), _normalize_tags()
│                                # ~300 lines
├── bot_dispatch.py              # Lead bot dispatch, Buyer bot dispatch, Seller bot dispatch
│                                # _get_tenant_ghl_client(), safe_send_message(), safe_apply_actions()
│                                # ~600 lines
├── ghl_actions.py               # prepare_ghl_actions() — all GHL tag/field action assembly
│                                # _build_cc_workflow_actions(), _calculate_lead_pricing()
│                                # _handle_billing_usage()
│                                # ~500 lines
├── routing_helpers.py           # _detect_buy_sell_intent(), _detect_negative_sentiment(),
│                                # _detect_rejected_offer(), _signals_to_handoff_profile(),
│                                # _select_slot_from_message(), _format_slot_options()
│                                # ~200 lines
├── qualification.py             # initiate_qualification() endpoint, health_check() endpoint
│                                # ~150 lines
└── dependencies.py              # All FastAPI Depends() factories (replaces 10 module-level singletons)
                                 # _get_conversation_manager(), _get_ghl_client_default(), etc.
                                 # ~150 lines
```

**Migration path**: Register the sub-router from `api/routes/ghl/__init__.py` at the same `/ghl` prefix. All existing API consumers are unaffected. The 10 module-level service singletons migrate to `dependencies.py` using FastAPI's dependency injection — this eliminates the current test-time initialization problem where importing `webhook.py` instantiates all services.

---

## Recommended Package Structure

Target: modular monolith with clear domain packages. No microservices — shared database, single deployment, but clear module ownership.

```
ghl_real_estate_ai/
├── core/                          # Framework plumbing (no business logic)
│   ├── llm_client.py              # LLMClient (stays)
│   ├── conversation_manager.py    # ConversationManager (stays)
│   └── mcp_servers/               # MCP server definitions (stays)
│
├── domains/                       # NEW: replaces flat services/
│   ├── bots/                      # Bot Conversation Domain
│   │   ├── lead/                  # Decomposed from agents/lead_bot.py
│   │   ├── buyer/                 # Decomposed from agents/jorge_buyer_bot.py
│   │   ├── seller/                # Decomposed from agents/jorge_seller_bot.py
│   │   ├── handoff/               # services/jorge/jorge_handoff_service.py + router
│   │   ├── pipeline/              # services/jorge/response_pipeline/ (stays)
│   │   ├── metrics/               # services/jorge/bot_metrics_collector.py, alerting_service.py, performance_tracker.py
│   │   └── experiments/           # services/jorge/ab_testing_service.py, prompt_experiment_runner.py
│   │
│   ├── intelligence/              # Intelligence & Scoring Domain
│   │   ├── scoring/               # CONSOLIDATES: lead_scorer.py + all variants → scorer.py
│   │   ├── behavioral/            # CONSOLIDATES: behavioral_trigger* → triggers.py
│   │   ├── churn/                 # CONSOLIDATES: churn_prediction* + churn_detection* → churn.py
│   │   ├── predictive/            # predictive_analytics_engine.py, predictive_lead_scorer.py
│   │   └── psychographic/         # psychographic_segmentation_engine.py, sentiment_drift_engine.py
│   │
│   ├── crm/                       # GHL Integration Domain
│   │   ├── client.py              # CONSOLIDATES: ghl_client.py + enhanced_ghl_client.py → single GHLClient
│   │   ├── batch.py               # ghl_batch_client.py
│   │   ├── sync.py                # ghl_sync_service.py, ghl_conversation_bridge.py
│   │   ├── workflows.py           # ghl_workflow_service.py + ghl_workflow_integration.py
│   │   └── webhooks.py            # ghl_webhook_service.py
│   │
│   ├── realtime/                  # Real-Time & Events Domain
│   │   ├── publisher.py           # Core EventPublisher infrastructure (~400 lines)
│   │   ├── lead_events.py         # Lead-specific publish methods
│   │   ├── bot_events.py          # Bot-specific publish methods
│   │   ├── property_events.py     # Property-specific publish methods
│   │   ├── behavioral_events.py   # Behavioral/churn publish methods
│   │   ├── system_events.py       # System/performance publish methods
│   │   └── websocket.py           # CONSOLIDATES: websocket_server.py + bi_websocket_server.py
│   │
│   ├── analytics/                 # Analytics & BI Domain
│   │   ├── engine.py              # CONSOLIDATES: analytics_engine.py + analytics_service.py
│   │   ├── bi_reporting.py        # business_intelligence_reporting_engine.py
│   │   ├── attribution.py         # attribution_analytics.py + revenue_attribution_system.py
│   │   ├── campaign.py            # campaign_analytics.py
│   │   └── market/                # market_intelligence_engine.py, rancho_cucamonga_market_service.py
│   │
│   ├── billing/                   # Billing & Subscriptions Domain
│   │   ├── service.py             # BillingService (stays)
│   │   ├── subscriptions.py       # SubscriptionManager (stays)
│   │   ├── usage.py               # usage_billing_service.py
│   │   └── revenue.py             # revenue_attribution.py + revenue_attribution_service.py
│   │
│   ├── compliance/                # Compliance & Security Domain
│   │   ├── guard.py               # compliance_guard.py (stays)
│   │   ├── middleware.py          # compliance_middleware.py (stays)
│   │   ├── sms.py                 # sms_compliance_service.py
│   │   ├── security.py            # security_framework.py + security_monitor.py
│   │   └── auth.py                # auth_service.py + auth_middleware.py
│   │
│   └── property/                  # Property & Market Domain
│       ├── mls.py                 # mls_client.py + simulated_mls_feed.py
│       ├── matching.py            # CONSOLIDATES: property_matcher.py + 4 variants
│       ├── market.py              # market_intelligence.py, real_time_market_intelligence.py
│       ├── neighborhood.py        # neighborhood_intelligence_service.py + neighborhood_insights.py
│       └── listings.py            # ai_listing_writer.py + intelligent_listing_generator.py
│
├── api/                           # HTTP layer (thin — delegates to domains/)
│   ├── routes/ghl/                # Decomposed webhook.py
│   └── routes/                    # Other routes (consolidated, see Merge section)
│
├── cache/                         # CONSOLIDATES all cache variants
│   └── service.py                 # Single CacheService with tiered L1/L2/L3 strategy
│
├── agents/                        # Bot entry points (thin — delegates to domains/bots/)
│   ├── lead_bot.py                # Re-export shim during migration
│   ├── jorge_buyer_bot.py         # Re-export shim during migration
│   └── jorge_seller_bot.py        # Re-export shim during migration
│
├── models/                        # Unchanged
├── streamlit_demo/                # Unchanged
└── utils/                         # Unchanged
```

---

## Merge/Delete Candidates

### High Priority: Consolidate (duplicate functionality, pick the best)

| Cluster | Files to Merge | Target | Decision Basis |
|---|---|---|---|
| Cache service | `cache_service.py`, `cache_service_optimized.py`, `optimized_cache_service.py`, `tiered_cache_service.py` | `cache/service.py` | `tiered_cache_service.py` has L1/L2/L3 design — keep it, deprecate others |
| Semantic cache | `semantic_cache_service.py`, `semantic_cache_optimized.py`, `bi_cache_service.py` | `cache/semantic.py` | Merge; 269 import sites make this urgent |
| GHL client | `ghl_client.py`, `ghl_api_client.py`, `secure_ghl_client.py` | `crm/client.py` | `enhanced_ghl_client.py` is the most complete; others are subsets |
| Event publisher | `event_publisher.py`, `optimized_event_publisher.py`, `enhanced_event_publisher_extensions.py` | `realtime/publisher.py` | Decompose per Plan A; `optimized_event_publisher.py` has micro-batching improvements to merge in |
| Lead scoring | `lead_scorer.py`, `lead_scoring_service.py`, `lead_scoring_v2.py`, `enhanced_lead_scorer.py`, `enhanced_lead_scoring.py`, `enhanced_smart_lead_scorer.py` | `intelligence/scoring/scorer.py` | `enhanced_smart_lead_scorer.py` + `ensemble_lead_scoring.py` are most recent |
| Analytics engine | `analytics_engine.py`, `analytics_service.py`, `advanced_analytics.py` | `analytics/engine.py` | `analytics_service.py` is most referenced (66 imports); keep its interface |
| Behavioral triggers | `behavioral_triggers.py`, `behavioral_trigger_engine.py`, `behavioral_trigger_detector.py`, `ai_behavioral_triggers.py` | `intelligence/behavioral/triggers.py` | `behavioral_trigger_engine.py` is most complete |
| Churn | `churn_prediction_engine.py`, `churn_detection_service.py`, `churn_integration_service.py` | `intelligence/churn/service.py` | `churn_prediction_engine.py` (1,671 lines) is the primary |

### Route Consolidations

| Current Files | Merged Target |
|---|---|
| `market_intelligence.py`, `market_intelligence_v2.py`, `market_intelligence_phase7.py`, `rc_market_intelligence.py` | `analytics/routes/market.py` |
| `lead_intelligence.py`, `lead_intelligence_v2.py` | `bots/routes/lead_intelligence.py` |
| `revenue_optimization.py`, `revenue_v2.py`, `commission_forecast.py` | `billing/routes/revenue.py` |
| `compliance.py`, `fha_respa_compliance.py`, `inbound_compliance.py`, `sms_compliance.py` | `compliance/routes/compliance.py` |
| `claude_chat.py`, `claude_concierge.py`, `claude_concierge_integration.py`, `ai_concierge.py`, `concierge_admin.py` | `bots/routes/concierge.py` |
| `websocket_routes.py`, `bi_websocket_routes.py`, `websocket_performance.py` | `realtime/routes/websocket.py` |

### Delete Candidates (superseded or experimental)

| File | Reason |
|---|---|
| `services/realtime_inference_engine.py` | Superseded by `realtime_inference_engine_v2.py` |
| `services/claude_assistant.py` | Thin wrapper; callers should use `claude_orchestrator.py` |
| `services/claude_assistant_optimized.py` | Same — duplicates orchestrator logic with caching |
| `api/routes/phase2_intelligence.py` | Phase-specific naming implies temporary; absorb or delete |
| `api/routes/market_intelligence_phase7.py` | Phase-specific; consolidate into market route |
| `api/routes/predictive_endpoints.txt`, `api/routes/executive_dashboard_endpoints.txt` | Text files in routes dir — documentation belongs in `docs/` |

---

## Circular Dependency Risks

### Confirmed Circular Patterns

**1. `claude_orchestrator.py` ↔ services that extend it**
`claude_orchestrator.py` uses local-scope imports (`from ghl_real_estate_ai.services.X import Y` inside `__init__`) to break import-time cycles. Six services confirmed using this pattern:
- `claude_enhanced_lead_scorer.py` imports orchestrator at method call time
- `claude_assistant.py` imports orchestrator inside `__init__`
- `performance_optimization_service.py` imports orchestrator inside a method

Root cause: `claude_orchestrator.py` imports from `behavioral_triggers`, `churn_prediction_engine`, `lead_scorer`, `predictive_lead_scorer` — all of which reference AI services that eventually touch the orchestrator.

**Fix**: Introduce a `core/llm_client.py`-level interface (`LLMOrchestrator` protocol). Domain services depend on the protocol, not the concrete class. `ClaudeOrchestrator` lives in `domains/bots/orchestration.py` and imports from domains — not the other way.

**2. `agents/lead_bot.py` ↔ `services/ghl_live_data_service.py`**
`ghl_live_data_service.py` imports `LeadBotWorkflow` from `agents/lead_bot.py`. `lead_bot.py` uses `ghl_client` via injection but doesn't import `ghl_live_data_service` — the cycle is one-way. However, any future addition in `lead_bot.py` that imports `ghl_live_data_service` would create a hard cycle.

**Fix**: `ghl_live_data_service.py` should depend on an abstract `BotWorkflow` protocol, not the concrete `LeadBotWorkflow`.

**3. `services/event_publisher.py` fan-out**
50 files import `event_publisher`. As long as `event_publisher.py` imports from `cache_service` and `websocket_server`, any domain service that imports from those and also emits events has a potential cycle. Currently latent — the publisher avoids importing domain services — but 126 circular workarounds across the codebase are a warning sign.

**Fix**: The `EventPublisher` class must remain a leaf node (no domain service imports). Domain-specific event builders should be in separate files that import the publisher but are not imported by it.

**4. `compliance_platform/` shadow package**
`compliance_platform/` is a nearly self-contained sub-package with its own `engine/`, `api/`, `database/`, `realtime/`. However, its `realtime/notification_service.py` imports from `services/` — creating a shadow dependency from the compliance sub-package back into the main services layer. This is a one-way dependency currently but the `compliance_platform/` package is not cleanly isolated.

**Fix**: Define a notification interface in `compliance_platform/` that the main services implement (inversion of control), rather than the compliance platform calling service layer directly.

---

## Migration Strategy

This is a 4-phase migration designed to ship continuously without a rewrite.

### Phase 1: Stabilize (Weeks 1-4) — No structure changes
**Goal**: Stop the bleeding. Make the existing mess safe to navigate.

1. **Add import guards to all 126 circular workarounds** — document in `docs/circular_imports.md` which imports are local-scope and why.
2. **Create `cache/service.py`** as a unified facade over the 7 cache variants. All new code imports from `cache/service.py`. Do not delete old files yet.
3. **Freeze the `api/routes/` directory** — no new route files until consolidation. Route additions go into existing files.
4. **Tag god-class files with `# DECOMPOSITION: see research/grok/01_architecture_decomposition.md`** comments.
5. **Add `__all__` to every `__init__.py` in `services/`** to make public surfaces explicit.

---

### Phase 2: Extract Domain Packages (Weeks 5-12)
**Goal**: Create the 8 domain directories with re-export shims.

One domain at a time, in dependency order (least-imported first):

1. **`compliance/`** — minimal inbound imports; extract `auth.py`, `guard.py`, `sms.py`
2. **`billing/`** — only imports from compliance + stripe; extract `service.py`, `subscriptions.py`
3. **`crm/`** — consolidate GHL clients to single `client.py`; delete 4 GHL client variants after updating 52 import sites
4. **`property/`** — consolidate 5 property_matcher variants
5. **`realtime/`** — decompose `event_publisher.py` per Plan A; consolidate 3 cache variants
6. **`intelligence/`** — consolidate 11 lead scoring variants → `scorer.py`; 6 behavioral variants → `triggers.py`; 5 churn variants → `churn.py`
7. **`analytics/`** — consolidate 9 analytics variants
8. **`bots/`** — decompose `lead_bot.py` per Plan B; decompose `webhook.py` per Plan C

At each step: update imports, run `pytest tests/`, measure no regression.

---

### Phase 3: Route Consolidation (Weeks 13-16)
**Goal**: Reduce 86 route files to ~20 clean domain routes.

Apply the route consolidation table from the Merge/Delete section. Each merge:
1. Create the target file with all endpoints
2. Register the new router in `app.py`
3. Remove the old router registrations
4. Delete old files only after verifying 0 references remain

---

### Phase 4: Enforce Module Boundaries (Weeks 17-20)
**Goal**: Prevent re-accumulation.

1. **Add `import-linter`** rules (one per domain boundary) to CI. Example: `bots` domain cannot import from `analytics` domain directly — must go through events.
2. **Delete all re-export shims** from migration phases 1-2.
3. **Delete all confirmed dead files** (phase-specific routes, superseded engine variants).
4. **Add architecture decision records (ADRs)** in `docs/adr/` for each boundary decision.
5. **Update `CLAUDE.md`** with the new module ownership map.

---

## Summary Risk Table

| Risk | Severity | Mitigation |
|---|---|---|
| 269 import sites for cache service variants | HIGH | Phase 1 unified facade; Phase 2 consolidation |
| 126 local-scope import workarounds | HIGH | Protocol-based DI removes root cause in Phase 2 |
| `event_publisher.py` god-class: 75 methods, 50 import sites | HIGH | Phase 2 Plan A decomposition |
| `lead_bot.py`: 2,815 lines with mixed concerns | HIGH | Phase 2 Plan B decomposition |
| `webhook.py`: route file doing service orchestration | HIGH | Phase 2 Plan C + dependencies.py |
| 11 lead scoring variants, callers pick randomly | MEDIUM | Phase 2 single scorer with strategy pattern |
| `compliance_platform/` shadow dependency | MEDIUM | Phase 2 inversion of control |
| Phase-specific route files (`_phase7`, `_v2`) | MEDIUM | Phase 3 route consolidation |
| No `import-linter` enforcement | MEDIUM | Phase 4 CI enforcement |
| `ghl_live_data_service.py` concrete bot import | LOW | Phase 2 protocol abstraction |
