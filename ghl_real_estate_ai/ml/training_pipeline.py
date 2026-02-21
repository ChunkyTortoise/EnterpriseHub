"""Full ML training pipeline for lead scoring."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

try:
    from sklearn.metrics import (
        accuracy_score,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
    )
    from sklearn.model_selection import cross_val_score, train_test_split

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


@dataclass
class TrainingResult:
    """Result of a training pipeline run."""

    model_name: str
    train_metrics: Dict[str, float]
    val_metrics: Dict[str, float]
    test_metrics: Dict[str, float]
    feature_importance: Dict[str, float]
    cross_val_scores: List[float]


class TrainingPipeline:
    """End-to-end training pipeline for the ensemble lead scorer."""

    def __init__(
        self,
        test_size: float = 0.2,
        val_size: float = 0.15,
        random_state: int = 42,
    ):
        self._test_size = test_size
        self._val_size = val_size
        self._random_state = random_state

    def run(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: Optional[List[str]] = None,
    ) -> Tuple["EnsembleLeadScorer", "TrainingResult"]:
        """Run the full training pipeline.

        Args:
            X: Feature matrix
            y: Binary labels
            feature_names: Feature names

        Returns:
            Trained EnsembleLeadScorer and TrainingResult
        """
        from ghl_real_estate_ai.ml.ensemble_scorer import EnsembleLeadScorer

        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for the training pipeline")

        # Split data
        X_temp, X_test, y_temp, y_test = train_test_split(
            X,
            y,
            test_size=self._test_size,
            random_state=self._random_state,
            stratify=y,
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp,
            y_temp,
            test_size=self._val_size,
            random_state=self._random_state,
            stratify=y_temp,
        )

        # Train ensemble
        scorer = EnsembleLeadScorer()
        train_metrics = scorer.train(X_train, y_train, feature_names)

        # Evaluate on each split
        val_metrics = self._evaluate(scorer, X_val, y_val)
        test_metrics = self._evaluate(scorer, X_test, y_test)

        # Cross-validation on full training set
        cv_scores = self._cross_validate(X_temp, y_temp)

        # Feature importance
        importance = {}
        if scorer.is_trained:
            result = scorer.score(X_test[0])
            importance = result.feature_importance

        training_result = TrainingResult(
            model_name="ensemble",
            train_metrics=train_metrics,
            val_metrics=val_metrics,
            test_metrics=test_metrics,
            feature_importance=importance,
            cross_val_scores=cv_scores,
        )

        logger.info(
            "Training complete. Val AUC: %.3f, Test AUC: %.3f",
            val_metrics.get("auc", 0),
            test_metrics.get("auc", 0),
        )

        return scorer, training_result

    def _evaluate(
        self,
        scorer: "EnsembleLeadScorer",
        X: np.ndarray,
        y: np.ndarray,
    ) -> Dict[str, float]:
        """Evaluate scorer on a dataset."""
        predictions = []
        scores = []
        for i in range(X.shape[0]):
            result = scorer.score(X[i])
            scores.append(result.score)
            predictions.append(1 if result.score >= 0.5 else 0)

        predictions_arr = np.array(predictions)
        scores_arr = np.array(scores)

        metrics = {
            "accuracy": float(accuracy_score(y, predictions_arr)),
            "precision": float(precision_score(y, predictions_arr, zero_division=0)),
            "recall": float(recall_score(y, predictions_arr, zero_division=0)),
            "f1": float(f1_score(y, predictions_arr, zero_division=0)),
        }

        try:
            metrics["auc"] = float(roc_auc_score(y, scores_arr))
        except ValueError:
            metrics["auc"] = 0.0

        return metrics

    def _cross_validate(
        self,
        X: np.ndarray,
        y: np.ndarray,
        cv: int = 5,
    ) -> List[float]:
        """Run cross-validation using sklearn GBM as proxy."""
        try:
            from sklearn.ensemble import GradientBoostingClassifier

            model = GradientBoostingClassifier(n_estimators=50, max_depth=3, random_state=self._random_state)
            scores = cross_val_score(model, X, y, cv=min(cv, len(y) // 2), scoring="roc_auc")
            return [float(s) for s in scores]
        except Exception:
            return []
