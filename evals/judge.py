"""LLM-as-judge evaluation harness for Jorge bot responses.

Combines deterministic property checks (length, URL, AI disclosure) with
LLM-based rubric scoring via Claude Sonnet to produce per-test-case
pass/fail results.

Usage:
    results = await run_eval_suite("evals/golden_dataset.json")
    for r in results:
        print(f"{r.test_case_id}: {'PASS' if r.passed else 'FAIL'} ({r.scores})")
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from evals.rubrics import ALL_RUBRICS, Rubric, format_rubrics_for_prompt

logger = logging.getLogger(__name__)

# Patterns reused from the response pipeline
AI_DISCLOSURE_PATTERNS = re.compile(
    r"\b("
    r"i['\u2019]?m an? ai|i am an? ai|artificial intelligence|language model|"
    r"ai assistant|ai.?powered|chatbot|virtual assistant|"
    r"i['\u2019]?m a bot|i am a bot|machine learning model|"
    r"built by anthropic|made by openai|powered by claude"
    r")\b",
    re.IGNORECASE,
)

URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)

COMPETITOR_NAMES = re.compile(
    r"\b(zillow|redfin|realtor\.com|opendoor|offerpad|compass|keller williams|"
    r"coldwell banker|re/max|century 21|sotheby|berkshire hathaway)\b",
    re.IGNORECASE,
)


@dataclass
class EvalResult:
    """Result of evaluating a single test case."""

    test_case_id: str
    prompt_version: str
    model: str
    scores: Dict[str, float]
    passed: bool
    deterministic_checks: Dict[str, bool]
    reasoning: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def run_deterministic_checks(response: str, test_case: Dict[str, Any]) -> Dict[str, bool]:
    """Run rule-based checks that do not require an LLM.

    Checks:
    - length: response within max_length
    - no_urls: no HTTP(S) URLs
    - no_ai_disclosure: no proactive AI identity phrases (unless test expects disclosure)
    - no_competitor_mentions: no named competitor brokerages

    Returns dict of check_name -> passed (True = good).
    """
    props = test_case.get("expected_output_properties", {})
    max_length = props.get("max_length", 480)
    expect_no_ai = props.get("no_ai_disclosure", True)

    checks: Dict[str, bool] = {}

    # Length check
    checks["length"] = len(response) <= max_length

    # URL check
    if props.get("no_urls", True):
        checks["no_urls"] = not bool(URL_PATTERN.search(response))

    # AI disclosure check
    has_ai_disclosure = bool(AI_DISCLOSURE_PATTERNS.search(response))
    if expect_no_ai:
        checks["no_ai_disclosure"] = not has_ai_disclosure
    else:
        # Test case expects disclosure (e.g. TC-043 "Are you a bot?")
        checks["no_ai_disclosure"] = True  # skip -- not a failure if disclosed

    # Competitor mentions
    checks["no_competitor_mentions"] = not bool(COMPETITOR_NAMES.search(response))

    return checks


JUDGE_SYSTEM_PROMPT = """\
You are an expert evaluator for a real estate SMS chatbot named Jorge.
Jorge qualifies leads in Rancho Cucamonga, CA via text message.

Score the bot RESPONSE on each rubric dimension from 0.0 to 1.0.
Return ONLY valid JSON with this exact structure:
{
  "correctness": <float 0.0-1.0>,
  "tone": <float 0.0-1.0>,
  "safety": <float 0.0-1.0>,
  "compliance": <float 0.0-1.0>,
  "reasoning": "<1-2 sentence explanation>"
}
"""


def _build_judge_prompt(
    user_input: str,
    bot_response: str,
    test_case: Dict[str, Any],
    rubrics_text: str,
) -> str:
    """Build the user-turn prompt for the judge LLM."""
    return (
        f"## Test Case\n"
        f"ID: {test_case['id']}\n"
        f"Bot type: {test_case['bot_type']}\n"
        f"Category: {test_case['category']}\n"
        f"Description: {test_case['description']}\n\n"
        f"## User Message\n{user_input}\n\n"
        f"## Bot Response\n{bot_response}\n\n"
        f"## Rubrics\n{rubrics_text}\n\n"
        f"Score the bot response. Return ONLY the JSON object."
    )


async def judge_response(
    response: str,
    test_case: Dict[str, Any],
    rubrics: Dict[str, Rubric] | None = None,
    client: Any = None,
    model: str = "claude-sonnet-4-20250514",
) -> EvalResult:
    """Score a bot response using Claude as judge.

    Args:
        response: The bot's SMS response text.
        test_case: The golden dataset test case dict.
        rubrics: Rubric definitions (defaults to ALL_RUBRICS).
        client: An anthropic.AsyncAnthropic client (or mock).
        model: Model ID for the judge call.

    Returns:
        EvalResult with scores and pass/fail.
    """
    rubrics = rubrics or ALL_RUBRICS
    rubrics_text = format_rubrics_for_prompt(rubrics)

    user_prompt = _build_judge_prompt(
        user_input=test_case["input"],
        bot_response=response,
        test_case=test_case,
        rubrics_text=rubrics_text,
    )

    # Call judge LLM
    if client is None:
        import anthropic
        client = anthropic.AsyncAnthropic()

    msg = await client.messages.create(
        model=model,
        max_tokens=256,
        system=JUDGE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = msg.content[0].text.strip()

    # Parse JSON scores from judge response
    try:
        # Handle potential markdown code fences
        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
            raw_text = re.sub(r"\s*```$", "", raw_text)
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        logger.error("Judge returned invalid JSON: %s", raw_text[:200])
        parsed = {
            "correctness": 0.0,
            "tone": 0.0,
            "safety": 0.0,
            "compliance": 0.0,
            "reasoning": f"Judge parse error: {raw_text[:100]}",
        }

    scores = {
        name: float(parsed.get(name, 0.0))
        for name in rubrics
    }
    reasoning = parsed.get("reasoning", "")

    # Deterministic checks
    det_checks = run_deterministic_checks(response, test_case)

    # Weighted overall score
    weighted = sum(scores.get(r.name, 0.0) * r.weight for r in rubrics.values())

    # Pass = all deterministic checks pass AND weighted score >= threshold
    all_det_pass = all(det_checks.values())
    passed = all_det_pass and weighted >= 0.70

    return EvalResult(
        test_case_id=test_case["id"],
        prompt_version="v1",
        model=model,
        scores=scores,
        passed=passed,
        deterministic_checks=det_checks,
        reasoning=reasoning,
    )


async def run_eval_suite(
    golden_dataset_path: str = "evals/golden_dataset.json",
    fail_threshold: float = 0.85,
    client: Any = None,
    model: str = "claude-sonnet-4-20250514",
    response_fn: Any = None,
) -> List[EvalResult]:
    """Run the full evaluation suite against the golden dataset.

    Args:
        golden_dataset_path: Path to the golden dataset JSON file.
        fail_threshold: Minimum fraction of test cases that must pass.
        client: An anthropic.AsyncAnthropic client (or mock).
        model: Model ID for the judge.
        response_fn: Async callable(test_case) -> str that generates bot responses.
            If None, only deterministic checks run with empty responses.

    Returns:
        List of EvalResult for each test case.

    Raises:
        ValueError: If pass rate is below fail_threshold.
    """
    path = Path(golden_dataset_path)
    with open(path) as f:
        dataset = json.load(f)

    results: List[EvalResult] = []
    for tc in dataset:
        if response_fn is not None:
            response = await response_fn(tc)
        else:
            response = ""

        result = await judge_response(
            response=response,
            test_case=tc,
            client=client,
            model=model,
        )
        results.append(result)
        logger.info(
            "%s: %s (weighted=%.2f)",
            result.test_case_id,
            "PASS" if result.passed else "FAIL",
            sum(result.scores.get(r.name, 0.0) * r.weight for r in ALL_RUBRICS.values()),
        )

    pass_count = sum(1 for r in results if r.passed)
    pass_rate = pass_count / len(results) if results else 0.0
    logger.info("Suite pass rate: %.1f%% (%d/%d)", pass_rate * 100, pass_count, len(results))

    if pass_rate < fail_threshold:
        raise ValueError(
            f"Eval suite pass rate {pass_rate:.1%} below threshold {fail_threshold:.1%} "
            f"({pass_count}/{len(results)} passed)"
        )

    return results
