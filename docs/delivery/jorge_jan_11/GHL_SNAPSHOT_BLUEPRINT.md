# 🏗️ GHL Technical Blueprint: Conversion Engine Snapshot

**Goal:** One-click deployment for new Jorge Salas clients.

### 1. Custom Fields (Data Collection)
Add these fields to your GHL Settings to allow the AI to sync data:
- **AI_Lead_Score:** (Number) 0-7 based on qualifying questions.
- **AI_Qualification_Notes:** (Large Text) Summary of lead motivation/timeline.
- **Preferred_Location:** (Text) Extracted area of interest.
- **Budget_Range:** (Text) Extracted price range.
- **Buyer_Portal_Link:** (URL) The unique link generated for that lead.

### 2. Custom Tags (Control Logic)
- **Needs Qualifying:** Starts the AI conversation.
- **AI-Off:** Kills the AI immediately (Manual takeover).
- **Hot-Lead:** Automatically added when score >= 3.
- **Match-Found:** Added when a property match is detected.

### 3. Workflow Triggers
- **Trigger:** Contact Tag Added → `Needs Qualifying`.
- **Action:** Webhook → URL: `https://your-railway-app.railway.app/ghl/webhook`.
- **Trigger:** Contact Tag Added → `AI-Off`.
- **Action:** Remove from all AI Workflows.

### 4. Smart Lists (The 'Hit List')
Create these lists for your agents:
- **🔥 AI Hot Leads:** Filter: Tag is `Hot-Lead` AND Tag is NOT `Appointment Booked`.
- **🕵️ AI Ghost Leads:** Filter: Tag is `Needs Qualifying` AND Last Outgoing Message > 24 hours ago.
