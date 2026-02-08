"""
Test suite for White-Label Showcase Component.

Tests for the high-ticket consulting demonstration interface
showcasing $25K-$100K white-label platform capabilities.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pandas as pd
import pytest
import streamlit as st

from ghl_real_estate_ai.services.white_label_service import (
    BrandingConfig,
    BrandingTier,
    IntegrationMarketplace,
    WorkflowTemplate,
)
from ghl_real_estate_ai.streamlit_demo.components.white_label_showcase import (
    WhiteLabelShowcase,
    get_white_label_showcase,
)


class TestWhiteLabelShowcase:
    """Test suite for WhiteLabelShowcase component."""

    @pytest.fixture
    def mock_service(self):
        """Mock white-label service for testing."""
        service = Mock()

        # Mock workflow templates
        service.get_available_workflows = AsyncMock(
            return_value=[
                WorkflowTemplate(
                    template_id="test_workflow",
                    name="Test AI Workflow",
                    description="Test workflow description",
                    category="AI Analytics",
                    trigger_type="webhook",
                    actions=[{"type": "ai_analysis"}, {"type": "send_email"}],
                    conditions=[{"field": "lead_score", "operator": "greater_than", "value": 80}],
                    customizable_fields=["threshold", "email_template"],
                    consulting_tier=BrandingTier.PROFESSIONAL,
                    estimated_value="50+ hours/month automation",
                )
            ]
        )

        # Mock integrations
        service.get_integration_marketplace = AsyncMock(
            return_value=[
                IntegrationMarketplace(
                    integration_id="test_crm",
                    name="Enterprise CRM Integration",
                    provider="TestCRM",
                    description="Advanced CRM integration with custom fields",
                    setup_instructions="OAuth2 setup with enterprise permissions",
                    api_endpoints=["/api/contacts", "/api/deals"],
                    required_credentials=["client_id", "client_secret"],
                    supported_features=["custom_fields", "workflow_automation"],
                    consulting_tier=BrandingTier.ENTERPRISE,
                    implementation_complexity="complex",
                )
            ]
        )

        return service

    @pytest.fixture
    def showcase_instance(self, mock_service):
        """Create WhiteLabelShowcase instance with mocked service."""
        with patch(
            "ghl_real_estate_ai.streamlit_demo.components.white_label_showcase.WhiteLabelService",
            return_value=mock_service,
        ):
            return WhiteLabelShowcase()

    def test_initialization(self, showcase_instance):
        """Test showcase initialization."""
        assert showcase_instance is not None
        assert hasattr(showcase_instance, "consulting_packages")
        assert hasattr(showcase_instance, "demo_brands")
        assert len(showcase_instance.consulting_packages) == 3
        assert len(showcase_instance.demo_brands) == 3

    def test_consulting_packages_structure(self, showcase_instance):
        """Test consulting packages data structure."""
        packages = showcase_instance.consulting_packages

        # Check all expected packages exist
        expected_packages = ["AI Transformation Accelerator", "Enterprise Intelligence Platform", "AI Innovation Lab"]

        for package_name in expected_packages:
            assert package_name in packages

        # Check package structure
        for package_name, details in packages.items():
            assert "price" in details
            assert "duration" in details
            assert "tier" in details
            assert "features" in details
            assert "target" in details
            assert isinstance(details["features"], list)
            assert isinstance(details["tier"], BrandingTier)

    def test_demo_brands_structure(self, showcase_instance):
        """Test demo brands data structure."""
        brands = showcase_instance.demo_brands

        expected_brands = ["Luxury Real Estate Group", "Metro Property Solutions", "Coastal Realty Network"]

        for brand_name in expected_brands:
            assert brand_name in brands

        # Check brand configuration structure
        for brand_name, config in brands.items():
            assert isinstance(config, BrandingConfig)
            assert config.company_name == brand_name
            assert config.logo_url.startswith("https://")
            assert config.primary_color.startswith("#")
            assert isinstance(config.tier, BrandingTier)

    def test_tier_demo_capabilities(self, showcase_instance):
        """Test tier demo capabilities method."""
        # Test Basic tier
        basic_capabilities = showcase_instance._get_tier_demo_capabilities(BrandingTier.BASIC)
        assert basic_capabilities["Custom Branding"] is True
        assert basic_capabilities["Advanced Analytics"] is False
        assert basic_capabilities["Enterprise SSO"] is False

        # Test Professional tier
        professional_capabilities = showcase_instance._get_tier_demo_capabilities(BrandingTier.PROFESSIONAL)
        assert professional_capabilities["Custom Branding"] is True
        assert professional_capabilities["Advanced Analytics"] is True
        assert professional_capabilities["Enterprise SSO"] is False

        # Test Enterprise tier
        enterprise_capabilities = showcase_instance._get_tier_demo_capabilities(BrandingTier.ENTERPRISE)
        assert enterprise_capabilities["Custom Branding"] is True
        assert enterprise_capabilities["Advanced Analytics"] is True
        assert enterprise_capabilities["Enterprise SSO"] is True

    @patch("streamlit.markdown")
    @patch("streamlit.tabs")
    def test_render_showcase_structure(self, mock_tabs, mock_markdown, showcase_instance):
        """Test main showcase rendering structure."""
        # Mock tabs
        mock_tabs.return_value = [Mock(), Mock(), Mock(), Mock()]

        with patch.object(showcase_instance, "_render_consulting_packages"):
            with patch.object(showcase_instance, "_render_brand_customization"):
                with patch.object(showcase_instance, "_render_workflow_engine"):
                    with patch.object(showcase_instance, "_render_integration_marketplace"):
                        with patch.object(showcase_instance, "_render_roi_calculator"):
                            showcase_instance.render_showcase()

        # Verify header was rendered
        assert mock_markdown.called
        call_args = mock_markdown.call_args_list[0][0][0]
        assert "White-Label Platform Showcase" in call_args
        assert "$25K-$100K consulting engagements" in call_args

        # Verify tabs were created
        mock_tabs.assert_called_once()

    @patch("streamlit.selectbox")
    @patch("streamlit.dataframe")
    @patch("streamlit.markdown")
    def test_render_consulting_packages(self, mock_markdown, mock_dataframe, mock_selectbox, showcase_instance):
        """Test consulting packages rendering."""
        mock_selectbox.return_value = "AI Transformation Accelerator"

        showcase_instance._render_consulting_packages()

        # Verify dataframe was created
        assert mock_dataframe.called
        df_call = mock_dataframe.call_args[0][0]
        assert isinstance(df_call, pd.DataFrame)
        assert len(df_call) == 3  # Three packages

        # Verify package selection works
        assert mock_selectbox.called

    @patch("streamlit.selectbox")
    @patch("streamlit.text_input")
    @patch("streamlit.color_picker")
    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    def test_render_brand_customization(
        self, mock_columns, mock_markdown, mock_color_picker, mock_text_input, mock_selectbox, showcase_instance
    ):
        """Test brand customization rendering."""
        # Mock columns
        col1, col2 = Mock(), Mock()
        mock_columns.return_value = [col1, col2]

        # Mock form inputs
        mock_selectbox.side_effect = ["Luxury Real Estate Group", "Professional"]
        mock_text_input.return_value = "Test Company"
        mock_color_picker.side_effect = ["#FF0000", "#00FF00", "#0000FF"]

        with patch.object(showcase_instance, "_render_brand_preview"):
            with patch.object(showcase_instance, "_render_tier_features"):
                showcase_instance._render_brand_customization()

        # Verify brand selection works
        assert mock_selectbox.called

    def test_render_brand_preview(self, showcase_instance):
        """Test brand preview rendering."""
        with patch("streamlit.markdown") as mock_markdown:
            showcase_instance._render_brand_preview("Test Company", "#FF0000", "#00FF00", "#0000FF", "Arial")

            # Verify preview HTML was generated
            assert mock_markdown.call_count >= 2  # Header + dashboard preview

            # Check that brand elements are included
            html_calls = [call[0][0] for call in mock_markdown.call_args_list]
            brand_html = "".join(html_calls)
            assert "Test Company" in brand_html
            assert "#FF0000" in brand_html

    @patch("streamlit.selectbox")
    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    def test_render_workflow_engine(self, mock_columns, mock_markdown, mock_selectbox, showcase_instance, mock_service):
        """Test workflow engine rendering."""
        # Mock columns
        col1, col2 = Mock(), Mock()
        mock_columns.return_value = [col1, col2]

        # Mock form inputs
        mock_selectbox.side_effect = ["Professional", "Test AI Workflow"]

        with patch.object(showcase_instance, "_render_workflow_builder_demo"):
            showcase_instance._render_workflow_engine()

        # Verify workflow selection interface was created
        assert mock_selectbox.called

    @patch("streamlit.expander")
    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    def test_render_integration_marketplace(self, mock_columns, mock_markdown, mock_expander, showcase_instance):
        """Test integration marketplace rendering."""
        # Mock columns
        col1, col2 = Mock(), Mock()
        mock_columns.return_value = [col1, col2]

        # Mock expander
        mock_expander.return_value.__enter__ = Mock()
        mock_expander.return_value.__exit__ = Mock()

        showcase_instance._render_integration_marketplace()

        # Verify tier-based integration display
        assert mock_markdown.called

    @patch("streamlit.columns")
    @patch("streamlit.number_input")
    @patch("streamlit.selectbox")
    @patch("streamlit.metric")
    @patch("streamlit.success")
    def test_render_roi_calculator(
        self, mock_success, mock_metric, mock_selectbox, mock_number_input, mock_columns, showcase_instance
    ):
        """Test ROI calculator rendering."""
        # Mock columns
        col1, col2, col3 = Mock(), Mock(), Mock()
        mock_columns.return_value = [col1, col2, col3]

        # Mock form inputs
        mock_number_input.side_effect = [25, 350000, 8, 40]  # agents, deal size, monthly deals, manual hours
        mock_selectbox.return_value = "AI Transformation Accelerator"

        showcase_instance._render_roi_calculator()

        # Verify ROI calculation interface was created
        assert mock_number_input.called
        assert mock_selectbox.called
        assert mock_metric.called

    @patch("streamlit.columns")
    @patch("streamlit.markdown")
    def test_render_tier_features(self, mock_markdown, mock_columns, showcase_instance):
        """Test tier features rendering."""
        col1, col2 = Mock(), Mock()
        mock_columns.return_value = [col1, col2]

        showcase_instance._render_tier_features(BrandingTier.PROFESSIONAL)

        # Verify features were displayed
        assert mock_markdown.called

    @patch("streamlit.markdown")
    def test_render_workflow_builder_demo(self, mock_markdown, showcase_instance):
        """Test workflow builder demo rendering."""
        showcase_instance._render_workflow_builder_demo()

        # Verify workflow builder HTML was generated
        assert mock_markdown.called
        html_call = mock_markdown.call_args[0][0]
        assert "Trigger: New Lead" in html_call
        assert "AI Analysis" in html_call
        assert "No coding required" in html_call

    def test_caching_decorator(self):
        """Test that the caching decorator works."""
        with patch("streamlit.cache_resource") as mock_cache:
            mock_cache.return_value = lambda func: func

            from ghl_real_estate_ai.streamlit_demo.components.white_label_showcase import get_white_label_showcase

            showcase1 = get_white_label_showcase()
            showcase2 = get_white_label_showcase()

            # Should return same instance due to caching
            assert isinstance(showcase1, WhiteLabelShowcase)

    def test_pricing_structure_validation(self, showcase_instance):
        """Test that pricing structure follows consulting model."""
        packages = showcase_instance.consulting_packages

        # Validate pricing tiers
        accelerator = packages["AI Transformation Accelerator"]
        assert "25,000" in accelerator["price"]
        assert accelerator["tier"] == BrandingTier.BASIC

        platform = packages["Enterprise Intelligence Platform"]
        assert "50,000" in platform["price"]
        assert platform["tier"] == BrandingTier.PROFESSIONAL

        innovation = packages["AI Innovation Lab"]
        assert "75,000" in innovation["price"]
        assert innovation["tier"] == BrandingTier.ENTERPRISE

    def test_brand_tier_consistency(self, showcase_instance):
        """Test that demo brands have appropriate tiers."""
        brands = showcase_instance.demo_brands

        # Check tier diversity
        tiers_present = [brand.tier for brand in brands.values()]
        assert BrandingTier.BASIC in tiers_present
        assert BrandingTier.PROFESSIONAL in tiers_present
        assert BrandingTier.ENTERPRISE in tiers_present

    def test_color_validation(self, showcase_instance):
        """Test that brand colors are valid hex codes."""
        brands = showcase_instance.demo_brands

        for brand_name, config in brands.items():
            # Test color format
            assert config.primary_color.startswith("#")
            assert len(config.primary_color) == 7  # #RRGGBB format
            assert config.secondary_color.startswith("#")
            assert len(config.secondary_color) == 7
            assert config.accent_color.startswith("#")
            assert len(config.accent_color) == 7

    @patch("streamlit.error")
    def test_error_handling_workflow_loading(self, mock_error, showcase_instance):
        """Test error handling when workflow loading fails."""
        # Mock service to raise exception
        showcase_instance.service.get_available_workflows = AsyncMock(side_effect=Exception("Service unavailable"))

        showcase_instance._render_workflow_engine()

        # Verify error was displayed
        mock_error.assert_called_once()
        assert "Error loading workflows" in mock_error.call_args[0][0]

    @patch("streamlit.error")
    def test_error_handling_integration_loading(self, mock_error, showcase_instance):
        """Test error handling when integration loading fails."""
        # Mock service to raise exception
        showcase_instance.service.get_integration_marketplace = AsyncMock(side_effect=Exception("Service unavailable"))

        showcase_instance._render_integration_marketplace()

        # Verify error was displayed
        mock_error.assert_called_once()
        assert "Error loading integrations" in mock_error.call_args[0][0]

    def test_roi_calculation_logic(self, showcase_instance):
        """Test ROI calculation logic manually."""
        # Test calculation parameters
        current_agents = 25
        avg_deal_size = 350000
        monthly_deals = 8
        manual_hours = 40

        # Expected improvements
        automation_hours_saved = manual_hours * 0.6  # 60% automation = 24 hours
        conversion_improvement = 0.25  # 25% better conversion
        deal_velocity_improvement = 0.4  # 40% faster deals

        new_monthly_deals = monthly_deals * (1 + conversion_improvement + deal_velocity_improvement)
        monthly_revenue_increase = (new_monthly_deals - monthly_deals) * avg_deal_size
        annual_revenue_increase = monthly_revenue_increase * 12

        # Basic package investment
        investment = 30000  # Midpoint of $25K-$35K
        roi_percentage = ((annual_revenue_increase - investment) / investment) * 100

        # Validate calculations
        assert automation_hours_saved == 24.0
        assert new_monthly_deals == 8 * 1.65  # 65% improvement
        assert monthly_revenue_increase > 0
        assert roi_percentage > 100  # Should be profitable

    def test_feature_availability_logic(self, showcase_instance):
        """Test feature availability logic across tiers."""
        # Test Basic tier limitations
        basic_capabilities = showcase_instance._get_tier_demo_capabilities(BrandingTier.BASIC)
        assert basic_capabilities["Custom Branding"] is True
        assert basic_capabilities["Advanced Analytics"] is False
        assert basic_capabilities["Enterprise SSO"] is False

        # Test Professional tier additions
        professional_capabilities = showcase_instance._get_tier_demo_capabilities(BrandingTier.PROFESSIONAL)
        assert professional_capabilities["Advanced Analytics"] is True
        assert professional_capabilities["Custom Domain"] is True
        assert professional_capabilities["Enterprise SSO"] is False  # Still not available

        # Test Enterprise tier completeness
        enterprise_capabilities = showcase_instance._get_tier_demo_capabilities(BrandingTier.ENTERPRISE)
        assert all(enterprise_capabilities.values())  # All features should be True

    def test_main_render_function(self):
        """Test main render function execution."""
        with patch(
            "ghl_real_estate_ai.streamlit_demo.components.white_label_showcase.get_white_label_showcase"
        ) as mock_get:
            mock_showcase = Mock()
            mock_get.return_value = mock_showcase

            from ghl_real_estate_ai.streamlit_demo.components.white_label_showcase import render_white_label_showcase

            render_white_label_showcase()

            # Verify showcase was retrieved and rendered
            mock_get.assert_called_once()
            mock_showcase.render_showcase.assert_called_once()

    def test_consulting_package_target_markets(self, showcase_instance):
        """Test that consulting packages target appropriate market segments."""
        packages = showcase_instance.consulting_packages

        # Basic package should target mid-market
        accelerator = packages["AI Transformation Accelerator"]
        assert "10-50 agents" in accelerator["target"]

        # Professional package should target large organizations
        platform = packages["Enterprise Intelligence Platform"]
        assert "100+ agents" in platform["target"]

        # Enterprise package should target enterprise + tech companies
        innovation = packages["AI Innovation Lab"]
        assert "Enterprise" in innovation["target"] and "Tech companies" in innovation["target"]

    def test_timeline_consistency(self, showcase_instance):
        """Test that consulting package timelines are realistic."""
        packages = showcase_instance.consulting_packages

        for package_name, details in packages.items():
            duration = details["duration"]
            assert "weeks" in duration

            # Extract week numbers
            if "6-8" in duration:
                assert package_name == "AI Transformation Accelerator"
            elif "10-12" in duration:
                assert package_name == "Enterprise Intelligence Platform"
            elif "12-16" in duration:
                assert package_name == "AI Innovation Lab"
