# Jorge AI Bot — Setup Guide

This guide walks you through getting the Jorge AI seller bot running and connected to your GoHighLevel account.

---

## Step 1: Prerequisites

Before you start, make sure you have:

- **Python 3.11 or newer** installed on your server
- A **GoHighLevel** (GHL) account with API access
- Your GHL **API key** and **Location ID** (find these in GHL > Settings > Business Profile)
- A server or hosting environment that can receive webhooks (e.g., Railway, Render, or any VPS)

---

## Step 2: Environment Variables

Create a `.env` file in the project root with these values:

```
# Required — GHL Integration
GHL_API_KEY=your_ghl_api_key_here
GHL_LOCATION_ID=your_location_id_here

# Required — AI Provider
ANTHROPIC_API_KEY=your_claude_api_key_here

# Required — Jorge Bot Activation
JORGE_SELLER_MODE=true

# Optional — Webhook Security
WEBHOOK_SECRET=your_webhook_secret_here

# Optional — Notification Workflow
HOT_SELLER_WORKFLOW_ID=your_workflow_id_here

# Optional — Database
DATABASE_URL=postgresql://user:pass@localhost:5432/enterprisehub

# Optional — Redis Cache
REDIS_URL=redis://localhost:6379/0
```

**Important**: Never share your `.env` file or commit it to git.

---

## Step 3: Install and Start the Server

Open a terminal in the project folder and run:

```bash
pip install -r requirements.txt
```

Then start the API server:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Your server is now running at `http://your-server-ip:8000`.

To verify it's working, open this URL in your browser:

```
http://your-server-ip:8000/api/ghl/health
```

You should see: `{"status": "healthy"}`

---

## Step 4: GHL Webhook Configuration

This connects GHL to the bot so incoming messages get processed.

1. In GHL, go to **Settings > Webhooks**
2. Click **Add Webhook**
3. Set the URL to: `https://your-server-domain.com/api/ghl/webhook`
4. Method: **POST**
5. Event: **Inbound Message** (or "Contact Reply")
6. Save

---

## Step 5: GHL Workflow Setup (Tag Triggers Bot)

This makes the bot automatically start when you tag a contact.

1. In GHL, go to **Automation > Workflows**
2. Click **Create Workflow**
3. Set trigger: **Tag Applied** > select **Needs Qualifying**
4. Add action: **HTTP Request**
   - Method: POST
   - URL: `https://your-server-domain.com/api/ghl/initiate-qualification`
   - Body (JSON):
     ```json
     {
       "contact_id": "{{contact.id}}",
       "location_id": "{{location.id}}"
     }
     ```
5. Save and **Publish** the workflow

Now when you add the "Needs Qualifying" tag to any contact, the bot will send the first message automatically.

---

## Step 6: Required GHL Tags

Create these tags in GHL (go to **Settings > Tags**). The bot uses them to track lead status:

| Tag | What It Means |
|-----|---------------|
| **Needs Qualifying** | Bot is active for this contact (you add this manually) |
| **Hot-Seller** | Seller answered all 4 questions, accepted timeline, high quality |
| **Warm-Seller** | Seller answered 3+ questions with decent quality |
| **Cold-Seller** | Seller gave vague answers or stopped responding |
| **AI-Off** | Bot is turned off (contact opted out or you manually stopped it) |
| **Qualified** | Handoff to human agent complete |
| **Stop-Bot** | Manual override to stop bot immediately |
| **Seller-Qualified** | Seller fully qualified and handed off |

**How it works**: Add "Needs Qualifying" to start the bot. The bot automatically adds Hot/Warm/Cold tags as it qualifies the lead. Add "AI-Off" or "Stop-Bot" to stop the bot at any time.

---

## Step 7: Custom Fields to Create in GHL

Create these custom fields in GHL (go to **Settings > Custom Fields**). The bot fills them automatically:

| Field Name | Type | What It Stores |
|-----------|------|----------------|
| seller_temperature | Text | hot, warm, or cold |
| seller_motivation | Text | Why they want to sell (from Question 1) |
| timeline_urgency | Text | Whether 30 to 45 day timeline works (from Question 2) |
| property_condition | Text | Move in ready or needs work (from Question 3) |
| price_expectation | Text | Their asking price (from Question 4) |
| questions_answered | Number | How many of the 4 questions they answered (0 to 4) |
| qualification_score | Number | Overall qualification score (0 to 100) |

---

## Step 8: Test the Bot

1. Pick a test contact in GHL (or create a new one)
2. Add the **Needs Qualifying** tag to that contact
3. The bot should send: "Hey [name], saw your property inquiry. Are you still thinking about selling?"
4. Reply as the contact with something like "Yes I'm thinking about it"
5. The bot should ask the first qualification question about motivation
6. Continue the conversation through all 4 questions
7. Check that the contact's custom fields and tags update correctly

**Tip**: To stop the bot on a test contact, add the "AI-Off" tag.

---

## Step 9: Access the Dashboard

The dashboard shows your lead pipeline, bot activity, and follow up queue.

Start it with:

```bash
streamlit run ghl_real_estate_ai/streamlit_demo/jorge_delivery_dashboard.py
```

Then open `http://your-server-ip:8501` in your browser.

The dashboard has 4 tabs:
- **Lead Pipeline**: See how contacts flow from New to Qualifying to Hot/Warm/Cold
- **Bot Activity**: Recent conversations and message counts
- **Temperature Map**: Visual breakdown of Hot vs Warm vs Cold leads
- **Follow Up Queue**: Upcoming and overdue follow ups

---

## Troubleshooting

### Bot does not send the first message
- Check that `JORGE_SELLER_MODE=true` is in your `.env` file
- Verify the GHL workflow (Step 5) is published and active
- Check that the webhook URL is correct and your server is running
- Look at server logs for errors: check the terminal where you ran `uvicorn`

### Bot does not respond to incoming messages
- Verify the webhook (Step 4) is configured with the correct URL
- Make sure the contact has the **Needs Qualifying** tag
- Make sure the contact does NOT have any of these tags: AI-Off, Qualified, Stop-Bot, Seller-Qualified
- Check the server logs for "AI not triggered" or error messages

### Bot responses sound robotic
- The tone engine automatically strips AI sounding language, emojis, and hyphens
- If responses still sound off, check server logs for "compliance" warnings
- The bot is set to Simple Mode by default, which uses the strict 4 question flow

### Tags not updating in GHL
- Verify your `GHL_API_KEY` has write permissions
- Check server logs for GHL API errors
- Make sure the tags from Step 6 exist in your GHL account

### Server won't start
- Make sure Python 3.11+ is installed: `python --version`
- Install dependencies: `pip install -r requirements.txt`
- Check that your `.env` file exists and has no typos
- If using a database, run migrations: `alembic upgrade head`

### Need to stop the bot for a contact
- Add the **AI-Off** tag to the contact in GHL
- Or add the **Stop-Bot** tag
- The bot will immediately stop processing that contact

---

## Quick Reference

| Action | How |
|--------|-----|
| Start bot for a contact | Add "Needs Qualifying" tag in GHL |
| Stop bot for a contact | Add "AI-Off" or "Stop-Bot" tag in GHL |
| Check bot status | Visit /api/ghl/health |
| View dashboard | `streamlit run ghl_real_estate_ai/streamlit_demo/jorge_delivery_dashboard.py` |
| View server logs | Check terminal running uvicorn |
| Run tests | `python -m pytest tests/test_jorge_delivery.py -v` |
