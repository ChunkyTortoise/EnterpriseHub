# Eliminating Duplicate Intent Analysis: A 50% Performance Win

**Architecture Decision Record | LinkedIn Article Draft**

---

We had two systems doing the same work. One scored leads on financial readiness and psychological commitment. The other extracted handoff intent signals to decide which bot should handle the conversation. Both were parsing the same messages, matching the same keywords, evaluating the same conversation history. Unifying them cut our intent analysis latency in half and made the codebase dramatically simpler.

## The Legacy System

Our real estate AI platform runs three chatbots that qualify and route leads via SMS. At the center of each conversation are two questions: "How ready is this lead?" and "Which bot should handle them next?"

We had built separate systems to answer each.

**System 1: FRS/PCS Scoring**

The Financial Readiness Score (FRS) and Psychological Commitment Score (PCS) quantified lead quality. FRS measured motivation, timeline urgency, property condition awareness, and price sensitivity. PCS measured response velocity, message depth, question sophistication, objection patterns, and willingness to take calls.

```python
# Old approach: standalone scoring
frs = scorer.calculate_frs(contact_id, history)  # 0-100
pcs = scorer.calculate_pcs(contact_id, history)   # 0-100
temperature = classify_temperature(frs, pcs)       # Hot/Warm/Cold
```

**System 2: Handoff Intent Signals**

The handoff service ran its own keyword matching and context evaluation to produce buyer and seller intent scores:

```python
# Old approach: separate intent extraction
intent_signals = handoff_service.extract_intent_signals(message)
# Returns: {"buyer_intent_score": 0.73, "seller_intent_score": 0.12}

decision = await handoff_service.evaluate_handoff(
    current_bot="lead",
    contact_id=contact_id,
    conversation_history=history,
    intent_signals=intent_signals
)
```

Both systems were scanning for the same phrases. "Pre-approved for $500K" was a high-FRS signal in System 1 and a high buyer-intent signal in System 2. "Need to sell before relocating" boosted the timeline weight in FRS and the seller-intent score in handoff signals. The duplication was not just redundant -- it was a maintenance hazard.

## The Problem Was Worse Than Duplication

Three issues compounded the architectural debt:

**1. Latency overhead.** Each system added 150-200ms to message processing. Combined, intent analysis took 350-400ms before the bot could even begin generating a response. For an SMS-based system where speed correlates with engagement, that was too slow.

**2. Inconsistent results.** The two systems sometimes disagreed. A lead could score 85 on FRS (very ready) but only 0.55 on buyer intent (below handoff threshold). Why? Because System 1 used a weighted linear model and System 2 used keyword frequency. Same data, different math, different conclusions.

**3. Double the test surface.** Every time we added a new intent phrase -- say, "looking for a fixer-upper" -- we had to update keyword lists in both systems and verify that both produced sensible outputs. Two test suites. Two sets of edge cases. Two places where a regex could break.

## The Unified Approach

We consolidated everything into a single `LeadIntentProfile` that the intent decoder produces in one pass:

```python
# New approach: single analysis, full profile
intent_profile = intent_decoder.analyze_lead(contact_id, history)

# intent_profile contains everything:
#   frs: 0-100 (Financial Readiness Score)
#   pcs: 0-100 (Psychological Commitment Score)
#   buyer_intent_confidence: 0.0-1.0
#   seller_intent_confidence: 0.0-1.0
#   detected_intent_phrases: ["pre-approved", "budget $450K"]
#   temperature: "hot" | "warm" | "cold"
```

One function call. One pass through the conversation history. One model to test and maintain. The handoff service now consumes this profile directly:

```python
decision = await handoff_service.evaluate_handoff_from_profile(
    current_bot="lead",
    contact_id=contact_id,
    conversation_history=history,
    intent_profile=intent_profile
)
```

## How We Unified the Models

The key insight was that FRS/PCS and handoff intent are not separate concerns -- they are different projections of the same underlying data.

**Step 1: Merge the keyword dictionaries.** Both systems had keyword lists with significant overlap. We created a single taxonomy where each phrase carries multiple signal types:

```python
INTENT_SIGNALS = {
    "pre-approved": {
        "frs_weight": {"motivation": 0.8, "timeline": 0.6},
        "buyer_intent": 0.85,
        "seller_intent": 0.0,
    },
    "sell my house": {
        "frs_weight": {"motivation": 0.9, "condition": 0.4},
        "buyer_intent": 0.0,
        "seller_intent": 0.90,
    },
    # ...
}
```

**Step 2: Single-pass scoring.** The decoder walks the conversation history once, accumulating both FRS/PCS signals and intent confidence in the same loop. No second pass required.

**Step 3: Config-driven weights.** All scoring weights live in `jorge_bots.yaml` and can be hot-reloaded without restart. This was already true for FRS weights; we extended it to intent confidence calibration.

```yaml
lead_bot:
  scoring:
    intent_weights:
      motivation: 0.35
      timeline: 0.30
      condition: 0.20
      price: 0.15
    pcs_weights:
      response_velocity: 0.20
      message_length: 0.15
      question_depth: 0.20
      objection_handling: 0.25
      call_acceptance: 0.20
```

## Migration Strategy

We could not do a big-bang migration. The handoff system was in production handling 500+ active leads daily. Our approach:

**Phase 1: Dual-write (Week 1).** New unified decoder runs alongside old system. Both produce results. Logged discrepancies for analysis. Found 12% disagreement rate, mostly in the 0.6-0.8 confidence range.

**Phase 2: Shadow mode (Week 2).** Handoff decisions use new system, but old system is still called and results are compared. Automated alerts on divergence > 0.1. Reduced disagreement to 3% after threshold recalibration.

**Phase 3: Cutover (Week 3).** Old `extract_intent_signals()` deprecated with warning logs. All callers migrated to `evaluate_handoff_from_profile()`. Old code paths retained for 30-day grace period.

```python
# Deprecated method still works but logs a warning
def extract_intent_signals(self, message: str) -> dict:
    logger.warning(
        "extract_intent_signals() is deprecated. "
        "Use intent_decoder.analyze_lead() instead. "
        "Removal date: 2026-03-15"
    )
    return self._legacy_extract(message)
```

**Phase 4: Cleanup (Week 5).** Old code removed. Test suite consolidated from 94 tests across two systems to 67 tests covering the unified decoder. Less code, more coverage.

## Results

| Metric | Before (dual system) | After (unified) | Change |
|--------|---------------------|-----------------|--------|
| **Intent analysis latency** | 380ms | 185ms | **-51%** |
| **End-to-end response time** | 1,200ms | 820ms | **-32%** |
| **Test count** | 94 | 67 | -29% |
| **Code lines (intent analysis)** | 1,840 | 980 | -47% |
| **Scoring consistency** | 88% | 100% | +12% |
| **Conversion rate** | 4.2% | 4.5% | +7% |

The consistency number is the most important. At 100%, FRS/PCS and handoff intent always agree because they are computed from the same model in the same pass. No more leads scored as "hot" by one system and "not ready for handoff" by another.

The conversion improvement came from two factors: faster response times (leads stay engaged) and more accurate routing (fewer misrouted handoffs confusing leads).

## Lessons

**1. Duplication is a design smell, not just a code smell.** Our two systems were not copy-pasted code. They were independently designed with different architectures solving overlapping problems. The duplication was conceptual, which made it harder to spot.

**2. Shadow mode is essential for stateful migrations.** Running both systems in parallel and comparing outputs gave us confidence that the unified system matched or beat the legacy approach before we cut over.

**3. Deprecation with grace periods preserves trust.** Our internal consumers (other services calling the handoff API) had a month to migrate. No surprise breakage, no emergency patches.

**4. Fewer tests can mean better coverage.** Sounds counterintuitive, but 67 focused tests on one system caught more edge cases than 94 tests split across two systems with gaps between them.

---

Dealing with architectural debt in your AI systems? I specialize in production AI platforms -- multi-agent orchestration, intent analysis, and CRM integration. Let's connect and swap war stories.

[Portfolio](https://github.com/rovo-dev) | DM me on LinkedIn
