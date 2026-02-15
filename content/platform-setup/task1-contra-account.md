# Task 1: Contra Account Setup

**Agent Model**: Claude Sonnet 4.5
**Tools Required**: Browser automation (claude-in-chrome)
**Estimated Time**: 15-20 minutes
**Priority**: P0 (High - No fees on first $10K)

---

## Objective

Create a complete Contra profile with 3 service listings using pre-written content from `content/contra/`.

## Prerequisites

**Content Files Ready**:
- `/Users/cave/Documents/GitHub/EnterpriseHub/content/contra/profile.md`
- `/Users/cave/Documents/GitHub/EnterpriseHub/content/contra/service-1.md` (Custom RAG System)
- `/Users/cave/Documents/GitHub/EnterpriseHub/content/contra/service-2.md` (AI Chatbot Integration)
- `/Users/cave/Documents/GitHub/EnterpriseHub/content/contra/service-3.md` (Streamlit Dashboard)

**Required Info**:
- Email: caymanroden@gmail.com
- Location: Palm Springs, CA
- Portfolio: chunkytortoise.github.io
- GitHub: github.com/ChunkyTortoise
- LinkedIn: linkedin.com/in/caymanroden

---

## Agent Prompt

```
You are setting up a Contra freelance account for an AI/ML engineer.

CONTEXT:
- User: Cayman Roden (caymanroden@gmail.com)
- Skills: AI/ML, RAG systems, FastAPI, multi-agent orchestration
- Goal: Create profile + 3 service listings
- All content is pre-written in markdown files

TASK CHECKLIST:

1. Navigate to contra.com/signup
2. Create account with caymanroden@gmail.com
3. Complete profile setup:
   - Read content from: /Users/cave/Documents/GitHub/EnterpriseHub/content/contra/profile.md
   - Copy profile headline, bio, skills
   - Add location: Palm Springs, CA (Remote)
   - Upload profile photo if prompt appears (skip if optional)
   - Connect GitHub: github.com/ChunkyTortoise
   - Connect LinkedIn: linkedin.com/in/caymanroden
   - Add portfolio link: chunkytortoise.github.io

4. Create Service Listing #1 (Custom RAG System):
   - Read content from: /Users/cave/Documents/GitHub/EnterpriseHub/content/contra/service-1.md
   - Title: "Custom RAG AI System (Question-Answering Engine)"
   - Pricing: $1,500 (from file)
   - Delivery: 5-7 days
   - Copy description, deliverables, tech stack from markdown
   - Publish listing

5. Create Service Listing #2 (AI Chatbot):
   - Read content from: /Users/cave/Documents/GitHub/EnterpriseHub/content/contra/service-2.md
   - Title: "Claude/GPT Chatbot Integration"
   - Pricing: $2,000 (from file)
   - Delivery: 7-10 days
   - Copy all content from markdown
   - Publish listing

6. Create Service Listing #3 (Streamlit Dashboard):
   - Read content from: /Users/cave/Documents/GitHub/EnterpriseHub/content/contra/service-3.md
   - Title: "Custom Streamlit Analytics Dashboard"
   - Pricing: $1,200 (from file)
   - Delivery: 5-7 days
   - Copy all content from markdown
   - Publish listing

7. Verify profile completeness:
   - Profile shows 100% complete
   - All 3 services are live
   - GitHub/LinkedIn connected
   - Portfolio link working

8. Record final profile URL and save to: /Users/cave/Documents/GitHub/EnterpriseHub/content/platform-setup/contra-setup-complete.txt

SUCCESS CRITERIA:
✅ Account created and verified
✅ Profile 100% complete
✅ 3 service listings published
✅ GitHub + LinkedIn connected
✅ Profile URL saved

IMPORTANT NOTES:
- If email verification is required, pause and notify user
- If payment method is required before publishing, skip and note in output
- Take screenshots of completed profile + each service listing
- If any step fails, document exactly where and why
```

---

## Expected Output

**File**: `content/platform-setup/contra-setup-complete.txt`

```
Contra Account Setup - COMPLETE
Date: 2026-02-15
Profile URL: https://contra.com/caymanroden
Status: Active

✅ Profile created (100% complete)
✅ Service 1: Custom RAG System ($1,500) - LIVE
✅ Service 2: AI Chatbot Integration ($2,000) - LIVE
✅ Service 3: Streamlit Dashboard ($1,200) - LIVE
✅ GitHub connected
✅ LinkedIn connected
✅ Portfolio link added

Screenshots saved:
- contra-profile.png
- contra-service-1.png
- contra-service-2.png
- contra-service-3.png

Next Steps:
- Verify email if not done
- Add payment method when first client pays
```

---

## Fallback Plan

If browser automation fails:
1. Manual setup takes ~20 minutes
2. Use content files directly (copy/paste)
3. Follow Contra's onboarding wizard
4. Reference: https://contra.com/help/getting-started

---

## Revenue Impact

- **First client**: No platform fees (0% on first $10K)
- **Service range**: $1,200-$2,000/project
- **Time to first sale**: 1-4 weeks (estimated)
- **Monthly potential**: $3K-6K (2-3 projects)
