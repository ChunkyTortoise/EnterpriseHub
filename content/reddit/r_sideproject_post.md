# I built 11 Python projects over 8 months — now they're all open source 🎯

Eight months ago, I was a software engineer who built things at work and... didn't build anything else. Sound familiar?

I decided to change that. Here's what I made, what I learned, and why you should start your own side project today.

---

## 🏗️ Where I Started

I had two problems:
1. I was curious about AI agents and LLM orchestration but hadn't shipped anything real
2. I owned a rental property in Rancho Cucamonga and spent hours manually managing leads

The solution? Build what I needed. Open source what I built.

---

## 📦 The Projects (11 Repos, 1 Mission)

### The Flagship: **EnterpriseHub**
An AI-powered platform that:
- Qualifies real estate leads automatically (80% accuracy, improving)
- Orchestrates 3 bot personas (Lead, Buyer, Seller)
- Syncs with GoHighLevel CRM
- Powers BI dashboards with Streamlit

### The Infrastructure: **AgentForge**
A multi-agent orchestration framework that grew out of EnterpriseHub. Now it can:
- Coordinate agent swarms with governance
- Handle dead-letter queues and retries
- Audit every agent interaction

### The Research: **Advanced RAG System**
Production-grade retrieval-augmented generation with:
- Hybrid search (dense + sparse)
- Re-ranking pipelines
- Citation tracking
- 500+ unit tests

---

## 📊 By The Numbers

| Metric | Value |
|--------|-------|
| Commits | 847 |
| Lines of Python | ~45,000 |
| Tests Written | 7,000+ |
| Docker Compose Files | 12 |
| Failed Deployments | 7 |
| Victory Beers Celebrated | Countless |

---

## 💡 The Real Lessons (Not The Motivational BS)

### "Just ship it" is terrible advice

I deleted 3 complete rewrites. Version 1 of AgentForge was garbage. Version 2 was better. Version 3 (what's open-sourced now) is decent.

**The lesson:** Perfectionism kills side projects. Ship ugly code that works, then refactor when you have real feedback.

---

### The 2-hour rule saved everything

Some weeks I had 0 time. Some weeks I had 20 hours. The projects that survived were the ones I could make progress on in 2 hours or less.

**What works:**
- Pick a single, small issue
- Open a branch immediately
- Commit when it works (even if ugly)
- PR yourself the next day

**What doesn't work:**
- "I'll work on it this weekend"
- "I need to plan everything first"
- "I'll do it when I have a big block of time"

---

### Tests are a side project's best friend

I added 4,000 tests in the last 2 months. Why? Because I kept breaking things I already shipped.

When you're working alone, you don't have teammates catching your bugs. Tests are your teammate.

**The ROI on tests:**
- Caught 23 regressions I would've shipped
- Refactored with confidence 15 times
- Onboarded myself back to code after 2-week gaps (multiple times)

---

## 🛠️ My Stack (What I'd Use Again)

- **FastAPI** — Async is real, and it's glorious
- **PostgreSQL + Redis** — Boring works
- **Claude Code** — My coding partner for 8 months
- **pytest** — Non-negotiable
- **Docker Compose** — "It works on my machine" is not an excuse
- **uv** — 10x faster package management

---

## 🚀 Ready To Start Your Own?

Here's your starter kit:

1. **Pick a problem you actually have** — Not what VC's fund, not what's trending
2. **Define "done"** — "Build an AI agent" is not measurable. "Qualify leads with 80% accuracy" is.
3. **Commit publicly** — GitHub stars are accountability
4. **Start ugly** — You can fix code. You can't fix nothing.
5. **Celebrate small wins** — Every commit is progress

---

## 🔗 The Code

**github.com/chunkytortoise** — All 11 repos, MIT licensed

- AgentForge
- Advanced RAG System
- EnterpriseHub
- Plus 8 supporting repos

---

## 🤝 What's Next

I'm not stopping. The roadmap includes:
- GraphRAG integration
- Multi-language support (Spanish first)
- Voice interface
- Maybe... a mobile app?

But for now, I'm shipping this post and taking a week off. You've earned it, future maintainers.

---

**TL;DR:** Built 11 Python projects in 8 months. 7,000 tests. Everything open source. Start before you're ready.

*Questions about side projects, AI agents, or surviving 8 months of evenings? AMA.*
