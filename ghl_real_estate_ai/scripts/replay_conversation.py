#!/usr/bin/env python3
"""
Conversation Replay Script for Jorge Bots.

Reads a JSON turn file and drives the seller or buyer bot through
each user turn sequentially, printing bot responses to stdout.

Usage:
    python replay_conversation.py --bot seller --turns turns/seller_hot.json
    python replay_conversation.py --bot buyer  --turns turns/buyer_budget.json --base-url https://jorge-realty-ai.onrender.com

Turn file format (JSON array):
    [
        {"role": "user", "content": "I want to sell my house in 90 days"},
        {"role": "user", "content": "3 bed 2 bath, around 1800 sqft"},
        {"role": "user", "content": "I owe about 380k on it"},
        {"role": "user", "content": "I need at least 450k"}
    ]

Only "user" role turns are replayed; "assistant" entries are skipped
(the script captures the live bot responses instead).

Outputs:
    TURN 1  [user]      I want to sell my house in 90 days
            [seller]    ...bot response...
            [data]      {"property_address": null, ...}
            [temp]      warm
    ...
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
import time
import urllib.error
import urllib.request
from typing import Any


BASE_URL_DEFAULT = "http://localhost:8000"
SELLER_ENDPOINT = "/test/seller"
BUYER_ENDPOINT  = "/test/buyer"

COL_RESET  = "\033[0m"
COL_CYAN   = "\033[96m"
COL_GREEN  = "\033[92m"
COL_YELLOW = "\033[93m"
COL_RED    = "\033[91m"
COL_GREY   = "\033[90m"
COL_BOLD   = "\033[1m"


def _c(color: str, text: str, use_color: bool = True) -> str:
    return f"{color}{text}{COL_RESET}" if use_color else text


def _post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc


def _load_turns(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        turns = json.load(fh)
    if not isinstance(turns, list):
        raise ValueError("Turn file must be a JSON array")
    return turns


def _print_turn(
    turn_num: int,
    user_msg: str,
    result: dict,
    bot_type: str,
    use_color: bool,
    verbose: bool,
) -> None:
    sep = "─" * 72
    print(_c(COL_GREY, sep, use_color))
    print(
        _c(COL_BOLD, f"TURN {turn_num}", use_color)
        + f"  [{_c(COL_CYAN, 'user', use_color)}]  "
        + user_msg
    )

    response = result.get("response", "")
    wrapped = textwrap.fill(response, width=72, initial_indent="        ", subsequent_indent="        ")
    label = _c(COL_GREEN, bot_type, use_color)
    print(f"        [{label}]  {response[:72]}")
    if len(response) > 72:
        print(wrapped[8:])  # already has indent

    temp = result.get("temperature")
    if temp:
        color = COL_RED if "hot" in temp.lower() else COL_YELLOW if "warm" in temp.lower() else COL_GREY
        print(f"        [temp]   {_c(color, temp, use_color)}")

    if verbose:
        data = result.get("extracted_data") or {}
        if data:
            print(f"        [data]   {json.dumps(data, indent=None)}")
        actions = result.get("actions") or []
        if actions:
            print(f"        [actions] {json.dumps(actions)}")


def replay(
    bot: str,
    turns_path: str,
    base_url: str,
    contact_id: str,
    buyer_name: str,
    reset: bool,
    verbose: bool,
    use_color: bool,
) -> None:
    turns = _load_turns(turns_path)
    endpoint = (SELLER_ENDPOINT if bot == "seller" else BUYER_ENDPOINT)
    url = base_url.rstrip("/") + endpoint

    print(_c(COL_BOLD, f"\n{'═'*72}", use_color))
    print(_c(COL_BOLD, f"  Jorge {bot.capitalize()} Bot — Replay", use_color))
    print(f"  Turns file : {turns_path}")
    print(f"  Endpoint   : {url}")
    print(f"  Contact ID : {contact_id}")
    print(_c(COL_BOLD, f"{'═'*72}\n", use_color))

    # Reset session first if requested
    if reset:
        try:
            del_req = urllib.request.Request(
                base_url.rstrip("/") + f"/test/session/{contact_id}",
                method="DELETE",
            )
            urllib.request.urlopen(del_req, timeout=10)
        except Exception:
            pass

    turn_num = 0
    errors = 0
    t0 = time.time()

    for item in turns:
        if item.get("role") != "user":
            continue
        turn_num += 1
        user_msg = item.get("content") or item.get("message") or ""
        if not user_msg:
            continue

        payload: dict[str, Any] = {
            "message": user_msg,
            "contact_id": contact_id,
        }
        if bot == "buyer":
            payload["buyer_name"] = buyer_name

        try:
            result = _post(url, payload)
        except RuntimeError as exc:
            errors += 1
            print(_c(COL_RED, f"  ERROR on turn {turn_num}: {exc}", use_color))
            continue

        _print_turn(turn_num, user_msg, result, bot, use_color, verbose)

    elapsed = time.time() - t0
    print(_c(COL_GREY, "─" * 72, use_color))
    status = _c(COL_GREEN, "DONE", use_color) if errors == 0 else _c(COL_RED, f"DONE ({errors} errors)", use_color)
    print(f"  {status}  —  {turn_num} turns in {elapsed:.1f}s")
    print()

    if errors:
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replay a canned conversation against the Jorge bot smoke-test endpoints.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--bot", choices=["seller", "buyer"], required=True,
                        help="Which bot to test")
    parser.add_argument("--turns", required=True,
                        help="Path to turns JSON file")
    parser.add_argument("--base-url", default=BASE_URL_DEFAULT,
                        help=f"Base URL of the running server (default: {BASE_URL_DEFAULT})")
    parser.add_argument("--contact-id", default="replay-test",
                        help="contact_id to use for the session (default: replay-test)")
    parser.add_argument("--buyer-name", default="Test Buyer",
                        help="Buyer name for buyer bot (default: 'Test Buyer')")
    parser.add_argument("--reset", action="store_true",
                        help="Clear the session before replaying")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print extracted_data and actions for each turn")
    parser.add_argument("--no-color", action="store_true",
                        help="Disable ANSI color output")
    args = parser.parse_args()

    replay(
        bot=args.bot,
        turns_path=args.turns,
        base_url=args.base_url,
        contact_id=args.contact_id,
        buyer_name=args.buyer_name,
        reset=args.reset,
        verbose=args.verbose,
        use_color=not args.no_color,
    )


if __name__ == "__main__":
    main()
