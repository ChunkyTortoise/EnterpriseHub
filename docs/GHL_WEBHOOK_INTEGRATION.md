# GoHighLevel Webhook Integration Guide

**Version:** 4.0.0
**Last Updated:** January 10, 2026
**Status:** Production Ready
**Webhook Version**: GHL API v2.0
**Reliability**: 99.9% uptime SLA

---

## Table of Contents

1. [Overview](#overview)
2. [Webhook Setup](#webhook-setup)
3. [Supported Events](#supported-events)
4. [Request/Response Patterns](#requestresponse-patterns)
5. [Integration Examples](#integration-examples)
6. [Error Handling](#error-handling)
7. [Monitoring & Logging](#monitoring--logging)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)

---

## Overview

EnterpriseHub integrates with GoHighLevel (GHL) through secure webhooks to synchronize lead data, track interactions, and trigger AI-enhanced actions. The webhook system provides real-time, bi-directional communication between GHL and EnterpriseHub.

### Architecture

```
GHL Event
    ↓
[GHL Webhook Gateway]
    ↓
[EnterpriseHub Webhook Endpoint]
    ├─→ [Signature Verification]
    ├─→ [Rate Limiting]
    ├─→ [Input Validation]
    └─→ [Event Processing]
        ├─→ [Update Database]
        ├─→ [Trigger ML Models]
        ├─→ [Update GHL Contact]
        └─→ [Send Notifications]
    ↓
[Response to GHL]
```

### Key Benefits

- **Real-Time Sync**: Immediate lead and contact updates
- **AI Enhancement**: Automatic lead scoring on every interaction
- **Workflow Automation**: Trigger actions based on GHL events
- **Smart Communication**: Personalized messages based on lead behavior
- **Closed-Loop Feedback**: Track outcomes and improve ML models

---

## Webhook Setup

### Step 1: Get Webhook Credentials

In GHL Dashboard:
1. Settings → API & Integrations
2. Webhooks → Add Webhook
3. Copy credentials:
   - **Webhook Secret**: `ghl_webhook_secret_xxx`
   - **Location ID**: `location_xxx`
   - **API Key**: `ghl_api_key_xxx`

### Step 2: Configure EnterpriseHub

Store in `.env`:

```bash
GHL_WEBHOOK_SECRET=ghl_webhook_secret_xxx
GHL_LOCATION_ID=location_xxx
GHL_API_KEY=ghl_api_key_xxx
GHL_WEBHOOK_URL=https://api.enterprisehub.com/webhooks/ghl
GHL_API_BASE_URL=https://api.gohighlevel.com/v1
```

### Step 3: Register Webhook Events

In GHL Dashboard, select events to receive:

```
Contacts
  ✓ contact.created
  ✓ contact.updated
  ✓ contact.deleted (optional)

Opportunities
  ✓ opportunity.created
  ✓ opportunity.updated
  ✓ opportunity.won
  ✓ opportunity.lost

Calendar
  ✓ appointment.scheduled
  ✓ appointment.completed
  ✓ appointment.missed

Messages
  ✓ message.received
  ✓ message.sent

Campaigns
  ✓ campaign.opened
  ✓ campaign.clicked
```

### Step 4: Verify Webhook Endpoint

```bash
# Test webhook connectivity
curl -X POST https://api.enterprisehub.com/webhooks/ghl/verify \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# Expected response
{
  "status": "ready",
  "version": "4.0.0"
}
```

---

## Supported Events

### Contact Events

#### contact.created

**Trigger**: New contact added to GHL

```json
{
  "type": "contact.created",
  "timestamp": "2026-01-10T15:30:00Z",
  "data": {
    "contact_id": "contact_xxx",
    "first_name": "John",
    "last_name": "Smith",
    "email": "john@example.com",
    "phone": "+1-555-123-4567",
    "source": "website",
    "custom_fields": {
      "budget": "300000-500000",
      "timeline": "3 months",
      "property_type": "single_family"
    }
  }
}
```

**Processing**:
1. Create lead in EnterpriseHub
2. Run initial ML scoring
3. Extract initial preferences
4. Send welcome sequence

#### contact.updated

**Trigger**: Contact information changed

```json
{
  "type": "contact.updated",
  "timestamp": "2026-01-10T15:35:00Z",
  "data": {
    "contact_id": "contact_xxx",
    "updated_fields": {
      "phone": "+1-555-123-4568",
      "custom_fields": {
        "budget": "400000-600000"
      }
    }
  }
}
```

**Processing**:
1. Update lead profile
2. Re-run ML scoring with new data
3. Identify preference changes
4. Update property matches

### Opportunity Events

#### opportunity.created

**Trigger**: Opportunity added for contact

```json
{
  "type": "opportunity.created",
  "timestamp": "2026-01-10T15:40:00Z",
  "data": {
    "opportunity_id": "opp_xxx",
    "contact_id": "contact_xxx",
    "name": "123 Main Street - Buyer",
    "value": 425000,
    "pipeline": "Real Estate Sales",
    "status": "lead"
  }
}
```

**Processing**:
1. Link opportunity to lead
2. Extract property details
3. Update lead properties
4. Track conversion funnel

#### opportunity.won

**Trigger**: Opportunity marked as won (success outcome)

```json
{
  "type": "opportunity.won",
  "timestamp": "2026-01-10T16:00:00Z",
  "data": {
    "opportunity_id": "opp_xxx",
    "contact_id": "contact_xxx",
    "property_address": "123 Main Street",
    "final_price": 425000,
    "close_date": "2026-02-15"
  }
}
```

**Processing**:
1. Record successful outcome
2. Update lead status to "sold"
3. Log transaction details
4. Feedback to ML model for learning
5. Trigger celebration email

#### opportunity.lost

**Trigger**: Opportunity marked as lost

```json
{
  "type": "opportunity.lost",
  "timestamp": "2026-01-10T16:05:00Z",
  "data": {
    "opportunity_id": "opp_xxx",
    "contact_id": "contact_xxx",
    "reason": "Found different agent",
    "closed_date": "2026-01-10"
  }
}
```

**Processing**:
1. Record churn outcome
2. Analyze why lost (feedback)
3. Update churn models
4. Trigger re-engagement sequence

### Appointment Events

#### appointment.scheduled

**Trigger**: Tour or appointment scheduled

```json
{
  "type": "appointment.scheduled",
  "timestamp": "2026-01-10T15:45:00Z",
  "data": {
    "appointment_id": "apt_xxx",
    "contact_id": "contact_xxx",
    "property_address": "123 Main Street",
    "appointment_date": "2026-01-15T14:00:00Z",
    "appointment_type": "property_tour"
  }
}
```

**Processing**:
1. Record tour scheduling
2. Strong positive signal for lead scoring
3. Update lead status
4. Adjust churn probability (lower risk)
5. Send tour confirmation

#### appointment.completed

**Trigger**: Tour or appointment completed

```json
{
  "type": "appointment.completed",
  "timestamp": "2026-01-15T15:00:00Z",
  "data": {
    "appointment_id": "apt_xxx",
    "contact_id": "contact_xxx",
    "duration_minutes": 45,
    "feedback": "Very interested in property"
  }
}
```

**Processing**:
1. Record tour completion
2. Extract feedback sentiment
3. Update engagement metrics
4. Trigger follow-up sequence

### Message Events

#### message.received

**Trigger**: Message received from contact

```json
{
  "type": "message.received",
  "timestamp": "2026-01-10T15:50:00Z",
  "data": {
    "message_id": "msg_xxx",
    "contact_id": "contact_xxx",
    "channel": "sms",  // or "email", "facebook"
    "content": "Hi, I'm very interested in the property on Main Street",
    "response_time_ms": 120
  }
}
```

**Processing**:
1. Record message received
2. Analyze sentiment
3. Extract intent signals
4. Trigger automatic response
5. Update engagement metrics

#### campaign.opened

**Trigger**: Email campaign opened

```json
{
  "type": "campaign.opened",
  "timestamp": "2026-01-10T16:00:00Z",
  "data": {
    "campaign_id": "camp_xxx",
    "contact_id": "contact_xxx",
    "open_time": "2026-01-10T16:00:00Z",
    "device": "mobile"
  }
}
```

**Processing**:
1. Record email engagement
2. Update engagement score
3. Note interaction for ML learning
4. Update behavioral features

---

## Request/Response Patterns

### Webhook Request Format

```python
@app.post("/webhooks/ghl")
async def receive_ghl_webhook(request: Request):
    """
    Main webhook endpoint for GHL events.
    """
    # Step 1: Get request body and signature
    body = await request.body()
    signature = request.headers.get("X-GHL-Signature")
    timestamp = request.headers.get("X-GHL-Timestamp")

    # Step 2: Verify signature (prevent spoofing)
    if not verify_webhook_signature(body, signature, timestamp):
        logger.warning("Invalid webhook signature")
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid signature"}
        )

    # Step 3: Parse payload
    payload = json.loads(body)

    # Step 4: Validate payload schema
    try:
        event = GHLWebhookEvent.parse_obj(payload)
    except ValidationError as e:
        logger.error(f"Invalid webhook payload: {e}")
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid payload"}
        )

    # Step 5: Process event asynchronously
    asyncio.create_task(process_webhook_event(event))

    # Step 6: Return success immediately
    return {"status": "received"}
```

### Event Processing Pattern

```python
async def process_webhook_event(event: GHLWebhookEvent):
    """
    Process GHL webhook event.
    """
    try:
        logger.info(f"Processing event: {event.type}")

        # Route to appropriate handler
        handler = EVENT_HANDLERS.get(event.type)
        if not handler:
            logger.warning(f"No handler for event type: {event.type}")
            return

        # Execute handler
        result = await handler(event.data)

        # Log success
        await audit_log.record({
            "event_type": event.type,
            "status": "success",
            "timestamp": datetime.utcnow(),
            "contact_id": event.data.get("contact_id")
        })

        logger.info(f"Event processed successfully: {event.type}")

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        await handle_webhook_error(event, e)
```

### Response Format

All webhook responses follow standard format:

```json
{
  "status": "success|processing|error",
  "message": "Human readable message",
  "data": {
    "event_id": "evt_xxx",
    "processing_time_ms": 142
  }
}
```

---

## Integration Examples

### Example 1: Contact Created → AI Scoring

```python
async def handle_contact_created(data: dict):
    """
    Handle new contact creation in GHL.
    """
    contact_id = data["contact_id"]
    contact_data = data

    # Create lead in EnterpriseHub
    lead = await leads.create({
        "ghl_contact_id": contact_id,
        "name": f"{data['first_name']} {data['last_name']}",
        "email": data["email"],
        "phone": data["phone"],
        "source": data.get("source", "ghl"),
        "properties": data.get("custom_fields", {})
    })

    # Run AI scoring
    score_result = await ml_service.score_lead(lead.id)

    # Update GHL contact with score
    await ghl_client.update_contact(
        contact_id=contact_id,
        custom_fields={
            "ai_score": round(score_result.score, 2),
            "score_confidence": round(score_result.confidence, 2),
            "lead_quality": score_result.quality,
            "recommended_action": score_result.recommended_actions[0].action
        }
    )

    # Send welcome email
    await email_service.send_welcome(lead.email, lead.name)

    logger.info(f"Lead created and scored: {lead.id} (score: {score_result.score})")
```

### Example 2: Appointment Scheduled → Lead Probability Update

```python
async def handle_appointment_scheduled(data: dict):
    """
    Handle appointment scheduling.
    """
    contact_id = data["contact_id"]
    property_address = data["property_address"]

    # Get lead
    lead = await leads.find_by_ghl_id(contact_id)

    # Record interaction
    await interaction_service.record_interaction(
        lead_id=lead.id,
        interaction_type="tour_scheduled",
        details={
            "property_address": property_address,
            "tour_date": data["appointment_date"]
        }
    )

    # Re-score lead (should increase score)
    new_score = await ml_service.score_lead(lead.id)

    # Update churn prediction (should decrease risk)
    churn_risk = await ml_service.predict_churn(lead.id)

    # Update GHL with new insights
    await ghl_client.update_contact(
        contact_id=contact_id,
        custom_fields={
            "updated_ai_score": round(new_score.score, 2),
            "churn_risk": round(churn_risk.probability, 2),
            "next_action": "Prepare for tour"
        }
    )

    # Send tour confirmation and tips
    await email_service.send_tour_confirmation(
        lead=lead,
        property=property_address,
        tour_date=data["appointment_date"]
    )
```

### Example 3: Opportunity Won → Record Success

```python
async def handle_opportunity_won(data: dict):
    """
    Handle successful opportunity.
    """
    contact_id = data["contact_id"]

    # Get lead
    lead = await leads.find_by_ghl_id(contact_id)

    # Record successful outcome
    await outcome_service.record_outcome(
        lead_id=lead.id,
        outcome_type="property_purchased",
        details={
            "property_address": data["property_address"],
            "final_price": data["final_price"],
            "close_date": data["close_date"]
        }
    )

    # Update lead status
    await leads.update(lead.id, {"status": "sold"})

    # Feedback to ML model
    await ml_service.record_positive_feedback(lead.id)

    # Update GHL
    await ghl_client.update_contact(
        contact_id=contact_id,
        custom_fields={
            "status": "sold",
            "sale_price": data["final_price"],
            "close_date": data["close_date"]
        }
    )

    # Send congratulations
    await email_service.send_congratulations(lead.email, lead.name)

    logger.info(f"Lead {lead.id} converted to sale!")
```

---

## Error Handling

### Retry Strategy

```python
class WebhookRetryManager:
    """
    Manage webhook retry logic.
    """

    RETRY_POLICY = {
        "max_retries": 3,
        "backoff_factor": 2,
        "initial_delay_seconds": 60,
        "max_delay_seconds": 3600
    }

    async def process_with_retry(self, event: GHLWebhookEvent):
        """
        Process event with exponential backoff retry.
        """
        for attempt in range(self.RETRY_POLICY["max_retries"]):
            try:
                await self.process_event(event)
                return  # Success

            except TemporaryError as e:
                if attempt < self.RETRY_POLICY["max_retries"] - 1:
                    # Calculate backoff delay
                    delay = (
                        self.RETRY_POLICY["initial_delay_seconds"] *
                        (self.RETRY_POLICY["backoff_factor"] ** attempt)
                    )
                    delay = min(delay, self.RETRY_POLICY["max_delay_seconds"])

                    logger.warning(
                        f"Event processing failed (attempt {attempt + 1}), "
                        f"retrying in {delay}s: {e}"
                    )

                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Event processing failed after retries: {e}")
                    await self.handle_permanent_failure(event, e)

            except PermanentError as e:
                logger.error(f"Permanent error processing event: {e}")
                await self.handle_permanent_failure(event, e)
                return
```

### Dead Letter Queue

```python
async def handle_permanent_failure(event: GHLWebhookEvent, error: Exception):
    """
    Handle events that cannot be processed.
    """
    # Store in dead letter queue
    await db.dead_letter_queue.insert_one({
        "event": event.dict(),
        "error": str(error),
        "timestamp": datetime.utcnow(),
        "status": "needs_investigation"
    })

    # Alert ops team
    await notify_ops_team(
        f"Webhook processing failed: {event.type}",
        severity="high"
    )

    logger.error(f"Event moved to DLQ: {event}")
```

---

## Monitoring & Logging

### Webhook Metrics

```python
class WebhookMetrics:
    """
    Track webhook performance metrics.
    """

    async def record_event(self, event_type: str, processing_time_ms: float, status: str):
        """
        Record webhook event metrics.
        """
        metrics = {
            "event_type": event_type,
            "processing_time_ms": processing_time_ms,
            "status": status,
            "timestamp": datetime.utcnow()
        }

        # Store in metrics database
        await db.webhook_metrics.insert_one(metrics)

        # Track in monitoring system
        await datadog.metric(
            f"ghl.webhook.{event_type}.processing_time",
            processing_time_ms,
            tags=["status:" + status]
        )

    async def get_webhook_health(self) -> dict:
        """
        Get webhook service health.
        """
        # Count events in last hour
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_events = await db.webhook_metrics.count_documents({
            "timestamp": {"$gte": hour_ago}
        })

        # Calculate success rate
        success_events = await db.webhook_metrics.count_documents({
            "timestamp": {"$gte": hour_ago},
            "status": "success"
        })

        success_rate = (success_events / recent_events * 100) if recent_events > 0 else 100

        # Calculate average processing time
        avg_processing = await db.webhook_metrics.aggregate([
            {"$match": {"timestamp": {"$gte": hour_ago}}},
            {"$group": {"_id": None, "avg_time": {"$avg": "$processing_time_ms"}}}
        ]).to_list(1)

        return {
            "events_last_hour": recent_events,
            "success_rate_percent": success_rate,
            "avg_processing_time_ms": avg_processing[0]["avg_time"] if avg_processing else 0,
            "status": "healthy" if success_rate > 99 else "degraded"
        }
```

---

## Testing

### Test Webhook Payload

```bash
# Test contact.created event
curl -X POST https://api.enterprisehub.com/webhooks/ghl \
  -H "Content-Type: application/json" \
  -H "X-GHL-Signature: xxx" \
  -H "X-GHL-Timestamp: $(date +%s)" \
  -d '{
    "type": "contact.created",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "data": {
      "contact_id": "test_contact_123",
      "first_name": "Test",
      "last_name": "User",
      "email": "test@example.com",
      "phone": "+1-555-123-4567"
    }
  }'
```

### Unit Tests

```python
@pytest.mark.asyncio
async def test_contact_created_webhook():
    """
    Test contact.created webhook handling.
    """
    payload = {
        "type": "contact.created",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "contact_id": "test_123",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+1-555-123-4567"
        }
    }

    response = await client.post("/webhooks/ghl", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "received"

    # Verify lead was created
    lead = await leads.find_by_ghl_id("test_123")
    assert lead.email == "john@example.com"

    # Verify scoring was run
    assert lead.ml_score is not None
```

---

## Troubleshooting

### Issue: Webhook not being received

```bash
# Check webhook URL
curl https://api.enterprisehub.com/webhooks/ghl/verify

# Check firewall/network
telnet api.enterprisehub.com 443

# Check GHL webhook logs
# In GHL: Settings → API & Integrations → Webhooks → View Logs
```

### Issue: Signature verification failing

```bash
# Verify secret is correct
echo $GHL_WEBHOOK_SECRET

# Check timestamp freshness
# Timestamps older than 5 minutes are rejected

# Test signature verification locally
python scripts/test_webhook_signature.py
```

### Issue: Contact not updating in GHL

```bash
# Check API key permissions
python scripts/verify_ghl_permissions.py

# Check rate limiting
# GHL limit: 1000 requests/minute

# Verify contact ID is correct
python scripts/list_ghl_contacts.py
```

---

## Support & Resources

### Documentation
- GHL Webhook Docs: https://docs.gohighlevel.com/webhooks
- GHL API Reference: https://docs.gohighlevel.com/api

### Status & Monitoring
- GHL Status Page: https://status.gohighlevel.com
- EnterpriseHub Status: https://status.enterprisehub.com

---

**Last Updated**: January 10, 2026
**Maintained By**: Integration Engineering Team
**Next Review**: January 17, 2026
