"""Data Analysis Pipeline — 2-agent chain: fetch data → generate insights.

Demonstrates AgentForge's async pipeline with mock sales data.
No API keys required — fully self-contained.

Run:
    python examples/data_analysis.py
"""
import asyncio
import json
from dataclasses import dataclass, field


@dataclass
class AgentResult:
    agent: str
    output: str
    tokens_used: int = 0
    latency_ms: int = 0
    metadata: dict = field(default_factory=dict)


MOCK_SALES = [
    {"month": "Jan", "revenue": 45000, "deals": 12, "churn": 2},
    {"month": "Feb", "revenue": 52000, "deals": 15, "churn": 1},
    {"month": "Mar", "revenue": 48000, "deals": 13, "churn": 3},
    {"month": "Apr", "revenue": 61000, "deals": 18, "churn": 1},
    {"month": "May", "revenue": 58000, "deals": 16, "churn": 2},
    {"month": "Jun", "revenue": 72000, "deals": 22, "churn": 1},
]


async def fetch_agent(query: str) -> AgentResult:
    """Fetch and structure data based on a query."""
    await asyncio.sleep(0.08)
    if "q1" in query.lower() or "quarter" in query.lower():
        data = MOCK_SALES[:3]
    elif "q2" in query.lower():
        data = MOCK_SALES[3:]
    else:
        data = MOCK_SALES
    return AgentResult(
        agent="DataFetchAgent",
        output=json.dumps(data, indent=2),
        tokens_used=len(data) * 20 + 40,
        latency_ms=92,
        metadata={"rows": len(data)},
    )


async def insights_agent(raw_data: str) -> AgentResult:
    """Analyze data and generate actionable insights."""
    await asyncio.sleep(0.1)
    records = json.loads(raw_data)

    total_rev = sum(r["revenue"] for r in records)
    total_deals = sum(r["deals"] for r in records)
    total_churn = sum(r["churn"] for r in records)
    avg_deal = total_rev / total_deals if total_deals else 0
    best = max(records, key=lambda r: r["revenue"])
    worst = min(records, key=lambda r: r["revenue"])

    growth = ((records[-1]["revenue"] - records[0]["revenue"]) / records[0]["revenue"] * 100) if len(records) > 1 else 0

    lines = [
        "Data Analysis Report",
        "=" * 40,
        f"Period: {records[0]['month']} - {records[-1]['month']}",
        f"Total Revenue: ${total_rev:,}",
        f"Total Deals: {total_deals}",
        f"Avg Deal Size: ${avg_deal:,.0f}",
        f"Total Churn: {total_churn} customers",
        f"Revenue Growth: {growth:+.1f}%",
        "",
        "Insights:",
        f"  1. Best month: {best['month']} (${best['revenue']:,})",
        f"  2. Weakest month: {worst['month']} (${worst['revenue']:,})",
        f"  3. {'Positive' if growth > 0 else 'Negative'} revenue trend ({growth:+.1f}%)",
        f"  4. Churn rate: {total_churn / len(records):.1f} customers/month avg",
    ]

    if growth > 20:
        lines.append("  5. Strong growth trajectory — consider scaling sales team")
    elif growth < 0:
        lines.append("  5. Revenue declining — investigate churn drivers")

    return AgentResult(
        agent="InsightsAgent",
        output="\n".join(lines),
        tokens_used=180,
        latency_ms=145,
    )


async def run_pipeline(query: str) -> None:
    print(f"{'=' * 60}")
    print("AgentForge Data Analysis Pipeline")
    print(f"Query: {query}")
    print(f"{'=' * 60}\n")

    print("[1/2] DataFetchAgent: Fetching data...")
    fetch_result = await fetch_agent(query)
    print(f"      Retrieved {fetch_result.metadata['rows']} rows ({fetch_result.latency_ms}ms)\n")

    print("[2/2] InsightsAgent: Analyzing...")
    insights_result = await insights_agent(fetch_result.output)
    print(f"      Report generated ({insights_result.latency_ms}ms)\n")

    print(f"{'─' * 60}")
    print(insights_result.output)
    print(f"{'─' * 60}")

    total_tokens = fetch_result.tokens_used + insights_result.tokens_used
    total_ms = fetch_result.latency_ms + insights_result.latency_ms
    print(f"\nPipeline complete | {total_tokens} tokens | {total_ms}ms total")


if __name__ == "__main__":
    asyncio.run(run_pipeline("H1 2026 sales performance"))
