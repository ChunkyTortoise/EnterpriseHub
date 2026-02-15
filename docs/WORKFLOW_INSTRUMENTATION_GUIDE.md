# Workflow Node Instrumentation Guide

## Quick Reference

**Add tracing to a workflow node in 2 steps:**

1. Import the decorator:
```python
from ghl_real_estate_ai.observability.workflow_tracing import trace_workflow_node
```

2. Decorate your node function:
```python
@trace_workflow_node("lead_bot", "send_day_3_sms")
async def send_day_3_sms(state: Dict) -> Dict:
    # Your existing logic
    return state
```

That's it! The decorator automatically captures all relevant metadata.

## Full Example: Lead Bot Instrumentation

### Before (no tracing)

```python
from typing import Dict

class WorkflowNodes:
    async def analyze_intent(self, state: Dict) -> Dict:
        """Analyze lead intent."""
        contact_id = state["lead_id"]
        # Analysis logic
        return state
    
    async def send_day_3_sms(self, state: Dict) -> Dict:
        """Send day 3 follow-up SMS."""
        contact_id = state["lead_id"]
        # SMS sending logic
        return state
```

### After (with tracing)

```python
from typing import Dict
from ghl_real_estate_ai.observability.workflow_tracing import trace_workflow_node

class WorkflowNodes:
    @trace_workflow_node("lead_bot", "analyze_intent")
    async def analyze_intent(self, state: Dict) -> Dict:
        """Analyze lead intent."""
        contact_id = state["lead_id"]
        # Analysis logic (unchanged)
        return state
    
    @trace_workflow_node("lead_bot", "send_day_3_sms")
    async def send_day_3_sms(self, state: Dict) -> Dict:
        """Send day 3 follow-up SMS."""
        contact_id = state["lead_id"]
        # SMS sending logic (unchanged)
        return state
```

**What changed**: Added 2 import lines + 2 decorators. Zero logic changes.

## Bot-Specific Naming Conventions

| Bot Type | Decorator Argument | Example Node Names |
|----------|-------------------|-------------------|
| Lead Bot | `"lead_bot"` | `analyze_intent`, `send_day_3_sms`, `generate_cma` |
| Buyer Bot | `"buyer_bot"` | `analyze_buyer_intent`, `schedule_showing`, `generate_buyer_response` |
| Seller Bot | `"seller_bot"` | `qualify_seller`, `calculate_frs`, `schedule_cma_appointment` |

## What Gets Automatically Captured

The `@trace_workflow_node` decorator automatically extracts from `state`:

| Attribute | Source | Example |
|-----------|--------|---------|
| `workflow.contact_id` | `state["lead_id"]` or `state["contact_id"]` | `"abc123"` |
| `workflow.current_step` | `state["current_step"]` | `"day_3"` |
| `workflow.temperature` | `state["temperature"]` | `"hot"` |
| `workflow.bot_type` | Decorator argument | `"lead_bot"` |
| `workflow.node_name` | Decorator argument | `"analyze_intent"` |
| `workflow.success` | Exception handling | `true` |
| `workflow.duration_ms` | Automatic timing | `245.67` |

## Adding Custom Attributes

Use `add_workflow_event()` inside your node:

```python
from ghl_real_estate_ai.observability.workflow_tracing import (
    trace_workflow_node,
    add_workflow_event,
)

@trace_workflow_node("seller_bot", "qualify_seller")
async def qualify_seller(self, state: Dict) -> Dict:
    contact_id = state["contact_id"]
    
    # Calculate FRS score
    frs_score = 85.5  # Your logic here
    
    # Add custom event to trace
    add_workflow_event("frs_calculated", score=frs_score)
    
    # Calculate PCS score
    pcs_score = 72.3  # Your logic here
    add_workflow_event("pcs_calculated", score=pcs_score)
    
    state["frs_score"] = frs_score
    state["pcs_score"] = pcs_score
    return state
```

**In Jaeger**, these events appear as annotations on the timeline.

## Advanced: Manual Span Creation

For fine-grained control, use `async_workflow_span()`:

```python
from ghl_real_estate_ai.observability.workflow_tracing import async_workflow_span

async def complex_qualification(self, state: Dict) -> Dict:
    contact_id = state["contact_id"]
    
    # Parent span for entire qualification
    async with async_workflow_span(
        "seller_bot",
        "qualify_seller",
        contact_id=contact_id
    ) as parent_span:
        
        # Sub-span for FRS calculation
        async with async_workflow_span(
            "seller_bot",
            "calculate_frs",
            contact_id=contact_id
        ) as frs_span:
            frs_score = 85.5
            frs_span.set_attribute("seller.frs_score", frs_score)
        
        # Sub-span for PCS calculation
        async with async_workflow_span(
            "seller_bot",
            "calculate_pcs",
            contact_id=contact_id
        ) as pcs_span:
            pcs_score = 72.3
            pcs_span.set_attribute("seller.pcs_score", pcs_score)
        
        # Add final qualification score to parent
        parent_span.set_attribute("seller.total_score", (frs_score + pcs_score) / 2)
    
    return state
```

**Result in Jaeger**: Nested spans showing sub-operations.

## Instrumenting Services

For non-workflow services (e.g., `IntentDecoder`), use `async_workflow_span()`:

```python
from ghl_real_estate_ai.observability.workflow_tracing import (
    async_workflow_span,
    add_workflow_event,
)

class LeadIntentDecoder:
    async def analyze_lead(self, contact_id: str, history: list) -> Dict:
        async with async_workflow_span(
            "intent_decoder",
            "analyze_lead",
            contact_id=contact_id
        ) as span:
            # Add metadata
            span.set_attribute("decoder.conversation_length", len(history))
            
            # Perform analysis
            buyer_intent = 0.75
            seller_intent = 0.15
            
            # Add events for findings
            if buyer_intent > 0.7:
                add_workflow_event("buyer_intent_detected", confidence=buyer_intent)
            
            # Set final attributes
            span.set_attribute("decoder.buyer_intent", buyer_intent)
            span.set_attribute("decoder.seller_intent", seller_intent)
            
            return {
                "buyer_intent_confidence": buyer_intent,
                "seller_intent_confidence": seller_intent,
            }
```

## Rollout Strategy

### Phase 1: High-Value Nodes (Week 1)

Instrument these nodes first for immediate value:

**Lead Bot**:
- `analyze_intent`
- `determine_path`
- `send_day_3_sms`
- `initiate_day_7_call`

**Seller Bot**:
- `qualify_seller`
- `calculate_frs`
- `schedule_cma_appointment`

**Buyer Bot**:
- `analyze_buyer_intent`
- `schedule_showing`

**Intent Decoder**:
- `analyze_lead()`
- `analyze_buyer()`
- `analyze_seller()`

### Phase 2: Full Coverage (Week 2)

Instrument remaining nodes:
- All day-X sequence nodes
- Lifecycle nodes (showing, offer, closing)
- Optimization nodes (predictive, adaptive)

### Phase 3: Fine-Tuning (Week 3)

- Add custom attributes for business metrics
- Add events for key milestones
- Optimize span names for clarity

## Testing Your Instrumentation

### 1. Enable Tracing Locally

```bash
# Start Jaeger
./scripts/start_tracing.sh

# Add to .env
OTEL_ENABLED=true
OTEL_ENDPOINT=http://localhost:4317
```

### 2. Trigger Workflow

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/webhooks/ghl \
  -H "Content-Type: application/json" \
  -d @test_payload.json
```

### 3. View Trace in Jaeger

1. Open http://localhost:16686
2. Select service: **enterprisehub**
3. Select operation: **POST /api/v1/webhooks/ghl**
4. Click **Find Traces**
5. Click on a trace to see waterfall view

### 4. Verify Span Attributes

In the span detail view, check:
- `workflow.bot_type` is correct
- `workflow.contact_id` is populated
- `workflow.duration_ms` seems reasonable
- No error status (unless expected)

## Troubleshooting

### Issue: Spans not appearing

**Check**:
1. `OTEL_ENABLED=true` in `.env`
2. Jaeger is running: `docker ps | grep jaeger`
3. Check app logs for: `"OpenTelemetry SDK detected — workflow tracing enabled"`

### Issue: Missing contact_id attribute

**Cause**: State dict doesn't have `lead_id` or `contact_id` key.

**Fix**: Ensure your state dict includes one of these keys:
```python
state = {
    "lead_id": "abc123",  # or "contact_id": "abc123"
    # ... other state
}
```

### Issue: Duplicate spans

**Cause**: Both `@trace_workflow_node` decorator AND manual `async_workflow_span()` used.

**Fix**: Use one or the other, not both:
```python
# Good (decorator only)
@trace_workflow_node("lead_bot", "analyze_intent")
async def analyze_intent(state):
    return state

# Good (manual only)
async def analyze_intent(state):
    async with async_workflow_span("lead_bot", "analyze_intent"):
        return state

# Bad (both - creates duplicate spans)
@trace_workflow_node("lead_bot", "analyze_intent")
async def analyze_intent(state):
    async with async_workflow_span("lead_bot", "analyze_intent"):  # DUPLICATE!
        return state
```

## Performance Considerations

**Overhead**: <5ms per traced operation

**Best Practices**:
1. Use decorators for simple nodes (minimal overhead)
2. Use manual spans only when you need custom attributes
3. Avoid tracing inside tight loops
4. Use conditional tracing for expensive operations:

```python
from ghl_real_estate_ai.observability.workflow_tracing import is_tracing_enabled

async def performance_critical_node(state):
    if is_tracing_enabled():
        # Add detailed metadata only when tracing is on
        async with async_workflow_span("lead_bot", "critical_node") as span:
            span.set_attribute("detail.expensive_calc", expensive_value())
    
    # Main logic runs regardless
    return perform_operation(state)
```

## Next Steps

1. Pick 5 high-value nodes to instrument
2. Add `@trace_workflow_node` decorators
3. Test locally with Jaeger
4. Verify traces look correct
5. Deploy to staging
6. Monitor P95 latency per node
7. Optimize slow nodes

## Questions?

See [DISTRIBUTED_TRACING_GUIDE.md](./DISTRIBUTED_TRACING_GUIDE.md) for full documentation.

---

**Last Updated**: 2026-02-15  
**Version**: 1.0.0
