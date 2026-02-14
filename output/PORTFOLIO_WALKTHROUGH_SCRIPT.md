# 5-Minute Portfolio Walkthrough Script

**Purpose**: Demonstrate production experience and technical depth through your GitHub portfolio
**When to use**: When interviewer says "Tell me about your experience" or "Show me what you've built"
**Time**: 5 minutes (practice to stay within limit)

---

## 🎬 Opening (30 seconds)

> "Let me show you my portfolio - I'll focus on the projects most relevant to [YOUR PROJECT]. I'm going to screen share my GitHub - one second."

[Share screen: github.com/ChunkyTortoise]

> "I have 11 production repositories here - everything has automated tests, CI/CD, and Docker. I'll walk you through the top 3 that map directly to what you need."

---

## 📁 Repository 1: EnterpriseHub (2 minutes)

**[Click on EnterpriseHub repository]**

> "This is EnterpriseHub - a real estate AI platform I built with multi-agent orchestration. It's my most relevant project for [YOUR NEEDS]."

### Architecture Overview (30 seconds)

**[Scroll to README architecture diagram]**

> "The architecture has three layers:
> 1. **Jorge Bots** at the top - three specialized AI agents (Lead, Buyer, Seller) that handle different conversation types
> 2. **FastAPI Core** in the middle - this is the orchestration layer that routes tasks and manages state
> 3. **PostgreSQL + Redis** at the bottom - persistence and caching"

### Key Features (60 seconds)

**[Point to specific sections in README]**

> "Let me highlight the features that apply to your project:

**For Kialash (multi-language, multi-channel)**:
> - **Multi-channel messaging**: Handles SMS, WhatsApp, web chat - links conversations across channels to a single contact record. See the `services/agent_mesh_coordinator.py` file.
> - **Tenant isolation**: PostgreSQL with proper partitioning, Redis namespacing by tenant_id
> - **Anti-hallucination**: 3-tier caching strategy - 88% cache hit rate means most responses come from verified cache, not LLM guessing

**For Chase (AI secretary)**:
> - **Agent Mesh Coordinator**: Routes incoming tasks to specialized agents - exactly what you need for Calendar Agent, Email Agent, Research Agent
> - **Claude Orchestrator**: Multi-strategy response parsing - handles JSON, regex, and Claude's tool calling. <200ms overhead.
> - **Handoff Service**: Cross-bot handoff logic with circular prevention and rate limiting - would map to handing off tasks between secretary sub-agents

### Technical Proof (30 seconds)

**[Scroll to Key Metrics section]**

> "Here are the production metrics:
> - **5,100+ automated tests** - all passing, CI runs on every commit
> - **89% LLM cost reduction** - via 3-tier Redis caching
> - **<200ms orchestration overhead** - P99 latency is 0.095ms
> - **88% cache hit rate** - verified over 30 days

These numbers are from actual benchmarks - I can show you the benchmark scripts if you want to see the methodology."

---

## 📁 Repository 2: AgentForge (ai-orchestrator) (1.5 minutes)

**[Navigate to ai-orchestrator repository]**

> "Second project: AgentForge - this is my tool orchestration engine. I built it to handle complex multi-step agent workflows."

### Core Capabilities (60 seconds)

**[Scroll through README features]**

> "Key features:
> 1. **Tool registry** - Dynamic registration of agent capabilities. For [Kialash: 'multi-language detection tools'] / [Chase: 'calendar, email, search tools']
> 2. **ReAct agent loop** - Multi-step reasoning. For example, [Kialash: 'detect language → route to appropriate agent → validate output'] / [Chase: 'check calendar → draft email → confirm with user → send']
> 3. **Evaluation framework** - Measure agent quality with custom metrics
> 4. **Agent memory** - Remember user preferences and past interactions

The core engine does **4.3 million tool dispatches per second** - you can see that in the benchmarks folder."

### Demo Point (30 seconds)

**[Show or describe agents/ directory]**

> "I have several pre-built agent types here: ReAct agents for reasoning, tool-calling agents for API integration, evaluation agents for quality checks. For your project, I'd [Kialash: 'adapt the tool-calling pattern for language-specific APIs'] / [Chase: 'use the ReAct loop for multi-step secretary tasks like scheduling meetings']."

---

## 📁 Repository 3: DocQA Engine (1 minute)

**[Navigate to docqa-engine repository]**

> "Third project: DocQA Engine - document Q&A with hybrid retrieval. This is relevant for [Kialash: 'RAG with hard scoping to prevent cross-tenant data leakage'] / [Chase: 'knowledge base for company policies, user preferences, and FAQ']."

### Architecture (30 seconds)

> "Uses hybrid retrieval - combines BM25 (keyword search) with semantic search (embeddings). Gets better results than either alone. The key feature for your use case is **hard scoping** with metadata filters - when Tenant A queries, they ONLY see Tenant A's documents. No cross-contamination."

### Proof Points (30 seconds)

**[Point to stats]**

> "500+ tests, all passing. Includes:
> - **Cross-encoder re-ranking** for better result quality
> - **Query expansion** for handling typos and synonyms
> - **Conversation manager** for multi-turn context
> - **Answer quality evaluation** - measures accuracy against ground truth

For your project, this would power [Kialash: 'the knowledge base layer with tenant isolation'] / [Chase: 'the secretary's ability to answer policy questions and remember user preferences']."

---

## 🎯 Closing (30 seconds)

**[Return to main GitHub profile page showing all 11 repos]**

> "Those are the top 3 projects most relevant to your needs. All 11 repositories follow the same patterns:
> - Automated tests (8,500+ total across portfolio)
> - Docker support for easy deployment
> - CI/CD with GitHub Actions
> - Architecture documentation
> - Production benchmarks

I also have:
> - **3 live Streamlit demos** (can show if time permits)
> - **33 Architecture Decision Records** across repos - documenting engineering tradeoffs
> - **Mermaid diagrams** in every README showing system architecture

[Kialash-specific]:
> "For your multi-language project, I'd start with EnterpriseHub's multi-channel architecture and add language detection middleware. The tenant isolation patterns are already production-ready."

[Chase-specific]:
> "For your AI secretary, I'd reuse EnterpriseHub's agent mesh coordinator for task routing, AgentForge's ReAct loop for multi-step reasoning, and DocQA for the knowledge base. The Gmail/Outlook OAuth is new, but I've done OAuth flows before - just different providers."

**[Stop screen share]**

> "Happy to dive deeper into any specific component. What questions do you have?"

---

## 🎤 Handling Common Follow-Up Questions

### "Can you show me the actual code?"

> "Absolutely. Let me show you [SPECIFIC FILE]."

**For Kialash**: Navigate to `services/agent_mesh_coordinator.py` or `services/claude_orchestrator.py`
**For Chase**: Navigate to `services/jorge/jorge_handoff_service.py` (analogous to secretary task routing)

**[Scroll through code, highlight key sections]**

> "Here's the [Kialash: 'routing logic that would adapt for language detection'] / [Chase: 'handoff logic that would map to passing tasks between secretary sub-agents']. See this function - it [EXPLAIN CORE LOGIC]. I wrote this to handle [SPECIFIC PRODUCTION PROBLEM]."

### "What about testing?"

> "Let me show you the test suite."

**[Navigate to tests/ directory]**

> "I use pytest with fixtures and mocks. Here's an example test for [RELEVANT FEATURE]. I aim for 80%+ coverage - you can see the coverage report in CI. The tests run on every commit, and I use GitHub Actions to enforce that main branch is always green."

**[Optional: Show .github/workflows/ if they're interested in CI/CD]**

### "Do you have live demos?"

> "Yes, I have Streamlit demos deployed. The main one is at chunkytortoise.github.io - it shows [DESCRIBE DEMO]. I can share my screen and walk through it if you'd like, or you can explore it yourself after the call."

**[If demo is down]**: "Normally it's live, but if Streamlit community cloud is having issues, I can spin up a local Docker container and show you. Takes 2 minutes."

### "How would this apply to our specific needs?"

**[This is the golden question - shows they're engaged]**

> "Great question. Let me map my existing architecture to your requirements."

**[Share screen again, open a blank text editor or whiteboard tool]**

**For Kialash**:
```
Your Needs → My Solution:
1. Multi-language → Language detection middleware (Claude API)
2. Multi-channel → Agent mesh coordinator (already handles SMS/WhatsApp/Web)
3. Multi-tenant → PostgreSQL partitioning + Redis namespacing (EnterpriseHub pattern)
4. Anti-hallucination → 3-tier caching + RAG score thresholds (88% cache hit rate)
```

**For Chase**:
```
Your Needs → My Solution:
1. Gmail integration → OAuth 2.0 flow (similar to GHL/Salesforce I've done)
2. Task routing → Agent mesh coordinator (Calendar Agent, Email Agent, etc.)
3. Email drafting → Claude Haiku + templates (like Jorge bot responses)
4. User preferences → Agent memory system (AgentForge pattern)
```

> "I'd estimate [TIME ESTIMATE] to adapt my existing codebase to your specific requirements. The core architecture is already built and tested - it's mainly about [CUSTOMIZATION NEEDED]."

---

## 🎯 Time Management Tips

**If running over 5 minutes**:
- Skip Repository 3 (DocQA) and just mention it: "I also have a DocQA engine for knowledge base, happy to show later if relevant"
- Shorten metrics to just 2-3 key numbers: "5,100 tests, <200ms latency, 89% cost reduction"
- Skip code deep-dive during walkthrough - offer it as follow-up: "Happy to show specific code sections if you want to dig in"

**If they interrupt with questions**:
- Answer briefly, then ask: "Should I continue the walkthrough, or would you rather discuss [THEIR QUESTION] in depth?"
- Follow their lead - engagement is more important than finishing the script

**If they seem impatient/bored**:
- Jump to closing: "I can send you the full portfolio tour via Loom recording, but let me get to your specific needs..."
- Ask what they care most about: "What part of the tech stack are you most concerned about? I'll focus there."

---

## 📋 Pre-Walkthrough Checklist

Before starting screen share:
- [ ] Close all personal/sensitive tabs
- [ ] Open github.com/ChunkyTortoise in main tab
- [ ] Pre-load EnterpriseHub, ai-orchestrator, docqa-engine repos in separate tabs
- [ ] Zoom browser to 125% (easier for them to read code)
- [ ] Test screen share audio + video
- [ ] Have architecture diagram ready in case screen share fails (can describe verbally)

---

## 🚀 Confidence Boosters

**If you get nervous**:
- Remember: You've ACTUALLY BUILT this stuff. It's not theoretical.
- Your 8,500+ tests and green CI are proof you're not a "tutorial developer"
- The metrics (89% cost reduction, <200ms latency) are real benchmarks, not made up
- You've already solved harder problems than what they're asking for

**If they seem skeptical**:
- Offer proof: "I can show you the CI logs, the benchmark scripts, or even spin up a Docker container live if you want to see it running"
- Share repo links in chat so they can explore after the call
- Offer references: "I can connect you with [PERSON] who can vouch for my work" (if applicable)

---

**Practice this script 2-3 times before the interview. Aim for 4.5 minutes, leaving buffer for interruptions.**
