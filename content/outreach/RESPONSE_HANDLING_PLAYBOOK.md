# Cold Outreach Response Handling Playbook

## Overview
This playbook provides structured responses to common scenarios when conducting cold outreach campaigns. Use these templates as starting points and personalize for each interaction.

---

## Response Categories

### 1. Positive Interest
### 2. Questions / Objections
### 3. Not Right Now / Timing
### 4. Not Interested / Unsubscribe
### 5. Automated Replies
### 6. Meeting Follow-Up

---

## 1. Positive Interest Responses

### Scenario 1A: "This looks interesting, can we schedule a call?"

**Your Response:**

```
Subject: Re: [Original Subject]

Hi {{first_name}},

Excellent! I'd love to walk you through how this applies to {{company}}'s use case.

I have availability this week:
- Tuesday 2/11, 10 AM or 2 PM PT
- Wednesday 2/12, 11 AM or 3 PM PT
- Thursday 2/13, 9 AM or 1 PM PT

Does any of those work? If not, feel free to grab time directly: [calendly_link]

In the meantime, here's a quick 5-minute walkthrough you can review async: [demo_link]

Looking forward to connecting!

Best,
{{your_name}}
```

**Next Actions:**
- [ ] Update CRM status to "Meeting Booked"
- [ ] Send calendar invite immediately after confirmation
- [ ] Prepare custom demo based on their company's use case
- [ ] Research company deeply (recent news, team, tech stack)
- [ ] Set reminder to send meeting prep email 24 hours before call

---

### Scenario 1B: "Can you send more information?"

**Your Response:**

```
Subject: Re: [Original Subject] - Additional Details

Hi {{first_name}},

Absolutely! Here's a breakdown of what we offer:

**What We Built:**
{{customized_description_based_on_their_needs}}

**How It Works:**
1. {{step_1}}
2. {{step_2}}
3. {{step_3}}

**Live Demos:**
- {{demo_1_name}}: {{demo_1_url}}
- {{demo_2_name}}: {{demo_2_url}}
- {{demo_3_name}}: {{demo_3_url}}

**Pricing:**
- Custom AI frameworks: $300-$8,000 (one-time)
- Monthly retainer: $2,500-$8,000/month
- Hourly consulting: $150-$250/hour

**Portfolio:** https://chunkytortoise.github.io

Happy to answer any specific questions or set up a quick call if easier. What would be most helpful for you?

Best,
{{your_name}}
```

**Next Actions:**
- [ ] Update CRM status to "Engaged"
- [ ] Set follow-up reminder for 2 days
- [ ] Track if they click demo links (shows engagement)
- [ ] Prepare to answer technical questions

---

### Scenario 1C: "We're interested but need to discuss internally"

**Your Response:**

```
Subject: Re: [Original Subject]

Hi {{first_name}},

That's great to hear! To help your internal discussion, I can provide:

**Option A:** A custom 1-page overview tailored to {{company}}'s specific use case (I can have this to you by tomorrow)

**Option B:** A 15-minute recorded Loom walkthrough addressing your team's specific questions

**Option C:** A live demo for your team (30 minutes, I'll walk through everything and answer questions in real-time)

Which would be most helpful for your decision-making process?

Also, are there specific concerns or questions I should address in the materials? (e.g., scalability, integration with existing systems, pricing, timeline, etc.)

Best,
{{your_name}}
```

**Next Actions:**
- [ ] Update CRM status to "Proposal Stage"
- [ ] Create custom 1-pager if requested
- [ ] Record custom Loom if requested
- [ ] Schedule team demo if requested
- [ ] Follow up in 3 days if no response

---

## 2. Questions / Objections

### Scenario 2A: "What's your pricing?"

**Your Response:**

```
Subject: Re: [Original Subject] - Pricing Details

Hi {{first_name}},

Great question! Pricing depends on scope and engagement model. Here's our structure:

**Custom AI Framework Development:**
- Simple integration: $300-$2,000
- Medium complexity (RAG pipeline, chatbot): $2,000-$5,000
- Complex multi-agent system: $5,000-$8,000

**Monthly Retainer (Ongoing Support):**
- Part-time (10-20 hrs/mo): $2,500-$5,000/month
- Full-time equivalent (40 hrs/mo): $8,000/month

**Hourly Consulting:**
- Strategy/architecture: $200-$250/hour
- Implementation: $150-$200/hour

**What's Included:**
✓ Production-ready code with comprehensive tests
✓ Live demo deployment
✓ Documentation and handoff
✓ 30-day post-launch support

For {{company}}, I'd estimate {{customized_estimate}} based on {{their_specific_needs}}.

Would a quick call help narrow down the right engagement model for your needs?

Best,
{{your_name}}
```

**Next Actions:**
- [ ] Update CRM with "Pricing Question" tag
- [ ] Prepare custom quote if they have specific requirements
- [ ] Set follow-up for 2 days

---

### Scenario 2B: "We already have an AI solution / vendor"

**Your Response:**

```
Subject: Re: [Original Subject]

Hi {{first_name}},

That's great that you're already working on AI! I'm curious - are you seeing any gaps or challenges with your current setup?

Common scenarios where we've helped companies with existing AI solutions:

**Scenario 1: Performance Optimization**
Existing system works but is too slow or expensive to scale
→ We optimize latency, reduce token costs, improve caching

**Scenario 2: Feature Gaps**
Current vendor doesn't support specific use cases you need
→ We build custom modules that integrate with existing systems

**Scenario 3: Capacity Constraints**
In-house team is maxed out, need external capacity
→ We augment your team on specific projects or ongoing basis

**Scenario 4: Second Opinion**
Want expert review of architecture or implementation
→ We provide code reviews, architecture audits, recommendations

Does any of that resonate with {{company}}'s situation? No pressure either way - just want to make sure I'm not wasting your time if we're not a fit!

Best,
{{your_name}}
```

**Next Actions:**
- [ ] Update CRM with "Existing Vendor" objection tag
- [ ] If they engage, position as complement not replacement
- [ ] If no response, move to nurture sequence

---

### Scenario 2C: "Can you provide references / case studies?"

**Your Response:**

```
Subject: Re: [Original Subject] - Portfolio & References

Hi {{first_name}},

Absolutely! Here's my track record:

**Live Production Systems:**
All 11 repos include live Streamlit demos (not prototypes - real production code):

1. **EnterpriseHub** (Real Estate AI Platform)
   - Multi-bot orchestration, CRM integration, BI dashboards
   - 4,937 automated tests, <200ms latency
   - Live demo: {{enterprisehub_url}}

2. **DocQA Engine** (RAG Document Analysis)
   - BM25 + TF-IDF hybrid retrieval, citation scoring
   - 322 tests covering edge cases
   - Live demo: {{docqa_url}}

3. **AgentForge** (AI Orchestration Framework)
   - Tool routing, tracing, flow visualization
   - 214 tests
   - Live demo: {{agentforge_url}}

4. **Insight Engine** (Predictive Analytics)
   - Forecasting, clustering, ML pipeline
   - 313 tests
   - Live demo: {{insight_url}}

5. **Prompt Engineering Lab**
   - Template optimization, A/B testing, token analysis
   - 168 tests
   - Live demo: {{prompt_url}}

**Full Portfolio:** https://chunkytortoise.github.io

**Client References:**
I'm currently freelancing (no FTE clients yet), but happy to provide:
- Code review from technical evaluators
- GitHub repos with commit history showing production quality
- Live demos you can test immediately

For {{company}}'s specific use case ({{their_use_case}}), the most relevant project would be {{most_relevant_project}}.

Would a 15-minute walkthrough of that project be helpful?

Best,
{{your_name}}
```

**Next Actions:**
- [ ] Update CRM with "References Requested" tag
- [ ] Prepare custom case study for their industry if needed
- [ ] Offer to connect them with anyone who's reviewed your code

---

### Scenario 2D: "We don't have budget right now"

**Your Response:**

```
Subject: Re: [Original Subject]

Hi {{first_name}},

Totally understand - budget cycles can be tricky. A few options:

**Option 1: Start Small**
Pilot project for $300-$2,000 to prove value before committing to larger engagement. If it works, we scale. If not, minimal risk.

**Option 2: Deferred Payment**
We can structure payments around milestones or defer until next budget cycle.

**Option 3: Hourly Basis**
Instead of retainer, work on hourly basis ($150-$250/hr) so you only pay for what you need.

**Option 4: Stay in Touch**
No immediate budget is totally fine! I'll add you to my quarterly newsletter (technical deep-dives, not sales spam). When budget opens up, you'll know how to reach me.

What feels like the best fit for {{company}}'s situation?

Best,
{{your_name}}
```

**Next Actions:**
- [ ] Update CRM with "Budget Constraint" tag
- [ ] Add to nurture sequence (quarterly check-ins)
- [ ] Note when their budget cycle likely resets (often Q1, Q3)

---

## 3. Not Right Now / Timing Responses

### Scenario 3A: "Interesting, but not the right time - check back in X months"

**Your Response:**

```
Subject: Re: [Original Subject]

Hi {{first_name}},

No problem at all - timing is everything! I'll reach back out in {{timeframe}}.

Quick question before I do: when the timing IS right, what would need to be true for this to be a priority? (e.g., specific project kicked off, team capacity freed up, budget allocated, etc.)

That way when I follow up, I can make sure my timing is actually helpful vs. just annoying you! 😊

Best,
{{your_name}}
```

**Next Actions:**
- [ ] Update CRM status to "Follow-Up Scheduled"
- [ ] Set calendar reminder to reach out in {{timeframe}}
- [ ] Note trigger conditions they mentioned
- [ ] Add to nurture sequence in the meantime

---

### Scenario 3B: "We're in the middle of [project/launch/etc], reach out after"

**Your Response:**

```
Subject: Re: [Original Subject]

Hi {{first_name}},

Totally get it - {{project/launch}} is the priority right now. Good luck with that!

Quick thought: would it be helpful to have a 5-minute async demo ready for when {{project/launch}} wraps up? That way when you have bandwidth, you can review on your schedule without needing to coordinate a live call.

I can send you a custom Loom walkthrough specific to {{company}}'s use case - just let me know!

Either way, I'll check back in after {{timeframe}}.

Best,
{{your_name}}
```

**Next Actions:**
- [ ] Update CRM with "Timing - Project In Progress" tag
- [ ] Create custom async demo if they accept offer
- [ ] Set follow-up reminder for after their project timeline

---

## 4. Not Interested / Unsubscribe Responses

### Scenario 4A: "Not interested"

**Your Response:**

```
Subject: Re: [Original Subject]

Hi {{first_name}},

No problem at all - thanks for letting me know!

Quick question (optional to answer): was this not a fit because:
a) Timing isn't right
b) Already have a solution
c) Not a priority
d) Something else

Always trying to improve my outreach, so any feedback helps. Either way, best of luck with {{company}}'s growth!

Best,
{{your_name}}
```

**Next Actions:**
- [ ] Update CRM status to "Closed Lost"
- [ ] Add their feedback to "Objections" tracking
- [ ] Remove from all email sequences
- [ ] Add to long-term nurture (6-12 month check-in) if they're polite

---

### Scenario 4B: "Please remove me from your list"

**Your Response:**

```
Subject: Removed - Sorry for the bother!

Hi {{first_name}},

Done - you're removed from my list. Apologies for the interruption!

Best,
{{your_name}}
```

**Next Actions:**
- [ ] **IMMEDIATELY** remove from all email sequences
- [ ] Mark as "Unsubscribed" in CRM
- [ ] Never contact again (unless they reach out)
- [ ] Ensure compliant with CAN-SPAM / GDPR

---

### Scenario 4C: Hostile/Rude Response

**Your Response:**

```
Subject: Removed

{{first_name}},

Removed. Apologies.

{{your_name}}
```

**Alternative:** Don't respond at all, just remove them.

**Next Actions:**
- [ ] Remove immediately from all sequences
- [ ] Mark as "Do Not Contact"
- [ ] Don't take it personally - move on to next prospect

---

## 5. Automated Replies

### Scenario 5A: "Out of Office" Auto-Reply

**Your Action:**

**DO NOT RESPOND** to auto-replies.

**Next Actions:**
- [ ] Note return date in CRM
- [ ] Set follow-up reminder for 1-2 days after they return
- [ ] Don't count as "reply" in metrics

---

### Scenario 5B: "Please contact [other person]" Auto-Reply

**Your Response:**

```
Subject: [Original Subject] - Referred by {{original_contact}}

Hi {{new_contact_name}},

{{original_contact}} suggested I reach out to you regarding {{topic}}.

{{brief_1_paragraph_summary}}

Would you be open to a quick 15-minute call this week to discuss?

Best,
{{your_name}}

---
Original email below for context:
[Include original email]
```

**Next Actions:**
- [ ] Add new contact to CRM
- [ ] Link to original contact (note referral source)
- [ ] Send warm introduction email
- [ ] Thank original contact if appropriate

---

## 6. Meeting Follow-Up Responses

### Scenario 6A: After Successful Demo Call

**Your Response (within 2 hours of call):**

```
Subject: Thanks for the call - Next steps for {{company}}

Hi {{first_name}},

Great connecting today! As discussed, here's a summary of next steps:

**What We Discussed:**
- {{key_point_1}}
- {{key_point_2}}
- {{key_point_3}}

**Proposed Solution:**
{{brief_solution_summary}}

**Next Steps:**
1. {{action_item_1}} (Owner: {{owner}}, Due: {{date}})
2. {{action_item_2}} (Owner: {{owner}}, Due: {{date}})
3. {{action_item_3}} (Owner: {{owner}}, Due: {{date}})

**Resources Shared:**
- {{demo_url}}
- {{github_repo}}
- {{portfolio_link}}

I'll follow up on {{date}} with {{deliverable}}. In the meantime, feel free to reach out with any questions!

Looking forward to working together.

Best,
{{your_name}}
```

**Next Actions:**
- [ ] Update CRM status to "Proposal Sent" or "Negotiating"
- [ ] Complete action items you committed to
- [ ] Set follow-up reminder for agreed-upon date
- [ ] Send proposal / contract if discussed

---

### Scenario 6B: After Call with "Maybe" / "We'll Get Back to You"

**Your Response (within 2 hours):**

```
Subject: Thanks for the call - Happy to answer any questions

Hi {{first_name}},

Thanks for taking the time to chat today! I know you're evaluating options, so here's a recap to help with your decision:

**What We Discussed:**
- {{key_point_1}}
- {{key_point_2}}

**Why This Might Be a Fit:**
- {{benefit_1_specific_to_their_needs}}
- {{benefit_2_specific_to_their_needs}}

**Common Questions We Didn't Cover:**
- {{anticipated_question_1}}
- {{anticipated_question_2}}

No pressure whatsoever - just want to make sure you have what you need to make the right decision for {{company}}.

When's a good time to follow up? Or feel free to reach out whenever works for you.

Best,
{{your_name}}
```

**Next Actions:**
- [ ] Set follow-up reminder for 1 week
- [ ] Prepare to answer anticipated objections
- [ ] Research any concerns they mentioned

---

### Scenario 6C: After No-Show / Missed Meeting

**Your Response (immediately after no-show):**

```
Subject: Missed our call - Everything okay?

Hi {{first_name}},

I just tried calling for our scheduled meeting at {{time}}. No worries if something came up!

I have a few backup times this week if you'd like to reschedule:
- {{option_1}}
- {{option_2}}
- {{option_3}}

Or feel free to grab time directly: [calendly_link]

If now's not a good time, totally understand - just let me know!

Best,
{{your_name}}
```

**Next Actions:**
- [ ] Wait 24 hours for response
- [ ] If no response, send one more follow-up in 3 days
- [ ] If still no response, move to "Closed Lost"

---

## Response Time Guidelines

| Response Type | Target Time | Max Time |
|--------------|-------------|----------|
| **Positive Interest** | Within 1 hour | Within 2 hours |
| **Questions** | Within 2 hours | Within 4 hours |
| **Objections** | Within 4 hours | Within 24 hours |
| **Not Interested** | Within 24 hours | Within 48 hours |
| **Automated Replies** | No response | N/A |
| **Post-Meeting** | Within 2 hours | Within 24 hours |

**Business Hours:** 9 AM - 6 PM PT, Monday-Friday

---

## Email Etiquette Best Practices

### Do's ✅
- ✅ Respond within 2 hours during business hours
- ✅ Keep responses under 200 words
- ✅ Always include a clear next action / CTA
- ✅ Use their name in greeting
- ✅ Proofread before sending
- ✅ Include relevant links / resources
- ✅ Match their tone (formal vs. casual)

### Don'ts ❌
- ❌ Send long walls of text
- ❌ Be pushy or aggressive
- ❌ Take "no" personally
- ❌ Argue with objections
- ❌ Send generic copy-paste responses
- ❌ Contact after they unsubscribe
- ❌ Respond to auto-replies

---

## Objection Handling Framework

### Listen → Acknowledge → Reframe → Provide Value

**Example:**

**Objection:** "We don't have budget"

1. **Listen:** "I understand budget is a concern."
2. **Acknowledge:** "That makes total sense - AI projects can be expensive."
3. **Reframe:** "What if we started with a small pilot for $500 to prove ROI before committing to a larger engagement?"
4. **Provide Value:** "Here's how a similar company started small and scaled..."

---

## CRM Tagging for Response Types

### Tags to Add Based on Response
- `positive-interest` → Replied with interest
- `question-pricing` → Asked about pricing
- `question-technical` → Asked technical questions
- `objection-budget` → Budget concern
- `objection-timing` → Not right time
- `objection-vendor` → Already have solution
- `meeting-booked` → Scheduled call
- `closed-won` → Became client
- `closed-lost` → Not interested
- `unsubscribed` → Remove from list

---

## Weekly Review Checklist

### Every Friday, Review:
- [ ] Total replies received this week
- [ ] Response sentiment breakdown (positive, neutral, negative)
- [ ] Common objections encountered
- [ ] Response time metrics (are you hitting <2 hour target?)
- [ ] Meetings booked
- [ ] Closed deals
- [ ] Update response templates based on what's working

---

## Escalation Scenarios

### When to Escalate / Get Help

**Scenario 1:** Enterprise deal (>$10k) shows interest
→ Loop in sales / business development if available

**Scenario 2:** Technical question you can't answer
→ Research, then respond (or admit you don't know and will find out)

**Scenario 3:** Legal / compliance concerns
→ Consult legal advisor before committing

**Scenario 4:** Hostile response / potential legal threat
→ Document, do not engage, consult legal if necessary

---

**Version**: 1.0
**Last Updated**: February 9, 2026
**Owner**: Outreach Campaign Manager
