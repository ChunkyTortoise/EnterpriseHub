# Phase 2 API Reference Guide

Complete reference for all Phase 2 API endpoints.

## Table of Contents
1. [Analytics Endpoints](#analytics-endpoints)
2. [Bulk Operations Endpoints](#bulk-operations-endpoints)
3. [Lead Lifecycle Endpoints](#lead-lifecycle-endpoints)

---

## Analytics Endpoints

### Dashboard Metrics
**GET** `/api/analytics/dashboard`

Get high-level analytics dashboard metrics.

**Query Parameters:**
- `location_id` (required): GHL Location ID
- `days` (optional, default: 7): Number of days to analyze

**Response:**
```json
{
  "total_conversations": 150,
  "avg_lead_score": 62.5,
  "conversion_rate": 0.15,
  "response_time_avg": 2.3,
  "hot_leads": 45,
  "warm_leads": 60,
  "cold_leads": 45,
  "period_start": "2026-01-01T00:00:00",
  "period_end": "2026-01-07T23:59:59"
}
```

### Performance Report
**GET** `/api/analytics/performance-report/{location_id}`

Generate detailed performance analysis report with optimization recommendations.

**Response:**
```json
{
  "location_id": "LOC_123",
  "report": "=== PERFORMANCE ANALYSIS REPORT ===\n...",
  "detailed_analysis": {
    "total_conversations": 150,
    "question_effectiveness": {...},
    "conversation_flow": {...},
    "optimization_opportunities": [...]
  },
  "generated_at": "2026-01-04T13:00:00"
}
```

### A/B Test Experiments

#### Create Experiment
**POST** `/api/analytics/experiments`

**Query Parameters:**
- `location_id` (required)

**Request Body:**
```json
{
  "name": "Opening Message Test",
  "variant_a": {"opening": "Hi! Looking for a home?"},
  "variant_b": {"opening": "Hey! Ready to find your dream home?"},
  "metric": "conversion_rate",
  "description": "Test different opening messages"
}
```

**Response:**
```json
{
  "experiment_id": "exp_20260104_130454_123456",
  "location_id": "LOC_123",
  "status": "active",
  "message": "Experiment created successfully"
}
```

#### List Experiments
**GET** `/api/analytics/experiments/{location_id}`

Returns all active experiments for the location.

#### Analyze Experiment
**GET** `/api/analytics/experiments/{location_id}/{experiment_id}/analysis`

Get statistical analysis and winner determination.

**Response:**
```json
{
  "experiment_id": "exp_...",
  "name": "Opening Message Test",
  "metric": "conversion_rate",
  "variant_a": {
    "mean": 0.15,
    "median": 0.15,
    "count": 50
  },
  "variant_b": {
    "mean": 0.22,
    "median": 0.20,
    "count": 48
  },
  "winner": "b",
  "confidence": 0.85,
  "recommendation": "Variant B is performing 7.0% better. Consider implementing."
}
```

#### Record Result
**POST** `/api/analytics/experiments/{location_id}/{experiment_id}/results`

**Query Parameters:**
- `variant`: "a" or "b"

**Request Body:**
```json
{
  "contact_id": "CONTACT_123",
  "conversion": true,
  "lead_score": 75.0,
  "response_time": 1.5
}
```

---

## Bulk Operations Endpoints

### Bulk Import

#### Import from JSON
**POST** `/api/bulk/import`

**Query Parameters:**
- `location_id` (required)

**Request Body:**
```json
{
  "leads": [
    {
      "first_name": "John",
      "last_name": "Doe",
      "phone": "+1234567890",
      "email": "john@example.com"
    }
  ],
  "tags": ["Imported", "Q1-2026"],
  "campaign_id": "CAMP_123"
}
```

**Response:**
```json
{
  "operation_id": "op_20260104_130500_789",
  "status": "processing",
  "message": "Importing 100 leads",
  "total_items": 100
}
```

#### Import from CSV
**POST** `/api/bulk/import/csv`

**Query Parameters:**
- `location_id` (required)
- `tags` (optional): Comma-separated tags

**Form Data:**
- `file`: CSV file (multipart/form-data)

**CSV Format:**
```csv
first_name,last_name,phone,email
John,Doe,+1234567890,john@example.com
Jane,Smith,+0987654321,jane@example.com
```

### Bulk Export

#### Export to JSON
**POST** `/api/bulk/export`

**Query Parameters:**
- `location_id` (required)

**Request Body:**
```json
{
  "filters": {
    "tags": ["Hot-Lead"],
    "created_after": "2026-01-01"
  },
  "fields": ["first_name", "last_name", "phone", "email", "lead_score"]
}
```

**Response:** JSON file download

#### Export to CSV
**POST** `/api/bulk/export/csv`

Same as JSON export but returns CSV file.

### Bulk SMS Campaign
**POST** `/api/bulk/sms/campaign`

**Query Parameters:**
- `location_id` (required)

**Request Body:**
```json
{
  "contact_ids": ["C1", "C2", "C3"],
  "message": "New property alert! Check out 123 Main St. Reply YES for details.",
  "schedule_at": "2026-01-05T09:00:00"
}
```

**Validation:**
- Message must be ≤160 characters
- Returns 400 error if exceeded

### Bulk Tagging
**POST** `/api/bulk/tags/apply`

**Query Parameters:**
- `location_id` (required)

**Request Body:**
```json
{
  "contact_ids": ["C1", "C2", "C3"],
  "tags_to_add": ["Q1-Campaign", "Interested"],
  "tags_to_remove": ["Cold-Lead"]
}
```

### Operation Status
**GET** `/api/bulk/operations/{operation_id}`

**Query Parameters:**
- `location_id` (required)

**Response:**
```json
{
  "operation_id": "op_123",
  "status": "completed",
  "total_items": 100,
  "processed_items": 100,
  "failed_items": 2,
  "errors": ["Contact C50: Invalid phone", "Contact C75: Duplicate"],
  "started_at": "2026-01-04T13:00:00",
  "completed_at": "2026-01-04T13:05:30"
}
```

---

## Lead Lifecycle Endpoints

### Stage Management

#### Transition Stage
**POST** `/api/lifecycle/stages/transition`

**Query Parameters:**
- `location_id` (required)

**Request Body:**
```json
{
  "contact_id": "CONTACT_123",
  "new_stage": "hot",
  "reason": "Scheduled property viewing",
  "notes": "Interested in 3BR homes in downtown"
}
```

**Valid Stages:** `cold`, `warm`, `hot`, `qualified`, `lost`

#### Get Stage History
**GET** `/api/lifecycle/stages/{location_id}/{contact_id}/history`

Returns complete transition history for a lead.

### Lead Health Monitoring

#### Get Lead Health
**GET** `/api/lifecycle/health/{location_id}/{contact_id}`

**Response:**
```json
{
  "contact_id": "CONTACT_123",
  "health_score": 0.75,
  "last_interaction": "2026-01-03T14:30:00",
  "days_since_contact": 1,
  "engagement_level": "high",
  "risk_level": "low",
  "recommended_action": "Continue nurturing, schedule follow-up"
}
```

#### Get At-Risk Leads
**GET** `/api/lifecycle/health/{location_id}/at-risk`

**Query Parameters:**
- `threshold` (optional, default: 0.3): Health score threshold (0-1)

Returns list of leads below health threshold.

### Re-engagement Campaigns

#### Create Campaign
**POST** `/api/lifecycle/reengage/campaign`

**Query Parameters:**
- `location_id` (required)

**Request Body:**
```json
{
  "contact_ids": ["C1", "C2"],
  "filters": {
    "days_inactive": 30,
    "last_stage": "warm"
  },
  "template": "Hi {first_name}, haven't heard from you in a while. Still looking?",
  "schedule_at": "2026-01-05T10:00:00"
}
```

#### Get Eligible Leads
**GET** `/api/lifecycle/reengage/{location_id}/eligible`

**Query Parameters:**
- `days_inactive` (optional, default: 30)

### Lifecycle Metrics
**GET** `/api/lifecycle/metrics/{location_id}`

**Query Parameters:**
- `days` (optional, default: 30): Analysis period

**Response:**
```json
{
  "total_leads": 500,
  "by_stage": {
    "cold": 200,
    "warm": 150,
    "hot": 100,
    "qualified": 40,
    "lost": 10
  },
  "avg_time_to_qualified": 14.5,
  "conversion_rate": 0.08,
  "churn_rate": 0.02,
  "active_nurture_sequences": 75
}
```

### Nurture Sequences

#### Start Sequence
**POST** `/api/lifecycle/nurture/start`

**Query Parameters:**
- `location_id` (required)
- `contact_id` (required)
- `sequence_type` (required): e.g., "warm_lead_nurture", "hot_lead_followup"

#### Stop Sequence
**POST** `/api/lifecycle/nurture/{sequence_id}/stop`

**Query Parameters:**
- `location_id` (required)

---

## Error Responses

All endpoints follow consistent error format:

```json
{
  "detail": "Error message description"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `202` - Accepted (async operation)
- `400` - Bad Request (validation error)
- `404` - Not Found
- `500` - Internal Server Error

---

## Rate Limiting

Phase 2 endpoints respect GHL API rate limits:
- 120 requests per minute per location
- Bulk operations are queued and processed asynchronously

---

## Authentication

All endpoints require valid GHL authentication. Include in headers:
```
Authorization: Bearer {GHL_API_KEY}
```

Or configure per-location keys using the tenant service.

---

For more information, see the full API documentation at `/docs` (development mode).
