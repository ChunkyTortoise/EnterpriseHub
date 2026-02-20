"""
OpenTelemetry Workflow Tracing Examples

This module demonstrates how to instrument Jorge bot workflows
with distributed tracing.
"""

from typing import Dict

from ghl_real_estate_ai.observability.workflow_tracing import (
    add_workflow_event,
    async_workflow_span,
    create_handoff_span,
    get_trace_id,
    propagate_trace_context,
    trace_workflow_node,
)

# ==============================================================================
# Example 1: Basic Workflow Node Instrumentation
# ==============================================================================

@trace_workflow_node("lead_bot", "analyze_intent")
async def analyze_intent(state: Dict) -> Dict:
    """Workflow node with automatic tracing.
    
    The decorator automatically:
    - Creates a span named "lead_bot.analyze_intent"
    - Extracts contact_id from state
    - Adds workflow metadata (current_step, temperature)
    - Records success/failure and duration
    """
    # Your workflow logic here
    contact_id = state.get("lead_id")
    conversation = state.get("conversation_history", [])
    
    # Perform intent analysis
    intent_score = 0.85  # Placeholder
    
    # Add custom event to the span
    add_workflow_event("intent_analyzed", score=intent_score)
    
    state["intent_score"] = intent_score
    return state


# ==============================================================================
# Example 2: Manual Span Creation for Complex Logic
# ==============================================================================

async def qualify_seller_with_detailed_tracing(state: Dict) -> Dict:
    """Demonstrate manual span creation for fine-grained tracing."""
    contact_id = state.get("contact_id")
    
    # Create a parent span for the entire qualification process
    async with async_workflow_span(
        "seller_bot",
        "qualify_seller",
        contact_id=contact_id
    ) as parent_span:
        
        # Add custom attributes
        parent_span.set_attribute("seller.property_address", state.get("property_address"))
        
        # Sub-span for FRS calculation
        async with async_workflow_span(
            "seller_bot",
            "calculate_frs",
            contact_id=contact_id
        ) as frs_span:
            frs_score = 85.5  # Placeholder
            frs_span.set_attribute("seller.frs_score", frs_score)
            add_workflow_event("frs_calculated", score=frs_score)
        
        # Sub-span for PCS calculation
        async with async_workflow_span(
            "seller_bot",
            "calculate_pcs",
            contact_id=contact_id
        ) as pcs_span:
            pcs_score = 72.3  # Placeholder
            pcs_span.set_attribute("seller.pcs_score", pcs_score)
            add_workflow_event("pcs_calculated", score=pcs_score)
        
        # Add final qualification attributes
        parent_span.set_attribute("seller.qualification_score", (frs_score + pcs_score) / 2)
        parent_span.set_attribute("seller.temperature", "hot" if frs_score > 80 else "warm")
        
        state["frs_score"] = frs_score
        state["pcs_score"] = pcs_score
        
    return state


# ==============================================================================
# Example 3: Cross-Bot Handoff with Trace Correlation
# ==============================================================================

async def execute_handoff_with_tracing(
    contact_id: str,
    source_bot: str,
    target_bot: str,
    confidence: float,
    reason: str,
) -> Dict:
    """Execute a cross-bot handoff with distributed tracing.
    
    This ensures the trace context propagates across bot boundaries,
    allowing you to track the full lead journey.
    """
    
    # Create handoff span
    with create_handoff_span(
        source_bot=source_bot,
        target_bot=target_bot,
        contact_id=contact_id,
        confidence=confidence,
        reason=reason,
    ):
        # Log the trace ID for correlation
        trace_id = get_trace_id()
        print(f"Handoff trace_id={trace_id}")
        
        # Add handoff event
        add_workflow_event("handoff_initiated", confidence=confidence)
        
        # Prepare handoff metadata with trace context
        handoff_metadata = {
            "contact_id": contact_id,
            "source_bot": source_bot,
            "target_bot": target_bot,
            "confidence": confidence,
        }
        
        # Inject trace context for propagation
        handoff_metadata = propagate_trace_context(handoff_metadata)
        
        # Execute handoff (placeholder)
        # await handoff_service.execute_handoff(...)
        
        add_workflow_event("handoff_completed", success=True)
        
        return {
            "handoff_executed": True,
            "trace_id": trace_id,
            "metadata": handoff_metadata,
        }


# ==============================================================================
# Example 4: Instrumentation in Service Layer
# ==============================================================================

class IntentDecoderWithTracing:
    """Example service class with tracing."""
    
    async def analyze_lead(self, contact_id: str, conversation_history: list) -> Dict:
        """Analyze lead intent with tracing."""
        
        async with async_workflow_span(
            "intent_decoder",
            "analyze_lead",
            contact_id=contact_id
        ) as span:
            # Add conversation metadata
            span.set_attribute("decoder.conversation_length", len(conversation_history))
            
            # Perform analysis (placeholder)
            buyer_intent = 0.75
            seller_intent = 0.15
            
            # Add events for significant findings
            if buyer_intent > 0.7:
                add_workflow_event("buyer_intent_detected", confidence=buyer_intent)
            if seller_intent > 0.7:
                add_workflow_event("seller_intent_detected", confidence=seller_intent)
            
            # Set final attributes
            span.set_attribute("decoder.buyer_intent", buyer_intent)
            span.set_attribute("decoder.seller_intent", seller_intent)
            
            return {
                "buyer_intent_confidence": buyer_intent,
                "seller_intent_confidence": seller_intent,
            }


# ==============================================================================
# Example 5: Error Handling with Tracing
# ==============================================================================

@trace_workflow_node("buyer_bot", "schedule_showing")
async def schedule_showing_with_error_handling(state: Dict) -> Dict:
    """Workflow node with error handling and tracing.
    
    Exceptions are automatically recorded in the span and re-raised.
    """
    contact_id = state.get("contact_id")
    
    try:
        # Attempt to schedule showing
        showing_scheduled = False  # Placeholder
        
        if not showing_scheduled:
            # Add event for business-level failure
            add_workflow_event("showing_scheduling_failed", reason="no_availability")
            state["showing_status"] = "unavailable"
        else:
            add_workflow_event("showing_scheduled", success=True)
            state["showing_status"] = "scheduled"
        
        return state
    
    except Exception as e:
        # Exception is automatically recorded by the decorator
        # and span is marked as error
        add_workflow_event("critical_error", error_type=type(e).__name__)
        raise


# ==============================================================================
# Example 6: Conditional Instrumentation
# ==============================================================================

from ghl_real_estate_ai.observability.workflow_tracing import is_tracing_enabled


async def performance_sensitive_operation(state: Dict) -> Dict:
    """Conditionally add detailed tracing only when enabled."""
    
    # Check if tracing is enabled before adding expensive metadata
    if is_tracing_enabled():
        # Add detailed attributes for debugging
        async with async_workflow_span("lead_bot", "detailed_analysis") as span:
            span.set_attribute("analysis.complexity", "high")
            span.set_attribute("analysis.algorithm", "advanced_ml")
            
            # Perform analysis
            result = {"analyzed": True}
            
            # Add result metadata
            for key, value in result.items():
                span.set_attribute(f"result.{key}", value)
    else:
        # Skip tracing overhead
        result = {"analyzed": True}
    
    state["analysis_result"] = result
    return state
