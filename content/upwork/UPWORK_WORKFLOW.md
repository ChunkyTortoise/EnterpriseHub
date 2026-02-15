# Upwork Job Search & Application Workflow

**Last Updated**: 2026-02-15

## Daily Routine (15-20 minutes)

### Morning (10 minutes)

1. **Search with high-value keywords** (pick 2-3 per day):
   ```
   - "RAG" + filter $60+/hr
   - "Claude API" OR "Anthropic"
   - "FastAPI" + "async" + "Python"
   - "multi-agent" OR "AI orchestration"
   - "Streamlit dashboard"
   ```

2. **Apply filters**:
   - ✅ Payment Verified
   - ✅ Client History: 1+ hires
   - ✅ Location: US, Canada, UK, EU
   - ✅ Experience: Intermediate to Expert

3. **Star 5-7 promising jobs**:
   ```bash
   # As you find jobs, track them:
   python scripts/upwork_tracker.py add "https://upwork.com/job/..." \
       --title "Senior RAG Engineer" \
       --rate "$70/hr" \
       --fit 9 \
       --keywords "RAG, FastAPI, PostgreSQL"
   ```

### Evening (10 minutes)

1. **Review starred jobs**:
   ```bash
   python scripts/upwork_tracker.py list starred
   ```

2. **Submit 1-2 proposals** (budget 10-15 connects each)

3. **Update tracker**:
   ```bash
   python scripts/upwork_tracker.py update 5 --status applied \
       --notes "Submitted customized proposal highlighting docqa-engine"
   ```

## Tracker Commands

### Add a Job
```bash
python scripts/upwork_tracker.py add "https://upwork.com/job/abc123" \
    --title "RAG System Developer" \
    --rate "$65/hr" \
    --fit 9 \
    --keywords "RAG, vector database, Claude"
```

### List All Jobs
```bash
# All jobs
python scripts/upwork_tracker.py list

# Filter by status
python scripts/upwork_tracker.py list starred
python scripts/upwork_tracker.py list applied
python scripts/upwork_tracker.py list interview
python scripts/upwork_tracker.py list rejected
```

### Show Job Details
```bash
python scripts/upwork_tracker.py show 5
```

### Update Job Status
```bash
# Mark as applied
python scripts/upwork_tracker.py update 5 --status applied

# Add interview notes
python scripts/upwork_tracker.py update 5 --status interview \
    --notes "Scheduled for Feb 18 at 2pm PST. They want to see AgentForge demo."

# Mark as rejected
python scripts/upwork_tracker.py update 5 --status rejected \
    --notes "Client went with someone else. Budget was too low anyway."
```

## Status Values

- `starred` - Found and saved for later
- `applied` - Proposal submitted
- `interview` - Interview scheduled or completed
- `offered` - Contract offered
- `accepted` - Contract accepted
- `rejected` - Not selected or declined
- `withdrawn` - You withdrew your proposal

## High-Value Search Keywords

### Premium ($70-100+/hr)

1. **"Claude API"** - Latest tech, sophisticated clients
2. **"multi-agent system"** - Advanced architecture
3. **"RAG optimization"** - Existing system improvements
4. **"LLM cost reduction"** - Business-focused (your 89% metric!)
5. **"async Python" + "FastAPI"** - Backend expertise

### Solid ($60-75/hr)

6. **"RAG" + "$60+"** - Your sweet spot
7. **"vector database" + "PostgreSQL"** - Full-stack data
8. **"Streamlit dashboard"** - Quick wins with demos
9. **"document processing" + "AI"** - docqa-engine match
10. **"AI chatbot integration"** - jorge bots portfolio

### Quick Wins ($500-1,500 fixed)

11. **"Streamlit" + Fixed Price $500-1,500**
12. **"Python automation" + "proof of concept"**
13. **"AI dashboard" + Fixed Price**

## Red Flags to Avoid

❌ **Client red flags**:
- No payment method verified
- 0 hires, 0 spent
- Location in low-budget countries only
- "Test project" for $50

❌ **Job red flags**:
- "Junior" or "Entry level" for complex AI work
- Rate < $40/hr for expert-level work
- "Simple chatbot" (usually not simple)
- Vague requirements with huge scope

## Proposal Budget

**You have**: 80 connects (purchased Feb 15)

**Typical cost**: 10-16 connects per proposal

**Budget**: ~5-8 proposals

**Strategy**: Apply to 1-2 jobs daily (10-15 connects/day) = 40-50 days of runway

## Weekly Goals

**Week 1** (Feb 15-21):
- [ ] Submit 5 ready proposals
- [ ] Find and track 20 new jobs
- [ ] Submit 5-7 additional proposals
- [ ] Goal: 2-3 interviews

**Week 2** (Feb 22-28):
- [ ] Update profile with generated content
- [ ] Record video intro
- [ ] Connect GitHub account
- [ ] Goal: 1-2 contract offers

**Week 3+**:
- [ ] First contract started
- [ ] Continue applying 1-2/day
- [ ] Build reviews and JSS

## Current Pipeline

**Ready to Submit** (5 proposals):
1. ✅ Semantic RAG + Word-Sense ($65/hr, fit 9/10)
2. ✅ Education RAG Open Source ($60/hr, fit 9/10)
3. ✅ RAG Debugging ($65/hr, fit 8/10)
4. ✅ Modular AI Platform ($500 fixed, fit 8/10)
5. ✅ Support Chatbot ($55/hr, fit 7/10)

**Active Prospects**:
- FloPro Jamaica: Awaiting contract offer ($75/hr)
- Kialash Persad: Follow up needed (call was Feb 11)
- Code Intelligence: Viewed by client ($500 fixed)

## Success Metrics to Track

Track in `client-pipeline.md`:

- **Response rate**: Target 20%+ (2 responses per 10 proposals)
- **Interview rate**: Target 10%+ (1 interview per 10 proposals)
- **Win rate**: Target 20%+ of interviews → contracts
- **Average hourly rate**: Track against $65-75 goal
- **Time to first contract**: Target < 30 days

## Pro Tips

1. **First 5 proposals get 80% of interviews** - Apply within 1 hour of posting
2. **Ask a question** in your proposal - shows engagement
3. **Link to live demos** - your 3 Streamlit apps are differentiators
4. **Reference specific requirements** - proves you read the job post
5. **Use metrics** - "89% cost reduction" beats "very efficient"
6. **Keep proposals under 300 words** - clients skim
7. **Front-load the hook** - first sentence = problem recognition

## Next Actions

**Today** (Feb 15):
1. ✅ Submit 5 ready proposals (you have connects!)
2. 🔍 Run 3 keyword searches, track 10 jobs
3. 📝 Update `client-pipeline.md` with activity

**This Week**:
- Submit 1-2 proposals daily
- Track all activity in scripts/upwork_tracker.py
- Update profile with content/upwork/profile-update.md
- Follow up with Kialash Persad

---

**Remember**: The MCP tool is just automation. Manual search + this tracker = same result, no AWS complexity.
