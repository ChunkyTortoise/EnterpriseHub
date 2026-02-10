#!/usr/bin/env python3
"""Seed development data for EnterpriseHub.

Usage:
  python scripts/seed_data.py
"""
from __future__ import annotations

import asyncio
from decimal import Decimal

from sqlalchemy import select

from ghl_real_estate_ai.database.session import get_async_session
from ghl_real_estate_ai.models.leads import Lead
from ghl_real_estate_ai.models.properties import Property
from ghl_real_estate_ai.models.conversations import Conversation


async def seed():
    async with get_async_session() as session:
        # Avoid duplicating seed data if it already exists
        existing = (await session.execute(select(Lead).limit(1))).scalar_one_or_none()
        if existing:
            print("Seed data already present; skipping.")
            return

        lead_1 = Lead(
            ghl_lead_id="ghl_001",
            email="ava.smith@example.com",
            phone="+15125550101",
            first_name="Ava",
            last_name="Smith",
            source="web",
            lead_score=72,
            qualification_stage="qualified",
            engagement_score=88,
            converted=False,
        )
        lead_2 = Lead(
            ghl_lead_id="ghl_002",
            email="liam.johnson@example.com",
            phone="+15125550102",
            first_name="Liam",
            last_name="Johnson",
            source="referral",
            lead_score=45,
            qualification_stage="nurturing",
            engagement_score=54,
            converted=False,
        )
        lead_3 = Lead(
            ghl_lead_id="ghl_003",
            email="mia.davis@example.com",
            phone="+15125550103",
            first_name="Mia",
            last_name="Davis",
            source="campaign",
            lead_score=90,
            qualification_stage="hot",
            engagement_score=95,
            converted=True,
        )

        prop_1 = Property(
            property_id="prop_1001",
            address="123 Terra Vista Pkwy",
            city="Rancho Cucamonga",
            state="CA",
            zip_code="91730",
            price=Decimal("875000.00"),
            status="active",
            property_type="single_family",
            bedrooms=4,
            bathrooms=Decimal("3.0"),
        )
        prop_2 = Property(
            property_id="prop_1002",
            address="480 Etiwanda Ave",
            city="Rancho Cucamonga",
            state="CA",
            zip_code="91739",
            price=Decimal("1125000.00"),
            status="pending",
            property_type="single_family",
            bedrooms=5,
            bathrooms=Decimal("4.0"),
        )

        convo_1 = Conversation(
            lead_id=lead_1.id,
            conversation_type="qualification",
        )

        session.add_all([lead_1, lead_2, lead_3, prop_1, prop_2, convo_1])
        await session.commit()
        print("Seed data inserted.")


if __name__ == "__main__":
    asyncio.run(seed())
