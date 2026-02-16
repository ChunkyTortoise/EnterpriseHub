# ConvertKit Automation Rules

Tag-based automation triggers for the Production AI Systems email sequences.

## Tags

| Tag | Description | Applied By |
|-----|-------------|------------|
| `waitlist` | Signed up for course waitlist | ConvertKit form |
| `cohort-1-prospect` | Interested in Cohort 1 | Auto (on waitlist signup) |
| `cohort-1-enrolled` | Purchased Cohort 1 | Maven webhook |
| `cohort-2-waitlist` | Waitlisted for Cohort 2 | Auto (after Cohort 1 close) |
| `high-intent` | Replied to value email or clicked multiple CTAs | Manual / auto-reply detection |
| `enrollment-email-sent` | Received the enrollment open email | Auto (sequence) |
| `scarcity-email-sent` | Received the scarcity email | Auto (sequence) |
| `final-reminder-sent` | Received the final reminder | Auto (sequence) |
| `cart-close-sent` | Received the cart close email | Auto (sequence) |
| `onboarded` | Completed onboarding (Discord + Codespace) | Manual / webhook |
| `completed-cohort` | Finished the cohort (5/6 labs + final) | Manual |
| `removed` | Removed from course (refund or moderation) | Manual |

## Sequences

### Sequence 1: Pre-Launch (Waitlist to Enrollment)

**Entry trigger**: Tag `waitlist` added

| Step | Email | Delay |
|------|-------|-------|
| 1 | 00-waitlist-welcome.md | Immediate |
| 2 | 01-social-proof.md | 9 days |
| 3 | 02-value-deep-dive.md | 7 days |
| 4 | 03-early-bird-open.md | 7 days |
| 5 | 04-scarcity.md | 4 days |
| 6 | 05-final-reminder.md | 2 days |
| 7 | 06-cart-close.md | 1 day |

**Exit conditions**:
- Tag `cohort-1-enrolled` added (purchased) → Remove from sequence, enter Onboarding
- Tag `removed` added → Remove from all sequences

### Sequence 2: Onboarding (Post-Purchase)

**Entry trigger**: Tag `cohort-1-enrolled` added

| Step | Email | Delay | Content |
|------|-------|-------|---------|
| 1 | Welcome + receipt | Immediate | "You're in! Here's your access." Discord invite link, GitHub Classroom join link, Codespace setup instructions |
| 2 | Pre-work | 2 days | "Before Day 1, do these 3 things": Join Discord, introduce yourself, launch a Codespace to verify setup |
| 3 | Day 1 reminder | Morning of Day 1 | Session link, what to have ready, first lab preview |
| 4 | Week 1 recap | End of Week 1 | Lab 1 deadline reminder, office hours schedule, community highlights |

### Sequence 3: Cohort 2 Nurture

**Entry trigger**: Tag `cohort-2-waitlist` added

| Step | Email | Delay | Content |
|------|-------|-------|---------|
| 1 | "You're on the list" | Immediate | Acknowledge waitlist, share Cohort 1 outcomes if available |
| 2 | Cohort 1 highlights | 2 weeks | Student projects, metrics, testimonials from Cohort 1 |
| 3 | Cohort 2 announcement | When ready | Dates, pricing (no longer beta), early access for waitlist |

## Automation Rules

### Rule 1: Waitlist Signup

```
WHEN: Subscriber added to form "Production AI Systems Waitlist"
DO:
  1. Add tag "waitlist"
  2. Add tag "cohort-1-prospect"
  3. Add to Sequence 1 (Pre-Launch)
```

### Rule 2: Purchase Completed

```
WHEN: Webhook received from Maven (purchase event)
DO:
  1. Add tag "cohort-1-enrolled"
  2. Remove tag "cohort-1-prospect"
  3. Remove from Sequence 1 (Pre-Launch)
  4. Add to Sequence 2 (Onboarding)
```

### Rule 3: Enrollment Period Closes

```
WHEN: Enrollment deadline passes (manual trigger or scheduled)
DO:
  1. For all subscribers with tag "cohort-1-prospect" AND without tag "cohort-1-enrolled":
     a. Remove tag "cohort-1-prospect"
     b. Add tag "cohort-2-waitlist"
     c. Remove from Sequence 1 (Pre-Launch)
     d. Add to Sequence 3 (Cohort 2 Nurture)
```

### Rule 4: High-Intent Detection

```
WHEN: Subscriber replies to any email in Sequence 1
DO:
  1. Add tag "high-intent"
  2. (For Rule 4 only: send early-bird email 6 hours before general release)
```

### Rule 5: Refund Processed

```
WHEN: Webhook received from Maven (refund event)
DO:
  1. Remove tag "cohort-1-enrolled"
  2. Add tag "removed"
  3. Remove from Sequence 2 (Onboarding)
  4. Add tag "cohort-2-waitlist" (give them another chance next cohort)
```

## Webhook Configuration

### Maven → ConvertKit

**Webhook URL**: `https://api.convertkit.com/v3/custom_fields` (via Zapier or direct integration)

**Events to capture**:
- `enrollment.completed` → Add tag "cohort-1-enrolled"
- `enrollment.refunded` → Remove tag, add "removed"

### Setup Steps:

1. In Maven: Settings > Integrations > Webhooks > Add webhook URL
2. In ConvertKit: Create a custom automation that listens for the webhook
3. Alternative: Use Zapier as middleware (Maven trigger → ConvertKit action)

## Metrics to Track

| Metric | Target | Where to Check |
|--------|--------|----------------|
| Waitlist conversion rate | > 15% | ConvertKit: waitlist → enrolled tags |
| Email open rate | > 40% | ConvertKit sequence analytics |
| Email click rate | > 5% | ConvertKit sequence analytics |
| Unsubscribe rate | < 2% | ConvertKit sequence analytics |
| Reply rate (value email) | > 5% | Manual inbox check |
