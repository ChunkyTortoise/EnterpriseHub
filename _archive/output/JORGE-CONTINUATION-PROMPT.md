# Jorge Bot — Post-Finalization Continuation Prompt

## Paste this into a new chat:

---

Continue Jorge bot cleanup from the finalization sprint (commit `081e0814`, 2026-02-19).

**Project root**: `/Users/cave/Projects/EnterpriseHub_new/`

## Context

The finalization sprint is done (13 beads, 4 tracks). Code is production-ready. 234 jorge tests passing in primary suite (`ghl_real_estate_ai/tests/`). Three cleanup items remain:

## Task 1: Fix 53 stale test failures in outer `tests/` directory

These are pre-existing mock mismatches, NOT from our sprint. Fix them:

### 1a. `tests/unit/test_jorge_tone_engine.py` (2 failures)
- `test_init_with_defaults` — references `self.profile` but class uses `self.tone_profile`
- `test_init_with_custom_profile` — passes `profile=` kwarg but `JorgeToneEngine.__init__()` doesn't accept it
- Fix: update tests to match actual class API in `ghl_real_estate_ai/services/jorge/jorge_tone_engine.py`

### 1b. `tests/test_jorge_delivery.py` (7 failures)
- All failures: `TypeError: 'MagicMock' object can't be awaited`
- Root cause: webhook handler calls async methods but tests mock with `MagicMock` instead of `AsyncMock`
- Fix: change `MagicMock()` to `AsyncMock()` for any mocked async function in the test fixtures

### 1c. `tests/security/test_jorge_webhook_security.py` (10+ failures)
- Webhook security test mocking issues
- Read the file, identify the mock pattern issue, fix

## Task 2: Migrate `jorge_seller_engine.py` off deprecated methods

The webhook active path in `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py` still calls 4 deprecated methods (now emit DeprecationWarning):
- Line ~778: `generate_cost_of_waiting_message` (loss_aversion persona)
- Line ~872: `generate_net_yield_justification` (low net yield)
- Line ~903: `generate_take_away_close` (low probability / vague streak)
- Line ~929: `generate_arbitrage_pitch` (investor persona)
- Lines ~1006, ~1017: `_apply_confrontational_tone` (investor + loss_aversion branches)
- Line ~688 (simple mode): `generate_take_away_close` (vague streak)

Replace with friendly equivalents that match the bot-layer pattern in `agents/seller/`. The `FRIENDLY_APPROACH=True` config is already default. Verify with: `python3 -m pytest ghl_real_estate_ai/tests/ -k "jorge" --tb=short -q`

## Task 3 (optional): Enable `conversation_repair` pipeline stage via env var

The `ConversationRepairProcessor` exists but is not in the default pipeline (by design). Consider adding an env var toggle:
- `CONVERSATION_REPAIR_ENABLED=false` (default off)
- When true, `factory.py` adds it as stage 4 (between compliance_check and ai_disclosure)

## Key Files

| File | Purpose |
|------|---------|
| `ghl_real_estate_ai/services/jorge/jorge_tone_engine.py` | Tone engine with 4 deprecated methods |
| `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py` | Webhook path calling deprecated methods |
| `ghl_real_estate_ai/services/enhanced_ghl_client.py` | GHL client with new calendar methods |
| `ghl_real_estate_ai/services/jorge/response_pipeline/factory.py` | Pipeline factory (5 stages) |
| `ghl_real_estate_ai/agents/seller/strategy_selector.py` | Friendly strategy selector (reference for migration) |
| `ghl_real_estate_ai/agents/seller/response_generator.py` | Friendly response generator (reference) |
| `ghl_real_estate_ai/agents/DEPLOYMENT_CHECKLIST.md` | Full deployment checklist |
| `ghl_real_estate_ai/services/jorge/TONE_DEPRECATION.md` | Deprecation documentation |
| `tests/unit/test_jorge_tone_engine.py` | Stale tone tests to fix |
| `tests/test_jorge_delivery.py` | Stale delivery tests to fix |
| `tests/security/test_jorge_webhook_security.py` | Stale security tests to fix |

## Verification

After all fixes:
```bash
# Primary suite (should stay at 234+, 0 failures)
python3 -m pytest ghl_real_estate_ai/tests/ -k "jorge" --tb=short -q

# Outer suite (target: reduce 53 failures to 0)
python3 -m pytest tests/ -k "jorge" --tb=short -q

# Verify no deprecation warnings in active paths
python3 -W error::DeprecationWarning -c "from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot; print('Clean')"
```

---
