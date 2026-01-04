GHL Real Estate AI - Quick Start Guide for Jorge

🚀 3-Step Setup (10 minutes total)

Step 1: Add Your Location (2 minutes)

1. Open the Admin Dashboard on your computer:
   
   streamlit run streamlit_demo/admin.py
   
   A dashboard will open in your browser.

2. Click "Tenant Management" button

3. Enter your location details:
  Location ID - Find in GHL (Settings → Business Profile)
  GHL API Key - Find in GHL (Settings → API & Integrations)
  Calendar ID (optional) - If you want AI to offer booking times

4. Click "Save Location"

Step 2: Connect the Webhook (5 minutes)

1. Go to your GHL Account → Workflows

2. Click "+ New Workflow"

3. Set it up:
  Name: AI Qualifying Bot
  Trigger: Contact receives tag → Needs Qualifying
  Action: Send Webhook
  URL: https://your-railway-url.app/ghl/webhook (Railway gives you this URL)
  Method: POST

4. Click Save

Step 3: Test It! (1 minute)

1. In GHL, pick a test contact

2. Add the tag: Needs Qualifying

3. Text them: _"I want to sell my house"_

4. The AI should respond automatically!



🎯 How to Control the AI

Turn AI ON
  Add tag: Needs Qualifying (buyer qualifying) or Hit List (seller qualifying)

Turn AI OFF
  Add tag: AI-Off or Qualified



🔥 Lead Scoring (What the AI Tracks)

The AI asks 7 key questions and scores leads automatically:

| Score | Status | GHL Tag | What It Means |
|-------|--------|---------|---------------|
| 3+ answers | HOT | Hot-Lead | Ready to move forward |
| 2 answers | WARM | Warm-Lead | Interested, needs more info |
| 0-1 answers | COLD | Cold-Lead | Just exploring |

The 7 Questions:
1. Budget/Price Range
2. Location Preference
3. Timeline (When moving?)
4. Beds/Baths or Home Condition
5. Financing (Pre-approved?)
6. Motivation (Why now?)
7. Wholesale or Full Listing?



🔄 Auto Follow-Up (If Lead Goes Silent)

If a lead doesn't respond:
  After 24 hours: AI sends: "Hey [name], just checking in - is this still a priority?"
  After 48 hours: AI sends: "Are you still interested or should we close your file?"



📅 Calendar Booking (Optional)

If you add a Calendar ID in Step 1, the AI will automatically offer booking times to HOT leads (3+ questions answered).



🔧 Troubleshooting

AI not responding to messages?
  ✓ Check the Needs Qualifying tag is on the contact
  ✓ Check the webhook URL is correct in GHL
  ✓ Check Railway logs for errors

Need to see logs?
  Go to your Railway dashboard and click "Logs"



✅ You're All Set!

The AI is now live. Start tagging contacts with Needs Qualifying or Hit List and watch it qualify them automatically.

Questions? Contact support or check Railway logs.
