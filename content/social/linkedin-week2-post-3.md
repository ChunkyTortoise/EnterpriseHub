# LinkedIn Week 2 -- Post 3

**Schedule**: Friday, February 21, 2026, 9:00 AM PT
**Topic**: I Built 3 CRM Integrations. Here's What Nobody Tells You.
**Content Type**: Practical experience report / lessons learned

---

I've integrated with GoHighLevel, HubSpot, and Salesforce. All three in the same codebase. All three through a unified protocol.

Here are the lessons I learned the hard way so you don't have to.

**Lesson 1: Rate limits are lies.**

Every CRM API publishes a rate limit. GoHighLevel says 10 requests/second. HubSpot says 100/10 seconds. Salesforce varies by edition.

In practice, you'll hit undocumented throttling well before those limits. GoHighLevel will 429 you at 7-8 req/sec during peak hours. HubSpot's batch API has a separate, lower limit than the single-record API. Salesforce's concurrent request limit is the one that actually bites you.

What worked: exponential backoff with jitter, per-endpoint rate tracking (not per-API), and a circuit breaker that fails fast when a CRM is degraded. Our GHL client has been stable at production scale managing a $50M+ pipeline.

**Lesson 2: Webhooks are the real integration.**

REST APIs are for prototypes. Webhooks are for production. The difference in user experience is massive.

With polling: "The contact updated 3 minutes ago, but our system still shows the old data."

With webhooks: "The contact updated, and our system reflected it within 2 seconds."

But webhook reliability is your problem, not the CRM's. You need idempotency, retry queues, and dead letter handling. A dropped webhook at 2 AM shouldn't mean a lost lead.

**Lesson 3: Build the adapter pattern from day one.**

I started with a GoHighLevel-specific client. When HubSpot came along, I refactored. When Salesforce came along, I refactored again. The third time, I built a proper CRM protocol -- an abstract base class that defines the interface, with concrete adapters for each provider.

Now adding a fourth CRM is a 2-day job, not a 2-week job. The adapter pattern isn't over-engineering when you know you'll have multiple providers. It's planning.

**Lesson 4: Test with real CRM accounts, not mocks.**

CRM APIs have quirks that mocks can't replicate. HubSpot's date formats change depending on the property type. Salesforce returns different field names in bulk queries vs single-record queries. GoHighLevel's tag API has undocumented character limits.

We run integration smoke tests against sandbox accounts weekly. It catches API changes before they hit production.

The result: 3 CRM integrations, one protocol, zero context loss during handoffs between systems. It took 3 months to get right. The protocol approach would have saved 6 weeks if I'd started with it.

Building CRM integrations? What's the biggest surprise you've hit?

#CRM #SoftwareEngineering #Python #APIIntegration #GoHighLevel #HubSpot #Salesforce #FastAPI

---

**Engagement strategy**: CRM developers and agency owners are a high-value audience for consulting. This post signals deep integration experience. Respond to comments with specifics about their CRM. If GHL agency owners engage, connect and follow up with the consulting offer.
