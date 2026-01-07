"""
GHL Conversation Bridge
Send and receive messages through GHL
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .ghl_api_client import GHLAPIClient

logger = logging.getLogger(__name__)


class GHLConversationBridge:
    """
    Bridge for SMS/Email conversations via GHL

    Features:
    - Send SMS through GHL
    - Send Email through GHL
    - Receive messages via webhooks
    - Conversation threading
    - Message history sync
    """

    def __init__(self, ghl_client: GHLAPIClient, tenant_id: str):
        self.ghl_client = ghl_client
        self.tenant_id = tenant_id

    def send_sms(
        self, contact_id: str, message: str, from_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send SMS via GHL

        Args:
            contact_id: GHL contact ID
            message: Message text
            from_number: Sending phone number

        Returns:
            Message result
        """
        try:
            result = self.ghl_client.send_sms(contact_id, message, from_number)
            logger.info(f"SMS sent to contact {contact_id}")
            return {
                "success": True,
                "message_id": result.get("id"),
                "contact_id": contact_id,
                "channel": "sms",
            }
        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return {"success": False, "error": str(e), "contact_id": contact_id}

    def send_email(
        self, contact_id: str, subject: str, body: str, from_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email via GHL"""
        try:
            result = self.ghl_client.send_email(contact_id, subject, body, from_email)
            logger.info(f"Email sent to contact {contact_id}")
            return {
                "success": True,
                "message_id": result.get("id"),
                "contact_id": contact_id,
                "channel": "email",
            }
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return {"success": False, "error": str(e), "contact_id": contact_id}

    def get_conversation_history(
        self, contact_id: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get message history for contact"""
        try:
            conversations = self.ghl_client.get_conversations(contact_id=contact_id)
            if not conversations.get("conversations"):
                return []

            conversation_id = conversations["conversations"][0]["id"]
            messages = self.ghl_client.get_messages(conversation_id, limit=limit)

            return messages.get("messages", [])
        except Exception as e:
            logger.error(f"Failed to get conversation history: {str(e)}")
            return []


if __name__ == "__main__":
    print("💬 GHL Conversation Bridge Demo\n")
    print("✅ Features:")
    print("   • send_sms() - Send SMS via GHL")
    print("   • send_email() - Send email via GHL")
    print("   • get_conversation_history() - Retrieve messages")
