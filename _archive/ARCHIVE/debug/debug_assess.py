
import asyncio
import sys
import traceback
from datetime import datetime, timezone
from uuid import uuid4

# Add project root to path
import os
sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import AsyncSession
# Force SQLite for debug
import ghl_real_estate_ai.compliance_platform.database.database as db_mod
db_mod.DATABASE_URL = "sqlite+aiosqlite:///./debug_compliance.db"
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
# DISABLE ECHO HERE for cleaner breadcrumbs
db_mod.engine = create_async_engine(db_mod.DATABASE_URL, echo=False)
db_mod.AsyncSessionLocal = async_sessionmaker(
    bind=db_mod.engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

from ghl_real_estate_ai.compliance_platform.database.database import AsyncSessionLocal, init_db
from ghl_real_estate_ai.compliance_platform.services.compliance_service import ComplianceService
from ghl_real_estate_ai.compliance_platform.models.compliance_models import ComplianceStatus, RiskLevel

async def debug_assessment():
    print("Starting debug assessment...")
    
    # 1. Initialize DB (creates tables)
    try:
        await init_db()
        print("Database initialized.")
    except Exception as e:
        print(f"Error initializing DB: {e}")
        traceback.print_exc()
        return

    async with AsyncSessionLocal() as session:
        service = ComplianceService(session=session, enable_ai_analysis=False)
        
        # 2. Register a model
        try:
            print("Registering model...")
            model = await service.register_model(
                name="Debug Model",
                version="1.0.0",
                description="A model for debugging 500 errors",
                model_type="nlp",
                provider="internal",
                deployment_location="cloud",
                intended_use="Debugging",
                use_case_category="general",
                data_residency=["us"],
                registered_by="debug_script"
            )
            print(f"Model registered: {model.model_id}")
            await session.commit()
        except Exception as e:
            print(f"Error registering model: {e}")
            traceback.print_exc()
            return

    # New session for assessment
    async with AsyncSessionLocal() as session:
        service = ComplianceService(session=session, enable_ai_analysis=False)
        try:
            print(f"Assessing model {model.model_id}...")
            # Added timeout to prevent indefinite hang
            async with asyncio.timeout(30):
                score, risk, violations = await service.assess_compliance(model.model_id)
            print("Assessment completed successfully!")
            print(f"Score: {score.overall_score}")
            print(f"Risk: {risk.risk_level}")
            print(f"Violations: {len(violations)}")
            await session.commit()
        except asyncio.TimeoutError:
            print("\n!!! ASSESSMENT TIMED OUT !!!")
        except Exception as e:
            print("\n!!! ASSESSMENT FAILED !!!")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {e}")
            print("\nFull Traceback:")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_assessment())
