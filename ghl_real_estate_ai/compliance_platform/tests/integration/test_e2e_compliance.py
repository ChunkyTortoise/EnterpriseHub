from typing import Generator
from unittest.mock import patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ghl_real_estate_ai.compliance_platform.api.router import router
from ghl_real_estate_ai.compliance_platform.database.database import get_db
from ghl_real_estate_ai.compliance_platform.database.models import Base
from ghl_real_estate_ai.compliance_platform.models.compliance_models import (
    RiskLevel,
)

# Setup Test DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def override_get_db():
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Create a FastAPI app for testing and include the router
app = FastAPI()
app.include_router(router)
app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client(setup_db) -> Generator:
    # Patch AsyncSessionLocal used in background tasks
    with patch("ghl_real_estate_ai.compliance_platform.api.router.AsyncSessionLocal", TestingSessionLocal):
        with TestClient(app) as c:
            yield c


@pytest.fixture
def mock_ai_analyzer():
    """Mock the AI analyzer to avoid external API calls."""
    # We patch RiskDetector.assess_model to avoid LLM calls
    with patch("ghl_real_estate_ai.compliance_platform.engine.risk_detector.RiskDetector.assess_model") as mock_assess:
        from datetime import datetime

        from ghl_real_estate_ai.compliance_platform.models.compliance_models import RiskAssessment

        async def side_effect(model, context):
            return RiskAssessment(
                model_id=model.model_id,
                model_name=model.name,
                risk_level=RiskLevel.HIGH,  # Force high risk
                risk_score=45.0,
                transparency_score=50.0,
                assessed_at=datetime.utcnow(),
            )

        mock_assess.side_effect = side_effect
        yield mock_assess


@pytest.mark.asyncio
async def test_e2e_compliance_workflow(client, mock_ai_analyzer):
    """
    End-to-End Integration Test for Compliance Platform
    """

    # 1. Register a new AI Model
    model_payload = {
        "name": "E2E Test Model",
        "version": "1.0.0",
        "description": "An AI model for end-to-end testing",
        "model_type": "nlp",
        "provider": "openai",
        "deployment_location": "cloud",
        "intended_use": "Customer support automation",
        "use_case_category": "customer_service",
        "data_residency": ["us"],
        "personal_data_processed": True,
        "sensitive_data_processed": False,
    }

    response = client.post("/api/v1/compliance/models/register", json=model_payload)
    assert response.status_code == 201
    data = response.json()
    model_id = data["id"]

    print(f"\n[E2E] Model Registered: {model_id}")

    # 2. Assess Compliance
    assess_payload = {
        "model_id": model_id,
        "check_types": ["full"],
        "async_mode": False,  # Sync for easier testing
        "context": {"env": "staging"},
    }

    response = client.post("/api/v1/compliance/assess", json=assess_payload)
    assert response.status_code == 200
    assessment_data = response.json()
    assert assessment_data["status"] == "completed"

    print(f"\n[E2E] Assessment Completed: Score={assessment_data['compliance_score']}")

    # 3. Verify Violations
    response = client.get(f"/api/v1/compliance/models/{model_id}/violations")
    assert response.status_code == 200
    violations = response.json()

    print(f"\n[E2E] Violations Found: {len(violations)}")

    if len(violations) > 0:
        violation_id = violations[0]["id"]

        # 4. Acknowledge a Violation
        ack_payload = {"acknowledged_by": "e2e_tester", "notes": "Acknowledging for test purposes"}

        response = client.post(
            f"/api/v1/compliance/models/{model_id}/violations/{violation_id}/acknowledge", json=ack_payload
        )
        assert response.status_code == 200
        ack_data = response.json()
        assert ack_data["status"] == "acknowledged"

        print(f"\n[E2E] Violation {violation_id} Acknowledged")

    # 5. Generate Compliance Report
    report_payload = {"model_id": model_id, "report_type": "executive", "period_days": 30}

    response = client.post("/api/v1/compliance/reports/generate", json=report_payload)
    assert response.status_code == 200
    report_data = response.json()
    report_id = report_data["report_id"]

    print(f"\n[E2E] Report Generation Started: {report_id}")

    # Check report status
    response = client.get(f"/api/v1/compliance/reports/{report_id}")
    assert response.status_code == 200
    final_report = response.json()
    print(f"Report Status: {final_report.get('status')}")

    # 6. Verify Dashboard Summary
    response = client.get("/api/v1/compliance/dashboard/summary")
    assert response.status_code == 200
    dashboard = response.json()
    assert dashboard["total_models"] >= 1

    print("\n[E2E] Dashboard Summary Verified")

    # 7. Test Batch Assessment
    batch_payload = {"model_ids": [model_id], "context": {"trigger": "batch_test"}}
    response = client.post("/api/v1/compliance/assess/batch", json=batch_payload)
    assert response.status_code == 200
    batch_data = response.json()
    assert batch_data["model_count"] == 1
    print("\n[E2E] Batch Assessment Triggered")

    # 8. Test Data Export
    response = client.get("/api/v1/compliance/reports/export?format=csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"
    print("\n[E2E] Data Export (CSV) Verified")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
