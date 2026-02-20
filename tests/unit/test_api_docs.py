from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

"""Unit tests for the API documentation schemas and OpenAPI spec.

Tests OpenAPI spec generation, tag presence, response schema validation,
and that demo routes use the new response models.
"""

import pytest

shap = pytest.importorskip("shap", reason="shap not installed")

from fastapi.testclient import TestClient

from ghl_real_estate_ai.api.schemas.api_docs import (
    OPENAPI_TAGS,
    BotStatusItem,
    BotStatusResponse,
    HealthResponse,
    LeadListResponse,
    LeadSummary,
    PipelineResponse,
    PipelineSummary,
    StageMetrics,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def client():
    """Create a FastAPI test client.

    Uses a minimal import to get the real app so that we test the actual
    OpenAPI spec produced by main.py.
    """
    from ghl_real_estate_ai.api.main import app

    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def openapi_spec(client) -> dict:
    """Fetch the OpenAPI spec from the running app."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    return response.json()


# ============================================================================
# Test: OpenAPI Spec Generation
# ============================================================================


class TestOpenAPISpec:
    """Tests for OpenAPI spec correctness."""

    def test_openapi_returns_200(self, client):
        """The /openapi.json endpoint should return 200."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_openapi_has_info(self, openapi_spec: dict):
        """OpenAPI spec should have info with title and version."""
        info = openapi_spec.get("info", {})
        assert info.get("title") == "EnterpriseHub API"
        assert info.get("version") == "5.0.1"

    def test_openapi_has_description(self, openapi_spec: dict):
        """OpenAPI spec should have a non-empty description."""
        info = openapi_spec.get("info", {})
        description = info.get("description", "")
        assert "real estate" in description.lower()


# ============================================================================
# Test: Tag Presence
# ============================================================================


class TestTagPresence:
    """Tests that OpenAPI tags are properly defined."""

    def test_tags_list_not_empty(self):
        """OPENAPI_TAGS should not be empty."""
        assert len(OPENAPI_TAGS) > 0

    def test_required_tags_present(self):
        """All required tag names should be defined."""
        tag_names = {t["name"] for t in OPENAPI_TAGS}
        required = {"leads", "pipeline", "bots", "analytics", "health", "Demo"}
        assert required.issubset(tag_names), f"Missing tags: {required - tag_names}"

    def test_tags_have_descriptions(self):
        """Each tag should have a non-empty description."""
        for tag in OPENAPI_TAGS:
            assert tag.get("description"), f"Tag '{tag['name']}' has no description"

    def test_tags_in_openapi_spec(self, openapi_spec: dict):
        """Tags from OPENAPI_TAGS should appear in the generated spec."""
        spec_tags = openapi_spec.get("tags", [])
        spec_tag_names = {t["name"] for t in spec_tags}
        # At minimum, the Demo tag should be present (used by demo routes)
        assert "Demo" in spec_tag_names


# ============================================================================
# Test: Response Schema Validation
# ============================================================================


class TestResponseSchemas:
    """Tests that Pydantic response schemas validate correctly."""

    def test_lead_summary_valid(self):
        """LeadSummary should accept valid data."""
        lead = LeadSummary(
            id="lead_001",
            first_name="Maria",
            last_name="Garcia",
            source="Zillow",
            score=85,
            temperature="Hot-Lead",
            stage="Qualified",
            created_at="2026-01-15T10:30:00",
            last_activity="2026-02-07T14:22:00",
        )
        assert lead.id == "lead_001"
        assert lead.score == 85

    def test_lead_summary_score_validation(self):
        """LeadSummary should reject score > 100."""
        with pytest.raises(Exception):
            LeadSummary(
                id="lead_001",
                first_name="Maria",
                last_name="Garcia",
                source="Zillow",
                score=150,  # Invalid: > 100
                temperature="Hot-Lead",
                stage="Qualified",
                created_at="2026-01-15T10:30:00",
                last_activity="2026-02-07T14:22:00",
            )

    def test_lead_list_response(self):
        """LeadListResponse should accept valid lead list."""
        lead = LeadSummary(
            id="lead_001",
            first_name="Maria",
            last_name="Garcia",
            source="Zillow",
            score=85,
            temperature="Hot-Lead",
            stage="Qualified",
            created_at="2026-01-15T10:30:00",
            last_activity="2026-02-07T14:22:00",
        )
        response = LeadListResponse(leads=[lead], total=1)
        assert response.total == 1
        assert len(response.leads) == 1

    def test_health_response_valid(self):
        """HealthResponse should accept valid health data."""
        resp = HealthResponse(
            status="healthy",
            active_bots=4,
            uptime_pct=99.87,
            version="5.0.1",
        )
        assert resp.status == "healthy"
        assert resp.active_bots == 4

    def test_stage_metrics_valid(self):
        """StageMetrics should accept valid stage data."""
        stage = StageMetrics(count=12, avg_score=45.0, avg_days_in_stage=1.2)
        assert stage.count == 12

    def test_bot_status_response(self):
        """BotStatusResponse should accept valid bot data."""
        bot = BotStatusItem(
            name="Jorge Lead Bot",
            type="lead",
            status="active",
            uptime_hours=72.3,
            conversations_today=47,
        )
        resp = BotStatusResponse(bots=[bot], total_conversations_today=47)
        assert len(resp.bots) == 1
        assert resp.total_conversations_today == 47

    def test_pipeline_summary_conversion_rate_bound(self):
        """PipelineSummary should reject conversion_rate > 1.0."""
        with pytest.raises(Exception):
            PipelineSummary(
                total_leads=40,
                conversion_rate=1.5,  # Invalid: > 1.0
                avg_days_to_close=28.5,
                pipeline_value=4_250_000,
                temperature_distribution={"Hot-Lead": 8},
            )


# ============================================================================
# Test: Demo Route Integration
# ============================================================================


class TestDemoRouteIntegration:
    """Tests that demo routes return data matching the response schemas."""

    def test_demo_leads_returns_200(self, client):
        """GET /demo/leads should return 200."""
        response = client.get("/demo/leads")
        assert response.status_code == 200

    def test_demo_pipeline_returns_200(self, client):
        """GET /demo/pipeline should return 200."""
        response = client.get("/demo/pipeline")
        assert response.status_code == 200

    def test_demo_health_returns_200(self, client):
        """GET /demo/health should return 200."""
        response = client.get("/demo/health")
        assert response.status_code == 200

    def test_demo_bots_returns_200(self, client):
        """GET /demo/bots should return 200."""
        response = client.get("/demo/bots")
        assert response.status_code == 200

    def test_demo_health_response_structure(self, client):
        """GET /demo/health should match HealthResponse schema."""
        response = client.get("/demo/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert "active_bots" in data
        assert "uptime_pct" in data
        assert "version" in data