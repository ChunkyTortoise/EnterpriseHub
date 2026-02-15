Proposal 12: AI Agent Developer — Claude API / MCP Integration for MSP Operations

Job: AI Agent Developer — Claude API / MCP Integration for MSP Operations (ServiceNow, Azure, M365)
Bid: $100/hr | Fit: 10/10 | Connects: 26
Status: Submitting

---

Cover Letter:

This is literally what I do every day. I have 5 MCP servers running in production right now (memory, postgres, redis, stripe, playwright) and 22 custom Claude Code agents handling everything from security audits to database migrations to multi-agent orchestration. Not prototypes, production systems with 8,500+ tests across the portfolio.

My main platform (EnterpriseHub) runs 3 autonomous AI bots that qualify leads, route conversations, and hand off between each other using confidence thresholds. The handoff service alone has 196 passing tests covering circular prevention, rate limiting (3/hr, 10/day per contact), conflict resolution with contact-level locking, and pattern learning that adjusts thresholds from outcome history. The orchestration layer handles 4.3M tool dispatches/second with under 200ms overhead.

For the ServiceNow triage agent specifically, I'd approach it the same way I built my intent decoder system. Classify the ticket using structured extraction (category, urgency, affected service), route based on confidence scores with fallback escalation paths, and have the agent take actions through MCP connectors to ServiceNow's REST API. I've already built the pattern for autonomous agents that take real actions in live systems with proper guardrails (approval gates above certain confidence thresholds, audit logging on every action, rollback capability).

I haven't worked directly with ServiceNow APIs, but I've integrated with GoHighLevel CRM (OAuth 2.0, webhooks, rate limiting, custom field syncing) and Stripe billing, which are similar REST API patterns. The Azure/M365 side I can pick up quickly since my stack already runs on cloud infrastructure with Docker and CI/CD pipelines.

I'm available 30+ hours/week and can start immediately. 20+ years of software engineering. Happy to walk through my MCP server implementations on a call.

Portfolio: https://chunkytortoise.github.io
GitHub: https://github.com/ChunkyTortoise

---

Screening Questions:

Q1: Describe your hands-on experience using the Anthropic Claude API. Include which Claude models you have used.
A1: I use the Claude API daily through Claude Code with Opus 4.6 as my primary model. My platform uses Claude for multi-turn conversation orchestration across 3 autonomous bots (lead qualifier, buyer bot, seller bot). The orchestrator handles multi-strategy response parsing, L1/L2/L3 caching that cut API costs by 89%, and structured extraction for intent analysis. I've also used Sonnet and Haiku for different workload tiers based on complexity vs cost trade-offs. The whole system has around 5,100 tests.

Q2: Have you built or worked with Model Context Protocol (MCP) servers or connectors? If yes, describe the setup.
A2: Yes, I run 5 MCP servers in production right now: memory (knowledge graph persistence), postgres (direct database queries), redis (cache inspection), stripe (billing management), and playwright (browser automation/E2E testing). I've also configured 22 custom Claude Code agents that leverage these MCP servers for specialized tasks like architecture analysis, security auditing, performance optimization, and multi-agent coordination. The agents use MCP tools to read databases, manage caches, process payments, and automate browser interactions.

Q3: Describe an autonomous AI agent you have built that took real actions in a live system. What actions did it take?
A3: My Jorge bot system runs 3 autonomous agents that take real actions in GoHighLevel CRM. The lead qualifier bot analyzes conversations and publishes temperature tags (Hot/Warm/Cold) that trigger CRM workflows and agent notifications. When confidence exceeds 0.7, the handoff service autonomously transfers contacts between bots, syncs custom fields (financial readiness scores, budget data), and updates conversation routing. The system handles rate limiting, circular prevention, and conflict resolution with contact-level locking. The buyer bot can evaluate financial readiness and trigger calendar booking for qualified leads. All of this runs without human intervention.

Q4: What is your experience integrating with ServiceNow APIs? If you have not worked with ServiceNow, describe a comparable enterprise API integration.
A4: I haven't integrated directly with ServiceNow, but I've built a production GoHighLevel CRM integration that covers the same patterns: OAuth 2.0 with automatic token refresh, 10 req/sec rate limiting with exponential backoff, webhook processing for real-time event updates, bidirectional data syncing (contacts, conversations, custom fields), and a setup validation script that verifies all custom fields, workflows, and calendar IDs exist before deployment. I've also integrated with Stripe for billing management. The patterns (REST API, auth, rate limiting, error handling, audit logging) are the same across enterprise APIs.

Q5: Explain how you would approach building a Service Desk Triage Agent that classifies, routes, and recommends actions.
A5: I'd model it after my intent decoder + handoff system. First, build a classification layer that extracts structured data from the ticket (category, urgency, affected systems, user impact) using Claude's structured output. Then a routing engine with confidence-based thresholds. Tickets above 0.8 confidence get auto-routed to the right team. Between 0.5-0.8, the agent suggests a route but flags for human review. Below 0.5, escalate to a human. For recommended actions, the agent would check a knowledge base of past resolutions (similar to my RAG pipeline) and suggest playbook steps. All actions go through MCP connectors to ServiceNow with audit logging. I'd add pattern learning that adjusts routing thresholds based on outcome data, same approach I use in my handoff service where thresholds adapt after minimum 10 data points.
