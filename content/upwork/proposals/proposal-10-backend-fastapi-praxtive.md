Proposal 10: Backend Developer (FastAPI / Python) — PraxtiveMD

Job: Backend Developer (FastAPI / Python) — Contract to Hire
Bid: $70/hr | Fit: 8/10 | Connects: 12-16
Status: Ready to submit

---

Cover Letter:

A HIPAA-compliant EHR platform needs backend engineering that treats security and compliance as design constraints from day one, not things you bolt on later. That's how I build everything.

EnterpriseHub is a FastAPI platform (around 5,100 tests) handling PII-sensitive real estate data with Fernet encryption at rest, JWT authentication with 1-hour tokens, 100 req/min rate limiting, and Pydantic validation on every input boundary. The system processes financial qualification data, property valuations, and CRM conversations — same privacy rigor you'd need for medical records, just a different domain.

On the performance side, my API layer handles 4.3M tool dispatches/second with under 200ms orchestration overhead. I've architected L1/L2/L3 Redis caching that achieved 89% cost reduction and 88% cache hit rate in production. Those same patterns would be critical for reducing database load in a high-throughput EHR system where you're pulling patient records, lab results, and billing data constantly.

For PraxtiveMD specifically, I'd focus on HIPAA-compliant data architecture (encrypted PII fields, audit logging, access controls), async patterns for labs/billing processing and WebSocket support for secure messaging, test-driven development with 80%+ coverage (my repos average 90%+), and P50/P95/P99 latency tracking with database query optimization.

I'm available 30+ hours/week and can start this week. 20+ years of software engineering, production deployments managing $50M+ pipelines. Happy to discuss the architecture in more detail.

Portfolio: https://chunkytortoise.github.io
GitHub: https://github.com/ChunkyTortoise
