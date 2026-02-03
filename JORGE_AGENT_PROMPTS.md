# Jorge Delivery — Parallel Agent Prompts

> Copy-paste the appropriate section into a new Claude Code chat to start each stream.
> Each agent works on its own stream. Check JORGE_TASKS.md before starting any task.

---

## STREAM A: Seller Bot Core Fixes

```
You are working on the EnterpriseHub project to finalize Jorge's seller bot for delivery.

BEFORE DOING ANYTHING:
1. Read /Users/cave/Documents/GitHub/EnterpriseHub/JORGE_SPEC.md (full specification)
2. Read /Users/cave/Documents/GitHub/EnterpriseHub/JORGE_TASKS.md (task list — you own Stream A)

YOUR TASKS (Stream A):

A1. Remove "Hit List" from activation_tags
   File: ghl_real_estate_ai/ghl_utils/config.py line 136
   Change: Remove "Hit List" and "Need to Qualify", keep ONLY "Needs Qualifying"
   Also fix line 140: bot_active_disposition → "Needs Qualifying"

A2. Add JORGE_SIMPLE_MODE config flag
   File: ghl_real_estate_ai/ghl_utils/jorge_config.py
   Add to JorgeSellerConfig: JORGE_SIMPLE_MODE: bool = True
   This disables enterprise features (investor arbitrage, Voss negotiation, psychology, drift detection)

A3. Gate enterprise branches in seller engine behind JORGE_SIMPLE_MODE
   File: ghl_real_estate_ai/services/jorge/jorge_seller_engine.py
   Method: _generate_seller_response (starts ~line 615)
   Create _generate_simple_response() that ONLY does:
   - Hot → handoff message
   - Vague streak >= 2 → take-away close
   - Questions < 4 → next question (or confrontational follow-up if vague)
   - Questions = 4 but not hot → warm acknowledgment
   Add guard at top of _generate_seller_response: if self.config.JORGE_SIMPLE_MODE → call simple method

A4. Remove duplicate arbitrage code
   File: ghl_real_estate_ai/services/jorge/jorge_seller_engine.py
   Lines ~860-900 are an exact copy of ~791-831. Delete the duplicate block.

A5. Add opt-out message detection in webhook
   File: ghl_real_estate_ai/api/routes/webhook.py
   Insert BEFORE the Jorge seller mode check (~line 158)
   Detect: "stop", "unsubscribe", "don't contact", "remove me", "not interested", etc.
   Action: Apply "AI-Off" tag, return exit message "No problem at all, reach out whenever you're ready"

A6. Add initiate-qualification endpoint
   File: ghl_real_estate_ai/api/routes/webhook.py
   New endpoint: POST /api/ghl/initiate-qualification
   Accepts: contact_id, location_id
   Fetches contact from GHL, sends opening message: "Hey [name], saw your property inquiry. Are you still thinking about selling?"

A7. Verify tone engine
   File: ghl_real_estate_ai/services/jorge/jorge_tone_engine.py
   Read and verify emoji removal, hyphen removal, 160 char limit, softening language removal.
   Fix only if broken.

RULES:
- Update JORGE_TASKS.md status as you complete each task
- Do NOT add features beyond what's listed
- Do NOT refactor surrounding code
- Keep changes minimal and surgical
- Test imports after changes: python -c "from ghl_real_estate_ai.api.routes.webhook import router"
```

---

## STREAM B: Buyer Bot & Lead Bot

```
You are working on the EnterpriseHub project to finalize Jorge's buyer and lead bots for delivery.

BEFORE DOING ANYTHING:
1. Read /Users/cave/Documents/GitHub/EnterpriseHub/JORGE_SPEC.md (full specification)
2. Read /Users/cave/Documents/GitHub/EnterpriseHub/JORGE_TASKS.md (task list — you own Stream B)

YOUR TASKS (Stream B):

B1. Verify buyer bot imports and instantiation
   File: ghl_real_estate_ai/agents/jorge_buyer_bot.py
   Run: python -c "from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot; print('OK')"
   Fix any import errors. Verify the class can be instantiated.

B2. Test buyer bot 6-node workflow end-to-end
   File: ghl_real_estate_ai/agents/jorge_buyer_bot.py
   Create a quick test script that:
   - Instantiates JorgeBuyerBot
   - Invokes the workflow with a mock BuyerBotState (simulating "I want a 4bd house in Rancho Cucamonga under 700k")
   - Verifies it produces a sensible response without errors
   Fix any runtime issues found.

B3. Add Rancho Cucamonga sample property data
   Create: ghl_real_estate_ai/data/sample_properties.json
   Include 13 properties across 3 tiers:
   - Entry ($500-700k): 5 properties in Victoria, Haven, Central Park
   - Mid ($700k-1.2M): 5 properties in Etiwanda, Terra Vista
   - Luxury ($1.2M+): 3 properties in Alta Loma, Day Creek
   Each property: id, address, price, beds, baths, sqft, condition, neighborhood, description (1 line)

B4. Wire PropertyMatcher to sample data
   File: ghl_real_estate_ai/services/property_matcher.py
   Read the current PropertyMatcher class.
   Add a method or modify existing match logic to load from sample_properties.json as a fallback when no external data source is available.
   The matcher should filter by: price range (budget ± 20%), beds, neighborhood preference.
   Return top 3 matches formatted for SMS (address, price, beds/baths, one-line description).

B5. Add buyer follow-up sequence config
   File: ghl_real_estate_ai/ghl_utils/jorge_config.py
   Add buyer-specific config:
   - BUYER_FOLLOWUP_SCHEDULE = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29]
   - BUYER_LONGTERM_INTERVAL = 14
   - BUYER_TEMPERATURE_TAGS = {"hot": "Hot-Buyer", "warm": "Warm-Buyer", "cold": "Cold-Buyer"}

B6. Verify lead bot intent routing
   File: ghl_real_estate_ai/agents/lead_bot.py
   Verify the intent decoder correctly identifies buyer vs seller intent.
   Test with sample messages: "I want to sell my house" → seller, "Looking for a 3 bedroom" → buyer
   Fix routing if broken.

RULES:
- Update JORGE_TASKS.md status as you complete each task
- Do NOT add enterprise features
- Keep PropertyMatcher changes backward-compatible (fallback only)
- Sample properties should be realistic Rancho Cucamonga data
- Test imports after changes
```

---

## STREAM C: Dashboard

```
You are working on the EnterpriseHub project to create Jorge's delivery dashboard.

BEFORE DOING ANYTHING:
1. Read /Users/cave/Documents/GitHub/EnterpriseHub/JORGE_SPEC.md (Section 5: Dashboard)
2. Read /Users/cave/Documents/GitHub/EnterpriseHub/JORGE_TASKS.md (task list — you own Stream C)

YOUR TASKS (Stream C):

C1-C6: Create a single file: ghl_real_estate_ai/streamlit_demo/jorge_delivery_dashboard.py

This dashboard has 4 tabs:

TAB 1 — Lead Pipeline:
- Funnel visualization: New → Qualifying → Hot / Warm / Cold
- Count per stage (use st.metric)
- Conversion rates between stages
- Data source: Try to import AnalyticsService. If unavailable, use clearly labeled sample data.

TAB 2 — Bot Activity:
- Table of recent conversations (last 20): contact name, last message, timestamp, temperature
- Metrics row: messages today, messages this week, avg response time, bot status
- Data source: Try ConversationManager or AnalyticsService. Fallback to sample data.

TAB 3 — Temperature Map:
- Plotly pie/donut chart: Hot (red) vs Warm (orange) vs Cold (blue)
- Line chart: temperature trend over last 30 days
- Table: Hot leads requiring immediate action (name, phone, questions answered, last contact)
- Data source: Try AnalyticsService. Fallback to sample data.

TAB 4 — Follow-Up Queue:
- Table: Upcoming follow-ups (next 7 days): name, temperature, scheduled date, follow-up #
- Table: Overdue follow-ups (past due): name, days overdue, last contact
- Metric: Follow-up completion rate
- Data source: Try follow-up scheduler service. Fallback to sample data.

DESIGN REQUIREMENTS:
- Clean, professional look — white/light background
- Standard Streamlit components (st.tabs, st.metric, st.dataframe, st.plotly_chart)
- Plotly for charts (already in requirements)
- NO "Obsidian" or "Elite" theming — keep it simple
- NO enterprise features (compliance, Voss, psychology, etc.)
- Any sample/mock data must be clearly labeled with st.info("Showing sample data — connect GHL for live data")
- Dashboard title: "Jorge AI Bot — Command Center"
- Add a launch mechanism: can be run with `streamlit run ghl_real_estate_ai/streamlit_demo/jorge_delivery_dashboard.py`

REFERENCE EXISTING CODE:
- Look at ghl_real_estate_ai/streamlit_demo/components/bot_health_monitoring_dashboard.py for how existing dashboards fetch data
- Look at ghl_real_estate_ai/services/analytics_service.py for the AnalyticsService API
- Look at ghl_real_estate_ai/streamlit_demo/components/jorge_analytics_dashboard.py for existing Jorge analytics patterns

RULES:
- Update JORGE_TASKS.md status as you complete each task
- Single file, 300-500 lines max
- No new dependencies — use only what's in requirements.txt
- Graceful degradation: if any service import fails, show sample data with a notice
```

---

## STREAM D: Testing & Packaging (Start after A+B complete)

```
You are working on the EnterpriseHub project to test Jorge's bots and create the delivery package.

BEFORE DOING ANYTHING:
1. Read /Users/cave/Documents/GitHub/EnterpriseHub/JORGE_SPEC.md (full specification)
2. Read /Users/cave/Documents/GitHub/EnterpriseHub/JORGE_TASKS.md (task list — you own Stream D)
3. WAIT until Stream A and Stream B tasks are marked DONE before starting D1-D4

YOUR TASKS (Stream D):

D1. Create seller bot E2E test
   File: tests/test_jorge_delivery.py (new)

   Test class: TestSellerQualificationFlow
   - Mock GHL webhook payload with "Needs Qualifying" tag
   - Simulate 5-message conversation (see JORGE_SPEC.md Section 9)
   - Verify: correct question sequence, temperature = "hot" at end, correct tags applied
   - Verify: response messages are < 160 chars, no emojis, no hyphens

D2. Create opt-out test
   Same file, class: TestOptOutHandling
   - Send message "stop" from contact with "Needs Qualifying" tag
   - Verify: "AI-Off" tag applied, exit message returned, no further bot processing
   - Test variants: "unsubscribe", "don't contact me", "not interested"

D3. Create edge case tests
   Same file, class: TestEdgeCases
   - Vague answer: verify confrontational follow-up generated
   - Multi-answer: verify bot skips ahead correctly
   - No response: verify follow-up scheduling triggers
   - Off-topic: verify bot redirects to next question

D4. Test tone compliance
   Same file, class: TestToneCompliance
   - Generate 10+ sample messages through the tone engine
   - Verify: no emojis (regex check), no hyphens, < 160 chars
   - Verify: no AI-sounding phrases ("I'd be happy to", "Thank you for sharing", "That's a great question")
   - Verify: messages use Jorge's style (direct, casual, confrontational)

D5. Write deployment guide
   File: JORGE_DEPLOYMENT_GUIDE.md (new)
   Structure:
   1. Prerequisites (Python 3.11+, GHL account, API keys)
   2. Environment setup (.env configuration — list required vars)
   3. GHL webhook configuration (URL, method, headers)
   4. GHL workflow setup (Tag Applied → HTTP Request → /api/ghl/initiate-qualification)
   5. Required GHL tags to create manually (list all from JORGE_SPEC.md Section 6.1)
   6. Custom fields to create in GHL (list from JORGE_SPEC.md Section 6.4)
   7. Testing the bot (send test message, verify response)
   8. Accessing the dashboard (streamlit run command)
   9. Troubleshooting (common errors and fixes)

D6. Run all tests and verify
   Run: python -m pytest tests/test_jorge_delivery.py -v
   Fix any failures.
   Run: python -c "from ghl_real_estate_ai.api.routes.webhook import router" (verify imports)
   Run: streamlit run ghl_real_estate_ai/streamlit_demo/jorge_delivery_dashboard.py --server.headless true (verify dashboard starts)

RULES:
- Update JORGE_TASKS.md status as you complete each task
- Tests should use unittest.mock — no real API calls
- Deployment guide should be written for Jorge (non-technical, step-by-step)
- Keep test file under 400 lines
```

---

## Quick Reference: Which Chat Does What

| Chat | Stream | Tasks | Can Start | Blocked By |
|------|--------|-------|-----------|------------|
| Chat 1 | A — Seller Core | A1-A7 | Now | Nothing |
| Chat 2 | B — Buyer/Lead | B1-B6 | Now | Nothing |
| Chat 3 | C — Dashboard | C1-C6 | Now | Nothing |
| Chat 4 | D — Test/Package | D1-D6 | After A+B done | Streams A, B |
