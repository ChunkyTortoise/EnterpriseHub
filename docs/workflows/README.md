# Jorge Bot LangGraph Workflow Visualizations

This directory contains Mermaid diagram representations of the LangGraph workflows powering all three Jorge bots.

## Quick View

View these diagrams using:
- **Mermaid Live Editor**: https://mermaid.live (copy/paste .mmd file contents)
- **VS Code**: Install Mermaid extension for inline rendering
- **GitHub**: Native Mermaid rendering in markdown (embed in docs)

## Generated Diagrams

### Lead Bot Workflows
- **`lead_bot_standard_workflow.mmd`**: Classic 3-7-30 day follow-up sequence
- **`lead_bot_enhanced_workflow.mmd`**: Advanced workflow with predictive analytics, behavioral optimization, and Track3 market intelligence

### Buyer Bot Workflows
- **`buyer_bot_workflow.mmd`**: Financial qualification → property matching → objection handling pipeline

### Seller Bot Workflows
- **`seller_bot_standard_workflow.mmd`**: Intent analysis → CMA generation → objection handling → pricing guidance
- **`seller_bot_enhanced_workflow.mmd`**: Adaptive negotiation with conversation memory and dynamic strategy selection

## Workflow Highlights

### Lead Bot (Standard)
```
Entry → Analyze Intent → Determine Path → [Conditional Routing]
├─ Generate CMA (immediate)
├─ Day 3 SMS (3-day mark)
├─ Day 7 Call (7-day mark)
├─ Day 14 Email (14-day mark)
├─ Day 30 Nudge (30-day mark)
├─ Schedule Showing (hot leads)
├─ Post-Showing Survey
├─ Facilitate Offer
└─ Closing Nurture
```

### Lead Bot (Enhanced)
```
Entry → Analyze Intent → Behavioral Analysis → Predict Optimization
      → Track3 Intelligence → Determine Path → [Enhanced Routing]
├─ Generate CMA
├─ Optimized Day 3 (personalized timing)
├─ Predictive Day 7 (conversion-optimized)
├─ Adaptive Day 14 (behavior-driven)
└─ Intelligent Day 30 (stall-breaking)
```

### Buyer Bot
```
Entry → Analyze Intent → Classify Persona → Financial Readiness
      → Calculate Affordability → Qualify Needs → Match Properties
      → [Conditional]
          ├─ Handle Objections → Generate Response
          └─ Generate Response
      → Executive Brief → Schedule Next Action → End
```

### Seller Bot (Standard)
```
Entry → Analyze Intent → Detect Stall → [Strategy Router]
├─ Handle Objection (price concerns, timing)
├─ Generate CMA (property valuation)
├─ Pricing Guidance (competitive analysis)
├─ Market Analysis (area trends)
├─ Defend Valuation (low-ball offers)
└─ Prepare Listing (ready to list)
        ↓
Select Strategy → Generate Response → Executive Brief
→ Recalculate PCS → Execute Follow-Up → End
```

### Seller Bot (Enhanced - Adaptive)
```
Entry → Analyze Intent → Detect Stall → Adaptive Strategy
      → [Conditional]
          ├─ Generate Adaptive Response → Brief → PCS → Memory → Follow-Up
          └─ Update Memory → Follow-Up
```

## Key Workflow Patterns

### Conditional Routing
All bots use **conditional edges** to route based on state:
- Lead Bot: Routes by `current_step` and `engagement_status`
- Buyer Bot: Routes by `objection_detected` flag
- Seller Bot: Routes by `stall_type` and `negotiation_state`

### Terminal Nodes
Every workflow path ends at `__end__` (LangGraph END marker), ensuring clean state termination.

### State Management
- **Lead Bot**: `LeadFollowUpState` (FRS score, follow-up day, engagement level)
- **Buyer Bot**: `BuyerBotState` (financial readiness, property matches, objections)
- **Seller Bot**: `JorgeSellerState` (FRS/PCS scores, objections, stall signals)

## Regeneration

To regenerate these diagrams (e.g., after workflow changes):

```bash
# All bots
python -m ghl_real_estate_ai.utils.workflow_visualizer --all

# Specific bot
python -m ghl_real_estate_ai.utils.workflow_visualizer --bot lead
python -m ghl_real_estate_ai.utils.workflow_visualizer --bot buyer
python -m ghl_real_estate_ai.utils.workflow_visualizer --bot seller
```

## Workflow Philosophy

### Design Principles
1. **Single Responsibility**: Each node performs one logical operation
2. **State Immutability**: Nodes return new state; they don't mutate input
3. **Fail-Safe Defaults**: Routing always has fallback paths
4. **Observable**: Every node logs entry/exit for tracing
5. **Testable**: Node functions are pure and easily mockable

### Performance Targets
- **Node Execution**: < 200ms per node (excluding LLM calls)
- **LLM Calls**: < 2s (Claude with streaming)
- **Total Workflow**: < 5s end-to-end (P95)

### Error Handling
- Each node wraps operations in try/except
- Errors logged with context (contact_id, node_name, state snapshot)
- Failed nodes return state with `error` field set
- Workflows continue to terminal node even on errors (graceful degradation)

## Integration with Observability

### OpenTelemetry Traces
Each workflow node is instrumented with:
- **Span**: `workflow.node.{node_name}`
- **Attributes**: `contact_id`, `bot_type`, `node_index`, `state_snapshot`
- **Events**: `node_start`, `node_complete`, `node_error`

### Metrics Tracked
- Node execution duration (P50/P95/P99)
- Conditional routing outcomes (histogram by path)
- Terminal node distribution (qualified vs nurture vs error)
- State size evolution (bytes per node)

## Architecture Notes

### Why LangGraph?
- **Visual Clarity**: Workflows map 1:1 to business logic
- **State Persistence**: Built-in checkpointing for long-running flows
- **Conditional Logic**: First-class support for branching
- **Streaming**: Real-time state updates via async generators
- **Debugging**: Graph visualization + replay capabilities

### Migration Path
Older bots (pre-Jorge) used imperative if/else chains. LangGraph migration benefits:
- **Testability**: 3x reduction in test complexity (mock nodes, not entire flow)
- **Maintainability**: Visual graph representation for non-engineers
- **Extensibility**: Add nodes without refactoring existing logic
- **Observability**: Automatic trace/span generation per node

---

**Generated**: February 15, 2026  
**Tool**: `ghl_real_estate_ai/utils/workflow_visualizer.py`  
**LangGraph Version**: 0.2.x  
**Maintained By**: DevOps Infrastructure Agent  
