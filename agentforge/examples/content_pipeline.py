"""Content Pipeline — 3-agent chain: research → draft → SEO review.

Demonstrates a 3-stage content creation workflow with mock agents.
No API keys required — fully self-contained.

Run:
    python examples/content_pipeline.py
"""

import asyncio
from dataclasses import dataclass, field


@dataclass
class AgentResult:
    agent: str
    output: str
    tokens_used: int = 0
    latency_ms: int = 0
    metadata: dict = field(default_factory=dict)


MOCK_RESEARCH = {
    "ai": {
        "trends": ["LLM agents", "MCP protocol", "zero-dep frameworks"],
        "stats": "Market growing 35% YoY",
    },
    "saas": {
        "trends": ["usage-based pricing", "PLG", "AI copilots"],
        "stats": "Average ARR growth 28%",
    },
    "default": {
        "trends": ["digital transformation", "automation", "data-driven decisions"],
        "stats": "Adoption up 40%",
    },
}


async def research_agent(topic: str) -> AgentResult:
    """Research a topic and return structured findings."""
    await asyncio.sleep(0.08)
    key = next((k for k in MOCK_RESEARCH if k in topic.lower()), "default")
    data = MOCK_RESEARCH[key]
    output = (
        f"Research on '{topic}':\n- Trends: {', '.join(data['trends'])}\n- Market: {data['stats']}"
    )
    return AgentResult(agent="ResearchAgent", output=output, tokens_used=95, latency_ms=84)


async def draft_agent(research: str, topic: str) -> AgentResult:
    """Draft a blog post from research findings."""
    await asyncio.sleep(0.1)
    lines = [
        f"# {topic.title()}: What You Need to Know in 2026",
        "",
        "## Key Findings",
        "",
    ]
    for line in research.split("\n"):
        if line.startswith("- "):
            lines.append(line)
    lines.extend(
        [
            "",
            "## Analysis",
            "",
            f"The {topic} landscape is evolving rapidly. Organizations that adapt early",
            "will capture disproportionate value in the coming years.",
            "",
            "## Takeaways",
            "",
            "1. Start small with proven frameworks",
            "2. Measure ROI from day one",
            "3. Invest in team enablement",
        ]
    )
    return AgentResult(agent="DraftAgent", output="\n".join(lines), tokens_used=210, latency_ms=156)


async def seo_agent(draft: str, topic: str) -> AgentResult:
    """Review draft for SEO optimization."""
    await asyncio.sleep(0.06)
    word_count = len(draft.split())
    has_h1 = draft.startswith("#")
    has_h2 = "## " in draft
    keyword_count = draft.lower().count(topic.lower().split()[0])

    score = 60
    suggestions = []
    if has_h1:
        score += 10
    else:
        suggestions.append("Add H1 heading with primary keyword")
    if has_h2:
        score += 10
    if keyword_count >= 3:
        score += 10
    else:
        suggestions.append(f"Increase keyword '{topic}' density (currently {keyword_count}x)")
    if word_count > 100:
        score += 10
    else:
        suggestions.append(f"Expand content (currently {word_count} words, target 300+)")

    output = (
        f"SEO Score: {score}/100\nWord count: {word_count}\nKeyword occurrences: {keyword_count}"
    )
    if suggestions:
        output += "\nSuggestions:\n" + "\n".join(f"  - {s}" for s in suggestions)
    else:
        output += "\nNo critical issues found."

    return AgentResult(agent="SEOReviewAgent", output=output, tokens_used=78, latency_ms=62)


async def run_pipeline(topic: str) -> None:
    print(f"{'=' * 60}")
    print("AgentForge Content Pipeline")
    print(f"Topic: {topic}")
    print(f"{'=' * 60}\n")

    print("[1/3] ResearchAgent: Gathering data...")
    research = await research_agent(topic)
    print(f"      Done ({research.latency_ms}ms)\n")

    print("[2/3] DraftAgent: Writing article...")
    draft = await draft_agent(research.output, topic)
    print(f"      Done ({draft.latency_ms}ms)\n")

    print("[3/3] SEOReviewAgent: Optimizing...")
    seo = await seo_agent(draft.output, topic)
    print(f"      Done ({seo.latency_ms}ms)\n")

    print(f"{'─' * 60}")
    print("DRAFT:")
    print(draft.output)
    print(f"\n{'─' * 60}")
    print("SEO REVIEW:")
    print(seo.output)
    print(f"{'─' * 60}")

    total_tokens = research.tokens_used + draft.tokens_used + seo.tokens_used
    total_ms = research.latency_ms + draft.latency_ms + seo.latency_ms
    print(f"\nPipeline complete | {total_tokens} tokens | {total_ms}ms total")


if __name__ == "__main__":
    asyncio.run(run_pipeline("AI agent frameworks"))
