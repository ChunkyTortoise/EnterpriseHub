# Proposal 5: AI Chatbot Developer Needed to Help Automate Support Chat

**Job**: Chatbot Developer Needed to Help Automate Support Chat
**Bid**: $55/hr | **Fit**: 7/10 | **Connects**: 8-12
**Status**: Ready when funded — no Connects available

---

## Cover Letter

You need a chatbot that actually deflects support tickets — not one that frustrates customers into opening more of them. The difference is a routing system that knows when to answer and when to hand off to a human.

I built that routing system for a production 3-bot real estate platform (jorge_real_estate_bots, 360+ tests): confidence scoring below 0.7 triggers escalation rather than a guess; circular handoff prevention blocks the same transfer within 30 minutes; rate limiting stops loops at 3 handoffs per hour. The system learns from outcome history to adjust thresholds dynamically. At 65% deflection — the industry benchmark for well-built systems — your support costs drop by over $3,600/month for a two-agent team. Live demo: https://ct-llm-starter.streamlit.app/

For your NopCommerce + Zoho SalesIQ setup, I'd build the AI layer as a standalone Python API your existing systems call via REST — no modifications to your core platforms:

| Week | Deliverables |
|------|-------------|
| **1-2** | Knowledge base ingestion pipeline + FastAPI scaffold (product docs, FAQs, support history) |
| **3-4** | Conversational flow engine + Zoho SalesIQ webhook integration |
| **5-6** | NopCommerce order lookup API + end-to-end tests + human handoff triggers |
| **7-8** | Monitoring dashboard, accuracy metrics, tuning from real conversations |

My docqa-engine (500+ tests) handles the knowledge base side with hybrid keyword + semantic search — it finds the right answer even when customers phrase things differently than your docs.

Available for a 15-minute call this week — or I can send a sample handoff-routing config so you can see exactly how the escalation logic works.

**GitHub**: https://github.com/ChunkyTortoise

---

## Rewrite Notes
- Key change: Removed the buried ROI projection (placed last in original) and moved the core value proposition — the routing system that knows when to escalate — to the hook; the $3,640/month savings figure is now embedded in the second paragraph where clients are still reading, not in a section they may never reach
- Hook used: "You need a chatbot that actually deflects support tickets — not one that frustrates customers into opening more of them."
- Demo linked: https://ct-llm-starter.streamlit.app/
- Estimated conversion lift: Original opened with a generic statement about what good chatbots need, then took three paragraphs to get to the routing system. Rewrite leads with the routing mechanism and embeds the ROI math immediately. The "sample handoff-routing config" CTA gives technical decision-makers something concrete to evaluate before scheduling a call.
