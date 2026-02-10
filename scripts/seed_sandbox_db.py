import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

SAMPLE_LEADS = [
    {
        "ghl_lead_id": "sandbox-lead-001",
        "email": "lead1@example.com",
        "first_name": "Alex",
        "last_name": "Morgan",
        "source": "sandbox",
        "lead_score": 72,
        "qualification_stage": "qualified",
    },
    {
        "ghl_lead_id": "sandbox-lead-002",
        "email": "lead2@example.com",
        "first_name": "Jamie",
        "last_name": "Lee",
        "source": "sandbox",
        "lead_score": 54,
        "qualification_stage": "engaged",
    },
]

SAMPLE_PROPERTIES = [
    {
        "property_id": "sandbox-prop-001",
        "address": "123 Sandbox Ave",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
        "price": 650000,
        "status": "active",
        "property_type": "single_family",
        "bedrooms": 3,
        "bathrooms": 2.5,
    },
    {
        "property_id": "sandbox-prop-002",
        "address": "456 Demo Blvd",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78702",
        "price": 875000,
        "status": "active",
        "property_type": "condo",
        "bedrooms": 2,
        "bathrooms": 2.0,
    },
]


async def seed():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is not set")

    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(database_url)

    async with engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";'))
        # Ensure tables exist
        await conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                ghl_lead_id VARCHAR(255) UNIQUE,
                email VARCHAR(255),
                phone VARCHAR(50),
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                source VARCHAR(100),
                lead_score INTEGER DEFAULT 0,
                qualification_stage VARCHAR(50) DEFAULT 'unqualified',
                engagement_score INTEGER DEFAULT 0,
                converted BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
        ))

        await conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS properties (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                property_id VARCHAR(255) UNIQUE,
                address TEXT,
                city VARCHAR(100),
                state VARCHAR(20),
                zip_code VARCHAR(20),
                price DECIMAL(12,2),
                status VARCHAR(20) DEFAULT 'active',
                property_type VARCHAR(50),
                bedrooms INTEGER,
                bathrooms DECIMAL(3,1),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
        ))

        for lead in SAMPLE_LEADS:
            await conn.execute(
                text(
                    """
                    INSERT INTO leads (ghl_lead_id, email, first_name, last_name, source, lead_score, qualification_stage)
                    VALUES (:ghl_lead_id, :email, :first_name, :last_name, :source, :lead_score, :qualification_stage)
                    ON CONFLICT (ghl_lead_id) DO NOTHING
                    """
                ),
                lead,
            )

        for prop in SAMPLE_PROPERTIES:
            await conn.execute(
                text(
                    """
                    INSERT INTO properties (property_id, address, city, state, zip_code, price, status, property_type, bedrooms, bathrooms)
                    VALUES (:property_id, :address, :city, :state, :zip_code, :price, :status, :property_type, :bedrooms, :bathrooms)
                    ON CONFLICT (property_id) DO NOTHING
                    """
                ),
                prop,
            )

    await engine.dispose()
    print("Sandbox seed complete")


if __name__ == "__main__":
    asyncio.run(seed())
