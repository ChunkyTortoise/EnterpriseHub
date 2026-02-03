# Jorge Delivery Plan - February 2, 2026

## Gap Analysis: Jorge's Spec vs Current Implementation

---

## SPECIFICATION RECONCILIATION

Jorge provided two sets of qualification criteria across emails. The **January 17 "Final Outline"** is the authoritative spec (labeled "final") and is what the codebase implements:

| # | Jorge's Exact Question (Jan 17) | Implemented? | File |
|---|-------------------------------|-------------|------|
| Q1 | "What's got you considering wanting to sell, where would you move to" | YES | `jorge_seller_engine.py:41` |
| Q2 | "If our team sold your home within the next 30 to 45 days, would that pose a problem for you" | YES | `jorge_seller_engine.py:44` |
| Q3 | "How would you describe your home, would you say it's move-in ready or would it need some work" | YES | `jorge_seller_engine.py:47` |
| Q4 | "What price would incentivize you to sell" | YES | `jorge_seller_engine.py:50` |

---

## GAP ANALYSIS BY REQUIREMENT

### A. SELLER BOT - Core Requirements

| Requirement | Jorge's Spec | Status | Gap |
|------------|-------------|--------|-----|
| Trigger on "Needs Qualifying" tag | Jan 17 email | IMPLEMENTED | None - webhook.py:162 checks this |
| 4 questions asked one at a time | Jan 17 email | IMPLEMENTED | `SellerQuestions.get_next_question()` handles sequencing |
| Hot Seller classification | All 4 answered + 30-45 day timeline + responsive | IMPLEMENTED | jorge_config.py:43-45 |
| Warm Seller classification | Most questions + >45 days + some hesitation | IMPLEMENTED | jorge_config.py:48-49 |
| Cold Seller classification | Vague/stops + long timeline | IMPLEMENTED | jorge_config.py:34 |
| Hot → Tag "Hot Seller" + priority call + notify human | Jan 17 email | IMPLEMENTED | Tag applied, workflow triggered |
| Warm → Tag "Warm Seller" + short nurture | Jan 17 email | IMPLEMENTED | Tag + nurture sequence |
| Cold → Tag "Cold Seller" + long nurture | Jan 17 email | IMPLEMENTED | Tag + long-term sequence |
| Follow-up every 2-3 days for 30 days | Jan 17 email | IMPLEMENTED | `ACTIVE_FOLLOWUP_SCHEDULE = [2, 5, 8, 11...]` |
| After 30 days → every 14 days | Jan 17 email | IMPLEMENTED | `LONGTERM_FOLLOWUP_INTERVAL = 14` |
| No emojis | Jan 17 email | IMPLEMENTED | `allow_emojis: False` |
| No hyphens | Jan 17 email | IMPLEMENTED | `allow_hyphens: False` (NO_HYPHENS = True) |
| Direct but natural tone | Jan 17 email | IMPLEMENTED | Confrontational tone engine |
| Opt-out → end automation | Jan 17 email | NEEDS VERIFICATION | Deactivation tags exist, but explicit opt-out detection unclear |
| Sound 100% human | Jan 2 email | NEEDS TESTING | Tone engine exists but Claude prompts need review |
| Confrontational/straightforward | Jan 17 email | IMPLEMENTED | Tone engine + strategy patterns |

### B. BUYER BOT - Requirements

| Requirement | Jorge's Spec | Status | Gap |
|------------|-------------|--------|-----|
| Send property based on criteria | Jan 4 email | PARTIAL | PropertyMatcher class exists but no MLS/property data feed |
| Follow up with buyers | Jan 4 email | PARTIAL | Buyer bot has qualification but limited follow-up sequencing |
| Financial readiness qualification | Implied | IMPLEMENTED | `assess_financial_readiness` node |
| Property preference extraction | Implied | IMPLEMENTED | `qualify_property_needs` node |
| Budget + timeline extraction | Implied | IMPLEMENTED | Budget keywords + urgency mapping |

### C. LEAD BOT - Requirements

| Requirement | Jorge's Spec | Status | Gap |
|------------|-------------|--------|-----|
| Qualify leads for conversion | Jan 4 email | IMPLEMENTED | 3-7-30 day sequence |
| Lead scoring | Implied | IMPLEMENTED | FRS + PCS scoring |
| Route to seller/buyer bot | Implied | PARTIAL | Intent detection exists but routing logic needs verification |

### D. DASHBOARD - Requirements

| Requirement | Implied Need | Status | Gap |
|------------|-------------|--------|-----|
| Lead pipeline (new → qualifying → qualified) | Essential | OVER-BUILT | 200+ components, need simplified view |
| Temperature breakdown (Hot/Warm/Cold) | Essential | EXISTS | In jorge_analytics_dashboard.py |
| Recent conversations | Essential | EXISTS | In multiple dashboard files |
| Follow-up schedule status | Essential | EXISTS | In follow-up related dashboards |
| Bot performance (response rate, accuracy) | Nice-to-have | EXISTS | Bot health monitoring dashboard |

### E. ADDITIONAL REQUIREMENTS

| Requirement | Source | Status | Gap |
|------------|--------|--------|-----|
| Phone call → summarize in Notes | Jan 4 email | NOT IMPLEMENTED | No call transcription/summarization |
| Onboarding notifications (new user, payment) | Jan 4 email | NOT IMPLEMENTED | Not in scope for bot delivery |
| Email/text blast campaigns | Jan 4 email | NOT IMPLEMENTED | Not in scope for bot delivery |
| "Hit List" NOT part of triggers | Jorge clarification | PARTIAL | Config has "Hit List" in activation_tags - NEEDS FIXING |

---

## CRITICAL ISSUES TO FIX

### P0 - Must Fix Before Delivery

1. **"Hit List" tag must be REMOVED from activation_tags**
   - Jorge explicitly said: "I do NOT want the 'hit list' being apart of the triggers/tags"
   - File: `ghl_real_estate_ai/ghl_utils/config.py:136` has `activation_tags = ["Hit List", "Need to Qualify", "Needs Qualifying"]`
   - FIX: Remove "Hit List" from activation_tags

2. **Import chain verification** - The bots have deep import chains with optional dependencies. Need to verify they actually start without crashing when optional packages are missing.

3. **Human-sounding responses** - The Claude prompts must be reviewed to ensure output doesn't sound AI-generated. Jorge is paying premium ($150) specifically for human-quality responses.

4. **Opt-out detection** - Need explicit handling for "stop", "unsubscribe", "don't contact me" messages to immediately end automation.

5. **End-to-end test** - The full webhook → bot processing → GHL action flow must be verified with a mock GHL payload.

### P1 - Should Fix Before Delivery

6. **Simplify dashboard entry point** - Jorge needs ONE dashboard URL, not 200+ components. Create a focused `jorge_dashboard.py` with 4-5 tabs max.

7. **Buyer bot property data** - The buyer bot has qualification logic but no actual property data source. Need at minimum a mock property database or MLS integration stub.

8. **Opening message flow** - When "Needs Qualifying" tag is first applied (no prior messages), the bot should send the initial outreach message proactively, not wait for a response.

9. **Appointment scheduling confirmation** - Hot seller handoff needs to offer specific time slots and confirm via SMS.

### P2 - Nice-to-Have for Delivery

10. **Edge case handling** - Multiple properties, joint ownership, off-topic responses
11. **Handoff message template** - "Let me connect you with [Agent Name]"
12. **Phone call summarization** - Requires Retell/Vapi integration (stretch goal)

---

## TASK LIST FOR PARALLEL EXECUTION

### Stream 1: Bot Core Fixes (Critical Path)

**Task 1.1**: Remove "Hit List" from activation tags
- File: `ghl_real_estate_ai/ghl_utils/config.py`
- Change: Remove "Hit List" from activation_tags list
- Ensure only "Needs Qualifying" triggers the bot

**Task 1.2**: Verify import chains work without optional deps
- Run each bot module in isolation
- Fix any import errors
- Ensure graceful fallback for missing optional packages

**Task 1.3**: Review and fix Claude system prompts for human tone
- File: `ghl_real_estate_ai/services/claude_assistant.py`
- File: `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py`
- Ensure prompts produce responses that sound human, not AI
- Add explicit instructions: no corporate jargon, no bullet points, casual commas instead of periods
- Test with sample conversations

**Task 1.4**: Add explicit opt-out detection
- Detect messages like "stop", "unsubscribe", "don't contact me", "not interested"
- Apply deactivation tag immediately
- Send graceful exit message
- File: Webhook handler + seller engine

**Task 1.5**: Verify and fix the initial outreach message
- When "Needs Qualifying" tag is applied but no conversation exists
- Bot should send first message proactively (not wait for user response)
- Message should be casual intro: "Hey [name], saw your property inquiry..."

### Stream 2: Buyer Bot Completion

**Task 2.1**: Verify buyer bot end-to-end flow
- Test the 6-node workflow runs without errors
- Verify financial readiness + property matching produces sensible output

**Task 2.2**: Add buyer follow-up sequence
- Mirror seller's 2-3 day / 14 day follow-up pattern for buyer leads
- Customize content for buyer context (property updates, market changes)

**Task 2.3**: Add basic property data source
- Create a sample Rancho Cucamonga property database
- Enable PropertyMatcher to return relevant results
- Format property details for SMS delivery

### Stream 3: Dashboard Simplification

**Task 3.1**: Create focused Jorge delivery dashboard
- Single Streamlit app with 4 tabs:
  1. **Lead Pipeline**: Funnel view (New → Qualifying → Hot/Warm/Cold)
  2. **Bot Activity**: Recent conversations, response times, message count
  3. **Temperature Map**: Breakdown of leads by temperature + trend
  4. **Follow-Up Queue**: Upcoming follow-ups, overdue items
- Use real data from existing services where available
- Clean, professional design (no "Obsidian" enterprise theming)

**Task 3.2**: Wire dashboard to actual data
- Connect to PostgreSQL/SQLite for lead data
- Connect to conversation manager for recent activity
- Connect to follow-up scheduler for queue data

### Stream 4: Integration Testing

**Task 4.1**: Create end-to-end test with mock GHL webhook
- Simulate a full conversation (5 exchanges)
- Verify: tag activation → question sequence → temperature classification → tag application
- Verify: follow-up scheduling triggers

**Task 4.2**: Test tone output quality
- Generate 10+ sample responses for each bot
- Score each for "human-sounding" quality
- Identify and fix any AI-sounding patterns

**Task 4.3**: Test edge cases
- Opt-out mid-conversation
- No response after first question
- Gibberish/off-topic responses
- Multiple questions answered in one message

### Stream 5: Delivery Package

**Task 5.1**: Create clean deployment guide
- Step-by-step GHL webhook setup
- Environment variable configuration
- Required GHL workflows/tags to create
- How to test the bot works

**Task 5.2**: Create Jorge-specific README
- What the system does (in plain English)
- How to monitor lead qualification
- How to access the dashboard
- How to turn off/on the bot
- Troubleshooting common issues

**Task 5.3**: Package clean deliverable
- Identify minimum files needed for deployment
- Remove enterprise/experimental features from delivery
- Create requirements.txt with only needed dependencies

---

## PARALLEL EXECUTION PLAN

```
Chat 1 (Bot Core):     Tasks 1.1, 1.2, 1.3, 1.4, 1.5
Chat 2 (Buyer Bot):    Tasks 2.1, 2.2, 2.3
Chat 3 (Dashboard):    Tasks 3.1, 3.2
Chat 4 (Testing):      Tasks 4.1, 4.2, 4.3 (after Streams 1-2 complete)
Chat 5 (Packaging):    Tasks 5.1, 5.2, 5.3 (after all streams complete)
```

### Dependencies
- Stream 4 depends on Streams 1 + 2 being complete
- Stream 5 depends on all other streams
- Streams 1, 2, 3 can run in parallel

---

## DELIVERY CHECKLIST

- [ ] "Hit List" removed from activation tags
- [ ] Seller bot asks Jorge's 4 exact questions in order
- [ ] Temperature classification matches spec (Hot/Warm/Cold)
- [ ] Follow-up timing: 2-3 days for 30 days, then 14 days
- [ ] Tone: No emojis, no hyphens, direct, human-sounding
- [ ] Opt-out handling works
- [ ] Exit logic stops automation immediately
- [ ] Webhook processes without errors
- [ ] Tags applied correctly in GHL
- [ ] Dashboard shows useful KPIs
- [ ] Buyer bot qualification works
- [ ] Clean deployment guide exists
- [ ] All imports resolve without errors
- [ ] Responses sound human, not AI
- [ ] Initial outreach message sends on tag application
