# AI Secretary SaaS - Architecture Proposal

**Prepared for**: Chase Ashley, FloPro Jamaica  
**Date**: February 12, 2026  
**Prepared by**: Cayman Roden

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE LAYER                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  Web App (React)    │    Mobile App (React Native)    │    Email Gateway   │
│  - Dashboard        │    - Push notifications          │    - Forwarding    │
│  - Draft review     │    - Quick actions               │    - Auto-process  │
│  - Settings         │    - Voice commands              │                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY (FastAPI)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  • JWT Authentication with refresh tokens                                    │
│  • Rate limiting: 100 req/min per tenant                                    │
│  • Request validation & sanitization                                         │
│  • Audit logging for all actions                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TASK CLASSIFICATION LAYER                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  Model: Claude 3 Haiku (fast, cheap, accurate)                              │
│                                                                              │
│  Input: "Schedule a 30-min call with Sarah next Tuesday"                    │
│  Output: {                                                                   │
│    "task_type": "calendar_scheduling",                                      │
│    "entities": {                                                             │
│      "contact": "Sarah",                                                     │
│      "duration": 30,                                                         │
│      "timeframe": "next Tuesday"                                             │
│    },                                                                        │
│    "priority": "medium",                                                     │
│    "confidence": 0.92                                                        │
│  }                                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
            ▼                         ▼                         ▼
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│  CALENDAR AGENT   │   │   EMAIL AGENT     │   │  RESEARCH AGENT   │
├───────────────────┤   ├───────────────────┤   ├───────────────────┤
│ • Google Calendar │   │ • Gmail API       │   │ • Web search      │
│ • Outlook API     │   │ • Outlook API     │   │ • Wikipedia       │
│ • FreeBusy query  │   │ • Draft creation  │   │ • Company DBs     │
│ • Slot selection  │   │ • Template engine │   │ • Summarization   │
│ • Meeting create  │   │ • Approval queue  │   │ • Citation        │
└───────────────────┘   └───────────────────┘   └───────────────────┘
            │                         │                         │
            └─────────────────────────┼─────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA & CACHING LAYER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────┐         ┌─────────────────────┐                   │
│  │     PostgreSQL      │         │       Redis         │                   │
│  ├─────────────────────┤         ├─────────────────────┤                   │
│  │ • User accounts     │         │ • Session cache     │                   │
│  │ • Preferences       │         │ • Response cache    │                   │
│  │ • Email drafts      │         │ • Rate limit counters│                  │
│  │ • Task history      │         │ • Queue management  │                   │
│  │ • Audit logs        │         │ • Real-time state   │                   │
│  └─────────────────────┘         └─────────────────────┘                   │
│                                                                              │
│  ┌─────────────────────┐         ┌─────────────────────┐                   │
│  │   Vector Store      │         │   Message Queue     │                   │
│  │   (Chroma/Pinecone) │         │   (RabbitMQ/SQS)    │                   │
│  ├─────────────────────┤         ├─────────────────────┤                   │
│  │ • Knowledge base    │         │ • Async processing  │                   │
│  │ • User preferences  │         │ • Email monitoring  │                   │
│  │ • Company policies  │         │ • Webhook handling  │                   │
│  └─────────────────────┘         └─────────────────────┘                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. Task Classification Layer
- **Model**: Claude 3 Haiku ($0.00025/request)
- **Latency**: <100ms average
- **Accuracy**: 95%+ on common intents
- **Fallback**: Rule-based classifier for edge cases

### 2. Calendar Agent
- **OAuth 2.0** for Google Calendar & Outlook
- **FreeBusy API** for availability detection
- **Preference-aware** slot selection (business hours, buffer time)
- **Conflict resolution** with user confirmation

### 3. Email Agent
- **Template-based** drafting with LLM customization
- **Approval workflow** - never auto-sends by default
- **Confidence scoring** for draft quality
- **Profanity filter** and recipient whitelist

### 4. Research Agent
- **Web search** via Serper API
- **Wikipedia** for factual queries
- **Company knowledge base** integration
- **Citation** for all sources

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SECURITY LAYERS                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Layer 1: Authentication                                         │
│  • JWT tokens with 15-min expiry                                 │
│  • Refresh tokens with 7-day expiry                              │
│  • OAuth 2.0 for Gmail/Outlook connections                       │
│                                                                  │
│  Layer 2: Authorization                                          │
│  • Role-based access control (RBAC)                              │
│  • Tenant isolation via row-level security                       │
│  • API key scoping for integrations                              │
│                                                                  │
│  Layer 3: Data Protection                                        │
│  • Fernet encryption for OAuth tokens                            │
│  • TLS 1.3 for all communications                                │
│  • PII redaction in logs                                         │
│                                                                  │
│  Layer 4: Rate Limiting                                          │
│  • 100 requests/min per tenant                                   │
│  • 10 AI actions/min per user                                    │
│  • Burst allowance for peak usage                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## MVP Timeline (9 Weeks)

| Phase | Week | Deliverables |
|-------|------|--------------|
| **Core Secretary** | 1-2 | Gmail OAuth, email fetching, task classification |
| | 3 | Calendar API integration, availability detection |
| | 4 | Email drafting, review UI, sending |
| **Multi-Tenant SaaS** | 5 | User registration, authentication, tenant isolation |
| | 6 | Stripe billing, usage tracking |
| | 7 | Admin dashboard, analytics |
| **Polish & Launch** | 8 | Security audit, performance optimization |
| | 9 | Beta testing, bug fixes, launch |

---

## Cost Estimates

### Infrastructure (Monthly)
| Component | Cost |
|-----------|------|
| Cloud Hosting (AWS/GCP) | $100-300 |
| PostgreSQL (Managed) | $50-150 |
| Redis (Managed) | $30-100 |
| Vector Store | $20-50 |
| **Total** | **$200-600/month** |

### LLM Costs (Per 1000 users)
| Usage | Cost |
|-------|------|
| Task Classification | $25/month |
| Email Drafting | $50/month |
| Research Queries | $25/month |
| **Total** | **$100/month** |

---

## Pricing Tiers

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0 | 50 AI actions/month, 1 email account |
| **Pro** | $19/mo | 500 actions, 3 accounts, advanced preferences |
| **Team** | $49/user/mo | Unlimited, shared scheduling, Slack integration |
| **Enterprise** | Custom | On-premise, SSO, custom training |

---

## Next Steps

1. **Technical Deep-Dive**: Review specific implementation details
2. **UI/UX Discussion**: Align on design system and user flows
3. **Timeline Confirmation**: Confirm 9-week MVP works for your launch date
4. **Contract Terms**: Discuss hourly vs fixed-price engagement

---

**Prepared by**: Cayman Roden  
**Email**: caymanroden@gmail.com  
**Phone**: (310) 982-0492  
**GitHub**: github.com/ChunkyTortoise  
**LinkedIn**: linkedin.com/in/caymanroden
