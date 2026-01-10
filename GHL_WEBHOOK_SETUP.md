# 🔗 GHL Webhook Tunneling Setup Guide

To connect Jorge's live GoHighLevel (GHL) account to the AI Lead Qualification system, you need to expose your local webhook service to the internet using a tunnel (e.g., ngrok).

## 🚀 Step 1: Start the Webhook Service

Run the FastAPI webhook service from the project root:

```bash
# Install dependencies if needed
pip install fastapi uvicorn httpx anthropic

# Start the service
python3 ghl_real_estate_ai/streamlit_demo/services/ghl_webhook_service.py
```

The service will be running at `http://localhost:8000`.

## 🌐 Step 2: Create a Tunnel with ngrok

If you don't have ngrok installed, get it at [ngrok.com](https://ngrok.com/).

```bash
# Create a tunnel to port 8000
ngrok http 8000
```

Copy the **Forwarding URL** provided by ngrok (e.g., `https://a1b2-c3d4.ngrok-free.app`).

## ⚙️ Step 3: Configure GoHighLevel

1.  Log in to the **Jorge Salas** GHL Agency or Sub-account.
2.  Go to **Automation** -> **Workflows**.
3.  Create a new Workflow or Edit an existing one.
4.  **Trigger:** Add a trigger like "Contact Tag Added" (Tag: `AI Assistant: ON`).
5.  **Action:** Add a "Webhook" action.
6.  **Method:** POST
7.  **URL:** Paste your ngrok URL followed by `/webhook/ghl` (e.g., `https://a1b2-c3d4.ngrok-free.app/webhook/ghl`).
8.  **Save** and **Publish** the workflow.

## 🧪 Step 4: Test the Connection

1.  Pick a test contact in GHL.
2.  Add the tag `AI Assistant: ON`.
3.  Check your ngrok logs and the webhook service output.
4.  The AI should automatically send the first qualifying question to the contact via GHL.

## 🔒 Security Note

- The service uses `GHL_WEBHOOK_SECRET` to verify signatures from GHL.
- Ensure this secret matches the one configured in GHL if you're using signature verification.
- For local development, if `GHL_WEBHOOK_SECRET` is not set, signature verification is skipped.

---

**Jorge's AI is now connected to live GHL events! 🧠⚡**
