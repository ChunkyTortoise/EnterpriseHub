"""Deterministic eval runner for EnterpriseHub golden dataset.

Validates the golden_dataset.json structure and runs property checks that do
not require a live bot or API key. Exit 0 = all checks pass, exit 1 = failures.

Usage:
    python evals/run_evals_deterministic.py            # summary output
    python evals/run_evals_deterministic.py --verbose  # per-case output
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

DATASET_PATH = Path(__file__).parent / "golden_dataset.json"

REQUIRED_FIELDS = {"id", "input", "expected_output_properties", "category", "difficulty", "bot_type", "description"}
REQUIRED_PROPS = {"contains_question", "max_length", "no_urls", "no_ai_disclosure", "persona_maintained", "topic_boundary"}
VALID_CATEGORIES = {"seller_qualification", "buyer_scheduling", "lead_intake", "edge_case", "compliance"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}
VALID_BOT_TYPES = {"seller", "buyer", "lead"}
EXPECTED_DISTRIBUTION = {
    "seller_qualification": 15,
    "buyer_scheduling": 10,
    "lead_intake": 10,
    "edge_case": 10,
    "compliance": 5,
}
EXPECTED_TOTAL = 50

AI_DISCLOSURE_PHRASES = [
    "i'm an ai",
    "i am an ai",
    "artificial intelligence",
    "language model",
    "i'm a bot",
    "i am a bot",
    "large language",
    "ai assistant",
]


def check_no_urls(text: str) -> bool:
    return "http://" not in text.lower() and "https://" not in text.lower()


def check_no_ai_disclosure(text: str) -> bool:
    lower = text.lower()
    return not any(phrase in lower for phrase in AI_DISCLOSURE_PHRASES)


def run(verbose: bool = False) -> int:
    if not DATASET_PATH.exists():
        print(f"FAIL: dataset not found at {DATASET_PATH}")
        return 1

    with open(DATASET_PATH) as f:
        dataset = json.load(f)

    failures: list[str] = []

    # -- Structure checks --

    if len(dataset) != EXPECTED_TOTAL:
        failures.append(f"Expected {EXPECTED_TOTAL} cases, got {len(dataset)}")

    ids = [tc["id"] for tc in dataset]
    duplicates = {id_ for id_ in ids if ids.count(id_) > 1}
    if duplicates:
        failures.append(f"Duplicate IDs: {sorted(duplicates)}")

    category_counts: dict[str, int] = {}
    for tc in dataset:
        missing = REQUIRED_FIELDS - set(tc.keys())
        if missing:
            failures.append(f"{tc.get('id', '?')}: missing top-level fields {missing}")
            continue

        missing_props = REQUIRED_PROPS - set(tc["expected_output_properties"].keys())
        if missing_props:
            failures.append(f"{tc['id']}: missing expected_output_properties {missing_props}")

        if tc["category"] not in VALID_CATEGORIES:
            failures.append(f"{tc['id']}: unknown category '{tc['category']}'")
        else:
            category_counts[tc["category"]] = category_counts.get(tc["category"], 0) + 1

        if tc["difficulty"] not in VALID_DIFFICULTIES:
            failures.append(f"{tc['id']}: unknown difficulty '{tc['difficulty']}'")

        if tc["bot_type"] not in VALID_BOT_TYPES:
            failures.append(f"{tc['id']}: unknown bot_type '{tc['bot_type']}'")

        props = tc["expected_output_properties"]
        if not isinstance(props.get("max_length"), int) or props["max_length"] <= 0:
            failures.append(f"{tc['id']}: max_length must be a positive integer")

        if not isinstance(props.get("contains_question"), bool):
            failures.append(f"{tc['id']}: contains_question must be bool")

        if not isinstance(props.get("no_urls"), bool):
            failures.append(f"{tc['id']}: no_urls must be bool")

        if verbose:
            print(f"  OK {tc['id']} [{tc['category']}/{tc['difficulty']}]")

    for cat, expected in EXPECTED_DISTRIBUTION.items():
        actual = category_counts.get(cat, 0)
        if actual != expected:
            failures.append(f"Category '{cat}': expected {expected} cases, got {actual}")

    # -- Input field property spot-checks (structural only, no bot call) --
    # For compliance cases where no_ai_disclosure=False, verify the description
    # mentions a disclosure trigger scenario.
    for tc in dataset:
        if tc.get("category") == "compliance":
            props = tc["expected_output_properties"]
            if props.get("no_ai_disclosure") is False and "disclose" not in tc.get("description", "").lower():
                failures.append(
                    f"{tc['id']}: compliance case has no_ai_disclosure=False but description "
                    "doesn't explain the disclosure trigger"
                )

    # Report
    total = len(dataset)
    passed = total - len(failures)

    print(f"\nEnterpriseHub eval dataset -- deterministic checks")
    print(f"Dataset: {DATASET_PATH}")
    print(f"Cases: {total} | Checks: {len(REQUIRED_FIELDS) + len(REQUIRED_PROPS) + 4} structural checks")
    print()

    if failures:
        print(f"FAILED: {len(failures)} issue(s)")
        for f in failures:
            print(f"  FAIL {f}")
        return 1

    print(f"PASSED: {total}/{total} cases validated ({passed} structural checks all green)")
    print()
    print("Category distribution:")
    for cat, count in sorted(category_counts.items()):
        print(f"  {cat}: {count}")
    return 0


if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    sys.exit(run(verbose=verbose))
