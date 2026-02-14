import pytest
pytestmark = pytest.mark.integration

"""Tests for Professional Export Engine."""

import pytest

from ghl_real_estate_ai.services.professional_export_engine import (

    BrandingConfig,
    ProfessionalExportEngine,
    ReportFormat,
    ReportType,
)


@pytest.fixture
def engine():
    return ProfessionalExportEngine(branding=BrandingConfig(agent_name="Jorge Test"))


@pytest.fixture
def sample_comparables():
    return [
        {
            "address": "100 Victoria St",
            "sale_price": 780_000,
            "sale_date": "2025-12-01",
            "sqft": 2200,
            "bedrooms": 4,
            "bathrooms": 2.5,
            "distance_miles": 0.3,
            "adjustments": {"sqft": 5000, "pool": -3000},
        },
        {
            "address": "200 Haven Ave",
            "sale_price": 820_000,
            "sale_date": "2025-11-15",
            "sqft": 2400,
            "bedrooms": 4,
            "bathrooms": 3,
            "distance_miles": 0.5,
            "adjustments": {"garage": 2000},
        },
        {
            "address": "300 Etiwanda Blvd",
            "sale_price": 750_000,
            "sale_date": "2025-10-20",
            "sqft": 2000,
            "bedrooms": 3,
            "bathrooms": 2,
            "distance_miles": 0.8,
            "adjustments": {"bedrooms": 10000},
        },
    ]


@pytest.fixture
def sample_property():
    return {
        "bedrooms": 4,
        "bathrooms": 2.5,
        "sqft": 2300,
        "year_built": 2015,
        "lot_size": "6,500 sqft",
        "condition": "Good",
    }


# -------------------------------------------------------------------------
# Market reports
# -------------------------------------------------------------------------


class TestMarketReports:
    @pytest.mark.asyncio
    async def test_html_report_generated(self, engine):
        result = await engine.generate_market_report("victoria", format="html")
        assert result.format == ReportFormat.HTML
        assert "<html>" in result.content
        assert "Victoria" in result.content

    @pytest.mark.asyncio
    async def test_csv_report_generated(self, engine):
        result = await engine.generate_market_report("haven", format="csv")
        assert result.format == ReportFormat.CSV
        assert "median_price" in result.content

    @pytest.mark.asyncio
    async def test_text_report_generated(self, engine):
        result = await engine.generate_market_report("etiwanda", format="text")
        assert result.format == ReportFormat.TEXT
        assert "Etiwanda" in result.content

    @pytest.mark.asyncio
    async def test_report_has_branding(self, engine):
        result = await engine.generate_market_report("victoria", format="html")
        assert "Jorge Test" in result.content

    @pytest.mark.asyncio
    async def test_report_size_positive(self, engine):
        result = await engine.generate_market_report("victoria")
        assert result.size_bytes > 0

    @pytest.mark.asyncio
    async def test_report_has_filename(self, engine):
        result = await engine.generate_market_report("haven", report_type="weekly")
        assert "haven" in result.filename
        assert "weekly" in result.filename

    @pytest.mark.asyncio
    async def test_custom_market_data(self, engine):
        data = {"median_price": 999_999, "avg_dom": 10, "inventory": 20}
        result = await engine.generate_market_report("victoria", market_data=data, format="text")
        assert "999,999" in result.content


# -------------------------------------------------------------------------
# CMA reports
# -------------------------------------------------------------------------


class TestCMAReports:
    @pytest.mark.asyncio
    async def test_cma_html(self, engine, sample_property, sample_comparables):
        result = await engine.generate_cma_report("456 Haven Ave", sample_property, sample_comparables, format="html")
        assert "Comparative Market Analysis" in result.content
        assert "456 Haven Ave" in result.content
        assert result.report_type == ReportType.CMA

    @pytest.mark.asyncio
    async def test_cma_contains_comparables(self, engine, sample_property, sample_comparables):
        result = await engine.generate_cma_report("456 Haven Ave", sample_property, sample_comparables)
        assert "100 Victoria St" in result.content
        assert "200 Haven Ave" in result.content

    @pytest.mark.asyncio
    async def test_cma_value_range(self, engine, sample_property, sample_comparables):
        result = await engine.generate_cma_report("456 Haven Ave", sample_property, sample_comparables)
        # Should contain dollar amounts for low/mid/high
        assert "$" in result.content

    @pytest.mark.asyncio
    async def test_cma_text_format(self, engine, sample_property, sample_comparables):
        result = await engine.generate_cma_report("456 Haven Ave", sample_property, sample_comparables, format="text")
        assert "CMA Report" in result.content
        assert "456 Haven Ave" in result.content

    @pytest.mark.asyncio
    async def test_cma_metadata(self, engine, sample_property, sample_comparables):
        result = await engine.generate_cma_report("456 Haven Ave", sample_property, sample_comparables)
        assert result.metadata["comparables_count"] == 3


# -------------------------------------------------------------------------
# Lead export
# -------------------------------------------------------------------------


class TestLeadExport:
    @pytest.mark.asyncio
    async def test_csv_export(self, engine):
        leads = [
            {"name": "Sarah", "phone": "555-1234", "status": "qualified"},
            {"name": "Mike", "phone": "555-5678", "status": "prospect"},
        ]
        result = await engine.export_leads_csv(leads)
        assert result.format == ReportFormat.CSV
        assert "Sarah" in result.content
        assert "Mike" in result.content

    @pytest.mark.asyncio
    async def test_csv_header(self, engine):
        leads = [{"name": "Test", "score": 8}]
        result = await engine.export_leads_csv(leads)
        assert "name" in result.content
        assert "score" in result.content

    @pytest.mark.asyncio
    async def test_empty_leads(self, engine):
        result = await engine.export_leads_csv([])
        assert "No leads" in result.content

    @pytest.mark.asyncio
    async def test_lead_count_metadata(self, engine):
        leads = [{"name": f"Lead {i}"} for i in range(5)]
        result = await engine.export_leads_csv(leads)
        assert result.metadata["lead_count"] == 5


# -------------------------------------------------------------------------
# Client presentations
# -------------------------------------------------------------------------


class TestPresentations:
    @pytest.mark.asyncio
    async def test_presentation_generated(self, engine):
        sections = [
            {"title": "Market Overview", "content": "The market is strong."},
            {"title": "Your Home", "content": "Valued at $800,000."},
        ]
        result = await engine.generate_presentation("Sarah Johnson", sections)
        assert "Sarah Johnson" in result.content
        assert "Market Overview" in result.content
        assert result.report_type == ReportType.CLIENT_PRESENTATION

    @pytest.mark.asyncio
    async def test_presentation_branding(self, engine):
        sections = [{"title": "Test", "content": "Content"}]
        result = await engine.generate_presentation("Client", sections)
        assert "Jorge Test" in result.content


# -------------------------------------------------------------------------
# Branding
# -------------------------------------------------------------------------


class TestBranding:
    def test_custom_branding(self):
        custom = BrandingConfig(
            agent_name="Custom Agent",
            accent_color="#FF0000",
        )
        engine = ProfessionalExportEngine(branding=custom)
        assert engine.branding.agent_name == "Custom Agent"
        assert engine.branding.accent_color == "#FF0000"