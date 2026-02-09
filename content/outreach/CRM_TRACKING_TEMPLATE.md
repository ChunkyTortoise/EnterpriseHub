# Cold Outreach Campaign - CRM Tracking Template

## Overview
This template provides a structured approach to tracking cold outreach campaigns across 30 targets. Use this as a spreadsheet template (Google Sheets, Airtable, or CRM system).

---

## Spreadsheet Structure

### Sheet 1: Master Contact List

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| **Contact ID** | Auto-number | Unique identifier | 1 |
| **Company Name** | Text | Target company | Abridge |
| **Category** | Dropdown | AI Startup, Real Estate Tech, Enterprise SaaS, Consulting, Healthcare/Legal/Finance | AI Startup |
| **Contact Name** | Text | Full name of recipient | Sarah Chen |
| **First Name** | Text | First name for personalization | Sarah |
| **Job Title** | Text | Current role | VP of Engineering |
| **Email Address** | Email | Primary contact email | sarah.chen@abridge.com |
| **LinkedIn URL** | URL | LinkedIn profile | linkedin.com/in/sarachen |
| **Company Website** | URL | Company domain | abridge.com |
| **Priority** | Dropdown | High, Medium, Low | High |
| **Status** | Dropdown | Not Sent, Sent, Opened, Clicked, Replied, Meeting Booked, Closed Won, Closed Lost | Not Sent |
| **Engagement Score** | Number (0-100) | Calculated engagement metric | 85 |
| **Tags** | Multi-select | Custom tags | RAG Expert, Series E, HIPAA |
| **Notes** | Long text | Research notes, context | Recent $5.3B valuation, expanding team |
| **Created Date** | Date | When contact was added | 2026-02-09 |
| **Last Updated** | Date | Last activity timestamp | 2026-02-09 |

---

### Sheet 2: Email Campaign Tracking

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| **Email ID** | Auto-number | Unique email identifier | 1 |
| **Contact ID** | Lookup | Links to Master Contact List | 1 |
| **Email Type** | Dropdown | Initial, Follow-up 1, Follow-up 2, Follow-up 3 | Initial |
| **Subject Line** | Text | Actual subject line sent | Production RAG architecture for clinical documentation scaling |
| **Subject Line Variant** | Dropdown | A, B, C | A |
| **Sent Date** | Date + Time | When email was sent | 2026-02-09 10:30 AM |
| **Opened?** | Checkbox | Email was opened | ✓ |
| **Open Date** | Date + Time | First open timestamp | 2026-02-09 2:15 PM |
| **Clicked?** | Checkbox | Link was clicked | ✓ |
| **Click Date** | Date + Time | First click timestamp | 2026-02-09 2:16 PM |
| **Link Clicked** | Text | Which link was clicked | Demo URL |
| **Replied?** | Checkbox | Recipient replied | ✗ |
| **Reply Date** | Date + Time | Reply timestamp | - |
| **Reply Sentiment** | Dropdown | Positive, Neutral, Negative, Objection | - |
| **Next Action** | Text | Follow-up action required | Send follow-up #1 on Feb 14 |
| **Email Body** | Long text | Full email content (for reference) | [Full email text] |

---

### Sheet 3: Campaign Performance

| Metric | Formula | Target | Current |
|--------|---------|--------|---------|
| **Total Contacts** | COUNT(Contact ID) | 30 | 30 |
| **Emails Sent** | COUNT(Status ≥ "Sent") | 30 | 0 |
| **Open Rate** | (Opened / Sent) × 100 | 25-35% | - |
| **Click Rate** | (Clicked / Sent) × 100 | 5-10% | - |
| **Reply Rate** | (Replied / Sent) × 100 | 5-10% | - |
| **Meeting Booked Rate** | (Meeting Booked / Sent) × 100 | 2-5% | - |
| **Conversion Rate** | (Closed Won / Sent) × 100 | 1-3% | - |
| **Avg Time to Reply** | AVG(Reply Date - Sent Date) | <3 days | - |
| **Avg Time to Meeting** | AVG(Meeting Date - Sent Date) | <7 days | - |
| **Best Performing Category** | Category with highest reply rate | - | - |
| **Best Subject Line** | Subject variant with highest open rate | - | - |

---

### Sheet 4: A/B Test Results

| Subject Line Variant | Category | Emails Sent | Opens | Open Rate | Clicks | Click Rate | Replies | Reply Rate | Winner? |
|---------------------|----------|-------------|-------|-----------|--------|-----------|---------|-----------|---------|
| "Production RAG architecture..." | AI Startup | 2 | 1 | 50% | 1 | 50% | 0 | 0% | - |
| "Quick thought on {{company}}'s AI roadmap" | AI Startup | 2 | 0 | 0% | 0 | 0% | 0 | 0% | - |
| "RAG pipeline question for {{company}}" | AI Startup | 2 | 1 | 50% | 0 | 0% | 0 | 0% | - |

---

### Sheet 5: Follow-Up Cadence Tracker

| Contact ID | Company | Initial Sent | F/U #1 Due | F/U #1 Sent | F/U #2 Due | F/U #2 Sent | F/U #3 Due | F/U #3 Sent | Remove Date |
|-----------|---------|--------------|-----------|-------------|-----------|-------------|-----------|-------------|-------------|
| 1 | Abridge | 2026-02-09 | 2026-02-12 | - | 2026-02-16 | - | 2026-02-23 | - | 2026-03-09 |

**Automation Rules:**
- **Follow-up #1**: 3 days after initial send (if no reply)
- **Follow-up #2**: 7 days after initial send (if no reply)
- **Follow-up #3**: 14 days after initial send (if no reply)
- **Remove from sequence**: 30 days after initial send OR after reply/meeting booked

---

### Sheet 6: Pipeline Stages

| Stage | Contact IDs | Count | Value ($) | Close Probability | Expected Value |
|-------|-------------|-------|-----------|-------------------|----------------|
| **Cold** | - | 30 | - | 0% | $0 |
| **Contacted** | - | 0 | - | 5% | $0 |
| **Engaged** (opened/clicked) | - | 0 | - | 10% | $0 |
| **Replied** | - | 0 | $0 | 20% | $0 |
| **Meeting Booked** | - | 0 | $0 | 40% | $0 |
| **Proposal Sent** | - | 0 | $0 | 60% | $0 |
| **Negotiating** | - | 0 | $0 | 80% | $0 |
| **Closed Won** | - | 0 | $0 | 100% | $0 |
| **Closed Lost** | - | 0 | - | 0% | $0 |

**Deal Values:**
- Custom AI framework: $300-$8,000 (one-time)
- Monthly retainer: $2,500-$8,000/month
- Consulting/subcontracting: $150-$250/hour

---

## CRM Tool Recommendations

### Option 1: Google Sheets (Free, Simple)
**Pros:**
- Free
- Easy to set up
- Collaborative
- Formulas for automatic calculations

**Cons:**
- Manual email tracking (need to update opens/clicks manually)
- No native email integration
- Limited automation

**Best for:** Small campaigns, budget-conscious, quick start

---

### Option 2: HubSpot Free CRM (Free, Mid-tier)
**Pros:**
- Free tier includes email tracking
- Automatic open/click tracking with HubSpot email extension
- Pipeline visualization
- Contact management
- Email templates with personalization
- Basic automation (sequences)

**Cons:**
- Learning curve
- Limited customization on free tier
- Need to use HubSpot's email sending (or pay for tracking)

**Best for:** Serious outreach, plan to scale, want automation

**Setup:**
1. Sign up for HubSpot Free CRM
2. Import 30 contacts from CSV
3. Create custom properties (Category, Priority, Engagement Score)
4. Set up email sequences for follow-ups
5. Install HubSpot Sales Chrome extension for email tracking

---

### Option 3: Streak CRM (Gmail-based, $15-49/mo)
**Pros:**
- Lives inside Gmail
- Automatic email tracking (opens, clicks)
- Mail merge with personalization
- Pipeline visualization
- Follow-up reminders

**Cons:**
- Requires Gmail
- Paid ($15/mo starter, $49/mo for full features)
- Less robust than HubSpot for complex workflows

**Best for:** Gmail users, want simplicity, willing to pay for convenience

---

### Option 4: Airtable ($20/mo, Advanced)
**Pros:**
- Highly customizable
- Relational database (link contacts to emails to companies)
- Beautiful interface
- Automation capabilities
- Forms, views, filters

**Cons:**
- No native email tracking (need Zapier integration)
- Steeper learning curve
- Paid ($20/mo for automation)

**Best for:** Data nerds, want full control, willing to invest in setup

---

## Implementation Checklist

### Week 1: Setup
- [ ] Choose CRM tool (Google Sheets, HubSpot, Streak, or Airtable)
- [ ] Import 30 contacts from OUTREACH_TARGETS.md
- [ ] Set up custom fields (Category, Priority, Status, Tags)
- [ ] Create email templates with personalization tokens
- [ ] Configure email tracking (if using HubSpot/Streak)
- [ ] Set up automated follow-up sequences

### Week 2: Launch
- [ ] Send initial batch (5-10 emails/day to avoid spam filters)
- [ ] Monitor open/click rates daily
- [ ] Respond to replies within 2 hours (business hours)
- [ ] Update CRM with engagement data
- [ ] Trigger follow-up #1 for non-responders (Day 3)

### Week 3: Optimize
- [ ] Analyze A/B test results (subject lines)
- [ ] Identify best-performing categories
- [ ] Adjust email copy based on feedback
- [ ] Send follow-up #2 (Day 7)
- [ ] Move engaged contacts to "Meeting Booked" stage

### Week 4: Close Loop
- [ ] Send follow-up #3 (Day 14)
- [ ] Remove non-responders from active sequence
- [ ] Calculate final campaign metrics
- [ ] Document lessons learned
- [ ] Plan next campaign based on insights

---

## Key Metrics to Track

### Leading Indicators (Predict success)
- **Open Rate**: Are subject lines working?
- **Click Rate**: Is the offer compelling?
- **Time to First Reply**: How fast are we responding?

### Lagging Indicators (Measure success)
- **Reply Rate**: Are emails resonating?
- **Meeting Booked Rate**: Is the CTA effective?
- **Conversion Rate**: Are we closing deals?

### Optimization Metrics
- **Best Performing Category**: Which segment converts best?
- **Best Subject Line**: Which subject drives highest engagement?
- **Optimal Send Time**: When do recipients engage most?

---

## Success Benchmarks

### Cold Outreach Industry Standards
| Metric | Poor | Average | Good | Excellent |
|--------|------|---------|------|-----------|
| **Open Rate** | <15% | 15-25% | 25-35% | >35% |
| **Click Rate** | <2% | 2-5% | 5-10% | >10% |
| **Reply Rate** | <2% | 2-5% | 5-10% | >10% |
| **Meeting Rate** | <1% | 1-2% | 2-5% | >5% |
| **Conversion Rate** | <0.5% | 0.5-1% | 1-3% | >3% |

### Campaign Goals (30 contacts)
- **Emails Sent**: 30 (initial) + 60-90 (follow-ups) = 90-120 total
- **Expected Opens**: 27-42 (25-35% open rate)
- **Expected Clicks**: 5-12 (5-10% click rate)
- **Expected Replies**: 2-6 (5-10% reply rate)
- **Expected Meetings**: 1-3 (2-5% meeting rate)
- **Expected Deals**: 0-1 (1-3% conversion rate)

**Revenue Projection:**
- **Conservative**: 1 deal × $2,500/mo retainer = $2,500/mo ($30,000/year)
- **Realistic**: 2 deals × $5,000/mo retainer = $10,000/mo ($120,000/year)
- **Optimistic**: 3 deals × $8,000/mo retainer = $24,000/mo ($288,000/year)

---

## Daily Workflow

### Morning (9-10 AM)
1. Check CRM for new replies
2. Respond to all replies within 2 hours
3. Update contact status and next actions
4. Send scheduled follow-ups (5-10 emails)

### Midday (12-1 PM)
5. Monitor email tracking (opens, clicks)
6. Research any new contacts that engaged
7. Prepare personalized follow-ups for engaged contacts

### Afternoon (3-4 PM)
8. Review pipeline stages
9. Update deal values and probabilities
10. Schedule meetings with interested contacts
11. Plan tomorrow's outreach batch

### End of Day
12. Log all activities in CRM
13. Update campaign performance metrics
14. Set reminders for follow-ups

---

## Data Privacy & Compliance

### GDPR / CAN-SPAM Compliance
- [ ] Include working unsubscribe link in every email
- [ ] Honor unsubscribe requests within 24 hours
- [ ] Include physical mailing address in footer
- [ ] Don't use deceptive subject lines
- [ ] Clearly identify sender

### Data Security
- [ ] Don't store sensitive data in spreadsheets
- [ ] Use password-protected CRM
- [ ] Enable 2FA on CRM account
- [ ] Regular backups of contact data

---

## Template Files

### CSV Import Template
```csv
Company Name,Category,Contact Name,First Name,Job Title,Email Address,LinkedIn URL,Company Website,Priority,Tags,Notes
Abridge,AI Startup,Sarah Chen,Sarah,VP of Engineering,sarah.chen@abridge.com,linkedin.com/in/sarachen,abridge.com,High,"RAG Expert, Series E, HIPAA",Recent $5.3B valuation
Harvey,AI Startup,John Smith,John,CTO,john.smith@harvey.ai,linkedin.com/in/johnsmith,harvey.ai,High,"Legal Tech, LLM",Series E $300M funding
```

### HubSpot Import Format
- Use HubSpot's CSV import wizard
- Map columns: Company Name → Company, Email Address → Email, etc.
- Create custom properties for Category, Priority, Tags

### Airtable Import
- Create base with "Contacts" table
- Import CSV directly
- Link to "Companies" and "Emails" tables for relational data

---

**Version**: 1.0
**Last Updated**: February 9, 2026
**Owner**: Outreach Campaign Manager
