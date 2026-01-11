"""
Production ML Model Training Script

GREEN PHASE: Train production-grade ML models to make failing tests pass.

This script trains:
1. XGBoost churn prediction model (92%+ precision target)
2. ML-based lead scoring model (95%+ accuracy target)

Uses real behavioral data from LeadBehavioralFeatureExtractor.

Author: TDD ML Model Development Specialist
Created: 2026-01-10
Phase: GREEN (Implementation)
"""

import argparse
import json
import logging
import numpy as np
import pandas as pd
import pickle
import xgboost as xgb
from datetime import datetime
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import (
    precision_score, recall_score, f1_score, accuracy_score,
    classification_report, confusion_matrix, roc_auc_score
)
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from typing import Dict, Tuple, Any
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ghl_real_estate_ai.models.lead_behavioral_features import (
    LeadBehavioralFeatureExtractor
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductionModelTrainer:
    """Production ML model trainer with TDD requirements"""

    def __init__(self, models_dir: Path, data_dir: Path):
        self.models_dir = models_dir
        self.data_dir = data_dir
        self.models_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Models directory: {self.models_dir}")
        logger.info(f"Training data directory: {self.data_dir}")

    def train_churn_prediction_model(
        self,
        target_precision: float = 0.92,
        target_recall: float = 0.88
    ) -> Dict[str, Any]:
        """
        Train XGBoost churn prediction model to achieve 92%+ precision.

        Returns:
            Dictionary with training metrics and model info
        """
        logger.info("=" * 80)
        logger.info("TRAINING CHURN PREDICTION MODEL (XGBoost)")
        logger.info("=" * 80)

        # Load training data
        logger.info("Loading training data...")
        train_df = self._load_training_data("churn")

        # Prepare features and labels
        X, y, feature_names = self._prepare_churn_features(train_df)

        logger.info(f"Training samples: {len(X)}")
        logger.info(f"Positive samples (churned): {y.sum()}")
        logger.info(f"Negative samples (retained): {(1-y).sum()}")
        logger.info(f"Churn rate: {y.mean():.2%}")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Train XGBoost model with hyperparameter tuning
        logger.info("\nTraining XGBoost model...")

        # Initial hyperparameters
        params = {
            'objective': 'binary:logistic',
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 200,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_weight': 3,
            'gamma': 0.1,
            'reg_alpha': 0.1,
            'reg_lambda': 1.0,
            'scale_pos_weight': (1 - y_train.mean()) / y_train.mean(),  # Handle imbalance
            'random_state': 42,
            'eval_metric': ['logloss', 'aucpr']
        }

        # Create DMatrix for XGBoost
        dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=feature_names)
        dtest = xgb.DMatrix(X_test, label=y_test, feature_names=feature_names)

        # Train with early stopping
        evals = [(dtrain, 'train'), (dtest, 'eval')]
        model = xgb.train(
            params,
            dtrain,
            num_boost_round=params['n_estimators'],
            evals=evals,
            early_stopping_rounds=20,
            verbose_eval=25
        )

        # Evaluate model
        logger.info("\nEvaluating model performance...")
        y_pred_proba = model.predict(dtest)
        y_pred = (y_pred_proba >= 0.5).astype(int)

        # Calculate metrics
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        auc_roc = roc_auc_score(y_test, y_pred_proba)

        logger.info(f"\nTest Set Performance:")
        logger.info(f"  Precision: {precision:.4f} (target: {target_precision:.4f})")
        logger.info(f"  Recall:    {recall:.4f} (target: {target_recall:.4f})")
        logger.info(f"  F1 Score:  {f1:.4f}")
        logger.info(f"  AUC-ROC:   {auc_roc:.4f}")

        # Classification report
        logger.info("\nClassification Report:")
        logger.info("\n" + classification_report(y_test, y_pred, target_names=['Retained', 'Churned']))

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        logger.info("\nConfusion Matrix:")
        logger.info(f"  TN: {cm[0,0]:4d}  FP: {cm[0,1]:4d}")
        logger.info(f"  FN: {cm[1,0]:4d}  TP: {cm[1,1]:4d}")

        # Feature importance
        importance_dict = model.get_score(importance_type='gain')
        feature_importance = sorted(
            [(k, v) for k, v in importance_dict.items()],
            key=lambda x: x[1],
            reverse=True
        )

        logger.info("\nTop 10 Most Important Features:")
        for feature, importance in feature_importance[:10]:
            logger.info(f"  {feature:40s}: {importance:.4f}")

        # Check if targets met
        if precision < target_precision:
            logger.warning(f"⚠️  Precision {precision:.4f} below target {target_precision:.4f}")
        else:
            logger.info(f"✅ Precision target met: {precision:.4f} >= {target_precision:.4f}")

        if recall < target_recall:
            logger.warning(f"⚠️  Recall {recall:.4f} below target {target_recall:.4f}")
        else:
            logger.info(f"✅ Recall target met: {recall:.4f} >= {target_recall:.4f}")

        # Save model
        model_version = "v2.1.0"
        model_file = self.models_dir / f"churn_model_{model_version}.xgb"
        model.save_model(str(model_file))
        logger.info(f"\n✅ Model saved to: {model_file}")

        # Save metadata
        metadata = {
            'model_type': 'xgboost_churn_prediction',
            'model_version': model_version,
            'training_date': datetime.now().isoformat(),
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'auc_roc': float(auc_roc),
            'churn_rate': float(y.mean()),
            'feature_count': len(feature_names),
            'feature_names': feature_names,
            'feature_importance': {k: float(v) for k, v in feature_importance},
            'hyperparameters': params,
            'data_source': 'LeadBehavioralFeatureExtractor',
            'feature_extractor': 'LeadBehavioralFeatureExtractor',
            'meets_precision_target': precision >= target_precision,
            'meets_recall_target': recall >= target_recall
        }

        metadata_file = self.models_dir / f"churn_model_{model_version}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"✅ Metadata saved to: {metadata_file}")

        return metadata

    def train_lead_scoring_model(
        self,
        target_accuracy: float = 0.95
    ) -> Dict[str, Any]:
        """
        Train ML-based lead scoring model to achieve 95%+ accuracy.

        Returns:
            Dictionary with training metrics and model info
        """
        logger.info("=" * 80)
        logger.info("TRAINING LEAD SCORING MODEL (Gradient Boosting)")
        logger.info("=" * 80)

        # Load training data
        logger.info("Loading training data...")
        train_df = self._load_training_data("lead_scoring")

        # Prepare features and labels
        X, y, feature_names = self._prepare_lead_scoring_features(train_df)

        logger.info(f"Training samples: {len(X)}")
        logger.info(f"Class distribution:")
        for class_name, count in zip(['cold', 'warm', 'hot'], np.bincount(y)):
            logger.info(f"  {class_name}: {count} ({count/len(y):.2%})")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Train Gradient Boosting model
        logger.info("\nTraining Gradient Boosting model...")

        # Hyperparameter tuning with GridSearch
        param_grid = {
            'n_estimators': [100, 200],
            'max_depth': [5, 7],
            'learning_rate': [0.05, 0.1],
            'subsample': [0.8, 1.0],
            'min_samples_split': [10, 20]
        }

        base_model = GradientBoostingClassifier(random_state=42)
        grid_search = GridSearchCV(
            base_model,
            param_grid,
            cv=5,
            scoring='accuracy',
            n_jobs=-1,
            verbose=1
        )

        grid_search.fit(X_train, y_train)

        logger.info(f"\nBest hyperparameters: {grid_search.best_params_}")
        logger.info(f"Best CV accuracy: {grid_search.best_score_:.4f}")

        # Get best model
        model = grid_search.best_estimator_

        # Evaluate on test set
        logger.info("\nEvaluating model performance...")
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)

        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)

        logger.info(f"\nTest Set Performance:")
        logger.info(f"  Accuracy: {accuracy:.4f} (target: {target_accuracy:.4f})")

        # Classification report
        logger.info("\nClassification Report:")
        logger.info("\n" + classification_report(
            y_test, y_pred,
            target_names=['cold', 'warm', 'hot']
        ))

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        logger.info("\nConfusion Matrix:")
        logger.info("          Predicted")
        logger.info("          Cold  Warm  Hot")
        logger.info(f"Actual Cold {cm[0,0]:4d}  {cm[0,1]:4d}  {cm[0,2]:4d}")
        logger.info(f"       Warm {cm[1,0]:4d}  {cm[1,1]:4d}  {cm[1,2]:4d}")
        logger.info(f"       Hot  {cm[2,0]:4d}  {cm[2,1]:4d}  {cm[2,2]:4d}")

        # Feature importance
        feature_importance = sorted(
            zip(feature_names, model.feature_importances_),
            key=lambda x: x[1],
            reverse=True
        )

        logger.info("\nTop 10 Most Important Features:")
        for feature, importance in feature_importance[:10]:
            logger.info(f"  {feature:40s}: {importance:.4f}")

        # Check if target met
        if accuracy < target_accuracy:
            logger.warning(f"⚠️  Accuracy {accuracy:.4f} below target {target_accuracy:.4f}")
        else:
            logger.info(f"✅ Accuracy target met: {accuracy:.4f} >= {target_accuracy:.4f}")

        # Save model
        model_version = "v1.0.0"
        model_file = self.models_dir / f"lead_scoring_model_{model_version}.pkl"

        with open(model_file, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"\n✅ Model saved to: {model_file}")

        # Save scaler if used
        # Note: This implementation doesn't use scaling, but can be added

        # Save metadata
        metadata = {
            'model_type': 'gradient_boosting_lead_scoring',
            'model_version': model_version,
            'training_date': datetime.now().isoformat(),
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'accuracy': float(accuracy),
            'cv_accuracy': float(grid_search.best_score_),
            'feature_count': len(feature_names),
            'feature_names': feature_names,
            'feature_importance': {k: float(v) for k, v in feature_importance},
            'hyperparameters': grid_search.best_params_,
            'classes': ['cold', 'warm', 'hot'],
            'data_source': 'real_lead_conversations',
            'meets_accuracy_target': accuracy >= target_accuracy
        }

        metadata_file = self.models_dir / f"lead_scoring_model_{model_version}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"✅ Metadata saved to: {metadata_file}")

        return metadata

    def _load_training_data(self, dataset_type: str) -> pd.DataFrame:
        """Load training dataset"""
        if dataset_type == "churn":
            data_file = self.data_dir / "churn_training_set.csv"
        elif dataset_type == "lead_scoring":
            data_file = self.data_dir / "lead_scoring_training_set.csv"
        else:
            raise ValueError(f"Unknown dataset type: {dataset_type}")

        if not data_file.exists():
            raise FileNotFoundError(
                f"Training data not found: {data_file}\n"
                f"Run generate_training_data.py first to create training datasets."
            )

        df = pd.read_csv(data_file)
        logger.info(f"Loaded {len(df)} samples from {data_file}")

        return df

    def _prepare_churn_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, list]:
        """
        Prepare features for churn prediction model.

        Returns:
            (X, y, feature_names)
        """
        # Feature columns based on LeadBehavioralFeatures
        feature_cols = [
            'days_since_last_activity',
            'interaction_velocity_7d',
            'interaction_velocity_14d',
            'interaction_velocity_30d',
            'email_response_rate',
            'sms_response_rate',
            'avg_response_time_minutes',
            'urgency_score',
            'intent_strength',
            'property_views',
            'search_queries',
            'days_since_creation',
            'total_interactions',
            'unique_interaction_days',
            'feature_completeness',
            'data_freshness_hours'
        ]

        X = df[feature_cols].values
        y = df['churned'].values

        return X, y, feature_cols

    def _prepare_lead_scoring_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, list]:
        """
        Prepare features for lead scoring model.

        Returns:
            (X, y, feature_names)
        """
        # Feature columns for lead scoring
        feature_cols = [
            'budget_provided',
            'location_specified',
            'timeline_confirmed',
            'property_requirements',
            'financing_status',
            'motivation_shared',
            'engagement_score',
            'response_rate',
            'property_views',
            'days_active',
            'interaction_frequency'
        ]

        X = df[feature_cols].values

        # Convert classification to numeric
        class_map = {'cold': 0, 'warm': 1, 'hot': 2}
        y = df['actual_classification'].map(class_map).values

        return X, y, feature_cols


def main():
    """Main training script"""
    parser = argparse.ArgumentParser(description='Train production ML models')
    parser.add_argument(
        '--models-dir',
        type=Path,
        default=Path(__file__).parent.parent / 'models' / 'trained',
        help='Directory to save trained models'
    )
    parser.add_argument(
        '--data-dir',
        type=Path,
        default=Path(__file__).parent.parent / 'tests' / 'fixtures' / 'training_data',
        help='Directory containing training data'
    )
    parser.add_argument(
        '--model',
        choices=['churn', 'lead_scoring', 'all'],
        default='all',
        help='Which model(s) to train'
    )
    parser.add_argument(
        '--churn-precision-target',
        type=float,
        default=0.92,
        help='Target precision for churn model'
    )
    parser.add_argument(
        '--lead-accuracy-target',
        type=float,
        default=0.95,
        help='Target accuracy for lead scoring model'
    )

    args = parser.parse_args()

    # Create trainer
    trainer = ProductionModelTrainer(args.models_dir, args.data_dir)

    # Train models
    results = {}

    if args.model in ['churn', 'all']:
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 1: CHURN PREDICTION MODEL TRAINING")
        logger.info("=" * 80 + "\n")

        churn_results = trainer.train_churn_prediction_model(
            target_precision=args.churn_precision_target
        )
        results['churn'] = churn_results

    if args.model in ['lead_scoring', 'all']:
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2: LEAD SCORING MODEL TRAINING")
        logger.info("=" * 80 + "\n")

        lead_results = trainer.train_lead_scoring_model(
            target_accuracy=args.lead_accuracy_target
        )
        results['lead_scoring'] = lead_results

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TRAINING SUMMARY")
    logger.info("=" * 80)

    for model_name, metrics in results.items():
        logger.info(f"\n{model_name.upper()} Model:")
        logger.info(f"  Version: {metrics['model_version']}")
        logger.info(f"  Training samples: {metrics['training_samples']}")

        if model_name == 'churn':
            logger.info(f"  Precision: {metrics['precision']:.4f} (target: 0.92)")
            logger.info(f"  Recall: {metrics['recall']:.4f}")
            logger.info(f"  Target met: {'✅ YES' if metrics['meets_precision_target'] else '❌ NO'}")
        else:
            logger.info(f"  Accuracy: {metrics['accuracy']:.4f} (target: 0.95)")
            logger.info(f"  Target met: {'✅ YES' if metrics['meets_accuracy_target'] else '❌ NO'}")

    logger.info("\n" + "=" * 80)
    logger.info("✅ TRAINING COMPLETE - Run pytest to verify models")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
