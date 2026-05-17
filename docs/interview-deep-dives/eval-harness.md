# Eval Harness Deep Dive

The eval harness combines deterministic checks with LLM-as-judge scoring. It lives in `evals/judge.py`, with data in `evals/golden_dataset.json` and baseline thresholds in `evals/baseline.json`.

## What To Inspect

- Deterministic checks for length, URL leakage, proactive AI disclosure, and competitor mentions.
- Weighted rubric scoring for correctness, tone, safety, and compliance.
- `tests/test_eval_harness.py`, which verifies invalid judge JSON, threshold failures, and suite behavior without real LLM calls.
- Nightly eval workflow configuration in `.github/workflows/nightly-eval.yml`.

## Failure Analysis Example

A response with a URL, proactive AI disclosure, or competitor mention can fail deterministic checks even if the tone sounds good. That is intentional: compliance and safety constraints are hard gates, not style preferences.
