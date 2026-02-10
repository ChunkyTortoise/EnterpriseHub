#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any, TypedDict
from urllib import error, request
from uuid import uuid4


class SwipePayload(TypedDict):
    contact_id: str
    property_id: str
    action: str


class SwipeResult(TypedDict):
    status: str
    high_intent: bool
    trigger_sms: bool
    adjustments: list[str]


class StateDetailsResult(TypedDict):
    status: str
    details: dict[str, Any]


def _request_json(
    *,
    method: str,
    url: str,
    payload: dict[str, Any] | None,
    request_id: str,
    api_key: str | None,
    timeout: float,
) -> tuple[int, dict[str, Any], dict[str, str]]:
    body = None
    headers = {
        "Accept": "application/json",
        "X-Request-ID": request_id,
    }
    if api_key:
        headers["X-API-Key"] = api_key
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url=url, data=body, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            response_body = json.loads(resp.read().decode("utf-8"))
            response_headers = {key.lower(): value for key, value in resp.headers.items()}
            return status, response_body, response_headers
    except error.HTTPError as exc:
        response_body = json.loads(exc.read().decode("utf-8"))
        response_headers = {key.lower(): value for key, value in exc.headers.items()}
        return exc.code, response_body, response_headers


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Typed client smoke for Portal API interview flow")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Portal API base URL")
    parser.add_argument("--api-key", default=None, help="Optional X-API-Key for demo auth mode")
    parser.add_argument("--contact-id", default="lead_001", help="Contact ID for swipe request")
    parser.add_argument("--property-id", default="prop_001", help="Property ID for swipe request")
    parser.add_argument("--timeout", type=float, default=10.0, help="Request timeout in seconds")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    base_url = args.base_url.rstrip("/")

    swipe_request: SwipePayload = {
        "contact_id": args.contact_id,
        "property_id": args.property_id,
        "action": "like",
    }
    swipe_request_id = f"client-swipe-{uuid4()}"
    swipe_status, swipe_body, swipe_headers = _request_json(
        method="POST",
        url=f"{base_url}/portal/swipe",
        payload=swipe_request,
        request_id=swipe_request_id,
        api_key=args.api_key,
        timeout=args.timeout,
    )
    if swipe_status != 200:
        print(json.dumps({"step": "swipe", "status": swipe_status, "body": swipe_body}, indent=2))
        return 1

    swipe_result: SwipeResult = swipe_body  # type: ignore[assignment]
    print(
        json.dumps(
            {
                "step": "swipe",
                "status": swipe_status,
                "request_id_sent": swipe_request_id,
                "request_id_received": swipe_headers.get("x-request-id"),
                "result": swipe_result,
            },
            indent=2,
        )
    )

    details_request_id = f"client-details-{uuid4()}"
    details_status, details_body, details_headers = _request_json(
        method="GET",
        url=f"{base_url}/system/state/details?limit=2",
        payload=None,
        request_id=details_request_id,
        api_key=args.api_key,
        timeout=args.timeout,
    )
    if details_status != 200:
        print(json.dumps({"step": "state-details", "status": details_status, "body": details_body}, indent=2))
        return 1

    details_result: StateDetailsResult = details_body  # type: ignore[assignment]
    print(
        json.dumps(
            {
                "step": "state-details",
                "status": details_status,
                "request_id_sent": details_request_id,
                "request_id_received": details_headers.get("x-request-id"),
                "inventory_interactions": details_result["details"]["inventory"]["interaction_count"],
                "appointments": details_result["details"]["appointment"]["booking_count"],
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
