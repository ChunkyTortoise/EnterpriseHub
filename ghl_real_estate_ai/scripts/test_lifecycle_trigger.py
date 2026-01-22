"""
🧬 Lifecycle Trigger Test Script
================================

Simulates a full lead journey (Lead -> Showing -> Offer -> Closed)
to verify event log reconciliation in the sync service.
"""

import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from ghl_real_estate_ai.services.agent_state_sync import sync_service
from ghl_real_estate_ai.utils.async_utils import run_async

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def simulate_journey(lead_id: str, lead_name: str):
    logger.info(f"🚀 Starting journey simulation for {lead_name} ({lead_id})")
    
    # 1. Inbound Lead
    await sync_service.record_lead_event(lead_id, "GHL", "New Lead created from Facebook Ad.", "action")
    await sync_service.record_lead_event(lead_id, "AI", "Analyzing intent for new inbound lead.", "thought")
    await asyncio.sleep(0.5)
    
    # 2. Qualification
    await sync_service.record_lead_event(lead_id, "AI", "Sent qualification SMS sequence.", "sms")
    await sync_service.record_lead_event(lead_id, "GHL", "Contact replied with budget and timeline.", "action")
    await sync_service.record_lead_event(lead_id, "AI", "Intent Decoded: Hot Lead (Score: 88).", "thought")
    await asyncio.sleep(0.5)
    
    # 3. Showing
    await sync_service.record_lead_event(lead_id, "GHL", "Tag Added: ai_schedule_showing", "action")
    await sync_service.record_lead_event(lead_id, "AI", "Triggered schedule_showing node.", "node")
    await sync_service.record_lead_event(lead_id, "AI", "Coordinating showing for 123 Oak St.", "thought")
    await sync_service.record_lead_event(lead_id, "GHL", "Appointment Booked: Showing at 123 Oak St.", "action")
    await asyncio.sleep(0.5)
    
    # 4. Offer
    await sync_service.record_lead_event(lead_id, "GHL", "Tag Added: ai_facilitate_offer", "action")
    await sync_service.record_lead_event(lead_id, "AI", "Triggered facilitate_offer node.", "node")
    await sync_service.record_lead_event(lead_id, "AI", "Analyzing market comps for 123 Oak St.", "thought")
    await sync_service.record_lead_event(lead_id, "AI", "Offer strategy sent to lead.", "sms")
    await asyncio.sleep(0.5)
    
    # 5. Under Contract
    await sync_service.record_lead_event(lead_id, "GHL", "Opportunity Status Changed: Won", "action")
    await sync_service.record_lead_event(lead_id, "AI", "Triggered escrow_nurture node.", "node")
    await sync_service.record_lead_event(lead_id, "AI", "Tracking milestone: Inspection Scheduled.", "thought")
    await asyncio.sleep(0.5)
    
    # 6. Closed
    await sync_service.record_lead_event(lead_id, "AI", "Triggered post_closing node.", "node")
    await sync_service.record_lead_event(lead_id, "AI", "Sent closing congratulations and referral request.", "sms")
    
    logger.info(f"✅ Journey simulation complete for {lead_name}")
    
    # Verify events
    events = sync_service.get_lead_events(lead_id)
    logger.info(f"📊 Total events recorded: {len(events)}")
    for e in reversed(events[:5]): # Show last 5
        logger.info(f"  [{e['time']}] {e['source']}: {e['event']}")

if __name__ == "__main__":
    asyncio.run(simulate_journey("L_TEST_999", "Testy McTestFace"))
