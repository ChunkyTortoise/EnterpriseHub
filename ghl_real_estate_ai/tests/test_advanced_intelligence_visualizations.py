"""
Tests for Advanced Intelligence Visualization Components

Comprehensive test suite for the new advanced dashboard features including:
- Lead journey mapping functionality
- Real-time sentiment analysis components
- Competitive intelligence dashboard
- Intelligent content recommendation engine
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import test targets
from streamlit_components.advanced_intelligence_visualizations import (
    AdvancedIntelligenceVisualizations,
    LeadJourneyStage,
    SentimentAnalysis,
    CompetitiveIntelligence,
    ContentRecommendation,
    create_advanced_visualizations,
    generate_sample_journey_stages,
    generate_sample_sentiment_data,
    generate_sample_competitive_data,
    generate_sample_content_recommendations
)


class TestAdvancedIntelligenceVisualizations:
    """Test suite for AdvancedIntelligenceVisualizations class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.viz = AdvancedIntelligenceVisualizations()

    def test_initialization(self):
        """Test proper initialization of visualization system."""
        assert self.viz is not None
        assert hasattr(self.viz, 'colors')
        assert isinstance(self.viz.colors, dict)
        assert 'primary' in self.viz.colors
        assert 'success' in self.viz.colors
        assert 'warning' in self.viz.colors

    def test_color_system(self):
        """Test color system functionality."""
        colors = self.viz._get_colors()
        assert isinstance(colors, dict)
        assert len(colors) >= 5  # Should have at least primary, success, warning, danger, info

        # Test color values are valid hex codes or color names
        for color_name, color_value in colors.items():
            assert isinstance(color_value, str)
            assert color_value.startswith('#') or color_value in ['red', 'blue', 'green', 'yellow', 'orange']

    @patch('streamlit.session_state', new_callable=dict)
    def test_session_state_initialization(self, mock_session_state):
        """Test session state initialization for advanced features."""
        # Mock streamlit session state
        with patch('streamlit.session_state', mock_session_state):
            viz = AdvancedIntelligenceVisualizations()

            # Should initialize session state if not present
            assert 'advanced_intelligence_state' in mock_session_state
            state = mock_session_state['advanced_intelligence_state']

            assert 'active_lead_journeys' in state
            assert 'sentiment_history' in state
            assert 'competitive_data' in state
            assert 'content_recommendations' in state

    @patch('streamlit.markdown')
    @patch('streamlit.plotly_chart')
    @patch('streamlit.columns')
    def test_lead_journey_rendering(self, mock_columns, mock_plotly, mock_markdown):
        """Test advanced lead journey map rendering."""
        # Setup test data
        journey_stages = generate_sample_journey_stages()

        # Mock streamlit components - return 3 mock columns each time
        mock_columns.return_value = [Mock(), Mock(), Mock()]

        # Test rendering doesn't raise exceptions
        try:
            with patch('streamlit_components.advanced_intelligence_visualizations.ENTERPRISE_THEME_AVAILABLE', False):
                self.viz.render_advanced_lead_journey_map(
                    lead_id="TEST_LEAD_001",
                    lead_name="Test Lead",
                    journey_stages=journey_stages,
                    real_time_updates=True
                )

            # Verify streamlit components were called
            assert mock_markdown.called

        except Exception as e:
            pytest.fail(f"Lead journey rendering failed: {e}")

    @patch('streamlit.markdown')
    @patch('streamlit.plotly_chart')
    @patch('streamlit.columns')
    @patch('streamlit.info')
    @patch('streamlit.success')
    @patch('streamlit.warning')
    def test_sentiment_dashboard_rendering(self, mock_warning, mock_success, mock_info, mock_columns, mock_plotly, mock_markdown):
        """Test real-time sentiment analysis dashboard rendering."""
        # Setup test data
        sentiment_data = generate_sample_sentiment_data()

        # Mock streamlit components
        mock_columns.return_value = [Mock(), Mock(), Mock(), Mock()]

        # Test rendering doesn't raise exceptions
        try:
            with patch('streamlit_components.advanced_intelligence_visualizations.ENTERPRISE_THEME_AVAILABLE', False):
                self.viz.render_realtime_sentiment_dashboard(
                    sentiment_data=sentiment_data,
                    current_conversation="Test conversation"
                )

            # Verify streamlit components were called
            assert mock_markdown.called

        except Exception as e:
            pytest.fail(f"Sentiment dashboard rendering failed: {e}")

    @patch('streamlit.markdown')
    @patch('streamlit.plotly_chart')
    @patch('streamlit.columns')
    def test_competitive_intelligence_rendering(self, mock_columns, mock_plotly, mock_markdown):
        """Test competitive intelligence dashboard rendering."""
        # Setup test data
        competitive_data = generate_sample_competitive_data()

        # Mock streamlit components
        mock_columns.return_value = [Mock(), Mock(), Mock(), Mock()]

        # Test rendering doesn't raise exceptions
        try:
            with patch('streamlit_components.advanced_intelligence_visualizations.ENTERPRISE_THEME_AVAILABLE', False):
                self.viz.render_competitive_intelligence_dashboard(
                    competitive_data=competitive_data,
                    market_trends=None
                )

            # Verify streamlit components were called
            assert mock_markdown.called

        except Exception as e:
            pytest.fail(f"Competitive intelligence rendering failed: {e}")

    @patch('streamlit.markdown')
    @patch('streamlit.plotly_chart')
    @patch('streamlit.columns')
    def test_content_engine_rendering(self, mock_columns, mock_plotly, mock_markdown):
        """Test intelligent content recommendation engine rendering."""
        # Setup test data
        lead_profile = {
            "age_range": "25-35",
            "interests": ["Modern design", "Urban living"],
            "communication_style": "Direct"
        }
        content_recommendations = generate_sample_content_recommendations()

        # Mock streamlit components
        mock_columns.return_value = [Mock(), Mock(), Mock(), Mock()]

        # Test rendering doesn't raise exceptions
        try:
            with patch('streamlit_components.advanced_intelligence_visualizations.ENTERPRISE_THEME_AVAILABLE', False):
                self.viz.render_intelligent_content_engine(
                    lead_profile=lead_profile,
                    content_recommendations=content_recommendations
                )

            # Verify streamlit components were called
            assert mock_markdown.called

        except Exception as e:
            pytest.fail(f"Content engine rendering failed: {e}")

    def test_sentiment_insights_generation(self):
        """Test AI insights generation from sentiment data."""
        # Create test sentiment data with specific patterns
        sentiment_data = [
            SentimentAnalysis(
                timestamp=datetime.now() - timedelta(minutes=10),
                overall_sentiment=-0.6,  # Negative
                emotion_breakdown={"Joy": 0.1, "Fear": 0.7, "Sadness": 0.5},
                voice_tone="Frustrated",
                confidence=0.9,
                engagement_level=0.3,  # Low engagement
                communication_style="Emotional",
                recommended_response="Use empathetic approach"
            ),
            SentimentAnalysis(
                timestamp=datetime.now() - timedelta(minutes=5),
                overall_sentiment=-0.2,  # Slightly negative
                emotion_breakdown={"Joy": 0.3, "Fear": 0.4, "Trust": 0.6},
                voice_tone="Concerned",
                confidence=0.85,
                engagement_level=0.6,
                communication_style="Questioning",
                recommended_response="Address concerns directly"
            ),
            SentimentAnalysis(
                timestamp=datetime.now(),
                overall_sentiment=0.4,  # Positive trend
                emotion_breakdown={"Joy": 0.7, "Trust": 0.8, "Anticipation": 0.6},
                voice_tone="Friendly",
                confidence=0.9,
                engagement_level=0.8,
                communication_style="Direct",
                recommended_response="Continue positive momentum"
            )
        ]

        insights = self.viz._generate_sentiment_insights(sentiment_data)

        # Should generate insights based on patterns
        assert isinstance(insights, list)
        assert len(insights) > 0

        # Check for expected insight types
        insight_types = [insight['type'] for insight in insights]
        assert 'success' in insight_types  # Positive trend detected

        # Validate insight structure
        for insight in insights:
            assert 'type' in insight
            assert 'title' in insight
            assert 'message' in insight
            assert insight['type'] in ['warning', 'success', 'info']


class TestDataModels:
    """Test suite for data model classes."""

    def test_lead_journey_stage_model(self):
        """Test LeadJourneyStage data model."""
        stage = LeadJourneyStage(
            stage_name="Initial Contact",
            stage_order=1,
            entry_time=datetime.now(),
            predicted_exit_time=datetime.now() + timedelta(days=1),
            conversion_probability=0.75,
            risk_factors=["Cold lead", "No prior relationship"],
            opportunities=["High intent", "Budget qualified"],
            claude_insights=["Strong interest signals", "Timeline urgency"],
            recommended_actions=["Send market overview", "Schedule call"]
        )

        assert stage.stage_name == "Initial Contact"
        assert stage.stage_order == 1
        assert 0.0 <= stage.conversion_probability <= 1.0
        assert isinstance(stage.risk_factors, list)
        assert isinstance(stage.opportunities, list)
        assert isinstance(stage.claude_insights, list)
        assert isinstance(stage.recommended_actions, list)

    def test_sentiment_analysis_model(self):
        """Test SentimentAnalysis data model."""
        sentiment = SentimentAnalysis(
            timestamp=datetime.now(),
            overall_sentiment=0.5,
            emotion_breakdown={"Joy": 0.7, "Trust": 0.8, "Fear": 0.2},
            voice_tone="Friendly",
            confidence=0.85,
            engagement_level=0.9,
            communication_style="Direct",
            recommended_response="Continue current approach"
        )

        assert -1.0 <= sentiment.overall_sentiment <= 1.0
        assert isinstance(sentiment.emotion_breakdown, dict)
        assert 0.0 <= sentiment.confidence <= 1.0
        assert 0.0 <= sentiment.engagement_level <= 1.0
        assert isinstance(sentiment.voice_tone, str)

    def test_competitive_intelligence_model(self):
        """Test CompetitiveIntelligence data model."""
        competitive_data = CompetitiveIntelligence(
            market_segment="Luxury Real Estate",
            competitive_position="Leader",
            market_share=0.25,
            key_differentiators=["AI technology", "Premium service"],
            competitive_threats=["New entrants", "Price competition"],
            market_opportunities=["Tech adoption", "Market expansion"],
            pricing_position="Premium",
            recommendation="Leverage AI as key differentiator"
        )

        assert competitive_data.market_segment == "Luxury Real Estate"
        assert competitive_data.competitive_position in ["Leader", "Challenger", "Follower", "Niche"]
        assert 0.0 <= competitive_data.market_share <= 1.0
        assert isinstance(competitive_data.key_differentiators, list)

    def test_content_recommendation_model(self):
        """Test ContentRecommendation data model."""
        content = ContentRecommendation(
            content_type="market_report",
            title="Q1 Market Analysis",
            relevance_score=0.85,
            predicted_engagement=0.78,
            optimal_timing="Tuesday 10:00 AM",
            delivery_channel="Email",
            personalization_notes=["Focus on buyer preferences", "Include local data"],
            claude_rationale="High relevance based on lead profile and interests"
        )

        assert content.content_type in ["listing", "market_report", "educational", "proposal"]
        assert 0.0 <= content.relevance_score <= 1.0
        assert 0.0 <= content.predicted_engagement <= 1.0
        assert isinstance(content.personalization_notes, list)


class TestSampleDataGenerators:
    """Test suite for sample data generation functions."""

    def test_generate_sample_journey_stages(self):
        """Test journey stages sample data generation."""
        stages = generate_sample_journey_stages()

        assert isinstance(stages, list)
        assert len(stages) > 0

        for stage in stages:
            assert isinstance(stage, LeadJourneyStage)
            assert stage.stage_order >= 1
            assert 0.0 <= stage.conversion_probability <= 1.0
            assert isinstance(stage.entry_time, datetime)

    def test_generate_sample_sentiment_data(self):
        """Test sentiment data sample generation."""
        sentiment_data = generate_sample_sentiment_data()

        assert isinstance(sentiment_data, list)
        assert len(sentiment_data) > 0

        for sentiment in sentiment_data:
            assert isinstance(sentiment, SentimentAnalysis)
            assert -1.0 <= sentiment.overall_sentiment <= 1.0
            assert 0.0 <= sentiment.confidence <= 1.0
            assert 0.0 <= sentiment.engagement_level <= 1.0

    def test_generate_sample_competitive_data(self):
        """Test competitive intelligence sample data generation."""
        competitive_data = generate_sample_competitive_data()

        assert isinstance(competitive_data, CompetitiveIntelligence)
        assert competitive_data.market_segment
        assert competitive_data.competitive_position in ["Leader", "Challenger", "Follower", "Niche"]
        assert 0.0 <= competitive_data.market_share <= 1.0
        assert len(competitive_data.key_differentiators) > 0

    def test_generate_sample_content_recommendations(self):
        """Test content recommendations sample data generation."""
        content_recommendations = generate_sample_content_recommendations()

        assert isinstance(content_recommendations, list)
        assert len(content_recommendations) > 0

        for content in content_recommendations:
            assert isinstance(content, ContentRecommendation)
            assert content.content_type
            assert 0.0 <= content.relevance_score <= 1.0
            assert 0.0 <= content.predicted_engagement <= 1.0


class TestFactoryFunctions:
    """Test suite for factory and utility functions."""

    def test_create_advanced_visualizations(self):
        """Test advanced visualizations factory function."""
        viz = create_advanced_visualizations()

        assert isinstance(viz, AdvancedIntelligenceVisualizations)
        assert hasattr(viz, 'colors')
        assert hasattr(viz, 'render_advanced_lead_journey_map')
        assert hasattr(viz, 'render_realtime_sentiment_dashboard')
        assert hasattr(viz, 'render_competitive_intelligence_dashboard')
        assert hasattr(viz, 'render_intelligent_content_engine')


class TestIntegrationScenarios:
    """Integration tests for real-world usage scenarios."""

    def setup_method(self):
        """Set up test fixtures for integration tests."""
        self.viz = create_advanced_visualizations()

    @patch('streamlit.markdown')
    @patch('streamlit.plotly_chart')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    @patch('streamlit.info')
    @patch('streamlit.success')
    @patch('streamlit.warning')
    def test_complete_dashboard_workflow(self, mock_warning, mock_success, mock_info, mock_metric, mock_columns, mock_plotly, mock_markdown):
        """Test complete dashboard workflow with all components."""
        # Mock streamlit components - always return 3 columns for consistency
        mock_columns.return_value = [Mock(), Mock(), Mock()]

        # Disable enterprise theme for testing
        with patch('streamlit_components.advanced_intelligence_visualizations.ENTERPRISE_THEME_AVAILABLE', False):
            try:
                # Test journey mapping
                journey_stages = generate_sample_journey_stages()
                self.viz.render_advanced_lead_journey_map(
                    lead_id="INTEGRATION_TEST_001",
                    lead_name="Integration Test Lead",
                    journey_stages=journey_stages
                )

                # Test sentiment analysis
                sentiment_data = generate_sample_sentiment_data()
                self.viz.render_realtime_sentiment_dashboard(sentiment_data)

                # Test competitive intelligence
                competitive_data = generate_sample_competitive_data()
                self.viz.render_competitive_intelligence_dashboard(competitive_data)

                # Test content engine
                content_recommendations = generate_sample_content_recommendations()
                self.viz.render_intelligent_content_engine(
                    lead_profile={"test": "profile"},
                    content_recommendations=content_recommendations
                )

                # Verify components were called
                assert mock_markdown.called

            except Exception as e:
                pytest.fail(f"Complete dashboard workflow failed: {e}")

    def test_data_consistency_across_components(self):
        """Test data consistency when shared across components."""
        # Generate related data sets
        journey_stages = generate_sample_journey_stages()
        sentiment_data = generate_sample_sentiment_data()
        competitive_data = generate_sample_competitive_data()
        content_recommendations = generate_sample_content_recommendations()

        # Verify data relationships and consistency
        assert len(journey_stages) > 0
        assert len(sentiment_data) > 0
        assert len(content_recommendations) > 0

        # Test that data can be cross-referenced
        lead_conversion_prob = journey_stages[-1].conversion_probability
        content_relevance_avg = sum(c.relevance_score for c in content_recommendations) / len(content_recommendations)

        # Basic relationship validation
        assert 0.0 <= lead_conversion_prob <= 1.0
        assert 0.0 <= content_relevance_avg <= 1.0

    def test_performance_with_large_datasets(self):
        """Test performance with larger datasets."""
        # Generate larger datasets
        large_sentiment_data = []
        for i in range(100):
            sentiment = SentimentAnalysis(
                timestamp=datetime.now() - timedelta(minutes=i),
                overall_sentiment=np.random.uniform(-0.5, 0.8),
                emotion_breakdown={
                    "Joy": np.random.uniform(0, 1),
                    "Trust": np.random.uniform(0, 1),
                    "Fear": np.random.uniform(0, 0.5)
                },
                voice_tone="Professional",
                confidence=np.random.uniform(0.8, 0.95),
                engagement_level=np.random.uniform(0.4, 0.9),
                communication_style="Direct",
                recommended_response="Test response"
            )
            large_sentiment_data.append(sentiment)

        # Test insights generation with large dataset
        insights = self.viz._generate_sentiment_insights(large_sentiment_data)

        assert isinstance(insights, list)
        # Should handle large datasets without performance issues


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])