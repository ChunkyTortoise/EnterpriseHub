# Tone Deprecation Notice

The confrontational tone methods in `jorge_tone_engine.py` are **deprecated** as of February 2026.

## Rationale

The "almost confrontational" language style was aspirational but does not align with client
expectations. Jorge's verified persona is **friendly, consultative, and relationship-focused**.

## Deprecated Methods

Each method now emits a `DeprecationWarning` via `warnings.warn(...)` on every call:

| Method | Purpose (deprecated) | Warning added |
|--------|---------------------|---------------|
| `generate_take_away_close` | Aggressive close for low-probability leads | Yes |
| `generate_net_yield_justification` | Confrontational price justification | Yes |
| `generate_cost_of_waiting_message` | Loss-aversion urgency messaging | Yes |
| `generate_arbitrage_pitch` | Technical arbitrage pressure pitch | Yes |

## Active Callers (to be migrated)

These files still invoke the deprecated methods via `jorge_seller_engine.py`:

- `jorge_seller_engine.py:688` -- calls `generate_take_away_close` (low-probability path)
- `jorge_seller_engine.py:903` -- calls `generate_take_away_close` (dynamic branching)
- `jorge_seller_engine.py:872` -- calls `generate_net_yield_justification` (price objection)
- `jorge_seller_engine.py:778` -- calls `generate_cost_of_waiting_message` (loss_aversion persona)
- `jorge_seller_engine.py:929` -- calls `generate_arbitrage_pitch` (investor persona)

## Migration Path

Replace deprecated calls with friendly equivalents from the active tone system:
- `generate_qualification_message()` -- standard qualification flow
- `generate_follow_up_message()` -- consultative follow-ups
- `generate_objection_response()` -- empathetic objection handling
- `generate_labeled_question()` -- Voss-style labeling (non-confrontational)
- `generate_calibrated_question()` -- calibrated questions

## Current Default

All seller bot code uses `FRIENDLY_APPROACH=True` and `USE_WARM_LANGUAGE=True` with tones:
CONSULTATIVE, EDUCATIONAL, ENTHUSIASTIC, UNDERSTANDING, SUPPORTIVE.

## Verification

Run `python -W all -c "from ghl_real_estate_ai.services.jorge.jorge_tone_engine import JorgeToneEngine; e = JorgeToneEngine(); e.generate_take_away_close()"` to confirm warnings are emitted.
