"""
Simulate Multi-Tenant Jorge Bot Traffic for Analytics Dashboard Visualization.

Generates realistic events for multiple locations:
- Seller Bot Interactions (Hot, Warm, Cold)
- Vague Answer Streaks
- Take-Away Close Triggers
- Lead Bot Scoring
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta
from ghl_real_estate_ai.services.analytics_service import AnalyticsService

async def simulate_location_traffic(service, location_id, name):
    print(f"🚀 Starting Traffic Simulation for {name} ({location_id})")
    
    # 1. Simulate Seller Bot Traffic
    seller_personas = [
        ("hot", 4, 0.9, 0, "handoff"),
        ("hot", 4, 0.8, 0, "handoff"),
        ("warm", 3, 0.6, 1, "qualification"),
        ("cold", 1, 0.3, 0, "nurture"),
        ("cold", 2, 0.2, 2, "take_away_close"), # Vague streak -> Take away
        ("warm", 3, 0.7, 0, "qualification"),
        ("cold", 1, 0.4, 1, "qualification"),
        ("hot", 4, 0.95, 0, "handoff"),
    ]

    for _ in range(2): 
        for temp, q_ans, qual, vague, resp_type in seller_personas:
            contact_id = f"contact_{uuid.uuid4().hex[:8]}"
            qual = min(1.0, max(0.0, qual + random.uniform(-0.1, 0.1)))
            
            data = {
                "temperature": temp,
                "questions_answered": q_ans,
                "response_quality": qual,
                "message_length": random.randint(20, 140),
                "vague_streak": vague,
                "response_type": resp_type
            }
            
            await service.track_event(
                event_type="jorge_seller_interaction",
                location_id=location_id,
                contact_id=contact_id,
                data=data
            )
            
            # Also track a message event
            await service.track_event(
                event_type="message_received",
                location_id=location_id,
                contact_id=contact_id
            )

    # 2. Simulate Lead Bot (Buyer) Traffic
    for i in range(random.randint(5, 15)):
        score = random.randint(40, 95)
        cls = "hot" if score > 75 else "warm" if score > 50 else "cold"
        await service.track_event(
            event_type="lead_scored",
            location_id=location_id,
            contact_id=f"lead_{uuid.uuid4().hex[:4]}",
            data={"score": score, "classification": cls}
        )

    # 3. Simulate Vapi Calls
    for i in range(random.randint(1, 3)):
        await service.track_event(
            event_type="log_event",
            location_id=location_id,
            contact_id=f"hot_seller_{uuid.uuid4().hex[:4]}",
            data={"event": "Vapi Outbound Call Triggered", "details": "Success"}
        )

async def simulate_traffic():
    service = AnalyticsService()
    
    locations = [
        ("loc_austin_001", "Austin Main"),
        ("loc_dallas_002", "Dallas Luxury"),
        ("loc_houston_003", "Houston Heights")
    ]
    
    tasks = []
    for loc_id, name in locations:
        tasks.append(simulate_location_traffic(service, loc_id, name))
    
    await asyncio.gather(*tasks)
    print("\n✅ Multi-Tenant Simulation Complete. Check Dashboard.")

if __name__ == "__main__":
    asyncio.run(simulate_traffic())