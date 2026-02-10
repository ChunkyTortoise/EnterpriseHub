#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import dataclass
from typing import Any, Dict, Literal
from urllib import error, request
from uuid import uuid4


@dataclass(frozen=True)
class EndpointCheck:
    name: str
    method: Literal["GET", "POST"]
    path: str
    payload: dict[str, Any] | None
    p95_threshold_ms: float


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Deterministic repeated-run latency checks with p95 threshold gates for Portal API"
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Portal API base URL")
    parser.add_argument("--runs", type=int, default=10, help="Number of samples per endpoint")
    parser.add_argument("--timeout", type=float, default=5.0, help="HTTP timeout in seconds")
    parser.add_argument("--api-key", default=None, help="Optional X-API-Key for demo auth mode")
    parser.add_argument("--tenant-id", default="tenant_default", help="Tenant header value used for tenant-scoped checks")
    parser.add_argument("--health-p95-ms", type=float, default=50.0, help="Pass threshold for /health p95 latency")
    parser.add_argument("--deck-p95-ms", type=float, default=200.0, help="Pass threshold for /portal/deck p95 latency")
    parser.add_argument("--swipe-p95-ms", type=float, default=100.0, help="Pass threshold for /portal/swipe p95 latency")
    parser.add_argument("--warmup-runs", type=int, default=1, help="Uncounted warm-up requests per endpoint")
    parser.add_argument(
        "--reset-every",
        type=int,
        default=5,
        help="Run POST /system/reset after every N swipe samples (0 disables periodic resets)",
    )
    return parser


def _request_once(
    *,
    base_url: str,
    endpoint: EndpointCheck,
    timeout: float,
    api_key: str | None,
    tenant_id: str | None,
) -> float:
    url = f"{base_url.rstrip('/')}{endpoint.path}"
    body = None
    headers = {
        "Accept": "application/json",
        "X-Request-ID": f"latency-{uuid4()}",
    }
    if api_key:
        headers["X-API-Key"] = api_key
    if tenant_id:
        headers["X-Tenant-ID"] = tenant_id
    if endpoint.payload is not None:
        body = json.dumps(endpoint.payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url=url, method=endpoint.method, headers=headers, data=body)

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
        raise RuntimeError(f"{endpoint.method} {endpoint.path} returned status {status}")
    return elapsed_ms


def _run_reset(*, base_url: str, timeout: float, api_key: str | None) -> None:
    reset_endpoint = EndpointCheck(
        name="reset",
        method="POST",
        path="/system/reset",
        payload=None,
        p95_threshold_ms=0.0,
    )
    _request_once(base_url=base_url, endpoint=reset_endpoint, timeout=timeout, api_key=api_key, tenant_id=None)


def _p95(samples: list[float]) -> float:
    if len(samples) == 1:
        return samples[0]
    sorted_samples = sorted(samples)
    idx = int(round(0.95 * (len(sorted_samples) - 1)))
    return sorted_samples[idx]


def main() -> int:
    args = _build_parser().parse_args()
    if args.runs <= 0:
        raise SystemExit("--runs must be >= 1")
    if args.warmup_runs < 0:
        raise SystemExit("--warmup-runs must be >= 0")

    endpoints = [
        EndpointCheck(
            name="health",
            method="GET",
            path="/health",
            payload=None,
            p95_threshold_ms=args.health_p95_ms,
        ),
        EndpointCheck(
            name="deck",
            method="GET",
            path="/portal/deck?contact_id=lead_001",
            payload=None,
            p95_threshold_ms=args.deck_p95_ms,
        ),
        EndpointCheck(
            name="swipe",
            method="POST",
            path="/portal/swipe",
            payload={"contact_id": "lead_001", "property_id": "prop_001", "action": "like"},
            p95_threshold_ms=args.swipe_p95_ms,
        ),
    ]

    _run_reset(base_url=args.base_url, timeout=args.timeout, api_key=args.api_key)

    samples: Dict[str, list[float]] = {endpoint.name: [] for endpoint in endpoints}
    for endpoint in endpoints:
        for _ in range(args.warmup_runs):
            _request_once(
                base_url=args.base_url,
                endpoint=endpoint,
                timeout=args.timeout,
                api_key=args.api_key,
                tenant_id=args.tenant_id,
            )
        for idx in range(1, args.runs + 1):
            elapsed_ms = _request_once(
                base_url=args.base_url,
                endpoint=endpoint,
                timeout=args.timeout,
                api_key=args.api_key,
                tenant_id=args.tenant_id,
            )
            samples[endpoint.name].append(elapsed_ms)
            if endpoint.name == "swipe" and args.reset_every > 0 and idx % args.reset_every == 0:
                _run_reset(base_url=args.base_url, timeout=args.timeout, api_key=args.api_key)

    print("| endpoint | runs | avg_ms | p95_ms | max_ms | p95_threshold_ms | status |")
    print("|---|---:|---:|---:|---:|---:|---|")

    has_failure = False
    for endpoint in endpoints:
        endpoint_samples = samples[endpoint.name]
        avg_ms = statistics.fmean(endpoint_samples)
        p95_ms = _p95(endpoint_samples)
        max_ms = max(endpoint_samples)
        status = "PASS" if p95_ms <= endpoint.p95_threshold_ms else "FAIL"
        if status == "FAIL":
            has_failure = True
        print(
            "| "
            f"{endpoint.name} | {len(endpoint_samples)} | {avg_ms:.2f} | {p95_ms:.2f} | {max_ms:.2f} | "
            f"{endpoint.p95_threshold_ms:.2f} | {status} |"
        )

    for endpoint in endpoints:
        endpoint_p95 = _p95(samples[endpoint.name])
        if endpoint_p95 <= endpoint.p95_threshold_ms:
            print(
                f"[PASS] {endpoint.name} p95 {endpoint_p95:.2f}ms <= {endpoint.p95_threshold_ms:.2f}ms threshold"
            )
        else:
            print(
                f"[FAIL] {endpoint.name} p95 {endpoint_p95:.2f}ms > {endpoint.p95_threshold_ms:.2f}ms threshold"
            )

    return 1 if has_failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
