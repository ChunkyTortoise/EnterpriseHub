
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ghl_real_estate_ai.compliance_platform.database.models import Base
from ghl_real_estate_ai.compliance_platform.database.repository import ModelRepository
from ghl_real_estate_ai.compliance_platform.models.compliance_models import ComplianceStatus, RiskLevel

# Use an in-memory SQLite DB for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.mark.asyncio
async def test_model_repository_crud(db_session):
    repo = ModelRepository(db_session)

    # Create
    model = await repo.create(
        name="Test DB Model",
        version="1.0",
        description="Testing persistence",
        model_type="classifier",
        provider="internal",
        deployment_location="aws",
        intended_use="testing",
        compliance_status=ComplianceStatus.COMPLIANT,
        risk_level=RiskLevel.MINIMAL,
    )

    assert model.model_id is not None
    assert model.name == "Test DB Model"

    # Read
    fetched = await repo.get(model.model_id)
    assert fetched is not None
    assert fetched.name == "Test DB Model"

    # Update
    updated = await repo.update(model.model_id, risk_level=RiskLevel.HIGH)
    assert updated.risk_level == RiskLevel.HIGH

    # List
    models = await repo.list_models()
    assert len(models) == 1
    assert models[0].name == "Test DB Model"

    # Delete
    deleted = await repo.delete(model.model_id)
    assert deleted is True

    fetched_after = await repo.get(model.model_id)
    assert fetched_after is None
