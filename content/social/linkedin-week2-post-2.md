# LinkedIn Week 2 -- Post 2

**Schedule**: Wednesday, February 19, 2026, 9:00 AM PT
**Topic**: The Real Cost of "Just Use LangChain"
**Content Type**: Hot take / decision framework

---

"Just use LangChain" is the new "just use WordPress."

It's advice that's correct 60% of the time and catastrophically wrong the other 40%.

I've built 11 production AI systems. I used LangChain in zero of them. Here's why that was the right call for me -- and why it might be the wrong call for you.

Where LangChain wins:
- Prototyping speed. If you need a RAG demo in 2 hours for a stakeholder meeting, LangChain is unbeatable. The abstractions are designed for fast iteration, not production optimization.
- Ecosystem breadth. 700+ integrations. If you need to connect to an obscure vector store or a niche LLM provider, someone's probably written a LangChain adapter.
- Community. When you Google an error, you'll find a StackOverflow answer.

Where LangChain hurts:
- **Dependency weight**. The core package pulls in 200KB+ of abstractions. For a system where the hot path is sub-millisecond cache lookups, that overhead matters.
- **Debugging opacity**. When something breaks in a chain, the stack trace goes through 6 layers of abstraction before you reach your code. In production at 3 AM, that's the difference between a 10-minute fix and a 2-hour investigation.
- **Performance ceilings**. I benchmarked our orchestration overhead at P99: 0.012ms. That's because the routing, caching, and parsing are custom code optimized for our specific patterns. Generic abstractions can't match that.

The decision framework I use:

**Use LangChain when**: You're prototyping. You need 5+ integrations. Your team is new to LLM development. Time-to-demo matters more than time-to-production.

**Skip LangChain when**: You have 1-3 providers. Performance is a hard requirement. You need to understand every line of your LLM pipeline. You're building infrastructure, not an application.

There's no universal right answer. But "just use LangChain" without asking these questions first is how teams end up rewriting their AI layer 6 months in.

What's your take? LangChain, custom, or something else?

#Python #AIEngineering #LLMOps #SoftwareArchitecture #LangChain #BuildInPublic

---

**Engagement strategy**: This will be polarizing. LangChain advocates will push back. Stay neutral and data-driven in replies. Acknowledge LangChain's strengths. The goal is to position yourself as someone who evaluates tools critically, not someone with an anti-LangChain agenda.
