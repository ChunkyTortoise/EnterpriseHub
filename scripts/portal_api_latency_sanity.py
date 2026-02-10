#!/usr/bin/env python3
from __future__ import annotations

import argparse
import statistics
import time
from dataclasses import dataclass
from typing import Dict, List
from urllib import error, request
from uuid import uuid4


@dataclass(frozen=True)
class EndpointCheck:
    name: str
    path: str


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lightweight repeated-run latency sanity checks for Portal API")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Portal API base URL")
    parser.add_argument("--runs", type=int, default=10, help="Number of samples per endpoint")
    parser.add_argument("--timeout", type=float, default=5.0, help="HTTP timeout in seconds")
    parser.add_argument("--api-key", default=None, help="Optional X-API-Key for demo auth mode")
    return parser


def _request_once(base_url: str, endpoint: EndpointCheck, timeout: float, api_key: str | None) -> float:
    url = f"{base_url.rstrip('/')}{endpoint.path}"
    headers = {
        "Accept": "application/json",
        "X-Request-ID": f"latency-{uuid4()}",
    }
    if api_key:
        headers["X-API-Key"] = api_key
    req = request.Request(url=url, method="GET", headers=headers)

    start = time.perf_counter()
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            resp.read()
    except error.HTTPError as exc:
        status = exc.code
        exc.read()
    elapsed_ms = (time.perf_counter() - start) * 1000

    if status != 200:
        raise RuntimeError(f"{endpoint.path} returned status {status}")
    return elapsed_ms


def _p95(samples: List[float]) -> float:
    if len(samples) == 1:
        return samples[0]
    sorted_samples = sorted(samples)
    idx = int(round(0.95 * (len(sorted_samples) - 1)))
    return sorted_samples[idx]


def main() -> int:
    args = _build_parser().parse_args()
    endpoints = [
        EndpointCheck(name="health", path="/health"),
        EndpointCheck(name="state_details", path="/system/state/details?limit=2"),
    ]

    samples: Dict[str, List[float]] = {endpoint.name: [] for endpoint in endpoints}

    for endpoint in endpoints:
        for _ in range(args.runs):
            samples[endpoint.name].append(
                _request_once(base_url=args.base_url, endpoint=endpoint, timeout=args.timeout, api_key=args.api_key)
            )

    print("| endpoint | runs | avg_ms | p95_ms | max_ms |")
    print("|---|---:|---:|---:|---:|")
    for endpoint in endpoints:
        endpoint_samples = samples[endpoint.name]
        avg_ms = statistics.fmean(endpoint_samples)
        p95_ms = _p95(endpoint_samples)
        max_ms = max(endpoint_samples)
        print(
            f"| {endpoint.name} | {len(endpoint_samples)} | {avg_ms:.2f} | {p95_ms:.2f} | {max_ms:.2f} |"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

