"""
Multi-Channel Swarm Orchestrator - Coordinated Lead Follow-up
Coordinates rapid response across SMS, Email, and Voice for hot leads.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.twilio_client import TwilioClient
from ghl_real_estate_ai.services.sendgrid_client import SendGridClient
from ghl_real_estate_ai.services.vapi_service import VapiService
from ghl_real_estate_ai.services.agent_state_sync import sync_service

logger = get_logger(__name__)

class MultiChannelSwarmOrchestrator:
    """
    Coordinates multi-channel follow-up for hot leads.
    
    Pillar 3: SaaS Monetization
    Feature #8: Multi-Channel Lead Swarm Automation
    """
    
    def __init__(self):
        self.sms_client = TwilioClient()
        self.email_client = SendGridClient()
        self.voice_client = VapiService()
        
    async def trigger_hot_lead_swarm(
        self, 
        lead_id: str, 
        lead_data: Dict[str, Any],
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Coordinated multi-channel follow-up within 5 minutes.
        """
        logger.info(f"🚀 Triggering Multi-Channel Swarm for hot lead: {lead_id}")
        
        lead_name = lead_data.get('name', 'Lead')
        sync_service.record_agent_thought(
            "Orchestrator", 
            f"Detected hot lead {lead_name}. Initiating multi-channel swarm sequence.",
            "Success"
        )
        
        # Step 1: Immediate SMS (0 min)
        sync_service.record_agent_thought("SMSBot", f"Sending immediate follow-up SMS to {lead_name}.")
        sms_task = self.sms_client.send_sms(
            to_number=lead_data.get("phone"),
            message=f"Hi {lead_name}, Jorge here! I just saw your interest in the Austin market. I'm preparing some exclusive data for you now. Check your email in a minute!",
            tenant_id=tenant_id
        )
        
        # Step 2: Coordinated Email (1 min later)
        email_delay = 60 # seconds
        email_task = self._delayed_email(
            lead_id=lead_id,
            lead_data=lead_data,
            delay=email_delay,
            tenant_id=tenant_id
        )
        
        # Step 3: Coordinated Voice Call (3 mins later)
        voice_delay = 180 # seconds
        voice_task = self._delayed_call(
            lead_id=lead_id,
            lead_data=lead_data,
            delay=voice_delay,
            tenant_id=tenant_id
        )
        
        # We don't await them all here to avoid blocking the main thread, 
        # but for this service we'll return the initial status
        asyncio.create_task(sms_task)
        asyncio.create_task(email_task)
        asyncio.create_task(voice_task)
        
        return {
            "status": "SWARM_ACTIVE",
            "lead_id": lead_id,
            "channels": ["SMS", "Email", "Voice"],
            "started_at": datetime.now().isoformat()
        }
        
    async def _delayed_email(self, lead_id: str, lead_data: Dict[str, Any], delay: int, tenant_id: Optional[str]):
        await asyncio.sleep(delay)
        logger.info(f"📧 Sending swarm email to {lead_id}")
        lead_name = lead_data.get('name', 'Lead')
        sync_service.record_agent_thought("EmailBot", f"Delivering exclusive market data email to {lead_name}.")
        await self.email_client.send_template_email(
            to_email=lead_data.get("email"),
            template_id="hot_lead_followup",
            dynamic_data={"name": lead_name, "market": "Austin"}
        )
        
    async def _delayed_call(self, lead_id: str, lead_data: Dict[str, Any], delay: int, tenant_id: Optional[str]):
        await asyncio.sleep(delay)
        logger.info(f"📞 Triggering swarm AI voice call to {lead_id}")
        lead_name = lead_data.get('name', 'Lead')
        sync_service.record_agent_thought("VoiceBot", f"Initiating AI voice qualification call with {lead_name}.", "Warning")
        await self.voice_client.initiate_outbound_call(
            phone_number=lead_data.get("phone"),
            lead_data=lead_data
        )
