# User Acceptance Testing (UAT) Scenarios: EnterpriseHub Phase 5

This document outlines the specific scenarios Jorge Salas should use to verify the "Stall-Breaker", "War Room", and "CMA Engine" features in the EnterpriseHub Dashboard.

## Prerequisites
- Dashboard URL: `http://localhost:8501` (or your production URL)
- Retell AI API Key (optional, for live calls)

---

## Scenario 1: The "Zillow-Defense" CMA Trigger
**Goal:** Verify that the system detects price objections and automatically generates a "Zillow-Defense" CMA.

1.  Navigate to the **Intent Analysis** tab.
2.  In the **Lead Message** box, enter:
    > "I'm thinking about selling, but Zillow says my house is worth $850k. I don't think I can get that much right now."
3.  Click **Analyze Intent**.
4.  **Verification:**
    - The FRS score should show the lead as **Price-Aware**.
    - The system should automatically trigger the CMA generation (look for "Generating CMA" in terminal logs or a PDF link in the response mock).
    - Note the `Zillow Variance` in the generated report.

---

## Scenario 2: The "Day 7" Stall-Breaker Call
**Goal:** Verify that the "Ghost-in-the-Machine" sequence initiates a voice call when a lead stops responding.

1.  Navigate to the **Tactical Lead Pipeline** tab.
2.  Find a lead marked as **Ghosted** (or simulate one in the pipeline).
3.  Open the **Voice AI** tab.
4.  Enter the lead's phone number and click **Start AI Call**.
5.  **Verification:**
    - If a Retell API key is configured, your phone should ring.
    - The AI agent should use a "Stall-Breaker" script, e.g., *"Zillow's algorithm doesn't know your kitchen was just renovated..."*
    - The Dashboard should show the call status as **Active** or **Success**.

---

## Scenario 3: The Jorge War Room (Market Heat)
**Goal:** Verify geographic lead clustering and "Hot Property" identification.

1.  Navigate to the **War Room** tab.
2.  Review the **Property Heat Map**.
3.  **Verification:**
    - You should see markers clustered around Austin, TX (or your local market).
    - Red markers indicate "Hot" properties where multiple leads have high FRS scores.
    - Click a marker to see the **Highest FRS** and **Lead Count**.
    - Review the **Lead Relationships** graph on the right to see which leads are connected to which properties.

---

## Scenario 4: Intent Decoder (FRS/PCS)
**Goal:** Verify the Lead Health scoring system.

1.  In the **Neural Scoring** tab, enter lead data:
    - **Budget:** $950,000
    - **Timeline:** 30 days
2.  Click **Analyze Lead**.
3.  **Verification:**
    - The **Intent Strength** and **Financial Readiness** bars should be high (>= 80%).
    - The **Recommended Actions** should include "Call within 1 hour".
    - The **Talking Points** should specifically reference the budget and timeline.

---

## Scenario 5: Jorge Persona // Seller Bot
**Goal:** Verify Jorge's confrontational qualification and stall-breaking tone.

1.  Navigate to the **Seller Bot** tab.
2.  In the **Seller Message** box, enter:
    > "I'm interested in selling, but I'm really busy right now. Can you call me in two weeks?"
3.  Click **Engage Jorge Persona**.
4.  **Verification:**
    - The system should detect a **STALL (get_back)**.
    - The strategy should pivot to **CONFRONTATIONAL**.
    - Jorge's response should challenge the lead, e.g., *"I appreciate it, but I need to know: are you actually selling, or just exploring? If you're serious, we talk today..."*

---

## Success Criteria
- [ ] CMA PDF links are generated and clickable.
- [ ] Voice AI calls initiate without blocking the Dashboard UI.
- [ ] War Room heatmap correctly visualizes lead density.
- [ ] FRS/PCS scores accurately reflect the lead's linguistic signals.
