"""Ensemble lead scorer combining XGBoost + LightGBM with rule-based blending."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Optional imports
try:
    from xgboost import XGBClassifier

    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    from lightgbm import LGBMClassifier

    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

try:
    from sklearn.ensemble import GradientBoostingClassifier

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


@dataclass
class ScoringResult:
    """Result from the ensemble scorer."""

    score: float  # 0.0 - 1.0 probability
    confidence: float  # Model confidence
    model_scores: Dict[str, float] = field(default_factory=dict)
    feature_importance: Dict[str, float] = field(default_factory=dict)
    explanation: str = ""


class EnsembleLeadScorer:
    """Ensemble scorer combining multiple ML models with rule-based blending.

    Uses XGBoost + LightGBM when available, falls back to sklearn GBM,
    and blends with a rule-based score.
    """

    def __init__(
        self,
        rule_weight: float = 0.3,
        ml_weight: float = 0.7,
    ):
        self._rule_weight = rule_weight
        self._ml_weight = ml_weight
        self._models: Dict[str, Any] = {}
        self._is_trained = False
        self._feature_names: List[str] = []

    @property
    def is_trained(self) -> bool:
        return self._is_trained

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """Train the ensemble on labeled data.

        Args:
            X: Feature matrix (n_samples, n_features)
            y: Binary labels (0/1)
            feature_names: Optional feature names

        Returns:
            Dict of model_name -> training accuracy
        """
        self._feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        metrics = {}

        if XGBOOST_AVAILABLE:
            xgb = XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                use_label_encoder=False,
                eval_metric="logloss",
                verbosity=0,
            )
            xgb.fit(X, y)
            self._models["xgboost"] = xgb
            metrics["xgboost"] = float(xgb.score(X, y))

        if LIGHTGBM_AVAILABLE:
            lgbm = LGBMClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                verbosity=-1,
            )
            lgbm.fit(X, y)
            self._models["lightgbm"] = lgbm
            metrics["lightgbm"] = float(lgbm.score(X, y))

        if not self._models and SKLEARN_AVAILABLE:
            # Fallback to sklearn
            gbm = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
            )
            gbm.fit(X, y)
            self._models["sklearn_gbm"] = gbm
            metrics["sklearn_gbm"] = float(gbm.score(X, y))

        self._is_trained = bool(self._models)
        logger.info("Trained ensemble with models: %s", list(self._models.keys()))
        return metrics

    def score(
        self,
        features: np.ndarray,
        rule_score: float = 0.5,
    ) -> ScoringResult:
        """Score a lead using the ensemble.

        Args:
            features: Feature vector (1, n_features) or (n_features,)
            rule_score: Rule-based score to blend with (0.0-1.0)

        Returns:
            ScoringResult with blended score.
        """
        if features.ndim == 1:
            features = features.reshape(1, -1)

        model_scores = {}

        if self._is_trained:
            for name, model in self._models.items():
                try:
                    proba = model.predict_proba(features)[0]
                    # proba is [p_class_0, p_class_1]
                    model_scores[name] = float(proba[1]) if len(proba) > 1 else float(proba[0])
                except Exception as e:
                    logger.warning("Model %s prediction failed: %s", name, e)

            if model_scores:
                ml_score = sum(model_scores.values()) / len(model_scores)
            else:
                ml_score = rule_score
        else:
            ml_score = rule_score

        # Blend ML and rule-based scores
        blended = (self._ml_weight * ml_score) + (self._rule_weight * rule_score)
        blended = max(0.0, min(1.0, blended))

        # Feature importance (from first available model)
        importance = {}
        if self._is_trained and self._feature_names:
            for name, model in self._models.items():
                if hasattr(model, "feature_importances_"):
                    imp = model.feature_importances_
                    importance = {
                        self._feature_names[i]: float(imp[i]) for i in range(min(len(imp), len(self._feature_names)))
                    }
                    break

        # Confidence based on model agreement
        if len(model_scores) >= 2:
            scores_list = list(model_scores.values())
            variance = np.var(scores_list)
            confidence = max(0.0, 1.0 - variance * 4)  # Higher variance = lower confidence
        else:
            confidence = 0.7 if self._is_trained else 0.3

        explanation = self._generate_explanation(blended, model_scores, importance)

        return ScoringResult(
            score=round(blended, 4),
            confidence=round(float(confidence), 4),
            model_scores=model_scores,
            feature_importance=importance,
            explanation=explanation,
        )

    def _generate_explanation(
        self,
        score: float,
        model_scores: Dict[str, float],
        importance: Dict[str, float],
    ) -> str:
        """Generate human-readable explanation."""
        parts = []
        if score >= 0.8:
            parts.append("High conversion probability")
        elif score >= 0.5:
            parts.append("Moderate conversion probability")
        else:
            parts.append("Lower conversion probability")

        if importance:
            top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:3]
            feature_strs = [f"{name}" for name, _ in top_features]
            parts.append(f"Top signals: {', '.join(feature_strs)}")

        return ". ".join(parts) + "."


@dataclass
class DriftAlert:
    """Alert when feature or prediction drift is detected."""

    feature_name: str
    drift_type: str  # "psi" or "ks"
    drift_score: float
    threshold: float
    is_significant: bool


class DriftDetector:
    """Detects feature and prediction drift using PSI and KS tests."""

    def __init__(self, psi_threshold: float = 0.2, ks_threshold: float = 0.05):
        self._psi_threshold = psi_threshold
        self._ks_threshold = ks_threshold
        self._reference_distributions: Dict[str, np.ndarray] = {}

    def set_reference(self, feature_name: str, values: np.ndarray) -> None:
        """Set reference distribution for a feature."""
        self._reference_distributions[feature_name] = values.copy()

    def check_drift(self, feature_name: str, current_values: np.ndarray) -> Optional[DriftAlert]:
        """Check if current values have drifted from reference.

        Uses Population Stability Index (PSI).
        """
        if feature_name not in self._reference_distributions:
            return None

        reference = self._reference_distributions[feature_name]
        psi = self._calculate_psi(reference, current_values)

        return DriftAlert(
            feature_name=feature_name,
            drift_type="psi",
            drift_score=round(float(psi), 4),
            threshold=self._psi_threshold,
            is_significant=psi > self._psi_threshold,
        )

    @staticmethod
    def _calculate_psi(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
        """Calculate Population Stability Index."""
        # Create bins from reference
        min_val = min(reference.min(), current.min())
        max_val = max(reference.max(), current.max())
        bin_edges = np.linspace(min_val, max_val, bins + 1)

        ref_hist, _ = np.histogram(reference, bins=bin_edges)
        cur_hist, _ = np.histogram(current, bins=bin_edges)

        # Normalize to proportions, add small epsilon to avoid division by zero
        eps = 1e-6
        ref_pct = (ref_hist + eps) / (ref_hist.sum() + eps * bins)
        cur_pct = (cur_hist + eps) / (cur_hist.sum() + eps * bins)

        psi = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
        return float(psi)


# Singleton
_scorer: Optional[EnsembleLeadScorer] = None


def get_ensemble_scorer() -> EnsembleLeadScorer:
    global _scorer
    if _scorer is None:
        _scorer = EnsembleLeadScorer()
    return _scorer
