# 🚀 Deployment Guide for Jorge Salas
## GHL Real Estate AI - Complete Setup Instructions

**Last Updated:** January 6, 2026  
**Estimated Setup Time:** 30-45 minutes

---

## 📋 Overview

This guide will walk you through deploying your GHL Real Estate AI system. You'll have:

1. **Streamlit Demo App** - Showcase your AI capabilities to clients
2. **GHL Webhook Backend** - Automated lead qualification via SMS
3. **Multi-tenant Setup** - Easy to add new sub-accounts

---

## 🎯 Part 1: Deploy the Streamlit Demo (Railway)

### Step 1: Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project"
3. Sign in with GitHub (recommended)

### Step 2: Connect Your GitHub Repository

1. Fork or clone the repository to your GitHub account
2. In Railway, click "Deploy from GitHub repo"
3. Select `enterprisehub/ghl_real_estate_ai`
4. Railway will auto-detect it's a Python/Streamlit app

### Step 3: Configure Environment Variables

In Railway project settings, add these variables:

```env
# Anthropic API (for AI features)
ANTHROPIC_API_KEY=your_anthropic_key_here

# GHL API (for webhook integration)
GHL_API_KEY=your_ghl_api_key_here
GHL_WEBHOOK_SECRET=your_secret_here

# App Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

**⚠️ Where to get these keys:**

- **Anthropic API Key:** 
  - Go to [console.anthropic.com](https://console.anthropic.com)
  - Sign up and navigate to API Keys
  - Create a new key (starts with `sk-ant-...`)
  
- **GHL API Key:**
  - Log into your GHL Agency account
  - Go to Settings → Integrations → API
  - Generate a new API key

### Step 4: Set Start Command

In Railway settings, set the start command:

```bash
streamlit run streamlit_demo/app.py --server.port=$PORT
```

### Step 5: Deploy

1. Click "Deploy"
2. Wait 2-3 minutes for build
3. Railway will give you a public URL like: `https://your-app-name.up.railway.app`

✅ **Your demo is now live!**

---

## 🔗 Part 2: Deploy the Webhook Backend (Same Railway Project)

### Step 1: Add Webhook Service

1. In your Railway project, click "New Service"
2. Select "Deploy from GitHub repo" (same repo)
3. Name it "ghl-webhook-backend"

### Step 2: Configure Webhook Settings

Add these environment variables (same as above, plus):

```env
# Webhook specific
PORT=8000
WEBHOOK_PATH=/webhook/ghl
```

### Step 3: Set Webhook Start Command

```bash
uvicorn services.ghl_webhook_service:app --host 0.0.0.0 --port $PORT
```

### Step 4: Get Your Webhook URL

After deployment, Railway gives you a URL like:
```
https://ghl-webhook-backend.up.railway.app
```

Your webhook endpoint will be:
```
https://ghl-webhook-backend.up.railway.app/webhook/ghl
```

✅ **Backend is deployed!**

---

## ⚙️ Part 3: Connect GHL to Your Webhook

### Step 1: Create AI Assistant Tags in GHL

1. Log into your GHL account
2. Go to Settings → Tags
3. Create two new tags:
   - `AI Assistant: ON`
   - `AI Assistant: OFF`

### Step 2: Create the Webhook Automation

1. Go to Automations → Create New Workflow
2. Name it: "AI Lead Qualification"

**Trigger Configuration:**
- **Trigger:** Contact Changed
- **Filter 1:** Tag "AI Assistant: ON" is added
- **Filter 2:** Tag "AI Assistant: OFF" is NOT present

**Action Configuration:**
- **Action:** Send Webhook
- **URL:** `https://ghl-webhook-backend.up.railway.app/webhook/ghl`
- **Method:** POST
- **Headers:**
  ```json
  {
    "Content-Type": "application/json",
    "X-GHL-Signature": "{{signature}}"
  }
  ```
- **Body:**
  ```json
  {
    "contactId": "{{contact.id}}",
    "locationId": "{{contact.location_id}}",
    "tags": {{contact.tags}},
    "customFields": {{contact.custom_fields}},
    "type": "ContactTagUpdate"
  }
  ```

### Step 3: Set Up Response Webhook

Create a second automation to handle incoming SMS responses:

1. **Trigger:** Inbound Message Received
2. **Filter:** From contacts with tag "AI Assistant: ON"
3. **Action:** Send Webhook
   - **URL:** `https://ghl-webhook-backend.up.railway.app/webhook/ghl/response`
   - **Body:**
     ```json
     {
       "contactId": "{{contact.id}}",
       "locationId": "{{contact.location_id}}",
       "message": "{{message.body}}",
       "timestamp": "{{message.date_added}}"
     }
     ```

✅ **GHL is now connected!**

---

## 🧪 Part 4: Test Your Setup

### Test 1: Manual Tag Test

1. Find a test contact in GHL
2. Add tag "AI Assistant: ON"
3. Within 10 seconds, the contact should receive an SMS with the first qualifying question

### Test 2: Response Test

1. Reply to the AI's SMS from your phone
2. AI should respond with the next question
3. Check the contact's tags - they should update based on answers (Hot/Warm/Cold)

### Test 3: Handoff Test

1. Answer 3+ qualifying questions
2. Your score should reach 70+
3. AI should send a handoff message
4. Tag "Hot Lead" should be added
5. Tag "AI Assistant: OFF" should be added (AI disengages)

---

## 🔐 Security Checklist

Before going live:

- [ ] All API keys stored in environment variables (not in code)
- [ ] GHL webhook signature verification enabled
- [ ] HTTPS enforced on Railway (enabled by default)
- [ ] Rate limiting configured (prevents abuse)
- [ ] Logs don't expose sensitive data

---

## 🌐 Part 5: Multi-Tenant Setup (For Sub-Accounts)

### For Each New Sub-Account:

1. **In GHL:** 
   - Create the "AI Assistant: ON/OFF" tags in the sub-account
   - Clone the automation workflows
   - Update webhook URLs to point to your Railway backend

2. **In Your Backend:**
   - No code changes needed!
   - The `locationId` field automatically isolates data per sub-account
   - Each sub-account's contacts are handled independently

### Easy Template Approach:

1. Export your automation as a template in GHL
2. Share template with team
3. They import it into their sub-account
4. Update the webhook URL (same for all)
5. Done! ✅

---

## 📊 Monitoring & Logs

### View Railway Logs:

1. Go to Railway dashboard
2. Click on your service
3. Click "Deployments" → "View Logs"

### What to Look For:

✅ **Good Logs:**
```
INFO: SMS sent to contact abc123
INFO: Contact abc123 - Score: 85 (Hot), Answers: 4
INFO: Lead abc123 is HOT (score: 85) - handing off to human
```

❌ **Error Logs:**
```
ERROR: Failed to send SMS: API key invalid
ERROR: Anthropic API error: Rate limit exceeded
```

---

## 🆘 Troubleshooting

### Issue: "Webhook not triggering"

**Solutions:**
1. Check GHL automation is published (not in draft)
2. Verify webhook URL is correct (no typos)
3. Test webhook manually with Postman or curl
4. Check Railway logs for incoming requests

### Issue: "AI not responding"

**Solutions:**
1. Verify `ANTHROPIC_API_KEY` is set correctly
2. Check API key has available credits
3. Look for errors in Railway logs
4. Test AI endpoint directly: `https://your-backend.up.railway.app/`

### Issue: "Wrong lead score"

**Solutions:**
1. Check scoring logic in `ghl_webhook_service.py`
2. Verify answers are being stored correctly
3. Review logs for answer extraction

### Issue: "Multiple sub-accounts interfering"

**Solutions:**
1. Verify `locationId` is being passed in webhook
2. Check state isolation in backend code
3. Use Redis or database for production (not in-memory dict)

---

## 📞 Support

If you run into issues:

1. **Check Logs First:** Most issues show up in Railway logs
2. **Test Endpoints:** Use Postman to test webhook endpoints directly
3. **Review Documentation:** Re-read relevant sections above
4. **Contact Support:** [Your support email/contact]

---

## 🎉 Success Checklist

Before marking deployment as complete:

- [ ] Demo app loads at Railway URL
- [ ] Webhook backend responds to health check
- [ ] GHL automation fires when tag added
- [ ] AI sends first qualifying question
- [ ] AI responds to contact replies
- [ ] Lead score updates correctly (Hot/Warm/Cold)
- [ ] Handoff triggers at score 70+
- [ ] Tags update in GHL appropriately
- [ ] Tested with 3+ test contacts
- [ ] Multi-tenant isolation verified

---

## 🚀 Next Steps

Once deployed:

1. **Train Your Team:** Show them how to use the demo
2. **Create Training Videos:** Record walkthroughs
3. **Set Up Monitoring:** Add uptime alerts (Railway has built-in)
4. **Scale Up:** Add more qualifying questions as needed
5. **Iterate:** Improve AI tone based on feedback

---

**Deployment Complete!** 🎊

Your GHL Real Estate AI system is now live and ready to qualify leads automatically.

**Questions?** Review the troubleshooting section or check Railway logs.
