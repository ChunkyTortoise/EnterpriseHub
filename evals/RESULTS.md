# Eval Results

## Deterministic Checks (no API key required)

Run: `python evals/run_evals_deterministic.py`

| Check | Result |
|---|---|
| Total cases | 50/50 |
| No duplicate IDs | PASS |
| Required fields present | PASS |
| Category distribution matches spec | PASS |
| Valid difficulty / bot_type values | PASS |
| max_length is positive int | PASS |
| Compliance disclosure cases explained | PASS |

**Last run:** 2026-04-26 | **Exit code:** 0

Category distribution:
- seller_qualification: 15
- buyer_scheduling: 10
- lead_intake: 10
- edge_case: 10
- compliance: 5

---

## LLM-as-Judge (requires ANTHROPIC_API_KEY)

Run: see `evals/judge.py` and `evals/README.md` for full instructions.

Property checks validate bot response structure (max_length, no_urls, no_ai_disclosure).
LLM-as-judge scores on tone, correctness, persona, and compliance adherence.

Not yet integrated into CI (requires live bot deployment and API key).
Gate target: >= 0.80 overall score across all 50 cases.
