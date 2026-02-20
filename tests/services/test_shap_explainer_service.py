import pytest

pytestmark = pytest.mark.integration

"""
Test suite for SHAP Explainer Service

Comprehensive tests for the SHAP explainability service, ensuring
transparent AI explanations work correctly and performantly.

Tests cover:
- SHAP explanation generation
- Business context mapping
- Visualization creation
- What-if scenario analysis
- Caching and performance
- Error handling and fallbacks
"""

import asyncio
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pandas as pd
import pytest
import shap
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from ghl_real_estate_ai.services.shap_explainer_service import (
    BusinessFeatureMapper,
    FeatureContext,
    SHAPExplainerService,
    SHAPExplanation,
    SHAPVisualizationBuilder,
    WhatIfAnalyzer,
    get_shap_explainer_service,
    get_shap_explanation,
)


class TestFeatureContext:
    """Test FeatureContext dataclass functionality"""

    def test_feature_context_creation(self):
        """Test creating FeatureContext with all fields"""
        context = FeatureContext(
            feature_name="response_time_hours",
            display_name="Response Speed",
            category="behavioral",
            description="How quickly the lead responds",
            positive_explanation_template="Quick response indicates engagement",
            negative_explanation_template="Slow response may indicate disinterest",
            business_impact="Quick responders convert 3x more",
            actionable_insight_template="Follow up within 2 hours",
        )

        assert context.feature_name == "response_time_hours"
        assert context.display_name == "Response Speed"
        assert context.category == "behavioral"
        assert "Quick response" in context.positive_explanation_template
        assert "Slow response" in context.negative_explanation_template


class TestBusinessFeatureMapper:
    """Test BusinessFeatureMapper functionality"""

    @pytest.fixture
    def feature_mapper(self):
        return BusinessFeatureMapper()

    def test_feature_mapper_initialization(self, feature_mapper):
        """Test that feature mapper initializes with expected features"""
        expected_features = [
            "response_time_hours",
            "message_length_avg",
            "questions_asked",
            "price_range_mentioned",
            "timeline_urgency",
        ]

        for feature in expected_features:
            assert feature in feature_mapper.feature_contexts
            context = feature_mapper.feature_contexts[feature]
            assert isinstance(context, FeatureContext)
            assert context.feature_name == feature

    def test_get_business_explanation_positive(self, feature_mapper):
        """Test business explanation for positive SHAP value"""
        explanation = feature_mapper.get_business_explanation(
            "response_time_hours",
            0.15,  # Positive SHAP value
            1.5,  # Feature value (1.5 hours)
        )

        assert "Response Speed:" in explanation
        assert "1.5 hours" in explanation
        assert "indicating high engagement" in explanation

    def test_get_business_explanation_negative(self, feature_mapper):
        """Test business explanation for negative SHAP value"""
        explanation = feature_mapper.get_business_explanation(
            "response_time_hours",
            -0.10,  # Negative SHAP value
            24.0,  # Feature value (24 hours)
        )

        assert "Response Speed:" in explanation
        assert "24.0 hours" in explanation
        assert "may indicate lower priority" in explanation

    def test_get_business_explanation_unknown_feature(self, feature_mapper):
        """Test business explanation for unknown feature"""
        explanation = feature_mapper.get_business_explanation("unknown_feature", 0.05, 10.0)

        assert "unknown_feature: +0.050 impact" in explanation

    def test_get_actionable_insight(self, feature_mapper):
        """Test getting actionable insights"""
        insight = feature_mapper.get_actionable_insight("response_time_hours", 0.1)
        assert insight is not None
        assert "Follow up within 2 hours" in insight

        # Unknown feature should return None
        unknown_insight = feature_mapper.get_actionable_insight("unknown_feature", 0.1)
        assert unknown_insight is None

    def test_get_feature_category(self, feature_mapper):
        """Test feature category retrieval"""
        category = feature_mapper.get_feature_category("response_time_hours")
        assert category == "behavioral"

        # Unknown feature should return 'other'
        unknown_category = feature_mapper.get_feature_category("unknown_feature")
        assert unknown_category == "other"


class TestSHAPVisualizationBuilder:
    """Test SHAP visualization builder functionality"""

    @pytest.fixture
    def feature_mapper(self):
        return BusinessFeatureMapper()

    @pytest.fixture
    def visualization_builder(self, feature_mapper):
        return SHAPVisualizationBuilder(feature_mapper)

    @pytest.fixture
    def sample_explanation(self):
        """Create sample SHAP explanation for testing"""
        return SHAPExplanation(
            lead_id="test_lead_001",
            lead_name="Test Lead",
            explained_at=datetime.now(),
            base_value=50.0,
            prediction=75.0,
            shap_values={
                "response_time_hours": 0.15,
                "message_length_avg": -0.05,
                "questions_asked": 0.20,
                "price_range_mentioned": 0.10,
            },
            feature_importance={
                "response_time_hours": 0.15,
                "message_length_avg": 0.05,
                "questions_asked": 0.20,
                "price_range_mentioned": 0.10,
            },
            business_explanations={},
            key_drivers=[],
            risk_factors=[],
            opportunities=[],
            waterfall_data={},
            feature_impact_data={},
            explanation_time_ms=150.0,
        )

    def test_build_waterfall_chart(self, visualization_builder, sample_explanation):
        """Test waterfall chart creation"""
        fig = visualization_builder.build_waterfall_chart(sample_explanation)

        assert fig is not None
        assert "data" in fig.to_dict()
        assert len(fig.data) == 1  # One trace for waterfall
        assert fig.data[0].type == "waterfall"
        assert "Test Lead" in fig.layout.title.text

    def test_build_feature_importance_chart(self, visualization_builder, sample_explanation):
        """Test feature importance chart creation"""
        fig = visualization_builder.build_feature_importance_chart(sample_explanation)

        assert fig is not None
        assert "data" in fig.to_dict()
        assert "Test Lead" in fig.layout.title.text
        # Should have traces for each feature
        assert len(fig.data) > 0


class TestWhatIfAnalyzer:
    """Test what-if scenario analysis functionality"""

    @pytest.fixture
    def sample_model(self):
        """Create sample trained model for testing"""
        # Create simple demo model
        X = np.random.rand(100, 5)
        y = (X[:, 0] + X[:, 1] > 1).astype(int)

        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        return model

    @pytest.fixture
    def sample_scaler(self):
        """Create sample scaler"""
        scaler = StandardScaler()
        X = np.random.rand(100, 5)
        scaler.fit(X)
        return scaler

    @pytest.fixture
    def what_if_analyzer(self, sample_model, sample_scaler):
        """Create what-if analyzer for testing"""
        explainer = shap.TreeExplainer(sample_model)
        feature_names = ["feature1", "feature2", "feature3", "feature4", "feature5"]

        return WhatIfAnalyzer(
            model=sample_model, scaler=sample_scaler, shap_explainer=explainer, feature_names=feature_names
        )

    @pytest.mark.asyncio
    async def test_analyze_scenario(self, what_if_analyzer):
        """Test what-if scenario analysis"""
        original_features = np.array([0.5, 0.3, 0.8, 0.2, 0.7])
        modified_features = {"feature1": 0.9, "feature3": 0.1}

        result = await what_if_analyzer.analyze_scenario(original_features, modified_features)

        # Verify result structure
        assert "original_score" in result
        assert "modified_score" in result
        assert "score_change" in result
        assert "modified_features" in result
        assert "shap_changes" in result
        assert "scenario_feasible" in result
        assert "recommendations" in result

        # Verify data types
        assert isinstance(result["original_score"], float)
        assert isinstance(result["modified_score"], float)
        assert isinstance(result["score_change"], float)
        assert result["modified_features"] == modified_features
        assert isinstance(result["recommendations"], list)

    def test_assess_feasibility(self, what_if_analyzer):
        """Test feasibility assessment for scenarios"""
        # Test realistic scenario
        realistic_scenario = {"response_time_hours": 1.0, "message_length_avg": 50.0, "questions_asked": 3.0}

        feasibility = what_if_analyzer._assess_feasibility(realistic_scenario)
        assert "response_time_hours" in feasibility
        assert feasibility["response_time_hours"] == "High"

        # Test unrealistic scenario
        unrealistic_scenario = {
            "response_time_hours": 100.0,  # 100 hours response time
            "questions_asked": 50.0,  # 50 questions
        }

        feasibility = what_if_analyzer._assess_feasibility(unrealistic_scenario)
        assert feasibility["response_time_hours"] == "Low"
        assert feasibility["questions_asked"] == "Low"

    def test_generate_recommendations(self, what_if_analyzer):
        """Test recommendation generation"""
        high_impact_scenario = {"response_time_hours": 0.5}
        recommendations = what_if_analyzer._generate_recommendations(
            high_impact_scenario,
            15.0,  # High score change
        )

        assert isinstance(recommendations, list)
        assert len(recommendations) <= 3  # Top 3 recommendations
        assert any("automated response" in rec.lower() for rec in recommendations)

        low_impact_scenario = {"message_length_avg": 60}
        recommendations = what_if_analyzer._generate_recommendations(
            low_impact_scenario,
            2.0,  # Low score change
        )

        assert any("Low impact" in rec for rec in recommendations)


class TestSHAPExplainerService:
    """Test main SHAP explainer service"""

    @pytest.fixture
    def shap_service(self):
        return SHAPExplainerService()

    @pytest.fixture
    def sample_ml_components(self):
        """Create sample ML components for testing"""
        # Create simple model
        X = np.random.rand(100, 10)
        y = (X[:, 0] + X[:, 1] > 1).astype(int)

        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)

        scaler = StandardScaler()
        scaler.fit(X)

        explainer = shap.TreeExplainer(model)

        feature_names = [
            "response_time_hours",
            "message_length_avg",
            "questions_asked",
            "price_range_mentioned",
            "timeline_urgency",
            "location_specificity",
            "financing_mentioned",
            "family_size_mentioned",
            "job_stability_score",
            "previous_real_estate_experience",
        ]

        return model, scaler, explainer, feature_names

    @pytest.mark.asyncio
    async def test_explain_prediction_success(self, shap_service, sample_ml_components):
        """Test successful SHAP explanation generation"""
        model, scaler, explainer, feature_names = sample_ml_components
        features = np.random.rand(10)

        with patch.object(shap_service.analytics, "track_event", new_callable=AsyncMock):
            explanation = await shap_service.explain_prediction(
                model=model,
                scaler=scaler,
                shap_explainer=explainer,
                feature_names=feature_names,
                features=features,
                lead_id="test_lead_001",
                lead_name="Test Lead",
                prediction_score=75.0,
            )

        # Verify explanation structure
        assert isinstance(explanation, SHAPExplanation)
        assert explanation.lead_id == "test_lead_001"
        assert explanation.lead_name == "Test Lead"
        assert explanation.prediction == 75.0
        assert len(explanation.shap_values) == len(feature_names)
        assert len(explanation.feature_importance) == len(feature_names)
        assert len(explanation.key_drivers) <= 5
        assert explanation.explanation_time_ms > 0
        assert not explanation.cached  # First time, not cached

    @pytest.mark.asyncio
    async def test_explain_prediction_cached(self, shap_service, sample_ml_components):
        """Test cached SHAP explanation retrieval"""
        model, scaler, explainer, feature_names = sample_ml_components
        features = np.random.rand(10)

        # Mock cache to return a cached explanation
        cached_explanation = SHAPExplanation(
            lead_id="test_lead_001",
            lead_name="Test Lead",
            explained_at=datetime.now(),
            base_value=50.0,
            prediction=75.0,
            shap_values={"feature1": 0.1},
            feature_importance={"feature1": 0.1},
            business_explanations={},
            key_drivers=[],
            risk_factors=[],
            opportunities=[],
            waterfall_data={},
            feature_impact_data={},
            explanation_time_ms=100.0,
            cached=True,
        )

        with patch("ghl_real_estate_ai.services.shap_explainer_service.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value=cached_explanation)

            explanation = await shap_service.explain_prediction(
                model=model,
                scaler=scaler,
                shap_explainer=explainer,
                feature_names=feature_names,
                features=features,
                lead_id="test_lead_001",
                lead_name="Test Lead",
                prediction_score=75.0,
            )

        assert explanation.cached == True
        assert explanation.lead_id == "test_lead_001"
        assert shap_service.metrics["cache_hits"] == 1

    @pytest.mark.asyncio
    async def test_explain_prediction_error_handling(self, shap_service):
        """Test error handling in SHAP explanation"""
        # Use invalid inputs to trigger an error
        with patch.object(shap_service.analytics, "track_event", new_callable=AsyncMock):
            explanation = await shap_service.explain_prediction(
                model=None,  # Invalid model
                scaler=None,
                shap_explainer=None,
                feature_names=[],
                features=np.array([]),
                lead_id="test_lead_001",
                lead_name="Test Lead",
                prediction_score=75.0,
            )

        # Should return minimal explanation on error
        assert isinstance(explanation, SHAPExplanation)
        assert explanation.lead_id == "test_lead_001"
        assert len(explanation.shap_values) == 0
        assert not explanation.what_if_ready
        assert "failed" in explanation.business_explanations.get("error", "")

    def test_generate_cache_key(self, shap_service):
        """Test cache key generation"""
        features = np.array([1.0, 2.0, 3.0])
        cache_key = shap_service._generate_cache_key("lead_123", features)

        assert cache_key.startswith("shap_explanation:lead_123:")
        assert len(cache_key) > len("shap_explanation:lead_123:")

        # Same features should generate same key
        cache_key2 = shap_service._generate_cache_key("lead_123", features)
        assert cache_key == cache_key2

        # Different features should generate different key
        different_features = np.array([1.1, 2.0, 3.0])
        cache_key3 = shap_service._generate_cache_key("lead_123", different_features)
        assert cache_key != cache_key3

    @pytest.mark.asyncio
    async def test_create_waterfall_visualization(self, shap_service):
        """Test waterfall visualization creation"""
        sample_explanation = SHAPExplanation(
            lead_id="test_lead",
            lead_name="Test Lead",
            explained_at=datetime.now(),
            base_value=50.0,
            prediction=75.0,
            shap_values={"feature1": 0.15, "feature2": -0.05},
            feature_importance={"feature1": 0.15, "feature2": 0.05},
            business_explanations={},
            key_drivers=[],
            risk_factors=[],
            opportunities=[],
            waterfall_data={},
            feature_impact_data={},
            explanation_time_ms=150.0,
        )

        fig = await shap_service.create_waterfall_visualization(sample_explanation)
        assert fig is not None
        assert fig.data[0].type == "waterfall"

    @pytest.mark.asyncio
    async def test_perform_what_if_analysis(self, shap_service, sample_ml_components):
        """Test what-if analysis functionality"""
        model, scaler, explainer, feature_names = sample_ml_components

        # Initialize what-if analyzer
        shap_service.what_if_analyzer = WhatIfAnalyzer(model, scaler, explainer, feature_names)

        sample_explanation = SHAPExplanation(
            lead_id="test_lead",
            lead_name="Test Lead",
            explained_at=datetime.now(),
            base_value=50.0,
            prediction=75.0,
            shap_values={},
            feature_importance={},
            business_explanations={},
            key_drivers=[],
            risk_factors=[],
            opportunities=[],
            waterfall_data={},
            feature_impact_data={},
            explanation_time_ms=150.0,
            what_if_ready=True,
        )

        modified_features = {"response_time_hours": 1.0}

        with patch.object(shap_service.analytics, "track_event", new_callable=AsyncMock):
            result = await shap_service.perform_what_if_analysis(sample_explanation, modified_features)

        assert "original_score" in result
        assert "modified_score" in result
        assert "analysis_time_ms" in result
        assert shap_service.metrics["what_if_scenarios"] == 1

    @pytest.mark.asyncio
    async def test_perform_what_if_analysis_not_ready(self, shap_service):
        """Test what-if analysis when not ready"""
        sample_explanation = SHAPExplanation(
            lead_id="test_lead",
            lead_name="Test Lead",
            explained_at=datetime.now(),
            base_value=50.0,
            prediction=75.0,
            shap_values={},
            feature_importance={},
            business_explanations={},
            key_drivers=[],
            risk_factors=[],
            opportunities=[],
            waterfall_data={},
            feature_impact_data={},
            explanation_time_ms=150.0,
            what_if_ready=False,  # Not ready
        )

        result = await shap_service.perform_what_if_analysis(sample_explanation, {"feature1": 1.0})

        assert "error" in result
        assert "not available" in result["error"]

    def test_get_performance_metrics(self, shap_service):
        """Test performance metrics retrieval"""
        # Set some test metrics
        shap_service.metrics["explanations_generated"] = 10
        shap_service.metrics["cache_hits"] = 5
        shap_service.metrics["what_if_scenarios"] = 3

        metrics = shap_service.get_performance_metrics()

        assert metrics["explanations_generated"] == 10
        assert metrics["cache_hits"] == 5
        assert metrics["what_if_scenarios"] == 3
        assert metrics["total_requests"] == 15
        assert metrics["cache_hit_rate_percent"] == 33.33


class TestFactoryFunctions:
    """Test factory functions and service initialization"""

    def test_get_shap_explainer_service(self):
        """Test singleton service factory"""
        service1 = get_shap_explainer_service()
        service2 = get_shap_explainer_service()

        # Should return same instance (singleton)
        assert service1 is service2
        assert isinstance(service1, SHAPExplainerService)

    @pytest.mark.asyncio
    async def test_get_shap_explanation_factory(self):
        """Test factory function for getting explanations"""
        # Create minimal mock components
        model = Mock()
        scaler = Mock()
        explainer = Mock()
        feature_names = ["feature1", "feature2"]
        features = np.array([1.0, 2.0])

        with patch("ghl_real_estate_ai.services.shap_explainer_service.SHAPExplainerService") as mock_service_class:
            mock_service = Mock()
            mock_service.explain_prediction = AsyncMock(return_value="test_explanation")
            mock_service_class.return_value = mock_service

            result = await get_shap_explanation(
                model, scaler, explainer, feature_names, features, "test_lead", "Test Lead", 75.0
            )

            assert result == "test_explanation"
            mock_service.explain_prediction.assert_called_once()


class TestIntegrationScenarios:
    """Integration tests for realistic usage scenarios"""

    @pytest.mark.asyncio
    async def test_end_to_end_explanation_workflow(self):
        """Test complete end-to-end SHAP explanation workflow"""
        # Create realistic ML components
        np.random.seed(42)  # For reproducible tests

        # Training data that mimics real estate lead features
        n_samples = 200
        X = np.random.rand(n_samples, 10)

        # Create realistic target based on some features
        y = (
            (X[:, 0] < 0.3)  # Quick response time
            & (X[:, 2] > 0.5)  # Asks questions
            & (X[:, 4] > 0.4)
        ).astype(int)  # Shows urgency

        # Train model
        model = RandomForestClassifier(n_estimators=20, random_state=42)
        model.fit(X, y)

        # Prepare scaler
        scaler = StandardScaler()
        scaler.fit(X)

        # Create explainer
        explainer = shap.TreeExplainer(model)

        feature_names = [
            "response_time_hours",
            "message_length_avg",
            "questions_asked",
            "price_range_mentioned",
            "timeline_urgency",
            "location_specificity",
            "financing_mentioned",
            "family_size_mentioned",
            "job_stability_score",
            "previous_real_estate_experience",
        ]

        # Create test lead features (good lead)
        test_features = np.array([0.1, 0.8, 0.9, 0.8, 0.9, 0.7, 0.6, 0.5, 0.8, 0.4])

        # Get explanation
        service = SHAPExplainerService()

        with patch.object(service.analytics, "track_event", new_callable=AsyncMock):
            explanation = await service.explain_prediction(
                model=model,
                scaler=scaler,
                shap_explainer=explainer,
                feature_names=feature_names,
                features=test_features,
                lead_id="integration_test_lead",
                lead_name="John Smith",
                prediction_score=85.0,
            )

        # Verify comprehensive explanation
        assert isinstance(explanation, SHAPExplanation)
        assert explanation.lead_name == "John Smith"
        assert explanation.prediction == 85.0
        assert len(explanation.shap_values) == 10
        assert len(explanation.key_drivers) > 0
        assert explanation.what_if_ready == True

        # Test visualization creation
        waterfall_fig = await service.create_waterfall_visualization(explanation)
        assert waterfall_fig is not None

        # Test what-if analysis
        modified_features = {
            "response_time_hours": 0.95,  # Make it worse
            "questions_asked": 0.1,  # Make it worse
        }

        what_if_result = await service.perform_what_if_analysis(explanation, modified_features)

        # Should show negative impact
        assert "score_change" in what_if_result
        # With worse features, score should decrease
        assert what_if_result["score_change"] < 0

    def test_business_context_accuracy(self):
        """Test that business context mapping provides accurate insights"""
        mapper = BusinessFeatureMapper()

        # Test response time context
        quick_response_explanation = mapper.get_business_explanation(
            "response_time_hours",
            0.2,
            0.5,  # Positive impact, 0.5 hours
        )

        slow_response_explanation = mapper.get_business_explanation(
            "response_time_hours",
            -0.15,
            24.0,  # Negative impact, 24 hours
        )

        assert "high engagement" in quick_response_explanation
        assert "lower priority" in slow_response_explanation
        assert "0.5 hours" in quick_response_explanation
        assert "24.0 hours" in slow_response_explanation

        # Test questions asked context
        active_questioner_explanation = mapper.get_business_explanation(
            "questions_asked",
            0.25,
            5.0,  # Positive impact, 5 questions
        )

        passive_questioner_explanation = mapper.get_business_explanation(
            "questions_asked",
            -0.1,
            0.0,  # Negative impact, 0 questions
        )

        assert "genuine interest" in active_questioner_explanation
        assert "passive interest" in passive_questioner_explanation

    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test service performance with multiple concurrent requests"""
        service = SHAPExplainerService()

        # Create simple model for testing
        X = np.random.rand(50, 5)
        y = np.random.randint(0, 2, 50)
        model = RandomForestClassifier(n_estimators=5, random_state=42)
        model.fit(X, y)

        scaler = StandardScaler()
        scaler.fit(X)

        explainer = shap.TreeExplainer(model)
        feature_names = ["f1", "f2", "f3", "f4", "f5"]

        async def generate_explanation(lead_num: int):
            features = np.random.rand(5)

            with patch.object(service.analytics, "track_event", new_callable=AsyncMock):
                return await service.explain_prediction(
                    model=model,
                    scaler=scaler,
                    shap_explainer=explainer,
                    feature_names=feature_names,
                    features=features,
                    lead_id=f"load_test_{lead_num}",
                    lead_name=f"Lead {lead_num}",
                    prediction_score=70.0,
                )

        # Generate 10 explanations concurrently
        start_time = asyncio.get_event_loop().time()

        tasks = [generate_explanation(i) for i in range(10)]
        explanations = await asyncio.gather(*tasks)

        end_time = asyncio.get_event_loop().time()
        total_time = (end_time - start_time) * 1000  # Convert to ms

        # Verify all explanations were generated
        assert len(explanations) == 10
        for explanation in explanations:
            assert isinstance(explanation, SHAPExplanation)
            assert explanation.prediction == 70.0

        # Performance should be reasonable (adjust threshold as needed)
        avg_time_per_explanation = total_time / 10
        assert avg_time_per_explanation < 1000  # Less than 1 second per explanation

        # Check service metrics
        metrics = service.get_performance_metrics()
        assert metrics["explanations_generated"] >= 10
        assert metrics["avg_explanation_time_ms"] > 0


@pytest.fixture
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])