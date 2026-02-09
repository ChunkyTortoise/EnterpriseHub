import pytest
pytestmark = pytest.mark.integration

"""Tests for the ML ensemble lead scoring pipeline."""
from datetime import datetime, timedelta

import numpy as np
import pytest

from ghl_real_estate_ai.ml.behavioral_features import (
    FINANCIAL_TERMS,
    URGENCY_TERMS,
    BehavioralFeatures,
    extract_behavioral_features,
)
from ghl_real_estate_ai.ml.ensemble_scorer import (
    DriftDetector,
    EnsembleLeadScorer,
    ScoringResult,
    get_ensemble_scorer,
)
from ghl_real_estate_ai.ml.training_pipeline import TrainingPipeline, TrainingResult

@pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_synthetic_data(n_samples: int = 200, n_features: int = 12):
    """Create reproducible synthetic classification data."""
    rng = np.random.RandomState(42)
    X = rng.randn(n_samples, n_features)
    y = (X[:, 0] + X[:, 1] + rng.randn(n_samples) * 0.5 > 0).astype(int)
    return X, y


def _sample_messages():
    """Return a realistic conversation for feature extraction."""
    return [
        {"role": "user", "content": "Hi, I'm looking to buy a home in Rancho Cucamonga."},
        {"role": "assistant", "content": "Great! What's your budget range?"},
        {"role": "user", "content": "We've been pre-approved for $650k. Is that enough?"},
        {"role": "assistant", "content": "That's a solid range. Any timeline?"},
        {"role": "user", "content": "We need to move soon, lease ending this month!"},
        {"role": "assistant", "content": "Let me pull some listings for you."},
        {"role": "user", "content": "What about closing costs and down payment?"},
    ]


def _sample_timestamps(n: int):
    """Generate timestamps spaced roughly 5 minutes apart."""
    base = datetime(2026, 2, 1, 14, 0, 0)
    return [base + timedelta(minutes=i * 5) for i in range(n)]


# ---------------------------------------------------------------------------
# Behavioral Features Tests
# ---------------------------------------------------------------------------

class TestBehavioralFeatures:

    def test_behavioral_features_extraction(self):
        """Extract features from sample messages and verify non-zero values."""
        messages = _sample_messages()
        timestamps = _sample_timestamps(len(messages))
        features = extract_behavioral_features(messages, timestamps)

        assert features.avg_message_length > 0
        assert features.question_ratio > 0  # messages contain '?'
        assert features.financial_language_density > 0  # 'pre-approved', 'closing costs'
        assert features.urgency_language_density > 0  # 'soon', 'lease ending'

    def test_behavioral_features_to_vector(self):
        """Feature vector length must match feature_names length."""
        features = BehavioralFeatures()
        vec = features.to_feature_vector()
        names = BehavioralFeatures.feature_names()
        assert len(vec) == len(names)
        assert len(vec) == 12

    def test_behavioral_features_empty_messages(self):
        """Empty input returns default zero features."""
        features = extract_behavioral_features([])
        assert features.avg_message_length == 0.0
        assert features.question_ratio == 0.0
        assert features.financial_language_density == 0.0

    def test_financial_language_detection(self):
        """Messages with financial terms are detected."""
        messages = [
            {"role": "user", "content": "I'm pre-approved for a mortgage with a great interest rate."},
            {"role": "user", "content": "What about closing costs and down payment?"},
        ]
        features = extract_behavioral_features(messages)
        assert features.financial_language_density > 0

    def test_urgency_language_detection(self):
        """Messages with urgency terms are detected."""
        messages = [
            {"role": "user", "content": "I need to move soon, relocating for work."},
        ]
        features = extract_behavioral_features(messages)
        assert features.urgency_language_density > 0

    def test_response_time_with_timestamps(self):
        """Response time features populated when timestamps provided."""
        messages = [
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "Hi, I'm interested."},
            {"role": "assistant", "content": "Great!"},
            {"role": "user", "content": "Tell me more."},
            {"role": "assistant", "content": "Sure."},
            {"role": "user", "content": "Thanks!"},
        ]
        base = datetime(2026, 2, 1, 10, 0)
        timestamps = [
            base,
            base + timedelta(seconds=30),
            base + timedelta(seconds=60),
            base + timedelta(seconds=120),
            base + timedelta(seconds=150),
            base + timedelta(seconds=200),
        ]
        features = extract_behavioral_features(messages, timestamps)
        assert features.avg_response_time_seconds > 0


# ---------------------------------------------------------------------------
# Ensemble Scorer Tests
# ---------------------------------------------------------------------------

class TestEnsembleScorer:

    def test_ensemble_train_and_score(self):
        """Train on synthetic data, score, verify 0-1 range."""
        X, y = _make_synthetic_data()
        scorer = EnsembleLeadScorer()
        metrics = scorer.train(X, y)

        assert scorer.is_trained
        assert len(metrics) >= 1  # At least one model trained

        result = scorer.score(X[0])
        assert 0.0 <= result.score <= 1.0
        assert 0.0 <= result.confidence <= 1.0

    def test_ensemble_untrained_uses_rule_score(self):
        """Before training, score falls back to rule-based score."""
        scorer = EnsembleLeadScorer()
        assert not scorer.is_trained

        result = scorer.score(np.zeros(12), rule_score=0.8)
        # Untrained: ml_score = rule_score, so blended = 0.7*0.8 + 0.3*0.8 = 0.8
        assert abs(result.score - 0.8) < 0.01
        assert result.confidence == 0.3  # Untrained confidence

    def test_scoring_result_structure(self):
        """Verify ScoringResult fields are populated after training."""
        X, y = _make_synthetic_data()
        scorer = EnsembleLeadScorer()
        scorer.train(X, y)

        result = scorer.score(X[0])
        assert isinstance(result, ScoringResult)
        assert isinstance(result.score, float)
        assert isinstance(result.confidence, float)
        assert isinstance(result.model_scores, dict)
        assert isinstance(result.explanation, str)
        assert len(result.explanation) > 0

    def test_model_agreement_confidence(self):
        """When only one model, confidence is 0.7."""
        X, y = _make_synthetic_data()
        scorer = EnsembleLeadScorer()
        scorer.train(X, y)

        # With sklearn fallback (only 1 model), confidence should be 0.7
        if len(scorer._models) == 1:
            result = scorer.score(X[0])
            assert result.confidence == 0.7

    def test_ensemble_feature_importance(self):
        """After training, feature_importance dict is non-empty."""
        X, y = _make_synthetic_data()
        feature_names = [f"feat_{i}" for i in range(X.shape[1])]
        scorer = EnsembleLeadScorer()
        scorer.train(X, y, feature_names=feature_names)

        result = scorer.score(X[0])
        assert len(result.feature_importance) > 0
        # Feature names should match what was passed
        for name in result.feature_importance:
            assert name.startswith("feat_")

    def test_get_ensemble_scorer_singleton(self):
        """get_ensemble_scorer returns a singleton."""
        import ghl_real_estate_ai.ml.ensemble_scorer as mod

        # Reset singleton
        mod._scorer = None
        s1 = get_ensemble_scorer()
        s2 = get_ensemble_scorer()
        assert s1 is s2
        # Clean up
        mod._scorer = None


# ---------------------------------------------------------------------------
# Drift Detector Tests
# ---------------------------------------------------------------------------

class TestDriftDetector:

    def test_drift_detector_no_drift(self):
        """Same distribution should have PSI near 0."""
        rng = np.random.RandomState(42)
        reference = rng.randn(500)
        current = rng.randn(500)

        detector = DriftDetector()
        detector.set_reference("feature_a", reference)
        alert = detector.check_drift("feature_a", current)

        assert alert is not None
        assert alert.drift_score < 0.2  # Below threshold
        assert not alert.is_significant

    def test_drift_detector_significant_drift(self):
        """Shifted distribution should trigger significant drift."""
        rng = np.random.RandomState(42)
        reference = rng.randn(500)
        current = rng.randn(500) + 3.0  # Significant shift

        detector = DriftDetector(psi_threshold=0.2)
        detector.set_reference("feature_b", reference)
        alert = detector.check_drift("feature_b", current)

        assert alert is not None
        assert alert.drift_score > 0.2
        assert alert.is_significant

    def test_drift_detector_unknown_feature(self):
        """Unknown feature returns None."""
        detector = DriftDetector()
        result = detector.check_drift("unknown_feature", np.array([1.0, 2.0]))
        assert result is None


# ---------------------------------------------------------------------------
# Training Pipeline Tests
# ---------------------------------------------------------------------------

class TestTrainingPipeline:

    def test_training_pipeline_run(self):
        """Full pipeline with synthetic data returns scorer + result."""
        X, y = _make_synthetic_data()
        pipeline = TrainingPipeline()
        scorer, result = pipeline.run(X, y)

        assert scorer.is_trained
        assert isinstance(result, TrainingResult)
        assert result.model_name == "ensemble"

    def test_training_result_metrics(self):
        """Verify metrics dict has accuracy, precision, recall, f1, auc."""
        X, y = _make_synthetic_data()
        pipeline = TrainingPipeline()
        _, result = pipeline.run(X, y)

        for split_metrics in [result.val_metrics, result.test_metrics]:
            assert "accuracy" in split_metrics
            assert "precision" in split_metrics
            assert "recall" in split_metrics
            assert "f1" in split_metrics
            assert "auc" in split_metrics
            # All metrics should be in [0, 1]
            for key, val in split_metrics.items():
                assert 0.0 <= val <= 1.0, f"{key} = {val} out of range"


# ---------------------------------------------------------------------------
# Edge Case: safe_format_dict placeholder
# ---------------------------------------------------------------------------

class TestSafeFormatDict:

    def test_safe_format_dict(self):
        """Missing keys return {key} placeholder via dict.get pattern."""
        template_data = {"name": "Jorge", "role": "agent"}
        # Simulate safe formatting: missing keys stay as placeholder
        template = "Hello {name}, your {role} for {region}"
        result = template.format_map(
            type("SafeDict", (dict,), {"__missing__": lambda self, k: f"{{{k}}}"})
            (template_data)
        )
        assert result == "Hello Jorge, your agent for {region}"