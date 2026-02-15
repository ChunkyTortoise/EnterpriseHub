# Tone Deprecation Notice

The confrontational tone methods in `jorge_tone_engine.py` are **deprecated** as of February 2026.

## Rationale

The "almost confrontational" language style was aspirational but does not align with client
expectations. Jorge's verified persona is **friendly, consultative, and relationship-focused**.

## Deprecated Methods

- `generate_take_away_close` -- aggressive close for low-probability leads
- `generate_net_yield_justification` -- confrontational price justification
- `generate_cost_of_waiting_message` -- loss-aversion urgency messaging
- `generate_arbitrage_pitch` -- technical arbitrage pressure pitch

## Current Default

All seller bot code uses `FRIENDLY_APPROACH=True` and `USE_WARM_LANGUAGE=True` with tones:
CONSULTATIVE, EDUCATIONAL, ENTHUSIASTIC, UNDERSTANDING, SUPPORTIVE.
