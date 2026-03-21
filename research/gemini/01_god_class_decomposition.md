# God-Class Decomposition Analysis

Generated: 2026-03-19
Analyst: Claude Code (Sonnet 4.6)
Files analyzed: 10,609 total lines across 4 files

---

## event_publisher.py (3,144 lines)

### Current Responsibilities

The file mixes five distinct concerns into one class:

1. **Infrastructure / Transport Layer** (lines 55-87, 1308-1590)
   - Lifecycle management (`start`, `stop`)
   - Micro-batching engine with priority lanes (`_publish_event`, `_process_event_batch`, `_process_event_batch_optimized`, `_schedule_micro_batch_processing`)
   - Event aggregation logic (`_aggregate_similar_events_optimized`)
   - Latency tracking (`_track_event_latency`)
   - Performance metrics collection (`EventMetrics` dataclass, `_processing_times`, `_latency_measurements`)

2. **Domain Event Publishers — Core CRM** (lines 89-480)
   - Lead lifecycle events: `publish_lead_update`, `publish_conversation_update`, `publish_commission_update`
   - Dashboard events: `publish_dashboard_refresh`, `publish_performance_update`
   - User/session events: `publish_user_activity`, `publish_system_alert`
   - Property events: `publish_property_alert`, `publish_property_match_update`
   - System health: `publish_system_health_update`

3. **Domain Event Publishers — Jorge Bot Ecosystem** (lines 481-690)
   - Bot lifecycle: `publish_bot_status_update`
   - Qualification progress: `publish_jorge_qualification_progress`, `publish_intent_analysis_complete`
   - Lead bot sequence: `publish_lead_bot_sequence_update`
   - Bot handoffs: `publish_bot_handoff_request`

4. **Domain Event Publishers — Bot-Specific (Buyer/SMS/AI Concierge)** (lines 783-1270)
   - Buyer bot events: `publish_buyer_intent_analysis`, `publish_buyer_qualification_progress`, `publish_buyer_qualification_complete`, `publish_buyer_follow_up_scheduled`
   - SMS compliance events: `publish_sms_compliance_event`, `publish_sms_opt_out_processed`, `publish_sms_frequency_limit_hit`
   - AI Concierge events: `publish_proactive_insight`, `publish_strategy_recommendation`, `publish_coaching_opportunity`, `publish_ai_concierge_status_update`

5. **Utility / Calculation Helpers** (scattered)
   - `_get_stage_progression` — conversation stage metadata
   - `_calculate_trend` — metric trend direction
   - `_calculate_health_score` — component health scoring
   - `_calculate_sequence_progress` — sequence day progress
   - `_calculate_concierge_efficiency` — AI concierge performance
   - `_get_session_info` — session metadata stub
   - `create_decorator` — function decorator factory

### Proposed Decomposition

Split into 5 modules under `services/event_publisher/`:

**`services/event_publisher/engine.py`** — Transport and batching infrastructure only
- `EventMetrics` dataclass
- `EventPublisherEngine` class: `start`, `stop`, `_publish_event`, `_process_event_batch_optimized`, `_schedule_micro_batch_processing`, `_aggregate_similar_events_optimized`, `_track_event_latency`
- No domain knowledge; receives `RealTimeEvent` and dispatches it

**`services/event_publisher/crm_events.py`** — CRM and dashboard domain events
- Mixin class `CRMEventPublisher`: `publish_lead_update`, `publish_conversation_update`, `publish_commission_update`, `publish_dashboard_refresh`, `publish_performance_update`, `publish_user_activity`, `publish_property_alert`, `publish_property_match_update`, `publish_system_alert`, `publish_system_health_update`
- Stage/trend helpers: `_get_stage_progression`, `_calculate_trend`, `_calculate_health_score`

**`services/event_publisher/bot_events.py`** — Jorge bot ecosystem events
- Mixin class `BotEventPublisher`: `publish_bot_status_update`, `publish_jorge_qualification_progress`, `publish_lead_bot_sequence_update`, `publish_intent_analysis_complete`, `publish_bot_handoff_request`
- Helper: `_calculate_sequence_progress`

**`services/event_publisher/buyer_events.py`** — Buyer and SMS compliance events
- Mixin class `BuyerEventPublisher`: `publish_buyer_intent_analysis`, `publish_buyer_qualification_progress`, `publish_buyer_qualification_complete`, `publish_buyer_follow_up_scheduled`, `publish_sms_compliance_event`, `publish_sms_opt_out_processed`, `publish_sms_frequency_limit_hit`

**`services/event_publisher/concierge_events.py`** — AI Concierge events
- Mixin class `ConciergeEventPublisher`: `publish_proactive_insight`, `publish_strategy_recommendation`, `publish_coaching_opportunity`, `publish_ai_concierge_status_update`
- Helper: `_calculate_concierge_efficiency`, `_get_session_info`

**`services/event_publisher/__init__.py`** — Facade (backward compatible)
```python
class EventPublisher(
    EventPublisherEngine,
    CRMEventPublisher,
    BotEventPublisher,
    BuyerEventPublisher,
    ConciergeEventPublisher,
):
    pass
```

### Resulting File Structure

```
services/
  event_publisher/
    __init__.py          ~  60 lines  (facade + get_event_publisher singleton)
    engine.py            ~ 280 lines  (batching, latency, metrics)
    crm_events.py        ~ 500 lines  (lead/commission/dashboard/system)
    bot_events.py        ~ 350 lines  (Jorge/lead-bot/handoff events)
    buyer_events.py      ~ 300 lines  (buyer + SMS compliance events)
    concierge_events.py  ~ 250 lines  (AI concierge events)
```

Total after: ~1,740 lines (45% reduction through focus; existing lines preserved, not deleted)

### Migration Steps

1. Create `services/event_publisher/` directory.
2. Extract `EventPublisherEngine` to `engine.py`; keep `get_event_publisher()` singleton in `__init__.py`.
3. Extract each mixin to its own file; mixins depend only on `engine.py`'s `_publish_event`.
4. Replace the current `services/event_publisher.py` file with the package `__init__.py` facade.
5. All existing callers import from `ghl_real_estate_ai.services.event_publisher` — no import changes needed.
6. Run `pytest tests/ -k event_publisher` to verify no regressions.

---

## lead_bot.py (2,815 lines)

### Current Responsibilities

1. **Configuration** (lines 107-120)
   - `LeadBotConfig` dataclass with feature flags and performance settings

2. **Workflow Orchestration — Standard** (lines 250-331)
   - `_build_standard_graph`: LangGraph StateGraph construction, node registration, edge wiring for the 3-7-30 day sequence (14 nodes, 10+ edges)

3. **Workflow Orchestration — Enhanced** (lines 333-437)
   - `_build_enhanced_graph`: Same structure but conditionally adds ML analytics nodes based on config flags; dynamic node chaining

4. **Optional ML Analytics Nodes** (lines 439-642)
   - `gather_lead_intelligence`: Bot intelligence middleware integration
   - `analyze_behavioral_patterns`: BehavioralAnalyticsEngine + PersonalityAdapter + TemperaturePredictionEngine
   - `predict_sequence_optimization`: SequenceOptimization prediction
   - `apply_track3_market_intelligence`: ML analytics journey/conversion/touchpoint prediction

5. **Enhanced Follow-Up Sequence Steps** (lines 644-971)
   - `send_optimized_day_3`, `initiate_predictive_day_7`, `send_adaptive_day_14`, `send_intelligent_day_30`
   - Each contains intelligence-driven timing adjustments, channel escalation logic, and Jorge handoff recommendations

6. **Standard Follow-Up Sequence Steps** (inherited from `BaseBotWorkflow`, ~1,200 lines not shown in first 200)
   - `send_day_3_sms`, `initiate_day_7_call`, `send_day_14_email`, `send_day_30_nudge`
   - `schedule_showing`, `post_showing_survey`, `facilitate_offer`, `contract_to_close_nurture`

7. **Core Qualification Nodes** (lines 1104-1400+)
   - `check_handoff_signals`: Regex-based buyer/seller intent extraction with early short-circuit
   - `analyze_intent`: LeadIntentDecoder, voice call data check, Lyrio sync, sequence state init
   - `determine_path`: Routing logic (CMA, hot-lead, sequence day, ghost state)

8. **Message Construction Helpers** (scattered)
   - `_construct_intelligent_day3_message`, `_construct_adaptive_day14_message`, `_construct_intelligent_day30_message`
   - `_extract_churn_risk_from_intelligence`, `_extract_preferred_engagement_timing`
   - `_route_next_step`, `_route_enhanced_step`

9. **ML Analytics Helpers** (lines 999-1103)
   - `_apply_market_timing_intelligence`: Sequence timing adjustments from urgency score
   - `_detect_critical_scenarios`: High-value cooling / qualification-ready detection
   - `_publish_jorge_handoff_recommendation`, `_publish_jorge_handoff_request`, `_publish_intelligent_jorge_handoff_request`

10. **Voice Call Integration** (lines 214-248)
    - `check_voice_call_data`: Redis lookup for recent voice call qualification data

11. **Infrastructure** (lines 68-93)
    - `_safe_background_task`: async error logging wrapper (module-level function)
    - `LeadBotConfig` initialization and optional component wiring

### Proposed Decomposition

Split into 5 modules under `agents/lead_bot/`:

**`agents/lead_bot/config.py`**
- `LeadBotConfig` dataclass
- `_safe_background_task` utility function

**`agents/lead_bot/graph_builder.py`** — LangGraph construction only
- `StandardGraphBuilder._build_standard_graph(workflow_instance)`
- `EnhancedGraphBuilder._build_enhanced_graph(workflow_instance)`
- No business logic; only node/edge registration

**`agents/lead_bot/sequence_steps.py`** — Standard follow-up implementations
- `StandardSequenceSteps` mixin: `send_day_3_sms`, `initiate_day_7_call`, `send_day_14_email`, `send_day_30_nudge`
- `LifecycleSteps` mixin: `schedule_showing`, `post_showing_survey`, `facilitate_offer`, `contract_to_close_nurture`
- `_route_next_step`

**`agents/lead_bot/enhanced_sequence_steps.py`** — ML-enhanced follow-up implementations
- `EnhancedSequenceSteps` mixin: `send_optimized_day_3`, `initiate_predictive_day_7`, `send_adaptive_day_14`, `send_intelligent_day_30`
- Message construction helpers: `_construct_intelligent_day3_message`, `_construct_adaptive_day14_message`, `_construct_intelligent_day30_message`
- Intelligence extraction helpers: `_extract_churn_risk_from_intelligence`, `_extract_preferred_engagement_timing`
- `_route_enhanced_step`

**`agents/lead_bot/analytics_nodes.py`** — Optional ML analytics pipeline nodes
- `AnalyticsNodes` mixin: `gather_lead_intelligence`, `analyze_behavioral_patterns`, `predict_sequence_optimization`, `apply_track3_market_intelligence`
- ML helpers: `_apply_market_timing_intelligence`, `_detect_critical_scenarios`
- Event helpers: `_publish_jorge_handoff_recommendation`, `_publish_jorge_handoff_request`, `_publish_intelligent_jorge_handoff_request`

**`agents/lead_bot/qualification_nodes.py`** — Core qualification workflow nodes
- `QualificationNodes` mixin: `check_handoff_signals`, `analyze_intent`, `determine_path`
- `qualify_intent`, `generate_cma` (routed destination nodes)
- Voice call integration: `check_voice_call_data`
- Sequence routing: `_map_int_to_sequence_day`

**`agents/lead_bot/__init__.py`** — Composed `LeadBotWorkflow` class
```python
class LeadBotWorkflow(
    QualificationNodes,
    AnalyticsNodes,
    EnhancedSequenceSteps,
    StandardSequenceSteps,
    BaseBotWorkflow,
):
    def __init__(self, ...): ...
    def _build_unified_graph(self): ...
```

### Resulting File Structure

```
agents/
  lead_bot/
    __init__.py                  ~  80 lines  (composed class + factory)
    config.py                    ~  60 lines  (LeadBotConfig + _safe_background_task)
    graph_builder.py             ~ 200 lines  (standard + enhanced graph construction)
    qualification_nodes.py       ~ 350 lines  (analyze_intent, check_handoff_signals, determine_path)
    sequence_steps.py            ~ 450 lines  (standard 3/7/14/30 + lifecycle steps)
    enhanced_sequence_steps.py   ~ 450 lines  (ML-enhanced steps + message builders)
    analytics_nodes.py           ~ 400 lines  (ML analytics pipeline nodes + helpers)
```

Total after: ~1,990 lines (29% reduction; individual files each under 450 lines)

### Migration Steps

1. Create `agents/lead_bot/` package directory.
2. Extract `LeadBotConfig` and `_safe_background_task` to `config.py` first (no dependencies).
3. Extract `QualificationNodes` mixin — depends on imports already present at top of `lead_bot.py`.
4. Extract `StandardSequenceSteps` mixin — depends on `BaseBotWorkflow` patterns.
5. Extract `AnalyticsNodes` mixin — has optional imports (`TRACK3_ML_AVAILABLE` guard); keep the try/except at top of `analytics_nodes.py`.
6. Extract `EnhancedSequenceSteps` mixin — depends on helpers from `analytics_nodes.py`.
7. Extract graph builders to `graph_builder.py` — depends on all node mixins.
8. Wire composition in `__init__.py`.
9. Ensure `from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow` still resolves.
10. Run `pytest tests/ -k lead_bot` before and after.

---

## webhook.py (2,715 lines)

### Current Responsibilities

1. **FastAPI Setup / Dependency Injection** (lines 106-200)
   - Module-level singleton instantiation for 12 services
   - `@lru_cache` singleton wrappers (`_get_conversation_manager`, `_get_ghl_client_default`, etc.)

2. **Utility / Parsing Functions** (lines 74-430)
   - `_signals_to_handoff_profile`: Builds minimal `LeadIntentProfile` for handoff routing
   - `_normalize_tags`, `_tag_present`, `_compute_mode_flags`, `_select_primary_mode`: Tag normalization and bot routing logic
   - `_detect_buy_sell_intent`: Regex-based buyer/seller keyword scoring
   - `_detect_negative_sentiment`, `_detect_rejected_offer`: CC workflow signal detection
   - `_format_slot_options`, `_select_slot_from_message`: Appointment slot parsing
   - `_CC_NEGATIVE_KEYWORDS`, `_CC_REJECTED_OFFER_KEYWORDS`, `_LEAD_PASSTHROUGH_TAGS`, `_SELLER_PASSTHROUGH_TAGS`: Constant sets

3. **Workflow Action Builder** (lines 432-494)
   - `_build_cc_workflow_actions`: Redis-deduped CC DTS campaign enrollment logic
   - `_get_tenant_ghl_client`: Tenant-aware GHL client factory

4. **Tag Webhook Handler** (lines 497-592)
   - `handle_ghl_tag_webhook`: Initial outreach on tag-add, bot routing, idempotency, CC AI-tag workflow enrollment

5. **Main Webhook Handler — Guards and Pre-routing** (lines 595-870)
   - `handle_ghl_webhook`: Loopback protection, idempotency guard, input length guard, tag fetching, activation/deactivation logic, opt-out detection

6. **Main Webhook Handler — Appointment Flow** (lines 912-1110)
   - Pending appointment slot selection: parse, book via `CalendarScheduler`, handle booking failure, re-offer, manual escalation fallback

7. **Main Webhook Handler — Seller Mode** (lines 1112-1354)
   - Jorge seller engine invocation, CC DTS enrollment, response pipeline, compliance guard, cross-bot handoff, HITL gate, billing, final response assembly

8. **Main Webhook Handler — Buyer Mode** (lines 1356-~1700)
   - Buyer bot invocation, temperature classification, custom field sync, calendar slot offering, analytics tracking, response pipeline, compliance, handoff check

9. **Main Webhook Handler — Lead Mode** (lines ~1700-~2300)
   - Lead bot invocation, tag publishing, billing tracking, lead scoring, MLS search, analytics

10. **Billing / Pricing Background Tasks** (lines ~2300-2715)
    - `_handle_billing_usage`, `_calculate_lead_pricing`: Subscription tracking, dynamic pricing, usage records
    - Potentially `_update_lead_attribution`, `_track_lead_source`

### Proposed Decomposition

Split into modules under `api/routes/webhook/`:

**`api/routes/webhook/dependencies.py`** — Service singletons and DI
- All module-level service instantiations and `@lru_cache` getter functions
- `SMS_MAX_CHARS`, `LLM_FALLBACK_MSG` constants

**`api/routes/webhook/routing.py`** — Tag normalization and mode selection
- All tag-related constants: `_LEAD_PASSTHROUGH_TAGS`, `_SELLER_PASSTHROUGH_TAGS`, `OPT_OUT_PHRASES`
- Functions: `_normalize_tags`, `_tag_present`, `_compute_mode_flags`, `_select_primary_mode`, `_detect_buy_sell_intent`
- `_signals_to_handoff_profile`

**`api/routes/webhook/guards.py`** — Request validation and early exits
- Input length guard, loopback protection, idempotency guard logic (extracted from `handle_ghl_webhook`)
- `_detect_negative_sentiment`, `_detect_rejected_offer`, `_CC_NEGATIVE_KEYWORDS`, `_CC_REJECTED_OFFER_KEYWORDS`
- Opt-out detection and response assembly

**`api/routes/webhook/appointment_handler.py`** — Appointment slot flow
- `_format_slot_options`, `_select_slot_from_message`
- `handle_pending_appointment(contact_id, user_message, context, ...)` — extracted appointment flow function

**`api/routes/webhook/seller_handler.py`** — Seller mode processing
- `handle_seller_mode(contact_id, user_message, ...)` — extracted seller flow
- `_build_cc_workflow_actions`
- `_get_tenant_ghl_client`

**`api/routes/webhook/buyer_handler.py`** — Buyer mode processing
- `handle_buyer_mode(contact_id, user_message, ...)` — extracted buyer flow
- Buyer temperature classification logic
- Buyer custom field sync

**`api/routes/webhook/lead_handler.py`** — Lead mode processing
- `handle_lead_mode(contact_id, user_message, ...)` — extracted lead flow

**`api/routes/webhook/billing.py`** — Billing and pricing background tasks
- `_handle_billing_usage`, `_calculate_lead_pricing`
- `_update_lead_attribution`, `_track_lead_source`

**`api/routes/webhook/__init__.py`** — FastAPI router, tag webhook, and main webhook
- `router = APIRouter(...)`
- `handle_ghl_tag_webhook`: thin orchestrator calling imports from above modules
- `handle_ghl_webhook`: thin orchestrator (~100 lines) that calls guards, routing, then delegates to `seller_handler`, `buyer_handler`, `lead_handler`, or `appointment_handler`
- Imports the `router` for mounting in `app.py`

### Resulting File Structure

```
api/routes/webhook/
  __init__.py             ~ 180 lines  (router + thin orchestrator handlers)
  dependencies.py         ~ 120 lines  (singletons + lru_cache getters)
  routing.py              ~ 200 lines  (tag normalization, mode flags, intent detection)
  guards.py               ~ 150 lines  (loopback, idempotency, opt-out, length guard)
  appointment_handler.py  ~ 200 lines  (slot selection, booking, escalation)
  seller_handler.py       ~ 350 lines  (seller engine, compliance, HITL, CC DTS)
  buyer_handler.py        ~ 400 lines  (buyer bot, temp classification, field sync, calendar)
  lead_handler.py         ~ 300 lines  (lead bot, scoring, MLS, tagging)
  billing.py              ~ 200 lines  (billing, pricing, attribution)
```

Total after: ~2,100 lines (23% reduction; each handler file independently testable)

### Migration Steps

1. Create `api/routes/webhook/` package directory.
2. Extract `dependencies.py` first — zero business logic, easy to verify.
3. Extract `routing.py` — pure functions, add unit tests for `_compute_mode_flags`.
4. Extract `guards.py` — pure functions, add unit tests for each guard condition.
5. Extract `appointment_handler.py` as a standalone async function.
6. Extract `seller_handler.py`, `buyer_handler.py`, `lead_handler.py` in parallel — each is independent.
7. Extract `billing.py` last (background task functions, no route dependencies).
8. Replace `api/routes/webhook.py` with `api/routes/webhook/__init__.py` that composes the above.
9. Update `app.py` import: `from ghl_real_estate_ai.api.routes.webhook import router` — no change needed if package `__init__.py` exports `router`.
10. Run full test suite: `pytest tests/ -k webhook`.

---

## claude_orchestrator.py (1,935 lines)

### Current Responsibilities

1. **Data Models / Type Definitions** (lines 35-89)
   - `ClaudeTaskType` enum (11 task types)
   - `ClaudeRequest` dataclass
   - `ClaudeResponse` dataclass with `__post_init__`

2. **System Prompt Management** (lines 189-271)
   - `_load_system_prompts`: 7 hardcoded system prompt strings (chat_assistant, lead_analyzer, report_synthesizer, script_generator, omnipotent_assistant, persona_optimizer, researcher_assistant)
   - `_get_system_prompt`: Task type to prompt key mapping

3. **Response Cache** (lines 172-292)
   - `_make_response_cache_key`: SHA-256 hash of request content
   - `_get_cached_response`: TTL-aware dict lookup with hit/miss tracking
   - `_response_cache` dict, `_response_cache_ttl`, counters

4. **Request Orchestration / Tool Loop** (lines 294-463)
   - `process_request`: Main entry point; handles cache check, context enhancement, tool loop (5 turns max), specialist handoff prompts, GHL sync trigger, response caching
   - `process_request_stream`: Streaming variant bypassing tool loop

5. **MCP Tool Management** (lines 490-538)
   - `_get_tools_for_request`: Gathers tool definitions from MCP servers by category
   - `_execute_tool_call`: Dispatches tool calls to appropriate MCP server
   - `_sync_action_to_ghl`: Background GHL custom field sync after ACTION category tools

6. **High-Level Domain Methods** (lines 624-853)
   - `chat_query`: Interactive chat with tool use enabled
   - `analyze_lead`: Comprehensive lead analysis with scoring
   - `synthesize_report`: Narrative report from metrics
   - `generate_script`: Personalized script with A/B variants
   - `orchestrate_intervention`: Churn intervention planning
   - `analyze_conversation_sentiment`: Delegates to `SentimentDriftEngine`
   - `detect_lead_persona`: Delegates to `PsychographicSegmentationEngine`
   - `provide_market_reality_check`: Delegates to `MarketContextInjector`
   - `perform_research`: Perplexity + Claude synthesis

7. **Context Building** (lines 877-951)
   - `_enhance_context`: Memory service fetch with in-process cache
   - `_build_prompt`: JSON serialization of context into prompt
   - `_call_claude`: Low-level LLM call (largely superseded by `llm.agenerate` in `process_request`)
   - `_gather_lead_context`: (referenced but not shown in first 1,935 lines — likely collects scoring data)

8. **Response Parsing** (lines 953-1935)
   - `_extract_json_block`: 3-strategy JSON extraction from Claude response
   - `_extract_balanced_json`: Balanced-bracket JSON parser
   - `_extract_list_items`: Markdown section item extractor
   - `_parse_response`: Dispatcher to per-task parsers
   - `_parse_confidence_score`: 4-strategy confidence extraction
   - `_parse_recommended_actions`: JSON + markdown action extraction
   - `_structure_action`: Action text to priority/timing dict
   - `_parse_script_variants`: A/B variant extraction
   - `_parse_risk_factors`: Risk factor extraction
   - `_parse_opportunities`: Opportunity extraction
   - `_structure_risk`, `_structure_opportunity`: Structuring helpers
   - `_get_complexity_for_task`, `_get_demo_fallback_response`, `_update_metrics`

### Proposed Decomposition

Split into 5 modules under `services/orchestrator/`:

**`services/orchestrator/types.py`** — Data models only
- `ClaudeTaskType` enum
- `ClaudeRequest` dataclass
- `ClaudeResponse` dataclass
- No imports from within the package

**`services/orchestrator/prompts.py`** — System prompt registry
- `SYSTEM_PROMPTS` dict: all 7 hardcoded prompt strings
- `TASK_PROMPT_MAP` dict: `ClaudeTaskType` -> prompt key
- `get_system_prompt(task_type)` function
- Pure data; no class needed

**`services/orchestrator/response_parser.py`** — Response parsing utilities
- `ResponseParser` class (or module-level functions):
  - `_extract_json_block`, `_extract_balanced_json`, `_extract_list_items`
  - `parse_response(content, task_type) -> ClaudeResponse`
  - `_parse_confidence_score`, `_parse_recommended_actions`, `_structure_action`
  - `_parse_script_variants`, `_parse_risk_factors`, `_parse_opportunities`
  - `_structure_risk`, `_structure_opportunity`
- Zero I/O; fully synchronous; 100% unit-testable without mocking

**`services/orchestrator/tool_executor.py`** — MCP tool management
- `ToolExecutor` class:
  - `__init__(mcp_servers, skill_registry)`
  - `get_tools_for_request(categories)` — gathers tool definitions
  - `execute_tool_call(tool_call)` — dispatches to MCP server
  - `sync_action_to_ghl(tool_name, arguments, result, contact_id)` — GHL field sync

**`services/orchestrator/cache.py`** — Response cache
- `ResponseCache` class:
  - `__init__(ttl_seconds=300)`
  - `make_key(request) -> str`
  - `get(key) -> Optional[ClaudeResponse]`
  - `set(key, response)`
  - `stats() -> dict`
- Pure in-memory; injectable for testing

**`services/claude_orchestrator.py`** (retained, slimmed)
- `ClaudeOrchestrator` class imports from all above modules
- Retains: `__init__`, `process_request`, `process_request_stream`, `_enhance_context`, `_build_prompt`, `_gather_lead_context`, `_call_claude`, domain methods (`chat_query`, `analyze_lead`, `synthesize_report`, etc.), `_get_complexity_for_task`, `_get_demo_fallback_response`, `_update_metrics`
- Delegates: caching to `ResponseCache`, parsing to `ResponseParser`, tool execution to `ToolExecutor`, prompts to `get_system_prompt`

### Resulting File Structure

```
services/
  orchestrator/
    __init__.py          ~  10 lines  (re-exports for backward compatibility)
    types.py             ~ 100 lines  (ClaudeTaskType, ClaudeRequest, ClaudeResponse)
    prompts.py           ~ 100 lines  (SYSTEM_PROMPTS dict + get_system_prompt)
    response_parser.py   ~ 450 lines  (all parsing helpers)
    tool_executor.py     ~ 150 lines  (MCP tool dispatch + GHL sync)
    cache.py             ~  80 lines  (ResponseCache)
  claude_orchestrator.py ~ 600 lines  (orchestration logic + domain methods)
```

Total after: ~1,490 lines (23% reduction; `response_parser.py` is now independently testable)

### Migration Steps

1. Extract `types.py` first — `ClaudeTaskType`, `ClaudeRequest`, `ClaudeResponse`. Update imports in `claude_orchestrator.py` and all callers.
2. Extract `prompts.py` — move `_load_system_prompts` content to module-level dicts. Replace `self.system_prompts[key]` calls with `get_system_prompt(task_type)`.
3. Extract `cache.py` — create `ResponseCache`; inject into `ClaudeOrchestrator.__init__` as `self._cache = ResponseCache(ttl=300)`.
4. Extract `response_parser.py` — move all `_parse_*` and `_extract_*` methods; inject as `self._parser = ResponseParser()` or use as free functions.
5. Extract `tool_executor.py` — move `_get_tools_for_request`, `_execute_tool_call`, `_sync_action_to_ghl`; inject as `self._tools = ToolExecutor(mcp_servers, skill_registry)`.
6. Slim `claude_orchestrator.py` by delegating to the above.
7. Update `services/orchestrator/__init__.py` to re-export `ClaudeOrchestrator` for backward compatibility.
8. Run `pytest tests/ -k orchestrator`.

---

## Cross-Cutting Migration Priorities

### Risk Ranking (lowest to highest)

| Priority | File | Risk | Reason |
|----------|------|------|--------|
| 1 (first) | `claude_orchestrator.py` | Low | `response_parser.py` extraction is pure functions; no runtime behavior change |
| 2 | `event_publisher.py` | Low | Mixin composition preserves all public APIs; batching engine isolated |
| 3 | `webhook.py` | Medium | Active production path; extract handlers one at a time, test each in isolation |
| 4 (last) | `lead_bot.py` | Medium | LangGraph graph construction is stateful; mixin MRO requires careful ordering |

### Shared Patterns Across All Four Files

1. **Module-level singletons**: All four files instantiate services at import time. After decomposition, use `functools.lru_cache` on factory functions or explicit DI containers rather than module globals.

2. **Circular import guards**: `lead_bot.py` and `claude_orchestrator.py` both use deferred local imports inside `__init__` to break circular dependencies. After extraction, document which modules are "leaf" (no intra-package dependencies) vs "orchestrator" (imports from leaves).

3. **Optional feature gating**: `lead_bot.py` uses `try/except ImportError` for ML analytics and bot intelligence. After extraction, move the guards to the top of `analytics_nodes.py` and `config.py` only — no guards should leak into the composition root.

4. **Test isolation**: After decomposition, each extracted module should have its own test file in `tests/unit/`. The current integration tests can remain; add unit tests targeting the new boundaries. Target: `response_parser.py`, `routing.py`, `guards.py`, and `engine.py` should all reach 90%+ unit test coverage with no network calls.
