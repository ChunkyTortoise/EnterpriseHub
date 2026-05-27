# EnterpriseHub Eval Scorecard

Date: 2026-05-23

## Summary

EnterpriseHub has a reviewer-ready AI evaluation surface: a 50-case golden dataset, deterministic response-property checks, LLM-as-judge rubric plumbing, a regression baseline, and a targeted pytest harness that passes locally.

## Current Verification

| Evidence | Result | Claim Type |
|---|---:|---|
| Golden dataset cases | 50 | Repository artifact |
| Dataset categories | seller 15, buyer 10, lead intake 10, edge case 10, compliance 5 | Repository artifact |
| Dataset difficulty | easy 16, medium 17, hard 17 | Repository artifact |
| Baseline rubrics | correctness 0.90, tone 0.90, safety 1.00, compliance 0.95 | Regression baseline |
| Targeted eval harness | 14/14 passed | Measured local command |

Command:

```bash
python3 -m pytest tests/test_eval_harness.py --override-ini='addopts=' -q
```

Observed result on 2026-05-23:

```text
14 passed
```

## Public Wording

Use:

> EnterpriseHub includes a 50-case golden dataset and a passing deterministic eval harness for qualification, edge cases, and compliance behavior.

Avoid:

> EnterpriseHub's live production model quality is proven by the eval scorecard.

The current scorecard proves the repo's eval discipline and deterministic checks. It does not prove live model quality without a fresh provider-backed eval run and committed output.
