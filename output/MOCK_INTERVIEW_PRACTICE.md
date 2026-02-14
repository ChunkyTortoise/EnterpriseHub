# Mock Interview Practice - Chase Ashley (AI Secretary)

**Purpose**: Practice questions and answers for today's interview  
**Time**: Practice each answer out loud, aim for 60-90 seconds

---

## 🎯 Opening Statement Practice

**Practice saying this out loud 3 times:**

> "I've built a production multi-agent system that handles exactly this - task routing, calendar integration, and intelligent handoffs between specialized agents. For your AI secretary, I'd use a task classification layer that routes incoming requests to domain-specific sub-agents: calendar, email drafting, research, reminders. Let me walk you through the architecture."

---

## 💬 Technical Questions

### Q1: "How would you architect the Gmail integration?"

**Answer (90 seconds):**

> "I'd use OAuth 2.0 for secure authentication. Here's the flow:
>
> First, the user authorizes via Google's OAuth consent screen. We receive an authorization code, exchange it for access and refresh tokens, and store them encrypted in our database using Fernet symmetric encryption.
>
> For email monitoring, I'd set up Google Pub/Sub webhooks. When a new email arrives, Google pushes a notification to our endpoint, and we fetch only the new messages. This is more efficient than polling.
>
> For token refresh, I check the expiry before each API call. If expired, I use the refresh token to get a new access token automatically. The user never needs to re-authenticate.
>
> Key security considerations: tokens are encrypted at rest, we use minimal OAuth scopes (only gmail.readonly, gmail.send, gmail.compose), and all API calls use TLS 1.3."

---

### Q2: "How do you handle calendar conflicts?"

**Answer (60 seconds):**

> "I use Google's FreeBusy API to get all existing events in the requested timeframe. Then I generate candidate slots based on the user's preferences - business hours, buffer time between meetings, no-meeting days.
>
> Each candidate slot is checked against the busy periods. If there's any overlap, the slot is rejected.
>
> I also score the remaining slots based on preferences. For example, if the user prefers morning meetings, those slots get higher scores. The top 3-5 slots are presented to the user for selection.
>
> For multi-attendee meetings, I check all attendees' calendars and find mutual availability. If no overlap exists, I suggest alternative times."

---

### Q3: "What's your approach to email drafting?"

**Answer (60 seconds):**

> "I use a template-based approach with LLM customization. For common scenarios like meeting invites or follow-ups, I have pre-defined templates that ensure consistent structure.
>
> The LLM - typically Claude Haiku for speed and cost - customizes the template with the specific context: recipient name, topic, available times, etc.
>
> Critical safety feature: emails NEVER auto-send by default. Every draft goes into a 'pending review' state. The user must explicitly approve before sending.
>
> I also calculate a confidence score for each draft. If confidence is below 0.8, I flag it for mandatory review. High-confidence drafts can optionally be auto-approved if the user enables that setting."

---

### Q4: "How would you prevent the AI from sending inappropriate emails?"

**Answer (60 seconds):**

> "Multiple safety layers:
>
> First, default to draft mode - the secretary never sends without user approval.
>
> Second, confidence scoring - if the AI isn't confident about the draft, it requires review.
>
> Third, profanity filter - I check for inappropriate language before showing the draft.
>
> Fourth, recipient whitelist - users can restrict sending to specific domains only.
>
> Fifth, audit trail - every draft is logged with reasoning, so users can review why certain content was generated.
>
> Finally, undo window - Gmail API supports a 30-second undo period for sent emails.
>
> Users can adjust the auto-send aggressiveness in settings, from 'never' to 'auto-send routine stuff'."

---

### Q5: "How do you handle user preferences and learning?"

**Answer (60 seconds):**

> "I store explicit preferences in a JSON structure: business hours, preferred meeting times, email tone, signature, buffer time between meetings.
>
> For implicit learning, I analyze user edits. When a user modifies an AI-generated draft, I use Claude to compare the original and edited versions. It identifies patterns: 'user prefers shorter emails' or 'user adds specific closing phrase.'
>
> These insights are merged into their preference profile. Over time, the system learns their style.
>
> I also track which meeting slots they accept or reject. If they consistently reject Friday afternoon slots, the system learns to deprioritize those."

---

## 💼 Business Questions

### Q6: "What's your timeline to MVP?"

**Answer (60 seconds):**

> "Nine weeks total, based on my existing EnterpriseHub codebase which has similar components.
>
> Phase 1 is four weeks: Gmail OAuth, email fetching, task classification, calendar integration, and email drafting with approval workflow.
>
> Phase 2 is three weeks: Multi-tenant architecture, user registration, Stripe billing, and admin dashboard.
>
> Phase 3 is two weeks: Security audit, performance optimization, and beta testing with 10-20 users before launch.
>
> This assumes 20-25 hours per week from me, and that you handle UI/UX design. If you need mobile apps or Outlook integration, that adds 4-6 weeks."

---

### Q7: "How would you monetize this?"

**Answer (60 seconds):**

> "Freemium model with tiered pricing:
>
> Free tier for acquisition: 50 AI actions per month, one email account, basic features.
>
> Pro tier at $19/month: 500 actions, three email accounts, advanced preferences like meeting buffers.
>
> Team tier at $49 per user per month: Unlimited actions, shared scheduling for teams, Slack integration.
>
> Enterprise tier with custom pricing: On-premise deployment, SSO, custom AI training on company data.
>
> Additional revenue from usage overages at $0.10 per action, and add-ons like CRM integration or voice secretary features."

---

### Q8: "What are your rates?"

**Answer (30 seconds):**

> "For this project, I'd propose either fixed-price or hourly:
>
> Fixed-price: $11,000 for the complete MVP, paid in milestones.
>
> Hourly: $70 per hour, estimated 180 hours total.
>
> I'm flexible and open to discussing what works best for your budget. If you commit to a longer engagement, I can offer a discounted rate."

---

## 🔧 Scenario Questions

### Q9: "What if Gmail API is down?"

**Answer (45 seconds):**

> "I implement a circuit breaker pattern. After a few consecutive failures, the circuit opens and we stop attempting API calls. This prevents cascading failures and gives Google time to recover.
>
> In the meantime, the secretary queues tasks locally. When the circuit closes - typically after 60 seconds of recovery time - we process the queued tasks.
>
> I also have retry logic with exponential backoff. Transient errors get retried with increasing delays: 1 second, 2 seconds, 4 seconds.
>
> Users see a graceful message: 'Gmail is temporarily unavailable. Your tasks are queued and will be processed shortly.'"

---

### Q10: "How do you handle data privacy?"

**Answer (60 seconds):**

> "Critical for trust. Here's my approach:
>
> Encryption at rest: All email content and OAuth tokens are encrypted with Fernet before storing in PostgreSQL.
>
> Encryption in transit: TLS 1.3 for all API calls.
>
> Minimal retention: Emails are only stored while being processed. Auto-delete after 30 days unless the user explicitly saves them.
>
> Access controls: Each user can only access their own data. Row-level security in PostgreSQL enforces this at the database level.
>
> GDPR compliance: Users can export all their data or request complete deletion.
>
> For enterprise clients, I offer on-premise deployment where they control all data on their own infrastructure."

---

## 🎤 Questions to Ask Chase

**Practice asking these naturally:**

1. "What's your target market - individuals or businesses? That affects feature prioritization."

2. "Do you have UI/UX designs already, or would you like me to recommend a design system?"

3. "What's your expected launch date? Want to make sure the timeline aligns."

4. "Are you open to using existing services like Stripe for billing and Twilio for SMS, or do you prefer building everything in-house?"

5. "What's your biggest concern - speed to market, cost optimization, or feature richness?"

---

## ⚡ Rapid Fire Practice

**Practice quick 15-second answers:**

**"Why should I hire you?"**
> "I've already built this architecture in EnterpriseHub - 5,100 tests, proven performance. You're not paying for learning curve."

**"What's your biggest weakness?"**
> "I tend to over-engineer for scale. I've learned to build for current needs while keeping a clear path forward."

**"How do you handle tight deadlines?"**
> "Prioritize ruthlessly. MVP features first, nice-to-haves later. Communicate early if timeline is at risk."

**"What if you get stuck?"**
> "Research, ask for clarification, propose options. Never spin wheels silently."

---

## 📋 Self-Assessment Checklist

After practicing, check:

- [ ] Can I recite the elevator pitch without notes?
- [ ] Can I answer "timeline to MVP" in under 60 seconds?
- [ ] Can I explain the architecture clearly?
- [ ] Can I discuss rates confidently?
- [ ] Do I have 3 questions ready to ask?

---

**Remember**: You've built this before. Speak with confidence.
