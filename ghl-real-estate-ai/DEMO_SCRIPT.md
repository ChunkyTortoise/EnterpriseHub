# Phase 2 Demo Script - 5 Minutes to WOW

## 🎯 Demo Objective
Show Jorge how Phase 2 multiplies the value of his GHL Real Estate AI system.

---

## ⏱️ Timeline (5 minutes)

### Minute 1: The Power Intro (0:00-1:00)
**Say:**
"Jorge, remember how Phase 1 qualified your leads automatically? Phase 2 takes that to the next level. Now you can track ROI, manage campaigns, and never lose a lead."

**Show:** 
- Open `http://your-railway-url/api/analytics/dashboard?location_id=demo&days=30`
- Point out: Hot leads count, conversion rate, average lead score

**Value Hook:** "This is what your clients will pay premium prices for."

---

### Minute 2: A/B Testing Magic (1:00-2:00)
**Say:**
"Want to know which opening message converts better? The system tests it automatically."

**Demo:**
```bash
# Create A/B test
curl -X POST "http://localhost:8000/api/analytics/experiments?location_id=demo" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Opening Message Test",
    "variant_a": {"message": "Hi! Looking for a home?"},
    "variant_b": {"message": "Ready to find your dream home?"},
    "metric": "conversion_rate"
  }'
```

**Show:** How the system tracks which variant performs better

**Value:** "This is what marketing agencies charge $5K+ for. Your clients get it built-in."

---

### Minute 3: Bulk Operations = Time Saved (2:00-3:00)
**Say:**
"Got 1,000 leads from a realtor? Import them in 30 seconds."

**Demo:**
```bash
# Import CSV
curl -X POST "http://localhost:8000/api/bulk/import/csv?location_id=demo&tags=Q1-Campaign" \
  -F "file=@sample_leads.csv"

# Bulk SMS to hot leads
curl -X POST "http://localhost:8000/api/bulk/sms/campaign?location_id=demo" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_ids": ["C1", "C2", "C3"],
    "message": "New 3BR in downtown just listed! Reply YES for details."
  }'
```

**Value:** "That's 10 hours of manual work done in seconds."

---

### Minute 4: Never Lose a Lead (3:00-4:00)
**Say:**
"The system monitors lead health. When someone goes cold, it re-engages automatically."

**Demo:**
```bash
# Check at-risk leads
curl "http://localhost:8000/api/lifecycle/health/demo/at-risk?threshold=0.3"

# Launch re-engagement campaign
curl -X POST "http://localhost:8000/api/lifecycle/reengage/campaign?location_id=demo" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {"days_inactive": 30},
    "template": "Hi {first_name}, haven't heard from you. Still looking?"
  }'
```

**Value:** "This is like having a sales manager who never sleeps."

---

### Minute 5: The Close (4:00-5:00)
**Say:**
"Jorge, here's what this means for your business:
- Your clients get enterprise-level features
- You charge premium prices
- Their ROI is measurable and provable
- You're not just a vendor - you're their growth partner"

**Show:** The numbers
- Phase 1: Lead qualification
- Phase 2: Campaign ROI tracking, bulk ops, automated nurturing
- **Result:** 10x more valuable to clients

**The Ask:**
"Let's deploy this to production and get it in front of your top 3 clients this week."

---

## 🎬 Demo Tips

1. **Keep it fast** - Speed impresses
2. **Focus on $$$** - Every feature = money saved or earned
3. **Use real numbers** - "Save 10 hours/week" beats "efficient"
4. **End with action** - "Let's deploy now"

---

## 📦 Demo Assets Needed

- [ ] Sample CSV with 50 leads
- [ ] Screenshot of dashboard with good metrics
- [ ] Pre-created A/B test with results
- [ ] Video recording of demo (2 mins)

---

**Created by:** Agent Gamma - Demo Creator
**Date:** 2026-01-04
