# Client Requirements Reference

**Job Title:** Build Self-Maintaining AI Agent with Claude API, LangChain & GitHub Integration

**Posted:** December 31, 2025  
**Budget:** $10,000 - $16,000  
**Timeline:** 8-12 weeks

---

## 📋 Exact Client Requirements

### **Core Capabilities Required:**

#### 1. **Conversational Interface**
**Client's Words:**
> "Web-based chat (secure login, only I can access)"

**Our Implementation Status:**
- ✅ Streamlit chat interface
- ⚠️ No authentication yet
- ⚠️ Not production-deployed

**Enhancement Needed:**
- Add basic authentication
- Deploy with secure access
- Add session management

---

#### 2. **File Management**
**Client's Words:**
> "Read/write to GitHub repository, update documents based on our conversations, maintain version history"

**Our Implementation Status:**
- ✅ GitHub Tools class written
- ⚠️ Not tested with real repos
- ⚠️ No version history UI

**Enhancement Needed:**
- Test with real GitHub repo
- Show commit history in UI
- Add file browser

---

#### 3. **Code Generation & Deployment**
**Client's Words:**
> "Write code, test it, deploy to staging automatically, deploy to production with my approval"

**Our Implementation Status:**
- ⚠️ Placeholder code generation
- ❌ No testing integration
- ❌ No deployment pipeline

**Enhancement Needed:**
- Real Claude API code generation
- Automated test runner
- Staging/production workflow

---

#### 4. **Persistent Memory**
**Client's Words:**
> "Remember all conversations across sessions, maintain decision log, never lose context"

**Our Implementation Status:**
- ✅ JSON-based memory
- ✅ Decision logging
- ⚠️ No context summarization

**Enhancement Needed:**
- PostgreSQL option for scale
- Context compression
- Search/retrieval

---

#### 5. **Business Support**
**Client's Words:**
> "Help create course content, draft documents, research competitors"

**Our Implementation Status:**
- ❌ Not implemented

**Enhancement Needed:**
- Add business tools node
- Web scraping capability
- Document generation
- Research templates

---

### **Tech Stack Required:**

✅ **Claude API** - Required (client specified)
✅ **LangChain or LangGraph** - LangGraph chosen
✅ **Python (Flask/FastAPI)** - Using Streamlit (acceptable)
⚠️ **PostgreSQL or Firebase** - JSON currently (need upgrade path)
✅ **GitHub integration** - Implemented
⚠️ **GCP Cloud Run or AWS** - Currently Streamlit Cloud
⚠️ **GitHub Actions (CI/CD)** - Partially configured

---

## 🎯 Client's Vision

**Key Quote:**
> "After handoff, I should be able to maintain and extend the entire system through conversation—without ongoing developer support. You're building yourself out of a job, and I'll pay well for it."

**What This Means:**
- Agent must be fully autonomous
- Documentation must be comprehensive
- Self-improvement capability critical
- No ongoing developer dependency

---

## 📊 Project Phases

### **Phase 1: Core Agent ($4,000-6,000)**

**Deliverables:**
- [ ] Conversational interface with secure login
- [ ] Persistent memory system
- [ ] GitHub integration (read/write)
- [ ] Basic tool use (file ops, code execution)

**Timeline:** 4 weeks

**Our Status:** ~70% complete

---

### **Phase 2: Deployment Pipeline ($2,000-4,000)**

**Deliverables:**
- [ ] Automated testing pipeline
- [ ] Staging environment auto-deploy
- [ ] Production deploy with approval
- [ ] Self-improvement loop

**Timeline:** 3 weeks

**Our Status:** ~20% complete

---

### **Phase 3: User-Facing Product ($4,000-6,000)**

**Deliverables:**
- [ ] Spec-to-product pipeline
- [ ] Business support tools
- [ ] Advanced reasoning
- [ ] Proactive suggestions

**Timeline:** 4 weeks

**Our Status:** ~10% complete

---

## ✅ Checklist: Match Client Requirements

### **Must-Have Features:**

**Conversational:**
- [x] Chat interface
- [ ] Secure authentication
- [x] Streaming responses
- [x] Session persistence

**GitHub:**
- [x] Read files
- [x] Write files
- [x] Create branches
- [x] Create PRs
- [ ] Show commit history
- [ ] File browser UI

**Code Generation:**
- [ ] Generate production code
- [ ] Run tests automatically
- [ ] Show test results
- [ ] Deploy to staging
- [ ] Manual production deploy

**Memory:**
- [x] Conversation history
- [x] Decision logging
- [ ] Context search
- [ ] PostgreSQL option
- [ ] Export/import

**Self-Improvement:**
- [x] Decision logging structure
- [ ] Pattern analysis
- [ ] Strategy updates
- [ ] A/B testing

**Business Tools:**
- [ ] Course content creator
- [ ] Document drafter
- [ ] Competitor research
- [ ] Web scraping

---

## 🎯 "Wow" Factors (Client Will Love)

### **Features That Will Impress:**

1. **Live GitHub File Browser**
   - See repository structure in real-time
   - Click to view/edit any file
   - Visual diff before committing

2. **Visual Workflow State**
   - See agent "thinking" in real-time
   - Progress bars for long operations
   - Node-by-node execution display

3. **Automated Testing Dashboard**
   - Tests run automatically
   - Green checkmarks for passing
   - Detailed failure reports

4. **Self-Improvement Metrics**
   - Success rate over time
   - Decision patterns identified
   - Agent-suggested improvements

5. **Cost Tracking**
   - API costs per operation
   - Budget alerts
   - Optimization suggestions

---

## 🚫 What Client Doesn't Want

**From reading between the lines:**

❌ **Ongoing dependencies**
- Don't build features that require constant maintenance
- Must be self-sustaining

❌ **Technical jargon**
- Client is business-focused
- UX must be non-technical

❌ **Incomplete features**
- Better to have fewer complete features
- Than many half-built ones

❌ **Vendor lock-in**
- Must be portable (GCP or AWS)
- No proprietary dependencies

---

## 💰 Budget Breakdown

**Client's Range:** $10,000 - $16,000 (8-12 weeks)

**Our Proposal:** $13,000 (11 weeks)
- Phase 1: $5,000
- Phase 2: $3,000
- Phase 3: $5,000

**Position:** Middle of range (safe)

---

## 📞 Client's Evaluation Criteria

**From job posting:**

### **They Asked Applicants To:**

1. ✅ "Share relevant project with AI agent and tool use"
   - We have: Live demo at ct-enterprise-ai.streamlit.app

2. ✅ "Describe approach to project"
   - We have: Detailed proposal document

3. ✅ "Confirm Claude API experience"
   - We have: 2,145 lines production code

4. ✅ "Timeline and rate"
   - We have: $13k, 11 weeks

**We check all boxes. Now make the demo undeniable.**

---

## 🎯 Success Definition

**Client will hire us if:**

1. **Demo works flawlessly**
   - They test it, it doesn't break
   - Examples work perfectly
   - UI is professional

2. **Shows exact capabilities requested**
   - Every requirement checked
   - Nothing promised that isn't shown
   - Clear path to Phase 2/3

3. **Proves Claude/LangGraph expertise**
   - Code is production-quality
   - Architecture is solid
   - No rookie mistakes

4. **Demonstrates self-sufficiency**
   - Agent improves itself
   - Documentation is complete
   - Client can extend it

---

## 📝 Notes from Client's Language

**Tone Analysis:**

- **Knowledgeable**: Knows what they want technically
- **Business-focused**: Wants to build a business, not just code
- **Quality-oriented**: "Looking for quality over speed"
- **Vision-driven**: Excited about self-improving systems

**What This Means:**
- Don't dumb things down (they understand tech)
- Focus on business value, not just features
- Take time to do it right
- Show enthusiasm for the vision

---

## 🚀 Next Steps

**To strengthen our position:**

1. **Complete Phase 1 features** (this session)
2. **Create impressive demo video**
3. **Capture professional screenshots**
4. **Update proposal with demo link**
5. **Follow up with client**

---

**This client is winnable. Match these requirements and you win.** 🎯
