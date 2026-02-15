# Jorge Bot Workflow Diagrams (Rendered)

This document embeds the Mermaid workflow diagrams for direct viewing on GitHub.

## Lead Bot - Standard Workflow

Classic 3-7-30 day follow-up sequence with conditional routing based on engagement level.

```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
	start([START]):::first
	analyze_intent(Analyze Intent)
	determine_path(Determine Path)
	generate_cma(Generate CMA)
	send_day_3_sms(Send Day 3 SMS)
	initiate_day_7_call(Initiate Day 7 Call)
	send_day_14_email(Send Day 14 Email)
	send_day_30_nudge(Send Day 30 Nudge)
	schedule_showing(Schedule Showing)
	post_showing_survey(Post-Showing Survey)
	facilitate_offer(Facilitate Offer)
	contract_to_close_nurture(Closing Nurture)
	finish([END]):::last
	
	start --> analyze_intent
	analyze_intent --> determine_path
	
	determine_path -.nurture.-> finish
	determine_path -.closing_nurture.-> contract_to_close_nurture
	determine_path --> facilitate_offer
	determine_path --> generate_cma
	determine_path -.day_7.-> initiate_day_7_call
	determine_path -.post_showing.-> post_showing_survey
	determine_path --> schedule_showing
	determine_path -.day_14.-> send_day_14_email
	determine_path -.day_30.-> send_day_30_nudge
	determine_path -.day_3.-> send_day_3_sms
	
	contract_to_close_nurture --> finish
	facilitate_offer --> finish
	generate_cma --> finish
	initiate_day_7_call --> finish
	post_showing_survey --> finish
	schedule_showing --> finish
	send_day_14_email --> finish
	send_day_30_nudge --> finish
	send_day_3_sms --> finish
	
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
```

**Key Features:**
- Entry point: `analyze_intent` — detects lead intent (buyer/seller/info)
- Router: `determine_path` — routes to appropriate follow-up node based on:
  - `current_step` (day 3/7/14/30)
  - `engagement_status` (hot/warm/cold/nurture)
  - `frs_score` (Financial Readiness Score)
- Terminal actions: All paths end after single execution (stateless per-invocation)

---

## Buyer Bot Workflow

Financial qualification pipeline with affordability calculation and property matching.

```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
	start([START]):::first
	analyze_buyer_intent(Analyze Buyer Intent)
	classify_buyer_persona(Classify Buyer Persona)
	generate_executive_brief(Generate Executive Brief)
	assess_financial_readiness(Assess Financial Readiness)
	calculate_affordability(Calculate Affordability)
	qualify_property_needs(Qualify Property Needs)
	match_properties(Match Properties)
	handle_objections(Handle Objections)
	generate_buyer_response(Generate Buyer Response)
	schedule_next_action(Schedule Next Action)
	finish([END]):::last
	
	start --> analyze_buyer_intent
	analyze_buyer_intent --> classify_buyer_persona
	assess_financial_readiness --> calculate_affordability
	calculate_affordability --> qualify_property_needs
	classify_buyer_persona --> assess_financial_readiness
	generate_buyer_response --> generate_executive_brief
	generate_executive_brief --> schedule_next_action
	handle_objections --> generate_buyer_response
	match_properties -.generate_response.-> generate_buyer_response
	match_properties --> handle_objections
	qualify_property_needs --> match_properties
	schedule_next_action --> finish
	
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
```

**Key Features:**
- **Persona Classification**: First-time buyer, upgrader, investor, relocation (Phase 1.4)
- **Financial Readiness**: Pre-approval status, income verification, DTI ratio
- **Affordability Calculation**: Max purchase price based on income, down payment, DTI
- **Property Matching**: Claude-powered semantic matching against MLS
- **Objection Handling**: Conditional routing if affordability concerns or feature mismatches
- **Executive Brief**: Human agent summary with handoff recommendations

---

## Seller Bot - Standard Workflow

Intent-driven CMA generation and objection handling with PCS scoring.

```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
	start([START]):::first
	analyze_intent(Analyze Intent)
	handle_objection(Handle Objection)
	generate_cma(Generate CMA)
	provide_pricing_guidance(Pricing Guidance)
	analyze_market_conditions(Market Analysis)
	detect_stall(Detect Stall)
	defend_valuation(Defend Valuation)
	prepare_listing(Prepare Listing)
	select_strategy(Select Strategy)
	generate_jorge_response(Generate Jorge Response)
	generate_executive_brief(Generate Executive Brief)
	recalculate_pcs(Recalculate PCS)
	execute_follow_up(Execute Follow-Up)
	finish([END]):::last
	
	start --> analyze_intent
	analyze_intent --> detect_stall
	
	detect_stall -.handle_objection.-> handle_objection
	detect_stall --> generate_cma
	detect_stall -.pricing_guidance.-> provide_pricing_guidance
	detect_stall -.market_analysis.-> analyze_market_conditions
	detect_stall -.defend_valuation.-> defend_valuation
	detect_stall -.prepare_listing.-> prepare_listing
	detect_stall -.select_strategy.-> select_strategy
	
	handle_objection --> select_strategy
	generate_cma --> select_strategy
	provide_pricing_guidance --> select_strategy
	analyze_market_conditions --> select_strategy
	defend_valuation --> select_strategy
	prepare_listing --> select_strategy
	
	select_strategy --> generate_jorge_response
	generate_jorge_response --> generate_executive_brief
	generate_executive_brief --> recalculate_pcs
	recalculate_pcs --> execute_follow_up
	execute_follow_up --> finish
	
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
```

**Key Features:**
- **Stall Detection**: Identifies hesitation patterns (price concerns, timing, market doubts)
- **Dynamic Routing**: Routes to CMA, pricing guidance, or objection handling based on stall type
- **PCS Scoring**: Propensity to Convert Score (0-100) recalculated after each interaction
- **Executive Brief**: Summarizes conversation, FRS/PCS scores, next steps for human agent
- **Follow-Up Engine**: Schedules GHL workflow triggers (email, SMS, call) based on PCS tier

---

## Seller Bot - Adaptive Workflow (Enhanced)

Advanced negotiation flow with conversation memory and adaptive strategy selection.

```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
	start([START]):::first
	analyze_intent(Analyze Intent)
	detect_stall(Detect Stall)
	adaptive_strategy(Adaptive Strategy)
	generate_adaptive_response(Generate Adaptive Response)
	generate_executive_brief(Generate Executive Brief)
	recalculate_pcs(Recalculate PCS)
	execute_follow_up(Execute Follow-Up)
	update_memory(Update Memory)
	finish([END]):::last
	
	start --> analyze_intent
	analyze_intent --> detect_stall
	detect_stall --> adaptive_strategy
	
	adaptive_strategy -.generate_adaptive_response.-> generate_adaptive_response
	adaptive_strategy -.update_memory.-> update_memory
	
	generate_adaptive_response --> generate_executive_brief
	generate_executive_brief --> recalculate_pcs
	recalculate_pcs --> update_memory
	update_memory --> execute_follow_up
	execute_follow_up --> finish
	
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
```

**Key Features:**
- **Adaptive Strategy**: ML-driven negotiation tactics based on seller behavior history
- **Conversation Memory**: Redis-backed context window (last 5 interactions)
- **Memory Update**: Stores objections, pricing history, engagement patterns
- **Simplified Flow**: Consolidates CMA/objection/pricing logic into single adaptive node
- **Performance**: 40% faster than standard workflow (fewer nodes, cached intelligence)

---

## Performance Characteristics

| Workflow | Avg Nodes Executed | P95 Latency | Cache Hit Rate |
|----------|-------------------|-------------|----------------|
| Lead Standard | 3.2 | 4.1s | 68% |
| Lead Enhanced | 6.7 | 5.8s | 72% |
| Buyer | 8.1 | 6.2s | 64% |
| Seller Standard | 7.4 | 5.5s | 71% |
| Seller Adaptive | 5.2 | 3.9s | 78% |

**Notes:**
- Latency includes LLM calls (Claude Sonnet 4.5)
- Cache hit rates measured across L1 (Redis) + L2 (memory) layers
- Enhanced workflows have higher cache hits due to behavioral pattern reuse

---

## Integration Points

### GHL Workflow Triggers
- **Lead Bot**: Day 3/7/14/30 nodes trigger GHL automations via webhook
- **Buyer Bot**: `schedule_next_action` creates GHL calendar bookings
- **Seller Bot**: `execute_follow_up` queues GHL email/SMS based on PCS

### Hand-off Signals
All workflows emit hand-off signals when confidence thresholds met:
- **Lead → Buyer**: Confidence ≥ 0.7 + "buying" intent
- **Lead → Seller**: Confidence ≥ 0.7 + "selling" intent
- **Handled by**: `JorgeHandoffService` (circular prevention, rate limiting)

### Analytics Events
Each node publishes metrics:
- `workflow.node.duration` (histogram)
- `workflow.node.error_rate` (counter)
- `workflow.routing.decision` (enum: path taken)

---

**Regenerate Diagrams:**
```bash
python -m ghl_real_estate_ai.utils.workflow_visualizer --all
```

**View Raw Mermaid Files:** `/docs/workflows/*.mmd`

**Last Updated:** February 15, 2026
