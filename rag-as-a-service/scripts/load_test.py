#!/usr/bin/env python3
"""Load test for RAG-as-a-Service API.

Usage:
    python scripts/load_test.py [--base-url URL] [--api-key KEY] [--concurrency N] [--duration S]

Targets: 50 req/s sustained, p95 < 500ms.
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import time

import httpx

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_CONCURRENCY = 10
DEFAULT_DURATION = 30  # seconds


async def test_health(client: httpx.AsyncClient) -> float:
    """Hit the health endpoint and return latency in ms."""
    start = time.monotonic()
    resp = await client.get("/health")
    elapsed = (time.monotonic() - start) * 1000
    resp.raise_for_status()
    return elapsed


async def test_query(client: httpx.AsyncClient, api_key: str) -> float:
    """Hit the query endpoint and return latency in ms."""
    start = time.monotonic()
    resp = await client.post(
        "/api/v1/query",
        json={"query": "What are the key features?", "top_k": 5},
        headers={"X-API-Key": api_key},
    )
    elapsed = (time.monotonic() - start) * 1000
    if resp.status_code not in (200, 429):
        resp.raise_for_status()
    return elapsed


async def test_upload(client: httpx.AsyncClient, api_key: str) -> float:
    """Upload a small test document and return latency in ms."""
    start = time.monotonic()
    content = b"This is a test document for load testing the RAG pipeline."
    resp = await client.post(
        "/api/v1/documents",
        files={"file": ("test.txt", content, "text/plain")},
        headers={"X-API-Key": api_key},
    )
    elapsed = (time.monotonic() - start) * 1000
    if resp.status_code not in (201, 429):
        resp.raise_for_status()
    return elapsed


async def worker(
    client: httpx.AsyncClient,
    api_key: str,
    test_fn: str,
    results: list[float],
    errors: list[str],
    stop_event: asyncio.Event,
) -> None:
    """Run requests in a loop until stop_event is set."""
    fn_map = {
        "health": lambda: test_health(client),
        "query": lambda: test_query(client, api_key),
        "upload": lambda: test_upload(client, api_key),
    }
    fn = fn_map[test_fn]

    while not stop_event.is_set():
        try:
            latency = await fn()
            results.append(latency)
        except Exception as e:
            errors.append(str(e))
        await asyncio.sleep(0.01)


def report(name: str, results: list[float], errors: list[str], duration: float) -> None:
    """Print a summary report."""
    total = len(results) + len(errors)
    rps = total / duration if duration > 0 else 0

    print(f"\n{'=' * 60}")
    print(f"  {name.upper()} RESULTS")
    print(f"{'=' * 60}")
    print(f"  Total requests:  {total}")
    print(f"  Successful:      {len(results)}")
    print(f"  Errors:          {len(errors)}")
    print(f"  Duration:        {duration:.1f}s")
    print(f"  Throughput:      {rps:.1f} req/s")

    if results:
        results_sorted = sorted(results)
        p50 = results_sorted[len(results_sorted) // 2]
        p95 = results_sorted[int(len(results_sorted) * 0.95)]
        p99 = results_sorted[int(len(results_sorted) * 0.99)]
        avg = statistics.mean(results)

        print(f"  Avg latency:     {avg:.1f}ms")
        print(f"  P50 latency:     {p50:.1f}ms")
        print(f"  P95 latency:     {p95:.1f}ms")
        print(f"  P99 latency:     {p99:.1f}ms")

        target_met = p95 < 500
        print(f"  P95 < 500ms:     {'PASS' if target_met else 'FAIL'}")

    target_rps = rps >= 50
    print(f"  >= 50 req/s:     {'PASS' if target_rps else f'FAIL ({rps:.1f})'}")
    print(f"{'=' * 60}")


async def run_test(
    base_url: str, api_key: str, test_fn: str, concurrency: int, duration: int
) -> None:
    """Run a single load test scenario."""
    results: list[float] = []
    errors: list[str] = []
    stop_event = asyncio.Event()

    async with httpx.AsyncClient(base_url=base_url, timeout=30) as client:
        workers = [
            asyncio.create_task(worker(client, api_key, test_fn, results, errors, stop_event))
            for _ in range(concurrency)
        ]

        await asyncio.sleep(duration)
        stop_event.set()

        await asyncio.gather(*workers)

    report(test_fn, results, errors, duration)


async def main(args: argparse.Namespace) -> None:
    """Run all load test scenarios."""
    print(f"RAG-as-a-Service Load Test")
    print(f"  Target:      {args.base_url}")
    print(f"  Concurrency: {args.concurrency}")
    print(f"  Duration:    {args.duration}s per test")

    # Health check (no auth needed)
    await run_test(args.base_url, args.api_key, "health", args.concurrency, args.duration)

    if args.api_key:
        await run_test(args.base_url, args.api_key, "query", args.concurrency, args.duration)
        await run_test(args.base_url, args.api_key, "upload", args.concurrency, args.duration)
    else:
        print("\nSkipping query/upload tests (no --api-key provided)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG-as-a-Service Load Test")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-key", default="")
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION)
    args = parser.parse_args()

    asyncio.run(main(args))
