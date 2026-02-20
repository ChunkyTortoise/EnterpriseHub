# Today's Live Upwork Proposals — Feb 19, 2026

**Status**: READY TO SUBMIT (after buying connects)
**Connects available**: 2 (need 6-17 per proposal)

## ⚠️ BLOCKER: BUY CONNECTS FIRST

You only have **2 connects**. Go here → https://www.upwork.com/nx/buy-connects

- **80 connects = $12** — enough for 5-7 proposals at this budget level
- Job below costs **17 connects** to apply

Without this, none of these proposals can be submitted.

---

## Job #1 — BEST MATCH TODAY

**Title**: Payroll Automation via freee HR API
**URL**: https://www.upwork.com/jobs/Payroll-Automation-via-freee-API_~022024658793093381386/
**Budget**: $500 fixed-price
**Proposals**: 5-10 (good — not flooded yet)
**Client**: Japan/Tokyo | 4.45 stars | $18K total spent | 84% hire rate | Payment verified
**Cost to apply**: 17 connects
**Tier**: 1 — fully defined scope, trusted client, fixed price

### Why this wins
- Best-defined scope on Upwork today: specific columns (FB-FL), specific API target (freee HR), specific trigger (Send button)
- Client has done this before ($500 fixed job in Mar 2025, great review)
- 84% hire rate = they actually close
- Ongoing project → could become repeat work

### Scope summary (from reading the full job)
Extract from Google Sheet "FAIR Copy" (tab: January 2026) → map columns FB-FL (days, OT, night, salary, allowances, transportation, etc.) → format into "(Attendance & Payroll) Main" sheet → add a custom "Send" button → push to freee HR via REST API.

Tool required: **Google Apps Script (GAS)** — JavaScript-based, runs inside Google Sheets. Standard REST API calls.

---

### PROPOSAL — COPY AND PASTE

> **Your bid**: $500 (match listed budget exactly)
> **Delivery**: 2-3 days
> **Connects needed**: 17

---

I've read your full spec and this is exactly the kind of project I build.

The flow you're describing: extract columns FB–FL from "FAIR Copy" → format into your "Attendance & Payroll Main" sheet → trigger a push to freee HR via API with a custom "Send" button. I've mapped REST API payloads to structured data sources like this many times.

My approach:
1. Review the "(Attendance & Payroll) Main" sheet structure you've left as reference, and confirm the column mapping from FAIR Copy → Main
2. Build the GAS script: auto-populate Main from the January 2026 data, format it to match freee HR's expected payload
3. Add the custom "Send" button that calls the freee HR API endpoint with proper authentication and handles the response (success/error message back in the sheet)
4. Test end-to-end with the sample data, clean up edge cases, document the script

Delivery: working version by Feb 21. I'll include a brief explanation of the code so your team can modify the column mapping if your sheet structure changes.

One question: does the freee HR API use OAuth 2.0 or a simple API key? If you have the API docs or a sandbox token, we can skip the auth setup step and go straight to data mapping.

---

## Job #2 — BACKUP (Run this search tomorrow)

The Delivery Automation ($400 fixed) was skipped today due to unverified payment. Recheck tomorrow — client may have verified by then.

**URL**: https://www.upwork.com/jobs/Delivery-Automation-Forms-Sheets-Make-Route-App_~022024654971402960138/

---

## What to Search Tomorrow (Second Round)

The chatbot and GHL searches today didn't return good Tier 1 fixed-price matches. Run these tomorrow morning:

### Search 1 — CSV/Excel Automation (high hit rate)
```
https://www.upwork.com/nx/search/jobs/?q=CSV+automation+python&sort=recency&job_type=fixed&budget=100,800
```

### Search 2 — API Integration (quick wins)
```
https://www.upwork.com/nx/search/jobs/?q=API+integration+webhook&sort=recency&job_type=fixed&budget=100,800
```

### Search 3 — n8n / Make automation (growing category)
```
https://www.upwork.com/nx/search/jobs/?q=n8n+automation+setup&sort=recency&job_type=fixed&budget=100,800
```

### Search 4 — Zapier replacement (clients ready to pay)
```
https://www.upwork.com/nx/search/jobs/?q=zapier+automation+python&sort=recency&job_type=fixed&budget=100,800
```

### Search 5 — GHL (try narrower scope)
```
https://www.upwork.com/nx/search/jobs/?q=GoHighLevel+workflow+setup&sort=recency&job_type=fixed&budget=100,1000
```

---

## Today's Search Results Summary

| Job | Budget | Type | Proposals | Client | Verdict |
|-----|--------|------|-----------|--------|---------|
| Payroll Automation (freee HR API) | $500 | Fixed | 5-10 | ⭐ $18K spent, 84% hire | **BID** |
| Delivery Automation (Forms→Sheets→Make) | $400 | Fixed | 5-10 | ⚠️ Unverified payment | Skip today |
| AI-Powered Website Scraping Tool | — | Hourly | — | Unverified | Skip |
| AI Automation for Financial Statements | $19-40/hr | Hourly | 5-10 | Unverified | Skip |
| MVP Tool for Data Scraping & Scoring | $2,000 | Fixed | 10-15 | New UK client | Too big |
| Raspberry Pi Email→Printer | $20-40/hr | Hourly | 5-10 | New UK client | Skip |
| GHL Expert (featured) | $8/hr | Hourly | 15-20 | Established | Rate too low |
| FastAPI Invoice Scanner (featured) | Hourly | Hourly | 15-20 | Strong client | Too crowded |
| Chatbot (Twilio+LangGraph+RAG) | $30 | Fixed | <5 | Canada | $30 for 3 weeks work — skip |

---

## Immediate Action Checklist

- [ ] **Buy 80 connects ($12)** → https://www.upwork.com/nx/buy-connects
- [ ] **Submit Job #1 proposal** (copy from above, check freee HR API docs first if possible)
- [ ] **Run tomorrow's searches** (new jobs posted overnight — biggest opportunity window)

---

## Notes on Connects Usage Going Forward

| Job Budget | Connects Cost |
|-----------|---------------|
| Fixed < $500 | 6 connects |
| Fixed $500-$999 | 8-12 connects |
| Fixed $1K-$4.9K | 12-16 connects |
| Fixed $5K+ | 16-32 connects |
| Hourly (basic) | 6-16 connects |

80 connects at $12 → approximately 6-12 proposals at Tier 1 budget range.
**Buy connects every time you hit < 20 remaining.**
