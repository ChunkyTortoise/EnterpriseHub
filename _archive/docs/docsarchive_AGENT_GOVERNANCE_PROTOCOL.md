# Agent Governance & Safety Protocol
## "The Guardrails"

Autonomous agents are powerful but risky. This protocol defines the **Hard Limits** and **Safety Switches** required for production deployment of the GHL Real Estate AI.

---

## 1. Operational Limits (The Kill Switches)

### 💰 Cost Control
*   **Per-Session Cap:** Max $1.00 USD (approx. 50 messages/turns).
*   **Daily Global Cap:** Max $50.00 USD across all agents.
*   **Action:** If cap hit -> Soft Fail (reply: "I need to pause for a moment, a human will contact you.") -> Alert Admin.

### 🔄 Loop Prevention
*   **Max Turns:** 15 turns per conversation session.
*   **Repetition Detector:** If Agent outputs the exact same string 2x in a row -> **Force Stop** and trigger `Reflexion` with "You are looping."
*   **Tool Loop:** If Agent calls the same tool with same args 3x -> **Force Stop**.

### ⏱️ Latency Guardrail
*   **Timeout:** If Agent "Thinks" for > 30 seconds -> Cancel and fallback to "I'm checking on that, give me a sec."
*   **Reason:** Prevents hanging connections on SMS/Voice channels.

---

## 2. Human-in-the-Loop (HITL) Triggers

The Agent **MUST** hand off to a human (`works_with` Agent) immediately if:

1.  **Sentiment Redline:** User uses profanity, expresses extreme anger, or threatens legal action.
    *   *Detection:* NLP Sentiment Score < -0.7 or Keyword List (`lawsuit`, `sue`, `lawyer`, `scam`).
2.  **Complexity Cliff:** User asks a question the Knowledge Base doesn't cover (RAG Confidence < 0.4).
3.  **Transaction Milestone:** User says "I want to make an offer" or "Send me the contract."
    *   *Policy:* Agents NEVER write contracts. They only schedule the human to do it.
4.  **Emergency/Safety:** User mentions physical danger or emergency.
    *   *Action:* Reply with emergency resources override; stop agent.

---

## 3. Data Privacy & Security (PII)

*   **Redaction:** All logs sent to LLM providers (Anthropic/OpenAI) **MUST** have PII (Phone, Email, Address) masked unless strictly necessary for the tool.
    *   *Pattern:* `+1 (555) 000-0000` -> `<PHONE_REDACTED>`
*   **Retention:** Chat logs stored in plain text for max 30 days, then encrypted/archived.
*   **Access:** Only Admins (Role: `admin`) can view raw chat logs. Agents (Role: `agent`) view summarized memory.

---

## 4. Deployment "Go/No-Go" Checklist

Before enabling the Agent on a live GHL sub-account:

*   [ ] **Budget Set:** OpenAI/Anthropic limits configured.
*   [ ] **Alerts Configured:** Slack/Email webhook for "HITL Trigger" verified.
*   [ ] **Knowledge Base Verified:** `market_intel_scraper` ran successfully today.
*   [ ] **Golden Set Pass:** Passed `AGENT_EVALUATION_PROTOCOL` with score > 4.0.
*   [ ] **Legal Disclaimer:** First message includes "I am an AI assistant" (Transparency Law compliance).
