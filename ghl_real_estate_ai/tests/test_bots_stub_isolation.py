"""
Isolation tests for the ML engine stubs.

These guard the ``is_stub`` detection contract documented in
docs/adr/0012. Production code in ``predictive_lead_bot`` and
``client_preference_learning_engine`` branches on ``is_stub`` to skip
ML-dependent work when the real ``bots.shared`` engines are not vendored.
A regression that swaps a real engine in for a stub (or the reverse) would
silently break that contract; these tests catch it.

The stub assertions import only from ``ghl_real_estate_ai.stubs.bots_stub``,
which has no application dependencies and loads with no environment set. The
real-engine assertions import ``advanced_ml_lead_scoring_engine``, which
chains to config validation that raises ``SystemExit`` at import time when
required environment variables are absent; that import is therefore guarded
and skipped rather than aborting collection.
"""

import pytest

from ghl_real_estate_ai.stubs.bots_stub import (
    FeatureEngineeringPipeline,
    MLAnalyticsEngine,
)


def test_stub_ml_analytics_engine_is_stub_true():
    """The stub MLAnalyticsEngine advertises itself as a stub on the class."""
    assert MLAnalyticsEngine.is_stub is True


def test_stub_ml_analytics_engine_instance_is_stub_true():
    """Instances inherit the stub flag (production code may check either)."""
    assert MLAnalyticsEngine(tenant_id="test").is_stub is True


def test_stub_feature_engineering_pipeline_is_stub_true():
    """The stub FeatureEngineeringPipeline advertises itself as a stub."""
    assert FeatureEngineeringPipeline.is_stub is True
    assert FeatureEngineeringPipeline().is_stub is True


def test_real_engines_are_flagged_not_stub():
    """
    The real ML engines expose ``is_stub is False`` so a real->stub swap is
    caught. Skipped if the real module cannot import in this environment
    (it requires service config that raises SystemExit when env is absent).
    """
    try:
        from ghl_real_estate_ai.services.advanced_ml_lead_scoring_engine import (
            AdvancedMLLeadScoringEngine,
        )
        from ghl_real_estate_ai.services.advanced_ml_lead_scoring_engine import (
            FeatureEngineeringPipeline as RealFeatureEngineeringPipeline,
        )
    except (ImportError, SystemExit) as exc:
        pytest.skip(f"real ML engine module unavailable in this environment: {exc!r}")

    assert AdvancedMLLeadScoringEngine.is_stub is False
    assert RealFeatureEngineeringPipeline.is_stub is False


def test_stub_and_real_disagree_on_is_stub():
    """
    Cross-check: a stub and its real counterpart must report opposite
    ``is_stub`` values. This is the property that makes the flag useful for
    detecting an accidental substitution. Skipped if the real module cannot
    import (see test_real_engines_are_flagged_not_stub).
    """
    try:
        from ghl_real_estate_ai.services.advanced_ml_lead_scoring_engine import (
            FeatureEngineeringPipeline as RealFeatureEngineeringPipeline,
        )
    except (ImportError, SystemExit) as exc:
        pytest.skip(f"real ML engine module unavailable in this environment: {exc!r}")

    assert FeatureEngineeringPipeline.is_stub != RealFeatureEngineeringPipeline.is_stub
