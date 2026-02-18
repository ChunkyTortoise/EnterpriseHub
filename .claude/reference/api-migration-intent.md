# API Migration: Unified Intent Analysis (Feb 2026)

**Status**: Deprecated API removes 2026-03-15. All new code must use unified API.

## New API (use this)

```python
intent_profile = intent_decoder.analyze_lead(contact_id, history)
# Returns LeadIntentProfile with:
#   frs, pcs (0-100), buyer_intent_confidence, seller_intent_confidence, detected_intent_phrases

decision = await handoff_service.evaluate_handoff_from_profile(
    current_bot="lead",
    contact_id=contact_id,
    conversation_history=history,
    intent_profile=intent_profile
)
```

## Old API (deprecated 2026-02-15, removed 2026-03-15)

```python
intent_signals = handoff_service.extract_intent_signals(message)
decision = await handoff_service.evaluate_handoff(..., intent_signals=intent_signals)
```

## Migration Checklist

- [ ] Replace `extract_intent_signals()` → `analyze_lead()`
- [ ] Replace `evaluate_handoff()` → `evaluate_handoff_from_profile()`
- [ ] Update tests: use `LeadIntentProfile` instead of `IntentSignals` dict
- [ ] Verify handoff routing (confidence thresholds unchanged at 0.7)

## Benefits

- 50% faster intent analysis (no duplicate pattern matching)
- FRS/PCS + handoff signals in one unified object
- Easier mocking in tests
