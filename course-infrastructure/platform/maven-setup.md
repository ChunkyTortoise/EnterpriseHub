# Maven Course Setup Guide

Step-by-step guide for creating and configuring the course on Maven.

## Course Creation

### Step 1: Create Course on Maven

1. Log in to [maven.com/instructor](https://maven.com/instructor)
2. Click **Create New Course**
3. Fill in the following fields:

**Course Title**: Production AI Systems: Build & Ship 5 SaaS Products

**Subtitle**: Learn to build, test, and deploy production-grade AI systems using real repositories with 8,500+ tests. Ship 5 working products in 6 weeks.

**Category**: Engineering & Technology > Software Engineering

**Tags**: AI, Machine Learning, Python, RAG, MCP, Production Systems, SaaS, DevOps

### Step 2: Course Description

Use the following copy for the Maven listing:

---

**Who is this for?**

Mid-to-senior software engineers (2+ years experience) who want to move beyond AI demos and build production-grade AI systems. You should be comfortable with Python, REST APIs, and basic SQL.

**What you'll build:**

Over 6 weeks, you will build and ship 5 working AI products using battle-tested open-source repositories:

1. **Multi-Agent System** (AgentForge) — Tool-using agents with structured output and memory
2. **Document Q&A Engine** (DocQA) — RAG pipeline with hybrid BM25 + vector search and evaluation
3. **MCP Servers** (MCP Server Toolkit) — Custom tool integration via Model Context Protocol
4. **AI Orchestration Platform** (EnterpriseHub) — Production hardening with caching, rate limiting, and CRM integration
5. **BI Dashboard** (Insight Engine) — Observability, anomaly detection, and business intelligence

**What makes this different:**

- You work with real production code (8,500+ tests, not toy examples)
- Every repo has CI/CD, Docker, and monitoring already configured
- The instructor has managed a $50M+ pipeline using these exact systems
- You deploy to real infrastructure, not just localhost

---

### Step 3: Pricing Configuration

| Tier | Maven Price | Description |
|------|------------|-------------|
| Beta (Cohort 1 only) | $797 | All 12 sessions, Discord community, 6 labs, certificate of completion |
| Standard | $1,297 | Everything in Beta + 1 private office hour session (30 min) |
| Premium | $1,997 | Everything in Standard + 3 private 1:1 code review sessions + LinkedIn recommendation |

**Enrollment settings:**
- Minimum enrollment: 10 students
- Maximum enrollment: 35 students
- Early bird discount: $797 beta price for first 20 enrollees
- Refund policy: Full refund within 7 days of course start if attended fewer than 2 sessions

### Step 4: Schedule Configuration

**Cohort 1 Timeline:**

| Item | Date |
|------|------|
| Waitlist opens | 4 weeks before start |
| Enrollment opens | 3 weeks before start |
| Early bird closes | 2 weeks before start |
| Enrollment closes | 1 day before start |
| Course start | Target: Q2 2026 |
| Course end | 6 weeks after start |

**Session Schedule:**

| Day | Time | Duration | Type |
|-----|------|----------|------|
| Tuesday | 6:00 PM PT / 9:00 PM ET | 90 min | Concept + Live Coding |
| Thursday | 6:00 PM PT / 9:00 PM ET | 90 min | Lab Review + Deep Dive |

**Session Format:**

Session A (Tuesday):
- 15 min: Concept introduction with architecture diagrams
- 45 min: Live coding walkthrough using actual repo code
- 15 min: Lab assignment introduction and setup verification
- 15 min: Q&A

Session B (Thursday):
- 20 min: Lab solution review (common patterns and mistakes)
- 40 min: Advanced topic deep-dive
- 20 min: Guest speaker or production case study
- 10 min: Next week preview

### Step 5: Instructor Profile

**Display Name**: Cave

**Bio**: Production AI engineer with 11 open-source repositories, 8,500+ automated tests, and systems managing a $50M+ real estate pipeline. Specializes in AI agent orchestration, RAG systems, and MCP integration. Built production systems achieving 89% cost reduction and 4.3M dispatches/sec throughput.

**Credibility Markers** (add to Maven profile):
- 8,500+ tests across 11 production repositories
- $50M+ pipeline managed with AI orchestration
- 89% cost reduction through intelligent caching
- 4.3M dispatches/sec throughput on production systems
- Open-source contributor with real deployment track records

### Step 6: Marketplace Optimization

**SEO-Optimized Title**: Production AI Systems: Build & Ship 5 SaaS Products

**Search Keywords**: production AI, RAG pipeline, MCP servers, AI agents, Python AI course, SaaS development, AI deployment, AI testing

**Marketplace Listing Tips**:
1. Lead with outcomes: "Ship 5 working AI products in 6 weeks"
2. Emphasize production quality: "Not toy demos — real code with 8,500+ tests"
3. Show social proof: Update with enrollment numbers and testimonials after Cohort 1
4. Use specific metrics: Numbers like 8,500 tests and $50M pipeline create credibility
5. Highlight the lab environment: Zero-setup Codespaces are a strong differentiator

### Step 7: Post-Course Setup

After Cohort 1 completes:
1. Export all session recordings from Zoom
2. Upload recordings to Maven as self-paced content
3. Create a $397 self-paced tier on Gumroad (see `pricing/stripe-products.md`)
4. Add testimonials and completion stats to Maven listing
5. Open Cohort 2 enrollment with updated pricing ($1,297 standard)

### Step 8: Maven Integrations

| Integration | Purpose | Setup |
|-------------|---------|-------|
| Zoom | Live sessions, breakout rooms, recordings | Connect via Maven Settings > Integrations |
| Stripe | Payment processing | Auto-configured by Maven |
| ConvertKit | Waitlist and email sequences | Webhook: Maven purchase → ConvertKit tag |
| Discord | Community access | Include invite link in post-purchase email |
