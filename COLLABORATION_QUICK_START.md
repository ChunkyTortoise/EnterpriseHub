# Real-Time Collaboration - Quick Start Guide

**Quick reference for implementing real-time agent coordination in EnterpriseHub**

---

## Installation

The collaboration engine is already integrated. No additional dependencies required.

## Basic Usage

### 1. Create a Collaboration Room

```python
from ghl_real_estate_ai.models.collaboration_models import CreateRoomRequest, RoomType

# Create room for agent team coordination
request = CreateRoomRequest(
    tenant_id="tenant_123",
    room_type=RoomType.AGENT_TEAM,
    name="Sales Team Coordination",
    created_by="agent_lead_456",
    initial_members=["agent_1", "agent_2", "agent_3"],
    max_members=50
)

# Via API
POST /api/v1/collaboration/rooms
{
  "tenant_id": "tenant_123",
  "room_type": "agent_team",
  "name": "Sales Team Coordination",
  ...
}
```

### 2. Send Messages

```python
from ghl_real_estate_ai.models.collaboration_models import SendMessageRequest, MessageType

# Send a message
request = SendMessageRequest(
    room_id="room_abc123",
    sender_id="agent_1",
    sender_name="John Agent",
    message_type=MessageType.TEXT,
    content="New high-priority lead just came in!",
    priority="high"
)

# Via API
POST /api/v1/collaboration/messages
{
  "room_id": "room_abc123",
  "sender_id": "agent_1",
  "sender_name": "John Agent",
  "message_type": "text",
  "content": "New high-priority lead just came in!",
  "priority": "high"
}
```

### 3. WebSocket Connection

```javascript
// JavaScript/React
const ws = new WebSocket(
  `ws://localhost:8000/api/v1/collaboration/ws/${roomId}?token=${jwtToken}&user_id=${userId}&display_name=${displayName}`
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.event_type) {
    case 'collaboration_message':
      displayMessage(data.message);
      break;
    case 'presence_update':
      updateUserStatus(data.data);
      break;
    case 'typing_indicator':
      showTypingIndicator(data.data);
      break;
  }
};

// Send a message
ws.send(JSON.stringify({
  event_type: "send_message",
  message_type: "text",
  content: "Hello team!",
  priority: "normal"
}));
```

## Common Use Cases

### Lead Handoff

```python
# Agent 1 hands off lead to Agent 2
request = SendMessageRequest(
    room_id="lead_collab_room",
    sender_id="agent_1",
    sender_name="Sarah Agent",
    message_type=MessageType.LEAD_HANDOFF,
    content="Handing off lead John Doe to Agent 2 for closing",
    priority=MessagePriority.HIGH,
    metadata={
        "lead_id": "lead_789",
        "new_owner": "agent_2",
        "lead_score": 95,
        "qualification_complete": True
    }
)
```

### Real-Time Coaching

```python
# Send coaching tip to agent
request = SendMessageRequest(
    room_id="training_room",
    sender_id="coach_123",
    sender_name="Coach Mike",
    message_type=MessageType.COACHING_TIP,
    content="Great job building rapport! Try asking about their timeline next.",
    priority=MessagePriority.NORMAL,
    metadata={
        "agent_id": "agent_1",
        "conversation_id": "conv_456"
    }
)
```

### Property Tour Coordination

```python
# Coordinate virtual property tour
request = SendMessageRequest(
    room_id="tour_room",
    sender_id="agent_1",
    sender_name="John Agent",
    message_type=MessageType.PROPERTY_SHARE,
    content="Showing master bedroom now. Client loves the walk-in closet!",
    priority=MessagePriority.NORMAL,
    metadata={
        "property_id": "prop_123",
        "client_id": "client_456",
        "tour_stage": "master_bedroom"
    }
)
```

## Performance Monitoring

```python
# Get collaboration metrics
GET /api/v1/collaboration/metrics

# Response
{
  "collaboration_engine": {
    "total_connections": 250,
    "active_rooms": 45,
    "average_message_latency_ms": 32.5,
    "p95_message_latency_ms": 45.2,
    "messages_per_second": 125.3
  },
  "performance_status": {
    "latency_target_met": true,  // <50ms
    "overall_healthy": true
  }
}
```

## Room Types Reference

| Room Type | Use Case | Example |
|-----------|----------|---------|
| `agent_team` | Team coordination | "Q1 Sales Team" |
| `client_session` | Client portal communication | "Smith Family Portal" |
| `lead_collaboration` | Lead handoffs | "Lead XYZ Coordination" |
| `property_tour` | Virtual tours | "123 Main St Tour" |
| `training_session` | Agent coaching | "New Agent Onboarding" |
| `emergency_response` | Urgent issues | "Critical Lead Response" |

## Message Types Reference

| Message Type | Description | Priority |
|--------------|-------------|----------|
| `text` | Standard message | normal |
| `lead_handoff` | Lead transfer | high |
| `property_share` | Property info | normal |
| `coaching_tip` | Real-time coaching | normal |
| `alert` | Important notification | high/urgent |
| `system` | System notification | normal |

## Integration Checklist

- [ ] Include collaboration router in FastAPI app
- [ ] Initialize collaboration engine on startup
- [ ] Configure JWT authentication
- [ ] Set up WebSocket endpoint
- [ ] Add frontend WebSocket client
- [ ] Implement message display UI
- [ ] Add presence indicators
- [ ] Set up performance monitoring

## Testing

```bash
# Run collaboration tests
pytest ghl_real_estate_ai/tests/test_realtime_collaboration.py -v

# Test specific feature
pytest ghl_real_estate_ai/tests/test_realtime_collaboration.py::test_send_message_latency -v

# Run with coverage
pytest ghl_real_estate_ai/tests/test_realtime_collaboration.py --cov
```

## Troubleshooting

**High Latency**
- Check Redis connection
- Monitor network latency
- Review circuit breaker status

**Connection Failures**
- Verify JWT token
- Check WebSocket URL format
- Ensure Redis is running

**Message Delivery Issues**
- Verify room exists
- Check user is room member
- Review WebSocket connection status

## Next Steps

- Read full documentation: `/REALTIME_COLLABORATION_IMPLEMENTATION.md`
- Review API reference: `/api/v1/docs`
- Check example implementations in tests
- Monitor performance metrics in production

---

**Quick Links:**
- Full Documentation: `REALTIME_COLLABORATION_IMPLEMENTATION.md`
- API Endpoints: `/api/v1/collaboration/*`
- Test Suite: `tests/test_realtime_collaboration.py`
- Models: `models/collaboration_models.py`

**Support:** See troubleshooting section or full documentation for detailed help.
