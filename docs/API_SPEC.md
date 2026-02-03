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
  "expires_in": 1800
}
```

Token expires in 30 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES = 30`). Refresh tokens last 7 days.

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

From `EnhancedRateLimitMiddleware` (`ghl_real_estate_ai/api/middleware/rate_limiter.py`):

```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60,
  "type": "rate_limit_error"
}
```

Response headers: `Retry-After: 60`, `X-Rate-Limit-Remaining: 0`, `X-Rate-Limit-Reset: <timestamp>`.

Bot traffic (detected by user-agent) receives 1/4 the normal rate limit. IPs are blocked for 15 minutes after repeated violations or >50 requests in 10 seconds. Health check endpoints (`/health`, `/api/health`, `/ping`) are exempt from rate limiting.

---

## Health & Status

Endpoints defined in `ghl_real_estate_ai/api/routes/health.py`, mounted at prefix `/api/health`.

### GET /api/health/

Basic liveness probe. No authentication required. Returns database and cache status.

**Response** (200 OK) -- `HealthResponse`:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-02T10:00:00",
  "version": "1.0.0",
  "environment": "production",
  "uptime_seconds": 86400,
  "checks": {
    "database": "healthy",
    "cache": "healthy"
  }
}
```

Status values: `healthy`, `degraded`, `unhealthy`, `critical`.

### GET /api/health/live

Kubernetes-style liveness probe. Very lightweight -- only verifies the process is responsive.

### GET /api/health/ready (Authenticated)

Kubernetes-style readiness probe. Checks database, cache, and security framework. Returns `DetailedHealthResponse` with per-service health details.

### GET /api/health/deep (Authenticated)

Comprehensive deep health check including external services (Apollo, Twilio, SendGrid, GHL). Includes system metrics (CPU, memory, disk) via `psutil`. Should not be called frequently.

### GET /api/health/metrics (Authenticated)

Performance and operational metrics including SLA compliance data.

### GET /api/health/dependencies (Authenticated)

Status of all external dependencies with response times.

### GET /api/health/status

Human-readable service status page suitable for monitoring dashboards. Returns 200 for healthy/degraded, 503 for unhealthy/critical.

### POST /api/health/alerts/test (Authenticated)

Test the alerting system by creating a test alert.

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

Endpoints defined in `ghl_real_estate_ai/api/routes/bot_management.py`, mounted at prefix `/api`.

### GET /api/bots/health

Bot management system health check.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2026-02-02T10:00:00",
  "bots": {
    "jorge-seller-bot": "initialized",
    "lead-bot": "initialized",
    "intent-decoder": "initialized"
  },
  "services": {
    "cache": "connected",
    "event_publisher": "available"
  }
}
```

### GET /api/bots

List all available bots with real-time status metrics.

**Response** (200 OK) -- `List[BotStatusResponse]`:
```json
[
  {
    "id": "jorge-seller-bot",
    "name": "Jorge Seller Bot",
    "status": "online",
    "lastActivity": "2026-02-02T10:00:00",
    "responseTimeMs": 42.0,
    "conversationsToday": 12,
    "leadsQualified": 5
  },
  {
    "id": "lead-bot",
    "name": "Lead Bot",
    "status": "online",
    "lastActivity": "2026-02-02T10:00:00",
    "responseTimeMs": 150.0,
    "conversationsToday": 8
  },
  {
    "id": "intent-decoder",
    "name": "Intent Decoder",
    "status": "online",
    "lastActivity": "2026-02-02T10:00:00",
    "responseTimeMs": 8.0,
    "conversationsToday": 20
  }
]
```

### POST /api/bots/{bot_id}/chat

Stream bot conversation responses with Server-Sent Events. Returns `text/event-stream`.

**Path Parameters**: `bot_id` -- one of `jorge-seller-bot`, `lead-bot`, `intent-decoder`

**Request** (`ChatMessageRequest`):
```json
{
  "content": "I want to sell my home in Victoria",
  "leadId": "lead-001",
  "leadName": "John Smith",
  "conversationId": "conv-abc123"
}
```

**SSE Events**:
```
data: {"type": "start", "conversationId": "conv-abc123", "botType": "jorge-seller-bot"}
data: {"type": "chunk", "content": "Hey", "chunk": "Hey", "progress": 0.1}
data: {"type": "complete", "full_response": "...", "metadata": {"processingTimeMs": 142.5}}
data: {"type": "done"}
```

### GET /api/bots/{bot_id}/status

Get individual bot health metrics.

### POST /api/jorge-seller/start

Start Jorge Seller Bot qualification conversation.

**Request** (`JorgeStartRequest`):
```json
{
  "leadId": "lead-001",
  "leadName": "John Smith",
  "phone": "+15550100",
  "propertyAddress": "456 Oak Ave, Rancho Cucamonga, CA 91730"
}
```

### POST /api/jorge-seller/process

Process seller message using unified Jorge Seller Bot with enterprise features. Frontend-compatible endpoint matching `enterprise-ui/src/app/api/bots/jorge-seller/route.ts`.

**Request** (`SellerChatRequest`):
```json
{
  "contact_id": "contact-001",
  "location_id": "loc-001",
  "message": "I want to sell my home",
  "contact_info": {"name": "John Smith", "phone": "+15550100"}
}
```

**Response** (`SellerChatResponse`):
```json
{
  "response_message": "Based on our conversation...",
  "seller_temperature": "warm",
  "questions_answered": 1,
  "qualification_complete": false,
  "actions_taken": [{"type": "qualification", "description": "Assessed as warm lead"}],
  "next_steps": "Continue qualification process",
  "analytics": {
    "seller_temperature": "warm",
    "qualification_progress": "1/4",
    "processing_time_ms": 142.5,
    "bot_version": "unified_enterprise"
  }
}
```

### GET /api/intent-decoder/{leadId}/score

Get FRS/PCS scores and intent analysis for a lead. Cached for 5 minutes.

**Response** (`IntentScoreResponse`):
```json
{
  "leadId": "lead-001",
  "frsScore": 72.5,
  "pcsScore": 65.0,
  "temperature": "warm",
  "classification": "motivated_seller",
  "nextBestAction": "Schedule property walkthrough",
  "processingTimeMs": 12.5,
  "breakdown": {
    "motivation": {"score": 80, "category": "high"},
    "timeline": {"score": 70, "category": "medium"},
    "condition": {"score": 65, "category": "medium"},
    "price": {"score": 75, "category": "high"}
  }
}
```

### POST /api/lead-bot/{leadId}/schedule

Trigger lead bot 3-7-30 sequence. Sequence day must be 3, 7, 14, or 30.

### POST /api/lead-bot/automation

Trigger Lead Bot automation for specific lead. Automation types: `day_3`, `day_7`, `day_30`, `post_showing`, `contract_to_close`.

### GET /api/performance/summary

Get comprehensive Jorge Enterprise performance summary.

### GET /api/performance/jorge

Get Jorge Seller Bot specific performance metrics.

### GET /api/performance/lead-automation

Get Lead Bot automation performance metrics.

### GET /api/performance/health

Get comprehensive system health report.

### GET /api/jorge-seller/{lead_id}/progress

Get Jorge Seller Bot qualification progress for a lead.

### POST /api/jorge-seller/{lead_id}/stall-breaker

Apply Jorge's confrontational stall-breaker script. Stall types: `generic`, `price`, `timeline`, `thinking`.

### POST /api/jorge-seller/{lead_id}/handoff

Trigger handoff from Jorge Seller Bot to Lead Bot or another bot.

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

All errors return a consistent JSON structure from `BulletproofErrorHandler` middleware (`ghl_real_estate_ai/api/middleware/error_handler.py`):

```json
{
  "success": false,
  "error": {
    "code": "ConnectionError",
    "category": "connection",
    "message": "Service temporarily unavailable. We're working on it.",
    "retryable": true,
    "severity": "high"
  },
  "correlation_id": "jorge_1706900000_abc12345",
  "timestamp": 1706900000.0,
  "endpoint": "POST /api/bots/jorge-seller-bot/chat",
  "guidance": {
    "action": "Check connectivity",
    "description": "Unable to connect to external services."
  },
  "retry": {
    "recommended": true,
    "suggested_delay_seconds": 5,
    "max_retries": 3
  }
}
```

Error categories: `http`, `timeout`, `connection`, `auth`, `claude_api`, `ghl_api`, `database`, `system`.

Response headers include: `X-Correlation-ID`, `X-Error-Category`, `X-Error-Retryable`.

Circuit breaker activates after 5 consecutive failures per endpoint (60s timeout), returning 503 with `CIRCUIT_BREAKER_OPEN`.

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

**Version**: 1.1.0 | **Last Updated**: February 2, 2026
