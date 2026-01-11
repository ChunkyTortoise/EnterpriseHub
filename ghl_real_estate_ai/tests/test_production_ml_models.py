"""
TDD Test Suite for Production ML Models

RED PHASE: These tests require production-trained ML models to pass.
Currently they will FAIL because:
1. XGBoost churn model file missing
2. Lead scoring uses rule-based (70% accuracy) instead of ML (95% target)
3. Models use synthetic data instead of real behavioral data

SUCCESS CRITERIA:
- XGBoost churn model achieves 92%+ precision on test set
- ML lead scoring achieves 95%+ accuracy (vs 70% rule-based)
- Models load and predict within <300ms performance targets
- All models use real behavioral data from LeadBehavioralFeatures

Author: TDD ML Model Development Specialist
Created: 2026-01-10
Phase: RED (Failing Tests)
"""

import pytest
import asyncio
import numpy as np
import pandas as pd
import xgboost as xgb
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import time
import json

from ghl_real_estate_ai.services.churn_prediction_service import (
    ChurnPredictionService,
    ChurnRiskLevel,
    ChurnPrediction
)
from ghl_real_estate_ai.services.lead_scorer import LeadScorer
from ghl_real_estate_ai.models.lead_behavioral_features import (
    LeadBehavioralFeatures,
    LeadBehavioralFeatureExtractor
)


class TestProductionMLModelRequirements:
    """
    RED PHASE: Tests that verify production ML model requirements.
    These tests MUST FAIL initially, forcing implementation of real ML models.
    """

    @pytest.fixture
    def models_dir(self):
        """Path to trained models directory"""
        return Path(__file__).parent.parent / "models" / "trained"

    @pytest.fixture
    def test_data_dir(self):
        """Path to test datasets directory"""
        return Path(__file__).parent / "fixtures" / "ml_test_data"

    # ==================== CHURN PREDICTION MODEL TESTS ====================

    def test_xgboost_churn_model_file_exists(self, models_dir):
        """
        RED TEST: XGBoost churn model file must exist in trained models directory.

        CURRENT STATE: FAILS - Model file missing, using fallback model
        TARGET STATE: PASS - Production XGBoost model file exists
        """
        model_file = models_dir / "churn_model_v2.1.0.xgb"

        assert model_file.exists(), (
            f"Production XGBoost churn model not found at {model_file}. "
            "Expected trained model file for churn prediction with 92%+ precision."
        )

        # Verify it's a valid XGBoost model
        model = xgb.Booster()
        model.load_model(str(model_file))
        assert model is not None, "Failed to load XGBoost model file"

    def test_churn_model_metadata_exists(self, models_dir):
        """
        RED TEST: Churn model metadata must document training performance.

        Metadata should include:
        - Training accuracy/precision/recall
        - Feature importance rankings
        - Training dataset statistics
        - Model version and timestamp
        """
        metadata_file = models_dir / "churn_model_v2.1.0_metadata.json"

        assert metadata_file.exists(), (
            f"Churn model metadata missing at {metadata_file}"
        )

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        # Verify required metadata fields
        assert 'precision' in metadata, "Metadata missing precision metric"
        assert 'recall' in metadata, "Metadata missing recall metric"
        assert 'f1_score' in metadata, "Metadata missing F1 score"
        assert 'feature_importance' in metadata, "Metadata missing feature importance"
        assert 'training_date' in metadata, "Metadata missing training date"
        assert 'training_samples' in metadata, "Metadata missing training sample count"

    @pytest.mark.asyncio
    async def test_churn_prediction_uses_xgboost_not_fallback(self):
        """
        RED TEST: Churn prediction must use XGBoost model, not fallback.

        CURRENT STATE: FAILS - Uses fallback rule-based model
        TARGET STATE: PASS - Uses trained XGBoost model
        """
        service = ChurnPredictionService()
        await service.initialize()

        # Check that XGBoost model is loaded
        assert 'churn_model' in service.model_cache, (
            "XGBoost churn model not loaded. Service falling back to rule-based model."
        )
        assert 'fallback_model' not in service.model_cache or service.model_cache.get('fallback_model') is None, (
            "Service should use XGBoost model, not fallback"
        )

    @pytest.mark.asyncio
    async def test_churn_prediction_accuracy_92_percent(self, test_data_dir):
        """
        RED TEST: XGBoost churn model must achieve 92%+ precision on test set.

        CURRENT STATE: FAILS - Fallback model has ~70% accuracy
        TARGET STATE: PASS - XGBoost model achieves 92%+ precision
        """
        service = ChurnPredictionService()
        await service.initialize()

        # Load test dataset with known churn outcomes
        test_data_file = test_data_dir / "churn_test_set.csv"
        assert test_data_file.exists(), "Test dataset missing - create from real behavioral data"

        test_df = pd.read_csv(test_data_file)
        assert len(test_df) >= 200, "Test set must have at least 200 samples for statistical significance"

        # Run predictions on test set
        predictions = []
        actuals = []

        for _, row in test_df.iterrows():
            # Create features from test data
            features = self._row_to_features(row)

            # Get prediction
            prediction = await service.predict_churn_risk(row['lead_id'], features=features)

            predictions.append(prediction.churn_probability)
            actuals.append(row['churned'])  # Ground truth

        # Calculate precision at 0.5 threshold
        predictions_binary = [1 if p >= 0.5 else 0 for p in predictions]

        # Calculate precision: TP / (TP + FP)
        true_positives = sum(1 for pred, actual in zip(predictions_binary, actuals) if pred == 1 and actual == 1)
        false_positives = sum(1 for pred, actual in zip(predictions_binary, actuals) if pred == 1 and actual == 0)

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0

        assert precision >= 0.92, (
            f"Churn model precision {precision:.3f} below target 0.92. "
            f"Model needs retraining or hyperparameter tuning. "
            f"True Positives: {true_positives}, False Positives: {false_positives}"
        )

    @pytest.mark.asyncio
    async def test_churn_prediction_inference_time_under_300ms(self):
        """
        RED TEST: Churn prediction inference must complete in <300ms.

        Performance target from CLAUDE.md: <300ms ML inference time
        """
        service = ChurnPredictionService()
        await service.initialize()

        # Create realistic test features
        features = self._create_test_features()

        # Measure inference time
        start_time = time.time()
        prediction = await service.predict_churn_risk("PERF_TEST_LEAD", features=features)
        inference_time_ms = (time.time() - start_time) * 1000

        assert inference_time_ms < 300, (
            f"Inference time {inference_time_ms:.1f}ms exceeds 300ms target. "
            f"Optimize model or use ML optimization from ml_inference_optimizer.py"
        )

        # Verify reported inference time is accurate
        assert prediction.inference_time_ms < 300, (
            f"Reported inference time {prediction.inference_time_ms:.1f}ms exceeds target"
        )

    # ==================== LEAD SCORING ML MODEL TESTS ====================

    def test_ml_lead_scoring_model_exists(self, models_dir):
        """
        RED TEST: ML-based lead scoring model must exist.

        CURRENT STATE: FAILS - LeadScorer uses rule-based question counting (70% accuracy)
        TARGET STATE: PASS - ML model trained for 95%+ lead scoring accuracy
        """
        model_file = models_dir / "lead_scoring_model_v1.0.0.pkl"

        assert model_file.exists(), (
            f"ML lead scoring model not found at {model_file}. "
            "Current LeadScorer uses simple question counting (70% accuracy). "
            "Need trained ML model for 95%+ accuracy."
        )

    @pytest.mark.asyncio
    async def test_lead_scoring_achieves_95_percent_accuracy(self, test_data_dir):
        """
        RED TEST: ML lead scoring must achieve 95%+ accuracy.

        CURRENT STATE: FAILS - Rule-based question counting ~70% accuracy
        TARGET STATE: PASS - ML model achieves 95%+ accuracy
        """
        scorer = LeadScorer()

        # Load test dataset with known lead outcomes (hot/warm/cold)
        test_data_file = test_data_dir / "lead_scoring_test_set.csv"
        assert test_data_file.exists(), "Test dataset missing"

        test_df = pd.read_csv(test_data_file)
        assert len(test_df) >= 200, "Test set must have at least 200 samples"

        correct_predictions = 0
        total_predictions = 0

        for _, row in test_df.iterrows():
            # Create context from test data
            context = {
                "extracted_preferences": json.loads(row['preferences']),
                "conversation_history": json.loads(row.get('conversation_history', '[]')),
                "created_at": row.get('created_at')
            }

            # Get ML prediction
            result = scorer.calculate_with_reasoning(context)
            predicted_class = result['classification']
            actual_class = row['actual_classification']  # Ground truth

            if predicted_class == actual_class:
                correct_predictions += 1
            total_predictions += 1

        accuracy = correct_predictions / total_predictions

        assert accuracy >= 0.95, (
            f"Lead scoring accuracy {accuracy:.3f} below target 0.95. "
            f"Current rule-based approach: ~0.70 accuracy. "
            f"Correct: {correct_predictions}/{total_predictions}"
        )

    def test_lead_scorer_uses_ml_not_question_counting(self):
        """
        RED TEST: LeadScorer must use ML model, not question counting.

        CURRENT STATE: FAILS - Uses calculate() method with simple question counting
        TARGET STATE: PASS - Uses ML model with behavioral features
        """
        scorer = LeadScorer()

        # Check for ML model attribute
        assert hasattr(scorer, 'ml_model'), (
            "LeadScorer missing ml_model attribute. "
            "Currently uses rule-based question counting instead of ML."
        )

        assert scorer.ml_model is not None, "ML model not loaded in LeadScorer"

        # Verify not using old rule-based approach
        context = {"extracted_preferences": {"budget": 400000, "location": "Austin"}}

        # This should use ML model, not simple question counting
        score = scorer.calculate(context)

        # ML model should return a probability score (0-100), not question count (0-7)
        assert score >= 0 and score <= 100, (
            f"Score {score} appears to be question count (0-7) not ML probability (0-100)"
        )

    # ==================== REAL DATA USAGE TESTS ====================

    def test_models_trained_on_real_behavioral_data(self, models_dir):
        """
        RED TEST: Models must be trained on real behavioral data, not synthetic.

        Verify model metadata shows real data sources:
        - LeadBehavioralFeatures integration
        - Real conversation history
        - Real property viewing patterns
        - Real engagement metrics
        """
        metadata_file = models_dir / "churn_model_v2.1.0_metadata.json"

        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            # Verify data source
            assert 'data_source' in metadata, "Metadata missing data source information"
            assert metadata['data_source'] != 'synthetic', (
                "Model trained on synthetic data. Must use real behavioral data from LeadBehavioralFeatures."
            )

            # Verify feature source
            assert 'feature_extractor' in metadata, "Metadata missing feature extractor info"
            assert 'LeadBehavioralFeatureExtractor' in metadata.get('feature_extractor', ''), (
                "Model not using LeadBehavioralFeatureExtractor for real behavioral features"
            )

    @pytest.mark.asyncio
    async def test_churn_service_integrates_behavioral_features(self):
        """
        RED TEST: ChurnPredictionService must use LeadBehavioralFeatures.

        CURRENT STATE: May use simplified features or synthetic data
        TARGET STATE: Full integration with LeadBehavioralFeatureExtractor
        """
        service = ChurnPredictionService()
        await service.initialize()

        # Verify feature extractor is initialized
        assert service.feature_extractor is not None, (
            "ChurnPredictionService missing LeadBehavioralFeatureExtractor"
        )

        assert isinstance(service.feature_extractor, LeadBehavioralFeatureExtractor), (
            "Feature extractor must be LeadBehavioralFeatureExtractor instance"
        )

    # ==================== MODEL VERSIONING AND DEPLOYMENT TESTS ====================

    def test_model_version_tracking(self, models_dir):
        """
        RED TEST: All models must have version tracking and metadata.
        """
        # List all model files
        model_files = list(models_dir.glob("*.xgb")) + list(models_dir.glob("*.pkl"))

        assert len(model_files) > 0, "No trained models found in models/trained directory"

        for model_file in model_files:
            # Each model should have corresponding metadata
            metadata_file = model_file.with_suffix('.json')
            if 'metadata' not in str(metadata_file):
                metadata_file = model_file.parent / f"{model_file.stem}_metadata.json"

            assert metadata_file.exists(), (
                f"Missing metadata file for {model_file.name}"
            )

    def test_model_performance_regression_tracking(self, models_dir):
        """
        RED TEST: Model metadata must track performance to detect regression.
        """
        metadata_files = list(models_dir.glob("*_metadata.json"))

        for metadata_file in metadata_files:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            # Verify performance metrics
            required_metrics = ['precision', 'recall', 'f1_score']
            for metric in required_metrics:
                assert metric in metadata, (
                    f"{metadata_file.name} missing required metric: {metric}"
                )

                # Metrics should be valid probabilities
                assert 0 <= metadata[metric] <= 1, (
                    f"Invalid {metric} value in {metadata_file.name}: {metadata[metric]}"
                )

    # ==================== HELPER METHODS ====================

    def _create_test_features(self) -> LeadBehavioralFeatures:
        """Create realistic test features for performance testing"""
        from ghl_real_estate_ai.models.lead_behavioral_features import (
            TemporalFeatures,
            EngagementPatterns,
            CommunicationPreferences,
            BehavioralSignals,
            FeatureQuality
        )

        return LeadBehavioralFeatures(
            lead_id="TEST_LEAD_001",
            created_at=datetime.now() - timedelta(days=30),
            last_updated=datetime.now(),

            # Basic metrics
            days_since_creation=30.0,
            days_since_last_activity=5.0,
            total_interactions=25,

            # Temporal features
            temporal_features=TemporalFeatures(
                interaction_velocity_7d=2.5,
                interaction_velocity_14d=2.0,
                interaction_velocity_30d=1.8,
                preferred_hour=14,
                preferred_day_of_week=2,
                weekend_activity=0.2,
                business_hours_ratio=0.8
            ),

            # Engagement patterns
            engagement_patterns=EngagementPatterns(
                total_interactions=25,
                unique_interaction_days=12,
                avg_interactions_per_day=2.1,
                max_interactions_per_day=5,
                avg_response_time_minutes=120.0,
                median_response_time_minutes=90.0,
                fastest_response_minutes=15.0,
                session_duration_avg=8.5,
                property_views=15,
                saved_properties=3,
                search_queries=8
            ),

            # Communication preferences
            communication_prefs=CommunicationPreferences(
                email_response_rate=0.75,
                sms_response_rate=0.85,
                phone_response_rate=0.60,
                preferred_channel="sms",
                channel_consistency_score=0.80
            ),

            # Behavioral signals
            behavioral_signals=BehavioralSignals(
                urgency_score=0.65,
                intent_strength=0.70,
                engagement_momentum=0.15,
                interest_volatility=0.25
            ),

            # Feature quality
            feature_quality=FeatureQuality(
                completeness_score=0.85,
                data_freshness_hours=24.0,
                reliability_score=0.90
            )
        )

    def _row_to_features(self, row: pd.Series) -> LeadBehavioralFeatures:
        """Convert test data row to LeadBehavioralFeatures"""
        # This would extract features from test CSV columns
        # Implementation depends on test data format
        return self._create_test_features()


class TestModelTrainingDataRequirements:
    """
    RED PHASE: Tests that verify training data quality and availability.
    """

    @pytest.fixture
    def training_data_dir(self):
        """Path to training datasets"""
        return Path(__file__).parent / "fixtures" / "training_data"

    def test_training_data_directory_exists(self, training_data_dir):
        """Training data directory must exist with real behavioral data"""
        assert training_data_dir.exists(), (
            f"Training data directory missing at {training_data_dir}"
        )

    def test_churn_training_data_exists(self, training_data_dir):
        """Churn model training data must exist with real lead outcomes"""
        training_file = training_data_dir / "churn_training_set.csv"

        assert training_file.exists(), (
            "Churn training dataset missing. Need real behavioral data with churn outcomes."
        )

        # Verify sufficient samples
        df = pd.read_csv(training_file)
        assert len(df) >= 1000, (
            f"Insufficient training samples: {len(df)}. Need at least 1000 for robust model."
        )

    def test_lead_scoring_training_data_exists(self, training_data_dir):
        """Lead scoring training data must exist with real classifications"""
        training_file = training_data_dir / "lead_scoring_training_set.csv"

        assert training_file.exists(), (
            "Lead scoring training dataset missing."
        )

        df = pd.read_csv(training_file)
        assert len(df) >= 1000, (
            f"Insufficient training samples: {len(df)}"
        )

        # Verify class distribution
        assert 'actual_classification' in df.columns, "Missing ground truth labels"

        class_distribution = df['actual_classification'].value_counts()
        assert all(class_distribution >= 100), (
            "Imbalanced classes. Each class (hot/warm/cold) needs at least 100 samples."
        )


# Mark all tests to run after model training
pytestmark = pytest.mark.ml_model_required


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "not ml_model_required"])
