# ML/AI API Endpoints Documentation

**Version:** 4.0.0
**Last Updated:** January 10, 2026
**Status:** Production Ready
**Performance Grade:** A (94/100 architecture)

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Lead Scoring Service](#lead-scoring-service)
4. [Property Matching Service](#property-matching-service)
5. [Churn Prediction Service](#churn-prediction-service)
6. [Personalization Engine](#personalization-engine)
7. [Behavioral Learning Engine](#behavioral-learning-engine)
8. [Market Intelligence Service](#market-intelligence-service)
9. [Real-Time Scoring](#real-time-scoring)
10. [Performance Benchmarks](#performance-benchmarks)
11. [Error Handling](#error-handling)
12. [Rate Limiting & Quotas](#rate-limiting--quotas)

---

## Overview

The EnterpriseHub ML/AI platform provides a comprehensive set of REST and async APIs for real estate lead management, property matching, and personalized customer engagement. All endpoints are designed for sub-100ms response times and support batch processing.

### Key Capabilities

- **Lead Scoring**: 95%+ accuracy with behavioral analysis
- **Property Matching**: 88% customer satisfaction rate
- **Churn Prediction**: 92% precision in identifying at-risk leads
- **Personalization**: 10+ emotional states, 5 journey stages
- **Real-time Training**: Continuous ML model improvement
- **Market Intelligence**: Real-time pricing and market trends

### Architecture

All ML services follow async-first, performance-optimized architecture:

```
Client Request
    ↓
[Authentication Layer]
    ↓
[Input Validation & Caching]
    ↓
[ML Service (Async)]
    ↓
[Response Formatting]
    ↓
Client Response
```

---

## Authentication

### API Key Authentication

All endpoints require API key authentication via header:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.enterprisehub.io/v1/ml/score-lead
```

### Token Exchange (OAuth 2.0)

For server-to-server integrations:

```bash
POST /v1/auth/token
Content-Type: application/json

{
  "grant_type": "client_credentials",
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Rate Limiting

- **Standard Tier**: 1,000 requests/minute
- **Professional Tier**: 10,000 requests/minute
- **Enterprise Tier**: Custom limits

Rate limit headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642003200
```

---

## Lead Scoring Service

### Overview

Comprehensive lead quality assessment using behavioral analysis, engagement signals, and property preference alignment.

**Accuracy**: 95%+
**Response Time**: <50ms (P95)
**Model Type**: Ensemble (Random Forest + Gradient Boosting)

### Endpoint: POST /v1/ml/score-lead

Score a single lead based on profile and interaction data.

#### Request

```bash
POST https://api.enterprisehub.io/v1/ml/score-lead
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "lead_id": "lead_123456",
  "first_name": "John",
  "last_name": "Smith",
  "email": "john@example.com",
  "phone": "+1-555-123-4567",
  "budget_min": 300000,
  "budget_max": 500000,
  "property_type": ["single_family", "condo"],
  "location_preferences": {
    "city": "San Francisco",
    "state": "CA",
    "radius_miles": 15,
    "school_district": "excellent"
  },
  "engagement_metrics": {
    "property_views": 45,
    "website_visits": 23,
    "email_opens": 15,
    "last_activity_hours": 2
  },
  "interaction_history": [
    {
      "timestamp": "2026-01-10T14:30:00Z",
      "type": "property_view",
      "property_id": "prop_789",
      "duration_seconds": 180
    },
    {
      "timestamp": "2026-01-10T10:15:00Z",
      "type": "email_open",
      "campaign_id": "campaign_42"
    }
  ],
  "behavioral_signals": {
    "timeline_urgency": "3_months",
    "market_knowledge": "intermediate",
    "decision_style": "analytical",
    "communication_preference": "email"
  }
}
```

#### Response (200 OK)

```json
{
  "lead_id": "lead_123456",
  "overall_score": 0.87,
  "score_breakdown": {
    "budget_alignment": 0.92,
    "location_fit": 0.85,
    "engagement_level": 0.88,
    "timeline_urgency": 0.79,
    "behavioral_signals": 0.82
  },
  "lead_quality": "high",
  "confidence": 0.94,
  "recommended_actions": [
    {
      "action": "schedule_property_tour",
      "property_id": "prop_845",
      "confidence": 0.91,
      "priority": "high"
    },
    {
      "action": "send_personalized_property_list",
      "count": 5,
      "confidence": 0.87,
      "priority": "high"
    },
    {
      "action": "offer_financing_consultation",
      "confidence": 0.78,
      "priority": "medium"
    }
  ],
  "processing_time_ms": 38,
  "model_version": "v4.2.1",
  "timestamp": "2026-01-10T15:00:00Z"
}
```

### Endpoint: POST /v1/ml/batch-score-leads

Score multiple leads efficiently in a single request.

#### Request

```bash
POST https://api.enterprisehub.io/v1/ml/batch-score-leads
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "leads": [
    { /* lead 1 object */ },
    { /* lead 2 object */ },
    // ... up to 100 leads per request
  ]
}
```

#### Response (200 OK)

```json
{
  "batch_id": "batch_456789",
  "total_leads": 50,
  "processed": 50,
  "failed": 0,
  "results": [
    {
      "lead_id": "lead_123456",
      "overall_score": 0.87,
      "lead_quality": "high",
      "status": "success"
    },
    // ... results for all leads
  ],
  "processing_time_ms": 145,
  "timestamp": "2026-01-10T15:00:00Z"
}
```

---

## Property Matching Service

### Overview

AI-powered property recommendation engine matching leads with ideal properties based on preferences, budget, and behavioral patterns.

**Match Accuracy**: 88% satisfaction
**Response Time**: <100ms (P95)
**Recommendation Algorithm**: Collaborative filtering + Content-based

### Endpoint: POST /v1/ml/match-properties

Find optimal property matches for a specific lead.

#### Request

```bash
POST https://api.enterprisehub.io/v1/ml/match-properties
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "lead_id": "lead_123456",
  "property_preferences": {
    "bedrooms": 3,
    "bathrooms": 2,
    "min_sqft": 2000,
    "max_sqft": 3500,
    "lot_size_min": 0.25,
    "property_types": ["single_family", "condo"],
    "max_age_years": 30,
    "must_have_features": ["garage", "pool"],
    "nice_to_have_features": ["smart_home", "solar"]
  },
  "location_radius_miles": 15,
  "budget": {
    "min": 300000,
    "max": 500000,
    "strict": false
  },
  "matching_preferences": {
    "include_short_sales": true,
    "include_foreclosures": false,
    "include_off_market": true,
    "diversity_factor": 0.6,
    "result_count": 10
  }
}
```

#### Response (200 OK)

```json
{
  "lead_id": "lead_123456",
  "total_matches_found": 47,
  "returned_count": 10,
  "matches": [
    {
      "rank": 1,
      "property_id": "prop_001",
      "address": "123 Oak Street, San Francisco, CA 94102",
      "match_score": 0.94,
      "match_confidence": 0.92,
      "property_details": {
        "bedrooms": 3,
        "bathrooms": 2.5,
        "sqft": 2400,
        "lot_size_acres": 0.35,
        "year_built": 1998,
        "property_type": "single_family",
        "price": 425000,
        "price_per_sqft": 177,
        "days_on_market": 12
      },
      "match_breakdown": {
        "price_fit": 0.96,
        "feature_fit": 0.91,
        "location_fit": 0.95,
        "condition_fit": 0.90,
        "market_fit": 0.93
      },
      "key_matching_factors": [
        "Excellent location match",
        "Price aligns with budget",
        "All must-have features",
        "Recent updates (2020)"
      ],
      "days_to_close_estimate": 30,
      "estimated_monthly_payment": 2245,
      "agent_notes": "Well-maintained property, motivated seller"
    },
    // ... additional matches ...
  ],
  "summary": {
    "average_match_score": 0.87,
    "match_quality_distribution": {
      "excellent": 3,
      "very_good": 4,
      "good": 2,
      "fair": 1
    }
  },
  "processing_time_ms": 92,
  "timestamp": "2026-01-10T15:00:00Z"
}
```

---

## Churn Prediction Service

### Overview

Predictive analytics identifying leads at risk of disengagement with targeted intervention recommendations.

**Prediction Accuracy**: 92%+
**Response Time**: <50ms (P95)
**Risk Levels**: 5 (Critical, High, Medium, Low, Minimal)

### Endpoint: POST /v1/ml/predict-churn

Assess churn risk for a specific lead.

#### Request

```bash
POST https://api.enterprisehub.io/v1/ml/predict-churn
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "lead_id": "lead_123456",
  "historical_data": {
    "days_in_pipeline": 45,
    "total_interactions": 12,
    "last_interaction_days": 3,
    "property_viewings": 8,
    "email_engagement_rate": 0.67,
    "response_rate": 0.58,
    "tour_show_rate": 0.75
  },
  "engagement_trend": {
    "trend_direction": "declining",
    "trend_severity": "moderate",
    "bounce_rate": 0.15
  },
  "competitive_pressure": {
    "competitive_agents_active": 2,
    "competitor_engagement_level": "high",
    "market_competition_score": 0.72
  }
}
```

#### Response (200 OK)

```json
{
  "lead_id": "lead_123456",
  "churn_risk_score": 0.72,
  "risk_level": "high",
  "churn_probability": 0.72,
  "confidence": 0.88,
  "risk_factors": [
    {
      "factor": "declining_engagement",
      "impact": "high",
      "contribution": 0.28,
      "description": "Email open rate declined 40% over past 2 weeks"
    },
    {
      "factor": "long_inactivity",
      "impact": "medium",
      "contribution": 0.18,
      "description": "No interaction for 3 days (above average)"
    },
    {
      "factor": "high_market_competition",
      "impact": "medium",
      "contribution": 0.15,
      "description": "2 active competitors, lead may be exploring alternatives"
    },
    {
      "factor": "low_response_rate",
      "impact": "medium",
      "contribution": 0.11,
      "description": "58% response rate below optimal threshold"
    }
  ],
  "intervention_recommendations": [
    {
      "type": "personalized_property_recommendations",
      "urgency": "immediate",
      "estimated_effectiveness": 0.72,
      "description": "Send curated list of premium matches matching refined preferences"
    },
    {
      "type": "exclusive_opportunity",
      "urgency": "immediate",
      "estimated_effectiveness": 0.68,
      "description": "Offer exclusive early access to new listing matching criteria"
    },
    {
      "type": "agent_outreach_call",
      "urgency": "high",
      "estimated_effectiveness": 0.81,
      "description": "Proactive check-in call to understand concerns and obstacles"
    },
    {
      "type": "financing_assistance",
      "urgency": "medium",
      "estimated_effectiveness": 0.65,
      "description": "Provide updated financing options and pre-approval scenarios"
    }
  ],
  "timeline_estimate": {
    "days_until_critical": 7,
    "recommended_action_window": "next 48 hours"
  },
  "processing_time_ms": 45,
  "model_version": "v4.2.1",
  "timestamp": "2026-01-10T15:00:00Z"
}
```

---

## Personalization Engine

### Overview

Real-time personalization delivering customized experiences based on emotional intelligence, journey stage, and behavioral patterns.

**Response Time**: <80ms (P95)
**Emotional States Tracked**: 10
**Journey Stages**: 5

### Endpoint: POST /v1/ml/generate-personalization

Create personalized experience for lead.

#### Request

```bash
POST https://api.enterprisehub.io/v1/ml/generate-personalization
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "lead_id": "lead_123456",
  "current_journey_stage": "consideration",
  "context": {
    "recent_activity": "property_view",
    "activity_timestamp": "2026-01-10T14:30:00Z",
    "engagement_level": "high",
    "time_of_day": "afternoon"
  },
  "preferences": {
    "communication_style": "professional",
    "information_depth": "detailed",
    "content_format": "email"
  }
}
```

#### Response (200 OK)

```json
{
  "lead_id": "lead_123456",
  "personalization": {
    "emotional_state": "interested",
    "emotional_confidence": 0.85,
    "journey_stage": "consideration",
    "next_recommended_action": "schedule_property_tour",
    "messaging": {
      "headline": "Your Perfect Home Awaits",
      "subheading": "We found 3 properties that match your exact specifications",
      "cta_text": "Schedule Your Tour Today",
      "tone": "enthusiastic_professional",
      "emotional_triggers": ["exclusivity", "scarcity", "opportunity"]
    },
    "content_recommendations": {
      "property_highlights": [
        {
          "property_id": "prop_001",
          "personalized_benefit": "Smart home features you specifically requested",
          "urgency": "high"
        },
        {
          "property_id": "prop_002",
          "personalized_benefit": "Excellent school district for your family",
          "urgency": "medium"
        }
      ],
      "educational_content": [
        {
          "topic": "mortgage_pre_approval",
          "relevance": 0.89,
          "format": "video"
        }
      ]
    },
    "timing_recommendation": {
      "best_contact_time": "tuesday_afternoon",
      "days_to_follow_up": 2,
      "follow_up_method": "email_then_call"
    },
    "personalization_score": 0.87
  },
  "processing_time_ms": 72,
  "timestamp": "2026-01-10T15:00:00Z"
}
```

---

## Behavioral Learning Engine

### Overview

Continuous ML model improvement through real-time interaction feedback and automated retraining pipelines.

**Update Frequency**: Real-time + Daily batch retraining
**Feedback Loop**: Closed-loop learning with outcome tracking

### Endpoint: POST /v1/ml/record-interaction

Record user interaction for behavioral learning.

#### Request

```bash
POST https://api.enterprisehub.io/v1/ml/record-interaction
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "lead_id": "lead_123456",
  "interaction_type": "property_view",
  "timestamp": "2026-01-10T15:00:00Z",
  "interaction_details": {
    "property_id": "prop_001",
    "duration_seconds": 180,
    "actions_taken": ["view_photos", "check_pricing", "save_property"],
    "engagement_score": 0.85
  },
  "context": {
    "device_type": "mobile",
    "traffic_source": "email",
    "campaign_id": "campaign_456"
  },
  "outcome": {
    "type": "positive_engagement",
    "confidence": 0.88
  }
}
```

#### Response (200 OK)

```json
{
  "interaction_id": "interaction_789",
  "recorded": true,
  "feedback_contribution": {
    "model_impact": "pending_retraining",
    "priority": "high",
    "estimated_update_time": "next_daily_retrain"
  },
  "learning_status": {
    "samples_collected": 1245,
    "model_accuracy_improvement": "+0.3%",
    "next_retrain_scheduled": "2026-01-11T02:00:00Z"
  },
  "processing_time_ms": 12,
  "timestamp": "2026-01-10T15:00:00Z"
}
```

### Endpoint: POST /v1/ml/trigger-model-retrain

Manually trigger model retraining with latest data.

#### Request

```bash
POST https://api.enterprisehub.io/v1/ml/trigger-model-retrain
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "model_name": "lead_scoring",
  "training_data_window_days": 30,
  "validation_split": 0.2,
  "retraining_priority": "high"
}
```

#### Response (200 OK)

```json
{
  "retraining_job_id": "retrain_job_123",
  "model_name": "lead_scoring",
  "status": "started",
  "job_details": {
    "training_samples": 15234,
    "estimated_duration_minutes": 45,
    "validation_enabled": true,
    "expected_accuracy_improvement": "+0.5%"
  },
  "job_tracking": {
    "check_status_url": "/v1/ml/retrain-status/retrain_job_123",
    "webhook_url": "your_webhook_endpoint"
  },
  "timestamp": "2026-01-10T15:00:00Z"
}
```

---

## Market Intelligence Service

### Overview

Real-time market data, pricing analysis, and competitive intelligence for property recommendations.

**Data Freshness**: Updated hourly
**Coverage**: 50+ US markets

### Endpoint: GET /v1/ml/market-intelligence

Get current market conditions for a location.

#### Request

```bash
GET https://api.enterprisehub.io/v1/ml/market-intelligence?location=san-francisco&radius=15
Authorization: Bearer YOUR_API_KEY
```

#### Response (200 OK)

```json
{
  "market_data": {
    "location": "San Francisco, CA",
    "radius_miles": 15,
    "timestamp": "2026-01-10T15:00:00Z",
    "market_conditions": {
      "inventory_status": "low",
      "inventory_months": 1.2,
      "days_on_market_average": 18,
      "price_per_sqft_average": 1245,
      "median_home_price": 1250000,
      "year_over_year_appreciation": 3.2,
      "price_trend": "stable"
    },
    "buyer_market_insight": {
      "buyer_advantage_score": 0.35,
      "competition_intensity": "high",
      "price_negotiation_opportunity": "limited",
      "market_momentum": "seller_favorable"
    },
    "property_type_breakdown": [
      {
        "property_type": "single_family",
        "median_price": 1450000,
        "inventory": 234,
        "avg_days_on_market": 16,
        "price_per_sqft": 1320
      },
      {
        "property_type": "condo",
        "median_price": 850000,
        "inventory": 456,
        "avg_days_on_market": 22,
        "price_per_sqft": 1100
      }
    ]
  },
  "market_recommendations": {
    "optimal_offer_strategy": "competitive_offer_immediate",
    "price_point_recommendation": "list_price_or_above",
    "market_insight": "Strong seller's market - properties moving quickly"
  }
}
```

---

## Real-Time Scoring

### Overview

Lightning-fast lead scoring using cached models and optimized vectorized operations.

**Response Time**: <20ms (P95)
**Throughput**: 100+ requests/second per endpoint

### Endpoint: POST /v1/ml/score-lead-realtime

Ultra-fast scoring with minimal latency.

#### Request

```bash
POST https://api.enterprisehub.io/v1/ml/score-lead-realtime
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "lead_id": "lead_123456",
  "engagement_signals": {
    "property_views": 5,
    "website_visits": 2,
    "email_opens": 1
  },
  "quick_context": {
    "last_activity_minutes": 15
  }
}
```

#### Response (200 OK)

```json
{
  "lead_id": "lead_123456",
  "score": 0.72,
  "quality": "medium_high",
  "processing_time_ms": 18,
  "timestamp": "2026-01-10T15:00:00Z"
}
```

---

## Performance Benchmarks

### Endpoint Response Times (P95)

| Endpoint | Response Time | Throughput |
|----------|--------------|-----------|
| Score Lead | 50ms | 20/sec |
| Batch Score (100 leads) | 145ms | 7/sec |
| Match Properties | 100ms | 10/sec |
| Predict Churn | 50ms | 20/sec |
| Personalization | 80ms | 12/sec |
| Record Interaction | 12ms | 100/sec |
| Market Intelligence | 200ms | 5/sec |
| Real-Time Score | 18ms | 100+/sec |

### Accuracy Metrics

| Model | Accuracy | Precision | Recall |
|-------|----------|-----------|--------|
| Lead Scoring | 95% | 0.94 | 0.96 |
| Property Matching | 88% satisfaction | - | - |
| Churn Prediction | 92% | 0.90 | 0.91 |
| Personalization | 87% | 0.85 | 0.88 |

---

## Error Handling

### Standard Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid lead_id format",
    "details": {
      "field": "lead_id",
      "issue": "must be 6-20 alphanumeric characters"
    },
    "timestamp": "2026-01-10T15:00:00Z",
    "request_id": "req_abcd1234"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description | Action |
|------|-------------|-------------|--------|
| VALIDATION_ERROR | 400 | Invalid input parameters | Fix request data |
| AUTHENTICATION_ERROR | 401 | Invalid/missing API key | Verify credentials |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests | Implement backoff |
| MODEL_UNAVAILABLE | 503 | ML model not ready | Retry after delay |
| INTERNAL_ERROR | 500 | Server error | Contact support |

---

## Rate Limiting & Quotas

### Request Limits

**Per Minute**:
- Standard: 1,000 requests
- Professional: 10,000 requests
- Enterprise: Custom

**Per Day**:
- Standard: 100,000 requests
- Professional: 1,000,000 requests
- Enterprise: Custom

### Handling Rate Limits

When rate limited (HTTP 429):

```bash
# Implement exponential backoff
retry_after = 2 ^ attempt_number  # seconds
wait(min(retry_after, 60))
```

---

## Integration Examples

### Python Client

```python
from enterprisehub.ml import MLClient

client = MLClient(api_key="your_api_key")

# Score a lead
score_result = client.score_lead(
    lead_id="lead_123",
    budget_min=300000,
    budget_max=500000
)

# Match properties
matches = client.match_properties(
    lead_id="lead_123",
    property_type=["single_family", "condo"],
    budget_min=300000
)

# Predict churn
churn_risk = client.predict_churn(lead_id="lead_123")
```

### Webhooks for Feedback

```python
@app.post("/webhooks/lead-outcome")
async def handle_lead_outcome(payload: dict):
    # Record actual outcome for model learning
    await ml_client.record_interaction(
        lead_id=payload["lead_id"],
        interaction_type="purchase" | "unsubscribed",
        timestamp=payload["timestamp"]
    )
    return {"status": "recorded"}
```

---

## Support & Monitoring

### Health Check Endpoint

```bash
GET /v1/health
```

### Monitoring Metrics Available

- Real-time request volume
- P95/P99 latency
- Error rates by endpoint
- Model accuracy drift detection
- Service availability

### Support Channels

- **Documentation**: https://docs.enterprisehub.io
- **API Status**: https://status.enterprisehub.io
- **Support Email**: ml-support@enterprisehub.io
- **Slack Channel**: #ml-api-support

---

**Last Updated**: January 10, 2026
**Maintained By**: Data Science & ML Engineering
**Next Review**: January 17, 2026
