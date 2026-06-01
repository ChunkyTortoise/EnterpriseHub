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

import asyncio
import os

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


def test_predictive_lead_bot_track3_degrades_when_ml_stub():
    """Track 3.1 short-circuits to a passthrough when the ML engine is a stub.

    Exercises the actual degradation branch in
    ``PredictiveLeadBot.apply_track3_market_intelligence`` (the consumer wiring
    added for ADR-0012). The stub branch reads only ``ml_analytics_is_stub`` and
    the passed state, so the heavy ``__init__`` is bypassed with
    ``object.__new__`` to keep the test independent of bot construction.
    """
    os.environ.setdefault("ANTHROPIC_API_KEY", "test")
    os.environ.setdefault("GHL_API_KEY", "test")
    os.environ.setdefault("GHL_LOCATION_ID", "test")
    try:
        from ghl_real_estate_ai.agents.predictive_lead_bot import PredictiveLeadBot
    except (ImportError, SystemExit) as exc:
        pytest.skip(f"predictive_lead_bot unavailable in this environment: {exc!r}")

    bot = object.__new__(PredictiveLeadBot)
    bot.ml_analytics_is_stub = True
    sentinel = object()
    state = {"lead_id": "test-lead", "sequence_optimization": sentinel}

    result = asyncio.run(bot.apply_track3_market_intelligence(state))

    assert result["track3_applied"] is False
    assert result["fallback_reason"] == "ml_analytics_engine_is_stub"
    assert result["enhanced_optimization"] is sentinel


def test_client_preference_health_check_reports_stub(monkeypatch):
    """health_check reports ml_analytics_engine="stub" when the engine is a stub.

    Exercises the status branch added for ADR-0012 by substituting a fake stub
    engine, so the assertion does not depend on constructing the real singleton.
    """
    os.environ.setdefault("ANTHROPIC_API_KEY", "test")
    os.environ.setdefault("GHL_API_KEY", "test")
    os.environ.setdefault("GHL_LOCATION_ID", "test")
    try:
        from ghl_real_estate_ai.services import (
            client_preference_learning_engine as cple,
        )
    except (ImportError, SystemExit) as exc:
        pytest.skip(f"client_preference_learning_engine unavailable: {exc!r}")

    class _FakeStubEngine:
        ml_engine_is_stub = True

        def get_metrics(self):
            return {}

    monkeypatch.setattr(cple, "get_client_preference_learning_engine", lambda: _FakeStubEngine())

    result = asyncio.run(cple.health_check())

    assert result["dependencies"]["ml_analytics_engine"] == "stub"
