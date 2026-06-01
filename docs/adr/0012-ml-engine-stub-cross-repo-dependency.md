# ADR 0012: ML Engine Stubs and the bots.shared Cross-Repo Dependency

## Status

Accepted

## Context

Two predictive-intelligence features import their ML engines from a `bots.shared`
package:

- `ghl_real_estate_ai/agents/predictive_lead_bot.py` imports `MLAnalyticsEngine`
  (and the `LeadJourneyPrediction`, `ConversionProbabilityAnalysis`,
  `TouchpointOptimization` result types) from `bots.shared.ml_analytics_engine`.
- `ghl_real_estate_ai/services/client_preference_learning_engine.py` imports
  `get_ml_analytics_engine` from the same package.

That `bots.shared` package is not vendored into this repository. It belongs to a
separate codebase and is not present on the import path here. Each import site is
wrapped in `try/except ImportError`, and the `except` branch falls back to
`ghl_real_estate_ai/stubs/bots_stub.py`. So in every standalone checkout of
EnterpriseHub, the ML engines resolve to the stub, not the real implementation.

The stub classes (`MLAnalyticsEngine`, `FeatureEngineeringPipeline`) are no-ops:
their methods return empty or zero-valued dataclasses. Before this ADR there was
no way for production code or a test to tell at runtime whether it held a real
engine or the stub. The stub also does not implement the Track 3.1 methods that
`predictive_lead_bot` calls (`predict_lead_journey`,
`predict_conversion_probability`, `predict_optimal_touchpoints`); those calls
raised `AttributeError` and were swallowed by a broad downstream `except`, which
hid the cause behind a generic failure log.

Separately, this repository contains its own real feature-engineering and ML
scoring code in `ghl_real_estate_ai/services/advanced_ml_lead_scoring_engine.py`
(`FeatureEngineeringPipeline`, `AdvancedMLLeadScoringEngine`) and
`ghl_real_estate_ai/ml/feature_engineering.py` (`FeatureEngineer`). These are
real implementations, but their call signatures do not match the
`bots.shared.MLAnalyticsEngine` interface the two consumers expect (the local
engine exposes `score_lead_comprehensive(lead_id, lead_data)`, not the Track 3.1
`predict_*` methods). They are therefore not drop-in replacements for the stub at
those call sites.

## Decision

### Detection contract: `is_stub`

Every ML engine class carries a boolean class attribute `is_stub` that production
code and tests can read without instantiating the class or catching an exception.

- Stub classes in `ghl_real_estate_ai/stubs/bots_stub.py` set `is_stub = True`:
  `MLAnalyticsEngine`, `FeatureEngineeringPipeline`.
- Real classes in
  `ghl_real_estate_ai/services/advanced_ml_lead_scoring_engine.py` set
  `is_stub = False`: `FeatureEngineeringPipeline`, `AdvancedMLLeadScoringEngine`.

Consumers read the flag defensively with `getattr(engine, "is_stub", False)` so an
engine that predates the contract is treated as real (the conservative default,
matching prior behavior).

The contract is pinned by
`ghl_real_estate_ai/tests/test_bots_stub_isolation.py`, which asserts the stub
engines report `is_stub is True`, asserts the real engines report
`is_stub is False` (skipped when the real module cannot import in a
service-less environment), and cross-checks that a stub and its real counterpart
disagree. A regression that swaps a real engine for a stub, or drops the flag,
fails those assertions.

### Consumer behavior on the stub

The import-level `try/except` already prefers the real engine when `bots.shared`
is importable and falls back to the stub otherwise. No local real engine has a
matching call signature, so no in-process substitution of a real engine for the
stub is possible at these call sites without a broader interface change. That
change is out of scope here (see Negative consequences). Instead, each consumer
detects the stub and degrades explicitly:

- `PredictiveLeadBot.__init__` records `ml_analytics_is_stub` and logs a warning.
  `apply_track3_market_intelligence` short-circuits when the engine is a stub,
  returning the same dict shape as its existing exception path
  (`track3_applied=False`, `fallback_reason="ml_analytics_engine_is_stub"`,
  `enhanced_optimization` set to the unchanged behavioral
  `sequence_optimization`). Downstream nodes already handle that shape, so the
  nurture sequence proceeds on behavioral optimization with no change in
  outputs. This replaces the previous reliance on a swallowed `AttributeError`.
  The short-circuit returns before the `status="processing"` bot-status event
  that the old failing path emitted, so the event stream carries one fewer
  status event in the stub case. No consumer reads that event for control flow,
  so this is cosmetic.
- `ClientPreferenceLearningEngine.__init__` records `ml_engine_is_stub` and logs
  a warning when the stub is in use. The engine's `health_check` reports
  `ml_analytics_engine: "stub"` instead of the previous unconditional
  `"connected"`. The stored `self.ml_engine` is otherwise not called anywhere in
  the engine, so no scoring path changes.

## Consequences

### Positive

- Whether the system is running on the real ML engine or the stub is now
  observable: a class attribute for code, log warnings at startup, and an honest
  `health_check` value. The over-claim of an unconditional `"connected"`
  dependency is gone.
- `predictive_lead_bot` no longer depends on an `AttributeError` being raised and
  caught to take the fallback path. The stub case is handled before the doomed
  calls, so the fallback reason is explicit rather than a generic exception
  string.
- The `is_stub` contract is regression-tested, so a future change that vendors a
  real engine, or that accidentally substitutes a stub for a real engine, is
  caught by `test_bots_stub_isolation.py`.
- The change is additive and behavior-preserving. The track3 short-circuit
  returns the exact dict shape the prior exception path returned, so no
  downstream node sees a new value.

### Negative

- The Track 3.1 market-timing features in `predictive_lead_bot`
  (journey-progression prediction, stage-specific conversion probability,
  touchpoint optimization) remain no-ops in any checkout without `bots.shared`.
  The nurture sequence falls back to behavioral sequence optimization. This is
  unchanged from prior behavior; this ADR documents it rather than fixing it.
- ML-derived preference signals in `client_preference_learning_engine` are
  unavailable on the stub. Preference learning still runs on its conversation,
  property-interaction, and behavioral extractors, which do not depend on the ML
  engine, so the effect is the absence of one signal source rather than a broken
  pipeline.
- A real local engine is not preferred at these call sites because its signature
  does not match the `bots.shared.MLAnalyticsEngine` interface the consumers
  call. Wiring the local `AdvancedMLLeadScoringEngine` or `FeatureEngineer` in
  would require an adapter that maps `score_lead_comprehensive` output onto the
  `LeadJourneyPrediction` / `ConversionProbabilityAnalysis` /
  `TouchpointOptimization` shapes the bot consumes. That adapter is a larger
  change with its own correctness risk and is deliberately deferred.
- Detection depends on each engine setting `is_stub` correctly. A new engine that
  omits the flag is treated as real by the `getattr` default and would bypass the
  stub-degradation path. The isolation test reduces but does not remove this
  risk, since it only checks the engines that exist today.
