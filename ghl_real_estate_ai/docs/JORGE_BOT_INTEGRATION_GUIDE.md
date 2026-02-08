# Jorge Bot Integration Guide

**Version:** 8.2  
**Date:** February 7, 2026  
**Scope:** Integration of Jorge Bot Services

---

## Table of Contents

1. [Service Overview](#service-overview)
2. [API Endpoints](#api-endpoints)
3. [Usage Examples](#usage-examples)
4. [Best Practices](#best-practices)
5. [Troubleshooting](#troubleshooting)

---

## Service Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Jorge Bot Services                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Lead Bot │  │Buyer Bot │  │Seller Bot│  │ Handoff  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │             │             │             │         │
│       └─────────────┼─────────────┼─────────────┘         │
│                     │             │                       │
│       ┌─────────────▼─────────────▼─────────────┐         │
│       │     JorgeHandoffService                 │         │
│       │  - Circular prevention                  │         │
│       │  - Rate limiting (3/hr, 10/day)        │         │
│       │  - Pattern learning                    │         │
│       └───────────────────┬───────────────────┘         │
│                           │                                 │
│       ┌───────────────────▼───────────────────┐          │
│       │  Supporting Services                   │          │
│       │  ┌─────────────┐ ┌─────────────┐     │          │
│       │  │ABTestingServ│ │PerformanceTr│     │          │
│       │  └─────────────┘ └─────────────┘     │          │
│       │  ┌─────────────┐ ┌─────────────┐     │          │
│       │  │AlertingServ│ │BotMetrics   │     │          │
│       │  └─────────────┘ └─────────────┘     │          │
│       └─────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### Service Dependencies

| Service | Depends On | Purpose |
|---------|------------|---------|
| JorgeHandoffService | Redis | Rate limiting, handoff locks |
| ABTestingService | PostgreSQL | Experiment persistence |
| PerformanceTracker | Redis | Rolling window metrics |
| AlertingService | SMTP/Slack/Webhook | Alert notifications |
| BotMetricsCollector | All bots | Metrics aggregation |

---

## API Endpoints

### Bot Public APIs

#### Lead Bot

```python
# File: ghl_real_estate_ai/agents/lead_bot.py
from LeadBotWorkflow import LeadBotWorkflow

bot = LeadBotWorkflow()

# Process lead conversation
result = await bot.process_lead_conversation(
    contact_id="ghl_contact_123",
    message="I'm looking to buy a home in Rancho Cucamonga",
    context={
        "location_id": "loc_456",
        "ghl_contact_data": {...}  # Optional GHL data
    }
)

# Returns: Dict[str, Any]
# {
#     "response": "Hi! I'd be happy to help you...",
#     "temperature": "hot",  # hot, warm, cold
#     "handoff_signals": {
#         "buyer_intent_score": 0.85,
#         "seller_intent_score": 0.15,
#         "should_handoff": True,
#         "recommended_bot": "buyer"
#     },
#     "lead_score": 82,
#     "conversation_stage": "Q2"
# }
```

#### Buyer Bot

```python
# File: ghl_real_estate_ai/agents/jorge_buyer_bot.py
from JorgeBuyerBot import JorgeBuyerBot

bot = JorgeBuyerBot()

# Process buyer conversation
result = await bot.process_buyer_conversation(
    contact_id="ghl_contact_123",
    message="What's my buying power with a $150K income?",
    context={
        "location_id": "loc_456",
        "ghl_contact_data": {...}
    }
)

# Returns: Dict[str, Any]
# {
#     "response": "Based on your income...",
#     "financial_readiness": {
#         "buying_power": 450000,
#         "affordability_tier": "mid",
#         "pre_approval_status": "pending"
#     },
#     "handoff_signals": {...}
# }
```

#### Seller Bot

```python
# File: ghl_real_estate_ai/agents/jorge_seller_bot.py
from JorgeSellerBot import JorgeSellerBot

bot = JorgeSellerBot()

# Process seller message
result = await bot.process_seller_message(
    contact_id="ghl_contact_123",
    message="How much is my home worth?",
    context={
        "location_id": "loc_456",
        "property_data": {...}
    }
)

# Returns: Dict[str, Any]
# {
#     "response": "Based on comparable sales...",
#     "frs_score": 78,  # Full Readiness Score
#     "pcs_score": 85,  # Preparation Checklist Score
#     "handoff_signals": {...}
# }
```

### Handoff Service API

```python
# File: ghl_real_estate_ai/services/jorge/jorge_handoff_service.py
from JorgeHandoffService import JorgeHandoffService

handoff_service = JorgeHandoffService()

# Evaluate handoff
decision = await handoff_service.evaluate_handoff(
    current_bot="lead",
    contact_id="ghl_contact_123",
    conversation_history=[...],
    intent_signals={
        "buyer_intent_score": 0.85,
        "seller_intent_score": 0.15
    }
)
# Returns: Dict with handoff decision

# Execute handoff
actions = await handoff_service.execute_handoff(
    decision,
    contact_id="ghl_contact_123"
)
# Returns: List of handoff actions
```

### A/B Testing Service API

```python
# File: ghl_real_estate_ai/services/jorge/ab_testing_service.py
from ABTestingService import ABTestingService

ab_service = ABTestingService()

# Create experiment
experiment_id = await ab_service.create_experiment(
    name="response_tone_test",
    variants=["formal", "casual", "empathetic"],
    weights={"formal": 0.4, "casual": 0.3, "empathetic": 0.3}
)

# Get variant for contact
variant = await ab_service.get_variant(
    experiment_id=experiment_id,
    contact_id="ghl_contact_123"
)
# Returns: "formal" | "casual" | "empathetic"

# Record outcome
await ab_service.record_outcome(
    experiment_id=experiment_id,
    contact_id="ghl_contact_123",
    variant=variant,
    outcome="converted"  # or "no_response", "bounced"
)

# Get results
results = ab_service.get_experiment_results(experiment_id)
# Returns: Dict with statistical analysis
```

### Performance Tracker API

```python
# File: ghl_real_estate_ai/services/jorge/performance_tracker.py
from PerformanceTracker import PerformanceTracker

tracker = PerformanceTracker()

# Track operation
await tracker.track_operation(
    bot_name="lead_bot",
    operation="process",
    duration_ms=1500,
    success=True,
    cache_hit=True
)

# Or use async context manager
async with tracker.track_async_operation("lead_bot", "handoff") as op:
    # Your code here
    pass

# Get stats
stats = await tracker.get_all_stats()
# Returns: Dict with P50, P95, P99, etc.

# Check SLA compliance
compliance = await tracker.check_sla_compliance()
# Returns: Dict with SLA status
```

### Alerting Service API

```python
# File: ghl_real_estate_ai/services/jorge/alerting_service.py
from AlertingService import AlertingService

alerting = AlertingService()

# Get active alerts
alerts = await alerting.get_active_alerts()

# Get alert history
history = await alerting.get_alert_history(limit=100)

# Send test alert
await alerting.send_alert({
    "rule_name": "test_alert",
    "severity": "info",
    "message": "Test alert",
    "metrics": {...}
})

# Custom alert check
triggered = await alerting.check_alerts(current_metrics)
```

### Bot Metrics Collector API

```python
# File: ghl_real_estate_ai/services/jorge/bot_metrics_collector.py
from BotMetricsCollector import BotMetricsCollector

collector = BotMetricsCollector()

# Collect all metrics
metrics = await collector.collect_metrics()

# Get formatted metrics
formatted = collector.get_metrics()

# Reset metrics
collector.reset_metrics()
```

---

## Usage Examples

### Complete Lead Qualification Flow

```python
from LeadBotWorkflow import LeadBotWorkflow
from JorgeHandoffService import JorgeHandoffService

async def qualify_lead(contact_id: str, message: str, location_id: str):
    """Complete lead qualification with handoff support."""
    
    # Initialize services
    lead_bot = LeadBotWorkflow()
    handoff_service = JorgeHandoffService()
    
    # Process lead
    result = await lead_bot.process_lead_conversation(
        contact_id=contact_id,
        message=message,
        context={"location_id": location_id}
    )
    
    # Check for handoff
    handoff = result.get("handoff_signals", {})
    if handoff.get("should_handoff"):
        decision = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id=contact_id,
            conversation_history=[...],
            intent_signals={
                "buyer_intent_score": handoff.get("buyer_intent_score", 0),
                "seller_intent_score": handoff.get("seller_intent_score", 0)
            }
        )
        
        if decision.get("should_handoff"):
            actions = await handoff_service.execute_handoff(
                decision,
                contact_id=contact_id
            )
            result["handoff_actions"] = actions
    
    return result
```

### A/B Testing Integration

```python
from JorgeBuyerBot import JorgeBuyerBot
from ABTestingService import ABTestingService

class ABTestableBuyerBot(JorgeBuyerBot):
    """Buyer Bot with A/B testing integration."""
    
    def __init__(self):
        super().__init__()
        self.ab_service = ABTestingService()
        self.experiment_id = None
    
    async def generate_response(self, contact_id: str, context: dict):
        """Generate response with A/B testing."""
        
        # Get variant for contact
        if self.experiment_id:
            variant = await self.ab_service.get_variant(
                self.experiment_id,
                contact_id
            )
            
            # Adjust response based on variant
            if variant == "formal":
                return self._generate_formal_response(context)
            elif variant == "casual":
                return self._generate_casual_response(context)
            else:
                return self._generate_empathetic_response(context)
        
        return await super().generate_response(contact_id, context)
```

### Performance Monitoring Integration

```python
from JorgeSellerBot import JorgeSellerBot
from PerformanceTracker import PerformanceTracker

async def monitored_seller_process(contact_id: str, message: str):
    """Seller bot processing with performance tracking."""
    
    tracker = PerformanceTracker()
    bot = JorgeSellerBot()
    
    async with tracker.track_async_operation("seller_bot", "process") as op:
        result = await bot.process_seller_message(
            contact_id=contact_id,
            message=message
        )
        
        # Track additional metrics
        op.set_metric("lead_score", result.get("frs_score", 0))
        op.set_metric("handoff_triggered", result.get("handoff_signals", {}).get("should_handoff", False))
    
    # Check SLA
    compliance = await tracker.check_sla_compliance()
    if not compliance["compliant"]:
        logger.warning(f"SLA violation: {compliance}")
    
    return result
```

### Alerting Integration

```python
from AlertingService import AlertingService
from PerformanceTracker import PerformanceTracker
import asyncio

async def monitoring_loop():
    """Background monitoring with alerting."""
    
    alerting = AlertingService()
    tracker = PerformanceTracker()
    
    while True:
        # Collect metrics
        stats = await tracker.get_all_stats()
        
        # Check alerts
        triggered = await alerting.check_alerts(stats)
        
        # Send alerts
        for alert in triggered:
            await alerting.send_alert(alert)
        
        # Wait before next check
        await asyncio.sleep(60)
```

---

## Best Practices

### 1. Use Context Managers for Tracking

```python
# Good: Using context manager
async with tracker.track_async_operation("buyer_bot", "process") as op:
    result = await bot.process_buyer_conversation(...)
    op.set_metric("lead_score", result.get("score", 0))

# Bad: Manual tracking
start = time.now()
result = await bot.process_buyer_conversation(...)
duration = time.now() - start
await tracker.track_operation("buyer_bot", "process", duration, True)
```

### 2. Handle Handoff Failures Gracefully

```python
try:
    actions = await handoff_service.execute_handoff(decision, contact_id)
    if not actions[0].get("handoff_executed"):
        logger.warning(f"Handoff blocked: {actions[0].get('reason')}")
except Exception as e:
    logger.error(f"Handoff failed: {e}")
    # Fallback to current bot
```

### 3. Use Deterministic Variant Assignment

```python
# Always use contact_id for assignment
# Never use random assignment
variant = await ab_service.get_variant(experiment_id, contact_id)
```

### 4. Record Outcomes Immediately

```python
# Record outcome as soon as result is known
if conversation_ended:
    await ab_service.record_outcome(
        experiment_id,
        contact_id,
        variant,
        outcome="converted"  # or "no_response"
    )
```

### 5. Configure Appropriate Cooldowns

```python
# Critical alerts: 5 minute cooldown
# Warning alerts: 10 minute cooldown
# Info alerts: 30 minute cooldown
```

---

## Troubleshooting

### Handoff Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| Handoffs always blocked | Rate limit exceeded | Wait for cooldown |
| Circular handoff detected | Same bot handoff within 30min | Allow 30min to pass |
| Handoff lock timeout | Concurrent handoff attempts | Use contact-level locking |

### A/B Testing Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| Variant not consistent | Wrong contact ID | Verify contact ID |
| No significance detected | Insufficient sample | Collect more data |
| Experiment not found | Experiment ID wrong | Check experiment ID |

### Performance Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| High P95 latency | Cache miss | Check Redis |
| SLA violations | Slow downstream | Check GHL API |
| Metrics not updating | Tracker disabled | Check `PERFORMANCE_TRACKING_ENABLED` |

### Alert Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| No alerts received | Channel disabled | Check config |
| Duplicate alerts | Cooldown not set | Configure cooldown |
| Alerts too noisy | Threshold too low | Adjust thresholds |

---

## API Reference Summary

| Service | Class | Key Methods |
|---------|-------|-------------|
| Lead Bot | `LeadBotWorkflow` | `process_lead_conversation()` |
| Buyer Bot | `JorgeBuyerBot` | `process_buyer_conversation()` |
| Seller Bot | `JorgeSellerBot` | `process_seller_message()` |
| Handoff | `JorgeHandoffService` | `evaluate_handoff()`, `execute_handoff()` |
| A/B Testing | `ABTestingService` | `create_experiment()`, `get_variant()`, `record_outcome()` |
| Performance | `PerformanceTracker` | `track_operation()`, `get_all_stats()`, `check_sla_compliance()` |
| Alerting | `AlertingService` | `check_alerts()`, `send_alert()`, `get_active_alerts()` |
| Metrics | `BotMetricsCollector` | `collect_metrics()`, `get_metrics()`, `reset_metrics()` |

---

**Document Version:** 8.2.0  
**Last Updated:** February 7, 2026  
**Related Documentation:**
- [Deployment Checklist](JORGE_BOT_DEPLOYMENT_CHECKLIST.md)
- [Alert Channels Guide](ALERT_CHANNELS_DEPLOYMENT_GUIDE.md)
- [A/B Testing Guide](AB_TESTING.md)
