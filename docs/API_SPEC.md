# EnterpriseHub API Specification

**Version**: 1.0.0
**Base URL**: `https://api.enterprise-hub.com/api`
**Last Updated**: February 2, 2026

---

## Table of Contents

1. [Authentication](#authentication)
2. [Rate Limiting](#rate-limiting)
3. [Health & Status](#health--status)
4. [Lead Management](#lead-management)
5. [Lead Bot Management](#lead-bot-management)
6. [Buyer Matching](#buyer-matching)
7. [Seller Analysis](#seller-analysis)
8. [Bot Management](#bot-management)
9. [Agent Ecosystem](#agent-ecosystem)
10. [Claude Chat & Concierge](#claude-chat--concierge)
11. [Analytics & BI](#analytics--bi)
12. [Property Intelligence](#property-intelligence)
13. [Customer Journey](#customer-journey)
14. [Webhooks](#webhooks)
15. [Voice Integration](#voice-integration)
16. [WebSocket Real-Time](#websocket-real-time)
17. [Error Monitoring](#error-monitoring)
18. [Security](#security)
19. [Error Codes](#error-codes)

---

## Authentication

### API Key Authentication

All API requests require authentication via the `Authorization` header or `X-API-Key` header:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.enterprise-hub.com/api/health
```

Or using the API key header:

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  https://api.enterprise-hub.com/api/health
```

### JWT Token Authentication

For interactive sessions and the admin portal, use JWT tokens:

```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your-password"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

Use the token in subsequent requests:

```bash
curl -H "Authorization: Bearer eyJhbGc..." \
  https://api.enterprise-hub.com/api/leads
```

### Enterprise SSO

For enterprise customers using SAML/OAuth SSO:

```bash
POST /api/enterprise/auth/sso/initiate
Content-Type: application/json

{
  "domain": "company.com",
  "redirect_uri": "https://app.company.com/callback"
}
```

### Multi-Tenant Authentication

Requests scoped to a GHL location require the location header:

```bash
curl -H "X-Location-ID: YOUR_GHL_LOCATION_ID" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.enterprise-hub.com/api/leads
```

---

## Rate Limiting

### Per-Environment Limits

| Environment | Unauthenticated | Authenticated | IP Blocking |
|------------|-----------------|---------------|-------------|
| Production | 100 req/min     | 1,000 req/min | Enabled     |
| Staging    | 500 req/min     | 5,000 req/min | Enabled     |
| Development| 10,000 req/min  | 50,000 req/min| Disabled    |

### Response Headers

Every API response includes rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1706900400
```

### Rate Limited Response (429)

```json
{
  "error": "rate_limit_exceeded",
  "message": "100 requests per minute limit exceeded",
  "retry_after": 30
}
```

---

## Health & Status

### GET /api/health

System health check endpoint.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "services": {
    "database": "connected",
    "redis": "connected",
    "claude_api": "available",
    "ghl_api": "available",
    "websocket": "active"
  },
  "uptime_seconds": 86400,
  "timestamp": "2026-02-02T10:00:00Z"
}
```

### GET /

Root endpoint with basic service info.

**Response** (200 OK):
```json
{
  "service": "GHL Real Estate AI",
  "version": "1.0.0",
  "status": "running",
  "environment": "production",
  "docs": "disabled in production"
}
```

---

## Lead Management

### GET /api/leads

List all leads with filtering and pagination.

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status: `new`, `qualified`, `nurture`, `closed` |
| `temperature` | string | Filter by temperature: `hot`, `warm`, `cold` |
| `page` | integer | Page number (default: 1) |
| `per_page` | integer | Items per page (default: 20, max: 100) |

**Response** (200 OK):
```json
{
  "leads": [
    {
      "id": "lead-001",
      "name": "John Smith",
      "phone": "+1-555-0100",
      "email": "john@example.com",
      "status": "qualified",
      "temperature": "hot",
      "lead_score": 8,
      "intent": "buyer_intent",
      "created_at": "2026-02-01T10:00:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "per_page": 20
}
```

### PATCH /api/leads/{lead_id}

Update lead information.

**Request**:
```json
{
  "status": "qualified",
  "temperature": "hot",
  "notes": "Pre-approved, looking in Victoria area"
}
```

**Response** (200 OK):
```json
{
  "id": "lead-001",
  "status": "qualified",
  "temperature": "hot",
  "updated_at": "2026-02-02T10:00:00Z"
}
```

---

## Lead Bot Management

### POST /api/lead-bot/sequences/start

Start a lead nurture sequence (3-7-30 day follow-up).

**Request**:
```json
{
  "lead_id": "lead-001",
  "sequence_type": "buyer_nurture",
  "channel": "sms"
}
```

**Response** (201 Created):
```json
{
  "sequence_id": "seq-abc123",
  "lead_id": "lead-001",
  "status": "active",
  "next_touchpoint": "2026-02-05T10:00:00Z",
  "touchpoints_remaining": 3
}
```

### POST /api/lead-bot/sequences/stop

Stop an active sequence.

**Request**:
```json
{
  "sequence_id": "seq-abc123",
  "reason": "lead_converted"
}
```

---

## Buyer Matching

### POST /api/properties/match

Match properties to buyer preferences.

**Request**:
```json
{
  "buyer_id": "buyer-001",
  "budget_min": 600000,
  "budget_max": 800000,
  "bedrooms": [3, 4],
  "neighborhoods": ["Victoria", "Haven", "Etiwanda"],
  "sort_by": "relevance"
}
```

**Response** (200 OK):
```json
{
  "match_session_id": "match-xyz789",
  "buyer_id": "buyer-001",
  "total_matches": 12,
  "matches": [
    {
      "rank": 1,
      "property_id": "prop-001",
      "address": "123 Main St, Rancho Cucamonga, CA 91730",
      "price": 725000,
      "bedrooms": 3,
      "bathrooms": 2,
      "square_feet": 1850,
      "match_score": 0.95,
      "explanation": "Perfect match: 3BR, $725k, Victoria neighborhood"
    }
  ],
  "next_actions": ["Schedule showing", "Request CMA"]
}
```

### GET /api/properties/{property_id}

Get detailed property intelligence.

**Response** (200 OK):
```json
{
  "id": "prop-001",
  "address": "123 Main St, Rancho Cucamonga, CA 91730",
  "price": 725000,
  "bedrooms": 3,
  "bathrooms": 2,
  "square_feet": 1850,
  "neighborhood": "Victoria",
  "market_data": {
    "days_on_market": 14,
    "price_per_sqft": 392,
    "comparable_avg_price": 735000
  }
}
```

---

## Seller Analysis

### POST /api/jorge-advanced/seller-analyze

Analyze property and generate CMA.

**Request**:
```json
{
  "seller_id": "seller-001",
  "property_address": "456 Oak Ave, Rancho Cucamonga, CA 91730",
  "bedrooms": 4,
  "bathrooms": 2.5,
  "square_feet": 2500,
  "condition": "good",
  "list_price": 850000
}
```

**Response** (200 OK):
```json
{
  "analysis_id": "anal-001",
  "cma": {
    "comparable_properties": [],
    "price_recommendation": {
      "low": 820000,
      "mid": 850000,
      "high": 880000,
      "confidence": 0.92
    }
  },
  "market_conditions": "Strong buyer market",
  "seller_temperature": "warm",
  "pcs_score": 72,
  "recommendations": [
    "Price competitively at $845,000",
    "Stage kitchen and master bedroom",
    "Professional photography recommended"
  ]
}
```

---

## Bot Management

### GET /api/bot-management/status

Get Jorge bot status and metrics.

**Response** (200 OK):
```json
{
  "bots": {
    "jorge_lead_bot": {
      "status": "active",
      "conversations_today": 47,
      "avg_response_time_ms": 380,
      "qualification_rate": 0.68
    },
    "jorge_buyer_bot": {
      "status": "active",
      "matches_today": 23,
      "avg_match_score": 0.87
    },
    "jorge_seller_bot": {
      "status": "active",
      "analyses_today": 12,
      "avg_confidence": 0.91
    }
  },
  "system_health": "healthy"
}
```

### POST /api/bot-management/toggle

Enable or disable a specific bot.

**Request**:
```json
{
  "bot_name": "jorge_buyer_bot",
  "enabled": true
}
```

---

## Agent Ecosystem

### GET /api/agent-ecosystem/status

Get status of all agents in the ecosystem.

**Response** (200 OK):
```json
{
  "agents": [
    {
      "name": "jorge_lead_bot",
      "type": "qualification",
      "status": "active",
      "load": 0.45,
      "conversations_active": 3
    }
  ],
  "mesh_status": "healthy",
  "total_agents": 12,
  "active_agents": 10
}
```

### GET /api/agent-ecosystem/metrics

Get agent performance metrics.

---

## Claude Chat & Concierge

### POST /api/claude-chat/message

Send a message to the Claude AI assistant.

**Request**:
```json
{
  "message": "What properties are available in Victoria under $800k?",
  "conversation_id": "conv-001",
  "context": {
    "lead_id": "lead-001",
    "intent": "buyer"
  }
}
```

**Response** (200 OK):
```json
{
  "response": "I found 8 properties in Victoria under $800k...",
  "conversation_id": "conv-001",
  "tokens_used": {
    "input": 250,
    "output": 180
  },
  "suggested_actions": ["View properties", "Schedule showing"]
}
```

### GET /api/claude-concierge/guidance

Get AI-powered coaching and guidance.

---

## Analytics & BI

### GET /api/analytics/dashboard

Get analytics dashboard data.

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `period` | string | `today`, `week`, `month`, `quarter` |
| `metrics` | string | Comma-separated metric names |

**Response** (200 OK):
```json
{
  "period": "month",
  "leads": {
    "total": 450,
    "qualified": 280,
    "conversion_rate": 0.62
  },
  "revenue": {
    "attributed": 125000,
    "pipeline": 450000
  },
  "bot_performance": {
    "avg_response_time_ms": 380,
    "accuracy": 0.92,
    "escalation_rate": 0.08
  }
}
```

### GET /api/business-intelligence/kpis

Get business intelligence KPI data.

### GET /api/predictive-analytics/forecast

Get predictive analytics and forecasts.

### GET /api/attribution-reports

Get revenue attribution reports.

### GET /api/ml-scoring/scores

Get ML-powered lead scores.

---

## Property Intelligence

### GET /api/property-intelligence/{property_id}

Get comprehensive property intelligence including market data, comparables, and AI insights.

### POST /api/pricing-optimization/analyze

Run pricing optimization analysis for a property.

---

## Customer Journey

### GET /api/customer-journey/{lead_id}

Get the full customer journey map for a lead.

**Response** (200 OK):
```json
{
  "lead_id": "lead-001",
  "journey_stage": "property_search",
  "touchpoints": [
    {
      "timestamp": "2026-01-15T10:00:00Z",
      "channel": "web",
      "action": "inquiry_submitted",
      "bot": "jorge_lead_bot"
    },
    {
      "timestamp": "2026-01-15T10:02:00Z",
      "channel": "sms",
      "action": "qualification_started",
      "bot": "jorge_lead_bot"
    },
    {
      "timestamp": "2026-01-16T14:00:00Z",
      "channel": "phone",
      "action": "showing_scheduled",
      "bot": "jorge_buyer_bot"
    }
  ],
  "next_recommended_action": "Send property comparison report"
}
```

---

## Webhooks

### POST /api/webhooks/ghl

GoHighLevel webhook receiver. Processes incoming GHL events (contact updates, messages, form submissions).

**Expected Payload** (from GHL):
```json
{
  "type": "ContactCreate",
  "locationId": "loc-001",
  "contactId": "contact-001",
  "body": "I'm interested in buying a home",
  "phone": "+1-555-0100"
}
```

**Headers**:
- `X-GHL-Signature`: HMAC signature for webhook verification

### POST /api/external-webhooks/{provider}

Receive webhooks from external providers (Stripe, Twilio, SendGrid).

### Webhook Events (Outbound)

The system can emit the following webhook events:

| Event | Description |
|-------|-------------|
| `lead.qualified` | Lead qualification completed |
| `lead.score_changed` | Lead score updated |
| `buyer.matched` | Properties matched to buyer |
| `seller.analyzed` | Seller analysis completed |
| `appointment.scheduled` | Appointment booked |
| `bot.escalation` | Bot escalated to human agent |

---

## Voice Integration

### POST /api/voice/vapi/webhook

VAPI voice AI webhook handler.

### POST /api/retell/webhook

Retell AI voice webhook handler.

### POST /api/voice/call

Initiate an outbound voice call.

**Request**:
```json
{
  "lead_id": "lead-001",
  "phone": "+1-555-0100",
  "purpose": "follow_up",
  "script_template": "buyer_qualification"
}
```

---

## WebSocket Real-Time

### WebSocket Connection

Connect to the WebSocket server for real-time updates:

```javascript
const ws = new WebSocket('wss://api.enterprise-hub.com/api/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['leads', 'bots', 'analytics']
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Real-time update:', data);
};
```

### Socket.IO Connection

For the BI dashboard, Socket.IO provides real-time updates:

```javascript
const socket = io('https://api.enterprise-hub.com', {
  transports: ['websocket', 'polling']
});

socket.on('lead_update', (data) => {
  console.log('Lead updated:', data);
});

socket.on('bot_metric', (data) => {
  console.log('Bot metric:', data);
});
```

### WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `lead_update` | Server -> Client | Lead data changed |
| `bot_metric` | Server -> Client | Bot performance metric |
| `alert` | Server -> Client | System alert |
| `conversation_update` | Server -> Client | Active conversation update |

### GET /api/websocket/performance

Get WebSocket server performance metrics.

---

## Error Monitoring

### GET /api/error-monitoring/dashboard

Get error monitoring dashboard data.

**Response** (200 OK):
```json
{
  "error_rate_5m": 0.02,
  "total_errors_today": 47,
  "top_errors": [
    {
      "type": "TimeoutError",
      "count": 12,
      "service": "claude_api",
      "last_seen": "2026-02-02T09:45:00Z"
    }
  ],
  "status": "healthy"
}
```

---

## Security

### GET /api/security/audit-log

Get security audit log entries.

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | string | ISO 8601 start date |
| `end_date` | string | ISO 8601 end date |
| `event_type` | string | Filter by event type |

### GET /api/security/status

Get security monitoring status.

---

## Error Codes

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Missing or invalid auth |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found |
| 409 | Conflict - Resource already exists |
| 422 | Validation Error - Invalid input data |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |
| 503 | Service Unavailable - Upstream dependency down |

### Error Response Format

All errors return a consistent JSON structure:

```json
{
  "error": "error_code",
  "message": "Human-readable description",
  "field": "specific_field (if applicable)",
  "code": "MACHINE_READABLE_CODE",
  "request_id": "req-abc123"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `invalid_api_key` | API key is missing or invalid |
| `rate_limit_exceeded` | Request rate limit exceeded |
| `lead_not_found` | Requested lead does not exist |
| `invalid_phone_format` | Phone number format is invalid |
| `qualification_in_progress` | Lead already being qualified |
| `service_unavailable` | External service is down |
| `token_budget_exceeded` | Monthly token budget exhausted |

---

## Performance Headers

Every API response includes performance headers:

| Header | Description |
|--------|-------------|
| `X-Process-Time` | Request processing time in seconds |
| `X-Server-Version` | API server version |
| `X-Performance` | Performance tier: `excellent`, `good`, `acceptable`, `slow` |
| `X-Content-Optimized` | Whether response was optimized |
| `X-Request-ID` | Unique request identifier for tracing |

---

## Mobile API

The mobile API is available at `/api/mobile/` with endpoints optimized for mobile clients.

### Mobile Headers

| Header | Description |
|--------|-------------|
| `X-Device-ID` | Mobile device identifier |
| `X-App-Version` | Mobile app version |
| `X-Platform` | `ios` or `android` |
| `X-Device-Model` | Device model for optimization |
| `X-GPS-Coordinates` | Location for proximity features |
| `X-AR-Capabilities` | AR/VR capability flags |

---

## OpenAPI / Swagger

In development mode, interactive API documentation is available at:

- **Swagger UI**: `GET /docs`
- **ReDoc**: `GET /redoc`

These endpoints are disabled in production for security.

---

**Version**: 1.0.0 | **Last Updated**: February 2, 2026
