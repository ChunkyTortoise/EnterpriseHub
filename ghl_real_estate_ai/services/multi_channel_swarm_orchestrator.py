"""
Multi-Channel Swarm Orchestrator - Coordinated Lead Follow-up
Coordinates rapid response across SMS, Email, and Voice for hot leads.
"""
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.twilio_client import TwilioClient
from ghl_real_estate_ai.services.sendgrid_client import SendGridClient
from ghl_real_estate_ai.services.vapi_service import VapiService
from ghl_real_estate_ai.services.agent_state_sync import sync_service
from ghl_real_estate_ai.services.ghl_client import GHLClient
from ghl_real_estate_ai.api.schemas.ghl import MessageType
from ghl_real_estate_ai.compliance_platform.engine.policy_enforcer import PolicyEnforcer

logger = get_logger(__name__)

class SwarmStep(BaseModel):
    channel: str # SMS, Email, Voice, WhatsApp
    delay_seconds: int
    message_template: Optional[str] = None
    action_name: str

class SwarmPlaybook(BaseModel):
    name: str
    steps: List[SwarmStep]

DEFAULT_PLAYBOOK = SwarmPlaybook(
    name="Hot Lead Rapid Response",
    steps=[
        SwarmStep(
            channel="SMS",
            delay_seconds=0,
            message_template="Hi {name}, Jorge here! I just saw your interest in the {market} market. Check your email for exclusive data!",
            action_name="Initial Contact"
        ),
        SwarmStep(
            channel="WhatsApp",
            delay_seconds=30,
            message_template="Hey {name}! Just sent you an SMS. Are you available for a quick chat about {market}?",
            action_name="WhatsApp Follow-up"
        ),
        SwarmStep(
            channel="Email",
            delay_seconds=60,
            message_template="hot_lead_followup",
            action_name="Data Delivery"
        ),
        SwarmStep(
            channel="Voice",
            delay_seconds=180,
            message_template="ai_voice_script_v1",
            action_name="Qualification Call"
        )
    ]
)

class MultiChannelSwarmOrchestrator:
    """
    Coordinates multi-channel follow-up playbooks for hot leads.
    Integrates with GHL, Twilio, SendGrid, and Vapi.
    Includes real-time FHA compliance enforcement.
    """
    
    def __init__(self):
        self.sms_client = TwilioClient()
        self.email_client = SendGridClient()
        self.voice_client = VapiService()
        self.ghl_client = GHLClient()
        self.compliance_enforcer = PolicyEnforcer()
        
    async def trigger_swarm(
        self, 
        lead_id: str, 
        lead_data: Dict[str, Any],
        playbook: Optional[SwarmPlaybook] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a multi-channel swarm playbook for a lead.
        """
        playbook = playbook or DEFAULT_PLAYBOOK
        logger.info(f"🚀 Triggering Swarm Playbook '{playbook.name}' for lead: {lead_id}")
        
        lead_name = lead_data.get('name', lead_data.get('first_name', 'Lead'))
        market = lead_data.get('market', 'Austin')
        
        # Record initialization in dashboard
        await self._record_activity("Orchestrator", f"Initiating '{playbook.name}' for {lead_name}")

        # Start background execution of playbook steps
        asyncio.create_task(self._execute_playbook(lead_id, lead_data, playbook, tenant_id))
        
        return {
            "status": "SWARM_ACTIVE",
            "playbook": playbook.name,
            "lead_id": lead_id,
            "steps_count": len(playbook.steps),
            "started_at": datetime.now(timezone.utc).isoformat()
        }

    async def _execute_playbook(self, lead_id: str, lead_data: Dict[str, Any], playbook: SwarmPlaybook, tenant_id: Optional[str]):
        """Executes steps in sequence with their respective delays."""
        lead_name = lead_data.get('name', lead_data.get('first_name', 'Lead'))
        market = lead_data.get('market', 'Austin')

        for step in playbook.steps:
            try:
                if step.delay_seconds > 0:
                    await asyncio.sleep(step.delay_seconds)

                await self._execute_step(step, lead_id, lead_data, lead_name, market, tenant_id)
            except Exception as e:
                logger.error(f"Error executing swarm step {step.action_name}: {e}")
                await self._record_activity(f"{step.channel}Bot", f"Failed: {step.action_name}", "Error")

    async def _execute_step(self, step: SwarmStep, lead_id: str, lead_data: Dict[str, Any], lead_name: str, market: str, tenant_id: Optional[str]):
        """Executes a single step of the playbook with compliance check."""
        logger.info(f"Executing swarm step: {step.action_name} via {step.channel}")
        
        # Prepare message content
        message_content = None
        if step.message_template and step.channel in ["SMS", "WhatsApp", "Email"]:
            if step.channel == "Email":
                message_content = step.message_template # Email uses template IDs
            else:
                message_content = step.message_template.format(name=lead_name, market=market)

        # Compliance Check (except for Voice which uses its own scripts for now)
        if message_content and step.channel != "Email":
            compliance = await self.compliance_enforcer.intercept_message(message_content)
            if not compliance["allowed"]:
                logger.warning(f"🚫 Blocking non-compliant message for lead {lead_id}: {compliance['violations']}")
                await self._record_activity(
                    "ComplianceBot", 
                    f"BLOCKED: FHA violation in {step.channel} step. Suggestion: {compliance['suggestion']}", 
                    "Error"
                )
                return

        if step.channel == "SMS":
            msg = step.message_template.format(name=lead_name, market=market)
            await self.sms_client.send_sms(to_number=lead_data.get("phone"), message=msg, tenant_id=tenant_id)
            await self._record_activity("SMSBot", f"Sent SMS: {step.action_name} to {lead_name}")

        elif step.channel == "WhatsApp":
            msg = step.message_template.format(name=lead_name, market=market)
            # Use GHL Client for WhatsApp if available in GHL
            await self.ghl_client.send_message(contact_id=lead_id, message=msg, channel=MessageType.WHATSAPP)
            await self._record_activity("WhatsAppBot", f"Sent WhatsApp: {step.action_name} to {lead_name}")

        elif step.channel == "Email":
            await self.email_client.send_template_email(
                to_email=lead_data.get("email"),
                template_id=step.message_template,
                dynamic_data={"name": lead_name, "market": market}
            )
            await self._record_activity("EmailBot", f"Delivered Email: {step.action_name} to {lead_name}")

        elif step.channel == "Voice":
            await self.voice_client.initiate_outbound_call(
                phone_number=lead_data.get("phone"),
                lead_data=lead_data
            )
            await self._record_activity("VoiceBot", f"Started Voice Call: {step.action_name} with {lead_name}", "Warning")

    async def _record_activity(self, agent: str, task: str, status: str = "Success"):
        """Helper to record agent activity for the dashboard."""
        try:
            # Check if record_agent_thought is async (it should be)
            if asyncio.iscoroutinefunction(sync_service.record_agent_thought):
                await sync_service.record_agent_thought(agent, task, status)
            else:
                sync_service.record_agent_thought(agent, task, status)
        except Exception as e:
            logger.warning(f"Failed to record dashboard activity: {e}")
