# GHL Webhook Handler

## Description
A comprehensive real estate webhook processing framework that standardizes GoHighLevel webhook integration patterns. This skill encapsulates proven patterns for secure webhook handling, lead qualification automation, and AI-powered response generation extracted from production real estate systems.

## Key Features
- **Secure Webhook Processing**: HMAC signature verification, request validation
- **Lead Qualification Logic**: Question-count based scoring with Hot/Warm/Cold classification
- **AI Response Generation**: Claude-powered conversational AI with real estate agent tone
- **Background Task Management**: Async SMS sending and GHL API integration
- **Conversation State Management**: Track lead progression through qualification funnel
- **Fallback Mechanisms**: Graceful degradation when external services fail

## When to Use This Skill
- Setting up GoHighLevel webhook endpoints for real estate lead qualification
- Implementing AI-powered lead nurturing workflows
- Building conversation-driven property matching systems
- Creating automated lead scoring and classification systems
- Integrating Claude AI with real estate CRM platforms

## Core Components

### 1. Webhook Security
- HMAC-SHA256 signature verification
- Request payload validation
- Rate limiting and circuit breaker patterns
- Error handling and logging

### 2. Lead Qualification Engine
- Jorge's proven 7-question framework
- Dynamic scoring: Hot (3+), Warm (2), Cold (1 or less)
- State management across conversation sessions
- Progress tracking and analytics

### 3. AI Response Generation
- Professional real estate agent persona
- SMS-optimized responses (<160 characters)
- Context-aware question progression
- Natural conversation flow with qualification intent

### 4. GHL Integration
- Contact tagging and status updates
- SMS message sending via API
- Custom field updates
- Automated handoff to human agents

## Implementation Framework

### Webhook Endpoint Structure
```python
@app.post("/webhook/ghl")
async def handle_ghl_webhook(request: Request, background_tasks: BackgroundTasks):
    # 1. Security verification
    # 2. Payload parsing
    # 3. Lead qualification check
    # 4. AI response generation
    # 5. Background task scheduling
    # 6. Response formatting
```

### Lead Scoring Algorithm
```python
def calculate_lead_score(answers: Dict[str, Any]) -> tuple[int, str]:
    """
    Jorge's proven criteria:
    - Hot: 3+ qualifying questions answered
    - Warm: 2 qualifying questions answered
    - Cold: 1 or less qualifying questions answered
    """
```

### AI Response Patterns
```python
def get_ai_response(context, question_type):
    """
    Professional, curious, direct tone:
    - "Quick question - what's your budget range looking like?"
    - "Got it. Which neighborhoods are you eyeing?"
    - "When are you hoping to make a move?"
    """
```

## Configuration Management
- Environment variable handling
- Multi-tenant support
- Feature flags for A/B testing
- Webhook secret rotation
- API rate limit configuration

## Testing Framework
- Webhook payload simulation
- Lead progression scenarios
- AI response quality validation
- Performance benchmarking
- Integration testing with GHL

## Monitoring and Analytics
- Response time tracking
- Conversion rate measurement
- Lead qualification funnel analysis
- AI response effectiveness metrics
- Error rate and failure handling

## Security Best Practices
- No secrets in code or logs
- Webhook signature validation
- Input sanitization
- Rate limiting protection
- Audit logging for compliance

## Integration Points
- **GoHighLevel API**: Contact management, SMS, tagging
- **Claude AI API**: Response generation, conversation handling
- **Redis/Database**: State management, caching
- **Monitoring**: Metrics collection, alerting
- **CRM Systems**: Lead handoff, data synchronization

## Business Value
- **Automated Lead Qualification**: 24/7 lead engagement without human intervention
- **Consistent Response Quality**: Professional, branded communication every time
- **Scalable Operations**: Handle unlimited concurrent conversations
- **Data-Driven Insights**: Track conversion funnel and optimize messaging
- **Reduced Response Time**: Instant engagement vs hours for human agents

## Real Estate Domain Expertise
- Proven qualification questions that predict buyer intent
- Natural conversation flow that doesn't feel robotic
- Proper handoff timing to maximize conversion
- Market-specific terminology and responses
- Compliance with real estate communication standards

---

*This skill represents 6 months of real estate AI development distilled into reusable patterns. Each component has been tested in production with real leads and proven conversion rates.*