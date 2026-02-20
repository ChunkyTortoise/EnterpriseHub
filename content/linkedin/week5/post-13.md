# LinkedIn Post #13 — CRM Integrations + Abstract Base Class Pattern

**Publish Date**: Monday, March 10, 2026 @ 8:30am PT
**Topic**: Portfolio Showcase — Lessons Learned
**Goal**: Demonstrate enterprise integration expertise, showcase architectural patterns that reduce complexity, attract CRM/SaaS engineers and tech leads

---

## Post Content

Five CRM integrations. One abstract base class. Zero rewrites.

When I started building CRM integrations for EnterpriseHub, I made the same mistake everyone makes: I wrote the GoHighLevel adapter first, got it working, then started on HubSpot.

Halfway through HubSpot, I realized I was copy-pasting rate limiting logic, retry handling, and webhook parsing. By the time I'd need Salesforce, I'd have three adapters that were 60% identical and 100% painful to maintain.

So I stopped and built the pattern first.

**The Abstract Base Class CRM protocol.**

Every CRM adapter in EnterpriseHub implements the same interface:

```python
class CRMAdapter(ABC):
    @abstractmethod
    async def sync_contact(self, contact: Contact) -> SyncResult: ...

    @abstractmethod
    async def process_webhook(self, payload: dict) -> WebhookEvent: ...

    @abstractmethod
    async def get_rate_limit(self) -> RateLimitConfig: ...
```

Three methods. That's the contract. Everything else — authentication, field mapping, pagination — lives in the concrete adapter. But the orchestration layer never knows or cares which CRM it's talking to.

**Why this matters in practice:**

**1. Adding a new CRM is a bounded problem.**

When I built the Salesforce OAuth adapter, I didn't touch the orchestration layer, the webhook router, or the sync scheduler. I wrote one class, implemented three methods, wrote tests against the shared test suite, and plugged it in.

Total time from "start Salesforce adapter" to "passing all integration tests": two days. The first adapter (GoHighLevel) took two weeks.

**2. Rate limiting is per-provider but the pattern is universal.**

GoHighLevel enforces 10 requests per second. HubSpot has different limits per endpoint. Salesforce has daily API call quotas.

Each adapter returns its own `RateLimitConfig`, and the shared rate limiter handles the rest. One rate limiter implementation. Five different rate limit configurations. Zero duplicated throttling logic.

**3. Testing is multiplicative, not additive.**

I have a shared test suite that runs against every adapter. Contact sync, webhook parsing, error handling, rate limit compliance — every adapter gets the same 40+ test cases automatically. Adapter-specific tests (like GHL's temperature tag publishing or Salesforce's OAuth refresh flow) layer on top.

The result: 80%+ coverage on every adapter without writing 80% of the tests five times.

**The five adapters today:**

- GoHighLevel: 10 req/s rate limit, webhook handlers, temperature tags, calendar booking
- HubSpot: Contact sync, deal pipeline mapping, engagement tracking
- HubSpot Extended: Custom object sync, workflow triggers, advanced field mapping
- Salesforce: OAuth 2.0 flow, bulk API support, field-level security
- Salesforce OAuth: Token refresh, connected app management, sandbox support

**What I'd do differently:**

I'd build the abstract base class before writing a single adapter. The pattern was obvious in hindsight — every CRM does contacts, webhooks, and rate limits. Starting with the contract would have saved the two weeks I spent refactoring GHL from a one-off into a proper adapter.

Code is live: github.com/ChunkyTortoise

**What's the most painful CRM integration you've dealt with?**

#CRM #APIIntegration #Python #SoftwareArchitecture #DesignPatterns

---

## Engagement Strategy

**CTA**: Experience-sharing question targeting integration engineers
**Expected Replies**: 60-80 (CRM pain is universal, engineers love sharing war stories about API inconsistencies)
**Response Time**: <1 hour for all comments

**Prepared Responses**:

**Q: "Why not use an integration platform like Zapier or Make instead of custom adapters?"**
A: For simple field syncing, Zapier is great. But EnterpriseHub needs real-time bidirectional sync with custom business logic — like updating a lead temperature tag based on conversation sentiment, then triggering a GHL workflow based on the new temperature. That kind of conditional, stateful integration exceeds what no-code platforms handle reliably. The ABC pattern gives me Zapier-level speed for adding new CRMs with full-code flexibility for business logic.

**Q: "How do you handle schema differences between CRMs? A HubSpot contact looks nothing like a Salesforce lead."**
A: Each adapter owns its own field mapping. The abstract interface uses a canonical `Contact` model — our internal representation. The HubSpot adapter maps `firstname` + `lastname` to our `full_name`. The Salesforce adapter maps `Name` to the same field. The mapping logic is in the adapter, not the orchestration layer. When a CRM adds or changes fields, only one adapter needs updating.

**Q: "What happens when a CRM API changes without warning?"**
A: This is exactly why I test at 80%+ coverage. GHL changed their webhook payload format last month — no announcement, no deprecation notice. Our CI caught it within hours because the webhook parsing tests started failing. Fix was a 3-line change in the GHL adapter. Zero impact on the other four adapters. That's the power of the pattern: blast radius is always contained to one adapter.

**Q: "Does the ABC pattern work for CRMs with fundamentally different architectures?"**
A: The key is keeping the interface minimal. Three methods is intentionally small. If I'd put `search_contacts()` or `create_deal()` in the base class, I'd be forcing every adapter to implement features their CRM might not support natively. Instead, those are optional methods that adapters implement via mixins. The base contract covers what every CRM does. Everything else is opt-in.

---

## Follow-Up Actions

- [ ] 8:30am PT: Publish post
- [ ] 8:35am: Comment on 5 CRM integration / API design posts
- [ ] Throughout day: Reply to all comments within 1 hour
- [ ] Send 5 connection requests to engaged commenters (target: integration engineers, CRM developers, SaaS architects)
- [ ] Track metrics: impressions, engagement rate, GitHub clicks
