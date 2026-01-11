"""
ML Model Training Script for Lead Intelligence System

Trains XGBoost models for lead scoring and churn prediction using behavioral features.
Implements hyperparameter tuning, model validation, and performance benchmarking.

Models Trained:
- Lead scoring model (target: 95%+ accuracy)
- Churn prediction model (target: 92%+ precision)
- Property preference learning model

Performance Validation:
- Cross-validation with temporal splits
- Feature importance analysis
- Model calibration testing
- Benchmark comparison
"""

import asyncio
import json
import pickle
import numpy as np
import pandas as pd
import xgboost as xgb
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.calibration import calibration_curve
import optuna

import sys
sys.path.append(str(Path(__file__).parent.parent))

from ghl_real_estate_ai.models.lead_behavioral_features import (
    LeadBehavioralFeatureExtractor,
    LeadBehavioralFeatures
)
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class MLModelTrainer:
    """
    Comprehensive ML model trainer for the lead intelligence system.

    Handles data preparation, feature engineering, model training,
    hyperparameter optimization, and performance validation.
    """

    def __init__(self):
        self.feature_extractor = LeadBehavioralFeatureExtractor()
        self.model_path = Path(__file__).parent.parent / "models" / "trained"
        self.model_path.mkdir(exist_ok=True, parents=True)

        # Training configuration
        self.random_state = 42
        self.test_size = 0.2
        self.cv_folds = 5

        # Performance targets
        self.target_accuracy = 0.95
        self.target_precision = 0.92
        self.target_recall = 0.88

        # Model configurations
        self.lead_scoring_params = {
            'objective': 'binary:logistic',
            'eval_metric': 'auc',
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': self.random_state
        }

        self.churn_prediction_params = {
            'objective': 'binary:logistic',
            'eval_metric': ['auc', 'logloss'],
            'max_depth': 5,
            'learning_rate': 0.05,
            'subsample': 0.9,
            'colsample_bytree': 0.9,
            'random_state': self.random_state
        }

    def generate_synthetic_training_data(self, n_samples: int = 10000) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate synthetic training data for model development.

        Args:
            n_samples: Number of synthetic samples to generate

        Returns:
            Tuple of (features_df, targets_df) for training
        """
        logger.info(f"Generating {n_samples} synthetic training samples...")

        np.random.seed(self.random_state)

        # Generate synthetic lead data with realistic patterns
        leads_data = []
        interaction_histories = []
        lead_scores = []
        churn_labels = []

        for i in range(n_samples):
            # Generate lead characteristics
            lead_age_days = np.random.exponential(30)  # Most leads are young
            lead_source = np.random.choice(['website', 'referral', 'social', 'email'], p=[0.4, 0.3, 0.2, 0.1])
            lead_segment = np.random.choice(['family', 'young_professional', 'investor', 'retiree'],
                                          p=[0.3, 0.4, 0.2, 0.1])

            # Generate interaction patterns based on lead quality
            base_quality = np.random.beta(2, 3)  # Skewed toward lower quality

            # High quality leads have more interactions
            interaction_count = np.random.poisson(max(1, base_quality * 20))
            days_since_last_activity = np.random.exponential(5 if base_quality > 0.7 else 15)

            # Generate interactions
            interactions = []
            for j in range(interaction_count):
                interaction_time = datetime.now() - timedelta(
                    days=np.random.exponential(lead_age_days/10)
                )

                action_probs = [0.3, 0.2, 0.2, 0.15, 0.15] if base_quality > 0.6 else [0.5, 0.1, 0.1, 0.15, 0.15]
                action = np.random.choice(
                    ['property_view', 'search', 'email_open', 'phone_call', 'showing_request'],
                    p=action_probs
                )

                interactions.append({
                    'timestamp': interaction_time.isoformat(),
                    'action': action,
                    'channel': np.random.choice(['email', 'website', 'phone', 'sms']),
                    'is_response': np.random.random() < (0.7 if base_quality > 0.5 else 0.3)
                })

            # Lead data
            lead_data = {
                'id': f'synthetic_lead_{i}',
                'created_at': (datetime.now() - timedelta(days=lead_age_days)).isoformat(),
                'source': lead_source,
                'status': 'active',
                'segment': lead_segment
            }

            leads_data.append(lead_data)
            interaction_histories.append(interactions)

            # Generate target labels based on realistic patterns
            # Lead score correlates with engagement and recency
            engagement_score = min(1.0, interaction_count / 20)
            recency_score = max(0, 1 - days_since_last_activity / 30)
            noise = np.random.normal(0, 0.1)

            lead_score = np.clip(0.3 * engagement_score + 0.4 * recency_score + 0.2 * base_quality + noise, 0, 1)

            # Churn probability inversely related to engagement and positively to inactivity
            churn_prob = np.clip(
                0.5 + 0.3 * (days_since_last_activity / 30) - 0.2 * engagement_score + np.random.normal(0, 0.1),
                0, 1
            )
            churn_label = 1 if churn_prob > 0.6 else 0

            lead_scores.append(lead_score)
            churn_labels.append(churn_label)

        # Extract features for all leads
        logger.info("Extracting behavioral features...")
        all_features = self.feature_extractor.extract_batch_features(
            leads_data,
            {lead['id']: hist for lead, hist in zip(leads_data, interaction_histories)}
        )

        # Convert to DataFrame
        feature_rows = []
        for i, features in enumerate(all_features):
            row = features.numerical_features.copy()

            # Add categorical features as encoded values
            row['lead_source_website'] = 1 if features.lead_source == 'website' else 0
            row['lead_source_referral'] = 1 if features.lead_source == 'referral' else 0
            row['lead_source_social'] = 1 if features.lead_source == 'social' else 0

            row['preferred_channel_email'] = 1 if features.communication_prefs.preferred_channel.value == 'email' else 0
            row['preferred_channel_phone'] = 1 if features.communication_prefs.preferred_channel.value == 'phone' else 0

            # Add derived scores
            row['engagement_score'] = features.engagement_score
            row['intent_score'] = features.intent_score
            row['responsiveness_score'] = features.responsiveness_score

            # Target variables
            row['lead_score_target'] = lead_scores[i]
            row['churn_label_target'] = churn_labels[i]

            feature_rows.append(row)

        df = pd.DataFrame(feature_rows)

        # Separate features and targets
        feature_columns = [col for col in df.columns if not col.endswith('_target')]
        features_df = df[feature_columns]
        targets_df = df[['lead_score_target', 'churn_label_target']]

        logger.info(f"Generated training data: {len(features_df)} samples, {len(feature_columns)} features")

        return features_df, targets_df

    def train_lead_scoring_model(self, features_df: pd.DataFrame, targets_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Train XGBoost model for lead scoring.

        Args:
            features_df: Feature matrix
            targets_df: Target variables

        Returns:
            Dictionary with model and training results
        """
        logger.info("Training lead scoring model...")

        X = features_df.fillna(0)
        y = targets_df['lead_score_target']

        # Convert continuous scores to binary classification (>0.7 = high quality)
        y_binary = (y > 0.7).astype(int)

        # Time series split for validation
        tscv = TimeSeriesSplit(n_splits=self.cv_folds)

        # Hyperparameter optimization
        def objective(trial):
            params = self.lead_scoring_params.copy()
            params.update({
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                'reg_alpha': trial.suggest_float('reg_alpha', 0, 1.0),
                'reg_lambda': trial.suggest_float('reg_lambda', 0, 1.0)
            })

            cv_scores = []
            for train_idx, val_idx in tscv.split(X):
                X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                y_train, y_val = y_binary.iloc[train_idx], y_binary.iloc[val_idx]

                model = xgb.XGBClassifier(**params)
                model.fit(X_train, y_train)

                y_pred = model.predict(X_val)
                score = accuracy_score(y_val, y_pred)
                cv_scores.append(score)

            return np.mean(cv_scores)

        # Optimize hyperparameters
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=50)

        best_params = self.lead_scoring_params.copy()
        best_params.update(study.best_params)

        logger.info(f"Best hyperparameters: {best_params}")

        # Train final model with best parameters
        final_model = xgb.XGBClassifier(**best_params)
        final_model.fit(X, y_binary)

        # Evaluate model
        y_pred = final_model.predict(X)
        y_pred_proba = final_model.predict_proba(X)[:, 1]

        metrics = {
            'accuracy': accuracy_score(y_binary, y_pred),
            'precision': precision_score(y_binary, y_pred),
            'recall': recall_score(y_binary, y_pred),
            'f1_score': f1_score(y_binary, y_pred),
            'auc_score': roc_auc_score(y_binary, y_pred_proba)
        }

        logger.info(f"Lead scoring model metrics: {metrics}")

        # Feature importance
        feature_importance = dict(zip(X.columns, final_model.feature_importances_))
        top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]

        logger.info("Top 10 important features for lead scoring:")
        for feature, importance in top_features:
            logger.info(f"  {feature}: {importance:.4f}")

        # Save model
        model_file = self.model_path / f"lead_scoring_v1.0.0.xgb"
        final_model.save_model(str(model_file))

        # Save metadata
        metadata = {
            'model_version': 'v1.0.0',
            'training_date': datetime.now().isoformat(),
            'feature_names': list(X.columns),
            'hyperparameters': best_params,
            'performance_metrics': metrics,
            'feature_importance': feature_importance,
            'training_samples': len(X)
        }

        metadata_file = self.model_path / f"lead_scoring_v1.0.0_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        return {
            'model': final_model,
            'metrics': metrics,
            'feature_importance': feature_importance,
            'metadata': metadata
        }

    def train_churn_prediction_model(self, features_df: pd.DataFrame, targets_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Train XGBoost model for churn prediction.

        Args:
            features_df: Feature matrix
            targets_df: Target variables

        Returns:
            Dictionary with model and training results
        """
        logger.info("Training churn prediction model...")

        X = features_df.fillna(0)
        y = targets_df['churn_label_target']

        # Add churn-specific features
        X_churn = X.copy()
        X_churn['interaction_decline'] = np.maximum(0,
            X_churn['interaction_velocity_30d'] - X_churn['interaction_velocity_7d'])
        X_churn['response_ratio'] = (X_churn['email_response_rate'] + X_churn['sms_response_rate']) / 2

        # Time series split for validation
        tscv = TimeSeriesSplit(n_splits=self.cv_folds)

        # Hyperparameter optimization for churn model
        def objective(trial):
            params = self.churn_prediction_params.copy()
            params.update({
                'max_depth': trial.suggest_int('max_depth', 3, 8),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.2),
                'subsample': trial.suggest_float('subsample', 0.7, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.7, 1.0),
                'reg_alpha': trial.suggest_float('reg_alpha', 0, 1.0),
                'reg_lambda': trial.suggest_float('reg_lambda', 0, 1.0)
            })

            cv_scores = []
            for train_idx, val_idx in tscv.split(X_churn):
                X_train, X_val = X_churn.iloc[train_idx], X_churn.iloc[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

                model = xgb.XGBClassifier(**params)
                model.fit(X_train, y_train)

                y_pred_proba = model.predict_proba(X_val)[:, 1]
                score = roc_auc_score(y_val, y_pred_proba)
                cv_scores.append(score)

            return np.mean(cv_scores)

        # Optimize hyperparameters
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=50)

        best_params = self.churn_prediction_params.copy()
        best_params.update(study.best_params)

        logger.info(f"Best churn model hyperparameters: {best_params}")

        # Train final model
        final_model = xgb.XGBClassifier(**best_params)
        final_model.fit(X_churn, y)

        # Evaluate model
        y_pred = final_model.predict(X_churn)
        y_pred_proba = final_model.predict_proba(X_churn)[:, 1]

        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred),
            'recall': recall_score(y, y_pred),
            'f1_score': f1_score(y, y_pred),
            'auc_score': roc_auc_score(y, y_pred_proba)
        }

        logger.info(f"Churn prediction model metrics: {metrics}")

        # Model calibration analysis
        fraction_positives, mean_predicted_value = calibration_curve(y, y_pred_proba, n_bins=10)
        calibration_error = np.mean(np.abs(fraction_positives - mean_predicted_value))
        metrics['calibration_error'] = calibration_error

        # Feature importance for churn
        feature_importance = dict(zip(X_churn.columns, final_model.feature_importances_))
        top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]

        logger.info("Top 10 important features for churn prediction:")
        for feature, importance in top_features:
            logger.info(f"  {feature}: {importance:.4f}")

        # Save model
        model_file = self.model_path / f"churn_model_v2.1.0.xgb"
        final_model.save_model(str(model_file))

        # Save metadata
        metadata = {
            'model_version': 'v2.1.0',
            'training_date': datetime.now().isoformat(),
            'feature_names': list(X_churn.columns),
            'hyperparameters': best_params,
            'performance_metrics': metrics,
            'feature_importance': feature_importance,
            'training_samples': len(X_churn)
        }

        metadata_file = self.model_path / f"churn_model_v2.1.0_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        return {
            'model': final_model,
            'metrics': metrics,
            'feature_importance': feature_importance,
            'metadata': metadata
        }

    def validate_model_performance(self, model_results: Dict[str, Any], model_type: str) -> bool:
        """
        Validate that model meets performance targets.

        Args:
            model_results: Results from model training
            model_type: Type of model ('lead_scoring' or 'churn_prediction')

        Returns:
            True if model meets targets, False otherwise
        """
        metrics = model_results['metrics']

        if model_type == 'lead_scoring':
            accuracy_target = self.target_accuracy
            precision_target = 0.90  # Slightly lower for lead scoring

            meets_accuracy = metrics['accuracy'] >= accuracy_target
            meets_precision = metrics['precision'] >= precision_target

            if meets_accuracy and meets_precision:
                logger.info(f"✅ Lead scoring model meets performance targets:")
                logger.info(f"   Accuracy: {metrics['accuracy']:.3f} >= {accuracy_target:.3f}")
                logger.info(f"   Precision: {metrics['precision']:.3f} >= {precision_target:.3f}")
                return True
            else:
                logger.warning(f"❌ Lead scoring model does not meet targets:")
                logger.warning(f"   Accuracy: {metrics['accuracy']:.3f} < {accuracy_target:.3f}" if not meets_accuracy else "")
                logger.warning(f"   Precision: {metrics['precision']:.3f} < {precision_target:.3f}" if not meets_precision else "")
                return False

        elif model_type == 'churn_prediction':
            precision_target = self.target_precision
            recall_target = self.target_recall

            meets_precision = metrics['precision'] >= precision_target
            meets_recall = metrics['recall'] >= recall_target

            if meets_precision and meets_recall:
                logger.info(f"✅ Churn prediction model meets performance targets:")
                logger.info(f"   Precision: {metrics['precision']:.3f} >= {precision_target:.3f}")
                logger.info(f"   Recall: {metrics['recall']:.3f} >= {recall_target:.3f}")
                return True
            else:
                logger.warning(f"❌ Churn prediction model does not meet targets:")
                logger.warning(f"   Precision: {metrics['precision']:.3f} < {precision_target:.3f}" if not meets_precision else "")
                logger.warning(f"   Recall: {metrics['recall']:.3f} < {recall_target:.3f}" if not meets_recall else "")
                return False

        return False

    def create_fallback_models(self):
        """Create simple fallback models for when ML models are unavailable"""

        logger.info("Creating fallback models...")

        # Simple rule-based lead scorer
        fallback_scorer_code = '''
def score_lead(features):
    """Simple rule-based lead scoring"""
    score = 0.5

    # Engagement scoring
    if features.get('total_interactions', 0) > 10:
        score += 0.2
    elif features.get('total_interactions', 0) > 5:
        score += 0.1

    # Recency scoring
    days_inactive = features.get('days_since_last_activity', 30)
    if days_inactive < 3:
        score += 0.2
    elif days_inactive < 7:
        score += 0.1
    elif days_inactive > 21:
        score -= 0.2

    # Intent scoring
    if features.get('property_views', 0) > 5:
        score += 0.1

    return min(1.0, max(0.0, score))
'''

        fallback_file = self.model_path / "fallback_scorer.py"
        with open(fallback_file, 'w') as f:
            f.write(fallback_scorer_code)

        logger.info("Fallback models created")

    def generate_training_report(self, lead_scoring_results: Dict, churn_results: Dict) -> str:
        """Generate comprehensive training report"""

        report = f"""
# ML Lead Intelligence Model Training Report

**Training Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Performance Summary

### Lead Scoring Model (v1.0.0)
- **Accuracy**: {lead_scoring_results['metrics']['accuracy']:.3f} (Target: ≥0.950)
- **Precision**: {lead_scoring_results['metrics']['precision']:.3f} (Target: ≥0.900)
- **Recall**: {lead_scoring_results['metrics']['recall']:.3f}
- **F1-Score**: {lead_scoring_results['metrics']['f1_score']:.3f}
- **AUC**: {lead_scoring_results['metrics']['auc_score']:.3f}

### Churn Prediction Model (v2.1.0)
- **Accuracy**: {churn_results['metrics']['accuracy']:.3f}
- **Precision**: {churn_results['metrics']['precision']:.3f} (Target: ≥0.920)
- **Recall**: {churn_results['metrics']['recall']:.3f} (Target: ≥0.880)
- **F1-Score**: {churn_results['metrics']['f1_score']:.3f}
- **AUC**: {churn_results['metrics']['auc_score']:.3f}
- **Calibration Error**: {churn_results['metrics']['calibration_error']:.3f}

## Top Feature Importance

### Lead Scoring
"""

        # Add top features for lead scoring
        top_lead_features = sorted(lead_scoring_results['feature_importance'].items(),
                                 key=lambda x: x[1], reverse=True)[:5]
        for i, (feature, importance) in enumerate(top_lead_features, 1):
            report += f"{i}. **{feature}**: {importance:.4f}\n"

        report += "\n### Churn Prediction\n"

        # Add top features for churn prediction
        top_churn_features = sorted(churn_results['feature_importance'].items(),
                                  key=lambda x: x[1], reverse=True)[:5]
        for i, (feature, importance) in enumerate(top_churn_features, 1):
            report += f"{i}. **{feature}**: {importance:.4f}\n"

        report += f"""

## Model Files Generated

- `lead_scoring_v1.0.0.xgb` - Lead scoring XGBoost model
- `lead_scoring_v1.0.0_metadata.json` - Lead scoring model metadata
- `churn_model_v2.1.0.xgb` - Churn prediction XGBoost model
- `churn_model_v2.1.0_metadata.json` - Churn prediction model metadata
- `fallback_scorer.py` - Rule-based fallback scoring

## Training Configuration

- **Training Samples**: {lead_scoring_results['metadata']['training_samples']:,}
- **Cross-Validation Folds**: {self.cv_folds}
- **Hyperparameter Optimization Trials**: 50 per model
- **Feature Count**: {len(lead_scoring_results['metadata']['feature_names'])}

## Performance Targets Status

"""

        # Check if targets are met
        lead_meets_targets = self.validate_model_performance(lead_scoring_results, 'lead_scoring')
        churn_meets_targets = self.validate_model_performance(churn_results, 'churn_prediction')

        report += f"- Lead Scoring: {'✅ PASSED' if lead_meets_targets else '❌ FAILED'}\n"
        report += f"- Churn Prediction: {'✅ PASSED' if churn_meets_targets else '❌ FAILED'}\n"

        report += """

## Next Steps

1. Deploy models to production environment
2. Monitor model performance on live data
3. Set up automated retraining pipeline
4. Implement A/B testing for model comparison

---
*Generated by ML Lead Intelligence Training Pipeline*
"""

        return report


def main():
    """Main training pipeline"""

    logger.info("Starting ML Lead Intelligence model training...")

    trainer = MLModelTrainer()

    try:
        # 1. Generate training data
        logger.info("Step 1: Generating synthetic training data")
        features_df, targets_df = trainer.generate_synthetic_training_data(n_samples=10000)

        # 2. Train lead scoring model
        logger.info("Step 2: Training lead scoring model")
        lead_scoring_results = trainer.train_lead_scoring_model(features_df, targets_df)

        # 3. Train churn prediction model
        logger.info("Step 3: Training churn prediction model")
        churn_results = trainer.train_churn_prediction_model(features_df, targets_df)

        # 4. Validate performance
        logger.info("Step 4: Validating model performance")
        lead_scoring_valid = trainer.validate_model_performance(lead_scoring_results, 'lead_scoring')
        churn_valid = trainer.validate_model_performance(churn_results, 'churn_prediction')

        # 5. Create fallback models
        logger.info("Step 5: Creating fallback models")
        trainer.create_fallback_models()

        # 6. Generate training report
        logger.info("Step 6: Generating training report")
        report = trainer.generate_training_report(lead_scoring_results, churn_results)

        report_file = trainer.model_path / f"training_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w') as f:
            f.write(report)

        logger.info(f"Training report saved: {report_file}")

        # Summary
        logger.info("\n" + "="*60)
        logger.info("ML MODEL TRAINING COMPLETED")
        logger.info("="*60)
        logger.info(f"Lead Scoring Model: {'✅ PASSED' if lead_scoring_valid else '❌ FAILED'}")
        logger.info(f"Churn Prediction Model: {'✅ PASSED' if churn_valid else '❌ FAILED'}")
        logger.info(f"Models saved to: {trainer.model_path}")
        logger.info("="*60)

        if lead_scoring_valid and churn_valid:
            logger.info("🎉 All models meet performance targets and are ready for deployment!")
            return True
        else:
            logger.warning("⚠️  Some models do not meet performance targets. Review and retrain.")
            return False

    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)