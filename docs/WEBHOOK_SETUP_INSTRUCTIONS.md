# 🔗 Webhook Setup Instructions for Jorge

Once the system is live, we need to connect your GoHighLevel account to the "Brain".

## Step 1: Get Your Webhook URL
I will provide you with **two** URLs today:
1.  **Dashboard URL:** Where you see the analytics.
2.  **API URL:** Where GHL sends data (the "Engine Room").

For this step, use the **API URL**:
`https://[YOUR-API-URL].up.railway.app/api/webhooks/ghl`

*(I will confirm the exact URL once deployment finishes in ~10 mins)*

## Step 2: Add to GHL Workflow
1.  Log in to **GoHighLevel** > **Automation** > **Workflows**.
2.  Find (or create) the workflow for **"Needs Qualifying"**.
    *   *Trigger:* Contact Tag Added -> "Needs Qualifying"
3.  Add an Action: **Webhook**.
4.  Paste the URL from Step 1.
5.  **Method:** POST.
6.  **Save** and **Publish**.

## Step 3: Test It
1.  Go to **Contacts**.
2.  Select a test contact (e.g., yourself).
3.  Add the tag **"Needs Qualifying"**.
4.  Wait 10-30 seconds.
5.  Check the "Notes" section or "Conversation" tab in GHL. You should see the AI analysis or a reply!
