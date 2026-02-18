import pytest
pytestmark = pytest.mark.integration

"""
Test suite for White-Label Service.

Comprehensive testing for enterprise white-label capabilities
supporting $25K-$100K consulting engagements.
"""

import asyncio
import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ghl_real_estate_ai.services.white_label_service import (

    BrandingConfig,
    BrandingTier,
    IntegrationMarketplace,
    WhiteLabelService,
    WorkflowTemplate,
)


class TestWhiteLabelService:
    """Test suite for WhiteLabelService."""

    @pytest.fixture
    def temp_service(self):
        """Create service with temporary storage for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = WhiteLabelService()
            # Override directories to use temp directory
            service.brands_dir = Path(temp_dir) / "brands"
            service.templates_dir = Path(temp_dir) / "templates"
            service.integrations_dir = Path(temp_dir) / "integrations"

            # Create directories
            service.brands_dir.mkdir(parents=True, exist_ok=True)
            service.templates_dir.mkdir(parents=True, exist_ok=True)
            service.integrations_dir.mkdir(parents=True, exist_ok=True)

            # Re-initialize enterprise assets into the temp directories
            service._initialize_enterprise_assets()

            yield service

    @pytest.fixture
    def sample_branding_config(self):
        """Sample branding configuration for testing."""
        return BrandingConfig(
            company_name="Test Company",
            logo_url="https://example.com/logo.png",
            primary_color="#6D28D9",
            secondary_color="#4C1D95",
            accent_color="#10B981",
            tier=BrandingTier.PROFESSIONAL,
        )

    @pytest.fixture
    def sample_workflow_template(self):
        """Sample workflow template for testing."""
        return WorkflowTemplate(
            template_id="test_workflow",
            name="Test Workflow",
            description="Test workflow for demonstration",
            category="Test",
            trigger_type="webhook",
            actions=[{"type": "test_action", "parameters": {"param1": "value1"}}],
            conditions=[{"field": "test_field", "operator": "equals", "value": "test_value"}],
            customizable_fields=["param1"],
            consulting_tier=BrandingTier.BASIC,
            estimated_value="Test value",
        )

    @pytest.mark.asyncio
    async def test_create_brand_config(self, temp_service, sample_branding_config):
        """Test brand configuration creation."""
        tenant_id = "test_tenant_123"

        brand_id = await temp_service.create_brand_config(tenant_id, sample_branding_config)

        assert brand_id.startswith("brand_test_tenant_123_")
        assert len(brand_id) > 20  # Should include timestamp

        # Verify file was created
        brand_files = list(temp_service.brands_dir.glob(f"{brand_id}.json"))
        assert len(brand_files) == 1

        # Verify content
        with open(brand_files[0], "r") as f:
            saved_data = json.load(f)

        assert saved_data["brand_id"] == brand_id
        assert saved_data["tenant_id"] == tenant_id
        assert saved_data["config"]["company_name"] == "Test Company"
        assert saved_data["config"]["tier"] == "professional"

    @pytest.mark.asyncio
    async def test_get_brand_config(self, temp_service, sample_branding_config):
        """Test brand configuration retrieval."""
        tenant_id = "test_tenant_123"

        # Create brand first
        brand_id = await temp_service.create_brand_config(tenant_id, sample_branding_config)

        # Retrieve brand
        retrieved_config = await temp_service.get_brand_config(brand_id)

        assert retrieved_config is not None
        assert retrieved_config.company_name == "Test Company"
        assert retrieved_config.tier == BrandingTier.PROFESSIONAL
        assert retrieved_config.primary_color == "#6D28D9"

    @pytest.mark.asyncio
    async def test_get_nonexistent_brand_config(self, temp_service):
        """Test retrieval of non-existent brand configuration."""
        result = await temp_service.get_brand_config("nonexistent_brand")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_brand_config(self, temp_service, sample_branding_config):
        """Test brand configuration update."""
        tenant_id = "test_tenant_123"

        # Create brand first
        brand_id = await temp_service.create_brand_config(tenant_id, sample_branding_config)

        # Update brand
        updates = {"company_name": "Updated Company Name", "primary_color": "#FF0000"}

        success = await temp_service.update_brand_config(brand_id, updates)
        assert success is True

        # Verify updates
        updated_config = await temp_service.get_brand_config(brand_id)
        assert updated_config.company_name == "Updated Company Name"
        assert updated_config.primary_color == "#FF0000"

    @pytest.mark.asyncio
    async def test_update_nonexistent_brand(self, temp_service):
        """Test updating non-existent brand configuration."""
        success = await temp_service.update_brand_config("nonexistent", {"company_name": "Test"})
        assert success is False

    @pytest.mark.asyncio
    async def test_branding_tier_validation_basic(self, temp_service):
        """Test branding tier validation for Basic tier."""
        config = BrandingConfig(
            company_name="Test Company",
            logo_url="https://example.com/logo.png",
            tier=BrandingTier.BASIC,
            custom_css="body { background: red; }",  # Not allowed in Basic
            custom_domain="test.com",  # Not allowed in Basic
        )

        with pytest.raises(ValueError, match="Custom CSS not available in Basic tier"):
            await temp_service.create_brand_config("tenant_123", config)

    @pytest.mark.asyncio
    async def test_branding_tier_validation_professional(self, temp_service):
        """Test branding tier validation for Professional tier."""
        large_css = "body { background: red; }" * 500  # > 5KB
        config = BrandingConfig(
            company_name="Test Company",
            logo_url="https://example.com/logo.png",
            tier=BrandingTier.PROFESSIONAL,
            custom_css=large_css,  # Too large for Professional
        )

        with pytest.raises(ValueError, match="Custom CSS limited to 5KB in Professional tier"):
            await temp_service.create_brand_config("tenant_123", config)

    @pytest.mark.asyncio
    async def test_branding_tier_validation_enterprise(self, temp_service):
        """Test branding tier validation for Enterprise tier (no restrictions)."""
        large_css = "body { background: red; }" * 1000  # > 5KB but allowed in Enterprise
        config = BrandingConfig(
            company_name="Test Company",
            logo_url="https://example.com/logo.png",
            tier=BrandingTier.ENTERPRISE,
            custom_css=large_css,
            custom_domain="enterprise.com",
        )

        # Should not raise any validation errors
        brand_id = await temp_service.create_brand_config("tenant_123", config)
        assert brand_id is not None

    def test_save_workflow_template(self, temp_service, sample_workflow_template):
        """Test workflow template saving."""
        temp_service._save_workflow_template(sample_workflow_template)

        template_file = temp_service.templates_dir / "workflow_test_workflow.json"
        assert template_file.exists()

        with open(template_file, "r") as f:
            saved_template = json.load(f)

        assert saved_template["template_id"] == "test_workflow"
        assert saved_template["name"] == "Test Workflow"
        assert saved_template["consulting_tier"] == "basic"

    @pytest.mark.asyncio
    async def test_get_available_workflows_by_tier(self, temp_service, sample_workflow_template):
        """Test workflow retrieval by consulting tier."""
        # Save sample template
        temp_service._save_workflow_template(sample_workflow_template)

        # Test Basic tier (should include Basic workflows)
        basic_workflows = await temp_service.get_available_workflows(BrandingTier.BASIC)
        assert len(basic_workflows) >= 1
        assert any(w.template_id == "test_workflow" for w in basic_workflows)

        # Test Professional tier (should include Basic + Professional)
        professional_workflows = await temp_service.get_available_workflows(BrandingTier.PROFESSIONAL)
        assert len(professional_workflows) >= len(basic_workflows)

        # Test Enterprise tier (should include all)
        enterprise_workflows = await temp_service.get_available_workflows(BrandingTier.ENTERPRISE)
        assert len(enterprise_workflows) >= len(professional_workflows)

    @pytest.mark.asyncio
    async def test_configure_custom_domain(self, temp_service, sample_branding_config):
        """Test custom domain configuration."""
        tenant_id = "test_tenant_123"

        # Create brand first
        brand_id = await temp_service.create_brand_config(tenant_id, sample_branding_config)

        # Configure custom domain
        ssl_config = {"certificate": "cert_data", "private_key": "key_data"}
        success = await temp_service.configure_custom_domain(brand_id, "custom.example.com", ssl_config)

        assert success is True

        # Verify domain was added to brand config
        updated_config = await temp_service.get_brand_config(brand_id)
        assert updated_config.custom_domain == "custom.example.com"
        assert updated_config.ssl_enabled is True

    @pytest.mark.asyncio
    async def test_generate_deployment_config(self, temp_service, sample_branding_config):
        """Test deployment configuration generation."""
        tenant_id = "test_tenant_123"

        # Create brand first
        brand_id = await temp_service.create_brand_config(tenant_id, sample_branding_config)

        # Generate deployment config
        deployment_config = await temp_service.generate_deployment_config(brand_id, tenant_id)

        assert deployment_config["brand_id"] == brand_id
        assert deployment_config["tenant_id"] == tenant_id
        assert deployment_config["deployment_type"] == "white_label"
        assert "branding" in deployment_config
        assert "tier_capabilities" in deployment_config
        assert "workflows" in deployment_config
        assert "integrations" in deployment_config

    @pytest.mark.asyncio
    async def test_generate_deployment_config_invalid_brand(self, temp_service):
        """Test deployment config generation with invalid brand ID."""
        with pytest.raises(ValueError, match="Brand configuration .* not found"):
            await temp_service.generate_deployment_config("invalid_brand", "tenant_123")

    def test_tier_capabilities_basic(self, temp_service):
        """Test tier capabilities for Basic tier."""
        capabilities = temp_service._get_tier_capabilities(BrandingTier.BASIC)

        assert capabilities["custom_branding"] is True
        assert capabilities["basic_analytics"] is True
        assert capabilities["standard_integrations"] is True
        assert capabilities["email_support"] is True

        # Should not have advanced features
        assert "advanced_analytics" not in capabilities
        assert "custom_domains" not in capabilities

    def test_tier_capabilities_professional(self, temp_service):
        """Test tier capabilities for Professional tier."""
        capabilities = temp_service._get_tier_capabilities(BrandingTier.PROFESSIONAL)

        # Should have basic features
        assert capabilities["custom_branding"] is True
        assert capabilities["basic_analytics"] is True

        # Should have professional features
        assert capabilities["advanced_analytics"] is True
        assert capabilities["workflow_automation"] is True
        assert capabilities["custom_domains"] is True
        assert capabilities["api_access"] is True

        # Should not have enterprise features
        assert "dedicated_support" not in capabilities
        assert "enterprise_sso" not in capabilities

    def test_tier_capabilities_enterprise(self, temp_service):
        """Test tier capabilities for Enterprise tier."""
        capabilities = temp_service._get_tier_capabilities(BrandingTier.ENTERPRISE)

        # Should have all features
        assert capabilities["custom_branding"] is True
        assert capabilities["advanced_analytics"] is True
        assert capabilities["workflow_automation"] is True
        assert capabilities["custom_domains"] is True
        assert capabilities["api_access"] is True
        assert capabilities["dedicated_support"] is True
        assert capabilities["enterprise_sso"] is True
        assert capabilities["white_label_mobile_app"] is True
        assert capabilities["audit_logs"] is True
        assert capabilities["data_residency"] is True

    def test_generate_custom_theme_css(self, temp_service, sample_branding_config):
        """Test custom CSS theme generation."""
        brand_id = "test_brand_123"

        # Create themes directory
        themes_dir = Path("data/white_label/themes")
        themes_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Generate theme
            asyncio.run(temp_service._generate_custom_theme(brand_id, sample_branding_config))

            # Verify theme file was created
            theme_file = themes_dir / f"{brand_id}_theme.css"
            assert theme_file.exists()

            # Verify CSS content
            with open(theme_file, "r") as f:
                css_content = f.read()

            assert "--primary-color: #6D28D9;" in css_content
            assert "--secondary-color: #4C1D95;" in css_content
            assert "--accent-color: #10B981;" in css_content
            assert "brand-primary" in css_content
            assert "brand-secondary" in css_content

        finally:
            # Cleanup
            if themes_dir.exists():
                shutil.rmtree(themes_dir)

    @pytest.mark.asyncio
    async def test_integration_marketplace_tier_filtering(self, temp_service):
        """Test integration marketplace filtering by consulting tier."""
        # Create test integration for Professional tier
        professional_integration = IntegrationMarketplace(
            integration_id="test_professional",
            name="Professional Integration",
            provider="TestProvider",
            description="Professional tier integration",
            setup_instructions="Setup instructions",
            api_endpoints=["/api/test"],
            required_credentials=["api_key"],
            supported_features=["feature1"],
            consulting_tier=BrandingTier.PROFESSIONAL,
            implementation_complexity="moderate",
        )

        temp_service._save_integration_config(professional_integration)

        # Test Basic tier (should not include Professional integration)
        basic_integrations = await temp_service.get_integration_marketplace(BrandingTier.BASIC)
        professional_ids = [i.integration_id for i in basic_integrations]
        assert "test_professional" not in professional_ids

        # Test Professional tier (should include Professional integration)
        professional_integrations = await temp_service.get_integration_marketplace(BrandingTier.PROFESSIONAL)
        professional_ids = [i.integration_id for i in professional_integrations]
        assert "test_professional" in professional_ids

    def test_initialization_creates_directories(self):
        """Test that service initialization creates required directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock Path.mkdir to verify it's called
            with patch("pathlib.Path.mkdir") as mock_mkdir:
                service = WhiteLabelService()

                # Verify directories were created
                assert mock_mkdir.call_count >= 3  # brands, templates, integrations

    @pytest.mark.asyncio
    async def test_enterprise_assets_initialization(self, temp_service):
        """Test that enterprise templates and integrations are properly initialized."""
        # Should have enterprise workflow templates
        enterprise_workflows = await temp_service.get_available_workflows(BrandingTier.ENTERPRISE)
        workflow_ids = [w.template_id for w in enterprise_workflows]

        assert "lead_intelligence_swarm" in workflow_ids
        assert "predictive_churn_prevention" in workflow_ids
        assert "executive_intelligence_reporting" in workflow_ids

        # Should have enterprise integrations
        enterprise_integrations = await temp_service.get_integration_marketplace(BrandingTier.ENTERPRISE)
        integration_ids = [i.integration_id for i in enterprise_integrations]

        assert "salesforce_enterprise" in integration_ids
        assert "microsoft_dynamics" in integration_ids

    def test_branding_config_dataclass_validation(self):
        """Test BrandingConfig dataclass validation and defaults."""
        # Test minimal config
        config = BrandingConfig(company_name="Test Company", logo_url="https://example.com/logo.png")

        assert config.primary_color == "#6D28D9"  # Default
        assert config.tier == BrandingTier.BASIC  # Default
        assert config.feature_flags == {}  # Default from __post_init__
        assert config.navigation_menu == []  # Default from __post_init__

    def test_workflow_template_dataclass(self):
        """Test WorkflowTemplate dataclass structure."""
        template = WorkflowTemplate(
            template_id="test_id",
            name="Test Template",
            description="Test description",
            category="Test Category",
            trigger_type="webhook",
            actions=[{"type": "test_action"}],
            conditions=[{"field": "test_field", "operator": "equals", "value": "test"}],
            customizable_fields=["field1"],
            consulting_tier=BrandingTier.BASIC,
            estimated_value="Test value",
        )

        assert template.template_id == "test_id"
        assert template.consulting_tier == BrandingTier.BASIC
        assert len(template.actions) == 1
        assert len(template.conditions) == 1

    def test_integration_marketplace_dataclass(self):
        """Test IntegrationMarketplace dataclass structure."""
        integration = IntegrationMarketplace(
            integration_id="test_integration",
            name="Test Integration",
            provider="Test Provider",
            description="Test description",
            setup_instructions="Setup steps",
            api_endpoints=["/api/endpoint"],
            required_credentials=["api_key"],
            supported_features=["feature1", "feature2"],
            consulting_tier=BrandingTier.PROFESSIONAL,
            implementation_complexity="moderate",
        )

        assert integration.integration_id == "test_integration"
        assert integration.consulting_tier == BrandingTier.PROFESSIONAL
        assert len(integration.api_endpoints) == 1
        assert len(integration.supported_features) == 2

    def test_service_factory_function(self):
        """Test the get_white_label_service factory function."""
        from ghl_real_estate_ai.services.white_label_service import get_white_label_service

        service = get_white_label_service()
        assert isinstance(service, WhiteLabelService)

    @pytest.mark.asyncio
    async def test_error_handling_in_brand_creation(self, temp_service):
        """Test error handling during brand creation."""
        # Mock file operations to raise an exception
        with patch("builtins.open", side_effect=IOError("Disk full")):
            config = BrandingConfig(company_name="Test Company", logo_url="https://example.com/logo.png")

            with pytest.raises(IOError):
                await temp_service.create_brand_config("tenant_123", config)