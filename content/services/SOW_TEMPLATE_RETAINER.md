# Statement of Work: Fractional AI CTO Retainer

---

**Prepared for**: {COMPANY}
**Prepared by**: Cayman Roden
**Date**: {DATE}
**SOW Reference**: {SOW_NUMBER}
**Effective Date**: {START_DATE}
**Initial Term**: {TERM_LENGTH} months

---

## 1. Overview

This Statement of Work defines the scope, deliverables, terms, and operating procedures for a Fractional AI CTO retainer engagement with {COMPANY}. Cayman Roden will serve as a dedicated AI architecture and engineering resource, providing technical leadership, feature development, performance optimization, and strategic guidance for {COMPANY}'s AI systems.

---

## 2. Retainer Tier

| | Details |
|---|---|
| **Tier** | {TIER_NAME} |
| **Monthly Rate** | ${MONTHLY_RATE}/month |
| **Included Hours** | {HOURS_PER_MONTH} hours/month |
| **Effective Hourly Rate** | ${EFFECTIVE_RATE}/hr |
| **Billing Cycle** | Monthly in advance, net-15 |
| **Initial Term** | {TERM_LENGTH} months |

### Tier Options Reference

| Tier | Rate | Hours | Best For |
|------|------|-------|----------|
| Starter | $8,000/mo | ~50 hrs | Bug fixes, minor features, monitoring, async support |
| Growth | $12,000/mo | ~80 hrs | Feature development, optimization, weekly syncs |
| Dedicated | $15,000/mo | ~100+ hrs | Near full-time, architecture ownership, daily availability |

---

## 3. Scope of Services

### Ongoing Responsibilities

- **Architecture Ownership**: Design, maintain, and evolve the AI system architecture. Make technology decisions aligned with business objectives. Document decisions via Architecture Decision Records (ADRs).
- **Feature Development**: Build new features, integrations, and capabilities within the allocated monthly hours. All code delivered with tests, documentation, and deployment configurations.
- **Performance Monitoring**: Track P50/P95/P99 latency, cache hit rates, LLM cost trends, and SLA compliance. Identify and resolve performance regressions.
- **Code Review**: Review all AI-related pull requests for quality, security, architectural consistency, and test coverage.
- **Incident Response**: Priority response for production issues affecting AI systems during business hours.
- **Team Mentoring**: Guide junior developers on AI engineering patterns, code quality, and testing practices.

### Monthly Deliverables

| Deliverable | Frequency | Description |
|-------------|-----------|-------------|
| Performance Report | Monthly | P50/P95/P99 latency trends, cache metrics, LLM costs, SLA status |
| Sprint Summary | Bi-weekly (Growth/Dedicated) | Completed work, in-progress items, blockers, upcoming priorities |
| Architecture Updates | As needed | ADRs for significant technical decisions |
| Code Contributions | Ongoing | Feature branches with tests, documentation, and CI passing |
| Strategic Roadmap | Quarterly | Technology roadmap aligned with business objectives |

### Communication Cadence

| Tier | Sync Meetings | Async Response | Availability |
|------|--------------|----------------|--------------|
| Starter | Monthly strategy call | < 4 hours (business hours) | Business hours PT |
| Growth | Weekly sync + monthly strategy | < 4 hours (business hours) | Business hours PT |
| Dedicated | Daily standup + weekly sync | < 2 hours (business hours) | Extended hours PT |

Business hours: 9:00 AM - 6:00 PM Pacific Time, Monday through Friday.

---

## 4. Hour Tracking and Rollover

### Tracking

- Hours are tracked in 15-minute increments.
- A shared time tracking report is available to {COMPANY} at all times.
- Time is tracked for: development, code review, meetings, research, documentation, and incident response.
- Time is not tracked for: invoicing, scheduling, or brief Slack exchanges under 5 minutes.

### Rollover Policy

- Up to **10 unused hours** may roll over to the following month.
- Rollover hours expire if not used in the following month (no multi-month accumulation).
- Rollover hours are used first before current-month hours.

### Overage

- If the monthly allocation is exhausted, additional hours are available at **$175/hr** (Priority rate).
- Overage must be pre-approved by {COMPANY} before work begins.
- Overage is invoiced at the end of the month with the next billing cycle.

---

## 5. Escalation Process

### Priority Levels

| Level | Definition | Response Time | Resolution Target |
|-------|-----------|---------------|-------------------|
| **P0 -- Critical** | Production system down, data loss, or security breach | < 1 hour | Same business day |
| **P1 -- High** | Major feature broken, significant performance degradation | < 4 hours | 1 business day |
| **P2 -- Medium** | Minor feature issue, non-critical bug | < 8 hours | 3 business days |
| **P3 -- Low** | Enhancement request, minor improvement | Next sprint | As scheduled |

### Escalation Path

1. **Primary channel**: Slack direct message or designated channel.
2. **If no response within SLA**: Email to caymanroden@gmail.com with "URGENT: {COMPANY}" in subject.
3. **If no response within 2x SLA**: Phone call to (310) 982-0492.

### After-Hours Policy

- P0 incidents outside business hours: Best-effort response via phone/text. After-hours work billed at 1.5x the effective hourly rate.
- P1-P3 outside business hours: Acknowledged within 1 hour of next business day.

---

## 6. Pricing and Payment

### Monthly Invoice

| Item | Amount |
|------|--------|
| {TIER_NAME} Retainer ({HOURS_PER_MONTH} hours) | ${MONTHLY_RATE} |
| Overage hours (if applicable) | $175/hr x {OVERAGE_HOURS} |
| **Monthly Total** | **${MONTHLY_TOTAL}** |

### Payment Terms

- Invoiced on the 1st of each month for the upcoming month.
- Payment due net-15 from invoice date.
- Accepted payment methods: ACH bank transfer, credit card.
- Late payments accrue interest at 1.5% per month.
- Two consecutive late payments constitute grounds for immediate termination.

### Rate Adjustments

- Rates are fixed for the initial term ({TERM_LENGTH} months).
- Rate adjustments for subsequent terms will be proposed 60 days before term renewal, not to exceed 10% annually.

---

## 7. Term and Termination

### Initial Term

This agreement begins on {START_DATE} and continues for {TERM_LENGTH} months, automatically renewing for successive {RENEWAL_LENGTH}-month terms unless terminated.

### Termination

- Either party may terminate with **30 days written notice**.
- Upon termination, Cayman Roden will:
  - Complete any in-progress work up to the termination date.
  - Provide all code, documentation, and credentials in a structured handoff.
  - Conduct a 60-minute knowledge transfer session covering system state, pending items, and maintenance notes.
  - Return or destroy any {COMPANY} confidential information within 10 business days.
- {COMPANY} is responsible for payment through the end of the notice period.
- No refunds for unused hours in the final month.

### Termination for Cause

Either party may terminate immediately if the other party:
- Materially breaches this SOW and fails to cure within 10 business days of written notice.
- Becomes insolvent or files for bankruptcy.

---

## 8. Intellectual Property

- All custom code, documentation, and configurations produced under this retainer become the property of {COMPANY}.
- Open-source libraries and frameworks retain their original licenses.
- Generic patterns, methodologies, and non-client-specific utilities remain the property of Cayman Roden and may be reused.
- Cayman Roden retains the right to reference {COMPANY} as a client in marketing materials unless {COMPANY} objects in writing.

---

## 9. Confidentiality

Both parties agree to maintain the confidentiality of all proprietary information for the duration of this agreement and **2 years** following termination. This includes source code, business data, API credentials, customer information, strategic plans, and financial data.

---

## 10. Limitation of Liability

Cayman Roden's total liability under this SOW shall not exceed the total fees paid during the 3-month period preceding the claim. Neither party shall be liable for indirect, incidental, or consequential damages.

---

## 11. Assumptions

1. {COMPANY} will provide timely access to all systems, repositories, and environments needed to perform the work.
2. {COMPANY} will designate a primary point of contact who is authorized to approve priorities, provide feedback, and make decisions.
3. Milestone reviews and priority approvals will be completed within 2 business days.
4. {COMPANY} is responsible for all third-party service costs (cloud hosting, LLM APIs, CRM subscriptions).
5. Work will be performed remotely from Palm Springs, CA.
6. All communication will be in English via Slack, email, or video call.

---

## 12. Signatures

**Cayman Roden** (Service Provider)

Signature: _________________________

Name: Cayman Roden

Date: _________________________

---

**{COMPANY}** (Client)

Signature: _________________________

Name: {CLIENT_NAME}

Title: {CLIENT_TITLE}

Date: _________________________

---

*This SOW is subject to the terms above. The retainer begins on the effective date upon execution by both parties and receipt of the first monthly payment.*
