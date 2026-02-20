# LinkedIn Post #7 — Architecture Decision Records

**Publish Date**: Monday, February 24, 2026 @ 8:30am PT
**Topic**: Portfolio Showcase — Engineering Practices
**Goal**: Establish thought leadership in software architecture, drive GitHub traffic, spark conversation about documentation practices

---

## Post Content

I wrote 33 Architecture Decision Records across 10 repos. It took me less time than debugging one undocumented design choice.

Here's the thing about technical decisions: they make perfect sense when you make them. Six months later, you're staring at your own code asking "why did I choose FAISS over Pinecone?"

That question cost me 3 days. I rewrote the integration, realized there was a good reason for the original choice (cold-start latency requirements), and reverted everything.

**That's when I started writing ADRs.**

An ADR is a one-page document that captures four things:
- **Context**: What problem were you solving?
- **Decision**: What did you choose?
- **Consequences**: What are the trade-offs?
- **Alternatives Considered**: What else did you evaluate?

**Real example from my RAG pipeline:**

```
ADR-017: Hybrid BM25 + Dense Retrieval over Pure Semantic Search

Context: Pure embedding search returned "similar" but wrong
chunks. Users searching for "FHA loan requirements" got results
about "VA loan benefits" — semantically close, factually wrong.

Decision: Implement hybrid retrieval with Reciprocal Rank Fusion.

Consequences:
+ Precision@5 improved 34%
+ Keyword-exact queries now return correct results
- Added BM25 index maintenance (~2min rebuild on update)
- Slightly higher latency (+12ms P95)

Alternatives: Re-ranking with cross-encoder (too slow at
200ms+), fine-tuned embeddings (insufficient training data).
```

**33 ADRs later, here's what I've learned:**

1. **ADRs save more time than they cost.** Writing takes 15 minutes. The debugging you avoid saves days. Across 10 repos and 8,500+ tests, I can trace every architectural choice back to a documented reason.

2. **They make onboarding 10x faster.** New contributors don't ask "why is this built this way?" They read the ADR. Context is preserved, not lost in Slack threads.

3. **They force you to consider alternatives.** If you can't name two alternatives you rejected, you probably didn't think hard enough about the decision.

4. **They're a living history.** Some of my ADRs have a "Status: Superseded by ADR-025" header. That's not failure — that's a codebase that evolves with documentation, not despite it.

**The decisions worth documenting:**
- Database/storage choices
- API design patterns
- Caching strategies (this one saved me $750/month — see ADR-009)
- Authentication approaches
- Testing strategies

**The ones not worth documenting:**
- Library version bumps
- Code style preferences (that's what linters are for)
- Obvious choices with no real alternatives

**My template (steal it):**

```markdown
# ADR-XXX: [Decision Title]
**Status**: Accepted | Superseded | Deprecated
**Date**: YYYY-MM-DD
**Context**: [Problem and constraints]
**Decision**: [What you chose and why]
**Consequences**: [Trade-offs, both positive and negative]
**Alternatives**: [What you considered and why you rejected it]
```

If you're building AI systems, the decisions are even more consequential. Model selection, retrieval strategy, caching layers, confidence thresholds — these choices compound. Document them now, or debug them later.

All 33 ADRs are in my repos: github.com/ChunkyTortoise

**Does your team write ADRs? What format do you use?**

#SoftwareArchitecture #EngineeringPractices #Documentation #TechLeadership #AIEngineering

---

## Engagement Strategy

**CTA**: Template sharing + engagement question
**Expected Replies**: 50-70 (broad engineering audience, ADRs are a hot topic)
**Response Time**: <1 hour for all comments

**Prepared Responses**:

**Q: "How do you get buy-in from your team to write ADRs?"**
A: Start small. Write one ADR for a decision the team just debated for 30+ minutes. When someone asks about it 2 months later, point them to the ADR instead of re-explaining. That single moment usually converts skeptics. The key is making ADRs lightweight — 15 minutes to write, not a 3-page essay. If it takes longer, you're overdoing it.

**Q: "What tools do you use for ADRs? Any specific tooling?"**
A: Plain markdown files in the repo, right next to the code. I use a `docs/ADR/` directory in each repo. No special tooling needed — `adr-tools` (npm package) can auto-number them, but honestly a markdown template works fine. The important thing is that ADRs live with the code, not in a separate wiki that nobody checks.

**Q: "Isn't this just over-documentation? YAGNI applies to docs too."**
A: Fair pushback. I only write ADRs for decisions that (1) have real alternatives, (2) involve trade-offs, and (3) will matter in 3+ months. Library version bumps? No ADR. Choosing between FAISS and Pinecone for your vector store? Absolutely. The bar is "will future-me wonder why I did this?" If yes, document it. If no, skip it.

**Q: "How do you handle ADRs becoming outdated?"**
A: Two approaches: (1) When a decision is superseded, I update the original ADR's status to "Superseded by ADR-XXX" and link to the new one. The old ADR stays — it's still valuable context. (2) I review ADRs during quarterly architecture reviews. If something is deprecated, I mark it. But honestly, most ADRs stay relevant longer than you'd expect.

---

## Follow-Up Actions

- [ ] 8:30am PT: Publish post
- [ ] 8:35am: Comment on 5 software architecture / documentation posts
- [ ] Throughout day: Reply to all comments within 1 hour
- [ ] Share ADR template as a downloadable gist if commenters request it
- [ ] Send 5 connection requests to engaged commenters (target: tech leads, staff engineers)
- [ ] Track metrics: impressions, engagement rate, GitHub clicks
