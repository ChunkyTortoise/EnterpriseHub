# ADR 0002: Multi-CRM Protocol Pattern

## Status

Accepted

## Context

The platform initially targeted GoHighLevel (GHL) as the sole CRM integration. However, real estate teams frequently use HubSpot or Salesforce depending on brokerage size and existing infrastructure. Supporting multiple CRMs with direct API calls would lead to conditional branching throughout the codebase, making each new integration exponentially harder to maintain.

Key requirements:
- Contact sync (create, update, tag) must work identically regardless of CRM
- Lead temperature tags (Hot/Warm/Cold) must map to each CRM's tagging system
- Webhook ingestion must normalize events from different CRM formats
- Rate limiting differs per CRM (GHL: 10 req/s, HubSpot: 100 req/10s, Salesforce: varies by edition)

## Decision

Define a `CRMProtocol` abstract base class that establishes the contract for all CRM interactions. Each CRM implements this interface through an adapter class:

```
CRMProtocol (ABC)
  |-- GHLAdapter        (~400 lines, production)
  |-- HubSpotAdapter    (~350 lines, production)
  |-- SalesforceAdapter  (~300 lines, beta)
```

The adapter pattern encapsulates:
- Authentication (OAuth2 for HubSpot/Salesforce, API key for GHL)
- Rate limiting (per-CRM token bucket implementation)
- Field mapping (each CRM's contact schema to our unified `LeadContact` model)
- Webhook normalization (different event formats to unified `CRMEvent` schema)

CRM selection is configured per-tenant via environment variable or database setting, with dependency injection providing the correct adapter at request time.

## Consequences

### Positive
- Adding a 4th CRM (e.g., Follow Up Boss, kvCORE) requires only a new adapter class (~200-400 lines) with no changes to business logic
- All bot services, handoff logic, and analytics work identically regardless of underlying CRM
- Testing is simplified: mock the protocol interface once, test business logic independently
- Per-CRM rate limiting is isolated, preventing one CRM's limits from affecting others

### Negative
- Protocol evolution requires updating all adapters simultaneously (e.g., adding a new method to `CRMProtocol`)
- Lowest-common-denominator risk: advanced CRM-specific features may not fit the unified interface
- Field mapping maintenance: CRM API changes require adapter updates
- Three separate OAuth token refresh cycles to manage in production
