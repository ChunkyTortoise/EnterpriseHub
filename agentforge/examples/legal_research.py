"""Legal Research Pipeline — 2-agent chain: search → summarize case law.

Demonstrates AgentForge's async pipeline with mock legal data.
No API keys required — fully self-contained.

Run:
    python examples/legal_research.py
"""
import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AgentResult:
    agent: str
    output: str
    tokens_used: int = 0
    latency_ms: int = 0
    metadata: dict = field(default_factory=dict)


MOCK_CASES = [
    {"name": "Smith v. Jones (2024)", "topic": "negligence", "holding": "Duty of care extends to foreseeable third parties."},
    {"name": "Acme Corp v. Widget Inc (2023)", "topic": "contract breach", "holding": "Liquidated damages clause upheld; actual damages not required."},
    {"name": "State v. Martinez (2024)", "topic": "negligence", "holding": "Comparative fault applies when plaintiff contributed to harm."},
    {"name": "Johnson v. City of Portland (2023)", "topic": "civil rights", "holding": "Qualified immunity denied where precedent clearly established."},
]


async def search_agent(query: str) -> AgentResult:
    """Search for relevant case law based on a legal query."""
    await asyncio.sleep(0.1)  # simulate latency
    keywords = query.lower().split()
    matches = [c for c in MOCK_CASES if any(k in c["topic"] or k in c["name"].lower() for k in keywords)]
    if not matches:
        matches = MOCK_CASES[:2]
    return AgentResult(
        agent="CaseSearchAgent",
        output=json.dumps(matches, indent=2),
        tokens_used=len(query.split()) * 3 + 80,
        latency_ms=112,
        metadata={"cases_found": len(matches)},
    )


async def summarize_agent(search_output: str, query: str) -> AgentResult:
    """Summarize case law findings into a legal brief."""
    await asyncio.sleep(0.1)
    cases = json.loads(search_output)
    lines = [f"Legal Research Brief: {query}", f"Date: {datetime.now().strftime('%Y-%m-%d')}", f"Cases analyzed: {len(cases)}", ""]
    for c in cases:
        lines.append(f"  - {c['name']}: {c['holding']}")
    lines.append("")
    lines.append(f"Conclusion: {len(cases)} relevant cases found supporting the legal analysis.")
    summary = "\n".join(lines)
    return AgentResult(
        agent="SummaryAgent",
        output=summary,
        tokens_used=len(summary.split()) * 2 + 60,
        latency_ms=198,
    )


async def run_pipeline(query: str) -> None:
    print(f"{'=' * 60}")
    print("AgentForge Legal Research Pipeline")
    print(f"Query: {query}")
    print(f"{'=' * 60}\n")

    # Step 1: Search
    print("[1/2] CaseSearchAgent: Searching case law...")
    search_result = await search_agent(query)
    print(f"      Found {search_result.metadata['cases_found']} cases ({search_result.latency_ms}ms)\n")

    # Step 2: Summarize
    print("[2/2] SummaryAgent: Generating brief...")
    summary_result = await summarize_agent(search_result.output, query)
    print(f"      Brief generated ({summary_result.latency_ms}ms)\n")

    print(f"{'─' * 60}")
    print(summary_result.output)
    print(f"{'─' * 60}")
    total_tokens = search_result.tokens_used + summary_result.tokens_used
    total_ms = search_result.latency_ms + summary_result.latency_ms
    print(f"\nPipeline complete | {total_tokens} tokens | {total_ms}ms total")


if __name__ == "__main__":
    asyncio.run(run_pipeline("negligence duty of care"))
