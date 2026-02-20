"""Reproducible benchmark for AgentForge execution overhead.

Usage:
    python scripts/benchmark_engine.py --runs 100
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

from agentforge import DAG, Agent, AgentInput, DAGConfig, ExecutionEngine


async def run_once() -> float:
    dag = DAG(config=DAGConfig(name="bench"))
    dag.add_node("a", Agent(name="a", instructions="Respond briefly.", llm="mock/mock-v1"))
    dag.add_node("b", Agent(name="b", instructions="Respond briefly.", llm="mock/mock-v1"))
    dag.add_edge("a", "b")

    start = time.perf_counter()
    await ExecutionEngine().execute(
        dag,
        input=AgentInput(messages=[{"role": "user", "content": "Benchmark run"}]),
    )
    return (time.perf_counter() - start) * 1000


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=100)
    parser.add_argument(
        "--output",
        default="evidence/benchmarks/latest.json",
        help="Path to write benchmark artifact",
    )
    args = parser.parse_args()

    latencies = []
    for _ in range(args.runs):
        latencies.append(await run_once())

    sorted_l = sorted(latencies)
    p50 = sorted_l[int(len(sorted_l) * 0.50)]
    p95 = sorted_l[int(len(sorted_l) * 0.95)]
    p99 = sorted_l[int(len(sorted_l) * 0.99)]

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "runs": args.runs,
        "provider": "mock/mock-v1",
        "metrics": {
            "p50_ms": round(p50, 4),
            "p95_ms": round(p95, 4),
            "p99_ms": round(p99, 4),
            "avg_ms": round(sum(latencies) / len(latencies), 4),
            "throughput_rps": round(1000.0 / (sum(latencies) / len(latencies)), 2),
        },
    }

    script_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    payload["script_sha256"] = script_hash

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
